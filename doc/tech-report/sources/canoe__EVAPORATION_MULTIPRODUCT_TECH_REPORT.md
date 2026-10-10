> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Evaporation of a condensate with two gaseous products: the rate law, its units, and one implicit step

kintera evaporates precipitation at a rate κ $C_{p}$ η, where κ = 12 D $v_{m}$/$d^{2}$ comes from diffusion to a sphere and η is the saturation deficit of the manuscript’s eq. 107. For a condensate with one gaseous product η is a concentration and the rate is dimensionally sound. For $\mathrm{NH_4SH}$(s,p) ⇒ $\mathrm{NH_3}$ + $\mathrm{H_2S}$ η is a product of two concentrations, so the rate carries one concentration unit too many and its size depends on the unit system: exactly, it equals the diffusion rate times ($C_{\mathrm{NH_3}}$ + $C_{\mathrm{H_2S}}$ + x) expressed in the unit chosen, which on Jupiter-like states in SI units makes it 8–21× too slow. Steady diffusion with surface equilibrium gives a rate proportional to the reaction extent that would restore equilibrium at fixed temperature; for one product that extent is today’s deficit, bit for bit, and for two it is the root of a quadratic. The MOSAIC aerosol scheme (Zaveri et al. 2008) solves the same surface-equilibrium quadratic (with unequal diffusivities), and Sugiyama et al. (2011, 2014) use the same equal-shift deficit inside an empirical rain-evaporation rate. With the extent law one linearised backward-Euler step provably cannot pass equilibrium; today’s law can, but only when a cell holds more $\mathrm{NH_4SH}$ precipitation, in moles, than ambient ammonia; in card 40’s own output that ratio never exceeds $1.05\times 10^{-4}$.

kintera commit `1f4f11b` (pinned; read at this commit) · manuscript: C. Li, *Thermodynamics of multiple non-dilute condensables: theory, algorithm and implementation*, draft 2026-09-03, §3–4 and Table 1 · evidence: scripts and outputs (`compare_laws.py`, `compare_laws_SI.out`, `compare_laws_mmol.out`, `root_precision_probe.py`, `root_precision_probe.out`, `step_overshoot.py`, `step_overshoot.out`, `card40_ratio.py`, `card40_ratio.out`, `card_check.py`, `card_check.out`) · revision 3, 2026-09-17 (implementation and validation record added; revision 2 of 2026-09-16 (revision 1 corrected after an independent audit: the test inventory, the overshoot headline, the unit demonstration, the literature wording, the relation to the saturation adjustment, two design gaps, line references; revision 2 corrected after a second audit: card 40’s κΔt and precipitation ratio))

**STATUS 2026-09-17: IMPLEMENTED ON A BRANCH, NOT LANDED.** kintera commit `f94a335` (one commit on the pinned `1f4f11b`); the pinned branch and every venv are unchanged. §1–§7 are the derivation (two independent audits), §8 describes the code as committed (two independent code audits), §10 is the validation record. The card-level effect on card 40 is not attributable at the sample size run (§10.4); moving the pin is a separate decision. **Every future kintera pin must carry `f94a335`** (§11).

## 1. Summary

**The defect.** `EvaporationImpl::forward` returns `kappa * eta` (`src/kinetics/evaporation.cpp:89-121`; κ and η at lines 106–120) with κ in $m^{3}$ $\mathrm{mol}^{-1}$ $s^{-1}$ and η = $e^{f(T)}$ − $\prod _{i}$ $C_{i}^{\nu _{i}}$ in (mol $m^{-3}$)$^{n}$, n = $\sum \nu _{i}$ the number of gaseous products. Only n = 1 gives $s^{-1}$. The manuscript defines η for general n (eqs. 107–109) and notes it is a concentration only for a single product (lines 395–396); Table 1 writes reaction 9 with a free coefficient $A_{2}$. Every card, however, gives the $\mathrm{NH_4SH}$ reaction the diffusion coefficient through `diff_c`, `vm` and `diameter`.

**The law.** For equal diffusivities per unit reaction extent, the particle surface sits at $C_{i}$ + $\nu _{i}$x with ∏($C_{i}$+$\nu _{i}$x)$^{\nu _{i}}$ = K, and the rate is κ $C_{p}$ x. For n = 1, x = K − C, identical to today. For two products with ν = 1, x = 2(K − $C_{1}C_{2}$) / \[($C_{1}$+$C_{2}$) + √(($C_{1}$−$C_{2}$)$^{2}$+4K)\].

**Size.** Exactly, η = x($C_{1}$+$C_{2}$+x): today’s rate is the diffusion rate multiplied by the number $C_{1}$+$C_{2}$+x in whatever unit of amount is used. In SI on card-40-like states that number is 0.048–0.12, so evaporation of $\mathrm{NH_4SH}$ precipitation runs 8–21× too slowly; at card 40’s own κΔt ≈ 13, one implicit step evaporates 4.6–20.5× less than the extent law.

