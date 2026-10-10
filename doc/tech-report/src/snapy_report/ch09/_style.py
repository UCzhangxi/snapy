"""Temporary style shim for the chapter 9 figures (STYLE.md section 6.2).

Chapter 9 imports its style from this module only. When the snapy_report package
of the book skeleton lands, replace the one import line in each ch09 figure
(`from snapy_report.ch09._style import ...`) by the package's figstyle and delete
this file. It provides exactly what the ch09 figures use and nothing else:

- the Okabe-Ito colours of STYLE.md section 6.2 (BLACK, ORANGE, SKY, GREEN,
  BLUE, VERMILLION, PURPLE, CELL_FILL, GHOST_FILL);
- the two figure widths SINGLE = 3.4 in and DOUBLE = 7.0 in;
- new_figure(width, height, ncols): applies DejaVu Sans 9 pt labels and 8 pt
  ticks and returns (fig, axes);
- save(fig, path): writes the figure to `path` (used only to look at a figure
  outside Quarto; the book draws figures itself).
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLACK = "#000000"
ORANGE = "#E69F00"
SKY = "#56B4E9"
GREEN = "#009E73"
BLUE = "#0072B2"
VERMILLION = "#D55E00"
PURPLE = "#CC79A7"
CELL_FILL = "#EAF5FC"
GHOST_FILL = "#F7E6EF"

SINGLE = 3.4
DOUBLE = 7.0


def new_figure(width, height, ncols=1):
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "svg.hashsalt": "snapy-tech-report",
    })
    return plt.subplots(1, ncols, figsize=(width, height))


def save(fig, path):
    fig.savefig(path, dpi=200, bbox_inches="tight", metadata={"Software": None})
