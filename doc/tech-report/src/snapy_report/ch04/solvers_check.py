"""Executable check of the HLLC, Roe and shallow-water Roe solvers (chapter 4, _hllc.qmd, _roe.qmd, _shallow.qmd).

What is checked: hllc_impl (src/riemann/hllc_impl.h:16-130), roe_impl (src/riemann/roe_impl.h:23-211) and
shallow_roe_impl (src/riemann/shallow_roe_impl.h:14-72, with shallow_water_roe_sound_speed of
src/eos/shallow_water_impl.h:18-20) at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported line for line for a
dry ideal gas (ny = 0, not ideal-moist) in the x1 direction (dim = 3, so ivx = IVX). el and er are the internal
energy densities the dispatch passes (peos "W->I", src/riemann/hllc.cpp:36). Claims C1-C6.

Run: python3 solvers_check.py   (numpy only; exits with the number of failed claims)
"""
import sys

import numpy as np


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


IDN, IVX, IVY, IVZ, IPR = 0, 1, 2, 3, 4
G = 1.4


def physical(w):
    rho, u, v, ww, p = w
    E = p / (G - 1) + 0.5 * rho * (u * u + v * v + ww * ww)
    return np.array([rho * u, rho * u * u + p, rho * u * v, rho * u * ww, (E + p) * u])


def cons(w):
    rho, u, v, ww, p = w
    return np.array([rho, rho * u, rho * v, rho * ww, p / (G - 1) + 0.5 * rho * (u * u + v * v + ww * ww)])


def snd(w):
    return np.sqrt(G * w[IPR] / w[IDN])


def hllc(wl, wr):
    """hllc_impl.h:16-130, ny = 0."""
    tiny = 1e-10
    el = wl[IPR] / (G - 1) + 0.5 * wl[IDN] * (wl[1] ** 2 + wl[2] ** 2 + wl[3] ** 2)
    er = wr[IPR] / (G - 1) + 0.5 * wr[IDN] * (wr[1] ** 2 + wr[2] ** 2 + wr[3] ** 2)
    cl, cr = snd(wl), snd(wr)
    rhoa, ca = .5 * (wl[IDN] + wr[IDN]), .5 * (cl + cr)
    pmid = .5 * (wl[IPR] + wr[IPR] + (wl[IVX] - wr[IVX]) * rhoa * ca)
    ql = 1. if pmid <= wl[IPR] else np.sqrt(1. + (G + 1) / (2 * G) * (pmid / wl[IPR] - 1.))
    qr = 1. if pmid <= wr[IPR] else np.sqrt(1. + (G + 1) / (2 * G) * (pmid / wr[IPR] - 1.))
    al, ar = wl[IVX] - cl * ql, wr[IVX] + cr * qr
    bp = ar if ar > 0. else tiny
    bm = al if al < 0. else -tiny
    vxl, vxr = wl[IVX] - al, wr[IVX] - ar
    tl = wl[IPR] + vxl * wl[IDN] * wl[IVX]
    tr = wr[IPR] + vxr * wr[IDN] * wr[IVX]
    ml, mr = wl[IDN] * vxl, -(wr[IDN] * vxr)
    am = (tl - tr) / (ml + mr)
    cp = max((ml * tr + mr * tl) / (ml + mr), 0.)
    vxl, vxr = wl[IVX] - bm, wr[IVX] - bp
    fl = np.array([wl[IDN] * vxl, wl[IDN] * wl[IVX] * vxl + wl[IPR], wl[IDN] * wl[IVY] * vxl,
                   wl[IDN] * wl[IVZ] * vxl, el * vxl + wl[IPR] * wl[IVX]])
    fr = np.array([wr[IDN] * vxr, wr[IDN] * wr[IVX] * vxr + wr[IPR], wr[IDN] * wr[IVY] * vxr,
                   wr[IDN] * wr[IVZ] * vxr, er * vxr + wr[IPR] * wr[IVX]])
    if am >= 0.:
        sl, sr, sm = am / (am - bm), 0., -bm / (am - bm)
    else:
        sl, sr, sm = 0., -am / (bp - am), bp / (bp - am)
    f = sl * fl + sr * fr
    f[IVX] += sm * cp
    f[IPR] += sm * cp * am
    return f


