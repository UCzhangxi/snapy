"""The condensate borrow: a negative cloud takes its deficit from the parent vapour.

Cartoon of the repair at src/eos/equation_of_state.cpp:242-268 at
snapy@e894700ff7aee30b52882e5202b16461413780b0. It reads no data.
"""
from snapy_report import figstyle as fs
import matplotlib.pyplot as plt


def make_fig():
    fig, ax = fs.new_figure(fs.SINGLE, 2.6)
    ax.set_axis_off()
    ax.add_patch(plt.Rectangle((0, 0), 2.4, 1.9, fc="#EAF5FC", ec=fs.BLACK, lw=0.9))
    ax.text(1.2, 2.06, "one cell", ha="center", fontsize=fs.SMALL_PT)
    ax.add_patch(plt.Rectangle((0.25, 1.05), 0.8, 0.62, fc="white", ec=fs.SKY, lw=1.3))
    ax.text(0.65, 1.36, "vapour", ha="center", va="center", fontsize=fs.SMALL_PT, color=fs.SKY)
    ax.add_patch(plt.Rectangle((1.35, 1.05), 0.8, 0.62, fc="white", ec=fs.VERMILLION, lw=1.3))
    ax.text(1.75, 1.36, "cloud\n$<0$", ha="center", va="center", fontsize=fs.SMALL_PT,
            color=fs.VERMILLION)
    ax.annotate("", xy=(1.35, 0.78), xytext=(1.05, 0.78),
                arrowprops=dict(arrowstyle="->", color=fs.GREEN, lw=1.6))
    ax.text(1.2, 0.52, "borrow the deficit", ha="center", fontsize=fs.SMALL_PT, color=fs.GREEN)
    ax.text(1.2, 0.24, "mass, energy and elements\nunchanged in this cell",
            ha="center", fontsize=fs.SMALL_PT)
    ax.set_xlim(-0.2, 2.6); ax.set_ylim(-0.1, 2.3)
    return fig
