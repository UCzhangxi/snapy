> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# The tall-column instability: cause, fixes, and dead ends

Why a motionless, stably stratified column destroyed itself once it spanned enough scale heights — the cause, the two commits that fix it, the six wrong turns that were paid for along the way, and exactly which pieces ship upstream.

Consolidated 2026-09-01 from earlier reports written 2026-08-18/19 on the lid closure and on the cause. This document is the story a reader can follow, with the provenance corrected to the commits that actually ship.

**STATUS — CAUSE FOUND AND FIXED (2026-08-19), shipping upstream (2026-09-01).** The extent-scaling instability of tall resting columns traces to one object: the well-balanced x1 reconstruction decomposed *density* against a bottom-anchored isentrope that is wrong by orders of magnitude aloft, and the face positivity floor then substituted that reference at the reflecting top wall every step. Two commits repair it and are on the upstream-PR branch. Formal 3-D certification of the fix (the 50-day jet-scored run) was deliberately held; what exists instead is 6062 simulated days of stable 3-D production on the fixed code with mass conserved to $1.3\times10^{-10}$ (deck `guillot_f025_n74_longc3`, cycle 2,325,500). State which of the two you are claiming; they are not the same thing.

**Review banner, added 2026-09-06** (read against snapy `e2e397a`). The reference, the floor fallback and the stage-weighted implicit time step are as described at the tip. Three details. (1) “also repairs a latent circular-shift wraparound”: on the PR branch commit `3b7485a` replaces `where(dl > 0., dl, dsf)`; the `torch::roll` existed only in an earlier development commit, so the shipped commit introduces the edge-replicated shift rather than repairing one (the commit message carries the same mismatch). (2) “35/35 C++ tests at the branch tip, build of `4c30368`”: `4c30368` is commit 13 of 25 in the PR series, not its tip. (3) §5 “the face reference is the average of the two adjacent smoothed values” holds for every face but the first, which takes the cell’s own smoothed value (`hydro_ref_x1_impl.h:140-142`). Two sibling commits this report does not cover — `2a5064a` (the temperature-floor path) and `8fb8f34` (the bottom-face relaxation option) — have their own short report on column correctness (2026-09-06).

## Provenance — what shipped, what did not, and where every commit lives now

The fix was developed in August 2026, rebuilt into a PR-quality series twice (2026-08-28 and 2026-09-01), so most SHAs of the earlier reports are historical. This table is the authority. Never verify by SHA alone across lineages — verify by content (`git log -S'<operative line>'`).

| change | original commit | ships upstream? | current SHA on the PR branch |
|----|----|----|----|
| smoothed local density reference (the cause fix) | `00a456b` | **YES** | `a84e68c` — also removes the $(K_{\rm bot}, \gamma)$ bottom-to-top relay and its dispatch plumbing, which the local reference orphans |
| positivity-floor fallback → donor cell (the guard correction) | `4ac6efb` | **YES** | `3b7485a` — also repairs a latent circular-shift wraparound in the fallback |
| RK stage weight inside the implicit solve | earlier development commits (retired 2026-08-31) | **YES** | `4503df5` — see §3a for the honest framing of this one |
| lid closure ×8 (`Ap *= 8.`) | `5e39334` (retired 2026-09-01, archived under a tag) | **NO — superseded** | not on the branch; measured inert at rest once the cause is fixed; its retirement is an open item |
| log-mean pressure reference on every grid | `6e68da1` | **NO — quality item, not the cure** | not on the branch; a candidate for a separate upstream PR on its own merits (§3e) |
| shock-path positivity clamps | `1561bbf` | **NO — excluded** | not on the branch |
| fatal local-reference variant | `b2e2fda`, reverted by `e97db14` (history preserved under an archive tag) | NO — the measured counterexample, §3d | — |

Earlier validation builds (at snapy `5e39334`, `0379406`, `4ac6efb`, `00a456b`, `6e68da1`, `1561bbf`) are retired; any of them can be rebuilt from its sha.

## 1. What was observed

A motionless, unforced, stably stratified column tears itself apart in snapy once the column spans enough scale heights — no jet, no radiation, no geometry, one rank, seconds to reproduce. The hot-Jupiter deliverable was pinned at an 84–88-level model top (~$10^{-4}$ bar) when the science goal needs $10^{-6}$ bar and below. Five rounds of single-knob testing produced mutually contradictory results, because every one of them scored *survival*, which near the wall is close to a coin flip.

## 2. The instrument, and the two method rules it enforced

Survival was replaced by the one-step amplification matrix G: perturb one conserved variable in one cell (acoustically scaled), advance exactly one cycle, difference, repeat 5×nx1 times. $\rho(G) > 1$ settles stability with no survival criterion, the eigenvector says where the mode lives, and re-assembling with one term ablated attributes it. Built natively in snapy (one process, `gsnapy.py`), then as a numpy surrogate of the full explicit operator (`esurr.py`, validated to $10^{-7}$ elementwise against the compiled code) so candidates could be scored before any C++ was written.

Two method rules were paid for and are permanent:

