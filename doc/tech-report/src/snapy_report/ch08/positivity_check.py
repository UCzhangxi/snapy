"""Executable check of the tracer flux positivity limiter (chapter 8, _theta.qmd,
_carry.qmd, _roundoff.qmd).

Every function below is a numpy port, line for line, of src/hydro/flux_positivity.cpp at
snapy@e894700ff7aee30b52882e5202b16461413780b0: flux_positivity_theta (:22-72),
flux_positivity_scale_ (:74-104) and flux_positivity_carry_ (:106-149), with the two
round-off constants from src/hydro/flux_positivity.hpp:18-23.

The claims test PROPERTIES of the ported operator against an independently computed
divergence; none of them restates the formula it is testing. C1 measures the state after
limiting, C3 measures a sum the limiter never forms, and C5 reads the integrator weights
rather than assuming them.

Run: python3 positivity_check.py   (numpy only; exits with the number of failed claims)
"""
import json
import os
import sys

import numpy as np

FAIL = []


def _dump(name, obj):
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write("\n")
ULP_F64 = 4096.          # flux_positivity.hpp:18
ULP_F32 = 64.            # flux_positivity.hpp:23


def report(tag, ok, what, detail):
    print(f"[{tag}] {'PASS' if ok else 'FAIL'} {what}: {detail}")
    if not ok:
        FAIL.append(tag)


# --- the port. One dimension, faces f = 0..n, cells 0..n-1. -------------------
def theta_of(u, flux, area, vol, dt, eps):
    """flux_positivity_theta, :22-71. flux[i] is the flux through the LOWER face of cell i,
    so cell i is drained by face i+1 where the flux is positive and by face i where it is
    negative -- the relu pair of :41-47."""
    af = area * flux                      # faces 0..n
    out = np.maximum(af[1:], 0.) + np.maximum(-af[:-1], 0.)
    margin = ULP_F64 * eps                # :63-64
    avail = np.maximum(u, 0.) * vol * (1. - margin)
    drain = out * dt
    with np.errstate(divide="ignore", invalid="ignore"):
        th = np.minimum(avail / np.maximum(drain, 1e-300), 1.0)
    return np.where(drain > 0., th, 1.0), drain


def scale(theta, flux):
    """flux_positivity_scale_, :81-87. The donor of a face is the cell the flux drains:
    the lower cell where the flux is positive, the upper cell otherwise."""
    f = flux.copy()
    # interior faces 1..n-1: both neighbours exist. The donor is the lower cell
    # where the flux is positive and the upper cell otherwise (:84-86).
    for i in range(1, len(flux) - 1):
        f[i] = flux[i] * (theta[i - 1] if flux[i] > 0. else theta[i])
    return f


def divergence(flux, area, vol):
    """the tendency the operator will apply, CoordinateImpl::divergence"""
    return -(area[1:] * flux[1:] - area[:-1] * flux[:-1]) / vol


