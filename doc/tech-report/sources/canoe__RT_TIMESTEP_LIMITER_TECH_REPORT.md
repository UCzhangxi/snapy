> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.
# A radiative timestep limiter that releases itself

Why `E/ΔF` is the wrong invariant, what the right one is, and how to derive it from the stability of the explicit source update.

2026-08-26/27 · snapy `hj2024_runner.py`

**It ran.** snapy, 6 ranks on one A100: **cycle 1 took `dt = 215.07 s` against the 215.2 s predicted from the §4 table before the job was submitted**, then released — the minimum dt over 26 926 cycles and 77 sim-days is still that cycle-1 value. It bound once, at the least-safe moment, and never again.

**Summary.** An explicit radiative source term is a *relaxation*, and the timestep that keeps it stable is set by the **derivative** ∂Q/∂T, not by the magnitude of the heating. A limiter built on the magnitude — $\tau = \Delta z\,E/\Delta F$ — diverges to infinity exactly at radiative equilibrium, the point where the explicit update is *most* fragile.

The replacement is one line of physics: $τ_{rad} = ρc_{v}/λ$ with `λ = 16 κ ρ σT³ ε`. It is finite everywhere, needs no ramp, needs no radiative-transfer solution, and **releases itself** as $τ_{rad} ∝ T^{-3}$ when the atmosphere cools. On the healthy 2024 card it clips day 0 and never binds again; on the 6.8×-more-opaque ISSI card it binds at cycle one instead of letting the run die around day 40.

## 1. The problem: an explicit source term with a short intrinsic timescale

Radiation enters the energy equation as a volumetric source. The runner applies it operator-split and explicitly:

$$u^{n+1} = u^n + Q(T^n)\,\Delta t,\qquad u = \rho c_v T\ [\mathrm{J\,m^{-3}}],\qquad Q = -\,dF/dz\ [\mathrm{W\,m^{-3}}]$$

Nothing about this is unusual, and for most of the atmosphere it is harmless. The trouble is the model top. There the gas is optically thin and hot, it radiates efficiently to space, and its heat capacity per unit volume is tiny — so its temperature responds to radiation on a timescale that can fall below the hydrodynamic timestep. When that happens, forward Euler overshoots: the cell cools past its equilibrium, the sign of the heating flips, and the next step overshoots the other way, with growing amplitude.

So we need a bound on Δt. The whole question is *which* bound.

## 2. Why the magnitude invariant is wrong

`τ = Δz E/ΔF = E/Q` answers the question *“how long until this cell's energy budget is exhausted at the current heating rate?”* That is a statement about the **size** of Q. Stability is a statement about its **slope**. The two come apart in the worst possible way:

- At radiative equilibrium `Q → 0`, so `E/Q → ∞` and the limiter **switches off entirely**. But ∂Q/∂T at equilibrium is *maximal*. Equilibrium is precisely where an explicit relaxation oscillates and diverges if Δt exceeds the relaxation time.

## 3. Deriving the right criterion

### 3a. Linearise the source

Write `T = T̄ + T′` and expand Q about the current state:

$$Q(T) \approx Q(\bar T) + (\partial Q/\partial T)\,T^\prime \equiv Q(\bar T) - \lambda T^\prime,\qquad \lambda \equiv -\partial Q/\partial T$$

λ \> 0 for a restoring response: heat the cell and it radiates harder. Substituting into $ρc_{v} dT/dt = Q$, the perturbation obeys

$$dT^\prime/dt = -T^\prime/\tau,\qquad \tau = \rho c_v/\lambda$$

### 3b. What forward Euler needs

Applying $T′^{n+1} = (1 - Δt/τ) T′^{n}$:

| condition         | on Δt    | behaviour                               |
|-------------------|----------|-----------------------------------------|
| \|1 − Δt/τ\| \< 1 | Δt \< 2τ | **stable** — amplitude decays           |
| 1 − Δt/τ \> 0     | Δt \< τ  | **monotone** — no sign flip, no ringing |

Monotonicity is the property worth buying: a scheme that merely decays while alternating sign still produces a cell that flips between 2900 K and something absurd on alternate steps. So we take `Δt = C τ` with `C ≤ 1`. `C = 0.5` halves the perturbation each step and leaves 4× margin to the stability boundary.

### 3c. λ for grey thermal emission

A grey absorber of mass opacity κ emits, per unit volume, `4πκρB(T) = 4κρσT⁴` (using `B = σT⁴/π`). Absorption depends on the *incident* field, not on the local T, so to first order it does not contribute to the slope. Hence

$$\lambda = \partial/\partial T\,[4\kappa\rho\sigma T^4] = 16\,\kappa\rho\sigma T^3 \;\Rightarrow\; \tau = \rho c_v/(16\kappa\rho\sigma T^3) = c_v/(16\kappa\sigma T^3)$$

