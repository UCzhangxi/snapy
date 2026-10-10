> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

Source: snapy 4d3b4d7:docs/derivations/diffusion-face-coefficient.md
# The x1 face coefficient of the diffusive fluxes with an x1 profile

**Scope.** `forcing/diffusion` with `nu_scale_x1` or `kappa_scale_x1` set. The
kinematic coefficients are multiplied by a dimensionless x1 profile $s(x_1)$, so
the coefficient that multiplies the gradient in the flux is a product of two
cell fields,

$$
c = s\,q, \qquad q = \rho \ \text{(viscosity, } \mu = \nu s \rho\text{)}, \qquad
q = \rho c_v \ \text{(conduction, } k = \kappa s \rho c_v\text{)} .
$$

The flux through the x1 face $i-\tfrac12$ between cells $a = i-1$ and $b = i$
is $F = -c_{i-1/2}\,(T_b - T_a)/\Delta x$ (and the same with $v$ in place of
$T$ for the shear stress); the tendency is
$-(F_{i+1/2} - F_{i-1/2})/\Delta x$ on a uniform Cartesian mesh.

**Base.** `src/forcing/diffusion.cpp:173-193` at `aea71ed` (`chengcli/snapy`
`main`), `face_scaled_coefficient`. The wall faces of a reflecting x1 boundary
already extrapolate the product $s q$ linearly from the two nearest active
cells; only the interior faces are at issue. On x2 and x3 faces both cells share
one x1 position, so $s_a = s_b$ and the two forms below coincide.

## 1. Product of means against mean of products

The base takes the product of the two face averages,

$$
c^{\rm PM}_{i-1/2} = \frac{s_a + s_b}{2}\,\frac{q_a + q_b}{2}
= \frac{s_a q_a + s_b q_b}{2} - \frac{(s_b - s_a)(q_b - q_a)}{4} ,
$$

so it differs from the mean of the products,

$$
c^{\rm MP}_{i-1/2} = \frac{s_a q_a + s_b q_b}{2} ,
$$

by the covariance term $-\tfrac14\,\Delta s\,\Delta q$.

**A constant dynamic coefficient.** Let $s\,q = C$ be uniform (a stratified
column with $s = C/q$: the convection decks whose dynamic viscosity and
conductivity are constant, $\nu = \nu_t/\rho_0(z)$, put $s = 1/\rho_0$). Then
$c^{\rm MP} = C$ exactly on every face, while

$$
c^{\rm PM}_{i-1/2} = \frac{C}{4}\left(\frac1{q_a} + \frac1{q_b}\right)(q_a + q_b)
= C\left[1 + \frac{(q_b - q_a)^2}{4\,q_a q_b}\right] .
$$

