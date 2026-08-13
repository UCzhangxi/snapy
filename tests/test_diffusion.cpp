// C/C++
#include <cmath>

// external
#include <gtest/gtest.h>
#include <yaml-cpp/yaml.h>

// torch
#include <torch/torch.h>

// snap
#include <snap/snap.h>

#include <snap/bc/bc_func.hpp>
#include <snap/bc/internal_boundary.hpp>
#include <snap/forcing/forcing.hpp>
#include <snap/mesh/meshblock.hpp>

// tests
#include "device_testing.hpp"

using namespace snap;

namespace {

std::shared_ptr<MeshBlockImpl> make_block() {
  return std::make_shared<MeshBlockImpl>(
      MeshBlockOptionsImpl::from_yaml("test_diffusion.yaml"));
}

void make_x1_periodic(MeshBlockOptions const& options) {
  options->bfuncs()[BoundaryFace::kInnerX1] =
      get_bc_func().at("periodic_inner");
  options->bfuncs()[BoundaryFace::kOuterX1] =
      get_bc_func().at("periodic_outer");
  options->bcnames()[BoundaryFace::kInnerX1] = "periodic_inner";
  options->bcnames()[BoundaryFace::kOuterX1] = "periodic_outer";
}

std::shared_ptr<MeshBlockImpl> make_periodic_block(int nx1) {
  auto options = MeshBlockOptionsImpl::from_yaml("test_diffusion.yaml");
  options->coord()->global_nx1() = nx1;
  options->coord()->nx1() = nx1;
  options->coord()->global_x1max() = 2. * M_PI;
  options->coord()->x1max() = 2. * M_PI;
  options->hydro()->diffusion()->kappa_iso() = 0.;
  make_x1_periodic(options);
  return std::make_shared<MeshBlockImpl>(options);
}

std::shared_ptr<MeshBlockImpl> make_x2_wall_block() {
  auto options = MeshBlockOptionsImpl::from_yaml("test_diffusion.yaml");
  options->coord()->global_nx2() = 6;
  options->coord()->nx2() = 6;
  options->coord()->global_x2max() = 6.;
  options->coord()->x2max() = 6.;
  options->bfuncs().push_back(get_bc_func().at("reflecting_inner"));
  options->bfuncs().push_back(get_bc_func().at("reflecting_outer"));
  options->bcnames().push_back("reflecting_inner");
  options->bcnames().push_back("reflecting_outer");
  return std::make_shared<MeshBlockImpl>(options);
}

torch::Tensor make_primitive(std::shared_ptr<MeshBlockImpl> const& block,
                             torch::Device device, torch::Dtype dtype) {
  auto coord = block->pcoord;
  auto w = torch::ones(
      {5, coord->options->nc3(), coord->options->nc2(), coord->options->nc1()},
      torch::device(device).dtype(dtype));
  w[IPR] = 1.e5;
  w.narrow(0, IVX, 3).zero_();
  return w;
}

void fill_periodic_x1(torch::Tensor const& var, int nghost) {
  BoundaryFuncOptions options;
  options.type(kPrimitive).nghost(nghost);
  get_bc_func().at("periodic_inner")(var, 3, options);
  get_bc_func().at("periodic_outer")(var, 3, options);
}

void fill_reflecting_x1(torch::Tensor const& var, int nghost) {
  BoundaryFuncOptions options;
  options.type(kPrimitive).nghost(nghost);
  get_bc_func().at("reflecting_inner")(var, 3, options);
  get_bc_func().at("reflecting_outer")(var, 3, options);
}

//! Density linear in x1 with slope kRhoSlope, then reflected so that the x1
//! ghosts hold the MIRROR of the first active cell instead of the value the
//! linear profile has there -- exactly what `reflecting` installs in a
//! stratified atmosphere. Temperature is linear over ALL cells, ghosts
//! included, so dT/dn is the same at every face and the conductive flux is
//! proportional to the face density alone.
constexpr double kRho0 = 1.0, kRhoSlope = 0.2, kTemp0 = 300.0,
                 kTempSlope = 10.0;

torch::Tensor make_linear_state(std::shared_ptr<MeshBlockImpl> const& block,
                                torch::Device device, torch::Dtype dtype,
                                torch::Tensor* temp) {
  auto coord = block->pcoord;
  auto w = torch::zeros(
      {5, coord->options->nc3(), coord->options->nc2(), coord->options->nc1()},
      torch::device(device).dtype(dtype));
  auto x = coord->x1v.to(device, dtype).view({1, 1, -1});
  *temp = kTemp0 + kTempSlope * x;
  w[IDN] = kRho0 + kRhoSlope * x;
  fill_reflecting_x1(w, coord->options->nghost());
  auto Rd = 8.31446261815324 / block->phydro->peos->options->weight();
  w[IPR] = w[IDN] * Rd * (*temp);
  return w;
}

}  // namespace

