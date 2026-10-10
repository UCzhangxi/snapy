"""Style shim for the chapter 5 figures (STYLE.md sections 6.2 and 10.4).

Chapter 5 imports its figure style from this module only, as chapter 9 does with its own shim. When the house
snapy_report figure style with these helpers lands, replace the one import line in each ch05 figure
(`from snapy_report.ch05 import _style as fs`) by the package's figstyle and delete this file. It provides exactly
what the ch05 figures use: the Okabe-Ito colours, the two widths of STYLE 6.2 (3.4 in and 7.0 in), DejaVu Sans
9 pt labels and 8 pt ticks, and the shared cartoon conventions (cell box, cell value, face value, wall, ghost,
seam). Figures are matplotlib Figure objects never registered with pyplot, so a Quarto cell shows each once.
"""
import logging

import matplotlib
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, Rectangle

BLACK = "#000000"       # grid, walls, axes
ORANGE = "#E69F00"      # face quantities, fluxes
SKY = "#56B4E9"         # cell quantities
GREEN = "#009E73"       # the scheme being described (its added term)
BLUE = "#0072B2"        # reference / exact solution
VERMILLION = "#D55E00"  # errors, defects, the term removed
PURPLE = "#CC79A7"      # ghosts, other blocks
CELL_FILL = "#EAF5FC"   # light blue: cell fill in cartoons
GHOST_FILL = "#F7E6EF"  # light reddish purple: ghost-cell fill in cartoons
WHITE = "#FFFFFF"
PALETTE = (BLACK, ORANGE, SKY, GREEN, BLUE, VERMILLION, PURPLE, CELL_FILL, GHOST_FILL, WHITE)

# fontTools reports the DejaVu files' zero timestamps when the PDF backend subsets them; in a Quarto cell that
# warning would be printed into the book
logging.getLogger("fontTools").setLevel(logging.ERROR)

SINGLE = 3.4
DOUBLE = 7.0
WIDTHS = {"single": SINGLE, "double": DOUBLE}
LABEL_PT = 9
SMALL_PT = 8

RC = {
    "font.family": "DejaVu Sans", "font.size": LABEL_PT, "axes.labelsize": LABEL_PT, "axes.titlesize": LABEL_PT,
    "xtick.labelsize": SMALL_PT, "ytick.labelsize": SMALL_PT, "legend.fontsize": SMALL_PT, "legend.frameon": False,
    "mathtext.fontset": "dejavusans", "text.usetex": False, "lines.linewidth": 1.4, "lines.markersize": 4.5,
    "axes.linewidth": 0.8, "hatch.color": BLACK, "svg.hashsalt": "snapy-tech-report", "svg.fonttype": "path",
    "pdf.fonttype": 42, "path.simplify": False,
    "axes.prop_cycle": matplotlib.cycler(color=[BLACK, ORANGE, SKY, GREEN, BLUE, VERMILLION, PURPLE]),
}


def new_figure(width="double", height=2.4, nrows=1, ncols=1, **subplot_kw):
    """a constrained-layout Figure of a house width (STYLE 6.2) and its axes"""
    matplotlib.rcParams.update(RC)
    fig = Figure(figsize=(WIDTHS.get(width, width), height), layout="constrained")
    return fig, fig.subplots(nrows, ncols, **subplot_kw)


def panel_labels(axes):
    for n, ax in enumerate(getattr(axes, "flat", axes)):
        ax.text(0.0, 1.0, f"({'abcd'[n]})", transform=ax.transAxes, ha="left", va="bottom", fontsize=LABEL_PT,
                fontweight="bold")


def cartoon(ax):
    ax.set_axis_off()
    ax.set_aspect("equal")


def cell(ax, x, y, w=1.0, h=1.0, label=None, kind="fluid", fill=False):
    """a cell box; kind "fluid" or "ghost" (hatched // on the ghost fill)"""
    if kind == "ghost":
        style = dict(fc=GHOST_FILL, ec=PURPLE, hatch="//")
    else:
        style = dict(fc=CELL_FILL if fill else WHITE, ec=BLACK, hatch=None)
    box = ax.add_patch(Rectangle((x, y), w, h, lw=0.8, **style))
    if label is not None:
        ax.text(x + 0.5 * w, y + 0.5 * h, label, ha="center", va="center", fontsize=SMALL_PT,
                bbox=dict(boxstyle="round,pad=0.1", fc=WHITE, ec="none"))
    return box


def cell_value(ax, x, y):
    return ax.plot([x], [y], ls="none", marker="o", ms=5, mfc=SKY, mec=BLACK, mew=0.5, zorder=4)[0]


def face_value(ax, x, y):
    return ax.plot([x], [y], ls="none", marker="^", ms=5.5, mfc=ORANGE, mec=BLACK, mew=0.5, zorder=4)[0]


def face_flux(ax, x, y, dx=0.0, dy=0.4, color=ORANGE):
    a = FancyArrowPatch((x - 0.5 * dx, y - 0.5 * dy), (x + 0.5 * dx, y + 0.5 * dy), arrowstyle="-|>",
                        mutation_scale=8, lw=1.2, color=color, zorder=5)
    return ax.add_patch(a)


def wall(ax, p0, p1):
    return ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=BLACK, lw=2.5, solid_capstyle="butt", zorder=3)[0]


def seam(ax, p0, p1):
    return ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=PURPLE, lw=1.4, ls=(0, (4, 2)), zorder=3)[0]


def bracket(ax, p0, p1, label=None, offset=0.15):
    """a horizontal stencil extent from p0 to p1, offset below (positive offset) or above, with its label"""
    (x0, y0), (x1, y1) = p0, p1
    ax.plot([x0, x0, x1, x1], [y0, y0 - offset, y1 - offset, y1], color=BLACK, lw=0.8)
    if label is not None:
        ax.text(0.5 * (x0 + x1), y0 - 2 * offset, label, fontsize=SMALL_PT, ha="center", va="top")


def slope_guide(ax, x0, y0, x1, order, label=None, color=BLACK):
    y1 = y0 * (x1 / x0) ** (-order)
    ax.plot([x0, x1], [y0, y1], color=color, lw=0.8, ls=":")
    ax.text(x1 * 1.05, y1, label or f"$h^{order}$", fontsize=SMALL_PT, va="center", color=color)
