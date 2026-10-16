"""The settling column of limiter_meters_check: theta of each cell and the offered and cut |flux| of each face,
from which thetamin, thetasevere and limcut are read (src/hydro/hydro_forward.cpp:762-818 at
snapy@6fbb39750f62b83df096058a4746e77d0a634bc5). Computed with limiter_meters_check.
"""
import numpy as np

from snapy_report import figstyle as fs
from snapy_report.ch13.checks.limiter_meters_check import settling_column, theta_of


def make_fig():
    rho_d, rho_y, flux, vol, area, dt = settling_column()
    theta, _ = theta_of(rho_y, flux, vol, area, dt)
    donor = np.concatenate([[1.], theta, [1.]])
    up = np.where(flux > 0., donor[:-1], donor[1:])
    fig, (a1, a2) = fs.new_figure(fs.DOUBLE, 2.3, 1, 2)
    a1.bar(np.arange(len(theta)), theta, color=fs.SKY, width=0.6)
    a1.axhline(0.9, color=fs.VERMILLION, lw=0.8, ls="--")
    a1.text(5.4, 0.92, "severe below 0.9", fontsize=fs.SMALL_PT, color=fs.VERMILLION, ha="right")
    a1.set_xlabel("cell")
    a1.set_ylabel(r"$\Theta$")
    a1.set_ylim(0, 1.1)
    k = np.arange(len(flux))
    a2.bar(k - 0.18, np.abs(flux), width=0.34, color=fs.ORANGE, label="offered")
    a2.bar(k + 0.18, np.abs(flux) - np.abs(up * flux), width=0.34, color=fs.VERMILLION, label="cut")
    a2.set_xlabel("face")
    a2.set_ylabel(r"$|F|$")
    a2.legend(fontsize=fs.SMALL_PT, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
    return fig
