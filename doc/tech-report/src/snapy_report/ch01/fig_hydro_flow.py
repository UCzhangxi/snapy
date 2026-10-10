"""Follow the hydro increment through seven sections; snapy@e894700ff7aee30b52882e5202b16461413780b0; no measured data."""
from .flow import make_flow


def make_fig():
    return make_flow(['EOS', 'x1 flux / seam', 'horizontal LR / panel', 'flux / donor factors', 'divergence / geometry', 'forcing / gravity', 'implicit increment'])
