"""Chapter 6 derivation checks: the algebra behind the why-steps and round-off bounds of the chapter 6 sections.

Ports of the code at the book pin chengcli/snapy 6fbb39750f62b83df096058a4746e77d0a634bc5 (sympy).
Each line prints [Cn] PASS or FAIL and the claim. Run: python3 src/snapy_report/ch06/checks/derivation_check.py
"""
import sympy as sp
R=sp.Rational
_res=[]
def ok(name,cond):
    _res.append(bool(cond))
    print("[C%d] %s %s"%(len(_res),"PASS" if cond else "FAIL",name))
xi,h,rm,g1=sp.symbols('xi h r_m g_1')
hp=sp.symbols('h',positive=True); rmp=sp.symbols('r_m',positive=True)

# template: continuity * phi, 1-D, phi=-g1 x
x,t=sp.symbols('x t'); rho=sp.Function('rho')(x,t); v=sp.Function('v')(x,t)
phi=-g1*x
lhs=phi*(sp.diff(rho,t)+sp.diff(rho*v,x))
rhs=sp.diff(rho*phi,t)+sp.diff(phi*rho*v,x)+rho*v*g1
ok("template: phi*(continuity) = d(rho phi)/dt + d(phi rho v)/dx + rho v g1", sp.simplify(lhs-rhs)==0)

# cell form: rho_i v_i with v_i = m_i/rho_i is m_i (C06-6)
m,rr=sp.symbols('mbar rhobar',positive=True)
ok("C06-6 rho_i * (m_i/rho_i) = m_i, so W_cell = g1 <rho v1>", sp.simplify(rr*(m/rr)-m)==0)

# fixer: sum V_i (-D rho_i/sum V rho) = -D; rk3 step weights
Vs=sp.symbols('V0:4',positive=True); rs=sp.symbols('rho0:4',positive=True); D=sp.symbols('D')
ok("fixer: sum V_i * (-D rho_i / sum_j V_j rho_j) = -D", sp.simplify(sum(Vs[i]*(-D*rs[i]/sum(Vs[j]*rs[j] for j in range(4))) for i in range(4))+D)==0)
w=[(0,1,1),(R(3,4),R(1,4),R(1,4)),(R(1,3),R(2,3),R(2,3))]
cw=[w[s][2]*sp.prod([w[u][1] for u in range(s+1,3)]) for s in range(3)]
ok("C06-3 rk3 step weights w2^(s) prod_{t>s} w1^(t) = 1/6, 1/6, 2/3", cw==[R(1,6),R(1,6),R(2,3)])
# and they are the true sensitivities of U^{n+1} to each stage increment
U0=sp.symbols('U0'); dU=sp.symbols('dU0:3'); U=U0
for s in range(3): U=w[s][0]*U0+w[s][1]*U+w[s][2]*dU[s]
ok("C06-3 dU^{n+1}/d(stage increment s) equals the step weights", [sp.diff(U,dU[s]) for s in range(3)]==cw)

# face form = 2 g1 (w_hi F+ + w_lo F-)
Ap,Am,V,xp,xm,xc,Fp,Fm=sp.symbols('A_p A_m V x_p x_m x_c F_p F_m')
Wf=g1/V*((xp-xc)*Ap*Fp+(xc-xm)*Am*Fm)
whi=R(1,2)*Ap*(xp-xc)/V; wlo=R(1,2)*Am*(xc-xm)/V
ok("face form = 2 g1 (omega_hi F+ + omega_lo F-)", sp.simplify(Wf-2*g1*(whi*Fp+wlo*Fm))==0)

# face-form error on spherical-polar, about r_m, per steradian
f=sp.symbols('f0:6'); F=sum(f[k]*xi**k/sp.factorial(k) for k in range(6))
r=rmp+xi; Vsp=sp.integrate(r**2,(xi,-hp/2,hp/2)); xcen=rmp+sp.integrate(r**2*xi,(xi,-hp/2,hp/2))/Vsp
avgF=sp.integrate(r**2*F,(xi,-hp/2,hp/2))/Vsp
Wsp=((rmp+hp/2-xcen)*(rmp+hp/2)**2*F.subs(xi,hp/2)+(xcen-rmp+hp/2)*(rmp-hp/2)**2*F.subs(xi,-hp/2))/Vsp
err=sp.series(sp.simplify(Wsp-avgF),hp,0,4).removeO()
ok("dwork-faceerr: W_face/g1 - <F> = h^2/12 F'' + h^2/(6 r) F' - h^2/(6 r^2) F + O(h^4)",
   sp.simplify(err-(hp**2/12*f[2]+hp**2/(6*rmp)*f[1]-hp**2/(6*rmp**2)*f[0]))==0)
# sigma^2 s[rho_dot] leading order is minus that error
rdot=-(sp.diff(r**2*F,xi))/r**2
ok("dwork-order: (h^2/12) d(rho_dot)/dr = -(h^2/12)(F''+2F'/r-2F/r^2) at r_m",
   sp.simplify(hp**2/12*sp.diff(rdot,xi).subs(xi,0)+hp**2/12*(f[2]+2*f[1]/rmp-2*f[0]/rmp**2))==0)

