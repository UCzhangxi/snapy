// C/C++
#include <string>

// external
#include <gtest/gtest.h>

// snap
#include <snap/snap.h>

#include <snap/hydro/hydro.hpp>
#include <snap/mesh/meshblock.hpp>

using namespace snap;

namespace {
//! build a uniform block and return the ke it logs
double logged_ke(double rho, double vx, double vy, bool double_momentum) {
  auto options = MeshBlockOptionsImpl::from_yaml("test_gravity_energy.yaml");
  auto block = std::make_shared<MeshBlockImpl>(options);
  auto coord = block->pcoord;

  auto w = torch::zeros({block->phydro->peos->nvar(), coord->options->nc3(),
                         coord->options->nc2(), coord->options->nc1()},
                        torch::kFloat64);
  w[IDN].fill_(rho);
  w[IVX].fill_(vx);
  w[IVY].fill_(vy);
  w[IPR].fill_(1.e5);

  Variables vars;
  vars["hydro_w"] = w;
  block->initialize(vars);
  block->pintg->options->ncycle_out(1);

  // a real cycle advances u only; hydro_w is a stage stale at print time
  if (double_momentum) {
    vars.at("hydro_u").narrow(0, IVX, 3).mul_(2.);
    vars.at("hydro_w").zero_();  // print_cycle_info must read u alone
  }

  testing::internal::CaptureStdout();
  block->print_cycle_info(vars, 0., 1.);
  std::string out = testing::internal::GetCapturedStdout();

  auto pos = out.find("ke=");
  EXPECT_NE(pos, std::string::npos) << out;
  if (pos == std::string::npos) return 0.;
  return std::stod(out.substr(pos + 3));
}
}  // namespace

TEST(cycle_info, logged_ke_scales_with_density) {
  double ke1 = logged_ke(2.5, 3., 4., false);
  double ke2 = logged_ke(5.0, 3., 4., false);
  ASSERT_GT(ke1, 0.);
  EXPECT_NEAR(ke2, 2. * ke1, 1.e-9 * ke2)
      << "ke(rho=2.5)=" << ke1 << " ke(rho=5.0)=" << ke2;
}

TEST(cycle_info, logged_ke_reads_the_conserved_state) {
  double ke0 = logged_ke(2.5, 3., 4., false);
  double ke2 = logged_ke(2.5, 3., 4., true);
  ASSERT_GT(ke0, 0.);
  // ke = |p|^2/2rho quadruples; reading the zeroed hydro_w would log NaN
  EXPECT_NEAR(ke2, 4. * ke0, 1.e-9 * ke2)
      << "ke=" << ke0 << " after doubling momentum=" << ke2;
}
