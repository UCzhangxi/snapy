"""Symbolic (sympy) checks for study/289-allrows/derivation.md.

S1  exact radial moments: r_c, r_v, delta = r_v - r_c, sigma_c^2, sigma_v^2.
S2  the generic row identity, to O(h^4):
        <rho u phi>_A - rhobar * (mbar/rhobar) * (sbar/rhobar)
      = sigma^2 rho u' phi' - delta (rho u phi)'          (s = rho phi)
    and the pressure piece  <p>_A - pbar_V = -delta p'.
    Every bar is a VOLUME average (weight r^2), <.>_A is the FACE average
    (weight r).  Fields are generic quartic Taylor polynomials about rbar.
S3  the exact spherical-polar theta-momentum pressure source,
        int_V p cot(theta)/r dV  =  <p>_A * (A2(theta+) - A2(theta-)),
    for p = p(r) arbitrary (checked for a generic quartic), i.e. the source
    is weighted by the FACE measure r dr, not by the cell measure r^2 dr.
S4  the same for the gnomonic panel, using the unit-normalised covariant
    momentum equation: int_V (p/r) d_alpha ln sqrt(g) dV = int p r dr * (...)
    with sqrt(g) = r^2 s(alpha,beta).
CPU: about 1.5 min (S2b/S2c dominate).
"""
import sympy as sp

rb, h, x = sp.symbols('rbar h x', positive=True)
r = rb + x


def avg(expr, w):
    """Average of expr(x) over x in [-h/2, h/2] with weight w(x)."""
    num = sp.integrate(sp.expand(expr * w), (x, -h / 2, h / 2))
    den = sp.integrate(sp.expand(w), (x, -h / 2, h / 2))
    return num / den


def series_h(e, n=4):
    return sp.series(sp.simplify(e), h, 0, n).removeO()


# ---------------- S1 ----------------
rc = sp.simplify(avg(r, r))
rv = sp.simplify(avg(r, r**2))
delta = sp.simplify(rv - rc)
s2c = sp.simplify(avg((r - rc)**2, r))
s2v = sp.simplify(avg((r - rv)**2, r**2))
print('S1 r_c      =', sp.factor(rc))
print('S1 r_v      =', sp.factor(rv))
print('S1 delta    =', sp.factor(delta))
print('S1 delta - h^2(12rb^2-h^2)/(12rb(12rb^2+h^2)) =',
      sp.simplify(delta - h**2 * (12 * rb**2 - h**2) / (12 * rb * (12 * rb**2 + h**2))))
print('S1 sigma_c^2 =', sp.factor(s2c), '  (h^2/12)(1-h^2/(12rb^2)) diff:',
      sp.simplify(s2c - h**2 / 12 * (1 - h**2 / (12 * rb**2))))
print('S1 sigma_c^2 - sigma_v^2 series:', sp.series(s2c - s2v, h, 0, 6))

# ---------------- S2 ----------------
N = 4  # quartic Taylor polynomials about rbar


def field(name):
    c = sp.symbols(f'{name}0:{N + 1}')
    return sum(c[k] * x**k / sp.factorial(k) for k in range(N + 1)), c


rho, cr = field('R')
u, cu = field('U')
phi, cf = field('F')
p, cp = field('P')
# keep rho > 0 symbolic: R0 is the value at rbar
wA, wV = r, r**2

# derivatives evaluated where?  The correction is O(h^2) and is evaluated from
# cell data; any O(h^2) shift of the evaluation point is O(h^4).  Use rbar.
d = lambda f: sp.diff(f, x).subs(x, 0)
at0 = lambda f: f.subs(x, 0)

s2 = h**2 / 12            # sigma^2 to the order kept
dl = h**2 / (12 * rb)     # delta to the order kept

# (a) mass: <rho u>_A - mbar_V
lhs = avg(rho * u, wA) - avg(rho * u, wV)
rhs = -dl * d(rho * u)
print('S2a mass      residual O(h^4)? ->', sp.simplify(series_h(lhs - rhs, 4)) == 0)

# (b) generic row rho u phi (tracer phi=q, transverse momentum phi=u_t,
#     normal momentum phi=u_n=u)
mbar, rbar_, sbar = avg(rho * u, wV), avg(rho, wV), avg(rho * phi, wV)
code = rbar_ * (mbar / rbar_) * (sbar / rbar_)
lhs = avg(rho * u * phi, wA) - code
rhs = s2 * at0(rho) * d(u) * d(phi) - dl * d(rho * u * phi)
print('S2b row rho u phi residual O(h^4)? ->', sp.simplify(series_h(lhs - rhs, 4)) == 0)

# (c) normal momentum: phi = u itself
sbar = avg(rho * u, wV)
code = rbar_ * (mbar / rbar_)**2
lhs = avg(rho * u * u, wA) - code
rhs = s2 * at0(rho) * d(u)**2 - dl * d(rho * u * u)
print('S2c rho u_n^2   residual O(h^4)? ->', sp.simplify(series_h(lhs - rhs, 4)) == 0)

