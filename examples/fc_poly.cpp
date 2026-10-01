// Fully compressible polytropic convection: Anders & Brown (2017), Phys. Rev.
// Fluids 2, 083501. Ported from athena's fc_poly problem generator.
//
// Rest check (noise 0, 128 x 512, 2 t_b): with diffusion off max |u|/c_s stays
// below 3.4e-13. With diffusion on, two known residuals remain at rest:
// * u2 in the wall row at each x2 block edge, |u|/c_s 1.15e-5 from cycle 1,
//   identical with stock reflecting walls: snapy's diffusion operator, see
//   branch xiz/test-wb-wall-corner;
// * the linear-T0 polytrope is not a discrete conductive equilibrium: the
//   interior face flux is off by +1.29e-3 under the top wall, which heats the
//   top cell at 1.29e-3 chi_t/dz = 6.0e-4 per unit volume and time.

// C/C++
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

// yaml
#include <yaml-cpp/yaml.h>

// kintera
#include <kintera/constants.h>

// snap
#include <snap/snap.h>

#include <snap/coord/coordinate.hpp>
#include <snap/eos/equation_of_state.hpp>
#include <snap/hydro/balance_column.hpp>
#include <snap/mesh/mesh.hpp>

using namespace snap;

namespace {

struct RunConfig {
  std::string input_file;
  std::string restart_file;
};

RunConfig ParseArguments(int argc, char** argv,
                         std::string const& default_input) {
  RunConfig cfg{default_input, ""};
  for (int i = 1; i < argc; ++i) {
    std::string arg(argv[i]);
    if ((arg == "-r" || arg == "--restart") && i + 1 < argc) {
      cfg.restart_file = argv[++i];
    } else {
      cfg.input_file = arg;
    }
  }
  return cfg;
}

// Everything is derived from the primaries eps, n_rho, Ra, Pr, aspect and the
// EOS (gamma, Rd), in units where T = rho = 1 at the top; z = x1 points up.
struct Polytrope {
  Polytrope(YAML::Node const& problem, double gamma_, double Rd_)
      : eps(problem["eps"].as<double>()),
        n_rho(problem["n_rho"].as<double>(3.)),
        Ra(problem["Ra"].as<double>()),
        Pr(problem["Pr"].as<double>(1.)),
        aspect(problem["aspect"].as<double>(4.)),
        gamma(gamma_),
        Rd(Rd_) {
    m = 1. / (gamma - 1.) - eps;
    TORCH_CHECK(m > 0., "fc_poly: eps too large for gamma, m = ", m);
    Lz = std::exp(n_rho / m) - 1.;
    Lx = aspect * Lz;
    cp = gamma * Rd / (gamma - 1.);
    g = Rd * (m + 1.);
    double dS0_cp = eps * (n_rho / m) * (gamma - 1.) / gamma;
    nu_t = std::sqrt(Pr * g * Lz * Lz * Lz * dS0_cp / Ra);
    chi_t = nu_t / Pr;
    t_b = std::sqrt(Lz * cp / (g * eps * n_rho));
  }

  double T0(double z) const { return 1. + Lz - z; }

  // background density for the dissipation, held at the wall value outside
  // [0, Lz] where T0 may go negative
  double rho0_clamped(double z) const {
    return std::pow(T0(std::clamp(z, 0., Lz)), m);
  }

