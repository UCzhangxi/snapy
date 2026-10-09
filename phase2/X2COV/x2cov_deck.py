#!/usr/bin/env python3
"""x2cov deck: the T1L box with a selectable implicit scheme and device, for the SNAPY_X2COV term.

The term (env SNAPY_X2COV=<factor>, unset = off) adds the x1 covariance
    dF = gamma/(gamma-1) dz^2/12 p d(ln p/rho)/dz du/dz
to the energy flux of every x2/x3 face. This driver needs no input file.

    [SNAPY_X2COV=1] [DEVICE=cuda] python x2cov_deck.py onestep --nz 32 --scheme 9 --out DIR
    [SNAPY_X2COV=1] [DEVICE=cuda] python x2cov_deck.py run --nz 32 --scheme 9 --eps 0.02 --nsteps 2000 --out DIR
    python x2cov_deck.py compare DIR_A DIR_B

Box: 0 <= z <= 1, 0 <= x <= 2 sqrt(2) (nx = 2 nz), R = g = 1, gamma = 1.4 (Cp = 3.5),
T0 = 1 - beta z with beta = 1/Cp + eps, p0 = T0^(1/beta), discretely balanced by snapy.balance_column.
Reflecting walls in z, periodic in x, inviscid, WENO5 + LMARS + RK3, gravity work as --gw.
Seed: the anelastic roll rho0 u = -dpsi/dz, rho0 w = dpsi/dx, psi ~ sin(pi z) sin(k x), max|w| = --amp.

onestep (oracle for the term itself; use eps = 0): one RK3 step of a seeded and an unseeded box.
  S = d s/dt (seeded - unseeded), s = Cv ln p - Cp ln rho. The physical tendency is Cp eps w / T0, so
  eps_eff = Re sum rho0 (T0 S)^ conj(w^) / (Cp sum rho0 |w^|^2)   (^ = x-Fourier coefficient at k).
  pred = the same projection of the term evaluated here in python on the seeded state (factor 1).
  With the term on, eps_eff(on) - eps_eff(off) must equal factor * pred, for any implicit scheme:
  the term is an explicit x2/x3 flux, and at eps = 0 the x1 acoustic adjustment leaves s unchanged
  to linear order.
run: nsteps steps; diag.json has max|w|, E+PE every 10 steps; W_final.pt is the final primitive state.
compare: max |W_A - W_B| per variable, relative to the variable's range.
"""
import argparse, json, math, os, sys
import torch
import snapy
from snapy import MeshBlock, MeshBlockOptions, kIDN, kIPR

GAMMA, CP, CV, NG = 1.4, 3.5, 2.5, 3
IV1, IV2 = 1, 2          # vertical (x1) and horizontal (x2) velocity slots
LX = 2.0 * math.sqrt(2.0)


def card(nz, scheme, gw, cfl):
    return f"""geometry:
  type: cartesian
  bounds: {{x1min: 0., x1max: 1., x2min: 0., x2max: {LX!r}, x3min: 0., x3max: 1.}}
  cells: {{nx1: {nz}, nx2: {2 * nz}, nx3: 1, nghost: {NG}}}
distribute: {{layout: slab, nb1: 1, nb2: 1, nb3: 1, verbose: false}}
dynamics:
  equation-of-state:
    type: ideal-gas
    gammad: {GAMMA!r}
    weight: 8.31446
    density-floor: 1.e-12
    pressure-floor: 1.e-12
    temperature-floor: 1.e-12
    limiter: true
  reconstruct:
    vertical:   {{type: weno5, scale: true, shock: false}}
    horizontal: {{type: weno5, scale: true, shock: false}}
  riemann-solver: {{type: lmars}}
boundary-condition:
  external:
    x1-inner: reflecting
    x1-outer: reflecting
    x2-inner: periodic
    x2-outer: periodic
    x3-inner: periodic
    x3-outer: periodic
integration:
  type: rk3
  cfl: {cfl}
  implicit-scheme: {scheme}
  nlim: -1
  tlim: 1.e9
  ncycle_out: 100000000
forcing:
  const-gravity: {{grav1: -1.0, gravity-work: {gw}}}
"""


