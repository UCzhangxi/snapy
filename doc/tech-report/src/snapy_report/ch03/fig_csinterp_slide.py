"""Ghost centres of layers 1-3 beyond a panel edge and their interpolation sources on the neighbouring panel.

Source angle tan(eta') = tan(eta) / tan(xi), as cs_build_ghost_usrc computes it (src/coord/cubed_sphere_utils.cpp:78-108)
at snapy@e894700ff7aee30b52882e5202b16461413780b0, for 16 cells per edge. Computed; it reads no data.
"""
import numpy as np
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 3.2))
    N, ng = 16, 3
    d = np.pi / (2 * N)
    eta = -np.pi / 4 + (np.arange(N) + 0.5) * d
    fs.wall(ax, 0.0, -N / 2, N / 2)
    for g in range(1, ng + 1):
        xi = np.pi / 4 + (g - 0.5) * d
        src = np.arctan(np.tan(eta) / np.tan(xi))
        y_ghost, y_src = eta / d, src / d
        x = g - 0.5
        ax.plot(np.full(N, x), y_ghost, "o", mfc="white", mec=fs.PURPLE, ms=4)
        ax.plot(np.full(N, -x), y_src, "o", color=fs.SKY, mec=fs.BLACK, mew=0.4, ms=4)
        for a, b in zip(y_ghost, y_src):
            ax.annotate("", xy=(-x + 0.15, b), xytext=(x - 0.15, a),
                        arrowprops=dict(arrowstyle="->", color=fs.GREEN, lw=0.5))
    ax.text(1.5, N / 2 + 0.4, "ghosts, layer 1-3", ha="center", fontsize=8)
    ax.text(-1.5, N / 2 + 0.4, "sources", ha="center", fontsize=8)
    ax.set_xlabel("distance from the edge [cells]")
    ax.set_ylabel("along-edge position [cells]")
    ax.set(xlim=(-3.2, 3.2), ylim=(-N / 2 - 0.5, N / 2 + 1.2))
    return fig
