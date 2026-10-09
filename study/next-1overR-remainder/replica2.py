"""Deck-general linear one-step replica of the eps_eff diagnostic (extends
../next-1overR/replica.py; same operators, same switches, plus):

  * any polytrope: T = 1 - z/(m+1) on [0, L], rho ~ T^m, p = rho T, in units R_gas = g = T_b = 1
    (so H_b = 1 and R is in units of H_b); gamma free.  m+1 = cp is the isentropic deck.
  * roll rho w = k sin(pi z/L) cos, rho u = -(pi/L) cos(pi z/L) sin, k = 2 pi / LX;
    seed 'sph' = the same roll made anelastic on the sphere ((R/r)^2, R/r factors),
    seed 'cart' = the Cartesian roll copied onto the sphere.
  * gwork 'face-exact': the face form with the 2-face weights made exact for the r^2 measure,
    E += -g [(1/2 + dv/h) F+ + (1/2 - dv/h) F-]   (= g F(x1v), F linear in r, exact <F>_V)
    plus curv_flux1 as in 'face'.
  * truth: continuum tendencies cell-averaged (rho T S = -rho T w s0' pointwise, any deck).
"""
import numpy as np
from numpy.polynomial.legendre import leggauss

XG, WG = leggauss(10)
UP5 = np.array([2, -13, 47, 27, -3]) / 60.0


class Deck:
    def __init__(self, gam=1.4, m=None, L=1.0, aspect=2 * np.sqrt(2.0), name=""):
        self.gam = gam
        self.cp = gam / (gam - 1)
        self.m = self.cp - 1 if m is None else m
        self.L = L
        self.LX = aspect * L
        self.name = name

    def bg(self, R):
        a = 1.0 / (self.m + 1)
        T = lambda r: 1 - a * (r - R)
        rho = lambda r: T(r) ** self.m
        p = lambda r: rho(r) * T(r)
        return T, p, rho


def cell_avg(f, rf, w=None):
    rm, rp = rf[:-1], rf[1:]
    if w is None:
        w = lambda r, a=rf[0]: (r / a) ** 2
    r = 0.5 * (rm + rp)[:, None] + 0.5 * (rp - rm)[:, None] * XG[None, :]
    return (f(r) * w(r) * WG).sum(1) / (w(r) * WG).sum(1)


_WCACHE = {}


def recon_weights(rf_ext, kind):
    key = (kind, len(rf_ext), rf_ext[0], rf_ext[-1])
    if key in _WCACHE:
        return _WCACHE[key]
    nc = len(rf_ext) - 1
    W = np.zeros((nc + 1, 6))
    for f in range(3, nc - 2):
        if kind == "cart":
            wl, wr = UP5, UP5[::-1]
        else:
            r0 = rf_ext[f]
            def solve(cells):
                M = np.array([[cell_avg(lambda r, n=n: ((r - r0) / (rf_ext[1] - rf_ext[0])) ** n,
                                        rf_ext[c:c + 2])[0] for c in cells] for n in range(5)])
                rhs = np.zeros(5); rhs[0] = 1.0
                return np.linalg.solve(M, rhs)
            wl = solve(range(f - 3, f + 2))
            wr = solve(range(f - 2, f + 3))
        W[f, 0:5] += 0.5 * wl
        W[f, 1:6] += 0.5 * wr
    _WCACHE[key] = W
    return W