**One implicit step.** With the new law the step is Δ = κΔt $C_{p}$x / (1 + κΔt($C_{p}$ + x)) \< min(x, $C_{p}$) for every Δt at fixed T: it cannot pass equilibrium or evaporate more precipitation than exists. Today’s step passes equilibrium only if $C_{p}$ \> $C_{1}$+$C_{2}$+x+1/(κΔt x), which needs more precipitation than ambient $\mathrm{NH_3}$; card 40 reaches a ratio of at most $1.05\times 10^{-4}$, and on the four tabulated states it never passes (Δ/x ≤ 0.98).

**Reach.** Only reactions with two gaseous products change: example card `40_jupiter_nh4sh_slab_cpu` (card 40), snapy’s `jupiter_crm`, `jupiter_gcm` and `jupiter_evap_precip_1d` examples, and nine of the manuscript’s Jupiter reference cards. Every single-product evaporation is unchanged by construction.

## 2. Where evaporation sits

kintera treats evaporation as one kind of kinetic reaction (manuscript §4). A card lists it as, for example,

    - equation: NH4SH(s,p) => NH3 + H2S
      type: evaporation
      rate-constant: {formula: nh3_h2s_lewis, diff_c: 0.2e-4, diff_T: 0., diff_P: 0., vm: 43.7e-6, diameter: 1.0e-4}

(card 40, `40_jupiter_nh4sh_slab_cpu/config.yaml:214-216`). The path through the code:

1.  **Rate constant.** `EvaporationImpl::forward` (`evaporation.cpp:89-121`) computes the diffusivity D = $D_c\,(T/T_{\mathrm{ref}})^{D_T}(P/P_{\mathrm{ref}})^{D_P}$ (with $D_c, D_T, D_P$ = `diff_c`, `diff_T`, `diff_P`), κ = 12 D $v_{m}$/$d^{2}$, the saturation term $e^{f}$ = exp(ln P\* − n ln(RT)) with n = $\sum _{\mathrm{products}}\nu _{i}$, and η = $e^{f}$ − $\prod C_{i}^{\nu _{i}}$ clamped at zero. It returns κη.
2.  **Mass action.** `KineticsImpl::forward` multiplies the rate constant by the reactant concentration, here the precipitation $C_{p}$ (`kinetics.cpp:405`): r = $\kappa \eta C_{p}$.
3.  **Jacobian.** The rate constant is evaluated on a copy of the concentrations that requires gradients, so its derivative ∂(κη)/∂C comes from autograd (`kinetics.cpp` forward, the `conc1.grad()` branch). `KineticsImpl::jacobian` (`kinetics.cpp:268-299`) adds the mass-action part r/$C_{p}$ on the reactant column. The hand-written `_jacobian_evaporation` (`jacobian_evaporation.cpp`, the manuscript’s eq. 111) is declared and defined but has no caller. `evolve_temperature` defaults to `false` (`kinetics.hpp:81`), so the temperature derivative is not assembled: the step is linearised at fixed T.
4.  **Implicit step.** `evolve_implicit` solves, per cell, (I/Δt − S J) Δξ = S r once (`evolve_implicit_impl.h`, `evolve_implicit_cell`; manuscript eq. 101). There is no iteration and no clamp.
5.  **Caller.** The runners call `paddle.evolve_kinetics` once per step and add the density increment to the conserved state; the latent heat enters through the equation of state, which holds the internal energy, and the saturation adjustment then runs inside the next snapy step.

At `1f4f11b` evaporation is exercised by `tests/test_kinetics.cpp` through `tests/jupiter.yaml` (`H2O(l,p) => H2O`, `NH3(s,p) => NH3`, lines 92–102), but those tests print and assert nothing, and no test has a two-product evaporation.

## 3. The defect, and why no run could show it

κ carries $m^{3}$ $\mathrm{mol}^{-1}$ $s^{-1}$ and $C_{p}$ carries mol $m^{-3}$. A reaction rate in mol $m^{-3}$ $s^{-1}$ therefore needs η in mol $m^{-3}$. For $\mathrm{H_2O}$(l,p) ⇒ $\mathrm{H_2O}$, η = P\*/(RT) − $C_{v}$ is a concentration. For $\mathrm{NH_4SH}$, with the Lewis (1969) fit ln($K_{p}$/$\mathrm{Pa}^{2}$) = (14.82 − 4705/T) ln 10 + 2 ln 101325 (`vapor_functions.h:81-83`), η = $K_{p}$/(RT)$^{2}$ − $C_{\mathrm{NH_3}}C_{\mathrm{H_2S}}$ is in $\mathrm{mol}^{2}$ $m^{-6}$.

A dimensional error of this kind makes the rate depend on the unit of amount, and here the dependence is exact. The quadratic of §4.2 reads $x^{2}$ + ($C_{1}$+$C_{2}$)x = K − $C_{1}C_{2}$ = η, so

$$
\eta = x\,(C_1 + C_2 + x):
$$

today’s rate is the diffusion rate multiplied by the number $C_{1}$+$C_{2}$+x, read in whatever unit of amount the code uses. It is too slow whenever that number is below one and too fast above it; changing mol to mmol multiplies it by $10^{3}$ by construction. `compare_laws.py` evaluates the laws on six states built from card 40’s abundances and the Lewis fit, in SI and in mmol; the table confirms the identity (for example 0.0458 + 0.00143 + 0.000461 = 0.0477) rather than adding evidence beyond it:

