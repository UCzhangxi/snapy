"""Wrap values through a callback or the layout; schematic, no measured data."""
from .diagrams import make_stencil

def make_fig():
    return make_stencil('periodic')