def run(deck, R, nz, seed="sph", recon="cart", gwork="face", x3corr="off", ref="exact",
        truth=False, parts=False, curv=True):
    T0f, p0f, rho0f = deck.bg(R)
    CP, G, L = deck.cp, 1.0, deck.L
    ng = 3
    h = L / nz
    rf = R + h * np.arange(-ng, nz + ng + 1)
    rfi = rf[ng:ng + nz + 1]
    rm, rp = rfi[:-1], rfi[1:]
    V = h * (rm**2 + rm * rp + rp**2) / 3.0
    A1 = rfi**2
    A3 = h * 0.5 * (rm + rp)
    rbar = 0.5 * (rm + rp)
    dv = rbar * h**2 / (2 * (rm**2 + rm * rp + rp**2))
    nphi = 2 * nz
    PHI = deck.LX / R
    dphi = PHI / nphi
    m = 2 * np.pi / PHI
    k = m / R
    phif = dphi * np.arange(nphi + 1)
    phic = 0.5 * (phif[:-1] + phif[1:])
    cavg = (np.sin(m * phif[1:]) - np.sin(m * phif[:-1])) / (m * dphi)
    savg = -(np.cos(m * phif[1:]) - np.cos(m * phif[:-1])) / (m * dphi)
    kz = np.pi / L
    z = lambda r: r - R
    if seed == "sph":
        A = lambda r: k * np.sin(kz * z(r)) * (R / r) ** 2
        B = lambda r: -kz * np.cos(kz * z(r)) * (R / r)
    elif seed in ("wsph", "wcart"):   # w ~ sin (velocity-shaped), rho u from continuity
        a_ = 1.0 / (deck.m + 1)
        P = lambda r: rho0f(r) * np.sin(kz * z(r))
        dP = lambda r: rho0f(r) * (kz * np.cos(kz * z(r))
                                   - deck.m * a_ / T0f(r) * np.sin(kz * z(r)))
        if seed == "wsph":            # (1/r^2)(r^2 A)' + m B / r = 0
            A = lambda r: k * P(r) * (R / r) ** 2
            B = lambda r: -dP(r) * (R / r)
        else:                         # Cartesian roll copied (not anelastic on the sphere)
            A = lambda r: k * P(r)
            B = lambda r: -dP(r)
    else:
        A = lambda r: k * np.sin(kz * z(r)) + 0 * r
        B = lambda r: -kz * np.cos(kz * z(r)) + 0 * r

    rho_c = cell_avg(rho0f, rfi)
    p_c = cell_avg(p0f, rfi)
    T_c = p_c / rho_c
    h_c = CP * T_c
    amp = 1e-5
    mw = amp * cell_avg(A, rfi)[:, None] * cavg[None, :]
    mu = amp * cell_avg(B, rfi)[:, None] * savg[None, :]
    w_t = mw / rho_c[:, None]
    u_t = mu / rho_c[:, None]

    wext = np.zeros((nz + 2 * ng, nphi))
    wext[ng:ng + nz] = w_t
    for g_ in range(ng):
        wext[ng - 1 - g_] = -w_t[g_]
        wext[ng + nz + g_] = -w_t[nz - 1 - g_]
    Wr = recon_weights(rf, recon)
    wf = np.array([Wr[f + ng] @ wext[f:f + 6] for f in range(nz + 1)])
    wf[0] = 0.0; wf[-1] = 0.0
    if ref == "exact":
        pf, rhof = p0f(rfi), rho0f(rfi)
    else:
        pf, rhof = wb_faces(p_c, rho_c, h, nz, ng, recon_weights(rf, "cart"))
    F1r = rhof[:, None] * wf
    F1E = CP * pf[:, None] * wf
    div1 = lambda F: (A1[1:, None] * F[1:] - A1[:-1, None] * F[:-1]) / V[:, None]

    def face_phi(a):
        c = [1 / 60, -8 / 60, 37 / 60, 37 / 60, -8 / 60, 1 / 60]
        return sum(c[n] * np.roll(a, 3 - n, 1) for n in range(6))
    uf = face_phi(u_t)
    F3r = rho_c[:, None] * uf
    F3E = CP * p_c[:, None] * uf
    if x3corr == "exact":
        # <rho u>_A and cp <p u>_A over the x3 face measure r dr (sin m phi at the faces)
        wr_ = lambda r, a=rfi[0]: r / a
        sf = np.sin(m * phif[:-1])[None, :]
        F3r = amp * cell_avg(B, rfi, wr_)[:, None] * sf
        F3E = amp * CP * cell_avg(lambda r: p0f(r) * B(r) / rho0f(r), rfi, wr_)[:, None] * sf
    elif x3corr in ("x1", "full"):
        dlt = dv - h**2 / (12 * rbar)
        s2 = h**2 / 12 * (1 - h**2 / (12 * rbar**2))
        def D1(a):
            out = np.zeros_like(a)
            out[1:-1] = (a[2:] - a[:-2]) / (2 * h + dv[2:] - dv[:-2])[:, None]
            return out
        dF3r = -dlt[:, None] * D1(F3r)
        dF3E = -dlt[:, None] * D1(F3E)
        if x3corr == "full":
            hc2 = np.repeat(h_c[:, None], nphi, 1)
            dF3E = dF3E + s2[:, None] * rho_c[:, None] * D1(hc2) * D1(uf)
        F3r = F3r + dF3r
        F3E = F3E + dF3E
    div3 = lambda F: A3[:, None] * (np.roll(F, -1, 1) - F) / (V[:, None] * dphi)

    drho = -div1(F1r) - div3(F3r)
    dE = -div1(F1E) - div3(F3E)
    if truth:
        # div(rho v) = (1/r^2)(r^2 A)' + m B / r, analytic (no cancellation at large R)
        if seed == "wsph":
            C = lambda r: 0 * r
        elif seed == "wcart":
            C = lambda r: k * dP(r) + 2 * A(r) / r + m * B(r) / r
        elif seed == "sph":
            C = lambda r: k * kz * np.cos(kz * z(r)) * (R / r) ** 2 + m * B(r) / r
        else:
            C = lambda r: k * kz * np.cos(kz * z(r)) + 2 * A(r) / r + m * B(r) / r
        hp = -CP / (deck.m + 1)                    # cp dT/dr
        q = lambda r: CP * T0f(r) * C(r) + A(r) * (hp + G)
        drho = -amp * cell_avg(C, rfi)[:, None] * cavg[None, :]
        dE = -amp * cell_avg(q, rfi)[:, None] * cavg[None, :]
        gwork = "none"
    if gwork == "cell":
        dE += -G * mw
    elif gwork in ("face", "face-exact", "face-rbar"):
        if gwork == "face-rbar":    # face form with phi_c = g rbar: trapezoid rule on G = r^2 F
            dE += -G * 0.5 * h * (A1[1:, None] * F1r[1:] + A1[:-1, None] * F1r[:-1]) / V[:, None]
        elif gwork == "face":
            dE += -G * (A1[1:, None] * F1r[1:] * (0.5 * h - dv)[:, None]
                        + A1[:-1, None] * F1r[:-1] * (0.5 * h + dv)[:, None]) / V[:, None]
        else:
            dE += -G * ((0.5 + dv / h)[:, None] * F1r[1:] + (0.5 - dv / h)[:, None] * F1r[:-1])
        if curv:
            m_c = rho_c[:, None] * w_t
            H = np.zeros((nz + 1, nphi))
            H[1:-1] = (h + dv[1:] - dv[:-1])[:, None] / 12 * (m_c[1:] - m_c[:-1])
            if gwork == "face-rbar" and curv:   # curv_flux1 on G = r^2 m: Euler-Maclaurin, O(h^4)
                Gc = rbar[:, None] ** 2 * m_c
                H[1:-1] = h / 12 * (Gc[1:] - Gc[:-1]) / A1[1:-1, None]
            elif curv == "sph":   # metric-consistent: (1/r^2)(r^2 H)' = h^2/12 m'' + O(h^2/R^2)
                H[1:-1] -= (h**2 / 6 / rfi[1:-1])[:, None] * 0.5 * (m_c[1:] + m_c[:-1])
            dE += G * div1(H)
            dE_curv = G * div1(H)
    if parts == "budget":
        rc = rbar if gwork == "face-rbar" else rbar + dv
        dEw = dE + div1(F1E) + div3(F3E)               # the gravity work alone
        d1 = -div1(F1r)
        col = (V[:, None] * (dEw + G * rc[:, None] * d1)).sum(0)   # per phi column
        return np.abs(col).max() / (V[:, None] * np.abs(dEw)).sum(0).max()
    rTS = dE - h_c[:, None] * drho
    if parts == "terms":
        x3 = -div3(F3E) + h_c[:, None] * div3(F3r)
        cv = locals().get("dE_curv", 0 * rTS)
        return {k: _proj(v, rho_c, T_c, w_t, m, phic, CP, nz)
                for k, v in (("x1", rTS - x3 - cv), ("curv", cv), ("x3", x3))}
    S = rTS / (rho_c * T_c)[:, None]
    emk = np.exp(-1j * m * phic)
    what = (2.0 / nphi) * (w_t * emk).sum(1)
    Shat = (2.0 / nphi) * (S * emk).sum(1)
    num = (rho_c * (T_c * Shat * what.conj()).real).sum()
    den = (CP * rho_c * np.abs(what) ** 2).sum()
    return num / den * nz**2


