#!/usr/bin/env python3
"""Executable check for section 6.4, the corrected-PE face gravity work (scheme D,
SNAP_GRAVITY_WORK_RADIAL_EXACT), book/chapters/06-gravity-energy/_dwork.qmd.

What it checks, from the discrete formulas of snapy at
snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy main):
  C1  sigma^2 of x1_variance equals the exact variance of x1 about the centroid on the
      cell's own measure (Cartesian: h^2/12; spherical-polar: the r^2 measure)        [sympy]
  C2  the weights of centroid_slope are the derivative of the quadratic through three
      centroids, at the middle point inside and at the end point at each block end    [sympy]
  C3  the cell potential energy: int rho phi dV = V [rho_bar phi(x_c) - g1 sigma^2 rho'(x_c)]
      + O(h^4 V); Cartesian remainder -g1 h^5 rho'''/480                              [sympy]
  C4  P = PE_d - g1 sum V sigma^2 s[rho] is O(h^4) accurate, PE_d only O(h^2); s[rho_bar]
      is rho'(x_c) + O(h^2), interior and end cells                                   [numpy]
  C5  uniform Cartesian closed forms of W^D (interior and wall cell) and their accuracy [sympy]
  C6  W^D - g1 <F>_V is O(h^4) in interior and wall cells, W^face only O(h^2)          [numpy]
  C7  E + P is conserved to round-off per RK3 step (snapy's rk3 weights) on closed
      columns: Cartesian non-uniform, spherical R/H = 1, 5, 1000, two x1 blocks, and a
      2-D Cartesian box with x2 fluxes; E + PE_d is not, and changes per stage by exactly
      +g1 sum V sigma^2 s[Delta rho]                                                  [numpy]
  C8  the lumped slope s~ of the implicit matrix: it annihilates constants, equals s inside,
      and at the end cells is (2a+b)/(a(a+b)) (rho_1 - rho_0), not a consistent slope; the
      bookkeeping of the matrix part and the post-solve remainder (an identity by
      construction, printed for the record); a mock solve whose redistribution changes the
      face masses closes E + P, and would not if D were booked on the raw change       [numpy]
  C9  the grid-scale ratio of the sigma^2 s term to the face work is sin^2(theta)/3,
      theta = pi h / lambda: a quarter at wavelength 3h, up to a third at 2h          [sympy]
  C10 an x1 seam: P of a column split into two blocks differs from the one-block P only
      through the one-sided slopes of the two seam cells, by O(h^4) relative          [numpy]
  C11 the VIC energy row: a toy block-tridiagonal column with the code's entry updates
      and right-hand side, solved in the ForwardSweep convention, gives
      dE - dE0 + dt (J delta)_E = +g1 sigma^2 s~[d rho - d rho0] (6.4.18); flipping the
      coupling's sign or swapping its lower/upper weights breaks it                   [numpy]

The numpy ports of x1_variance, centroid_slope and corrected_pe_work below are line for
line against src/hydro/gravity_work_radial.hpp:13-63@e894700ff7aee30b52882e5202b16461413780b0; the lumped matrix stencil is
line for line against src/implicit/implicit_hydro.cpp:301-318@e894700ff7aee30b52882e5202b16461413780b0 (rx_tri:
src/implicit/implicit_hydro.cpp:293-300@e894700ff7aee30b52882e5202b16461413780b0), and the entry updates of C11 against
src/implicit/implicit_hydro.cpp:326-332@e894700ff7aee30b52882e5202b16461413780b0 with the block convention of
src/implicit/forward_sweep_impl.h:35-49, 89-126@e894700ff7aee30b52882e5202b16461413780b0 (B_i multiplies delta_{i-1}, C_i
delta_{i+1}). The column-major entry selection (select(-2, 0).select(-1, m - 1) = row E,
column total mass) is checked by reading, not by this script.

Orders are least-squares fits over the last three resolutions (n1 = 64, 128, 256 unless
stated). Tolerances: "round-off" gates are 1e-14 relative to the conserved total (about 50
ulp of double precision for sums of O(10^2-10^3) terms of one sign); order windows accept
+-0.2 around the predicted order (3.8 for "fourth order") because the fits use three
resolutions that are not yet fully asymptotic.

Run: python3 d_face_work_pe_check.py   (numpy, sympy; a few seconds). Exit status = number of
failed claims. The committed d_face_work_pe_check.out is this script's stdout; it also writes
d_face_work_pe_check.json (the C6 ladders), which the chapter's order figure plots.
"""
import json
import os
import sys

import numpy as np
import sympy as sp

np.set_printoptions(precision=3)
RESULTS = []
DATA = {}  # ladders written to d_face_work_pe_check.json for the data figure


def report(tag, ok, label, numbers=""):
    RESULTS.append(ok)
    print(f"[{tag}] {'PASS' if ok else 'FAIL'} {label}: {numbers}".rstrip(": "), flush=True)
    return ok


def slope_fit(n, e):
    """least-squares order of e(n) ~ n^-p"""
    return -np.polyfit(np.log(np.asarray(n, float)), np.log(np.asarray(e, float)), 1)[0]


# ---------------------------------------------------------------------------------------
# numpy ports of src/hydro/gravity_work_radial.hpp@e894700ff7aee30b52882e5202b16461413780b0 (line numbers in comments)
# ---------------------------------------------------------------------------------------
def x1_variance(x1f, spherical):  # :13-22
    n = x1f.shape[0] - 1
    h = x1f[1:n + 1] - x1f[0:n]
    h2 = h * h
    if not spherical:
        return h2 / 12.
    rb = .5 * (x1f[1:n + 1] + x1f[0:n])
    vol = rb * rb * h + h * h2 / 12.  # (r+^3 - r-^3) / 3
    shift = rb * h * h2 / (6. * vol)  # x1v - rb
    return (rb * rb * h * h2 / 12. + h * h2 * h2 / 80.) / vol - shift * shift


