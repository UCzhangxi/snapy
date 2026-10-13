"""Build options from YAML and reject unknown keys; snapy@6fbb39750f62b83df096058a4746e77d0a634bc5; no measured data."""
from .flow import make_flow


def make_fig():
    return make_flow(['YAML root', 'owning reader', 'fixed-key validation', 'sub-options', 'module construction'])
