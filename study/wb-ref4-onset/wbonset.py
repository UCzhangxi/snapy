"""Linear onset replica for snapy's x1 WB reference with SNAP_WB_REF4 (W) and
SNAP_GRAVITY_WORK_RADIAL_EXACT (D), on a uniform Cartesian column.

Discrete: replica.Deck (numpy clone of hydro_forward @117e449: WB x1
reconstruction, WENO5 linear weights, LMARS, face gravity work, x2 flux
covariance 'cov'), extended with
  W  : dref = pref * F(rho/p), F = (-1,4,10,4,-1)/16 with cubic wall
       extrapolation (wb_ref4.cpp:120-163, 263-272); dsf = 4th-order face value
       of dref (wb_ref4.cpp:195-221, 276-286), range guards as coded;
  D  : face work + grav1 dz^2/12 slope(-div_1 F_rho), curvature flux off
       (hydro_forward.cpp:765-771, gravity_work_radial.hpp:57-63);
  fixes (see docs/onset-wb-ref4.md).
Inviscid, reflecting walls. Background: exact cell averages of
T = 1 - beta z, beta = g/cp + eps g/R, depth NH pressure e-folds.
Linear operator for one x2 Fourier mode by centred JVPs; growth rate =
largest real eigenvalue. Continuous: inviscid Chebyshev eigenproblem."""
import sys
import numpy as np
import scipy.linalg as sla
from numpy.polynomial.legendre import leggauss
from replica import Deck, IDN, IVX, IVY, IVZ, IPR, NG, GAMMA, CP, CV, R, G

XG, WG = leggauss(8)


def depth(NH, eps):
    beta = G / CP + eps * G / R
    return (1 - np.exp(-NH * R * beta / G)) / beta, beta


# ----------------------------------------------------------------- continuous
def cheb(N):
    x = np.cos(np.pi * np.arange(N + 1) / N)
    c = np.hstack([2, np.ones(N - 1), 2]) * (-1) ** np.arange(N + 1)
    X = np.tile(x, (N + 1, 1)).T
    D = np.outer(c, 1 / c) / (X - X.T + np.eye(N + 1))
    return D - np.diag(D.sum(1)), x


def continuous(NH, eps, k, N=(96, 144)):
    """largest real eigenvalue present (to 1e-7 relative) at both resolutions:
    the inviscid collocation has one spurious wall mode that moves with N"""
    a, b = (_spectrum(NH, eps, k, n) for n in N)
    good = [x for x in a if np.min(np.abs(b - x)) < 1e-7 * abs(x)]
    return max(good)


def _spectrum(NH, eps, k, N):
    L, beta = depth(NH, eps)
    D, x = cheb(N); z = (1 - x) / 2 * L; Dz = -2 / L * D; n = N + 1
    I = np.eye(n); Zr = np.zeros((n, n)); dg = np.diag; ik = 1j * k
    T0 = 1 - beta * z; p0 = T0 ** (G / (R * beta)); rho0 = p0 / (R * T0)
    Pr, PT = R * dg(T0), R * dg(rho0)
    A = np.block([
        [Zr, -ik * dg(rho0), -Dz @ dg(rho0), Zr],
        [-ik * Pr, Zr, Zr, -ik * PT],
        [-Dz @ Pr - G * I, Zr, Zr, -Dz @ PT],
        [Zr, -ik * dg(p0), dg(rho0 * CV * beta) - dg(p0) @ Dz, Zr]]).astype(complex)
    B = np.block([[I, Zr, Zr, Zr], [Zr, dg(rho0), Zr, Zr], [Zr, Zr, dg(rho0), Zr],
                  [Zr, Zr, Zr, dg(rho0 * CV)]]).astype(complex)
    for e in (0, N):
        r = 2 * n + e; A[r, :] = 0; A[r, r] = 1; B[r, :] = 0
    lam = sla.eig(A, B, right=False)
    ok = np.isfinite(lam) & (np.abs(lam) < 1e2) & (np.abs(lam.imag) < 1e-7) & (lam.real > 0)
    return np.sort(lam[ok].real)[::-1]


