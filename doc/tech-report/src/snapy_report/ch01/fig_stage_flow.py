"""Accumulate and combine one stage; snapy@e894700ff7aee30b52882e5202b16461413780b0; no measured data."""
from .flow import make_flow


def make_fig():
    return make_flow(['publish stage / save', 'hydro increment', 'scalar / dry carry', 'user increments', 'RK / limiter / solids', 'last-stage adjustment / BC'])
