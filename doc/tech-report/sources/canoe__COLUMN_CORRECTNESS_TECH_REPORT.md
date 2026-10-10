> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Two correctness fixes on the vertical column

Two commits found in August 2026 on the deep hot-Jupiter column are independent of the well-balanced reference that a companion report describes, and independent of each other. One makes the moist equation of state’s temperature-to-energy path return the internal energy it claims to return, so that the configured temperature floor actually binds. The other adds an option to relax the prescribed bottom temperature at the domain’s lower face, where a pressure level lives in a finite-volume grid, rather than at the first cell centre half a cell above it. Both are correctness fixes; the second costs stability on the one initial condition it was tried on, which is why it ships off by default.

Prepared 2026-09-06 against snapy `e2e397a`; every excerpt below is byte-identical at the current tip `61cebeb`, since the 2026-09-06 regroup and review fixes touched none of the files quoted here · two fork-only commits, `2a5064a` (eos) and `8fb8f34` (relax-bot-temp), neither upstream · companion to the well-balanced-reference report; in the regrouped branch (at `61cebeb`) these two are one group commit, `e00b246`, after the vertical-stability group · evidence: the two commit messages, which carry their own A/B measurements and are quoted here as such; `tests/test_eos_temp2inteng.py`; the hot-Jupiter card’s README; the only measurement made for this document is a re-run of that ctest on the pinned venv.

**The temperature-floor path.** `IdealMoistImpl::_temp2intEng`, the “UT→I” conversion, multiplied the species’ reference internal energies by the temperature and left out the dry gas’s heat capacity altogether. Its one caller is the temperature-floor clamp in `apply_conserved_limiter_`, which forms the minimum internal energy at the configured floor and clamps the conserved energy to it; with the energy under-reported by a factor of 88 on a realistic ice-giant species set, a configured 20 K floor enforced 0.23 K, i.e. the floor was not there (commit `2a5064a`). Nothing already computed was wrong because of it. Fixed by adding the offset instead of scaling it and including the dry term; `tests/test_eos_temp2inteng.py` pins the identity that was broken and the affine structure behind it.

**Where the bottom temperature is prescribed.** `relax-bot-temp` relaxed the first interior cell centre towards `btemp`. A bottom temperature is prescribed at a pressure level, which is the domain’s lower face; relaxing the centre half a cell above it drove the face 33 K above its prescribed value on a 2900 K hot-Jupiter column and made the forcing about 500 times stronger than it should have been at the start (commit `8fb8f34`). `at-face: true` relaxes the extrapolated face temperature instead. It is a correctness fix that costs stability on that one initial condition, so it is off by default and enabling it is a deliberate, validated choice; the hot-Jupiter card runs with it off and states its `btemp` as a cell-centre value for that reason.

**What is open.** The velocity and composition relaxations still act on the cell centre, so a card with `at-face: true` has an internally inconsistent bottom boundary; the commit says so. The option has no unit test of its own; its evidence is the same-binary A/B in the commit message. A paired multi-initial-condition A/B, which would settle whether the stability cost is general, has not been run.

## 1. The temperature-floor path returned the wrong energy

### What was wrong

The moist EOS computes internal energy per unit volume in two directions. The forward direction, “W→I” (`_prim2intEng`), forms $p f_\sigma / f_\epsilon / (\gamma_d - 1)$ and then *adds* the reference offsets $\rho_d u_{0,d} + \sum \rho_y u_{0,y}$; the inverse subtracts them before forming the pressure. The temperature path, “UT→I”, is supposed to give the same quantity at a prescribed temperature. It built

$$(\rho_d u_{0,d} + \sum \rho_y u_{0,y} + \sum \rho_y c_{v,y}) \cdot T$$

which is wrong twice. The offsets are energies per unit mass, not heat capacities, so they belong outside the temperature factor; and the dry channel’s $\rho_d c_{v,d} T$ was missing, which is the larger error because it is the dominant term of a mostly-dry column. On a realistic ice-giant species set the function returned 1.1 % of the true internal energy (commit `2a5064a`).

### Why it was silent

“UT→I” has exactly one caller: the temperature-floor clamp in `EquationOfStateImpl::apply_conserved_limiter_` (`equation_of_state.cpp:186-190`), which forms the kinetic energy, calls “UT→I” at the configured `temperature-floor` and clamps `cons[IPR]` from below to their sum. Under-report the minimum internal energy by a factor of 88 and the clamp never binds: a configured 20 K floor enforced 0.23 K. Nothing already computed was wrong because of it — the floor simply was not there. The sign is thermodynamics-dependent: a species set with positive reference energies would have made the minimum hugely positive instead, and the clamp would then have injected energy everywhere (commit `2a5064a`). The one shipped path that reads the floor is therefore the one path where the defect could show, and on the cards in use it showed as a floor that did nothing.

### What the tip does

