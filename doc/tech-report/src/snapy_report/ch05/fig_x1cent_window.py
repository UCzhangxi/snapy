"""SNAP_X1_CENTROID_EXACT (chapter 5): r^2 means, plain means and the windows of the two maps.

Top: a radial cell with its mid-radius and the r^2 centroid x1v, which sits h^2/(6 r) further out. Middle: the
five-cell window that converts r^2 means to the cell's plain mean, centred in the interior and one-sided at a wall.
Bottom: the six-face window of the pressure source, which reaches two faces past a seam. x1 = r to the right.
Cartoon; no data. Code it depicts: snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy),
src/coord/x1_centroid.cpp lines 104-155 and 184-222.
"""
from snapy_report.ch05 import _style as fs
from snapy_report.ch05 import _draw as d


def make_fig():
    fig, ax = fs.new_figure("double", 2.9)
    fs.cartoon(ax)
    fs.cell(ax, 0.0, 2.4, 2.4, 0.8, fill=True)
    ax.plot([1.2, 1.2], [2.4, 3.2], color=fs.BLACK, lw=0.8, ls=":")
    ax.plot([1.45, 1.45], [2.4, 3.2], color=fs.GREEN, lw=1.4)
    d.text(ax, 1.15, 3.42, "mid-radius $\\overline{r}_i$", ha="right")
    d.text(ax, 1.5, 3.42, "$x_{1v} = \\overline{r}_i + h^2/(6\\overline{r}_i)$", ha="left")
    d.row(ax, 0, 8, y=1.0)
    d.wall_at(ax, 0.0, y=1.0)
    fs.cell(ax, 4, 1.0, 1.0, 1.0, label="$i$", fill=True)
    fs.bracket(ax, (2, 2.0), (7, 2.0), label=None, offset=-0.12)
    d.text(ax, 4.5, 2.2, "plain mean of $i$: five $r^2$ means")
    fs.cell(ax, 0, 1.0, 1.0, 1.0, label="$i_s$", fill=True)
    fs.bracket(ax, (0, 1.0), (5, 1.0), label="wall: one-sided")
    d.row(ax, 0, 4, y=-0.6, ghosts_hi=2)
    d.seam_at(ax, 5.0, y=-0.6)
    for f in range(2, 8):
        fs.face_value(ax, f, -0.1)
    d.text(ax, 8.2, -0.1, "$S_i$: six faces, two from the neighbour", ha="left")
    ax.set_xlim(-0.5, 12.6)
    ax.set_ylim(-1.0, 3.65)
    return fig
