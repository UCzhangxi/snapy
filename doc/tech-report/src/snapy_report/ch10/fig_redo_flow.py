"""Step acceptance for the moist causes; snapy@6fbb39750f62b83df096058a4746e77d0a634bc5.

Cartoon of local_redo_flags, reduce_redo_flags and apply_redo (src/mesh/meshblock.cpp:1238-1353); no measured data.
"""
from snapy_report.ch01.flow import make_flow


def make_fig():
    return make_flow([
        "local flags: floor, clamp, limiter, nan, saturation, vic-solve",
        "MAX over every block and rank -> one cause word",
        "no cause: accept, reset the redo counter",
        "cause and redo count <= max_redo: restore the saved state, redo with dt/2",
        "redo count > max_redo: terminate (restore first only for vic-solve)",
    ])
