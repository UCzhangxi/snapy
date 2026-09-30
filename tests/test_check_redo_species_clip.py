#!/usr/bin/env python3
"""check_redo must not redo a step whose only limiter action was a species clip.

A redo pays when a smaller time step removes its cause. Density and energy repairs can shrink
with dt; a clipped negative cloud or vapor mass need not, and a moist run that clips species
every step then redoes every step until the redo budget runs out and the run terminates.
A 2D moist Jupiter CRM dies that way after a few cycles, all causes
"limiter", while it ran 400 cycles when only density and energy repairs marked a step.

The step starts from a uniform moist block with one interior cell carrying a small negative
cloud (-1e-6 of the density, far above round-off). A control step without that cell must be
accepted, and so must the step whose only repair is clipping that cloud.

  python test_check_redo_species_clip.py [--device cuda]
"""
import argparse
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
CLIP = -1.0e-6  # cloud mass per unit density planted in one interior cell


def start(device, yaml_file, clip):
    from snapy import MeshBlock, MeshBlockOptions, kICY, kIDN, kIPR

    block = MeshBlock(MeshBlockOptions.from_yaml(yaml_file))
    block.to(torch.device(device))
    w = dict(block.named_buffers())["hydro.D"].clone().zero_()
    w[kIDN] = 1.0
    w[kIPR] = 1.0e5
    w[kICY] = 1.0e-3  # vapor; cloud (kICY + 1) is zero
    block_vars, _ = block.initialize({"hydro_w": w})
    if clip:
        u = block_vars["hydro_u"]
        k, j, i = u.size(1) // 2, u.size(2) // 2, u.size(3) // 2
        u[kICY + 1, k, j, i] = CLIP * u[kIDN, k, j, i]
    return block, block_vars


def step(block, block_vars):
    dt = block.max_time_step(block_vars)
    for stage in range(len(block.intg.stages)):
        block.forward(block_vars, dt, stage)
    return block.check_redo(block_vars)


def control_arm(device, yaml_file):
    block, block_vars = start(device, yaml_file, clip=False)
    err = step(block, block_vars)
    return None if err == 0 else "a step with nothing to clip was rejected (err=%d)" % err


def clip_arm(device, yaml_file):
    block, block_vars = start(device, yaml_file, clip=True)
    err = step(block, block_vars)
    return None if err == 0 else "a step whose only repair was a species clip was rejected (err=%d)" % err


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--yaml", default=os.path.join(HERE, "test_fix_vapor_reports_failure.yaml"))
    args = ap.parse_args(argv)
    if args.device.startswith("cuda") and not torch.cuda.is_available():
        print("SKIP: cuda requested but not available")
        return 125

    failures = []
    for name, arm in (("control", control_arm), ("clip", clip_arm)):
        msg = arm(args.device, args.yaml)
        print("%-8s %s" % (name, "PASS" if msg is None else "FAIL: " + msg))
        if msg is not None:
            failures.append(name)
    if failures:
        print("FAIL (%s): %s" % (args.device, ", ".join(failures)))
        return 1
    print("PASS (%s): a species clip alone does not redo the step" % args.device)
    return 0


if __name__ == "__main__":
    sys.exit(main())
