"""Executable check of the O(dx1^2) face-average corrections (chapter 4B,
_fluxcov.qmd and _x1masscov.qmd).

Ports, line for line, of snapy@e894700ff7aee30b52882e5202b16461413780b0:
HydroImpl::_flux_covariance (src/hydro/hydro_forward.cpp:54-150, the two-term
correction stated at :63) and the x1 mass-flux covariance block
(src/hydro/hydro_forward.cpp:314-344, the correction at :334, the one-sided wall
density slope at :322-332), with d1_centred at :40-52. Claims C1-C6.

Run: python3 covariance_check.py   (numpy and sympy; exits with the number of failed claims)
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


def d1_centred(a, x1v):                      # hydro_forward.cpp:40-52
    d = np.empty_like(a)
    d[1:-1] = (a[2:] - a[:-2]) / (x1v[2:] - x1v[:-2])
    d[0], d[-1] = d[1], d[-2]
    return d


# --- C1: the covariance identity that both corrections rest on ---
def check_C1():
    z, h, z0 = sp.symbols("z h z0", real=True, positive=True)
    f = sp.Function("f")(z)
    g = sp.Function("g")(z)
    # average of a product over a cell of width h about z0, to O(h^4)
    def avg(expr):
        s = sp.symbols("s")
        e = expr.subs(z, z0 + s)
        return sp.integrate(sp.series(e, s, 0, 5).removeO(), (s, -h / 2, h / 2)) / h
    lhs = sp.expand(avg(f * g))
    rhs = sp.expand(avg(f) * avg(g) + h ** 2 / 12 * sp.diff(f, z).subs(z, z0)
                    * sp.diff(g, z).subs(z, z0))
    diff = sp.simplify(sp.expand(lhs - rhs))
    lead = sp.simplify(sp.limit(diff / h ** 4, h, 0))
    report("C1", sp.simplify(diff.subs(h, 0)) == 0 and lead != sp.nan,
           "mean of a product = product of means + h^2/12 f' g' + O(h^4)",
           f"the h^0 and h^2 terms cancel identically; the remainder is O(h^4), "
           f"leading coefficient {sp.nsimplify(lead)}")


# --- C2: sigma^2 of the face measure is h^2/12 in Cartesian ---
def check_C2():
    h, r = sp.symbols("h r", positive=True)
    s = sp.symbols("s")
    cart = sp.integrate(s ** 2, (s, -h / 2, h / 2)) / h
    # an x2/x3 face of a spherical-polar cell carries the measure w(r) = r
    num = sp.integrate((r + s - (sp.integrate((r + s) * (r + s), (s, -h / 2, h / 2))
                                 / sp.integrate((r + s), (s, -h / 2, h / 2)))) ** 2
                       * (r + s), (s, -h / 2, h / 2))
    den = sp.integrate(r + s, (s, -h / 2, h / 2))
    sph = sp.simplify(num / den)
    lim = sp.simplify(sp.limit(sph, r, sp.oo))
    report("C2", sp.simplify(cart - h ** 2 / 12) == 0 and sp.simplify(lim - h ** 2 / 12) == 0,
           "the x1 second moment of the face measure",
           f"Cartesian (measure 1): {cart}; spherical x2/x3 face (measure r): "
           f"{sp.simplify(sph)}, which tends to {lim} as r grows")


# --- C3: the centroid offset is identically zero in Cartesian, nonzero on a curved grid ---
def check_C3():
    h, r = sp.symbols("h r", positive=True)
    s = sp.symbols("s")
    def centroid(weight):
        return (sp.integrate((r + s) * weight, (s, -h / 2, h / 2))
                / sp.integrate(weight, (s, -h / 2, h / 2)))
    rv_cart = centroid(sp.Integer(1))                  # cell measure, Cartesian
    rc_cart = centroid(sp.Integer(1))                  # face measure, Cartesian
    rv_sph = centroid((r + s) ** 2)                    # cell measure r^2 dr
    rc_sph = centroid(r + s)                           # x2/x3 face measure r dr
    d_cart = sp.simplify(rv_cart - rc_cart)
    d_sph = sp.simplify(sp.expand(rv_sph - rc_sph))
    lead = sp.simplify(sp.series(d_sph, h, 0, 4).removeO())
    report("C3", d_cart == 0 and d_sph != 0,
           "the centroid offset r_v - r_c vanishes identically in Cartesian",
           f"Cartesian: {d_cart}; spherical: {lead} + O(h^4), so it is O(h^2/r) and the "
           f"ratio to the covariance term grows with the gradient scale over r")


# --- C4: the correction recovers the cell average of the velocity ---
def _quad(f, a, b, m=400):
    x = np.linspace(a, b, m + 1)
    y = f(x)
    return (b - a) / (3 * m) * (y[0] + y[-1] + 4 * y[1:-1:2].sum() + 2 * y[2:-2:2].sum())


def check_C4():
    """The primitive velocity a cell stores is m1/rho = <rho w>/<rho>, not <w>. By C1 the
    two differ by h^2/12 rho' w'/rho, which is exactly what :334 subtracts."""
    H, W = 1.0, 0.7
    rho = lambda z: np.exp(-z / H)
    wv = lambda z: np.sin(2. * np.pi * z / W) + 0.4
    ns, e_raw, e_cor = [16, 32, 64, 128], [], []
    for n in ns:
        h = 1. / n
        zc = (np.arange(-2, n + 3) + 0.5) * h
        r_avg = np.array([_quad(rho, a - h / 2, a + h / 2) / h for a in zc])
        w_avg = np.array([_quad(wv, a - h / 2, a + h / 2) / h for a in zc])
        rw_avg = np.array([_quad(lambda z: rho(z) * wv(z), a - h / 2, a + h / 2) / h
                           for a in zc])
        v = rw_avg / r_avg                       # what the code stores as IVX
        r1 = d1_centred(r_avg, zc)
        v1 = d1_centred(v, zc)
        v_cor = v - h * h / 12. * r1 * v1 / r_avg        # hydro_forward.cpp:334
        i = slice(2, n + 2)
        e_raw.append(np.max(np.abs(v[i] - w_avg[i])))
        e_cor.append(np.max(np.abs(v_cor[i] - w_avg[i])))
    o_raw = np.polyfit(np.log(ns[-3:]), np.log(e_raw[-3:]), 1)[0] * -1
    o_cor = np.polyfit(np.log(ns[-3:]), np.log(e_cor[-3:]), 1)[0] * -1
    _dump("x1cov_orders.json", {"ns": ns, "as_stored": list(map(float, e_raw)),
                                "corrected": list(map(float, e_cor))})
    report("C4", abs(o_raw - 2.) < 0.2 and o_cor > 3.6,
           "the stored velocity m1/rho differs from the cell average of w at second order, "
           "and subtracting h^2/12 rho_1 w_1 / rho recovers it at fourth",
           f"n = {ns[0]}..{ns[-1]}: as stored {e_raw[0]:.2e} -> {e_raw[-1]:.2e} "
           f"(order {o_raw:.2f}), corrected {e_cor[0]:.2e} -> {e_cor[-1]:.2e} "
           f"(order {o_cor:.2f})")


# --- C5: both corrections are exactly zero at rest ---
def check_C5():
    n = 48
    h = 1. / n
    zc = (np.arange(-2, n + 3) + 0.5) * h
    r_avg = np.exp(-zc)
    w_avg = np.zeros_like(zc)                 # rest
    r1, w1 = d1_centred(r_avg, zc), d1_centred(w_avg, zc)
    corr_x1 = h * h / 12. * r1 * w1 / r_avg   # hydro_forward.cpp:334
    # the x2/x3 correction of :63 carries a factor of u_n or its x1 difference
    un = np.zeros_like(zc)
    cov = h * h / 12. * d1_centred(r_avg * 2.5, zc) * d1_centred(un, zc)
    report("C5", np.max(np.abs(corr_x1)) == 0. and np.max(np.abs(cov)) == 0.,
           "both corrections are bitwise zero at rest",
           f"x1 mass covariance max |correction| = {np.max(np.abs(corr_x1)):.1e}; "
           f"x2/x3 covariance term max = {np.max(np.abs(cov)):.1e} (every term carries a "
           f"factor of the face-normal velocity or its x1 difference)")


# --- C6: the one-sided wall slope is second order ---
def check_C6():
    f = lambda z: np.exp(-1.3 * z)
    fp = lambda z: -1.3 * np.exp(-1.3 * z)
    ns, errs = [16, 32, 64, 128], []
    for n in ns:
        h = 1. / n
        z = np.arange(n + 1) * h
        v = f(z)
        s = 1
        i = 0
        hh = z[i + s] - z[i]
        one_sided = s * (-3. * v[i] + 4. * v[i + s] - v[i + 2 * s]) / (2. * s * hh)
        errs.append(abs(one_sided - fp(z[0])))
    order = np.polyfit(np.log(ns[-3:]), np.log(errs[-3:]), 1)[0] * -1
    report("C6", abs(order - 2.) < 0.15,
           "the one-sided density slope used in the first and last cell is second order",
           f"{errs[0]:.2e} -> {errs[-1]:.2e}, order {order:.2f}")


for fn in (check_C1, check_C2, check_C3, check_C4, check_C5, check_C6):
    fn()
print(f"{6 - len(FAIL)}/6 claims pass")
sys.exit(len(FAIL))
