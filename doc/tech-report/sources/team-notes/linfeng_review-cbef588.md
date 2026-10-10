# Preliminary independent review: `UCzhangxi/snapy` `next/curved-gravity-work-wb` at cbef588 (W/G/D/K)

Status: **preliminary**. I give no SIGN-OFF line here. A formal sign-off needs the final PR number and full head SHA, plus a delta review of that head.

## 0. What was pinned and verified

| item | value | how |
|---|---|---|
| requested base tree prefix `18e48c96` | tree `18e48c968db8758b0786d32b496cc8115c6d96ae` | `git rev-parse 18e48c96`: this is a **tree** object, not a commit |
| commit carrying that tree | `cbef588c1264dce86fea537f19479a4646e6b575` ("Take the x1 diffusion face coefficient as the mean of the cells' products") | `git log --all --format='%H %T %s' \| grep ' 18e48c96'` (only one commit matches) |
| requested head prefix `cbef588` | `cbef588c1264dce86fea537f19479a4646e6b575`, tree `18e48c96…` | `git rev-parse --verify cbef588^{commit}` |
| W/G/D/K diff base (merge base with `chengcli/snapy` main) | `aea71ed852effb09e6aa155dd26349f1210ef556` (= `upstream/main` when fetched) | `git merge-base upstream/main cbef588` |
| branch tip when fetched (2026-10-09) | `e5d0ec265f5b0589255745fae219e311507c86dd`, tree `9dfcfc031010020f8e68dc4fbebef514b2a00940` | `git rev-parse origin/next/curved-gravity-work-wb` |

The requested base tree and head are therefore the same commit, cbef588. The branch has already moved 7 commits past it (fd5e292, 6b8bd43, 79239b5, e659b69, 1648373, 0373968, e5d0ec2). Those are the expected seam fixes. **I reviewed and tested cbef588, not the branch tip.** Section 4 lists what the later commits change, read but not built or tested.

Scope read line by line: `git diff aea71ed..cbef588`, 35 files, +4066/−60. That covers W = `SNAP_WB_REF4` (`wb_ref4.{hpp,cpp}`, `hydro.cpp`, `balance_column.cpp`), G = `SNAP_X1_CENTROID_EXACT` (`x1_centroid.{hpp,cpp}`, `spherical_polar.{hpp,cpp}`, `hydro_forward.cpp`), D = `SNAP_GRAVITY_WORK_RADIAL_EXACT` (`gravity_work_radial.hpp`, `hydro_forward.cpp`, `implicit_hydro.cpp`, `meshblock.cpp`, `hydro.{hpp,cpp}`) and K = the diffusion face coefficient (`diffusion.cpp`), together with their tests and docs. I read `docs/derivations/wb-ref4.md` in full and `curved-gravity-work-weight.md` §7–8 in full.

Known findings that I do **not** repeat as new: G's pressure-source window and plain-mean ghost conversion use block-edge one-sided stencils. D's slope does the same in the explicit, implicit and logged-PE paths. D silently disables on cubed-sphere. K changes x2/x3 at rounding level.

## 1. New findings (preliminary; none blocks the D/VIC conservation claim)

**N1. Scope: the branch carries changes outside W/G/D/K.** Low severity, a process issue.
- `examples/bryan.yaml` changes the H2O/H2O(l) `cv_R` values (3.08424 and 9.070249; commits def53da, df9931e). This alters the thermodynamics of the Bryan example. I checked the stated identity by hand: 9.070249 − 3.08424 − 1 = 4.986009 = δ, and u0_R(l) = −24.845 × 273.16 = −6786.6602. `test_bryan_balance_ic` passes. It is still a physics change unrelated to the gravity-work/WB work.
- `tests/run_restart_cycle_limit.py` adds per-rank log separation (6b82e0c). This is test infrastructure.

Recommendation: the maintainer should decide whether these ride along or go in a separate PR, and the PR justification should cover them.

**N2. D (VIC): the "solved density change" is not separated from the requested or raw change by any test.** Medium severity: missing evidence, not a defect.
- The code is right in form. The post-solve term at `src/implicit/implicit_hydro.cpp:388-401` (cbef588) uses `moved = du[IDN] - _du0[IDN]`, summed over all `ICY` rows. That is computed after `vic_redistribute_*` (line 297) and after the availability-clamp bookkeeping, so it is the final stored density change: the same quantity, and the same mass rows, that the logged P at `src/mesh/meshblock.cpp:1052` differentiates.
- But every D test is dry, with no `ICY` rows, no active availability clamp, no solid mask, and VIC at Courant 1.2 only (`tests/test_gravity_work_radial_exact.py:171`). In those runs the solved change equals the matrix's raw change. A wrong choice, such as `_mass_corr[IVX]` requested or `_delta` raw, would pass the same tests.
- Missing evidence: a moist VIC column (condensate rows) with the dry or availability clamp active and the step still accepted, showing per-step E+P at round-off.

