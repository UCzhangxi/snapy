#!/usr/bin/env python3
"""T4 S-field statistics from the SNAPY_GW_DUMP files of t4_s_patch.py (snapy 117e449 + instrument).

Per call (one RK stage): items [S_full, W, rho, v1, dt, sum(E vol), sum(rho Phi vol), vol, S_applied]
(see t4_s_patch.py).  S_full = face-minus-cell gravity work / dt (both modes); W = g rho v1 (cell work);
B = g rho' v1 with rho' = rho - horizontal mean (the buoyancy-flux part of W).

Instrument oracle (face mode, exact to round-off): with G = sum((S_applied + W) vol), the
SSP-RK3 Shu-Osher PE bookkeeping PE1 = PE0 - dt G0, PE2 = 3/4 PE0 + 1/4 (PE1 - dt G1),
PE0' = 1/3 PE0 + 2/3 (PE2 - dt G2) holds per step (implicit scheme 9 changes nothing here: the
implicit block moves no mass across x1 faces beyond the flux it is handed -- reported, not asserted).
Statistics, interior (z cells nw..nz-nw) vs wall (first/last nw cells): rms(S)/rms(W), rms(S)/rms(B),
corr(S, v1), corr(S, B), sum(S vol)/sum(W vol), sum(S vol)/sum(B vol).

  analyze_s_t4.py DUMPDIR [--nwall 2] [--skip 0] [--json out.json]
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import torch

ap = argparse.ArgumentParser()
ap.add_argument("dump")
ap.add_argument("--nwall", type=int, default=2)
ap.add_argument("--skip", type=int, default=0)
ap.add_argument("--json", default="")
a = ap.parse_args()

files = sorted(glob.glob(os.path.join(a.dump, "gw_*.pt")), key=lambda p: int(p.split("_")[-1][:-3]))
if len(files) < 6:
    sys.exit(f"only {len(files)} dump files")
keys = ["S", "W", "rho", "v", "dt", "E", "PE", "vol", "Sa"]
rec = []
for p in files:
    it = [x.double().numpy() for x in torch.load(p, weights_only=False)]
    r = dict(zip(keys, it))
    nz = r["S"].shape[-1]
    r["vol"] = np.broadcast_to(r["vol"], r["S"].shape)
    for k in ("S", "W", "rho", "v", "Sa", "vol"):
        r[k] = r[k].reshape(-1, nz)
    r["dt"], r["E"], r["PE"] = float(r["dt"].reshape(-1)[0]), float(r["E"]), float(r["PE"])
    rec.append(r)
n = len(rec)
out = {"dump": os.path.abspath(a.dump), "ncalls": n, "shape_x2_x1": list(rec[0]["S"].shape), "nwall": a.nwall}

G = np.array([((r["Sa"] + r["W"]) * r["vol"]).sum() for r in rec])
PE = np.array([r["PE"] for r in rec])
DT = np.array([r["dt"] for r in rec])
res = []
for k in range(0, n - 3, 3):
    if not (DT[k] == DT[k + 1] == DT[k + 2]):
        continue
    p0, p1, p2, p3 = PE[k:k + 4]
    d = DT[k]
    res += [p1 - (p0 - d * G[k]), p2 - (0.75 * p0 + 0.25 * (p1 - d * G[k + 1])),
            p3 - (p0 / 3 + 2.0 / 3.0 * (p2 - d * G[k + 2]))]
out["O1_rel_PE"] = float(np.abs(res).max() / np.abs(PE).max()) if res else None
out["S_applied_eq_S_full"] = float(max(np.abs(r["Sa"] - r["S"]).max() for r in rec) /
                                   max(np.abs(r["S"]).max() for r in rec))

use = rec[a.skip:]
nz = rec[0]["S"].shape[-1]
nw = a.nwall


def stats(skey, sel):
    st = lambda k: np.stack([r[k][:, sel] for r in use])
    S, W, rho, v, vol = st(skey), st("W"), st("rho"), st("v"), st("vol")
    B = W * (rho - rho.mean(axis=1, keepdims=True)) / rho  # axis 1 = x2: horizontal mean per level
    rms = lambda x: float(np.sqrt((x ** 2).mean()))
    c = lambda x, y: float(np.corrcoef(x.ravel(), y.ravel())[0, 1])
    return dict(rSW=rms(S) / rms(W), rSB=rms(S) / rms(B), cSv=c(S, v), cSB=c(S, B),
                gSW=float((S * vol).sum() / (W * vol).sum()), gSB=float((S * vol).sum() / (B * vol).sum()),
                rmsS=rms(S), rmsW=rms(W), rmsB=rms(B))


parts = {"all": slice(0, nz), "interior": slice(nw, nz - nw), "wall": np.r_[0:nw, nz - nw:nz]}
out["stats"] = {s: {p: stats(s, sel) for p, sel in parts.items()} for s in ("S", "Sa")}
print(f"{a.dump}: {n} calls, (x2, x1) = {rec[0]['S'].shape}, O1 rel {out['O1_rel_PE']}, "
      f"max|S_applied - S_full|/max|S| = {out['S_applied_eq_S_full']:.3e}")
print(f"{'S':3s} {'part':9s} {'rmsS/rmsW':>10s} {'rmsS/rmsB':>10s} {'corr(S,w)':>10s} {'corr(S,B)':>10s} "
      f"{'sumS/sumW':>10s} {'sumS/sumB':>10s}")
for s in ("S", "Sa"):
    for p in parts:
        t = out["stats"][s][p]
        print(f"{s:3s} {p:9s} {t['rSW']:10.3e} {t['rSB']:10.3e} {t['cSv']:10.3f} {t['cSB']:10.3f} "
              f"{t['gSW']:10.3e} {t['gSB']:10.3e}")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
