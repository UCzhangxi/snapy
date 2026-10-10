"""Call ownership at snapy@e894700ff7aee30b52882e5202b16461413780b0; no data."""
from .flow import make_tree


def make_fig():
    return make_tree('Mesh / MeshBlock', ['caller: drives stages', 'hydro / scalar: increments',
                                       'layout: exchanges', 'external integrator / thermo'])
