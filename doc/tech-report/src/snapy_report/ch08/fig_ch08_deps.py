"""The dependency map of chapter 8: what each mechanism protects and what reads it.

Cartoon. Every edge is stated and cited in the section it comes from; this figure only
collects them. It reads no data.
"""
from snapy_report import figstyle as fs
import matplotlib.pyplot as plt

NODES = {
    "switch": (0.4, 2.9, "`limiter`\nswitch"),
    "theta": (2.1, 3.3, "tracer\nlimiter"),
    "carry": (3.9, 3.3, "energy and\nmomentum carry"),
    "scalar": (2.1, 2.2, "passive\nscalars"),
    "eos": (2.1, 1.1, "EOS floors\n(two passes)"),
    "recon": (0.4, 1.1, "face\nfloors"),
    "borrow": (3.9, 1.6, "condensate\nborrow"),
    "fixvap": (5.6, 1.1, "column\nrepair"),
    "marks": (3.9, 0.2, "limiter\nmarks"),
    "redo": (5.6, 0.2, "redo\ndetector"),
    "vic": (5.6, 2.4, "implicit\ndry clamp"),
}
EDGES = [("switch", "theta", "turns on"), ("switch", "scalar", "turns on"),
         ("switch", "eos", "turns on"), ("switch", "recon", "turns on"),
         ("theta", "carry", "requires"), ("eos", "borrow", "requires"),
         ("borrow", "fixvap", "falls back to"), ("eos", "marks", "sets"),
         ("marks", "redo", "read by"), ("vic", "redo", "read by")]
STYLE = {"turns on": (fs.GREEN, "--"), "requires": (fs.BLACK, "-"),
         "falls back to": (fs.VERMILLION, ":"), "sets": (fs.BLACK, "-"),
         "read by": (fs.BLUE, "-.")}


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 3.1))
    ax.set_axis_off()
    for a, b, kind in EDGES:
        col, ls = STYLE[kind]
        x0, y0, _ = NODES[a]
        x1, y1, _ = NODES[b]
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="->", color=col, ls=ls, lw=1.1,
                                    shrinkA=24, shrinkB=24, alpha=0.9))
    for key, (x, y, lab) in NODES.items():
        ax.text(x, y, lab.replace("`", ""), ha="center", va="center", fontsize=7,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=fs.BLACK, lw=0.8))
    seen = []
    for kind, (col, ls) in STYLE.items():
        if kind in seen:
            continue
        seen.append(kind)
        ax.plot([], [], color=col, ls=ls, lw=1.1, label=kind)
    ax.legend(frameon=False, ncol=5, loc="lower center", bbox_to_anchor=(0.5, -0.1))
    ax.set_xlim(-0.6, 6.5)
    ax.set_ylim(-0.6, 3.9)
    return fig
