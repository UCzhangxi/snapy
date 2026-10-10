> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Limiting mass without limiting energy

The implicit vertical solver returns density, momentum and energy as one coupled answer. Since the tracer-positivity merge (#196), a safety clamp can alter the density on its way out while the momentum and energy are written from the solver untouched two lines later — leaving the cell holding one solver's energy and a different solver's mass. Because the clamp moves mass between neighbours antisymmetrically, total mass conserves to the last bit, so every gate this project owns passes. The clamp's own safety argument rests on a guarantee that is switched off by default, on both channels it protects. Proposed fix: stop repairing silently and start failing loudly.

**NOTE (added 2026-09-01).** Unchanged and still open: no fix for this defect is on the upstream PR branch (tip `4c30368`). Related but orthogonal: that branch now **rejects** unknown keys under `dynamics:` (`4c30368`), and kintera now rejects unknown `reference-state:` keys (`033f385`) — §15’s remark about silently-ignored configuration keys predates that validation work.

snapy `main @ 43e04fd` · defect introduced by `bcbd07a` (“Fix tracer positivity”, \#196) and unchanged since · companion to the tracer-positivity design report (2026-07-31), whose design the merged code is compared against · **revision 2** — independently reviewed against source 2026-08-25; four substantive corrections folded in, see §15 · 2026-08-25

**STATUS, added 2026-09-06 — still a proposal, and still untouched.** Nothing here was implemented, and none of the 2026-08 or 2026-09 tracer-positivity work touched its subject. The commits after `57e3fcd` — eight of them, not the nine an earlier draft of this banner claimed (review of 2026-09-06) — change the tracer *flux* limiter, the columnar vapour repair, `check_redo` and the two time-step bounds; this report is about the implicit solver’s *density* clamp (`vic.clamp`), which is a different mechanism. The defect it describes remains open and unmeasured.

Its subject is now recorded as an open item in the consolidated tracer-positivity report (2026-09-06) §12, which is the entry point for tracer positivity as a whole. The reference state is now snapy `61cebeb` with kintera `1f4f11b`, both replayed on 2026-09-06 as one commit per subject for the upstream pull request. Every sha named in this report stays reachable in the archived history. The banner below still applies verbatim, in particular the point that `flux_positivity.cpp` narrows to the tracer channels and does not execute at all on a dry card.

**⚠ STATUS BANNER, added 2026-08-25. Read before acting on this report.**

**1. This is a CORRECTNESS report and has NO bearing on the hot-Jupiter science-run blow-ups.** It was written while chasing the wrong "positivity". snapy's `flux_positivity.cpp` narrows to `u.narrow(0, ICY, ny)` — tracer channels only — and at `ny = 0` it does not execute at all, which is every dry hot-Jupiter science run. Thermodynamic positivity of $\rho$ and $p$ does not exist in snapy. The 3-D science configuration dies at 0.82 d for reasons measured separately, and none of them is in this document. **Do not read this as a stability lead.**

**2. The fix proposed in §8 was SUPERSEDED by a second independent review.** That review confirmed §6's top-face closure mechanism and closed its magnitude gap ($M_\mathrm{top}/m_\mathrm{top} \approx (|R|/S)\cdot(S/m_\mathrm{top})$, and $S/m_\mathrm{top}$ was measured reaching $1.7\times10^{16}$, so the observed 0.356 is what closure error predicts). It then found that the option-and-modes proposal is the wrong first move: §5.2's frequency argument transfers a statistic from the over-sensitive counter to a different population; the 2,865 events in the 147–172 band come in exact multiples of 128 (the column count), i.e. one domain-wide instant and a denominator artifact, not a limiter; and the residual population that could be a genuine clamp binding is **at most ~147 events in 1.7 million**. **The recommended action is instead the 12-line pass-2b crumb fix** — remove the top-face non-closure mass-weighted, exactly as R is removed one loop earlier — followed by rerunning the existing meter case, where `vic.max|dn-delta|/rho` collapsing to $\lesssim 10^{-12}$ versus staying O(0.1) separates closure from clamp with four clean orders of margin.

**3. Nothing here has been implemented.** No snapy source was modified.

**Problem.** When either availability clamp acts, the cell it acts on is left internally inconsistent: the solver's energy and momentum alongside a density that is not the solver's. Temperature and velocity are then wrong by roughly the fraction the density was altered by.

**Why nobody noticed.** The clamp is exactly mass-conserving whether it acts or not, and every standing gate in this project is a mass gate.

**Why the clamp is there.** Its design document justifies it as a backstop behind a guarantee — a separate component that makes negatives impossible upstream. That component is gated on a flag which **defaults to off**, so in a default configuration the guarantee does not exist and the backstop is load-bearing.

**Fix.** A binding clamp means the solver asked to drain a cell below empty. Treat that as the failure it is: detect, report, and stop — on both channels, by default. Keep today's behaviour available as an explicit mode so existing results stay reproducible.

**Honest limit.** We have *not* yet measured a clamp actually binding. The instrument used so far reports a downstream state difference, which has at least three possible causes — and the evidence currently points at one of the other two (§5, §6). Building the in-kernel counter is step one, not step five.

**Review banner, added 2026-09-06** (read against snapy `e2e397a`). Still a proposal; the clamp it analyses (`vic_redistribute_impl.h`) is untouched by all 25 commits of the PR series. Three corrections. (1) Line drift: the limiter guard cited as `hydro_forward.cpp:313` is at `:325` (313-323 is now a comment), and the two commented-out NaN guards are at `implicit_hydro.cpp:145-147` and `:207-209`. (2) The status box’s “nine snapy commits between `57e3fcd` and `e2e397a`”: eight follow `57e3fcd`, and two of them (`d9a1dbb`, `0452175`, the two time-step knobs) edit `implicit_hydro.{cpp,hpp}`, a file this report cites by line. (3) §2 “Component A is reached only through `hydro_forward.cpp`”: it is also reached from `scalar.cpp:158-162` and `:175-200` on any card with passive scalars, dry or not; and §7’s “no loud failure downstream” is partly stale since `115efc2`, whose detector rejects a cell at the floor with the limiter off too — with one gap, a NaN, closed in the 2026-09-06 series.

## 1. What this machinery is for

Start with the problem the merge was written to solve, because the defect is a side effect of an otherwise good idea.

Each timestep, the code moves material between cells by computing a flux across every face. A cell's water vapour goes up because vapour flowed in one side and down because it flowed out the other. The flux comes from a *reconstruction*: fit a polynomial through neighbouring cell values, evaluate it at the face. Near a sharp edge — the top of a cloud deck, say — that polynomial overshoots and can return a negative vapour value on a face beside a cell holding no vapour at all. Multiplied by the wind, that becomes a flux draining a cell that had nothing to give.

There is a blunter route to the same place. A cell holds a finite amount, and in one step the outgoing fluxes across all its faces can simply add up to more than it has. A fully explicit code cannot do this, because the CFL condition keeps steps short enough that a cell only loses a small fraction of its contents. But snapy solves the **vertical direction implicitly**, specifically to take steps far longer than the vertical acoustic limit. That protection is therefore gone, and a vertical step can legitimately try to drain most of a cell.

Negative densities are not merely untidy: in the equation of state they give a negative temperature or a NaN. snapy historically dealt with them afterwards, at four places downstream, the last of which simply set negative concentrations to zero and continued — which *creates mass from nothing*. The design document measured it: in a deliberately fragile test, total tracer mass *grew* by $1.8\times10^{-3}$ in ten cycles. The merge was meant to stop negatives being created rather than repairing them after the fact.

## 2. What the design proposed, and the guarantee it rests on

**Component A** clamps the *flux* rather than the cell. For each cell, add up how much of a tracer is due to leave across all its faces, compare with what the cell holds, and if the outflow is too large form one scale factor — a cell that can afford only 60 % of what is asked gets 0.6. Multiply each face's flux by the factor belonging to whichever cell is *donating* across it. Nothing can be drained below zero, and conservation is exact, because a face carries one number scaled by one factor.

**Component B** does the analogous thing for the implicit vertical solve. That solve returns a per-cell correction to the cell's mass. The old code applied it to each tracer pro rata: if a cell's mass rose 1 %, every tracer in it rose 1 %. That neither conserves nor transports — arriving mass takes the receiving cell's own composition, so implicit vertical motion cannot move a composition contrast at all. Component B turns those per-cell corrections into face transfers and moves each tracer by that face mass times the *donor's* mixing ratio.

Component B also carries a safety clamp: sweeping up the column, never move more across a face than the donor has available. **That clamp is what this report is about**, and its justification, §6.2, is one sentence:

> `avail_i` — **non-negative under Component A, which is why B is designed to run on top of A**.

So B's clamp is a *backstop behind a guarantee*. Component A has already made negatives impossible; in normal operation B's clamp should essentially never act.

### The guarantee is off by default

Component A is reached only through `hydro_forward.cpp:313`:

    if (options->eos()->limiter() && ny > 0) {

and `equation_of_state.hpp:52` reads `ADD_ARG(bool, limiter) = false;`.

**So in a default configuration Component A never runs, and B's clamp — on every channel — is operating with no guarantee behind it.** It is not a backstop. It is a load-bearing repair applied to the output of the solver.

This is the fact that decides the shape of the fix, and it applies equally to the tracer channels and the dry channel. There is no asymmetry between them to exploit.

### The scope the design drew

Both components were to touch **tracers only**. Section 6.3:

> The dry channel keeps its existing update verbatim… This keeps the diff surgical and leaves the MS-VIC dry/momentum/energy algebra — the dev's domain — **bit-untouched**.

Partly courtesy — the algebra belongs to the original derivation. But there is a physical reason too. A tracer mass fraction is a passenger. **The dry density is not a passenger — it *is* the density**, what the equation of state divides by to get temperature and what momentum divides by to get velocity. Both components also shipped switched off, and §10.4 explains: the defaults are `false` “precisely so the merge decision and the re-blessing decision can be made independently, per case.”

## 3. What actually merged

The change was reworked before merging. The flags were deleted — Component B is now unconditional, Component A rides the pre-existing `eos.limiter`, and `grep -rn 'species_flux' src/` returns nothing. And Component B was extended to the dry gas by a new *pass 3a*, carrying the same availability clamp, with no counterpart in the design document; the dry-mass repair the document promised to leave alone was deleted.

`vic_constituent_column` runs once per column. Pass 1 forms, per cell, the mass the implicit solve wants beyond the explicit update, accumulating a column residual `R`. Pass 2 removes that residual in proportion to cell mass so the remainder sums to zero, then prefix-sums it into a face transfer that telescopes to zero at the top. Then:

    // pass 3a — dry gas (new in the merge)                              :93
    T q = Mf > 0 ? Mf * dryfrac : Mf * dryfrac_up;
    if (q >  avail)     q =  avail;      // :106
    if (q < -avail_up)  q = -avail_up;   // :107

    // pass 3b — tracers (the design's pass 3), clamped identically      :115, :127-128

and the per-cell map writes the tendencies:

    DU(IDN, i)       += MASS(IDN, i);      // :144  dry density — clamped, flux form
    DU(IVX + dir, i)  = delta[i](1);       // :150  momentum    — raw solver, ASSIGNED
    DU(IPR, i)        = delta[i](4);       // :153  energy      — raw solver, ASSIGNED
    DU(ICY + n, i)   += MASS(ICY + n, i);  // :157  tracers     — clamped, flux form

Note the operators. Density and tracers *accumulate* an increment the clamp can alter. Momentum and energy are *assigned* the solver's output by a path no limiter can reach.

## 4. The defect

The implicit solver solves one coupled system for density, momentum and energy together and returns a **consistent triple**: this much mass, this much momentum, this much energy, and they belong to each other.

The merged code routes mass through a path a clamp can modify and the other two through a path it cannot. When either clamp acts, the cell ends the step with **the solver's energy and momentum but not the solver's mass**. The triple is broken.

The consequence follows from the definitions. Velocity is momentum over density; specific internal energy is total energy over density less the kinetic part; temperature follows from that through the equation of state. Give a cell an energy computed for one density and then a different density, and the temperature read back is wrong — by roughly the fraction the density was wrong by.

*That last step is an inference from the definitions, not a measurement. Quantifying it is test T2.*

### What “the clamp binds” actually means

Worth making explicit, because it decides the fix. The quantity the clamp tests against is

    T avail = (W(IDN, 0) * dryfrac + DU(IDN, 0)) * VOL(0);
    if (avail < 0) avail = 0;

— the cell's contents *after* the explicit update, floored at zero. **“The clamp binds” and “the density would have gone negative” are the same event.** A binding clamp is therefore not a routine flux adjustment; it is the solver reporting that it wants an impossible state. (The floor at zero adds a second case: if the explicit update *already* left the cell negative, `avail` is zero and every outgoing transfer binds.)

### Two smaller problems

**The decision cannot be unmade.** With Component B's flag deleted, the merge cannot be evaluated against its predecessor without rebuilding. (Component A is still switchable through `eos.limiter`, and snapy's own `tests/test_flux_positivity.py` exercises that A/B — so this applies to B alone.)

**The dry path has no test.** The design validates on one vapour plus one cloud (§9.1) and a silicate cloud case (§9.2). **Neither has `ny = 0`.** The dry path the merge created has no coverage of any kind and runs in every dry implicit simulation.

## 5. What is measured, and what is not

**No clamp binding has been measured.** The instrument used so far does not count bindings. It computes a downstream state difference, `rel = |DU(IDN) − δ(0)| / |δ(0)|`, and tallies how often that exceeds a threshold. A binding clamp is one possible cause of that difference. It is not the only one.

Three things can separate the density the code writes from the density the solver asked for:

1.  **Residual removal** — measured at $|R|/S = 4.88\times10^{-16}$. Negligible, and accounted for.
2.  **A binding clamp** — the hypothesis.
3.  **Top-face closure error** — overlooked in revision 1, and the subject of §6.

### 5.1 What the run reports

| quantity | value | what it is |
|----|----|----|
| `vic.max|dn-delta|/rho` | 0.356287 | largest discrepancy, as a fraction of cell density — one global maximum, not localised |
| `vic.|R|/summ` | 4.88332e-16 | residual removal: cause 1, negligible |
| `vic.clamp.material` | 6,091 | discrepancy \> 1 % *of the implicit increment* — not of cell density |
| `vic.clamp.any` | 2,008,625 | discrepancy $> 10^{-10}$; too sensitive to be meaningful |

**What survives.** The 0.356 maximum is far too large for any round-off mechanism, so *something* non-trivial happens at least once. That is the whole of what is currently established about magnitude.

**What does not survive.** The counter names are misleading and revision 1 took them at face value. Neither counts a clamp. And the `material` threshold is weaker than it sounds: it is 1 % of the *implicit increment*, a quantity whose own maximum in this run is `vic.max_rel_dn_vs_delta = 160.958` — so 1 % is a low bar, and nothing ties the physically-meaningful 0.356 to any particular one of the 6,091 events.

### 5.2 Where the events are, and why that is a warning

Of the 6,091 material events, **3,079 sit at level 179** — the topmost interior cell. Of the remaining 3,012, some 2,865 lie in the 147–172 band, 124 at levels 177–178 and 23 elsewhere.

Now the arithmetic that revision 1 should have done. At level 179 the `any` counter fires 1,695,895 times, against 128 columns × 4,459 cycles × 3 Runge–Kutta stages = 1,712,256 opportunities. That is **99.0 % of every stage-column at that level**.

A clamp is an emergency brake: it acts only when a cell is about to be drained below empty, which should be occasional and situational. Something occurring on 99 % of steps at one fixed location is the signature of a *systematic bookkeeping residual*, not of a limiter. Revision 1 used exactly this reasoning to demote the `any` counter, then failed to apply it to the level-179 half of `material`.

### 5.3 Mass is conserved exactly — which is the whole problem

Each clamped transfer is applied antisymmetrically: whatever the clamp declines to move out of one cell, it also declines to add to the neighbour.

    MASS(IDN, i)     -= q / VOL(i);
    MASS(IDN, i + 1) += q / VOL(i + 1);

Summed over a column closed at both ends, that telescopes to zero *for any values of q whatsoever*. Total mass is conserved to the last bit, clamped or not. Not itself a defect — it is the reason the defect is invisible.

### 5.4 Removing the clamp has already been measured as harmless

On an instrumented build (*not* in `main`), the gate `SNAPY_VIC_EXO_DENSITY=1` overwrites the density row with the solver's value and is therefore the clamp-inert dry channel to round-off at `ny = 0`. A leave-one-out campaign ran this as a *paired* A/B on ten shared initial conditions without realising what it was measuring: 4/10 completions with the clamp live against 6/10 with it inert, paired lifetime test 4–4, **p = 1.00** — not distinguishable.

This bounds the risk of changing the clamp's behaviour. It does not establish that the clamp ever binds.

## 6. A second finding: the top face does not close in floating point

The construction in pass 2 removes the column residual so the per-cell increments sum to zero, then stacks them into face transfers from the closed bottom upward. The arithmetic is arranged so that by the top face the accumulated transfer cancels *exactly*. That is true in exact arithmetic. In floating point the cancellation leaves a remainder, and the remainder lands entirely on the last cell:

$$\mathrm{DU}(\mathrm{IDN}, 179) - \delta_{179}(0) = -R\rho/S + M_\mathrm{top}/V_{179}$$

The important point is that **$M_\mathrm{top}$ is not bounded by $|R|/S\cdot\rho$**. It is an accumulated cancellation error over the whole column, so the residual measurement of $4.9\times10^{-16}$ says nothing about its size. Revision 1 asserted “no other candidate in the algebra” and was simply wrong.

This mechanism predicts a discrepancy that is present at level 179 on essentially every step, which is exactly what §5.2 shows. It is the leading explanation for the level-179 events, and it is plausibly a small defect in its own right — a systematic mass misplacement at the model top, in the same place the well-balanced-reference problem, the sponge and the reflecting top wall all live. It is conserved (the crumb has to come from somewhere), so once again nothing we own would see it.

Separating this from a genuine clamp binding requires an in-kernel counter. There is no way to do it from the outside.

## 7. Why nothing we own can see any of this

| gate | what it checks | sees it? |
|----|----|----|
| `masst` | total column mass | no — conserved exactly |
| design §9.1 unit test | tracer positivity and drift, `ny = 2` | no — never runs the dry path |
| design §9.2 case-14 A/B | `masst` on a cloud case | no — a mass gate |
| mass ledger | mass creation and destruction | no — mass again |
| rest-column instruments | a motionless column stays motionless | untested — the gap |

Every standing gate is a **mass** gate. Both mechanisms in this report move mass somewhere the solver did not ask for while conserving the total, and corrupt the state through the energy and momentum rows, which nothing checks against the density row. Same structural blind spot as an earlier tracer finding: “a donor/receiver MIS-PARTITION, not a leak, which is why no gate saw it: every standing gate here is a MASS gate.”

### And there is no loud failure waiting downstream either

This matters for the fix, because “remove the clamp so the failure becomes visible” is only sound if a visible failure actually follows. It does not. If a negative density is allowed through, one of two things happens:

- With `eos.limiter: true`, `apply_conserved_limiter_` (`equation_of_state.cpp:164-166`) runs `cons.masked_fill_(isnan, 0.)` and `cons[IDN].clamp_min_(density_floor)` on every conserved-to-primitive conversion. That floor **creates mass one-way** and is invisible to every gate above — the same defect class, moved one stage downstream and made *non-conservative*.
- With `eos.limiter: false` the function returns immediately, so there is no floor at all and the negative density reaches `sqrt(gamma*pres/dens)` → NaN. Both NaN guards in `implicit_hydro.cpp` (:126-128, :188-190) are commented out.

## 8. The fix

The clamp binds exactly when the solver has asked for an impossible state (§4). The right response to that is to stop, not to patch one of the solver's three coupled outputs and pass the other two through. And because §2 shows neither channel has a guarantee at default settings, both clamps get the same treatment.

### F1 — replace the silent repair with an explicit policy

One option, two modes, applied to **both** pass 3a and pass 3b. Nothing in any existing configuration file changes; the default applies automatically.

| mode | behaviour | when to use it |
|----|----|----|
| `abort` *(new default)* | a binding event is a hard error naming cell, level, channel and magnitude | everything; you never write this |
| `clamp` | today's merged behaviour, bit for bit | reproducing existing results; stage 1 below |

**A third mode was considered and rejected.** An `off` setting — no clamp and no abort, letting the state through — looks like a useful escape hatch but is strictly worse than either mode above: §7 establishes that what waits downstream is either a mass-creating density floor or an unguarded NaN. Its only function would be to produce a silently wrong answer, which is the thing this report exists to remove, and it would sit against the project's own direction on the floor-and-clamp inventory.

Three properties make this preferable to simply deleting the clamp, which is what revision 1 proposed:

1.  **It does not depend on the unmeasured claim.** If the counter shows the clamp never binds, `abort` changes nothing and closes a latent hazard. If it does bind, we learn so immediately and loudly. Correct either way.
2.  **It preempts the downstream absorber.** Stopping at the binding event means never reaching the state where a negative density falls through to the mass-creating floor of §7. Deleting the clamp without an abort walks directly into it.
3.  **It does not touch the algebra of the original derivation.** The momentum and energy path is unchanged, so the scope boundary the original design drew is respected.

It also restores the design document's own principle (§10.4) that the merge decision and the re-blessing decision stay separable, and it matches this project's standing position on the floor-and-clamp inventory and the design's own recommendation for kintera's zero-clamp (§7): a remaining negative “indicates an upstream bug rather than a state to be silently absorbed.”

### F2 — instrument the event, unconditionally

In all three modes, count and size every binding:

- `implicit_clamp_hits`, split by channel, registered exactly like the existing `positivity_hits`;
- `implicit_clamp_max`, the largest shortfall relative to the cell's own mass, so the magnitude is reported and not merely the count;
- the level, so §5.2's distribution can be reproduced from inside the kernel rather than inferred from outside it.

This is what separates a genuine binding from the top-face residual of §6, and it is the reason the rollout has two stages.

### Rollout

**Stage 1 — measurement, zero behaviour change.** Ship F2 with the mode set to `clamp`. No run changes in any way. Run T1–T3. This answers the question revision 1 assumed it had already answered.

**Stage 2 — policy.** Flip the default to `abort`, informed by stage 1. If stage 1 shows the clamp never binds and the level-179 signal is entirely the top-face residual, then §6 becomes the live defect and this report's centre of gravity moves with it.

## 9. What the fix does not touch

**The consistent-triple limiter.** The principled alternative is to keep the clamp and limit momentum and energy coherently alongside mass — build face-flux representations of those increments by the same prefix-sum construction pass 2 uses for mass, and scale all three together. Not proposed here, for three reasons: it is a redesign of the dry/momentum/energy algebra, which belongs to the original derivation and is the exact boundary the original design refused to cross; the energy increment is not decomposable into something advected, since it carries pressure work and gravitational coupling rather than enthalpy riding on the mass flux; and it would make a mask thermodynamically consistent rather than removing it, which makes the underlying failure harder to find.

**The top-face closure error** (§6) is diagnosed here but not fixed. If it is confirmed as the dominant mechanism it deserves its own treatment, most likely a compensated summation or an explicit zeroing of the top transfer.

**The two pre-existing hazards found along the way** (§7) — the mass-creating density floor, and the two commented-out NaN guards — are reported, not fixed. They predate this merge and are separate decisions.

Also untouched: Component A, the residual removal, the deletion of the old dry repair, the single-block assumption for implicit runs, and every other element of the merge.

## 10. Implementation

| file | change |
|----|----|
| `src/implicit/vic_redistribute_impl.h` | mode switch + counters at both clamp sites (:106-107, :127-128) |
| `src/implicit/implicit_dispatch.{cpp,cu,hpp}` | thread mode and counters through both paths |
| `src/implicit/implicit_hydro.cpp` | read the option |
| `src/hydro/hydro.{cpp,hpp}` | register the diagnostic buffers |
| `src/hydro/hydro_options.cpp` | the option, printed by `report()` |
| `tests/test_dry_positivity.{py,yaml}` | **new** — the missing `ny = 0` coverage |

    T q = Mf > 0 ? Mf * dryfrac : Mf * dryfrac_up;

    T over = (q > avail) ? (q - avail)
           : (q < -avail_up) ? (-avail_up - q) : T(0);

    if (over > 0) {                       // F2: always measured
      ++hits; max_over = max(max_over, over / (W(IDN,i) * VOL(i)));
      if (mode == kAbort) FAIL(i, level, channel, over);
      else                q = (q > avail) ? avail : -avail_up;   // kClamp
    }

Two notes for whoever builds it. The kernel is shared verbatim between the CPU loop and the CUDA dispatcher through the impl-header pattern, so counters must accumulate safely on both — follow `positivity_hits`, already a device-resident integer buffer — and a hard failure from inside a device kernel needs a flag-and-check-after pattern, not a throw. And `clang-format` runs in pre-commit and reformats: commit first, rebuild second, or the binary you cite and the source you committed will differ.

## 11. Testing

### T1 — a dry column at rest

A motionless hydrostatic column with no tracers. Nothing to advect; every m/s is discretisation error. The harness exists already — single rank, seconds per case. **The assertion is that the clamp must not bind:** a limiter has no business intervening in a column that is not doing anything. Run the height ladder, since §5.2 and §6 both point at the model top — quiet at 84 levels and firing at 120 localises it there and ties it to the well-balanced-reference problem.

### T2 — separate the two mechanisms, and size the consequence

With the F2 counters live, report per level: how often the clamp binds, how often `DU(IDN)` differs from the solver's value *without* a binding (that is §6's residual), and for genuine bindings the temperature error implied at fixed energy and momentum. This turns §4's inference into a measurement and settles §6 at the same time.

### T3 — paired A/B on the ten shared initial conditions

`clamp` against `abort` on the existing shared ICs with the perturbation off, scored with the existing paired scorer. No new campaign infrastructure. Score on the T2 meters as well as completion — the point is not lifetime.

### T4 — regression on the moist path

The design's own tracer test must pass across the change in `clamp` mode. And on a moist case, measure whether pass 3b's clamp ever binds — with `eos.limiter` defaulting off, §2 predicts it can, and that is the tracer-side half of the same defect.

## 12. Predictions

Stated in advance so the tests can fail honestly.

| \# | prediction | falsified if |
|----|----|----|
| P1 | the level-179 signal is mostly §6's closure residual, not clamp bindings | the counter shows genuine bindings on ~99 % of stage-columns there |
| P2 | genuine bindings are rare, and concentrated near the top when they occur | they are common and uniformly distributed |
| P3 | switching to `abort` is outcome-neutral on lifetime, per §5.4 | runs that completed now abort early — which would mean the model has been leaning on the clamp |
| P4 | the tracer clamp binds in default-configured moist runs (`eos.limiter: false`) | it never binds — then Component A's absence is harmless in practice |
| P5 | the implied temperature error is of order the mass displacement | it is orders smaller — the defect is real but immaterial |

**P3 is the one to watch.** If making a failure loud causes runs to stop that previously completed, that is not an argument for silence. It is the same as an earlier finding — that stability here is propped up by terms which are individually indefensible — and it would be reported, not reverted.

## 13. Status, and what the original derivation must settle

**Diagnosis:** the defect mechanism (§4) is established from source and independently verified. **Magnitude and frequency:** not established — see §5. **Fix:** designed, not built.

Two things rest on the original derivation. **The scope question:** the merge pushed a component past the boundary its own design declared and deleted the flag that made the choice reversible. That was deliberate, so there was a reason, and it is not recorded anywhere we can read — what the dry extension was for should be established before proposing a patch. **The consistent-triple option** (§9): if clamping is to be retained as a repair, the limiter has to act on mass, momentum and energy coherently, and that is a change to the original derivation.

What is ours regardless is **stage 1**: the counters, then T1 and T2. The missing dry-run coverage is a gap in our own instrumentation, the harness exists, and the result is evidence either way. **Do this before sending anything upstream** — revision 1 of this report would have sent upstream a frequency claim that the instrument could not support.

## 14. Reproduction

    # in a snapy checkout
    git log --oneline -1                                    # 43e04fd
    grep -rn 'species_flux' src/                            # empty — B has no flag
    sed -n '93,115p;140,159p' src/implicit/vic_redistribute_impl.h    # both clamps, the map
    sed -n '313,318p' src/hydro/hydro_forward.cpp           # A is tracer-only...
    grep -n 'ADD_ARG(bool, limiter)' src/eos/equation_of_state.hpp    # ...and defaults OFF
    sed -n '160,170p' src/eos/equation_of_state.cpp         # the downstream mass-creating floor
    sed -n '124,130p;186,192p' src/implicit/implicit_hydro.cpp        # NaN guards, commented out

    # the measurement (note: the SNAPY_VIC_EXO_DENSITY gate of §5.4 exists only on an
    # instrumented build, NOT in main); L = rank_0.log of the 2-D box meter case clamp_s1
    grep 'vic\.' $L | head -8

## 15. Changes in revision 2

Revision 1 was reviewed against source by an independent reviewer on 2026-08-25. The defect mechanism, the algebra, the conservation argument, the deviation from the design document and all six measured numbers were confirmed. Four substantive corrections were folded in.

| rev 1 claimed | corrected to |
|----|----|
| the clamp fires 6,091 times materially | no binding has been measured at all; the counters report a downstream state difference with at least three causes (§5), and the level-179 distribution points at §6 rather than at the clamp |
| the dry channel is unguarded, tracers are guarded by Component A → delete the dry clamp, keep the tracer one | Component A's flag defaults to `false`, so *neither* channel is guaranteed by default; both clamps get identical treatment (§2, §8) |
| $\mathrm{DU}(\mathrm{IDN},i) = \delta_i(0) - R\rho_i/S$ justifies the fix generally | that identity holds for the *channel sum*, and for the dry row only at `ny = 0`; deleting the dry clamp alone leaves the same defect on the moist path |
| remove the clamp so the failure becomes loud; strict mode optional | no loud failure follows — a mass-creating density floor or an unguarded NaN absorbs it (§7). Stopping must be the default, not an opt-in |

Also corrected: the claim that our decks carry silently-ignored config keys (no instance exists); the attribution of `SNAPY_VIC_EXO_DENSITY` to `main` rather than to the instrumented build; and the 147–172 band figure (2,865 of the 3,012 non-179 events, not all of them).

Source document — the tracer-positivity design report, §6.2, §6.3, §7, §9, §10.4.
