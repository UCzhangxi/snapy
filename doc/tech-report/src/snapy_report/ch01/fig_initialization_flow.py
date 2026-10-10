"""Initialize primitives, ghosts and conserved states; snapy@e894700ff7aee30b52882e5202b16461413780b0; no measured data."""
from .flow import make_flow


def make_fig():
    return make_flow(['shape checks', 'physical primitive ghosts', 'primitive exchange', 'EOS and scalar density', 'solids / conserved ghosts'])
