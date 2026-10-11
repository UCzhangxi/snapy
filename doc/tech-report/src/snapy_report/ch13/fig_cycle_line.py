"""One cycle line, token by token: the volume integral each token prints and the reduction that combines the
blocks and ranks, from print_cycle_diagnostics (src/mesh/meshblock.cpp:1004-1112 at
snapy@e894700ff7aee30b52882e5202b16461413780b0). A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs

ROWS = [
    ("mass0=", r"$\sum_i \rho_{d,i} V_i$", "SUM", fs.SKY),
    ("masst=", r"$\sum_i (\rho_{d,i}+\sum_n \rho_{n,i}) V_i$ (if species)", "SUM", fs.SKY),
    ("ke=", r"$\sum_i \frac{1}{2}m_{j}m^{j}/\rho_i\,V_i$", "SUM", fs.SKY),
    ("ie= / energy=", r"$\sum_i E_i V_i$", "SUM", fs.SKY),
    ("pe=", r"$\sum_i \rho_i(-g_1x_{1,i})V_i$ (if $g_1\neq0$)", "SUM", fs.SKY),
    ("limcut=", "cut / offered $x_1$ flux, run to date", "SUM, ratio", fs.ORANGE),
    ("thetamin=", r"smallest limiter $\theta$, run to date", "MIN", fs.ORANGE),
    ("thetasevere=", r"count of severe cuts, run to date", "SUM", fs.ORANGE),
    ("vicclamp=", "largest clamp residual, run to date (VIC)", "MAX", fs.ORANGE),
    ("fixgrav=", "fixer deposit, run to date (pending #303)", "global", fs.GREY),
]


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 3.0))
    ax.set_axis_off()
    n = len(ROWS)
    for k, (tok, integral, op, col) in enumerate(ROWS):
        y = n - k
        ax.text(0.0, y, tok, fontsize=8, family="monospace", va="center", color=fs.BLACK)
        ax.add_patch(plt.Rectangle((1.55, y - 0.35), 0.12, 0.7, fc=col, ec="none"))
        ax.text(1.8, y, integral, fontsize=8, va="center")
        ax.text(6.3, y, op, fontsize=8, va="center", ha="right", color=fs.GREEN if op != "global" else fs.GREY)
    ax.text(0.0, n + 1, "token", fontsize=8, weight="bold")
    ax.text(1.8, n + 1, "what it sums over interior cells and local blocks", fontsize=8, weight="bold")
    ax.text(6.3, n + 1, "reduce to root", fontsize=8, weight="bold", ha="right")
    ax.plot([0, 6.3], [5.5, 5.5], color=fs.GREY, lw=0.6, ls="--")
    ax.text(4.2, 5.55, "run-to-date meters below", fontsize=7, color=fs.GREY, ha="center", va="center",
            bbox=dict(fc="white", ec="none", pad=1))
    ax.set_xlim(-0.05, 6.35)
    ax.set_ylim(0.4, n + 1.4)
    return fig
