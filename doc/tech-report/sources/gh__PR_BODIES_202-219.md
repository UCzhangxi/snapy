> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# snapy upstream pull requests #202-#219 (merged), bodies
Fetched 2026-10-09 from the public chengcli/snapy repository (GitHub REST API).

## PR #202: Fix/gravity vic energy conservation

Merged 2026-09-08; merge commit `02c3cdc`.

## Summary

This PR improves gravitational energy conservation in explicit vertical
transport and VIC.

Previously, continuity transported mass using face fluxes, while gravitational
work was calculated from cell-centered velocity. VIC could also redistribute
mass without applying a fully consistent energy correction.

## Changes

- Calculate explicit gravitational work from the same final vertical mass flux
  used by continuity.
- Include dry gas, tracers, precipitation, and sedimentation transport.
- Exclude horizontal mass divergence from vertical gravitational work.
- Preserve the original gravity coupling during the VIC solve, then apply the
  conservative correction afterward.
- Derive the VIC energy correction from the mass redistribution actually
  applied.
- Add regression tests for explicit transport, VIC redistribution,
  multidimensional flow, and prescribed sedimentation.

## Validation

The related C++ test suites pass:

- `test_forcing`
- `test_riemann`
- `test_hydrostatic`
- `test_hydro_ref_x1`
- `test_condensate_conservation`

Additional tests cover multiple Runge–Kutta schemes, Riemann solvers,
non-hydrostatic factors, CFL values, resolutions, and dry/moist states.

## Scope

The conservation guarantee applies primarily to closed vertical boundaries.
Explicit outflow energy accounting is improved, but VIC still uses its existing
closed implicit boundary treatment. Fully implicit VIC outflow support is not
part of this PR.

## PR #203: Fix auto tagging: Use the workflow file from the base branch

Merged 2026-09-15; merge commit `85f2d00`.

(no body)

## PR #204: fix: use total mixture density in VIC

Merged 2026-09-16; merge commit `5b142af`.

## Summary

- keep `CopyPrimitives` density equal to the EOS primitive total mixture density;
- remove the second addition of explicit-species mass into the VIC density;
- add a regression test showing that splitting one species label into two identical labels does not change the reconstructed hydrodynamic state.

## Root cause

For the moist EOS, primitive `IDN` is already total mixture density and the
explicit species entries are mass fractions of that total. The previous loop
therefore assembled

```text
rho_vic = rho_total * (1 + sum(q_explicit))
```

instead of `rho_vic = rho_total`. This changed the VIC flux Jacobian, Roe
averages, and acoustic decomposition according to how the same physical
mixture was labeled.

Git history traces the loop to `2185173` (`Fix GCM decompose (#98)`). It
predates the gravity-energy work merged in #202 and is not introduced by that
patch.

## Validation

- [x] `pre-commit run --all-files` with `clang-format 20.1.4`;
- [x] clean macOS CPU build against current `main`;
- [x] 30/30 tests in `build/tests` passed, including
      `test_backward_substitution.release`;
- [x] isolated numerical A/B: relabeling an otherwise identical gas produced
      a 3.2969 amplification factor before the fix and approximately 1 after;
- [x] corrected local runs completed a 400 s uniform moist box and a 120 s
      full Hycean probe at CFL 0.8; the uncorrected builds failed near 57 s and
      21 s respectively;
- [x] remote CUDA/UCX environment validation run: all selected
      CPU/CUDA native tests passed, followed by a 3600 s coupled Hycean run
      with 1020 accepted steps, zero redo, and finite positive state;
- [x] GitHub pre-commit, Ubuntu, and macOS CI.

The remotely validated source commit (`3e5a7c7`) and this rebased PR commit
(`ab08fbd`) have the same stable patch-id.


## PR #205: Revise outflow bc

Merged 2026-09-18; merge commit `0daab2a`.

(no body)

## PR #206: Fix wall ghost updates after saturation adjustment

Merged 2026-09-22; merge commit `914b43b`.

The final RK stage fills physical ghost cells before saturation changes the interior species densities. On the next stage, the stale ghosts create a thermodynamic jump at reflecting walls and leak energy and water.

Move the existing boundary fill after saturation adjustment. This ports an earlier ordering fix from `a47faae` to the boundary API on main #205, without the other changes in that commit.

The regression uses a closed 32-cell moist column, with condensation and evaporation at each wall. It checks that phase change occurs and that relative energy and total-water errors stay below `1e-12`. Both hardware sets land at ~1e-14 after the fix — roughly two orders below that threshold, at the roundoff floor — while the before-values sit six to seven orders above it.

Float64 measurements, `0daab2a` → `6d912a6` (maximum over lower/upper walls), original run, RTX 5090:

| Device / case       | Energy before | Energy after | Water before | Water after |
| ------------------- | ------------- | ------------ | ------------ | ----------- |
| CPU / condensation  | 6.99e-6       | 1.09e-14     | 1.19e-5      | 1.19e-14    |
| CPU / evaporation   | 6.35e-6       | 1.21e-14     | 5.41e-6      | 9.33e-15    |
| CUDA / condensation | 6.99e-6       | 1.12e-14     | 1.19e-5      | 1.21e-14    |
| CUDA / evaporation  | 6.35e-6       | 1.19e-14     | 5.41e-6      | 9.55e-15    |

Independent reproduction, same `0daab2a` → `6d912a6` comparison (baseline = `0daab2a` + test files only, `meshblock.cpp` untouched), AWS p5.48xlarge (H100, GPU 0):

| Device / case       | Energy before | Energy after | Water before | Water after |
| ------------------- | ------------- | ------------ | ------------ | ----------- |
| CPU / condensation  | 6.99e-6       | 1.08e-14     | 1.19e-5      | 1.08e-14    |
| CPU / evaporation   | 6.35e-6       | 1.21e-14     | 5.41e-6      | 8.88e-15    |
| CUDA / condensation | 6.99e-6       | 1.10e-14     | 1.19e-5      | 1.10e-14    |
| CUDA / evaporation  | 6.35e-6       | 1.19e-14     | 5.41e-6      | 9.55e-15    |

(Per-wall values are identical to ~11 digits on the baseline; table shows the max as in the original.)

Wall-saturation, radiating-boundary, condensate-conservation and moist-diffusion tests pass on CPU and CUDA: 35 tests, no skips (`test_wall_saturation` 2 + `test_radiating_boundary` 21 + `test_condensate_conservation` 4 + `test_diffusion_moist` 8). 2-rank `test_exchange` was green on both trees (CPU); those configs are dry ideal-gas with no reactions, so they do not exercise the saturation path.

```sh
ctest --test-dir build --output-on-failure -R '^test_wall_saturation[.]release$'
```


## PR #211: tests/build: python ctests import the built snapy; reject unknown dynamics keys; keep Find* header roots

Merged 2026-09-24; merge commit `c4236e0`.

## Summary

