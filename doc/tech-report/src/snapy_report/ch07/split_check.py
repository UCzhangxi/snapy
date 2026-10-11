"""Executable check of the operator split at the step boundary (chapter 7, _split.qmd).

What is checked: the Lie (sequential) split of MeshBlockImpl::advance_local and the example driver
(src/mesh/meshblock.cpp:795-841, examples/run_hydro.cpp:166-191 at
snapy@e894700ff7aee30b52882e5202b16461413780b0): the dynamics advance a whole step, then the saturation
adjustment, then the kinetics, each on the result of the one before. Two non-commuting linear operators stand in
for them. Claims C1-C3.

Run: python3 split_check.py   (numpy only; exits with the number of failed claims)
"""
import sys

import numpy as np


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def expm(M):
    w, V = np.linalg.eig(M)
    return (V @ np.diag(np.exp(w)) @ np.linalg.inv(V)).real


A = np.array([[-1.0, 0.4], [0.0, -0.3]])   # stands in for the dynamics
B = np.array([[-0.2, 0.0], [0.7, -2.0]])   # stands in for the step-boundary source
U0 = np.array([1.0, 0.5])
T = 1.0


def split(n, strang=False):
    dt = T / n
    u = U0.copy()
    if strang:
        ea, eb2 = expm(A * dt), expm(B * dt / 2)
        for _ in range(n):
            u = eb2 @ (ea @ (eb2 @ u))
    else:
        ea, eb = expm(A * dt), expm(B * dt)
        for _ in range(n):
            u = eb @ (ea @ u)                  # dynamics first, then the boundary source
    return u


def check_C1_lie_split_is_first_order():
    exact = expm((A + B) * T) @ U0
    errs = [np.abs(split(n) - exact).max() for n in (20, 40, 80)]
    order = np.log2(errs[1] / errs[2])
    return report("C1", abs(order - 1.) < 0.05, "the sequential split converges at first order in dt",
                  "errors %s at 20, 40, 80 steps; fitted order %.3f" % (", ".join("%.2e" % e for e in errs), order))


def check_C2_strang_for_contrast():
    exact = expm((A + B) * T) @ U0
    errs = [np.abs(split(n, True) - exact).max() for n in (20, 40, 80)]
    order = np.log2(errs[1] / errs[2])
    return report("C2", abs(order - 2.) < 0.05, "a symmetric (Strang) split would be second order; snapy does not use it",
                  "fitted order %.3f" % order)


def check_C3_commuting_operators_split_exactly():
    a, b = np.diag([-1.0, -0.3]), np.diag([-0.2, -2.0])
    err = np.abs(expm(b) @ expm(a) @ U0 - expm(a + b) @ U0).max()
    return report("C3", err < 1e-14, "the splitting error is the commutator: commuting operators split exactly",
                  "error %.1e" % err)


def main():
    checks = [check_C1_lie_split_is_first_order, check_C2_strang_for_contrast,
              check_C3_commuting_operators_split_exactly]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
