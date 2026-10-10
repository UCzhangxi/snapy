#!/usr/bin/env python3
"""Executable check of chapter 5 (hydrostatic and well-balanced treatment), STYLE.md section 7.

What is checked: the closed forms of the Derivation layers of chapter 5, and an independent rebuild of the default
x1 reference. Claims C1-C10 are exact (sympy rationals) or closed forms evaluated numerically; C11-C15 rebuild the
reference from the formulas of the chapter, in numpy, without reading or importing snapy, and compare it with the
analytic column and with the numbers snapy's own test prints; C16-C21 are the spherical-polar, hydrostatic-mode,
grid-classification and Favre-ratio identities.

Formulas mirrored: snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy),
  src/hydro/hydro_ref_x1_impl.h (scan, six-face cell pressure, binomial with the wall continuation, dsf/dref),
  src/hydro/wb_ref4.cpp (F filter, cubic wall values, quartic-primitive face weights),
  src/coord/x1_centroid.cpp (plain-mean conversion, x1 pressure source),
  src/hydro/hydro_forward.cpp (hydrostatic-mode operator), src/hydro/balance_column.cpp (fixed point).
The rebuild is written from the equations of the chapter, not ported line for line, so that agreement with the
C++ test output (C11) is an independent check of the kernel and not of a transcription.

Run: python3 wbref_check.py   (from any directory; numpy and sympy only; a few seconds)
Prints one line per claim, "[Cn] PASS/FAIL <label>: <numbers>", and exits with the number of failures.
"""
import math
import sys

import numpy as np
import sympy as sp

PIN = "e894700ff7aee30b52882e5202b16461413780b0"
x = sp.symbols("x")
RESULTS = []


def report(tag, ok, label, numbers):
    RESULTS.append(bool(ok))
    print(f"[{tag}] {'PASS' if ok else 'FAIL'} {label}: {numbers}", flush=True)
    return bool(ok)


def lagrange_basis(nodes, var):
    out = []
    for j, xj in enumerate(nodes):
        term = sp.Integer(1)
        for m, xm in enumerate(nodes):
            if m != j:
                term *= (var - xm) / (xj - xm)
        out.append(sp.expand(term))
    return out


# ----------------------------------------------------------------------------------------------- exact closed forms

def check_C1_six_face_interior():
    """the interior cell pressure: the cell average of the quintic through six faces, (11,-93,802,802,-93,11)/1440"""
    faces = [sp.Rational(2 * k - 5, 2) for k in range(6)]  # cell i = [-1/2, 1/2]; faces i-5/2 .. i+5/2
    w = [sp.integrate(L, (x, -sp.Rational(1, 2), sp.Rational(1, 2))) for L in lagrange_basis(faces, x)]
    want = [sp.Rational(v, 1440) for v in (11, -93, 802, 802, -93, 11)]
    code = [sp.Rational(11, 1440), -sp.Rational(31, 480), sp.Rational(401, 720)]
    code = code + code[::-1]
    return report("C1", w == want == code, "six-face interior weights",
                  "derived " + ", ".join(map(str, w)) + "; code w6 equal")


def check_C2_six_face_wall_rows():
    """the one-sided rows w6e: cells 0 and 1 above a wall, faces 0..5"""
    faces = [sp.Integer(k) for k in range(6)]
    basis = lagrange_basis(faces, x)
    rows = [[sp.integrate(L, (x, s, s + 1)) for L in basis] for s in (0, 1)]
    code = [[sp.Rational(95, 288), sp.Rational(1427, 1440), -sp.Rational(133, 240), sp.Rational(241, 720),
             -sp.Rational(173, 1440), sp.Rational(3, 160)],
            [-sp.Rational(3, 160), sp.Rational(637, 1440), sp.Rational(511, 720), -sp.Rational(43, 240),
             sp.Rational(77, 1440), -sp.Rational(11, 1440)]]
    sums = [sum(r) for r in rows]
    return report("C2", rows == code and sums == [1, 1], "one-sided six-face wall rows",
                  f"row0 {rows[0]}, row1 {rows[1]}; both sum to 1; code w6e equal")


def moments(weights, offsets, nmax):
    return [sum(w * sp.Integer(m) ** n for w, m in zip(weights, offsets)) for n in range(nmax + 1)]


