"""The stage schedule of a bare block and its segments (chapter 11, @sec-ch11-segments), at the code pin.

The ops and their order are those of StageExecutor::build_schedule (src/mesh/stage_executor.cpp); the grouping is
StageSchedule::regroup (src/mesh/segment.cpp): consecutive ops of one kind and capturability share a segment, and
a host exchange is a segment of its own. No data: a diagram.
"""
from matplotlib.patches import Rectangle

from snapy_report import figstyle as fs

OPS = ("exchange", "advance", "forcing", "combine", "saturation", "chemistry", "boundaries")


def segments(eager):
    """(first, last, kind) of each segment of the schedule, with the ops in `eager` not capturable."""
    out = [(0, 0, "host")]
    start = 1
    for i in range(1, len(OPS)):
        cut = OPS[i] in eager or (i > start and OPS[i - 1] in eager)
        if cut:
            out.append((start, i - 1, "eager" if OPS[i - 1] in eager else "graph"))
            start = i
    out.append((start, len(OPS) - 1, "eager" if OPS[-1] in eager else "graph"))
    return out


def _row(ax, y, eager, title):
    w, gap = 1.0, 0.12
    for i, name in enumerate(OPS):
        x = i * (w + gap)
        host = i == 0
        fill = fs.GHOST_FILL if (host or name in eager) else fs.CELL_FILL
        ax.add_patch(Rectangle((x, y), w, 0.5, fc=fill, ec=fs.BLACK, lw=0.8))
        ax.text(x + w / 2, y + 0.25, name, ha="center", va="center", fontsize=fs.SMALL_PT)
    for first, last, kind in segments(eager):
        x0, x1 = first * (w + gap), last * (w + gap) + w
        ax.plot([x0, x0, x1, x1], [y - 0.06, y - 0.12, y - 0.12, y - 0.06], color=fs.BLACK, lw=0.8)
        ax.text((x0 + x1) / 2, y - 0.2, kind, ha="center", va="top", fontsize=fs.SMALL_PT)
    ax.text(0, y + 0.62, title, ha="left", va="bottom", fontsize=fs.SMALL_PT)


def make_fig():
    fig, ax = fs.new_figure("double", 2.6)
    fs.cartoon(ax)
    _row(ax, 1.35, (), "no eager op: the host exchange, then one captured segment")
    _row(ax, 0.0, ("forcing", "boundaries"),
         "a user forcing and an outflow boundary set: their ops run eager between captured segments")
    ax.set_xlim(-0.05, len(OPS) * 1.12)
    ax.set_ylim(-0.45, 2.1)
    return fig
