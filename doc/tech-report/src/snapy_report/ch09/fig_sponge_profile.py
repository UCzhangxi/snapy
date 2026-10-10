"""Scale factor sin^2(pi eta / 2) of the top and bottom sponge layers, per cell.

Data: data/sponge_profile.csv, written by sponge_check.py (claim C1), which ports
src/forcing/top_sponge_lyr.cpp:58-62 and bot_sponge_lyr.cpp:58-62 at
snapy@e894700ff7aee30b52882e5202b16461413780b0; 20 cells of 0.5 on [0, 10], width 2.
"""
import os

import numpy as np

from snapy_report.ch09._style import BLUE, GREEN, ORANGE, SINGLE, new_figure

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sponge_profile.csv")


def make_fig():
    lo, hi, top, bot = np.loadtxt(DATA, delimiter=",", unpack=True)
    fig, ax = new_figure(SINGLE, 2.6)
    xs = np.linspace(0., 10., 400)
    ax.plot(xs, np.sin(np.pi / 2 * np.clip((2. - (10. - xs)) / 2., 0, 1))**2, color=BLUE, lw=0.8, ls=":")
    ax.plot(xs, np.sin(np.pi / 2 * np.clip((2. - xs) / 2., 0, 1))**2, color=BLUE, lw=0.8, ls=":")
    ax.stairs(top, np.append(lo, hi[-1]), color=GREEN, lw=1.3, label="top sponge, per cell")
    ax.stairs(bot, np.append(lo, hi[-1]), color=ORANGE, lw=1.3, ls="--", label="bottom sponge, per cell")
    ax.set_xlabel("$x_1$ [m]")
    ax.set_ylabel(r"$\sin^2(\pi\eta/2)$ [-]")
    ax.legend(frameon=False, loc="center")
    return fig
