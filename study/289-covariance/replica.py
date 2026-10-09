"""Numpy replica of snapy's explicit RHS (hydro_forward.cpp @117e449) for the
T1L deck: 2D (x1 = z walls, x2 = x periodic), ideal gas, WB x1 reconstruction
(hydro_ref_x1_impl.h, CPU path), WENO5 (linear weights or JS+scale), LMARS,
const gravity (cell / face forms incl. the dz^2/12 curvature correction),
dynamic isotropic diffusion (diffusion.cpp), reflecting fixed-T walls.

Array layout: q[var, j(x2), i(x1)] with NG ghosts on both axes.
Linear eigenvalues: finite-difference JVPs on one x2 Fourier mode."""
import numpy as np

GAMMA = 1.4
R = 1.0
CV = R / (GAMMA - 1)
CP = CV + R
G = 1.0
NG = 3
IDN, IVX, IVY, IVZ, IPR = 0, 1, 2, 3, 4

W6 = np.array([11 / 1440, -31 / 480, 401 / 720, 401 / 720, -31 / 480, 11 / 1440])
W6E = np.array([[95 / 288, 1427 / 1440, -133 / 240, 241 / 720, -173 / 1440, 3 / 160],
                [-3 / 160, 637 / 1440, 511 / 720, -43 / 240, 77 / 1440, -11 / 1440]])


