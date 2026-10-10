"""Dependency ownership at snapy@e894700ff7aee30b52882e5202b16461413780b0; no data."""
from .flow import make_tree


def make_fig():
    return make_tree('snapy', ['Harp: integrator', 'Kintera: thermo / restart',
                             'torch: tensor runtime', 'comm / IO libraries'])