def check_C3_filters():
    """B = (1,4,6,4,1)/16: moments 1,0,1 (bias h^2/2 q''); F = (-1,4,10,4,-1)/16: 1,0,0,0,-3/2, zero at k dz = pi"""
    off = [-2, -1, 0, 1, 2]
    B = [sp.Rational(v, 16) for v in (1, 4, 6, 4, 1)]
    F = [sp.Rational(v, 16) for v in (-1, 4, 10, 4, -1)]
    mb, mf = moments(B, off, 4), moments(F, off, 4)
    # acting on cell averages of a smooth q: the filtered value is q_bar + (m2/2) h^2 q'' + ...
    resp = [sum(w * sp.cos(sp.pi * m) for w, m in zip(f, off)) for f in (B, F)]
    ok = mb[:3] == [1, 0, 1] and mf == [1, 0, 0, 0, -sp.Rational(3, 2)] and resp == [0, 0]
    return report("C3", ok, "binomial and fourth-order filter moments",
                  f"B moments {mb[:3]}, F moments {mf}, response at k dz = pi: B {resp[0]}, F {resp[1]}")


def check_C4_repeated_wall_cell():
    """with r_j = r0 + j a, repeating r0 past the wall: cell errors 3/8 a, 1/16 a; face errors 23/32, 7/32, 1/32 a"""
    a, r0 = sp.symbols("a r0")
    B = [sp.Rational(v, 16) for v in (1, 4, 6, 4, 1)]
    true = lambda j: r0 + j * a                       # noqa: E731
    rep = lambda j: true(max(j, 0))                   # noqa: E731
    rs = lambda i: sum(B[m + 2] * rep(i + m) for m in range(-2, 3))   # noqa: E731
    cell = [sp.simplify(rs(i) - true(i)) for i in (0, 1)]
    face = [sp.simplify(sp.Rational(1, 2) * (rs(f - 1) + rs(f)) - (r0 + (f - sp.Rational(1, 2)) * a))
            for f in (0, 1, 2, 3)]
    ok = cell == [3 * a / 8, a / 16] and face == [23 * a / 32, 7 * a / 32, a / 32, 0]
    return report("C4", ok, "repeated wall cell is first order", f"cells 0,1: {cell}; faces 0..3: {face}")


def wall_rop(r0, r1, k):
    """the wall continuation of rho/p, k cells past the wall (chapter equation, hydro_ref_x1_wall_rop)"""
    e = r0 * (r0 / r1) ** k if r1 > r0 else r0 + k * (r0 - r1)
    return e if e > 0 else r0


def check_C5_continuation_is_linear():
    """the linear branch makes the binomial exact for linear r at faces 0..2; the ln branch differs by O(a^2)"""
    a, r0 = sp.symbols("a r0", positive=True)
    B = [sp.Rational(v, 16) for v in (1, 4, 6, 4, 1)]
    true = lambda j: r0 + j * a                       # noqa: E731
    lin = lambda j: true(j) if j >= 0 else r0 + (-j) * (r0 - true(1))   # noqa: E731
    lnb = lambda j: true(j) if j >= 0 else r0 * (r0 / true(1)) ** (-j)  # noqa: E731
    out = []
    for cont in (lin, lnb):
        rs = lambda i: sum(B[m + 2] * cont(i + m) for m in range(-2, 3))   # noqa: E731
        out.append([sp.series(sp.Rational(1, 2) * (rs(f - 1) + rs(f)) - (r0 + (f - sp.Rational(1, 2)) * a),
                              a, 0, 3).removeO() for f in (0, 1, 2)])
    ok = out[0] == [0, 0, 0] and all(sp.Poly(e, a).monoms()[-1][0] >= 2 for e in out[1] if e != 0)
    return report("C5", ok, "wall continuation restores O(dz^2) at faces 0-2",
                  f"linear branch errors {out[0]}; ln branch errors {[sp.factor(e) for e in out[1]]}")


def check_C6_continuation_bounds():
    """the continuation lies in [r0 (r0/r1)^k, r0 (1+k)] and is positive, for r1 >= 0 (random sample)"""
    rng = np.random.default_rng(5)
    bad, n = 0, 0
    for r0, r1 in zip(rng.uniform(1e-6, 10, 20000), np.r_[rng.uniform(0, 20, 19990), np.zeros(10)]):
        for k in (1, 2, 3):
            e = wall_rop(r0, r1, k) if r1 > 0 else r0 + k * r0
            lo = r0 * (r0 / r1) ** k if r1 > 0 else 0.0
            n += 1
            bad += not (e > 0 and min(lo, r0) * (1 - 1e-12) <= e <= r0 * (1 + k) * (1 + 1e-12))
    return report("C6", bad == 0, "wall continuation bounds", f"{n} samples, {bad} outside the bounds")