class Deck:
    def __init__(self, nz, eps, mu, form="cell", weno="linear", nx=None,
                 dF=0.0, dF_kind="lnT", dFm=0.0, curv=True, diffusion=True,
                 mom_fix=0.0, wall_pert="even", x1_mom=False, lm_u=1.0, lm_p=1.0, curv_wall=False, dF_wall=True, dF_order=2, rho_plain=False):
        self.nz = nz
        self.nx = nx or 2 * nz
        self.eps = eps
        self.beta = G / CP + eps * G / R
        self.mu = mu
        self.K = CP * mu
        self.form = form
        self.weno = weno
        self.dz = 1.0 / nz
        self.Lx = 2 * np.sqrt(2)
        self.dx = self.Lx / self.nx
        self.k = 2 * np.pi / self.Lx
        self.zc = (np.arange(nz) + 0.5) * self.dz
        self.zf = np.arange(nz + 1) * self.dz
        self.xc = (np.arange(self.nx) + 0.5) * self.dx
        self.dF = dF            # coefficient on the x2 enthalpy covariance term
        self.dF_kind = dF_kind
        self.dFm = dFm          # coefficient on an x1 mass-flux covariance fix
        self.curv = curv
        self.diffusion = diffusion
        self.Twall = (1.0, 1.0 - self.beta)
        self.wall_pert = wall_pert
        self.x1_mom = x1_mom
        self.curv_wall = curv_wall
        self.dF_wall = dF_wall
        self.dF_order = dF_order
        self.rho_plain = rho_plain
        self.lm_u, self.lm_p = lm_u, lm_p

    # ------------------------------------------------------------ background
    def background(self, balance=True):
        """cell values: T = T0(zc) exactly, p from the discrete WB balance
        (balance_column fixed point: p - pref = const, rho = p / (R T))."""
        T = 1 - self.beta * self.zc
        p = T ** (G / (R * self.beta))
        rho = p / (R * T)
        if balance:
            for it in range(200):
                col = self._ghost_col(rho, p)
                psf_lo, psf_hi, pref, dsf, dref = self.wb_ref(col[0], col[1])
                pp = p - pref[NG:-NG]
                c = pp[-1]
                err = np.max(np.abs(pp - c) / (rho * G * self.dz))
                if err < 1e-15:
                    break
                p = pref[NG:-NG] + c
                rho = p / (R * T)
        return rho, p, T

    def _ghost_col(self, rho, p):
        # only interior matters for the WB reference rows used; mirror ghosts
        r = np.concatenate([rho[:NG][::-1], rho, rho[-NG:][::-1]])
        q = np.concatenate([p[:NG][::-1], p, p[-NG:][::-1]])
        return r, q

    # ----------------------------------------------------------- WB reference
    def wb_ref(self, rho, p):
        """hydro_ref_x1_impl (CPU). rho, p: (..., nc1) incl. ghosts."""
        dz = self.dz
        nc1 = rho.shape[-1]
        il, iu = NG, nc1 - NG - 1
        anchor = p[..., iu] * np.exp(-G * 0.5 * dz / (p[..., iu] / rho[..., iu]))
        dp = G * rho * dz
        psf_lo = np.empty_like(rho); psf_hi = np.empty_like(rho)
        # i <= iu: hi = anchor + sum_{j=i+1..iu} dp_j
        cs = np.cumsum(dp[..., ::-1], -1)[..., ::-1]  # cs[i] = sum_{j>=i} dp_j
        tail = cs[..., iu + 1] if iu + 1 < nc1 else 0.0
        hi_part = cs - tail[..., None] if np.ndim(tail) else cs - tail  # sum_{j=i..iu}
        psf_lo[..., :iu + 1] = anchor[..., None] + hi_part[..., :iu + 1]
        psf_hi[..., :iu + 1] = psf_lo[..., :iu + 1] - dp[..., :iu + 1]
        face = anchor.copy()
        for i in range(iu + 1, nc1):
            psf_lo[..., i] = face
            psf_hi[..., i] = face - dp[..., i]
            face = psf_hi[..., i]
        faces = np.concatenate([psf_lo, psf_hi[..., -1:]], -1)  # nc1+1 faces
        pref = 0.5 * (psf_lo + psf_hi)
        lower = np.minimum(psf_lo, psf_hi); upper = np.maximum(psf_lo, psf_hi)

        def six(i, start, wts):
            v = sum(wts[m] * faces[..., start + m] for m in range(6))
            ok = (v >= lower[..., i]) & (v <= upper[..., i])
            pref[..., i] = np.where(ok, v, pref[..., i])
        for i in range(nc1):
            wall_in = il <= i < il + 2
            wall_out = iu - 2 < i <= iu
            if 2 <= i < nc1 - 2 and not wall_in and not wall_out:
                six(i, i - 2, W6)
            if wall_in:
                six(i, il, W6E[i - il])
            if wall_out:
                s = iu + 1 - 5
                row = 4 - (i - s)
                six(i, s, W6E[row][::-1])
        rop = rho / p
        idx = np.clip(np.arange(nc1), il, iu)
        rs = np.zeros_like(rho)
        for m, wgt in zip(range(-2, 3), (1, 4, 6, 4, 1)):
            j = np.clip(np.arange(nc1) + m, il, iu)
            rs += wgt * rop[..., j]
        rs /= 16
        if getattr(self, "rs_wall_exact", False):  # linear-exact wall closure
            g = rop
            rs[..., il] = g[..., il]
            rs[..., il + 1] = (g[..., il] + 2 * g[..., il + 1] + g[..., il + 2]) / 4
            rs[..., iu] = g[..., iu]
            rs[..., iu - 1] = (g[..., iu] + 2 * g[..., iu - 1] + g[..., iu - 2]) / 4
        rf = rs.copy()
        rf[..., 1:] = 0.5 * (rs[..., :-1] + rs[..., 1:])
        dref = pref * rs
        dsf = psf_lo * rf
        return psf_lo, psf_hi, pref, dsf, dref

    # --------------------------------------------------------- reconstruction
    def recon(self, q, axis):
        """returns (ql, qr): ql[f] = left state at face f (from cell f-1),
        qr[f] = right state at face f (from cell f). Face f = lower face of
        cell f. Valid for f in [NG, n-NG]."""
        q = np.moveaxis(q, axis, -1)
        n = q.shape[-1]
        ql = np.zeros_like(q); qr = np.zeros_like(q)
        c = slice(2, n - 2)
        qm2, qm1, q0, qp1, qp2 = (q[..., 0:n - 4], q[..., 1:n - 3], q[..., 2:n - 2],
                                  q[..., 3:n - 1], q[..., 4:n])
        # value at the left face of cell c (qr[c]) -- coefficients cm
        p0 = -1 / 6 * qm2 + 5 / 6 * qm1 + 1 / 3 * q0
        p1 = 1 / 3 * qm1 + 5 / 6 * q0 - 1 / 6 * qp1
        p2 = 11 / 6 * q0 - 7 / 6 * qp1 + 1 / 3 * qp2
        # value at the right face of cell c (ql[c+1]) -- coefficients cp
        r0 = -1 / 6 * qp2 + 5 / 6 * qp1 + 1 / 3 * q0
        r1 = 1 / 3 * qp1 + 5 / 6 * q0 - 1 / 6 * qm1
        r2 = 11 / 6 * q0 - 7 / 6 * qm1 + 1 / 3 * qm2
        if self.weno == "linear":
            qr[..., c] = 0.3 * p0 + 0.6 * p1 + 0.1 * p2
            ql[..., 3:n - 1] = 0.3 * r0 + 0.6 * r1 + 0.1 * r2
        else:
            vs = (np.abs(qm2) + np.abs(qm1) + np.abs(q0) + np.abs(qp1) + np.abs(qp2)) / 5
            safe = np.where(vs != 0, vs, 1.0)
            ph = [x / safe for x in (qm2, qm1, q0, qp1, qp2)]
            def betas(a, b, cc, d, e):
                b0 = 13 / 12 * (a - 2 * b + cc) ** 2 + 0.25 * (a - 4 * b + 3 * cc) ** 2
                b1 = 13 / 12 * (b - 2 * cc + d) ** 2 + 0.25 * (-b + d) ** 2
                b2 = 13 / 12 * (cc - 2 * d + e) ** 2 + 0.25 * (3 * cc - 4 * d + e) ** 2
                return b0, b1, b2
            b0, b1, b2 = betas(*ph)
            a0, a1, a2 = 0.3 / (b0 + 1e-6) ** 2, 0.6 / (b1 + 1e-6) ** 2, 0.1 / (b2 + 1e-6) ** 2
            out = (a0 * p0 + a1 * p1 + a2 * p2) / (a0 + a1 + a2)
            qr[..., c] = np.where(vs != 0, out, 0.0)
            phr = ph[::-1]
            b0, b1, b2 = betas(*phr)
            a0, a1, a2 = 0.3 / (b0 + 1e-6) ** 2, 0.6 / (b1 + 1e-6) ** 2, 0.1 / (b2 + 1e-6) ** 2
            out = (a0 * r0 + a1 * r1 + a2 * r2) / (a0 + a1 + a2)
            ql[..., 3:n - 1] = np.where(vs != 0, out, 0.0)
        return np.moveaxis(ql, -1, axis), np.moveaxis(qr, -1, axis)

    # ------------------------------------------------------------------ LMARS
    def lmars(self, wl, wr, ivx):
        """flux arrays (5, ...) for face states wl, wr; ivx = normal velocity."""
        rl, rr = wl[IDN], wr[IDN]
        pl, pr = wl[IPR], wr[IPR]
        ke_l = 0.5 * (wl[IVX] ** 2 + wl[IVY] ** 2 + wl[IVZ] ** 2)
        ke_r = 0.5 * (wr[IVX] ** 2 + wr[IVY] ** 2 + wr[IVZ] ** 2)
        hl = pl / (GAMMA - 1) / rl + ke_l + pl / rl
        hr = pr / (GAMMA - 1) / rr + ke_r + pr / rr
        rhobar = 0.5 * (rl + rr)
        cbar = np.sqrt(0.5 * GAMMA * (pl + pr) / rhobar)
        ul, ur = wl[ivx], wr[ivx]
        pbar = 0.5 * (pl + pr) + self.lm_p * 0.5 * rhobar * cbar * (ul - ur)
        ubar = 0.5 * (ul + ur) + self.lm_u * 0.5 / (rhobar * cbar) * (pl - pr)
        up = ubar > 0
        F = np.empty_like(wl)
        rho_u = np.where(up, rl, rr)
        F[IDN] = ubar * rho_u
        for v in (IVX, IVY, IVZ):
            F[v] = ubar * rho_u * np.where(up, wl[v], wr[v])
        F[ivx] += pbar
        F[IPR] = ubar * rho_u * np.where(up, hl, hr)
        return F

    # ------------------------------------------------------------- boundaries
    def fill_ghosts(self, U):
        """U: (5, nx, nz) interior conserved -> (5, nx+2NG, nz+2NG) with ghosts.
        x2 periodic; x1 reflecting walls with fixed-T ghosts."""
        nx, nz = self.nx, self.nz
        V = np.zeros((5, nx + 2 * NG, nz + 2 * NG))
        V[:, NG:-NG, NG:-NG] = U
        # x1 walls (on interior columns)
        for side in (0, 1):
            if side == 0:
                g = slice(0, NG); m = slice(2 * NG - 1, NG - 1, -1)
            else:
                g = slice(nz + NG, nz + 2 * NG); m = slice(nz + NG - 1, nz - 1, -1)
            Vm = V[:, NG:-NG, m]
            rho = Vm[IDN]
            ke = 0.5 * (Vm[IVX] ** 2 + Vm[IVY] ** 2 + Vm[IVZ] ** 2) / rho
            pm = (GAMMA - 1) * (Vm[IPR] - ke)
            Tm = pm / (R * rho)
            Tg = 2 * self.Twall[side] - Tm
            V[IDN, NG:-NG, g] = rho
            V[IVX, NG:-NG, g] = -Vm[IVX]
            V[IVY, NG:-NG, g] = Vm[IVY]
            V[IVZ, NG:-NG, g] = Vm[IVZ]
            V[IPR, NG:-NG, g] = rho * CV * Tg + ke
        # x2 periodic (all x1 incl ghosts)
        V[:, :NG, :] = V[:, nx:nx + NG, :]
        V[:, nx + NG:, :] = V[:, NG:2 * NG, :]
        return V

    @staticmethod
    def prim(V):
        W = np.empty_like(V)
        W[IDN] = V[IDN]
        W[IVX:IVZ + 1] = V[IVX:IVZ + 1] / V[IDN]
        ke = 0.5 * (V[IVX] ** 2 + V[IVY] ** 2 + V[IVZ] ** 2) / V[IDN]
        W[IPR] = (GAMMA - 1) * (V[IPR] - ke)
        return W

    # -------------------------------------------------------------------- RHS
    def rhs(self, U, parts=False):
        nx, nz, dz, dx = self.nx, self.nz, self.dz, self.dx
        V = self.fill_ghosts(U)
        W = self.prim(V)
        nc1 = nz + 2 * NG
        il, iu = NG, nz + NG - 1
        I = (slice(NG, -NG), slice(NG, -NG))
        # ---- x1 (vertical) WB reconstruction
        psf_lo, psf_hi, pref, dsf, dref = self.wb_ref(W[IDN], W[IPR])
        Wp = W.copy()
        Wp[IPR] = W[IPR] - pref
        Wp[IDN] = W[IDN] - dref
        for c in (IPR, IDN):
            if self.wall_pert == "odd":
                Wp[c][:, il - NG:il] = -Wp[c][:, il:il + NG][:, ::-1]
                Wp[c][:, iu + 1:iu + 1 + NG] = -Wp[c][:, iu + 1 - NG:iu + 1][:, ::-1]
            elif self.wall_pert == "even":
                Wp[c][:, il - NG:il] = Wp[c][:, il:il + NG][:, ::-1]
                Wp[c][:, iu + 1:iu + 1 + NG] = Wp[c][:, iu + 1 - NG:iu + 1][:, ::-1]
            else:  # smooth: quartic extrapolation from 5 interior cells
                a = Wp[c]
                for m in range(1, NG + 1):
                    a[:, il - m] = 5*a[:, il-m+1] - 10*a[:, il-m+2] + 10*a[:, il-m+3] - 5*a[:, il-m+4] + a[:, il-m+5]
                    a[:, iu + m] = 5*a[:, iu+m-1] - 10*a[:, iu+m-2] + 10*a[:, iu+m-3] - 5*a[:, iu+m-4] + a[:, iu+m-5]
        if self.x1_mom:
            Wp[IVX] = W[IDN] * W[IVX]
        wl, wr = self.recon(Wp, axis=2)
        if self.x1_mom:
            wl[IVX] /= (wl[IDN] + dsf); wr[IVX] /= (wr[IDN] + dsf)
        wl[IPR] += psf_lo; wr[IPR] += psf_lo
        if getattr(self, "dsf_recon", False):  # face reference = same reconstruction of dref
            if getattr(self, "dref_ghost_smooth", False):
                dref = dref.copy()
                for m in range(1, NG + 1):
                    dref[..., il - m] = 5*dref[..., il-m+1] - 10*dref[..., il-m+2] + 10*dref[..., il-m+3] - 5*dref[..., il-m+4] + dref[..., il-m+5]
                    dref[..., iu + m] = 5*dref[..., iu+m-1] - 10*dref[..., iu+m-2] + 10*dref[..., iu+m-3] - 5*dref[..., iu+m-4] + dref[..., iu+m-5]
            dl_, dr_ = self.recon(dref[None], axis=2)
            wl[IDN] += dl_[0]; wr[IDN] += dr_[0]
        else:
            wl[IDN] += dsf; wr[IDN] += dsf
        if getattr(self, "drho_bg", None) is not None:  # remove a background face-density offset
            wl[IDN][:, il:iu + 2] -= self.drho_bg[None, :]
            wr[IDN][:, il:iu + 2] -= self.drho_bg[None, :]
        if self.rho_plain:  # density reconstructed directly (no WB split)
            rl_, rr_ = self.recon(W[IDN:IDN + 1], axis=2)
            wl[IDN] = rl_[0]; wr[IDN] = rr_[0]
        # faces il..iu+1, interior columns
        fs = slice(il, iu + 2)
        F1 = self.lmars(wl[:, NG:-NG, fs], wr[:, NG:-NG, fs], IVX)
        # ---- x2 (horizontal) reconstruction
        wl2, wr2 = self.recon(W, axis=1)
        gs = slice(NG, nx + NG + 1)
        F2 = self.lmars(wl2[:, gs, NG:-NG], wr2[:, gs, NG:-NG], IVY)
        if self.dF != 0.0:
            F2[IPR] += self.dF * self.dF_term(W)
        div = (F1[..., 1:] - F1[..., :-1]) / dz + (F2[:, 1:, :] - F2[:, :-1, :]) / dx
        du = -div
        Wi = W[(slice(None),) + I]
        # ---- const gravity (cell)
        g1 = -G
        du[IVX] += Wi[IDN] * g1
        du[IPR] += Wi[IDN] * Wi[IVX] * g1
        # ---- face form
        if self.form == "face":
            mflux = F1[IDN]  # (nx, nz+1)
            phi_f = G * self.zf
            phi_c = G * self.zc
            mdiv = (mflux[:, 1:] - mflux[:, :-1]) / dz
            pdiv = (phi_f[1:] * mflux[:, 1:] - phi_f[:-1] * mflux[:, :-1]) / dz
            fgw = phi_c * mdiv - pdiv
            if self.curv:
                rhov = W[IDN] * W[IVX]
                rv = rhov[NG:-NG, NG - 1:NG + nz + 1]  # cells il-1..iu+1
                curv = dz / 12 * (rv[:, 1:] - rv[:, :-1])  # faces il..iu+1
                if not self.curv_wall:
                    curv[:, 0] = 0; curv[:, -1] = 0
                fgw -= g1 * (curv[:, 1:] - curv[:, :-1]) / dz
            orig = Wi[IDN] * Wi[IVX] * g1
            du[IPR] += fgw - orig
        if self.dFm != 0.0:
            pass
        # ---- diffusion
        if self.diffusion:
            du -= self.diffusion_div(W)
        return du

    def dF_term(self, W):
        """x2-face covariance correction (to be ADDED to the true-minus-scheme
        sense: scheme flux F2 is too small by this). Computed from cell
        primitives with centred x1 differences, averaged to x2 faces."""
        dz = self.dz
        p, rho, u = W[IPR], W[IDN], W[IVY]
        T = p / (R * rho)
        def d1(f):
            out = (f[:, 2:] - f[:, :-2]) / (2 * dz)
            if self.dF_order == 4:
                o4 = np.zeros_like(out)
                o4[:, 1:-1] = (-f[:, 4:] + 8 * f[:, 3:-1] - 8 * f[:, 1:-3] + f[:, :-4]) / (12 * dz)
                o4[:, 0] = out[:, 0]; o4[:, -1] = out[:, -1]
                out = o4
            return out
        dlnT = d1(np.log(T))
        du_z = d1(u)
        if self.dF_kind == "lnT":
            cell = (GAMMA / (GAMMA - 1)) * dz**2 / 12 * p[:, 1:-1] * dlnT * du_z
        # restrict to interior x1, average to x2 faces (x2 cells NG-1..nx+NG)
        cell = cell[:, NG - 1:NG - 1 + self.nz]
        if not self.dF_wall:
            cell = cell.copy(); cell[:, 0] = 0; cell[:, -1] = 0
        c = cell[NG - 1:self.nx + NG + 1]
        return 0.5 * (c[1:] + c[:-1])

    def diffusion_div(self, W):
        """dynamic isotropic diffusion (diffusion.cpp, dynamic: true)."""
        dz, dx = self.dz, self.dx
        nu, kap = self.mu, self.K
        T = W[IPR] / (R * W[IDN])
        vel = [W[IVX], W[IVY], W[IVZ]]  # x1, x2, x3 components
        h = [dz, dx]
        ax = [1, 0]  # array axis for idir 0 (x1) and 1 (x2) on (nx, nz) slices
        nxg, nzg = W.shape[1], W.shape[2]
        # div_vel on cells extended by one in both active dims
        def cd(f, idir):  # centred derivative on full array, valid inside
            out = np.zeros_like(f)
            if idir == 0:
                out[:, 1:-1] = (f[:, 2:] - f[:, :-2]) / (2 * dz)
            else:
                out[1:-1, :] = (f[2:, :] - f[:-2, :]) / (2 * dx)
            return out
        divv = cd(vel[0], 0) + cd(vel[1], 1)
        divs = []
        fluxes = []
        for idir in (0, 1):
            flux = np.zeros((5, nxg, nzg))  # face f = lower face of cell f
            for ivar in range(3):
                v = vel[ivar]
                if idir == 0:
                    st = np.zeros_like(v); st[:, 1:] = (v[:, 1:] - v[:, :-1]) / dz
                    dfa = np.zeros_like(v); dfa[:, 1:] = 0.5 * (divv[:, 1:] + divv[:, :-1])
                    vfa = np.zeros_like(v); vfa[:, 1:] = 0.5 * (v[:, 1:] + v[:, :-1])
                else:
                    st = np.zeros_like(v); st[1:, :] = (v[1:, :] - v[:-1, :]) / dx
                    dfa = np.zeros_like(v); dfa[1:, :] = 0.5 * (divv[1:, :] + divv[:-1, :])
                    vfa = np.zeros_like(v); vfa[1:, :] = 0.5 * (v[1:, :] + v[:-1, :])
                if ivar == idir:
                    st = 2 * st - 2 / 3 * dfa
                elif ivar < 2:
                    cdv = cd(vel[idir], ivar)
                    if idir == 0:
                        cross = np.zeros_like(v); cross[:, 1:] = 0.5 * (cdv[:, 1:] + cdv[:, :-1])
                    else:
                        cross = np.zeros_like(v); cross[1:, :] = 0.5 * (cdv[1:, :] + cdv[:-1, :])
                    st = st + cross
                mf = -nu * st
                flux[IVX + ivar] = mf
                flux[IPR] += vfa * mf
            if idir == 0:
                dT = np.zeros_like(T); dT[:, 1:] = (T[:, 1:] - T[:, :-1]) / dz
            else:
                dT = np.zeros_like(T); dT[1:, :] = (T[1:, :] - T[:-1, :]) / dx
            flux[IPR] -= kap * dT
            fluxes.append(flux)
        f1, f2 = fluxes
        out = (f1[:, NG:-NG, NG + 1:-NG + 1 if NG > 1 else None] - f1[:, NG:-NG, NG:-NG]) / dz
        out += (f2[:, NG + 1:-NG + 1, NG:-NG] - f2[:, NG:-NG, NG:-NG]) / dx
        return out

    # --------------------------------------------------------- linearisation
    def base_state(self):
        rho, p, T = self.background()
        U0 = np.zeros((5, self.nx, self.nz))
        U0[IDN] = rho
        U0[IPR] = p / (GAMMA - 1)
        return U0

    def operator(self, h=1e-7):
        """complex nvar*nz matrix A for the x2 Fourier mode exp(i k x)."""
        U0 = self.base_state()
        r0 = self.rhs(U0)
        self.residual = np.abs(r0).max()
        nz, nx = self.nz, self.nx
        cosx = np.cos(self.k * self.xc)[:, None]
        sinx = np.sin(self.k * self.xc)[:, None]
        vars_ = [IDN, IVX, IVY, IPR]
        scale = {IDN: U0[IDN, 0], IVX: U0[IDN, 0], IVY: U0[IDN, 0], IPR: U0[IPR, 0]}
        n = len(vars_) * nz
        A = np.zeros((n, n), complex)
        for a, va in enumerate(vars_):
            for i in range(nz):
                eps = h * scale[va][i]
                dU = np.zeros_like(U0)
                dU[va, :, i] = eps * cosx[:, 0]
                Jv = (self.rhs(U0 + dU) - self.rhs(U0 - dU)) / (2 * eps)
                for b, vb in enumerate(vars_):
                    re = 2 / nx * (Jv[vb] * cosx).sum(0)
                    im = -2 / nx * (Jv[vb] * sinx).sum(0)
                    A[b * nz:(b + 1) * nz, a * nz + i] = re + 1j * im
        return A, vars_

    def growth(self, return_vec=False):
        A, vars_ = self.operator()
        lam, V = np.linalg.eig(A)
        ok = np.abs(lam.imag) < 1e-8 + 1e-3 * np.abs(lam.real)
        i = np.argmax(np.where(ok, lam.real, -np.inf))
        if return_vec:
            return lam[i], V[:, i]
        return lam[i].real
