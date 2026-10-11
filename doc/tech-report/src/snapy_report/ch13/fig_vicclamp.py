"""The two-cell column of vicclamp_check with its species starved: the solve asks for a transfer M through the
face, only the dry fraction moves, and each cell misses M sum(y), which is the clamp residual
(src/implicit/implicit_hydro.cpp:358-378 at snapy@e894700ff7aee30b52882e5202b16461413780b0). A cartoon; it
reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 1.9))
    ax.set_axis_off()
    for k, lab in enumerate(["cell i (donor)", "cell i+1"]):
        ax.add_patch(plt.Rectangle((0.3, 0.2 + 1.0 * k), 2.0, 0.9, fc="#EAF5FC", ec=fs.BLACK, lw=0.7))
        ax.text(1.3, 0.65 + 1.0 * k, lab, ha="center", va="center", fontsize=8)
    ax.plot([0.3, 2.3], [1.1, 1.1], color=fs.ORANGE, lw=2.0)
    ax.annotate("", xy=(2.7, 1.45), xytext=(2.7, 0.75), arrowprops=dict(arrowstyle="->", color=fs.ORANGE, lw=1.2))
    ax.text(2.85, 1.1, r"asked: $M$", fontsize=9, va="center", color=fs.ORANGE)
    ax.text(4.3, 1.45, r"dry moves $M(1-\sum y)$", fontsize=9, color=fs.GREEN)
    ax.text(4.3, 1.05, r"species starved: move 0", fontsize=9, color=fs.VERMILLION)
    ax.text(4.3, 0.55, r"residual $=|M(1-\sum y) - M|/|M| = \sum y$", fontsize=9)
    ax.set_xlim(0.2, 9.0)
    ax.set_ylim(0.1, 2.2)
    return fig
