> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# A tracer that pumped itself across a seam

*and the residual underneath it*

The passive tracer broke its maximum principle by 20× on a cubed-sphere panel edge. Two defects, both now closed: the seam mode, its cause, fix and validation (§1–8, 2026-08-27/28); then the residual left underneath it, why §9’s verdict was overturned, and the two reconstructions that failed to close it (§9–18, 2026-08-29); and finally the bound on the update that does close it (§19–23, 2026-08-30).

**STATUS, added 2026-09-06 — both fixes are IN THE PIN.** The provenance map below ends at the PR branch; it now ends further on. Both commits are in the pin: the seam fix `5c61b39` and the upper bound `82410e3` are both ancestors of the x86 pin: snapy `61cebeb` with kintera `1f4f11b`, both replayed on 2026-09-06 as one commit per subject for the upstream pull request. Every sha named in this report stays reachable through an archive tag. Both are also in the aarch64 pin `4b802af`. In the regrouped series the two travel inside the single tracer-positivity group commit. §23’s provenance section, which describes them by their earlier development commits, is stale in that respect only — the measurements are unaffected. Neither is upstream; they are part of the pull-request series.

**Superseded as the entry point** by the consolidated tracer-positivity report (2026-09-06), which places both defects in the four-generation account of tracer positivity and carries the later seam fix and the floating-point work that came after. This report stands as the detailed record of these two defects, including the two failed reconstructions kept for the record; read the consolidated one first.

**PROVENANCE MAP (added 2026-09-01) — supersedes the per-section SHA corrections.** The SHAs in this report are one to two lineages old. Seam fix: `283b9df` → `bd412e9` → **`5c61b39`**; upper bound: `583a839`+`2b2a1d6`+`54e7f97` → `ab31dbb` → **`82410e3`** — both now on the PR branch (the status box’s “nothing is pushed” is out of date). Validation builds at `54e7f97`, `2b2a1d6`, `1f51f45` and (since 2026-09-01) `82410e3` are retired — all rebuildable from their shas. The development commits are retired under tags; the failed trials are preserved as tags at `1f51f45` (mp5) and `25dbe45` (mono5). §16’s 36/37 suite figure is historical — at the PR-branch tip the C++ suite is 35/35 and the python-test registration issue is closed. Verify by content, never by SHA: `git log -S'scalar_wl:+'`.

**STATUS, 2026-08-30 — CLOSED, both defects.** The seam mode (§1–8) was fixed on 2026-08-28; on the carried lineage that commit is `bd412e9`, *not* the `283b9df` named in §10. The residual (§9–12) is closed as of today by bounding the *update* rather than changing the reconstruction — **§19–23**. Two sections are deliberately preserved as dead ends and should not be read as current: **§13–16 are a failed trial** (`mp5`, see §17), and the candidate `mono5` that §13–17 point toward **was built, worked, and was then rejected** — §20 says why. **Nothing here is pushed or upstream. \[2026-09-01: superseded — both fixes now sit on the PR branch; see the provenance map above.\]**

**Review banner, added 2026-09-06** (read against snapy `e2e397a`). In addition to the provenance note above: (1) §22’s θ-interpolation paragraph — the limiter’s θ “exchanged with interpolation … inherited, not introduced” — is closed by `4b59cf6`, which makes both θ exchanges raw copies (`hydro_forward.cpp:341`, `scalar.cpp:144`). (2) §19/§22 “bounds a conserved quantity below at zero”: since `5f8a7f2` the limiter retains 4096·eps of the cell, so the complement bound enforces $r \le b$ to within that margin; every measurement here predates it, and the margin commit’s A/B is bit-identical on every conserved total. (3) §19’s one config key is the runner’s `chemistry.scalar-numerics.upper-bound`; snapy’s own key is `scalar: upper-bound` (`scalar_options.cpp:22`), and the two shared runners cannot set it.

## 1. The symptom

A passive tracer obeys $Dr/Dt = 0$. Its mixing ratio can never exceed the value it was given. In the ISSI Test 1 hot-Jupiter run it reached **19.665** against an initial 1, monotonically over fourteen simulated days, in 4837 cells, with no negatives anywhere. The field was not submittable and the defect was silent: every conservation gate in the stack passed throughout.

## 2. What it was not

Five mechanisms were excluded on evidence before the cause was found. They are recorded because each cost time and none should be re-derived.

| Candidate | Why it is out |
|----|:---|
| `_sanitize_scalar_state`'s `clamp_min(0)` | Nothing negative anywhere for it to lift; and `redo=0` on all 1728 cycle lines, so its step-loop call site never executes. |
| `apply_conserved_limiter_` | Never touches `scalar_s`. |
| the s↔ρ round trip | At the peak cell ρ is constant to 1.5 % while its *s* grows 57 %. Real tracer-mass motion, not a division artefact. |
| advective CFL | Re-derived on snapy's own gnomonic metric: in the offending cells the CFL sum is median 0.030, max 0.105. Five cells in 393216 exceed 0.5, all at *r* = 0. |
| the flux positivity limiter | Orientation-blind (see §4), so it cannot select 4 edges of 12. |

**And one retraction.** The defect was first attributed to WENO5 being non-monotone, on the strength of a 1-D reproducer reaching 18.37. **That reproducer used forward Euler; the card uses `rk3`.** Forward Euler is linearly unstable for any upwind-biased reconstruction above first order. Under SSP-RK3 the same harness gives **1.000599**, and a *smooth sine* with 250 points per wavelength and no discontinuity anywhere reproduces the blow-up identically — so the harness was measuring integrator stability, never boundedness. *Any 1-D tracer harness in this stack must use the same integrator as the card it reasons about.*

## 3. The measurement that found it

The extreme cells are not spread through the domain. They are a sheet one cell thick on a panel row, with the neighbour on the far side eleven orders of magnitude lower:

    x3 cross-section through the peak (day 405)
    0.9838  0.9823  0.9804  0.9776 | 19.66 | 3.487e-11  6.833e-10  9.893e-09

Depletion on one side, pile-up on the other, and the total conserved. Nothing was being created; tracer was being pumped back and forth across a single face.

## 4. The discriminator: orientation

