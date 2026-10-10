> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# snapy upstream pull requests #220-#226 (merged), bodies
Fetched 2026-10-09 from the public chengcli/snapy repository (GitHub REST API).

## PR #220: scalar, hydro, implicit, mesh: tracer positivity at panel seams with an upper bound; passive tracers follow the dry air

Merged 2026-09-25; merge commit `bc4d411`.

## Summary

- **scalar, hydro — positivity at panel seams, an upper bound, a floating-point margin.** At a flip-flag panel seam the scalar's two reconstructed states arrived swapped, so the upwind solver took the downwind state. The positivity limiter's donor factor crossed seams as an interpolated blend, so the two sides of a face used different factors and tracer mass leaked. The factor also aimed at an exact zero, which floating point lands below. Now the scalar sends its states under direction-suffixed keys, as the hydro does; theta is exchanged as a raw copy in both hydro and scalar; the limiter stops 4096 ulp short of zero. A new scalar option `upper-bound` (default -1, off; 0 is rejected; needs the eos limiter) keeps r ≤ b by limiting the complement b·ρ − s, and adds the flux change back, so faces that were not limited stay bitwise unchanged.
- **implicit, hydro, mesh — tracers follow the dry air.** Tracers are per unit dry air. The vertical implicit correction moved them with the total face mass transfer, and a forcing that creates or removes dry air (`relax-bot-comp`) did not move them at all. Now the VIC stores the clamped dry transfer per face and the scalar update uses it, and the hydro records the dry-density increment of its forcings each stage (only on blocks with tracers) so the tracers follow it.
- **mesh — user stage forcings, same convention.** A stage forcing registered from Python writes `hydro_du` outside the bracket above. It is now bracketed the same way. **Migration:** a forcing that writes the density row *and* hand-corrects `scalar_ds` for the same air now moves its tracers twice; drop the manual correction. `docs/api/mesh.rst` and the stage-forcing section of `docs/user_guide/simulation.rst` state the convention.

## Tests

Linux CPU, torch 2.6. Red = the tip's test files run against a build of main `14f926f` (the base, after #216); green = the same files against a build of the tip `9ba4f15`. Numbers are read from the run logs.

| gate | red (main `14f926f`) | green (`9ba4f15`) |
|---|---|---|
| `test_flux_positivity_cubedsphere_python` (first commit) | **fails**: mass drift across the seam 3.217e-3 (base arm) and 3.198e-3 (limited arm); the tracer reaches max 1.012176, outside [0, 1]; the limiter never fires. The test's read of the new `scalar.positivity_hits` buffer was made tolerant for this run only; unmodified it stops with `KeyError` on main | passes: drift 2.238e-15 in both arms; limited arm max 0.999999668, min −5.5e-322, limiter fired 117,290 times |
| `test_flux_positivity_cubedsphere_moist_python` (fourth commit) | **passes on main too, so it does not discriminate there**: limited arm drift 1.383e-13, 77 times the tip's 1.796e-15 but under the test's 1e-12 tolerance; limiter fired 260 times; base arm drift 1.796e-15, as at the tip | passes: vapor+cloud total drift 1.796e-15 in both arms; limited arm min +0, limiter fired (95 to 172 times, depending on run and device); 1.9e-3 of the species mass crossed a seam |
| `test_tracer_dry_convention_python` (second commit) | **fails**: uniform tracer departs by 3.318e-6 (implicit schemes 1 and 9), 4.304e-1 (relax, moistening), 9.976e-3 (relax, drying), 4.324e-1 (combined) | passes: every arm ≤ 1.11e-15 |
| `test_stage_forcing_dry_tracer_python` (third commit) | **fails**: "a stage forcing changed dry air without moving the tracers". On bare main this red covers the second and third commits together; the third commit alone was also measured red, with the same message, on a build of the first two commits | passes |
| `test_flux_positivity_python` | passes (an existing test, registered here for the first time) | passes: limited arm min +0, species drift 2.0e-16, 68 hits |
| `test_scalar.release` (adds `scalar_upper_bound_holds_both_sides`), `test_user_output.release`, `test_radiating_boundary.release` | — | pass |

The moist seam test is a regression check for moist species across the panel seams. It does not discriminate against main at its 1e-12 tolerance: main's limited arm drifts 1.4e-13 to 1.7e-13 on the toolchains measured, against 1.8e-15 at the tip. Each of the three fixes is guarded by its own gate above, which fails on main.

`ctest -N` at the tip lists the five python gates, each carrying `PYTHONPATH` for the snapy built from this tree; run one by one with `ctest -j 1`, the five python gates and the three C++ tests above each report "100% tests passed" (8/8). The provenance line in each run shows the python gates importing snapy from that build's own install prefix, not from an installed package.

What `test_flux_positivity_cubedsphere` asserts: both arms conserve every tracer, drift < 1e-12; the limited arm fires, hits > 0; and the limited arm stays in [0, 1] as min ≥ −1e-15 and max ≤ 1 + 1e-5. The measured min −5.5e-322 is a negative subnormal, some 300 orders of magnitude smaller than the −1e-15 tolerance, so it passes. The lower-bound check does not discriminate here: on main the limited arm's min is −1.4e-73, which also passes it; main fails on drift and on the max (its hits count is not measurable, since main has no such buffer). The gate's bite comes from drift and the upper bound.

## Compatibility

- Cards without `upper-bound` and without tracers are unaffected by the limiter change except where theta < 1: there the limiter now stops 4096 ulp short of zero, and seam ghosts take the neighbour's factor instead of an interpolated one.
- Moist runs with tracers change numerically: tracers now follow the dry air through the implicit correction and through forcings that change dry density.
- `tests/test_user_output.cpp` changes because its fixture used the idiom this PR retires (it wrote the density row and hand-corrected `scalar_ds`).
- The hydro's `positivity_hits` diagnostic changes value (see Provenance): it now counts interior entries only.

## Provenance

