import sys
from exact import deck_mu, growth as gex
from replica import Deck
eps=1e-3; nz=int(sys.argv[1]); mu=deck_mu(eps); s0=gex(eps,mu)
for form,kw in (("cons",dict(form="face",curv_wall=True)),("cell",dict(form="cell"))):
    s=Deck(nz,eps,mu,dF=1.0,dF_order=4,**kw).growth(); print(f"nz {nz} {form} dF 4th-order derivs: {s/s0-1:+.6f}",flush=True)
