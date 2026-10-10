> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Leg K — diffusion face coefficient as the mean of products (snapy, next PR)
Base: chengcli/snapy main aea71ed (= #293 merged; tree 0183dd1 = 0af1402's tree, checked).
Commits: d806e86 tests + derivation (RED on base code), 4d3b4d7 fix.

## Where the defect is (read at 0af1402)
- src/forcing/diffusion.cpp:173-193 `face_scaled_coefficient(value, scale, ...)`: interior face =
  face_average(value) * scale_at_faces(scale) = mean(value) * mean(scale) on x1 faces. Wall faces already
  extrapolate the PRODUCT (exact for a linear product). Two callers, both in DiffusionImpl::forward:
  viscosity (value = rho, scale = nu_scale_x1) and conduction (value = rho*cv, scale = kappa_scale_x1).
- x2/x3 faces: scale_at_faces returns the cell's own x1 value (the profile does not vary along x2/x3), so the
  product of means equals the mean of products there algebraically; only x1 carries the defect.
- face_coefficient (no profile): mean(rho) or mean(rho*cv) is already a mean of products (constant nu/kappa
  times the cell value). Unchanged.
- Reached only when nu_scale_x1 or kappa_scale_x1 is set. In snapy's repo: tests only. A downstream convection
  benchmark installs scale = 1/rho0(z) on both. That is the
  constant-dynamic-coefficient case the defect is about: at rest rho = rho0, the new face coefficient is 1
  exactly; the old one is mean(1/rho0)*mean(rho0) = 1 + (drho)^2/(4 rho_a rho_b).

## Switch decision: UNCONDITIONAL (no switch)
- Cases without nu_scale_x1/kappa_scale_x1 never call face_scaled_coefficient: unchanged by construction (checked
  bitwise below). A profile of ones stays bitwise equal to no profile (q*1 = q).
- The only cases that change are the profile cases, and in them the old form is the defect: a 1/rho0 scale
  is exactly the constant-dynamic-coefficient case. A switch would only keep
  a known-wrong default. Results measured with the old form on such profile cases
  will move at O(dz^2) inside, O(dz) in the wall cells.

## Correction to the expected order
- Product of means on a uniform product: interior tendency O(dz^2), but the WALL cells O(dz), because the wall face
  is extrapolated (exact) and the next face carries the excess e = (dq)^2/(4 q_a q_b). Replica (python, numpy):
  constant C, rho = (1.25-x)^1.5, T linear: max|tend| 18.3/11.2/6.24/3.31 (nx 16..128, order -> 0.92, wall cell),
  interior 5.6/2.1/0.67/0.19 (order -> 1.81); mean of products <= 1e-12. Smooth s, T: both forms order 1.91-1.98.
  Script: docs/derivations/diffusion_face_coefficient.py (at 4d3b4d7).

## Deliverables (at 4d3b4d7)
- tests/test_diffusion_x1_scale.cpp: constant_dynamic_coefficient_column_has_no_tendency (RED/GREEN; conduction
  and shear, nx1 16 and 64, tol 1e-12 |F|/dx) and smooth_profile_flux_converges_at_second_order (order > 1.85, nx1
  32/64/128, GREEN on both forms).
- docs/derivations/diffusion-face-coefficient.md (+ the .py replica).
- Gates: ctest -j1 base aea71ed vs fix 4d3b4d7 (fail sets), RED run of the new tests on base code, deck
  arms (test_diffusion.yaml one step: none / ones / 1/rho) base vs fix.

## Results
- RED (new tests on aea71ed code): constant_dynamic FAILED: heat 3272 / 1117 and shear 0.183 / 0.0624
  at nx1 16 / 64 (tolerance 1e-12 scale; shear order 0.78, the wall-cell O(dz)); smooth_profile OK. GREEN (4d3b4d7):
  both PASS.
- fail->pass: `parent d806e868: FAIL (exit 1) | 1 FAILED TEST` / `head 4d3b4d7d: PASS (exit 0) | [ PASSED ] 2 tests.`
  / `VERDICT: FAIL->PASS`.
- ctest -j1 (base aea71ed, fix 4d3b4d7): 184 passed, 846 failed out of 1031 on both; fail sets IDENTICAL
  (26 Failed = 13 Eigen blas/resize + 13 snapy env-bound mpi/ucx/gloo/straka/restart; 820 Not Run = Eigen tests
  not in ALL + test_eos, which does not compile on the test machine: glibc `major` macro). test_diffusion*, x1_scale (C++ + python) pass.
- Deck arms (test_diffusion.yaml one step, base build vs fix build): none IDENTICAL, ones IDENTICAL, inv_rho
  DIFFER (max 2.7e-3 of |u| 2.5e5); ones == none bitwise in both builds.
- Decks reaching the function: snapy: none outside tests/test_diffusion_x1_scale.{cpp,py} (git grep).
  A downstream check that asserts the OLD form's residual ratio 2 delta^2/rho0^3 must be re-stated (residual -> 0)
  with the fix, since the profile arm's residual is then round-off.
- Independent check on the defect claim: supported (source lines + awk recompute of the replica); its open item (C++
  RED/GREEN) is closed by fail->pass above.
- Harness note: on the compute nodes the default git cannot read worktrees; the base-mode `git checkout` of the
  gate script failed silently (0 tests ran), hence the separate RED run with the test file staged by hand.
