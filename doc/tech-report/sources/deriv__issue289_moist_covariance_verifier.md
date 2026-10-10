> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

Source: snapy afe9f6b:docs/derivations/issue289_moist_covariance_verifier.md
# #289: the transverse-face covariance gaps for a general (moist) EOS — independent check

Independent check. I derived everything below before reading a separately posted proposal and
compared only at the end (§6). Machine checks:
- `moist_cov_sympy.py`: symbolic, exact for the O(Δx₁²) term;
- `moist_cov_quadrature.py`: direct 50-digit face quadrature with a concrete moist EOS;
- `j_bound.py`: a size estimate for the J pieces.

Their outputs are `sympy_out.txt` and `quad_out.txt`; all of these files sit next to this one.

## 1. Setup

An x2 (or x3) face spans one x1 cell, $\zeta\in[-\Delta x_1/2,\Delta x_1/2]$. The scheme evaluates the face flux
from the x1-averaged conserved state, $F(\bar U)$. The finite-volume flux is the face average $\langle F(U)\rangle$.
The reconstruction in x2 is assumed to deliver $\bar U$ at the face; the x2 error is a separate matter.

Conserved state:
$$U=(\rho,\ m_n,\ m_t,\ E,\ Y_k),\quad m=\rho u,\quad Y_k=\rho y_k,\quad
E=\rho\,(e+\ell(y))+\tfrac12\rho|v|^2,\quad \ell=\textstyle\sum_k y_k u_{0k},$$

- $e$ is the specific thermal energy, the one the EOS sees: $p=\rho\,\Pi(e,y)$.
- $\ell$ is the offset that W→I adds (§5).

The scheme recovers $y=Y/\rho$ and $e=E/\rho-|m|^2/(2\rho^2)-\ell(Y/\rho)$ from $\bar U$. A constant dry offset is
included by writing $\ell=u_{0d}+\sum_n y_n(u_{0n}-u_{0d})$; a constant part of $\ell$ drops out of every
derivative below.

x2 fluxes ($u_n$ is the face-normal velocity, $u_t$ a transverse one; x3 faces are the same with roles swapped):
- mass: $m_n$
- normal momentum: $m_n^2/\rho+p$
- transverse momentum: $m_nm_t/\rho$
- energy: $(E+p)\,m_n/\rho$
- tracer: $Y_km_n/\rho$

## 2. The O(Δx₁²) gap

Expand $U(\zeta)=U_0+U_1\zeta+\tfrac12U_{11}\zeta^2+\dots$. Then $\bar U=U_0+\tfrac{\Delta x_1^2}{24}U_{11}+O(\Delta x_1^4)$, and
$\langle (U-\bar U)_a(U-\bar U)_b\rangle=s_2\,U_{1a}U_{1b}+O(\Delta x_1^4)$ with

$$s_2=\langle\zeta^2\rangle=\Delta x_1^2/12 .$$

Expanding $F$ about $\bar U$ (not $U_0$), the linear term averages to zero exactly, and the third moments vanish by
parity at this order. So

$$\boxed{\ \langle F(U)\rangle-F(\bar U)=\tfrac{s_2}{2}\,U_1^{\mathsf T}F_{UU}\,U_1+O(\Delta x_1^4)\ } $$

with $F_{UU}$ taken at the point. The scripts evaluate exactly this quadratic form. They replace $\Pi$ by its
second-order Taylor polynomial about $\psi_0=(e,y)$ (exact for second derivatives), set $U(s)=U_0+sU_1$, and
take $\tfrac{s_2}{2}\,d^2F/ds^2|_0$.

## 3. Results (exact at O(Δx₁²), all velocity orders)

Notation: subscript 1 means $\partial_{x_1}$, $\psi=(e,y_1,\dots)$, $h=e+\ell+\Pi=(\text{W→I}+p)/\rho$ (no KE), and

$$J=\tfrac{s_2}{2}\,\psi_1^{\mathsf T}\,\Pi_{\psi\psi}\,\psi_1 .$$

