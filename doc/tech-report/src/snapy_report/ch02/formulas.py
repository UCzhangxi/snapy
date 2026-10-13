"""Independent formula checks, symbolic derivations and round-off ports; no compiled solver execution.

Formulas: snapy 6fbb39750f62b83df096058a4746e77d0a634bc5 (the code pin);
kintera c55b13b2204997d2d09e04498558ab9495d8ee77. See chapter Code tables.
Synthetic inputs in this file are the complete decks; the random decks use
numpy's default_rng with the seed named in each check. All floating-point
arithmetic uses CPU float64. Relative tolerance 1e-12 allows accumulated
round-off in small well-conditioned sums. Rotor central differences use 2e-6
relative: finite-difference truncation and cancellation, not an EOS runtime
tolerance. Round-off claims compare a float64 port of the code's operation
order with exact rational arithmetic (fractions.Fraction) on the same float
inputs, and pass when every measured error is inside the bound the chapter
derives (first order in the unit round-off EPS_M/2).
"""
from fractions import Fraction as Q

import numpy as np
import sympy as sp

EPS_M = 2.0**-52  # machine epsilon of float64; one rounding is within EPS_M/2


def check_C1_laws():
    flux = np.array([0., 2., -3., 1., 0.])
    volumes = np.array([1., 3., 2., 4.])
    residual = abs(np.dot(volumes, -np.diff(flux) / volumes))
    ok = residual < 1e-12
    print(f'[C1] {"PASS" if ok else "FAIL"} telescoping={residual:.3e}')
    return ok


def check_C1_ideal_gas():
    metric = np.array([[1., 0., 0.], [0., 1., .3], [0., .3, 1.]])
    rho, p, gamma = 1.3, 1e5, 1.4
    v = np.array([2., -3., 4.])
    mom = rho * metric @ v
    energy = p / (gamma - 1) + .5 * v @ mom
    recovered_v = np.linalg.solve(metric, mom / rho)
    recovered_p = (gamma - 1) * (energy - .5 * recovered_v @ mom)
    residual = max(abs(recovered_p/p-1), np.max(abs(recovered_v-v)))
    ok = residual < 1e-12
    print(f'[C1] {"PASS" if ok else "FAIL"} metric inverse residual={residual:.3e}')
    return ok


def mixture():
    # dry gas, vapor, condensate; zero pressure coefficient for condensate
    rho = np.array([.92, .05, .03])
    cv = np.array([720., 1400., 2100.])
    gas = np.array([287., 461., 0.])
    offset = np.array([100., 2e6, -1e5])
    return rho, cv, gas, offset


def check_C1_ideal_moist():
    rho, cv, gas, offset = mixture()
    y = rho[1:]/sum(rho)
    feps = 1 + y[0]*(gas[1]/gas[0]-1)-y[1]
    fsig = 1 + np.dot(y, cv[1:]/cv[0]-1)
    temperature = 240.
    energy = np.dot(rho, offset+cv*temperature)
    pressure = np.dot(rho, gas)*temperature
    recovered = gas[0]/cv[0]*feps/fsig*(energy-np.dot(rho, offset))
    residual = abs(recovered/pressure-1)
    ok = residual < 1e-12
    print(f'[C1] {"PASS" if ok else "FAIL"} mixture factors residual={residual:.3e}')
    return ok


def rotor(temperature, normal=False):
    j = np.arange(41, dtype=float)
    m = j*(j+1)
    odd = j % 2 == 1
    def ensemble(weight):
        weight = weight*np.exp(-87.55*m/temperature)
        weight /= sum(weight)
        mean = np.dot(weight,m)
        variance = np.dot(weight,m*m)-mean*mean
        return mean, (87.55/temperature)**2*variance
    if normal:
        even_mean, even_cv = ensemble((2*j+1)*~odd)
        odd_mean, odd_cv = ensemble((2*j+1)*odd)
        mean, capacity = .25*even_mean+.75*odd_mean, .25*even_cv+.75*odd_cv
    else:
        mean, capacity = ensemble((2*j+1)*np.where(odd,3.,1.))
    return 1.5*temperature+87.55*mean, 1.5+capacity


