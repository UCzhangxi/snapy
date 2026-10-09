"""Discrete rest-state residual of snapy's x2/x3 momentum rows, with and
without the centroid shift  F -> F - delta * D1(F)  on the x2/x3 pressure flux.

Replicates, operator by operator, at chengcli/snapy 117e449 (+ e7f9904's delta):
  spherical-polar : spherical_polar.cpp  reset(), face_area2/3, cell_volume,
                    forward():  div[IVY] -= coord_src1_i*coord_src1_j*(rho vz^2 + p)
  gnomonic panel  : gnomonic_equiangle.cpp reset() (dx*_ang_*, sine/cosine_*),
                    face_area1/2/3, trapezoid cell_volume, x_ov_rD_kji,
                    y_ov_rC_kji, flux2global2_/3_ (non-orthogonal g23), and
                    forward(): div[IVY] -= x_ov_rD*(p + ...), div[IVZ] -= y_ov_rC*(p + ...)
  both            : CoordinateImpl::divergence (A_{j+1}F_{j+1} - A_j F_j)/V,
                    LMARS at rest (pbar = (pL+pR)/2, every u-term exactly 0),
                    delta = radial_face_centroid_shift_ (e7f9904, exact form),
                    D1 = centred difference over x1v, interior x1 only (e7f9904).
Tendency = -div + src (snapy: div -= src, then du = -dt*div).

Cases
  A  baseline (no correction)
  B  flux corrected, source unchanged         (what "add delta*D1(p) to the flux" does alone)
  C  flux corrected AND source weight p -> p - delta*D1(p)   (area-measure source)
Prints max |tendency| on interior cells, relative to max |G p| (G the geometric
source factor), and checks that B's residual is exactly +delta*D1(p)*G.
Also: uniform-tracer test (non-rest flow) and the rest-state zero of the
mass/tracer/energy corrections.  CPU: < 1 s.
"""
import numpy as np

np.set_printoptions(precision=3)
NG = 2


def radial_grid(R0, H, nx1, uniform_dx=None):
    h = H / nx1
    x1f = R0 + h * np.arange(-NG, nx1 + NG + 1)
    return x1f


def delta_shift(x1f):
    rm, rp = x1f[:-1], x1f[1:]
    h = rp - rm
    rb = 0.5 * (rm + rp)
    h2, t = h * h, 12 * rb * rb
    return h2 * (t - h2) / (12 * rb * (t + h2))


def D1(f, x1v):
    """centred x1 difference, zero on the two edge cells (as e7f9904)"""
    out = np.zeros_like(f)
    out[..., 1:-1] = (f[..., 2:] - f[..., :-2]) / (x1v[2:] - x1v[:-2])
    return out


def mask_interior(f):
    out = np.zeros_like(f)
    out[..., NG:-NG] = f[..., NG:-NG]
    return out


def pressure_profile(r, R0):
    # any smooth hydrostatic p(r): isothermal, g ~ 1/r^2, scale height 0.1 R0
    Hs = 0.1 * R0
    return np.exp(-(R0 / Hs) * (1.0 - R0 / r))


