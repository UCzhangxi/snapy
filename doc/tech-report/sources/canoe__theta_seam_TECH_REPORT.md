> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# A donor factor that crossed the seam as a blend

The tracer flux-positivity limiter scales every face flux by one factor, the donor cell’s θ, and conserves because both cells sharing a face use the same number. On the cubed sphere the seam ghost of θ was filled by the same interpolating exchange that fills density and wind, so the far side of every panel seam received a blend of neighbour cells instead of the donor’s factor. Wherever a tracer front met a seam the two sides scaled the shared face by different numbers and tracer mass appeared or vanished. The design had named this as a follow-up and deferred it; the one measurement on file was taken in a geometry where it cannot show. Measured here at up to $2.4\times10^{-3}$ of a tracer in 300 cycles and, on a spun-up hot Jupiter, $4.8\times10^{-6}$ in 0.8 days. Fixed by shipping θ across seams as a raw copy: two flags. The per-species factor is measured and kept; the partition is bounded and left.

snapy `4b802af` → `cdbbda8` on 2026-09-02: `4b59cf6` (this fix + the seam ctest, squashed) and `cdbbda8` (version-tag matching). Build `5730923` has a tree byte-identical to `cdbbda8` · design: the positivity-fix design report (2026-07-31) §5.3–5.4 · **revision 2** (ratio columns re-measured against the conserved density) · 2026-09-02

**STATUS, added 2026-09-06 (revised the same day).** The fix described here is **in the pin**. It is commit `4b59cf6` — an earlier draft of this banner said it “entered at `57e3fcd`”, which was merely the pin of the day and is a tests-only commit two later (review of 2026-09-06). It is carried into the x86 pin: snapy `61cebeb` with kintera `1f4f11b`, both replayed on 2026-09-06 as one commit per subject for the upstream pull request. ⚠ The **aarch64** build is still held at snapy `4b802af`, which does *not* contain `4b59cf6`, so **the seam leak measured here is live on that build** until the arm rebuild.

**One sentence in §12 is now stale.** The parenthetical that “`check_redo` only makes a local copy” no longer describes the code. The first half of that passage — that `hydro_w` is one stage stale between `forward()` calls — is not only still true but became load-bearing: a later change built `check_redo`’s floor detector on that array and it silently accepted a destroyed state carrying an 11 km/s cell. As of snapy `115efc2` (in the pin) `check_redo` recomputes the primitives from the current conserved state on a clone, decides collectively by MAX-allreduce because the time step is global, and restores `hydro_w` and the scalar primitive on rollback. Gate: `tests/test_check_redo_floor.py`.

**Superseded as the entry point** by the consolidated tracer-positivity report (2026-09-06), which consolidates this report with the earlier tracer-seam reports, the 2026-07-31 design report and later floating-point work. This report stands as the detailed record; read the consolidated one first.

**What was wrong.** `hydro_forward.cpp` 4.C and `scalar.cpp` exchanged the limiter factor θ with `interpolate(true)`. On the cubed-sphere layout the receive path then runs `interp_ghost`, which gathers along the panel edge with fractional weights at every ghost depth, so a seam ghost of θ was a blend of two neighbour cells. The design report’s own §5.4 says the panel-edge exchange of donor factors was a documented follow-up before cubed-sphere production; it was never done.

**How big.** Only when θ jumps along a seam, i.e. when a tracer front or a plateau boundary crosses one. Then: +$1.5\times10^{-3}$ of the hat tracer and −$1.3\times10^{-4}$ of its complement in 300 cycles (six panels, 24 cells per edge), +$9.2\times10^{-4}$ in 100 cycles on six MPI ranks, and +$4.8\times10^{-6}$ of a dye in 360 cycles (0.8 days) on the ISSI card restarted from a 10-day spun-up state. With the limiter off, or the front away from every seam, every arm conserves to $2\times10^{-14}$. The earlier 2026-09-01 number (−$2.3\times10^{-11}$) came from a dye whose band edges sat on the polar panels, where no θ jump ever met a seam.