  double eps, n_rho, Ra, Pr, aspect, gamma, Rd;
  double m, Lz, Lx, cp, g, nu_t, chi_t, t_b;
};

// the input carries the grid and gravity snapy needs; they must match the
// derived atmosphere
void check_input(YAML::Node const& config, Polytrope const& p) {
  auto require = [](char const* what, double got, double want) {
    TORCH_CHECK(std::abs(got - want) <= 1.e-10 * std::max(1., std::abs(want)),
                "fc_poly: ", what, " = ", got, " but the derived value is ",
                want);
  };
  auto bounds = config["geometry"]["bounds"];
  require("x1min", bounds["x1min"].as<double>(), 0.);
  require("x1max", bounds["x1max"].as<double>(), p.Lz);
  require("x2min", bounds["x2min"].as<double>(), 0.);
  require("x2max", bounds["x2max"].as<double>(), p.Lx);
  require("grav1", config["forcing"]["const-gravity"]["grav1"].as<double>(),
          -p.g);
  TORCH_CHECK(!config["forcing"]["diffusion"],
              "fc_poly: forcing.diffusion is derived here; remove it");

  // the linear T0 continued into the top ghosts must stay positive
  auto cells = config["geometry"]["cells"];
  double T0_ghost =
      1. - cells["nghost"].as<int>() * p.Lz / cells["nx1"].as<double>();
  TORCH_CHECK(T0_ghost > 0.,
              "fc_poly: grid too coarse, top ghost T0 = ", T0_ghost,
              "; raise nx1");
  if (T0_ghost < 0.25) {
    std::cout << "fc_poly: WARNING top ghost T0 = " << T0_ghost << std::endl;
  }
}

// nu(z) = nu_t/rho0(z), chi(z) = chi_t/rho0(z), as a table with one knot per
// global x1 cell centre, ghosts included; snapy's kinematic conduction flux is
// kappa*rho*cv*dT/dn, hence kappa_iso = chi_t/cv
void set_dissipation(MeshBlockOptions const& opts, YAML::Node const& cells,
                     Polytrope const& p) {
  int ng = cells["nghost"].as<int>();
  int nx1 = cells["nx1"].as<int>();
  double dz = p.Lz / nx1;

  auto table = torch::empty({2, nx1 + 2 * ng}, torch::kFloat64);
  auto t = table.accessor<double, 2>();
  for (int k = 0; k < nx1 + 2 * ng; ++k) {
    t[0][k] = (k - ng + 0.5) * dz;
    t[1][k] = 1. / p.rho0_clamped(t[0][k]);
  }

  auto diff = DiffusionOptionsImpl::create();
  diff->nu_iso(p.nu_t)
      .kappa_iso(p.chi_t / (p.cp - p.Rd))
      .nu_scale_x1_table(table)
      .kappa_scale_x1_table(table.clone());
  opts->hydro()->diffusion(diff);
}

// splitmix64, as athena's fc_poly, so both codes draw the same noise
double hash_uniform(std::uint64_t a) {
  a += 0x9e3779b97f4a7c15ULL;
  a = (a ^ (a >> 30)) * 0xbf58476d1ce4e5b9ULL;
  a = (a ^ (a >> 27)) * 0x94d049bb133111ebULL;
  a = a ^ (a >> 31);
  return static_cast<double>(a >> 11) / static_cast<double>(1ULL << 53);
}

// leftover |a|/g of the balanced column: keeps |u|/c_s < 1e-12 for ~2 t_b
constexpr double kBalanceRtol = 1.e-14;

// the polytrope projected onto the scheme's own discrete hydrostatic balance
// at fixed T, then white noise in T entering through p; the noise is hashed
// from the global cell index, so it does not depend on the decomposition
void initialize_block(MeshBlock block, Variables& vars, Polytrope const& p,
                      YAML::Node const& config, torch::Device const& device) {
  auto problem = config["problem"];
  double noise = problem["noise"].as<double>(1.e-2);
  auto seed = problem["seed"].as<std::int64_t>(42);
  std::int64_t nx1 = config["geometry"]["cells"]["nx1"].as<std::int64_t>();
  std::int64_t nx2 = config["geometry"]["cells"]["nx2"].as<std::int64_t>();
  double dx1 = p.Lz / nx1, dx2 = p.Lx / nx2;

  auto pcoord = block->pcoord;
  TORCH_CHECK(pcoord->options->nx1() == nx1,
              "fc_poly: the balance needs the whole x1 column in one block");
  TORCH_CHECK(block->phydro->options->wb_wall_clamp(),
              "fc_poly: the balance needs dynamics/wb-wall-clamp: true");
  int nc1 = pcoord->options->nc1();
  int nc2 = pcoord->options->nc2();
  int nc3 = pcoord->options->nc3();
  auto x1v = pcoord->x1v.cpu();
  auto x2v = pcoord->x2v.cpu();
  auto z = x1v.accessor<double, 1>();
  auto x = x2v.accessor<double, 1>();

  auto temp = torch::empty({nc3, nc2, nc1}, torch::kFloat64);
  auto kick = torch::ones({nc3, nc2, nc1}, torch::kFloat64);
  auto t = temp.accessor<double, 3>();
  auto f = kick.accessor<double, 3>();
  for (int k = 0; k < nc3; ++k) {
    for (int j = 0; j < nc2; ++j) {
      for (int i = 0; i < nc1; ++i) {
        t[k][j][i] = p.T0(z[i]);
        auto gi = std::llround(z[i] / dx1 - 0.5);
        auto gj = std::llround(x[j] / dx2 - 0.5);
        if (gi >= 0 && gi < nx1 && gj >= 0 && gj < nx2) {
          double u = hash_uniform(
              static_cast<std::uint64_t>(seed * 1000003LL + gj * nx1 + gi));
          f[k][j][i] = 1. + noise * p.eps * (u - 0.5);
        }
      }
    }
  }

  auto w = torch::zeros({block->phydro->peos->nvar(), nc3, nc2, nc1},
                        torch::kFloat64);
  w[IDN] = temp.pow(p.m);
  w[IPR] = w[IDN] * p.Rd * temp;

  auto in = block->part({0, 0, 0}, PartOptions().exterior(false));
  auto dx = pcoord->dx1f.cpu().narrow(0, pcoord->il(), nx1).contiguous();
  auto [balanced, residual, sweeps] = balance_column(
      w.index(in).contiguous(), dx, p.g, /*wall_clamp=*/true, kBalanceRtol,
      /*max_iter=*/400);
  w.index_put_(in, balanced);
  std::cout << std::scientific << std::setprecision(3)
            << "fc_poly: balance residual=" << residual << " sweeps=" << sweeps
            << std::endl;

  w[IPR] *= kick;
  vars["hydro_w"] = w.to(device);
}

// Ma_rms = sqrt of the volume mean of |u|^2/c_s^2, Ma_max = max |u|/c_s, KE =
// integral of rho|u|^2/2, over every block of every process
struct Diagnostics {
  double mach_rms, mach_max, ke;
};

Diagnostics diagnose(Mesh const& mesh, MeshVariables const& vars) {
  auto sums = torch::zeros({3}, torch::kFloat64);
  auto peak = torch::zeros({1}, torch::kFloat64);
  for (size_t i = 0; i < mesh->blocks.size(); ++i) {
    auto block = mesh->blocks[i];
    auto in = block->part({0, 0, 0}, PartOptions().exterior(false).ndim(3));
    auto w = vars[i].at("hydro_w");
    double gamma = block->phydro->peos->options->gammad();

    auto vol = block->pcoord->cell_volume().index(in);
    auto rho = w[IDN].index(in);
    auto u2 = w.narrow(0, IVX, 3).square().sum(0).index(in);
    auto mach2 = u2 * rho / (gamma * w[IPR].index(in));
    sums += torch::stack(
                {(mach2 * vol).sum(), vol.sum(), (0.5 * rho * u2 * vol).sum()})
                .cpu();
    peak = torch::maximum(peak, mach2.max().sqrt().cpu().view({1}));
  }

  std::vector<torch::Tensor> buf = {sums}, top = {peak};
  auto layout = mesh->blocks.front()->get_layout();
  if (layout->has_process_group()) {
    layout->comm->allreduce(buf, c10d::ReduceOp::SUM);
    layout->comm->allreduce(top, c10d::ReduceOp::MAX);
  }
  auto s = buf[0].accessor<double, 1>();
  return {std::sqrt(s[0] / s[1]), top[0].item<double>(), s[2]};
}

void report(Mesh const& mesh, MeshVariables const& vars, double time,
            Polytrope const& p) {
  auto d = diagnose(mesh, vars);
  if (mesh->blocks.front()->options->layout()->process_rank() != 0) return;
  std::cout << std::scientific << std::setprecision(10) << "FCPOLY t=" << time
            << " t_b=" << time / p.t_b << " Ma_rms=" << d.mach_rms
            << " Ma_max=" << d.mach_max << " KE=" << d.ke << std::endl;
}

// A&B fixed-temperature wall (athena fc_poly FillGhost): the pressure is
// mirrored exactly, so the LMARS wall mass flux cancels; T0 is continued into
// the ghost and T - T0 mirrored oddly, so T = T0 on the wall and the wall
// conducts the background flux; u1 odd, u2 and u3 even
void fill_fixed_temperature(torch::Tensor const& var, int dim,
                            BoundaryFuncOptions op, bool outer) {
  int nc = var.size(dim), ng = op.nghost();
  if (nc == 1) return;
  int g0 = outer ? nc - ng : 0, a0 = outer ? nc - 2 * ng : ng;
  auto ghost = var.narrow(dim, g0, ng);
  auto src = var.narrow(dim, a0, ng).flip(dim);

  // passive scalars and the flux-positivity factor mirror evenly
  if (op.type() == kScalar) {
    ghost.copy_(src);
    return;
  }
  TORCH_CHECK(op.eos && op.coord && var.size(0) == 5 && dim == var.dim() - 1,
              "fixed_temperature: a dry ideal-gas x1 wall only");

  double gamma = op.eos->options->gammad();
  double Rd = kintera::constants::Rgas / op.eos->species_weight();
  double Lz = op.coord->options->global_x1max();
  auto zg = op.coord->x1v.narrow(0, g0, ng);
  auto za = op.coord->x1v.narrow(0, a0, ng).flip(0);

  bool cons = op.type() == kConserved;
  auto rho_a = src[IDN];
  auto u = cons ? src.narrow(0, IVX, 3) / rho_a : src.narrow(0, IVX, 3).clone();
  auto p_a = cons ? (gamma - 1.) * (src[IPR] - 0.5 * rho_a * u.square().sum(0))
                  : src[IPR];

  // T_g = T0(z_g) - (T_a - T0(z_a))
  auto T_g = 2. * (1. + Lz) - zg - za - p_a / (rho_a * Rd);
  TORCH_CHECK((T_g > 0.).all().item<bool>(),
              "fixed_temperature: non-positive ghost temperature");
  auto rho_g = p_a / (Rd * T_g);
  u[0].neg_();

  auto out = torch::empty_like(ghost);
  out[IDN] = rho_g;
  if (cons) {
    out.narrow(0, IVX, 3) = rho_g * u;
    out[IPR] = p_a / (gamma - 1.) + 0.5 * rho_g * u.square().sum(0);
  } else {
    out.narrow(0, IVX, 3) = u;
    out[IPR] = p_a;
  }
  ghost.copy_(out);
}

}  // namespace