- **ε-convergence is mandatory.** The finite-difference step contaminates $\rho(G)$ badly (25.0 at $\varepsilon=10^{-6}$ vs 7.42 converged, on the same column); an early "corroboration" between two numbers was coincidence at a contaminated step size. Everything quoted here is at $\varepsilon=10^{-8}$ with a second decade checked.
- **Rest gates cannot rank reference designs.** The fatal variant of §3d passed every rest-state gate and then destroyed a certified configuration in developed convection. The nonlinear ladder — with the certified 84-level rung as the decisive gate — must accompany every reference change. And $\rho(G)$ is a within-code A/B diagnostic.

## 3. The wrong turns, in order — each labelled, none deleted

These are why the final attribution is trusted: every plausible alternative was measured and killed by its own control, and two of the wrong turns produced correct, useful fixes for what turned out to be symptoms.

*DEAD END / PARKED*

**3a. "The stage composition is the defect" (2026-08-18).** The hypothesis was that passing the stage-weighted step $\beta_s\Delta t$, rather than the full step, into the implicit solve at every stage is the defect. Snapy never had this form: it already solved over the full step. Emulating the per-stage $\beta_s\Delta t$ form in snapy makes the linear rest metric slightly *worse* (1.796→2.302).

**What ships anyway, and why that is not a contradiction:** the PR carries `4503df5`, which moves snapy *onto* the $\beta\cdot\Delta t$ operator. In snapy it has a directional nonlinear signal (2/10 vs 4/10 completions, sign p = 0.07 — weak, and stated as weak), and its cost is unmeasurable. Linear rest metric slightly worse, nonlinear behaviour weakly better: both facts are true at once, and the commit message carries them.

*SUPERSEDED (correct fix of a symptom)*

**3b. The lid closure ×8 (snapy, 2026-08-18).** Snapy's single-stage implicit map is unstable on its own, eigenvector always the topmost cell. The reflecting-lid closure models the wall as a first-order mirror flux while the explicit scheme it corrects damps lid-cell vertical momentum ~4.4× harder; scaling the wall-face diffusion into its measured saturation plateau (`Ap *= 8.`, one operative line, plateau flat from k=4 to $k=10^{6}$) lifted the surviving column from 84 to 102 levels. Every part of that measurement stands. What fell was the *attribution*: the under-damping was not an independent defect but a symptom — the inflated wall impedance the closure was fighting came from the floor substituting a wildly wrong density reference at that face (§4). With the cause fixed, the ×8 is measured inert at rest (identical to six digits with or without it). It is **not on the PR branch**; its retirement is an open cleanup.

*RETRACTED ATTRIBUTION*

**3c. "Both walls are the vertical WENO5 shock path."** The lid-report ablation showed both modes vanish with `shock: false`, and for a day the shock branch was the declared root cause. Retracted: the shock path is a *correlate* — it is where the overshoot at the mirror-ghost kink happens to be produced — not the cause. The cause is what the floor substitutes when the overshoot fires (§4). `shock: false` itself was already known to be unusable: it moves the quiet-column wall a decade and kills the certified 84-level 3-D run at 1.79 d.

*FATAL — the counterexample that shapes the design*

**3d. The "principled" local reference (`b2e2fda`, reverted).** The obvious repair — make the density reference the local state itself, $\rho_{\rm ref} = p_{\rm ref}\,\rho/p$ — passed every rest gate and then killed the certified 84-level rung at 6.51 days, bit-identically on two independent nodes. Mechanism: a reference that tracks the instantaneous state exactly makes $\rho'/\rho \equiv p'/p$, so the entropy/buoyancy degree of freedom is absorbed into the reference and bypasses the high-order reconstruction entirely. Rest instruments are structurally blind to this class (a rest column has no entropy perturbations). This is why the shipped reference is *smoothed* — it must follow the column at large scales only — and why the nonlinear ladder is the arbiter for any future reference change.

*QUALITY ITEM, NOT THE CURE*

**3e. The log-mean pressure reference (`6e68da1`).** Using the logarithmic-mean cell-average pressure on every grid (exact for an exponential column) drops the rest-state seed 21× and makes the explicit map essentially neutral (1.0747 → 1.001–1.003). It is a genuine accuracy improvement, **not shipped in this PR** (the PR is scoped to the instability), and stands as a separate upstream candidate.

*REFUTED (single-knob suspects)*

**3f. Everything else**, each by its own control: more implicit diffusion everywhere (worse), flooring degenerate eigenvalues (worse), removing gravity from the Jacobian (much worse), removing the lid closure (worse — it is a stabiliser), the Riemann solver (hllc reproduces lmars to <1%), reconstruction order (plm is worse than weno5), explicit spin-up (saves nothing, kills a healthy rung), 1-D reduction (invalid instrument — the vertical timestep limiter is advective and unbounded at rest, and 1-D silently runs explicit).

## 4. The cause