def centroid_slope(q, x):  # :28-51, along the last axis of q
    n = x.shape[0]
    s = np.zeros_like(q)
    if n < 3:
        return s
    hm = x[1:n - 1] - x[0:n - 2]
    hp = x[2:n] - x[1:n - 1]
    s[..., 1:n - 1] = (-hp / (hm * (hm + hp)) * q[..., 0:n - 2]
                       + (hp - hm) / (hm * hp) * q[..., 1:n - 1]
                       + hm / (hp * (hm + hp)) * q[..., 2:n])
    a = x[1] - x[0]
    b = x[2] - x[1]
    s[..., 0] = (-(2. * a + b) / (a * (a + b)) * q[..., 0] + (a + b) / (a * b) * q[..., 1]
                 - a / ((a + b) * b) * q[..., 2])
    a = x[n - 2] - x[n - 3]
    b = x[n - 1] - x[n - 2]
    s[..., n - 1] = (b / (a * (a + b)) * q[..., n - 3] - (a + b) / (a * b) * q[..., n - 2]
                     + (a + 2. * b) / ((a + b) * b) * q[..., n - 1])
    return s


def corrected_pe_work(drho, x1f, x1v, is_, ie, grav1, spherical):  # :57-63
    var = x1_variance(x1f[is_:ie + 1], spherical)
    return grav1 * var * centroid_slope(drho, x1v[is_:ie])


# ---------------------------------------------------------------------------------------
# grid helpers (src/coord: Cartesian x1v = midpoint; spherical-polar x1v = volume centroid)
# ---------------------------------------------------------------------------------------
class Column:
    def __init__(self, x1f, spherical):
        self.f = np.asarray(x1f, float)
        self.sph = spherical
        rm, rp = self.f[:-1], self.f[1:]
        if spherical:  # per steradian
            self.A = self.f ** 2
            self.V = (rp ** 3 - rm ** 3) / 3.
            self.x = 0.75 * (rp ** 4 - rm ** 4) / (rp ** 3 - rm ** 3)
        else:  # per unit horizontal area
            self.A = np.ones_like(self.f)
            self.V = rp - rm
            self.x = 0.5 * (rp + rm)
        self.n = self.V.size

    def div(self, F):
        """Delta_i[A F] / V_i for face values F (n + 1)"""
        return (self.A[1:] * F[1:] - self.A[:-1] * F[:-1]) / self.V

    def avg(self, fun, order=12):
        """exact <fun>_V per cell by Gauss-Legendre on the cell's measure"""
        t, wq = np.polynomial.legendre.leggauss(order)
        rm, rp = self.f[:-1, None], self.f[1:, None]
        r = 0.5 * (rp + rm) + 0.5 * (rp - rm) * t[None, :]
        jac = r ** 2 if self.sph else np.ones_like(r)
        return (0.5 * (rp - rm) * wq[None, :] * jac * fun(r)).sum(1) / self.V


def face_work(col, F, g1):
    """W^face per unit volume and time (src/hydro/hydro_forward.cpp:794-811@e894700ff7aee30b52882e5202b16461413780b0, divided by dt)"""
    phi_f, phi_c = -g1 * col.f, -g1 * col.x
    return phi_c * col.div(F) - col.div(phi_f * F)


def d_work(col, F, g1, blocks=None):
    """W^D = W^face + g1 sigma^2 s[rho_dot], s one-sided at each block's x1 ends"""
    W = face_work(col, F, g1)
    rdot = -col.div(F)
    for lo, hi in blocks or [(0, col.n)]:
        W[lo:hi] += corrected_pe_work(rdot[lo:hi], col.f[lo:hi + 1], col.x[lo:hi], 0, hi - lo,
                                      g1, col.sph)
    return W


def P_of(col, rho, g1, blocks=None):
    """P = sum V [rho phi - g1 sigma^2 s[rho]] (src/mesh/meshblock.cpp:1047-1056@e894700ff7aee30b52882e5202b16461413780b0), per block"""
    pe = rho * (-g1 * col.x)
    for lo, hi in blocks or [(0, col.n)]:
        pe[..., lo:hi] = pe[..., lo:hi] - corrected_pe_work(
            rho[..., lo:hi], col.f[lo:hi + 1], col.x[lo:hi], 0, hi - lo, g1, col.sph)
    return (pe * col.V).sum()


def PEd_of(col, rho, g1):
    return (rho * (-g1 * col.x) * col.V).sum()


