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
  char fname[] = "/tmp/test-ideal-gas-cons2prim-layout-XXXXXX";
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
    type: ideal-gas
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
  auto block = MeshBlock(options);
  block->to(torch::kCPU, torch::kFloat64);
  return block;
}

torch::Tensor make_cons(MeshBlock const& block) {
  auto pc = block->pcoord->options;
  auto cons = torch::rand({block->phydro->peos->nvar(), pc->nc3(), pc->nc2(),
                           pc->nc1()},
                          torch::kFloat64);
  cons[IDN].add_(1.);
  cons[IPR].mul_(1.e5).add_(1.e5);
  return cons;
}
}  // namespace

// cons is a view with a wider row stride than the prim it is converted into
TEST(IdealGasCons2Prim, reads_cons_with_its_own_row_stride) {
  auto block = make_block();
  auto eos = block->phydro->peos;
  auto cons = make_cons(block);
  auto ref = eos->compute("U->W", {cons.clone()});

  auto sizes = cons.sizes().vec();
  sizes.back() += 3;
  auto wide = torch::zeros(sizes, cons.options());
  auto view = wide.narrow(-1, 0, cons.size(-1));
  view.copy_(cons);
  auto prim = torch::empty_like(cons);
  ASSERT_NE(view.stride(0), prim.stride(0));
  eos->compute("U->W", {view, prim});
  EXPECT_TRUE(torch::allclose(prim, ref, 1.e-12, 1.e-12))
      << "max error " << (prim - ref).abs().max().item<double>();
}

// a float64 cons converted into a float32 prim: values, not reinterpreted bits
TEST(IdealGasCons2Prim, reads_cons_in_its_own_dtype) {
  auto block = make_block();
  auto eos = block->phydro->peos;
  auto cons = make_cons(block);
  auto ref = eos->compute("U->W", {cons.clone()});

  auto prim = torch::empty_like(cons, torch::kFloat32);
  try {
    eos->compute("U->W", {cons, prim});
  } catch (c10::Error const&) {
    return;  // refusing the mismatch is also correct
  }
  EXPECT_TRUE(torch::allclose(prim.to(torch::kFloat64), ref, 1.e-5, 1.e-5))
      << "max error " << (prim.to(torch::kFloat64) - ref).abs().max().item<double>();
}
