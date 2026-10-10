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
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 1.5))
    ax.set_axis_off()
    w, gap = 1.0, 0.26
    for i, (lab, col) in enumerate(STEPS):
        x = i * (w + gap)
        ax.add_patch(plt.Rectangle((x, 0), w, 1, fc="white", ec=col, lw=1.4))
        ax.text(x + w / 2, 0.5, lab, ha="center", va="center", fontsize=6.5)
        if i < len(STEPS) - 1:
            ax.annotate("", xy=(x + w + gap, 0.5), xytext=(x + w, 0.5),
                        arrowprops=dict(arrowstyle="->", color=fs.BLACK, lw=0.9))
    ax.set_xlim(-0.3, len(STEPS) * (w + gap))
    ax.set_ylim(-0.35, 1.35)
    return fig