**The fix.** `interpolate(false)` at both θ exchanges: the raw index-matched copy the hydro already uses for its reconstructed seam states, so the first ghost layer, the only one the scaling reads, holds the neighbour’s edge-cell θ exactly. After it every arm, every geometry (one process, six ranks, subdivided panels, the spun-up hot Jupiter) conserves to round-off, and the limiter-off and in-panel arms are unchanged to the last digit.

**What is not changed.** The per-species θ: the positivity limiter adds nothing measurable to a sum-to-one residual and the upper bound reduces it, so the design’s §5.3 trade-off stands. The mass/energy partition: bounded, second order in the trace mass fraction, unmeasured, left open. Facts found on the way, including one false alarm about the base scheme, are recorded in §12.

**Review banner, added 2026-09-06** (read against snapy `e2e397a`). (1) The status box above says the fix “entered at snapy `57e3fcd`”: that was the pin at the time; the fix is commit `4b59cf6`, and `57e3fcd` is a tests-only commit two later. (2) §1’s $\theta_i = \min(1, u_iV_i/(\Delta t\,\mathrm{out}_i))$ and “cannot be drained below zero” are the pre-`5f8a7f2` form; the limiter now retains 4096·eps of the cell (`flux_positivity.cpp:51-55`), bit-identical on every total measured here. (3) The slab-test row of §8 was measured on `test_flux_positivity.yaml` before `4f59088` gave its condensate a reference internal energy; an A/B on the seam card was bit-identical, so the number stands.

## 1. What this machinery is, and the one invariant it rests on

After the high-order face fluxes of a stage are final, the limiter forms, per species and per cell, the outgoing mass the divergence is about to remove,

$$\mathrm{out}_i = \sum_{\mathrm{faces}} \max(\pm A_fF_f,\, 0),\qquad \theta_i = \min\!\left(1,\ \frac{u_iV_i}{\Delta t\,\mathrm{out}_i}\right),$$

and multiplies every face flux by the θ of the cell it drains (`flux_positivity.cpp`). Three properties follow by construction: the cell cannot be drained below zero in one Euler step; the SSP structure of the integrators extends that to every stage; and *conservation is exact because each face carries one factor, shared by both adjacent cells*. That last sentence is the whole contract. When the donor of a face lives on another rank, the receiving rank must hold the donor’s θ in its ghost layer, and it must be the donor’s number, not an estimate of it. `flux_positivity.hpp` says so in its header, and the design report (§5.4) says the ghost layer is filled “exactly like conserved-variable ghosts”. On a slab that is a copy. On the cubed sphere it is not.

## 2. Where the evidence stood

The original defect report bundled three claims of different strength. That both call sites use `interpolate(true)` was verified by reading the source at the pin. That conservation degrades “~1300×” at seams was inherited from three runs on an older build (`ab31dbb`), one dye, 300 cycles: in-panel −$1.65\times10^{-14}$, straddling −$2.33\times10^{-11}$, straddling with the limiter off −$1.76\times10^{-14}$. That the interpolation causes the degradation was an inference. The design’s certifying unit test (`tests/test_flux_positivity.py`) is a single-rank slab, cannot cross a panel seam, and, it turns out, was never registered with ctest.

Reading the design again settles the first question before any run. Its §5.4 closes with:

> “Cubed-sphere panel edges interpolate ghosts and are therefore only approximately single-valued for θ; planar/slab runs (all current implicit production) are unaffected, and a panel-edge exchange of donor factors (piggybacking on the existing cross-panel messages) is the documented follow-up before cubed-sphere production use […].”

So this is not a divergence between design and code. It is an item the design scheduled and nobody did, which became load-bearing the day a passive tracer ran on the cubed sphere.

## 3. The instrument

