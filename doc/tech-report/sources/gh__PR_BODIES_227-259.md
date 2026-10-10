> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# snapy upstream pull requests #227-#259 (merged), bodies
Fetched 2026-10-09 from the public chengcli/snapy repository (GitHub REST API).

## PR #227: hygiene: seven small independent fixes (tests, cmake, ICY, ImplicitOptions, eos keys, unregistered tests)

Merged 2026-09-27; merge commit `644c903`.

## Merge summary

Seven small, independent hygiene changes, one concern each, plus a kintera version floor added in review. None changes a number any shipped example produces.

- **tests: tighter seam-conservation bound.** The cubed-sphere flux-positivity tests allowed a relative mass drift of 1e-12, about 400 times the round-off they produce. The bound is now 1e-13, and the dry test gains `--device cuda`.
- **cmake: sm_120 only for nvcc >= 12.8.** Any nvcc from 12.0 to 12.7 failed to build the CUDA library (`Unsupported gpu architecture 'compute_120'`). Lists for 12.8 and later are unchanged.
- **refactor: the hydro-variable offset is named `ICY`, not a bare 5.** No live bare-5 hydro offsets remain; every card tested is byte-identical.
- **python: `ImplicitOptions.type()` is bound as the read-only getter it is.** The old binding cast the method to a getter/setter pair it does not have. Every call was undefined behaviour: `type()` raised "Unsupported implicit scheme" for valid schemes.
- **docs: `ImplicitOptions` documents the options it has.** `enabled`, `max_iter`, `tolerance` and a `method` YAML key never existed. They are replaced by `scheme`, `type`, `advection_cfl`, `shear_cfl` and the real `integration/` keys.
- **eos: unknown `dynamics/equation-of-state` keys are refused.** A typo, a wrong-case key or a key nothing reads (`tracer-floor`, in six examples) used to load silently. It is now an error naming the key and listing the valid ones.
- **tests: every test source is accounted for (#224).** Ten test sources were never registered in ctest. Three are now registered as DISABLED ctests (two of them compile in every configuration again), the other seven are listed with the reason each is not registered, and `FULL_TESTS` is a real `option(... OFF)` (`-DFULL_TESTS=OFF` used to turn the set on).
- **build, eos: requires kintera >= 2.5.0 (added in review).** kintera reads and validates `dynamics/equation-of-state/uv-solver` only from 2.5.0, so pyproject, CI and `find_package(Kintera 2.5.0 REQUIRED)` now refuse an older kintera; a new test checks that `uv-solver: kkt` reaches kintera's options and that `uv-solver: bogus` is refused with "Invalid UV solver". Users on kintera 2.4.x must upgrade. A kintera built from a checkout without tags reports version 0.0.0 and is refused too, so fetch tags before building it from source.

Each commit's section below gives its own before/after numbers, measured on that commit's own base (the drift, CMake, binding and docs commits on `9738861`, the EOS commit on `97b3be4`, the test-registration commit on `bda4b6c`); a full CPU and CUDA ctest on the combined head is reported under CI. Review commit by commit; any one can be dropped without touching the others.

**Suggested squash message** (keeps the two user-visible breaks in main's history):
```
hygiene: seven small fixes (tests, cmake, ICY, ImplicitOptions, eos keys, unregistered tests); require kintera >= 2.5.0

- Builds with NMASS > 0 are refused at compile time (static_assert in snap.h): species rows follow the five hydro rows.
- Requires kintera >= 2.5.0 (pyproject, CI, find_package), the first kintera that reads and validates uv-solver.
- Unknown dynamics/equation-of-state keys are refused; cards carrying tracer-floor or other unread keys must drop them.
```

---

## 1. tests: tighten cubed-sphere flux-positivity DRIFT_TOL to 1e-13; dry test takes --device

**Change.** `DRIFT_TOL` goes from 1e-12 to 1e-13 in `tests/test_flux_positivity_cubedsphere.py` and `tests/test_flux_positivity_cubedsphere_moist.py`. The dry test gains `--device {cpu,cuda}`, done as in the moist test: the blocks and the initial state move to the device, and the per-block totals come back to the CPU before summing. An assert checks that the state really is on the requested device.

**Drift measured on the tests' own deck** (nlim 40, float64, relative drift of the tracer/species total; 3 repeats per row, bit-identical in every row; the maximum over cycles equals the end value in every run except where shown):

sm_120: RTX 5090 (cc 12.0), nvcc 13.1.115, torch 2.10.0+cu128, kintera 2.5.0 (PyPI), arch list 75 80 86 89 90 120. Dry CUDA rows come from a local copy of the dry test with the same `--device` change.

| test | arm | device | end drift | limiter hits |
|---|---|---|---|---|
| dry | base | cpu | 2.238189e-15 | 0 |
| dry | limited | cpu | 2.398060e-15 | 117058 |
| dry | base | cuda | 2.238189e-15 | 0 |
| dry | limited | cuda | 2.238189e-15 | 116172 |
| moist | base / limited | cpu | 1.796061e-15 | 0 / 139 |
| moist | base / limited | cuda | 1.796061e-15 | 0 / 95 |

sm_70: V100-PCIE-32GB (cc 7.0), nvcc 12.2, torch 2.6.0+cu124, kintera v2.5.0 (built from source), arch list 70 (local build setting; see section 2 for why the default list does not build on 12.2).

| test | arm | device | end drift | max over cycles | limiter hits |
|---|---|---|---|---|---|
| dry | base | cpu | 2.238189e-15 | 2.238189e-15 | 0 |
| dry | limited | cpu | 2.238189e-15 | 2.238189e-15 | 117290 |
| dry | base | cuda | 2.238189e-15 | 2.398060e-15 | 0 |
| dry | limited | cuda | 2.398060e-15 | 2.398060e-15 | 116647 |
| moist | base / limited | cpu | 1.796061e-15 | 1.796061e-15 | 0 / 139 |
| moist | base / limited | cuda | 1.796061e-15 | 1.796061e-15 | 0 / 176 |

**Derivation of 1e-13.** The largest drift on either arch is 2.398060e-15. 1e-13 is about 42 times that, rounded to a decade. Two things need margin:
- **Arch and build.** The dry arms land on the same two values on both machines, but which arm gets which value changes between builds, even on CPU (dry limited on CPU: 2.398060e-15 with torch 2.10, 2.238189e-15 with torch 2.6). A bound such as 5e-15 would be fragile.
- **Growth.** The drift grows about linearly with cycles, at roughly 5-6e-17 per cycle (dry, V100 CPU: 2.30e-16 at cycle 1, 1.12e-15 at cycle 20, 2.24e-15 at cycle 40). A card about twice as long still passes. 1e-14 would leave only about 4 times headroom.

The new bound is still 10 times tighter than before. Hypothesis, not used for the bound: the two dry values are exactly 14 and 15 times 1.598707e-16, which fits whole rounding steps of the tracer total. The moist value is 11.23 of those steps, so the step depends on each test's total. This was not checked by printing the total's ulp.

**Gate (V100 node, this commit).**
- Both unmodified tests pass with the new bound on CPU and on CUDA, including the dry test's new `--device cuda` arm. The largest drift is 2.398e-15, and each value matches the table above.
- ctest registers both tests (`python tests/<name>.py`, no arguments), and both pass.
- Red check: multiplying the final total by (1 + 3e-13) gives drifts of 2.975e-13 to 2.981e-13. That passes at the old bound 1e-12 and fails at 1e-13 (dry CPU, dry CUDA, moist CPU). Each failure prints exactly the two drift failures, while the hit and bound checks still pass.

---

## 2. cmake: add sm_120 only for nvcc >= 12.8

**Change.** `CMakeLists.txt` appended `90 120` for every nvcc >= 12.0, and the `TORCH_CUDA_VERSION` fallback branch did the same. nvcc knows `compute_120` only from 12.8, so now 120 is appended only for >= 12.8, in both branches. 90 stays at >= 12.0; nvcc supports it from 11.8, so that gate is conservative, not wrong. No arch is added.

**Build, nvcc 12.2** (V100 node, torch 2.6.0+cu124, `BUILD_TESTS=ON`; the two trees differ only in `CMakeLists.txt`):

| | main | this commit |
|---|---|---|
| configure | rc 0 | rc 0 |
| gencode (`flags.make`) | 60 61 70 75 80 86 89 90 120 | 60 61 70 75 80 86 89 90 |
| build | fails: `nvcc fatal : Unsupported gpu architecture 'compute_120'` (10 times), no CUDA library | rc 0 |
| `cuobjdump --list-elf libsnap_cuda_release.so` | (not built) | SASS sm_60 61 70 75 80 86 89 90 |
| moist seam test `--device cuda` | (no CUDA library) | pass, drift 1.796e-15 |
| `ctest -j 1` | (no CUDA library) | 57/64 pass |

The 7 ctest failures are `test_exchange`, `test_output_barrier`, `test_check_redo_parallel`, `test_straka`, `test_shallow_xy`, `test_shallow_splash` and `test_restart_cycle_limit`. All are multi-process tests, and each fails on `port: 29500 ... EADDRINUSE` on that node. None of their logs mentions a missing kernel image, an invalid device function or a compute capability.

**Arch list by toolkit.** The arch block was configured alone, copied verbatim from each tree, with `find_package(CUDAToolkit)` and each NVIDIA HPC SDK nvcc (configure only, no snapy code compiled):

| nvcc | main | this commit |
|---|---|---|
| 12.2 | 60 61 70 75 80 86 89 90 120 | 60 61 70 75 80 86 89 90 |
| 12.6 | 60 61 70 75 80 86 89 90 120 | 60 61 70 75 80 86 89 90 |
| 12.8 | 60 61 70 75 80 86 89 90 120 | unchanged |
| 12.9 | 60 61 70 75 80 86 89 90 120 | unchanged |
| 13.0 | 75 80 86 89 90 120 | unchanged |

**Limits.**
- The `TORCH_CUDA_VERSION` branch runs only when `CUDAToolkit_VERSION` is undefined, which a successful `find_package(CUDAToolkit REQUIRED)` never leaves; it was changed for consistency and not exercised.
- Pre-existing, found by review: that fallback branch never removes 60/61/70 for a 13.x toolkit, as the main branch does; out of scope here.
- 89 is still unconditional, and nvcc older than 11.8 does not know it; that is out of scope here.
- Pre-existing, not changed: `libsnap_cuda_release.so` carries SASS only, no PTX (seen with this commit and in a build of main with the arch list reduced to 70). Cause, identified in review: `CUDA_SEPARABLE_COMPILATION ON` (`src/CMakeLists.txt:143`), so the device-link step emits SASS only. sm_121 runs the sm_120 SASS; sm_100/sm_103 and later major architectures would get "no kernel image". Out of scope here.

---

## 3. refactor: name the hydro-variable offset `ICY` instead of a bare 5

Measured by the commit's author (the upstream maintainer's agent):

- **Grep, over src, tests and python on each commit.** The hydro-offset pattern drops from 21 hits in 15 files at the base to 1 at this commit. That one is inside the commented-out kernel in `eos_dispatch.cpp`, so no live bare-5 offsets are left. The broad bare-5 pattern goes from 35 to 15, and the other 14 are stencil widths, the WENO5 guard, a restart-filename offset and the `.0000` suffix. `ICY` uses go from 279 to 303. Diffstat: 15 files, +28/-21.
- **Cards.** Two clean CPU builds from the same configure line (Release, no CUDA, NMASS unset). Each card ran twice per commit with 4 threads, and every output file was compared. All four runs match byte-for-byte: shock at 200 steps (36 files), straka_single at 300 steps (4), bryan at 100 steps (5), and jupiter_evap_precip_1d at 200 steps (27, with `MALLOC_PERTURB_=165`). The straka and bryan step counts were capped.
- **Tests.** CPU ctest at this commit: 65/65, with one CUDA-only skip. CUDA ctest 66/66 on both GPUs, including the 2-rank UCX test, and the NMASS=2 compile-time refusal were measured earlier on the same commit.
- **NMASS guard.** Builds with NMASS > 0 (the legacy layout, species at rows 1..NMASS) are now refused at compile time by a static_assert in snap.h: no test, example or CI job builds that layout, and code on main already assumed species follow the five hydro rows (e.g. sedimentation's `hydro_ids - 5`); build with the default NMASS = 0, where species follow IPR and their number is set at run time.

---

## 4. python: bind ImplicitOptions.type() as the read-only getter it is

**Change.** `python/csrc/pyimplicit.cpp` bound `type` with `ADD_OPTION`. That macro C-casts the member to a getter `std::string const& (S::*)() const` and to a setter `S& (S::*)(std::string const&)`. `ImplicitOptionsImpl::type()` is neither: it returns `std::string` by value and has no setter, so every call went through a mis-typed member pointer. `type` is now a plain `.def` of the real method, and the setter overload is removed from `implicit.pyi`. All 117 `ADD_OPTION` uses in `python/csrc` were checked against the `ADD_ARG` declarations of their structs, and this is the only mismatch. Nothing in the tree calls `type()` from Python.

**Test** `tests/test_implicit_options_type.py` (new, registered in ctest). It checks the name for schemes 0, 1 and 9, an error for the unsupported scheme 5, and a `TypeError` for `type("vic-full")`.

| check | main + test | this commit |
|---|---|---|
| `scheme(0).type()` | RuntimeError: Unsupported implicit scheme | `"none"` |
| `scheme(1).type()` | RuntimeError: Unsupported implicit scheme | `"vic-partial"` |
| `scheme(9).type()` | RuntimeError: Unsupported implicit scheme | `"vic-full"` |
| `type("vic-full")` | RuntimeError (the call ran the getter) | TypeError |

Full `ctest -j 1` (CPU): the only outcome that changes is the new test (fails on main, passes here). The same eight tests as in section 6 fail on our test machine identically on main and with this commit: `test_exchange`, `test_output_barrier`, `test_check_redo_parallel`, `test_exchange_ucx`, `test_straka`, `test_shallow_xy`, `test_shallow_splash` and `test_restart_cycle_limit`. It is a pybind getter with no device path, so there is no CUDA arm.

---

## 5. docs: ImplicitOptions lists the options it actually has

**Change.** `docs/api/implicit.rst` documented `enabled()`, `max_iter()` and `tolerance()`, and `docs/user_guide/configuration.rst` showed a `hydro/implicit` block with `enabled`, `max_iter`, `tolerance` and `method`. None of these exist. Both pages now cover:
- `scheme` (0 none, 1 vic-partial, 9 vic-full);
- `type` (read-only);
- `advection_cfl`: `dt <= advection_cfl * dx1 / |v1|` when x1 is implicit and the grid is not a 1-D column; default 1.0, must be > 0;
- `shear_cfl`: `dt <= shear_cfl * cs * dx / (|v_lo| * |v_hi|)` at x1 faces where a horizontal wind jumps by at least `cs`; default 0.0 (off), must be >= 0;
- `from_yaml`, which returns `None` when no scheme is set;
- the real YAML keys: `integration/implicit-scheme`, `implicit-advection-cfl`, `shear-cfl`.

The stub `python/snapy/implicit.pyi` and the `from_yaml` signature in `implicit.rst` now say the return is `ImplicitOptions` or `None`, matching the code (`from_yaml` returns `None` when there is no `integration` block or the scheme is absent or 0).

**Check.** On a built package, `hasattr(ImplicitOptions(), m)` is True for `scheme`, `type`, `advection_cfl` and `shear_cfl`, and False for `enabled`, `max_iter` and `tolerance`. Each formula was read from the code that applies it. `sphinx-build -n` (Sphinx 9.1, `docs/requirements.txt`): no new warnings, and the `ImplicitOptions` cross-reference in `configuration.rst` resolves (one warning fewer than main). The stub parses (`ast.parse`).

---

## 6. eos: refuse unknown dynamics/equation-of-state keys

**Change.** `EquationOfStateOptions::from_yaml` read the block key by key, with defaults, so a key nothing reads loaded silently. It now refuses any key outside:
- the keys snapy reads: `type`, `gammad`, `weight`, `density-floor`, `pressure-floor`, `temperature-floor`, `limiter`, `eos-file`, `verbose`;
- the keys kintera reads from the same block: `max-iter`, `ftol`, `uv-solver`.

The error names the key and lists the valid ones, in the style of the existing `dynamics/` and `forcing/` checks. The valid-key text is built from the same arrays as the check, and the `dynamics/` message is now built the same way (byte-identical text). `tracer-floor` has never had a reader in snapy or kintera. It is removed from `examples/{bryan,jupiter_crm,jupiter_crm_dry,jupiter_evap_precip_1d,jupiter_gcm,jupiter_gcm_dry}.yaml` and from the `test_riemann` card.

**Tests** (in `tests/test_hydro_options.cpp`, test commit first):

| test | before the fix | with the fix |
|---|---|---|
| `reject_unknown_equation_of_state_keys`: `tracer-floor`, `limter`, `Limiter` | FAIL x3 (each accepted) | PASS |
| `every_equation_of_state_key_is_accepted_and_read` (all 12 keys set to non-default values; each reaches its option, except `uv-solver`, which kintera reads only from v2.5.0) | PASS | PASS |
| other `hydro_options` tests (5, plus 1 CUDA-only skipped on CPU) | PASS | PASS |
| `test_riemann` (card lost `tracer-floor`) | 8/8 | 8/8 |

The second test guards the whitelist itself: a list that missed a key which is read could not pass.

**Full `ctest -j 1`** (CPU, 67 tests): the only outcome that changes is `test_hydro_options` (fails before the fix, passes with it). Eight other tests fail on our test machine, identically on main and with this commit: `test_exchange`, `test_output_barrier`, `test_check_redo_parallel`, `test_exchange_ucx`, `test_straka`, `test_shallow_xy`, `test_shallow_splash` and `test_restart_cycle_limit`.

**Card sweep.** `HydroOptions.from_yaml` was run on every YAML card with an equation-of-state block: the 46 in this repository and 123 in a downstream collection. The only change: 63 downstream cards that still carry `tracer-floor` are now refused with the new message. No other card's outcome changes.

**Known limits.**
- **Version skew:** a key that a newer kintera starts reading from this block is refused until it is added to the kintera list. That is the loud direction. The reverse was silent: a kintera older than v2.5.0 does not read `uv-solver`, so snapy accepted that key and nothing read it. The last commit closes this by requiring kintera >= 2.5.0.
- Only the top level of the block is checked; values are checked by the code that reads them, as before.
- Cards outside this repository that carry `tracer-floor`, or any other unread key, now fail to load and must drop it.
- The test compiles against kintera v2.4.2 headers (the declared minimum) as well as v2.5.0; before this revision its `uv_solver()` assertion did not (checked by a compile-only build against each header set).
- Pre-existing, out of scope: `pyproject.toml` declares `kintera>=2.1.0` for the build and `kintera>=2.4.2` at run time.

---

## 7. tests: account for the ten unregistered test sources; make FULL_TESTS a real option

Written by the commit's author (the upstream maintainer's agent):

- Register `test_read_topo`, `test_aneos` (C++) and `test_exchange.py` (torchrun, 4 ranks) as DISABLED ctests. The two C++ ones are now built in every configuration, so they keep compiling against the current API. ctest lists all three as "Not Run (Disabled)".
- List the other seven sources in `tests/CMakeLists.txt` with the reason each is not registered (removed APIs/headers, or missing module/data/arguments).
- `FULL_TESTS` is now `option(... OFF)` and checked with `if(FULL_TESTS)`. Before this, `if(DEFINED FULL_TESTS)` meant `-DFULL_TESTS=OFF` also turned the set on.
- CI: set `FULL_TESTS=ON` on Linux, so `test_mesh_multi_block`, `test_exchange_decomp` and `test_shallow_splash_decomp` run (the ucx/cuda variant skips). Exclude `test_shallow_xy_decomp`, which takes 332-433 s locally.

Measured on a CUDA build: `ctest -N` 68 -> 71 (`FULL_TESTS=ON`: 73 -> 76). The 68 executed tests keep the same verdicts (66 pass; `test_eos` and `test_exchange_ucx_cuda` fail on main too).

Closes #224

---

## CI and review

Measured by the upstream owner's reviewing agent on the combined head as it stood at `e677147` (the later revisions change only documentation text, one test assertion and test formatting):
- CUDA build, `ctest -j 1`: 68/69. The one failure is `test_exchange_ucx_cuda`, "invalid device ordinal" with one GPU visible, and it fails the same way on main.
- CPU-only build: 68/68.
- All 8 commits' patch-ids match the individually reviewed branches.

The head is now `7f6b1b5`: those 8 commits plus the #224 commit `85c44b3` from `fix/224-register-tests`, cherry-picked with its code unchanged (same patch-id, author kept); only an automated-tool trailer was dropped from its message. Review then added `03f208d` (kintera >= 2.5.0 and the uv-solver test), so the head is `03f208d`.

Upstream CI on the current head: runs on this PR.



## PR #230: eos: repair a negative parentless cloud within its column, keeping the column mass

Merged 2026-09-27; merge commit `80b85b5`.

Fixes #229.

## Merge summary

**eos: a parentless cloud borrows its deficit along the column.** Numbers change only where a cloud species with no nucleation parent (for example precipitation made by coagulation) goes negative.

- **Problem.** `apply_conserved_limiter_` clamped such a cloud to zero cell by cell, which creates mass equal to the deficit it removes.
- **How found.** A reading of the conserved limiter code (#229), confirmed by a failing test on main.
- **Fix.** Parentless clouds go through the same columnar repair vapor already uses (`call_fix_vapor`, dry air as the weight). Clouds with a parent vapor are unchanged. Zeroing remains only when a column's rounded total of that species within the meshblock is strictly negative.
- **Tests, red to green.** `tests/test_parentless_cloud`, 3 cases. On main plus the first case alone, all 4 arms (cpu/cuda x Float/Double) fail with "created 1.0 of the deficit". On the head, all 12 arms (3 cases) pass on a V100.
- **What review caught.** An independent review agent found that a column with a negative total is still clamped, which creates mass. That exception is now documented and tested. It then found that the comment said "non-positive" where the code gives up only on a strictly negative total. The comment now states the exact condition, and a zero-total case was added.
- **Full ctest -j1, head vs main `c8d9824`, same rig.** No new failures on CPU or a V100. No CUDA-skipped test on the V100.
- **CUDA gate at `5c43ae9`** (the upstream owner's reviewing agent, RTX 5090, CUDA Release, sm_120): test_parentless_cloud 12/12, all 6 cuda arms on device; full ctest 72/72 with both GPUs visible, main `c8d9824` 71/71; no skipped cases.
- **Status.** Head `5c43ae9` (rebased onto main `c8d9824` after #225; range-diff vs `b1bf6ac` all '='), CI run 36336463785 green.
- **Review.** Both reviewers approved `b1bf6ac` before the rebase. At `5c43ae9` (a pure rebase), the upstream owner's reviewing agent re-signed (CUDA gate); the independent review agent re-read the range-diff and its reading stands, with its formal re-sign waiting on its own runtime check.
- **Size.** 4 files, +219/−2 (`src/eos/equation_of_state.cpp` +28/−2; tests +191).
- **Limits.** The repair is per meshblock. A column whose total within the meshblock is strictly negative is still clamped, as before this PR.
- **Suggested squash message:** `eos: a parentless cloud borrows its deficit along the column`

---

## Summary

- **Problem.** `apply_conserved_limiter_` repairs a negative condensate by borrowing from its nucleation parent vapor. A cloud species that no nucleation reaction produces (for example precipitation made by coagulation) has no parent, so it was clamped to zero cell by cell. That adds back 1.0x the deficit: the clamp creates the mass it removes from the negative.
- **Change.** Parentless clouds now go through the same columnar repair vapor already uses: `call_fix_vapor` over the cloud slots, with dry air as the weight. A negative cell takes its deficit from the same species elsewhere in the column, and the column mass is kept. Clouds with a parent vapor are unchanged: they are non-negative by that point and pass through. The repair is per meshblock and scans each column from the top. It falls back to zeroing only when the column's rounded total of that species within the meshblock is strictly negative; a zero total is repaired. The clamp then adds mass equal to the remaining deficit, as the old per-cell clamp did.

## Tests

`tests/test_parentless_cloud` has three cases, each on cpu/cuda x Float/Double:
- `repair_keeps_the_column_mass` over-drains rain in one cell of an 8-cell column. The column's total mass must be unchanged, rain non-negative and dry air untouched.
- `negative_column_is_clamped` sets all interior rain to 0 except one cell at -1e-4. Rain must end non-negative and dry air unchanged, and the column mass rises by exactly 1e-4: the documented fallback.
- `zero_column_is_repaired` puts -2^-13 and +2^-13 in one column, with the negative cell first below and then above the positive one. Both placements must end with rain all zero, dry air unchanged and a column-mass change of exactly 0.

```
main dcb3f7d + first case only: RED in all 4 arms (cpu/cuda x Float/Double): "created 1.0 of the deficit"
head 5c43ae9:                   GREEN in all 12 arms on a V100 (3 cases x cpu/cuda x Float/Double)
                                CPU build: the 6 cpu arms pass, the 6 cuda arms are skipped
                                (the first case also passed on a Quadro RTX 4000, the fix author's run)
full ctest -j1, head vs main c8d9824, same rig:
  CPU  build: main 62 of 70 pass, head 63 of 71; the same 8 failures on both
  V100 build: main 62 of 69 pass, head 63 of 70; the same 7 failures on both; no CUDA-skipped test
CUDA gate, RTX 5090 (the upstream owner's reviewing agent; CUDA Release, sm_120, torch cu128):
  test_parentless_cloud 12/12 on the GPU, all 6 cuda arms on device, none skipped
  test_condensate_conservation 4/4
  full ctest: head 72/72 and main c8d9824 71/71 with both GPUs visible; on one GPU each
  fails only test_exchange_ucx_cuda, a 2-rank test ('invalid device ordinal')
  a verbose rerun of the 8 binaries that can skip showed no skipped cases
```

The failures common to main and the head are multi-process tests that fail on our test machine in the same way on main: `test_exchange`, `test_output_barrier`, `test_check_redo_parallel`, `test_straka`, `test_shallow_xy`, `test_shallow_splash` and `test_restart_cycle_limit`, plus `test_exchange_ucx` on the CPU build (not registered on the V100 build, which has UCX off).

## Provenance

Five commits on main `c8d9824`, rebased after #225 merged (range-diff vs `b1bf6ac` all '='):
- `326cb9b` tests: repairing a cloud with no nucleation parent keeps the column mass
- `02ff810` eos: a parentless cloud borrows its deficit along the column (author: the upstream maintainer)
- `e503b82` eos, tests: document and test the parentless-cloud clamp fallback (author: the upstream maintainer)
- `0764291` eos, tests: state the parentless-cloud fallback condition exactly (author: the upstream maintainer)
- `5c43ae9` style: clang-format the zero-column test's cons allocation

## CI and review

Upstream CI on the head `5c43ae9` (on main `c8d9824`): run 36336463785 green (pre-commit, ubuntu, macOS).

- **The independent review agent, at `9d0f6a0` (an earlier revision, now `02ff810`):** changes. The fallback still clamps a column whose own total is negative, which creates mass. In answer, `e503b82` accepts that exception, says so in the comment and tests it (`negative_column_is_clamped`). Before this PR every such cell was clamped, so that case is unchanged, not a regression.
- **The independent review agent, at `0a51d76` (an earlier revision, now `e503b82`):** changes. The comment said a non-positive total is left unrepaired, but the code gives up only when its working-precision total is strictly negative. In answer, `0764291` rewords the comment and adds the zero-total boundary (`zero_column_is_repaired`). There is no behaviour change.
- **Before the rebase:** SIGN-OFF approve from the independent review agent and the upstream owner's reviewing agent (RTX 4000 + CPU) at `b1bf6ac`.

**Sign-offs at `5c43ae9`.**
- The upstream owner's reviewing agent: SIGN-OFF approve at `5c43ae9` (CUDA gate on the RTX 5090)
- The independent review agent: re-read the range-diff at `5c43ae9` (all five patches identical); its code-review reading stands. Its formal re-sign waits on its own runtime check, which its environment cannot run at present.
- A second independent review agent: offline; a second GPU check on a V100 stands in for it (above), and it reviews post hoc when back



## PR #231: sedimentation: a rising particle takes its flux from the cell it leaves

Merged 2026-09-27; merge commit `bf66ec3`.

Fixes #228.

## Merge summary

- **Problem:** a rising particle (vsed > 0) took its sedimentation flux from the cell above the face instead of the cell it was leaving. All three sedimentation code paths (the fused CPU/CUDA kernel, the tensor fallback and the MPS path) built face i from cell i whatever the sign of vsed, and walls were sealed by zeroing cell velocities.
- **How found:** filed as #228 with a failing test; every shipped card sets `const-vsed < 0`, so no shipped example reaches it, but a positive `const-vsed`, a positive grav1 or Stokes settling of particles lighter than the gas does.
- **Change:** face i takes cell i for settling particles and cell i-1 for rising ones. The kernel runs one thread per face and reads both neighbours, so no two threads write one face; the tensor and MPS paths share a small upwind helper (`sedimentation_upwind`). Walls are sealed on faces, so nothing enters through the bottom. `psed->vsed` now holds the velocity each face carries; for settling it is unchanged. Fix author: the upstream maintainer.
- **Tests:** `tests/test_sedimentation_guards` gains `rising_cloud_is_taken_from_the_cell_below` (plus a `_cuda` twin): a resting column with a per-cell cloud and `const-vsed` +2, each interior face must carry rho*y*vsed and its energy from cell i-1, and both walls exactly 0.
- **Red -> green:** red on main: 10 failing checks per device (mass and energy at interior faces 3-7), on CPU, a V100 and an RTX 5090. Green: all sedimentation cases pass on CPU, the V100 and the RTX 5090.
- **Full ctest -j1 at `fe5470f`:** RTX 5090 (the upstream owner's reviewing agent's CUDA gate): 70/70 enabled, no CUDA-skipped cases, `test_sedimentation_guards` 4/4 including the GPU arm. CPU: main `80b85b5` and head both 63 of 71 pass; V100: both 63 of 70. The failing sets are identical to main's in the same environment (environment-only multi-process/port failures), so the fix changes nothing else.
- **Cross-check:** the new test exercises the fused kernel; a separate (uncommitted) comparison of the fused kernel against the tensor fallback, rising and settling, CPU and CUDA, agreed to 1.5e-11 on fluxes of about 1.3e5.
- **Review:** the upstream owner's reviewing agent: SIGN-OFF approve at `fe5470f` (CUDA gate on the RTX 5090); an independent review agent: SIGN-OFF approve (code review) at `fe5470f`, resting on CI run 36343185946 and the RTX 5090 CUDA gate. Both reviewers reproduced the replayed tree independently.
- **Size:** +154/-41 in 5 files: `sed_hydro_impl.h` +57/-23, `sed_hydro.cpp` +10/-12, `sed_hydro_dispatch.cpp` +9/-6, `sed_hydro_dispatch.hpp` +17, `tests/test_sedimentation_guards.cpp` +61.
- **Status:** head `fe5470f507035ad2169ab282cd18fa9f084655a0` on main `80b85b5`, replayed after #230 merged: range-diff vs `8c45988` is '=' '!' '=', where the '!' is context only (#227's `ICY` lines next to the fix; the fix's own lines are identical), and the tree is the one both reviewers reproduced. CI run 36343185946: green.
- **Limits and follow-ups:** the MPS path was not run (no Apple GPU); no test mixes rising and settling species in one column. Both are follow-ups.
- **Squash message:**
```
sedimentation: a rising particle takes its flux from the cell it leaves (#228)

Face i now takes cell i for settling particles (vsed < 0) and cell i-1 for
rising ones (vsed > 0) in the fused kernel, the tensor fallback and the MPS
path; walls are sealed on faces. Settling fluxes are unchanged.
```

## Commits

Three commits on main `80b85b5`:
- `f8da885` tests: a rising cloud (const-vsed > 0) is taken from the cell below the face
- `1b915b7` sedimentation: take each particle's flux from its upwind cell (#228) (author: the upstream maintainer)
- `fe5470f` style: clang-format sedimentation_donor_impl's rising call (whitespace only)

## Files

```
M	src/sedimentation/sed_hydro.cpp
M	src/sedimentation/sed_hydro_dispatch.cpp
M	src/sedimentation/sed_hydro_dispatch.hpp
M	src/sedimentation/sed_hydro_impl.h
M	tests/test_sedimentation_guards.cpp
```




## PR #235: eos, sedimentation: a block reads its own species table after a second card is loaded; require kintera >= 2.5.8

Merged 2026-09-28; merge commit `a91403e`.

## Merge summary

**eos, sedimentation: after a second card is loaded, a block reads its own species table; snapy now requires kintera >= 2.5.8.** Fixes #234.

- **Problem.** kintera keeps a process-global species table, and loading a second card replaces it (the case kintera #121 fixed for kintera itself). Two snapy sites still resolved species through that global table after parse time: the EOS cloud-parent cache, and `SedVelOptions::species()`. After a second card is loaded, a block built from the first card gets the second card's names and cloud-parent split. Total mass is still conserved, but the split between vapours and the particle names are wrong.
- **How found.** A kintera #121 follow-up that was never filed; reported as #234 with a failing test.
- **Fix** (the upstream maintainer, `f4aabcb`). The EOS cloud-parent cache calls kintera's `populate_thermo` and reads the thermo's own `names()`/`mu()` by position, instead of resolving global ids. `SedVelOptions` stores the particle names it resolved at parse time in a new `particle_names` field, and `species()` returns them. The global lookup stays only in `SedVelOptions::from_yaml` (at parse time, correct by construction) and as a fallback for options built by hand with ids alone. `tests/test_eos_species_registry.py` reads the table on purpose; no other snapy site reads it. 3 files, +49/−21.
- **kintera minimum** (the upstream maintainer, `9040a5f`). The fix uses `SpeciesThermo::names()`/`mu()`, which first appear in kintera v2.5.8 (the #121 commit, `6a4aad9`); v2.5.7 has `populate_thermo` but not those. The minimum is raised to 2.5.8 wherever snapy declares kintera: `CMakeLists.txt` `find_package(Kintera 2.5.8 REQUIRED)` (was 2.5.0), a failure reason in `FindKintera.cmake`, `pyproject.toml` build-system and dependencies, `ci.yml` (was >= 2.5.0), the two `release.yml` pins (were >= 2.1.0), and `README.md` / `docs/installation.rst` (stated >= 1.1.5). 7 files, +15/−11.
- **Tests, red to green.** The test commit `e15ab06` adds `test_two_cards_species` (3 cases). On main, case 1 passes; case 2 `species()` returns `[NH4SH H2O(l)]` instead of `[H2O(l) NH4SH]`; case 3 the limiter debits H2O(l) from (H2O, NH3, H2S) as 0.333242 / 0.666758 / 0 instead of 1 / 0 / 0, and NH4SH as 0 / 0 / 1 instead of 0 / 0.333242 / 0.666758. The same verdicts on CPU and CUDA, float and double (float values equal to float rounding, e.g. -5.96e-08 for a 0).
  - the upstream maintainer's rig (Quadro RTX 4000, sm_75, nvcc 12.9, torch 2.10.0+cu128, kintera v2.5.10): red 16/24 on the CUDA build and 8/12 on CPU-only; green 24/24 and 12/12 at the final tree. Full `ctest -j1`: CPU-only 71/72 -> 72/72; CUDA 71/73 -> 72/73. The one remaining CUDA failure is `test_eos moist_mixture/cuda_Double`, an out-of-memory on the 8 GB card that fails identically on main.
  - A second rig (x86-64 CPU, kintera 2.5.10.dev4 `4814333`): both red claims reproduced on `e15ab06`; green in f32 and f64 on the head; full `ctest -j1` 8/72 failed, the same 8 as main on that rig (multi-process tests that fail there on main too), none extra.
- **Configure check.** Against kintera 2.4.7 and against 2.5.1.dev8, configure stops with `Could NOT find Kintera: Found unsuitable version ... Reason given by package: snapy requires kintera >= 2.5.8 (SpeciesThermo names()/mu(), kintera #121)`. Against 2.5.10 it configures. Note that CMake keeps only the leading X.Y.Z of the version, so a 2.5.8.devN install passes CMake but is refused by the PEP 440 pin.
- **CI.** Green on run 36367558340 (attempt 2, after kintera 2.5.11 reached PyPI): pre-commit, ubuntu-latest and macOS-latest. Both install the kintera 2.5.11 wheel and CMake reports `found suitable version "2.5.11", minimum required is "2.5.8"`; `test_two_cards_species` runs and passes on both (ctest 76/76 on Linux, 62/62 on macOS, the usual disabled/skipped entries aside). The first attempt failed only at the kintera install, before 2.5.11 existed on PyPI.
- **Commits.** 3 on main `bf66ec3`: test `e15ab06`, fix `f4aabcb`, minimum `9040a5f`. The two fix commits are the upstream maintainer's `1fa9ca1` and `98a243a` with the same trees; only a trailer line was dropped from the first.
- **Review.** An independent review agent: fresh line-by-line review of both commits, no blockers; its sign-off waits on the kintera release and green CI. The upstream owner's reviewing agent signs its own increment on the PR head.
- **Suggested squash message:** `eos, sedimentation: a block reads its own species table after a second card is loaded; require kintera >= 2.5.8`


## PR #242: config, layout, hydro: refuse an unknown YAML key per block, refuse a multi-tensor Gloo message, pin the moist-mixture carry gap (#233, #240, #236)

Merged 2026-09-28; merge commit `d061d82`.

Closes #233. Closes #240. Refs #236 (stays open).

## Merge summary
- Problem: (#233) a misspelled key in most YAML blocks is read as absent, so the run keeps the default without a word: `grav1` becomes 0, `nx2` becomes 1, a wall stays reflecting, a reconstruction or Riemann `type` falls back to `dc`/`roe`. (#240) on Gloo, a message of more than one tensor fails inside Gloo with "ProcessGroupGloo::send takes a single tensor", on a recv too, which does not say what to do. (#236) the positivity limiter's carry (#226) is skipped on moist-mixture.
- Fix: `check_keys()` (src/input/check_keys.{hpp,cpp}) compares a block's keys with the keys its reader reads and names the full path and the valid keys, like #227's check. It is called at the top of every snapy-owned fixed-key block: 29 blocks, listed below. `ProcessGroupContext::send/recv` refuse a multi-tensor Gloo message before it reaches Gloo and say to split it. #236 gets a comment at the call and a test that pins the gap.
- Tests: RED on the base, GREEN on the fix, per commit below (Linux x86 cluster, gcc 11.3, libtorch 2.6, UCX build, kintera 2.5.10.dev4). CUDA twins by a contributor, run on sm_90.
- Size: 10 commits, one test commit before each fix. No run changes: no deck in snapy or in our downstream decks uses a refused key (scan of 174 decks and the tests' inline YAML), and every current snapy send/recv already carries one tensor.
- Status: head d1f4d78; CI pending on this draft.
- Squash message: "config, layout, hydro: refuse an unknown YAML key per block (#233), refuse a multi-tensor Gloo message with the fix (#240), pin the moist-mixture carry gap (#236); CUDA twins for the cubed-sphere seams and one VIC step"

All full `ctest -j1` runs below fail the same 3 tests (test_shallow_splash, test_shallow_xy, test_straka); main 2249b4a fails exactly these 3 on the same machine (a cluster run, 72/75), so they are that machine's baseline, not this change.

## #233: an unknown key is refused
A misspelled key now stops the load with the key's full path and the valid keys, instead of silently running with the default.
- Step 1 (b332a85 test, 5762de5 fix): forcing/const-gravity, geometry/cells, boundary-condition/external. RED, the test on a91403e: `test_yaml_keys` 3 FAILED, the_card_itself_loads OK. GREEN, 5762de5: 4/4 OK; ctest 73/76 = baseline.
- Step 2 (0978d96 test, b7c1dff fix): dynamics/reconstruct and its vertical and horizontal blocks, dynamics/riemann-solver, forcing/{coriolis, diffusion, body-heat, top-cool, bot-heat, relax-bot-comp, relax-bot-temp, relax-bot-velo, top-sponge-lyr, bot-sponge-lyr, plume-forcing}, geometry, geometry/bounds, outputs/<i>, boundary-condition, boundary-condition/internal, scalar, scalar/reconstruct, scalar/riemann-solver, sedimentation, distribute. RED, the test on cf81e58: `test_yaml_keys` 4 OK, 25 FAILED (each loaded with the unknown key). GREEN, b7c1dff (same job): 29/29 OK; ctest 73/76 = baseline.
- Step 3 (99896ec test, d1f4d78 fix): integration, which pyharp's integrator also reads; the check lists pyharp's keys by name (type, cfl, tlim, nlim, ncycle_out, verbose; pyharp integrator.cpp, the same in 2.6.5 and 2.7.0), as #227 does for kintera. A misspelled `cfl` ran at pyharp's default 0.9. RED, the test on 2c910b3: `test_yaml_keys` 29 OK, 1 FAILED (integration_refuses_an_unknown_key: `CFL` loaded without a word). GREEN, d1f4d78: 30/30 OK; ctest 76/79 = baseline.
- Each key list is the set its reader reads, checked against the source. `distribute` still accepts `backend` (dead since #181; the backend comes from the BACKEND environment variable), because 3 snapy tests and many downstream decks still write it. forcing/diffusion keeps its specific message for the legacy `K` and `type`.
- Not checked: the top level (an open set that kintera, pyharp and the drivers also read) and the species-name maps under sedimentation (radius, density, const-vsed), where an unknown species is already refused.

## #240: a multi-tensor Gloo message is refused with the fix (7804eba test, bd18aa5 guard)
On Gloo, ProcessGroupContext::send/recv refuse a message of more than one tensor before it reaches Gloo and say to split it into one message per tensor. Every current snapy call site already sends one (layout.cpp `exchange_each_var`, the hydro_forward.cpp seam flux, the hydro.cpp well-balanced ghosts), so no run changes. The test is registered on macOS only, because Gloo is the Mac backend and Linux runs UCX.
- RED: the test on a91403e: `test_gloo_one_tensor` FAILED at test_gloo_one_tensor.cpp:38, 4 times (2 ranks x send, recv); Gloo's message was "ProcessGroupGloo::send takes a single tensor".
- GREEN: the guard (a cluster run, on 78be511 = bd18aa5 before the macOS-only wrap): `test_gloo_one_tensor` Passed; ctest 74/77 = baseline. With the wrap, the Linux build registers no test_gloo_one_tensor (a cluster run, 79 tests), and macOS CI runs it.

## #236: the moist-mixture carry gap, pinned (cf81e58)
moist-mixture defines no species_enthalpy, so the carry is skipped and its withheld species mass keeps no energy or momentum. A comment names this at the call, and `flux_positivity.moist_mixture_withholds_no_energy_or_momentum_yet` pins it: on moist-mixture the advected column limits its faces while the energy and momentum fluxes equal the unlimited run's. It fails the day the carry reaches moist-mixture, and its message says to check it with `expect_carried`. Hydro::forward has no Python binding, so this is a gtest in #226's harness rather than a pytest xfail; it keeps the strict-xfail contract.
- On this commit: the test is OK, with all 6 carry tests; ctest 74/77 = baseline.
- Not vacuous: with a local-only stub where moist-mixture's species_enthalpy returns 0 (so the carry runs), it FAILS at faces 3 to 6: "moist-mixture now withholds carried energy or momentum; #236 is fixed, check it with expect_carried(off, on)".

## CUDA twins (2c910b3, by a contributor)
test_vic_moist_device (one moist step, implicit scheme on CPU and CUDA), test_flux_positivity_cubedsphere_cuda and test_flux_positivity_cubedsphere_moist_cuda. On sm_90 (cuda:0): test_vic_moist_device passed, max|cpu-cuda| 5.821e-11 (bound 1e-9); the dry seam twin passed, drift 2.238e-15; the moist seam twin passed, drift 1.796e-15. Without a GPU each exits 125 and ctest skips it: on the CPU build the three are Skipped and their CPU siblings test_flux_positivity_cubedsphere and _moist pass (5/5, 0 failed).

## Limits
- plume-forcing is parsed only under plume-eos; a block under another EOS is still dropped silently.


## PR #243: eos, hydro: fix_vapor conserves column mass on a grid of varying cell volume; the ghost species enthalpy is computed, not exchanged (#241, #238)

Merged 2026-09-28; merge commit `bf8d139`.

Closes #241. Closes #238.

## Merge summary
- Problem: (#241) the columnar repair of a negative vapor or parentless cloud (fix_vapor) conserves the column sum of density, not of mass: it has no cell-volume weight, so on a grid whose x1 cell volume varies, a repair changes the column's mass. (#238) the positivity limiter's carry exchanged the species enthalpy with theta, although the ghost value is species_enthalpy() of the ghost's own w.
- Fix: fix_vapor weights each cell by its volume relative to the column's first cell, in the sums, in the redistribution and when it takes a shortfall from above; both call sites (vapor and parentless cloud) pass the cell volumes, on CPU and CUDA. The species enthalpy is computed from w, ghosts included, and no longer exchanged.
- Numbers change: #241 only, on grids whose x1 cell volume varies (gnomonic-equiangle, spherical-polar, non-uniform x1), and only in cells a vapor or parentless-cloud repair touches. Size: on the test's spherical-polar column (8 cells, volume growing 6.5 times) one repair changed the column's vapor mass by 8.05e-2 relative before the fix and by at most 2e-16 after (float64); on the shipped examples/jupiter_gcm.yaml deck the issue measured 1.2e-4 relative for one repair, and a 40-cycle run fired the repair twice. A uniform grid is bit-identical: every weight is exactly 1. #238 changes no bit.
- Tests: RED on main, GREEN on the fix (Linux x86 cluster, gcc 11.3, libtorch 2.6, UCX build, kintera 2.5.10.dev4).
- Size: 3 commits.
- Status: head 10235df, replayed onto main d061d82 after #242: 021a1da -> f8962d7, 60dbeda -> b4503f1, 0c2fde5 -> 10235df, patches unchanged (range-diff all `=`); CI run 36476240038. The evidence below names the commit each run used. On the replayed head: `test_fix_vapor_volume` 2/2, full `ctest -j1` 77/80, the baseline 3.
- Squash message: "eos, hydro: fix_vapor conserves column mass on a grid of varying cell volume (#241); compute the ghost species enthalpy instead of exchanging it (#238)"

All full `ctest -j1` runs below fail the same 3 tests (test_shallow_splash, test_shallow_xy, test_straka), as main 2249b4a does on the same machine (72/75): that machine's baseline, not this change.

## #238: the species enthalpy is not exchanged (f8962d7, was 021a1da)
We drop hydro_hspec from the exchange and recompute it from species_enthalpy(w); output bit-identical (36 tensors, 6 panels, a cluster run). w's ghosts are filled before the hydro step reads them (exchange and boundary functions after every stage), so species_enthalpy(w) covers them. Each exchange stage sends one message fewer per remote peer.
- Re-measured on this head's base: the six-panel moist cubed-sphere deck of test_flux_positivity_cubedsphere_moist, with the limiter firing 139 times at panel seams, on main 2249b4a and on 021a1da: every conserved and primitive tensor of all 6 panels is bit-identical after the run (36 tensors), in the limited and the unlimited arm. Full `ctest -j1` on 021a1da: 72/75, the baseline 3.

## #241: fix_vapor conserves column mass (b4503f1 test, 10235df fix; were 60dbeda, 0c2fde5)
`test_fix_vapor_volume`: one negative cell in a spherical-polar column (r from 1 to 3, 8 cells, cell volume growing 6.5 times), covered by the cells below, repaired through apply_conserved_limiter_ for a vapor and for a parentless cloud; the column's sum(rho q V) must hold to 1e-12. A Cartesian control must pass on both sides and equal the old repair bit for bit.
- RED, the test on 2249b4a: `test_fix_vapor_volume` FAILED at test_fix_vapor_volume.cpp:84 for the spherical-polar column, float64 and float32, vapor and parentless rain alike: relative change of sum(rho q V) = 8.05e-2. The Cartesian control passes (float64: 0; float32: -2.1e-9, round-off).
- GREEN, 0c2fde5 (same job): `test_fix_vapor_volume` 2/2 OK: spherical-polar relative change 1.9e-16 (vapor) and -1.2e-16 (rain) in float64, -5.7e-9 and -5.4e-9 in float32; the Cartesian control is unchanged (float64: 0) and equals the old repair bit for bit. test_eos 11/11 and test_parentless_cloud 6/6 OK. Full `ctest -j1` 73/76, the baseline 3.
- CUDA (sm_70, a CUDA build of 0c2fde5; two cluster runs; nvcc 12.2, libtorch 2.6): `test_fix_vapor_volume` runs on cpu and cuda, float64 and float32, and passes 4/4. Counter-check: with a local-only stub that passes a uniform volume in the CUDA dispatch (eos_dispatch.cu), its cuda cases FAIL and its cpu cases pass, so the test catches a CUDA-only regression. test_eos 17/17 (moist_mixture on cuda, float64, passes on this GPU), test_parentless_cloud 12/12, test_fix_vapor_reports_failure_cuda passes; full `ctest -j1` fails only the baseline 3. A CUDA run by a reviewer is still owed.

## Limits
- The weight is relative to the column's first cell, so a uniform column is bit-identical; a Cartesian grid whose x1 spacings differ in the last bit (faces from a mesh generator) can move at that level.


## PR #244: eos, layout: repair a negative parentless cloud over the whole x1 column when it spans meshblocks (#232)

Merged 2026-09-29; merge commit `9378f06`.

Closes #232. Closes #246 (carried, see Carried fix). #243 (fix_vapor weighted by cell volume, #241) merged as bf8d139; this PR is replayed onto it.

## Merge summary
- Problem: the columnar repair of a negative parentless cloud (a condensate with no nucleation parent, e.g. rain) sees only its own meshblock's part of each x1 column. With the column split along x1 (nb1 > 1), the lower block finds too little rain above, the kernel's failure code is ignored for the cloud slots, and the clamp that follows creates mass equal to the deficit: +1.000e-4 with nb1 = 2 against 0.0 with nb1 = 1, on CPU and CUDA, float32 and float64.
- Fix: when a block's x1 column spans meshblocks, each block gathers the whole column (cloud, major density, cell volume; `LayoutImpl::gather_x1`, same-process blocks through a shared board, other processes through one send/recv per piece), runs the existing kernel on it and keeps its own part. Every block computes the same result, so no scatter is needed. The clamp still follows and now fires only when the whole column is short, the exception documented and tested in test_parentless_cloud. `apply_conserved_limiter_` takes a `whole_column` flag, set only by the two calls in `MeshBlockImpl::advance_local`; every other call, and nb1 = 1, is unchanged.
- Numbers change: for nb1 > 1 decks with a parentless-cloud repair, which now scans the global column as nb1 = 1 does (the mass it created at a block boundary disappears, and a repair may now draw on cells across the boundary); nb1 = 1 is bit-identical (the kernel receives the same tensors).
- Tests: RED on the base, GREEN on the fix (Linux x86 cluster, gcc 11.3, libtorch 2.6, UCX build, kintera 2.5.10.dev4).
- Size: 5 commits (the red test by the upstream maintainer, our fix, the test's entry point, the two-process test, and the upstream maintainer's #246 test-grid fix); +133/-19 over the test, plus the two-process test (+91) and the #246 fix (+1/-1).
- Status: head 0fecbb8 = f7927cf's 4 commits replayed onto main bf8d139 (#243 merged): 90faa48 -> 4687bcb, 121add8 -> 8719376, 83b3b07 -> 947d27c, f7927cf -> 52fd3aa, patches unchanged (range-diff all `=`), plus 0fecbb8 = the carried #246 fix. Earlier: d2a52cd -> 90faa48, 649d921 -> 121add8, cf811bd -> 83b3b07 (replay onto #243 10235df on main d061d82); CI run 36476266345 on 83b3b07. On 0fecbb8: `test_parentless_cloud_nb1` 4/4, `test_parentless_cloud_nb1_mp` passes on UCX and on Gloo, `test_fix_vapor_volume` 2/2, `test_eos` 11/11 (CPU), full `ctest -j1` 80/83, failing only the baseline 3. The evidence below names the commit each run used. On the replayed head: `test_parentless_cloud_nb1` 4/4, full `ctest -j1` 78/81, the baseline 3.
- Squash message: "eos, layout: repair a negative parentless cloud over the whole x1 column when it spans meshblocks; test_eos fits an 8 GB GPU (#232, #246)"

## Evidence
- RED, d2a52cd = the failing test (by the upstream maintainer) on the base: `test_parentless_cloud_nb1`: nb1 = 1 passes (float64, float32); nb1 = 2 FAILS, total mass changed by +1.000e-4 = the whole deficit (float64 0.99999999999767, float32 0.99999997 of it).
- GREEN, cf811bd: `test_parentless_cloud_nb1` 4/4 OK (nb1 = 1 and 2, float64 and float32); test_parentless_cloud 6/6 and test_fix_vapor_volume 2/2 OK.
- Two processes (f7927cf, `test_parentless_cloud_nb1_mp`): the same column with one block per process on two ranks, so the gather must go through the process group; registered for UCX (`setup_parallel_test`) and, where UCX is built, again on Gloo. RED, the test on #243's head 10235df: FAILS on UCX and on Gloo, each rank's rain mass changed by +1.000e-4 = the whole deficit. GREEN, f7927cf's tree: passes on UCX and on Gloo (rain and total mass held to 1e-12), `test_parentless_cloud_nb1` 4/4, full `ctest -j1` 80/83, the baseline 3.
- Full `ctest -j1` on cf811bd: 74/77, failing only the baseline 3 (the test machine's baseline is 3 failures: test_shallow_splash, test_shallow_xy, test_straka, which main fails identically).

## Carried fix: #246 (COLLAB v3.2)
- `95771b211973a2184c7812462fe578a3c3bedbd0` by the upstream maintainer (branch `fix/246-test-eos-oom`, base d061d82): `tests/test_eos.yaml` nx3 100 -> 25 (grid 402x402x102 -> 402x402x27, 16.5M -> 4.4M cells); dimensionality, nghost, species, checks and tolerances unchanged (the checks are pointwise).
- Before/after, from the fix's own measurement on an 8 GB sm_75 card (Quadro RTX 4000): on main, `test_eos` moist_mixture/cuda_Double runs out of memory in `torch::allclose` (7.6 GB); with the fix, `test_eos` 17/17 at 3.6 GB peak GPU memory, wall 16.7 s -> 5.1 s.
- Carried as 0fecbb8: 95771b2's patch byte for byte, author kept, message trimmed (no `Co-Authored-By` trailer; `Closes #246` is in this body). Match it by patch or tree, not by sha. CPU gate on 0fecbb8: `test_eos` 11 passed, 0 failed, and its 6 CUDA cases skip on the CPU node (17 in all).

## Why the test's entry point changes (83b3b07, was cf811bd)
The original test calls `apply_conserved_limiter_` on each block in turn, from one thread, on free-standing tensors. That is not how the model runs the repair: `Mesh::forward` runs `advance_local` for all blocks at once, one worker thread per block, and step (4) is where the repair happens. A block called alone cannot see the other blocks' part of the column, so no conservative fix can pass the original form, and a collective inside a serial call would deadlock. cf811bd keeps the test's setup and every assertion and changes only the call: one thread per block, as `Mesh::forward` does, with `whole_column = true` as `advance_local` passes it. The flag is opt-in because the limiter also runs inside every `U->W`/`W->U` conversion, including serial paths (restart initialisation, Python bindings) where a collective would hang.

## Limits
- A caller that runs `advance_local` block by block from one thread with nb1 > 1 now waits at the gather; serial `exchange_ghost_zones` calls already do the same.
- The two-process test covers two ranks with one block each; more ranks per column and more than one block per rank on a remote peer are covered only by the same code path, not by a test.
- CUDA: the gather synchronises the current stream as the existing exchange does. A reviewer's run on 83b3b07 (RTX 5090, built against kintera a8bef99): `test_parentless_cloud_nb1` 8/8 including cuda Float and Double for the split column, with `gather_x1` confirmed to run on the GPU; full `ctest` 82/82 (3 disabled). That run covers the same-process path; the two-process test runs on CPU, so the cross-process path has not run on CUDA.


## PR #248: mesh: check_redo redoes a step whose saturation adjustment failed; require kintera >= 2.5.13 (kintera #130)

Merged 2026-09-29; merge commit `69e0084`.

The snapy side of kintera #130: `check_redo` now acts on the saturation-adjustment failures that kintera #131 counts. Designed by a contributor's agent (its local branch fabbb3a, see Design source); written on main d061d82 and replayed onto main 9378f06 (#244 merged).

## Merge summary
- Problem: when kintera's saturation adjustment does not converge in a cell (for example `max-iter` reached in a strongly supersaturated NH4SH cell), the step was accepted as if the cell had been adjusted. Since kintera #131, `ThermoY` counts those cells (`take_saturation_adjustment_failures()`), but nothing in snapy read the count.
- Fix: `MeshBlockImpl::saturation_failures()` drains the count from the block's `ThermoY` (0 without one). Both `check_redo` (MeshBlock and Mesh) read it on every call as a fifth MAX-reduced flag, so one unadjusted cell in any block of the process group redoes the step with a smaller dt, like the floor, clamp, limiter and NaN causes. The redo message names the cause `saturation` (cause bit 16). Draining on every call means a failure is counted once, so the restored state is not redone again. `advance_local` also drains it when a step starts, beside `reset_limiter_marks`, so a failure counted between steps is not charged to the next step. On CUDA each drain reads one integer to the host, and only when kintera counted since the last drain.
- Kintera floor: `take_saturation_adjustment_failures()` is in kintera since #131, first released in v2.5.13 (kintera main a8bef99 = tag v2.5.13). The minimum rises from 2.5.8 to 2.5.13 in CMake (and in the `FindKintera` failure reason), `pyproject.toml` (build and run), the CI and release pip lines, and the installation notes, as #235 did for 2.5.8.
- Numbers change: only for a step in which the saturation adjustment failed somewhere. That step is now redone with a smaller dt. A run with no failed adjustment is unchanged: the flag stays 0.
- Tests: RED on the base, GREEN on the fix, on CPU and on a V100 CUDA build (below).
- Status: head ec71569 = 0437884's 4 commits replayed onto main 9378f06 (#244 merged), patches unchanged (range-diff all `=`): 47167e6 -> 3bd5b0e, ec4f929 -> 8327284, 8c058fe -> 94cd618, 0437884 -> ec71569. The evidence below names the commit each run used. On ec71569 (a cluster run, CPU, kintera a8bef99 = v2.5.13): `test_check_redo_saturation` passes every arm, `test_check_redo_floor` and `test_check_redo_parallel` pass, full `ctest -j1` 82/85, failing only the baseline 3.
- Size: 4 commits (the failing test, then the fix; then, from review, a failing test for a failure counted between steps and its fix); test +318, fix +43/-22 in 10 files (3 source files; the other 7 carry the floor), review test +33/-6, review fix +5/-3 in the same 3 source files.
- Squash message: "mesh: check_redo redoes a step whose saturation adjustment failed; require kintera >= 2.5.13 (kintera #130)"

## Evidence
All runs are on the Linux x86 cluster (gcc 11.3, libtorch 2.6). Each run names its snapy commit and the kintera it was built against.
- RED: 47167e6 = the test alone on d061d82, kintera a8bef99 (v2.5.13), CPU: `test_check_redo_saturation` FAILS in both arms that read the verdict: the max-iter 1 step leaves 11 failed adjustments and `MeshBlock::check_redo` returns 0, and with the cell in block 1 of the two-block Mesh `Mesh::check_redo` returns 0. The control arm (default max-iter: 0 failures, `check_redo` 0) passes. `test_check_redo_floor` and `test_check_redo_parallel` pass.
- GREEN: ec4f929, kintera a8bef99 (v2.5.13), CPU (cluster runs: build and the new tests, then the full suite on the same build): `test_check_redo_saturation` passes every arm: the max-iter 1 step (11 failed adjustments) is redone once with the cause `saturation` alone, `hydro_u` is restored, the count is drained to 0, and a second `check_redo` accepts the restored state; in the two-block Mesh, `Mesh::check_redo` redoes both blocks with `saturation` alone and then accepts; the control step is accepted. `test_check_redo_floor` and `test_check_redo_parallel` pass. Full `ctest -j1`: 78/81, failing only the test machine's baseline 3 (test_shallow_splash, test_shallow_xy, test_straka), which main fails identically.
- Review round, kintera a8bef99. RED: 8c058fe = the review test on ec4f929 (the runs built 4b00654, the same tree fce60f8 before an author-address fix). On CPU and on the V100 build the between-steps arm FAILS: one cell fails between the steps, then the clean step is redone with the cause `saturation`. Every other arm passes. GREEN: 0437884 (runs built d00f961, the same tree bea2537). Every arm passes on CPU and, on the V100 build, on `cuda` and on CPU. `test_check_redo_floor` and `test_check_redo_parallel` pass. Full `ctest -j1`: 78/81 on CPU and 77/80 on the CUDA build, failing only the baseline 3.
- CUDA: V100 (sm_70), kintera a8bef99 built for CUDA (it reports 2.5.14.dev0 only because the architecture edit dirties its tree), a cluster run, built with `compute_70,sm_70`: on ec4f929, `test_check_redo_saturation_cuda` passes every arm on `cuda` (11 failed adjustments, one redo with the cause `saturation` alone, then none; the Mesh arm likewise), and the CPU test passes on the same build. Full `ctest -j1`: 77/80, failing only the baseline 3 (this build has no UCX, so it registers one test fewer). On 47167e6 (the test alone, same build tree), the test FAILS on `cuda` in both arms (`check_redo` 0, `Mesh::check_redo` 0).

## The test
`tests/test_check_redo_saturation.py` puts kintera's own failing cell (from kintera's `test_saturation_failure_reported.py`: NH4SH about 150 times supersaturated, no cloud yet) into one interior cell of a 4x4 MeshBlock at rest, and runs one real RK3 step. The test has five arms:
1. With the default `max-iter`, the adjustment converges: 0 failures, and `check_redo` must return 0.
2. With `max-iter: 1` the same step must leave at least one cell unadjusted, so the test cannot pass vacuously.
3. The same step, read only by `check_redo`, must return 1 with the cause `saturation` alone and restore `hydro_u`. A second `check_redo` on the restored state must return 0.
4. A failure counted between steps: with `max-iter: 1`, the block's own `ThermoY` is run on the cell alone (its diagnostic must show the failure, so the arm cannot pass vacuously), then a step with no NH3 in the block, so nothing to adjust, must be accepted (`check_redo` 0).
5. A two-block `Mesh` in one process (nb2 = 2) with the cell in block 1 only: `Mesh::check_redo` must return 1 with the cause `saturation` alone, restore both blocks, and accept the restored state on the next call.
`test_check_redo_saturation_cuda.py` runs the same test on `cuda` and exits 125 (skipped) without a GPU, as `test_fix_vapor_reports_failure_cuda.py` does.

## Design source and cross-check
The design is a contributor's: their branch fabbb3a (`kintera130-saturation-redo`, on 0daab2a, not pushed) drains `take_saturation_adjustment_failures()` in `check_redo`, requests a rollback when the count is nonzero, and requires kintera >= 2.5.13. Its own run (CPU, kintera a8bef99): a C++ NH4SH regression, `test_saturation_adjustment_redo`, fails on its base (`check_redo` == 0) and passes at its head (exactly one redo, and the drained count does not cause another). This PR follows the same design: drain in `check_redo`, roll back on nonzero, floor 2.5.13, one redo then none. Its description does not mention the Mesh-level `check_redo` or a named cause in the redo message; this PR has both. The comparison is of the check_redo and rollback logic, not a tree diff, because fabbb3a is on another fork base. The contributor is asked to confirm the equivalence in review.

## Limits
- `saturation_failures()` finds the ThermoY by the module name `hydro.eos.thermo`, as `advance_local` already does. An EOS without a ThermoY reports 0, so the redo never fires for it.
- The count covers every `ThermoY::forward` from the start of the step to `check_redo`. In snapy the only call in a step is `advance_local`'s saturation adjustment (step 6, last stage). A failure counted between steps (for example a `ThermoY` call from Python) is discarded when the next step starts, and is not reported anywhere else.
- A failure that a smaller dt cannot fix now ends the run: every redo fails again, and after `max_redo` redos the run terminates, where the base accepted every step. Measured by the upstream maintainer's agent in its review (`max-iter: 1`, 5 steps): on this PR 0 steps accepted, 5 redos with dt 2.1e-4 -> 6.6e-6, then terminated; on the base, 5 steps accepted. This is deliberate: an unadjusted cell is treated like the other redo causes, and the run stops cleanly (`check_redo` returns -1, outputs and restart files kept) rather than carrying a supersaturated cell forward, as the base did silently. A run that stops this way can be restarted with a larger `max-iter`.
- The between-steps arm calls `ThermoY.forward` on the block interior, the shape `advance_local` passes. With a different shape, kintera up to a8bef99 reuses its warm-start buffers, and the next step reads past them (kintera #132). The test does not depend on that fix.
- The Mesh arm runs two blocks in one process. Across processes the flag goes through the same MAX allreduce as the other four causes (`test_check_redo_parallel`), but no multi-process run has a saturation failure in it.


## PR #249: forcing: an x1 profile for the kinematic diffusion coefficients, from Python or a YAML table

Merged 2026-09-29; merge commit `f24576b`.

forcing.diffusion takes an x1 profile of the kinematic nu_iso / kappa_iso, from Python or from a YAML table. #216 left this out because it had no YAML form and no test; this PR adds both.

Closes #251: CUDA reconstruction (WENO5, WENO3, polynomial degree 3 and 5) on a line longer than 1024 cells. Fix by a contributor's agent (1c1cc0e, failing test 3c25c49), carried here unchanged.

## Merge summary
- Problem: the kinematic diffusion flux is `-nu_iso * rho_face * stress` and `-kappa_iso * (rho cv)_face * dT/dn`, with one `nu_iso` and one `kappa_iso` for the whole domain. A coefficient that varies with height could only take one representative value. For example, constant dynamic viscosity on a polytrope is nu(z) = nu_t / rho0(z) (Anders & Brown 2017), which `dynamic: true` does not cover when the kinematic form is wanted.
- Fix: `nu_scale_x1` / `kappa_scale_x1` multiply `nu_iso` / `kappa_iso` by a positive profile in x1. There are two ways to give it:
  - YAML, under `forcing.diffusion`: `nu_scale_x1: {x1: [...], scale: [...]}` (and `kappa_scale_x1` likewise). The knots are in the x1 coordinate; the profile is linear between them and held constant beyond the ends. At `reset` it is interpolated onto the block's x1 cell centres, ghosts included, so the same table works for any resolution and any split of x1 into blocks.
  - Python: the same table as a (2, n) float64 tensor, `nu_scale_x1_table` / `kappa_scale_x1_table`; or, when one block spans x1, a float64 tensor over the block's x1 cell centres, ghosts included (`options.hydro().diffusion().nu_scale_x1(t)`). Either is set on `DiffusionOptions` before the `MeshBlock` is built.
- How the profile reaches the faces: both forms end as one per-cell profile. In the interior, the profile and the density (or rho cv) are averaged to the face separately and multiplied. At a physical x1 wall, their product is extrapolated from the two nearest active cells, as the unscaled coefficient already is. So a table and the same values given per cell give the same flux bit for bit.
- Time step: `max_time_step` bounds with `nu_iso * max(nu profile)` and `kappa_iso * max(kappa profile)`.
- Refused: a table with fewer than two points, lengths that differ, x1 not strictly increasing, a scale that is not finite and positive, or an unknown sub-key (all at YAML parse); a per-cell tensor of the wrong length, dtype or sign; a per-cell tensor when x1 is split into more than one block (every block shares the options, so each would take the same block-sized profile; the error points to the table); both forms for one coefficient; either with `dynamic: true`; a profile set, replaced, cleared or written into after the block is built, or `dynamic` set to true beside it (at the next `forward` or `max_time_step`, the two entry points that read the cached profiles, through one check: reset keeps the option tensors, their version counters and a copy of their values, so a write through a NumPy array behind `torch.from_numpy` or through `.data`, which bumps no version, is caught by comparing the values); an inference tensor, per cell or as a table (it keeps no version counter, so a later in-place write under `torch.inference_mode()` could not be detected; a YAML table is always built as an ordinary tensor).
- Carried (c7131ae): every evaporation reaction in `examples/*.yaml` set `diff_T: 0, diff_P: 0`, which holds kintera's evaporation diffusivity D = diff_c (T/300 K)^diff_T (P/1e5 Pa)^diff_P at diff_c at every height. They now take kintera's defaults 1.75 and -1, the gas-kinetic D ~ T^1.75 / P (11 reactions in 5 files). The rate also scales with the condensate's molar volume vm, and three non-water condensates carried water's 18e-6 m^3/mol. They now take their own: NH3(s) 20.8e-6 (17.03 g/mol / 0.82 g/cm^3) and NH4SH(s) 43.7e-6 (51.11 g/mol / 1.17 g/cm^3) in jupiter_crm and jupiter_gcm, and H2S(l) 35.9e-6 in uranus (34.08 g/mol / 0.950 g/cm^3, the saturated liquid at its normal boiling point, 212.2 K, NIST Chemistry WebBook). jupiter_evap_precip_1d already had its own values (NH3(s) 25e-6, NH4SH(s) 43e-6) and keeps them. `tests/` is unchanged, and no test loads these files.
- Carried (#251; 688cda4 + aca9b51 by a contributor's agent, ba4e83f): `stencil_kernel` launches one CUDA thread per cell of a line, and a CUDA block holds at most 1024 threads, so a reconstruction line of 1025 cells or more failed on CUDA with "invalid configuration argument". A line of up to 1024 cells keeps that launch. A longer line stays one block per line and walks it in tiles of up to 256 outputs, loading each tile's inputs plus the stencil overhang into shared memory (at most 48 KB; the tile halves until it fits) and calling the same shared-memory weights (`recon_tile_width`, `stencil_kernel_tiled`, `interp_line_tiled` in `src/recon/`). ba4e83f is formatting only (clang-format on the new test, which pre-commit asks for).
- Numbers change: none from the profile unless one is set; with one set, only the diffusion fluxes and the diffusion time-step bound change. The shipped examples' evaporation rates now depend on T and P (the carried commit below): earth_crm, jupiter_crm, jupiter_gcm, jupiter_evap_precip_1d and uranus change wherever their clouds evaporate. #251 changes no number on CPU or on a CUDA line of up to 1024 cells (the same launch); a longer CUDA line, which failed before, now matches CPU.
- Tests: RED on main, GREEN here, on CPU and on a V100 CUDA build (below).
- Docs: the four options in `docs/api/forcing.rst` and `python/snapy/forcing.pyi`, the YAML table in `docs/user_guide/configuration.rst`.
- Size: 10 commits (7 for the profile: the failing tests, the feature, the carried examples fix, the review fixes: split-x1 refusal, change-after-build refusal, the nb1 tests and the docs, the inference-tensor refusal, the same change check at `max_time_step`, then the value comparison; 3 for #251: the failing test, the fix, the formatting); tests +816 in 3 files (`tests/test_diffusion_x1_scale.{cpp,py}`, `tests/CMakeLists.txt`), feature +280/-8 in `src/forcing/diffusion.cpp`, `src/forcing/forcing.hpp`, `python/csrc/pyforcing.cpp`; docs +96/-3 in 3 files; examples +11/-11 in 5 files; #251: test +55 then +111/-22 and +3/-5 in `tests/test_weno5_cuda_line.cpp` and `tests/CMakeLists.txt`, fix +237/-19 in `src/recon/interp_impl.cuh` and `src/recon/recon_dispatch.cu`.
- Squash message: "forcing: an x1 profile for the kinematic diffusion coefficients, from Python or a YAML table; recon: tile CUDA lines longer than 1024 cells (#251)"

## Evidence
All runs are on the Linux x86 cluster (gcc 11.3, libtorch 2.6, kintera a8bef99 = v2.5.13), on main 9378f06, except the replay line.
- Replay onto main 69e0084 (#248 merged): head 28721fd = ba4e83f's 10 commits replayed, patches unchanged (range-diff all `=`), tree 5c570ea. Before the merge the same replay onto #248's signed head ec71569 (whose tree 69e0084 has) gave b29d9e7 with the same tree 5c570ea. On it: CPU `test_diffusion_x1_scale` 22 cases, `test_diffusion` 30/30, the Python test passes, full `ctest -j1` 85/88 (with #248's tests) failing only the baseline 3; V100 `test_weno5_cuda_line` passes, `test_weno` 77/77, `test_reconstruct` 16/16, `test_diffusion_x1_scale` 36/36, `test_diffusion` 52/52.
- RED: 97f7058 = the tests alone, CPU. `test_diffusion_x1_scale` cannot build (no `nu_scale_x1` on `DiffusionOptions`). `test_diffusion_x1_scale.py` FAILS both arms at run time (`'snapy.DiffusionOptions' object has no attribute 'nu_scale_x1'`). `test_diffusion` passes (30/30).
- GREEN: 5dc484e7, CPU. `test_diffusion_x1_scale` passes all 9 tests (13 cases: the 4 device tests on cpu float32 and float64, plus 5; its 8 CUDA cases skip on the CPU node). `test_diffusion` passes (30/30). `test_diffusion_x1_scale.py` passes both arms. Full `ctest -j1`: 82/85, failing only the test machine's baseline 3 (test_shallow_splash, test_shallow_xy, test_straka), which main fails identically.
- The sine-mode tests can tell the profile from none: they run to s nu k^2 t = 0.096, so an ignored s = 2.5 would leave exp(-0.039) = 0.962 of the mode instead of exp(-0.096) = 0.908, a gap of 0.054 against the 3e-4 tolerance.
- CUDA: 5dc484e7 on a V100 (sm_70; the build flags carry `compute_70,sm_70`), kintera a8bef99 built for CUDA, a cluster run. `test_diffusion_x1_scale` passes all 21 cases, the 8 CUDA cases included: ones bitwise equal to no profile, both scaled decays, and YAML equal to the tensor, each in float32 and float64. `test_diffusion` passes (52/52). `test_diffusion_x1_scale.py --device cuda` passes both arms. Full `ctest -j1`: 80/83, failing only the baseline 3 (this build has no UCX, so it registers two tests fewer).
- Review fixes, 639cd06. RED = c7131ae with the new tests only, CPU: `cells_profile_is_refused_when_x1_is_split` fails (a per-cell tensor is accepted with nb1 = 2 and 4, for nu and for kappa) and `profile_change_after_build_is_refused` fails (replacing the per-cell tensor or the table, or writing into either, is silently ignored; clearing one, or adding a per-cell tensor to a table, was already refused); `table_profile_is_independent_of_the_x1_split` already passes. GREEN, CPU: `test_diffusion_x1_scale` passes all 12 tests (17 cases; its 10 CUDA cases skip on the CPU node); `test_diffusion` 30/30; the Python test passes; full `ctest -j1`: 82/85, failing only the baseline 3. CUDA, V100 (a cluster run, sm_70): `test_diffusion_x1_scale` 27/27 cases pass, 0 skipped; `test_diffusion` 52/52; `test_diffusion_x1_scale.py --device cuda` passes.
- Inference-tensor refusal, b5c13c0. RED = 639cd06 with the new tests only: `inference_tensor_profile_is_refused` fails on cpu float32/float64 and cuda float32/float64 (an inference tensor is accepted per cell and as a table, and a YAML table parsed under inference mode is an inference tensor); the Python `inference` arm fails on cpu and cuda ("an inference tensor was accepted as a profile"). GREEN = b5c13c0: CPU `test_diffusion_x1_scale` passes all 13 tests (19 cases; 12 CUDA cases skip), `test_diffusion` 30/30, the Python test passes, full `ctest -j1` 82/85 failing only the baseline 3 (as main); V100 `test_diffusion_x1_scale` 31/31 cases, `test_diffusion` 52/52, `test_diffusion_x1_scale.py --device cuda` passes.
- max_time_step check, 8396947. RED = b5c13c0 with the new test only: `profile_change_is_refused_by_max_time_step` fails on cpu float32/float64 and cuda float32/float64: `max_time_step` accepts a larger replacement table, a write into the per-cell tensor and `dynamic` set to true, and `forward` accepts `dynamic` set to true. GREEN = 8396947: CPU `test_diffusion_x1_scale` passes all 14 tests (21 cases; 14 CUDA cases skip), `test_diffusion` 30/30, the Python test passes, full `ctest -j1` 82/85 failing only the baseline 3 (as main); V100 `test_diffusion_x1_scale` 35/35 cases, `test_diffusion` 52/52, `test_diffusion_x1_scale.py --device cuda` passes.
- Value comparison, 1e07d88. RED = 8396947 with the new tests only: `profile_write_through_outside_storage_is_refused` fails on CPU and on the V100 build (neither `max_time_step` nor `forward` throws after a write through `from_blob` memory or through `variable_data`), and the Python `outside` arm fails on cpu and cuda ("from_numpy: a write after the build was not refused"). GREEN = 1e07d88: CPU `test_diffusion_x1_scale` passes all 15 tests (22 cases; 14 CUDA cases skip), `test_diffusion` 30/30, the Python test passes (all four arms), full `ctest -j1` 82/85 failing only the baseline 3 (as main); V100 `test_diffusion_x1_scale` 36/36 cases, `test_diffusion` 52/52, `test_diffusion_x1_scale.py --device cuda` passes. Cost (a cluster run, CPU, 1 thread): `torch.equal` on a block-sized float64 profile takes 0.9-1.8 us (20 to 1030 cells); in place, `max_time_step` with two profiles costs +1.8 us per call on a 128x1 block and +4.6 us on a 128x128 block, and a step makes 4 checks (`max_time_step` and 3 stages), about 0.3% and 0.1% of the step's 2.5 ms and 20 ms.
- #251 (CUDA lines > 1024 cells). RED on a V100 (sm_70; the author's evidence is an H100): 3c25c49 on this PR's diffusion commits: `line_above_1024_matches_cpu` fails at 1025 cells with "CUDA error: invalid configuration argument"; the widened test of aca9b51 alone: `line_above_1024_matches_cpu` fails in 20 cases, each "invalid configuration argument": the 4 reconstructions x the 5 lines longer than 1024 (1025, 1030, 1280, two lines of 1025, 1030 along dim 2); the 32- and 1024-cell cases match CPU. GREEN = ba4e83f: V100 `test_weno5_cuda_line` passes (all 32 cases: 4 reconstructions x 8 lines), `test_weno` 77/77, `test_reconstruct` 16/16, `test_diffusion_x1_scale` 36/36, `test_diffusion` 52/52, full `ctest -j1` 81/84 failing only the baseline 3 (this build has no UCX, so it registers two tests fewer); CPU the new test skips; `test_diffusion_x1_scale` 22 cases, `test_diffusion` 30/30, the Python test passes, full `ctest -j1` 83/86 failing only the baseline 3 (as main).
- Carried examples fix, c7131ae: each changed file parsed as its runner loads it (`MeshBlockOptions.from_yaml` and kintera `KineticsOptions.from_yaml`, as examples/run_hydro.cpp and jupiter_evap_precip_1d.cpp do), at 5dc484e7 and at c7131ae. kintera reads diff_T 1.75 and diff_P -1 for all 11 reactions, and vm 2.08e-5 (NH3(s)) and 4.37e-5 (NH4SH(s)) in jupiter_crm and jupiter_gcm, and 3.59e-5 (H2S(l)) in uranus; every other number is unchanged (5 files, 0 mismatches). Full `ctest -j1` on c7131ae (a cluster run, CPU): 82/85, failing only the baseline 3.

## The tests
`tests/test_diffusion_x1_scale.cpp` (gtest; the device-parametrized cases run on CPU float32/float64 and, where available, CUDA):
1. `yaml_table_parses`, `yaml_table_rejects_bad_input`: the table form and each refusal listed above.
2. `unity_profile_is_bitwise_no_profile`: a profile of ones, per cell and as a table, gives the tendency of no profile exactly (`torch::equal`), walls included.
3. `viscous_sine_mode_decays_at_the_scaled_rate`, `conductive_sine_mode_decays_at_the_scaled_rate`: with a uniform scale s = 2.5 on a periodic box, a sine mode in v2 decays as exp(-s nu k^2 t), and a sine mode in T at rest (fixed rho, dT = dE / (rho cv)) as exp(-s kappa k^2 t). k = 1, 64 cells, 100 explicit steps at dt = 0.1 dx^2 / (s nu); tolerance 3e-4 absolute and relative, the same scheme and tolerance as test_diffusion's unscaled sine mode.
4. `linear_profile_gives_the_analytic_tendency`: s(x) = 1 + x/10 at rho = 1 gives dt nu (2 + 0.4 x) for v2 = x^2 and dt kappa cv (2 + 0.4 x) for T = 300 + x^2 in every cell, the wall cells included, to 1e-12 relative. This is the non-uniform check: the same numbers test_diffusion has for rho = 1 + x/10.
5. `yaml_table_equals_the_cells_profile`: a table whose knots are the cell centres gives the same tendency as those values set per cell, bit for bit, and a different one from no profile.
6. `timestep_uses_the_largest_scaled_coefficient`, `reset_refuses_bad_profiles`.
7. `table_profile_is_independent_of_the_x1_split`: a 16-cell column with a table profile on nu (4 knots, off the cell centres) and on kappa, built as one block and as 2 and 4 blocks along x1 (a `Mesh` in one process, cubed layout): the interior tendencies joined along x1 equal the one-block tendency bit for bit (`torch::equal`), on every device and dtype; the same column without a profile differs.
8. `cells_profile_is_refused_when_x1_is_split`: a per-cell tensor is accepted with nb1 = 1 and refused with nb1 = 2 and 4, for nu and for kappa; the table is accepted with nb1 = 2.
9. `profile_change_after_build_is_refused`: after the block is built and one `forward` has run, replacing the per-cell tensor, writing into it, clearing it, replacing the table, writing into it, or adding a per-cell tensor to a table makes the next `forward` throw.
10. `inference_tensor_profile_is_refused`: a per-cell tensor and a table made under inference mode (`c10::InferenceMode`, as `torch.inference_mode()`) are refused at build, on every device; a YAML table parsed under inference mode is an ordinary tensor and builds.
11. `profile_change_is_refused_by_max_time_step`: after the build, a larger replacement table, a write into the per-cell tensor, or `dynamic` set to true makes `max_time_step` throw before any `forward` (and `forward` too), on every device; the unchanged profile gives its bound 1 / (2 nu).
12. `profile_write_through_outside_storage_is_refused`: a per-cell profile over outside memory (`from_blob`, as `torch.from_numpy`) and one written through its `.data` alias (`variable_data`); after the build, the write lands in the profile and bumps no version, and `max_time_step` and `forward` both throw.

`tests/test_diffusion_x1_scale.py`: the same through Python and a full `MeshBlock` step (nx1 = 16, reflecting x1 walls, a sheared and conducting state): a profile of ones from Python and from YAML gives the step of no profile bit for bit, and a YAML table on the cell centres gives the step of the same profile from Python bit for bit. The `outside` arm: after the build, a write into the NumPy array behind `torch.from_numpy`, and separately through `.data`, makes the next step (which calls `max_time_step` first) throw. The `inference` arm: a profile made under `torch.inference_mode()` is refused with an error naming the inference tensor, and a YAML table parsed under it builds.

`tests/test_weno5_cuda_line.cpp` (#251; skipped without CUDA): WENO5, WENO3, polynomial degree 5 and 3, each on one line of 32, 1024, 1025, 1030 and 1280 cells, on two lines of 1025 in one tensor (the block index must stay the line id), and along dim 2 on 32 and 1030 cells (a line stride other than 1): the CUDA result equals the CPU result to 1e-12 (float64).

## Limits
- The profile depends on x1 only (the vertical in snapy's cartesian convention). Profiles in x2 or x3 are not provided.
- `dynamic: true` takes no profile: a dynamic coefficient that varies in x1 is a separate feature.
- #251: the tiled launch is tested in float64 only.


## PR #253: diffusion: an opt-in kappa_iso conduction on potential temperature, so a resting adiabatic column stays at rest (#252)

Merged 2026-09-29; merge commit `3f7ad96`.

Closes #252.

Five commits: the red test (3374c48), then four by a contributor: the fix (e3e7bf4), and a guard that allows `on_theta` only on a dry ideal gas (b353c65, 92922ea, db3fd8d).

**What.** `kappa_iso` conducts heat down the temperature gradient, so a dry column at rest on an adiabat (dT/dz = -g/cp) does not stay at rest. This PR adds an opt-in key `on_theta` (default `false`) that makes the conduction act on potential temperature, which leaves that column unchanged. The default stays the T form, so no existing case changes a number.

**Test.** `tests/test_kappa_adiabatic_rest.py` (CPU) and `tests/test_kappa_adiabatic_rest_cuda.py` (skips with 125 without a GPU). Two arms step the same column 10 times at one shared dt, with `kappa_iso` = 75 and with `kappa_iso` = 0; the oracle is max|T(K) - T(0)| < 1e-9 K.
- Red on main f24576b: 1.36e-2 K (bottom -1.33e-2, top +1.36e-2); the K = 0 control differs by exactly 0.
- Green at e3e7bf4, `on_theta: true`: 8.5e-14 K on one CPU platform, 2.3e-13 K on another, 2.3e-13 K on an H100; the default's drift stays 1.361e-2 K and is asserted.
- With `on_theta`, the flux uses `(T/theta)_face * dtheta/dn`, with theta = T (1e5 Pa / p)^(R/cp) from the mixture's R and cp; the dynamic branch uses the same replacement. The unknown-key check (#242) accepts `on_theta` and still refuses misspellings.
- Diffusion gtests: identical on base and head (52 + 8 + 36 cases).

**Guard (b353c65, 92922ea, db3fd8d).** `on_theta: true` is allowed only on a dry ideal gas: EOS type `ideal-gas`, no cloud species, and no vapor beyond the dry carrier. Anything else is refused, and the error names the EOS type and #252. The check runs when `Diffusion` is built, before the heat-capacity check, so `shallow-water` and `plume-eos` also get this message. It runs again at the start of `forward` and `max_time_step`, as `check_profiles()` does for `dynamic`, because the options object is shared and `on_theta` can be set after construction. `on_theta: false` never reaches it.
- `on_theta_refuses_eos_other_than_ideal_gas`: `ideal-moist`, `moist-mixture`, an `ideal-gas` card carrying vapor and cloud, and `shallow-water` are refused; a dry `ideal-gas` constructs.
- `on_theta_set_after_construction_refuses`: a moist EOS built with `on_theta` false, then set to true, refuses at the next forward.
- Docs: `docs/user_guide/configuration.rst`, `docs/api/forcing.rst` and the `forcing.pyi` docstring.

**Known follow-ups (non-blocking, from review).** The `on_theta` comment in `forcing.hpp` still says only "EOS type is ideal-gas"; the after-construction refusal is tested through `forward` but not `max_time_step`, and not for an ideal-gas card with vapor or for `plume-eos`; with `on_theta` on, `forward` evaluates the cv heat capacity twice; the theta reference pressure is fixed at 1e5 Pa (documented; it only rescales theta).

**Limit.** Which theta a moist or variable-composition column should use, and which form should be the default, is the open question in #252. This PR does not decide it.


## PR #258: run_hydro exits nonzero on an abnormal termination (#255); round-off repairs are not positivity events (#256); kinetics sees the saturation-adjusted state (#257)

Merged 2026-09-30; merge commit `84a5dbd`.

Closes #255, closes #256, closes #257.

Twelve commits on main `3f7ad96`, head c5e7f3c: three test commits by a contributor (e4b1162, 3626a73, 2b961bf), three for #255, two for #256, one clang-format commit (6d2be74, whitespace only), the Float32 bound for #256 (d5a5706), and two for #257: its red test by a contributor (f841f0e) and its fix by the upstream maintainer (c5e7f3c).

**#255: an abnormal termination exits nonzero.** `MeshBlock::finalize` and `Mesh::finalize` return 1 on the one branch that prints `Terminating abnormally`, and 0 otherwise. A signal, the wall-time limit, the cycle limit and the time limit still return 0. A one-block mesh returns its block's status. `run_hydro` and every other example driver (bryan, straka, shock, shallow_xy, shallow_splash, jupiter_evap_precip_1d) return that status from `main` (0350390, 2bf4e68). `jupiter_evap_precip_1d` prints `Completed` only after a normal termination (6765e9f). `mesh.pyi` now declares that `finalize` returns int.
- Test: `UranusCycle1.abnormal_termination_exits_nonzero` uses `tests/test_abnormal_exit_floor.yaml`, whose pressure floor sits above the initial pressure. Every step then trips `causes: floor` and uses up the redo budget, whatever the physics. Red on main (exits 0), green here.

**#256: a round-off species repair is not a positivity event.** On the shipped `examples/uranus.yaml`, cycle 1 was redone five times and aborted. The redo came from the limiter's patch mark. Kinetics leaves -1e-304 to -2e-302 kg/m^3 of H2S(l) / H2S(l,p) in the 53 cloud-free cells, `fix_vapor` zeroes them in `check_redo`'s cons2prim, and any change at all marked a patch. `thetasevere` is only printed. The fix is one bound, 4096 ulp (9.1e-13 in Float64; Float32 below) of the cell's total gas mass, which is the same margin theta already holds back. A species repair or a withheld mass below that bound no longer marks a redo and is no longer counted as severe. The repairs and clips themselves are unchanged (50b5ee7, af49f9f).
- `UranusCycle1.column_finishes_the_two_cycles` (96 x 1, the smallest column with the shipped signature): red on main, green here. The full `uranus.yaml` at 20 cycles runs with no redo at dt 5.567 s; on main it aborts at cycle 1.
- `cycle_info.positivity_severe_needs_more_than_roundoff_withheld`: a withheld mass of 1e-6 of the cell is still severe, and 1e-300 is not. `forcing.limiter_roundoff_species_repair_is_not_redone`: a -1e-300 repair is not redone, and -1e-9 is.
- `examples/earth_crm.yaml` (ideal-moist) had the same cycle-1 abort. It now runs its 50 cycles. The redos that remain are real repairs of about 1e-12 of rho, above the bound.

**#256 in Float32 (d5a5706; Float32 fix and tests by the upstream maintainer).** At 6d2be74 the round-off bound scales with the dtype's eps (`src/hydro/flux_positivity.cpp:11-15`), so in Float32 its 4096 ulp is 4.9e-4 of the cell gas mass. Float32 does reach the limiter: `DeviceTest` runs kFloat32, and `test_parentless_cloud` calls the conserved limiter in Float32. There, a -1e-4 cloud repair was not redone, and a settling column with 1e-4 of cloud counted 0 severe instead of 5. The bound is now 64 ulp (7.6e-6) in Float32 and stays 4096 ulp (9.1e-13) in Float64; the flux limiter's own 4096-ulp margin is unchanged. Why 64: Float32 depletion rounds by at most 0.99 ulp (1e6 random states), the flux round-off withheld on the uranus column is at most 1e-20, and clean runs make no repairs. Float32 now catches repairs down to -1e-5 (before: -1e-3). A 67-case Float64 sweep is identical before and after. 4 files, +81/-14.
- New Float32 cases in `test_forcing` (repairs of -1e-4 and -1e-5 are redone; -8 ulp and -1e-37 are not) and `test_cycle_diagnostics` (1e-4 and 1e-5 of cloud count 5 severe; 1e-30 counts 0). They fail on 6d2be74 in exactly the four real cases and pass with d5a5706.
- CPU: C++ 63/63, Python 28/28 (6 CUDA skips). CUDA, `test_forcing` / `test_cycle_diagnostics` / `test_parentless_cloud` / `test_uranus`: 39/9/12/2 pass on 6d2be74, 40/10/12/2 on d5a5706.
- Unchanged and out of scope: in Float32, `earth_crm` and `uranus` hit NaNs on cycle 1, and casting a block to Float32 also turns the sedimentation index buffer into floats.

**#257: kinetics sees the saturation-adjusted state (c5e7f3c).** `run_hydro` and `jupiter_evap_precip_1d` ran kinetics on a stale `hydro_w`, from before the saturation adjustment, so kinetics removed cloud that had already evaporated and forced real H2S / H2S(l) repairs. Both drivers now call `peos->forward(hydro_u, hydro_w)` before kinetics; 2 lines each.
- Test: `UranusLate.column_reaches_cycle_40` (f841f0e) on `tests/test_uranus_late_abort.yaml`, a 100 x 1 column cut from `examples/uranus.yaml`. It is 01b4cc0 without its `run_deck()` refactor hunks, which 2b961bf already carries. c5e7f3c adds 3 EXPECTs to it: no redo, no exhausted redo budget, no abnormal termination.
- At f841f0e the column exits 1 (`Terminating abnormally`) at cycle 32 after 13 redos on CUDA (sm_75, kintera 2.5.13) and 14 on CPU (kintera 4dc613d; all in cycles 30-32). Without the fix the test fails both of its f841f0e checks, and all 5 once c5e7f3c's EXPECTs are added. At c5e7f3c it exits 0 with no redo at the cycle-40 limit, and the test passes 5/5 on both builds.

**Checks at c5e7f3c.** CPU replay rig, ctest -j1, against main `3f7ad96`: 94 registered, 91 run, 79 pass, 12 fail, and the fail set is the same as main's (multi-process and example-driver tests that also fail on main on that rig). `UranusLate` 1/1, `UranusCycle1` 2/2; the gtests go from 49 OK at d5a5706 to 50 OK, with 0 failed and 6 skipped on both. CUDA (RTX 4000, sm_75): the 29 related tests pass 29/29, `ctest -L python` 28/28, the Uranus tests 3/3. The Float32 tests run on CPU only.

**Limit.** The full `examples/uranus.yaml` now runs past cycle 232 and aborts at cycle 342 on an H2S repair at RK stage 0 near the top cells (a repair of 1.8e-13 against a tolerance of about 1.1e-14). That is #260 and is not addressed here. Not run: the full 100 x 200 deck to completion, and any Float32 test on CUDA.


## PR #259: hydro, implicit, diffusion: p_ref across in-process x1 seams (#254), VIC donor margin (#260), on_theta conductivity (#261)

Merged 2026-09-30; merge commit `5eeb9b6`.

Closes #254, closes #260. Fixes the `on_theta` path of #261; the default-path question stays open on #261.

Thirteen commits on main `84a5dbd`, head fa136b5. 11 files, +738/-65.
- #254: two failing tests by a contributor (e9cbc8f, 3ac2f13), two fixes by the upstream maintainer (d965030, e7d743c), one test bound (b738eaa), two comment-only commits (500023f, 1d78096) and a clang-format pass (1237bc4). 7 files, +582/-59. Found with #250's T4 harness.
- #260: fix (e3d8eb6) and test (64564b9) by the upstream maintainer, and a float32 twin of the test (24572a9). 2 files, +91/-6.
- #261: failing test (295ccdc) and fix (fa136b5). 2 files, +65/-0.

## #254: `p_ref` across in-process x1 seams

**The anchor.** The downward `p_ref` scan passed its running face value from block to block only when the x1 split was across processes (process group, pz > 1, one block per process). A mixed layout (pz > 1 with several blocks per process) was refused. A second x1 block in the same process got an empty anchor and restarted the scan from its own top cell, so `p_ref` jumped at every in-process x1 seam, on every density form. `Layout::take_x1_anchor` / `pass_x1_anchor` now carry the anchor down any x1 split: to a block in the same process through a board (the block below waits until the block above posts), and to a remote block through the process group as before (d965030).
- `HydroRefX1.local_blocks_restart_the_reference_at_the_seam`: one process, x1 from 0 to 4, nx1 = 4, uniform rho = 1, p = 1e5, grav1 = -10, one block against two (pz = 2, blocks_per_process = 2). On main, `p_ref` in the cell under the seam is 100020.000125 with one block and 100000.000125 in the lower of two blocks. The gap is 20 = g * rho * dx. The test exits 1 on main, and here the gap is 0.

**The ghost rows.** With the anchor fixed, the `p_ref` / `dref` ghost rows still went only to a remote neighbour. A same-process neighbour kept its block-local ghost values, so the reconstruction saw a different perturbation on each side of the seam. `_hydro_ref_x1` now sends its seam rows to every x1 neighbour: a local one through `post_to_local_block` / `take_from_local_block`, and a remote one with the same tags and order as before (e7d743c).
- `HydroRefX1.in_process_split_matches_one_block_after_200_steps`: a 32 x 8 polytrope with a cold bubble, four blocks in one process against one block, 200 steps. The max relative difference goes from 6.4e-5 to 5.2e-15 in rho, from 1.1e-6 to 1.2e-15 in p, and from 1.4e-4 to 5.4e-14 in vx. The bound is 1e-12 rather than 1e-14 (b738eaa). The 5.4e-14 in vx is round-off from the chained anchor scan, and 1e-12 is still about 1e8 below the error the test guards.

**Messages between blocks.** `send_to_block` / `recv_from_block` address a block by its rank and fold both local block indices into the tag, so several blocks per process do not collide. With one block per process, the tag and the message are the same as on main. The x1 seam flux average still runs across process seams only. After the ghost-row exchange the two seam-face states already agree, so a same-process seam has nothing to average. Mixed layouts now run instead of being refused.

## #260: a VIC species donor keeps a 4096-ulp margin

**The chain.** `examples/uranus.yaml` aborted on CPU at cycle 342 after five limiter-only redos. The marked quantity is H2S(l,p) (species slot 2, parentless), not H2S vapor, in the top two cells of 76 columns at RK stage 0.
- VIC pass 3b (`src/implicit/vic_redistribute_impl.h`) clamps the downward species transfer at the donor's availability, (rho * y + du) * V. rho * y is rebuilt from the primitives and can be one ulp above the conserved density, so the transfer took one ulp more than the cell held. After the flux limiter left 5.7e-33 of the cell's 7.52e-22 kg/m^3, u0 + du came out at -9.40e-38 (-0.56 ulp).
- The parentless-cloud column repair then re-mixed that cell with the one below at one mixing ratio. It moved 1.85e-13 kg/m^3 upward, 17 times the 4096-ulp repair bound (1.09e-14). The amount is set by the neighbour's content, not by the deficit, so it grew as dt halved (17.0, 21.1, 23.1, 24.2, 24.7, 24.9 times the bound) and no redo could clear it.

**Fix (e3d8eb6).** Pass 3b now leaves 4096 ulp of rho * y in every donor, the same margin `flux_positivity_theta` already holds back. At cycle 342 the top cell keeps 6.84e-34 (4096 ulp of 7.52e-22), and nothing is repaired.

**Tests (64564b9, 24572a9).** `vic_redistribution.a_drained_species_donor_stays_non_negative` in `tests/test_backward_substitution.cpp` builds a 2-cell column whose top cell holds 7.52e-22 of a species, with the conserved density one ulp below rho * y and a face transfer that drains far more than is left. The arithmetic is exact, so the result is bit-deterministic; 24572a9 runs the same fixture in float32 beside float64. CPU, fresh builds, kintera 4dc613d:

| | float32 | float64 | ulp of rho * y | result |
|---|---|---|---|---|
| 1237bc4 + the tests | -5.0487e-29 | -9.4040e-38 | -0.5629 | FAIL |
| head | 3.6729e-25 | 6.8414e-34 | 4095.26 | PASS |

The column's species mass change is 0 in both. the upstream maintainer measured the same ulp values independently. On `8c8fc53`, before the rebase, the fix took the full `examples/uranus.yaml` on CPU from an abort at cycle 342 to 500 cycles with 0 redos (largest limiter repair 1.7e-289 of the bound, was 24.9), and ran 5/5 identical on CUDA (RTX 4000), species mass error -3.8e-14 relative.

## #261: `on_theta` conducts with rho cp

**The rate.** With `on_theta: true`, the kinematic path turned `kappa_iso` into a conductivity with rho * cv, so theta diffused at `kappa_iso / gamma`. It now uses rho * cp = rho * cv + p / T, with the R = p / (rho T) that the theta computation uses (fa136b5, +2 lines in `src/forcing/diffusion.cpp`). With `dynamic: true`, `kappa_iso` is the conductivity k and the flux carries no heat capacity, so theta already diffuses at k / (rho cp) and that path is unchanged; its time-step bound, `kappa_iso / (rho_min cv)`, stays conservative.
- `DeviceTest.on_theta_sine_mode_decays_at_kappa` (295ccdc): 64 cells on a periodic 0 to 2π box, `kappa_iso` 0.25, theta = theta0 (1 + 0.01 sin x) at rest, the diffusion forcing alone for 200 forward-Euler steps. The measured decay rate over the expected one is 0.714021 (float32) / 0.714023 (float64) at 295ccdc, FAIL, and 0.999994 / 0.999978 at the head, PASS.

## Checks

- Full ctest on CPU, 1237bc4 against the head: the same 12 failures on both (standing on this machine), no new failure. `test_backward_substitution` 7/7.
- `pre-commit run --all-files` clean (clang-format 20.1.4).
- CUDA (RTX 5090, serial): test_diffusion 56/56 (32 cpu, 24 cuda; on_theta cuda 0.999971 / 0.999978, 0.714 before the fix), test_backward_substitution 7/7, VIC margin 4095.26 ulp on host and in a CUDA kernel; full ctest identical to 1237bc4.
- Reviewed and approved on fa136b5 by three independent reviewers; CI green on all three jobs.

## Limits

- #254: the blocks of one process must advance concurrently, as the mesh worker threads run them. A caller that steps them one at a time stops with an error after 5 minutes. A block-to-block message through the process group allows at most 16 blocks per process (the tag fold).
- #260: the largest repair ratio was not measured on CUDA.
- #261: the default temperature path is unchanged. Whether `kappa_iso` on that path should also use cp (it diffuses T at `kappa_iso / gamma` when p stays uniform) is left for the maintainer on #261, since changing it would change every existing case that uses `kappa_iso`.
