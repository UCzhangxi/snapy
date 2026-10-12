# GPU step survey: snapy main 6fbb397 vs v2.10.9 (914b43b)

Final report, 2026-10-12. Branch `claude/gpu-step-survey` (cut from chengcli/snapy
main 6fbb397). Raw data and tools are in `docs/perf/data/`; the env-gated
prototypes are the commits below this report on the same branch.

**On "measured" vs "estimated":** no GPU was available. Everything marked
*measured* comes from CPU builds of both versions (kintera 2.6.2, torch
2.10, one intra-op thread). Kernel counts are a CPU proxy (section 1) that
reproduces the CUDA counts within 2%. Every GPU millisecond figure is an
*estimate*, scaled from the lead's measurements (ms/launch on the 2-D decks,
nsys at 160^3) or from bytes moved. Each one is marked "est.".

## Summary

1. **The regression is mostly more launches plus more full-array passes, not
   one hot kernel.**
   - Main adds +571 launches per step on the dry 2-D deck and +1142 on the
     moist deck (proxy; the lead measured +551 and +1133). At about 8 to 9 us of
     host time per launch, that alone explains the 2-D slowdown (dry +5.9 ms,
     moist +9.2 ms).
   - At 160^3 the same additions are full-array passes. In order of size:
     `flux_positivity_carry_` (largest), the covariance, the VIC radial-exact
     work, the limiter marks, the check_redo EOS clone and the meters.
   - On CPU at 1 thread the added *compute* is visible in the same scopes
     (section 3).
2. **CUDA graphs** would roughly halve or better the 2-D step (dry about
   11.9 -> about 4-5 ms est., moist about 21 -> about 8-9 ms est.) but need
   real refactoring:
   - dt is a host double baked into about 40 kernel arguments;
   - 16 to 31 host syncs per step;
   - storage swaps via `set_`;
   - kintera's Newton loop with a data-dependent trip count.

   They gain about 1% at 160^3.
3. **Fusion is what pays at 100^3-160^3.** Fused carry+scale (about -25 of
   29 ms est.), fused covariance (about -25 of 45 ms est.), and the x1
   reference kernel with shared-memory staging (about -5 ms est.) cover most
   of the +134 ms. Simple eager cuts add about 10 ms more est.
4. **Measured on CPU:** every env-gated prototype on this branch is bitwise
   identical to default over 200 steps on both 2-D decks: state including
   ghosts, dt of every step, redo count and printout. That holds alone and
   with all flags combined. All flags together cut the proxy launch count
   from 1610 to 1532 (dry) and from 2859 to 2467 (moist), before Zoey's set.
5. **Recommendation:**
   - Large domains: fusion first (carry, covariance, x1 reference), then the
     limiter/redo-clone cuts. Graphs are not worth it there.
   - Small 2-D decks: the cheap launch cuts first. Then decide on graphs,
     whose prerequisite (dt and the latches on the device, no `set_`) is
     about 1 to 2 weeks of work.
   - Fusion first in both cases: it helps both regimes, while graphs help
     only the small one.

## 1. Method and proxy validation (measured)

`data/perf_profile.cpp` (scoped profiler) and `examples/perf_step.cpp` (tool
on this branch) run the `examples/run_hydro.cpp` step loop: dynamics,
kinetics, check_redo, and `print_cycle_info` every cycle (the default
`ncycle_out`). A `RecordFunction` callback counts leaf ATen ops: ops with no
child op, excluding views, `empty` and `to`. It records their tensor bytes and
attributes them to the innermost `snap::` scope; `instrument.py` and
`spec_*.json` insert the scopes, locally only. Custom kernels (VIC, the x1
reference, `fix_vapor`, sedimentation) are not ATen ops: they are listed
separately and add about 15 to 25 per step. Decks: `docs/perf/dry2d.yaml` and
`moist2d.yaml` (earth_crm, 100x200, `implicit-scheme: 1`; dry = species,
reactions and sedimentation removed).

| | v2.10.9 proxy | v2.10.9 CUDA (lead) | main proxy | main CUDA (lead) |
|---|---|---|---|---|
| dry 2-D launches/step | 1039 | 1056 | 1610 | 1607 |
| moist 2-D launches/step | 1717 | 1713 | 2859 | 2846 |
| CPU 1 thread, ms/step (4 runs at once) | dry 90.8, moist 194.2 | | dry 115.1 (1.27x), moist 263.6 (1.36x) | |

