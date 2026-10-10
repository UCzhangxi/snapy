# Moist-row balance-column test: patch on UCzhangxi/snapy next/x1-wall-closure caa1833

| item | value |
|---|---|
| base | caa1833b4266b83e11e31961547942c3d098fe9a, tree 3e4ccef266777d38db8335e57bb1164cc3999e4f (verified) |
| commit | fc3534c34dc514805b80ba3ac75bf14b80dd4e12, tree 1a4a375a68e20cf484b7069fe411822bf0c697a1, local branch `test/moist-balance-column` |
| author | Xinyue <xinyuewa@umich.edu>; no AI or Co-authored-by trailers. No git identity was configured, so amend the name if you want a different one. |
| patch file | 0001-test-balance_column-on-a-moist-column-with-one-conde.patch, one file, 9582 bytes |
| sha256 (raw file) | 124491a97e87b02637818acb7f98749ea75c362375729389ac9409ed4f407d5e |
| git am check | `git am` on a fresh clone at caa1833 reproduces tree 1a4a375a68e20cf484b7069fe411822bf0c697a1 |
| files | tests/test_balance_column.cpp (+133 lines: one new TEST plus two helpers, one include), tests/test_balance_column_moist.yaml (new card) |
| registration | none needed: the case goes into the existing `setup_test(test_balance_column)` and the `_wb_ref4` / `_x1_centroid` arms (tests/CMakeLists.txt:31, 62-69). The yaml is copied by the existing `file(GLOB inputs *.yaml *.py)`. |
| build | CPU source build of the C++ core (CMake Release, Ninja, NETCDF on, CUDA off), GCC 11.5.0, at fc3534c. Linked against torch 2.10.0+cu128 (used on CPU) and kintera 2.6.1 (pip package; its C++ library and headers). |
| format | clang-format 20.1.4 `-style=Google` as in .pre-commit-config.yaml; changes only the new lines, and the base file was already clean |

## What the test asserts (BalanceColumn.a_moist_column_with_one_condensable_comes_out_at_rest)
- **Setup:** one condensable through kintera, as in test_wall_saturation.yaml: dry air, H2O vapour and H2O(l), with h2o_bryan nucleation and the ideal-moist EOS. The column is 10 km, nx1 32, with the dry test's g = 10.44 and reflecting walls.
- **Profile:** T = 300 K - 6.5 K/km z, and vapour mass fraction 0.01 exp(-z/1.5 km), which stays subsaturated. The condensate is 0. p/rho = R_mix T, with R_mix taken from the solver's own EOS ("W->T" at rho = p = 1). The column is marched with the same forward Euler as the dry fixture.
- **Non-vacuity:** R_mix varies by more than 1e-3 along the column, and the marched audit is above 1e-4.
- **Balance audit:** the dry test's residual() audit, max|p' - C|/(rho g dz), must be below rtol = 1e-10 and equal to the residual balance_column reports. Same bound as the dry a_marched_column_comes_out_at_rest. Justification: moisture enters balance_column only through the per-cell p/rho it holds fixed, and the reference scans the total primitive density, so the dry bound applies unchanged.
- **Species and temperature:** the vapour and condensate rows come back bit-for-bit, and T (W->T) is unchanged to 1e-14. These match the dry test's channel and p/rho bounds.
- **Solver momentum row:** one RK3 step of the card's block from rest, measuring max|v1|/(g dt) over the owned cells. It must be below 1e-10, the dry rest check's TOL_ON in test_x1_centroid_rest.py, which bounds the same |a|/g. The control is the unbalanced marched column, which must exceed 1e-6. A phase change is excluded by requiring the condensate row to stay exactly 0 and the vapour to stay within 1e-12.

## Commands and output
```
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DNETCDF=ON -DCUDA=OFF && cmake --build build --parallel 6
cd build/tests && ctest -R "balance_column|wb_wall_corner|hydro_ref_x1|wb_ref_wall|hydrostatic|wall_saturation"
  ... 100% tests passed out of 8   (test_balance_column, _wb_ref4, _x1_centroid, test_wb_wall_corner,
                                     test_hydro_ref_x1, test_wb_ref_wall, test_hydrostatic, test_wall_saturation)
./test_balance_column.release                     -> [  PASSED  ] 11 tests.
./test_balance_column.release --gtest_filter='*moist*'   (same numbers with SNAP_WB_REF4=1 and SNAP_X1_CENTROID_EXACT=1)
  moist column: audit before 3.356992e-01, after 8.895698e-11 (rtol 1.000000e-10), 13 sweeps
  moist column: max |v1|/(g dt) after one step, balanced 2.575131e-11, marched 2.054391e-02
  [       OK ] BalanceColumn.a_moist_column_with_one_condensable_comes_out_at_rest (30 ms)
```
| check | measured | bound |
|---|---|---|
| audit, marched column | 3.357e-01 | > 1e-4 (fixture is the defect) |
| audit, balanced column | 8.896e-11 | < 1e-10, and equal to the reported residual |
| solver x1 row, balanced | 2.575e-11 | < 1e-10 |
| solver x1 row, marched (control) | 2.054e-02 | > 1e-6 |

