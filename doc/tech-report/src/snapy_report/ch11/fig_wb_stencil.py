"""Keep wall ghosts consistent with the hydrostatic reference; schematic, no measured data."""
from .diagrams import make_stencil

def make_fig():
    return make_stencil('wb')
