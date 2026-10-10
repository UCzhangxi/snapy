"""Executable check of the grid and geometry derivations (chapter 3).

What is checked, against the formulas of snapy@e894700ff7aee30b52882e5202b16461413780b0:
  C1-C3  radial face moments: CoordinateImpl::radial_face_moment2_ and radial_face_centroid_shift_
         (src/coord/coordinate.cpp:446-488) against the exact integrals, and the rationals of
         tests/test_radial_face_moments.cpp:30-34;
  C4-C5  spherical-polar coefficients, centroids, the face-pressure identity and the angular-momentum form
         (src/coord/spherical_polar.cpp:17-28, 78-104, 265-303);
  C6-C9  gnomonic angle, solid angle, lowering and raising, and the uniform-pressure balance
         (src/coord/gnomonic_equiangle.cpp:70-148, 343-413; src/coord/coord_utils_impl.h:9-24);
  C10    Morton rank order of a 4x4 block grid (src/layout/connectivity.hpp:67-70, connectivity.cpp:28-43);
  C11    cross-panel ghost slide (src/coord/cubed_sphere_utils.cpp:78-108).

Run: python3 geometry_check.py   (numpy and sympy only; prints one labelled line per claim and returns the number
of failed claims from main())
"""
import math
import sys

import numpy as np
import sympy as sp


def report(tag, ok, label, numbers=""):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return bool(ok)


rm, rp, rb, h = sp.symbols("r_m r_p rbar h", positive=True)
r = sp.Symbol("r", positive=True)
MID = {rm: rb - h / 2, rp: rb + h / 2}


def I(n):
    return sp.integrate(r**n, (r, rm, rp))


def check_C1_centroids():
    rc = sp.simplify((I(2) / I(1)).subs(MID))
    rv = sp.simplify((I(3) / I(2)).subs(MID))
    ok = sp.simplify(rc - (12 * rb**2 + h**2) / (12 * rb)) == 0 and \
        sp.simplify(rv - 3 * rb * (4 * rb**2 + h**2) / (12 * rb**2 + h**2)) == 0
    return report("C1", ok, "face centroid I2/I1 and volume centroid I3/I2", "closed forms exact (sympy)")


def moment_shift():
    c = I(2) / I(1)
    m2 = sp.simplify(((I(3) - 2 * c * I(2) + c**2 * I(1)) / I(1)).subs(MID))
    shift = sp.simplify((I(3) / I(2) - c).subs(MID))
    return m2, shift


def check_C2_rationals():
    m2, shift = moment_shift()
    cases = [(sp.Rational(3, 2), sp.Rational(5, 2), sp.Rational(47, 1176), sp.Rational(47, 576)),
             (3, 5, sp.Rational(47, 588), sp.Rational(47, 144)),
             (1, 2, sp.Rational(13, 252), sp.Rational(13, 162))]
    ok = True
    for a, b, s, m in cases:
        sub = {rb: sp.Rational(a + b, 2), h: sp.Rational(b - a)}
        ok &= sp.simplify(shift.subs(sub) - s) == 0 and sp.simplify(m2.subs(sub) - m) == 0
    return report("C2", ok, "test rationals", "shift 47/1176, 47/588, 13/252; moment 47/576, 47/144, 13/162: exact")


def check_C3_code_forms():
    m2, shift = moment_shift()
    code_m2 = h**2 / 12 * (1 - h**2 / (12 * rb**2))                               # coordinate.cpp:455-458
    code_shift = h**2 * (12 * rb**2 - h**2) / (12 * rb * (12 * rb**2 + h**2))     # coordinate.cpp:482-485
    ok = sp.simplify(m2 - code_m2) == 0 and sp.simplify(shift - code_shift) == 0
    lead = sp.limit(shift / (h**2 / (12 * rb)), h, 0)
    return report("C3", ok and lead == 1, "cancellation-free moment and shift equal the integrals",
                  "shift / (h^2/(12 rbar)) -> %s as h -> 0" % lead)


