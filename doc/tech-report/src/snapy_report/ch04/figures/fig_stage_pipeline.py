"""The order of one Runge-Kutta stage inside HydroImpl::forward.

Cartoon of src/hydro/hydro_forward.cpp:207-999 at
snapy@e894700ff7aee30b52882e5202b16461413780b0. It reads no data.
"""
from snapy_report import figstyle as fs
import matplotlib.pyplot as plt


STEPS = [("EOS\n$u\\to w$", fs.SKY), ("$x_1$ recon\n+ Riemann", fs.ORANGE),
         ("seam\naverage", fs.PURPLE), ("$x_2/x_3$ recon\n+ Riemann", fs.ORANGE),
         ("covariance", fs.GREEN), ("species\nlimiter", fs.VERMILLION),
         ("divergence\n+ sources", fs.SKY), ("forcings", fs.SKY),
         ("implicit\ncorrection", fs.BLUE)]


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 2.4))
    ax.set_axis_off()
    w, h, gap, rowgap, per = 1.6, 1.0, 0.45, 0.7, 5
    pos = []
    for i, (lab, col) in enumerate(STEPS):
        row, k = divmod(i, per)
        x, y = k * (w + gap), -row * (h + rowgap)
        pos.append((x, y))
        ax.add_patch(plt.Rectangle((x, y), w, h, fc="white", ec=col, lw=1.4))
        ax.text(x + w / 2, y + h / 2, lab, ha="center", va="center", fontsize=fs.SMALL_PT)
    for i in range(len(STEPS) - 1):
        (x0, y0), (x1, y1) = pos[i], pos[i + 1]
        if y0 == y1:
            ax.annotate("", xy=(x1, y1 + h / 2), xytext=(x0 + w, y0 + h / 2),
                        arrowprops=dict(arrowstyle="->", color=fs.BLACK, lw=0.9))
        else:
            ax.annotate("", xy=(x1 + w / 2, y1 + h), xytext=(x0 + w / 2, y0),
                        arrowprops=dict(arrowstyle="->", color=fs.BLACK, lw=0.9,
                                        connectionstyle="arc3,rad=0"))
    ax.set_xlim(-0.2, per * (w + gap))
    ax.set_ylim(-(h + rowgap) - 0.2, h + 0.2)
    return fig
