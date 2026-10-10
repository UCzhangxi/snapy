"""Independent exact identities and configuration contracts; no snapy runtime."""
from fractions import Fraction as Q
import sympy as sp


def check_parser():
    def parse(value, radial=False):
        value = ('1' if radial else '0') if value is None else value.lower()
        return value not in ({'0', 'false', 'off', 'no'} if radial else {'', '0', 'false', 'off', 'no'})
    values = [None, '', '0', 'FALSE', 'Off', 'nO', '1', 'yes', 'false ']
    assert [parse(v) for v in values] == [False]*6 + [True]*3
    assert [parse(v, True) for v in values] == [True, True] + [False]*4 + [True]*3
    # XC implies WB, but a ghost-depth requirement needs nonzero gravity too.
    for wb in (False, True):
        for xc in (False, True):
            for gravity in (False, True):
                need = (wb or xc) and gravity
                assert need == (gravity and any((wb, xc)))
    return '[C1] parser truth table: 18 cases; implication: 8 cases passed'


def check_filter():
    weights = list(map(Q, [-1, 4, 10, 4, -1]))
    weights = [w/16 for w in weights]
    moments = [sum(w*Q(l)**n for w,l in zip(weights, range(-2,3))) for n in range(5)]
    assert moments == [1,0,0,0,Q(-3,2)]
    for x, weights in [(-1,[4,-6,4,-1]),(-2,[10,-20,15,-4])]:
        assert all(sum(Q(w)*Q(j)**n for j,w in enumerate(weights)) == Q(x)**n for n in range(4))
    r=sp.symbols('r')
    for n in range(4):
        means=[sp.integrate(r**n,(r,j,j+1)) for j in range(-2,2)]
        got=sum(w*q/12 for w,q in zip([-1,7,7,-1],means))
        assert sp.simplify(got-(1 if n==0 else 0))==0
    return '[C2] filter, cubic wall continuation and face moments: exact residual 0'


def check_spherical():
    r=sp.symbols('r')
    edges=list(map(sp.Integer,range(3,9)))
    means=sp.Matrix([[sp.integrate(r**(n+2),(r,a,b))/sp.integrate(r**2,(r,a,b))
                      for a,b in zip(edges[:-1],edges[1:])] for n in range(5)])
    target=sp.Matrix([sp.integrate(r**n,(r,5,6)) for n in range(5)])
    weights=means.inv()*target
    assert means*weights-target==sp.zeros(5,1)
    assert sum(weights)==1
    for n in range(6):
        p=r**n
        pressure_force=-sp.integrate(r*r*sp.diff(p,r),(r,5,6))
        flux=-(36*p.subs(r,6)-25*p.subs(r,5))
        source=2*sp.integrate(r*p,(r,5,6))
        assert sp.simplify(pressure_force-flux-source)==0
    return '[C3] five spherical moments and six pressure identities: exact residual 0'


def check_covariance():
    x,h,a0,a1,b0,b1=sp.symbols('x h a0 a1 b0 b1', nonzero=True)
    mean=lambda f:sp.integrate(f,(x,-h/2,h/2))/h
    a=a0+a1*x; b=b0+b1*x
    assert sp.simplify(mean(a*b)-mean(a)*mean(b)-h*h*a1*b1/12)==0
    assert sp.simplify(mean(a*b)/mean(a)-h*h*a1*b1/(12*mean(a))-mean(b))==0
    # Shared face correction has equal and opposite integrated increments.
    left,right,flux=sp.symbols('left right flux', nonzero=True)
    assert sp.simplify(left*(-flux/left)+right*(flux/right))==0
    return '[C4] covariance, mass-weighted mean and shared-face cancellation: exact residual 0'


def check_budget():
    # A nonuniform three-point slope is a fixed linear map. This oracle only
    # needs that linearity; it does not copy the implementation's slope code.
    slope=sp.Matrix([[-3,4,-1],[-1,0,1],[1,-4,3]])/2
    rho=sp.Matrix(sp.symbols('rho:3')); change=sp.Matrix(sp.symbols('change:3'))
    volume=sp.Matrix([1,2,3]); phi=sp.Matrix([2,4,6]); variance=sp.Matrix([1,4,9])/12
    g=sp.Integer(-2)
    def potential(q):
        return sum(volume[i]*(phi[i]*q[i]-g*variance[i]*(slope*q)[i]) for i in range(3))
    energy=sum(volume[i]*(-phi[i]*change[i]+g*variance[i]*(slope*change)[i]) for i in range(3))
    assert sp.simplify(energy+potential(rho+change)-potential(rho))==0
    return '[C5] corrected potential-energy increment: exact residual 0'


CHECKS=(check_parser,check_filter,check_spherical,check_covariance,check_budget)
if __name__=='__main__':
    for check in CHECKS: print(check())
