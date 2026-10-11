"""Executable check of the cycle-line budget (chapter 13, _cycle.qmd).

What is checked: print_cycle_diagnostics (src/mesh/meshblock.cpp:1004-1112), the metric raise it calls
(coord_vec_raise_impl, src/coord/coord_utils_impl.h:9-16) and the two callers (meshblock.cpp:1114-1119,
src/mesh/mesh.cpp:409-420) at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported to numpy on small blocks.
Claims C1-C5.

Run: python3 cycle_check.py   (numpy only; exits with the number of failed claims)
"""
import sys

import numpy as np


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


IDN, IVX, IVY, IVZ, IPR, ICY = 0, 1, 2, 3, 4, 5


def raise_(m2, m3, cth):
    """coord_vec_raise_impl: contravariant components from covariant ones with cos(theta) between x2 and x3."""
    s2 = 1. - cth * cth
    return m2 / s2 - m3 * cth / s2, -m2 * cth / s2 + m3 / s2


def block_sums(u, vol, cth, grav1, x1v):
    """One block's contribution: conserved sums, ke and pe (meshblock.cpp:1035-1056, no radial-exact switch)."""
    rho = u[IDN] + u[ICY:].sum(0)
    m1, m2, m3 = u[IVX], u[IVY], u[IVZ]
    r2, r3 = raise_(m2, m3, cth)
    ke = 0.5 * (m1 * m1 + m2 * r2 + m3 * r3) / rho
    pe = rho * (-grav1 * x1v)
    return (u * vol).sum(axis=(1, 2, 3)), (ke * vol).sum(), (pe * vol).sum()


def uniform(nvar, shape, rho_d, ys, m, e):
    u = np.zeros((nvar,) + shape)
    u[IDN] = rho_d
    for n, y in enumerate(ys):
        u[ICY + n] = y
    u[IVX], u[IVY], u[IVZ] = m
    u[IPR] = e
    return u


SHAPE = (1, 2, 3)
VOL = np.full(SHAPE, 0.5)
X1V = np.broadcast_to(np.array([0.5, 1.5, 2.5]), SHAPE)


def check_C1_ke_contracts_with_the_metric():
    u = uniform(7, SHAPE, 2.5, (0., 0.), (0., 3., 4.), 1e5)
    _, flat, _ = block_sums(u, VOL, 0., 0., X1V)
    _, skew, _ = block_sums(u, VOL, 0.5, 0., X1V)
    ok = abs(skew / flat - 13. / 18.75) < 1e-14
    return report("C1", ok, "ke = 1/2 m_i m^i / rho with the momentum raised; c = 0.5, (m2, m3) = (3, 4) gives 13/0.75 "
                  "against 25 flat", "ratio %.15f, expected %.15f" % (skew / flat, 13. / 18.75))


def check_C2_density_is_the_total():
    u_t = uniform(7, SHAPE, 2.5, (0., 0.), (7.5, 0., 0.), 1e5)
    u_m = uniform(7, SHAPE, 2.0, (0.25, 0.25), (7.5, 0., 0.), 1e5)
    u_d = uniform(5, SHAPE, 2.0, (), (7.5, 0., 0.), 1e5)
    kt, km, kd = (block_sums(u, VOL, 0., -10., X1V)[1] for u in (u_t, u_m, u_d))
    pt, pm = (block_sums(u, VOL, 0., -10., X1V)[2] for u in (u_t, u_m))
    ok = abs(km / kt - 1.) < 1e-14 and abs(kd / kt - 1.25) < 1e-14 and abs(pm / pt - 1.) < 1e-14
    return report("C2", ok, "ke and pe weigh the total density (dry plus every species): moving 0.5 of 2.5 into species "
                  "changes nothing, dropping it gives 1.25 times the ke", "ke mixed/total %.15f, dry-only/total %.15f, pe mixed/total %.15f"
                  % (km / kt, kd / kt, pm / pt))


def check_C3_pe_is_the_geopotential_integral():
    u = uniform(7, SHAPE, 2.5, (0., 0.), (0., 0., 0.), 1e5)
    _, _, pe = block_sums(u, VOL, 0., -10., X1V)
    want = 2.5 * 10. * (X1V * VOL).sum()
    return report("C3", abs(pe - want) < 1e-12 * want, "pe = sum rho (-g1 x1v) V; g1 = -10, rho = 2.5",
                  "pe %.12g, 2.5 * 10 * sum z V = %.12g" % (pe, want))


def check_C4_local_sums_then_one_reduction():
    rng = np.random.default_rng(1)
    u = rng.uniform(0.5, 2., (7, 1, 4, 12))
    vol = rng.uniform(0.5, 1.5, (1, 4, 12))
    x1v = np.broadcast_to(np.linspace(0.5, 11.5, 12), (1, 4, 12))
    whole = block_sums(u, vol, 0.3, -9.8, x1v)
    parts = [block_sums(u[..., s], vol[..., s], 0.3, -9.8, x1v[..., s]) for s in (slice(0, 3), slice(3, 6),
                                                                              slice(6, 9), slice(9, 12))]
    errs = [np.abs(sum(p[k] for p in parts) - whole[k]).max() / np.abs(whole[k]).max() for k in range(3)]
    ok = max(errs) < 1e-14
    return report("C4", ok, "four blocks summed locally and then reduced once give the whole-domain sums", "relative differences: conserved %.1e, ke %.1e, pe %.1e"
                  % tuple(errs))


def check_C5_precision_of_the_two_lines():
    md10 = 17                      # std::numeric_limits<double>::max_digits10
    s_block = "%.*e" % (md10 - 4, 1. / 3.)
    s_mesh = "%.*e" % (md10 - 3, 1. / 3.)
    ok = len(s_block.split("e")[0].split(".")[1]) == 13 and len(s_mesh.split("e")[0].split(".")[1]) == 14
    return report("C5", ok, "the MeshBlock line prints max_digits10 - 4 = 13 decimals with ie=, the Mesh line "
                  "max_digits10 - 3 = 14 with energy=", "%s vs %s" % (s_block, s_mesh))


def main():
    checks = [check_C1_ke_contracts_with_the_metric, check_C2_density_is_the_total,
              check_C3_pe_is_the_geopotential_integral, check_C4_local_sums_then_one_reduction,
              check_C5_precision_of_the_two_lines]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
