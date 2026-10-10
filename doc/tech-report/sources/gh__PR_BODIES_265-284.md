> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# snapy upstream pull requests #265-#284 (merged), bodies
Fetched 2026-10-09 from the public chengcli/snapy repository (GitHub REST API).

## PR #265: mesh: re-apply x1 walls inside tangential ghost slabs (#264)

Merged 2026-10-02; merge commit `4d856fb`.

Closes #264.

**Summary.**
- Problem: at a physical x1 wall, the corner ghosts beside an x2/x3 block edge kept the reflection of the pre-exchange column. With viscosity on, the cross-derivative terms at the wall row then did not cancel, and a resting, x2-uniform column grew u2 from cycle 1 (|u|/c_s 1.15e-5 at every x2 block edge of a 128 x 512 rest run).
- How found: a rest check of Anders & Brown (2017) polytropic convection (the fc_poly example, under review), confirmed by a 32 x 8 one-block test.
- Fix (a contributor's agent): after the tangential exchange, every installed x1 face function except outflow is re-applied inside the x2/x3 ghost slabs. A slab whose own tangential face is a physical boundary is left to that face's function. A first version keyed on the name `reflecting` and missed user wall functions; the final one does not.
- Tests: `test_wb_wall_corner.cpp`, 8 cases (stock and user wall, a one-block vs two-block x2 split, scalar corner primitives; each on CPU and CUDA). Red on main + test, user wall red on the first fix, the split case red on a copy-edge-column fix, all green at head.
- Size: 4 files, +388/-0: `src/mesh/meshblock.cpp` +47, `src/bc/bc_func.hpp` +4 (comment), `tests/test_wb_wall_corner.cpp` +336 (new), `tests/CMakeLists.txt` +1.
- Status: head ff2b4968f942e20e0f8714bca988d164528bc543; CI run 36904206982 green (pre-commit, ubuntu, macOS); CUDA ctest 99/99 at this head.
- Moist decks: no abort and no redo on main or head. Uranus is bit-identical; the Jupiter CRM differs by 1e-7 at t = 2000 s, then convection amplifies it.
- Limits: only x1 walls are re-applied; `Mesh::exchange_ghost_zones` has no refresh. Float32 not run. CPU-only builds with a visible GPU run other tests' CUDA paths: #266 (open question, not addressed here).
- Squash message: `mesh: re-apply x1 walls inside tangential ghost slabs (#264)`

Eight commits on main `5eeb9b6`:
- f1774875ea1e5528fd9cc921a529075b45c673d2 (a contributor): the red test.
- b1f87a66c3df26ab64b32647bb3a634da25001c7 (a contributor): the fix for walls named `reflecting`.
- 81cd351a6a507d3121d8dcd11f66a99af18f6492 (a contributor): re-apply every installed x1 face function, not only those named `reflecting`.
- 54e41a823364ee708a39f176272f53bc736b31f2 (a contributor): clang-format, no change in behavior.
- 8c7799ff18a38cfc212dd78a33ae396e3a1d5afd (a contributor): the test, extended as described under Tests.
- e630d916da3237b36c7f7db2349fe68fab9599ee (a contributor): fill periodic x1 corners too, leave a slab to a physical tangential face, and state the face-function contract in `bc_func.hpp`.
- 799b2b466d1b7b777544565167392a2423829b5c (a contributor): tests only, the x2 split case below (on CPU and CUDA); the file's CUDA cases skip in a CPU-only build.
- ff2b4968f942e20e0f8714bca988d164528bc543 (a contributor, head): rebuild the scalar primitives after the corner refresh, with a regression (below).

**#264: a viscous column grows u2 at a wall beside an x2 block edge.** The tangential exchange fills face ghosts but not corners (`skip_corner`). At an x1 wall, the corner cells therefore kept the reflection of the column taken before the exchange. Inside the block this is harmless. In the wall-adjacent row, though, the viscous stress reaches those corner cells through its cross derivatives, which then fail to cancel at the x2 edge, and u2 grows from rest. kappa_iso alone does not do it. With one block, the periodic x2 edge is such a seam too.
- Fix: `MeshBlockImpl::exchange_ghost_zones` re-applies the x1 face functions inside the x2 and x3 ghost slabs after the exchange. It does not re-apply the whole boundary pass, which would also wrap periodic faces and overwrite a neighbour's ghosts.
  - Outflow is not re-applied: its background must match the full block, and it needs primitives.
  - A slab whose x2 or x3 face carries a non-periodic function is left alone, since that face already wrote the corner (e630d91).
  - `bc_func.hpp` now states the contract this relies on: a face function may be called again on an nghost-wide slab, and a second call must give the same ghosts.
- b1f87a6 re-applied only functions whose name starts with `reflecting`. The check was a 128 x 512 resting polytrope behind the example's own wall function (`x1-inner/x1-outer: fixed_temperature`), 32 ranks. Cycle-1 max|u2|/c_s was 1.1509e-5 with and without b1f87a6, and 0 with 81cd351 and with e630d91. Behind stock `reflecting` walls it was 1.1505e-5 on main and 0 with every version.

**Tests (8c7799f).** `tests/test_wb_wall_corner.cpp` runs a resting polytrope (32 x 8 cells, one block, reflecting x1 walls, periodic x2, `nu_iso` 0.0234) for 10 steps. It checks max|u2|/c_s <= 1e-12 and max|v|/c_s <= 1e-12. Against f177487:
- The initial condition is projected onto the scheme's discrete hydrostatic balance with `balance_column` (`wb-wall-clamp: true`). Unprojected, the analytic polytrope alone grows u1 to 1.93e-7 c_s in the top rows with no diffusion, so the |v| line could not pass.
- `x2_uniform_rest_keeps_u2_zero_cuda` runs the same column on CUDA.
- `user_wall_keeps_u2_zero` (+ `_cuda`) puts the column behind the stock reflecting condition registered under another name.

Results of the head's test file built on three sources (CUDA build, V100; CPU and CUDA values agree to 12 digits):

| source | `x2_uniform_rest_keeps_u2_zero` | `user_wall_keeps_u2_zero` |
|---|---|---|
| f177487 (main + test) | FAIL, u2 3.9763e-5 | FAIL, u2 6.9629e-5 |
| b1f87a6 | pass | FAIL, u2 6.9629e-5 |
| e630d91 (head) | pass | pass |

Without diffusion, all four cases pass on every source. 8c7799f gives the same results as e630d91.

**Split test (799b2b4).** `x2_split_matches_one_block_exactly` (+ `_cuda`) runs a viscous flow that varies in x2 (a smooth 1e-3 tangential velocity) on one block and on two blocks split in x2, and requires the two to agree exactly (max abs error of primitive and conserved fields = 0). The four rest cases cannot catch a fix that copies the edge column into the corner: that wrong fix passes them, but not this case.

| source | split case, CPU device (w / u) | split case, CUDA device (w / u) |
|---|---|---|
| f177487 (main + test) | FAIL, 1.7493e-3 / 2.6221e-3 | FAIL, 1.7493e-3 / 2.6221e-3 |
| copy-edge-column wrong fix (reference branch, not merged) | FAIL, 4.3648e-5 / 7.4345e-5 | FAIL, 4.3648e-5 / 7.4345e-5 |
| head | pass, 0 / 0 | pass, 0 / 0 |

Measured on a V100 (both builds) and independently on an RTX 5090. On the CUDA build ctest is otherwise unchanged against e630d91 (81 of 91, the same 10 failures); in a CPU-only build the file's two CUDA cases move from fail to skip and nothing else changes. Moving `scalar_r` after the corner refresh left every value bit-identical, so the source is unchanged.

**Scalar corner primitives (ff2b496).** `exchange_ghost_zones` rebuilt the passive-scalar primitives (`set_scalar_primitive`) before the corner refresh, so with a tracer that varies in x1 and x2 the cached scalar primitives in the refreshed corners were stale. The call now runs after both refreshes (`src/mesh/meshblock.cpp` +4/-1). `scalar_corner_primitive_matches_conserved` (+ `_cuda`) requires each corner's cached primitive to equal the one rebuilt from the conserved fields. At 799b2b4 all 12 corner checks fail per device (max difference 4.1038e-7, CPU and CUDA); at head all pass. No number changes: scalar advection recomputes its ratio from the conserved fields, so every interior hydro and scalar value is bit-identical before and after the move, on CPU and CUDA, behind reflecting and user walls. On the CUDA build ctest is unchanged against e630d91 (81 of 91, the same 10 failures).

**Checks** (V100, torch 2.6.0+cu124, kintera 2.5.16.dev1+gb02e3da):
- ctest -j 1 on the CUDA build at head: 81 of 91 pass. The 10 failures are the same set on main + test (80 of 91 there; the 11th failure is the corner test): `test_exchange`, `test_output_barrier`, `test_check_redo_parallel`, `test_sedimentation_cubed_seam` (+ `_gloo`), `test_parentless_cloud_nb1_mp`, `test_straka`, `test_shallow_xy`, `test_shallow_splash`, `test_restart_cycle_limit`. All of them are multi-process or example runs that fail in this environment on main as well.
- On CPU (a contributor's agent), ctest -j 1 at 81cd351 with the original test: 51 of 53 pass. The failures were the corner test, on its |v| line only (u2 = 0; fixed by the projection above), and `test_uranus_cycle1_abort` (needs `run_hydro.release`, not built without examples).
- The fix changes the corner ghosts of every viscous wall-bounded run, so the two moist decks were run on CPU (`run_hydro.release`), main 5eeb9b6 against head:
  - Decks: `examples/uranus.yaml` for 500 cycles, and a 2-D moist Jupiter CRM (100 x 100, `nu_iso` = `kappa_iso` = 10) for 4000 cycles.
  - Seeding: `run_hydro`'s initial velocity noise (`torch::rand_like`) differs from process to process, so both builds seeded it with `torch::manual_seed(0)`. The seed was a local edit only and is not part of this PR.
  - Both decks end on the cycle limit with no abort and redo = 0 on every cycle, on main and at head.
  - `uranus.yaml` (no diffusion) is bit-identical at t = 2505 s.
  - The Jupiter CRM is identical at t = 0. At t = 2000 s it differs by at most 1.35e-7 of each field's maximum (theta_v; the float32 output's resolution). Once convection starts (cycle ~1250) the difference grows: temperature 1.0e-3, theta 4.7e-3 and liquid H2O path 0.26 of the maximum at t ≈ 48000 s.
  - For scale, two unseeded runs of main differ by temperature 8.4e-3, theta 3.6e-2 and liquid H2O path 0.90 at the same time.
  - The decks set reflecting x1 and periodic x2/x3 walls. 8c7799f and e630d91 give bit-identical results on both.

**Limits.**
- Only x1 faces are re-applied. The corners of an x2 or x3 wall beside a seam in another direction are not refreshed, and that case is not tested.
- Float32 was not run.
- The diffusion operator's wall list (`is_wall_boundary`, `src/mesh/meshblock_options.cpp:270-271`) matches names: `reflecting_*` and `fixed_temperature_*`. The test's `user_wall_*` is not on it, so that face keeps the two-cell ghost average. This is why the user-wall case reads 6.96e-5 instead of 3.98e-5 before the fix; that list is unchanged here. The 128 x 512 run used `x1-inner/x1-outer: fixed_temperature` (functions `fixed_temperature_inner/outer`, registered by the example), which is on the list.
- `MeshImpl::exchange_ghost_zones(MeshVariables&, int)` (`src/mesh/mesh.cpp:366-373`) goes through `exchange()`, not `MeshBlockImpl::exchange_ghost_zones`, so it has no refresh: a runner that calls it after an operator split gets no corner fix.

Fix by a contributor's agent; tests and measurements by a contributor; the split case and its wrong-fix control were designed and first measured by the upstream maintainer's agent; the stale scalar corners were found in review and measured by the upstream maintainer's agent.



## PR #268: eos, diffusion, tests, examples: small fixes (#267, #261, #266, #250 D1)

Merged 2026-10-02; merge commit `19976d0`.

Four small, independent fixes in one PR, one commit each (authors kept). Base: main 5eeb9b6.

Closes #267. Closes #261. Closes #266. Carries the #250 D1 fix (#250 is closed; see its last comment).

**#267 — eos: a vapor column split along x1 is repaired as one column** (a180989 failing test, 7821d45 fix, 643865e doc + test)
- `fix_vapor` repaired only the block-local part of an x1 column, so a column split over nb1 > 1 blocks aborted with "Failed to fix vapor mass fractions" where one block repairs it. The vapor column is now gathered along x1 (layout pz > 1), repaired whole, and each block copies back its slice.
- Test `test_vapor_column_nb1`: nb1 = 2 vs nb1 = 1, every interior vapor cell compared exactly (`EXPECT_EQ`), cpu/cuda x float/double. Red on main (nb1 = 2 throws), 8/8 green here, CUDA included.

**#261 — diffusion: kappa_iso conducts on temperature only** (7c16ed2)
- Heat conduction is a flux of temperature, -kappa grad T. The `on_theta` option (added in #253) conducted potential temperature and, as #261 measured, at kappa / gamma. It is removed with its code path, binding, docs and tests; a YAML that still sets it is refused as an unknown key. 34949d9 removes the orphaned `tests/test_kappa_adiabatic_rest_cuda.py` wrapper.

**#266 — tests: a CPU build skips every CUDA test path** (99b14ee)
- A build without CUDA now disables every test named or labelled cuda/gpu and sets `SNAPY_BUILD_CUDA=0` for the Python tests, even when a GPU is visible (blanket build-capability guard).
- d32bd47: on CMake < 3.22 (the minimum is 3.18) the variable is set with `ENVIRONMENT`, since `ENVIRONMENT_MODIFICATION` needs 3.22.

**#250 D1 — examples: Bryan opt-in IC at the solver's discrete moist rest** (7110117)
- `balance-ic` (default off) iterates saturation and hydrostatic projection in the Bryan caller until density changes by <= 4 eps, pressure by <= 1e-13 relative and the projection residual <= 1e-13, capped at 8 passes; `balance_column` stays a hydrostatic projector. On the 200 x 16 rest column it stops at pass 6 (last max|dp| 1.6e-9 Pa). Test `test_bryan_balance_ic`.

**Verification** (on 7110117; d32bd47 changes only the CMake < 3.22 branch of the CPU-build test setup, not reached by a CUDA build) (V100 sm_70, ctest -j1; the 10 failures in every run are torchrun port EADDRINUSE rows that fail identically on main):
- CUDA build: 80/90, failure set identical to main's CUDA build; 195 CUDA gtest cases OK, 0 failed; all 6 cuda/gpu ctest entries pass.
- CPU-only build with a GPU visible: 74/84, the 6 cuda/gpu entries disabled, 0 CUDA cases started. Control, main CPU-only on the same node type: 50/90, 30 extra failures from CUDA cases (#266 reproduced on main, gone here).
- Full CPU ctest before/after each fix on the fixer's own build: no new failure. pre-commit --all-files clean (the #261 and #266 commits carry a clang-format-only fix, 8 files +14/-16).


## PR #269: limiter: on the moist-mixture EOS, withheld species mass carries its energy and momentum (#236)

Merged 2026-10-03; merge commit `f20b0a0`.

Closes #236 (arm A, z = 1; the limits are listed at the end).

At a limited face, arm A withholds species mass together with its energy and its momentum. For moist-mixture the specific enthalpy is `u_n + z_n R_n T` for a vapour, plus kinetic energy. `u_n` and `z_n` come from kintera (`eval_intEng_R` / `eval_czh` in `MoistMixtureImpl::species_enthalpy`), then `Rgas * inv_mu`. It is not a hard-coded linear formula. Ideal-moist is unchanged and stays bitwise equal to main on every row and face.

The first commit (`3077c75`) is the squash of `5281c51fd272662c8625142c01c29584af42afb7` and `562d4979b92e4f48d5bd1a5043b9d9e81068ef75` onto main `5eeb9b6761ae484a98b3993aae18314fc58cf862`. Its tree matches the second of those. The second commit (`2514db8`) adds only the `_cuda` twin of the carry test; the third (`fb7b6c8`) makes that twin skip via `snapy_cuda_test_enabled()`, so a CPU-only build with a visible GPU skips it instead of failing. All three are replayed unchanged (range-diff `=`) onto main `e80b5c1`. The test `flux_positivity.moist_mixture_withheld_mass_keeps_its_energy_and_momentum` pins the carry. On main the same column was pinned the other way (`moist_mixture_withholds_no_energy_or_momentum_yet`), so the new test fails there and passes here. A second test checks the NASA-9 / H2 species sum against internal energy plus pressure (relative tolerance `1e-9`; the column residual is `1.4e-16`). A `_cuda` twin of the carry test runs the same column on the GPU (skipped without CUDA). Neither test uses `debug_disable_flux_positivity`. That knob stays out. An unlimited reference is `limiter: false`.

Study artefacts stay at these commits:

- rescore, 16 cards, species-only census: `03b16e17c7dbf288d35520b398273de2f27b5f34`
- uranus 500 and `study/236/gate2/RESULTS.md`: `819334e41102adf9b9edb45dc7c476b5736fc411`

Gate 2, CPU, fp64, kintera 2.5.13, `use_nasa9_cp=0`, `use_h2_cp=0`, `Rgas=8.31446`. Species census is 0 on all 16 cards. O3, T, I1, and I2 pass. Worst O3 enthalpy ratio `9.42e-4`, worst `|dT|` `1.14e-13` K, worst I1 `2.75e-5`. I2 is bitwise. Limited-face counts match the Gate 0 list: adv 5, settling 5, x2 30, donors 4, mixed 5, vapor-u0 5. IDN flux is bitwise equal to the unlimited flux. Worst energy ratio `1.21e-4`, worst momentum ratio `1.30e-4`, worst column ratio `4.73e-5`. The five moist-mixture mutations each turn O3 and the energy carry red by at least `1e3` times the tolerance (smallest O3 ratio `9.04e10`, mutation 4; smallest energy ratio `1.22e10`). B2's flux is bitwise equal to `limiter: false` on all 16 (`max abs 0`).

Uranus, 500 cycles, same seeded driver, no redo and no abort. The effect is small. max `|dT|` of arm A minus main is `1.232e-9` K. `positivity_hits` is 484761 against main 484774. Total energy differs by 768 J, relative `5.09e-16`.

Not in this PR:

- `z != 1` is not done.
- Arm G is not done. Its positivity proof needs CFL at most 0.5, and the vertical direction is implicit.
- Dry IDN below `1e-10` at `dt = 1` is outside #236. Unmodified main shows the same minima.
- `equilibrate_tp did not converge after 5 iterations`, 9682 times on both main and arm A in the uranus run: not an arm A defect; fixed separately by #273 and chengcli/kintera#138.

CUDA (V100, ctest -j1, on the same three commits over main 19976d0): 81/91 vs main 81/91, the same failure set (10 torchrun port EADDRINUSE rows), 0 status changes; the `_cuda` twin runs and passes on cuda:0. CPU-only build with a GPU visible: 75/85 vs main 75/85, same failure set, 0 CUDA cases started; the twin is skipped (on the second commit alone it failed with `DispatchStub: missing kernel for cuda`).


## PR #273: examples, build, output: small fixes (#270, #271, #272)

Merged 2026-10-02; merge commit `e80b5c1`.

Three small, independent fixes in one PR, one commit each (authors kept). Base: main 19976d0 (#268).

Refs #270 (its kintera side is chengcli/kintera#138). Closes #271. Closes #272.

**#270 — examples: uranus max-iter 5 -> 10** (6eed6c0)
- `examples/uranus.yaml` L76 (equation of state) and L90 (internal boundary). nlim stays -1. 10 is already kintera's default when the key is absent. The L90 key caps only the `rectify_solid` flip loop, reached only from Python; raised for consistency.
- With max-iter 5 the initialization prints 9682 `equilibrate_tp did not converge` lines, 3090 of them real non-converged calls; the rest are the last-iteration off-by-one fixed in kintera#138. At max-iter 10: 0 lines.
- 20 cycles, `examples/run_hydro.cpp` built at ddd1a79 (before #268), CPU, one thread, one run per cap (a reviewer's own run at this head reproduces the warning counts, 9682 -> 0, and shows no measurable step-time change, 0.233 vs 0.234 s/step): no warning of any kind during the 20 steps at either cap; cycle-20 internal energy 1.5100017318351e+18 (cap 5) vs 1.5100017145055e+18 (cap 10), relative 1.1e-8; 0.084 vs 0.099 s/step (one run each; not a timing claim). extrapolate_dlnp, which reads the same cap: 86 calls, 0 exhaustion warnings at both caps.
- No test or CI job loads `examples/uranus.yaml`; the uranus test decks keep max-iter 5.

**#271 — build: cmake_minimum_required 3.22** (3d5d749, 071b53c)
- The tree uses `cmake_path` (3.20) in FindTorch/FindKintera/FindHarp/FindDisort and `ENVIRONMENT_MODIFICATION` (3.22) in the tests; 3.21.4 aborts with `std::out_of_range` in the Torch lookup and 3.18.4 stops at `cmake_path`. With the floor at 3.22 a too-old CMake stops with the version message.
- 3d5d749 raises the floor and removes the PYTHONPATH branches for CMake < 3.22; 071b53c removes the remaining < 3.22 fallback (the `ENVIRONMENT` form of `SNAPY_BUILD_CUDA` added in #268), so a CPU build sets it only through `ENVIRONMENT_MODIFICATION`. `external/gloo` is untouched.
- CMake 3.22.6: main and this branch configure and build, 96 tests each, every Python ctest with the same result on both. CI runners use 3.31.6 (ubuntu) and 4.4.3 (macOS), so CI does not test the floor itself.

**#272 — output: after a restart, an output whose dt was changed fires again** (abbffad test, c6b233d fix)
- On restore, a saved `next_time` more than one `dt` past the resume time becomes `current_time + dt`, so the first frame is one interval later; a saved time within one `dt` is kept (the key-collision case keeps its cadence); `dt <= 0` keeps the saved time.
- With `dt` unchanged the reset cannot trigger: every firing keeps `next_time <= t + dt`. The resumed cadence starts at `current_time + dt`, off the old `dt` grid (a brand-new output snaps to `t - fmod(t, dt)` instead). An output deferred by setting `next_time` by hand (Python or C++) now comes back one `dt` after a restart.
- Test (straka, resume from t = 23.05 with `prim` changed from dt 1e30 to 7): 0 frames before the fix; after it, frames at 30.28, 37.25, 44.21, 51.16, 58.09, 65.28, 72.20. `run_restart_new_output` and `run_restart_key_collision` pass.

**Verification** (same tree on the #268 head; V100 sm_70, ctest -j1; the 10 failures in every run are torchrun port EADDRINUSE rows that fail identically on main):
- CUDA build: 82/92 vs main's 81/91, failure and skip sets identical, 0 status changes; 199 CUDA gtest cases OK, 0 failed. The one added ctest entry, `test_restart_dt_change` (#272), passes.
- CPU-only build with a GPU visible: 76/86 vs main's 75/85 on the same node type, failure sets identical, the 6 cuda/gpu entries disabled, 0 CUDA cases started; `test_restart_dt_change` passes.
- CMake 3.22 configures (3.22.0-rc1 and 3.22.6).


## PR #274: Slim routine CI and remove obsolete tests

Merged 2026-10-03; merge commit `2b6431a`.

PRs currently rebuild obsolete tests and repeat setup. This change runs the Linux core suite and four macOS smoke checks on pull requests, with full Linux and broader macOS coverage on main pushes and manual runs. Required check names stay unchanged.

- Remove obsolete or print-only tests and unused fixtures; retain assertion-based reconstruction coverage.
- Share restart setup and CUDA scripts, and shrink uniform EOS inputs without changing assertions or tolerances.
- Keep mesh_multi_block, straka, and exchange_decomp mandatory on Linux PRs. Additional references and decomposition cases remain in the full suite; the existing shallow_xy_decomp exclusion stays.
- Isolate reference outputs so Bryan files cannot contaminate pd-combine. Broader macOS runs exclude test_mesh_multi_block.release pending the Gloo-stall investigation.

Rebased onto #269 at f20b0a0, preserving its moist-mixture carry regressions and #273's restart-dt regression. Relative to main, the changes remain limited to CI, tests, and the FULL_TESTS help text: 2,122 fewer lines.

Validation at 3937f8b on a local machine: Linux CPU build and 79/79 core CTests passed in 366.90 s; workflow parsing, 79 core/84 full registrations, exact macOS exclusion, and git diff --check passed. The final tree differs from the previous bf5203a head only by #269's four upstream files. [Current-head CI](https://github.com/chengcli/snapy/actions/runs/37082433140) is running.

The three reference cases and six-rank splash decomposition passed before the rebase at 1a6a996; the full suite was not rerun on the final head. Local macOS and CUDA runtime remain unverified.


## PR #279: Fix audited numerical edge cases and simplify duplicated solver paths

Merged 2026-10-03; merge commit `e77940f`.

Closes #278.

Fix five reproduced edge cases and consolidate the duplicated paths audited after September 20. The fixes preserve existing public behavior where it is intentional, including independent user `scalar_ds`, log labels/precision, legacy restart matching, and redo cause ordering.

| Issue item | Change |
| --- | --- |
| 1 | Bound dynamic conduction by the minimum local mixture `rho * cv`, instead of dry-gas `cv`. |
| 2 | Carry dry-mass removal with the source-free RK stage ratio, after transport/implicit transfer; if that dry-mass base is exactly zero, preserve the entry tracer ratio. Keep explicit user tracer sources additive. Cover native/user addition and removal in RK1, RK2, RK3 and RK3S4. |
| 3 | Extrapolate bottom face temperature with actual cell/face spacing and the corresponding relaxation gain. |
| 4 | Give restart schedules an exact-cadence identity. Store legacy keys followed by precise keys in the same tensor, so older readers can load it and older writers discard the precise suffix when rewriting. |
| 5 | Check convergence after the final permitted `balance_column` update without duplicating the residual calculation. |
| 6 | Share cycle diagnostics; aggregate all local blocks before process reductions, including KE, PE and limiter meters. |
| 7 | Reuse `check_keys`, accepting missing/null optional blocks as defaults while rejecting non-map values; retain the `fric-heat` error and Kintera-owned keys. |
| 8 | Share whole-column repair mechanics while preserving cloud clamp versus vapor failure/copyback semantics. |
| 9 | Share redo collection and per-cause global reduction; drain saturation failures once per block. |
| 10 | Share six-face reference-pressure evaluation without changing arithmetic order or the independent oracle. |
| 11 | Register the five equivalent restart tests in one loop; retain multiblock-specific behavior. |

Numerical validation on `2af05fd2` (before the formatting-only follow-up):

- CPU Release build and fresh Python bindings passed. Of 82 registered CTests, all 81 enabled tests have passing results across the two configurations below; the CUDA/UCX decomposition test was disabled. This includes all 21 Python CTests, native unit tests, reference examples, restart cases and Gloo decomposition checks.
- The initial full serial run passed 79/81 enabled tests. Straka failed because the task's temporary Python package lacked `snapy.api`; after copying the existing source package, its unchanged test passed. The splash decomposition test's proc6 input requires PNetCDF; rebuilding the same source with `PNETCDF=ON` passed all four decompositions (mesh6, proc6, proc2×mesh3, proc3×mesh2). Neither recovery changed repository source or the reference oracle.
- The restart regression also passed with an actual older executable: new writer → old reader/writer → new reader, alongside precise, legacy-key and keyless cases.
- Independent old/new pressure-stencil comparisons were bitwise identical for float/double over five boundary/interior scenarios on each of CPU and CUDA (`sm_120`). This is a standalone kernel check, not full Torch CUDA integration.
- Regression coverage includes active-transport native/user dry sources in every stage of RK1/RK2/RK3/RK3S4, explicit additive tracer sources, moist dynamic-conduction stability, stretched-grid relaxation, final-iteration convergence, and diagnostics across two ranks with two local blocks each.
- `git diff --check` passed. At that formatting follow-up, production source was net 108 lines shorter (325 added, 433 removed).

The scalar-plus-gravity CPU microcheck measured medians of 3.140 versus 3.176 ms/step (5 batches of 20 steps); this small sample is not a statistically established performance result. The empty-native-forcing path avoids the added source calculation. Custom forcings remain conservative and need no new type/count cache.

The MPS stencil is unchanged. Full Torch CUDA integration and MPS execution were not run. The separate pre-write restart-counter issue #277 is outside this change.


CI follow-up `220f4a8a`: applied the repository’s `clang-format 20.1.4` rules. The formatting diff matches the original CI-generated patch exactly; independent review found no logic changes. Full local `pre-commit run --all-files` passes. [GitHub CI](https://github.com/chengcli/snapy/actions/runs/37094555659) passed on this commit: pre-commit, Linux build/test (80/80 CTests), and macOS build/test (4/4 CTests).


Review follow-up `b7ec5278` resolves two regressions found by hands-on cross-review:

- The moist public-API depletion case can make the source-free dry mass exactly zero. The entry-ratio fallback prevents the new NaN while retaining the base RK1 tracer mass of `-0.0005`; it does not introduce an epsilon cutoff. The committed regression fails at `220f4a8` and passes after the fix.
- Empty/null `dynamics`, `equation-of-state`, and `forcing` blocks again use defaults. Sequence/scalar values still fail validation, and null dynamics does not bypass forcing-key validation. The committed empty-block regression also fails at `220f4a8` and passes after the fix.

Validation provenance for this follow-up:

- After the automation pushed `b7ec5278`, an independent rebuild of that exact commit passed seven focused CPU CTests: EOS, scalar, hydro options, YAML keys, flux positivity, stage forcing and the new zero-base regression. Full local pre-commit passed.
- An additional public-API replay against that exact commit passed all four RK schemes with exact-zero and near-zero controls: every stage remained finite, all redo checks were zero, and tracer conservation/ratio checks passed.
- Before the concurrent push, the independently implemented candidate `5422d8c9` passed all 81 enabled CPU/PNetCDF CTests across two configurations (one CUDA/UCX test disabled). Its production changes were independently compared with `b7ec5278` and found semantically equivalent. This is supporting candidate evidence, not an exact-`b7ec5278` full-suite claim.
- [CI for the current commit](https://github.com/chengcli/snapy/actions/runs/37104068453) passed pre-commit, Linux (81/81 CTests, including both new regressions), and macOS (4/4 CTests). The macOS subset does not include the two new regressions. Full CUDA integration and MPS were not rerun by this Desktop task for this follow-up.

The pre-existing final-dry-mass-exactly-zero division is distinct from the source-free-base regression fixed here. No merge has been performed.


## PR #282: Clean up and remove plume eos

Merged 2026-10-03; merge commit `531579c`.

(no body)

## PR #284: Gravity work: cell form by default with a global E+PE fixer; face-wallc and face as options

Merged 2026-10-07; merge commit `531e839`.

Refs #283 (the explicit part; the implicit-operator part of #283 stays open)

Files: python/csrc/pyforcing.cpp, python/snapy/forcing.pyi, src/forcing/{const_gravity.cpp,forcing.hpp}, src/hydro/{flux_positivity.cpp,flux_positivity.hpp,hydro.cpp,hydro.hpp,hydro_forward.cpp}, src/implicit/implicit_hydro.cpp, src/mesh/{mesh.cpp,meshblock.cpp,meshblock.hpp}, tests/CMakeLists.txt, tests/run_straka_redo.cmake, tests/test_forcing.cpp, tests/test_implicit_gravity_tall_column.py, tests/test_gravity_work_fixer.py

Nine source files:
- the two options live with const-gravity (2 files);
- the work forms live in hydro (3);
- the implicit swap is gated (1);
- the once-per-step fixer and its diagnostic live in the meshblock step, with one sum over a Mesh's local blocks (3).

`tests/test_forcing.cpp` only selects `gravity-work: face` in the existing tests that pin the face form.

## What

`forcing/const-gravity` gains two keys:

| key | values | default |
|---|---|---|
| `gravity-work` | `cell`, `face-wallc`, `face` | `cell` |
| `gravity-work-fixer` | `true`, `false` | `true` with `cell`; with a face form an explicit `true` in YAML is refused, and the Python default resolves to `false` |

- **`cell`** (default). The energy equation keeps the const-gravity cell work `-g rho v` at cell centres. That is the form the implicit matrix linearises. The explicit face correction and the implicit face-work swap from #202 are both off. One exception: mass moved by sedimentation or by the positivity limiter (the part of the face mass flux beyond the Riemann flux) keeps its face-form work. The Riemann mass flux is averaged across x1 seams together with the flux, so this difference is single-valued at seams.
- **`gravity-work-fixer`** (default with `cell`). The cell form keeps momentum and energy consistent, but it does not conserve total energy plus potential energy to round-off. The fixer restores that:
  - In each stage it measures the dynamics' change of E+PE: the gravity work booked into E, `Phi` times the x1 mass divergence, and the implicit block's change. Each stage counts with its weight in the step's update (rk3: 1/6, 1/6, 2/3).
  - After the last stage it does one global reduction and adds `-D` back as heat, uniform per unit mass. A Mesh with several local blocks sums them first. Momentum and mass are untouched.
  - Solid (immersed-boundary) cells are left out of the normalising mass and of the deposit, since their state is refilled each step. Measured with the top 4 cells of a column solid: the fluid E+PE loses 2.19 % of D per step without the mask (the solid mass share), 0 with it.
  - The cycle diagnostics print the fixer energy of the accepted steps as `fixgrav=`, among the run-to-date meters. Like them, it counts from the start of the run and is not carried across a restart. A redone step's −D is discarded with the state and is not counted.
  - It measures the mass that crossed the physical x1 boundary faces in each step and stops the run if that exceeds 1e3 machine epsilons (of the run's dtype) of the mass in the x1 wall cells, because then `D` would also contain a real boundary flux. A sealed wall measures 0.14 eps in both float64 and float32. Any impenetrable wall works, compiled or installed from Python, with or without a name. Open x1 boundaries need `gravity-work-fixer: false`.
  - A periodic x1 boundary is refused: mass that wraps across it jumps by `grav1 Lx1` in the potential (measured: E+PE drift 3.6e-2 in the closed box). The check reads the layout's x1 wrap as well as the boundary name, so it also holds when Python `bfuncs()` has cleared the names.
  - A step that the redo check will discard (limiter repair or NaN) is left to it, as with the fixer off. The check is per step: a leak below the bound is not refused, and its E+PE error is of round-off size.
  - It refuses `grav2` or `grav3` != 0, because its potential is `-grav1 x1`. This is checked when the hydro module is built, so it applies to YAML and Python alike. Both keys are also in the Python API: `ConstGravityOptions.gravity_work()` and `.gravity_work_fixer()`.
  - Sedimentation needs no separate refusal: the settling flux is already sealed at the x1 walls.
- **`face-wallc`**. The face-mass-flux work, with the cell work kept in the two x1 wall cells. With an implicit scheme the wall cells also keep the matrix's cell work, and it prints a warning that points to #283.
- **`face`**. The pre-change form, bitwise: face-mass-flux work in every cell. The existing face-form tests use it, and it also warns under an implicit scheme.

## Why

- Under the implicit solver the face work sat outside the operator, and a tall rest column blew up at acoustic Courant ~66 (#283).
- The cell form is the work that the momentum equation and the implicit matrix already use. The fixer restores the E+PE conservation that the face form had by construction.
- A low-Mach onset check against a linear (EVP) reference is planned as follow-up evidence.

## Migration

- Changed by default: every deck with `forcing/const-gravity` `grav1 != 0` and an energy equation. Its energy now gets the cell-form gravity work plus the fixer, so its numbers move.
- To reproduce pre-#284 numbers exactly, set `gravity-work: face`. It is bitwise identical to main, and the fixer is refused with it.
- A deck whose x1 boundary lets mass through (outflow or inflow), or is periodic, must set `gravity-work-fixer: false`, or choose a face form. The fixer stops the run when mass crosses an x1 boundary, because its defect would then include a real boundary flux.
- Under an implicit scheme, both face forms print a warning that points to #283.

## Numbers change

Every deck with `grav1 != 0` and an energy equation changes by default. Sizes from snapy's own tests:

| check | main (face) | this PR (cell + fixer) |
|---|---|---|
| tall isothermal rest column, implicit, acoustic Courant 65.6, 40 steps (#283 test) | blows up: max\|w\| 8.9e24 m/s | at rest: max\|w\| 5.8e-9 m/s |
| same column, Courant 6.6 | 4.6e-9 m/s | 5.0e-9 m/s |
| moving isentropic column (w0/c = 1e-2, 2 sound crossings), total-entropy drift, nz 64 / 128 | 1.11 / 0.235 | 1.97 / 0.473 |
| same, E+PE drift (relative) | 2.3e-14 / 4.7e-14 | 2.3e-14 / 4.7e-14 |
| closed box, 200 steps: E+PE drift with the fixer off (the defect the fixer removes) | — | 1.9e-6 (fixer on: 1.2e-14) |

The entropy drift of a moving column changes by about 2x and is still first order in w0. The E+PE budget stays at round-off. `face-wallc` gives the face form's numbers away from the x1 walls. Its two wall cells keep the cell work, so its E+PE is not exact: 1.3e-6 in the closed box.

## Tests

| test | parent 068f9f4 | head |
|---|---|---|
| `test_implicit_gravity_tall_column` (#283) | FAIL: large step max\|w\| 8.9e24 m/s (control rung passes) | PASS: 5.8e-9 / 5.0e-9 m/s |
| `test_gravity_work_fixer` (new) | n/a (the keys do not exist) | PASS: E+PE 1.2e-14 explicit, 1.1e-14 implicit (bound 1e-12); float32 runs 200 steps (6.1e-6); fixer off 1.9e-6; outflow x1 (float64, float32) and periodic x1 refused (also on the cubed layout after a Python `bfuncs()` round trip); implicit face-wallc keeps the wall-cell work; a NaN goes to the redo check |
| `test_straka_redo` (new: straka at cfl 1.6 to t = 60 s, fixer on) | — | PASS: steps redone, run completes (with the previous per-step check it aborted on a non-finite step) |
| CPU ctest (`-E test_shallow_xy_decomp`) | 173 passed / 1020 | 176 passed / 1022; no failure that the parent does not have |

Reproduce. The two new tests are ctest scripts, not pytest modules, so `pytest` collects nothing from them:

```
ctest -R "test_implicit_gravity_tall_column|test_gravity_work_fixer" --output-on-failure   # from the build dir
python tests/test_implicit_gravity_tall_column.py    # or run each script directly
python tests/test_gravity_work_fixer.py
```

CPU ctest:
- Both builds register the vendored Eigen/BLAS tests: 834 entries that are not built here or fail identically in both.
- The snapy fail set is identical apart from the #283 test (fails on the parent, passes on the head): 13 multi-process (MPI/UCX/gloo), straka and restart-cycle entries that need resources this CPU node lacks.
- The new test passes.

Not run here: CUDA, and the fixer on a cubed-sphere or multi-rank layout. The reduction uses the same layout communicator as the time-step reduction.

## Limit: tall columns at large implicit steps

The fixer adds its heat outside the implicit operator. In a tall column at a large implicit step, that heat can drive the column:

| case | depth | vertical acoustic Courant (c dt / dx1) | cell + fixer | cell, fixer off |
|---|---|---|---|---|
| #283 isothermal column, at rest and moving, 4000 steps | 11 scale heights | 66 / 148 | stable | stable |
| same, at rest (moving: 197) | | 168 to 657 | unstable | stable |
| `examples/jupiter_gcm_dry` at its own dt, 1000 steps | ~3 scale heights | 247 | stable, no redo | stable |

Shallow columns go further but are not unlimited: a ~3 scale-height column with the fixer is stable at Courant 1000 and needs redos at 3000. So the limit depends on the deck, not on the Courant number alone. A deck deeper than about 10 scale heights that runs at an implicit vertical acoustic Courant above about 150 should check its column. `gravity-work-fixer: false` keeps it stable, at the cost of the E+PE budget. The run is not refused, because a Courant-only rule would also block decks like `jupiter_gcm_dry` that are fine. Far beyond that limit, at an implicit Courant number of a few thousand, the sealed-wall round-off itself reaches the boundary-mass bound (measured: 1370 eps against 1000 at Courant 6000), and the run is refused; `gravity-work-fixer: false` applies there too. A fix that removes the limit is planned as a follow-up.

## Review checklist (for reviewers)

1. CUDA build: ctest, both new tests with `--device cuda`.
2. Layout/decomposition arms (x1 seams, cubed sphere, several ranks): bitwise with the fixer off; one fixer-on arm with E+PE drift <= 1e-11.
3. A rest column over >= 1e4 buoyancy periods: no secular growth of internal energy from the fixer.
4. Restart with the fixer on: bitwise equal to a straight-through run. The fixer keeps no state across steps.
5. The default moves numbers by design. `gravity-work: face` reproduces the pre-change numbers bitwise.
