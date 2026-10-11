"""Executable check of the x1 seam flux average (chapter 4, _seam.qmd).

What is checked: the telescoping identity the section states and the average both ranks book at an x1 seam,
unpack(..., 0.5 * (mine + theirs)) in HydroImpl::forward (src/hydro/hydro_forward.cpp:487-495 at
snapy@e894700ff7aee30b52882e5202b16461413780b0), on a one-dimensional column split into two blocks whose
reconstructions disagree at the seam. Claims C1-C2.

Run: python3 seam_check.py   (numpy only; exits with the number of failed claims)
"""
import sys

import numpy as np


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


rng = np.random.default_rng(12)
N = 10                                     # cells per block
A = rng.uniform(0.5, 2.0, 2 * N + 1)       # face areas
F = rng.normal(size=2 * N + 1)             # face fluxes as one block would compute them
F0, F1 = 0.37, 0.41                        # the seam flux as block 0 and block 1 compute it


def total_change(seam_lo, seam_hi):
    """Sum over both blocks of -(A F)_{i+1/2} + (A F)_{i-1/2}: block 0 books seam_lo, block 1 books seam_hi."""
    f0 = F[:N + 1].copy()
    f1 = F[N:].copy()
    f0[-1], f1[0] = seam_lo, seam_hi
    d0 = -(A[1:N + 1] * f0[1:] - A[:N] * f0[:-1])
    d1 = -(A[N + 1:] * f1[1:] - A[N:-1] * f1[:-1])
    return d0.sum() + d1.sum()


BOUNDARY = -(A[-1] * F[-1] - A[0] * F[0])


def check_C1_disagreement_leaks():
    leak = total_change(F0, F1) - BOUNDARY
    want = -A[N] * (F0 - F1)
    ok = abs(leak - want) < 1e-14
    return report("C1", ok, "if the two blocks book different seam fluxes, the column total misses A (F0 - F1)",
                  "leak %.6f, A (F1 - F0) = %.6f" % (leak, -want))


def check_C2_average_restores_telescoping():
    mine0, mine1 = F0, F1
    up = 0.5 * (mine0 + mine1)             # block 0, its upper face: mine = F0, theirs = F1
    dn = 0.5 * (mine1 + mine0)             # block 1, its lower face: mine = F1, theirs = F0
    leak = total_change(up, dn) - BOUNDARY
    ok = up == dn and abs(leak) < 1e-14
    return report("C2", ok, "both blocks book 0.5 (mine + theirs): the two values are bitwise equal and the column "
                  "total is the boundary flux", "up == down: %s; leak %.1e" % (up == dn, leak))


def main():
    checks = [check_C1_disagreement_leaks, check_C2_average_restores_telescoping]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