| T \[K\] | P \[bar\] | S = $C_{1}C_{2}$/K | η/x \[mol $m^{-3}$\] | η/x \[mmol $m^{-3}$\] |
|----|----|----|----|----|
| 210 | 2.5 | 0.749 | 0.0477 | 47.7 |
| 220 | 3.0 | 0.103 | 0.0655 | 65.5 |
| 230 | 4.0 | 0.0216 | 0.121 | 121 |
| 230 | 4.0 | 0.000216 | 0.084 | 84 |

Source: `compare_laws_SI.out`, `compare_laws_mmol.out`. States: $x_{\mathrm{NH_3}}$ = $3.2\times 10^{-4}$, $x_{\mathrm{H_2S}}$ = $10^{-5}$ (card 40’s `problem` block) except the last row, which divides both by ten.

In SI units today’s rate is 0.048–0.12 of the diffusion rate on these states, i.e. 8–21× too slow. No conservation diagnostic can reveal this: mass and energy are conserved whatever the rate, since the stoichiometric column sums to zero and the latent exchange rides on the internal energy, and the saturation adjustment removes any supersaturation the step leaves. An evaporation-time-scale check could; the one that exists, the manuscript’s `plot_precipitation_evaporation_timescales.py`, covers $\mathrm{H_2O}$ and $\mathrm{NH_3}$ only (its `REACTIONS`, lines 66–69).

## 4. The rate law from steady diffusion

### 4.1 One gaseous product

A sphere of diameter d in quiescent gas, with surface concentration $C_{s}$ and ambient C, loses 2π d D ($C_{s}$ − C) moles per second in steady state (radius r gives 4πrD). Precipitation of molar concentration $C_{p}$ and molar volume $v_{m}$ in particles of one diameter has number density N = 6 $C_{p}v_{m}$/($\pi d^{3}$). The rate per unit volume is

$$
r = 2\pi d D N\,(C_s - C) = \frac{12\,D\,v_m}{d^2}\,C_p\,(C_s - C) = \kappa\,C_p\,(C_s - C),
$$

which is kintera’s κ. With the surface at saturation, $C_{s}$ = P\*/(RT) = K, so $C_{s}$ − C = η for n = 1. Ventilation, the Kelvin effect and kinetic (Fuchs) corrections are absent, as in the code.

### 4.2 Two gaseous products

For $\mathrm{NH_4SH}$(s) ⇒ $\mathrm{NH_3}$ + $\mathrm{H_2S}$ each gas leaves the particle by its own diffusion, $F_{i}$ = $\kappa _{i}C_{p}$($C_{i,s}$ − $C_{i}$) with $\kappa _{i}$ = 12 $D_{i}v_{m}$/$d^{2}$. Two conditions close the problem:

- **Stoichiometry.** The solid dissolves congruently, so one mole of each gas leaves per mole of $\mathrm{NH_4SH}$: $F_{1}$ = $F_{2}$ = F, the reaction rate.
- **Surface equilibrium.** The pure solid has unit activity, so at its surface $C_{1,s}C_{2,s}$ = K, with K = $K_{p}$/(RT)$^{2}$ (manuscript eq. 40 with n = 2).

With equal diffusivities, $\kappa _{1}$ = $\kappa _{2}$ = κ (the code carries one `diff_c` per reaction), write x = F/($\kappa C_{p}$). Then $C_{i,s}$ = $C_{i}$ + x and

$$
(C_1 + x)(C_2 + x) = K \quad\Leftrightarrow\quad x^2 + (C_1+C_2)\,x - (K - C_1C_2) = 0.
$$

The physical root is the one with both surface concentrations positive, $C_{i}$ + x \> 0:

$$
x = \tfrac12\left[-(C_1+C_2) + \sqrt{(C_1-C_2)^2 + 4K}\right] = \frac{2(K - C_1C_2)}{(C_1+C_2) + \sqrt{(C_1-C_2)^2 + 4K}}.
$$

The two forms are equal (multiply the first by its conjugate and use ($C_{1}$−$C_{2}$)$^{2}$ + 4K − ($C_{1}$+$C_{2}$)$^{2}$ = 4(K − $C_{1}C_{2}$)). The second has no subtraction of nearly equal numbers and is the one to evaluate. Its sign is the sign of K − $C_{1}C_{2}$, so it is positive exactly when the air is subsaturated, as η is, and it is clamped at zero in the same place. The rate is r = $\kappa C_{p}$x. The other root has $C_{i}$ + x \< 0 for both gases and is unphysical.

### 4.3 Limits

| regime | x | reading |
|----|----|----|
| near equilibrium, K − $C_{1}C_{2}$ small | (K − $C_{1}C_{2}$)/($C_{1}$+$C_{2}$) | the linearisation; η divided by a concentration |
| one gas abundant, $C_{1}^{2}$ \>\> K, $C_{1}$ \>\> $C_{2}$ | K/$C_{1}$ − $C_{2}$ | the single-vapour law for the minor gas, whose saturation concentration is K/$C_{1}$ |
| both gases absent | √K | each surface concentration is √K |
| one product (n = 1) | K − C | today’s η, the same expression |

