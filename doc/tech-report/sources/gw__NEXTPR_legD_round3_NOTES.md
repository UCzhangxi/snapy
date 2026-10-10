> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Leg D: option b (what face+H was cancelling), 2026-10-09

**Verdict: criterion MET.** cov+F+W4 beats cov+W4 and converges at second order in eps nz^2. Recommendation: the next PR
ships F and W4 together, and the Cartesian #289 oracle is quoted with both on. Note that +0.0068 of that number is the deck's
point-value IC (oracle below), not the scheme; or quote it on an average-IC deck variant.
Evidence: cmp_w4.out, wall_budget_dump.out, the w4 eps-budget json outputs.

## 0. Replica faithfulness (the check behind step 1)
wall_budget.py books every term of the wall-cell energy budget separately. It is checked per cell against the C++ eps
diagnostic (per-level dt->0 Richardson extrapolation with dt factors 1, 1/2, 1/4).
- With snapy's actual reconstruction (weno5 shock:false = WENO5-JS on every variable, including the WB density
  perturbation with even wall ghosts), max|cell diff| is 1.9e-5/2.6e-6/1.2e-6 at nz 16/32/64 on the head build (4 arms).
  On the merged build it is <= 8.3e-5 (nz 16) and <= 1.2e-6 (nz 64) on all 8 arms.
- With linear UP5 it was 3.8e-2/2.2e-2/1.2e-2: the WENO weights set the code reference's near-wall face density.
This was failing, then passing; cmp_head.out vs cmp_head_weno.out.

## 1. Wall-cell budget (eps deck, code reference, C++ initial state; nz 16/32/64)
Two terms are O(h) at the wall cells:
- **H (curvature flux, face+H):**
  - cell 0: +9.8e-3/4.9e-3/2.5e-3
  - cell n-1: +2.2e-2/1.1e-2/5.7e-3