# ---------------------------------------------------------------------------------------
def check_C1_variance():
    a, h = sp.symbols("a h", positive=True)
    r = sp.symbols("r", positive=True)
    V = sp.integrate(r ** 2, (r, a, a + h))
    rc = sp.integrate(r ** 3, (r, a, a + h)) / V
    var = sp.integrate((r - rc) ** 2 * r ** 2, (r, a, a + h)) / V
    rb = a + h / 2
    vol = rb * rb * h + h ** 3 / 12
    shift = rb * h ** 3 / (6 * vol)
    code = (rb * rb * h ** 3 / 12 + h ** 5 / 80) / vol - shift ** 2
    d_sph = sp.simplify(var - code)
    d_vol = sp.simplify(V - vol)
    d_shift = sp.simplify(rc - rb - shift)
    z = sp.symbols("z")
    var_c = sp.integrate((z - (a + h / 2)) ** 2, (z, a, a + h)) / h
    d_cart = sp.simplify(var_c - h ** 2 / 12)
    # numerically: no cancellation at large r/h (written about the midpoint)
    f = np.array([1.e6, 1.e6 + 1.])
    exact = float(var.subs({a: sp.Integer(10) ** 6, h: 1}))
    rel = abs(x1_variance(f, True)[0] - exact) / exact
    ok = d_sph == 0 and d_vol == 0 and d_shift == 0 and d_cart == 0 and rel < 1e-12
    return report("C1", ok, "x1_variance = <(x1 - x1v)^2>_V (Cartesian and r^2 measure)",
                  f"symbolic differences {d_cart}, {d_sph}; volume {d_vol}; centroid shift {d_shift}; "
                  f"r/h = 1e6 relative error {rel:.1e}")


def check_C2_slope_weights():
    x0, x1, x2, q0, q1, q2, X = sp.symbols("x0 x1 x2 q0 q1 q2 X")
    L = sp.interpolate([(x0, q0), (x1, q1), (x2, q2)], X)
    dL = sp.diff(L, X)
    hm, hp = x1 - x0, x2 - x1
    inner = -hp / (hm * (hm + hp)) * q0 + (hp - hm) / (hm * hp) * q1 + hm / (hp * (hm + hp)) * q2
    a, b = x1 - x0, x2 - x1
    first = -(2 * a + b) / (a * (a + b)) * q0 + (a + b) / (a * b) * q1 - a / ((a + b) * b) * q2
    last = b / (a * (a + b)) * q0 - (a + b) / (a * b) * q1 + (a + 2 * b) / ((a + b) * b) * q2
    d = [sp.simplify(dL.subs(X, x1) - inner), sp.simplify(dL.subs(X, x0) - first),
         sp.simplify(dL.subs(X, x2) - last)]
    # each stencil annihilates constants and is exact for quadratics
    return report("C2", all(e == 0 for e in d),
                  "centroid_slope weights = derivative of the 3-point quadratic (middle, first, last)",
                  f"symbolic differences {d}")


def check_C3_cell_pe():
    h, g1, zc = sp.symbols("h g1 z_c")
    c = sp.symbols("c0:6")
    z = sp.symbols("z")
    rho = sum(c[k] * (z - zc) ** k for k in range(6))
    exact = sp.integrate(rho * (-g1 * z), (z, zc - h / 2, zc + h / 2))
    rbar = sp.integrate(rho, (z, zc - h / 2, zc + h / 2)) / h
    model = h * (rbar * (-g1 * zc) - g1 * h ** 2 / 12 * c[1])
    rem = sp.expand(exact - model)
    want = -g1 * h ** 5 / 480 * (6 * c[3]) - g1 * h ** 7 * c[5] / 448
    ok_c = sp.simplify(rem - want) == 0
    # spherical: the same identity per steradian, expanded in h about rbar = R
    R, r = sp.symbols("R r", positive=True)
    lo, hi = R - h / 2, R + h / 2
    V = (hi ** 3 - lo ** 3) / 3
    rc = sp.Rational(3, 4) * (hi ** 4 - lo ** 4) / (hi ** 3 - lo ** 3)
    var = sp.integrate((r - rc) ** 2 * r ** 2, (r, lo, hi)) / V
    rho_s = sum(c[k] * (r - rc) ** k for k in range(5))
    ex_s = sp.integrate(rho_s * (-g1 * r) * r ** 2, (r, lo, hi))
    rbar_s = sp.integrate(rho_s * r ** 2, (r, lo, hi)) / V
    model_s = V * (rbar_s * (-g1 * rc) - g1 * var * c[1])
    ser = sp.series(sp.simplify((ex_s - model_s) / V), h, 0, 6).removeO()
    low = [sp.simplify(ser.coeff(h, k)) for k in range(4)]
    c4 = sp.simplify(ser.coeff(h, 4))
    ok_s = all(e == 0 for e in low) and c4 != 0
    return report("C3", ok_c and ok_s,
                  "cell PE = V[rho_bar phi(x_c) - g1 sigma^2 rho'(x_c)] + O(h^4 V)",
                  f"Cartesian remainder = {sp.factor(want)} (rho''' = 6 c3); spherical (per volume): "
                  f"h^0..h^3 coefficients {low}, h^4 coefficient {sp.factor(c4)}")


