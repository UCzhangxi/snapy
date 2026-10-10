"""Check Chapter 2 saturation identities at snapy e894700ff7aee30b52882e5202b16461413780b0.
Run: python3 saturation_check.py, from any directory. Independent algebra, not snapy runtime.
The complete synthetic deck and tolerances are in formulas.py.
"""
from pathlib import Path
import runpy

namespace = runpy.run_path(str(Path(__file__).with_name("formulas.py")))


def main():
    checks = [v for k, v in sorted(namespace.items()) if k.startswith("check_C") and k.endswith("_saturation")]
    return sum(not check() for check in checks)


if __name__ == "__main__":
    raise SystemExit(main())