With $\Delta q \simeq q'\Delta x$ the excess is
$e_{i-1/2} = \tfrac14 (\Delta x\, q'/q)^2 + O(\Delta x^3)$: second order, always
positive, largest where the relative gradient $q'/q$ is largest. For a linear $T$
(conductive equilibrium, $F_0 = -C\,T'$ uniform) the tendency of cell $i$ is

$$
\dot E_i = -\frac{F_0}{\Delta x}\,(e_{i+1/2} - e_{i-1/2})
\simeq -F_0\, e'(x_i) = O(\Delta x^2)
$$

inside. In the cell next to a wall one face is the extrapolated wall face, whose
coefficient is exact ($e = 0$), so there

$$
\dot E_{\rm wall} = \pm\frac{F_0}{\Delta x}\, e_{\rm first\ interior\ face}
= O(\Delta x) .
$$

For a density that falls upward, $q'/q$ is largest at the top, so the top cell
takes the largest spurious heating (with $F_0$ upward, the top wall face carries
less flux than the face below it); the column builds a thin stable layer there.

**A smooth variable coefficient.** $c^{\rm MP}$ is the trapezoidal average of
$c(x)$ over the face, so $c^{\rm MP} = c(x_{i-1/2}) + O(\Delta x^2)$; the
centred difference of $T$ is second order too, and the face flux converges at
second order. $c^{\rm PM}$ differs from it by $\tfrac14 s' q' \Delta x^2$, also
second order: on a smooth problem with no special balance both forms converge
at the same rate, and the difference shows only where a balance should be exact.

## 2. The fix

`face_scaled_coefficient(value, scale, ...)` now returns
`face_coefficient(value * scale, ...)`: the same two-cell average and wall
extrapolation that the unscaled coefficient already uses, applied to the
product. A profile of ones gives the coefficient of no profile bit for bit
($q \times 1 = q$). Without a profile the code path is not entered, so every
case that sets neither `nu_scale_x1` nor `kappa_scale_x1` is unchanged.

## 3. Checks

- `docs/derivations/diffusion_face_coefficient.py`: a numpy transcription of
  the x1 operator (interior average, wall extrapolation, centred gradient).
  Constant $C$ on $\rho = (1.25 - x)^{3/2}$, $x \in [0, 1]$, $T = 300 + 50x$:
  mean of products gives $|\dot E| \le 10^{-12}$; product of means gives
  $|\dot E|_{\max}$ = 18.3, 11.2, 6.24, 3.31 at nx = 16, 32, 64, 128 (order
  0.7, 0.84, 0.92, the wall cell) and 5.6, 2.1, 0.67, 0.19 inside (order 1.40,
  1.66, 1.81). Smooth $s = 1 + \tfrac12\cos 3x$, $T = 300 + 50\sin 2x$: face
  flux error order 1.91, 1.96, 1.98 for both forms.
- `tests/test_diffusion_x1_scale.cpp`,
  `constant_dynamic_coefficient_column_has_no_tendency`: the same column through
  `Diffusion::forward`, conduction and shear, every interior cell
  $|\dot u| < 10^{-12}\,|F|/\Delta x$ at nx1 = 16 and 64. Fails on the base.
- `smooth_profile_flux_converges_at_second_order`: the face fluxes recovered
  from the tendency by summing up from the lower wall, against the exact flux,
  order $> 1.85$ from nx1 = 32 to 64 to 128, conduction and shear. Passes on
  both forms, as §1 predicts.


## Verification script `docs/derivations/diffusion_face_coefficient.py` (at `4d3b4d7`)

```python
"""Face coefficient of the x1 diffusive flux with an x1 profile: product of
means against mean of products.

A transcription of DiffusionImpl::forward's x1 conductive flux on a uniform
Cartesian column with reflecting walls: interior face coefficient from the two
neighbouring cells, wall face extrapolated linearly from the two nearest active
cells, normal gradient (T_i - T_{i-1}) / dx, tendency -(F_{i+1/2} - F_{i-1/2})
/ dx. The coefficient is c = s * q with s the x1 profile and q the cell value
(rho, or rho cv); both forms extrapolate the product s q at a wall.

  1. constant c (s = 1/q, T linear): the mean of products gives zero tendency
     to round-off; the product of means gives an O(dx^2) tendency.
  2. smooth variable c: both forms give a second-order face flux.

  python diffusion_face_coefficient.py
"""
import numpy as np

NG = 2


def rho_of(x):
    """polytrope-like column: rho falls ~10x over [0, 1], fastest at the top"""
    return (1.25 - x) ** 1.5


def column(nx):
    dx = 1. / nx
    x = (np.arange(nx + 2 * NG) - NG + 0.5) * dx
    return x, dx


def face_coefficient(s, q, form):
    """interior faces i - 1/2 for i = NG .. NG + nx (nx + 1 faces)"""
    a, b = slice(NG - 1, -NG), slice(NG, -NG + 1 or None)
    if form == "product_of_means":
        c = 0.5 * (s[a] + s[b]) * 0.5 * (q[a] + q[b])
    else:
        c = 0.5 * (s[a] * q[a] + s[b] * q[b])
    p = s * q  # walls: linear extrapolation of the product, uniform mesh
    c[0] = 1.5 * p[NG] - 0.5 * p[NG + 1]
    c[-1] = 1.5 * p[-NG - 1] - 0.5 * p[-NG - 2]
    return c


def face_flux(s, q, T, dx, form):
    a, b = slice(NG - 1, -NG), slice(NG, -NG + 1 or None)
    return -face_coefficient(s, q, form) * (T[b] - T[a]) / dx


def tendency(s, q, T, dx, form):
    F = face_flux(s, q, T, dx, form)
    return -(F[1:] - F[:-1]) / dx


def main():
    print("1. constant c = s q = 1, T = 300 + 50 x, F = -50: max|tendency| over all cells,")
    print("   and over the interior (the two wall cells left out)")
    print("%6s %14s %14s %8s %14s %8s" % ("nx", "mean_of_prod", "prod_of_means", "order",
                                         "interior", "order"))
    prev = None
    for nx in (16, 32, 64, 128):
        x, dx = column(nx)
        q = rho_of(x)
        s, T = 1. / q, 300. + 50. * x
        new = np.abs(tendency(s, q, T, dx, "mean_of_products")).max()
        du = tendency(s, q, T, dx, "product_of_means")
        old, inner = np.abs(du).max(), np.abs(du[1:-1]).max()
        order = ("", "") if prev is None else tuple(
            "%.2f" % np.log2(a / b) for a, b in zip(prev, (old, inner)))
        print("%6d %14.3e %14.3e %8s %14.3e %8s" % (nx, new, old, order[0], inner, order[1]))
        prev = old, inner
        assert new < 1e-12 * 50. / dx, new

    print("2. smooth c = (1 + 0.5 cos 3x) rho, T = 300 + 50 sin 2x: "
          "max|F - F_exact| / max|F_exact| at the faces")
    print("%6s %14s %8s %14s %8s" % ("nx", "mean_of_prod", "order", "prod_of_means", "order"))
    prev = {}
    for nx in (32, 64, 128, 256):
        x, dx = column(nx)
        xf = np.arange(nx + 1) * dx
        q, s, T = rho_of(x), 1. + 0.5 * np.cos(3. * x), 300. + 50. * np.sin(2. * x)
        exact = -(1. + 0.5 * np.cos(3. * xf)) * rho_of(xf) * 100. * np.cos(2. * xf)
        row = [nx]
        for form in ("mean_of_products", "product_of_means"):
            e = np.abs(face_flux(s, q, T, dx, form) - exact).max() / np.abs(exact).max()
            row += [e, "" if form not in prev else "%.2f" % np.log2(prev[form] / e)]
            prev[form] = e
        print("%6d %14.3e %8s %14.3e %8s" % tuple(row))
        if row[2]:
            assert float(row[2]) > 1.9, row


if __name__ == "__main__":
    main()
```
