"""The names an output block can list and the diagnostic fields each one writes, from
OutputType::loadDiagOutputData (src/output/load_diag_output_data.cpp:47-337 at
snapy@e894700ff7aee30b52882e5202b16461413780b0). A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs

ROWS = [("thermo", "temp, theta, theta_v, entropy, rh_<product>", "needs a thermo block", fs.GREEN),
        ("diagnostics", "div, div_h, curl", "all three", fs.SKY),
        ("div, div_h, curl", "the one named", "curl: vector in 3-D, VEL3 in 2-D", fs.SKY),
        ("implicit", "ic_dry, ic_mom, ic_etot, ic_<species>", "last VIC correction", fs.ORANGE),
        ("path", "path_<species>", "column mass per bottom area", fs.PURPLE),
        ("avg", "avg_rho, avg_vel, avg_press, avg_<species>", "volume mean over x2, x3", fs.PURPLE)]


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 3.0))
    ax.set_axis_off()
    ax.text(0.0, 7, "listed name", fontsize=8, weight="bold")
    ax.text(2.0, 7, "fields written (and a note)", fontsize=8, weight="bold")
    for k, (name, fields, note, col) in enumerate(ROWS):
        y = 6 - k
        ax.add_patch(plt.Rectangle((-0.08, y - 0.35), 0.06, 0.7, fc=col, ec="none"))
        ax.text(0.0, y, name, fontsize=8, family="monospace", va="center")
        ax.text(2.0, y + 0.17, fields, fontsize=7.5, family="monospace", va="center")
        ax.text(2.0, y - 0.25, note, fontsize=7, va="center", color=fs.GREY)
    ax.set_xlim(-0.1, 8.2)
    ax.set_ylim(0.4, 7.5)
    return fig
