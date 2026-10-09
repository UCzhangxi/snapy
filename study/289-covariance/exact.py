"""Exact linear growth rate for the T1L deck: fully compressible, constant mu,
K = Cp mu, stress-free fixed-T walls, Chebyshev collocation.
Units Lz = R = g = T_b = p_b = 1."""
import numpy as np
import scipy.linalg as sla
from scipy.optimize import brentq

GAMMA = 1.4
R = 1.0
G = 1.0
CV = R / (GAMMA - 1.0)
CP = CV + R
K_WAVE = np.pi / np.sqrt(2.0)


def cheb(N):
    x = np.cos(np.pi * np.arange(N + 1) / N)
    c = np.hstack([2, np.ones(N - 1), 2]) * (-1) ** np.arange(N + 1)
    X = np.tile(x, (N + 1, 1)).T
    dX = X - X.T
    D = np.outer(c, 1 / c) / (dX + np.eye(N + 1))
    D -= np.diag(D.sum(1))
    return D, x


def background(z, eps):
    beta = G / CP + eps * G / R
    T0 = 1 - beta * z
    p0 = T0 ** (G / (R * beta))
    rho0 = p0 / (R * T0)
    return beta, T0, p0, rho0


def operators(eps, mu, N=64, k=K_WAVE, extra=None):
    """A q = sigma B q, q = [rho, u, w, T]. extra(z, ops) -> 4x4 block matrix
    added to A (a perturbation operator in the same variables)."""
    D, x = cheb(N)
    z = (1 - x) / 2  # z from 0 to 1 (x=1 -> z=0)
    Dz = -2 * D
    D2 = Dz @ Dz
    n = N + 1
    I = np.eye(n)
    beta, T0, p0, rho0 = background(z, eps)
    dT0 = -beta * np.ones(n)
    Kc = CP * mu
    ik = 1j * k
    dg = np.diag
    Z = np.zeros((n, n))
    # p' = R(rho0 T' + T0 rho')
    P_rho = R * dg(T0)
    P_T = R * dg(rho0)
    lap = D2 - k**2 * I
    # continuity
    A11 = Z.copy(); A12 = -ik * dg(rho0); A13 = -Dz @ dg(rho0); A14 = Z.copy()
    # x-momentum
    A21 = -ik * P_rho
    A22 = mu * (lap + (1 / 3) * ik * ik * I)
    A23 = mu * (1 / 3) * ik * Dz
    A24 = -ik * P_T
    # z-momentum
    A31 = -Dz @ P_rho - G * I
    A32 = mu * (1 / 3) * ik * Dz
    A33 = mu * (lap + (1 / 3) * D2)
    A34 = -Dz @ P_T
    # energy (T)
    A41 = Z.copy()
    A42 = -ik * dg(p0)
    A43 = -dg(rho0 * CV * dT0) - dg(p0) @ Dz
    A44 = Kc * lap
    A = np.block([[A11, A12, A13, A14], [A21, A22, A23, A24],
                  [A31, A32, A33, A34], [A41, A42, A43, A44]]).astype(complex)
    B = np.block([[I, Z, Z, Z], [Z, dg(rho0), Z, Z], [Z, Z, dg(rho0), Z],
                  [Z, Z, Z, dg(rho0 * CV)]]).astype(complex)
    if extra is not None:
        A = A + extra(z, dict(Dz=Dz, D2=D2, rho0=rho0, p0=p0, T0=T0, beta=beta,
                              k=k, n=n))
    # BCs: u_z = 0, w = 0, T = 0 at both walls (rows 0 and N of each block)
    for b in (0, N):
        for blk, row in ((1, Dz[b]), (2, I[b]), (3, I[b])):
            r = blk * n + b
            A[r, :] = 0
            A[r, blk * n:(blk + 1) * n] = row
            B[r, :] = 0
    return A, B, z


def growth(eps, mu, N=64, extra=None, return_vec=False):
    A, B, z = operators(eps, mu, N, extra=extra)
    lam, V = sla.eig(A, B)
    ok = np.isfinite(lam) & (np.abs(lam) < 1e3)
    lam = lam[ok]; V = V[:, ok]
    # slow, real-ish modes: pick largest real part among |imag| small
    i = np.argmax(np.where(np.abs(lam.imag) < 1e-6 + 1e-3 * np.abs(lam.real), lam.real, -np.inf))
    if return_vec:
        return lam[i], V[:, i], z
    return lam[i].real


def ra_c(eps, N=64):
    f = lambda lnmu: growth(eps, np.exp(lnmu), N)
    # sigma decreases with mu; bracket
    lo, hi = np.log(1e-4), np.log(1.0)
    lnmu = brentq(f, np.log(np.sqrt(eps / 5000)), np.log(np.sqrt(eps / 200)), xtol=1e-14)
    mu = np.exp(lnmu)
    return eps / mu**2


def deck_mu(eps, N=64):
    return np.sqrt(eps / (50 * ra_c(eps, N)))


if __name__ == "__main__":
    for N in (48, 64, 80):
        print(N, "Ra_c(0.02) =", repr(ra_c(0.02, N)), " (target 1268.5968053249962)")
    for eps, tgt_rac, tgt_s in ((1e-3, 1300.080007, 0.01669758006), (1e-4, None, 0.005278896843)):
        rc = ra_c(eps)
        mu = np.sqrt(eps / (50 * rc))
        s = growth(eps, mu)
        print(f"eps {eps}: Ra_c {rc:.6f} (tgt {tgt_rac}) sigma {s:.11f} (tgt {tgt_s}) mu {mu:.6e}")
