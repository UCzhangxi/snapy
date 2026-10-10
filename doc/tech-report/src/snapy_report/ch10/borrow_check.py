"""Executable check of the parent-vapour borrow (chapter 10, _borrow.qmd).

What is checked: EquationOfStateImpl::cache_cloud_parents_ (src/eos/equation_of_state.cpp:110-163)
and the borrow in apply_conserved_limiter_ (:262-268) at
snapy@e894700ff7aee30b52882e5202b16461413780b0, ported line for line below. Claims C1-C4.
Also writes data/borrow_bars.csv for fig_borrow_bars.py.

Run: python3 borrow_check.py   (numpy and sympy; exits with the number of failed claims)
"""
import os
import sys

import numpy as np
import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def cache_parents(names, mu, nvapor, clouds, reactions):  # equation_of_state.cpp:110-163
    cache = {}
    for c in clouds:
        parents, parent_mass = [], 0.
        for reactants, products in reactions:
            if c not in products:
                continue
            for parent, coefficient in reactants.items():
                if parent not in names[1:nvapor]:  # :142-145, slot 0 (dry) is never a parent
                    continue
                m = coefficient * mu[names.index(parent)]
                parents.append([parent, m])
                parent_mass += m
            break  # :152, first producing reaction only
        cache[c] = [] if parent_mass <= 0. else [(p, m / parent_mass) for p, m in parents]
    return cache


def borrow(rho, cache):  # equation_of_state.cpp:262-268
    out = dict(rho)
    for c, parents in cache.items():
        if not parents:
            continue
        deficit = min(out[c], 0.)
        for p, share in parents:
            out[p] += deficit * share
        out[c] = max(out[c], 0.)
    return out


NAMES = ["dry", "NH3", "H2S", "NH4SH(s)"]
MU = [2.016e-3, 17.031e-3, 34.082e-3, 51.113e-3]  # kg/mol; NH4SH = NH3 + H2S
NH4SH = ({"NH3": 1., "H2S": 1.}, {"NH4SH(s)": 1.})


def check_C1_cell_mass():
    cache = cache_parents(NAMES, MU, 3, ["NH4SH(s)"], [NH4SH])
    rho = {"dry": 1., "NH3": 2e-4, "H2S": 3e-4, "NH4SH(s)": -1e-4}
    out = borrow(rho, cache)
    before, after = sum(rho.values()), sum(out.values())
    np.savetxt(os.path.join(HERE, "data", "borrow_bars.csv"),
               np.array([[rho[n], out[n]] for n in NAMES[1:]]), delimiter=",", fmt="%.10e",
               header="rows NH3,H2S,NH4SH(s); columns before,after [kg m^-3]")
    ok = abs(after - before) < 1e-18 and out["NH4SH(s)"] == 0.
    return report("C1", ok, "the borrow keeps the cell's total density and sets the condensate to zero",
                  "shares NH3 %.6f, H2S %.6f; total change %.1e; NH3 %.4e -> %.4e, H2S %.4e -> %.4e"
                  % (cache["NH4SH(s)"][0][1], cache["NH4SH(s)"][1][1], after - before,
                     rho["NH3"], out["NH3"], rho["H2S"], out["H2S"]))


def check_C2_elements():
    d, m1, m2 = sp.symbols("d mu_1 mu_2", positive=True)  # deficit, molar masses of the two parents
    share1, share2 = m1 / (m1 + m2), m2 / (m1 + m2)
    mol1, mol2 = d * share1 / m1, d * share2 / m2  # moles of each parent debited
    mol_c = d / (m1 + m2)  # moles of condensate filled (its molar mass is mu_1 + mu_2)
    r1, r2 = sp.simplify(mol1 - mol_c), sp.simplify(mol2 - mol_c)
    return report("C2", r1 == 0 and r2 == 0,
                  "for A + B -> AB the mass shares debit exactly one mole of each parent per mole of condensate",
                  "symbolic residuals %s, %s (so every element is conserved)" % (r1, r2))


def check_C3_first_reaction_only():
    second = ({"NH3": 2.}, {"NH4SH(s)": 1.})
    cache = cache_parents(NAMES, MU, 3, ["NH4SH(s)"], [NH4SH, second])
    parents = [p for p, _ in cache["NH4SH(s)"]]
    return report("C3", parents == ["NH3", "H2S"],
                  "only the first nucleation reaction that produces a cloud sets its parents",
                  "parents %s with a second reaction 2 NH3 -> NH4SH(s) listed after the first" % parents)


def check_C4_dry_never_parent_and_parentless():
    react = ({"dry": 1., "NH3": 1.}, {"NH4SH(s)": 1.})
    cache = cache_parents(NAMES, MU, 3, ["NH4SH(s)"], [react])
    rain = cache_parents(NAMES + ["rain"], MU + [18e-3], 3, ["rain"], [NH4SH])
    ok = [p for p, _ in cache["NH4SH(s)"]] == ["NH3"] and cache["NH4SH(s)"][0][1] == 1. and rain["rain"] == []
    return report("C4", ok, "dry air is skipped as a reactant; a cloud no reaction produces has no parents",
                  "parents with dry listed %s; parents of rain %s"
                  % ([(p, s) for p, s in cache["NH4SH(s)"]], rain["rain"]))


def main():
    checks = [check_C1_cell_mass, check_C2_elements, check_C3_first_reaction_only,
              check_C4_dry_never_parent_and_parentless]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