| flux | gap $\langle F\rangle-F(\bar U)$ |
|---|---|
| mass | $0$ |
| tracer $k$ | $s_2\,\rho\,u_{n,1}\,y_{k,1}$ |
| transverse momentum | $s_2\,\rho\,u_{n,1}\,u_{t,1}$ |
| normal momentum | $s_2\,\rho\,u_{n,1}^2+\delta p$ |
| energy | $s_2\,\rho\,u_{n,1}\,(h+\tfrac12|v|^2)_{,1}+u_n\,\delta p$ |
| pressure the scheme rebuilds, $\delta p$ | $\rho J-\tfrac{s_2}{2}\,\rho\,\Pi_e\,|v_1|^2$ |

Derivation of the structure, which the sympy run confirms term by term:
- A ratio $q=Q/\rho$ has quadratic form $-2\rho_1 q_1/\rho$, so a flux $Q\,m/\rho$ gives $s_2\,\rho\,u_1 q_1$.
  The $u\rho_1$ and $q\rho_1$ cross terms cancel identically, as in the dry case.
- $p=\rho\,\Pi(\psi(U))$ is homogeneous of degree 1 in $U$. Its quadratic form is
  $\rho\,\psi_1^{\mathsf T}\Pi_{\psi\psi}\psi_1+2\rho_1\Pi_\psi\psi_1+\rho\,\Pi_\psi\cdot\psi_{UU}[U_1,U_1]$.
  The last term is $-2\rho_1\Pi_\psi\psi_1$ plus the kinetic-energy part $-\rho\,\Pi_e|v_1|^2$, so it cancels
  the middle term and leaves $\delta p$.
- The energy flux $(E+p)\,u_n$ splits as $s_2\rho\,u_{n,1}H_1+u_n\,\delta p$, with $H=(E+p)/\rho$.

**Linearised about a resting state** (velocity a perturbation, background gradients $O(1)$), every term
quadratic in velocity drops:

- mass: $0$
- tracer $k$: $s_2\,\rho\,u_{n,1}\,y_{k,1}$
- normal momentum: $\rho J$
- transverse momentum: $0$
- energy: $s_2\,\rho\,u_{n,1}\,h_{,1}+\rho\,u_n\,J$

**Notes.**
- $J$ involves only the Hessian of $\Pi$ along $\psi_1$. It vanishes when $\Pi$ is linear along the gradient,
  e.g. a single ideal gas, where $\Pi=e/\kappa$ with constant $\kappa$.
- $J$ is invariant under any linear change of variables in $\psi$. It is therefore the same whether $e$ is taken
  with or without the (linear-in-$y$) offset.
- For an ideal moist gas, $\Pi_{ee}=0$, so $J=\tfrac{s_2}{2}(2\Pi_{ey}e_1y_1+\Pi_{yy}y_1^2)$.

**Numerical confirmation** (`quad_out.txt`): non-zero velocities, two tracers with composition gradients, and
latent-size offsets. Halving $\Delta x_1$ from 0.04 to 0.01, (measured − predicted)/|measured| falls 4.0× per
halving for every flux (normal momentum 3.99×). So the residual is $O(\Delta x_1^4)$ and the table above is the
complete $O(\Delta x_1^2)$ gap.

## 4. The e7f9904 prefactor

At e7f9904 (`e7f99040834c5be3e97ee9e952d28453dfd0b7d4`), `src/hydro/hydro_forward.cpp`:
```
60:  auto lnt = (p / wbar[IDN]).log();
61:  auto enth = peos->compute("W->I", {wbar}) + p;
101:      enth.narrow(-1, 1, n1 - 2) * s2.narrow(-1, 1, n1 - 2) * dlnt * dun -
102:      ds.narrow(-1, 1, n1 - 2) * dhflx;
```
So the energy covariance term is $(I+p)\,s_2\,\partial_1\ln(p/\rho)\,\partial_1u_n$ (plus the curved-grid centroid term,
not at issue here). `src/eos/ideal_moist.cpp`:
```
219:  // add the internal energy offset
220:  auto yd = 1. - yfrac.sum(0);
221:  ie += prim[IDN] * yd * u0[0];
222:  ie +=
223:      prim[IDN] * yfrac.unfold(0, ny, 1).matmul(u0.narrow(0, 1, ny)).squeeze(0);
```
So W→I $=\rho(e+\ell)$ with $\ell=y_du_{0d}+\sum_n y_nu_{0n}$, and $I+p=\rho h$.

For the ideal moist EOS, $\Pi=e/\kappa(y)$ with $\kappa=1/(\gamma_i-1)$ (`ideal_moist.cpp:202,217`), so
$h=(\kappa+1)\Pi+\ell$. Then