def check_C1_moist_mixture():
    t = sp.symbols('T', positive=True)
    a = sp.symbols('a0:8')
    cp = a[0]/t**2+a[1]/t+a[2]+a[3]*t+a[4]*t**2+a[5]*t**3+a[6]*t**4
    enthalpy = -a[0]/t+a[1]*sp.log(t)+a[2]*t+a[3]*t**2/2+a[4]*t**3/3+a[5]*t**4/4+a[6]*t**5/5+a[7]
    exact = sp.simplify(sp.diff(enthalpy-t,t)-(cp-1)) == 0
    print(f'[C1] {"PASS" if exact else "FAIL"} nine-coefficient polynomial derivative exact={exact}')
    return exact


def check_C2_moist_mixture():
    errs = []
    for normal in (False, True):
        for temp in (30., 50., 100., 300., 1000.):
            step = temp*1e-4
            derivative = (rotor(temp+step,normal)[0]-rotor(temp-step,normal)[0])/(2*step)
            errs.append(abs(derivative/rotor(temp,normal)[1]-1))
    ok = max(errs) < 2e-6
    print(f'[C2] {"PASS" if ok else "FAIL"} rotor derivative max relative={max(errs):.3e}')
    return ok


def check_C3_moist_mixture():
    # Synthetic Z(T)=1+a*T. This exercises the pressure-loop subtraction and
    # stopping condition, not a registered nonideal species or sound speed.
    # Loop: thermo_y.cpp:447-469 at the kintera pin in the module docstring.
    conc = np.maximum(np.array([2., 0.]), 1e-8)
    a, target = 1e-3, 300.
    pressure_R = conc.sum() * target * (1+a*target)
    temperature = pressure_R / conc.sum()
    converged = False
    for iteration in range(10):
        cz = 1+a*temperature
        func = temperature * (cz*conc).sum() - pressure_R
        cp_minus_cv = 1+2*a*temperature
        previous = temperature
        temperature -= func / (cp_minus_cv*conc).sum()
        if abs(1-previous/temperature) < 1e-6:
            converged = True
            break
    residual = abs(temperature-target)
    ok = converged and iteration > 0 and residual < 1e-9
    print(f'[C3] {"PASS" if ok else "FAIL"} synthetic nonlinear pressure loop: iterations={iteration+1}; temperature error={residual:.3e} K')
    return ok


def check_C1_consistency():
    rho, cv, gas, offset = mixture()
    energy = lambda t: np.dot(rho, offset+cv*t)
    values = [energy(t) for t in (100.,200.,300.)]
    intercept = values[0]-(values[1]-values[0])
    residual = abs(intercept/np.dot(rho,offset)-1)
    ok = residual < 1e-12
    print(f'[C1] {"PASS" if ok else "FAIL"} affine intercept residual={residual:.3e}')
    return ok


def check_C2_consistency():
    rho, cv, gas, offset = mixture()
    input_temperature = 240.
    internal_energy = sum(rho[n]*(offset[n]+cv[n]*input_temperature) for n in range(3))
    recovered = (internal_energy-np.dot(rho,offset))/np.dot(rho,cv)
    residual = abs(recovered-input_temperature)
    ok = residual < 1e-10
    print(f'[C2] {"PASS" if ok else "FAIL"} temperature round trip error={residual:.3e} K')
    return ok


