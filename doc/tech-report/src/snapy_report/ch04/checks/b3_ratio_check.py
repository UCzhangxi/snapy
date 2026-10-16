"""Executable check of the compositional/thermal ratio R of the face-flux covariance (chapter 4B, _fluxcov.qmd).

Ports the covariance rows of src/hydro/hydro_forward.cpp HydroImpl::_flux_covariance (the cov closure) at
snapy@6fbb39750f62b83df096058a4746e77d0a634bc5 (src/hydro/hydro_forward.cpp:157-184): energy sigma1^2 rho D1[h] D1[u_n], tracer n
sigma1^2 rho D1[u_n] D1[q_n], dry mass minus the tracer sum, sigma1^2 = dx1^2/12 in Cartesian. Each row's x2
divergence is the error the uncorrected scheme makes; R is the ratio of the buoyancy those errors carry,
compositional over thermal.
[C1] route B (the ported rows on a discrete column) converges to route A (closed form, R = a T q_z / T_z) at O(dz^2).
[C2] dz cancels: halving dz divides both rows by 4, and the common factor sigma1^2 rho D1[u_n] drops out of R.
[C3] R at the cloud base of the three cases has the sign and order of magnitude (within a factor 3) of the
     independent written order-of-magnitude estimate (chengcli/snapy#289 item 3); it is not expected to reproduce it.

Inputs, none fitted:
- the decks at the code pin, examples/, keys species/dry, forcing/const-gravity/grav1 and problem/{Ps, Ts, xH2O}:
  earth_crm.yaml (Ts 300 K, Ps 1e5 Pa, xH2O 0.02, grav1 -9.8, dry {O 0.42, N 1.56, Ar 0.01});
  jupiter_crm.yaml (Ts 600 K, Ps 100e5 Pa, xH2O 3e-3, grav1 -22, dry {H 1.5, He 0.15});
  uranus.yaml (Ts 250 K, Ps 50e5 Pa, grav1 -9.01, same dry gas). Every gas has cv_R 2.5, so cp/R = 3.5 per mole.
- vapour pressure: kintera@c55b13b2204997d2d09e04498558ab9495d8ee77 src/vapors/vapor_functions.h h2o_ideal and
  ch4_ideal; L = R_v T^2 dln(e_s)/dT from the same fit.
- uranus.yaml carries no CH4: deep CH4 mole fraction 0.023 (Lindal et al. 1987, JGR 92, 14987) and 0.04
  (Karkoschka & Tomasko 2009, Icarus 202, 287).
- cloud base: lift the deck's surface gas on its dry adiabat until x p = e_s(T). Above it, T_z is either the
  saturated (pseudo)adiabat or the dry adiabat; both are printed.
Run: python3 b3_ratio_check.py   (numpy only; exits with the number of failed claims)
"""
import sys

import numpy as np

RGAS = 8.314462618  # J/(mol K)
CPR = 3.5  # cv_R 2.5 for every gas in the three decks
MU = {"H": 1.008, "He": 4.0026, "O": 15.999, "N": 14.007, "Ar": 39.948, "H2O": 18.015, "CH4": 16.043}  # g/mol
ESTIMATE = {"Earth H2O": (0.10, 0.12), "Jupiter H2O": (-0.28, -0.28), "ice giant CH4": (-0.8, -0.8)}  # the written estimate


def svp(bl, gl, bs, gs, tr, pr):  # kintera logsvp_ideal: ln(e/pr) = b (1 - 1/t) - g ln t, t = T/tr
    def f(T):
        t = T / tr; b, g = (bl, gl) if T > tr else (bs, gs)
        return pr * np.exp((1. - 1. / t) * b - g * np.log(t)), (b / t**2 - g / t) / tr  # e_s, dln(e_s)/dT
    return f


