"""Radial face moment over h^2/12 and face-centroid shift over its leading term, against h / x^m.

Closed forms of CoordinateImpl::radial_face_moment2_ and radial_face_centroid_shift_
(src/coord/coordinate.cpp:446-488) at snapy@6fbb39750f62b83df096058a4746e77d0a634bc5. Analytic; it reads no data.
"""
import numpy as np

from snapy_report import figstyle as fs


def make_fig():
    fig, ax = fs.new_figure(fs.SINGLE, 2.4)
    q = np.linspace(0.0, 1.6, 200)  # h / x^m, below the degenerate limit 2
    moment = 1.0 - q**2 / 12.0
    shift = (12.0 - q**2) / (12.0 + q**2)
    ax.plot(q, moment, color=fs.GREEN, ls="-", label=r"$\mathtt{face\_moment2\_x1}/(\Delta x_1^2/12)$")
    ax.plot(q, shift, color=fs.BLUE, ls="--", label=r"$\mathtt{face\_centroid\_shift\_x1}/(\Delta x_1^2/(12x^{\mathrm{m}}))$")
    ax.set_xlabel(r"$\Delta x_1/x^{\mathrm{m}}$ [-]")
    ax.set_ylabel("ratio [-]")
    ax.set_ylim(0.5, 1.05)
    ax.legend(loc="lower left", frameon=False)
    return fig
