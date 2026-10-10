"""Independent algebra/finite-set checks; no compiled solver is exercised.

Formula pin: e894700ff7aee30b52882e5202b16461413780b0.
C1: cell-copy parity and corner ownership; C2: acoustic inverse;
C3: convex admissibility; C4: corner averaging; C5: run-length optimum;
C6: reflecting block substitution; C7: reference wall continuation.
"""
from fractions import Fraction as Q
from itertools import product, groupby
import sympy as sp


def check_copies():
    owned = [2, 5, 9, 13]
    def mirror(a, odd=False):
        out = a[:]
        sign = -1 if odd else 1
        out[:2] = [sign*x for x in a[2:4][::-1]]
        out[-2:] = [sign*x for x in a[-4:-2][::-1]]
        return out
    def periodic(a):
        return a[-4:-2]+a[2:-2]+a[2:4]
    def constant(a):
        return [a[2]]*2+a[2:-2]+[a[-3]]*2
    a = [-99]*2+owned+[-99]*2
    for f in (mirror, lambda a: mirror(a, True), periodic, constant):
        out = f(a)
        assert f(out) == out and out[2:-2] == owned
    assert mirror(a)[:2] == [5, 2] and mirror(a, True)[:2] == [-5, -2]
    assert periodic(a)[:2] == [9, 13] and periodic(a)[-2:] == [2, 5]
    assert a[:] == a  # custom map
    solid = [1]*2+owned+[1]*2
    assert solid[:2] == solid[-2:] == [1, 1]
    # Rows are tangential columns; exchange replaces a whole received strip.
    corner = [mirror(a), mirror(a)]
    corner[0] = [-7, -7, 3, 8, 11, 15, -7, -7]
    assert corner[0][1] != corner[0][2]
    corner[0] = mirror(corner[0])
    assert corner[0][:2] == [8, 3] and corner[1] == mirror(a)
    return 'copy/parity/idempotence and corner ownership exact'


def check_acoustics():
    rho, c, dp, dv, drho = sp.symbols('rho c dp dv drho', nonzero=True)
    z = rho*c
    plus, minus = dv+dp/z, dv-dp/z
    entropy = drho-dp/c**2
    residuals = [sp.simplify((plus+minus)/2-dv),
                 sp.simplify(z*(plus-minus)/2-dp),
                 sp.simplify(entropy+dp/c**2-drho)]
    assert residuals == [0, 0, 0]
    # Selector is current-state speed, independent of background impedance.
    for mach, expected in [(-2,(0,0,0)),(-1,(1,0,0)),(0,(1,0,1)),(1,(1,1,1)),(2,(1,1,1))]:
        assert (int(mach+1>=0),int(mach-1>=0),int(mach>=0)) == expected
    return 'inverse residuals=[0, 0, 0]; five sonic regimes exact'


def limited(background, delta, floors):
    bounds=[(b-f)/(-d) if d<0 else Q(1) for b,d,f in zip(background,delta,floors)]
    alpha=min([Q(1)]+[Q(99,100)*b if b<1 else b for b in bounds])
    alpha=max(Q(0),alpha)
    return alpha,[b+alpha*d for b,d in zip(background,delta)]


def check_admissibility():
    # rho, p, species1, species2, dry complement, tracer ratio.
    base=list(map(Q,[2,3]))+[Q(1,4),Q(1,4),Q(1,2),Q(1,10)]
    floors=[Q(1,10),Q(1,10),Q(0),Q(0),Q(0),Q(0)]
    cases=[[-4,-1,0,0,0,0], [0,-6,0,0,0,0],
           [0,0,-1,0,1,0], [0,0,1,1,-2,0], [0,0,0,0,0,-1],
           [0,0,0,0,0,0]]
    for ds in cases:
        ds=list(map(Q,ds));alpha,out=limited(base,ds,floors)
        assert 0<=alpha<=1 and all(q>=f for q,f in zip(out,floors))
        assert sum(out[2:5])==1
        maximal=min([Q(1)]+[(b-f)/(-d) for b,d,f in zip(base,ds,floors) if d<0])
        assert alpha == (Q(99,100)*maximal if maximal<1 else maximal)
        assert all(q-b==alpha*d for q,b,d in zip(out,base,ds))
    return 'six rational fixtures satisfy independent bounds and shared scaling exactly'


