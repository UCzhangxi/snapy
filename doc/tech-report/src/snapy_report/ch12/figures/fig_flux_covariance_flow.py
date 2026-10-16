"""Deterministic labelled configuration diagram; no measured data."""
import matplotlib.pyplot as plt
from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 3.4))
    labels = ['cell centroid', 'face centroid: shift', 'x1 covariance + shift', 'x2 or x3 flux', 'matching source gate']
    for n, label in enumerate(labels):
        y = len(labels)-1-n
        ax.text(.5, y, label, ha="center", va="center", fontsize=8,
                bbox=dict(boxstyle="round,pad=.45", fc=fs.SKY if n % 2 == 0 else fs.GREEN, ec=fs.BLACK))
        if n+1 < len(labels):
            ax.annotate("", xy=(.5,y-.72), xytext=(.5,y-.25),
                        arrowprops=dict(arrowstyle="->", color=fs.BLACK))
    ax.set(xlim=(0,1), ylim=(-.5,len(labels)-.5))
    ax.axis("off")
    return fig
