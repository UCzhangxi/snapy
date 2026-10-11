"""Order of the face-form gravity work, without and with the cp3/cp5/weno5 curvature flux, interior and wall cells.

Data: data/face_order.csv, written by cellface_check.py (claims C3-C4), which ports
src/hydro/hydro_forward.cpp:794-848 at snapy@e894700ff7aee30b52882e5202b16461413780b0 (exact point fluxes,
g1 = -10, x1 in [0, 1]).
"""
import os

import matplotlib.pyplot as plt
import numpy as np

from snapy_report import figstyle as fs

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "face_order.csv")


def make_fig():
    fs.apply()
    n, fi, fw, ki, kw = np.loadtxt(DATA, delimiter=",", unpack=True)
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 3.4))
    ax.loglog(n, fi, "o-", color=fs.VERMILLION, label="face, interior")
    ax.loglog(n, fw, "s--", color=fs.VERMILLION, label="face, wall")
    ax.loglog(n, ki, "o-", color=fs.GREEN, label="face + K, interior")
    ax.loglog(n, kw, "s--", color=fs.GREEN, label="face + K, wall")
    for order, y0 in ((1, kw[0]), (2, fi[0]), (4, ki[0])):
        y1 = y0 * 2. * (n[-1] / n[0]) ** (-order)
        ax.loglog([n[0], n[-1]], [2. * y0, y1], ":", color=fs.BLUE, lw=.9)
        ax.text(n[-1] * 1.1, y1, "$h^%d$" % order, fontsize=8, color=fs.BLUE, va="center")
    ax.set_xticks(n, [str(int(k)) for k in n])
    ax.minorticks_off()
    ax.set_xlabel("cells $n_1$ [-]")
    ax.set_ylabel("max error of the work [-]")
    fig.tight_layout(rect=(0, .2, 1, 1))
    fig.legend(*ax.get_legend_handles_labels(), fontsize=8, frameon=False, ncol=2, loc="lower center")
    return fig
