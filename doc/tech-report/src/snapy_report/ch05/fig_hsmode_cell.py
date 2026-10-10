"""Hydrostatic mode (chapter 5): gravity replaced by the cell's own reconstructed face-pressure difference.

One cell between its two x1 faces (x1 upward here): the left state at the upper face and the right state at the
lower face, the Riemann face pressures p* at both faces, and the body force (1 - nh) of which is replaced. Cartoon;
no data. Code it depicts: snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy),
src/hydro/hydro_forward.cpp lines 389-397 and 901-906.
"""
from snapy_report.ch05 import _style as fs
from snapy_report.ch05 import _draw as d


def make_fig():
    fig, ax = fs.new_figure("single", 2.6)
    fs.cartoon(ax)
    fs.cell(ax, 0.0, 0.0, 1.6, 1.6, label="$i$", fill=True)
    fs.face_value(ax, 0.8, 1.45)
    d.text(ax, 1.75, 1.45, "$p^{L}_{i+1/2}$ (cell $i$)", ha="left")
    fs.face_value(ax, 0.8, 0.15)
    d.text(ax, 1.75, 0.15, "$p^{R}_{i-1/2}$ (cell $i$)", ha="left")
    fs.face_flux(ax, 0.8, 1.9, 0.0, 0.4)
    d.text(ax, 1.75, 1.95, "$p^{*}_{i+1/2}$", ha="left")
    fs.face_flux(ax, 0.8, -0.3, 0.0, 0.4)
    d.text(ax, 1.75, -0.3, "$p^{*}_{i-1/2}$", ha="left")
    d.arrow(ax, (-0.45, 1.3), (-0.45, 0.3), color=fs.VERMILLION)
    d.text(ax, -0.6, 0.8, "$(1-n_h)\\,\\overline{\\rho}_i g_1$", ha="right", color=fs.BLACK)
    d.arrow(ax, (-0.15, 0.3), (-0.15, 1.3), color=fs.GREEN)
    ax.set_xlim(-2.6, 3.9)
    ax.set_ylim(-0.7, 2.3)
    return fig
