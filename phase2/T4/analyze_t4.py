#!/usr/bin/env python3
"""TEST 4 analysis: the two oracles from snapy prim frames.

  (i)  steady energy balance: f(z) = (F_enth + F_KE)(z) / F, horizontally averaged and
       time-averaged over the window; f_int = mean of f over the interior z/Lz in [0.2, 0.8].
       F_enth = cp <rho w (T - <T>)>, F_KE = <rho w |u|^2/2>, F_visc = -nu <rho (w (2 w_z - 2/3 div)
       + u (u_z + w_x))> (snapy's kinematic stress, diffusion.cpp); no explicit conduction in this
       deck (F_cond = 0), so the oracle is f_int -> 1.
       (The <rho w> cp <T> part is dropped: its time mean is zero in a sealed box.)
  (ii) M_rms = sqrt(volume mean of |u|^2 / c_s^2) averaged over the window; scaling vs eps.

  run mode:   analyze_t4.py run <rundir> [--t0-tc 20]       -> <rundir>/t4_summary.json
  table mode: analyze_t4.py table <summary.json>...          -> markdown table + slopes

Errors: the standard error of a window mean uses blocks of 2 t_c (frames every 0.5 t_c).
"""
import glob
import json
import math
import os
import re
import sys

import numpy as np
import yaml


def load_frames(rundir):
    import netCDF4
    files = sorted(glob.glob(os.path.join(rundir, "*.out0.*.nc")))
    out = []
    for fn in files:
        with netCDF4.Dataset(fn) as ds:
            t = float(ds["time"][0])
            g = lambda k: np.asarray(ds[k][0, :, 0, :], dtype=np.float64)  # (x1, x2)
            out.append((t, g("rho"), g("press"), g("vel1"), g("vel2"),
                        np.asarray(ds["x1"][:]), np.asarray(ds["x1f"][:])))
    return out


def last_dt(rundir):
    dts = []
    for fn in sorted(glob.glob(os.path.join(rundir, "run_*.log"))):
        for line in open(fn, errors="replace"):
            m = re.search(r"cycle=(\d+).* dt=([0-9.eE+-]+)", line)
            if m:
                dts.append(float(m.group(2)))
    return float(np.median(dts[-20:])) if dts else float("nan")


def block_mean(x, nb):
    x = np.asarray(x)
    n = len(x) // nb
    if n < 2:
        return float(np.mean(x)), float("nan")
    b = x[: n * nb].reshape(n, nb).mean(1)
    return float(np.mean(x)), float(np.std(b, ddof=1) / math.sqrt(n))


def run(rundir, t0_tc=20.0):
    ident = yaml.safe_load(open(os.path.join(rundir, "IDENTITY.yaml")))
    d = ident["derived"]
    gamma, Rd, F, Lz, tc, g = d["gamma"], d["Rd"], d["F"], d["Lz"], d["t_c"], d["g"]
    nu = d.get("nu", 0.0)
    cp = gamma * Rd / (gamma - 1.0)
    frames = load_frames(rundir)
    ts, fint, mach, ke, fprof, fvis = [], [], [], [], [], []
    for (t, rho, p, w, u, z, zf) in frames:
        T = p / (rho * Rd)
        cs2 = gamma * p / rho
        Tm = T.mean(1, keepdims=True)
        fe = cp * (rho * w * (T - Tm)).mean(1)
        fk = (rho * w * 0.5 * (u * u + w * w)).mean(1)
        dz_, dx_ = float(z[1] - z[0]), d["Lx"] / u.shape[1]
        ddx = lambda a: (np.roll(a, -1, 1) - np.roll(a, 1, 1)) / (2 * dx_)
        ddz = lambda a: np.gradient(a, dz_, axis=0)
        div = ddz(w) + ddx(u)
        fv = -nu * (rho * (w * (2 * ddz(w) - 2.0 / 3.0 * div) + u * (ddz(u) + ddx(w)))).mean(1)
        f = (fe + fk + fv) / F
        zi = (z / Lz >= 0.2) & (z / Lz <= 0.8)
        ts.append(t / tc)
        fint.append(float(f[zi].mean()))
        mach.append(float(math.sqrt(((u * u + w * w) / cs2).mean())))
        ke.append(float((0.5 * rho * (u * u + w * w)).mean()))
        fprof.append(f)
        fvis.append(float((fv / F)[zi].mean()))
    ts = np.array(ts)
    sel = ts >= t0_tc
    nb = 4  # 2 t_c blocks at 0.5 t_c output
    s = {"rundir": os.path.abspath(rundir), "snapy": ident.get("snapy"),
         "gw": ident["gravity_work"], "eps": d["eps"], "t_end_tc": float(ts[-1]) if len(ts) else 0,
         "nframes_window": int(sel.sum()), "t0_tc": t0_tc}
    card = yaml.safe_load(open(ident["card"])) if os.path.exists(ident["card"]) else None
    if card:
        s["nz"] = card["geometry"]["cells"]["nx1"]
        s["nx"] = card["geometry"]["cells"]["nx2"]
        s["scheme"] = card["integration"]["implicit-scheme"]
        s["seed"] = card["problem"]["seed"]
    if frames:
        t, rho, p, w, u, z, zf = frames[-1]
        dz = float(zf[1] - zf[0])
        cs = np.sqrt(gamma * p / rho)
        H = Rd * (p / rho) / g
        dt = last_dt(rundir)
        s["courant_v"] = float(dt * (cs + np.abs(w)).max() / dz)
        s["dz_over_H_max"] = float((dz / H).max())
        s["dz_over_H_min"] = float((dz / H).min())
        s["dt"] = dt
    if sel.sum() >= 2:
        s["f_int"], s["f_int_se"] = block_mean(np.array(fint)[sel], nb)
        s["M_rms"], s["M_rms_se"] = block_mean(np.array(mach)[sel], nb)
        s["f_visc_int"] = float(np.mean(np.array(fvis)[sel]))
        s["f_profile"] = np.mean(np.array(fprof)[sel], 0).tolist()
        s["z_over_Lz"] = (frames[0][5] / Lz).tolist()
    s["series"] = {"t_tc": ts.tolist(), "f_int": fint, "M_rms": mach, "ke": ke}
    with open(os.path.join(rundir, "t4_summary.json"), "w") as f:
        json.dump(s, f)
    print(json.dumps({k: v for k, v in s.items() if k not in ("series", "f_profile", "z_over_Lz")}))
    return s


