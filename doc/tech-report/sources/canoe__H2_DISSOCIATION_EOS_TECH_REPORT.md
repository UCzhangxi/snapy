> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.
# H2 dissociation inside the equation of state: one lumped species, an emergent adiabat, and the fused per-cell kernels

How a brown-dwarf deep atmosphere gets the right adiabatic gradient without advecting atomic hydrogen or running a chemistry operator; the two opt-in heat-capacity options that came with it; the one-cell blind spot that hid a fatal field-shape bug; and the scalar kernels that removed the dispatch overhead of the resulting equation of state.

kintera · `src/thermo/h2_dissociation.hpp`, `h2_dissociation_scalar.hpp`, `eval_uhs.cpp`, `thermo_y.cpp`, `thermo.hpp`, `species.{hpp,cpp}`, `thermo_options.cpp` · twelve model commits from `4c05166` to `507ef02`, with the style commit `d34f3f4` among them, over the two heat-capacity commits `a95b988` and `c714bf2`, reviewed at `83e30f1` plus the review's five follow-up commits (tip `fdc38e9`; excerpts and line numbers are at that tip) · prepared 2026-09-06; the fresh numbers here come from runs logged with the review and every quoted number names its log, test or commit.

## 1. Summary, and the three things worth carrying away

Below a few thousand kelvin H$_2$ is molecular and a constant heat capacity is a fair approximation; in a brown dwarf's deep atmosphere it dissociates, and the adiabatic gradient departs from the constant-cp value of 2/7 by tens of per cent. Representing the dissociation with advected H and a chemistry operator would have needed changes in pyharp, in the runner and in kintera's solvers.

The branch folds H$_2$ ⇔ 2H into the thermodynamics of *one* lumped H/He species. At a given temperature and molar concentration the speciation is a closed-form quadratic from the NASA-9 Gibbs energies of H$_2$, H and He, and the particle count, internal energy and both heat capacities are all derived from that same speciation. snapy's moist-mixture equation of state already delegates every thermodynamic question to kintera, so snapy is untouched, no tracer is advected, the radiative transfer still sees one gas species, and the adiabatic gradient is emergent. A second, opt-in path runs the same mathematics as one scalar loop per cell instead of a chain of tensor operations, because the tensor form turned out to be dominated by dispatch overhead rather than arithmetic.

### (i) Put the equilibrium in the equation of state, not in the tracers

H$_2$ ⇔ 2H is collisional and equilibrates in nanoseconds at these densities; the composition is a pure function of state. Anything that is a function of state belongs to the equation of state. That decision removed three pieces of work at once and is why the shipped card `30_bd_2d_dcz_h2diss_lumped_cpu` differs from its constant-cp predecessor 29 only in what a change of thermodynamics should touch: the `reference-state` keys (`Tref`, `use-nasa9-cp`, `use-h2-dissociation`, `fused-h2diss`), the species composition (per particle), the EOS type (`moist-mixture` for `ideal-moist`), and a domain height recomputed for the new deep temperature.

### (ii) Consistency is the point, and it is what makes the gradient emergent

The particle count `cz`, the internal energy carrying the dissociation energy, the heat capacity at constant volume including the latent term, and the reacting-gas Mayer relation for `cp` are all evaluated from one speciation at one `(T, c)`. Correcting `cp` alone would not do: the commit that introduced the model records that the particle-number term carries about twelve per cent of the gradient in the brown-dwarf deep (a claim quoted, not re-measured; §9).

### (iii) One cell is a blind spot

Every validation of the model before its first two-dimensional run was a single cell: the oracle comparison, the round trips, the deployment checks. A tensor-shape bug that outer-produced the temperature against the coefficient axis is invisible at one cell and fatal for any block with more than one; it was found on the first attempt to run the model in 2D. The regression test now pins four field shapes.

### Headline numbers

| quantity | value | source |
|----|----|----|
| emergent adiabatic gradient, lumped species {H: 1.6667, He: 0.16667}, 3900 K, 1019 bar | 0.18453 (cz = 1.01907) | this report's probe log (§3) |
| same, 1000 K, any of 10–1000 bar | 0.29035 (cz = 1.00002) | same |
| same, 3900 K, 11.7 bar | 0.11143 (cz = 1.17175) | same |
| fused kernels vs torch path on the same twelve states: P, cz, cv, e | bit-identical; gradient to $5.8\times10^{-12}$ | `logs/h2diss_states_compare.log` |
| round trips VU→T and PV→T at `ftol 1e-10`, eleven of the twelve states | ≤ $6.9\times10^{-7}$ K, ≤ $2.7\times10^{-7}$ K; at 3900 K / 11.7 bar the VU→T Newton from the cold guess returns NaN (§9) | same logs; `logs/vu_t_cold_start_limit.log` |
| `use-nasa9-cp` on vs off with the lumped species | no difference in any column | `logs/h2diss_states_compare.log` (§4) |