def check_C4_P_order():
    g1, H = -10., 1.
    out, ok = [], True
    for name, sph, r0 in (("Cartesian, stretched", False, 0.), ("spherical R=5H", True, 5.)):
        e_P, e_D, e_s_in, e_s_end, ns = [], [], [], [], [16, 32, 64, 128, 256]
        for n in ns:
            t = np.linspace(0., 1., n + 1)
            if sph:
                f = r0 + 3. * H * t
            else:  # smooth stretching, h varies by ~2x across the column
                f = 3. * H * (t + 0.15 * np.sin(np.pi * t) * t)
            col = Column(f, sph)
            rho_f = lambda r: np.exp(-(r - f[0]) / H) * (1. + 0.3 * np.sin(2. * (r - f[0])))
            drho_f = lambda r: (-(1. + 0.3 * np.sin(2. * (r - f[0])))
                                + 0.6 * np.cos(2. * (r - f[0]))) * np.exp(-(r - f[0]) / H)
            rho = col.avg(rho_f)
            exact = (col.avg(lambda r: rho_f(r) * (-g1 * r)) * col.V).sum()
            e_P.append(abs(P_of(col, rho, g1) - exact) / abs(exact))
            e_D.append(abs(PEd_of(col, rho, g1) - exact) / abs(exact))
            ds = np.abs(centroid_slope(rho, col.x) - drho_f(col.x))
            e_s_in.append(ds[1:-1].max())
            e_s_end.append(max(ds[0], ds[-1]))
        pP, pD = slope_fit(ns[2:], e_P[2:]), slope_fit(ns[2:], e_D[2:])
        pi, pe = slope_fit(ns[2:], e_s_in[2:]), slope_fit(ns[2:], e_s_end[2:])
        ok &= pP > 3.8 and 1.8 < pD < 2.2 and pi > 1.7 and pe > 1.7
        out.append(f"{name}: |P-PE|/PE {e_P[0]:.2e} -> {e_P[-1]:.2e} (order {pP:.2f}), "
                   f"|PE_d-PE|/PE {e_D[0]:.2e} -> {e_D[-1]:.2e} (order {pD:.2f}); "
                   f"|s[rho_bar]-rho'| interior {e_s_in[0]:.2e} -> {e_s_in[-1]:.2e} (order {pi:.2f}), "
                   f"end cells {e_s_end[0]:.2e} -> {e_s_end[-1]:.2e} (order {pe:.2f})")
    # order threshold 1.7 for s: the fit over nz 64..256 is still pre-asymptotic on the
    # spherical column (local orders 1.6 -> 1.9); the claim used in the text is O(h^2)
    return report("C4", ok, "P is O(h^4), PE_d O(h^2), s[rho_bar] = rho'(x_c) + O(h^2) (nz 16..256)",
                  "; ".join(out))


def check_C5_closed_forms():
    h, g1 = sp.symbols("h g1")
    Fs = sp.symbols("F0:6")  # F_k = F at face k - 1/2, k = 0..5; F0 = wall
    rdot = [-(Fs[k + 1] - Fs[k]) / h for k in range(5)]
    # uniform: interior s = (q_{i+1} - q_{i-1}) / 2h; first cell (-3 q0 + 4 q1 - q2) / 2h
    s_in = (rdot[3] - rdot[1]) / (2 * h)
    s_0 = (-3 * rdot[0] + 4 * rdot[1] - rdot[2]) / (2 * h)
    W_in = g1 * (Fs[3] + Fs[2]) / 2 + g1 * h ** 2 / 12 * s_in  # cell 2: faces 2, 3
    W_0 = (g1 * (Fs[1] + Fs[0]) / 2 + g1 * h ** 2 / 12 * s_0).subs(Fs[0], 0)
    want_in = g1 * ((Fs[3] + Fs[2]) / 2 - (Fs[4] - Fs[3] - Fs[2] + Fs[1]) / 24)
    want_0 = g1 * (19 * Fs[1] - 5 * Fs[2] + Fs[3]) / 24
    d1, d2 = sp.simplify(W_in - want_in), sp.simplify(W_0 - want_0)
    # accuracy: F a polynomial in z; compare with the exact cell average
    z = sp.symbols("z")
    wall = []
    for k in range(1, 5):
        F = z ** k  # F(0) = 0 at the wall
        fv = {Fs[m]: F.subs(z, m * h) for m in range(6)}
        wall.append(sp.simplify(want_0.subs(fv) / g1 - sp.integrate(F, (z, 0, h)) / h))
    a = sp.symbols("a0:7")
    F = sum(a[k] * z ** k for k in range(7))
    fv = {Fs[m]: F.subs(z, (m - sp.Rational(5, 2)) * h) for m in range(6)}  # cell 2 centred at z = 0
    err = sp.expand(want_in.subs(fv) / g1 - sp.integrate(F, (z, -h / 2, h / 2)) / h)
    low = [sp.simplify(err.coeff(h, k)) for k in range(4)]
    h4 = sp.nsimplify(err.coeff(h, 4))
    ok = d1 == 0 and d2 == 0 and wall[:3] == [0, 0, 0] and wall[3] != 0 and low == [0, 0, 0, 0]
    return report("C5", ok, "uniform closed forms: W_i/g1 = (F+ + F-)/2 - (F_{i+3/2}-F_+-F_-+F_{i-3/2})/24, "
                            "W_0/g1 = (19F_1/2 - 5F_3/2 + F_5/2)/24",
                  f"differences {d1}, {d2}; wall cell error for F = z..z^4: {wall} (h^4 for z^4: exact "
                  f"through cubics); interior error h^0..h^3 coefficients {low}, h^4 coefficient {h4} "
                  f"(a4 = F''''/24)")


