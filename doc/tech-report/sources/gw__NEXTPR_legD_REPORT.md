> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Leg D — radial-exact weights for the face gravity work (snapy, next PR)
Final sha 6499404 (docs-only). Base 8cea3ae (#293 head). Earlier docs-only commit: c06546d.


## Option F against the r-bar form, and one discrete P everywhere (fail->pass, 3bd859e)
- (a) replica sec 8 (optionF_replica_out.txt): r-bar form (study dcba4b2 sec 4) conserves E+P_rbar (5e-15),
  interior O(h^4) but wall cells O(h) (cell 0 1.0e-3 at nz 256, same as face+H: H is zeroed at the walls) and column
  total O(h^2) (+3.4e-4 nz 64 R 5, = face's); F: walls O(h^4), column -4.7e-7. P_rbar is an O(h^2) PE (3.5e-5 nz 64), P O(h^4) (3.0e-8).
- (b) PE sites: fixer + its epe lambda (cell mode only; F is face only -> disjoint), implicit projection/clamp work (inside
  moved = du-du0 -> F remainder covers it), cycle diagnostics pe= (PE_d: WRONG under switch -> fixed b7ea6cb, test 3bd859e),
  tests' E+PE_d oracles (switch off by construction).

## Option b: what face+H was cancelling
- Local merge (never pushed): c2624e3 onto fdf895b = e65db14
  (conflict = two adjacent declarations in hydro.cpp/hpp, both kept). Build BUILD-GOOD.
- wall_budget.py: linear one-stage replica, each term booked separately vs its exact cell value. CHECK vs C++ (cmp_cpp_replica.py,
  C++ per-level dt->0 Richardson from diag_eps_budget.py): with snapy's reconstruction (weno5 shock:false = WENO5-JS, scaled, eps 1e-6,
  on every variable incl. the WB density perturbation) max|cell diff| 1.9e-5/2.6e-6/1.2e-6 (nz 16/32/64), all 4 arms (cmp_head_weno.out);
  with linear UP5 it was 3.8e-2/2.2e-2/1.2e-2 (cmp_head.out): the near-wall face density of the code reference is set by the WENO weights.
- Budget on the C++ initial state (wall_budget_dump.out), code reference: wall-cell O(h) terms = H (cell 0 +9.8e-3/4.9e-3/2.5e-3,
  n-1 +2.2e-2/1.1e-2/5.7e-3) AND the reference density WBr (cell 0 +2.7e-3/1.5e-3/7.8e-4, n-1 +8.9e-3/4.1e-3/2.0e-3); WBr also has an
  O(h) interior sum -7.6e-2/-3.9e-2/-1.8e-2. face+H's positive wall error offset WBr's negative interior sum. F's wall work error O(h^2).
  W4: WBr wall O(h^2) (-3.4e-4/-8.4e-5/-2.1e-5), interior sum +1.7e-3..3.7e-3 (constant: the point-IC term below).
- Point-value IC: the deck's cell values read as cell averages carry an O(h^2) entropy gradient. Oracle (dump, 4th-order
  deconvolution, -w ds/dz projected): +0.00634/+0.00668/+0.00678; replica cov+F+W4 +0.00596/+0.00663/+0.00677 (residual
  -3.8e-4/-5e-5/-1e-5). Exact-average inputs (wall_budget_avg.out): cov+F+W4 -8.5e-4/-1.85e-4/-4.3e-5/-1.0e-5 (nz 16..128, p 2.1).
- Replica predictions for the C++ 4-way (point IC): cov -0.0130/-0.0049/+0.0003; cov+W4 +0.0374/+0.0227/+0.0149 (O(h): H's wall error
  now unbalanced); cov+F -0.0444/-0.0210/-0.0078; cov+F+W4 +0.0060/+0.0066/+0.0068 (= IC term + O(h^2)).
- Bitwise e1e-3_n32_face and e2e-2_n16_cell head vs ctl IDENTICAL (nc + diag.txt). ctest: same 26 Failed
  + 820 Not Run on both (test_eos.cpp glibc `major` macro); head +1 test (test_gravity_work_radial_exact_python) passes.
  Rerun with an uncommitted #undef shim on both (head / ctl). T1L onset rel_err nz32/nz64: off -0.1493/-0.0349,
  F -0.1583/-0.0360, cov -0.0022/+0.0001, F+cov -0.0101/-0.0009.