## 2. Where it sits

**The plain-English point.** snapy never computes a temperature, a pressure or a heat capacity itself when the moist-mixture EOS is selected; it asks kintera. So a thermodynamic model that is complete inside kintera is complete for the whole stack.

**The mechanism.** `ThermoYImpl` (`thermo_y.cpp`) answers snapy's requests through `compute("VT->P")`, `"VU->T"`, `"PV->T"`, `"VT->cv"` and their relatives. The forward quantities go through five hooks in `eval_uhs.cpp` — `eval_cv_R`, `eval_cp_R`, `eval_czh`, `eval_czh_ddC`, `eval_intEng_R` — each of which starts from the constant-`cref_R` baseline and overrides species by species. The two inversions (`VU→T`, `PV→T`) are Newton iterations on temperature that call those hooks (`thermo_y.cpp:366-415` and `:425-463` in their torch form). The lumped species is species 0 of the card; its H and He atom counts are read from its `composition` at load (`ThermoOptionsImpl::from_yaml`, key `reference-state/use-h2-dissociation`, which also requires a positive H count). The NASA-9 coefficients of H$_2$, H and He are fetched by name from the bundled database (`species.cpp`, `nasa9_coeffs_by_name`), independent of the species registry, so the three internal species need not be registry species and the process-global registry trap does not reach them; the (2, 3, 9) block is cached once per device and dtype (`h2diss_coeffs_cached`, `eval_uhs.cpp`).

**The pointer.** Card: `30_bd_2d_dcz_h2diss_lumped_cpu` (`config.yaml`; `use-h2-dissociation: true`, `fused-h2diss: true`, composition `{H: 1.6667, He: 0.16667}` per particle, so μ = 2.3470 g/mol — the formula-unit `{H: 1.5, He: 0.15}` weighs 2.112 g but holds 0.9 mol of particles and made μ ten per cent light). Keys accepted in `reference-state`: `use-nasa9-cp`, `use-h2-cp`, `h2-cp-mode`, `use-h2-dissociation`, `fused-h2diss` (unknown keys are rejected with a suggestion since `6bc46c1`).

## 3. The physics, and a fresh table

**The plain-English point.** Given temperature and how much of the lumped species is in a cubic metre, how much of its hydrogen is atomic is one quadratic; everything else follows by differentiating that answer.

**The mechanism.** With absolute NASA-9 enthalpies and entropies (the `a7` constant carries the formation enthalpy, so `2h_H − h_H2` is the dissociation energy `D(T)`), `ln K_p = −(2g_H − g_H2)` and `K_c = K_p P₀/(RT)`. With `n_H c` hydrogen atoms per cubic metre the equilibrium `[H]` solves `2[H]² + K_c[H] − K_c n_H c = 0`, written in the cancellation-free form that stays exact as `K_c → ∞`; then $[\mathrm{H_2}] = (n_H c - [H])/2$ and `[He] = n_He c`. From that speciation:

$$cz = n_{\mathrm{tot}}/c,\qquad e/R = \sum_i n_i\,(h_i/R - T)/c,\qquad cv/R = \Big[\sum_i n_i\,cv_i/R + \sum_i (u_i/R)\,dn_i/dT\Big]/c,\qquad cp/R = cv/R + \frac{(cz + T\cdot dcz/dT)^2}{cz + c\cdot dcz/dc}$$

The second sum in `cv` is the latent term; the last line is the exact Mayer relation for a reacting ideal gas. `d[H]/dT` comes from van 't Hoff on `K_c`; `d[H]/dc` from the quadratic. The internal energy is referenced to 300 K (`kTref` in `h2_dissociation.hpp`, matching `kNasa9Tref` in `eval_uhs.cpp`) by subtracting the same speciation's `U` at 300 K, so the model joins the constant-cv baseline continuously there. At 300 K dissociation is of order $e^{-70}$, so that reference is independent of `c` to about $10^{-13}$ ($5.7\times10^{-14}$ over $10^{-4}$–$10^{5}$ mol m$^{-3}$, `logs/test_h2diss_scalar_fdc38e9.log`) — the fact the fused path exploits by hoisting it (§6). The chemical particle factor is *composed* with whatever the registered compressibility hook returns, `Z_total = Z_chem · Z_nonideal`, with the product rule for its concentration derivative (`866a4ad`); today no hook is registered and the composition is a no-op, but a future non-ideal `Z` will stack instead of being clobbered. Cold, `cz → 1` and the model reduces to NASA-9 H$_2$/He.

