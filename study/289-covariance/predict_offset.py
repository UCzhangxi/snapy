import numpy as np
cp=3.5; beta=1/cp; g=1.0
meas={(1,128):-0.00731,(2,128):-0.00982,(3,128):-0.01343,(5,128):-0.02174,
      (1,64):-0.01380,(2,64):-0.01666,(3,64):-0.02079,(5,64):-0.03027}
base={(1,128):-0.24685,(2,128):-0.27228,(3,128):-0.30907,(5,128):-0.39366}
print("Dp  nz  wall-layer  interior   total    | replica offset contribution | total/base")
for Dp in (1,2,3,5):
    L=(1-np.exp(-beta*Dp))/beta
    for nz in (64,128,256,512):
        dz=L/nz; zc=(np.arange(nz)+.5)*dz; zf=np.arange(nz+1)*dz
        T=lambda z:1-beta*z; p=lambda z:T(z)**(1/beta); rho=lambda z:p(z)/T(z)
        w=lambda z:np.sin(np.pi*z/L)
        lnf_z=lambda z: beta/T(z)
        f1=lambda z: beta/T(z)**2; f2=lambda z: 2*beta**2/T(z)**3; p1=lambda z:-rho(z)
        off_int=dz**2*(p(zf)*f2(zf)/6+p1(zf)*f1(zf)/12)
        off_wall=np.zeros(nz+1)
        for j,c in zip((1,2,3),(-1/480,7/192,1/480)):
            off_wall[j]+=c*dz*lnf_z(zf[j])*rho(zf[j])
            off_wall[nz-j]+=-c*dz*lnf_z(zf[nz-j])*rho(zf[nz-j])
        def proj(off):
            num=0.0
            for k in range(1,nz):
                dF=off[k]*w(zf[k])
                num+=dF*(T(zc[k-1])*w(zc[k-1])-T(zc[k])*w(zc[k]))
                for c in (k-1,k):   # face-form gravity work sees dF
                    num+=w(zc[c])*(-g*dF/2)/cp*dz
            return num/((rho(zc)*w(zc)**2).sum()*dz)*nz**2
        a,b=proj(off_wall),proj(off_int)
        m=meas.get((Dp,nz)); bb=base.get((Dp,nz))
        print(f"{Dp}  {nz:3d}  {a:+.5f}  {b:+.5f}  {a+b:+.5f}  | {m if m is None else f'{m:+.5f}'} | {'' if bb is None else f'{(a+b)/bb:.3f}'}")
