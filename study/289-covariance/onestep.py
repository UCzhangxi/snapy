"""One-step eps = 0 entropy tendency of the snapy replica (projected eps_spur * nz^2).
Polytrope T = 1 - z/cp on [0, L]; anelastic field w = sin(pi z/L) cos kx, rho u from
continuity; momentum set to exact cell averages; no diffusion.
  python onestep.py L nz"""
import sys
import numpy as np
from numpy.polynomial.legendre import leggauss
from replica import Deck, IDN, IVX, IVY, IPR, GAMMA, CP, R

L = float(sys.argv[1]); nz = int(sys.argv[2])
xg, wg = leggauss(12)
beta = 1 / CP


def make(form, dF, **kw):
    d = Deck(nz, 0.0, 0.0, form=form, dF=dF, diffusion=False, **kw)
    d.dz = L / nz
    d.zc = (np.arange(nz) + 0.5) * d.dz
    d.zf = np.arange(nz + 1) * d.dz
    d.Lx = 2 * np.sqrt(2) * L
    d.dx = d.Lx / d.nx
    d.k = 2 * np.pi / d.Lx
    d.xc = (np.arange(d.nx) + 0.5) * d.dx
    d.Twall = (1.0, 1.0 - beta * L)
    return d


def tendency(d, amp=1e-7):
    U0 = d.base_state()
    rho_s = lambda z: (1 - beta * z) ** (1 / beta - 1)
    zq = d.zc[:, None] + 0.5 * d.dz * xg[None, :]
    cavg = lambda f: (f(zq) * wg).sum(1) / 2
    m_w = lambda z: rho_s(z) * np.sin(np.pi * z / L)
    e = 1e-6
    dm = lambda z: (m_w(z + e) - m_w(z - e)) / (2 * e)
    sx = np.sin(d.k * d.dx / 2) / (d.k * d.dx / 2)
    cosx = np.cos(d.k * d.xc)[:, None]; sinx = np.sin(d.k * d.xc)[:, None]
    dU = np.zeros_like(U0)
    dU[IVX] = amp * cavg(m_w)[None, :] * cosx * sx
    dU[IVY] = amp * (-cavg(dm) / d.k)[None, :] * sinx * sx
    r = (d.rhs(U0 + dU) - d.rhs(U0 - dU)) / (2 * amp)
    rho = U0[IDN, 0]; p = (GAMMA - 1) * U0[IPR, 0]; T = p / (R * rho)
    ds = (GAMMA - 1) * r[IPR] / (GAMMA * p) - r[IDN] / rho
    dsc = 2 / d.nx * (ds * cosx).sum(0)
    wc = 2 / d.nx * ((dU[IVX] / amp / U0[IDN]) * cosx).sum(0)
    return (rho * wc * T * dsc).sum() / (rho * wc * wc).sum() * nz**2


out = []
for form in ("cell", "face"):
    for dF in (0.0, 1.0):
        out.append(f"{form}{'+dF' if dF else ''} {tendency(make(form, dF)):+.5f}")
out.append(f"cell+dF+rho_w-recon {tendency(make('cell', 1.0, x1_mom=True)):+.5f}")
out.append(f"face+dF wallcons {tendency(make('face', 1.0, curv_wall=True)):+.5f}")
out.append(f"face+dF wallcons rho_plain {tendency(make('face', 1.0, curv_wall=True, rho_plain=True)):+.5f}")
out.append(f"face base rho_plain {tendency(make('face', 0.0, rho_plain=True)):+.5f}")
print(f"L {L} nz {nz}: eps_spur*nz^2 : " + "  ".join(out), flush=True)
