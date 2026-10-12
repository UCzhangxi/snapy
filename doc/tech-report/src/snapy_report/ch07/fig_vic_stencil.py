"""The block row of cell i in the VIC system: the Roe matrices |A| at the two faces, the flux Jacobians in the
three cells and the coefficients a, b, c, from vic_assemble_full_impl (src/implicit/vic_assemble_full_impl.h:51-99
at snapy@e894700ff7aee30b52882e5202b16461413780b0). A cartoon; it reads no data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 2.4))
    ax.set_axis_off()
    for k, lab in enumerate(["i-1", "i", "i+1"]):
        x = 0.4 + 2.2 * k
        ax.add_patch(plt.Rectangle((x, 0.9), 2.2, 1.0, fc="#EAF5FC", ec=fs.BLACK, lw=0.7))
        ax.plot(x + 1.1, 1.4, "o", color=fs.SKY, ms=6, mec=fs.BLACK, mew=0.5)
        ax.text(x + 1.1, 1.62, "cell %s" % lab, ha="center", fontsize=8)
        ax.text(x + 1.1, 1.08, r"$J_{%s}$" % lab, ha="center", fontsize=9, color=fs.BLUE)
    for k, lab in enumerate([r"$\mathsf{A}^-$, $A_i$", r"$\mathsf{A}^+$, $A_{i+1}$"]):
        x = 2.6 + 2.2 * k
        ax.plot([x, x], [0.9, 1.9], color=fs.ORANGE, lw=2.0)
        ax.text(x, 2.0, lab, ha="center", fontsize=8, color=fs.ORANGE)
    ax.text(0.4, 0.55, r"$\mathsf{B}_i=-\frac{A_i}{2V_i}\,(\mathsf{A}^-+J_{i-1})$", fontsize=9)
    ax.text(4.8, 0.55, r"$\mathsf{C}_i=-\frac{A_{i+1}}{2V_i}\,(\mathsf{A}^+-J_{i+1})$", fontsize=9)
    ax.text(0.4, 0.1, r"$\mathsf{A}_i=\frac{1}{2V_i}\,(A_i\mathsf{A}^-+A_{i+1}\mathsf{A}^++(A_{i+1}-A_i)J_i)+\mathsf{I}/\Delta t$"
            r"$\;(-\,\Phi$, gravity$)$", fontsize=9)
    ax.set_xlim(0, 8.0)
    ax.set_ylim(0, 2.25)
    return fig
