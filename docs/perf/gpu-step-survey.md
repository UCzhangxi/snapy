# GPU step survey: snapy main 6fbb397 vs v2.10.9 (914b43b)

> **INTERIM (2026-10-12).**
> **Done:** source read of the full step path, including `implicit_hydro.cpp`,
> `flux_positivity.cpp` and the EOS limiter in full. Both versions built CPU-only
> against kintera 2.6.2, with a profiling driver that counts leaf ATen ops
> (the proxy for CUDA kernels) and bytes touched per named scope. Proxy
> validation against the measured kernel counts. Host-device sync inventory.
> A first ranking, plus checks of the five CPU suspects and the covariance
> suspects.
> **Remains:** per-scope 1-thread CPU wall times (the driver mode is written
> but not yet run); env-gated patches for Zoey's RTX 5090 (one commit each,
> default off) with the exact run recipe; the final ranked table with
> estimates at 160^3.
> **ETA for the final:** about 4 to 5 hours after this commit.

Branch: `claude/gpu-step-survey`, cut from chengcli/snapy main 6fbb397. Raw data
and tooling are in `docs/perf/data/`.

## 1. Method and proxy validation

`docs/perf/data/perf_profile.cpp` mirrors `examples/run_hydro.cpp`: the same
initial state, kinetics step and `check_redo`, with `print_cycle_info` every
cycle as in run_hydro's default. A thread-local `RecordFunction` callback counts
**leaf** ATen ops: ops with no child op, excluding views, `empty`, `to` and
other no-kernel ops. Each one is counted once as a kernel, with the bytes of its
tensor inputs and outputs. Ops are attributed to the innermost `snap::` scope.
`instrument.py` and `spec_*.json` insert those scopes into each version; they
are local only and not part of any patch. Custom kernels (VIC, the x1 reference,
`fix_vapor`) are not ATen ops and are not counted (about 15 to 25 per step).

Decks: `examples/earth_crm.yaml` at 100x200, `implicit-scheme: 1`. The dry deck
has the H2O species, reactions and sedimentation removed; the moist deck keeps
all three species and runs kinetics.

| deck | v2.10.9 proxy | v2.10.9 CUDA (lead) | main proxy | main CUDA (lead) | delta proxy / CUDA |
|---|---|---|---|---|---|
| dry 2-D | 1039 | 1056 | 1610 | 1607 | +571 / +551 |
| moist 2-D | 1717 | 1713 | 2859 | 2846 | +1142 / +1133 |

The proxy reproduces the kernel counts to within 2%, so per-scope deltas from
it can be trusted as launch counts.

CPU at 1 thread (four runs at once on four cores, so absolute times are
inflated): dry 102 -> 120 ms/step (1.17x), moist 206 -> 263 ms/step (1.28x).
This agrees with the lead's 1.19x and 1.21x.

## 2. Where the +571 (dry) and +1142 (moist) launches are

Kernels per step, proxy. "MB" is the logical bytes touched per step on the
21.8k-cell 2-D grid; multiply by about 210 for 160^3, and by a further 1.5 to 2
for per-direction work, since 3-D adds the x3 faces. Full tables are in
`data/diff_dry.txt` and `data/diff_moist.txt`.

| scope | dry old->new | moist old->new | MB/step new (moist) |
|---|---|---|---|
| flux covariance (`_flux_covariance` + add) | 0 -> 90 | 0 -> 186 | 89 |
| 4.C carry (`flux_positivity_carry_`) | - | 0 -> 150 | 98 |
| 4.C species enthalpy (`species_enthalpy`) | - | 0 -> 57 | 24 |
| 4.C census meters (hits/severe/min) + lim_cut/lim_flux | - | 12 -> 90 | 28 |
| `print_cycle_info` every cycle (energies, PE, meters) | 10 -> 82 | 13 -> 88 | 11 |
| VIC radial-exact couple + post | 0 -> 108 | 0 -> 123 | 38 |
| VIC clamp-residual / dry-clamp meters | 0 -> 60 | 0 -> 69 | 15 |
| VIC projection + geometry (work_lo/hi, sin, mask) | 9 -> 48 | 9 -> 48 | 13 |
| VIC face-work post | 45 -> 66 | 51 -> 72 | 18 |
| VIC finiteness screens (2 syncs per stage) | 6 -> 30 | 6 -> 30 | 13 |
| limiter repair marks (all call sites) | 0 -> 55 | 0 -> 165 | 36 |
| check_redo EOS rerun on a clone | 4 -> 72 | 4 -> 98 | 39 |
| exchange (x1 wall refresh on x2 ghost slabs) | 54 -> 78 | 54 -> 78 | 0.5 |
| gravity work (face form) | 69 -> 93 | 75 -> 99 | 33 |

## 3. Host-device syncs per step at main (GPU)

The CPU proxy sees 16 per step dry and 22 moist. That count misses the D2H reads
that are no-ops on CPU and the `fix_vapor` count; those are added from the
source below.

