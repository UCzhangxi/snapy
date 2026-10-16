"""Executable check of the gravity work inside the vertical implicit operator (chapter 6, _vic.qmd).

What is checked: the energy row of vic_assemble_full_impl (src/implicit/vic_assemble_full_impl.h:38-40, 94-120),
the face weights work_lo / work_hi (src/implicit/implicit_hydro.cpp:239-242) and the projection and clamp work
(src/implicit/implicit_hydro.cpp:382-414) at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported line for line.
Variables are ordered as the code's: 0 density (IDN), 1 x1 momentum (IVX), 4 energy (IPR); the row of cell i is
a[i] q_i + b[i] q_{i-1} + c[i] q_{i+1}. Claims C1-C4.

Run: python3 vicwork_check.py   (numpy only; exits with the number of failed claims)
"""
import sys

import numpy as np

IDN, IVX, IPR = 0, 1, 4


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def energy_rows(Am, Ap, area_i, area_ip1, vol, grav, lower, upper, face_work, cartesian_face, diffusive_cell):
    """Rows IPR of a[i], b[i], c[i] from the gravity terms only (vic_assemble_full_impl.h:38-40, 94-120)."""
    phi = np.zeros((5, 5))
    phi[IVX, IDN] = grav  # :39
    phi[IPR, IVX] = grav  # :40
    a = -phi.copy()  # :94-96, the flux Jacobian parts are dropped: they are not gravity terms
    b = np.zeros((5, 5))
    c = np.zeros((5, 5))
    if face_work and cartesian_face:  # :101-108
        em = np.zeros(5)
        em[IVX] = 1.
        a[IPR, IVX] += grav
        a[IPR] -= 0.5 * grav * (em + 0.5 * (Ap[IDN] - Am[IDN]))
        b[IPR] -= 0.5 * grav * (0.5 * em + 0.5 * Am[IDN])
        c[IPR] -= 0.5 * grav * (0.5 * em - 0.5 * Ap[IDN])
    elif face_work or diffusive_cell:  # :109-120
        a[IPR] -= grav * (upper * Ap[IDN] - lower * Am[IDN])
        b[IPR] -= grav * lower * Am[IDN]
        c[IPR] += grav * upper * Ap[IDN]
        if face_work:
            a[IPR, IVX] += grav * (1. - lower - upper)
            b[IPR, IVX] -= grav * lower
            c[IPR, IVX] -= grav * upper
    return a[IPR], b[IPR], c[IPR]


def linear_face_work(Am, Ap, grav, lower, upper):
    """Minus the face work 2g (upper F_{i+1/2} + lower F_{i-1/2}) of the operator's own linearised mass flux
    F_{i+1/2} = (m_i + m_{i+1})/2 - (Ap[IDN] . (q_{i+1} - q_i))/2, as coefficients on q_{i-1}, q_i, q_{i+1}."""
    em = np.zeros(5)
    em[IVX] = 1.
    # 2 g upper F_{i+1/2} = g upper (m_i + m_{i+1}) - g upper Ap(q_{i+1} - q_i)
    ci = grav * upper * (em + Ap[IDN])
    cn = grav * upper * (em - Ap[IDN])
    # 2 g lower F_{i-1/2} = g lower (m_{i-1} + m_i) - g lower Am(q_i - q_{i-1})
    ci = ci + grav * lower * (em - Am[IDN])
    cp = grav * lower * (em + Am[IDN])
    return -cp, -ci, -cn


def check_C1_face_rows_are_face_work():
    rng = np.random.default_rng(1)
    worst = 0.
    for _ in range(200):
        Am, Ap = rng.normal(size=(5, 5)), rng.normal(size=(5, 5))
        grav, lower, upper = -rng.uniform(1., 30.), rng.uniform(.05, .45), rng.uniform(.05, .45)
        a, b, c = energy_rows(Am, Ap, 1., 1., 1., grav, lower, upper, True, False, False)
        pb, pa, pc = linear_face_work(Am, Ap, grav, lower, upper)
        worst = max(worst, np.abs(a - pa).max(), np.abs(b - pb).max(), np.abs(c - pc).max())
    return report("C1", worst < 1e-12, "with gravity-work: face the energy row is minus the face work of the "
                  "operator's own linearised mass flux", "max |row - (-W^face)| = %.1e over 200 random rows" % worst)


