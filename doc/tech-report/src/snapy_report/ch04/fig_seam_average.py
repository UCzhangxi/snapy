"""A process seam in x1: both ranks own the same face and average their fluxes.

Cartoon of the seam exchange, src/hydro/hydro_forward.cpp:425-508 at
snapy@e894700ff7aee30b52882e5202b16461413780b0. It reads no data.
"""
from snapy_report import figstyle as fs
import matplotlib.pyplot as plt


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.4))
    ax.set_axis_off()
    ax.set_aspect("equal")
    for x in (0, 1):
        ax.add_patch(plt.Rectangle((x, 0.5), 1, 0.9, fc="#EAF5FC", ec=fs.BLACK, lw=0.8))
    ax.plot([1, 1], [0.5, 1.4], color=fs.PURPLE, lw=2.2, ls="--")
    ax.text(0.5, 1.52, "rank 0", ha="center", fontsize=7)
    ax.text(1.5, 1.52, "rank 1", ha="center", fontsize=7)
    ax.text(1.0, 1.72, "x1 seam", ha="center", fontsize=7, color=fs.PURPLE)
    ax.plot(0.93, 0.95, "^", color=fs.GREEN, ms=7, mec=fs.BLACK, mew=0.4)
    ax.plot(1.07, 0.95, "^", color=fs.BLUE, ms=7, mec=fs.BLACK, mew=0.4)
    ax.text(0.86, 0.72, "$F^{(0)}$", fontsize=7, color=fs.GREEN, ha="right")
    ax.text(1.14, 0.72, "$F^{(1)}$", fontsize=7, color=fs.BLUE)
    ax.annotate("", xy=(1.3, 0.2), xytext=(0.7, 0.2),
                arrowprops=dict(arrowstyle="<->", color=fs.BLACK, lw=1.0))
    ax.text(1.0, 0.02, "exchange, then both set\n$F = \\frac{1}{2}(F^{(0)}+F^{(1)})$",
            ha="center", fontsize=7)
    ax.set_xlim(-0.2, 2.2)
    ax.set_ylim(-0.45, 2.0)
    return fig
