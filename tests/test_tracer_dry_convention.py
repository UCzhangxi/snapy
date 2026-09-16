#!/usr/bin/env python3
"""Passive tracers are per DRY air: scalar_s = hydro_u[IDN] * r, transported by the dry mass
flux. A tracer that starts uniform must therefore stay uniform (to round-off) under every
operator that moves or converts dry air. Three arms on a warm unsaturated moist column:

  init     MeshBlock.initialize() builds scalar_s from the DRY density, not the total.
  implicit the vertical implicit correction moves tracers with the dry face transfer, not
           the total one (it over-moved them by 1/(1 - sum y)).
  relax    relax-bot-comp converts dry air to vapour in the bottom cell; the tracer riding
           that dry air goes with it (r was left to drift).

Each arm also checks that its operator actually did something big enough that the old
behaviour would have been visible at >= 1000x the tolerance, so a pass is never vacuous.

  python test_tracer_dry_convention.py [--device cuda] [--yaml PATH]
"""
import argparse
import math
import os
import sys
import tempfile
from pathlib import Path

import torch
import yaml

R0 = 1.0e-3
TOL = 1.0e-12


def make_block(config, device):
    from snapy import MeshBlock, MeshBlockOptions

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, dir=os.getcwd()) as f:
        yaml.safe_dump(config, f)
        tmp = f.name
    try:
        block = MeshBlock(MeshBlockOptions.from_yaml(tmp))
    finally:
        os.unlink(tmp)
    block.to(torch.device(device))
    return block


def initial_state(block, config, moving):
    from snapy import kICY, kIDN, kIPR, kIV1

    w = dict(block.named_buffers())["hydro.D"].clone().zero_()
    ng = config["geometry"]["cells"]["nghost"]
    nx1 = config["geometry"]["cells"]["nx1"]
    x1max = float(config["geometry"]["bounds"]["x1max"])
    dz = x1max / nx1
    z = (torch.arange(w.size(-1), dtype=torch.float64, device=w.device) - ng + 0.5) * dz
    T, R = 320.0, 3900.0
    p = 1.0e5 * torch.exp(-z * 10.0 / (R * T))
    w[kIPR] = p.view(1, 1, -1)
    w[kIDN] = (p / (R * T)).view(1, 1, -1)
    w[kICY] = 0.02  # vapour mass fraction of the total; cloud stays 0
    if moving:
        w[kIV1] = (5.0 * torch.sin(math.pi * z / x1max)).view(1, 1, -1)
    r = torch.full((1,) + tuple(w.shape[1:]), R0, dtype=w.dtype, device=w.device)
    return w, r


def interior(config):
    ng = config["geometry"]["cells"]["nghost"]
    return (slice(None), slice(None), slice(ng, -ng), slice(ng, -ng))


def run(config, device, moving, nlim):
    from snapy import kIDN

    block = make_block(config, device)
    w, r = initial_state(block, config, moving)
    v, _ = block.initialize({"hydro_w": w, "scalar_r": r})
    I = interior(config)
    bufs = dict(block.named_buffers())
    mass_corr = next((b for k, b in bufs.items() if k.endswith("mass_corr")), None)
    # largest relative over-transport the old implicit tracer update (total M instead of
    # the dry transfer) would have applied in one stage, summed over stages
    implicit_bug_scale = 0.0
    # departures are measured from the post-initialisation r, so each arm tests only its
    # own operator (not the initialisation, which the init arm covers)
    r_init = v["scalar_s"][I] / v["hydro_u"][kIDN][I[1:]]
    for _ in range(nlim):
        dt = block.max_time_step(v)
        for stage in range(len(block.intg.stages)):
            block.forward(v, dt, stage)
            if mass_corr is not None and mass_corr.numel() > 0:
                from snapy import kIV1
                g = config["geometry"]
                vol = (float(g["bounds"]["x1max"]) / g["cells"]["nx1"]) * (
                    float(g["bounds"]["x2max"]) / g["cells"]["nx2"]) * (
                    float(g["bounds"]["x3max"]) / g["cells"]["nx3"])
                excess = (mass_corr[kIV1] - mass_corr[kIV1 + 1]).abs()[I[1:]]
                implicit_bug_scale += float((excess / (v["hydro_u"][kIDN][I[1:]] * vol)).max())
    dev = float((v["scalar_s"][I] / (v["hydro_u"][kIDN][I[1:]] * r_init) - 1.0).abs().max())
    return v, dev, implicit_bug_scale


