> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

Source: snapy 1cf0bbc:docs/derivations/x1-centroid-spherical.md
# #289: $r^2$-exact x1 cell-to-face maps on spherical-polar grids (`SNAP_X1_CENTROID_EXACT`)

This file derives the switch `SNAP_X1_CENTROID_EXACT` (off unless set, read once per process; it acts on
spherical-polar blocks only) and states the oracle it is tested against. It extends the fourth-order
well-balanced reference of `wb-ref4.md` (`SNAP_WB_REF4`) to the $r^2$ cell measure. The exact identities used
below are checked by `docs/derivations/verify_x1_centroid.py` (sympy, exact rational arithmetic). The code is
`src/coord/x1_centroid.cpp`, called from `HydroImpl::forward` (`src/hydro/hydro_forward.cpp`, the x1 block),
`HydroImpl::_hydro_ref_x1` (`src/hydro/hydro.cpp`) and `SphericalPolarImpl::forward`
(`src/coord/spherical_polar.cpp`). The test is `tests/test_x1_centroid_rest.py`.

## 0. Notation

- $r \equiv x_1$, gravity $g$ toward $-r$. Cell $i$ spans $[r_{i-1/2}, r_{i+1/2}]$, width $h_i$, mid-radius
  $\bar r_i$. Face areas and the radial volume, per unit solid angle: $A_{i\pm1/2} = r_{i\pm1/2}^2$,
  $V_i = (r_{i+1/2}^3 - r_{i-1/2}^3)/3$, as `face_area1()` and `cell_volume()` form them.
- A finite-volume cell holds the **$r^2$ mean** $\langle q\rangle_i = V_i^{-1}\int r^2 q\,dr$. The **plain mean**
  is $\overline{q}_i = h_i^{-1}\int q\,dr$.
- $x = (r - \bar r_i)/h_i$ is the local coordinate of cell $i$.

## 1. The defect: the stored value is not the plain mean

Expanding $q$ about $\bar r_i$,

$$
\langle q\rangle_i = \overline{q}_i + \delta_i\, q'(\bar r_i) + O(h^4/\bar r^2), \qquad
\delta_i = \frac{\int r^2 (r-\bar r_i)\,dr}{\int r^2\,dr} = \frac{h_i^2}{6\bar r_i} + O(h^4/\bar r^3),
$$

so the stored value sits at the centroid $x_{1v} = \bar r_i + \delta_i$, not at the mid-radius. Every x1
cell-to-face map in the solver is a uniform-measure formula: the WENO5 reconstruction, the hydrostatic scan
$p_{i-1/2} = p_{i+1/2} + g h_i \rho_i$, the cell pressure reference (the cell average of the quintic through
six faces) and Leg W's density reference. Fed $r^2$ means they are off by $\delta_i q' = O(h^2/r)$:

- (i) the face values of the reconstruction carry $O(h^2/r)$;
- (ii) the scan step is $g h\langle\rho\rangle$ where hydrostatics needs $g\int\rho\,dr = g h\overline\rho$, so the
  face pressures drift by $O(h^2/r)$ per cell against the stored cell pressures $\langle p\rangle$; at rest the
  perturbation $\langle p\rangle - p_{\rm ref}$ is then $O(h^2/r)$ instead of zero, and its reconstructed face
  value is a spurious force;
- (iii) the pressure source. The momentum equation in the cell is
  $-\frac{1}{V}\int r^2 \partial_r p\,dr = -\frac{1}{V}[A p] + \frac{1}{V}\int 2 r p\,dr$. The base source
  (with the face pressures in the flux) is $(A_{i+1/2}p_{i+1/2} - A_{i-1/2}p_{i-1/2})/V_i - (p_{i+1/2} -
  p_{i-1/2})/h_i$, so the net pressure force is the plain difference $-(p_{i+1/2} - p_{i-1/2})/h_i$. It balances
  gravity $g\langle\rho\rangle_i$ only with the scan of (ii); once the scan is right ($g h\overline\rho$), the
  force has to be the $r^2$ mean of $-\partial_r p$, which the plain difference is not.

