"""Select outgoing acoustic and advected perturbations; schematic, no measured data."""
from .diagrams import make_stencil

def make_fig():
    return make_stencil('outflow')
