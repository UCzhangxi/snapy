"""Reference numbers for the curved-grid x2-face covariance (item 2c).
Units H = R = g = T_b = p_b = 1 (g constant, as const-gravity), gamma 1.4.
Column r in [Rb, Rb+1], adiabatic (eps = 0): T0 = 1 - (r-Rb)/Cp, p0 = T0^Cp, rho0 = p0/T0.
(A) flux test on one x2 (theta) face: u_n(r) = cos(pi (r-Rb)) at the face;
    exact face average (weight r) vs snapy's flux from cell averages (weight r^2,
    spherical exact volume; gnomonic trapezoid volume).
(B) eps = 0 entropy tendency projected on w = sin(pi (r-Rb)), anelastic D."""
import numpy as np
from numpy.polynomial.legendre import leggauss

g, Rg, gam = 1.0, 1.0, 1.4
cp = gam / (gam - 1) * Rg
beta = g / cp
xg, wg = leggauss(24)


def bg(Rb):
    T = lambda r: 1 - beta * (r - Rb)
    p = lambda r: T(r) ** (1 / beta)
    rho = lambda r: p(r) / (Rg * T(r))
    h = lambda r: cp * T(r)
    return T, p, rho, h


def flux_test(Rb, nz, cells):
    T, p, rho, h = bg(Rb)
    d = 1.0 / nz
    u = lambda r: np.cos(np.pi * (r - Rb))
    rows = []
    for i in cells:
        rm = Rb + (i + 0.5) * d
        r = rm + 0.5 * d * xg
        q = lambda f, w: (f(r) * w(r) * wg).sum() * d / 2
        wf = lambda r: r; wc = lambda r: r**2; one = lambda r: 1.0 + 0 * r
        for kind in ("cart", "sph", "gno"):
            if kind == "cart":
                Vf = q(one, one); Vc = Vf; wfk, wck = one, one
            else:
                Vf = q(wf, one); wfk, wck = wf, wc
                Vc = q(wc, one) if kind == "sph" else (rm**2 + d**2 / 4) * d
            avgc = lambda f: q(f, wck) / Vc
            exact = q(lambda r: rho(r) * h(r) * u(r), wfk) / Vf
            m, P, Rh = avgc(lambda r: rho(r) * u(r)), avgc(p), avgc(rho)
            scheme = m * cp * P / (Rg * Rh)
            exact_m = q(lambda r: rho(r) * u(r), wfk) / Vf
            err_E, err_m = exact - scheme, exact_m - m
            # cell-centred analytic derivatives at the midpoint
            e = 1e-6
            D = lambda f: (f(rm + e) - f(rm - e)) / (2 * e)
            cart = d**2 / 12 * rho(rm) * D(u) * D(h)
            a = 0.0 if kind == "cart" else -1.0 / rm
            nu = 0.0 if kind != "gno" else (d**2 / 4 - d**2 / 12) / (rm**2 + d**2 / 12)
            curvE = cart + d**2 / 12 * a * D(lambda r: rho(r) * h(r) * u(r)) + nu * rho(rm) * h(rm) * u(rm)
            curvM = d**2 / 12 * a * D(lambda r: rho(r) * u(r)) + nu * rho(rm) * u(rm)
            hs = cp * P / (Rg * Rh)
            ent = err_E - hs * err_m           # buoyancy-relevant combination
            ent_pred = d**2 / 12 * rho(rm) * D(h) * (D(u) - (0 if kind == "cart" else u(rm) / rm))
            rows.append((kind, i, rm, err_E, err_E - cart, err_E - curvE, err_m, err_m - curvM, ent, ent - ent_pred))
    return rows


def eps_spur(Rb, curved=True, form="base", N=4000):
    """projected eps_spur * nz^2 for the eps=0 column, w = sin(pi z), anelastic D.
    base: scheme lacks the whole term; 'cart': Cartesian dF added; 'exact': curved dF added."""
    T, p, rho, h = bg(Rb)
    z = (np.arange(N) + 0.5) / N
    r = Rb + z if curved else 1e9 + z
    # use the same thermodynamic profile in z for both (only the metric changes)
    Tz, rhoz, hz = T(Rb + z), rho(Rb + z), h(Rb + z)
    w = np.sin(np.pi * z)
    geo = r**2 if curved else np.ones_like(z)
    D = -np.gradient(geo * rhoz * w, z) / (rhoz * geo)
    dD = np.gradient(D, z)
    hr = np.gradient(hz, z)
    # entropy error rate per dz^2 (s' in units of cp): (1/12) (h_r/h) * K
    if form == "base":
        K = dD
    elif form == "cart":       # residual after Cartesian dF: -(h_r/h) D / r
        K = -D / r if curved else 0 * D
    else:
        K = 0 * D
    S = (1 / 12) * hr / hz * K
    loc = Tz * S / w  # local eps_spur / dz^2  (exact: ds'/dt = eps w / T)
    wt = rhoz * w**2 * geo
    proj = (rhoz * w * Tz * S * geo).sum() / wt.sum()
    return proj, loc[N // 2]


if __name__ == "__main__":
    print("(B) eps=0 projected eps_spur * nz^2 (and mid-column local value), w = sin(pi z):")
    for Rb, curved in ((5.0, True), (None, False)):
        for form in ("base", "cart", "exact"):
            pr, mid = eps_spur(Rb if Rb else 5.0, curved, form)
            print(f"   {'R=5H' if curved else 'Cartesian':9s} {form:5s}: projected {pr:+.5f}  mid {mid:+.5f}")
    print("(A) flux test at Rb = 5H, eps = 0; errors divided by dr^2 (exact - scheme):")
    print("   kind  nz cell   r_mid   errE   errE-cartDF  errE-curvDF   errM  errM-curvM   ent  ent-pred")
    for nz in (16, 32, 64):
        cells = [0, nz // 2, nz - 1]
        for row in flux_test(5.0, nz, cells):
            kind, i, rm, eE, eEc, eEx, eM, eMx, ent, entr = row
            d2 = (1.0 / nz) ** 2
            print(f"   {kind:4s} {nz:3d} {i:3d} {rm:.4f} {eE/d2:+.5f} {eEc/d2:+.6f} {eEx/d2:+.2e} {eM/d2:+.5f} {eMx/d2:+.2e} {ent/d2:+.5f} {entr/d2:+.2e}")
