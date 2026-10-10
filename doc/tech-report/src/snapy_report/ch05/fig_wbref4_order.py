"""The one-step spurious stratification of a neutral column with and without SNAP_WB_REF4 (chapter 5).

|N2_eff| nz^2 against nz for 1 and 3 pressure e-folds, the four arms of tests/test_wb_ref4_order.py: the switch off
and on, each with the corrected-PE face work at its default (on) and with SNAP_GRAVITY_WORK_RADIAL_EXACT=0. Data:
data/wb_ref4_order.json, from two runs of the test at snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy), CPU,
double, one rank.
"""
import numpy as np

from snapy_report.ch05 import _style as fs
from snapy_report.ch05 import _draw as d


def make_fig():
    data = d.load("wb_ref4_order.json")
    nz = np.array(data["nz"], float)
    fig, axes = fs.new_figure("double", 2.6, 1, 2, sharey=True)
    styles = {"ref4 off, radial-exact on": (fs.VERMILLION, "o", "-"),
              "ref4 on, radial-exact on": (fs.GREEN, "s", "-"),
              "ref4 off, radial-exact 0": (fs.VERMILLION, "o", ":"),
              "ref4 on, radial-exact 0": (fs.GREEN, "s", ":")}
    for ax, ef in zip(axes, ("1", "3")):
        for name, (c, m, ls) in styles.items():
            v = np.abs(np.array(data["arms"][name][ef]))
            v = np.where(v > 0, v, np.nan)
            ax.loglog(nz, v, color=c, marker=m, ls=ls, mfc="white" if ls == ":" else c, mec=c, label=name)
        ax.set_xlabel("$n_1$ [count]")
        ax.set_xticks(nz)
        ax.set_xticklabels([str(int(v)) for v in nz])
        ax.minorticks_off()
        ax.set_title(f"{ef} e-fold" + ("s" if ef != "1" else ""), fontsize=fs.SMALL_PT)
    fs.slope_guide(axes[0], 40, 2.0e-3, 110, 2, label="$n_1^{-2}$")
    axes[0].set_ylabel("$|N^2_{\\mathrm{eff}}|\\,n_1^2$ [-]")
    axes[1].legend(loc="lower left", fontsize=fs.SMALL_PT)
    fs.panel_labels(axes)
    return fig