def build(a, seed, beta):
    os.makedirs(a.out, exist_ok=True)
    cardf = os.path.join(a.out, "card.yaml")
    open(cardf, "w").write(card(a.nz, a.scheme, a.gw, a.cfl))
    options = MeshBlockOptions.from_yaml(cardf)
    options.output_dir(a.out)
    block = MeshBlock(options)
    device = torch.device(options.device_str() or "cpu")
    block.to(torch.device("cpu"))
    coord, eos = block.module("coord"), block.module("hydro.eos")
    x1v, x2v, x3v = coord.buffer("x1v"), coord.buffer("x2v"), coord.buffer("x3v")
    X3, X2, X1 = torch.meshgrid(x3v, x2v, x1v, indexing="ij")
    T0 = 1.0 - beta * X1
    p0 = torch.pow(T0, 1.0 / beta)
    w = torch.zeros((eos.nvar(),) + tuple(X1.shape), dtype=X1.dtype)
    w[kIDN], w[kIPR] = p0 / T0, p0
    I = slice(NG, -NG)
    dx1f = coord.buffer("dx1f")[I].contiguous()
    wb, res, _ = snapy.balance_column(w[:, :, I, I].contiguous(), dx1f, 1.0, True, 3e-14, 400)
    w[:, :, I, I] = wb
    if seed:
        k = 2.0 * math.pi / LX
        z, x, rho = X1[0, I, I], X2[0, I, I], w[kIDN, 0, I, I]
        uu = -math.pi * torch.cos(math.pi * z) * torch.sin(k * x) / rho
        ww = k * torch.sin(math.pi * z) * torch.cos(k * x) / rho
        A = a.amp / float(ww.abs().max())
        w[IV1, 0, I, I], w[IV2, 0, I, I] = A * ww, A * uu
    block.to(device)
    bv, t = block.initialize({"hydro_w": w.to(device)})
    return block, bv, eos, coord, res, device


def advance(block, bv, dt):
    block.inc_cycle()
    for st in range(len(block.intg.stages)):
        block.forward(bv, dt, st)
    assert block.check_redo(bv) == 0


def prim(bv, eos):
    return eos.compute("U->W", [bv["hydro_u"]]).cpu()   # end-of-step state (hydro_w = last-stage input)


def onestep(a):
    beta = 1.0 / CP + a.eps
    b0, bv0, eos, coord, res0, dev = build(a, False, beta)
    b1, bv1, _, _, res1, _ = build(a, True, beta)
    dt = a.dtfac * float(b1.max_time_step(bv1))
    W0i, W1i = prim(bv0, eos).clone(), prim(bv1, eos).clone()
    I = slice(NG, -NG)

    def s_of(W):
        return CV * torch.log(W[kIPR, 0, I, I]) - CP * torch.log(W[kIDN, 0, I, I])

    s0a, s1a = s_of(W0i), s_of(W1i)
    advance(b0, bv0, dt)
    advance(b1, bv1, dt)
    S = ((s_of(prim(bv1, eos)) - s1a) - (s_of(prim(bv0, eos)) - s0a)) / dt

    k = 2.0 * math.pi / LX
    x = coord.buffer("x2v").cpu()[I]
    nx = x.shape[0]
    emk = torch.exp(-1j * k * x.to(torch.complex128))[:, None]
    rho_b = W0i[kIDN, 0, NG, I]
    T0 = W0i[kIPR, 0, NG, I] / W0i[kIDN, 0, NG, I]
    what = (2.0 / nx) * (W1i[IV1, 0, I, I] * emk).sum(0)

    def eps_of(F):
        Fh = (2.0 / nx) * (F * emk).sum(0)
        num = rho_b * (T0 * Fh * what.conj()).real
        return float(num.sum() / (CP * rho_b * what.abs() ** 2).sum())

    # the term, factor 1, on the seeded initial state (ghosts included), as a flux divergence
    Wg = W1i[:, 0]
    x1v, dx1f = coord.buffer("x1v").cpu(), coord.buffer("dx1f").cpu()
    dx2 = float(coord.buffer("dx2f").cpu()[NG])
    lnT, u, h = torch.log(Wg[kIPR] / Wg[kIDN]), Wg[IV2], x1v[2:] - x1v[:-2]
    cov = torch.zeros_like(lnT)
    cov[:, 1:-1] = GAMMA / (GAMMA - 1) * dx1f[1:-1] ** 2 / 12 * Wg[kIPR][:, 1:-1] * \
        (lnT[:, 2:] - lnT[:, :-2]) / h * (u[:, 2:] - u[:, :-2]) / h
    F = torch.zeros_like(cov)
    F[1:] = 0.5 * (cov[:-1] + cov[1:])          # x2 face j sits between cells j-1 and j
    dE = (-(F[NG + 1:-NG + 1] - F[NG:-NG]) / dx2)[:, I]
    Spred = (GAMMA - 1) * CV * dE / Wg[kIPR][I, I]   # ds = Cv dp / p, dp = (gamma - 1) dE

    out = dict(mode="onestep", nz=a.nz, eps=a.eps, scheme=a.scheme, gw=a.gw, device=str(dev),
               x2cov=os.environ.get("SNAPY_X2COV", "unset"), dt=dt, amp=a.amp, bal_res=[res0, res1],
               eps_eff_nz2=eps_of(S) * a.nz ** 2, pred_nz2=eps_of(Spred) * a.nz ** 2,
               snapy=snapy.__version__)
    return out