Card 40 carries 32 times more $\mathrm{NH_3}$ than $\mathrm{H_2S}$ (`xNH3: 3.2e-4`, `xH2S: 1.e-5`), but the second row also needs $C_{1}^{2}$ \>\> K, which depends on temperature as much as on S ($C_{1}^{2}$/K = 24, 3.3, 0.69 on the states with S = 0.749, 0.103, 0.0216): at 230 K, 4 bar, $C_{\mathrm{NH_3}}$ = 0.0669 is below √K = 0.0805 and the limiting-species form is off by 1.8× (§7). Which row applies depends on how far below the cloud the precipitation has fallen; the quadratic covers all of them.

### 4.4 General stoichiometry, and what the law is

For products with coefficients $\nu _{i}$ and equal diffusivities, the flux of gas i is $\nu _{i}$F, so $C_{i,s}$ = $C_{i}$ + $\nu _{i}$x and x solves

$$
g(x) = \sum_i \nu_i \ln(C_i + \nu_i x) - \ln K = 0.
$$

g is strictly increasing on x \> $\mathrm{max}_{i}$(−$C_{i}$/$\nu _{i}$) and runs from −∞ to +∞ there, so the root is unique, and it is positive exactly when $\prod C_{i}^{\nu _{i}}$ \< K. Adding $x\nu _{i}$ to each product concentration is advancing the evaporation reaction by an extent x; the equation says that this extent brings the ambient air to equilibrium at fixed T. **The rate is κ $C_{p}$ times the fixed-T extent to equilibrium.** Its zero set is the equilibrium condition of manuscript eq. 38: x = 0 exactly when $\prod C_{i}^{\nu _{i}}$ = K. It is not the extent the saturation adjustment applies, which linearises the logarithmic residual (eqs. 46–50), holds the internal energy rather than T (eqs. 41–43), and acts on the cloud species rather than the precipitation. The fixed-T extent is what makes §5 work, and it is the natural general form. This design implements only n = 1 (closed form, unchanged) and two products with ν = 1 (the quadratic); any other product stoichiometry is rejected with an error at construction (§8), because no card needs it and a Newton root inside the rate constant is a separate piece of work.

## 5. One implicit step

For a single reaction the per-cell system of §2 step 4 reduces to a scalar. With Δξ = Sε, (I/Δt − SJ)Sε = Sr gives ε(1/Δt − J·S) = r, and J·S = dr/dε, the derivative of the rate along the reaction. So one step is

$$
\Delta = \frac{r\,\Delta t}{1 - \Delta t\,\mathrm{d}r/\mathrm{d}\varepsilon},
$$

at fixed T (§2 step 3). Along the evaporation reaction each product gains $\nu _{i}$dε and the precipitation loses dε.

### 5.1 With the extent law

Differentiating g(x(ε)) = 0 with $dC_{i}$/dε = $\nu _{i}$: $\sum \nu _{i}$($\nu _{i}$ + $\nu _{i}$dx/dε)/($C_{i}$+$\nu _{i}$x) = 0, hence **dx/dε = −1** exactly, for any stoichiometry. With r = $\kappa C_{p}$x and $dC_{p}$/dε = −1, dr/dε = −κ($C_{p}$ + x), and with a = κΔt,

$$
\Delta = \frac{a\,C_p\,x}{1 + a(C_p + x)}.
$$

Because 1 + a($C_{p}$ + x) \> $aC_{p}$ and \> ax, Δ \< x and Δ \< $C_{p}$ for every Δt \> 0. One step cannot carry the air past equilibrium at the step’s temperature, and cannot evaporate more precipitation than there is. For n = 1 this is the bound previously recorded for single-product evaporation; the extent law extends it to every stoichiometry.

### 5.2 With today’s law

Two products, ν = 1: dη/dε = −($C_{1}$+$C_{2}$) − 2ε, which is −($C_{1}$+$C_{2}$) at ε = 0 where the Jacobian is taken. So dr/dε = −κ(η + $C_{p}$($C_{1}$+$C_{2}$)) and

$$
\Delta = \frac{a\,C_p\,\eta}{1 + a\left(\eta + C_p(C_1+C_2)\right)}.
$$

Δ \< $C_{p}$ still holds, but the bound on the gas side is η/($C_{1}$+$C_{2}$). From the quadratic, η = x($C_{1}$+$C_{2}$) + $x^{2}$, so

$$
\frac{\eta}{C_1+C_2} = x\left(1 + \frac{x}{C_1+C_2}\right) > x.
$$

Substituting η = x($C_{1}$+$C_{2}$+x) into Δ \> x and simplifying gives the exact condition for today’s step to pass equilibrium:

$$
\Delta > x \quad\Leftrightarrow\quad C_p > C_1 + C_2 + x + \frac{1}{a\,x}.
$$

The cell must hold more precipitation, in moles, than the ambient $\mathrm{NH_3}$ plus $\mathrm{H_2S}$ plus the equilibrium extent. The upper bound on the overshoot, approached as $C_{p}$ → ∞ at any a, is the factor 1 + x/($C_{1}$+$C_{2}$):