def check_C6_work_order():
    g1, H, out, ok = -10., 1., [], True
    for name, sph, r0 in (("spherical R=5H", True, 5.), ("Cartesian", False, 0.)):
        ns = [16, 32, 64, 128, 256]
        rows = {k: [] for k in ("face_in", "face_wall", "D_in", "D_wall")}
        for n in ns:
            col = Column(r0 + np.linspace(0., 4. * H, n + 1), sph)
            Ffun = lambda r: np.exp(-(r - r0) / H) * np.sin(np.pi * (r - r0) / (4. * H))
            F = Ffun(col.f)
            F[0] = F[-1] = 0.
            exact = g1 * col.avg(Ffun)
            for key, W in (("face", face_work(col, F, g1)), ("D", d_work(col, F, g1))):
                e = np.abs(W - exact) / abs(g1)
                rows[key + "_in"].append(e[1:-1].max())
                rows[key + "_wall"].append(max(e[0], e[-1]))
        p = {k: slope_fit(ns[2:], v[2:]) for k, v in rows.items()}
        DATA["C6 " + name] = {"nz": ns, **{k: [float(x) for x in v] for k, v in rows.items()}}
        ok &= 1.8 < p["face_in"] < 2.2 and 1.8 < p["face_wall"] < 2.2 and p["D_in"] > 3.8 \
            and p["D_wall"] > 3.8
        out.append(f"{name}: face interior {rows['face_in'][0]:.2e} -> {rows['face_in'][-1]:.2e} "
                   f"(order {p['face_in']:.2f}), face wall {rows['face_wall'][0]:.2e} -> "
                   f"{rows['face_wall'][-1]:.2e} ({p['face_wall']:.2f}); D interior {rows['D_in'][0]:.2e} -> "
                   f"{rows['D_in'][-1]:.2e} ({p['D_in']:.2f}), D wall {rows['D_wall'][0]:.2e} -> "
                   f"{rows['D_wall'][-1]:.2e} ({p['D_wall']:.2f})")
    return report("C6", ok, "max|W - g1<F>_V|/|g1|, F = e^{-z/H} sin(pi z/4H), closed walls, nz 16..256",
                  "; ".join(out))


RK3 = ((0., 1., 1.), (3. / 4., 1. / 4., 1. / 4.), (1. / 3., 2. / 3., 2. / 3.))  # pyharp integrator.cpp


def rk3_step(col, U, dt, g1, blocks, rhs):
    U0 = {k: v.copy() for k, v in U.items()}
    for w0, w1, w2 in RK3:
        du = rhs(col, U, dt, g1, blocks)
        U = {k: w0 * U0[k] + w1 * U[k] + w2 * du[k] for k in U}
    return U


def rhs_1d(col, U, dt, g1, blocks):
    """one explicit stage of a closed column. The identity holds for any face fluxes, so the
    fluxes are arbitrary bounded nonlinear functions of the state (diffusive terms keep the
    toy stable); the momentum row only feeds the fluxes and does not enter E + P"""
    rho, m, E = U["rho"], U["m"], U["E"]
    F = np.zeros(col.n + 1)
    FE = np.zeros(col.n + 1)
    Fm = np.zeros(col.n + 1)
    rl, rr, ml, mr, El, Er = rho[:-1], rho[1:], m[:-1], m[1:], E[:-1], E[1:]
    F[1:-1] = 0.05 * np.tanh(ml + mr) - 0.2 * np.sqrt(np.abs(rl * rr)) * (rr - rl) \
        + 0.01 * np.sin(rl + mr)
    FE[1:-1] = 0.05 * np.tanh((El + Er) * (ml + mr)) - 0.1 * (Er - El)
    Fm[1:-1] = -0.1 * (mr - ml) + 0.05 * np.tanh(rr - rl)
    Fm[0], Fm[-1] = 0.05, -0.05  # wall momentum flux: enters the momentum row only
    div = col.div(F)
    du = {"rho": -dt * div, "m": -dt * col.div(Fm) + 0.3 * dt * np.sin(3. * rho), "E": -dt * col.div(FE)}
    du["E"] += dt * rho * m / rho * g1  # src/forcing/const_gravity.cpp:48-52@e894700ff7aee30b52882e5202b16461413780b0: cell work rho v1 g1
    face = dt * face_work(col, F, g1)  # src/hydro/hydro_forward.cpp:809-811@e894700ff7aee30b52882e5202b16461413780b0
    for lo, hi in blocks:  # src/hydro/hydro_forward.cpp:817-822@e894700ff7aee30b52882e5202b16461413780b0, per block
        face[lo:hi] += corrected_pe_work(-dt * div[lo:hi], col.f[lo:hi + 1], col.x[lo:hi], 0,
                                         hi - lo, g1, col.sph)
    du["E"] += face - dt * rho * m / rho * g1  # src/hydro/hydro_forward.cpp:891@e894700ff7aee30b52882e5202b16461413780b0, face - original
    return du


