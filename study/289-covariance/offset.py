"""Verifier for the WB x1 face-density offset (hydro_ref_x1_impl.h, CPU path).
Cell-averaged polytrope (exact cell averages, eps = 0), depth Dp pressure e-folds.
 (1) background face density rho_f = dsf + R(rho - dref) vs exact rho(z_f);
     interior formula  drho_f = dz^2 [ p f''/6 + p' f'/12 ],  f = rho/p.
 (2) one-step projected eps_spur*nz^2: base / +dF / with the offset removed
     (rho reconstructed directly) / predicted offset contribution from (1).
  python offset.py Dp nz"""
import sys
import numpy as np
from numpy.polynomial.legendre import leggauss
from replica import Deck, IDN, IVX, IVY, IPR, NG, GAMMA, CP, R

Dp = float(sys.argv[1]); nz = int(sys.argv[2])
beta = 1 / CP
L = (1 - np.exp(-beta * Dp)) / beta
xg, wg = leggauss(16)
Tf = lambda z: 1 - beta * z
pf = lambda z: Tf(z) ** (1 / beta)
rf_ = lambda z: pf(z) / Tf(z)


def make(form, dF, **kw):
    d = Deck(nz, 0.0, 0.0, form=form, dF=dF, diffusion=False, **kw)
    d.dz = L / nz
    d.zc = (np.arange(nz) + 0.5) * d.dz
    d.zf = np.arange(nz + 1) * d.dz
    d.Lx = 2 * np.sqrt(2) * L; d.dx = d.Lx / d.nx; d.k = 2 * np.pi / d.Lx
    d.xc = (np.arange(d.nx) + 0.5) * d.dx
    d.Twall = (1.0, 1.0 - beta * L)
    zq = d.zc[:, None] + 0.5 * d.dz * xg[None, :]
    avg = lambda f: (f(zq) * wg).sum(1) / 2
    rho_c, p_c = avg(rf_), avg(pf)
    d.background = lambda balance=True: (rho_c, p_c, p_c / rho_c)
    return d


def face_density(d):
    U0 = d.base_state()
    V = d.fill_ghosts(U0); W = d.prim(V)
    psf_lo, psf_hi, pref, dsf, dref = d.wb_ref(W[IDN], W[IPR])
    Wp = W.copy(); Wp[IPR] = W[IPR] - pref; Wp[IDN] = W[IDN] - dref
    il, iu = NG, nz + NG - 1
    for c in (IPR, IDN):
        Wp[c][:, il - NG:il] = Wp[c][:, il:il + NG][:, ::-1]
        Wp[c][:, iu + 1:iu + 1 + NG] = Wp[c][:, iu + 1 - NG:iu + 1][:, ::-1]
    wl, wr = d.recon(Wp, axis=2)
    if getattr(d, "dsf_recon", False):
        if getattr(d, "dref_ghost_smooth", False):
            dref = dref.copy()
            for m in range(1, NG + 1):
                dref[..., il - m] = 5*dref[..., il-m+1] - 10*dref[..., il-m+2] + 10*dref[..., il-m+3] - 5*dref[..., il-m+4] + dref[..., il-m+5]
                dref[..., iu + m] = 5*dref[..., iu+m-1] - 10*dref[..., iu+m-2] + 10*dref[..., iu+m-3] - 5*dref[..., iu+m-4] + dref[..., iu+m-5]
        dl_, dr_ = d.recon(dref[None], axis=2)
        rho_f = 0.5 * (wl[IDN] + dl_[0] + wr[IDN] + dr_[0])[0, il:iu + 2]
    else:
        rho_f = 0.5 * (wl[IDN] + wr[IDN] + 2 * dsf)[0, il:iu + 2]
    p_f = 0.5 * (wl[IPR] + wr[IPR] + 2 * psf_lo)[0, il:iu + 2]
    return rho_f, p_f, np.abs(d.rhs(U0)).max()


def tendency(d, amp=1e-7):
    U0 = d.base_state()
    zq = d.zc[:, None] + 0.5 * d.dz * xg[None, :]
    cavg = lambda f: (f(zq) * wg).sum(1) / 2
    m_w = lambda z: rf_(z) * np.sin(np.pi * z / L)
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


