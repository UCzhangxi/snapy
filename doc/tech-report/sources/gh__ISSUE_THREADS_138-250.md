> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# snapy upstream issue threads #138-#250
Fetched 2026-10-09 from the public chengcli/snapy repository (GitHub REST API). Issue body, then each comment in order.

## Issue #138: Test restart of multiple ways of decomposition

State: closed; opened 2026-03-15; closed 2026-03-16.

The latest version supports running multiple MeshBlocks using one process (Mesh). Write test code to make sure that the restart file mechanism works with multiple MeshBlocks. Use straka, shallow_xy and shallow_splash as the baseline cases. Fix code if it doesn't work.

## Issue #208: No test for decomposed moist reflecting-wall + saturation (serial grav1 does not catch #206)

State: closed; opened 2026-09-23; closed 2026-10-02.

## Coverage gap

A decomposed moist reacting run with a physical reflecting wall — physical wall ghost **and** inter-block ghost in the same step with saturation on — has no test. #206 fixed the serial wall-ghost ordering; nothing checks the parallel path.

Related: #206.

## Negative result (do not repeat this attempt)

A serial `const-gravity: grav1: -9.8` variant of `test_wall_saturation` **does not discriminate** the #206 bug. Protocol: current API (`914b43bc`) with `apply_boundaries` moved *before* saturation vs after. Not a checkout of `0daab2a` (`0daab2a` predates the boundary-API change). AWS p5.48xlarge, H100 GPU 0, 0 skips.

| Device / case | Energy before | Energy after | Water before | Water after |
| --- | --- | --- | --- | --- |
| CPU / condensation | 8.49e-7 | 8.49e-7 | 1.15e-14 | 1.15e-14 |
| CPU / evaporation | 2.01e-7 | 2.01e-7 | 9.9e-15 | 8.9e-15 |
| CUDA / condensation | 8.49e-7 | 8.49e-7 | 1.20e-14 | 1.15e-14 |
| CUDA / evaporation | 2.01e-7 | 2.01e-7 | 9.1e-15 | 9.4e-15 |

Water is already at the roundoff floor with the **old** ordering. The no-grav #206 column was ~7e-6 / 1.2e-5 → 1e-14; adding gravity does not recreate that leak.

Closed as #207 (not merged). Branch `test/wall-saturation-grav1` can be deleted.

## Energy residual

~8e-7 in `hydro_u[IPR]` with gravity on, **present in both trees**. I believe this is hydrostatic / moist PE bookkeeping (`hydro_u[IPR]` is not a closed energy when `const-gravity` does work), not a wall-ghost leak. Water mass is conserved at ~1e-14 either way.

If this is a real conservation gap under gravity, it should be its own investigation; I am not treating it as a #206 regression.

## Layout blocker

`SlabLayoutImpl` requires `pz == 1`. YAML `distribute.nb1` maps to `pz` (`layout.cpp`). An x1 decomposition of this 32-cell column is **not expressible**. An eventual parallel test has to split a legal axis (x2/x3) or the layout constraint has to change.

## Path to a real regression

1. Figure out which decomposition is legal for this column.
2. Get the 2-rank run not to crash (see companion SIGSEGV issue).
3. Then check whether it fails on the old ordering. If it does, that becomes the PR. If it does not, the parallel path is already consistent and this issue can close.


### Comment 1 (2026-10-02)

No current test covers a decomposed moist reflecting wall with saturation. test_wall_saturation is one block. The only 2-rank attempt is #209, a CPU Gloo SIGSEGV, and the maintainer deprecated Gloo on 2026-09-28, so that crash is not a path we will fix. Closing this with #209.

What is still absent, on the backend that replaced Gloo, is a 2-rank UCX run: moist EOS, reflecting x1 walls, saturation on, split on a legal axis (x2, because a slab layout requires pz == 1).

## Issue #209: SIGSEGV: 2-rank slab nb2=2 moist reflecting-wall column (CPU, gloo)

State: closed; opened 2026-09-23; closed 2026-10-02.

## What

A 2-rank moist reacting reflecting-wall column, split in **x2** (because x1/`nb1` is illegal — slab `pz` must be 1), SIGSEGV'd after Gloo connected.

Tried while writing a follow-up to #206. Not in tree; reconstructed from the attempt.

## Config

- 2 ranks, CPU (`CUDA_VISIBLE_DEVICES` empty)
- `torchrun --no-python --nproc-per-node=2`
- `distribute.layout: slab`, `nb1: 1`, `nb2: 2`, `nb3: 1`, `blocks_per_process: 1`
- `geometry.cells: {nx1: 32, nx2: 2, nx3: 1, nghost: 3}` (nx2 divisible by nb2)
- `boundary-condition.external: {x1-inner: reflecting, x1-outer: reflecting}`
- moist EOS + nucleation (`H2O <=> H2O(l)`) + `forcing.const-gravity.grav1: -9.8`
- Driver: `Mesh(MeshOptionsImpl::from_yaml(...))`, `gtest_main`, one `TEST`

## Failure

- Rank 1: **SIGSEGV** (exit -11), ~150 ms after start
- Rank 0: SIGTERM from torchrun after peer death
- Gloo had already connected both ranks (`Rank 0/1 is connected to 1 peer ranks`)
- No C++ exception message on the crashing rank; rank 0 sometimes saw gloo `Read error ... Connection reset by peer`

Host: AWS p5.48xlarge, Linux, torch from pyenv, gloo backend (UCX off in that build).

No usable native backtrace captured (torchrun swallowed rank 1). Repro is: 2-rank slab `nb2: 2` + moist + reflecting x1 walls + gravity, CPU.

## Why separate

This is a crash, not a coverage gap. Triage independently of whether a parallel moist-wall regression exists.


### Comment 1 (2026-09-28)

Same comment. Deprecating Gloo.

### Comment 2 (2026-10-02)

Closing. The maintainer on 2026-09-28, on this issue: "Same comment. Deprecating Gloo." The crash is a 2-rank CPU Gloo run. The same day's decision on #239 is that Gloo is Mac-only and Linux CI does not run it, so there is no further Linux Gloo repro.

## Issue #224: tests/: ten test sources are never built or run, and the FULL_TESTS set is not in CI

State: closed; opened 2026-09-26; closed 2026-09-27.

**Counts at main (bda4b6c).** Configured as CI does (`-DCUDA=OFF -DNETCDF=ON -DBUILD_TESTS=ON`, configure only), `tests/CMakeLists.txt` registers 67 ctests, or 72 with `-DFULL_TESTS=ON`:

| | files in tests/ | registered | only under FULL_TESTS | never registered |
|---|---|---|---|---|
| C++/CUDA sources (`test_*.cpp`, `test_*.cu`) | 47 | 39 | 1 | 7 |
| Python tests (`test_*.py`) | 24 | 21 | 0 | 3 |

- **C++/CUDA row.** The 39 sources make 40 ctests: `test_exchange` runs twice, once with gloo and once with ucx.
- **Python row.** The 21 are 18 that run directly and 3 that `run_*.cmake` scripts use as checkers for the straka, shallow_xy and shallow_splash example runs.
- **The other ctests.** 6 of the 67 are restart harnesses (`run_restart_*.py`). The 5 FULL_TESTS entries are `test_mesh_multi_block` and 4 `run_*_decomp.py` harnesses.
- **How this was counted.** Registered names came from `ctest --show-only=json-v1`, keeping the tests whose backtrace is in snapy's own CMake files, and were matched against `ls tests/test_*.{cpp,cu,py}`. A plain `ctest -N` at the build root reports 1005 tests, because 938 of them are Eigen's own tests, which FetchContent pulls in.
- **Every configuration.** None of the ten unregistered files is mentioned on any active line of `tests/CMakeLists.txt`, so this holds for every configuration, CUDA included.

**The ten files:**
- **Registration commented out** (lines 79-81), in three files:
  - `test_read_topo.cpp` needs a topography `.pt` file that is not in the repo, and makes no assertions.
  - `test_aneos.cpp` matches the current `ANEOSThermo` API. But the only constructor in the tree is a weak stub that throws, and `example.aneos` is not in the repo.
  - `test_thomas_solver.cu` includes `snap/implicit/tridiag_thomas_impl.h`, which no longer exists.
- **Code that is no longer in the tree**, in four files:
  - `test_transform.cpp` and `test_cs_velocity_rotation.cpp` include headers that are no longer in the tree.
  - `test_implicit.cpp` includes `globals.h` and `fvm/...`, and uses `namespace canoe`.
  - `test_hydro.cpp` uses `namespace canoe` and `flux_divergence`, neither of which exists now. It is also MPS-only.
- **Python**, in three files:
  - `test_crater.py` runs `from canoe import *` on a local 256³ HDF5 dump and is hard-coded to `cuda:0`.
  - `test_robert.py` compares two netCDF files whose paths come from argv.
  - `test_exchange.py` needs 4 ranks and makes no assertions.

Separately, `ci.yml` does not set `FULL_TESTS`, so the five FULL_TESTS entries never run in CI. They exercise real multi-process exchange.

Why it matters: an unregistered test cannot fail, so it rots silently while it looks like coverage. Five of the ten would no longer compile, and each of the other five needs something the repo does not provide: a data file, an implementation, a launcher or arguments.


## Issue #228: sedimentation: a rising particle (vsed > 0) takes its flux from the cell above the face, not the cell it leaves

State: closed; opened 2026-09-27; closed 2026-09-27.

**Symptom.** At main (bda4b6c), a species with a positive sedimentation velocity has its settling flux at x1 face i computed from cell i, the cell above the face. A rising particle leaves cell i-1, so the face carries the wrong cell's mass, energy and momentum. For vsed < 0 (settling), cell i is the upwind cell, and the flux is right.

**Reproduction.** One test commit on bda4b6c adds `sedimentation.rising_cloud_is_taken_from_the_cell_below` (plus a `_cuda` twin) to `tests/test_sedimentation_guards.cpp`, using that file's card (`tests/test_gravity_sedimentation.yaml`) with `const-vsed: {cloud: +2}` and grav1 = -1e-12. The column is resting, and the cloud mass fraction is 0.01, 0.02, ..., 0.06 from bottom to top. After one `Hydro::forward`, every interior face must carry rho*y*vsed, and that mass's `W->E` energy, of cell i-1, and both walls must carry exactly 0.

```
./test_sedimentation_guards.release --gtest_filter='sedimentation.*'
```

**Red on main** (CPU, float64): 10 failures, mass and energy at each of the 5 interior faces. Both wall checks and the two existing cases pass. For example:
```
face 3: the cell above gives 0.040000000000000001   (expected 0.02 = 2 * 1 * 0.01, cell below)
face 7: the cell above gives 0.12
face 7 (energy): the cell above gives -155927.99324460514
[  FAILED  ] sedimentation.rising_cloud_is_taken_from_the_cell_below
```

**Mechanism (hypothesis, from reading the code).** `hydro_forward.cpp:166` calls `psed->forward(w, _flux1)` with cell-centred `w`. Both paths then write face i from cell i. The tensor path (`sed_hydro.cpp:37`) computes `rhos = wr[IDN] * wr.index_select(...)` on that `w`. The ideal-moist kernel (`sed_hydro_impl.h:81-87`) reads `w[hydro_id * ncells + flat]` and adds into `flux[hydro_id * ncells + flat]`. There is no branch on the sign of vsed. The walls are sealed by zeroing vsed at cells `<= il` and `> iu` (`sed_hydro.cpp:29,32`; `sed_hydro_impl.h:41`). A donor chosen by sign therefore also needs its own seal at the bottom face, which the test checks.

**Reach.** Every shipped card sets `const-vsed < 0`. vsed > 0 arises from a positive `const-vsed`, from a positive grav1, or from Stokes settling of particles lighter than the gas. The positivity limiter's carry picks its donor from the sign of the face flux (f > 0 means cell i-1). For vsed > 0 it therefore already assumes the donor this test requires.


## Issue #229: eos: the conserved limiter zero-clamps a cloud with no nucleation parent, creating the mass it clamps

State: closed; opened 2026-09-27; closed 2026-09-27.

**Symptom.** At main (bda4b6c), `apply_conserved_limiter_` repairs a negative condensate by borrowing the deficit from its nucleation parent vapour in the same cell, which is exactly conservative. A cloud species that no nucleation reaction produces has no parent. The precipitation that `coagulation` makes is one example, as in `examples/earth_crm.yaml`, `jupiter_crm.yaml` and `jupiter_evap_precip_1d.yaml`. Such a species is clamped to zero instead, and the clamp adds the deficit to the total mass. The comment above that loop already names the effect: zeroing a negative condensate "invented mass one-way".

**Reproduction.** One test commit on bda4b6c adds `tests/test_parentless_cloud.{cpp,yaml}`. The card has `vapor <=> cloud` (nucleation), `cloud => rain` (coagulation) and `rain => vapor` (evaporation) on an 8-cell column, the reaction structure of the CRM cards. Rain holds 0.001 everywhere except -1e-4 in one interior cell. `apply_conserved_limiter_` must leave the column's total mass unchanged, rain non-negative and dry air untouched. The test checks the column total rather than each cell, so a same-cell borrow and a column redistribution both pass.

```
./test_parentless_cloud.release
```

**Red on main.** The cpu_Double and cpu_Float arms fail only the mass check. The CUDA arms were not run (no GPU):
```
the repair created 0.99999999999766942 of the deficit     (cpu_Double)
the repair created 0.99999997473787516 of the deficit     (cpu_Float)
[  FAILED  ] DeviceAndDtype/DeviceTest.parentless_cloud_repair_keeps_the_column_mass/cpu_Double
[  FAILED  ] DeviceAndDtype/DeviceTest.parentless_cloud_repair_keeps_the_column_mass/cpu_Float
```

**Mechanism (hypothesis, from reading the code).** `cache_cloud_parents_` (`equation_of_state.cpp:93-133`) fills a cloud's parent list only from `nucleation` reactions, and returns early when there are none (`:100`). In the limiter, a cloud with an empty list takes `c.clamp_min_(0.)` (`:213-217`) with no matching debit, so the whole deficit is created. Coagulated precipitation is also the species these cards sediment, which is the flux most likely to over-drain a cell. Whether a negative precipitation value actually occurs in the shipped CRM runs has not been measured.


## Issue #232: Parentless-cloud repair creates mass at x1 meshblock boundaries (nb1 > 1)

State: closed; opened 2026-09-27; closed 2026-09-29.


## Symptom

The columnar repair of a negative parentless cloud (a condensate with no nucleation parent, e.g. rain made by coagulation) in `apply_conserved_limiter_` only sees the cells of its own meshblock. With the domain split along x1 (`distribute.nb1 > 1`), a block whose local column total of that cloud is not positive falls back to `clamp_min_(0.)` and invents mass equal to the deficit, although the same global column has enough of that cloud in the neighbouring block and is repaired conservatively with `nb1 = 1`. The result depends on the decomposition. This matches PR #230 case 1 (two meshblocks along x1): -1e-4 local change in the lower block, +1.0e-4 total mass change, identical on CPU and CUDA, float32 and float64. Pre-existing on `main`; not introduced by #226 or #231.

## Where (main @ bf66ec3)

`src/eos/equation_of_state.cpp:226` takes the block-local interior view, and `:267-278` runs `call_fix_vapor` over it for the cloud slots inside the per-block advance (`src/mesh/meshblock.cpp:727-739`, step 4), before the ghost exchange (`src/mesh/mesh.cpp:339-341`), so the scan uses the block's own `nx1`. The kernel (`src/eos/fix_vapor_impl.h:36-44`) sums "above" only to the block's top interior cell, finds `above < deficit` and returns 1. That return code is discarded for the cloud slots (the vapor call at `:291` checks it), and the following `clamp_min_(0.)` creates mass equal to the deficit.

## Reproduction

One 16-cell column, `tests/test_parentless_cloud.yaml` species card with `nx1: 16`, rain = 0.001 in global cells 8..15, 0 in cells 0..7 except cell 3 = -1e-4; call `apply_conserved_limiter_` on every block as `advance_local()` step 4 does; sum dry + vapor + cloud + rain over all interiors before and after (CPU, `CUDA=OFF`):

| Case | Total mass change (float64) | Total mass change (float32) | Where |
|---|---|---|---|
| `nb1 = 1` | 0.0 | -7.3e-12 (round-off) | - |
| `nb1 = 2` | +1.000e-4 | +1.000e-4 | all in the lower block, 0 in the upper |

No test in `tests/` sets `nb1` at all. The slab layout rejects `nb1 > 1` (`src/layout/slab_layout.cpp:12`), so the split needs `layout: cubed`. A failing gtest (`nb1 = 1` passes, `nb1 = 2` fails) is posted as a patch alongside this issue.

## What a fix needs

