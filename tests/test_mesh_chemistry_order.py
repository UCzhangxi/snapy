"""A Mesh runs chemistry in the same order as a bare block.

On the last stage a bare MeshBlock runs its scheduled chemistry op, then the stage boundaries, then the axial
closure (MeshBlockImpl::forward). A Mesh runs the stage, then the axial closure over its blocks, then the
chemistry of each block (Mesh::forward). The closure adds momentum but no energy, so the chemistry's
temperature depends on which runs first.

The deck: the reduced Jupiter chemistry case of test_sk4_chemistry_source (water and ammonia clouds and rain)
on one gnomonic-equiangle block of a thin shell, FP64, with conserve-axial-momentum: exact, Coriolis about the
closure's axis, a horizontal wind, reflecting walls. A one-block Mesh and a bare MeshBlock take the same
steps from the same state; their interiors must be equal bitwise after every step.

Controls, which must hold before and after the fix: with the closure off, or with no chemistry, the two are
equal bitwise, so a difference is the order of the two.

  python test_mesh_chemistry_order.py [--steps 3]
"""
import argparse
import os
import sys
import tempfile

import torch
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_sk4_chemistry_source import config  # noqa: E402

import kintera as kt  # noqa: E402
from snapy import Mesh, MeshBlock, MeshBlockOptions, MeshOptions, kICY, kIDN, kIPR, kIV1  # noqa: E402

NGHOST = 3
R0 = 6.0e6
WIND = 20.0
OMEGA = 1.0e-3
DT = 0.1


def deck(closure):
    cfg = config("float64")
    cfg["geometry"] = {
        "type": "gnomonic-equiangle",
        "bounds": {"x1min": R0, "x1max": R0 + 2.0e5, "x2min_pi": -0.02, "x2max_pi": 0.02,
                   "x3min_pi": -0.02, "x3max_pi": 0.02},
        "cells": {"nx1": 24, "nx2": 4, "nx3": 4, "nghost": NGHOST, "interp_order": 4},
    }
    cfg["distribute"] = {"layout": "slab", "nb2": 1, "nb3": 1}
    # exact needs FP64 and neither the anomaly nor the perturbation flux
    cfg["dynamics"].update({"anomaly": False, "perturbation-flux": False,
                            "conserve-axial-momentum": closure})
    cfg["forcing"].pop("diffusion", None)  # needs the cubed-sphere layout on this geometry
    cfg["forcing"]["coriolis"] = {"type": "xyz", "omega1": OMEGA}
    for face in ("x2-inner", "x2-outer", "x3-inner", "x3-outer"):
        cfg["boundary-condition"]["external"][face] = "reflecting"
    return cfg


def fill(block):
    w = block.module("hydro").buffer("D").clone().zero_()
    ty = block.module("hydro.eos.thermo")
    z = block.module("coord").buffer("x1v") - R0
    temp = (400.0 - 1.0e-3 * z).clamp_min(150.0)
    rd = 8.31446261815324 * ty.buffer("inv_mu")[0]
    pressure = 1.0e7 * (temp / 400.0) ** (24.79 / (rd * 0.001))
    w[kIPR] = pressure.view(1, 1, -1)
    w[kIDN] = (pressure / (rd * temp)).view(1, 1, -1)
    w[kICY].fill_(0.01)
    w[kICY + 1].fill_(0.001)
    w[kICY + 3].fill_(1.0e-5)
    w[kICY + 5].fill_(1.0e-6)
    w[kIV1] = (0.01 * torch.sin(torch.pi * z / 2.0e5)).view(1, 1, -1)
    w[kIV1 + 1] = WIND
    w[kIV1 + 2] = 0.5 * WIND
    return {"hydro_w": w, "scalar_r": torch.full_like(w[:1], 0.001)}


def make(closure, chemistry):
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(deck(closure), f)
        path = f.name
    try:
        kin = kt.KineticsOptions.from_yaml(path)
        block = MeshBlock(MeshBlockOptions.from_yaml(path))
        options = MeshOptions.from_yaml(path)
        options.blocks_per_process(1)
        mesh = Mesh(options)
        if chemistry:
            block.set_chemistry(kin)
            mesh.set_chemistry(kin)
    finally:
        os.unlink(path)
    (mb,) = list(mesh.blocks)
    bv, _ = block.initialize(fill(block))
    mv, _ = mesh.initialize([fill(mb)])
    return block, bv, mesh, mv


def interior(t):
    return t[:, NGHOST:-NGHOST, NGHOST:-NGHOST, NGHOST:-NGHOST].double()


def run(closure, chemistry, steps):
    """per step: (cells that differ, max |d|, max |d|/|ref|) over the interior of hydro_u and scalar_r"""
    block, bv, mesh, mv = make(closure, chemistry)
    out = []
    for step in range(steps):
        for stage in range(len(block.intg.stages)):
            block.forward(bv, DT, stage)
            mesh.forward(mv, DT, stage)
        cells, dmax, rmax = 0, 0.0, 0.0
        for key in ("hydro_u", "scalar_r"):
            a, b = interior(bv[key]), interior(mv[0][key])
            assert torch.isfinite(a).all() and torch.isfinite(b).all(), (closure, chemistry, step, key)
            d = (a - b).abs()
            cells += int((d > 0).sum())
            dmax = max(dmax, d.max().item())
            rmax = max(rmax, (d / a.abs().clamp_min(1.0e-300)).max().item())
        out.append((cells, dmax, rmax))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=3)
    args = ap.parse_args()
    torch.set_num_threads(1)
    failures = []
    for closure, chemistry, what in (("off", True, "control: closure off"),
                                     ("exact", False, "control: no chemistry")):
        diffs = run(closure, chemistry, args.steps)
        print("%s: %s" % (what, diffs), flush=True)
        if any(c for c, _, _ in diffs):
            failures.append("%s: the Mesh and the bare block differ, %s" % (what, diffs))
    diffs = run("exact", True, args.steps)
    print("closure exact with chemistry: %s" % diffs, flush=True)
    bad = [s for s, (c, _, _) in enumerate(diffs) if c]
    if bad:
        c, d, r = diffs[bad[0]]
        failures.append("closure exact with chemistry: the Mesh differs from the bare block from step %d "
                        "(%d cells, max |d| %.3e, max rel %.3e)" % (bad[0], c, d, r))
    for f in failures:
        print("FAIL:", f)
    print("PASSED" if not failures else "FAILED (%d)" % len(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
