import sys
from exact import deck_mu, growth as gex
from replica import Deck
eps=float(sys.argv[1]); nz=int(sys.argv[2])
mu=deck_mu(eps); s0=gex(eps,mu)
for kw in [dict(curv_wall=True), dict(curv_wall=True,x1_mom=True), dict(x1_mom=True)]:
    r=[]
    for form in ("cell","face"):
        for dF in (0.,1.):
            if form=="cell" and kw.get("curv_wall"): continue
            s=Deck(nz,eps,mu,form=form,dF=dF,**kw).growth(); r.append(f"{form}{'+dF' if dF else ''} {s/s0-1:+.5f}")
    print(f"eps {eps:g} nz {nz} {kw}: "+"  ".join(r),flush=True)