# ------------------------------------------------------------------ spherical
def spherical(R0=1.0, H=0.5, nx1=32, nx2=24, nx3=8, th=(0.4, 2.7)):
    x1f = radial_grid(R0, H, nx1)
    rm, rp = x1f[:-1], x1f[1:]
    x1v = 0.75 * (rp**4 - rm**4) / (rp**3 - rm**3)            # radial_centers
    x2f = np.linspace(th[0], th[1], nx2 + 1)
    x3f = np.linspace(0.0, 0.6, nx3 + 1)
    dx3f = np.diff(x3f)
    radial_volume = (rp**3 - rm**3) / 3.0
    radial_area23 = 0.5 * (rp**2 - rm**2)
    tm, tp = x2f[:-1], x2f[1:]
    polar_volume = np.abs(np.cos(tm) - np.cos(tp))
    c1i = (radial_area23 / radial_volume)[None, None, :]
    c1j = ((np.abs(np.sin(tp)) - np.abs(np.sin(tm))) / polar_volume)[None, :, None]
    A2 = radial_area23[None, None, :] * np.abs(np.sin(x2f))[None, :, None] * dx3f[:, None, None]
    A3 = np.broadcast_to(radial_area23[None, None, :] * np.diff(x2f)[None, :, None],
                         (nx3 + 1, nx2, x1v.size))
    V = radial_volume[None, None, :] * polar_volume[None, :, None] * dx3f[:, None, None]

    p = np.broadcast_to(pressure_profile(x1v, R0), (nx3, nx2, x1v.size)).copy()
    dl = delta_shift(x1f)

    # x2 faces: LMARS pbar at rest, faces 0..nx2 (wall faces use the inner value)
    pl = np.concatenate([p[:, :1], p], axis=1)
    pr = np.concatenate([p, p[:, -1:]], axis=1)
    pbar2 = 0.5 * (pl + pr)
    pbar3 = 0.5 * (np.concatenate([p[:1], p], 0) + np.concatenate([p, p[-1:]], 0))
    G = c1i * c1j

    out = {}
    for case in 'ABC':
        F2 = pbar2 - (dl * D1(pbar2, x1v) if case in 'BC' else 0.0)
        F3 = pbar3 - (dl * D1(pbar3, x1v) if case in 'BC' else 0.0)
        P = p - (dl * D1(p, x1v) if case == 'C' else 0.0)
        div2 = (A2[:, 1:] * F2[:, 1:] - A2[:, :-1] * F2[:, :-1]) / V
        div3 = (A3[1:] * F3[1:] - A3[:-1] * F3[:-1]) / V
        resY = mask_interior(-div2 + G * P)          # theta row (IVY)
        resZ = mask_interior(-div3)                  # phi row (IVZ): no pressure source
        out[case] = (resY, resZ)
    scale = np.abs(mask_interior(G * p)).max()
    pred = mask_interior(+dl * D1(p, x1v) * G)       # predicted case-B residual
    return out, scale, pred, x1f


