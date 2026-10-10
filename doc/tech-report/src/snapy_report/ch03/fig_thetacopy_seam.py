"""A seam face with its donor on panel A: raw-copied factor (top) and interpolated blend (bottom).

Mechanism of src/hydro/hydro_forward.cpp:671-698 at snapy@e894700ff7aee30b52882e5202b16461413780b0. A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.8))
    for y, ghost_label, leak in ((1.4, r"$\Theta_A$", False), (0.0, r"$\tilde\Theta$", True)):
        fs.cell_box(ax, -1, y)
        fs.cell_box(ax, 0, y, ghost=True)
        ax.plot([0, 0], [y - 0.05, y + 1.05], color=fs.PURPLE, ls="--", lw=1.4)
        ax.text(-0.5, y + 0.5, r"donor $\Theta_A$", ha="center", va="center", fontsize=8)
        ax.text(0.5, y + 0.5, "B ghost " + ghost_label, ha="center", va="center", fontsize=8)
        ax.annotate("", xy=(0.35, y + 0.15), xytext=(-0.35, y + 0.15),
                    arrowprops=dict(arrowstyle="->", color=fs.ORANGE, lw=1.2))
        if leak:
            ax.text(1.08, y + 0.5, "leak\n" + r"$(\Theta_A-\tilde\Theta)\mathcal{F}$", fontsize=8,
                    color=fs.VERMILLION, va="center")
        else:
            ax.text(1.08, y + 0.5, "single-valued", fontsize=8, color=fs.GREEN, va="center")
    ax.text(-1.0, 2.55, "raw copy", fontsize=8)
    ax.text(-1.0, 1.15, "interpolated", fontsize=8)
    ax.set(xlim=(-1.1, 2.1), ylim=(-0.1, 2.7))
    ax.axis("off")
    return fig
