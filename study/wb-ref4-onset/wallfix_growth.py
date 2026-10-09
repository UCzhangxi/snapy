"""Onset growth-rate error of the linear column with the wall fix; and with W
on, the V term switched (x1 momentum reconstructed as rho w instead of w)."""
import sys
from wallfix import WallCol
from wbonset import continuous
NH, eps = float(sys.argv[1]), float(sys.argv[2])
nzs = [int(a) for a in sys.argv[3].split(",")]
cases = (("cov default", dict(ref="default")), ("cov cubic", dict(ref="cubic")),
         ("cov cubic+D", dict(ref="cubic", D=True)), ("cov W+D", dict(ref="W", D=True)),
         ("cov W+D rho-w recon", dict(ref="W", D=True, x1_mom=True)),
         ("cov cubic+D rho-w recon", dict(ref="cubic", D=True, x1_mom=True)))
for nz in nzs:
    out = []
    for name, kw in cases:
        d = WallCol(NH, eps, nz, nx=2 * nz, **kw)
        s0 = continuous(NH, eps, d.k)
        out.append(f"{name} {d.growth()/s0-1:+.3e}")
    print(f"NH {NH} eps {eps} nz {nz}: " + "  ".join(out), flush=True)
