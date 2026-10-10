"""Order physical fills, exchange and corner refresh; schematic, no measured data."""
from .diagrams import make_stencil

def make_fig():
    return make_stencil('timing')