def check_C7_cubic_wall_values():
    """E rows (4,-6,4,-1), (10,-20,15,-4) extrapolate a cubic; then (F r) equals r in the two end cells"""
    nodes = [sp.Integer(k) for k in range(4)]
    basis = lagrange_basis(nodes, x)
    rows = [[L.subs(x, -k) for L in basis] for k in (1, 2)]
    r = sp.symbols("r0:6")
    F = [sp.Rational(v, 16) for v in (-1, 4, 10, 4, -1)]
    ext = {-1: sum(c * r[q] for c, q in zip(rows[0], range(4))), -2: sum(c * r[q] for c, q in zip(rows[1], range(4)))}
    val = lambda j: ext[j] if j < 0 else r[j]   # noqa: E731
    ends = [sp.simplify(sum(F[m + 2] * val(i + m) for m in range(-2, 3)) - r[i]) for i in (0, 1)]
    ok = rows == [[4, -6, 4, -1], [10, -20, 15, -4]] and ends == [0, 0]
    return report("C7", ok, "cubic wall values and the end-cell identity", f"E rows {rows}; (F r)_i - r_i = {ends}")


def check_C8_quartic_primitive_faces():
    """face value of a cell field from the quartic primitive: (-1,7,7,-1)/12, wall (25,-23,13,-3)/12, (3,13,-5,1)/12"""
    nodes = [sp.Integer(k) for k in range(5)]
    dL = [sp.diff(L, x) for L in lagrange_basis(nodes, x)]

    def weights(xf):
        return [sum(dL[j].subs(x, xf) for j in range(k + 1, 5)) for k in range(4)]
    got = [weights(2), weights(0), weights(1)]
    want = [[sp.Rational(v, 12) for v in row] for row in ((-1, 7, 7, -1), (25, -23, 13, -3), (3, 13, -5, 1))]
    return report("C8", got == want, "quartic-primitive face weights", f"interior, wall, next: {got}")


def check_C9_log_mean():
    """the non-uniform cell pressure dp/ln(lo/hi): exact for an isothermal cell, O(dz^2) for a polytrope"""
    g, z0 = 1.0, 0.3
    errs = {}
    for name, p in (("isothermal", lambda z: np.exp(-z)), ("polytrope", lambda z: (1 - 0.5 * z) ** 2)):
        rho = (lambda z: np.exp(-z)) if name == "isothermal" else (lambda z: (1 - 0.5 * z))
        e = []
        for dz in (0.1, 0.05, 0.025):
            gx, gw = np.polynomial.legendre.leggauss(8)
            zz = z0 + 0.5 * dz * (gx + 1)
            pbar, rbar = 0.5 * np.dot(gw, p(zz)), 0.5 * np.dot(gw, rho(zz))
            lo, hi = p(z0), p(z0 + dz)
            dp = g * rbar * dz
            e.append(abs(dp / math.log(lo / hi) - pbar) / pbar)
        errs[name] = e
    order = math.log2(errs["polytrope"][1] / errs["polytrope"][2])
    ok = max(errs["isothermal"]) < 1e-14 and 1.8 < order < 2.2
    return report("C9", ok, "log-mean cell pressure",
                  f"isothermal max rel error {max(errs['isothermal']):.1e}; polytrope rel errors "
                  + " / ".join(f"{v:.3e}" for v in errs["polytrope"]) + f" (dz 0.1/0.05/0.025), order {order:.2f}")


def check_C10_top_anchor():
    """the top anchor p_top exp(-g dz/2 / (p/rho)_top) from cell averages: relative offset sinh(a)/a - 1 ~ a^2/6"""
    out, ok = [], True
    for a in (0.05, 0.025, 0.0125):   # a = dz / (2H), isothermal column, H = 1
        dz = 2 * a
        zc = 1.0
        pbar = math.exp(-zc) * math.sinh(a) / a       # cell average of exp(-z) over [zc - a, zc + a]
        rbar = pbar                                    # rho = p for R T = 1
        anchor = pbar * math.exp(-0.5 * dz / (pbar / rbar))
        exact = math.exp(-(zc + a))
        rel = anchor / exact - 1
        ok &= abs(rel - (math.sinh(a) / a - 1)) < 1e-15 and abs(rel / (a * a / 6) - 1) < 2 * a * a
        out.append(f"a {a}: {rel:.4e} (a^2/6 = {a * a / 6:.4e})")
    return report("C10", ok, "top anchor offset is a column constant of relative size (dz/2H)^2/6", "; ".join(out))


# ------------------------------------------------------------------ independent rebuild of the default x1 reference

NG = 3
W6 = np.array([11, -93, 802, 802, -93, 11]) / 1440.0
W6E = np.array([[95 / 288, 1427 / 1440, -133 / 240, 241 / 720, -173 / 1440, 3 / 160],
                [-3 / 160, 637 / 1440, 511 / 720, -43 / 240, 77 / 1440, -11 / 1440]])
BIN = np.array([1, 4, 6, 4, 1]) / 16.0
FIL = np.array([-1, 4, 10, 4, -1]) / 16.0


