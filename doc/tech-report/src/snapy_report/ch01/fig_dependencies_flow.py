"""Dependency ownership at snapy@6fbb39750f62b83df096058a4746e77d0a634bc5; no data."""
from .flow import make_tree


def make_fig():
    return make_tree('snapy', ['Harp: integrator', 'Kintera: thermo / restart',
                             'torch: tensor runtime', 'comm / IO libraries'])
