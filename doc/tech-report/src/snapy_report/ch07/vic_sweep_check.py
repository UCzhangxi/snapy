"""Executable check of the VIC block Thomas sweep (chapter 7, _vic-sweep.qmd).

What is checked: ForwardSweep (src/implicit/forward_sweep_impl.h:25-139), vic_backward_substitute
(src/implicit/vic_redistribute_impl.h:27-36) and the failed-column sentinel (src/implicit/vic_solve_failure.h:13-19)
at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported in vic_port.py. Claims C1-C4.

Run: python3 vic_sweep_check.py   (numpy only; exits with the number of failed claims)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vic_port as vp  # noqa: E402


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


rng = np.random.default_rng(5)


def random_system(n, N, dt=1.):
    a = np.array([np.eye(N) / dt + rng.normal(size=(N, N)) for _ in range(n)])
    b = rng.normal(size=(n, N, N)) * 0.3
    c = rng.normal(size=(n, N, N)) * 0.3
    return a, b, c


def dense(a, b, c):
    n, N = a.shape[:2]
    M = np.zeros((n * N, n * N))
    for k in range(n):
        M[k * N:(k + 1) * N, k * N:(k + 1) * N] = a[k]
        if k > 0:
            M[k * N:(k + 1) * N, (k - 1) * N:k * N] = b[k]
        if k < n - 1:
            M[k * N:(k + 1) * N, (k + 1) * N:(k + 2) * N] = c[k]
    return M


def check_C1_sweep_equals_dense_solve():
    out = []
    for N in (3, 5):
        a, b, c = random_system(60, N, dt=0.2)
        rhs = rng.normal(size=(60, N))
        ok, af, d = vp.forward_sweep(a, b, c, rhs)
        x = vp.backward_substitute(af, d)
        ref = np.linalg.solve(dense(a, b, c), rhs.ravel()).reshape(60, N)
        out.append(np.abs(x - ref).max() / np.abs(ref).max())
    return report("C1", max(out) < 1e-11, "forward sweep plus back substitution solves the block-tridiagonal system",
                  "60 layers: relative difference from a dense solve %.1e (N = 3), %.1e (N = 5)" % tuple(out))


def check_C2_rhs_is_the_explicit_tendency_over_dt():
    W = np.array([[1.2, 3., 0., 0., 9e4], [1., 2., 0., 0., 8e4], [.8, 1., 0., 0., 7e4], [.7, 0., 0., 0., 6e4]])
    gam = np.full(4, 1.4)
    area, vol = np.ones(3), np.ones(2) * 100.
    du = rng.normal(size=(2, 5)) * 1e-2
    errs = []
    for dt in (1e-3, 1e3):
        a, b, c = vp.assemble_full(W, gam, area, vol, dt)
        _, af, d = vp.forward_sweep(a, b, c, du / dt)
        delta = vp.backward_substitute(af, d)
        J = dense(a, b, c) - np.eye(10) / dt
        ref = np.linalg.solve(np.eye(10) + dt * J, du.ravel()).reshape(2, 5)
        errs.append(np.abs(delta - ref).max() / np.abs(ref).max())
    small = vp.backward_substitute(*vp.forward_sweep(*vp.assemble_full(W, gam, area, vol, 1e-9), du / 1e-9)[1:])
    lim = np.abs(small - du).max() / np.abs(du).max()
    ok = max(errs) < 1e-10 and lim < 1e-5
    return report("C2", ok, "with the right-hand side du/dt the sweep returns delta = (I + dt J)^-1 du, "
                  "and delta -> du as dt -> 0", "relative errors %.1e (dt = 1e-3), %.1e (dt = 1e3); "
                  "|delta - du| / |du| at dt = 1e-9: %.1e" % (errs[0], errs[1], lim))


def check_C3_singular_block_fails_the_whole_column():
    a, b, c = random_system(20, 5)
    # make the eliminated block at layer 12 exactly singular: a12 - b12 a'11 = 0 with a'11 from the sweep
    ok0, af, _ = vp.forward_sweep(a[:12], b[:12], c[:12], np.zeros((12, 5)))
    a[12] = b[12] @ af[11]
    ok, af2, d = vp.forward_sweep(a, b, c, rng.normal(size=(20, 5)))
    x = vp.backward_substitute(af2, d)
    ok_all = ok0 and not ok and np.isnan(d).all() and np.isnan(x).all()
    return report("C3", ok_all, "a singular eliminated block at layer 12 of 20 marks every layer of the column NaN, "
                  "and back substitution leaves the column untouched", "sweep ok = %s; NaN entries %d of %d"
                  % (ok, int(np.isnan(x).sum()), x.size))


def check_C4_serial_dependency():
    a, b, c = random_system(30, 5)
    rhs = rng.normal(size=(30, 5))
    _, af, d = vp.forward_sweep(a, b, c, rhs)
    x = vp.backward_substitute(af, d)
    rhs2 = rhs.copy()
    rhs2[0] += 1e-3
    _, af2, d2 = vp.forward_sweep(a, b, c, rhs2)
    x2 = vp.backward_substitute(af2, d2)
    moved = int((np.abs(x2 - x).max(1) > 0).sum())
    return report("C4", moved == 30, "every layer depends on every right-hand side: a change at the bottom reaches the top, "
                  "so the column is solved serially, one thread per column", "layers changed: %d of 30" % moved)


def main():
    checks = [check_C1_sweep_equals_dense_solve, check_C2_rhs_is_the_explicit_tendency_over_dt,
              check_C3_singular_block_fails_the_whole_column, check_C4_serial_dependency]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