def main():
    from snapy import kIDN

    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
    parser.add_argument(
        "--yaml", default=str(Path(__file__).resolve().parent / "test_tracer_dry_convention.yaml"))
    args = parser.parse_args()
    with open(args.yaml) as f:
        base = yaml.safe_load(f)
    failures = []

    # ---- init: scalar_s from dry density ----
    cfg = yaml.safe_load(yaml.safe_dump(base))
    block = make_block(cfg, args.device)
    w, r = initial_state(block, cfg, moving=False)
    v, _ = block.initialize({"hydro_w": w, "scalar_r": r})
    I = interior(cfg)
    s = v["scalar_s"][I]
    dry_err = float((s / (v["hydro_u"][kIDN][I[1:]] * R0) - 1).abs().max())
    tot_err = float((s / (v["hydro_w"][kIDN][I[1:]] * R0) - 1).abs().max())
    loading = float((v["hydro_w"][kIDN][I[1:]] / v["hydro_u"][kIDN][I[1:]] - 1).abs().max())
    print(f"init    : |s/(rho_dry r)-1|={dry_err:.3e}  |s/(rho_tot r)-1|={tot_err:.3e}  "
          f"rho_tot/rho_dry-1={loading:.3e}")
    if not dry_err < TOL:
        failures.append(f"init: scalar_s is not rho_dry*r (err {dry_err:.3e})")
    if not loading > 1000 * TOL:
        failures.append(f"init: dry and total density indistinguishable ({loading:.3e}); test cannot bite")

    # ---- implicit: tracer moved with the dry face transfer ----
    cfg = yaml.safe_load(yaml.safe_dump(base))
    cfg["integration"]["implicit-scheme"] = 1
    _, dev, bug_scale = run(cfg, args.device, moving=True, nlim=cfg["integration"]["nlim"])
    print(f"implicit: max|r/r_init-1|={dev:.3e}  old-code over-transport scale={bug_scale:.3e}")
    if not dev < TOL:
        failures.append(f"implicit: uniform tracer departed by {dev:.3e}")
    if not bug_scale > 1000 * TOL:
        failures.append(f"implicit: the solve moved too little mass ({bug_scale:.3e}); test cannot bite")

    # ---- relax: relax-bot-comp carries the tracer with the dry air it converts ----
    cfg = yaml.safe_load(yaml.safe_dump(base))
    cfg["integration"]["implicit-scheme"] = 0
    nlim = cfg["integration"]["nlim"]
    v0, _, _ = run(cfg, args.device, moving=False, nlim=nlim)
    cfg["forcing"]["relax-bot-comp"] = {"tau": 10.0, "species": ["vapor"], "xfrac": [0.2]}
    v1, dev, _ = run(cfg, args.device, moving=False, nlim=nlim)
    I = interior(cfg)
    forced = float(((v1["hydro_u"][kIDN] - v0["hydro_u"][kIDN])[I[1:]] / v0["hydro_u"][kIDN][I[1:]]).abs().max())
    print(f"relax   : max|r/r_init-1|={dev:.3e}  dry-density change due to the forcing={forced:.3e}")
    if not dev < TOL:
        failures.append(f"relax: uniform tracer departed by {dev:.3e}")
    if not forced > 1000 * TOL:
        failures.append(f"relax: forcing converted too little dry air ({forced:.3e}); test cannot bite")

    if failures:
        for msg in failures:
            print("FAIL:", msg)
        sys.exit(1)
    print("### tracer dry-convention test passed. ###")


if __name__ == "__main__":
    main()