The moist row balances. The balanced audit (8.9e-11) sits just under rtol because balance_column stops at the first sweep below rtol; the dry fixture behaves the same way under the same rtol. The CUDA case is not covered: test_balance_column has no device arms, so the new case is CPU-only like the rest of that file.

## Patch (verbatim)
````diff
From fc3534c34dc514805b80ba3ac75bf14b80dd4e12 Mon Sep 17 00:00:00 2001
From: Xinyue <xinyuewa@umich.edu>
Date: Fri, 9 Oct 2026 22:35:03 -0400
Subject: [PATCH] test: balance_column on a moist column with one condensable

A 10 km column with the dry air / H2O / H2O(l) set and h2o_bryan
nucleation of test_wall_saturation (ideal-moist through kintera), vapour
falling off with height so R_mix varies by > 1e-3 along it. Asserted with
the dry column's bounds, which carry over since moisture reaches
balance_column only through the per-cell p/rho it holds fixed:
  - the audit residual max|p' - C|/(rho g dz) < rtol = 1e-10 and equal to
    the reported one (the marched fixture starts at > 1e-4);
  - the vapour and condensate rows bit-for-bit, T to 1e-14 (W->T);
  - the solver's x1 momentum row, max|v1|/(g dt) after one RK3 step of the
    card's block from rest, < 1e-10 (TOL_ON of test_x1_centroid_rest),
    with the marched column as the control (> 1e-6), and no phase change.
Runs in the existing test_balance_column ctest entries, including the
SNAP_WB_REF4 and SNAP_X1_CENTROID_EXACT arms.
---
 tests/test_balance_column.cpp        | 133 +++++++++++++++++++++++++++
 tests/test_balance_column_moist.yaml |  40 ++++++++
 2 files changed, 173 insertions(+)
 create mode 100644 tests/test_balance_column_moist.yaml

diff --git a/tests/test_balance_column.cpp b/tests/test_balance_column.cpp
index fb13a1f..c2c3f2f 100644
--- a/tests/test_balance_column.cpp
+++ b/tests/test_balance_column.cpp
@@ -16,6 +16,7 @@
 #include <snap/hydro/balance_column.hpp>
 #include <snap/hydro/hydro_dispatch.hpp>
 #include <snap/hydro/wb_ref4.hpp>
+#include <snap/mesh/meshblock.hpp>

 namespace {

@@ -364,4 +365,136 @@ TEST(BalanceColumn, x1_centroid_switch_balances_only_a_cartesian_column) {
     }
 }