- **tests: python ctests import the snapy they were built with.** The `*_python` ctests imported whatever snapy was installed, so a stale install gave a false red and a broken branch a false green. They are now registered through `snapy_add_python_test()`, and a new cache variable, `SNAPY_TEST_PYTHONPATH`, is prepended to their `PYTHONPATH`. Configure warns when it is unset.
- **tests: prepend `SNAPY_TEST_PYTHONPATH` instead of replacing `PYTHONPATH`** (upstream maintainer, from review). Replacing it dropped the caller's `PYTHONPATH` and any environment a test set for itself, so a caller-selected kintera silently gave way to site-packages. It now goes through `ENVIRONMENT_MODIFICATION path_list_prepend` (CMake >= 3.22), with an `APPEND` fallback for older CMake. A new test, `test_python_import_path_python`, checks the wiring.
- **hydro: reject unknown dynamics keys.** A typo, or an option no code reads, under `dynamics:` was silently ignored. Any top-level key outside the seven that are read now fails at load, and the error names the key (the test checks this since the upstream maintainer's review commit).
- **build: keep the Kintera/Harp/Disort header roots across reconfigures.** Each Find module unset its header cache entry on every configure. So a reconfigure under a different `PYTHONPATH` moved the include root while `<PKG>_LIBRARY` kept its old value: the build compiled against one copy and linked another. The three `unset()` lines are dropped, and `docs/installation.rst` says to use a fresh build directory (or `--fresh`) after switching Python environments.

## Commits

| Commit | Author | Subject |
|---|---|---|
| `4e5cff7` | contributor | tests: python ctests import the snapy they were built with (+ radiating-boundary enrolment) |
| `8ddc943` | contributor | hydro: reject unknown dynamics keys |
| `bd67b1e` | contributor | build: keep the Kintera/Harp/Disort header roots across reconfigures |
| `6dcb917` | upstream maintainer | tests: prepend SNAPY_TEST_PYTHONPATH instead of replacing PYTHONPATH |
| `aafcf8a` | upstream maintainer | tests: hydro_options checks the error names dynamics/positivity |

## Tests

| Gate | Result |
|---|---|
| `test_radiating_boundary.release` | pass |
| `test_radiating_boundary_python` (`PYTHONPATH` starts with the build's own install, shown by `ctest -N -V`) | pass |
| `test_wall_saturation.release` | pass |
| `test_hydro_options.release` (new) | fails on main (bad key does not throw), passes here. Mutation check (upstream maintainer): with the error message changed to omit the key, it fails |
| `test_python_import_path_python` (new) | see below |

`test_python_import_path_python`, run locally with CMake 3.22 and 3.31.6:

| Configuration | Result |
|---|---|
| replace code of `bd67b1e` + the new test | fails: "caller PYTHONPATH entry ... was dropped", other 4 `*_python` pass |
| this branch, `SNAPY_TEST_PYTHONPATH` set | 5/5 `*_python` pass |
| this branch, `SNAPY_TEST_PYTHONPATH` unset | new test skipped (exit 125), other 4 pass |

Configure twice, same build tree: the first configure imports kintera from one install, the second from another. The check reads the kintera `-isystem` root in `build/src/CMakeFiles/snap_release.dir/flags.make`.

| Tree | Include root | `KINTERA_LIBRARY` |
|---|---|---|
| base (main) | moves to the second install | stays on the first: skewed |
| this branch | stable | stable |

Review measurement (upstream maintainer): on main, the second configure moves the kintera and pyharp include roots in 38 targets' compile flags while the link lines keep the old libraries; on this branch no target moves. Disort's include root is on no compile line.

## CI

Upstream CI at `aafcf8a` (run [36047231682](https://github.com/chengcli/snapy/actions/runs/36047231682), 2026-09-24): all 3 checks passed.

| Job | Result | Time | ctest |
|---|---|---|---|
| pre-commit | pass | 13s | – |
| build-and-test (ubuntu-latest) | pass | 24m42s | 41/41 (test_python_import_path_python skipped) |
| build-and-test (macOS-latest) | pass | 29m46s | 35/35 (test_python_import_path_python skipped) |

CI does not set `SNAPY_TEST_PYTHONPATH`, so the new test skips there by design, and neither the `ENVIRONMENT_MODIFICATION` branch (CMake >= 3.22) nor the older-CMake fallback runs in CI. The prepend was checked locally with CMake 3.22 and 3.31.6: red with the replace code ("caller PYTHONPATH entry ... was dropped"), 5/5 with the patch, skipped when unset. The fallback for CMake < 3.22 was not exercised.

## Behaviour change

Unknown top-level keys under `dynamics:` now fail at load. The accepted keys are `equation-of-state`, `reconstruct`, `riemann-solver`, `verbose`, `disable-flux-x1`, `disable-flux-x2` and `disable-flux-x3`. The interior of `equation-of-state` is not checked, because other libraries read their own keys there. `examples/earth_crm.yaml` drops `dynamics/disable`, which no code reads.

The Find-module change also changes behaviour: reconfiguring an existing build directory no longer follows a changed Python environment. A fresh build directory (or `cmake --fresh`) is unaffected.

## Files

```
M  cmake/modules/FindDisort.cmake
M  cmake/modules/FindHarp.cmake
M  cmake/modules/FindKintera.cmake
M  docs/installation.rst
M  examples/earth_crm.yaml
M  src/hydro/hydro_options.cpp
M  tests/CMakeLists.txt
A  tests/test_hydro_options.cpp
A  tests/test_python_import_path.py
```

## Provenance

Branch @`aafcf8a` on upstream main `914b43b`, 5 commits. Reviewed 3/3 at `aafcf8a` (the upstream owner's reviewing agent, a second independent review agent, an independent review agent); upstream CI green (run 36047231682).

## Limits

- Only the 3 python tests present on main are converted to the new helper: `test_mesh_exchange`, `test_cubed_sphere_vertical_velocity_exchange` and `test_jit_user_forcing`. `test_radiating_boundary_python` keeps its own `add_test()` and is enrolled explicitly. Later PRs register their own tests.
- The `APPEND` fallback for CMake < 3.22 is not exercised, locally or in CI. It also captures the caller's `PYTHONPATH` at configure time, not at test time.
- ctest 3.22.0-rc1 segfaults when it starts a test that has `ENVIRONMENT_MODIFICATION`. It is a bug in that release candidate: the same build directory passes under ctest 3.31.6.
- Disort's header root is not on any compile line today, so its part of the Find-module change has no observable effect yet.
- Deriving the version from `v*` tags only is a separate follow-up PR.



## PR #212: bc, output, recon: rectify_solid outer ghosts; restart schedules by key; PLM 0/0 guard; atomic flip count

Merged 2026-09-25; merge commit `924d2d8`.

## Summary

- **bc**: `rectify_solid` used the inner boundary function for the outer ghosts, so the outer ghost slabs were never marked solid. It now uses the outer function.
- **mesh, output**: restart schedules were restored by position. An output block added after the restart fired off the dt grid, and a block inserted ahead of another took that block's schedule. Now each block claims its saved schedule by a key (file type, dt, variables), and its own slot is tried first. A new block joins the dt grid. File numbers stay positional, so an in-place resume never rewrites finished frames.
- **recon**: the PLM van Leer mean divided 0/0 on round-off-sized slopes, and the NaN spread through the column. The harmonic mean is now taken only where `dwl*dwr > 0`, and the result is 0 elsewhere (`interp_plm` gets the same fix).
- **bc**: the flip count in `flip_zero_cpu` was a plain int accumulated across a parallel region, so updates were lost and rectification could stop early. It is now a relaxed `std::atomic<int>`.

## Tests

The feature-removed tree is this tip with every `src/` change of the branch reverted. The tests are kept.

| gate | feature removed | this branch |
|---|---|---|
| `test_rectify.release` | **fails**: `test_rectify.cpp:113`: "ghost slab along dim 0 is not solid: inner 1 outer 0" | passes |
| `test_restart_new_output` | **fails**: `run_restart_new_output.py:139` AssertionError: "new stream is not co-temporal with the restored one after resume" (out1 42.15, 49.10, ... against out2 47.30, 54.24, ...) | passes |
| `test_restart_insert_output` | **fails**: `run_restart_insert_output.py:73` AssertionError: "streams not co-scheduled after resume: next_time [92.0, 77.0, 75.086]" | passes |
| `test_restart_key_collision` | passes. It is a regression guard: it goes red if the own-slot-first claim is removed (out1 loses its saved cadence: `out1 next_time 77.0 (expected 86.0 from its saved cadence)`; out2 writes an extra frame at the resume time), and the old positional code does neither | passes |
| `test_restart_inplace_reorder` | passes. It is a regression guard against a key-restored counter overwriting completed frames, which positional code cannot do | passes |
| `test_plm.release` | **fails**: `test_plm.cpp:190` `ASSERT_TRUE(isfinite(resultl))` in `interp_plm_round_off_slopes_stay_finite`, float and double | passes |
| `test_flip_zero_count.release` (run 5x) | **fails 5/5**: "flip count 39770 on 8 threads != 43332 serial ... increments were lost" (range 39770 to 40129) | passes 5/5 |

The restart runners launch the solver through `torchrun`. Here they ran through a direct single-rank launcher standing in for `torchrun`, because of the local port clash. As a control, the existing `test_restart_cycle_limit` passes through the same launcher.

## CI

Upstream CI at `f8d7e66` (run [36100257509](https://github.com/chengcli/snapy/actions/runs/36100257509), 2026-09-24): all 3 checks passed.

| Job | Result | Time | ctest |
|---|---|---|---|
| pre-commit | pass | 19s | – |
| build-and-test (ubuntu-latest) | pass | 25m33s | 46/46 (`test_restart_key_collision` 10.67 s) |
| build-and-test (macOS-latest) | pass | 28m46s | 36/36 (the restart tests are not in the macOS set) |

CUDA (upstream CI has no GPU):

- `6c04554`, one H100 (`sm_90`), nvcc 12.5, torch 2.10.0+cu128, kintera `9fa7333` CUDA build (a second independent review agent): `test_rectify`, `test_flip_zero_count`, all six `test_restart_*`, `test_eos`, the four `*_python` exchange/forcing tests, `test_straka`, `test_shallow_xy`, `test_shallow_splash` pass. No test skipped for lack of CUDA. The last three were each run in a clean directory; see Limits.
- `f8d7e66`, RTX 5090, CUDA Release build (the upstream owner's reviewing agent): `tests/run_restart_key_collision.py` passes (`ok: resume at 40.086; saved file_number [2, 6, 4]`, final next_time `[92, 86, 77]`). The same file also passed on the H100 build of `6c04554`.

## Review

AI review; each line is the reviewer's verbatim sign-off, times 2026-09-24 PT.

| Reviewer | Sign-off | Time |
|---|---|---|
| the second independent review agent | `SIGN-OFF #212 @ daa6c22: approve` | 12:14 |
| an independent review agent | `SIGN-OFF #212 @ daa6c22: approve` | 12:16 |
| the upstream owner's reviewing agent | `SIGN-OFF #212 @ daa6c22: approve` | 13:01 |
| the second independent review agent | `SIGN-OFF #212 @ 6c04554: approve` (pure-rebase re-sign: range-diff 4/4 `=`, CI green) | 15:31 |
| the second independent review agent | `SIGN-OFF #212 @ f8d7e66: approve` (H100 CUDA run of the test file, plus a read) | 23:20 |
| the independent review agent | `SIGN-OFF #212 @ f8d7e66: approve` (read, plus CI) | 23:21 |
| the upstream owner's reviewing agent | `SIGN-OFF #212 @ f8d7e66: approve` (RTX 5090 CUDA run, plus a read) | 23:22 |

`f8d7e66` adds one test-only commit found in review: a mutation run showed that `test_restart_key_collision` still passed with the own-slot-first claim removed, although the schedules were wrong. The added cadence check (the independent review agent) closes that gap; it was reproduced red/green by the second independent review agent (H100) and the upstream owner's reviewing agent (RTX 5090).

## Provenance

- Branch @`f8d7e66f86bbf5274526aec960967e398170d01d`, on upstream main `c4236e0` (#211). It needs no other PR. `f8d7e66` is `6c04554` plus one commit touching only `tests/run_restart_key_collision.py` (+22/−1). `6c04554` is a pure rebase of `daa6c22` (on `914b43b`): `git range-diff` shows all 4 commits `=`.
- The gates ran at an earlier tip of the same four commits (`590e293`); the rebase onto main changes no line of them (range-diff all `=`).
- Dev-gated on Linux CPU, torch 2.6, red to green as above. The multi-rank test was launched without torchrun because of a local port clash; here that means the restart runners, which are single-rank.

## Limits

- **CUDA.** Covered by the runs above. The CUDA flip counter already uses `atomicAdd` and is unchanged.
- **Restart runners across ranks.** In a gate copy (not committed) with `blocks_per_process = 1` and `--nproc-per-node=2`, all four restart runners pass on `f8d7e66`, and on `f8d7e66` with #213 (`f23d5db`) merged, on CPU and on one H100 (the second independent review agent). key-collision prints `saved file_number [2, 6, 4]`. new-output and insert-output print `next_time [92.0, 77.0, 77.0]`. inplace-reorder prints `saved file_number [2, 6, 3]`. Each runner prints the same line on all four arms. The committed runners still launch one process.
- **Two restart tests do not go red on the old code.** `test_restart_key_collision` and `test_restart_inplace_reorder` pass on the feature-removed tree, because they guard the new key rule, not the old defect. Mutation runs show what they guard:
  The key-collision test now goes red when the own-slot-first preclaim is removed: out1 loses its saved cadence and out2 writes an extra resume-time frame.
  The combined preclaim-removal plus key-based-counter mutant also goes red; key-based counter restoration alone remains guarded by the in-place-reorder test.
  Unmutated 6c04554 passes, so schedule ownership and positional file-number continuity are now independently covered.
- **The `out2_resumed` check assumes the resume leg overwrites frame `saved[2]`.** If a future case ends before out2's next write, the base-leg copy of that frame can sit at or before `resume_t` and fail on correct code. Comparing against `before` would guard against that.
- **Follow-ups (non-blocking, from review).** Loosen the 1e-6 time tolerance on the extra-frame check (and the older one) to about 1e-3, since netCDF stores time as float32; step each stream by its own interval instead of `edited["dt"]`; add a guard that the two saved next_times differ, so the comparison cannot pass trivially. None fires in this case: the extra frame a missing claim writes is stored 6.9e-7 below the resume time, inside the check.
- **Follow-up: `schedule_key` precision (Copilot review, `src/output/output_type.cpp:15`).** The key is built from `std::to_string(dt)`, which keeps six decimals, so two cadences that differ below 1e-6 (e.g. `1.0000001` and `1.0000002`) share a key, and on restart one block could take the other's `next_time`. The schedules this PR tests differ by O(1), so nothing covered here is affected. Fix in a follow-up: hash the exact bits of `dt`, or format it with `max_digits10`.
- **Follow-up: restart runners without `torchrun`.** The four `run_restart_*.py` runners fail instead of returning the ctest skip code when `torchrun` is missing.
- **Examples in a shared test directory.** On the GPU box `test_straka`, `test_shallow_xy` and `test_shallow_splash` first failed because `pd-combine` globs every leftover `*.out*.nc` in `build/tests`; each passes in a clean directory. This is test isolation, independent of this PR (the same tests pass in CI).

## Files

```
M	src/bc/bc_dispatch.cpp
M	src/bc/rectify_solid.cpp
M	src/mesh/meshblock.cpp
M	src/output/output_type.cpp
M	src/output/output_type.hpp
M	src/output/restart.cpp
M	src/recon/interp_simple.hpp
M	src/recon/plm.cpp
M	tests/CMakeLists.txt
A	tests/run_restart_inplace_reorder.py
A	tests/run_restart_insert_output.py
A	tests/run_restart_key_collision.py
A	tests/run_restart_new_output.py
A	tests/test_flip_zero_count.cpp
M	tests/test_plm.cpp
M	tests/test_rectify.cpp
```



## PR #213: output: optional NC_DOUBLE netcdf output; hold every rank until combined files exist

Merged 2026-09-25; merge commit `cc72779`.

## Summary

- **output**: netcdf output was float-only, so an output file could not resolve anything below about 1e-7. A new option, `double_precision: true` on an output block, writes `NC_DOUBLE`; the default stays `NC_FLOAT`. The parallel netcdf writer refuses the option at construction instead of silently writing float. The option is listed by `OutputOptions::report()` and exposed in the Python bindings and `output.pyi` (upstream maintainer).
- **output**: the write path keeps one buffer of the selected type (a second independent review agent, after a review finding by an independent review agent). The default path allocates `float[nbuf]`, the same as main, and casts each computed double to float once, so `+inf` and NaN survive. `double[nbuf]` is used only when `double_precision` is on. NetCDF is not asked to narrow doubles, because it stores the float fill value for an out-of-range value.
- **output**: non-root ranks returned from the collective output call before the root had written the combined netcdf or restart file. There is now a mirror barrier after each root-only combine. It sits in a scope guard, so a throw on the root still releases the other ranks.
- **tests**: new tests check that `double_precision` reads back exactly, that the default is still `NC_FLOAT`, that the YAML key defaults off and is reported, that the default path keeps `+inf` and NaN in the cells where they were planted and the single cast of `1/3` in every other cell (positional asserts (review: the independent review agent; test: the second independent review agent)), and (2 ranks) that every rank sees the complete combined files when `make_outputs` returns. The output tests remove their files with `std::filesystem::remove` instead of `remove_all`, because the `remove_all` exported by the pip `libtorch.so` crashes on a non-empty directory (upstream maintainer).

## Commits

| Commit | Author | Subject |
|---|---|---|
| `7817bdf` | contributor | output: allow NC_DOUBLE netcdf output (double_precision, default off) |
| `ee46a90` | contributor | tests: netcdf double_precision writes NC_DOUBLE that reads back exactly |
| `d084cd1` | contributor | output: hold every rank until the combined output file exists |
| `395311f` | contributor | tests: every rank sees the complete combined files when make_outputs returns |
| `f5bcd05` | upstream maintainer | tests: don't call std::filesystem::remove_all in the output tests |
| `70ff9c7` | upstream maintainer | output: general wording for double_precision comments; expose it in report() and Python |
| `f6fe281` | the second independent review agent | output: write netcdf floats from a float buffer |
| `f23d5db` | the second independent review agent | test: assert netcdf float cells by position |

## Tests

The feature-removed tree is `395311f` with every `src/` change of the branch reverted. The tests are kept. Line numbers refer to `395311f`.

| gate | feature removed | this branch |
|---|---|---|
| `OutputPrecision.netcdf_double_precision_reads_back_exactly` | **fails** at three lines of `test_user_output.cpp`. `:443`: the variable type is 5 (`NC_FLOAT`), not `NC_DOUBLE`. `:453`: the data does not read back equal. `:458`: time reads back 0.3333333432674408 instead of 1/3 | passes |
| `OutputSlice.netcdf_writes_selected_coordinate_and_collapsed_dimension` (asserts the `NC_FLOAT` default) | passes: this is a regression guard, and the default was already float | passes |
| `test_output_barrier.release` (2 ranks, 5 runs) | **fails 5/5** at three lines of `test_output_barrier.cpp`. `:62`: "rank 1 returned before the combine". `:83`: "rank 1 returned before the restart bundle". `:88`: "rank 1: the root was still bundling" | passes 5/5 |
| `OutputPrecision.netcdf_float_output_keeps_nonfinite` (new) | regression guard for the byte-compatible behaviour of `395311f`. It asserts by position: `+inf` in the three planted cells, NaN in the three planted cells, and the single cast of `1/3` in each of the other 66. It fails if narrowing is left to NetCDF (`+inf` becomes the fill value) or if the write is dropped. Positional asserts (review: the independent review agent; test: the second independent review agent) | passes |
| `OutputPrecision.yaml_double_precision_defaults_off_and_is_reported` (new) | – | passes |

**Default-path byte identity** (upstream maintainer): the default `NC_FLOAT` output of `395311f` and `f6fe281` (`f23d5db` changes only `tests/test_user_output.cpp`) was compared byte for byte, from one driver linked against each build (64×32×16 grid, 7 hydro variables; edge inputs include float halfway points, subnormals, overflow to inf, NaN payloads and −0.0).

| file | elements | differing | file bytes differing |
|---|---|---|---|
| edge_prim | 229,604 | 0 | 0 of 972,031 |
| edge_cons | 229,604 | 0 | 0 of 971,643 |
| phys_prim | 229,604 | 0 | 0 of 972,031 |
| phys_cons | 229,604 | 0 | 0 of 971,643 |
| phys_diag | 329,380 | 0 | 0 of 1,412,260 |

The whole files are identical, headers included, and every variable is `NC_FLOAT` on both builds. As a check that the inputs would catch a difference, a truncating narrowing would change 228,048 of the edge values.

**Coordinate rounding** (upstream maintainer, `shallow_splash_mesh6`, against `914b43b`): 18 of 482 horizontal coordinate values move, by at most 1 float ulp (x2 7/144, x2f 3/145, x3 6/96, x3f 2/97). Against a double-precision reference, this branch is correctly rounded on 482/482 values and main on 464/482. Everything else (x1, time, rho, vel1-3, lat, lon, and all 13 `straka_single` variables) is bit-identical.

## CI

Upstream CI at `f23d5db` (run [36064581239](https://github.com/chengcli/snapy/actions/runs/36064581239), 2026-09-24): all 3 checks passed.

| Job | Result | Time | ctest |
|---|---|---|---|
| pre-commit | pass | 16s | – |
| build-and-test (ubuntu-latest) | pass | 21m14s | 42/42 |
| build-and-test (macOS-latest) | pass | 35m9s | 36/36 (test_output_barrier.release took 316.8 s, vs 1.9 s on ubuntu) |

Upstream CI at the previous head `f6fe281` (run [36048576566](https://github.com/chengcli/snapy/actions/runs/36048576566), 2026-09-24): all 3 checks passed.

| Job | Result | Time | ctest |
|---|---|---|---|
| pre-commit | pass | 14s | – |
| build-and-test (ubuntu-latest) | pass | 20m30s | 40/40 |
| build-and-test (macOS-latest) | pass | 34m27s | 34/34 (test_output_barrier.release took 317 s, vs 1.8 s on ubuntu) |

## Review

AI review; each line is the reviewer's verbatim sign-off, times 2026-09-24 PT. The second independent review agent wrote `f6fe281` and `f23d5db`, so the independent sign-offs on the current head are the independent review agent's and the upstream owner's reviewing agent's.

| Reviewer | Sign-off | Time |
|---|---|---|
| the second independent review agent (author of `f6fe281`, `f23d5db`) | `SIGN-OFF #213 @ f23d5db: approve` | 15:33 |
| the independent review agent | `SIGN-OFF #213 @ f23d5db: approve` | 15:34 |
| the upstream owner's reviewing agent | `SIGN-OFF #213 @ f23d5db: approve` | 18:33 |
| the second independent review agent | `SIGN-OFF #213 @ 8e3d1e7: approve (rebase, range-diff 8/8 =, CI green)` (2026-09-25, round 1) | 05:43 |
| the second independent review agent | `fda91fe` (round 2): not signed, because its CI was cancelled | 06:09 |
| the second independent review agent | `SIGN-OFF #213 @ 9d39b57: approve (rebase, range-diff 8/8 =, CI green)` (2026-09-25, round 3, final head) | 06:46 |

## Provenance

- Branch tip `9d39b57` on upstream main `f8b7a78` (#214), 8 commits. It needs no other PR. It is `f23d5db` (on `914b43b`) rebased three times, after #212, #215 and #214 merged; each `git range-diff` was 8/8 `=`. The commit table above lists the pre-rebase SHAs.
- Reviewed at `f6fe281` by the upstream owner's reviewing agent and the second independent review agent; all three signed `f23d5db` (Review below).
- Upstream CI at `9d39b57` (run [36139244830](https://github.com/chengcli/snapy/actions/runs/36139244830), 2026-09-25): pre-commit 16s, build-and-test ubuntu-latest 25m29s, macOS-latest 35m29s, all passed.
- The original four commits were dev-gated on Linux CPU, torch 2.6, red to green as above. The multi-rank test was launched without torchrun because of a local port clash.

## Limits

- **Coordinate axes shift on the default path.** On the default `NC_FLOAT` path, the cubed-sphere x2/x2f/x3/x3f axes on panels with a non-zero offset now round once instead of twice, so a moved value moves by one float ulp (numbers above). Five shipped examples are affected. Everything else is bit-identical.
- **CUDA gate.** 2x RTX 5090, CUDA Release build (nvcc 13.1), torch 2.10.0+cu128: ctest 41/41 passed at f23d5db, 0 skipped. The three CPU-pinned netcdf output tests were rerun on CUDA in an uncommitted copy. Every assertion holds, and the GPU files match the CPU files exactly (max rel diff 0).
- **pnetcdf double_precision refusal exercised.** A pnetcdf output with `double_precision: true` is refused at construction (src/output/pnetcdf.cpp:54) on CPU and on CUDA with: "PNetcdfOutput: double_precision is not implemented for the parallel-netcdf writer; it would silently write NC_FLOAT. Use type: netcdf for double-precision output." The output directory is unchanged and nothing is written. The write-time check (pnetcdf.cpp:67) also refuses and writes nothing. A float pnetcdf control run writes 6 NC_FLOAT files. On CUDA the error fires before the block moves to the device, so the GPU run adds no device-specific evidence.
- **Output barrier on a CUDA mesh.** test_output_barrier's assertions, unchanged, hold on 2 ranks (torchrun, gloo, rank r on cuda:r, one per GPU, 2 blocks per rank): 6/6 runs pass, the combined .nc and restart files exist before any rank proceeds, and no .part files are left. These CUDA and pnetcdf checks ran from uncommitted copies and are not part of the PR's test suite.
- **CUDA barrier not shown red.** The CUDA barrier variant was not run against a build without the barrier. The only evidence that it fails without the barrier is from CPU.
- **pnetcdf single-rank only.** The pnetcdf refusal was not exercised with multiple ranks.
- **Barrier on the error path untested.** The scope-guard barrier's error path, a throw on the root, is still not exercised by any test.
- **macOS 2-rank tests are slow on the CI runner.** `test_output_barrier.release` took 317.09 s on macOS. `test_exchange.release` takes the same time there on main (317.53 s at `c4236e0`, 317.99 s at `914b43b`), against about 2 s on ubuntu, so the delay is the runner's 2-rank startup, not this PR.
- **The Python binding of `double_precision` was not rebuilt locally.** CI builds the extension.

## Files

```
M	docs/user_guide/output.rst
M	python/csrc/pyoutput.cpp
M	python/snapy/output.pyi
M	src/output/combine_netcdf.cpp
M	src/output/combine_restart.cpp
M	src/output/netcdf.cpp
M	src/output/output_type.cpp
M	src/output/output_type.hpp
M	src/output/pnetcdf.cpp
M	tests/CMakeLists.txt
A	tests/test_output_barrier.cpp
M	tests/test_user_output.cpp
```



## PR #214: build: derive the version from v* tags only

Merged 2026-09-25; merge commit `f8b7a78`.

## Summary

- **build: derive the version from `v*` tags only.** setuptools_scm's default `git describe` matches every tag that contains a digit. This repository carries three such non-version tags (`prod-2026-07-14`, `s2-cubed-fix-2026-07-14`, `wb-v1-aba7f1e`), and a clone may add its own. When one of them is the nearest tag, the version is either unparseable, which aborts `pip install`, or silently wrong: `prod-2026-09-24` parses as version `24`. The describe command is now limited to `v*` tags.

## Tests

Version resolution with `python -m setuptools_scm`, using setuptools-scm 8.0.0 (the `>=8` floor in `[build-system]`) and 10.3.4, with git 2.50. "main" is one empty local commit on top of `914b43b`, because `914b43b` itself carries `v2.10.9`. "this branch" is `4ab0549`. Each tag was a local lightweight tag on the tip, deleted after its check.

| Tag on the tip | main, 8.0.0 | main, 10.3.4 | this branch, 8.0.0 and 10.3.4 |
|---|---|---|---|
| none | `2.10.10.dev1+g…` | `2.10.10.dev1+g…` | `2.10.10.dev1+g4ab0549` |
| `v9.9.9` | `9.9.9` | `9.9.9` | `9.9.9` |
| `wb-v1-aba7f1e2` | `InvalidVersion: 'v1-aba7f1e2'` | `ValueError: Can't parse version from tag` | `2.10.10.dev1+g4ab0549` |
| `prod-2026-09-24` | `24` (wrong, no error) | `24` (wrong, no error) | `2.10.10.dev1+g4ab0549` |

The last two rows are the regression: main fails or returns a wrong version, and this branch resolves. The first two rows show that the branch still resolves ordinary checkouts. There is no ctest for this, because it is packaging metadata.

## Files

```
M  pyproject.toml
```

## CI

Upstream CI at `bcec850` (run [36064870388](https://github.com/chengcli/snapy/actions/runs/36064870388), 2026-09-24): all 3 checks passed.

| Job | Result | Time | ctest |
|---|---|---|---|
| pre-commit | pass | 12s | – |
| build-and-test (ubuntu-latest) | pass | 24m35s | 41/41 |
| build-and-test (macOS-latest) | pass | 27m6s | 35/35 |

## Review

AI review; each line is the reviewer's verbatim sign-off, times 2026-09-24 PT.

| Reviewer | Sign-off | Time |
|---|---|---|
| an independent review agent | `SIGN-OFF #214 @ bcec850: approve` | 15:03 |
| a second independent review agent | `SIGN-OFF #214 @ bcec850: approve` | 15:31 |
| the upstream owner's reviewing agent | `SIGN-OFF #214 @ bcec850: approve` | 18:33 |
| the second independent review agent | `SIGN-OFF #214 @ c32c66a: approve (rebase, range-diff 1/1 =, CI green)` (2026-09-25; `bcec850` → `0ee5582` → `c32c66a`, two pure rebases onto main after #212 and #215) | 06:03 |

## Provenance

Branch @`c32c66a` on upstream main `088765b` (#215), rebased 2026-09-25 from `bcec850` (on `c4236e0`) with `git range-diff` 1/1 `=`; CI on `c32c66a` (run [36136753365](https://github.com/chengcli/snapy/actions/runs/36136753365)): all 3 checks passed. `bcec850` is a pure rebase of `4ab0549`, where the table above was measured. It needs no other PR. The second independent review agent reproduced every row on `bcec850` (and the main column on `c4236e0`) with setuptools-scm 8.0.0 and 10.3.4; the only change is the suffix: `bcec850` is two commits past `v2.10.9`, so it resolves to `2.10.10.dev2+gbcec850` where `4ab0549` gave `2.10.10.dev1+g4ab0549`.

## Limits

- setuptools-scm 10.3.4 prints `DeprecationWarning: Configuration field 'git_describe_command' is deprecated. Use 'scm.git.describe_command' instead.` The newer form is not used because setuptools-scm 8.0.0, which the `>=8` floor still admits, rejects it (`TypeError: Configuration.__init__() got an unexpected keyword argument 'scm'`). The key can move once the floor is raised.
- Only the `git describe` path is covered. Versions from an sdist or a git archive (no `.git`) are unaffected by this change and were not exercised.



## PR #215: Outflow/radiating BC: use conserved dry density u[IDN] (fixes #205)

Merged 2026-09-25; merge commit `088765b`.

# outflow/radiating bc: use conserved dry density u[IDN] for tracers (fixes #205)

## Summary

The stepper gets tracer mixing ratios from `scalar_r = scalar_s / u[IDN]`. For `ideal-moist` and `moist-mixture`, `u[IDN]` is the **dry** density `(1 − Σq)·w[IDN]`. The outflow/radiating boundary path in `MeshBlockImpl` (and tracer seeding in `finalize_initialization`) used the total density `w[IDN]` instead. As a result, moist tracers were off by a factor of 1/(1−q) at init and in the ghost cells. This PR switches all three sites to the conserved dry density `u[IDN]`. For ideal gas, `u[IDN] == w[IDN]`, so ideal-gas runs are unchanged.

| # | Location | Before | After |
|---|---|---|---|
| 1 | `apply_boundaries`, conserved radiating path | `r = tracers / w[IDN]` | `r = tracers / hydro[IDN]` |
| 2 | `apply_boundaries`, `flush` lambda | `s = r * w[IDN]` | `s = r * u[IDN]` |
| 3 | `finalize_initialization`, tracer seeding | `scalar_s = w[IDN] * scalar_r` | `scalar_s = u[IDN] * scalar_r` |

- Head `fb1517b0c2004fea1e4728ebb2df74ab20f6ffaa`, tree `38459cb1796c117393e86a3c74e007f08e98a4fd`, parent `f2f6d774e98c52319a313ff077794a32e0322e9a` (tree `4c76f07`), whose parent is `c4236e0` (origin/main, #211)
- `fb1517b` is a clang-format 20.1.4 rewrap of the `bfuncs()` list on top of `f2f6d77` (`tests/test_radiating_boundary.cpp` +4/−6, `meshblock.cpp` unchanged, whitespace-stripped test file hash identical); the test numbers below were measured at `f2f6d77`.
- Diff stat (measured at `fb1517b`, `git diff --stat c4236e0 fb1517b`):
  - `src/mesh/meshblock.cpp` +6/−3
  - `tests/test_radiating_boundary.cpp` +81/−3 (fixes 3 assertions, adds `conserved_tracers_ride_dry_density` and `moist_tracers_are_per_dry_air`)
  - total: 2 files, +87/−6

```
 src/mesh/meshblock.cpp            |  9 +++--
 tests/test_radiating_boundary.cpp | 84 +++++++++++++++++++++++++++++++++++++--
 2 files changed, 87 insertions(+), 6 deletions(-)
```

## Tests

CPU build: Release, `CUDA=OFF` (project default), `NETCDF=ON`, `BUILD_TESTS=ON`, GPUs hidden. The 7 CUDA-parameterized cases in `test_radiating_boundary` are skipped on CPU.

| Tree | `test_radiating_boundary.release` (gtest) | Full `ctest -j 1` |
|---|---|---|
| (a) c4236e0 (before) | 21 run: 14 passed, 0 failed, 7 skipped (CUDA) — 2.57 s | 41/41 passed, 1 skipped (`test_python_import_path_python`) — 130.2 s |
| (b) c4236e0 + new test file only | 23 run: 14 passed, **2 failed**, 7 skipped — 2.62 s | — |
| (c) f2f6d77 (after) | 23 run: 16 passed, 0 failed, 7 skipped — 2.65 s | 41/41 passed, 1 skipped — 165.6 s |

Wall times were measured on a shared host (load average about 16). The ctest runtime difference is noise; the radiating-boundary test runtime is unchanged (2.57 s vs 2.65 s).

Failures in (b), which are the bug caught by the new tests:

- `conserved_tracers_ride_dry_density`: max |s/u[IDN] − r| = 2.222e-02 for both `ideal-moist` and `moist-mixture`. After the fix it passes at 1e-12 tolerance.
- `moist_tracers_are_per_dry_air`: the errors match the analytic values (init/outflow 0.5·q/(1−q), inflow 0.3·q/(1−q)), identical for both EOSes. After the fix every entry is below 1e-12.

| q | init | inflow | outflow |
|---|---|---|---|
| 0.001 | 5.005e-04 | 3.003e-04 | 5.005e-04 |
| 0.01 | 5.051e-03 | 3.030e-03 | 5.051e-03 |
| 0.05 | 2.632e-02 | 1.579e-02 | 2.632e-02 |

## Sign-off

Reviewer 1: SIGN-OFF #215 @ fb1517b0c2004fea1e4728ebb2df74ab20f6ffaa: approve
Reviewer 2: SIGN-OFF #215 @ fb1517b0c2004fea1e4728ebb2df74ab20f6ffaa: approve
Reviewer 3 (upstream maintainer): SIGN-OFF #215 @ fb1517b0c2004fea1e4728ebb2df74ab20f6ffaa: approve

Sign-offs were given in the review discussion.


## PR #216: diffusion, sedimentation: one-sided wall coefficients, dynamic coefficients, one Stokes formula; strict diffusion inputs

Merged 2026-09-25; merge commit `14f926f`.

## Summary

- **diffusion: a wall face coefficient must not be built from a boundary ghost.** At a reflecting x1 wall the face coefficient was averaged with the ghost, which mirrors the first active cell. That is a first-order error, and on a linear profile it gives the wall cell half the interior tendency. The wall coefficient is now extrapolated one-sided from the two nearest active cells. The change covers x1 walls only, keyed on a new `is_wall_boundary` that reads the boundary name now kept beside each boundary function (`set_bfunc` takes an optional `name`).
- **forcing: diffusion as dynamic coefficients.** `forcing/diffusion` could only express kinematic `nu_iso`/`kappa_iso` times the density, so a problem posed at constant dynamic coefficients (mu, k) could not be run as specified. `dynamic: true` now reads them as mu and k, with no face density and a time-step bound of mu/rho_min. The coefficients stay uniform: `dynamic` is the only new option, in YAML and Python.
- **sedimentation: one Stokes formula on every path, sealed only at physical walls.** The Stokes mean free path used k_B² where k_B·T belongs (fused CPU/CUDA kernel and MPS path), so the slip correction was absent; the MPS path added `const-vsed` where the other paths replace with it; and the settling flux was sealed at every block edge rather than at physical walls, so condensate could not cross an internal x1 seam.
- **diffusion: fixed_temperature is a wall; a non-finite diffusivity throws.** The wall whitelist missed non-reflecting physical walls, and a NaN diffusivity silently dropped the diffusion time-step bound. `is_physical_boundary` and `is_wall_boundary` now share one guarded face lookup.
- **riemann: aneos LMARS writes clr[IRT] instead of rebinding clr.** The solver rebound a registered buffer.
- **implicit: reject an unsupported implicit-scheme at construction.** A scheme outside {0, 1, 9} was accepted.
- **hydro: refuse nb1 > 1 with more than one block per process.** Both x1 relays use a block rank as a process rank; the configuration is now refused at setup rather than patched.
- **tests: dynamic diffusion coefficients carry no density.** This is the test for the second commit (`dynamic`).
- **diffusion: a NaN kappa_iso is no longer masked by a finite nu_iso.** `max_time_step` checked only `std::max(nu, kappa)`, which returns the finite `nu` when `kappa` is NaN, and a zero `nu` returned before the check. So a NaN conductivity ran silently in both modes, and since `kappa_iso > 0` is false for NaN it also dropped the conduction. Each coefficient is now checked on its own, before the combined bound (review: an independent review agent).
- **diffusion: reject malformed dynamic, nu_iso and kappa_iso values and a non-positive time-step bound** (found in review by the upstream owner's reviewing agent; patch by a second independent review agent). `dynamic` was read with `as<bool>(false)`, so a malformed value silently became false; it now accepts only `true` or `false`. `nu_iso` and `kappa_iso` must be finite numbers >= 0 (0 stays valid). A non-positive or non-finite diffusion time-step bound, for example from a negative density, now throws instead of reaching `Hydro::max_time_step`. Three new cases in `tests/test_diffusion.cpp` cover it.

## Tests

The red tree is the branch tip with the feature source reverted and every test kept. `src/forcing/diffusion.cpp` returns to the base version. The other source files of the five fix commits (sedimentation through hydro) return to their state before those commits. Headers stay as on the branch, so the tests compile.

| Gate | Red (feature source reverted) | Green (branch) |
|---|---|---|
| `test_diffusion.release` | `wall_face_coefficient_reads_no_ghost` fails at `test_diffusion.cpp:228`; `wall_flux_does_not_depend_on_the_ghost_density` at `:387`; `wall_names_are_an_exact_whitelist` at `:326` (`is_wall_boundary` on a Dirichlet wall name; a string-classification test, see Limits); `timestep_rejects_a_non_finite_diffusivity` at `:408`; `dynamic_coefficients_carry_no_density` at `:442`, `:445` (tendencies) and `:453` (time step). `timestep_rejects_each_non_finite_coefficient` (new; review: the independent review agent) is red on `ae2d349`, the commit before its fix: 4 of its 5 cases do not throw (kappa NaN with nu 0.5 and with nu 0, each with dynamic false and true), in Float and Double; the fifth (nu NaN, dynamic true) already threw, and `timestep_rejects_a_non_finite_diffusivity` passes there | 27 pass |
| `test_forcing.release` | `fused_sedimentation_matches_tensor_path` fails at `test_forcing.cpp:637`; `sedimentation_is_sealed_only_at_physical_walls` at `:660`; the other 18 pass | 20 pass |
| `test_hydro_options.release` | `reject_unsupported_implicit_scheme` fails at `test_hydro_options.cpp:79` (scheme 3 accepted); `reject_unknown_dynamics_keys` passes | 2 pass |

Two tests hold on the red tree by design, because they pin the scope of the wall fix: `x2_wall_is_not_one_sided` and `periodic_x1_face_is_not_extrapolated`. The CUDA cases of `test_diffusion` are skipped on this CPU build.

The full build (`-k`) compiles every target except `test_eos`, which also fails on the base: a glibc `major` macro clash on the build host.

## Compatibility

- There are no removed or renamed YAML keys. `dynamic` defaults to false, which leaves the kinematic path unchanged.
- Numeric scope. With `dynamic: false` (the default) results are unchanged except in four places, which do change: x1-wall kinematic diffusion (the wall face coefficient); the aneos LMARS solver; the Stokes branch, i.e. sedimentation without `const-vsed` (dormant in shipped cards: every example card sets a non-zero `const-vsed` for each settling species); and multi-block x1 sedimentation (the flux now crosses internal seams).
- The following now fail at setup instead of running:
  - an `implicit-scheme` outside {0, 1, 9};
  - a non-finite diffusivity (at the first time step);
  - `nb1 > 1` combined with more than one block per process (documented in `docs/user_guide/mixed_parallel_strategy.rst`).
- Python: `set_bfunc` gains an optional `name`. Setting `bfuncs` in bulk clears the stored boundary names.
- **Left out:** per-cell x1 profiles of the kinematic coefficients (`nu_scale_x1`, `kappa_scale_x1`). They had no YAML form and no test, so they were dropped from this PR, C++ and Python binding alike.

## Provenance

- Branch tip `1037fc9` (tree `b9ccc1d`) on upstream main `a1a08bd` (#218), 10 commits. It needs no other PR. It is `3f0f6f8` (on `cc72779`) rebased over #217 and #218. The one conflict was in `tests/test_hydro_options.cpp`: #217 and this PR each add a TEST after `reject_unknown_dynamics_keys`, and both are kept (`reject_removed_and_unknown_forcing_keys` first, then `reject_unsupported_implicit_scheme`), nothing else changed; `git range-diff` against `3f0f6f8` is 9 `=` and 1 `!`, the `!` being only that hunk's position. Four independent rebases reached the same tree `547258b` on `572a256` (the PR author, the second independent review agent, the independent review agent, the upstream owner's reviewing agent), where `test_hydro_options` passes 3/3 (CPU Release, the second independent review agent); the final rebase from there onto `a1a08bd` is 10/10 `=`. Before that: tip `3f0f6f8` on `cc72779` (#213), 10 commits, which is `84de0c6` (on `c4236e0`, tree `e59fcf0e`, where the sign-offs below were given) rebased onto the new main with `git range-diff` 10/10 `=`. `84de0c6` is `264e5c5` plus the review fix above. `ae2d349`'s tree is identical to the previous single-fix-commit tip `d9d9c31` (`git diff --quiet` exits 0): the fixes were split into five commits, one per concern, with no code change.
- Dev-gated on Linux CPU, torch 2.6, red→green as above. Upstream CI numbers will be added after the draft PR opens.

## Limits

Paths no test reaches (every other change is reached by a gtest listed under Tests):

- The two MPS-only formula changes in `sed_hydro_dispatch.cpp` (the k_B·T mean free path and `const-vsed` replacing, not adding to, the Stokes velocity). `fused_sedimentation_matches_tensor_path` checks the fused CPU kernel against the tensor path; no test runs the MPS path.
- The aneos LMARS `clr[IRT]` fix. No test or example card uses aneos with LMARS.
- Both x1 `blocks_per_process` guards (`hydro.cpp`, the x1 reference relay; `hydro_forward.cpp`, the x1 seam exchange). No test runs `nb1 > 1` with more than one block per process, so neither refusal is exercised.

Also:

- Reachability of the kappa_iso fix: a YAML NaN is already rejected at parse (`kappa_iso >= 0` fails), so it is reached only from options set in code (C++, or the Python binding `DiffusionOptions.kappa_iso`); there a NaN kappa also silently dropped the conduction, since `kappa_iso() > 0.` is false for NaN.
- `wall_names_are_an_exact_whitelist` is a string-classification test: it sets boundary names by hand. No `fixed_temperature_*` boundary function is registered in this tree, so the new whitelist entry changes no result today, and the size of its effect on a Dirichlet temperature wall is not measured.
- Diffusion coefficients are uniform in space: there is no x1 profile, and `dynamic` is the only new diffusion option.
- **CUDA.** At `264e5c5` (the upstream owner's reviewing agent, sm_75 build run on an RTX 5090 through PTX JIT): `ctest -j1` 42/42, no CUDA skips, and the Stokes fix checked on the device (green: fused = tensor = −7.1129053601e-06, relative difference 2.4e-16; red, fix reverted: fused −2.3253109607e-06, relative error 0.673). On the review-fixed tree (`e59fcf0e`), `test_diffusion` passes 52/52 including the CUDA Float and Double cases, on an RTX 4000 (the upstream owner's reviewing agent) and on an H100 (the second independent review agent). The MPS path was not run.
- No full ctest was run on this branch.
- **Python setters bypass the new checks.** The strict checks run only in `DiffusionOptionsImpl::from_yaml`. The Python properties `nu_iso`, `kappa_iso` and `dynamic` write the member directly (`python/csrc/pyforcing.cpp`, `ADD_OPTION`), so a caller can set a negative number or a non-bool. No shipped YAML card or example sets these properties; every card goes through `from_yaml`, which checks.

## Review

AI review; each line is the reviewer's verbatim sign-off, times 2026-09-25 PT.

| Reviewer | Sign-off | Time |
|---|---|---|
| the upstream owner's reviewing agent | CUDA gate at `264e5c5`: 42/42, Stokes fix red/green on device (review, before the fix) | 01:39 |
| the independent review agent | `SIGN-OFF PR 4 @ 84de0c6 (tree e59fcf0e): approve (read)` | 04:06 |
| the second independent review agent (author of the review fix) | `SIGN-OFF PR 4 @ 84de0c6 (tree e59fcf0e): approve (author)` | 04:14 |
| the upstream owner's reviewing agent | `SIGN-OFF PR 4 @ 264e5c5+staged pr4_v3 (tree e59fcf0e): approve (tree matches; test_diffusion 52/52 CPU+CUDA, Release)` | 04:41 |
| the second independent review agent | `SIGN-OFF #216 @ 3f0f6f8: approve (rebase)` (range-diff 10/10 `=`, CI green; author of the last commit, so a rebase check only) | 09:09 |
| the upstream owner's reviewing agent | `SIGN-OFF #216 @ 3f0f6f8: approve (rebase, range-diff 10/10 =, CI green)` | 09:14 |
| the second independent review agent (author of the last commit, so a rebase check only) | `SIGN-OFF #216 @ 1037fc9 (tree b9ccc1d): approve (rebase, range-diff 9 = + 1 ! keep-both test_hydro_options, CI green)` | 11:55 |
| the independent review agent | `SIGN-OFF #216 @ 1037fc9 (tree b9ccc1d): approve (rebase, range-diff 9 = + 1 ! keep-both test_hydro_options, CI green)` | 12:10 |
| the upstream owner's reviewing agent | `SIGN-OFF #216 @ 1037fc9 (tree b9ccc1d): approve (rebase, range-diff 9 = + 1 ! keep-both test_hydro_options, CI green)` (also replayed the rebase: beyond the conflict markers the only edit is the closing brace and blank line between the two tests) | 12:12 |

The first four sign-offs are on tree `e59fcf0e` (`84de0c6`, on `c4236e0`); the next two re-sign the rebased tip `3f0f6f8`; the rest re-sign the conflict-resolved tip `1037fc9` (tree `b9ccc1d`, on `a1a08bd`). Upstream CI at `3f0f6f8` (run [36155134472](https://github.com/chengcli/snapy/actions/runs/36155134472)) and at `1037fc9` (run [36171780906](https://github.com/chengcli/snapy/actions/runs/36171780906)): pre-commit, ubuntu-latest and macOS-latest all passed.

## Files

```
M  docs/api/forcing.rst
M  docs/api/mesh.rst
M  docs/user_guide/configuration.rst
M  docs/user_guide/mixed_parallel_strategy.rst
M  python/csrc/pyforcing.cpp
M  python/csrc/pymesh.cpp
M  python/snapy/forcing.pyi
M  python/snapy/mesh.pyi
M  src/forcing/diffusion.cpp
M  src/forcing/forcing.hpp
M  src/hydro/hydro.cpp
M  src/hydro/hydro_forward.cpp
M  src/implicit/implicit_hydro.cpp
M  src/mesh/meshblock.hpp
M  src/mesh/meshblock_options.cpp
M  src/riemann/lmars.cpp
M  src/sedimentation/sed_hydro.cpp
M  src/sedimentation/sed_hydro_dispatch.cpp
M  src/sedimentation/sed_hydro_impl.h
M  tests/test_diffusion.cpp
A  tests/test_diffusion_2d.yaml
M  tests/test_forcing.cpp
M  tests/test_hydro_options.cpp
A  tests/test_stokes_sedimentation.yaml
```



## PR #217: forcing, sedimentation, mesh: remove double-counting fric-heat (card-breaking); sedimentation guards; true logged ke; limiter meters

Merged 2026-09-25; merge commit `572a256`.

**Card-breaking.** `forcing/fric-heat` is removed. A card that sets it, including `fric-heat: false`, now fails at load with "'forcing/fric-heat' has been removed ... Delete it." Any key under `forcing:` other than the twelve that are read (`const-gravity`, `coriolis`, `diffusion`, `body-heat`, `top-cool`, `bot-heat`, `relax-bot-comp`, `relax-bot-temp`, `relax-bot-velo`, `top-sponge-lyr`, `bot-sponge-lyr`, `plume-forcing`) now also fails at load. Misspellings such as `fric_heat` get the generic unknown-key error. A `sedimentation:` block without `forcing/const-gravity` is refused at setup; it used to segfault. No card in this repository is affected. No shipped `*.yaml` sets `fric-heat` or an unread forcing key, and every shipped card with sedimentation also sets `const-gravity`. The one test card without gravity, `tests/test_gravity_sedimentation.yaml`, gets gravity set in code before the block is built (one new test builds it without, to check the refusal). Downstream cards that set `fric-heat` must delete the key. No replacement key is needed.

**Log output.** `ke=` in the cycle log now reports the true kinetic energy, so its values will differ from runs before this PR. The log line also gains `pe=` and run-to-date fields. Scripts that parse `ke=` or depend on the log line layout need updating. Restart files are unaffected: existing restarts load unchanged.

## Summary

- **forcing, sedimentation, mesh, implicit: frictional heating double-counts #202's face gravity work, and three more.** The four problems and fixes:
  - **fric-heat double count.** #202's x1 face gravity work already carries the sedimentation channel of the mass flux, and `fric-heat` added the same precipitation energy release a second time. It also read an unsealed `vsed`, sliced the wrong species when fewer clouds sediment than exist, and fired at `nx1 == 1`. Removed: the option, its parse and its registration. An unknown-key sweep on `forcing:` makes a card that still sets it fail loudly.
  - **Sedimentation without gravity.** Sedimentation without `const-gravity` dereferenced a null `grav1`. The flux call also sat outside the `disable_flux_x1` guard. Fixed with a `TORCH_CHECK` at setup and the missing guard.
  - **Logged `ke`.** The logged `ke` was a specific kinetic energy, read from a stale `hydro_w`. It is now computed from the conserved state (constituent-summed density, metric-raised momentum), and the log gains `pe=`.
  - **Meters.** Nothing showed whether the VIC availability clamp binds, or how much flux the positivity limiter removes. New run-to-date meters on the cycle line: `vicclamp`, `limcut`, `thetamin`, `thetasevere`. They are diagnostic only.

## Tests

The red tree is the branch tip with the source reverted to the base. There, `fric-heat` is restored, the forcing-key sweep is gone, `ke` is the old one, and the sedimentation guards and meters are absent. Only the new accessor and buffer declarations are kept, so the tests compile, and every test is kept.

| Gate | Red (feature source reverted) | Green (branch) |
|---|---|---|
| `test_cycle_diagnostics.release` (new), the six `ke`/`pe`/marker tests | all 6 fail: `logged_ke_scales_with_density` at `test_cycle_diagnostics.cpp:75`; `logged_ke_reads_the_conserved_state` at `:84`; `meter_group_is_marked_run_to_date` at `:116`; `logged_ke_sums_the_constituents` at `:203`; `logged_ke_raises_the_momentum_with_the_metric` at `:215`; `logged_pe_is_the_column_geopotential` at `:224` (line numbers at `5bb8928`) | 6 pass |
| `test_cycle_diagnostics.release`: `positivity_meters_read_their_hand_computed_values`, `vicclamp_reads_the_clamped_fraction` (new) | – (the meters are new; there is no pre-fix state) | pass, 3/3 runs. A resting 6-cell column settling at `const-vsed` −2 with dt = 1: `thetamin` 0.5, `thetasevere` 5, `limcut` 0.5 and the offered flux 5 × 2 ρ_cloud, on the buffers and on the printed line. A 2-cell implicit column with every constituent's availability driven negative: `vicclamp` = Σy = 0.03 (and < 1e-12 unclamped), with the face transfer checked non-zero |
| `test_sedimentation_guards.release` (new) | red = this branch with only the two guards backed out: `refuses_a_card_without_const_gravity` fails at `test_sedimentation_guards.cpp:45` (card accepted); `is_skipped_when_the_x1_flux_is_off` fails at `:74` (the cloud moves) and `:75` (the second call differs from the first) | 2 pass |
| `test_hydro_options.release` | `reject_removed_and_unknown_forcing_keys` fails at `test_hydro_options.cpp:76` (`fric-heat` accepted) and `:79` (unknown key accepted); `reject_unknown_dynamics_keys` passes (it comes from main, #211, which already checks the message, so this PR no longer changes it) | 2 pass |
| `test_forcing.release` | regression guard, green on base, branch and the guards-reverted tree (18 pass, including `vertical_gravity_work_includes_sedimentation_mass_flux`) | 18 pass |

The full build (`-k`) compiles every target except `test_eos`, which also fails on the base: a glibc `major` macro clash on the build host.

## Compatibility

- Card-breaking, as stated at the top.
- The cycle line changes format. `ke=` now reports a true kinetic energy (its values change), and the line gains `pe=` plus a `run-to-date:` group with `limcut=`, `thetamin=`, `thetasevere=` and `vicclamp=`. Only `thetamin=` and `thetasevere=` always print: `pe=` needs a nonzero `const-gravity`, `limcut=` a nonzero accumulated flux, and `vicclamp=` the implicit availability correction (`picorr`). Log parsers keyed on the old line need updating.
- Physics changes only for cards that set `fric-heat`, and those now refuse to load. The one other change is the new `disable_flux_x1` guard on sedimentation, which is reachable only from options built in code (see Limits).
- The original commit also carried a test of the implicit gravity work under rk3 stage weighting. It moves to PR 3, which adds the stage weighting it tests.

## Provenance

- Branch tip `faf83b2` on upstream main `cc72779` (#213), 3 commits. It needs no other PR. It is `5bb8928` (`ca1f556` + two test commits, on `c4236e0`, where the sign-offs below were given) rebased onto the new main. `git range-diff` is 2 `=` and 1 `!`: the `!` is one context line in `ca1f556`'s `src/mesh/meshblock.cpp` include hunk (`#include <mutex>` became `#include <vector>`, from includes #212 and #213 added above it); every added and removed line is byte-identical. A second independent review agent and the upstream owner's reviewing agent each reproduced the rebase independently (tree `9bc8fd2`, the same as `faf83b2`) and ran the three test programs, 12/12 cases on CPU.
- Dev-gated on Linux CPU, torch 2.6, red→green as above. Upstream CI numbers will be added after the draft PR opens.

## Limits

- The meters' cross-rank reduction ran only single-process.
- The corrected `ke`, the new `pe=` and the meters (`limcut`, `thetamin`, `thetasevere`, `vicclamp`) are on the MeshBlock cycle line (`MeshBlockImpl::print_cycle_info`) only. The multi-block Mesh line (`MeshImpl::print_cycle_info`) is unchanged: it never printed `ke`, and it still prints `mass0=`, `masst=` and `energy=`.
- The `disable_flux_x1` path is reachable only from options built in code: `from_yaml` zeroes `grav1` under `disable-flux-x1`, and sedimentation then returns early.
- **CUDA.** Covered on one H100 (sm_90) at `5bb8928` by the second independent review agent: 34/34 C++ tests, the CUDA-named cases ran (none skipped), and the three python tests from a fresh install of this tree. The sedimentation null-grav1 guard and the logged-`ke` tests are host-side; they have no device red/green.
- **`plume-forcing` on a non-plume EOS is silently not installed.** Installation is gated on `eos/type: plume-eos` in `hydro_options.cpp`, which predates this PR; the new unknown-key error lists `plume-forcing` as valid without saying it needs that EOS.
- **Meters on the cycle line.** `thetamin`/`thetasevere` print their initial values when the limiter never ran, and `limcut` is omitted while the flux meter is 0. The run-to-date test checks that the tokens exist, follow `run-to-date:`, and that the marker follows `dt=`; the meter test checks the numbers.
- **"Run-to-date" means since this process started.** The meter buffers are not in the restart variables, so they reset when a block is constructed, including after a restart.
- **Follow-ups (non-blocking, from review).** A friendlier `fric-heat` removal message that names the replacement physics, and routing any `fric*` key to it (misspellings such as `fric_heat` get the generic unknown-key error today); a list- or scalar-valued `forcing:` block gives raw yaml-cpp errors; the valid-key list is maintained by hand in two places; the user-guide gravity example (`configuration.rst:113-125`) was already stale and does not say that unknown forcing keys now fail.

## Review

AI review; each line is the reviewer's verbatim sign-off, times 2026-09-25 PT.

| Reviewer | Sign-off | Time |
|---|---|---|
| the second independent review agent | `SIGN-OFF PR 8 @ 5bb8928d4df5795fd0c93c2414c3070bf3287020: approve` (CPU read) | 01:05 |
| the second independent review agent | `SIGN-OFF PR 8 @ 5bb8928: approve (CPU + H100 CUDA)` | 01:37 |
| the upstream owner's reviewing agent | `SIGN-OFF PR 8 @ 5bb8928: approve code, with nits` (conditional on the card-breaking paragraph, since added in its own words) | 01:50 |
| an independent review agent | `SIGN-OFF PR 8 @ 5bb8928: approve (read)` | 03:52 |
| the second independent review agent | `SIGN-OFF #217 @ faf83b2: approve (rebase, range-diff 2/3 =, CI green)` (the `!` is the include context line) | 09:13 |
| the independent review agent | `SIGN-OFF #217 @ faf83b2: approve (rebase, range-diff 2 = + 1 context-only !, CI green)` | 09:14 |
| the upstream owner's reviewing agent | `SIGN-OFF #217 @ faf83b2 (tree 9bc8fd2): approve (rebase, range-diff 2 = + 1 context-only !, CI green)` | 09:34 |

The first four sign-offs are on `5bb8928` (on `c4236e0`); the last three re-sign the rebased tip `faf83b2` (tree `9bc8fd2`). Upstream CI at `faf83b2` (run [36156480689](https://github.com/chengcli/snapy/actions/runs/36156480689)): pre-commit, ubuntu-latest and macOS-latest all passed.

## Files

```
M  src/forcing/forcing.hpp
D  src/forcing/fric_heat.cpp
M  src/hydro/hydro.cpp
M  src/hydro/hydro.hpp
M  src/hydro/hydro_forward.cpp
M  src/hydro/hydro_options.cpp
M  src/hydro/register_forcing_modules.cpp
M  src/implicit/implicit_hydro.cpp
M  src/implicit/implicit_hydro.hpp
M  src/mesh/meshblock.cpp
M  src/sedimentation/sed_hydro.cpp
M  tests/CMakeLists.txt
A  tests/test_cycle_diagnostics.cpp
A  tests/test_cycle_diagnostics.yaml
M  tests/test_hydro_options.cpp
A  tests/test_sedimentation_guards.cpp
```



## PR #218: eos, mesh, hydro: upward vapour repair with failure reporting; step rejection on fresh primitives; implicit x1 time-step bounds

Merged 2026-09-25; merge commit `a1a08bd`.

## Summary

- **eos**: a vapour deficit in the bottom cell of a column could never be repaired, the CUDA repair never reported a failure, and the CPU failure counter was a data race. Now the repair takes the shortfall from the cells above, capped at the deficit. CUDA counts failures in a device tensor with `atomicAdd`, and CPU uses `std::atomic`.
- **mesh**: step rejection was decided per rank and per block. It missed cells sitting exactly at the floor, missed NaN, skipped cells behind an energy screen that can miss a negative pressure, and restored only the conserved state. Now it tests a fresh primitive against 1.001x the density and pressure floors on every step, makes one allreduced decision for every block on every rank, and restores `hydro_w` and the scalar primitive as well.
- **hydro**: with x1 implicit, `max_time_step` dropped that direction's advective bound, and nothing bounded a supersonic shear across an x1 face. Two new options fix this: `integration/implicit-advection-cfl` (default 1.0) and `integration/shear-cfl` (default 0, meaning off). Either one without an implicit direction is a hard error.
- **implicit** (found in review; patch by a second independent review agent): `implicit-advection-cfl` and `shear-cfl` were read with a numeric fallback, so a non-numeric value silently became the default. They must now be finite numbers (`> 0` and `>= 0` as before); `tests/test_implicit_cfl.cpp` covers bad, negative, valid and default values. The step-redo log line now says "at or within 0.1% of the floor", which matches the existing `1.001` comparison.
- **tests** (found in the review's CUDA run): the mesh arm of `test_check_redo_floor.py` built its velocity on the CPU, so on CUDA it failed with a cuda:0 vs cpu device mismatch. It now builds the velocity on the coordinate device. The upstream owner's reviewing agent checked it red and green on CUDA.

## Tests

The feature-removed tree is this tip with the `src/eos`, `src/mesh` and `src/hydro/hydro.cpp` changes reverted. The tests are kept, and so are the new option parsing and bindings, so that each test reaches its assertions.

| gate | feature removed | this branch |
|---|---|---|
| `test_check_redo_parallel.release` (2 ranks) | **fails 5/5**. `test_check_redo_parallel.cpp:61`: "rank 0 / rank 1 did not redo the step that rank 0 floored" (`Which is: 0`). `:66`: "rank 0 block 0 was not rolled back" | passes 5/5 |
| `test_implicit_advection_cfl_python` | **fails**: `FAIL (cpu): implicit x1, advection_cfl 1.0, implicit x1, advection_cfl 0.25` (dt 1.34e-3 against the expected 1.0e-4 and 2.5e-5) | passes |
| `test_shear_cfl_python` | **fails**: `FAIL (cpu): jump 6cs, shear_cfl 0.2, jump 6cs, shear_cfl 0.1` (dt 3.34e-4 against the expected 5.94e-5 and 2.97e-5) | passes |
| `test_check_redo_floor_python` | **fails**: `FAIL (cpu): block, nan, mesh`. "floored cell not rejected (err=0; stale hydro_w min rho=1)", "a NaN density was not rejected (err=0)", "floor in one block of six not rejected (err=0)" | passes |
| `test_fix_vapor_reports_failure_python` | passes: on CPU the old code already raises, and the path this test guards is CUDA | passes |
| `test_fix_vapor_counts_every_column_python` (CPU, at least 2 threads; one broken column among 16,384, at 32 positions) | **fails 10/10** runs at 80 threads: 30 to 32 of the 32 broken columns go unreported in each run. With the same tree at 1 thread it passes 3/3 | passes 10/10 at 40 threads |
| `test_fix_vapor_reports_failure_cuda_python` (skipped without a GPU) | **fails** on a V100: `FAIL (cuda): unrepairable vapour column was NOT reported` (the old counter always returned 0) | passes on a V100; skipped on CPU-only nodes, as intended |

`ctest -N` lists all seven gates, and each `*_python` test carries `PYTHONPATH` for the snapy built from this tree.

## Compatibility

- **Existing `implicit-scheme: 1` and `9` cards change numerically, with no new key.** They now get the default `implicit-advection-cfl: 1.0`, so in 2-D and 3-D the time step is also bounded by an advective Courant number of 1 in the implicit x1 direction (|w1| Δt / Δx1 ≤ 1), a direction that had no bound before. The step changes only where this bound is the tightest one; how often that happens on the shipped cards was not measured. A large `implicit-advection-cfl` relaxes the bound. 1-D runs keep their old acoustic x1 bound. `shear-cfl` defaults to 0 (off) and changes nothing unless set.
- Shipped cards affected: 6 of the 13 `examples/` cards that set `implicit-scheme` (scheme 1: `jupiter_crm`, `jupiter_crm_dry`, `jupiter_evap_precip_1d`, `uranus`; scheme 9: `jupiter_gcm`, `jupiter_gcm_dry`). The other 7 set 0. Among the tests, `test_riemann.cpp` sets scheme 1.
- **The CPU failure counter gave a real false success, not only a data race on paper.** Measured by `test_fix_vapor_counts_every_column` on the old `int` counter: at 80 threads the count ended at 0, so no error was raised, for 30 to 32 of the 32 broken columns in each of 10 runs; at 1 thread it never did. The likely mechanism, not confirmed in the generated code, is a thread whose chunk held no failing column storing its stale zero back over the failing thread's count. Who reaches it: upstream's C++ executables do, because torch uses every core unless `-p` sets the thread count. Python runs do not, because `import snapy` sets one thread, unless the caller raises it afterwards.

## Provenance

- Branch tip `b619941` on upstream main `572a256` (#217), 8 commits: `0af0493` (on `cc72779`) pure-rebased, `git range-diff cc72779..0af0493 572a256..b619941` 8/8 `=`, tree `9a0b572`. Before that: tip `0af0493` on `cc72779` (#213), 8 commits. It needs no other PR. It is `a4b7d93` (on `c4236e0`, tree `2c0ce0c0`, where the sign-offs below were given) rebased onto the new main. The one conflict was in `tests/CMakeLists.txt`, where #213 and this PR each add a `setup_parallel_test` line at the same place; both are kept (`test_output_barrier`, then `test_check_redo_parallel`) and nothing else changed. `git range-diff` is 7 `=` and 1 `!`, and the `!` is only that context line. The PR author and the upstream owner's reviewing agent reached the same tree `f3a4611` independently. On it, a CUDA Release build passes `test_check_redo_parallel`, `test_output_barrier` and `test_implicit_cfl`, and `ctest -j1` is 55/56. The one failure is `test_exchange_ucx_cuda` with one visible GPU, which fails the same way on `a4b7d93` (see Limits).
- `a4b7d93` is `c222b1a` plus `aac8b26` (the six-panel deck carries no scalar upper-bound yet) and the two review commits above.
- The mesh commit adds `tests/test_flux_positivity_cubedsphere.yaml`, the six-panel deck that `test_check_redo_floor.py` reads. It is byte-identical to the copy in the tracer-positivity PR.
- The gates ran at this tip: `test_check_redo_floor_python` red and green, plus the three other gates re-run green (the multi-rank test passed 2/2).
- Dev-gated on Linux CPU, torch 2.6, red to green as above. The multi-rank test was launched without torchrun because of a local port clash.
- Upstream CI numbers will be added after the draft PR opens.

## Limits

- **CUDA.** The vapour-counter gate ran red and green on one V100 (CUDA 12.2, torch 2.6, sm_70), as above. On the review-fixed tree (`2c0ce0c0`), one H100 (sm_90, the second independent review agent) ran `ctest -j1` 48/48 with no skips. Five example and restart tests first failed on a torchrun port clash with a concurrent suite and passed when rerun alone. `test_implicit_cfl` passes, and `test_check_redo_floor.py` passes all three arms on CPU and on CUDA (with the preload below).
- **`eos_limiter` gtests not built.** The upward-repair gtests in `test_eos.cpp` were not built here, because `test_eos` does not compile against this glibc: `major` is a macro there. That also happens on the base.
- **Cost not measured.** Running the inversion unconditionally costs about five per cent of a cycle in 3-D. That figure is counted from the kernels, not measured.
- **Python redo test on CUDA needs kintera's CUDA library preloaded.** `block.forward` raises `DispatchStub: missing kernel for cuda` unless `libkintera_cuda_release.so` is loaded. The kernel is kintera's `call_func2`, registered in that library, and neither this tree nor main's `libsnap_cuda_release.so` links it. With the preload, the block and nan arms pass. This is pre-existing packaging, not this PR. Shear and the column report pass on the H100 without the preload, because they never call `eval_intEng_R`.
- **Floor message.** It now says "at or within 0.1% of the floor", matching the existing `1.001` comparison; the comparison itself is unchanged.
- **Full CUDA ctest at `4569cec`** (the upstream owner's reviewing agent, 2026-09-25): RTX 5090, one visible GPU, 48/49; no CUDA test skipped. The one failure is `test_exchange_ucx_cuda`, a 2-rank test that crashes with "invalid device ordinal" when only one GPU is visible, instead of returning the skip code 125. That is pre-existing test behaviour, and the test passes when run on its own. On an RTX 4000, `test_eos` runs out of device memory, as it already does at base `c4236e0`.

## Review

AI review; each line is the reviewer's verbatim sign-off, times 2026-09-25 PT.

| Reviewer | Sign-off | Time |
|---|---|---|
| the second independent review agent | `SIGN-OFF PR 7 @ 4569cec: approve` (CPU read, before the review fixes) | 02:24 |
| an independent review agent | `SIGN-OFF PR 7 @ a4b7d93 (tree 2c0ce0c0): approve (read)` | 04:06 |
| the second independent review agent (author of both review fixes) | `SIGN-OFF PR 7 @ a4b7d93 (tree 2c0ce0c0): approve (author)` | 04:14 |
| the upstream owner's reviewing agent | `SIGN-OFF PR 7 @ a4b7d93 (tree 2c0ce0c0): approve (implicit_cfl + redo_floor CPU/CUDA, redo-vel red/green on CUDA, ctest 49/50 = known ucx_cuda)` | 06:08 |
| the second independent review agent | `SIGN-OFF #218 @ 0af0493 (tree f3a4611): approve (rebase, range-diff 7 = + 1 !, CI green)` (the `!` is the tests/CMakeLists.txt resolution keeping both `setup_parallel_test` lines; author of the review fixes, so a rebase check only) | 09:38 |
| the independent review agent | `SIGN-OFF #218 @ 0af0493 (tree f3a4611): approve (rebase, range-diff 7 = + 1 context-only !, CI green)` | 09:39 |
| the upstream owner's reviewing agent | `SIGN-OFF #218 @ 0af0493 (tree f3a4611): approve (rebase, range-diff 7 = + 1 !, CI green)` | 09:41 |
| the second independent review agent | `SIGN-OFF #218 @ b619941 (tree 9a0b572): approve (rebase, range-diff 8/8 =, CI green)` (pure rebase onto `572a256` after #217 merged; all `=`, so one re-sign) | 11:02 |

The first four sign-offs are on tree `2c0ce0c0` (`a4b7d93`, on `c4236e0`); the next three re-sign the rebased tip `0af0493` (tree `f3a4611`); the last re-signs the pure rebase `b619941` (tree `9a0b572`) onto `572a256`. Upstream CI at `0af0493` (run [36157428627](https://github.com/chengcli/snapy/actions/runs/36157428627)) and at `b619941` (run [36166600975](https://github.com/chengcli/snapy/actions/runs/36166600975)): pre-commit, ubuntu-latest and macOS-latest all passed.

## Files

```
M	python/csrc/pyimplicit.cpp
M	python/snapy/implicit.pyi
M	src/eos/eos_dispatch.cpp
M	src/eos/eos_dispatch.cu
M	src/eos/fix_vapor_impl.h
M	src/hydro/hydro.cpp
M	src/implicit/implicit_hydro.cpp
M	src/implicit/implicit_hydro.hpp
M	src/mesh/mesh.cpp
M	src/mesh/meshblock.cpp
M	src/mesh/meshblock.hpp
M	tests/CMakeLists.txt
A	tests/test_check_redo_floor.py
A	tests/test_check_redo_parallel.cpp
M	tests/test_condensate_conservation.yaml
M	tests/test_diffusion_moist.yaml
M	tests/test_eos.cpp
A	tests/test_fix_vapor_counts_every_column.py
A	tests/test_fix_vapor_reports_failure.py
A	tests/test_fix_vapor_reports_failure.yaml
A	tests/test_fix_vapor_reports_failure_cuda.py
M	tests/test_flux_positivity.yaml
A	tests/test_flux_positivity_cubedsphere.yaml
M	tests/test_forcing_3d.yaml
A	tests/test_implicit_advection_cfl.py
A	tests/test_implicit_cfl.cpp
A	tests/test_shear_cfl.py
```



## PR #219: eos, forcing: temperature-floor internal energy; opt-in at-face bottom relaxation; sponge and drag forces lowered to covariant

Merged 2026-09-25; merge commit `5939862`.

## Summary

- **eos**: `_temp2intEng` got the internal energy of a configured temperature floor wrong. It scaled the reference offsets by T instead of adding them, and it dropped the dry heat capacity. Now it adds the offset through `internal_energy_offset` and includes `rho_d*cv_d*T`, so `"UT->I"` matches `"W->I"`.
- **forcing**: `relax-bot-temp` relaxed the first cell centre, but the prescribed temperature belongs to the lower face. A new opt-in `at-face: true` relaxes `1.5*T0 - 0.5*T1` with the gain divided by 1.5. It is off by default.
- **tests**: a new test checks that `at-face` relaxes toward the face extrapolation and that the default is bit-identical.
- **forcing**: `at-face` no longer aborts on a bottom temperature inversion. Its first call used to require `mean(T0) >= mean(T1)` as a check of the slice orientation, but an inversion (`T0 < T1`) is a legal state where the face extrapolation is well-defined, and temperature ordering cannot tell which way a slice runs. The check, its one-shot process-wide flag and the include it needed are removed (review: an independent review agent).
- **forcing**: the top sponge, bottom sponge and bottom-velocity relaxation added a contravariant force to covariant momenta. On the cubed sphere this rotated the wind instead of braking it. The force is now lowered with `coord_vec_lower_`, which is the identity on orthogonal grids, so those grids are bit-identical.

## Tests

The feature-removed tree is this tip with every `src/` change of the branch reverted. The tests are kept.

| gate | feature removed | this branch |
|---|---|---|
| `test_eos_temp2inteng_python` | **fails** in two ways. The round trip misses at every T: "UT->I and W->I differ by 5.824e+01" at 50 K, up to 1.597e+03 at 400 K. The intercept is also wrong: "the T=0 intercept of ie(T) is 0 but the reference offset is -2.548588e+05" | passes |
| `test_forcing.release`: `forcing.relax_bottom_temperature_at_face` | **fails** at `test_forcing.cpp:278`: `torch::allclose(on, expected, 1.e-13, 0.)` | passes |
| `test_forcing.release`: `forcing.cubed_sphere_sponge_drag_is_covariant` | **fails** 18x at `:331` (the cross term is 0.0547 where it should be at most 9.3e-14) and 18x at `:337` | passes |
| `test_forcing.release`: `forcing.relax_bottom_temperature_at_face_under_an_inversion` (new; review: the independent review agent) | red = this tip with `src/forcing/relax_bot_temp.cpp` at `65aa186`: **aborts** with "[RelaxBotTemp] index convention violated: offset 0 of the lower-boundary slice (T=406.894) should be deeper, and so no colder, than offset 1 (T=411.751)" | passes: the tendency equals `(1/1.5)(dt/tau) rho cv (btemp - (1.5 T0 - 0.5 T1))` to 1e-13 |
| `test_forcing.release` (whole binary) | fails | passes (21 tests) |

Line numbers in the first rows refer to `65aa186`'s test file; the inversion test sits above them and shifts them by 30 at this tip (`:278` is now `:308`, `:331` and `:337` are `:361` and `:367`). The inversion test is placed first so that it is the first `at-face` call in the process, which is the call the removed check guarded. `forcing.relax_bottom_temperature_at_face`, which also pins the default (`at-face: false`) tendency with `torch::equal`, passes at this tip.

`ctest -N` lists both gates. `test_eos_temp2inteng_python` carries `PYTHONPATH` for the snapy built from this tree.

## Provenance

- Branch tip `973ede5` (tree `c05d6dc`) on upstream main `14f926f` (#216), 6 commits: `e5162f5` pure-rebased over #216, `git range-diff a1a08bd..e5162f5 14f926f..973ede5` 6/6 `=`. It needs no other PR. Before that: tip `e5162f5` (tree `dd3f8b4`) on `a1a08bd` (#218), which is `f9ffd85` (on `c4236e0`, tree `0a583bcb`, where the sign-offs below were given) rebased over #212 to #218. The one conflict was in `tests/CMakeLists.txt` at the first commit: main's new python tests and this PR's `snapy_add_python_test(test_eos_temp2inteng ...)` land at the same spot, and both are kept, main's lines first; nothing else changed. `git range-diff c4236e0..f9ffd85 a1a08bd..e5162f5` is 5 `=` and 1 `!`, the `!` being only that hunk's context (`src/eos/ideal_moist.cpp` and the two test files in that commit are unchanged). Three independent rebases reached the same tree `dd3f8b4` (the PR author, the independent review agent, a second independent review agent); on it the three `at_face` gtests pass 3/3 and `test_eos_temp2inteng.py` passes against the module built from that tree (the second independent review agent, CPU Release; round-trip relative error at 50 to 400 K between 1.4e-16 and 1.9e-15). Before that: tip `f9ffd85` = `495081b` (`65aa186` + the check removal) + the at-face bool check, on `c4236e0` (#211).
- Dev-gated on Linux CPU, torch 2.6, red to green as above.
- Upstream CI at `e5162f5` (run [36174351163](https://github.com/chengcli/snapy/actions/runs/36174351163)): pre-commit, ubuntu-latest and macOS-latest all passed. Upstream CI at `973ede5` (run [36179567336](https://github.com/chengcli/snapy/actions/runs/36179567336)): pre-commit, ubuntu-latest and macOS-latest all passed. The first five sign-offs below are on tree `0a583bcb` (`f9ffd85`, on `c4236e0`); the next three re-sign the rebased tip `e5162f5` (tree `dd3f8b4`); the last re-signs the pure rebase `973ede5` (tree `c05d6dc`).

## Limits

- **`at-face` stays off by default.** On the one initial condition tried, the corrected forcing cost stability, so it is opt-in and has no production run behind it.
- **Drag not run at scale.** The drag fix is gated by a single-block check on every panel. It has not been run in a full cubed-sphere simulation here.
- **CUDA.** At `495081b`, the upstream owner's reviewing agent reverted each fix and saw it go red on CPU and on CUDA (RTX 5090). On the review-fixed tree (`0a583bcb`), `test_forcing` passes on one H100 (the second independent review agent). The Python tests were not rerun there, because no package was installed from that tree. The new tests themselves are CPU-only (see below).
- **New tests are CPU-only.** The new gtests are plain `TEST` with default CPU double tensors. `test_eos_temp2inteng.py` accepts `--device cuda`, but the CMake registration does not pass it, so the suite runs it on CPU.
- **The covariance test checks direction only.** `cubed_sphere_sponge_drag_is_covariant` checks that the horizontal drag is parallel to the covariant momentum (cross product near zero) and nonzero. A drag pointing the same way as the momentum would pass, and nothing checks the size of the force.
- **`temperature-floor` is not validated.** It is read with `as<double>(20.)` and never checked for positive or finite (`equation_of_state.cpp`). The new Python test checks that UT->I matches W->I; it does not reject a negative floor. The gap predates this PR.

## Review

AI review; each line is the reviewer's verbatim sign-off, times 2026-09-25 PT.

| Reviewer | Sign-off | Time |
|---|---|---|
| the upstream owner's reviewing agent | `SIGN-OFF PR 9 @ 495081b: approve` (every fix reverted went red on CPU and CUDA) | 00:08 |
| the independent review agent | `SIGN-OFF PR 9 @ f9ffd85 (tree 0a583bcb): approve (read)` | 04:06 |
| the second independent review agent (author of the at-face fix) | `SIGN-OFF PR 9 @ f9ffd85 (tree 0a583bcb): approve (author)` | 04:14 |
| the upstream owner's reviewing agent | `SIGN-OFF PR 9 @ 495081b+at-face patch f30b9990 (tree 0a583bcb): approve (test_forcing 22/22 CPU + CUDA build)`; test_forcing uses CPU tensors, so the CUDA run shows build and linking only | 06:05 |
| the upstream owner's reviewing agent | `SIGN-OFF PR 9 @ f9ffd85 (tree 0a583bcb): approve (test_forcing 22/22 CPU + CUDA build)` (same tree, re-posted at the pushed commit) | 08:32 |
| the second independent review agent | `SIGN-OFF #219 @ e5162f5 (tree dd3f8b4): approve (rebase, range-diff 5 = + 1 ! keep-both CMakeLists, CI green)` (author of the at-face bool check, so a rebase check only; ran the at-face gtests 3/3 and test_eos_temp2inteng on this tree) | 12:12 |
| the independent review agent | `SIGN-OFF #219 @ e5162f5 (tree dd3f8b4): approve (rebase, range-diff 5 = + 1 ! keep-both CMakeLists, CI green)` | 12:13 |
| the upstream owner's reviewing agent | `SIGN-OFF #219 @ e5162f5 (tree dd3f8b4): approve (rebase, range-diff 5 = + 1 ! keep-both CMakeLists, CI green)` (replayed f9ffd85 onto a1a08bd with merge-tree: the result differs from e5162f5 only by the conflict-marker lines) | 12:14 |
| the second independent review agent | `SIGN-OFF #219 @ 973ede5 (tree c05d6dc): approve (rebase, range-diff 6/6 =, CI green)` (pure rebase onto `14f926f` after #216 merged; all `=`, so one re-sign) | 13:03 |

## Files

```
M	src/eos/ideal_moist.cpp
M	src/forcing/bot_sponge_lyr.cpp
M	src/forcing/forcing.hpp
M	src/forcing/relax_bot_temp.cpp
M	src/forcing/relax_bot_velo.cpp
M	src/forcing/top_sponge_lyr.cpp
M	tests/CMakeLists.txt
A	tests/test_eos_temp2inteng.py
A	tests/test_eos_temp2inteng.yaml
M	tests/test_forcing.cpp
A	tests/test_forcing_cubed_sphere.yaml
```