# ------------------------------------------------------------------ gnomonic
def gnomonic(R0=1.0, H=0.5, nx1=32, nx=16, panel=(-np.pi / 4, np.pi / 4)):
    x1f = radial_grid(R0, H, nx1)
    dx1f = np.diff(x1f)
    x1v = 0.5 * (x1f[:-1] + x1f[1:])                            # arithmetic on this grid
    x2f = np.linspace(*panel, nx + 1)
    x3f = np.linspace(*panel, nx + 1)
    x2v, x3v = 0.5 * (x2f[1:] + x2f[:-1]), 0.5 * (x3f[1:] + x3f[:-1])
    # --- reset(): shapes (k, j, 1)
    x = np.tan(x2v)[None, :, None]; xf = np.tan(x2f)[None, :, None]
    y = np.tan(x3v)[:, None, None]; yf = np.tan(x3f)[:, None, None]
    C, Cf, D, Df = np.sqrt(1 + x * x), np.sqrt(1 + xf * xf), np.sqrt(1 + y * y), np.sqrt(1 + yf * yf)
    sine_cell = np.sqrt(1 + x * x + y * y) / (C * D)
    cos_f2 = -xf * y / (Cf * D); sin_f2 = np.sqrt(1 + xf * xf + y * y) / (Cf * D)
    cos_f3 = -x * yf / (C * Df); sin_f3 = np.sqrt(1 + x * x + yf * yf) / (C * Df)
    x1_ = np.tan(x2f[:-1])[None, :, None]; x2_ = np.tan(x2f[1:])[None, :, None]
    d1 = np.sqrt(1 + x1_**2 + y * y); d2 = np.sqrt(1 + x2_**2 + y * y)
    d1f = np.sqrt(1 + x1_**2 + yf * yf); d2f = np.sqrt(1 + x2_**2 + yf * yf)
    dx2f_ang = np.arccos((1 + x1_ * x2_ + y * y) / (d1 * d2))
    dx2f_ang_face3 = np.arccos((1 + x1_ * x2_ + yf * yf) / (d1f * d2f))
    y1 = np.tan(x3f[:-1])[:, None, None]; y2 = np.tan(x3f[1:])[:, None, None]
    d1 = np.sqrt(1 + x * x + y1**2); d2 = np.sqrt(1 + x * x + y2**2)
    d1f = np.sqrt(1 + xf * xf + y1**2); d2f = np.sqrt(1 + xf * xf + y2**2)
    dx3f_ang = np.arccos((1 + x * x + y1 * y2) / (d1 * d2))
    dx3f_ang_face2 = np.arccos((1 + xf * xf + y1 * y2) / (d1f * d2f))
    rad23 = (x1v * dx1f)[None, None, :]
    A1 = (x1f * x1f)[None, None, :] * (dx2f_ang * dx3f_ang * sine_cell)
    A2 = rad23 * dx3f_ang_face2                                  # (k, j+1/2, i)
    A3 = rad23 * dx2f_ang_face3                                  # (k+1/2, j, i)
    V = 0.5 * (A1[..., :-1] + A1[..., 1:]) * dx1f[None, None, :]  # TRAPEZOID, as coded
    fx, fy = A2 * sin_f2, A3 * sin_f3
    x_ov_rD = (fx[:, 1:] - fx[:, :-1]) / V
    y_ov_rC = (fy[1:] - fy[:-1]) / V

    def flux2global2(txx, txy, txz):           # gnomonic_equiangle.cpp flux2global2_
        g23, gi22, g33 = cos_f2, 1.0 / (sin_f2 * sin_f2), 1.0
        T22 = np.sqrt(gi22); T32 = -np.sqrt(gi22) * g23 / g33; T33 = 1.0 / np.sqrt(g33)
        fz = T32 * txy + T33 * txz; fyy = T22 * txy
        ty, tz = fyy, fz
        return txx, ty + tz * cos_f2, tz + ty * cos_f2

    def flux2global3(txx, txy, txz):           # flux2global3_
        g22, g23, gi33 = 1.0, cos_f3, 1.0 / (sin_f3 * sin_f3)
        T22 = 1.0 / np.sqrt(g22); T23 = -g23 / g22 * np.sqrt(gi33); T33 = np.sqrt(gi33)
        fyy = T22 * txy + T23 * txz; fz = T33 * txz
        ty, tz = fyy, fz
        return txx, ty + tz * cos_f3, tz + ty * cos_f3

    n1 = x1v.size
    p = np.broadcast_to(pressure_profile(x1v, R0), (nx, nx, n1)).copy()
    dl = delta_shift(x1f)
    pbar2 = 0.5 * (np.concatenate([p[:, :1], p], 1) + np.concatenate([p, p[:, -1:]], 1))
    pbar3 = 0.5 * (np.concatenate([p[:1], p], 0) + np.concatenate([p, p[-1:]], 0))
    z2, z3 = np.zeros_like(pbar2), np.zeros_like(pbar3)

    out = {}
    for case in ['A', 'B', 'B_global', 'C']:
        if case in ('B', 'C'):      # correct the LOCAL normal row, before flux2global
            _, f2y, f2z = flux2global2(z2, pbar2 - dl * D1(pbar2, x1v), z2)
            _, f3y, f3z = flux2global3(z3, z3, pbar3 - dl * D1(pbar3, x1v))
        else:
            _, f2y, f2z = flux2global2(z2, pbar2, z2)
            _, f3y, f3z = flux2global3(z3, z3, pbar3)
            if case == 'B_global':  # correct the GLOBAL rows after flux2global
                f2y, f2z = f2y - dl * D1(f2y, x1v), f2z - dl * D1(f2z, x1v)
                f3y, f3z = f3y - dl * D1(f3y, x1v), f3z - dl * D1(f3z, x1v)
        divY = ((A2[:, 1:] * f2y[:, 1:] - A2[:, :-1] * f2y[:, :-1]) +
                (A3[1:] * f3y[1:] - A3[:-1] * f3y[:-1])) / V
        divZ = ((A2[:, 1:] * f2z[:, 1:] - A2[:, :-1] * f2z[:, :-1]) +
                (A3[1:] * f3z[1:] - A3[:-1] * f3z[:-1])) / V
        P = p - (dl * D1(p, x1v) if case == 'C' else 0.0)
        out[case] = (mask_interior(-divY + x_ov_rD * P), mask_interior(-divZ + y_ov_rC * P))
    scale = max(np.abs(mask_interior(x_ov_rD * p)).max(), np.abs(mask_interior(y_ov_rC * p)).max())
    predY = mask_interior(+dl * D1(p, x1v) * x_ov_rD)
    predZ = mask_interior(+dl * D1(p, x1v) * y_ov_rC)
    return out, scale, (predY, predZ), x1f


