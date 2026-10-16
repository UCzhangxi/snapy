"""Accumulate and combine one stage; snapy@6fbb39750f62b83df096058a4746e77d0a634bc5; no measured data."""
from ..flow import make_flow


def make_fig():
    return make_flow(['publish stage / save', 'hydro increment', 'scalar / dry carry', 'user increments', 'RK / limiter / solids', 'last-stage adjustment / BC'])