The cube has twelve panel edges. `flip_flag = (my_side % 2) == (nb_side % 2)` (`cubed_sphere_layout.cpp:711`) is true on the four that join two sides of the same outward-normal sign: **1T–3R, 2T–3T, 2B–5B, 4B–5L**. Ranking all 24 half-edges by max *r*:

| half-edge | sign | max r | half-edge | sign | max r |
|----|----|----|----|----|----|
| 1T → 3R | SAME | 19.665 | 2L → 1R | opp | 1.225 |
| 3R → 1T | SAME | 4.414 | 4R → 0L | opp | 1.104 |
| 4B → 5L | SAME | 1.986 | 0L → 4R | opp | 1.037 |
| 2T → 3T | SAME | 1.626 | … all remaining opp ≤ 1.002 | | |

**Five of eight same-sign half-edges exceed 1.25; zero of sixteen opposite-sign ones do.** The hydro, measured the same way on the same frames, is *orientation-blind*: its seam jumps are $3$–$5\times10^{-4}$ with identical maxima in both groups.

## 5. The cause

`ScalarImpl::forward` shipped both reconstructed states under one *un-suffixed* key, `scalar_rlr`. The hydro ships `hydro_wl:+` and `hydro_wr:-`. That `:` suffix is not cosmetic: it selects a directional partial send/recv in `CubedSphereLayoutImpl::serialize`/`deserialize`, and the deliberately mirrored skip rules are what resolve the L/R roles across a panel edge.

With one un-suffixed key both halves travel both ways and take no directional branch. At a same-sign edge L and R arrive **swapped**, and the upwind solver (`riemann_solver.cpp:44`, `vel*(ui*wl + (1-ui)*wr)` with `ui = vel>0`) therefore selects the **downwind** state. That is an anti-upwind scheme on one face: unconditionally unstable, one cell wide, and exactly mass-conserving — which is why every conservation gate we own reported the code healthy.

The geometric transforms cannot rescue it. On the depth-1 strips these exchanges ship, `flip_flag` flips a *singleton* dimension and is a literal no-op, as is the transpose. The directional send/recv skip is the only mechanism that can resolve the reversal, and that is exactly what the un-suffixed key bypassed.

## 6. The fix

```diff
-  send_vars2["scalar_rlr"] =
-      rtmp2.view({2 * nvar(), rtmp2.size(2), rtmp2.size(3), rtmp2.size(4)});
+  send_vars2["scalar_wl:+"] = rtmp2[ILT];
+  send_vars2["scalar_wr:-"] = rtmp2[IRT];
```

and the same at the DIM3 site. Four functional lines in one function; no runner, config or card change. Buffer accounting is unchanged, because the skip rules leave exactly one key surviving in each direction — one buffer sent and one received per offset, as before.

## 7. Validation

Two runs from the identical day-391 restart, the identical config file and the identical runner. **The only difference is the binary.**

| day | max `r`, control (1dfcfe5) | max `r`, fix (283b9df) | n(`r` > 1.5), control | n(`r` > 1.5), fix |
|----|----|----|----|----|
| 391.02 | 1.000000 | 1.000000 | 0 | 0 |
| 392.02 | 1.005778 | 1.005779 | 0 | 0 |
| 393.02 | 1.014415 | 1.014405 | 0 | 0 |
| 394.02 | **2.476222** | 1.005008 | **5** | 0 |
| 395.02 | **4.075411** | 1.014481 | **18** | 0 |
| 396.02 | **6.509032** | 1.002051 | **31** | 0 |

Every frame is shown, and the *extent* is shown beside the peak, because a single frame’s maximum is one number from one cell and this project has been burned by reading a noisy peak. The extent tells the same story more strongly: the control has a growing *population* of violating cells and the fix has none at any frame.

The control reproduces the original run to five significant figures, so the harness is faithful. In the fix arm the spike never forms, the peak moves off the panel rows entirely, and the orientation signature vanishes: the same/opposite max ratio falls from **6.498 to 0.986**, with no same-sign edge above 1.05 where the control has two.

## 8. What the A/B does *not* establish

The two arms are not perturbatively close and were never going to be. At ~4 km s$^{-1}$ on an $8\times10^{7}$ m radius a parcel laps the planet several times a day, so by the first frame the arms already differ across most of the domain. These are **two trajectories**, not one trajectory with a seam repaired.

The conclusion survives that, because a maximum principle is an invariant that must hold on *any* trajectory — but the A/B alone cannot separate “the fix removed the violation” from “this realisation did not happen to violate”. What closes that gap is the mechanism derivation in §5 together with the localisation in §3–4: the control’s violating cells all sit on the seam row, the fixed arm has none there at any frame, and its residual sits on panel *midlines* instead. A five-day window also says nothing about recurrence later.

## 9. What remained — and why this section’s original verdict was overturned

The fix arm’s run maximum is **1.0145** (day 395), not the 1.0021 of its last frame — a ~1.4 % overshoot, off-seam, spread through the domain and not growing. An earlier draft quoted the last frame as though it were the residual and understated it sevenfold. Both arms sit at 1.0144 on day 393 before the control diverges, so the residual is present in both and is not something the fix introduced. It is the reconstruction’s own non-monotonicity, measured independently in the corrected RK3 1-D harness at **1.000428** with a held source, bit-identical at 1 000 and 40 000 steps.

**This section originally concluded that neither `plm` nor a limiter was worth adopting**, on two grounds: that a bounded, saturating overshoot is ordinary high-order behaviour well inside what the intercomparison resolves, and that *“a limiter added earlier would have masked this defect by capping the spike at 1 while tracer kept piling against the wall.”* **Both premises are now void** (2026-08-29). On the *corrected* ISSI card the residual is **1.14, not 1.014** — a hundred times the 1-D figure and ten times what was measured here. And with the seam defect fixed there is no longer a second defect underneath for a limiter to hide: §12 shows that changing one reconstruction key drives the violation to exactly zero, which is only true if the reconstruction is the sole remaining source. The masking argument was correct in 2026-08-28 and is not correct now.

**One provenance correction.** The fix commit named in §10 as `283b9df` is *not* in the commit series now carried. The equivalent commit on the PR branch is **`bd412e9`**, *“scalar: ship the cross-panel L/R states as direction-suffixed keys”*; the content is identical, the SHA is not. Verify with `git log -S'scalar_wl:+'`, never by SHA alone.