def bin_c(c):
    return "<1" if c < 1 else ("1-10" if c <= 10 else ">10")


def bin_h(h):
    return "<0.1" if h < 0.1 else ("0.1-0.5" if h <= 0.5 else ">0.5")


def table(files):
    rows = [json.load(open(f)) for f in files]
    rows = [r for r in rows if "M_rms" in r]
    groups = {}
    for r in rows:
        groups.setdefault((r["scheme"], r["gw"], r["nz"], r["eps"]), []).append(r)
    print("| scheme | form | nz | eps | seeds | C_v (bin) | dz/H max (bin) | f_int mean +/- sd(seeds) | M_rms mean +/- sd(seeds) |")
    print("|---|---|---|---|---|---|---|---|---|")
    agg = {}
    for k in sorted(groups):
        g = groups[k]
        f = np.array([r["f_int"] for r in g])
        m = np.array([r["M_rms"] for r in g])
        c = np.mean([r["courant_v"] for r in g])
        h = np.mean([r["dz_over_H_max"] for r in g])
        sdf = f.std(ddof=1) if len(f) > 1 else float("nan")
        sdm = m.std(ddof=1) if len(m) > 1 else float("nan")
        agg[k] = (m.mean(), sdm / math.sqrt(len(m)) if len(m) > 1 else float("nan"))
        print(f"| {k[0]} | {k[1]} | {k[2]} | {k[3]:g} | {','.join(str(r['seed']) for r in g)} | "
              f"{c:.2f} ({bin_c(c)}) | {h:.3f} ({bin_h(h)}) | {f.mean():.4f} +/- {sdf:.4f} | "
              f"{m.mean():.4e} +/- {sdm:.2e} |")
    print("\nM_rms vs eps slopes (least squares in log-log over the eps present; oracle 1/3):")
    keys = sorted({k[:3] for k in agg})
    for kk in keys:
        es = sorted(k[3] for k in agg if k[:3] == kk)
        if len(es) < 2:
            continue
        x = np.log([e for e in es])
        y = np.log([agg[kk + (e,)][0] for e in es])
        p = np.polyfit(x, y, 1)[0]
        pairs = [f"{es[i]:g}->{es[i+1]:g}: {(y[i+1]-y[i])/(x[i+1]-x[i]):.3f}" for i in range(len(es) - 1)]
        print(f"  scheme {kk[0]} {kk[1]} nz {kk[2]}: slope {p:.3f}  local [{'; '.join(pairs)}]")


if __name__ == "__main__":
    if sys.argv[1] == "run":
        t0 = 20.0
        if "--t0-tc" in sys.argv:
            t0 = float(sys.argv[sys.argv.index("--t0-tc") + 1])
        run(sys.argv[2], t0)
    elif sys.argv[1] == "table":
        table(sys.argv[2:])
