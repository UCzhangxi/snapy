"""Check Chapter 2 moist-mixture identities at snapy 6fbb39750f62b83df096058a4746e77d0a634bc5 (the code pin).
Run: python3 moist-mixture_check.py, from any directory. Independent algebra, not snapy runtime.
The complete synthetic deck and tolerances are in formulas.py.
Pin audit: the src/eos diff from e894700 to 6fbb3975 changes failure-count handling, not the thermodynamic algebra ported here.
"""
from pathlib import Path
import runpy

namespace = runpy.run_path(str(Path(__file__).resolve().parent.parent / "formulas.py"))


def main():
    checks = [v for k, v in sorted(namespace.items()) if k.startswith("check_C") and k.endswith("_moist_mixture")]
    return sum(not check() for check in checks)


if __name__ == "__main__":
    raise SystemExit(main())
