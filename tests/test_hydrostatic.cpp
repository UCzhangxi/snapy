// C/C++
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>

// POSIX
#include <unistd.h>

// gtest
#include <gtest/gtest.h>

// snap
#include <snap/snap.h>

#include <snap/mesh/mesh.hpp>

using namespace snap;

namespace {

const char* cubed_sphere_hydrostatic_config = R"(
reference-state:
  Tref: 300.
  Pref: 100.

species:
  - name: dry
    composition: {O: 0.42, N: 1.56, Ar: 0.01}
    cv_R: 2.5

dynamics:
  equation-of-state:
    type: ideal-gas
    gammad: 1.4
    density-floor: 1.e-12
    pressure-floor: 1.e-12
    limiter: false

  reconstruct:
    vertical: {type: weno5, scale: false, shock: false}
    horizontal: {type: weno5, scale: false, shock: false}

  riemann-solver:
    type: lmars

integration:
  type: rk3
  cfl: 0.4
  implicit-scheme: 0

forcing:
  const-gravity:
    grav1: -1.
    non-hydrostatic: 0.

distribute:
  layout: cubed-sphere
  nb2: 1
  nb3: 1
  blocks_per_process: 6
  verbose: false

geometry:
  type: gnomonic-equiangle
  cells: {nx1: 24, nx2: 8, nx3: 8, nghost: 3}
  bounds:
    x1min: 10.
    x1max: 11.
    x2min_pi: -0.25
    x2max_pi: 0.25
    x3min_pi: -0.25
    x3max_pi: 0.25

boundary-condition:
  external:
    x1-inner: reflecting
    x1-outer: reflecting
    x2-inner: custom
    x2-outer: custom
    x3-inner: custom
    x3-outer: custom
)";

const char* split_slab_config = R"(
reference-state: {Tref: 300., Pref: 100.}
species:
  - {name: dry, composition: {O: 0.42, N: 1.56, Ar: 0.01}, cv_R: 2.5}
dynamics:
  hydrostatic-init: @HSE@
  equation-of-state: {type: ideal-gas, gammad: 1.4, density-floor: 1.e-12, pressure-floor: 1.e-12, limiter: false}
  reconstruct:
    vertical: {type: weno5, scale: false, shock: false}
    horizontal: {type: weno5, scale: false, shock: false}
  riemann-solver: {type: lmars}
integration: {type: rk3, cfl: 0.4, implicit-scheme: 0}
forcing:
  const-gravity: {grav1: -1., non-hydrostatic: 1.}
distribute: {layout: cubed, nb1: @NB1@, nb2: 1, nb3: 1, blocks_per_process: @NB1@, verbose: false}
geometry:
  type: cartesian
  cells: {nx1: 32, nx2: 4, nx3: 1, nghost: 3}
  bounds: {x1min: 10., x1max: 250., x2min: 0., x2max: 40., x3min: 0., x3max: 10.}
boundary-condition:
  external:
    x1-inner: reflecting
    x1-outer: reflecting
    x2-inner: periodic
    x2-outer: periodic
    x3-inner: periodic
    x3-outer: periodic
)";

std::string write_temp_config(std::string text = cubed_sphere_hydrostatic_config) {
  char fname[] = "/tmp/test-hydrostatic-XXXXXX";
  int fd = mkstemp(fname);
  EXPECT_NE(fd, -1);
  if (fd != -1) close(fd);

  std::ofstream outfile(fname);
  outfile << text;
  outfile.close();
  return fname;
}

void initialize_hydrostatic_column(MeshBlock const& block, Variables& vars) {
  constexpr double gamma = 1.4;
  constexpr double pressure0 = 100.;
  constexpr double density0 = 1.;
  constexpr double gravity = 1.;
  constexpr double radius0 = 10.;

  auto pcoord = block->pcoord;
  auto entropy = pressure0 / std::pow(density0, gamma);
  auto exponent = (gamma - 1.) / gamma;
  auto pressure_power = std::pow(pressure0, exponent) -
                        exponent * gravity * (pcoord->x1v - radius0) /
                            std::pow(entropy, 1. / gamma);
  auto pressure = pressure_power.pow(1. / exponent);
  auto density = (pressure / entropy).pow(1. / gamma);

  auto nc1 = pcoord->options->nc1();
  auto nc2 = pcoord->options->nc2();
  auto nc3 = pcoord->options->nc3();
  auto w = torch::zeros({block->phydro->peos->nvar(), nc3, nc2, nc1},
                        torch::kFloat64);
  w[IDN].copy_(density.view({1, 1, nc1}).expand({nc3, nc2, nc1}));
  w[IPR].copy_(pressure.view({1, 1, nc1}).expand({nc3, nc2, nc1}));
  vars["hydro_w"] = w;
}

