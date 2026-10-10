> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# snapy upstream issue threads #251-#294
Fetched 2026-10-09 from the public chengcli/snapy repository (GitHub REST API). Issue body, then each comment in order.

## Issue #251: CUDA: stencil_kernel fails on lines longer than 1024 cells (block-size limit)

State: closed; opened 2026-09-29; closed 2026-09-29.

On CUDA, reconstruction along a line longer than 1024 cells (ghost cells included) fails at launch with `cudaErrorInvalidConfiguration`. Lines of 1024 cells or fewer match the CPU result.

**Cause.** `stencil_kernel` in `src/utils/loops.cuh` launches one block per line with `dim3 block(line_length, 1, 1)`, and `threadIdx.x` is the cell index. A CUDA block holds at most 1024 threads, so a line of 1025 cells cannot launch. Shared memory is not the limit: at 1024 cells, float64 and 5 variables it is (1024*5+45)*8 = 41320 bytes, under the 48 KB default.

**Reach.** Any CUDA run with more than about 1018 interior cells along a reconstructed direction in one block. For example, Straka at 25 m (1030 cells per line with ghosts) had to be split across two blocks. WENO5 is shown failing; weno3 and polynomial reconstruction use the same launcher, so they fail the same way above 1024.

**Reproduction.** A test at main 9378f0606a309959807385a2fbc9092573880f34, commit 3c25c49118ad7b9d41afe4ff35932ba9a59305af: `tests/test_weno5_cuda_line.cpp`. On an H100 (sm_90), float64, 5 variables: 1024 cells passes (max abs difference from CPU below 1e-12), and 1025 cells fails at launch.

**Fix direction.** Tile the launch so that a line longer than the block limit is spread over several blocks or loops over cells, and keep the current launch for lines of 1024 or fewer. The fix is in progress on the same branch and will cover all three reconstructions that share the launcher, with a test for each.

Found during the #250 study.


## Issue #252: diffusion: kappa_iso conducts on T, so a resting adiabatic column drifts (walls ~0.9 K in 259 s at K = 75)

State: closed; opened 2026-09-29; closed 2026-09-29.

**Symptom.** A dry column at rest on an adiabat (constant potential temperature, hydrostatic) does not stay at rest once
`kappa_iso` is on. With `kappa_iso = 0` the same column stays at rest to round-off, so the scheme itself is well balanced
here and the whole drift comes from the conduction term.

**Where.** `src/forcing/diffusion.cpp:541-557` at main f24576b (dT/dn at 542-543, the rho cv flux at 549-557): the heat flux is
`-kappa_iso * (rho cv)_face * dT/dn`. On an adiabat dT/dz = -g/cp, which is not zero, so heat is conducted down the
lapse rate even though the column is neutrally stable. Hypothesis: the term is meant to act like turbulent mixing of
potential temperature, for which the flux is proportional to d(theta)/dn and vanishes on this column.

**Reproduction.** Red test: `tests/test_kappa_adiabatic_rest.py` (plus a `_cuda` twin) at commit
3374c48, one commit on main
f24576b. It runs N = 10 at K = 75 and fails with max|T(K) - T(0)| = 1.36e-2 K against a 1e-9 K tolerance; the K = 0
control differs by exactly 0. Setup: dry ideal gas (Rd 287.0, cp 1004.5 J/kg/K), 0 to 6.4 km, 64 cells (dz 100 m), reflecting x1
walls, g 9.8, T = 300 K - g z / cp at rest; WENO5, LMARS, RK3. Two arms step the same column N times at one shared
dt = 0.2594 s, with `kappa_iso` = K and with `kappa_iso` = 0. Oracle: T(K) - T(0), which is zero for conduction on theta.

**Measured** (snapy main 69e0084, CPU; the N = 10 rows reproduce at f24576b):

| N (t) | control max\|T-T0\| | K | bottom cell | top cell | interior mean (middle half) |
|---|---|---|---|---|---|
| 1 (0.26 s) | 1.1e-13 K | 10 | -1.25e-4 | +1.26e-4 | +1.15e-6 |
| | | 75 | -9.34e-4 | +9.44e-4 | +8.62e-6 |
| 10 (2.6 s) | 1.7e-13 K | 10 | -1.79e-3 | +1.83e-3 | +2.19e-5 |
| | | 75 | -1.33e-2 | +1.36e-2 | +1.64e-4 |
| 100 (26 s) | 1.5e-12 K | 10 | -1.77e-2 | +1.79e-2 | +1.88e-4 |
| | | 75 | -1.25e-1 | +1.27e-1 | +1.41e-3 |
| 1000 (259 s) | 1.3e-11 K | 10 | -1.65e-1 | +1.67e-1 | +1.89e-3 |
| | | 75 | -8.60e-1 | +8.83e-1 | +1.41e-2 |

- The drift is linear in K: the 75/10 ratio is 7.49 at every N.
- The interior heats at the analytic rate K g² cv / (R cp² T) = 7.93e-7 K/s per unit K (K = 75, N = 1000: 1.54e-2 K
  estimated, 1.41e-2 K measured).
- The wall cells dominate: the bottom cools and the top warms, antisymmetrically, at about half of K g / (cp dz) × t.
  The wall-face flux treatment is not diagnosed here.
- At K = 75 this is the same size as the ~2.5 K drift seen in the Straka case (K = 75, 900 s).

**Proposal.** Add an option to conduct on potential temperature (flux ∝ d(theta)/dn), keeping today's T form available.
A PR with the option and the test turned green will follow and link here.

**Open question for discussion.** Which form should be the default? Conduction on T is right for molecular heat
conduction; conduction on theta is right when `kappa_iso` stands in for turbulent mixing, which is how the atmospheric
examples use it. A moist or variable-composition column would also need a choice of which theta.


## Issue #254: hydro: p_ref restarts at each x1 block seam within one process (the scan relays only across processes)

State: closed; opened 2026-09-29; closed 2026-09-30.

**Symptom.** When one process holds a column in more than one x1 block, the hydrostatic reference pressure `p_ref` jumps at the seam between those blocks. Every well-balanced density form (`smooth5`, `none`, `isentrope`, `local_polytrope`) shows it. #250's T4 harness measured a jump of 1.3e-4 in relative terms (chengcli/snapy `study/250-t4-harness` at `1ffb3c16d8c6e182461876a30734af73320a45a9`, results in https://github.com/chengcli/snapy/issues/250#issuecomment-5900930851). When the same column is split across processes instead, `p_ref` stays continuous.

**Reproduction (a failing test, no production change).** Commit `0e4056d8de80420e27ae0be437101d603004d942`, on main `3f7ad96`: `tests/test_pref_local_seam.cpp` + `.yaml`. One process, x1 from 0 to 4 with nx1 = 4 (dx = 1), uniform rho = 1, p = 1e5, grav1 = -10. The column runs as 1 block, then as 2 blocks (pz = 2, blocks_per_process = 2). The test compares `p_ref` in the interior cell just below the seam:
- one block: 100020.00012499791
- two blocks, lower block: 100000.00012499791
- gap: 20 = g * rho * dx over the two cells above the seam. The upper block, which holds the domain top, agrees with the one-block run to within 1e-6.

Four cells, two per block, is the smallest split in which the cell under the seam is an ordinary interior cell: a block with nx1 = 1 stores no ghosts, so `p_ref` would use the edge stencil there. The test exits 1 on main.

**Mechanism (measured).** The downward reference scan restarts on each block. `hydro.cpp` relays the running face value only when the layout has a process group, pz > 1 and one block per process. A second block in the same process gets an empty anchor, so its scan starts again from its own top cell. The lower block's value equals such a fresh-anchor restart on its own top cell, to every printed digit.

**Reach.** Any run with more than one x1 block per process, on every density form. Splits across processes are not affected.

**Expected.** `p_ref` is single-valued across x1 block seams for every layout, the same as a one-block run to round-off. The test above passes, and a split across processes stays unchanged.

Found with #250's T4 harness.


## Issue #255: run_hydro exits 0 after 'Terminating abnormally'

State: closed; opened 2026-09-30; closed 2026-09-30.

**Symptom.** When a run ends with `[MeshBlock] Maximum number of redo attempts exceeded. Terminating.` and `Terminating abnormally`, `run_hydro` still exits with status 0. A batch script, CI job or chain of runs that checks `$?` records the aborted run as a success.

**Reproduction.** Commit `3626a7379df21119b513fc922043ac841c74ecd5` (test-only, on main `3f7ad96`). One of its two tests asserts a nonzero exit after `Terminating abnormally`, and it fails on main. The same happens with the full `./run_hydro.release -i examples/uranus.yaml`, which aborts at cycle 1 (the companion issue) and exits 0. Seen on CPU and CUDA.

**Expected.** Any abnormal termination exits nonzero. Normal completion keeps exit 0.



## Issue #256: examples/uranus.yaml aborts on cycle 1: five limiter redos, then Terminating abnormally (CPU and CUDA)

State: closed; opened 2026-09-30; closed 2026-09-30.

**Symptom.** The shipped `examples/uranus.yaml` never gets past cycle 1 on main `3f7ad967921eebb8b382bb97969384eef2bbd570`. Cycle 1 is retried five times, with dt going from 5.567 s down to 0.174 s. Every retry gives the cause as the limiter, with thetamin 0 and thetasevere about 3000. Then `[MeshBlock] Maximum number of redo attempts exceeded. Terminating.` and `Terminating abnormally` at time = 0, cycle = 1. It fails the same way on CPU and on CUDA (one H100); thetasevere at redo 5 is 3027 on CPU and 3015 on CUDA. There is no non-positive temperature and no extrapolate_ad warning.

**Reproduction (failing tests, no production change).** Commit `3626a7379df21119b513fc922043ac841c74ecd5`, two test-only commits on main `3f7ad96`: `tests/test_uranus_cycle1_abort.cpp` + `.yaml`. The smallest column with the shipped signature (limiter only, no extrapolate_ad warning) is nx1 = 96, nx2 = 1, nlim = 2. At 92 x 1 or 10 x 1 the run also aborts, but it prints extrapolate_ad non-convergence, which the shipped deck does not. The test fails because the run does not reach its cycle limit. Full deck: `./run_hydro.release -i examples/uranus.yaml`.

**Ruled out (measured).** The initial-condition setup prints `equilibrate_tp did not converge after 5 iterations` 9,682 times, because the deck sets max-iter 5. That is not the cause: with max-iter 50 no warning is printed, the mass changes only in its last digits, and cycle 1 still aborts, thetasevere 3029. The #236 prototype (`study/236-mm-species-enthalpy` `dc4abdd`) does not change the failure either.

**Seen on.** Two independent builds. The first used GCC 11.5.0, torch 2.10.0+cu128, kintera 2.5.13 built from `a8bef99`, the pyharp 2.6.5 wheel and pydisort 1.8.13. The second used kintera `ce9609d` (v2.5.13-4), the pyharp 2.4.6 wheel and pydisort 1.8.13. `run_hydro` adds unseeded noise, so runs are not bit-identical, but the failure is the same in every run.

**Mechanism.** Not known yet. Hypothesis: the limiter's positivity bound fires on the first step of this moist-mixture column for a reason that a smaller dt does not remove. The next step is to find which variable and which cell set thetasevere.

**Expected.** The shipped example runs past cycle 1. If it cannot, the example states why.

Found while working on #236; reproduced with the failing test. The exit status after `Terminating abnormally` is #255.


### Comment 1 (2026-09-30)

**Mechanism (measured, instrumentation only).** 96 x 1 case from `bug/uranus-cycle1-abort` `3626a73`, CPU, the first attempt of cycle 1.

