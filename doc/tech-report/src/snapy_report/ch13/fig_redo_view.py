"""The six redo causes as the log shows them: the bit, the word printed in the cause list, and the local test that
sets it (MeshBlockImpl::local_redo_flags and apply_redo, src/mesh/meshblock.cpp:1229-1286 at
snapy@e894700ff7aee30b52882e5202b16461413780b0). A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs

ROWS = [(1, "floor", "density or pressure at or within 0.1% of its floor (or NaN)"),
        (2, "clamp", "the VIC dry-gas clamp emptied a cell"),
        (4, "limiter", "the EOS limiter patched a cell"),
        (8, "nan", "the EOS limiter found a NaN"),
        (16, "saturation", "the saturation adjustment left a cell unadjusted"),
        (32, "vic-solve", "the VIC refused a column (restores even past max_redo)")]


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 2.2))
    ax.set_axis_off()
    ax.text(0.0, 7, "bit", fontsize=8, weight="bold")
    ax.text(0.7, 7, "printed as", fontsize=8, weight="bold")
    ax.text(2.2, 7, "set when, on any rank (MAX over ranks)", fontsize=8, weight="bold")
    for k, (bit, word, why) in enumerate(ROWS):
        y = 6 - k
        ax.add_patch(plt.Rectangle((-0.05, y - 0.38), 0.5, 0.76, fc=fs.VERMILLION if bit == 32 else fs.ORANGE,
                                   ec="none", alpha=0.85))
        ax.text(0.2, y, "%d" % bit, fontsize=8, ha="center", va="center")
        ax.text(0.7, y, word, fontsize=8, family="monospace", va="center")
        ax.text(2.2, y, why, fontsize=8, va="center")
    ax.text(0.0, 0.0, "Redoing the step with smaller dt (causes: floor limiter vic-solve).   <- mask 37",
            fontsize=7.5, family="monospace", color=fs.GREY)
    ax.set_xlim(-0.1, 8.0)
    ax.set_ylim(-0.5, 7.5)
    return fig