def run(a):
    beta = 1.0 / CP + a.eps
    b, bv, eos, coord, res, dev = build(a, True, beta)
    I = slice(NG, -NG)
    x1v = coord.buffer("x1v").to(dev)

    def budget():
        U = bv["hydro_u"][:, 0, I, I]
        return float((U[kIPR] + U[kIDN] * x1v[I]).sum()), float(bv["hydro_w"][IV1, 0, I, I].abs().max())

    e0, _ = budget()
    hist, dts = [], []
    for n in range(1, a.nsteps + 1):
        dt = float(b.max_time_step(bv))
        advance(b, bv, dt)
        dts.append(dt)
        if n % 10 == 0 or n == a.nsteps:
            e, wmax = budget()
            hist.append([n, sum(dts), (e - e0) / abs(e0), wmax])
            if not math.isfinite(e):
                break
    W = prim(bv, eos)
    torch.save(W, os.path.join(a.out, "W_final.pt"))
    fin = bool(torch.isfinite(W).all())
    return dict(mode="run", nz=a.nz, eps=a.eps, scheme=a.scheme, gw=a.gw, device=str(dev),
                x2cov=os.environ.get("SNAPY_X2COV", "unset"), nsteps=a.nsteps, amp=a.amp, bal_res=res,
                t_end=sum(dts), dt_first=dts[0], finite=fin,
                max_w_end=float(W[IV1, 0, I, I].abs().max()),
                max_abs_rel_dE=max(abs(h[2]) for h in hist), hist=hist, snapy=snapy.__version__)


def compare(da, db):
    A = torch.load(os.path.join(da, "W_final.pt"))
    B = torch.load(os.path.join(db, "W_final.pt"))
    I = slice(NG, -NG)
    out = {}
    for name, v in (("rho", kIDN), ("w", IV1), ("u", IV2), ("p", kIPR)):
        x, y = A[v, 0, I, I], B[v, 0, I, I]
        rng = float(x.max() - x.min()) or 1.0
        out[name] = dict(max_abs=float((x - y).abs().max()), range=rng,
                         rel=float((x - y).abs().max()) / rng)
    return out


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        print(json.dumps(compare(sys.argv[2], sys.argv[3]), indent=1))
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["onestep", "run"])
    ap.add_argument("--nz", type=int, default=32)
    ap.add_argument("--eps", type=float, default=0.0)
    ap.add_argument("--scheme", type=int, default=9)
    ap.add_argument("--gw", default="face")
    ap.add_argument("--cfl", type=float, default=0.4)
    ap.add_argument("--dtfac", type=float, default=1.0)
    ap.add_argument("--amp", type=float, default=1e-5)
    ap.add_argument("--nsteps", type=int, default=2000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = onestep(a) if a.mode == "onestep" else run(a)
    print(json.dumps({k: v for k, v in out.items() if k != "hist"}))
    json.dump(out, open(os.path.join(a.out, "diag.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