# (d) pressure: <p>_A - pbar_V  (p read as the volume average of p)
lhs = avg(p, wA) - avg(p, wV)
rhs = -dl * d(p)
print('S2d pressure   residual O(h^4)? ->', sp.simplify(series_h(lhs - rhs, 4)) == 0)

# (e) pressure as snapy actually forms it: p_code = (g-1)(Ebar - mbar^2/(2 rhobar))
#     with E = p/(g-1) + rho u^2/2 pointwise (one velocity component suffices).
#     Fully symbolic simplification is slow here, so the Taylor coefficients,
#     rbar and gamma are replaced by random exact rationals (3 independent
#     draws); a rational identity that holds at random rational points holds
#     identically with probability 1 (Schwartz-Zippel); arithmetic is exact.
import random
random.seed(289)
g = sp.symbols('gamma', positive=True)
Ebar = avg(p / (g - 1) + rho * u**2 / 2, wV)
pcode = (g - 1) * (Ebar - mbar**2 / (2 * rbar_))
lhs = avg(p, wA) - pcode
rhs = -dl * d(p) - (g - 1) / 2 * s2 * at0(rho) * d(u)**2
rhs_wrong = -dl * d(p)          # what "p has no covariance piece" would give
for trial in range(3):
    vals = {c: sp.Rational(random.randint(-9, 9), random.randint(1, 9)) for c in cu + cp + cr[1:]}
    vals[cr[0]] = sp.Rational(random.randint(1, 9), random.randint(1, 9))
    vals[rb] = sp.Rational(random.randint(10, 40), random.randint(1, 5))
    vals[g] = sp.Rational(7, 5)
    e = sp.series(sp.together((lhs - rhs).subs(vals)), h, 0, 4).removeO()
    ew = sp.series(sp.together((lhs - rhs_wrong).subs(vals)), h, 0, 4).removeO()
    print(f'S2e p from cons2prim, draw {trial}: residual through h^3 = {sp.simplify(e)}'
          f'   (without the kinetic term: {sp.simplify(ew)})')

# (f) uniform tracer: phi = q constant -> correction = q * mass correction
q = sp.symbols('q')
lhs = avg(rho * u * q, wA) - rbar_ * (mbar / rbar_) * (avg(rho * q, wV) / rbar_)
print('S2f uniform q: exact face defect / (q * mass defect) =',
      sp.simplify(lhs / (q * (avg(rho * u, wA) - mbar))))

# ---------------- S3 spherical-polar theta source ----------------
rm, rp, tm, tp, dphi, th, rr = sp.symbols('r_m r_p theta_m theta_p dphi theta r', positive=True)
pc = sp.symbols('c0:5')
pr = sum(pc[k] * rr**k for k in range(5))   # generic p(r)
src = sp.integrate(sp.integrate(pr * sp.cos(th) / sp.sin(th) / rr * rr**2 * sp.sin(th),
                                (rr, rm, rp)), (th, tm, tp)) * dphi
A2 = lambda t: (rp**2 - rm**2) / 2 * sp.sin(t) * dphi
pA = sp.integrate(pr * rr, (rr, rm, rp)) / sp.integrate(rr, (rr, rm, rp))
pV = sp.integrate(pr * rr**2, (rr, rm, rp)) / sp.integrate(rr**2, (rr, rm, rp))
print('S3 exact theta source - <p>_A (A2+ - A2-) =',
      sp.simplify(src - pA * (A2(tp) - A2(tm))))
print('S3 exact theta source - pbar_V (A2+ - A2-) != 0 :',
      sp.simplify(src - pV * (A2(tp) - A2(tm))) != 0)

# ---------------- S4 gnomonic panel source ----------------
al, be = sp.symbols('alpha beta')
X, Y = sp.tan(al), sp.tan(be)
# equiangular gnomonic unit-sphere area density (sqrt(g)/r^2)
s = (1 + X**2) * (1 + Y**2) / (1 + X**2 + Y**2)**sp.Rational(3, 2)
sqrtg = rr**2 * s
# unit-normalised covariant momentum: the alpha pressure source is (p/r) d_alpha ln sqrt(g)
integrand_r = sp.simplify(pr / rr * sp.diff(sp.log(sqrtg), al) * sqrtg / s)  # r-part times d_alpha s/s
# integrand = p(r)/r * r^2 * d_alpha s  -> separate the radial factor
radial = sp.simplify(integrand_r / sp.diff(sp.log(s), al))
print('S4 gnomonic radial integrand of alpha-source  =', sp.factor(radial),
      ' (== p(r) * r: FACE measure)', sp.simplify(radial - pr * rr) == 0)