class Polytrope:
    """T = 1 - beta z, g = R = 1, one pressure scale height deep (the column of tests/test_wb_ref_wall.cpp)"""

    def __init__(self, beta):
        self.beta = beta
        self.depth = 1.0 if beta == 0 else (1 - math.exp(-beta)) / beta

    def p(self, z):
        return np.exp(-z) if self.beta == 0 else (1 - self.beta * z) ** (1 / self.beta)

    def rho(self, z):
        return self.p(z) / (1 - self.beta * z)


def cell_averages(f, zf, npt=8):
    gx, gw = np.polynomial.legendre.leggauss(npt)
    zc, h = 0.5 * (zf[1:] + zf[:-1]), 0.5 * (zf[1:] - zf[:-1])
    return 0.5 * sum(w * f(zc + s * h) for s, w in zip(gx, gw))


def column(prof, nz):
    """exact cell averages on nz owned cells plus NG even-mirrored ghosts each side"""
    dz = prof.depth / nz
    zf = np.arange(nz + 1) * dz
    rho, p = cell_averages(prof.rho, zf), cell_averages(prof.p, zf)
    pad = lambda q: np.r_[q[:NG][::-1], q, q[-NG:][::-1]]   # noqa: E731
    return dz, pad(rho), pad(p)


def scan(rho, p, dz, g=1.0):
    """face pressures: psf[f] at the lower face of cell f, f = 0..nc1; top anchor from the top owned cell"""
    nc1 = len(rho)
    iu = nc1 - 1 - NG
    psf = np.empty(nc1 + 1)
    psf[iu + 1] = p[iu] * math.exp(-g * 0.5 * dz / (p[iu] / rho[iu]))
    for i in range(iu, -1, -1):
        psf[i] = psf[i + 1] + g * rho[i] * dz
    for i in range(iu + 1, nc1):
        psf[i + 1] = psf[i] - g * rho[i] * dz
    return psf


def smoothed_ratio(rho, p, extend=True):
    """r^s_i = B r over cells i-2..i+2; past each wall the continuation (or the wall cell repeated)"""
    nc1, il = len(rho), NG
    iu = nc1 - 1 - NG
    r = rho / p

    def val(j):
        if j < il:
            return wall_rop(r[il], r[il + 1], il - j) if extend else r[il]
        if j > iu:
            return wall_rop(r[iu], r[iu - 1], j - iu) if extend else r[iu]
        return r[j]
    return np.array([sum(BIN[m + 2] * val(i + m) for m in range(-2, 3)) for i in range(nc1)])


def face_density_ref(rho, p, dz, extend=True, dz_grid=None):
    """dsf at faces il..iu+1: psf times the mean of the two neighbouring smoothed ratios; dz_grid is the width the
    scan uses, when it differs from the width the cell averages were taken over"""
    psf = scan(rho, p, dz if dz_grid is None else dz_grid)
    rs = smoothed_ratio(rho, p, extend)
    il, iu = NG, len(rho) - 1 - NG
    return np.array([psf[f] * 0.5 * (rs[f - 1] + rs[f]) for f in range(il, iu + 2)])


def cell_pressure_ref(rho, p, dz):
    """pref on owned cells: six-face interior rows, one-sided rows in the two cells at each (clamped) wall"""
    psf = scan(rho, p, dz)
    il, iu = NG, len(rho) - 1 - NG
    out = []
    for i in range(il, iu + 1):
        if i - il < 2:
            v = W6E[i - il] @ psf[il:il + 6]
        elif iu - i < 2:
            v = W6E[iu - i][::-1] @ psf[iu - 4:iu + 2]
        else:
            v = W6 @ psf[i - 2:i + 4]
        lo, hi = sorted((psf[i], psf[i + 1]))
        out.append(v if lo <= v <= hi else 0.5 * (psf[i] + psf[i + 1]))
    return np.array(out), psf


