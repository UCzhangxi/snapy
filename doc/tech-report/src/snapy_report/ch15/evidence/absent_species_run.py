"""Zero in, zero out in the solver: an absent species under the implicit step.

This is a RUN record, not one of the chapter's checks: it needs a built snapy
in the active Python and is not part of `src/tests`. The committed check
`src/snapy_report/ch15/checks/invariants_zero_check.py` makes the same claim on
a port of the operators and needs nothing but numpy; this one makes it on the
compiled code, with the implicit vertical solve, the moist conserved limiter
and the cross-panel exchange that the port does not carry.

Six gnomonic-equiangular panels of the same shell as `aam_budget_run.py`, with
a four-species moist thermodynamics (dry, NH3, H2S, NH4SH) and the NH3 + H2S
nucleation of `tests/test_condensate_conservation.yaml`. NH3 is PRESENT and is
the control; H2S and its condensate NH4SH are ABSENT, set to exactly zero.
A warm bubble drives vertical motion, so the implicit x1 solve, the positivity
limiter and the species transport all do real work on the present row.

Each cycle it records, over the interiors of all six panels,

  min and count of non-zeros of each absent species row
  min of the present species row  (the limiter's own guarantee)
  the global mass of each species row

The exact answer is that an absent row stays bitwise zero for any number of
steps: `flux_positivity_theta` rectifies the cell's amount instead of flooring
it, so an absent cell's factor is exactly zero and its donor faces are scaled
to zero. A non-zero entry in an absent row is the kintera #147/#151 defect
class appearing in snapy.

  python3 src/snapy_report/ch15/evidence/absent_species_run.py \
      [--device cpu|cuda] [--nx 8] [--cycles 200] [--scheme 9] [--json PATH]

Exits 0 when every absent row is still exactly zero at the end, 1 otherwise.
"""
import argparse
import copy
import datetime
import json
import os
import platform
import sys
import time

import torch

from snapy_report.ch15.evidence.aam_budget_run import (
    DECK, P0, RHO0, build, interior, load_cuda_sidecars,
)

PIN = "ccf40f9565642c32be69f4b9ef0cfa6daff3f201"   # doc/tech-report/code_pin.yml

#: dry plus the two vapours and the condensate of tests/test_condensate_conservation.yaml
SPECIES = [
    {"name": "dry", "composition": {"H": 1.5, "He": 0.15}, "cv_R": 2.5},
    {"name": "NH3", "composition": {"N": 1, "H": 3}, "cv_R": 3.5},
    {"name": "H2S", "composition": {"H": 2, "S": 1}, "cv_R": 3.5},
    {"name": "NH4SH", "composition": {"N": 1, "H": 5, "S": 1}, "cv_R": 9.0, "u0_R": -1.2e4},
]
REACTIONS = [{"equation": "NH3 + H2S <=> NH4SH", "type": "nucleation",
              "rate-constant": {"formula": "nh3_h2s_lewis"}}]

PRESENT = 0            # NH3, row ICY + 0: the control, given a non-zero profile
ABSENT = (1, 2)        # H2S and NH4SH, rows ICY + 1 and ICY + 2: exactly zero
NAMES = {0: "NH3 (present control)", 1: "H2S (absent)", 2: "NH4SH (absent)"}


def deck(nx, scheme):
    cfg = copy.deepcopy(DECK)
    cfg["species"] = copy.deepcopy(SPECIES)
    cfg["reactions"] = copy.deepcopy(REACTIONS)
    # ideal-moist is what gives the hydro array its species rows, and the
    # conserved limiter is the operator under test, so it is ON here
    cfg["dynamics"]["equation-of-state"] = {
        "type": "ideal-moist", "density-floor": 1.0e-20,
        "pressure-floor": 1.0e-20, "limiter": True}
    cfg["integration"]["implicit-scheme"] = scheme
    for key in ("nx1", "nx2", "nx3"):
        cfg["geometry"]["cells"][key] = nx
    return cfg