| site (6fbb397) | per step | needed? |
|---|---|---|
| `hydro.cpp:411` `dt_min.min().item()` (max_time_step) | 1 | dt on the host; needed unless dt stays on the device |
| `implicit_hydro.cpp:378` finiteness screen `.item()` | 3 (1 per stage) | no: can be a device flag read in check_redo |
| `implicit_hydro.cpp:517` result screen `.item()` | 3 | same |
| `equation_of_state.cpp:296` -> `eos_dispatch.cu:74` `nerr.item<int>()` (fix_vapor count, vapor repair) | moist: 9 (every conserved-limiter call with ny>0) | no: accumulate on the device and check in check_redo. v2.10.9 had no sync here (its host int never counted) |
| `meshblock.cpp:1101-1119` print_cycle_diagnostics, 8 to 10 `.item()` | 8-10 when `ncycle_out` = 1 (the default) | batch into one `.cpu()`: same printout, 1 sync |
| `meshblock.cpp:1330` check_redo flags `.to(kCPU)` | 1 | yes (redo decision), once per step |
| kintera `thermo_y.cpp:510` Newton loop `.item()` in `VU->T` (saturation adjustment and kinetics) | moist: about 2 to 4, data-dependent iteration count | kintera change; blocks capturing the last stage |
| `meshblock.cpp:868` gravity-work fixer `.cpu()` | 0 on these decks (fixer off with gw=face) | - |

Total on GPU: dry about 16, moist about 31. v2.10.9 had about 6 (dry) and 7
(moist).

## 4. CPU suspects from the lead (status)

1. **floor_hit cons2prim every step.** Partly refuted. `floor_hit()`
   (meshblock.cpp:1199-1213) is not called on the step path. `check_redo` ->
   `local_redo_flag_tensor` does one `peos->forward(hydro_u.clone())`
   (meshblock.cpp:1294): +68 kernels dry and +94 moist, with the
   conserved+primitive limiter and marks inside. It is needed for the floor
   flag and for marking a repair caused by kinetics. A fused "floors + would-the-limiter-repair"
   reduction (density and pressure minima on the interior only) can replace it,
   1 to 3 kernels.
2. **Conserved limiter every stage.** Confirmed: it runs at :756 every stage,
   again at :798 (last stage, moist), inside U->W (`ideal_moist.cpp:165`, every
   stage), in the check_redo clone and in the kinetics EOS: 7 calls per step
   dry and 9 moist (W->U at :161 is only reached by outflow and initialisation).
   On a dry deck the limiter is idempotent: clamp rho, then clamp E against KE
   plus the minimum internal energy, both recomputed from the same values. The
   :756 call on stages 0 and 1 is immediately repeated by the next stage's U->W
   on the same interior; the exchange copy and a reflecting mirror commute with
   pointwise clamps. Skipping it should then be bitwise for dry. The
   last-stage call must stay, because `_hydro_u0` is taken before the next
   stage-0 EOS. Moist: not provably idempotent. The cloud-deficit repair changes rho after
   the energy clamp, so a second pass can move E in a cell with a repair; most
   such steps are redone anyway via the marks, but round-off repairs are
   unmarked. This needs the 200-step bitwise check on GPU.
3. **#217 meters every stage** (hydro_forward.cpp:771-783 and 805, 814-819).
   Confirmed: 90 kernels per step moist (30 per stage), about 28 MB/step at
   2-D. Their only reader is print_cycle_diagnostics (meshblock.cpp:1084-1087);
   no control flow uses them. The cheapest bitwise-for-state change is one
   fused reduction kernel for hits, severe, min, cut and flux. The counts and
   the min are exact; the cut and flux sums differ in summation order, which is
   acceptable for diagnostics. Alternatively, gate the meters behind
   `ncycle_out > 0`.
4. **Sedimentation velocity twice per face** (sed_hydro_impl.h:113,120).
   Confirmed. Each cell's Stokes properties are evaluated as the settling donor
   of its upper face and again as the rising donor of the face above. Worse,
   `eta` and `lambda` (sqrt, `pow(.,0.16)`, divisions; lines 57-60) are computed
   even when `const_vsed != 0`, where they are unused. Bitwise fixes: compute
   eta and lambda only on the Stokes branch, and evaluate per-cell `vsed` once.
   It is 1 kernel on GPU, so the saving there is small (estimate under 1 ms at
   160^3); on CPU it explains the +2.6 ms sedimentation.
5. **Scalar covariance rebuilds face states** (hydro_forward.cpp:702-706,
   734-738 and `scalar_flux_covariance` at 208-277). Confirmed, but only with
   passive scalars (none in these decks). It clones cwl and cwr (full nvar
   face states) and the dry row, then recomputes wbar, the projection, un, rho,
   dx1 and s2. Bitwise fix: keep `s2*rho` (cell part) and `d1(un)` from
   `_flux_covariance` instead of the clones.

**Covariance +13.5% on 1-thread Straka** (ideal-gas, ny=0, limiter off):
- "covariance forces 4.C on": `(limiter || cov2 || cov3) && ny > 0`
  (hydro_forward.cpp:762). This is refuted for Straka (ny=0) but true for any
  moist deck with `limiter: false`. There it adds the whole 4.C block (theta,
  census, theta exchange, species enthalpy, carry, scale, meters: about 470
  kernels per step moist).
