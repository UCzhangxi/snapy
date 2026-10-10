"""One Cartesian cell with its widths and the three face areas (src/coord/coordinate.cpp:425-440 at snapy@e894700ff7aee30b52882e5202b16461413780b0).

A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.6))
    dx, dy, dz = 2.0, 1.4, 1.0
    ox, oy = 0.6, 0.45  # oblique offset for the depth axis
    front = [(0, 0), (dx, 0), (dx, dz), (0, dz)]
    top = [(0, dz), (dx, dz), (dx + ox, dz + oy), (ox, dz + oy)]
    side = [(dx, 0), (dx + ox, oy), (dx + ox, dz + oy), (dx, dz)]
    ax.add_patch(Polygon(front, fc="#EAF5FC", ec=fs.BLACK))
    ax.add_patch(Polygon(top, fc=fs.SKY, ec=fs.BLACK, alpha=0.6, hatch=".."))
    ax.add_patch(Polygon(side, fc=fs.ORANGE, ec=fs.BLACK, alpha=0.6, hatch="\\\\"))
    ax.text(dx / 2, -0.15, r"$\Delta x_2$", ha="center", va="top", fontsize=9)
    ax.text(-0.1, dz / 2, r"$\Delta x_1$", ha="right", va="center", fontsize=9)
    ax.text(dx + ox / 2 + 0.1, oy / 2 - 0.05, r"$\Delta x_3$", ha="left", va="top", fontsize=9)
    ax.text(dx / 2 + ox / 2, dz + oy / 2, r"$\Delta x_2\Delta x_3$", ha="center", va="center", fontsize=8)
    ax.text(dx + ox / 2, dz / 2 + oy / 2, r"$\Delta x_1\Delta x_3$", ha="center", va="center", fontsize=8,
            rotation=90)
    ax.text(dx / 2, dz / 2, r"$\Delta x_1\Delta x_2$", ha="center", va="center", fontsize=8)
    fs.cell_value(ax, dx / 2 + ox / 2, dz / 2 + oy / 2 - 0.25)
    ax.set(xlim=(-0.6, dx + ox + 0.6), ylim=(-0.5, dz + oy + 0.2), aspect="equal")
    ax.axis("off")
    return fig