The lead's 8-thread CPU regression (1.53x/1.59x) is larger than the
1-thread one (1.19x/1.21x). That is the same signature as on GPU: per-op
overhead (thread-pool dispatch on CPU, launch on GPU) times more and smaller
ops. The 1-thread per-scope times in section 3 separate the real added work.

## 2. Added launches by scope (measured, proxy, per step)

Full tables: `data/diff_dry.txt`, `data/diff_moist.txt`. MB is the logical
bytes touched on the 21.8k-cell grid; multiply by about 210 for 160^3, and by
about 1.5 to 2 for work done per face direction.

| scope | dry old -> new | moist old -> new | MB/step new, moist |
|---|---|---|---|
| covariance (`_flux_covariance` + `flux += dcov`) | 0 -> 90 | 0 -> 186 | 89 |
| 4.C carry (`flux_positivity_carry_`) | - | 0 -> 150 | 98 |
| 4.C species enthalpy | - | 0 -> 57 | 24 |
| 4.C census + lim_cut/lim_flux meters | - | 12 -> 90 | 28 |
| `print_cycle_info` every cycle | 10 -> 82 | 13 -> 88 | 11 |
| VIC radial-exact couple + post | 0 -> 108 | 0 -> 123 | 38 |
| VIC clamp meters | 0 -> 60 | 0 -> 69 | 15 |
| VIC projection/geometry | 9 -> 48 | 9 -> 48 | 13 |
| VIC face-work post | 45 -> 66 | 51 -> 72 | 18 |
| VIC finiteness screens | 6 -> 30 | 6 -> 30 | 13 |
| limiter repair marks (all call sites) | 0 -> 55 | 0 -> 165 | 36 |
| check_redo EOS on a clone | 4 -> 72 | 4 -> 98 | 39 |
| exchange (x1 wall refresh on x2 ghost slabs) | 54 -> 78 | 54 -> 78 | 0.5 |
| gravity work | 69 -> 93 | 75 -> 99 | 33 |

## 3. Added CPU time by scope (measured, 1 thread, exclusive ms/step)

Full tables: `data/cpu_scope_time_{dry,moist}.txt`. The largest additions are
listed. "implicit (own)" is the VIC custom kernels themselves (assemble,
solve, redistribute) plus unscoped glue.

| scope | dry old -> new | moist old -> new | reading |
|---|---|---|---|
| 4.C carry | - | 0 -> 11.8 | the largest single addition |
| implicit (own: VIC kernels) | 40.7 -> 45.4 | 42.7 -> 49.5 | real extra work in the sweep (ludcmp + isfinite per layer, section 6.4); matches GPU 3.0 -> 5.0 ms |
| covariance + add | 0 -> 3.1 | 0 -> 7.0 | |
| limiter marks (all sites) | 0 -> 4.9 | 0 -> 14.5 | `dens_energy()` stacks and copies of the interior on every call |
| VIC radial couple + post | 0 -> 4.5 | 0 -> 5.9 | |
| sedimentation | - | 9.4 -> 13.0 | Stokes eta/lambda per face, twice per cell (section 6.6) |
| check_redo EOS clone | 0 -> 2.6 | 0 -> 5.5 | |
| 4.C hspec + census + meters | - | 0.4 -> 5.5 | |
| VIC meters + screens | 1.7 -> 4.7 | 2.7 -> 6.6 | |
| gravity work | 1.4 -> 2.1 | 1.8 -> 2.5 | |
| x1 reference | 3.4 -> 3.2 | 3.8 -> 3.3 | no CPU increase; the GPU +7 ms is a latency effect (section 5.3) |

These agree with the lead's 8-thread scope deltas: conserved limiter (marks),
primitive limiter (marks), implicit, check_redo, covariance, face gravity
work, carry, sedimentation.

## 4. CUDA graphs: what blocks capture (6fbb397 file:line)

The unit should be one graph per RK stage (three per step). The step-level
code stays eager: max_time_step, print, kinetics, check_redo. The moist last
stage ends its graph before the saturation adjustment.