- C++ 4-way on the merged build (cmp_w4.out), eps nz^2 dt->0 nz 16/32/64: cov -0.01300/-0.00493/+0.00025;
  cov+W4 +0.03738/+0.02266/+0.01486 (O(h); wall cell 0 +1.03e-2/5.0e-3/2.5e-3, n-1 +2.08e-2/1.09e-2/5.6e-3 = H's wall error);
  cov+F -0.04448/-0.02097/-0.00784; cov+F+W4 +0.00589/+0.00662/+0.00676 (wall cell 0 +3.0e-4/8.6e-5/2.3e-5 p 1.9, n-1
  -1.44e-3/-3.4e-4/-8.1e-5 p 2.0). Minus the point-IC oracle: -4.5e-4/-6e-5/-1.6e-5. Replica matches all 8 arms (max|cell diff|
  <= 8.3e-5 nz 16, <= 1.2e-6 nz 64). Acceptance criterion MET: cov+F+W4 better than cov+W4 and second order in eps nz^2.
- Independent Cartesian derivation folded in: its eq.(4) point CONFIRMED by sympy (F to s^4: h^4 coeff
  -F''/(360 rbar^2)+F'''/(360 rbar)+F''''/480, remainder O(h^6)); its Cartesian-clause point agreed. Derivation + replica fixed
  as local commit 950ad98 (NOT pushed). Its H-wall O(h) result agrees with step 1 in order/location.
- ctest correction: the ~820 Not Run are Eigen's vendored test suite (never built), not test_eos; with the shim test_eos.release
  PASSES (head: 26 Failed = 13 Eigen/BLAS + 13 snapy MPI/parallel/straka/restart, compare ctl).
- T1L onset on the merged build rel_err nz32/64: cov -0.0022/+0.0001, rxcov -0.0101/-0.0009 (= head), covW4 +0.0118/+0.0020,
  rxcovW4 +0.0038/+0.0010. ctest shim ctl = head per-test, head +1 PASS.
- D+W ship together; rebased onto aea71ed (#293 merged): 5536c0a (pre-rebase df2f8fb);
  conflict in implicit_hydro.cpp resolved (corrected-PE block before #292's finite reject). Quick oracles run on the rebased build.

## Result: exactness and discrete E+PE conservation CONFLICT -> nothing picked
- Derivation: curved-gravity-work-weight.md (repo copy docs/derivations/ at c06546d). Check: radial_weight_replica.py -> radial_weight_replica_out.txt
  (repo copy curved_gravity_work_weight.py, identical output md5 232473d7).
- Face form (code, hydro_forward.cpp:676-692; VIC work_lo/hi = same weights x 1/2): error vs exact r^2 average
  = h^2/12 F'' + h^2/(6 rbar) F' - h^2/(6 rbar^2) F (sympy; matches the ablation's term). Exact for divergence-free G = r^2 F = const.
- Unique 2-pt weights exact for F in {1, r}: a = (r_c - r-)/h on F+, b = (r+ - r_c)/h on F- (offsets swapped vs face form);
  error h^2/12 F'' - h^4/(360 rbar^2) F''; reduce to 1/2,1/2 in Cartesian.
- Conservation <=> per-face weight sum S_f = A_f (r_c,i+1 - r_c,i) (lemma) <=> face form with any face potential s_f.
  Face form: S_f - need = 0 exactly. Exact weights: = h^3 (3R^4 - R^2h^2 + h^4/6)/(9R^4 - 3R^2h^2 + h^4) = h^3/3 + ..., rel h^2/(3R^2).
- One step, closed column, (dE+dPE)/sum|WV|: face 3.9e-15 / -6.5e-13 / 3.1e-15; exact -1.3e-6 (R=5H, h/R 9.4e-3), +1.2e-10 (R=1000H), +2.0e-4 (R=H).
  Relative to E+PE: exact -4.1e-8 / +2.8e-14 / +2.2e-5 -> fails oracle (c) 1e-14 everywhere.
- Conserving family s_f = r_f + lam h^2/r_f: lam=+1/6 kills the F term (doubles F'), lam=-1/6 kills F' (doubles F); never both; both round-off conservative.
- Oracle (e) replica: face error minus h^2/12 F'' slope 2 in h, x R const (4.7e-4 at R/H 5..500); exact slope 4.00.
- Hypothesis (unverified): the ablation's wrong-sign shift (+1.05 vs -1.07 predicted) is option B's defect (same order). Check: ablation arms with options C and D.

## Option F: F WORKS (derivation §7; optionF_replica.py -> optionF_replica_out.txt)
- P = PE_d - g1 sum V sigma^2 s[rho] (sigma^2 = r^2-measure variance, s = quadratic slope at centroids, one-sided at walls/block edges) = exact PE + O(h^4).
- W = W_face + g1 sigma^2 s[rhodot]; sum W V + dP/dt = 0 identically. One step: (dE+dP)/(E+P) <= 1.2e-15 (sph R=H,5H,1000H; Cartesian).
- Q1 O(h^4) interior (slope 4.00) and wall (4.4-4.6); R-ladder flat 1.4e-7..3.0e-7 (R/H 5..5000). Q2 Cartesian CHANGES (1.6e-3 of max|W|), E+PE_d no longer conserved there.
  Q3 walls: one-sided 3-pt slope only. Q4 tables in §7.
- cp3/cp5/weno5 curvature flux H: face+H leaves -h^2/(6R^2)F interior and is O(h) in wall cells; F+H double counts -> F must REPLACE H.
- Settling: A, C, D identical column totals (1.420e-3 @R5 nz32); B differs by its PE_d defect (-1.29e-4, 9%); F column error -7.3e-6.
- Code plan: F gated to spherical-polar + gravity-work: face (keeps oracle b bitwise); explicit term in hydro_forward, VIC term post-solve from the solved density change.

## Option F state
- Requirement: apply F on Cartesian too (same switch); oracle b becomes: Cartesian on: E+P round-off, interior work unchanged to O(h^4), change in wall cells; report face+H vs F wall order on T1L/x2cov decks; if F breaks rest balance / #289 eps_eff / ctest: STOP and report, no gating.
- Added Cartesian oracles (off vs on): 1 wall-cell order (first/last interior cell and interior separately, nz 16/32/64/128, face+H vs F); 2 E+P per step round-off, E+PE_d reported; 3 #289 oracles unchanged-or-better: eps_eff*nz^2 (off -0.258/-0.251/-0.247, on -0.0130/-0.0049/+0.0002 nz16/32/64) and T1L onset rel_err eps 1e-3 nz32/64 face, with F on and F+SNAP_FLUX_COVARIANCE; 4 Cartesian hydrostatic rest; 5 2-D Cartesian nx3=1 explicit + VIC; 6 self-contained Cartesian section in the derivation (every step explicit; an independent reviewer will check it).
- Code: c2624e3 = new src/hydro/gravity_work_radial.hpp (x1_variance, centroid_slope, corrected_pe_work), HydroImpl::gravity_work_radial_exact()/radial_exact_work() (face + cartesian|spherical-polar), hydro_forward adds the term and skips curv_flux1 H when on, implicit_hydro post-solve adds g1 var s[du-du0 density]. A local build patch applied uncommitted.
- Builds: head c2624e3, control 8cea3ae.

## Option F results — STOP condition: #289 eps_eff gets worse with F on
- Builds: head (C++ = c2624e3; pip version string gc30ba73), control 8cea3ae; both BUILD-GOOD PASS.
- New test (local commit 99d836a, test only): head TEST_EXIT=0; control 8cea3ae TEST_EXIT=1 (RED: "switch changed
  nothing", E+P drift, eq. 7 mismatch). Head numbers, max per-step |d(E+P)|/|E+P| on (off): sph 3.2e-16 (4.2e-8),
  sph_vic 3.2e-16 (1.65e-7), cart 2.6e-16 (9.4e-8), cart_vic 2.6e-16 (3.6e-7), cart2d 3.9e-16 (4.4e-10), cart2d_vic
  3.9e-16 (1.25e-9); E+PE_d per step on: 4.2e-8, 1.65e-7, 9.4e-8, 3.6e-7, 4.4e-10, 1.2e-9. Eq. 7 in code, one plm
  stage: |dE(on-off) - g1 sigma^2 s[drho]| = 2.5e-14 (sph), 2.6e-14 (cart) vs term 3.3e-5, |E| 246. Cartesian rest
  50 steps max|u1|/cs on (off): 7.2e-16 (7.6e-16) explicit, 4.0e-16 (4.2e-16) VIC.
- Spherical rest sp_rest (100 steps): max|u1| off 5.332e-8, F on 5.325e-8 (x3 on and x3 off alike; ctl = head off).
- #289 eps_eff nz^2 (nz 16/32/64), head build: off -0.2578/-0.2513/-0.2465 and cov -0.0130/-0.0049/+0.0003
  (both reproduce the reference numbers); F on -0.2892/-0.2674/-0.2546; F+cov -0.0444/-0.0210/-0.0078. Shift F-minus-not
  = -0.031/-0.016/-0.008 in both pairs: additive, ~ -0.5/nz in eps nz^2. Criterion "unchanged or improve": FAILS.

## Option F, wall-cell order and Cartesian section
- Oracle 1 (wall cells) and 6 (Cartesian section) DONE: replica §6/§7, derivation §8 (Cartesian,
  self-contained). Cartesian face+H: first wall cell O(h) (1.65e-2 -> 2.05e-3, slope 1.00), interior O(h^4); F: first
  cell 1.29e-4 -> 3.08e-8 (slope 4.02), last 3.96, interior 4.00. F - (face+H): interior slope 4.00, wall slope 1.
  Spherical: face+H first cell slope 0.99, interior 1.99; F first 4.56, interior 4.00.
- Test tests/test_gravity_work_radial_exact.py + CMake registration committed (c30ba73).

## Log
- Code located (explicit hydro_forward.cpp face_gravity_work; implicit implicit_hydro.cpp:201-204 work_lo/hi into vic_assemble_*_impl.h).
- replica + derivation; control tree at 8cea3ae prepared.
- c06546d pushed.
