import sys, time
import numpy as np
from wbonset import Column, continuous
NH = float(sys.argv[1]); eps = float(sys.argv[2]); nzs = [int(a) for a in sys.argv[3].split(",")]
cases = sys.argv[4].split(",") if len(sys.argv) > 4 else ["cov", "covW", "covWD"]
weno = sys.argv[5] if len(sys.argv) > 5 else "linear"
ghostT = sys.argv[6] if len(sys.argv) > 6 else "fixed"
opts = {"cov": {}, "covW": dict(W=True), "covWD": dict(W=True, D=True), "covD": dict(D=True),
        "base": dict(cov=False), "WD": dict(cov=False, W=True, D=True)}
t0 = time.time()
for nz in nzs:
    c = Column(NH, eps, nz, nx=2 * nz)
    s0 = continuous(NH, eps, c.k)
    out = []
    for name in cases:
        kw = dict(opts.get(name, {}))
        if name.startswith("fix:"):
            kw = dict(W=True, D=True, fix=name[4:])
        d = Column(NH, eps, nz, nx=2 * nz, weno=weno, **kw); d.ghostT = ghostT
        s = d.growth()
        out.append(f"{name} {s/s0-1:+.3e}")
    print(f"[{weno},{ghostT}] NH {NH} eps {eps} nz {nz} sigma_c {s0:.6e}: " + "  ".join(out) + f"  ({time.time()-t0:.0f}s)", flush=True)