- Cover the deficit across the full global column (cross-block column reduction along x1) or communicate the residual to the neighbouring block, so the outcome is independent of `nb1`.
- Honour the `call_fix_vapor` return code for the cloud slots instead of clamping; the clamp should only fire when the global column is in net deficit (the exception PR #230 documented).
- Add an `nb1 > 1` variant of `test_parentless_cloud` asserting the same result as `nb1 = 1`.
- Run it on CPU and CUDA, float32 and float64.


### Comment 1 (2026-09-28)

Design note for a fix, from a code reading of main bf66ec3 (nothing built or run yet; costs are estimates). Comments welcome before implementation.

Root cause: the repair for clouds without a parent vapour scans only the block's own part of each column. At the block edge it finds too little rain above, the kernel reports a failure, that failure is ignored, and the clamp that follows creates mass equal to the deficit. That is the +1.000e-4 seen with nb1 = 2, against 0.0 with nb1 = 1. The repair runs in the state-update step and again before saturation adjustment, both before the ghost exchange.

I compared two fixes. (A) Gather each whole x1 column onto one block, run the existing kernel there, and send the pieces back. Each non-root block sends and receives one message per repair call and the root handles 2(pz-1). It works for any nb1 and on the same-process copy path, and should match nb1 = 1 exactly. (B) Pass the leftover deficit to the neighbour block. It can't reuse the ghost buffers because they move a stage late. It would need up to pz-1 rounds one after another and a new kernel, and it still depends on nb1.

I recommend A. Plan: a column gather/scatter helper in the layout code; the parentless repair split into its own function that respects the failure code, so the clamp only fires when the whole column is short; calls from advance_local when nb1 > 1, with no new flag. Test: nb1 = 2 and 3 versions of test_parentless_cloud, checking total mass summed across ranks before and after (1e-14 in float64, 1e-6 in float32) and rain matching nb1 = 1, on CPU and CUDA.


## Issue #233: config: a misspelled key in most YAML blocks is silently ignored and the block falls back to a default

State: closed; opened 2026-09-28; closed 2026-09-28.

**Symptom.** Almost every YAML block snapy parses reads its keys by name with a default (`node["key"].as<T>(default)`) and never looks at the keys it was given. An unknown or misspelled key is therefore ignored without a message, and the setting it was meant to change keeps its default. The run starts normally and differs from the intended configuration.

**Damaging cases** (misspelled key → value actually used, on main `bf66ec3`):
- `forcing/const-gravity/grav1` → `0.` (`src/forcing/const_gravity.cpp:17`): the run has no gravity.
- `integration/cfl` → `0.9` (pyharp's integrator `from_yaml`).
- `boundary-condition/external/x1-inner` (and the other sides) → `"reflecting"` (`src/mesh/meshblock_options.cpp:94`).
- `geometry/cells/nx2` → `1` (`src/coord/coordinate.cpp:121`): a 2-D deck runs 1-D.
- `dynamics/reconstruct/<vertical|horizontal>/type` → `"dc"` (`src/recon/reconstruct.cpp:31`); `dynamics/riemann-solver/type` → `"roe"` (`src/riemann/riemann_solver.cpp:24`).
- `outputs[i]/variables` → empty list; `outputs[i]/dt` → `0.` (`src/output/output_type.cpp:44,80`).

**Blocks that already refuse an unknown key:**
- `dynamics` and `forcing` (top level): `src/hydro/hydro_options.cpp:67` and `:95`.
- `dynamics/equation-of-state` (#227): `src/eos/equation_of_state.cpp:38-65`, with a separate list of the keys kintera reads.
- `sedimentation/const-vsed`: refuses a name that is not a species (`src/sedimentation/sed_options.cpp:71`), as a side effect of the species lookup.

**Blocks that accept an unknown key silently:** `geometry` and its `bounds`/`cells`, `distribute`, `dynamics/reconstruct` and its sub-blocks, `dynamics/riemann-solver`, `integration`, `scalar` and its sub-blocks, `sedimentation`, `boundary-condition` and its `external`/`internal`, every `forcing/<name>` sub-block (const-gravity, coriolis, diffusion, body-heat, top-cool, bot-heat, relax-bot-comp, relax-bot-temp, relax-bot-velo, top-sponge-lyr, bot-sponge-lyr, plume-forcing), `outputs[i]`, and misspelled top-level block names. kintera's `reference-state` and `species[i]` are silent as well (kintera's side). A few misspellings fail later on an unrelated value check (e.g. `width must be greater than zero`), whose message does not name the key.

**How to reproduce.** Take any deck that loads, add one line inside a block, and load it as a run does:
```python
import snapy
op = snapy.MeshBlockOptions.from_yaml("deck.yaml")
snapy.MeshBlock(op)
snapy.MeshOptions.from_yaml("deck.yaml")
```
With `misspeled-key: 1` under `dynamics/equation-of-state`, this raises #227's message. Under `forcing/const-gravity`, or with `grav1` renamed to `garv1`, it loads without a word. One probe per block (an unknown key, plus a misspelling of one real key) covers the list above.

**What a fix needs.** One shared helper that checks a node's keys against the keys its `from_yaml` reads, like #227's check. It should report the full path and the valid keys, and be called at the top of each block's `from_yaml` above. Blocks shared with another library (the EOS with kintera, `integration` with pyharp) need that library's keys listed as well, as #227 does. A test per block, a deck with one unknown key that must raise, keeps the lists in step when keys are added.


## Issue #234: species: after a second card is loaded, sedimentation names and the limiter's cloud-parent split read the new card's table

State: closed; opened 2026-09-28; closed 2026-09-28.

**Symptom.** kintera's species table (`kintera::species_names`, `kintera::species_weights`) is process-global. Since kintera #121 (`6a4aad9`), it is refilled whenever a card with a different species list is loaded. snapy still reads that global table, using the global ids a block got when its own card was parsed. So once a second card is loaded in the same process, a block from the first card can read the second card's names and molar masses. #121's own notes say "snapy reads the global table in one place (the cloud-parent cache) … moves to the per-object copy in a follow-up snapy PR". That follow-up was never made, and there is a second place.

**Where (main `bf66ec3`):**
- `src/eos/equation_of_state.cpp:122-160`, `cache_cloud_parents_()`: `species_names[cids[j]]` (l. 135), the parent lookup in `species_names` (l. 138-142) and `species_weights[species_id]` (l. 147). It is called only from the `EquationOfStateImpl` constructor (l. 119).
- `src/sedimentation/sed_options.cpp:123-130`, `SedVelOptionsImpl::species()`: maps `particle_ids()` back through `species_names` every time it is called, including from `SedHydroImpl::forward` (`src/sedimentation/sed_hydro.cpp:74`).

**Red test.** Commit `e15ab06` (one commit on `bf66ec3`) adds `tests/test_two_cards_species.cpp` and two cards. Card A has dry, H2O, NH3, H2S, H2O(l) (parent H2O) and NH4SH (parents NH3 + H2S), both clouds sedimenting. Card B has the same six species in a different order, so every stale id stays in range but names another species. Each case first checks that loading B refilled the table. Results on main, float32 and float64 alike:
1. Block A built, card B loaded, A's limiter used: **passes**. The parent map was filled in the constructor.
2. Same order, A's sedimentation `species()`: **fails**, `[ NH4SH H2O(l) ] instead of [ H2O(l) NH4SH ]`. Only the names are wrong. `forward` uses only the count, and the hydro slots, radius, density and settling speed were fixed at parse time.
3. A's options parsed, card B loaded, then block A built: **fails**. The limiter repairs a negative cloud from the wrong vapors. Per unit deficit, (H2O, NH3, H2S) pay:
   - H2O(l): `0.333242 0.666758 0` instead of `1 0 0`.
   - NH4SH: `0 0 1` instead of `0 0.333242 0.666758`.

The same cases without card B all pass, run one per process or together. Total mass is conserved in case 3; only the split between vapors is wrong, so a total-mass check does not catch it.

**Not tested.** With a second card that has *fewer* species, the same reads go past the end of the table: `species()` on every `forward` call (order 1), and `cache_cloud_parents_` (order 3). That is undefined behaviour and may crash. The test avoids it on purpose.

**What a fix needs.** Read the block's own copy, not the global table. Since #121, each kintera `SpeciesThermo` keeps `names()` and `mu()`, copied when the object is built, in the order `species()` returns: vapors, then clouds.
- `cache_cloud_parents_` can find a cloud's name and its parents' molar masses there by position.
- `SedVelOptions` can store its particle names (or the thermo it was resolved against) at parse time, instead of resolving ids at call time.

With that, all three cases pass whatever card was loaded last, and the fewer-species read goes away.


## Issue #236: limiter: on the moist-mixture EOS, positivity-limited species fluxes carry no energy or momentum

State: closed; opened 2026-09-28; closed 2026-10-03.

**Symptom.** With `limiter: true`, the tracer positivity limiter (`src/hydro/hydro_forward.cpp` section 4.C, `flux_positivity_scale_`) scales a species face flux down where it would drive the donor cell negative. On the `moist-mixture` EOS, the energy (`IPR`) and momentum (`IVX`-`IVZ`) fluxes at that face are not reduced with it. The withheld species mass stays in the donor cell, but its momentum and enthalpy still leave, so the donor's velocity and energy no longer match its mass. In a uniform flow the donor's velocity drops. Column and box totals of energy and momentum still conserve to round-off, because every face flux stays single-valued: the defect is local.

**Relation to #226.** At main `bf66ec3` no EOS gets this carry (there `hydro_forward.cpp:361` calls only `flux_positivity_scale_`). #226 (head `bdd9071`; the line numbers in this paragraph and below are at that head unless marked) adds `flux_positivity_carry_` (`hydro_forward.cpp:373-376`), which runs only when `species_enthalpy()` is defined (`:355`). The base returns `{}` (`equation_of_state.hpp:126`), and only `IdealMoistImpl` overrides it (`ideal_moist.cpp:260`). So after #226 `ideal-moist` is carried and `moist-mixture` still takes main's path. #226 narrows the gap and introduces nothing; this issue tracks the remainder.

**Reach.** `moist-mixture` is the default EOS type (`equation_of_state.hpp:45`, and the `from_yaml` default at `equation_of_state.cpp:69`). The shipped `examples/uranus.yaml:72-75` sets `type: moist-mixture` with `limiter: true`. The other 7 limiter-on examples use `ideal-moist`.

**Reproduction.** Commit `f12c7c6` (`bdd9071` plus one commit touching only `tests/test_flux_positivity_carry.cpp`) adds `flux_positivity.moist_mixture_withheld_mass_keeps_its_energy_and_momentum`. It runs #226's six carry cases with the card's EOS type set to `moist-mixture`, on CPU. Oracle: at each limited face, the energy and momentum face-flux shortfall must equal dm*h and dm*v of the donor cell, where dm is the withheld species mass.

```
./test_flux_positivity_carry.release --gtest_filter='flux_positivity.*'
```

**Red at `f12c7c6`** (CPU, float64): 90 failures, all of them energy or momentum face-flux checks. The measured shortfall is 0 at every limited face. The 5 `ideal-moist` carry tests pass.

| case | limited faces | max \|expected dE\| | expected dM |
|---|---|---|---|
| advected, lmars | 5 | 24736.3 | x1 0.06, x2 0.09 |
| advected, hllc | 5 | 24736.3 | x1 0.06, x2 0.09 |
| settling | 5 | 27229 | x2 0.06 |
| along x2 | 5 | 24736.3 | 0.06 / 0.09 |
| donors | 4 | 41351.1 | 0.0806 / 0.1287 / 0.0245 |
| mixed | 5 | 42014.9 | 0.176 / 0.209 / 0.0664 |

Control: main `bf66ec3` with the same test file fails all 6 carry tests, `ideal-moist` included, with a shortfall of 0.

**Mechanism (hypothesis, from reading the code).** `MoistMixtureImpl` has no `species_enthalpy()` override, so `hspec` is undefined and the carry is skipped.

**Open question on the fix.** `MoistMixtureImpl` needs a per-species enthalpy: `W->E` per species (`_prim2speciesEng`, `moist_mixture.cpp:174-194`) divided by rho*y, plus a partial-pressure share. That share is R_n*T for an ideal vapour, but not in general on this EOS's kintera real-gas path (`eval_czh`, `moist_mixture.cpp:237`). How should that share be defined there? Once that split is defined, #226's carry harness and the red test above should apply unchanged.


### Comment 1 (2026-09-28)

Decision: kept open as a known limitation, not fixed now. So that it is not forgotten, the hygiene PR (with #233) adds two markers that live in the code: a comment at `flux_positivity_carry_` naming the moist-mixture gap and this issue, and a strict expected-failure test that checks the energy and momentum budget of a positivity-limited species flux on the moist-mixture EOS. The test reports XFAIL today; whoever implements the carry sees it XPASS, and strict mode makes them remove the marker and close this issue in the same PR.


### Comment 2 (2026-09-29)

**Proposed fix for #236: `MoistMixtureImpl::species_enthalpy`, prototyped and measured (study branch, no PR)**

Study branch (not a PR): [`study/236-mm-species-enthalpy`](https://github.com/chengcli/snapy/tree/study/236-mm-species-enthalpy) at `dc4abddac8989fdad3a2683fb0413255b304e83c` (3 commits on `3f7ad96`: `9e5d6ca` test instrumentation only, `fd43d7b` the fix, `dc4abdd` the pin swapped for `expect_carried`). `9e5d6ca` adds a residual printout, a `CARRY_EOS` env override and an opt-in timing probe for this study; a real PR would drop them.

Analysed at snapy `3f7ad96` and kintera `4dc613d` (built against kintera 2.5.13 `a8bef99`; `eval_uhs` is unchanged between the two).

**1. What `species_enthalpy()` must return on moist-mixture**

Per species n ≥ 1 (vapours and clouds, not dry), the donor cell's **specific flux enthalpy in J/kg**:

h_n = u_n(T, c) + z_n(T, c)·R_n·T (vapours only) + ½ v·v_lowered

- u_n is kintera's specific internal energy, *including* the `u0_R` reference/latent offset. It is `eval_intEng_R(T, conc)·R/μ_n`, with uref_R + cref_R·T + the NASA-9 or H2 terms when those are enabled (kintera `src/thermo/eval_uhs.cpp:266-302`).
- z_n R_n T is the vapour's share of the pressure, using kintera's own pressure definition p = R T Σ_gas c_n z_n (`thermo_y.cpp:512-519`, `_temp_to_pres`). Clouds get no share (their czh is 0, `eval_uhs.cpp:226`). This settles the open question in the issue body: on the real-gas path the share is z_n R_n T with the same `eval_czh` that `VT->P` uses. By construction, Σ_n ρ_n h_n (with dry) = U + p + ρ·KE, which matches the energy flux the Riemann solver builds (LMARS: `F_E = ubar·ρ·(U/ρ + KE + p/ρ)`, `src/riemann/lmars_dispatch.cpp:69,90`), because U is `VT->U` = Σ c_n u_n R (kintera `thermo.hpp:229-235`), the same U that `_prim2cons` stores in `cons[IPR]` (`moist_mixture.cpp:118-119`).
- **Kinetic energy is added inside h_n.** It is not a separate term: the carry multiplies h_n by the withheld mass dm and subtracts the product from `flux[IPR]` (`src/hydro/flux_positivity.cpp:117-121`). This is the same convention as `IdealMoistImpl::species_enthalpy` (`ideal_moist.cpp:260-280`, u0 + c·T + KE, with c += R_n for vapours). With czh ≡ 1 and no NASA-9, the new method equals it exactly.
- **Momentum needs no EOS term.** The carry subtracts dm·(ρv)/ρ from the donor (`hydro_forward.cpp:374`, `flux_positivity.cpp:122-124`), i.e. withheld mass times the cell velocity. That matches how the face momentum flux is built (`ubar·ρ·y_n` species flux and `ubar·ρ·v` momentum flux, `lmars_dispatch.cpp:87-88`). Pressure stays in the face pressure and is not carried. Momentum was only missing on moist-mixture because the call is gated on `hspec.defined()` (`hydro_forward.cpp:373`).
- **Where it exists already:** every ingredient is in kintera ≥ 2.5.13 and is already called from `moist_mixture.cpp` (`eval_intEng_R`, used at `:185`; `eval_czh`, used at `:237`). kintera's `eval_enthalpy_R` (`eval_uhs.cpp:462-489`) gives the same gas column (u + czh·T). I did not use it because its cloud branch is `uref + cref·T + czh`: it drops `intEng_R_extra`/NASA-9 and adds czh without the ·T. That makes no difference while those are unset, but it is not VT->U-consistent in general. Prototype: 24 lines in `moist_mixture.cpp` and 1 in `moist_mixture.hpp`. It reuses the cached `ivol` and `temp` (`_ensure_cache`) and returns a tensor of shape `(ny, nc3, nc2, nc1)`, like ideal-moist.
- Found while checking: `_prim2speciesEng` (`W->E`, `moist_mixture.cpp:185`) passes `ivol` (kg/m³) as the `conc` argument of `eval_intEng_R`, whereas `VT->U` passes mol/m³. This is harmless while `intEng_R_extra` is empty (it is only set programmatically in kintera, not from YAML), but W->E and VT->U would disagree otherwise. The new method uses mol/m³.

**2. Does the strict pin pass? No, by design it fails. The positive check passes.**

CPU, float64, `test_flux_positivity_carry`. For the "before" rows I reran #226's six carry cases with the card's EOS forced to moist-mixture through a scratch env override; this is the same experiment as the red test in the issue body. Residual = max over faces of |(F_off − F_on) − dm·h| for energy and |… − dm·v| for momentum:

| case (moist-mixture) | limited faces | max \|expected dE\| | energy residual before → after | momentum residual before → after |
|---|---|---|---|---|
| advected, lmars | 10 | 24736.3 | 2.47e4 (rel 1.0) → 1.09e-11 (rel 4.4e-16) | 0.09 (rel 1.0) → 2.38e-12 |
| advected, hllc | 10 | 24736.3 | 2.47e4 (1.0) → 7.28e-12 (2.9e-16) | 0.09 (1.0) → 2.38e-12 |
| settling | 5 | 27229 | 2.72e4 (1.0) → 0 | 0.06 (1.0) → 0 |
| along x2 | 10 | 24736.3 | 2.47e4 (1.0) → 1.09e-11 (4.4e-16) | 0.09 (1.0) → 2.38e-12 |
| donors | 8 | 41351.1 | 4.14e4 (1.0) → 2.55e-11 (6.2e-16) | 0.129 (1.0) → 4.74e-12 |
| mixed | — | 42014.9 | 4.20e4 (1.0) → 2.91e-11 (6.9e-16) | 0.209 (1.0) → 1.30e-11 |

- Before: 90 failed checks, the same count as the issue. After: 5/5 CPU cases pass under the existing 1e-12 relative tolerance, and the numbers are bit-identical to the ideal-moist arms. Column totals of IPR/IVX/IVY/IVZ still agree to ≤5.8e-11 on a scale of 1.1e6. On CUDA (RTX 4000, sm_75), the `_cuda` twins on moist-mixture pass too: energy rel ≤6.1e-16, 8/8 OK.
- The pin `moist_mixture_withholds_no_energy_or_momentum_yet` **fails** with the fix. That is the strict-XPASS signal: 15 checks at faces 3–7 in rows IVX, IVY, IPR, with the message "#236 is fixed, check it with expect_carried". For example, the energy flux at face 3 goes from 246272.12 to 221535.77, a shortfall of 24736.35 = dm·h. Replacing its body with `expect_carried(off, on)`, as the message says, makes it pass (rel 4.4e-16 / 2.6e-11).
- Other tests: test_eos 11/11, test_radiating_boundary 16/16, test_diffusion_moist 8/8, test_riemann 8/8 on CPU (CUDA variants not built there). None of these has the limiter on with moist-mixture, so they only show that nothing else moved.
- What else it needs: **no tolerance change**. Remove the `#236` comment at `hydro_forward.cpp:372`, and swap the pin for the positive test. **No other EOS path**: ideal-gas, plume and shallow-water have no species rows, so the `ny > 0` branch never runs. After this, both species-carrying EOSs (ideal-moist, moist-mixture) carry. **Condensates**: clouds get u_n + KE with no pressure share, and the settling case covers them. **Boundary fluxes**: unchanged; the carry uses the theta that is ghost-filled with the same bfuncs, and totals conserve as before. **Not covered by the harness**: czh ≠ 1, NASA-9/H2 cp, or `intEng_R_extra`. The oracle in `expect_carried` hard-codes `W->E + R_v·T`, so for those cases it would need a z_n-aware oracle, or an identity test Σρ_n h_n + ρ_d h_d = U + p + ρKE. czh and `intEng_R_extra` are not settable from YAML in kintera 4dc613d.

**3. Reach (limiter: true together with moist-mixture)**

- `examples/uranus.yaml:70-76`: 12 species, H2S nucleation/coagulation/evaporation, sedimentation const-vsed −200 m/s for H2S(l,p) (so the settling part of the carry applies), run with `examples/run_hydro.cpp`. This is the **only** shipped deck. The type is explicit, not from the default.
- Tests: only `test_flux_positivity_carry.cpp`'s pin, via an inline edit.
- Implicit case: `type` defaults to moist-mixture (`equation_of_state.hpp:45`, `equation_of_state.cpp:72`), but `limiter` defaults to false (`:52`, `:89`), so a deck has to write `limiter: true` itself. Such a deck with no `type` would get moist-mixture silently; no shipped deck does this. Scan: all 54 tracked YAML files (53 with an equation-of-state block) plus the inline cards and programmatic `limiter(true)` calls in `tests/`. All other limiter-on decks are ideal-moist (7 examples, 8 test cards) or ideal-gas.
- Side finding, unrelated to #236: `uranus.yaml` aborts on cycle 1 with "Maximum number of redo attempts exceeded" (5 redos, cause "limiter", thetamin 0). It does this identically at `3f7ad96` without the fix and with it (CPU, kintera 2.5.13, `nlim: 20`, outputs removed). So the only affected deck does not run on this setup today, and I could not measure an end-to-end effect. Not checked with kintera 2.5.15.

**4. Recommendation: fix now as its own small PR.**

- Size: about 25 LOC in `src/eos/moist_mixture.{hpp,cpp}`, 1 line removed in `hydro_forward.cpp`, and in the test file about −23/+10 for the pin swap. Optionally about 30 more to run all six carry cases on both EOSs. That is 3–4 files and about 60 LOC.
- Runtime: one limited `Hydro::forward` on a 256×256 slab (3 species, every face limited, CPU, 4 threads, 3 repeats) goes from 42.13 to 46.69 ms (+4.56 ms, +10.8%). `species_enthalpy` alone is 1.13 ms, against 0.58 ms on ideal-moist, whose forward is 20.5 ms. This only applies with the limiter on, and 256² with all faces limited is the worst case.
- Risk: low. The carry code is unchanged and already runs on ideal-moist. What changes is results on limited faces of moist-mixture runs, i.e. `uranus.yaml`, and that is the intended change. The residual risk is the untested czh ≠ 1 / NASA-9 path.
- kintera: no new API and no version bump (`kintera>=2.5.13` already covers `eval_intEng_R` and `eval_czh`). If we want the W->E `ivol`/`conc` mismatch fixed, it can go into the same PR or its own.
- Tests to add or update: swap the pin for `expect_carried`, and parametrize the six carry cases (CPU and `_cuda`) over {ideal-moist, moist-mixture}. Optionally add a U + p identity test with czh ≠ 1 set programmatically.

**Not yet checked**

- Real-gas czh != 1, NASA-9/H2 cp, and `intEng_R_extra` on moist-mixture (the harness oracle hard-codes `W->E + R_v·T`; czh and `intEng_R_extra` are not settable from YAML in kintera `4dc613d`).
- kintera 2.5.15 not tested: built against the installed kintera 2.5.13 (`a8bef99`), whose `eval_uhs` is identical to `4dc613d`.
- Full ctest and the Python limiter tests (`test_flux_positivity*.py`) not run.
- CUDA runs of test_eos, test_radiating_boundary, test_diffusion_moist and test_riemann not done (only `test_flux_positivity_carry` was run on CUDA).
- End-to-end effect on `examples/uranus.yaml` not measured: it aborts at cycle 1 both before and after the fix.


### Comment 3 (2026-09-30)

**Limited-face counts, reconciled.** Measured at main `3f7ad967921eebb8b382bb97969384eef2bbd570` and at the study branch `dc4abddac8989fdad3a2683fb0413255b304e83c`, both CPU, with a print-only local patch (the counts are identical at both shas). Distinct limited faces are **5 / 5 / 5 / 5 / 4 / 5** (advected lmars, advected hllc, settling, along x2, donors, mixed), matching the issue body. Pairs of limited face × species are **10 / 10 / 5 / 10 / 8 / 10**.

The 10/10/5/10/8 in my earlier comment is `expect_carried`'s own `limited` counter. It increments once per species at each face, so vapour + cloud give 2 per face, and only the settling case, where only the cloud settles, gives 1. It is not a different test, and the instrumentation commit does not change it; the earlier table also left out the mixed case's count.


### Comment 4 (2026-09-30)

**Study plan rev 3**, posted here as the plan of record for review. Nothing has been built or run for it yet.

---

#236 plan rev 3, part 1/3: the second critique and the oracles. Drafting only; nothing run.

Critique -> change
1. Step 0 aborted on counts -> Step 0 now records the six moist-mixture limited-face counts on main. It still requires all six moist-mixture cases red and every ideal-moist arm green. A count other than 5/5/5/5/4/5 is recorded and does not abort; the measured counts become the reference for every exact-count check after that.
2. B was per mole, the code works in J/kg -> h [J/kg] = hbar [J/mol] / M_n, with M_n = 1/inv_mu. 842a116 does this at moist_mixture.cpp:207-211, then adds KE at :217. O1 and O2 now give both units. New control: a dropped inv_mu must fail by relative 0.982 for water and 0.971 for dry air (a factor of 55.5 and 34.5), not at 1e-12.
3. W->E bug -> eval_intEng_R(temp, ivol) is passed kg/m3 (moist_mixture.cpp:184-185). It is always its own fix and never folded into A or B.
4. A = B today -> new gate G-AB (part 2).
Cell count settled: 24 moist-mixture gate cells + 12 ideal-moist controls = 36.

Definitions: zeta = z + c z'; vbar_n = zeta_n / sum c zeta; phi_n = c_n(u_n' + R T z_n'), with ' = d/dc_n.
B (gas) = u_n + z_n R T + phi_n - vbar_n * sum c phi.
B (cloud) = u_c.
Both in J/mol; divide by M_n. Assumes p = R T sum c z(T, c_n), zero-volume clouds, fixed T and p, and T=0 with u0_R as the reference.
R = 8.314462618.

O1 (closed form, standalone)
- Model: z = 1 + B c, B = b - a/(RT); u = u0 + cv T - a c.
- Inputs:
  - dry: a 0.137, b 3.87e-5, cv 2.5R, u0 0, M 28.97e-3
  - vapour: a 0.5536, b 3.05e-5, cv 3.5R, u0 -4.4e4 J/mol, M 18.015e-3
  - state: T 353 K, c 1000 / 1000 mol/m3
- Expected:
  - dry 10646.79 J/mol = 367511.0 J/kg
  - vapour -32344.85 J/mol = -1795439.8 J/kg
- Must reject (dry / vapour):
  - A: -18456.7 / +29680.3 J/kg (rel 5.0e-2 / 1.7e-2)
  - C = (U+p)/rho_gas: rel 2.26 / 0.74
  - dropped inv_mu: 0.971 / 0.982

O2 (finite difference; uses only the O1 model's p(T,V,N) and U)
- Fix p* = p(V=1).
- Newton-solve for V at N'; H = U + p*V.
- Central difference in N_n, step 1e-5 N_n, plus one Richardson step; divide by M_n.
- Must match O1 within 1e-6 J/mol + 1e-8 rel (measured 1.1e-10).
- Rejects A, C and dropped inv_mu by the same sizes as O1.

O3 (YAML only, no W->E)
- T = p / (R sum_gas rho y / M)
- h_v = (R/M_v)(u0_R + cv_R T + T) + KE
- h_c = (R/M_c)(u0_R + cv_R T) + KE
- Card: vapour cv_R 3.5, u0 0; cloud 9.0, u0 -3430; dry 2.5. M taken from the code in Step 0 (nominal 28.97e-3 / 18.015e-3).
- Uniform state: T 353.347 K, h_v 7.33861e5 J/kg, h_c -1.15325e5 J/kg.
- The gates evaluate O3 at the code's T.
- Must reject (rel):
  - C on the vapour: 0.51
  - cloud + R_c T: 1.41
  - cloud with cv 3.5: 7.78
  - cloud as a vapour: 7.36
  - dropped inv_mu: 0.982
  - K2's p/rho_c (8.7e-4) is reported, not failed.

Non-circular: any other split is h + delta with sum c delta = 0 and delta != 0. Each oracle pins every h_n separately, and every control must miss by at least 1e3 x its tolerance.

---

#236 plan rev 3, part 2/3: tolerances and gates

Tolerances: |x-y| <= abs + rel*max. Each line is abs / rel.
- T vs code: 1e-9 K / 1e-11
- h_n vs O1 or O3: 1e-9 J/kg / 1e-12
- O2 vs O1: 1e-6 J/mol / 1e-8
- sum identity: 1e-6 J/m3 / 1e-12 (necessary only)
- limited counts vs Step 0, and the dry mass flux: exact
- face energy residual: 1e-9 / 1e-12
- face momentum residual: 1e-12 / 1e-12
- column totals: 1e-12 / 1e-12 of sum|du|
- CPU vs CUDA:
  - h_n: 1e-9 / 1e-14
  - theta: 1e-15 / 1e-13
  - species flux: 1e-15 / 1e-13
  - energy flux: 1e-9 / 1e-13
  - momentum flux: 1e-12 / 1e-13
  - counts: exact
- code M vs composition M: rel 2e-5 (sanity only)
- runtime: median of 5; soft gate B <= A + 15%

G-AB
- Rule: |h_A - h_B| <= 4 eps S_n, eps = 2^-52, S_n = (R/M)(|u0_R| + cv_R T + z T) + KE.
- Why: with func2 empty, czh = 1, czh_ddC = 0 and intEng_extra = 0 exactly (kintera eval_uhs.cpp:225-226, 247, 268-288). So phi = 0 and B = A. Coded as A + 0, the difference is bitwise 0. A reordering of at most 4 correctly rounded ops stays <= 2 ulp of S_n.
- Bound at the card: cloud 2.7e-9 J/kg (rel 2.4e-14 of h), vapour 6.5e-10 (8.9e-16).
- Covers: the 12 MM z=1 cells (6 CPU + 6 CUDA), every cell including ghosts, vapour and cloud.
- The test first asserts that czh, czh_ddC and intEng_R_extra are empty.
- If it fails, B is not the reduction claimed and is stopped.

Gates
- 0 (CPU): build main 3f7ad96. Record the six MM counts, M_n and T. Pass if all six MM cases are red (energy residual rel 1.0 at every limited face) and every ideal-moist arm is green. A count mismatch is recorded, not an abort. 842a116's after-numbers are recorded against the issue's.
- 1 (CPU, no snapy): O1/O2 values reproduced in J/mol and J/kg; O2 vs O1 within tolerance; every control fails by its stated size (+-10%) and by >= 1e3 x tolerance; T 353.347 K.
- 2 (CPU): 18 CPU cells (12 under b) meet every tolerance; every control fails, dropped inv_mu at about 0.97-0.98; G-AB holds on the 6 CPU z=1 cells.
- 3 (CUDA, RTX 4000, fp64): 18 CUDA cells (12 under b) meet the oracle and CPU-vs-CUDA rows; G-AB holds on the 6 CUDA z=1 cells. A skip is a gap and fails the gate.
- 4: full ctest + python limiter tests show no new failures vs main; ideal-moist fluxes bitwise equal to main; column totals hold; runtime recorded.
- Coverage: all 24 MM cells covered (a), or the 12 z=1 cells covered with z!=1 out of scope (b).

---

#236 plan rev 3, part 3/3: grid, branches, decision

Grid, target test_flux_positivity_carry. Columns: IM cpu/cuda | MM z=1 cpu/cuda | MM z!=1 cpu/cuda. E = exists at 842a116 (line), N = new, G = gap, U = uncovered.
- adv lmars: E172/NG | E352/NG | NU/NU
- adv hllc: E172/NG | NG/NG | NU/NU
- settling: E187/NG | NG/NG | NU/NU
- along x2: E200/NG | NG/NG | NU/NU
- donors: E241/E245 | NG/NG | NU/NU
- mixed: E337/E342 | NG/NG | NU/NU
A cell is covered only if it ran on its device and passed. CPU-only or skip = gap. The thread's scratch-override runs do not count.

Branches (a maintainer decision)
- (a) A test-only kintera option registers z_virial, z_virial_ddC and u_virial in the func2 CPU and device tables; all 12 z!=1 cells can then run.
- (b) z!=1 is excluded; those 12 cells stay uncovered. The report must say "no real-gas or z!=1 conclusion; A and B are indistinguishable on every reachable config".

Decision
- Drop any candidate that fails a gate; C and dropped inv_mu must fail.
- (a): the smallest candidate that passes O1, O2, G-AB and all 24 cells. Tie-breakers: CUDA parity, then cost (<= +15%), then LOC.
- (b): A plus a TORCH_CHECK that refuses non-empty czh / czh_ddC / intEng_R_extra on gases. B is not claimed.
- Condensates: K1 (u_c), unless the EOS gains a condensate volume.
- The W->E bug is always its own fix, never folded into the winner.

Rev 2 answers to the first critique, all kept:
- A is a hypothesis.
- The oracles are standalone formulas.
- All cells are listed with GAP/UNCOVERED rules.
- There is an abs + rel tolerance per observable.
- The controls come with expected failure sizes.
- O3 uses only YAML constants.

Open:
- Branch (a) or (b).
- kintera computes M via harp::get_compound_weight (molar_mass.cpp:17-18). harp's table is not in my workspace. IUPAC weights give 28.96998e-3 or 28.96968e-3, both within 1.1e-5 of 28.97e-3. O3 therefore takes M from the code.
- The baseline counts are only a prior.


## Issue #237: ci: multi-process tests never run on the Gloo backend on Linux, so Gloo-only failures show on macOS alone

State: closed; opened 2026-09-28; closed 2026-09-28.

**Symptom.** Linux CI never runs a multi-process test on the Gloo backend, so a Gloo-only failure shows up on macOS CI alone. PR #226 at `bdd9071` is the case in point: `test_sedimentation_cubed_seam` aborts on macOS (both ranks: `c10::Error: ProcessGroupGloo::send takes a single tensor`) and passes on Ubuntu.

**Why Linux misses it.** `default_backend()` is Gloo on Darwin and in any build without UCX. The Linux job installs commux, so its multi-process tests run on UCX, whose `send` accepts a vector of tensors. Gloo's `send` accepts exactly one (`checkSingleTensor`). `LayoutImpl::exchange_remote` passes one tensor per exchanged variable (`send_bufs[bid]` holds `vars.size()` tensors) through `ProcessGroupContext::send`, so any remote exchange of two or more variables aborts under Gloo and only under Gloo.

**Reproduction.** The same 2-rank binary (source = `bdd9071`) with the backend forced: Gloo exits 134 on both ranks with the CI's message; UCX exits 0 on both. The #226 follow-up fixes that exchange; this issue is about the CI gap that let it through three pushes (`396ee7e`, `473aad8`, `bdd9071`), each red on macOS only.

**Proposal.** Run the multi-process tests on the Linux job a second time with the Gloo backend forced, or add a Gloo matrix entry, so both backends are covered on every push.


### Comment 1 (2026-09-28)

Same comment. Gloo may be deprecated. Up for later discussion

### Comment 2 (2026-09-28)

Closing per the maintainer's decision on #239: Gloo is Mac-only and Linux should never use it, so Linux CI does not need Gloo multi-process tests.

## Issue #238: exchange: the ghost hydro_hspec equals species_enthalpy() of the ghost's own state; drop it from the exchange?

State: closed; opened 2026-09-28; closed 2026-09-28.

**Context.** #226 (head `3cf2f6c`) adds the positivity limiter's carry on the `ideal-moist` EOS. In `src/hydro/hydro_forward.cpp` it exchanges `hydro_hspec` together with `hydro_theta`, so that a face on a block seam sees the donor cell's own species enthalpy.

**The ghost hspec is read.** `flux_positivity_carry_` takes `lower()`/`upper()` slices of `hspec`, so at a block-boundary face whose donor is the ghost cell, it reads the ghost's `hspec`.

**But it carries nothing new.** The ghost's `hspec` holds the same bits as `species_enthalpy()` of that ghost's own `w`. Measured: with `hydro_hspec` left out of the exchange (control built on `bdd9071`), the output is bit-identical to the head on
- the 2-rank Cartesian seam test;
- the six-panel cubed-sphere moist deck, run as 1 process x 6 panels and as 2 processes x 3 panels, with 139 limiter hits at seams.

**Cost of keeping it.** One extra message per remote peer per exchange stage: after #226 each exchanged variable is its own message.

**Open question (for the maintainers).** Drop `hydro_hspec` from the exchange and recompute it from the ghost's primitives? Or keep it as insurance for interpolated panel-seam ghosts, where `species_enthalpy()` of an interpolated `w` might not equal the donor's value?

**Not a change in #226.** The maintainer asked for this issue. #226 stays as is.


### Comment 1 (2026-09-28)

Decision (with the maintainer's earlier lean): recompute the ghost's species enthalpy from the ghost's own state instead of exchanging `hydro_hspec`. The measured result says the exchanged value already equals `species_enthalpy()` of the ghost's `w` bit for bit, so outputs should not change; the fix drops one message per peer per stage. It lands after #226 merges, in the same PR as #241 (the EOS-repair PR), with the bit-identical check quoted.


## Issue #240: comm: Gloo point-to-point takes one contiguous tensor per send; snapy's comm layer accepts a list

State: closed; opened 2026-09-28; closed 2026-09-28.

**Symptom.** A Gloo send or recv takes exactly one contiguous tensor (`ProcessGroupGloo::send takes a single tensor`). `ProcessGroupContext::send/recv` (src/layout/process_group.cpp:146-172) accept a vector and pass it straight to Gloo; UCX accepts the vector. So any multi-tensor message works on UCX and aborts on Gloo, and Linux CI runs UCX (#237, #239).

**Where a message can carry more than one tensor (main bf66ec3).** `exchange_remote` (layout.cpp:618, cubed_sphere_layout.cpp:1044) sends one tensor per exchanged variable. Every in-tree caller exchanges one variable per call, or a ':+'/':-' pair of which each face buffer carries one. The x1 relays and seam flux (hydro.cpp, hydro_forward.cpp) and all allreduce/reduce calls pass one fresh tensor. The public `Mesh.exchange` and `Mesh.exchange_ghost_zones` (python/csrc/pymesh.cpp:283, :285) pass the caller's whole map, so K variables become K tensors. No example or snapy module does that; #226's limiter did (theta + species enthalpy).

**Reproduction.** Build a two-process mesh (slab, 2 blocks per process, or the six-panel deck with 3), fill two variables, then call `mesh.exchange(vars, SyncOptions().interpolate(False).type(kScalar))` under torchrun with 2 processes.
- On main: BACKEND=gloo exits 1 on both ranks with the message above; one variable, or BACKEND=ucx, passes with correct ghosts.
- On #226's head (2b83dfe): both backends pass, because `exchange_each_var` sends one message per variable.

**Open design question.** Where should the one-tensor rule live?
(a) The comm layer: `ProcessGroupContext::send/recv` split (or pack) a k-tensor message for Gloo, so every caller is safe, including future direct callers.
(b) The call sites / layout, as #226 does: callers split per variable, and `ProcessGroupContext` rejects k != 1 on Gloo with a clear error instead of Gloo's.
Considerations: (a) keeps UCX's one-call semantics and costs k messages, or one copy to pack. (b) keeps the comm layer thin but relies on every caller. Also open: whether allreduce/reduce should get the same guard (all single-tensor today).

Opened as agreed with the snapy owner on 2026-09-27; for discussion. Not a blocker for #226 or #239.


### Comment 1 (2026-09-28)

Decision: option (b). #226's per-variable exchange closes the only path that reached this, so the comm layer keeps its one-call form and gains a guard: `ProcessGroupContext::send/recv` on Gloo reject a message of k != 1 tensors with a clear error that names the fix (split per variable), instead of Gloo's generic abort. The guard and a two-process Gloo test go into the config/tests hygiene PR with #233; this issue closes with it.


### Comment 2 (2026-09-28)

This is up for discussion. Snapy does not guarantee Gloo. Later on, snapy should rely solely on commux/UCX as the communication layer.

## Issue #241: eos: fix_vapor conserves the column sum of vapor density, not vapor mass

State: closed; opened 2026-09-28; closed 2026-09-28.

fix_vapor conserves the column sum of vapor density, not vapor mass. The columnar repair of negative vapor (src/eos/fix_vapor_impl.h:28-59, called from EquationOfStateImpl::apply_conserved_limiter_, equation_of_state.cpp:281-291, and for parentless clouds at :265-278) accumulates and rewrites rho*q cell by cell with no cell-volume weight. On any grid whose x1 cell volume varies (gnomonic-equiangle and spherical-polar grow with radius; any non-uniform x1), a repair therefore keeps sum(rho q) fixed and changes sum(rho q V). A test on the shipped examples/jupiter_gcm.yaml deck (16 levels, one negative vapor cell covered by the two cells below) gives sum(rho q) unchanged to the bit and sum(rho q V) changed by 1.2e-4 relative. In a 40-cycle run of the shipped deck the repair fired twice, on one or two cells, with a mass change below round-off, so today's effect is small. It grows with the deficit and with the volume contrast, though, and the kernel cannot be right without the volume. Suggested fix: pass the interior cell volumes to fix_vapor and accumulate and redistribute rho*q*V (the parentless-cloud call too); a Cartesian uniform grid is then bit-unchanged.


## Issue #245: Deprecate plume eos and plume forcing

State: open; opened 2026-09-28.

They were temporary works and should be deprecated.

## Issue #246: tests: test_eos moist_mixture/cuda_Double runs out of memory on an 8 GB GPU (its 402x402x102 grid needs about 10.7 GB)

State: closed; opened 2026-09-28; closed 2026-09-29.

`test_eos` `DeviceAndDtype/DeviceTest.moist_mixture/cuda_Double` fails with a CUDA out-of-memory error on a GPU with 8 GB, on main d061d82 and on #243's head 10235df. It is a memory limit of the test's grid, not a defect in the equation of state.

## Failing case
- GPU: Quadro RTX 4000 (sm_75, 7.62 GiB), driver 615.71.09, nvcc 12.9.86, torch 2.10.0+cu128.
- `test_eos` passes 16/17. `moist_mixture/cuda_Double` fails 3 of 3 runs on each commit, and on a second GPU of the same kind. `moist_mixture/cuda_Float` and `moist_mixture/cpu_Double` pass.
- It fails in `torch::allclose(cons, cons2, 1.E-6, 1.E-6)` (tests/test_eos.cpp:143) while allocating 630 MiB. That is one 5-variable float64 field on the test's grid.
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` fails the same way, so it is not fragmentation.

## Why
Every `test_eos` case builds its block from tests/test_eos.yaml: `cells: {nx1: 400, nx2: 400, nx3: 100, nghost: 1}`, i.e. 402 x 402 x 102 = 16.5 million cells; one 5-variable float64 field is 5 x 16.5e6 x 8 B = 629 MiB. The moist-mixture case holds several such fields at once (cons, prim, cons2 and the temporaries of `W->U` and `allclose`).
- With nx3 cut to 50 the case passes 3/3 on the same GPU, with a peak of about 5.36 GB. Memory scales with the cell count, so the full grid needs about 10.7 GB (estimated from that peak, not measured): it fits a 16 or 32 GB GPU and not an 8 GB one.

## Proposed fix
The checks are pointwise (cons -> prim -> cons round trip, gamma, sound speed), so they do not need a large grid.
- A (preferred): a smaller grid in tests/test_eos.yaml, e.g. `nx3: 50` (measured to pass at about 5.4 GB) or smaller still, which also shortens the test on every device.
- B: keep the grid and skip the CUDA case (`GTEST_SKIP`) when the free GPU memory (`cudaMemGetInfo`) is less than the case needs.
Either way the other `test_eos` cases share the card, so a grid change applies to all of them; none of their checks depends on the grid size.


### Comment 1 (2026-09-28)

Credit: the sm_75 measurements in this issue (the failing runs on d061d82 and 10235df, the 630 MiB allocation at test_eos.cpp:143, the expandable_segments check, and the nx3: 50 run at about 5.36 GB) are from an independent review.


## Issue #250: hydro: which well-balanced density reference (rho_ref) should x1 reconstruction use? A study proposal

State: closed; opened 2026-09-29; closed 2026-10-02.

Which density reference should snapy's well-balanced x1 reconstruction use? This issue proposes a study with ground truth independent of the model, so the choice rests on measurements across the atmospheres snapy is meant for, not on one case. Measurements made outside snapy that motivated it are not reproduced here.

## 1. What the density reference does
snapy reconstructs x1 face states in a well-balanced (WB) way. A hydrostatic reference is subtracted, the
perturbation is reconstructed, and the reference is added back at the face. Two references are involved:
- **Pressure reference p_ref.** This is what makes a resting atmosphere stay at rest. It is not in question here.
- **Density reference rho_ref.** It only decides how accurately the face density is reconstructed, since
  rho' = rho - rho_ref is what WENO sees. A good rho_ref makes rho' small and smooth. A bad one makes rho' larger and
  rougher than rho itself.
The choice is about accuracy away from rest, and about robustness.

## 2. The forms that exist today
| form | rho_ref | exact when | where |
|---|---|---|---|
| isentrope | the bottom cell's adiabat, rho ∝ p^(1/gamma) | the whole column is on that dry adiabat | not in snapy main |
| smooth5 | p_ref × (5-point clamped binomial smoothing of rho/p along x1) | T (and mean molecular weight) vary smoothly | snapy main `src/hydro/hydro_ref_x1_impl.h:62-68,184-185` (9378f06) |
| none | 0: reconstruct rho itself | never exact, but rho is a smooth exponential | not in snapy main |
snapy's rho/p divide has no positivity guard; no shipped example has hit it so far.

## 3. What has been measured, and why it does not decide the question

The measurements behind this section were made outside snapy and are not reproduced here. A convergence "truth" that is the same code at higher resolution covers one profile, one boundary type, dry and linear; errors shared by all forms (pressure split, vertical implicit solve, boundary treatment) are invisible to it.

## 4. The study we propose: ground truth that does not come from the model
Goal: choose (or design) the rho_ref with the smallest WORST-CASE error over the atmospheres the code is meant for, plus
robustness. Neptune alone is not enough.

**Regimes: profile families × resolution**
- dry adiabatic (convective)
- isothermal
- stable, constant N²
- inversion (T rising with height)
- sharp tropopause and smooth tropopause
- superadiabatic layer
- moist adiabat with condensation and a mean-molecular-weight gradient: H2O on Jupiter, CH4 on Neptune, and a
  heavy-vapour case where mu increases upward
- both an H2-He and an N2/CO2 background
- dz/H from ~2 to ~50

**Tests, each with an independent truth**
- **T1, static face reconstruction (cheap unit test).** Use analytic profiles, where the exact face density is known.
  Run snapy's own reconstruction path with each rho_ref and report the face error versus dz/H.
- **T2, linear acoustic-gravity normal modes.**
  1. Build an independent eigen solver for the linearised compressible Euler equations on a given T(z), mu(z), g
     (e.g. Chebyshev collocation).
  2. Validate the solver on the analytic isothermal dispersion relation first.
  3. Initialise the model with one eigenmode, run a few periods, and measure the frequency error, the eigenfunction
     error and the convergence order.
  Use a boundary treatment that is identical across forms (rigid lid, and lid + sponge) so that boundary error can be
  separated from reference error.
- **T3, nonlinear cases with published references.**
  - Straka et al. (1993) density current. The background is dry neutral, so isentrope is exact: this is the control.
  - Bryan & Fritsch (2002) moist bubble. The background is saturated neutral, so isentrope is NOT exact: this case
    discriminates.
  - Optionally, wave breaking in an isothermal layer, judged by two independent codes agreeing at high resolution.
- **T4, robustness.**
  - large anomalies (cold pools, strong inversions)
  - rho/p positivity
  - stretched x1 grids
  - block seams: rho_ref must be single-valued across blocks and decompositions
  - bit-reproducibility across rank counts
  - cost

**Decision rule.** For each regime, express each form's error relative to the best form. Pick the form whose largest
ratio is smallest, then check it against T4. A default must not be more than ~2x worse than the best anywhere a real
configuration reaches.

**Candidates worth testing beyond the three**
- **Local polytrope:** rho_ref = rho_i (p/p_i)^(1/n_i), with n_i taken from neighbouring cells. It is exact for adiabatic,
  isothermal and any locally polytropic layer, and so unifies isentrope (global n = gamma) and smooth5.
- **Hydrostatic integration of a smoothed T(z)**, consistent with p_ref by construction.
- **Keeping `none` as an option.**

## 5. Deliverables (snapy side)
1. T1 and T2 as registered tests (ctest/pytest) with tolerances, and T3 as example cases with a comparison script.
2. A results table (regime × form × resolution).
3. A PR that adds the chosen form. smooth5 must stay available and bit-identical. The PR may add `none` and should guard
   the rho/p divide.
4. A statement of which shipped examples change their numbers.


### Comment 1 (2026-09-29)

## T1 — static x1 face density

Code: commit `e1380ba1a208b55d815354dc5940c17e2fb33546`, parent main `9378f0606a309959807385a2fbc9092573880f34`. Not a pull request. The run is CPU, double precision, WENO5, one Cartesian block, reflecting x1 walls.

`dz/H` is the interior cell width. The units are `g = 1`, `Rd = 1`, `T(0) = 1`, `p(0) = 1`, so the reference scale height `H = Rd T(0) / g` is 1. A grid is kept only when `nx1 >= 8`, so a short column cannot reach `dz/H = 2`. The dry adiabat is only 2H tall (temperature would cross zero near 3.5H). The isothermal column is 16H and does include `dz/H = 2`.

Each cell is given the exact hydrostatic mass `(p_left - p_right) / dz` and the average pressure. The number below is the maximum, over every face that bounds an interior cell, of `|rho_face - rho_analytic| / rho_analytic`, using the worse of the left and right reconstructed states.

`smooth5` is the production path: `_hydro_ref_x1`, the wall-ghost fill, WENO with the floor off, and the positivity fallback. Calling it twice on the same column is bitwise identical. The other three forms change only `dref` and `dsf`.

- **isentrope** — bottom interior cell's adiabat, `rho_b (p / p_b)^(1/gamma)`. The face is evaluated at the production face pressure `psf_lo`.
- **none** — both density references are zero. Pressure is still the production hydrostatic reference.
- **local polytrope** — `n = dln p / dln rho` from the two neighbouring cells, replaced by `gamma` when `|dln rho| < 1e-8` or `|n| < 0.05`. The cell reference equals the cell density, so the perturbation is zero. The face reference is the average of the two adjacent polytropes at `psf_lo`.

The profiles are not snapy's thermodynamics. Closed forms are used where they exist. The smooth tropopause and the moist columns are an independent RK4 hydrostatic integration with a step of about `1e-4`. The moist cases are nondimensional pseudo-adiabats, not a laboratory Clausius-Clapeyron fit and not kintera:

| regime | domain | gamma | notes |
|---|---|---|---|
| dry adiabat, H2-He and CO2 | 2H | 1.4 and 1.3 | `T = 1 - kappa z` |
| isothermal, H2-He and CO2 | 16H | 1.4 and 1.3 | |
| isothermal, N2 | 4H | 1.4 | same column as H2-He at equal `dz/H` |
| constant N^2 | 3H | 1.4 | `N^2 = kappa/2`, `theta = exp(N^2 z)` |
| inversion | 4H | 1.4 | lapse `+0.15` |
| sharp tropopause | 4H | 1.4 | adiabat below 1H, isothermal above |
| smooth tropopause | 4H | 1.4 | lapse fades across a tanh of width 0.25H |
| superadiabatic | 1.2H | 1.4 | lapse `1.5 kappa` |
| H2O on H2-He | 3H | 1.4 | `epsilon = 18/2.3`, `q(0) = 0.02`, `L/Rd = 5` |
| CH4 on H2-He | 3H | 1.4 | `epsilon = 16/2.3`, `q(0) = 0.05`, `L/Rd = 3` |
| H2O on CO2 | 3H | 1.3 | `epsilon = 18/44`, `q(0) = 0.02`, `L/Rd = 5` |
| heavy vapour, mu increasing upward | 4H | 1.4 | `q` rises with height, `mu_v = 40`, `mu_d = 2.3` |

N2 matches H2-He for `smooth5` and `none` at the same `dz/H` (both `8.122e-6` at `dz/H = 0.25`). The isentrope does not match, because it is anchored at the bottom and the N2 column is only 4H.

### Worst case

Ratio means the error divided by the best form on that same regime and `dz/H`.

All rows, including `dz/H` of 1 and 2:

| form | worst error | worst ratio | where the ratio is worst |
|---|---|---|---|
| smooth5 | 2.20 | 135 | inversion, `dz/H = 0.02` |
| isentrope | 2.60 | 3.2e11 | isothermal H2-He, `dz/H = 0.02` |
| none | 2.46 | 4.7e9 | isothermal H2-He, `dz/H = 0.02` |
| local polytrope | 0.175 | 1.3e7 | isothermal H2-He, `dz/H = 0.02` |

Restricted to `dz/H <= 0.5` (at least two cells per scale height):

| form | worst error | where that error is | worst ratio | where the ratio is worst |
|---|---|---|---|---|
| smooth5 | 7.96e-2 | CH4, `dz/H = 0.25` | 135 | inversion, `dz/H = 0.02` (`8.57e-4` vs local polytrope `6.36e-6`) |
| isentrope | 2.39 | isothermal H2-He, `dz/H = 0.5` | 3.2e11 | isothermal H2-He, `dz/H = 0.02` (`0.406` vs smooth5 `1.27e-12`) |
| none | 0.288 | CH4, `dz/H = 0.25` | 4.7e9 | isothermal H2-He, `dz/H = 0.02` |
| local polytrope | 6.53e-2 | CH4, `dz/H = 0.25` | 1.3e7 | isothermal H2-He, `dz/H = 0.02` (`1.67e-5` vs smooth5 `1.27e-12`) |

### What T1 says, and what it does not

No form stays within about 2x of the best form on every row. On the ratio rule, smooth5 is the least bad, and its 135x miss is `8.6e-4` against `6.4e-6` on a fine inversion, not an O(1) error. On absolute error with at least two cells per scale height, the local polytrope is slightly ahead (`0.065` vs `0.080`). The isentrope does not converge on a tall isothermal column: at `dz/H = 0.02` the error is still `0.41`, because a bottom-anchored adiabat is the wrong shape. This is not a choice of what snapy should ship. That waits on T3, T4, and the combined table.

### Full table

regime | form | dz/H | gamma | max relative face error
---|---|---|---|---
dry_adiabat/H2He | smooth5 | 2.500e-01 | 1.400e+00 | 3.585e-02
dry_adiabat/H2He | isentrope | 2.500e-01 | 1.400e+00 | 1.209e-02
dry_adiabat/H2He | none | 2.500e-01 | 1.400e+00 | 1.088e-01
dry_adiabat/H2He | local_polytrope | 2.500e-01 | 1.400e+00 | 1.215e-02
dry_adiabat/H2He | smooth5 | 1.250e-01 | 1.400e+00 | 2.094e-02
dry_adiabat/H2He | isentrope | 1.250e-01 | 1.400e+00 | 3.136e-03
dry_adiabat/H2He | none | 1.250e-01 | 1.400e+00 | 5.586e-02
dry_adiabat/H2He | local_polytrope | 1.250e-01 | 1.400e+00 | 3.140e-03
dry_adiabat/H2He | smooth5 | 5.000e-02 | 1.400e+00 | 9.024e-03
dry_adiabat/H2He | isentrope | 5.000e-02 | 1.400e+00 | 5.131e-04
dry_adiabat/H2He | none | 5.000e-02 | 1.400e+00 | 2.285e-02
dry_adiabat/H2He | local_polytrope | 5.000e-02 | 1.400e+00 | 5.132e-04
dry_adiabat/H2He | smooth5 | 2.000e-02 | 1.400e+00 | 3.650e-03
dry_adiabat/H2He | isentrope | 2.000e-02 | 1.400e+00 | 8.284e-05
dry_adiabat/H2He | none | 2.000e-02 | 1.400e+00 | 9.266e-03
dry_adiabat/H2He | local_polytrope | 2.000e-02 | 1.400e+00 | 8.284e-05
isothermal/H2He | smooth5 | 2.000e+00 | 1.400e+00 | 2.195e+00
isothermal/H2He | isentrope | 2.000e+00 | 1.400e+00 | 2.543e+00
isothermal/H2He | none | 2.000e+00 | 1.400e+00 | 2.458e+00
isothermal/H2He | local_polytrope | 2.000e+00 | 1.400e+00 | 1.752e-01
isothermal/H2He | smooth5 | 1.000e+00 | 1.400e+00 | 2.100e-01
isothermal/H2He | isentrope | 1.000e+00 | 1.400e+00 | 2.604e+00
isothermal/H2He | none | 1.000e+00 | 1.400e+00 | 3.149e-01
isothermal/H2He | local_polytrope | 1.000e+00 | 1.400e+00 | 4.219e-02
isothermal/H2He | smooth5 | 5.000e-01 | 1.400e+00 | 9.374e-04
isothermal/H2He | isentrope | 5.000e-01 | 1.400e+00 | 2.387e+00
isothermal/H2He | none | 5.000e-01 | 1.400e+00 | 1.512e-01
isothermal/H2He | local_polytrope | 5.000e-01 | 1.400e+00 | 1.045e-02
isothermal/H2He | smooth5 | 2.500e-01 | 1.400e+00 | 8.122e-06
isothermal/H2He | isentrope | 2.500e-01 | 1.400e+00 | 1.563e+00
isothermal/H2He | none | 2.500e-01 | 1.400e+00 | 7.462e-02
isothermal/H2He | local_polytrope | 2.500e-01 | 1.400e+00 | 2.606e-03
isothermal/H2He | smooth5 | 1.250e-01 | 1.400e+00 | 9.537e-08
isothermal/H2He | isentrope | 1.250e-01 | 1.400e+00 | 8.845e-01
isothermal/H2He | none | 1.250e-01 | 1.400e+00 | 3.745e-02
isothermal/H2He | local_polytrope | 1.250e-01 | 1.400e+00 | 6.512e-04
isothermal/H2He | smooth5 | 5.000e-02 | 1.400e+00 | 3.300e-10
isothermal/H2He | isentrope | 5.000e-02 | 1.400e+00 | 3.795e-01
isothermal/H2He | none | 5.000e-02 | 1.400e+00 | 1.500e-02
isothermal/H2He | local_polytrope | 5.000e-02 | 1.400e+00 | 1.042e-04
isothermal/H2He | smooth5 | 2.000e-02 | 1.400e+00 | 1.266e-12
isothermal/H2He | isentrope | 2.000e-02 | 1.400e+00 | 4.063e-01
isothermal/H2He | none | 2.000e-02 | 1.400e+00 | 6.000e-03
isothermal/H2He | local_polytrope | 2.000e-02 | 1.400e+00 | 1.667e-05
const_N2/H2He | smooth5 | 2.500e-01 | 1.400e+00 | 2.549e-02
const_N2/H2He | isentrope | 2.500e-01 | 1.400e+00 | 2.924e-02
const_N2/H2He | none | 2.500e-01 | 1.400e+00 | 1.087e-01
const_N2/H2He | local_polytrope | 2.500e-01 | 1.400e+00 | 1.059e-02
const_N2/H2He | smooth5 | 1.250e-01 | 1.400e+00 | 1.462e-02
const_N2/H2He | isentrope | 1.250e-01 | 1.400e+00 | 1.906e-02
const_N2/H2He | none | 1.250e-01 | 1.400e+00 | 5.580e-02
const_N2/H2He | local_polytrope | 1.250e-01 | 1.400e+00 | 2.711e-03
const_N2/H2He | smooth5 | 5.000e-02 | 1.400e+00 | 6.184e-03
const_N2/H2He | isentrope | 5.000e-02 | 1.400e+00 | 9.025e-03
const_N2/H2He | none | 5.000e-02 | 1.400e+00 | 2.316e-02
const_N2/H2He | local_polytrope | 5.000e-02 | 1.400e+00 | 4.402e-04
const_N2/H2He | smooth5 | 2.000e-02 | 1.400e+00 | 2.530e-03
const_N2/H2He | isentrope | 2.000e-02 | 1.400e+00 | 3.910e-03
const_N2/H2He | none | 2.000e-02 | 1.400e+00 | 9.642e-03
const_N2/H2He | local_polytrope | 2.000e-02 | 1.400e+00 | 7.086e-05
inversion/H2He | smooth5 | 5.000e-01 | 1.400e+00 | 2.485e-02
inversion/H2He | isentrope | 5.000e-01 | 1.400e+00 | 1.118e-01
inversion/H2He | none | 5.000e-01 | 1.400e+00 | 1.722e-01
inversion/H2He | local_polytrope | 5.000e-01 | 1.400e+00 | 3.906e-03
inversion/H2He | smooth5 | 2.500e-01 | 1.400e+00 | 1.172e-02
inversion/H2He | isentrope | 2.500e-01 | 1.400e+00 | 6.291e-02
inversion/H2He | none | 2.500e-01 | 1.400e+00 | 8.574e-02
inversion/H2He | local_polytrope | 2.500e-01 | 1.400e+00 | 9.858e-04
inversion/H2He | smooth5 | 1.250e-01 | 1.400e+00 | 5.639e-03
inversion/H2He | isentrope | 1.250e-01 | 1.400e+00 | 3.374e-02
inversion/H2He | none | 1.250e-01 | 1.400e+00 | 4.184e-02
inversion/H2He | local_polytrope | 1.250e-01 | 1.400e+00 | 2.475e-04
inversion/H2He | smooth5 | 5.000e-02 | 1.400e+00 | 2.190e-03
inversion/H2He | isentrope | 5.000e-02 | 1.400e+00 | 1.436e-02
inversion/H2He | none | 5.000e-02 | 1.400e+00 | 1.633e-02
inversion/H2He | local_polytrope | 5.000e-02 | 1.400e+00 | 3.971e-05
inversion/H2He | smooth5 | 2.000e-02 | 1.400e+00 | 8.571e-04
inversion/H2He | isentrope | 2.000e-02 | 1.400e+00 | 6.023e-03
inversion/H2He | none | 2.000e-02 | 1.400e+00 | 6.457e-03
inversion/H2He | local_polytrope | 2.000e-02 | 1.400e+00 | 6.360e-06
tropopause_sharp/H2He | smooth5 | 5.000e-01 | 1.400e+00 | 4.600e-02
tropopause_sharp/H2He | isentrope | 5.000e-01 | 1.400e+00 | 2.112e-01
tropopause_sharp/H2He | none | 5.000e-01 | 1.400e+00 | 2.042e-01
tropopause_sharp/H2He | local_polytrope | 5.000e-01 | 1.400e+00 | 2.595e-02
tropopause_sharp/H2He | smooth5 | 2.500e-01 | 1.400e+00 | 2.240e-02
tropopause_sharp/H2He | isentrope | 2.500e-01 | 1.400e+00 | 1.197e-01
tropopause_sharp/H2He | none | 2.500e-01 | 1.400e+00 | 9.283e-02
tropopause_sharp/H2He | local_polytrope | 2.500e-01 | 1.400e+00 | 1.281e-02
tropopause_sharp/H2He | smooth5 | 1.250e-01 | 1.400e+00 | 1.092e-02
tropopause_sharp/H2He | isentrope | 1.250e-01 | 1.400e+00 | 6.483e-02
tropopause_sharp/H2He | none | 1.250e-01 | 1.400e+00 | 4.865e-02
tropopause_sharp/H2He | local_polytrope | 1.250e-01 | 1.400e+00 | 6.335e-03
tropopause_sharp/H2He | smooth5 | 5.000e-02 | 1.400e+00 | 4.312e-03
tropopause_sharp/H2He | isentrope | 5.000e-02 | 1.400e+00 | 2.781e-02
tropopause_sharp/H2He | none | 5.000e-02 | 1.400e+00 | 2.066e-02
tropopause_sharp/H2He | local_polytrope | 5.000e-02 | 1.400e+00 | 2.515e-03
tropopause_sharp/H2He | smooth5 | 2.000e-02 | 1.400e+00 | 1.701e-03
tropopause_sharp/H2He | isentrope | 2.000e-02 | 1.400e+00 | 1.142e-02
tropopause_sharp/H2He | none | 2.000e-02 | 1.400e+00 | 8.379e-03
tropopause_sharp/H2He | local_polytrope | 2.000e-02 | 1.400e+00 | 1.002e-03
tropopause_smooth/H2He | smooth5 | 5.000e-01 | 1.400e+00 | 4.729e-02
tropopause_smooth/H2He | isentrope | 5.000e-01 | 1.400e+00 | 2.298e-01
tropopause_smooth/H2He | none | 5.000e-01 | 1.400e+00 | 2.195e-01
tropopause_smooth/H2He | local_polytrope | 5.000e-01 | 1.400e+00 | 2.430e-02
tropopause_smooth/H2He | smooth5 | 2.500e-01 | 1.400e+00 | 2.249e-02
tropopause_smooth/H2He | isentrope | 2.500e-01 | 1.400e+00 | 1.323e-01
tropopause_smooth/H2He | none | 2.500e-01 | 1.400e+00 | 1.019e-01
tropopause_smooth/H2He | local_polytrope | 2.500e-01 | 1.400e+00 | 6.041e-03
tropopause_smooth/H2He | smooth5 | 1.250e-01 | 1.400e+00 | 1.076e-02
tropopause_smooth/H2He | isentrope | 1.250e-01 | 1.400e+00 | 7.223e-02
tropopause_smooth/H2He | none | 1.250e-01 | 1.400e+00 | 5.332e-02
tropopause_smooth/H2He | local_polytrope | 1.250e-01 | 1.400e+00 | 1.508e-03
tropopause_smooth/H2He | smooth5 | 5.000e-02 | 1.400e+00 | 4.175e-03
tropopause_smooth/H2He | isentrope | 5.000e-02 | 1.400e+00 | 3.101e-02
tropopause_smooth/H2He | none | 5.000e-02 | 1.400e+00 | 2.254e-02
tropopause_smooth/H2He | local_polytrope | 5.000e-02 | 1.400e+00 | 2.412e-04
tropopause_smooth/H2He | smooth5 | 2.000e-02 | 1.400e+00 | 1.645e-03
tropopause_smooth/H2He | isentrope | 2.000e-02 | 1.400e+00 | 1.270e-02
tropopause_smooth/H2He | none | 2.000e-02 | 1.400e+00 | 9.114e-03
tropopause_smooth/H2He | local_polytrope | 2.000e-02 | 1.400e+00 | 3.860e-05
superadiabatic/H2He | smooth5 | 1.200e-01 | 1.400e+00 | 2.745e-02
superadiabatic/H2He | isentrope | 1.200e-01 | 1.400e+00 | 5.637e-03
superadiabatic/H2He | none | 1.200e-01 | 1.400e+00 | 3.890e-02
superadiabatic/H2He | local_polytrope | 1.200e-01 | 1.400e+00 | 1.953e-03
superadiabatic/H2He | smooth5 | 5.000e-02 | 1.400e+00 | 1.212e-02
superadiabatic/H2He | isentrope | 5.000e-02 | 1.400e+00 | 2.141e-03
superadiabatic/H2He | none | 5.000e-02 | 1.400e+00 | 1.630e-02
superadiabatic/H2He | local_polytrope | 5.000e-02 | 1.400e+00 | 3.512e-04
superadiabatic/H2He | smooth5 | 2.000e-02 | 1.400e+00 | 4.960e-03
superadiabatic/H2He | isentrope | 2.000e-02 | 1.400e+00 | 8.261e-04
superadiabatic/H2He | none | 2.000e-02 | 1.400e+00 | 6.544e-03
superadiabatic/H2He | local_polytrope | 2.000e-02 | 1.400e+00 | 5.707e-05
moist_H2O_jupiter/H2He | smooth5 | 2.500e-01 | 1.400e+00 | 7.622e-02
moist_H2O_jupiter/H2He | isentrope | 2.500e-01 | 1.400e+00 | 5.983e-02
moist_H2O_jupiter/H2He | none | 2.500e-01 | 1.400e+00 | 2.298e-01
moist_H2O_jupiter/H2He | local_polytrope | 2.500e-01 | 1.400e+00 | 5.878e-02
moist_H2O_jupiter/H2He | smooth5 | 1.250e-01 | 1.400e+00 | 2.022e-02
moist_H2O_jupiter/H2He | isentrope | 1.250e-01 | 1.400e+00 | 1.531e-02
moist_H2O_jupiter/H2He | none | 1.250e-01 | 1.400e+00 | 1.206e-01
moist_H2O_jupiter/H2He | local_polytrope | 1.250e-01 | 1.400e+00 | 1.261e-02
moist_H2O_jupiter/H2He | smooth5 | 5.000e-02 | 1.400e+00 | 4.358e-03
moist_H2O_jupiter/H2He | isentrope | 5.000e-02 | 1.400e+00 | 6.922e-03
moist_H2O_jupiter/H2He | none | 5.000e-02 | 1.400e+00 | 5.381e-02
moist_H2O_jupiter/H2He | local_polytrope | 5.000e-02 | 1.400e+00 | 3.101e-03
moist_H2O_jupiter/H2He | smooth5 | 2.000e-02 | 1.400e+00 | 2.727e-03
moist_H2O_jupiter/H2He | isentrope | 2.000e-02 | 1.400e+00 | 2.129e-03
moist_H2O_jupiter/H2He | none | 2.000e-02 | 1.400e+00 | 2.316e-02
moist_H2O_jupiter/H2He | local_polytrope | 2.000e-02 | 1.400e+00 | 1.787e-03
moist_CH4_neptune/H2He | smooth5 | 2.500e-01 | 1.400e+00 | 7.962e-02
moist_CH4_neptune/H2He | isentrope | 2.500e-01 | 1.400e+00 | 9.786e-02
moist_CH4_neptune/H2He | none | 2.500e-01 | 1.400e+00 | 2.877e-01
moist_CH4_neptune/H2He | local_polytrope | 2.500e-01 | 1.400e+00 | 6.531e-02
moist_CH4_neptune/H2He | smooth5 | 1.250e-01 | 1.400e+00 | 2.079e-02
moist_CH4_neptune/H2He | isentrope | 1.250e-01 | 1.400e+00 | 2.468e-02
moist_CH4_neptune/H2He | none | 1.250e-01 | 1.400e+00 | 1.114e-01
moist_CH4_neptune/H2He | local_polytrope | 1.250e-01 | 1.400e+00 | 1.717e-02
moist_CH4_neptune/H2He | smooth5 | 5.000e-02 | 1.400e+00 | 4.210e-03
moist_CH4_neptune/H2He | isentrope | 5.000e-02 | 1.400e+00 | 5.654e-03
moist_CH4_neptune/H2He | none | 5.000e-02 | 1.400e+00 | 5.352e-02
moist_CH4_neptune/H2He | local_polytrope | 5.000e-02 | 1.400e+00 | 3.105e-03
moist_CH4_neptune/H2He | smooth5 | 2.000e-02 | 1.400e+00 | 2.971e-03
moist_CH4_neptune/H2He | isentrope | 2.000e-02 | 1.400e+00 | 1.785e-03
moist_CH4_neptune/H2He | none | 2.000e-02 | 1.400e+00 | 2.301e-02
moist_CH4_neptune/H2He | local_polytrope | 2.000e-02 | 1.400e+00 | 1.718e-03
heavy_vapour_mu_up/H2He | smooth5 | 5.000e-01 | 1.400e+00 | 8.778e-03
heavy_vapour_mu_up/H2He | isentrope | 5.000e-01 | 1.400e+00 | 1.254e-01
heavy_vapour_mu_up/H2He | none | 5.000e-01 | 1.400e+00 | 1.600e-01
heavy_vapour_mu_up/H2He | local_polytrope | 5.000e-01 | 1.400e+00 | 8.058e-03
heavy_vapour_mu_up/H2He | smooth5 | 2.500e-01 | 1.400e+00 | 4.102e-03
heavy_vapour_mu_up/H2He | isentrope | 2.500e-01 | 1.400e+00 | 7.217e-02
heavy_vapour_mu_up/H2He | none | 2.500e-01 | 1.400e+00 | 7.891e-02
heavy_vapour_mu_up/H2He | local_polytrope | 2.500e-01 | 1.400e+00 | 2.017e-03
heavy_vapour_mu_up/H2He | smooth5 | 1.250e-01 | 1.400e+00 | 1.967e-03
heavy_vapour_mu_up/H2He | isentrope | 1.250e-01 | 1.400e+00 | 3.909e-02
heavy_vapour_mu_up/H2He | none | 1.250e-01 | 1.400e+00 | 3.847e-02
heavy_vapour_mu_up/H2He | local_polytrope | 1.250e-01 | 1.400e+00 | 5.047e-04
heavy_vapour_mu_up/H2He | smooth5 | 5.000e-02 | 1.400e+00 | 7.566e-04
heavy_vapour_mu_up/H2He | isentrope | 5.000e-02 | 1.400e+00 | 1.676e-02
heavy_vapour_mu_up/H2He | none | 5.000e-02 | 1.400e+00 | 1.504e-02
heavy_vapour_mu_up/H2He | local_polytrope | 5.000e-02 | 1.400e+00 | 8.081e-05
heavy_vapour_mu_up/H2He | smooth5 | 2.000e-02 | 1.400e+00 | 2.926e-04
heavy_vapour_mu_up/H2He | isentrope | 2.000e-02 | 1.400e+00 | 7.030e-03
heavy_vapour_mu_up/H2He | none | 2.000e-02 | 1.400e+00 | 5.956e-03
heavy_vapour_mu_up/H2He | local_polytrope | 2.000e-02 | 1.400e+00 | 1.293e-05
dry_adiabat/CO2 | smooth5 | 2.500e-01 | 1.300e+00 | 2.433e-02
dry_adiabat/CO2 | isentrope | 2.500e-01 | 1.300e+00 | 8.156e-03
dry_adiabat/CO2 | none | 2.500e-01 | 1.300e+00 | 9.303e-02
dry_adiabat/CO2 | local_polytrope | 2.500e-01 | 1.300e+00 | 8.183e-03
dry_adiabat/CO2 | smooth5 | 1.250e-01 | 1.300e+00 | 1.378e-02
dry_adiabat/CO2 | isentrope | 1.250e-01 | 1.300e+00 | 2.082e-03
dry_adiabat/CO2 | none | 1.250e-01 | 1.300e+00 | 4.782e-02
dry_adiabat/CO2 | local_polytrope | 1.250e-01 | 1.300e+00 | 2.084e-03
dry_adiabat/CO2 | smooth5 | 5.000e-02 | 1.300e+00 | 5.820e-03
dry_adiabat/CO2 | isentrope | 5.000e-02 | 1.300e+00 | 3.373e-04
dry_adiabat/CO2 | none | 5.000e-02 | 1.300e+00 | 1.958e-02
dry_adiabat/CO2 | local_polytrope | 5.000e-02 | 1.300e+00 | 3.374e-04
dry_adiabat/CO2 | smooth5 | 2.000e-02 | 1.300e+00 | 2.334e-03
dry_adiabat/CO2 | isentrope | 2.000e-02 | 1.300e+00 | 5.424e-05
dry_adiabat/CO2 | none | 2.000e-02 | 1.300e+00 | 7.950e-03
dry_adiabat/CO2 | local_polytrope | 2.000e-02 | 1.300e+00 | 5.425e-05
isothermal/CO2 | smooth5 | 2.000e+00 | 1.300e+00 | 2.195e+00
isothermal/CO2 | isentrope | 2.000e+00 | 1.300e+00 | 2.195e+00
isothermal/CO2 | none | 2.000e+00 | 1.300e+00 | 2.458e+00
isothermal/CO2 | local_polytrope | 2.000e+00 | 1.300e+00 | 1.752e-01
isothermal/CO2 | smooth5 | 1.000e+00 | 1.300e+00 | 2.100e-01
isothermal/CO2 | isentrope | 1.000e+00 | 1.300e+00 | 1.228e+00
isothermal/CO2 | none | 1.000e+00 | 1.300e+00 | 3.149e-01
isothermal/CO2 | local_polytrope | 1.000e+00 | 1.300e+00 | 4.219e-02
isothermal/CO2 | smooth5 | 5.000e-01 | 1.300e+00 | 9.374e-04
isothermal/CO2 | isentrope | 5.000e-01 | 1.300e+00 | 1.076e+00
isothermal/CO2 | none | 5.000e-01 | 1.300e+00 | 1.512e-01
isothermal/CO2 | local_polytrope | 5.000e-01 | 1.300e+00 | 1.045e-02
isothermal/CO2 | smooth5 | 2.500e-01 | 1.300e+00 | 8.122e-06
isothermal/CO2 | isentrope | 2.500e-01 | 1.300e+00 | 6.952e-01
isothermal/CO2 | none | 2.500e-01 | 1.300e+00 | 7.462e-02
isothermal/CO2 | local_polytrope | 2.500e-01 | 1.300e+00 | 2.606e-03
isothermal/CO2 | smooth5 | 1.250e-01 | 1.300e+00 | 9.537e-08
isothermal/CO2 | isentrope | 1.250e-01 | 1.300e+00 | 3.908e-01
isothermal/CO2 | none | 1.250e-01 | 1.300e+00 | 3.745e-02
isothermal/CO2 | local_polytrope | 1.250e-01 | 1.300e+00 | 6.512e-04
isothermal/CO2 | smooth5 | 5.000e-02 | 1.300e+00 | 3.300e-10
isothermal/CO2 | isentrope | 5.000e-02 | 1.300e+00 | 4.430e-01
isothermal/CO2 | none | 5.000e-02 | 1.300e+00 | 1.500e-02
isothermal/CO2 | local_polytrope | 5.000e-02 | 1.300e+00 | 1.042e-04
isothermal/CO2 | smooth5 | 2.000e-02 | 1.300e+00 | 1.266e-12
isothermal/CO2 | isentrope | 2.000e-02 | 1.300e+00 | 1.784e-01
isothermal/CO2 | none | 2.000e-02 | 1.300e+00 | 6.000e-03
isothermal/CO2 | local_polytrope | 2.000e-02 | 1.300e+00 | 1.667e-05
moist_H2O/CO2 | smooth5 | 2.500e-01 | 1.300e+00 | 2.984e-02
moist_H2O/CO2 | isentrope | 2.500e-01 | 1.300e+00 | 3.507e-02
moist_H2O/CO2 | none | 2.500e-01 | 1.300e+00 | 1.658e-01
moist_H2O/CO2 | local_polytrope | 2.500e-01 | 1.300e+00 | 4.118e-02
moist_H2O/CO2 | smooth5 | 1.250e-01 | 1.300e+00 | 2.033e-02
moist_H2O/CO2 | isentrope | 1.250e-01 | 1.300e+00 | 1.203e-02
moist_H2O/CO2 | none | 1.250e-01 | 1.300e+00 | 8.445e-02
moist_H2O/CO2 | local_polytrope | 1.250e-01 | 1.300e+00 | 6.920e-03
moist_H2O/CO2 | smooth5 | 5.000e-02 | 1.300e+00 | 9.125e-03
moist_H2O/CO2 | isentrope | 5.000e-02 | 1.300e+00 | 3.425e-03
moist_H2O/CO2 | none | 5.000e-02 | 1.300e+00 | 3.527e-02
moist_H2O/CO2 | local_polytrope | 5.000e-02 | 1.300e+00 | 1.094e-03
moist_H2O/CO2 | smooth5 | 2.000e-02 | 1.300e+00 | 3.802e-03
moist_H2O/CO2 | isentrope | 2.000e-02 | 1.300e+00 | 1.138e-03
moist_H2O/CO2 | none | 2.000e-02 | 1.300e+00 | 1.477e-02
moist_H2O/CO2 | local_polytrope | 2.000e-02 | 1.300e+00 | 1.760e-04
isothermal/N2 | smooth5 | 5.000e-01 | 1.400e+00 | 9.373e-04
isothermal/N2 | isentrope | 5.000e-01 | 1.400e+00 | 1.288e-01
isothermal/N2 | none | 5.000e-01 | 1.400e+00 | 1.512e-01
isothermal/N2 | local_polytrope | 5.000e-01 | 1.400e+00 | 1.045e-02
isothermal/N2 | smooth5 | 2.500e-01 | 1.400e+00 | 8.122e-06
isothermal/N2 | isentrope | 2.500e-01 | 1.400e+00 | 7.447e-02
isothermal/N2 | none | 2.500e-01 | 1.400e+00 | 7.409e-02
isothermal/N2 | local_polytrope | 2.500e-01 | 1.400e+00 | 2.606e-03
isothermal/N2 | smooth5 | 1.250e-01 | 1.400e+00 | 9.537e-08
isothermal/N2 | isentrope | 1.250e-01 | 1.400e+00 | 4.044e-02
isothermal/N2 | none | 1.250e-01 | 1.400e+00 | 3.610e-02
isothermal/N2 | local_polytrope | 1.250e-01 | 1.400e+00 | 6.512e-04
isothermal/N2 | smooth5 | 5.000e-02 | 1.400e+00 | 3.300e-10
isothermal/N2 | isentrope | 5.000e-02 | 1.400e+00 | 1.740e-02
isothermal/N2 | none | 5.000e-02 | 1.400e+00 | 1.441e-02
isothermal/N2 | local_polytrope | 5.000e-02 | 1.400e+00 | 1.042e-04
isothermal/N2 | smooth5 | 2.000e-02 | 1.400e+00 | 1.267e-12
isothermal/N2 | isentrope | 2.000e-02 | 1.400e+00 | 7.285e-03
isothermal/N2 | none | 2.000e-02 | 1.400e+00 | 5.947e-03
isothermal/N2 | local_polytrope | 2.000e-02 | 1.400e+00 | 1.667e-05

form | worst error | worst ratio to the best form | where
---|---|---|---
smooth5 | 2.195e+00 | 1.348e+02 | inversion/H2He dz/H=0.020000
isentrope | 2.604e+00 | 3.210e+11 | isothermal/H2He dz/H=0.020000
none | 2.458e+00 | 4.739e+09 | isothermal/H2He dz/H=0.020000
local_polytrope | 1.752e-01 | 1.317e+07 | isothermal/H2He dz/H=0.020000

Same ratio, restricted to dz/H <= 0.5 (at least 2 cells per H).
form | worst error | worst ratio to the best form | where
---|---|---|---
smooth5 | 7.962e-02 | 1.348e+02 | inversion/H2He dz/H=2.000e-02
isentrope | 2.387e+00 | 3.210e+11 | isothermal/H2He dz/H=2.000e-02
none | 2.877e-01 | 4.739e+09 | isothermal/H2He dz/H=2.000e-02
local_polytrope | 6.531e-02 | 1.317e+07 | isothermal/H2He dz/H=2.000e-02


### Comment 2 (2026-09-29)

## T2 — isothermal dispersion check

The solver only. No snapy run in this comment.

Code: commit `df2cd9a87299cd95f8c1c9580123897833b6be8b`, parent main `9378f0606a309959807385a2fbc9092573880f34`. Script: `studies/t2_isothermal_eigen.py`. Not a pull request.

Chebyshev collocation (degree 48) of the linearised compressible Euler equations on an isothermal column. Rigid lids, `w = 0` at both ends. One Fourier mode in x. Units `g = 1`, `H = 1`, `gamma = 1.4`, so `c_s = sqrt(gamma g H)` and `N^2 = (gamma-1)/gamma * g/H`. The column is `4H` tall.

The comparison is the rigid-lid dispersion relation

`omega^4 - omega^2 c_s^2 (k_x^2 + k_z^2 + 1/(4 H^2)) + N^2 c_s^2 k_x^2 = 0`,

with `k_z = n pi / L`, `n = 1, 2, 3`, and `k_x` in `{0, 0.5, 1, 2}`. Both the acoustic root and the gravity root are matched.

Worst relative frequency error: `1.89e-14`. The `k_x = 0` acoustic roots, which do not involve `N^2`, agree to `4e-16`. The gravity roots agree to `2e-14`.

Not in this check: a sponge, a non-isothermal `T(z)` or `mu(z)`, and initialising snapy with an eigenmode. Those are the rest of T2, after this validation.

### Comment 3 (2026-09-29)

## T2 step 3: one isothermal gravity mode in snapy

Code: commit `612976cddb4e9ed85ec80f2c41149b3d6fe5a8f2`. Not a pull request.

`smooth5` is the production path: the new method is not called, so the production `dref`/`dsf` are unchanged. `isentrope`, `none`, and `local_polytrope` replace only those two tensors and live on this branch.

Setup: L=4H, H=1, gamma=1.4, g=1, Rd=1, rigid x1 lids, periodic x2. One gravity mode, n=1, kx=1, nx2=64, amplitude 1e-4. RK3, CFL 0.4, LMARS, WENO5, nghost 3, no sponge, no implicit correction, non-hydrostatic fraction 1. Two periods, dt fixed from the initial CFL. omega_true = 0.40403230080237695.

`rel_freq` is (omega_fit - omega_true)/omega_true, with omega_fit the slope of unwrapped atan2(as, ac). `eigen_rel` is the L2 of the vertical velocity orthogonal to span{w(z) cos(kx x), w(z) sin(kx x)}, divided by ||w_sim||, at the end. `amp_ratio` is hypot(ac, as)/amp at the end. Periodic x2 ghosts are exchanged after every stage. Without that exchange a resting column grows a horizontal velocity, because the periodic ghosts are a layout exchange rather than a boundary function.

Rest control, amp=0, smooth5, nx1=16, same two periods: max interior speed 2.59e-6. The table would not have been written above 1e-4.

The eigenfunction error flattens from dz/H=0.05 to 0.02 (about 7e-4 to 9e-4) while the frequency error keeps falling (about 3e-5 to a few 1e-6). That floor is the fixed nx2=64, not the density reference.

This is not a ship call. On this one mode the four forms stay close. The widest gap is at dz/H=0.5, where |rel_freq| is 2.93e-3 (local polytrope), 3.52e-3 (smooth5), 4.03e-3 (isentrope), 9.77e-3 (none).

| form | dz/H | nx1 | rel_freq | eigen_rel | amp_ratio |
|---|---:|---:|---:|---:|---:|
| smooth5 | 0.5 | 8 | -3.525e-3 | 1.810e-1 | 1.0098 |
| isentrope | 0.5 | 8 | -4.026e-3 | 1.934e-1 | 0.9849 |
| none | 0.5 | 8 | +9.774e-3 | 2.180e-1 | 0.9685 |
| local_polytrope | 0.5 | 8 | -2.929e-3 | 1.801e-1 | 1.0161 |
| smooth5 | 0.25 | 16 | -8.712e-4 | 4.722e-3 | 1.0015 |
| isentrope | 0.25 | 16 | -1.611e-3 | 8.386e-3 | 0.9978 |
| none | 0.25 | 16 | +3.380e-4 | 6.108e-3 | 0.9989 |
| local_polytrope | 0.25 | 16 | -7.209e-4 | 5.058e-3 | 1.0029 |
| smooth5 | 0.125 | 32 | -2.078e-4 | 1.303e-3 | 1.0003 |
| isentrope | 0.125 | 32 | -4.242e-4 | 1.997e-3 | 0.9997 |
| none | 0.125 | 32 | -7.662e-5 | 1.376e-3 | 1.0002 |
| local_polytrope | 0.125 | 32 | -1.696e-4 | 1.254e-3 | 1.0007 |
| smooth5 | 0.05 | 80 | -3.210e-5 | 9.247e-4 | 1.00005 |
| isentrope | 0.05 | 80 | -6.675e-5 | 7.843e-4 | 0.99999 |
| none | 0.05 | 80 | -2.389e-5 | 9.318e-4 | 1.00005 |
| local_polytrope | 0.05 | 80 | -2.611e-5 | 7.760e-4 | 1.00010 |
| smooth5 | 0.02 | 200 | -5.026e-6 | 9.107e-4 | 1.000006 |
| isentrope | 0.02 | 200 | -1.047e-5 | 7.360e-4 | 0.999999 |
| none | 0.02 | 200 | -4.485e-6 | 9.109e-4 | 1.000007 |
| local_polytrope | 0.02 | 200 | -4.054e-6 | 7.571e-4 | 1.000015 |


### Comment 4 (2026-09-29)

## T3 / T4 — reported, not re-run

I did not re-run any of these jobs. Every number below is transcribed from a report by another study contributor (posted 2026-09-28 PT) and the two files attached to it, `t3_report.md` and a T4 report file. A per-form stretched-grid rest residual given in a follow-up matches the `R` column of the stretch table below. Nothing here was regenerated.

**Code, as named in that report.** `chengcli/snapy` branch `study/rho-ref-250`: `f82b2aae1775d61e46d96983688258791e6a99bc` (the `wb-density-ref` option) and `dc1c5caecfc9cb00c00eface135600bda2bc1cf4` (T3 configs and scripts), on main `9378f06`. Those two commits are on the branch. The branch head is now `7e93b4eb0728995e103230d5f3adfdc7beb2c0f7`, which adds `local_polytrope`. That commit is **not** in the T3/T4 numbers below. The T4 harness `study/rho-ref-250-t4` at `93c445f016312e87283c4c76801a1ce320bbf43f` is still not on GitHub (the commit is not found). It is not reviewable. T3's report says the GPU was an RTX 5090, one run per GPU, CPU single-threaded, kintera 2.5.13.

`local_polytrope` was not in this T3 or T4 matrix. The report said a T3 run of it had been started; no such table was posted. It stays absent here.

### Reported T3 reading, before the cross-regime summary

The report's T3-only reading, copied from `t3_report.md`: Straka does not separate the forms (they agree to <= 0.1% at 25 m). On Bryan & Fritsch, `none` has the smallest worst-case error at all three resolutions and `isentrope` is the worst. The report marked that as not yet the recommendation. The published Bryan & Fritsch 100 m reference is itself unconverged: the 50 m `theta_e'` max exceeds the published 100 m value of 4.10 K.

## Results (GPU; relative error vs the published value in parentheses)

#### straka: bubble, metric (rel. error vs published)

| dx | form | theta_p_min | u_max | u_min | w_max | w_min | front_m | theta_p_max | worst rel err | wall s |
|---|---|---|---|---|---|---|---|---|---|---|
| ref | - | -9.770 | 36.460 | -15.190 | 12.930 | -15.950 | 15537.44 | n/a | - | - |
| 100 | smooth5 | -9.591 (1.8%) | 36.128 (0.9%) | -15.383 (1.3%) | 12.919 (0.1%) | -15.767 (1.1%) | 15245.67 (1.9%) | 0.050 | 1.9% (front_m) | 30 |
| 100 | isentrope | -9.554 (2.2%) | 35.889 (1.6%) | -15.256 (0.4%) | 12.898 (0.2%) | -15.831 (0.7%) | 15244.05 (1.9%) | 0.049 | 2.2% (theta_p_min) | 34 |
| 100 | none | -9.544 (2.3%) | 35.670 (2.2%) | -15.397 (1.4%) | 12.851 (0.6%) | -15.935 (0.1%) | 15232.90 (2.0%) | 0.183 | 2.3% (theta_p_min) | 32 |
| 50 | smooth5 | -9.713 (0.6%) | 36.244 (0.6%) | -15.327 (0.9%) | 12.987 (0.4%) | -16.003 (0.3%) | 15381.71 (1.0%) | 0.026 | 1.0% (front_m) | 52 |
| 50 | isentrope | -9.699 (0.7%) | 36.101 (1.0%) | -15.335 (1.0%) | 13.007 (0.6%) | -16.038 (0.6%) | 15383.12 (1.0%) | 0.025 | 1.0% (front_m) | 53 |
| 50 | none | -9.694 (0.8%) | 36.080 (1.0%) | -15.341 (1.0%) | 13.006 (0.6%) | -16.046 (0.6%) | 15376.86 (1.0%) | 0.064 | 1.0% (u_max) | 53 |
| 25 | smooth5 | -9.730 (0.4%) | 36.210 (0.7%) | -15.332 (0.9%) | 12.982 (0.4%) | -16.018 (0.4%) | 15400.65 (0.9%) | 0.00949 | 0.9% (u_min) | 153 |
| 25 | isentrope | -9.726 (0.5%) | 36.166 (0.8%) | -15.338 (1.0%) | 12.990 (0.5%) | -16.030 (0.5%) | 15401.24 (0.9%) | 0.00848 | 1.0% (u_min) | 155 |
| 25 | none | -9.725 (0.5%) | 36.166 (0.8%) | -15.338 (1.0%) | 12.989 (0.5%) | -16.030 (0.5%) | 15400.70 (0.9%) | 0.016 | 1.0% (u_min) | 153 |

#### straka: unperturbed background (initial-state residual at t_end)

| dx | form | max\|w\| | max\|u\| | max\|dtheta\| | wall s |
|---|---|---|---|---|---|
| 100 | smooth5 | 4.33e-13 | 0.000 | 0.000 | 32 |
| 100 | isentrope | 6.37e-13 | 0.000 | 0.000 | 30 |
| 100 | none | 3.79e-13 | 0.000 | 0.000 | 33 |
| 50 | smooth5 | 8.73e-13 | 0.000 | 0.000 | 48 |
| 50 | isentrope | 5.74e-13 | 0.000 | 0.000 | 48 |
| 50 | none | 8e-13 | 0.000 | 0.000 | 48 |

#### bryan: bubble, metric (rel. error vs published)

| dx | form | theta_e_p_max | theta_e_p_min | w_max | w_min | theta_rho_p_max | theta_rho_p_min | top_m(theta_e'=1K) | worst rel err | wall s |
|---|---|---|---|---|---|---|---|---|---|---|
| ref | - | 4.095 | -0.306 | 15.713 | -9.927 | n/a | n/a | n/a | - | - |
| 200 | smooth5 | 3.163 (22.8%) | -0.135 (55.9%) | 13.285 (15.5%) | -8.349 (15.9%) | 2.690 | -0.066 | 8408.68 | 55.9% (theta_e_p_min) | 38 |
| 200 | isentrope | 2.754 (32.7%) | -0.079 (74.2%) | 13.251 (15.7%) | -8.307 (16.3%) | 2.378 | -0.053 | 8463.03 | 74.2% (theta_e_p_min) | 36 |
| 200 | none | 3.252 (20.6%) | -0.245 (19.9%) | 13.232 (15.8%) | -8.338 (16.0%) | 2.805 | -0.223 | 8454.14 | 20.6% (theta_e_p_max) | 37 |
| 100 | smooth5 | 4.455 (8.8%) | -0.197 (35.4%) | 15.187 (3.3%) | -9.571 (3.6%) | 3.847 | -0.125 | 8437.57 | 35.4% (theta_e_p_min) | 59 |
| 100 | isentrope | 3.677 (10.2%) | -0.109 (64.5%) | 15.128 (3.7%) | -9.548 (3.8%) | 3.181 | -0.077 | 8452.02 | 64.5% (theta_e_p_min) | 61 |
| 100 | none | 4.518 (10.3%) | -0.278 (9.1%) | 15.071 (4.1%) | -9.586 (3.4%) | 3.928 | -0.272 | 8460.55 | 10.3% (theta_e_p_max) | 59 |
| 50 | smooth5 | 5.140 (25.5%) | -0.258 (15.7%) | 15.979 (1.7%) | -10.327 (4.0%) | 4.455 | -0.164 | 8451.82 | 25.5% (theta_e_p_max) | 103 |
| 50 | isentrope | 4.151 (1.4%) | -0.137 (55.3%) | 16.065 (2.2%) | -10.332 (4.1%) | 3.619 | -0.087 | 8451.60 | 55.3% (theta_e_p_min) | 106 |
| 50 | none | 4.643 (13.4%) | -0.264 (13.6%) | 16.069 (2.3%) | -10.373 (4.5%) | 4.048 | -0.260 | 8455.60 | 13.6% (theta_e_p_min) | 104 |

#### bryan: unperturbed background (initial-state residual at t_end)

| dx | form | max\|w\| | max\|u\| | max\|dtheta_e\| | max\|dtheta_rho\| | wall s |
|---|---|---|---|---|---|---|
| 200 | smooth5 | 0.00173 | 6.26e-09 | 0.000153 | 0.000916 | 38 |
| 200 | isentrope | 0.00173 | 6.17e-09 | 3.05e-05 | 0.000916 | 37 |
| 200 | none | 0.00173 | 5.7e-09 | 0.000366 | 0.000977 | 38 |
| 100 | smooth5 | 0.000505 | 6.73e-09 | 3.05e-05 | 0.000244 | 57 |
| 100 | isentrope | 0.000505 | 6.68e-09 | 3.05e-05 | 0.000244 | 57 |
| 100 | none | 0.000505 | 6.47e-09 | 6.1e-05 | 0.000244 | 56 |

#### worst-case relative error per form (max over the referenced metrics)

| case | dx | smooth5 | isentrope | none | best | ratio worst/best |
|---|---|---|---|---|---|
| bryan | 200 | 55.9% (theta_e_p_min) | 74.2% (theta_e_p_min) | 20.6% (theta_e_p_max) | none | smooth5 2.72, isentrope 3.60, none 1.00 |
| bryan | 100 | 35.4% (theta_e_p_min) | 64.5% (theta_e_p_min) | 10.3% (theta_e_p_max) | none | smooth5 3.43, isentrope 6.24, none 1.00 |
| bryan | 50 | 25.5% (theta_e_p_max) | 55.3% (theta_e_p_min) | 13.6% (theta_e_p_min) | none | smooth5 1.88, isentrope 4.07, none 1.00 |
| straka | 100 | 1.9% (front_m) | 2.2% (theta_p_min) | 2.3% (theta_p_min) | smooth5 | smooth5 1.00, isentrope 1.18, none 1.23 |
| straka | 50 | 1.0% (front_m) | 1.0% (front_m) | 1.0% (u_max) | isentrope | smooth5 1.01, isentrope 1.00, none 1.05 |
| straka | 25 | 0.9% (u_min) | 1.0% (u_min) | 1.0% (u_min) | smooth5 | smooth5 1.00, isentrope 1.04, none 1.04 |

#### CPU spot checks (max |metric_cpu - metric_gpu|)

| run | max abs diff over metrics | cpu wall s | gpu wall s |
|---|---|---|---|
| bryan_bubble_dx200_isentrope | 0 | 28 | 36 |
| bryan_bubble_dx200_none | 0 | 28 | 37 |
| bryan_bubble_dx200_smooth5 | 0 | 23 | 38 |
| straka_bubble_dx100_isentrope | 0 | 59 | 34 |
| straka_bubble_dx100_none | 0 | 59 | 32 |
| straka_bubble_dx100_smooth5 | 0 | 61 | 30 |

## Findings

All 297 planned study jobs were attempted: 258 ran to completion and 39 exited on explicit unsupported-layout checks. Process completion is not a blanket numerical pass; the detailed checks below retain failures.

- Rank reproducibility, none: 16/16 comparisons bit-identical; largest max|diff|=0.
- Rank reproducibility, smooth5: 14/16 comparisons bit-identical; largest max|diff|=6.54763e-19.
- Smooth5 compatibility with main: 73/73 completed state comparisons bit-identical. The common unsupported layouts are retained as failed jobs.
- Isentrope cannot be measured on split x1 columns in this implementation: it explicitly requires nb1=1. Mixed process/local-block x1 layouts are rejected for all forms.
- Local-block decomposition, smooth5: maximum state difference 1.1192e-08; maximum initial density-reference seam jump 0.00660391. The issue is already present in main.
- Local-block decomposition, none: maximum state difference 5.78549e-09; maximum initial density-reference seam jump 0. The local-block handling is inherited from main; the main-baseline comparison itself uses smooth5.
- All 36 stretched rest cases exceed the diagnostic R<=1e-8 exact-rest target. The largest residual is 0.000736749. This shared pressure/reference discretization effect is not removed by changing rho_ref.
- Positivity evolution: 48/48 passed through 2000 steps. Minimum rho=2.40973e-299, minimum p=1.20487e-300; total recorded NaN/Inf entries=0. Guard on/off is bit-identical in 24/24 positive-input pairs.
- Direct fault limitation, smooth5/divide_weight_overflow: guard-on non-finite dref counts are cpu=3, cuda=3. These are post-EOS fault injections, not failures observed in the positive-input evolution cases.
- Direct fault limitation, isentrope/divide_bottom_zero: guard-on non-finite dref counts are cpu=64, cuda=64. These are post-EOS fault injections, not failures observed in the positive-input evolution cases.

The smooth5 guard removes invalid individual ratios, but does not avoid the raw division, protect the weighted numerator against overflow, or protect the isentrope anchor denominator. Final face fallbacks can hide non-finite references. No reconstruction fix or default-form change was made. The harness is local branch study/rho-ref-250-t4, commit 93c445f016312e87283c4c76801a1ce320bbf43f, based on implementation f82b2aa. Upstream subsequently added T3-only commit dc1c5ca; the tested reconstruction source is unchanged. No GitHub issue comment, push or PR was made.

## Stretched grids

| Profile | Form | Platform | q | R | face error | error / uniform | rest check |
|---|---|---|---:|---:|---:|---:|---|
| isothermal | isentrope | cpu | 1 | 1.45495e-11 | 0.00127717 | 1 | PASS |
| isothermal | none | cpu | 1 | 1.45495e-11 | 0.004383 | 1 | PASS |
| isothermal | smooth5 | cpu | 1 | 1.45495e-11 | 1.01725e-05 | 1 | PASS |
| isothermal | isentrope | cpu | 1.02 | 4.86657e-05 | 0.000633154 | 0.495749 | FAIL |
| isothermal | none | cpu | 1.02 | 4.86657e-05 | 0.00278997 | 0.636542 | FAIL |
| isothermal | smooth5 | cpu | 1.02 | 4.86657e-05 | 1.15593e-05 | 1.13634 | FAIL |
| isothermal | isentrope | cpu | 1.05 | 0.000213824 | 0.000208458 | 0.163219 | FAIL |
| isothermal | none | cpu | 1.05 | 0.000213824 | 0.00511427 | 1.16684 | FAIL |
| isothermal | smooth5 | cpu | 1.05 | 0.000213824 | 3.87894e-05 | 3.81318 | FAIL |
| isothermal | isentrope | cpu | 1.1 | 0.000736749 | 0.000327636 | 0.256534 | FAIL |
| isothermal | none | cpu | 1.1 | 0.000736749 | 0.0094094 | 2.14679 | FAIL |
| isothermal | smooth5 | cpu | 1.1 | 0.000736749 | 0.000132232 | 12.9991 | FAIL |
| polytrope | isentrope | cpu | 1 | 1.97053e-13 | 5.19925e-06 | 1 | PASS |
| polytrope | none | cpu | 1 | 1.97053e-13 | 0.00311859 | 1 | PASS |
| polytrope | smooth5 | cpu | 1 | 1.97053e-13 | 0.00127668 | 1 | PASS |
| polytrope | isentrope | cpu | 1.02 | 2.49832e-05 | 2.69991e-06 | 0.519288 | FAIL |
| polytrope | none | cpu | 1.02 | 2.49832e-05 | 0.00328693 | 1.05398 | FAIL |
| polytrope | smooth5 | cpu | 1.02 | 2.49832e-05 | 0.00132027 | 1.03414 | FAIL |
| polytrope | isentrope | cpu | 1.05 | 8.96623e-05 | 9.00631e-06 | 1.73223 | FAIL |
| polytrope | none | cpu | 1.05 | 8.96623e-05 | 0.00605312 | 1.94098 | FAIL |
| polytrope | smooth5 | cpu | 1.05 | 8.96623e-05 | 0.00239464 | 1.87568 | FAIL |
| polytrope | isentrope | cpu | 1.1 | 0.000286076 | 3.05617e-05 | 5.87809 | FAIL |
| polytrope | none | cpu | 1.1 | 0.000286076 | 0.0112299 | 3.60097 | FAIL |
| polytrope | smooth5 | cpu | 1.1 | 0.000286076 | 0.00429983 | 3.36799 | FAIL |
| isothermal | isentrope | cuda | 1 | 1.45591e-11 | 0.00127717 | 1 | PASS |
| isothermal | none | cuda | 1 | 1.45591e-11 | 0.004383 | 1 | PASS |
| isothermal | smooth5 | cuda | 1 | 1.45591e-11 | 1.01725e-05 | 1 | PASS |
| isothermal | isentrope | cuda | 1.02 | 4.86657e-05 | 0.000633154 | 0.495749 | FAIL |
| isothermal | none | cuda | 1.02 | 4.86657e-05 | 0.00278997 | 0.636542 | FAIL |
| isothermal | smooth5 | cuda | 1.02 | 4.86657e-05 | 1.15593e-05 | 1.13634 | FAIL |
| isothermal | isentrope | cuda | 1.05 | 0.000213824 | 0.000208458 | 0.163219 | FAIL |
| isothermal | none | cuda | 1.05 | 0.000213824 | 0.00511427 | 1.16684 | FAIL |
| isothermal | smooth5 | cuda | 1.05 | 0.000213824 | 3.87894e-05 | 3.81318 | FAIL |
| isothermal | isentrope | cuda | 1.1 | 0.000736749 | 0.000327636 | 0.256534 | FAIL |
| isothermal | none | cuda | 1.1 | 0.000736749 | 0.0094094 | 2.14679 | FAIL |
| isothermal | smooth5 | cuda | 1.1 | 0.000736749 | 0.000132232 | 12.9991 | FAIL |
| polytrope | isentrope | cuda | 1 | 1.80681e-13 | 5.19925e-06 | 1 | PASS |
| polytrope | none | cuda | 1 | 1.80681e-13 | 0.00311859 | 1 | PASS |
| polytrope | smooth5 | cuda | 1 | 1.80681e-13 | 0.00127668 | 1 | PASS |
| polytrope | isentrope | cuda | 1.02 | 2.49832e-05 | 2.69991e-06 | 0.519288 | FAIL |
| polytrope | none | cuda | 1.02 | 2.49832e-05 | 0.00328693 | 1.05398 | FAIL |
| polytrope | smooth5 | cuda | 1.02 | 2.49832e-05 | 0.00132027 | 1.03414 | FAIL |
| polytrope | isentrope | cuda | 1.05 | 8.96623e-05 | 9.00631e-06 | 1.73223 | FAIL |
| polytrope | none | cuda | 1.05 | 8.96623e-05 | 0.00605312 | 1.94098 | FAIL |
| polytrope | smooth5 | cuda | 1.05 | 8.96623e-05 | 0.00239464 | 1.87568 | FAIL |
| polytrope | isentrope | cuda | 1.1 | 0.000286076 | 3.05617e-05 | 5.87809 | FAIL |
| polytrope | none | cuda | 1.1 | 0.000286076 | 0.0112299 | 3.60097 | FAIL |
| polytrope | smooth5 | cuda | 1.1 | 0.000286076 | 0.00429983 | 3.36799 | FAIL |

CUDA rows are in the source file and are omitted here only where the face-error column matches the CPU row exactly. The CUDA rest residual `R` matches the CPU value at the printed digits except on the uniform (`q = 1`) rows, where it differs in the last digit (for example isothermal `q = 1`: CPU `1.45495e-11`, CUDA `1.45591e-11`). The largest stretched rest residual is `0.000736749`, isothermal `q = 1.1`, and it is the same number for `smooth5`, `isentrope` and `none`.

Other T4 findings, same file, not re-run:

- 297 jobs attempted: 258 finished, 39 hit an explicit unsupported-layout check.
- Rank reproducibility: `none` 16/16 bit-identical (max diff 0); `smooth5` 14/16 bit-identical, largest max diff `6.54763e-19`.
- `smooth5` vs main: 73/73 completed state comparisons bit-identical.
- Local-block seam, max state difference: `smooth5` `1.1192e-08` (already on main), `none` `5.78549e-09`. `isentrope` is not supported (`nb1 = 1` required). Mixed process/local-block layouts are refused for every form.
- Positivity: 48/48 ran 2000 steps, no NaN/Inf. Minimum rho `2.40973e-299`, minimum p `1.20487e-300`. Guard on/off is bit-identical in 24/24 positive-input pairs.
- The guard does not cover `smooth5` weighted-sum overflow (guard-on non-finite `dref` counts cpu=3, cuda=3) or the isentrope anchor denominator (`divide_bottom_zero`, guard-on non-finite `dref` counts cpu=64, cuda=64). These are injected faults, not failures of the positive-input runs.

The 297-row seam and positivity matrices stay in the T4 report file. They are not retyped here.

## Regime x form x resolution

T1 and T2 step 3 are the comments already on this issue (not re-run). T3 and T4 are the reported numbers above. `local_polytrope` has no T3 or T4 row.

Worst case in each regime. T1 "ratio" is the error divided by the best form on that same row. T3 is the worst relative error against the published metric.

| regime | where | smooth5 | isentrope | none | local polytrope |
|---|---|---:|---:|---:|---:|
| T1 face error, worst ratio, `dz/H <= 0.5` | inversion `dz/H = 0.02` for smooth5; isothermal H2-He `dz/H = 0.02` for the other three | 135 | 3.2e11 | 4.7e9 | 1.3e7 |
| T1 face error, worst absolute, `dz/H <= 0.5` | CH4 `dz/H = 0.25`, except isentrope (isothermal H2-He `dz/H = 0.5`) | 7.96e-2 | 2.39 | 0.288 | 6.53e-2 |
| T2 step 3, one isothermal gravity mode, worst \|rel_freq\| | `dz/H = 0.5`, nx1 = 8 | 3.52e-3 | 4.03e-3 | 9.77e-3 | 2.93e-3 |
| T3 Straka, worst relative error | 100 / 50 / 25 m | 1.9% / 1.0% / 0.9% | 2.2% / 1.0% / 1.0% | 2.3% / 1.0% / 1.0% | not run |
| T3 Bryan & Fritsch, worst relative error | 200 / 100 / 50 m | 55.9% / 35.4% / 25.5% | 74.2% / 64.5% / 55.3% | 20.6% / 10.3% / 13.6% | not run |
| T4 stretched rest residual `R` | isothermal, `q = 1.1`, CPU and CUDA | 7.37e-4 | 7.37e-4 | 7.37e-4 | not this form |

At the fine end of T2 step 3 (`dz/H = 0.02`) the four forms are within about `1e-5` in frequency. That row does not pick a form.

## Recommendation

The issue's rule is the smallest worst-case error over the regimes, then T4. On that rule these numbers do **not** support replacing `smooth5`.

- `none` wins Bryan & Fritsch at every resolution reported (worst-case 20.6% / 10.3% / 13.6%, against 55.9% / 35.4% / 25.5% for `smooth5`). Straka does not separate them. That is the T3 report's own reading, and the table supports it. It does not survive T1: on a resolved isothermal column `none` is `4.7e9` times `smooth5`.
- `isentrope` is the worst form on both that isothermal face test (`3.2e11` times `smooth5` at `dz/H = 0.02`) and Bryan & Fritsch (3.6–6.2 times the best form). T4 cannot run it on a split x1 column, and the guard does not cover its anchor denominator.
- `smooth5` has the smallest worst T1 ratio (135, and the absolute miss there is `8.57e-4` against `6.36e-6`). Its Bryan & Fritsch loss is a factor of about 1.9–3.4 against `none`, on a published 100 m reference the T3 report says is unconverged (the 50 m `theta_e'` max is larger than the published 100 m value).
- `local_polytrope` has the smallest T1 absolute error at `dz/H <= 0.5` (`6.53e-2`) and the smallest frequency error on the one T2 mode. It was not in T3 or T4, so it is not a ship choice from this table.
- T4 does not overturn this. The stretched-grid rest residual is the same for all three forms (`7.37e-4` at isothermal `q = 1.1`); it comes from the grid, not from `rho_ref`. The local-block seam is already on main for `smooth5`. Rank differences for `smooth5` are at `6.5e-19`.

Recommendation: keep `smooth5` as the default. Do not adopt `isentrope`. Do not adopt `none` on the strength of Bryan & Fritsch alone. Do not ship `local_polytrope` until it has a T3 and a T4. This is not the ship call; that stays with the maintainer.


### Comment 5 (2026-09-29)

## T3 re-run (4 forms) + T4 robustness: results table, decision rule, T4 pass/fail

**Code.** Branch https://github.com/chengcli/snapy/tree/study/250-t4-harness, head `1ffb3c16d8c6e182461876a30734af73320a45a9`, on main `3f7ad96` (not `9378f06`). Not a pull request. The branch has the three `study/rho-ref-250` commits cherry-picked unchanged (`wb-density-ref` option + guard, T3 scripts, `local_polytrope`), then a T4 harness under `study/rho_ref_250/t4/` and `study/rho_ref_250/decide_250.py`. The T4 harness in the 09:34 transcription (local commit `93c445f`, branch `study/rho-ref-250-t4`) is not in any checkout on this machine, not in any reflog, stash or unreachable object, and not on GitHub. It was **re-created** from the issue text, so its T4 metrics are not the same as the transcribed ones (see the last section). No library code changes beyond the cherry-picks. The T4 driver reads `_hydro_ref_x1` through a derived-class member pointer.

Build: Release, CUDA 13.1, RTX 5090 ×2, kintera 2.5.13. T3 runs on GPU, with CPU spot checks. T4 multi-rank runs use Gloo on CPU (1/2/4 ranks) and UCX on 2 GPUs (1/2 ranks).

### Results table: regime × form, worst ratio to the best form over resolution

T1 and T2 are the tables already on this issue, parsed and not re-run (T1 with `dz/H <= 0.5`). T3 is re-run here.

| regime | resolutions | smooth5 | isentrope | none | local_polytrope |
|---|---|---:|---:|---:|---:|
| T1 dry adiabat H2-He / CO2 | dz/H 0.02–0.25 | 44.1 / 43 | 1 / 1 | 112 / 147 | 1 / 1 |
| T1 isothermal H2-He / CO2 / N2 | 0.02–0.5 | 1 / 1 / 1 | 3.2e11 / 1.4e11 / 5.8e9 | 4.7e9 | 1.3e7 |
| T1 constant N² | 0.02–0.25 | 35.7 | 55.2 | 136 | 1 |
| T1 inversion | 0.02–0.5 | **135** | 947 | 1020 | 1 |
| T1 sharp / smooth tropopause | 0.02–0.5 | 1.77 / 42.6 | 11.4 / 329 | 8.36 / 236 | 1 / 1 |
| T1 superadiabatic | 0.02–0.12 | 86.9 | 14.5 | 115 | 1 |
| T1 moist H2O Jupiter / CH4 Neptune / H2O on CO2 | 0.02–0.25 | 1.6 / 1.73 / 21.6 | 2.23 / 1.82 / 6.47 | 17.4 / 17.2 / 83.9 | 1 / 1 / 1.38 |
| T1 heavy vapour, mu up | 0.02–0.5 | 22.6 | 544 | 461 | 1 |
| T2 isothermal gravity mode, \|rel_freq\| | 0.02–0.5 | 2.71 | 5.54 | 3.34 | 2.21 |
| T3 Bryan & Fritsch (re-run) | 200/100/50 m | 3.43 | 6.24 | 1.14 | 1.22 |
| T3 Straka (re-run) | 100/50/25 m | 1.01 | 1.18 | 1.23 | **∞ (aborts at 50 and 25 m)** |

T3 re-run, worst relative error against the published value:

| case | dx | smooth5 | isentrope | none | local_polytrope |
|---|---|---:|---:|---:|---:|
| Bryan | 200 m | 55.9% | 74.2% | 20.6% | 18.1% |
| Bryan | 100 m | 35.4% | 64.5% | 10.3% | 12.6% |
| Bryan | 50 m | 25.5% | 55.3% | 13.6% | 15.2% |
| Straka | 100 m | 1.9% | 2.2% | 2.3% | 19.9% (w_max 15.50 vs 12.93) |
| Straka | 50 m | 1.0% | 1.0% | 1.0% | FAILED: aborted t = 819 s, 21 floor redos |
| Straka | 25 m | 0.9% | 1.0% | 1.0% | FAILED: aborted t = 798 s, 13 floor redos |

CPU and GPU give identical T3 metrics (max abs diff 0 on 8 spot runs). Rest backgrounds are at round-off for every form (Straka max|w| ≤ 1.34e-12; Bryan 1.73e-3 / 5.05e-4 m/s at 200 / 100 m, the same for all forms).

### Decision rule

| test set | rows | smooth5 | isentrope | none | local_polytrope | smallest worst |
|---|---:|---:|---:|---:|---:|---|
| T1 (dz/H ≤ 0.5) | 62 | 135 | 3.2e11 | 4.7e9 | 1.3e7 | smooth5 |
| T2 step 3 | 5 | 2.71 | 5.54 | 3.34 | 2.21 | local_polytrope |
| T3 (re-run) | 6 | 3.43 | 6.24 | **1.23** | ∞ | none |
| **all** | 73 | **135** | 3.2e11 | 4.7e9 | ∞ | **smooth5** |

**Chosen form: `smooth5`. Worst-case ratio 135**, at T1 inversion `dz/H = 0.02`, where the absolute error is `8.57e-4` against `6.36e-6`. Its worst T3 ratio is 3.43 (Bryan 100 m, against `none`). No form meets the "~2× of the best everywhere" bar. On T3 alone `none` wins, but it is 4.7e9× worse than the best form on resolved isothermal faces (T1). `local_polytrope` wins T1 and T2 but fails the Straka control at 50 and 25 m.

### T4 pass/fail

| T4 item | what was run | smooth5 | isentrope | none | local_polytrope |
|---|---|---|---|---|---|
| large anomalies | −40 K cold pool on an adiabat, −30 K and +10 K in a +20 K/km inversion, −20 K at a sharp tropopause; 2000 steps each | **PASS** 4/4 | PASS 4/4 | PASS 4/4 | **FAIL** 2/4 (aborts: adiabat cold pool at step 776, tropopause at step 595) |
| rho/p positivity | isothermal 40 H (dz/H 0.31, p to 5e-13 p0) and 200 H (dz/H 1.56, p to 2e-82 p0), −10 K anomaly, 2000 steps, guard off/on | **PASS at 40 H** (2000 steps, min rho 6.9e-18); aborts at 200 H step 556 | FAIL (40 H aborts at step 26; 200 H at step 1) | PASS at 40 H; 200 H aborts at step 511 | FAIL (40 H aborts at step 1381; 200 H at 856) |
| rho/p guard | one-cell faults, count of non-finite dref+dsf, guard off → on (CPU = CUDA) | p=0: 11→0; bottom p=0: 13→0; rho/p overflow: 77→72 (**not covered**) | bottom p=0: 140→140 (anchor not covered) | 0 in all | 2–37, the guard does not apply |
| stretched x1 | rest columns q = 1, 1.02, 1.05, 1.1, 1000 steps, max\|v\|/c_s | PASS (same as every form) | same | same | same |
| block seams (process split, nb1 = 2, 4) | dsf / psf jump at shared faces; dref vs 1 rank at t = 0 | **PASS** (0 / 0 / 0) | refused (needs nb1 = 1) | PASS | PASS |
| block seams (local blocks, nb1 = 2 in 1 process) | same | **FAIL** dsf 1.4e-4, psf 1.3e-4, state 1.3e-5 rel | refused | FAIL psf 1.3e-4 (p_ref), state 3.4e-7 | FAIL dsf 1.4e-4, state 2.9e-3, \|Δv\| 0.73 m/s |
| bit-reproducibility across ranks | x2 splits 1/2/4 ranks (CPU) and 1/2 (GPU UCX); x1 splits 1/2/4 (CPU Gloo) and 1/2 (GPU UCX) | x2: 8/8 bitwise; x1 GPU: 2/2 bitwise; **x1 CPU: 0/4, ≤ 8.0e-15 rel** | x2: 8/8; x1 refused | x2 8/8; x1 GPU 2/2; x1 CPU 0/4 (≤ 9.8e-15) | x2 8/8; x1 GPU 1/2 (6.3e-15); x1 CPU 0/4 (≤ 8.4e-15) |
| cost | reference call, 262×1030 block, 1 GPU; 500 steps at 256×1024; T3 total GPU wall | **127 µs; 1.66 s; 613 s** (≈ none) | 215 µs; 1.77 s; 632 s | 126 µs; 1.70 s; 612 s | 292 µs; 2.19 s; 632 s |

Stretched rest residual max|v|/c_s after 1000 steps. The value is identical for all four forms to the printed digits:

| q | 1.0 | 1.02 | 1.05 | 1.1 |
|---|---:|---:|---:|---:|
| isothermal 4 H | 2.2e-10 | 9.6e-5 | 2.7e-4 | 1.17e-3 |
| dry polytrope 6.4 km | ~2e-15 | 4.5e-7 | 4.5e-6 | 1.19e-5 |

A −15 K cold pool on q = 1.05 runs 1000 steps for every form.

What T4 says about smooth5. It passes anomalies, positivity to 40 H, seams when the column is split across processes, stretched grids, and bitwise reproducibility on x2 splits and on x1 splits over 2 GPUs. It costs about the same as `none` (127 vs 126 µs per reference call, 1.66 vs 1.70 s for 500 steps).

**Shared failures (not specific to smooth5 or to `rho_ref`):**
- **x1 splits on CPU (Gloo, 2 and 4 ranks) are not bitwise reproducible.** The final state differs from 1 rank by ≤ 8.0e-15 (smooth5), 9.8e-15 (none) and 8.4e-15 (local_polytrope) relative; isentrope refuses nb1 > 1. The t = 0 references are identical, and 2 ranks on 2 GPUs (UCX) are bitwise for smooth5 and none.
- **The rho/p guard does not cover rho/p overflow.** One overflowing cell gives 77 non-finite dref+dsf with the guard off and 72 with it on. It does not cover the isentrope anchor either (bottom p = 0: 140 → 140). It does fix smooth5's p = 0 divide (11 → 0, bottom 13 → 0).
- **Every form aborts on the 200 H isothermal column** (dz/H 1.56, p down to 2e-82 p0), on floor redos: smooth5 at step 556, none 511, local_polytrope 856, isentrope 1.

**New finding: p_ref jumps at in-process x1 block seams.** With nb1 = 2 as two local blocks in one process, the face pressure reference `psf` differs across the seam by up to **1.3e-4** (relative; tropopause case, 1.8e-6 on the polytrope case) for every form that runs there, including `none` (isentrope refuses nb1 > 1). The same split across two processes gives a jump of exactly 0. This is consistent with the x1 reference relay in `_hydro_ref_x1` running only between process ranks (my reading of the code, not separately tested). The final-state differences from 1 block are smooth5 1.3e-5, none 3.4e-7 and local_polytrope 2.9e-3 (|Δv| 0.73 m/s). This is on main and is independent of the `rho_ref` choice.

### Differences from the 09:34 transcription

1. **T3, smooth5 / isentrope / none: no differences.** All 168 transcribed metric values reproduce at the printed precision, on the newer main (`3f7ad96`). Wall times differ by ≤ 7 s.
2. **T3, new rows:** `local_polytrope` was absent at 09:34. It aborts Straka at 50 and 25 m and has a 19.9% w_max error at 100 m. On Bryan it is best at 200 m (18.1%), so Bryan 200 m ratios move from smooth5 2.72 / isentrope 3.60 / none 1.00 to 3.08 / 4.09 / 1.14.
3. **Rank reproducibility:** 09:34 had none 16/16 bitwise and smooth5 14/16 (max 6.5e-19). The re-created harness finds every x2 split bitwise for every form. x1 splits on 2 GPUs (UCX) are bitwise for smooth5 and none. x1 splits on CPU (Gloo) are never bitwise, at ~1e-14, for any form. The 6.5e-19 was not reproduced. The harness is different, so the counts are not comparable one to one.
4. **Local-block seam:** 09:34 had smooth5 state diff 1.1e-8 with a seam jump of 6.6e-3, and none 5.8e-9 with jump 0. Here: smooth5 1.3e-5 with jump 1.4e-4, and none 3.4e-7 with rho_ref jump 0. The cases and normalisation differ. The qualitative result agrees, and one thing is new: **p_ref also jumps (1.3e-4) for every form** on local blocks.
5. **Positivity:** 09:34 had 48/48 through 2000 steps, min rho 2.4e-299. Here, only smooth5 and none pass, and only at 40 H. All forms abort at 200 H, and isentrope and local_polytrope abort at 40 H. The profiles differ, so this is not a contradiction of the 09:34 cases, but it is a harder test they did not pass.
6. **Guard faults:** 09:34 counts were smooth5 overflow 3 and isentrope bottom-zero 64. Here they are 72 and 140 (dref + dsf on a 70×134 block, CPU = CUDA). Same conclusion: neither is covered by the guard. Guard on/off final states are bitwise identical in 8/8 positivity pairs here (NaN-aware where both arms aborted), against 24/24 at 09:34.
7. **Stretched:** 09:34 reported R ≤ 7.37e-4, independent of form. Here the metric is max|v|/c_s, 1.17e-3 at isothermal q = 1.1, also independent of form. Same conclusion, different metric.

### Reproduce

```
git fetch origin study/250-t4-harness
git checkout 1ffb3c16d8c6e182461876a30734af73320a45a9
cmake -B build -DCMAKE_BUILD_TYPE=Release -DCUDA=ON -DNETCDF=ON && cmake --build build -j 24   # kintera >= 2.5.13
cd study/rho_ref_250
bash build_driver.sh ../../build && bash t4/build_t4.sh ../../build
python run_t3.py --bin $PWD/../../build/bin --out RUN/t3 --cpu-spot
python analyze_t3.py RUN/t3 --json RUN/t3.json && python make_table.py RUN/t3.json
python t4/run_t4.py --bin $PWD/../../build/bin --out RUN/t4
python t4/analyze_t4.py RUN/t4 --json RUN/t4.json
python decide_250.py --t1 T1_comment.md --t2 T2_step3_comment.md --t3 RUN/t3.json --by-regime
```
(`--bin` must be absolute. The T1 and T2 inputs are the bodies of the T1 and T2-step-3 comments on this issue.)

This is not the ship call; that stays with the maintainer.


### Comment 6 (2026-09-29)

Closing: keep `smooth5`, today's default, as the reference density for x1 reconstruction. No code change, no PR.

- **Results:** T1-T3 re-run with all four forms plus the full T4 robustness matrix, https://github.com/chengcli/snapy/issues/250#issuecomment-5900930851. The harness is on `study/250-t4-harness` at `1ffb3c16d8c6e182461876a30734af73320a45a9`, on main `3f7ad96`. That branch is study-only and will not be merged.
- **Cross-check (independent, not re-run):** the decision-rule arithmetic holds. The smooth5 worst-case ratio is 134.8, reported as 135: the T1 inversion at dz/H = 0.02, 8.571e-4 against local_polytrope's 6.360e-6. The T3 worst is Bryan 100 m, 35.4% / 10.3% = 3.44, reported as 3.43. All 168 T3 numbers reproduce the earlier transcription at printed precision.
- **Why smooth5:** it has the smallest worst-case ratio across T1-T3, not because it is close to the best everywhere. No form stays within 2x of the best on every row. `none` wins T3 alone but is 4.7e9x worse on isothermal T1 faces. `isentrope` is 3.2e11x worse. `local_polytrope` wins T1 and T2 but aborts Straka at 50 m and 25 m. In T4, smooth5 passes large anomalies, positivity on a 40 H column, cross-process seams, stretched grids and bit-reproducibility across rank counts, and costs 127 us per reference call.
- **Shared limits, the same for every form (recorded here, not new issues):** x1 splits on CPU differ by about 1e-14; the guard does not cover rho/p overflow; every form aborts on a 200 H column.
- **Follow-up:** p_ref jumps by 1.3e-4 at a seam when x1 is split into blocks within one process, for every form. It gets its own issue, backed by a failing test.


### Comment 7 (2026-09-30)

Reopening. The `smooth5` default stands for now, but the T3 part of this study is not settled. BF02's published theta_e' extremes (4.095 / -0.306 K) lie outside the range that moist-reversible advection conserves (the t=0 field, about [-0.02, 3.99] K). So T3's relative-error metric rewards reproducing BF02's own overshoot and undershoot. Details and numbers will follow in a separate comment.


### Comment 8 (2026-10-02)

Closing this study. The written finding, with every arm's numbers and code shas, is FINDING.md at commit 1e9156b5cb56ff2ef485b3ea91f128f59613df4b. Moist bubble (BF02), 50 m, D = depth of the final theta_e' minimum:

1. **Default unchanged: smooth5.** isentrope scores better on this bubble (2), but one idealised case is not enough to change a default.
2. **Known limit.** No reference form meets the BF02 theta_e' floor (<= 0.02 K) at <= 100 m. Closest: isentrope with vertical WENO `scale: true`, D = 0.0953 K, and the only arm whose theta_e' max stays under 3.99 K (3.81 K). Others: isentrope 0.137, smooth5 0.258, none 0.264, local_polytrope 0.330, per-cell moist 0.399 K. The reference choice is causal (none -> isentrope halves D); moisture in the column reference has no effect (moist column / dry isentrope = 1.003); per-cell centred forms are the worst.
3. **WENO normalisation.** `scale: true` on the vertical reconstruction cuts the isentrope arm by 30 % but raises the none arm by 28 %, so it acts through the reference rather than as added diffusion.

Not opened as new issues: the eps runs and an isentrope / moist reference option. Either is reopened only if a production run shows sensitivity to the reference. The Bryan IC discrete-rest fix rides as a commit in the #236 study PR.