def report():
    print('=' * 78)
    print('REST STATE  p = p(r), u = 0.  max|tendency| / max|G p| on interior cells')
    print('  A: no correction   B: flux - delta*D1(p) only   C: B + source p -> p - delta*D1(p)')
    print('=' * 78)
    for nx1 in (16, 32, 64, 128):
        out, scale, pred, x1f = spherical(nx1=nx1)
        h = x1f[1] - x1f[0]
        rA, rB, rC = (np.abs(out[c][0]).max() / scale for c in 'ABC')
        z = max(np.abs(out[c][1]).max() for c in 'ABC')
        match = np.abs(out['B'][0] - pred).max() / np.abs(pred).max()
        print(f'spherical  h={h:.4f}  theta-row A {rA:.2e}  B {rB:.2e}  C {rC:.2e}'
              f' | B vs +delta D1p G: {match:.1e} | phi-row (all cases) max {z:.1e}')
    print()
    for nx1 in (16, 32, 64, 128):
        out, scale, (pY, pZ), x1f = gnomonic(nx1=nx1)
        h = x1f[1] - x1f[0]
        r = {c: max(np.abs(out[c][0]).max(), np.abs(out[c][1]).max()) / scale for c in out}
        match = max(np.abs(out['B'][0] - pY).max() / np.abs(pY).max(),
                    np.abs(out['B'][1] - pZ).max() / np.abs(pZ).max())
        print(f'gnomonic   h={h:.4f}  alpha+beta rows A {r["A"]:.2e}  B {r["B"]:.2e}'
              f'  B(global-frame) {r["B_global"]:.2e}  C {r["C"]:.2e} | B vs prediction: {match:.1e}')
    print()
    print('Residual B scales like delta*|p\'|/p ~ h^2/(12 r H_s): ratio 4 per halving of h above.')


