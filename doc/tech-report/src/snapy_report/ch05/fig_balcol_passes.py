"""Moist balance-ic loop of the bryan example (chapter 5, balance_column): what saturation moves after each projection.

Per pass: the largest relative pressure change the saturation adjustment makes to the column balance_column has just
projected, and the number of projection sweeps. Data: data/bryan_balance_ic.json, printed by ctest
test_bryan_balance_ic at snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy), CPU, double.
"""
import numpy as np

from snapy_report.ch05 import _style as fs
from snapy_report.ch05 import _draw as d


def make_fig():
    data = d.load("bryan_balance_ic.json")
    t = np.array(data["passes"])
    fig, axes = fs.new_figure("double", 2.3, 1, 2)
    axes[0].semilogy(t[:, 0], t[:, 3], color=fs.GREEN, marker="o", mfc="white", mec=fs.GREEN)
    axes[0].axhline(1e-13, color=fs.BLACK, ls=":", lw=0.8)
    axes[0].text(1.0, 2.0e-13, "stop: $10^{-13}$", fontsize=fs.SMALL_PT, va="bottom")
    axes[0].set_xlabel("pass [count]")
    axes[0].set_ylabel("saturation max $|\\Delta p/p|$ [-]")
    axes[1].plot(t[:, 0], t[:, 2], color=fs.BLACK, marker="s", mfc="white", mec=fs.BLACK)
    axes[1].set_xlabel("pass [count]")
    axes[1].set_ylabel("projection sweeps [count]")
    for ax in axes:
        ax.set_xticks(t[:, 0])
    fs.panel_labels(axes)
    return fig
