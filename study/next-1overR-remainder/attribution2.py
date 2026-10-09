"""Tables for README.md (replica2.py, ~2 min CPU).  Excess = (eps nz^2 sphere - eps nz^2 Cartesian
twin) * R/H_b, nz = 128, in the PR #293 harness sign and H_b units (g = R_gas = T_b = 1)."""
import numpy as np
from replica2 import Deck, run, excess, INF

AB = Deck(gam=5/3, m=1.5, L=6.488906699059797 / (7.488906699059797 / 2.5), name="AB")
L1 = Deck(name="L1")
NZ = 128
Rs = (5, 20, 1000)

print("A. The three teammate facts in the replica.  AB = Anders-Brown polytrope deck of")
print("   tests/test_wb_wall_corner.cpp (gamma 5/3, adiabatic, depth 2.17 H_b); L1 = gamma 1.4, depth 1 H_b.")
print("   seed 'sph': rho w ~ sin (the #293 harness roll), anelastic on the sphere; 'wsph': w ~ sin.")
print("   floor = continuum truth of the diagnostic for the Cartesian roll copied onto the sphere;")
print("   main = d59836d, face work + curv_flux1, main's WB reference, x3 off;")
print("   term = main - (main with the 2-face weights exact for the r^2 measure, curv_flux1 kept).")
for d in (AB, L1):
    for sd, sc in (("sph", "cart"), ("wsph", "wcart")):
        fl = [excess(d, R, NZ, seed=sc, truth=True) for R in (5, 1000)]
        mn = [excess(d, R, NZ, seed=sd, ref="code") for R in (5, 1000)]
        tm = [mn[i] - excess(d, R, NZ, seed=sd, ref="code", gwork="face-exact") for i, R in enumerate((5, 1000))]
        print(f"   {d.name} {sd:4s}  floor {fl[0]:+.3f} {fl[1]:+.3f}   main {mn[0]:+.3f} {mn[1]:+.3f}"
              f"   term {tm[0]:+.3f} {tm[1]:+.3f}   floor/term {fl[1]/tm[1]:+.2f}  main/term {mn[1]/tm[1]:+.2f}")
print("   teammate (R = 5, 1000): floor +1.72 +1.95, main -1.43 -1.69, term -1.07 -1.23 (shift +1.05 +1.19)")
print("                            floor/term -1.59, main/term +1.37")

ARMS = [("1 main (face+curv, WB main, x3 off)", dict(ref="code")),
        ("2  + exact 2-face wts, curv main  [d]", dict(ref="code", gwork="face-exact")),
        ("3  + x1 r^2 weights (0.3)", dict(ref="code", gwork="face-exact", recon="sph")),
        ("4  + exact WB reference   [= (b)]", dict(gwork="face-exact", recon="sph")),
        ("5  + x3 #293", dict(gwork="face-exact", recon="sph", x3corr="full")),
        ("6  + x3 exact face average", dict(gwork="face-exact", recon="sph", x3corr="exact")),
        ("7 main face+curv, exact WB, x3 off", dict()),
        ("8 main face+curv, exact WB, x3 #293", dict(x3corr="full")),
        ("9 main face+curv, exact WB, x3 exact", dict(x3corr="exact")),
        ("10 rbar+curv(r^2m), x1, WB, x3 #293", dict(gwork="face-rbar", recon="sph", x3corr="full")),
        ("11 rbar+curv(r^2m), x1, WB, x3 exact", dict(gwork="face-rbar", recon="sph", x3corr="exact")),
        ("12 exact wts+curv sph, x1, WB, x3 ex", dict(gwork="face-exact", curv="sph", recon="sph", x3corr="exact")),
        ("13 cell work, x1, WB, x3 exact", dict(gwork="cell", recon="sph", x3corr="exact"))]
print("\nB. Excess along the fixes, nz 128, R = " + ", ".join(map(str, Rs)) + "   | Cartesian twin eps nz^2")
for d, sd in ((AB, "sph"), (AB, "wsph"), (L1, "sph")):
    print(f"   {d.name}, seed {sd}")
    for name, kw in ARMS:
        print(f"   {name:38s} " + " ".join(f"{excess(d, R, NZ, seed=sd, **kw):+.4f}" for R in Rs)
              + f"   | {run(d, INF, NZ, seed=sd, **kw):+.4f}")

print("\nC. The face-form entropy identity (exact WB reference): rho T S = -(h(r_c) - h_c) div1 F")
print("   + g div1 H  - div3(F3E - h_c F3).  Excess and Cartesian value of each part:")
for d, sd in ((AB, "sph"), (AB, "wsph"), (L1, "sph")):
    for name, kw in (("main face+curv, x3 off", dict()), ("main face+curv, x3 exact", dict(x3corr="exact")),
                     ("rbar+curv(r^2m), x3 exact", dict(gwork="face-rbar", x3corr="exact"))):
        c = run(d, INF, NZ, seed=sd, parts="terms", **kw)
        ex = {R: run(d, R, NZ, seed=sd, parts="terms", **kw) for R in (5, 1000)}
        print(f"   {d.name} {sd:4s} {name:26s} cart: " + " ".join(f"{k} {c[k]:+.3f}" for k in c)
              + " | excess R5: " + " ".join(f"{k} {(ex[5][k]-c[k])*5:+.3f}" for k in c)
              + " | R1000: " + " ".join(f"{k} {(ex[1000][k]-c[k])*1000:+.3f}" for k in c))

print("\nD. E+PE per phi column, max |sum_i V (W + g r_c d1 rho)| / sum |V W|, R = 5, nz 128, AB")
for gw, cv in (("face", True), ("face-exact", True), ("face-rbar", True)):
    print(f"   {gw:10s}: {run(AB, 5., NZ, gwork=gw, curv=cv, parts='budget'):.2e}")
