"""Executable check of the stage operator, the geometry and the Riemann fluxes
(chapter 4, _divergence.qmd, _sphsrc.qmd, _gnomonic.qmd, _riemann.qmd, _lmars.qmd).

Ports of snapy@e894700ff7aee30b52882e5202b16461413780b0: CoordinateImpl::divergence
(src/coord/coordinate.cpp:509-553), the spherical-polar areas and volume
(src/coord/spherical_polar.cpp:178-211), lmars_impl (src/riemann/lmars_impl.h:17-78)
and the face-local index map at :20-22. Claims C1-C8.

Run: python3 operator_check.py   (numpy and sympy; exits with the number of failed claims)
"""
import sys

import numpy as np
import sympy as sp

FAIL = []
IDN, IVX, IVY, IVZ, IPR = 0, 1, 2, 3, 4
ICY = 5


def report(tag, ok, what, detail):
    print(f"[{tag}] {'PASS' if ok else 'FAIL'} {what}: {detail}")
    if not ok:
        FAIL.append(tag)


# --- the spherical-polar metric, exactly as the code builds it ---
def sph_geometry(r, th, ph):
    """face_area1 :178-183, face_area2 :185-191, face_area3 :193-198, cell_volume :200-211"""
    dph = np.diff(ph)
    a1 = r[:, None, None] ** 2 * np.abs(np.cos(th[None, :-1, None])
                                        - np.cos(th[None, 1:, None])) * dph[None, None, :]
    rad = 0.5 * (r[1:] ** 2 - r[:-1] ** 2)
    a2 = rad[:, None, None] * np.abs(np.sin(th[None, :, None])) * dph[None, None, :]
    # an x3 face exists at every phi face, so the last axis is nph + 1 long (:193-198)
    a3 = (rad[:, None, None] * np.diff(th)[None, :, None]
          * np.ones(len(ph))[None, None, :])
    vol = ((r[1:] ** 3 - r[:-1] ** 3) / 3.)[:, None, None] \
        * np.abs(np.cos(th[:-1]) - np.cos(th[1:]))[None, :, None] * dph[None, None, :]
    return a1, a2, a3, vol


def divergence(f1, f2, f3, a1, a2, a3, vol):
    """coordinate.cpp:509-553, one block, all cells interior"""
    d = np.zeros_like(vol)
    d += a1[1:] * f1[1:] - a1[:-1] * f1[:-1]
    d += a2[:, 1:] * f2[:, 1:] - a2[:, :-1] * f2[:, :-1]
    d += a3[:, :, 1:] * f3[:, :, 1:] - a3[:, :, :-1] * f3[:, :, :-1]
    return d / vol


def _grid(nr=6, nt=5, npz=4, r0=2.0, r1=3.0):
    r = np.linspace(r0, r1, nr + 1)
    th = np.linspace(0.3, np.pi - 0.3, nt + 1)
    ph = np.linspace(0.0, 1.1, npz + 1)
    return r, th, ph


# --- C1: a uniform Cartesian state keeps an exactly zero tendency ---
def check_C1():
    """On a Cartesian block every face area in a direction is the same, so a flux that does
    not vary telescopes to exactly zero: the operator preserves a constant state bitwise."""
    nx, ny_, nz = 5, 4, 3
    h1, h2, h3 = 0.3, 0.7, 1.1
    a1 = np.full((nx + 1, ny_, nz), h2 * h3)
    a2 = np.full((nx, ny_ + 1, nz), h1 * h3)
    a3 = np.full((nx, ny_, nz + 1), h1 * h2)
    vol = np.full((nx, ny_, nz), h1 * h2 * h3)
    f1 = np.full((nx + 1, ny_, nz), 2.5)
    f2 = np.full((nx, ny_ + 1, nz), -1.25)
    f3 = np.full((nx, ny_, nz + 1), 0.75)
    d = divergence(f1, f2, f3, a1, a2, a3, vol)
    report("C1", np.max(np.abs(d)) == 0.,
           "a uniform flux on a Cartesian block gives a bitwise zero tendency",
           f"max |div| = {np.max(np.abs(d)):.1e} over {nx}x{ny_}x{nz} cells; the equal face "
           f"areas make the two terms of each direction cancel exactly, not just to round-off")


