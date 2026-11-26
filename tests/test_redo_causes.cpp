// gtest
#include <gtest/gtest.h>

// external
#include <yaml-cpp/yaml.h>

// C/C++
#include <cstdio>
#include <fstream>

// snap
#include <snap/mesh/meshblock.hpp>

using namespace snap;

// The retry word has the six causes apply_redo names (floor, clamp, limiter,
// nan, saturation, vic-solve), and every one of them has a slot in the flag
// tensor that local_redo_flag_tensor builds. A cause bit no slot can set is
// dead: read_redo_flags must not grow one for a slot that is never stacked.
TEST(redo_causes, every_cause_bit_has_a_flag_slot) {
  auto node = YAML::Load(R"(
geometry:
  type: cartesian
  cells: {nx1: 8, nx2: 4, nx3: 1, nghost: 3}
  bounds: {x1min: 0, x1max: 8, x2min: 0, x2max: 4, x3min: 0, x3max: 1}
dynamics:
  equation-of-state: {type: ideal-gas, gammad: 1.4, weight: 0.029}
  reconstruct:
    vertical: {type: plm}
    horizontal: {type: plm}
  riemann-solver: {type: lmars}
integration: {type: rk3, cfl: 0.5}
boundary-condition:
  external: {x1-inner: reflecting, x1-outer: reflecting,
             x2-inner: periodic, x2-outer: periodic,
             x3-inner: periodic, x3-outer: periodic}
)");
  std::string path = "test-redo-causes.yaml";
  {
    std::ofstream card(path);
    card << node;
  }
  auto block = MeshBlock(MeshBlockOptionsImpl::from_yaml(path));
  std::remove(path.c_str());
  auto coord = block->pcoord;
  auto w = torch::zeros(
      {5, coord->options->nc3(), coord->options->nc2(), coord->options->nc1()},
      torch::kFloat64);
  w[IDN].fill_(1.);
  w[IPR].fill_(1.e5);
  Variables vars{{"hydro_w", w}};
  block->initialize(vars);

  auto flags = block->local_redo_flag_tensor(vars);
  ASSERT_EQ(flags.dim(), 1);
  int64_t nslot = flags.size(0);
  EXPECT_EQ(nslot, 8);
  // a resting, floor-free state flags nothing
  EXPECT_EQ(flags.abs().sum().item<double>(), 0.);

  auto none = MeshBlockImpl::read_redo_flags(flags);
  EXPECT_EQ(none.size(), 6u) << "one bit per cause apply_redo names";

  // each slot the block stacks sets exactly one of those bits
  std::vector<int> hit(none.size(), 0);
  for (int64_t s = 0; s < nslot; ++s) {
    auto one = torch::zeros_like(flags);
    one[s] = 1.;
    auto bits = MeshBlockImpl::read_redo_flags(one);
    int n = 0;
    for (size_t b = 0; b < bits.size(); ++b)
      if (bits[b]) {
        ++n;
        ++hit[b];
      }
    EXPECT_EQ(n, 1) << "slot " << s;
  }
  // and every bit is reachable from some slot
  for (size_t b = 0; b < hit.size(); ++b)
    EXPECT_GT(hit[b], 0) << "cause bit " << b << " has no slot";
}
