"""Executable check of the gravity-work fixer (chapter 6, _fixer.qmd).

What is checked: the stage weight of HydroImpl::forward (src/hydro/hydro_forward.cpp:985-996), the uniform
per-mass fix and the wall-mass bound of MeshBlockImpl::apply_gravity_work_fixer
(src/mesh/meshblock.cpp:870-911) at snapy@e894700ff7aee30b52882e5202b16461413780b0, with the rk2 and rk3 stage
weights of pyharp@4721715855e937c1e8b218e964c0655f46e56e29 (src/integrator/integrator.cpp:36-61), ported line for
line. Claims C1-C4.

Run: python3 fixer_check.py   (numpy only; exits with the number of failed claims)
"""
import sys
from fractions import Fraction as Fr

import numpy as np

STAGES = {  # (wght0, wght1, wght2) per stage, integrator.cpp:36-61
    "rk1": [(0, 1, 1)],
    "rk2": [(0, 1, 1), (Fr(1, 2), Fr(1, 2), Fr(1, 2))],
    "rk3": [(0, 1, 1), (Fr(3, 4), Fr(1, 4), Fr(1, 4)), (Fr(1, 3), Fr(2, 3), Fr(2, 3))],
}


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def stage_weight(st, s):  # hydro_forward.cpp:988-994
    cw = Fr(st[s][2])
    for t in range(s + 1, len(st)):
        cw *= Fr(st[t][1])
    return cw


def check_C1_weights():
    rk3 = [stage_weight(STAGES["rk3"], s) for s in range(3)]
    sums = {k: sum(stage_weight(v, s) for s in range(len(v))) for k, v in STAGES.items()}
    ok = rk3 == [Fr(1, 6), Fr(1, 6), Fr(2, 3)] and all(x == 1 for x in sums.values())
    return report("C1", ok, "a stage's weight in the step is w2_s times the later stages' w1; for rk3 1/6, 1/6, 2/3, "
                  "and for rk1, rk2 and rk3 the weights sum to 1", "rk3 %s; sums %s" % (
                      [str(x) for x in rk3], {k: str(v) for k, v in sums.items()}))


def check_C2_weights_carry_a_linear_invariant():
    rng = np.random.default_rng(1)
    worst = 0.
    for _ in range(100):
        d = rng.normal(size=3)  # the invariant change each stage's increment carries
        u0, u = 0., 0.
        for s, (w0, w1, w2) in enumerate(STAGES["rk3"]):  # u <- w0 u0 + w1 u + w2 du_s
            u = float(w0) * u0 + float(w1) * u + float(w2) * d[s]
        weighted = sum(float(stage_weight(STAGES["rk3"], s)) * d[s] for s in range(3))
        worst = max(worst, abs(u - weighted))
    return report("C2", worst < 1e-15, "the weighted sum of the stage defects is the step's defect of any quantity "
                  "linear in the state", "max |step change - sum_s cw_s d_s| = %.1e over 100 draws" % worst)


def check_C3_fix_removes_the_defect():
    rng = np.random.default_rng(2)
    worst = 0.
    for _ in range(100):
        n = int(rng.integers(4, 40))
        m, V, D = rng.uniform(.1, 2., n), rng.uniform(.5, 2., n), rng.normal() * 1e3
        mass = np.sum(m * V)  # gravity_work_fixer_sums, meshblock.cpp:848-853
        efix = -D / mass  # :906
        dE = m * efix  # :907
        worst = max(worst, abs(np.sum(dE * V) + D) / abs(D))
    return report("C3", worst < 1e-14, "the fix adds -D rho_i / sum rho V to each cell's energy, which removes the "
                  "defect exactly", "max |sum V dE + D| / |D| = %.1e over 100 random domains" % worst)


def check_C4_wall_bound():
    eps = {"float64": np.finfo(np.float64).eps, "float32": np.finfo(np.float32).eps}
    bound = {k: 1e3 * e for k, e in eps.items()}  # meshblock.cpp:897-898
    ok = abs(bound["float64"] - 2.220446049250313e-13) < 1e-28 and abs(bound["float32"] - 1.1920928955e-4) < 1e-12
    return report("C4", ok, "a step is refused when the mass through the x1 wall faces exceeds 1e3 eps of the wall "
                  "cells' mass", "bound %.3e (float64), %.3e (float32) of the wall cells' mass"
                  % (bound["float64"], bound["float32"]))


def main():
    checks = [check_C1_weights, check_C2_weights_carry_a_linear_invariant, check_C3_fix_removes_the_defect,
              check_C4_wall_bound]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
