"""Donor choice of the implicit tracer transfer at one x1 face; snapy@6fbb39750f62b83df096058a4746e77d0a634bc5.

Cartoon of src/mesh/meshblock.cpp:661-676 (claim C3 of tracer_check.py); no measured data.
"""

from snapy_report import figstyle as fs


def make_fig():
    fig, axes = fs.new_figure(fs.DOUBLE, 2.4, 1, 2)
    for ax, sign, title in zip(axes, (1, -1), ("(a) $M>0$: upward", "(b) $M<0$: downward")):
        ax.set(xlim=(0, 3), ylim=(0, 2.2))
        ax.axis("off")
        fs.cell_box(ax, 1, 0.05, 1, 1)
        fs.cell_box(ax, 1, 1.05, 1, 1)
        fs.cell_value(ax, 1.5, 0.55)
        fs.cell_value(ax, 1.5, 1.55)
        ax.text(1.65, 0.55, "$r_{n,i-1}$", va="center", fontsize=fs.SMALL_PT)
        ax.text(1.65, 1.55, "$r_{n,i}$", va="center", fontsize=fs.SMALL_PT)
        fs.face_value(ax, 2.0, 1.05)
        ax.text(2.1, 1.05, r"face $i-\frac{1}{2}$", va="center", fontsize=fs.SMALL_PT)
        y0, y1 = (0.75, 1.35) if sign > 0 else (1.35, 0.75)
        ax.annotate("", xy=(1.2, y1), xytext=(1.2, y0), arrowprops=dict(arrowstyle="->", color=fs.ORANGE, lw=1.6))
        donor = "$r_{n,i-1}M$" if sign > 0 else "$r_{n,i}M$"
        ax.text(0.15, 1.05, donor, va="center", fontsize=fs.SMALL_PT, color=fs.BLACK)
        ax.set_title(title, fontsize=fs.LABEL_PT, loc="left")
    return fig
