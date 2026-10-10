"""Two-product evaporation drive against saturation ratio: the extent law and the earlier law.

Data: data/kinetics_extent.csv, written by kinetics_check.py (claim C4), which ports
src/kinetics/evaporation.cpp:165-192 at kintera@c55b13b2204997d2d09e04498558ab9495d8ee77.
"""
import os

import matplotlib.pyplot as plt
import numpy as np

from snapy_report import figstyle as fs

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "kinetics_extent.csv")


def make_fig():
    fs.apply()
    s, x1, e1, x10, e10 = np.loadtxt(DATA, delimiter=",", unpack=True)
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.6))
    ax.plot(s, x1 / x1[0], color=fs.GREEN, label=r"extent, $c_1=c_2$")
    ax.plot(s, x10 / x10[0], color=fs.GREEN, ls="--", label=r"extent, $c_1=10c_2$")
    ax.plot(s, e1 / e1[0], color=fs.BLUE, ls=":", label=r"$K-c_1c_2$ (earlier law)")
    ax.set_xlabel(r"saturation ratio $c_1c_2/K$ [-]")
    ax.set_ylabel("drive / drive at 0 [-]")
    ax.legend(frameon=False)
    return fig
