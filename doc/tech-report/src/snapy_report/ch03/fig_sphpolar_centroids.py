"""A spherical-polar shell cell with its midpoint, volume centroid and face-measure centroid.

Positions from src/coord/spherical_polar.cpp:17-21 and src/coord/coordinate.cpp:467-488 at snapy@e894700ff7aee30b52882e5202b16461413780b0, for a thick cell
r in [1, 2] so that the three marks separate. A cartoon; it reads no data.
"""
import numpy as np
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.8))
    rm, rp = 1.0, 2.0
    t = np.linspace(np.pi / 2 - 0.35, np.pi / 2 + 0.35, 60)
    for r in (rm, rp):
        ax.plot(r * np.cos(t), r * np.sin(t), color=fs.BLACK, lw=1.0)
    for a in (t[0], t[-1]):
        ax.plot([rm * np.cos(a), rp * np.cos(a)], [rm * np.sin(a), rp * np.sin(a)], color=fs.BLACK, lw=1.0)
    mid = 0.5 * (rm + rp)
    rv = 0.75 * (rp**4 - rm**4) / (rp**3 - rm**3)
    rc = (2.0 / 3.0) * (rp**3 - rm**3) / (rp**2 - rm**2)
    marks = ((mid, "midpoint", "s", fs.GREY, 1.25), (rc, "face centroid", "^", fs.ORANGE, 1.55),
             (rv, "volume centroid", "o", fs.SKY, 1.85))
    for r, lab, mk, col, ylab in marks:
        ax.plot(0, r, mk, color=col, mec=fs.BLACK, mew=0.5, ms=6)
        ax.plot([0.05, 0.45], [r, ylab], color=col, lw=0.6)
        ax.text(0.48, ylab, "%s, r = %.3f" % (lab, r), va="center", fontsize=8)
    ax.annotate("", xy=(0.0, rp + 0.25), xytext=(0.0, rp - 0.1),
                arrowprops=dict(arrowstyle="->", color=fs.GREEN))
    ax.text(0.05, rp + 0.12, r"radial source $\langle r^{-1}\rangle$", fontsize=8, color=fs.GREEN)
    ax.set(xlim=(-0.9, 2.1), ylim=(0.8, 2.45), aspect="equal")
    ax.axis("off")
    return fig
