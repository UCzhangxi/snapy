"""Even-parity perturbation ghosts at a reflecting x1 wall (chapter 5, the well-balanced x1 reconstruction).

Shows the bottom wall, three owned cells and three ghost cells: the perturbations p' and rho' are mirrored with even
parity into the ghosts, the normal velocity with odd parity. Cartoon; no data. Code it depicts:
snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy), src/hydro/hydro_forward.cpp lines 295-312.
"""
import numpy as np

from snapy_report.ch05 import _style as fs
from snapy_report.ch05 import _draw as d


def make_fig():
    fig, ax = fs.new_figure("double", 2.0)
    fs.cartoon(ax)
    vals = [0.62, 0.38, 0.52]                     # p' in cells i_s, i_s+1, i_s+2 (heights in the box)
    vel = [0.25, -0.18, 0.12]                     # v_1 in the same cells (arrow lengths)
    for y0, kind in ((1.25, "p"), (0.0, "v")):
        d.row(ax, 0, 2, y=y0, ghosts_lo=3, labels=None)
        d.wall_at(ax, 0.0, y=y0)
        for k in range(3):
            for xc, sgn in ((k + 0.5, 1.0), (-k - 0.5, -1.0)):
                if kind == "p":
                    fs.cell_value(ax, xc, y0 + vals[k])
                else:
                    v = vel[k] * (1.0 if sgn > 0 else -1.0)
                    d.arrow(ax, (xc, y0 + 0.5 - v), (xc, y0 + 0.5 + v), color=fs.BLACK)
    d.text(ax, 3.45, 1.75, "$p'$, $\\rho'$: even", ha="left")
    d.text(ax, 3.45, 0.5, "$v_1$: odd", ha="left")
    for k, lab in enumerate(("$i_s$", "$i_s+1$", "$i_s+2$")):
        d.text(ax, k + 0.5, -0.35, lab)
    for k, lab in enumerate(("$i_s-1$", "$i_s-2$", "$i_s-3$")):
        d.text(ax, -k - 0.5, -0.35, lab)
    d.text(ax, 0.0, 2.65, "wall $i_s-1/2$")
    ax.set_xlim(-3.3, 5.2)
    ax.set_ylim(-0.6, 2.85)
    return fig