On a hydrostatic column of $r^2$ means the base therefore leaves an $O(h^2/r)$ radial force, and the
horizontal-energy covariance harness sees a $1/R$ term of magnitude about $0.022/R$ in $\varepsilon_{\rm eff} n_z^2$ (`#289`, leg (d); section 6).

## 2. (i)+(ii): convert every x1 input to plain means

Before the x1 block, every primitive row is replaced, for the x1 maps only, by its plain mean

$$
\overline{q}_i = \sum_{k=0}^{4} c_{i,k}\,\langle q\rangle_{s_i + k},
$$

with weights fixed by exactness for the monomials $x^n$, $n = 0..4$ (in cell $i$'s own coordinate):

$$
\sum_{k} c_{i,k}\,\langle x^n\rangle_{s_i+k} = \overline{x^n}_i = \left(1,\ 0,\ \tfrac{1}{12},\ 0,\ \tfrac{1}{80}\right)_n .
$$

- The window $s_i = \max(\mathrm{lo}, \min(\mathrm{hi}-4, i-2))$ is centred, and kept inside the owned cells at
  a physical x1 wall ($\mathrm{lo} = i_s$, $\mathrm{hi} = i_u$), inside the whole array at a seam.
- The $5\times5$ moment matrix $\langle x^n\rangle_{s+k}$ is integrated by four-point Gauss-Legendre, exact
  because $x^n r^2$ has degree $\le 6$, and solved once per block (dense, partial pivoting).
- Exactness to degree 4 makes the conversion error $O(h^5 q^{(5)})$ times an $O(h/r)$ measure factor, i.e.
  $O(h^6/r)$; it is not exact at degree 5 (both checked in `verify_x1_centroid.py`, interior and both wall
  windows, uniform and stretched grids; the weights sum to 1).
- Ghost cells past a clamped wall get the mirrored correction of the owned cells,
  $\overline{q}_{i_s-1-m} = \langle q\rangle_{i_s-1-m} \pm (\overline{q}_{i_s+m} - \langle q\rangle_{i_s+m})$,
  odd for the normal velocity at a reflecting wall, so a mirrored state stays mirrored.
- The primitives themselves are not changed: the conversion is a view for the x1 maps. After it, the scan step
  is $g h\overline\rho = \int \rho\,dr + O(h^7/r)$, which is (ii), and the reconstruction sees the plain means
  its weights assume, which is (i).

## 3. The reference: Leg W on plain means is $r^2$-exact

On plain means the Leg W reference (`wb-ref4.md`: the filter $F = (-1,4,10,4,-1)/16$ on $\rho/p$ with cubic
wall extrapolation, the quartic-primitive face value, the range and resolution guards) is exactly the
Cartesian algorithm, whose $O(\Delta z^4)$ face-density error is derived there. Nothing in `wb_ref4.cpp`
changes; the switch on a spherical-polar block turns this reference on for the x1 block (`hydro.cpp`), so the
one switch gives the whole design. Its face density is then fourth order in the interior. At the three faces
next to a wall the error is $O(h^3)$, Leg W's own property, the same in Cartesian: the anchor's $O(h^2)$
constant $c$ enters $\rho' = \rho - p_{\rm ref} F[\rho/p]$ as $-c\,F[\rho/p]$, and the even-parity ghosts of
$\rho'$ turn its slope into an $O(h c)$ face value. The base clamped binomial is $O(h)$ there; in a Python replica of the x1
pipeline the wall face-density error goes from $2.7\times10^{-3}$ (base) to
$5.7\times10^{-8}$ ($n_z = 64$) and $7.2\times10^{-9}$ ($n_z = 128$).

## 4. (iii): the pressure source as the $r$-moment of a quintic

With $\tilde p$ the quintic through the six face pressures nearest cell $i$ (window
$s = \max(i_s, \min(i_u - 4, i - 2))$, one-sided at the block ends, so it always contains both faces of cell
$i$), the x1 pressure source is

$$
S_i = \frac{2}{V_i}\int_{r_{i-1/2}}^{r_{i+1/2}} r\,\tilde p\,dr = \sum_{j=0}^{5} w_{i,j}\, p_{s+j}, \qquad
w_{i,j} = \frac{2}{V_i}\int r L_j(r)\,dr ,
$$

$L_j$ the Lagrange basis on the six faces, the integral by four-point Gauss-Legendre (exact: degree 6).
Integration by parts, with $\tilde p$ passing through both faces of the cell,

$$
-\frac{A_{i+1/2} p_{i+1/2} - A_{i-1/2} p_{i-1/2}}{V_i} + S_i = -\frac{1}{V_i}\int r^2\,\tilde p'\,dr ,
$$

so the net pressure force is the $r^2$ mean of $-\partial_r\tilde p$, the finite-volume form of the momentum
equation. A constant $p$ gives $S_i V_i = A_{i+1/2} - A_{i-1/2}$ exactly (with $V_i$ in the same cube form as
`cell_volume()`), so a constant pressure exerts no force against the face-area flux. Both identities are
checked exactly in `verify_x1_centroid.py`.

With `non-hydrostatic` $< 1$ the gravity term is replaced, in part, by the hydrostatic correction, the pressure
gradient of the cell's own reconstructed face states $p^L_{i+1/2}$, $p^R_{i-1/2}$. Without the switch it is the
plain difference $(p^L_{i+1/2} - p^R_{i-1/2})/\Delta x_1$, the same operator as the pressure force, so the two
cancel at rest whatever the column. With the switch the correction takes the operator of the pressure force:

$$
\frac{A_{i+1/2}\,p^L_{i+1/2} - A_{i-1/2}\,p^R_{i-1/2}}{V_i} - S_i ,
$$

$S_i$ from the Riemann face pressures as in the source, so at rest ($p^L = p^R = p^*$) it again cancels the
pressure force exactly, and away from rest the two differ only by $p^* - p^{L,R}$, as without the switch.

## 5. The rest balance and the oracle

Take a hydrostatic column, $p' = -g\rho$, initialised as the cell holds it: $r^2$ means of $\rho$ and $p$. With
the switch:

1. the conversion gives $\overline\rho_i$ to $O(h^6/r)$;
2. the scan gives faces $p_{i-1/2} = p(r_{i-1/2}) + c + O(h^6/r)$ (smooth in $i$), $c$ the anchor constant;
3. the reference cell pressure matches the cell's plain mean to the reference's own (Cartesian) order, so
   at rest the reconstructed perturbation vanishes to that order and the Riemann pressure is the face
   pressure; for the quadratic $p$ of the test below it vanishes to round-off;
4. the net force in cell $i$ is $-\frac{1}{V}\int r^2(\tilde p' + g\rho)\,dr$: the constant $c$ drops out
   (section 4) and $\tilde p' + g\rho = O(h^5/r)$.

For a density of degree $\le 4$ every step is exact and the column is balanced exactly, whatever $c$, and it
is not balanced without the conversion (`verify_x1_centroid.py`, check 4). For a smooth non-polynomial column
the curvature part of the residual is $O(h^6/r)$; what is left is the truncation of the fourth-order reference
itself, the same as in Cartesian geometry. In a Python replica of the x1 pipeline, where the reference is the
exact quintic, the maximum radial force is $3\times10^{-14}$ to $8\times10^{-14}$ at $r/H = 5, 20, 160, 1000$
($n_z = 64, 128$), against the base's $1.5\times10^{-6}$ ($r/H = 5$) to $1.0\times10^{-11}$ ($r/H = 1000$). In
the code (isothermal column $e^{-(r - r_0)/H}$, $n_z = 32$, one RK3 step, $\max|\rho v_1|/(\Delta t\,g\rho)$,
interior / wall cells) the switch takes $r_0/H = 5$ from $2.4\times10^{-5}$ / $2.5\times10^{-5}$ to
$1.0\times10^{-9}$ / $1.8\times10^{-8}$, which is the level of the base at $r_0/H = 1000$
($1.4\times10^{-9}$ / $1.4\times10^{-8}$), where curvature no longer matters: that floor, larger at the walls
(the reference's one-sided wall closure), does not depend on $r_0$.

The oracle (`tests/test_x1_centroid_rest.py`) therefore uses a column the design is exact for: a linear
density $\rho = 1 - 0.3\,(r - r_0)$ (quadratic $p$), cells initialised with their $r^2$ means, at $r_0/H = 5$
and $1000$, $n_z = 32$, explicit and vertically implicit, one RK3 step; asserted: switch on,
$\max|\rho v_1|/(\Delta t\,g\rho) < 10^{-10}$ in the interior and wall cells; switch off, $> 10^{-8}$ at
$r_0/H = 5$ (an ignored or misspelled switch fails). Measured: on, $1\times10^{-14}$ to $3\times10^{-14}$
everywhere; off, $2.4\times10^{-5}$ ($r_0/H = 5$) and $6.5\times10^{-10}$ ($r_0/H = 1000$).

## 6. What is left of the $1/R$ term

In the covariance harness (`#289` leg (d), spherical column, divergence-free seed, cell work, `#293` $x_3$
correction in full) the $1/R$ content $R\,[\varepsilon n_z^2(R) - \varepsilon n_z^2(\infty)]$ goes from
$-0.009 \ldots -0.027$ (base, $R/H = 5 \ldots 1000$, $n_z = 64, 128$) to $+0.0004 \ldots +0.0007$; it tends to
$+0.00045$, an $O(h^2/R)$ term. It is not the centroid and not the reference: it is the reconstruction of
the Favre velocity $\langle\rho w\rangle/\langle\rho\rangle$, a ratio of $r^2$ means and not itself a mean, as if
it were a cell mean of $w$ (a Cartesian $O(h^2)$ error, seen through the $2/r$ of the divergence). Feeding the
exact plain mean of $w$ instead takes it to $-0.00001$ at $n_z = 256$ (same replica). The
same holds for any x1 input that is a ratio of means ($T = p/\rho$, $\rho/p$ inside $F$); the conversion makes
the means plain, not the ratios exact.

The code reproduces the replica (one step, $R/H = 5, 20, 160, 1000$): off $-0.0011, -0.0170, -0.0226,
-0.0236$ and on $+0.0005, +0.0006, +0.0005, -0.0000$ at $n_z = 64$; off $-0.0030, -0.0205, -0.0274, -0.0340$ and
on $+0.0004, +0.0004, -0.0004, -0.0060$ at $n_z = 128$, where $R/H = 1000$ is noise-limited ($R$ times a
$\Delta\varepsilon$ of a few $10^{-10}$). These are column means with unit weight per cell, the harness's
metric. Weighted by cell volume instead, the on arm reads $+0.018 \ldots +0.020$ and the off arm
$-0.004 \ldots -0.012$, in the replica as in the code: the volume weight carries its own $1/R$ ($r^2 \propto
1 + 2x/R$) across the column's error profile, so it does not measure the scheme's $1/R$ term.

## 7. Scope

- **Seams.** The conversion reads ghost cells at an x1 seam, and the windows of the outermost ghosts and the
  source windows at block ends are one-sided, so a column split into x1 blocks differs from one block at
  $O(h^6/r)$. Every block makes the same choice because the switch is read once per process.
- **Cubed sphere.** Not implemented: the gnomonic grids store $x_{1v}$ at the mid-radius, and their x1 maps
  would need the same conversion with the panel's own radial measure. The switch does nothing there.
- **Cartesian.** The switch is inert (no conversion, base source), so Cartesian results are bitwise unchanged.
- **Off.** With the switch off every line of the base runs as before.


## Verification script `docs/derivations/verify_x1_centroid.py` (at `1cf0bbc`)

```python
"""Exact checks behind docs/derivations/x1-centroid-spherical.md (SNAP_X1_CENTROID_EXACT), in sympy.

On a spherical-polar x1 grid of rational faces (r0 = 5, dr = 1/8, ten cells, so r/dr = 40; and a stretched
grid), with exact rational arithmetic:
  1. the five-point r^2-mean -> plain-mean conversion C is exact for every polynomial of degree <= 4, at the
     centred interior window and at both one-sided windows of a clamped wall, and NOT exact at degree 5
     (so its error is O(dr^5) times the fifth derivative);
  2. four-point Gauss-Legendre integrates every integrand the code forms (x^n r^2 with n <= 4; r L_j with L_j
     a quintic) exactly, so the code's weights are the exact ones;
  3. the pressure source S_i = (2/V_i) int r p~ dr, p~ the quintic through six faces, satisfies
     A_{i+1/2} p_{i+1/2} - A_{i-1/2} p_{i-1/2} - V_i S_i = int r^2 p~' dr exactly (integration by parts),
     and a constant pressure gives zero net force, with V_i = (r_{i+1/2}^3 - r_{i-1/2}^3)/3;
  4. the rest balance: for a density rho(r) of degree <= 4 and p = -g int rho dr (degree <= 5), the face
     pressures built by the hydrostatic scan from the CONVERTED cell densities, plus any constant offset c,
     give a net x1 force -(flux difference)/V + S - g <rho>_{r^2} = 0 exactly in every cell.
Every check is an exact identity; the script raises on the first failure.

  python3 docs/derivations/verify_x1_centroid.py
"""
import sympy as sp

r, x = sp.symbols("r x", real=True)
Q = sp.Rational
GX = [sp.sqrt(Q(3, 7) - Q(2, 7) * sp.sqrt(Q(6, 5))), sp.sqrt(Q(3, 7) + Q(2, 7) * sp.sqrt(Q(6, 5)))]
GW = [Q(1, 2) + sp.sqrt(30) / 36, Q(1, 2) - sp.sqrt(30) / 36]
GAUSS4 = [(-GX[1], GW[1]), (-GX[0], GW[0]), (GX[0], GW[0]), (GX[1], GW[1])]


def check(cond, what):
    assert cond, what
    print("ok:", what)


def r2mean(f, a, b):
    return sp.integrate(f * r**2, (r, a, b)) / sp.integrate(r**2, (r, a, b))


def plainmean(f, a, b):
    return sp.integrate(f, (r, a, b)) / (b - a)


def gauss4(f, a, b):
    """four-point Gauss-Legendre of f(r) over [a, b], as the code forms it"""
    return sum(w * f.subs(r, (a + b) / 2 + (b - a) / 2 * xq) for xq, w in GAUSS4) * (b - a) / 2


def conv_weights(xf, i, lo, hi):
    """the code's conversion weights for cell i: window clamped to [lo, hi], moments of x = (r - c)/h"""
    s = max(lo, min(hi - 4, i - 2))
    c, h = (xf[i] + xf[i + 1]) / 2, xf[i + 1] - xf[i]
    M = sp.Matrix(5, 5, lambda n, k: r2mean(((r - c) / h) ** n, xf[s + k], xf[s + k + 1]))
    rhs = sp.Matrix([1, 0, Q(1, 12), 0, Q(1, 80)])
    return s, list(M.LUsolve(rhs))


def lagrange(X, j, t):
    return sp.prod([(t - X[m]) / (X[j] - X[m]) for m in range(len(X)) if m != j])


GRIDS = {
    "uniform r0=5 dr=1/8": [Q(5) + Q(k, 8) for k in range(11)],
    "stretched": [Q(5) + Q(k, 8) + Q(k * k, 400) for k in range(11)],
}

for name, xf in GRIDS.items():
    nc = len(xf) - 1
    # 1. conversion exact to degree 4, not 5; interior and both clamped walls
    for i in (0, 1, nc // 2, nc - 2, nc - 1):
        s, wt = conv_weights(xf, i, 0, nc - 1)
        for deg in range(6):
            f = (r - Q(53, 10)) ** deg
            got = sum(wt[k] * r2mean(f, xf[s + k], xf[s + k + 1]) for k in range(5))
            err = sp.nsimplify(got - plainmean(f, xf[i], xf[i + 1]))
            if deg <= 4:
                check(err == 0, "%s: conversion exact, cell %d (window %d..%d), degree %d" % (name, i, s, s + 4, deg))
            else:
                check(err != 0, "%s: conversion NOT exact at degree 5, cell %d" % (name, i))
        check(sp.simplify(sum(wt) - 1) == 0, "%s: conversion weights sum to 1, cell %d" % (name, i))

    # 2. Gauss-4 is exact for the code's integrands
    a, b = xf[3], xf[4]
    c, h = (a + b) / 2, b - a
    for n in range(5):
        f = ((r - c) / h) ** n * r**2
        check(sp.simplify(gauss4(f, a, b) - sp.integrate(f, (r, a, b))) == 0,
              "%s: Gauss-4 exact for x^%d r^2" % (name, n))
    X = [(xf[3 + j] - c) / h for j in range(6)]
    for j in range(6):
        f = r * lagrange(X, j, (r - c) / h)
        check(sp.simplify(gauss4(f, a, b) - sp.integrate(f, (r, a, b))) == 0,
              "%s: Gauss-4 exact for r L_%d" % (name, j))

    # 3. integration by parts and constant pressure, at an interior and both one-sided windows
    P = sp.symbols("P0:%d" % (nc + 1))
    for i in (0, nc // 2, nc - 1):
        s = max(0, min(nc - 5, i - 2))
        a, b = xf[i], xf[i + 1]
        V = (b**3 - a**3) / 3
        pt = sum(P[s + j] * lagrange([xf[s + k] for k in range(6)], j, r) for j in range(6))
        S = 2 / V * sp.integrate(r * pt, (r, a, b))
        check(sp.expand(pt.subs(r, a) - P[i]) == 0 and sp.expand(pt.subs(r, b) - P[i + 1]) == 0,
              "%s: p~ passes through both faces of cell %d" % (name, i))
        ibp = b**2 * P[i + 1] - a**2 * P[i] - V * S - sp.integrate(r**2 * sp.diff(pt, r), (r, a, b))
        check(sp.expand(ibp) == 0, "%s: A p | - V S = int r^2 p~' dr, cell %d" % (name, i))
        const = {P[k]: 1 for k in range(nc + 1)}
        check(sp.simplify((b**2 - a**2) - V * S.subs(const)) == 0,
              "%s: constant pressure exerts no force, cell %d" % (name, i))

    # 4. rest balance from converted r^2-mean densities, a scan and an arbitrary anchor offset
    g, cst = Q(7, 3), sp.Symbol("c")
    rho = 3 - (r - xf[0]) + Q(1, 2) * (r - xf[0]) ** 2 - Q(1, 5) * (r - xf[0]) ** 3 + Q(1, 9) * (r - xf[0]) ** 4
    rbar = [r2mean(rho, xf[i], xf[i + 1]) for i in range(nc)]
    plain = []
    for i in range(nc):
        s, wt = conv_weights(xf, i, 0, nc - 1)
        plain.append(sum(wt[k] * rbar[s + k] for k in range(5)))

    def worst_force(scan_rho):
        pf = [None] * (nc + 1)
        pf[nc] = cst
        for i in range(nc - 1, -1, -1):  # top-down scan: the hydrostatic step
            pf[i] = pf[i + 1] + g * (xf[i + 1] - xf[i]) * scan_rho[i]
        worst = 0
        for i in range(nc):
            s = max(0, min(nc - 5, i - 2))
            a, b = xf[i], xf[i + 1]
            V = (b**3 - a**3) / 3
            pt = sum(pf[s + j] * lagrange([xf[s + k] for k in range(6)], j, r) for j in range(6))
            S = 2 / V * sp.integrate(r * pt, (r, a, b))
            force = -(b**2 * pf[i + 1] - a**2 * pf[i]) / V + S - g * rbar[i]
            worst = max(worst, abs(sp.nsimplify(sp.expand(force))))
        return worst

    check(worst_force(plain) == 0,
          "%s: rest column of r^2 means is exactly balanced in every cell (any offset c)" % name)
    check(worst_force(rbar) != 0, "%s: without the conversion the same column is not balanced" % name)

print("all checks passed")
```
