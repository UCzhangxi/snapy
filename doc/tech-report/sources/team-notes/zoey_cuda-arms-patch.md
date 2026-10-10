# CUDA arms for the checks added since aea71ed (snapy, one patch on caa1833)

Nothing pushed or posted. No build or ctest was run for this export. The GPU and skip results below come from the earlier **incremental** CUDA build. The clean CUDA build on caa1833 was stopped partway, as Xi asked, so there is no full ctest on caa1833.

| item | value |
|---|---|
| commit | `d7132f659151d3334dd01d01c02fa0ed90debef8` |
| parent | `caa1833b4266b83e11e31961547942c3d098fe9a` (UCzhangxi next/x1-wall-closure) |
| tree | `48d015888e9aa41ba4c191a4d07ccea4af7e1442` |
| author | Zoey Hu <hzin@umich.edu>; no AI, Co-authored-by or Signed-off trailers |
| file | `0001-test-CUDA-arms-for-the-checks-added-since-aea71ed.patch` |
| size | 23690 bytes (re-run of `git format-patch -1 d7132f6`; identical to the earlier 23690 B file, checked with `cmp`) |
| sha256 | `ffb01f7dd2315fd64bcba3a179ba8f9abe22f74b6e9a6a3ebc4768f038bb04ed` (matches the earlier value) |
| git am | applied cleanly to a fresh scratch worktree at caa1833 (rc 0); resulting tree `48d01588…` equals d7132f6's tree; scratch worktree removed |
| files, +/- | tests/CMakeLists.txt +21/-0; test_balance_column.cpp +30/-4; test_diffusion_x1_scale.cpp +44/-10; test_face_floor.cpp +18/-0; test_gravity_work_radial_exact.py +5/-2; test_wb_ref_wall.cpp +21/-0; test_x1_seam_split.cpp +59/-24; total 7 files +198/-40 |

Per-arm results. These are from the **incremental** CUDA build on an RTX 5090. For the GPU column, `CUDA_VISIBLE_DEVICES=0`. For the no-GPU column, `CUDA_VISIBLE_DEVICES=` (empty).

| new arm | GPU | no GPU visible | command |
|---|---|---|---|
| test_x1_seam_split: _x1_centroid_cuda, _radial_exact_cuda, _radial_exact_off_cuda, _wb_ref4_cuda (4 ctest entries) | 4/4 passed; seam gaps 0 to 5.8e-15, E+P drift ≤ 4.7e-15 with the switch on | 4/4 ctest Skipped | `ctest -j1 -R 'test_x1_seam_split'` |
| test_balance_column: a_marched_column_comes_out_at_rest_cuda, x1_centroid_switch_balances_only_a_cartesian_column_cuda (in the default, SNAP_WB_REF4=1 and SNAP_X1_CENTROID_EXACT=1 entries) | passed in all 3 envs | 2 SKIPPED | `[env] ./test_balance_column.release --gtest_filter='*cuda*'` |
| test_face_floor: face_floor_fires_on_an_unresolved_column_cuda (GPU vs CPU parity, rel tol 1e-5; the pinned CPU assertion is untouched) | passed in all 3 envs; 2.8319e-08 on CUDA and CPU | SKIPPED | `[env] ./test_face_floor.release --gtest_filter='*unresolved*cuda*'` |
| test_wb_ref_wall: order_table_cuda_matches_cpu (beta 0.5 and 0, nz 16-128, tol 1e-13) | passed; max abs CUDA-CPU difference 4.44e-16 | SKIPPED | `./test_wb_ref_wall.release --gtest_filter='*cuda*'` |
| test_diffusion_x1_scale: constant_dynamic_coefficient_column_has_no_tendency_cuda, smooth_profile_flux_converges_at_second_order_cuda | 2/2 passed | 2 SKIPPED | `./test_diffusion_x1_scale.release --gtest_filter='diffusion_x1_scale.*'` |
| test_gravity_work_radial_exact_cuda_python (`--device cuda`, exit 125 without CUDA) | passed (19.0 s) | ctest Skipped | `ctest -j1 -R test_gravity_work_radial_exact` |

The skip-path ctest run also showed the existing test_wb_ref4_order_cuda_python and test_x1_centroid_rest_cuda_python as Skipped.

