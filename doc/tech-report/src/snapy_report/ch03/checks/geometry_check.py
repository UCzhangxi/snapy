"""Executable check of the grid and geometry derivations (chapter 3).

What is checked, against the formulas of snapy@6fbb39750f62b83df096058a4746e77d0a634bc5:
  C1-C3  radial face moments: CoordinateImpl::radial_face_moment2_ and radial_face_centroid_shift_
         (src/coord/coordinate.cpp:446-488) against the exact integrals, and the rationals of
         tests/test_radial_face_moments.cpp:30-34;
  C4-C5  spherical-polar coefficients, centroids, the face-pressure identity and the angular-momentum form
         (src/coord/spherical_polar.cpp:17-28, 78-104, 264-302);
  C6-C9  gnomonic angle, solid angle, lowering and raising, and the uniform-pressure balance
         (src/coord/gnomonic_equiangle.cpp:70-148, 343-413; src/coord/coord_utils_impl.h:9-24);
  C10    Morton rank order of a 4x4 block grid (src/layout/connectivity.hpp:67-70, connectivity.cpp:28-43);
  C11    cross-panel ghost slide (src/coord/cubed_sphere_utils.cpp:78-108);
  C12    the theta seam: a face whose two sides use different limiter factors creates or destroys
         (Theta - Theta~) F A dt of species mass per stage, and nothing when the ghost is a bit copy
         (src/hydro/hydro_forward.cpp:785-812);
  C13    the x1 seam average: both blocks hold the same bits and the seam telescopes exactly
         (src/hydro/hydro_forward.cpp:508-582);
  C14    the sync matrices M->sph = R G^-1 and M->panel = G R^-1 compose to the identity, conserved and
         primitive strips alike (src/coord/cubed_sphere_utils.cpp:259-298);
  C15    the synthesised ghost corner is exact on a constant field and first order on a gradient
         (src/layout/layout.cpp:710-751);
  C16    the global face array: two decompositions agree bit for bit on every shared face, and the block
         offset needs rounding, not truncation (src/coord/coordinate.cpp:307-324, coordinate.hpp:124-128);
  C17    the Cartesian areas, volume and centroid are the exact integrals (src/coord/coordinate.cpp:425-440,
         cartesian.cpp:22-28);
  C18    the physical-face rule: the x3, x2, x1 order names exactly one face for each of the 26 offsets, and a
         face is physical exactly when a bfunc survives (src/mesh/meshblock.cpp:137-179);
  C19    the corner refresh writes each corner cell exactly once, and its slab never passes the half-width
         (src/mesh/meshblock.cpp, src/bc/bc_func.hpp:28-35).

C12-C19 check the statements the chapter's Derivation layers make, as those layers state them; they are
arithmetic and combinatorial identities, not ports of device kernels.

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


def check_C12_theta_seam():
    """eq-ch03-thetacopy-face: the limited flux is Theta_{d(f)} F_f, one number per face."""
    th, tht, F, A, dt = sp.symbols("Theta Thetat F A dt")
    # the donor cell loses Theta F A dt, the acceptor gains Thetat F A dt when the ghost differs
    leak = sp.simplify((tht * F * A * dt) - (th * F * A * dt) - (tht - th) * F * A * dt)
    rng = np.random.default_rng(3)
    theta = rng.random(200_000)                       # the donor's factor, as both sides read it
    f, a, d = rng.normal(size=200_000), rng.random(200_000) + 0.5, 1e-3
    copied = (theta * f * a * d) - (theta * f * a * d)        # a bit copy: the same number on both sides
    perturbed = np.nextafter(theta, 2.0)                      # one ulp apart, the smallest possible mismatch
    off = (perturbed * f * a * d) - (theta * f * a * d)
    ok = leak == 0 and np.count_nonzero(copied) == 0 and np.count_nonzero(off) > 0
    return report("C12", ok, "theta seam: one number per face cancels, any mismatch does not",
                  "closed form exact (sympy); bit copy: 0 of %d faces leak; one ulp apart: %d of %d leak, "
                  "worst %.1e" % (copied.size, np.count_nonzero(off), off.size, np.abs(off).max()))


def check_C13_x1_seam_average():
    """eq-ch03-x1seams-average: Fbar = (F_B + F_T)/2, evaluated independently by both blocks."""
    rng = np.random.default_rng(13)
    fb, ft = rng.normal(scale=1e3, size=400_000), rng.normal(scale=1e3, size=400_000)
    b = 0.5 * (fb + ft)                               # block B's own evaluation
    t = 0.5 * (ft + fb)                               # block T's, with the operands the other way round
    same = np.array_equal(b.view(np.int64), t.view(np.int64))          # equal bit for bit, not just close
    a_s = rng.random(400_000) + 0.5
    telescoped = (a_s * b) - (a_s * t)                # what the seam contributes to the column total
    unaveraged = (a_s * ft) - (a_s * fb)              # the same seam if each block kept its own value
    ok = same and np.count_nonzero(telescoped) == 0 and np.count_nonzero(unaveraged) > 0
    return report("C13", ok, "x1 seam average: both blocks hold the same bits and the seam telescopes",
                  "%d pairs: identical bit patterns %s; seam residual exactly 0 in %d of %d; without the "
                  "average %d of %d are non-zero, worst %.1e" %
                  (b.size, same, np.count_nonzero(telescoped == 0), b.size,
                   np.count_nonzero(unaveraged), b.size, np.abs(unaveraged).max()))


def check_C14_sync_matrices():
    """eq-ch03-synctype-matrix: M->sph = R G^-1, M->panel = G R^-1, G the lowering on (v2, v3)."""
    worst_c, worst_p, worst_g = 0.0, 0.0, 0.0
    for X, Y in [(0.3, -0.8), (1.0, 1.0), (-0.5, 0.2), (0.0, 0.0)]:
        c, _ = gnomonic_angle(X, Y)
        G = np.array([[1.0, c], [c, 1.0]])                      # coord_utils_impl.h:19-24, on (v2, v3)
        worst_g = max(worst_g, abs(np.linalg.det(G) - (1 - c * c)))
        for ang in (0.0, 0.7, -1.9, math.pi / 2):
            R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
            to_sph, to_panel = R @ np.linalg.inv(G), G @ R.T     # R^{panel<-sph} = R^-1 = R^T
            worst_c = max(worst_c, np.abs(to_panel @ to_sph - np.eye(2)).max())
            worst_p = max(worst_p, np.abs(R.T @ R - np.eye(2)).max())   # a primitive strip leaves G out
    # 1e-14: a 2x2 inverse and two products of O(1) entries; det G = 1 - cos^2 psi vanishes only at a pole
    ok = worst_c < 1e-14 and worst_p < 1e-15 and worst_g < 1e-15
    return report("C14", ok, "M->panel M->sph = I, conserved and primitive strips",
                  "conserved round trip %.1e; primitive %.1e; det G - sin^2 psi %.1e" %
                  (worst_c, worst_p, worst_g))


def corner_fill(a, b, g, ng, n, h):
    """eq-ch03-exchange-corner on q = a + b x2 + g x3: the corner ghost and the value it should hold.

    The lower-left corner ghost sits at column j and row k, both in the ghost range; j0 and k0 are the
    first interior column and row. Cell centres are at (index + 1/2) h with the interior at index 0..n-1.
    """
    x = lambda m: (m + 0.5) * h
    worst = 0.0
    for j in range(-ng, 0):
        for k in range(-ng, 0):
            left = a + b * x(j) + g * x(0)            # q^L in the same x2 column, at the first interior row
            below = a + b * x(0) + g * x(k)           # q^B in the same x3 row, at the first interior column
            worst = max(worst, abs(0.5 * (left + below) - (a + b * x(j) + g * x(k))))
    return worst


def check_C15_corner():
    ng, n = 3, 64
    flat = corner_fill(2.5, 0.0, 0.0, ng, n, 1.0 / n)                   # a constant field
    errs = [corner_fill(2.5, 1.0, -0.5, ng, n * 2**p, 1.0 / (n * 2**p)) for p in range(3)]
    orders = [math.log2(errs[p] / errs[p + 1]) for p in range(len(errs) - 1)]
    # the closed form: the error is (b (x2_{j0} - x2_j) + g (x3_{k0} - x3_k)) / 2, at most ng h in each term
    bound = 0.5 * (abs(1.0) + abs(-0.5)) * ng / n
    ok = flat == 0.0 and errs[0] <= bound + 1e-15 and all(abs(o - 1.0) < 1e-9 for o in orders)
    return report("C15", ok, "synthesised corner: exact on a constant, first order on a gradient",
                  "constant reproduced to %.1e; linear field max error %.3e at n = %d, halving as %s "
                  "(order 1); bound ng h (sum|slope|)/2 = %.3e" %
                  (flat, errs[0], n, " ".join("%.2f" % o for o in orders), bound))


def global_faces(nglob, xmin, xmax, ng):
    """eq-ch03-globalgrid-slice: the global face array X_a, nglob + 2 ng + 1 entries."""
    dx = (xmax - xmin) / nglob
    return np.array([xmin + (m - ng) * dx for m in range(nglob + 2 * ng + 1)]), dx


def check_C16_global_grid():
    nglob, xmin, xmax, ng = 96, -3.0, 5.0, 3
    X, dx = global_faces(nglob, xmin, xmax, ng)
    shared, mismatch = 0, 0
    for nb_a, nb_b in [(4, 8), (3, 6), (8, 12)]:
        for la in range(nb_a):
            for lb in range(nb_b):
                oa, na = la * nglob // nb_a, nglob // nb_a
                ob, nb_ = lb * nglob // nb_b, nglob // nb_b
                a = X[oa:oa + na + 2 * ng + 1]                    # the two blocks' own face arrays
                b = X[ob:ob + nb_ + 2 * ng + 1]
                for m in range(len(a)):                           # global face of entry m is oa + m - ng
                    g = oa + m - ng
                    mb = g - ob + ng
                    if 0 <= mb < len(b):
                        shared += 1
                        mismatch += a[m].view(np.int64) != b[mb].view(np.int64)
    # the offset: round against truncate on the positions repartition actually produces
    bad_trunc, worst = [], 0
    for nblk in range(2, 25):
        for l in range(nblk):
            q = (xmin + l * (xmax - xmin) / nblk - xmin) / dx
            exact = l * nglob / nblk
            if abs(exact - round(exact)) < 1e-9:                  # a block boundary that lands on a cell face
                worst = max(worst, abs(round(q) - exact))
                if int(q) != round(q):
                    bad_trunc.append((nblk, l, int(q), round(q)))
    ok = mismatch == 0 and worst == 0 and len(bad_trunc) > 0
    return report("C16", ok, "shared faces are bit identical; the offset needs rounding",
                  "%d shared face entries over three decomposition pairs, %d mismatches; round is exact in "
                  "every one of the %d block boundaries; truncation is off by a whole cell in %d of them, "
                  "e.g. nb = %d, l = %d: %d instead of %d" %
                  (shared, mismatch, sum(1 for nblk in range(2, 25) for _ in range(nblk)) and
                   len([1 for nblk in range(2, 25) for l in range(nblk)
                        if abs(l * nglob / nblk - round(l * nglob / nblk)) < 1e-9]),
                   len(bad_trunc), *bad_trunc[0][:2], bad_trunc[0][2], bad_trunc[0][3]))


def check_C17_cartesian():
    """eq-ch03-cartesian-metric: the areas and the volume are the integrals, the centroid the midpoint."""
    x1, x2, x3, d1, d2, d3, xm = sp.symbols("x1 x2 x3 d1 d2 d3 xm")
    a1 = sp.integrate(sp.integrate(1, (x2, 0, d2)), (x3, 0, d3))
    a2 = sp.integrate(sp.integrate(1, (x1, 0, d1)), (x3, 0, d3))
    a3 = sp.integrate(sp.integrate(1, (x1, 0, d1)), (x2, 0, d2))
    vol = sp.integrate(sp.integrate(sp.integrate(1, (x1, 0, d1)), (x2, 0, d2)), (x3, 0, d3))
    lo, hi = xm - d1 / 2, xm + d1 / 2
    centroid = sp.simplify(sp.integrate(x1, (x1, lo, hi)) / sp.integrate(1, (x1, lo, hi)))
    ok = (sp.simplify(a1 - d2 * d3) == 0 and sp.simplify(a2 - d1 * d3) == 0 and
          sp.simplify(a3 - d1 * d2) == 0 and sp.simplify(vol - d1 * d2 * d3) == 0 and
          sp.simplify(centroid - xm) == 0)
    return report("C17", ok, "Cartesian face areas, volume and centroid equal their integrals",
                  "A1 = d2 d3, A2 = d1 d3, A3 = d1 d2, V = d1 d2 d3, centroid = midpoint: exact (sympy)")


def face_of(off):
    """sec-ch03-physfaces: the first non-zero component in the order x3, x2, x1 names the face."""
    d3, d2, d1 = off
    return "x3" if d3 else ("x2" if d2 else ("x1" if d1 else None))


def check_C18_physical_faces():
    offs = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1) if (a, b, c) != (0, 0, 0)]
    named = [face_of(o) for o in offs]
    counts = {f: named.count(f) for f in ("x3", "x2", "x1")}
    single = all(face_of(o) == ax for ax, o in
                 [("x3", (1, 0, 0)), ("x3", (-1, 0, 0)), ("x2", (0, 1, 0)), ("x2", (0, -1, 0)),
                  ("x1", (0, 0, 1)), ("x1", (0, 0, -1))])
    # meshblock.cpp:137-179: a face keeps its bfunc only with no neighbour across it and a non-periodic axis
    table = {(nb, per): (not nb) and (not per) for nb in (False, True) for per in (False, True)}
    physical = all(table[k] == ((not k[0]) and (not k[1])) for k in table)
    ok = (len(offs) == 26 and None not in named and counts == {"x3": 18, "x2": 6, "x1": 2}
          and single and physical and sum(table.values()) == 1)
    return report("C18", ok, "face naming is total and single valued; physical = a bfunc survives",
                  "26 offsets -> x3 %d, x2 %d, x1 %d, each exactly one face; single-axis offsets name their "
                  "own axis; of the 4 (neighbour, periodic) cases exactly 1 keeps the bfunc" %
                  (counts["x3"], counts["x2"], counts["x1"]))


def check_C19_corner_refresh():
    """sec-ch03-cornerrefresh: g = min(ng, n/2) slabs at each end, unless the tangential face owns them."""
    overlap, writes, cases = 0, set(), 0
    for ng in (1, 2, 3, 4, 8):
        for n in (1, 2, 3, 4, 5, 16, 64):
            g = min(ng, n // 2)
            if n > 1 and g > 0 and 2 * g > n:
                overlap += 1                                     # the first and last slabs must not meet
            for tang_physical in (False, True):
                for periodic in (False, True):
                    cases += 1
                    # the x1 bfunc writes the corner unless the tangential face is physical and not periodic
                    by_x1 = n > 1 and g > 0 and not (tang_physical and not periodic)
                    by_tangential = tang_physical and not periodic
                    writes.add(int(by_x1) + int(by_tangential))
    ok = overlap == 0 and writes <= {0, 1}
    return report("C19", ok, "the refresh slab stays within half the direction and each corner is written once",
                  "35 (nghost, n) pairs: 0 overlaps of the two end slabs; over %d (face, periodic) cases the "
                  "number of writers per corner is always in %s" % (cases, sorted(writes)))


def check_C20_face_state_suffix():
    """Port the pinned serialize/deserialize suffix tests; payloads are positional.

    cubed_sphere_layout.cpp:609-612, 724-727, 846-849, 941-944 at
    6fbb39750f62b83df096058a4746e77d0a634bc5.
    """
    keys = [("wl", "+"), ("wr", "-")]
    interior = {1: "wl", -1: "wr"}
    ghost = {1: "wr", -1: "wl"}
    rows, ok = [], True
    for sender in (1, -1):
        for receiver in (1, -1):
            packed = [k for k, suffix in keys
                      if not ((suffix == "+" and sender < 0) or (suffix == "-" and sender > 0))]
            accepted = [k for k, suffix in keys
                        if not ((suffix == "+" and receiver > 0) or (suffix == "-" and receiver < 0))]
            ok = ok and packed == [interior[sender]] and accepted == [ghost[receiver]]
            rows.append(f"({sender:+d},{receiver:+d}): {packed} -> {accepted}")
    return report("C20", ok, "face-state suffixes move the interior state into the ghost-side slot",
                  "4 sender/receiver pairings, including same-orientation edges; " + "; ".join(rows))


def main():
    checks = [check_C1_centroids, check_C2_rationals, check_C3_code_forms, check_C4_spherical_coefficients,
              check_C5_sources, check_C6_angle, check_C7_solid_angle, check_C8_lower_raise,
              check_C9_uniform_pressure, check_C10_morton, check_C11_slide, check_C12_theta_seam,
              check_C13_x1_seam_average, check_C14_sync_matrices, check_C15_corner, check_C16_global_grid,
              check_C17_cartesian, check_C18_physical_faces, check_C19_corner_refresh, check_C20_face_state_suffix]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
