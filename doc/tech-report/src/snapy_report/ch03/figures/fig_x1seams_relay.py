"""A column split into three x1 blocks: reference relay, ghost-row copies and seam-flux averaging.

Mechanisms of src/hydro/hydro.cpp:517-662 (HydroImpl::_hydro_ref_x1) and src/hydro/hydro_forward.cpp:508-582 at snapy@6fbb39750f62b83df096058a4746e77d0a634bc5. A cartoon; it reads no data.
"""

from snapy_report import figstyle as fs


def make_fig():
    fig, ax = fs.new_figure(fs.SINGLE, 3.4)
    for b in range(3):
        y0 = 1.3 * b
        fs.cell_box(ax, 0, y0, 1.2, 1.0)
        fs.cell_box(ax, 0, y0 - 0.15, 1.2, 0.15, ghost=True)
        fs.cell_box(ax, 0, y0 + 1.0, 1.2, 0.15, ghost=True)
        ax.text(0.6, y0 + 0.5, "block %d" % b, ha="center", va="center", fontsize=fs.SMALL_PT)
    for s in (1, 2):
        y = 1.3 * s - 0.15
        ax.annotate("", xy=(1.45, y - 0.05), xytext=(1.45, y + 0.35),
                    arrowprops=dict(arrowstyle="->", color=fs.BLACK, lw=1.0))
        ax.text(1.55, y + 0.1, "relay", fontsize=fs.SMALL_PT, va="center")
        ax.annotate("", xy=(-0.25, y + 0.15), xytext=(-0.25, y - 0.25),
                    arrowprops=dict(arrowstyle="->", color=fs.PURPLE, lw=1.0))
        ax.annotate("", xy=(-0.45, y - 0.0), xytext=(-0.45, y + 0.4),
                    arrowprops=dict(arrowstyle="->", color=fs.PURPLE, lw=1.0))
        ax.plot(0.45, y + 0.07, "^", color=fs.ORANGE, ms=5)
        ax.plot(0.75, y + 0.07, "v", color=fs.ORANGE, ms=5)
    ax.text(-0.35, 3.9, "ghost rows", fontsize=fs.SMALL_PT, color=fs.PURPLE, ha="center")
    ax.text(0.6, 4.3, "top anchors the scan", fontsize=fs.SMALL_PT, ha="center")
    ax.set(xlim=(-0.9, 2.3), ylim=(-0.3, 4.5))
    ax.axis("off")
    return fig