def roe(wl, wr, override=True):
    """roe_impl.h:23-211, ny = 0, not ideal-moist; override=False skips the supersonic branches :176-195."""
    tiny = 1e-10
    etl = wl[IPR] / (G - 1) + 0.5 * wl[IDN] * (wl[1] ** 2 + wl[2] ** 2 + wl[3] ** 2)
    etr = wr[IPR] / (G - 1) + 0.5 * wr[IDN] * (wr[1] ** 2 + wr[2] ** 2 + wr[3] ** 2)
    sl, sr = np.sqrt(wl[IDN]), np.sqrt(wr[IDN])
    isd = 1. / (sl + sr)
    rhobar = sl * sr
    v1, v2, v3 = ((sl * wl[k] + sr * wr[k]) * isd for k in (IVX, IVY, IVZ))
    hl, hr = (etl + wl[IPR]) / wl[IDN], (etr + wr[IPR]) / wr[IDN]
    h = (hl * sl + hr * sr) * isd
    rhol0, rhor0 = wl[IDN], wr[IDN]
    fl, fr = physical(wl), physical(wr)
    qbar0 = (rhol0 / sl + rhor0 / sr) * isd
    f = 0.5 * (fl + fr)
    gm1 = G - 1
    q = h - 0.5 * (v1 * v1 + v2 * v2 + v3 * v3)
    cs2 = max(gm1 * max(q, tiny), tiny)
    cs = np.sqrt(cs2)
    spd_m, spd_0, spd_p = abs(v1 - cs), abs(v1), abs(v1 + cs)
    du, dv, dw, dp = (wr[k] - wl[k] for k in (IVX, IVY, IVZ, IPR))
    am_ = -0.5 * rhobar / cs * du + 0.5 * dp / cs2
    ap_ = +0.5 * rhobar / cs * du + 0.5 * dp / cs2
    av, aw = rhobar * dv, rhobar * dw
    a0 = rhor0 - rhol0 - dp / cs2 * qbar0
    llf = rhol0 + am_ * qbar0 < 0 or rhol0 + am_ * qbar0 + a0 < 0
    f[IDN] -= 0.5 * (spd_m * am_ * qbar0 + spd_0 * a0 + spd_p * ap_ * qbar0)
    f[IVX] -= 0.5 * (spd_m * am_ * (v1 - cs) + spd_0 * (v1 * a0) + spd_p * ap_ * (v1 + cs))
    f[IVY] -= 0.5 * (spd_m * am_ * v2 + spd_0 * (v2 * a0 + av) + spd_p * ap_ * v2)
    f[IVZ] -= 0.5 * (spd_m * am_ * v3 + spd_0 * (v3 * a0 + aw) + spd_p * ap_ * v3)
    f[IPR] -= 0.5 * (spd_m * am_ * (h - v1 * cs) + spd_0 * (rhobar * (hr - hl - v1 * du) + a0 * h - dp)
                     + spd_p * ap_ * (h + v1 * cs))
    if override:
        if v1 - cs > 0:
            f = fl.copy()
        if v1 + cs < 0:
            f = fr.copy()
    assert not llf
    return f


def shallow(wl, wr):
    """shallow_roe_impl.h:14-72 with dir_yz = 0, dim = 3: rows (h, h u, h v)."""
    sl, sr = np.sqrt(wl[0]), np.sqrt(wr[0])
    isd = 1. / (sl + sr)
    ub, vb = (wl[1] * sl + wr[1] * sr) * isd, (wl[2] * sl + wr[2] * sr) * isd
    cb = np.sqrt(0.5 * (wl[0] + wr[0]))
    d0, dx, dy = wr[0] - wl[0], wr[1] - wl[1], wr[2] - wl[2]
    hb = np.sqrt(wl[0] * wr[0])
    a1 = 0.5 * (cb * d0 - hb * dx) / cb
    a2 = hb * dy
    a3 = 0.5 * (cb * d0 + hb * dx) / cb
    waves = [a1 * np.array([1., ub - cb, vb]), a2 * np.array([0., 0., 1.]), a3 * np.array([1., ub + cb, vb])]
    speeds = [abs(ub - cb), abs(ub), abs(ub + cb)]
    f = 0.5 * (sw_flux(wl) + sw_flux(wr))
    for s, wv in zip(speeds, waves):
        f -= 0.5 * s * wv
    return f