$$(I+p)\,\partial_1\ln\Pi-\rho\,\partial_1h=\rho\,\ell\,\partial_1\ln(p/\rho)-p\,\partial_1\kappa-\rho\,\partial_1\ell .$$

Sympy confirms this identically. In a dry, uniform column ($\kappa_1=\ell_1=0$, $\ell\ne0$):
$$\frac{(I+p)\,\partial_1\ln\Pi}{\rho\,\partial_1h}=1+\frac{\ell}{(\kappa+1)\,p/\rho},$$
which sympy confirms. With a non-zero dry offset $u_{0d}$, $\ell\neq0$ even in a single-species column, so the
e7f9904 coefficient is off by that factor there.

## 5. Offset invariance, and the dry limit

Shifting the offsets $u_{0k}\to u_{0k}+c_k$ redefines $E\to E+\rho\,c\cdot y$. The exact system maps to itself if
the energy equation gains $c\,\cdot$ (tracer equations). For the corrections:

- **h-differenced energy row** $s_2\rho\,u_{n,1}h_1$: it shifts by $s_2\rho\,u_{n,1}\,c\cdot y_1$, which is exactly
  $c\,\cdot$ (tracer rows $s_2\rho\,u_{n,1}y_{k,1}$). Invariant **only if** the tracer rows carry their
  correction. Without them, the shift of the energy row has no counterpart. A constant shift of $\ell$ changes
  nothing, since $h_1$ is unchanged.
- **e7f9904 row** $\rho h\,\partial_1\ln\Pi\,\partial_1u_n$: it shifts by
  $s_2\rho\,u_{n,1}(c\cdot y)\,\partial_1\ln\Pi$, which is **not** $c\,\cdot$ (tracer rows) even with tracer rows
  added. It is not offset-invariant, and a constant offset already changes it.
- **Dry, uniform, zero-offset limit** ($\ell=0$, $\kappa$ constant): $\rho h_1=\rho(\kappa+1)\Pi_1=(I+p)\,\partial_1\ln\Pi$
  exactly, so the h-differenced row reduces to e7f9904's term. Sympy gives 0.

## 6. Comparison with the posted proposal, made after §§1–5

| claim | verdict | note |
|---|---|---|
| (a) energy $s_2\rho\,\partial_1u_n\partial_1h+\rho u_nJ$, $h=(\text{W→I}+p)/\rho$ without KE | **agree** at linear order about rest | the exact form adds $s_2\rho\,u_{n,1}\,(\tfrac12|v|^2)_{,1}-\tfrac{s_2}{2}\rho\,u_n\Pi_e|v_1|^2$, quadratic in velocity |
| (b) tracer $s_2\rho\,\partial_1u_n\partial_1y_n$ | **agree** exactly | |
| (c) momentum $\rho J$ | **agree** for the normal momentum at linear order | exact: $s_2\rho u_{n,1}^2+\rho J-\tfrac{s_2}{2}\rho\Pi_e|v_1|^2$; transverse momentum $s_2\rho u_{n,1}u_{t,1}$, zero at linear order |
| (d) mass 0 | **agree** exactly | |
| (e) $J=\tfrac{s_2}{2}\psi_1^{\mathsf T}\Pi_{\psi\psi}\psi_1$, $\psi=(e,y)$, zero unless $\Pi$ is nonlinear along the gradient | **agree** | invariant under linear changes of $\psi$, so offset convention does not matter |
| prefactor error $\rho\ell\,\partial_1\ln(p/\rho)-p\,\partial_1\kappa-\rho\,\partial_1\ell$ | **agree** (sign: e7f9904 minus exact) | |
| dry uniform factor $1+\ell/((\kappa+1)p/\rho)$ | **agree** | |
| h-differencing offset-invariant only with the tracer rows | **agree** | and e7f9904's form is not invariant with or without them |
| dry, uniform, zero-offset limit equals e7f9904's term | **agree** | |

