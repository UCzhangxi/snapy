# Notation for the snapy Technical Report

One symbol, one meaning, across all chapters. A chapter that needs a symbol not listed here defines it at first use
and flags it to the editor, who adds it here or picks another. Where a source note uses a different letter, the
chapter translates to this table; the "source letter" column records the common translations.

Units are SI. "per unit volume" means per m$^3$ of the cell's own measure (on spherical-polar grids that includes
the $r^2\sin\theta$ metric).

## 1. Coordinates and grids

| symbol | meaning | code | source letter |
|---|---|---|---|
| $x_1, x_2, x_3$ | the three coordinate directions; $x_1$ is always the vertical (radial) direction | x1, x2, x3 | |
| $z$ | $x_1$ on a Cartesian grid (height) [m] | `x1v`, `x1f` | |
| $r$ | $x_1$ on a spherical-polar grid (radius) [m] | `x1v`, `x1f` | |
| $\theta$ | $x_2$ on a spherical-polar grid (colatitude) [rad] | x2 | |
| $\varphi$ | $x_3$ on a spherical-polar grid (azimuth) [rad]; never the potential | x3 | $\phi$ in coord code |
| $\xi, \eta$ | the two gnomonic-equiangle panel coordinates of a cubed-sphere block ($x_2, x_3$) [rad] | | $\alpha,\beta$ |
| $i, j, k$ | cell indices in $x_1, x_2, x_3$ | `i`, `j`, `k` | |
| $i\pm\tfrac12$ | the $x_1$ faces of cell $i$; also written $f$ for a generic face | | |
| $n_1, n_2, n_3$ | interior cells per block in each direction | `nx1`, `nx2`, `nx3` | `nz` for $n_1$ |
| $n_g$ | ghost cells on each side | `nghost` | NG |
| $x_{1,i\pm1/2}$ | face positions | `x1f` | $r_\pm$, $z_\pm$ |
| $x_{1,i}$ | cell volume centroid ($r_{c,i}$ on spherical-polar) | `x1v` | $r_c$ |
| $\bar x_{1,i}$ | cell midpoint $\tfrac12(x_{1,i-1/2}+x_{1,i+1/2})$ ($\bar r_i$ on spherical-polar) | | $\bar r$ |
| $h_i$ | $x_1$ width of cell $i$, $x_{1,i+1/2}-x_{1,i-1/2}$; written $\Delta x_1$ where the direction must be explicit | `dx1f` | $\Delta z$, $h$ |
| $\delta_i$ | centroid offset $x_{1,i}-\bar x_{1,i}$ (zero on Cartesian) | | $\delta$ |
| $A_{i\pm1/2}$ | $x_1$ face area | `face_area1()` | $A_f$ |
| $V_i$ | cell volume | `cell_volume()` | |
| $\varpi_{jk}$ | solid-angle factor of a spherical-polar cell, $V = \varpi_{jk}\,\tfrac13(r_{+}^3-r_{-}^3)$ | | $\Omega(\theta,\varphi)$ |
| $\sigma_i^2$ | variance of $x_1$ about the centroid over cell $i$ on its own measure, $\langle (x_1-x_{1,i})^2\rangle_{V_i}$ | `x1_variance` | $\sigma^2$ |
| $\mathcal I$ | the interior cells of a block; $\partial\mathcal I$ its boundary faces | `interior` part | |

## 2. State, thermodynamics and species