**Fresh numbers.** The probe `probe_h2diss_states.py` takes the example-30 species, twelve `(T, ρ)` states chosen so the pressure lands near 10, 100 and 1000 bar, and computes `cz` from `VT→P`, `cv/R` from a finite difference of `VT→U`, and the adiabatic gradient $(\partial\ln T/\partial\ln P)_s$ by a centred isentropic step in density (`du = −P d(1/ρ)`, solved for the end temperature) at three step sizes, so the reader can see the difference converge. Every column is identical with `fused-h2diss` on or off except the gradient, which agrees to $5.8\times10^{-12}$ (`logs/h2diss_states_compare.log`). The round trips (`VU→T` from `VT→U`, `PV→T` from `VT→P`) close to $6.9\times10^{-7}$ K and $2.7\times10^{-7}$ K on eleven of the twelve states; on the twelfth, 3900 K at 11.7 bar, the torch `VU→T` Newton does not converge from its cold guess and returns NaN — the probe's summary line skipped that NaN, and the independent read of this report caught it; §9 has the scan.

| T \[K\] | P \[bar\] | cz | cv/R | e/R \[K\] | $\nabla_{\mathrm{ad}}$, ε = $10^{-2}$ | $10^{-3}$ | $10^{-4}$ |
|----|----|----|----|----|----|----|----|
| 1000 | 10.000 | 1.00002 | 2.4442 | 1658.93 | 0.29036 | 0.29035 | 0.29035 |
| 1000 | 1000.020 | 1.00002 | 2.4442 | 1658.93 | 0.29036 | 0.29035 | 0.29035 |
| 2000 | 10.003 | 1.00025 | 2.9333 | 4322.43 | 0.25470 | 0.25470 | 0.25470 |
| 2000 | 1000.043 | 1.00004 | 2.8602 | 4311.31 | 0.25911 | 0.25910 | 0.25910 |
| 3000 | 10.225 | 1.02254 | 6.4943 | 8490.04 | 0.15452 | 0.15452 | 0.15452 |
| 3000 | 100.721 | 1.00721 | 4.2161 | 7688.68 | 0.20041 | 0.20041 | 0.20041 |
| 3000 | 1002.299 | 1.00230 | 3.4775 | 7432.12 | 0.22635 | 0.22634 | 0.22634 |
| 3900 | 11.718 | 1.17175 | 16.5865 | 19106.52 | 0.11143 | 0.11143 | 0.11143 |
| 3900 | 105.878 | 1.05878 | 8.2619 | 13259.03 | 0.14367 | 0.14367 | 0.14367 |
| 3900 | 1019.072 | 1.01907 | 4.9614 | 11203.70 | 0.18453 | 0.18453 | 0.18453 |

The probe log, kintera `2.4.10.dev27+g83e30f13c`, μ = $2.347147\times10^{-3}$ kg/mol; the 100 bar rows at 1000 and 2000 K are in the log and omitted here. At 1000 K the gradient is R/cp of NASA-9 H$_2$/He (cp/R = cv/R + 1 = 3.4442; 1/3.4442 = 0.2903); at 3900 K and 12 bar there are 17.2 per cent more particles than moles of the lumped species and the gradient has fallen to 0.111.

One number on record is worth setting beside this table. The example-30 README and the card's header quote “$\nabla_{\mathrm{ad}}$(deep) = 0.197” and, from the introducing commit, a cp-only value of 0.162 against a true 0.197. That 0.197 is not a value at 3900 K and 1000 bar: the probe's 3000 K / 1002 bar row (0.226) and 3900 K / 1019 bar row (0.185) bracket it.

## 4. The two heat-capacity options that came first

**The plain-English point.** Before dissociation was folded in, the heat capacity itself was a constant per species. Two opt-in options replaced that: tabulated NASA-9 polynomials for any species that has them, and a first-principles rotational partition function for a species named `H2`, which reproduces the ortho/para conversion peak near 50 K and the rotational freeze-out that the NASA-9 combustion fits, valid from 200 K, cannot.