The defect is a property of panel seams, so a Cartesian box cannot show it, but it does not need the scheduler either: snapy runs six panels as six blocks in one process (Mesh API, `blocks_per_process: 6`, the layout the existing exchange test uses). The harness (`seam_harness.py`) is a dry ideal gas on a thin spherical shell, no gravity, a solid-body zonal wind of 10 m/s, and three passive tracers: `a` a hat in longitude and latitude, `b = 1 − a`, and `c = 1`. Scalar numerics are the ISSI card’s (weno5 scale+shock, upwind, `upper-bound: 1.0`). Every 50 cycles it prints the interior total of each tracer, its extrema, max\|a+b−1\|, max\|c−1\| and the limiter’s hit count. Three placements of the hat: *in-panel* (its edges outside the reconstruction stencil of any seam), *edge* (its downwind edge exactly on the +X/+Y seam), and *plateau* (the seam under the flat top of the hat, the ISSI c06 geometry). One arm takes 20–40 s on a CPU node; the eight-arm grid is a three-minute job.

Two things the instrument taught before it measured anything. A single radial cell, as in `tests/test_exchange.yaml`, is not a valid hydro setup on the sphere: the radial momentum equation carries a geometric source that the face-area difference of a real column balances, and with one cell and no x1 flux nothing balances it; pressure drains into radial kinetic energy and the run dies at cycle 45 even at rest. With four radial cells the rest state is exact to $5\times10^{-13}$ after 60 cycles. And “in-panel” at 12 cells per edge is not in-panel: a hat edge two cells from a seam sits inside the weno5 stencil and leaked $3\times10^{-9}$; at 24 cells with a 20° half-width it is at round-off.

## 4. The measurement on the pin

Pinned build `4b802af`, 300 cycles, 24 cells per panel edge, drift = (total − initial)/initial over the interior of all six panels. Ratio columns re-measured against the conserved density (revision 2, §12); the drifts are identical to the first pass.

| hat | limiter | bound | drift a | drift b | drift c | max a | max\|a+b−1\| |
|----|----|----|----|----|----|----|----|
| in-panel | off | off | −1.8e-14 | −1.7e-14 | −1.8e-14 | 1.000119 | 1.21e-4 |
| in-panel | on | off | −1.9e-14 | −1.7e-14 | −1.8e-14 | 1.000119 | 1.21e-4 |
| in-panel | on | on | −1.8e-14 | −2.7e-9 | −1.8e-14 | 1.000000000000 | 1.04e-4 |
| edge on seam | off | off | −1.8e-14 | −1.8e-14 | −1.8e-14 | 1.00157 | 8.1e-3 |
| edge on seam | on | off | −1.9e-12 | −1.29e-4 | −1.8e-14 | 1.00157 | 7.3e-2 |
| edge on seam | on | on | +1.52e-3 | −1.29e-4 | −1.8e-14 | 1.000000000000 | 5.6e-3 |
| plateau over seam | on | on | +8.5e-4 | −7.6e-5 | −1.8e-14 | 1.000000000000 | 1.5e-4 |
| edge on seam, cp5 | on | on | +2.4e-3 | −2.1e-4 | −1.8e-14 | 1.000000000000 | 8.2e-3 |

Four readings. The limiter-off rows conserve at round-off in every geometry, so the base cross-panel scalar transport is conservative and the leak is θ’s alone. The leak needs a *jump* in θ along a seam: `b` is zero inside the hat, so its positivity θ is 0 along the seam segment inside the latitude band and 1 outside, and the interpolated ghost hands the far side a blend at the two band edges. The complement θ of `a` (the upper bound) is 0 on every plateau cell, so it carries the same jump and, being plateau-wide, leaks ten times more. And the sign is structural: the far side applies too small a factor to an outgoing flux, so the tracer whose plateau is upwind gains and the one whose depleted side is upwind loses. The uniform tracer `c` has no jump anywhere and never drifts.