| symbol | meaning | code | source letter |
|---|---|---|---|
| $\rho$ | total density, dry plus every species that carries mass [kg m$^{-3}$] | primitive `w[IDN]`; conserved $\sum$ `u[IDN]`+`u[ICY+n]` | |
| $\rho_d$ | dry-air density | conserved `u[IDN]` | |
| $y_n$ | mass fraction of species $n$ (vapour or condensate), $n = 1..N_y$ | primitive `w[ICY+n]` | $q_n$ |
| $\rho_n$ | partial density of species $n$, $\rho y_n$ | conserved `u[ICY+n]` | |
| $N_y$ | number of species rows | `ny` | |
| $\mathbf v = (v_1,v_2,v_3)$ | velocity [m s$^{-1}$] | `w[IVX]`, `w[IVY]`, `w[IVZ]` | $u, w$ |
| $m_1, m_2, m_3$ | momentum density $\rho v_a$ | `u[IVX]`.. | $m$ |
| $p$ | pressure [Pa] | `w[IPR]` | |
| $T$ | temperature [K] | `"W->T"` | |
| $e$ | specific internal energy [J kg$^{-1}$] | | |
| $\hat h$ | specific enthalpy $e + p/\rho$ | | $h$ (not used: $h$ is the cell width) |
| $E$ | total energy density, internal plus kinetic, $\rho e + \tfrac12\rho|\mathbf v|^2$ [J m$^{-3}$]; excludes potential energy | conserved `u[IPR]` | $E$ |
| $\mathbf U$ | conserved state vector $(\rho_d, m_1, m_2, m_3, E, \rho_1..\rho_{N_y})$ | `hydro_u`, rows `IDN, IVX, IVY, IVZ, IPR, ICY..` | |
| $\mathbf W$ | primitive state vector $(\rho, v_1, v_2, v_3, p, y_1..y_{N_y})$ | `hydro_w` | |
| $\gamma$ | ratio of specific heats (local, may vary with composition) | `gamma` | |
| $c_v, c_p$ | specific heats at constant volume and pressure | | |
| $R_d$, $R_n$ | specific gas constants of dry air and species $n$ | | $R$ |
| $\mathcal R$ | universal gas constant | | |
| $c_s$ | sound speed | `"W->L"` | $a$ |
| $p_{\rm sat}$ | saturation vapour pressure | | $e_s$ (not used: $e$ is internal energy) |
| $\chi$ | the ratio $\rho/p$ used by the default reference and its wall continuation [s$^2$ m$^{-2}$] | `rop` | $r$ (not used: $r$ is radius) |
| $\theta_p$ | potential temperature | | $\theta$ (not used: $\theta$ is colatitude) |
| $H$ | a density or pressure scale height [m] | | $H$ |

## 3. Fluxes, reconstruction and Riemann solver

| symbol | meaning | code |
|---|---|---|
| $\mathbf F_a$ | the numerical flux vector through faces normal to $x_a$ | `_flux1`, `_flux2`, `_flux3` |
| $F_{i+1/2}$ | total $x_1$ mass flux density at face $i+\tfrac12$, the sum of the dry and every mass-carrying species row [kg m$^{-2}$ s$^{-1}$] | `_flux1[IDN] + sum _flux1[ICY..]` |
| $G_{i+1/2}$ | $x_1$ mass flow through the face, $A_{i+1/2}F_{i+1/2}$ (per steradian on spherical-polar) | |
| $\mathcal F^E_{i+1/2}$ | $x_1$ energy flux density (enthalpy and kinetic energy advection, pressure work) | `_flux1[IPR]` |
| $q^{\rm L}_f, q^{\rm R}_f$ | reconstructed left and right states of a quantity $q$ at face $f$ | `wl`, `wr` |
| $q^{\pm}$ | upper/lower in $x_1$; used only for faces of one cell, $q_\pm = q_{i\pm1/2}$ | |
| $\mathcal W[\cdot]$ | the reconstruction operator (PLM, WENO5, cp3/cp5, ...) acting on cell values | `precon1`.. |
| $\mathcal K_f$ | the cp3/cp5/weno5 curvature flux, $\mathcal K_{i-1/2} = \tfrac{1}{12}(x_{1,i}-x_{1,i-1})(m_{1,i}-m_{1,i-1})$, zero at physical $x_1$ boundaries | `curv_flux1` |
| $\Lambda$ | diagonal matrix of characteristic speeds | `Lambda` |
| $\mathsf R, \mathsf R^{-1}$ | right eigenvectors and their inverse | `Rmat`, `Rimat` |

## 4. Operators and averages

