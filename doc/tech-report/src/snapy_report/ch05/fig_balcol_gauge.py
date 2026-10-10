"""balance_column's fixed point (chapter 5): the column is moved onto p = p_ref(p) + C at fixed p/rho.

A column of cells (x1 to the right) with its pressure perturbation p' = p - p_ref before and after the projection:
before, p' varies along the column; after, it is one constant C, read at the top cell. Cartoon with illustrative
values, no run. Code it depicts: snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy),
src/hydro/balance_column.cpp lines 81-104.
"""
import numpy as np

from snapy_report.ch05 import _style as fs


def make_fig():
    fig, ax = fs.new_figure("single", 2.3)
    i = np.arange(8)
    before = 0.6 + 0.35 * np.sin(0.9 * i)
    after = np.full_like(before, before[-1])
    ax.plot(i, before, color=fs.VERMILLION, marker="o", mfc="white", mec=fs.VERMILLION, ls="--",
            label="marched column")
    ax.plot(i, after, color=fs.GREEN, marker="s", mfc="white", mec=fs.GREEN, label="projected: $p' = C$")
    ax.annotate("gauge $C$ at the top cell", xy=(7, after[-1]), xytext=(3.2, 0.15), fontsize=fs.SMALL_PT,
                arrowprops=dict(arrowstyle="-|>", color=fs.BLACK, lw=0.8))
    ax.set_xlabel("cell $i$ [count]")
    ax.set_ylabel("$p - p_{\\mathrm{ref}}$ [arb.]")
    ax.set_yticks([])
    ax.set_ylim(0.0, 1.15)
    ax.legend(loc="upper left")
    return fig