This is also why the ISSI measurement was seven orders smaller. That dye covered \|lon\|\<80°, \|lat\|\<80°: every equatorial seam ran under its plateau with θ uniformly 0 along the whole seam, and its band edges sat on the polar panels, so no jump met a seam and only round-off-level mismatches remained. The in-panel bound row above (−$2.7\times10^{-9}$, where `b`’s plateau covers every seam with no jump) is the same benign case. A real tracer field has fronts crossing seams continuously.

## 5. The discriminator

Two arms settle the mechanism without a print statement. With the limiter off the leak vanishes in every geometry, so it is θ. With the ghost fill changed from the interpolating exchange to the raw copy and nothing else touched (§7), the leak vanishes in every geometry (§8), so it is the interpolation. An intermediate probe, printing max\|ghost θ − exact θ\|, would have answered only a magnitude: the interpolation kernel (`gnomonic_equiangle.cpp`, `_interp_ghost_LR/BT`) gathers with fractional weights at every ghost depth including the first, so a non-zero difference is forced wherever θ varies along the edge.

## 6. The cause

Both sites did the same thing:

    // src/hydro/hydro_forward.cpp (4.C)          // src/scalar/scalar.cpp (sync_theta)
    SyncOptions topts;                             SyncOptions theta_opts;
    topts.interpolate(true).type(kScalar);         theta_opts.interpolate(true).type(kScalar);
    pmb->exchange(tvars, topts);                   pmb->exchange(tvars, theta_opts);

On the cubed-sphere layout the cross-panel receive path (`cubed_sphere_layout.cpp` deserialize) does `index_put_` of the raw strip and then, if `interpolate()`, `pcoord->interp_ghost(var, offset)`, which rewrites the ghost strip as a blend along the edge. The machinery for the alternative already existed: the hydro ships its reconstructed seam states with `cross_panel_only(true).interpolate(false)`, a raw copy with the edge reversal and transposition handled, and that is exactly why the base seam flux is single-valued. Because `interp_ghost` interpolates only along the edge, depth by depth, the raw copy at depth one is the neighbour’s edge-cell value, and `flux_positivity_scale_` reads nothing deeper than depth one.

## 7. The fix

Commit `6e5adf7`, nineteen insertions in three files. `interpolate(false)` at both exchanges. A `positivity_hits` buffer on the scalar module, mirroring the hydro’s, incremented at both scalar limiter sites (the tracer’s own θ and the complement’s) so a run can say whether the scalar limiter fired at all; the ISSI lineage had inferred that from drift for a month. The census at all three sites now counts interior cells explicitly: the independent review found that cells which are ghosts in x2/x3 but interior in x1 accumulate real x1 outflow in `flux_positivity_theta` and can carry θ\<1, so the existing hydro comment “ghosts are exactly 1 here” was wrong and its count double-counted across ranks.

The review (scoped to “changes a number, hangs, or crashes”) traced the cubed-sphere serialize/deserialize for cell-centred data with `interpolate(false)`, the subdivided-panel single-round exchange (the first time intra- and cross-panel θ messages post in one round, so subdivided-panel geometry had to be tested, §8), corner handling (`skip_corner` leaves corners at 1; a corner ghost is never the donor of a face the divergence consumes), non-cubed layouts (the flag is not read; bit-identical), the in-process rendezvous key (the flag is part of it, but every block takes the same branch), and the counter (same idiom as hydro’s, moves with `.to()`, nothing serialises buffers by name). Verdict: safe to build. One adjacent hole it noted and this fix does not close: on a cubed sphere with `pz > 1` the x1 ghosts of θ are neither exchanged nor overwritten; that configuration is disallowed (`nb1` must be 1 on the cubed sphere), so it is recorded, not fixed.

Two further commits accompany the fix. `ed1e06a` adds `tests/test_flux_positivity_cubedsphere.py`, six panels in one process with a tracer hat whose downwind edge sits on the +X/+Y seam, asserting both arms conserve to $10^{-12}$ and the limited arm fires and stays in \[0, 1\]; it registers that test and the existing slab test with ctest, neither having been registered before. `5730923` tells setuptools_scm to infer the version from `v*` tags only, because an `archive/…` tag on the pin commit made `git describe` return a non-version and every build of any commit after the pin failed at the install step (§12).