H2O = svp(24.845, 4.986009, 22.98, 0.52, 273.16, 611.7)
CH4 = svp(10.15, 2.1, 10.41, 0.9, 90.67, 11690.)
CASES = [  # name, Ts, Ps, g, mu_dry, mu_vap, x_vap, e_s
    ("Earth H2O", 300., 1e5, 9.8, .42 * MU["O"] + 1.56 * MU["N"] + .01 * MU["Ar"], MU["H2O"], 0.02, H2O),
    ("Jupiter H2O", 600., 100e5, 22., 1.5 * MU["H"] + .15 * MU["He"], MU["H2O"], 3e-3, H2O),
    ("ice giant CH4", 250., 50e5, 9.01, 1.5 * MU["H"] + .15 * MU["He"], MU["CH4"], 0.023, CH4),
    ("ice giant CH4", 250., 50e5, 9.01, 1.5 * MU["H"] + .15 * MU["He"], MU["CH4"], 0.04, CH4),
]


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


class Gas:
    def __init__(self, g, mud, muv, es):
        self.g, self.mud, self.muv, self.es = g, mud * 1e-3, muv * 1e-3, es

    def state(self, T, p):  # saturated: x = e_s/p, q = x mu_v/mu
        e, A = self.es(T); x = e / p; mu = x * self.muv + (1. - x) * self.mud
        q = x * self.muv / mu
        cp = CPR * RGAS * ((1. - q) / self.mud + q / self.muv)
        return x, q, mu, cp, A

    def tz(self, T, p, moist):  # dT/dz on the dry adiabat or the saturated pseudo-adiabat
        x, q, mu, cp, A = self.state(T, p)
        if not moist:
            return -self.g / cp
        L = RGAS / self.muv * T * T * A; B = x * self.muv * self.mud / mu**2; dlnp = -self.g * mu / (RGAS * T)
        return -(self.g - L * B * dlnp) / (cp + L * B * A)  # cp dT + L dq = -g dz, dq = B dln x

    def a(self, mu):  # -(dln rho/dq) at fixed p, T
        return mu * (1. / self.muv - 1. / self.mud)


def cloud_base(gas, Ts, Ps, x):
    lo, hi = 1., Ps
    for _ in range(200):
        p = np.sqrt(lo * hi); T = Ts * (p / Ps)**(1. / CPR)
        lo, hi = (lo, p) if x * p < gas.es(T)[0] else (p, hi)
    return Ts * (hi / Ps)**(1. / CPR), hi


def route_a(gas, T, p, moist):  # closed form: R = a T q_z / T_z
    x, q, mu, cp, A = gas.state(T, p); Tz = gas.tz(T, p, moist)
    xz = x * (A * Tz + gas.g * mu / (RGAS * T)); qz = gas.muv * gas.mud / mu**2 * xz
    return gas.a(mu) * T * qz / Tz


def column(gas, T0, p0, moist, dz):  # cells -1, 0, +1 about the cloud base, RK4 on (T, p)
    def rhs(y):
        mu = gas.state(*y)[2]
        return np.array([gas.tz(y[0], y[1], moist), -gas.g * y[1] * mu / (RGAS * y[0])])

    def step(y, h):
        k1 = rhs(y); k2 = rhs(y + .5 * h * k1); k3 = rhs(y + .5 * h * k2); k4 = rhs(y + h * k3)
        return y + h / 6. * (k1 + 2 * k2 + 2 * k3 + k4)
    y0 = np.array([T0, p0]); ys = []
    for sgn in (-1., 1.):
        y = y0.copy()
        for _ in range(64):
            y = step(y, sgn * dz / 64.)
        ys.append(y)
    return [ys[0], y0, ys[1]]


def route_b(gas, T0, p0, moist, dz, m=2. * np.pi / 2e4):
    """The ported rows (HydroImpl::_flux_covariance, the cov closure) at the middle cell; u_n = sin(m z + 1)."""
    cells = column(gas, T0, p0, moist, dz)
    z = np.array([-dz, 0., dz]); un = np.sin(m * z + 1.)
    T = np.array([c[0] for c in cells]); st = [gas.state(c[0], c[1]) for c in cells]
    q = np.array([s[1] for s in st]); cp = np.array([s[3] for s in st])
    hd, hv = CPR * RGAS / gas.mud * T, CPR * RGAS / gas.muv * T  # h_n = cp_n T, u0_R = 0 for the gases
    h = (1. - q) * hd + q * hv
    rho = p0 * st[1][2] / (RGAS * T0)
    d1 = lambda f: (f[2] - f[0]) / (2. * dz)  # noqa: E731
    s2 = dz * dz / 12.
    row_e = s2 * rho * d1(h) * d1(un)  # energy row
    row_q = s2 * rho * d1(un) * d1(q)  # tracer row; the dry row is -row_q
    # T error: the energy row less the enthalpy the species rows carry; q error: the tracer row
    t_err = (row_e - (hv[1] - hd[1]) * row_q) / (rho * cp[1])
    q_err = row_q / rho
    return gas.a(st[1][2]) * q_err / (t_err / T0), row_e, row_q