# --- C2: div(r rhat) = 3 exactly ---
def check_C2():
    r, th, ph = _grid()
    a1, a2, a3, vol = sph_geometry(r, th, ph)
    f1 = np.broadcast_to(r[:, None, None], (len(r), len(th) - 1, len(ph) - 1)).copy()
    f2 = np.zeros((len(r) - 1, len(th), len(ph) - 1))
    f3 = np.zeros((len(r) - 1, len(th) - 1, len(ph)))
    d = divergence(f1, f2, f3, a1, a2, a3, vol)
    err = np.max(np.abs(d - 3.))
    report("C2", err < 1e-12,
           "the spherical-polar areas and volume give div(r rhat) = 3 to round-off",
           f"max |div - 3| = {err:.2e} over a {len(r)-1}x{len(th)-1}x{len(ph)-1} block "
           f"(this is the identity tests/test_cubed_sphere_cell_volume.py asserts per cell)")


# --- C3: the volume is the exact radial integral, not r^2 dr ---
def check_C3():
    r = sp.symbols("r", positive=True)
    h = sp.symbols("h", positive=True)
    exact = sp.integrate(r ** 2, (r, r - h / 2, r + h / 2))
    midpoint = r ** 2 * h
    diff = sp.simplify(sp.expand(exact - midpoint))
    report("C3", sp.simplify(diff - h ** 3 / 12) == 0,
           "the cell volume uses the exact radial integral (r_+^3 - r_-^3)/3, not r^2 dr",
           f"exact minus midpoint = {diff}, so the midpoint form would be short by "
           f"h^3/12 per unit solid angle")


# --- C4: the divergence telescopes over the block ---
def check_C4():
    rng = np.random.default_rng(4)
    r, th, ph = _grid()
    a1, a2, a3, vol = sph_geometry(r, th, ph)
    f1 = rng.normal(size=(len(r), len(th) - 1, len(ph) - 1))
    f2 = rng.normal(size=(len(r) - 1, len(th), len(ph) - 1))
    f3 = rng.normal(size=(len(r) - 1, len(th) - 1, len(ph)))
    d = divergence(f1, f2, f3, a1, a2, a3, vol)
    bulk = (d * vol).sum()
    bdry = (a1[-1] * f1[-1]).sum() - (a1[0] * f1[0]).sum() \
        + (a2[:, -1] * f2[:, -1]).sum() - (a2[:, 0] * f2[:, 0]).sum() \
        + (a3[:, :, -1] * f3[:, :, -1]).sum() - (a3[:, :, 0] * f3[:, :, 0]).sum()
    rel = abs(bulk - bdry) / max(1e-30, abs(bdry))
    report("C4", rel < 1e-13,
           "sum of V times the divergence equals the net flux through the block boundary",
           f"relative difference {rel:.2e} on random face fluxes, so the operator is in "
           f"flux form and conserves by construction")


# --- the LMARS port ---
def lmars(wl, wr, hl, hr, gl, gr, ny=0):
    """lmars_impl.h:17-78, dim = 1 so ivx = IVX"""
    hl = hl + 0.5 * (wl[IVX] ** 2 + wl[IVY] ** 2 + wl[IVZ] ** 2) + wl[IPR] / wl[IDN]
    hr = hr + 0.5 * (wr[IVX] ** 2 + wr[IVY] ** 2 + wr[IVZ] ** 2) + wr[IPR] / wr[IDN]
    rhobar = 0.5 * (wl[IDN] + wr[IDN])
    gbar = 0.5 * (gl + gr)
    cbar = np.sqrt(0.5 * gbar * (wl[IPR] + wr[IPR]) / rhobar)
    pbar = 0.5 * (wl[IPR] + wr[IPR]) + 0.5 * (rhobar * cbar) * (wl[IVX] - wr[IVX])
    ubar = 0.5 * (wl[IVX] + wr[IVX]) + 0.5 / (rhobar * cbar) * (wl[IPR] - wr[IPR])
    flx = np.zeros(5 + ny)
    src, h = (wl, hl) if ubar > 0. else (wr, hr)
    rd = 1.0 - sum(src[ICY + n] for n in range(ny))
    flx[IDN] = ubar * src[IDN] * rd
    for n in range(ny):
        flx[ICY + n] = ubar * src[IDN] * src[ICY + n]
    flx[IVX] = ubar * src[IDN] * src[IVX] + pbar
    flx[IVY] = ubar * src[IDN] * src[IVY]
    flx[IVZ] = ubar * src[IDN] * src[IVZ]
    flx[IPR] = ubar * src[IDN] * h
    return flx, pbar, ubar


