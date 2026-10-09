import numpy as np
from replica import Deck, IDN, IVX, IVY, IPR, NG, GAMMA, R
from numpy.polynomial.legendre import leggauss
eps=1e-3
xg,wg=leggauss(8)
for nz in (16,32,64,128):
    d=Deck(nz,eps,1e-4,form="face"); d.nx=8; d.xc=(np.arange(8)+.5)*d.Lx/8; d.dx=d.Lx/8
    b=d.beta
    rho_s=lambda z:(1-b*z)**(1/b)/(1-b*z)
    zq=(d.zc[:,None]+0.5*d.dz*xg[None,:])
    avg=lambda f:(f(zq)*wg).sum(1)/2
    U0=d.base_state()
    rho_bal=U0[IDN,0]
    amp=1e-7
    wfun=lambda z:np.sin(np.pi*z)
    m=amp*avg(lambda z:rho_s(z)*wfun(z))
    def F_of(sgn):
        U=U0.copy(); U[IVX]+=sgn*m[None,:]
        V=d.fill_ghosts(U); W=d.prim(V)
        psf_lo,psf_hi,pref,dsf,dref=d.wb_ref(W[IDN],W[IPR])
        Wp=W.copy(); Wp[IPR]=W[IPR]-pref; Wp[IDN]=W[IDN]-dref
        il,iu=NG,nz+NG-1
        for c in (IPR,IDN):
            Wp[c][:,il-NG:il]=Wp[c][:,il:il+NG][:,::-1]; Wp[c][:,iu+1:iu+1+NG]=Wp[c][:,iu+1-NG:iu+1][:,::-1]
        wl,wr=d.recon(Wp,axis=2); wl[IPR]+=psf_lo; wr[IPR]+=psf_lo; wl[IDN]+=dsf; wr[IDN]+=dsf
        F=d.lmars(wl[:,NG:-NG,il:iu+2],wr[:,NG:-NG,il:iu+2],IVX)
        rhof=0.5*(wl[IDN]+wr[IDN])[0,il:iu+2]
        return F[IDN][0],rhof
    Fp,rf=F_of(1); Fm,_=F_of(-1); F=(Fp-Fm)/2/amp
    ex=rho_s(d.zf)*wfun(d.zf)
    e=F-ex
    covm=d.dz**2/12*np.gradient(rho_s(d.zf),d.zf)*np.pi*np.cos(np.pi*d.zf)
    i=nz//2
    print(f"nz {nz}: e/dz^2 mid {e[i]/d.dz**2:+.4f} (dFm model {covm[i]/d.dz**2:+.4f}); "
          f"e/dz^2 at z=0.25 {e[nz//4]/d.dz**2:+.4f} (model {covm[nz//4]/d.dz**2:+.4f}); "
          f"rho_f rel err mid /dz^2 {(rf[i]/rho_s(d.zf[i])-1)/d.dz**2:+.4f}; bal rho rel diff/dz^2 mid {(rho_bal[i]/avg(rho_s)[i]-1)/d.dz**2:+.4f}")
