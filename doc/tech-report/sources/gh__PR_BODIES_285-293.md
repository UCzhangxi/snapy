> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# snapy upstream pull requests #285-#293 (merged), bodies
Fetched 2026-10-09 from the public chengcli/snapy repository (GitHub REST API).

## PR #285: Keep implicit gravity work consistent with mass transport

Merged 2026-10-08; merge commit `117e449`.

Fixes #283's implicit gravity-work operator mismatch.

Put Cartesian x1 face work inside the implicit energy row. In cell mode, book Roe mass-diffusion work with the actual face areas, cell volumes and face-to-centre distances, including spherical/cubed-sphere grids. Seal implicit mass transport at solid cells and account for energy changes from redistribution.

The original 11.3H #283 face-column regression passes at acoustic Courant 65.6, 197 and 657. Curved-grid budgets pass; the previous Cartesian gate omitted this term. Remove the blanket dz/Hp refusal and restore the 300 km floor-test deck.

Limits:
- A 45-cell, 40H face column at dt=1500 first requests retry on attempt 27, after accepting |w| about 365 m/s. Further accepted states can reach km/s velocities before max-redo stops the run. Some coarse face runs complete without a stop. Retry checks positivity/repair, not accuracy; small E+PE drift does not imply stability.
- On a 40H column at dz/Hp=0.8 and C=657, cell + fixer reaches 4.4946x top density after 300 accepted CPU steps (4.4962x on CUDA). With the fixer off, the CPU result is 0.9916x. Unlike base 531e839, which stops after 12 accepted steps in this case, this head continues. This is a behavior change. The coarse-grid thermal feedback remains unresolved; reducing dt or refining the grid removes it in the tested controls. Cell/fixer-off retains quadrature drift.
- The old #284 Limit is not a universal bound: reviewers find the 11H rest column stable through C~2000-2700, with sealed-wall roundoff refusal already near C2500 on CUDA/C2750 on CPU. These are deck/backend-specific observations, not thresholds; C6000 is not a general refusal onset.

Legacy face-wallc behavior is unchanged. This PR does not provide a general coarse-column accuracy or stability guarantee. Follow-up #286 tracks the fixer feedback and accuracy-based rejection.


## PR #288: Use curved-grid metrics for implicit face gravity work

Merged 2026-10-09; merge commit `d59836d`.

Implicit `gravity-work: face` currently linearizes cell work on curved grids and replaces it after the solve. This puts a different source in the matrix from the one applied to the energy update.

Both VIC assemblies now use the existing face-area, cell-volume and centre-to-face weights for the full face mass flux. Curved grids enter the same in-operator path as Cartesian grids, including the existing correction for projected or clamped mass transfers. The pressure reference and `cell`/`face-wallc` modes keep their existing definitions.

**Discrete conservation and energy-row derivation**

Let $\rho$ denote total mass density. For constant radial acceleration $g$, define $\Phi_i=-g x_i$, $\Phi_f=-g x_f$, and
$$
\kappa_{i,l}=\frac{A_l(x_i-x_l)}{V_i},\qquad
\kappa_{i,u}=\frac{A_u(x_u-x_i)}{V_i}.
$$
The existing `work_lo` and `work_hi` inputs are $w_l=\kappa_l/2$ and $w_u=\kappa_u/2$.

With frozen Roe diffusion matrices $B_l,B_u$, the incremental face mass fluxes are
$$
F_l=\tfrac12(m_{i-1}+m_i)-\tfrac12 B_l^\rho(\delta q_i-\delta q_{i-1}),
\quad
F_u=\tfrac12(m_i+m_{i+1})-\tfrac12 B_u^\rho(\delta q_{i+1}-\delta q_i).
$$
The energy source is $S_E=g(\kappa_l F_l+\kappa_u F_u)$. Subtracting its derivatives from the implicit energy row gives
$$
\partial_i S_E=g[(w_l+w_u)e_m+w_u B_u^\rho-w_l B_l^\rho],
$$
$$
\partial_{i-1}S_E=g\,w_l(e_m+B_l^\rho),\qquad
\partial_{i+1}S_E=g\,w_u(e_m-B_u^\rho).
$$
This replaces the old cell-work derivative $g e_m$ in both the 5×5 and reduced 3×3 systems. On a uniform Cartesian grid $w_l=w_u=1/4$. That path retains the exact original expressions and operation order, so implicit Cartesian face mode remains bitwise unchanged.

Let $M_f=\Delta t\,A_fF_{\rho,f}$ and $Q_f=\Delta t\,A_fF_{E,f}$. The cell updates obey
$$
V_i\Delta\rho_i=M_l-M_u,
$$
$$
V_i\Delta E_i=Q_l-Q_u+(\Phi_l-\Phi_i)M_l-(\Phi_u-\Phi_i)M_u.
$$
Therefore
$$
V_i\Delta(E_i+\Phi_i\rho_i)
=Q_l-Q_u+\Phi_lM_l-\Phi_uM_u.
$$
Shared internal faces cancel exactly. With sealed boundaries and no independent energy sources, the discrete sum $\sum_iV_i(E_i+\Phi_i\rho_i)$ is conserved in exact arithmetic, up to solve and floating-point error numerically. The projection/clamp correction uses the actual transferred mass, preserving this identity after redistribution. This statement excludes separate heating, saturation or floor interventions.


The two new curved-face finite-difference regressions fail on the base and pass with the fix (8/8 full/partial Jacobian tests). The face-operator and stratified/solid scripts pass with incremental native CPU and CUDA sm_120 builds. The raw curved-grid matrix energy-budget defect falls from about 6.64e-4 to below 3e-16. The base already closed the final-update budget at roundoff through its post-solve face swap; this fixes the operator inconsistency. Independent reviews found the spherical column stable through acoustic Courant 300, versus the base's first failure at 65.6.

Limit: independent review measured a scheme-9 per-step E+PE change of about 3e-12 from the column base at radius 7e7 m, versus about 1e-15 in the solver's $gr$ gauge. Main shows the same roundoff on a Cartesian column with its origin shifted to 7e7 m; this PR does not change it.


## PR #292: Cleanup after #288: reject failed VIC solves and test spherical columns

Merged 2026-10-09; merge commit `e51bdc2`.

Fixes #290 and #294. #288 is merged at **d59836d453a6e687b373f72456e5d9d439b8ef7e**. Current cleanup head: **7a69bef3eea41c1be1fdda4717d6c766f2d6acf3**, one scoped vicclamp diagnostic commit above **af6a3f879ec23c8aabd02d12ae221a618b713d0f**. An independent delta check and an independent CUDA re-sign remain pending. No merge or READY declaration.

