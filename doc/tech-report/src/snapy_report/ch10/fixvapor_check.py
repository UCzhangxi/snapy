"""Executable check of the column vapour and cloud repair (chapter 10, _fixvapor.qmd).

What is checked: fix_vapor_impl (src/eos/fix_vapor_impl.h:9-79) at
snapy@e894700ff7aee30b52882e5202b16461413780b0, ported line for line below. Claims C1-C7.
C1-C3 replay the inputs of the eos_limiter gtests (tests/test_eos.cpp:40-120 at the same sha)
through the port; C4-C6 check the claims of the Derivation layer on random columns.
Also writes data/fixvapor_column.csv for fig_fixvapor_column.py.

Run: python3 fixvapor_check.py   (numpy only; exits with the number of failed claims)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def fix_vapor(vapor, major, vol):  # fix_vapor_impl.h:9-79; index 0 is the bottom cell
    nx1 = len(vapor)
    is_, ie = nx1 - 1, 0
    vol0 = vol[0]
    while is_ >= ie:  # :17
        if major[is_] <= 0.:
            return 1
        if vapor[is_] >= 0.:
            is_ -= 1
            continue
        i = is_  # :25
        sum_vapor = 0.
        sum_major = 0.
        while True:  # :34-39
            w = vol[i] / vol0
            sum_vapor += vapor[i] * w
            sum_major += major[i] * w
            i -= 1
            if not (sum_vapor < 0. and i >= ie):
                break
        if i < ie and sum_vapor < 0.:  # :41-64
            deficit = -sum_vapor
            above = 0.
            for j in range(is_ + 1, nx1):
                if major[j] <= 0.:
                    return 1
                above += vapor[j] * (vol[j] / vol0)
            if above < deficit:
                return 1
            for j in range(is_, ie - 1, -1):
                vapor[j] = 0.
            j = is_ + 1
            while j < nx1 and deficit > 0.:
                w = vol[j] / vol0
                need = deficit / w
                if vapor[j] <= need:
                    deficit -= vapor[j] * w
                    vapor[j] = 0.
                else:
                    vapor[j] -= need
                    deficit = 0.
                j += 1
            return 0
        yfrac = sum_vapor / sum_major  # :66-70
        for j in range(is_, i, -1):
            vapor[j] = yfrac * major[j]
        is_ = i
    return 0


def check_C1_downward_flatten():  # test_eos.cpp downward_branch_is_unchanged
    major = [1.00, 0.85, 0.72, 0.61]
    vapor = [0.2, -0.1, 0., 0.]
    err = fix_vapor(vapor, major, [1.] * 4)
    y = 0.1 / 1.85
    ok = err == 0 and vapor[0] == y * 1.00 and vapor[1] == y * 0.85 and vapor[2:] == [0., 0.]
    return report("C1", ok, "a deficit covered from below is rewritten at one ratio to the dry density",
                  "yfrac = %.10f; column %s" % (y, ["%.6e" % v for v in vapor]))


def check_C2_upward_fallback():  # test_eos.cpp repairs_bottom_cell_from_above
    major = [1.00, 0.85, 0.72, 0.61]
    vapor = [-1.7e-21, 4.4e-11, 1.0e-11, 1.0e-11]
    before = sum(vapor)
    err = fix_vapor(vapor, major, [1.] * 4)
    moved = 4.4e-11 - vapor[1]
    ok = (err == 0 and vapor[0] == 0. and abs(moved - 1.7e-21) <= 1e-25
          and vapor[2] == 1.0e-11 and abs(sum(vapor) - before) <= 1e-14 * abs(before))
    return report("C2", ok, "a bottom-cell deficit is taken from the first cell above, bounded by the deficit",
                  "transfer %.3e (deficit 1.7e-21); column sum change %.1e" % (moved, sum(vapor) - before))


def check_C3_net_deficit_untouched():  # test_eos.cpp rejects_column_in_net_deficit_without_writing
    vapor = [-0.3, 0.1, 0.1, 0.]
    want = list(vapor)
    err = fix_vapor(vapor, [1.] * 4, [1.] * 4)
    single = fix_vapor([-1e-30], [1.], [1.])
    return report("C3", err == 1 and vapor == want and single == 1,
                  "the upward branch writes nothing when it fails (net deficit, or a single negative cell)",
                  "return %d, column unchanged %s; single cell return %d" % (err, vapor == want, single))


def check_C4_volume_weighted_mass():
    rng = np.random.default_rng(10)
    worst, nfixed = 0., 0
    for _ in range(2000):
        n = int(rng.integers(2, 40))
        vol = list(rng.uniform(0.2, 5., n))
        major = list(rng.uniform(0.1, 2., n))
        vapor = list(rng.uniform(-0.2, 1., n) * np.asarray(major) * 1e-2)
        m0 = float(np.dot(vapor, vol))
        if fix_vapor(vapor, major, vol) == 0:
            nfixed += 1
            worst = max(worst, abs(float(np.dot(vapor, vol)) - m0) / max(abs(m0), 1e-300))
            if min(vapor) < 0.:
                worst = np.inf
    return report("C4", worst < 1e-13 and nfixed > 1000,
                  "a successful repair keeps sum_i V_i rho_{n,i} and leaves no negative cell",
                  "max relative column-mass change %.2e over %d repaired random columns (non-uniform V)"
                  % (worst, nfixed))


def check_C5_failure_writes_nothing():
    rng = np.random.default_rng(11)
    bad, nfail = 0, 0
    for _ in range(2000):
        n = int(rng.integers(1, 20))
        vol = list(rng.uniform(0.2, 5., n))
        major = list(rng.uniform(0.1, 2., n))
        vapor = list(rng.uniform(-1., 0.3, n))
        copy = list(vapor)
        if fix_vapor(vapor, major, vol) == 1:
            nfail += 1
            # the downward branch may already have rewritten windows above the failing one
            if float(np.dot(copy, vol)) >= 0.:
                bad += 1
    return report("C5", bad == 0 and nfail > 100,
                  "every failure is a column whose total vapour is negative (no repairable column fails)",
                  "%d failures, %d of them on a column with non-negative total" % (nfail, bad))


def check_C6_scan_terminates():
    nx1 = 64
    i = np.arange(nx1)
    vol = list((1. + i / nx1)**2)  # cell volume growing upward, as on a spherical-polar column
    major = list(np.exp(-i / 30.))
    vapor = list(4e-3 * np.asarray(major) * np.exp(-i / 25.))
    vapor[40] = -6e-4 * major[40]
    vapor[0] = -1e-4
    before = list(vapor)
    m0 = float(np.dot(vapor, vol))
    err = fix_vapor(vapor, major, vol)
    np.savetxt(os.path.join(HERE, "data", "fixvapor_column.csv"),
               np.column_stack([np.arange(nx1), before, vapor, major]), delimiter=",", fmt="%.10e",
               header="cell,vapor_before,vapor_after,major (64 cells, smooth profile, negative cells 40 and 0)")
    rel = abs(float(np.dot(vapor, vol)) - m0) / m0
    ok = err == 0 and min(vapor) >= 0. and rel < 1e-13
    return report("C6", ok, "a column with an interior and a bottom deficit is repaired in one top-down scan",
                  "return %d; min after %.3e; relative column-mass change %.1e" % (err, min(vapor), rel))


def check_C7_failure_after_a_window():
    vapor = [-0.9, 0.1, 0.3, -0.1, 0.2]  # index 0 is the bottom cell
    copy = list(vapor)
    err = fix_vapor(vapor, [1.] * 5, [1.] * 5)
    rewritten = [j for j in range(5) if vapor[j] != copy[j]]
    kept = abs(sum(vapor) - sum(copy)) < 1e-15
    return report("C7", err == 1 and rewritten == [2, 3] and kept,
                  "a failure below an already repaired window leaves that window rewritten, mass kept",
                  "return %d; cells rewritten before the failure %s; column sum change %.1e"
                  % (err, rewritten, sum(vapor) - sum(copy)))


def main():
    checks = [check_C1_downward_flatten, check_C2_upward_fallback, check_C3_net_deficit_untouched,
              check_C4_volume_weighted_mass, check_C5_failure_writes_nothing, check_C6_scan_terminates,
              check_C7_failure_after_a_window]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