**The mechanism.** `use-nasa9-cp` (`a95b988`): for species carrying NASA-9 data, `cp/R` is the seven-term polynomial on the low or high range and the internal energy is `(h(T) − h(T₀)) − (T − T₀)` with `T₀` = 300 K, so it coincides with the constant-cv value there; a mask leaves every other species on the baseline (`eval_uhs.cpp`, `eval_nasa9`). `use-h2-cp` (`c714bf2`): for a species literally named `H2`, a rigid-rotor sum over J = 0…40 with $\theta_{\mathrm{rot}}$ = 87.55 K, in `equilibrium` mode (one Boltzmann ensemble, ortho weight 3, which produces the conversion peak) or `normal` mode (a fixed 1:3 para:ortho mixture, each ensemble equilibrated internally); it overrides NASA-9 for that species (`eval_h2cp`). Neither touches entropy: `eval_entropy_R` still uses the constant `cp_gas_R`, so the header warns against enabling `use-nasa9-cp` together with condensation of a NASA-9 vapour (`species.hpp`).

**Fresh numbers.** `probe_h2cp.py` on a pure-H$_2$ card, one mode per process:

| T \[K\] | cp/R, equilibrium | cp/R, normal |
|---------|-------------------|--------------|
| 20      | 2.6085            | 2.5000       |
| 30      | 3.3496            | 2.5000       |
| 50      | 4.5684            | 2.5038       |
| 80      | 3.8004            | 2.5785       |
| 100     | 3.4169            | 2.6925       |
| 150     | 3.1845            | 3.0227       |
| 300     | 3.4526            | 3.4522       |
| 1000    | 3.5002            | 3.5002       |

`logs/h2cp_equilibrium.log`, `logs/h2cp_normal.log`. The introducing commit quotes 4.57 at 50 K (equilibrium), 2.50 at 50 K (normal) and 3.45 at 300 K against an independent partition-function reference that is not in the repository; the three values reproduce. Both modes reach the classical 7/2 by 1000 K, and normal mode sits on the frozen 5/2 below 30 K.

**With the lumped species, `use-nasa9-cp` does nothing.** The dissociation thermo overrides the lumped species' `cv`, `cp` and internal energy whatever that flag says, and the card has no other species. Measured: every column of the §3 table is identical with the flag on and off (`logs/h2diss_states_compare.log`). The example-30 README's warning that the flag is required (“without it moist-mixture still uses a constant cref_R”) is therefore wrong for that card; the flag matters only if a second, NASA-9-tabulated gas species is added. Likewise the card's comment that `Tref` “MUST match” the 300 K reference is enforced nowhere: the model is continuous with the constant-cv baseline at 300 K by construction, whatever `Tref` the card sets.

## 5. The field-shape bug

**The plain-English point.** The first attempt to run the model in two dimensions crashed inside snapy's `cons2prim`; on a square block it did not even throw but returned a pressure field with an extra spatial axis. Every validation before that day had been one cell, where the bug is invisible.

**The mechanism.** `speciate` passed the temperature as `(spatial…, 1)` to helpers that select each NASA-9 coefficient with `a.select(-1, k)`, which drops the coefficient axis to `(spatial…)`; the trailing singleton then broadcast against the field's last spatial dimension. At one cell `(1)` against `(1, 1)` is `(1, 1)` and a `.squeeze(-1)` hid it. On a flat 81-cell field `VT→P` returned `(81, 81)`; on a 134×134 block it returned `(1, 134, 134, 134)`; on a non-square block it threw. The fix (`427c063`) keeps `T` per cell and drops the squeeze — one header, an inline body only, so it shipped as a kintera wheel swap with no snapy rebuild. The regression test `tests/test_h2diss_ndfield.py` asserts the output shape at `(81,)`, `(1, 10, 134)`, `(1, 134, 134)` and `(2, 3, 4)`, that a batch equals the same cells one at a time, and a `VU→T` round trip on a `(1, 10, 134)` block; it ran 6/6 on the pinned iso and on the follow-up iso for this report (`logs/pytest_perfile_kintera-iso-83e30f1.log`, `logs/pytest_perfile_kintera-iso-fdc38e9.log`; one interpreter per test file, because the species registry is global and the same files fail when run in one process). snapy's `W→T` symptom was the same defect.

## 6. The fused per-cell path

**The plain-English point.** The torch form of this equation of state is correct and was 99.7 per cent of the runtime. Not because the arithmetic is heavy — a quadratic and a few polynomials per cell — but because each Newton inversion is about a thousand tensor operations, each with a fixed dispatch cost, and a 2D field of 512 cells per rank cannot amortise them (the header of `h2_dissociation_scalar.hpp`; commit `3b7e8b2`). The fused path turns the loop inside out: one launch per solve, a scalar Newton per cell, early exit per cell.

**How the diagnosis was made.** Two code traces attributed the cost to dispatch overhead: about 22–25 full-field Newton inversions per RK3 cycle (mostly `PV→T` on Riemann face states), each hook re-speciating the whole state to keep one field, the 300 K reference recomputed every iteration, a cold start every call, and a device sync per iteration to test convergence on the field maximum.

