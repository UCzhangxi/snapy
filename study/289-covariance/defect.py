import numpy as np, sys
from exact import deck_mu
from replica import Deck, IDN, IVX, IVY, IPR, NG
eps=1e-3
for nz in (32,64):
    mu=deck_mu(eps)
    d=Deck(nz,eps,mu,form="face",dF=1.0)
    lam,v=d.growth(return_vec=True)
    U0=d.base_state(); nzz=d.nz
    # build real perturbation from eigvec: var blocks IDN,IVX,IVY,IPR ; cos part
    dU=np.zeros_like(U0); amp=1e-7
    ph=np.exp(1j*d.k*d.xc)[:,None]
    for b,vb in enumerate([IDN,IVX,IVY,IPR]):
        dU[vb]=np.real(v[b*nzz:(b+1)*nzz][None,:]*ph)
    # normalise by max |rho w|
    s=amp/np.abs(dU[IVX]).max(); dU*=s
    def mflux(U):
        V=d.fill_ghosts(U); W=d.prim(V)
        psf_lo,psf_hi,pref,dsf,dref=d.wb_ref(W[IDN],W[IPR])
        Wp=W.copy(); Wp[IPR]=W[IPR]-pref; Wp[IDN]=W[IDN]-dref
        il,iu=NG,nzz+NG-1
        for c in (IPR,IDN):
            Wp[c][:,il-NG:il]=Wp[c][:,il:il+NG][:,::-1]; Wp[c][:,iu+1:iu+1+NG]=Wp[c][:,iu+1-NG:iu+1][:,::-1]
        wl,wr=d.recon(Wp,axis=2); wl[IPR]+=psf_lo; wr[IPR]+=psf_lo; wl[IDN]+=dsf; wr[IDN]+=dsf
        F=d.lmars(wl[:,NG:-NG,il:iu+2],wr[:,NG:-NG,il:iu+2],IVX)
        return F[IDN], W
    Fp,Wp_=mflux(U0+dU); Fm,Wm=mflux(U0-dU)
    F=(Fp-Fm)/2
    m=(U0+dU)[IVX]-U0[IVX]   # cell rho w
    mg=np.concatenate([-m[:,:1],m,-m[:,-1:]],1)  # odd ghosts
    curv=d.dz/12*(mg[:,1:]-mg[:,:-1]); curv[:,0]=0; curv[:,-1]=0
    D=0.5*(F[:,1:]+F[:,:-1])-(curv[:,1:]-curv[:,:-1]) - m
    j=0
    print(f"nz {nz}: max|m| {np.abs(m[j]).max():.3e}")
    print("  D/max|m| first 6:", np.round(D[j,:6]/np.abs(m[j]).max(),8))
    print("  D/max|m| mid 3  :", np.round(D[j,nzz//2-1:nzz//2+2]/np.abs(m[j]).max(),8))
    print("  D/max|m| last 6 :", np.round(D[j,-6:]/np.abs(m[j]).max(),8))