With gravity on, snapy's x1 sweep decomposes pressure and density against hydrostatic references, reconstructs only the perturbations, and restores the references at the faces. The pressure side is constrained by the well-balanced property. The density reference is a free choice, and the shipped choice was a single isentrope anchored at the *bottom* of the column: $\rho_{\rm ref} = (p_{\rm ref}/K_{\rm bot})^{1/\gamma}$. On a stratified column that reference departs from the real density exponentially with height — as $\exp[(1-1/\gamma)z/H]$, measured 36× at 96 levels, 99× at 110, 204× at 120 — so the "perturbation" $\rho-\rho_{\rm ref}$ is a catastrophic cancellation, and the WENO5 reconstruction of it overshoots at the mirror-ghost kink of the reflecting top wall.

**The floor turns a bad reference into a wall.** The face-restore positivity floor fires at exactly one face in the production base state — the reflecting top wall — every step, and its fallback value was the reference's face density: ~200× the true value. The wall's acoustic impedance $\rho c$ is inflated ~14×. That single face is simultaneously the implicit lid mode (what the ×8 was compensating) and the explicit top-cell momentum mode (whose growth, ×3.5 per 10 levels, is numerically the growth of the reference error). One face, both modes.

## 5. What ships (the two commits, plus the stage-weight term)

**`a84e68c` — track the x1 density reference to the smoothed column.** $\rho_{\rm ref} = p_{\rm ref}\cdot s$ with $s$ a clamped 5-point binomial smoothing of $\rho/p$ along x1; face reference is the average of the two adjacent smoothed values. The smoothing width is a measured plateau, not a tuning (widths 3/5/7/9 agree to five digits; width 5 ships as the smallest member). The cancellation dies (median $|\rho'|/\rho$: 2.26 → $3.4\times10^{-4}$) while grid-scale entropy anomalies stay in the reconstructed field — the property whose absence was fatal in §3d. The global $(K_{\rm bot},\gamma)$ bottom-to-top relay existed only to keep the old isentrope single-valued across an x1-decomposed column; the new reference is local, so the relay and its plumbing through the dispatch layer are removed in the same commit rather than shipped dead.

**`3b7485a` — the positivity floor falls back to the donor cell.** A guard correction, and its message says so: it does not change how often the floor fires, only what it substitutes — a local first-order value instead of a reference that can be orders of magnitude off. Bit-identical wherever the floor does not fire. How to check the guard is not masking a defect: count substitutions per step, by face and by level; a rate concentrated on one wall face is a masked defect. Also repairs a latent wraparound (the old shift was circular, so index 0 would have received the density from the top of the column had the range ever widened).

**`4503df5` — the RK stage weight, applied inside the implicit solve.** The term of §3a, shipped with its honest framing: snapy's nonlinear signal is directional but weak, and it is scoped to the 3-stage integrator only.

## 6. What proves it

| gate | stock | fixed (shipped pair) |
|----|----|----|
| explicit $\rho(G)$, 96→160 levels, at the explicit dt | 1.07 → 6.69 → 23.1 → 76.9 (×3.5 per 10 levels) | 1.0747, flat to all printed digits 96=110=120=130=140=160 |
| implicit $\rho(M)$, same ladder | 2.26 → 4.03 → floor artifact | 1.2452, flat 96–160 (quoted as an extent-flat family only — not ε-converged; see §7) |
| nonlinear rest ladder, 10 d | 84 levels only | 84, 96, 102, 120, 140, 160 — all 10 d (140/160 need floors at the density regime, $10^{-20}$) |
| isothermal decks, 10 d | 45 OK / 50 dead 1.2 d / 60 dead 0.03 d | all 10 d; mass drift $-5.6/-3.8/-5.6\times10^{-14}$ |
| 3-D production (in lieu of the held certification) | — | 6062 simulated days, mass to $-1.3\times10^{-10}$ (deck `guillot_f025_n74_longc3`) |
| unit test | — | `tests/test_hydro_ref_x1.cpp`, updated in `a84e68c`, passes in the branch suite (35/35 C++ tests at the branch tip; build of `4c30368`) |

Numbers above are the run log's.

## 7. What is not established, and what is watched

- **Formal 3-D certification was held.** The claim on offer is the production evidence in §6, not a certification. The rest ladder is the reproducer, not the deliverable.
- **The implicit 1.245-family is not ε-converged** (the shock path is non-differentiable at rest); it is quoted only as extent-flat, never as a precise number. The principled cure if it ever binds (pentadiagonal assembly, scored 1.02 in the surrogate) is on record.
- **Non-normality still grows with extent** ($\|G\|$ rises 86→8657 from 96 to 160 levels while $\rho$ stays flat). Watched, not attacked.
- **The lid ×8 retirement** (`5e39334`) remains an open item.
- **Above ~120 levels, floors must match the density regime** ($10^{-10}$ clamps the true top density and voids the measurement) — a standing prerequisite for any work up there.

## 8. Artifacts and reproduction

    # one matrix, ~90 s on one CPU (overlay any snapy build on PYTHONPATH):
    RANK=0 WORLD_SIZE=1 python gsnapy.py --profile isothermal --nx1 50 --eps 1e-8 --tag demo --outdir /tmp/demo