def check_C1_saturation():
    # One mass-balanced vapor -> cloud reaction of identical molar mass.
    conc = np.array([2.,1.]); stoich = np.array([-1.,1.]); extent = .25
    updated = conc+stoich*extent
    cv = np.array([20.,30.]); offset = np.array([5000.,0.]); initial_t = 300.
    energy = np.dot(conc,offset+cv*initial_t)
    recovered_t = (energy-np.dot(updated,offset))/np.dot(updated,cv)
    residual = abs(np.dot(updated,offset+cv*recovered_t)/energy-1)
    ok = residual < 1e-12
    print(f'[C1] {"PASS" if ok else "FAIL"} fixed-energy recovery residual={residual:.3e}')
    return ok


def check_C2_saturation():
    conc = np.array([2.,1.]); stoich = np.array([-1.,1.]); extent = .25
    updated = conc+stoich*extent
    residual = abs(sum(updated)-sum(conc))
    ok = residual < 1e-12 and min(updated) > 0
    print(f'[C2] {"PASS" if ok else "FAIL"} balanced reaction mass residual={residual:.3e}')
    return ok


def illustrate_aneos():
    speed, rho, pressure = 500., 2., 1e5
    gamma = speed*speed*rho/pressure
    print(f'[I1] ILLUSTRATION effective gamma={gamma:.1f}; no external table validation')
    return True


def check_C1_shallow_water():
    # Independent inverse-map check; the square-root identity is not evidence.
    depth = np.array([1.,4.,9.])
    velocity = np.array([2.,-3.,.5])
    momentum = depth*velocity
    recovered = momentum/depth
    residual = np.max(np.abs(recovered-velocity))
    ok = residual < 1e-12
    print(f'[C1] {"PASS" if ok else "FAIL"} depth momentum round trip residual={residual:.3e}')
    return ok


def check_C2_laws():
    # Symbolic: the volume-weighted sum of the flux-only increments of six cells
    # leaves only the two boundary face products (eq-ch02-laws-increment).
    n = 6
    dt = sp.symbols('Delta_t', positive=True)
    face = sp.symbols('P0:%d' % (n + 1))
    total = sum(-dt * (face[i + 1] - face[i]) for i in range(n))
    exact = sp.simplify(total + dt * (face[n] - face[0])) == 0
    print(f'[C2] {"PASS" if exact else "FAIL"} symbolic telescoping over {n} cells exact={exact}')
    return exact


def check_C3_laws():
    # Round-off of the flux-only increment, ported in the order of
    # CoordinateImpl::divergence and HydroImpl::forward: P = A*F once per face,
    # d = P[i+1] - P[i], div = d / V, du = (-dt) * div. Seed 2.
    rng = np.random.default_rng(2)
    worst = 0.
    for _ in range(200):
        n = 32
        area = rng.uniform(.5, 2., n + 1)
        flux = rng.normal(0., 1., n + 1) * 10.**rng.uniform(-3, 3, n + 1)
        vol = rng.uniform(.5, 2., n)
        dt = float(rng.uniform(1e-3, 1.))
        face = area * flux
        du = (-dt) * ((face[1:] - face[:-1]) / vol)
        defect = sum(Q(v) * Q(d) for v, d in zip(vol, du)) + Q(dt) * (Q(face[-1]) - Q(face[0]))
        bound = 1.5 * EPS_M * dt * float(np.abs(face[1:] - face[:-1]).sum())
        worst = max(worst, abs(float(defect)) / bound)
    ok = worst <= 1.
    print(f'[C3] {"PASS" if ok else "FAIL"} conservation defect / derived bound max={worst:.3f} (200 random rows of 32 cells)')
    return ok


def check_C2_ideal_gas():
    # Symbolic: eliminating T from e = cv T and p = rho R T with R = (gamma-1) cv
    # gives p = (gamma-1) rho e; along an isentrope p = K rho**gamma,
    # dp/drho = gamma p / rho.
    rho, e, cv, g, temp, k = sp.symbols('rho e c_v gamma T K', positive=True)
    p = rho * (g - 1) * cv * temp
    first = sp.simplify(p.subs(temp, e / cv) - (g - 1) * rho * e) == 0
    q = k * rho**g
    second = sp.simplify(sp.diff(q, rho) - g * q / rho) == 0
    ok = first and second
    print(f'[C2] {"PASS" if ok else "FAIL"} symbolic pressure and isentropic sound speed exact={ok}')
    return ok