- "W->I on face means per direction per stage": confirmed (hydro_forward.cpp:100).
  For ideal-gas that is 1 kernel; for ideal-moist about 10, including two
  `addmv`.
- Other waste in `_flux_covariance`:
  - wbar is formed for all nvar rows, though only rho, p, un and the species
    are used.
  - `dflx = zeros_like(wl)` fills nvar rows and `_flux2 += dcov` adds all nvar
    rows, although only IPR (dry) or IPR, IDN and ICY (moist) are non-zero.
  - s2 = dx1f^2/12 and dx1 are recomputed on every call.

  That is 29 kernels per stage dry and 61 moist, against about 8 needed in
  eager form or 1 fused. Adding only the non-zero rows is bitwise except for the
  sign of zeros (x + (+0) turns -0 into +0), which `torch.equal` ignores.
- Scalar rows: not present in Straka.

## 5. First ranking (to be refined in the final)

Expected saving / (effort x risk). Kernel savings are measured with the proxy;
ms are estimates (2-D: about 8 us of host time per launch from 12.94 ms /
1607; 160^3: from MB scaled by 210 and the nsys numbers given).

| # | item | kernels/step saved (dry/moist) | 2-D ms | 160^3 moist ms | effort | bitwise |
|---|---|---|---|---|---|---|
| 1 | fused `flux_positivity_carry_` + scale (+ meters) | -/~190 | ~1.5 | ~25 of the 29 | 1-2 d | plausible with `__dmul_rn`/`__dadd_rn` (no FMA), species sum in order 0,1,2; GPU check needed |
| 2 | fused covariance (dry: exact; moist: W->I's `addmv` order is cuBLAS's) | 87/183 | 0.7/1.5 | ~35 of 45 | 1-2 d | dry plausible; moist needs a tolerance, or replace `addmv` in the EOS with explicit loops everywhere |
| 3 | `print_cycle_info` batched to 1 sync, or `ncycle_out` > 1 | ~70 and 7 syncs | 0.6-1.0 | ~0 | 1 h | yes (printout identical) |
| 4 | VIC screens -> device flag (6 syncs/step); meters only when printed | 30+60 | 0.7 | ~2 | 0.5 d | yes for the state |
| 5 | `fix_vapor` count on the device (moist: 9 syncs/step) | 9 syncs | 0.3-0.5 | ~0.5 | 2 h | yes |
| 6 | skip the :756 limiter on stages 0,1 | ~56/~140 | 0.5/1.1 | ~3-5 | 1 h | dry: expected exact; moist: GPU check |
| 7 | check_redo EOS rerun -> fused floor/limiter check | 68/94 | 0.5/0.8 | ~5 | 0.5-1 d | decisions identical if the same arithmetic is kept |
| 8 | geometry cache (`cell_volume`/`face_area*` recomputed by outer/einsum on every call) | (to be measured) | - | small | 2 h | yes |
| 9 | `hydro_ref_x1` kernel: rho/p smoothed twice per cell (rs and rf), wall `pow` | 0 | 0 | ~5 of +7 | 0.5 d | yes (shared-memory reuse, same expressions) |
| 10 | VIC N=3: `ludcmp` added on every layer only as a singularity test, before the unchanged `inverse()` (forward_sweep_impl.h:75-76,122-123), plus 12 `isfinite` per layer | 0 | 0 | ~1.5 of 2.0 | 0.5 d | values identical; the rejection test must stay equivalent |
| 11 | CUDA graphs per stage/step | all launches | 2-D: 12.9 -> ~4-5 est. | ~1% | 1-2 wk | yes once blockers are fixed |

**CUDA-graph blockers (summary; details in the final):**
- dt and `dt*wght2` are host doubles baked into kernel arguments in every module
  (hydro_forward, forcings, implicit, positivity, sedimentation, VIC kernels).
- The syncs in section 3.
- Storage swaps: `hydro_u.set_` (meshblock.cpp:755), `_div.set_`
  (hydro_forward.cpp:841), `vsed.set_(torch::empty)` (sed_hydro.cpp:93),
  `reset_limiter_marks` allocating each step (equation_of_state.cpp:354), and
  kintera's `nfail_ = nfail_ + ...`.
- Host branches on device data: VIC reject, `_solve_failed`, and the kintera
  Newton loop.
- The cross-rank exchange (Gloo is not capturable; NCCL p2p is).

**Recommendation so far:**
- Large per-GPU domains (100^3 to 160^3) are bandwidth-bound. Do fusion first
  (items 1, 2, 9, 10), then the cheap simple items. Graphs gain at most about 1%
  there.
- Small 2-D decks are launch-bound (about 8 us per launch). Graphs give the
  largest gain there but cost the most effort. The cheap launch cuts (items 3 to
  8) recover about 3 to 5 ms of the 5.9 ms dry regression first, without graphs.
