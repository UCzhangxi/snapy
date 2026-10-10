"""A 64-cell column with an interior and a bottom vapour deficit, before and after fix_vapor.

Data: data/fixvapor_column.csv, written by fixvapor_check.py (claim C6), a line-for-line port of
src/eos/fix_vapor_impl.h:9-79 at snapy@e894700ff7aee30b52882e5202b16461413780b0.
"""
import os

import matplotlib.pyplot as plt
import numpy as np

from snapy_report import figstyle as fs

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fixvapor_column.csv")


def make_fig():
    fs.apply()
    cell, before, after, major = np.loadtxt(DATA, delimiter=",", unpack=True)
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 3.2))
    ax.plot(before / major * 1e3, cell, color=fs.VERMILLION, ls="--", marker="x", ms=3, label="before")
    ax.plot(after / major * 1e3, cell, color=fs.GREEN, marker="o", ms=2.5, label="after")
    ax.axvline(0., color=fs.BLACK, lw=0.8)
    ax.set_xlabel(r"$\rho_n/\rho_{\mathrm{d}}$ [$10^{-3}$]")
    ax.set_ylabel("cell index $i$ (0 = bottom)")
    ax.legend(frameon=False, loc="center left")
    return fig