## 10. The residual on the corrected card is 1.14, and it saturates

The ISSI Test-1 dye was re-run on the *corrected* Guillot c32 card — right opacities, Guillot initial state — restarted at day 480 from a spun-up state on a build which carries the §6 seam fix. Twenty daily frames, one variable per frame:

| day | $n_{\rm plume}$ | n(r>1) | $n_{>1}/n_{\rm plume}$ | excess / inventory | max r |
|----|----|----|----|----|----|
| 481 | 26 211 | 327 | 0.0125 | 5.2e-05 | 1.087 |
| 483 | 39 302 | 1 020 | 0.0260 | 2.0e-04 | **1.143** |
| 486 | 67 663 | 1 564 | 0.0231 | 4.9e-05 | 1.033 |
| 490 | 112 915 | 1 869 | 0.0166 | 1.6e-04 | 1.108 |
| 495 | 156 352 | 2 564 | 0.0164 | 1.3e-04 | 1.119 |
| 499 | 184 724 | 3 065 | 0.0166 | 4.7e-05 | 1.048 |

Read the last three columns together. `max r` oscillates in a band 1.03–1.14 with no trend. The *violated fraction* peaks on day 483 and then sits flat near 1.7 %. The overshoot’s share of the dye inventory peaks at 2e-4 and *decays*. This is a bounded, saturated overshoot — qualitatively the same object as the 1.002 residual of §9, a hundred times larger in amplitude.

**Two readings of this run were wrong before the table was built, and both are instructive.** First, it was recorded as *decaying* (1.143 → 1.033) — that was frames 0–6 of a twenty-frame run, and 1.033 is one trough of an oscillation that climbs back to 1.130. Second, the raw count `n(r>1)` grows tenfold and was read as a ratchet. It is not: the plume itself spreads tenfold over the same window, so the count is tracking *front area*. Normalising kills the effect. *A count is not a severity until you divide it by what it is a count of.*

## 11. It is not the seam — measured over every frame, not the first few

`seam_census.py` on all twenty frames: interior max ≥ seam max at every frame but one; interior violations outnumber seam ones about 7:1 *and the two grow together*; no cell anywhere exceeds r = 5; the peak sits at an interior point, `(x1,x3,x2) = (35,26,3)`, and the cross-section through it is a smooth multi-cell bump rather than the one-cell anti-upwind spike of §3. The §4 orientation signature is absent. Whatever this is, it is not the seam mode recurring.

## 12. The discriminator: one key

Two arms from the identical day-480 restart, identical in every byte of configuration except `chemistry.scalar-numerics.reconstruct.type`:

| day | weno5 max r | plm max r    | weno5 n(r>1) | plm n(r>1) |
|-----|-------------|--------------|---------------|-------------|
| 480 | 1.000000    | 1.000000     | 0             | 0           |
| 481 | 1.087232    | **1.000000** | 327           | **0**       |
| 482 | 1.132387    | **1.000000** | 720           | **0**       |
| 483 | 1.142884    | **1.000000** | 1 020         | **0**       |

The `plm` arm ran on to day 530 — **51 frames, every one of them exactly 1.000000, with no violating cell at any point**. Not slowed: absent. In the earlier run the `plm` arm only *slowed* the pile-up, but that arm was fighting the unfixed seam bug underneath. With §6 in place, reconstruction order is the whole of what is left.

The objection to `plm` is that it buys the bound with numerical diffusion, corrupting the very mixing rate Test 1 exists to measure. Measured at day 499, nineteen days in: the fraction of dye inventory still in a sharp front (r > 0.5) is **0.7618 under weno5 and 0.7459 under plm** — about 2 % more smearing. Real, modest, and the price of dropping from fifth order to second.

## 13. Why the fix must be a limiter, and which one

**Godunov’s barrier settles the first question.** Any *linear* scheme that preserves monotonicity is at most first-order accurate. A bounded high-order scheme must therefore be nonlinear — solution-dependent — and every practical construction of that is a limiter somewhere. WENO’s adaptive weights already are one; they simply promise the wrong thing. *Essentially* non-oscillatory explicitly permits small overshoots. Zhang & Shu say so directly, and motivate their own work with this exact case: *“when u is a volume ratio which should not go outside the range of \[0,1\].”*

So the choice is only *which* mechanism and *where*. Two candidates were considered seriously.

**Zhang–Shu** gives a theorem, and was the initial preference for that reason. It was rejected on structure, not on merit. The construction needs a reconstruction *polynomial* on each cell, evaluated at N-point Legendre Gauss–Lobatto nodes, with the cell average written as a convex combination of interior node values and the two endpoints; the bound is enforced at every node. snapy’s `Interp` modules return a pair of face values and nothing else — there is no polynomial and there are no interior nodes. Adopting it means building a scalar reconstruction polynomial snapy has never formed: an architecture change, not a limiter. Its bound is also the *global* range of the initial data, weaker than the local maximum principle wanted here.

**MP5** (Suresh & Huynh 1997) fits the existing data structures exactly. It limits *interface values* — precisely what `Weno5Interp` produces. It reuses the same five-point stencil, so `nghost` is unchanged and **no new ghost exchange is introduced**, which matters more than usual here because the cross-panel exchange is where the seam mode lived. Its bypass test (2.30) is satisfied *a priori* by smooth data, so the limiter is inactive and costs nothing where the solution is smooth. And the paper is titled *Accurate Monotonicity-Preserving Schemes with Runge–Kutta Time Stepping*: it was designed for this pairing, the same pairing whose neglect produced the §2 retraction.

**CFL caveat, on the record.** The monotonicity proof requires $\sigma \le 1/(1+\alpha)$, i.e. 0.2 at the recommended $\alpha = 4$; the authors note 0.4 works in practice. The card sets `integration.cfl: 0.5`, but that is the *acoustic* number. The quantity the tracer proof constrains is the *advective* CFL, which §2 measured in the offending cells at median 0.030, max 0.105. Inside the bound, with room.

## 14. The fix — FAILED TRIAL, kept for the record

