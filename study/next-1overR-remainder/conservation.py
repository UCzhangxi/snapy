"""(c) Gravity-work weights on the spherical-polar x1 grid: discrete E+PE conservation and
local accuracy.  sympy for the exact per-face identities, numpy for the local order.

Discrete E+PE = sum_i V_i (E_i + rho_i phi_i), phi_i = g r_c,i.  The x1 mass fluxes change
sum V rho phi by -g sum_f A_f F_f (r_c,i+1 - r_c,i), so a work W_i = -g sum_f c_if F_f
conserves E+PE iff for every interior face f the column sum  sum_i V_i c_if = A_f (r_c,i+1 - r_c,i).
"""
import numpy as np
import sympy as sp

h, rf = sp.symbols("h r_f", positive=True)


def cell(rm, rp):
    V = (rp**3 - rm**3) / 3
    x1v = sp.Rational(3, 4) * (rp**4 - rm**4) / (rp**3 - rm**3)
    return V, x1v, x1v - (rm + rp) / 2


Vi, xi, di = cell(rf - h, rf)          # cell below face f
Vj, xj, dj = cell(rf, rf + h)          # cell above face f
A = rf**2

print("1. Face form, phi_c = g x1v: column sum of face f = A_f (x1v_i+1 - x1v_i) by construction")
print("   (each face's work is split at r_f), so E+PE closes to round-off for any F.")

# teammate's exact-measure 2-face weight: W_i = -g [(1/2 + d/h) F+ + (1/2 - d/h) F-]
# (exact for F linear in r under r^2 dr); its column sum for face f, minus what phi = g x1v needs
col = Vi * (sp.Rational(1, 2) + di / h) + Vj * (sp.Rational(1, 2) - dj / h)
leak = sp.simplify(col - A * (xj - xi))
print("\n2. Exact-measure weight, phi_c = g x1v:  column sum - A_f dx1v =")
print("  ", sp.factor(leak))
print("   series:", sp.series(leak, h, 0, 6).removeO())
print("   -> E+PE changes at d/dt = -g sum_f F_f * leak_f per unit solid angle: not conservative;")
print("      relative to the work, leak/(A h) = h^2/(3 r^2) + O(h^4).")

# best possible with phi_c = g x1v: sum_i V_i W_i is pinned to -g sum_f A_f dx1v_f F_f
need = sp.series(A * (xj - xi) - h * rf**2, h, 0, 6).removeO()
print("\n3. Any conservative work with phi_c = g x1v has  sum_i V_i W_i = -g sum_f F_f A_f dx1v_f, and")
print("   A_f dx1v_f - h r_f^2 =", sp.simplify(need))
print("   while the exact sum_i V_i <F>_V = int r^2 F dr = sum_f h r_f^2 F_f + (Cartesian end terms).")
print("   The bulk difference -(h^3/6) sum_f F_f = -(h^2/6) int F dr cannot be removed locally:")
print("   phi_c = g x1v caps every conservative work at an O(h^2/R^2) error, -g (h^2/6) F / r^2 in W.")

# r_c = rbar: column sum A_f h, exactly the trapezoid rule on G = r^2 F
Vm, xm, dm = cell(rf - h, rf)
print("\n4. phi_c = g rbar (arithmetic mid-radius): face form = (h/2V)(G+ + G-), G = r^2 F, the")
print("   trapezoid rule; curv_flux1 on G, A_f H_f = (h/12)(G_i - G_i-1), is divergence form (zero at")
print("   walls, conservative) and removes -(h^2/12) G'' (Euler-Maclaurin): exact to O(h^4).")

# ---- numerics: local error of W_i vs -g <F>_V, smooth F, R = 5 H_b, L = 1 ----
from numpy.polynomial.legendre import leggauss
xg, wg = leggauss(12)
F = lambda r, R: np.sin(np.pi * (r - R)) * (R / r) ** 2 * np.exp(-(r - R))
print("\n5. Local error max_i |W_i - <F>_V,i| (g = 1), F = sin(pi z)(R/r)^2 e^-z, R = 5, L = 1;")
print("   columns: nz, err*nz^2 and err*nz^4 for each form")
forms = ["face x1v + curv main", "exact wts + curv main", "face rbar + curv r^2m"]
rows = []
for nz in (16, 32, 64, 128, 256):
    R = 5.0
    hh = 1.0 / nz
    rfi = R + hh * np.arange(nz + 1)
    rm, rp = rfi[:-1], rfi[1:]
    V = hh * (rm**2 + rm * rp + rp**2) / 3
    rb = 0.5 * (rm + rp)
    dv = rb * hh**2 / (2 * (rm**2 + rm * rp + rp**2))
    r = rb[:, None] + 0.5 * hh * xg[None, :]
    Fav = (F(r, R) * r**2 * wg).sum(1) / (r**2 * wg).sum(1)      # <F>_V = cell mass flux m_c
    Ff = F(rfi, R)
    A1 = rfi**2
    out = []
    # main: face split at x1v + curv on m, H = dx1v/12 dm_c
    Wf = (A1[1:] * Ff[1:] * (0.5 * hh - dv) + A1[:-1] * Ff[:-1] * (0.5 * hh + dv)) / V
    H = np.zeros(nz + 1); H[1:-1] = (hh + dv[1:] - dv[:-1]) / 12 * (Fav[1:] - Fav[:-1])
    divH = (A1[1:] * H[1:] - A1[:-1] * H[:-1]) / V
    out.append(Wf - divH - Fav)
    We = (0.5 + dv / hh) * Ff[1:] + (0.5 - dv / hh) * Ff[:-1]
    out.append(We - divH - Fav)
    Wt = 0.5 * hh * (A1[1:] * Ff[1:] + A1[:-1] * Ff[:-1]) / V
    Gc = rb**2 * Fav
    HG = np.zeros(nz + 1); HG[1:-1] = hh / 12 * (Gc[1:] - Gc[:-1]) / A1[1:-1]
    out.append(Wt - (A1[1:] * HG[1:] - A1[:-1] * HG[:-1]) / V - Fav)
    sl = slice(2, nz - 2)                     # interior (curv is zeroed at the walls)
    rows.append((nz, [np.abs(e[sl]).max() for e in out]))
for nz, errs in rows:
    print(f"   nz {nz:4d}  " + "   ".join(f"{f}: {e*nz**2:.2e} / {e*nz**4:.2e}" for f, e in zip(forms, errs)))
# split main's error into its O(h^2/R^2) prediction  (h^2/6) F / r^2
nz = 256; hh = 1 / nz; R = 5.0
rb = R + hh * (np.arange(nz) + 0.5)
print(f"   main's O(h^2) error vs the prediction +(h^2/6) F/r^2 at nz {nz}: "
      f"ratio {np.abs(rows[-1][1][0]) / np.abs(hh**2 / 6 * F(rb, R) / rb**2)[2:-2].max():.3f}")