def check_C11_reproduces_the_cpp_table():
    """the rebuilt dsf errors equal the order table tests/test_wb_ref_wall.cpp prints at the pin (beta 0.5 and 0)"""
    # printed by ctest test_wb_ref_wall.release, CPU, double, snapy@e894700ff7aee30b52882e5202b16461413780b0 (WbRefWall.order_table):
    # nz: face1 dsf, face2 dsf, top1 dsf, top2 dsf, interior max dsf (>= 3 faces from each wall)
    cpp = {0.5: {16: (8.040e-04, 9.827e-04, 1.457e-03, 2.003e-03, 1.958e-03),
                 32: (1.950e-04, 2.335e-04, 3.864e-04, 5.427e-04, 5.471e-04),
                 64: (4.821e-05, 5.714e-05, 9.960e-05, 1.415e-04, 1.450e-04),
                 128: (1.215e-05, 1.430e-05, 2.529e-05, 3.614e-05, 3.738e-05)},
           0.0: {16: (6.374e-05, 6.785e-05, 1.529e-04, 1.436e-04, 1.349e-04),
                 32: (1.544e-05, 1.593e-05, 3.944e-05, 3.823e-05, 3.705e-05),
                 64: (3.801e-06, 3.861e-06, 1.001e-05, 9.860e-06, 9.707e-06),
                 128: (9.429e-07, 9.503e-07, 2.523e-06, 2.504e-06, 2.484e-06)}}
    # The test averages its cells over depth/nz but writes x1max into the block's YAML with the stream's default six
    # significant digits, so the block's dx1f, which the scan uses, is (0.786939 - depth)/depth = 4.1e-7 wider at
    # beta 0.5 (exact at beta 0, depth 1). The rebuild uses the same two widths; with one consistent width the
    # bottom-wall faces move by up to 2.5e-7 in relative error (printed as "consistent grid").
    worst, rows, shift = 0.0, [], 0.0
    for beta, table in cpp.items():
        prof = Polytrope(beta)
        for nz, want in table.items():
            dz, rho, p = column(prof, nz)
            dz_grid = float(f"{prof.depth:g}") / nz
            exact = prof.rho(np.arange(nz + 1) * dz)
            e = face_density_ref(rho, p, dz, dz_grid=dz_grid) / exact - 1
            e_cons = face_density_ref(rho, p, dz) / exact - 1
            shift = max(shift, np.abs(e - e_cons)[:3].max())
            nf = len(e)
            got = (e[1], e[2], e[nf - 2], e[nf - 3], np.abs(e[3:nf - 3]).max())
            worst = max(worst, max(abs(abs(a) / b - 1) for a, b in zip(got, want)))
            if nz == 64:
                rows.append(f"beta {beta:g} nz 64 face1 {got[0]:+.3e} top1 {got[2]:+.3e} interior {got[4]:.3e}")
    # the C++ prints 4 significant digits, so agreement is to half a unit in the 4th digit, 5e-4 relative at worst
    return report("C11", worst < 6e-4, "independent rebuild reproduces test_wb_ref_wall's table",
                  f"worst relative difference {worst:.1e} over 40 printed numbers; " + "; ".join(rows)
                  + f"; consistent grid moves faces 0-2 by at most {shift:.1e}")


def fitted_order(errs, nzs):
    return np.polyfit(np.log(nzs), np.log(errs), 1)[0] * -1


def check_C12_wall_orders():
    """face 1 dsf error: about first order with the repeated wall cell, second order with the continuation"""
    prof, nzs = Polytrope(0.5), (32, 64, 128, 256)
    e_rep, e_ext = [], []
    for nz in nzs:
        dz, rho, p = column(prof, nz)
        exact = prof.rho(np.arange(nz + 1) * dz)
        e_rep.append(abs(face_density_ref(rho, p, dz, extend=False)[1] / exact[1] - 1))
        e_ext.append(abs(face_density_ref(rho, p, dz, extend=True)[1] / exact[1] - 1))
    o_rep, o_ext = fitted_order(e_rep, nzs), fitted_order(e_ext, nzs)
    ok = 0.9 < o_rep < 1.2 and 1.9 < o_ext < 2.1
    return report("C12", ok, "face-1 dsf order, repeated wall cell vs continuation (beta 0.5)",
                  "repeated " + " / ".join(f"{v:.3e}" for v in e_rep) + f" order {o_rep:.2f}; continued "
                  + " / ".join(f"{v:.3e}" for v in e_ext) + f" order {o_ext:.2f} (nz 32/64/128/256)")


def check_C13_six_face_cell_pressure():
    """pref - p_bar is one column constant c plus O(dz^6) in the interior; the scan faces are exact up to c"""
    prof, nzs = Polytrope(0.0), (8, 16, 32)          # isothermal: p is not a polynomial
    res, face_dev = [], []
    for nz in nzs:
        dz, rho, p = column(prof, nz)
        pref, psf = cell_pressure_ref(rho, p, dz)
        exact_faces = prof.p(np.arange(nz + 1) * dz)
        dev = psf[NG:NG + nz + 1] - exact_faces
        face_dev.append(np.ptp(dev) / exact_faces.max())
        d = pref - p[NG:NG + nz] - dev[0]
        res.append(np.abs(d[2:-2]).max() / p.max())
    order = fitted_order(res, nzs)
    ok = max(face_dev) < 1e-13 and order > 5.5
    return report("C13", ok, "scan faces exact up to a constant; six-face pref order",
                  f"isothermal, spread of (psf - p(z_f)) {max(face_dev):.1e} of p; interior |pref - p_bar - c| "
                  + " / ".join(f"{v:.3e}" for v in res) + f" (nz 8/16/32), order {order:.2f}")


def weno5_linear(q, f):
    """the left state at face f (lower face of cell f) of fifth-order linear (smooth-data) WENO5"""
    i = f - 1
    return (2 * q[i - 2] - 13 * q[i - 1] + 47 * q[i] + 27 * q[i + 1] - 3 * q[i + 2]) / 60.0


