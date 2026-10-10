"""Executable check of sedimentation (chapter 10, _sed.qmd).

What is checked: SedVelImpl::forward (src/sedimentation/sed_vel.cpp:34-71) and the donor/sealing rule
sedimentation_upwind (src/sedimentation/sed_hydro_dispatch.hpp:12-24) at
snapy@e894700ff7aee30b52882e5202b16461413780b0, ported line for line below, with the YAML defaults of
src/sedimentation/sed_options.cpp:120-123 and kintera's KBoltz (src/constants.h:9 at
kintera@c55b13b2204997d2d09e04498558ab9495d8ee77). Claims C1-C5.
Also writes data/sed_vsed.csv for fig_sed_vsed.py.

Run: python3 sed_check.py   (numpy only; exits with the number of failed claims)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KBOLTZ = 1.380649e-23  # kintera src/constants.h:9
D, EPS_LJ, M, UPPER = 2.827e-10, 8.24e-22, 3.34e-27, 5.e3  # sed_options.cpp:120-123 (H2 background)


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def vsed(dens, pres, temp, radius, density, grav, const_vsed=0.):  # sed_vel.cpp:34-71
    reduced_temp = KBOLTZ * temp / EPS_LJ
    eta = (5.0 / 16.0) * np.sqrt(M * KBOLTZ / np.pi) * np.sqrt(temp) * reduced_temp**0.16 / (D * D * 1.22)
    lam = eta / pres * np.sqrt(np.pi * KBOLTZ * temp / (2.0 * M))
    kn = lam / radius
    beta = 1.0 + kn * (1.256 + 0.4 * np.exp(-1.1 / kn))
    stokes = beta / (9.0 * eta) * (2.0 * radius**2 * grav * (density - dens))
    vel = np.where(const_vsed != 0.0, const_vsed, stokes)
    return np.clip(vel, -UPPER, UPPER), beta, eta


def upwind(q, v, il, iu):  # sed_hydro_dispatch.hpp:12-24; face i lies between cells i-1 and i
    face = np.where(v < 0., q, 0.)
    face[1:] += np.where(v > 0., q, 0.)[:-1]
    face[iu + 1:] = 0.
    face[:il + 1] = 0.
    return face


def check_C1_sign():
    v, _, _ = vsed(0.1, 1e4, 150., 1e-5, 1000., -24.79)
    return report("C1", v < 0., "with g_1 < 0 and a particle denser than the gas the velocity is negative (settling)",
                  "w_s = %.4e m s^-1 at p = 1e4 Pa, T = 150 K, a = 10 um, rho_p = 1000 kg m^-3, g_1 = -24.79" % v)


def check_C2_cunningham_limits():
    _, b_small, _ = vsed(0.1, 1e7, 150., 1e-3, 1000., -24.79)  # continuum: Kn << 1
    _, b_large, _ = vsed(0.1, 1e-1, 150., 1e-8, 1000., -24.79)  # free molecular: Kn >> 1
    eta = vsed(0.1, 1e-1, 150., 1e-8, 1000., -24.79)[2]
    lam = eta / 1e-1 * np.sqrt(np.pi * KBOLTZ * 150. / (2.0 * M))
    kn = lam / 1e-8
    ok = abs(b_small - 1.) < 1e-3 and abs(b_large / kn - 1.656) < 1e-3
    return report("C2", ok, "the slip factor tends to 1 in the continuum and to 1.656 Kn in the free-molecular limit",
                  "beta - 1 = %.2e at Kn << 1; beta/Kn = %.5f at Kn = %.3e" % (b_small - 1., b_large / kn, kn))


def check_C3_viscosity_pressure_free():
    _, _, e1 = vsed(0.1, 1e3, 200., 1e-5, 1000., -10.)
    _, _, e2 = vsed(0.1, 1e6, 200., 1e-5, 1000., -10.)
    return report("C3", e1 == e2, "the Chapman-Enskog viscosity depends on T only, not on p",
                  "mu(200 K) = %.6e Pa s at 1e3 and 1e6 Pa" % e1)


def check_C4_clamp_and_prescribed():
    v_big, _, _ = vsed(1e-6, 1e-2, 150., 1e-2, 3000., -24.79)
    v_c, _, _ = vsed(0.1, 1e4, 150., 1e-5, 1000., -24.79, const_vsed=-2.)
    ok = v_big == -UPPER and v_c == -2.
    return report("C4", ok, "the velocity is clamped to +-upper-limit, and a non-zero const-vsed replaces it",
                  "clamped %.1f m s^-1 (upper-limit 5e3); const-vsed -2 gives %.1f" % (v_big, v_c))


def check_C5_sealed_column_conserves():
    rng = np.random.default_rng(5)
    n, il, iu = 12, 2, 9  # ghosts 0-2 and 10-11 around interior cells 3..9
    q = rng.uniform(0., 1., n)
    v = rng.choice([-1., 1.], n)
    face = upwind(q, v, il, iu)
    div = face[1:] - face[:-1]  # cell i gets face[i+1] - face[i] (a flux of the signed velocity)
    interior_sum = div[il + 1:iu + 1].sum()
    sealed = face[il + 1] == 0. and face[iu + 1] == 0.
    radii = np.logspace(-7, -3, 41)
    rows = [radii]
    for p in (1e4, 1e6):
        rows.append(vsed(0.1, p, 150., radii, 1000., -24.79)[0])
        rows.append(-2. * radii**2 * 24.79 * (1000. - 0.1) / (9. * vsed(0.1, p, 150., radii, 1000., -24.79)[2]))
    np.savetxt(os.path.join(HERE, "data", "sed_vsed.csv"), np.column_stack(rows), delimiter=",", fmt="%.10e",
               header="radius [m], w_s(1e4 Pa), Stokes(1e4 Pa), w_s(1e6 Pa), Stokes(1e6 Pa) [m s^-1]; "
                      "T = 150 K, rho = 0.1, rho_p = 1000 kg m^-3, g_1 = -24.79, H2 defaults")
    return report("C5", sealed and abs(interior_sum) < 1e-15,
                  "with both physical walls sealed the interior flux divergence sums to zero",
                  "wall faces %.1f and %.1f; interior sum of face differences %.1e"
                  % (face[il + 1], face[iu + 1], interior_sum))


def main():
    checks = [check_C1_sign, check_C2_cunningham_limits, check_C3_viscosity_pressure_free,
              check_C4_clamp_and_prescribed, check_C5_sealed_column_conserves]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