A singular VIC solve currently shares status `1` with successful even-parity LU and can return nonfinite corrections. LU now returns zero on failure, retains +/-1 success parity, rejects scale-relative small pivots and nonfinite arithmetic, and checks all four original LU sites plus the four initial/later 3x3 bypass checks. The 3x3 checks factor a copy and retain the original inverse on success. Rejected columns skip backward substitution/redistribution, latch through RK stages, and enter the globally reduced `check_redo` cause. Retry and terminal VIC failure restore step input, including all local blocks. Diagnostics give rank, column, step, RK stage and retry.

**Files:** `src/math/ludcmp.h`; `src/implicit/{forward_sweep_impl.h,tridiag_thomas_impl.h,vic_solve_failure.h,vic_redistribute_impl.h,implicit_dispatch.cpp,implicit_dispatch.cu,implicit_hydro.cpp,implicit_hydro.hpp}`; `src/mesh/{mesh.cpp,meshblock.cpp,meshblock.hpp}`; `tests/{CMakeLists.txt,test_lu_failure.cpp,test_implicit_gravity_tall_column.py}` (the tall-column file preserves the face-only/fixer-off ladder and restores adjacent DEFAULT cell-work + global-fixer coverage at dt=997/100 s); `docs/derivations/290-lu-pivot-tolerance.md`. Cleanup-only diff: parent `d59836d` to cleanup head `80506f0`. The completed pure rebase drops #288’s original commits from this branch; the PR now contains only the cleanup delta.

### Pivot tolerance

Keep the original row magnitude `s_i = max_k |a_ik|` with its row permutation. Reject `|pivot|/s_i <= 8*N*epsilon_T`, including the last pivot. A length-N dot product/subtraction has accumulation factor `gamma_(2N) ~= N*epsilon_T` with IEEE unit roundoff `epsilon_T/2`; eight times that scale is a conservative guard band. The ratio is dimensionless and invariant under finite row scaling. This is a safety guard, not a condition-number estimate or a certified accuracy bound under arbitrary elimination growth. The derivation note (`docs/derivations/290-lu-pivot-tolerance.md@e75c1c3`) states the limits. N=3/5 thresholds are 2.8610e-6/4.7684e-6 for float and 5.3291e-15/8.8818e-15 for double.

### CUDA dispatch return-contract follow-up

Dispatch-follow-up measured head: **40402ecbc5d9301e968785fa3d855b6343eb5d00**, parent **328dad9aaedc3f4a78d5479cb258484969192f45**. A reviewer's reported `implicit_dispatch.cu:165` is a `ForwardSweep` call, not a ninth direct `ludcmp` call. All eight direct LU calls already check zero: live `forward_sweep_impl.h` lines 64,76,111,123 and legacy/test-only `tridiag_thomas_impl.h` lines 49,54,81,86. The CPU wrapper checks `ForwardSweep` at line 159; the CUDA wrapper previously ignored that Boolean. [Issue reconciliation](https://github.com/chengcli/snapy/issues/290#issuecomment-6079144343).

The CUDA wrapper now checks the Boolean and returns from the column lambda at lines 165–167 (`src/implicit/implicit_dispatch.cu:165@40402ec`), matching the CPU wrapper's skip. The failure sentinel remains intact for host `check_redo`/rollback handling. Because the existing NaN guard already prevented failed backward substitution, this enforces an invariant rather than fixing a newly observed output failure; no separate behavioral RED is claimed for this three-line guard.

The original RED/GREEN test file is unchanged. Its four targeted device retry/stop tests at lines 207,211,215,219 (`tests/test_lu_failure.cpp:207@40402ec`) exercise this dispatch for partial/full assembly and step rollback. They were **not run on device locally**; their execution belongs to an independent device gate. A source-pattern test would only mirror this guard, and an artificial false-with-finite-output sweep would violate the existing sentinel contract, so no such regression was added.

Fresh validation: CUDA Release rebuild succeeds with **0 #20014-D and 0 #20011-D warnings**, counted in its successful build log; CPU regression run passes **21 cases in 62 ms**, with the four device cases skipped; full CPU `ctest -j1` passes **85/85 in 192.85 s**. The only new code delta is one CUDA file, +3/-2 lines. Applicable touched-file pre-commit hooks pass; its clang-format hook excludes `.cu`, so `clang-format --dry-run --Werror --lines=165:168` was run separately with 20.1.4 and passed. The earlier bitwise/column evidence below is pinned to its measured head; the CPU source is unchanged by this dispatch follow-up.

