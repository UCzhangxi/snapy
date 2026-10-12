"""An x1 wall meeting an x2 block seam: the x1 ghost rows inside the tangential ghost slab are rewritten by the wall
function (src/mesh/meshblock.cpp:937-979 at snapy@6fbb39750f62b83df096058a4746e77d0a634bc5). A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.8))
    for j in range(4):
        for i in range(3):
            fs.cell_box(ax, j, i)
    for j in range(4, 6):
        for i in range(3):
            fs.cell_box(ax, j, i, ghost=True)
        for i in (-2, -1):
            ax.add_patch(Rectangle((j, i), 1, 1, fc=fs.GREEN, ec=fs.BLACK, alpha=0.6))
    for j in range(4):
        for i in (-2, -1):
            fs.cell_box(ax, j, i, ghost=True)
    ax.plot([-0.2, 6.2], [0, 0], color=fs.BLACK, lw=2.5)
    ax.plot([4, 4], [-2.2, 3.2], color=fs.PURPLE, ls="--", lw=1.4)
    ax.text(2.0, 3.25, "this block", ha="center", fontsize=8)
    ax.text(5.0, 3.25, "x2 ghost slab", ha="center", fontsize=8)
    ax.text(6.3, 0.05, r"$x_1$ wall", fontsize=8, va="bottom")
    ax.text(5.0, -2.6, "rewritten", ha="center", fontsize=8, color=fs.GREEN)
    ax.set(xlim=(-0.4, 7.4), ylim=(-2.9, 3.6), aspect="equal")
    ax.axis("off")
    return fig
