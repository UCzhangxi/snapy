"""The 3x3 neighbour stencil of a block with the buffer id of each offset (get_buffer_id,
src/layout/layout.hpp:32-35 at snapy@e894700ff7aee30b52882e5202b16461413780b0); face slabs exchanged, corners synthesised. A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 3.0))
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            bid = (dx % 3) + (dy % 3) * 3
            corner = abs(dx) + abs(dy) == 2
            fs.cell_box(ax, dx, dy, 0.92, 0.92, ghost=(dx, dy) != (0, 0))
            col = fs.PURPLE if corner else fs.BLACK
            ax.text(dx + 0.46, dy + 0.6, "id %d" % bid, ha="center", fontsize=8, color=col)
            if corner:
                ax.text(dx + 0.46, dy + 0.3, "synthesised", ha="center", fontsize=7.5, color=fs.PURPLE)
            elif (dx, dy) != (0, 0):
                ax.annotate("", xy=(0.46 + 0.3 * dx, 0.46 + 0.3 * dy), xytext=(dx + 0.46 - 0.2 * dx, dy + 0.46 - 0.2 * dy),
                            arrowprops=dict(arrowstyle="->", color=fs.ORANGE, lw=1.2))
    ax.text(0.46, 0.2, "block", ha="center", fontsize=8)
    ax.set_xlabel(r"offset in $x_2$")
    ax.set_ylabel(r"offset in $x_3$")
    ax.set(xlim=(-1.1, 2.0), ylim=(-1.1, 2.0), aspect="equal", xticks=[-0.54, 0.46, 1.46], yticks=[-0.54, 0.46, 1.46])
    ax.set_xticklabels(["-1", "0", "+1"])
    ax.set_yticklabels(["-1", "0", "+1"])
    return fig
