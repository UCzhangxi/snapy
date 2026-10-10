"""Transport passive scalars with dry mass; snapy@e894700ff7aee30b52882e5202b16461413780b0; no measured data."""
from .flow import make_flow


def make_fig():
    return make_flow(['dry density / scalar density', 'ratio reconstruction', 'hydro dry flux', 'panel states / donor copy', 'scalar increment'])
