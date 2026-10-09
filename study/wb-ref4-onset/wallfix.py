"""Rest face density of snapy's default x1 WB reference near the walls, and the
minimal wall fix (hydro_ref_x1_impl.h:68-78, 159-167).

rho_f = R_even[rho - dref] + dsf   (hydro_forward.cpp:269-315)
  default : B = (1,4,6,4,1)/16 of r = rho/p with EDGE REPLICATION past a
            clamped wall (rop_smooth, j clamped to [jlo, jhi])
  cubic   : the same B, but the values past a clamped wall are the cubic
            extrapolation (in cell index) of the four owned cells next to it
            (only the out-of-range reads change; interior cells bitwise equal)
  lin     : linear-exact two-cell closure (rs = r at the wall cell,
            (1,2,1)/4 at the next), for comparison
  W       : SNAP_WB_REF4 (wbonset.Column)
Background: exact cell averages of T = 1 - beta z, NH pressure e-folds.
  python wallfix.py NH eps"""
import sys
import numpy as np
from wbonset import Column
from replica import IDN, IPR, NG

NH = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
eps = float(sys.argv[2]) if len(sys.argv) > 2 else 1e-3

# Lagrange extrapolation to index -m from values at 0,1,2,3
EXT = {m: np.array([np.prod([(-m - b) / (a - b) for b in range(4) if b != a]) for a in range(4)])
       for m in (1, 2, 3, 4, 5)}


def smooth(r, il, iu, mode):
    """B of r (..., nc1) for every cell, reads past [il, iu] per mode"""
    nc1 = r.shape[-1]
    def val(j):
        if il <= j <= iu or mode == "none":
            return r[..., min(max(j, 0), nc1 - 1)]
        if mode == "edge":
            return r[..., il if j < il else iu]
        if j < il:
            return sum(EXT[il - j][q] * r[..., il + q] for q in range(4))
        return sum(EXT[j - iu][q] * r[..., iu - q] for q in range(4))
    B = (1, 4, 6, 4, 1)
    return np.stack([sum(B[m + 2] * val(i + m) for m in range(-2, 3)) / 16
                     for i in range(nc1)], -1)


class WallCol(Column):
    def __init__(self, *a, ref="default", **kw):
        super().__init__(*a, W=(ref == "W"), **kw)
        self.ref = ref

    def wb_ref(self, rho, p):
        psf_lo, psf_hi, pref, dsf, dref = super().wb_ref(rho, p)
        if self.ref in ("default", "W"):
            return psf_lo, psf_hi, pref, dsf, dref
        nc1 = rho.shape[-1]; il, iu = NG, nc1 - NG - 1
        r = rho / p
        if self.ref == "cubic":
            rs = smooth(r, il, iu, "cubic")
        elif self.ref == "lin":
            rs = smooth(r, il, iu, "edge")
            rs[..., il] = r[..., il]; rs[..., iu] = r[..., iu]
            rs[..., il + 1] = (r[..., il] + 2 * r[..., il + 1] + r[..., il + 2]) / 4
            rs[..., iu - 1] = (r[..., iu] + 2 * r[..., iu - 1] + r[..., iu - 2]) / 4
        rf = rs.copy(); rf[..., 1:] = 0.5 * (rs[..., :-1] + rs[..., 1:])
        return psf_lo, psf_hi, pref, psf_lo * rf, pref * rs


def face_density(d):
    """left/right rest face densities at faces il..iu+1 of one column"""
    U0 = d.base_state()
    W = d.prim(d.fill_ghosts(U0))
    psf_lo, psf_hi, pref, dsf, dref = d.wb_ref(W[IDN], W[IPR])
    Wp = W.copy(); Wp[IPR] = W[IPR] - pref; Wp[IDN] = W[IDN] - dref
    il, iu = NG, d.nz + NG - 1
    for c in (IPR, IDN):   # even-parity perturbation ghosts, hydro_forward.cpp:276-292
        Wp[c][:, il - NG:il] = Wp[c][:, il:il + NG][:, ::-1]
        Wp[c][:, iu + 1:iu + 1 + NG] = Wp[c][:, iu + 1 - NG:iu + 1][:, ::-1]
    wl, wr = d.recon(Wp, axis=2)
    fs = slice(il, iu + 2)
    return (wl[IDN] + dsf)[0, fs], (wr[IDN] + dsf)[0, fs], (d.recon(dref[None], axis=2), dsf)


def exact_rho(d, z):
    T = 1 - d.beta * z
    return T ** (1 / (d.beta) - 1)   # g = R = 1: p = T^(1/beta), rho = p/T


if __name__ == "__main__":
    refs = ("default", "cubic", "lin", "W")
    nzs = (16, 32, 64, 128)
    res = {}
    for ref in refs:
        for nz in nzs:
            d = WallCol(NH, eps, nz, ref=ref, nx=4)
            rl, rr, _ = face_density(d)
            ex = exact_rho(d, d.zf)
            el, er = (rl - ex) / ex, (rr - ex) / ex
            res[ref, nz] = (el, er)
    print(f"# NH {NH} eps {eps}: relative rest face-density error (rho_f - rho(z_f))/rho(z_f)")
    print("# faces counted from the bottom wall face (0) and the top wall face (T0); L/R = left/right state;")
    print("# 'interior' = max over faces 5..nz-5; order = log2(err(nz)/err(2nz))")
    for ref in refs:
        print(f"\n[{ref}]")
        print("  nz    " + "  ".join(f"{s:>10s}" for s in ("b1 R", "b2 R", "b2 L", "b3 L", "t1 L", "t2 L", "t2 R", "t3 R", "interior")))
        prev = None
        for nz in nzs:
            el, er = res[ref, nz]
            row = [er[1], er[2], el[2], el[3], el[-2], el[-3], er[-3], er[-4],
                   max(np.abs(el[5:-5]).max(), np.abs(er[5:-5]).max())]
            line = f"  {nz:4d}  " + "  ".join(f"{v:+.3e}" for v in row)
            if prev is not None:
                line += "   order " + " ".join(f"{np.log2(abs(a / b)):.2f}" for a, b in zip(prev, row))
            print(line); prev = row
