"""Per-cell difference between the cell work and the face work on one closed column.

Data: data/cell_defect.csv, written by cellface_check.py (claim C2), which ports src/hydro/hydro_forward.cpp:790-811
and src/forcing/const_gravity.cpp:48-52 at snapy@e894700ff7aee30b52882e5202b16461413780b0.
"""
import os

import numpy as np

from snapy_report import figstyle as fs

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cell_defect.csv")


def make_fig():
    x, d = np.loadtxt(DATA, delimiter=",", unpack=True)
    fig, ax = fs.new_figure(fs.SINGLE, 2.4)
    ax.bar(x, d, width=.8 * (x[1] - x[0]), color=fs.VERMILLION, edgecolor=fs.BLACK, lw=.4)
    ax.axhline(0., color=fs.BLACK, lw=.8)
    ax.set_xlabel("$x_1$ [-]")
    ax.set_ylabel(r"$V(W^{\mathrm{cell}}-W^{\mathrm{face}})$ [-]")
    ax.set_title("sum over the cells = defect of $E+\\mathrm{PE}_d$", fontsize=fs.SMALL_PT)
    return fig
