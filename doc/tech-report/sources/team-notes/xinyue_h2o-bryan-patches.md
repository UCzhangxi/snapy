# kintera h2o_bryan patches: 0001, 0002a, 0003
Base `192d724a434176221a0f8a6e42bddfd448853245`; head `42daebce90dab83dce0e6af2a50889fc956db580` (branch `fix/h2o-bryan-latent-heat`). Each size and sha256 below is of the raw patch file on disk (`sha256sum <file>`), **not** of this markdown or of the fenced text. To recreate a file, copy the text between its fences exactly, ending with the final newline after `2.52.0`, plus the one blank line that follows it; the raw files are attached separately. The new `h2o-comparison.svg` is not included here; it is delivered separately (59784 bytes, sha256 `d539b64b5269b44c39f7de709b63482076b6dbf2c5543a6d5097efded3035efc`, git blob `6db7994c6d9ffa3f638ca89ee82e678d0b3367ce` at 42daebc).

## 0001

- File: `0001-Add-failing-test-for-h2o_bryan-latent-heat-at-273.15.patch`
- Size: 2621 bytes
- sha256 (raw file): `e4cb0c0a558c5aca988e8cf8b7fce8cdd822dac6641f64ce9b4b1ed2729e6bba`

`````diff
From 033b677f656b59cce66aa64831c8009aed01a070 Mon Sep 17 00:00:00 2001
From: xinyuewa <xinyuewa@umich.edu>
Date: Fri, 9 Oct 2026 17:49:00 -0400
Subject: [PATCH 1/3] Add failing test for h2o_bryan latent heat at 273.15 K

Bryan and Fritsch (2002) use L_v0 = 2.5e6 J/kg at 273.15 K. With
kintera's R_v = Rgas / M(H2O), L = R_v T^2 dln(p)/dT from h2o_bryan_ddT
is 1.00147 * 2.5e6 at the current beta = 24.845. The new test requires
1e-6 relative.

Also pin h2o_ideal and h2o_ideal_ddT bitwise to values captured at
192d724, so the fix cannot touch the generic water curve.
---
 tests/test_vapor_functions.cpp | 28 ++++++++++++++++++++++++++++
 1 file changed, 28 insertions(+)

diff --git a/tests/test_vapor_functions.cpp b/tests/test_vapor_functions.cpp
index daf671c..31a9106 100644
--- a/tests/test_vapor_functions.cpp
+++ b/tests/test_vapor_functions.cpp
@@ -10,9 +10,11 @@
 #include <torch/torch.h>

 // kintera
+#include <kintera/constants.h>
 #include <kintera/vapors/vapor_functions.h>

 #include <kintera/thermo/log_svp.hpp>
+#include <kintera/utils/molar_mass.hpp>

 using namespace kintera;

@@ -175,6 +177,32 @@ TEST(VaporFunctions, h2o_bryan_dispatches_through_log_svp) {
   EXPECT_NEAR(grad[1].item<double>(), h2o_bryan_ddT_expected(289.85), 1.e-12);
 }

+// Bryan and Fritsch (2002, MWR 130), appendix: L_v0 = 2.5e6 J/kg at 273.15 K.
+// Kirchhoff form: L(T) = R_v T^2 dln(p)/dT = R_v (beta tr - delta T).
+TEST(VaporFunctions, h2o_bryan_latent_heat_matches_bryan_fritsch) {
+  double rv = constants::Rgas / molar_mass({{"H", 2.}, {"O", 1.}});
+  double temp = 273.15;
+  double latent = rv * temp * temp * h2o_bryan_ddT(temp);
+  EXPECT_NEAR(latent / 2.5e6, 1., 1.e-6);
+}
+
+// Reference values captured from h2o_ideal at 192d724.
+TEST(VaporFunctions, h2o_ideal_is_bitwise_unchanged) {
+  struct {
+    double temp, value, ddT;
+  } const refs[] = {{200.0, -0x1.d3e6936ac6f68p+0, 0x1.3c1196556c6e2p-3},
+                    {250.0, 0x1.15572a189aa81p+2, 0x1.92dd2f1e0f5a8p-4},
+                    {273.15, 0x1.9a963c89fe1d6p+2, 0x1.50cf513b1f4f3p-4},
+                    {273.16, 0x1.9aa3b55810a5ep+2, 0x1.50c8ee6b236cep-4},
+                    {290.0, 0x1.e3e248d1b1505p+2, 0x1.041d28c07fb3p-4},
+                    {300.0, 0x1.057ecd4aa535fp+3, 0x1.e195ea58fe871p-5}};
+  for (const auto &ref : refs) {
+    SCOPED_TRACE(ref.temp);
+    EXPECT_EQ(h2o_ideal(ref.temp), ref.value);
+    EXPECT_EQ(h2o_ideal_ddT(ref.temp), ref.ddT);
+  }
+}
+
 // NIST WebBook, Antoine parameters: H2S (Stull 1947), CO2 (Giauque 1937).
 TEST(VaporFunctions, nist_antoine_coefficients) {
   EXPECT_NEAR(
--
2.52.0

`````

