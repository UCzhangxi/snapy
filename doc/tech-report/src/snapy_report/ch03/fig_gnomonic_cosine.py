"""cos psi = -XY/(CD) over one gnomonic panel (src/coord/gnomonic_equiangle.cpp:75-80 at snapy@e894700ff7aee30b52882e5202b16461413780b0).

Analytic; it reads no data.
"""
import numpy as np
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.9))
    a = np.linspace(-np.pi / 4, np.pi / 4, 201)
    xi, eta = np.meshgrid(a, a, indexing="xy")
    X, Y = np.tan(xi), np.tan(eta)
    c = -X * Y / (np.sqrt(1 + X * X) * np.sqrt(1 + Y * Y))
    levels = np.linspace(-0.5, 0.5, 11)
    cs = ax.contourf(np.degrees(xi), np.degrees(eta), c, levels=levels, cmap="cividis")
    ax.contour(np.degrees(xi), np.degrees(eta), c, levels=levels, colors=fs.BLACK, linewidths=0.4)
    cb = fig.colorbar(cs, ax=ax, ticks=[-0.5, -0.25, 0, 0.25, 0.5])
    cb.set_label(r"$\cos\psi$ [-]")
    ax.set_xlabel(r"$\xi$ [deg]")
    ax.set_ylabel(r"$\eta$ [deg]")
    ax.set_aspect("equal")
    return fig
