> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# X2COV verification — the claimed x2 energy-flux covariance fix

Base = snapy main 117e449. Fix = 117e449 + x2cov.patch (scratch commit 115a8fa).

## 1. Where the term belongs and its discrete form
- The x2 (and x3) face fluxes are computed by the Riemann solver (riemann/lmars_impl.h) from WENO5 states
  reconstructed along x2 from the x1-averaged primitives. The energy flux is ubar*rho*h = gamma/(gamma-1) pbar ubar
  (+ KE flux) from those averages. The finite-volume flux needs the x1 AVERAGE over the face of the point flux
  gamma/(gamma-1) p m/rho. Exact at second order: <f> - f(<p>,<m>,<rho>) = gamma/(gamma-1) dz^2/12 * u_z * (p_z - p rho_z/rho)
  = gamma/(gamma-1) dz^2/12 p d ln(p/rho)/dz du/dz (the u rho_z and u p_z cross terms cancel identically). So the
  claimed Delta F is the exact covariance, with the LOCAL state (no background needed; zero at rest and for isothermal
  states). Mass flux (linear in m) and the x2 momentum fluxes (pressure linear; rho u w, rho u^2 quadratic in the
  perturbation) carry no linear covariance; the x1 fluxes have no x2 background gradient.
- Discrete form (hydro_forward.cpp, after the x2/x3 Riemann call): cell value C = gamma/(gamma-1) dx1f^2/12 p
  [ln(p/rho)]_z [u]_z with centred x1 differences over cells i-1, i+1 (ghosts as set by the wall functions), interior
  x1 rows only; face value = mean of the two cells sharing the x2 face; added to the face energy flux. Gate
  SNAPY_X2COV = multiplier (unset or 0: code path skipped). Same for x3 faces with the x3 velocity.

## Process note
- A first mechanism pack read bv["hydro_w"] after the step: that is the primitive state at the INPUT of the last
  RK3 stage (u0 + dt L/2 at linear order), so every one-step tendency came out x0.5. Caught by the isothermal control:
  exact answer eps nz^2 = -(R/Cp) 32^2 = -292.57, measured -146.29. Fixed (W from hydro_u) and rerun. The same read
  is in T1L run_t1l.py's diag (a half-step lag in the sampled time): no effect on fitted rates.

## 2. Mechanism: one-step tendency on an eps = 0 background (mech_x2cov.py, mech_table.txt)
eps_eff = effective superadiabaticity the scheme's entropy tendency implies for the seeded eigenmode velocity
(physical value 0 here); x nz^2. "pred" = the change the coded term should make, evaluated independently in python
on the seeded state (factor 1). "bg" = eps of the discretely balanced background itself (w-weighted, centred).

| nz | base (unset) | fix (=1) | fix x2 (=2) | fix - base | pred | bg |
|---|---|---|---|---|---|---|
| 16 | -0.2872 | -0.0475 | +0.1923 | +0.2397 | +0.2397 | +0.062 |
| 32 | -0.2651 | -0.0231 | +0.2189 | +0.2420 | +0.2420 | +0.031 |
| 64 | -0.2531 | -0.0105 | +0.2321 | +0.2426 | +0.2426 | +0.016 |
- Base: eps_spur nz^2 -> -0.25 (claim -0.240, formula -0.241): reproduced. Fixed: the residual falls ~x2 per doubling
  (eps_eff ~ nz^-3), 4 % of base at nz 64. Response linear in the factor (x2 - x1 = x1 - unset = pred to 4 digits): the
  code adds exactly the derived term. dt/4 gives identical numbers (5 digits): a tendency, not a time-step effect.
- Wall-excluded projection within 0.01 of the full one; the error is interior, not a wall effect.
- Control: isothermal background (eps = -R/Cp): exact -292.5714, measured -292.5711 (base and fix); pred = 0.

## 3. Growth runs, base vs fix (18 runs + 2 bitwise, all RUN_EXIT=0; growth_table.txt)
T1L deck (cell = default gravity work, face = face work), fit_t1l.py over the e-fold windows; base = 117e449 fits
(fits_base.json), fix = SNAPY_X2COV=1 (fits_fix.json). All fix fits complete, mass drift <= 1.2e-11.

| run | eps nz^2 | base rel_err | fix rel_err | fix/base | base*eps nz^2 | fix*eps nz^2 | fix complete |
|---|---|---|---|---|---|---|---|
| e2e-2_n16_cell | 5.12 | -0.03483 | -0.005256 | +0.151 | -0.1783 | -0.0269 | True |
| e2e-2_n32_cell | 20.48 | -0.007929 | -0.0005657 | +0.071 | -0.1624 | -0.0116 | True |
| e2e-2_n64_cell | 81.92 | -0.001886 | -4.599e-05 | +0.024 | -0.1545 | -0.0038 | True |
| e1e-3_n16_cell | 0.256 | -1.131 | -0.09462 | +0.084 | -0.2894 | -0.0242 | True |
| e1e-3_n32_cell | 1.024 | -0.1605 | -0.01206 | +0.075 | -0.1643 | -0.0123 | True |
| e1e-3_n64_cell | 4.096 | -0.03635 | -0.001296 | +0.036 | -0.1489 | -0.0053 | True |
| e2.56e-4_n64_cell | 1.049 | -0.1488 | -0.005159 | +0.035 | -0.1560 | -0.0054 | True |
| e1e-4_n32_cell | 0.1024 | -0.9654 | -0.1144 | +0.119 | -0.0989 | -0.0117 | True |
| e1e-4_n64_cell | 0.4096 | -0.4357 | -0.01351 | +0.031 | -0.1785 | -0.0055 | True |
| e2e-2_n16_face | 5.12 | -0.03136 | -0.001884 | +0.060 | -0.1606 | -0.0096 | True |
| e2e-2_n32_face | 20.48 | -0.00749 | -0.0001298 | +0.017 | -0.1534 | -0.0027 | True |
| e2e-2_n64_face | 81.92 | -0.001828 | +1.155e-05 | -0.006 | -0.1498 | +0.0009 | True |
| e1e-3_n16_face | 0.256 | -0.8503 | -0.01515 | +0.018 | -0.2177 | -0.0039 | True |
| e1e-3_n32_face | 1.024 | -0.1493 | -0.002438 | +0.016 | -0.1529 | -0.0025 | True |
| e1e-3_n64_face | 4.096 | -0.03494 | +6.119e-05 | -0.002 | -0.1431 | +0.0003 | True |
| e2.56e-4_n64_face | 1.049 | -0.1424 | +0.0002831 | -0.002 | -0.1493 | +0.0003 | True |
| e1e-4_n32_face | 0.1024 | -1.065 | +0.01212 | -0.011 | -0.1091 | +0.0012 | True |
| e1e-4_n64_face | 0.4096 | -0.4116 | +0.001094 | -0.003 | -0.1686 | +0.0004 | True |

order p = log2(err(nz)/err(2nz)):
  cell eps 0.02 nz 16->32: base p = 2.14, fix p = 3.22
  cell eps 0.02 nz 32->64: base p = 2.07, fix p = 3.62
  cell eps 0.001 nz 16->32: base p = 2.82, fix p = 2.97
  cell eps 0.001 nz 32->64: base p = 2.14, fix p = 3.22
  cell eps 0.0001 nz 32->64: base p = 1.15, fix p = 3.08
  face eps 0.02 nz 16->32: base p = 2.07, fix p = 3.86
  face eps 0.02 nz 32->64: base p = 2.03, fix p = 3.49
  face eps 0.001 nz 16->32: base p = 2.51, fix p = 2.64
  face eps 0.001 nz 32->64: base p = 2.10, fix p = 5.32
  face eps 0.0001 nz 32->64: base p = 1.37, fix p = 3.47

- Fix cuts |rel_err| at every point, by 6.6x to 571x (cell 6.6-41x, face 17-571x; the face factors above ~100x
  are limited by the fit noise). Face work: |rel_err| <= 1.5 % at eps nz^2 >= 0.256 (base 0.18-85 %), and every one of
  these sits above its fit's window_spread (e.g. e1e-3_n16_face 1.52 % vs spread 1.11 %); at eps nz^2 = 0.10
  (e1e-4_n32_face) fix 1.2 % is BELOW its spread 2.5 %, i.e. within fit noise (base 107 %, spread 62 %).
  Cell work keeps a residual -0.004..-0.027 / (eps nz^2) (inferred, not checked: the cell gravity-work error, which face work removes).
- Order in nz: base ~2 (the dz^2 defect; 1.15/1.37 at eps 1e-4, pre-asymptotic with |rel_err| ~ 1). Fix: the cell
  series gives 2.97-3.62, the clean evidence that the O(dz^2) error is gone; the face orders (3.5-5.3) are blurred by
  the fix rel_err changing sign (eps 0.02: -1.3e-4 -> +1.2e-5; eps 1e-3: -2.4e-3 -> +6.1e-5).
- base*eps nz^2 is -0.15..-0.29, not one constant: sigma^2 ~ eps, so rel_err(sigma) -> eps_spur/(2 eps) at large eps
  nz^2 and the wall terms add at nz 16; the one-step tendency (section 2) is the clean collapse.

- Independent review (on fits_base/fits_fix.json, the growth-run logs, x2cov.patch vs bef847c, mech_table.txt):
  `VERDICT: supported. The load-bearing part holds: the fix cuts |rel_err| at all 18 points, the one-step tendency
  matches the prediction, and the off path is bitwise identical.` Its corrections are folded in above (6.6-571x, not
  7-100x; face orders blurred by sign change; base order at eps 1e-4). Its limits: bitwise-off shown on 2 of 18 decks,
  CPU only; 'pred' re-implements the same discrete formula, so it shows the code adds the derived term, not that the
  term is the whole error (the growth runs show that); not covered: moist EOS, tracers, curved grids, the PR's form.