**N3. D (VIC): the post-solve term is not gated by the immersed-solid mask.** Low severity, hypothesis.
- `implicit_hydro.cpp:396-399` adds `corrected_pe_work(...)` to every column, with no `mask == 0` gate. The projection/clamp work right above it does use the gate (`implicit_hydro.cpp:355`).
- In a solid cell `moved` should be 0, but its slope stencil reads fluid neighbours, so a solid cell next to fluid can receive energy. It is then refilled each step.
- Hypothesis (untested): harmless to the fluid budget, but E+P with solids is undefined. No test covers D with `solid`.

**N4. W: the resolution flag is computed from block-local ghost `psf` and is not exchanged at x1 seams.** Low severity, hypothesis.
- `wb4_flag = wb_ref4_cells(...)` (`src/hydro/hydro.cpp:489`) runs before the seam ghost-row exchange of `pref`/`dref` (`hydro.cpp:509-548`). The flag (|ln(psf_lo/psf_hi)| > 0.5, dilated by two cells) is never exchanged.
- `wb_ref4_faces` then reads `flag` at the ghost cell `is-1`. For a split column the guard decision near a seam can therefore differ from one block. That only happens where the flag sits near the threshold, or where the local ghost scan differs from the owner's scan.
- Untested. The doc itself says multi-process seams are covered only by the in-process split test (`wb-ref4.md` §12).

**N5. W test coverage: `test_face_floor_wb_ref4` no longer exercises the floor fallback.** Low severity.
- With the switch on, `tests/test_face_floor.cpp:71-83` swaps the "floor fires" assertions for pinned switched fluxes (−1.1874e-7, 0.0303467).
- No test then checks the positivity-floor fallback under `SNAP_WB_REF4`. It still runs under the switch, but nothing triggers it.

**N6. #292 restore, not D-specific.** An observation, pre-existing.
- In my 2-D VIC rejection probe, `check_redo` restores the interior of `hydro_u` bitwise, but 912 ghost-row values differ from the pre-step state (max |Δ| = 0.85).
- This is identical with the switch **off**, and the redone step is bitwise identical to a clean step, so it has no effect on the result.
- Hypothesis: the ghosts are refilled between the restore and use (`peos->forward` in `apply_redo` or the stage boundary update). I did not trace this further.

## 2. D implicit/VIC path: the brief's specific questions

**(a) Does the post-solve g σ² s[ρ̇] term use the solved density change, consistently?** Yes, by code reading (cbef588):
- **Solve.** `_du0.copy_(du)` (`implicit_hydro.cpp:195`) holds the explicit stage increment, including the explicit D term. That term enters the RHS before the solve when `face_work_in_operator()` (`hydro_forward.cpp:752-757, 897-901`), so it passes through the matrix's energy row. After the solve, redistribution (`:297`) and the clamp/projection booking (`:325-356`), `moved = du − du0` summed over IDN+ICY (`:393-397`) is exactly the implicit part of the stored density change.
- **Explicit part.** The explicit part uses `-dt * vertical_mass_div` from the same IDN+ICY flux sum (`hydro_forward.cpp:700-716, 752-757`).
- **Linearity.** `corrected_pe_work` is linear, so the sum is g σ² s[Δρ_total]. The logged P (`meshblock.cpp:1043-1056`) uses the same total ρ (IDN + all rows ≥ ICY), the same σ² and the same stencil.
- **RK weighting.** The stage's density and energy live in the same `du`, so the RK weighting (and `dt_corr = b·dt` inside the solve) scales them together.
- **Measured.** E+P per **stage** ≤ 3.85e-16 (table below). Caveat from N2: in these dry runs that cannot distinguish the solved change from the raw change.

**(b) #292 failed-solve rejection and redo: is anything booked twice or lost?** Neither.
- **Code reading.**
  - The D term is added in place on `du` before the `bad_results` / `bad_correction` checks (`implicit_hydro.cpp:388-411`), and `reject()` does `du.copy_(_du0)`, `w.copy_(w0)` and zeroes `_corr` / `_mass_corr` (`:200-218`). A rejected solve therefore discards both its D term and its whole matrix correction for the whole block: every column, not only the bad ones.
  - `_solve_failed` makes later stages return a zero correction (`:176-180`). Their explicit D terms are still booked, but into a step that `check_redo` will discard.
  - `reduce_redo_flags` allreduces with MAX (`meshblock.cpp:1294`), so every rank redoes. `apply_redo` restores `_hydro_u0` (`:1251`) and drops the gravity-work fix (`:1250`).
  - On the redo, stage 0 re-saves `_hydro_u0` and calls `reset_solve_failure()` (`:612-618`), and the explicit and implicit D terms are recomputed once.