| # | blocker | where | what removing it takes |
|---|---|---|---|
| G1 | **dt is a host double** in kernel arguments: `-dt * _div`, the forcings, the gravity work, `out.mul_(dt)` in theta, `dt_corr = dt * wght2`, the VIC kernels (`rhs / dt`), the radial couple (`/ dt`), sedimentation, kintera `evolve_implicit` | hydro_forward.cpp:769,872,879,926,935,981,986,990,1004,1020,1039-1041,1065-1068; flux_positivity.cpp:67; implicit_hydro.cpp:353-355,363-372; forcing/*.cpp (about 40 sites) | Pass dt as a 0-d device tensor and have the custom kernels read it through a pointer. This can be bitwise if every `dt * a * b` keeps its order as tensor ops. 2 to 4 days. |
| G2 | **implicit screens**: `.item()` x2 per stage | implicit_hydro.cpp:378, 517 | device latch: prototype `SNAP_DEVICE_SCREENS` (bitwise, CPU-measured) |
| G3 | **fix_vapor count** `nerr.item()` per limiter call with species (moist: 9/step) | eos_dispatch.cu:74 via equation_of_state.cpp:296 | device count read in check_redo: prototype `SNAP_DEVICE_FIX_VAPOR` |
| G4 | storage swaps (`set_`) to fresh allocations | meshblock.cpp:755,768 (`hydro_u.set_`, `scalar_s.set_`); hydro_forward.cpp:841,860 (`_div.set_`); sed_hydro.cpp:35,93 (`vsed.set_`) | write into the existing storage (`copy_`/out=); bitwise; 0.5 day |
| G5 | per-step allocations of state the graph would capture | equation_of_state.cpp:354 (`reset_limiter_marks` allocates); kintera thermo_y.cpp:368 (`nfail_ = nfail_ + ...`), meshblock.cpp:1321 (`nfail_ = Tensor()`) | `zero_()` and in-place add; kintera change |
| G6 | data-dependent host loop | kintera thermo_y.cpp:505-514 (`VU->T` Newton, `.item()` per iteration) in saturation and kinetics | keep it outside the graphs (last stage split), or a fixed iteration count (not bitwise) |
| G7 | host branch on device data in the VIC latch | implicit_hydro.cpp:176 (`_solve_failed` host bool) | covered by G2 |
| G8 | per-step reads outside the stage graphs | hydro.cpp:411 (dt), meshblock.cpp:1330 (redo flags), meshblock.cpp:1101-1119 (8-10 prints) | stay eager; print batched to 1 read (`SNAP_BATCH_PRINT`) |
| G9 | cross-rank exchange inside a stage | layout.cpp:640 (Gloo send/recv), hydro_forward.cpp:522-582 (seam flux) | Gloo is not capturable; NCCL p2p is. Single GPU: self-copies only, no blocker |

**Expected saving (est.).** The 2-D decks are launch-bound: about 9.2 us per
launch dry (11.86 ms / 1289 after Zoey's set) and 8.0 us moist. In a graph
the floor is the sum of kernel durations: about 2 to 4 us for a 22k-cell
array, plus about 1 us between nodes. That gives roughly dry 4-5 ms and moist
8-9 ms per step (from 11.9 and 21.2). At 160^3 the GPU is busy for 395 ms
while the host needs about 25 ms to launch, so graphs save only the drains at
the syncs (about 30 x 10-50 us), under 1%.

## 5. Fusion candidates

| kernel | launches removed (proxy, measured) | memory passes | bitwise | prototype |
|---|---|---|---|---|
| 5.1 `flux_positivity_carry_` + `flux_positivity_scale_`, one pass per direction | moist -153/step (2859 -> 2700, +6 custom) | about 16 passes over ny-sized arrays per direction -> 1 read of theta/hspec/vel/fsed + flux update | **CPU: bitwise** (200 steps). CUDA: needs the species sum in order (((0+x0)+x1)+...)+0 (torch's short outer reduction); written with `__dmul_rn/__dadd_rn/__dsub_rn` so there is no FMA contraction | `SNAP_FUSED_CARRY` |
| 5.2 covariance rows + `flux += dcov` | dry -33, moist -117 | dflx zeros, the cov temporaries and the full-nvar add -> 1 pass; the face mean and W->I stay eager | **CPU: bitwise** dry and moist. W->I stays the EOS call, so cuBLAS `addmv` is unchanged. CUDA: same `_rn` care | `SNAP_FUSED_COV` |
| 5.3 x1 reference kernel | 0 (one kernel already) | rho/p smoothed once per cell instead of twice; the scan's increments and rho/p staged in shared memory (the serial thread-0 scan read global memory, about nc1 dependent loads per column) | CPU path unchanged. CUDA: same expressions; the scan keeps `face + gw*dx` so nvcc contracts it as before; check needed | `SNAP_REF_X1_SMEM` (CUDA only) |
| 5.4 limiter marks + floors inline (reference design 5) | dry up to about 55, moist about 165 (before Zoey's C3 fold) | `dens_energy()` stack, `ne`, `any` per call -> a flag inside the clamp kernel | needs a custom limiter kernel; the clamps are exact ops, so bitwise is plausible | not prototyped |
| 5.5 implicit pre/post (radial couple, post, face work, meters, deproject) | dry about 150, moist about 170 | about 20 temporaries per stage | radial couple/post use `index_select` stencils: fusable with exact op order; medium effort | not prototyped |

Estimated 160^3 moist savings (scaled from nsys):
- carry: about -22 to -25 of 29 ms;
- covariance: about -20 to -25 of 45 ms (the eager wbar and moist W->I
  remain, about 10 to 15 ms);
- x1 reference: about -4 to -5 of +7 ms (low confidence: the latency model
  is not measured);
- marks: about -5 ms;
- implicit pre/post: about -8 ms.

## 6. Simple changes, and the lead's CPU suspects (checked in source)

**6.1 floor_hit cons2prim every step.** Partly refuted. `floor_hit()`
(meshblock.cpp:1199) is not on the step path. `check_redo` ->
`local_redo_flag_tensor` runs one `peos->forward(hydro_u.clone())`
(meshblock.cpp:1294). It costs 68 (dry) / 94 (moist) launches and 2.6 / 5.5
ms CPU at 1 thread.
- It is needed: it supplies the floor flag, and its limiter marks a repair
  that kinetics caused.
- Cheapest change: derive the redo flags from the next cons2prim (reference
  design 5). The lead found that REUSE never engages, because stage 0
  refills the ghosts first.
- Bitwise alternative: one fused interior-only reduction of the same floors
  and repair tests. It is EOS-specific (ideal-moist f_eps/f_sig, the column
  `fix_vapor`), so 0.5 to 1 day. Not prototyped.

**6.2 Conserved limiter every stage.** Confirmed: 7 calls per step dry and 9
moist.
- Call sites: meshblock.cpp:756 every stage; :798 on the last stage (moist);
  inside U->W at ideal_moist.cpp:165; on the check_redo clone; on the kinetics
  EOS. (W->U at :161 is only reached by outflow and initialisation.)
- The :756 call on stages 0 and 1 is repeated by the next stage's U->W on the
  same interior. For ny = 0 the limiter is pointwise and idempotent (rho
  clamp, then E clamped to KE + e_min recomputed from the same values), and
  reflecting, periodic and extrapolation ghosts are copies or sign flips that
  commute with it.
- **Measured:** `SNAP_SKIP_STAGE_LIMITER` is bitwise over 200 steps on both
  decks. The moist deck is also bitwise, although the cloud repair is not
  provably idempotent. It saves 56 / 96 launches.
- Keep the last-stage call: `_hydro_u0` is copied before the next stage-0
  limiter.
- For a production version, restrict it to built-in pointwise BCs (no
  outflow, no Python bfuncs), no solids, no scalars and no cubed-sphere
  interpolation.

**6.3 #217 meters every stage** (hydro_forward.cpp:771-783, 805, 814-819;
VIC clamp meter implicit_hydro.cpp:395-414). Confirmed: 90 launches per step
moist, 2.5 + 0.8 ms CPU moist, and the VIC meters another 60/69. They are
read only by `print_cycle_diagnostics` (meshblock.cpp:1084-1087). Taking them
only on printing cycles is bitwise for the state but saves nothing at the
default `ncycle_out = 1`. The bigger cheap win is `ncycle_out` > 1 itself:
`print_cycle_info` costs 82/88 launches and 8-10 syncs per printed cycle.

**6.4 VIC sweep, N = 3** (forward_sweep_impl.h:75-76, 122-123).
- Every layer now runs `ludcmp` only as a singularity test, then keeps the
  old `a.inverse()`, plus 12 `isfinite` per layer.
- This explains the VIC kernel growth (GPU 3.0 -> 5.0 ms, CPU +4.7/+6.8 ms):
  more registers and compute in a sweep that is one thread per column with
  uncoalesced AoS loads.
- Building the inverse from the LU (reference design 7) is **not bitwise**,
  but keeps the rejection test equivalent.

**6.5 x1 reference twice.** The kernel forms each cell's 5-point smoothed
rho/p twice (rs, and rf of the cell above), plus `pow` in the wall
continuation (hydro_ref_x1_impl.h:189-200). There is no CPU growth, so on
GPU the cost is latency (thread-0 scan over global memory) and divergence.
See 5.3.

**6.6 Sedimentation twice per face** (sed_hydro_impl.h:113, 120). Confirmed.
- Each cell's Stokes state is evaluated as the settling donor of its own
  face and again as the rising donor of the face above.
- `eta` and `lambda` (sqrt, `pow(.,0.16)`) are computed even when
  `const_vsed != 0` (lines 57-60), where they are unused.
- Bitwise fix: compute eta and lambda only on the Stokes branch, and vsed
  once per cell.
- Cost: CPU +3.6 ms moist; GPU, a single kernel, under 1 ms est. at 160^3.

**6.7 Scalar covariance rows** (hydro_forward.cpp:702-706, 734-738;
`scalar_flux_covariance` 208-277). Confirmed, but only with passive scalars
(none in these decks): it clones the full face states and recomputes wbar,
the projection, un and s2. Bitwise fix: keep `s2*rho` and `d1(un)` from
`_flux_covariance`.

**6.8 Covariance +13.5% on 1-thread Straka (athena +2.9%).**
- "Covariance forces 4.C on" (hydro_forward.cpp:762,
  `(limiter || cov2 || cov3) && ny > 0`): refuted for Straka (ny = 0). It is
  true for any moist deck with `limiter: false`, where it adds the whole 4.C
  block, about 470 launches per step.
- "W->I on face means per direction per stage": confirmed
  (hydro_forward.cpp:100). It is 1 op for ideal-gas and about 10 for
  ideal-moist, including two `addmv`.
- Other waste per call:
  - `0.5*(wl+wr)` over all nvar rows;
  - `zeros_like(wl)` plus a full-nvar `flux += dcov`, where only IPR, IDN and
    the species are non-zero;
  - s2 and dx1 recomputed.

  That is 29 launches per stage dry and 61 moist, against about 8 in lean
  eager form or 1 fused. Measured on CPU: covariance 3.1 ms of 115 dry. In
  snapy every torch op makes a full pass with a temporary; athena does it in
  one loop.

**6.9 Other cheap items.**
- `cell_volume()`/`face_area*()` are rebuilt by `outer`/`einsum` on every call
  (coordinate.cpp:425-440). `SNAP_GEOM_CACHE` is bitwise and saves 50/86
  launches, mostly overlapping Zoey's IMP/C2/LIM4C caches.
- `fix_vapor` allocates `zeros` per call (G3).
- `print_cycle_info` reads 8-10 values one `.item()` at a time (G8).

## 7. Ranked table (net of Zoey's set)

Zoey's set (P1, C1, C2, C3, IMP, LIM4C, WALL1) gives dry 1289 / moist 2640
launches and 11.86 / 21.15 ms. Kernel savings below are proxy-measured on
6fbb397 and then reduced by the overlap with her set, where there is one. The
2-D ms come from about 9.2 (dry) and 8.0 (moist) us per launch, plus about
20 us per sync removed (est.). Score = saving / (effort x risk). The "adopts"
column names the reference design used (1 4.C, 2 covariance, 3 diagnostic
counters, 4 implicit checks, 5 one cons2prim, 6 smoothed reference, 7 LU
inverse).

| rank | item (file:line @6fbb397) | launches saved dry/moist (net) | 2-D ms (est.) dry/moist | 160^3 moist ms (est.) | effort | bitwise | proof | adopts |
|---|---|---|---|---|---|---|---|---|
| 1 | `ncycle_out` > 1 for production / benchmarks (meshblock.cpp:1009) | 82/88 and 8-10 syncs per skipped cycle | 0.9 / 0.9 | ~0 | config | yes (state) | trivially | 3 |
| 2 | fused carry+scale (hydro_forward.cpp:808-812, flux_positivity.cpp:106-149) | 0 / ~150 | 0 / 1.2 | -22 to -25 | done (prototype) | CPU yes; CUDA to test | `SNAP_FUSED_CARRY` 200-step dump | 1 (partly: one pass; enthalpy still for all faces) |
| 3 | fused covariance (hydro_forward.cpp:54-206, 693-708) | ~33 / ~117 | 0.3 / 0.9 | -20 to -25 | done (prototype) | CPU yes; CUDA to test | `SNAP_FUSED_COV` | 2 (rows only, s2 inline; W->I kept for bitwise) |
| 4 | skip the :756 limiter on stages 0,1 (meshblock.cpp:756) | ~50 / ~85 | 0.5 / 0.7 | -3 to -5 | done (prototype) | CPU yes, both decks; dry provable, moist empirical | `SNAP_SKIP_STAGE_LIMITER` | 5 (partly) |
| 5 | fix_vapor count on the device (eos_dispatch.cu:74) | 0 / 18 and 9 syncs | 0 / 0.3 | ~0.5 | done (prototype) | yes (CPU path unchanged) | GPU test | 4 |
| 6 | x1 reference with shared-memory staging (hydro_dispatch.cu:12-31) | 0 | 0 | -4 to -5 (low confidence) | done (prototype, CUDA only) | CUDA to test | `SNAP_REF_X1_SMEM` | 6 |
| 7 | redo flags from a fused floor/repair check instead of the EOS clone (meshblock.cpp:1294) | ~60 / ~85 | 0.6 / 0.7 | -4 | 0.5-1 d | decisions identical if the arithmetic is kept | 200-step dump incl. redo count | 5 |
| 8 | limiter marks inline in a clamp kernel (equation_of_state.cpp:199-322) | ~35 / ~130 after C3 | 0.3 / 1.0 | -5 | 1 d | plausible | dump | 5 |
| 9 | sedimentation: eta/lambda on the Stokes branch, vsed once per cell (sed_hydro_impl.h:57-60,113-125) | 0 | 0 (CPU -3.6 ms moist) | <1 | 0.5 d | yes | dump | - |
| 10 | meters only on printing cycles (hydro_forward.cpp:771-819, implicit_hydro.cpp:395-414) | (N-1)/N x 90-150 at ncycle_out = N | 0 at N = 1 | -2 | 2 h | yes (state); printed values become samples | dump at N = 1 and N = 10 | 3 |
| 11 | VIC screens as a device latch (implicit_hydro.cpp:378,517) | +54 launches, -6 syncs | about neutral eager | ~0 | done (prototype) | yes | `SNAP_DEVICE_SCREENS` + test_lu_failure | 4 (latch, not in-sweep) |
| 12 | batched print read (meshblock.cpp:1101-1119) | -8 syncs, about neutral launches | 0.15 | 0 | done (prototype) | yes, identical printout | `SNAP_BATCH_PRINT` | 3 |
| 13 | implicit pre/post fusion (radial couple/post, face work, deproject) | ~150 / ~170 | 1.4 / 1.4 | -8 | 2-3 d | plausible | dump | 4 |
| 14 | VIC N=3: inverse from the pivot-test LU (forward_sweep_impl.h:75-80,122-127) | 0 | 0 | -1.5 of 2 | 0.5 d | **no** (tolerance) | rel. diff over 200 steps | 7 |
| 15 | CUDA graphs per stage (G1-G9) | all launches | dry -7, moist -12 | under 1% | 1-2 wk | yes once G1-G5 are bitwise | dump + capture | - |
| 16 | geometry cache (coordinate.cpp:425-440) | 50/86 before Zoey; small after IMP/C2/LIM4C | ~0.1 | ~0 | done (prototype) | yes | `SNAP_GEOM_CACHE` | - |

## 8. Prototypes on this branch (env-gated, default off)

| commit | flag | CPU bitwise, 200 steps, dry/moist | leaf ops dry / moist (default 1610 / 2859) |
|---|---|---|---|
| 3204502 | `SNAP_GEOM_CACHE=1` | yes / yes | 1560 / 2773 |
| be430d1 | `SNAP_SKIP_STAGE_LIMITER=1` | yes / yes | 1554 / 2763 |
| 1f36310 | `SNAP_DEVICE_SCREENS=1` | yes / yes | 1664 / 2913 (-6 syncs) |
| 567e2d1 | `SNAP_DEVICE_FIX_VAPOR=1` | yes / yes (CUDA-only change) | 1610 / 2859 (GPU: -9 syncs, -18 launches) |
| 801de8e | `SNAP_BATCH_PRINT=1` | yes / yes, identical printout | 1620 / 2870 (-8 syncs) |
| 52307c7 | `SNAP_FUSED_CARRY=1` | yes / yes | 1610 / 2700 (+6 custom) |
| a33e8bf | `SNAP_FUSED_COV=1` | yes / yes | 1574 / 2739 (+3 custom) |
| 304c96b | `SNAP_REF_X1_SMEM=1` | n/a on CPU (CUDA only) | 1610 / 2859 |
| all flags together | | yes / yes | 1532 / 2467 |

"Bitwise" means: state bytes including ghosts, dt bytes of every step, redo
count and printout (`data/flags_cpu_bitwise.txt`). None of the CUDA code was
compiled here (no nvcc).

**GPU recipe (RTX 5090 / A100):** build with `-DBUILD_EXAMPLES=ON -DCUDA=ON`, then:

```
B=build/bin/perf_step.release
for d in dry moist; do K=$([ $d = moist ] && echo 1 || echo 0)
  PERF_DEVICE=cuda PERF_KINETICS=$K PERF_STEPS=200 PERF_DUMP=base_$d.pt $B -i docs/perf/${d}2d.yaml
  for f in SNAP_FUSED_CARRY SNAP_FUSED_COV SNAP_REF_X1_SMEM SNAP_SKIP_STAGE_LIMITER \
           SNAP_DEVICE_SCREENS SNAP_DEVICE_FIX_VAPOR SNAP_BATCH_PRINT SNAP_GEOM_CACHE; do
    env $f=1 PERF_DEVICE=cuda PERF_KINETICS=$K PERF_STEPS=200 PERF_DUMP=${f}_$d.pt \
        PERF_WARM=10 PERF_TIME=50 PERF_COUNT=5 $B -i docs/perf/${d}2d.yaml
    $B --compare base_$d.pt ${f}_$d.pt
  done
done
```

`--compare` prints `equal(==)`, `bytes_identical`, the dt and redo agreement,
and max abs/rel; the timed runs print `ms_per_step`, `cuda_kernels_per_step`
(Kineto), `cuda_memcpy_memset_per_step` and the leaf-op proxy.

## 9. Recommendation

- **Large per-GPU domains (100^3-160^3)** are bandwidth-bound.
  1. Fusion first: carry (rank 2), covariance (rank 3), the x1 reference
     (rank 6). Together about -50 ms of the +134 ms (est.).
  2. Then the eager cuts that remove full passes: limiter skip (4), the
     redo clone (7), marks (8), implicit pre/post (13). About -20 ms more
     (est.).
  3. Graphs will not pay there.
- **Small 2-D decks** are launch-bound at 8 to 9 us per launch.
  1. Do the config and launch cuts first: `ncycle_out`, then items 2-5 and
     7-8. About 3 to 5 ms of the regression comes back (est.), on top of
     Zoey's set.
  2. Graphs are the only way to go well below v2.10.9 (about 4-5 ms dry
     est.). They need G1 (device dt) and G4/G5 before any capture.
- **Fusion or graphs first: fusion.** It helps both regimes, it is local, and
  each kernel can be checked bitwise against the eager path. The graph
  prerequisites (G2, G3, G4, G5) are useful anyway and can land alongside.

**Uncertainty.**
- All GPU ms are estimates. The launch cost per op is taken from the lead's
  measurements; 160^3 figures scale proxy bytes and the nsys numbers.
- The `_rn`-intrinsic kernels are bitwise by construction only if torch's
  CUDA reduction order for a short outer dimension is the assumed one. That
  is the main thing the GPU run will show.
- The x1-reference latency explanation is the least certain item.

**Note on `claude/pr-a`.** Before the stop message, the per-commit pipeline
had pushed one commit to `claude/pr-a`: a2bbd06, "Read the cycle diagnostics
with one device-to-host copy", on perf/pr-a-base 4bf339c, CPU-bitwise over
200 steps on both decks. Nothing else was pushed. Ignore the branch or delete
it as you prefer.
