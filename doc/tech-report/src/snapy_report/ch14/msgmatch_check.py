"""Executable check of the exchange message tags (chapter 14, _msgmatch.qmd).

What is checked, at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported line for line below:
- get_buffer_id and make_comm_tag (src/layout/layout.hpp:32-35, 161-170);
- the per-variable tag of exchange_each_var (src/layout/layout.cpp:652-666);
- the block-to-block fold of send_to_block (src/layout/layout.cpp:849-877) applied to the
  hydro relay tags 0x7715-0x7724 (src/hydro/hydro.cpp:518, 594-595; src/hydro/hydro_forward.cpp:284, 447-448, 507);
- the gather_x1 tag base 1 << 24 (src/layout/layout.cpp:777-847).
Claims C1-C5.

Run: python3 msgmatch_check.py   (standard library only; exits with the number of failed claims)
"""
import itertools
import sys


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def get_buffer_id(offset):  # layout.hpp:32-35; Python % is already non-negative
    dy, dx, dz = offset
    return dx % 3 + (dy % 3) * 3 + (dz % 3) * 9


def make_comm_tag(local_block_index, offset, phyid):  # layout.hpp:161-170
    tag = phyid * 1024 + local_block_index * 32 + get_buffer_id(offset)
    if not (phyid >= 0 and 0 <= tag < 65536):
        raise ValueError("comm tag %d outside [0, 65536)" % tag)
    return tag


OFFSETS = list(itertools.product((-1, 0, 1), repeat=3))
RELAY = [0x7715, 0x7717, 0x7718, 0x7720, 0x7721, 0x7722, 0x7724]
GATHER = 1 << 24


def check_C1_base_tag_one_to_one():
    ids = sorted({get_buffer_id(o) for o in OFFSETS})
    tags = [make_comm_tag(l, o, phi) for phi in range(64) for l in range(32) for o in OFFSETS]
    refused = 0
    for phi in (-1, 64):
        try:
            make_comm_tag(0, (0, 0, 0), phi)
        except ValueError:
            refused += 1
    return report("C1", len(set(tags)) == len(tags) and min(tags) >= 0 and max(tags) < 65536 and refused == 2,
                  "T0 is one to one in (phi, l, beta) for 0 <= phi < 64, l < 32, and phi = -1 or 64 is refused",
                  "%d buffer ids (%d..%d), %d tags, %d distinct, range %d..%d; refused %d of 2"
                  % (len(ids), ids[0], ids[-1], len(tags), len(set(tags)), min(tags), max(tags), refused))


def check_C2_variable_tag():
    n_max = 32767  # exchange_each_var refuses more than 32768 variables
    top = 65535 + 65536 * n_max
    sample = [(t0, n) for t0 in (0, 1, 26, 1023, 65535) for n in (0, 1, 255, 256, n_max)]
    back = all(((t0 + 65536 * n) // 65536, (t0 + 65536 * n) % 65536) == (n, t0) for t0, n in sample)
    return report("C2", back and top < 2 ** 31,
                  "T = T0 + 65536 n is one to one and stays below 2^31 for n < 32768",
                  "%d sampled (T0, n) recovered from T; largest T = %d = 2^31 - %d"
                  % (len(sample), top, 2 ** 31 - top))


def check_C3_unchecked_block_bound():
    a = make_comm_tag(32, (0, 0, 0), 0)
    b = make_comm_tag(0, (0, 0, 0), 1)
    return report("C3", a == b,
                  "l < 32 is needed and not checked: l = 32 at phi is accepted and equals l = 0 at phi + 1",
                  "make_comm_tag(32, 0, phi=0) = %d = make_comm_tag(0, 0, phi=1) = %d" % (a, b))


def check_C4_relay_tags():
    t0_small = {make_comm_tag(l, o, phi) for phi in range(64) for l in range(16) for o in OFFSETS}
    hit = [hex(t) for t in RELAY if t in t0_small]
    folded = [t + 0x10000 * (me * bpp + peer) for t in RELAY for bpp in range(1, 17)
              for me in range(bpp) for peer in range(bpp)]
    low = all(f % 65536 in RELAY for f in folded)
    return report("C4", not hit and low and max(folded) < GATHER,
                  "the hydro relay tags are no T0 at l < 16; folded, they keep their low 16 bits and stay below 2^24",
                  "relay tags hitting T0: %d; largest folded tag %d = 2^24 - %d" % (len(hit), max(folded),
                                                                                   GATHER - max(folded)))


def check_C5_gather_separation():
    first = min(n for n in range(32768) if 65536 * n >= GATHER)
    below = 65535 + 65536 * (first - 1) < GATHER
    return report("C5", first == 256 and below,
                  "exchange tags stay below the gather_x1 base 2^24 while an exchange has at most 256 variables",
                  "first variable index whose tags reach 2^24: n = %d" % first)


def main():
    checks = [check_C1_base_tag_one_to_one, check_C2_variable_tag, check_C3_unchecked_block_bound,
              check_C4_relay_tags, check_C5_gather_separation]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
