"""Tables for README.md: what main's spherical-polar x1/x2 operators put into eps_eff nz^2
at O(h^2/R), term by term, and what the fixes leave (replica.py; ~1 min CPU)."""
import numpy as np
from replica import run, background, CP, G

INF = 1e6     # the Cartesian limit (cancellation-free metrics make R = 1e6 exact enough)

print("A. Cartesian-limit check of the replica against tests/test_horizontal_flux_covariance.py")
print("   (harness: off in [-0.32,-0.20]; on, face work, CART_REF -0.0130/-0.0049/+0.0003 at nz 16/32/64)")
for nz in (16, 32, 64, 128):
    off = run(INF, nz, gwork="face", ref="code")
    on = run(INF, nz, gwork="face", ref="code", x3corr="full")
    print(f"   nz {nz:4d}  off {off:+.4f}  on {on:+.4f}")

ARMS = [("cell work, x3 off", dict()),
        ("cell work, x3 #293 full", dict(x3corr="full")),
        ("face work, x3 #293 full", dict(gwork="face", x3corr="full")),
        ("cell work, x3 full, WB ref as main", dict(x3corr="full", ref="code")),
        ("FIX: cell, x3 full, r^2 x1 weights", dict(x3corr="full", recon="sph")),
        ("FIX: + WB ref with r^2 weights", dict(x3corr="full", recon="sph", ref="code-sph")),
        ("FIX: face, x3 full, r^2 x1 weights", dict(gwork="face", x3corr="full", recon="sph"))]

print("\nB. R * [eps nz^2 (R) - eps nz^2 (inf)], nz = 64, anelastic roll (truth = 0 exactly)")
print(f"   {'arm':38s}" + "".join(f"  R={R:<5g}" for R in (5, 10, 20, 40)))
for name, kw in ARMS:
    cart = run(INF, 64, **kw)
    print(f"   {name:38s}" + "".join(f"  {(run(R, 64, **kw) - cart) * R:+.4f}" for R in (5., 10., 20., 40.)))

print("\nC. Convergence of the 1/R content at R = 5: 5 [eps nz^2 (5) - eps nz^2 (inf)]")
print(f"   {'arm':38s}" + "".join(f"  nz={n:<4d}" for n in (32, 64, 128, 256)))
for name, kw in ARMS[1:3] + ARMS[4:6]:
    print(f"   {name:38s}" + "".join(f"  {(run(5., n, **kw) - run(INF, n, **kw)) * 5:+.5f}"
                                      for n in (32, 64, 128, 256)))

# analytic leading term of the x1 reconstruction bias (README eq. 3.4), cell work:
#   eps nz^2 = (g/cp) (1/6R) sum rho w w' / sum rho w^2 ,  w = k sin(pi z) R^2 / (rho r^2)
print("\nD. Analytic prediction of the x1-weight term (eq. 3.4), cell work, vs B row 2 - row 5")
for R in (5., 10., 20., 40.):
    T, p, rho = background(R)
    r = R + (np.arange(20000) + 0.5) / 20000
    w = np.sin(np.pi * (r - R)) * R**2 / (rho(r) * r**2)
    wp = np.gradient(w, r)
    pred = (G / CP) / 6 * (rho(r) * w * wp).sum() / (rho(r) * w * w).sum()
    meas = ((run(R, 128, x3corr="full") - run(INF, 128, x3corr="full"))
            - (run(R, 128, x3corr="full", recon="sph") - run(INF, 128, x3corr="full", recon="sph"))) * R
    print(f"   R={R:4g}  predicted R*eps nz^2 = {pred:+.5f}   replica = {meas:+.5f}")

print("\nE. The diagnostic itself: continuum truth of eps nz^2 for the CARTESIAN roll copied onto")
print("   the sphere (not anelastic there: div(rho v) = 2 rho w / r + ...). Scheme-independent.")
for R in (5., 10., 20., 40.):
    t = run(R, 64, seed="cart", truth=True)
    s = run(R, 64, seed="cart", x3corr="full")
    print(f"   R={R:4g}  truth {t:+.5f}  R*truth {t * R:+.4f}   scheme(cell, x3 full) - truth {s - t:+.5f}")
