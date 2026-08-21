// C/C++
#include <algorithm>

// yaml
#include <yaml-cpp/yaml.h>

// torch
#include <ATen/TensorIterator.h>

// snap
#include <snap/snap.h>

#include <snap/coord/coord_utils.hpp>
#include <snap/hydro/hydro.hpp>
#include <snap/mesh/meshblock.hpp>
#include <snap/utils/level_meter.hpp>
#include <snap/utils/log.hpp>

#include "aneos.hpp"
#include "eos_dispatch.hpp"
#include "equation_of_state.hpp"
#include "ideal_gas.hpp"
#include "ideal_moist.hpp"
#include "moist_mixture.hpp"
#include "plume_eos.hpp"
#include "shallow_water.hpp"

namespace snap {

// [SCAFFOLDING] SNAPY_METER: per-level tally of the conserved limiter's three
// SILENT repairs -- the NaN sweep, the density floor and the energy (20 K
// temperature) floor. S49's cell black box caught the h150/5-layer death cell
// at EXACTLY the 20 K floor one RK stage before the abort, at level 105 of 150;
// this is what turns "a silent repair fired in the interior" from one observed
// cell into a per-level count. Diagnostic build only, NOT for upstream.
namespace {

struct EosMeters {
  LevelMeter nan_{"eos.nan_erased[x2/x3 ghosts excluded]"};
  LevelMeter dfl_{"eos.density_floor[x2/x3 ghosts excluded]"};
  LevelMeter efl_{"eos.energy_floor(20K)[x2/x3 ghosts excluded]"};
  int64_t calls = 0;
};

EosMeters* g_eos_meters = nullptr;

void eos_meter_report() {
  if (g_eos_meters == nullptr || g_eos_meters->calls == 0) return;
  std::cout << "[METER] FINAL apply_conserved_limiter_ calls="
            << g_eos_meters->calls << "\n";
  g_eos_meters->nan_.report("FINAL ");
  g_eos_meters->dfl_.report("FINAL ");
  g_eos_meters->efl_.report("FINAL ");
  std::cout.flush();
}

EosMeters& eos_meters() {
  if (g_eos_meters == nullptr) {
    g_eos_meters = new EosMeters();  // leaked on purpose; printed by atexit
    std::atexit(eos_meter_report);
  }
  return *g_eos_meters;
}

}  // namespace

EquationOfStateOptions EquationOfStateOptionsImpl::from_yaml(
    std::string const& filename, bool verbose) {
  auto config = YAML::LoadFile(filename);
  auto op = EquationOfStateOptionsImpl::create();

  if (!config["dynamics"]) return op;
  if (!config["dynamics"]["equation-of-state"]) return op;

  auto node = config["dynamics"]["equation-of-state"];
  op->verbose() = node["verbose"].as<bool>(verbose);

  op->type() = node["type"].as<std::string>("moist-mixture");
  if (op->verbose()) {
    SINFO(EquationOfStateOptions) << "EOS type = " << op->type() << std::endl;
  }

  op->gammad() = node["gammad"].as<double>(1.4);
  op->weight() = node["weight"].as<double>(29.e-3);

  op->density_floor() = node["density-floor"].as<double>(1.e-6);
  if (op->verbose()) {
    SINFO(EquationOfStateOptions)
        << "density floor = " << op->density_floor() << std::endl;
  }

  op->pressure_floor() = node["pressure-floor"].as<double>(1.e-3);
  op->temperature_floor() = node["temperature-floor"].as<double>(20.);

  op->limiter() = node["limiter"].as<bool>(false);
  if (op->verbose()) {
    SINFO(EquationOfStateOptions)
        << "limiter = " << (op->limiter() ? "true" : "false") << std::endl;
  }

  op->eos_file() = node["eos-file"].as<std::string>("");
  if (op->verbose() && !op->eos_file().empty()) {
    SINFO(EquationOfStateOptions)
        << "eos file = " << op->eos_file() << std::endl;
  }

  op->thermo() = kintera::ThermoOptionsImpl::from_yaml(filename, op->verbose());

  if (op->thermo()) {
    TORCH_CHECK(
        NMASS == 0 || (op->thermo()->vapor_ids().size() +
                           op->thermo()->cloud_ids().size() ==
                       1 + NMASS),
        "Athena++ style indexing is enabled (NMASS > 0), but the number of "
        "vapor and cloud species in the thermodynamics options does not match "
        "the expected number of vapor + cloud species = ",
        1 + NMASS);
  }

  return op;
}

EquationOfStateImpl::EquationOfStateImpl(EquationOfStateOptions const& options_,
                                         torch::nn::Module* p)
    : options(options_) {
  phydro = dynamic_cast<HydroImpl const*>(p);
  TORCH_CHECK(phydro, "[EquationOfState] Parent module is null.");
  cache_cloud_parents_();
}

void EquationOfStateImpl::cache_cloud_parents_() {
  if (!options->thermo()) return;

  auto const species = options->thermo()->species();
  auto const& vids = options->thermo()->vapor_ids();
  auto const& cids = options->thermo()->cloud_ids();
  auto const nucleation = options->thermo()->nucleation();
  cloud_parent_cache_.resize(cids.size());
  if (!nucleation) return;

  for (size_t j = 0; j < cids.size(); ++j) {
    double parent_mass = 0.;
    for (auto const& reaction : nucleation->reactions()) {
      if (!reaction.products().count(species[cids[j]])) continue;

      for (auto const& [parent, coefficient] : reaction.reactants()) {
        auto species_it = std::find(species.begin(), species.end(), parent);
        if (species_it == species.end()) continue;
        int species_id = std::distance(species.begin(), species_it);
        auto vapor_it = std::find(vids.begin() + 1, vids.end(), species_id);
        if (vapor_it == vids.end()) continue;

        int vapor_index = std::distance(vids.begin(), vapor_it);
        double mass = coefficient * kintera::species_weights[species_id];
        cloud_parent_cache_[j].emplace_back(ICY + vapor_index - 1, mass);
        parent_mass += mass;
      }
      break;
    }

    if (parent_mass <= 0.) {
      cloud_parent_cache_[j].clear();
      continue;
    }
    for (auto& parent : cloud_parent_cache_[j]) {
      parent.second /= parent_mass;
    }
  }
}

torch::Tensor EquationOfStateImpl::internal_energy_offset(
    torch::Tensor hydro_like) const {
  return torch::zeros_like(hydro_like[IDN]);
}

torch::Tensor EquationOfStateImpl::specific_heat_cv(torch::Tensor prim,
                                                    torch::Tensor temp) {
  return torch::zeros_like(temp);
}

torch::Tensor EquationOfStateImpl::compute(
    std::string ab, std::vector<torch::Tensor> const& args) {
  TORCH_CHECK(false, "[EquationOfState] compute() is not implemented.",
              "Please use this method in a derived class.");
}

/*torch::Tensor EquationOfStateImpl::get_buffer(std::string) const {
  TORCH_CHECK(false, "[EquationOfState] get_buffer() is not implemented.",
              "Please use this method in a derived class.");
}*/

torch::Tensor EquationOfStateImpl::forward(torch::Tensor cons,
                                           torch::optional<torch::Tensor> out) {
  auto prim = out.value_or(torch::empty_like(cons));
  return compute("U->W", {cons, prim});
}

void EquationOfStateImpl::apply_conserved_limiter_(torch::Tensor const& cons) {
  auto pmb = phydro->pmb;
  auto pcoord = pmb->pcoord;

  if (!options->limiter()) return;  // no limiter

  const bool meter = snapy_meter_on();
  // Drop the x2/x3 ghost columns: they are periodic copies here, so counting
  // them multiplies one real firing by (1 + 2*nghost/nx2) and makes an
  // all-ghost event look like an interior one. The x1 ghosts are KEPT -- the
  // per-level histogram labels them, and whether the lid ghosts fire is itself
  // a question.
  auto eos_interior = [&](torch::Tensor b) {
    if (pcoord->kl() > 0) b.slice(0, 0, pcoord->kl()).zero_();
    if (pcoord->ku() + 1 < b.size(0)) b.slice(0, pcoord->ku() + 1).zero_();
    if (pcoord->jl() > 0) b.slice(1, 0, pcoord->jl()).zero_();
    if (pcoord->ju() + 1 < b.size(1)) b.slice(1, pcoord->ju() + 1).zero_();
    return b;
  };
  auto eos_crop = [&](torch::Tensor t) {
    return t.slice(0, pcoord->kl(), pcoord->ku() + 1)
        .slice(1, pcoord->jl(), pcoord->ju() + 1);
  };
  torch::Tensor nanmask;
  if (meter) {
    auto& m = eos_meters();
    m.calls++;
    // Geometry so the report can separate an INTERIOR firing from a ghost one.
    for (auto* p : {&m.nan_, &m.dfl_, &m.efl_})
      p->geometry(pcoord->il(), pcoord->iu());
    nanmask = torch::isnan(cons).any(0);
    m.nan_.add(eos_interior(nanmask.clone()));
    // Count the density clamp the way it actually FIRES: the NaN sweep below
    // sets a NaN density to 0 and the clamp then lifts it to the floor, which
    // is a repair -- but `NaN < floor` is false, so the naive predicate misses
    // exactly the cells that matter during a blow-up.
    m.dfl_.add(eos_interior((cons[IDN] < options->density_floor()) |
                            torch::isnan(cons[IDN])));
  }

  cons.masked_fill_(torch::isnan(cons), 0.);
  cons[IDN].clamp_min_(options->density_floor());

  // for (int i = ICY; i < ICY + nvapor; ++i)
  //   cons.index(interior)[i] = pull_neighbors3(cons.index(interior)[i]);
  //  batched
  // cons.index(interior).narrow(0, ICY, nvapor) =
  //    pull_neighbors4(cons.index(interior).narrow(0, ICY, nvapor));

  int ny = 0;
  int nvapor = 0;
  int ncloud = 0;
  if (options->thermo()) {
    nvapor = options->thermo()->vapor_ids().size() - 1;
    ncloud = options->thermo()->cloud_ids().size();
    ny = nvapor + ncloud;
  }

  if (nvar() > IPR) {
    auto mom = cons.narrow(0, IVX, 3).clone();
    coord_vec_raise_(mom, pcoord->cosine_cell_kj);
    auto rho = cons[IDN] + cons.narrow(0, ICY, ny).sum(0);
    auto ke = 0.5 * (mom * cons.narrow(0, IVX, 3)).sum(0) / rho;
    auto min_temp = options->temperature_floor() * torch::ones_like(ke);
    auto min_ie = compute("UT->I", {cons, min_temp});
    auto min_e = ke + min_ie;
    if (meter) {
      auto& m = eos_meters();
      // Exclude cells the NaN sweep already zeroed: `0 < min_e` is true for
      // every one of them, so without this the energy-floor count is dominated
      // by NaN fallout that eos.nan_erased has ALREADY counted -- reported as
      // "the 20 K floor fired here" when the cell was never cold, it was dead.
      // `min_e` itself can be non-finite once a species sum drives rho <= 0
      // (the ICY rows are repaired only further down), so require it finite.
      m.efl_.add(eos_interior((cons[IPR] < min_e) & torch::isfinite(min_e) &
                              torch::logical_not(nanmask)));
      m.efl_.worst(eos_crop(cons[IPR]), eos_crop(min_e), pcoord->il(),
                   pcoord->iu());
      if (m.calls % 200 == 0) {
        std::cout << "[METER] apply_conserved_limiter_ calls=" << m.calls
                  << "\n";
        m.nan_.report("");
        m.dfl_.report("");
        m.efl_.report("");
        std::cout.flush();
      }
    }
    cons[IPR].clamp_min_(min_e);
  }

  if (options->thermo() && ny > 0) {
    auto nghost = pcoord->options->nghost();
    auto interior = pmb->part({0, 0, 0}, PartOptions().exterior(false));

    // A negative condensate value means the tracer flux over-drained the cell;
    // the mass is in a neighbour, not missing. Zeroing it (`clamp_min_(0.)`)
    // invented mass one-way -- measured at 102% of the total-mass drift in
    // silicate cloud runs. Instead, borrow the deficit from the parent vapor in
    // the SAME cell: exactly conservative in mass, energy and elements, and
    // per-cell, so ghost copies receive the identical repair and ranks stay in
    // sync. A cell whose vapor cannot cover the deficit goes vapor-negative and
    // is handled by the columnar fix_vapor below. The phase shift is ~1% of the
    // local value and the saturation adjustment re-equilibrates it at the end
    // of the same cycle.
    for (int j = 0; j < ncloud; ++j) {
      int slot = ICY + nvapor + j;
      auto c = cons[slot];
      auto const& parents = cloud_parent_cache_[j];
      if (parents.empty()) {
        // Clouds not produced by nucleation have no parent-vapor metadata.
        c.clamp_min_(0.);
        continue;
      }

      auto deficit = c.clamp_max(0.);
      for (auto const& [parent_slot, mass_fraction] : parents) {
        cons[parent_slot] += deficit * mass_fraction;
      }
      c.clamp_min_(0.);  // condensate to exactly zero
    }

    auto vapor = cons.index(interior).narrow(0, ICY, nvapor);
    auto major = cons.index(interior)[IDN].unsqueeze(0);
    auto iter = at::TensorIteratorConfig()
                    .resize_outputs(false)
                    .declare_static_shape(vapor.sizes(),
                                          /*squash_dim=*/vapor.dim() - 1)
                    .add_output(vapor)
                    .add_owned_input(major.expand_as(vapor))
                    .build();

    int err = at::native::call_fix_vapor(cons.device().type(), iter);
    TORCH_CHECK(err == 0,
                "[EquationOfState] apply_conserved_limiter_: "
                "Failed to fix vapor mass fractions.");
  }
}

void EquationOfStateImpl::apply_primitive_limiter_(torch::Tensor const& prim) {
  if (!options->limiter()) return;  // no limiter
  prim.masked_fill_(torch::isnan(prim), 0.);
  prim[IDN].clamp_min_(options->density_floor());

  if (options->thermo()) {
    int ny = options->thermo()->vapor_ids().size() +
             options->thermo()->cloud_ids().size() - 1;
    prim.narrow(0, ICY, ny).clamp_min_(0.);
  }

  prim[IPR].clamp_min_(options->pressure_floor());
}

EquationOfState EquationOfStateImpl::create(EquationOfStateOptions const& opts,
                                            torch::nn::Module* p,
                                            std::string const& name) {
  TORCH_CHECK(p, "[EquationOfState] Parent module pointer is null.");
  TORCH_CHECK(opts, "[EquationOfState] Options pointer is null.");

  if (opts->type() == "ideal-gas") {
    return p->register_module(name, IdealGas(opts, p));
  } else if (opts->type() == "ideal-moist") {
    return p->register_module(name, IdealMoist(opts, p));
  } else if (opts->type() == "moist-mixture") {
    return p->register_module(name, MoistMixture(opts, p));
  } else if (opts->type() == "aneos") {
    return p->register_module(name, ANEOS(opts, p));
  } else if (opts->type() == "shallow-water") {
    return p->register_module(name, ShallowWater(opts, p));
  } else if (opts->type() == "plume-eos") {
    return p->register_module(name, PlumeEOS(opts, p));
  } else {
    TORCH_CHECK(false, "EquationOfState: Unknown type: ", opts->type());
  }
}

}  // namespace snap
