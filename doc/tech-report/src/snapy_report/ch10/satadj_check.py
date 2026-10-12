"""Executable check of the saturation-adjustment write-back (chapter 10, _satadj.qmd).

What is checked, at snapy@6fbb39750f62b83df096058a4746e77d0a634bc5, ported line for line below:
- the state formed for the solve and the write-back of MeshBlockImpl::advance_local, step (6)
  (src/mesh/meshblock.cpp:800-816).
The equilibrium solve itself (kintera ThermoYImpl::forward) is replaced by a stand-in that moves mass
between a vapour and its condensate at fixed sum of the fractions, or, for C2, changes that sum on purpose;
the solve's own algebra is chapter 2's (src/snapy_report/ch02/saturation_check.py).
Claims C1-C3.

Run: python3 satadj_check.py   (numpy; exits with the number of failed claims)
"""
import sys

import numpy as np

IDN, IVX, IVY, IVZ, IPR, ICY = 0, 1, 2, 3, 4, 5


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def adjust(u, solve):  # meshblock.cpp:800-816 on a whole block (no ghosts in this port)
    u = u.copy()
    ny = u.shape[0] - ICY
    ke = 0.5 * (u[IVX] ** 2 + u[IVY] ** 2 + u[IVZ] ** 2) / (u[IDN] + u[ICY:].sum(0))  # "U->K"
    rho = u[IDN] + u[ICY:ICY + ny].sum(0)
    ie = u[IPR] - ke
    yfrac = u[ICY:ICY + ny] / rho
    solve(rho, ie, yfrac)  # rho and ie by value, yfrac in place
    u[ICY:ICY + ny] = yfrac * rho
    return u, rho


def condense(rho, ie, y):  # stand-in: move a share of vapour 0 to its condensate 1, sum kept
    move = 0.3 * y[0]
    y[0] -= move
    y[1] += move


def state(rng, n=4096):
    u = np.empty((ICY + 2, n))
    u[IDN] = rng.uniform(0.5, 1.5, n)
    u[ICY] = u[IDN] * rng.uniform(1e-3, 3e-2, n)
    u[ICY + 1] = u[IDN] * rng.uniform(0., 1e-3, n)
    u[IVX:IVZ + 1] = rng.normal(0., 20., (3, n)) * u[IDN]
    u[IPR] = 2.5e5 + rng.uniform(0., 1e4, n)
    return u


def check_C1_only_species_rows():
    u = state(np.random.default_rng(10))
    v, _ = adjust(u, condense)
    same = all(np.array_equal(v[i], u[i]) for i in (IDN, IVX, IVY, IVZ, IPR))
    moved = np.abs(v[ICY] - u[ICY]).max()
    return report("C1", same and moved > 0.,
                  "the write-back changes only the species rows: dry density, momentum and E are bitwise unchanged",
                  "4096 cells: rows 0-4 identical %s; largest species change %.1e" % (same, moved))


def check_C2_density_follows_sum():
    u = state(np.random.default_rng(11))
    rho_in = u[IDN] + u[ICY:].sum(0)
    v, rho = adjust(u, condense)
    kept = np.abs(v[IDN] + v[ICY:].sum(0) - rho_in).max() / rho_in.max()

    def leak(r, ie, y):
        condense(r, ie, y)
        y[1] += 1e-6

    w, _ = adjust(u, leak)
    drift = np.abs((w[IDN] + w[ICY:].sum(0) - rho_in) / rho_in - 1e-6).max()
    return report("C2", kept < 4 * np.finfo(float).eps and drift < 1e-12,
                  "rho is unchanged to round-off when the solve keeps sum y_n, "
                  "and moves by rho times its change otherwise",
                  "sum kept: max |rho' - rho| / rho = %.1e; sum + 1e-6: max |(rho' - rho)/rho - 1e-6| = %.1e"
                  % (kept, drift))


def check_C3_untouched_cells_round_trip():
    u = state(np.random.default_rng(12))
    v, _ = adjust(u, lambda r, ie, y: None)
    rel = np.abs(v[ICY:] - u[ICY:]) / np.abs(u[ICY:]).clip(1e-300)
    ulp = (rel / np.finfo(float).eps).max()
    changed = np.count_nonzero(v[ICY:] != u[ICY:])
    return report("C3", ulp <= 2.,
                  "a cell the solve leaves alone gets rho_n back as (rho_n / rho) rho, "
                  "within 2 eps relative, not always bitwise",
                  "8192 species values: %d not bitwise equal, max change %.2f eps relative" % (changed, ulp))


def main():
    checks = [check_C1_only_species_rows, check_C2_density_follows_sum, check_C3_untouched_cells_round_trip]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
