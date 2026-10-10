"""Dispatch tensor kernels by device; snapy@e894700ff7aee30b52882e5202b16461413780b0; no measured data."""
from .flow import make_flow


def make_fig():
    return make_flow(['tensor device / dtype', 'dispatch stub', 'CPU columns | CUDA kernels', 'pointwise | line | tiled'])
