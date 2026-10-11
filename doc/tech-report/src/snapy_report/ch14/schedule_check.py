"""Executable check of the output statistics (chapter 14, _schedule.qmd).

What is checked, at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported line for line below:
- update_weighted_moments, OutputType::AccumulateStats, ResetStats and PrimStatStd
  (src/output/output_type.cpp:282-360).
Claims C1-C3.

Run: python3 schedule_check.py   (numpy; exits with the number of failed claims)
"""
import sys

import numpy as np


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


class Stats:  # the members of OutputType that the statistics use
    def __init__(self):
        self.mean = self.m2 = None
        self.elapsed, self.last, self.initialized = 0.0, 0.0, False

    def update(self, value, weight, previous_weight):  # update_weighted_moments, output_type.cpp:282-294
        if self.mean is None:
            self.mean, self.m2 = np.zeros_like(value), np.zeros_like(value)
        delta = value - self.mean
        total = previous_weight + weight
        self.mean += delta * (weight / total)
        self.m2 += weight * delta * (value - self.mean)

    def accumulate(self, value, t):  # AccumulateStats, output_type.cpp:297-326
        if not self.initialized:
            self.last, self.initialized = t, True
            return
        dt = t - self.last
        if dt > 0.0:
            self.update(value, dt, self.elapsed)
            self.elapsed += dt
        self.last = t

    def reset(self, t):  # ResetStats, output_type.cpp:328-345
        if self.mean is not None:
            self.mean[...] = 0.
            self.m2[...] = 0.
        self.elapsed, self.last, self.initialized = 0.0, t, True

    def std(self, current):  # PrimStatStd, output_type.cpp:354-360
        if self.elapsed <= 0.0 or self.m2 is None:
            return np.zeros_like(current)
        return np.sqrt(np.maximum(self.m2 / self.elapsed, 0.0))


def run(times, values, reset_first):
    s = Stats()
    if reset_first:  # an earlier write left the statistics reset at times[0]
        s.accumulate(values[0] * 0. + 1e9, times[0] - 1.)
        s.accumulate(values[0] * 0. - 1e9, times[0] - .5)
        s.reset(times[0])
    for t, q in zip(times, values):
        s.accumulate(q, t)
    return s


def direct(times, values):  # right-endpoint weights: q_i carries t_i - t_{i-1}; q_0 carries nothing
    w = np.diff(times)
    q = np.array(values[1:])
    mean = np.tensordot(w, q, 1) / w.sum()
    var = np.tensordot(w, (q - mean) ** 2, 1) / w.sum()
    return mean, var


def check_C1_welford_equals_two_pass():
    rng = np.random.default_rng(1414)
    worst_m, worst_s = 0., 0.
    for trial in range(20):
        times = np.cumsum(rng.uniform(0.1, 10., 200))
        values = list(rng.normal(300., 20., (200, 8)))
        s = run(times, values, reset_first=bool(trial % 2))
        mean, var = direct(times, values)
        worst_m = max(worst_m, np.abs(s.mean - mean).max() / np.abs(mean).max())
        worst_s = max(worst_s, np.abs(s.std(values[-1]) - np.sqrt(var)).max() / np.sqrt(var).max())
    # bounds: round-off of 200 updates, far above the measured 1e-15
    return report("C1", worst_m < 1e-13 and worst_s < 1e-12,
                  "the recurrence gives the step-weighted mean and the population deviation of the two-pass formula",
                  "20 runs of 200 unequal steps (half after a reset): max rel. error mean %.1e, sigma %.1e"
                  % (worst_m, worst_s))


def check_C2_right_endpoint():
    times = [0., 1., 3.]
    values = [np.array([100.]), np.array([1.]), np.array([4.])]
    s = run(times, values, reset_first=False)
    return report("C2", s.mean[0] == 3. and s.elapsed == 3.,
                  "the state at the first call carries no weight; each later state carries the step ending at it",
                  "q = 100, 1, 4 at t = 0, 1, 3: mean %g (= (1*1 + 2*4)/3), W = %g" % (s.mean[0], s.elapsed))


def check_C3_population_not_sample():
    times = [0., 1., 2.]
    values = [np.array([0.]), np.array([1.]), np.array([3.])]
    s = run(times, values, reset_first=False)
    const = run([0., 1., 2.5, 4.], [np.array([7.1])] * 4, reset_first=False)
    sig = s.std(values[-1])[0]
    return report("C3", sig == 1. and const.m2[0] == 0. and const.std(values[-1])[0] == 0.,
                  "sigma = sqrt(M2 / W) with no small-sample correction; a constant field has M2 = 0 exactly",
                  "q = 1, 3 with equal steps: sigma %g (sample form would give %g); constant: M2 = %g"
                  % (sig, np.sqrt(2.), const.m2[0]))


def main():
    checks = [check_C1_welford_equals_two_pass, check_C2_right_endpoint, check_C3_population_not_sample]
    return sum(not c() for c in checks)


if __name__ == "__main__":
    sys.exit(main())