Historical pre-rebase upstream CI: [37918470768](https://github.com/chengcli/snapy/actions/runs/37918470768), head **40402ecbc5d9301e968785fa3d855b6343eb5d00**, event `pull_request`, **awaiting maintainer approval** (`completed/action_required`, zero jobs). No CI pass for that run is claimed. Draft status is not excluded by `ci.yml`; changing it would not clear approval, and upstream repository access is read-only. The earlier successful fork run below belongs to 328dad9aaedc3f4a78d5479cb258484969192f45, not this latest head. No additional fork run at the latest head is claimed.

Pre-rebase diff counts: **16 files, +584/-82** against stacked source parent 070ba601ef8cc225cd294d320e4b7554e358b1aa; **24 files, +639/-129** against main 117e449a620bd7fd50abe19239ab660a56d5d4cb. Those counts were recorded before #288 merged; the current diff against d59836d453a6e687b373f72456e5d9d439b8ef7e is 16 files, +584/-82.

### CUDA finite-check follow-up

An independent A100 gate **failed at e75c1c3fc4d4656a701e9cf14bf70ac9f36a8890**: both VIC CUDA assembly retry tests and scheme-9 decks hung; reverting only `ludcmp.h` restored the retry tests (reported 756/621 ms). These are reported independent measurements, not my local runtime results. The host/device call as the hang's cause remains a hypothesis until the assigned A100 rerun. [Issue ownership and reproduction](https://github.com/chengcli/snapy/issues/290#issuecomment-6077862205).

The follow-up replaces all seven finite-check sites (nine `allFinite()` expressions) with explicit per-element `std::isfinite` loops. It changes only `src/math/ludcmp.h`, `src/implicit/forward_sweep_impl.h`, and `src/implicit/vic_redistribute_impl.h`; success arithmetic, pivot tolerance and failure/rollback policy are preserved. `tests/test_lu_failure.cpp` is unchanged (SHA-256 `db87fbc89e446f1d754c0849490005942acbaed209e5d6d2c960b38eb40bd130`).

CPU results at finite-check head 328dad9aaedc3f4a78d5479cb258484969192f45: original base RED remains 21 failures; GREEN passes 21 CPU cases in 74 ms, with four device skips. Full default serial CPU CTest passes 85/85 in 249.61 s. Both nonsingular decks remain bitwise equal to base in all 12 cell/face × scheme 0/1/9 cases, across all four returned tensors. Cartesian and radial spherical face-work columns each pass five Courant rungs through 250 (40 steps/rung); maximum radial spherical speed is 4.935272260671767e-9 m/s. Touched-file pre-commit passes on the three changed headers.

A Release source build with nvcc 12.6.85 / GCC 11.5.0 targeting SM80 (A100) succeeds: `cmake --build <cuda-build> --target snap_release snap_cuda_release --parallel 4`. Counted `warning #20014-D` and `warning #20011-D` in the complete successful build log: **0 and 0**, respectively. The archived unchanged e75c1c3 production `implicit_dispatch.cu` compile emitted **24 of each locally** (the independent build reported 32 #20014-D); compiler-warning counts depend on build instantiations. No diagnostic suppression was added. Two local include-staging problems (mixed source headers, then missing `.cuh` forwarding headers) were corrected before the successful CUDA build; no installed packages or additional production files were changed. This is compiler validation, not an A100 runtime pass.

Finite-check sites retained at the latest head: LU input line 38 / output line 92 (`src/math/ludcmp.h:38@40402ec`), forward sweep lines 70,82,84,117,129,131 (`src/implicit/forward_sweep_impl.h:70@40402ec`), and backward sentinel line 34 (`src/implicit/vic_redistribute_impl.h:34@40402ec`).

Intermediate-head CI: upstream pull-request run [37909803342](https://github.com/chengcli/snapy/actions/runs/37909803342) is **awaiting maintainer approval** (`completed/action_required`, zero jobs) at 328dad9aaedc3f4a78d5479cb258484969192f45; it is not an executed test failure. Earlier upstream run [37894082930](https://github.com/chengcli/snapy/actions/runs/37894082930) is also approval-held at e75c1c3. A fork CI dispatch succeeded at full old head e75c1c3fc4d4656a701e9cf14bf70ac9f36a8890: Ubuntu 91/91 enabled tests in 519.93 s (including PNetCDF decomposition), macOS 77/77 in 2308.95 s, and pre-commit. That pass does **not** validate the new head; a second fork CI dispatch **completed successfully** at verified identical head 328dad9aaedc3f4a78d5479cb258484969192f45. All three jobs passed: pre-commit; **91/91 enabled Ubuntu CTest cases in 670.46 s**, including LU failure and PNetCDF decomposition (one CUDA test disabled); and **77/77 macOS CTest cases in 2330.35 s**, including LU failure. Both checkout logs confirm the exact full head. This workflow runs CUDA=OFF and does not replace the independent A100 runtime gate. Independent A100 runtime and sign-off gates remain pending at the new head.

### Original quantitative CPU evidence at e75c1c3

CPU Release source build: GCC 11.5.0, CMake 3.31.8, Torch 2.7.1+cu126, Kintera 2.6.0, PyHarp 2.7.2, PyDisort 1.8.15, NetCDF 4.8.1. CUDA/UCX/PNetCDF are OFF; NetCDF and Snapy's tests are ON. Torch's CUDA-enabled wheel does not constitute a Snapy CUDA build.

| Check | Base 070ba601ef8cc225cd294d320e4b7554e358b1aa | Cleanup e75c1c3fc4d4656a701e9cf14bf70ac9f36a8890 |
|---|---|---|
| LU/rollback CPU gtests | 21 failed, 0 passed | 21 passed, 0 failed |
| Cartesian face column, 40 steps/rung | no failure at C=6.6,65.6,100,197,250 | same |
| Strictly radial spherical x1 face column, 40 steps/rung | no failure at C=6.6,65.6,100,197,250 | same; max radial speed 4.9353e-9 m/s |
| Two nonsingular decks, cell/face, schemes 0/1/9, 5 steps | reference | 12/12 cases bitwise equal, all four returned state tensors |
| Full default CPU `ctest -j1` | not claimed | 85/85 passed, 189.02 s |
| Touched-file pre-commit | not claimed | clean |

RED used the current test source compiled with unmodified archived base headers and the preserved CPU library built at the full base SHA. The first 16 regressions were committed before production fixes (`83b5ed98742a0b2143355819b6ad1732b23ec1c5`). Added coverage includes finite-input assembly failure into redo and a two-local-block terminal-stop test that failed before its fix. Four CUDA gtests are explicitly skipped in the CPU build.

GREEN commands:

```
cmake --build <cpu-build> --parallel 4
(cd <cpu-build>/tests && ./test_lu_failure.release)
ctest --test-dir <cpu-build> -j1 --output-on-failure
python tests/test_implicit_gravity_tall_column.py --device cpu --nstep 40
pre-commit run --files <the 15 cleanup files listed above>
```

The default full CTest's first attempt passed 78/85: an isolated Python import lacked a dependency, and preloading the native library caused six NetCDF import/check segfaults. A direct import reproduced that preload failure. A task-local dependency wrapper and removal of the preload corrected the environment; the subsequent full run passed. After restoring the same configuration from the optional dependency attempt, a fresh build and full serial run again passed 85/85 in 189.02 s. No production NetCDF changes were made. The additional `FULL_TESTS=ON` serial CPU run passed 88/89 enabled tests in 450.50 s; its one disabled test is CUDA/UCX. The remaining shallow-splash decomposition arm explicitly requires PNETCDF=ON. A task-local Pinc 0.2.0 attempt could not link: Commux is absent and the wheel needs Torch/C++ runtime symbols unavailable here. That optional local PNetCDF build remained unavailable; both recorded fork CI runs passed the PNetCDF decomposition test in their configured environments. The validated CPU configuration is PNETCDF=OFF/FULL_TESTS=OFF.

### #285/#288 follow-ups and limits

Verified **already in main 117e449a620bd7fd50abe19239ab660a56d5d4cb**, against #285 final delta **ae4dd4ba20159402f855383485ef3c29626bae38**: sealed-wall refusal advice, CUDA assembly formatting, and native retry rollback assertions. Those changes are preserved; the stratified/solid test remains unchanged. The CUDA file gains only the explicit forward-sweep failure guard described above; existing #285 formatting is preserved. The meshblock comment now cites the reported 11H-deck refusal range near C=2500 (CUDA)/2750 (CPU), explicitly as deck-dependent measurements reported in #285, not new measurements or universal thresholds.

The spherical regression uses one angular cell to test a strictly radial column; Cartesian keeps its original eight periodic copies. A separate eight-angular-cell spherical probe measured on base 070ba601ef8cc225cd294d320e4b7554e358b1aa and previous head e75c1c3fc4d4656a701e9cf14bf70ac9f36a8890 first exceeded the 1e-7 m/s rest tolerance at C=197 (step 28), and at C=250 exceeded it at step 13. This limit is **pre-existing, unchanged** across base/head; both measured a maximum speed of 1.1715986861388748e-7 m/s at the first failure. This cleanup does not claim angular-mode stability. The same probe is retained in the author's evidence, not made into a relaxed passing test. #286 and #289 implementation are excluded. Passing through C=250 is a tested range, not a general stability guarantee.

### Verification ownership

Implementation and assigned CPU verification remain my responsibility. **An independent A100 gate covers:** full CUDA `ctest -j1`, device RED/GREEN (including the four cases skipped in the CPU build), and nonsingular bitwise decks at this exact head. The `cuda_*assembly*` gtests provide device retry/terminal rollback coverage; device pivot and sweep checks remain part of that independent gate. **Independent reviewers own current-head sign-offs, including a check of the original 0.755 face column and its independent RED cases.** The earlier A100 runtime gate failed at e75c1c3. Assigned reviewers must re-sign the new pure-rebase head 80506f082cad35cba5e89286fb8cf1c14642d139 after verifying tree identity and range-diff; please return the full verified head SHA. The reported independent CUDA evidence is attributed below, not claimed as my runtime work. I have not duplicated their CUDA/review work, and no independent sign-off is claimed. No merge or release is authorized by this PR.

### Authorized pure rebase after #288 merge

Head **80506f082cad35cba5e89286fb8cf1c14642d139**, base **d59836d453a6e687b373f72456e5d9d439b8ef7e**, tree **0510975febc2d54773eefc3f285669125c3c3f0f**. The tree is exactly identical to pre-rebase head **40402ecbc5d9301e968785fa3d855b6343eb5d00**; `git diff --exit-code 40402ecbc5d9301e968785fa3d855b6343eb5d00 80506f082cad35cba5e89286fb8cf1c14642d139` is empty. #288 was squash-merged: its signed head **070ba601ef8cc225cd294d320e4b7554e358b1aa** and merged main/tag commit share tree **939b9b2bcc0092ae67bf9349eccfd95efcfa6d9b**; the original signed head is not an ancestor of the squash commit. The cleanup head now descends from the merged main commit.

`git rebase --onto d59836d 070ba60` applied cleanly. Range-diff `070ba60..40402ec d59836d..80506f082cad35cba5e89286fb8cf1c14642d139`:

```text
1:  83b5ed9 = 1:  0754d53 test: reproduce LU failure and VIC retry gaps (#290)
2:  e75c1c3 = 2:  c97bd51 fix: reject failed VIC solves through step redo (#290)
3:  328dad9 = 3:  4232d9e Use device-safe finite checks in VIC and LU
4:  40402ec = 4:  80506f0 Honor VIC forward-sweep failure in CUDA dispatch
```

All four patches, authors, author dates and commit messages are unchanged; no attribution trailers were added. Current cleanup-only diff: **16 files, +584/-82**. The one authorized push used an explicit lease on **40402ecbc5d9301e968785fa3d855b6343eb5d00**. No source edit, rebuild or duplicate numerical gate was performed. The push/source/rebase/rebuild hold is reinstated.

The existing measured evidence is carried by exact tree identity, not rerun or renamed as new measurements: my CPU **21 GREEN cases / four device skips**, serial CTest **85/85 in 192.85 s**, and CUDA compilation **0 #20014-D / 0 #20011-D** were measured at 40402ecbc5d9301e968785fa3d855b6343eb5d00. Earlier bitwise/column and fork-CI evidence remains pinned to the heads stated above. An independent reviewer reports independent CUDA **RED 0/4 → GREEN 4/4**, **12/12 bitwise**, and **0 #20014-D / 0 #20011-D** at 40402ecbc5d9301e968785fa3d855b6343eb5d00; that is attributed independent evidence and carries by tree identity, not a new device run by me. The assigned reviewers own re-signs on 80506f082cad35cba5e89286fb8cf1c14642d139; none is claimed here.

Restarted upstream `ci.yml` pull-request synchronize run **[37940998206](https://github.com/chengcli/snapy/actions/runs/37940998206)** targets exact head **80506f082cad35cba5e89286fb8cf1c14642d139**. Its public page says **awaiting approval from a maintainer**; API state is `completed/action_required`, **zero jobs**. This is an approval hold, not an executed test failure or CI pass. The workflow accepts synchronize events to main and has no draft exclusion; the draft was preserved. No new fork run or CI pass is claimed in this rebase update.

### Five-request review revision

Old head **80506f082cad35cba5e89286fb8cf1c14642d139** → new head **af6a3f879ec23c8aabd02d12ae221a618b713d0f**. One new commit; the existing four cleanup commits, authors and messages are unchanged. Revision diff: **4 files, +83/-15**.

1. [Tall-column test:49](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/tests/test_implicit_gravity_tall_column.py#L49) omits both gravity-work keys for the DEFAULT arm, exercising cell work with the global fixer enabled; [line 147](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/tests/test_implicit_gravity_tall_column.py#L147) preserves the old dt=997/100 s runs. The face-only/fixer-off Cartesian and radial spherical ladder remains intact. CPU: both default arms pass **40 steps**, max|w| **4.511774343115081e-9 / 4.670689623043551e-9 m/s** at 997/100 s. Both face ladders still pass all five Courants through 250. This file and rationale are on the Files line above.
2. [Thomas sweep:63](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/src/implicit/tridiag_thomas_impl.h#L63) and [line 99](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/src/implicit/tridiag_thomas_impl.h#L99) replace the remaining two finite-check sites (four allFinite expressions) with per-element `std::isfinite`. This header remains test-only in the current production include graph. No change to nonsingular arithmetic or tolerance.
3. [Pivot derivation:58](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/docs/derivations/290-lu-pivot-tolerance.md#L58) now states float32 conditioning limitations. **166/5000 at cond 1e6 and 4915/5000 at 1e8** are attributed to an independent review probe, not measured by me. They are not a universal condition-number cutoff.
4. [CPU/device finite-column tests:291](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/tests/test_lu_failure.cpp#L291) call `forward_masked` with finite float32 inputs, a 1% per-layer pressure gradient, finite gamma=1.4 and positive dt=10000 s. The test requires rejection, untouched correction/primitive inputs, redo cause and rollback to the saved step input. A workspace-only **guard-disabled comparison** (same dispatch/sweep/LU code except the relative-pivot guard, with renamed template symbols to isolate it) is RED: **1 test fails**, rejection false, input modification and redo/rollback failures. Production GREEN: **22 CPU cases pass in 63 ms**, **5 device cases skipped** including the new device twin. This is targeted guard-disabled RED evidence; it does not relabel the original base RED or claim a device forward_masked execution. Existing RED/rollback cases remain intact.
5. **_clamp_residual does not reset each step.** It is registered as zero in [implicit_hydro.cpp:116](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/src/implicit/implicit_hydro.cpp#L116), exposed as a running maximum in [implicit_hydro.hpp:88](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/src/implicit/implicit_hydro.hpp#L88), and its sole update is [implicit_hydro.cpp:312](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/src/implicit/implicit_hydro.cpp#L312). Stage-zero resets [meshblock.cpp:616](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/src/mesh/meshblock.cpp#L616) clear only dry-clamp/failure marks. The reject lambda restores du/w/corrections but not this meter. `torch::maximum(0, NaN)` produces NaN, and the next maximum with finite zero remains NaN (local tensor-semantic reproduction). Thus a NaN residual from redistribution before the late finite-result reject at [line 382](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/src/implicit/implicit_hydro.cpp#L382) can persist. Early LU failure is checked before this update, so the new finite-pivot rejection does not reach it. **No actual finite-input late-reject column poisoning this diagnostic has been reproduced here**; this conditional diagnostic risk is reported, not silently fixed beyond the revision scope. Any production follow-up needs an issue, ownership and end-to-end RED before source edits.

Local CUDA checks: nvcc **12.6.85**, actual available GPU **GTX 1080 Ti**, SM61 standalone Thomas probe. **6/6** device controls/rejections pass: N=3/5, nonsingular control and finite near-singular first/later matrix. The expanded standalone compile emits **13 #20014-D / 19 #20011-D**, versus **21/27** compiling the old header with the same probe. The eight removed warnings of each class came from the finite-check sites; **no allFinite diagnostic remains**. Remaining warnings arise from the pre-existing Eigen 5x5 inverse instantiation in the legacy ordinary `if` branch, not the new loops. The earlier smaller 3x3-only compile had zero of these warnings; no claim of zero total warnings in the expanded probe or a new full CUDA build is made. **The new CUDA forward_masked gtest and full CUDA suite were not run locally**; an independent reviewer owns the exact-head CUDA re-signing/touched-test rerun.

Touched-file pre-commit passes; source Release build succeeds with GCC 11.5.0 / CMake 3.31.8 using the existing source-build configuration. No installed packages were modified. **Final serial CPU `ctest -j1`: 85/85 passed in 222.13 s** at this revision; the new CPU near-singular regression is included. Exact-head CI status is recorded below. Existing quantitative evidence and limitations elsewhere in this body remain attributed to their measured heads.

Exact-head upstream `ci.yml` synchronize run **[37955438151](https://github.com/chengcli/snapy/actions/runs/37955438151)**, full head **af6a3f879ec23c8aabd02d12ae221a618b713d0f**, is **awaiting maintainer approval**: API `completed/action_required`, **0 jobs**; the public page explicitly confirms the hold. This is not an executed test failure or CI pass. Workflow has no draft exclusion; draft status was preserved. No additional fork run is claimed. The one revision is pushed, and the source/push hold is reinstated for independent delta review and an independent device rerun/re-signing.

### Float32 zero-scale vicclamp fix (#294)

Issue-first ownership and reproduction: [#294](https://github.com/chengcli/snapy/issues/294), with [end-to-end RED](https://github.com/chengcli/snapy/issues/294#issuecomment-6084778345) established before production edits. At old head **af6a3f879ec23c8aabd02d12ae221a618b713d0f**, a finite float32 rest-column solve succeeds with unchanged zero corrections but vicclamp is NaN on both calls; its double control passes. This is the zero-scale case, distinct from the conditional late-reject diagnostic risk described earlier.

New head **7a69bef3eea41c1be1fdda4717d6c766f2d6acf3**, one commit, **2 files +64/-1**. [implicit_hydro.cpp:313](https://github.com/chengcli/snapy/blob/7a69bef3eea41c1be1fdda4717d6c766f2d6acf3/src/implicit/implicit_hydro.cpp#L313) uses the minimum normal float32 value **1.1754943508222875e-38** for float32 and retains **1e-300** exactly for double. A normal floor also avoids relying on subnormal CUDA arithmetic. [Rest-column assertions:344](https://github.com/chengcli/snapy/blob/7a69bef3eea41c1be1fdda4717d6c766f2d6acf3/tests/test_lu_failure.cpp#L344) check finite zero vicclamp, accepted solves and unchanged correction inputs over two calls; [float/double tests:351](https://github.com/chengcli/snapy/blob/7a69bef3eea41c1be1fdda4717d6c766f2d6acf3/tests/test_lu_failure.cpp#L351). These changes are in the existing Files line’s `implicit_hydro.cpp` and `test_lu_failure.cpp`. No running-max reset, solve policy or flow arithmetic change.

Measured CPU **RED: one float32 failure, one double pass, exit1**. After the source Release rebuild, **GREEN: 24 CPU cases pass in 56 ms; five device cases skipped**. Full serial CPU `ctest -j1`: **85/85 pass in 191.10 s**. Double pre/post snapshots are **raw-byte identical in all 12 cases / 56 tensors**, including **eight vicclamp diagnostics**: two decks (Cartesian/radial spherical), cell/face work, schemes 0/1/9, five steps each. No original-base measurements or independent results are relabeled as this verification.

The actual tall-column CTest log reports **2.73 s** for its 12 runs; this is below 60 s, so `tests/CMakeLists.txt` remains unchanged with TIMEOUT=120. Touched-file pre-commit and `git diff --check` pass. A local Torch CPU/CUDA dtype-floor smoke check returns finite zero for float32 and double; this is not a full Snapy CUDA build or an independent device re-sign. No installed packages were modified.

Range-diff against the old head (base d59836d) preserves all five existing commits and adds only this diagnostic commit:

```text
1:  0754d53 = 1:  0754d53 test: reproduce LU failure and VIC retry gaps (#290)
2:  c97bd51 = 2:  c97bd51 fix: reject failed VIC solves through step redo (#290)
3:  4232d9e = 3:  4232d9e Use device-safe finite checks in VIC and LU
4:  80506f0 = 4:  80506f0 Honor VIC forward-sweep failure in CUDA dispatch
5:  af6a3f8 = 5:  af6a3f8 Address cleanup review coverage and float32 limits (#290)
-:  ------- > 6:  7a69bef Keep float32 rest-column vicclamp finite (#294)
```

Exact-head upstream `ci.yml` pull-request synchronize run **[37958509985](https://github.com/chengcli/snapy/actions/runs/37958509985)**, head **7a69bef3eea41c1be1fdda4717d6c766f2d6acf3**, is **awaiting maintainer approval**: API `completed/action_required`, **zero jobs**, confirmed by its public page. This is an approval hold, not an executed test failure or a CI pass. Draft status was preserved; no additional fork run is claimed. The source/push hold is reinstated; no further #292 changes, duplicate CUDA re-sign, #293 work, merge or READY declaration.


## PR #293: #289 item 2: exact O(dx1^2) covariance and centroid correction to the x2/x3 fluxes on curved grids (behind SNAP_FLUX_COVARIANCE, default OFF)

Merged 2026-10-09; merge commit `aea71ed`.

## (a) Summary

Issue #289 reports that the horizontal (x2/x3) face energy flux in snapy is
built from cell-centre states, while a finite-volume face flux is the
**area-weighted average over the face**. For a product the two differ:

$$
\langle ab\rangle_A - \langle a\rangle_A \langle b\rangle_A = \sigma^2\, \partial_1 a\, \partial_1 b + O(h^4)
$$

so a term of relative order `dx1^2` is missing. #289 gives the Cartesian form
with `sigma^2 = dz^2/12`.

This PR covers **item 2**: the x3 direction and the **curved** grids
(spherical-polar and the gnomonic cubed sphere), for **all** rows, not only
energy. On a curved grid the Cartesian form is not simply `dz^2/12`, and it is
not the only correction. Two distinct O(dr^2) effects appear, because the cell
and the x2/x3 face carry **different measures**:

* **the face second moment.** The x2/x3 face measure is `r dr`, not `dr`, so
  `sigma_c^2 = (h^2/12) * (1 - h^2/(12 rbar^2))` exactly, not `h^2/12`.
* **the centroid offset.** The cell measure is `r^2 dr` (volume centroid `r_v`)
  but the face measure is `r dr` (area centroid `r_c`). The code's cell value
  lives at `r_v`, the face average wants `r_c`, and they differ by
  `delta = r_v - r_c = h^2/(12 rbar) + O(h^4/rbar^3)`
  (closed form in the derivation). This term is **first order in delta**, so it
  is the larger of the two and it is absent from the Cartesian form entirely
  (`delta == 0` there). Missing it was the one substantive error found and
  corrected during this work.

Per-row the structure is universal: the **covariance** part is row-specific (a
sum over the distinct pairs in that row's flux), and the **centroid** part is
`-delta * d1(F)` for every row.

Rebased onto current `main` `d59836d453a6e687b373f72456e5d9d439b8ef7e` (tag v2.11.3, i.e. after #288
merged); the branch sits directly on it with no merge commit.

## (b) The rows, and the switch

Everything is behind the environment switch **`SNAP_FLUX_COVARIANCE`, default
OFF** (`src/hydro/hydro.cpp:188`; unset / `0` / `false` / `off` / `no` all read
as off, parsed once into a function-local static). **With the switch off,
main's behaviour is bit-unchanged** - that is the property the reference test
asserts, not an approximate agreement.

**One exception, and it is by design: the cubed-sphere geometry change is
unconditional.** `GnomonicEquiangleImpl::face_area1()` and `cell_volume()`
(`src/coord/gnomonic_equiangle.cpp`) are replaced by the exact solid angle of
the gnomonic cell and the exact radial integral `(rp^3 - rm^3)/3`, and that
replacement is **not** behind `SNAP_FLUX_COVARIANCE`. The old forms were an
approximation of the same geometry, and gating a cell volume on a flux switch
would leave the grid inconsistent with itself. So **the bitwise switch-off
property holds on Cartesian and on spherical-polar**, where `cell_volume()` and
`face_area1()` are untouched, **but not on the gnomonic cubed sphere**, where
the switch-off result differs from `main` by the cell-volume and face-area
correction alone. `tests/test_cubed_sphere_cell_volume.py` tests that change on
its own: the six panels' volumes sum to `4 pi (ro^3 - ri^3)/3` and the discrete
divergence of `F = r rhat` is 3 in every cell, both only with the exact forms.

Rows, as implemented in `_flux_covariance()` (`src/hydro/hydro_forward.cpp`):

| row | covariance part | centroid part |
|---|---|---|
| total mass | **zero** | `-delta * d1(mass flux)` |
| dry mass | minus the sum of the tracer covariances | included in the above |
| moist tracers | `sigma_c^2 * rho * d1(q) * d1(u_n)` per tracer | `-delta * d1(q * mflx)` |
| energy | `sigma_c^2 * rho * d1(h) * d1(u_n)` | `-delta * d1((I+p) u_n)` |
| momentum | none (velocity-squared terms are out of scope, see (e)) | `-delta * d1(flux)`, pressure part as `p*` |

Two points that are consequences of the code, not choices:

* **The cell states are Favre (density-weighted).** `PRIM(IVX) = CONS(IVX) /
  PRIM(IDN)` and `PRIM(ICY+n) = CONS(ICY+n) / PRIM(IDN)`
  (`src/eos/ideal_moist_impl.h:40,:44`), so `rhobar * ubar == <rho u>`
  *identically*. Every covariance pair containing `rho'` must therefore be
  dropped or it is double counted. An earlier revision of this branch had the
  mass and tracer rows wrong for exactly this reason; the correction was
  verified against the code before it was applied.
* **Hydrostatic rest balance is preserved exactly.** The centroid shift of the
  normal-momentum flux breaks the discrete rest balance unless the *same*
  shifted pressure `p* = p - delta * d1(p)` is used in the **geometric source
  term** as well (`src/hydro/hydro_forward.cpp:597-628`). With both, the
  residual returns to round-off on spherical and on all six gnomonic panels.
  This holds for any metric, because the cancellation is linear in the one cell
  pressure.

The term telescopes for mass, each tracer and energy (total mass, total tracer
mass and `E+PE` stay exact to round-off), and at a closed x2/x3 wall every
scalar-row correction is **exactly** zero, since each carries `u_n` or
`d1(u_n)` and `u_n == 0` there. The momentum row telescopes as a flux but is
not a pure divergence - its geometric sources are not fluxes - so no exact
momentum invariant exists in main either, and none is created or destroyed
here.

Code scope vs the merge base `d59836d`: 16 files, +1384/-7 under `src/coord`,
`src/hydro` and `tests`, plus 9 files and +4828 of derivation under
`docs/derivations` (25 files, +6212/-7 in total; `git diff --shortstat` at head
`8cea3ae5a8297c82205c1cb9da03681f2343c0dc`). The tests are
`tests/test_horizontal_flux_covariance.py`, `tests/test_flux_covariance_rows.py`
and `tests/test_cubed_sphere_cell_volume.py`, plus the two added in
`668a6471a202fa4d95a9da40818ad1a29b869f82`:
**`tests/test_flux_covariance_seams.py`** - six cubed-sphere panels with closed
walls and a sheared non-rest moist state, where total mass, vapour mass and
`E+PE` must hold to round-off over 10 steps, and a spherical-polar rest state
that must stay at rest with the x3 flux disabled - and
**`tests/test_radial_face_moments.cpp`**, which checks
`radial_face_centroid_shift_` and `radial_face_moment2_` against the exact
integrals on three cells, so that either helper returning 0 fails.

**The seams test's two cases are not the same kind of test.** Its
**rest-gating case** is the one that fails on the earlier code: with the x3 flux
disabled on a spherical-polar rest state, the all-directions gate this branch
used before `668a6471a202fa4d95a9da40818ad1a29b869f82` shifts the x2 flux by
`p*` while leaving the x2 geometric source on the plain `p`, so the state does
not stay at rest. Its **conservation case** instead guards an invariant that
must survive the new term: total mass, vapour mass and `E+PE` over six panels.
Since `8cea3ae5a8297c82205c1cb9da03681f2343c0dc` both cases also assert that the
switch-on and switch-off arms differ by more than 1e-13 relative, so a renamed
or ignored `SNAP_FLUX_COVARIANCE` can no longer pass them; a reviewer reports
9.5e-12 and 9.1e-5 for those two differences at that commit.

**What `tests/test_flux_covariance_rows.py` does and does not prove.** Only its
**Cartesian arm** (`arm_cartesian`, which compares `eps_eff*nz^2` against the
`e7f9904` reference) is a RED test that fails on `main`: it is the arm that
needs this correction to pass. The **rest**, **uniform** and **offset** arms are
**regression guards**, not RED tests. A hydrostatic column staying at rest, a
uniform vapour field staying uniform under a cubed-sphere flow and invariance
under a constant tracer-velocity offset all hold on `main` too; those arms are
there to show that the new term does not break them, and they would equally
catch a future regression.

## (c) The derivation

Committed next to the code on this branch, as the deliverable
it is - not as a summary:

* **`docs/derivations/289-covariance-x3-curved.md`** (~2000 lines, LaTeX math)
  and its generated **`.tex`**, built by the committed
  **`docs/derivations/md2tex.py`**. The `.tex` has **never been compiled** - no
  TeX installation exists on the machine this was written on.
* The exact curved form carries no "small-curvature" or "thin-shell" limit
  sentence. The PR carries the exact form,
  cross-verified.
* The numeric checks are committed as scripts, so every number in the document
  is reproducible: `verify_exact_curved.py`, `verify_centroid_term.py`,
  `allrows_quadrature.py`, `energy_row.py`, `rest_balance.py`, `onesided.py`.
  These evaluate a **transcription** of the discrete operators from the cited
  `file:line` against Gauss-Legendre quadrature; they are not runs of snapy.
  Where a number is a transcription and not a measurement, the document says
  so.

## (d) Evidence, by source

**Independent cluster gates** - at commit `0b6b6ef6f1a013d9d57e4fd4033394e0df6bac9c`:
`ctest` 181 = 178 + 3, the Cartesian
`dz^4` convergence, and the three new tests GREEN. These carry over to
the branch head: the only differences are under
`docs/derivations`.

**A reviewer's numbers** - at `0b6b6ef`: dry Cartesian `eps_eff*nz^2` =
-0.013020 / -0.004937 / +0.000250 at nz 16/32/64 (within 3.1e-5 of the `e7f9904`
reference); offset invariance under shifting `u0` 3.5e-12; rest balance 4.1e-11
on spherical and gnomonic; a uniform vapour field staying uniform to 3e-17;
`ctest -j1` 90/90. The reviewer's CPU/CUDA run at `69941d8` additionally reports both
Cartesian decks clean on CPU and GPU with the switch off and on, GPU vs CPU
agreeing to 2.4e-15 relative in density and energy and 7e-16 absolute in
velocity after 20 steps.

**Independent check 1 - a reviewer**, commit
`afe9f6b827df51c6af5d3857e8cbd8d225db9b83` ("Record the velocity-squared gap
terms as known and excluded from #289"), file
`docs/derivations/issue289_moist_covariance_verifier.md`.

**Independent check 2 - an independent derivation**,
commit `e2c3f57120d772e5e861d8bf9674e4f7ab447e35`, path `study/289-allrows/`
(`derivation.md`, `symbolic_rows.py`, `quad_source.py`, `rest_balance.py` and
their `.out`). Reached the same two-term structure, the same per-row pair
assignment and the same `p -> p - delta*d1(p)` source mirroring independently.
**Its reported figures belong to its own deck, not to this branch's runs:** flux-only
breaks the rest balance by `+delta*d1(p)` times the source coefficient,
7.97e-04 -> 1.26e-5 with a factor of 4 per halving, and the mirrored source
restores round-off on spherical (theta row) and gnomonic (alpha and beta rows).
No disagreement with this branch's result was found; the only difference is
presentation.

**Commit-sha note.** Shas cited earlier in the review thread have moved twice:
once by a message-trailer rewrite, and once by the rebase onto the new `main`.
Current equivalents at head `8cea3ae5a8297c82205c1cb9da03681f2343c0dc`; the
mappings themselves are unchanged:

| cited earlier | after trailer rewrite | current (post-rebase) |
|---|---|---|
| `10270ed` | `76de0d7032c2ee2a66faf16c28ff67268c61f8c7` | `fc31f4c63fd5753a962a42927e97d7dca1bed273` |
| `807cfd8` | `86cf41350cebfad48c196dfa4610e030aabf7814` | `38063d1975db4587cf08852cc316356e84da1f12` |
| `69941d8` | (unchanged) | `6804422edc3c5c9e2f40665b407197d0cc5e06e3` |
| `0b6b6ef` | lifted as `b6593cf` | `518ceacc9d5cbca78b6e12ae22f9181c0c460bbe` |

The trailer-rewrite mappings were verified by identical tree shas
(`415ae7aac717d3d1416e723a835e29e80d29e549` and
`7af6d769f367303330d3046ae9ce8c55726f4437`) and identical subjects, not by
position. The rebase was verified with `git range-diff`: 10 commits in, 10 out,
1:1 and in order, nine of them byte-identical and the first differing only in a
context line that `main` itself changed. The set of lines this branch adds or
removes is byte-identical before and after the rebase, and the original
commit authors are preserved.

**Not claimed:** the library has never linked in the workspace where the
derivation was written, so none of the numbers above attributed to
independent checks are the author's, and no run of this code is claimed by the author.

## (e) Known and excluded

Full text in the derivation, §4C.3. In brief:

* **Velocity-squared covariances - out of scope**.
  `E+p = rho*h + (1/2)*rho*|u|^2`; only the enthalpy part is
  kept, so the dropped terms are the kinetic covariances, smaller by
  `O(Ma^2)` - relative 1e-8 to 1e-6 in #289's `Ma ~ 1e-4..1e-3` regime. The
  same scope decision excludes the `rho*u_phi^2` part of the geometric source `m_pp`
  (`src/coord/spherical_polar.cpp:262-265`) away from rest.
* **The two centroid terms are deliberately asymmetric.** The energy centroid
  part is `-delta * d1((I+p) u_n)` (`src/hydro/hydro_forward.cpp:147`, with
  `enth = W->I + p` at `:79`), so it **leaves the kinetic-energy flux out**,
  while the momentum centroid part is `-delta * d1(rho u_n u_v)` (`:163`),
  which **keeps** its velocity-squared part. Both follow the low-Mach `Ma^2`
  scope decision above: the kinetic piece dropped from the energy row is an `O(Ma^2)`
  addition to a term that survives without it, whereas the momentum row's flux
  is itself quadratic in velocity, so dropping that part would leave the row
  with no centroid term at all.
* **The momentum centroid's velocity-squared part is not mirrored into the
  geometric source - excluded**. Only the
  pressure part `p*` is mirrored. The unmirrored remainder is quadratic in
  velocity: exactly zero at rest, and a product of two perturbations in the
  linear onset problem.
* **The residual metric inconsistency `J` - excluded, with its bound.**
  Estimated at ~6e-8 to 1e-7 at the deck parameters used, from the
  stratification equivalent of the centroid shift. This is a
  transcription-based estimate, not a measurement of snapy.
* **The one-sided x1 pressure difference at the first and last interior
  cell - a deliberate stencil choice, not an exclusion.** Next to a
  cubed-sphere panel edge the x2/x3 face states in the x1 ghost rows are not
  filled for this purpose, so the **pressure** difference reads no ghost row:
  `d1_pressure` (`src/hydro/hydro_forward.cpp:21-31`) replaces the centred
  formula with a one-sided one at the first and last interior cell (lines
  `26-29`), unconditionally, so it is one-sided on **every** grid and not only
  near a panel edge. **This does not extend to the other rows.** Their
  covariance and centroid parts use the centred `d1`
  (`src/hydro/hydro_forward.cpp:129-131`), which **does** read the x1 ghost row
  at the first and last interior cell. It is harmless for the rest
  balance, because the same scalar multiplies two identical geometric
  coefficients and any difference cancels provided flux and source use the same
  one - and they do, both calling `d1_pressure` with the same `il()`/`iu()`
  (`hydro_forward.cpp:168` for the flux, `:617` for the geometric source).
  Measured on interior x1 cells, x2-momentum rest residual relative to
  `|S*p|`: base 2.392e-14, flux only 9.592e-08, flux and source together
  2.523e-14, and 2.523e-14 / 5.574e-15 at the two cells where the stencil
  actually is one-sided (`docs/derivations/onesided.py`).
* **An x1-split run differs from a single-block run, at the block-edge cells.**
  `d1_pressure` takes its one-sided branch at each block's own `il()`/`iu()`
  (`src/hydro/hydro_forward.cpp:168` and `:617`), so a domain decomposed along
  x1 uses it at interior cells that a single-block run differences centredly.
  The gap is `delta` times the one-sided error, an order estimate of
  `O(h^2/R) * O(h) = O(h^3/R)`, and only at those cells. The **rest balance
  stays exact** either way, because the flux and the geometric source take the
  *same* difference from the *same* call.
* **H9 is closed**, by `668a6471a202fa4d95a9da40818ad1a29b869f82`. The source
  shift used to be gated on *both* horizontal directions at once, so with one
  horizontal flux disabled the other's flux was shifted while its source was
  not. The gate is now per direction - the x2 source takes `p*` exactly when the
  x2 faces are corrected and the x3 source exactly when the x3 faces are
  (`src/hydro/hydro_forward.cpp:597-628`) - and
  `tests/test_flux_covariance_seams.py` covers the case.
* **Still open** and labelled as such in §4C.5: a discrete angular-momentum
  invariant (H5) and a face-level Favre reading (H8).

## (f) Two numbers that must not be collapsed

The independent check's **7.97e-04** and this branch's **9.359e-08** are
**different measurements** and must not be read as a discrepancy or averaged:

* 7.97e-04 is the flux-only rest-balance residual on **that study's own deck**,
  at its radius and depth, and it is the quantity shown to fall by 4x per
  halving.
* 9.359e-08 is the **stratification equivalent** of the centroid shift at
  **this** deck's parameters (`delta = 3.306e-03 m`, `d1(p) = -1.641 Pa/m`,
  `p = 5.518e+04 Pa`, i.e. `delta*|d1(p)|/p = 9.832e-08`), from
  `docs/derivations/rest_balance.py`.

Different `R` and different depth, therefore different numbers for the same
effect. Both show the same thing: flux-only breaks the balance, flux plus
mirrored source restores it to round-off.

## Status

Draft. Opened for review of the derivation and the row structure. The switch is
off by default, so with it off **Cartesian and spherical-polar results are
unchanged, bitwise**. **Cubed-sphere results do change**, by the exact
cell-volume and face-area correction alone, which is unconditional by design;
§(b) states why and names the test that covers it on its own.
