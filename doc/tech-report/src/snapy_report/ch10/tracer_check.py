"""Executable check of the dry-air tracers (chapter 10, _tracer.qmd).

What is checked, at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported line for line below:
- the complement upper bound of ScalarImpl::forward (src/scalar/scalar.cpp:175-198);
- the implicit tracer transfer of MeshBlockImpl::forward (src/mesh/meshblock.cpp:661-676).
Claims C1-C3. The donor side and the telescoping of the transfer are chapter 1's
(src/snapy_report/ch01/stage_check.py, claim C2) and are not repeated here.

Run: python3 tracer_check.py   (numpy and sympy; exits with the number of failed claims)
"""
import sys

import numpy as np
import sympy as sp


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def bound_flux(fs, fm, b, theta):  # scalar.cpp:184-197 for one direction
    g = b * fm - fs
    h = g.copy()
    g = g * theta  # flux_positivity_scale_ on the complement flux
    return fs + (h - g)


def vic_transfer(r, m, vol):  # meshblock.cpp:661-676, x1 last, face i below cell i
    r_below = np.zeros_like(r)
    r_below[1:] = r[:-1]
    p = np.where(m > 0., r_below, r) * m
    p_above = np.zeros_like(p)
    p_above[:-1] = p[1:]
    return (p - p_above) / vol


def check_C1_blend():
    fs, fm, b, th = sp.symbols("F_s F_m b Theta")
    new = fs + ((b * fm - fs) - th * (b * fm - fs))
    resid = sp.simplify(new - (th * fs + (1 - th) * b * fm))
    return report("C1", resid == 0,
                  "limiting the complement blends F_s toward b F_m, the flux of a tracer at the bound",
                  "F_s' - (Theta F_s + (1 - Theta) b F_m) = %s" % resid)


def check_C2_bitwise_where_unlimited():
    rng = np.random.default_rng(7)
    fm = rng.normal(size=10000).astype(np.float32)
    fs = (fm * rng.uniform(0., 1e-3, 10000)).astype(np.float32)
    b = np.float32(0.9)
    added = bound_flux(fs, fm, b, np.float32(1.))
    recomputed = b * fm - (b * fm - fs)  # the form the code comment rejects
    return report("C2", np.array_equal(added, fs) and np.count_nonzero(recomputed != fs) > 0,
                  "adding the change leaves F_s bitwise unchanged where Theta = 1; recomputing would not",
                  "float32, 10000 faces: changed by the code's form %d; by recomputing b F_m - g %d"
                  % (np.count_nonzero(added != fs), np.count_nonzero(recomputed != fs)))


def check_C3_uniform_ratio_moves_with_dry_mass():
    rng = np.random.default_rng(8)
    n = 16
    m = rng.normal(size=n) * 1e-2
    m[0] = 0.  # closed bottom face
    vol = rng.uniform(0.5, 2., n)
    ds = vic_transfer(np.full(n, 0.37), m, vol)
    m_above = np.append(m[1:], 0.)
    dry = (m - m_above) / vol  # the same face transfer applied to unit ratio
    err = np.abs(ds - 0.37 * dry).max() / np.abs(0.37 * dry).max()  # bound: a few ulp of the largest transfer
    return report("C3", err < 1e-15,
                  "a uniform ratio r moves as r times the dry transfer, so r stays uniform",
                  "max |ds - r d(rho_d)| / max |r d(rho_d)| = %.1e" % err)


def main():
    checks = [check_C1_blend, check_C2_bitwise_where_unlimited, check_C3_uniform_ratio_moves_with_dry_mass]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
