"""The wall continuation of the default reference (chapter 5): rho/p past a clamped wall.

r = rho/p in the three owned cells next to the bottom wall (x1 to the right) and the two values the binomial reads
past the wall: the true continuation, the repeated wall cell, and the linear and ln-linear continuations of the
code. Panel (a) is a column where r rises away from the wall (r_1 > r_0, the ln-linear branch), panel (b) one where
it falls (the linear branch). Cartoon with illustrative values, no run. Code it depicts:
snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy), src/hydro/hydro_ref_x1_impl.h lines 62-108.
"""
import numpy as np

from snapy_report.ch05 import _style as fs


def _cont(r0, r1, k):
    e = r0 * (r0 / r1) ** k if r1 > r0 else r0 + k * (r0 - r1)
    return e if e > 0 else r0


def make_fig():
    fig, axes = fs.new_figure("double", 2.4, 1, 2, sharey=True)
    for ax, slope in zip(axes, (0.12, -0.12)):
        j = np.arange(-2, 3)
        true = 1.0 + slope * j + 0.02 * j ** 2
        r = true[2:]
        ax.axvspan(-2.5, -0.5, color=fs.GHOST_FILL, lw=0)
        ax.axvline(-0.5, color=fs.BLACK, lw=2.5)
        ax.plot(j, true, color=fs.BLUE, ls="--", label="true profile")
        ax.plot(j[2:], r, ls="none", marker="o", mfc=fs.SKY, mec=fs.BLACK, label="owned cells")
        ax.plot([-1, -2], [r[0], r[0]], ls="none", marker="s", mfc=fs.VERMILLION, mec=fs.BLACK,
                label="repeated wall cell")
        ax.plot([-1, -2], [_cont(r[0], r[1], 1), _cont(r[0], r[1], 2)], ls="none", marker="D", mfc=fs.GREEN,
                mec=fs.BLACK, label="continuation (code)")
        ax.set_xticks([-2, -1, 0, 1, 2])
        ax.set_xticklabels(["$-2$", "$-1$", "$0$", "$1$", "$2$"])
        ax.set_xlabel("cell index from the wall [-]")
    axes[0].set_ylabel("$\\rho/p$ [-]")
    axes[0].set_title("$r_1 > r_0$: ln-linear", fontsize=fs.SMALL_PT)
    axes[1].set_title("$r_1 \\leq r_0$: linear", fontsize=fs.SMALL_PT)
    axes[1].legend(loc="upper right")
    fs.panel_labels(axes)
    return fig
