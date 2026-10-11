"""ludcmp's verdict on the near-singular test matrix of vic_pivot_check (rows (1,0,0), (0,1,0), (0.5,0.8,eps))
as the pivot ratio eps/0.8 crosses tau_3 = 24 eps_mach, in float32 and float64 (src/math/ludcmp.h:35, 83 at
snapy@e894700ff7aee30b52882e5202b16461413780b0). Computed with vic_port.ludcmp.
"""
import matplotlib.pyplot as plt
import numpy as np

from snapy_report import figstyle as fs
from snapy_report.ch07 import vic_port as vp
from snapy_report.ch07.vic_pivot_check import near_singular, tol


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.2))
    ratio = np.logspace(-17, -3, 141)
    for y, dt, col in ((1, np.float64, fs.BLUE), (0, np.float32, fs.ORANGE)):
        ok = np.array([vp.ludcmp(near_singular(dt(0.8 * r), dt), dt)[0] != 0 for r in ratio])
        ax.scatter(ratio[ok], np.full(ok.sum(), y), s=6, color=col, marker="o")
        ax.scatter(ratio[~ok], np.full((~ok).sum(), y), s=10, color=fs.VERMILLION, marker="x", lw=0.8)
        ax.axvline(float(tol(dt, 3)), color=col, lw=0.8, ls="--")
    ax.set_xscale("log")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["float32", "float64"])
    ax.set_ylim(-0.6, 1.6)
    ax.set_xlabel(r"pivot ratio $|p_j|/s_j$")
    ax.text(1e-16, 1.3, r"x refused, o accepted; dashed: $\tau_3$", fontsize=7)
    return fig