# --- C5: a uniform state gives the exact physical flux ---
def check_C5():
    g = 1.4
    w = np.array([1.3, 0.7, -0.2, 0.4, 2.1])
    e = w[IPR] / (g - 1.)
    hint = e / w[IDN]
    flx, pbar, ubar = lmars(w, w, hint, hint, g, g)
    H = (e + w[IPR]) / w[IDN] + 0.5 * (w[IVX] ** 2 + w[IVY] ** 2 + w[IVZ] ** 2)
    want = np.array([w[IDN] * w[IVX],
                     w[IDN] * w[IVX] ** 2 + w[IPR],
                     w[IDN] * w[IVX] * w[IVY],
                     w[IDN] * w[IVX] * w[IVZ],
                     w[IDN] * w[IVX] * H])
    err = np.max(np.abs(flx - want))
    report("C5", err < 1e-13 and abs(pbar - w[IPR]) < 1e-14 and abs(ubar - w[IVX]) < 1e-14,
           "lmars is consistent: equal left and right states give the exact physical flux",
           f"max |flux - exact| = {err:.1e}; pbar = p and ubar = u exactly "
           f"(the jump terms carry (u_l - u_r) and (p_l - p_r))")


# --- C6: the acoustic structure of the face state ---
def check_C6():
    g = 1.4
    wl = np.array([1.0, 0.0, 0., 0., 1.0])
    wr = np.array([1.0, 0.0, 0., 0., 1.2])
    _, pbar, ubar = lmars(wl, wr, 1., 1., g, g)
    rhobar = 1.0
    cbar = np.sqrt(0.5 * g * (wl[IPR] + wr[IPR]) / rhobar)
    ok_u = abs(ubar - (0.5 / (rhobar * cbar)) * (wl[IPR] - wr[IPR])) < 1e-14
    wl2 = np.array([1.0, 0.3, 0., 0., 1.0])
    wr2 = np.array([1.0, -0.3, 0., 0., 1.0])
    _, pbar2, ubar2 = lmars(wl2, wr2, 1., 1., g, g)
    ok_p = abs(pbar2 - (1.0 + 0.5 * rhobar * np.sqrt(g) * 0.6)) < 1e-12
    report("C6", ok_u and ok_p,
           "the face velocity carries the pressure jump over rho c, and the face pressure "
           "carries the velocity jump times rho c",
           f"a pure pressure jump of 0.2 drives ubar = {ubar:.6f}; two states converging at "
           f"0.3 raise pbar to {pbar2:.6f} above the mean 1.0")


# --- C7: the species rows and the dry row sum to the total mass flux ---
def check_C7():
    g = 1.4
    ny = 3
    rng = np.random.default_rng(7)
    y = rng.uniform(0.02, 0.15, ny)
    wl = np.concatenate([[1.2, 0.5, 0.1, -0.1, 2.0], y])
    wr = np.concatenate([[0.9, 0.45, 0.1, -0.1, 1.7], y * 1.1])
    flx, _, ubar = lmars(wl, wr, 1.5, 1.6, g, g, ny=ny)
    src = wl if ubar > 0 else wr
    total = flx[IDN] + sum(flx[ICY + n] for n in range(ny))
    want = ubar * src[IDN]
    report("C7", abs(total - want) < 1e-14,
           "the dry row plus every species row is the total mass flux",
           f"|sum of mass rows - ubar rho| = {abs(total - want):.1e}; the dry row carries "
           f"rd = 1 - sum(y) so the split is exact with {ny} species")


# --- C8: the face-local index map ---
def check_C8():
    rows = []
    ok = True
    for dim in (1, 2, 3):
        ivx = IPR - dim
        ivy = IVX + ((ivx - IVX) + 1) % 3
        ivz = IVX + ((ivx - IVX) + 2) % 3
        ok &= sorted([ivx, ivy, ivz]) == [IVX, IVY, IVZ]
        rows.append(f"dim {dim}: normal row {ivx}, tangential {ivy} and {ivz}")
    report("C8", ok,
           "ivx = IPR - dim rotates the three momentum rows into the face-local frame",
           "; ".join(rows) + " -- a permutation of the momentum rows for every direction")


for fn in (check_C1, check_C2, check_C3, check_C4, check_C5, check_C6, check_C7, check_C8):
    fn()
print(f"{8 - len(FAIL)}/8 claims pass")
sys.exit(len(FAIL))
