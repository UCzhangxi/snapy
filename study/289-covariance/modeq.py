"""Modified-equation predictions: add candidate O(dz^2) truncation terms to the
exact linear operator and measure the growth-rate change."""
import numpy as np
from exact import growth, deck_mu, CP, CV, R, G, GAMMA

def blocks(n):
    return lambda i, j: (slice(i * n, (i + 1) * n), slice(j * n, (j + 1) * n))


def term_dF(dz, coef=1.0):
    """x2 enthalpy-flux covariance: scheme flux = true - dF,
    dF = Cp/R dz^2/12 p0 (ln T0)_z u_z -> rho0 Cv dT/dt += ik dF"""
    def extra(z, o):
        n = o["n"]; b = blocks(n)
        E = np.zeros((4 * n, 4 * n), complex)
        E[b(3, 1)] = coef * 1j * o["k"] * (CP / R) * dz**2 / 12 * np.diag(o["p0"] * (-o["beta"] / o["T0"])) @ o["Dz"]
        return E
    return extra


def term_dFm(dz, form, coef=1.0):
    """x1 mass flux error from w_prim = <rho w>/<rho>: dFm = dz^2/12 rho0_z w_z.
    form 'cell': gravity work from cell <rho w> (does not see dFm);
    form 'face': gravity work from the face mass flux (sees dFm)."""
    def extra(z, o):
        n = o["n"]; b = blocks(n); Dz = o["Dz"]
        rho0, T0, beta = o["rho0"], o["T0"], o["beta"]
        drho = Dz @ rho0
        M = coef * dz**2 / 12 * np.diag(drho) @ Dz  # dFm = M w
        E = np.zeros((4 * n, 4 * n), complex)
        E[b(0, 2)] = -Dz @ M
        # rho0 Cv dT = -R T0 d_z dF - Cp T0_z dF  (- g dF in face form)
        hz = CP * (-beta)
        E[b(3, 2)] = -np.diag(R * T0) @ Dz @ M - hz * M - (G * M if form == "face" else 0)
        return E
    return extra


if __name__ == "__main__":
    for eps in (1e-3, 2.56e-4, 1e-4, 0.02):
        mu = deck_mu(eps)
        s0 = growth(eps, mu)
        for nz in (16, 32, 64):
            dz = 1.0 / nz
            r = {}
            r["dF"] = growth(eps, mu, extra=term_dF(dz)) / s0 - 1
            r["dFm_cell"] = growth(eps, mu, extra=term_dFm(dz, "cell")) / s0 - 1
            r["dFm_face"] = growth(eps, mu, extra=term_dFm(dz, "face")) / s0 - 1
            both_c = lambda z, o: term_dF(dz)(z, o) + term_dFm(dz, "cell")(z, o)
            both_f = lambda z, o: term_dF(dz)(z, o) + term_dFm(dz, "face")(z, o)
            r["cell"] = growth(eps, mu, extra=both_c) / s0 - 1
            r["face"] = growth(eps, mu, extra=both_f) / s0 - 1
            print(f"eps {eps:g} nz {nz}: " + "  ".join(f"{k} {v:+.4f}" for k, v in r.items())
                  + f"   C_dF={-r['dF']*eps*nz**2:.4f}")