def initial_state(cfg, mesh, blocks, omega, qpresent, dtemp):
    """The balanced isothermal shell of `aam_budget_run.py` plus a warm bubble
    and a non-zero NH3 profile. The two absent rows are left at exactly zero."""
    import snapy
    from snapy import kICY, kIDN, kIPR, kIV1, kIV3
    from snapy.coord import cs_sph_to_contra_

    g = -cfg["forcing"]["const-gravity"]["grav1"]
    ng = cfg["geometry"]["cells"]["nghost"]
    nx1 = cfg["geometry"]["cells"]["nx1"]
    mesh_vars = []
    for face_id, block in enumerate(blocks):
        coord = block.module("coord")
        r = coord.buffer("x1v")[ng:ng + nx1].cpu()
        dr = coord.buffer("dx1f")[ng:ng + nx1].cpu()
        p = P0 * torch.exp(-(r - r[0]) * RHO0 * g / P0)
        col = torch.zeros(kIPR + 1, 1, 1, nx1, dtype=torch.float64)
        col[kIDN, 0, 0] = p * RHO0 / P0
        col[kIPR, 0, 0] = p
        wb, _, _ = snapy.balance_column(col, dr.contiguous(), g)

        w = dict(block.named_buffers())["hydro.D"].clone().zero_()
        for c in (kIDN, kIPR):
            w[c][..., ng:ng + nx1] = wb[c, 0, 0].to(w)
            w[c][..., :ng] = w[c][..., ng:ng + 1]
            w[c][..., ng + nx1:] = w[c][..., ng + nx1 - 1:ng + nx1]

        lat = coord.buffer("latitude").to(w)
        lon = coord.buffer("longitude").to(w)
        radius = coord.buffer("x1v").unsqueeze(0).unsqueeze(0).to(w)

        # a warm bubble near the equator, so the implicit x1 solve has work to do
        r0 = 0.5 * (cfg["geometry"]["bounds"]["x1min"] + cfg["geometry"]["bounds"]["x1max"])
        bubble = torch.exp(-((radius - r0) / 1.0e5) ** 2
                           - (lat / 0.3) ** 2 - (lon / 0.3) ** 2)
        w[kIPR] = w[kIPR] * (1.0 + dtemp * bubble)

        # NH3 present everywhere, the two absent rows left at exactly zero
        w[kICY + PRESENT] = qpresent * (1.0 + 0.5 * bubble)

        vel = torch.zeros_like(w[kIV1:kIV3 + 1])
        vel[2] = omega * radius * torch.cos(lat)
        alpha = coord.buffer("x2v").unsqueeze(0).unsqueeze(-1).to(w)
        beta = coord.buffer("x3v").unsqueeze(-1).unsqueeze(-1).to(w)
        a = alpha.expand_as(vel[0]).contiguous()
        b = beta.expand_as(vel[0]).contiguous()
        cs_sph_to_contra_(vel, a, b, face_id)
        w[kIV1:kIV3 + 1] = vel
        mesh_vars.append({"hydro_w": w})
    mesh_vars, _ = mesh.initialize(mesh_vars)
    return mesh_vars


def rows(cfg, blocks, mesh_vars):
    """For each species row: min, count of non-zeros and total mass, over the
    interiors of all six panels."""
    from snapy import kICY
    out = {}
    for which in (PRESENT,) + ABSENT:
        lo, nz, mass = float("inf"), 0, 0.0
        for face_id, block in enumerate(blocks):
            sl = interior(block, cfg)
            vol = block.module("coord").cell_volume()[sl]
            row = mesh_vars[face_id]["hydro_u"][kICY + which][sl]
            lo = min(lo, float(row.min()))
            nz += int(torch.count_nonzero(row))
            mass += float((row * vol).sum())
        out[which] = {"min": lo, "nonzero": nz, "mass": mass}
    return out