TEST(diffusion_options, parse_and_reject_legacy_keys) {
  auto options = DiffusionOptionsImpl::from_yaml(
      YAML::Load("diffusion: {nu_iso: 2.0, kappa_iso: 3.0}"));
  ASSERT_TRUE(options);
  EXPECT_DOUBLE_EQ(options->nu_iso(), 2.);
  EXPECT_DOUBLE_EQ(options->kappa_iso(), 3.);

  EXPECT_ANY_THROW(DiffusionOptionsImpl::from_yaml(
      YAML::Load("diffusion: {K: 2.0, type: theta}")));
  EXPECT_ANY_THROW(
      DiffusionOptionsImpl::from_yaml(YAML::Load("diffusion: {nu_iso: -1.0}")));
}

TEST(diffusion_options, reject_enabled_curved_coordinates) {
  auto options = MeshBlockOptionsImpl::from_yaml("test_diffusion.yaml");
  options->coord()->type() = "spherical-polar";
  EXPECT_ANY_THROW(std::make_shared<MeshBlockImpl>(options));

  options->hydro()->diffusion()->nu_iso() = 0.;
  options->hydro()->diffusion()->kappa_iso() = 0.;
  EXPECT_NO_THROW(std::make_shared<MeshBlockImpl>(options));
}

TEST(diffusion_options, reject_conduction_without_reference_specific_heat) {
  auto options = MeshBlockOptionsImpl::from_yaml("test_diffusion.yaml");
  options->hydro()->eos()->type() = "shallow-water";
  options->hydro()->diffusion()->nu_iso() = 0.;
  EXPECT_ANY_THROW(std::make_shared<MeshBlockImpl>(options));
}

TEST_P(DeviceTest, uniform_state_has_zero_tendency) {
  auto block = make_block();
  block->to(device, dtype);
  EXPECT_TRUE(
      torch::allclose(block->pcoord->center_distance1(),
                      torch::ones_like(block->pcoord->center_distance1())));
  auto w = make_primitive(block, device, dtype);
  auto temp = block->phydro->peos->compute("W->T", {w});
  auto du = torch::zeros_like(w);

  block->phydro->pdiffusion->forward(du, w, temp, 0.1);
  EXPECT_TRUE(torch::allclose(du, torch::zeros_like(du), 1.e-6, 1.e-6));
}

TEST_P(DeviceTest, transverse_velocity_uses_viscous_laplacian) {
  auto block = make_block();
  block->to(device, dtype);
  auto w = make_primitive(block, device, dtype);
  auto x = block->pcoord->x1v.to(device, dtype);
  w[IVY] = x.square();
  auto temp = block->phydro->peos->compute("W->T", {w});
  auto du = torch::zeros_like(w);

  block->phydro->pdiffusion->forward(du, w, temp, 0.1);
  auto expected = torch::zeros_like(du[IVY]);
  expected.index(block->part({0, 0, 0}, PartOptions().exterior(false).ndim(3)))
      .fill_(0.1);
  EXPECT_TRUE(torch::allclose(du[IVY], expected, 1.e-5, 1.e-5));
}

TEST_P(DeviceTest, temperature_uses_conductive_laplacian) {
  auto block = make_block();
  block->to(device, dtype);
  auto w = make_primitive(block, device, dtype);
  auto x = block->pcoord->x1v.to(device, dtype);
  auto temp = x.square().view({1, 1, -1});
  auto Rd = 8.31446261815324 / block->phydro->peos->options->weight();
  w[IPR] = w[IDN] * Rd * temp;
  auto du = torch::zeros_like(w);

  block->phydro->pdiffusion->forward(du, w, temp, 0.1);
  auto cv_ref = block->phydro->peos->species_cv_ref();
  EXPECT_NEAR(du[IPR][0][0][4].item<double>(), 0.05 * cv_ref, 1.e-3);
  EXPECT_TRUE(torch::allclose(du[IDN], torch::zeros_like(du[IDN])));
  EXPECT_TRUE(torch::allclose(du.narrow(0, IVX, 3),
                              torch::zeros_like(du.narrow(0, IVX, 3))));
}

