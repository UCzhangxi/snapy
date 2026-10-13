"""The 1/R content of the one-step effective stratification on a spherical-polar column (chapter 5).

R [eps_eff n1^2 (R) - eps_eff n1^2 (inf)] against R/H, SNAP_X1_CENTROID_EXACT off (left) and on (right), for
n1 = 32 to 256; the reference eps_eff n1^2 (inf) is the same column in Cartesian geometry with the same switches.
Error bars: half the spread over seed amplitudes 0.9, 1.0 and 1.1 times 1e-4 (round-off, magnified by R). Data:
data/oneoverr_remainder.json, written by run_oneoverr_remainder.py against a source build of
snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy), CPU, double, one rank.
"""
import numpy as np

from snapy_report.ch05 import _style as fs
from snapy_report.ch05 import _draw as d


def make_fig():
    data = d.load("oneoverr_remainder.json")
    rh = np.array(data["rh"], float)
    fig, axes = fs.new_figure("double", 2.6, 1, 2)
    styles = {"32": (fs.ORANGE, "^"), "64": (fs.SKY, "o"), "128": (fs.BLUE, "s"), "256": (fs.BLACK, "D")}
    for ax, arm, title in zip(axes, ("off", "on"), ("SNAP_X1_CENTROID_EXACT off", "SNAP_X1_CENTROID_EXACT on")):
        for nz in map(str, data["nz"]):
            c, m = styles.get(nz, (fs.BLACK, "o"))
            v = np.array(data["remainder"][arm][nz])
            e = np.array(data["remainder_noise"][arm][nz])
            ax.errorbar(rh, v, yerr=e, color=c, marker=m, mfc="white", mec=c, capsize=2, label=f"$n_1$ = {nz}")
        ax.axhline(0.0, color=fs.BLACK, lw=0.6, ls=":")
        ax.set_xscale("log")
        ax.set_xticks(rh)
        ax.set_xticklabels([f"{v:g}" for v in rh])
        ax.minorticks_off()
        ax.set_xlabel("$r_0/L_z$ [-]")
        ax.set_title(title, fontsize=fs.SMALL_PT)
    axes[0].set_ylabel("$D$ [-]")
    axes[1].set_ylim(-0.0005, 0.0025)
    axes[0].legend(loc="upper right", fontsize=fs.SMALL_PT)
    fs.panel_labels(axes)
    return fig