**§13–16 describe a trial that DID NOT WORK. Read §17 before acting on any of it.** `mp5` is correct, reviewed, tested and committed, and it does *not* fix the problem this report is about: on the GCM it removes ~75 % of the violating cells and essentially none of the peak (1.1428 → 1.1427). It is retained because it is a free strict improvement over the default at zero accuracy cost, and because the reason it fails is worth knowing. It is **not** the answer, and the method selection in §13 was wrong — see §17.4 for what the requirement actually selects.

A new interpolation type `mp5`: the WENO5 interface value with the Suresh–Huynh constraint applied to it, so the scheme keeps WENO5’s shock capturing and gains its monotonicity constraint. **220 insertions, zero deletions**, across `src/recon/mp5.cpp` (new), a class declaration in `src/recon/interpolation.hpp`, one `else if` in the factory, and `tests/test_mp5.cpp` (new). Nothing existing is modified or removed; unless a config names `mp5`, snapy runs exactly the code it ran before.

The limiter is written in device-agnostic ATen operations rather than the hand-written CPU/CUDA kernel pair the other reconstructions use. That deviates from house style deliberately: writing the same five-point index arithmetic twice is the shape of the bug that produced the seam mode, and the scalar path carries one variable, so the cost of tensor temporaries falls where it does not matter.

## 15. The bug in the fix, and the thing that caught it

The first implementation was wrong, in a way worth recording because *every physics metric approved of it*.

On a linear ramp — where (2.30) is satisfied with margin and MP5 must be a no-op — it collapsed WENO5 to the donor-cell value:

    w = 0,1,2,3,...      correct face value = k - 0.5

    weno5  L:  3.5  4.5  5.5  6.5      <-- correct
    mp5    L:  3.   4.   5.   6.       <-- clamped to the cell value
    mp5    R:  4.   5.   6.   7.       <-- clamped the other way

That is first-order accuracy everywhere, the exact opposite of the point. **And it made the headline number better.** An over-limited scheme is trivially bounded, so the 1-D harness reported `max r = 1.000000` — a *perfect* score, better than the correct implementation’s 1.000005. A boundedness test would have signed it off.

**Cause.** The stencil orientation in snapy is not symmetric and is not guessable from `mp5.cpp`. The `cm` coefficient rows in `weno5.cpp` are `(−1,5,2)/6` with linear weight **.3**, `(2,5,−1)/6` with **.6**, `(11,−7,2)/6` with **.1**. Matched against the standard left-biased Jiang–Shu split — whose weights are 1/10, 6/10, 3/10 — those are $p_2$, $p_1$, $p_0$: **the sub-stencils are stored back to front.** So `left` must read position $p$ as $v_{j+2-p}$, while `right`, built from the flipped coefficients, reads forwards. Both were inverted.

Read backwards on an increasing ramp, $v^{\rm MP}$ becomes $v_j$, the bypass test is always active, and `[vmin,vmax]` collapses to `[v_j−h, v_j]` — so `median` clips to the cell value. The algebra predicts the observed output exactly.

**What caught it was not a physics gate.** It was a gate comparing the C++ face states, field by field and side by side, against an *independently written* implementation of the same equations. That is why `tests/test_mp5.cpp` asserts **mp5 == weno5 on smooth data** rather than asserting a bound: the boundedness assertion passes on the broken orientation. The test was verified by reintroducing the defect — 4 of 6 cases fail with the wrong orientation, 6 of 6 pass with the right one.

## 16. Validation

**Face states, against an independent implementation.** Four fields × two `scale` settings × both sides, sixteen combinations, agreement to **0.000e+00** in every one; faces the limiter leaves alone are bit-identical to plain `weno5`; zero faces limited on a linear ramp.

**1-D advection, SSP-RK3, 4000 steps, cfl 0.4, top-hat, periodic** — measured with the compiled C++, not a prototype:

| scheme    | max r           | excess over the bound |
|-----------|-----------------|-----------------------|
| `weno5`   | 1.000599430     | 5.994e-04             |
| **`mp5`** | **1.000005061** | **5.061e-06**         |
| `plm`     | 1.000000000     | 0                     |

**118× less overshoot, and no accuracy cost**: on a smooth sine the L1 error against the exact solution is unchanged from `weno5` to seven digits, because (2.30) detects that the constraint already holds and leaves the value alone.

**Regression suite.** The test suite on the trial build: **37 tests, 36 pass**. The single failure is `test_eos_temp2inteng_python`, which is an artefact of the harness and not of any change — that test is registered with no `PYTHONPATH`, so its bare `import snapy` resolves to the *installed* package rather than the build under test. The suite is 37 rather than 36 because `test_mp5` is now in it, and it passes.

## 17. Why the trial failed, and what the requirement actually selects

### 17.1 The cubed-sphere A/B: mp5 does not close the magnitude

Three arms from the identical day-480 restart on the Guillot c32 cubed-sphere card, differing in one config key, all on CPU at the decomposition the restart was written with:

| day | weno5 max r | mp5 max r | weno5 n(r>1) | mp5 n(r>1) | front r>0.5, weno5 / mp5 |
|-----|-------------|-----------|---------------|-------------|---------------------------|
| 481 | 1.087232    | 1.086844  | 327           | **95**      | 0.9673 / 0.9675           |
| 483 | 1.142807    | 1.142686  | 1 021         | **254**     | 0.9364 / 0.9364           |
| 486 | 1.033086    | 1.033406  | 1 568         | **322**     | 0.8952 / 0.8956           |
| 488 | 1.073637    | 1.069095  | 1 694         | **686**     | 0.8719 / 0.8720           |

**mp5 removes about three quarters of the violating cells and essentially none of the peak** — 1.1428 → 1.1427, a 0.01 % change, against 118× less excess in the 1-D harness. Front sharpness is identical between the arms, so the improvement in extent is free; it is simply not the quantity that was the problem. `plm`, one key away, holds **exactly 1.000000 for 51 frames**.

### 17.2 The survivors are all at extrema, where MP5 declines to act

Suresh & Huynh guarantee monotonicity only where the five-point data are *monotone*; the enlarged interval (2.24) exists precisely to permit overshoot at extrema so that accuracy is preserved there (their Fig. 2.4–2.5). Testing the surviving violations against that condition (`extrema_test.py`) — the fraction of cells with `r > 1` whose stencil is monotone:

