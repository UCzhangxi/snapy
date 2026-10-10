"""One finite-volume cell with its six faces, the areas and the volume.

Cartoon of CoordinateImpl::divergence, src/coord/coordinate.cpp:509-553 at
snapy@e894700ff7aee30b52882e5202b16461413780b0. It reads no data.
"""
from snapy_report import figstyle as fs
import matplotlib.pyplot as plt


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.5))
    ax.set_axis_off()
    ax.set_aspect("equal")
    ax.add_patch(plt.Rectangle((0, 0), 2, 2, fc="#EAF5FC", ec=fs.BLACK, lw=1.0))
    ax.text(1, 1, "$V_i$", ha="center", va="center", fontsize=9, color=fs.SKY)
    ax.plot(1, 1, "o", color=fs.SKY, ms=5, mec=fs.BLACK, mew=0.5)
    for x, y, dx, dy, lab in ((0, 1, -0.55, 0, "$A_{i-1/2}F_{i-1/2}$"),
                              (2, 1, 0.55, 0, "$A_{i+1/2}F_{i+1/2}$")):
        ax.annotate("", xy=(x + dx, y), xytext=(x, y),
                    arrowprops=dict(arrowstyle="->", color=fs.ORANGE, lw=1.6))
        ax.plot(x, y, "^", color=fs.ORANGE, ms=7, mec=fs.BLACK, mew=0.5)
        ax.text(x + dx * 1.15, y + 0.22, lab, ha="center", fontsize=7, color=fs.ORANGE)
    for x, y, dy in ((1, 2, 0.5), (1, 0, -0.5)):
        ax.annotate("", xy=(x, y + dy), xytext=(x, y),
                    arrowprops=dict(arrowstyle="->", color=fs.ORANGE, lw=1.2))
        ax.plot(x, y, "^", color=fs.ORANGE, ms=6, mec=fs.BLACK, mew=0.5)
    ax.text(1, 2.62, "$x_2$, $x_3$ faces", ha="center", fontsize=7, color=fs.ORANGE)
    ax.annotate("", xy=(1.45, 0.55), xytext=(1.0, 1.0),
                arrowprops=dict(arrowstyle="->", color=fs.GREEN, lw=1.4))
    ax.text(1.5, 0.42, "geometric\nsource", fontsize=7, color=fs.GREEN, ha="left")
    ax.set_xlim(-1.3, 3.3)
    ax.set_ylim(-0.9, 2.9)
    return fig
