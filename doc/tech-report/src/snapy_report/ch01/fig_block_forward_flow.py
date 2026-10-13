"""Exchange before a single-block stage; snapy@6fbb39750f62b83df096058a4746e77d0a634bc5; no measured data."""
from .flow import make_flow


def make_fig():
    return make_flow(['caller modifies interior', 'conserved exchange', 'advance_local', 'physical boundary fill'])
