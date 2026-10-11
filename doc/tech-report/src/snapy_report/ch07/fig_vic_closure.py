"""The column closure: the ghost below the first cell (and above the last) is the mirror of its neighbour,
d_ghost = Bnd d, Bnd = diag(1, -1, 1, 1, 1), folded into the diagonal block
(src/implicit/vic_assemble_full_impl.h:44-45, 122-126 at snapy@e894700ff7aee30b52882e5202b16461413780b0).
A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 2.0))
    ax.set_axis_off()
    ax.add_patch(plt.Rectangle((0.3, 0.4), 1.6, 1.0, fc="#F4E1EC", ec=fs.PURPLE, lw=0.8, ls="--"))
    ax.text(1.1, 1.15, "ghost", ha="center", fontsize=8, color=fs.PURPLE)
    ax.text(1.1, 0.75, r"$\mathrm{Bnd}\,\delta_{0}$", ha="center", fontsize=9)
    for k in range(2):
        ax.add_patch(plt.Rectangle((1.9 + 1.6 * k, 0.4), 1.6, 1.0, fc="#EAF5FC", ec=fs.BLACK, lw=0.7))
        ax.text(2.7 + 1.6 * k, 0.75, r"$\delta_{%d}$" % k, ha="center", fontsize=9)
    ax.plot([1.9, 1.9], [0.3, 1.5], color=fs.BLACK, lw=2.2)
    ax.text(1.9, 1.6, "wall", ha="center", fontsize=8)
    ax.annotate("", xy=(1.3, 0.55), xytext=(2.5, 0.55),
                arrowprops=dict(arrowstyle="->", color=fs.PURPLE, lw=0.8, connectionstyle="arc3,rad=0.4"))
    ax.text(5.6, 1.15, r"$b_0\,\delta_{-1}$ with $\delta_{-1}=\mathrm{Bnd}\,\delta_0$:", fontsize=9)
    ax.text(5.6, 0.75, r"$a_0\leftarrow a_0+b_0\,\mathrm{Bnd}$, $\;\mathrm{Bnd}=\mathrm{diag}(1,-1,1,1,1)$", fontsize=9)
    ax.text(5.6, 0.35, "mass, transverse momentum, energy: no wall flux", fontsize=8, color=fs.GREEN)
    ax.set_xlim(0.2, 11.6)
    ax.set_ylim(0.2, 1.8)
    return fig
