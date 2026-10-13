"""Chapter 5 derivation checks: the sympy claims behind the derivation steps of the chapter 5 sections.

Pure sympy, no snapy import; each line prints PASS or FAIL and the claim. The formulas are those of chengcli/snapy
at the book pin 6fbb39750f62b83df096058a4746e77d0a634bc5. Run: python3 src/snapy_report/ch05/derivation_check.py
"""
import sympy as sp
R=sp.Rational
ok=lambda name,cond: print(("PASS " if cond else "FAIL ")+name)

# --- XC-1: centroid defect and its remainder
rm,D,xi=sp.symbols('r_m Delta xi',positive=True)
q=sp.symbols('q0:7')
Q=sum(q[k]*xi**k/sp.factorial(k) for k in range(7))
w=(rm+xi)**2
I2=sp.integrate(w,(xi,-D/2,D/2)); I3=sp.integrate(w*xi,(xi,-D/2,D/2))
ok("XC-1 int r^2 dr = D(rm^2+D^2/12)", sp.simplify(I2-D*(rm**2+D**2/12))==0)
ok("XC-1 int (r-rm) r^2 dr = rm D^3/6", sp.simplify(I3-rm*D**3/6)==0)
delta=I3/I2
ok("XC-1 delta = 2 D^2 rm/(D^2+12 rm^2)", sp.simplify(delta-2*D**2*rm/(D**2+12*rm**2))==0)
xi2=sp.integrate(w*xi**2,(xi,-D/2,D/2))/I2
ok("XC-1 <xi^2> = D^2/12 + O(D^4/rm^2)", sp.simplify(sp.series(xi2,D,0,5).removeO()-(D**2/12+D**4/(180*rm**2)))==0)
avg=sp.integrate(sp.expand(w*Q),(xi,-D/2,D/2))/I2; plain=sp.integrate(Q,(xi,-D/2,D/2))/D
rem=sp.series(avg-plain-delta*q[1],D,0,6).removeO()
ok("XC-1 remainder = D^4 q3/(240 rm) + D^4 q2/(360 rm^2) + O(D^6)", sp.simplify(rem-(D**4*q[3]/(240*rm)+D**4*q[2]/(360*rm**2)))==0)

# --- XC-3: integration by parts of the pressure source (per unit solid angle)
r,rmi,rpl=sp.symbols('r r_minus r_plus',positive=True)
c=sp.symbols('c0:6'); pt=sum(c[k]*r**k for k in range(6))       # any quintic
V=(rpl**3-rmi**3)/3; S=2/V*sp.integrate(r*pt,(r,rmi,rpl))
lhs=-(rpl**2*pt.subs(r,rpl)-rmi**2*pt.subs(r,rmi))/V+S
rhs=-sp.integrate(r**2*sp.diff(pt,r),(r,rmi,rpl))/V
ok("XC-3 -(A+p+ - A-p-)/V + S = -V^-1 int r^2 dp/dr dr", sp.simplify(lhs-rhs)==0)
p0=sp.symbols('p0'); S0=2/V*sp.integrate(r*p0,(r,rmi,rpl))
ok("XC-3 constant p: S V = A+ - A-", sp.simplify(S0*V-(rpl**2-rmi**2)*p0)==0)

# --- OR-1: Favre expansion, remainder O(D^4)
rr=sp.symbols('rho0:6'); vv=sp.symbols('v0:6')
Rho=sum(rr[k]*xi**k/sp.factorial(k) for k in range(6)); Vel=sum(vv[k]*xi**k/sp.factorial(k) for k in range(6))
Iw=lambda f: sp.integrate(sp.expand(w*f),(xi,-D/2,D/2))
fav=Iw(Rho*Vel)/Iw(Rho); vbar=sp.integrate(Vel,(xi,-D/2,D/2))/D
ok("OR-1 vbar = v + D^2 v''/24 + O(D^4)", sp.simplify(sp.series(vbar,D,0,4).removeO()-(vv[0]+D**2*vv[2]/24))==0)
s=sp.series(fav-vbar-(D**2/12*rr[1]*vv[1]/rr[0]+delta*vv[1]),D,0,4).removeO()
ok("OR-1 Favre - plain = D^2/12 rho'v'/rho + delta v' + O(D^4)", sp.simplify(s)==0)
# Cartesian (rm -> oo) intermediate lines
cart_fav=sp.integrate(Rho*Vel,(xi,-D/2,D/2))/sp.integrate(Rho,(xi,-D/2,D/2))
ok("OR-1 Cartesian: <rho v>/<rho> = v + D^2 rho'v'/(12 rho) + D^2 v''/24 + O(D^4)",
   sp.simplify(sp.series(cart_fav,D,0,4).removeO()-(vv[0]+D**2*rr[1]*vv[1]/(12*rr[0])+D**2*vv[2]/24))==0)

# --- moment solves for six-face cell averages (RK5-1, WC-2)
def six_face(offsets):
    w_=sp.symbols('w0:6'); eqs=[sum(w_[m]*offsets[m]**k for m in range(6))-sp.integrate(xi**k,(xi,-R(1,2),R(1,2))) for k in range(6)]
    sol=sp.solve(eqs,w_,dict=True)[0]; return [sol[w_[m]] for m in range(6)]
