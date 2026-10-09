import numpy as np, time, sys
from exact import deck_mu, growth as gex
from replica import Deck
cases=[(1e-3,16),(1e-3,32),(1e-3,64),(2.56e-4,64),(0.02,16),(0.02,32),(0.02,64)]
if len(sys.argv)>1: cases=[(float(sys.argv[1]),int(sys.argv[2]))]
for eps,nz in cases:
    mu=deck_mu(eps); s0=gex(eps,mu)
    out=[]
    for form in ("cell","face"):
        for dF in (0.0,1.0):
            d=Deck(nz,eps,mu,form=form,dF=dF); s=d.growth()
            out.append(f"{form}{'+dF' if dF else ''} {s/s0-1:+.5f}")
    print(f"eps {eps:g} nz {nz}: "+"  ".join(out),flush=True)