def check_C2_cartesian_rows():
    rng = np.random.default_rng(2)
    xf = np.cumsum(np.r_[0., rng.uniform(.5, 2., 12)])  # non-uniform Cartesian column
    x1v = .5 * (xf[:-1] + xf[1:])
    area = np.ones(13)
    vol = area[:-1] * np.diff(xf)
    lo = .5 * area[:-1] * (x1v - xf[:-1]) / vol  # implicit_hydro.cpp:239-240
    hi = .5 * area[1:] * (xf[1:] - x1v) / vol  # :241-242
    worst_w = max(np.abs(lo - .25).max(), np.abs(hi - .25).max())
    worst = 0.
    for _ in range(200):
        Am, Ap = rng.normal(size=(5, 5)), rng.normal(size=(5, 5))
        g = -rng.uniform(1., 30.)
        r1 = energy_rows(Am, Ap, 1., 1., 1., g, .25, .25, True, True, False)
        r2 = energy_rows(Am, Ap, 1., 1., 1., g, .25, .25, True, False, False)
        worst = max(worst, *(np.abs(x - y).max() for x, y in zip(r1, r2)))
    return report("C2", worst_w < 1e-15 and worst < 1e-12, "on a Cartesian column both weights are 1/4 to round-off, "
                  "and the Cartesian rows are the general rows with exactly 1/4 written in",
                  "max |weight - 1/4| = %.1e on a non-uniform column; max row difference %.1e" % (worst_w, worst))


def check_C3_cell_mode_rows():
    rng = np.random.default_rng(3)
    Am, Ap = rng.normal(size=(5, 5)), rng.normal(size=(5, 5))
    g, lo, hi = -9.8, .2, .3
    a, b, c = energy_rows(Am, Ap, 1., 1., 1., g, lo, hi, False, False, True)
    a0, b0, c0 = energy_rows(Am, Ap, 1., 1., 1., g, lo, hi, False, False, False)
    ok = a0[IVX] == -g and a[IVX] == -g - g * (hi * Ap[IDN, IVX] - lo * Am[IDN, IVX]) and abs(
        b[IDN] + g * lo * Am[IDN, IDN]) < 1e-15
    return report("C3", ok, "with gravity-work: cell the energy row keeps the cell work g m_i and adds only the "
                  "dissipative |A| part of the face work", "momentum entry of a: plain %.2f, with the |A| part %.4f"
                  % (a0[IVX], a[IVX]))


def check_C4_projection_and_clamp():
    rng = np.random.default_rng(4)
    n, g = 10, -9.8
    xf = np.linspace(0., 10., n + 1)
    x1v = .5 * (xf[:-1] + xf[1:])
    vol = np.diff(xf)
    requested = np.r_[0., rng.normal(size=n - 1), 0.]  # face masses; closed walls
    explicit = rng.normal(size=n)
    projected = (requested[:-1] - requested[1:]) / vol
    raw = explicit + projected  # the solve applied exactly
    phi = -g * x1v
    projection = phi * (raw - explicit - projected)  # implicit_hydro.cpp:402-403
    moved = np.r_[0., rng.normal(size=n - 1) * 1e-3, 0.]  # moved minus requested, walls sealed
    dp_lo, dp_hi = -g * (xf[:-1] - x1v), -g * (xf[1:] - x1v)
    clamp = -(dp_hi * moved[1:] - dp_lo * moved[:-1]) / vol  # :405-411
    dm = (moved[:-1] - moved[1:]) / vol  # the mass the clamp moved
    total = np.sum(vol * (clamp + phi * dm))  # energy plus PE change of the clamp, closed column
    ok = np.abs(projection).max() < 1e-12 and abs(total) < 1e-12
    return report("C4", ok, "the projection work vanishes when the solve is applied exactly, and the clamp work "
                  "keeps E + PE_d over a closed column", "max |projection work| = %.1e; sum V (W_clamp + phi dm) = %.1e"
                  % (np.abs(projection).max(), total))


def main():
    checks = [check_C1_face_rows_are_face_work, check_C2_cartesian_rows, check_C3_cell_mode_rows,
              check_C4_projection_and_clamp]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