**Size of J (optional; a rough estimate, not the proposal's metric).** `j_bound.py` assumes an H2-He atmosphere with 5%
water vapour falling to 0 over 10 km, T = 300 K, a 2 K/km lapse rate and a 50 km column mode. Under those
assumptions, $|\rho u J|/|s_2\rho u_1h_1|$ is 0.9e-3 with a 2.5e6 J/kg offset gradient, and 2.2e-3 without one.
The proposal's "6e-8 vs 1e-5" is a ratio of 6e-3. These are the same order and both say the J pieces are small next to the
covariance term. The metrics differ, so this is consistency, not confirmation.

**Hypotheses, not shown here:**
- Dropping the velocity-quadratic terms is harmless for turbulent (non-linear) flow. That is item 5's question.
- The discrete $D_1[h]$ form inherits the exactness above. I have derived the continuous gap only, not checked
  any implementation.

## 7. Known and excluded: quadratic velocity terms

By a scoping decision, the velocity-squared parts of the exact gaps in §3 are **not** part of
#289. They are listed here exactly as derived, so they are on record:

| flux | excluded term (added to the linear form) |
|---|---|
| normal momentum | $+\,s_2\,\rho\,u_{n,1}^2-\tfrac{s_2}{2}\,\rho\,\Pi_e\,|v_1|^2$ |
| transverse momentum | $s_2\,\rho\,u_{n,1}\,u_{t,1}$ |
| energy | $+\,s_2\,\rho\,u_{n,1}\,(\tfrac12|v|^2)_{,1}-\tfrac{s_2}{2}\,\rho\,u_n\,\Pi_e\,|v_1|^2$ |

**Reason.** #289 removes a bias that is linear in the perturbation about a stratified background;
that bias is what shifts convective onset. The terms above are the scheme's ordinary second-order truncation error
in nonlinear flow. They are present in every direction, not only on transverse faces, and they vanish in the linear
problem about a resting state. So they are excluded from the #289 correction.

**J also stays out of the implementation, pending confirmation.** The bounds:
- my rough estimate in §6 puts the J piece at about $10^{-3}$ of the covariance piece in the energy row;
- the proposal's metric gives 6e-8 against 1e-5, a ratio of about $6\times10^{-3}$.


## Verification script `docs/derivations/j_bound.py` (at `afe9f6b`)

```python
"""Rough size of the J pieces vs the covariance piece in the x2 energy row, ideal-moist two-component gas.
Pi(e, y) = e * r(y), r = R(y)/cv(y) mass-weighted (H2-He dry: R 3600, cv 9000; H2O vapour: R 461.5, cv 1418),
so Pi_ee = 0 and J = (s2/2) [2 r'(y) e_1 y_1 + e r''(y) y_1^2]. For a mode with u_n1 = m u_n the ratio of
rho u_n J to s2 rho u_n1 h_1 is |(1/2)(2 r' e_1 y_1 + e r'' y_1^2)| / (m |h_1|), h = e + ell + Pi, ell = (u0v - u0d) y.
Assumed (not from the deck): T = 300 K, lapse 2 K/km, vapour y = 0.05 falling to 0 over 10 km
(y_1 = -5e-6 /m), column 50 km so m = pi/50 km, u0v - u0d = 2.5e6 J/kg (latent-heat-like offset) or 0.
Run: python -I j_bound.py"""
import math
Rd, Rv, cvd, cvv = 3600., 461.5, 9000., 1418.
y, T, dT = 0.05, 300., -2e-3
R = lambda y: Rd * (1 - y) + Rv * y
cv = lambda y: cvd * (1 - y) + cvv * y
r = lambda y: R(y) / cv(y)
hh = 1e-6
r1 = (r(y + hh) - r(y - hh)) / (2 * hh)
r2 = (r(y + hh) - 2 * r(y) + r(y - hh)) / hh**2
e = cv(y) * T
y1 = -0.05 / 10e3
e1 = cv(y) * dT + (cvv - cvd) * y1 * T
m = math.pi / 50e3
J_over_s2 = 0.5 * (2 * r1 * e1 * y1 + e * r2 * y1**2)
for dl in (2.5e6, 0.0):
    h1 = e1 * (1 + r(y)) + e * r1 * y1 + dl * y1
    print(f'offset gradient {dl:.1e}: J/s2 = {J_over_s2:.3e}  h_1 = {h1:.3e}  ratio rho u J / (s2 rho u_1 h_1) = {abs(J_over_s2) / (m * abs(h1)):.3e}')
```


## Verification script `docs/derivations/moist_cov_quadrature.py` (at `afe9f6b`)

```python
"""Numerical check of the symbolic gaps (moist_cov_sympy.py) by direct face quadrature.

Concrete ideal-moist EOS with two tracers (mass-weighted R and cv, so Pi = e R(y)/cv(y) is nonlinear in y):
    R(y) = Rd (1 - y1 - y2) + R1 y1 + R2 y2,  cv(y) likewise,  Pi = e R/cv,  ell = u01 y1 + u02 y2.
Smooth primitive profiles in x1 with non-zero velocities. For each dx1 = h, the exact face average <F(U)> is
computed by 40-point Gauss-Legendre in 50-digit arithmetic, F(Ubar) from the averaged conserved state (as the
scheme does), and compared with the predicted full gap (s2 = h^2/12):
    mass 0; tracer s2 rho u_n1 y_k1; transverse momentum s2 rho u_n1 u_t1;
    normal momentum s2 rho u_n1^2 + p_gap; energy s2 rho u_n1 (h_s + |v|^2/2)_1 + u_n p_gap,
    p_gap = rho J - (s2/2) rho Pi_e |v_1|^2,  J = (s2/2) psi_1^T Pi_psipsi psi_1, psi = (e, y1, y2),
with h_s = e + ell + Pi. The absolute residual must fall as h^4, i.e. the residual relative to the O(h^2)
gap must fall 4x per halving of h.
Run: python -I moist_cov_quadrature.py
"""
import mpmath as mp

mp.mp.dps = 50
Rd, R1, R2 = mp.mpf(3600), mp.mpf(461.5), mp.mpf(188.9)
cvd, cv1, cv2 = mp.mpf(9000), mp.mpf(1418), mp.mpf(1500)
u01, u02 = mp.mpf('2.5e6'), mp.mpf('-1.0e6')


def Pi(e, a, b):
    return e * (Rd * (1 - a - b) + R1 * a + R2 * b) / (cvd * (1 - a - b) + cv1 * a + cv2 * b)


# smooth primitive profiles around z0
z0 = mp.mpf('0.3')
prof = {
    'rho': lambda z: 1.2 * mp.exp(-0.7 * z),
    'un': lambda z: 3 + 2 * mp.sin(2 * z),
    'ut': lambda z: -1 + mp.cos(3 * z),
    'e': lambda z: 9000 * 300 * (1 - 0.3 * z) + 4000 * mp.sin(z),
    'y1': lambda z: 0.04 * mp.exp(-3 * z),
    'y2': lambda z: 0.01 + 0.02 * z ** 2,
}


def U_of(z):
    r, un, ut, e, a, b = (prof[k](z) for k in ('rho', 'un', 'ut', 'e', 'y1', 'y2'))
    ell = u01 * a + u02 * b
    return [r, r * un, r * ut, r * (e + ell) + r * (un ** 2 + ut ** 2) / 2, r * a, r * b]


def fluxes(U):
    r, mn, mt, En, Ya, Yb = U
    a, b = Ya / r, Yb / r
    e = En / r - (mn ** 2 + mt ** 2) / (2 * r ** 2) - (u01 * a + u02 * b)
    p = r * Pi(e, a, b)
    return {'mass': mn, 'mom_normal': mn ** 2 / r + p, 'mom_transverse': mn * mt / r,
            'energy': (En + p) * mn / r, 'tracer1': Ya * mn / r, 'tracer2': Yb * mn / r}


def predicted(h):
    s2 = h ** 2 / 12
    d = lambda k: mp.diff(prof[k], z0)
    v = {k: prof[k](z0) for k in prof}
    r = v['rho']
    psi = [v['e'], v['y1'], v['y2']]
    psi1 = [d('e'), d('y1'), d('y2')]
    f = lambda e, a, b: Pi(e, a, b)
    H = [[mp.diff(f, psi, tuple(1 if k in (i, j) and i != j else (2 if k == i == j else 0) for k in range(3)))
          for j in range(3)] for i in range(3)]
    J = s2 / 2 * sum(psi1[i] * H[i][j] * psi1[j] for i in range(3) for j in range(3))
    Pi_e = mp.diff(f, psi, (1, 0, 0))
    v1sq = d('un') ** 2 + d('ut') ** 2
    p_gap = r * J - s2 / 2 * r * Pi_e * v1sq
    hs = lambda z: prof['e'](z) + u01 * prof['y1'](z) + u02 * prof['y2'](z) + Pi(prof['e'](z), prof['y1'](z), prof['y2'](z))
    H1 = mp.diff(hs, z0) + v['un'] * d('un') + v['ut'] * d('ut')
    return {'mass': 0, 'tracer1': s2 * r * d('un') * d('y1'), 'tracer2': s2 * r * d('un') * d('y2'),
            'mom_transverse': s2 * r * d('un') * d('ut'), 'mom_normal': s2 * r * d('un') ** 2 + p_gap,
            'energy': s2 * r * d('un') * H1 + v['un'] * p_gap}


def measured(h):
    nodes = mp.gauss_quadrature(40, 'legendre') if hasattr(mp, 'gauss_quadrature') else None
    avg = lambda g: mp.quad(g, [z0 - h / 2, z0 + h / 2]) / h
    Ubar = [avg(lambda z, i=i: U_of(z)[i]) for i in range(6)]
    Fbar = fluxes(Ubar)
    out = {}
    for k in Fbar:
        Fav = avg(lambda z, k=k: fluxes(U_of(z))[k])
        out[k] = Fav - Fbar[k]
    return out


prev = None
print('h, then per flux: measured gap, (measured - predicted)/|measured|')
for h in (mp.mpf('0.04'), mp.mpf('0.02'), mp.mpf('0.01')):
    m, p = measured(h), predicted(h)
    row = {k: (m[k], (m[k] - p[k]) / (abs(m[k]) if m[k] != 0 else 1)) for k in m}
    print('h =', mp.nstr(h, 3))
    for k, (g, rel) in row.items():
        ratio = '' if prev is None or prev[k][1] == 0 or rel == 0 else f'  shrink x{mp.nstr(prev[k][1] / rel, 4)}'
        print(f'  {k:15s} gap {mp.nstr(g, 6):>14s}  rel.resid {mp.nstr(rel, 3):>10s}{ratio}')
    prev = row
```


## Verification script `docs/derivations/moist_cov_sympy.py` (at `afe9f6b`)

```python
"""Independent symbolic check of the O(dx1^2) face-average gaps of the x2 (transverse) fluxes for a
general EOS p = rho * Pi(e, y1, y2) with species energy offsets (W->I adds sum_n y_n u0_n).

Face of an x2 face spans one x1 cell, zeta in [-dx1/2, dx1/2]. The scheme evaluates F(Ubar), Ubar the x1
average of the conserved state U; the exact flux is <F(U)>. With <zeta^2> = dx1^2/12 =: s2 and the first-order
term vanishing exactly when expanding about Ubar,
    gap = <F(U)> - F(Ubar) = (s2/2) * U_1^T F_UU U_1 + O(dx1^4),
where U_1 = dU/dx1. Conserved U = (rho, m_n, m_t, E, Y1, Y2) with m = rho u, Y_k = rho y_k,
E = rho (e + ell(y)) + rho |v|^2 / 2, ell = u01 y1 + u02 y2 (the W->I offset), and the scheme recovers
e = E/rho - |m|^2/(2 rho^2) - ell(Y/rho), y = Y/rho. Fluxes along x2 (normal velocity u_n):
mass m_n; normal momentum m_n^2/rho + p; transverse momentum m_n m_t/rho; energy (E + p) m_n/rho;
tracer Y_k m_n/rho.
Everything is evaluated pointwise: P = primitive values, dP = their x1 derivatives (plain symbols).
Run: python -I moist_cov_sympy.py   (prints each gap, the comparison with the claims, and PASS/FAIL lines)
"""
import sympy as sp

rho, un, ut, e, y1, y2 = sp.symbols('rho u_n u_t e y1 y2', real=True)
drho, dun, dut, de, dy1, dy2 = sp.symbols('rho_1 u_n1 u_t1 e_1 y1_1 y2_1', real=True)
u01, u02, s2 = sp.symbols('u01 u02 s2', real=True)
R, Mn, Mt, E, Y1, Y2 = sp.symbols('R M_n M_t E Y1 Y2', real=True)
Pi = sp.Function('Pi')
P = [rho, un, ut, e, y1, y2]
dP = [drho, dun, dut, de, dy1, dy2]
Usym = [R, Mn, Mt, E, Y1, Y2]

ell = lambda a, b: u01 * a + u02 * b
# conserved state as a function of primitives
Uofp = {R: rho, Mn: rho * un, Mt: rho * ut, E: rho * (e + ell(y1, y2)) + rho * (un**2 + ut**2) / 2,
        Y1: rho * y1, Y2: rho * y2}
U1 = [sum(sp.diff(Uofp[u], p) * d for p, d in zip(P, dP)) for u in Usym]   # dU/dx1

# Pi derivatives at the point (e, y1, y2), as plain symbols: Pi, Pi_e, Pi_1, Pi_2, Pi_ee, Pi_e1, ...
names = {}
def Pd(*idx):
    key = tuple(sorted(idx))
    if key not in names:
        names[key] = sp.Symbol('Pi_' + ''.join('e12'[i] for i in key) if key else 'Pi')
    return names[key]

# The gap needs only second derivatives at the point, so Pi may be replaced EXACTLY (for this purpose) by its
# second-order Taylor polynomial about psi0 = (e, y1, y2); no undefined-function chain rule is involved.
psi0 = [e, y1, y2]
def Pi_T(psi):
    d = [psi[i] - psi0[i] for i in range(3)]
    return (Pd() + sum(Pd(i) * d[i] for i in range(3))
            + sp.Rational(1, 2) * sum(Pd(i, j) * d[i] * d[j] for i in range(3) for j in range(3)))

s = sp.Symbol('s')
Us = {u: Uofp[u] + s * du for u, du in zip(Usym, U1)}   # U(x1) along the face: U0 + s U_1

def scheme_p(U):
    """pressure the scheme rebuilds from a conserved state U (dict of expressions)"""
    r, mn, mt, En, Ya, Yb = (U[k] for k in Usym)
    eps_ = En / r - (mn**2 + mt**2) / (2 * r**2) - ell(Ya / r, Yb / r)
    return r * Pi_T([eps_, Ya / r, Yb / r])

def flux(name, U):
    r, mn, mt, En, Ya, Yb = (U[k] for k in Usym)
    p = scheme_p(U)
    return {'mass': mn, 'mom_normal': mn**2 / r + p, 'mom_transverse': mn * mt / r,
            'energy': (En + p) * mn / r, 'tracer1': Ya * mn / r, 'tracer2': Yb * mn / r}[name]

fluxes = ['mass', 'mom_normal', 'mom_transverse', 'energy', 'tracer1', 'tracer2']

def gap(name):
    F = flux(name, Us)
    d2 = sp.diff(F, s, 2).subs(s, 0)
    return sp.expand(sp.simplify(s2 / 2 * d2))

# the claims (the posted proposal), written in this script's symbols
psi1 = [de, dy1, dy2]
Hpsi = [[Pd(0, 0), Pd(0, 1), Pd(0, 2)], [Pd(0, 1), Pd(1, 1), Pd(1, 2)], [Pd(0, 2), Pd(1, 2), Pd(2, 2)]]
J = s2 / 2 * sum(psi1[i] * Hpsi[i][j] * psi1[j] for i in range(3) for j in range(3))
h = e + ell(y1, y2) + Pd()            # h = (W->I + p)/rho = e + ell + Pi  (no kinetic energy)
dh = de + u01 * dy1 + u02 * dy2 + Pd(0) * de + Pd(1) * dy1 + Pd(2) * dy2
claims = {
    'mass': 0,
    'mom_normal': rho * J,
    'mom_transverse': 0,
    'energy': s2 * rho * dun * dh + rho * un * J,
    'tracer1': s2 * rho * dun * dy1,
    'tracer2': s2 * rho * dun * dy2,
}

eps_ = sp.Symbol('epsilon')   # velocity amplitude, for the linearisation about rest


def linear_part(expr):
    """terms of order <= 1 in the velocity (u_n, u_t and their derivatives scaled by eps_)"""
    sub = {un: eps_ * un, ut: eps_ * ut, dun: eps_ * dun, dut: eps_ * dut}
    ex = sp.expand(expr.subs(sub, simultaneous=True))
    return sp.expand(ex.coeff(eps_, 0) + ex.coeff(eps_, 1))


results = {}
for k in fluxes:
    g = gap(k)
    res_full = sp.simplify(g - claims[k])
    res_lin = sp.simplify(linear_part(g) - linear_part(sp.expand(claims[k])))
    results[k] = (g, res_full, res_lin)
    print(f'=== {k}')
    print('  gap            =', sp.factor_terms(g))
    print('  gap - claim    =', sp.factor_terms(res_full))
    print('  linear in |v|: gap - claim =', res_lin, '->', 'PASS' if res_lin == 0 else 'FAIL')

# exact energy gap in a compact form: s2 rho u_n1 H_1 + u_n * (p gap), H = h + |v|^2/2
H1 = dh + un * dun + ut * dut
p_gap = results['mom_normal'][0] - s2 * rho * dun**2
chk = sp.simplify(results['energy'][0] - (s2 * rho * dun * H1 + un * p_gap))
print('=== energy exact identity: gap = s2 rho u_n1 (h + |v|^2/2)_1 + u_n * [p gap]  ->', 'PASS' if chk == 0 else f'FAIL {chk}')
chk = sp.simplify(results['mom_normal'][0] - (s2 * rho * dun**2 + p_gap))
print('=== p gap (full, incl. kinetic part of e) =', sp.factor_terms(sp.expand(p_gap)))
print('    p gap - rho J =', sp.factor_terms(sp.simplify(p_gap - rho * J)))

# ---- prefactor claim for the e7f9904 form (I+p) d1 ln(p/rho) d1 u_n, ideal moist Pi = e / kappa(y) ----
kap = sp.Function('kappa')(y1, y2)
Pi_id = e / kap
dk = sp.diff(kap, y1) * dy1 + sp.diff(kap, y2) * dy2
dPi_id = sp.diff(Pi_id, e) * de + sp.diff(Pi_id, y1) * dy1 + sp.diff(Pi_id, y2) * dy2
h_id = e + ell(y1, y2) + Pi_id
dh_id = de + u01 * dy1 + u02 * dy2 + dPi_id
I_plus_p = rho * h_id
e7 = I_plus_p * dPi_id / Pi_id            # (I+p) d1 ln(p/rho), p/rho = Pi
exact = rho * dh_id
ellv = ell(y1, y2)
dell = u01 * dy1 + u02 * dy2
p_id = rho * Pi_id
claim_diff = rho * ellv * dPi_id / Pi_id - p_id * dk - rho * dell
d = sp.simplify(e7 - exact - claim_diff)
print('=== prefactor: (I+p) d ln(p/rho) - rho d h  ==  rho ell d ln(p/rho) - p d kappa - rho d ell  ->', 'PASS' if d == 0 else f'FAIL {d}')
# dry, uniform column: kappa, y constant (d kappa = d ell = 0), ell != 0
ratio = sp.simplify((e7 / exact).subs({dy1: 0, dy2: 0}))
claimed = 1 + ellv / ((kap + 1) * Pi_id)
print('=== dry uniform ratio e7/exact =', sp.factor(ratio), ' claim 1 + ell/((kappa+1) p/rho):',
      'PASS' if sp.simplify(ratio - claimed) == 0 else 'FAIL')
# zero offset, uniform composition: e7 term equals the exact one
z = sp.simplify((e7 - exact).subs({u01: 0, u02: 0, dy1: 0, dy2: 0}))
print('=== dry, uniform, zero-offset limit e7 - exact =', z, '->', 'PASS' if z == 0 else 'FAIL')

# ---- offset invariance: u0 -> u0 + c shifts E by rho c.y; energy row must shift by c.(tracer rows) ----
c1, c2 = sp.symbols('c1 c2', real=True)
def energy_corr_h(o1, o2):
    return s2 * rho * dun * (de + o1 * dy1 + o2 * dy2 + Pd(0) * de + Pd(1) * dy1 + Pd(2) * dy2)
shift_h = sp.simplify(energy_corr_h(u01 + c1, u02 + c2) - energy_corr_h(u01, u02))
tr = c1 * claims['tracer1'] + c2 * claims['tracer2']
print('=== offset shift of the h-differenced energy row == c . (tracer rows) ->', 'PASS' if sp.simplify(shift_h - tr) == 0 else 'FAIL')
def energy_corr_e7(o1, o2):
    hh = e + o1 * y1 + o2 * y2 + Pi_id
    return rho * hh * dPi_id / Pi_id * dun * s2
shift_e7 = sp.simplify(energy_corr_e7(u01 + c1, u02 + c2) - energy_corr_e7(u01, u02))
print('=== offset shift of the e7f9904 energy row =', sp.factor(shift_e7), '; equals c.(tracer rows)?',
      'yes' if sp.simplify(shift_e7 - tr) == 0 else 'no')
```
