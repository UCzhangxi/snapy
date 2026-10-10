"""An NH4SH(s) deficit filled from NH3 and H2S in one cell, before and after the borrow.

Data: data/borrow_bars.csv, written by borrow_check.py (claim C1), which ports
src/eos/equation_of_state.cpp:110-163 and :262-268 at snapy@e894700ff7aee30b52882e5202b16461413780b0.
"""
import os

import matplotlib.pyplot as plt
import numpy as np

from snapy_report import figstyle as fs

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "borrow_bars.csv")


def make_fig():
    fs.apply()
    before, after = np.loadtxt(DATA, delimiter=",", unpack=True)
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.4))
    x = np.arange(3)
    ax.bar(x - 0.18, before * 1e4, 0.34, color=fs.SKY, edgecolor=fs.BLACK, label="before")
    ax.bar(x + 0.18, after * 1e4, 0.34, color=fs.GREEN, edgecolor=fs.BLACK, hatch="//", label="after")
    ax.axhline(0., color=fs.BLACK, lw=0.8)
    ax.set_xticks(x, [r"$\mathrm{NH_3}$", r"$\mathrm{H_2S}$", r"$\mathrm{NH_4SH(s)}$"])
    ax.set_ylabel(r"$\rho_n$ [$10^{-4}$ kg m$^{-3}$]")
    ax.legend(frameon=False, loc="upper left")
    return fig