+// ONE CONDENSABLE, MOISTURE ON. The dry air / H2O / H2O(l) set of
+// test_wall_saturation through kintera (ideal-moist, h2o_bryan), in a 10 km
+// column under the same kGrav. The vapour falls off with height, so the
+// mixture's p/rho differs cell by cell from the dry column's; that ratio is
+// the only way moisture reaches balance_column, which holds it fixed, and the
+// primitive density the reference scans is the total (dry + vapour +
+// condensate) one. So the dry bounds carry over unchanged: the audit < rtol,
+// the temperature to 1e-14, the species rows bit-for-bit. The solver's x1
+// momentum row is then checked the way test_x1_centroid_rest checks a dry
+// column, max |v1| / (g dt) after one RK3 step from rest, against the same
+// 1e-10 (TOL_ON there, rtol here: both bound |a|/g).
+constexpr char kMoistCard[] = "test_balance_column_moist.yaml";
+constexpr double kMoistTs = 300.0;  // surface temperature [K]
+constexpr double kLapse = 6.5e-3;   // [K/m], subsaturated aloft
+constexpr double kVapor0 = 1.0e-2;  // surface vapour mass fraction
+constexpr double kVaporH = 1.5e3;   // vapour scale height [m]
+
+//! The marched moist column of the card: T(z) linear, vapour q(z), condensate
+//! zero, and p/rho = R_mix T with R_mix from the solver's own EOS ("W->T" at
+//! rho = p = 1), marched by the same forward Euler as marched_column.
+Column moist_marched_column(snap::MeshBlock const& b) {
+  auto pc = b->pcoord;
+  int il = pc->il(), nx1 = pc->iu() - il + 1;
+  int nvar = b->phydro->peos->nvar();
+  auto opt = torch::TensorOptions().dtype(torch::kFloat64);
+  auto dx1f = pc->dx1f.narrow(0, il, nx1).to(opt).clone();
+  auto zc = pc->x1v.narrow(0, il, nx1).to(opt).clone();
+
+  auto w = torch::zeros({nvar, 1, 1, nx1}, opt);
+  w[snap::ICY].copy_((kVapor0 * torch::exp(-zc / kVaporH)).view({1, 1, -1}));
+  auto unit = w.clone();
+  unit[snap::IDN].fill_(1.);
+  unit[snap::IPR].fill_(1.);
+  auto rmix_t = (1. / b->phydro->peos->compute("W->T", {unit})).contiguous();
+  auto rmix = rmix_t.accessor<double, 3>();
+  auto zt = zc.accessor<double, 1>();
+
+  auto rho_t = w[snap::IDN], prs_t = w[snap::IPR];
+  auto rho = rho_t.accessor<double, 3>();
+  auto prs = prs_t.accessor<double, 3>();
+  double p = kPs;
+  for (int i = 0; i < nx1; ++i) {
+    double t = kMoistTs - kLapse * zt[i];
+    if (i > 0) {
+      double tp = kMoistTs - kLapse * zt[i - 1];
+      p -= kGrav * (p / (rmix[0][0][i - 1] * tp)) * (zt[i] - zt[i - 1]);
+    } else {
+      p -= kGrav * (kPs / (rmix[0][0][0] * kMoistTs)) * zt[0];
+    }
+    prs[0][0][i] = p;
+    rho[0][0][i] = p / (rmix[0][0][i] * t);
+  }
+  return {w, dx1f};
+}
+
+//! The solver's x1 momentum row: one RK3 step from rest of the column, as the
+//! card's block, and max |v1| / (g dt) over the owned cells, with the end
+//! state's condensable rows so a phase change cannot pass unseen.
+std::pair<double, torch::Tensor> moist_row_force(torch::Tensor const& col) {
+  auto b = snap::MeshBlock(snap::MeshBlockOptionsImpl::from_yaml(kMoistCard));
+  b->to(torch::kCPU, torch::kFloat64);
+  auto pc = b->pcoord;
+  int il = pc->il(), iu = pc->iu(), nx1 = iu - il + 1;
+  auto w = torch::zeros(
+      {col.size(0), pc->options->nc3(), pc->options->nc2(), pc->options->nc1()},
+      col.options());
+  w.narrow(-1, il, nx1).copy_(col.expand({-1, w.size(1), w.size(2), -1}));
+  for (int m = 0; m < il; ++m) {  // overwritten by the reflecting walls
+    w.narrow(-1, m, 1).copy_(w.narrow(-1, il, 1));
+    w.narrow(-1, iu + 1 + m, 1).copy_(w.narrow(-1, iu, 1));
+  }
+  snap::Variables v{{"hydro_w", w}};
+  b->initialize(v);
+  double dt = b->max_time_step(v);
+  for (int stage = 0; stage < b->pintg->stages.size(); ++stage)
+    b->forward(v, dt, stage);
+  auto end =
+      b->phydro->peos->compute("U->W", {v.at("hydro_u")}).narrow(-1, il, nx1);
+  double f = (end[snap::IVX].abs().max() / (kGrav * dt)).item<double>();
+  return {f, end.narrow(0, snap::ICY, end.size(0) - snap::ICY).clone()};
+}
+
+TEST(BalanceColumn, a_moist_column_with_one_condensable_comes_out_at_rest) {
+  constexpr double rtol = 1.e-10;
+  torch::set_num_threads(1);
+  auto b = snap::MeshBlock(snap::MeshBlockOptionsImpl::from_yaml(kMoistCard));
+  b->to(torch::kCPU, torch::kFloat64);
+  int ny = b->phydro->peos->nvar() - snap::ICY;
+  ASSERT_EQ(ny, 2) << "one condensable: a vapour row and a condensate row";
+  auto c = moist_marched_column(b);
+  auto eos = b->phydro->peos;
+
+  // the moisture is real: the column's R_mix moves by more than 1e-3 ...
+  auto rt = c.w[snap::IPR] / c.w[snap::IDN];
+  auto temp0 = eos->compute("W->T", {c.w});
+  auto rmix = rt / temp0;
+  EXPECT_GT(((rmix.max() - rmix.min()) / rmix.min()).item<double>(), 1.e-3);
+  // ... and the fixture is the defect
+  double before = residual(c, /*uniform=*/true);
+  EXPECT_GT(before, 1.e-4);
+
+  auto [wb, err, sweeps] = balance(c.w, c.dx1f, kGrav, true, rtol);
+  double actual = residual({wb, c.dx1f}, /*uniform=*/true);
+  std::cout << std::scientific << "moist column: audit before " << before
+            << ", after " << actual << " (rtol " << rtol << "), " << sweeps
+            << " sweeps\n";
+  EXPECT_LT(actual, rtol);
+  EXPECT_DOUBLE_EQ(actual, err);
+  EXPECT_GT(sweeps, 0);
+
+  // only p and rho move: the condensable rows ride through, T stays put
+  EXPECT_TRUE(
+      torch::equal(wb.narrow(0, snap::ICY, ny), c.w.narrow(0, snap::ICY, ny)));
+  auto temp1 = eos->compute("W->T", {wb});
+  EXPECT_LT(((temp1 - temp0).abs() / temp0).max().item<double>(), 1.e-14);
+
+  // the solver's x1 momentum row, with the condensable pair live
+  auto [f_balanced, y_balanced] = moist_row_force(wb);
+  auto [f_marched, y_marched] = moist_row_force(c.w);
+  std::cout << "moist column: max |v1|/(g dt) after one step, balanced "
+            << f_balanced << ", marched " << f_marched << '\n';
+  EXPECT_LT(f_balanced, rtol);
+  // the control: the same check sees the marched column's defect
+  EXPECT_GT(f_marched, 1.e-6);
+  // subsaturated throughout, so nothing condensed and the vapour stayed put
+  EXPECT_TRUE(torch::equal(y_balanced[1], torch::zeros_like(y_balanced[1])));
+  EXPECT_LT(((y_balanced[0] - wb[snap::ICY]).abs() / wb[snap::ICY])
+                .max()
+                .item<double>(),
+            1.e-12);
+}
+
 }  // namespace
