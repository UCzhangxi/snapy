"""Where a reconstruction writes, and which rows take which interpolant.

Cartoon of _apply_inplace (src/recon/reconstruct.cpp:50-65) and
ReconstructImpl::forward (:79-158) at
snapy@e894700ff7aee30b52882e5202b16461413780b0. It reads no data.
"""
from snapy_report import figstyle as fs
import matplotlib.pyplot as plt


def make_fig():
    fs.apply()
    fig, axes = plt.subplots(1, 2, figsize=(fs.DOUBLE, 2.3))
    a = axes[0]
    a.set_axis_off()
    a.set_aspect("equal")
    for i in range(6):
        ghost = i < 2 or i > 3
        a.add_patch(plt.Rectangle((i, 0), 1, 1, fc="#F7E6EF" if ghost else "#EAF5FC",
                                  ec=fs.BLACK, lw=0.7, hatch="//" if ghost else None))
        a.plot(i + 0.5, 0.5, "o", color=fs.SKY, ms=4, mec=fs.BLACK, mew=0.4)
    for i, lab in ((2, "$i_l$"), (3, "$i_u$")):
        a.text(i + 0.5, -0.3, lab, ha="center", fontsize=8)
    for f, lab in ((2, "$i_l$"), (4, "$i_u{+}1$")):
        a.plot(f, 0.5, "^", color=fs.ORANGE, ms=7, mec=fs.BLACK, mew=0.5)
        a.text(f, 1.25, lab, ha="center", fontsize=7, color=fs.ORANGE)
    a.text(3.0, 1.62, "faces the solver reads", ha="center", fontsize=7, color=fs.ORANGE)
    a.set_title("(a) face index map", loc="left")
    a.set_xlim(-0.4, 6.4)
    a.set_ylim(-0.7, 2.0)

    b = axes[1]
    b.set_axis_off()
    rows = [("density", "interp1", fs.GREEN), ("velocity", "interp2", fs.BLUE),
            ("pressure", "interp2", fs.BLUE), ("tracers", "interp1", fs.GREEN)]
    for j, (row, which, col) in enumerate(rows):
        y = len(rows) - 1 - j
        b.text(0.0, y, row, fontsize=8, va="center")
        b.annotate("", xy=(1.55, y), xytext=(0.95, y),
                   arrowprops=dict(arrowstyle="->", color=col, lw=1.3))
        b.text(1.65, y, which, fontsize=8, va="center", color=col)
    b.text(0.0, -1.05, "with shock: true every row takes interp1", fontsize=7)
    b.set_title("(b) which rows take which interpolant", loc="left")
    b.set_xlim(-0.1, 3.0)
    b.set_ylim(-1.6, 3.6)
    return fig
