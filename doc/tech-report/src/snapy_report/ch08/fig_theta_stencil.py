"""The outflow a cell is charged for, and which cell's factor scales a face.

Cartoon of flux_positivity_theta and flux_positivity_scale_, src/hydro/flux_positivity.cpp
:22-104 at snapy@e894700ff7aee30b52882e5202b16461413780b0. It reads no data.
"""
from snapy_report import figstyle as fs
import matplotlib.pyplot as plt


def make_fig():
    fs.apply()
    fig, axes = plt.subplots(1, 2, figsize=(fs.DOUBLE, 2.5))
    a = axes[0]
    a.set_axis_off(); a.set_aspect("equal")
    for i in range(3):
        a.add_patch(plt.Rectangle((i, 0), 1, 1, fc="#EAF5FC", ec=fs.BLACK, lw=0.8))
    a.plot(1.5, 0.5, "o", color=fs.SKY, ms=6, mec=fs.BLACK, mew=0.5)
    a.text(1.5, 0.26, "$u_i V_i$", ha="center", fontsize=8, color=fs.SKY)
    # only the OUTGOING parts are summed
    a.annotate("", xy=(0.55, 0.72), xytext=(1.0, 0.72),
               arrowprops=dict(arrowstyle="->", color=fs.VERMILLION, lw=1.6))
    a.annotate("", xy=(2.45, 0.72), xytext=(2.0, 0.72),
               arrowprops=dict(arrowstyle="->", color=fs.VERMILLION, lw=1.6))
    a.annotate("", xy=(1.3, 0.14), xytext=(0.75, 0.14),
               arrowprops=dict(arrowstyle="->", color=fs.GREY, lw=1.1))
    a.text(1.5, 1.14, "$\\mathrm{out}_i=\\sum_f \\max(\\pm AF,0)$",
           ha="center", fontsize=8, color=fs.VERMILLION)
    a.text(0.72, -0.12, "inflow is not charged", fontsize=6.5, color=fs.GREY)
    a.set_title("(a) what the cell is charged for", loc="left")
    a.set_xlim(-0.3, 3.3); a.set_ylim(-0.45, 1.6)

    b = axes[1]
    b.set_axis_off(); b.set_aspect("equal")
    for i in range(2):
        b.add_patch(plt.Rectangle((i, 0), 1, 1, fc="#EAF5FC", ec=fs.BLACK, lw=0.8))
    b.plot([1, 1], [0, 1], color=fs.ORANGE, lw=2.5)
    b.text(0.5, 1.14, "$\\theta_{i-1}$", ha="center", fontsize=8, color=fs.GREEN)
    b.text(1.5, 1.14, "$\\theta_i$", ha="center", fontsize=8, color=fs.BLUE)
    b.annotate("", xy=(1.42, 0.66), xytext=(0.58, 0.66),
               arrowprops=dict(arrowstyle="->", color=fs.GREEN, lw=1.5))
    b.text(1.0, 0.76, "$F>0$", ha="center", fontsize=7, color=fs.GREEN)
    b.annotate("", xy=(0.58, 0.3), xytext=(1.42, 0.3),
               arrowprops=dict(arrowstyle="->", color=fs.BLUE, lw=1.5))
    b.text(1.0, 0.1, "$F\\leq 0$", ha="center", fontsize=7, color=fs.BLUE)
    b.text(1.0, -0.38, "the face takes the factor of the cell it drains",
           ha="center", fontsize=6.5)
    b.set_title("(b) the donor rule", loc="left")
    b.set_xlim(-0.5, 2.5); b.set_ylim(-0.7, 1.6)
    fig.tight_layout()
    return fig
