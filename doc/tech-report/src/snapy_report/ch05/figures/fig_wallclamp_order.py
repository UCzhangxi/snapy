"""Face-density reference error next to the walls against the interior, default reference (chapter 5).

Relative error of dsf at the first and second faces above the bottom wall, the first and second faces below the
top wall, and the largest interior error (at least three faces from each wall), for nz = 16, 32, 64, 128 on the
polytrope T = 1 - z/2 of tests/test_wb_ref_wall.cpp. Data: data/wb_ref_wall_order.json, printed by ctest
test_wb_ref_wall.release at snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy), CPU, double.
"""
import numpy as np

from snapy_report.ch05 import _style as fs
from snapy_report.ch05 import _draw as d


def make_fig():
    data = d.load("wb_ref_wall_order.json")
    t = np.array(data["beta_0.5"])
    nz = t[:, 0]
    fig, ax = fs.new_figure("single", 2.6)
    series = ((1, "bottom face 1", fs.GREEN, "o", "-"), (2, "bottom face 2", fs.GREEN, "s", "--"),
              (7, "top face 1", fs.ORANGE, "^", "-"), (8, "top face 2", fs.ORANGE, "v", "--"),
              (9, "interior max", fs.BLACK, "D", ":"))
    for col, lab, c, m, ls in series:
        ax.loglog(nz, np.abs(t[:, col]), color=c, marker=m, ls=ls, mfc="white", mec=c, label=lab)
    fs.slope_guide(ax, 20, 2.5e-5, 80, 2, label="$n_1^{-2}$")
    ax.set_xlabel("$n_1$ [count]")
    ax.set_ylabel("relative error of $\\rho_{\\mathrm{sf}}$ [-]")
    ax.set_xticks(nz)
    ax.set_xticklabels([str(int(v)) for v in nz])
    ax.minorticks_off()
    ax.legend(loc="lower left", fontsize=fs.SMALL_PT)
    return fig
