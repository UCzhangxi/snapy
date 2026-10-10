"""Donor choice of the implicit tracer transfer at one x1 face; snapy@e894700ff7aee30b52882e5202b16461413780b0.

Cartoon of src/mesh/meshblock.cpp:661-676 (claims C3-C4 of tracer_check.py); no measured data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, axes = plt.subplots(1, 2, figsize=(fs.DOUBLE, 2.4))
    for ax, sign, title in zip(axes, (1, -1), ("(a) $M>0$: upward", "(b) $M<0$: downward")):
        ax.set(xlim=(0, 3), ylim=(0, 2.2))
        ax.axis("off")
        fs.cell_box(ax, 1, 0.05, 1, 1)
        fs.cell_box(ax, 1, 1.05, 1, 1)
        fs.cell_value(ax, 1.5, 0.55)
        fs.cell_value(ax, 1.5, 1.55)
        ax.text(1.65, 0.55, "$r_{n,i-1}$", va="center", fontsize=8)
        ax.text(1.65, 1.55, "$r_{n,i}$", va="center", fontsize=8)
        fs.face_value(ax, 2.0, 1.05)
        ax.text(2.1, 1.05, r"face $i-\frac{1}{2}$", va="center", fontsize=8)
        y0, y1 = (0.75, 1.35) if sign > 0 else (1.35, 0.75)
        ax.annotate("", xy=(1.2, y1), xytext=(1.2, y0), arrowprops=dict(arrowstyle="->", color=fs.ORANGE, lw=1.6))
        donor = "$r_{n,i-1}M$" if sign > 0 else "$r_{n,i}M$"
        ax.text(0.15, 1.05, donor, va="center", fontsize=8, color=fs.BLACK)
        ax.set_title(title, fontsize=9, loc="left")
    fig.tight_layout()
    return fig
