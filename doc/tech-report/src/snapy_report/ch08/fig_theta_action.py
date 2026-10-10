"""How hard the limiter works, and what it buys, against the step size.

Data figure. It reads data/theta_action.json, the committed output of positivity_check.py
(claim C1), and draws nothing it does not read.
"""
import json
import os

from snapy_report import figstyle as fs
import matplotlib.pyplot as plt


def make_fig():
    fs.apply()
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "data", "theta_action.json")) as fh:
        d = json.load(fh)
    fig, axes = plt.subplots(1, 2, figsize=(fs.DOUBLE, 2.7))
    ax = axes[0]
    ax.semilogx(d["dt"], d["unlimited_min"], "-o", color=fs.VERMILLION,
                label="unlimited", mfc="white")
    ax.semilogx(d["dt"], d["limited_min"], "-s", color=fs.GREEN,
                label="limited", mfc="white")
    ax.axhline(0., color=fs.BLACK, lw=0.8, ls=":")
    ax.set_xlabel("$\\Delta t$ [-]")
    ax.set_ylabel("worst cell value after one step [-]")
    ax.set_title("(a) what it buys", loc="left")
    ax.legend(frameon=False, loc="lower left")
    ax.grid(True, which="major", color="#DDDDDD", lw=0.5)

    ax = axes[1]
    ax.semilogx(d["dt"], [100. * f for f in d["limited_fraction"]], "-^",
                color=fs.ORANGE, mfc="white")
    ax.set_xlabel("$\\Delta t$ [-]")
    ax.set_ylabel("cells with $\\theta<1$ [%]")
    ax.set_title("(b) how hard it works", loc="left")
    ax.grid(True, which="major", color="#DDDDDD", lw=0.5)
    fig.tight_layout()
    return fig
