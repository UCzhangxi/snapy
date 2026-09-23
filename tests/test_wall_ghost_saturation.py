#!/usr/bin/env python3
"""A wall ghost must mirror the interior cell AFTER the saturation adjustment, not before.

The final-stage saturation adjustment (and conserved limiter) change interior cells; the physical
boundary ghosts must be filled AFTER that, or a wall cell whose condensate evaporated keeps a stale
ghost and, at the next stage 0, LMARS sees a pressure jump at the wall and mass crosses it.

Moist slab column, reflecting x1 walls, no gravity, warm unsaturated vapour, 3 cycles:
  wall      cloud only in the bottom and top interior cells (evaporates at cycle 1)
  interior  the same cloud only in cells well away from both walls (control)

The discriminating check is the WALL GHOST, not mass conservation: after the final stage the
condensate in the first physical ghost must be the exact mirror of its interior cell. Filling
the ghosts before the adjustment leaves the `wall` arm's ghost holding the cloud the adjustment
just evaporated -- a gap of the whole planted cloud. The `interior` arm is the control. Both
arms still conserve total and dry mass to 1e-13, and the bite check still applies.

  python test_wall_ghost_saturation.py
"""
import os
import sys
import tempfile
from pathlib import Path

import torch
import yaml

HERE = Path(__file__).resolve().parent
TOL = 1.0e-13
# the boundary function COPIES, so the mirror is exact; 1e-9 of the planted cloud is
# nine orders below the gap a pre-adjustment ghost fill leaves behind
GHOST_TOL = 1.0e-9


def run(arm):
    from snapy import MeshBlock, MeshBlockOptions, kICY, kIDN, kIPR

    with open(HERE / "test_tracer_dry_convention.yaml") as f:
        c = yaml.safe_load(f)
    c.pop("scalar", None)
    c["forcing"] = {}
    c["integration"]["implicit-scheme"] = 0
    c["dynamics"]["equation-of-state"]["limiter"] = True
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, dir=os.getcwd()) as f:
        yaml.safe_dump(c, f)
        tmp = f.name
    try:
        block = MeshBlock(MeshBlockOptions.from_yaml(tmp))
    finally:
        os.unlink(tmp)
    ng, nx1 = c["geometry"]["cells"]["nghost"], c["geometry"]["cells"]["nx1"]
    w = dict(block.named_buffers())["hydro.D"].clone().zero_()
    w[kIPR] = 1.0e5
    w[kIDN] = 1.0e5 / (3900.0 * 320.0)
    w[kICY] = 0.005
    il, iu = ng, ng + nx1 - 1
    if arm == "wall":
        w[kICY + 1][..., il] = 1.0e-3
        w[kICY + 1][..., iu] = 1.0e-3
    else:
        w[kICY + 1][..., il + 8] = 1.0e-3
        w[kICY + 1][..., iu - 8] = 1.0e-3
    v, _ = block.initialize({"hydro_w": w})
    I = (slice(None), slice(ng, -ng), slice(ng, -ng))
    vol = block.module("coord").cell_volume()[I]

    def mass():
        u = v["hydro_u"]
        return (float(((u[kIDN] + u[kICY:].sum(0))[I] * vol).sum()), float((u[kIDN][I] * vol).sum()),
                float((u[kICY + 1][I] * vol).sum()))

    m0, d0, c0 = mass()
    # the scale the ghost gap is measured against: the condensate actually planted
    cond_scale = float(v["hydro_u"][kICY + 1].abs().max())
    evaporated = False
    gap = 0.0
    for _ in range(3):
        dt = block.max_time_step(v)
        for stage in range(len(block.intg.stages)):
            block.forward(v, dt, stage)
        cond = v["hydro_u"][kICY + 1]
        gap = max(gap,
                  float((cond[..., il - 1] - cond[..., il]).abs().max()),
                  float((cond[..., iu + 1] - cond[..., iu]).abs().max()))
        evaporated = evaporated or mass()[2] < 1.0e-6 * c0
    m1, d1, _ = mass()
    return abs(m1 / m0 - 1), abs(d1 / d0 - 1), c0, evaporated, gap, cond_scale


def main():
    failures = []
    for arm in ("wall", "interior"):
        dm, dd, c0, evap, gap, scale = run(arm)
        print(f"{arm:8s}: total mass rel {dm:.3e}  dry mass rel {dd:.3e}  initial cloud {c0:.3e}  "
              f"evaporated={evap}  ghost/interior condensate gap {gap:.3e} of {scale:.3e}")
        if not (c0 > 0 and evap):
            failures.append(f"{arm}: the cloud did not exist or did not evaporate; test cannot bite")
        if not (scale > 0):
            failures.append(f"{arm}: no condensate was planted; the ghost check cannot bite")
        if not (gap <= GHOST_TOL * scale):
            failures.append(
                f"{arm}: the first physical ghost is not the mirror of its interior cell "
                f"(condensate gap {gap:.3e}, {gap / scale:.3e} of the planted cloud); "
                "the wall ghosts were filled before the saturation adjustment")
        if not (dm < TOL and dd < TOL):
            failures.append(f"{arm}: mass not conserved (total {dm:.3e}, dry {dd:.3e})")
    for msg in failures:
        print("FAIL:", msg)
    if failures:
        sys.exit(1)
    print("### wall ghost / saturation adjustment test passed. ###")


if __name__ == "__main__":
    main()
