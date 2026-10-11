"""Check of the cubed-sphere centroid-offset term of the corrected-PE face work (section 6.4).

Ports, line for line, x1_variance, centroid_slope, x1_centroid_offset and corrected_pe_work of
src/hydro/gravity_work_radial.hpp at snapy@9ad0936779ae001dba65c9eafccaa7c058686c97, on a
gnomonic-equiangle column per steradian (A = r^2, V = (r+^3 - r-^3)/3, x1v = face midpoint).
[CS1] booked work + change of P sums to the wall potential flux (zero) with the term, and leaves
      an O(h^2/R) defect if the term is in the work but not in P.
[CS2] |P - int rho phi dV| / |int rho phi dV|: order 4 with the term in P, order 2 without.
Nondimensional: g1 = -10, scale height H = 1, inner radius R.  Run: python3 d_cs_centroid_term_check.py
"""
import numpy as np

G = -10.0


def variance(f):
    h = np.diff(f); rb = .5 * (f[1:] + f[:-1]); v = rb * rb * h + h**3 / 12.
    sh = rb * h**3 / (6. * v)
    return (rb * rb * h**3 / 12. + h**5 / 80.) / v - sh * sh


def slope(q, x):
    n = len(x); s = np.zeros_like(q); hm = x[1:-1] - x[:-2]; hp = x[2:] - x[1:-1]
    s[1:-1] = -hp / (hm * (hm + hp)) * q[:-2] + (hp - hm) / (hm * hp) * q[1:-1] + hm / (hp * (hm + hp)) * q[2:]
    a, b = x[1] - x[0], x[2] - x[1]
    s[0] = -(2 * a + b) / (a * (a + b)) * q[0] + (a + b) / (a * b) * q[1] - a / ((a + b) * b) * q[2]
    a, b = x[-2] - x[-3], x[-1] - x[-2]
    s[-1] = b / (a * (a + b)) * q[-3] - (a + b) / (a * b) * q[-2] + (a + 2 * b) / ((a + b) * b) * q[-1]
    return s


def offset(f, xv):
    h = np.diff(f); rb = .5 * (f[1:] + f[:-1]); v = rb * rb * h + h**3 / 12.
    return rb * h**3 / (6. * v) + (rb - xv)


def column(R, n, L=4.0):
    f = R + np.linspace(0., L, n + 1); xv = .5 * (f[1:] + f[:-1])
    return f, xv, (f[1:]**3 - f[:-1]**3) / 3.


def P(rho, f, xv, V, delta=True):
    p = rho * (-G * xv) - G * variance(f) * slope(rho, xv)
    if delta: p = p - G * offset(f, xv) * rho
    return np.sum(V * p)


rng = np.random.default_rng(303)
print("[CS1] one stage, random interior fluxes, walls closed; (dE_grav + dP) / sum|W V dt|")
for R in (5., 60., 1000.):
    f, xv, V = column(R, 32); A = f * f; F = np.r_[0., rng.standard_normal(31), 0.]; dt = 1e-3
    drho = -dt * np.diff(A * F) / V
    face = -V * drho * (-G * xv) - dt * np.diff(A * (-G * f) * F)        # dt W_face V
    corr = V * G * (variance(f) * slope(drho, xv) + offset(f, xv) * drho)  # dt (sigma^2 s + delta) V g1
    W = face + corr  # P is linear in rho, so its change over the stage is P[drho] exactly
    d_with = np.sum(W) + P(drho, f, xv, V)
    d_without = np.sum(W) + P(drho, f, xv, V, False)
    sc = np.sum(np.abs(W))
    print(f"  R/H={R:6.0f}: with term {d_with / sc:+.2e}   term in W but not in P {d_without / sc:+.2e}")
    assert abs(d_with / sc) < 1e-12 and abs(d_without / sc) > 1e3 * abs(d_with / sc)

print("[CS2] |P - int rho phi dV| / |int rho phi dV|, rho = exp(-(r - R)), R = 5")
xg, wg = np.polynomial.legendre.leggauss(8)
errs = {True: [], False: []}; ns = (16, 32, 64, 128)
for n in ns:
    f, xv, V = column(5., n)
    a, b = f[:-1, None], f[1:, None]; r = .5 * (a + b) + .5 * (b - a) * xg; w = .5 * (b - a) * wg * r * r
    rho = np.sum(w * np.exp(-(r - 5.)), 1) / V; exact = np.sum(w * np.exp(-(r - 5.)) * (-G * r))
    for d in (True, False): errs[d].append(abs(P(rho, f, xv, V, d) - exact) / abs(exact))
for d in (True, False):
    e = np.array(errs[d]); o = np.log2(e[:-1] / e[1:])
    print(f"  {'with' if d else 'without'} term: " + " ".join(f"{x:.2e}" for x in e) + "  orders " + " ".join(f"{x:.2f}" for x in o))
assert min(np.log2(np.array(errs[True][1:-1]) / np.array(errs[True][2:]))) > 3.7  # last three resolutions
assert max(np.log2(np.array(errs[False][:-1]) / np.array(errs[False][1:]))) < 2.3
print("ALL PASS (2 claims)")
