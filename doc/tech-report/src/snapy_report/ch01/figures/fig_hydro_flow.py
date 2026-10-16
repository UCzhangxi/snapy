"""Follow the hydro increment through seven sections; snapy@6fbb39750f62b83df096058a4746e77d0a634bc5; no measured data."""
from ..flow import make_flow


def make_fig():
    return make_flow(['EOS', 'x1 flux / seam', 'horizontal LR / panel', 'flux / donor factors', 'divergence / geometry', 'forcing / gravity', 'implicit increment'])
