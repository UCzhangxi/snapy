"""The hydrostatic reference kernel (chapter 5): the top-down face-pressure scan and the six-face cell pressure.

Top: cells of one column between two walls (x1 to the right); the scan starts at the top anchor (half a cell above
the top cell centre) and adds g rho_i dx1 cell by cell towards the bottom wall. Bottom: the six faces whose quintic
gives the interior cell pressure of cell i, and the one-sided six-face window of the two wall cells. Cartoon; no
data. Code it depicts: snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy),
src/hydro/hydro_ref_x1_impl.h lines 22-60 and 110-180.
"""
from snapy_report.ch05 import _style as fs
from snapy_report.ch05 import _draw as d


def make_fig():
    fig, ax = fs.new_figure("double", 2.6)
    fs.cartoon(ax)
    n = 8
    d.row(ax, 0, n - 1, y=1.4)
    d.wall_at(ax, 0.0, y=1.4)
    d.wall_at(ax, float(n), y=1.4)
    for f in range(n + 1):
        fs.face_value(ax, f, 1.9)
    d.arrow(ax, (n - 0.05, 2.65), (0.05, 2.65), color=fs.GREEN)
    d.text(ax, n / 2, 2.85, "scan: $p_{i-1/2} = p_{i+1/2} + g\\,\\overline{\\rho}_i\\,\\Delta x_1$", color=fs.BLACK)
    d.text(ax, n + 0.15, 2.3, "top anchor", ha="left")
    # lower row: interior six-face window and the one-sided wall window
    d.row(ax, 0, n - 1, y=0.0)
    d.wall_at(ax, 0.0, y=0.0)
    d.wall_at(ax, float(n), y=0.0)
    fs.cell(ax, 4, 0.0, 1.0, 1.0, label="$i$", fill=True)
    for f in range(2, 8):
        fs.face_value(ax, f, 0.5)
    fs.bracket(ax, (2, 0.0), (7, 0.0), label="interior: six faces, $i-5/2 \\ldots i+5/2$")
    fs.cell(ax, 0, 0.0, 1.0, 1.0, label="$i_s$", fill=True)
    fs.cell(ax, 1, 0.0, 1.0, 1.0, label="$i_s{+}1$", fill=True)
    fs.bracket(ax, (0, 1.0), (5, 1.0), label=None, offset=-0.12)
    d.text(ax, 2.5, 1.22, "wall rows: faces $i_s-1/2 \\ldots i_s+9/2$")
    ax.set_xlim(-0.6, n + 1.9)
    ax.set_ylim(-0.7, 3.05)
    return fig
