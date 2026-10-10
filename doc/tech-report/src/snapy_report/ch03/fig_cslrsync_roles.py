"""Left and right states at a face shared by two panels; interior-side states are sent, ghost-side states overwritten.

Suffix rules of src/layout/cubed_sphere_layout.cpp:710-719 and 924-932 at snapy@e894700ff7aee30b52882e5202b16461413780b0. A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.2))
    fs.cell_box(ax, -1, 0)
    fs.cell_box(ax, 0, 0)
    fs.wall(ax, 0, -0.1, 1.1)
    ax.text(-0.5, 0.75, "panel A", ha="center", fontsize=8)
    ax.text(0.5, 0.75, "panel B", ha="center", fontsize=8)
    ax.plot(-0.12, 0.45, "^", color=fs.ORANGE, mec=fs.BLACK, ms=7)
    ax.plot(0.12, 0.45, "^", mfc="white", mec=fs.ORANGE, ms=7)
    ax.plot(0.12, 0.2, "^", color=fs.ORANGE, mec=fs.BLACK, ms=7)
    ax.plot(-0.12, 0.2, "^", mfc="white", mec=fs.ORANGE, ms=7)
    ax.annotate("", xy=(0.1, 0.5), xytext=(-0.1, 0.5), arrowprops=dict(arrowstyle="->", color=fs.GREEN))
    ax.annotate("", xy=(-0.1, 0.15), xytext=(0.1, 0.15), arrowprops=dict(arrowstyle="->", color=fs.GREEN))
    ax.annotate("", xy=(-0.2, -0.25), xytext=(-0.8, -0.25), arrowprops=dict(arrowstyle="->", color=fs.BLACK))
    ax.annotate("", xy=(0.2, -0.25), xytext=(0.8, -0.25), arrowprops=dict(arrowstyle="->", color=fs.BLACK))
    ax.text(-0.5, -0.4, "A's +axis", ha="center", va="top", fontsize=8)
    ax.text(0.5, -0.4, "B's +axis", ha="center", va="top", fontsize=8)
    ax.set(xlim=(-1.1, 1.1), ylim=(-0.65, 1.1), aspect="equal")
    ax.axis("off")
    return fig