- **WBr (density part of the code's WB reference: one-sided pref rows, clamped binomial rs, dref = pref*rs):**
  - cell 0: +2.7e-3/1.5e-3/7.8e-4
  - cell n-1: +8.9e-3/4.1e-3/2.0e-3
  - its interior sum is also O(h): -7.6e-2/-3.9e-2/-1.8e-2

All other wall-cell terms are O(h^2) or better: x1 flux divergence p 1.7-2.1, x2 p 3, WB pressure part p 2, face work p 2,
F's work p 2.4-3, #289 covariance p 1.6-2.1.

**What face+H was cancelling:** H's positive wall error offset the code reference's negative O(h) density error. F removes H's
error and so exposed WBr. W4 makes WBr O(h^2) at the walls: -3.4e-4/-8.4e-5/-2.1e-5.

## 2. C++ 4-way on the local merge of c2624e3 and fdf895b
- Merge commit: e65db14 (local, never pushed).
- eps_eff nz^2, dt->0:

| arm | nz 16 | nz 32 | nz 64 | wall cell 0 | wall cell n-1 |
|---|---|---|---|---|---|
| cov | -0.01300 | -0.00493 | +0.00025 | +1.33e-2/6.6e-3/3.3e-3 | +2.87e-2/1.48e-2/7.5e-3 |
| cov+W4 | +0.03738 | +0.02266 | +0.01486 (O(h)) | +1.03e-2/5.0e-3/2.5e-3 | +2.08e-2/1.09e-2/5.6e-3 |
| cov+F | -0.04448 | -0.02097 | -0.00784 | +3.4e-3/1.7e-3/8.3e-4 | +6.5e-3/3.5e-3/1.8e-3 |
| **cov+F+W4** | **+0.00589** | **+0.00662** | **+0.00676** | +3.0e-4/8.6e-5/2.3e-5 (p 1.9) | -1.44e-3/-3.4e-4/-8.1e-5 (p 2.0) |

- cov+W4's wall cells are H's wall error, now unbalanced.
- Arms without cov: off -0.2577/-0.2513/-0.2465; W4 -0.2074/-0.2237/-0.2319; F -0.2892/-0.2674/-0.2546; F+W4 -0.2388/-0.2398/-0.2400.

**Point-value IC oracle.** The deck's cell values are point values; read as cell averages, they carry an O(h^2) entropy
gradient. Prediction from the dump (4th-order deconvolution, -w ds/dz projected): +0.00634/+0.00668/+0.00678.
- cov+F+W4 minus the prediction: -4.5e-4/-6e-5/-1.6e-5 (C++).
- With exact cell-average inputs (replica, wall_budget_avg.out), cov+F+W4 is -8.5e-4/-1.85e-4/-4.3e-5/-1.0e-5 at nz 16..128 (p 2.1).

So the residual after the IC term is 1e-5 for cov+F+W4, against ~0.008 for cov+W4 at nz 64.

## 3. Further checks
- **Bitwise, switch off, head c2624e3 vs control 8cea3ae:** e1e-3_n32_face and e2e-2_n16_cell are IDENTICAL (.nc + diag.txt).
- **ctest:** the same 26 Failed + 820 Not Run on both arms. Head has +1 test,
  test_gravity_work_radial_exact_python, and it PASSES.
- **Correction to an earlier reading:** the ~820 Not Run are Eigen's own vendored test suite (packetmath, product_*, qr, ...),
  which `make` never builds. They are not the test_eos.cpp `major` macro.
- **Shim reruns** (uncommitted #undef major/minor in test_eos.cpp, reverted after): head / ctl give 26 Failed (13 Eigen/BLAS + 13 snapy MPI/parallel, test_straka,
  test_restart_cycle_limit) and 819 Not Run on both, an IDENTICAL per-test list except that head adds
  test_gravity_work_radial_exact_python (PASS). test_eos.release PASSES on both.
- **T1L onset rel_err, nz 32 / nz 64 (fit_t1l.one):**
  - head (no W4): off -0.1493/-0.0349; F -0.1583/-0.0360; cov -0.0022/+0.0001; F+cov -0.0101/-0.0009.
  - merged build: cov -0.0022/+0.0001 and rxcov -0.0101/-0.0009 (reproduce head exactly); covW4 +0.0118/+0.0020;
    rxcovW4 (F+cov+W4) +0.0038/+0.0010. So with W4 on, F improves onset (|err| 3x smaller at nz 32, 2x at nz 64),
    and all four arms converge. cov alone (no W4) is still the closest on this deck.

## 4. The independent Cartesian derivation (cartesian-gravity-work-weight.md), folded in
- **Its item 1 (H zeroed at the wall faces makes the wall cells first order, +g h/12 m' at the bottom, -g h/12 m' at the
  top; the plain face form is second order at the walls).** This agrees in order and in location with step 1:
  - H's wall-cell error halves with h at both walls;
  - the plain face-work term is p 2 at the wall cells.
  - Its coefficient is not checked against these numbers. Unverified; the check that would settle it is to compare
    g h m'(wall)/12, projected the same way, with the budget's H wall entries.
- **The extra wall error that F exposes is not face work.** It is the code WB reference density (WBr), an eps-deck wall
  term, as expected. W4 removes it (section 2).
- **Its point 3b (eq. (4) is missing two h^4 terms): CONFIRMED.**
  - sympy with F expanded to s^4 gives -F''/(360 rbar^2) + F'''/(360 rbar) + F''''/480. The odd orders vanish, so the
    remainder is O(h^6). The replica had truncated F at s^2.
  - Fixed: the replica now expands to s^4 and prints the full coefficient; eq. (4) is restored.
- **Its point 3a (the Cartesian "gives up the trapezoid error" clause): AGREED, it was wrong.**
  - The Cartesian defect is a pure wall term. A wall closure plus a modified PE removes it with exact conservation.
    Section 8 (F) does this, and its four-point booking does it at O(h^4) in every cell.
  - The clause is rewritten. Two of its smaller points were also taken:
    - the headline now states its two hypotheses (two-point weights, PE held at PE_d);
    - the R = 1000H residual of 6.5e-13 is now called a cancellation floor, not round-off.
- **Where the fixes are:**
  - Local commit 950ad98 on top of 99d836a, NOT pushed. It touches
    docs/derivations/curved-gravity-work-weight.md and curved_gravity_work_weight.py.
  - The same edits are in the working copy of the derivation (curved-gravity-work-weight.md, radial_weight_replica.py and its output).
  - Note: the repo copy still lacks the option-F sections 7-8 and optionF_replica.py; whether they go into the PR is
    still open.
- **Its hypothesis 4 (a modified potential rescues spherical option B):** untested.
  - By the section-4 Lemma, any two-point booking conserves E+P~ for the potential found by telescoping the N-1 interior-face
    conditions (N unknowns), so conservation itself is automatic, with nothing to satisfy at the second wall.
  - For weights (3) the per-face defect is h^3/3, so eta ~ g1 h^2/(3 r_c), not /6.
  - The open question is only P~'s accuracy against int rho phi dV. Unverified; the check that would settle it is replica
    section 2 with phi~ in PE, plus the PE-accuracy comparison it describes.

## 5. Push (D and W ship together; rebase onto aea71ed)
- Rebased 4 commits onto aea71ed (8cea3ae + #292 + #293). The one conflict was implicit_hydro.cpp: #292's finite-column
  reject and the corrected-PE block touch the same spot. The block now goes BEFORE the reject, so a non-finite term is
  rejected too. range-diff vs the pre-rebase df2f8fb: commits 1, 3, 4 are `=`; commit 2 differs only in that hunk's context.
- A clang-format fix (whitespace) was folded into the code commit; the pre-commit check FAILED on it before the fold and
  PASSES after.
- Quick oracle subset on the rebased build (incremental build + ctest -R gravity_work|implicit|lu_failure|
  test_eos|vic|tall_column): BUILD-GOOD PASS (snapy 2.11.6.dev4+g5536c0a); 13/13 PASS (test_gravity_work_radial_exact_python,
  test_gravity_work_fixer_python, test_lu_failure, test_implicit_gravity_tall_column_python, test_implicit_stratified_solid_python,
  test_implicit_face_work_jacobian/operator, test_eos.release, ...).
- Pushed as commit 5536c0aa3c3524cdc48f433975d228835f06f677 (tree 174ef12b).

The local merge e65db14 was never pushed.
