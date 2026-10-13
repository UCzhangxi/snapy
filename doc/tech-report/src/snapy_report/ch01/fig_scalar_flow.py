"""Transport passive scalars with dry mass; snapy@6fbb39750f62b83df096058a4746e77d0a634bc5; no measured data."""
from .flow import make_flow


def make_fig():
    return make_flow(['dry density / scalar density', 'ratio reconstruction', 'hydro dry flux', 'panel states / donor copy', 'scalar increment'])
