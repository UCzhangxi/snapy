"""What the face form reads for cell i, and the curvature flux zeroed at a wall.

Cartoon of src/hydro/hydro_forward.cpp:794-811 and 828-848 at snapy@e894700ff7aee30b52882e5202b16461413780b0;
no measured data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, axes = plt.subplots(1, 2, figsize=(fs.DOUBLE, 2.2))
    a, b = axes
    for ax in axes:
        ax.set_axis_off()
        ax.set(xlim=(-.3, 4.3), ylim=(-.9, 1.6))
    a.set_title("(a) face form, cell i", fontsize=9, loc="left")
    for k, lab in enumerate(["i-1", "i", "i+1"]):
        fs.cell_box(a, .5 + k, 0., 1., 1.)
        a.text(1. + k, -.3, lab, ha="center", fontsize=8)
    fs.cell_value(a, 2., .5)
    a.text(2., .72, r"$\phi_i$", ha="center", fontsize=9)
    for x, t, ha in ((1.5, r"$\phi_{i-1/2}F_{i-1/2}$", "right"), (2.5, r"$\phi_{i+1/2}F_{i+1/2}$", "left")):
        fs.face_value(a, x, .5)
        a.text(x, 1.2, t, ha=ha, fontsize=8, color=fs.ORANGE)
    a.text(2., -.75, r"weights $x_{1,i}-x_{1,i-1/2}$ and $x_{1,i+1/2}-x_{1,i}$", ha="center", fontsize=8)
    b.set_title("(b) curvature flux K at the bottom wall", fontsize=9, loc="left")
    fs.cell_box(b, 0., 0., .8, 1., ghost=True)
    for k in range(3):
        fs.cell_box(b, .8 + k, 0., 1., 1.)
        b.text(1.3 + k, -.3, str(k), ha="center", fontsize=8)
    fs.wall(b, .8, -.1, 1.1)
    b.text(.8, 1.25, "K = 0", ha="center", fontsize=8, color=fs.VERMILLION)
    for x in (1.8, 2.8):
        b.plot(x, .5, "^", color=fs.GREEN, ms=6)
        b.text(x, 1.25, "K", ha="center", fontsize=8, color=fs.GREEN)
    b.text(2.3, -.75, "wall cell 0 sees K on one face only: first order", ha="center", fontsize=8)
    fig.tight_layout()
    return fig
