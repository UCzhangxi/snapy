"""Linear one-step replica of snapy's eps_eff diagnostic on a spherical-polar column.

Geometry: r in [R, R+1] (H = 1), one theta cell on the equator, phi periodic over an arc
LX = 2 sqrt 2 at r = R, nphi = 2 nz (the x2 roll of test_horizontal_flux_covariance laid in
the x3 = phi direction, which is exactly axisymmetric). Background: isentropic, g = Rgas = 1,
gamma = 1.4, T0 = 1 - (r-R)/cp.  Initial state = exact cell averages over the r^2 dr measure.

At t = 0 only the velocity is perturbed, so the instantaneous entropy tendency of the stored
averages is set by the mass and energy rows only:
    rho_c T_c S = dE_int/dt - h_c drho/dt ,  h_c = cp p_c/rho_c   (cell values),
with E_int = p/(gamma-1). (One RK3 step of seeded-minus-unseeded is this tendency to O(dt h^2).)
The diagnostic is the harness's projection on the seeded w at the roll's wavenumber:
    eps_eff = sum_r rho0 Re(T0 S^ conj w^) / (cp sum_r rho0 |w^|^2).

Discrete operators replicated from main d59836d (linear limit, smooth data):
  * x1 faces: WENO5 in the smooth limit = 5th-order upwind (2,-13,47,27,-3)/60 on the CELL
    values as if they were plain averages; LMARS at rest-balanced faces -> u = (wl+wr)/2,
    F_rho = rho_f u, F_E = cp p_f u; face background p_f, rho_f from the well-balanced
    reference ('exact' = continuum at r_f, the 4th-order-fixed reference).
  * x1 divergence (A+ F+ - A- F-)/V with A = r_f^2 dOmega, V = (r+^3-r-^3)/3 dOmega (exact).
  * x3 faces: same recon in phi (uniform), F = rho_c u_f, cp p_c u_f; optional #293 terms.
  * gravity work: 'cell' (const-gravity rho v g, the default) or 'face' (phi_c div F - div
    phi_f F with phi_c = g x1v, plus the cp5/weno5 curv_flux1 term).
Switches let each candidate be repaired in isolation.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss

GAM = 1.4
CP = GAM / (GAM - 1)
G = 1.0
LX = 2 * np.sqrt(2.0)
XG, WG = leggauss(10)
UP5 = np.array([2, -13, 47, 27, -3]) / 60.0   # left state at i+1/2 from cells i-2..i+2


def background(R):
    T = lambda r: 1 - (r - R) / CP
    p = lambda r: T(r) ** CP
    rho = lambda r: p(r) / T(r)
    return T, p, rho


def cell_avg(f, rf, w=None):
    """average of f over each cell [rf_i, rf_i+1] with weight w(r) (Gauss 10)."""
    rm, rp = rf[:-1], rf[1:]
    if w is None:
        w = lambda r, a=rf[0]: (r / a) ** 2
    r = 0.5 * (rm + rp)[:, None] + 0.5 * (rp - rm)[:, None] * XG[None, :]
    num = (f(r) * w(r) * WG).sum(1)
    den = (w(r) * WG).sum(1)
    return num / den


def recon_weights(rf_ext, ng, kind):
    """weights (nfaces, 6) on cells i-3..i+2 for the face value at face i (between cells
    i-1 and i), as (left+right)/2 of the two 5-point upwind states.
    kind 'cart': snapy's uniform weights; 'sph': the same stencils made exact for
    polynomials of degree <= 4 under the r^2 dr cell average (the consistent x1 weights)."""
    nc = len(rf_ext) - 1
    W = np.zeros((nc + 1, 6))
    for f in range(3, nc - 2):
        if kind == "cart":
            wl = UP5                      # cells f-3..f+1
            wr = UP5[::-1]                # cells f-2..f+2
        else:
            r0 = rf_ext[f]
            def solve(cells):
                M = np.array([[cell_avg(lambda r, n=n: (r - r0) ** n, rf_ext[c:c + 2])[0]
                               for c in cells] for n in range(5)])
                rhs = np.zeros(5); rhs[0] = 1.0
                return np.linalg.solve(M, rhs)
            wl = solve(range(f - 3, f + 2))
            wr = solve(range(f - 2, f + 3))
        W[f, 0:5] += 0.5 * wl
        W[f, 1:6] += 0.5 * wr
    return W


def run(R, nz, seed="sph", recon="cart", gwork="cell", x3corr="off", ref="exact",
        weight="harness", interior=0, truth=False):
    T0f, p0f, rho0f = background(R)
    ng = 3
    h = 1.0 / nz
    rf = R + h * np.arange(-ng, nz + ng + 1)          # extended faces
    rfi = rf[ng:ng + nz + 1]
    rm, rp = rfi[:-1], rfi[1:]
    # cancellation-free forms of snapy's metrics (same values; usable at R -> large)
    V = h * (rm**2 + rm * rp + rp**2) / 3.0             # (rp^3-rm^3)/3, per unit solid angle
    A1 = rfi**2
    A3 = h * 0.5 * (rm + rp)                            # (rp^2-rm^2)/2, per unit dtheta
    rbar = 0.5 * (rm + rp)
    dv = rbar * h**2 / (2 * (rm**2 + rm * rp + rp**2))  # x1v - rbar, exact
    x1v = rbar + dv                                     # = 0.75 (rp^4-rm^4)/(rp^3-rm^3)
    nphi = 2 * nz
    PHI = LX / R
    dphi = PHI / nphi
    m = 2 * np.pi / PHI
    k = m / R
    phif = dphi * np.arange(nphi + 1)
    phic = 0.5 * (phif[:-1] + phif[1:])
    cavg = (np.sin(m * phif[1:]) - np.sin(m * phif[:-1])) / (m * dphi)   # <cos m phi>
    savg = -(np.cos(m * phif[1:]) - np.cos(m * phif[:-1])) / (m * dphi)  # <sin m phi>

    # radial profiles of rho w (A) and rho u_phi (B):  rho w = A cos, rho u = B sin
    z = lambda r: r - R
    if seed == "sph":   # anelastic on the sphere: (1/r^2)(r^2 A)' + m B / r = 0
        A = lambda r: k * np.sin(np.pi * z(r)) * (R / r) ** 2
        B = lambda r: -np.pi * np.cos(np.pi * z(r)) * (R / r)
    else:               # the Cartesian roll copied with z = r - R (not anelastic here)
        A = lambda r: k * np.sin(np.pi * z(r)) + 0 * r
        B = lambda r: -np.pi * np.cos(np.pi * z(r)) + 0 * r

    rho_c = cell_avg(rho0f, rfi)
    p_c = cell_avg(p0f, rfi)
    T_c = p_c / rho_c
    h_c = CP * T_c
    amp = 1e-5
    mw = amp * cell_avg(A, rfi)[:, None] * cavg[None, :]       # (rho w) bar
    mu = amp * cell_avg(B, rfi)[:, None] * savg[None, :]       # (rho u) bar
    w_t = mw / rho_c[:, None]                                    # Favre
    u_t = mu / rho_c[:, None]

    # ---- x1 faces ----
    # extend w with reflecting ghosts (odd)
    wext = np.zeros((nz + 2 * ng, nphi))
    wext[ng:ng + nz] = w_t
    for g_ in range(ng):
        wext[ng - 1 - g_] = -w_t[g_]
        wext[ng + nz + g_] = -w_t[nz - 1 - g_]
    Wr = recon_weights(rf, ng, recon)
    wf = np.zeros((nz + 1, nphi))
    for f in range(nz + 1):
        F = f + ng
        wf[f] = Wr[F] @ wext[F - 3:F + 3]
    wf[0] = 0.0; wf[-1] = 0.0                       # reflecting walls: wl = -wr
    if ref == "exact":
        pf, rhof = p0f(rfi), rho0f(rfi)
    elif ref in ("code", "code-sph"):
        pf, rhof = wb_faces(p_c, rho_c, h, nz, ng, Wr if ref == "code-sph" else
                            recon_weights(rf, ng, "cart"))
    else:   # "r2": main's reference rebuilt on the r^2 measure, with r^2 recon weights
        pf, rhof = wb_faces(p_c, rho_c, h, nz, ng, recon_weights(rf, ng, "sph"),
                            r2=(rfi, dv))
    F1r = rhof[:, None] * wf
    F1E = CP * pf[:, None] * wf
    div1 = lambda F: (A1[1:, None] * F[1:] - A1[:-1, None] * F[:-1]) / V[:, None]

    # ---- x3 (phi) faces: uniform recon, periodic ----
    def face_phi(a):
        # face j-1/2 between cells j-1 and j: cp6 on cells j-3..j+2
        c = [1 / 60, -8 / 60, 37 / 60, 37 / 60, -8 / 60, 1 / 60]
        return sum(c[n] * np.roll(a, 3 - n, 1) for n in range(6))
    uf = face_phi(u_t)                               # faces 0..nphi-1 (periodic)
    F3r = rho_c[:, None] * uf
    F3E = CP * p_c[:, None] * uf
    if x3corr == "exact":
        # <rho u>_A and cp <p u>_A over the face measure r dr, at phi faces (sin m phi_f)
        wr_ = lambda r, a=rfi[0]: r / a
        sf = np.sin(m * phif[:-1])[None, :]
        F3r = amp * cell_avg(B, rfi, wr_)[:, None] * sf
        F3E = amp * CP * cell_avg(lambda r: p0f(r) * B(r) / rho0f(r), rfi, wr_)[:, None] * sf
    elif x3corr != "off":
        dlt = dv - h**2 / (12 * rbar)                   # r_v - r_c, r_c = rbar + h^2/(12 rbar)
        s2 = h**2 / 12 * (1 - h**2 / (12 * (0.5 * (rm + rp)) ** 2))
        def D1(a):
            out = np.zeros_like(a)
            out[1:-1] = (a[2:] - a[:-2]) / (2 * h + dv[2:] - dv[:-2])[:, None]
            return out
        dF3r = -dlt[:, None] * D1(F3r)
        dF3E = -dlt[:, None] * D1(F3E)
        if x3corr == "full":
            hc2 = (h_c * np.ones((1, nphi)).T).T
            dF3E = dF3E + s2[:, None] * rho_c[:, None] * D1(hc2) * D1(uf)
        F3r = F3r + dF3r
        F3E = F3E + dF3E
    # per unit solid angle: V has dOmega = dtheta dphi; A3 has dtheta -> divide by dphi
    div3 = lambda F: A3[:, None] * (np.roll(F, -1, 1) - F) / (V[:, None] * dphi)

    drho = -div1(F1r) - div3(F3r)
    dE = -div1(F1E) - div3(F3E)
    if truth:
        # continuum: drho/dt = -div(rho v) = -C(r) cos(m phi); on the adiabat dE_int = h drho
        e = 1e-5
        C = lambda r: (((r + e) ** 2 * A(r + e) - (r - e) ** 2 * A(r - e)) / (2 * e) / r**2
                       + m * B(r) / r)
        hC = lambda r: CP * T0f(r) * C(r)
        drho = -amp * cell_avg(C, rfi)[:, None] * cavg[None, :]
        dE = -amp * cell_avg(hC, rfi)[:, None] * cavg[None, :]
        gwork = "none"
    if gwork == "cell":
        dE += -G * mw
    elif gwork != "none":
        # phi_c div F - div(phi_f F) = -[A+ F+ (r+ - x1v) - A- F- (r- - x1v)]/V, offsets exact
        dE += -G * (A1[1:, None] * F1r[1:] * (0.5 * h - dv)[:, None]
                    - A1[:-1, None] * F1r[:-1] * (-0.5 * h - dv)[:, None]) / V[:, None]
        if gwork == "face":   # curv_flux1 (cp5/weno5)
            m_c = rho_c[:, None] * w_t
            H = np.zeros((nz + 1, nphi))
            H[1:-1] = (h + dv[1:] - dv[:-1])[:, None] / 12 * (m_c[1:] - m_c[:-1])
            dE += G * div1(H)
    rTS = dE - h_c[:, None] * drho
    S = rTS / (rho_c * T_c)[:, None]

    emk = np.exp(-1j * m * phic)
    what = (2.0 / nphi) * (w_t * emk).sum(1)
    Shat = (2.0 / nphi) * (S * emk).sum(1)
    sl = slice(interior, nz - interior)
    wt = np.ones(nz) if weight == "harness" else V
    num = (wt * rho_c * (T_c * Shat * what.conj()).real)[sl].sum()
    den = (wt * CP * rho_c * np.abs(what) ** 2)[sl].sum()
    if weight == "local":
        return (T_c[:, None] * S / w_t)[:, 0] * nz**2, S, w_t
    return num / den * nz**2


def wb_faces(p_c, rho_c, h, nz, ng, Wr, r2=None):
    """main's well-balanced x1 faces at rest (hydro_ref_x1_impl.h, uniform grid):
    psf scan with g rho_c dx1f from the top anchor, pref from the six-face weights, dsf/dref
    from the binomially smoothed rho/p; faces = reference + recon(perturbation), (l+r)/2."""
    lo = np.zeros(nz); hi = np.zeros(nz)
    rho_scan = rho_c
    if r2 is not None:
        # the scan needs int rho dr = h <rho> (plain mean), not h rho_c (r^2 mean):
        # <rho> = rho_c - (x1v - rbar) d_r rho + O(h^4)
        rfi, dv = r2
        d = np.gradient(rho_c, 0.5 * (rfi[:-1] + rfi[1:]) + dv)
        rho_scan = rho_c - dv * d
    top = p_c[-1] * np.exp(-G * 0.5 * h / (p_c[-1] / rho_c[-1]))
    face = top
    for i in range(nz - 1, -1, -1):
        hi[i] = face; lo[i] = face + G * rho_scan[i] * h; face = lo[i]
    pref = 0.5 * (lo + hi)
    w6 = np.array([11 / 1440, -31 / 480, 401 / 720, 401 / 720, -31 / 480, 11 / 1440])
    fall = np.append(lo, hi[-1])                       # faces 0..nz
    for i in range(nz):
        if 2 <= i < nz - 2:
            v = w6 @ fall[i - 2:i + 4]
            if min(lo[i], hi[i]) <= v <= max(lo[i], hi[i]):
                pref[i] = v
        elif i < 2:
            v = np.array([[95/288, 1427/1440, -133/240, 241/720, -173/1440, 3/160],
                          [-3/160, 637/1440, 511/720, -43/240, 77/1440, -11/1440]])[i] @ fall[0:6]
            if min(lo[i], hi[i]) <= v <= max(lo[i], hi[i]):
                pref[i] = v
        else:
            row = 4 - (i - (nz - 5))
            wts = np.array([[95/288, 1427/1440, -133/240, 241/720, -173/1440, 3/160],
                            [-3/160, 637/1440, 511/720, -43/240, 77/1440, -11/1440]])[row][::-1]
            v = wts @ fall[nz - 5:nz + 1]
            if min(lo[i], hi[i]) <= v <= max(lo[i], hi[i]):
                pref[i] = v
    if r2 is not None:
        # pref = r^2 mean of the degree-5 face interpolant (six faces, one-sided at walls)
        fall = np.append(lo, hi[-1])
        for i in range(nz):
            s0 = min(max(i - 2, 0), nz - 5)
            rr = rfi[s0:s0 + 6]
            c = np.polyfit(rr - rr[0], fall[s0:s0 + 6], 5)
            from numpy.polynomial.legendre import leggauss
            xg, wg = leggauss(8)
            r = 0.5 * (rfi[i] + rfi[i + 1]) + 0.5 * h * xg
            pref[i] = (np.polyval(c, r - rr[0]) * r**2 * wg).sum() / (r**2 * wg).sum()
    rop = rho_c / p_c
    rs = np.array([(rop[np.clip(i + np.arange(-2, 3), 0, nz - 1)] * [1, 4, 6, 4, 1]).sum() / 16
                   for i in range(nz)])
    rfc = np.concatenate([[rs[0]], 0.5 * (rs[1:] + rs[:-1])])
    dref = pref * rs
    def rec(pert):
        ext = np.zeros(nz + 2 * ng); ext[ng:ng + nz] = pert
        for g_ in range(ng):
            ext[ng - 1 - g_] = pert[g_]; ext[ng + nz + g_] = pert[nz - 1 - g_]
        return np.array([Wr[f + ng] @ ext[f + ng - 3:f + ng + 3] for f in range(nz + 1)])
    if r2 is not None:
        # face rho/p taken with the same r^2-consistent weights as the perturbation, so that
        # dsf and the reconstructed dref carry the same measure (main: two-point mean)
        rfc = rec(rs)[:nz]
    dsf = lo * rfc
    psf = np.append(lo, hi[-1]); dsff = np.append(dsf, hi[-1] * rs[-1])
    pf = psf + rec(p_c - pref)
    rhof = dsff + rec(rho_c - dref)
    return pf, rhof


def dfdr(f, r, e=1e-6):
    return (f(r + e) - f(r - e)) / (2 * e)


if __name__ == "__main__":
    for nz in (32, 64, 128):
        print(nz, run(5.0, nz), run(5.0, nz, recon="sph"))