## 8. Validation

### 8.1 The same eight arms on the fixed build

| hat | limiter | bound | drift a | drift b | drift c | max a | max\|a+b−1\| |
|----|----|----|----|----|----|----|----|
| in-panel | off | off | −1.8e-14 | −1.7e-14 | −1.8e-14 | 1.000119 | 1.206e-4 |
| in-panel | on | off | −1.8e-14 | −1.7e-14 | −1.8e-14 | 1.000119 | 1.206e-4 |
| in-panel | on | on | −1.7e-14 | −1.7e-14 | −1.8e-14 | 1.000000000000 | 1.045e-4 |
| edge on seam | off | off | −1.8e-14 | −1.8e-14 | −1.8e-14 | 1.00157 | 8.1e-3 |
| edge on seam | on | off | −1.8e-14 | −1.7e-14 | −1.8e-14 | 1.00157 | 2.8e-3 |
| edge on seam | on | on | −1.8e-14 | −1.7e-14 | −1.8e-14 | 1.000000000000 | 1.08e-3 |
| plateau over seam | on | on | −1.8e-14 | −1.8e-14 | −1.8e-14 | 1.000000000000 | 1.52e-4 |
| edge on seam, cp5 | on | on | −1.8e-14 | −1.7e-14 | −1.8e-14 | 1.000000000000 | 6.6e-3 |

The limiter-off and in-panel rows are unchanged to the last printed digit against §4: where θ is uniform along a seam the raw copy and the interpolation agree, so the change is inert exactly where it should be. The seam rows drop from $10^{-3}$ to $2\times10^{-14}$. The sum-to-one residual at the seam also falls, $7.3\times10^{-2}$ to $2.8\times10^{-3}$ with the positivity θ alone, because the leaked mass had been corrupting the local constraint too. With the bound on, the maximum of `a` is exactly 1.000000000000 in every arm and the uniform tracer is exactly 1 (revision 2, §12: the ratio columns are now formed against the conserved density; the earlier 1.0000037 was an instrument artefact).

### 8.2 The other geometries and the certified build

| configuration | pin 4b802af | fixed | hits (fixed) |
|----|----|----|----|
| seam ctest, 6 blocks in one process, 12 cells/edge, 40 cycles | +2.0e-3 (20 cyc) | 2.4e-15 | 116,930 |
| subdivided panels, nb2 = nb3 = 2 (24 blocks), edge, 60 cycles | +8.1e-4 | −3.8e-15 | — |
| six MPI ranks (gloo), one panel each, edge, 100 cycles | +9.2e-4 | −6.1e-15 | — |
| certified build `5730923`, edge, one process, 300 cycles | — | −1.8e-14 | 2,016,132 |
| ISSI runner + card from rest, 16 cells/edge, 6 CPU ranks, 300 cycles, dye edges on the ±45° seams | −1.7e-14 | −1.7e-14 | 20,832,611 |
| ISSI runner + card **restarted at day 10** (spun-up winds), 32 cells/edge, 6 GPU ranks, 360 cycles, same dye | +4.76e-6 | −2.2e-14 | 97,026,095 |
| slab test `test_flux_positivity.py` (non-cubed layout, must be unchanged) | passes | passes | 68 |

The from-rest ISSI arm shows no leak on either build: in the first 0.67 days of a Guillot column there is not yet enough wind across the seams for a θ jump to move mass. The spun-up arm is the one that matters for the science: with the day-10 circulation, the pin leaks $4.8\times10^{-6}$ of the dye in 0.8 days, roughly $6\times10^{-6}$ per day, which over a 1000-day tracer experiment is a few $10^{-3}$ of the tracer mass, and the fixed build holds it to −$2\times10^{-14}$ while the limiter fires $9.7\times10^{7}$ times. With the corrected census (§12) the fixed build holds the dye maximum at exactly 1.000000000000 at every output cycle of that arm, so the bound survives the implicit vertical correction on this card; the 1.000035 first read there was the stale-density artefact.

