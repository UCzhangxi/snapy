"""Flow of the gravity-work fixer's defect through one step; snapy@e894700ff7aee30b52882e5202b16461413780b0.

Cartoon of src/hydro/hydro_forward.cpp:858-889 and 985-996 and src/mesh/meshblock.cpp:832-911; no measured data.
"""
from snapy_report.ch01.flow import make_flow


def make_fig():
    return make_flow([
        "each stage s: defect d_s = V-sum of cell work + face work of F - F^R + phi dm (+ implicit part)",
        "weight it by w2_s times the later stages' w1 and add it to D",
        "last stage: sum D, the fluid mass and the wall-face mass over blocks and ranks (one allreduce)",
        "refuse the step if more than 1e3 eps of the wall cells' mass crossed an x1 wall",
        "add -D rho_i / sum(rho V) to every cell's energy; log the fix as fixgrav=",
    ])
