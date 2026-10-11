"""Energy-row entries the gravity work adds to the VIC block row of cell i, per gravity-work mode.

Cartoon of src/implicit/vic_assemble_full_impl.h:38-40 and 101-120 at snapy@e894700ff7aee30b52882e5202b16461413780b0
(claims C1-C3 of vicwork_check.py); no measured data.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from snapy_report import figstyle as fs

ROWS = [  # (mode, entries of b[i], a[i], c[i] in the energy row)
    ("cell", ["-g lo A-", "-g m\n-g(hi A+ - lo A-)", "+g hi A+"]),
    ("face", ["-g lo m\n-g lo A-", "-g(lo+hi) m\n-g(hi A+ - lo A-)", "-g hi m\n+g hi A+"]),
]


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 2.3))
    ax.set_axis_off()
    ax.set(xlim=(0, 12.4), ylim=(-.5, 2.9))
    for k, lab in enumerate(("b[i]: cell i-1", "a[i]: cell i", "c[i]: cell i+1")):
        ax.text(3.0 + 3.2 * k, 2.6, lab, ha="center", fontsize=8)
    for r, (mode, cells) in enumerate(ROWS):
        y = 1.3 - 1.4 * r
        ax.text(.0, y + .45, "gravity-work:\n" + mode, fontsize=8, va="center")
        for k, txt in enumerate(cells):
            ax.add_patch(Rectangle((1.5 + 3.2 * k, y - .1), 3.0, 1.1, facecolor="#EAF5FC", edgecolor=fs.BLACK, lw=.6))
            ax.text(3.0 + 3.2 * k, y + .45, txt, ha="center", va="center", fontsize=8, color=fs.GREEN)
    fig.tight_layout()
    return fig
