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

#include <snap/hydro/hydro.hpp>
#include <snap/mesh/meshblock.hpp>

using namespace snap;

namespace {
MeshBlock make_block() {
  char fname[] = "/tmp/test-shallow-water-limiter-XXXXXX";
  int fd = mkstemp(fname);
  EXPECT_NE(fd, -1);
  if (fd != -1) close(fd);
  std::ofstream(fname) << R"(
geometry:
  type: cartesian
  bounds: {x1min: -10., x1max: 10., x2min: -5, x2max: 5.}
  cells: {nx1: 8, nx2: 4, nx3: 1, nghost: 3}
dynamics:
  equation-of-state: {type: shallow-water, limiter: true}
  reconstruct:
    vertical: {type: weno5, scale: false, shock: false}
    horizontal: {type: weno5, scale: false, shock: false}
  riemann-solver: {type: shallow-roe, dir: xy}
boundary-condition:
  external:
    x1-inner: periodic
    x1-outer: periodic
    x2-inner: periodic
    x2-outer: periodic
integration: {type: rk3, cfl: 0.9}
)";
  auto options = MeshBlockOptionsImpl::from_yaml(fname);
  std::remove(fname);
  return MeshBlock(options);
}
}  // namespace

// A shallow-water state has four rows (no energy, no species): the primitive
// limiter must floor the depth and leave rows IPR and ICY alone.
TEST(ShallowWaterLimiter, converts_with_limiter_on) {
  auto block = make_block();
  auto eos = block->phydro->peos;
  ASSERT_TRUE(eos->options->limiter());
  ASSERT_EQ(eos->nvar(), 4);
  auto pc = block->pcoord->options;
  auto w = torch::zeros({4, pc->nc3(), pc->nc2(), pc->nc1()}, torch::kFloat64);
  w[IDN].fill_(10.);
  w[IVX].fill_(1.);
  w[IVY].fill_(-2.);

  torch::Tensor u, w2;
  EXPECT_NO_THROW(u = eos->compute("W->U", {w.clone()}));
  ASSERT_TRUE(u.defined());
  EXPECT_TRUE(torch::allclose(u[IVX], 10. * w[IVX]));
  EXPECT_TRUE(torch::allclose(u[IVY], 10. * w[IVY]));
  EXPECT_NO_THROW(w2 = eos->forward(u));
  ASSERT_TRUE(w2.defined());
  EXPECT_TRUE(torch::allclose(w2, w));
}