def ref4_cells_and_faces(rho, p, dz):
    """SNAP_WB_REF4 on a uniform column with two clamped walls: dref = pref F(r), dsf = quartic-primitive face value"""
    pref, psf = cell_pressure_ref(rho, p, dz)
    il, iu = NG, len(rho) - 1 - NG
    r = (rho / p)[il:iu + 1]
    n = len(r)
    E = np.array([[4, -6, 4, -1], [10, -20, 15, -4]], float)

    def val(j):
        if j < 0:
            return E[-j - 1] @ r[0:4]
        if j > n - 1:
            return E[j - n] @ r[n - 1:n - 5:-1]
        return r[j]
    fr = np.array([sum(FIL[m + 2] * val(i + m) for m in range(-2, 3)) for i in range(n)])
    dref = pref * fr
    wint, wwall, wnext = (np.array(v) / 12.0 for v in ((-1, 7, 7, -1), (25, -23, 13, -3), (3, 13, -5, 1)))
    faces = []
    for f in range(n + 1):
        if f == 0:
            faces.append(wwall @ dref[0:4])
        elif f == 1:
            faces.append(wnext @ dref[0:4])
        elif f == n:
            faces.append(wwall @ dref[n - 1:n - 5:-1])
        elif f == n - 1:
            faces.append(wnext @ dref[n - 1:n - 5:-1])
        else:
            faces.append(wint @ dref[f - 2:f + 2])
    return pref, dref, np.array(faces)


def check_C14_face_offset_formula():
    """base: delta rho_f = rho_sf - I[rho_ref]_f = dz^2/12 (p' R' + 2 p R'') + O(dz^4); SNAP_WB_REF4: O(dz^4)"""
    prof, nzs = Polytrope(0.5), (32, 64, 128, 256)
    ratio, base, ref4 = [], [], []
    for nz in nzs:
        dz, rho, p = column(prof, nz)
        il, iu = NG, NG + nz - 1
        pref, _ = cell_pressure_ref(rho, p, dz)
        rs = smoothed_ratio(rho, p)
        dref = pref * rs[il:iu + 1]
        dsf = face_density_ref(rho, p, dz)
        f_mid = nz // 2                              # a face in the middle of the column
        dref_pad = np.r_[np.zeros(NG), dref, np.zeros(NG)]
        delta = dsf[f_mid] - weno5_linear(dref_pad, il + f_mid)
        z = f_mid * dz
        h = 1e-4
        R = lambda zz: prof.rho(zz) / prof.p(zz)   # noqa: E731
        dp = (prof.p(z + h) - prof.p(z - h)) / (2 * h)
        dR = (R(z + h) - R(z - h)) / (2 * h)
        d2R = (R(z + h) - 2 * R(z) + R(z - h)) / h ** 2
        ratio.append(delta / (dz * dz / 12 * (dp * dR + 2 * prof.p(z) * d2R)))
        base.append(abs(delta) / prof.rho(z))
        _, dref4, dsf4 = ref4_cells_and_faces(rho, p, dz)
        dref4_pad = np.r_[np.zeros(NG), dref4, np.zeros(NG)]
        ref4.append(abs(dsf4[f_mid] - weno5_linear(dref4_pad, il + f_mid)) / prof.rho(z))
    o_base, o_ref4 = fitted_order(base, nzs), fitted_order(ref4, nzs)
    ok = abs(ratio[-1] - 1) < 0.02 and 1.9 < o_base < 2.1 and o_ref4 > 3.8
    return report("C14", ok, "mid-column face-density offset, base vs SNAP_WB_REF4 (beta 0.5)",
                  "base/formula " + " / ".join(f"{v:.4f}" for v in ratio) + f"; base order {o_base:.2f}; "
                  "ref4 " + " / ".join(f"{v:.2e}" for v in ref4) + f" order {o_ref4:.2f} (nz 32/64/128/256)")


