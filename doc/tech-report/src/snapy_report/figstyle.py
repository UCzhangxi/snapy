"""Shared figure style for the snapy Technical Report (STYLE.md section 6).

Import from a figure script with
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common"))
    import figstyle as fs
then call fs.apply() before creating figures and fs.save(fig, __file__) at the end.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Okabe-Ito, colour-blind safe; meanings fixed across the report (STYLE.md 6.2)
BLACK = "#000000"      # grid, walls, axes
ORANGE = "#E69F00"     # face quantities, fluxes
SKY = "#56B4E9"        # cell quantities
GREEN = "#009E73"      # the scheme being described (its added term)
YELLOW = "#F0E442"     # highlights
BLUE = "#0072B2"       # reference / exact
VERMILLION = "#D55E00"  # errors, defects, the term removed
PURPLE = "#CC79A7"     # ghosts, other blocks
GREY = "#999999"       # de-emphasised context (not a data colour)

SINGLE = 3.4  # in, single-column width
DOUBLE = 7.0  # in, double-column width
DPI = 200


def apply():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "lines.linewidth": 1.4,
        "lines.markersize": 4.5,
        "axes.linewidth": 0.8,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
        "svg.hashsalt": "snapy-tech-report",  # reproducible SVG ids
        "path.simplify": False,
    })


def slope_guide(ax, x0, y0, x1, order, label=None, color=BLACK):
    """a reference line y ~ x^-order from (x0, y0) to x1, labelled with its order"""
    y1 = y0 * (x1 / x0) ** (-order)
    ax.plot([x0, x1], [y0, y1], color=color, lw=0.8, ls=":")
    ax.text(x1 * 1.05, y1, label or f"$h^{order}$", fontsize=8, va="center", color=color)


def save(fig, script_file, svg=False):
    base = os.path.splitext(os.path.abspath(script_file))[0]
    fig.savefig(base + ".png", metadata={"Software": None})
    if svg:
        fig.savefig(base + ".svg", metadata={"Date": None})
    print(base + ".png")


def cell_box(ax, x, y, width=1., height=1., ghost=False):
    """Shared cell glyph, with hatching for ghosts (STYLE 6.2)."""
    from matplotlib.patches import Rectangle
    box = Rectangle((x, y), width, height, edgecolor=BLACK,
                    facecolor="#F7E6EF" if ghost else "#EAF5FC",
                    hatch="//" if ghost else None)
    ax.add_patch(box)
    return box


def cell_value(ax, x, y):
    return ax.plot(x, y, 'o', color=SKY)


def face_value(ax, x, y):
    return ax.plot(x, y, '^', color=ORANGE)


def wall(ax, x, bottom, top):
    return ax.plot([x, x], [bottom, top], color=BLACK, lw=2.5)
