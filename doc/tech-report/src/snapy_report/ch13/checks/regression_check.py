"""Executable check of the log-based mass check (chapter 13, _regression.qmd).

What is checked: MASS_PATTERN, load_masses and check_mass of tests/run_example_mass_check.py (:12, 128-144) at
snapy@e894700ff7aee30b52882e5202b16461413780b0, applied to cycle lines printed in the format of
print_cycle_diagnostics (src/mesh/meshblock.cpp:1088-1111). Claims C1-C3.

Run: python3 regression_check.py   (numpy only; exits with the number of failed claims)
"""
import re
import sys

MASS_PATTERN = re.compile(r"mass0=([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)")


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def cycle_line(cycle, mass, precision=13, label=" ie="):
    """The head and the first tokens of a cycle line, in the printed format."""
    return ("cycle=%d redo=0 time=%.*e dt=%.*e mass0=%.*e masst=%.*e ke=%.*e%s%.*e run-to-date: thetamin=%.*e "
            "thetasevere=0" % (cycle, precision, 0.1 * cycle, precision, 0.1, precision, mass, precision, 1.01 * mass,
                               precision, 3.0, label, precision, 2.5e5, precision, 1.0))


def drift(masses):
    """check_mass: the first and the last sample only, relative to max(|start|, 1)."""
    start, end = masses[0], masses[-1]
    return abs(end - start) / max(abs(start), 1.0)


def check_C1_pattern_reads_mass0_only():
    lines = [cycle_line(c, 1.2345678901234e3) for c in range(3)] + [cycle_line(3, 1.2345678901234e3, 14, " energy=")]
    masses = [float(m.group(1)) for m in MASS_PATTERN.finditer("\n".join(lines))]
    ok = masses == [1.2345678901234e3] * 4
    return report("C1", ok, "the pattern reads one mass0 per line, from the block (13 decimals) and the Mesh "
                  "(14 decimals) line alike, and never masst", "%d samples, all %.13e" % (len(masses), masses[0]))


def check_C2_first_and_last_only():
    masses = [1000., 1000. * (1 + 5e-6), 1000. * (1 + 1e-9)]
    d = drift(masses)
    ok = d < 1e-8 and abs(masses[1] / masses[0] - 1) > 1e-8
    return report("C2", ok, "only the first and the last sample are compared: a 5e-6 excursion in between passes "
                  "the default rtol 1e-8", "drift %.1e" % d)


def check_C3_scale_floor():
    small = [1e-3, 1e-3 * (1 + 1e-6)]
    big = [1e3, 1e3 * (1 + 1e-6)]
    ds, db = drift(small), drift(big)
    ok = ds < 1e-8 < db
    return report("C3", ok, "the scale is max(|mass0|, 1): below a total mass of 1 the test is absolute, so a 1e-6 "
                  "relative drift of a 1e-3 mass passes while the same drift of a 1e3 mass fails",
                  "1e-3: %.1e; 1e3: %.1e" % (ds, db))


def main():
    checks = [check_C1_pattern_reads_mass0_only, check_C2_first_and_last_only, check_C3_scale_floor]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
