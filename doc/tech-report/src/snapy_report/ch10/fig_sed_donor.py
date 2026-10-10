"""Donor cells and sealing of the sedimentation flux in one x1 column; snapy@e894700ff7aee30b52882e5202b16461413780b0.

Cartoon of sedimentation_upwind (src/sedimentation/sed_hydro_dispatch.hpp:12-24) and the bounds of
SedHydroImpl::forward (src/sedimentation/sed_hydro.cpp:79-83); no measured data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 3.6))
    ax.set(xlim=(0, 3.4), ylim=(-0.2, 6.2))
    ax.axis("off")
    for k in range(6):
        ghost = k == 0 or k == 5
        fs.cell_box(ax, 1, k, 1, 1, ghost=ghost)
    ax.plot([0.8, 2.2], [1, 1], color=fs.BLACK, lw=2.5)
    ax.plot([0.8, 2.2], [5, 5], color=fs.BLACK, lw=2.5)
    for y in (2, 3, 4):
        ax.annotate("", xy=(1.5, y - 0.3), xytext=(1.5, y + 0.3),
                    arrowprops=dict(arrowstyle="->", color=fs.ORANGE, lw=1.4))
        ax.text(2.3, y, "from cell above\n(settling)", fontsize=7, va="center")
    ax.text(2.3, 1, "physical wall:\nsealed", fontsize=7, va="center")
    ax.text(2.3, 5, "physical wall:\nsealed", fontsize=7, va="center")
    ax.text(0.1, 3, "interior\ncells", fontsize=7, va="center")
    fig.tight_layout()
    return fig