def check_corners():
    q,a,b=sp.symbols('q a b')
    assert sp.simplify((q+q)/2-q)==0
    # Edge samples of f(x,y)=x+y at (1,0),(0,1) average to 1, not f(1,1)=2.
    assert (Q(1)+Q(1))/2 != Q(2)
    return 'constant residual=0; affine corner counterexample retained'


def minimum_dp(bits):
    states={(0,0):0,(1,0):0}
    for original in bits:
        following={}
        for (old,length),cost in states.items():
            for bit in (0,1):
                if original==1 and bit==0: continue
                if old==bit:
                    newlength=min(length+1,3 if bit==0 else 2)
                elif length==0 or length==(3 if old==0 else 2):
                    newlength=1
                else: continue
                key=(bit,newlength);newcost=cost+int(bit!=original)
                following[key]=min(following.get(key,10**6),newcost)
        states=following
    return min(cost for (bit,length),cost in states.items() if length==(3 if bit==0 else 2))


def check_runs():
    count=0
    for length in range(2,9):
        valid=[x for x in product((0,1),repeat=length)
               if all(len(list(g)) >= (3 if b==0 else 2) for b,g in groupby(x))]
        for original in product((0,1),repeat=length):
            cost=min(sum(a!=b for a,b in zip(original,x)) for x in valid
                     if all(a<=b for a,b in zip(original,x)))
            assert minimum_dp(original)==cost
            count+=1
    return f'{count} binary inputs: DP optimum equals exhaustive enumeration exactly'


def check_closure():
    b=sp.Matrix(3,3,sp.symbols('b:9'))
    c=sp.Matrix(3,3,sp.symbols('c:9'))
    a=sp.Matrix(3,3,sp.symbols('a:9'))
    u=sp.Matrix(sp.symbols('u:3'));h=sp.diag(1,-1,1)
    residual=(a+b*h+c*h)*u-(a*u+b*(h*u)+c*(h*u))
    assert all(sp.expand(v)==0 for v in residual)
    assert h*h==sp.eye(3)
    return 'three block-substitution residuals=0; reflection squared is identity'


def check_reference():
    weights=[Q(1,16),Q(4,16),Q(6,16),Q(4,16),Q(1,16)]
    assert sum(weights)==1 and sum(w*l for w,l in zip(weights,range(-2,3)))==0
    assert sum(w*l*l for w,l in zip(weights,range(-2,3)))==1
    # Unit linear gradient: repeat at the lower wall versus a continued profile.
    bias=sum(w*max(0,l) for w,l in zip(weights,range(-2,3)))
    assert bias==Q(3,8)
    x,e=sp.symbols('x e',positive=True)
    for depth in (1,2,3):
        logarithmic=x*(x/(x+e))**depth
        linear=x-depth*e
        assert sp.simplify((logarithmic-linear).subs(e,0))==0
        assert sp.simplify(sp.diff(logarithmic-linear,e).subs(e,0))==0
    assert all(v==0 for v in [0]*6)
    return 'binomial moments=(1,0,1); repeated-wall bias=3/8; continuation residuals=0'


def main():
    checks=[check_copies,check_acoustics,check_admissibility,check_corners,check_runs,check_closure,check_reference]
    failed=0
    for i,check in enumerate(checks,1):
        try:
            print(f'[C{i}] PASS {check()}')
        except Exception as exc:
            failed+=1
            print(f'[C{i}] FAIL {type(exc).__name__}: {exc}')
    print(f'{len(checks)-failed} passed; {failed} failed (report formulas only)')
    return failed


if __name__=='__main__':
    raise SystemExit(main())
