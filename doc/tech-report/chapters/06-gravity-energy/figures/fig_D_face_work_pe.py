#!/usr/bin/env python3
"""Figure 6.4.1: the corrected-PE face gravity work (scheme D, SNAP_GRAVITY_WORK_RADIAL_EXACT).

(a) Interior cell i: the face form reads the two faces of the cell; the added term
    g1 sigma^2 s[rho_dot] reads the four faces i-3/2 .. i+3/2 (the three cells of the slope).
(b) Bottom wall: the slope is one-sided over cells 0, 1, 2, so W^D_0 reads faces 1/2, 3/2, 5/2
    (uniform grid: (19 F_1/2 - 5 F_3/2 + F_5/2)/24); the wall face carries F = 0 and no ghost
    cell is read.
(c) An x1 seam between two blocks: each block takes one-sided slopes at its own ends, so
    P = P_A + P_B; the seam face's flux and potential are shared and telescope.
(d) The implicit matrix: the energy row's coupling to the total-mass unknown, g1 sigma^2 s~/dt;
    inside it is s, at each end the third weight of the one-sided slope is lumped onto the
    neighbour so the block system stays tridiagonal; the post-solve term books the difference.
(e, f) Order of accuracy, max |W - g1 <F>_V| / |g1| over interior and wall cells, face form and
    D, read from checks/d_face_work_pe_check.json (written by checks/d_face_work_pe_check.py).

Formulas: snapy dae902b, src/hydro/gravity_work_radial.hpp, src/implicit/implicit_hydro.cpp.
Run: python3 fig_D_face_work_pe.py  (writes fig_D_face_work_pe.png next to this script)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "common"))
import figstyle as fs  # noqa: E402

import matplotlib.patches as mp  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

fs.apply()
W = 0.9  # cell width in the cartoons


def cell(ax, x, y, label=None, kind="fluid", color=None):
    hatch = {"ghost": "//", "solid": "xx"}.get(kind)
    ec = fs.PURPLE if kind == "ghost" else fs.BLACK
    fc = "white" if color is None else color
    ax.add_patch(mp.Rectangle((x, y), W, 1, fc=fc, ec=ec, lw=0.8, hatch=hatch))
    if label:
        ax.text(x - 0.08, y + 0.5, label, ha="right", va="center", fontsize=7.5)


def centroid(ax, x, y, color=fs.SKY, marker="o"):
    ax.plot([x + W / 2], [y + 0.5], marker=marker, color=color, ms=4.5, mec=fs.BLACK, mew=0.5)


def flux(ax, x, y, color=fs.ORANGE, lw=1.6, label=None, side="right"):
    ax.annotate("", xy=(x + W / 2, y + 0.28), xytext=(x + W / 2, y - 0.28),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=8))
    if label:
        dx = W + 0.08 if side == "right" else -0.08
        ax.text(x + dx, y, label, ha="left" if side == "right" else "right", va="center", fontsize=7.5,
                color=fs.BLACK)


def bracket(ax, x, y0, y1, color, text, side="right", off=0.0):
    """a square bracket beside the column with a short label"""
    xb = x + W + 1.15 + off if side == "right" else x - 0.75 - off
    d = -0.1 if side == "right" else 0.1
    ax.plot([xb + d, xb, xb, xb + d], [y0, y0, y1, y1], color=color, lw=1.6)
    ax.text(xb + (0.1 if side == "right" else -0.1), 0.5 * (y0 + y1), text, color=color,
            ha="left" if side == "right" else "right", va="center", fontsize=7.5)


def frame(ax, title):
    ax.set_aspect("equal")  # every cartoon spans 7.6 units in x1, so all share one scale
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=9)


fig = plt.figure(figsize=(fs.DOUBLE, 5.7))
outer = fig.add_gridspec(2, 1, height_ratios=[1.1, 1.0], hspace=0.22)
top = outer[0].subgridspec(1, 4, width_ratios=[1, 1, 1, 1.15], wspace=0.08)
bottom = outer[1].subgridspec(1, 2, wspace=0.28)

# (a) interior cell i -------------------------------------------------------------------
ax = fig.add_subplot(top[0])
labels = ["$i-2$", "$i-1$", "$i$", "$i+1$", "$i+2$"]
for k, lab in enumerate(labels):
    cell(ax, 0, k, lab, color="#EAF5FC" if k in (1, 2, 3) else None)
    centroid(ax, 0, k, color=fs.SKY if k in (1, 2, 3) else fs.GREY)
for k, lab in zip(range(1, 5), ["$F_{i-3/2}$", "$F_{i-1/2}$", "$F_{i+1/2}$", "$F_{i+3/2}$"]):
    flux(ax, 0, k, color=fs.ORANGE if k in (2, 3) else fs.GREEN, label=lab)
bracket(ax, 0, 2, 3, fs.ORANGE, "face")
bracket(ax, 0, 1, 4, fs.GREEN, "D", off=1.5)
ax.annotate("", xy=(-1.35, 4.9), xytext=(-1.35, 0.1),
            arrowprops=dict(arrowstyle="-|>", color=fs.BLACK, lw=0.8))
ax.text(-1.35, 5.2, "$x_1$", ha="center", va="bottom")
ax.set_xlim(-1.45, 4.15)
ax.set_ylim(-1.15, 6.45)
frame(ax, "(a) interior cell")

# (b) bottom wall ---------------------------------------------------------------------------
ax = fig.add_subplot(top[1])
for k in range(2):
    cell(ax, 0, -2 + k, kind="ghost")
ax.text(W + 0.15, -1.0, "ghosts:\nnot read", ha="left", va="center", fontsize=7.5, color=fs.PURPLE)
for k in range(4):
    cell(ax, 0, k, f"${k}$", color="#EAF5FC" if k < 3 else None)
    centroid(ax, 0, k, color=fs.SKY if k < 3 else fs.GREY)
ax.plot([-0.3, W + 0.3], [0, 0], color=fs.BLACK, lw=3)
ax.text(W + 0.4, 0.0, "wall: $F=0$", fontsize=7.5, va="center")
for k, lab in zip(range(1, 4), ["$F_{1/2}$", "$F_{3/2}$", "$F_{5/2}$"]):
    flux(ax, 0, k, color=fs.ORANGE if k == 1 else fs.GREEN, label=lab)
bracket(ax, 0, 0.1, 2.9, fs.GREEN, "$s_0$", side="left", off=0.2)
ax.set_xlim(-1.8, 3.8)
ax.set_ylim(-2.3, 5.3)
frame(ax, "(b) wall cell")

# (c) x1 seam --------------------------------------------------------------------------------
ax = fig.add_subplot(top[2])
names = ["A$_0$", "A$_1$", "A$_2$", "B$_0$", "B$_1$", "B$_2$"]
for k in range(6):
    cell(ax, 0, k, names[k], color="#EAF5FC" if k < 3 else "#F7E6EF")
    centroid(ax, 0, k, color=fs.SKY if k < 3 else fs.PURPLE, marker="o" if k < 3 else "s")
ax.plot([-0.35, W + 0.35], [3, 3], color=fs.PURPLE, lw=1.6, ls="--")
ax.text(W + 0.42, 3.0, "seam", fontsize=7.5, va="center")
bracket(ax, 0, 0.1, 2.9, fs.SKY, "$s$ in A", off=0.0)
bracket(ax, 0, 3.1, 5.9, fs.PURPLE, "$s$ in B", off=0.0)
ax.set_xlim(-1.4, 4.2)
ax.set_ylim(-0.8, 6.8)
frame(ax, "(c) x1 block seam")

# (d) implicit matrix --------------------------------------------------------------------
ax = fig.add_subplot(top[3])
n = 6
for i in range(n):
    for k in range(n):
        ax.add_patch(mp.Rectangle((k, n - 1 - i), 1, 1, fc="white", ec=fs.GREY, lw=0.5))
for i in range(n):
    cols = [0, 1, 2] if i == 0 else ([n - 3, n - 2, n - 1] if i == n - 1 else [i - 1, i, i + 1])
    for k in cols:
        lumped_away = (i == 0 and k == 2) or (i == n - 1 and k == n - 3)
        ax.add_patch(mp.Rectangle((k + 0.12, n - 1 - i + 0.12), 0.76, 0.76,
                                  fc="white" if lumped_away else fs.GREEN, ec=fs.GREEN, lw=1.0,
                                  hatch="////" if lumped_away else None))
for (i, kf, kt) in ((0, 2, 1), (n - 1, n - 3, n - 2)):
    y = n - 1 - i + 0.5
    ax.annotate("", xy=(kt + 0.55, y + 0.05), xytext=(kf + 0.45, y + 0.05),
                arrowprops=dict(arrowstyle="-|>", color=fs.VERMILLION, lw=1.3, mutation_scale=9))
ax.text(n / 2, n + 0.2, "columns: cells $k$", ha="center", va="bottom", fontsize=7.5)
ax.text(-0.15, n - 0.5, "$i=0$", ha="right", va="center", fontsize=7.5)
ax.text(-0.15, 0.5, "$n_1-1$", ha="right", va="center", fontsize=7.5)
ax.text(-0.15, n / 2, "rows:\ncells $i$", ha="right", va="center", fontsize=7.5)
ax.set_xlim(-2.1, n + 0.34)
ax.set_ylim(-0.8, n + 0.8)
frame(ax, "(d) VIC energy row")

# (e, f) convergence -----------------------------------------------------------------------
with open(os.path.join(HERE, "..", "checks", "d_face_work_pe_check.json")) as f:
    data = json.load(f)
for col, (key, title) in enumerate((("C6 spherical R=5H", "(e) spherical-polar, $r_0=5H$"),
                                    ("C6 Cartesian", "(f) Cartesian"))):
    ax = fig.add_subplot(bottom[col])
    d = data[key]
    nz = d["nz"]
    ax.loglog(nz, d["face_in"], "-o", color=fs.ORANGE, label="face form, interior")
    ax.loglog(nz, d["face_wall"], "--s", color=fs.ORANGE, mfc="white", label="face form, wall cells")
    ax.loglog(nz, d["D_in"], "-o", color=fs.GREEN, label="D, interior")
    ax.loglog(nz, d["D_wall"], "--s", color=fs.GREEN, mfc="white", label="D, wall cells")
    fs.slope_guide(ax, 32, d["face_in"][1] * 2.2, 200, 2)
    fs.slope_guide(ax, 32, d["D_in"][1] * 0.25, 200, 4)
    ax.set_xlabel("$n_1$ (cells over $4H$)")
    if col == 0:
        ax.set_ylabel("max $|W-g_1\\langle F\\rangle_V|\\,/\\,|g_1|$\n[kg m$^{-2}$ s$^{-1}$]")
    ax.set_title(title, loc="left")
    ax.set_xlim(12, 360)
    ax.set_xticks(nz)
    ax.set_xticklabels([str(v) for v in nz])
    ax.xaxis.set_minor_formatter(plt.NullFormatter())
    ax.grid(True, which="major", color="#DDDDDD", lw=0.5)
    if col == 0:
        fig.legend(loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.035))

fs.save(fig, __file__)