def check_C15_balance_fixed_point():
    """balance_column's iteration p <- pref(p) + C, rho <- p/(p/rho)_0 converges on a marched column"""
    prof, nz = Polytrope(0.3), 64                    # neither polynomial nor exponential: not balanced as given
    dz = prof.depth / nz
    zc = (np.arange(nz) + 0.5) * dz
    # point values at the centres would already sit at the fixed point to O(dz^4); a smooth 1e-3 pressure bump at
    # fixed p/rho is a column that is not balanced and has to be projected
    rho, p = prof.rho(zc), prof.p(zc)
    bump = 1 + 1e-3 * np.sin(np.pi * zc / prof.depth)
    rho, p = rho * bump, p * bump
    rt = p / rho

    def residual_and_update(rho, p):
        rp, pp = np.r_[rho[:NG][::-1], rho, rho[-NG:][::-1]], np.r_[p[:NG][::-1], p, p[-NG:][::-1]]
        pref, _ = cell_pressure_ref(rp, pp, dz)
        dev = p - pref
        c = dev[-1]
        return np.max(np.abs(dev - c) / (rho * dz)), pref + c
    first, sweeps = None, 0
    for sweeps in range(121):
        err, pnew = residual_and_update(rho, p)
        first = err if first is None else first
        if err < 1e-10:
            break
        p, rho = pnew, pnew / rt
    drift = np.abs(p / rho - rt).max() / rt.min()
    return report("C15", err < 1e-10 and sweeps > 0 and drift < 1e-14,
                  "independent balance_column fixed point (beta 0.3, nz 64, 1e-3 bump)",
                  f"residual {first:.3e} -> {err:.3e} after {sweeps} updates; max relative change of p/rho {drift:.1e}")


# --------------------------------------------------------------------------------- spherical-polar x1 identities

def check_C16_plain_mean_conversion():
    """the five-cell r^2-mean -> plain-mean conversion is exact to degree 4 and not 5; weights sum to 1"""
    gx, gw = np.polynomial.legendre.leggauss(4)
    rf = 5.0 + np.cumsum(np.r_[0.0, 0.1 * (1 + 0.3 * np.sin(np.arange(9)))])   # a stretched radial grid
    worst4, deg5, sums = 0.0, 0.0, []
    for i, s in ((4, 2), (0, 0), (1, 0), (8, 4)):      # interior, two bottom-wall windows, a top-wall window
        c, h = 0.5 * (rf[i] + rf[i + 1]), rf[i + 1] - rf[i]
        M = np.zeros((5, 5))
        for k in range(5):
            a, b = rf[s + k], rf[s + k + 1]
            r = 0.5 * (a + b) + 0.5 * (b - a) * gx
            wq = gw * r * r
            for n in range(5):
                M[n, k] = (wq * ((r - c) / h) ** n).sum() / wq.sum()
        wts = np.linalg.solve(M, [1, 0, 1 / 12, 0, 1 / 80])
        sums.append(wts.sum())
        for n in range(6):
            r2mean = []
            for k in range(5):
                a, b = rf[s + k], rf[s + k + 1]
                r = 0.5 * (a + b) + 0.5 * (b - a) * gx
                r2mean.append((gw * r * r * ((r - c) / h) ** n).sum() / (gw * r * r).sum())
            exact = ((0.5) ** (n + 1) - (-0.5) ** (n + 1)) / (n + 1)
            err = abs(np.dot(wts, r2mean) - exact)
            if n < 5:
                worst4 = max(worst4, err)
            else:
                deg5 = max(deg5, err)
    ok = worst4 < 1e-12 and deg5 > 1e-8 and max(abs(np.array(sums) - 1)) < 1e-12
    return report("C16", ok, "plain-mean conversion exactness",
                  f"max error degree <= 4: {worst4:.1e}; degree 5: {deg5:.1e}; |sum - 1| <= "
                  f"{max(abs(np.array(sums) - 1)):.1e}")


def check_C17_pressure_source():
    """S_i = (2/V) int r p~ dr: constant p gives S V = A+ - A-; the net force is the r^2 mean of -dp~/dr"""
    r = sp.symbols("r")
    faces = [sp.Rational(50, 10) + sp.Rational(k, 10) for k in range(6)]
    basis = lagrange_basis(faces, r)
    i0, i1 = faces[2], faces[3]              # the cell between faces 2 and 3 (centred window)
    V = (i1 ** 3 - i0 ** 3) / 3
    w = [2 / V * sp.integrate(r * L, (r, i0, i1)) for L in basis]
    const_ok = sp.simplify(sum(w) * V - (i1 ** 2 - i0 ** 2)) == 0
    pv = [sp.Rational(k * k + 3, 7) for k in range(6)]                 # arbitrary face pressures
    pt = sum(c * L for c, L in zip(pv, basis))
    lhs = -(i1 ** 2 * pt.subs(r, i1) - i0 ** 2 * pt.subs(r, i0)) / V + sum(c * wj for c, wj in zip(pv, w))
    rhs = -sp.integrate(r ** 2 * sp.diff(pt, r), (r, i0, i1)) / V
    parts_ok = sp.simplify(lhs - rhs) == 0
    return report("C17", const_ok and parts_ok, "x1 pressure source identities (exact rationals)",
                  f"constant p: S V - (A+ - A-) = 0 is {const_ok}; by parts: net force = r^2 mean of -dp~/dr "
                  f"is {parts_ok}")


