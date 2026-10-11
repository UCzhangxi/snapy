"""Executable check of the VIC column closure (chapter 7, _vic-closure.qmd).

What is checked: the closure a += b Bnd at the bottom and a += c Bnd at the top, Bnd = diag(1, -1, 1, 1, 1)
(src/implicit/vic_assemble_full_impl.h:44-45, 122-126; vic_assemble_partial_impl.h:50, 142-144 at
snapy@e894700ff7aee30b52882e5202b16461413780b0), ported in vic_port.py with grav = 0. Claims C1-C4.

Run: python3 vic_closure_check.py   (numpy only; exits with the number of failed claims)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vic_port as vp  # noqa: E402


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


rng = np.random.default_rng(11)
BND = np.diag([1., -1., 1., 1., 1.])


def sealed_column(n=8):
    """A moving, layered column whose ghosts mirror the first and last interior cells."""
    W = np.zeros((n + 2, 5))
    W[1:-1, vp.IDN] = np.exp(-np.linspace(0., 2., n))
    W[1:-1, vp.IVX] = rng.uniform(-40., 40., n)
    W[1:-1, vp.IVY] = rng.uniform(-20., 20., n)
    W[1:-1, vp.IPR] = 1e5 * np.exp(-np.linspace(0., 2.2, n))
    gam = np.full(n + 2, 1.4)
    for g, i in ((0, 1), (n + 1, n)):
        W[g] = W[i]
        W[g, vp.IVX] = -W[i, vp.IVX]
    area = np.full(n + 1, 1.)
    vol = rng.uniform(80., 120., n)
    return W, gam, area, vol


def apply(a, b, c, d, dt):
    """The operator minus I/dt: (a - I/dt) d_i + b d_{i-1} + c d_{i+1}, with nothing outside the column."""
    n = len(d)
    out = np.array([(a[i] - np.eye(5) / dt) @ d[i] for i in range(n)])
    out[1:] += np.einsum("kij,kj->ki", b[1:], d[:-1])
    out[:-1] += np.einsum("kij,kj->ki", c[:-1], d[1:])
    return out


def check_C1_closure_is_a_mirror_ghost():
    W, gam, area, vol = sealed_column()
    n, dt = len(vol), 5.
    a, b, c = vp.assemble_full(W, gam, area, vol, dt)
    a0, b0, c0 = vp.assemble_full(W, gam, area, vol, dt, first_block=False, last_block=False)
    rhs = rng.normal(size=(n, 5))
    _, af, df = vp.forward_sweep(a, b, c, rhs)
    d = vp.backward_substitute(af, df)
    # the open system with the two ghost unknowns eliminated by d_ghost = Bnd d_edge
    M = np.zeros((5 * n, 5 * n))
    for k in range(n):
        M[5 * k:5 * k + 5, 5 * k:5 * k + 5] = a0[k]
        if k > 0:
            M[5 * k:5 * k + 5, 5 * k - 5:5 * k] = b0[k]
        if k < n - 1:
            M[5 * k:5 * k + 5, 5 * k + 5:5 * k + 10] = c0[k]
    M[:5, :5] += b0[0] @ BND
    M[-5:, -5:] += c0[-1] @ BND
    ref = np.linalg.solve(M, rhs.ravel()).reshape(n, 5)
    err = np.abs(d - ref).max() / np.abs(ref).max()
    return report("C1", err < 1e-12, "a += b Bnd at the bottom (c Bnd at the top) is the ghost d_0 = Bnd d_1 eliminated",
                  "relative difference from the explicit-ghost solve %.1e" % err)


def check_C2_sealed_column_conserves():
    W, gam, area, vol = sealed_column()
    n, dt = len(vol), 5.
    a, b, c = vp.assemble_full(W, gam, area, vol, dt)
    worst = np.zeros(5)
    for _ in range(50):
        d = rng.normal(size=(n, 5)) * np.array([1e-3, 1e-1, 1e-1, 1e-1, 1e2])
        tot = (apply(a, b, c, d, dt) * vol[:, None]).sum(0)
        scale = (np.abs(apply(a, b, c, d, dt)) * vol[:, None]).sum(0)
        worst = np.maximum(worst, np.abs(tot) / scale)
    ok = max(worst[[0, 2, 3, 4]]) < 1e-13 and worst[1] > 1e-3
    return report("C2", ok, "with the closure, the column sums of the mass, transverse momentum and energy rows vanish; "
                  "normal momentum keeps the wall pressure",
                  "|sum V (op d)| / sum V |op d| over 50 random d: rho %.1e, rho u %.1e, rho v %.1e, rho w %.1e, E %.1e"
                  % tuple(worst))


def check_C3_open_ends_leak():
    W, gam, area, vol = sealed_column()
    n, dt = len(vol), 5.
    a0, b0, c0 = vp.assemble_full(W, gam, area, vol, dt, first_block=False, last_block=False)
    d = rng.normal(size=(n, 5)) * np.array([1e-3, 1e-1, 1e-1, 1e-1, 1e2])
    op = apply(a0, b0, c0, d, dt) * vol[:, None]
    leak = abs(op[:, 0].sum()) / np.abs(op[:, 0]).sum()
    return report("C3", leak > 1e-3, "without the closure (ghost d = 0), the column loses mass through its ends",
                  "|sum V (op d)_rho| / sum V |(op d)_rho| = %.2e" % leak)


def check_C4_mirror_wall_face_is_at_rest():
    W, gam, area, vol = sealed_column()
    worst = 0.
    for g, i in ((0, 1), (-1, -2)):
        p = vp.roe_average(0.4, W[g], W[i])
        worst = max(worst, abs(p[vp.IVX]) / abs(W[i, vp.IVX]))
    return report("C4", worst < 1e-15, "the Roe state at a mirror wall face has zero normal velocity",
                  "|u_Roe| / |u_edge| at the two walls: %.1e" % worst)


def main():
    checks = [check_C1_closure_is_a_mirror_ghost, check_C2_sealed_column_conserves, check_C3_open_ends_leak,
              check_C4_mirror_wall_face_is_at_rest]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
