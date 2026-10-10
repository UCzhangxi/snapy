"""Check Chapter 2 aneos identities at snapy e894700ff7aee30b52882e5202b16461413780b0.
Run: python3 aneos_check.py, from any directory. Independent algebra, not snapy runtime.
The complete synthetic deck and tolerances are in formulas.py.
"""
from formulas import check_C1_aneos


def main():
    return int(not check_C1_aneos())


if __name__ == "__main__":
    raise SystemExit(main())
