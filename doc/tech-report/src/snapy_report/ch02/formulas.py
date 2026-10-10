"""Independent formula checks and an isolated pressure-loop port; no compiled solver execution.

Formulas: snapy e894700ff7aee30b52882e5202b16461413780b0;
kintera c55b13b2204997d2d09e04498558ab9495d8ee77. See chapter Code tables.
Synthetic inputs in this file are the complete decks. All arithmetic uses CPU
float64. Relative tolerance 1e-12 allows accumulated floating-point round-off
in small well-conditioned sums. Rotor central differences use 2e-6 relative:
finite-difference truncation and cancellation, not an EOS runtime tolerance.
"""
import numpy as np
import sympy as sp


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
    print(f'[C1] {"PASS" if exact else "FAIL"} NASA polynomial derivative exact={exact}')
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