Note ρ cancels. This is the familiar Newtonian radiative relaxation time; the factor 16 is `d(T⁴)/dT = 4T³` times the 4 in the emission coefficient. Forms quoted with $c_{p}/(4κσT³)$ differ by the $c_{p}$/$c_{v}$ choice and by whether the 4 from the derivative is carried; use the one consistent with the energy variable you are actually stepping, which here is internal energy at constant volume.

### 3d. The optical-depth correction, and why it is load-bearing

A cell thick enough to reabsorb its own emission cannot respond as fast as the thin formula says. The standard closure is the **escape probability**

$$\varepsilon(\tau_{\mathrm{cell}}) = (1 - e^{-\tau_{\mathrm{cell}}})/\tau_{\mathrm{cell}},\qquad \tau_{\mathrm{cell}} = \kappa\rho\Delta z$$

with `ε → 1` when thin and $ε → 1/τ_{cell}$ when thick. The final criterion is therefore

$$\lambda = 16\,\kappa\rho\sigma T^3\varepsilon,\qquad \tau_{\mathrm{rad}} = \rho c_v/\lambda = c_v/(16\kappa\sigma T^3\varepsilon)$$

$$\Delta t = \min(\Delta t_{\mathrm{hydro}},\ C\cdot\min_{\mathrm{domain}}\tau_{\mathrm{rad}}),\qquad C = 0.5$$

**ε is not decoration.** ρ cancels everywhere else, so *without* ε every cell in an isothermal column returns the identical $τ_{\mathrm{rad}}$ and the optically thick deep atmosphere binds just as hard as the thin top. On the 2024 column that is 430 s imposed by a cell whose true relaxation time is 52 254 s — a 120× spurious penalty.

A useful check on the closure: in the thick limit $τ_{rad} → c_{v}ρΔz/(16σT³)$ and **κ cancels**. That is right — once a cell is opaque, making it more opaque does not change how fast it can cool.

## 4. Numbers

The 2024 card's initial column (isothermal 2879.83 K, $κ_{\mathrm{LW}}$ = $10^{-3}$ m² kg$^{-1}$, Δz = 70 312.5 m, $c_{v}$ = 9285 J kg$^{-1}$ K$^{-1}$):

| P \[bar\] | ρ         | $τ_{\mathrm{cell}}$ | ε      | $τ_{\mathrm{rad}}$ \[s\] |
|-----------|-----------|------------------|--------|-----------------------|
| 185.50    | 1.734e+00 | 1.219e+02        | 0.0082 | 52253.7               |
| 50.00     | 4.675e-01 | 3.287e+01        | 0.0304 | 14084.6               |
| 1.00      | 9.350e-03 | 6.574e-01        | 0.7329 | 584.7                 |
| 0.0130    | 1.215e-04 | 8.540e-03        | 0.9957 | **430.3**             |

Column minimum 430.3 s, so $C τ_{rad} = 215 s$.

### 4a. Self-release

$τ_{rad} ∝ T^{-3}$, so the constraint evaporates as the top cools — from physics, not from a clock:

| top T | $τ_{\mathrm{rad}}$ | C $τ_{\mathrm{rad}}$ | binding vs $Δt_{\mathrm{hydro}}$ ≈ 124–227 s? |
|----|----|----|----|
| 2880 K | 430 s | 215 s | yes, once, at t = 0 |
| 2000 K | 1285 s | 642 s | no |
| 1261 K | 5126 s | 2563 s | no — 40× clear |

### 4b. Why the ISSI card is the hard one

The ISSI science card carries $κ_{LW} = 6.8×10^{-3}$ against the 2024 card's $10^{-3}$. Since $τ_{rad} ∝ 1/κ$, the ISSI card is **6.8× stiffer radiatively** while its hydro CFL is unchanged. That single ratio is the quantitative answer to why one card is easy and the other is not:

| ISSI top T | $τ_{\mathrm{rad}}$ | C $τ_{\mathrm{rad}}$ | binding?  |
|------------|-----------------|-------------------|-----------|
| 2858 K     | 66.7 s          | 33.4 s            | yes, hard |
| 1800 K     | 267 s           | 134 s             | yes       |
| 1436 K     | 526 s           | 263 s             | releasing |
| 1200 K     | 901 s           | 451 s             | free      |

So the cost is a *transient* during the hot spin-down, not a permanent tax. Once the ISSI top passes ~1400 K the limiter lets go and Δt returns to the hydro CFL.

## 5. Implementation

### 5a. Rank safety — the part that must not be got wrong

`block.max_time_step()` **MIN-reduces Δt across ranks in C++**, so every rank leaves it holding the same number. Applying a *rank-local* bound afterwards makes them disagree; the ranks then reach the output collective at different cycles and the job dies in `commux tag_recv failed: Message truncated`.

The fix is not to avoid touching Δt — it is to make the thing you touch it with **already global**. $τ_{rad}$ is MIN-all-reduced over the domain *before* the `min()`, so both operands are identical on every rank and so is the result.