double max_rest_velocity(Mesh& mesh, MeshVariables& vars, int nsteps) {
  double worst = 0.;
  for (int step = 0; step < nsteps; ++step) {
    auto dt = mesh->max_time_step(vars);
    for (int stage = 0; stage < mesh->blocks.front()->pintg->stages.size();
         ++stage) {
      mesh->forward(vars, dt, stage);
    }

    for (size_t i = 0; i < mesh->blocks.size(); ++i) {
      auto interior = mesh->blocks[i]->part(
          {0, 0, 0}, PartOptions().exterior(false).ndim(3));
      worst = std::max(
          worst,
          vars[i].at("hydro_w")[IVX].index(interior).abs().max().item<double>());
    }
  }
  return worst;
}

// the same isentrope, but INTEGRATED cell by cell as every initial-condition builder
// integrates one, instead of evaluated from the closed form
void initialize_marched_column(MeshBlock const& block, Variables& vars) {
  constexpr double gamma = 1.4;
  constexpr double pressure0 = 100.;
  constexpr double density0 = 1.;
  constexpr double gravity = 1.;

  auto pcoord = block->pcoord;
  auto nc1 = pcoord->options->nc1();
  int il = pcoord->il();
  double dz = pcoord->dx1f[il].item<double>();
  double entropy = pressure0 / std::pow(density0, gamma);

  auto pres = torch::zeros({nc1}, torch::kFloat64);
  auto dens = torch::zeros({nc1}, torch::kFloat64);
  auto pa = pres.accessor<double, 1>();
  auto da = dens.accessor<double, 1>();
  // march from the GLOBAL bottom to this block's first cell: at nb1 > 1 every block would
  // otherwise restart at pressure0 and the seam would carry a jump, not a column
  double p = pressure0, d = std::pow(pressure0 / entropy, 1. / gamma);
  for (int k = 0; k < pcoord->options->ix1(); ++k) {
    p -= gravity * d * dz;
    d = std::pow(p / entropy, 1. / gamma);
  }
  pa[il] = p;
  da[il] = d;
  for (int i = il; i + 1 < nc1; ++i) {
    pa[i + 1] = pa[i] - gravity * da[i] * dz;
    da[i + 1] = std::pow(pa[i + 1] / entropy, 1. / gamma);
  }
  for (int i = il; i > 0; --i) {
    pa[i - 1] = pa[i] + gravity * da[i] * dz;
    da[i - 1] = std::pow(pa[i - 1] / entropy, 1. / gamma);
  }

  auto nc2 = pcoord->options->nc2();
  auto nc3 = pcoord->options->nc3();
  auto w = torch::zeros({block->phydro->peos->nvar(), nc3, nc2, nc1}, torch::kFloat64);
  w[IDN].copy_(dens.view({1, 1, nc1}).expand({nc3, nc2, nc1}));
  w[IPR].copy_(pres.view({1, 1, nc1}).expand({nc3, nc2, nc1}));
  vars["hydro_w"] = w;
}

// the SAME column, deep enough that dz/H is not negligible, and marched
double deep_rest_velocity(int nx1, bool hydrostatic_init) {
  std::string text = cubed_sphere_hydrostatic_config;
  text.replace(text.find("x1max: 11."), 10, "x1max: 250.");
  text.replace(text.find("nx1: 24"), 7, "nx1: " + std::to_string(nx1));
  text.replace(text.find("dynamics:\n"), 10,
               std::string("dynamics:\n  hydrostatic-init: ") +
                   (hydrostatic_init ? "true\n" : "false\n"));

  auto fname = write_temp_config(text);
  auto mesh = Mesh(MeshOptionsImpl::from_yaml(fname));
  std::remove(fname.c_str());
  mesh->to(torch::kCPU, torch::kFloat64);

  MeshVariables vars(mesh->blocks.size());
  for (size_t i = 0; i < mesh->blocks.size(); ++i) {
    initialize_marched_column(mesh->blocks[i], vars[i]);
  }
  auto part = mesh->blocks[0]->part({0, 0, 0}, PartOptions().exterior(false).ndim(3));
  auto w0 = vars[0].at("hydro_w");
  auto rt0 = (w0[IPR] / w0[IDN]).index(part).clone();
  auto p0 = w0[IPR].index(part).clone();

  mesh->initialize(vars);

  auto w1 = vars[0].at("hydro_w");
  // p moves; rho moves with it so that p/rho -- the temperature -- does not
  auto rt1 = (w1[IPR] / w1[IDN]).index(part);
  EXPECT_LT((rt1 / rt0 - 1.).abs().max().item<double>(), 1.e-13);
  // key off: the interior is untouched. The only automated statement of that property.
  if (!hydrostatic_init)
    EXPECT_EQ((w1[IPR].index(part) / p0 - 1.).abs().max().item<double>(), 0.);
  return max_rest_velocity(mesh, vars, 100);
}

