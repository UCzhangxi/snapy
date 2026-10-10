"""Executable check of the reconstruction family (chapter 4, _framework/_dc/_plm/_cp/_weno/_ppm).

Every interpolant below is a numpy port, coefficient for coefficient, of
src/recon/interp_simple.hpp at snapy@e894700ff7aee30b52882e5202b16461413780b0
(interp_cp2 :43-45, interp_plm :57-63, interp_ppm :67-69, interp_cp3 :73-75,
interp_cp4 :79-82, interp_weno3 :94-106, interp_cp5 :110-114, interp_cp6 :118-121,
interp_weno5 :134-153), and of the selection in src/recon/interpolation.cpp:11-39
at the same sha. Claims C1-C7 of the Derivation layers.

Run: python3 recon_check.py   (numpy and sympy; exits with the number of failed claims)
"""
import json
import os
import sys

import numpy as np
import sympy as sp

FAIL = []


def _dump(name, obj):
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write("\n")


def report(tag, ok, what, detail):
    print(f"[{tag}] {'PASS' if ok else 'FAIL'} {what}: {detail}")
    if not ok:
        FAIL.append(tag)


# --- the ports. Each returns the value at the LEFT face of the centre cell. ---
def interp_cp2(a, b):                      # :43-45
    return 0.5 * a + 0.5 * b


def interp_cp3(m1, c, p1):                 # :73-75
    return 1. / 3. * m1 + 5. / 6. * c - 1. / 6. * p1


def interp_cp4(m2, m1, c, p1):             # :79-82
    return -1. / 12. * m2 + 7. / 12. * m1 + 7. / 12. * c - 1. / 12. * p1


def interp_cp5(m2, m1, c, p1, p2):         # :110-114
    return (-1. / 20. * m2 + 9. / 20. * m1 + 47. / 60. * c
            - 13. / 60. * p1 + 1. / 30. * p2)


def interp_cp6(m3, m2, m1, c, p1, p2):     # :118-121
    return (1. / 60. * m3 - 2. / 15. * m2 + 37. / 60. * m1
            + 37. / 60. * c - 2. / 15. * p1 + 1. / 60. * p2)


def interp_plm(m1, c, p1):                 # :57-63
    dwl, dwr = c - m1, p1 - c
    dw2 = dwl * dwr
    dwm = np.where(dw2 > 0., 2. * dw2 / np.where(dwl + dwr == 0., 1., dwl + dwr), 0.)
    return c - 0.5 * dwm


def interp_ppm(m2, m1, c, p1, p2):         # :67-69
    return c


def weno3_parts(m1, c, p1):                # :94-106
    p0 = 0.5 * c + 0.5 * m1
    p1_ = -0.5 * p1 + 1.5 * c
    b0 = (m1 - c) ** 2
    b1 = (c - p1) ** 2
    return (p0, p1_), (b0, b1), (2. / 3., 1. / 3.)


def interp_weno3(m1, c, p1, eps=1e-6):
    (p0, p1_), (b0, b1), (d0, d1) = weno3_parts(m1, c, p1)
    a0, a1 = d0 / (b0 + eps) ** 2, d1 / (b1 + eps) ** 2
    return (a0 * p0 + a1 * p1_) / (a0 + a1)


def weno5_parts(m2, m1, c, p1, p2):        # :134-153
    q0 = (1. / 3.) * c + (5. / 6.) * m1 - (1. / 6.) * m2
    q1 = (-1. / 6.) * p1 + (5. / 6.) * c + (1. / 3.) * m1
    q2 = (1. / 3.) * p2 - (7. / 6.) * p1 + (11. / 6.) * c
    b0 = 13. / 12. * (c - 2. * m1 + m2) ** 2 + .25 * (3. * c - 4. * m1 + m2) ** 2
    b1 = 13. / 12. * (p1 - 2. * c + m1) ** 2 + .25 * (p1 - m1) ** 2
    b2 = 13. / 12. * (p2 - 2. * p1 + c) ** 2 + .25 * (p2 - 4. * p1 + 3. * c) ** 2
    return (q0, q1, q2), (b0, b1, b2), (.3, .6, .1)