| S        | equilibrium extent x | today, η/($C_{1}$+$C_{2}$) | ratio |
|----------|----------------------|----------------------------------------|-------|
| 0.749    | 4.61e-4              | 4.66e-4                                | 1.01  |
| 0.103    | 1.14e-2              | 1.38e-2                                | 1.21  |
| 0.0216   | 5.23e-2              | 9.19e-2                                | 1.76  |
| 0.000216 | 7.71e-2              | 9.39e-1                                | 12.2  |

Source: `compare_laws_SI.out`, columns `x_quad` and `BEinf_now`; concentrations in mol $m^{-3}$.

That bound is not reachable on card 40. The condition needs more $\mathrm{NH_4SH}$ precipitation, in moles, than ambient $\mathrm{NH_3}$; over every cell of every frame of card 40’s own run the largest ratio is $1.05\times 10^{-4}$ (`card40_ratio.out`; the precipitation-to-$\mathrm{H_2S}$ ratio, by contrast, reaches $2.2\times 10^{5}$ where $\mathrm{H_2S}$ is locally exhausted, so $\mathrm{H_2S}$ alone does not bound it). The scalar model on the tabulated states, with precipitation equal to and ten times the $\mathrm{H_2S}$ abundance, at card 40’s own a = κΔt = 13.3 (κ = 1.049 $m^{3}$ $\mathrm{mol}^{-1}$ $s^{-1}$, Δt = 12.69 s from its run log) and at the stiff $10^{6}$:

| S        | $C_{p}$/$C_{\mathrm{H_2S}}$ | a    | today Δ/x | extent law Δ/x |
|----------|-------------------------------|------|-----------|----------------|
| 0.749    | 1                             | 13.3 | 9.08e-4   | 0.0186         |
| 0.749    | 10                            | 13.3 | 9.01e-3   | 0.159          |
| 0.749    | 10                            | 1e6  | 0.977     | 0.969          |
| 0.103    | 10                            | 13.3 | 0.0140    | 0.159          |
| 0.103    | 10                            | 1e6  | 0.657     | 0.590          |
| 0.0216   | 10                            | 13.3 | 0.0306    | 0.141          |
| 0.0216   | 10                            | 1e6  | 0.326     | 0.286          |
| 0.000216 | 10                            | 13.3 | 2.15e-3   | 0.0136         |

Source: `step_overshoot.out` (24 rows including a = $10^{2}$; a selection here). The scalar model is §5.1–5.2’s formula, not kintera’s solver.

No row passes equilibrium. At card 40’s a = 13.3 today’s step is 4.6–20.5× smaller than the extent law’s, the practical consequence of §3; in the stiff limit the two agree to within 14 %, today’s usually the larger. The overshoot of today’s law is a property of the formula, not an effect card 40 exhibits; the guarantee of §5.1 matters for configurations with more precipitation than ambient vapour.

### 5.3 What §5 does not cover

- **Temperature.** Evaporation cools the air and lowers K, so the equilibrium extent at the end of the step is smaller than x at the start. With `evolve_temperature` off the linearisation cannot see this; the bound is on the fixed-T extent.
- **Coupled reactions.** The argument is for one reaction. Card 40 also evaporates $\mathrm{NH_3}$(s,p) into the same $\mathrm{NH_3}$; the full system is not reduced to a scalar.
- **The clamp.** x is clamped at zero, so its derivative is zero on the supersaturated side, where the rate is zero anyway.

## 6. Literature

| source | what it does | checked |
|----|----|----|
| Zaveri, Easter, Fast & Peters 2008, JGR 113, D13204 (MOSAIC) | $\mathrm{NH_4Cl}$ and $\mathrm{NH_4NO_3}$: equal fluxes of the two gases, surface product = $K_{\mathrm{eq}}$, a quadratic for the surface concentration with unequal transfer coefficients $k_{A}$ ≠ $k_{B}$, a series branch against cancellation; k = $2\pi D_{p}ND_{g}$f(Kn,α), the same diffusion factor as $\kappa C_{p}$ | source code read; paper behind a paywall |
| Sugiyama et al. 2011 GRL doi:10.1029/2011GL047878; 2014 Icarus 229, 71 | Jupiter $\mathrm{NH_4SH}$: the equal-shift root X = ½\[($p_{1}$+$p_{2}$) − √(($p_{1}$−$p_{2}$)$^{2}$+$4K_{p}$)\] used both for saturation adjustment and as the undersaturation in the Kessler rain-evaporation rate | source code and thesis read |
| Wexler & Seinfeld 1990, Atmos. Environ. 24A, 1231 | single-particle $\mathrm{NH_3}$/$\mathrm{HNO_3}$/HCl fluxes from the vapour profiles around the particle; the origin of the formulation above | abstract only |
| Harrison, Sturges, Kitto & Li 1990, Atmos. Environ. 24A, 1883 | measured dry $\mathrm{NH_4Cl}$/$\mathrm{NH_4NO_3}$ evaporation much slower than diffusion predicts; a surface-kinetic limit | abstract only |
| Carlson, Rossow & Orton 1988, J. Atmos. Sci. 45, 2066 | condensation time constants; $\mathrm{NH_4SH}$ through ln K = ΔG/RT; no two-gas flux law | pp. 2066–2070 read |
| Gao & Benneke 2018, ApJ, doi:10.3847/1538-4357/aad461 | ZnS from Zn + $\mathrm{H_2S}$ with $\mathrm{H_2S}$ in excess: the limiting-species form, the second row of §4.3 | paper read |