TEST_P(DeviceTest, viscous_sine_mode_matches_analytic_decay) {
  constexpr int nx1 = 64;
  constexpr int nsteps = 100;
  auto block = make_periodic_block(nx1);
  block->to(device, dtype);
  auto coord = block->pcoord;
  auto w = make_primitive(block, device, dtype);
  auto x = coord->x1v.to(device, dtype).view({1, 1, -1});
  w[IVY] = torch::sin(x);
  fill_periodic_x1(w, coord->options->nghost());

  auto nu = block->phydro->pdiffusion->options->nu_iso();
  auto dx = (coord->options->x1max() - coord->options->x1min()) / nx1;
  auto dt = 0.1 * dx * dx / nu;
  for (int n = 0; n < nsteps; ++n) {
    auto temp = block->phydro->peos->compute("W->T", {w});
    auto du = torch::zeros_like(w);
    block->phydro->pdiffusion->forward(du, w, temp, dt);
    w[IVY] += du[IVY];
    fill_periodic_x1(w, coord->options->nghost());
  }

  auto interior = block->part({0, 0, 0}, PartOptions().exterior(false).ndim(3));
  auto time = nsteps * dt;
  auto expected = torch::sin(x) * std::exp(-nu * time);
  EXPECT_TRUE(torch::allclose(w[IVY].index(interior), expected.index(interior),
                              3.e-4, 3.e-4));
}

// ISSUES S39. On a linear density profile the two-cell average is exact on
// every INTERIOR face, so a uniform dT/dn gives the same tendency in every
// interior cell -- unless the wall face reads the ghost, which the reflecting
// fill has put off the profile. Reading the ghost halves the tendency in the
// two wall cells while leaving the interior right: the A11 signature.
TEST_P(DeviceTest, wall_face_coefficient_reads_no_ghost) {
  auto block = make_block();
  block->to(device, dtype);
  torch::Tensor temp;
  auto w = make_linear_state(block, device, dtype, &temp);
  auto du = torch::zeros_like(w);

  block->phydro->pdiffusion->forward(du, w, temp, 0.1);

  auto interior = block->part({0, 0, 0}, PartOptions().exterior(false).ndim(3));
  auto got = du[IPR].index(interior);
  auto cv_ref = block->phydro->peos->species_cv_ref();
  auto expected = 0.1 * block->phydro->pdiffusion->options->kappa_iso() *
                  cv_ref * kTempSlope * kRhoSlope;
  EXPECT_TRUE(
      torch::allclose(got, torch::full_like(got, expected), 1.e-5, 1.e-5))
      << "du[IPR] over the interior: " << got;
}

// The same construction along x2, so that face_coefficient runs with the face
// axis in the middle of the tensor rather than last. Density and temperature
// are uniform along x1, so the x1 direction contributes nothing.
TEST_P(DeviceTest, wall_face_coefficient_reads_no_ghost_in_x2) {
  auto block = make_x2_wall_block();
  block->to(device, dtype);
  auto coord = block->pcoord;
  auto w = torch::zeros(
      {5, coord->options->nc3(), coord->options->nc2(), coord->options->nc1()},
      torch::device(device).dtype(dtype));
  auto y = coord->x2v.to(device, dtype).view({1, -1, 1});
  auto temp = kTemp0 + kTempSlope * y;
  w[IDN] = kRho0 + kRhoSlope * y;
  {
    BoundaryFuncOptions bops;
    bops.type(kPrimitive).nghost(coord->options->nghost());
    get_bc_func().at("reflecting_inner")(w, 2, bops);
    get_bc_func().at("reflecting_outer")(w, 2, bops);
  }
  auto Rd = 8.31446261815324 / block->phydro->peos->options->weight();
  w[IPR] = w[IDN] * Rd * temp;

  auto du = torch::zeros_like(w);
  block->phydro->pdiffusion->forward(du, w, temp, 0.1);

  auto interior = block->part({0, 0, 0}, PartOptions().exterior(false).ndim(3));
  auto got = du[IPR].index(interior);
  auto cv_ref = block->phydro->peos->species_cv_ref();
  auto expected = 0.1 * block->phydro->pdiffusion->options->kappa_iso() *
                  cv_ref * kTempSlope * kRhoSlope;
  EXPECT_TRUE(
      torch::allclose(got, torch::full_like(got, expected), 1.e-5, 1.e-5))
      << "du[IPR] over the interior: " << got;
}

