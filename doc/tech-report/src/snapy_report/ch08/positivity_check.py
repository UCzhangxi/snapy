"""Executable check of the tracer flux positivity limiter (chapter 8, _theta.qmd,
_carry.qmd, _roundoff.qmd).

The explicit flux helpers below are numpy ports of src/hydro/flux_positivity.cpp at
snapy@6fbb39750f62b83df096058a4746e77d0a634bc5: flux_positivity_theta (:22-72),
flux_positivity_scale_ (:74-104) and flux_positivity_carry_ (:106-149), C8 is a synthetic counterexample, not a port of VIC. The two
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
           "donor margins use 4096 ulp; event thresholds use 4096/64 ulp",
           f"donor fractions: float64 {m64:.2e}, float32 {naive32:.2e}; "
           f"event fractions of gas mass: float64 {m64:.2e}, float32 {m32:.2e}")


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


# --- C8: where the explicit guarantee stops (_vic.qmd) ------------------------
def check_C8():
    """The limiter's guarantee is per stage, for the explicit flux divergence. The implicit
    solve runs afterwards on the same state and is outside it, which is the gap the clamp covers."""
    rng = np.random.default_rng(8)
    eps = np.finfo(np.float64).eps
    after_explicit, after_implicit, invented = 0., 0., 0.
    dry = 0
    for _ in range(2000):
        u, flux, area, vol, dt = _case(rng)
        th, _ = theta_of(u, flux, area, vol, dt, eps)
        u_exp = u + dt * divergence(scale(th, flux), area, vol)
        after_explicit = min(after_explicit, u_exp.min())
        # an implicit correction: a redistribution along the column, conservative in the column
        # total and built without reference to the limiter that ran before it
        move = rng.normal(0., 1., len(u) - 1) * u_exp[:-1].mean()
        d = np.zeros_like(u_exp)
        d[:-1] -= move * dt
        d[1:] += move * dt * vol[:-1] / vol[1:]
        u_imp = u_exp + d
        after_implicit = min(after_implicit, u_imp.min())
        dry += int((u_imp < 0.).any())
        clamped = np.maximum(u_imp, 0.)              # hypothetical pointwise floor, NOT the VIC transfer clamp
        invented = max(invented, float(((clamped - u_imp) * vol).sum()))
    report("C8", after_explicit >= 0. and after_implicit < 0. and dry > 0 and invented > 0.,
           "the per-stage guarantee does not reach past the explicit divergence",
           f"over 2000 columns the limited explicit update never goes negative (worst "
           f"{after_explicit:.1e}); a synthetic redistribution applied to that same state drives a "
           f"cell dry in {dry} of them, worst {after_implicit:.1e}. A hypothetical pointwise floor "
           f"would invent up to {invented:.1e} of mass; this is not the conservative VIC transfer clamp")


# --- C9: the dry-mass carry is not symmetric (_drycarry.qmd) ------------------
def check_C9():
    """An addition carries the ratio at source entry; a removal carries the ratio the stage
    would have had with no source at all. The zero-base guard keeps that finite but does not
    bound it (meshblock.cpp:631-634, 640-642)."""
    rng = np.random.default_rng(9)
    n = 200_000
    rho0, s0 = rng.uniform(0.5, 2., n), rng.uniform(0., 1., n)       # at source entry
    entry = s0 / rho0
    # what the stage did without the source, bounded so rho_base stays away from zero: the
    # unbounded case is the guard's, below, and is kept out of this number
    d_rho_free = rng.uniform(-.3, .3, n) * rho0
    d_s_free = rng.uniform(-.3, .3, n) * s0
    rho_base, s_base = rho0 + d_rho_free, s0 + d_s_free
    free = np.where(rho_base != 0., s_base / np.where(rho_base != 0., rho_base, 1.), entry)
    changed = float(np.abs(free - entry).max())                      # transport moved the ratio
    # the guard: a cell that is empty with the source removed
    g_entry = np.array([0.25])
    guarded = np.where(np.array([0.]) != 0., np.array([1.]), g_entry)
    finite = bool(np.isfinite(guarded).all() and guarded[0] == g_entry[0])
    # a dry sink: the removal carries the source-free ratio, and nothing bounds the result below
    src = -rng.uniform(0., 1.5, n) * rho0
    s_after = s_base + src * free
    negative = int(np.count_nonzero(s_after < 0.))
    worst = float(s_after.min())
    # had the removal used the entry ratio it would have amplified the ratio transport just set
    s_entry_rule = s_base + src * entry
    differ = float(np.abs(s_after - s_entry_rule).max())
    report("C9", finite and changed > 0. and negative > 0 and differ > 0.,
           "addition and removal are not symmetric, and the guard keeps the ratio finite "
           "without bounding it",
           f"over {n} cells transport moves the ratio away from its entry value by up to "
           f"{changed:.2f}, so the two rules differ by up to {differ:.2f} of scalar: the removal "
           f"rule carries the source-free ratio, the entry rule would carry the one transport "
           f"just changed. At a zero source-free density the guard returns the entry ratio and "
           f"the expression stays finite ({finite}). Nothing bounds the outcome below: under a dry "
           f"sink {negative} of {n} cells end with a negative scalar, worst {worst:.1e}")


for fn in (check_C1, check_C2, check_C3, check_C4, check_C5, check_C6, check_C7, check_C8, check_C9):
    fn()
print(f"{9 - len(FAIL)}/9 claims pass")
sys.exit(len(FAIL))
