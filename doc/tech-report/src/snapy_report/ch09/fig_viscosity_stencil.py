"""The stencil of the viscous and conductive x1 face flux on a 2-D Cartesian grid.

Drawn from DiffusionImpl::forward, src/forcing/diffusion.cpp:504-562, with the helpers at
:70-108, at snapy@e894700ff7aee30b52882e5202b16461413780b0. A cartoon; it reads no data.
"""
from matplotlib.patches import Rectangle

from snapy_report.ch09._style import BLACK, CELL_FILL, GREEN, ORANGE, SKY, DOUBLE, new_figure


def make_fig():
    fig, ax = new_figure(DOUBLE, 2.8)
    ax.set_axis_off()
    ax.set_aspect("equal")
    for i in range(4):
        for j in range(3):
            ax.add_patch(Rectangle((i, j), 1, 1, fc=CELL_FILL, ec=BLACK, lw=0.6))
            ax.plot(i + 0.5, j + 0.5, "o", color=SKY, ms=5, mec=BLACK, mew=0.5)
    for i, lab in enumerate(["$i-2$", "$i-1$", "$i$", "$i+1$"]):
        ax.text(i + 0.5, -0.25, lab, ha="center", fontsize=8)
    for j, lab in enumerate(["$j-1$", "$j$", "$j+1$"]):
        ax.text(-0.3, j + 0.5, lab, va="center", ha="center", fontsize=8)
    # x1 face i-1/2 between cells i-1 and i, row j
    ax.plot([2, 2], [1, 2], color=ORANGE, lw=2.5)
    ax.plot(2, 1.5, "^", color=ORANGE, ms=7, mec=BLACK, mew=0.5)
    ax.text(2.05, 2.1, "$i-\\frac{1}{2}$", fontsize=8, color=ORANGE)
    # face-normal derivative: the two cells across the face
    ax.annotate("", xy=(2.5, 1.5), xytext=(1.5, 1.5),
                arrowprops=dict(arrowstyle="<->", color=GREEN, lw=1.2))
    # cross term: centred x2 derivatives in cells i-1 and i
    for i in (1.5, 2.5):
        ax.annotate("", xy=(i, 2.5), xytext=(i, 0.5),
                    arrowprops=dict(arrowstyle="<->", color=BLACK, lw=0.8, ls="--"))
    ax.text(4.3, 2.3, "green: $\\partial_1 v$ across the face (two cells)", fontsize=8)
    ax.text(4.3, 1.75, "dashed: $\\partial_2 v_1$ centred in $i-1$ and $i$, averaged", fontsize=8)
    ax.text(4.3, 1.2, "orange: face value; coefficient $\\rho$ or $\\rho c_v$ is the", fontsize=8)
    ax.text(4.3, 0.85, "two-cell average (one-sided at a wall)", fontsize=8)
    ax.set_xlim(-0.6, 9.5)
    ax.set_ylim(-0.5, 3.1)
    return fig
