"""Executable check of the cell and face forms of the gravity work (chapter 6, _cell.qmd and _face.qmd).

What is checked: the x1 gravity-work block of HydroImpl::forward (src/hydro/hydro_forward.cpp:790-898), the cell
work of ConstGravityImpl::forward (src/forcing/const_gravity.cpp:48-52) and the spherical-polar cell centre
radial_centers (src/coord/spherical_polar.cpp:17-21) at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported
line for line for one x1 column with non_hydrostatic = 1. Claims C1-C5. Writes data/cell_defect.csv and
data/face_order.csv for fig_cell_defect.py and fig_face_order.py.

Run: python3 cellface_check.py   (numpy only; exits with the number of failed claims)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
G = -10.  # grav1, nondimensional


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def column(xf, spherical):
    """face area, cell volume and cell centre of an x1 column (per unit area or per steradian)."""
    if spherical:
        rm, rp = xf[:-1], xf[1:]
        return xf**2, (rp**3 - rm**3) / 3., 0.75 * (rp**4 - rm**4) / (rp**3 - rm**3)
    return np.ones_like(xf), np.diff(xf), .5 * (xf[:-1] + xf[1:])


def face_work(F, xf, area, vol, xv, dt):  # hydro_forward.cpp:794-811 (is..ie = the whole column)
    phi_face, phi_cell = -G * xf, -G * xv
    div = (area[1:] * F[1:] - area[:-1] * F[:-1]) / vol
    pdiv = (area[1:] * F[1:] * phi_face[1:] - area[:-1] * F[:-1] * phi_face[:-1]) / vol
    return dt * (phi_cell * div - pdiv), div


def curvature(m, xv, area, vol, dt):  # hydro_forward.cpp:828-848, both x1 ends physical
    n = len(xv)
    K = np.zeros(n + 1)
    K[1:n] = (xv[1:] - xv[:-1]) / 12. * (m[1:] - m[:-1])
    return -dt * G * (area[1:] * K[1:] - area[:-1] * K[:-1]) / vol, K


def state(n, spherical, seed):
    rng = np.random.default_rng(seed)
    xf = np.linspace(5., 6., n + 1) if spherical else np.linspace(0., 1., n + 1)
    area, vol, xv = column(xf, spherical)
    rho, v = np.exp(-(xv - xv[0])) * (1. + .1 * rng.random(n)), .1 * rng.normal(size=n)
    F = np.r_[0., .5 * (rho[1:] * v[1:] + rho[:-1] * v[:-1]), 0.]  # a closed column's x1 mass flux
    return xf, area, vol, xv, rho, v, F


def check_C1_face_conserves():
    worst = 0.
    for spherical in (False, True):
        xf, area, vol, xv, rho, v, F = state(24, spherical, 1)
        dt = .01
        W, div = face_work(F, xf, area, vol, xv, dt)
        dpe = -G * xv * (-dt * div)  # PE_d change of the mass the fluxes move
        scale = np.sum(vol * np.abs(W))
        worst = max(worst, abs(np.sum(vol * (W + dpe))) / scale)
    return report("C1", worst < 1e-14, "the face form conserves E + PE_d exactly on a closed column",
                  "max |sum V (W^face + phi drho)| / sum V |W^face| = %.1e (Cartesian and spherical-polar)" % worst)


def check_C2_cell_defect():
    xf, area, vol, xv, rho, v, F = state(24, False, 2)
    dt = .01
    Wc = dt * rho * v * G  # const_gravity.cpp:50-51
    Wf, div = face_work(F, xf, area, vol, xv, dt)
    dpe = -G * xv * (-dt * div)
    defect = np.sum(vol * (Wc + dpe))
    same = abs(defect - np.sum(vol * (Wc - Wf))) <= 1e-15 * np.sum(vol * np.abs(Wc))
    bflux = F.copy()  # gravity-work: cell books the face work of F - F^R only (hydro_forward.cpp:784-788)
    zero = face_work(F - bflux, xf, area, vol, xv, dt)[0]
    np.savetxt(os.path.join(HERE, "data", "cell_defect.csv"), np.column_stack([xv, vol * (Wc - Wf)]),
               delimiter=",", fmt="%.10e", header="x1 centre, V (W^cell - W^face) per cell (24 cells, dt 0.01)")
    ok = same and abs(defect) > 1e-6 * np.sum(vol * np.abs(Wc)) and not zero.any()
    return report("C2", ok, "the cell form leaves an E + PE_d defect equal to sum V (W^cell - W^face); with F = F^R "
                  "cell mode books no face work", "defect / sum V |W^cell| = %.3e; face work of F - F^R: all zero"
                  % (defect / np.sum(vol * np.abs(Wc))))


def m_exact(x):
    return np.exp(-x) * np.sin(2.5 * x + .3)


def order_errors(n, curv):
    xf = np.linspace(0., 1., n + 1)
    area, vol, xv = column(xf, False)
    W, _ = face_work(m_exact(xf), xf, area, vol, xv, 1.)
    if curv:
        W = W + curvature(m_exact(xv), xv, area, vol, 1.)[0]
    gx, gw = np.polynomial.legendre.leggauss(10)
    ex = np.array([G * .5 * np.sum(gw * m_exact(.5 * (a + b) + .5 * (b - a) * gx)) for a, b in zip(xf[:-1], xf[1:])])
    e = np.abs(W - ex)
    return e[1:-1].max(), max(e[0], e[-1])


NS = (32, 64, 128, 256)


def slopes(errs):
    return [np.log2(errs[k] / errs[k + 1]) for k in range(len(errs) - 1)]


def check_C3_face_order():
    r = [order_errors(n, False) for n in NS]
    oi, ow = slopes([a for a, _ in r]), slopes([b for _, b in r])
    ok = min(oi[-2:]) > 1.95 and min(ow[-2:]) > 1.95
    return report("C3", ok, "the face form's work is second order against the exact cell average, interior and "
                  "wall cells", "orders interior %s, wall %s (n = 32..256)" % (["%.2f" % o for o in oi],
                                                                               ["%.2f" % o for o in ow]))


def check_C4_curvature_flux():
    r0 = [order_errors(n, False) for n in NS]
    r = [order_errors(n, True) for n in NS]
    oi, ow = slopes([a for a, _ in r]), slopes([b for _, b in r])
    xf, area, vol, xv, rho, v, F = state(24, True, 3)
    dK, K = curvature(rho * v, xv, area, vol, .01)
    tel = abs(np.sum(vol * dK)) / np.sum(vol * np.abs(dK))
    np.savetxt(os.path.join(HERE, "data", "face_order.csv"),
               np.column_stack([NS, [a for a, _ in r0], [b for _, b in r0], [a for a, _ in r], [b for _, b in r]]),
               delimiter=",", fmt="%.10e", header="n, face interior, face wall, face+K interior, face+K wall "
               "(max error of the booked work against the exact cell average, g1 = -10, x1 in [0, 1])")
    ok = min(oi[-2:]) > 3.9 and max(abs(o - 1.) for o in ow[-2:]) < .05 and tel < 1e-14 and K[0] == K[-1] == 0.
    return report("C4", ok, "the curvature flux makes the interior work fourth order, leaves the wall cells first "
                  "order, and sums to zero over the column", "orders interior %s, wall %s; |sum V div K| / "
                  "sum V |div K| = %.1e" % (["%.2f" % o for o in oi], ["%.2f" % o for o in ow], tel))


def check_C5_face_wallc():
    xf, area, vol, xv, rho, v, F = state(24, False, 4)
    dt = .01
    Wc = dt * rho * v * G
    Wf, div = face_work(F, xf, area, vol, xv, dt)
    corr = Wf - Wc  # hydro_forward.cpp:891
    corr[0] = corr[-1] = 0.  # face-wallc: :893-897
    booked = Wc + corr
    defect = np.sum(vol * (booked + (-G * xv) * (-dt * div)))
    want = vol[0] * (Wc[0] - Wf[0]) + vol[-1] * (Wc[-1] - Wf[-1])
    ok = abs(defect - want) < 1e-15 * np.sum(vol * np.abs(Wc)) and abs(defect) > 0.
    return report("C5", ok, "face-wallc keeps the cell work in the two wall cells, so its E + PE_d defect is "
                  "their cell-minus-face work", "defect %.3e, wall-cell difference %.3e" % (defect, want))


def main():
    checks = [check_C1_face_conserves, check_C2_cell_defect, check_C3_face_order, check_C4_curvature_flux,
              check_C5_face_wallc]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
