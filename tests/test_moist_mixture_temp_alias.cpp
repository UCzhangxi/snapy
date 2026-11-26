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
  char fname[] = "/tmp/test-moist-mixture-temp-alias-XXXXXX";
  int fd = mkstemp(fname);
  EXPECT_NE(fd, -1);
  if (fd != -1) close(fd);
  std::ofstream(fname) << R"(
reference-state: {Tref: 300., Pref: 1.e5}
species:
  - name: dry
    composition: {O: 0.42, N: 1.56, Ar: 0.01}
    cv_R: 2.5
geometry:
  type: cartesian
  bounds: {x1min: 0., x1max: 1., x2min: 0., x2max: 1., x3min: 0., x3max: 1.}
  cells: {nx1: 8, nx2: 6, nx3: 4, nghost: 1}
dynamics:
  equation-of-state:
    type: moist-mixture
    density-floor:  1.e-10
    pressure-floor: 1.e-10
    limiter: false
boundary-condition:
  external:
    x1-inner: reflecting
    x1-outer: reflecting
    x2-inner: reflecting
    x2-outer: reflecting
    x3-inner: reflecting
    x3-outer: reflecting
)";
  auto options = MeshBlockOptionsImpl::from_yaml(fname);
  std::remove(fname);
  return MeshBlock(options);
}
}  // namespace

// The temperature handed to a caller is the caller's: a later W->T on another
// state must not overwrite it through the closure's cache.
TEST(MoistMixtureTemp, result_survives_the_next_call) {
  auto block = make_block();
  block->to(torch::kCPU, torch::kFloat64);
  auto eos = block->phydro->peos;
  ASSERT_EQ(eos->options->type(), "moist-mixture");
  auto pc = block->pcoord->options;
  auto cons = torch::empty({eos->nvar(), pc->nc3(), pc->nc2(), pc->nc1()},
                           torch::kFloat64);
  cons.uniform_(0., 1.);
  cons[IDN].add_(1.);
  cons[IPR].mul_(1.e5).add_(1.e5);
  cons[IPR] += 0.5 * cons.narrow(0, IVX, 3).pow(2).sum(0) / cons[IDN];
  auto prim = eos->forward(cons);

  auto t1 = eos->compute("W->T", {prim});
  auto t1_copy = t1.clone();
  auto prim2 = prim.clone();
  prim2[IPR].mul_(1.25);
  auto t2 = eos->compute("W->T", {prim2});

  ASSERT_FALSE(torch::allclose(t2, t1_copy)) << "the two states coincide";
  EXPECT_TRUE(torch::equal(t1, t1_copy))
      << "the first temperature was overwritten: max change "
      << (t1 - t1_copy).abs().max().item<double>() << " K";
}
