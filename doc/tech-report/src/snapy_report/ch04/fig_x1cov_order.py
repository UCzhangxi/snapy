"""The x1 mass-flux covariance: the stored velocity against the cell average of w.

Data figure. It reads data/x1cov_orders.json, the committed output of
covariance_check.py (claim C4).
"""
import json
import os

from snapy_report import figstyle as fs
import matplotlib.pyplot as plt


def make_fig():
    fs.apply()
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "data", "x1cov_orders.json")) as fh:
        d = json.load(fh)
    fig, ax = plt.subplots(figsize=(fs.SINGLE, 2.8))
    ax.loglog(d["ns"], d["as_stored"], "-o", color=fs.VERMILLION,
              label="$m_1/\\rho$ as stored", mfc="white")
    ax.loglog(d["ns"], d["corrected"], "-s", color=fs.GREEN,
              label="after the correction", mfc="white")
    fs.slope_guide(ax, 48, d["as_stored"][1] * 0.4, 110, 2, "$h^2$")
    fs.slope_guide(ax, 48, d["corrected"][1] * 0.4, 110, 4, "$h^4$")
    ax.set_xlabel("$n_1$ (cells over the unit interval)")
    ax.set_ylabel("max $|v - \\langle w\\rangle|$ [-]")
    ax.set_xticks(d["ns"])
    ax.set_xticklabels([str(v) for v in d["ns"]])
    ax.xaxis.set_minor_formatter(plt.NullFormatter())
    ax.grid(True, which="major", color="#DDDDDD", lw=0.5)
    ax.legend(frameon=False, loc="lower left")
    fig.tight_layout()
    return fig