def check_C7_conservation():
    g1, H, out, ok = -10., 1., [], True
    rng = np.random.default_rng(7)
    cases = (("Cartesian stretched", False, 0., [(0, 32)]),
             ("spherical R=H", True, 1., [(0, 32)]),
             ("spherical R=5H", True, 5., [(0, 32)]),
             ("spherical R=1000H", True, 1000., [(0, 32)]),
             ("spherical R=5H, 2 x1 blocks", True, 5., [(0, 13), (13, 32)]))
    pe_id = []
    for name, sph, r0, blocks in cases:
        t = np.linspace(0., 1., 33)
        f = r0 + 3. * H * (t + (0. if sph else 0.15 * np.sin(np.pi * t) * t))
        col = Column(f, sph)
        U = {"rho": np.exp(-(col.x - f[0]) / H) * (1. + 0.05 * rng.standard_normal(col.n)),
             "m": 0.1 * rng.standard_normal(col.n), "E": 2.5 + 0.1 * rng.standard_normal(col.n)}
        U["E"] = U["E"] * U["rho"]
        dt = 0.2 * (f[1] - f[0])
        EP = lambda U: (U["E"] * col.V).sum() + P_of(col, U["rho"], g1, blocks)
        EPd = lambda U: (U["E"] * col.V).sum() + PEd_of(col, U["rho"], g1)
        # one stage: E + PE_d changes by +g1 sum V sigma^2 s[Delta rho] (the sign of section 2.6)
        du = rhs_1d(col, U, dt, g1, blocks)
        lhs = (du["E"] * col.V).sum() + PEd_of(col, du["rho"], g1)
        rhs = sum((corrected_pe_work(du["rho"][lo:hi], col.f[lo:hi + 1], col.x[lo:hi], 0, hi - lo, g1, sph)
                   * col.V[lo:hi]).sum() for lo, hi in blocks)
        # lhs is a difference of terms of size |du_E V| and |du_rho phi V| (large at R = 1000H), so the
        # round-off gate is relative to their sum, not to the (small) result
        mag = (np.abs(du["E"]) * col.V).sum() + (np.abs(du["rho"] * g1 * col.x) * col.V).sum()
        pe_id.append(abs(lhs - rhs) / mag)
        ok &= abs(lhs - rhs) <= 1e-14 * mag and abs(rhs) > 1e3 * abs(lhs - rhs)
        dEP = dEPd = 0.
        rho_start = U["rho"].copy()
        for _ in range(20):
            a, b = EP(U), EPd(U)
            U = rk3_step(col, U, dt, g1, blocks, rhs_1d)
            d, dd = abs(EP(U) - a) / abs(a), abs(EPd(U) - b) / abs(b)
            dEP = d if not np.isfinite(d) else max(dEP, d)  # a NaN must fail, not vanish in max()
            dEPd = max(dEPd, dd)
        moved = np.abs(U["rho"] - rho_start).max() / np.abs(rho_start).max()  # not a trivial run
        ok &= dEP <= 1e-14 and dEPd > 1e3 * dEP and np.isfinite(U["E"]).all() and moved > 1e-3
        out.append(f"{name}: max per-step |d(E+P)|/|E+P| {dEP:.1e}, |d(E+PE_d)|/|E+PE_d| {dEPd:.1e} "
                   f"(max|rho - rho_0|/max rho_0 after 20 steps {moved:.1e})")
    # 2-D Cartesian box: x2 fluxes move mass between columns at the same level, book no work
    n1, n2 = 24, 8
    t = np.linspace(0., 1., n1 + 1)
    col = Column(3. * H * (t + 0.15 * np.sin(np.pi * t) * t), False)
    dx2 = 0.5
    rho = np.exp(-col.x / H)[None, :] * (1. + 0.05 * rng.standard_normal((n2, n1)))
    E = 2.5 * rho
    m = 0.1 * rng.standard_normal((n2, n1))
    vol = col.V[None, :] * dx2

    def EP2(rho, E):
        pe = rho * (-g1 * col.x) - corrected_pe_work(rho, col.f, col.x, 0, n1, g1, False)
        return ((E + pe) * vol).sum()

    dEP2, dt = 0., 0.2 * (col.f[1] - col.f[0])
    for _ in range(20):
        r0_, E0_, m0_ = rho.copy(), E.copy(), m.copy()
        a = EP2(rho, E)
        for w0, w1, w2 in RK3:
            drho, dE, dm = np.zeros_like(rho), np.zeros_like(E), np.zeros_like(m)
            for jj in range(n2):
                du = rhs_1d(col, {"rho": rho[jj], "m": m[jj], "E": E[jj]}, dt, g1, [(0, n1)])
                drho[jj], dE[jj], dm[jj] = du["rho"], du["E"], du["m"]
            F2 = 0.3 * (rho - np.roll(rho, 1, 0)) + 0.1 * np.sin(rho + np.roll(rho, 1, 0))  # face j-1/2
            FE2 = 0.2 * (E - np.roll(E, 1, 0))
            drho -= dt * (np.roll(F2, -1, 0) - F2) / dx2
            dE -= dt * (np.roll(FE2, -1, 0) - FE2) / dx2
            rho = w0 * r0_ + w1 * rho + w2 * drho
            E = w0 * E0_ + w1 * E + w2 * dE
            m = w0 * m0_ + w1 * m + w2 * dm
        d = abs(EP2(rho, E) - a) / abs(a)
        dEP2 = d if not np.isfinite(d) else max(dEP2, d)
    ok &= dEP2 <= 1e-14
    out.append(f"2-D Cartesian 8x24, periodic x2 fluxes: max per-step |d(E+P)|/|E+P| {dEP2:.1e}")
    out.append("one stage, |d(E+PE_d) - g1 sum V sigma^2 s[d rho]| / (sum|dE V| + sum|d rho phi V|) per case: "
               + ", ".join(f"{v:.1e}" for v in pe_id))
    return report("C7", ok, "E + P per RK3 step, 20 steps, closed x1 walls (tolerance 1e-14 relative)",
                  "; ".join(out))


def lumped(col, g1):
    """rx_tri of src/implicit/implicit_hydro.cpp:293-318@e894700ff7aee30b52882e5202b16461413780b0 (one column)"""
    n = col.n
    S = centroid_slope(np.eye(n), col.x)  # S[k][i]: weight of cell k in the slope of cell i
    gv = g1 * x1_variance(col.f, col.sph)
    rx_mid = gv * np.diagonal(S)
    rx_lo = np.zeros(n)
    rx_hi = np.zeros(n)
    rx_lo[1:] = np.diagonal(S, 1)
    rx_hi[:-1] = np.diagonal(S, -1)
    rx_hi[0] += S[2][0]
    rx_lo[n - 1] += S[n - 3][n - 1]
    rx_lo *= gv
    rx_hi *= gv

    def rx_tri(q):
        s = rx_mid * q
        s[1:] += rx_lo[1:] * q[:-1]
        s[:-1] += rx_hi[:-1] * q[1:]
        return s
    return rx_tri