def check_C3_ideal_gas():
    # Round-off of p = (gamma-1) (E - K), ported in the order of
    # ideal_gas_cons2prim on an orthogonal cell (the raise is exact there).
    # Derived bound: |p_hat/p - 1| <= EPS_M (1 + 2 K / (rho e)). Seed 3.
    rng = np.random.default_rng(3)
    gamma = 1.4
    worst, ratio_max = 0., 0.
    for _ in range(2000):
        rho = float(10.**rng.uniform(-3, 2))
        pres = float(10.**rng.uniform(1, 6))
        mach = float(10.**rng.uniform(-2, 1.5))
        speed = mach * np.sqrt(gamma * pres / rho)
        direction = rng.normal(size=3)
        vel = speed * direction / np.linalg.norm(direction)
        mom = rho * vel
        energy = pres / (gamma - 1) + .5 * float(vel @ mom)
        v = mom / rho
        ke = .5 * (v[0] * mom[0] + v[1] * mom[1] + v[2] * mom[2])
        p_hat = (gamma - 1.) * (energy - ke)
        k_exact = sum(Q(m) * Q(m) for m in mom) / (2 * Q(rho))
        ie_exact = Q(energy) - k_exact
        p_exact = (Q(gamma) - 1) * ie_exact
        bound = EPS_M * (1. + 2. * float(k_exact / ie_exact))
        worst = max(worst, abs(float((Q(p_hat) - p_exact) / p_exact)) / bound)
        ratio_max = max(ratio_max, float(k_exact / ie_exact))
    ok = worst <= 1.
    print(f'[C3] {"PASS" if ok else "FAIL"} pressure round-off / derived bound max={worst:.3f}; K/(rho e) up to {ratio_max:.0f}')
    return ok


def check_C2_ideal_moist():
    # Symbolic: two vapours and one condensate. Sum the gas partial pressures and
    # the heat capacities of all species; divide by rho R_d T and rho c_vd.
    rho, temp, big_r = sp.symbols('rho T mathcal_R', positive=True)
    mu = sp.symbols('mu_d mu_1 mu_2', positive=True)
    cv = sp.symbols('c_vd c_v1 c_v2 c_v3', positive=True)
    y = sp.symbols('y1:4', nonnegative=True)
    yd = 1 - sum(y)
    rd = big_r / mu[0]
    pres = rho * temp * big_r * (yd / mu[0] + y[0] / mu[1] + y[1] / mu[2])
    feps = 1 + y[0] * (mu[0] / mu[1] - 1) + y[1] * (mu[0] / mu[2] - 1) - y[2]
    fsig = 1 + sum(y[n] * (cv[n + 1] / cv[0] - 1) for n in range(3))
    rho_cv = rho * (yd * cv[0] + sum(y[n] * cv[n + 1] for n in range(3)))
    first = sp.simplify(pres - rho * rd * feps * temp) == 0
    second = sp.simplify(rho_cv - rho * cv[0] * fsig) == 0
    gamma_d = 1 + rd / cv[0]
    gamma = 1 + (pres / (rho * temp)) / (rho_cv / rho)
    third = sp.simplify(gamma - (1 + (gamma_d - 1) * feps / fsig)) == 0
    ok = first and second and third
    print(f'[C2] {"PASS" if ok else "FAIL"} symbolic f_eps, f_sig and frozen gamma exact={ok}')
    return ok