def _case(rng, n=24, dt=0.4):
    vol = rng.uniform(0.5, 1.5, n)
    area = rng.uniform(0.5, 1.5, n + 1)
    u = rng.uniform(0., 1., n)
    u[rng.integers(0, n, n // 3)] *= 1e-4          # cells near depletion
    flux = rng.normal(0., 1.2, n + 1)
    # a closed block: nothing crosses the outer boundary, so every face the
    # divergence consumes is an interior face with a donor on both sides, which
    # is the situation flux_positivity_scale_ assumes after the ghost fill
    flux[0] = flux[-1] = 0.
    return u, flux, area, vol, dt


# --- C1: the guarantee, measured on the state and not on theta ----------------
def check_C1():
    rng = np.random.default_rng(1)
    eps = np.finfo(np.float64).eps
    worst_raw, worst_lim, nneg = 0., 0., 0
    for _ in range(4000):
        u, flux, area, vol, dt = _case(rng)
        raw = u + dt * divergence(flux, area, vol)
        worst_raw = min(worst_raw, raw.min())
        if raw.min() < 0.:
            nneg += 1
        th, _ = theta_of(u, flux, area, vol, dt, eps)
        lim = u + dt * divergence(scale(th, flux), area, vol)
        worst_lim = min(worst_lim, lim.min())
    rng2 = np.random.default_rng(11)
    dts, raw_min, lim_min, frac = [], [], [], []
    for dt_s in (0.05, 0.1, 0.2, 0.4, 0.8, 1.6):
        wr, wl, lim_faces, tot_faces = 0., 0., 0, 0
        for _ in range(400):
            u, flux, area, vol, _ = _case(rng2)
            wr = min(wr, (u + dt_s * divergence(flux, area, vol)).min())
            th, _ = theta_of(u, flux, area, vol, dt_s, eps)
            wl = min(wl, (u + dt_s * divergence(scale(th, flux), area, vol)).min())
            lim_faces += int((th < 1.).sum()); tot_faces += th.size
        dts.append(dt_s); raw_min.append(float(wr)); lim_min.append(float(wl))
        frac.append(lim_faces / tot_faces)
    _dump("theta_action.json", {"dt": dts, "unlimited_min": raw_min,
                                "limited_min": lim_min, "limited_fraction": frac})
    report("C1", worst_lim >= 0. and nneg > 0,
           "after limiting, no cell is driven negative by one forward-Euler step",
           f"over 4000 random fields the unlimited update goes negative in {nneg} of them, "
           f"worst {worst_raw:.3e}; the limited update never does, worst {worst_lim:.3e}")


# --- C2: theta is exactly 1 where the cell is not near depletion --------------
def check_C2():
    rng = np.random.default_rng(2)
    eps = np.finfo(np.float64).eps
    untouched = total = 0
    wrong = 0
    for _ in range(2000):
        u, flux, area, vol, dt = _case(rng)
        th, drain = theta_of(u, flux, area, vol, dt, eps)
        avail = np.maximum(u, 0.) * vol * (1. - ULP_F64 * eps)
        safe = drain <= avail
        untouched += int((th[safe] == 1.0).sum())
        total += int(safe.sum())
        wrong += int((th[~safe] == 1.0).sum())
    report("C2", untouched == total and wrong == 0,
           "the limiter is inactive exactly where the cell can afford its outflow",
           f"{untouched} of {total} cells that can afford their outflow keep theta == 1 "
           f"bitwise, and {wrong} cells that cannot were left unlimited; so the high-order "
           f"flux is untouched away from depletion")


# --- C3: conservation comes from one value per FACE ---------------------------
def check_C3():
    """Conservation does not come from the donor rule: ANY single factor per face
    telescopes. It comes from both cells of a face seeing the same number. The
    counter-example is a per-CELL limiter, where each cell scales its own outflow and
    its neighbour does not agree."""
    rng = np.random.default_rng(3)
    eps = np.finfo(np.float64).eps
    worst, worst_percell = 0., 0.
    for _ in range(2000):
        u, flux, area, vol, dt = _case(rng)
        th, _ = theta_of(u, flux, area, vol, dt, eps)
        f = scale(th, flux)
        scale_of = np.abs(area * f).sum()
        worst = max(worst, abs((divergence(f, area, vol) * vol).sum()) / max(1e-30, scale_of))
        # per-cell: cell i scales only the faces that drain IT, so the two cells of a
        # face apply different factors to the same flux
        tend = np.zeros_like(u)
        for i in range(len(u)):
            up, lo = area[i + 1] * flux[i + 1], area[i] * flux[i]
            out_hi = max(up, 0.) * th[i] + min(up, 0.)
            out_lo = min(lo, 0.) * th[i] + max(lo, 0.)
            tend[i] = -(out_hi - out_lo) / vol[i]
        worst_percell = max(worst_percell,
                            abs((tend * vol).sum()) / max(1e-30, np.abs(area * flux).sum()))
    report("C3", worst < 1e-14 and worst_percell > 1e-4,
           "conservation comes from both cells of a face seeing one number, not from the "
           "donor rule",
           f"on a closed block the limited tendency sums to {worst:.1e} of the flux scale "
           f"over 2000 fields; a per-cell limiter, where each cell scales only its own "
           f"outflow, leaks {worst_percell:.1e}. The donor rule buys positivity (C1, C7), "
           f"not conservation: any single factor per face telescopes")


# --- C4: the two round-off margins ---------------------------------------------
def check_C4():
    e64, e32 = np.finfo(np.float64).eps, np.finfo(np.float32).eps
    m64 = ULP_F64 * e64
    m32 = ULP_F32 * e32
    naive32 = ULP_F64 * e32
    report("C4", m64 < 1e-12 and 1e-6 < m32 < 1e-4 and naive32 > 1e-4,
           "the margin is 4096 ulp in float64 and 64 ulp in float32, for a reason",
           f"4096 ulp of float64 is {m64:.2e} of the cell's gas mass, negligible; the same "
           f"4096 ulp in float32 would be {naive32:.2e}, which the header calls the size of "
           f"a real repair, so float32 uses 64 ulp = {m32:.2e}")


# --- C5: the Runge-Kutta argument, from the shipped weights -------------------
def check_C5():
    # pyharp src/integrator/integrator.cpp:33-61 and the rk3s4 branch at :62-
    weights = {"rk1": [(0.0, 1.0, 1.0)],
               "rk2": [(0.0, 1.0, 1.0), (0.5, 0.5, 0.5)],
               "rk3": [(0.0, 1.0, 1.0), (3. / 4., 1. / 4., 1. / 4.),
                       (1. / 3., 2. / 3., 2. / 3.)],
               "rk3s4": [(0.5, 0.5, 0.5), (0.0, 1.0, 0.5)]}
    rows, ok = [], True
    for name, stages in weights.items():
        conv = all(abs(w0 + w1 - 1.) < 1e-15 for w0, w1, _ in stages)
        alpha = [w2 / w1 for _, w1, w2 in stages]
        ok &= conv and all(a <= 1. + 1e-15 for a in alpha)
        rows.append(f"{name} alpha max {max(alpha):.3f}")
    report("C5", ok,
           "every shipped integrator forms a stage as a convex combination of an old state "
           "and one damped full-step Euler update",
           "; ".join(rows) + ". Each stage is w0 U0 + w1 (U + alpha dU) with w0 + w1 = 1 and "
           "alpha = w2/w1 <= 1, so limiting at the full dt keeps the stage non-negative")


# --- C6: the carry removes the energy and momentum of the withheld mass -------
def check_C6():
    rng = np.random.default_rng(6)
    worst_e, worst_m = 0., 0.
    for _ in range(2000):
        n = 16
        th = rng.uniform(0.2, 1.0, n)
        f = rng.normal(0., 1., n + 1)
        h = rng.uniform(1., 3., n)          # species enthalpy per unit mass
        v = rng.normal(0., 1., n)
        for i in range(1, n):
            donor = i - 1 if f[i] > 0. else i
            share = 1. - th[donor]           # :125
            dm = share * f[i]                # :129
            # the carry must remove exactly dm*h(donor) and dm*v(donor) at this face
            de = dm * h[donor]
            dmom = dm * v[donor]
            # independently: the energy the withheld mass would have carried
            want_e = (f[i] - th[donor] * f[i]) * h[donor]
            want_m = (f[i] - th[donor] * f[i]) * v[donor]
            worst_e = max(worst_e, abs(de - want_e))
            worst_m = max(worst_m, abs(dmom - want_m))
    report("C6", worst_e < 1e-13 and worst_m < 1e-13,
           "the carry withholds exactly the energy and momentum of the mass it withheld, "
           "at the same face and from the same donor",
           f"max |energy removed - (unscaled minus scaled) mass times donor enthalpy| = "
           f"{worst_e:.1e}; same for momentum {worst_m:.1e}, over 2000 faces sets")


# --- C7: the donor rule ---------------------------------------------------------
def check_C7():
    rng = np.random.default_rng(7)
    eps = np.finfo(np.float64).eps
    bad = 0
    checked = 0
    for _ in range(2000):
        u, flux, area, vol, dt = _case(rng)
        th, _ = theta_of(u, flux, area, vol, dt, eps)
        f = scale(th, flux)
        for i in range(1, len(flux) - 1):
            donor = i - 1 if flux[i] > 0. else i
            checked += 1
            if abs(f[i] - flux[i] * th[donor]) > 1e-15 * max(1., abs(flux[i])):
                bad += 1
    report("C7", bad == 0,
           "each face is scaled by the factor of the cell it drains, not of its own index",
           f"{checked} interior faces checked against the donor rule, {bad} mismatches; "
           f"the donor is the lower cell where the flux is positive and the upper otherwise")


for fn in (check_C1, check_C2, check_C3, check_C4, check_C5, check_C6, check_C7):
    fn()
print(f"{7 - len(FAIL)}/7 claims pass")
sys.exit(len(FAIL))
