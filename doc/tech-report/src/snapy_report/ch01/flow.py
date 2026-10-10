"""Labelled call/data cartoons; no live simulation and no measured data."""
import matplotlib.pyplot as plt
from snapy_report import figstyle as fs


def make_flow(labels):
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 0.65 * len(labels)))
    ax.set(xlim=(0, 1), ylim=(-0.6, len(labels)-0.4))
    ax.axis("off")
    for index, label in enumerate(labels):
        y = len(labels)-1-index
        ax.text(0.5, y, label, ha="center", va="center", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor=fs.GREEN))
        if index < len(labels)-1:
            ax.annotate("", xy=(0.5, y-0.66), xytext=(0.5, y-0.34),
                        arrowprops=dict(arrowstyle="->", color=fs.BLACK))
    fig.tight_layout()
    return fig


def make_tree(root_label, branches):
    """One owner requiring independent services; branches do not call each other."""
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 3.2))
    ax.set(xlim=(-0.05, 1.05), ylim=(-0.2, 1.1))
    ax.axis('off')
    ax.text(0.2, 0.5, root_label, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor=fs.GREEN))
    for index, label in enumerate(branches):
        y = 1-index/max(1,len(branches)-1)
        ax.text(0.72, y, label, ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor=fs.GREEN))
        ax.annotate('', xy=(0.52,y), xytext=(0.31,0.5),
                    arrowprops=dict(arrowstyle='->',color=fs.BLACK))
    fig.tight_layout()
    return fig