def check_C4_spherical_coefficients():
    th, tm, tp = sp.symbols("theta theta_m theta_p", positive=True)
    inv_r = sp.integrate(r, (r, rm, rp)) / sp.integrate(r**2, (r, rm, rp))
    cot = sp.integrate(sp.cos(th), (th, tm, tp)) / sp.integrate(sp.sin(th), (th, tm, tp))
    x2v = sp.integrate(th * sp.sin(th), (th, tm, tp)) / sp.integrate(sp.sin(th), (th, tm, tp))
    ok = sp.simplify(inv_r - sp.Rational(1, 2) * (rp**2 - rm**2) / ((rp**3 - rm**3) / 3)) == 0
    ok &= sp.simplify(cot - (sp.sin(tp) - sp.sin(tm)) / (sp.cos(tm) - sp.cos(tp))) == 0
    ok &= sp.simplify(x2v - ((sp.sin(tp) - tp * sp.cos(tp)) - (sp.sin(tm) - tm * sp.cos(tm)))
                      / (sp.cos(tm) - sp.cos(tp))) == 0
    return report("C4", ok, "coord_src1_i = <1/r>, coord_src1_j = <cot theta>, polar centroid", "exact (sympy)")


def check_C5_sources():
    V1 = (rp**3 - rm**3) / 3
    ok = sp.simplify((rp**2 - rm**2) / V1 - 2 * (sp.Rational(1, 2) * (rp**2 - rm**2)) / V1) == 0
    Fm, Fp = sp.symbols("F_m F_p")
    c2 = (rp - rm) / ((rm + rp) * V1)                                           # spherical_polar.cpp:92-94
    total = (rp**2 * Fp - rm**2 * Fm) / V1 + c2 * (rm**2 * Fm + rp**2 * Fp)
    ok &= sp.simplify(total - (rp**3 * Fp - rm**3 * Fm) / ((rm + rp) / 2 * V1)) == 0
    return report("C5", ok, "uniform-p face form = 2p<1/r>; r-flux angular-momentum form telescopes",
                  "exact (sympy), with r^2 per unit solid angle")


def gnomonic_angle(X, Y):  # gnomonic_equiangle.cpp:75-81
    C, D = np.sqrt(1 + X * X), np.sqrt(1 + Y * Y)
    return -X * Y / (C * D), np.sqrt(1 + X * X + Y * Y) / (C * D)


def unit(xi, eta):
    v = np.array([1.0, math.tan(xi), math.tan(eta)])
    return v / np.linalg.norm(v)


def check_C6_angle():
    worst = 0.0
    e = 1e-6
    for xi, eta in [(0.6, -0.4), (-0.7, 0.7), (0.2, 0.75), (0.0, 0.3)]:
        a = unit(xi + e, eta) - unit(xi - e, eta)
        b = unit(xi, eta + e) - unit(xi, eta - e)
        num = a @ b / np.linalg.norm(a) / np.linalg.norm(b)
        c, s = gnomonic_angle(math.tan(xi), math.tan(eta))
        worst = max(worst, abs(num - c), abs(c * c + s * s - 1))
    c_corner, _ = gnomonic_angle(1.0, 1.0)
    # 1e-8: central differences with step 1e-6 carry O(1e-12) truncation and O(1e-10) round-off
    return report("C6", worst < 1e-8 and abs(c_corner + 0.5) < 1e-15, "cos psi = -XY/(CD), sin psi = delta/(CD)",
                  "max deviation from finite-difference tangents %.1e; corner cos psi = %.2f" % (worst, c_corner))


def check_C7_solid_angle():
    n = 7
    a = np.linspace(-math.pi / 4, math.pi / 4, n + 1)
    X, Y = np.meshgrid(np.tan(a), np.tan(a), indexing="ij")
    corner = np.arctan(X * Y / np.sqrt(1 + X * X + Y * Y))                      # gnomonic_equiangle.cpp:130
    omega = corner[1:, 1:] - corner[1:, :-1] - corner[:-1, 1:] + corner[:-1, :-1]
    six = 6 * omega.sum() - 4 * math.pi
    # Gauss-Legendre quadrature of dX dY / delta^3 over one cell
    g, w = np.polynomial.legendre.leggauss(40)
    x0, x1, y0, y1 = math.tan(a[2]), math.tan(a[3]), math.tan(a[1]), math.tan(a[2])
    xs, ys = 0.5 * (x1 - x0) * g + 0.5 * (x1 + x0), 0.5 * (y1 - y0) * g + 0.5 * (y1 + y0)
    XX, YY = np.meshgrid(xs, ys, indexing="ij")
    q = 0.25 * (x1 - x0) * (y1 - y0) * (np.outer(w, w) / (1 + XX**2 + YY**2) ** 1.5).sum()
    dq = q - omega[2, 1]
    # 1e-13 / 1e-14: a sum of 49 or 4 arctangents of order 1 in double precision
    return report("C7", abs(six) < 1e-13 and abs(dq) < 1e-14, "corner-sum solid angle",
                  "6 panels - 4 pi = %.1e; quadrature - corner sum = %.1e" % (six, dq))