def check_C8_lumped_slope():
    g1, out, ok = -10., [], True
    rng = np.random.default_rng(3)
    for name, sph, r0 in (("Cartesian", False, 0.), ("spherical R=5H", True, 5.)):
        n = 20
        col = Column(r0 + 3. * np.linspace(0., 1., n + 1) ** 1.1, sph)
        rx_tri = lumped(col, g1)
        gv = g1 * x1_variance(col.f, sph)
        const = np.abs(rx_tri(np.full(n, 3.7))).max()
        q = rng.standard_normal(n)
        inside = np.abs(rx_tri(q)[1:-1] - gv[1:-1] * centroid_slope(q, col.x)[1:-1]).max()
        ends = np.abs(rx_tri(q)[[0, -1]] - (gv * centroid_slope(q, col.x))[[0, -1]]).max()
        a, b = col.x[1] - col.x[0], col.x[2] - col.x[1]  # the lumped first-cell slope, (6.4.16)
        end0 = abs(rx_tri(q)[0] - gv[0] * (2 * a + b) / (a * (a + b)) * (q[1] - q[0])) / abs(rx_tri(q)[0])
        # mock implicit solve: the solve moves mass with face masses M (kg per unit area or per sr),
        # closed walls; redistribution/clamps change them to M' (the solved change); the energy
        # row books the face form of M' (matrix rows + post-solve projection/clamp work, ch. 7)
        # plus, for D, g1 sigma^2 s~[raw - du0] in the matrix and the remainder after the solve.
        drho0 = 0.01 * rng.standard_normal(n)  # explicit total-mass increment (du0)
        M = np.zeros(n + 1)
        M[1:-1] = 0.02 * rng.standard_normal(n - 1)
        Mp = M.copy()
        Mp[5] *= 0.3  # a binding clamp at face 5
        Mp[11] += 0.004
        raw = drho0 - col.div(M)  # delta rho of the solve (before redistribution)
        solved = drho0 - col.div(Mp)  # du[IDN] + sum du[ICY] after redistribution
        moved = solved - drho0
        dE_face = face_work(col, Mp, g1)  # face form of the solved face masses
        matrix_part = rx_tri(raw - drho0)
        post = corrected_pe_work(moved, col.f, col.x, 0, n, g1, sph) - rx_tri(raw - drho0)
        dE = dE_face + matrix_part + post
        total = np.abs(matrix_part + post - gv * centroid_slope(moved, col.x)).max()
        defect = (dE * col.V).sum() + P_of(col, moved, g1)
        mut = ((dE_face + gv * centroid_slope(raw - drho0, col.x)) * col.V).sum() + P_of(col, moved, g1)
        scale = (np.abs(dE) * col.V).sum()
        # gates: s~[const] and s~ - s inside are sums of three O(|g1 sigma^2| / h) terms that cancel
        # exactly in exact arithmetic, so round-off of 1e-13 |g1 sigma^2| max |weight| (weights ~ 1/h ~ 10);
        # the ends must differ at O(1) of the slope (not a round-off difference): > 1e-3 relative.
        wmax = np.abs(gv).max() * 2. / (col.x[1] - col.x[0])
        ok &= const < 1e-13 * wmax and inside < 1e-13 * wmax \
            and ends > 1e-3 * np.abs(rx_tri(q)).max() and end0 < 1e-13 \
            and abs(defect) <= 1e-14 * scale and abs(mut) > 1e3 * abs(defect)
        out.append(f"{name}: |s~[const]| {const:.1e}, |s~-s| inside {inside:.1e}, at the ends {ends:.1e} "
                   f"(first cell = (2a+b)/(a(a+b)) (q1-q0) to {end0:.1e}); bookkeeping identity "
                   f"|matrix + post - g1 sigma^2 s[moved]| {total:.1e} (by construction); mock solve: E+P defect "
                   f"{defect:.1e} (sum|dE V| {scale:.1e}), booked on the raw change instead {mut:.1e}")
    return report("C8", ok, "the lumped slope of the implicit matrix, and the raw-vs-solved booking",
                  "; ".join(out))


def check_C9_grid_scale():
    th = sp.symbols("theta")
    face = sp.cos(th)  # F_{i+-1/2} = cos(theta) for F = cos(2 pi x / lambda), theta = pi h / lambda
    corr = (sp.cos(th) - sp.cos(3 * th)) / 12  # -(F_{i+3/2} - F_+ - F_- + F_{i-3/2}) / 24
    ratio = sp.simplify((corr / face).subs(th, sp.pi / 3))
    small = sp.series(corr / face, th, 0, 4).removeO()
    closed = sp.simplify(sp.expand_trig(corr / face) - sp.sin(th) ** 2 / 3)
    at2h = sp.limit(corr / face, th, sp.pi / 2)
    return report("C9", ratio == sp.Rational(1, 4) and closed == 0 and at2h == sp.Rational(1, 3),
                  "sigma^2 s term / face work for a face-flux wave F = cos(2 pi x / lambda), theta = pi h / lambda",
                  f"ratio = sin^2(theta)/3 (difference {closed}); wavelength 3h: {ratio}; limit at 2h: {at2h}; "
                  f"long waves: {small}, i.e. O(h^2)")


