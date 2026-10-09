"""The momentum side of the same offset: the x1 pressure force at rest (README section 4).

main's net radial pressure force per volume, after spherical_polar.cpp's face_pressure1 source,
is  -(p+ - p-)/dx1f  (the divergence's (A+p+ - A-p-)/V cancels against the source's own).
The cell average needs the r^2 mean of -dp/dr.  Three states, isentropic column, g = 1:
  (a) cell-average IC + continuum faces (a reference fixed to 4th order): main's force leaves
      the imbalance  -(p+ - p-)/h - g rho_c = +delta_v p'' = -g delta_v rho'  -> O(h^2/R);
  (b) main's own well-balanced state: scanned faces p(r_f + delta_v), so the imbalance is zero
      by construction, and the face pressure is off by delta_v p' instead;
  (c) the consistent force: -(1/V) int r^2 d_r p~ dr, p~ the degree-5 interpolant of the six
      nearest face pressures, i.e. the geometric source (2/V) int r p~ dr in place of
      (A+p+ - A-p-)/V - (p+ - p-)/dx1f:  with (a)'s faces the imbalance is O(h^4) or smaller."""
import numpy as np
from numpy.polynomial.legendre import leggauss
from replica import background, cell_avg, wb_faces, recon_weights

XG, WG = leggauss(8)


def imbalance(R, nz):
    T, p, rho = background(R)
    ng, h = 3, 1.0 / nz
    rf = R + h * np.arange(nz + 1)
    rm, rp = rf[:-1], rf[1:]
    V = h * (rm**2 + rm * rp + rp**2) / 3
    rho_c, p_c = cell_avg(rho, rf), cell_avg(p, rf)
    pf = p(rf)
    main = -(pf[1:] - pf[:-1]) / h - rho_c                      # (a)
    rfe = R + h * np.arange(-ng, nz + ng + 1)
    pfw, _ = wb_faces(p_c, rho_c, h, nz, ng, recon_weights(rfe, ng, "cart"))
    wb_face_err = pfw - pf                                       # (b)
    cons = np.zeros(nz)                                          # (c)
    for i in range(nz):
        s0 = min(max(i - 2, 0), nz - 5)
        c = np.polyfit(rf[s0:s0 + 6] - rf[s0], pf[s0:s0 + 6], 5)
        dc = np.polyder(c)
        r = 0.5 * (rm[i] + rp[i]) + 0.5 * h * XG
        cons[i] = -(np.polyval(dc, r - rf[s0]) * r**2 * WG).sum() * 0.5 * h / V[i] - rho_c[i]
    rmid = 0.5 * (rm + rp)
    pred = -(h**2 / (6 * rmid)) * np.gradient(rho(rmid), rmid)  # -g delta_v rho'
    sl = slice(3, nz - 3)
    return (np.abs(main[sl]).max(), np.abs(main - pred)[sl].max(), np.abs(wb_face_err).max(),
            np.abs(cons[sl]).max())


print("max interior |imbalance| / g rho scale, and the WB face-pressure offset")
print(f"{'R':>5} {'nz':>5} {'(a) main':>11} {'R nz^2 (a)':>11} {'(a)-pred':>11} "
      f"{'(b) R nz^2 dp_f':>16} {'(c) consistent':>15}")
for R in (5., 20.):
    for nz in (32, 64, 128, 256):
        a, ap, b, c = imbalance(R, nz)
        print(f"{R:5g} {nz:5d} {a:11.3e} {a * R * nz**2:11.4f} {ap:11.3e} {b * R * nz**2:16.4f} {c:15.3e}")
