"""Dependency map of the chapter 6 schemes; snapy@e894700ff7aee30b52882e5202b16461413780b0.

Logical relations read from the code the scheme files cite (const_gravity.cpp:28-41, hydro.cpp:56-81 and 116-126,
hydro_forward.cpp:813-849, implicit_hydro.cpp:266-277); no measured data.
"""
import matplotlib.pyplot as plt

from snapy_report import figstyle as fs
from snapy_report.ch06._draw import arrow, bare, label, node


def make_fig():
    fs.apply()
    fig, ax = plt.subplots(figsize=(fs.DOUBLE, 2.9))
    bare(ax)
    ax.set(xlim=(0, 1), ylim=(0, 1.06))
    cell = node(ax, .12, .80, "cell form\n(gravity-work: cell)")
    face = node(ax, .50, .80, "face form\n(gravity-work: face)")
    dwork = node(ax, .85, .80, "corrected-PE face work\n(SNAP_GRAVITY_WORK_\nRADIAL_EXACT)")
    fixer = node(ax, .12, .18, "gravity-work fixer")
    wallc = node(ax, .50, .18, "face-wallc")
    vic = node(ax, .85, .18, "VIC gravity work\n(cell and face rows)")
    curv = label(ax, .58, 1.0, "curvature flux K", color=fs.VERMILLION)
    inv = label(ax, .97, .50, "E + P")
    fig.canvas.draw()
    arrow(ax, fixer, cell)  # requires
    arrow(ax, dwork, face)  # requires
    arrow(ax, dwork, inv, ls="--")  # implies
    arrow(ax, dwork, curv, style="-[", color=fs.VERMILLION)  # turns off
    arrow(ax, face, fixer, style="-[", color=fs.VERMILLION)  # refused with
    arrow(ax, wallc, fixer, style="-[", color=fs.VERMILLION)
    arrow(ax, vic, face)  # its face rows require the face form
    return fig