The diffusion-limited law is therefore standard where dissociating condensates are modelled with explicit mass transfer. Harrison et al. make it an upper bound for dry salts; the same caution applies here and is not addressed by this change.

## 7. Alternatives considered

| form | units | behaviour on the tabulated states | verdict |
|----|----|----|----|
| today, $\kappa C_{p}$(K − $C_{1}C_{2}$) | wrong | 0.048–0.12 of the diffusion rate in SI; overshoots in one step | defect |
| $A_{2}$(K − $C_{1}C_{2}$), $A_{2}$ free (after manuscript Table 1, which writes $A_{2}$\[exp $f_{3}$(T) − p($\mathrm{NH_3}$)p($\mathrm{H_2S}$)\]$^{+}$ in partial pressures and without the precipitation factor) | consistent if $A_{2}$ carries them | no physical meaning for `diff_c`, `vm`, `diameter`; overshoot unchanged | rejected: every card supplies diffusion parameters |
| √K (1 − $C_{1}C_{2}$/K) | right | right only with both gases absent; 5.1× too fast at S = 0.749 (2.35e-3 vs 4.61e-4) | rejected |
| limiting species, K/$C_{\mathrm{major}}$ − $C_{\mathrm{minor}}$ | right | right near saturation (4.8e-4 vs 4.61e-4); 12.6× too fast at S = 2.16e-4 (0.968 vs 0.0771) | rejected; it is a limit of the chosen law |
| quadratic, unequal $D_{i}$ (MOSAIC) | right | exact for unequal diffusivities | deferred: needs a second diffusivity in the card format; the code has one |
| **quadratic, equal D** | right | all limits of §4.3; n = 1 unchanged; no overshoot | **chosen** |

Numbers: `compare_laws_SI.out` columns `x_sqrtK`, `x_limit`, `x_quad`.

## 8. Implementation

One commit, `f94a335`, touching `src/kinetics/evaporation.cpp`, `src/kinetics/evaporation.hpp` and the new `tests/test_evaporation_extent.py`.

- **Construction check** (`EvaporationImpl::reset`). Every evaporation reaction must be irreversible, with exactly one reactant and one or two products, every coefficient 1; otherwise a `TORCH_CHECK` names the reaction. This also rejects single-product forms such as `2 H2O(l,p) => H2O`. The indices of the two-product reactions are kept in a plain member `two_product_rxns_`, not a registered buffer, so a module dtype cast cannot turn them into floats (the pattern of `KineticsImpl::rev_indices_`); they are moved to the device at use.
- **Rate constant** (`EvaporationImpl::forward`). The saturation term is kept in a variable, `ksat`, and today’s `eta = ksat − ∏C^ν`, clamped at zero, is computed for every reaction exactly as before. For the two-product reactions only, selected along the reaction axis: the concentrations are clamped at zero; the product and the sum of the two product concentrations are formed with the product mask (a `where` for the sum, so a non-finite value in another species cannot enter); the root is `√(max(sum^2 − 4·prod, 0) + 4·ksat)`, algebraically √(($C_{1}$−$C_{2}$)$^{2}$ + 4K) and index-free, with its argument and the denominator floored at the smallest normal number of float32 for float32 tensors and of float64 otherwise (float16 and bfloat16 fall back to the float64 value; no kintera path uses them); x = 2(ksat − prod)/(sum + root), clamped at zero, is written back with `index_copy`. The returned value is κ times that η.
- **Consequences checked by audit.** Single-product columns keep their values and their autograd derivatives bit for bit (`index_copy` passes the gradient of untouched columns through). The floors change nothing while K is a normal number. The sum-minus-four-product form cancels only when $C_{1}$ ≈ $C_{2}$, where the sum squared is at most about 4K, so the loss stays at the ulp level: over 200 000 random subsaturated states concentrated near $C_{1}$ = $C_{2}$ and near saturation the worst relative difference in x from the direct ($C_{1}$−$C_{2}$)$^{2}$ form is $5.8\times 10^{-16}$ (`root_precision_probe.py` → `root_precision_probe.out`). The GPU path uses only `index_select`, `index_copy` and `where`; it was not run on a GPU. The index member costs one small host-to-device copy per call on CUDA, as `rev_indices_` does.
- **Not changed:** κ, the saturation functions, the mass-action factor, the implicit solver, and the unused `_jacobian_evaporation`.

## 9. Limits of the model, unchanged by this work

