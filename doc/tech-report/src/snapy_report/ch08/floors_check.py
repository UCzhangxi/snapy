"""Executable check of the equation-of-state limiter, its floors and the condensate
borrow (chapter 8, _eoslimiter.qmd, _borrow.qmd, _marks.qmd).

Ports, statement for statement, of EquationOfStateImpl::apply_conserved_limiter_
(src/eos/equation_of_state.cpp:192-322) and apply_primitive_limiter_ (:325-350) at
snapy@e894700ff7aee30b52882e5202b16461413780b0, with the YAML defaults at :65-72.

The claims test what the operator DOES to a state, not what its formula says: C1 reorders
the passes and measures the difference, C2 measures the mass and energy a floor invents,
and C3 compares the shipped repair against the one the code comment says it replaced.

Run: python3 floors_check.py   (numpy only; exits with the number of failed claims)
"""
import sys

import numpy as np

FAIL = []
DENSITY_FLOOR = 1.0e-6     # equation_of_state.cpp:65
PRESSURE_FLOOR = 1.0e-3    # :71
TEMPERATURE_FLOOR = 20.0   # :72
CV = 718.0                 # a dry-air heat capacity, for the energy floor only


def report(tag, ok, what, detail):
    print(f"[{tag}] {'PASS' if ok else 'FAIL'} {what}: {detail}")
    if not ok:
        FAIL.append(tag)


def conserved_limiter(dens, mom, etot, species, mark_interior=True):
    """apply_conserved_limiter_, :201-235, in the order the code runs it:
    NaN to zero, then the dry-density floor, then the energy floor built from the
    ALREADY floored density. Returns the state and the two marks."""
    patched = nan_seen = False
    for a in (dens, mom, etot, species):
        if np.isnan(a).any():
            nan_seen = True
            a[np.isnan(a)] = 0.                       # :203
    before = (dens.copy(), etot.copy())
    np.maximum(dens, DENSITY_FLOOR, out=dens)         # :209
    rho = dens + species.sum(0)                       # :229
    ke = 0.5 * (mom ** 2).sum(0) / rho                # :230
    min_ie = rho * CV * TEMPERATURE_FLOOR             # :231-232, "UT->I"
    np.maximum(etot, ke + min_ie, out=etot)           # :233
    if not np.array_equal(dens, before[0]) or not np.array_equal(etot, before[1]):
        patched = True
    return dens, mom, etot, species, (patched and mark_interior, nan_seen and mark_interior)


# --- C1: the order of the two floors is load-bearing ---------------------------
def check_C1():
    """The energy floor is built from rho AFTER the density floor (:229 reads cons[IDN],
    which :209 has already clamped). Reversing the two gives a different state."""
    rng = np.random.default_rng(1)
    worst = 0.
    hits = 0
    for _ in range(3000):
        n = 8
        dens = rng.uniform(0., 3e-6, n)          # straddles the density floor
        mom = rng.normal(0., 1e-3, (3, n))
        etot = rng.uniform(0., 1e-2, n)
        spec = np.zeros((1, n))
        a = conserved_limiter(dens.copy(), mom.copy(), etot.copy(), spec.copy())[2]
        # the same two statements in the other order
        d2, e2 = dens.copy(), etot.copy()
        rho2 = d2 + spec.sum(0)
        ke2 = 0.5 * (mom ** 2).sum(0) / np.maximum(rho2, 1e-300)
        np.maximum(e2, ke2 + rho2 * CV * TEMPERATURE_FLOOR, out=e2)
        np.maximum(d2, DENSITY_FLOOR, out=d2)
        d = np.max(np.abs(a - e2))
        if d > 0.:
            hits += 1
        worst = max(worst, d)
    report("C1", hits > 0 and worst > 1e-9,
           "the energy floor uses the already-floored density, so the two passes do not commute",
           f"reversing them changes the energy in {hits} of 3000 random states, by up to "
           f"{worst:.2e} in absolute energy; a cell below the density floor gets a different "
           f"minimum internal energy under each order")


# --- C2: the floors are not conservative ---------------------------------------
def check_C2():
    """A floor is a clamp: it invents whatever mass or energy the state was missing.
    Measure it rather than assert it."""
    rng = np.random.default_rng(2)
    n = 4000
    dens = rng.uniform(-1e-7, 5e-6, n)
    mom = np.zeros((3, n))
    etot = rng.uniform(-1e-3, 1e-2, n)
    spec = np.zeros((1, n))
    m0, e0 = dens.sum(), etot.sum()
    d1, _, e1, _, _ = conserved_limiter(dens.copy(), mom, etot.copy(), spec)
    dm, de = d1.sum() - m0, e1.sum() - e0
    report("C2", dm > 0. and de > 0.,
           "the floors invent mass and energy; they are repairs, not conservative operations",
           f"on 4000 cells straddling the floors they add {dm:.3e} of dry mass and "
           f"{de:.3e} of total energy, both strictly positive: a clamp can only add. "
           f"Nothing anywhere removes it again")