def _proj(rTS, rho_c, T_c, w_t, m, phic, CP, nz):
    emk = np.exp(-1j * m * phic)
    S = rTS / (rho_c * T_c)[:, None]
    what = (w_t * emk).sum(1)
    Shat = (S * emk).sum(1)
    return ((rho_c * (T_c * Shat * what.conj()).real).sum()
            / (CP * rho_c * np.abs(what) ** 2).sum() * nz**2)


def wb_faces(p_c, rho_c, h, nz, ng, Wr, G=1.0):
    """main's well-balanced x1 faces at rest (hydro_ref_x1_impl.h), as in ../next-1overR."""
    lo = np.zeros(nz); hi = np.zeros(nz)
    top = p_c[-1] * np.exp(-G * 0.5 * h / (p_c[-1] / rho_c[-1]))
    face = top
    for i in range(nz - 1, -1, -1):
        hi[i] = face; lo[i] = face + G * rho_c[i] * h; face = lo[i]
    pref = 0.5 * (lo + hi)
    w6 = np.array([11 / 1440, -31 / 480, 401 / 720, 401 / 720, -31 / 480, 11 / 1440])
    edge = np.array([[95/288, 1427/1440, -133/240, 241/720, -173/1440, 3/160],
                     [-3/160, 637/1440, 511/720, -43/240, 77/1440, -11/1440]])
    fall = np.append(lo, hi[-1])
    for i in range(nz):
        if 2 <= i < nz - 2:
            v = w6 @ fall[i - 2:i + 4]
        elif i < 2:
            v = edge[i] @ fall[0:6]
        else:
            v = edge[4 - (i - (nz - 5))][::-1] @ fall[nz - 5:nz + 1]
        if min(lo[i], hi[i]) <= v <= max(lo[i], hi[i]):
            pref[i] = v
    rop = rho_c / p_c
    rs = np.array([(rop[np.clip(i + np.arange(-2, 3), 0, nz - 1)] * [1, 4, 6, 4, 1]).sum() / 16
                   for i in range(nz)])
    rfc = np.concatenate([[rs[0]], 0.5 * (rs[1:] + rs[:-1])])
    dref = pref * rs
    def rec(pert):
        ext = np.zeros(nz + 2 * ng); ext[ng:ng + nz] = pert
        for g_ in range(ng):
            ext[ng - 1 - g_] = pert[g_]; ext[ng + nz + g_] = pert[nz - 1 - g_]
        return np.array([Wr[f + ng] @ ext[f:f + 6] for f in range(nz + 1)])
    dsf = lo * rfc
    psf = np.append(lo, hi[-1]); dsff = np.append(dsf, hi[-1] * rs[-1])
    return psf + rec(p_c - pref), dsff + rec(rho_c - dref)


INF = 1e6


def excess(deck, R, nz, **kw):
    """(eps nz^2 on the sphere - eps nz^2 Cartesian twin) * R/H_b; the twin has the same seed
    formula at R = INF, where both seeds coincide."""
    kc = dict(kw); kc["seed"] = "wsph" if kw.get("seed", "sph").startswith("w") else "sph"
    return (run(deck, R, nz, **kw) - run(deck, INF, nz, **kc)) * R
