"""Where the saturation adjustment sits in one RK step; snapy@e894700ff7aee30b52882e5202b16461413780b0.

Cartoon of MeshBlockImpl::forward (src/mesh/meshblock.cpp:609-841) and the driver's check_redo; no measured data.
"""
from snapy_report.ch01.flow import make_flow


def make_fig():
    return make_flow([
        "stage 0: save the state, drain the saturation-failure counter",
        "every stage: forward, RK average, whole-column conserved limiter",
        "last stage only: whole-column limiter again",
        "last stage only: UV adjustment of the interior cells (kintera ThermoY)",
        "boundary fill of the ghosts",
        "after the step: check_redo reads the failure count",
    ])
