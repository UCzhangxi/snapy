"""Check Chapter 2 shallow-water identities at snapy 6fbb39750f62b83df096058a4746e77d0a634bc5 (the code pin).
Run: python3 shallow-water_check.py, from any directory. Independent algebra, not snapy runtime.
The complete synthetic deck and tolerances are in formulas.py.
"""
from pathlib import Path
import runpy

namespace = runpy.run_path(str(Path(__file__).with_name("formulas.py")))


def main():
    checks = [v for k, v in sorted(namespace.items()) if k.startswith("check_C") and k.endswith("_shallow_water")]
    return sum(not check() for check in checks)


if __name__ == "__main__":
    raise SystemExit(main())