// selected by `x1-inner/x1-outer: fixed_temperature`; the name marks the face
// as a wall for the diffusion operator
BC_FUNCTION(fixed_temperature_inner, var, dim, op) {
  fill_fixed_temperature(var, dim, op, false);
}

BC_FUNCTION(fixed_temperature_outer, var, dim, op) {
  fill_fixed_temperature(var, dim, op, true);
}

int main(int argc, char** argv) {
  torch::set_num_threads(1);
  torch::set_num_interop_threads(1);

  auto args = ParseArguments(argc, argv, "fc_poly.yaml");
  auto config = YAML::LoadFile(args.input_file);

  auto options = MeshOptionsImpl::from_yaml(args.input_file);
  auto eos = options->block()->hydro()->eos();
  TORCH_CHECK(eos->type() == "ideal-gas", "fc_poly: needs an ideal-gas EOS");
  Polytrope poly(config["problem"], eos->gammad(),
                 kintera::constants::Rgas / eos->weight());
  check_input(config, poly);
  set_dissipation(options->block(), config["geometry"]["cells"], poly);

  auto mesh = Mesh(options);
  auto device = torch::Device(mesh->options->device_str());
  if (device.is_cuda()) {
    std::cout << "Running on CUDA" << std::endl;
  }
  mesh->to(device);

  if (mesh->blocks.front()->options->layout()->process_rank() == 0) {
    std::cout << std::setprecision(10) << "fc_poly: m=" << poly.m
              << " Lz=" << poly.Lz << " g=" << poly.g << " nu_t=" << poly.nu_t
              << " chi_t=" << poly.chi_t << " t_b=" << poly.t_b << std::endl;
  }

  MeshVariables vars(mesh->blocks.size());
  if (args.restart_file.empty()) {
    for (size_t i = 0; i < mesh->blocks.size(); ++i) {
      initialize_block(mesh->blocks[i], vars[i], poly, config, device);
    }
  }

  double current_time = args.restart_file.empty()
                            ? mesh->initialize(vars)
                            : mesh->initialize(vars, args.restart_file.c_str());
  mesh->make_outputs(vars, current_time);

  int cycle = mesh->blocks.front()->cycle;
  int ncycle_out = mesh->blocks.front()->pintg->options->ncycle_out();
  report(mesh, vars, current_time, poly);
  while (!mesh->blocks.front()->pintg->stop(cycle, current_time)) {
    ++cycle;
    mesh->set_cycle(cycle);

    auto dt = mesh->max_time_step(vars);
    mesh->print_cycle_info(vars, current_time, dt);

    for (int stage = 0; stage < mesh->blocks.front()->pintg->stages.size();
         ++stage) {
      mesh->forward(vars, dt, stage);
    }

    int redo = mesh->check_redo(vars);
    if (redo > 0) {
      cycle = mesh->blocks.front()->cycle;
      continue;
    }
    if (redo < 0) break;

    current_time += dt;
    mesh->make_outputs(vars, current_time);
    if (ncycle_out > 0 && cycle % ncycle_out == 0) {
      report(mesh, vars, current_time, poly);
    }
  }

  return mesh->finalize(vars, current_time);
}