def check_C8_lower_raise():
    c, v, w = sp.symbols("c v w")
    lv, lw = v + w * c, w + v * c                                               # coord_utils_impl.h:19-24
    s2 = 1 - c**2
    rv, rw = lv / s2 - lw * c / s2, -lv * c / s2 + lw / s2                       # coord_utils_impl.h:9-16
    s = sp.sqrt(1 - c**2)
    norm = sp.simplify(((v + c * w) ** 2 + (s * w) ** 2) - (v**2 + w**2 + 2 * c * v * w))
    ok = sp.simplify(rv - v) == 0 and sp.simplify(rw - w) == 0 and norm == 0
    return report("C8", ok, "raise(lower(v)) = v; x1-face orthonormal frame keeps |v|^2", "exact (sympy)")


def flux2global2(txy, txz, c, s):  # gnomonic_equiangle.cpp:357-384, with g22 = g33 = 1, gi22 = 1/s^2
    fz = -(1 / s) * c * txy + txz
    fy = (1 / s) * txy
    return fy + fz * c, fz + fy * c


def flux2global3(txy, txz, c, s):  # gnomonic_equiangle.cpp:386-413
    fy = txy - c * (1 / s) * txz
    fz = (1 / s) * txz
    return fy + fz * c, fz + fy * c


def check_C9_uniform_pressure():
    worst = 0.0
    for X, Y in [(0.3, -0.8), (1.0, 1.0), (-0.5, 0.2)]:
        c, s = gnomonic_angle(X, Y)
        m2, m3 = flux2global2(1.0, 0.0, c, s)
        worst = max(worst, abs(m2 - s), abs(m3))
        m2, m3 = flux2global3(0.0, 1.0, c, s)
        worst = max(worst, abs(m2), abs(m3 - s))
    # 1e-15: three products of O(1) numbers in double precision
    return report("C9", worst < 1e-15, "a face pressure p maps to covariant flux (p sin psi, 0) on x2 faces",
                  "max deviation %.1e (x2 and x3 faces, three points)" % worst)


def compact(x):
    x &= 0x55555555
    x = (x ^ (x >> 1)) & 0x33333333
    x = (x ^ (x >> 2)) & 0x0F0F0F0F
    x = (x ^ (x >> 4)) & 0x00FF00FF
    return (x ^ (x >> 8)) & 0x0000FFFF


def morton(px, py):  # connectivity.cpp:28-43, connectivity.hpp:67-70
    out, code = [], 0
    while len(out) < px * py:
        x, y = compact(code), compact(code >> 1)
        if x < px and y < py:
            out.append((x, y))
        code += 1
    return out


def check_C10_morton():
    order = morton(4, 4)
    ok = order[:4] == [(0, 0), (1, 0), (0, 1), (1, 1)] and order[4] == (2, 0) and len(set(order)) == 16
    return report("C10", ok, "Morton order of a 4x4 block grid (rx, ry) by rank", " ".join("%d%d" % p for p in order))


def slide(N, ng):
    d = math.pi / (2 * N)
    worst, dev = 0.0, 0.0
    for g in range(1, ng + 1):
        xi = math.pi / 4 + (g - 0.5) * d
        for j in range(N):
            eta = -math.pi / 4 + (j + 0.5) * d
            s = (eta - math.atan(math.tan(eta) / math.tan(xi))) / d
            worst, dev = max(worst, abs(s)), max(dev, abs(s - (g - 0.5) * math.sin(2 * eta)))
    return worst, dev


def check_C11_slide():
    worst, dev = slide(64, 3)
    return report("C11", worst < 2.5 and dev < 0.08, "ghost source slide, N = 64, nghost = 3",
                  "max slide %.4f cells (bound 2.5); max |exact - (l - 1/2) sin 2 eta| %.3f cells" % (worst, dev))


def main():
    checks = [check_C1_centroids, check_C2_rationals, check_C3_code_forms, check_C4_spherical_coefficients,
              check_C5_sources, check_C6_angle, check_C7_solid_angle, check_C8_lower_raise,
              check_C9_uniform_pressure, check_C10_morton, check_C11_slide]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