# pe4 Cartesian remainder, and spherical variance formula
q=sp.symbols('q0:6'); Rho=sum(q[k]*xi**k/sp.factorial(k) for k in range(6))
cart=sp.integrate(Rho*xi,(xi,-hp/2,hp/2))-hp*(hp**2/12)*q[1]
ok("dwork-pe4 Cartesian remainder per cell = h^5/480 rho''' (times -g1)", sp.simplify(sp.series(cart,hp,0,7).removeO()-hp**5/480*q[3])==0)
Vv=rmp**2*hp+hp**3/12
ok("dwork-variance V = r_m^2 h + h^3/12", sp.simplify(Vsp-Vv)==0)
dl=sp.integrate(r**2*xi,(xi,-hp/2,hp/2))/Vsp
ok("dwork-variance delta = r_m h^3/(6V)", sp.simplify(dl-rmp*hp**3/(6*Vv))==0)
sig=sp.integrate(r**2*xi**2,(xi,-hp/2,hp/2))/Vsp-dl**2
ok("dwork-variance sigma^2 = (r_m^2 h^3/12 + h^5/80)/V - delta^2", sp.simplify(sig-((rmp**2*hp**3/12+hp**5/80)/Vv-dl**2))==0)
ok("dwork-cs delta = h^2/(6 r_m) + O(h^4/r^3)", sp.simplify(sp.series(dl,hp,0,4).removeO()-hp**2/(6*rmp))==0)

# slope weights
dm,dp_,a,b=sp.symbols('Delta_m Delta_p a b',positive=True); z=sp.symbols('z'); y0,y1,y2=sp.symbols('y0:3')
quad=sp.interpolate([(-dm,y0),(0,y1),(dp_,y2)],z)
s_int=sp.diff(quad,z).subs(z,0)
ok("dwork-slope interior weights", sp.simplify(s_int-(-dp_/(dm*(dm+dp_))*y0+(dp_-dm)/(dm*dp_)*y1+dm/(dp_*(dm+dp_))*y2))==0)
quad0=sp.interpolate([(0,y0),(a,y1),(a+b,y2)],z)
s0=sp.diff(quad0,z).subs(z,0)
ok("dwork-slope end weights", sp.simplify(s0-(-(2*a+b)/(a*(a+b))*y0+(a+b)/(a*b)*y1-a/((a+b)*b)*y2))==0)
lump=sp.simplify(sp.Poly(s0,y0,y1,y2).coeff_monomial(y1)+sp.Poly(s0,y0,y1,y2).coeff_monomial(y2))
ok("dwork-lumped s~_0 weight on rho_1 = (2a+b)/(a(a+b)), 3/(2h) uniform", sp.simplify(lump-(2*a+b)/(a*(a+b)))==0 and sp.simplify(lump.subs({a:hp,b:hp})-R(3,2)/hp)==0)

# uniform closed forms
Fh=sp.symbols('F_m32 F_m12 F_p12 F_p32')
rd=lambda Fl,Fr: -(Fr-Fl)/hp
s_i=(rd(Fh[2],Fh[3])-rd(Fh[0],Fh[1]))/(2*hp)
WD=(Fh[1]+Fh[2])/2+hp**2/12*s_i
ok("dwork-uniform interior", sp.simplify(WD-((Fh[1]+Fh[2])/2-(Fh[3]-Fh[2]-Fh[1]+Fh[0])/24))==0)
F12,F32,F52=sp.symbols('F12 F32 F52')
s0u=(-3*rd(0,F12)+4*rd(F12,F32)-rd(F32,F52))/(2*hp)
WD0=F12/2+hp**2/12*s0u
ok("dwork-uniform wall", sp.simplify(WD0-(19*F12-5*F32+F52)/24)==0)
zz=sp.symbols('zz')
ex=lambda Fz: sp.simplify(WD0.subs({F12:Fz.subs(zz,hp),F32:Fz.subs(zz,2*hp),F52:Fz.subs(zz,3*hp)})-sp.integrate(Fz,(zz,0,hp))/hp)
ok("dwork-uniform wall exact for z, z^2, z^3 and error 19/30 h^4 for z^4", [ex(zz),ex(zz**2),ex(zz**3)]==[0,0,0] and sp.simplify(ex(zz**4)-R(19,30)*hp**4)==0)
th=sp.symbols('theta')
ok("dwork wave ratio (1 - cos3t/cos t)/12 = sin^2 t/3", sp.simplify(sp.expand_trig((1-sp.cos(3*th)/sp.cos(th))/12-sp.sin(th)**2/3))==0)