def check_C18_centroid_defect():
    """the r^2 centroid sits delta = h^2/(6 r_bar) + O(h^4/r^3) above the mid-radius"""
    rb, h = sp.symbols("rb h", positive=True)
    r = sp.symbols("r")
    num = sp.integrate(r ** 2 * (r - rb), (r, rb - h / 2, rb + h / 2))
    den = sp.integrate(r ** 2, (r, rb - h / 2, rb + h / 2))
    delta = sp.simplify(num / den)
    lead = sp.simplify(sp.series(delta, h, 0, 6).removeO())
    ok = sp.simplify(lead - (h ** 2 / (6 * rb) - h ** 4 / (72 * rb ** 3))) == 0
    return report("C18", ok, "centroid offset of an r^2 cell", f"delta = {sp.factor(delta)}; series {lead}")


def check_C19_hydrostatic_mode_cancels_at_rest():
    """at rest (pL = pR = p*) the hydrostatic correction cancels the pressure force, plain and r^2 forms"""
    rng = np.random.default_rng(19)
    pstar = rng.uniform(1, 2, 8)
    r = np.linspace(5.0, 5.7, 8)
    dz = np.diff(r)
    plain_force = -(pstar[1:] - pstar[:-1]) / dz
    plain_corr = (pstar[1:] - pstar[:-1]) / dz
    A, V = r ** 2, (r[1:] ** 3 - r[:-1] ** 3) / 3
    S = rng.uniform(0, 1, 7)                       # any source: it appears with opposite signs in the two
    sph_force = -(A[1:] * pstar[1:] - A[:-1] * pstar[:-1]) / V + S
    sph_corr = (A[1:] * pstar[1:] - A[:-1] * pstar[:-1]) / V - S
    worst = max(np.abs(plain_force + plain_corr).max(), np.abs(sph_force + sph_corr).max())
    return report("C19", worst < 1e-12, "hydrostatic-mode correction cancels the pressure force at rest",
                  f"max |force + correction| {worst:.1e} (non-hydrostatic 0)")


def check_C20_uniform_test():
    """the uniform-grid test: relative spread of dx1f below 1e-10 of the mean selects the six-face rows"""
    d = np.full(64, 0.0123)
    d_round = d * (1 + 1e-12 * np.sin(np.arange(64)))
    d_str = d * (1 + 1e-6 * np.arange(64))
    uni = lambda a: np.ptp(a) < 1e-10 * a.mean()   # noqa: E731
    ok = uni(d) and uni(d_round) and not uni(d_str)
    return report("C20", ok, "uniform-grid classification", f"round-off spread uniform: {uni(d_round)}; "
                  f"1e-6 stretching uniform: {uni(d_str)}")


def check_C21_favre_ratio():
    """<rho w>/<rho> - w_bar = h^2/12 rho' w'/rho + delta w' + O(h^3) for linear rho, w with the r^2 weight"""
    rb, h, r0, r1, w0, w1, xx = sp.symbols("rb h r0 r1 w0 w1 xx")
    wgt = (rb + xx) ** 2
    rho, w = r0 + r1 * xx, w0 + w1 * xx
    lim = (xx, -h / 2, h / 2)
    favre = sp.integrate(wgt * rho * w, lim) / sp.integrate(wgt * rho, lim)
    plain = sp.integrate(w, lim) / h
    diff = sp.series(sp.simplify(favre - plain), h, 0, 3).removeO()
    want = h ** 2 / 12 * r1 * w1 / r0 + h ** 2 / (6 * rb) * w1
    ok = sp.simplify(sp.expand(diff - want)) == 0
    return report("C21", ok, "Favre ratio of r^2 means against the plain mean (linear profiles)",
                  f"difference to O(h^2): {sp.factor(diff)}")


def main():
    print(f"chapter 5 check, formulas of snapy@{PIN} (chengcli/snapy)")
    print(f"numpy {np.__version__}, sympy {sp.__version__}")
    for fn in (check_C1_six_face_interior, check_C2_six_face_wall_rows, check_C3_filters,
               check_C4_repeated_wall_cell, check_C5_continuation_is_linear, check_C6_continuation_bounds,
               check_C7_cubic_wall_values, check_C8_quartic_primitive_faces, check_C9_log_mean,
               check_C10_top_anchor, check_C11_reproduces_the_cpp_table, check_C12_wall_orders,
               check_C13_six_face_cell_pressure, check_C14_face_offset_formula, check_C15_balance_fixed_point,
               check_C16_plain_mean_conversion, check_C17_pressure_source, check_C18_centroid_defect,
               check_C19_hydrostatic_mode_cancels_at_rest, check_C20_uniform_test, check_C21_favre_ratio):
        fn()
    fails = RESULTS.count(False)
    print(f"{len(RESULTS) - fails} passed, {fails} failed")
    return fails


if __name__ == "__main__":
    sys.exit(main())