| symbol | meaning |
|---|---|
| $\langle q\rangle_{V_i}$ | volume average of a function $q(x)$ over cell $i$ on its own measure, $\tfrac{1}{V_i}\int_{V_i}q\,dV$ |
| $\bar q_i$ | the cell average stored by the code, written with the bar only where a point value of the same quantity also appears |
| $q(x_{1,i})$ | point value at the centroid |
| $\Delta_i[q]$ | $x_1$ face difference over cell $i$, $q_{i+1/2}-q_{i-1/2}$; with areas, $\Delta_i[Aq] = A_{i+1/2}q_{i+1/2}-A_{i-1/2}q_{i-1/2}$ |
| $\nabla_{\!1}\!\cdot G$ | discrete $x_1$ divergence, $\Delta_i[AF]/V_i$ |
| $s_i[q]$ | centroid slope: the $x_1$ derivative at $x_{1,i}$ of the quadratic through $(x_{1,k}, q_k)$, $k\in\{i-1,i,i+1\}$ inside a block and the three cells next to the end at each $x_1$ end of a block (`centroid_slope`) |
| $\tilde s_i[q]$ | the tridiagonal (lumped) form of $s_i$ held by the implicit matrix: identical inside, the third end weight added to the neighbour's |
| $\mathsf S$ | the matrix of $s$: $(\mathsf S q)_i = s_i[q]$; $\tilde{\mathsf S}$ likewise for $\tilde s$ |
| $\operatorname{cov}_i(a,b)$ | the in-cell covariance $\langle ab\rangle_{V_i} - \langle a\rangle_{V_i}\langle b\rangle_{V_i}$; to leading order $\sigma_i^2\,\partial_1a\,\partial_1b$ |
| $\dot q$ | time derivative of a cell average produced by one operator (stated each time) |
| $[q]_{\rm walls}$ | $q$ at the top wall minus $q$ at the bottom wall |

## 5. Gravity, potential energy and gravity work

| symbol | meaning | code |
|---|---|---|
| $g_1, g_2, g_3$ | constant gravity components [m s$^{-2}$]; $g_1<0$ points to decreasing $x_1$ | `grav1`.. |
| $\phi$ | gravitational potential, $\phi(x_1) = -g_1x_1$ (increases upward); never an angle | `phi_cell`, `phi_face` |
| $\phi_i$, $\phi_{i\pm1/2}$ | $\phi$ at the centroid and at the faces | `phi_cell`, `phi_face` |
| $\alpha_{\rm nh}$ | non-hydrostatic factor in $[0,1]$: the fraction of gravity applied as a body force | `non-hydrostatic` |
| $\mathrm{PE}_d$ | discrete potential energy $\sum_iV_i\rho_i\phi_i$ | (logged `pe=` with the switch off) |
| $P$ | corrected discrete potential energy $\sum_iV_i[\rho_i\phi_i - g_1\sigma_i^2s_i[\rho]]$, exact to $O(h^4)$ | (logged `pe=` with the switch on) |
| $\mathcal P$ | the exact potential energy $\int\rho\phi\,dV$ of a smooth density field | |
| $W_i$ | $x_1$ gravity work per unit volume and time booked into $E$ in cell $i$ [W m$^{-3}$] | |
| $W^{\rm cell}_i$ | cell form $\rho_iv_{1,i}g_1$ | `original_gravity_work` |
| $W^{\rm face}_i$ | face form $\tfrac{1}{V_i}[\phi_i\Delta_i[AF]-\Delta_i[A\phi F]]$ | `face_gravity_work` |
| $W^{\rm D}_i$ | corrected-PE face work $W^{\rm face}_i + g_1\sigma_i^2s_i[\dot\rho]$ | `face_gravity_work += corrected_pe_work(...)` |
| $\mathcal D$ | the $E+\mathrm{PE}_d$ defect of a step, the quantity the gravity-work fixer removes [J] | `gravity_work_defect()` |
| $F^{\rm ref}$ | the reference-state part of the $x_1$ mass flux | `bflux1` |

## 6. Hydrostatic reference state

