import sys, numpy as np
Dp, nz = sys.argv[1], sys.argv[2]
sys.argv=["offset.py",Dp,nz]
src=open("offset.py").read(); src=src[:src.index("off = rho_f")]
exec(src)
for lab,flags in (("code",{}),("FIX dsf=R(dref)",dict(dsf_recon=True)),("C",dict(dsf_recon=True,rs_wall_exact=True,dref_ghost_smooth=True))):
    dd=make("face",0.0)
    for k,v in flags.items(): setattr(dd,k,v)
    rf2,_,res=face_density(dd)
    e=(rf2-rf_(zf))/rf_(zf)/dd.dz**2
    print(f"Dp {Dp} nz {nz} {lab:16s}: rest {res:.1e}  faces 1..3 bottom {e[1]:+.3f} {e[2]:+.3f} {e[3]:+.3f}  top {e[-2]:+.3f} {e[-3]:+.3f} {e[-4]:+.3f}  interior max {np.abs(e[4:-4]).max():.1e}")
