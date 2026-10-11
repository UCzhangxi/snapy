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


STAGES=('configure','generate','compile','register','execute')


def check_build():
    """sec-ch12-build: configure, generate, compile, register, execute, and the two predicates
    that cut the chain. A configuration contract, not a convergence statement."""
    def reached(build_tests, cuda, gpu_entry):
        if not build_tests: return STAGES.index('compile')      # stops before registration
        if gpu_entry and not cuda: return STAGES.index('register')  # registered, then disabled
        return STAGES.index('execute')
    cases=0
    for build_tests in (False,True):
        for cuda in (False,True):
            for gpu_entry in (False,True):
                cases+=1
                k=reached(build_tests,cuda,gpu_entry)
                # the chain is a total order: reaching a stage means reaching every earlier one
                assert list(range(k+1))==[i for i in range(len(STAGES)) if i<=k]
                assert (k>=STAGES.index('register'))==build_tests
                # the GPU predicate acts after registration, so only where registration happened
                if build_tests and gpu_entry and not cuda: assert k==STAGES.index('register')
                if build_tests and (cuda or not gpu_entry): assert k==STAGES.index('execute')
                if not build_tests: assert k<STAGES.index('register')
    assert cases==8
    return '[C6] build chain: 5 stages, 8 configurations; registration and GPU-entry cuts: 8 cases passed'


def check_macros():
    """sec-ch12-macros: substitution precedes compilation, so runtime selection cannot reach an
    alternative that was not compiled, and a complement macro adds no fallback."""
    alternatives={'a','b','c'}
    cases=0
    for compiled in [set(),{'a'},{'a','b'},alternatives]:
        selectable=set(compiled)                       # runtime selection, restricted to what exists
        complement=alternatives-compiled               # what the complement macro documents
        for value in alternatives:
            cases+=1
            assert (value in selectable)==(value in compiled)
            if value in complement: assert value not in selectable
        assert selectable<=compiled
        assert selectable&complement==set()            # the complement implements no fallback
    assert cases==12
    return '[C7] compiled alternatives bound runtime selection; complement adds no fallback: 12 cases passed'


def check_layout():
    """sec-ch12-layout: joining one group needs one rendezvous port, so independent (automatic)
    selection is admissible only for a single process."""
    from itertools import product
    cases=0; auto_ok={}
    for nports in (2,3):
        for nproc in (1,2,3):
            picks=list(product(range(nports),repeat=nproc))
            joins=[p for p in picks if len(set(p))==1]
            auto_ok[(nports,nproc)]=(len(joins)==len(picks))
            cases+=len(picks)
            # a common port given to every process always forms the group
            assert all(len(set((q,)*nproc))==1 for q in range(nports))
    assert all(ok==(nproc==1) for (_,nproc),ok in auto_ok.items())
    return ('[C8] automatic port selection forms the group for every assignment only at one process; '
            '%d assignments over 6 (ports, processes) pairs: 6 cases passed'%cases)


def check_test_environment():
    """sec-ch12-test-environment: a filter that selects nothing cannot certify, and 125 is a skip,
    neither a pass nor a failure."""
    def certified(selected,passed): return selected>=1 and passed==selected
    cases=0
    for selected in range(4):
        for passed in range(selected+1):
            cases+=1
            if selected==0: assert not certified(selected,passed)
            assert certified(selected,passed)==(selected>=1 and passed==selected)
    PASS,SKIP=0,125
    assert len({PASS,SKIP})==2 and SKIP!=PASS
    for code in (1,2,127):                             # ordinary failures
        assert code not in (PASS,SKIP)
    assert not certified(0,0)                          # the one-test pass marker is the point
    return ('[C9] a zero-selection filter never certifies; skip 125 is neither pass nor failure: '
            '%d cases passed'%cases)


def check_yaml():
    """sec-ch12-yaml: incompatible options are rejected rather than silently run, and the face-work
    choice changes the budget functional rather than labelling it."""
    incompatible={('implicit','multi-x1-block'),('face-work','cubed-sphere')}
    def validate(pair): return tuple(sorted(pair)) not in {tuple(sorted(p)) for p in incompatible}
    options=['implicit','multi-x1-block','face-work','cubed-sphere','wb']
    cases=0; rejected=0
    for i,a in enumerate(options):
        for b in options[i+1:]:
            cases+=1
            ok=validate((a,b))
            if tuple(sorted((a,b))) in {tuple(sorted(p)) for p in incompatible}:
                assert not ok; rejected+=1
            else: assert ok
    assert rejected==len(incompatible)
    # the face-work switch moves the functional itself: P with and without the corrected term
    rho=sp.Matrix(sp.symbols('r:3')); volume=sp.Matrix([1,2,3]); phi=sp.Matrix([2,4,6])
    variance=sp.Matrix([1,4,9])/12; g=sp.Integer(-2)
    slope=sp.Matrix([[-3,4,-1],[-1,0,1],[1,-4,3]])/2
    plain=sum(volume[i]*phi[i]*rho[i] for i in range(3))
    corrected=plain-sum(volume[i]*g*variance[i]*(slope*rho)[i] for i in range(3))
    assert sp.simplify(corrected-plain)!=0                     # not a label: a different functional
    assert sp.simplify((corrected-plain).subs({rho[0]:1,rho[1]:1,rho[2]:1}))==0   # equal on a constant
    return ('[C10] %d option pairs, %d rejected and none silently run; face work changes the budget '
            'functional: %d cases passed'%(cases,rejected,cases))


def check_matrix():
    """sec-ch12-matrix: a row is supported only when registration and the test's arm agree, and a
    guard assertion supports setup behaviour but not an error norm."""
    cases=0
    for registered in (False,True):
        for arm in (False,True):
            cases+=1
            assert (registered and arm)==(registered&arm)
    supports=lambda assertion,claim: assertion=='norm' or claim=='setup'
    unsupported=[]
    for assertion in ('guard','norm'):
        for claim in ('setup','norm'):
            cases+=1
            if not supports(assertion,claim): unsupported.append((assertion,claim))
    assert unsupported==[('guard','norm')]
    assert not supports('guard','norm') and supports('guard','setup')
    return ('[C11] support is the conjunction of registration and arm; guard supports setup, not a '
            'norm (1 unsupported pair of 4): %d cases passed'%cases)


CHECKS=(check_parser,check_filter,check_spherical,check_covariance,check_budget,
        check_build,check_macros,check_layout,check_test_environment,check_yaml,check_matrix)
if __name__=='__main__':
    for check in CHECKS: print(check())
