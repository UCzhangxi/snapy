"""(a) Morton rank order of a 4x4 block grid; (b) the cubed-sphere face numbering.

From build_zorder_coords2 (src/layout/connectivity.cpp:28-43) and CS_FACE_NAMES with the net of
src/layout/cubed_sphere_layout.cpp:207-246 at snapy@e894700ff7aee30b52882e5202b16461413780b0. A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def _compact(x):
    x &= 0x55555555
    x = (x ^ (x >> 1)) & 0x33333333
    x = (x ^ (x >> 2)) & 0x0F0F0F0F
    x = (x ^ (x >> 4)) & 0x00FF00FF
    return (x ^ (x >> 8)) & 0x0000FFFF


def make_fig():
    fs.apply()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(fs.DOUBLE, 2.8))
    pts = [(_compact(c), _compact(c >> 1)) for c in range(16)]
    for rank, (x, y) in enumerate(pts):
        fs.cell_box(a1, x, y)
        a1.text(x + 0.5, y + 0.5, str(rank), ha="center", va="center", fontsize=8)
    a1.plot([x + 0.5 for x, _ in pts], [y + 0.5 for _, y in pts], color=fs.GREEN, lw=1.0)
    a1.set_xlabel(r"$r_x$ (along $x_2$)")
    a1.set_ylabel(r"$r_y$ (along $x_3$)")
    a1.set(xlim=(0, 4), ylim=(0, 4), aspect="equal", xticks=[0.5, 1.5, 2.5, 3.5], yticks=[0.5, 1.5, 2.5, 3.5])
    a1.set_xticklabels(range(4))
    a1.set_yticklabels(range(4))
    a1.text(-0.12, 1.02, "(a)", transform=a1.transAxes, fontsize=9)
    names = ["+X", "+Y", "-X", "+Z", "-Y", "-Z"]
    pos = {4: (0, 1), 0: (1, 1), 1: (2, 1), 2: (3, 1), 3: (1, 2), 5: (1, 0)}
    for f, (x, y) in pos.items():
        fs.cell_box(a2, x, y)
        a2.text(x + 0.5, y + 0.55, "%d  %s" % (f, names[f]), ha="center", va="center", fontsize=8)
    a2.set(xlim=(-0.1, 4.1), ylim=(-0.1, 3.0), aspect="equal")
    a2.axis("off")
    a2.text(0.0, 1.02, "(b)", transform=a2.transAxes, fontsize=9)
    return fig
