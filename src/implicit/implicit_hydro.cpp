// yaml
#include <yaml-cpp/yaml.h>

#include <string>
#include <vector>

// snap
#include <snap/snap.h>

#include <cstdlib>
#include <snap/coord/coord_utils.hpp>
#include <snap/hydro/hydro.hpp>
#include <snap/mesh/meshblock.hpp>
#include <snap/utils/tvd_meter.hpp>

#include "implicit_dispatch.hpp"
#include "implicit_hydro.hpp"

namespace snap {

ImplicitOptions ImplicitOptionsImpl::from_yaml(const std::string& filename,
                                               bool /*verbose*/) {
  auto config = YAML::LoadFile(filename);
  if (!config["integration"]) return nullptr;
  if (!config["integration"]["implicit-scheme"]) return nullptr;
  return from_yaml(config["integration"]["implicit-scheme"]);
}

ImplicitOptions ImplicitOptionsImpl::from_yaml(const YAML::Node& node) {
  int s = node.as<int>();
  // scheme 0 == "none": an implicit object that does nothing. Treat it as if
  // the `implicit-scheme` key were absent (return nullptr) so `implicit-scheme:
  // 0` is a true explicit spelling that also runs at nb1>1, instead of tripping
  // the nb1 guard on a phantom no-op object. picorr != null now faithfully
  // means "implicit is active".
  if (s == 0) return nullptr;
  auto op = ImplicitOptionsImpl::create();
  op->scheme(s);
  return op;
}

std::string ImplicitOptionsImpl::type() const {
  switch (scheme()) {
    case 0:
      return "none";
      break;
    case 1:
      return "vic-partial";
      break;
    case 9:
      return "vic-full";
      break;
    default:
      TORCH_CHECK(false, "Unsupported implicit scheme");
  }
}

ImplicitHydroImpl::ImplicitHydroImpl(ImplicitOptions const& options_,
                                     torch::nn::Module* p)
    : options(options_) {
  phydro = dynamic_cast<HydroImpl const*>(p);
  reset();
}

void ImplicitHydroImpl::reset() {
  TORCH_CHECK(phydro, "[ImplicitHydro] Parent Hydro is null");
  _a = register_buffer("a", torch::empty({0}, torch::kFloat64));
  _b = register_buffer("b", torch::empty({0}, torch::kFloat64));
  _c = register_buffer("c", torch::empty({0}, torch::kFloat64));
  _delta = register_buffer("delta", torch::empty({0}, torch::kFloat64));
  _du0 = register_buffer("du0", torch::empty({0}, torch::kFloat64));
  _corr = register_buffer("corr", torch::empty({0}, torch::kFloat64));
  _mass_corr = register_buffer("mass_corr", torch::empty({0}, torch::kFloat64));
}

void ImplicitHydroImpl::ensure_workspace(torch::Tensor const& w) {
  auto pcoord = phydro->pmb->pcoord;
  int nx1 = pcoord->options->nx1();
  int nx2 = pcoord->options->nx2();
  int nx3 = pcoord->options->nx3();
  int m = options->size();

  auto abc_shape = std::vector<int64_t>{1, nx3, nx2, nx1 * m * m};
  auto delta_shape = std::vector<int64_t>{1, nx3, nx2, nx1 * m};

  auto needs_reset = [&](torch::Tensor const& t,
                         std::vector<int64_t> const& shape) {
    return !t.defined() || t.sizes().vec() != shape ||
           t.scalar_type() != w.scalar_type() || t.device() != w.device();
  };

  auto maybe_resize = [&](torch::Tensor& t, std::vector<int64_t> const& shape) {
    if (needs_reset(t, shape)) {
      t.set_(torch::empty(shape, w.options()));
    }
  };

  maybe_resize(_a, abc_shape);
  maybe_resize(_b, abc_shape);
  maybe_resize(_c, abc_shape);
  maybe_resize(_delta, delta_shape);
  maybe_resize(_du0, w.sizes().vec());
  maybe_resize(_corr, w.sizes().vec());
  maybe_resize(_mass_corr, w.sizes().vec());
}

torch::Tensor ImplicitHydroImpl::forward(torch::Tensor du, torch::Tensor w,
                                         torch::Tensor gamma, double dt) {
  if (options->scheme() == 0) {  // null operation
    if (_corr.sizes() != du.sizes() ||
        _corr.scalar_type() != du.scalar_type() ||
        _corr.device() != du.device()) {
      _corr.set_(torch::zeros_like(du));
    } else {
      _corr.zero_();
    }
    return _corr;
  }

  TORCH_CHECK(phydro->options->grav(),
              "[ImplicitHydro] forcing does not have const-gravity");

  auto pcoord = phydro->pmb->pcoord;
  auto interior = phydro->pmb->part({0, 0, 0}, PartOptions().exterior(false));
  auto cos_theta = pcoord->cosine_cell_kj;
  auto sin_theta = torch::sqrt(1.0 - cos_theta * cos_theta);

  /*if (torch::isnan(du.index(interior)).any().item<bool>()) {
    TORCH_CHECK(false, "[ImplicitHydro] NaN encountered before implicit solve");
  }*/

  ensure_workspace(w);
  _du0.copy_(du);
  _mass_corr.zero_();

  /// (1) Project to local orthonormal frame
  w[IVY] += w[IVZ] * cos_theta;
  w[IVZ] *= sin_theta;

  coord_vec_raise_(du.narrow(0, IVX, 3), cos_theta);
  pcoord->prim2local1_(du);

  //// -------- Solve block-tridiagonal matrix --------- ////
  auto iter =
      at::TensorIteratorConfig()
          .resize_outputs(false)
          .check_all_same_dtype(true)
          .declare_static_shape(du.index(interior).sizes(),
                                /*squash_dims=*/{0, 3})
          .add_owned_output(du.index(interior))
          .add_owned_output(_mass_corr.index(interior))
          .add_owned_input(w.index(interior))
          .add_owned_input(gamma.unsqueeze(0).index(interior))
          .add_owned_input(
              pcoord->face_area1().unsqueeze(0).contiguous().index(interior))
          .add_owned_input(
              pcoord->cell_volume().unsqueeze(0).contiguous().index(interior))
          .add_input(_a)
          .add_input(_b)
          .add_input(_c)
          .add_input(_delta)
          .build();

  // Linearize the FULL gravity: du always carries it (body force + rho_grav
  // sum to grav1); scaling by non_hydrostatic() drops the gravity coupling
  // and destabilizes the solve at dt >> dt_acoustic whenever nh < 1.
  auto grav1 = phydro->options->grav()->grav1();

  if ((options->scheme() >> 3) & 1) {
    at::native::vic_assemble_full(du.device().type(), iter, dt, grav1, 0);
    at::native::vic_solve_full(du.device().type(), iter, dt, grav1, 0);
    at::native::vic_redistribute_full(du.device().type(), iter, dt, grav1, 0);
  } else {
    // Match the full-VIC pipeline: assemble coefficients, run the column
    // solve + reductions, then apply the per-cell redistribution map.
    at::native::vic_assemble_partial(du.device().type(), iter, dt, grav1, 0);
    at::native::vic_solve_partial(du.device().type(), iter, dt, grav1, 0);
    at::native::vic_redistribute_partial(du.device().type(), iter, dt, grav1,
                                         0);
  }

  // ---- [S54] vic_redistribute AUDIT. NON-ACTING; gated on SNAPY_TVD_METER.
  // ---- With ny = 0 (this deck: one species, kinetics off) the entire
  // vic_redistribute pipeline reduces ALGEBRAICALLY to
  //
  //     DU(IDN,i) = delta_i(0) - R * rho_i / sum_j(rho_j V_j)
  //
  // whenever the availability clamp (vic_redistribute_impl.h:106-107) never
  // truncates a transfer.  R = sum_i phi_i is the column residual, the net mass
  // the implicit solve asked for that a closed column cannot represent as a
  // face flux; snapy removes it mass-weighted, ExoCubed keeps it.
  //
  // Therefore  k_i := (DU(IDN,i) - delta_i(0)) / rho_i  is CONSTANT down a
  // column if and only if the clamp is dormant, and its constant value is
  // -R/sum(m).  So ONE read-only comparison measures both unknowns at once:
  // deviation from constancy  => the clamp fired (and where);
  // the constant itself       => the size of R.
  //
  // ExoCubed writes du_(IDN) = delta_i(0) flat (forward_backward.hpp:106), so
  // "clamp dormant AND R == 0" means the two codes are IDENTICAL here and the
  // stage comes off the suspect list by algebra rather than by an ablation.
  // [S54] EXOCUBED-PARITY DENSITY UPDATE, env-gated on SNAPY_VIC_EXO_DENSITY.
  //
  // In THIS deck the whole vic_redistribute apparatus has exactly one
  // observable effect, and all three of its other legs are measured inert:
  //   * species routing  -- ny = 0 (one species, kinetics off), pass 3b no-ops;
  //   * residual removal -- R measured at 1.4e-16 of column mass, i.e. zero;
  //   * face-transfer export -- MASS(IVX+dir) is read ONLY under
  //     `if (pscalar->nvar() > 0)` (meshblock.cpp:670-687), and this deck has
  //     no passive scalars.
  // What remains is the availability clamp (vic_redistribute_impl.h:106-107).
  // So overwriting the density row with delta_i(0) is simultaneously "disable
  // the clamp", "disable vic_redistribute", and "do exactly what ExoCubed does"
  // (forward_backward.hpp:106). One line, three experiments.
  if ((options->scheme() >> 3) & 1) {
    torch::NoGradGuard nograd;
    int m = options->size();
    auto dui = du.index(interior);
    auto wint = w.index(interior);
    auto voli = pcoord->cell_volume().unsqueeze(0).contiguous().index(interior);
    auto dn = dui.narrow(0, IDN, 1);
    auto rho = wint.narrow(0, IDN, 1);
    auto d0 =
        _delta.view({_delta.size(0), _delta.size(1), _delta.size(2), -1, m})
            .select(-1, 0);
    static const bool exo_density =
        std::getenv("SNAPY_VIC_EXO_DENSITY") != nullptr;
    if (tvd_meter_on()) {
      // R measured DIRECTLY (independent of any constancy assumption):
      //   R = sum_i (delta_i(0) - du_explicit_i) * V_i          [mass/step]
      // _du0 is du saved before the solve (:131); the frame projection at
      // :138-139 touches IVX..IVZ only, so the IDN row is untouched.
      auto du0dn = _du0.index(interior).narrow(0, IDN, 1);
      auto sum_m = (rho * voli).sum(-1, true);
      auto Rcol = ((d0 - du0dn) * voli).sum(-1, true);
      FaceMeter::note_max("vic.|R|", Rcol.abs().max().item<double>());
      FaceMeter::note_max("vic.|R|/summ",
                          (Rcol.abs() / sum_m).max().item<double>());

      // ⚠ SECOND CORRECTION TO THIS TEST. Once R is MEASURED to be zero to
      // round-off (1.4e-16 of column mass), the identity collapses from
      //   "k_i := (DU(IDN,i) - delta_i(0))/rho_i is CONSTANT down the column"
      // to the far simpler
      //   "DU(IDN,i) == delta_i(0)  exactly, cell by cell".
      // A constancy test is then degenerate: k is identically zero, so any
      // normalisation by k's own spread is 0/0 and reports round-off as signal.
      // (That is what the previous two versions did -- first against a column
      // mean, then against max|k|.) The right question with R = 0 is simply
      // HOW BIG the discrepancy is, measured against the implicit increment it
      // is supposed to equal.
      auto absdiff = (dn - d0).abs();
      auto rel = absdiff / d0.abs().clamp_min(1e-300);
      FaceMeter::tally_levels("vic.clamp.any", rel > 1e-10);
      FaceMeter::tally_levels("vic.clamp.material", rel > 1e-2);
      FaceMeter::note_max("vic.max_rel_dn_vs_delta", rel.max().item<double>());
      // physical magnitude: relative density change per step that the clamp
      // moved
      FaceMeter::note_max("vic.max|dn-delta|/rho",
                          (absdiff / rho).max().item<double>());
    }
    if (exo_density) du.index(interior).narrow(0, IDN, 1).copy_(d0);
  }

  /// (3) De-project from local orthonormal frame
  w[IVZ] /= sin_theta;
  w[IVY] -= w[IVZ] * cos_theta;
  pcoord->flux2global1_(du);

  _corr.copy_(du);
  _corr.sub_(_du0);

  /*if (torch::isnan(du.index(interior)).any().item<bool>()) {
    TORCH_CHECK(false, "[ImplicitHydro] NaN encountered after implicit solve");
  }*/

  return _corr;
}

std::shared_ptr<ImplicitHydroImpl> ImplicitHydroImpl::create(
    ImplicitOptions const& opts, torch::nn::Module* p,
    std::string const& name) {
  TORCH_CHECK(p != nullptr, "[ImplicitHydro] Parent module is nullptr");
  TORCH_CHECK(opts != nullptr, "[ImplicitHydro] Options pointer is nullptr");

  return p->register_module(name, ImplicitHydro(opts, p));
}

}  // namespace snap
