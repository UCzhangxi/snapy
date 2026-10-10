"""Shared drawing helpers of the chapter 5 cartoons: a row of x1 cells laid out left to right (x1 increases to the
right), with ghost cells, walls, seams and index labels drawn only through the chapter style shim `_style`."""
import json
from importlib import resources

from matplotlib.patches import FancyArrowPatch

from snapy_report.ch05 import _style as fs


def row(ax, first, last, y=0.0, h=1.0, ghosts_lo=0, ghosts_hi=0, labels=None, fill=False):
    """cells first..last (integer x positions, width 1) plus hatched ghosts on either side; labels maps x -> text"""
    labels = labels or {}
    for k in range(first - ghosts_lo, last + ghosts_hi + 1):
        kind = "ghost" if (k < first or k > last) else "fluid"
        fs.cell(ax, k, y, 1.0, h, label=labels.get(k), kind=kind, fill=fill and kind == "fluid")


def wall_at(ax, xw, y=0.0, h=1.0, pad=0.25):
    return fs.wall(ax, (xw, y - pad), (xw, y + h + pad))


def seam_at(ax, xs, y=0.0, h=1.0, pad=0.25):
    return fs.seam(ax, (xs, y - pad), (xs, y + h + pad))


def arrow(ax, p0, p1, color=fs.BLACK, ls="-", lw=1.2, style="-|>"):
    a = FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=9, lw=lw, color=color, ls=ls, zorder=5,
                        shrinkA=0, shrinkB=0)
    return ax.add_patch(a)


def text(ax, x, y, s, **kw):
    kw.setdefault("fontsize", fs.SMALL_PT)
    kw.setdefault("ha", "center")
    kw.setdefault("va", "center")
    return ax.text(x, y, s, **kw)


def load(name):
    """a committed data file of this chapter (STYLE 6.1), with its provenance"""
    return json.loads((resources.files("snapy_report.ch05") / "data" / name).read_text())
