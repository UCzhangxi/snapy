"""#289 item 4: rho u_z q_z (snapy: q = <rho q>/<rho>, mass weighted) vs m_z q_z
(covariance against the unweighted <q>). Linear: m_z q_z = rho0 u_z q0_z + rho0_z u q0_z;
the second piece is NOT a scheme error for snapy's storage."""
import numpy as np, scipy.linalg as sla
from tracer import ops
from exact import cheb, K_WAVE, deck_mu


def sigma_form(eps, mu, delta, qb, nz, form, N=64):
    A, B = ops(eps, mu, delta, qb, N=N, dz=1 / nz)          # rho u_z q_z (correct)
    if form == "m":                                          # add rho0_z/rho0 u q0_z piece
        D, x = cheb(N); z = (1 - x) / 2; Dz = -2 * D; n = N + 1
        rho0 = np.real(np.diag(B[n:2 * n, n:2 * n])).copy()  # B row 1 holds rho0
        rho0[[0, N]] = np.nan                                 # BC rows zeroed: rebuild ends
        ii = np.arange(1, N)
        rho0 = np.exp(np.polyval(np.polyfit(z[ii], np.log(rho0[ii]), 12), z))
        q0z = -qb * np.exp(-z)
        lr = (Dz @ np.log(rho0))
        row = slice(4 * n, 5 * n); col = slice(n, 2 * n)
        add = (1 / nz)**2 / 12 * np.diag(q0z * lr) * (1j * K_WAVE)
        add[[0, N], :] = 0                                    # keep BC rows
        A[row, col] += add
    lam = sla.eig(A, B, right=False)
    ok = np.isfinite(lam) & (np.abs(lam) < 1e3) & (np.abs(lam.imag) < 1e-6)
    return lam[ok].real.max()


def sigma0(eps, mu, delta, qb, N=64):
    A, B = ops(eps, mu, delta, qb, N=N)
    lam = sla.eig(A, B, right=False)
    ok = np.isfinite(lam) & (np.abs(lam) < 1e3) & (np.abs(lam.imag) < 1e-6)
    return lam[ok].real.max()


if __name__ == "__main__":
    mu = deck_mu(1e-3)
    for name, eps, delta, qb in (("earth water, eps 1e-3", 1e-3, 1 / 0.622 - 1, 0.02),
                                 ("heavy vapour q 0.01, eps_T 0.01", 0.01, 2.3 / 18 - 1, 0.01),
                                 ("heavy vapour q 0.01, eps_T 0.0095", 0.0095, 2.3 / 18 - 1, 0.01)):
        s0 = sigma0(eps, mu, delta, qb)
        out = []
        for nz in (16, 32, 64):
            r = sigma_form(eps, mu, delta, qb, nz, "r") / s0 - 1
            m = sigma_form(eps, mu, delta, qb, nz, "m") / s0 - 1
            out.append(f"nz {nz}: rho u_z q_z {r:+.5f}  m_z q_z {m:+.5f}")
        print(f"{name}: sigma0 {s0:.6f}\n   " + "\n   ".join(out))