def check_C3_ideal_moist():
    # Round-off of the thermal energy rho e_th = E - K - rho_d u_d - sum_n rho_n u_n,
    # ported in the order of IdealMoistImpl::_cons2prim. Derived bound:
    # |error| <= (N_y + 8) (EPS_M/2) Xi with Xi = |E| + K + sum |rho_n u_n| (dry included).
    # Seed 4; two vapours and one condensate, reference energies up to 3e6 J/kg.
    rng = np.random.default_rng(4)
    worst, lam_max = 0., 0.
    ny = 3
    for _ in range(2000):
        rho_d = float(10.**rng.uniform(-2, 1))
        rho_s = rho_d * rng.uniform(0., .1, ny)
        u0 = np.concatenate([[rng.uniform(-1e5, 1e5)], rng.uniform(-3e6, 3e6, ny)])
        rho = rho_d + rho_s.sum()
        thermal = rho * float(rng.uniform(1e4, 1e6))
        vel = rng.normal(0., 1., 3) * 10.**rng.uniform(0, 3)
        mom = rho * vel
        offs = rho_d * u0[0] + float((rho_s * u0[1:]).sum())
        energy = thermal + offs + .5 * float(vel @ mom)
        v = mom / rho
        ke = .5 * (v[0] * mom[0] + v[1] * mom[1] + v[2] * mom[2])
        ie = energy - ke
        ie = ie - rho_d * u0[0]
        ie = ie - (rho_s * u0[1:]).sum()
        rho_x = Q(rho_d) + sum(Q(r) for r in rho_s)
        k_exact = sum(Q(m) * Q(m) for m in mom) / (2 * rho_x)
        ie_exact = Q(energy) - k_exact - Q(rho_d) * Q(u0[0]) - sum(Q(r) * Q(u) for r, u in zip(rho_s, u0[1:]))
        a = abs(energy) + float(k_exact) + abs(rho_d * u0[0]) + float(np.abs(rho_s * u0[1:]).sum())
        bound = (ny + 8) * EPS_M / 2 * a
        worst = max(worst, abs(float(Q(float(ie)) - ie_exact)) / bound)
        lam_max = max(lam_max, a / abs(float(ie_exact)))
    ok = worst <= 1.
    print(f'[C3] {"PASS" if ok else "FAIL"} thermal-energy round-off / derived bound max={worst:.3f}; Xi/(rho e_th) up to {lam_max:.1f}')
    return ok


def check_C3_consistency():
    # Symbolic: dry air, two vapours, one condensate with constant capacities.
    # The per-species carried enthalpies (u* + c_v T + K/rho, plus R_n T for a gas)
    # sum to E + p, with E = W->I + K and p from the gases only.
    temp, ke = sp.symbols('T k', positive=True)  # ke: specific kinetic energy
    rho = sp.symbols('rho_d rho_1 rho_2 rho_3', positive=True)
    ustar = sp.symbols('u_d u_1 u_2 u_3', real=True)
    cv = sp.symbols('c_vd c_v1 c_v2 c_v3', positive=True)
    rg = sp.symbols('R_d R_1 R_2', positive=True)
    gas = [True, True, True, False]
    rgas = list(rg) + [0]
    carried = sum(rho[n] * (ustar[n] + cv[n] * temp + (rgas[n] * temp if gas[n] else 0) + ke) for n in range(4))
    internal = sum(rho[n] * (ustar[n] + cv[n] * temp) for n in range(4))
    energy = internal + sum(rho) * ke
    pres = sum(rho[n] * rgas[n] * temp for n in range(4))
    ok = sp.simplify(carried - (energy + pres)) == 0
    print(f'[C3] {"PASS" if ok else "FAIL"} symbolic carried enthalpy sum equals E + p exact={ok}')
    return ok


