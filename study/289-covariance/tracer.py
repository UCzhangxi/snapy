"""Compositional buoyancy test of the x2 tracer-flux covariance.
State [rho, u, w, T, q]; ideal gas with R_mix = R (1 + delta q); cv fixed.
Background: T0 = 1 - beta z, q0 = qb exp(-z/Hq), hydrostatic p0 integrated.
Truncation term of the scheme (x2 tracer flux too small by dz^2/12 rho u_z q_z):
   rho0 dq/dt += dz^2/12 rho0 q0_z d_x d_z u  ->  sigma q += dz^2/12 q0_z ik Dz u."""
import numpy as np, scipy.linalg as sla
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from exact import cheb, K_WAVE, CV, CP, R, G, GAMMA


def ops(eps, mu, delta, qb, Hq=1.0, N=64, dz=None, qz_scale=1.0):
    D, x = cheb(N); z = (1 - x) / 2; Dz = -2 * D; D2 = Dz @ Dz; n = N + 1
    I = np.eye(n); dg = np.diag; Zm = np.zeros((n, n)); k = K_WAVE; ik = 1j * k
    beta = G / CP + eps * G / R
    T0 = 1 - beta * z
    q0 = qb * np.exp(-z / Hq); q0z = -q0 / Hq
    Rm = R * (1 + delta * q0)
    lnp = lambda zz: -G / (R * (1 + delta * qb * np.exp(-zz / Hq)) * (1 - beta * zz))
    sol = solve_ivp(lambda zz, y: lnp(zz), (0, 1), [0.0], dense_output=True, rtol=1e-12, atol=1e-14)
    p0 = np.exp(sol.sol(z)[0]); rho0 = p0 / (Rm * T0)
    lap = D2 - k**2 * I
    # p' = Rm (rho0 T' + T0 rho') + R delta rho0 T0 q'
    Pr, PT, Pq = dg(Rm * T0), dg(Rm * rho0), dg(R * delta * rho0 * T0)
    D_q = mu / rho0[0]
    A = np.zeros((5 * n, 5 * n), complex); B = np.zeros_like(A)
    b = lambda i, j: (slice(i * n, (i + 1) * n), slice(j * n, (j + 1) * n))
    A[b(0, 1)] = -ik * dg(rho0); A[b(0, 2)] = -Dz @ dg(rho0)
    A[b(1, 0)] = -ik * Pr; A[b(1, 1)] = mu * (lap - k**2 / 3 * I); A[b(1, 2)] = mu / 3 * ik * Dz
    A[b(1, 3)] = -ik * PT; A[b(1, 4)] = -ik * Pq
    A[b(2, 0)] = -Dz @ Pr - G * I; A[b(2, 1)] = mu / 3 * ik * Dz; A[b(2, 2)] = mu * (lap + D2 / 3)
    A[b(2, 3)] = -Dz @ PT; A[b(2, 4)] = -Dz @ Pq
    A[b(3, 1)] = -ik * dg(p0); A[b(3, 2)] = -dg(rho0 * CV * (-beta)) - dg(p0) @ Dz
    A[b(3, 3)] = CP * mu * lap
    A[b(4, 2)] = -dg(q0z * qz_scale); A[b(4, 4)] = D_q * lap
    if dz is not None:
        A[b(4, 1)] += dz**2 / 12 * dg(q0z) @ (ik * Dz)
    for i, d in enumerate((1, rho0, rho0, rho0 * CV, 1)):
        B[b(i, i)] = dg(np.ones(n) * d)
    for e in (0, N):
        for blk, row in ((1, Dz[e]), (2, I[e]), (3, I[e]), (4, I[e])):
            r = blk * n + e; A[r, :] = 0; A[r, blk * n:(blk + 1) * n] = row; B[r, :] = 0
    return A, B


def sigma(*a, **kw):
    A, B = ops(*a, **kw)
    lam = sla.eig(A, B, right=False)
    ok = np.isfinite(lam) & (np.abs(lam) < 1e3) & (np.abs(lam.imag) < 1e-6)
    return lam[ok].real.max()


if __name__ == "__main__":
    from exact import deck_mu
    eps = 1e-3; mu = deck_mu(eps)
    for name, delta, qb in (("earth water (light vapour)", 1 / 0.622 - 1, 0.02),
                            ("jupiter water (heavy vapour)", 18 / 2.3 - 1, 0.01)):
        s0 = sigma(eps, mu, delta, qb)
        for nz in (16, 32, 64):
            dz = 1 / nz
            s1 = sigma(eps, mu, delta, qb, dz=dz)
            s2 = sigma(eps, mu, delta, qb, qz_scale=1 - np.pi**2 * dz**2 / 12)
            print(f"{name}: sigma0 {s0:.6f}; nz {nz}: covariance term rel {s1/s0-1:+.5f}; "
                  f"q0_z*(1-pi^2dz^2/12) rel {s2/s0-1:+.5f}")
