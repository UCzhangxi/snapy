> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Moist O(Δx₁²) gaps of the x2/x3 face fluxes, and the discrete form for `_flux_covariance`

This document gives the generic derivation for a finite-volume code on a hydrostatic (or any vertically varying)
background. It extends the dry #289 term to a multi-species EOS with energy offsets. Symbolic checks are in
`u3_symbolic.py` (same directory); their log is `u3_symbolic.log`. Every check quoted below prints 0 there.

## 1. Setting

In an x2 (or x3) face, the finite-volume update needs the average over the cell's x1 extent of the point flux.
To linear order about a state at rest, the point fluxes are:

- mass: $\rho u$;
- tracers: $\rho u\,y_n$;
- energy: $\rho u\,h$;
- momentum: $\rho u^2 + p$.

The specific state is $\psi = (\hat e, y_1,\dots,y_N)$, with $\hat e$ the internal energy per mass. Two EOS facts
are all the derivation uses:

1. $p = \rho\,\Pi(\psi)$, so $h = \hat e + \Pi(\psi)$ depends on $\psi$ only. This holds for any ideal-gas
   mixture, with or without zero-volume condensates and per-species energy offsets.
2. The code's cell primitives are density-weighted means: $\{f\} = \langle\rho f\rangle/\langle\rho\rangle$ for
   $f = \hat e, y_n, u$. That is because the conserved variables are $\rho$, $\rho y_n$, $\rho u$ and $E$.
   The EOS is then evaluated on these means.

Under the density weight, with $\Delta = \Delta x_1$, $\{\zeta^2\} - \{\zeta\}^2 = \Delta^2/12 + O(\Delta^4)$.

## 2. The gaps (exact to $O(\Delta^2)$)

Define

$$
J \equiv \frac{\Delta^2}{24}\,\psi_{x_1}^{\sf T}\,\frac{\partial^2\Pi}{\partial\psi^2}\,\psi_{x_1}
$$

(the Jensen term from evaluating a nonlinear $\Pi$ at mean states). Then

| flux | exact face average minus what the solver gets | check |
|---|---|---|
| energy | $\frac{\Delta^2}{12}\rho\,\partial_1 u_n\,\partial_1 h + \rho u_n J$ | (L): residual 0 |
| tracer $n$ | $\frac{\Delta^2}{12}\rho\,\partial_1 u_n\,\partial_1 y_n$ | (L), special case |
| mass | 0 | — |
| momentum | $\rho J$ (the cell pressure is low by $\rho J$) | (A): residual 0 |

Notes on the table:

- In the energy row, $h$ is the solver's own enthalpy: $h = (\text{W→I} + p)/\rho$, without kinetic energy. That is
  what LMARS multiplies by $\rho u$.
- $J = 0$ when $\Pi$ is linear in $\psi$ along the background gradient. That holds for uniform composition with a
  T-independent $c_v$. Only then is the dry #289 term the whole gap.

## 3. What the enthalpy gradient contains

Write $\kappa = c_{v,\rm mix}/R_{\rm mix} = 1/(\gamma_i-1)$ and $\ell = \sum_n y_n u_{0,n}$. The sum runs over all
species, dry included: these are the energy offsets that W→I adds (`ideal_moist.cpp:220-223`). Then

$$
\rho\,\partial_1 h = \frac{\gamma_i}{\gamma_i-1}\,p\,\partial_1\ln\frac{p}{\rho} + p\,\partial_1\kappa + \rho\,\partial_1\ell
\qquad\text{(check (B): residual 0)}.
$$

At uniform composition with no offsets, this reduces exactly to the dry #289 form (checks (a2) and (a3)).

## 4. What the prefactor in e7f9904 computes

The x2/x3 energy correction of commit e7f9904 is
$\sigma^2\,(I+p)\,\partial_1\ln(p/\rho)\,\partial_1 u_n$, with $I+p = \rho h$. Check (F) gives

$$
(I+p)\,\partial_1\ln\frac{p}{\rho} - \rho\,\partial_1 h = \rho\,\ell\,\partial_1\ln\frac{p}{\rho} - p\,\partial_1\kappa - \rho\,\partial_1\ell .
$$

So that prefactor equals the exact $\rho\,\partial_1 h$ only when every energy offset is zero and the composition is
uniform. Two consequences:

- With a nonzero offset, $\rho\ell\,\partial_1\ln T$ is added even in a dry, uniform column. It is wrong by the
  factor $1 + \ell/((\kappa+1)\Pi)$.
- Where $y$ varies, the prefactor misses $p\,\partial_1\kappa + \rho\,\partial_1\ell$.

## 5. Recommended discrete form

Keep the e7f9904 structure: cell-centred differences over the two neighbours, $\sigma^2$ = `face_moment2_x1()`,
the centroid-shift term unchanged. Then change it as follows.

```
h      = (peos->compute("W->I", {wbar}) + p) / wbar[IDN]        # the solver's h, no KE
dh     = (h[2:] - h[:-2]) / dx1
dF_E   = wbar[IDN] * s2 * dh * dun            # replaces enth * s2 * dlnt * dun
dF_y_n = wbar[IDN] * s2 * (y_n[2:] - y_n[:-2]) / dx1 * dun   # every tracer slot (mass fraction y_n)
```

Why these choices:

- Differencing $h$ itself makes the term exact for any EOS of the form $p = \rho\Pi(\psi)$. It is invariant to the
  arbitrary energy offsets only when the tracer rows are included. Shifting $u_{0,n}$ changes $\partial_1 h$ by
  $\sum_n \Delta u_{0,n}\partial_1 y_n$, and the tracer rows carry exactly the compensating change into the
  buoyancy.
- An energy-only correction is complete only where the composition is uniform.
- The Jensen parts ($\rho u J$ on energy, $\rho J$ on momentum) need second differences of the full state and the
  EOS Hessian. Their size relative to the covariance term has not been measured on a snapy column.

## 6. EOS with a temperature-dependent $c_v$ (`moist_mixture`)

There, $\hat e(T)$ is nonlinear, so $\Pi(\hat e)$ is nonlinear even at uniform composition: $\Pi_{\hat e\hat e} =
-R\,c_v'(T)/c_v^3$. This gives

$$
J = -\frac{\Delta^2}{24}\,R\,\frac{c_v'(T)}{c_v}\,(\partial_1 T)^2 \ne 0 \quad\text{at } y = \text{const},
$$

so the dry limit of #289 is not exact for that EOS. The size is estimated, not run. On a near-adiabat,
$\partial_1 T = -g/c_p$, and with $\mathrm{d}\ln c_v/\mathrm{d}\ln T \sim 0.5$ the stratification equivalent is
$|\varepsilon_J| \sim (R/c_p)^3\,\Delta^2/(96 H_p^2)$. That is $\sim10^{-3}(\Delta/H_p)^2$, far below the
covariance term's $\sim0.03(\Delta/H_p)^2$.

The $\partial_1 h$ form of §5 stays exact for the covariance part. The W→I call already carries $c_v(T)$, which is
another reason to difference $h$ rather than $\ln(p/\rho)$.

Unverified: the actual $c_v(T)$ is set by the thermodynamics library's `eval_cv_R`, which was not read.