# --------------------------------------------------------- uniform tracer test
def tracer_test(nx1=32, nx2=24, ny=2):
    """One explicit x2 step on a spherical-polar (theta) sweep with a smooth
    non-zero flow and UNIFORM mass fractions q_n.  Rows as in snapy/LMARS:
       IDN (dry)  F = ubar rho (1 - sum q),   ICY+n  F = ubar rho q_n.
    Correction of row 'phi' (phi = 1 - sum q or q_n), from the face state
    wbar = (wl + wr)/2 as in e7f9904:
       dF[phi] = sigma^2 rho D1(u_n) D1(phi) - delta D1(rho u_n phi)
    'naive' evaluates D1 of the product; 'split' uses the exact discrete
    product rule D1(a b) = avg(b) D1(a) + avg(a) D1(b), avg = (f_{i+1}+f_{i-1})/2,
    so that dF[q] = q * dF[1] bitwise when q is uniform."""
    R0, H = 1.0, 0.5
    x1f = radial_grid(R0, H, nx1)
    rm, rp = x1f[:-1], x1f[1:]
    x1v = 0.75 * (rp**4 - rm**4) / (rp**3 - rm**3)
    h = rp - rm; rb = 0.5 * (rm + rp)
    s2 = h**2 / 12 * (1 - h**2 / (12 * rb**2))
    dl = delta_shift(x1f)
    x2f = np.linspace(0.4, 2.7, nx2 + 1); x2v = 0.5 * (x2f[1:] + x2f[:-1])
    A2 = (0.5 * (rp**2 - rm**2))[None, :] * np.sin(x2f)[:, None]
    V = ((rp**3 - rm**3) / 3)[None, :] * np.abs(np.cos(x2f[:-1]) - np.cos(x2f[1:]))[:, None]
    R, TH = np.meshgrid(x1v, x2v)
    rho = np.exp(-(R - R0) / 0.1) * (1 + 0.1 * np.cos(3 * TH))
    u = 0.3 * np.sin(2 * TH) * np.cos(4 * np.pi * (R - R0))      # u_theta(r, theta)
    q = np.array([0.013, 0.0007])[:ny]                               # uniform species
    # faces (interior faces only; walls closed)
    rhoL, rhoR = rho[:-1], rho[1:]; uL, uR = u[:-1], u[1:]
    ubar = 0.5 * (uL + uR)
    rho_up = np.where(ubar > 0, rhoL, rhoR)
    qf = np.broadcast_to(q[:, None, None], (ny,) + ubar.shape)
    rhob = 0.5 * (rhoL + rhoR); ub = ubar
    mflux = ub * rhob
    dF1 = -dl * D1(mflux, x1v)                  # dF[1] = -delta D1(rho u)
    out = {}
    for mode in ('none', 'mass_only', 'naive', 'split'):
        Fd = ubar * rho_up * (1 - qf.sum(0))
        Fq = ubar * rho_up * qf
        if mode != 'none':
            phid = 1 - qf.sum(0)
            if mode == 'split':
                avg = lambda f: np.concatenate([f[..., :1], 0.5 * (f[..., 2:] + f[..., :-2]), f[..., -1:]], -1)
                dFd = avg(phid) * dF1 + (s2 * rhob * D1(ub, x1v) - dl * avg(mflux)) * D1(phid, x1v)
                dFq = np.stack([avg(qf[n]) * dF1 + (s2 * rhob * D1(ub, x1v) - dl * avg(mflux)) * D1(qf[n], x1v)
                                for n in range(ny)])
            else:
                dFd = s2 * rhob * D1(ub, x1v) * D1(phid, x1v) - dl * D1(mflux * phid, x1v)
                dFq = np.stack([s2 * rhob * D1(ub, x1v) * D1(qf[n], x1v) - dl * D1(mflux * qf[n], x1v)
                                for n in range(ny)])
            Fd = Fd + dFd
            if mode != 'mass_only':
                Fq = Fq + dFq
        zero = np.zeros((1, u.shape[1]))
        Fd = np.concatenate([zero, Fd, zero]); Fq = np.concatenate([np.zeros((ny, 1, u.shape[1])), Fq,
                                                                    np.zeros((ny, 1, u.shape[1]))], 1)
        dt = 0.2 * (x2f[1] - x2f[0]) * R0 / 0.3
        rhod = rho * (1 - q.sum()); rq = rho[None] * q[:, None, None]
        rhod_n = rhod - dt * (A2[1:] * Fd[1:] - A2[:-1] * Fd[:-1]) / V
        rq_n = rq - dt * (A2[1:] * Fq[:, 1:] - A2[:-1] * Fq[:, :-1]) / V
        qn = rq_n / (rhod_n + rq_n.sum(0))
        out[mode] = np.abs(qn[:, :, NG:-NG] - q[:, None, None]).max(axis=(1, 2)) / q
    print('=' * 78)
    print('UNIFORM TRACER  q = (0.013, 0.0007), smooth u_theta(r,theta) != 0, one x2 step')
    print('  max |q_new - q| / q per species')
    for k, v in out.items():
        print(f'   {k:10s}', '  '.join(f'{e:.2e}' for e in v))
    print('  mass_only = mass row corrected, tracer rows not: q drifts at O(delta) -> must correct both.')


def rest_zero_rows():
    """mass, tracer, energy, transverse-momentum corrections at rest: every term
    carries u_n or D1(u_n), exactly 0.0 in floating point."""
    x1f = radial_grid(1.0, 0.5, 32); rm, rp = x1f[:-1], x1f[1:]
    x1v = 0.75 * (rp**4 - rm**4) / (rp**3 - rm**3); dl = delta_shift(x1f)
    s2 = (rp - rm)**2 / 12
    p = pressure_profile(x1v, 1.0); rho = p * 1.3; un = np.zeros_like(p); q = 0.01 + 0 * p
    rows = {'mass': -dl * D1(rho * un, x1v),
            'tracer': s2 * rho * D1(un, x1v) * D1(q, x1v) - dl * D1(rho * un * q, x1v),
            'energy': 3.5 * p * s2 * D1(np.log(p / rho), x1v) * D1(un, x1v) - dl * D1(3.5 * p * un, x1v),
            'mom_t': s2 * rho * D1(un, x1v) * D1(un, x1v) - dl * D1(rho * un * un, x1v)}
    print('=' * 78)
    print('REST: corrections that carry u_n are bitwise zero:',
          {k: float(np.abs(v).max()) for k, v in rows.items()})


if __name__ == '__main__':
    report()
    rest_zero_rows()
    tracer_test()
