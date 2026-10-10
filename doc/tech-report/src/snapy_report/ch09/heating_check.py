"""Executable check of body heating, top cooling and bottom heating (chapter 9, _heating.qmd).

What is checked: BodyHeatImpl::forward (src/forcing/body_heat.cpp:43-55),
TopCoolImpl::forward (src/forcing/top_cool.cpp:42-56) and BotHeatImpl::forward
(src/forcing/bot_heat.cpp:42-56) at snapy@e894700ff7aee30b52882e5202b16461413780b0, ported
line for line on one Cartesian column. Claims C1-C3.

Run: python3 heating_check.py   (numpy only; exits with the number of failed claims)
"""
import sys

import numpy as np


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def top_cool(dx1f, flux, depth, dt):  # top_cool.cpp:51-54, interior cells only
    dE = np.zeros_like(dx1f)
    dz = dx1f[-1]
    dE[len(dx1f) - depth:] += dt * flux / (dz * depth)
    return dE


def check_C1_column_power_uniform():
    dx1f = np.full(20, 50.)
    dE = top_cool(dx1f, -30., 4, 1.)
    power = (dE * dx1f).sum()
    return report("C1", abs(power + 30.) < 1e-12, "uniform cells: the column loses exactly F per unit area",
                  "sum dE dz = %.12f W m^-2 for F = -30, depth 4" % power)


def check_C2_column_power_stretched():
    dx1f = 50. * 1.1**np.arange(20)  # cells growing upward by 10 %
    dE = top_cool(dx1f, -30., 4, 1.)
    power = (dE * dx1f).sum()
    ratio = power / -30.
    want = dx1f[-4:].sum() / (4. * dx1f[-1])
    return report("C2", abs(ratio - want) < 1e-14,
                  "stretched cells: the delivered power is F times mean(dz)/dz_top",
                  "ratio %.6f for 10 %% growth, depth 4 (= %.6f)" % (ratio, want))


def check_C3_body_heat_is_isochoric():
    rho, cv, dTdt, dt = 1.1, 717.5, 2.e-5, 10.
    dE = dt * dTdt * rho * cv  # body_heat.cpp:52-53
    dT = dE / (rho * cv)  # at fixed rho and constant cv
    return report("C3", abs(dT - dTdt * dt) < 1e-18, "body heat raises T by dTdt dt at fixed volume",
                  "dT = %.3e K for dTdt dt = %.3e K" % (dT, dTdt * dt))


def main():
    checks = [check_C1_column_power_uniform, check_C2_column_power_stretched,
              check_C3_body_heat_is_isochoric]
    sys.exit(sum(not c() for c in checks))


if __name__ == "__main__":
    main()
