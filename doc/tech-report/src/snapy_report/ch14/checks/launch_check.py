"""Executable check of the global block rank (chapter 14, _launch.qmd).

What is checked, at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported line for line below:
- owner_process_rank, local_block_index and global_block_rank of LayoutOptions
  (src/layout/layout.hpp:83-93).
Claims C1-C3.

Run: python3 launch_check.py   (standard library only; exits with the number of failed claims)
"""
import sys


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def owner_process_rank(r, b):  # layout.hpp:83-85
    return r // max(1, b)


def local_block_index(r, b):  # layout.hpp:87-89
    return r % max(1, b)


def global_block_rank(p, l, b):  # layout.hpp:91-93
    return p * max(1, b) + l


def check_C1_round_trip():
    bad, n = 0, 0
    for b in range(1, 17):
        for nproc in (1, 2, 3, 6, 24):
            for r in range(nproc * b):
                n += 1
                bad += global_block_rank(owner_process_rank(r, b), local_block_index(r, b), b) != r
    return report("C1", bad == 0, "r -> (p, l) -> r is the identity",
                  "b = 1..16, 1-24 processes: %d ranks, %d mismatches" % (n, bad))


def check_C2_one_to_one():
    bad, n = 0, 0
    for b in range(1, 17):
        for nproc in (1, 2, 3, 6, 24):
            ranks = [global_block_rank(p, l, b) for p in range(nproc) for l in range(b)]
            n += len(ranks)
            bad += sorted(ranks) != list(range(nproc * b))
    return report("C2", bad == 0, "(p, l) -> r maps the P b pairs onto 0..P b - 1, with no gap or repeat",
                  "%d pairs, %d layouts not a bijection" % (n, bad))


def check_C3_unset_is_one():
    ok = all(owner_process_rank(r, b) == r and local_block_index(r, b) == 0 and global_block_rank(r, 0, b) == r
             for b in (0, -1) for r in range(64))
    return report("C3", ok, "blocks_per_process below 1 acts as 1: block rank = process rank",
                  "b = 0 and -1, ranks 0-63")


def main():
    checks = [check_C1_round_trip, check_C2_one_to_one, check_C3_unset_is_one]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
