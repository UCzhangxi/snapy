"""Stencil of the corrected-PE face work: interior cell, wall cell, x1 seam, and the VIC energy row.

Cartoon of corrected_pe_work and centroid_slope (src/hydro/gravity_work_radial.hpp) and of the tridiagonal coupling
of src/implicit/implicit_hydro.cpp:301-333 at snapy@e894700ff7aee30b52882e5202b16461413780b0; no measured data.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

from snapy_report import figstyle as fs


def row(ax, x0, labels, ghost=(), slope=(), faces=()):
    for k, lab in enumerate(labels):
        fs.cell_box(ax, x0 + k, 0., 1., 1., ghost=k in ghost)
        ax.text(x0 + k + .5, -.28, lab, ha="center", va="center", fontsize=8)
        if k in slope:
            ax.plot(x0 + k + .5, .5, "o", color=fs.GREEN, ms=6)
    for f in faces:
        fs.face_value(ax, x0 + f, .5)


def panel(ax, title):
    ax.set_axis_off()
    ax.set_title(title, fontsize=9, loc="left")
    ax.set(xlim=(-.3, 5.3), ylim=(-.7, 1.4))


def make_fig():
    fs.apply()
    fig, axes = plt.subplots(2, 2, figsize=(fs.DOUBLE, 3.6))
    a, b, c, d = axes.ravel()
    panel(a, "(a) interior cell")
    row(a, 1, ["i-1", "i", "i+1"], slope=(0, 1, 2), faces=(2, 3))
    panel(b, "(b) bottom wall cell")
    row(b, 0, ["ghost", "0", "1", "2"], ghost=(0,), slope=(1, 2, 3), faces=(2,))
    fs.wall(b, 1., -.1, 1.1)
    b.text(1.0, 1.25, "wall, F = 0", ha="center", fontsize=8)
    panel(c, "(c) x1 block seam")
    c.set(xlim=(-.3, 6.3))
    row(c, 0, ["n-3", "n-2", "n-1", "0", "1", "2"], slope=(0, 1, 2, 3, 4, 5), faces=(3,))
    c.plot([3, 3], [-.15, 1.15], ls="--", color=fs.PURPLE, lw=2.)
    c.text(1.5, 1.25, "block A", ha="center", fontsize=8)
    c.text(4.5, 1.25, "block B", ha="center", fontsize=8)
    panel(d, "(d) VIC energy row, total-mass column")
    for k, lab in enumerate(["0", "1", "2"]):
        d.add_patch(Rectangle((1 + k, 0), 1, 1, facecolor="white" if k == 2 else "#EAF5FC", edgecolor=fs.BLACK,
                              hatch="//" if k == 2 else None))
        d.text(1.5 + k, -.28, "col " + lab, ha="center", fontsize=8)
    d.text(.55, .5, "row 0", ha="center", va="center", fontsize=8)
    d.add_patch(FancyArrowPatch((3.5, 1.1), (2.5, 1.1), connectionstyle="arc3,rad=-.5", arrowstyle="-|>",
                                mutation_scale=9, color=fs.GREEN))
    d.text(3.0, -.62, "end weight lumped onto the neighbour", ha="center", fontsize=8)
    fig.tight_layout()
    return fig
