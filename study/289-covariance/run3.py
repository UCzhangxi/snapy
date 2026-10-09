import sys
from exact import deck_mu, growth as gex
from replica import Deck
eps=float(sys.argv[1]); nz=int(sys.argv[2])
mu=deck_mu(eps); s0=gex(eps,mu)
for kw in [dict(), dict(wall_pert="smooth"), dict(x1_mom=True), dict(wall_pert="smooth",x1_mom=True)]:
    r=[]
    for form in ("cell","face"):
        s=Deck(nz,eps,mu,form=form,dF=1.0,**kw).growth(); r.append(f"{form}+dF {s/s0-1:+.5f}")
    print(f"eps {eps:g} nz {nz} {kw}: "+"  ".join(r),flush=True)
