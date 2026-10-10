"""A column split into three x1 blocks: reference relay, ghost-row copies and seam-flux averaging.

Mechanisms of src/hydro/hydro.cpp:502-640 and src/hydro/hydro_forward.cpp:425-499 at snapy@e894700ff7aee30b52882e5202b16461413780b0. A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 3.4))
    for b in range(3):
        y0 = 1.3 * b
        fs.cell_box(ax, 0, y0, 1.2, 1.0)
        fs.cell_box(ax, 0, y0 - 0.15, 1.2, 0.15, ghost=True)
        fs.cell_box(ax, 0, y0 + 1.0, 1.2, 0.15, ghost=True)
        ax.text(0.6, y0 + 0.5, "block %d" % b, ha="center", va="center", fontsize=8)
    for s in (1, 2):
        y = 1.3 * s - 0.15
        ax.annotate("", xy=(1.45, y - 0.05), xytext=(1.45, y + 0.35),
                    arrowprops=dict(arrowstyle="->", color=fs.BLACK, lw=1.0))
        ax.text(1.55, y + 0.1, "relay", fontsize=8, va="center")
        ax.annotate("", xy=(-0.25, y + 0.15), xytext=(-0.25, y - 0.25),
                    arrowprops=dict(arrowstyle="->", color=fs.PURPLE, lw=1.0))
        ax.annotate("", xy=(-0.45, y - 0.0), xytext=(-0.45, y + 0.4),
                    arrowprops=dict(arrowstyle="->", color=fs.PURPLE, lw=1.0))
        ax.plot(0.45, y + 0.07, "^", color=fs.ORANGE, ms=5)
        ax.plot(0.75, y + 0.07, "v", color=fs.ORANGE, ms=5)
    ax.text(-0.35, 3.9, "ghost rows", fontsize=8, color=fs.PURPLE, ha="center")
    ax.text(0.6, 3.95, "top anchors the scan", fontsize=8, ha="center")
    ax.set(xlim=(-0.9, 2.3), ylim=(-0.3, 4.1))
    ax.axis("off")
    return fig