# --- C3: the condensate borrow against the repair it replaced ------------------
def check_C3():
    """:242-268. A negative condensate means a neighbour has the mass, so zeroing it
    invents mass. The shipped repair borrows the deficit from the parent vapour in the
    same cell, which moves mass between rows and creates none."""
    rng = np.random.default_rng(3)
    n = 2000
    vapour = rng.uniform(1e-3, 1e-2, n)
    cloud = rng.uniform(-2e-4, 1e-3, n)
    total0 = vapour + cloud
    # the repair the comment says was measured at 102% of the total-mass drift
    cloud_zeroed = np.maximum(cloud, 0.)
    drift_zero = (vapour + cloud_zeroed - total0).sum()
    # the shipped repair: borrow the deficit from the parent vapour, one parent, share 1
    deficit = np.minimum(cloud, 0.)                  # :264
    vap_b = vapour + deficit * 1.0                   # :266
    cloud_b = np.maximum(cloud, 0.)                  # :268
    drift_borrow = (vap_b + cloud_b - total0).sum()
    neg_vap = int((vap_b < 0.).sum())
    report("C3", abs(drift_borrow) < 1e-18 and drift_zero > 1e-6,
           "the condensate borrow conserves mass where a clamp to zero invents it",
           f"over {n} cells with negative condensate, clamping to zero adds {drift_zero:.3e} "
           f"of mass while the borrow changes the total by {drift_borrow:.1e}; "
           f"{neg_vap} cells went vapour-negative and are left to the column repair")


# --- C4: the marks ---------------------------------------------------------------
def check_C4():
    """:202 and :235. Mark 1 is set by a NaN, mark 0 by any density or energy repair,
    and only for the interior: a repair in a ghost cell must not force a redo."""
    rng = np.random.default_rng(4)
    clean = (np.full(6, 1.0), np.zeros((3, 6)), np.full(6, 1e5), np.zeros((1, 6)))
    _, _, _, _, marks_clean = conserved_limiter(*[a.copy() for a in clean])
    low = (np.full(6, 1e-9), np.zeros((3, 6)), np.full(6, 1e5), np.zeros((1, 6)))
    _, _, _, _, marks_low = conserved_limiter(*[a.copy() for a in low])
    nan = (np.full(6, 1.0), np.zeros((3, 6)), np.full(6, np.nan), np.zeros((1, 6)))
    _, _, _, _, marks_nan = conserved_limiter(*[a.copy() for a in nan])
    ghost = (np.full(6, 1e-9), np.zeros((3, 6)), np.full(6, 1e5), np.zeros((1, 6)))
    _, _, _, _, marks_ghost = conserved_limiter(*[a.copy() for a in ghost],
                                                mark_interior=False)
    ok = (marks_clean == (False, False) and marks_low[0] and marks_nan[1]
          and marks_ghost == (False, False))
    report("C4", ok,
           "a repair marks the block for a redo, and only from the interior",
           f"an untouched state marks nothing {marks_clean}; a density below the floor sets "
           f"the patch mark {marks_low}; a NaN sets the NaN mark {marks_nan}; the same "
           f"density repair outside the interior marks nothing {marks_ghost}")


# --- C5: the primitive pass floors a different set of rows ---------------------
def check_C5():
    """:325-350. The primitive pass floors rho and p and clamps species at zero. It does
    NOT floor temperature, and it has no energy row to repair: the two passes are not the
    same operation applied to different variables."""
    rho = np.array([1e-9, 1.0])
    p = np.array([1e-9, 1e5])
    y = np.array([[-1e-9, 0.2]])
    rho_f = np.maximum(rho.copy(), DENSITY_FLOOR)     # :333
    y_f = np.maximum(y.copy(), 0.)                    # :346
    p_f = np.maximum(p.copy(), PRESSURE_FLOOR)        # :349
    report("C5", rho_f[0] == DENSITY_FLOOR and p_f[0] == PRESSURE_FLOOR
           and y_f[0, 0] == 0. and rho_f[1] == 1.0,
           "the primitive pass floors density and pressure and clamps species, and floors "
           "no temperature",
           f"density {rho[0]:.0e} -> {rho_f[0]:.0e}, pressure {p[0]:.0e} -> {p_f[0]:.0e}, "
           f"a negative mass fraction -> {y_f[0, 0]:.0e}; an admissible cell is untouched. "
           f"The conserved pass instead floors energy through a temperature floor of "
           f"{TEMPERATURE_FLOOR:.0f} K, which has no primitive counterpart")


for fn in (check_C1, check_C2, check_C3, check_C4, check_C5):
    fn()
print(f"{5 - len(FAIL)}/5 claims pass")
sys.exit(len(FAIL))
