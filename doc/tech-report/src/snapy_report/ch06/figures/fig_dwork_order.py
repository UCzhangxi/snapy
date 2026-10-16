"""Order of the booked gravity work, face form and corrected-PE work, interior and wall cells.

Data: the C6 ladders of ../data/d_face_work_pe_ladders.json (checks/d_face_work_pe_check.py --write-data), the output of the
6.4 check at the formulas of snapy@e894700ff7aee30b52882e5202b16461413780b0 (read in place, not copied).
"""
import json
from pathlib import Path


from snapy_report import figstyle as fs

DATA = Path(__file__).resolve().parents[1] / "data" / "d_face_work_pe_ladders.json"


def make_fig():
    d = json.loads(DATA.read_text())
    fig, axes = fs.new_figure(fs.DOUBLE, 2.7, 1, 2, sharey=True)
    for ax, key, tag in zip(axes, ("C6 spherical R=5H", "C6 Cartesian"), ("(a) spherical-polar, R = 5H",
                                                                           "(b) Cartesian")):
        c = d[key]
        n = c["nz"]
        ax.loglog(n, c["face_in"], "o-", color=fs.VERMILLION, label="face, interior")
        ax.loglog(n, c["face_wall"], "s--", color=fs.VERMILLION, label="face, wall")
        ax.loglog(n, c["D_in"], "o-", color=fs.GREEN, label="corrected-PE, interior")
        ax.loglog(n, c["D_wall"], "s--", color=fs.GREEN, label="corrected-PE, wall")
        for order, y0 in ((2, c["face_in"][0]), (4, c["D_in"][0])):
            ax.loglog([n[0], n[-1]], [y0 * 2.5, y0 * 2.5 * (n[-1] / n[0]) ** (-order)], ":", color=fs.BLUE, lw=.9)
            ax.text(n[-1] * 1.08, y0 * 2.5 * (n[-1] / n[0]) ** (-order), "$h^%d$" % order, fontsize=fs.SMALL_PT,
                    color=fs.BLUE, va="center")
        ax.set_xticks(n, [str(k) for k in n])
        ax.minorticks_off()
        ax.set_xlabel("cells $n_1$ [-]")
        ax.set_title(tag, fontsize=fs.LABEL_PT, loc="left")
    axes[0].set_ylabel("max error of the booked work [-]")
    axes[1].legend(fontsize=fs.SMALL_PT, frameon=False, loc="lower left")
    return fig
