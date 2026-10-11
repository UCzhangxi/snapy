"""Executable check of the positivity-limiter meters (chapter 13, _limiter-meters.qmd).

What is checked: the meters accumulated in HydroImpl::forward (src/hydro/hydro_forward.cpp:648-705) from
flux_positivity_theta (src/hydro/flux_positivity.cpp:22-72) with the round-off bounds of
src/hydro/flux_positivity.hpp:18-23, and their printing (src/mesh/meshblock.cpp:1102-1107) at
snapy@e894700ff7aee30b52882e5202b16461413780b0, ported to numpy on a one-dimensional settling column. Claims C1-C4.

Run: python3 limiter_meters_check.py   (numpy only; exits with the number of failed claims)
"""
import sys

import numpy as np


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


ULP = {np.float64: 4096., np.float32: 64.}           # kPositivityRoundoffUlp, kPositivityRoundoffUlpFloat
MARGIN_ULP = 4096.                                   # the margin of flux_positivity_theta, in every precision


def theta_of(rho_y, flux, vol, area, dt, dtype=np.float64):
    """flux_positivity_theta in one dimension: flux on faces 0..n, cell i drained by its upper face where the
    flux is positive and by its lower face where it is negative."""
    af = area * flux
    out = np.maximum(af[1:], 0.) + np.maximum(-af[:-1], 0.)
    margin = MARGIN_ULP * np.finfo(dtype).eps
    avail = np.maximum(rho_y, 0.) * vol * (1. - margin)
    drain = out * dt
    theta = np.where(drain > 0., np.minimum(avail / np.maximum(drain, 1e-300), 1.), 1.)
    return theta, drain


def meters(rho_d, rho_y, flux, vol, area, dt, dtype=np.float64):
    """The census and the cut, as hydro_forward.cpp:656-705 accumulates them for one stage."""
    theta, drain = theta_of(rho_y, flux, vol, area, dt, dtype)
    hits = int((theta < 1.).sum())
    cell_mass = (rho_d + rho_y) * vol
    withheld = (1. - theta) * drain
    severe = int(((theta < 0.9) & (withheld > ULP[dtype] * np.finfo(dtype).eps * cell_mass)).sum())
    donor = np.concatenate([[1.], theta, [1.]])     # ghost theta 1 at the closed ends
    up = np.where(flux > 0., donor[:-1], donor[1:])  # the factor of each face's donor cell
    offered = np.abs(flux).sum()
    cut = (np.abs(flux) - np.abs(up * flux)).sum()
    return dict(hits=hits, severe=severe, thetamin=theta.min(), limcut=cut / offered if offered > 0 else None)


def settling_column(n=6, vsed=2., dx=1., cfl=2.):
    rho_y = np.full(n, 0.01)
    rho_d = np.ones(n)
    flux = np.zeros(n + 1)
    flux[1:n] = -rho_y[1:] * vsed               # each upper cell drains down; walls at both ends
    dt = cfl * dx / vsed                         # dt |vsed| / dx = 2, so theta = 1/2 in each drained cell
    return rho_d, rho_y, flux, np.full(n, dx), np.ones(n + 1), dt


def check_C1_hand_computed_settling_column():
    m = meters(*settling_column())
    ok = m["hits"] == 5 and m["severe"] == 5 and abs(m["thetamin"] - 0.5) < 1e-12 and abs(m["limcut"] - 0.5) < 1e-12
    return report("C1", ok, "a settling column with dt |v_sed| / dx = 2 on five draining cells: theta 1/2, five hits, "
                  "five severe, limcut 1/2", "hits %d, severe %d, thetamin %.15f, limcut %.15f"
                  % (m["hits"], m["severe"], m["thetamin"], m["limcut"]))


def check_C2_roundoff_drain_is_not_severe():
    rho_d, rho_y, flux, vol, area, dt = settling_column()
    rho_y[3] = 0.
    flux[3] = -1e-20                              # an empty cell drained by a round-off face flux
    m = meters(rho_d, rho_y, flux, vol, area, dt)
    theta, _ = theta_of(rho_y, flux, vol, area, dt)
    ok = theta[3] == 0. and m["hits"] == 5 and m["severe"] == 4
    return report("C2", ok, "an empty cell drained by a 1e-20 face flux has theta 0 and counts as a hit, but its "
                  "withheld mass is below round-off, so it is not severe", "theta of that cell %.1f; hits %d, severe %d"
                  % (theta[3], m["hits"], m["severe"]))


def check_C3_roundoff_bounds():
    b64 = ULP[np.float64] * np.finfo(np.float64).eps
    b32 = ULP[np.float32] * float(np.finfo(np.float32).eps)
    ok = abs(b64 - 9.094947017729282e-13) < 1e-27 and abs(b32 - 7.62939453125e-06) < 1e-18
    return report("C3", ok, "the severe threshold is 4096 ulp of the gas mass in float64 and 64 ulp in float32",
                  "float64 %.6e, float32 %.6e of the cell's gas mass" % (b64, b32))


def check_C4_values_when_the_limiter_never_ran():
    rho_d, rho_y, flux, vol, area, dt = settling_column()
    m = meters(rho_d, rho_y, flux * 0., vol, area, dt)
    ok = m["hits"] == 0 and m["severe"] == 0 and m["thetamin"] == 1. and m["limcut"] is None
    return report("C4", ok, "with no offered flux, thetamin stays at its initial 1, thetasevere at 0, and limcut is "
                  "not printed", "thetamin %.1f, severe %d, limcut %s" % (m["thetamin"], m["severe"], m["limcut"]))


def main():
    checks = [check_C1_hand_computed_settling_column, check_C2_roundoff_drain_is_not_severe, check_C3_roundoff_bounds,
              check_C4_values_when_the_limiter_never_ran]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
