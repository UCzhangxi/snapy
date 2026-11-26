// C/C++
#include <cstdio>
#include <fstream>

// POSIX
#include <unistd.h>

// external
#include <gtest/gtest.h>

// torch
#include <torch/torch.h>

// snap
#include <snap/snap.h>

#include <snap/eos/aneos/aneos_thermo.hpp>
#include <snap/hydro/hydro.hpp>
#include <snap/mesh/meshblock.hpp>

using namespace snap;

// A stand-in for the ANEOS table (the library ships weak stubs that throw):
// an ideal gas with a fixed adiabatic index.
namespace {
constexpr double kR = 287.;
constexpr double kGamma = 1.4;
}  // namespace

namespace snap {
ANEOSThermoImpl::ANEOSThermoImpl(const std::string& fname) : filename(fname) {}
void ANEOSThermoImpl::reset() {}
void ANEOSThermoImpl::pretty_print(std::ostream& os) const {
  os << "test ANEOS stand-in";
}
std::tuple<torch::Tensor, torch::Tensor, torch::Tensor>
ANEOSThermoImpl::compute(std::string ab,
                         std::vector<torch::Tensor> const& args) {
  auto rho = args[0];
  if (ab == "DP->TUL") {
    auto p = args[1];
    return {p / (rho * kR), p / (kGamma - 1.), torch::sqrt(kGamma * p / rho)};
  } else if (ab == "DU->PTL") {
    auto p = (kGamma - 1.) * args[1];
    return {p, p / (rho * kR), torch::sqrt(kGamma * p / rho)};
  } else if (ab == "DT->PUL") {
    auto p = rho * kR * args[1];
    return {p, p / (kGamma - 1.), torch::sqrt(kGamma * p / rho)};
  }
  TORCH_CHECK(false, "test ANEOS stand-in: unknown ", ab);
}
}  // namespace snap

namespace {
MeshBlock make_block() {
  char fname[] = "/tmp/test-aneos-metric-XXXXXX";
  int fd = mkstemp(fname);
  EXPECT_NE(fd, -1);
  if (fd != -1) close(fd);
  std::ofstream(fname) << R"(
geometry:
  type: gnomonic-equiangle
  cells: {nx1: 1, nx2: 6, nx3: 6, nghost: 2}
  bounds: {x1min: 1., x1max: 2., x2min_pi: -0.25, x2max_pi: 0.25, x3min_pi: -0.25, x3max_pi: 0.25}
distribute:
  layout: slab
  nb2: 1
  nb3: 1
  verbose: false
dynamics:
  equation-of-state: {type: aneos, eos-file: stand-in, limiter: false}
boundary-condition:
  external:
    x1-inner: reflecting
    x1-outer: reflecting
    x2-inner: custom
    x2-outer: custom
    x3-inner: custom
    x3-outer: custom
)";
  auto options = MeshBlockOptionsImpl::from_yaml(fname);
  std::remove(fname);
  return MeshBlock(options);
}
}  // namespace

// On a gnomonic panel the momenta are covariant, rho (v2 + cos v3), and the
// kinetic energy carries the cross term rho cos v2 v3, as in ideal-gas.
TEST(AneosMetric, gnomonic_momentum_and_energy_use_the_metric) {
  auto block = make_block();
  auto eos = block->phydro->peos;
  ASSERT_EQ(eos->options->type(), "aneos");
  auto pc = block->pcoord->options;
  auto opts = torch::TensorOptions().dtype(torch::kFloat64);
  auto w = torch::zeros({eos->nvar(), pc->nc3(), pc->nc2(), pc->nc1()}, opts);
  double rho = 1.3, v1 = 3., v2 = 10., v3 = 20., p = 1.e5;
  w[IDN].fill_(rho);
  w[IVX].fill_(v1);
  w[IVY].fill_(v2);
  w[IVZ].fill_(v3);
  w[IPR].fill_(p);
  auto c = block->pcoord->cosine_cell_kj.to(opts).expand_as(w[IDN]);
  ASSERT_GT(c.abs().max().item<double>(), 0.05) << "no off-diagonal metric";

  auto u = eos->compute("W->U", {w.clone()});
  auto ke = 0.5 * rho * (v1 * v1 + v2 * v2 + v3 * v3 + 2. * c * v2 * v3);
  EXPECT_TRUE(torch::allclose(u[IVY], rho * (v2 + c * v3), 1.e-12, 1.e-12))
      << "momentum 2 is not lowered";
  EXPECT_TRUE(torch::allclose(u[IVZ], rho * (v3 + c * v2), 1.e-12, 1.e-12))
      << "momentum 3 is not lowered";
  EXPECT_TRUE(torch::allclose(u[IPR], p / (kGamma - 1.) + ke, 1.e-12, 1.e-9))
      << "energy misses the cross term: max error "
      << (u[IPR] - p / (kGamma - 1.) - ke).abs().max().item<double>();

  // the inverse raises the velocities back
  auto w2 = eos->forward(u);
  EXPECT_TRUE(torch::allclose(w2, w, 1.e-12, 1.e-9));
}