# ------------------------------------------------------------------- discrete
class Column(Deck):
    def __init__(self, NH, eps, nz, W=False, D=False, cov=True, fix=None,
                 nx=8, **kw):
        super().__init__(nz, eps, 0.0, form="face", dF=1.0 if cov else 0.0,
                         diffusion=False, nx=nx, **kw)
        L, beta = depth(NH, eps)
        self.L, self.beta = L, beta
        self.dz = L / nz
        self.zc = (np.arange(nz) + 0.5) * self.dz
        self.zf = np.arange(nz + 1) * self.dz
        self.Lx = 2 * np.sqrt(2) * L
        self.dx = self.Lx / self.nx
        self.k = 2 * np.pi / self.Lx
        self.xc = (np.arange(self.nx) + 0.5) * self.dx
        self.Twall = (1.0, 1.0 - beta * L)
        self.W, self.D, self.fix = W, D, fix
        if D:
            self.curv = False

    def background(self, balance=True):
        zq = self.zc[:, None] + 0.5 * self.dz * XG[None, :]
        avg = lambda f: (f(zq) * WG).sum(1) / 2
        T = lambda z: 1 - self.beta * z
        p = lambda z: T(z) ** (G / (R * self.beta))
        rho = lambda z: p(z) / (R * T(z))
        rc, pc = avg(rho), avg(p)
        return rc, pc, pc / (R * rc)

    def fill_ghosts(self, U):
        V = super().fill_ghosts(U)
        if getattr(self, "ghostT", "fixed") == "mirror":   # reflecting: T even
            nz = self.nz
            for g, m in ((slice(0, NG), slice(2 * NG - 1, NG - 1, -1)),
                         (slice(nz + NG, nz + 2 * NG), slice(nz + NG - 1, nz - 1, -1))):
                V[IPR, NG:-NG, g] = V[IPR, NG:-NG, m]
            V[:, :NG, :] = V[:, self.nx:self.nx + NG, :]
            V[:, self.nx + NG:, :] = V[:, NG:2 * NG, :]
        return V

    # --- W: the fourth-order density reference (uniform grid)
    def wb_ref(self, rho, p):
        psf_lo, psf_hi, pref, dsf, dref = super().wb_ref(rho, p)
        if not self.W:
            return psf_lo, psf_hi, pref, dsf, dref
        nc1 = rho.shape[-1]; il, iu = NG, nc1 - NG - 1
        r = rho / p
        F = np.array([-1, 4, 10, 4, -1]) / 16
        E = [np.array([4., -6., 4., -1.]), np.array([10., -20., 15., -4.])]
        dref = dref.copy(); d_old = dref.copy()
        for i in range(il, iu + 1):
            fr = 0.0
            for m in range(-2, 3):
                j = i + m
                if j < il:
                    fr = fr + F[m + 2] * sum(E[il - j - 1][q] * r[..., il + q] for q in range(4))
                elif j > iu:
                    fr = fr + F[m + 2] * sum(E[j - iu - 1][q] * r[..., iu - q] for q in range(4))
                else:
                    fr = fr + F[m + 2] * r[..., j]
            nb = r[..., [max(il, i - 1), i, min(iu, i + 1)]]
            lo, hi = nb.min(-1), nb.max(-1)
            ok = (fr >= lo - 1e-10 * abs(lo)) & (fr <= hi + 1e-10 * abs(hi))
            dref[..., i] = np.where(ok, pref[..., i] * fr, d_old[..., i])
        dsf = dsf.copy()
        for f in range(il, iu + 2):
            s = min(max(f - 2, il), iu - 3)
            wts = face_weights(f - s)
            face = sum(wts[q] * dref[..., s + q] for q in range(4))
            if self.fix == "dsf_unguarded":
                dsf[..., f] = face; continue
            dl, dr = dref[..., f - 1], dref[..., f]
            lo, hi = np.minimum(dl, dr), np.maximum(dl, dr)
            ok = (face >= lo - 1e-10 * abs(lo)) & (face <= hi + 1e-10 * abs(hi))
            dsf[..., f] = np.where(ok, face, dsf[..., f])
        return psf_lo, psf_hi, pref, dsf, dref

    # --- D: corrected-PE work instead of the curvature flux
    def rhs(self, U, parts=False):
        du = super().rhs(U)
        if self.D:
            V = self.fill_ghosts(U); Wp = self.prim(V)
            F1 = self._mass_flux1(U)
            mdiv = (F1[:, 1:] - F1[:, :-1]) / self.dz          # cells
            drho = -mdiv
            sl = np.zeros_like(drho); h = self.dz
            sl[:, 1:-1] = (drho[:, 2:] - drho[:, :-2]) / (2 * h)
            sl[:, 0] = (-3 * drho[:, 0] + 4 * drho[:, 1] - drho[:, 2]) / (2 * h)
            sl[:, -1] = (drho[:, -3] - 4 * drho[:, -2] + 3 * drho[:, -1]) / (2 * h)
            du[IPR] += (-G) * h**2 / 12 * sl
        return du

    def _mass_flux1(self, U):
        # recompute the x1 mass flux exactly as Deck.rhs does (cached there)
        return self._F1[IDN]


def face_weights(t):
    """weights of cells s..s+3 for the face at index s+t (t = 0..4): derivative
    of the quartic through the primitive at 5 faces (uniform), wb_ref4.cpp:195"""
    X = np.arange(5) - t
    def dl(j):
        s = 0.0
        for l in range(5):
            if l == j: continue
            pr = 1 / (X[j] - X[l])
            for m in range(5):
                if m in (j, l): continue
                pr *= (0 - X[m]) / (X[j] - X[m])
            s += pr
        return s
    return [sum(dl(j) for j in range(k + 1, 5)) for k in range(4)]


if __name__ == "__main__":
    print([np.round(np.array(face_weights(t)) * 12, 6) for t in (0, 1, 2)])
