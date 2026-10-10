"""Step acceptance for the moist causes; snapy@e894700ff7aee30b52882e5202b16461413780b0.

Cartoon of local_redo_flags, reduce_redo_flags and apply_redo (src/mesh/meshblock.cpp:1229-1304); no measured data.
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