To save the patch from this file: copy everything between the ```` ```diff ```` line and the closing fence, and add one trailing newline. The patch ends with git's version line followed by one blank line. That gives the 23690 bytes and the sha256 above.

## 0001-test-CUDA-arms-for-the-checks-added-since-aea71ed.patch

```diff
From d7132f659151d3334dd01d01c02fa0ed90debef8 Mon Sep 17 00:00:00 2001
From: Zoey Hu <hzin@umich.edu>
Date: Fri, 9 Oct 2026 22:39:25 -0400
Subject: [PATCH] test: CUDA arms for the checks added since aea71ed

Each check added or extended since aea71ed that ran on the CPU only now
also runs on the GPU, with the same oracle and tolerance, and skips when
CUDA is not available. The CPU arms run as before.
- test_x1_seam_split: centroid_exact, radial_exact (on and the off
  control) and wb_ref4 arms on CUDA, one ctest entry each; the entry
  reports a skip, not a failure, without a GPU (SKIP_REGULAR_EXPRESSION)
- test_balance_column: a_marched_column_comes_out_at_rest (the
  SNAP_WB_REF4 audit included) and
  x1_centroid_switch_balances_only_a_cartesian_column on CUDA, in all
  three entries (default, _wb_ref4, _x1_centroid)
- test_face_floor: the unresolved column on CUDA gives the CPU's
  dipped-face mass flux, to the CPU check's relative tolerance 1e-5;
  the pinned CPU value itself is not touched
- test_wb_ref_wall: the order table's face errors on CUDA match the CPU
  to 1e-13 (measured 4.4e-16), beta 0.5 and 0, nz 16-128
- test_diffusion_x1_scale: the constant dynamic coefficient and the
  second-order flux checks on CUDA
- test_gravity_work_radial_exact: --device cuda, exit 125 (skip) without
  CUDA; registered as test_gravity_work_radial_exact_cuda_python
---
 tests/CMakeLists.txt                    | 21 +++++++
 tests/test_balance_column.cpp           | 34 ++++++++--
 tests/test_diffusion_x1_scale.cpp       | 54 +++++++++++++---
 tests/test_face_floor.cpp               | 18 ++++++
 tests/test_gravity_work_radial_exact.py |  7 ++-
 tests/test_wb_ref_wall.cpp              | 21 +++++++
 tests/test_x1_seam_split.cpp            | 83 ++++++++++++++++++-------
 7 files changed, 198 insertions(+), 40 deletions(-)

