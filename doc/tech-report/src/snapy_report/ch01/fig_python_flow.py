"""Expose the C++ API to Python; snapy@6fbb39750f62b83df096058a4746e77d0a634bc5; no measured data."""
from .flow import make_flow


def make_fig():
    return make_flow(['Python imports', 'extension bindings', 'Mesh / MeshBlock API', 'C++ stage and kernels'])