## 9. Cross-species: measured, and kept as designed

The design’s §5.3 states the trade-off: each species gets its own θ, so the composition of a parcel is altered where the limiter fires; a common θ = min over species would restore proportional transport at the price of limiting species that did not need it. The literature says the same thing three times (Blossey–Durran 2008 eq 43, Zhang–Shu’s system limiter, the interface state of Zhang et al. 2025), and two facts sharpen it: θ is scale invariant, so proportional tracers already share θ exactly and only tracers with different spatial structure can be limited differently; and per step the residual is bounded by (1 − θ) times the content of the depleting cell, i.e. by the tracer mass in the near-empty cells.

The instrument is max\|a + b − 1\| over interior cells with a and b complementary, and the decision rule was fixed before measuring: adopt a group-shared θ only if the limiter’s increment is at least a tenth of the residual the reconstruction produces on its own. In-panel, 300 cycles: reconstruction alone $1.206\times10^{-4}$; with the positivity limiter $1.206\times10^{-4}$, identical to four digits; with the bound $1.041\times10^{-4}$, a 14 % reduction because the bound removes the overshoot. The increment is unmeasurable. Per-species θ stays, and no common-θ variant was built. The magnitudes once quoted for this came from a reconstruction-limiter harness, not this limiter, and are retired.

## 10. Partition: bounded, not measured, left

The Riemann solver builds the mass, species, momentum and enthalpy fluxes from one mass flux (`lmars_impl.h`); θ scales only the species channels. Throttling a species flux by $(1-\theta)F_c$ while the total mass flux is untouched converts that much species mass into dry air at the face; momentum and energy remain conserved and consistent with the total mass flux, and the enthalpy carried assumes the unthrottled composition, an error of second order in the trace mass fraction. It is confined to near-depleted cells, inert on hot-Jupiter cards (`ny = 0`), and was measured immaterial at geEx settings earlier. No change is made and no new measurement was taken here; it stays open with that bound attached.

## 11. What the literature says the scheme is, and what it could become

Seven papers were read for this. The limiter is, equation for equation, Zalesak 1979’s $R^-$ with $w^{\min} = 0$, Skamarock 2006’s positive-definite renormalisation and Blossey–Durran 2008’s $r^{\mathrm{pos}}$; it is also the “same range at every outflow face” simplification Thuburn 1996 names and declines to refine. Three families of bound-preserving limiter exist. The reconstruction-side ones (Zhang–Shu’s Gauss–Lobatto rescale, Thuburn’s face-ratio clip, the smoothness blend of Zhang et al. 2025) and the solution-side one (Guba 2014’s per-element QP) need no seam agreement at all, but every one of them carries a Courant condition on its guarantee, and snapy’s vertical Courant number exceeds one by design. The flux-clip family is the only one whose positivity is Courant-free, which is why it is the right family here, and the seam requirement (exchange the derived factor, never recompute it from ghosts, Zalesak §3) is its price. That price is one raw ghost copy per stage.

Two things the literature offers that this work did not take, recorded with their triggers. Every other flux-clip paper scales only the high-order increment above an upwind base, so its θ → 0 limit is donor-cell transport where ours is no transport at all; Skamarock measured that form as nearly free in accuracy. The trigger for adopting it is a measured “θ = 0 stalls a front” symptom, which the new hits counter makes countable. And the “limit only the last RK sub-step” of Zhang et al. 2025 is sound for their linearised RK3 and unsound for SSP-RK3, where every stage’s flux enters the answer; it must not be copied.

## 12. Found on the way

