"""Check Chapter 1 stage algebra without snapy.

Formula pin: snapy@e894700ff7aee30b52882e5202b16461413780b0.
Run: python3 stage_check.py from any working directory.
C1 checks the coefficient product in src/hydro/hydro_forward.cpp:985-995.
C2 mirrors the upwind/shift/difference in src/mesh/meshblock.cpp:663-675.
C3 checks src/mesh/meshblock.cpp:633-645, including its zero-base fallback.
These are symbolic identities and numpy formula checks, not C++ runtime tests.
All cited ranges are at the full formula pin above.
"""
import numpy as np
import sympy as sp


def check_C1_weights():
    a = sp.symbols('a0:3')
    b = sp.symbols('b0:3')
    c = sp.symbols('c0:3')
    d = sp.symbols('d0:3')
    initial = sp.Symbol('initial')
    state = initial
    for stage in range(3):
        state = a[stage]*initial + b[stage]*state + c[stage]*d[stage]
    residuals = [sp.simplify(sp.diff(state, d[s])-c[s]*sp.prod(b[s+1:])) for s in range(3)]
    ok = all(r == 0 for r in residuals)
    print(f"[C1] {'PASS' if ok else 'FAIL'} supplied-stage coefficients: residuals={residuals}")
    return ok


def check_C2_transfer():
    # Exact code operation sequence: shift ratio below, upwind by sign, shift
    # transfer above, subtract and divide by volume. Last slot is a guard.
    ratio = np.array([0.2, 0.7, 0.3, 0.9, 0.4], dtype=np.float64)
    volume = np.array([1., 2., 3., 4., 1.])
    residuals = []
    tolerances = []
    for mass in (np.array([0., 0.4, -0.2, 0.1, 0.]),
                 np.array([-0.3, 0.4, -0.2, 0.1, 0.5])):
        below = np.zeros_like(ratio)
        below[1:] = ratio[:-1]
        transfer = np.where(mass > 0., below, ratio) * mass
        above = np.zeros_like(transfer)
        above[:-1] = transfer[1:]
        increment = (transfer-above)/volume
        residuals.append(abs(np.sum(volume[:-1]*increment[:-1])-(transfer[0]-transfer[-1])))
        tolerances.append(64*np.finfo(np.float64).eps*max(1., np.sum(abs(transfer))))
    ok = all(r <= t for r,t in zip(residuals, tolerances))
    print(f"[C2] {'PASS' if ok else 'FAIL'} telescoping closed/open ends: max_residual={max(residuals):.17g}; tolerance={max(tolerances):.17g}")
    return ok


def check_C3_dry_source():
    density, tracer, weight, source = sp.symbols('density tracer weight source', nonzero=True)
    residual = sp.factor((tracer+weight*source*tracer/density)/(density+weight*source)-tracer/density)
    base_density = np.array([2., 0., 2.])
    base_tracer = np.array([0.6, 0., 0.6])
    entry = np.array([0.8, 0.8, 0.8])
    dry = np.array([-0.5, -0.5, 0.5])
    # np.divide(where=...) expresses the selected quotient without emitting an
    # irrelevant zero-division warning; torch::where selection is the claim.
    removal = np.divide(base_tracer, base_density, out=entry.copy(), where=base_density != 0)
    carry = np.where(dry < 0., removal, entry)
    got = carry*dry
    expected = np.array([-0.15, -0.4, 0.4])
    error = np.max(abs(got-expected))
    tolerance = 64*np.finfo(np.float64).eps
    ok = residual == 0 and error <= tolerance
    print(f"[C3] {'PASS' if ok else 'FAIL'} dry-source ratio and branches: symbolic_residual={residual}; max_error={error:.17g}; tolerance={tolerance:.17g}")
    return ok


def main():
    return sum(not check() for check in (check_C1_weights, check_C2_transfer, check_C3_dry_source))


if __name__ == '__main__':
    raise SystemExit(main())