- `thetasevere` counts interior (cell, species) entries with theta < 0.9, summed over stages. It goes from 0 to 3 at redo 1 because all three RK stages mark the same single entry, not because three cells are involved.
- That entry is NH3 (the limiter's species slot n = 1; dry is not limited) in cell i = 55, x1 = 191406.25 m (interior cell 52 of 96).
- The conserved NH3 density in that cell is exactly 0, and so is the cell below. The cell above holds 4.68e-4 kg/m^3.
- theta = avail / (dt * outgoing), where avail = relu(u) * volume * (1 - 4096 eps). With u = 0, avail is 0. The upper face flux is positive and drains the empty cell: 2.3e-18, 7.2e-18 and 4.7e-18 kg/m^2/s over the three stages. The lower face drains it too, at about -2e-22 to -4e-22. Volume is 5.25e9 m^3, dt 2.819 s.
- So 0 divided by a positive drain gives theta = 0, which is below 0.9, and the entry counts as severe. The step is redone. A smaller dt does not change theta, so all five redos fail the same way and the run aborts.
- The same cell is flagged on a repeat run. The 1e-18 face flux moves with the unseeded velocity noise, but the zero density and the neighbour do not.

In short: the severity census treats a round-off-sized outflow from a cell that holds none of the species (the edge of the NH3 layer) as a severe positivity violation. The limiter already withholds that flux, and the withheld mass is at round-off level. What should count as severe is the question for the fix.


### Comment 2 (2026-09-30)

**Reach is wider than moist-mixture.** The shipped `examples/earth_crm.yaml` (ideal-moist EOS) also aborts on cycle 1 at main `3f7ad96` with the same signature: five limiter redos, then `Terminating abnormally`. Found while testing the #255 fix. A fix for this issue should get both `uranus.yaml` and `earth_crm.yaml` past cycle 1.


## Issue #257: examples/uranus.yaml (with #256's fix) aborts at cycle 232 on real H2S / H2S(l) repairs along a row

State: closed; opened 2026-09-30; closed 2026-09-30.

**Symptom.** With #256's fix, the shipped `examples/uranus.yaml` gets past cycle 1 but still aborts later. At `nlim: 500` (the file's own `nlim` is -1) it runs clean through cycle 38. From cycle 39 on, every cycle redoes on the limiter (194 of the 232) and recovers, until cycle 232 uses up all five redos and ends with `Maximum number of redo attempts exceeded` / `Terminating abnormally`. mass0 = 7.8796252561722e+11.

**What crosses the bound.** A species repair of `H2S` and `H2S(l)` together, spanning one whole horizontal row. The first one on the shipped deck is 1.58e-10 kg/m^3 at rho = 0.885, which is 1.8e-10 of the cell's gas density. That is about 200 times the 4096-ulp bound #256 introduces, so it is a real repair, not round-off, and the redo is doing its job. The question is why these negatives appear from cycle 39 on, and why a smaller dt does not remove them at cycle 232.

**Reproduction (a failing test, no production change).** Commit `01b4cc0a479d9aedb5e8b26e377544cf84e031bf`, one test-only commit on top of #256's fix (`93d1de1`, chengcli/snapy `fix/256-limiter-census`). `UranusLate.column_reaches_cycle_40` uses a 100 x 1 column with `nlim: 40`. It dies at cycle 32, where the transfer is about 5e-9 of the cell, and never prints `Terminating on cycle limit`. 80 x 1 finishes 50 cycles with no redo, and 50 x 1 reaches `nlim: 40`. CPU.

**Not this issue.** With `nx2` of 4 or 16 the same column dies within the first few cycles with `limcut` of order 1. That is a different failure and is not covered by this test.

**Mechanism.** Not known yet. Hypothesis: something in the column's H2S cycle (kinetics, saturation adjustment or transport) produces negative H2S and H2S(l) along a row once the H2S layer has evolved for about 40 cycles, and the redo cannot shrink them away.

Found with #256's fix.


### Comment 1 (2026-09-30)

**Mechanism (measured, instrumentation only).** The 100 x 1 case from `bug/uranus-late-h2s` `01b4cc0`, on CPU, cell i = 55 (about 194 km, T 121.4 K, P 3.99e5 Pa, rho 0.847). `run_hydro`'s kinetics step works on a stale primitive state. Transport and the positivity limiter are not involved, the saturation adjustment's own output never goes negative, and #236 is not related.

1. On the last RK stage the saturation adjustment evaporates all the H2S(l) (9.45e-8 -> 0 kg/m^3), but only in `hydro_u` (`meshblock.cpp:787-790`).
2. `hydro_w` was last refreshed on entry to stage 2 (`hydro_forward.cpp:26`), so it still holds the cloud from before the adjustment.
3. `run_hydro`'s kinetics builds its concentrations from that stale `hydro_w` (`examples/run_hydro.cpp:177`). Coagulation (0.01/s) removes 2.49e-9 kg/m^3 and applies it to `hydro_u`, where the cloud is already 0 (`:185`, `:189`).
4. In `check_redo`, `cons2prim` repairs the resulting negative by borrowing from the parent H2S (`equation_of_state.cpp:282`), which is why H2S and H2S(l) move together. The repair is 2.9e-9 of rho, about 3,200x #256's bound, so it marks a redo.

**Why redo cannot clear it.** The repair halves each time dt halves, but the adjustment takes the cloud to exactly 0 at every dt. At cycle 31 it falls from 6.95e-11 to 2.23e-12 over redos 0-5. Clearing the bound would need dt < 0.035 s, about 6.3 halvings, and only 5 redos are allowed. Cycle 30 got through at redo 3 only because the adjustment happened to leave 2.55e-9 of cloud. On the full deck the state is horizontally uniform, so the whole x2 row moves together (400 marks = 200 cells x 2 species).

**Fix direction.** `run_hydro`'s kinetics should see the state after the adjustment: refresh `hydro_w` from `hydro_u` before the kinetics. The other options are to run the kinetics before the adjustment, or to cap coagulation at the cloud that is actually available; both treat the symptom. Not checked yet: whether other drivers or `earth_crm.yaml` follow the same stale-state pattern.


## Issue #260: examples/uranus.yaml (with #256's and #257's fixes) aborts at cycle 342 on an H2S repair at RK stage 0

State: closed; opened 2026-09-30; closed 2026-09-30.

Follow-up to #257: with #257's fix (8c8fc53, now in #258), the stale-`hydro_w` abort at cycle 232 is gone, and the full deck runs to cycle 342.

**Symptom.** full `examples/uranus.yaml` at `8c8fc5332d2f422d48ecd750f1c3df255dca26bf` aborts on CPU at cycle 342 after six limiter-only retries.

**Reproduction.** CPU-only Release invocation: `DEVICE=cpu CUDA_VISIBLE_DEVICES= build/bin/run_hydro.release -i examples/uranus.yaml`. It reaches termination in 51.0119 CPU seconds, including all six cycle-342 attempts.

**Measured.** the first severe repair is H2S at local indices `[2, 0, 0, 98]`, RK stage 0. Its conserved species-density repair is about `1.848e-13`, versus a tolerance of roughly `1.09e-14`–`1.27e-14`. I verified the limiter, CPU dispatch, and column-repair call chain.

**Not known.** no source file:line has yet been verified as the point where that H2S quantity first becomes invalid. Causality remains unattributed; its independence from the earlier stale-`hydro_w` failure is supported by the distinct species, stage, and location, but is still an inference.

**Expected.** The CPU deck continues beyond cycle 342 without exhausting the limiter redo budget; acceptance is 500 cycles.

Found in review of #257, on a CPU build.


## Issue #261: diffusion: with on_theta, kappa_iso diffuses theta at kappa_iso / gamma (the flux keeps rho*cv)

State: closed; opened 2026-09-30; closed 2026-10-02.

**Symptom.** With `on_theta: true`, `kappa_iso` diffuses potential temperature at `kappa_iso / gamma`, not at `kappa_iso`. A sine mode of theta decays at 0.714 of the expected rate (gamma = 1.4), so a case written for Straka et al. (1993), D(theta)/Dt = K lap(theta) with K = 75 m²/s, would need `kappa_iso` ≈ 105 to get K = 75.

**Reproduction.** Red test `DeviceTest.on_theta_sine_mode_decays_at_kappa` in `tests/test_diffusion.cpp`, at commit 16dfee8, one commit on main 3f7ad96 (test only, no source change):
```
git checkout 16dfee8   # the red-test commit
cmake --build build --target test_diffusion.release && cd build/tests && ./test_diffusion.release --gtest_filter='*on_theta*'
```
Setup: `tests/test_diffusion.yaml` (dry ideal gas, cv_R 2.5), 64 cells on a periodic 0 to 2π box, `nu_iso` 0, `kappa_iso` 0.25, `on_theta: true`. At rest with uniform p, theta = theta0 (1 + 0.01 sin x). The test applies the diffusion forcing alone for 200 forward-Euler steps (dt = 0.25 dx²/kappa_iso), projects theta onto sin x, and compares the measured decay rate with the forward-Euler rate at the centred stencil's k².

Why the forcing alone decides it: with an energy flux −rho c kappa (T/theta) grad(theta), D(theta)/Dt = (c / cp) kappa lap(theta), both at fixed rho and at fixed p. So no hydro step is needed, and c = cv gives kappa / gamma.

**Measured** (main 3f7ad96, CPU):

| dtype | rate / (kappa_iso k²) | rate / expected | result |
|---|---|---|---|
| float32 | 0.714882 | 0.714021 | FAIL |
| float64 | 0.714884 | 0.714023 | FAIL |

The other 30 CPU cases in `test_diffusion` pass. As a control we changed one line, using `rho * cp` in place of `rho * cv` on the `on_theta` path only. The ratio then becomes 0.999994 (float32) and 0.999978 (float64), and all 32 cases pass. That is a measurement of the prefactor, not a proposed fix.

**Mechanism (hypothesis).** `src/forcing/diffusion.cpp:509` builds the face coefficient as `rho * cv` for every conduction path. `on_theta` (`:516-523`) replaces only the gradient with (T/theta) d(theta)/dn and keeps that coefficient in the flux (`:597-608`). For theta to diffuse at `kappa_iso`, the `on_theta` flux needs `rho * cp`.

**Reachability.** Opt-in: `on_theta` defaults to `false` and came in with #253. We know of no configuration that sets it. The rest-state test from #252 cannot see the rate, because theta is flat at rest.

**Open question for the maintainer.** Does `kappa_iso` mean the thermal diffusivity k / (rho cp)? The docs call it a "thermal diffusivity". By the same algebra, the default temperature path (−rho cv kappa grad T) diffuses T at `kappa_iso / gamma` when p stays uniform, and at `kappa_iso` only at fixed rho. So: should cp be used on the `on_theta` path only, or also on the default path? Changing the default path would change the results of every existing case that uses `kappa_iso`.


## Issue #263: hydro, eos: since #226 a species-only clip requests a redo, so a moist CRM redoes until max_redo

State: closed; opened 2026-09-30; closed 2026-09-30.

**Symptom.** Since #226 (2249b4a), a 2D moist Jupiter cloud-resolving case (H2O + NH3, 100x100, `ideal-moist` EOS with `limiter: true`, rk3, cfl 0.9) aborts within a few cycles with `[MeshBlock] Maximum number of redo attempts exceeded. Terminating abnormally`. Every redo has cause `limiter`. The same card on the same stack otherwise runs 400 cycles to t = 5032.44 s with 0 redos.

**Bisect** (CPU, one probe per snapy sha, everything else fixed):

```
5b142af              GOOD  400 cycles, 0 redos
a91403e (#235)       GOOD  400 cycles, 0 redos      <- #226's parent on main
2249b4a (#226)       BAD   abort at cycle 6, 6 redos, all "limiter"
84a5dbd (#258, #256) BAD   abort at cycle 30, 25 redos, all "limiter"
5eeb9b6 (main)       BAD   (x86 CPU/GPU, arm64 CPU/GPU)
```

**Mechanism (hypothesis, the discriminating run is in progress).** Our #226 replaced the old repair flag, which was set only when the conserved limiter changed an interior density or energy, with `EquationOfState::limiter_marks_[0]`. That mark is also set when (a) the conserved limiter's vapor/cloud clamp changes any species (`equation_of_state.cpp:322` at 2249b4a), or (b) the primitive limiter sees a negative vapor/cloud mass fraction (`:340-344`). A moist CRM clips a species somewhere on nearly every attempt, and a smaller dt does not remove the clip, because advection re-creates it, so the step is redone until `max_redo`.

**Failing test.** Commit 60fe012d4b1c9c076fa7b68e1aa7d5012e57f797 (on main 5eeb9b6, test only, no src change): `tests/test_check_redo_species_clip.py` + a `_cuda` twin. A moist block gets cloud = -1e-6 rho in one interior cell and takes one step; `check_redo` must return 0 (a control step without the clip also returns 0).

```
                CPU              CUDA (V100)
main 5eeb9b6    RED  (err = 1)   RED
2249b4a         RED              -
a91403e         GREEN            GREEN
```

The test pins the decision (a species clip alone rejects the step), not the abort: in this toy the redo's restore repairs the planted cell, so the second attempt passes.

**Question for the fix.** Should a species-only clip (no interior density/energy change) ever request a redo? #226 marks it on purpose; the proposal is that species clips are recorded (census) but do not request a redo, while density/energy repairs keep requesting one.


### Comment 1 (2026-09-30)

**Mechanism measured** (was a hypothesis in the description). Each `limiter_marks_[0]` site was tagged and counted in the Jupiter CRM reproducer (CPU, 1 rank; the mark logic itself unchanged):

```
                         D  A   P   redos  terminated
2249b4a (#226)           0  6   0   6      cycle 6
5eeb9b6 tree (fa136b5)   0  28  0   28     cycle 34
```

D = the conserved limiter changed an interior density or energy (the pre-#226 criterion); A = the conserved limiter changed a species (vapor/cloud clamp, `equation_of_state.cpp:350-352` on main); P = the primitive limiter saw a negative vapor/cloud fraction.

Every redo comes from branch A alone, one A mark per attempt: density and energy never needed a repair, and the primitive limiter never saw a negative species. The species repair exceeds #256's `positivity_roundoff * rho` tolerance, so #256 does not cover it. This is the case the failing test plants.


### Comment 2 (2026-09-30)

**Closing: not a snapy source defect.** The trigger is the external driver, not snapy. That driver applies kinetics to the post-stage `hydro_w` without refreshing it from `hydro_u` first. snapy's own `run_hydro` has done that refresh since #257. The stale kinetics leaves ~30k cells with above-round-off negative species at the end of each accepted step. The next attempt's species repair then marks a redo, and the redo restores the same state. Same card, snapy main tree (fa136b5), CPU:

```
driver                                        cycles   redos      negative species at step start
external driver, unmodified                   abort    220 (all   ~29.5k-29.9k cells, min/rho -8.8e-13
                                                       limiter)
external driver + hydro_w refreshed first      4000     0          ~15.7k cells, denormal only (min/rho -1.1e-303)
snapy run_hydro (#257 order)                   4000     0          -
```

Every 400-cycle checkpoint in both 4000-cycle runs has 0 redos. The failing test at 60fe012d planted a negative start state and is withdrawn. A species repair of a bad start state still requests a redo that no dt can cure; that is the behavior #226 chose, and whether it should stay is a question for the limiter study in #236, not a fix here.


## Issue #264: diffusion: viscosity creates u2 in an x2-uniform rest state at the x1-wall row beside x2 block edges

State: closed; opened 2026-10-01; closed 2026-10-02.

## Symptom

A resting, x2-uniform column bounded by a reflecting x1 wall gains a spurious horizontal velocity u2 at cycle 1. It appears only when viscosity is on, and only in the wall-adjacent row, in the two cells beside an x2 block edge. With one block, those cells sit at the periodic x2 edge. A column that is uniform in x2 should keep u2 = 0 to round-off.

- `tests/test_wb_wall_corner.cpp`, `WallCorner.x2_uniform_rest_keeps_u2_zero`, on main 5eeb9b6. Setup: a resting polytrope, 32x8 cells, one block, reflecting x1, periodic x2, `nu_iso` 0.0234, 10 steps. Result: max|u2|/c_s = **3.98e-5** and max|v|/c_s = 4.08e-5, where the test asserts at most 1e-12.
- Controls that pass with the same setup: `kappa_iso` only, and no diffusion. Viscosity alone causes it.
- In a 128x512 resting polytrope run on 32 ranks, |u|/c_s = 1.15e-5 at every x2 block edge in the wall-adjacent row, from cycle 1, repeating every 16 cells. The value is bit-identical between snapy's stock `reflecting` boundary and a user wall boundary function, so the wall implementation is not the cause.

## Reproduction

Red test, which fixes nothing: commit f1774875ea1e5528fd9cc921a529075b45c673d2, one commit on main 5eeb9b6761ae484a98b3993aae18314fc58cf862 (+128 lines in `tests/test_wb_wall_corner.cpp`, +1 line in `tests/CMakeLists.txt`). Build and run it on CPU:

```
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCUDA=OFF -DBUILD_TESTS=ON
cmake --build build --target test_wb_wall_corner.release
cd build/tests && ./test_wb_wall_corner.release
```

## Mechanism (hypothesis, not yet shown)

At the x1-wall row, the viscous stencil reaches the corner ghost cells: the x1 ghosts of an x2-ghost column. Those cells are not filled consistently with the wall and the x2 neighbour, so the cross-derivative terms of the viscous stress do not cancel at the x2 edge. #254's x1-seam path does not cover this case, because it acts across x1 seams and not on a physical wall row at an x2 edge.

## Acceptance

The red test passes (max|u2|/c_s and max|v|/c_s at most 1e-12) on CPU and CUDA, and no existing test regresses.


### Comment 1 (2026-10-01)

Correction to the issue body: the second bullet ("Controls that pass with the same setup: `kappa_iso` only, and no diffusion") holds for u2 only. Those controls were run before the max|v|/c_s check was added to the test, and nobody reran them afterwards. With the committed test on f177487 (CPU):

- no diffusion (block removed, `nu_iso` 0, or `nu_iso` and `kappa_iso` both 0, all bit-identical): max|u2|/c_s = 0, max|v|/c_s = **1.93e-7**
- `kappa_iso` 0.0156 only: max|u2|/c_s = 0, max|v|/c_s = 2.20e-3

That |v| is u1, uniform in x2. Per x1 row it rises from 2.6e-12 at the bottom to 3.9e-8 / 1.69e-7 / 1.93e-7 in the top three rows. The cause is the test's initial condition, not the solver: the analytic polytrope is not in the scheme's discrete hydrostatic balance. The u2 finding, and "viscosity alone causes it", stand.

In #265 (head 8c7799f) the test is changed so that its |v| line can pass. The initial condition is projected with `snap::balance_column` (with `dynamics: wb-wall-clamp: true`), the projection that `tests/test_balance_column.cpp` gates. Both lines stay at 1e-12, and the u2 check is unchanged. The same commit adds a CUDA twin of the test, and a user-wall case (`user_wall_keeps_u2_zero`): the stock reflecting condition registered under another name. The user-wall case fails on b1f87a6 (u2 6.96e-5), because that fix found walls by the name `reflecting`. It passes on 81cd351. On a 128x512 resting polytrope behind a user fixed-temperature wall, cycle-1 max|u2|/c_s is 1.15e-5 on b1f87a6 and 0 on 81cd351.


## Issue #266: tests: CPU-only build with a visible GPU runs CUDA test paths (blanket vs targeted skip)

State: closed; opened 2026-10-01; closed 2026-10-02.

**Open question, for the maintainers.** It does not block #265, which carries only its own file-local guard.

A CPU-only Snapy build can see a CUDA-capable PyTorch installation and a GPU. Runtime availability checks then select CUDA paths whose Snapy kernels were not built. This issue separates the build-capability policy from the wall-corner fix in PR #265; it proposes no implementation decision.

## Reproduction and measured main base

- Repository: `chengcli/snapy`; current `origin/main` checked at task start: `5eeb9b6761ae484a98b3993aae18314fc58cf862`.
- This is **not** `e630d916da3237b36c7f7db2349fe68fab9599ee`, the PR #265 baseline used in the earlier controlled comparison.
- CPU-only build: `CUDA=OFF`, `UCX=OFF`, `FULL_TESTS=OFF`, `PNETCDF=OFF`, `BUILD_TESTS=ON`, `BUILD_TESTING=OFF` (dependency tests disabled).
- Python 3.11, Torch 2.10.0+cu128, Kintera **2.5.13**, NVIDIA GeForce RTX 5090 visible as device 0; `torch.cuda.is_available()` is true.
- `CUDA_VISIBLE_DEVICES=0`, `OMP_NUM_THREADS=1`, `BACKEND=gloo`; the same existing CPU build directory and dependency environment were used for the PR baseline, blanket-guard comparison, and this main check. No packages were installed for this check.
- Full `.release` CTest set ran serially after rebuilding main; default timeout 180 seconds, with individual test properties retained.

```sh
cmake -S . -B build-cpu -DCUDA=OFF -DUCX=OFF -DFULL_TESTS=OFF \
  -DPNETCDF=OFF -DBUILD_TESTS=ON -DBUILD_TESTING=OFF
cmake --build build-cpu -j 8
CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=1 BACKEND=gloo \
  ctest --test-dir build-cpu -j 1 --timeout 180 --output-on-failure -R '\.release$'
```

Measured main `.release` result: **28 passed, 24 failed, 0 skipped, 2 disabled, 54 registered**. Counts are from the completed CTest JUnit output and failure-name log.

## Failing executables: main versus the PR baseline

**The earlier 25-failure count is for `e630d91`, not current main.** Main does not contain or register `test_wb_wall_corner.release`; that test was introduced by PR #265. The complete prior 25-name list is retained below, with current-main results distinguished rather than claiming an absent test failed.

| `.release` executable | Current main | PR baseline `e630d91` |
| --- | --- | --- |
| `test_cloud_parent_slots.release` | FAIL | FAIL |
| `test_condensate_conservation.release` | FAIL | FAIL |
| `test_coordinate.release` | FAIL | FAIL |
| `test_cubed_sphere_exchange.release` | FAIL | FAIL |
| `test_diffusion.release` | FAIL | FAIL |
| `test_diffusion_moist.release` | FAIL | FAIL |
| `test_eos.release` | FAIL | FAIL |
| `test_face_floor.release` | FAIL | FAIL |
| `test_fix_vapor_volume.release` | FAIL | FAIL |
| `test_flux_positivity_carry.release` | FAIL | FAIL |
| `test_forcing.release` | FAIL | FAIL |
| `test_hydro_options.release` | FAIL | FAIL |
| `test_hydro_ref_x1.release` | FAIL | FAIL |
| `test_parentless_cloud.release` | FAIL | FAIL |
| `test_parentless_cloud_nb1.release` | FAIL | FAIL |
| `test_radiating_boundary.release` | FAIL | FAIL |
| `test_reconstruct.release` | FAIL | FAIL |
| `test_rectify.release` | FAIL | FAIL |
| `test_riemann.release` | FAIL | FAIL |
| `test_scalar.release` | FAIL | FAIL |
| `test_sedimentation_guards.release` | FAIL | FAIL |
| `test_two_cards_species.release` | FAIL | FAIL |
| `test_wb_wall_corner.release` | not registered (PR-only test) | FAIL |
| `test_weno.release` | FAIL | FAIL |
| `test_weno5_cuda_line.release` | FAIL | FAIL |

A representative failure excerpt, verbatim:

```text
DispatchStub: missing kernel for cuda
```

## Quantified effect of the blanket guard

The controlled comparison on the same machine kept the environment and CMake caches unchanged between `e630d916da3237b36c7f7db2349fe68fab9599ee` and `49879c54e9e32e9bc4f4edbd5da78498b27ff9a7` (`test/265-wb-wall-corner`). The latter is retained as a reference; its repo-wide guards are not proposed for PR #265.

- All **25** failing `.release` executables on the PR baseline became green under `49879c5`; all 53 enabled C++ executables passed there. The current-main failures above are the corresponding non-wall-corner cases. The blanket patch itself was not applied to main in this check.
- In addition to skipping failing CUDA cases, the shared fixture skips **92 GoogleTest cases that already passed** in a CPU-only Snapy build with a GPU visible. Those cases use available Torch/device operations without necessarily requiring Snapy CUDA kernels.
- **102** completed failing GoogleTest cases moved to skipped. The baseline parentless-cloud subprocess also aborted before reaching later existing cases; four of those become skipped and two CPU cases run successfully under the blanket guard.
- `test_rectify.release` is a separate behavior change: it moves **fail → pass by selecting CPU**, not by reporting a skip.
- Thus there were no newly failing tests, but the blanket patch did not satisfy a strict allowance of only fail → skip plus the new passing wall-corner case.

All 92 were also confirmed passing in the current-main CPU-only rerun. They are grouped below; float and double parameterizations count separately.

| Binary | Previously passing cases changed to skipped |
| --- | ---: |
| `test_coordinate.release` | 20 |
| `test_diffusion.release` | 22 |
| `test_diffusion_moist.release` | 4 |
| `test_diffusion_x1_scale.release` | 14 |
| `test_eos.release` | 4 |
| `test_internal_boundary.release` | 2 |
| `test_plm.release` | 10 |
| `test_radiating_boundary.release` | 2 |
| `test_reconstruct.release` | 4 |
| `test_refine.release` | 2 |
| `test_two_cards_species.release` | 4 |
| `test_weno.release` | 4 |
| **Total** | **92** |

## Distinct Python-package failures

The complete CTest suites in the earlier controlled comparison also ran Python tests that imported **installed Snapy 2.10.8 and its installed extension**, rather than either rebuilt checkout. Kintera remained 2.5.13 and `SNAPY_TEST_PYTHONPATH` was unset. The `.release`-only main rerun above does not include these Python tests.

| Commit / build | Passed | Failed | Skipped | Disabled | Registered |
| --- | ---: | ---: | ---: | ---: | ---: |
| `e630d91` CPU | 43 | 47 | 1 | 3 | 94 |
| `e630d91` CUDA | 68 | 22 | 1 | 3 | 94 |
| `49879c5` CPU | 68 | 16 | 7 | 3 | 94 |
| `49879c5` CUDA | 68 | 22 | 1 | 3 | 94 |

Both CUDA runs had the same **22 Python failures**. The blanket CPU configuration skips six CUDA-labelled Python tests, leaving **16** failures. These are distinct from missing native CUDA kernels in the CPU-only C++ executables. Representative Python output, verbatim:

```text
RuntimeError: zeros: Dimension size must be non-negative.
KeyError: 'scalar.positivity_hits'
```

Prepending the CMake build directory and source Python directory to `PYTHONPATH` still selected the installed package: these build directories have no importable checkout-built Python extension. A matching Python package installation or a path to an already-built package is a separate validation concern; no package/environment repair was made during these measurements.

## Why 94 differs from the earlier 98/99 totals

The PR baseline and blanket-guard builds register **94** CTests with `FULL_TESTS=OFF` and `UCX=OFF`; **3** are disabled, leaving 91 enabled. `FULL_TESTS=ON` adds five (`test_mesh_multi_block.release`, `test_exchange_decomp`, `test_shallow_xy_decomp`, `test_shallow_splash_decomp`, `test_shallow_splash_ucx_cuda_decomp`). UCX adds two (`test_parentless_cloud_nb1_mp_gloo`, `test_exchange_ucx`), and CUDA with UCX adds `test_exchange_ucx_cuda`.

- CPU enabled count: **94 − 3 + 5 + 2 = 98**.
- CUDA enabled count: **94 − 3 + 5 + 2 + 1 = 99**.
- Current main registers **93** tests under the measured reduced configuration, one fewer than the PR baseline because its wall-corner test is absent.

This arithmetic explains the broader enabled-test denominators from the registration rules; the original 98/99 logs were unavailable, so their historical configuration and Python package selection have not been independently confirmed. Registered, disabled, skipped, and passed counts should be reported separately.

## Open policy question: blanket or targeted skipping?

- **Blanket build-capability guard:** gives a uniform meaning to `CUDA=OFF`, prevents accidental entry into unbuilt kernels, and is simple to maintain. It also suppresses the 92 currently passing Torch/device cases and broadens the change beyond the tests that fail.
- **Targeted guards:** skip only tests or paths that require Snapy CUDA kernels, retaining working Torch/device coverage in CPU-only builds. They require identifying those dependencies and maintaining that mapping as test bodies change.
- **Automatic device-selection programs:** `test_rectify.release` raises a separate reporting choice between selecting CPU and explicitly skipping a CUDA-specific check.

Which policy should the suite use, and should Torch-only CUDA coverage remain active when Snapy itself is built without CUDA? This issue records the tradeoffs and leaves the decision open.


## Independent confirmation

A separate CPU-only/CUDA build pair on a V100 node (torch 2.6.0+cu124, sm_70), comparing e630d91 with 49879c5 per GoogleTest case, counted the same 92 OK -> SKIPPED cases under the blanket guard (coordinate 20, diffusion 22, diffusion_x1_scale 14, plm 10, eos/weno/reconstruct/diffusion_moist/two_cards_species 4 each, internal_boundary/radiating_boundary/refine 2 each) and 25 C++ binaries turned green.


### Comment 1 (2026-10-01)

Blanket build-capability guard

## Issue #267: eos: the vapor column repair is block-local, so a column split along x1 aborts where one meshblock repairs it

State: closed; opened 2026-10-01; closed 2026-10-02.

`EquationOfStateImpl::apply_conserved_limiter_` repairs a negative vapor along the x1 column with `fix_vapor`. Since #244 the
parentless-cloud pass gathers a column that is split along x1 (`whole_column`, `layout->gather_x1`) and repairs it whole, so its
outcome does not depend on `nb1`. The vapor pass right after it still runs on `cons.index(interior)` only, block by block
(`src/eos/equation_of_state.cpp`, the `call_fix_vapor` over `vapor` near the end of the function, at 5eeb9b6).

**Effect.** With `nb1 > 1`, a block whose own part of the column has a negative vapor total cannot borrow from the block above.
`fix_vapor` returns an error and `TORCH_CHECK` aborts with `Failed to fix vapor mass fractions`, although the whole column has
plenty of vapor and the same state on one meshblock is repaired with the mass kept. When the block-local total is non-negative,
the repair succeeds but redistributes within the block only, so the result still depends on `nb1`.

**Reproducer.** Commit 1db182d5ba565ea86677dcbb326749e6905a5b62 (on 5eeb9b6) adds `tests/test_vapor_column_nb1.cpp`, the vapor
twin of `test_parentless_cloud_nb1`: one 16-cell column, vapor 0.01 in global cells 8..15, zero in 0..7 except cell 3 at -1e-4,
clouds zero. `nb1 = 1`: repaired, mass kept. `nb1 = 2`: throws `Failed to fix vapor mass fractions`. Red on CPU and CUDA, float32
and float64 (V100, torch 2.6).

**Reach.** Only decks that split x1 can hit it; the production decks we run use `nb1 = 1`. In the x1-split moist decks we have
(H2S/CH4 Neptune setup at `nb1 = 2` and `nb1 = 8`), a probe that ran both repairs side by side in every limiter call found no
negative vapor at all: `nb1 = 2` to t = 3000 s (2365 cycles) and `nb1 = 8` to t = 3e4 s (23630 cycles, about 2.8e5 limiter
calls per block), zero negative vapor cells, zero block-local failures, zero differences between the block-local and whole-column
repair. So no run we have reaches it today; the abort is latent until an x1-split deck drives vapor negative near a block seam.

**Suggested direction.** The same gather as #244: repair the vapor of a split column whole on each block and keep each block's part.
No fix is attached; the failing test is commit 1db182d.


## Issue #270: thermo: equilibrate_tp stops at max-iter 5 without converging (9682 times in 500 cycles of examples/uranus.yaml), and the step continues

State: closed; opened 2026-10-02; closed 2026-10-02.

**What.** `examples/uranus.yaml` run for 500 cycles (CPU, one thread, main 5eeb9b6, 20000 interior cells) prints `equilibrate_tp did not converge after 5 iterations.` 9682 times. The run still reaches the cycle limit (t = 2783.8 s) with no redo and no abort. The same build with the #236 change (#269) prints the same count, so this is on main.

**Where.**
- kintera `src/thermo/equilibrate_tp.h:351-354` (4dc613d) prints the warning and returns `2 * 10 + kkt_err` when `iter >= max_iter`.
- `examples/uranus.yaml` sets `max-iter: 5` (L76, L90); the kintera default is 10 (`src/thermo/thermo.hpp:80`).

**Open questions (not measured yet).**
1. Does the caller act on the non-zero return, or does the cell keep the unconverged T and composition?
2. How far from equilibrium are those cells when the loop stops (residual), and does it change the solution compared with a converged step?
3. Does `max-iter: 10` (the default) converge them, and at what cost?

**Next.** A test that pins one such cell (state in, iterations, residual out), then either a fix or a documented tolerance for `max-iter: 5`.


### Comment 1 (2026-10-02)

Fixed by chengcli/kintera#138 (kintera v2.5.16: a solve that converges on its last allowed iteration no longer reports failure; same gating in six host loops) and #273 (examples/uranus.yaml max-iter 5 -> 10). The Uranus example's initialization goes from 9682 `equilibrate_tp did not converge` lines to 0.


## Issue #271: build: cmake_minimum_required(VERSION 3.18) cannot be met (cmake_path needs 3.20; 3.21 crashes)

State: closed; opened 2026-10-02; closed 2026-10-02.

**What.** `CMakeLists.txt:1` declares `cmake_minimum_required(VERSION 3.18)`, but the tree does not configure on 3.18 or 3.21:
- `cmake/modules/FindKintera.cmake:53,55` and `FindHarp.cmake:43,46,47` (and the Torch lookup) use `cmake_path`, which needs CMake 3.20. On 3.18.4 configure stops there.
- On 3.21.4 CMake aborts with `std::out_of_range` inside the Torch lookup.
- 3.22 and later (3.31, 4.3 checked) configure.

**Proposal.** Raise the minimum to the lowest version that configures (3.22 as far as checked), so a too-old CMake fails with a clear version message instead of a crash. Found while reviewing the CMake < 3.22 guard in #268.


## Issue #272: output: after a restart, an output whose dt was changed keeps the old next_time and may never fire

State: closed; opened 2026-10-02; closed 2026-10-02.

**What.** After a restart, an output whose `dt` was changed in the YAML keeps the saved `next_time` from the old schedule, so it may never fire again.

**Reproduction** (straka recipe, the `tests/run_restart_new_output.py` harness, main 4d856fb): base run with a restart output `dt 23` and a NetCDF `prim` output at `dt 1e30` (disabled), to `tlim 40`; resume from t = 23 with `prim` at `dt 7`, to `tlim 75` -> **0 prim frames** (expected t = 30, 37, 44, ...). With the old `dt 1000` changed to 7, the output stays silent until t = 1000.

**Where** (4d856fb):
- `src/output/output_type.cpp:15-21`: `schedule_key()` hashes `file_type`, `dt` and the variables, so a changed `dt` does not match its saved key.
- `src/mesh/meshblock.cpp:1224-1253`: the positional fallback then gives the output its old slot, and `:1259-1261` restore the saved `next_time` verbatim; `:883-887` writes only at `t >= next_time`. Only an output the restart has never seen is re-aligned (`:1262-1265`).
- `dt 0` (the default) writes every cycle (`output_type.cpp:50`), so a very large `dt` is the only way to disable an output, and enabling it later on a restart is exactly the case that fails.
- Related, latent: `src/input/parameter_input.cpp:772-813` still carries the old `ForwardNextTime` with an unsafe int cast at `:800`; it is compiled but has no caller.

**Proposed fix.** On restart, if a restored `next_time` is more than one `dt` ahead of the current time (or `dt` changed), restart the cadence at the current time, as for a new output; `dt <= 0` keeps today's behaviour. A test: the reproduction above must give the expected frames.


## Issue #275: study (parked): well-balanced x1 reconstruction for moist columns, follow-up of #250

State: open; opened 2026-10-02.

**Parked study, follow-up of #250.** Recorded here so it is not lost; nobody is assigned and it is not scheduled.

#250 asked which well-balanced reference density to use for the x1 reconstruction in a moist column. Its finding is in FINDING.md at commit 1e9156b. The default stayed `smooth5`. Moist bubble (BF02), 50 m, D = depth of the final theta_e' minimum: isentrope with vertical WENO `scale: true` 0.0953 K, isentrope 0.137, smooth5 0.258, none 0.264, local_polytrope 0.330, per-cell moist 0.399 K.

Open questions:
1. **No reference meets the BF02 floor.** None of the forms reaches theta_e' <= 0.02 K at <= 100 m. Is the remaining error in the reference, the reconstruction, or the phase-change coupling?
2. **Real-run effect.** Not measured in snapy; a developed-run comparison made outside snapy is not reproduced here.
3. **A moist or isentrope reference option** for snapy's default, only if (2) shows sensitivity.
4. **WENO `scale: true`** cuts the isentrope arm by 30 % but raises the none arm by 28 %, so it acts through the reference; not explained.
5. The eps-ladder runs were parked.

Reopen trigger: a production run that shows sensitivity to the reference choice.


## Issue #276: study (parked): positivity-limited species fluxes on a non-ideal EOS (z != 1) and arm G, follow-up of #236

State: open; opened 2026-10-02.

**Parked study, follow-up of #236 / #269.** Recorded here so it is not lost; nobody is assigned and it is not scheduled.

#269 (arm A) makes a positivity-limited face withhold species mass together with its energy and momentum on the moist-mixture EOS. The carried specific enthalpy is `u_n + z_n R_n T` for a vapour, plus kinetic energy, with `u_n` and `z_n` from kintera. It is verified only for `z = 1`: kintera's `func2` registry was empty as of kintera 2.5.15, so `eval_czh` returns 1 and no non-ideal case is reachable.

Not done:
1. **`z != 1` (non-ideal EOS).** When kintera gains a non-ideal compressibility model, the enthalpy carry and the pressure share must be re-checked: the conservation oracles of #236 (energy, momentum, column ratios against the unlimited flux) on cards with `z != 1`, and a mutation test that turns them red if `z_n` is dropped.
2. **Arm G.** Its positivity proof needs CFL <= 0.5, and the vertical direction is implicit, so it does not apply as written.
3. **Dry IDN minima below `1e-10` at `dt = 1`.** Outside #236; unmodified main shows the same minima.

Reopen trigger: a non-ideal `czh` model in kintera, or a production case that needs arm G.


## Issue #277: restart: a resumed run rewrites its last outputs, including its source restart file, and the restart index does not advance

State: open; opened 2026-10-03.

**What.** A restart file stores each output's `file_number` and `next_time` as they were *before* the write that produced it was counted. On resume, the restored state says that output is still due, so the first `make_outputs` call rewrites the last output of each type, including the restart file the run was started from, and the restart index does not advance.

**Reproduction** (main e80b5c1, CPU, 2 ranks): `examples/straka.yaml` with `tlim 300` (netcdf output) writes `straka.00000.restart`, `straka.00001.restart` and `straka.final.restart`; inside 00001, `file_number` is 1, `next_time` is 300, `last_time` is 300.012. Resume in the same directory with `-r straka.00001.restart` and `nlim` one step past it: `straka.00001.restart` is rewritten before the first step (mtime changes, sha256 unchanged because the state is the restored one), no `straka.00002.restart` is written, and `straka.final.restart` is replaced. Resuming into a fresh directory leaves the source file alone but still writes index 00001 again.

**Where** (e80b5c1):
- `src/output/restart.cpp:47-50` saves `out->file_number` and `out->next_time` while the restart output itself is being written.
- `src/mesh/meshblock.cpp:883-887` advances `next_time` and `file_number` only after `write_output_file` returns, so the saved values are the pre-write ones.
- `src/mesh/meshblock.cpp:1257` restores the saved `file_number`; the restored `next_time` (300) is behind the restored time (300.012), so the output is due at once (the #272 clamp only handles a `next_time` more than one `dt` ahead).
- `examples/straka.cpp:137` calls `make_outputs` right after `initialize`, before the time loop.

**Impact.** No data is lost: the rewrite reproduces the same bytes. Each resume does one redundant write of every due output, and an in-place resume rewrites its only source restart file; an interruption during that write could leave it damaged.

**Possible fix** (not done): store the post-write `file_number + 1` and `next_time + dt` for the output being written, or skip outputs whose restored `next_time <= last_time` on the first call after a restart. A test: resume in place, assert the source restart file is untouched and the next restart index is 00002.

Recorded so it is not lost; not scheduled.


## Issue #278: Post-2026-09-20 audit: numerical correctness and duplicated logic

State: closed; opened 2026-10-03; closed 2026-10-03.

## Purpose and scope

This is a request for cross-review of Snapy changes since 2026-09-20: five reproduced correctness findings and six maintenance/simplification items. Reviewed main: `f20b0a098ef4994ed9d48d80a167d473d9d41ceb` (2026-10-02).

The maintenance items are proposals, not claims of numerical failure. No simplification has been implemented or validated as equivalent yet. Please challenge the reproductions, identify intended behavior, and suggest smaller fixes before implementation. Item numbers below are stable review IDs.

## Consolidated review table

| ID | Priority / status | Origin and source | Finding / evidence | Proposed approach and acceptance checks |
|---|---|---|---|---|
| 1 | P2 / reproduced | #216; [diffusion.cpp:595-599](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/forcing/diffusion.cpp#L595-L599) | Dynamic conduction bounds its timestep with dry reference cv rather than local mixture cv. An accepted RK1 step amplified a temperature perturbation from 0.1003 to 0.2333. | Bound the actual local thermal diffusivity kappa/(rho*cv_mix). Check pure-dry and varying-mixture cases, conduction decay and combined viscosity/conduction. |
| 2 | P2 / reproduced | #220; [meshblock.cpp:713-715](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/mesh/meshblock.cpp#L713-L715) | The scalar upper-bound guarantee can be invalidated by the later dry-mass forcing correction, which uses the old mixing ratio. A full accepted RK1 step with upper_bound=1 returned r=1.02. | Account for transport and mass-source contributions in the scalar/complement budget. Check bounds and conservation together, including removal/addition and multistage integration; avoid a nonconservative final clamp. |
| 3 | P2 / reproduced | #219; [relax_bot_temp.cpp:85-102](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/forcing/relax_bot_temp.cpp#L85-L102) | at-face relaxation hardcodes uniform-grid extrapolation and gain. A linear temperature profile already satisfying the target face temperature received a spurious 3.33 K cell increment on a stretched grid. | Derive weights and gain from actual face/center coordinates. Check uniform and stretched grids, zero forcing at the target and the intended relaxation response. |
| 4 | P3 / reproduced, narrow trigger | #212; [output_type.cpp:15-20](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/output/output_type.cpp#L15-L20) | std::to_string(dt) loses cadence precision when constructing schedule keys. A real restart with close cadences and reordered outputs produced extra/missing frames. | Preserve enough floating-point precision in schedule identity, with an explicit checkpoint-compatibility strategy. Test close cadences, reordering and legacy checkpoints. Distinct from the pre-write counter issue in #277; coordinate overlapping restart tests. |
| 5 | P3 / reproduced | #221; [balance_column.cpp:65-86](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/hydro/balance_column.cpp#L65-L86) | The last allowed update is not followed by a residual check. A case converging after 19 updates fails at max_iter=19 but succeeds at max_iter=20, reporting 19 updates. | Check convergence of the final returned state. Cover initially converged, exactly-at-limit and truly unconverged cases. |
| 6 | P3 / maintenance, observed divergence | #217; [Mesh diagnostics](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/mesh/mesh.cpp#L386-L459), [MeshBlock diagnostics](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/mesh/meshblock.cpp#L946-L1020) | Cycle diagnostics have two implementations that have diverged: MeshBlock reports KE, PE and limiter diagnostics absent from the Mesh path. | Share diagnostic calculation while retaining correct local-block and process aggregation. Check single-block, multiple blocks per process, and multi-process totals without double counting. |
| 7 | P3 / avoidable duplication | #211/#217/#227, common helper added by #242; [HydroOptions](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/hydro/hydro_options.cpp#L44-L99), [EOS](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/eos/equation_of_state.cpp#L48-L69) | dynamics, forcing and EOS hand-roll whitelist iteration and error-list formatting already supported by check_keys. | Reuse the existing helper, retaining the dedicated fric-heat removal error, Kintera keys and useful error paths. Check all accepted keys, misspellings and malformed inputs. |
| 8 | P3 / simplification proposal | #244/#268; [EOS column repair](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/eos/equation_of_state.cpp#L302-L362) | Cloud and vapor paths duplicate gather, slicing, TensorIterator setup, repair and copyback. Estimated reduction: 20-30 lines. | Extract a local helper but preserve distinct failure policies: cloud repair may clamp after failure; vapor must check failure before copyback. Keep both collective calls and their order. Check varying volumes, x1 decomposition, conservation and unrepairable states; no local-negative-only communication shortcut. |
| 9 | P3 / simplification proposal | #223/#226/#248; [Mesh redo](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/mesh/mesh.cpp#L461-L497), [MeshBlock redo](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/mesh/meshblock.cpp#L1174-L1191) | Five redo causes are separately collected, reduced and bit-packed in two paths. Estimated reduction: 15-25 lines. | Share local-cause collection and reduction/packing. Preserve floor-before-limiter ordering, single consumption of saturation-failure counters, Mesh signal handling and one global decision. Check each cause and synchronized rollback of every block. |
| 10 | P3 / simplification proposal | #221; [six-face reference stencil](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/src/hydro/hydro_ref_x1_impl.h#L110-L173) | Several branches repeat a six-face weighted sum and the same bounds/acceptance logic; this period added the wall branches. Estimated reduction: 20-30 lines. | Extract only the common CPU/CUDA evaluator. Preserve summation order, branch precedence and thin/fits/wall guards. Check float/double, wall corners, thin grids, balance_column and decomposition parity. |
| 11 | P3 / simplification proposal | #212/#273, coordinate with #274; [CTest registrations](https://github.com/chengcli/snapy/blob/f20b0a098ef4994ed9d48d80a167d473d9d41ceb/tests/CMakeLists.txt#L333-L421) | Restart CTest registrations repeat the same command/options/properties. #274 reduces duplication but still has five equivalent registration blocks, about 74 lines. | Use a name list and foreach, about 15 lines; retain the multiblock registration separately because its properties differ. Compare test names, commands, working directories, timeout, skip code and labels, then execute representative tests. |

Line reductions are estimates, not a target or a measured patch result.

## Reproduction details for the five correctness items

1. **Dynamic conduction:** ideal-moist H2/H2O mixture, dry cv_R=2.5, vapor cv_R=3.5, water-vapor mass fraction 0.9, T approximately 1000 K, rho=1, no cloud, limiter disabled; 16 periodic x1 cells, dx=1, dynamic kappa=1e8, nu=0, RK1, CFL=0.4. The native values were cv_dry=10310.5902778 and cv_mix=2484.87801196. The block selected dt=2.06211805556e-5, while the forward-Euler heat bound was 1.24243900598e-5. max|T-1000| grew 0.1003149 -> 0.2333441 and check_redo returned 0. A mixture-cv timestep control reduced the perturbation to 0.0203149.
2. **Scalar/source interaction:** target cell rho=1, scalar r=0.9 with upstream r=1, velocity=1000 and pressure=1e5; dt=0.0006 is below the block's dtmax=0.0006549428. Advection gives scalar mass 0.96. A user stage forcing removes half of the target conserved hydro state, including momentum and energy, without an explicit scalar_ds. The automatic correction removes 0.45 using old r=0.9, giving rho=0.5, scalar mass=0.51, r=1.02; check_redo=0. This is a complete RK1 step, not just an intermediate flux calculation.
3. **Face relaxation:** bottom face x=0, first cell widths 1 and 3, centers 0.5 and 2.5, and T(x)=100+10x. The real face temperature is 100 K, but 1.5*105-0.5*125=95 K. With target=100, dt=tau=1, the native forcing adds 3.333333 K. A consistent uniform-grid control gives zero. This is an isolated forcing-operator check with consistent thermodynamic state and updated coordinate metrics.
4. **Schedule collision:** netCDF outputs with identical variables and dt A=4e-7, B=4.9e-7 produce the same decimal cadence string. In a real CPU Straka restart at t=6.224594731e-7, saved next times are A=8e-7 and B=9.8e-7. Reorder to B,A and resume through t=1.374598e-6. B actually writes at approximately 8.0401e-7 and 1.29679e-6; A only at 9.85561e-7. Expected cadence counts in this window are B once, A twice. The current cadence clamp does not repair the mismatch: both wrong saved times remain within current_time+dt. The domain was scaled down to make CFL steps small enough to resolve these cadences.
5. **Iteration limit:** an initially marched isothermal column with 64 cells, dz=1000, g=10, R=287 and T=300 reaches residual 4.31893318511e-11 after 19 updates, below rtol=1e-10. max_iter=19 throws using the preceding residual 1.10574e-10; max_iter=20 succeeds and reports 19 updates.

The native CPU checks reused Snapy 2.10.37 built from 4d856fb, with the relevant defect paths checked against the reviewed main. Later changes, including the restart cadence clamp, were inspected for applicability. This is not a claim that a fresh full CPU/CUDA/multi-process suite passed at f20b0a098.

## Cross-review and implementation sequence

- Prioritize items 1-3. Items 7, 8 and 11 offer the clearest duplication reduction; scrutinize numerical/parallel semantics for 9 and 10 before changing them.
- For each item, please state confirm / challenge / intended behavior, the exact SHA, and a reproducer or source-based reason. Simpler alternatives are welcome.
- Consolidate agreed scope, implement with focused failing/passing regression checks, then run the relevant broader tests. Keep correctness fixes and cleanup in separate reviewable commits before opening a PR.
- Coordinate item 11 with the open #274 rather than creating conflicting cleanup. #277 is a distinct restart-counter issue. The moist-mixture carry gap fixed by #269 is excluded.
- No established performance defect is claimed for whole-column gathering without a benchmark. Preserve necessary profile-mutation checks, restart compatibility branches and communication synchronization.


## Issue #280: well-balance (parked): a column at rest is not at rest on a stretched (non-uniform) x1 grid

State: open; opened 2026-10-03.

**Parked: recorded so it is not lost; not scheduled.**

**What.** A column at rest on a stretched (non-uniform) x1 grid does not stay at rest. Measured outside snapy (not reproduced here), not yet in snapy.

**snapy.** Expected to have the same problem; not measured. The hydrostatic scan in `src/hydro/hydro_ref_x1_impl.h` uses `dx1f`, but the face interpolation of the x1 reference uses fixed rational coefficients (around `hydro_ref_x1_impl.h:120-130`), i.e. uniform spacing. Whether the WENO5/cp5 reconstruction also assumes uniform spacing is not checked.

**Test to add when this is picked up.** A resting adiabat and an isothermal column on a stretched x1 grid (e.g. `x1rat 1.05`), max|v| after a fixed time vs nx1 = 32/64/128. The correct answer is round-off at every resolution.


## Issue #281: well-balance: make the x1 reference an explicit choice (key + warning or required) instead of a silent smooth5 default

State: open; opened 2026-10-03.

**What.** The x1 well-balanced reference is fixed: `src/hydro/hydro_ref_x1_impl.h` always uses rho/p smoothed by a clamped 5-point binomial (`smooth5`, kept as the default by #250). There is no YAML key to choose another form and no message saying which one a run used, so a project never checks whether it fits its case.

**Why one default is not safe.** The best reference depends on the case:
- Moist bubble (Bryan & Fritsch 2002), #250 / #275: an isentrope reference is better (D = 0.137 K vs 0.258 K for smooth5 at 50 m).

**Proposal.**
1. A dynamics key for the x1 reference (e.g. `smooth5`, `isentrope`, `none`), and either require it on a cold start or print a clear warning when it is unset, naming the form being used.
2. A small picker: cheap 1-D rest and gravity-wave probes that run each form on a project's own column and recommend one.

Related: #275 (moist well-balanced study), #250.


## Issue #283: Implicit solver: face-form gravity work is added outside the implicit operator; a tall rest column blows up at large dt

State: closed; opened 2026-10-06; closed 2026-10-08.

## Summary

The implicit solver linearises the cell-centred gravity work, but the energy equation also receives two face-form gravity-work terms that are added after the implicit solve, outside the operator. At a large implicit time step this mismatch makes a tall isothermal column at rest blow up. With both face terms removed, the same column stays at rest.

- **What the matrix linearises.** Both VIC assemblies add the gravity coupling `Phi` on (ρw ← ρ) and (E ← ρw). The energy row is therefore the linearised cell work, dE/dt += g ρw.
  - vic-partial: [vic_assemble_partial_impl.h#L40-L42](https://github.com/chengcli/snapy/blob/531579c96d3cc4778f124ac33475fde0420cf102/src/implicit/vic_assemble_partial_impl.h#L40-L42) and [#L101-L103](https://github.com/chengcli/snapy/blob/531579c96d3cc4778f124ac33475fde0420cf102/src/implicit/vic_assemble_partial_impl.h#L101-L103)
  - vic-full: [vic_assemble_full_impl.h#L32-L34](https://github.com/chengcli/snapy/blob/531579c96d3cc4778f124ac33475fde0420cf102/src/implicit/vic_assemble_full_impl.h#L32-L34)
- **The solver's input is consistent with that.** The explicit tendency handed to the solve contains the same cell work (the comment at [hydro_forward.cpp#L424-L430](https://github.com/chengcli/snapy/blob/531579c96d3cc4778f124ac33475fde0420cf102/src/hydro/hydro_forward.cpp#L424-L430)).
- **What is applied after the solve, without linearisation:**
  1. The explicit correction from cell work to face-mass-flux work, [hydro_forward.cpp#L431-L498](https://github.com/chengcli/snapy/blob/531579c96d3cc4778f124ac33475fde0420cf102/src/hydro/hydro_forward.cpp#L431-L498), applied at [#L554-L558](https://github.com/chengcli/snapy/blob/531579c96d3cc4778f124ac33475fde0420cf102/src/hydro/hydro_forward.cpp#L554-L558).
  2. The swap from #202: it replaces the matrix's implicit work dt·g·δ(ρw) by the work of the mass the VIC redistribution moved through each face, [implicit_hydro.cpp#L252-L271](https://github.com/chengcli/snapy/blob/531579c96d3cc4778f124ac33475fde0420cf102/src/implicit/implicit_hydro.cpp#L252-L271).

## Evidence (main 531579c, CPU)

1. **The operator never sees the face terms.** I took a central-difference Jacobian of the energy row of the solver's input (one step, 16-cell moving column, vic-partial). It is identical, to the last bit, with term 1 on or off.
2. **Size of the swap (term 2).** I measured it from the solver's own buffers on the same moving column. The swap minus the matrix's work is 0.5 %, 3.7 % and 20 % of the step's energy increment at acoustic Courant 1, 10 and 66.
3. **Tall rest column.** The setup:
   - 45 cells of 29.9 km (11.3 scale heights); g = 23.1 m/s², T = 786 K, γ = 1.403461, Rd = 3515, p_bot = 100 bar.
   - 8 periodic columns in x2, reflecting walls.
   - rk3, weno5, lmars, implicit-scheme 9.
   - Discretely balanced with `balance_column`, no perturbation, 10 days.

   The face terms were switched off with local instrumentation only, not part of this report.

| arm | dt 997 s (acoustic Courant 65.6) | dt 100 s (Courant 6.6) |
|---|---|---|
| main (both face terms) | blows up: max\|w\| 2e-6 m/s at step 10, ×2.7 per step, ~1e24 by day 1 | stays at rest: max\|w\| 4.6e-9 → 9e-13 |
| both face terms off (pure cell work) | stays at rest 10 d: 3.8e-9 on day 1, 6e-13 afterwards | stays at rest: 4.5e-9 → 8e-13 |
| swap (2) off, correction (1) on | non-finite at 0.97 d | — |
| swap (2) on, correction (1) off | blows up: 0.13 m/s at step 12 | — |

Either face term alone is enough to destabilise the large step. The small step is fine either way.

## Reproduce

Failing test (`tests/test_implicit_gravity_tall_column.py`, registered as a ctest). It runs 40 steps per rung; each rung must stay finite with max|w| < 1e-7 m/s. It takes a few seconds on CPU.

```
ctest -R test_implicit_gravity_tall_column --output-on-failure
# or: python tests/test_implicit_gravity_tall_column.py
large step dt= 997.0 s  acoustic Courant  65.6  ...  step 1 4.696e-09  step 10 2.061e-06  step 20 5.206e-02  step 30 2.969e+24
control    dt= 100.0 s  acoustic Courant   6.6  ...  step 1 4.556e-09  step 10 1.161e-10  step 20 8.676e-12  step 40 3.665e-13
control    PASS: max|w| = 4.556e-09 m/s over 40 steps (tol 1e-07)
FAIL large step (dt 997 s): max|w| = 8.908e+24 m/s over 40 steps (tol 1e-07)
```

With both face terms disabled the same test passes: large step max|w| 3.8e-9, control 4.5e-9.

## Fix directions (open; not chosen)

- **Put the face work inside the implicit operator.** Linearise g·(face mass flux) in the energy row. This couples E_i to its neighbours through the Riemann mass flux (including its pressure-jump term), and makes the #202 swap the operator's own term rather than a post-hoc replacement.
- **Use the cell work under implicit,** which is what the matrix already linearises. Trade-off: the cell form is consistent with kinetic energy (momentum and energy see the same ρg), but total energy plus potential energy is no longer conserved to round-off, as it is with the face form.
- Either way, the test above should pass at both rungs.

## Files

src/implicit/vic_assemble_partial_impl.h, src/implicit/vic_assemble_full_impl.h, src/implicit/implicit_hydro.cpp, src/hydro/hydro_forward.cpp


### Comment 1 (2026-10-07)

## Proposed fix design

The design below is offered as the spec for the fix PR; the claimant may of course improve on it.

1. **Default: cell-form gravity work.** The energy equation gets the x1 gravity work at cell centres, `dE_i = -g rho_i v_i dt`. This is the term the implicit matrix already linearises ([vic_assemble_partial_impl.h#L40-L42](https://github.com/chengcli/snapy/blob/531579c96d3cc4778f124ac33475fde0420cf102/src/implicit/vic_assemble_partial_impl.h#L40-L42)). On the default path this removes both face terms:
   - the explicit face correction ([hydro_forward.cpp#L431-L498](https://github.com/chengcli/snapy/blob/531579c96d3cc4778f124ac33475fde0420cf102/src/hydro/hydro_forward.cpp#L431-L498), applied at [#L554-L558](https://github.com/chengcli/snapy/blob/531579c96d3cc4778f124ac33475fde0420cf102/src/hydro/hydro_forward.cpp#L554-L558));
   - the implicit swap ([implicit_hydro.cpp#L252-L271](https://github.com/chengcli/snapy/blob/531579c96d3cc4778f124ac33475fde0420cf102/src/implicit/implicit_hydro.cpp#L252-L271)).
2. **Exception.** Mass moved through a face by sedimentation or by the positivity limiter (the sedimentation flux and the limiter's correction to the face mass flux) keeps its face-form gravity booking.
3. **Global energy fixer, on by default with the cell form.** The cell form keeps momentum and energy consistent (both see the same `rho g`), but it no longer conserves total energy plus potential energy to round-off. The fixer restores that. Once per step, after the last mass change and before the time-step and diagnostic computation:
   - Compute the defect `D = sum_i Phi_i * delta(rho_i) * V_i + (the gravity work the step added to E)`, i.e. the change in potential energy plus the booked work. Exact conservation would make D zero.
   - Add `-D` back as heat, uniformly per unit mass, into the internal energy: `delta(E_i) = -D * rho_i / sum_j(rho_j V_j)`. This costs one global reduction per step. It is the same idea as FV3's `consv_te`.
   - Write D (or the applied heating rate) to the history output, so the fix is visible.
   - Refuse to run with the fixer on when mass can cross the x1 boundaries: a non-reflecting or periodic x1 boundary, or a sedimentation wall that is not sealed. There D also contains a real boundary flux, and spreading it as heat would be wrong.
4. **One alternative, as an option:** face-form work, but with cell-form work in the two wall-adjacent cells. Under the implicit solver it must print a warning that points to this issue, because of the instability shown above.

### Acceptance

- The failing test from the issue body passes at both rungs.
- In a closed box, total energy plus potential energy is conserved to round-off with the fixer on.
- Columns at rest stay at rest.
- Dry low-Mach convection (onset and convective flux) is unchanged within its run-to-run error.


## Issue #286: Coarse implicit columns amplify gravity-fixer heat and accept inaccurate states

State: open; opened 2026-10-07.

Follow-up from #283 and #285. No additional scan is needed.

At #285 head `8710d021fbdf74cf04b4d88bacd41e3850a046e0`, a coarse 40H column can accept inaccurate states while remaining finite, positive and energy-conserving.

Setup: the discretely balanced isothermal column from `tests/test_implicit_face_work_operator.py`, expanded to 40 pressure scale heights; 50 cells (dz/H=0.8), rk3, WENO5, LMARS, scheme 9, reflecting x1 walls, eight periodic x2 columns. Start at rest. Each step begins at nominal acoustic Courant 657 (dt=31923.98807969932 s); use native `check_redo`, halve dt on a positive retry, and stop on a negative return.

Source-build results:

| arm | accepted steps | top density / initial |
|---|---:|---:|
| base 531e839, cell + fixer, CPU | 12, then max-redo stop | 0.6702868649 |
| head, cell + fixer, CPU | 300, no stop | 4.4945628085 |
| head, cell + fixer, CUDA | 300, no stop | 4.4962308824 |
| head, cell, fixer off, CPU | 300, no stop | 0.9916282589 |

This cell+fixer no-stop is a change from base. The CPU head's top temperature reaches 1439.769095 K while E+PE drift is -1.754e-14.

Cause isolation: rollback restores the conserved input exactly. Keeping the fixer computation but removing only its applied heat gives the same logged state metrics and retry sequence as fixer-off at every step. The maximum applied heat is 2.622809084e-4 J/kg (~3.0105e-8 K per step), far smaller than the resulting temperature change. This isolates thermal feedback; the precise amplification mechanism is not yet established.

Face mode has a related accuracy problem: coarse runs can accept hundreds of m/s before retry or termination. Some base runs do this too. Native timestep selection helps the cell control but does not eliminate the coarse face error. Positivity/repair checks do not measure solution accuracy.

Next:
- Isolate how the stiff column solve amplifies the small thermal correction; compare fixer on/off and heat-removal controls over equal physical times.
- Investigate treating the global thermal correction consistently with the implicit solve.
- Design an accuracy criterion that can request retry or stop before large rest-state errors are accepted.
- Keep the original #283 regression and Cartesian/curved-grid energy budgets; check CPU/CUDA, grid/dt refinement and decomposition.

Do not replace this with a handpicked Courant or density-change cutoff. #285 fixes the operator mismatch, but does not resolve this coarse-column feedback.


### Comment 1 (2026-10-09)

Decision for this round: this is a documented limit, not a fix.

Regime: the failure needs a coarse column, dz/H around 0.8, together with an acoustic Courant number around 657. It does not appear at either condition alone.

Measured clean range on main 117e449a620bd7fd50abe19239ab660a56d5d4cb (CPU, cell form with the global E+PE fixer): clean through dz/Hp 1.0 at Courant 83, and an 11 H isothermal column at rest clean to Courant about 2700 (the sealed-wall refusal fires from about 2750).

No current production configuration reaches the failing regime, so the investigation stops here. Reopen if one does.


## Issue #287: gravity-work: face inside the implicit operator on curved grids (cubed-sphere / spherical x1)

State: open; opened 2026-10-08.

## Summary

`gravity-work: face` inside the implicit operator works only on Cartesian grids (#285). On curved grids (cubed-sphere, spherical x1 = r), an implicit run with `gravity-work: face` still books the face work outside the operator. The implicit matrix linearises the cell work instead, so the two disagree. On a tall column this is the setup that blew up at vertical acoustic Courant ~66 (#283). As a result, `face` cannot be used in the configuration our production GCMs run: cubed-sphere, implicit scheme 9, vertical acoustic Courant ~20 to ~250. This issue records what is needed to close that gap.

## Where the restriction is (main 117e449)

- `src/hydro/hydro.cpp:183-187`: `face_work_in_operator()` requires `pcoord->options->type() == "cartesian"`.
- `src/hydro/hydro.cpp:84-91`: otherwise an implicit run with `gravity-work: face` warns, and the face work stays outside the operator.
- `src/hydro/hydro_forward.cpp:626-646`: the outside-operator path adds `gravity_energy_correction` (face minus cell work) to `du[IPR]` after the implicit solve.
- `src/implicit/implicit_hydro.cpp:232-233, 317-332`: the face-work swap in the energy row ("cartesian x1").
- `src/implicit/vic_assemble_full_impl.h:103` and `vic_assemble_partial_impl.h:124`: the weight `A (x1f - x1v) / V` is taken as 1/2 at both faces, which is true only in Cartesian x1.

## What a curved-grid version needs (to be worked out)

1. In the energy row, use the face mass flux with the curvilinear geometry: the face areas A(r_{i±1/2}), the cell volume V_i and the centre-to-face potential differences Φ(r_f) − Φ(r_c). Do not assume the factor 1/2. The same applies to the mass-diffusion work booked in cell mode (#285) where it uses that weight.
2. Do the same in both VIC assemblies (full and partial), and in the Jacobian of the energy row.
3. Keep the discrete E+PE telescoping identity exact with these weights. Show this as a derivation in the PR, not only as a test.
4. Lift the `cartesian` check in `face_work_in_operator()` once 1-3 pass.

## Acceptance tests (proposed)

1. E+PE closure in face mode, fixer off, on a spherical/cubed-sphere column, explicit and scheme 9: per-step change of total E+PE at round-off (as in `tests/test_gravity_work_fixer.py` for Cartesian).
2. Rest state: a hydrostatic spherical column stays at rest (well-balance unchanged).
3. `tests/test_implicit_gravity_tall_column.py` extended to a spherical/cubed-sphere column. It must survive at the Courant numbers where the Cartesian column does, up to ~250 (the real-deck range).
4. Finite-difference check of the energy-row Jacobian on a curved column.
5. `gravity-work: cell` is bitwise unchanged on all grids.

## Context

The cell-vs-face physics comparison is running on Cartesian decks now (convective onset against a linear eigen-solver, from Mach ~0.03 down to ~1e-3, several resolutions, explicit and implicit). Its outcome decides how urgent this is. If face is better in any regime that our decks reach, the production path needs this issue fixed. If cell is better everywhere, this stays a completeness item. Either way, the analysis of the curved-grid weights is worth doing now, so that it is ready.


## Issue #289: Low-Mach convective onset too slow: the horizontal energy flux misses an O(dz^2) covariance term

State: open; opened 2026-10-09.

## Summary

At low Mach number, snapy's growth rate of convective onset is too slow. The error is the same for both gravity-work forms (`cell` and `face`) and scales as

rel_err = sigma_snapy / sigma_exact - 1 ≈ -C / (eps nz²),  C ≈ 0.15-0.18,

where eps = ∇ - ∇_ad is the background superadiabatic excess and nz the number of vertical cells. Our production decks (ice giants, Mach 1e-4 to 1e-3) sit at eps nz² << 1, so weak convection there is dominated by this error, whichever form is used. This matters more than the cell/face choice.

A candidate cause has been derived: the horizontal (x2, x3) energy flux misses an O(dz²) covariance term. An exploratory implementation removes most of the error. Independent verification is running. This issue records the derivation, the evidence so far and the open work, so that the work can proceed in parallel.

## Measurement (main 117e449)

Deck: 2-D Cartesian, compressible ideal gas (gamma 1.4). Linear background T0 = 1 - beta z in a box one bottom pressure scale height deep (rho_b/rho_t ≈ 2.32), periodic x with k = pi/sqrt(2). Walls are stress-free, impermeable and fixed-T. Constant mu, K = Cp mu, Pr 1, Ra = 50 Ra_c(k, eps). Explicit RK3, WENO5, LMARS, vertical acoustic Courant 0.40. The exact rate comes from a Chebyshev eigenvalue solver: it reproduces the reference Ra_c(k) = 1268.5968053249962 to 1e-12, and sigma(eps 1e-3) = 0.01669758006.

Relative error of the growth rate (cell / face). Two independent decks were built by different people, with their own eigen-solvers.

| eps | nz | eps nz² | deck A | deck B |
|---|---|---|---|---|
| 1e-2 | 16 | 2.56 | -6.86 % / -6.13 % | -6.9 % / -6.1 % |
| 1e-3 | 32 | 1.02 | -16.0 % / -14.9 % | -16.1 % / -15.0 % |
| 2.56e-4 | 64 | 1.05 | | -14.9 % / -14.3 % |
| 1e-4 | 64 | 0.41 | | -43.8 % / -41.3 % |
| 1e-4 | 32 | 0.10 | no clean growth | |

The error is second order in nz and collapses on eps nz². The discrete background is exact at t = 0, so the error comes from the dynamics. Scaling the LMARS dissipation terms (the acoustic term in ubar ×0 and ×2; the pressure term in pbar ×0 and ×0.5) leaves the error unchanged (-15.857 % in every case).

## Candidate cause: the x1 average of the horizontal energy flux

In 2-D, an x2 face spans one cell height dz. The finite-volume flux through it is the x1 average over the face of the point flux gamma/(gamma-1) p u. The code instead evaluates the flux from x1-averaged states: gamma/(gamma-1) p̄ (m̄/ρ̄). Expanding p, m and rho to second order about the face centre, the difference is

<f> - f(p̄, m̄, ρ̄) = gamma/(gamma-1) (dz²/12) u_z (p_z - p rho_z / rho) = gamma/(gamma-1) (dz²/12) p [ln(p/rho)]_z u_z.

The u rho_z and u p_z cross terms cancel identically. So

Delta F = gamma/(gamma-1) (dz²/12) p (ln T)_z u_z.

It depends only on the local state. It is zero at rest and zero for an isothermal state. In a stratified background, (ln T0)_z = O(1) (it is set by beta, not by eps), so Delta F is linear in the perturbation. Its divergence acts as a spurious stable stratification:

eps_spur = -(beta m² / 12) dz²,

where m is the vertical wavenumber of the mode. This is about -0.24 / nz² for the first mode. Adding eps_spur to the eigen-solver predicts face at eps 1e-3, nz 32 as -14.60 %; the measured value is -14.75 %.

Evidence so far (exploratory, not yet independently reproduced):
- On an exactly adiabatic background (eps = 0), the one-step tendency of the eigenmode gives eps_spur nz² = -0.240 (nz 64). The formula, evaluated on the eigenfunction, gives -0.241. This check does not involve the growth fits.
- Adding Delta F to the x2 energy flux:

| case | cell | face |
|---|---|---|
| eps 1e-3, nz 32 | -15.9 % → -1.0 % | -14.8 % → -0.06 % |
| eps 1e-4, nz 64 | -43.6 % → -1.07 % | → +0.33 % |
| eps 1e-4, nz 32 | -91 % → -10.7 % | → +1.2 % |

With the term in place, `face` is about 10x closer to the exact rate than `cell`. So the cell/face comparison must be redone with the fix.

## Open work (can run in parallel)

1. **Independent implementation and verification on Cartesian** (in progress). Covers: the eps = 0 tendency at nz 16/32/64; growth with and without the fix, cell and face, at eps nz² ≈ 1 and 0.4, nz up to 128; hydrostatic rest (max |u| after 1000 steps); E+PE per step at round-off with walls closed (Delta F is a flux, so it should telescope); strong convection eps 0.02 nz 16/32/64 not made worse.
2. **x3 direction and curved grids.** The same term on x3 faces. On a spherical-x1 or cubed-sphere grid, the face average over r carries the face metric (the face area varies with r across the face), which adds O(dr²) terms. Derive the curvilinear form, implement it, and test it on a spherical column at eps 0 (the tendency) and in a short cubed-sphere run.
3. **Tracer fluxes.** By the same expansion, the x2 flux of a tracer q has <m q> - m̄ q̄ = (dz²/12) m_z q_z. With a background vapour gradient q0_z, this is also linear in the perturbation. Does it bias moist (compositional) buoyancy in the same way? Analysis first, then one moist test.
4. **Implicit path (scheme 9) and CUDA.** The vertical implicit solve does not form the x2/x3 fluxes, so the term should apply unchanged. Confirm this on one implicit deck and on CUDA.
5. **Completeness.** Is Delta F the whole O(dz²) error, or one piece of it? After the fix, cell keeps about -1 % where face goes to about 0. Is the residual the cell gravity-work form, and is it O(dz²) or higher order?
6. **Effect on turbulent (ILES) statistics.** A short check of convective flux and KE with and without the term on a strongly convecting deck.

## Acceptance (proposed)

- eps = 0 tendency: eps_spur nz² goes from about -0.24 to below 0.01 at nz 16/32/64.
- Onset at eps nz² ≈ 1: |rel_err| drops by at least 10x, and the collapse on eps nz² disappears.
- Rest state, E+PE closure and strong convection unchanged within round-off or the stated tolerance.
- The default path is bitwise unchanged until the term is enabled; then it is enabled by default after review.


## Issue #290: Cleanup after #288: distinguish and propagate singular LU failures

State: closed; opened 2026-10-09; closed 2026-10-09.

Implementation of the requested cleanup, stacked on #288 head `070ba601ef8cc225cd294d320e4b7554e358b1aa`. Independent verification is pending; no independent sign-off is claimed here. #289 implementation is excluded.

Reproduction on that head (GCC 11.5.0, `c++ -std=c++17 -O3`, Eigen 3.4.0): call `ludcmp` on identity, identity with row 0 zeroed, and identity with row 1 copied from row 0; initialize the permutation indices to identity. Invert the third result with `luminv` as the current callers do. For both N=3 and N=5:

```
identity_return=1 zero_row_return=1 dependent_return=1 dependent_inverse_finite=0
```

A successful even-parity factorization and a detected zero-row singularity share status 1. A singular matrix with no zero input row reaches a zero pivot without rejection. Two of two regression cases fail.

Source at the exact head:
- [ludcmp.h lines 20–39](https://github.com/chengcli/snapy/blob/070ba601ef8cc225cd294d320e4b7554e358b1aa/src/math/ludcmp.h#L20-L39): success parity / singular return ambiguity.
- [ludcmp.h lines 70–79](https://github.com/chengcli/snapy/blob/070ba601ef8cc225cd294d320e4b7554e358b1aa/src/math/ludcmp.h#L70-L79): pivot division without magnitude rejection.
- [forward_sweep_impl.h](https://github.com/chengcli/snapy/blob/070ba601ef8cc225cd294d320e4b7554e358b1aa/src/implicit/forward_sweep_impl.h#L55-L108) and [tridiag_thomas_impl.h](https://github.com/chengcli/snapy/blob/070ba601ef8cc225cd294d320e4b7554e358b1aa/src/implicit/tridiag_thomas_impl.h#L46-L81): four unchecked LU calls, and unchecked small-matrix inverses.

Before changing failure semantics, please clarify the return convention, pivot magnitude threshold/scaling, caller failure propagation (including CPU/CUDA and retry/rollback), whether both 3x3 paths switch to LU, and the enumerated #285/#288 follow-ups. The coarse-column accuracy/fixer investigation is #286; this issue does not claim that work.

CPU Release source-build preparation is underway, not yet a verified successful build. This issue records ownership and reproduction before production fixes.


### Comment 1 (2026-10-09)

I own the CUDA follow-up on cleanup/288-ludcmp / #292. A reviewer reports A100 hangs at e75c1c3fc4d4656a701e9cf14bf70ac9f36a8890 in both CUDA assembly retry tests and scheme 9; reverting only ludcmp.h restores the retry tests (reported 756/621 ms). This is independent reported RED evidence, not my runtime measurement. My unchanged-head production implicit_dispatch.cu compile with nvcc 12.6.85 reproduces host/device allFinite warnings (#20014-D and #20011-D). The A100 hang cause remains a hypothesis. I will replace all seven finite-check sites with explicit std::isfinite element loops, preserve the existing RED test, and return a new full head for the assigned independent A100 gate.


### Comment 2 (2026-10-09)

I accepted the CUDA dispatch follow-up for #292. At e75c1c3fc4d4656a701e9cf14bf70ac9f36a8890, implicit_dispatch.cu:165 calls ForwardSweep, not ludcmp directly, and discards its Boolean result. The eight direct ludcmp calls are already checked; four in ForwardSweep are live on CPU/CUDA, four in tridiag_thomas_impl.h are legacy/test-only. CPU implicit_dispatch.cpp:159 checks ForwardSweep. Existing NaN sentinel handling already prevents observable bad backward substitution; this is an unenforced return contract, not a newly reproduced behavioral failure. I will add the same Boolean guard to the CUDA lambda, retain the original RED/GREEN test source and its four CUDA retry/stop cases, and validate compilation and warning counts. The independent A100 device execution remains pending.


## Issue #291: A step costs 1.54x more on 2.11.2 than on 2.10.9 for a small 2D moist grid: 46% more kernels, mostly inside `forward`

State: open; opened 2026-10-09.

**Symptom.** On a 2D moist CRM (178 x 120, one block, one A100), a step takes 42.1 ms on snapy 2.11.2 + kintera 2.6.0 and 27.4 ms on 2.10.9 + kintera 2.5.0. Measured on `117e449`, which is still the head of main. dt and steps per simulated day are the same (6.56 s, ~13,160 steps/day), there are no redos in either, and our production runs show the same ratio (40.9 vs 26.2 ms/step over days of simulation).

**Setup.** `ideal-moist` EOS with `limiter: true`, H2O + H2O(l) + H2O(l,p), weno5, lmars, rk3, `implicit-scheme: 1`, cfl 0.9, constant gravity, sedimentation, kinetics through kintera. External Python driver that follows `run_hydro`'s order (stages, refresh `hydro_w`, kinetics, `check_redo`). Both versions ran with the same driver, restart, node type and torch (2.10.0+cu128), one after the other in one job. Old wheels installed into a separate prefix.

**Measured** (cycles 100-600 for wall time; cycles 600-700 under `torch.profiler` for counts):

```
                              2.11.2    2.10.9    ratio
wall per step                 42.1 ms   27.4 ms   1.54
CUDA kernels per step         3005      2061      1.46
GPU busy per step             22.4 ms   14.8 ms   1.51
mean kernel duration          7.4 us    7.2 us
.item() per step              33        7

phase split (driver timer, ms/step)
  block.forward (3 stages)    35.2      26.1
  check_redo                  1.31      0.13
  kinetics                    3.07      2.54
  radiation (ours)            2.35      2.35
```

The grid is small enough that every kernel runs at the minimum launch-bound duration (~7 us) and the GPU is busy about half the time in both versions, so the step cost scales with the kernel count. The extra ops are mostly `as_strided`/`slice`/`select`/`narrow`/`mul`, and `sum` goes from 153 to 243 per step.

**What the switches account for** (2.11.2, timing only):

```
                              ms/step   kernels   .item()
default (cell + fixer)        42.3      3005      33
gravity-work-fixer: false     40.7      2839      27
gravity-work: face            41.2      2869      27
wb-wall-clamp: false          42.1      3005      33
```

The gravity-work changes account for about 1.5 of the ~15 ms and 166 of the 944 extra kernels. We did not attribute the remaining ~780 kernels. Reading `hydro_forward.cpp` between `914b43b` and `117e449`, every stage now also runs:

- the positivity census (`_positivity_hits`, `_positivity_severe`, `_positivity_min`) and the limiter meters (`_lim_flux`, `_lim_cut`). As far as we can see, these are read only by the cycle printout, every `ncycle_out` cycles (`meshblock.cpp` around L1044-1090)
- `flux_positivity_carry_` with `species_enthalpy` (#236)
- the sedimentation-flux and dry-mass bookkeeping

`check_redo` reads its five flags with separate device-to-host reads (`floor_hit` 2, `vic_dry_clamp_hit` 1, `limiter_hits` 1, `saturation_failures` 1).

**Not known.** How the remaining ~13 ms splits among these. We have no per-block timings inside `forward`.

We can run a build with `RECORD_FUNCTION` scopes if per-block timings would help.


## Issue #294: Float32 rest-column vicclamp becomes NaN from zero scale

State: open; opened 2026-10-09.

This focused diagnostic follow-up is implemented in #292. Existing #290 covers LU rejection/rollback; this issue tracks the separate float32 diagnostic defect. No independent sign-off, merge or READY declaration is claimed.

At source head af6a3f879ec23c8aabd02d12ae221a618b713d0f, [implicit_hydro.cpp:311](https://github.com/chengcli/snapy/blob/af6a3f879ec23c8aabd02d12ae221a618b713d0f/src/implicit/implicit_hydro.cpp#L311) clamps the face-mass scale to 1e-300. That floor converts to zero in float32. For a rest column with zero transfer on both faces, lhs=rhs=0, so the residual computes 0/0=NaN. Its running maximum retains NaN for the run.

Minimal reproduction using Torch 2.7.1+cu126, CPU:
```python
import torch
scale = torch.zeros(1, dtype=torch.float32).clamp_min(1e-300)
ratio = torch.zeros_like(scale) / scale
print(scale, ratio, torch.isfinite(ratio))
# tensor([0.]) tensor([nan]) tensor([False])
```

Planned regression: finite float32 rest-column correction through forward_masked, assert no solve failure, unchanged zero correction and finite vicclamp. Establish RED on this head before fixing. Use a dtype-safe scale floor, retain the double floor/arithmetic exactly, and compare double state/diagnostic bit patterns across the change. Scope is diagnostic arithmetic plus the regression; measure the tall-column CTest runtime and increase timeout only if >60 seconds. Independent CUDA re-signing is pending.


### Comment 1 (2026-10-09)

RED established before production edits at af6a3f879ec23c8aabd02d12ae221a618b713d0f: source-built `test_lu_failure.release --gtest_filter=lu_failure.*rest_column_finite_vicclamp` exits 1. The float32 finite rest-column test has no solve failure and unchanged zero corrections but vicclamp is NaN on both calls; the float64 control passes. This is the end-to-end zero-scale diagnostic reproduction, distinct from earlier fixture setup errors. The scoped fix retains the double floor and uses the minimum normal float32 value for float32.


### Comment 2 (2026-10-09)

Fix pushed at 7a69bef3eea41c1be1fdda4717d6c766f2d6acf3 in #292. GREEN: 24 CPU cases pass, five device skips; the float32 and double rest-column cases both report finite zero vicclamp. Full CPU CTest 85/85 in 191.10 s; tall-column test 2.73 s (timeout unchanged). Raw-byte comparison preserves all 12 double cases / 56 tensors including eight vicclamp diagnostics. Exact-head upstream CI 37958509985 is approval-held with zero jobs; independent CUDA re-signing remains pending. No merge or READY declaration.