The offset sum is what `internal_energy_offset` already computes (the hydro’s callers use it; the two conversion paths above still open-code theirs), so it is used rather than open-coded a third time; the heat capacity per unit volume carries the dry term. The point most easily got wrong when reading this: `cons[IDN]` is the *dry* density in snapy’s conserved vector (the limiter itself forms the total as `cons[IDN] + Σcons[ICY..]`, `equation_of_state.cpp:186`), so $\texttt{cons[IDN]}\, c_{v,d} + \sum \texttt{cons}_y\, c_{v,y}$ is not a double count; it equals the forward path’s $\rho c_{v,d}\left(1 + \sum y\,(c_{v,y}/c_{v,d} - 1)\right)$ exactly.

      // Heat capacity per unit volume. The DRY channel carries cvd and dominates
      // a mostly-dry column, so leaving it out is not a small error.
      auto rho_cv =
          cons[IDN] * cvd + (cons.narrow(0, ICY, ny) * cvy.view(vec)).sum(0);

      // u0 is an energy per unit mass, not a heat capacity: the offset is ADDED to
      // the thermal energy, never scaled by temperature. This is the same offset
      // _prim2intEng adds and _cons2prim subtracts, so "UT->I" at a state's own
      // temperature now reproduces "W->I" at that state, which is the identity the
      // temperature-floor clamp in EquationOfStateImpl relies on.
      return internal_energy_offset(cons) + rho_cv * temp;

`src/eos/ideal_moist.cpp`, the tail of `_temp2intEng` at `e2e397a`.

### Guarded by

`tests/test_eos_temp2inteng.py`, registered with ctest. It asserts two things, because the old code would have passed a thinner gate: the round trip — “UT→I” at a state’s own temperature reproduces “W→I” over a four-temperature sweep to a relative $10^{-12}$ — and the affine structure, that `ie(T)` is a straight line whose intercept at $T = 0$ is the reference offset. The old code was affine too, through the origin, so the round trip alone would not have pinned the offset’s place. The test’s YAML carries a vapour and cloud pair whose reference energies are non-zero — the vapour’s derived by kintera from its enthalpy, the cloud’s set explicitly since `4f59088` — for the same reason: a configuration whose offset happens to be zero cannot see an offset that is wrongly scaled. Re-run on the pinned venv for this report: PASS, intercept equal to the offset to a relative $1.1\times10^{-16}$. The clamp itself has no test of its own; the identity it relies on is what the test pins.

## 2. Where the bottom temperature is prescribed

### The geometry

A bottom boundary temperature is prescribed at a pressure level, and in a finite-volume grid a pressure level is a face. The domain’s lower face already carries the prescribed pressure: on the deep hot-Jupiter column of the commit’s A/B, with $10^{7}$ Pa at the face and a scale height $H = R_d T/g$ of 441 km, the first cell centre should read $100\exp(-dz/2H)$ = 96.66 bar and the run measures 96.69 bar. The temperature, though, was always relaxed at that first cell centre, half a cell above the face (commit `8fb8f34`).

### What that did, measured

| 2-D column, btemp = 2900 K | $T_0$ (first centre) | $T_1$ | $T_\mathrm{face} = 1.5T_0 - 0.5T_1$ |
|----|----|----|----|
| t = 0 (the initial condition is right) | 2876.5 K | 2829.8 K | 2899.93 K |
| after 5 days of centre relaxation | 2898.8 K | 2830.8 K | 2932.9 K |

Commit `8fb8f34`. The forcing drives the centre onto 2900 K and in doing so drags the boundary 33 K above the prescribed value, 4.7 % in $\sigma T^4$ at the level where the interior flux enters. At the start it sees a 23.5 K deficit at the centre where the face deficit is 0.05 K, about 500 times the forcing it should apply: the run carries a large spurious bottom heat source.

### What the tip does