def interp_weno5(m2, m1, c, p1, p2, eps=1e-6):
    (q0, q1, q2), (b0, b1, b2), (d0, d1, d2) = weno5_parts(m2, m1, c, p1, p2)
    a0, a1, a2 = d0 / (b0 + eps) ** 2, d1 / (b1 + eps) ** 2, d2 / (b2 + eps) ** 2
    return (a0 * q0 + a1 * q1 + a2 * q2) / (a0 + a1 + a2)


# --- C1: which polynomial degree each linear stencil reproduces at the face ---
def check_C1():
    x = sp.symbols("x")
    h = sp.Integer(1)
    # the face sits at -h/2 from the centre cell; cell k is sampled at k*h
    stencils = {
        "cp2": ([-1, 0], lambda v: sp.Rational(1, 2) * v[0] + sp.Rational(1, 2) * v[1]),
        "cp3": ([-1, 0, 1], lambda v: sp.Rational(1, 3) * v[0] + sp.Rational(5, 6) * v[1]
                - sp.Rational(1, 6) * v[2]),
        "cp4": ([-2, -1, 0, 1], lambda v: -sp.Rational(1, 12) * v[0] + sp.Rational(7, 12) * v[1]
                + sp.Rational(7, 12) * v[2] - sp.Rational(1, 12) * v[3]),
        "cp5": ([-2, -1, 0, 1, 2], lambda v: -sp.Rational(1, 20) * v[0] + sp.Rational(9, 20) * v[1]
                + sp.Rational(47, 60) * v[2] - sp.Rational(13, 60) * v[3]
                + sp.Rational(1, 30) * v[4]),
        "cp6": ([-3, -2, -1, 0, 1, 2], lambda v: sp.Rational(1, 60) * v[0]
                - sp.Rational(2, 15) * v[1] + sp.Rational(37, 60) * v[2]
                + sp.Rational(37, 60) * v[3] - sp.Rational(2, 15) * v[4]
                + sp.Rational(1, 60) * v[5]),
    }
    out = []
    ok = True
    for name, (offs, w) in stencils.items():
        # cell AVERAGES of x^d over cell k, and the point value at the face -h/2
        deg = 0
        while deg < 9:
            avg = [sp.integrate(x ** deg, (x, k * h - h / 2, k * h + h / 2)) / h for k in offs]
            if sp.simplify(w(avg) - (sp.Rational(-1, 2) ** deg)) != 0:
                break
            deg += 1
        order = deg  # exact for degrees 0..deg-1
        expect = {"cp2": 2, "cp3": 3, "cp4": 4, "cp5": 5, "cp6": 6}[name]
        ok &= (order == expect)
        out.append(f"{name} exact to degree {order - 1} (order {order})")
    report("C1", ok, "centred face stencils reproduce cell averages of polynomials "
           "exactly up to their nominal degree", "; ".join(out))


# --- C2/C3: the WENO linear weights rebuild the centred polynomial ---
def check_C2():
    m1, c, p1 = sp.symbols("m1 c p1")
    # the two candidate stencils of interp_weno3, as exact rationals (:96-97)
    q0 = sp.Rational(1, 2) * c + sp.Rational(1, 2) * m1
    q1 = -sp.Rational(1, 2) * p1 + sp.Rational(3, 2) * c
    lin = sp.expand(sp.Rational(2, 3) * q0 + sp.Rational(1, 3) * q1)
    tgt = sp.expand(sp.Rational(1, 3) * m1 + sp.Rational(5, 6) * c - sp.Rational(1, 6) * p1)
    report("C2", sp.simplify(lin - tgt) == 0,
           "weno3 linear weights (2/3, 1/3) rebuild cp3 exactly",
           f"difference {sp.simplify(lin - tgt)}; so weno3 is third order where the field is smooth")


