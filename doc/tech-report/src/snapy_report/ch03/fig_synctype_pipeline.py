"""The velocity path of a conserved strip across a panel edge (src/layout/cubed_sphere_layout.cpp:736-753, 934-956
and src/coord/cubed_sphere_utils.cpp:259-298 at snapy@e894700ff7aee30b52882e5202b16461413780b0). A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 1.3))
    steps = ["raise", "to spherical", "relabel, send", "interpolate", "to panel", "lower"]
    cols = [fs.GREEN, fs.SKY, fs.ORANGE, fs.BLUE, fs.SKY, fs.GREEN]
    for n, (s, c) in enumerate(zip(steps, cols)):
        ax.text(n, 0, s, ha="center", va="center", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.4", fc=c, ec=fs.BLACK, alpha=0.5))
        if n + 1 < len(steps):
            ax.annotate("", xy=(n + 0.62, 0), xytext=(n + 0.38, 0),
                        arrowprops=dict(arrowstyle="->", color=fs.BLACK))
    ax.text(1.0, -0.55, "sender", ha="center", fontsize=8)
    ax.text(4.0, -0.55, "receiver", ha="center", fontsize=8)
    ax.text(0.0, 0.5, "conserved only", ha="center", fontsize=7.5)
    ax.text(5.0, 0.5, "conserved only", ha="center", fontsize=7.5)
    ax.set(xlim=(-0.6, 5.6), ylim=(-0.8, 0.8))
    ax.axis("off")
    return fig