## 0002a

- File: `0002a-Set-h2o_bryan-beta-so-L-273.15-K-2.5e6-J-kg.patch`
- Size: 5224 bytes
- sha256 (raw file): `4c8f2adabb9e1c8f33d2556dcf4f8b91aeb7420c1c17ebd6bba95bc57d12ea55`

`````diff
From 7e127550d7bebfac9584ef07ae66196bae2a2088 Mon Sep 17 00:00:00 2001
From: xinyuewa <xinyuewa@umich.edu>
Date: Fri, 9 Oct 2026 17:51:34 -0400
Subject: [PATCH 2/3] Set h2o_bryan beta so L(273.15 K) = 2.5e6 J/kg

h2o_bryan and h2o_bryan_ddT carried h2o_ideal's liquid beta = 24.845,
which gives L(273.15) = R_v (beta tr - delta T) = 2.50368e6 J/kg with
R_v = Rgas / M(H2O) = 8.31446 / 0.018015 = 461.5298 J/(kg K), 0.147 %
above Bryan and Fritsch (2002). beta = (2.5e6 / R_v + delta 273.15) / tr
= 24.815845124764618; 24.815845 leaves -6.3e-9 relative error in L.

h2o_ideal keeps its own literal and is bitwise unchanged. The expected
values in test_vapor_functions.cpp and the h2o_bryan entry in
docs/reaction_catalogue.py transcribe the same constant and are updated
with it; without that, three gtest cases and
test_reaction_equilibrium.py::test_documented_native_curves fail.

The h2o reaction page, its CSV and comparison SVG are regenerated with
docs/plot_reaction_comparisons.py --all (numpy 2.4.4, matplotlib 3.10.8,
which reproduce the base pages byte for byte); only h2o_bryan rows change.
---
 docs/reaction_catalogue.py                   | 2 +-
 docs/source/_static/reactions/h2o-values.csv | 6 +++---
 docs/source/reactions/h2o.rst                | 8 ++++----
 src/vapors/vapor_functions.h                 | 4 ++--
 tests/test_vapor_functions.cpp               | 4 ++--
 5 files changed, 12 insertions(+), 12 deletions(-)

diff --git a/docs/reaction_catalogue.py b/docs/reaction_catalogue.py
index 34a1d4b..93d7af9 100644
--- a/docs/reaction_catalogue.py
+++ b/docs/reaction_catalogue.py
@@ -51,7 +51,7 @@ def add(key, title, reactants, cloud, curves, sources, note='', h2=0, cloud_nu=1

 add('h2o', 'Water', {'H2O': 1}, 'H2O', [
     ideal('h2o_ideal', [273.16, 611.7, 24.845, 4.986009, 22.98, .52], [230, 303]),
-    ideal('h2o_bryan', [273.16, 611.7, 24.845, 4.986009, 24.845, 4.986009], [230, 303]),
+    ideal('h2o_bryan', [273.16, 611.7, 24.815845, 4.986009, 24.815845, 4.986009], [230, 303]),
     antoine('NIST liquid', [5.40221, 1838.675, -31.737], [273, 303])],
     [('Bridgeman and Aldrich (1964), NIST Antoine table, 273–303 K', NIST.format('C7732185'))],
     'The ideal branches switch at 273.16 K. h2o_bryan continues the liquid branch below the triple point; it is not an ice fit. The displayed legacy interval is a plotting interval, not a verified validity range.')
diff --git a/docs/source/_static/reactions/h2o-values.csv b/docs/source/_static/reactions/h2o-values.csv
index 7a9e026..b61a78d 100644
--- a/docs/source/_static/reactions/h2o-values.csv
+++ b/docs/source/_static/reactions/h2o-values.csv
@@ -2,9 +2,9 @@ formula,temperature_K,ln_Q_Pa
 h2o_ideal,230,2.193423775
 h2o_ideal,266.5,5.854792938
 h2o_ideal,303,8.346098496
-h2o_bryan,230,2.611509532
-h2o_bryan,266.5,5.91842199
-h2o_bryan,303,8.346098496
+h2o_bryan,230,2.616980531
+h2o_bryan,266.5,5.919150591
+h2o_bryan,303,8.343227257
 NIST liquid,273,6.40388033
 NIST liquid,288,7.431033685
 NIST liquid,303,8.344590271
diff --git a/docs/source/reactions/h2o.rst b/docs/source/reactions/h2o.rst
index 8fb1107..d8477d5 100644
--- a/docs/source/reactions/h2o.rst
+++ b/docs/source/reactions/h2o.rst
@@ -38,7 +38,7 @@ Coefficient conventions
      - legacy; coefficient provenance unresolved
    * - h2o_bryan
      - ideal
-     - [273.16, 611.7, 24.845, 4.986009, 24.845, 4.986009]
+     - [273.16, 611.7, 24.815845, 4.986009, 24.815845, 4.986009]
      - 230–303
      - legacy; coefficient provenance unresolved
    * - NIST liquid
@@ -69,13 +69,13 @@ Coefficient conventions
      - 8.346098496
    * - h2o_bryan
      - 230
-     - 2.611509532
+     - 2.616980531
    * - h2o_bryan
      - 266.5
-     - 5.91842199
+     - 5.919150591
    * - h2o_bryan
      - 303
-     - 8.346098496
+     - 8.343227257
    * - NIST liquid
      - 273
      - 6.40388033
diff --git a/src/vapors/vapor_functions.h b/src/vapors/vapor_functions.h
index 51158f4..70a957c 100644
--- a/src/vapors/vapor_functions.h
+++ b/src/vapors/vapor_functions.h
@@ -48,13 +48,13 @@ inline double h2o_ideal_ddT(double T) {

 DISPATCH_MACRO
 inline double h2o_bryan(double T) {
-  double beta = 24.845, delta = 4.986009, tr = 273.16, pr = 611.7;
+  double beta = 24.815845, delta = 4.986009, tr = 273.16, pr = 611.7;
   return logsvp_ideal(T / tr, beta, delta) + log(pr);
 }

 DISPATCH_MACRO
 inline double h2o_bryan_ddT(double T) {
-  double beta = 24.845, delta = 4.986009, tr = 273.16;
+  double beta = 24.815845, delta = 4.986009, tr = 273.16;
   return logsvp_ideal_ddT(T / tr, beta, delta) / tr;
 }

diff --git a/tests/test_vapor_functions.cpp b/tests/test_vapor_functions.cpp
index 31a9106..77b903d 100644
--- a/tests/test_vapor_functions.cpp
+++ b/tests/test_vapor_functions.cpp
@@ -21,7 +21,7 @@ using namespace kintera;
 namespace {

 double h2o_bryan_expected(double T) {
-  double beta = 24.845;
+  double beta = 24.815845;
   double delta = 4.986009;
   double tr = 273.16;
   double pr = 611.7;
@@ -29,7 +29,7 @@ double h2o_bryan_expected(double T) {
 }

 double h2o_bryan_ddT_expected(double T) {
-  double beta = 24.845;
+  double beta = 24.815845;
   double delta = 4.986009;
   double tr = 273.16;
   double t = T / tr;
--
2.52.0

`````