| day | n(r>1) | monotone x1 | monotone x3 | monotone x2 | monotone all three |
|-----|---------|-------------|-------------|-------------|--------------------|
| 481 | 95      | 0.063       | 0.063       | 0.232       | **0.0000**         |
| 483 | 254     | 0.000       | 0.134       | 0.370       | **0.0000**         |
| 486 | 322     | 0.016       | 0.044       | 0.360       | **0.0000**         |
| 488 | 686     | 0.018       | 0.099       | 0.416       | **0.0000**         |

**Not one violating cell, at any frame, sits on data monotone in all three directions.** In the vertical, where the gradients are sharpest, almost none are monotone at all. The peak cell is a local maximum in every direction simultaneously:

    peak cell (x1,x3,x2) = (34,13,52)   r = 1.06910
    x1:  0.05765  0.38775  1.06910  0.91175  0.36036    monotone = False
    x3:  0.66169  1.00130  1.06910  1.04704  1.01828    monotone = False
    x2:  1.06515  1.06728  1.06910  1.06882  1.06626    monotone = False

**MP5 is not failing; it is doing exactly what it promises, and what it promises is not a strict bound.** The 4× reduction in count is MP5 fixing every violation on a monotone stretch — its entire remit. The magnitude lives where the method deliberately stands down. It follows that no tuning *within* MP5 can close this, and the §13 selection was wrong: it optimised for fitting snapy's existing data structures rather than for the stated requirement, which was a strict bound on a mixing ratio.

### 17.3 Why the 1-D harness did not see it — and could have

The failure was the test field, not the dimensionality. A top-hat advecting in 1-D is monotone everywhere but two corners, and *advection preserves its shape*: it never develops new extrema, so the harness lived almost entirely inside MP5's guarantee. Shear and strain in three dimensions *manufacture* extrema continuously — filaments, folds, cusps — which is exactly the population the table above counts. A 1-D field full of extrema (a near-grid-scale wave, or a strained profile) would very likely have shown this in minutes. The hint was already present and unread: on *random* data the gate reported MP5 limiting 44 of 45 faces, and `max r` was never measured on such a field.

### 17.3b The 1-D test that would have caught it

The claim above — that the harness field, not the dimensionality, was the problem — is testable. Same rk3 harness, same 2000 steps, same cfl; only the initial field changes, ordered by the fraction of cells whose five-point stencil is *not* monotone:

| field | non-monotone | weno5 max r | mp5 max r | plm max r | mp5 gain |
|----|----|----|----|----|----|
| top-hat | **0.000** | 1.0005612 | 1.0000051 | 1.0000000 | **110.9×** |
| sine, 250 pts/wave | 0.016 | 0.9999984 | 0.9999984 | 0.9999605 | 1.0× |
| **sine, 32 pts/wave** | **0.190** | **1.0041192** | **1.0041192** | **1.0000000** | **1.0×** |
| sine, 8 pts/wave | 0.750 | 1.0000000 | 1.0000000 | 1.0000000 | exact |
| random in \[0,1\] | 0.992 | 0.9998030 | 0.9998030 | 0.9998030 | exact |

**The 32-points-per-wavelength sine is a one-line minimal reproducer of the GCM failure.** A smooth, well-resolved wave — no discontinuity, no shear, no seam, no geometry — overshoots by 0.4 % under `weno5`; `mp5` reduces that by *exactly nothing*, identical to seven digits; `plm` eliminates it. mp5's advantage collapses from 110.9× to 1.0× the moment extrema appear, and the GCM's violating cells are 100 % non-monotone. The two measurements are the same measurement.

**Acceptance test for any future tracer-boundedness claim in this stack: the 32 pts/wave sine, not a top-hat.** A top-hat has zero non-monotone stencils and advection preserves that, so it cannot exercise the case where every monotonicity-preserving method stands down. Reporting a 118× improvement measured on it was correct arithmetic and an unrepresentative field.

### 17.4 What the requirement actually selects

The literature has solved this. The apparent gap was a search failure: the first pass looked for the *methods already named* rather than for the *problem*, and found the two papers that matched the framing already adopted. Searching the same library for bounded transport instead returns the standard answers, several of which were sitting there the whole time.

**The real theorem is narrower than "you need a limiter."** Godunov's barrier says a *linear* monotonicity-preserving scheme is at most first order, so some nonlinear mechanism is unavoidable. What remains is a genuine trade-off *at a smooth extremum*, and every method is classified by how it resolves it:

| method | at a smooth extremum | fit to snapy |
|----|:---|:---|
| MP5 (Suresh & Huynh 1997) | **permits overshoot** to protect accuracy — the wrong side of the trade for a mixing ratio | drops into `Interp`; done, and it fails (§17.1) |
| PPM + Colella–Woodward (1984) | **clips** — flattens the parabola at detected extrema. Strictly monotone, 3rd order | drops into `Interp`; snapy already reserves a `ppm` slot, currently a stub that throws |
| Lin & Rood (1996) | clips; the flux-form semi-Lagrangian tracer standard | flux level, dimensionally split |
| Zhang & Shu (2011) | clips, but *provably without degrading the order* — a strict maximum principle | needs a reconstruction polynomial at Gauss–Lobatto nodes snapy never forms |
| FCT (Zalesak 1979) | clips; blends low- and high-order fluxes | needs only the two fluxes and cell bounds — all present |
| **LMARSpy (Zhang et al. 2025)** | **sharpness-preserving** monotonicity limiter — suppresses spurious oscillation while keeping sharp gradients | A-grid, LMARS, cubed sphere, GPU-ready |