def check_C10_seam():
    g1, H, out, e = -10., 1., [], []
    ns = [32, 64, 128, 256]
    for n in ns:
        col = Column(5. + 3. * np.linspace(0., 1., n + 1), True)
        rho = col.avg(lambda r: np.exp(-(r - 5.) / H) * (1. + 0.3 * np.sin(3. * r)))
        one = P_of(col, rho, g1)
        two = P_of(col, rho, g1, [(0, n // 2), (n // 2, n)])
        e.append(abs(two - one) / abs(one))
    p = slope_fit(ns, e)
    return report("C10", p > 3.8, "x1 seam: |P(2 blocks) - P(1 block)| / |P|, spherical R=5H",
                  f"nz {ns}: {[f'{v:.2e}' for v in e]}, order {p:.2f}")


def check_C11_vic_row():
    """toy column: m = 3 unknowns per cell (total mass, normal momentum, energy) as in the partial VIC"""
    g1, out, ok = -10., [], True
    rng = np.random.default_rng(11)
    for name, sph, r0 in (("Cartesian", False, 0.), ("spherical R=5H", True, 5.)):
        n, m, dt = 12, 3, 0.3
        col = Column(r0 + 3. * np.linspace(0., 1., n + 1) ** 1.1, sph)
        S = centroid_slope(np.eye(n), col.x)  # code convention: S[k][i], cell k in the slope of i
        gv = g1 * x1_variance(col.f, sph)
        rx_mid = gv * np.diagonal(S)
        rx_lo, rx_hi = np.zeros(n), np.zeros(n)
        rx_lo[1:] = np.diagonal(S, 1)
        rx_hi[:-1] = np.diagonal(S, -1)
        rx_hi[0] += S[2][0]
        rx_lo[n - 1] += S[n - 3][n - 1]
        rx_lo, rx_hi = rx_lo * gv, rx_hi * gv
        J0 = 0.3 * rng.standard_normal((n, m, m))  # the Jacobian terms of A_i (without I/dt)
        B0 = 0.3 * rng.standard_normal((n, m, m))
        C0 = 0.3 * rng.standard_normal((n, m, m))
        B0[0] = 0.
        C0[-1] = 0.
        du0 = rng.standard_normal((n, m))  # explicit increment (du0), rows (mass, momentum, energy)

        def solve(sign=1., swap=False):
            A = J0 + np.eye(m)[None] / dt
            B, C = B0.copy(), C0.copy()
            lo, hi = (rx_hi, rx_lo) if swap else (rx_lo, rx_hi)
            A[:, 2, 0] -= sign * rx_mid / dt  # src/implicit/implicit_hydro.cpp:326@e894700ff7aee30b52882e5202b16461413780b0 entry(_a).sub_(rx_mid / dt)
            B[:, 2, 0] -= sign * lo / dt      # :327 entry(_b): multiplies delta_{i-1}
            C[:, 2, 0] -= sign * hi / dt      # :328 entry(_c): multiplies delta_{i+1}
            rhs = du0.copy()
            q = du0[:, 0]
            tri = rx_mid * q
            tri[1:] += rx_lo[1:] * q[:-1]
            tri[:-1] += rx_hi[:-1] * q[1:]
            rhs[:, 2] -= tri                  # :332 du[IPR] -= rx_tri(rx_mass0)
            rhs /= dt                         # src/implicit/forward_sweep_impl.h:35-49@e894700ff7aee30b52882e5202b16461413780b0 rhs = DU / dt
            M = np.zeros((n * m, n * m))
            for i in range(n):
                M[i * m:(i + 1) * m, i * m:(i + 1) * m] = A[i]
                if i > 0:
                    M[i * m:(i + 1) * m, (i - 1) * m:i * m] = B[i]
                if i < n - 1:
                    M[i * m:(i + 1) * m, (i + 1) * m:(i + 2) * m] = C[i]
            return np.linalg.solve(M, rhs.ravel()).reshape(n, m)

        def residual(delta):
            Jd = np.einsum("iab,ib->ia", J0, delta)
            Jd[1:] += np.einsum("iab,ib->ia", B0[1:], delta[:-1])
            Jd[:-1] += np.einsum("iab,ib->ia", C0[:-1], delta[1:])
            q = delta[:, 0] - du0[:, 0]
            tri = rx_mid * q
            tri[1:] += rx_lo[1:] * q[:-1]
            tri[:-1] += rx_hi[:-1] * q[1:]
            lhs = delta[:, 2] - du0[:, 2] + dt * Jd[:, 2]
            return np.abs(lhs - tri).max() / np.abs(tri).max()
        r_ok, r_sign, r_swap = residual(solve()), residual(solve(-1.)), residual(solve(1., True))
        # 1e-12: a dense solve of a 36x36 system with condition number ~1e2-1e3
        ok &= r_ok < 1e-12 and r_sign > 1e-3 and r_swap > 1e-3
        out.append(f"{name}: residual of (6.4.18) {r_ok:.1e}; coupling sign flipped {r_sign:.1e}; "
                   f"lower/upper swapped {r_swap:.1e}")
    return report("C11", ok, "VIC energy row with the D coupling: dE - dE0 + dt (J delta)_E = g1 sigma^2 s~[d rho - d rho0]",
                  "; ".join(out))


def main():
    for chk in (check_C1_variance, check_C2_slope_weights, check_C3_cell_pe, check_C4_P_order,
                check_C5_closed_forms, check_C6_work_order, check_C7_conservation, check_C8_lumped_slope,
                check_C9_grid_scale, check_C10_seam, check_C11_vic_row):
        try:
            chk()
        except Exception as exc:  # a crash is a failure, not a silent skip
            report(chk.__name__.split("_")[1], False, "raised", repr(exc))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "d_face_work_pe_check.json"), "w") as f:
        json.dump(DATA, f, indent=1)
    nfail = RESULTS.count(False)
    print(f"{len(RESULTS) - nfail}/{len(RESULTS)} claims pass", flush=True)
    sys.exit(nfail)


if __name__ == "__main__":
    main()