def check_C4_moist_mixture():
    # Symbolic: (a) at fixed composition c_n = rho w_n, so
    # dp/drho|_T = (R T / rho) sum_n c_n (Z_n + c_n dZ_n/dc_n) for Z_n = Z_n(c_n);
    # (b) one Newton step on rho e - U(T) is the update of eq-ch02-moist-mixture-newton.
    rho, temp, big_r = sp.symbols('rho T mathcal_R', positive=True)
    w = sp.symbols('w1:4', positive=True)
    z = [sp.Function('Z%d' % n) for n in range(1, 4)]
    conc = [rho * wn for wn in w]
    pres = big_r * temp * sum(c * zn(c) for c, zn in zip(conc, z))
    cn = sp.symbols('c1:4', positive=True)
    target = big_r * temp / rho * sum(c * (zn(c) + c * sp.diff(zn(c), c)) for c, zn in zip(cn, z))
    target = target.subs({cn[i]: conc[i] for i in range(3)})
    first = sp.simplify(sp.diff(pres, rho) - target.doit()) == 0
    t0, energy = sp.symbols('T_0 E_th', positive=True)
    u = sp.Function('U')
    newton = t0 - (u(t0) - energy) / sp.diff(u(t0), t0)
    update = t0 + (energy - u(t0)) / sp.diff(u(t0), t0)
    second = sp.simplify(newton - update) == 0
    # (c) for a quadratic U (capacities linear in T) the Newton error is exactly
    # psi_new = U'' psi_old^2 / (2 Psi(T_old)), the step-1 identity of the stopping rule.
    tr, psi, q0, q1, q2 = sp.symbols('T_r psi q0 q1 q2')
    uq = lambda t: q0 + q1 * t + q2 * t**2
    t_old = tr + psi
    t_new = t_old + (uq(tr) - uq(t_old)) / sp.diff(uq(t0), t0).subs(t0, t_old)
    third = sp.simplify((t_new - tr) - sp.diff(uq(t0), t0, 2) * psi**2 / (2 * sp.diff(uq(t0), t0).subs(t0, t_old))) == 0
    ok = first and second and third
    print(f'[C4] {"PASS" if ok else "FAIL"} symbolic isothermal sound speed, Newton update and Newton error exact={ok}')
    return ok


def check_C5_moist_mixture():
    # Stopping rule of kintera's _intEng_to_temp (thermo_y.cpp:495-517 at the kintera pin;
    # ftol 1e-6, 10 iterations), ported in its order for N species with molar energy
    # u_n(T) = u0_n + a_n T + (b_n/2) T^2, so the volumetric capacity is
    # Psi(T) = sum_n c_n (a_n + b_n T). The error left at the stop is bounded by
    #   (Upsilon/2) (ftol T / (1 - varsigma))^2                       Newton truncation
    #   + 7 N (EPS_M/2) Xi_U / Psi_min + (EPS_M/2) T + (N+2) (EPS_M/2) ftol T   rounding
    # with Upsilon = max|Psi'| / min Psi, varsigma = (Upsilon/2) |start error| < 1/2 and
    # Xi_U = |rho e| + sum_n c_n (|u0_n| + |a_n T| + |b_n T^2/2|) the magnitudes entering
    # the residual (5 roundings per u_n, 1 per product, N-1 in the sum, 1 in the
    # subtraction). The exact root solves the quadratic in mpmath at 60 digits.
    # Two decks, seed 5: energy zeros up to 1e5 and up to 1e10 J/mol.
    import mpmath as mp
    mp.mp.dps = 60
    ftol, out = 1e-6, []
    for scale in (1e5, 1e10):
        rng = np.random.default_rng(5)
        worst = 0.
        for _ in range(200):
            n = int(rng.integers(2, 7))
            conc = rng.uniform(.1, 40., n)
            a = rng.uniform(15., 60., n)
            b = rng.uniform(1e-4, 4e-2, n)
            u0 = rng.uniform(-scale, scale, n)
            target = float(rng.uniform(150., 1500.))
            energy = float(np.sum(conc * (u0 + a * target + b / 2 * target * target)))
            temp = (energy - np.sum(u0 * conc)) / np.sum(a * conc)
            start = temp
            for _it in range(10):
                prev = temp
                u = u0 + a * temp + (b * 0.5) * (temp * temp)
                temp += (energy - np.sum(u * conc)) / np.sum((a + b * temp) * conc)
                if abs(1. - prev / temp) < ftol:
                    break
            cm = [mp.mpf(float(x)) for x in conc]
            qa = sum(c * mp.mpf(float(x)) / 2 for c, x in zip(cm, b))
            qb = sum(c * mp.mpf(float(x)) for c, x in zip(cm, a))
            qc = sum(c * mp.mpf(float(x)) for c, x in zip(cm, u0)) - mp.mpf(energy)
            root = (-qb + mp.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa)
            lo, hi = min(start, float(root)), max(start, float(root))
            psi_min = float(np.sum(conc * (a + b * lo)))
            upsilon = float(np.sum(conc * b)) / psi_min
            varsigma = upsilon / 2 * abs(start - float(root))
            if not varsigma < .5:
                return print('[C5] FAIL contraction varsigma >= 1/2') or False
            xi_u = abs(energy) + float(np.sum(conc * (np.abs(u0) + a * hi + b / 2 * hi * hi)))
            bound = (upsilon / 2 * (ftol * hi / (1 - varsigma))**2
                     + 7 * n * EPS_M / 2 * xi_u / psi_min + EPS_M / 2 * hi + (n + 2) * EPS_M / 2 * ftol * hi)
            worst = max(worst, float(abs(mp.mpf(float(temp)) - root)) / bound)
        out.append(worst)
    ok = max(out) <= 1.
    print(f'[C5] {"PASS" if ok else "FAIL"} Newton stop error / derived bound max={out[0]:.3f} '
          f'(energy zeros to 1e5), {out[1]:.3f} (to 1e10); 200 random mixtures each')
    return ok