- **Equal diffusivities** for the two gases (one `diff_c` per reaction). A Chapman–Enskog estimate made during the audit, not a measurement, puts D($\mathrm{NH_3}$–$\mathrm{H_2}$)/D($\mathrm{H_2S}$–$\mathrm{H_2}$) near 1.3; in the $\mathrm{H_2S}$-limited regime the flux is set by $\mathrm{H_2S}$’s diffusivity alone, so what matters there is which gas `diff_c` represents. MOSAIC’s unequal-k quadratic is the extension.
- Monodisperse particles, no ventilation, no Kelvin or kinetic (Fuchs–Sutugin) correction.
- **No Stefan flow.** The diffusion law assumes a dilute vapour. Negligible for $\mathrm{NH_4SH}$ at mole fractions below $10^{-3}$; the same assumption sits in the single-product law, where it is not negligible for a non-dilute condensable such as $\mathrm{H_2O}$ on a water-rich planet, the setting the manuscript is about.
- **No particle-temperature (Mason) term.** The particle cools as it evaporates; with a reaction enthalpy near 90 kJ $\mathrm{mol}^{-1}$ the audit’s rough estimate is a correction of a few to about 20 % on the subsaturated states. Not estimated here with any rigour.
- The diffusion-limited rate is an upper bound for dry dissociating salts (Harrison et al. 1990).
- Fixed temperature in the implicit step (§5.3).

## 10. Validation record

Builds: the pinned venv (kintera `1f4f11b`); separate builds of `b00ffa1` (an intermediate commit) and `3d2a1ec`, whose C++ is identical to `f94a335` (the two commits differ only in `tests/`). The two separate builds used `PNETCDF=OFF`.

### 10.1 Unit tests, written to fail first

`tests/test_evaporation_extent.py`, 22 cases, one file in its own process (kintera’s species registry is global):

- the two-product rate equals κx against an independent Python evaluation, on six states ($\mathrm{NH_3}$-rich, far below saturation, equal abundances, empty air, S = 0.9995, supersaturated), and on the five subsaturated ones the surface residual ($C_{1}$+x)($C_{2}$+x)/K − 1 is below $10^{-10}$;
- a single-product reaction beside a two-product one has the same rate and the same derivative as on its own, expanded and unexpanded; expanded and unexpanded concentrations give identical rates; the derivative matches a central finite difference;
- at 10 K, where K underflows to zero, the rate is zero and the gradient finite, in float64 and float32, for $C_{1}$ = $C_{2}$ = 0 and $10^{-3}$;
- negative product concentrations give the empty-air rate $\kappa C_{p}$√K;
- five other stoichiometries, including a reversible one, are rejected;
- through the real `Kinetics` (a card loaded in a subprocess: `forward`, `jacobian`, `evolve_implicit`): the rate is $\kappa C_{p}$x, and one step with $C_{p}$ = 1 mol $m^{-3}$ and Δt = $10^{6}$ s leaves $C_{1}C_{2}$ ≤ K and $C_{p}$ ≥ 0.

The unit-scaling test planned in revision 2 was not written. Matching the rate to κx from a dimensionally consistent formula to $10^{-10}$ already establishes that the code computes that function, and its scaling follows from the formula; kintera’s constants are SI, so the unit of amount cannot be changed inside the code to test it directly.

**A test repair after the fix was built.** The first run of the final test file on `3d2a1ec` had four failures, in every arm alike: the float32 underflow test called `_both().to(dtype)`, and the module binding’s `.to` returns `None`. The call was split in two, and the H2O reaction in the `Kinetics` subprocess was given non-zero concentrations so the single-product gate is not degenerate. That is commit `f94a335`, which changes only `tests/`; the counts below are from the rerun.

| build | result | log |
|----|----|----|
| pin `1f4f11b` | 13 failed, 9 passed | final test log |
| intermediate `b00ffa1` | 2 failed, 20 passed | same; the two failures are the float32 underflow cases the second audit of the code found (`final/b00ffa1_failures.out`) |
| **final (`3d2a1ec` = `f94a335` C++)** | **22 passed** | same |

The nine cases that pass on the pin are the regression guards (supersaturated state, single-product identity ×2, shapes, finite difference, float64 and float32 underflow), meant to pass on both. Through `Kinetics` on the pin, the stiff step leaves $C_{1}C_{2}$ = 0.238 against K = $6.48\times 10^{-3}$: today’s law does overshoot in kintera’s own solver once $C_{p}$ exceeds the ambient gases, as §5.2 predicts.

### 10.2 Bit-identity gates

`gate/kinetics_gate.py` runs the test file’s `Kinetics` subprocess and prints every value as a hexadecimal float. Pin versus final: the single-product (`H2O(l,p) => H2O`) rate and its `rc_ddC` column are identical. `b00ffa1` versus final: every field identical. The reason the card runs of §10.4 on `b00ffa1` stand for the final commit is the C++ diff between the two (`git diff b00ffa1 3d2a1ec -- src`): a renamed mask, the float32-only floor, and a comment; the gate is consistent with it, on two states. Outputs: `final/gate_*.out`.

### 10.3 Existing kintera tests

Every `tests/test*.py` run on the pin and on `b00ffa1` (suite logs; for `test_equilibrate_uv_gain.py` the summary line is in `suite/equilibrate_uv_gain_summary.out`, 3 passed on both): identical results for every existing file; only the new file differs. The suite was not rerun on the final C++, and kintera’s C++ ctest was not run.

### 10.4 Card 40, before and after

Four arms, seeded (`initialization.seed: 12345`; the card’s IC kick is otherwise unseeded), 20 CPU ranks, t = $2\times 10^{5}$ s, all `RUN_EXIT=0`, 15764 cycles each: `pin_a`, `pin_b` (pinned kintera), `fix_a`, `fix_b` (build of `b00ffa1`). Reductions `card40/card40_compare.py` and `card40_pairs.py`: domain totals ∑ρy per output frame.