- **Measured** (limiter-off arm, so the NaN reaches VIC `bad_inputs`; causes reported `floor vic-solve`; 9 `[ImplicitHydro] … nonfinite solve` messages), for sph_vic, cart_vic and cart2d_vic:
  - The interior is restored bitwise: interior max |Δ| = 0 in 3 of 3 cases.
  - The redone step is bitwise equal to a clean step from the same state (3 of 3).
  - The E+P change of the redone step is 0.0, 0.0 and 1.28e-16 relative, identical to the clean step.
  - With the limiter **on**, the EOS limiter catches the NaN first (`limiter nan`) and VIC never sees it.
  - Not exercised: a reject at `bad_results` or `bad_correction` (finite inputs, nonfinite solve output). There, discarding the D term rests on code reading only.

**(c) E+P conservation in VIC (switch on unless noted), CPU, float64, from the branch's own test and my probe:**

| case | Courant (dt·c_s/dz) | steps | max per-step \|Δ(E+P)\|/\|E+P\| | max per-stage | cumulative | E+PE_d per step (for contrast) |
|---|---|---|---|---|---|---|
| sph_vic | 1.2 | 200 | 3.22e-16 | 3.22e-16 | 1.14e-14 | 1.65e-07 |
| sph_vic | 5 | 200 | 3.22e-16 | 3.22e-16 | 1.14e-14 | 5.53e-07 |
| sph_vic | 20 | 200 | 3.22e-16 | 3.22e-16 | 8.70e-15 | 4.86e-07 |
| cart_vic | 1.2 | 200 | 3.85e-16 | 3.85e-16 | 1.12e-14 | 3.64e-07 |
| cart_vic | 5 | 200 | 3.85e-16 | 3.85e-16 | 1.12e-14 | 1.17e-06 |
| cart_vic | 20 | 200 | 3.85e-16 | 3.85e-16 | 9.49e-15 | 1.02e-06 |
| cart2d_vic | 1.2 | 200 | 3.85e-16 | 3.85e-16 | 1.09e-14 | 3.07e-09 |
| cart2d_vic | 5 / 20 | — | floor redo at step 8 / 2, **same in the switch-off arm** (explicit x2 CFL exceeded), not a D effect | | | |

- Switch-off control: E+P per step is 1.65e-07 to 1.17e-06, per stage up to 1.43e-06, while E+PE_d stays ≤ 3.85e-16. So the probe is sensitive to the switch.
- The branch test (`tests/test_gravity_work_radial_exact.py`, 20 steps) gives, switch on:
  - per-step E+P: sph 3.22e-16, sph_vic 3.22e-16, cart 2.56e-16, cart_vic 2.56e-16, cart2d 3.85e-16, cart2d_vic 3.85e-16.
  - rest max|u1|/c_s, off/on: cart 7.551e-16 / 7.195e-16, cart_vic 4.183e-16 / 4.048e-16.
  - one PLM stage, eq. 7 residual: 2.48e-14 (sph) and 2.63e-14 (cart), against a term of 3.3e-5.
  - logged ie + pe against E+P: ≤ 2.53e-14.

## 3. Line-by-line notes that found nothing wrong

- **D.**
  - `x1_variance` is the r²-measure variance about the r²-centroid. `x1v` is `0.75(r₊⁴−r₋⁴)/(r₊³−r₋³)` (`spherical_polar.cpp:17-20`), consistent with `shift = rb·h³/(6V)`.
  - The `centroid_slope` interior and both one-sided weights match the derivative of the 3-point Lagrange quadratic.
  - Excluding H (`!radial_exact`) matches derivation §7 ("F must replace H").
  - x2/x3 mass transfer leaves the summed P unchanged because the volume is separable (Cartesian and spherical-polar), as §7 property 3 and §8.6 claim.
- **G.**
  - The plain-mean weights solve r²-moments with 4-point Gauss–Legendre, exact for degree ≤ 6 integrands. The rhs is (1, 0, 1/12, 0, 1/80).
  - The source weights are (2/V)∫r L_j dr over the quadratic, with `vol` in cube form.
  - The hydrostatic correction with the switch uses Riemann p* in S_i. The comment says "the cell's own face states", but `x1-centroid-spherical.md` §4 documents the actual choice, so this is not a finding.
  - G turns W's reference on for spherical-polar (`hydro.cpp:480`), which is documented. `balance_column` follows only `SNAP_WB_REF4`, not G. Hypothesis: that matters only if `balance_column` is used to balance a spherical-polar column with G on.
- **W.**
  - The cubic-extrapolation rows E = (4,−6,4,−1) and (10,−20,15,−4) check out by Lagrange evaluation.
  - The face-primitive weights Σ_{j>k} dz_k L_j′(x_f) are correct.
  - The non-uniform cell-pressure 3-point Gauss rule is correct.
  - `wb_ref4_faces` needs `is ≥ 1`, which holds with ghosts.
