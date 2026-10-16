"""Executable check of the resumed output times (chapter 14, _restart.qmd).

What is checked, at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported line for line below:
- the next_time rule of MeshBlockImpl::_init_from_restart (src/mesh/meshblock.cpp:1376-1398);
- the output test and advance of MeshBlockImpl::make_outputs (src/mesh/meshblock.cpp:991-995).
Claims C1-C3.

Run: python3 restart_check.py   (numpy; exits with the number of failed claims)
"""
import math
import sys

import numpy as np


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def restored_next(saved, t, dt):  # meshblock.cpp:1381-1390, an output matched to a saved one
    if dt > 0.0 and saved > t + dt:
        return t + dt
    return saved


def new_next(t, dt):  # meshblock.cpp:1391-1395, an output new in the resumed card
    return t - math.fmod(t, dt) if dt > 0.0 else t


def fires(t, next_time):  # meshblock.cpp:991
    return t >= next_time


def check_C1_shrunk_interval():
    t, dt = 3600.0, 60.0
    shrunk = restored_next(t + 600.0, t, dt)        # saved with dt = 600, resumed with dt = 60
    disabled = restored_next(1e300, t, dt)          # an output disabled by a far-future time
    kept = restored_next(t + 0.5 * dt, t, dt)       # a live cadence within one interval
    nonpos = restored_next(1e300, t, 0.0)
    ok = shrunk == t + dt and disabled == t + dt and kept == t + 0.5 * dt and nonpos == 1e300
    return report("C1", ok, "a saved time more than one interval ahead is clamped to t_r + dt; others are kept",
                  "saved t_r+600 -> t_r+%g; saved 1e300 -> t_r+%g; saved t_r+30 -> t_r+%g; dt = 0 keeps %g"
                  % (shrunk - t, disabled - t, kept - t, nonpos))


def check_C2_new_output_on_grid():
    rng = np.random.default_rng(14)
    dts = rng.uniform(1e-3, 1e3, 20000)
    ts = dts * rng.uniform(0., 1e4, 20000)
    nxt = np.array([new_next(t, dt) for t, dt in zip(ts, dts)])
    below = np.all(nxt <= ts)
    within = np.all(ts - nxt < dts)
    k = nxt / dts
    grid = np.abs(k - np.round(k)).max()  # k < 1e4: a few ulp of k is ~1e-12
    first = all(fires(t, n) for t, n in zip(ts, nxt))
    return report("C2", below and within and first and grid < 16 * 1e4 * np.finfo(float).eps,
                  "a new output starts on the multiple of dt at or below t_r and fires at the first output check",
                  "20000 (t_r, dt): next <= t_r %s, t_r - next < dt %s, max |next/dt - round| = %.1e"
                  % (below, within, grid))


def check_C3_one_write_per_interval():
    t_r, dt_old, dt = 3600.0, 600.0, 60.0
    nxt = restored_next(t_r + dt_old, t_r, dt)
    writes, t = [], t_r
    for _ in range(int(round(dt_old / 10.0))):   # 10 s steps up to the old saved time
        t += 10.0
        if fires(t, nxt):
            writes.append(t)
            nxt += dt
    return report("C3", writes == [t_r + 60.0 * k for k in range(1, 11)],
                  "after the clamp the output writes every dt from t_r + dt, not first at the old saved time",
                  "writes in (t_r, t_r + 600]: %d, first at t_r + %g" % (len(writes), writes[0] - t_r))


def main():
    checks = [check_C1_shrunk_interval, check_C2_new_output_on_grid, check_C3_one_write_per_interval]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
