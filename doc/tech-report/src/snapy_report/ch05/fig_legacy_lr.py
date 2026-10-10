"""The legacy x1 wall routines (chapter 5): the wall-face state copy of the non-well-balanced path.

At the bottom wall face (x1 to the right) the left state's pressure and density are overwritten with the right
state's, so the two sides of the wall face agree; the isentropic ghost fill is drawn struck out because its call is
commented out. Cartoon; no data. Code it depicts: snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy),
src/hydro/hydro.cpp lines 448-460 and src/hydro/hydro_forward.cpp lines 247-250, 378-384.
"""
from snapy_report.ch05 import _style as fs
from snapy_report.ch05 import _draw as d


def make_fig():
    fig, ax = fs.new_figure("single", 1.9)
    fs.cartoon(ax)
    d.row(ax, 0, 2, ghosts_lo=2)
    d.wall_at(ax, 0.0)
    fs.face_value(ax, -0.18, 0.5)
    fs.face_value(ax, 0.18, 0.5)
    d.arrow(ax, (0.2, 0.85), (-0.2, 0.85), color=fs.GREEN, style="-|>")
    d.text(ax, 0.0, 1.5, "$p^{L}, \\rho^{L} \\leftarrow p^{R}, \\rho^{R}$")
    ax.plot([-2.0, 0.0], [0.15, 0.15], color=fs.VERMILLION, lw=1.0)
    d.text(ax, -0.4, -0.3, "isentropic ghosts (not called)", color=fs.BLACK)
    ax.set_xlim(-2.9, 3.2)
    ax.set_ylim(-0.6, 1.8)
    return fig
