"""Executable check of the output-field diagnostics (chapter 13, _output-diag.qmd).

What is checked: interp_to_face and the divergence fields of OutputType::loadDiagOutputData
(src/output/load_diag_output_data.cpp:22-45, 166-205), the virtual potential temperature (:101-104) and the
column path (:262-282) at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported to numpy on a Cartesian grid.
C5 ports the round-off path of the div field at snapy@6fbb39750f62b83df096058a4746e77d0a634bc5: the face mean
(load_diag_output_data.cpp:42), face_area1 (src/coord/coordinate.cpp:425-427), the face products and their difference
in CoordinateImpl::divergence (:535-537), cell_volume (:437-440) and the division (:552), against exact rationals.
Claims C1-C5.

Run: python3 output_diag_check.py   (numpy only; exits with the number of failed claims)
"""
import sys
from fractions import Fraction

import numpy as np


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def interp_to_face(v):
    """Face k (the lower face of cell k) holds the mean of cells k-1 and k; face 0 copies cell 0."""
    f = np.empty_like(v)
    f[0] = v[0]
    f[1:] = 0.5 * (v[:-1] + v[1:])
    return f


def div1(v, dx):
    """Cartesian divergence on interior cells 1..n-2 from the lower faces k and k+1."""
    f = interp_to_face(v)
    return (f[2:-1] - f[1:-2]) / dx


def check_C1_face_values():
    x = np.linspace(0.5, 9.5, 10)
    v = 3. * x + 1.
    f = interp_to_face(v)
    xf = x - 0.5
    ok = np.allclose(f[1:], 3. * xf[1:] + 1., rtol=0, atol=1e-13) and f[0] == v[0]
    return report("C1", ok, "a linear field is exact on every face but the first, which copies its cell",
                  "face 0 = %.1f (cell value; the linear value is %.1f); max error elsewhere %.1e"
                  % (f[0], 3. * xf[0] + 1., np.abs(f[1:] - 3. * xf[1:] - 1.).max()))


def check_C2_divergence():
    dx = 0.5
    x = np.arange(12) * dx + dx / 2
    d0 = np.abs(div1(np.full(12, 7.), dx)).max()
    d1 = np.abs(div1(2.5 * x, dx) - 2.5).max()
    ok = d0 == 0. and d1 < 1e-13
    return report("C2", ok, "div of a uniform velocity is 0 and of v1 = 2.5 x1 is 2.5 in the interior",
                  "max |div| uniform %.1e; max |div - 2.5| linear %.1e" % (d0, d1))


def check_C3_virtual_potential_temperature():
    Rd, T, rho = 287.0, 280., 1.1
    theta = 300.
    p_dry = rho * Rd * T
    p_moist = rho * 1.02 * Rd * T
    tv_dry = theta * p_dry / (rho * Rd * T)
    tv_moist = theta * p_moist / (rho * Rd * T)
    ok = tv_dry == theta and abs(tv_moist / theta - 1.02) < 1e-15
    return report("C3", ok, "theta_v = theta p / (rho R_d T): equal to theta for dry air, theta times R/R_d otherwise",
                  "dry %.12g, R = 1.02 R_d: %.12g" % (tv_dry, tv_moist))


def check_C4_column_path():
    dz = np.array([100., 150., 200., 250.])
    rho_y = np.array([1e-2, 5e-3, 2e-3, 1e-3])
    area = 4.0
    path = (rho_y * dz * area).sum() / area
    want = (rho_y * dz).sum()
    return report("C4", abs(path - want) < 1e-15, "path_<species> = sum rho_y V / A_bottom is the column mass per "
                  "unit area on a Cartesian column", "path %.6g kg m^-2, sum rho_y dz %.6g" % (path, want))


def check_C5_divergence_roundoff(trials=4000, n=8, seed=5):
    """Float64 div on a Cartesian block with non-dyadic spacings, against the exact value of the same inputs."""
    rng = np.random.default_rng(seed)
    eps = np.finfo(float).eps
    worst = 0.
    for _ in range(trials):
        v = rng.uniform(-1, 1, n) * 10.0 ** rng.integers(-3, 3)
        dx1, dx2, dx3 = rng.uniform(0.1, 2.0, 3)
        face = interp_to_face(v)
        area = dx3 * dx2                       # face_area1
        vol = dx3 * (dx2 * dx1)                # cell_volume, einsum(dx3, dx2 outer dx1)
        fv = [Fraction(x) for x in v]
        ff = [fv[0]] + [(fv[k - 1] + fv[k]) / 2 for k in range(1, n)]
        ax = Fraction(dx3) * Fraction(dx2)
        vx = ax * Fraction(dx1)
        for i in range(1, n - 1):
            q = (area * face[i + 1] - area * face[i]) / vol
            exact = (ax * ff[i + 1] - ax * ff[i]) / vx
            scale = Fraction(max(abs(v[i - 1]), abs(v[i]), abs(v[i + 1]))) / Fraction(dx1)
            worst = max(worst, float(abs(Fraction(q) - exact) / scale) / eps)
    ok = 2. < worst <= 7.
    return report("C5", ok, "div round-off is within 7 eps_m max|v1|/dx1 (14 roundings of eps_m/2); "
                  "the 2 eps_m bound that omits the face area and the volume is exceeded",
                  "max |error| / (eps_m max|v1|/dx1) over %d x %d cells: %.3f" % (trials, n - 2, worst))


def main():
    checks = [check_C1_face_values, check_C2_divergence, check_C3_virtual_potential_temperature, check_C4_column_path,
              check_C5_divergence_roundoff]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