d = make("face", 0.0)
rho_f, p_f, res = face_density(d)
zf = d.zf
f = lambda z: rf_(z) / pf(z)
e = 1e-5
f1 = (f(zf + e) - f(zf - e)) / (2 * e); f2 = (f(zf + e) - 2 * f(zf) + f(zf - e)) / e**2
p1 = -rf_(zf)
pred = d.dz**2 * (pf(zf) * f2 / 6 + p1 * f1 / 12)
err = rho_f - rf_(zf)
k = [nz // 4, nz // 2, 3 * nz // 4]
print(f"Dp {Dp} (L={L:.3f}, T_top={1-beta*L:.3f}) nz {nz}: rest residual {res:.1e}")
print("   interior drho_f/(rho dz^2): measured " + " ".join(f"{err[i]/rf_(zf[i])/d.dz**2:+.5f}" for i in k)
      + "   formula " + " ".join(f"{pred[i]/rf_(zf[i])/d.dz**2:+.5f}" for i in k))
print("   wall faces (1..3 from bottom / top) drho_f/(rho dz^2): "
      + " ".join(f"{err[i]/rf_(zf[i])/d.dz**2:+.3f}" for i in (1, 2, 3)) + " / "
      + " ".join(f"{err[-1-i]/rf_(zf[-1-i])/d.dz**2:+.3f}" for i in (1, 2, 3))
      + f";  p_f max rel err/dz^2 {np.abs((p_f-pf(zf))/pf(zf))[1:-1].max()/d.dz**2:.2e}")
off = rho_f - rf_(zf)            # background offset at faces il..iu+1
dfx = make("face", 0.0); dfx.dsf_recon = True
dfc = make("face", 0.0); dfc.dsf_recon = "C"; dfc.rs_wall_exact = dfc.dref_ghost_smooth = True
rho_c2, _, resc = face_density(dfc)
print(f"   C: rest residual {resc:.1e}; |drho_f/rho|/dz^2 interior max {np.max(np.abs((rho_c2-rf_(zf))/rf_(zf))[4:-4])/d.dz**2:.2e}; wall faces 1..3 bottom/top " + " ".join(f"{(rho_c2[i]-rf_(zf[i]))/rf_(zf[i])/d.dz**2:+.2e}" for i in (1,2,3,-2,-3,-4)))
rho_fx, _, resx = face_density(dfx)
print(f"   FIX (dsf = R(dref)): rest residual {resx:.1e}; max |drho_f/rho|/dz^2 interior {np.max(np.abs((rho_fx-rf_(zf))/rf_(zf))[4:-4])/d.dz**2:.2e}, wall faces {np.max(np.abs((rho_fx-rf_(zf))/rf_(zf))[1:4])/d.dz**2:.2e} {np.max(np.abs((rho_fx-rf_(zf))/rf_(zf))[-4:-1])/d.dz**2:.2e}")
off_int = off.copy(); off_int[:4] = 0; off_int[-4:] = 0
def mk(form, dF, drho=None, fix=False, **kw):
    dd = make(form, dF, **kw); dd.drho_bg = drho; dd.dsf_recon = fix
    dd.rs_wall_exact = dd.dref_ghost_smooth = (fix == "C"); return dd
out = {}
for name, form, dF, drho, kw in (("face base", "face", 0.0, None, {}),
                                  ("face+dF", "face", 1.0, None, {}),
                                  ("face+dF -offset", "face", 1.0, off, {}),
                                  ("face+dF -interior offset", "face", 1.0, off_int, {}),
                                  ("faceWC+dF", "face", 1.0, None, dict(curv_wall=True)),
                                  ("faceWC+dF -offset", "face", 1.0, off, dict(curv_wall=True)),
                                  ("cell base", "cell", 0.0, None, {}),
                                  ("cell+dF", "cell", 1.0, None, {}),
                                  ("cell+dF -offset", "cell", 1.0, off, {}),
                                  ("faceWC+dF FIX", "face", 1.0, "fix", dict(curv_wall=True)),
                                  ("face+dF FIX", "face", 1.0, "fix", {}),
                                  ("cell+dF FIX", "cell", 1.0, "fix", {}),
                                  ("face base FIX", "face", 0.0, "fix", {}),
                                  ("faceWC+dF C", "face", 1.0, "C", dict(curv_wall=True)),
                                  ("face+dF C", "face", 1.0, "C", {}),
                                  ("cell+dF C", "cell", 1.0, "C", {}),
                                  ("cell+dF+mom C", "cell", 1.0, "C", dict(x1_mom=True))):
    if isinstance(drho, str):
        out[name] = tendency(mk(form, dF, None, fix=(True if drho == "fix" else "C"), **kw))
    else:
        out[name] = tendency(mk(form, dF, drho, **kw))
print("   eps*nz^2: " + "  ".join(f"{k} {v:+.5f}" for k, v in out.items()), flush=True)
