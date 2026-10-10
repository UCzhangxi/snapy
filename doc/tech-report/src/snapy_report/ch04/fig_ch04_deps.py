"""The dependency map of chapter 4: which scheme requires, implies or disables which.

Cartoon. Every edge is stated and cited in the scheme section it comes from; this figure
only collects them. It reads no data.
"""
from snapy_report import figstyle as fs
import matplotlib.pyplot as plt

# (x, y, label)
NODES = {
    "divergence": (0.5, 2.6, "flux\ndivergence"),
    "recon": (0.5, 1.3, "reconstruction\nframework"),
    "weno": (2.0, 1.9, "weno3\nweno5"),
    "cp": (3.5, 1.3, "cp3\ncp5"),
    "riemann": (0.5, 0.0, "Riemann\nframework"),
    "facep": (2.0, 0.0, "face\npressure"),
    "sources": (3.5, 0.6, "geometric\nsources"),
    "seam": (2.0, 2.9, "seam\naveraging"),
    "fluxcov": (5.0, 1.9, "flux\ncovariance"),
    "x1cov": (5.0, 0.5, "$x_1$ mass\ncovariance"),
}
# (from, to, kind): kind in {"requires", "implies", "disables"}
EDGES = [
    ("recon", "weno", "implies"), ("weno", "cp", "implies"),
    ("riemann", "facep", "implies"), ("facep", "sources", "requires"),
    ("divergence", "seam", "requires"),
    ("fluxcov", "facep", "requires"), ("fluxcov", "sources", "requires"),
    ("x1cov", "recon", "requires"),
]
STYLE = {"requires": (fs.BLACK, "-"), "implies": (fs.GREEN, "--"),
         "disables": (fs.VERMILLION, ":")}


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 2.9))
    ax.set_axis_off()
    for a, b, kind in EDGES:
        col, ls = STYLE[kind]
        x0, y0, _ = NODES[a]
        x1, y1, _ = NODES[b]
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="->", color=col, ls=ls, lw=1.1,
                                    shrinkA=22, shrinkB=22, alpha=0.9))
    for key, (x, y, lab) in NODES.items():
        ax.text(x, y, lab, ha="center", va="center", fontsize=7,
                bbox=dict(boxstyle="round,pad=0.32", fc="white", ec=fs.BLACK, lw=0.8))
    for i, (kind, (col, ls)) in enumerate(STYLE.items()):
        ax.plot([], [], color=col, ls=ls, lw=1.1, label=kind)
    ax.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.12))
    ax.set_xlim(-0.6, 6.1)
    ax.set_ylim(-0.8, 3.5)
    return fig
