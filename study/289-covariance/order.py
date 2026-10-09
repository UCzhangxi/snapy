import sys
from exact import deck_mu, growth as gex
from replica import Deck
eps=float(sys.argv[1]); nz=int(sys.argv[2])
mu=deck_mu(eps); s0=gex(eps,mu)
r=[]
for name,kw in (("cell+dF",dict(form="cell")),("cell+dF+mom",dict(form="cell",x1_mom=True)),
                ("faceWallCons+dF",dict(form="face",curv_wall=True)),("face+dF",dict(form="face"))):
    s=Deck(nz,eps,mu,dF=1.0,**kw).growth(); r.append(f"{name} {s/s0-1:+.6f}")
print(f"eps {eps:g} nz {nz}: "+"  ".join(r),flush=True)