**The mechanism, in the order it was built.**

- `h2_dissociation_scalar.hpp` (`7e4c4dc`): a plain-`double` transcription of `speciate` and `eval`, line for line the same algebra, reading the same (2, 3, 9) coefficient block; nothing hard-coded. Its guard, `tests/test_h2diss_scalar.cpp`, compares it to the torch `eval` on a 71×41 grid over 200–4500 K and $10^{-2}$–$10^{4}$ mol m$^{-3}$; at its first run `cz` was bit-identical, `cp`/`cv` agreed to about $5\times10^{-15}$ and `e` to $2\times10^{-12}$ (commit message). The guard was a standalone `main` until the review's follow-up `79189c8` registered it as a ctest; run on 2026-09-06 it gives `cz` bit-identical, `cz_ddC` $1.4\times10^{-17}$, `cp`/`cv` $3.6\times10^{-15}$, `e` $3.6\times10^{-12}$ (`logs/test_h2diss_scalar_fdc38e9.log`; §8).
- `_intEng_to_temp_fused` and `_pres_to_temp_fused` (`3b7e8b2`, `07176a7`; `thermo_y.cpp:465-548` and `:550-620`): one `at::parallel_for` over cells, the same Newton as the torch loops, per-cell exit at `ftol`. The `PV→T` step is subtracted and damped: `f(T) = T·cz·c − P/R` rises with `T`, and `(cp − cv)·c ≥ f′ = (cz + T·dcz/dT)·c` for a dissociating gas because `dcz/dT > 0` and `dcz/dc < 0` in the Mayer denominator, so the step never overshoots. (The torch loop had once added the step; harmless while `cz ≡ 1` made the initial guess exact, divergent to 17 000 K with dissociation — recorded in the torch loop's comment.)
- The five hooks (`5dc1349`): one launch computes the pack `[e_R, cv_R, cp_R, cz, cz_ddC]` per cell (`eval_uhs.cpp:240-272`) and each hook returns its field (`:276`, `:321`, `:361`, `:400`, `:448`). Profiling on the production run had put the hooks at 70 per cent of the fused-on budget (commit message, py-spy).
- Warm start (`219cc7a`; the seeds became buffer-dictionary-only in `507ef02`): the previous solve's converged temperature seeds the next, per instance (`warm_vu`, `warm_pv`); seeds only, since the per-cell exit test guards accuracy; a non-finite or non-positive seed falls back to the cold guess, a finite stale one is used and corrected by the iteration. Then the 300 K reference and `ln T` hoisted out of the iteration (`be8036b`): transcendentals per Newton iteration from ten logarithms and two exponentials to one of each.
- The predicate (`h2diss_fused_ok`, `eval_uhs.cpp:223-235`): flag on, dissociation on species 0 as the only gas, no clouds, no registered compressibility hook, CPU, float64. Anything else takes the torch path, which remains the oracle. Until the review's follow-up `57df4fc` the two Newton kernels used a second predicate that lacked the hook and float64 conditions (the CPU check sat at their call sites); both call sites now use this one.

**Correctness.** This report's own probe (§3): on twelve states, every forward quantity bit-identical and the derived gradient to $5.8\times10^{-12}$.

**The ABI story, stated precisely.** Two commits (`06f5ae4`, `507ef02`) moved the warm-start seeds first to the end of `ThermoYImpl` and then out of it entirely, into the Module buffer dictionary, after a member inserted mid-class had shifted `options` and sent the pin's snapy reading a garbage pointer (a 56 GB allocation in the MeshBlock constructor). The header comment says `sizeof(ThermoYImpl)` is identical to upstream and a consumer built against upstream headers needs no rebuild. That is true relative to the branch's own July pin, which is what it meant; it is not true relative to chengcli `main`, because the two heat-capacity commits and this model append eight fields to `SpeciesThermoImpl` (`use_nasa9_cp`, `use_h2_cp`, `h2_cp_mode`, `use_h2_dissociation`, `h2_diss_id`, `h2_diss_nH`, `h2_diss_nHe`, `fused_h2diss`; `species.hpp`), from which `ThermoOptionsImpl` derives, so a snapy built against upstream headers reads a different options layout. For the upstream pull request that is moot — the consumer is rebuilt — but the sentence should not be read as “binary compatible with upstream”.

## 7. The code today, path by path

Every excerpt is verbatim from `fdc38e9` at the cited lines.

### The speciation (`h2_dissociation.hpp:96-113`)

      auto gH = s.hH / temp - sH;  // G/(RT)
      auto gH2 = s.hH2 / temp - sH2;
      auto lnKp = -(2.0 * gH - gH2);
      auto Kp = torch::exp(lnKp.clamp(-700., 700.));
      s.Kc = Kp * kP0 / (constants::Rgas * temp);  // mol/m^3

      auto nHc = nH * cc;
      // root of 2[H]^2 + Kc[H] - Kc*nHc = 0 in the cancellation-free form
      // H = 2*Kc*nHc / (Kc + sqrt(Kc^2 + 8*Kc*nHc)): exact -> nHc as Kc -> inf
      // (full dissociation), whereas (-Kc + sqrt(...))/4 loses all precision there
      // (large-Kc cancellation).
      auto disc = (s.Kc * s.Kc + 8.0 * s.Kc * nHc).clamp_min(0.);
      s.H = (2.0 * s.Kc * nHc / (s.Kc + disc.sqrt()).clamp_min(1e-300))
                .clamp_min(0.)
                .minimum(nHc);
      s.H2 = (nHc - s.H) / 2.0;
      s.He = nHe * cc;
      s.ntot = s.H + s.H2 + s.He;

### The derived quantities (`h2_dissociation.hpp:137-153`)

      auto dH_R = 2.0 * s.hH - s.hH2;  // (2h_H - h_H2)/R  [K]  == D(T)/R
      auto dKc_dT = s.Kc * (dH_R / temp.pow(2) - 1.0 / temp);  // van 't Hoff
      auto dH_dT = dKc_dT * (nH * cc - s.H) / denom;
      auto dH_dc = s.Kc * nH / denom;

      auto cz = s.ntot / cc;
      auto dcz_dT = dH_dT / (2.0 * cc);
      auto dcz_dc = dH_dc / (2.0 * cc) - s.H / (2.0 * cc * cc);

      auto uH = s.hH - temp, uH2 = s.hH2 - temp;
      auto cv_R = (s.H * (s.cpH - 1.0) + s.H2 * (s.cpH2 - 1.0) +
                   s.He * (s.cpHe - 1.0) + uH * dH_dT + uH2 * (-dH_dT / 2.0)) /
                  cc;

      auto num = (cz + temp * dcz_dT).pow(2);
      auto den = (cz + cc * dcz_dc).clamp_min(1e-8);
      auto cp_R = cv_R + num / den;

The floor on `den` can never fire: `d n_tot/dc = d[H]/dc /2 + n_H/2 + n_He` is at least `n_H/2 + n_He`, of order one.

### The field-shape fix (`h2_dissociation.hpp:80-83`)

      auto Tb = temp;  // per-cell (spatial...): h_R_of/cp_R_of/s_R_of consume the
                       // coeff axis via a.select(-1,k) -> (spatial...), so T must
                       // NOT carry a trailing singleton (else it OUTER-PRODUCTS).
                       // n=1 masked this for all prior validation.

### The one fused-path predicate (`eval_uhs.cpp:223-235`)

    bool h2diss_fused_ok(SpeciesThermo const& op, torch::Tensor const& temp,
                         torch::Tensor const& conc) {
      // A registered czh() user function would compose a non-ideal Z with the
      // chemical Z (see eval_czh); the fast path assumes Z_nonideal == 1, so
      // REQUIRE czh unregistered rather than assume it.
      for (auto const& f : op->czh()) {
        if (!f.empty()) return false;
      }
      return h2diss_on(op) && op->fused_h2diss() && op->h2_diss_id() == 0 &&
             op->vapor_ids().size() == 1 && op->cloud_ids().size() == 0 &&
             conc.size(-1) == 1 && temp.is_cpu() &&
             temp.scalar_type() == torch::kFloat64;
    }

### The damped `PV→T` Newton, per cell (`thermo_y.cpp:596-609`)

          double Ti = P / (c * Rgas);  // ideal-gas guess (exact when cz==1)
          if (warm && std::isfinite(warm[i]) && warm[i] > 0.) Ti = warm[i];
          bool ok = false;
          for (int it = 0; it < max_iter; ++it) {
            auto R = h2diss_scalar::eval(Ti, c, nH, nHe, ab, e0);
            const double func = Ti * R.cz * c - P / Rgas;
            const double Tnew = Ti - func / ((R.cp_R - R.cv_R) * c);
            const double conv = std::fabs(1.0 - Ti / Tnew);
            Ti = Tnew;
            if (conv < ftol) {
              ok = true;
              break;
            }
          }

### The `VU→T` Newton, per cell (`thermo_y.cpp:519-537`)

          const double rho_i = rho[i];
          const double c = rho_i * invmu0;  // mol/m^3 (dry conc)
          const double e_tgt = eint[i];     // J/m^3
          // const-cv cold guess, identical to the torch path
          double Ti = (e_tgt - rho_i * u0_0) / (rho_i * cv0_0);
          if (warm && std::isfinite(warm[i]) && warm[i] > 0.) Ti = warm[i];
          bool ok = false;
          for (int it = 0; it < max_iter; ++it) {
            auto R = h2diss_scalar::eval(Ti, c, nH, nHe, ab, e0);
            const double u = (uref0 + kTref * cref0 + R.e_R) * Rgas;  // J/mol
            const double cv = R.cv_R * Rgas;                          // J/(mol K)
            const double Tnew = Ti + (e_tgt - u * c) / (cv * c);
            const double conv = std::fabs(1.0 - Ti / Tnew);
            Ti = Tnew;
            if (conv < ftol) {
              ok = true;
              break;
            }
          }

## 8. Validation ledger

| what | where | result |
|----|----|----|
| twelve-state probe, torch and fused, with and without `use-nasa9-cp` | `logs/h2diss_states_*.{log,json}`, `h2diss_states_compare.log` | §3 table; fused vs torch bit-identical (gradient 5.8e−12); nasa9 flag a no-op; round trips 6.9e−7 K and 2.7e−7 K on eleven states, NaN on the twelfth (§9) |
| H$_2$ heat capacity, both ortho/para modes | `logs/h2cp_equilibrium.log`, `logs/h2cp_normal.log` | §4 table; the introducing commit's three values reproduce |
| `tests/test_h2diss_ndfield.py`, one interpreter per file | `logs/pytest_perfile_kintera-iso-83e30f1.log`, `…-fdc38e9.log` | 6/6 on both isos |
| `tests/test_h2diss_scalar.cpp` | commit `7e4c4dc` message; as a ctest, `logs/ctest_fdc38e9.log` (29/29) and `logs/test_h2diss_scalar_fdc38e9.log` | July: cz bit-identical, cp/cv ~5e−15, e ~2e−12; 2026-09-06: cz 0, cz_ddC 1.4e−17, cp/cv 3.6e−15, e 3.6e−12, e0 5.7e−14 |
| `tests/test_h2_cp.py` (new, `fdc38e9`) | `logs/pytest_perfile_kintera-iso-*.log`; `logs/ctest_fdc38e9.log` | 2/2 on both isos |
| deck `30_bd_2d_dcz_h2diss_lumped_cpu` | CPU run log (2026-09-06, the pin `83e30f1`) | PASS-NC at 2 cycles (smoke length; no drift sample) |

## 9. Limits and open items

- **The cold start fails where dissociation is strong.** The torch `VU→T` Newton starts from the constant-cv guess `(U − ρu₀)/(ρcv₀)`, which at 3900 K and 12 bar is 7665 K because the internal energy carries the dissociation energy; from there the iteration returns NaN whatever the budget (50, 200, 1000). The scan in `logs/vu_t_cold_start_limit.log` puts the edge between cz 1.07 (3500 K, 12.9 bar, converges) and cz 1.11 (3700 K, 13.3 bar, NaN); every state at 33 bar and above converges, up to 4300 K and 1037 bar (cz 1.037). The fused kernel fails the same way from a cold guess and converges from a warm seed, which is why the fused probe's round trip passed. A hot, low-pressure card would be affected. Not fixed here; recorded as a finding of the review.
- **The oracle comparison was never committed.** The introducing commit's 0.06 % mean / 0.18 % maximum agreement with an independent H$_2$ ⇔ 2H table over 1000–3900 K and 10–1000 bar, and the “cp-only lands on 0.162 instead of 0.197” sentence, have no artefact in the repository; a `test_h2diss_eos` that a later message calls “unchanged” never existed on any branch. The §3 table is what a reader can reproduce today.
- **The scalar guard did not run between 2026-07-18 and its registration.** Its numbers above are the July ones until the first ctest on the follow-up tip.
- **GPU.** The fused kernels are CPU-only by predicate; on GPU the torch path runs and is launch-bound (parked: correct, about 600 launches per Newton iteration). The example-30 README's CPU-faster-than-GPU measurement is from July.
- **One lumped species only.** The model requires species 0 to be the lumped gas; a card with a second gas species or any cloud falls back to the torch path (and the fused predicate declines), and the torch path itself has been exercised only on the single-species card.
- **Entropy.** Neither heat-capacity option nor the dissociation model touches `eval_entropy_R`; do not combine them with condensation of a NASA-9 vapour.
- **float64 only**, by construction: a float32 field fails inside `ThermoY` before any solve, so the predicate's dtype guard is defensive rather than reachable.
- **The hard-coded 300 K reference** (`kNasa9Tref`, `kTref`) is a model constant, not the card's `Tref`; the continuity argument holds at 300 K regardless.
- **The ABI sentence** in `thermo.hpp` is accurate only relative to the branch's own pin (§6).
- **Helium is inert and monatomic**; metals are not represented. This is the H/He deep atmosphere, not a metal-rich one.

## 10. Upstream status

Everything here is fork-only (commit `fdc38e9`). Upstream's own route to the same physics is the general gas-phase equilibrium of kintera \#100/#101, in which H$_2$ ⇔ 2H is a YAML reaction over real H$_2$, H and He species solved by a Newton with a line search; it was validated for the brown-dwarf deep to 0.2 per cent in dissociation fraction and is the right design when H is genuinely advected and out of equilibrium, as on an ultra-hot Jupiter. The lumped model is the complement: for a pair in local equilibrium it costs one quadratic per cell, adds no species to the radiative transfer, and needs no operator. For the pull request the twelve model commits and the two format commits collapse into one group commit (the 2026-09-06 regroup), with the two heat-capacity commits as their own group; the field-shape bug, the composition of the chemical `Z`, and the two ABI moves are called out in the message because each cost a day.

## 11. Provenance

| commit | subject | this report |
|----|----|----|
| a95b988 | thermo: opt-in NASA-9 cp/cv/intEng (`use_nasa9_cp`) | §4 |
| c714bf2 | thermo: opt-in first-principles H2 cp/cv/intEng (`use_h2_cp`) | §4 |
| 4c05166 | thermo: opt-in H2\<-\>2H equilibrium EOS on a lumped H/He species | §2, §3 |
| 866a4ad | thermo(h2diss): COMPOSE the chemical Z with a non-ideal Z | §3 |
| 7384762 | thermo(h2diss): cancellation-free root + per-device coefficient cache | §3, §2 |
| 427c063 | thermo(h2diss): fix field-shape bug | §5 |
| 7e4c4dc | thermo(h2diss): scalar per-cell transcription (S1) | §6 |
| 3b7e8b2 | thermo(h2diss): fused VU-\>T kernel (S2) | §6 |
| 07176a7 | thermo(h2diss): fused PV-\>T kernel (S3) | §6 |
| 5dc1349 | thermo(h2diss): fused fast path for the five eval\_\* hooks (S5a) | §6 |
| 219cc7a | thermo(h2diss): warm-start the fused kernels + shared coeff cache | §6 |
| be8036b | thermo(h2diss): hoist the T0 reference + shared lnT | §6 |
| 06f5ae4 | thermo: move the warm-start buffers to the END of ThermoYImpl (ABI) | §6 |
| 507ef02 | thermo(abi): keep warm-start seeds ONLY in the Module buffer dict | §6 |
| d34f3f4, 0da65b7 | style: clang-format | — |
| 57df4fc | thermo: one predicate for the fused h2diss path (review follow-up) | §6, §7 |
| 79189c8 | tests: register the h2diss scalar transcription guard as a ctest (review follow-up) | §8 |
| fdc38e9 | tests: gate use-h2-cp against the values its commit quotes (review follow-up) | §4, §8 |

Regrouped for the upstream pull request on 2026-09-06 (tree identical to `fdc38e9`): the model, its two style commits and the two follow-ups became `1f4f11b`, the heat-capacity options and their test `39cce71`. The pre-regroup tip is `83e30f1`; the fixed tip is `fdc38e9`.

## Appendix A — identifiers

| term | meaning |
|----|----|
| lumped species | the one gas species of the card, `{H: n_H, He: n_He}` atoms per mole, whose internal H$_2$/H/He composition the EOS resolves |
| `cz` (`czh`) | particles per mole of the lumped species; kintera's compressibility hook slot, composed as `Z_chem · Z_nonideal` |
| `K_p`, `K_c` | equilibrium constant at the standard pressure `P₀` = $10^{5}$ Pa, and in concentration units |
| `e_R`, `u0_R`, `uref_R`, `cref_R` | internal energy over R relative to 300 K; the card's reference internal energy at `Tref`; the same shifted to T = 0 by `ThermoY::reset`; the constant heat capacity baseline |
| `fused-h2diss`, `h2diss_fused_ok` | the YAML flag and the predicate for the scalar per-cell path |
| Design C, S1…S5a | the fused-kernel plan and its steps |

Written 2026-09-06 as the technical report for the kintera H$_2$-dissociation and heat-capacity commit groups of the final review. Numbers measured for this report are logged with the review; every other number names its test or commit. Excerpts are verbatim from `fdc38e9`.