## 0003

- File: `0003-Add-derivation-note-for-the-h2o_bryan-latent-heat-be.patch`
- Size: 6400 bytes
- sha256 (raw file): `3ff6901ebf933bc29291b3be16abb62053e93a4629f9c818578e05aa5e21373e`

`````diff
From 42daebce90dab83dce0e6af2a50889fc956db580 Mon Sep 17 00:00:00 2001
From: xinyuewa <xinyuewa@umich.edu>
Date: Fri, 9 Oct 2026 17:52:24 -0400
Subject: [PATCH 3/3] Add derivation note for the h2o_bryan latent-heat beta

Kirchhoff form, kintera's R_v and its source, old and new beta, L(273.15)
before and after, and the SVP comparison with Bolton (1980) at 250, 290
and 300 K.
---
 docs/h2o_bryan_latent_heat.md | 130 ++++++++++++++++++++++++++++++++++
 1 file changed, 130 insertions(+)
 create mode 100644 docs/h2o_bryan_latent_heat.md

diff --git a/docs/h2o_bryan_latent_heat.md b/docs/h2o_bryan_latent_heat.md
new file mode 100644
index 0000000..9ad609f
--- /dev/null
+++ b/docs/h2o_bryan_latent_heat.md
@@ -0,0 +1,130 @@
+# h2o_bryan: latent heat at 273.15 K
+
+`h2o_bryan` (`src/vapors/vapor_functions.h`) is the saturation vapor pressure
+used for the Bryan and Fritsch (2002, MWR 130, appendix) moist benchmark. That
+case takes a constant-capacity latent heat with L_v0 = 2.5e6 J/kg at
+T_0 = 273.15 K. Up to 192d724, `h2o_bryan` reused the liquid beta of
+`h2o_ideal` (24.845). That beta gives L(273.15) about 0.15 % too high.
+
+## Kirchhoff form
+
+Both functions use the same ideal form, with t = T / t_r:
+
+    ln p(T) = ln p_r + beta (1 - t_r / T) - delta ln(T / t_r)
+    d ln p / dT = beta t_r / T^2 - delta / T
+
+Clausius-Clapeyron with an ideal vapor, L = R_v T^2 d ln p / dT, gives
+
+    L(T) = R_v (beta t_r - delta T)
+
+This is linear in T with slope -R_v delta = c_pv - c_l, so beta fixes L at
+one temperature and delta fixes the slope.
+`h2o_bryan` has t_r = 273.16 K, p_r = 611.7 Pa and delta = 4.986009.
+
+## R_v
+
+kintera has no water-specific constant. It builds R_v from the gas constant
+and the harp atomic weights that `molar_mass` uses:
+
+| quantity | value | source |
+|---|---|---|
+| R | 8.31446 J/(mol K) | `src/constants.h:6` (`constants::Rgas`) |
+| M(H2O) | 2 x 1.008 + 15.999 = 18.015 g/mol | pyharp 2.6.5 `harp/element.cpp:54,61` via `kintera::molar_mass` (`src/utils/molar_mass.cpp:17`) |
+| R_v | 461.5298362475715 J/(kg K) | R / M(H2O) |
+
+## beta
+
+    beta = (L_v0 / R_v + delta T_0) / t_r = 24.815845124764618
+
+| beta | L(273.15) [J/kg] | L / 2.5e6 - 1 |
+|---|---|---|
+| 24.845 (old, = h2o_ideal liquid) | 2503675.599 | +1.470e-3 |
+| 24.816 | 2500019.5 | +7.8e-6 |
+| 24.81585 | 2500000.6 | +2.5e-7 |
+| 24.815845 (new) | 2499999.984 | -6.3e-9 |
+
+At least five decimals are needed to reach 1e-6. The code uses 24.815845.
+`h2o_ideal` keeps its own literal 24.845 and is bitwise unchanged
+(`VaporFunctions.h2o_ideal_is_bitwise_unchanged`).
+
+## SVP against Bolton (1980)
+
+The benchmark's moisture formulas use Bolton's
+e_s = 611.2 exp(17.67 (T - 273.15) / (T - 29.65)) Pa.
+
+| T [K] | Bolton [Pa] | old h2o_bryan [Pa] | old diff | new h2o_bryan [Pa] | new diff |
+|---|---|---|---|---|---|
+| 250 | 95.4891 | 95.2348 | -0.266 % | 95.4924 | +0.003 % |
+| 290 | 1917.9970 | 1921.1636 | +0.165 % | 1917.9138 | -0.004 % |
+| 300 | 3534.5197 | 3539.4575 | +0.140 % | 3530.2372 | -0.121 % |
+
+The values come from compiling the header before and after the change and
+evaluating `exp(h2o_bryan(T))` directly. p_r = 611.7 Pa at 273.16 K is
+unchanged; Bolton gives 611.64 Pa there (+0.009 %). The cause of the
+remaining -0.12 % at 300 K has not been analysed here. It is not the
+reference pressure.
+
+## Changed expectations
+
+Three existing expectations pin the h2o_bryan constant, not the physics.
+They change in the same commit as the header. Every other test is
+unchanged, and `h2o_ideal` is bitwise identical.
+
+1. `tests/test_vapor_functions.cpp`, `h2o_bryan_expected`:
+   beta 24.845 -> 24.815845. Values at the tested temperatures (ln Pa):
+
+   | T [K] | old | new |
+   |---|---|---|
+   | 250 | 4.556345539765576 | 4.559046458965575 |
+   | 273.16 | 6.416241966248519 | 6.416241966248519 |
+   | 289.85 | 7.551155054063129 | 7.549476265206824 |
+   | 300 | 8.171728750030239 | 8.169120349363572 |
+
+2. `tests/test_vapor_functions.cpp`, `h2o_bryan_ddT_expected`:
+   beta 24.845 -> 24.815845. Values (1/K):
+
+   | T [K] | old | new |
+   |---|---|---|
+   | 250 | 0.0886425272 | 0.08851510352320001 |
+   | 273.16 | 0.07270094816224923 | 0.07259421584419387 |
+   | 289.85 | 0.0635790182569613 | 0.06348422366961026 |
+   | 300 | 0.058787305555555565 | 0.058698816891111116 |
+
+3. `docs/reaction_catalogue.py`, `h2o_bryan` entry, checked by
+   `tests/test_reaction_equilibrium.py::test_documented_native_curves`:
+   `[273.16, 611.7, 24.845, 4.986009, 24.845, 4.986009]` ->
+   `[273.16, 611.7, 24.815845, 4.986009, 24.815845, 4.986009]`.
+   The documented ln Q values change as follows:
+
+   | T [K] | old | new |
+   |---|---|---|
+   | 230 | 2.6115095315005963 | 2.6169805306310305 |
+   | 266.5 | 5.918421989930005 | 5.919150591430943 |
+   | 303 | 8.346098495661849 | 8.34322725737802 |
+
+These values are float64 evaluations of the helper formula.
+
+## Generated pages
+
+`docs/plot_reaction_comparisons.py --all` regenerates
+`docs/source/reactions/h2o.rst`, `docs/source/_static/reactions/h2o-values.csv`
+and `h2o-comparison.svg` from the catalogue. With numpy 2.4.4 and
+matplotlib 3.10.8 (the recorded environment) it reproduces every page at
+192d724 byte for byte. On the new catalogue, only the h2o_bryan parameter row
+and the h2o_bryan ln Q values change in the rst and csv. The SVG is a single
+figure, so the lower panel's axis range moves with the h2o_bryan ratio curve.
+
+`validation.json` is not re-recorded. Its `source_sha256` covers
+`src/vapors/vapor_functions.h`, so `plot_reaction_comparisons.py --all --check`
+reports the native measurements as stale until `reaction_validation.py --cuda`
+is rerun on a CUDA build; that rerun re-measures every reaction. On CPU at the
+new constant, `native_curves('cpu')` gives a maximum h2o_bryan ln Q
+difference of 4.441e-15, the same as the recorded value.
+`validation.json` is stale for h2o_bryan only: it fingerprints
+`src/vapors/vapor_functions.h`, and only its two h2o_bryan `native_curves`
+entries (cpu, cuda) depend on this constant, since the equilibrium cases use
+a manufactured inline curve. Re-run `python docs/reaction_validation.py --cuda`
+to refresh it. No CI or pre-commit gate runs `--check`.
+
+Downstream inputs that set u0_R = -beta t_r for this curve (for example
+snapy `bryan.yaml`) need the new beta.
--
2.52.0

`````

