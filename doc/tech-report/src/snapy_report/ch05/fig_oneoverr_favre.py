"""What is left of the 1/R term (chapter 5): a ratio of r^2 means is not a mean.

Profiles across one radial cell: rho w, rho and their ratio, against the plain mean of w. The Favre velocity
<rho w>/<rho> that the x1 maps reconstruct differs from the plain mean of w by O(h^2), which the 2/r of the
divergence turns into an O(h^2/R) term. Cartoon with illustrative profiles, no run. Concept from
docs/derivations/x1-centroid-spherical.md section 6 at snapy@e894700ff7aee30b52882e5202b16461413780b0 (chengcli/snapy).
"""
import numpy as np

from snapy_report.ch05 import _style as fs


def make_fig():
    fig, ax = fs.new_figure("single", 2.3)
    xx = np.linspace(-0.5, 0.5, 101)
    rho = np.exp(-1.6 * xx)
    w = 0.6 + 0.9 * xx + 0.8 * xx ** 2
    favre = np.trapezoid(rho * w * (1 + 0.4 * xx) ** 2, xx) / np.trapezoid(rho * (1 + 0.4 * xx) ** 2, xx)
    plain = np.trapezoid(w, xx)
    ax.plot(xx, w, color=fs.BLACK, label="$w(r)$")
    ax.axhline(plain, color=fs.BLUE, ls="--", label="plain mean of $w$")
    ax.axhline(favre, color=fs.VERMILLION, ls=":", label="$\\langle\\rho w\\rangle/\\langle\\rho\\rangle$")
    ax.set_xlabel("$(r - \\overline{r}_i)/h$ [-]")
    ax.set_ylabel("$w$ [arb.]")
    ax.set_yticks([])
    ax.legend(loc="upper left")
    return fig