def run(args):
    sidecars = load_cuda_sidecars() if args.device == "cuda" else []
    if sidecars:
        print(f"# CUDA sidecars loaded: {', '.join(sidecars)}")
    import snapy
    cfg = deck(args.nx, args.scheme)
    mesh, blocks = build(cfg, args.device)
    mesh_vars = initial_state(cfg, mesh, blocks, args.omega, args.qpresent, args.dtemp)
    intg = blocks[0].module("intg")

    print(f"# snapy {snapy.__version__} at pin {PIN[:12]}, torch {torch.__version__}, "
          f"python {platform.python_version()}")
    print(f"# device {args.device}, 6 panels, nx = {args.nx}, {args.cycles} cycles, "
          f"implicit-scheme {args.scheme}, moist limiter on")

    first = rows(cfg, blocks, mesh_vars)
    worst = {w: dict(first[w]) for w in first}
    t0 = time.time()
    cycles_done = 0
    for cycle in range(1, args.cycles + 1):
        mesh.set_cycle(cycle)
        dt = mesh.max_time_step(mesh_vars)
        for stage in range(len(intg.stages)):
            mesh.forward(mesh_vars, dt, stage)
        if mesh.check_redo(mesh_vars) != 0:
            print(f"# step rejected at cycle {cycle}; stopping")
            break
        cycles_done = cycle
        now = rows(cfg, blocks, mesh_vars)
        for which in now:
            worst[which]["min"] = min(worst[which]["min"], now[which]["min"])
            worst[which]["nonzero"] = max(worst[which]["nonzero"], now[which]["nonzero"])
        if cycle == 1:
            after_one = {w: dict(now[w]) for w in now}
    wall = time.time() - t0
    final = rows(cfg, blocks, mesh_vars)

    print(f"# wall {wall:.1f} s, {cycles_done} cycles")
    print(f"{'species row':24s} {'worst min':>14s} {'max non-zeros':>14s} "
          f"{'after 1 cycle':>14s} {'final mass':>14s}")
    for which in (PRESENT,) + ABSENT:
        print(f"{NAMES[which]:24s} {worst[which]['min']:+14.6e} "
              f"{worst[which]['nonzero']:14d} {after_one[which]['min']:+14.6e} "
              f"{final[which]['mass']:14.6e}")

    bad = [NAMES[w] for w in ABSENT
           if worst[w]["min"] != 0.0 or worst[w]["nonzero"] != 0]
    if bad:
        print(f"RED: {', '.join(bad)} acquired a non-zero amount over {cycles_done} "
              f"implicit cycles")
    else:
        print(f"GREEN: both absent rows are bitwise zero in every interior cell of all "
              f"6 panels at every one of {cycles_done} implicit cycles; the present "
              f"control row never goes below {worst[PRESENT]['min']:+.3e}")

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"pin": PIN, "snapy": snapy.__version__, "torch": torch.__version__,
                       "device": args.device, "nx": args.nx, "scheme": args.scheme,
                       "cycles": cycles_done, "wall_s": wall,
                       "worst": {NAMES[w]: worst[w] for w in worst},
                       "final": {NAMES[w]: final[w] for w in final},
                       "when": datetime.datetime.now(datetime.timezone.utc).isoformat()},
                      f, indent=1)
    return 1 if bad else 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
    p.add_argument("--nx", type=int, default=8, help="cells per panel edge and in radius")
    p.add_argument("--cycles", type=int, default=200)
    p.add_argument("--scheme", type=int, default=9, help="integration/implicit-scheme")
    p.add_argument("--omega", type=float, default=2.0e-5, help="solid-body rotation [1/s]")
    p.add_argument("--qpresent", type=float, default=1.0e-3, help="NH3 mass fraction")
    p.add_argument("--dtemp", type=float, default=0.1, help="relative warm-bubble amplitude")
    p.add_argument("--json", default=None)
    return run(p.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