def sw_flux(w):
    h, u, v = w
    return np.array([h * u, h * u * u + 0.5 * h * h, h * u * v])


rng = np.random.default_rng(4)


def rand_state(umax=50.):
    return np.array([rng.uniform(0.3, 2.), *rng.uniform(-umax, umax, 3), rng.uniform(5e4, 2e5)])


def check_C1_hllc_consistent():
    worst = 0.
    for _ in range(200):
        w = rand_state()
        f = physical(w)
        worst = max(worst, np.abs(hllc(w, w.copy()) - f).max() / np.abs(f).max())
    return report("C1", worst < 1e-13, "HLLC is consistent: equal left and right states give the physical flux",
                  "max relative error over 200 states %.1e" % worst)


def check_C2_hllc_resolves_a_contact():
    worst = 0.
    for u in (0., 30., -30.):
        wl = np.array([1.2, u, 5., -3., 1e5])
        wr = np.array([0.4, u, 5., -3., 1e5])
        f = hllc(wl, wr)
        exact = physical(wl) if u >= 0 else physical(wr)
        if u == 0.:
            exact = np.array([0., 1e5, 0., 0., 0.])
        worst = max(worst, np.abs(f - exact).max() / np.abs(exact).max())
    return report("C2", worst < 1e-13, "HLLC resolves an isolated contact (equal p and u, a density jump of 3) exactly: "
                  "at rest, moving right and moving left", "max relative error %.1e" % worst)


def check_C3_roe_consistent():
    worst = 0.
    for _ in range(200):
        w = rand_state()
        f = physical(w)
        worst = max(worst, np.abs(roe(w, w.copy()) - f).max() / np.abs(f).max())
    return report("C3", worst < 1e-13, "Roe is consistent: equal states give the physical flux",
                  "max relative error over 200 states %.1e" % worst)


def check_C4_roe_property():
    worst = n = 0
    while n < 200:
        wl, wr = rand_state(30.), rand_state(30.)
        wl[IVX] += 800.
        wr[IVX] += 800.
        f = roe(wl, wr, override=False)            # the decomposition alone, without the supersonic branch
        worst = max(worst, np.abs(f - physical(wl)).max() / np.abs(physical(wl)).max())
        n += 1
    return report("C4", worst < 1e-11, "the characteristic decomposition reproduces the flux jump: with every wave "
                  "moving right the decomposed flux, before the supersonic branch, is the left physical flux",
                  "max relative difference over 200 random pairs %.1e" % worst)


def check_C5_roe_stationary_contact():
    wl = np.array([1.2, 0., 5., -3., 1e5])
    wr = np.array([0.4, 0., 5., -3., 1e5])
    f = roe(wl, wr)
    exact = np.array([0., 1e5, 0., 0., 0.])
    err = np.abs(f - exact).max() / 1e5
    return report("C5", err < 1e-13, "Roe holds a stationary contact exactly: zero mass and energy flux, momentum flux p",
                  "max relative error %.1e" % err)


def check_C6_shallow_roe():
    worst_c = worst_r = 0.
    for _ in range(200):
        w = np.array([rng.uniform(0.5, 2.), *rng.uniform(-1., 1., 2)])
        worst_c = max(worst_c, np.abs(shallow(w, w.copy()) - sw_flux(w)).max())
        wl = np.array([rng.uniform(0.5, 1.), rng.uniform(3., 4.), rng.uniform(-1., 1.)])
        wr = np.array([rng.uniform(0.5, 1.), rng.uniform(3., 4.), rng.uniform(-1., 1.)])
        worst_r = max(worst_r, np.abs(shallow(wl, wr) - sw_flux(wl)).max() / np.abs(sw_flux(wl)).max())
    ok = worst_c < 1e-14 and worst_r < 1e-13
    return report("C6", ok, "shallow-roe is consistent, and with every wave moving right it returns the left flux, "
                  "so its decomposition reproduces the jump", "max errors %.1e (equal states), %.1e (supercritical)"
                  % (worst_c, worst_r))


def main():
    checks = [check_C1_hllc_consistent, check_C2_hllc_resolves_a_contact, check_C3_roe_consistent,
              check_C4_roe_property, check_C5_roe_stationary_contact, check_C6_shallow_roe]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