| $\mathrm{NH_4SH}$ precipitation, mean of frames 1–8 | relative difference |
|----|----|
| pin_b / pin_a (same code) | −0.431 |
| fix_b / fix_a (same code) | +0.019 |
| fix / pin, four cross pairs | −0.545, −0.199, −0.536, −0.184 |

All four cross pairs have the sign the fix predicts (faster evaporation, less precipitation), but the two runs of the pinned code differ by as much, and two cross pairs change sign in individual frames. **The card-level effect is not attributable at this sample size.** $\mathrm{H_2S}$ totals agree to better than $7\times 10^{-4}$ in every pair (largest $6.25\times 10^{-4}$, `card40_pairs.out`); $\mathrm{H_2O}$ and $\mathrm{NH_3}$ precipitation move without a consistent sign. The seeded card is not run-to-run reproducible: the two pinned runs already differ at frame 0 ($\mathrm{NH_3}$ total $6\times 10^{-8}$), unlike a seeded 16-rank card in earlier work, which was bitwise reproducible; the source was not pursued. An attributable card-level measurement needs a deterministic configuration or an ensemble.

### 10.5 Not done

- snapy’s `jupiter_evap_precip_1d`: its driver is C++ (`examples/jupiter_evap_precip_1d.cpp`) and links kintera, so it needs snapy’s examples rebuilt against the new kintera; not attempted.
- GPU execution of the new path; landing on the pinned branch.

## 11. Carrying this commit forward

**Branch.** One kintera commit, `f94a335` on `1f4f11b`. It is **not** merged into the pinned branch, and no venv carries it.

**Rule for future pins.** Any new kintera production pin, and any rebase of the pinned branch onto a newer upstream, must include `f94a335`. It is carried as its own commit: cherry-picked onto the new base, re-run through `tests/test_evaporation_extent.py` (22 cases, all must pass) and `gate/kinetics_gate.py` (single-product rate and `rc_ddC` bit-identical to the base). A pin without it silently brings back the dimensionally inconsistent $\mathrm{NH_4SH}$ evaporation rate.

**What adopting it changes.** Only reactions of `type: evaporation` with two gaseous products; in every card that is `NH4SH(s,p) => NH3 + H2S`, whose evaporation becomes faster (8–21× on the §3 states). Single-product evaporation, gas-phase kinetics, nucleation and the saturation adjustment, and coagulation are untouched. A card whose evaporation reaction is reversible, has more than one reactant, three or more products, or a coefficient other than 1 now fails at load time with an error.

**Cards and runners need no change.** The card keys (`diff_c`, `diff_T`, `diff_P`, `vm`, `diameter`, `formula`) keep their meaning, and the runners call `evolve_kinetics` as before; card 40 ran unmodified on the fix (§10.4). Every evaporation reaction in the card corpus passes the new check: 60 card files with a reactions block (example decks, the 22 snapy example cards at `29e513b`, the manuscript’s Jupiter reference cards) contain 49 `H2O(l,p) => H2O`, 48 `NH3(s,p) => NH3`, 13 `NH4SH(s,p) => NH3 + H2S`, 4 each of `CH4(s,p)`, `H2S(s,p)`, `MgSiO3(s,p)` and one `H2S(l,p)` evaporation, none rejected (`card_check.py` → `card_check.out`).

**Expect moved numbers.** Any Jupiter run with $\mathrm{NH_4SH}$ precipitation will differ once the pin carries this commit; that is the fix, not a regression. The card-level size is not yet measured (§10.4).

## Appendix A — identifiers

| item | where |
|----|----|
| rate constant | kintera `src/kinetics/evaporation.cpp:89-121` @ `1f4f11b` |
| mass action | `src/kinetics/kinetics.cpp:405` |
| assembled Jacobian | `src/kinetics/kinetics.cpp:268-299` |
| unused analytic Jacobian | `src/kinetics/jacobian_evaporation.cpp` |
| `evolve_temperature` default | `src/kinetics/kinetics.hpp:81` |
| implicit per-cell solve | `src/kinetics/evolve_implicit_impl.h` |
| Lewis $\mathrm{NH_4SH}$ fit | `src/vapors/vapor_functions.h:81-86` |
| cards with a two-product evaporation (the `equation:` line) | card 40 `40_jupiter_nh4sh_slab_cpu/config.yaml:214`; snapy `examples/jupiter_crm.yaml:183`, `jupiter_gcm.yaml:180`, `jupiter_evap_precip_1d.yaml:166` (@ `29e513b`); nine of the manuscript’s Jupiter reference cards, e.g. `jup_crm3d_H2O-NH3-H2S_F100_nu0.01.yaml:196` |
| evaporation smoke test | `tests/test_kinetics.cpp` with `tests/jupiter.yaml:92-102` (no assertions) |
| comparison scripts and outputs | `compare_laws.py` (its printed κ is for reference only and is not used by the ratios) and `step_overshoot.py` |

§1–7 written 2026-09-16 from source read at the commits named above and from the scripts in the evidence directory; §8 and §10 written 2026-09-17 from the commit and the logs named there.