diff --git a/tests/test_balance_column_moist.yaml b/tests/test_balance_column_moist.yaml
new file mode 100644
index 0000000..7053c0f
--- /dev/null
+++ b/tests/test_balance_column_moist.yaml
@@ -0,0 +1,40 @@
+# test_balance_column: one condensable (H2O / H2O(l), h2o_bryan) through
+# kintera, as in test_wall_saturation, in a 10 km column under const gravity
+reference-state: {Tref: 0., Pref: 1.e5}
+species:
+  - name: dry
+    composition: {O: 0.4200039819342909, N: 1.560014790041652, Ar: 0.01}
+    cv_R: 2.5
+  - name: H2O
+    composition: {H: 2, O: 1}
+    cv_R: 1.534301
+    u0_R: 0.
+  - name: H2O(l)
+    composition: {H: 2, O: 1}
+    cv_R: 7.52031
+    u0_R: -6786.6602
+reactions:
+  - equation: H2O <=> H2O(l)
+    type: nucleation
+    rate-constant: {formula: h2o_bryan}
+geometry:
+  type: cartesian
+  bounds: {x1min: 0., x1max: 1.e4, x2min: 0., x2max: 1., x3min: 0., x3max: 1.}
+  cells: {nx1: 32, nx2: 1, nx3: 1, nghost: 3}
+dynamics:
+  equation-of-state:
+    type: ideal-moist
+    limiter: true
+    density-floor: 1.e-10
+    pressure-floor: 1.e-10
+    max-iter: 20
+    ftol: 1.e-8
+  reconstruct:
+    vertical: {type: weno5, scale: true, shock: false}
+    horizontal: {type: weno5, scale: true, shock: false}
+  riemann-solver: {type: lmars}
+boundary-condition:
+  external: {x1-inner: reflecting, x1-outer: reflecting}
+integration: {type: rk3, cfl: 0.9, implicit-scheme: 0}
+forcing:
+  const-gravity: {grav1: -10.44}
--
2.52.0

````
