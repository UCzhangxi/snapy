"""One global x2 face array with its ghost extension, sliced for two and for three blocks.

Drawn from CoordinateImpl::block_faces_ (src/coord/coordinate.cpp:307-324) at snapy@e894700ff7aee30b52882e5202b16461413780b0: six global cells, two ghost
faces per side. A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 2.2))
    n, ng = 6, 2
    faces = list(range(-ng, n + ng + 1))
    for g in faces:
        ax.plot([g, g], [2.6, 3.0], color=fs.GREY if g < 0 or g > n else fs.BLACK, lw=1.0)
        ax.text(g, 3.1, str(g), ha="center", fontsize=8)
    ax.text(-ng - 0.6, 2.8, "global", ha="right", va="center", fontsize=8)
    for row, nb in ((1.6, 2), (0.4, 3)):
        w = n // nb
        for b in range(nb):
            lo, hi = b * w, (b + 1) * w
            y = row - 0.25 * (b % 2)
            for g in range(lo - ng, lo):
                fs.cell_box(ax, g, y, 1.0, 0.22, ghost=True)
            for g in range(hi, hi + ng):
                fs.cell_box(ax, g, y, 1.0, 0.22, ghost=True)
            fs.cell_box(ax, lo, y, w, 0.22)
            ax.text(lo + w / 2, y + 0.11, "block %d" % b, ha="center", va="center", fontsize=8)
        ax.text(-ng - 0.6, row - 0.05, "nb2 = %d" % nb, ha="right", va="center", fontsize=8)
    for g in (2, 3, 4):
        ax.plot([g, g], [0.1, 2.6], color=fs.PURPLE, ls="--", lw=0.8)
    ax.set(xlim=(-ng - 2.6, n + ng + 0.5), ylim=(0.0, 3.4))
    ax.axis("off")
    return fig
