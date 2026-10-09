import sys
from exact import deck_mu, growth as gex
from replica import Deck
eps=1e-3; nz=int(sys.argv[1]); mu=deck_mu(eps); s0=gex(eps,mu)
for name,kw in (("cons",{}),("cons dF_wall0",dict(dF_wall=False)),("cons wall_pert odd",dict(wall_pert="odd"))):
    s=Deck(nz,eps,mu,form="face",curv_wall=True,dF=1.0,**kw).growth(); print(f"nz {nz} {name}: {s/s0-1:+.6f}",flush=True)
