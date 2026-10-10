"""Dependency map of the chapter 10 schemes; snapy@e894700ff7aee30b52882e5202b16461413780b0.

Logical relations read from the code cited in each scheme file; no measured data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs

NODES = {
    "tracer": (0.07, 0.78, "dry-air\ntracers"),
    "limiter": (0.32, 0.78, "conserved limiter\n(limiter: true)"),
    "satadj": (0.62, 0.78, "saturation\nadjustment"),
    "kinetics": (0.92, 0.78, "driver\nkinetics"),
    "borrow": (0.17, 0.40, "parent-vapour\nborrow"),
    "fixvapor": (0.42, 0.40, "column vapour\nrepair"),
    "redo": (0.74, 0.40, "check_redo"),
    "gravity": (0.62, 0.06, "const-gravity\n(Chapter 6)"),
    "sed": (0.92, 0.06, "sedimentation"),
}
EDGES = [  # solid: requires or is part of; dashed: raises a redo cause; dotted: upper bound needs the limiter
    ("borrow", "limiter", "-"), ("fixvapor", "limiter", "-"), ("satadj", "limiter", "-"),
    ("kinetics", "redo", "-"), ("sed", "gravity", "-"),
    ("limiter", "redo", "--"), ("satadj", "redo", "--"),
    ("tracer", "limiter", ":"),
]


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 3.0))
    ax.set(xlim=(-0.04, 1.04), ylim=(-0.12, 0.98))
    ax.axis("off")
    boxes = {}
    for key, (x, y, label) in NODES.items():
        boxes[key] = ax.text(x, y, label, ha="center", va="center", fontsize=8,
                             bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=fs.GREEN))
    fig.canvas.draw()  # the box outlines exist only after a draw; arrows are clipped to them
    for a, b, ls in EDGES:
        xa, ya, _ = NODES[a]
        xb, yb, _ = NODES[b]
        ax.annotate("", xy=(xb, yb), xytext=(xa, ya),
                    arrowprops=dict(arrowstyle="-|>", color=fs.BLACK, ls=ls, lw=1.0,
                                    patchA=boxes[a].get_bbox_patch(), patchB=boxes[b].get_bbox_patch()))
    ax.text(-0.03, 0.06, "solid: requires / is part of\ndashed: raises a redo cause\ndotted: needs it switched on",
            fontsize=7, va="center")
    fig.tight_layout()
    return fig