diff --git a/tests/CMakeLists.txt b/tests/CMakeLists.txt
index 628aa87..bded03a 100644
--- a/tests/CMakeLists.txt
+++ b/tests/CMakeLists.txt
@@ -54,6 +54,23 @@ seam_arm(_radial_exact_off "SNAP_GRAVITY_WORK_RADIAL_EXACT=0"
 # SNAP_WB_REF4 alone: its resolution flag switching on next to the seam
 seam_arm(_wb_ref4 "SNAP_WB_REF4=1"
          wb_ref4_flag_at_the_seam_split_matches_one_block)
+if(CUDA)
+  # the same arms on the GPU; without one the test skips and so does the entry
+  seam_arm(_x1_centroid_cuda "SNAP_X1_CENTROID_EXACT=1"
+           centroid_exact_split_matches_one_block_cuda)
+  seam_arm(_radial_exact_cuda "SNAP_GRAVITY_WORK_RADIAL_EXACT=1"
+           radial_exact_split_gap_cuda)
+  seam_arm(_radial_exact_off_cuda "SNAP_GRAVITY_WORK_RADIAL_EXACT=0"
+           radial_exact_split_gap_cuda)
+  seam_arm(_wb_ref4_cuda "SNAP_WB_REF4=1"
+           wb_ref4_flag_at_the_seam_split_matches_one_block_cuda)
+  foreach(_a _x1_centroid_cuda _radial_exact_cuda _radial_exact_off_cuda
+             _wb_ref4_cuda)
+    set_tests_properties(
+      test_x1_seam_split${_a}.${buildl}
+      PROPERTIES SKIP_REGULAR_EXPRESSION "\\[  SKIPPED \\] 1 test")
+  endforeach()
+endif()
 setup_test(test_wb_wall_corner)
 setup_test(test_face_floor)
 setup_test(test_wb_ref_wall)
@@ -246,6 +263,9 @@ if(CUDA)
   snapy_add_python_test(test_x1_centroid_rest_cuda
     SCRIPT test_x1_centroid_rest.py ARGS --device cuda
     TIMEOUT 300 LABELS "python;hydro;cuda")
+  snapy_add_python_test(test_gravity_work_radial_exact_cuda
+    SCRIPT test_gravity_work_radial_exact.py ARGS --device cuda
+    TIMEOUT 300 LABELS "python;hydro;gravity;cuda")
   set_tests_properties(
     test_fix_vapor_reports_failure_cuda_python
     test_check_redo_saturation_cuda_python
@@ -254,6 +274,7 @@ if(CUDA)
     test_vic_moist_device_python
     test_wb_ref4_order_cuda_python
     test_x1_centroid_rest_cuda_python
+    test_gravity_work_radial_exact_cuda_python
     PROPERTIES SKIP_RETURN_CODE 125)
 endif()

diff --git a/tests/test_balance_column.cpp b/tests/test_balance_column.cpp
index fb13a1f..7f1da84 100644
--- a/tests/test_balance_column.cpp
+++ b/tests/test_balance_column.cpp
@@ -6,6 +6,8 @@
 // gtest
 #include <gtest/gtest.h>

+#include "cuda_test_gate.hpp"
+
 // torch
 #include <torch/torch.h>

@@ -208,10 +210,15 @@ TEST(BalanceColumn, without_the_clamp_the_two_references_disagree) {
   EXPECT_FALSE(torch::equal(free_ref.pref, blk_ref.pref.narrow(-1, 3, nx1)));
 }

-TEST(BalanceColumn, a_marched_column_comes_out_at_rest) {
+//! the column on `device`
+Column on(Column const& c, torch::Device device) {
+  return {c.w.to(device), c.dx1f.to(device)};
+}
+
+void a_marched_column_comes_out_at_rest(torch::Device device) {
   constexpr double rtol = 1.e-10;
   for (bool uniform : {true, false}) {
-    auto c = marched_column(64, 3.0e5, uniform);
+    auto c = on(marched_column(64, 3.0e5, uniform), device);
     double before = residual(c, uniform);
     EXPECT_GT(before, 1.e-4)
         << "the fixture is not the defect: uniform=" << uniform;
@@ -226,6 +233,15 @@ TEST(BalanceColumn, a_marched_column_comes_out_at_rest) {
   }
 }

+TEST(BalanceColumn, a_marched_column_comes_out_at_rest) {
+  a_marched_column_comes_out_at_rest(torch::kCPU);
+}
+
+TEST(BalanceColumn, a_marched_column_comes_out_at_rest_cuda) {
+  if (!snapy_cuda_test_enabled()) GTEST_SKIP() << "CUDA is not available";
+  a_marched_column_comes_out_at_rest(torch::Device(torch::kCUDA, 0));
+}
+
 // The final permitted update must be checked before declaring non-convergence.
 TEST(BalanceColumn, the_last_allowed_update_can_converge) {
   constexpr double rtol = 1.e-10;
@@ -343,8 +359,8 @@ TEST(BalanceColumn, x1_centroid_switch_implies_the_ref4_predicate) {
 // under SNAP_X1_CENTROID_EXACT a spherical-polar column's reference converts
 // r^2 means to plain means, which this planar column does not model: only a
 // column declared cartesian is balanced, anything else is refused
-TEST(BalanceColumn, x1_centroid_switch_balances_only_a_cartesian_column) {
-  auto c = marched_column(64, 3.0e5, /*uniform=*/true);
+void x1_centroid_switch_balances_only_a_cartesian_column(torch::Device device) {
+  auto c = on(marched_column(64, 3.0e5, /*uniform=*/true), device);
   auto run = [&](char const* geometry) {
     snap::balance_column(c.w, c.dx1f, kGrav, true, 1.e-10, 120, geometry);
   };
@@ -364,4 +380,14 @@ TEST(BalanceColumn, x1_centroid_switch_balances_only_a_cartesian_column) {
     }
 }

+TEST(BalanceColumn, x1_centroid_switch_balances_only_a_cartesian_column) {
+  x1_centroid_switch_balances_only_a_cartesian_column(torch::kCPU);
+}
+
+TEST(BalanceColumn, x1_centroid_switch_balances_only_a_cartesian_column_cuda) {
+  if (!snapy_cuda_test_enabled()) GTEST_SKIP() << "CUDA is not available";
+  x1_centroid_switch_balances_only_a_cartesian_column(
+      torch::Device(torch::kCUDA, 0));
+}
+
 }  // namespace
diff --git a/tests/test_diffusion_x1_scale.cpp b/tests/test_diffusion_x1_scale.cpp
index bb47342..6e8ef14 100644
--- a/tests/test_diffusion_x1_scale.cpp
+++ b/tests/test_diffusion_x1_scale.cpp
@@ -151,9 +151,11 @@ torch::Tensor stratified_rho(torch::Tensor const& x) {
 }

 //! test_diffusion.yaml's column (reflecting x1 walls) on nx1 cells over
-//! [0, 1], both kinematic coefficients scaled by `scale` of the x1 centres
+//! [0, 1], both kinematic coefficients scaled by `scale` of the x1 centres;
+//! on a CUDA device it is moved there in double precision
 std::shared_ptr<MeshBlockImpl> scaled_column(
-    int nx1, std::function<torch::Tensor(torch::Tensor const&)> const& scale) {
+    int nx1, std::function<torch::Tensor(torch::Tensor const&)> const& scale,
+    torch::Device device = torch::kCPU) {
   auto options = base_options();
   options->coord()->global_nx1() = nx1;
   options->coord()->nx1() = nx1;
@@ -162,11 +164,14 @@ std::shared_ptr<MeshBlockImpl> scaled_column(
   auto s = scale(build(options)->pcoord->x1v.to(torch::kFloat64));
   options->hydro()->diffusion()->nu_scale_x1(s);
   options->hydro()->diffusion()->kappa_scale_x1(s.clone());
-  return build(options);
+  auto block = build(options);
+  if (device.is_cuda()) block->to(device, torch::kFloat64);
+  return block;
 }

 //! interior tendency (dt = 1) of the stratified column, at rest with
-//! temperature `field` (heat) or at 300 K with v2 = `field` (shear); cv out
+//! temperature `field` (heat) or at 300 K with v2 = `field` (shear); cv out;
+//! the tendency is returned on the CPU
 torch::Tensor stratified_tendency(std::shared_ptr<MeshBlockImpl> const& block,
                                   torch::Tensor const& field, bool heat,
                                   double* cv) {
@@ -175,7 +180,7 @@ torch::Tensor stratified_tendency(std::shared_ptr<MeshBlockImpl> const& block,
   auto x = coord->x1v.to(torch::kFloat64).view({1, 1, -1});
   auto w = torch::zeros(
       {5, coord->options->nc3(), coord->options->nc2(), coord->options->nc1()},
-      torch::kFloat64);
+      x.options());
   w[IDN] = stratified_rho(x);
   auto temp = (heat ? field : 300. + 0. * x).expand_as(w[IDN]).clone();
   if (!heat) w[IVY] = field;
@@ -185,7 +190,7 @@ torch::Tensor stratified_tendency(std::shared_ptr<MeshBlockImpl> const& block,
   auto du = torch::zeros_like(w);
   block->phydro->pdiffusion->forward(du, w, temp, 1.);
   auto interior = block->part({0, 0, 0}, PartOptions().exterior(false).ndim(3));
-  return du[heat ? IPR : IVY].index(interior).reshape(-1);
+  return du[heat ? IPR : IVY].index(interior).reshape(-1).cpu();
 }

 }  // namespace
@@ -363,6 +368,8 @@ TEST(diffusion_x1_scale, linear_profile_gives_the_analytic_tendency) {
   EXPECT_TRUE(torch::allclose(heat, 0.025 * cv * shape, 1.e-12, 0.)) << heat;
 }

+namespace {
+
 // A constant DYNAMIC coefficient over a stratified column: s = 1/rho makes
 // mu = nu s rho and k = kappa s rho cv uniform, so a linear T at rest and a
 // linear v2 carry a uniform flux and no tendency in any cell. The face
@@ -371,10 +378,11 @@ TEST(diffusion_x1_scale, linear_profile_gives_the_analytic_tendency) {
 // gives an O(dx^2) tendency inside and an O(dx) one in the wall cells, whose
 // extrapolated wall face is exact (docs/derivations/
 // diffusion-face-coefficient.md).
-TEST(diffusion_x1_scale, constant_dynamic_coefficient_column_has_no_tendency) {
+void constant_dynamic_coefficient_column_has_no_tendency(torch::Device device) {
   for (int nx1 : {16, 64}) {
     auto block = scaled_column(
-        nx1, [](torch::Tensor const& x) { return 1. / stratified_rho(x); });
+        nx1, [](torch::Tensor const& x) { return 1. / stratified_rho(x); },
+        device);
     auto x = block->pcoord->x1v.to(torch::kFloat64).view({1, 1, -1});
     auto dx = 1. / nx1;
     double cv;
@@ -390,17 +398,32 @@ TEST(diffusion_x1_scale, constant_dynamic_coefficient_column_has_no_tendency) {
   }
 }

+}  // namespace
+
+TEST(diffusion_x1_scale, constant_dynamic_coefficient_column_has_no_tendency) {
+  constant_dynamic_coefficient_column_has_no_tendency(torch::kCPU);
+}
+
+TEST(diffusion_x1_scale,
+     constant_dynamic_coefficient_column_has_no_tendency_cuda) {
+  if (!snapy_cuda_test_enabled()) GTEST_SKIP() << "CUDA is not available";
+  constant_dynamic_coefficient_column_has_no_tendency(
+      torch::Device(torch::kCUDA, 0));
+}
+
+namespace {
+
 // A smooth variable coefficient, s = 1 + cos(3 x) / 2 on the stratified rho:
 // the face fluxes, recovered from the tendency by summing up from the lower
 // wall (F_{i+1/2} - F_{1/2} = -dx sum_{j <= i} du_j at dt = 1), converge to the
 // exact flux at second order, every face measured, the wall faces included.
-TEST(diffusion_x1_scale, smooth_profile_flux_converges_at_second_order) {
+void smooth_profile_flux_converges_at_second_order(torch::Device device) {
   auto s_of = [](torch::Tensor const& x) {
     return 1. + 0.5 * torch::cos(3. * x);
   };
   double prev[2] = {0., 0.};
   for (int nx1 : {32, 64, 128}) {
-    auto block = scaled_column(nx1, s_of);
+    auto block = scaled_column(nx1, s_of, device);
     auto x = block->pcoord->x1v.to(torch::kFloat64).view({1, 1, -1});
     auto dx = 1. / nx1;
     auto xf = torch::arange(nx1 + 1, torch::kFloat64) * dx;
@@ -429,6 +452,17 @@ TEST(diffusion_x1_scale, smooth_profile_flux_converges_at_second_order) {
   }
 }

+}  // namespace
+
+TEST(diffusion_x1_scale, smooth_profile_flux_converges_at_second_order) {
+  smooth_profile_flux_converges_at_second_order(torch::kCPU);
+}
+
+TEST(diffusion_x1_scale, smooth_profile_flux_converges_at_second_order_cuda) {
+  if (!snapy_cuda_test_enabled()) GTEST_SKIP() << "CUDA is not available";
+  smooth_profile_flux_converges_at_second_order(torch::Device(torch::kCUDA, 0));
+}
+
 // YAML knots on the cell centres give the profile set as a tensor, bit for bit
 TEST_P(DeviceTest, yaml_table_equals_the_cells_profile) {
   auto x1v = centres(base_options());
diff --git a/tests/test_face_floor.cpp b/tests/test_face_floor.cpp
index 6a76bef..a7aca68 100644
--- a/tests/test_face_floor.cpp
+++ b/tests/test_face_floor.cpp
@@ -121,3 +121,21 @@ TEST(hydro, face_floor_uses_adjacent_density_cuda) {
   if (!snapy_cuda_test_enabled()) GTEST_SKIP() << "CUDA is not available";
   face_floor_uses_adjacent_density(torch::Device(torch::kCUDA, 0));
 }
+
+// the unresolved column on the GPU floors the same face: its mass flux is the
+// CPU's, to the CPU check's relative tolerance (the CPU value is pinned above)
+TEST(hydro, face_floor_fires_on_an_unresolved_column_cuda) {
+  if (!snapy_cuda_test_enabled()) GTEST_SKIP() << "CUDA is not available";
+  auto dipped_mass = [](torch::Device device) {
+    auto block = dipped_column(device, 10.);
+    int dipped = block->pcoord->iu() - 1;
+    return block->phydro->flux1()[IDN].select(-1, dipped).item<double>();
+  };
+  double cpu = dipped_mass(torch::kCPU);
+  double cuda = dipped_mass(torch::Device(torch::kCUDA, 0));
+  std::printf(
+      "wb_ref4 %d, p = 10 e^{-x/2}: dipped face mass flux %.4e (CUDA)"
+      ", %.4e (CPU)\n",
+      static_cast<int>(HydroImpl::wb_ref4()), cuda, cpu);
+  EXPECT_NEAR(cuda, cpu, 1.e-5 * std::abs(cpu));
+}
diff --git a/tests/test_gravity_work_radial_exact.py b/tests/test_gravity_work_radial_exact.py
index 4f2e26e..966ebd0 100644
--- a/tests/test_gravity_work_radial_exact.py
+++ b/tests/test_gravity_work_radial_exact.py
@@ -30,7 +30,7 @@ g 1, depth 100) between closed (reflecting) x1 walls, seeded u1 = 0.05 c_s sin(p
   8. on, the VIC column with a 4-cell immersed solid block: per-step E + P over the fluid cells <= 1e-14.
 The switch is read once per process, so each arm runs in a child process.

-  python test_gravity_work_radial_exact.py [--device cpu]
+  python test_gravity_work_radial_exact.py [--device cpu|cuda]
 """
 import argparse
 import json
@@ -308,10 +308,13 @@ def child(out, device):

 def main():
     ap = argparse.ArgumentParser()
-    ap.add_argument("--device", default="cpu")
+    ap.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
     ap.add_argument("--child", default=None)
     ap.add_argument("--diag", default=None)
     a = ap.parse_args()
+    if a.device == "cuda" and not torch.cuda.is_available():
+        print("CUDA is not available")
+        sys.exit(125)
     torch.set_default_dtype(torch.float64)
     if a.diag:
         diag(a.diag, a.child, a.device)
diff --git a/tests/test_wb_ref_wall.cpp b/tests/test_wb_ref_wall.cpp
index 771a252..3af591d 100644
--- a/tests/test_wb_ref_wall.cpp
+++ b/tests/test_wb_ref_wall.cpp
@@ -264,6 +264,27 @@ TEST(WbRefWall, faces_next_to_the_walls_are_second_order_cuda) {
   faces_next_to_the_walls_are_second_order(torch::Device(torch::kCUDA, 0));
 }

+// The order table on the GPU: every face error the CPU reports, both profiles
+// and every resolution, to round-off
+TEST(WbRefWall, order_table_cuda_matches_cpu) {
+  if (!snapy_cuda_test_enabled()) GTEST_SKIP() << "CUDA is not available";
+  for (double beta : {0.5, 0.}) {
+    Profile prof{beta};
+    for (int nz : {16, 32, 64, 128}) {
+      auto a = face_errors(nz, prof);
+      auto b = face_errors(nz, prof, torch::Device(torch::kCUDA, 0));
+      for (auto [what, ea, eb] :
+           {std::tuple{"dsf", a.dsf, b.dsf}, std::tuple{"rho_L", a.rl, b.rl},
+            std::tuple{"rho_R", a.rr, b.rr}}) {
+        double d = (ea - eb).abs().max().item<double>();
+        std::printf("beta %g nz %3d %-5s max |CUDA - CPU| %.2e\n", beta, nz,
+                    what, d);
+        EXPECT_LE(d, 1.e-13) << "beta " << beta << " nz " << nz << " " << what;
+      }
+    }
+  }
+}
+
 int main(int argc, char** argv) {
   testing::InitGoogleTest(&argc, argv);
   return RUN_ALL_TESTS();
diff --git a/tests/test_x1_seam_split.cpp b/tests/test_x1_seam_split.cpp
index 658013e..0a41b09 100644
--- a/tests/test_x1_seam_split.cpp
+++ b/tests/test_x1_seam_split.cpp
@@ -23,6 +23,8 @@
 //
 // Each ctest entry (tests/CMakeLists.txt) runs one test with its switch set,
 // and passes only if that test ran and passed: a missing switch is a failure.
+// The _cuda tests are the same checks on the GPU; their entries report a skip
+// when CUDA is not available.

 // external
 #include <gtest/gtest.h>
@@ -40,6 +42,8 @@
 #include <torch/torch.h>
 #include <unistd.h>

+#include "cuda_test_gate.hpp"
+
 // snap
 #include <snap/snap.h>

@@ -95,7 +99,8 @@ boundary-condition:
   return buf;
 }

-Mesh make_column(int nb1, int nx1, double nh, char const* gw, int ng = 3) {
+Mesh make_column(int nb1, int nx1, double nh, char const* gw, int ng = 3,
+                 torch::Device device = torch::kCPU) {
   char fname[] = "/tmp/x1-seam-split-XXXXXX";
   int fd = mkstemp(fname);
   EXPECT_NE(fd, -1);
@@ -113,7 +118,7 @@ Mesh make_column(int nb1, int nx1, double nh, char const* gw, int ng = 3) {
   mesh_opts->block(block_opts);
   mesh_opts->blocks_per_process(nb1);
   auto mesh = Mesh(mesh_opts);
-  mesh->to(torch::kCPU, torch::kFloat64);
+  mesh->to(device, torch::kFloat64);
   return mesh;
 }

@@ -137,7 +142,7 @@ void fill_column(Mesh mesh, MeshVariables& vars, bool cold = false) {
                      torch::zeros_like(z));
     auto w = torch::zeros({mesh->blocks[b]->phydro->peos->nvar(),
                            coord->options->nc3(), coord->options->nc2(), nc1},
-                          torch::kFloat64);
+                          coord->x1v.options());
     w[IDN].copy_(rho.view({1, 1, nc1}));
     w[IPR].copy_(p.view({1, 1, nc1}));
     w[IVX].copy_(v1.view({1, 1, nc1}));
@@ -190,9 +195,10 @@ double energy_p(Mesh mesh, MeshVariables const& vars) {

 // max over rho, rho v1 and E of |split - one| / max|one| after nstep steps
 double split_gap(int nx1, double nh, char const* gw, int nstep,
-                 double* ep_drift = nullptr, bool cold = false) {
-  auto one = make_column(1, nx1, nh, gw);
-  auto two = make_column(2, nx1, nh, gw);
+                 double* ep_drift = nullptr, bool cold = false,
+                 torch::Device device = torch::kCPU) {
+  auto one = make_column(1, nx1, nh, gw, 3, device);
+  auto two = make_column(2, nx1, nh, gw, 3, device);
   EXPECT_EQ(one->blocks.size(), 1u);
   EXPECT_EQ(two->blocks.size(), 2u);
   MeshVariables v1(1), v2(2);
@@ -218,25 +224,14 @@ double split_gap(int nx1, double nh, char const* gw, int nstep,
   return gap;
 }

-}  // namespace
-
-TEST(X1SeamSplit, switches_off_nghost_1_sets_up) {
-  ASSERT_FALSE(std::getenv("SNAP_X1_CENTROID_EXACT") ||
-               std::getenv("SNAP_GRAVITY_WORK_RADIAL_EXACT") ||
-               std::getenv("SNAP_WB_REF4"));
-  // the nghost >= 3 check is the switches' own: the default nghost is 1
-  EXPECT_NO_THROW(make_column(1, 16, 1., "cell", 1));
-  EXPECT_NO_THROW(make_column(2, 16, 1., "cell", 1));
-}
-
-TEST(X1SeamSplit, centroid_exact_split_matches_one_block) {
+void centroid_exact_split_matches_one_block(torch::Device device) {
   ASSERT_TRUE(std::getenv("SNAP_X1_CENTROID_EXACT"));
   ASSERT_FALSE(std::getenv("SNAP_GRAVITY_WORK_RADIAL_EXACT") ||
                std::getenv("SNAP_WB_REF4"));
   torch::set_num_threads(1);
   ASSERT_TRUE(x1_centroid_exact_enabled());
   for (double nh : {1., 0.}) {
-    double gap = split_gap(32, nh, "cell", 20);
+    double gap = split_gap(32, nh, "cell", 20, nullptr, false, device);
     std::printf("non-hydrostatic %g: 2 blocks vs 1, max rel gap %.3e\n", nh,
                 gap);
     // round-off: 20 steps of a 32-cell column
@@ -244,13 +239,14 @@ TEST(X1SeamSplit, centroid_exact_split_matches_one_block) {
   }
 }

-TEST(X1SeamSplit, radial_exact_split_gap) {
+void radial_exact_split_gap(torch::Device device) {
   ASSERT_TRUE(std::getenv("SNAP_GRAVITY_WORK_RADIAL_EXACT"));  // 1, or 0
   bool on = HydroImpl::gravity_work_radial_exact();
   torch::set_num_threads(1);
   for (int nx1 : {32, 64, 128}) {
     double drift = 0.;
-    double gap = split_gap(nx1, 1., "face", 20 * nx1 / 32, &drift);
+    double gap =
+        split_gap(nx1, 1., "face", 20 * nx1 / 32, &drift, false, device);
     std::printf(
         "switch %d, nz %d: 2 blocks vs 1, max rel gap %.3e; split E+P "
         "drift %.3e\n",
@@ -259,14 +255,14 @@ TEST(X1SeamSplit, radial_exact_split_gap) {
   }
 }

-TEST(X1SeamSplit, wb_ref4_flag_at_the_seam_split_matches_one_block) {
+void wb_ref4_flag_at_the_seam_split_matches_one_block(torch::Device device) {
   ASSERT_TRUE(std::getenv("SNAP_WB_REF4"));
   ASSERT_FALSE(std::getenv("SNAP_X1_CENTROID_EXACT"));
   ASSERT_TRUE(wb_ref4_enabled());
   ASSERT_FALSE(x1_centroid_exact_enabled());
   torch::set_num_threads(1);
   for (double nh : {1., 0.}) {
-    double gap = split_gap(16, nh, "cell", 20, nullptr, /*cold=*/true);
+    double gap = split_gap(16, nh, "cell", 20, nullptr, /*cold=*/true, device);
     std::printf(
         "SNAP_WB_REF4, cold, non-hydrostatic %g: 2 blocks vs 1, max rel gap "
         "%.3e\n",
@@ -275,7 +271,7 @@ TEST(X1SeamSplit, wb_ref4_flag_at_the_seam_split_matches_one_block) {
   }
   // the flag reads scan pressures three cells away: fewer ghosts is an error
   for (int ng : {1, 2}) try {
-      make_column(2, 16, 1., "cell", ng);
+      make_column(2, 16, 1., "cell", ng, device);
       ADD_FAILURE() << "nghost " << ng << " accepted";
     } catch (c10::Error const& e) {
       EXPECT_NE(std::string(e.what()).find("needs nghost >= 3"),
@@ -283,3 +279,42 @@ TEST(X1SeamSplit, wb_ref4_flag_at_the_seam_split_matches_one_block) {
           << e.what();
     }
 }
+
+}  // namespace
+
+TEST(X1SeamSplit, switches_off_nghost_1_sets_up) {
+  ASSERT_FALSE(std::getenv("SNAP_X1_CENTROID_EXACT") ||
+               std::getenv("SNAP_GRAVITY_WORK_RADIAL_EXACT") ||
+               std::getenv("SNAP_WB_REF4"));
+  // the nghost >= 3 check is the switches' own: the default nghost is 1
+  EXPECT_NO_THROW(make_column(1, 16, 1., "cell", 1));
+  EXPECT_NO_THROW(make_column(2, 16, 1., "cell", 1));
+}
+
+TEST(X1SeamSplit, centroid_exact_split_matches_one_block) {
+  centroid_exact_split_matches_one_block(torch::kCPU);
+}
+
+TEST(X1SeamSplit, radial_exact_split_gap) {
+  radial_exact_split_gap(torch::kCPU);
+}
+
+TEST(X1SeamSplit, wb_ref4_flag_at_the_seam_split_matches_one_block) {
+  wb_ref4_flag_at_the_seam_split_matches_one_block(torch::kCPU);
+}
+
+TEST(X1SeamSplit, centroid_exact_split_matches_one_block_cuda) {
+  if (!snapy_cuda_test_enabled()) GTEST_SKIP() << "CUDA is not available";
+  centroid_exact_split_matches_one_block(torch::Device(torch::kCUDA, 0));
+}
+
+TEST(X1SeamSplit, radial_exact_split_gap_cuda) {
+  if (!snapy_cuda_test_enabled()) GTEST_SKIP() << "CUDA is not available";
+  radial_exact_split_gap(torch::Device(torch::kCUDA, 0));
+}
+
+TEST(X1SeamSplit, wb_ref4_flag_at_the_seam_split_matches_one_block_cuda) {
+  if (!snapy_cuda_test_enabled()) GTEST_SKIP() << "CUDA is not available";
+  wb_ref4_flag_at_the_seam_split_matches_one_block(
+      torch::Device(torch::kCUDA, 0));
+}
--
2.43.0

```
