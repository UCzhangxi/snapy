#!/usr/bin/env python3
"""check_redo must reject a step that floored a cell and restore hydro_u AND hydro_w.

The floor is planted in hydro_u only: a detector reading the (one stage stale) hydro_w
would pass it.

  python test_check_redo_floor.py [--device cuda]
"""
import argparse
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--yaml", default=os.path.join(HERE, "test_fix_vapor_reports_failure.yaml"))
    args = ap.parse_args()
    if args.device.startswith("cuda") and not torch.cuda.is_available():
        print("SKIP: cuda requested but not available")
        return 0

    from snapy import MeshBlock, MeshBlockOptions, kICY, kIDN, kIPR

    block = MeshBlock(MeshBlockOptions.from_yaml(args.yaml))
    block.to(torch.device(args.device))
    eos = next(m for _, m in block.named_modules() if type(m).__name__ == "IdealMoist")
    density_floor = eos.options.density_floor()

    w = dict(block.named_buffers())["hydro.D"].clone().zero_()
    w[kIDN] = 1.0
    w[kIPR] = 1.0e5
    w[kICY] = 1.0e-3
    block_vars, _ = block.initialize({"hydro_w": w})

    u0 = block_vars["hydro_u"].clone()
    dt = block.max_time_step(block_vars)
    for stage in range(len(block.intg.stages)):
        block.forward(block_vars, dt, stage)
    if block.check_redo(block_vars) != 0:
        print("FAIL (%s): healthy step was rejected" % args.device)
        return 1

    k, j, i = u0.size(1) // 2, u0.size(2) // 2, u0.size(3) // 2
    block_vars["hydro_u"][kIDN, k, j, i] = density_floor  # at the floor, not below it
    block_vars["hydro_u"][kICY:, k, j, i] = 0.0
    w_stale_min = block_vars["hydro_w"][kIDN].min().item()

    err = block.check_redo(block_vars)
    if err != 1:
        print("FAIL (%s): floored cell not rejected (err=%d; stale hydro_w min rho=%g)"
              % (args.device, err, w_stale_min))
        return 1
    if not torch.equal(block_vars["hydro_u"], u0):
        print("FAIL (%s): hydro_u not restored to the pre-step state" % args.device)
        return 1
    w_expect = eos.compute("U->W", [u0.clone()])
    if not torch.equal(block_vars["hydro_w"], w_expect):
        print("FAIL (%s): hydro_w not recomputed from the restored hydro_u" % args.device)
        return 1
    if block.check_redo(block_vars) != 0:
        print("FAIL (%s): restored state was rejected" % args.device)
        return 1
    print("PASS (%s): floored step rejected, hydro_u and hydro_w restored (floor %g)"
          % (args.device, density_floor))
    return 0


if __name__ == "__main__":
    sys.exit(main())
