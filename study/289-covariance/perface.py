import sys, numpy as np
sys.argv=["offset.py","1","64"]
src=open("offset.py").read()
src=src[:src.index("out = {}")]
exec(src)
base=tendency(mk("face",1.0,None,curv_wall=True))
print("faceWC+dF base", f"{base:+.5f}")
n=len(off)
for faces in ([1],[2],[3],[n-2],[n-3],[n-4],[1,2,3,n-2,n-3,n-4]):
    o=np.zeros_like(off); o[faces]=off[faces]
    print("remove offset at faces",faces, f"{tendency(mk('face',1.0,o,curv_wall=True)):+.5f}")
print("offsets/dz^2 at faces 0..4:", np.round(off[:5]/rf_(zf[:5])/d.dz**2,4), " top:", np.round(off[-5:]/rf_(zf[-5:])/d.dz**2,4))
