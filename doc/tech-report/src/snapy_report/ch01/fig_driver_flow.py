"""Driver loop and accepted steps; snapy@6fbb39750f62b83df096058a4746e77d0a634bc5; no measured data."""
from .flow import make_flow


def make_fig():
    return make_flow(['caller: choose dt', 'all stages', 'kinetics (run_hydro)', 'reject / accept', 'accepted outputs'])