- **Filed and closed the same day: an instrument artefact, not a defect.** The uniform tracer `c` appeared to deviate from 1 by up to $7\times10^{-6}$ in a moving flow, limiter on or off, weno5 or cp5, exactly 0 at rest, and to cap the upper bound at 1.0000037. Three discriminators settled it: the deviation is born in the first stage of the first step and scales linearly with the wind, so it is not a lag between the scalar and density updates; after every stage the scalar’s F1/F2/F3 and divergence buffers for `c` are *bitwise* the hydro’s mass channel; and the ratio formed against `hydro_u[IDN]` is exactly 1, while max\|`hydro_w` − `hydro_u`\| equals the “deviation”. The primitive state exposed between `forward()` calls is one stage stale (it is refreshed inside the next hydro forward; `check_redo` only makes a local copy). The harness and the ISSI census had divided by it; snapy’s own `set_scalar_primitive` divides by the conserved density. Both instruments now do the same, and with that every ratio column in this report was re-measured: the bound holds exactly, the uniform tracer is exactly 1, and the cross-species residuals are unchanged (§9).
- **Base-scheme overshoot at seams.** With no limiter a tracer step crossing a seam overshoots to 1.051 at 12 cells per edge and 1.0016 at 24, against 1.00012 for the same step inside a panel: the cross-panel reconstruction from interpolated ghosts is much worse than the interior one. The bound hides it; the earlier maximum-principle history lives here.
- **A single radial cell is not a valid hydro configuration on the sphere** (§3). The exchange test that uses it is fine as an exchange test.
- **Any commit after the pin failed to build.** `git describe` picks the nearest tag of any kind; an `archive/…` tag sits on `4b802af`, so for every descendant setuptools_scm hit a non-version tag and `pip install` aborted with an `AssertionError` in `_parse_tag`. The pin itself built because at distance zero a different rule applied. Fixed in `5730923`; until that lands, `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_SNAPY` gets a build through.
- **The slab positivity test was never in ctest.** Registered now, with the seam test.

## 13. Gates

Two, so the property cannot silently regress again. In snapy: `tests/test_flux_positivity_cubedsphere.py`, registered with ctest, ten seconds, asserts both arms conserve to $10^{-12}$ across a seam with a θ jump on it and that the limited arm fires. In the example battery: case `45_tracer_seam_cubedsphere_cpu`, the harness as its runner, six gloo ranks, 100 cycles, scored by `run_panel_seam_guard` on the first and last `[TRACER]` lines of rank 0 with PASS iff max\|reldrift\| \< $10^{-12}$ and hits \> 0, INCONCLUSIVE below two samples. The threshold is fifty times the measured floor ($2\times10^{-14}$) and eight orders below the defect ($10^{-4}$ to $10^{-3}$); the existing x1 guard’s $10^{-8}$ would have passed the ISSI number and failed nothing. Tracer totals are printed by the runners, not by snapy’s cycle line, so a chemistry card with many species does not swell every run’s output; the ISSI runner gained the same `[TRACER]` census.

## 14. Provenance

- Source: snapy. Developed as `6e5adf7`, `ed1e06a`, `5730923`, then cherry-picked as `4b59cf6` (squashed fix + test) and `cdbbda8` (build fix). The merged tree is byte-identical to the tested one (`3d45399…`), so every number below stands unchanged on the merged commits. Not on upstream; part of an upstream PR series.
- Builds: pin `4b802af`; dev install `6e5adf7` (finished build tree + pretend version, used for the fixed-arm grids and the GPU pair); certified `5730923` (used for the ctest, the 300-cycle edge arm and the six-rank run).
- Runs: harness grids (pin and fixed); six-rank pair; ISSI from rest (pin and fixed); spun-up GPU pair restarted from the day-10 restart file of the ISSI card.
- Papers: Zalesak 1979; Thuburn 1996; Skamarock 2006; Blossey & Durran 2008; Zhang, Xia & Shu 2012; Guba, Taylor & St-Cyr 2014; Zhang et al. 2025 (a different group).

Source precedence throughout: the source at the pin, then a measurement taken here, then the original defect report, then a report. Every number in this document was produced in this work on the builds named above; the only inherited numbers are the three in §2, quoted as inherited.