**The strongest candidate is the LMARSpy limiter.** *LMARSpy: A GPU-Ready Nonhydrostatic Dynamical Core With a Sharpness-Preserving Monotonicity Limiter and a Conservative Vertical Implicit Solver*, *J. Adv. Model. Earth Syst.* **17**, e2025MS005056 (2025), doi:10.1029/2025MS005056. It is an A-grid LMARS cubed-sphere core, and its stated aim is exactly this problem: suppress unphysical oscillation *while preserving sharp gradients*. Read it before implementing anything else. **Second choice: PPM with the Colella–Woodward constraint**, which is strictly monotone, third order (against `plm`'s second), and drops straight into the `ppm` slot snapy has already reserved — a smaller change than `mp5` was.

§13's reasoning — that Zhang–Shu was structurally unavailable and MP5 was therefore the pick — had a true premise and a false conclusion. Zhang–Shu's cost is real, but it was treated as eliminating the whole *class* of extremum-clipping methods, when PPM/CW, Lin–Rood, FCT and the LMARSpy limiter all sit in that class and all fit. The selection optimised for the data structures already present rather than for the stated requirement, which was a strict bound.

## 18. What this does *not* establish

- **MP5 is monotonicity-preserving, not strictly bound-preserving.** Its interval (2.24) is deliberately enlarged near extrema — that enlargement is what preserves accuracy — and it permits a small overshoot exactly there. Hence 1.000005, not 1.000000. Suresh & Huynh guarantee monotonicity where the five-point data are monotone, and nowhere claim more.
- **Clipping the face states to the tracer’s physical range does not close that gap** — tested, 1.000005061 → 1.000004164. The residual lives in the cell averages after the update, not in the face values. Bounding face values is necessary and not sufficient without Zhang–Shu’s quadrature decomposition.
- **The 118× has not yet been shown to carry to the GCM.** A 1-D harness on a uniform grid is not a cubed sphere with stratified density.
- **The GPU path is unexercised.** The unit test’s four CUDA cases skip on a front end with no device. The ATen implementation is device-agnostic by construction, which is an argument, not a measurement.
- **The cost of `mp5` is unmeasured.** It adds one pass over the face array per direction per stage.

## 19. The residual closes by bounding the update, not the reconstruction

§13 argued that the fix had to be a limiter, and then went looking among *reconstructions* — mp5, then mono5. That framing was the mistake. A reconstruction decides what value sits on each cell face; the maximum principle is a statement about cell *averages after the update*. Choosing a better face value makes the violation smaller without ever making it impossible, which is exactly the behaviour §17 measured and then §20 measures again for a second scheme. The fix that works constrains the update directly and leaves the reconstruction alone.

The construction is one observation. snapy already ships a flux positivity limiter for the hydro species channels — `flux_positivity_theta` and `flux_positivity_scale_` in `src/hydro/flux_positivity.hpp` — which bounds a conserved quantity *below* at zero by scaling each cell’s outgoing face fluxes by a factor $\theta \le 1$. That machinery is one-sided, and an upper bound looks like a different problem. It is not. Write the complement

$$g = b\rho - s, \qquad G = b F_{\rm mass} - F_s$$

Then $r \le b$ is precisely $g \ge 0$, and $G$ is the flux of $g$, provided $\rho$ is itself updated by $-\Delta t\,\nabla\cdot F_{\rm mass}$. So the *same* limiter, applied unchanged to $(g, G)$, bounds the tracer above. The scaled complement flux is mapped back by $F_s = b F_{\rm mass} - G$. Because that map is a per-face affine expression in quantities that are already single-valued on a shared face, the result is still single-valued there — the scheme stays conservative *by construction*, which is the property this project insists on rather than bit-identical reconstruction.

What the scaling blends toward is worth naming, because the obvious alternative is wrong. Scaling $G$ down drives $F_s$ toward $b F_{\rm mass}$, which is the donor-cell flux of a tracer sitting exactly at the bound. Scaling $F_s$ itself toward zero would also bound it, and would stop a uniform plateau at $r = b$ from advecting at all.

The whole change is about 110 lines including its tests, adds no numerical scheme, and adds one config key, `chemistry.scalar-numerics.upper-bound`. It is a hard gate rather than a convention: because bounding one side while leaving the other free is a trap, the code `TORCH_CHECK`s that the eos limiter is enabled rather than assuming the config is sensible.

### 19.1 The identity that is not an identity — found by review, not by the A/B

The first implementation mapped the scaled complement back the obvious way, by recomputing the value: $F_s = b F_{\rm mass} - g$. That is exact in algebra and false in floating point, and the way it is false is the dangerous way. The error is *absolute* in $b F_{\rm mass}$, so it does not scale with the tracer flux it lands on, and it is committed on *every face on every step* — including the overwhelming majority of faces where $\theta = 1$ and the limiter was supposed to be a no-op. At $b = 1$ and $F_{\rm mass} = 2$:

| dtype   | tracer flux in | comes back as | relative error |
|---------|----------------|---------------|----------------|
| float32 | 1e-3           | 1.00005e-3    | 4.7e-05        |
| float32 | 1e-6           | 9.537e-7      | 4.6e-02        |
| float32 | 1e-9           | **0.0**       | **100 %**      |
| float64 | 1e-9           | 1.0000001e-9  | 8.3e-08        |

In float32 a species whose mixing ratio is near the epsilon of the bound has its flux annihilated to exactly zero. It stops advecting. There is no NaN, no assertion, and no conservation violation — the flux is still single-valued on the face, it is just wrong. This is the same shape of defect as the seam mode in §5: **exactly conserving, and exactly wrong.**

The fix is to add the *change* rather than recompute the value,

$$F_s \leftarrow F_s + (g_0 - g) \qquad \text{instead of} \qquad F_s \leftarrow b F_{\rm mass} - g$$

which is the same expression rearranged — both equal $\theta F_s + (1-\theta)\, b F_{\rm mass}$ — but is bitwise identity where $\theta = 1$, and confines the cancellation to cells where $r$ is genuinely near $b$. There, $F_s$ and $b F_{\rm mass}$ are the same magnitude and there is nothing left to cancel.

**Why neither the A/B nor 280 randomised harness runs caught this.** The dye sits at $r \sim 1$, where the round-trip is accurate, and the GCM arm ran in float64. Every instrument pointed at this fix was pointed at the regime where it works. The defect lives in float32 and at small mixing ratios — which is to say, on the GPU, in coupled chemistry, on the day someone advects a trace species. It was found by reading the code, not by running it, and that is the general point: **a validation suite built around one use case measures that use case, not the change.**

The same review found three smaller defects worth recording because each is a class rather than an instance. `upper-bound: 0` was admitted as a live bound; since $b = 0$ forces $\theta = 0$ on every face, a user writing it to mean “off” would have got a tracer that never moves, reported by `report()` as a perfectly innocent `upper-bound = 0`. It is now rejected rather than reinterpreted. The `TORCH_CHECK` guarding the eos limiter sat inside `forward`, so it fired once per timestep and killed a misconfigured multi-rank job after setup and I/O rather than at block construction; it now lives in `reset()` with its siblings. And the unit test asserted only the two bounds — which, as §19.2 shows, a limiter that does nothing at all also satisfies.

### 19.2 A test that a degenerate limiter passes

The test set the tracer moving on a spatially *uniform* mass flux, which is what makes it a clean fixture and also what defeats it. If the limiter returned $\theta \equiv 0$, every face flux would collapse to $b F_{\rm mass}$, uniform, whose divergence is exactly zero — so the field never moves, `max r` stays at its initial 1.0 and `min s` at 0, and both assertions pass. The reviewer traced two further degenerate variants, a flipped state complement and a flipped flux complement, that also force $\theta = 0$ and also pass.

So the test was sensitive to the *flag* — it does catch removing the limiter, since unlimited WENO5 climbs past tolerance within twelve steps — and had no purchase on the limiter’s content. This is the trap already warned about in the abstract, met concretely. It now asserts that the top-hat actually advected, that it advected *downstream* rather than merely diffusing, and that the uniform second channel was left alone; and it scales its tolerance by dtype, which matters because the suite instantiates float32 and the bound was being checked to 1e-12.

## 20. The candidate that lost: `mono5`

Between mp5 and the bound, a second reconstruction was built and did work: `mono5`, the Zhang & Chen (2025) blend of the donor-cell, 3rd- and 5th-order interface values weighted by the gradient-ratio limiter $\phi(r) = 2r/(1+r^2)$, which is 1 on locally linear data and floors to zero where consecutive slopes reverse. Unlike mp5 it is bounded at extrema, which is where every surviving violation lived. It cut the overshoot by roughly three orders of magnitude. It was nevertheless rejected, for three reasons of decreasing weight.

**It is a mitigation with no proof, and the authors say so.** Their §3.3 declines to claim monotonicity above second order, and the measurement agrees: the residual overshoot grows with Courant number, from about 3e-4 at cfl 0.70 to 4e-3 at 0.80, against the card’s 0.5. A card run closer to its stability limit would be less bounded, silently. The complement bound has no residual to grow.

**Its high order was largely decoration.** Measured convergence on smooth data was 1.83, against `plm`’s 1.76 — a five-point stencil delivering a two-point scheme’s accuracy, because the limiter is active almost everywhere that matters.

**It cost four times the code for less.** The commit is 236 lines and introduces a new `Interp` type into the library’s public vocabulary, with the naming problem that follows — `mono5` claims a monotonicity its own authors disclaim, and the reference implementation treats limiting as a flag across stencil widths rather than as a distinct scheme, so `type: cp5, limiter: 1.0` would have been truer than any new type name. That question is now moot. The branch and its build are deleted; the complete commit is preserved as an appliable patch, with the independent review it received beside it.

**The general lesson, since this is now the second reconstruction to lose the same argument.** A high-order reconstruction is the wrong instrument for a bound. Both candidates reduced the violation substantially and neither eliminated it, because neither constrains the quantity the principle is about. Estimate this class of work by the deliverable and not by the algebra: a new `Interp` type in snapy has now twice cost around 230 lines against a “15–30 line” estimate of the formula.

## 21. The A/B that decided it

Four arms from the identical day-480 restart on the corrected Guillot c32 cubed-sphere card, each differing from the control by one config line, all on CPU at 6 ranks — a restart can only be read at the decomposition that wrote it. `ub_bound` carries `upper-bound: 1.0` with the reconstruction left at `weno5`, so the bound is doing all of the work. The `mono5` arm was archived when the scheme was rejected.

**Which build these numbers are from.** The bound arm was re-run on the corrected build (§19.1) after the round-trip defect was found. Every statistic in the table below is *unchanged to four decimals* from the original pre-fix arm, which is what §19.1 predicts: the dye sits near $r = 1$ in float64, the regime where the round trip was accurate. The pre-fix arm is kept as the evidence for the before-and-after comparison at the end of §19.1, not as a result.

| day | weno5 max r | weno5 f>0.5 | plm max r | plm f>0.5 | mono5 max r | mono5 f>0.5 | weno5 + bound max r | weno5 + bound f>0.5 |
|----|----|----|----|----|----|----|----|----|
| 483 | 1.142807 | 0.9364 | 1.000000 | 0.9344 | 1.000736 | 0.9394 | **1.000000** | 0.9364 |
| 486 | 1.033086 | 0.8952 | 1.000000 | 0.8879 | 1.006447 | 0.8986 | **1.000000** | 0.8947 |
| 489 | 1.094429 | 0.8574 | 1.000000 | 0.8471 | 1.003233 | 0.8604 | **1.000000** | 0.8575 |
| 493 | 1.119853 | 0.8198 | 1.000000 | 0.8004 | 1.000539 | 0.8185 | **1.000000** | 0.8197 |

The bound arm was run **twice, independently, on two different compute nodes**, and the two agree **bit-for-bit in `r_dye` on all fourteen frames** — not to a tolerance, exactly. That is a real determinism result for this configuration, and it is worth stating what it does and does not cover: **both runs used the same thread count** (16 per rank). Thread count is not a neutral variable in this stack — pyharp’s longwave result is known to depend on it (a separate defect, found 2026-08-30 in a different workstream) — so this demonstrates reproducibility *at fixed threads*, not reproducibility in general.

Three things to read out of the table, in the right order.

**The bound holds exactly, on every one of fourteen frames, and nothing goes negative.** `mono5` does not: it still leaves between 35 and 58 violating cells per frame. But “max r = 1.000000” is what an *enforced* bound reads by construction, so that column is not the evidence that enforcing it was a good idea. It is only the evidence that the enforcement works.

**The evidence is the sharpness column.** `f>0.5` is the share of the dye inventory still sitting in cells above half-strength — how much of the plume is a front rather than a smear. The bound tracks unlimited `weno5` to within 0.0005 at every matched frame, which is the signature you would predict from a fix that never touches the reconstruction. `plm` is consistently blunter and gets worse with time, from 0.002 behind at day 483 to 0.019 behind at day 493 — by then it has demoted about 2.4 % of the inventory out of the sharp front. That is the real price of the workaround the card has been carrying, and it is the thing the bound buys back.

**`mono5`’s sharpness wanders rather than losing.** It runs *above* unlimited weno5 at days 483–489 and below it at 493. That is not a measurement of a better scheme; it is two runs of a chaotic flow diverging, because changing the reconstruction changes the trajectory. No sharpness claim either way is supportable from this A/B, and the case against mono5 rests on §20, not on this table.

## 22. What the bound does *not* establish

The construction in §19 is exact, and its premises are not.

- **ρ does not actually move by $-\Delta t\,\nabla\cdot F_{\rm mass}$ alone on this card, and the bound held anyway.** `implicit-scheme: 9` applies a vertical correction outside that balance, and so would any forcing writing `du[IDN]` — `plume_forcing.cpp:33` does. So the arm above is a demonstration that the conclusion survives a violated premise *on this card*, not a proof that it survives generally. The implicit correction here is evidently too small to matter; nothing measured says how large it may become.
- **The clean control is not constructible.** The obvious test — run the same bound with `implicit-scheme: 0` and isolate the implicit solver — cannot be run: the vertical *acoustic* CFL collapses dt under the runner’s floor within a simulated minute, which is exactly the job the implicit vertical solve exists to do. Lowering `integration.cfl` and the floor far enough would change the Courant numbers the bound depends on, so it would not be a clean control either. The honest and cheaper test is to perturb ρ outside the divergence term in the numpy harness; that has not been done.
- **The timestep these runs used was chosen by a routine that reads the ghost bands, so the Courant numbers quoted here are not exactly the interior values.** The runner’s radiative timestep limiter slices only the vertical and then takes a domain minimum, so **29.1 % of the columns it reduces over are halo** (a finding from another run, where it was fatal). Checked directly for these arms rather than assumed: the timestep varied only 2.1× across the whole run (94.6–200 s) with no unphysical-cell warnings, against a factor $10^{233}$ collapse in the run where it did bite. So no ghost cell here was badly enough corrupted to win the minimum. Whether a mildly corrupted one influenced it on some cycles is *untested* — the diagnostic that would say only prints on a normal exit, and these runs ended on the wall clock. Either way the effect is one-sided: the reduction is a minimum, so a bad cell can only make the timestep *smaller*, which makes the Courant condition below easier to satisfy, not harder.
- **The longwave radiation in these runs came from a code path whose answer depends on the CPU thread count.** pyharp’s longwave branch feeds an under-shaped array to a strided iterator, so the result changes with how the work is divided (found 2026-08-30 in a separate investigation, on the same pin these arms used; shortwave is unaffected, GPU is unaffected). It does not touch the conclusion here — a maximum principle holds on *any* trajectory, and every arm ran identical radiation at an identical thread count, so the A/B is controlled — but it is why the determinism statement in §21 is qualified, and it means the trajectory these arms followed is not the one a single-threaded or GPU run would have followed.
- **Mass Courant < 1 is a real condition and it fails silently.** Past roughly 0.854 the limiter can leave a cell exporting tracer it does not have. This card measures well inside, and nothing in the code notices if a future one does not.
- **Multi-species constraint drift is unfixed, and is not caused by this fix.** With several tracers under a linear constraint, a per-species limiter drifts the constraint by a few percent — `plm` does this too. One shared coefficient restores machine precision but costs two to three orders of magnitude in L1 on a smooth tracer co-advected with a sharp one. Moot for a single dye, live the day chemistry is coupled. This deserves its own issue, not a footnote here.
- **The implicit vertical mass correction runs *after* the limiter and is not bounded by it.** `MeshBlockImpl` adds its column transfer to the scalar tendency after `pscalar->forward` has returned, so the entire limiting apparatus — the pre-existing lower bound as well as this upper bound — sits upstream of it. It is a donor-cell transfer and so is bounded *iff* the per-face mass moved does not exceed the cell’s mass, but nothing checks that. The arm above held the bound anyway, so on this card the correction is small; that is a measurement of one card, not a guarantee.
- **On a cubed sphere the limiter’s θ is exchanged with interpolation.** At a panel edge the ghost θ is an interpolated value rather than the neighbour’s exact factor, so the two ranks may scale a shared face by different coefficients, which is precisely the single-valued-seam-flux property §19 leans on. This is inherited, not introduced: the hydro’s own limiter and the scalar lower bound already do it. The bound adds a second such exchange per stage and so doubles the exposure. A global tracer-mass budget on a multi-panel run, limiter on versus off, settles it cheaply.
- **The GPU path is unexercised for the bound.** The `plm` arm was run on both devices and agreed; the bound has only been run on CPU. The implementation is device-agnostic ATen, which is an argument and not a measurement.
- **Cost is unmeasured.** The bound adds a second limiter pass and a second θ exchange per stage.

## 23. Provenance

| item | where |
|----|:---|
| seam fix (§6) | `bd412e9` on the PR branch; originally `283b9df` |
| **the fix (§19)** | `583a839` + `2b2a1d6` + `54e7f97`, based on `a9e9447`. `54e7f97` is the §19.1 correction and **should be squashed into the first two before landing**. Unit suite 35/36 — the one failure, `test_eos_temp2inteng_python`, is a harness artefact: it is registered with no `PYTHONPATH` and so imports the *installed* snapy (2.10.5) rather than the build under test (2.10.6.dev15). **Not pushed.** |
| the deciding arm (§21) | `ub_bound`, against a build of `54e7f97`; the independent repeat is `ub_bound_repeat`. Pre-fix arm against a build of `2b2a1d6`, archived |
| mono5, rejected (§20) | `25dbe45`, build **deleted**; commit preserved as a patch |
| mp5 (§14) | `1f51f45`, based on `a9e9447` |
| the plm arm (§12) | the original GPU arm (51 frames) and the CPU arm in the §21 A/B |
| tools | `advect_1d_rk3.py` the corrected harness, `seam_census.py` the localisation, `extent.py` the normalised-extent statistic, a 280-run verification of the complement identity |
| papers | A. Suresh & H. T. Huynh, *J. Comput. Phys.* **136**, 83–99 (1997) — mp5.<br />X. Zhang & C. Chen, *JAMES* **17**, e2025MS005056 (2025) — mono5; source Zenodo 10.5281/zenodo.14936890, CC-BY-4.0. |
