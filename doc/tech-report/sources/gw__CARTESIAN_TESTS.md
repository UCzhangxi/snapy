> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# snapy Cartesian (planar) tests: gravity work, flux covariance, VIC solver

Read-only catalog, written 2026-10-09, of snapy's Cartesian tests, with snapy's numbers as reference.

Refs read (`git show <ref>:<path>` equivalent):
- main `e51bdc2c8040d84a9f14ffcafbb857a55e6e394c` (contains #284 531e839, #285 117e449, #288 d59836d, #292 e51bdc2)
- PR #293 head `0af14029c667ef9f03fd8e92c528fd863db6f829` (flux covariance, #289 item 2)
- leg W `551787682e761724c906fa3e7203cfdf5b7b1c5e` (SNAP_WB_REF4)

Line numbers are in the file at the ref named in the "ref" column (`main` = e51bdc2, `293` = 0af1402, `W` = 551787). Tests whose arms are all curved (cubed-sphere, spherical-polar) are excluded (list at the end). For mixed tests only the Cartesian arm is described.

## Table

| # | test (tests/) | first appears (ref / commit) | PR / issue | one-line physics statement | key tolerance(s) | RED before fix? | CTest TIMEOUT |
|---|---|---|---|---|---|---|---|
| 1 | test_implicit_gravity_tall_column.py | main / 531e839 (#284); pre-image 068f9f4a; reworked in e51bdc2 | #283, #284, #288 | a discretely balanced tall isothermal rest column stays at rest under implicit-9 at acoustic Courant up to 250 | max abs(w) < `W_TOL` = 1.0e-7 m/s (:24) | yes: "FAIL -> PASS"; on old main grows ~2.7x/step, 1e24 by step 30 | 120 |
| 2 | test_gravity_work_fixer.py | main / 531e839 (#284); pre-image da4b8d5a; extended in 117e449 | #283, #284, #285 | E+PE closed in a reflecting box for the default cell form plus global fixer, explicit and implicit; face-wallc work identity | drift <= `TOL` = 1.0e-12 (:38); fixer-off control > 100 TOL; float32 <= nstep*eps32 | control arm (fixer off) is the planted RED; no stated pre-fix run | 120 |
| 3 | test_implicit_face_work_operator.py | main / 117e449 (#285) | #283, #285 | gravity-work: face inside the implicit operator keeps the tall column at rest and E+PE closed | W_TOL 1.0e-7 m/s (:34); EPE_TOL 1.0e-11 (:35) | yes: "12/12 fail before this change, pass after" (commit msg) | 300 |
| 4 | test_implicit_stratified_solid.py | main / 117e449 (#285); touched in d59836d | #283, #285, #288 | tall columns to 150 cells, solid-wall mass closure, clamped face-work energy defect, restart from a coarse column | mass < 1e-12; energy defect < 1e-10; EPE_TOL 1.0e-11 (inherited) | not stated | 300 |
| 5 | test_implicit_face_work_jacobian.cpp | main / 117e449 (#285); curved arms added in d59836d (#288) | #285, #288 | VIC energy-row source equals the finite-difference derivative of the frozen-Roe face work (Cartesian arms: 4 of 8 gtests) | `EXPECT_NEAR(fd, row, 1.e-5)` (:113), h = 1.e-5 (:107) | not stated | gtest, fast |
| 6 | test_lu_failure.cpp (grid arms only) | main / e51bdc2 (#292) | #290, #294, #292 | a failed or near-singular VIC solve is rejected through step redo, restoring step input; a rest column with zero gravity stays finite | exact equalities (`torch::equal`), residual `== 0.` (:346) | yes: first commit of #292 is "reproduce LU failure and VIC retry gaps (#290)" | gtest, fast |
| 7 | test_horizontal_flux_covariance.py | 293 / 725a7ed (study 9a4e927) | #289 item 2, #293 | with SNAP_FLUX_COVARIANCE on, the one-step spurious stratification of an isentropic column with a convective roll vanishes | off: eps_eff nz^2 in [-0.32, -0.20] (:36); on: abs < 0.03 (:37); E+PE drift <= 1.e-12 (:39) | yes: arm "off" asserts the defect exists | 180 |
| 8 | test_flux_covariance_rows.py (Cartesian arms 3, 4) | 293 / 518ceac (0b6b6ef) | #289, #293 | moist offset invariance of the all-rows covariance term; dry limit reproduces the covariance-only eps_eff | OFFSET_TOL 1e-10 (:35); CART_TOL 2e-3 (:39); CART_REF (:38) | not stated | 300 |
| 9 | test_wb_ref4_order.py | W / 336101b | #289, next PR (leg W) | with SNAP_WB_REF4 the one-step spurious N2_eff of a neutral polytrope is 4th order in dz (observed order ~3) instead of 2nd | order >= `ORDER_ON` 2.75 (:38); off arm order < `ORDER_OFF` 2.5 (:39) | yes: "RED: with the switch env name misspelled the on arm reproduces the off numbers (rc 1)"; 3.5 s | 300 |
| 10 | test_balance_column.cpp | main / ce3fb3a (37ac940) | #221 (older, supporting) | snapy.balance_column puts a marched column into the scheme's own discrete hydrostatic balance | rtol 1.e-10 (:186); T-channel change < 1.e-14 (:233) | not stated | gtest |
| 11 | test_face_floor.cpp (+ .yaml) | main / 9738861 | #221 (older, supporting) | face floor uses the adjacent density when a cell is dipped | EXPECT_NEAR(lower_mass, 4.07888, 1.e-3) (:69); dipped mass < 1e-9 (:70); dipped_mom > 0.03042 (:71) | not stated | gtest |

## Per-test notes

Common notes: all python tests use `snapy.MeshBlock`, rk3, weno5 (vertical and horizontal, scale true), lmars, reflecting x1 walls, periodic x2/x3, `balance_column` for the IC, x1 vertical. "Fixer" = `gravity-work-fixer`.

### 1. test_implicit_gravity_tall_column.py (main)
- Asserts: column at rest, every rung finite and max abs(w) < 1e-7 m/s after `--nstep` steps (default 40, :118). Prints the first failing rung; "passing a finite ladder does not establish a universal stability threshold" (:5-6).
- Deck (:20-47): GRAV 23.1, GAMMA 1.403461, RD 3515.0, T0 786.0 (isothermal), PS 1.0e7; NZ 45, DZ 29946.8085106 (11.3 scale heights), NX2 8 periodic copies, nx3 1, nghost 3; x2max 31415926.53589793, x3max 3926990.8169872416. density/pressure floor 3.4682e-18, temperature-floor 1.e-6, limiter on. cfl 0.5, implicit-scheme 9 (vic-full), `gravity-work: face`, `gravity-work-fixer: False`. IC: p = PS exp(-g z/(R T0)), rho = p/(R T0), then `balance_column`. No perturbation (rest).
- Ladder: acoustic Courant `COURANTS = (6.6, 65.6, 100.0, 197.0, 250.0)` (:22), dt = courant*DZ/cs. Extra arm "default-cell-global-fixer" (default keys omitted) at dt = 997.0 and 100.0 (:147).
- Spherical-polar arm exists in the same file (excluded).

### 2. test_gravity_work_fixer.py (main)
- Deck (:34-60): GAMMA 1.4, RD 287, GRAV 9.8, TS 300, PS 1e5; isentropic column (T = TS - g z/Cp), LZ = TS(1 - exp(-3(GAMMA-1))) Cp/g so rho_top/rho_bot = e^-3; NZ 32, nx2 = nx3 = 1; MACH 1e-2 (w = MACH cs sin(pi z/LZ)); floors 1e-12; cfl 0.4; `--nstep` default 200; `balance_column` IC.
- Arms (:185-190), tolerance TOL = 1.0e-12 (:38): (a) cell + fixer explicit (scheme 0), (b) cell + fixer implicit (scheme 1), both `drift <= TOL`; (c) face-wallc reported only; (d) cell, fixer off: `drift > 100*TOL` (planted control); (e) Python-installed unnamed wall `<= TOL`; (f) float32 `<= nstep*eps32` (:200).
- Refusals: outflow x1 (float64, float32) message "crossed an x1 boundary face"; periodic x1 "non-periodic x1" (the cubed-layout refusal arm is not Cartesian).
- First-stage identity (:225-235): one stage, face-wallc vs face interior and vs cell walls: contrast > 1.e-3 and error < TOL*contrast.
- Implicit face-wallc work identity (`wallc_work`, :145-171, schemes 1 and 9): dt 10.0, rho 1, p 1e5, du[IV1] = sin(pi z); relative error < TOL, scale > 1.e-3, clamp == 0 (:242).
- NaN in the bottom wall cell: `check_redo` nonzero; Python options defaults `cell`/True; grav2 != 0 with fixer refused at construction ("grav2 = grav3 = 0").

### 3. test_implicit_face_work_operator.py (main)
- Same column as #1 (:29-30) with `gravity-work: face`, no fixer key; NSTEP default 40 (:113). Matrix: schemes `((9, "vic-full"), (1, "vic-partial"))` x `RUNGS = ((997.0, 10.0), (3000.0, 10.0), (10000.0, 1.0))` (dt, w0 of the moving run; Courant 65.6, 197, 657) x w0 in (0, w0_moving), w = w0 sin(pi z/H): 12 runs.
- Asserts: finite; at rest max abs(w) < W_TOL 1.0e-7 (:34); E+PE (sum of E + rho g z over the interior) relative drift < EPE_TOL 1.0e-11 (:35). Docstring: old behavior blows up at Courant 65.6 by step 27; fixed gives ~5e-9 m/s and E+PE drift ~1e-14.

### 4. test_implicit_stratified_solid.py (main)
Cartesian throughout except `curved_energy` (excluded). Runs as a script (`__main__`, :227-283); imports decks from #3 and #2.
- `coarse_restart` (:197): 40-scale-height rest column built, traced as a restart, `initialize_from_restart` with scheme 9 must not throw.
- `tall_run` loops (:230-254), scheme 9, gravity-work in (cell+fixer, cell, face), nz in (120, 140, 150), heights nz*11.3/45, 300 steps at dt = 657 dz/cs: finite, no redo, steps == 300, abs(top_rho) < 0.01, abs(top_T/T0 - 1) < 0.01, wmax < 0.1, abs(mass) < 1e-12, clamp == 0, and abs(epe_drift) < EPE_TOL (1e-11) except for cell without fixer. Coarse columns nz 45 (heights 40) and nz 160 (heights 40), 40 steps at dt = 1500: wmax < 0.1, abs(mass) < 1e-12; the face coarse run may redo but then must roll back to its input exactly.
- `solid_run` (:85): box deck of #2 with an internal 4-cell solid block (placement top/middle/bottom, optionally strided x2); schemes 0, 1, 9; 20 steps at dt = max_time_step: finite, abs(mass) < 1e-12 per fluid span.
- `clamp_energy` (:129): 8x1x1 box, grav1 -1, rho = p = 1, du[IV1, 6] = 100, dt 1.0, gamma 1.4; E+PE redistribution error abs <= 1e-10 for schemes 1, 9 and work cell, face.
- Timeout 300, long.

### 5. test_implicit_face_work_jacobian.cpp (main)
- Cartesian arms (curved = false): `full_energy_row_matches_frozen_roe_flux` (N=5), `partial_energy_row_matches_frozen_roe_flux` (N=3), `full_cell_work_includes_roe_mass_diffusion`, `partial_cell_work_includes_roe_mass_diffusion` (kVicDiffusiveCell). Unit area and volume, face = {1,2,4,7} only used when curved. Primitive triple w[15] (:33), gamma 1.4 x3, grav -9.8 (:62), dt .5 passed to assembly.
- Assertion: the energy-row source (b0 - b, a0 - a, c0 - c of the assembled blocks with and without gravity) matches the central FD (h = 1.e-5) of the face (or diffusive-cell) work with frozen Roe matrices, for every cell and variable, absolute 1.e-5 (:113).
- Test names containing `curved_face_metrics` are curved (excluded).

### 6. test_lu_failure.cpp (main)
- Grid-free matrix tests (ludcmp / forward sweep: `factor_cases`, `sweep_cases`, float and double, N = 3, 5, legacy and current): zero pivot, near-singular row `4*eps` relative, NaN/Inf, overflow all return 0 / fail; identity returns +1; swapped rows -1 (:19-57). Pivot rule in docs/derivations/290-lu-pivot-tolerance.md: reject when abs(p_j)/s_j <= 8 N eps_T. These do not use a grid (matrix oracles).
- Cartesian `retry_case` (:115): 8x2x1, bounds 0..8, 0..2, 0..1, gamma 1.4, weight 0.029, plm, lmars, `const-gravity {grav1: -1, gravity-work: face, gravity-work-fixer: false}`, rk3, scheme 1 or 9, cfl 0.5; rho 1, p 1.e5. A failed assembly (gamma NaN, or dt 0) or float32 finite near-singular solve (dt 1.e4, p scaled (1+0.01 i)) must leave du and prim unchanged (`torch::equal`), `check_redo` returns 1 (retry) or -1 (stop, current_redo = max_redo), and hydro_u is restored to the saved step input. Tests: partial/full x retry/stop x (NaN gamma, zero dt), `finite_near_singular_forward_masked`, CUDA variants.
- `mesh_terminal_failure_restores_all_blocks` (:242): 2 blocks from test_mesh_multi_block.yaml (cartesian), terminal failure on one block restores both.
- `rest_column_clamp` (:301): 8x2x1 box, scheme 9, grav1 = 0, rho = p = 1, dt 1, float32 and float64, two steps: du and correction exactly zero, prim unchanged, clamp residual exactly 0.

### 7. test_horizontal_flux_covariance.py (293)
- Physics: the x2 face energy flux uses x1-averaged face states, missing the covariance gamma/(gamma-1) dz^2/12 p d(ln T)/dz du/dz, which acts as a spurious stratification eps_spur ~ -0.235/nz^2 (docstring :4-9). Switch `SNAP_FLUX_COVARIANCE` read once per process; arms run in child processes (`ARMS = {"unset": None, "zero": "0", "on": "1"}`, :40).
- Deck (:33-61): GAMMA 1.4, CP 3.5, CV 2.5, g = R = 1, T0 = 1 - z/CP isentropic; x1 in [0,1], x2 in [0, 2 sqrt2]; cells nx1 = nz, nx2 = 2 nz, nx3 1; nz in (16, 32); floors 1e-12; cfl 0.4; scheme 0; `gravity-work: face`; IC `balance_column(..., 1.0, True, 3e-14, 400)`; seed: roll psi ~ sin(pi z) sin(k x), k = 2 pi/LX, amplitude scaled so max abs(w) = 1.e-5; one RK3 step with dt = `max_time_step`; seeded minus unseeded entropy tendency S projected on w at wavenumber k: eps_eff = Re sum rho0 (T0 S^) conj(w^)/(Cp sum rho0 abs(w^)^2).
- Assertions (:190-202): off `BASE = (-0.32, -0.20)` for eps_eff*nz^2; on `abs(.) < FIXED = 0.03`; unset and "0" bitwise identical; on differs from unset; E+PE drift of the seeded box (nz 16, NSTEP = 50, switch on) `<= EPE_TOL = 1.e-12`.

### 8. test_flux_covariance_rows.py (293), Cartesian arms only
- Cartesian deck `card("cartesian")` (:69-76): x1 in [0, 4.0e5], x2 in [0, 8.0e5], x3 [0,1]; nx1 16, nx2 32, nx3 1, ng 3; P0 1.0e5, RHO0 0.1, G 10.0 (isothermal balanced column, `balance_column`); rk3 cfl 0.5 scheme 0, weno5, lmars, limiter False, floors 1e-20; reference-state Tref 300, Pref 1e5; species dry (cv_R 2.5), vapor (cv_R 3.5), cloud (cv_R 9.0, u0_R -3430.0) with ideal-moist EOS and `vapor <=> cloud` nucleation (cloud stays 0).
- Arm 3 offset invariance (:219-239, `NFLOW` = 20 steps): q = 0.02 exp(-z/1.5e5); shear u2 = 20 tanh((z - 2.0e5)/5.0e4), u1 = 0.5 sin(2 pi x/8.0e5) sin(pi z/4.0e5); shifting the vapor `u0_R` between 0 and 2000 changes the primitive state by `rel < OFFSET_TOL = 1e-10` with the switch on (also printed for unset).
- Arm 4 dry Cartesian limit (:242, calls test #7 `eps_eff_nz2`): with the switch on, `abs(got - ref) < CART_TOL = 2e-3` where `CART_REF = {16: -0.012989245130996795, 32: -0.00492854912907752, 64: 0.0002522684000292447}` (:38; the covariance-only form recorded at e7f9904).
- Arms 1, 2 (rest on spherical-polar and gnomonic, uniform tracer on six panels) are curved: excluded.

### 9. test_wb_ref4_order.py (W)
- Deck (:36-63): neutral polytrope, R_d = 1, GAMMA = 5/3, M = 1/(GAMMA-1), G = M + 1, T0 = 1 + Lz - z, rho0 = T0^M, p0 = T0^(M+1), Lz = exp(n/(M+1)) - 1 for n = `EFOLDS = (1.0, 3.0)` pressure e-folds; Lx = 2 Lz, nz = `NZS = (32, 64, 128)`, nx2 = 2 nz, nx3 1; floors 1e-12; cfl 0.4, scheme 0, `gravity-work: face`, `SNAP_FLUX_COVARIANCE=1` always on; `AMP = 1.0e-4` divergence-free momentum mode rho0 v1 = A k sin(qz) cos(kx), rho0 v2 = -A q cos(qz) sin(kx), q = k = pi/Lz; IC = exact 4x4 Gauss-Legendre cell averages of rho, m1, m2, E; one RK3 step at dt = 0.3 dz/sqrt(GAMMA (1 + Lz)); ds = mode minus rest of s = ln(p rho^-GAMMA); N2_eff = (G/GAMMA) sum(-ds/dt w)/sum w^2, w = v1 at t = 0.
- Asserts: with `SNAP_WB_REF4=1`, observed order of abs(N2_eff) >= 2.75 over both doublings (:169); unset: order at last doubling < 2.5 (:171).
- Reference numbers (commit 336101b message), N2_eff*nz^2 at nz 32/64/128: 1 e-fold off +0.1454 / +0.1090 / +0.0873 (orders 2.42, 2.32); on -0.1381 / -0.0707 / -0.0358 (2.96, 2.98); 3 e-folds off +0.5584 / +0.5870 / +0.5598 (1.93, 2.07); on -0.4030 / -0.2257 / -0.1194 (2.84, 2.92). docs/derivations/wb-ref4.md section 9 gives nz 64/128/256 and 2, 5 e-folds (e.g. 5 e-folds on -0.9454 / -0.5492 / -0.2961, order 2.78, 2.89; off +1.5600 / +1.7330 / +1.7072).

### 10-11. Older supporting tests
- test_balance_column.cpp: gtests `a_marched_column_comes_out_at_rest` (rtol 1.e-10, residual before > 1.e-4), `a_balanced_column_is_a_fixed_point`, `a_ghost_free_column_reproduces_a_blocks_own_reference` (bitwise `torch::equal` of pref/psf/dref against a block's own reference), `without_the_clamp_the_two_references_disagree`. Column-level (nx1 cells, 1x1 transverse), uniform and non-uniform dz = dz(0.6 + 0.8 i/(nx1-1)). Not read in full detail beyond the assertions listed.
- test_face_floor.cpp/.yaml: cartesian 32x1x1, x1 in [0, 32], weno5 scale false, reflecting walls, one upper cell dipped by 1e-4 and the cell below cut to 0.2; forward(1.e-4). Not part of the recent gravity-work PRs; included as an older supporting test.

## Excluded (no Cartesian arm)
- test_flux_covariance_seams.py (293): six-panel cubed sphere conservation, spherical-polar rest with x3 flux disabled. Tolerances for reference only: DRIFT_TOL 1e-12, REST_TOL 1e-9, DIFF_TOL 1e-13.
- test_radial_face_moments.cpp (293): spherical-polar / cubed-sphere radial moments (exact rationals 47/1176, 47/576 etc.); its Cartesian counterpart is only the closed form h^2/12.
- Curved arms of tests 1, 4, 5 (spherical-polar, gnomonic) and the cubed-layout refusal in test 2.
- test_vic_moist_device.py (#242): CPU vs CUDA moist VIC step on the tracer deck; not gravity work (DEVICE_TOL 1.0e-9, VIC_FLOOR 1.0e-8).

## Derivation files (docs/derivations/*)
| file | ref | Cartesian content |
|---|---|---|
| 289-covariance-x3-curved.md (+ .tex, 1990 lines) | 293, W | Cartesian: sections 1.1-1.2, 1.4 (face-average moments), 2.1-2.6 (expansions and `sigma_1^2 = dx^2/12` Cartesian, 2.6 at :538), 2.10 (spurious stratification), 3.2, 5 (final form, 5.1 environment switch at :1092), 6 (what each test checks, :1140; tests 7 and 8 above), 4A/4B (row-by-row, general; the dry Cartesian limit is the check). Curved only: 1.3 (per-grid face measure, partly Cartesian), 2.7, 2.8, 2A (centroid term), 8 (cubed-sphere volume), 3 (x3 direction). |
| wb-ref4.md (+ .tex, wb_ref4_weights.py) | W | all Cartesian x1: sections 1-4, 6-9; section 5 is non-uniform x1; section 8 is the oracle of test 9, section 9 the results table, section 10 reconciliation with prototype 473db21. |
| 290-lu-pivot-tolerance.md | main, 293 | grid-free (pivot rule tau_N = 8 N eps_T; float32 VIC conditioning note at :58); basis of test 6. |
| allrows_quadrature.py, energy_row.py, onesided.py, rest_balance.py, verify_centroid_term.py, verify_exact_curved.py, md2tex.py | 293, W | check scripts for the 289 derivation; rest_balance.py (4A.3 rest balance) and energy_row.py are reusable Cartesian-compatible checks; verify_exact_curved.py and verify_centroid_term.py are curved. (Contents not opened; roles taken from the derivation text and file names.) |
| (none for #283-#288 gravity work) | main | No derivation file exists for #284/#285/#288 at e51bdc2; their reasoning is in the commit messages (531e839, 117e449, d59836d). |

## Not determined
- No measured runtimes except test 9 (3.5 s per commit message); CTest TIMEOUT values are upper bounds (grep of tests/CMakeLists.txt).
- RED status stated only where listed in the table; tests 2 (apart from the control arm), 4, 5, 8, 10, 11 carry no RED statement.
- Test 4 and 6 were read for assertions, not run; no test was executed.
- Derivation scripts not opened; test_implicit_options_type.py and test_implicit_advection_cfl.py not read (not gravity-work physics).
