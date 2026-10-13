"""Chapter 14 derivation checks: the algebra behind the why-steps of the chapter 14 sections.

Ports of the code at the book pin chengcli/snapy 6fbb39750f62b83df096058a4746e77d0a634bc5 (sympy, numpy, fractions).
Each line prints [Cn] PASS or FAIL and the claim. Run: python3 src/snapy_report/ch14/derivation_check.py
"""
import sympy as sp
_n=[0]
def ok(name,cond):
    _n[0]+=1
    print("[C%d] %s %s"%(_n[0],"PASS" if cond else "FAIL",name.split(" ",1)[1]))
    _res.append(bool(cond))
_res=[]

# C14-2: rank = proc*b + loc (layout.hpp:83-93 at the pin), with b<1 acting as 1
def rt(b,P):
    bb=max(1,b); seen=set(); good=True
    for proc in range(P):
        for loc in range(bb):
            r=proc*bb+loc; good &= (r//bb==proc and r%bb==loc); seen.add(r)
    return good and seen==set(range(P*bb))
ok("C14-2 rank round trip and coverage, b=0..16, n_proc=1..8", all(rt(b,P) for b in range(0,17) for P in range(1,9)))

# C14-3/C14-4: tag algebra of make_comm_tag (layout.hpp:163-170)
base={}
dup=False
for phy in range(64):
    for loc in range(32):
        for buf in range(27):
            t=1024*phy+32*loc+buf
            dup |= t in base; base[t]=(phy,loc,buf)
ok("C14-3 tag0 = 1024 phy + 32 loc + buf is one to one: 64*32*27 = 55296 distinct", not dup and len(base)==55296)
ok("C14-3 tag0 < 65536 for phy<64, loc<32, buf<27", max(base)<65536)
ok("C14-3 loc=32 gives the tag of loc=0 at phy+1", all(1024*p+32*32+b==1024*(p+1)+b for p in range(63) for b in range(27)))
ok("C14-3 n <= 32767 keeps tag = tag0 + 65536 n below 2^31", 65535+65536*32767 < 2**31 and 65536*32768==2**31)
ok("C14-3 tag < 2^24 for every tag0 iff n <= 255 (256 variables)", 65535+65536*255 < 2**24 and 0+65536*256 >= 2**24)
k=sp.symbols('k',integer=True)
relay=[0x7715,0x7717,0x7718,0x7720,0x7721,0x7722,0x7724,0x7726,0x7730,0x7732,0x7734,0x7736,0x7740,0x7742,0x7744,0x7746]
base16={1024*p+32*l+b for p in range(64) for l in range(16) for b in range(27)}
ok("C14-4 none of the 16 relay tags at the pin is a base tag with loc < 16", not any(t in base16 for t in relay))
ok("C14-4 folded with 65536*f, f < 256 (b <= 16), relay tags keep their low 16 bits and stay below 2^24",
   all((t+65536*f)%65536==t and t+65536*f<2**24 for t in relay for f in range(256)))
ok("C14-4 the 15 b<=16 fold factors f = loc_send*b + loc_recv are < 256", max(ls*b+lr for b in range(1,17) for ls in range(b) for lr in range(b))<256)

# C14-8: weighted Welford induction step (output_type.cpp:282-294)
W1,wi,qi,mb,M2=sp.symbols('W_prev w_i q_i qbar_prev M2_prev',positive=True)
Wi=W1+wi
qbar=mb+wi/Wi*(qi-mb)
ok("C14-8 qbar_i = (W_prev qbar_prev + w_i q_i)/W_i", sp.simplify(qbar-(W1*mb+wi*qi)/Wi)==0)
# sum_{j<i} w_j (q_j - qbar_i)^2 = M2_prev + W_prev (qbar_prev - qbar_i)^2 (parallel-axis); add w_i (q_i - qbar_i)^2
lhs=M2+W1*(mb-qbar)**2+wi*(qi-qbar)**2
rhs=M2+wi*(qi-mb)*(qi-qbar)
ok("C14-8 M2_i from the definition equals the code's update M2_prev + w_i (q_i - qbar_prev)(q_i - qbar_i)", sp.simplify(lhs-rhs)==0)
# parallel-axis identity checked on three explicit points
w=sp.symbols('w1:4',positive=True); q=sp.symbols('q1:4'); c=sp.symbols('c')
Wt=sum(w); m=sum(w[j]*q[j] for j in range(3))/Wt
ok("C14-8 parallel-axis: sum w_j (q_j - c)^2 = sum w_j (q_j - m)^2 + W (m - c)^2",
   sp.simplify(sum(w[j]*(q[j]-c)**2 for j in range(3))-(sum(w[j]*(q[j]-m)**2 for j in range(3))+Wt*(m-c)**2))==0)
# three-step numeric run of the recurrence against two-pass formulas
import random
random.seed(1); ws=[random.random() for _ in range(50)]; qs=[random.random() for _ in range(50)]
mean=0.0; m2=0.0; tot=0.0
for wj,qj in zip(ws,qs):
    d=qj-mean; tot+=wj; mean+=d*wj/tot; m2+=wj*d*(qj-mean)
Wsum=sum(ws); mu=sum(a*b for a,b in zip(ws,qs))/Wsum; var=sum(a*(b-mu)**2 for a,b in zip(ws,qs))
ok("C14-8 recurrence equals two-pass weighted mean and M2 (50 random steps, 1e-12)", abs(mean-mu)<1e-12 and abs(m2-var)<1e-12)

# C14-5: MIN/MAX are order independent and exact; SUM error bound for any summation order/tree
import itertools, numpy as np
rng=np.random.default_rng(7)
vals=list(rng.standard_normal(6)*10.0**rng.integers(-8,8,6))
mins={min(p) for p in itertools.permutations(vals)}; maxs={max(p) for p in itertools.permutations(vals)}
ok("C14-5 MIN and MAX of 6 doubles: one result over all 720 orders, equal to an input", len(mins)==1 and len(maxs)==1 and mins.pop() in vals)
def tree_sum(xs,rng):
    xs=[np.float64(x) for x in xs]
    while len(xs)>1:
        i,j=sorted(rng.choice(len(xs),2,replace=False)); a=xs.pop(j); b=xs.pop(i); xs.append(a+b)
    return xs[0]
eps=2.0**-53; worst=0.0
from fractions import Fraction
for trial in range(300):
    n=int(rng.integers(2,40)); xs=list(rng.standard_normal(n)*10.0**rng.integers(-6,6,n))
    exact=float(sum(Fraction(x) for x in xs)); s=tree_sum(xs,rng)
    bound=(n-1)*eps*sum(abs(x) for x in xs)
    worst=max(worst,abs(s-exact)/bound)
ok("C14-5/C14-11 any-order sum of n doubles is within (n-1) eps sum|x| of the exact sum (300 random trees)", worst<=1.0)
# C14-11: propagation through efix = -D/M times rho: relative error of a quotient
d,m,ed,em=sp.symbols('D M e_D e_M')
f=(d*(1+ed))/(m*(1+em))/(d/m)-1
z={ed:0,em:0}
ok("C14-11 (D(1+e_D))/(M(1+e_M)) = (D/M)(1 + e_D - e_M + O(e^2))",
   sp.simplify(f.subs(z))==0 and sp.simplify(sp.diff(f,ed).subs(z))==1 and sp.simplify(sp.diff(f,em).subs(z))==-1)

# C14-7: float32 rounding of a double in the normal range: |fl32(x)-x| <= 2^-24 |x|
x=rng.uniform(-1,1,200000)*10.0**rng.uniform(-37,38,200000)
x=x[np.abs(x)>=np.finfo(np.float32).tiny]
rel=np.abs(x.astype(np.float32).astype(np.float64)-x)/np.abs(x)
ok("C14-7 static_cast<float>: relative error <= 2^-24 on 2e5 normal-range doubles (max %.3e)"%rel.max(), rel.max()<=2.0**-24)
with np.errstate(over="ignore"): big=np.float32(np.float64(3.5e38))
ok("C14-7 values above FLT_MAX become inf", np.isinf(big))
ts=rng.uniform(1,1e6,20000); ts=ts.astype(np.float32).astype(np.float64)   # times that are float32-exact, as a written time is
lost=all(np.float32(t)==np.float32(t+0.999*2.0**-25*t) for t in ts)
shown=all(np.float32(t)!=np.float32(t+1.001*2.0**-23*t) for t in ts)
ok("C14-7 float32 time: a step below 2^-25 t vanishes, one above 2^-23 t shows (2e4 float32-exact times)", lost and shown)

# C14-9: restart next-time rule (meshblock.cpp:1436-1450 at the pin)
def resume(saved,tr,dt,matched=True):
    if matched: return tr+dt if (dt>0 and saved>tr+dt) else saved
    return tr-np.fmod(tr,dt) if dt>0 else tr
ok("C14-9 shrunk interval: saved 1000, t_r 100, dt 10 -> 110", resume(1000.,100.,10.)==110.)
ok("C14-9 far-future (disabled) output -> t_r + dt", resume(1e30,100.,10.)==110.)
ok("C14-9 within one interval keeps the saved time", resume(105.,100.,10.)==105.)
ok("C14-9 dt <= 0 keeps the saved time", resume(1e30,100.,0.)==1e30)
ok("C14-9 new output joins the grid at or below t_r: t_r 107, dt 10 -> 100", resume(None,107.,10.,False)==100.)

print("%d passed, %d failed"%(sum(_res),len(_res)-sum(_res)))