## 4. Safety (safety_x2cov.py) — strong-convection growth runs in the growth pack
- Rest (T1L deck, eps 1e-3 nz 32, 1000 steps): max|u| 2.83e-15 (cell) / 1.95e-15 (face), max|w| 0, base = fix exactly.
- Closed adiabatic walls, face form, no diffusion, seeded mode, 1000 steps: per-step |d(E+PE)|/(E+PE) <= 3.5e-16, drift
  -5.7e-14, base and fix equal while the states differ (max|w| 1.2302e-4 vs 1.2247e-4): the term is conservative.
- Isothermal background, seeded velocity, 100 steps: max|W_fix - W_base| <= 1.8e-14 with |v| 1.5e-5 (round-off).

## 5. Production path (Uranus: cubed sphere, implicit scheme 9, x3 on) — analysis only, no runs
Line numbers are snapy 117e449 `src/hydro/hydro_forward.cpp` unless named.
- Where: right after the x2 and x3 Riemann calls (l.314 and l.329), as in the study patch.
  The fluxes become `_div` at l.418, and the implicit correction (l.579-632, `_apply_implicit_correction`) acts on
  `du = -dt _div` afterwards. Scheme 9 couples x1 columns only, so the term enters exactly like the rest of the
  explicit horizontal flux, at every RK stage. Nothing changes in the implicit block.
- x3: the same covariance is missing and is covered by the second call (sweep dim -3, normal velocity IVZ).
- Momentum and mass fluxes: no linear covariance (DERIVATION_x2cov.md §2d). The mass flux is linear in the state;
  the momentum flux's pressure part is linear and rho u^2 / rho u w are quadratic in velocity. Nothing to add.
- Tracers and moist enthalpy: the energy term in the study patch uses K p d ln(p/rho)/dz, which is exact for one
  ideal gas with constant gamma. For a multi-component moist EOS the general form is dz^2/12 rho u_z h_z, with
  h = (E+p)/rho.
  Every advected mixing ratio Y also misses dz^2/12 rho u_z Y_z in its x2/x3 flux. For condensates this is the same
  spurious-stable bias acting on the moisture gradient. That is not tested here; it needs a moist one-step test like
  the §2 test.
- Cubed sphere (`src/coord/gnomonic_equiangle.cpp`). Two changes are needed.
  (1) Velocity frame. The Riemann solver rotates the face states in place to the local orthonormal frame
      (`prim2local2_`, l.270: u_n = uu2/sqrt(gi22); called from `src/riemann/lmars.cpp` l.60-61). The cell w passed
      to the patch holds the projected components, so the coded u_z is wrong by the face metric factor.
  (2) Seams. The patch builds the term from cell-centred w, including ghosts. On panel edges those ghosts are
      interpolated, so the two sides of a seam face would add different values: not conservative there. The x2/x3
      reconstructed face states are exchanged between blocks (l.296-306, `launch_exchange(... DIM2/DIM3 ...)`).
  Recommended production form: after each Riemann call, take the face states wlr2 (already in the local frame after
  the call) and set w_f = (wl + wr)/2 per x1 row. Then
  dF = gamma/(gamma-1) dz^2/12 p_f D[ln(p_f/rho_f)] D[u_n,f], with centred differences in x1 on the face rows.
  This gives frame and seam consistency for free and needs no cell-to-face average.
  Unverified: that wlr2 carries x1 ghost rows and is identical on both sides of a seam. The check is to print
  max|dF_left - dF_right| on a seam face in a 1-step cubed-sphere run.
- Spherical geometry: face_area2 = x1v dx1f (l.197, r-weighted) while cell_volume is r^2-weighted (l.205). The extra
  height-average terms are O(dz^2 F_z / r), i.e. O(H/r) of the term. For Uranus (H ~ 30-50 km, r ~ 25,000 km) that
  is <= 2e-3, negligible.
- Stretched x1 grid: the patch already uses non-uniform centred differences (x1v) and the local dx1f, so it is
  consistent to O(dz^2) on a smoothly stretched grid (residual O(dz^3) there, O(dz^4) on a uniform one).

## 6. #289 item 3: implicit scheme 9, and CUDA vs CPU (CPU and a V100 GPU; x2cov_deck.py)
Deck: the T1L box, inviscid, built-in reflecting walls, analytic anelastic roll seed, face form, RK3.
Commit bef847c: the patch plus x2cov_deck.py and a README.
One-step tendency at eps = 0, eps_eff*nz^2:
| case | off | on (x1) | on (x2) | on - off | pred | dt |
|---|---|---|---|---|---|---|
| scheme 0, nz32 | -0.25134 | -0.00532 | | 0.24602 | 0.24601 | 0.01059 |
| scheme 9, nz16 | -0.25786 | -0.01466 | +0.22854 | 0.24320 | 0.24320 | 0.03001 |
| scheme 9, nz32 | -0.25137 | -0.00535 | +0.24066 | 0.24602 | 0.24601 | 0.01497 |
| scheme 9, nz64 | -0.24655 | +0.00014 | +0.24683 | 0.24669 | 0.24669 | 0.00748 |
| scheme 9, nz32, CUDA | -0.25137 | -0.00535 | | 0.24602 | 0.24601 | 0.01497 |
- The term applies unchanged under scheme 9: scheme 9 = scheme 0 to 4 digits at a 1.4x larger dt.
  On - off = pred to 5 digits; linear in the factor. This is the DERIVATION §6 prediction (entropy part untouched by
  the x1 solve).
- Residual with the term on, in this deck: -0.0147, -0.0054, +0.0001. It is smaller and differently shaped than
  with the T1L fixed-T walls (-0.047, -0.023, -0.010), so the residual depends on the wall treatment. Not
  isolated (unverified).
- Stability: 2000 steps (t = 30), eps 0.02 and 1e-3, nz32, scheme 9, on and off: all finite;
  max_t |E+PE - E0|/E0 = 1.1e-13 for all four.
  The term raises the growth: max|w| at t = 30 is 6.982e-5 on vs 6.864e-5 off (eps 0.02), and 1.1766e-5 vs
  1.1325e-5 (eps 1e-3). That is the expected sign: the spurious stability is removed.
- CUDA vs CPU, term on, 2000 steps at eps 0.02 (a growing mode):
  - rho: max diff 4e-14; p: 3e-15.
  - w: 3.0e-13 against |w| 7e-5, i.e. 2.2e-9 of range; u: 4.7e-10 of range.
  - Term off, same comparison: w 2.9e-9, u 7.0e-10. Same size: the term adds no device-dependent difference. The
    residual is round-off amplified by the unstable mode over 2000 steps. One-step tendencies are identical to 5
    digits.
  - For scale, on vs off (CPU) differs by 8.5e-3 of the w range: about 4e6 times the device difference.

## 7. The reference test (10-08): the PR code comes from a separate implementation; this study keeps the reference test
- A PR skeleton (one local commit 725a7ed off 117e449, Cartesian-gated YAML
  option) was dropped and kept unpushed for reference only.
- Reference test committed on study/x2cov-verify: 9a4e927388f1c80dee02df4a36cb6095d6136317 (parent bef847c):
  tests/test_horizontal_flux_covariance.py + its tests/CMakeLists.txt line (python;hydro, TIMEOUT 180). eps = 0, one RK3
  step, Cartesian nz 16/32, each arm (unset / SNAPY_X2COV=0 / =1) in its own process (the switch is cached): off
  eps_eff nz^2 in [-0.32,-0.20], on |.| < 0.03, unset == 0 bitwise, on != unset, E+PE drift over 50 steps <= 1e-12.
  Uses face gravity work: with cell work the cell form's own O(dz^2) error leaves on = -0.052 at nz 16 (> 0.03).
- Fail -> pass (CPU): base 117e449: off = on = -0.25776 / -0.25134, FAIL 'on |.| >= 0.03' x2 and
  'the switch changed nothing' x2, exit 1. Fix: off -0.25776/-0.25134, on -0.01456/-0.00532, drift
  2.94e-15, exit 0 (~11 s). nz 32 values equal the #289 item-3 deck (section 6).