| symbol | meaning | code |
|---|---|---|
| $\rho_{\rm ref}, p_{\rm ref}$ | cell reference density and pressure of the well-balanced $x_1$ reconstruction | `rho_ref`, `p_ref` |
| $\rho_{\rm sf}, p_{\rm sf}$ | face ("scan face") reference density and pressure | |
| $\rho' = \rho - \rho_{\rm ref}$ | the perturbation the reconstruction acts on | |
| $\chi^s_i$ | the binomially smoothed $\chi$ of the default reference | |
| $B$ | the binomial weights $(1,4,6,4,1)/16$ | |

## 7. Time integration and the implicit solver

| symbol | meaning | code |
|---|---|---|
| $\Delta t$ | the step | `dt` |
| $t^n$ | time at step $n$ | `cycle` |
| $\mathbf U^{(s)}$ | state after RK stage $s$ | |
| $w_{0,s}, w_{1,s}, w_{2,s}$ | the stage weights: $\mathbf U \leftarrow w_0\mathbf U^n + w_1\mathbf U + w_2\Delta t\,\mathcal L(\mathbf U)$ | `wght0()`, `wght1()`, `wght2()` |
| $\mathcal L$ | the semi-discrete right-hand side (all explicit operators) | |
| $\Delta\mathbf U^{(0)}$ | the explicit stage increment handed to the implicit solve | `du0` |
| $\boldsymbol\delta_i$ | the implicit solve's unknown in cell $i$ (total mass, normal momentum, [tangential momenta], energy) | `delta` |
| $\delta\rho_i$ | the total-mass component of $\boldsymbol\delta_i$ | `delta[...][0]` |
| $\Delta\rho_i$ | the solved total density change after redistribution and clamps | `du[IDN] + sum du[ICY..]` |
| $\mathsf A_i, \mathsf B_i, \mathsf C_i$ | the diagonal, lower and upper blocks of row $i$ of the block-tridiagonal system | `_a`, `_b`, `_c` |
| $\mathsf A^{\pm}$ | the Roe dissipation matrices $\mathsf R|\Lambda|\mathsf R^{-1}$ at faces $i\pm\tfrac12$ | `Ap`, `Am` |
| $\partial\mathbf F/\partial\mathbf U$ | flux Jacobian | `dfdq_*` |
| $\mathsf\Phi$ | the gravity source Jacobian | `Phi` |
| $\omega^{\rm lo}_i, \omega^{\rm hi}_i$ | the implicit face-work weights $\tfrac12A_{i\mp1/2}|x_{1,i}-x_{1,i\mp1/2}|/V_i$ | `work_lo`, `work_hi` |
| $C$ | Courant number (named: acoustic, advective, vertical acoustic) | `cfl` |
| $\epsilon_{\rm piv}$ | LU pivot tolerance | |

## 8. Diffusion, sedimentation, forcing

| symbol | meaning |
|---|---|
| $\mu$, $\nu$ | dynamic and kinematic viscosity |
| $\kappa$ | thermal diffusivity (or conductivity, stated) |
| $K_f$ | a diffusion coefficient evaluated on face $f$ |
| $w_{{\rm s},n}$ | sedimentation (terminal) velocity of species $n$ |
| $\Omega$ | planetary rotation rate |
| $\tau$ | a relaxation time scale (named) |

## 9. Diagnostics and errors

| symbol | meaning |
|---|---|
| $\mathrm{KE}, \mathrm{IE}$ | kinetic and internal energy totals (logged `ke=`, `ie=`) |
| $\varepsilon$ | relative error of the linear convective onset growth rate against its oracle; $\varepsilon_{\rm eff}$ the one-step effective value |
| $e_\infty$, $e_1$ | max-norm and 1-norm errors (named quantity) |
| $\mathcal O$ | an oracle (exact or reference value) |

## 10. Reserved letters (do not reuse)

$h$ (cell width), $r$ (radius), $\phi$ (potential), $\varphi$ (azimuth), $\theta$ (colatitude), $e$ (specific internal
energy), $E$ (total energy density), $P$ (corrected PE), $W$ (gravity work), $\mathbf W$ (primitive vector, bold
only), $H$ (scale height), $\mathcal K$ (curvature flux), $s$ (centroid slope; RK stage index is a superscript in
parentheses), $\sigma^2$ (cell variance), $\chi$ ($\rho/p$), $\varepsilon$ (onset error).
