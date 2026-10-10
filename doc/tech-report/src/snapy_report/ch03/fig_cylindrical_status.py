"""Status of the coordinate types at snapy@e894700ff7aee30b52882e5202b16461413780b0 (src/coord/coordinate.cpp:593-610). A cartoon; it reads no data."""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 0.9))
    types = ["cartesian", "spherical-polar", "gnomonic-equiangle", "cylindrical"]
    for n, t in enumerate(types):
        ok = t != "cylindrical"
        ax.text(n, 0, t + ("\nbuilds a metric" if ok else "\nno metric"), ha="center", va="center", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.4", fc=fs.GREEN if ok else "white",
                          ec=fs.BLACK, alpha=0.5, hatch=None if ok else "xx"))
    ax.set(xlim=(-0.6, 3.6), ylim=(-0.6, 0.6))
    ax.axis("off")
    return fig
