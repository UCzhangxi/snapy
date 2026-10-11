"""Executable check of the explicit Runge-Kutta stage update (chapter 7, _rk.qmd).

What is checked: the stage update u <- w0 u0 + w1 u + w2 dU of MeshBlockImpl::advance_local
(src/mesh/meshblock.cpp:755 at snapy@e894700ff7aee30b52882e5202b16461413780b0), with the stage weights of
IntegratorImpl (src/integrator/integrator.cpp:35-78 at pyharp@4721715855e937c1e8b218e964c0655f46e56e29),
ported line for line, and dU = dt L(u) the full-step increment. Claims C1-C4.

Run: python3 rk_check.py   (numpy only; exits with the number of failed claims)
"""
import math
import sys

import numpy as np

# integrator.cpp:35-78, (wght0, wght1, wght2) per stage
WEIGHTS = {
    "rk1": [(0., 1., 1.)],
    "rk2": [(0., 1., 1.), (.5, .5, .5)],
    "rk3": [(0., 1., 1.), (3. / 4., 1. / 4., 1. / 4.), (1. / 3., 2. / 3., 2. / 3.)],
    "rk3s4": [(.5, .5, .5), (0., 1., .5), (2. / 3., 1. / 3., 1. / 6.), (0., 1., .5)],
}


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def step(kind, u0, rhs, dt):
    """one step: every stage forms w0 u0 + w1 u + w2 dt L(u) (meshblock.cpp:755, integrator.cpp:119-120)"""
    u = u0
    for w0, w1, w2 in WEIGHTS[kind]:
        u = w0 * u0 + w1 * u + w2 * dt * rhs(u)
    return u


def check_C1_stability_polynomials():
    z = np.array([0.1, -0.7, 0.3 + 0.9j, -1.5 + 0.2j])
    want = {"rk1": 1 + z,
            "rk2": 1 + z + z**2 / 2,
            "rk3": 1 + z + z**2 / 2 + z**3 / 6,
            "rk3s4": 1 + z + z**2 / 2 + z**3 / 6 + z**4 / 48}
    worst = max(np.abs(step(k, 1. + 0j, lambda u: u * z, 1.) - want[k]).max() for k in WEIGHTS)
    return report("C1", worst < 1e-14, "amplification factors on u' = lambda u",
                  "rk1 1+z; rk2 to z^2/2; rk3 to z^3/6; rk3s4 to z^3/6 + z^4/48; max error %.1e" % worst)


def check_C2_order_on_a_nonlinear_ode():
    # u' = -u^2 + sin t, autonomous form with t as a second component
    def rhs(y):
        return np.array([-y[0] ** 2 + math.sin(y[1]), 1.])
    T, y0 = 1., np.array([1., 0.])
    def solve(kind, n):
        y = y0.copy()
        for _ in range(n):
            y = step(kind, y, rhs, T / n)
        return y[0]
    ref = solve("rk3s4", 20000)
    out, ok = [], True
    want = {"rk1": 1, "rk2": 2, "rk3": 3, "rk3s4": 3}
    for kind in WEIGHTS:
        errs = [abs(solve(kind, n) - ref) for n in (40, 80, 160)]
        order = np.log2(errs[1] / errs[2])
        ok = ok and abs(order - want[kind]) < 0.1
        out.append("%s %.2f" % (kind, order))
    return report("C2", ok, "fitted order on a nonlinear ODE, n = 40, 80, 160 steps", ", ".join(out))


def check_C3_convex_stages():
    out, ok = [], True
    want = {"rk1": 1., "rk2": 1., "rk3": 1., "rk3s4": 2.}
    for kind, stages in WEIGHTS.items():
        convex = all(abs(w0 + w1 - 1.) < 1e-15 and w0 >= 0 and w1 > 0 for w0, w1, _ in stages)
        # at stage 0 the current state is u0, so the forward-Euler step carries w0 + w1
        c = min(((w0 + w1) if s == 0 else w1) / w2 for s, (w0, w1, w2) in enumerate(stages))
        ok = ok and convex and abs(c - want[kind]) < 1e-15
        out.append("%s C=%g" % (kind, c))
    return report("C3", ok, "each stage is a convex combination of u0 and a forward-Euler step; SSP coefficient C = min over stages of (Euler weight)/w2",
                  ", ".join(out))


def check_C4_positivity_up_to_the_ssp_limit():
    # u' = -u: forward Euler keeps u >= 0 for dt <= 1; the scheme keeps it for dt <= C
    out, ok = [], True
    for kind, c in (("rk3", 1.), ("rk3s4", 2.)):
        pos = all(step(kind, 1., lambda u: -u, dt) >= 0 for dt in np.linspace(0.01, c, 200))
        ok = ok and pos
        out.append("%s nonnegative for dt <= %g" % (kind, c))
    return report("C4", ok, "the stage values stay nonnegative up to dt = C", "; ".join(out))


def main():
    checks = [check_C1_stability_polynomials, check_C2_order_on_a_nonlinear_ode, check_C3_convex_stages,
              check_C4_positivity_up_to_the_ssp_limit]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
