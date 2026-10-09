import numpy as np
from tracer import sigma
from exact import deck_mu
mu = deck_mu(1e-3)
for name, eps, delta, qb in (("earth water, eps 1e-3", 1e-3, 1/0.622-1, 0.02),
                             ("heavy vapour (jupiter water) q 0.01, eps_T 0.01", 0.01, 2.3/18-1, 0.01),
                             ("heavy vapour q 0.01, eps_T 0.0095", 0.0095, 2.3/18-1, 0.01)):
    s0 = sigma(eps, mu, delta, qb)
    out=[]
    for nz in (16, 32, 64):
        dz=1/nz
        s1 = sigma(eps, mu, delta, qb, dz=dz)
        out.append(f"nz {nz}: {s1/s0-1:+.5f}")
    print(f"{name}: sigma0 {s0:.6f}  covariance-term rel err  " + "  ".join(out))
