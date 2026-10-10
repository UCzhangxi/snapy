"""The SNAP_WB_REF4 stencils (chapter 5): the five-cell filter F with cubic wall values, and the face window.

Top: the filter F = (-1, 4, 10, 4, -1)/16 for the wall cell i_s; its two values past the wall, E_1 and E_2, are
cubic extrapolations of the four owned cells nearest it, so ghosts are never read. Bottom: the face density at face f
from the quartic through the primitive at five faces (four cells), centred in the interior and kept inside the
owned cells at the wall. x1 to the right. Cartoon; no data. Code it depicts:
snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy), src/hydro/wb_ref4.cpp lines 120-158 and 195-221.
"""
from snapy_report.ch05 import _style as fs
from snapy_report.ch05 import _draw as d


def make_fig():
    fig, ax = fs.new_figure("double", 2.6)
    fs.cartoon(ax)
    d.row(ax, 0, 6, y=1.5, ghosts_lo=2)
    d.wall_at(ax, 0.0, y=1.5)
    fs.cell(ax, 0, 1.5, 1.0, 1.0, label="$i_s$", fill=True)
    for k in range(4):
        fs.cell_value(ax, k + 0.5, 2.3)
    for k, txt in ((-1, "$E_1$"), (-2, "$E_2$")):
        ax.plot([k + 0.5], [2.3], ls="none", marker="D", ms=5, mfc=fs.GREEN, mec=fs.BLACK, zorder=4)
        d.text(ax, k + 0.5, 2.85, txt)
    fs.bracket(ax, (-2, 1.5), (3, 1.5), label="$F$ on cells $i_s-2 \\ldots i_s+2$")
    d.row(ax, 0, 6, y=0.0, ghosts_lo=2)
    d.wall_at(ax, 0.0, y=0.0)
    for f in range(0, 5):
        fs.face_value(ax, f, 0.5)
    fs.bracket(ax, (0, 0.0), (4, 0.0), label="wall face: cells $i_s \\ldots i_s+3$")
    d.text(ax, 7.2, 0.5, "interior: $(-1, 7, 7, -1)/12$", ha="left")
    d.text(ax, 7.2, 2.0, "$(F r)_{i_s} = r_{i_s}$", ha="left")
    ax.set_xlim(-2.4, 10.4)
    ax.set_ylim(-0.75, 3.1)
    return fig
