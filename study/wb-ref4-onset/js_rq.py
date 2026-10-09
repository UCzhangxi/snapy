"""First-order growth rate of the mode under nonlinear WENO-JS weights in the
mode-dominated regime: sigma_js ~ psi_L N(psi) / psi_L psi, with psi, psi_L
the eigenvectors of the linear-weight operator and N the centred difference of
the JS right-hand side at a finite mode amplitude (mode >> background rho')."""
import sys
import numpy as np
from wbonset import Column, continuous
from replica import IDN, IVX, IVY, IPR

NH, eps = float(sys.argv[1]), float(sys.argv[2])
nzs = [int(a) for a in sys.argv[3].split(",")]
amps = [float(a) for a in sys.argv[4].split(",")] if len(sys.argv) > 4 else [1e-3, 1e-5]
for nz in nzs:
    out = []
    for name, kw in (("cov", {}), ("covWD", dict(W=True, D=True))):
        d = Column(NH, eps, nz, nx=2 * nz, **kw)
        s0 = continuous(NH, eps, d.k)
        A, vars_ = d.operator()
        lam, V = np.linalg.eig(A)
        i = np.argmax(np.where(np.abs(lam.imag) < 1e-8 + 1e-3 * abs(lam.real), lam.real, -np.inf))
        lamL, VL = np.linalg.eig(A.T)
        j = np.argmin(np.abs(lamL - lam[i]))
        psi, psiL = V[:, i], VL[:, j]
        U0 = d.base_state()
        cosx = np.cos(d.k * d.xc)[:, None]; sinx = np.sin(d.k * d.xc)[:, None]
        res = [f"{name} lin {lam[i].real/s0-1:+.3e}"]
        dj = Column(NH, eps, nz, nx=2 * nz, weno="js", **kw)
        for amp in amps:
            dU = np.zeros_like(U0)
            for b, vb in enumerate(vars_):
                c = psi[b * nz:(b + 1) * nz]
                dU[vb] = np.real(c)[None, :] * cosx - np.imag(c)[None, :] * sinx
            scale = amp / np.max(np.abs(dU[IDN]) / U0[IDN])
            Jv = (dj.rhs(U0 + scale * dU) - dj.rhs(U0 - scale * dU)) / (2 * scale)
            N = np.concatenate([2 / d.nx * (Jv[vb] * cosx).sum(0) - 2j / d.nx * (Jv[vb] * sinx).sum(0) for vb in vars_])
            sj = (psiL @ N) / (psiL @ psi)
            res.append(f"JS@{amp:g} {sj.real/s0-1:+.3e}")
        out.append("  ".join(res))
    print(f"NH {NH} eps {eps} nz {nz}: " + "  |  ".join(out), flush=True)