def check_C3():
    m2, m1, c, p1, p2 = sp.symbols("m2 m1 c p1 p2")
    # the three candidate stencils of interp_weno5, as exact rationals (:137-139)
    q0 = sp.Rational(1, 3) * c + sp.Rational(5, 6) * m1 - sp.Rational(1, 6) * m2
    q1 = -sp.Rational(1, 6) * p1 + sp.Rational(5, 6) * c + sp.Rational(1, 3) * m1
    q2 = sp.Rational(1, 3) * p2 - sp.Rational(7, 6) * p1 + sp.Rational(11, 6) * c
    lin = sp.expand(sp.Rational(3, 10) * q0 + sp.Rational(6, 10) * q1 + sp.Rational(1, 10) * q2)
    tgt = sp.expand(-sp.Rational(1, 20) * m2 + sp.Rational(9, 20) * m1
                    + sp.Rational(47, 60) * c - sp.Rational(13, 60) * p1
                    + sp.Rational(1, 30) * p2)
    report("C3", sp.simplify(lin - tgt) == 0,
           "weno5 linear weights (3/10, 6/10, 1/10) rebuild cp5 exactly",
           f"difference {sp.simplify(lin - tgt)}; so weno5 is fifth order where the field is smooth")


# --- C4: measured order on a smooth profile ---
def _face_error(interp, nstencil, f, F, n):
    h = 1. / n
    xc = (np.arange(-4, n + 4) + 0.5) * h
    v = (F(xc + h / 2) - F(xc - h / 2)) / h            # exact cell averages of f
    k = 4
    if nstencil == 3:
        got = interp(v[k - 1:k + n], v[k:k + n + 1], v[k + 1:k + n + 2])
    else:
        got = interp(v[k - 2:k + n - 1], v[k - 1:k + n], v[k:k + n + 1],
                     v[k + 1:k + n + 2], v[k + 2:k + n + 3])
    xf = xc[k:k + n + 1] - h / 2
    return np.max(np.abs(got - f(xf)))


def check_C4():
    """Design order is reached where the field has no critical point; at a critical point
    the Jiang-Shu weights of weno3 fall back to second order. Both are measured."""
    # the monotone ladder stops at 64: by 256 a fifth-order face error on a smooth
    # exponential is at the round-off floor and the fitted slope measures noise
    ns_a = [16, 32, 64]
    ns = [32, 64, 128, 256]
    # (a) monotone, no critical point in [0, 1]
    fa = lambda z: np.exp(1.5 * z)
    Fa = lambda z: np.exp(1.5 * z) / 1.5
    # (b) a full sine: two interior critical points
    fb = lambda z: np.sin(2. * np.pi * z) + 0.3 * np.cos(6. * np.pi * z)
    Fb = lambda z: (-np.cos(2. * np.pi * z) / (2. * np.pi)
                    + 0.3 * np.sin(6. * np.pi * z) / (6. * np.pi))

    def order_of(interp, k, f, F, ladder=None):
        ladder = ladder or ns
        e = [_face_error(interp, 3 if k == 3 else 5, f, F, n) for n in ladder]
        return e, np.polyfit(np.log(ladder[-3:]), np.log(e[-3:]), 1)[0] * -1

    rows, ok = [], True
    for name, interp, k, design in (("cp3", interp_cp3, 3, 3.), ("cp5", interp_cp5, 5, 5.),
                                    ("weno3", interp_weno3, 3, 3.), ("weno5", interp_weno5, 5, 5.)):
        ea, oa = order_of(interp, k, fa, Fa, ns_a)
        ok &= abs(oa - design) < 0.25
        rows.append(f"{name} {oa:.2f}")
    crit = {}
    for name, interp, k in (("weno3", interp_weno3, 3), ("weno5", interp_weno5, 5)):
        eb, ob = order_of(interp, k, fb, Fb)
        crit[name] = ob
    # the linear stencils keep their order through a critical point; weno3 does not
    _, ocp3 = order_of(interp_cp3, 3, fb, Fb)
    ok &= abs(ocp3 - 3.) < 0.25 and crit["weno3"] < 2.6 and crit["weno5"] > 4.5
    _dump("recon_orders.json", {
        "ns_monotone": ns_a, "ns_critical": ns,
        "monotone": {n: list(map(float, order_of(i, k, fa, Fa, ns_a)[0]))
                     for n, i, k in (("cp3", interp_cp3, 3), ("cp5", interp_cp5, 5),
                                     ("weno3", interp_weno3, 3), ("weno5", interp_weno5, 5))},
        "critical": {n: list(map(float, order_of(i, k, fb, Fb)[0]))
                     for n, i, k in (("cp3", interp_cp3, 3), ("cp5", interp_cp5, 5),
                                     ("weno3", interp_weno3, 3), ("weno5", interp_weno5, 5))}})
    report("C4", ok, "measured face order",
           f"no critical point (n = {ns_a[0]}..{ns_a[-1]}): " + ", ".join(rows)
           + f"; through two critical points (n = {ns[0]}..{ns[-1]}) cp3 stays {ocp3:.2f} but weno3 falls to "
             f"{crit['weno3']:.2f} and weno5 keeps {crit['weno5']:.2f}")


