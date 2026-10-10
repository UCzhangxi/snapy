"""Executable check of the driver-level kinetics (chapter 10, _kinetics.qmd).

What is checked, at kintera@c55b13b2204997d2d09e04498558ab9495d8ee77:
- the two-product extent of EvaporationImpl::forward (src/kinetics/evaporation.cpp:165-192), ported below;
- the implicit step of evolve_implicit_cell (src/kinetics/evolve_implicit_impl.h:66-77), ported below;
and the species update of examples/run_hydro.cpp:187-191 at snapy@e894700ff7aee30b52882e5202b16461413780b0.
Claims C1-C4. Also writes data/kinetics_extent.csv for fig_kinetics_extent.py.

Run: python3 kinetics_check.py   (numpy and sympy; exits with the number of failed claims)
"""
import os
import sys

import numpy as np
import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def extent(c1, c2, k2):  # evaporation.cpp:165-192, one two-product reaction, float64
    c1, c2 = max(c1, 0.), max(c2, 0.)
    sub = c1 * c2 <= k2
    if not sub:
        c1 = c2 = 0.
    prod, s, diff = c1 * c2, c1 + c2, c1 - c2
    tiny = np.finfo(float).tiny
    root = np.sqrt(max(diff * diff + 4. * k2, tiny))
    x = 2. * (k2 - prod) / max(s + root, tiny)
    return max(x if sub else 0., 0.)


def implicit_step(rate, jac, stoich, dt):  # evolve_implicit_impl.h:66-77
    a = np.eye(stoich.shape[0]) / dt - stoich @ jac
    return np.linalg.solve(a, stoich @ rate)


def check_C1_extent_root():
    c1, c2, k, x = sp.symbols("c_1 c_2 K x", positive=True)
    xcode = 2 * (k - c1 * c2) / (c1 + c2 + sp.sqrt((c1 - c2)**2 + 4 * k))
    resid = sp.simplify(sp.expand((c1 + xcode) * (c2 + xcode) - k))
    num = max(abs((a + extent(a, b, kk)) * (b + extent(a, b, kk)) - kk) / kk
              for a, b, kk in [(1e-3, 2e-2, 1e-4), (0., 0., 1.), (3., 1e-9, 4.), (1e-150, 1e-150, 1e-200)])
    return report("C1", resid == 0 and num < 1e-14,
                  "the code's extent is the positive root of (c_1 + x)(c_2 + x) = K, in a form without cancellation",
                  "symbolic residual %s; max relative residual of the port %.1e over 4 cases" % (resid, num))


def check_C2_one_step_is_backward_euler():
    kf, kb, dt = 3., 1., 0.7
    c = np.array([1., 0.])  # A <-> B
    stoich = np.array([[-1.], [1.]])
    rate = np.array([kf * c[0] - kb * c[1]])
    jac = np.array([[kf, -kb]])
    dc = implicit_step(rate, jac, stoich, dt)
    exact = np.linalg.solve(np.eye(2) - dt * stoich @ jac, c) - c  # backward Euler of a linear system
    return report("C2", np.allclose(dc, exact, rtol=1e-15, atol=1e-15),
                  "for a linear rate law the step (I/dt - N J) dc = N rate is one backward-Euler step",
                  "dc = %s, backward Euler %s" % (np.array2string(dc, precision=12), np.array2string(exact, precision=12)))


def check_C3_no_overshoot():
    kf, kb = 3., 1.
    stoich = np.array([[-1.], [1.]])
    jac = np.array([[kf, -kb]])
    ceq = kb / (kf + kb)
    worst = 0.
    for dt in np.logspace(-3, 6, 50):
        c = np.array([1., 0.])
        dc = implicit_step(np.array([kf * c[0] - kb * c[1]]), jac, stoich, dt)
        ratio = (c[0] + dc[0] - ceq) / (c[0] - ceq)
        # tolerance: 1e-14 times the condition number 1 + dt (k_f + k_b) of I/dt - N J (one LU solve)
        worst = max(worst, abs(ratio - 1. / (1. + dt * (kf + kb))) / (1e-14 * (1. + dt * (kf + kb))))
        if not (0. < ratio <= 1.):
            worst = np.inf
    return report("C3", worst < 1.,
                  "one step moves toward equilibrium by 1/(1 + dt (k_f + k_b)) and never past it, for any dt",
                  "max deviation from the contraction factor / (1e-14 cond) = %.2f over dt in [1e-3, 1e6]" % worst)


def check_C4_species_update_keeps_mass():
    mu = np.array([17.031e-3, 34.082e-3, 51.113e-3])  # NH3, H2S, NH4SH(s), kg/mol
    stoich = np.array([[1.], [1.], [-1.]])  # NH4SH(s) -> NH3 + H2S
    rng = np.random.default_rng(4)
    worst = 0.
    for _ in range(100):
        rate = rng.uniform(0., 1., 1)
        jac = rng.normal(size=(1, 3))
        dconc = implicit_step(rate, jac, stoich, rng.uniform(0.01, 10.))
        drho = dconc * mu  # run_hydro.cpp:189-191, del_rho = del_conc / inv_mu
        worst = max(worst, abs(drho.sum()) / np.abs(drho).max())
    s = np.linspace(0., 1., 101)
    rows = [s]
    for ratio in (1., 10.):  # c_1/c_2 at fixed K = 1
        c2 = np.sqrt(s / ratio)
        c1 = ratio * c2
        rows.append([extent(a, b, 1.) for a, b in zip(c1, c2)])
        rows.append(1. - c1 * c2)  # the earlier law, K - c_1 c_2, clamped at 0 above saturation
    np.savetxt(os.path.join(HERE, "data", "kinetics_extent.csv"), np.column_stack(rows), delimiter=",",
               fmt="%.10e", header="S = c1 c2 / K; extent(c1=c2); eta(c1=c2); extent(c1=10 c2); eta(c1=10 c2); K = 1")
    return report("C4", worst < 1e-14,
                  "a mass-balanced reaction changes the species densities with zero net mass",
                  "max |sum_n mu_n dc_n| / max|mu_n dc_n| = %.1e over 100 random steps" % worst)


def main():
    checks = [check_C1_extent_root, check_C2_one_step_is_backward_euler, check_C3_no_overshoot,
              check_C4_species_update_keeps_mass]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
