#!/usr/bin/env python3
"""Fit the T1L growth rate from run_t1l.py's diag.txt (predeclared, the same for both forms).

Window: t in [1, 5] / sigma_EVP (EVP e-folds 1-5 after the seed); sub-windows [1, 3] and [3, 5] for
window stability. Fit: least squares of ln|A_w| (mass-weighted projection of w onto the EVP mode).
Also the same for the wall-excluded projection and for A_T (the temperature projection), and the
frequency omega = d(arg A_w)/dt (zero for the real EVP mode; nonzero flags an oscillating discrete mode).

    python fit_t1l.py RUNDIR [RUNDIR ...]  -> one line per run (also --json)
"""
import json
import os
import re
import sys

import numpy as np


def fit(t, a, t0, t1):
    s = (t >= t0) & (t <= t1)
    if s.sum() < 5:
        return float("nan")
    return float(np.polyfit(t[s], np.log(np.abs(a[s])), 1)[0])


def fit_freq(t, a, t0, t1):
    s = (t >= t0) & (t <= t1)
    if s.sum() < 5:
        return float("nan")
    return float(np.polyfit(t[s], np.unwrap(np.angle(a[s])), 1)[0])


def one(d):
    card = open(os.path.join(d, "card.yaml")).read()
    sig = float(re.search(r"sigma_EVP = ([0-9.eE+-]+)", card).group(1))
    eps = float(re.search(r"# eps = ([0-9.eE+-]+)", card).group(1))
    gw = re.search(r"gravity-work: (\w+)", card).group(1)
    nz = int(re.search(r"nx1: (\d+)", card).group(1))
    x = np.loadtxt(os.path.join(d, "diag.txt"))
    t = x[:, 1]
    Aw = x[:, 2] + 1j * x[:, 3]
    AT = x[:, 4] + 1j * x[:, 5]
    Awi = x[:, 6] + 1j * x[:, 7]
    e1, e3, e5 = 1 / sig, 3 / sig, 5 / sig
    r = dict(run=os.path.basename(os.path.normpath(d)), eps=eps, nz=nz, gw=gw, sigma_EVP=sig,
             t_end_efold=float(t[-1] * sig), complete=bool(t[-1] >= e5 * (1 - 1e-9)),
             sigma=fit(t, Aw, e1, e5), sigma_13=fit(t, Aw, e1, e3), sigma_35=fit(t, Aw, e3, e5),
             sigma_nowall=fit(t, Awi, e1, e5), sigma_T=fit(t, AT, e1, e5),
             maxMach_end=float(x[-1, 10]), mass_drift=float(x[-1, 11] / x[0, 11] - 1),
             phase_end=float(np.angle(Aw[-1])), omega=fit_freq(t, Aw, e1, e5))
    r["rel_err"] = r["sigma"] / sig - 1
    r["window_spread"] = (r["sigma_35"] - r["sigma_13"]) / sig
    return r


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    rows = [one(d) for d in args]
    if "--json" in sys.argv:
        print(json.dumps(rows, indent=1))
    else:
        for r in rows:
            print(f"{r['run']:28s} eps={r['eps']:.0e} nz={r['nz']:3d} {r['gw']:4s} "
                  f"efolds={r['t_end_efold']:.2f} sigma={r['sigma']:.10g} EVP={r['sigma_EVP']:.10g} "
                  f"rel={r['rel_err']:+.4e} win13/35={r['sigma_13'] / r['sigma_EVP'] - 1:+.3e}/"
                  f"{r['sigma_35'] / r['sigma_EVP'] - 1:+.3e} nowall={r['sigma_nowall'] / r['sigma_EVP'] - 1:+.3e} "
                  f"T={r['sigma_T'] / r['sigma_EVP'] - 1:+.3e} omega/sig={r['omega'] / r['sigma_EVP']:+.2e} Ma={r['maxMach_end']:.2e}")