The reduction uses a **separate gloo group on `MASTER_PORT+1`**: snapy has owned the default process group since \#181 and its transport may be ucx/commux on device memory, so re-registering underneath it would change the halo path. One CPU double per step. If the group cannot be formed on a multi-rank run, the runner **refuses to start** rather than silently applying a rank-local bound.

### 5b. Two guards that are not optional

**Unphysical cells must be excluded explicitly, not absorbed.** A cell with `T ≤ 0`, `ρ ≤ 0` or `P ≤ 0` belongs to the EOS repair, not to the timestep. Letting `clamp(λ, min=tiny)` turn it into a huge $τ_{rad}$ that `min()` ignores is safe *by accident* and it is silent. Exclude such cells, **count them, and report**; if every cell is dead, raise rather than return a number.

**The flux-reuse interval must obey the same criterion.** The runner applies the radiative source every step but recomputes it only on the RT cadence, so the source is FROZEN across `max(Δt, cooldown)`. The derivation in §3 assumes re-evaluation each step. If the frozen interval exceeds $2τ_{rad}$ the bound is a fiction however perfect the limiter is — on the ISSI card a 200 s cooldown against $2τ_{rad} = 133 s$ violates it on its own. Warn at decade intervals at minimum. **The clean fix, unbuilt: force an RT recompute on any step where the limiter binds.**

### 5c. snapy — `hj2024_runner.py`

    tau   = kappa * rho * dz
    eps   = (1 - exp(-tau))/tau            # series 1 - tau/2 + tau^2/6 below 1e-6
    cv    = P/(rho*T)/(gamma-1)            # Rd = P/(rho T), pointwise
    lam   = 16 * kappa * rho * sigma * T**3 * eps
    trad  = (rho*cv/lam).min()             # block minimum

    trad  = allreduce_MIN(trad)            # DOMAIN minimum, before dt is touched
    dt    = min(dt, safety * trad)

κ is rebuilt from the live `GreyOpacity` object's own `kappa_terms`/`kappa_cut`, so a pressure-dependent opacity is handled and the limiter can never bound a different opacity than the RT actually uses. Config: `radiative-transfer.rt_limiter: off|relax` (default `off`) and `rt_limiter_safety` (default 0.5, validated to (0, 1\]).

## 6. Verification

| test | result |
|----|----|
| 2024 IC column, domain minimum | 430.33 s vs 430.3 by hand — OK |
| single thin cell ($τ_{\mathrm{cell}}$ = 8.5e−3) → ε→1 limit | 430.33 vs 428.50 — OK |
| single thick cell ($τ_{\mathrm{cell}}$ = 122) → ε→1/τ limit | 52261.3 vs 52261.3 — OK |
| $T^{-3}$ scaling, τ(1000)/τ(2000) | 8.049 vs 8.0 — OK \* |
| thick deep cell must not bind against a thin top cell | 430.33 (= the top cell) — OK |
| collective hard-fails when required and uninitialised | raises |

\* 8.049 rather than exactly 8 is physical, not an error: at fixed pressure ρ ∝ 1/T, so $τ_{\mathrm{cell}}$ and hence ε shift slightly with temperature. The pure $T^{-3}$ law is exact only at fixed ρ.

## 7. Limits of validity

- **`c_v = P/(ρT)/(γ−1)` is exact only at `NVAPOR = 0`.** `P/(ρT)` gives the MIXTURE $R_{eff}$ but `γ` is the dry value. Correct for both decks today; on a moist deck take the mixture $c_{v}$ from thermo.
- **The linearisation keeps only the local emission derivative.** It ignores the response of the radiation field itself, which *reduces* λ. The bound is therefore conservative in the optically thin limit — the safe direction.
- **ε is a standard but approximate closure.** An exact λ would come from differentiating the Toon or DISORT solution; that is possible and much more work.
- **It assumes grey thermal emission dominates the stiffness.** Scattering, CIA or a strong band feature would not be seen. Shortwave beam heating is correctly omitted — it has no local-T feedback and so contributes nothing to λ.
- **Band truncation.** If the longwave band does not span the Planck function, the cell emits only the in-band fraction and the true λ is smaller by that factor. On the 2024 card the IR band \[100, 10000\] cm$^{-1}$ captures 75.4 % of σT⁴ at 2880 K, so the current form overestimates λ by ~1.3× there — again conservative, but worth carrying explicitly if this is ever tightened.
- **It is predictive, not reactive.** A reactive backstop — measure $r = |Δe_{rad}|/e_{int}$ after the step and cut Δt if `r` exceeds ~0.25 — catches whatever the linearisation missed, but is one step late by construction. It belongs *under* this bound, not instead of it, and it needs its own MAX-all-reduce and a place in the restart file, since it makes Δt path-dependent.

**The destination.** The genuinely correct answer is to make the radiative source **implicit in T**, at which point no timestep bound is needed at all. λ as derived above *is* the Jacobian such a solve requires, and snapy already runs an implicit vertical solve. This limiter is the right explicit bound; it is not a substitute for that.
