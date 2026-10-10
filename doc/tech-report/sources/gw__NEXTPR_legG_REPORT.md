> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Leg G — x1 cell-centroid offset on spherical-polar (SNAP_X1_CENTROID_EXACT)
Base 8cea3ae. Study: commit 10822ce (study/next-1overR); replica.py = the study's replica plus a `shift` arm.

## Design (switch SNAP_X1_CENTROID_EXACT, read once like SNAP_FLUX_COVARIANCE in hydro.cpp:184)
Spherical-polar only (coord type check), so Cartesian is untouched code -> bitwise by construction.
1. (i)+(ii) one move: before the x1 block of hydro_forward.cpp, w1 = w - delta_v D1 w on every row (delta_v =
   x1v - (x1f_i+x1f_i+1)/2; D1 centred on x1v, one-sided at il/iu on physical walls). w1 feeds _hydro_ref_x1 (so
   scan step = g h (rho_c - delta_v D1 rho_c), anchor/pref/dsf/dref all consistent in the uniform sense) and
   precon1. Ghosts at physical non-outflow walls: correction mirrored with parity (IVX odd) so wl = -wr holds.
2. (iii) spherical_polar.cpp forward(): pressure part of src1 = (2/V) int r p~ dr, p~ = degree-5 interpolant of
   the six nearest face pressures (one-sided at block ends), weights precomputed from x1f.
3. Not touched: curv_flux1 (face-work term; study: x1 bias cancels under face work), rho_grav for
   non-hydrostatic < 1 (default 1; warn once if switch on with nh < 1), cubed sphere (x1v = mid-radius there).
Implicit (VIC): RHS = explicit du, so rest stays rest; just tested.

