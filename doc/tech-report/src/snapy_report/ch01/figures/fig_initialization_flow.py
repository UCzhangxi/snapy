"""Initialize primitives, ghosts and conserved states; snapy@6fbb39750f62b83df096058a4746e77d0a634bc5; no measured data."""
from ..flow import make_flow


def make_fig():
    return make_flow(['shape checks', 'physical primitive ghosts', 'primitive exchange', 'EOS and scalar density', 'solids / conserved ghosts'])
