"""Reference continuity across an x1 seam (chapter 5): the anchor relay and the ghost-row exchange.

Two blocks of one column split along x1 (x1 to the right): the upper block scans from the domain top and passes its
bottom-face pressure to the block below as that block's top anchor; then each block's ghost rows of p_ref and
rho_ref are overwritten with the neighbour's interior rows. Cartoon; no data. Code it depicts:
snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy), src/hydro/hydro.cpp lines 509-533, 577-640.
"""
from snapy_report.ch05 import _style as fs
from snapy_report.ch05 import _draw as d


def make_fig():
    fig, ax = fs.new_figure("double", 2.3)
    fs.cartoon(ax)
    # lower block cells 0..3 with 2 upper ghosts; upper block cells 5..8 with 2 lower ghosts, drawn on two rows
    d.row(ax, 0, 3, y=0.0, ghosts_hi=2)
    d.row(ax, 4, 7, y=1.6, ghosts_lo=2)
    d.wall_at(ax, 0.0, y=0.0)
    d.wall_at(ax, 8.0, y=1.6)
    d.seam_at(ax, 4.0, y=0.0)
    d.seam_at(ax, 4.0, y=1.6)
    d.text(ax, 2.0, -0.35, "lower block")
    d.text(ax, 6.0, 2.95, "upper block (owns the domain top)")
    fs.face_value(ax, 4.0, 2.1)
    d.arrow(ax, (3.95, 1.95), (3.95, 1.15), color=fs.GREEN)
    d.text(ax, 3.0, 2.25, "anchor", bbox=dict(boxstyle="round,pad=0.1", fc=fs.WHITE, ec="none"))
    d.arrow(ax, (7.9, 2.75), (4.1, 2.75), color=fs.GREEN)
    d.text(ax, 8.1, 2.75, "scan", ha="left")
    # ghost-row copies: upper interior rows 4,5 -> lower ghosts 4,5; lower interior 2,3 -> upper ghosts 2,3
    for k in (4, 5):
        d.arrow(ax, (k + 0.5, 1.55), (k + 0.5, 1.05), color=fs.PURPLE, ls="--")
    for k in (2, 3):
        d.arrow(ax, (k + 0.5, 1.05), (k + 0.5, 1.55), color=fs.PURPLE, ls="--")
    d.text(ax, 9.0, 0.5, "ghost rows of $p_{\\mathrm{ref}}$, $\\rho_{\\mathrm{ref}}$\nfrom the neighbour", ha="left")
    ax.set_xlim(-0.5, 11.6)
    ax.set_ylim(-0.6, 3.1)
    return fig
