"""The face-local frame, the two reconstructed states and the face pressure.

Cartoon of RiemannSolverImpl and lmars_impl.h:17-78 at
snapy@e894700ff7aee30b52882e5202b16461413780b0. It reads no data.
"""
from snapy_report import figstyle as fs
import matplotlib.pyplot as plt


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.6))
    ax.set_axis_off()
    ax.set_aspect("equal")
    for x, fcol in ((0, "#EAF5FC"), (1, "#EAF5FC")):
        ax.add_patch(plt.Rectangle((x, 0), 1, 1.2, fc=fcol, ec=fs.BLACK, lw=0.8))
    ax.plot([1, 1], [0, 1.2], color=fs.ORANGE, lw=2.5)
    ax.text(0.5, 1.33, "cell $i-1$", ha="center", fontsize=fs.SMALL_PT)
    ax.text(1.5, 1.33, "cell $i$", ha="center", fontsize=fs.SMALL_PT)
    ax.plot(0.88, 0.6, ">", color=fs.GREEN, ms=7, mec=fs.BLACK, mew=0.4)
    ax.text(0.80, 0.78, "$\\mathbf{W}^{\\mathrm{L}}$", fontsize=fs.SMALL_PT, color=fs.GREEN, ha="right")
    ax.plot(1.12, 0.6, "<", color=fs.BLUE, ms=7, mec=fs.BLACK, mew=0.4)
    ax.text(1.20, 0.78, "$\\mathbf{W}^{\\mathrm{R}}$", fontsize=fs.SMALL_PT, color=fs.BLUE)
    ax.annotate("", xy=(1.0, -0.42), xytext=(1.0, -0.05),
                arrowprops=dict(arrowstyle="-", color=fs.ORANGE, lw=1.0))
    ax.text(1.0, -0.62, "$v_f$, $p_f$ at the face", ha="center",
            fontsize=fs.SMALL_PT, color=fs.ORANGE)
    ax.annotate("", xy=(1.42, 0.25), xytext=(1.0, 0.25),
                arrowprops=dict(arrowstyle="->", color=fs.BLACK, lw=1.1))
    ax.text(1.44, 0.25, "$n$", fontsize=fs.SMALL_PT, va="center")
    ax.text(0.02, -0.88, "the normal row is $\\mathrm{ivx} = \\mathrm{IPR} - \\mathrm{dim}$",
            fontsize=fs.SMALL_PT)
    ax.set_xlim(-0.15, 2.15)
    ax.set_ylim(-1.05, 1.65)
    return fig