# VIC energy rows
em,Ap_,Am_=sp.symbols('e_m Aplus Aminus'); qm,qi,qp=sp.symbols('q_im1 q_i q_ip1'); wl,wh=sp.symbols('w_lo w_hi')
Fp_=(em*qi+em*qp)/2-Ap_*(qp-qi)/2; Fm_=(em*qm+em*qi)/2-Am_*(qi-qm)/2
W=2*g1*(wh*Fp_+wl*Fm_)
ok("vic-rows B_E = -g1 w_lo (e_m + A-)", sp.simplify(-sp.diff(W,qm)+g1*wl*(em+Am_))==0)
ok("vic-rows A_E = -g1 (w_lo+w_hi) e_m - g1 (w_hi A+ - w_lo A-)", sp.simplify(-sp.diff(W,qi)-(-g1*(wl+wh)*em-g1*(wh*Ap_-wl*Am_)))==0)
ok("vic-rows C_E = -g1 w_hi (e_m - A+)", sp.simplify(-sp.diff(W,qp)+g1*wh*(em-Ap_))==0)

# VIC energy row with the coupling (scalar check of eq-ch06-dwork-energyrow)
dE,dE0,dt,sd,sd0,J=sp.symbols('dE dE0 dt_c s_delta s_delta0 J')
sol=sp.solve(sp.Eq(dE/dt - g1*sd/dt + J, dE0/dt - g1*sd0/dt), dE)[0]
ok("dwork-energyrow dE = dE0 + g1 s~[d rho - d rho0] - dt_c (J delta)_E", sp.simplify(sol-(dE0+g1*(sd-sd0)-dt*J))==0)

# C06-5: phi(r_c) = phi(x1v) - g1 delta, so P_i and the extra work term
rc,x1v=sp.symbols('r_c x_1v'); phif=lambda s: -g1*s
ok("C06-5 phi(r_c) = phi(x1v) - g1 (r_c - x1v)", sp.simplify(phif(rc)-(phif(x1v)-g1*(rc-x1v)))==0)

# ---- round-off bounds used by the why-step blocks (first order in delta) ----
# (a) a sum of n terms with one rounding per addition: S_hat - S = sum_k B_k d_k + O(d^2)
d=sp.symbols('d1:4'); bt=sp.symbols('b0:4'); e=sp.symbols('eps')
Sh=bt[0]
for k in range(1,4): Sh=(Sh+bt[k])*(1+e*d[k-1])
B=[sum(bt[:k+1]) for k in range(4)]
first=sp.expand(sp.series(Sh,e,0,2).removeO())-sum(bt)
ok("bound(a): fl-sum error = sum_k B_k delta_k to first order", sp.simplify(first-e*sum(B[k]*d[k-1] for k in range(1,4)))==0)
# (b) telescoping face terms: exact sum of per-cell terms t_i = (Q_{i+1/2}-Q_{i-1/2}) with Q_{-1/2}=Q_{n-1/2}=0 is zero
Q=sp.symbols('Q0:5')
ok("bound(b): sum_i (Q_{i+1/2} - Q_{i-1/2}) with zero wall values is 0", sp.simplify(sum((Q[i+1] if i+1<4 else 0)-(Q[i] if i>0 else 0) for i in range(4)))==0)
# (c) fixer deposit: M_hat=M(1+tM), efix=-D/M_hat*(1+t1) in double, converted to the state dtype (1+tc),
# d_i=m_i efix (1+t2_i), E_new=(E+d)(1+t3_i)  (meshblock.cpp apply_gravity_work_fixer at the pin)
D_,tM,t1,tc=sp.symbols('D tM t1 tc'); ms=sp.symbols('mv0:3',positive=True); Es=sp.symbols('E0:3'); t2=sp.symbols('t2_0:3'); t3=sp.symbols('t3_0:3')
M_=sum(ms); efix=-D_/(M_*(1+e*tM))*(1+e*t1)*(1+e*tc)
dE=sum((Es[i]+ms[i]*efix*(1+e*t2[i]))*(1+e*t3[i])-Es[i] for i in range(3))
lin=sp.expand(sp.series(dE+D_,e,0,2).removeO())
target=e*(D_*(tM-t1-tc)-sum(D_*ms[i]/M_*t2[i] for i in range(3))+sum((Es[i]-D_*ms[i]/M_)*t3[i] for i in range(3)))
ok("bound(c): sum V dE + D = D(tM - t1 - tc) - sum D m_i/M t2_i + sum E_i^new t3_i to first order", sp.simplify(lin-sp.expand(target))==0)
# (d) the |D| coefficient: |tM| <= N_f, |t1|, |tc|, |t2_i| <= 1 and sum m_i/M = 1, so N_f + 3; without tc it is N_f + 2
Nf=sp.symbols('N_f',positive=True,integer=True)
coef=Nf+1+1+sum(ms[i]/M_ for i in range(3))
ok("bound(d): the |D| coefficient of the fixer deposit is N_f + 3 (the conversion of efix to the state dtype included), not N_f + 2", sp.simplify(coef-(Nf+3))==0 and sp.simplify(coef-1-(Nf+2))==0)

print("%d passed, %d failed"%(sum(_res),len(_res)-sum(_res)))