- Owed later: gates on the PR head (ctest -j1; the T1L points with the PR's switch).

## 8. Deep boxes: the onset error left with the term on (10-08)
- Question: with dF on, how large is the remaining onset error in 3 H and 5 H boxes, and does it scale as dz^2 (the
  second O(dz^2) term: the well-balanced reference's face density offset, which grows with depth)?
- Deck: evp_deep.py + run_deep.py = the T1L EVP/driver with the box N_H = ln(p_b/p_t) pressure scale heights
  deep (Lz = (1 - exp(-beta N_H))/beta; the 1 H deck is N_H = 1.18; a depth in bottom-H units cannot reach 5 H since
  the adiabat's T hits 0 at z = Cp), Lx = 2 sqrt(2) Lz, Ra = eps Lz^4/mu^2 = 50 Ra_c. Points: eps 1e-3 at nz 32 and 64,
  eps 2.5e-4 at nz 64 (eps nz^2 = 1, 4, 1), face and cell, term off vs on: 24 runs.
- EVP (evp_deep.json): oracle lz = 1 reproduces evp_t1l Ra_c(eps 0.02) = 1268.5968053 to 2.3e-12
  (PASS); sigma converged to <= 5e-10 over Chebyshev n 64-160. 3 H: Lz 2.012, rho_b/rho_t 8.5, Ra_c 3565, sigma 0.01704
  (eps 1e-3) / 0.008515 (2.5e-4). 5 H: Lz 2.656, contrast 35.4, Ra_c 8220, sigma 0.01621 / 0.008098.
- Pilot (3 runs x 2000 steps): balance residual <= 1e-14, RUN_EXIT 0; 5 H nz 64 dt is diffusion-capped
  (C_z 0.30). Both arms use the x2cov iso (unset = bitwise 117e449, section 3).
- 24 runs; fit with fit_t1l.py.
- RESULT (24/24 RUN_EXIT 0, all fits complete, mass drift <= 3.4e-12; table_deep.txt):
  face work, term on: rel_err +1.33e-2 / +4.05e-3 / +1.61e-2 (3 H: e1e-3 n32 / e1e-3 n64 / e2.5e-4 n64) and
  +3.85e-2 / +1.03e-2 / +4.11e-2 (5 H), against base -0.159 / -0.037 / -0.156 (3 H), -0.180 / -0.042 / -0.177 (5 H):
  opposite sign to base, on/off = -0.08..-0.11 (3 H), -0.21..-0.25 (5 H); 1 H: |on| <= 2.4e-3. dz^2 checks: fixed
  eps nz32/nz64 = 3.28 (3 H), 3.73 (5 H) (4 = dz^2); fixed eps nz^2 ratio = 0.82, 0.94 (1 = dz^2/eps). Each on value is
  >= 10x its window spread. Cell work, term on: +/-3e-3..+1.8e-2, smaller (cancels against the cell form's own error),
  scaling not clean (3 H changes sign). Base itself grows with depth (face e1e-3 n32: -0.149 / -0.159 / -0.180).
- Reading: a second O(dz^2) defect, destabilising, grows with depth, remains after dF; which term it is is not shown
  here (the one-step row split, section 9, addresses that).
- Independent review: `VERDICT: supported (the measured residual and its dz^2 scaling hold; the "second defect" reading is a
  hypothesis, and the claim itself says it is not shown)`. Corrections: at eps nz^2 ~ 1 on/off = 8.4-10.4 % (3 H),
  21.4-23.2 % (5 H); the 1 H n32 face residual -2.4e-3 is real (15x its spread). Two-resolution order 1.71 (3 H),
  1.90 (5 H); an A + B dz^2 fit leaves a ~+0.09 % floor at every depth (cause unknown). Rival reading: the dF term's own
  discretisation over-corrects. Settling: nz 128 points, and the term scaled by 0.5 (a residual tracking the coefficient
  = the term itself).

## 9. One-step row split on the left eigenfunction (10-09)
Question: does snapy carry an O(dz^2) pair from w = <m1>/<rho>, split into a mass-row part and an energy-row part of
opposite sign? Method (lev/onestep_lev.py): T1L 1 H deck, eps 1e-3, discretely balanced rest state. Seed = the EVP
mode as exact cell averages of (rho, m1, m2, E), max|w| 1e-4, +A and -A; take the odd part. One rk3 step at cfl 0.4.
e = odd/dt - (exp(sigma dt) - 1)/dt * seed. The EVP's left eigenvector vl/W gives phi; it is mapped to conserved rows
(phi_rho - Cv T0 phi_theta, phi_w, phi_u, phi_theta) and projected: dsig/sig = <phi_row, e_row>/<phi, seed>/sigma.
Oracles:
- d sigma/d Ra from vl matches a finite difference to 1.7e-6 (PASS).
- The split must not depend on the EVP resolution: phi from n 64/96/128/160 moves every row by <= 0.54 % of the
  largest row. Taken alone, phi = vl/W converges only algebraically (3e-3 at n 96 vs 128), because the wall rows
  pollute it, so its own 1e-5 gate FAILs. The split is the gate.
- dt independence: cfl 0.1 changes the base total from -3.6165 % to -3.6170 %.

| nz  | gw   | switch | dens     | mom1    | mom2    | Etot     | total     | measured onset (fits) |
|-----|------|--------|----------|---------|---------|----------|-----------|-----------------------|
| 64  | cell | off    | +7.970 % | -5e-6   | -3e-6   | -11.585 % | -3.617 %  | -3.635 % |
| 64  | cell | on     | +7.970 % | -3e-6   | -3e-6   | -8.114 %  | -0.145 %  | -0.130 % |
| 64  | face | off    | +7.964 % | -2e-6   | -6e-6   | -11.441 % | -3.478 %  | -3.494 % |
| 64  | face | on     | +7.964 % | -1e-6   | -5e-6   | -7.970 %  | -0.007 %  | +0.006 % |
| 128 | cell | off    | +2.034 % | -1e-6   | -3e-7   | -2.918 %  | -0.885 %  |          |
| 128 | cell | on     | +2.034 % | -1e-6   | -2e-7   | -2.051 %  | -0.017 %  |          |
| 128 | face | off    | +2.033 % | -1e-6   | -6e-7   | -2.896 %  | -0.863 %  |          |
| 128 | face | on     | +2.033 % | -9e-7   | -5e-7   | -2.028 %  | +0.005 %  |          |

(mom1/mom2 are fractions, not %.) The EVP-resolution spread of the "on" totals is about +-0.02 % at nz 64 and
+-0.01 % at nz 128, so those totals are zero within it, except nz 64 cell, which is -0.12 to -0.15 %.

Reading:
1. The pair exists. dens is +7.97 % at nz 64 and +2.03 % at nz 128 (ratio 3.92, dz^2), and it is destabilising. Its
   energy-row counterpart is -7.97 % / -2.03 %. They cancel, so an energy-only or total number hides both.
2. The switch moves only Etot. dens is identical to 4 digits off vs on. Etot moves by +3.471 % (nz 64) and
   +0.868 % (nz 128), ratio 4.00. That move is the whole of the base onset error.
3. Analytic check (lev/predict_lev.py): put dw = (dz^2/12)(rho0_z/rho0) w_z into the mass flux and the enthalpy flux,
   then project with the same phi. Predicted: dens +8.338 % / +2.085 %, Etot -8.393 % / -2.098 %. Measured over
   predicted: dens 0.956 / 0.976 (tends to 1 as dz -> 0); Etot (on, face) 0.950 / 0.967. Predicted net -0.054 % /
   -0.014 %. The conversion error accounts for the mass row, and for the energy row once dF is in.
4. The totals reproduce the measured onset errors from the growth runs to 0.02 % of sigma.
5. Caveat (independent review): the dens/Etot split is snapy's own bookkeeping, not an invariant. The mapping is forced by
   snapy's variables, (M Q^-1)^H phi with E = internal + kinetic and no rho g z (src/eos/ideal_gas_impl.h:29-31).
   With E + rho g z, or E - h0 rho, weight would move between the rows. The pair is one error: a velocity error dw
   carries both the mass and its enthalpy. Only the net is physical, and with dF on it is ~0 (face).
   Residual of the dens row, measured minus predicted: -0.37 % (nz 64), -0.05 % (nz 128). The ratio is 7.3, about
   dz^3, so any other O(dz^2) mass-flux error is <= ~0.5 % of the dens row. Same error class elsewhere: the x3 faces,
   and tracer/moist rows converted as q = <rho q>/<rho>.
Independent review: `VERDICT: supported (numbers, switch and totals checked; two limits: the analytic match was not re-run,
and the dens/Etot split depends on the choice of variables)`. Its settling checks are done. predict_lev.py
reprints dens +8.3384e-02 / +2.0846e-02 and Etot -8.3928e-02 / -2.0982e-02. snapy's E has no rho g z term.

## 10. Deep-box row split: which row carries the residual with dF on (10-09)
Section 9's one-step on N_H 3 and 5 (onestep_lev.py --nh: deep/evp_deep.py operator, deep/run_deep.py card and walls),
eps 1e-3, nz 32/64, face and cell, switch off/on. Rows are the median over EVP n 64..192 (reproject.py), +- half the
range. vl/W converges slowly near the walls, so the bar is +-0.07-0.09 % at nz 64 and +-0.2-0.3 % at nz 32. Table:
lev/table_lev_deep.txt (lev/table_lev_deep.py). Abridged, % of sigma, switch on unless marked:

| N_H | nz | gw   | dens  | Etot(off) | Etot(on) | mom1+2 | total(on)    | growth run | dens/dens_V | Etot(on)/Etot_V | X     |
|-----|----|------|-------|-----------|----------|--------|--------------|------------|-------------|-----------------|-------|
| 1   | 64 | face | +7.97 | -11.43    | -7.96    | -0.001 | +0.00+-0.02  | +0.01      | 0.956       | 0.949           | +0.06 |
| 3   | 32 | face | +30.81| -45.77    | -29.47   | -0.003 | +1.34+-0.22  | +1.33      | 0.920       | 0.846           | +2.57 |
| 3   | 64 | face | +8.04 | -11.72    | -7.64    | -0.001 | +0.40+-0.07  | +0.41      | 0.960       | 0.877           | +0.72 |
| 5   | 32 | face | +32.49| -49.26    | -28.59   | -0.007 | +3.88+-0.29  | +3.85      | 0.930       | 0.752           | +6.75 |
| 5   | 64 | face | +8.44 | -12.59    | -7.41    | -0.002 | +1.02+-0.09  | +1.03      | 0.966       | 0.780           | +1.77 |
| 3   | 64 | cell | +8.04 | -12.04    | -7.95    | -0.001 | +0.09+-0.07  | +0.10      | 0.960       | 0.913           | +0.41 |
| 5   | 64 | cell | +8.44 | -13.18    | -7.99    | -0.002 | +0.44+-0.09  | +0.47      | 0.966       | 0.841           | +1.19 |

X = total(on) - net_V * dens/dens_V is the residual outside V and outside dF. Unscaled (total - net_V) it differs
by < 0.03 at nz 64.
Findings:
1. All 10 one-step totals reproduce the growth-run residuals within their bars; the largest gap is 0.14 against
   +-0.29.
2. The mass row follows V at every depth, with dens/dens_V = 0.956/0.960/0.966 at nz 64. It is identical off vs on
   and face vs cell. The momentum rows are < 0.01 %.
3. dF moves Etot by its analytic projection: measured/predicted 0.997 (nz 32) and 0.9998 (nz 64) at every depth.
   An independent check (lev/cov_check.py, 16-point Gauss quadrature of the EVP mode per cell) asks whether dF is the
   x2-face covariance the base scheme misses: <gamma/(gamma-1) p m/rho> - gamma/(gamma-1)<p><m>/<rho>, projected,
   is dF to 1.0003 (nz 64) and 1.001 (nz 32) at 1, 3 and 5 H. So dF corrects exactly the covariance it targets at
   every depth; it does not over-correct.
4. The residual is in the energy row. With dF on, Etot falls short of V's energy counterpart more and more with depth
   (Etot(on)/Etot_V 0.949/0.877/0.780 face, nz 64). X = +0.06/+0.72/+1.77 % (face) and -0.08/+0.41/+1.19 % (cell)
   at 1/3/5 H, nz 64. nz 32 -> 64 ratio: 3.6/3.8 (face), 2.3/3.5 (cell; nz 32 bar +-0.23-0.29), so roughly dz^2.
   About 40 % of X at 5 H (60 % at 3 H) is gone in the cell gravity-work form, so part of X sits in the gravity-work
   source.
5. Coincidence noted by the independent review, unexplained: with dF off, the face energy row minus the scaled V energy row is
   -3.41/-3.36/-3.41 % at nz 64 (1/3/5 H). So X(N_H) - X(1 H) matches dF(N_H) - dF(1 H): 1.710 vs 1.714 at 5 H,
   0.666 vs 0.619 at 3 H. The SNAPY_X2COV = 0.5 run does not settle this. The dF move is exactly linear in the
   multiplier (item 3), so every reading predicts total(0.5) = total(0) + dF/2. Item 3's quadrature is the settling
   check, and it says dF is the right amount.
6. The rows are snapy's bookkeeping (section 9, caveat 5): with E + rho g z the split would move. "Energy row" means
   "outside the V pair, in snapy's E equation".
Independent review (before item 3's quadrature check): `VERDICT: unverified`. The numbers recompute, the scaling does not
matter, and the EVP-n spread is 20x smaller than the trend. Open: whether dF is the right amount at depth, which
item 3 now settles in dF's favour. Its suggested 0.5x run does not discriminate (item 5).
Next test: the both-switches rerun with SNAPY_WB_REF_EXACT. X is the target; if X vanishes, the reference
offset is the energy-row piece.

## 11. PR-head gates: commits 807cfd8 and e7f9904 (10-09)
Heads: 807cfd8 (the sha under review) and e7f9904 (branch tip since; adds the curved centroid term, which is
`face_centroid_shift_x1() = 0` in Cartesian). Switch: env `SNAP_FLUX_COVARIANCE` (boolean, read once; unset/0 = off).
Builds: FetchContent on the 117e449 build's dependency sources (cmake/ unchanged between 117e449 and both heads;
same tags). 807cfd8: BUILD-GOOD PASS (2.11.3.dev1+g807cfd8). e7f9904: built the same way.

Gate 3 (row split, T1L 1 H, eps 1e-3, one step, same seed and dt; cmp_lev.py; 8 runs EXIT=0). % of sigma, median
over EVP n 64..192:

| case | PR on Etot | study on Etot | PR - study Etot | other rows PR - study | PR off Etot | gate (< 0.02 %) |
|---|---|---|---|---|---|---|
| n64 face | -7.9624 | -7.9638 | +0.0014 | 0.0000 | -11.4320 | PASS |
| n64 cell | -8.1069 | -8.1083 | +0.0014 | 0.0000 | -11.5765 | PASS |
| n128 face | -2.0265 | -2.0266 | +0.0001 | 0.0000 | -2.8936 | PASS |
| n128 cell | -2.0489 | -2.0490 | +0.0001 | 0.0000 | -2.9159 | PASS |

The two implementations differ by 2e-5 (n64) / 4e-6 (n128) of the residual, ~nz^-3: the PR evaluates the term from
the face states (wl+wr)/2, the study averages two cell values; both are the same O(dz^2) term. Noise floor (off arms,
both = 117e449, seed from a fresh EVP solve that agrees to round-off): 1e-12..1.5e-9 relative, Etot rows equal to 1e-9 %.
Gate 2 and the e7f9904 Cartesian gates (bitwise.sh: cmp of card.out0.0000{0,1}.nc + diag.txt; T1L decks,
full runs, RUN_EXIT=0):

| comparison | deck e2e-2 nz16 cell | deck e1e-3 nz32 face |
|---|---|---|
| 807cfd8 switch off vs 117e449 | IDENTICAL | IDENTICAL |
| e7f9904 switch off vs 117e449 | IDENTICAL | IDENTICAL |
| e7f9904 switch on vs 807cfd8 switch on | IDENTICAL | IDENTICAL |
| sanity: e7f9904 on vs e7f9904 off | DIFFER (card.out0.00001.nc) | DIFFER (card.out0.00001.nc) |

So in Cartesian the centroid term adds exactly nothing (face_centroid_shift_x1 = 0 there) and the switch is live.

Cubed-sphere rest gate on e7f9904 (cs_rest.py; e7f9904 off/on and 117e449). Deck and
initial state = snapy tests/test_hydrostatic.cpp at 117e449 (6 gnomonic panels in one process, nx2 = nx3 = 8, weno5,
lmars, rk3 cfl 0.4, explicit, const gravity, isentropic column), changed only in nx1 24 -> 32, x1 [10, 11] ->
[1000, 1300] and 300 steps instead of 100. Depth: the deck's adiabat ends at 3.5 H0 (H0 = p0/(rho0 g) = 100), so ~10 H deep is impossible with
this initial state; 300 = 3 H0 = 6.8 pressure e-folds, top local scale height 14 > dz 9.4. 300 steps, interior max|u|:

| step | 1 | 10 | 12 (peak) | 50 | 100 | 200 | 300 | max\|u2,u3\| over run |
|---|---|---|---|---|---|---|---|---|
| 117e449 | 3.34e-8 | 3.09e-7 | 3.12e-7 | 7.68e-8 | 2.40e-8 | 8.60e-9 | 5.01e-9 | 2.58e-14 |
| e7f9904 off | 3.34e-8 | 3.09e-7 | 3.12e-7 | 7.68e-8 | 2.40e-8 | 8.60e-9 | 5.01e-9 | 2.58e-14 |
| e7f9904 on | 3.34e-8 | 3.09e-7 | 3.12e-7 | 7.68e-8 | 2.40e-8 | 8.60e-9 | 5.01e-9 | 2.73e-14 |

- Off vs 117e449: final state (all six blocks' hydro_w, ghosts included) byte-identical (cmp of final_w.npy) and
  the whole max|u|/dt history exactly equal. PASS.
- On vs off: max|u1| agrees to 3.1e-7 relative at every step (~1e-13 absolute); the horizontal velocities stay at
  round-off in both (2.7e-14 vs 2.6e-14). Final interior/ghost state differs by <= 3e-13 in p (of 95) and 6e-15 in rho.
  The term is proportional to the normal velocity, so at rest it acts only on round-off. On is no worse than off.
- Not round-off rest in either arm (nor in 117e449): the radial velocity is a 3e-7 transient (Mach ~3e-8,
  sound speed 11.8) from the base scheme's discrete hydrostatic imbalance, decaying to 5e-9 by step 300. The
  switch does not change it.

ctest -j1 (CPU build with tests, `-E test_shallow_xy_decomp`; arms 117e449, 807cfd8, e7f9904). All three arms: the same 178 passes
(72 snapy tests, among them test_hydrostatic.release, the cubed-sphere flux-positivity and exchange tests) and the
same 13 snapy failures, all known environment-bound ones (the MPI/UCX/gloo exchange tests, straka,
restart_cycle_limit, mesh_multi_block, exchange_decomp). The pass and fail sets are identical (diff empty) for
807cfd8 and e7f9904 against 117e449. PASS. Bookkeeping: the reused Eigen sources also register Eigen's own suite
(820 "Not Run" plus 13 Eigen resize/blas failures). With the 13 snapy failures that makes the footer's "846 failed
out of 1025" in every arm (178 passed + 1 skipped + 846). test_straka fails at its torchrun --nproc-per-node=2
launch (CalledProcessError), the same in all arms.

Gates 4 and 5 (fit_pr.py, the study's fit, fit_t1l.py).
Growth-rate rel_err with the term on, PR (807cfd8) vs the study switch (section 3 table, deep table):

| run | PR rel_err | study rel_err | PR - study | study window spread | term's shift (off -> on) |
|---|---|---|---|---|---|
| e1e-3 nz32 cell | -1.1834e-2 | -1.2059e-2 | +2.25e-4 | 2.6e-4 | +0.148 |
| e1e-3 nz32 face | -2.2153e-3 | -2.4379e-3 | +2.23e-4 | 1.6e-4 | +0.147 |
| e1e-3 nz64 cell | -1.2822e-3 | -1.2960e-3 | +1.39e-5 | 6.0e-5 | +0.035 |
| e1e-3 nz64 face | +7.50e-5 | +6.12e-5 | +1.38e-5 | 1.1e-5 | +0.035 |
| e2.56e-4 nz64 cell | -5.1044e-3 | -5.1586e-3 | +5.42e-5 | 2.8e-4 | +0.144 |
| e2.56e-4 nz64 face | +3.3715e-4 | +2.8308e-4 | +5.41e-5 | 6.8e-5 | +0.143 |
| deep 3 H e1e-3 nz64 cell | +1.0502e-3 | +1.0339e-3 | +1.63e-5 | 2.3e-4 | +0.041 |
| deep 3 H e1e-3 nz64 face | +4.0669e-3 | +4.0506e-3 | +1.63e-5 | 8.9e-5 | +0.041 |

All fit windows complete, mass drift <= 7e-12. PR - study is the same for face and cell (it does not depend on the gravity-work
form), falls 16x from nz32 to nz64 (dz^4), and is 0.15 % (nz32) / 0.04 % (nz64, eps 1e-3) / 0.04 % (nz64, eps 2.56e-4) of the term's own shift. That is
the higher-order difference between face-state and cell-averaged evaluation seen in gate 3. It is at or below the
study fit's window spread except nz32/nz64 face (1.4x, 1.3x the spread).

Every build here (117e449 and both heads) carries the same local build patch (CUDA arch list,
process_group torch-version guard; CMakeLists.txt and src/layout/process_group.cpp, 4 lines), so arms differ only
by the PR commits.

Independent review (read-only, on the run artifacts; RESULT sha256 47417b6): VERDICT supported. It cmp'd the
bitwise pairs and the cubed-sphere final states itself, confirmed from the run logs that each arm ran the stated
build and switch value, diffed the ctest sets, and checked the cs_rest.py deck against test_hydrostatic.cpp.
It corrected the Eigen bookkeeping (now fixed above) and the unlisted 300-step change (now listed).

### 11b. Assembled head 147005a (10-09)
147005a = e7f9904 + tests/test_horizontal_flux_covariance.py + its CMake line (diff: tests/ only; the cell-volume
patch 3fa7bc0 is not on the branch yet). The lifted test still drives the study switch: it sets
and pops `SNAPY_X2COV` (lines 2, 15, 179, 181), which the head's code never reads, so its "on" arm runs the term off.
Runs (e7f9904 build = 147005a's library):

| test file | 117e449 | head library (e7f9904 = 147005a) |
|---|---|---|
| as lifted (SNAPY_X2COV) | rc 1: on = off = -0.258 / -0.251, "switch changed nothing" | rc 1, the same, RED |
| switch renamed to SNAP_FLUX_COVARIANCE (sed, 4 lines) | rc 1, RED | rc 0, GREEN: eps_eff nz^2 on -0.0130 (nz16), -0.0049 (nz32); off -0.258 / -0.251 |

E+PE drift over 50 steps with the term on: 2.9e-15. Fix for the branch: replace SNAPY_X2COV by SNAP_FLUX_COVARIANCE in the
test (the "0" arm still means off there). Waiting for the assembled sha (with 3fa7bc0) for the build, full ctest,
cell-volume test and the cubed-sphere rest gate.

### 11c. Assembled head 10270ed (the sha to gate; 10-09)
10270ed = e7f9904 -> 147005a (lifted test) -> 0486f2c (cell volume, from 3fa7bc0) -> 10270ed (test switch renamed to
SNAP_FLUX_COVARIANCE). Same recipe (same 4-line local build patch).

| gate | result |
|---|---|
| build | BUILD-GOOD PASS, 2.11.3.dev5+g10270ed |
| compile warnings, touched src (coordinate, gnomonic_equiangle, spherical_polar, hydro, hydro_forward) | default flags: none; -Wall -Wextra: 82, all also at 117e449, 0 new (unused-parameter in headers, 4 unused T11 in gnomonic_equiangle.cpp) |
| ctest -j1 | 180 pass = 117e449's 178 + test_cubed_sphere_cell_volume_python + test_horizontal_flux_covariance_python; fail set identical to 117e449 (13 snapy env-bound) |
| test_restart_cycle_limit (separately) | fails at its torchrun --nproc-per-node=2 launch of straka (CalledProcessError) in every build here, 117e449 included; on this build host it cannot show the e7f9904 flakiness |
| test_horizontal_flux_covariance.py | 117e449 RED (on = off, "switch changed nothing"); head GREEN (eps_eff nz^2 on -0.0130 / -0.0049, off -0.258 / -0.251) |
| test_cubed_sphere_cell_volume.py | 117e449 RED (six-panel volume off by 3.3e-3, div(r rhat) != 3 by 3.4e-5); head GREEN |
| Cartesian, switch off vs 117e449 (2 decks) | IDENTICAL, IDENTICAL |
| Cartesian, switch on vs e7f9904 on (2 decks) | IDENTICAL, IDENTICAL (on != off: DIFFER) |
| cubed-sphere rest, off / on (300 steps) | max\|u1\| peak 3.124e-7 (step 12) -> 5.01e-9 (step 300) in both, as in 117e449; on/off u1 rel diff <= 6.3e-7; max\|u2,u3\| 2.44e-14 on vs 2.36e-14 off. PASS (on no worse than off) |

Head off vs 117e449 on the cubed sphere is no longer byte-identical, as expected, since the cell-volume patch
changes the gnomonic geometry. The final state differs by 4.6e-12 in p (of 95) and 3.7e-14 in rho; the u1 history
differs by 1.6e-5 relative and the same transient remains.

Independent review (read-only, on the run artifacts; HEAD 10270ed57aca, evidence hashed): VERDICT supported. It
re-ran the cmp on both decks, confirmed the run logs name the right build and switch for every arm, saw the RED
outputs at 117e449 were real check failures, and confirmed the ctest diffs. Its two open points are settled:
(a) a late mtime on src/coord/coordinate.hpp is the warning job's own `touch`. git status shows only the local build
patch, and the build was made from HEAD content before it. The -Wall line
numbers point at snap/coord/coordinate.hpp, a different file from src/coord/coordinate.hpp.
(b) The -Wall matcher collapses repeated identical warnings. The independent review counted the repeated keys against the
source (T11 4/4, prim 3/3, flux 3/3, as at 117e449), so none is hidden here.

### 11d. Head 0b6b6ef (10-09)
0b6b6ef = 10270ed -> 75b0e90 (all-rows centroid shift; judged DEFECTIVE in review: mass/tracer covariance on
non-density-weighted pairs) -> 0b6b6ef (density-weighted mass and tracer rows, dry row = minus their sum, energy row
rho s2 D1[h] D1[u_n] with h = (W->I + p)/rho, centroid term on every row, momentum centroid with p* in the lateral
geometric source). Touched vs 10270ed: src/hydro/hydro_forward.cpp only in src (+ tests/test_flux_covariance_rows.py, tests/CMakeLists.txt, docs).
Same recipe (same 4-line local build patch).

| gate | result |
|---|---|
| build | BUILD-GOOD PASS, 2.11.3.dev7+g0b6b6ef |
| compile warnings, touched src (coordinate, gnomonic_equiangle, spherical_polar, hydro, hydro_forward vs 117e449) | default flags: none (65 objects rebuilt); -Wall -Wextra: 82, all also at 117e449, 0 new |
| 1. ctest -j1 | 181 pass = 117e449's 178 + test_cubed_sphere_cell_volume_python + test_horizontal_flux_covariance_python + test_flux_covariance_rows_python; fail set identical to 117e449 (13 snapy env-bound + Eigen's); footer 846 failed of 1028 (1025 at 117e449, 1027 at 10270ed: the new tests registered). The test_eos.cpp "macro major" compile error is in every build here (117e449 included) |
| 3. Cartesian, switch off vs 117e449 (2 decks) | IDENTICAL, IDENTICAL |
| 2a. Cartesian, switch on vs e7f9904 on (2 decks) | DIFFER, as expected: max\|du\| 4.8e-10 / 1.1e-10 against the term's own max\|du\| (e7 on - off) 2.6e-6 / 2.3e-6, ratio 1.8e-4 (eps 2e-2 nz16 cell) / 5.0e-5 (eps 1e-3 nz32 face); rho, p equal in the float32 output |
| 4. test_flux_covariance_rows.py (new) | head GREEN: rest max\|v\|/c_s 4.12e-11 (spherical-polar), 4.13e-11 (gnomonic), on = off; uniform vapor 2.6e-17; offset invariance on 2.9e-12; dry Cartesian within 3.1e-5 of the e7f9904 reference. 10270ed RED (offset invariance with the term on 8.9e-8 > 1e-10; the rest passes). 117e449 RED (switch absent: Cartesian -0.258 etc.) |
| 4. RED reference 75b0e90 (built the same way) | test_flux_covariance_rows.py RED: dry Cartesian eps_eff nz^2 on -0.6249 / -0.6209 / -0.6167 (nz 16/32/64; the implementer's reported -0.62 reproduces), offset invariance on 2.8e-5; rest and uniform tracer pass. So the new test catches the non-density-weighted pairs on two of its four checks |
| 4. test_horizontal_flux_covariance.py (lifted) | head GREEN (on -0.01302 / -0.00494, off -0.25776 / -0.25134); 117e449 RED |
| 4. test_cubed_sphere_cell_volume.py | head GREEN (volume 0, div(r rhat) - 3 3.1e-14); 117e449 RED |
| 5. cubed-sphere rest, off / on (300 steps, cs_rest.py) | off byte-identical to 10270ed off (final_w and the whole history); on vs off: u1 history rel diff <= 5.4e-7, final state <= 3e-13 in p (of 95); max\|u1\| peak 3.124e-7 (step 12) -> 5.01e-9 (step 300) in all arms, max\|u2,u3\| 3.1e-14 on vs 2.4e-14 off. PASS (on no worse than off) |

Dry Cartesian one-step eps_eff nz^2 (eps_cart.py = the lifted test's eps_eff_nz2 at nz 16, 32, 64):

| nz | 0b6b6ef on | implementer's report | e7f9904 on (10270ed build) | 0b6b6ef - e7f9904 | off (0b6b6ef = 117e449, bit-equal) |
|---|---|---|---|---|---|
| 16 | -0.0130201 | -0.013020 | -0.0129892 | -3.08e-5 | -0.257757 |
| 32 | -0.0049372 | -0.004937 | -0.0049285 | -8.70e-6 | -0.251336 |
| 64 | +0.0002498 | +0.000250 | +0.0002523 | -2.45e-6 | -0.246537 |

The implementer's numbers reproduce to the printed digits. The test's CART_REF (the e7f9904 values) matches the 10270ed build to
5.7e-12 / 3.2e-11 / 2.5e-9 (nz 16/32/64). The difference falls 3.55x and 3.48x per doubling of nz, so in eps_eff it scales as nz^-3.8 (about dz^4), against the
term's own dz^2 effect (off - on = -0.245 nz^-2): agreement at the next order, as expected.

2b. One-step row split (cmp_lev.py; the reference is 807cfd8 on = e7f9904 on in Cartesian). 0b6b6ef on minus
807cfd8 on, % of sigma:

| nz | face Etot | cell Etot | dens (face / cell) | residual rel L2 (face / cell) |
|---|---|---|---|---|
| 64 | -3.15e-5 | -3.17e-5 | +1.1e-7 / -4.2e-8 | 4.8e-7 / 6.3e-7 |
| 128 | -1.83e-6 | -2.07e-6 | +2.2e-8 / +4.0e-8 | 8.7e-8 / 1.3e-7 |

Etot difference order: nz^-4.1 (face), nz^-3.9 (cell), against the term's own Etot shift of 3.47 % (nz64) and
0.87 % (nz128), which is dz^2. Seed and dt are equal to round-off, and the off arms agree with 807cfd8 off to 6e-12
to 7e-10 (noise floor).

2c. Onset at the 3 T1L points (10/10 RUN_EXIT 0; fit_pr.py; the output's "study" column is 807cfd8 here).
Growth-rate rel_err with the term on:

| run | 0b6b6ef | 807cfd8 (= e7f9904 on) | 0b6b6ef - 807cfd8 | study window spread | term's shift (off -> on) |
|---|---|---|---|---|---|
| e1e-3 nz32 cell | -1.1840e-2 | -1.1834e-2 | -5.11e-6 | 2.6e-4 | +0.148 |
| e1e-3 nz32 face | -2.2203e-3 | -2.2153e-3 | -5.05e-6 | 1.6e-4 | +0.147 |
| e1e-3 nz64 cell | -1.2825e-3 | -1.2822e-3 | -3.13e-7 | 6.0e-5 | +0.035 |
| e1e-3 nz64 face | +7.4725e-5 | +7.5029e-5 | -3.03e-7 | 1.1e-5 | +0.035 |
| e2.56e-4 nz64 cell | -5.1055e-3 | -5.1044e-3 | -1.05e-6 | 2.8e-4 | +0.144 |
| e2.56e-4 nz64 face | +3.3598e-4 | +3.3715e-4 | -1.17e-6 | 6.8e-5 | +0.143 |

All fit windows complete, mass drift <= 7.1e-12. The difference is the same for face and cell, falls 16.3x from nz32
to nz64 (dz^4), is 3e-5 / 9e-6 / 8e-6 of the term's own shift, and is 31x to 270x below the fit's window spread.

Summary for 0b6b6ef: every gate passes. Switch off = 117e449 bitwise in Cartesian and = 10270ed bitwise on the
cubed sphere. Switch on differs from the covariance-only form (e7f9904) at the next order only: dz^4 in eps_eff, in
the Etot row and in the onset growth rate.

Independent review (read-only, on the run artifacts; HEAD 0b6b6ef6f1a0, RESULT sha256 39855b7): VERDICT supported.
It checked the parent chain (0b6b6ef -> 75b0e90 -> 10270ed) and confirmed from the run logs that every arm ran the
stated iso and switch. It re-ran the cmp on both Cartesian decks and on the cubed-sphere final_w, diffed the ctest
sets (Skipped and Not Run handling the same in every build), and recomputed the nz orders (eps_eff nz^-3.83 / -3.80,
Etot nz^-4.11 / -3.94, onset 16.3x / 16.7x) and the spread ratios (31x to 267x). Its wording corrections are applied
above. One open point, on the tool, not the head: the -Wall matcher compares warnings after `sort -u`, so a new copy
of an existing warning would be labelled OLD. Counted by hand, nothing is hidden here (one of each hydro_forward.cpp
message, and the coordinate.hpp ones are the 117e449 set shifted by 51 comment lines). For future heads, compare
`uniq -c` counts. The rows test's Cartesian tolerance (2e-3) is loose: it separates 75b0e90 (-0.62) from the fix,
and 10270ed only through offset invariance.

### 11e. Final #289 head 6719873 (10-09)
6719873 = 0b6b6ef's code rebased onto main d59836d (= 117e449 + #288, curved-grid metrics for the implicit face
gravity work). d59836d is an ancestor of 6719873, and `git diff -- src tests` 117e449->0b6b6ef and d59836d->6719873
carry the same +/- lines (md5 of the sorted lines 7e1125fbea83705d17d59c88359490ec in both). Control = d59836d,
built the same way. Builds d59836d and 6719873, both BUILD-GOOD.

| gate | result |
|---|---|
| compile warnings, touched src (coordinate, gnomonic_equiangle, spherical_polar, hydro, hydro_forward) | default flags: none (65 objects rebuilt); -Wall -Wextra: 82, all also at d59836d with the same copy counts (`uniq -c` matcher), 0 new copies |
| 1. ctest -j1 | 6719873: 181 pass = d59836d's 178 + test_cubed_sphere_cell_volume_python + test_flux_covariance_rows_python + test_horizontal_flux_covariance_python; the same 181 as 0b6b6ef. Fail set identical to d59836d's, which is identical to 117e449's (26 lines: 13 snapy env-bound + 13 Eigen). Footer 846 failed of 1028 (1025 at d59836d) |
| 2. three new tests | 6719873 GREEN: rows (Cartesian -0.004937 / +0.000250 at nz 32/64), hfc (on -0.01302 / -0.00494, off -0.25776 / -0.25134), cell volume (div(r rhat) - 3 = 3.1e-14). d59836d RED on all three (switch absent; six-panel volume off by 3.3e-3) |
| 2. eps_eff nz^2 (eps_cart.py) | on -0.013020090976743195 / -0.004937248921938693 / +0.0002498201101545082, off -0.25775710629804033 / -0.25133584623873123 / -0.2465371812775321 (nz 16/32/64): equal to 0b6b6ef's to the last printed digit |
| 3. Cartesian, switch off vs d59836d (2 decks) | IDENTICAL, IDENTICAL; and d59836d off = 117e449 off, IDENTICAL on both |
| 4. Cartesian, switch on vs 0b6b6ef on | IDENTICAL on both decks and on the two e1e-3 nz32 onset runs (cell, face) |
| 5. cubed-sphere rest, explicit, gravity-work cell (the 11d deck) | head off = 0b6b6ef off, head on = 0b6b6ef on, d59836d = 117e449: byte-identical (final_w and history). On vs off as in 11d (u1 history rel <= 5.4e-7, final <= 3e-13). PASS |

Why #288 changes nothing above: every deck in gates 3 to 5 runs explicit (implicit-scheme 0), and the cubed-sphere
deck uses gravity-work cell (the default). #288 changes only the implicit face gravity work on curved grids. So the
cubed-sphere rest deck with gravity-work face was added, explicit (scheme 0) and implicit (schemes 9 vic-full and 1
vic-partial), for 117e449 off, d59836d off, 0b6b6ef off/on, 6719873 off/on (cs_rest.py --implicit k --gw face;
18/18 RUN_EXIT 0). The gravity-work-cell implicit arms were compared as well.

| path | #288 delta (d59836d - 117e449) | head - 0b6b6ef, off and on | (head - 0b6b6ef) - #288 delta | #289 delta (on - off) at head vs at 0b6b6ef |
|---|---|---|---|---|
| explicit, face | 0 (byte-identical) | 0 (byte-identical) | 0 | byte-identical |
| implicit 9, face | rho 2.3e-11, u1 1.7e-9, p 0.66 (of 95); u1 history rel 4.3e-2 | the same | <= 1.2e-12 (round-off) | differ by <= 9.6e-13 |
| implicit 1, face | the same as scheme 9 | the same | <= 1.2e-12 | <= 9.6e-13 |
| implicit 9 / 1, cell | 0 (byte-identical) | 0 (byte-identical) | 0 | - |

So the switch-on difference between 6719873 and 0b6b6ef appears only on the implicit face path on the cubed sphere,
and there it is #288's own change, carried unchanged: the two PRs add, with a cross term at round-off. All rest
states stay at rest: max|u1| peak 7.67e-8 (step 3) -> 1.63e-10 (step 300) implicit face with #288 (d59836d, 6719873;
7.48e-8 -> 1.69e-10 without it: 117e449, 0b6b6ef), 3.12e-7 -> 4.9e-9 (face) / 5.0e-9 (cell) explicit, in every arm; switch on vs off: u1 history rel <= 1.2e-5 at 6719873, <= 2.0e-5 at 0b6b6ef (implicit face).

Summary for 6719873: every gate passes. Switch off = d59836d bitwise in Cartesian. On the cubed sphere switch off is
not d59836d bitwise (u1 history rel 1.6e-5 to 2.2e-5, p up to 7.7e-6 of 95), as for 0b6b6ef and 10270ed against
117e449 (11c, 11d), attributed to the PR's switch-independent gnomonic cell-volume fix (the head's hydro code is
bitwise main in Cartesian with the switch off; no hydro-only build isolates it); switch off = 0b6b6ef off bitwise there,
except on the implicit face path (#288). Switch on = 0b6b6ef bitwise except on the implicit face cubed sphere, where
the difference is #288's own change to <= 1.2e-12.

Independent review (read-only; RESULT sha256 9e399a8): first VERDICT refuted, on the summary
sentence only: it read "switch off = d59836d bitwise ... on the cell-work cubed sphere", which the cubed-sphere
comparison outputs contradict (byte-identical False vs d59836d, from the cell-volume fix). It confirmed everything
else: bitwise_out.txt 9/9 IDENTICAL, the diff md5 at both bases, ctest sets (178 = 117e449's at d59836d, 181 = 0b6b6ef's
at the head, all four fail lists the same 26 lines), the face additivity residual <= 1.2e-12 and the change in the #289
delta <= 9.6e-13, and #288's hydro.cpp change (face_work_in_operator() no longer Cartesian-only). Summary and the
peak-u1 line ("every arm") corrected as above. Re-check: VERDICT supported (all 30 csimp/csface arms
ran the stated build, switch, scheme and gw; the cubed-sphere switch-off cause is attributed, not isolated, worded so).

### 11f. Review-fix head 668a647 (10-09)
668a647 = 6719873 + one commit: the p* shift of the lateral geometric pressure source in hydro_forward.cpp is
gated per direction (the x2 source takes p* when the x2 faces are corrected, x3 likewise; before, any uncorrected
resolved direction dropped the shift for both), a CR byte out of coordinate.hpp, clang-format of coordinate.cpp, two
tests (tests/test_radial_face_moments.cpp, tests/test_flux_covariance_seams.py). Touched vs 6719873: src/coord/
coordinate.{cpp,hpp}, src/hydro/hydro_forward.cpp, tests/. Reading the diff: with the switch off the new branch calls
the same pcoord->forward(w, ...) as before, and with every resolved direction corrected it computes the same div as
before, so bitwise equality is expected everywhere except a resolved direction with its faces uncorrected.
Same recipe; build BUILD-GOOD (2.11.4.dev11+g668a647).

| gate | result |
|---|---|
| 1. ctest -j1 | 183 pass = 6719873's 181 + test_flux_covariance_seams_python + test_radial_face_moments.release (the three #289 tests among them); fail set identical to 6719873's (26 lines: 13 snapy env-bound + 13 Eigen); footer 846 failed of 1030 |
| 1. the two new tests + the three #289 tests (run from the commit's copies) | 668a647 GREEN: rows, hfc, cell volume as at 6719873 (eps_eff nz^2 on/off equal to 6719873's to the last digit); seams GREEN: six-panel conservation with the term on, mass / vapor / E+PE drift 4.3e-14 / 6.1e-15 / 3.5e-14 over 10 steps; x3-disabled spherical rest max\|v\|/c_s off 4.120e-11, on 4.120e-11. The seams test at 6719873 is RED on the gating arm only: on 5.544e-06 (conservation the same) |
| 2. switch off vs 6719873 | Cartesian 2 decks IDENTICAL (and = d59836d); cubed-sphere rest explicit cell, implicit 9/1 cell, face explicit/9/1: byte-identical (final_w and history); spherical-polar rest with and without x3 flux: byte-identical |
| 3. switch on vs 6719873 | Cartesian 2 decks + the two e1e-3 nz32 onset runs IDENTICAL; cubed-sphere rest explicit and implicit (9, 1), cell and face work: byte-identical; spherical-polar rest with x3 flux on: byte-identical |
| 4. the new case: spherical-polar rest, x3 flux disabled, nx3 > 1, switch on | seams test: 5.544e-6 (6719873) -> 4.120e-11 (668a647) = switch off. Independent deck (sp_rest.py: cs_rest's isentropic column on a spherical-polar sector, x1 [1000, 1300], colatitude [0.3, 0.7] pi, x3 [0, 0.4] pi, 32 x 8 x 8, 100 steps, not discretely balanced): max\|u2\|/c_s 6.985e-6 (6719873) -> 1.133e-15 (668a647), against 8.6e-16 off and 1.1e-15 with x3 flux on; max\|u1\|/c_s 5.3e-8 in every arm (the analytic column's own imbalance) |
| warnings, touched src (coordinate.cpp, hydro_forward.cpp; -Wall vs 6719873's copies) | -Wall -Wextra: 32, 0 new copies; default flags (coordinate.cpp/.hpp, hydro_forward.cpp): none |

Summary for 668a647: every gate passes. Switch off = 6719873 bitwise on every deck (Cartesian, cubed sphere explicit
and implicit with cell and face work, spherical-polar with and without x3 flux). Switch on = 6719873 bitwise on all
of them except the x3-disabled spherical rest, the case the commit fixes: max|v|/c_s 5.5e-6 -> 4.1e-11 in the seams
test (= switch off, 4.120e-11) and max|u2|/c_s 7.0e-6 -> 1.1e-15 in the independent deck (roundoff: switch off 8.6e-16,
x3-flux-on switch-on 1.1e-15). Test exit codes (hfc prints no pass banner; it exits nonzero on failure):
rc=0 for all five at 668a647, rc=1 for seams at 6719873.

Independent review (read-only): VERDICT supported, checked against RESULT sha256 d172e092e612, the
comparison outputs and the run logs. It confirmed every row against the primary files
(pass diff = exactly the two new tests, fail diff empty; 8/8 Cartesian and 15/16 rest pairs IDENTICAL, the 16th the
fixed sp x3off_on arm; isos, switch values and deck options right in every maxu.json and log). It corrected the
summary's "both equal to switch off" (true for the seams test only; applied above).

## 11g. Rebased #293 head on e51bdc2 (10-09)

#292 merged into main as e51bdc2 (= d59836d + "reject failed VIC solves and test spherical columns"; it touches the
implicit solver: src/implicit/*, math/ludcmp.h, mesh/meshblock.cpp). #293 is rebased onto it.
8cea3ae (the pre-rebase #293 head) = 668a647 + a comment rewrap in coordinate.cpp (lines 475-477)
+ docs + a seams-test edit (git diff 668a647 8cea3ae --stat), so the 668a647 runs of 11f stand in for 8cea3ae's
code.

| Step | Result |
|---|---|
| control build e51bdc2 | BUILD-GOOD, snapy 2.11.5.dev0+ge51bdc2 |
| control ctest -j1 | 179 pass = d59836d's 178 + test_lu_failure.release (#292's new test; its tall-column python test passes, as at d59836d); fail set identical to d59836d's (26 lines, LC_ALL=C sorted diff empty); footer 846 failed of 1026 |
| control runs (10 switch-off arms: Cartesian x2, cubed sphere explicit, implicit 9/1 x cell/face, explicit face, spherical x3 on/off) | 10/10 RUN_EXIT=0 |
| head = local rebase | Scratch worktree, `git rebase e51bdc2` of 8cea3ae (detached, merge-base d59836d, 13 commits): clean, range-diff 13/13 `=`, HEAD b886adf84516, tree 0183dd105ae4bd37814da9238f88058bf7870817 = the expected tree. Results below carry over to the pushed head by tree hash |
| head build | BUILD-GOOD, snapy 2.11.5.dev13+gb886adf |
| head ctest -j1 | 184 pass = e51bdc2's 179 + the PR's 5 (cubed_sphere_cell_volume_python, flux_covariance_rows_python, flux_covariance_seams_python, horizontal_flux_covariance_python, radial_face_moments.release) = 668a647's 183 + test_lu_failure.release; fail set identical to e51bdc2's (26 lines, diff empty); footer 846 failed of 1031 |
| head tests | rows, hfc, cellvol, seams (the head's edited copy: it now also asserts that on and off differ, final state 9.5e-12, x2 momentum flux 9.1e-5 relative), #292's tall column: 7/7 arms rc=0. Seams x3-disabled rest: off 4.120e-11, on 4.120e-11 = 11f. eps on/off JSON = 668a647's in every field but the snapy path |
| switch off vs e51bdc2 | Cartesian 2/2 IDENTICAL; spherical x3 on/off 2/2 IDENTICAL; cubed sphere 6/6 DIFFER, by exactly the PR's switch-independent delta (cell-volume fix; same as the cubed-sphere switch-off difference vs d59836d in 11e): (head - e51bdc2) - (668a647 - d59836d) = 0 in every byte-compared array, delta 7.7e-13 (implicit cell) to 7.7e-6 (implicit face, |w| max 95) |
| #292 on these decks | e51bdc2 = d59836d bitwise on all 6 cubed-sphere rest arms (explicit, implicit 9/1, cell/face) and on both Cartesian decks (they equal the 668a647-section Cartesian comparison, itself = d59836d) |
| switch on, Cartesian vs 8cea3ae (= 668a647's code) | bwon x2 and fix x2: 4/4 IDENTICAL to 668a647 |
| implicit (VIC) arms at rest, schemes 9 and 1, cell and face, off and on | all 8 byte-identical to 668a647 (same switch); max\|u1\|/c_s 6.581e-8 (cell) and 7.665e-8 (face) at e51bdc2, head off and head on alike; horizontal 2-2.6e-13 |
| x3-disabled spherical rest (sp_rest.py) | head = 668a647 byte-identical, off and on; max\|u2\|/c_s off 8.613e-16, on 1.133e-15 (= x3-flux-on, switch-on arm); e51bdc2 off 8.613e-16 |
| -Wall -Wextra on the 4 .cpp the PR touches vs e51bdc2 | 82 warnings (more files touched relative to e51bdc2 than in 11f), 0 new copies |
| default-flag warnings | none (NO_WARNINGS) on the 9 src files the PR touches vs e51bdc2  |

Summary for 11g (tree 0183dd105ae4): every gate passes, and #292 does not interact with the PR. On these decks #292
changes nothing: e51bdc2 = d59836d bitwise on all six cubed-sphere rest arms (explicit, implicit schemes 9 and 1, cell
and face work) and on both Cartesian decks. The rebased head equals 668a647 byte for byte on every arm, switch off and
on: Cartesian, cubed sphere, spherical with and without x3 flux. With the switch off, the head equals e51bdc2 bitwise
on Cartesian and spherical. On the cubed sphere it differs from e51bdc2 by exactly 668a647 - d59836d (residual 0), the
switch-independent cell-volume fix. ctest: 184 = 179 + the PR's 5, fail set unchanged. The x3-disabled spherical rest
stays fixed: seams 4.120e-11 on = off; sp_rest max|u2|/c_s 1.133e-15 on, 8.613e-16 off.

Independent review (read-only): VERDICT supported. It checked RESULT sha256 70fd53c8bd6a, the comparison
script and its output, every maxu.json (iso and switch per arm) and the ctest lists: the four fail files are identical
after LC_ALL=C sort; the pass diffs are exactly the PR's 5 tests and test_lu_failure. Its three caveats, settled:
(1) It could not reach the build host. Re-run on a local clone: tree 0183dd105ae4bd37814da9238f88058bf7870817, HEAD b886adf84516;
`git range-diff d59836d..8cea3ae e51bdc2..HEAD` gives 13 lines, all `=`; `git diff --stat 668a647 8cea3ae` touches
the two derivation docs, coordinate.cpp (comment only, lines 475-477) and the seams test.
(2) The ctest footers imply one more pass than the lists (1031 - 846 = 185 vs 184; 1026 - 846 = 180 vs 179). The
difference is one Skipped test, test_python_import_path_python, which ctest does not count as failed (tally of
build's ctest_out.txt: 184 Passed, 1 Skipped, 26 Failed, 820 Not Run).
(3) Wording. The "residual 0" in cmp8 section 3 is not an independent check: it follows from head = 668a647 and
e51bdc2 = d59836d byte for byte. At rest, the x3-disabled spherical arms equal the x3-on arms, so in 11g the case
discriminates only through 11f, where 6719873 gave max|u2|/c_s 6.985e-6 and the seams test 5.544e-6. The head
inherits the fix by being byte-identical to 668a647 on those arms.

## 12. Next PR: #293 head 0af1402 + W + G + D (10-09)
Switches: cov = SNAP_FLUX_COVARIANCE, W = SNAP_WB_REF4, D = SNAP_GRAVITY_WORK_RADIAL_EXACT (explicit + VIC),
G = SNAP_X1_CENTROID_EXACT (spherical-polar). Control = 0af1402: its tree is 0183dd105ae4 (checked on the build host),
the tree built as b886adf in 11g, so the b886adf build and its ctest sets are the control.
Gate recipe: worktree, ancestor check, build, then ctest -j1, five run packs, the head's added/changed python tests on
head and control, -Wall and default-flag warnings. Decks: cart_cw.py = section 4's safety decks with E+P beside E+PE,
E+P = the corrected PE the D switch conserves; cs_rest.py, sp_rest.py (+ --implicit), sp_epe.py = leg G's seeded
spherical column with E+P; compared with cmp9.py.
Control runs (T1L + Cartesian, cubed-sphere/spherical; off and cov, 49 runs): all RUN_EXIT=0.
- Reproducible and the copied decks unchanged: control vs 11g's runs of the same build, byte-identical on the 6 pairs
  checked (T1L e1e-3 n32 face off and cov, e2e-2 n16 cell off; cs s9 face off, cs s1 cell cov, sp x3-off cell off).
  The Cartesian decks give section 4's numbers to the digit: E+PE per step 3.5e-16, drift -5.7e-14, max|w| 1.2302e-4
  (cov) / 1.2247e-4 (off); rest max|u1| 2.83e-15 (cell) / 1.95e-15 (face).
- Onset rel_err (fit_t1l.one, complete, mass drift <= 3.5e-12): nz32 off -0.1493, cov -2.220e-3; nz64 off -0.0349,
  cov +7.47e-5.
- E+P (the D switch's corrected PE) is NOT conserved at the control, as expected without D: per step 3.4e-13 Cartesian,
  6e-11 (R0 5) / 5e-14 (R0 1000) spherical, against E+PE 2-4e-16. So the E+P column discriminates.
- Rest at the control: cs explicit 3.12e-7, VIC 6.581e-8 (cell) / 7.665e-8 (face), as in 11g; sp explicit 5.33e-8,
  VIC 6.7e-9; on (cov) = off. 'all' arms at the control (unknown switches) equal cov.
- Head-test runner dry run (0183dd1's four added tests on the b886adf build): 8/8 rc=0.

### 12 results: local head 9ec88bb20ec9, tree a7fa0a714144 (= d1f30d8; 10-09)
The head was assembled locally: aea71ed (#293 merged; tree
0183dd105ae4 = the control's) + W = exactly 8cea3ae..b3a19d7 (1454878 336101b fdf895b 5517876 022d8c4 b3a19d7) + G 1cf0bbc
+ D aea71ed..5536c0a (d9f7050 a7cc53b 74fafbb 5536c0a). One conflict (a7cc53b, hydro.cpp/hpp: W's and D's adjacent
declaration blocks): both kept, W first, nothing else changed. Tree a7fa0a714144d281cc886b95b1d76c41b5d7d210 = the
required a7fa0a71, so the results carry over to the pushed sha d1f30d8.

| Gate | Result |
|---|---|
| build | BUILD-GOOD, snapy 2.11.6.dev11+g9ec88bb |
| ctest -j1 | 189 pass = control's 184 + 5 new (test_balance_column_wb_ref4.release, test_face_floor_wb_ref4.release, test_wb_ref4_order_python, test_x1_centroid_rest_python, test_gravity_work_radial_exact_python); fail set identical to the control's (26 lines, LC_ALL=C sorted diff empty; the extraction reproduces the b886adf ctest lists exactly from b886adf's ctest_out.txt); footer 846 failed of 1036. test_restart_cycle_limit (b3a19d7 edits its runner) still fails as at the control: its 2-rank torchrun straka run exits 1, like the other multi-rank tests in the fail set |
| new python tests, head vs control iso | test_x1_centroid_rest, test_wb_ref4_order, test_gravity_work_radial_exact: head rc=0, control rc=1, each on its switch assertion (centroid: interior/wall 6.5e-10 >= 1e-10 with the switch on; WB4: order 2.32 / 1.93 < 2.75; gravity work: one-stage dE(on-off) - g1 sigma^2 s[drho] = 3.3e-5 vs 2.5e-14 at head). run_restart_cycle_limit.py is a ctest helper (needs --build-dir), rc=2 both: covered by ctest |
| -Wall -Wextra, 7 touched .cpp vs control | 69 warnings; the 6 "new copies" are the control's own layout.hpp unused-parameter warnings (iloc, offset, rank), counted in the two files the head adds (x1_centroid.cpp, wb_ref4.cpp: no base copy) and OLD in every other file: 0 warnings in code the head writes |
| default-flag warnings, 12 touched src | NO_WARNINGS |
| runs | 132/132 RUN_EXIT=0 each checked to have run on the head build (pack log + the run's snapy path) |
| switch off and cov alone, head vs 0af1402 | 47/47 byte-IDENTICAL (final state + per-step history): T1L x5, Cartesian x6, cubed sphere x12, spherical rest x16, spherical energy column x8 |

Switch on:
- Where a switch is a no-op, it is bitwise: D (acts with gravity-work: face on Cartesian / spherical-polar) = off on every
  cell-work deck and on all 6 cubed-sphere decks; G = off on all 6 cubed-sphere decks. 'all' = covWD on T1L (G is
  spherical-only): same rel_err to every digit.
- Closed walls, max per-step relative change (drift over the run):

| deck | off / cov | W | D | covWD (Cart) / all (sph) | G |
|---|---|---|---|---|---|
| Cart E+PE | 3.5e-16 | 3.5e-16 | 3.4e-13 | 2.4e-15 | - |
| Cart E+P | 3.4e-13 | 2.6e-15 | **3.5e-16** | **3.5e-16** | - |
| sph R0=5 face E+PE | 2.4e-16 | - | 6.2e-11 | 4.0e-14 | 2.4e-16 |
| sph R0=5 face E+P | 6.2e-11 | - | **2.4e-16** | **2.4e-16** | 4.0e-14 |
| sph R0=5 VIC face E+P | 1.0e-10 | - | **2.4e-16** | **2.4e-16** | 4.7e-14 |
| sph R0=1000 face E+P | 4.9e-14 | - | **2.6e-16** | **2.6e-16** | 4.7e-14 |

  D trades the conserved quantity from E+PE to E+P, to round-off, Cartesian and spherical, explicit and VIC, alone and
  with every other switch on. Mass drift <= 5.9e-15 in every arm.
- T1L onset rel_err (eps 1e-3, face work; complete fits, mass drift <= 3.5e-12):

| | off | cov | cov+W | cov+W+D | all |
|---|---|---|---|---|---|
| nz32 | -0.1493 | -2.220e-3 | +1.181e-2 | +3.816e-3 | +3.816e-3 |
| nz64 | -0.0349 | +7.47e-5 | +1.975e-3 | +9.65e-4 | +9.65e-4 |

  W moves the onset error positive and makes it larger than with cov alone (x5 at nz32, x26 at nz64); D cuts W's error to a
  third (nz32) and a half (nz64) and converges at second order (3.816e-3 -> 9.65e-4, ratio 3.95); cov alone converges faster here (ratio 30).
- Cartesian rest (1000 steps): max|u1| 1.9-2.8e-15 in every arm (off 2.83e-15 cell / 1.95e-15 face; W 2.44e-15 / 2.22e-15;
  D = off / 2.50e-15; all 2.44e-15 / 2.28e-15): round-off.
- Cubed-sphere rest, max|u1|/c_s: W changes the 4th digit only (explicit 3.124e-7 both; VIC 6.579e-8 vs 6.581e-8 cell,
  7.663e-8 vs 7.665e-8 face); D and G bitwise = off; horizontal 2-3e-13 in every arm.
- Spherical rest, max|u1|/c_s: G halves the explicit residual (5.33e-8 -> 2.44e-8, cell and face, x3 on and off) and
  lowers VIC (cell 6.71e-9 -> 5.57e-9, face 6.61e-9 -> 6.40e-9); W and D change it at the 3rd-4th digit (explicit
  5.33e-8, VIC face D 6.52e-9); all: explicit 2.44-2.46e-8, VIC cell 5.57e-9, VIC face 7.06e-9 (7% above off, the one arm
  above off; same order). Horizontal <= 1.5e-14 everywhere.