# --- C5: the PLM slope is the van Leer harmonic mean ---
def check_C5():
    rng = np.random.default_rng(4)
    m1, c, p1 = rng.normal(size=(3, 20000))
    face = interp_plm(m1, c, p1)
    lo, hi = np.minimum(m1, c), np.maximum(m1, c)
    # TVD: the left face value stays between the two cells it sits between
    tvd = np.all((face >= np.minimum(lo, hi) - 1e-12) & (face <= np.maximum(lo, hi) + 1e-12))
    # at a local extremum the slope is clipped to zero, so the face value is the cell value
    ext = (c - m1) * (p1 - c) <= 0.
    flat = np.max(np.abs(face[ext] - c[ext]))
    # smooth limit: harmonic mean of two nearly equal slopes is their common value
    s = 1e-3
    lin = interp_plm(-s, 0., s)
    report("C5", tvd and flat == 0. and abs(lin + 0.5 * s) < 1e-15,
           "plm uses the van Leer harmonic-mean slope",
           f"TVD on 20000 random triples: {tvd}; slope clipped to zero at every extremum "
           f"(max |face - cell| = {flat:.1e}); on a linear field it returns the centred value exactly")


# --- C6: ppm is a stub ---
def check_C6():
    rng = np.random.default_rng(6)
    v = rng.normal(size=(5, 1000))
    d = np.max(np.abs(interp_ppm(*v) - v[2]))
    report("C6", d == 0.,
           "interp_ppm returns the cell value unchanged, so type ppm is donor cell",
           f"max |interp_ppm - cell| over 1000 random stencils = {d:.1e} (the body is 'return phi')")


# --- C7: donor cell is first order at the face ---
def check_C7():
    f = lambda z: np.sin(2. * np.pi * z)
    F = lambda z: -np.cos(2. * np.pi * z) / (2. * np.pi)
    ns = [32, 64, 128, 256]
    e = []
    for n in ns:
        h = 1. / n
        xc = (np.arange(n + 2) - 0.5) * h
        v = (F(xc + h / 2) - F(xc - h / 2)) / h
        e.append(np.max(np.abs(v[1:n + 1] - f(xc[1:n + 1] - h / 2))))
    order = np.polyfit(np.log(ns[-3:]), np.log(e[-3:]), 1)[0] * -1
    report("C7", abs(order - 1.) < 0.1,
           "donor cell is first order at the face",
           f"{e[0]:.2e} -> {e[-1]:.2e}, order {order:.2f}")


for fn in (check_C1, check_C2, check_C3, check_C4, check_C5, check_C6, check_C7):
    fn()
print(f"{7 - len(FAIL)}/7 claims pass")
sys.exit(len(FAIL))