// The same state under a periodic x1: the ghost is then the true wrapped
// neighbour, so the two-cell average is correct and the wall extrapolation
// must NOT fire. The deliberately off-profile ghost makes the two answers
// differ, so this discriminates.
TEST_P(DeviceTest, periodic_x1_face_is_not_extrapolated) {
  auto options = MeshBlockOptionsImpl::from_yaml("test_diffusion.yaml");
  make_x1_periodic(options);
  auto block = std::make_shared<MeshBlockImpl>(options);
  block->to(device, dtype);
  torch::Tensor temp;
  auto w = make_linear_state(block, device, dtype, &temp);
  auto du = torch::zeros_like(w);

  block->phydro->pdiffusion->forward(du, w, temp, 0.1);

  int nghost = block->pcoord->options->nghost();
  auto cv_ref = block->phydro->peos->species_cv_ref();
  auto full = 0.1 * block->phydro->pdiffusion->options->kappa_iso() * cv_ref *
              kTempSlope * kRhoSlope;
  // mirrored ghost => the wrap face average sits half a slope short
  EXPECT_NEAR(du[IPR][0][0][nghost].item<double>(), 0.5 * full, 1.e-4 * full);
}

// Only reflecting and solid fill the ghost with a state that does not stand for
// the fluid at the face. Everything else -- including a caller-supplied
// function whose name was never recorded -- must keep the two-cell average.
TEST(diffusion_options, only_reflecting_and_solid_count_as_walls) {
  auto options = MeshBlockOptionsImpl::from_yaml("test_diffusion.yaml");
  EXPECT_TRUE(options->is_wall_boundary(0, 0, -1));
  EXPECT_TRUE(options->is_wall_boundary(0, 0, 1));

  for (std::string name : {"periodic", "outflow", "custom"}) {
    options->bfuncs()[BoundaryFace::kInnerX1] =
        get_bc_func().at(name + "_inner");
    options->bcnames()[BoundaryFace::kInnerX1] = name + "_inner";
    EXPECT_FALSE(options->is_wall_boundary(0, 0, -1)) << name;
    EXPECT_TRUE(options->is_physical_boundary(0, 0, -1)) << name;
  }

  options->bfuncs()[BoundaryFace::kInnerX1] = get_bc_func().at("solid_inner");
  options->bcnames()[BoundaryFace::kInnerX1] = "solid_inner";
  EXPECT_TRUE(options->is_wall_boundary(0, 0, -1));

  // an unnamed function, e.g. one installed from Python, is not a wall
  options->bcnames()[BoundaryFace::kInnerX1] = "";
  EXPECT_FALSE(options->is_wall_boundary(0, 0, -1));

  // and neither is anything once the two records disagree in length
  options->bcnames().clear();
  EXPECT_FALSE(options->is_wall_boundary(0, 0, 1));
}

// ISSUES S39. InternalBoundary fills solid cells with placeholder primitives
// (solid-density 1e3, solid-pressure 1e9) so the Riemann path treats them as a
// wall. A uniform fluid has zero diffusive tendency everywhere; if the operator
// reads those placeholders it injects a huge spurious flux into the fluid cells
// flanking the solid.
TEST_P(DeviceTest, solid_interface_carries_no_diffusive_flux) {
  auto block = make_block();
  block->to(device, dtype);
  auto w = make_primitive(block, device, dtype);
  // a uniform TANGENTIAL wind: mark_prim_solid_ zeroes it inside the solid, so
  // the solid/fluid faces also carry a shear the viscous branch must refuse.
  // v1 stays zero, so div_vel is identically zero and cannot confound this.
  w[IVY] = 3.0;

  auto solid = torch::zeros(
      {block->pcoord->options->nc3(), block->pcoord->options->nc2(),
       block->pcoord->options->nc1()},
      torch::device(device).dtype(torch::kBool));
  int nghost = block->pcoord->options->nghost();
  solid.narrow(2, nghost + 2, 2).fill_(true);

  block->pib->mark_prim_solid_(w, solid);
  auto temp = block->phydro->peos->compute("W->T", {w});
  block->phydro->pdiffusion->solid = solid;

  auto du = torch::zeros_like(w);
  block->phydro->pdiffusion->forward(du, w, temp, 0.1);

  auto interior = block->part({0, 0, 0}, PartOptions().exterior(false).ndim(3));
  for (int n = 0; n < 5; ++n) {
    auto got = du[n].index(interior);
    EXPECT_TRUE(torch::allclose(got, torch::zeros_like(got), 1.e-8, 1.e-8))
        << "du[" << n << "] over the interior: " << got;
  }
}

TEST_P(DeviceTest, timestep_uses_largest_diffusivity) {
  auto block = make_block();
  block->to(device, dtype);
  auto w = make_primitive(block, device, dtype);
  EXPECT_NEAR(block->phydro->pdiffusion->max_time_step(w), 1., 1.e-12);

  w[IPR] = 1.e-6;
  EXPECT_NEAR(block->phydro->max_time_step(w), 1., 1.e-6);
}