def check_C3_saturation():
    # Symbolic: differentiate the fixed-energy constraint
    # rho e = sum_n mu_n c_n e_n(T), e_n = u*_n + c_vn T (dry included), at fixed rho e.
    temp = sp.symbols('T', positive=True)
    n = 3
    c = sp.symbols('c0:%d' % n, positive=True)
    dc = sp.symbols('dc0:%d' % n, real=True)
    mu = sp.symbols('mu0:%d' % n, positive=True)
    us = sp.symbols('u0:%d' % n, real=True)
    cv = sp.symbols('cv0:%d' % n, positive=True)
    dt = sp.symbols('dT', real=True)
    e = [us[i] + cv[i] * temp for i in range(n)]
    energy = sum(mu[i] * c[i] * e[i] for i in range(n))
    differential = sum(sp.diff(energy, c[i]) * dc[i] for i in range(n)) + sp.diff(energy, temp) * dt
    solved = sp.solve(sp.Eq(differential, 0), dt)[0]
    stated = -sum(mu[i] * e[i] * dc[i] for i in range(n)) / sum(mu[i] * c[i] * cv[i] for i in range(n))
    ok = sp.simplify(solved - stated) == 0
    print(f'[C3] {"PASS" if ok else "FAIL"} symbolic fixed-energy temperature differential exact={ok}')
    return ok


def check_C2_shallow_water():
    # Symbolic: with d = g * depth stored in the IDN slot, the one-dimensional
    # shallow-water flux (d v, d v^2 + d^2/2) has eigenvalues v -+ sqrt(d).
    d, v = sp.symbols('d v', positive=True)
    q1, q2 = sp.symbols('q1 q2', positive=True)
    flux = sp.Matrix([q2, q2**2 / q1 + q1**2 / 2])
    jac = flux.jacobian([q1, q2]).subs({q1: d, q2: d * v})
    eig = sorted(jac.eigenvals().keys(), key=sp.default_sort_key)
    ok = {sp.simplify(x) for x in eig} == {v - sp.sqrt(d), v + sp.sqrt(d)}
    print(f'[C2] {"PASS" if ok else "FAIL"} symbolic gravity-wave speeds v -+ sqrt(d) exact={ok}')
    return ok