// the same marched column on a slab split into nb1 blocks IN ONE PROCESS: pz > 1 with no
// process group, so there is no gauge relay -- the configuration fix 1's tolerance assumes
double split_slab_rest_velocity(int nb1, bool hydrostatic_init) {
  std::string text = split_slab_config;
  text.replace(text.find("@HSE@"), 5, hydrostatic_init ? "true" : "false");
  for (size_t p = text.find("@NB1@"); p != std::string::npos; p = text.find("@NB1@"))
    text.replace(p, 5, std::to_string(nb1));

  auto fname = write_temp_config(text);
  auto mesh = Mesh(MeshOptionsImpl::from_yaml(fname));
  std::remove(fname.c_str());
  mesh->to(torch::kCPU, torch::kFloat64);

  MeshVariables vars(mesh->blocks.size());
  for (size_t i = 0; i < mesh->blocks.size(); ++i) {
    initialize_marched_column(mesh->blocks[i], vars[i]);
  }
  mesh->initialize(vars);
  return max_rest_velocity(mesh, vars, 100);
}

}  // namespace

TEST(HydrostaticAtmosphere, cubed_sphere_remains_at_rest) {
  torch::set_num_threads(1);
  torch::set_num_interop_threads(1);

  auto fname = write_temp_config();
  auto mesh = Mesh(MeshOptionsImpl::from_yaml(fname));
  std::remove(fname.c_str());
  mesh->to(torch::kCPU, torch::kFloat64);
  ASSERT_EQ(mesh->blocks.size(), 6);

  MeshVariables vars(mesh->blocks.size());
  for (size_t i = 0; i < mesh->blocks.size(); ++i) {
    initialize_hydrostatic_column(mesh->blocks[i], vars[i]);
  }
  mesh->initialize(vars);

  constexpr int nsteps = 100;
  double max_vertical_velocity = max_rest_velocity(mesh, vars, nsteps);

  std::cout << "maximum spurious vertical velocity after " << nsteps
            << " steps: " << max_vertical_velocity << std::endl;
  EXPECT_TRUE(std::isfinite(max_vertical_velocity));
  EXPECT_LT(max_vertical_velocity, 1.e-8);
}

// S115. The case above starts from the closed-form isentrope, which is hydrostatic to
// round-off. Every production column is INTEGRATED instead, and the integration is only
// O(dz^2) accurate -- so the column handed to a well-balanced scheme is not the resting
// state it is meant to be, and the scheme faithfully turns that error into a force.
TEST(HydrostaticAtmosphere, deep_column_needs_a_discretely_balanced_initial_column) {
  double off32 = deep_rest_velocity(32, false);
  double off64 = deep_rest_velocity(64, false);
  double on32 = deep_rest_velocity(32, true);
  double on64 = deep_rest_velocity(64, true);

  std::cout << "deep column, max spurious |vel1| after 100 steps:\n"
            << "  marched column         nx1=32: " << off32
            << "   nx1=64: " << off64 << "   ratio: " << off64 / off32 << "\n"
            << "  hydrostatic-init       nx1=32: " << on32
            << "   nx1=64: " << on64 << std::endl;

  EXPECT_GT(off32, 1.e-6);
  EXPECT_LT(off64, 0.6 * off32);
  EXPECT_LT(on32, 1.e-9);
  EXPECT_LT(on64, 1.e-9);
}

// An x1-split column on one process has no gauge relay, so each block would keep its own
// constant if the relay were the only thing holding them together. It must still rest.
TEST(HydrostaticAtmosphere, a_locally_split_column_also_rests) {
  double off1 = split_slab_rest_velocity(1, false);
  double on1 = split_slab_rest_velocity(1, true);
  double off2 = split_slab_rest_velocity(2, false);
  double on2 = split_slab_rest_velocity(2, true);
  std::cout << "split slab, max spurious |vel1| after 100 steps:\n"
            << "  nb1=1  off: " << off1 << "  on: " << on1 << "\n"
            << "  nb1=2  off: " << off2 << "  on: " << on2 << std::endl;

  // unsplit: the projection works, measured against its own unprojected control
  EXPECT_LT(on1, 1.e-2 * off1);
  // split within one process: documented no-op (no relay -> block-local reference), so the
  // key changes nothing at all rather than half-balancing the column
  EXPECT_DOUBLE_EQ(on2, off2);
}