- Tip `c9f9f2f` (tree `a44c1e5`) on main `5939862` (#219). It is `9ba4f15` (tree `c2e4793`, on `14f926f`, where the review below was done) rebased over #219. The one conflict was in `tests/CMakeLists.txt` at the first commit: #219's `test_eos_temp2inteng` registration and this PR's `test_flux_positivity` and `test_flux_positivity_cubedsphere` registrations land at the same spot, and both are kept, #219's line first. `git range-diff 14f926f..9ba4f15 5939862..c9f9f2f` is 1 `=` and 3 `!`: the first commit's `!` is that hunk, the other two are hunk-header context only, and no `src/` line changed. Three independent rebases reached tree `a44c1e5` (the PR author, a second independent review agent, an independent review agent); on it `ctest -N` lists each of the six python registrations once, and `test_eos_temp2inteng` and the three positivity python tests pass (the second independent review agent, CPU). The four commits at `9ba4f15`, one per concern:
  - `f5b0eeb` hydro, scalar: tracer positivity at panel seams, an upper bound, and a floating-point margin
  - `8795736` implicit, hydro, mesh: passive tracers follow the dry air
  - `30250ec` mesh: a stage forcing's dry air carries its tracers, like a native one
  - `9ba4f15` tests: add cubed-sphere moist species flux-positivity seam test (author: the upstream maintainer)
- Rebasing the series over #217 conflicted in two places. In `src/hydro/hydro.hpp` the member list is the union: main's `_positivity_hits, _positivity_severe, _positivity_min, _lim_cut, _lim_flux` plus this PR's `_forcing_dry`. In `src/hydro/hydro_forward.cpp` the positivity census after `flux_positivity_theta` keeps main's block (`cells`, the interior view `ti`, `_positivity_severe`, `_positivity_min`) and counts hits on that interior view, `_positivity_hits += (ti < 1.).sum();`. This also corrects the diagnostic that #217 left: its line `_positivity_hits += (theta < 1.).sum()` over-counted in 2-D and 3-D, because `flux_positivity_theta` accumulates each direction on its own interior slice, so the ghost rows transverse to a direction do receive drain and their theta drops below 1 (measured by the upstream owner's reviewing agent in `test_flux_positivity`, 2-D: 170 hits over the full array against 68 over the interior; confirmed from the slicing by the second independent review agent). The comment claiming ghosts are exactly 1 is gone.
- `tests/CMakeLists.txt` keeps both sets of registrations. The yaml deck this PR once carried is dropped: #218's `tests/test_flux_positivity_cubedsphere.yaml` is on main, and the first commit adds `upper-bound: 1.0` to it, which the cubed-sphere gates require (the reader treats a missing key as −1, and the limited arm would not cap).
- Dev-gated on Linux CPU, torch 2.6, red to green as above; independently on CPU with torch 2.10 (the independent review agent) and on CUDA (the second independent review agent, below). Upstream CI at `9ba4f15` (run [36189359704](https://github.com/chengcli/snapy/actions/runs/36189359704)) and at `c9f9f2f` (run [36193826876](https://github.com/chengcli/snapy/actions/runs/36193826876)): pre-commit, ubuntu-latest and macOS-latest all passed.

## CUDA

Run by the second independent review agent at `9ba4f15` (tree `c2e4793`) on main `14f926f`: CUDA Release, sm_90 only (the local nvcc 12.5 cannot compile sm_120, so the architecture list was narrowed by an uncommitted local edit that is not part of this tree).

- `ctest -j1`: 60 passed, 0 failed, 1 skipped. The skip is `test_python_import_path_python`, which needs `SNAPY_TEST_PYTHONPATH` set; it is not a CUDA skip, and `test_fix_vapor_reports_failure_cuda_python` passed. Some tests passed only on a rerun after two local environment fixes, a `torchrun` from a different Python and `ncrcat` missing from `PATH`; none of those failures came from the code.
- On the device (`--device cuda`), `test_tracer_dry_convention` passes at the tip (combined max |r/r_init−1| = 1.332e-15) and fails on main with the same numbers as on CPU: 3.318e-6 (implicit schemes 1 and 9), 4.304e-1 (relax, moistening), 9.976e-3 (relax, drying), 4.324e-1 (combined).
- `test_stage_forcing_dry_tracer` passes at the tip (max |r/r0−1| = 4.441e-16, with the expected interior dry-mass change 1.0005e-3) and fails on main: "a stage forcing changed dry air without moving the tracers".
- The moist seam test at the tip drifts 1.796e-15 in both arms on the device, as on CPU.

## Review

AI review, times 2026-09-25 PT. All three reviewed tip `9ba4f15` (tree `c2e4793`) on `14f926f`.

| reviewer | verdict @ sha | notes |
|---|---|---|
| the second independent review agent | `CHECK PR 5 v3 @ 9ba4f15 (tree c2e4793)`: CUDA Release, sm_90 | `ctest -j1` 60 passed, 1 non-CUDA skip; `test_tracer_dry_convention` and `test_stage_forcing_dry_tracer` red on main, green at the tip on the device; moist seam drift 1.796e-15 (13:33) |
| the independent review agent | `SIGN-OFF PR 5 @ 9ba4f15 (tree c2e4793): approve (tracer_dry and stage_forcing are non-vacuous; moist seam is explicitly green-only at 1e-12 and does not discriminate against main)` | independent base and tip builds (torch 2.10); vacuity audit: the tracer and stage-forcing gates fail on main, the moist seam test does not (13:47) |
| the upstream owner's reviewing agent | `CHECK PR 5 v3 @ 9ba4f15 (tree c2e4793): PASS` | census interior-only, severe/min and flux-cut meters unchanged; member lists are unions; CMake registrations 60 -> 65, none removed; all positivity and gate tests pass, `test_scalar` 4/4 CPU, `test_cycle_diagnostics` 8/8; hydro hits on the same theta, main whole-tensor vs this PR's interior: 2-D slab 170 -> 68 (13:59) |
| the second independent review agent | `SIGN-OFF #220 @ c9f9f2f (tree a44c1e5): approve (rebase, range-diff 1 = + 3 ! keep-both CMakeLists, CI green)` | rebase over #219 (15:29) |
| the upstream owner's reviewing agent | `SIGN-OFF #220 @ c9f9f2f (tree a44c1e5): approve (rebase, range-diff 1 = + 3 ! keep-both CMakeLists, CI green)` | range-diff is 1 !, 2 !, 3 =, 4 !; the other 20 files byte-identical to `9ba4f15` (15:31) |
| the independent review agent | `SIGN-OFF #220 @ c9f9f2f (tree a44c1e5): approve (rebase, range-diff 1 = + 3 ! keep-both CMakeLists, CI green)` | independent check of head, base, range-diff and CI (15:33) |

Resolutions agreed in review: the `hydro_forward.cpp` census counts hits on the interior view (the second independent review agent and the upstream owner's reviewing agent, from the slicing and a measurement); the `hydro.hpp` member list is the union (all three); the moist seam test stays a regression check and its tolerance is tightened in a follow-up (all three).

## Limits

- A uniform tracer checks that tracer and dry air stay consistent; it cannot see a wrong donor or upwind choice in tracer transport.
- The upper bound weakens the lower bound from unconditional to conditional on the mass Courant number staying below 1, and it assumes ρ moves by −dt·div(F_mass) alone, which the implicit vertical correction and a forcing writing `du[IDN]` break. Both are stated in `scalar.cpp`.
- **CUDA needs kintera's CUDA library preloaded.** Without `libkintera_cuda_release.so` preloaded, any CUDA path that evaluates internal energy dies with `DispatchStub: missing kernel for cuda` (kintera `call_func2`, not linked by `libsnap_cuda`). The gap is on main too.
- **Limiter hit counts vary by run and device.** In the moist seam test's limited arm the limiter fired 95 times on CUDA (sm_90) and 139, 158 and 172 times in three CPU runs, while the drift is 1.796e-15 wherever it was printed. The counts are therefore not fixed numbers (the 2-D slab's interior count, 68, agreed in every check that measured it); the positivity tests check only that the limiter fired (hits > 0).
- On the dev-gate machine `tests/test_eos.cpp` does not compile against its glibc (`major` is a macro there); identical on main, an environment limit, and every gate binary above built.

## Files

`git diff --name-status 5939862..c9f9f2f` (21 files, +927/−27, the same as `14f926f..9ba4f15`):

```
M	docs/api/mesh.rst
M	docs/user_guide/simulation.rst
M	python/csrc/pyscalar.cpp
M	python/snapy/mesh.pyi
M	src/hydro/flux_positivity.cpp
M	src/hydro/hydro.hpp
M	src/hydro/hydro_forward.cpp
M	src/implicit/vic_redistribute_impl.h
M	src/mesh/meshblock.cpp
M	src/scalar/scalar.cpp
M	src/scalar/scalar.hpp
M	src/scalar/scalar_options.cpp
M	tests/CMakeLists.txt
A	tests/test_flux_positivity_cubedsphere.py
M	tests/test_flux_positivity_cubedsphere.yaml
A	tests/test_flux_positivity_cubedsphere_moist.py
M	tests/test_scalar.cpp
A	tests/test_stage_forcing_dry_tracer.py
A	tests/test_tracer_dry_convention.py
A	tests/test_tracer_dry_convention.yaml
M	tests/test_user_output.cpp
```



## PR #221: hydro: column density reference, floor fallback, stage-weighted implicit dt, wall clamp, balance_column

Merged 2026-09-26; merge commit `9738861`.

## Summary

- **hydro — the vertical column's density reference, floor fallback and implicit stage weighting.** The well-balanced x1 density reference was one bottom-anchored isentrope, wrong by orders of magnitude aloft on a deep column, and the face positivity floor substituted that value at a reflecting top every step. The implicit vertical correction was assembled with the full dt at every RK stage, so a stage that advances only a fraction of dt was under-regularised by the reciprocal of that fraction. Now the reference is p_ref times a 5-point-smoothed rho/p, local to the column; the floor falls back to the adjacent cell's density; and the correction's dt is weighted by the stage for three-stage integrators, using the stage that `advance_local` publishes.
- **hydro — the well-balanced x1 reference never reads a wall ghost (`dynamics: wb-wall-clamp`, default on).** At a physical x1 wall the reference's cell-pressure estimator and its rho/p smoothing reached into the ghost cells, whose contents are not a hydrostatic continuation of the column, so the reference kinked in the two cells nearest each wall and weno5 turned that into a standing vertical force. Both stencils are now clamped to interior cells at a physical wall; internal seams are untouched and boundary functions keep writing the ghosts they want. `wb-wall-clamp: false` reproduces the previous behaviour.
- **hydro — `balance_column` primitive, and the clamp gated to real walls.** A new primitive projects a column onto the discrete hydrostatic balance of the kernel that is actually linked, so a runner no longer re-implements the vertical operator in Python. The clamp now runs only on rows that cross a physical wall, not on a thin block's ghosts.

## Tests

Red = the gate run with the fix it guards removed; green = the tip. RTX 5090, CUDA 13.1, torch 2.10, CPU and CUDA builds (the upstream owner's reviewing agent); the two added assertions A and B were measured by an independent review agent on CPU.

```
Green: test_face_floor, test_forcing, test_hydro_options, test_hydro_ref_x1, test_balance_column:
       5/5 on CPU and on CUDA (cuda_matches_cpu and the three *_cuda twins run on CUDA only; the twins skip without a GPU)
Device path: the *_cuda twins move the block and inputs to cuda:0 and hit hydro_ref_x1_cuda (hydro_dispatch.cu):
  face_floor 1 call; reaches_the_x1_reference 2 (clamp on, then off); rk3_stage_weighting 3 (one per stage)
Red arms (CPU and cuda:0 agree):
  face_floor, floor lines back to the dsf reference: |dipped-face mass flux| 9.4699757327708193e-08 (limit < 1e-9);
    dipped_mom 0.030372413990551024 (needs > 0.03042)
  stage weighting, drop the wght2 scaling: stage momentum diff 0 (needs > 1e-6)
  wb-wall-clamp wire -> false: wb_wall_clamp_reaches_the_x1_reference fails (allclose true, max diff 0)
  balance primitive, revert its src/python hunks: test_hydro_ref_x1 fails; test_balance_column does not compile
  balance primitive, gate hunks only: test_hydro_ref_x1 + test_balance_column fail
  A, drop `phydro->rk_stage = stage` in MeshBlockImpl::advance_local: rk3_stage_is_published_by_block_step fails at
    stages 0, 1 and 2 (actual -1); green 1/1, test_forcing 26/26
  B, relax the balance solver's convergence threshold 1e-10 -> 1e-4: the new residual < rtol bound fails,
    7.40e-05 (uniform) and 5.27e-05 (nonuniform) vs 1e-10; green, test_balance_column 7/7
Green on cuda:0: mass flux 6.3084574550540378e-11, dipped_mom 0.030447506353481969;
  clamp max diff 3.48e-4; stage diff 0.0211498438562; CPU parity ~1e-12 relative or better
Regression only: test_hydro_options (unchanged under the balance-primitive reverts); wb_wall_clamp_ships_enabled pins the
  parser default and key, not the numerical path
Full suite with the twins: CUDA_VISIBLE_DEVICES=0,1 ctest -j 1 -> 66/66, 0 skipped, 374 s; at 93d06ba on a fresh
  CUDA build (native sm_120; nsys: hydro_ref_x1 kernel launched 1, 2, 3 and 4 times for face_floor, clamp, rk3 and
  cuda_matches_cpu): 66/66, 0 skipped, 399 s
```

## Compatibility

- Every run with gravity and a well-balanced x1 reference changes numerically: the density reference, the wall-cell stencils and the stage-weighted implicit correction are all new.
- `wb-wall-clamp: false` restores the previous wall behaviour; no card in the tree sets it.
- New API: `balance_column` (C++ and Python).

## Provenance

- Four commits on main `bc4d411`, one per concern, plus the tests:
  - `4d8af9f` hydro: the vertical column -- density reference, floor fallback, stage-weighted implicit dt
  - `bd91588` tests: the face-floor fallback and the rk3 stage weighting of the implicit correction
  - `8e3b985` hydro: the well-balanced x1 reference never reads a wall ghost (dynamics/wb-wall-clamp)
  - `f06264a` hydro: expose the discrete hydrostatic balance as a primitive, and gate the wall clamp
  - `93d06ba` tests: device twins for the gates; rk_stage through a real step; balance residual bound
- Two append-only conflicts against main, both kept: `tests/test_hydro_options.cpp` (main's `reject_unsupported_implicit_scheme` first, then the two `wb_wall_clamp_*` tests; `<snap/mesh/meshblock.hpp>` once) and `tests/CMakeLists.txt` (`test_sedimentation_guards` first, then `test_balance_column`). Three independent replays of the three fixes reached the same tree `509ea9e` (the PR author, a second independent review agent, the independent review agent).
- `face_floor_uses_adjacent_density` was written by the second independent review agent; the `*_cuda` twins by the upstream owner's reviewing agent; the A and B assertions by the independent review agent.

## Review

| reviewer | verdict @ sha | notes |
|---|---|---|
| the second independent review agent | `SIGN-OFF #221 @ 93d06ba (tree 868344c): approve (replay tree 509ea9e)` | independent replay of the three fixes onto `bc4d411` reached `509ea9e`; the gate numbers are the upstream owner's reviewing agent's and the independent review agent's (20:17 PT) |
| the upstream owner's reviewing agent | `SIGN-OFF #221 @ 93d06ba (tree 868344c): approve (fresh CUDA Release build, native sm_120, ctest 66/66)` | both GPUs visible, 0 skipped, 399 s; twins and `cuda_matches_cpu` on the device (nsys: 1/2/3/4 launches); A and B pass; `test_forcing.cpp` blob `47429819` (20:18 PT) |
| the independent review agent | `SIGN-OFF #221 @ 93d06ba (tree 868344c): approve (independent replay 509ea9e; vacuity audit; A and B red/green)` | A red when `advance_local` stops publishing `rk_stage`, green 1/1, test_forcing 26/26; B red with the relaxed balance threshold, green 1/1, test_balance_column 7/7; `test_forcing.cpp` blob `47429819`; CPU runs (20:3x PT) |

## Limits

- The face-floor test does not cover the fallback's edge replication.
- `wb_wall_clamp_reaches_the_x1_reference` proves the option is wired into the solver (the two settings differ), not the physical result.
- `test_hydro_ref_x1`'s nonuniform-pref equality does not see the clamp, and the MPS dispatch guard is not covered (no MPS in CI).
- In the CUDA build the non-twin tests use CPU tensors; the device path is covered by the three `*_cuda` twins and `cuda_matches_cpu`.
- On a fresh CUDA build with native sm_120 (the upstream owner's reviewing agent), each `*_cuda` twin takes 6.6 to 8 s against 0.35 s for `cuda_matches_cpu`; the cause of that delay is not established, and results are unaffected. The A and B assertions run on CPU tensors.
- One full CUDA suite run before the final one was 60/66: six multi-process tests (test_exchange, test_output_barrier, test_check_redo_parallel, test_exchange_ucx, test_exchange_ucx_cuda, test_straka) failed fast, then passed on an immediate rerun and in the next full run. Their first-run output was not kept, so the cause is unknown; this PR does not touch them.



## PR #222: coord, cubed-sphere: single-valued faces from one global grid; correct exchange on a subdivided panel

Merged 2026-09-27; merge commit `dcb3f7d`.

## Summary

- **coord, mesh, output — single-valued block faces from one global grid.** Each block built its coordinate faces from its own sub-interval, so one global face was a different double in different blocks and in different decompositions, by 1 ULP, and every gnomonic metric term inherited the difference. The global grid also had no way to be absent: options built programmatically (layout + integrator + a block from Python), a card with bounds but no cells, `MeshOptions.set_local_horizontal_cells`, and a super-resolution output block could each leave a block sliced from a grid that does not describe it (for example `start (5) + length (13) exceeds dimension size (6)`). Now every block's faces are sliced from one global face array; `global_nxN` defaults to 0 ("no global grid declared") and `resolve_global_grid()` adopts the block's own bounds where none was declared, or checks the block against the declared grid (a few ULP of tolerance), and refuses a block that cannot be a grid.
- **cubed-sphere — a correct cross-panel exchange on a subdivided panel.** On a panel divided among several blocks the cross-panel ghost exchange failed two ways: the source strip was one cell too narrow for the along-edge slide of the interpolation source, and a block offset was folded into the double before `floor()`. The slide is zero only at nb2 = 2 (its one interior seam sits at beta = 0); at nb2 = 3 it is 1.25 cells and at nb2 = 4 1.77 cells, past a one-cell strip at any resolution. Now both sides carry a tangential margin of nghost cells, the block shift is added as an integer to the global source coordinate, and an interpolating sync on a subdivided panel runs as two rounds (intra-panel, then cross-panel) with corners synthesised once after both. The phase flag is bound in Python.

## Tests

CPU Release and CUDA Release sm_90 (a second independent review agent). Red for the exchange is the test run at the single-valued-faces commit (`38a3de5` before the rebase onto `bda4b6c`, now `6630ba6`; without the exchange fix); green is the tip's code. These red/green runs were measured on the pre-rebase commits.

```
test_coordinate (faces commit), CPU: does not compile on the old main bc4d411 (the test uses the new ix2()). At 38a3de5,
  blocks_match_the_undecomposed_grid_bitwise and the_yaml_path_keeps_its_declared_global_grid pass.
subdivided_panel_exchange_matches_one_block (exchange commit), CPU: at 38a3de5 only nb2 = 4 throws
  (index -1 out of bounds for dimension 1 with size 4, in GnomonicEquiangleImpl::_interp_ghost_LR);
  nb2 = 1 and 2 match. With the exchange fix, all three match (torch::equal on interior x2f, dx2f, hydro_u[IDN]).
subdivided_panel_exchange_matches_one_block_cuda, cuda:0 (sm_90): the same split. At 38a3de5 only nb2 = 4 fails
  (device-side index assert during initialize); with the exchange fix all three match.
test_local_horizontal_cells_python: prints OK; snapy imported from the build under test (checked via snapy.__file__
  and ldd), and the script checks x1, x2 and x3 face bounds.
subdivided_panel_exchange_matches_one_block_cuda at 3944838 (V100): the Mesh is now built on the device; the test asserts
  one CUDA stream per block in the worker pool (0 on CPU), and nb2 = 2 and 4 still match nb2 = 1 bitwise.
test_local_horizontal_cells.py (px = 2, py = 3; the setter called with (8, 1) then (4, 6)): RED at 9c7ebaa
  ("is not exactly 8 cells of the declared global x2 grid"), GREEN at 6823c84; also passes on main.
CUDA ctest -j1 at 6823c84 (the upstream owner's reviewing agent; 2x RTX 4000, torch 2.10.0+cu128, nvcc 12.9):
  68/70; main: 66/68; the same 2 fail on both (test_eos moist_mixture/cuda_Double: out of memory;
  test_exchange_ucx_cuda: invalid device ordinal with one GPU visible).
CUDA ctest -j1 (sm_90, before this review's two commits): 63 passed, 0 failed, 1 skip (test_python_import_path_python,
  SNAPY_TEST_PYTHONPATH unset; not a CUDA skip).
```

## Compatibility

- Face coordinates can change by 1 ULP in multi-block and multi-decomposition runs: they are now the same double in every block.
- Options that describe a block inconsistent with a declared global grid, or a block with no cells or a zero span, now raise where the grid is formed instead of aborting later or building with zero spacing.
- Ghost interpolation of order 4 on the cubed sphere is now refused: it reaches one cell past the strip the cross-panel exchange carries, at any number of blocks per panel.
- New Python binding: the exchange phase flag (`intra_panel_only`) in `python/csrc/pylayout.cpp`; `docs/api/mesh.rst` and `python/STUB_FILES.md` updated.

## Provenance

- Eight commits on main `bda4b6c`:
  - `6630ba6` coord, mesh, output: single-valued block faces from one global grid
  - `e55afcc` cubed-sphere: a correct cross-panel exchange on a subdivided panel
  - `597e8d5` tests: a subdivided cubed-sphere panel exchanges exactly like one block
  - `cda2034` tests: run the subdivided-panel exchange check on CUDA too
  - `00699e5` coord: a declared block must cover exactly nx global cells
  - `9c7ebaa` tests: set_local_horizontal_cells twice on code-built multi-block options
  - `6823c84` mesh: set_local_horizontal_cells can be called more than once
  - `3944838` tests: the subdivided-panel CUDA check builds its Mesh on the device
- The two fix commits are one source commit split by concern. Together their tree equals that source commit applied whole on `bda4b6c`, apart from one line: `test_local_horizontal_cells_python` is registered through main's `snapy_add_python_test`, so it gets the test `PYTHONPATH` (found by the upstream owner's reviewing agent's hunk map).
- The exchange test and its CUDA twin were written by the second independent review agent; the tests commit is formatted with clang-format 20.1.4 `-style=Google`, as the pre-commit hook runs it.

## Review

- **Review fix.** A fresh review found that a second `set_local_horizontal_cells` call on code-built multi-block options threw; `6823c84` removes the resolve from the setter (grids are still validated when the coordinate is built and at repartition), with a regression test (`9c7ebaa`) that fails before it.

| reviewer | verdict @ sha | notes |
|---|---|---|
| the second independent review agent | | |
| the upstream owner's reviewing agent | | |
| an independent review agent | | |

## Limits

- `test_coordinate`'s red on main is a compile error (the new `ix2()`), not a failed assertion.
- nb2 = 3 is not in the exchange test (nx2 = 8 is not divisible by 3); nb2 = 4 is the arm that fails without the fix.
- On the CUDA review machine an editable install of an older snapy was on the Python path; twenty first-pass failures imported it and passed when rerun against this tree. The numbers above are from the rerun.
- This PR and #221 both touch `src/mesh/meshblock.cpp`; whichever merges second is rebased.
- `cells.interp_order: 4` on the cubed sphere is now refused at construction (main accepted it): the 4-point ghost interpolation reaches one cell beyond what the cross-panel exchange carries; no card, test or example sets it, and reconstruction order (cp5/weno5, nghost 3) is unaffected.
- repartition (called by Mesh and by from_yaml) takes the block's bounds from the declared global grid, so local x2/x3 bounds set by hand on code-built options that disagree with an already declared global grid (from YAML, from an earlier set_local_horizontal_cells call, or from global_*) are replaced without a message, as main already did for every repartition; no shipped card, test or caller sets such bounds, and the check that remains is that the resolved grid is consistent, not that hand-set local bounds were kept.




## PR #223: eos, implicit, mesh: own dry gas, redo on repairs, gravity work against relative potentials, cloud parent index

Merged 2026-09-26; merge commit `bda4b6c`.

## Summary

- **eos, sedimentation — the EOS keeps its own dry gas.** The EOS and the fused sedimentation read the dry molar mass and cv from kintera's process-global species tables, which the first card to initialise in a process owns. They now use the EOS's own dry gas.
- **mesh, implicit — redo a step the scheme had to repair, and name the cause.** A step was redone only when the state came out at or within 0.1% of the density or pressure floor after the RK average, which hides two repairs: pass 3a's VIC dry-gas availability clamp can empty a donor cell, and `apply_conserved_limiter_` can raise an interior cell to the density or temperature floor after the average. Both are now flagged (reset at stage 0, reduced over ranks in both the MeshBlock and Mesh redo paths), a marked step is redone at half dt, and the log line names the cause: `Density/pressure at or within 0.1% of the floor, the VIC dry-gas clamp emptied a cell, or the limiter patched one. Redoing the step with smaller dt (causes: floor clamp limiter).`
- **implicit — gravity work on the mass actually moved, against relative potentials.** The VIC charged gravity work with the absolute potential, whose origin is arbitrary; phi cancels only while drho·V equals the face transfers, and an availability clamp breaks that identity, so the mismatch times the absolute phi went into the clamping cell's energy. The column total stayed conserved, so the existing energy test could not see it. Pass 3a/3b now record the mass each face actually moved after the clamps and charge it against the potential difference between face and cell centre.
- **eos — the cloud parent cache mixes two species index spaces.** `cache_cloud_parents_` looked a cloud up in kintera's compact list of reacting species using an index into the global registry; the two coincide only when every declared species reacts. `examples/uranus.yaml` (twelve species; only H2S and its two condensates react, in three reactions) reads past the end (heap-buffer-overflow under a sanitizer); on other cards of that shape the parent list comes out empty and the limiter clamps a negative condensate to zero, inventing mass. The fix uses the global registry throughout.

## Tests

Red = the gate run with the fix it guards reverted; green = this head. A second independent review agent (sm_90 CUDA build) and the upstream owner's reviewing agent (RTX 5090 sm_120 CUDA build); each count is tied to its own build.

```
Tests (7563ac1, tree 2c61ea46)

test_eos_species_registry, default device, CUDA-linked module. Green: all four relative changes 0. Red with ideal_moist.cpp and sed_hydro.cpp from 60f272e's parent: W->T 1.100e+01, UT->I 9.005e-01, W->E 3.233e+00, step diff 1.349e-01. FAIL. (the second independent review agent, sm_90)

forcing.implicit_gravity_work_ignores_the_potential_origin_under_clamp. Green at the tip. Red with 6f0b0f6's two implicit files reverted: 6.1309 against bound 5.20e-9. FAILED. The upstream owner's reviewing agent measured 6.131 against 5.197e-9.

Cloud-parent test_cloud_parent_slots. Green: 4/4, cpu and cuda, float and double. Red with equation_of_state.cpp reverted: segfault on the first case (cpu_Float), not an assertion failure. The upstream owner's reviewing agent got rc 139.

Redo-on-repair gate (the upstream owner's reviewing agent, fresh CUDA Release build detached at fbc5501). Green at fbc5501: test_backward_substitution 5/5, test_forcing 25/25 (ctest 2/2). Red with the redo commit's six source files (implicit_hydro.cpp/.hpp, vic_redistribute_impl.h, mesh.cpp, meshblock.cpp/.hpp) put back to fbc5501^, tests kept: test_backward_substitution 3/5 (dry_only_transport_is_conservative_and_clamped, line 173: mass_fix[IPR*stride1] 0, expected 1; a_negative_dry_fraction_still_marks_the_clamped_donor, line 211: mass_fix[IPR*stride1+1] 0, expected 1; the -0.1 clamp bound and zero-mark checks still pass, so what is missing before the redo commit is the donor mark); test_forcing does not compile (test_forcing.cpp:606 calls MeshBlockImpl::limiter_patch_hit, added by the redo commit), so this red has no per-pressure values. Restored: 5/5 and 25/25. Targeted red at the tip: dropping the _limiter_patched flag update fails the limiter-patch test at pres=1000; restored, test_forcing 26/26.

Python ctest -R '_python$' (the second independent review agent, sm_90): 17 passed, 1 skipped. The only skip is test_python_import_path. No CUDA skip.

C++ ctest -E '_python$' (the second independent review agent, sm_90): 46 tests, 0 skipped. No CUDA skip. The four stale-library failures were re-run on the rebuilt tip and passed (backward_substitution 5/5, straka 67.41 s, shallow_xy 73.44 s, shallow_splash 8.72 s).

Suite count on the upstream owner's reviewing agent's sm_120 build: 66/66, 0 skips. This sm_90 build registers 64 tests (46 C++ + 18 Python).

CI 36213471210: pre-commit, ubuntu, and macOS success.
```

## Compatibility

- Runs where the VIC dry clamp empties a cell, or where the conserved limiter patches an interior cell, now redo the step at half dt.
- Implicit runs with a clamp firing change numerically in the clamping cells' energy.
- Cards that declare a species no reaction uses change in the conserved limiter's condensate repair (and no longer read out of bounds).

## Provenance

- Four commits on main `9738861` (after #221), rebased from `bc4d411` with `git range-diff` all `=` (tested head `7563ac1` -> `97b3be4`):
  - `a0a4716` (was `60f272e`) eos, sedimentation: the EOS keeps its own dry gas
  - `dcf29e6` (was `fbc5501`) mesh, implicit: redo a step the scheme had to repair, and name the cause
  - `ec8123b` (was `6f0b0f6`) implicit: gravity work on the mass actually moved, against relative potentials
  - `97b3be4` (was `7563ac1`) eos: the cloud parent cache mixes two species index spaces
- One real conflict, in `src/mesh/meshblock.cpp` `apply_redo()`: main (#218) had reworded the redo log line. The resolution keeps this PR's causes and main's criterion ("at or within 0.1% of the floor"); main's floor test was already `!(min > 1.001*floor)`, so only the text differed. `tests/CMakeLists.txt` keeps both registrations (`test_wall_saturation` first, then `test_cloud_parent_slots`). The replay tree `2c61ea4` was reproduced independently by the second independent review agent.

## Review

| reviewer | verdict @ sha | notes |
|---|---|---|
| the second independent review agent | `SIGN-OFF #223 @ 97b3be4 (tree 08d679f): approve` | range-diff `bc4d411..7563ac1` vs `9738861..97b3be4` 4/4 `=`; CI 36217297122 green; the test_forcing abort seen tonight was a kintera header/library mismatch in the build (reproduced on `bc4d411`), and a matched build of main passes 26/26 with one CUDA-only skip; earlier: the species-registry, potential-origin and cloud-parent gates, Python ctest 17 passed |
| the upstream owner's reviewing agent | `SIGN-OFF #223 @ 97b3be4 (tree 08d679f): approve` | tree and 4/4 `=` range-diff vs `7563ac1` confirmed; fresh CUDA Release build including sm_120 (RTX 5090, nvcc 13.1, torch 2.10+cu128); kintera 2.5.0 headers and libraries from one hash-verified prefix (CMakeCache and runtime); test_forcing 29/29, test_backward_substitution 5/5, test_cloud_parent_slots 4/4, 0 skips, CUDA cases on GPU 0; earlier at `7563ac1`: CUDA ctest 66/66 and red/green for the redo, potential-origin, cloud-parent and limiter-flag gates |
| an independent review agent | `SIGN-OFF #223 @ 97b3be4 (tree 08d679f): approve` | exact head and tree verified, 0 behind and 4 ahead of `9738861`; range-diff 4/4 equivalent; complete 15-file diff reviewed, no findings; CI 36217297122 (pre-commit, Ubuntu, macOS) green at this head; a local build was not possible (no compatible kintera), so the red/green and CUDA runs are the second independent review agent's and the upstream owner's reviewing agent's |

## Limits

- NMASS>0 is not a supported build. A dry-plus-cloud card that passes the species-count check still dies in the implicit solver (Eigen Matrix<double,5,5>, IPR=5) before the gravity-work path, with both the redo commit's and the gravity-work commit's implicit files. No CI job sets NMASS>0.



## PR #225: gravity work: remove the face form's curvature excess

Merged 2026-09-27; merge commit `c8d9824`.

## Merge summary

**gravity work: remove the face form's curvature excess.** Numbers change for cp3, cp5 and weno5 x1 faces with x1 gravity; this includes every shipped example with gravity.

- **Problem.** The face-form x1 gravity work books g times the two-face average of the face mass flux F, while the kinetic energy sees the cell momentum m = ρv. snapy reconstructs ρ and v = m/ρ separately. With cp3, cp5 or weno5 x1 faces, the two-face average of F therefore exceeds m by dx²/12 (m'' + ρ'v') plus higher order, and the excess heats cell by cell. In a resting, forcing-free stratified column it drives grid-scale vertical motion.
- **How found.** Grid-scale vertical motion grew in a resting stratified atmosphere in a downstream configuration that is not in this repository. Its numbers are not quoted, since reviewers cannot rerun it.
- **Fix.** The m'' part is removed as the divergence of H = dx/12 (m_i − m_{i−1}), with H = 0 at physical x1 walls, so E + Σ ρΦV still telescopes. It is applied only with cp3, cp5 or weno5 x1 faces. The implicit half is unchanged.
- **How much it removes.** It removes exactly 2/3 of the leading excess for linear ρ and linear v at g = 0 (0.45 with gravity on a hydrostatic linear-ρ column), and 0.88 for a sinusoidal v (10 km wavelength) on an isothermal column (7.3 km scale height). The ρ'v' remainder is not the divergence of any local face quantity, so no correction that keeps the face form's exact energy budget can remove it. That would take a change to the mass flux itself.
- **Why only three schemes.** In a convergence study at 32/64/128 cells, the remainder left by cp3, cp5 and weno5 converges to dx²/12 ρ'v' at 4th order. weno3 (order 2.6), plm and dc do not converge to it, and ppm is not implemented. No card in this repository uses cp3, weno3 or ppm.
- **Tests, red to green.** New `forcing.vertical_gravity_work_removes_the_curvature_excess` and its `_cuda` twin. On the base the cp3 arm books round-off (≤1.8e-12) where 2e-5 is expected, on CPU and V100 (earlier revisions); with the fix both pass. The test also runs cp5 and weno5 arms at nghost 3 (added in review): with the guard narrowed to cp3 they miss 2e-5, and they pass on the head.
- **CUDA gate at `fbd934b`** (RTX 5090, CUDA Release, sm_120): full ctest -j1 71/71; main `644c903` 69/71, whose 2 failures were a reference-file download error and passed 2/2 on rerun; 0 CUDA-skipped gtest cases. test_forcing on device: the curvature test and its _cuda twin fail on main (cp3/cp5/weno5 book round-off ~1e-12 where 2.0e-5 is expected) and pass at `fbd934b` (31/31).
- **A/B, 100 cycles.** `straka_single` with plm or dc x1 faces, and `shock`, are bit-identical to main. `straka_single` as shipped (weno5) differs from main in all 18340 cells, and is bit-identical to the revision reviewed first.
- **Status.** Head `fbd934b` (rebased onto main `644c903` after #227; range-diff vs `a4d3f44` all '='), CI run 36319431215 green.
- **Review.** SIGN-OFF approve from an independent review agent and the upstream owner's reviewing agent at `fbd934b` (range-diff re-sign). The upstream owner's reviewing agent's three asks on an earlier revision (the "only at higher order" claim, the weno3/ppm scope, a CUDA arm for the test) are all made.
- **Size.** 2 files, +105/−0 (`src/hydro/hydro_forward.cpp` +25, `tests/test_forcing.cpp` +80).
- **Limits.** Where the limiter or sedimentation changes F, the correction removes only an estimate. A single-block periodic x1 domain loses the correction in its two end cells. On a stretched x1 grid the 1/12 form is approximate. A lapse-rate column keeps a further dx² term of about 4% of ρ'v'.
- **Suggested squash message:** `gravity work: remove the face form's curvature excess`

---

## 1. The defect and the change

**Defect.** The face-form x1 gravity work in `src/hydro/hydro_forward.cpp` books g times the two-face average of the face mass flux F, while the kinetic energy sees the cell momentum m = ρv. snapy reconstructs ρ and v = m/ρ separately. The primitive v = m̄/ρ̄ equals the average of v plus dx²/12 ρ'v'/ρ, to O(dx⁴). A scheme that treats v as a cell average and is at least 3rd order then returns F_f = (ρv)(x_f) + dx²/12 ρ'v', so

(F₋ + F₊)/2 − m̄ = dx²/12 [(ρv)'' + ρ'v'] + higher order = A + B.

The excess heats cell by cell. In a resting, forcing-free stratified column it drives grid-scale vertical motion.

**Change.** The correction removes the m'' part, A, as the divergence of H = dx/12 (m_i − m_{i−1}). H is set to zero at physical x1 walls, so E + Σ ρΦV still telescopes. The code's correction is C = (m_{i+1} − 2m_i + m_{i−1})/12 = A + O(dx⁴).

B = dx²/12 ρ'v' stays. An expression is the x-derivative of a local function only if its Euler operator vanishes, and B's operator (−v'' with respect to ρ, −ρ'' with respect to v) does not. So B is not the divergence of any local face quantity. Its column sum is also nonzero in general, and no divergence with H = 0 at the walls can cancel that. Removing B would take a change to the mass flux itself.

The fraction removed, A/(A + B), depends on the profile:
- exactly 2/3 at g = 0 for linear ρ and linear v, where m'' = 2ρ'v' (0.45 with gravity on a hydrostatic linear-ρ column, from the further dx² term in the last Known limit);
- 0.88 for a sinusoidal v (10 km wavelength) on an isothermal column (7.3 km scale height);
- in general B/A ~ 1/(kH), for wavenumber k and density scale height H.

On that isothermal column at 32 cells per wavelength, what remains after the correction equals dx²/12 ρ'v' to 2% (cp5, weno5) or 7% (cp3), and the difference converges at 4th order.

**Scope.** The correction applies only with cp3, cp5 or weno5 x1 faces, where the remainder is that ρ'v' term. With dc or plm faces the excess has a different form: the remainder is 4-8 times ρ'v' and does not shrink relative to it. With weno3, the nonlinear weights leave a dx² face error near extrema of v: the remainder is 1.8-4 times ρ'v' and converges at order 2.6. ppm is not implemented. The implicit half is left unchanged.

The correction sits in the explicit gravity-work block of `HydroImpl::forward`. It uses the face work built from the x1 mass flux after positivity scaling and sedimentation, and adds to the same energy tendency as before.

---

## 2. Tests

**Environment.** kintera v2.5.0 (the PyPI release upstream CI installs) and torch 2.6.0, with local compatibility shims that are not in the PR. The base arm is the new test alone on the base.

`vertical_gravity_work_removes_the_curvature_excess` is a helper that runs on a device, with a CPU `TEST` and a `_cuda` `TEST`. On a seeded column it checks three things:
- cp3 books `dt * g * dx²/12 * (ρv)''` off the walls;
- weno3 and dc book nothing;
- cp5 and weno5 (three ghost cells, asserted) book the same value as cp3;
- the column sum stays zero.
The tolerance is 1e-9: the excess is a difference of O(1e3) energy tendencies built from O(1e5) fluxes. The signal is 2e-5. The test checks the correction, not that the booked work equals ρvg.

Test results (earlier revision, before the rebase; re-gated at `fbd934b`, see the merge summary):

| test | base + test | with the fix |
|---|---|---|
| `vertical_gravity_work_removes_the_curvature_excess` (CPU) | FAIL on the cp3 arm: books ≤1.8e-12 where 2e-5 is expected; the weno3 and dc arms and the column sum pass | PASS |
| `vertical_gravity_work_removes_the_curvature_excess_cuda` (V100) | FAIL, same arm and value | PASS |
| whole `test_forcing`, CPU build | 28 passed, 1 failed, 2 skipped (the `_cuda` cases) | 29 passed, 2 skipped |
| whole `test_forcing`, V100 build | 29 passed, 2 failed (the two new cases) | 31/31 |

The cp5 and weno5 arms were added in review (a4d3f44): with the guard narrowed to cp3 they book 0 and miss 2e-5, while the other arms pass; on the head all pass.

**Full `ctest -j 1`** (earlier revision, before the rebase; re-gated at `fbd934b`, see the merge summary).
- **CPU (67 tests).** The only outcome that changes is `test_forcing` (fails on base + test, passes with the fix). The other failures on our test machine are the same on main and with this branch: `test_exchange`, `test_output_barrier`, `test_check_redo_parallel`, `test_exchange_ucx`, `test_straka`, `test_shallow_xy`, `test_shallow_splash` and `test_restart_cycle_limit`. All are multi-process tests that fail on a port clash on that machine.
- **V100 build (66 tests, UCX off).** The same seven fail on both arms, without `test_exchange_ucx`. No gtest case is skipped on that build.

---

## 3. Measurements

**Independent build (Xeon CPU; kintera v2.5.0).**

**Per-scheme convergence.** A standalone C++ driver, not part of this PR, ran one hydro forward per case against this commit's library. The setup:
- a column over x1 in [0, 20 km], lmars, ideal gas (R 286.7, γ 1.4), limiter off;
- cell averages by 6-point Gauss quadrature, measured in the window 3-17 km;
- N = 32/64/128 cells, so the 10 km wavelength spans 16/32/64 cells.

The metrics:
- e is the two-face average of F minus the cell ρv;
- C is the code's correction, read two ways: from the formula, and as booked minus face-form from the tendency. The two agree to ≤2.9e-14 in every corrected case;
- B = dx²/12 ρ'v', computed analytically;
- the fraction removed is f = ⟨C,e⟩/⟨e,e⟩, and the residual measure is q = rms(e − C − B)/rms(B).

Isothermal hydrostatic column (H 7.31 km), v = 0.5 + 0.3 sin(2πz/10 km), gravity on (the well-balanced path). The analytic B/A is 0.24, so the analytic f is 0.88:

| x1 scheme | f at N=64 | q at N=32 / 64 / 128 | order of rms(e − C − B), 32→64, 64→128 | corrected |
|---|---|---|---|---|
| cp3 | 0.871 | 0.29 / 0.074 / 0.019 | 3.96, 3.95 | yes |
| cp5 | 0.878 | 0.067 / 0.016 / 0.004 | 4.09, 4.01 | yes |
| weno5 (scale and shock on) | 0.877 | 0.13 / 0.019 / 0.004 | 4.78, 4.20 | yes |
| weno5 (scale and shock off) | 0.878 | equal to cp5 to 4 digits | | yes |
| weno3 (scale on) | 0.744 | 4.2 / 2.7 / 1.8 | 2.62, 2.64 | no |
| plm | 0.319 | 5.2 / 4.5 / 4.4 | 2.23, 2.02 | no |
| dc | 0.335 | 7.9 / 8.1 / 8.4 | 1.98, 1.95 | no |

For the three schemes marked "no" the table shows what the correction would do if applied; the code does not apply it to them. Other profiles:
- **Linear ρ and linear v, gravity off.** f = 0.6667 for every scheme: exactly 2/3. dc's residual converges at order 1.
- **Lapse-rate column** (6.5 K/km), cp5 and weno5, gravity on. f = 0.885 and q = 0.08 / 0.040 / 0.037: q stalls at about 4% of B. With gravity off, q = 0.07 / 0.017 / 0.004 (order 4.1). That places the extra dx² term in the well-balanced reconstruction; it is the last item in Known limits.
- **Isothermal column, gravity off.** cp5 and weno5 give q = 0.017-0.034 at N=64 (order ≥ 4), but cp3 gives q = 18.8 / 9.4 / 4.8 (order 3.0). The correction runs only with gravity on, so the gravity-on rows above decide the scope. Hypothesis, not tested: without gravity the column is unbalanced, and cp3's O(dx³) pressure jump enters the lmars mass flux.

**A/B, 100 cycles from a fixed initial condition, CPU.** Three arms: main, this commit, and the revision reviewed first (whose guard excluded only dc and plm).

| card (`examples/`) | cfl | this commit vs main | this commit vs first revision |
|---|---|---|---|
| `straka_single.yaml`, x1 plm | 0.3 | bit-identical | bit-identical |
| `straka_single.yaml`, x1 dc | 0.3 | bit-identical | bit-identical |
| `shock.yaml` (weno5, no gravity) | 0.9 | bit-identical | bit-identical |
| `straka_single.yaml` as shipped (weno5) | 0.9 | differs in 18340 of 18340 cells; max\|Δu\|/max\|u\| per row: ρ 4.6e-6, m1 1.6e-5, m2 1.6e-5, m3 0, E 1.3e-7 | bit-identical |
| `straka_single.yaml`, x1 weno3 | 0.3 | bit-identical | differs in 18340 cells (m1 2.8e-5) |

weno3 is the only behaviour change from the first revision, and no card in this repository uses it. With plm or dc faces, `straka_single` goes non-finite at the card's own cfl 0.9 in both main and the fix, so those arms run at cfl 0.3. On a V100 (nvcc 12.2, torch 2.6.0), `shock` and `straka_single` with plm faces (cfl 0.3) are bit-identical to main, and `straka_single` as shipped differs, with per-row values equal to the CPU values to 3 digits.

**The upstream owner's reviewing agent**, on the first revision `e239dba` (10:04 post; CUDA build on RTX 5090, nvcc 13.1.115, torch 2.10.0+cu128), quoted: "base + new test gives test_forcing 29/30 (only the cp3 check of the new test fails, 1e-12 vs 2e-5); head 30/30. Full snapy suite base 67/68, head 68/68, so no regressions." And: "Claimed vs measured (same on CPU and cuda:0): signal 2e-5 = 2.000e-5; round-off 1.4-2.2e-12 (claimed ~1e-11); tendencies 9e3 from fluxes 2.2e5; sign-flip mutation moves it by 4.0e-5; unzeroed wall 3.87e-4 inner / 5.07e-4 outer (claimed ~3e-4), caught only by the telescoping check." And: "CPU and CUDA agree to 1.5e-9."

On this revision, quoted: "REVIEW … @ 693dc89: approve — all three earlier asks are addressed (formula, allow-list, _cuda test) and the numbers reproduce." Its measurements on cuda:0: base plus the head's test file gives test_forcing 29/31 (only the cp3 arm fails, CPU and cuda), head 31/31, with the `_cuda` test running on the GPU; full ctest base 67/68, head 68/68. Code vs formula ≤4e-15; convergence orders cp3 3.99/4.00, cp5 4.03/4.01, weno5 4.18/4.05; weno3 2.68 (64→128 only; 0.99 on 32→64); plm/dc remainders about 5x and 9.5x ρ'v', not shrinking; at N = 32 the remainder is within 8.7% / 1.8% / 2.0% of ρ'v' (cp3/cp5/weno5); 0.88 matches the analytic value (0.887/0.878); "2/3 is exact at g=0". A/B over 100 cycles on cuda:0, bitwise: weno5 previous revision vs this one identical; plm, dc, shock and weno3 identical to main; weno5/cp5 differ as intended (|dp| 1.3e-2 Pa). Known limits (a)-(c) match the code; it did not reproduce the 4% lapse-rate figure. Its wording nit ("exactly 2/3" is the g = 0 ratio; with gravity on a hydrostatic linear-ρ column the flux gives 0.45) is folded into the commit message. These measurements were at `693dc89`; the head has since gained a test commit and a rebase, and the patch was re-gated at `fbd934b` (CUDA gate in the merge summary).

**Review note: the clean-cell excess (settled).** Its 2.93e-4 was one cell (x1 = 3.5) of the test's seeded cp3 column; the −1.19e-3 is the mean over all 48 off-wall cells, and it reproduces it exactly. Making p hydrostatic takes the mean to +2.7e-4; with g = 0 the excess is 3.0e-4 in every cell, which is the formula. In its words: "My single cell was cherry-picked; the g=0 run is the clean evidence." The removed value, 2.0e-4, matches in both measurements.

---

## Known limits

From the commit message:
- The correction uses the cell ρv. Where the positivity limiter rescales F, or sedimentation adds to it, the correction removes only an estimate of the curvature part. Energy is conserved regardless, since the correction is a divergence.
  ρ in the correction is the total density (gas and condensate; `prim[IDN]` in both moist EOS), so condensate carried by the flow is covered; only its sedimentation flux lies outside ρv.
- A periodic x1 face counts as a physical boundary, so on a single-block periodic x1 domain H is zeroed at the seam. The column still telescopes, but the two end cells lose the correction. No card combines x1 gravity with periodic x1; in this repository only the `shallow_xy` examples are periodic in x1, and they have no constant gravity.
- On a stretched x1 grid the 1/12 form is approximate (H uses the local centre spacing); conservation is unaffected. A stretched x1 grid is reachable only through `reset_coordinates`, which no card or example calls.
- Where ρ/p varies with height, a further dx² term remains: about 4% of ρ'v' on a 6.5 K/km lapse-rate column.
- ρ'v' itself remains (section 1): about 1/3 of the leading excess on linear profiles and 0.12 on the isothermal sinusoid.
- ppm x1 faces are not implemented and are not corrected; weno3, plm and dc are deliberately not corrected.
- The cp5/weno5 test arms check that the correction is booked with the formula's value, not that it cancels the true face excess; there is no stretched-grid arm (only `reset_coordinates` stretches x1, no card uses it).

The previous revision also named the cell momentum `phi` in a comment, while `phi` is the geopotential elsewhere in the block. It is now `m`, as the review asked.

---

## Reach

Every configuration with a nonzero constant x1 gravity (`grav1`) and cp3, cp5 or weno5 x1 reconstruction. The correction also runs with an implicit vertical scheme, since it corrects only the explicit face term. In this repository every example with `grav1` uses weno5 x1 faces, so all of them change (read from the cards at main):
- `bryan`, `earth_crm`, `jupiter_crm`, `jupiter_crm_dry`, `jupiter_evap_precip_1d`, `jupiter_gcm`, `jupiter_gcm_dry` and `uranus`;
- `straka`, `straka_mesh2`, `straka_proc2` and `straka_single`.

Among the tests, `tests/test_tracer_dry_convention.yaml` (weno5, `grav1`) reaches it. Examples without gravity (`shock`, the shallow-water family) are unaffected. Of the 31 cards in this repository that set an x1 scheme, 26 use weno5, 4 plm and 1 cp5; none uses cp3, weno3 or ppm. Cards that set none default to dc.

---

## CI and review

Upstream CI on the head `fbd934b` (on main `644c903`): run 36319431215 green.

**Provenance.** The head `fbd934b` sits on main `644c903`, two commits: `a4d3f44` rebased after #227 merged (range-diff all '='). `a4d3f44` was `ce309c4` plus one test-and-comment commit added in review ("tests: the curvature correction is checked on cp5 and weno5 (nghost 3)"). `ce309c4` is `693dc89` rebased without change after #223 merged, with message-only edits (the test's round-off and mutation sizes now the measured values below, and the 2/3 claim qualified to g = 0): the trees are identical. `693dc89` is the revision made in answer to the review of `e239dba`.

**The upstream owner's reviewing agent.**
- On `e239dba` (10:04 post), the previous revision: "REVIEW … @ e239dba: changes — code is correct and conservative, but the commit message's 'only at higher order' claim is wrong (clean-cell face excess 2.93e-4 vs 2.0e-4 removed); justify or allow-list the weno3/ppm scope; add a cuda arm to the test." What changed in response, per commit `30a062c`:
  - the message now states the 2/3 and 0.88 fractions and why ρ'v' remains;
  - the guard is an allow-list (cp3, cp5, weno5) from the convergence study above;
  - the test gained a `_cuda` twin and a weno3 arm that expects no correction;
  - `phi` is renamed `m`;
  - its other concerns (limiter and sedimentation estimate, periodic-x1 seam, stretched grids) are in Known limits.
  The earlier message's production-run claims are removed, since reviewers cannot reproduce that setup.
- On `693dc89` (11:25 post): approve (quoted in the measurements section above).

Where its numbers and ours differ, both are given here without reconciling them:
- **Round-off and mutation sizes in the test.** Its measurements, 1.4-2.2e-12 round-off and 3.87e-4 (inner) / 5.07e-4 (outer) for an unzeroed wall, replace the estimates the previous commit message gave ("~1e-11", "~3e-4").
- **Clean-cell excess on the test's column.** Settled (review note above): its 2.93e-4 was a single cell, ours the 48-cell mean, which it reproduces.

**Merge matrix.** Measured by the upstream owner's reviewing agent on the pre-rebase heads (base `97b3be4`), with this PR at its first revision `e239dba` ("face"), the two limiter fixes ("carry" and "marks", now combined in one limiter PR). The numbers are as posted; only its branch labels are replaced. 10:04 post (CUDA builds, RTX 5090), "all clean, CUDA builds OK":

| merged | result |
|---|---|
| carry + marks | carry 3/3, forcing 35/35, limiter 6/6, meshnan pass cpu+cuda |
| carry + face | carry 3/3, forcing 30/30, curvature pass |
| marks + face | forcing 36/36, limiter 6/6, meshnan pass, curvature pass |
| all three | carry 3/3, forcing 36/36, meshnan pass, curvature pass |

"hydro_forward hunks don't overlap or interact." Its 10:28 post confirmed that the three-way check posted earlier passes. Its 11:25 post re-ran the merge with the limiter-marks PR on this revision: all 4 combinations clean, and the carry, test_forcing, limiter, check_redo_floor (with meshnan, cpu and cuda:0) and curvature tests pass.

**Sign-offs.**
- The independent review agent: SIGN-OFF approve at `fbd934b` (range-diff re-sign)
- The upstream owner's reviewing agent: SIGN-OFF approve at `fbd934b` (range-diff re-sign; CUDA gate)
- A second independent review agent: offline; post-hoc review when back




## PR #226: hydro, eos, mesh: the positivity limiter withholds carried energy and momentum, and every limiter call marks a repaired step

Merged 2026-09-28; merge commit `2249b4a`.

## Merge summary

This PR combines two fixes to the conserved-variable limiter that were prepared and reviewed as separate branches; they are combined here because upstream squash-merges. Each keeps its own test commit and fix commit, applied in order on main `bf66ec3`; a review follow-up to Part 1 adds a third test and fix pair, and one to Part 2 adds a fourth (species-only repairs, `521622c`/`473aad8`).

- **Part 1, hydro: the positivity limiter withholds the energy and momentum of the mass it withholds.** When the limiter cuts a vapour or cloud face flux, the energy and momentum that mass carried were still delivered to the receiver cell; now they are withheld with it.
- **Part 1 follow-up, hydro: a withheld mixed face flux carries each part's energy and momentum at its own donor.** In an updraft that outruns settling, the net cloud flux is upward while its settling part leaves the cell above, so one donor per face gave the withheld settling mass the wrong cell's energy and momentum. `hydro_forward` now passes the settling part of the x1 species flux to the carry, which withholds the advected and settling parts each at its own donor. Without sedimentation (x2, x3) the arithmetic is unchanged. Fix by the upstream maintainer (`cd05295`); test `23a7474`.
- **Part 2, eos, mesh: every limiter call marks a repaired step, and a NaN is its own redo cause.** A floor applied at stage entry or before the saturation adjustment, or a NaN zeroed in a momentum, species or primitive row, now triggers a redo instead of being silently accepted.
- **Head:** `2b83dfe`, 17 commits on main `bf66ec3` (tree `c2e3cf7`). The first 9 are `10b219b`'s commits, unchanged (same shas); the first 8 of those are unchanged from `6a3e321`, which was rebased without conflict from `0fa3257` (on `bda4b6c`); the 9th adds a test only (Seam test, below). The 4 after `10b219b` clang-format the seam test (`396ee7e`) and make a species-only limiter repair (a negative vapour refilled from its column, a cloud borrowing from its parent vapour, a species clamped in W->U) mark the step for a redo: test `521622c` plants such repairs and expects a redo with the limiter cause, fix `473aad8` makes both limiters set the limiter mark when they change an interior species row, and `bdd9071` also runs the three cases on the device in `limiter_marks_on_cuda`. The 2 after `bdd9071` make remote exchanges work on Gloo: test `662b972` runs the cubed-seam case on Gloo and compares it with UCX, and fix `3cf2f6c` sends each exchanged variable as its own message (Gloo fix, below). The 2 after `3cf2f6c` bound the message tags (test `9ca66e5`, fix `2b83dfe`, 3 files +20/-1; Gloo fix, below). Against `0fa3257`, 7 of the 8 commits are unchanged; the follow-up fix differs only in its author line, corrected from a machine label to the upstream maintainer (same email). The four Part 1 and Part 2 commits have the same patch-ids as the two reviewed branches (`47211b9`, `b463eff`).
- **Review.** A fresh review asked for a carry test that can see a wrong donor; `50e63e7` adds a non-uniform column with both flux signs (details under Part 1 Tests). A later review found the mixed-flux case: its test `23a7474` fails with 20 failures (energy and momentum at every limited interior face) before `cd05295` and passes after it. `6a3e321` is clang-format only. `10b219b` adds a cubed-seam test from an independent review agent.
- **Tests touched:** `test_flux_positivity_carry` (new, 7 cases including 2 CUDA twins), `test_forcing`, `test_check_redo_floor.py`. Full `ctest -j 1` on `6a3e321` (the first 8 commits of this head) and on main `bf66ec3`, same rig (x86-64 Linux, torch 2.6.0, kintera v2.5.0):
  - CPU build: main 71 run, 8 failed; head 72 run, 8 failed; the same 8 on both (`test_exchange`, `test_exchange_ucx`, `test_output_barrier`, `test_check_redo_parallel`, `test_straka`, `test_shallow_xy`, `test_shallow_splash`, `test_restart_cycle_limit`: multi-process and example tests that fail on that machine on main too). `test_flux_positivity_carry` 5/5 CPU cases pass (its 2 CUDA twins skip on a CPU build); the `test_forcing` limiter cases and `test_check_redo_floor.py` pass.
  - V100 CUDA build (sm_70): main 70 run, 7 failed; head 71 run, 7 failed; the same 7 (the list above without `test_exchange_ucx`). `test_flux_positivity_carry` 7/7 on `cuda:0`, both CUDA twins included; `test_forcing` passes, including `limiter_marks_on_cuda`; no gtest skipped.
- **Seam test (`10b219b`).** `test_sedimentation_cubed_seam` (`tests/test_sedimentation_cubed_seam.cpp` +148, `tests/CMakeLists.txt` +1), contributed by the independent review agent, exercises a mixed sedimentation flux at a cubed seam: 2 ranks, layout `cubed`, `nb1=2`. On an x86-64 CPU build, both ranks launched by hand: at `10b219b` the seam fluxes are identical on both ranks, with 6 limiter hits, and condensate mass is conserved. At `23a7474` (before the mixed-donor fix `cd05295`) it fails: the mixed carry is wrong, with the energy off by 9898.6. With seam averaging disabled it also fails: the seam fluxes mismatch, and condensate mass drifts from 0.33600 to 0.33825. Full `ctest -j 1` on `10b219b` gives the same failures as main, plus this test under torchrun with EADDRINUSE, a port clash on that machine that also fails main's 7 other torchrun tests; launched by hand it passes. CUDA: not run on `10b219b`.
- **CI:** pending on `2b83dfe`.
- **Limit: `moist-mixture` is not carried; tracked in #236.** The carry needs a per-species enthalpy, and only `ideal-moist` provides one (`IdealMoistImpl::species_enthalpy`). On `moist-mixture`, the default EOS type, positivity-limited species fluxes are still scaled without their energy and momentum, exactly as on main `bf66ec3`: this PR narrows that pre-existing gap and introduces nothing there. Red test: commit `f12c7c6`; the open question of how to define the per-species enthalpy on the real-gas path is in #236.
- **Limit.** Tags: a local block index >= 32 already overlapped phyid + 1 before this PR whenever phyid varies; harmless in-tree (phyid is always 0), and bounding the block index would break runs with 32 or more local blocks. Not changed here.
- **Suggested squash message:** `hydro, eos, mesh: the positivity limiter withholds the energy and momentum of the mass it withholds; every limiter call marks a repaired step, and a NaN is its own redo cause`
  `layout: exchange_remote sends each exchanged variable as its own message, so a multi-variable exchange works on Gloo (ProcessGroupGloo::send takes one tensor).`

### Gloo fix (test `662b972`, fix `3cf2f6c`; tag bounds: test `9ca66e5`, fix `2b83dfe`)

**Problem.** A Gloo send takes one tensor, but `exchange_remote` handed it every variable of an exchange at once, so a remote exchange of two variables (the limiter's theta and species enthalpy) aborted under Gloo. Both layouts (`src/layout/layout.cpp`, `src/layout/cubed_sphere_layout.cpp`) now send and receive one tensor per variable; variable n adds n * 65536 to the tag, so a single-variable exchange keeps its tag. Size: 5 files, +108/-20 (the fix 3 source files, +28/-20; the test 2 files, +80).

**Tag bounds.** Each exchanged variable n adds n * 65536 to its message tag, so make_comm_tag now rejects a tag outside [0, 65536) (in practice 0 <= SyncOptions::phyid < 64, now documented) and exchange_each_var rejects more than 32768 variables; every tag in use today is unchanged. Test: CommTag.rejects_tags_that_collide_with_the_variable_offset, red at 9ca66e5 (phyid 64 and -1 do not throw), green at 2b83dfe.

**Test, red to green.** `test_sedimentation_cubed_seam_gloo` (`tests/run_seam_backends.py`, one `tests/CMakeLists.txt` entry) runs the 2-rank cubed-seam case (limiter, ideal-moist, vapour and cloud) with `BACKEND=gloo`. Both ranks must exit 0, and where snapy is built with UCX, the Gloo result line (17 digits) must equal the UCX run's. On `bdd9071` it fails: Gloo exits with rc 134 on both ranks, with "ProcessGroupGloo::send takes a single tensor". On `3cf2f6c` it passes: Gloo rc 0/0, UCX rc 0/0, and the two result lines are identical:

```
seam_flux_momentum1=99901.819728861505
seam_flux_energy=493359.10824948602
mixed_carry_correct=1
```

**The UCX path is unchanged.** On the seam test, the UCX result line of `3cf2f6c` equals that of `bdd9071` bit for bit. The 2-process cubed-sphere moist deck (3 panels per process, 40 cycles) gives bit-identical energies and species under Gloo and under UCX on `3cf2f6c`, and these equal `bdd9071` under UCX.

**Messages and time.** Per remote peer, an exchange of k variables now makes k single-tensor send/recv pairs instead of one pair carrying k tensors; k = 2 for the limiter's theta and hspec exchange, and single-variable exchanges keep their message count and tag. On UCX the number of messages on the wire does not change, because commux already posts one tagged message per tensor. UCX time per cycle, 2 processes x 3 panels, rank 0, three interleaved before/after pairs:

```
limiter on:  before 0.0643 0.0771 0.0657 s   after 0.0645 0.0673 0.0618 s   (medians 0.0657 vs 0.0645)
limiter off: before 0.0507 0.0432 0.0463 s   after 0.0441 0.0469 0.0423 s
```

No change beyond run-to-run noise.

**The exchanged hspec is read, but no test can tell it from a local recompute.** `flux_positivity_carry_` reads the ghost's hspec at a block-boundary face whose donor is the ghost cell, so the exchanged value is used across the seam. It carries the same bits as `species_enthalpy()` of that ghost's own w, though: with `hydro_hspec` left out of the exchange, the 2-rank seam test and the six-panel moist deck (1x6 and 2x3 processes x panels, 139 limiter hits at seams) are bit-identical to `3cf2f6c`. So no test can fail on that control.

---

The two parts below are the original PR descriptions, unchanged except for heading levels and their Provenance lines; the Part 1 follow-up is described only in this summary, and their test counts and commit ids refer to the pre-rebase revisions.

---

## Part 1: the positivity limiter withholds carried energy and momentum

### Merge summary

**hydro: the positivity limiter now withholds the energy and momentum of the species mass it withholds.** Numbers change wherever the limiter cuts a vapour or cloud flux.

- **Problem.** When a face would drain a species below zero, the limiter scales that species flux by the donor's theta but leaves the energy and momentum fluxes alone. The withheld mass still carries its energy and momentum from donor to receiver. Totals are conserved, but the two cells are mis-partitioned.
- **Fix.** Before the theta scaling, each face subtracts dm·h from the energy flux and dm·v from the momentum fluxes, where dm = (1 − θ)·F is the withheld species mass flux and h and v are the donor's energy per unit species mass and momentum per unit mass. h comes from a new virtual `EquationOfState::species_enthalpy` (ideal-moist only). It travels with θ in the raw exchange, so both sides of a seam use the same value.
- **Tests, red to green.** The new `tests/test_flux_positivity_carry` has 3 cases: lmars and hllc along x1, lmars along x2, and cloud settling. It fails 3/3 on the base, where the energy and momentum face-flux differences are 0 but about −2.47e4 is expected, and passes 3/3 with the fix, on CPU and CUDA builds.
- **Effect.** On a moist, limiter-on variant of the repository's `tests/test_flux_positivity.yaml` deck, run for 20 cycles: max |ΔT| 0.792 K. The dry and limiter-off arms are bit-identical, on CPU and V100. The upstream owner's reviewing agent measured max |ΔT| 0.0039 K on `examples/jupiter_evap_precip_1d`.
- **Review.** Our independent review corrected the test's hand prediction and asked for an x2 case and a CUDA run; both are in. The upstream owner's reviewing agent approved the same tree, with non-blocking notes (Known limits).
- **Size.** 9 files, +312/−0: the fix is 6 source files (+85), the test 3 files (+227).
- **Limits.** h and v are donor-cell values, not face values. The hllc pressure work is split approximately. Cubed-sphere panel seams use the ghost's interpolated momentum. The moist-mixture EOS keeps the old behaviour.
- **Suggested squash message:** `hydro: the positivity limiter withholds the energy and momentum of the mass it withholds`

---

### 1. The defect and the change

**Defect.** `src/hydro/hydro_forward.cpp` builds the donor θ of each species (`src/hydro/flux_positivity.cpp`), raw-exchanges it and calls `flux_positivity_scale_`, which multiplies only the species rows of the face fluxes. The IDN row is the dry mass flux, so withholding species mass lowers the total mass flux. The momentum and energy rows still carry that mass, so the receiver gains energy and momentum without the mass that carries them.

**Change.** Before the θ scaling, each face subtracts:
- `dm * h` from the energy flux, and `dm * v` from each momentum flux, where `dm = (1 - θ) * F` is the withheld species mass flux (the unscaled species flux times the withheld fraction);
- `v` is the donor cell's momentum per unit mass;
- `h` is the donor cell's energy per unit species mass, split the way the flux itself splits it: `u0 + cv T + KE`, plus `R T` for a vapour (a cloud has no pressure share).

For the ideal-moist EOS this is the exact per-constituent split of the lmars enthalpy flux and of the settling flux. `h` comes from a new virtual `EquationOfState::species_enthalpy`, implemented for ideal-moist and undefined by default. It is raw-exchanged together with θ, so a seam face sees the donor's own value on both sides and the correction telescopes exactly. Gravity work is rebuilt later from the limited mass flux, so `h` carries no geopotential.

Files: `src/eos/equation_of_state.hpp` (+5), `src/eos/ideal_moist.{cpp,hpp}` (+23), `src/hydro/flux_positivity.{cpp,hpp}` (+48), `src/hydro/hydro_forward.cpp` (+9); the test commit adds `tests/test_flux_positivity_carry.{cpp,yaml}` and one `tests/CMakeLists.txt` line.

**Bit-identity by construction.** A dry block (no species), a limiter-off block, and the ideal-gas and moist-mixture EOS (which keep the default, empty `species_enthalpy`) skip the new path entirely. Where θ = 1 everywhere, dm is zero.

---

### 2. Tests

The new gtest works on a six-cell ideal-moist column (vapour y = 0.01, cloud y = 0.02, ρ = 1, p = 1e5, so T ≈ 353 K, reflecting walls). Each case builds a limiter-off block and a limiter-on block from the same state, runs one hydro forward in each, and compares their face fluxes. The oracle does not depend on the fix: it takes the per-mass energy from the EOS's `W->E`, `R_v` from the species weight, and the donor from the sign of the unlimited flux. The energy and momentum fluxes must differ by exactly the withheld species mass flux times h and times v at the donor (rel 1e-12). The dry flux must be unchanged, some face must be limited, and the column totals of the tendency must be equal in the two arms.

| case | base + test | with the fix |
|---|---|---|
| `withheld_advected_mass_keeps_its_energy_and_momentum` (x1, lmars and hllc) | FAIL: energy, x- and y-momentum on interior faces 3-7, both solvers | PASS |
| `withheld_mass_keeps_its_energy_and_momentum_along_x2` (x2, lmars) | FAIL: energy, x2- and x3-momentum on faces 3-7 | PASS |
| `withheld_settling_mass_keeps_its_energy_and_momentum` (cloud settling) | FAIL: energy and y-momentum on faces 3-7 | PASS |

At the base the energy and momentum fluxes are identical in the two arms (difference 0). The expected energy difference is −24736.35 per face, and a hand calculation from the card gives −24736.39; the gap is atomic-mass rounding. The z-momentum, dry-flux, "some face limited" and column-totals asserts pass at the base as well: they guard the fix and do not discriminate, since the base is also exactly conservative.

**Non-uniform donor test, added in review (`8a40ae5`).** A fresh review asked for a carry test that can see a wrong donor, since a uniform column gives the same answer regardless of which cell is treated as the donor. The new case builds a six-cell column where density, temperature, species energy and all three velocities vary cell to cell; two faces are limited with an upward species flux (donors `c0`, `c1`) and two with a downward one (donors `c4`, `c5`), and the expected energy and momentum are computed from the donor cell. Swapping the donor index fails the case at all four limited faces. Swapping only the energy and velocity (using the right donor's theta) also fails the case, while the three uniform-state cases still pass — so the new case is the one that would catch a donor mix-up the others cannot. A `_cuda` twin runs the same case (V100: 5/5 green; the donor swap fails both). Limits: x1 with lmars only; the x2 and hllc paths are still checked only on uniform states, and there is no sedimentation case.

**Environment.** kintera v2.5.0 (the PyPI release upstream CI installs) and torch 2.6.0, with local compatibility shims that are not in the PR. The gtest builds its blocks on the host, so in the CUDA build it gives the same verdicts (base 3/3 FAIL, fix 3/3 PASS); the on-device check is the A/B in section 3.

**Full `ctest -j 1`**, on CPU and on a V100 CUDA build: the only outcome that changes is `test_flux_positivity_carry` (fails on base + test, passes with the fix). The other failures on our test machine are the same on main and with this branch. On CPU they are `test_exchange`, `test_output_barrier`, `test_check_redo_parallel`, `test_exchange_ucx`, `test_straka`, `test_shallow_xy`, `test_shallow_splash` and `test_restart_cycle_limit`. The CUDA build (UCX off) has the same seven without `test_exchange_ucx`. All are multi-process tests that fail on a port clash on that machine. The existing flux-positivity tests (slab, cubed sphere, cubed-sphere moist), `test_cycle_diagnostics`, `test_sedimentation_guards`, `test_condensate_conservation` and `test_forcing` pass with the fix.

**`test_eos`.** The fix adds a virtual to the EOS, so `test_eos` matters, but `tests/test_eos.cpp` does not compile against that machine's glibc 2.17 headers, on main or here. It declares a function named `major`, which `<sys/sysmacros.h>` defines as a macro. With a local, uncommitted `#undef major/minor` shim on both arms, `test_eos` gives the same result per case on base and fix: 11 passed and 6 CUDA parameters skipped on CPU, and 17/17 on the V100 build, where the 6 CUDA parameters ran on the device.

---

### 3. Measurements

**Independent build (Xeon CPU; V100, nvcc 12.2, torch 2.6.0; kintera v2.5.0).** The deck is the repository's own `tests/test_flux_positivity.yaml`: a 2-D slab, periodic in x2, a uniform 20 m/s wind over a sharp vapour top-hat, cp5 reconstruction, lmars. It ran for 20 cycles, base library against fix library, in three arms, driven by a script that is not part of this PR:

| arm | CPU | V100 (`cuda:0`) |
|---|---|---|
| dry, limiter on (no species) | bit-identical | bit-identical |
| moist, limiter off | bit-identical | bit-identical |
| moist, limiter on | differs: 676 limited cells in both arms; max \|ΔT\| 0.792 K, max \|Δ energy\| 489 J/m³, max \|Δ x2-momentum\| 3.1e-2 | differs: 676 limited cells in both arms; max \|ΔT\| 0.792 K |

With the fix, CUDA against CPU on the moist, limiter-on arm: max |ΔT| 3.4e-13 K and max |Δ energy| 1.5e-10 J/m³. That is round-off, and it shows that the new `species_enthalpy` and carry path runs on the device. As a consistency check, 489 J/m³ divided by ρ·cv ≈ 720 J/m³/K gives about 0.68 K, the same size as ΔT.

This deck is the limiter's stress case. The unlimited cp5 polynomial undershoots at the edge of the top-hat and sends a spurious backward vapour flux out of empty cells, which θ = 0 withholds in full. So 0.792 K is an upper-end number, not a typical one. We did not measure run time.

**Upstream owner's reviewing agent** (CUDA build, Quadro RTX 4000; run device and length not stated): "On jupiter_evap_precip_1d I get max|dT| 0.0039 K and about 7% more wall time." He could not rerun the 0.792 K deck, because its moist variant and driver are not in the repository.

---

### Known limits

From the commit message:
- h and v are the donor cell's values, not the face state's, so `dm * (h_face - h_cell)` remains.
- For hllc, the pressure-work part of the energy flux is not mass-borne. The vapour's `R T` there is its partial-pressure share, an approximation.
- At a cubed-sphere panel seam, the momentum per unit mass is the ghost's own value, which is interpolated and in the local basis.
- Like the θ scaling, the correction also edits the faces of transverse ghost rows. The tendency never reads them; it takes interior cells only.
- A sedimentation velocity given to a vapour would get an `R T` that its settling flux does not carry. No card settles a vapour.
- The carry is tested only for negative settling (`vsed < 0`). With `vsed > 0` the sedimentation flux at a face is built from the cell above while the flux drains the cell below, so the carried energy and momentum come from the wrong cell; this is pre-existing on main (no sedimentation-source changes here). No card or test in the repository uses `vsed > 0`; left to a separate issue.
- The moist-mixture EOS defines no per-species split and keeps the previous behaviour. Measured on `examples/uranus.yaml` (moist-mixture, limiter on, the only shipped moist-mixture card with the limiter): run reduced (50×40, 5000 cycles, CPU) on main and on this PR, it is bit-identical at all 20 dumps with 0 redos; the limiter withheld species flux on every step, and the carry it does not apply would have moved about 4e-10 of the face energy flux (at most ~1.6e-5 K per step).
- The test covers x1 and x2 faces of a cartesian block: no seam and no x3 face.

From review:
- Upstream owner's reviewing agent (non-blocking): "Donor velocity isn't raw-exchanged at seams (hydro_forward.cpp:367)", and "The test's momentum check reuses the implementation's formula." Our reading, from our independent review: at a non-panel seam the momentum ghosts are raw copies, so the momentum part is exact there. At a panel seam the ghosts are interpolated, as the commit states, and the two sides' momenta are in different bases, so no exact pairing exists.

---

### Reach

Every configuration with `limiter: true` and at least one vapour or cloud species under the ideal-moist EOS, on steps where θ < 1 at some face. In this repository that is `examples/bryan.yaml`, `earth_crm.yaml`, `jupiter_crm.yaml`, `jupiter_evap_precip_1d.yaml` and `jupiter_gcm.yaml` (read from the cards at main). `jupiter_crm_dry.yaml` and `jupiter_gcm_dry.yaml` have no species and skip the new path. `examples/uranus.yaml` uses the moist-mixture EOS and keeps the previous behaviour. In a downstream collection, 19 of 52 limiter-on cards (plus 4 templates) carry a vapour or cloud species. That count was taken on an earlier revision of the collection.

---

### CI and review

Upstream CI: pending on `2b83dfe`.

**Provenance.** In this combined PR these are commits `354b8b7` (test) and `0d209f1` (fix), cherry-picked without change from `47211b9` (identical patch-ids), which sits on main `bda4b6c`. `47211b9` is `1d5b493` (test commit `a015df6`) rebased without change after #223 merged: the trees are identical. The reviews below were done on `1d5b493`.

**Upstream owner's reviewing agent**, verdict on `1d5b493` (CUDA build on `cuda:0`, Quadro RTX 4000): "REVIEW … @ 1d5b493: approve." His measurements, quoted: "The carry test fails 3/3 at a015df6: flux deltas are 0 where −24736 is expected. It passes 3/3 at head, and a cuda:0 twin shows the same red → green. Serial ctest is 66 pass/2 fail/1 skip at head vs 65/3/1 at base+test. The two failures show up at every sha and come from the hardware or environment: test_eos runs out of memory on the 8 GB card, and test_exchange_ucx_cuda can't bind port 29500. Python ctests are 18/18 at both. The carry math is right: signs, both directions and all three dimensions, and the energy split is consistent with the species-energy, lmars and settling fluxes. pre-commit is clean."

Where his numbers and ours differ, both are given here without reconciling them:
- **`test_eos`.** His: runs out of memory on an 8 GB card, at every sha. Ours: does not compile against glibc 2.17 without a local shim; with the shim, 17/17 on a V100, the same on base and fix.

**Merge matrix.** Measured by the upstream owner's reviewing agent on the pre-rebase heads (base `97b3be4`), with this PR ("carry"), the limiter-marks PR ("marks") and the face-gravity-work PR ("face"). The numbers are as posted; only his branch labels are replaced. 10:04 post (CUDA builds, RTX 5090), "all clean, CUDA builds OK":

| merged | result |
|---|---|
| carry + marks | carry 3/3, forcing 35/35, limiter 6/6, meshnan pass cpu+cuda |
| carry + face | carry 3/3, forcing 30/30, curvature pass |
| marks + face | forcing 36/36, limiter 6/6, meshnan pass, curvature pass |
| all three | carry 3/3, forcing 36/36, meshnan pass, curvature pass |

"hydro_forward hunks don't overlap or interact." 10:28 post (Quadro RTX 4000): carry, marks and the EOS-key commit of the combined hygiene PR "merge cleanly pairwise"; with carry + marks merged, "the carry test passes 3/3 on CPU and cuda and test_forcing is 35/35". 11:18 re-check of the marks PR's current fix (platform not stated): it "re-merges cleanly" with carry, "and on that build test_forcing is 35/35 and all four check_redo_floor arms pass". The face PR's current revision has not yet been re-run in the matrix.

**Sign-offs at `2b83dfe`.**
- The upstream owner's reviewing agent: PENDING
- The independent review agent: PENDING

---

## Part 2: every limiter call marks a repaired step; a NaN is a redo cause

### Merge summary

**eos, mesh: every limiter call marks a repaired step, and a NaN is its own redo cause.** Runs the limiter never repairs are bit-identical.

- **Problem.** A step is redone when the conserved limiter changes an interior density or energy, but that test runs only around the call after the RK average. A floor the same limiter applies at stage entry or before the saturation adjustment goes unseen. A NaN zeroed in a momentum or species row, or by the primitive limiter, marks nothing. Such a step is accepted with the NaN silently replaced by zero.
- **How found.** By reading every call site of the limiter against the redo test that #223 added. That commit's own Known limits name these gaps as outside its scope.
- **Fix.** The mark moves into the EOS, so every limiter call sets it. It is two device bools set with `logical_or_`, with no host sync in the limiter; `check_redo` reads both in one device-to-host copy (`limiter_hits()`). A NaN is a new cause (value 8), named `nan` in the redo log line.
- **Tests, red to green.** Four new `test_forcing` cases fail on the base with `check_redo` returning 0: a NaN in a velocity row, a NaN in a vapour row, a floor patch at stage entry, and a NaN that only the primitive limiter sees. So do their CUDA twin (8 assertions) and the new `meshnan` arm of `test_check_redo_floor.py`. All pass with the fix, and a clean-step control passes on both.
- **Effect.** A dry, limiter-on 2-D shear slab, run 201 cycles, is bit-identical to the base in float64. Eight limiter-on downstream cards were bit-identical on the previous revision, with 0 redo lines in either arm.
- **Review.** Our independent review corrected one Known-limits sentence (a defect inherited between steps costs one redo, not `max_redo`) and asked for guards on the primitive limiter and the Mesh path; both were added. The upstream owner's reviewing agent approved. His nits 1 (a single host read) and 3 (document the side channel) are folded in; nits 2 and 4 stay open (Known limits).
- **Cost** (upstream owner's reviewing agent): host syncs per step are the same as the base. Kernel launches are +7% (dry) and +3% (moist), and step time is ×1.04-1.10 on small grids.
- **Size.** 7 files, +198/−39: the fix is 5 source files (+72/−33), the tests 2 files (+126/−6).
- **Limits.** Only interior cells are tested. A repair inside the step that survives halving dt redoes to `max_redo` and ends the run. A defect left between steps costs one redo, and the log names a cause the step did not produce.
- **Suggested squash message:** `eos, mesh: every limiter call marks a repaired step, and a NaN is its own redo cause`

---

### 1. The defect and the change

**Defect.** The conserved limiter (`apply_conserved_limiter_`) zeroes NaNs in every row and then applies the density and temperature floors. The primitive limiter zeroes NaNs the same way. #223 redoes a step when interior density or energy changes, but it compares them only across the call after the RK average, in `MeshBlock::advance_local`. Two gaps remain:
- The same limiter also runs when a stage converts conserved to primitive variables, and again before the saturation adjustment. A floor it applies there is invisible to the redo decision.
- A NaN the limiter zeroes in a momentum or species row leaves density and energy unchanged, so the step is never marked. Such a step is accepted with the NaN silently replaced by zero.

**Change.**
- `apply_conserved_limiter_` marks an interior NaN in any row, tested before it is zeroed. It also marks an interior density or energy changed by its floors (density only when the EOS has no energy row). `apply_primitive_limiter_` marks an interior NaN; a primitive at a floor is still `floor_hit`'s cause.
- The marks are a two-element bool tensor on the state's device ([0] a floor patched an interior density or energy, [1] an interior NaN), set with `logical_or_` and no host sync. `EquationOfState::reset_limiter_marks` zeroes them. A 3-line comment on `limiter_marks()` in `src/eos/equation_of_state.hpp` documents the side channel.
- The MeshBlock resets the marks at stage 0. Both redo paths (MeshBlock and Mesh) read them after `floor_hit`, and `apply_redo` resets them again after a redo decision, so a `check_redo` on the restored state does not see the previous step's marks. `floor_hit`'s fresh conversion runs the limiter on a copy of the end state: a repair there means this step ended below a floor, and this step is the one a redo can still cure.
- `MeshBlock::limiter_hits()` returns `{patched, nan}` from one device-to-host copy. `MeshBlock::check_redo` evaluates `floor_hit` in its own statement first, and `Mesh::check_redo` calls `limiter_hits()` once per block. `limiter_patch_hit()` stays and forwards to it. The MeshBlock's own compare around the post-average call is removed.
- A NaN is a new cause, value 8, reduced with MAX over ranks like the others. The log line names it: "... the VIC dry-gas clamp emptied a cell, or the limiter patched one or found a NaN. Redoing the step with smaller dt (causes: nan)."

Files: `src/eos/equation_of_state.{cpp,hpp}`, `src/mesh/mesh.cpp`, `src/mesh/meshblock.{cpp,hpp}`; tests in `tests/test_forcing.cpp` and `tests/test_check_redo_floor.py`.

**This revision includes the review nits.** The version first reviewed read the two marks with two `.item()` calls, one extra host sync per step. It now reads them in one copy, and the side-channel comment is added. The test commit is unchanged. The fix diff between the two revisions is 4 files, +21/−14.

---

### 2. Tests

**Environment.** kintera v2.5.0 (the PyPI release upstream CI installs) and torch 2.6.0, with local compatibility shims that are not in the PR. Each gtest ran in its own process. The base arm is the test commit alone on the base.

| test | base + tests | with the fix |
|---|---|---|
| `limiter_nan_in_a_velocity_row_redoes_the_step` (planted before stage 0; the retry after the redo must be accepted) | FAIL (`check_redo` 0) | PASS |
| `limiter_nan_in_a_vapor_row_redoes_the_step` (seen only at stage-1 entry) | FAIL (0) | PASS |
| `limiter_patch_at_stage_entry_redoes_the_step` (temperature-floor patch at stage-1 entry) | FAIL (0) | PASS |
| `limiter_nan_in_a_primitive_redoes_the_step` (seen only by the primitive limiter) | FAIL (0) | PASS |
| `limiter_clean_step_is_not_redone` (dry and moist; negative control) | PASS | PASS |
| `limiter_marks_on_cuda` (the same cases on the device; V100) | FAIL: 8 assertions, the redo and cause asserts of the four planted cases; the clean pair passes | PASS (ran, not skipped) |
| `limiter_patch_is_reported_below_the_temperature_floor` (existing) | PASS | PASS |
| `test_check_redo_floor.py`, new `meshnan` arm (NaN velocity in one block of a six-block Mesh) | FAIL "not rejected (err=0)"; the block, nan and mesh arms pass | PASS, all four arms |

The whole `test_forcing` binary on CPU: base 29 passed, 2 skipped (CUDA cases), 4 failed (the four red tests); fix 33 passed, 2 skipped. On the V100 build with this revision: 35/35. Each NaN case asserts `(causes: nan)` and the stage-entry case `(causes: limiter)`, so the floor bit is not what fires. The `mesh` arm of `test_check_redo_floor.py` fails if the reset after a redo decision is dropped.

**Full `ctest -j 1`.** This was run on the previous revision, whose source differs from this head only by the single-read change and the comment.
- **V100 build (UCX off), with the final tests.** The base fails `test_forcing` and `test_check_redo_floor_python` plus seven multi-process tests: `test_exchange`, `test_output_barrier`, `test_check_redo_parallel`, `test_straka`, `test_shallow_xy`, `test_shallow_splash` and `test_restart_cycle_limit`. The fix fails only those seven.
- **CPU build**, run before the primitive, CUDA and `meshnan` cases were added. The only outcome that changes is `test_forcing`. The other failures are the same on main and with the fix: those seven plus `test_exchange_ucx`. All eight are multi-process tests that fail on a port clash on that machine.
- **`test_eos`** does not compile against that machine's glibc 2.17 headers, on main or here, unless a local `#undef major/minor` shim is applied. With the shim, base and fix give identical per-test outcomes.

Launched by hand with 2 ranks on their own port, `test_check_redo_parallel`, `test_output_barrier` and `test_exchange` pass on both ranks, base and fix. That run checks the cross-rank reduction of the new cause.

---

### 3. Measurements

**Independent build (Xeon CPU; V100, nvcc 12.2, torch 2.6.0; kintera v2.5.0).**

- **Bit-identity, this revision.** A dry, limiter-on 2-D shear slab from a downstream example set (ideal gas, implicit scheme 9, 1 process, 78×32 cells) ran 201 cycles, with the full float64 state dumped. Three pairs were compared: this head against the base, this head against the previous revision, and the previous revision against the base. In every pair:
  - `hydro_u`, `hydro_w` and the two solid-fill tensors (5×1×38×84 each) differ in 0 cells;
  - 0 netCDF variables differ, and 201/201 cycle lines are equal;
  - there are 0 redo lines in all three runs.
  The comparison is not vacuous: 12768 of the 15960 `hydro_u` entries changed from t = 0.
- **Downstream cards, previous revision.** Eight limiter-on cards were run base against fix:
  - the dry shear slab above;
  - two ideal-moist slabs at 2 ranks, one of them at rest with implicit scheme 9;
  - two moist slabs with clouds at 20 ranks;
  - a moist bubble on the Mesh API at 4 ranks;
  - a cubed sphere at 24 ranks;
  - a 6-panel cubed sphere in one process.
  All eight are bit-identical, with 0 redo lines in either arm. Two of the moist cards reproduce themselves at t = 0 only with `MALLOC_PERTURB_` set, because of a pre-existing non-determinism in their initial condition that differs even base against base. With it set, they are bit-identical base against fix, final restart included.
- **GPU cost, previous revision** (one more host sync per step than this head). The downstream shear slab ran on a V100, 100 steps, 3 repetitions. The fix costs +0.68 ms/step (+6%) at 78×32. At 156×64, 312×128 and 624×256 it costs +0.24, +0.57 and +0.42 ms/step (≤1.5%, at or below the per-repetition scatter). The difference does not grow with the cell count, so the cost is kernel launches, not bandwidth.

**Upstream owner's reviewing agent**, on this revision `78b5d6d` (11:18 post; platform not stated), quoted: "The extra sync is gone: host syncs per step are 5 dry / 38 moist, the same as base (1907e87 had 6 / 39). The Mesh path does 18 syncs per check_redo over 6 blocks, same as base. Kernel launches are still +7% dry / +3% moist, which is nit 4." And: "On limiter-on dry and moist bubbles, 200 steps x5 on CPU and CUDA, there were 0 redos, and the final float64 state is bit-identical to both base and 1907e87. Step time is x1.04-1.10." On the first revision (10:28 post, Quadro RTX 4000) he also reported "+4–14% step time on small grids (noisy)".

---

### Known limits

From the commit message:
- Only interior cells are tested, as before. A NaN or floor confined to ghost cells is still repaired without a mark. Ghosts are rewritten by the exchange and the boundary condition, and a redo cannot cure a value it did not produce.
- The condensate/parent-vapour borrow and `fix_vapor` remain non-causes, since they are exactly conservative. **Correction:** of the repairs that do not mark a redo, the parent-vapour borrow and the vapour column fix are exactly conservative, but the zero-clamp of a cloud species with no nucleation parent is not: it creates the mass it clamps (a probe with −1e-4 kg/m³ in one cell of an 8-cell moist column created 97.7 of the 100 kg deficit). This clamp and the primitive floors are unchanged from main; the clamp is left to a separate issue. A primitive at a floor remains `floor_hit`'s cause.
- A repair inside the step that survives halving dt redoes to `max_redo` and ends the run, as #223 documented.
- A NaN or floor that the caller leaves in the state between steps (runner-side forcing, a restart state) is caught by the next step's stage-0 limiter. That step is redone once, since the restore repairs the state, and the log names the cause although the step did not produce it.
- The limiter marks are set as a side effect of every limited conversion on the block, so any W->U or U->W conversion made while the limiter is on (a user stage forcing, a conversion whose result is discarded, or the radiating-boundary flush) marks the step for a redo if it repairs a cell; with the limiter on, prefer conversions that do not go through the limited equation of state for scratch work, and note that no shipped card combines the limiter with outflow.
- A floor or NaN state carried in from between steps now costs exactly one redo (the restore repairs it and the marks are reset, so the retry is clean), and a NaN source that recurs every step now exhausts max_redo and stops the run visibly, where before it was repaired silently.

Open review nits from the upstream owner's reviewing agent (non-blocking):
- "The moist tests fail under `--gtest_filter='forcing.limiter_*'` because the species table is global." The first card loaded sets kintera's process-global species table, so the clean test loads the moist card first. The tests pass in the full binary and one per process.
- The limiter tests share kintera's process-global species table, so `./test_forcing.release --gtest_filter='*limiter*'` loads a dry card first and two moist tests fail with 'Species vapor not found in species list' (on a CPU build of this head: 4 pass, 1 skipped CUDA test, 2 fail; on a CUDA-host build the reviewer saw 4 pass, 3 fail, the third presumably limiter_marks_on_cuda, inferred), while the full suite and each test alone pass; main shows the same order dependence, and kintera's per-card species tables (kintera #121) remove the cause once snapy builds against a release that contains them.
- "The dens/energy snapshot is copied on every limiter call." This is where the extra kernel launches come from.
- "The new comment on the marks is accurate, though it could say that scratch conversions in user forcings also mark the step."

Pre-existing, unchanged: the NaN test uses `isnan`, which does not catch ±inf.

---

### Reach

Every configuration with `limiter: true`. With the limiter off, both limiter functions return before the new code. With it on, behaviour changes only on a step in which some limiter call finds an interior NaN, or floors an interior density or energy outside the post-average call; that step is now redone. In this repository the limiter-on examples are `bryan`, `earth_crm`, `jupiter_crm`, `jupiter_crm_dry`, `jupiter_evap_precip_1d`, `jupiter_gcm`, `jupiter_gcm_dry` and `uranus` (read from the cards at main). None of the runs above, ours or the reviewer's, marked a single step.

---

### CI and review

Upstream CI: pending on `2b83dfe`.

**Provenance.** In this combined PR these are commits `8fe7004` (test) and `cd1d0d1` (fix), cherry-picked without change from `b463eff` (identical patch-ids) on top of Part 1; the PR head is now `2b83dfe`, with further commits added in review (Merge summary). `b463eff` sits on main `bda4b6c`. `b463eff` is `78b5d6d` (test commit `740e461`) rebased without change after #223 merged, with one message-only edit (a squashed commit's hash replaced by "#223"): the trees are identical. `78b5d6d` is the first reviewed fix `1907e87` plus nits 1 and 3.

**Upstream owner's reviewing agent.**
- On `1907e87` (10:28 post, CUDA build, Quadro RTX 4000): "REVIEW … @ 1907e87: approve, non-blocking nits." Quoted: "At base with the new tests, 4 CPU limiter tests fail (check_redo returns 0), the CUDA twin fails 8 assertions, and meshnan fails on CPU and CUDA. At head all 7 limiter tests and all 4 check_redo_floor arms pass on both devices. Dropping the post-redo reset turns the mesh and meshnan arms red, so that claim holds. ctest is 66/68 at base and at head, and 67/69 with [the carry PR] merged, with the same two environment failures each time. test_forcing goes from 29 to 35 tests." (Bracketed text replaces his branch label; the carry PR is the other limiter PR, which withholds carried energy and momentum.)
- On `78b5d6d` (11:18 post, platform not stated): "REVIEW … @ 78b5d6d: approve. Nits 1 and 3 are fixed as claimed; nits 2 and 4 are still open, non-blocking." Quoted: "On cuda:0 (GPU 1), test_forcing is 35/35 and the CUDA twin actually ran (479 ms); with the GPU hidden it's 33 passed, 2 skipped. All four check_redo_floor arms pass on CPU and CUDA. Dropping the post-redo reset turns mesh and meshnan red again, and base with the new tests is still red." And: "Full ctest is 66/68, with only the known 8 GB OOM and the 2-GPU test failing." And: "pre-commit passes with clang-format 20.1.4."

Where his numbers and ours differ, both are given here without reconciling them:
- **Step-time cost.** His: step time ×1.04-1.10 on dry and moist bubbles, this revision, CPU and CUDA (earlier "+4–14% step time on small grids (noisy)" on the first revision). Ours: +6% at 78×32, falling to ≤1.5% at 156×64 and above, on a V100, on the first revision.
- **Full ctest.** His: 66/68 at this revision, the two failures being an out-of-memory `test_eos` on an 8 GB card and a 2-GPU test. Ours, on the previous revision: the eight multi-process tests listed in section 2 fail on both arms, and `test_eos` compiles only with a local shim.
- **CUDA twin run time.** His: 479 ms. Ours: 992 ms on a V100, on the previous revision.

**Merge matrix.** Measured by the upstream owner's reviewing agent on the pre-rebase heads (base `97b3be4`), with this PR ("marks"), the other limiter PR ("carry") and the face-gravity-work PR ("face"). The numbers are as posted; only his branch labels are replaced. 10:04 post (CUDA builds, RTX 5090), "all clean, CUDA builds OK":

| merged | result |
|---|---|
| carry + marks | carry 3/3, forcing 35/35, limiter 6/6, meshnan pass cpu+cuda |
| carry + face | carry 3/3, forcing 30/30, curvature pass |
| marks + face | forcing 36/36, limiter 6/6, meshnan pass, curvature pass |
| all three | carry 3/3, forcing 36/36, meshnan pass, curvature pass |

"hydro_forward hunks don't overlap or interact." 10:28 post (Quadro RTX 4000): carry, marks and the EOS-key commit of the combined hygiene PR "merge cleanly pairwise". 11:18 re-check of this PR's current fix (platform not stated): it "re-merges cleanly with" carry, "and on that build test_forcing is 35/35 and all four check_redo_floor arms pass". The face PR's current revision has not yet been re-run in the matrix.

**Sign-offs at `2b83dfe`.**
- The upstream owner's reviewing agent: PENDING
- The independent review agent: PENDING