## Reconstruction and tree check

0002a is patch 0002 (fix commit `7e127550d7bebfac9584ef07ae66196bae2a2088`) without the
`docs/source/_static/reactions/h2o-comparison.svg` hunk. It was made with
`git format-patch -1 7e12755 -- . ':(exclude)docs/source/_static/reactions/h2o-comparison.svg'`,
so the From/Date/author header, the message and every other hunk match 0002 exactly. Only the
diffstat changes, because git recomputes it (5 files changed, 12 insertions(+), 12 deletions(-)).
The subject is numbered `[PATCH 2/3]` as in the original.

Steps, from a clean checkout of chengcli/kintera at 192d724, with the four files in `../patches/`:

```
git checkout -b fix/h2o-bryan-latent-heat 192d724a434176221a0f8a6e42bddfd448853245
git am ../patches/0001-Add-failing-test-for-h2o_bryan-latent-heat-at-273.15.patch \
       ../patches/0002a-Set-h2o_bryan-beta-so-L-273.15-K-2.5e6-J-kg.patch
cp ../patches/h2o-comparison.svg docs/source/_static/reactions/h2o-comparison.svg
sha256sum docs/source/_static/reactions/h2o-comparison.svg   # expect d539b64b...035efc
git add docs/source/_static/reactions/h2o-comparison.svg
git commit --amend --no-edit       # folds the SVG into the fix commit
git am ../patches/0003-Add-derivation-note-for-the-h2o_bryan-latent-heat-be.patch
git rev-parse HEAD^{tree}          # expect 008d87d3ed9eb163019487c1ce01b7d08de0aac9
```

Result on dart2, run on a fresh worktree at 192d724:

- All three patches applied cleanly.
- `HEAD^{tree}` = `008d87d3ed9eb163019487c1ce01b7d08de0aac9`, which equals `42daebc^{tree}`.
- The fix-commit tree after the amend is `94f05ca2c72ad88ec8649d8870597d8a13ff460a`, which equals `7e12755^{tree}`.
- The author `xinyuewa <xinyuewa@umich.edu>` and the author dates are kept by `git am`.

Commit shas will differ from 033b677/7e12755/42daebc because the committer and commit date are
the applier's. Use the tree shas to compare.