## Finding (replica only, unverified in code: a build of the switch would settle it)
The target numbers (+0.0224/R -> +0.0004/R; rest to round-off) are the study's EXACT-reference arms. The code has
main's own well-balanced reference, and with it the three changes do not reach them. replica.py (study copy +
`shift`, `dsf_rec`, `wall_exact` arms; sha256 9025f4cd110a) models exactly the planned code:
1. eps_eff 1/R content, R*[eps nz^2(R) - eps nz^2(1e5)], cell work, x3 #293 on (predict_1overR_nz{32,64,128}.out):
   | arm | nz 32, R=5 | nz 64, R=5..40 | nz 128, R=5 |
   |---|---|---|---|
   | main (code ref) | -0.0057 | -0.0090 / -0.0156 / -0.0194 / -0.0215 | -0.0108 |
   | legG (code ref + shift) | +0.0147 | +0.0115 / +0.0138 / +0.0151 / +0.0158 | +0.0096 |
   | exact ref (study) | | +0.0226 / +0.0218 / +0.0213 / +0.0211 | |
   | exact ref + shift (= study's r^2-weight fix) | +0.0011 | +0.0006 / +0.0007 / +0.0007 / +0.0007 | +0.0005 |
   In main the x1-weight term (+0.022) and the WB faces at r_f + delta_v (-0.031) nearly cancel. The shift removes
   both: every INTERIOR background face is then exact with no 1/R part (R*nz^2 face error 0.0000 for p and rho).
   What is left (+0.008..+0.016) is main's reference's own Cartesian O(h^2) face density error (nz^2 0.0034, the
   same at R = 5 and 1e5) seen through the spherical 2/r divergence, plus the O(h) clamped wall density
   (wall_attribution.out: exact walls -> +0.008). It is not the centroid offset.
2. Rest of a cell-average column, max |x1 force imbalance| (predict_rest.out, nz 64): R = 5: main 1.5e-6 interior /
   1.7e-6 all cells; legG 4.8e-8 interior (30x better) / 2.2e-6 all (wall cells, one-sided 6-face form on the
   reference's wall faces). R = 1000: main 3.9e-11 / 4.4e-11, legG 2.4e-10 / 1.1e-8. Not round-off in either arm.
   Independent check caveat (supported): legG's interior imbalance falls as 1/R, main's as 1/R^2, so legG is worse
   than main above R/H ~ 160 (interior) and from R/H ~ 4 over all cells. At giant-planet R/H ~ 1e3 the planned
   force form balances rest WORSE than main. Face-error evidence: face_error.out.
So (c) and (d) as written fail by prediction. The scope change that would meet them: a face reference exact to
O(h^4) on the switch (the "reference fixed to 4th order" the study's harness used), i.e. a fourth change to
hydro_ref_x1 (dsf/pref), which also changes the Cartesian scheme unless gated to spherical-polar.

## Design G (shift + r^2-exact 4th-order reference, stacked on Leg W 1454878)
Design G (replica arm ref="w", conv=True): before the x1 block every x1 input (all primitive rows) goes through a
5-point r^2-mean -> plain-mean conversion C (weights exact for degree <= 4 under the r^2 cell measure, window
centred, one-sided inside the owned cells at walls; conv_weights in replica.py; exactness checked to 3e-16 for
degrees 0-4). This is (i)+(ii) to O(h^6/R) instead of the first design's a - dv D1 a. Then Leg W's reference
(SNAP_WB_REF4, replica wb_faces_w = spec 4.1/4.2/4.4, checked against Leg W's wb_ref4.cpp) runs unchanged on the
converted values: on plain means it is the Cartesian algorithm, so it is r^2-exact without touching wb_ref4.
Plus (iii): src1 pressure part = (2/V) int r p~ dr, p~ the quintic through six faces.
1. (c) rest, max |x1 force| of a cell-average column (predict_rest2.out), interior / 3 wall cells:
   | R/H | nz | main | G |
   |---|---|---|---|
   | 5 | 64 / 128 | 1.5e-6, 1.7e-6 / 3.9e-7, 4.4e-7 | 4.1e-14, 2.6e-14 / 7.8e-14, 6.0e-14 |
   | 20 | 64 / 128 | 9.7e-8, 1.1e-7 / 2.5e-8, 2.8e-8 | 3.5e-14, 6.6e-14 / 8.4e-14, 2.8e-14 |
   | 160 | 64 / 128 | 1.5e-9, 1.7e-9 / 3.9e-10, 4.3e-10 | 4.8e-14, 7.4e-14 / 7.4e-14, 5.6e-14 |
   | 1000 | 64 / 128 | 3.9e-11, 4.4e-11 / 1.0e-11, 1.1e-11 | 2.9e-14, 6.3e-14 / 8.4e-14, 4.1e-14 |
   G is at round-off everywhere, interior and walls: no regression at any R/H. W alone = main for pressure.
2. (d) 1/R content R*[eps nz^2(R) - eps nz^2(1e5)], x3 #293 full (predict_1overR2_nz{64,128}_{cell,face}.out):
   cell work, nz 64: main -0.009/-0.019/-0.023/-0.023 (R = 5/20/160/1000), W alone -0.020..-0.039,
   G +0.0006/+0.0007/+0.0007/+0.0007; nz 128: G +0.0004/+0.0005/+0.0005/+0.0005. G = exact-ref + conv to 5 digits:
   the reference is no longer a source. Face work: G -0.0049 (nz 64) -> -0.0026 (128) at R = 1000, order 3 -> 0.
   Residual (order_1overR2.out, isolate_1overR2.out): cell work tends to +0.00045/R nz^-2, an O(h^2/R) term,
   50x below the target's +0.0224. Source: the x1 face velocity: with the exact face w it is 0.00000 (x3 exact).
   It is snapy's reconstruction of the Favre velocity <rho w>/<rho> as if it were an average of w, a Cartesian
   O(h^2) error seen through the 2/r of the divergence; not the centroid, not the reference. Out of Leg G scope.
3. Walls (face_error_w.out): main's clamped binomial gives an O(h) wall face density error (2.7e-3 at nz 64).
   W's one-sided closure (cubic extrapolation of rho/p, clamped I4 window) on converted inputs gives 5.7e-8 at
   nz 64, 7.2e-9 at 128: O(h^3), 5e4x below main. The O(h^3) (faces 0-2 only) is W's own, the same in Cartesian:
   the anchor's O(h^2) constant c enters rho' = rho - pref Fr as -c R(z), and the even-parity ghosts of rho'
   turn its slope into an O(h c) face error. Interior faces are O(h^4) (1.2e-10 at nz 64). Pressure faces:
   round-off up to the anchor constant. Note for Leg W, not a Leg G blocker.

   Independent check (fresh context, 2026-10-09): supported, checked against snapy 1454878 and replica.py +
   the .out files; it flagged (1) the replica guards only interior faces while wb_ref4.cpp:279-280 also guards
   the wall faces (settled only by the C++ rest run), (2) the Favre attribution was inferred. Settling run
   settle_favre.out: with the exact PLAIN mean of w as the x1 input, cell work x3 exact goes +0.00037/+0.00043/
   +0.00044 -> -0.00008/-0.00002/-0.00001 (nz 64/128/256): the residual is the Favre-velocity input, confirmed.
4. Exact (sympy) checks of the design: docs/derivations/verify_x1_centroid.py in the branch: conversion exact
   to degree 4 and not 5 (interior and wall windows, uniform and stretched grids), Gauss-4 exact for every code
   integrand, the integration by parts of (iii), zero force from a constant p, and a degree-4 density column of
   r^2 means balanced EXACTLY by scan + (iii) for any anchor offset (and not balanced without C). All pass.

## Build gates (2026-10-09, base fdf895b vs head legG)
- Builds: base and head BUILD-GOOD. Run packs: base (10 runs), head (20), gates (36), all RUN_EXIT=0.
- (a) bitwise.sh base_off vs head_off: T1L e2e-2_n16_cell, e1e-3_n32_face IDENTICAL (3 files each). cs/sp decks
  write final_w.npy + maxu.json, not compared by bitwise.sh (0 files): still to compare by cmp of final_w.npy.
- RED/GREEN, first deck (isothermal exp column): head on 1e-9 interior / 1.4e-8 walls, R-independent and equal
  to the base at r0/H = 1000: the reference's own Cartesian truncation, not curvature; the replica's round-off
  assumed an exact reference. Test re-decked on a linear-density column (all x1 formulas exact):
  RED (base) rc 1, off 2.4e-5 at r0/H 5; GREEN (head) rc 0, on 1e-14..3e-14 everywhere.
- sp_rest (spherical-polar, non-hydrostatic 0, r0/H 10) head_on max|u1|/cs 1.07e-3 vs off 5.3e-8: REGRESSION.
  Cause (unverified until the rebuild): in hydrostatic-split mode rho_grav = (pL - pR)/dx1 cancels only the
  plain-difference pressure force; the switch's r^2 force leaves O(h^2 p''/r) (~1e-4 rel., matches). Fix
  09a04d9: rho_grav = (A pL| - A pR|)/V - S(p*) under the switch; doc section 4 extended. Rebuilt.
- (f) base ctest: 846/1033 fail (test_eos.cpp does not compile on the test machine, same on main); compare sets.

### After the fix (head build = 09a04d9; ac8af0e differs only by clang-format, include order, docs)
| oracle | result |
|---|---|
| (a) off = base, bitwise | PASS: T1L x2 (card.out*.nc + diag.txt), cs x6 + sp x2 (final_w.npy) all cmp-identical |
| (b) Cartesian on = off | PASS: T1L x2 and cs x6 identical; sp x2 differ (switch live, as intended) |
| (c) rest, r^2-mean column | PASS: GREEN on 1e-14; RED rc 1. sp_rest (nh 0, r0/H 10): on 2.44e-8 vs off 5.33e-8 (was 1.07e-3) |
| (c) exp column, sp_epe | R5: off 1.3e-5 / 1.0e-5 -> on 4.5e-10 / 3.0e-10 (imp0/imp1); R1000: 7.2e-10 / 9.9e-11 -> 3.5e-10 / 8.4e-11 (reference's Cartesian floor) |
| (d) 1/R, unit weight | off nz64 -0.0011/-0.0170/-0.0226/-0.0236, on +0.0005/+0.0006/+0.0005/-0.0000 (R/H 5/20/160/1000); nz128 off -0.0030/-0.0205/-0.0274/-0.0340, on +0.0004/+0.0004/-0.0004/-0.0060 (R/H 1000 noise-limited: R x 4e-10) |
| (e) closed-wall E+PE | max dEPE ~5e-15 off and on; mass ~6e-15 |
| (f) ctest fail set | PASS: head 846 = base 846, diff empty; pass set = base + test_x1_centroid_rest_python |

(d) matches the replica's G arm to ~3 digits (replica unit nz64 +0.00056/+0.00067/+0.00071/+0.00071). The target's
"+0.0224/R" is the study's exact-reference arm; the code's off arm (main's reference) is negative, -0.017..-0.024.
Weighted by cell volume, on reads +0.018..+0.020 and off -0.004..-0.012, replica and code alike (replica G volume
nz64 +0.0184/+0.0199/+0.0204/+0.0203); interpretation (r^2 ~ 1+2x/R reweights the local error profile) pending
an independent check. Unit weight = the harness's metric = the oracle's.

Independent checks (2026-10-09): (1) gates, unverified -> settled: (a)(b)(c)(f) hold from the artifacts; the rho_grav
block was untested at round-off (test default non-hydrostatic 1). Settling run (nh 0): on 8e-15..1.4e-14 vs
off 6e-8 / 7e-7. The test now loops non-hydrostatic 1 and 0: GREEN (8 cases <= 3.3e-14), RED (base,
rc 1). (e) is in reduce_legG.py's table (max dEPE ~5e-15 off and on). (2) 1/R metric, supported: the
weight-only term at R = 1e5 is +0.0198 (on) / +0.0117 (off) and accounts for the volume numbers; "~3 digits" is
overstated: eps nz^2 agrees with the replica to 0.1-0.2 %, its small 1/R residual only to 10-30 %.

## State
- Commit 1cf0bbc21c75f4163ae7614ab3b67f2bd1e60a42 (= ac8af0e + the non-hydrostatic 0 test arm), one commit on
  fdf895b (Leg W).
- Rebase onto main aea71ed (#293 merged): local branch = aea71ed + W's three
  #289 commits cherry-picked (5c88954 7345055 9264dbe, clean) + G aafd88e (patch-id equal to 1cf0bbc's).
- The build tree of the head is 09a04d9 + a local build patch (not ac8af0e; code-equivalent).
- Later: rebase onto W when W rebases after #293 merges into main e51bdc2.

## 1/R closure (face work, arms off / cov / covW / covWD / covWDG)
- Tree: e65db14 (D c2624e3 on W fdf895b) + G cherry-picked (f438328, patch-id b43f389c = 1cf0bbc's).
- Harness scripts: arm.py (sets all four switches 1/0 explicitly, then runs the script),
  sp_eps.py (SNAP_FLUX_COVARIANCE now setdefault), sp_epe.py, list_closure.txt (75 eps + 40 rest runs),
  reduce_closure.py (c = R[eps nz^2(R) - eps nz^2(1e5)], order p = 2 + log2(c(nz)/c(2nz)) at R = 160).
- First pass (tree e65db14+G, 115/115 RUN_EXIT=0, ARM env lines checked): table in
  reduce_e65db14G.txt. Unit weight, nz 64, R/H 5/20/160/1000: off +0.054/+0.053/+0.054/+0.064,
  cov +0.018/-0.001/-0.006/+0.004, covW +0.007/-0.016/-0.022/-0.012, covWD +0.002/-0.014/-0.019/-0.020,
  covWDG +0.0002/+0.0002/+0.0002/+0.0000. nz 128 at R/H >= 160: every arm drifts ~ -6e-4 R (off too): the R = 1e5
  reference is biased at nz 128 -> extra R = 2e3, 5e3, 1e4, 3e4 runs to fit e(R) = e_c + A/R + B/R^2.
  Rest (exp column, face work, 100 steps): covWDG 4.5e-10 (R5) .. 3.5e-10 (R1000) vs off 1.3e-5 .. 7.2e-10;
  only R1000 imp1 is 1.22e-10 vs off 1.02e-10. E+PE drift: covWD 2.5e-9 (R5, D's known h^3/3 defect), covWDG 1.4e-13.
- Final tree (D = 5536c0a on aea71ed): local merge of the aea71ed rebase above
  with 5536c0a (c689274; hydro.cpp/hpp additive conflicts kept both sides; hydro files identical to the
  e65db14+G tree, implicit_hydro.cpp differs by #292 only). D 5536c0a = c2624e3 up to line wrapping. Rebuilt,
  then the closure list and the extra-R list rerun on it.


### Rebase quick subset on aea71ed (base vs head = aafd88e), PASS
(a) off = base on all 8 decks (cmp); (b) Cartesian on = off (bitwise + cs, cmp); (c) GREEN 8 cases <= 3.3e-14,
RED exit 1 (11 FAILs); sp_rest step 76 max|u1|/cs off 4.88e-8 = base, on 3.17e-9.

### Closure rerun on the final tree (c689274 = aea71ed + W + D 5536c0a + G)
Reference = true Cartesian deck
(sp_eps.py --cart: cartesian geometry, x1 [R,R+1], x3 [0,LX], plain means, seed A = k sin(pi z), B = -pi cos(pi z)),
because e(R=1e5) at nz 128 carries a +5.9e-4 bias common to all arms.
Runs: 135 spherical, all RUN_EXIT=0; Cartesian (a first attempt failed: R=0 divide in config, fixed);
amplitude check. Reduced: reduce_cart.txt (reduce_cart.py). c, unit weight, nz 32/64/128:
- off +0.052 flat (p 2.0); cov -0.009, covW -0.025, covWD -0.020 at R=1000, flat in nz (p ~2): O(h^2/R) excess left.
- covWDG R=5 +6.2e-4/+1.6e-4/+0.4e-4 (p 4.0, 3.9); R=20 9.0/2.3/0.5e-4; R=160 1.00/0.25/0.18e-3; R=1000 1.04/0.25/0.21e-3.
- Round-off floor: the nz 128 cells at R >= 160 move by 1-2e-4 in c when only the seed amplitude goes 1e-5 -> 1e-4
  (covWDG R=160 +0.00018 -> -0.00000, R=1000 +0.00021 -> +0.00009; nz 64 moves <= 4e-5). So p(nz 64->128) at
  R >= 160 is not resolved; nz 32->64 there gives p 4.0/4.1. Verdict: full set closes the 1/R excess at 4th order.
- Rest (100 steps): covWDG max|v1|/cs 3.5-4.5e-10 (imp0) at every R vs off 1.3e-5..7.2e-10; only R1000 imp1 above off
  (1.22e-10 vs 1.02e-10, covWD 1.18e-10); E+PE covWDG 1.2-1.6e-13 (covWD 2.5e-9 at R5, off 5e-15).
- Independent check on the closure verdict: supported (c689274, reduce_cart.txt, 150 eps.json, ARM lines). Caveats it raised:
  covW and cov are not flat in nz (covW still converging toward ~-0.02); the build tag = exactly the local build patch.