w6=six_face([m-R(5,2) for m in range(6)])
ok("RK5-1 w6 = (11,-93,802,802,-93,11)/1440", w6==[R(x,1440) for x in (11,-93,802,802,-93,11)])
ok("RK5-1 code w6 = {11/1440,-31/480,401/720,...}", [R(11,1440),R(-31,480),R(401,720)]==w6[:3])
w6e0=six_face([m-R(1,2) for m in range(6)]); w6e1=six_face([m-R(3,2) for m in range(6)])
ok("WC-2 w6e wall cell", w6e0==[R(95,288),R(1427,1440),R(-133,240),R(241,720),R(-173,1440),R(3,160)])
ok("WC-2 w6e next cell", w6e1==[R(-3,160),R(637,1440),R(511,720),R(-43,240),R(77,1440),R(-11,1440)])

# --- WC-1: repeated wall cell
x0,a=sp.symbols('chi0 a')
chi=lambda j: x0 if j<0 else x0+j*a
binom=lambda j: (chi(j-2)+4*chi(j-1)+6*chi(j)+4*chi(j+1)+chi(j+2))/16
exact=lambda j: x0+j*a
errs=[sp.simplify(binom(j)-exact(j)) for j in (-1,0,1,2)]
ok("WC-1 chi^s_0 - chi_0 = 3a/8, chi^s_1 - chi_1 = a/16", errs[1]==R(3,8)*a and errs[2]==a/16)
face=[sp.simplify((errs[f]+errs[f+1])/2) for f in range(3)]+[sp.simplify((binom(2)+binom(3)-exact(2)-exact(3))/2)]
ok("WC-1 face errors 23/32, 7/32, 1/32, 0 (times a)", face==[R(23,32)*a,R(7,32)*a,R(1,32)*a,0])

# --- WB4-1: face weights from the derivative of the quartic through the primitive
h=sp.symbols('h',positive=True); rho=sp.symbols('rho0:4'); x=sp.symbols('x')
Pv=[0]; [Pv.append(Pv[-1]+rho[k]*h) for k in range(4)]
P=sp.interpolate(list(zip([j*h for j in range(5)],Pv)),x)
got=[sp.Poly(sp.expand(sp.diff(P,x).subs(x,j*h)),*rho).coeffs() for j in range(3)]
want=[[R(25,12),R(-23,12),R(13,12),R(-3,12)],[R(3,12),R(13,12),R(-5,12),R(1,12)],[R(-1,12),R(7,12),R(7,12),R(-1,12)]]
ok("WB4-1 face weights j=0,1,2", got==want)
F=[R(-1,16),R(4,16),R(10,16),R(4,16),R(-1,16)]
ok("WB4 (extra) F moments 1,0,0,0,-3/2", [sum(F[m]*(m-2)**k for m in range(5)) for k in range(5)]==[1,0,0,0,R(-3,2)])
c0,c1,c2,c3=sp.symbols('c0:4'); cub=sp.interpolate([(0,c0),(1,c1),(2,c2),(3,c3)],x)
ok("WB4 (extra) cubic wall values", sp.expand(cub.subs(x,-1)-(4*c0-6*c1+4*c2-c3))==0 and sp.expand(cub.subs(x,-2)-(10*c0-20*c1+15*c2-4*c3))==0)

# --- RK5-2: face-density offset with the kernel's own operators
X=sp.symbols('X'); H=sp.symbols('H',positive=True); cc=sp.symbols('c')
a_=sp.symbols('a0:5'); b_=sp.symbols('b0:5')
p=sum(a_[k]*X**k for k in range(5)); ch=sum(b_[k]*X**k for k in range(5))   # point p and chi; rho = p chi
cellavg=lambda f,k: sp.integrate(f,(X,(k-1)*H,k*H))/H          # cell k spans [(k-1)H, kH]; face 0 is X=0 between cells 0 and 1
face=lambda k: k*H                                                # face k at X = kH (right face of cell k)
psf=lambda k: p.subs(X,face(k))+cc
prefc=lambda k: sum(w6[m]*psf(k-3+m) for m in range(6))          # six faces k-3..k+2 around cell k (faces k-1, k)
chic=lambda k: cellavg(p*ch,k)/cellavg(p,k)
chis=lambda k: (chic(k-2)+4*chic(k-1)+6*chic(k)+4*chic(k+1)+chic(k+2))/16
rhoref=lambda k: prefc(k)*chis(k)
rhosf0=psf(0)*(chis(0)+chis(1))/2                                  # face between cells 0 and 1
W=lambda f: (2*f(-2)-13*f(-1)+47*f(0)+27*f(1)-3*f(2))/60           # fifth-order linear left value at the right face of cell 0
def ser(e,n=4): return sp.series(e,H,0,n).removeO()
chic=lambda k: ser(sp.cancel(cellavg(p*ch,k)/cellavg(p,k)))
off=sp.expand(ser(sp.expand(rhosf0-W(rhoref)),3))
pd=[sp.diff(p,X,k).subs(X,0) for k in range(3)]; cd=[sp.diff(ch,X,k).subs(X,0) for k in range(3)]
target=H**2/12*(pd[1]*cd[1]+2*pd[0]*cd[2])+cc*H**2/6*cd[2]
ok("RK5-2 rho_sf - W[rho_ref] = H^2/12 (p' chi' + 2 p chi'') + c H^2/6 chi'' + O(H^3)", sp.expand(off-target)==0)

# --- LG-1: legacy isentropic ghost ODE
pp,K,g,gam=sp.symbols('p K g gamma',positive=True)
aa=(gam-1)/gam; rho_=(pp/K)**(1/gam)
ok("LG-1 d(p^a)/dx = a p^(a-1)(-rho g) = -a g / K^(1/gamma)", sp.simplify(aa*pp**(aa-1)*(-rho_*g)+aa*g/K**(1/gam))==0)
