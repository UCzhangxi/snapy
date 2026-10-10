"""Repeat the nearest owned cell; schematic, no measured data."""
from .diagrams import make_stencil

def make_fig():
    return make_stencil('extrapolation')
