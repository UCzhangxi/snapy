"""Executable check of the x1 seam relay of the reference scan (chapter 5, _seam.qmd).

What is checked: the scan hydro_ref_x1_scan_impl (src/hydro/hydro_ref_x1_impl.h:22-60) with its single-block top
anchor, and the relay of @eq-ch05-seam-relay, where a block below a seam takes as its top anchor the bottom-face
pressure of the block above (take_x1_anchor / pass_x1_anchor, src/hydro/hydro.cpp:540-548, 591-593), at
snapy@6fbb39750f62b83df096058a4746e77d0a634bc5, ported to numpy for one column. Claims C1-C2.

Run: python3 seam_check.py   (numpy only; exits with the number of failed claims)
"""
import sys

import numpy as np


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


G = 9.8


def scan(rho, p, dx, anchor=None):
    """Interior cells only (iu = last cell): returns (psf_lo, psf_hi) per cell, scanning down from the top."""
    n = len(rho)
    top = anchor if anchor is not None else p[-1] * np.exp(-G * 0.5 * dx[-1] / (p[-1] / rho[-1]))
    lo, hi = np.empty(n), np.empty(n)
    face = top
    for i in range(n - 1, -1, -1):
        hi[i] = face
        lo[i] = face + G * rho[i] * dx[i]
        face = lo[i]
    return lo, hi


def column(n=64):
    rng = np.random.default_rng(2)
    dx = rng.uniform(80., 120., n)
    z = np.cumsum(dx) - 0.5 * dx
    rho = 1.2 * np.exp(-z / 8000.) * (1. + 0.01 * rng.normal(size=n))
    p = 1e5 * np.exp(-z / 8000.)
    return rho, p, dx


def split_scan(rho, p, dx, nblocks):
    """Blocks from the top down: the top block uses its own anchor, every lower block the relayed bottom face."""
    edges = np.linspace(0, len(rho), nblocks + 1).astype(int)
    lo, hi = np.empty(len(rho)), np.empty(len(rho))
    anchor = None
    for b in range(nblocks - 1, -1, -1):
        s = slice(edges[b], edges[b + 1])
        lo[s], hi[s] = scan(rho[s], p[s], dx[s], anchor)
        anchor = lo[s][0]                  # pass_x1_anchor: the bottom-face pressure of this block
    return lo, hi


def check_C1_split_equals_one_block():
    rho, p, dx = column()
    lo1, hi1 = scan(rho, p, dx)
    worst = max(max(np.abs(split_scan(rho, p, dx, nb)[k] - (lo1, hi1)[k]).max() for k in (0, 1)) for nb in (2, 4, 8))
    return report("C1", worst == 0., "a column split into 2, 4 or 8 blocks with relayed anchors gives the one-block "
                  "face pressures; the relay continues the same additions in the same order",
                  "max |difference| %.1e Pa" % worst)


def check_C2_seam_face_single_valued():
    rho, p, dx = column()
    lo, hi = split_scan(rho, p, dx, 4)
    edges = np.linspace(0, len(rho), 5).astype(int)[1:-1]
    worst = max(abs(hi[e - 1] - lo[e]) for e in edges)
    return report("C2", worst == 0., "at each seam the top face of the block below equals the bottom face of the block "
                  "above", "max |difference| at 3 seams %.1e Pa" % worst)


def main():
    checks = [check_C1_split_equals_one_block, check_C2_seam_face_single_valued]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
