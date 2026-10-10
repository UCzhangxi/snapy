"""Executable check of the moist redo causes (chapter 10, _redo.qmd).

What is checked: MeshBlockImpl::reduce_redo_flags (src/mesh/meshblock.cpp:1288-1300), the cause names
of apply_redo (:1237-1240) and its termination rule (:1241-1247, :1261-1267) at
snapy@e894700ff7aee30b52882e5202b16461413780b0, ported line for line below. Claims C1-C3.

Run: python3 redo_check.py   (numpy only; exits with the number of failed claims)
"""
import itertools
import sys

import numpy as np

NAMES = ["floor", "clamp", "limiter", "nan", "saturation", "vic-solve"]  # order of local_redo_flags, :1283-1285


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def reduce_flags(per_rank):  # meshblock.cpp:1288-1300; allreduce MAX over ranks of 0/1 doubles
    glob = np.max(np.array(per_rank, dtype=float), axis=0)
    causes = 0
    for i in range(6):
        causes |= int(glob[i] > 0.) << i
    return causes


def names(causes):  # meshblock.cpp:1237-1240
    return [n for i, n in enumerate(NAMES) if causes & (1 << i)]


def decide(causes, current_redo, max_redo):  # meshblock.cpp:1241-1270; returns (action, restored)
    if not causes:
        return "accept", False
    current_redo += 1
    if current_redo > max_redo and not (causes & 32):
        return "terminate", False
    if current_redo > max_redo:
        return "terminate", True
    return "redo", True


def check_C1_bits():
    want = {1: ["floor"], 4: ["limiter"], 8: ["nan"], 16: ["saturation"], 32: ["vic-solve"]}
    ok = all(names(c) == n for c, n in want.items()) and names(reduce_flags([[0, 0, 0, 0, 1, 0]])) == ["saturation"]
    return report("C1", ok, "the six flags become bits 1, 2, 4, 8, 16, 32; moist physics raises 4 (species repair) and 16 (saturation)",
                  "saturation alone gives causes = %d" % reduce_flags([[0, 0, 0, 0, 1, 0]]))


def check_C2_max_is_or():
    bad = 0
    for a, b in itertools.product(range(64), repeat=2):
        ra = [(a >> i) & 1 for i in range(6)]
        rb = [(b >> i) & 1 for i in range(6)]
        bad += reduce_flags([ra, rb]) != (a | b)
    return report("C2", bad == 0, "a MAX reduction of 0/1 flags over ranks is the bitwise OR of every rank's causes",
                  "%d mismatches over all 4096 pairs of two-rank cause sets" % bad)


def check_C3_termination():
    rows = [decide(16, 5, 5), decide(48, 5, 5), decide(16, 4, 5), decide(0, 5, 5)]
    want = [("terminate", False), ("terminate", True), ("redo", True), ("accept", False)]
    return report("C3", rows == want,
                  "past max_redo a moist cause terminates without restoring; with vic-solve the state is restored "
                  "first", "saturation at 6th attempt %s; saturation + vic-solve %s; 5th attempt %s; no cause %s"
                  % tuple(rows))


def main():
    checks = [check_C1_bits, check_C2_max_is_or, check_C3_termination]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
