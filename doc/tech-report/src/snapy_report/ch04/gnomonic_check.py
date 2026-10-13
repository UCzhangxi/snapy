"""Executable check of the gnomonic equiangle cell geometry (chapter 4, _gnomonic.qmd).

What is checked: the exact solid angle of a cell's x1 face as the corner sum of
atan(x y / sqrt(1 + x^2 + y^2)), x = tan x2f, y = tan x3f (solid_angle_kj, src/coord/gnomonic_equiangle.cpp:124-137
at snapy@6fbb39750f62b83df096058a4746e77d0a634bc5), ported to numpy. Claims C1-C3.

Run: python3 gnomonic_check.py   (numpy only; exits with the number of failed claims)
"""
import sys

import numpy as np


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def solid_angles(x2f, x3f):
    xc = np.tan(x2f)[None, :]
    yc = np.tan(x3f)[:, None]
    corner = np.arctan(xc * yc / np.sqrt(1. + xc * xc + yc * yc))
    return corner[1:, 1:] - corner[1:, :-1] - corner[:-1, 1:] + corner[:-1, :-1]


def quad(a2, b2, a3, b3, n=64):
    """Gauss-Legendre quadrature of the solid-angle density (1 + x^2 + y^2)^(-3/2) over the cube-face rectangle."""
    g, w = np.polynomial.legendre.leggauss(n)
    xa, xb, ya, yb = np.tan(a2), np.tan(b2), np.tan(a3), np.tan(b3)
    x = 0.5 * (xb - xa) * g + 0.5 * (xb + xa)
    y = 0.5 * (yb - ya) * g + 0.5 * (yb + ya)
    X, Y = np.meshgrid(x, y)
    W = np.outer(w, w) * 0.25 * (xb - xa) * (yb - ya)
    return (W * (1. + X * X + Y * Y) ** -1.5).sum()


def check_C1_panel_sums_to_four_pi_over_six():
    rng = np.random.default_rng(3)
    worst = 0.
    for n in (4, 16, 64):
        x2f = np.sort(np.concatenate([[-np.pi / 4, np.pi / 4], rng.uniform(-np.pi / 4, np.pi / 4, n - 1)]))
        x3f = np.linspace(-np.pi / 4, np.pi / 4, n + 1)
        worst = max(worst, abs(6. * solid_angles(x2f, x3f).sum() - 4. * np.pi))
    return report("C1", worst < 1e-12, "the cells of a panel sum to 4 pi / 6 for any partition, so six panels give "
                  "4 pi: the corner differences telescope", "max |6 sum - 4 pi| over 3 random partitions %.1e" % worst)


def check_C2_cell_is_exact_not_quadrature():
    x2f = np.linspace(-np.pi / 4, np.pi / 4, 9)
    x3f = np.linspace(-np.pi / 4, np.pi / 4, 9)
    om = solid_angles(x2f, x3f)
    worst = max(abs(om[k, j] - quad(x2f[j], x2f[j + 1], x3f[k], x3f[k + 1])) / om[k, j]
                for k in range(8) for j in range(8))
    return report("C2", worst < 1e-13, "each cell's corner formula equals the solid-angle integral over its "
                  "cube-face rectangle (64-point Gauss reference)", "max relative difference over 64 cells %.1e" % worst)


def check_C3_shell_volume():
    x = np.linspace(-np.pi / 4, np.pi / 4, 7)
    om = solid_angles(x, x)
    r = np.array([1.0, 1.3, 1.9, 2.0])
    vol = 6. * om.sum() * ((r[1:] ** 3 - r[:-1] ** 3) / 3.).sum()
    want = 4. / 3. * np.pi * (r[-1] ** 3 - r[0] ** 3)
    return report("C3", abs(vol / want - 1.) < 1e-14, "solid angle times (r_+^3 - r_-^3)/3, summed over six panels "
                  "and three shells, is the shell volume", "relative difference %.1e" % abs(vol / want - 1.))


def main():
    checks = [check_C1_panel_sums_to_four_pi_over_six, check_C2_cell_is_exact_not_quadrature, check_C3_shell_volume]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