- **K.** `face_scaled_coefficient` gives the mean of products, with wall extrapolation of the product (unchanged). The x2/x3 rounding change is a known finding, fixed in e659b69 (section 4).

## 4. Delta cbef588 → e5d0ec2 (read only; not built, not tested; formal delta review pending)

- **G source window and plain-mean ghosts at seams: addressed.** The new `HydroImpl::_x1_ghost_rows` exchanges the seam ghost plain means (tag 0x7724/5) and two ghost face pressures (tag 0x7722/3). `x1_pressure_source_stencils` gains `clamp_in` / `clamp_out`, so seam windows stay centred. The tags do not collide with 0x7715/0x7717/0x7718/0x7720/0x7721.
- **D one-sided slope at seams: not changed, only documented.** The comment in `gravity_work_radial.hpp` and the doc now say a split column differs at O(h⁴).
- **D on cubed-sphere: now a setup error** (`TORCH_CHECK` in `HydroImpl::reset`). `pcoord` is created before `phydro` in MeshBlock, so the check is reached there. A Hydro built without a MeshBlock skips it.
- **K x2/x3: the bitwise path is restored for `idir != 0`.**
- **New test `tests/test_x1_seam_split.cpp`:** not run.

## 5. Build and test record (all at cbef588c1264dce86fea537f19479a4646e6b575, clean tree)

- **Source build** following the README (`cmake -B build -DCMAKE_BUILD_TYPE=Release -DNETCDF=ON …; cmake --build build`; `pip install .`), CPU only (`-DCUDA=OFF -DUCX=OFF`), reusing the workspace's prebuilt dependency libraries: kintera 2.6.0 (≥ 2.5.13 required), pyharp 2.7.2, pydisort 1.8.15, torch 2.7.1+cu126, Python 3.11.13. Result: rc=0, and the package installed as `snapy 0.0.1.dev347+gcbef588c1`. I confirmed at import that the process maps this build's `libsnap_release.so`. No installed package was edited.
- **Environment workarounds** (none touch the source tree):
  - The filesystem refuses symlinks, so the repo's `snap -> src` link is a 3-byte file. I staged a timestamp-preserving copy of `src` as `snap/` (`cp -a`). A plain `cp -r` breaks GCC `#pragma once` identity and gave redefinition errors on the first attempt.
  - The `ln -sf` test and example inputs were copied into `build/tests` and `build/bin`.
  - `torchrun` comes from a wrapper on PATH.
- **Targeted tests:** `BACKEND=gloo ctest -R "<22 W/G/D/K, implicit, redo, diffusion tests>"`: **22 of 22 pass** after the input copy. The first run had 5 "bad file: *.yaml" failures and 1 missing `torchrun`, all from the environment. The list includes `test_gravity_work_radial_exact_python`, `test_wb_ref4_order_python`, `test_x1_centroid_rest_python`, `test_diffusion_x1_scale(.release/_python)`, `test_balance_column(_wb_ref4)`, `test_face_floor(_wb_ref4)`, `test_implicit_face_work_operator_python`, `test_gravity_work_fixer_python` and `test_check_redo_{floor,saturation,parallel}`.
- **Full suite:** `BACKEND=gloo ctest -j6`: 95 snapy tests. 84 passed in parallel. 7 multi-process tests failed under -j6 and pass serially; hypothesis: contention between concurrent torchrun/gloo jobs. 3 example tests failed on missing inputs and pass after the copy. That makes **94 of 95 pass**. `test_python_import_path_python` fails with `ModuleNotFoundError: torch`, because the test overrides PYTHONPATH and torch is reachable only through PYTHONPATH here. That is an environment issue, unrelated to the branch. The ~927 Eigen sub-tests are "Not Run" because they are not built.
- **Probe:** `SNAP_GRAVITY_WORK_RADIAL_EXACT={1,0} python vic_probe.py --tests xiz-gw/tests --mode conserve --nstep 200 --mults 1.2,5,20`, then `--mode redo [--no-limiter]`. The probe is a reviewer harness outside the repo that reuses the test's `build()` and `Column`.

## 6. Missing evidence (precise)

1. Moist VIC with active availability/dry clamp, accepted steps, and per-step E+P with condensate rows (N2).
2. A VIC reject at `bad_results` or `bad_correction` with finite inputs, to show directly that the D term is discarded there. At present this rests on code reading only.
3. D with immersed solids (N3), with x1 outflow boundaries, and in float32.
4. Real multi-process x1 seams for W, G and D at cbef588. The seam behaviour of W's flag (N4) is untested.
5. CUDA. I ran nothing on GPU in this review.
6. A build and test of the branch tip e5d0ec2, and of the final PR head once named, followed by the delta review and the formal sign-off.
