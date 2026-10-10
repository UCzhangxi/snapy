"""Rectify a mask and close fluid faces against solids; schematic, no measured data."""
from .diagrams import make_stencil

def make_fig():
    return make_stencil('solids')
