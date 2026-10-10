"""Cell-local flow; snapy e894700ff7aee30b52882e5202b16461413780b0. No measured data."""
import matplotlib.pyplot as plt
from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 3.1))
    labels = ['primitive identity + version', 'reuse or refresh cache', 'partial densities + temperature', 'energy / gamma / speed']
    for n, label in enumerate(labels):
        y = 3-n
        ax.text(.5, y, label, ha="center", va="center", fontsize=8,
                bbox=dict(boxstyle="round,pad=.5", fc=fs.SKY if n in (0,3) else fs.GREEN, ec=fs.BLACK))
        if n < 3:
            ax.annotate("", xy=(.5,y-.72), xytext=(.5,y-.25), arrowprops=dict(arrowstyle="->", color=fs.BLACK))
    ax.set(xlim=(0,1), ylim=(-.4,3.4))
    ax.axis("off")
    return fig
