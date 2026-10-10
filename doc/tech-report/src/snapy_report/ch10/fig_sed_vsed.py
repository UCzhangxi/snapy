"""Terminal velocity against particle radius for the H2 defaults at two pressures.

Data: data/sed_vsed.csv, written by sed_check.py (claim C5), a port of src/sedimentation/sed_vel.cpp:34-71 at
snapy@e894700ff7aee30b52882e5202b16461413780b0 (T = 150 K, rho = 0.1, rho_p = 1000 kg m^-3, g_1 = -24.79 m s^-2).
"""
import os

import matplotlib.pyplot as plt
import numpy as np

from snapy_report import figstyle as fs

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sed_vsed.csv")


def make_fig():
    fs.apply()
    a, w4, s4, w6, s6 = np.loadtxt(DATA, delimiter=",", unpack=True)
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.8))
    ax.loglog(a, -w4, color=fs.GREEN, label=r"$10^4$ Pa, slip-corrected")
    ax.loglog(a, -s4, color=fs.BLUE, ls=":", label="Stokes (both p)")
    ax.loglog(a, -w6, color=fs.GREEN, ls="--", label=r"$10^6$ Pa, slip-corrected")
    ax.axhline(5e3, color=fs.VERMILLION, lw=0.8, ls="-.", label="upper-limit")
    ax.set_xlabel("particle radius $a_n$ [m]")
    ax.set_ylabel(r"$-w_{\mathrm{s},n}$ [m s$^{-1}$]")
    ax.legend(frameon=False, fontsize=7)
    return fig
