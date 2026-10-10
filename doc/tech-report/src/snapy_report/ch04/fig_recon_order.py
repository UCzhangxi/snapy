"""Measured face order of the interpolants, with and without a critical point in the data.

Data figure. It reads data/recon_orders.json, the committed output of recon_check.py
(claim C4), and draws nothing it does not read.
"""
import json
import os

from snapy_report import figstyle as fs
import matplotlib.pyplot as plt

STYLES = {"cp3": (fs.BLUE, "o", "-"), "cp5": (fs.SKY, "s", "-"),
          "weno3": (fs.VERMILLION, "^", "--"), "weno5": (fs.GREEN, "d", "--")}


def make_fig():
    fs.apply()
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "data", "recon_orders.json")) as fh:
        d = json.load(fh)
    fig, axes = plt.subplots(1, 2, figsize=(fs.DOUBLE, 2.9))
    for ax, key, ns_key, title in ((axes[0], "monotone", "ns_monotone",
                                    "(a) no critical point"),
                                   (axes[1], "critical", "ns_critical",
                                    "(b) through two critical points")):
        ns = d[ns_key]
        for name, (col, mk, ls) in STYLES.items():
            ax.loglog(ns, d[key][name], ls, marker=mk, color=col, label=name, mfc="white")
        ax.set_xlabel("$n_1$ (cells over the unit interval)")
        ax.set_title(title, loc="left")
        ax.set_xticks(ns)
        ax.set_xticklabels([str(v) for v in ns])
        ax.xaxis.set_minor_formatter(plt.NullFormatter())
        ax.grid(True, which="major", color="#DDDDDD", lw=0.5)
    axes[0].set_ylabel("max face error [-]")
    fs.slope_guide(axes[1], 64, d["critical"]["weno3"][1] * 0.45, 200, 2, "$h^2$")
    fs.slope_guide(axes[1], 64, d["critical"]["weno5"][1] * 0.45, 200, 5, "$h^5$")
    axes[0].legend(frameon=False, ncol=2, loc="lower left")
    fig.tight_layout()
    return fig
