#!/usr/bin/env python3
"""TEST 4 driver: flux-driven low-Mach convection in snapy (card from make_card_t4.py).

The loop and the hashed IC follow our earlier internal convection benchmark deck; the
problem differs: the initial state is the NEUTRAL (adiabatic) polytrope and the box is driven
by snapy's own bot-heat / top-cool fixed fluxes, F = eps rho_t c_t^3. The card carries the
primaries; this driver re-derives F, Lz, g and aborts if the card disagrees.

    python run_t4.py -c card.yaml --output-dir DIR [-r RESTART]
"""
import argparse
import os
import sys

import numpy as np
import torch
import yaml
from snapy import MeshBlock, MeshBlockOptions, kIDN, kIPR

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from make_card_t4 import derive  # noqa: E402

_M64 = (1 << 64) - 1


def hash_uniform(a):  # splitmix64 of the global cell index (decomposition-independent noise)
    a = (a + 0x9E3779B97F4A7C15) & _M64
    a = ((a ^ (a >> 30)) * 0xBF58476D1CE4E5B9) & _M64
    a = ((a ^ (a >> 27)) * 0x94D049BB133111EB) & _M64
    a = a ^ (a >> 31)
    return (a >> 11) / float(1 << 53)


def verify(config, d, tol=1e-10):
    b = config["geometry"]["bounds"]
    f = config["forcing"]
    nz = int(config["geometry"]["cells"]["nx1"])
    checks = [("x1max", float(b["x1max"]), d["Lz"]), ("x2max", float(b["x2max"]), d["Lx"]),
              ("grav1", float(f["const-gravity"]["grav1"]), -d["g"]),
              ("bot-heat.flux", float(f["bot-heat"]["flux"]), d["F"]),
              ("top-cool.flux", float(f["top-cool"]["flux"]), -d["F"]),
              ("bot-heat.depth", float(f["bot-heat"]["depth"]), d["layer"] * nz),
              ("top-cool.depth", float(f["top-cool"]["depth"]), d["layer"] * nz),
              ("diffusion.nu_iso", float(f["diffusion"]["nu_iso"]), d["nu"]),
              ("diffusion.kappa_iso", float(f["diffusion"]["kappa_iso"]), 0.0)]
    for name, got, want in checks:
        if abs(got - want) > tol * max(1.0, abs(want)):
            raise SystemExit(f"[t4] card {name} = {got!r} but derived {want!r}: regenerate it")
    ext = config["boundary-condition"]["external"]
    if ext["x1-inner"] != "reflecting" or ext["x1-outer"] != "reflecting":
        raise SystemExit("[t4] x1 walls must be reflecting (sealed, insulating)")


def polytrope_ic(block, eos, d, noise, seed, nx1_global):
    coord = block.module("coord")
    x1v, x2v, x3v = coord.buffer("x1v"), coord.buffer("x2v"), coord.buffer("x3v")
    X3, X2, X1 = torch.meshgrid(x3v, x2v, x1v, indexing="ij")
    T0 = 1.0 + d["Lz"] - X1
    rho0 = torch.pow(T0, d["m"])
    dx1 = float(x1v[1] - x1v[0])
    dx2 = float(x2v[1] - x2v[0])
    gi = torch.round((X1 - 0.5 * dx1) / dx1).to(torch.int64)
    gj = torch.round((X2 - 0.5 * dx2) / dx2).to(torch.int64)
    key = (seed * 1000003 + gj.cpu().numpy().astype(object) * int(nx1_global)
           + gi.cpu().numpy().astype(object))
    r = np.vectorize(hash_uniform, otypes=[np.float64])(key & _M64)
    r = torch.as_tensor(r, dtype=X1.dtype, device=X1.device)
    T = T0 * (1.0 + noise * (r - 0.5))
    w = torch.zeros((eos.nvar(),) + tuple(X1.shape), dtype=X1.dtype, device=X1.device)
    w[kIDN] = rho0
    w[kIPR] = rho0 * d["Rd"] * T
    return w


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-c", "--config", required=True)
    p.add_argument("--output-dir", default=".")
    p.add_argument("-r", "--restart", default="")
    a = p.parse_args()
    with open(a.config) as f:
        config = yaml.safe_load(f)
    pr = config["problem"]
    d = derive(float(pr["eps"]), float(pr["n_rho"]), float(pr["gamma"]), float(pr["aspect"]),
               float(pr["layer"]), float(pr["Re"]))
    verify(config, d)
    nz = int(config["geometry"]["cells"]["nx1"])
    gw = config["forcing"]["const-gravity"].get("gravity-work", "cell")
    print(f"[t4] eps={d['eps']:g} F={d['F']!r} Lz={d['Lz']!r} t_c={d['t_c']!r} "
          f"nz={nz} nx={config['geometry']['cells']['nx2']} "
          f"scheme={config['integration']['implicit-scheme']} gw={gw} seed={pr['seed']}",
          flush=True)

    options = MeshBlockOptions.from_yaml(a.config)
    options.output_dir(a.output_dir)
    block = MeshBlock(options)
    device = torch.device(options.device_str())
    block.to(device)
    eos = block.module("hydro.eos")
    if a.restart:
        bv, t = block.initialize_from_restart(a.restart)
        block.to(device)
    else:
        bv, t = block.initialize({"hydro_w": polytrope_ic(block, eos, d, float(pr["noise"]),
                                                          int(pr["seed"]), nz)})
    os.makedirs(a.output_dir, exist_ok=True)
    with open(os.path.join(a.output_dir, "IDENTITY.yaml"), "w") as f:
        yaml.safe_dump({"problem": "T4 flux-driven convection", "derived": d,
                        "gravity_work": gw, "card": os.path.abspath(a.config),
                        "restart": a.restart or None,
                        "snapy": __import__("snapy").__version__}, f, sort_keys=False)
    if not a.restart:
        block.make_outputs(bv, t)
    while not block.intg.stop(block.inc_cycle(), t):
        dt = block.max_time_step(bv)
        block.print_cycle_info(bv, t, dt)
        for stage in range(len(block.intg.stages)):
            block.forward(bv, dt, stage)
        err = block.check_redo(bv)
        if err > 0:
            continue
        if err < 0:
            break
        t += dt
        block.make_outputs(bv, t)
    block.finalize(bv, t)


if __name__ == "__main__":
    main()
