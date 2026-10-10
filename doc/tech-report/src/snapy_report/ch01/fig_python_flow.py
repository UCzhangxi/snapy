"""Expose the C++ API to Python; snapy@e894700ff7aee30b52882e5202b16461413780b0; no measured data."""
from .flow import make_flow


def make_fig():
    return make_flow(['Python imports', 'extension bindings', 'Mesh / MeshBlock API', 'C++ stage and kernels'])
