"""A 2x2 slab decomposition with reflecting x2 walls and periodic x3: physical, internal and periodic faces.

Classification of src/mesh/meshblock.cpp:137-179 at snapy@e894700ff7aee30b52882e5202b16461413780b0. A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.8))
    for bx in range(2):
        for by in range(2):
            fs.cell_box(ax, bx, by)
            ax.text(bx + 0.5, by + 0.5, "(%d,%d)" % (bx, by), ha="center", va="center", fontsize=8)
    for x in (0, 2):
        fs.wall(ax, x, 0, 2)
    ax.plot([1, 1], [0, 2], color=fs.PURPLE, ls="--", lw=1.4)
    ax.plot([0, 2], [1, 1], color=fs.PURPLE, ls="--", lw=1.4)
    for y in (0, 2):
        ax.plot([0, 2], [y, y], color=fs.BLUE, ls=":", lw=1.6)
    ax.text(-0.08, 1.0, "wall", rotation=90, ha="right", va="center", fontsize=8)
    ax.text(1.0, 2.08, "periodic", ha="center", va="bottom", fontsize=8, color=fs.BLUE)
    ax.text(1.06, 1.06, "internal", ha="left", va="bottom", fontsize=8, color=fs.PURPLE)
    ax.set_xlabel(r"$x_2$ block $r_x$")
    ax.set_ylabel(r"$x_3$ block $r_y$")
    ax.set(xlim=(-0.3, 2.2), ylim=(-0.1, 2.35), aspect="equal", xticks=[], yticks=[])
    for s in ax.spines.values():
        s.set_visible(False)
    return fig
