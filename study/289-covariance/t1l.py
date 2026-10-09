#!/usr/bin/env python3
"""T1L deck in snapy: time-stepped growth rate of the eps-convection mode.
  python t1l.py EPS NZ FORM [--fix COEF] [--nsteps-max N] [--rest NSTEP] [--energy NSTEP]
FORM = cell | face. --fix sets SNAPY_DF_COEF (env-gated x2/x3 covariance term)."""
import argparse, math, os, sys, tempfile, time
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("eps", type=float)
ap.add_argument("nz", type=int)
ap.add_argument("form")
ap.add_argument("--fix", type=float, default=0.0)
ap.add_argument("--rest", type=int, default=0, help="rest-state test: steps")
ap.add_argument("--energy", type=int, default=0, help="energy test: steps")
ap.add_argument("--efolds", type=float, default=5.0)
ap.add_argument("--amp", type=float, default=1e-6)
ap.add_argument("--threads", type=int, default=1)
ap.add_argument("--nodiff", action="store_true")
ap.add_argument("--iso", action="store_true")
ap.add_argument("--save", default="")
args = ap.parse_args()
os.environ["SNAPY_DF_COEF"] = repr(args.fix)

import torch
torch.set_num_threads(args.threads)
import yaml
import snapy
from snapy import MeshBlock, MeshBlockOptions, kIDN, kIPR, kIV1
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exact import deck_mu, growth, operators, K_WAVE
import scipy.linalg as sla

GAMMA, R, G = 1.4, 1.0, 1.0
CV = R / (GAMMA - 1); CP = CV + R
RGAS = 8.31446261815324
eps, nz = args.eps, args.nz
nx = 2 * nz
beta = G / CP + eps * G / R
LX = 2 * math.sqrt(2)
mu = deck_mu(eps)
sig_ex = growth(eps, mu)
TW = (1.0, 1.0) if args.iso else (1.0, 1.0 - beta)
ng = 3


def config():
    base = {
        "geometry": {"type": "cartesian",
                     "bounds": {"x1min": 0.0, "x1max": 1.0, "x2min": 0.0, "x2max": LX,
                                "x3min": 0.0, "x3max": 1.0},
                     "cells": {"nx1": nz, "nx2": nx, "nx3": 1, "nghost": ng}},
        "dynamics": {
            "equation-of-state": {"type": "ideal-gas", "gammad": GAMMA, "weight": RGAS / R,
                                  "limiter": False},
            "reconstruct": {"vertical": {"type": "weno5", "scale": True, "shock": False},
                            "horizontal": {"type": "weno5", "scale": True, "shock": False}},
            "riemann-solver": {"type": "lmars"}},
        "boundary-condition": {"external": {"x1-inner": "reflecting", "x1-outer": "reflecting",
                                            "x2-inner": "periodic", "x2-outer": "periodic",
                                            "x3-inner": "periodic", "x3-outer": "periodic"}},
        "integration": {"type": "rk3", "cfl": 0.4, "implicit-scheme": 0, "nlim": -1, "tlim": 1.e9},
        "forcing": {"const-gravity": {"grav1": -G, "gravity-work": args.form},
                    "diffusion": {"nu_iso": float(mu), "kappa_iso": float(CP * mu), "dynamic": True}},
    }
    if args.nodiff:
        del base["forcing"]["diffusion"]
    return base


def fixed_t_wall(face):
    """reflecting wall; temperature ghost T_g = 2 T_wall - T_mirror."""
    def bc(var, dim, op):
        if var.size(dim) == 1:
            return
        n = var.size(dim)
        lo = 0 if face == 0 else n - ng
        src = ng if face == 0 else n - 2 * ng
        var.narrow(dim, lo, ng).copy_(var.narrow(dim, src, ng).flip(dim))
        t = op.type()
        if t in (snapy.kConserved, snapy.kPrimitive):
            var[4 - dim].narrow(dim - 1, lo, ng).mul_(-1)
            g = var.narrow(dim, lo, ng)  # (nvar, ..., ng) after flip: mirror values
            rho = g[kIDN]
            if t == snapy.kConserved:
                ke = 0.5 * (g[1] ** 2 + g[2] ** 2 + g[3] ** 2) / rho
                p = (GAMMA - 1) * (g[kIPR] - ke)
                Tg = 2 * TW[face] - p / (R * rho)
                g[kIPR].copy_(rho * CV * Tg + ke)
            else:
                Tg = 2 * TW[face] - g[kIPR] / (R * rho)
                g[kIPR].copy_(rho * R * Tg)
    return bc


with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, dir=os.getcwd()) as f:
    yaml.safe_dump(config(), f)
    tmp = f.name
try:
    opts = MeshBlockOptions.from_yaml(tmp)
finally:
    os.unlink(tmp)
opts.set_bfunc(0, 0, -1, fixed_t_wall(0))
opts.set_bfunc(0, 0, 1, fixed_t_wall(1))
block = MeshBlock(opts)
block.to(torch.device("cpu"), torch.float64)