def main():
    bad = 0; res = []
    for name, Ts, Ps, g, mud, muv, x, es in CASES:
        gas = Gas(g, mud, muv, es); T0, p0 = cloud_base(gas, Ts, Ps, x)
        H = RGAS * T0 / (g * gas.state(T0, p0)[2])
        q0, mu0 = gas.state(T0, p0)[1:3]
        row = {"name": name, "x": x, "T0": T0, "p0": p0, "q": q0, "mu": 1e3 * mu0, "a": gas.a(mu0)}
        for moist in (True, False):
            rb = [route_b(gas, T0, p0, moist, H / n) for n in (32, 64, 128)]
            row[moist] = (route_a(gas, T0, p0, moist), [b[0] for b in rb], [b[1] for b in rb], [b[2] for b in rb],
                          route_b(gas, T0, p0, moist, H / 64, m=2. * np.pi / 7e3)[0], -gas.tz(T0, p0, moist))
        res.append(row)
    runs = [r[m] for r in res for m in (True, False)]
    err = [[abs(b - v[0]) / abs(v[0]) for b in v[1]] for v in runs]
    order = [np.log2(e[1] / e[2]) for e in err]
    bad += not report("C1", max(e[2] for e in err) < 1e-3 and min(order) > 1.9,
                      "route B (the ported rows) converges to route A (a T q_z / T_z) at second order",
                      "max |R_B - R_A| / |R_A| at dz = H/32, H/64, H/128: %.1e %.1e %.1e; orders %.2f..%.2f"
                      % (max(e[0] for e in err), max(e[1] for e in err), max(e[2] for e in err),
                         min(order), max(order)))
    rat = [v[k][i] / v[k][i + 1] for v in runs for k in (2, 3) for i in (1,)]
    mode = max(abs(v[4] - v[1][1]) / abs(v[1][1]) for v in runs)
    bad += not report("C2", max(abs(x - 4.) for x in rat) < 5e-2 and mode < 1e-12,
                      "dz cancels in R: halving dz divides both rows by 4, and R does not depend on the mode's "
                      "D1[u_n] at all", "energy and tracer rows, H/64 over H/128, in [%.4f, %.4f]; "
                      "max |R(m) - R(m')| / |R| = %.1e" % (min(rat), max(rat), mode))
    lines, worst = [], 1.
    for r in res:
        lo, hi = ESTIMATE[r["name"]]
        for moist in (True, False):
            ra, rb, gam = r[moist][0], r[moist][1][1], r[moist][5]
            f = min(ra / lo, ra / hi); worst = min(worst, f, 1. / max(ra / lo, ra / hi))
            lines.append("  %-13s x %.3f  p %6.3f bar  T %5.1f K  q %.4f  mu %6.3f g/mol  a %+.3f  %s %5.2f K/km  "
                         "R %+.3f (%+.3f)  estimate %s"
                         % (r["name"], r["x"], r["p0"] / 1e5, r["T0"], r["q"], r["mu"], r["a"],
                            "saturated" if moist else "dry      ", gam * 1e3, ra, rb,
                            ("%+.2f" % lo) if lo == hi else ("%+.2f..%+.2f" % (lo, hi))))
    bad += not report("C3", worst > 1. / 3., "R at the cloud base (route A; route B at dz = H/64) has the sign and "
                      "order of the written estimate", "min over cases of R/estimate and estimate/R = %.2f" % worst)
    print("\n".join(lines))
    print("ALL PASS (3 claims)" if bad == 0 else "%d FAILED" % bad)
    return bad


if __name__ == "__main__":
    sys.exit(main())