With `at-face: true` on the `relax-bot-temp` block, the forcing controls the extrapolated face temperature $T_\mathrm{face} = 1.5T_0 - 0.5T_1$ instead of $T_0$. Only cell 0 is nudged and $dT_\mathrm{face}/dT_0 = 1.5$, so the gain is divided by 1.5; the damping coefficient on $T_0$ is then unchanged at $-1/\tau$, and the option adds no time-step constraint. A relaxation is kept rather than a Dirichlet ghost condition on purpose: the lower boundary is a rigid, no-flux wall, and pinning the temperature there would imply a conductive flux the equations do not carry. Only the location was wrong.

      auto target = temp_bot;
      double gain = 1.0;
      if (options->at_face()) {
        auto bottom2 = phydro->pmb->part(
            {0, 0, -1}, PartOptions().exterior(false).depth(2).ndim(3));
        auto t2 = temp.index(bottom2);
        // PartOptions::depth is capped at nghost even when exterior(false)
        // selects INTERIOR cells, so nghost = 1 would silently hand back a
        // width-1 slice. Shape query only -- no device sync.
        TORCH_CHECK(t2.size(-1) >= 2,
                    "[RelaxBotTemp] at-face needs two interior cells at the "
                    "lower boundary; got ",
                    t2.size(-1), ". Set nghost >= 2.");
        auto T0 = t2.narrow(-1, 0, 1);
        auto T1 = t2.narrow(-1, 1, 1);
        target = 1.5 * T0 - 0.5 * T1;
        gain = 1.0 / 1.5;

`src/forcing/relax_bot_temp.cpp`, inside `RelaxBotTempImpl::forward` at `e2e397a`. Two guards were added after review: the one in the excerpt, that the depth-2 slice really holds two interior cells (`PartOptions::depth` is capped at `nghost` even for interior cells, and `nghost` defaults to 1), and, following it in the source, a one-time check that offset 0 of the slice is the deeper, and so no colder, cell, so a flipped index convention fails loudly instead of extrapolating the wrong way; `≥` rather than `>` because an isothermal column is legal and is what the existing unit test builds.

### Why it is off by default

Validated by a same-binary A/B on the 2-D column: with the option off the run is bit-identical to the unmodified code; with it on, the face holds 2899.93 K as prescribed, but on this one initial condition the corrected forcing destabilises the deep column and the run stops at 2.41 days where the uncorrected arm completes 5 days, reproducibly (commit `8fb8f34`). So this is a correctness fix, not a stability fix, and on that initial condition it costs stability. It ships off pending a paired multi-initial-condition A/B, and enabling it should be a deliberate, validated choice.

The hot-Jupiter production card runs with the option off (its log prints `at-face = false`), and its `btemp` is the bottom cell-centre temperature (2646.96 K), not the wall value (2686.81 K), the two differing by 39.8 K on that grid; the run log prints `at-face = false` so the choice is on record.

### The second instance, deliberately left

The commit records it: `relax_bot_velo.cpp` and `relax_bot_comp.cpp` relax the first interior cell centre in the same way (`relax_bot_velo.cpp:53`, `relax_bot_comp.cpp:88-90` at the tip). If the face argument holds for temperature it holds for velocity and composition, and a card with `at-face: true` therefore has a bottom boundary that is internally inconsistent. Because the option is off by default and unused by the production card, this is an open design item rather than a live defect. The one-time convention check is process-global (a static flag), so with several blocks per process only the first block is checked; harmless, and noted.

## 3. Validation ledger

| gate | what it asserts | result |
|----|----|----|
| `tests/test_eos_temp2inteng.py` | “UT→I” equals “W→I” at the state’s own temperature over 50–400 K; `ie(T)` affine with the reference offset as intercept | PASS; re-run on the pinned venv 2026-09-06 (intercept to $1.1\times10^{-16}$) |
| `tests/test_forcing.cpp::relax_bottom_temperature` | the default (centre) path: `du[IPR]` at the bottom equals $dt/\tau\cdot\rho c_v(\mathrm{btemp} - T)$ and nothing else moves | gtest; unchanged by the option (gain 1, target the centre) |
| same-binary A/B, 2-D column, option off | bit-identical to the unmodified code | commit `8fb8f34` |
| same-binary A/B, option on | the face holds the prescribed value | 2899.93 K held; the run stops at 2.41 d (commit `8fb8f34`) |
| full example-deck suite on the pin, twice | no regression from either commit | 56/56 twice |

## 4. Limits and open items

The `at-face` branch has no unit test; its evidence is the A/B in the commit message. A gate would build a linearly stratified column, enable the option and assert that `du[IPR]` at the bottom equals $(1/1.5)\cdot dt/\tau\cdot\rho c_v\left(\mathrm{btemp} - (1.5T_0 - 0.5T_1)\right)$; it is a dozen lines beside the existing test and was not written here. The stability cost is a single-initial-condition result. The velocity and composition relaxations remain at the centre. And the temperature floor now binds where it did not: any card that had been relying, unknowingly, on a floor that enforced 0.23 K may see the clamp fire for the first time. The full example-deck suite on the pin passed, but a clamp that fires does not fail a case, so whether any shipped card’s floor now binds was not measured.

## 5. Upstream status and provenance

Both commits are fork-only at `e2e397a`: `2a5064a` (eos: the temperature path must add the reference offset, not scale it, with `tests/test_eos_temp2inteng.{py,yaml}`) and `8fb8f34` (relax-bot-temp: option to hold the bottom face at `btemp`). The first is upstream-reportable as a plain defect; the second is an opt-in feature whose default the upstream author may want to decide. In the regrouped branch they form one commit, `e00b246`, after the vertical-stability group; both original shas stay reachable from an archive branch. Sources: the two commit messages (`git show 2a5064a`, `git show 8fb8f34`), the tip source at the lines cited, and the hot-Jupiter card’s README for the card’s choice.

Source precedence: the source at the pin, then the commit messages’ own A/B measurements. No number in this document was produced by this document; the two 2-D column runs quoted from `8fb8f34` are named by no output directory, so they are quoted from the message and were not re-read.