dz = 1.0 / nz
dx = LX / nx
zc = (np.arange(nz) + 0.5) * dz
xc = (np.arange(nx) + 0.5) * dx
T0 = np.ones_like(zc) if args.iso else 1 - beta * zc
p0 = np.exp(-G * zc / R) if args.iso else T0 ** (G / (R * beta))
col = torch.zeros(kIPR + 1, 1, 1, nz, dtype=torch.float64)
col[kIDN, 0, 0] = torch.tensor(p0 / (R * T0))
col[kIPR, 0, 0] = torch.tensor(p0)
wb, err, sweeps = snapy.balance_column(col, torch.full((nz,), dz, dtype=torch.float64), G)
rho_b = wb[kIDN, 0, 0].numpy(); p_b = wb[kIPR, 0, 0].numpy()

# exact eigenmode, interpolated to the cell centres (Chebyshev polynomial)
Ncheb = 64
A, B, zch = operators(eps, mu, Ncheb)
lam, V = sla.eig(A, B)
ok = np.isfinite(lam) & (np.abs(lam) < 1e3) & (np.abs(lam.imag) < 1e-6)
i = np.argmax(np.where(ok, lam.real, -np.inf))
v = V[:, i]
n1 = Ncheb + 1
def interp(f):
    c = np.polynomial.chebyshev.chebfit(1 - 2 * zch, f, Ncheb)
    return np.polynomial.chebyshev.chebval(1 - 2 * zc, c)
rho_h, u_h, w_h, T_h = (interp(v[j * n1:(j + 1) * n1]) for j in range(4))
sc = 1.0 / w_h[np.argmax(np.abs(w_h))]
rho_h, u_h, w_h, T_h = rho_h * sc, u_h * sc, w_h * sc, T_h * sc
cs = math.sqrt(GAMMA)
A0 = args.amp * cs
ph = np.exp(1j * K_WAVE * xc)[:, None]
re = lambda f: np.real(f[None, :] * ph)

w = block.buffer("hydro.D").clone().zero_()  # (nvar, nc3, nc2, nc1)
sl = (Ellipsis, slice(ng, ng + nx), slice(ng, ng + nz))
if args.rest:
    drho = np.zeros((nx, nz)); du = drho; dw = drho; dT = drho
else:
    drho = A0 * re(rho_h); du = A0 * re(u_h); dw = A0 * re(w_h); dT = A0 * re(T_h)
rho = rho_b[None, :] + drho
T = (p_b / (R * rho_b))[None, :] + dT
w[kIDN][sl] = torch.tensor(rho)[None]
w[kIPR][sl] = torch.tensor(rho * R * T)[None]
w[kIV1][sl] = torch.tensor(dw)[None]
w[2][sl] = torch.tensor(du)[None]
block_vars, _ = block.initialize({"hydro_w": w})

dt = 0.4 * dz / math.sqrt(GAMMA * p_b.max() / rho_b[np.argmax(p_b)])
dt = 0.4 * dz / max(math.sqrt(GAMMA * p_b[j] / rho_b[j]) for j in range(nz))
nstage = len(block.module("intg").stages)
zz = torch.tensor(zc)
ex = torch.tensor(np.exp(-1j * K_WAVE * xc))
wproj = torch.tensor(np.conj(w_h))


def amp():
    u = block_vars["hydro_u"][sl][:, 0]  # (nx, nz)
    wv = (u[kIV1] / u[kIDN]).numpy()
    a = (np.exp(-1j * K_WAVE * xc)[:, None] * wv).sum(0)  # (nz,)
    return abs((a * np.conj(w_h)).sum())


def epe():
    u = block_vars["hydro_u"][sl][:, 0].double()
    return ((u[kIPR] + u[kIDN] * G * zz[None, :]).sum() * dz * dx).item()


t0 = time.time()
if args.rest or args.energy:
    nst = args.rest or args.energy
    e0 = epe(); dmax = 0.0
    for n in range(nst):
        for s in range(nstage):
            block.forward(block_vars, dt, s)
        e = epe(); dmax = max(dmax, abs(e - e0) / abs(e0))
    u = block_vars["hydro_u"][sl][:, 0]
    if args.save:
        np.save(args.save, u.numpy())
    vmax = (u[1:3].abs() / u[kIDN]).max().item()
    print(f"RESULT eps {eps} nz {nz} {args.form} fix {args.fix} steps {nst}: max|v| {vmax:.3e} "
          f"max|dE+PE|/E {dmax:.3e} ({time.time()-t0:.0f}s)", flush=True)
    sys.exit(0)

a0 = amp()
la0 = math.log(a0)
ts, las = [], []
t = 0.0
nmax = int(((args.efolds + 1.5) / max(sig_ex * 0.5, 1e-9)) / dt) + 1
n = 0
while n < nmax:
    for s in range(nstage):
        block.forward(block_vars, dt, s)
    t += dt; n += 1
    if n % 10 == 0:
        la = math.log(amp())
        ts.append(t); las.append(la)
        if la - la0 > args.efolds + 0.05:
            break
ts = np.array(ts); las = np.array(las)
m = (las - la0 >= 1.0) & (las - la0 <= args.efolds)
if m.sum() < 5:
    # did not grow enough; report the slope over the last half
    m = ts > ts[-1] / 2
    note = "NOT-GROWN"
else:
    note = ""
slope = np.polyfit(ts[m], las[m], 1)[0]
print(f"RESULT eps {eps} nz {nz} {args.form} fix {args.fix}: sigma {slope:.8f} exact {sig_ex:.8f} "
      f"rel {slope/sig_ex-1:+.5f} {note} steps {n} t {t:.1f} ({time.time()-t0:.0f}s)", flush=True)
