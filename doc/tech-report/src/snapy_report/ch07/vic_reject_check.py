"""Executable check of VIC rejection and rollback (chapter 7, _vic-reject.qmd).

What is checked: the control flow of ImplicitHydroImpl::forward_masked (src/implicit/implicit_hydro.cpp:160-484),
its latch (implicit_hydro.hpp:96-101), the stage-zero reset (src/mesh/meshblock.cpp:616-619) and the redo flag
(src/mesh/meshblock.cpp:1278-1286) at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported as a small state
machine; the solve itself is the vic_port.py sweep. Claims C1-C4.

Run: python3 vic_reject_check.py   (numpy only; exits with the number of failed claims)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vic_port as vp  # noqa: E402


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


GUARDS = ("inputs", "sentinel", "results", "correction")


class Corrector:
    """forward_masked with the four guards: nonfinite inputs (222-224), the solve sentinel (350-351), nonfinite
    results (473-475) and a nonfinite correction (480-481). `poison` injects a NaN at one guard."""

    def __init__(self):
        self.solve_failed = False
        self.solves = 0

    def forward_masked(self, du, w, dt, a, b, c, poison=None):
        if self.solve_failed:                              # 175-180: the latch
            return np.zeros_like(du)
        du0, w0 = du.copy(), w.copy()                      # 195, 198

        def reject():                                      # 200-218
            self.solve_failed = True
            du[...] = du0
            w[...] = w0
            return np.zeros_like(du)

        if poison == "inputs":
            du[0, 0, 0] = np.nan
        if not (np.isfinite(du).all() and np.isfinite(w).all()):
            return reject()
        w[..., vp.IVY] += 1.                               # 227-231: the frame projection edits w in place
        self.solves += 1
        delta = np.zeros_like(du)
        for k in range(du.shape[0]):                       # one column at a time, as the dispatch does
            aa = a[k].copy()
            if poison == "sentinel" and k == du.shape[0] // 2:
                aa[0] = 0.                                 # a zero block: ludcmp returns 0
            _, af, d = vp.forward_sweep(aa, b[k], c[k], du[k] / dt)
            delta[k] = vp.backward_substitute(af, d)
        if not np.isfinite(delta).all():                   # 350-351
            return reject()
        du[...] = delta
        if poison == "results":
            du[0, 1, 1] = np.inf
        if not np.isfinite(du).all():                      # 473-475
            return reject()
        corr = du - du0                                    # 477-478
        if poison == "correction":
            corr[0, 2, 2] = np.nan
        if not np.isfinite(corr).all():                    # 480-481
            return reject()
        return corr


rng = np.random.default_rng(13)
N_COL, N_LAYER = 4, 8
SHAPE = (N_COL, N_LAYER, 5)


def system():
    a = np.eye(5) * 2. + rng.normal(size=(N_COL, N_LAYER, 5, 5)) * .1
    return a, rng.normal(size=(N_COL, N_LAYER, 5, 5)) * .1, rng.normal(size=(N_COL, N_LAYER, 5, 5)) * .1


def check_C1_every_guard_restores_bitwise():
    rows, ok = [], True
    for g in GUARDS:
        p = Corrector()
        du, w = rng.normal(size=SHAPE), rng.normal(size=SHAPE)
        du_in, w_in = du.copy(), w.copy()
        corr = p.forward_masked(du, w, 0.5, *system(), poison=g)
        same = np.array_equal(du, du_in) and np.array_equal(w, w_in) and not corr.any() and p.solve_failed
        ok &= same
        rows.append("%s %s" % (g, "restored" if same else "NOT restored"))
    return report("C1", ok, "each of the four guards restores du and w bit for bit, returns a zero correction and latches",
                  ", ".join(rows))


def check_C2_latch_skips_later_stages():
    p = Corrector()
    a, b, c = system()
    out = []
    for stage in range(3):
        du, w = rng.normal(size=SHAPE), rng.normal(size=SHAPE)
        corr = p.forward_masked(du, w, 0.5, a, b, c, poison="sentinel" if stage == 0 else None)
        out.append(float(np.abs(corr).max()))
    ok = p.solves == 1 and out == [0., 0., 0.]
    return report("C2", ok, "after a failure at stage 0 the later stages of the step return zero without solving",
                  "solves run %d of 3 stages; max |correction| per stage %s" % (p.solves, out))


def redo_flags(p):
    """meshblock.cpp:859-862 and 1278-1286: the VIC failure is the sixth cause, bit 32."""
    return 32 if p.solve_failed else 0


def check_C3_failure_requests_a_redo_and_the_retry_starts_clean():
    p = Corrector()
    a, b, c = system()
    p.forward_masked(rng.normal(size=SHAPE), rng.normal(size=SHAPE), .5, a, b, c, poison="sentinel")
    mask = redo_flags(p)
    p.solve_failed = False                                 # meshblock.cpp:616-619 at stage 0 of the retry
    corr = p.forward_masked(rng.normal(size=SHAPE), rng.normal(size=SHAPE), .25, a, b, c)
    ok = mask == 32 and redo_flags(p) == 0 and np.abs(corr).max() > 0
    return report("C3", ok, "a failed step raises redo cause 32; the stage-0 reset lets the retry solve again",
                  "cause mask %d; retry mask %d, retry max |correction| %.3g" % (mask, redo_flags(p), np.abs(corr).max()))


def check_C4_one_bad_column_rolls_back_the_block():
    p = Corrector()
    a, b, c = system()
    du, w = rng.normal(size=SHAPE), rng.normal(size=SHAPE)
    du_in = du.copy()
    good = Corrector().forward_masked(du.copy(), w.copy(), .5, a, b, c)
    corr = p.forward_masked(du, w, .5, a, b, c, poison="sentinel")
    ok = np.abs(good).max() > 0 and not corr.any() and np.array_equal(du, du_in)
    return report("C4", ok, "one failed column of %d returns a zero correction for every column of the block; "
                  "no column is partly updated" % N_COL,
                  "max |correction| without the failure %.3g, with it %.1g; du unchanged: %s"
                  % (np.abs(good).max(), np.abs(corr).max(), np.array_equal(du, du_in)))


def main():
    checks = [check_C1_every_guard_restores_bitwise, check_C2_latch_skips_later_stages,
              check_C3_failure_requests_a_redo_and_the_retry_starts_clean, check_C4_one_bad_column_rolls_back_the_block]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
