# X2COV: the x1 covariance in the x2/x3 face energy flux (study switch)

The switch `SNAPY_X2COV=<factor>` (unset = off; the default path is unchanged bit for bit) adds
`gamma/(gamma-1) dz^2/12 p d(ln p/rho)/dz du/dz` to the energy flux of every x2 and x3 face
(`src/hydro/hydro_forward.cpp`, after the x2 and x3 Riemann calls; `u` is the face-normal velocity).
The face flux is built from x1-averaged states; the x1 average of the flux exceeds it by this term at second
order, and without it a temperature gradient acts as a spurious stable stratification
eps_spur = -(beta m^2/12) dz^2.

`x2cov_deck.py` (no input files) runs the inviscid convective box with any implicit scheme, on CPU or CUDA
(`DEVICE=cuda`):

    SNAPY_X2COV=1 python x2cov_deck.py onestep --nz 32 --scheme 9 --out on    # and with SNAPY_X2COV unset -> off
    SNAPY_X2COV=1 python x2cov_deck.py run --nz 32 --scheme 9 --eps 0.02 --nsteps 2000 --out run_cpu
    SNAPY_X2COV=1 DEVICE=cuda python x2cov_deck.py run --nz 32 --scheme 9 --eps 0.02 --nsteps 2000 --out run_gpu
    python x2cov_deck.py compare run_cpu run_gpu

Oracles: `onestep` at eps = 0: eps_eff_nz2(on) - eps_eff_nz2(off) = factor * pred_nz2 (pred is the term evaluated
independently in the driver), for scheme 0 and scheme 9 alike; `run`: finite, |d(E+PE)|/(E+PE) at round-off;
`compare`: CPU vs CUDA final states.
