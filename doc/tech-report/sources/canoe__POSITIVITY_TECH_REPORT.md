> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Keeping tracers positive in snapy

A tracer must not go negative, and tracer mass must not appear or vanish. In snapy those are not two properties but one, and the whole of it rests on a single sentence: every face flux is multiplied by *one* factor, the factor of the cell that face drains, and both cells sharing the face use that same number. This report is the consolidated account of four generations of work on that sentence — the limiter and the implicit column flux that established it, the repair chain that sat downstream of it and had defects of its own, the panel seams and the maximum principle that showed the sentence could be broken by an exchange rather than by arithmetic, and finally floating point, where the sentence turned out to be unachievable exactly as written. It also records what is still open, and what was measured wrongly along the way.

Prepared 2026-09-06, on snapy `e2e397a` and kintera `83e30f1` · of the twelve commits in this family two are in upstream `main` (`6cf0fae` \#195, ours; `bcbd07a` \#196, the upstream author’s) and ten are fork-only · supersedes `Positivity-fix-TECH_REPORT.pdf` (2026-07-31), whose design analysis it cites rather than replaces · consolidates the seam, maximum-principle and dry-channel reports

**The invariant.** After a stage’s high-order fluxes are final, the limiter asks of each cell and each species how much of that species the divergence is about to carry out, and if that is more than the cell holds, it scales every one of that cell’s outgoing fluxes down by the single factor θ that makes the outflow exactly affordable. Because the factor belongs to the donor, and because the donor of a face is the same cell whichever side you stand on, each face is scaled once. Nothing is created and nothing is lost. Positivity and conservation are the same statement.

**Four generations.** *One* (2026-07/08) built the machinery: the flux limiter, and a rewrite of the implicit vertical correction so that it moves species as a face flux rather than a pointwise pro-rata patch. *Two* found that the repair chain downstream of transport had its own leaks — a condensate clamp that invented mass, a vapour redistribution that double-counted a cell, and a step-rejection detector that the limiter had silently made unreachable. *Three* moved to the cubed sphere, where two separate seam defects appeared: reconstructed tracer states arriving swapped across a panel edge, and the limiter’s own factor arriving as an interpolated blend instead of the donor’s number. *Four* found that the factor targets an exact zero, which in floating point lands just below zero, so the guarantee could not hold by construction; and that the repair which was supposed to catch that could not repair the bottom cell of a column, and on GPU could not report its own failure at all.

**Where it stands.** Every defect named above is fixed at `e2e397a`. Across every geometry tested — one process, six MPI ranks, subdivided panels, a spun-up hot Jupiter on six GPUs — tracer mass now conserves to round-off, about $2\times10^{-14}$, where before the seam fix it drifted by up to $2.4\times10^{-3}$ in 300 cycles. The floating-point margin changes no conserved quantity to fifteen significant figures.

**What is open.** The limiter scales the species channel but not the momentum and enthalpy the Riemann solver built from the same mass flux, so a throttled species flux mis-partitions that mass into dry air at the face (bounded, unmeasured). Per-species factors break linear constraints across tracers, which matters the day coupled chemistry advects a constrained set. The implicit solver’s own density clamp has an analogous partition problem, analysed but not implemented. And the accuracy repair the literature makes a case for — scale only the high-order increment above an upwind base — has not been done.

## 1. Summary, and the three things worth carrying away

Tracer transport in snapy has to hold four properties at once: tracers stay non-negative, a mixing ratio stays below its bound, tracer mass is conserved exactly including across the seams of a cubed sphere, and accuracy away from fronts is not thrown away to buy the first three. The machinery that does this is small — 586 lines across six files at the pin, with three call sites — and its correctness rests almost entirely on one design decision, stated once in 2026-07 and defended, broken and repaired repeatedly since.

Three observations run through everything that follows. They are stated here and referred back to rather than restated.

### (i) One factor per face, shared by both cells

The limiter’s conservation argument is not an accounting exercise; it is structural. A face carries one number. Whatever leaves the donor arrives in the receiver, because the same scaled flux appears with opposite sign in the two divergences. There is no bookkeeping hole to audit. The consequence, and the reason this document exists, is that *every defect in it is a way that sentence was silently broken*: by an exchange that delivered an interpolated value instead of the donor’s (§7), by an exchange that delivered the reconstructed states in the wrong order (§7), by a target that floating point could not hit (§8), by a repair that scaled one channel of a face and not the others (§7, §12).

### (ii) A defect that conserves mass exactly is invisible to a mass gate

Three of the defects here conserve total mass to the last bit and were therefore invisible to every gate this project owned, because every gate this project owned was a mass gate. The swapped seam states of §7 produce an anti-upwind mode one cell wide that moves exactly as much mass as it should, in the wrong direction. The mass/energy mis-partition of §7 converts species mass into dry air at a face while conserving both. The implicit solver’s density clamp (§12) moves mass antisymmetrically and leaves the cell holding one solver’s mass and another’s energy. Each was found by looking at something other than a mass total.

### (iii) The instrument is part of the experiment

Four times the thing doing the measuring was itself wrong. The census of limiter firings counted ghost cells and double-counted across ranks (§7). A tracer that appeared to deviate from unity in a moving flow was reading a primitive state that is one stage stale (§7). Four python ctests were registered but not listed, so under a test-path build they imported whatever pip had installed rather than the tree under test — a false red against an older venv and a false green against a newer one (§11). And the moist test harness on which much of generations three and four was measured had a condensate with no reference internal energy, making its latent heat exactly zero at the reference temperature and condensation endothermic above it (§8). Only the last of these changed no number, and that was checked rather than assumed.

### Headline gates

| what | result | where |
|----|----|----|
| Unit A/B, 2-D slab, 10 cycles, unlimited reconstruction: minimum vapour | −4.11e−4 → exactly 0.0 | design report §9.1 |
| Same arm, species mass drift (mass *created* downstream by a zero-clamp) | +1.82e−3 → 2e−16 | design report §9.1 |
| Case 14 silicate cloud, implicit solver, 5000 s, same binary: total mass | +9.7e−8 transient → flat at 4.1e−13 | design report §10.2 |
| Tracer front on a panel seam, 300 cycles, 24 cells per edge | +1.52e−3 → −1.8e−14 | §7 |
| Spun-up hot Jupiter, six GPU ranks, 360 cycles, dye | +4.76e−6 → −2.2e−14 | §7 |
| kintera zero-clamp events in the moist seam harness, 300 cycles | 263,433 with the limiter off; none with it on | §6 |
| Floating-point margin, A/B against the unfixed build, 300-cycle moist cubed sphere | every conserved total bit-identical to 15 s.f. | §8 |
| The two generation-4 fixes, one at a time, five harness arms | both together reach cycle 300 on all five; neither alone does | §8 |
| Example-deck suite on the pin | core 15/15; full 56/56, twice | §11 |

## 2. Where tracers live, and the three ways their mass moves

Before any of the mechanisms can be read, it is worth being concrete about what is being conserved and by which code. Two kinds of tracer exist in snapy and they travel by different modules, but both end up scaled by the same limiter.

The hydro conserved vector per cell is

$$U = (\rho_d, \rho u_1, \rho u_2, \rho u_3, E, \rho y_1, \ldots, \rho y_{ny}),$$

indexed `IDN`, `IVX`, `IVY`, `IVZ`, `IPR`, then `ICY` upward. The point most easily got wrong is that `IDN` carries the *dry* component $\rho_d = \rho(1 - \sum y_n)$, not the total density; the $y_{n}$ are mass fractions, vapours first and then clouds. Passive scalars are a separate conserved field $s = \rho_d r$ with mixing ratio $r$ per unit dry mass, handled by `ScalarImpl` rather than by the hydro. Face indexing follows the divergence convention of `CoordinateImpl::divergence`: `flux[i]` is the flux through the *lower* face of cell i. Throughout, “a stage” means one call of `MeshBlockImpl::forward`; the increment `du` accumulates ΔU per stage over the full Δt, and the integrator applies stage weights afterwards.

Tracer mass moves in exactly three ways, and the limiter has to be in front of all three or in front of none.

1.  **The explicit face flux.** LMARS picks one side by the sign of the interface velocity and writes, for each species, the upwind mass flux times the upwind mass fraction. It is already in donor form; that is the structure everything here builds on.
2.  **The implicit vertical column correction.** With `integration: implicit-scheme: 1` or `9` a block-tridiagonal system is solved per column in the density, vertical momentum and energy. *Species never enter the matrix.* What happens to them afterwards is the subject of Component B in §5.
3.  **Sedimentation.** Falling condensate is folded into the x1 hydro flux *before* the limiter runs, so it sits inside the outflow budget: falling precipitation cannot over-drain a cell either.

Downstream of transport sits what is best called the **repair chain**: whatever negatives survive are handled after the fact, at four sites in sequence. First `apply_conserved_limiter_` (`equation_of_state.cpp:160`), which every EOS calls at least twice per stage, and which fills NaNs with zero, floors density, floors energy, borrows a negative condensate from its parent vapour, and finally runs the columnar `fix_vapor` scan. Then kintera’s own input clamp inside the saturation adjustment. Then, at the end of the cycle, `check_redo`, which is supposed to reject the step and retry at a smaller Δt if the state is unphysical. Generations two and four are largely about defects in that chain, and §9 is about its last link.

The limiter itself has three call sites: the hydro species channels at `hydro_forward.cpp:331`, and twice in `scalar.cpp` — the tracer’s own lower-bound factor at `:159` and, for the upper bound, the factor of its complement at `:188`.

## 3. The invariant, and the argument that it survives a multi-stage integrator

The scheme is short enough to state completely. After all fluxes for a stage are final, compute per species c and per cell i the outgoing mass over the stage, exactly as the divergence will apply it, and from it the largest uniform rescaling of that cell’s outgoing fluxes that cannot drain it below zero in one forward-Euler step of size Δt:

$$\mathrm{out}_i = \sum_\mathrm{faces} \max(\pm A_f F_f, 0), \qquad \theta_i = \min\left(1, \frac{u_i V_i}{\Delta t\, \mathrm{out}_i}\right).$$

Then multiply every face’s species flux by the θ of its donor cell — the lower cell where that species’ flux is positive, the upper cell otherwise. Three properties follow, each by construction rather than by measurement.

**Positivity.** Cell i’s total outflow after scaling is at most $\theta_i\,\mathrm{out}_i\,\Delta t \le u_i V_i$; inflow only helps.

**Conservation.** A face carries one factor, shared by both adjacent cells. Whatever leaves the donor arrives in the neighbour.

**Accuracy.** θ ≡ 1 wherever a cell is not near depletion, so the high-order flux is untouched almost everywhere; the scheme degrades toward first-order donor-cell only at the edge of vacuum, which is where the unlimited flux was unphysical anyway.

The step from “one Euler step” to “a Runge–Kutta stage” is the part that makes this cheap, and it is worth spelling out because it is the reason no CFL change is needed. Every shipped integrator writes a stage as

$$U^\mathrm{new} = w_0 U^{(0)} + w_1 U^{(s)} + w_2 \Delta U(U^{(s)}) = w_0 U^{(0)} + w_1\left(U^{(s)} + \alpha \Delta U(U^{(s)})\right), \qquad \alpha = w_2/w_1 \le 1.$$

That is a convex combination of previous states and at most one full-Δt forward-Euler step. If $U^{(0)} \ge 0$ and $U^{(s)} + \Delta U \ge 0$ componentwise, then $U^\mathrm{new} \ge 0$, noting for $\alpha < 1$ that $U + \alpha\Delta U = (1-\alpha)U + \alpha(U + \Delta U)$. So a limiter that guarantees non-negativity for a single full-Δt Euler update guarantees it for the whole multi-stage scheme, at the unchanged CFL. For `rk1`, `rk2` and `rk3` every stage has $w_2 = w_1$; for `rk3s4`, $w_2/w_1 \in \{1, \tfrac12\}$.

Two details of the construction are easy to misread and both matter later. The donor of a face is chosen by the sign of *that species’* flux, not the mass flux. With an unlimited reconstruction a face mixing ratio $y_{f}$ can go negative just downwind of a sharp cloud edge, which makes the species flux oppose the wind; the species-sign rule then correctly identifies the cell being drained — a cell that may hold no tracer at all — whose θ is zero, and that zeroes the spurious backward flux exactly. And ghost cells receive θ = 1 from the kernel, because their outflow sums are not accumulated. Their true factors have to arrive from elsewhere: the caller must fill θ’s ghost layer the way a conserved variable’s ghosts are filled, by exchange plus the physical boundary functions, *before* the scaling runs. That requirement is written into the header of `flux_positivity.hpp`, and it is the sentence that generation three found had been honoured on a slab and not on a cubed sphere.

Two places later broke the invariant without breaking the code. In §7, a seam exchange that interpolated the factor rather than copying it, so the two sides of a shared face used different numbers. In §8, the observation that θ as written targets a post-update value of exactly zero — non-negative in exact arithmetic, a hair below zero in floating point.

## 4. Chronology

Twelve commits over five weeks, in two groups: the design work that went upstream, and the fork-only sequence that followed once the machinery met a cubed sphere and then met floating point. Two earlier upstream commits are included because they set the stage for §6. The middle column says what the symptom was, because the symptoms are rarely what the mechanism sounds like.

| date | commit | what it did, and what the symptom was | upstream |
|----|----|----|----|
| 2026-07-16 | 71f04ba | eos: guard a null thermo in `apply_primitive_limiter_` (#186). | yes |
| 2026-07-17 | bcb8b41 | x1 seam flux averaging and the `check_redo` rework (#188). Symptom: an EOS referenced to 300 K has legitimately negative conserved energy below $T_{\mathrm{ref}}$, so the old check fired a fatal, halving-proof redo on a valid cold layer. | yes |
| 2026-07-31 | (design report) | Component A, the flux positivity limiter, and Component B, the implicit species column flux. Symptom: transport creating negatives that the repair chain then converted into created mass. | → |
| 2026-08-01 | 6cf0fae | eos: conserve mass when repairing negative species densities (#195) — the condensate borrow, plus the `fix_vapor` seed fix. Symptom: total mass growing in condensing cases. | yes |
| 2026-08-02 | bcbd07a | Fix tracer positivity (#196) = Components A and B merged. **The last upstream commit in this family.** | yes |
| 2026-08-18 | 3b7485a | the face-density positivity floor falls back to the donor cell. | fork |
| 2026-08-27 | 5c61b39 | direction-suffixed cross-panel keys for the scalar’s reconstructed states. Symptom: a one-cell-wide anti-upwind mode along every panel seam that conserved mass exactly. | fork |
| 2026-08-31 | 82410e3 | the tracer bounded above by the positivity of its complement. Symptom: a mixing ratio reaching 1.143 where its bound was 1. | fork |
| 2026-09-02 | 4b59cf6 | θ made single-valued across panel seams, and both positivity tests registered with ctest. Symptom: tracer mass appearing or vanishing wherever a front crossed a seam. | fork |
| 2026-09-04 | 5f8a7f2 | the positivity margin, 4096 ulp. Symptom: `Failed to fix vapor mass fractions`. | fork |
| 2026-09-04 | 19b4766 | the upward vapour repair. Same symptom, independent second cause. | fork |
| 2026-09-04 | 8c43cca | CUDA and CPU failure reporting for `fix_vapor`. Symptom: none — that was the defect. | fork |
| 2026-09-05 | 115efc2 | `check_redo`: a fresh-primitive floor detector, decided collectively, restoring the primitives on rollback. Symptom: a step accepted with an 11 km/s cell in it. | fork |
| 2026-09-05 | 4f59088 | test and harness condensates given a physical reference internal energy. | fork |
| 2026-09-05 | e2e397a | the four python ctests listed in `SNAPY_PYTHON_TESTS`, so they import the tree under test. **The pin.** | fork |

Attribution, stated once so the rest of the report can be read without ambiguity. Two commits in that table are in upstream `main`, and they got there by different routes: `6cf0fae` (#195) is ours, merged upstream, and `bcbd07a` (#196) is the upstream author’s merge of Components A and B. Everything after `bcbd07a` is fork-only and ours. The one commit in the table by neither is `71f04ba` (#186), another contributor’s. The design of the scheme is ours, not the code developer’s.

## 5. Generation one — the limiter, and the implicit column flux

The first generation asked a simple question: should negatives be repaired after they appear, or prevented at the flux level? Repairing them after the fact had been the policy, and it was leaking mass in three distinct ways.

### The three defects it was built for

**D1, transport creates negatives**, by two mechanisms that need distinguishing. The first is reconstruction over- and undershoot: an unlimited polynomial puts a negative face value $y_{f}$ just downwind of a sharp cloud edge, and the resulting flux is a spurious *backward* flux that drains cells containing no tracer at all. The second is multi-face over-drain, where the sum of outgoing fluxes over a step exceeds the cell’s content. Under an acoustic CFL a fully explicit code cannot do this — the drain fraction per face is small by construction — but an implicit-Δt run steps far above the vertical acoustic limit, so the explicit vertical species flux can legitimately drain order-unity fractions of a cell per stage.

**D2, the repairs move or create mass.** Of the four repair sites, one teleports vapour vertically for numerical reasons and one creates mass outright. In the unit test’s base arm that creation was measured at +$1.8\times10^{-3}$ relative in ten cycles. Every repair site also has to get chemistry right, and that burden grows with each new reaction type.

**D3, the implicit species update neither conserves nor transports.** This is the subtlest of the three and the one with the longest history behind it. The implicit solve produces a per-cell correction to the total mass change, `diffusion_fix`, and the legacy code applied it to species pointwise and pro rata by the cell’s own mass fraction, `du += diffusion_fix * y_i`. That changes the column’s species mass by $\sum_i \mathrm{diffusion\_fix}_i\, y_i V_i \neq 0$ whenever y varies with height, which is always. Worse, it is *compositionally inert*: mass arriving in a cell takes that cell’s own y, so implicit vertical motion could not move a mixing-ratio contrast at all.

### Component A — the flux positivity limiter

Component A is the scheme of §3, applied to the species channels of the hydro and, through the same kernel, to the passive scalar. Its cost is about twenty-seven element-wise tensor operations on the species channels plus one thin ghost exchange per stage. There is no custom kernel: it is pure ATen, one source for CPU and GPU, and the outflow accumulation mirrors `CoordinateImpl::divergence` index for index so that θ is consistent with exactly the fluxes the divergence will apply.

### Component B — the implicit species column flux

Component B is the cure for D3, and it is worth stating in one sentence because the sentence is the whole idea: *convert the implicit solve’s pointwise correction into a face flux by removing the column residual mass-weighted, so that the increments sum to zero exactly.* Let $\phi_i$ be the mass the implicit solve adds to cell $i$ and $R = \sum\phi_i$ the column residual — the part of the correction with no flux representation. Removing it mass-weighted,

$$\phi'_i = \phi_i - R\, \frac{m_i}{\sum_j m_j}, \qquad m_i = \rho_i V_i,$$

gives $\sum\phi'_i = 0$ exactly. A zero-sum set of cell increments in a closed column is the divergence of a *unique* set of face transfers, obtained by one prefix sum with both ends closed by construction. Species are then moved by that flux, donor-upwinded, so conservation over the column is a telescoping identity — and, because the donor’s mixing ratio is what travels, implicit vertical motion finally advects composition.

Because the column pass is serial (it contains a prefix sum), it can afford something the explicit side cannot: exact running-availability bookkeeping, the ideal one-dimensional flux-corrected-transport limit. Sweeping bottom-up with the running availability of the lower cell, a transfer is clamped to what is actually there. The clamped transfer is still applied antisymmetrically to the two cells, so clamping reduces the amount moved without ever breaking conservation.

### What it measured

Three same-binary A/B experiments, all in the design report.

| experiment | base arm | limited / A+B |
|----|----|----|
| Unit A/B, 2-D slab 4×256, periodic in x2, unlimited cp5 reconstruction, Mach-0.05 wind, 10 cycles of rk3 — minimum vapour | −4.11e−4 | exactly 0.0 |
| … species total drift | +1.82e−3 | 2e−16 |
| … passive scalar drift | 2e−14 | 3.9e−16 |
| … θ firings | 0 | 880 |
| Case 14 silicate cloud, `implicit-scheme: 9`, 5000 s, 16 ranks, same binary — total mass | +9.7e−8 injected at condensation onset, then bled back | flat, \|Δ\| = 4.1e−13 |
| … wall clock | 126.95 s | 131.15 s (1.033×) |

The base arm’s species total *grows*, which is the point of quoting it: the transport negatives are converted into created mass downstream by kintera’s zero-clamp, so the unit test demonstrates D1 and D2 in one shot. Component A alone is identical to legacy in the mass budget — expected, since the limiter does not change total mass — and it is Component B that flattens case 14. The historically reported “residual sink of −$1.94\times10^{-7}$ per $10^{4}$ s” is, on this evidence, the decay slope of the onset injection inside the measurement window; B removes the injection and the decay together.

A separate 1000-cycle single-rank run instrumented the census: `positivity_hits` = 451,694, about 0.4 % of (cell, species, stage) entries. The limiter does real work in that case — implicit Δt makes explicit vertical drains legitimately large, mechanism D1(b) — while leaving the total mass and the flow statistics unchanged.

One consequence of Component B was flagged at the time and is worth repeating because it is a deliberate physics change, not a bug fix. With B on, implicit vertical motion advects composition, so trajectories decorrelate from legacy at the chaotic level: end-state kinetic energy differs by about 60 % after 5000 s while every conserved quantity agrees. Both flags therefore defaulted to `false`, precisely so the merge decision and the re-blessing decision could be taken separately.

### What merged, and what the merge changed underneath

What landed upstream is **`bcbd07a`, “Fix tracer positivity (#196)”, 2026-08-02**, which is an ancestor of `main`. An earlier branch commit, `3232080`, never landed.

Two things changed in the merge that outlived it. First, `bcbd07a` deleted the `positivity` and `implicit-species-flux` config keys: Component A now rides on `eos.limiter`, and Component B is unconditional whenever the implicit correction is active. The commit message still documents the deleted keys, and at the time there was no unknown-key validation, so a configuration that wrote them produced silence rather than an error. The general fix — reject unknown `dynamics` keys — is `4c30368` and is in the pin. Second, and consequently, *a same-binary A/B of A against no-A is no longer possible on the shipped code*. The flag is gone. Anything comparing “limiter on” against “limiter off” after `bcbd07a` is comparing `eos.limiter`, which also controls the density and energy floors and the shock-path clamps. That matters for reading several measurements later in this report and it is stated once here.

## 6. Generation two — the repair chain, and its own defects

With transport fixed, attention moved downstream. The repair chain existed to catch whatever transport produced, and it turned out that three of its four sites had defects of their own, and that the fourth — the step-rejection detector at the very end — had been made unreachable by the same flag that turns the limiter on.

### The condensate clamp created mass

When a tracer flux over-drains a cell, the condensate value goes negative; the mass is in a neighbour, not missing. Zeroing it with `clamp_min_(0.)` invents that mass one-way, and in silicate-cloud runs this was measured at 102 % of the total-mass drift — the entire drift, within measurement. The fix is a per-cell borrow: debit the deficit from the parent vapour or vapours in the same cell, by stoichiometric mass fraction, so that $\mathrm{NH_4SH}$ debits $\mathrm{NH_3}$ and $\mathrm{H_2S}$ by 17.03/51.11 and 34.08/51.11. That is exactly conservative in mass *and* in element, and being per-cell it means ghost copies receive an identical repair and ranks stay in sync. Same-binary A/B: +$1.2913\times10^{-5}$ → −$1.9458\times10^{-7}$ per $10^{4}$ s, a factor of 66; case 14 at $5\times10^{4}$ s, +$8.11\times10^{-5}$ → −$1.58\times10^{-8}$. Merged upstream as `6cf0fae` (#195).

### `fix_vapor` double-counted a cell

The columnar vapour repair scans top-down and, on finding a negative, accumulates vapour and dry mass downward until the running sum turns non-negative, then redistributes a common mass fraction over the cells it covered. Its accumulators were seeded with `vapor[is]` and `major[is]` and the first pass of the loop then added the same cell i again. The result is a one-way vapour *sink* on every fire. Zeroing the seeds makes the accumulation cover exactly the cells that are rewritten, so the redistribution conserves identically. It landed with the borrow, and the corrected reasoning is in the shipped source as a comment.

### kintera’s input clamp, and why it was demoted rather than fixed

kintera’s saturation adjustment zero-clamps a negative input concentration — silent, one-way mass creation. Its `return 1` is commented out, and both dispatch sites call the function as a bare statement and discard its value, so *every* error path in it is unreachable to the caller and `printf` is the only channel that works. That is still true at the pinned kintera, verified on 2026-09-06 at `equilibrate_uv.h:82`.

What decided its priority was a measurement rather than an argument, and the measurement is the sharpest statement in this report of what the limiter is *for*. In the moist seam harness, over 300 cycles, with the limiter off there were **263,433** kintera zero-clamp events; with the limiter on the clamp never fired at all. A quarter of a million silent one-way mass creations in 300 cycles, prevented. And at production scale the clamp does not fire either: zero events over 200 cycles on a moist run that both limits and survives, against a positive control of 1,169,871 in the same job with `limiter: false`, corroborated on decks 10, 11, 13, 14, 21, 32, 39, 40 and 42 and on a 106,983-cycle GPU card. That is what demoted this item and then closed it. One honest qualification: the GPU zeros in that dataset ride on device `printf` with no positive control, so the demotion rests on the CPU evidence.

### The detector at the end of the chain could not fire

`check_redo` is snapy’s step-rejection mechanism: if the state is unphysical, roll back and retry at half the time step. It tested exactly two things — conserved density at or below zero, and, through cons2prim, physical pressure at or below zero. Both are floored by `apply_conserved_limiter_`, density at line 166 and energy at line 190, after a `masked_fill_` that replaces NaN with zero at line 165. So under `eos.limiter: true` neither predicate can be true, a step is never rejected, and even a NaN blow-up is absorbed silently. This was proven from a run rather than argued: both predicates read *no* while eleven interior cells were being repaired.

The provenance matters, because it is not a regression and nobody introduced it. Two safety mechanisms with opposite philosophies were added independently and the second silently subsumed the first — `check_redo` says *reject and retry smaller*, the limiter says *substitute a floor and continue*. Both floors are upstream (`f7082a46` 2025-12-01 for density and `f252dcc9` 2026-02-11 for conserved energy); our `bcb8b41` (#188) landed five months later, fixed a different defect — an EOS referenced to 300 K has legitimately negative conserved energy below $T_{\mathrm{ref}}$, so the old check fired a fatal, halving-proof redo on a valid cold layer — and merely documented the deadness it inherited.

A second, independent defect sat in the same function. `check_redo` was **rank-local**: no collective anywhere in it, yet it decremented the cycle counter and bumped a local `current_redo` that `max_time_step` applies *after* its MIN-allreduce. One rank rolling back alone therefore desynchronises the run — and because the loop-exit predicate lives in pyharp and is purely rank-local too, the first rank to exit strands its peers inside a collective.

**The interlock, and why both were left standing for a month.** The blindness made the desync unreachable. `eos.limiter: true` was 41 of 45 configs and every 3-D global card, so wherever the rank-local decision existed it could not be taken. Fixing one without the other would have made the desync reachable. The production evidence for leaving them was substantial: 2,325,500 cycles — 6062 simulated days — with `redo = 0` throughout and a hydro mass drift of −$1.3\times10^{-10}$. If the floor were substituting meaningfully, that conservation would not hold. The obvious fix had also been tried and had failed: an environment switch that triggered a redo whenever the limiter fired cascaded 11 → 3 → 23 → 19 → 3 → 1512 cells over six redos and died at the same time as its control. Both were fixed together a month later; that is §9.

One further coupling belongs here because it is easy to miss: `limiter: true` disables *both* safety nets at once. The shock-path positivity clamps are gated on the same flag. The production configuration — `shock: true` with `limiter: true` — is exactly the corner in which those clamps are unreachable, and it ran for 6062 simulated days with no positivity failure. That was a decision, taken deliberately, not an oversight.

## 7. Generation three — seams, and the maximum principle

Everything up to here was measured on slabs. The cubed sphere has panel edges, where the ghost layer of one block is filled from a neighbour whose grid is rotated relative to it, and where the exchange therefore has to interpolate along the edge. Two independent defects lived there, and neither was visible to a mass total.

### Swapped states at a seam (defect one)

The passive scalar shipped both of its cross-panel reconstructed states under *one un-suffixed key*, where the hydro ships direction-suffixed keys `hydro_wl:+` and `hydro_wr:-`. The suffix is not decoration: it selects the directional send and receive whose mirrored skip rules resolve left from right across a panel edge. Un-suffixed, both halves travel both ways, so at a seam with a flip flag the left and right states arrive **swapped** and the upwind Riemann solver picks the *downwind* state. The result is an anti-upwind mode, one cell wide, along every seam — and it is *exactly mass-conserving*, which is why every conservation gate in the project passed over it. The fix is four lines.

This is the cleanest instance of observation (ii). A defect that conserves mass exactly is invisible to a mass gate, and every gate this project owned was a mass gate. What found it was looking at the mixing ratio rather than the total.

### The residual, and why the bound is on the update rather than the reconstruction (defect two)

With the seam fixed, the tracer still overshot: the maximum mixing ratio reached 1.143 where its bound was 1. The reason is that `weno5` is essentially non-oscillatory but *not* monotonicity-preserving; nothing about the seam was involved, and a one-key `plm` arm from the same restart held exactly 1.000000 for 51 frames.

The fix bounds the *update*, not the reconstruction, and it reuses machinery that already existed rather than adding a scheme. The observation is that r ≤ b is the positivity of the complement bρ − s, whose flux is $b F_\mathrm{mass} - F_s$. So the existing positivity limiter applies to the complement unchanged — a second θ, not the first — and the upper bound costs one config key, `scalar: upper-bound` (`scalar_options.cpp:22`). Scaling the complement blends the species flux toward the donor-cell flux of a tracer sitting at the bound, which is the right limit; scaling the species flux toward zero would bound it too, but would stop a plateau advecting.

**Two reconstructions were tried and deleted; do not propose a third.** `mp5` and `mono5` were both implemented and both removed, and the reason is the general lesson rather than a property of either: *a reconstruction sets face values, and the maximum principle is a statement about cell averages after the update.* Each shrank the violation without ever making it impossible.

Three conditions the bound rests on, all silent if violated, and all recorded rather than asserted away. The mass Courant number must stay below one, past which θ can leave a cell exporting tracer it does not have. Density must move by $-\Delta t\,\nabla\cdot F_\mathrm{mass}$ alone, which `implicit-scheme: 9` and any forcing writing `du[IDN]` both break. And the EOS limiter must be on, which the code checks with a `TORCH_CHECK` at construction rather than trusting the configuration. The GCM arm holds the bound anyway — but that is *empirical, not proof*, and the clean control is not constructible, because the card cannot run `implicit-scheme: 0` at all: the vertical acoustic CFL collapses its time step below the floor within about a minute.

One implementation detail is worth keeping because it is the kind of thing that is correct in algebra and wrong in arithmetic. Having limited the complement g, add the *change* (h − g) back to the species flux; never recompute $F_s = b F_\mathrm{mass} - g$. The two are equal in algebra only. Recomputing carries an error absolute in $b F_\mathrm{mass}$, so it perturbs *every* face even where θ = 1, and in float32 it annihilates the flux of a species whose ratio is near the epsilon of b. The shipped form is bitwise identity wherever nothing was limited.

### A donor factor that crossed the seam as a blend

The second seam defect is the one that breaks the invariant of §3 most directly. Both θ exchanges — the hydro’s and the scalar’s — used `interpolate(true)`. On the cubed-sphere layout the receive path then runs `interp_ghost`, which gathers along the panel edge with fractional weights at *every* ghost depth. A seam ghost of θ was therefore a **blend** of neighbour cells, not the donor’s factor. Wherever a tracer front met a seam, the two sides scaled the shared face by different numbers, and tracer mass appeared or vanished.

This was not a divergence between design and code. The design report’s §5.4 named the panel-edge exchange of donor factors as a documented follow-up — “T3” — to be done before cubed-sphere production use, and it was never done. It became load-bearing the day a passive tracer ran on the cubed sphere.

Measured, 300 cycles, 24 cells per panel edge, one-shot dye so total tracer mass must be conserved:

| geometry | before | after |
|----|----|----|
| tracer front inside a panel, six cells from any seam | −1.8e−14 | −1.8e−14 |
| front edge sitting on a seam | +1.52e−3 | −1.8e−14 |
| … its complement | −1.29e−4 | −1.8e−14 |
| plateau lying over a seam | +8.5e−4 | −1.8e−14 |
| cp5 reconstruction, front edge on a seam | +2.4e−3 | −1.8e−14 |
| any of the above with the limiter off | −1.8e−14 | −1.8e−14 |
| seam ctest | +2.0e−3 | 2.4e−15 |
| subdivided panels, 24 blocks | +8.1e−4 | −3.8e−15 |
| six MPI ranks | +9.2e−4 | −6.1e−15 |
| hot-Jupiter card restarted at day 10 with spun-up winds, six GPU ranks, 360 cycles (the limiter fires $9.7\times10^{7}$ times) | +4.76e−6 | −2.2e−14 |

The limiter-off row is the control that matters: with the limiter off, cross-panel transport conserves exactly as well as intra-panel transport. It is the interpolated ghost θ that breaks it, not the seam.

In physical terms the last row is about $6\times10^{-6}$ per simulated day of a dye, so a few parts in $10^{3}$ of the tracer mass over a 1000-day experiment.

**The fix** is `interpolate(false)` at both sites: the raw index-matched copy the hydro already uses for its reconstructed seam states. It works because `interp_ghost` interpolates only *along* the edge, depth by depth, so the raw copy at depth one is the neighbour’s edge-cell value — and the scaling reads nothing deeper than depth one.

The sign of the defect is structural rather than random: the far side applies too small a factor to an outgoing flux, so the tracer whose plateau is upwind gains and the one whose depleted side is upwind loses. A uniform tracer, which has no jump anywhere, never drifts. That is also the explanation for the awkward fact that an earlier hot-Jupiter measurement of the same quantity had come out seven orders of magnitude smaller, at −$2.3\times10^{-11}$: that dye covered \|lon\|, \|lat\| \< 80°, so every equatorial seam ran under its plateau with θ uniformly zero along the whole seam, and its band edges sat on the polar panels. *No θ jump ever met a seam.* The measurement was taken in a geometry in which the defect cannot appear.

### Three honest limits on the seam-factor result

**The census was wrong too.** Cells that are ghosts in x2 or x3 but interior in x1 accumulate real x1 outflow and can carry θ \< 1, so the old comment asserting that ghosts are exactly 1 at that point was wrong, and the count double-counted across ranks. An interior-only census is part of the fix.

**An adjacent hole the fix does not close.** On a cubed sphere with more than one block in the radial direction, the x1 ghosts of θ are neither exchanged nor overwritten. That configuration is disallowed — the cubed sphere requires one block in x1 — so this is recorded rather than fixed.

**The species path is not measured across a seam.** The hydro species path shows no seam signal, and the honest reason is that under a *limited* reconstruction the species θ essentially never departs from 1, because the reconstruction produces no undershoot to drain an empty cell. So the statement “the species path is fixed too” rests on the two call sites being the same code changed identically — *not* on a measurement. Every attempt to construct a species-θ-jump-on-a-seam test aborted in `fix_vapor` instead, and that abort is §8.

### Cross-species factors, and the partition

Two questions were opened alongside the seam and settled differently.

**Should species share one θ?** The literature’s answer for tracers bound by a linear constraint is yes — one shared factor over the constrained group. The decision rule here was fixed before measuring: adopt a group-shared θ only if the limiter’s increment to the sum-to-one residual is at least a tenth of what the reconstruction produces on its own. In-panel, 300 cycles: the reconstruction alone gives $1.206\times10^{-4}$; with the limiter, $1.206\times10^{-4}$, identical to four digits; with the upper bound, $1.041\times10^{-4}$, a 14 % *reduction*. Per-species θ stays.

Two facts sharpen why that answer is not surprising. θ is *scale invariant*, so proportional tracers already share it exactly and only tracers with different spatial structure can be limited differently. And per step the residual is bounded by (1 − θ) times the content of the depleting cell — a local composition error, never a global one. The magnitudes once quoted for this item, “a few percent” and “two to three orders in L1”, came from a *reconstruction*-limiter harness and not from this limiter; they are retired.

**The partition is open.** θ scales the species channel but not the momentum and enthalpy the Riemann solver built from the same mass flux. Throttling a species flux therefore converts that much species mass into dry air at the face. Energy is still *conserved* — the pressure face flux is single-valued — so this is a donor/receiver *mis-partition*, not a leak, and it is second order in the trace mass fraction. That is exactly why no gate saw it: every gate here is a mass gate. It is inert on the hot-Jupiter cards, which carry no species at all. Bounded, unmeasured, left open.

### Two instrument findings, and a build failure hiding behind a missing test

One instrument note was filed and closed the same day and is the clearest case of observation (iii). A uniform tracer appeared to deviate from unity by $7\times10^{-6}$ in a moving flow, and by exactly zero at rest. Three discriminators settled it, the decisive one being that the ratio formed against the *conserved* density is exactly 1 while the maximum difference between the exposed primitive and the conserved density equals the apparent deviation. **The primitive state exposed between `forward()` calls is one stage stale.** Both instruments now divide by the conserved density. That fact, filed as an instrument note, became the root cause of a detector defect a month later, which is §9.

Found on the way, and worth keeping for anyone reading cross-panel numbers: with no limiter at all, a tracer step crossing a seam overshoots to 1.051 at 12 cells per edge and 1.0016 at 24, against 1.00012 inside a panel. The cross-panel reconstruction from interpolated ghosts is substantially worse than the interior one; the upper bound hides it.

And the slab positivity test had never been registered with ctest at all. It and the new seam test are both registered now. A build failure had been hiding behind that gap: `git describe` picked up an `archive/…` tag on the pin, so every descendant’s `setuptools_scm` returned a non-version and `pip install` aborted. It was fixed by matching `v*` tags only.

## 8. Generation four — floating point

The fourth generation began with an abort message, `Failed to fix vapor mass fractions`, and ended by retracting a theorem. Two independent defects sat behind that one message, and a third was found by the review of the fix.

### The limiter could not deliver non-negativity, by construction

θ as written targets a post-update cell content of *exactly zero*. In exact arithmetic that is non-negative and the design report’s positivity bullet holds. But the update that follows is a cancellation, and its round-off is of order eps·avail, so an exact-zero target lands a hair *below* zero — and the repair layer downstream is handed a negative it cannot always fix. The consequence has to be stated plainly because it retracts something the 2026-07-31 report asserted by construction: **the limiter could not deliver non-negativity in floating point as written, and no improvement to the repair layer could have closed that.**

Measured: a deficit of −$1.7\times10^{-21}$ against a pre-drain cell content of $3.3\times10^{-5}$. That is eps·u·V to within a factor of four, which is what identifies it as round-off rather than a flux error.

The fix retains a margin of 4096 · eps(dtype) of the cell: $\mathrm{avail} = u.\mathrm{relu}() \cdot V \cdot (1 - 4096\,\epsilon)$. In double that is $9\times10^{-13}$, well clear of the round-off; it is strictly *more* restrictive than what it replaces, and it is exactly conservative because θ still scales a single-valued face flux — the conservation half of §3 is untouched. The margin is tied to the tensor’s precision deliberately: a fixed $1\times10^{-12}$ would be exactly 1.0 in float and would silently do nothing there.

The A/B against the unfixed build, on a 300-cycle moist cubed-sphere run, is the reassurance that this changes no physics: **every conserved total, drift and extremum bit-identical to fifteen significant figures**. The only difference anywhere in the run is about 2,000 fewer limiter clips out of 24.7 million, or $8\times10^{-5}$ — the cells that were being clipped right at the round-off boundary.

Two caveats belong with it. In float32 the margin is $4.9\times10^{-4}$, or 0.05 %, which is not negligible; no production card runs float32, so that branch is dormant, but it is a real number and it is listed among the open items. And 4096 is a magic constant: it is comfortably above the observed round-off and comfortably below anything physical, but a derivation would help a future reader and does not exist.

### The bottom cell was unrepairable, however small the deficit

The second defect behind the same message is independent of the first. `fix_vapor_impl` borrowed *downward only*. A negative in the *bottom* cell of a column therefore had nowhere to borrow from and was unrepairable however small it was and however much vapour sat above it. Measured: −$1.7\times10^{-21}$ in the bottom cell while the three cells above held +$4.4\times10^{-11}$, ten orders of magnitude more than needed.

Why the bottom cell reaches that state first is geometric: on a sphere the innermost shell has the largest surface-to-volume ratio, so any flux error there hurts most; the column profile follows a 1/r law to better than 0.1 %.

The fix is to reach upward once the downward scan is exhausted — as a bounded **transfer**, not a flatten. The distinction is the whole design. The downward branch flattens because it is a local mixing repair over the neighbourhood the limiter has just churned. Reaching upward, a flatten would move a window-*mean* amount of vapour to cure a round-off deficit: on a real moist column that is a spurious downward vapour pump, draining a large fraction of the cell above to repair a deficit twenty orders of magnitude smaller. Coverage is checked before anything is written, so an unrepairable column is reported *untouched*.

### The two fixes are complementary, and neither is redundant

This was measured one fix at a time on five harness arms, because a pair of plausible fixes for one symptom is exactly the situation in which one of them is usually unnecessary.

| arm | pin | upward repair only | margin only | both |
|----|----|----|----|----|
| five moist harness arms, cycles reached (target 300) | 1 / 3 / 14 / 3 on four of them | 300 / 24 / 27 / 26 | 1 / 300 / 300 / 300 | 300 on all five |

Each cures exactly the arms the other misses. With the margin in front, the upward branch is entered *only for denormals*: six records on one arm, the worst $9.6\times10^{-322}$, and it never fired at all on six of eight arms. Below about $10^{-300}$ a *relative* margin cannot exist, because denormals have no spare bits and avail·(1−margin) rounds back to avail. So the upward branch cannot move physically meaningful mass; it exists to keep an unrepresentable deficit from aborting a run.

### The failure that could not be reported

Found by the correctness review of the floating-point fix, and independently upstream-reportable. `call_fix_vapor_cuda` captured the host accumulator `all_err` **by value** into the device lambda, with the `atomicAdd` commented out. It therefore returned zero unconditionally, and the `TORCH_CHECK` behind “Failed to fix vapor mass fractions” could never fire on GPU: an unrepairable column was silently left with negative vapour. The earlier comforting statement that the condition “announces itself” was CPU-only.

Demonstrated on an A100 on the identical state: `PASS (cpu)` and `FAIL (cuda)` before the fix, `PASS` on both and on two independent nodes after. The CPU side had a milder cousin — `all_err += err` inside a parallel `for_each`, an unsynchronised read-modify-write that can drop a failure — now a `std::atomic<int>`.

The fix shape is dictated by the platform: `atomicAdd` is device-only, so `GPU_LAMBDA` cannot call it, and the counter has to be a device tensor accumulated from a `__device__` lambda and read back with `item()`. That costs one device-to-host synchronisation per `apply_conserved_limiter_` call, i.e. per RK stage per block. It is small, but it is new, and it is the price of being able to detect the failure at all.

The same pattern is worth auditing elsewhere and has not been. `bc_dispatch.cu` uses a `__device__` symbol with `cudaMemcpyToSymbol` and `cudaMemcpyFromSymbol` on the legacy stream, ordered against torch’s current stream only by luck. And in kintera, `equilibrate_uv` returns a real code that both dispatch sites discard, which is the same defect as §6’s clamp seen from the reporting side.

### The regime that exposed both, and what that means for production

The violent regime in which both defects fire thousands of times is the harness’s own `horizontal: {plm, shock: false}`. With `shock: true`, under either scheme, the limiter never fires in 300 cycles — and *every shipped moist card uses `shock: true`*, which is why the Neptune geEx case ran 660,000 cycles clean. So these are two real, latent defects, exposed by a non-production reconstruction setting that hammers them. Production reaches the same defects rarely — geEx’s minimum tracer value of −$1.6\times10^{-9}$ shows negatives do occur there — and survived by luck of geometry rather than by immunity.

The discriminators that established this are worth recording because two of them refute attractive stories. Moving the tracer hat off the seam is identical to baseline, so the seam is irrelevant to it. With no wind, nothing happens at all. With `shock: true`, the run is flat to cycle 300 with zero limiter hits. The drain of a factor of three per cycle is the harness’s reconstruction, not the seam and not the limiter.

One retraction of a retraction is worth carrying: the earlier reading that “an unlimited reconstruction empties the cell” was *right*. Only its `cp5` attribution was wrong, because the harness’s `--recon` switch sets the *passive tracer* scheme, not the vapour’s.

### An inverted latent heat in the harness itself

The harness condensate carried `cv_R: 9.0` and no `u0_R`, while its vapour had `cv_R: 3.5`. The latent heat at the reference temperature was therefore exactly zero and condensation was endothermic above it. This is observation (iii) again, and the fourth instance: part of the apparatus on which generations three and four were measured was itself wrong.

It was swept across 16 harness cards, 9 floating-point harness copies and 6 snapy test YAMLs, and — this is the part that mattered — the seam-gate A/B was **bit-identical** over the whole log, because that harness state never saturates. *No seam, element-budget or floating-point harness number moves.* That was checked rather than assumed. Prevention is a load-time warning in kintera when a reaction’s latent heat at $T_{\mathrm{ref}}$ is not positive.

The corrected criterion, which is easy to get wrong: `u0_R` is u/R *at* $T_{\mathrm{ref}}$ — the thermodynamics layer subtracts $c_\mathrm{ref}/R \cdot T_\mathrm{ref}$ later — so the latent heat at $T_{\mathrm{ref}}$ is the stoichiometric sum of `u0_R` over the reaction, and a bare condensate gives exactly zero. The quantity $\texttt{cv\_R}\, T_\mathrm{ref} + \texttt{u0\_R}$ is a different thing.

Finally, one element-budget miss that is *not* transport’s and should not be filed against it. A residual of −$3.597\times10^{-9}$ is present in *every* moist arm — on and off a seam, pinned and fixed — and it is real, not round-off. Its signature is the chemistry step’s: the cloud fully evaporates, the vapour gains, and the sum fails to close. It is re-scoped, most likely an artefact of the Mesh API driver the harness uses, and it does not reproduce in the shipped case 10 at the pin.

## 9. The detector at the end of the chain

The repair chain ends with a decision, not a repair: if the state is unphysical, reject the step and retry at a smaller time step. Three defects in that decision were carried as known-and-latent through generations two and three (§6) and were fixed together in `115efc2`, along with a fourth found by review before it shipped.

The three known ones were: the detector was blind under the limiter, because the limiter floors both quantities it tested; the decision was rank-local while the time step is global, so one rank rolling back desynchronises the run; and the rollback restored the conserved state but not the primitive, so the runner’s next `max_time_step` read a destroyed primitive, the time step collapsed to $10^{-180}$ s and the floor guard aborted — one genuine rescue, then a poisoned time step.

### The fourth defect: the detector was reading a stale array

This is the through-line from the stale-primitive instrument note of §7, and it is the reason that instrument note was worth keeping. `hydro_w` is written by the EOS at the *entry* of every RK stage and nowhere else. When the runner calls `check_redo` after the last stage, `hydro_w` therefore holds the primitive of the state at the entry of that stage — one stage stale. A cell floored in the last stage is invisible until the next cycle, and by then the saved rollback state is already the destroyed one.

The consequence was measured, not inferred, from the pre-explosion seed with the runner’s time-step floor set to 0.1 s. The stale detector **accepted** a retried step whose own primitive one stage later carried $|v_1| = 1\times10^{4}$ m/s; nineteen halvings to $4\times10^{-4}$ s could not then step past it. The fresh detector, on the same seed, **rejected** nineteen last-stage floors that the stale probe had called clean, and never committed one.

The fix is to recompute the primitives from the current conserved state *on a clone*, `peos->forward(hydro_u.clone())`, test both density and pressure against 1.001 times their floors, MAX-allreduce the flag so the decision is collective, and restore both `hydro_w` and the scalar primitive on rollback. It is bit-neutral where it should be: the no-op deck is bit-identical across all six ranks, and rescued events fire at the same cycles as before.

**Two corrections to the paragraph above, from the 2026-09-06 review.** Neither was known when this section was written, and both are fixed in the regrouped branch.

*“Collective” means across ranks, per block.* `MeshImpl::check_redo` loops over its blocks and each block issues its own allreduce, so block *i* on this rank pairs with block *i* on every other rank — and `MeshImpl::max_time_step` reads only `blocks.front()`’s redo counter. With more than one block per process a floor in one block therefore rolled back that block alone, and the time step was not halved. Production runs one block per rank, where the statement above is exact; the Mesh API is where it was not. The rank-level fix had stopped one level short.

*It was not bit-neutral for shallow water.* The rewrite dropped the `size(0) > IPR` guard that the previous code put around the pressure test, and `IPR` is 4 while a shallow-water state has four rows — so every shallow-water run that reached `check_redo` threw `c10::IndexError` from `115efc2` onward. No example deck is shallow-water and the C++ ctests had not been run since, so the full example-deck suite passed over it twice. `tests/test_shallow_xy` and `tests/test_shallow_splash` fail at `e2e397a` and pass with the guard restored. The claim of bit-neutrality was true of the decks that were tested and false in general — which is the difference between a no-op gate and a proof.

### What the retry can and cannot rescue

It cures the gentle events, at about 1 % wasted steps. It cannot cure an event that has already grown past recovery — the eruption class, where the eruption step itself passes the floor screen and the *next* one floors. A screen on the one-step pressure-loss fraction would catch that class a step earlier; it is not implemented. The distinction matters because after the fix the card still dies at the same cycle with the bound relaxed: the fresh detector is strictly better at not committing a floored state, and it does not make an unrecoverable mode recoverable.

One design decision was taken on 2026-09-05 and is recorded here rather than re-argued: an unrepairable vapour column stays a **hard abort**, not a redo trigger. It throws inside the stage, before `check_redo`, so a repaired retry could not catch it anyway; and with the margin of §8 in front, it can only fire on a genuinely broken state. Revisit only if a production run hits it.

A consequence of the rewrite worth stating plainly, because it was accepted rather than overlooked: `check_redo` is now a second place from which the vapour abort can fire, since it runs a full conserved-to-primitive conversion on its clone.

## 10. The code today, path by path

Everything below is verbatim from `e2e397a`. Each excerpt is preceded by one line saying what to read it for.

### The contract, in the header

This is the sentence the rest of the report is about, and it is where the ghost-fill requirement of §3 is written down. Note the last paragraph: the kernel gives ghosts θ = 1 and hands responsibility for their true values to the caller.

    //! \brief Per-cell positivity limiter factors for donor-form tracer fluxes.
    //!
    //! For each channel c and cell i, sums the outgoing (donor-side) flux over all
    //! faces of the cell exactly as the divergence will apply them,
    //!   out_i = sum_faces max(+/- A*F, 0),
    //! and returns
    //!   theta_i = min(1, u_i * V_i / (dt * out_i)),
    //! the largest uniform scaling of cell i's outgoing fluxes that cannot drain
    //! the cell below zero in one forward-Euler step of size dt. Applying theta of
    //! the donor cell to every face (flux_positivity_scale_) then guarantees
    //!   u_i + dt * du_i(transport) >= 0
    //! cell by cell. All shipped integrators (rk1/rk2/rk3: wght2 == wght1 per
    //! stage; rk3s4: wght2 <= wght1) form each stage as a convex combination of
    //! previous states and one full-dt Euler step, so per-stage limiting at the
    //! full dt preserves non-negativity of the stage updates as well.
    //!
    //! theta == 1 wherever the cell is not near depletion, so the high-order flux
    //! is untouched almost everywhere; conservation is exact because each face is
    //! scaled by a single factor shared by both adjacent cells.
    //!
    //! Ghost cells get theta = 1 here (their outflow sum is not computed); the
    //! caller must make donor factors single-valued at internal seams by filling
    //! theta's ghost layer the same way conserved-variable ghosts are filled
    //! (exchange + physical boundary functions) BEFORE calling
    //! flux_positivity_scale_.

### The factor

The accumulation mirrors the divergence index for index, so θ is consistent with exactly the fluxes that will be applied. The margin of §8 is the `(1. - margin)` on `avail`; the `where` guard is what gives ghosts, and any cell with zero outflow, a neutral 1.

    auto out = torch::zeros_like(u);

    // Accumulate the outgoing A*F over exactly the faces the divergence uses
    // (lower faces il..iu+1 per dimension; see CoordinateImpl::divergence).
    // For cell i, the upper face is index i+1 and drains the cell where the
    // flux is positive; the lower face is index i and drains it where the flux
    // is negative.
    if (flux1.defined()) {
      int il = pcoord->il(), iu = pcoord->iu();
      int nf = iu - il + 2;  // faces il..iu+1
      auto af = pcoord->face_area1(il, il + nf) * flux1.slice(DIM1, il, il + nf);
      out.slice(DIM1, il, iu + 1) +=
          af.slice(DIM1, 1, nf).relu() + af.slice(DIM1, 0, nf - 1).neg().relu();
          ...
    // theta = min(1, avail / (dt*out)) where out > 0; 1 elsewhere (in
    // particular in all ghost cells, whose outflow is not accumulated above --
    // their true factors arrive via the caller's ghost fill).
    // Stop 4096 ulp short of zero: an exact-zero target rounds negative (S93).
    double eps = u.scalar_type() == torch::kFloat
                     ? std::numeric_limits<float>::epsilon()
                     : std::numeric_limits<double>::epsilon();
    double margin = 4096. * eps;
    auto avail = u.relu() * pcoord->cell_volume() * (1. - margin);
    auto drain = out.mul_(dt);
    return torch::where(drain > 0.,
                        (avail / drain.clamp_min(1e-300)).clamp_max(1.0),
                        torch::ones_like(u));

### The scaling

Per face, the donor is selected by the sign of *that channel’s* flux, and only the faces the divergence consumes are touched.

    if (flux1.defined()) {
      int il = pcoord->il(), iu = pcoord->iu();
      auto f = flux1.slice(DIM1, il, iu + 2);          // faces il..iu+1
      auto th_lo = theta.slice(DIM1, il - 1, iu + 1);  // donor when f > 0
      auto th_hi = theta.slice(DIM1, il, iu + 2);      // donor when f <= 0
      f.mul_(torch::where(f > 0., th_lo, th_hi));
    }

### The seam fix, at the hydro call site

Two flags. `interpolate(false)` is the whole of the seam fix; the census on the line above is taken before the ghost fill and over interior cells only, which is the corrected instrument.

    auto theta = flux_positivity_theta(uy, f1, f2, f3, pmb->pcoord, dt);
    // census of interior (cell, species) entries, before the ghost fill
    auto cells = pmb->part({0, 0, 0}, PartOptions().exterior(false));
    _positivity_hits += (theta.index(cells) < 1.).sum();

    // Raw copy, never interpolated: the donor of a panel-seam face is the
    // neighbour's edge cell, and an interpolated ghost is not its factor.
    Variables tvars;
    tvars["hydro_theta"] = theta;
    SyncOptions topts;
    topts.interpolate(false).type(kScalar);
    pmb->exchange(tvars, topts);

### The second θ, and the add-the-change rule

The upper bound is the positivity of the complement, limited by the same kernel. The final three lines are the arithmetic point of §7: add the change, never recompute the flux.

    if (_flux3.defined()) h3 = (g3 = b * mf(DIM3) - _flux3).clone();

    auto theta = flux_positivity_theta(b * rho - u, g1, g2, g3, pcoord, dt);
    _positivity_hits += (theta.index(cells) < 1.).sum();
    flux_positivity_scale_(sync_theta(theta), g1, g2, g3, pcoord);

    // Add the CHANGE, never recompute F_s = b*F_mass - g. The two are equal in
    // algebra only: recomputing carries an error absolute in b*F_mass, so it
    // perturbs EVERY face even where theta is 1, and in float32 it annihilates
    // the flux of a species whose ratio is near the epsilon of b. This form is
    // bitwise identity where nothing was limited.
    if (_flux1.defined()) _flux1.add_(h1 - g1);
    if (_flux2.defined()) _flux2.add_(h2 - g2);
    if (_flux3.defined()) _flux3.add_(h3 - g3);

### The upward branch of the vapour repair

Bounded transfer, not a flatten; coverage checked before anything is written, so an unrepairable column is left untouched and reported.

    if (i < ie && sum_vapor < 0.) {
      // below is exhausted: take the shortfall from above, untouched on failure
      T deficit = -sum_vapor;
      T above = 0.;
      for (int j = is + 1; j < nx1; ++j) {
        if (major[j] <= 0.) return 1;
        above += vapor[j];
      }
      if (above < deficit) return 1;

      for (int j = is; j >= ie; --j) vapor[j] = 0.;
      for (int j = is + 1; j < nx1 && deficit > 0.; ++j) {
        T take = vapor[j] < deficit ? vapor[j] : deficit;
        vapor[j] -= take;
        deficit -= take;
      }
      return 0;
    }

### Both dispatchers

The CPU accumulator is an atomic because `for_each` is parallel. The CUDA counter lives on the device because `atomicAdd` cannot be called from a `GPU_LAMBDA`; the `item()` is the one synchronisation per call that the reporting fix costs.

    int call_fix_vapor_cpu(at::TensorIterator& iter) {
      int grain_size = iter.numel() / at::get_num_threads();
      // for_each is parallel
      std::atomic<int> all_err{0};

      AT_DISPATCH_FLOATING_TYPES(iter.dtype(), "call_fix_vapor_cpu", [&] {
        auto nx1 = at::native::ensure_nonempty_size(iter.output(), -1);

        iter.for_each(
            [&](char** data, const int64_t* strides, int64_t n) {
              for (int i = 0; i < n; i++) {
                auto vapor = reinterpret_cast<scalar_t*>(data[0] + i * strides[0]);
                auto major = reinterpret_cast<scalar_t*>(data[1] + i * strides[1]);
                int err = fix_vapor_impl(vapor, major, nx1);
                if (err) all_err.fetch_add(err, std::memory_order_relaxed);
              }
            },
            grain_size);
      });

      return all_err.load();

    int call_fix_vapor_cuda(at::TensorIterator& iter) {
      at::cuda::CUDAGuard device_guard(iter.device());

      // count failures on the device (S99: a host int captured by value never reported)
      auto nerr = at::zeros({1}, at::TensorOptions().dtype(at::kInt).device(iter.device()));
      int* nerr_ptr = nerr.data_ptr<int>();

      AT_DISPATCH_FLOATING_TYPES(iter.dtype(), "call_fix_vapor_cuda", [&] {
        auto nx1 = at::native::ensure_nonempty_size(iter.output(), -1);

        native::gpu_kernel<2>(
            iter, [=] __device__(char* const data[2], unsigned int strides[2]) {
              auto vapor = reinterpret_cast<scalar_t*>(data[0] + strides[0]);
              auto major = reinterpret_cast<scalar_t*>(data[1] + strides[1]);
              int err = fix_vapor_impl(vapor, major, nx1);
              if (err) atomicAdd(nerr_ptr, err);
            });
      });

      return nerr.item<int>();
    }

### The detector

The clone is the stale-primitive lesson made structural, the allreduce is the rank-local fix, and the restore of `hydro_w` and the scalar primitive is the third defect of §9.

    int MeshBlockImpl::check_redo(Variables &vars) {
      auto hydro_u = vars.at("hydro_u");
      auto interior = part({0, 0, 0}, PartOptions().exterior(false));
      TORCH_CHECK(vars.count("hydro_w"),
                  "MeshBlock::check_redo needs hydro_w to restore the primitives");
      // hydro_w is one stage stale: test the primitives as they stand
      auto w = phydro->peos->forward(hydro_u.clone()).index(interior);
      auto const &eos = phydro->peos->options;
      bool redo = w[IDN].min().item<double>() <= 1.001 * eos->density_floor() ||
                  w[IPR].min().item<double>() <= 1.001 * eos->pressure_floor();

      auto flag = torch::tensor({redo ? 1. : 0.}, torch::dtype(torch::kFloat64));
      std::vector<at::Tensor> flag_reduce = {flag};
      if (_playout->has_process_group()) {
        _playout->comm->allreduce(flag_reduce, c10d::ReduceOp::MAX);
      }

      if (flag_reduce[0].item<double>() > 0.) {

## 11. Validation ledger

The gates fall into three groups: unit tests that assert the property, a deck that asserts it end to end on a cubed sphere with MPI, and the full example-deck suite that asserts nothing here regressed. All are on the pin.

| gate | what it asserts | result |
|----|----|----|
| gtests `eos_limiter.*` in `tests/test_eos.cpp` | the columnar vapour repair: four tests on the upward transfer (it fires, it is bounded, it refuses a column in net deficit without writing, it declines a single-cell column) plus one asserting the downward branch is unchanged | 5/5 |
| `tests/test_flux_positivity.py` | the slab A/B of §5: base arm goes negative, limited arm does not, both conserve | PASS |
| `tests/test_flux_positivity_cubedsphere.py` | both arms conserve to $10^{-12}$ across a seam with a θ jump on it, and the limited arm fires | PASS |
| `tests/test_fix_vapor_reports_failure.py` | an unrepairable column is reported, on CPU and on CUDA | PASS (device-agnostic) |
| `tests/test_check_redo_floor.py` | a floor planted in the conserved state alone is detected, and both primitives are restored | PASS — and it fails on the pre-rewrite build, so it discriminates |
| `tests/test_implicit_advection_cfl.py`, `tests/test_shear_cfl.py` | the two time-step bounds added alongside this work | PASS |
| deck `45_tracer_seam_cubedsphere_cpu` | six ranks, 100 cycles, scored on the first and last tracer census lines | PASS |
| core / full example-deck suite on the pin | no regression | 15/15; 56/56, twice |

The seam case is scored as PASS if and only if the maximum relative drift is below $10^{-12}$ *and* the hit count is greater than zero — the second half matters, because a gate that passes when the limiter never fires is not testing anything. The threshold is fifty times the measured floor of $2\times10^{-14}$ and eight orders of magnitude below the defect it guards against. For comparison, the pre-existing x1 guard’s threshold of $10^{-8}$ would have passed the defective hot-Jupiter number and failed nothing.

**The gate that was itself broken.** Four of those python ctests were registered but not listed in `SNAPY_PYTHON_TESTS`, so under a `-DSNAPY_TEST_PYTHONPATH` build they imported whatever pip had installed rather than the tree under test — a false red against an older venv and a false green against a newer one. It was found by review and fixed in `e2e397a`, which is the pin. The rule that follows: any new `*_python` ctest goes into that list in the same commit that registers it. This is the third instance of observation (iii) and the one with the widest blast radius, because it silently affects every test result taken in that build mode.

## 12. Limits and open items

Each of these is a live row, and each is stated with what is actually known rather than with an intention.

**The mass and energy partition.** The limiter scales the species channel but not the momentum and enthalpy built from the same mass flux, so a throttled species flux converts that much species mass into dry air at the face. Conserved, mis-partitioned, second order in the trace mass fraction, invisible to a mass gate, inert where there are no species. Bounded, unmeasured, open.

**Linear constraints across tracers.** Per-species θ breaks a linear relation across tracers in the interior. One shared factor restores it to machine precision but costs orders of magnitude in L1 on a smooth tracer co-advected with a sharp one, because the sharp tracer’s factor throttles the smooth one. The literature (Gong et al. 2023) documents the identical problem and lists consistent multi-species advection as future work, so there is no drop-in fix to borrow. This is a decision to take *before* coupling chemistry, not after.

**The implicit solver’s density clamp.** A proposal, and nothing more: no snapy source was modified for it. The clamp alters density while momentum and energy are written from the solver two lines later, leaving a cell holding one solver’s mass and another’s energy. Because the clamp moves mass antisymmetrically, total mass conserves to the last bit and every gate passes — observation (ii) once more. It is a *different* clamp from the tracer limiter this report is about, and its own report says it has no bearing on the hot-Jupiter science-run blow-ups; where the species channels are absent, `flux_positivity.cpp` narrows to nothing and does not execute at all.

**float32.** The margin of §8 is $4.9\times10^{-4}$ in single precision. No production card runs float32, so the branch is dormant, but it is not harmless if one ever does.

**Multiple radial blocks on a cubed sphere.** θ’s x1 ghosts are neither exchanged nor overwritten there. The configuration is disallowed, so this is recorded rather than fixed.

**kintera’s input clamp.** Still a silent one-way mass creation with an unreachable error return, at `equilibrate_uv.h:82` in the pinned kintera. Demoted rather than fixed, on the measurement that it does not fire in production — which is a statement about the transport limiter in front of it, not about the clamp.

**The accuracy repair the literature makes a case for.** Every other flux-clip paper scales only the high-order increment *above an upwind base*, so their θ → 0 limit is donor-cell transport where ours is *no transport*: a fully limited face freezes. Skamarock measured that form as nearly free (L2 $5.26\times10^{-2}$ against $4.92\times10^{-2}$ unlimited). It is not done. The trigger for doing it is a measured “θ = 0 stalls a front” symptom, which the hits counter now makes countable.

**Two things explicitly not to borrow.** The trick of Zhang & Chen (2025) of limiting only the last Runge–Kutta sub-step is sound for their linearised RK3 and unsound for SSP-RK3, where every stage’s flux enters the answer. And Zhang–Shu’s Gauss–Lobatto rescaling costs a two- to fourfold time-step cut, which the design report already declined.

## 13. Upstream status

Two of the twelve commits are in upstream `main`: `6cf0fae` (#195, the condensate borrow and the `fix_vapor` seed fix) and `bcbd07a` (#196, Components A and B). The other ten are fork-only, all of them after `bcbd07a`.

They are listed here in the order they were written. Since 2026-09-06 the pull request does not present them individually: the branch was replayed as one commit per subject, and the eight commits of this report that concern tracer positivity — `5c61b39` the direction-suffixed cross-panel keys, `82410e3` the complement upper bound, `4b59cf6` θ single-valued across seams with both positivity tests registered, `5f8a7f2` the margin, `19b4766` the upward repair, `8c43cca` the CUDA and CPU reporting, `4f59088` the test thermodynamics and `115efc2` the `check_redo` rewrite — travel as the single tracer-positivity group commit, whose message lists them. Two commits this report cites belong to other groups of the same pull request: `3b7485a`, the well-balanced face-density floor, goes with the vertical-column group (it is the second half of `a84e68c` and is not a tracer-positivity change), and `e2e397a`, the ctest list, goes with the hygiene group alongside `4c30368`. Every sha above remains reachable through an archive tag.

## 14. Provenance, and what can still be reproduced

The x86 reference is snapy `e2e397a` with kintera `83e30f1`. The aarch64 build is held at snapy `4b802af` and kintera `033f385` by decision, and the two architectures therefore hold different halves of this report. This needs saying precisely, because it is easy to assume otherwise.

The arm build *has* generations one and two and the swapped-seam work: `bcb8b41`, `6cf0fae`, `bcbd07a`, `3b7485a`, `5c61b39` and `82410e3` are all ancestors of `4b802af`. It *does not have* `4b59cf6`, `5f8a7f2`, `19b4766`, `8c43cca`, `4f59088`, `115efc2` or `e2e397a`. In plain terms, a GH200 run today carries the limiter, the implicit column flux, the condensate borrow and the upper bound, but **not** the seam fix of §7, and none of §8 or §9: no positivity margin, no upward vapour repair, no CUDA failure reporting, and the old blind rank-local detector. That is the configuration in which the seam leak of §7 is live, and it is a GPU configuration, which is also the one in which an unrepairable column fails silently.

Source for reading: commit `e2e397a`.

**The run payloads have been reclaimed, and nothing here can be re-measured from frames.** In every case what was kept is the evidence: the per-species tracer census lines, the JSON summaries, the configs and the launchers. So this report quotes from recorded logs throughout, and anything that would need a rerun is listed in §12 as open rather than asserted.

## Appendix A — where this sits in the literature

Eight papers were read in full against this scheme, with equation and page references. The purpose of reading them was to answer two questions: is snapy’s θ a known object, and are the choices made around it the ones the literature would make. The answers are yes and mostly.

The taxonomy is what makes the design decisions legible, so it is worth stating first. Three families of bound-preserving limiter exist, and they differ in *what object is limited* and therefore in *whether anything has to agree across a seam*. A **flux clip** acts on the final face flux through a per-cell donor factor; conservation is carried by there being one factor per face; the seam requirement is that the donor’s factor be known on both sides; and there is *no Courant condition* on the guarantee, because outflow is bounded by contents by construction. A **reconstruction limit** acts on the face value before the Riemann solve; it needs nothing across a seam, but every member of the family carries a Courant condition. A **solution limit** acts on nodal values with the element mean pinned; again no seam requirement, again a feasibility Courant condition. **snapy’s vertical Courant number exceeds one by design**, because the vertical correction is implicit. That single fact eliminates two of the three families, and the seam requirement of the surviving one is the price — one raw ghost copy of a cell field per stage.

**Zalesak 1979** is the parent. Its P/Q/R construction forms, per cell, the incoming and outgoing antidiffusive fluxes, the room available to each bound, and the ratios $R^{+}$ and $R^{-}$; the face factor is then the minimum of the receiver’s $R^{+}$ and the donor’s $R^{-}$ (eq. 13). snapy’s θ is exactly $R^{-}$ with the lower bound set to zero. Zalesak’s multidimensional sums over all faces of a cell are what protect against the simultaneous-drain case that no dimensionally-split limiter can see — mechanism D1(b) of §5. And the rule that the seam defect of §7 turned out to be about is his: *exchange the derived factor; do not recompute it from ghost data*.

**Thuburn 1996** limits the interfacial mixing ratio rather than the flux, on an arbitrary grid, and its conservation statement is the same structural one used here: each face has only one value, so the update conserves irrespective of how the values are chosen. Two things in it bear on our choices. It names the simplification snapy uses — the same range at every outflow face — and declines to refine it. And its guarantee requires the sum of outflow Courant numbers to stay below one, above which, in its own words, the scheme “blows up quickly”. That is precisely the condition an implicit vertical step violates.

**Skamarock 2006** is the closest relative in structure. Its positive-definite renormalisation is the same per-cell scalar built from a cell’s outgoing fluxes. Its contribution to our open items is the accuracy point of §12: it applies the renormalisation only to the higher-order corrective fluxes above a first-order upwind partial update, and measures that form as nearly free — L2 of $5.26\times10^{-2}$ against $4.92\times10^{-2}$ unlimited. It also treats mass consistency as a precondition rather than an option. It says nothing about processor seams, multiple tracers or curvilinear grids.

**Blossey & Durran 2008** supplies the sharpest statement about multiple tracers. Its positivity pass (eq. 21) is a donor-cell-only, single-valued-per-face factor — structurally the same object as θ, differing in that it limits the high-order increment above an upwind base rather than the total flux. Its §4.5 is the direct hit for the cross-tracer constraint item of §12: linear tracer correlations survive a *monotonicity* limiter automatically, a *positivity* limiter breaks them whenever the offset is non-zero, and the remedy is to force the constrained species to share the minimum of their factors (eq. 43). A further point, which is an inference on our side rather than the paper’s: a donor-only factor reads nothing across the face, so it is the safe form at an interpolated panel edge, whereas a two-sided factor would need the neighbour’s state exchanged exactly as well. That is a reason to keep the upper bound as the complement trick rather than as a receiver-side factor.

**Zhang, Xia & Shu 2012** is the maximum-principle-satisfying discontinuous Galerkin machinery, including the system limiter that uses one factor for the whole constrained state. Its cost is the reason the design report declined it: the Gauss–Lobatto rescaling carries a provable-positivity CFL restriction that amounts to a two- to fourfold time-step cut against the production setting.

**Guba, Taylor & St-Cyr 2014** is the solution-limit family: a per-element quadratic program that finds the nodal field closest to the unlimited one subject to exact element mass and nodal bounds, at about 11 % over the unlimited scheme. Its relevance here is a warning rather than a method — any diffusion or damping applied to tracers but not to density breaks tracer–mass consistency regardless of the limiter, which is worth an audit of its own.

**Zhang & Chen 2025** is in the same LMARS lineage, and it is included because its trick is tempting and must not be copied: limiting only in the last RK sub-step. That is sound for their linearised RK3 and unsound for SSP-RK3, where every stage’s flux enters the answer. The paper is dry — no tracers, no moisture, no positivity statement — and its limiter is an accuracy device, not a bound-preservation device.

**Gong et al. 2023** describes a chemistry module for a finite-volume MHD code and says, once, the thing that matters to the cross-tracer constraint item: because reconstruction in passive-scalar advection is done independently for each species, the scheme does not conserve the relations between them, and consistent multi-species advection is listed as future work. There is therefore no drop-in fix to borrow, which is why that item is a decision rather than a task.

Source precedence throughout this report: the source at the pin, then a recorded measurement, then an earlier report. No number in this document was produced by this document; every figure is quoted from one of those, and where a number would be useful and does not exist — the species path across a seam, the magnitude of the partition error, the float32 branch in production — the text says so rather than estimating it.
