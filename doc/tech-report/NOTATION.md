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
| $x^{\mathrm{m}}_{1,i}$ | cell midpoint $\tfrac12(x_{1,i-1/2}+x_{1,i+1/2})$ ($r^{\mathrm{m}}_i$ on spherical-polar); it is not the cell average of $x_1$, which is the centroid $x_{1,i}$ | | $\bar r$, $\bar x_1$ |
| $h_i$ | $x_1$ width of cell $i$, $x_{1,i+1/2}-x_{1,i-1/2}$; written $\Delta x_1$ where the direction must be explicit | `dx1f` | $\Delta z$, $h$ |
| $\Delta_\pm$ | centroid spacings $x_{1,i+1}-x_{1,i}$ ($+$) and $x_{1,i}-x_{1,i-1}$ ($-$), used in non-uniform stencils; never $h_\pm$, which would read as cell widths | | $h_\pm$ |
| $l$ | stencil offset index ($\bar\rho_{i+l}$); never $k$, which is the $x_3$ index | | $k$ in figure scripts |
| $\vartheta$ | local phase $\pi h/\lambda_w$ of a wave of wavelength $\lambda_w$ in a Fourier error estimate | | |
| $\delta_i$ | centroid offset $x_{1,i}-x^{\mathrm{m}}_{1,i}$ (zero on Cartesian) | | $\delta$ |
| $A_{i\pm1/2}$ | $x_1$ face area | `face_area1()` | $A_f$ |
| $V_i$ | cell volume | `cell_volume()` | |
| $\varpi_{jk}$ | horizontal factor of a cell volume, $V_{ijk}=\varpi_{jk}V^{(1)}_i$: the solid angle on spherical-polar ($V^{(1)}_i=\tfrac13(r_{+}^3-r_{-}^3)$), $\Delta x_2\Delta x_3$ on Cartesian ($V^{(1)}_i=h_i$) | | $\Omega(\theta,\varphi)$ |
| $V^{(1)}_i$ | the $x_1$ factor of the cell volume, $V_{ijk}=\varpi_{jk}V^{(1)}_i$: $\tfrac13(x_{1,i+1/2}^3-x_{1,i-1/2}^3)$ on spherical-polar, $h_i$ on Cartesian | | |
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
| $E$ | total energy density, internal plus kinetic, $\rho e + \tfrac12\rho\lvert\mathbf v\rvert^2$ [J m$^{-3}$]; excludes potential energy | conserved `u[IPR]` | $E$ |
| $\mathbf U$ | conserved state vector $(\rho_d, m_1, m_2, m_3, E, \rho_1..\rho_{N_y})$ | `hydro_u`, rows `IDN, IVX, IVY, IVZ, IPR, ICY..` | |
| $\mathbf W$ | primitive state vector $(\rho, v_1, v_2, v_3, p, y_1..y_{N_y})$ | `hydro_w` | |
| $\gamma$ | ratio of specific heats (local, may vary with composition) | `gamma` | |
| $c_v, c_p$ | specific heats at constant volume and pressure | | |
| $R_d$, $R_n$ | specific gas constants of dry air and species $n$ | | $R$ |
| $\mathcal R$ | universal gas constant | | |
| $c_s$ | sound speed | `"W->L"` | $a$ |
| $p_{\mathrm{sat}}$ | saturation vapour pressure | | $e_s$ (not used: $e$ is internal energy) |
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
| $q^{\mathrm{L}}_f, q^{\mathrm{R}}_f$ | reconstructed left and right states of a quantity $q$ at face $f$ | `wl`, `wr` |
| $q^{\pm}$ | upper/lower in $x_1$; used only for faces of one cell, $q_\pm = q_{i\pm1/2}$ | |
| $\mathcal W[\cdot]$ | the reconstruction operator (PLM, WENO5, cp3/cp5, ...) acting on cell values | `precon1`.. |
| $\mathcal K_f$ | the cp3/cp5/weno5 curvature flux, $\mathcal K_{i-1/2} = \tfrac{1}{12}(x_{1,i}-x_{1,i-1})(m_{1,i}-m_{1,i-1})$, zero at physical $x_1$ boundaries | `curv_flux1` |
| $\Lambda$ | diagonal matrix of characteristic speeds | `Lambda` |
| $\mathsf R, \mathsf R^{-1}$ | right eigenvectors and their inverse | `Rmat`, `Rimat` |

## 4. Operators and averages

| symbol | meaning |
|---|---|
| $\langle q\rangle_{V_i}$ | volume average of a function $q(x)$ over cell $i$ on its own measure, $\tfrac{1}{V_i}\int_{V_i}q\,dV$ |
| $\bar q_i$ | the cell average stored by the code, written with the bar only where a point value of the same quantity also appears. The overbar means the cell average and nothing else: a midpoint, a reference or a background value never carries a bar |
| $q(x_{1,i})$ | point value at the centroid |
| $\Delta_i[q]$ | $x_1$ face difference over cell $i$, $q_{i+1/2}-q_{i-1/2}$; with areas, $\Delta_i[Aq] = A_{i+1/2}q_{i+1/2}-A_{i-1/2}q_{i-1/2}$ |
| $\nabla_{\!1}\!\cdot G$ | discrete $x_1$ divergence, $\Delta_i[AF]/V_i$ |
| $\mathcal N_i$ | the stencil set of the centroid slope of cell $i$ (stencil cells indexed by $l$) |
| $s_i[q]$ | centroid slope: the $x_1$ derivative at $x_{1,i}$ of the quadratic through $(x_{1,k}, q_k)$, $k\in\{i-1,i,i+1\}$ inside a block and the three cells next to the end at each $x_1$ end of a block (`centroid_slope`) |
| $\tilde s_i[q]$ | the tridiagonal (lumped) form of $s_i$ held by the implicit matrix: identical inside, the third end weight added to the neighbour's |
| $\mathsf S$ | the matrix of $s$: $(\mathsf S q)_i = s_i[q] = \sum_l\mathsf S_{il}q_l$ (row $i$: the weights of the cells $l$ in the slope of $i$; the code stores the transpose); $\tilde{\mathsf S}$ likewise for $\tilde s$ |
| $\operatorname{cov}_i(a,b)$ | the in-cell covariance $\langle ab\rangle_{V_i} - \langle a\rangle_{V_i}\langle b\rangle_{V_i}$; to leading order $\sigma_i^2\,\partial_1a\,\partial_1b$ |
| $\dot q$ | time derivative of a cell average produced by one operator (stated each time) |
| $[q]_{\mathrm{walls}}$ | $q$ at the top wall minus $q$ at the bottom wall |
| $\partial_1 q$, $\partial_1^2 q$, $\partial_1^3 q$ | derivatives of a smooth field $q(x_1)$ with respect to $x_1$, evaluated where stated; a prime is never used for a derivative, because $\rho'$ is the reference perturbation (§6) |

## 5. Gravity, potential energy and gravity work

| symbol | meaning | code |
|---|---|---|
| $g_1, g_2, g_3$ | constant gravity components [m s$^{-2}$]; $g_1<0$ points to decreasing $x_1$ | `grav1`.. |
| $\phi$ | gravitational potential, $\phi(x_1) = -g_1x_1$ (increases upward); never an angle | `phi_cell`, `phi_face` |
| $\phi_i$, $\phi_{i\pm1/2}$ | $\phi$ at the centroid and at the faces | `phi_cell`, `phi_face` |
| $\alpha_{\mathrm{nh}}$ | non-hydrostatic factor in $[0,1]$: the fraction of gravity applied as a body force | `non-hydrostatic` |
| $\mathrm{PE}_d$ | discrete potential energy $\sum_iV_i\rho_i\phi_i$ | (logged `pe=` with the switch off) |
| $P$ | corrected discrete potential energy $\sum_iV_i[\rho_i\phi_i - g_1\sigma_i^2s_i[\rho]]$, exact to $O(h^4)$ | (logged `pe=` with the switch on) |
| $\mathcal P$ | the exact potential energy $\int\rho\phi\,dV$ of a smooth density field | |
| $W_i$ | $x_1$ gravity work per unit volume and time booked into $E$ in cell $i$ [W m$^{-3}$] | |
| $W^{\mathrm{cell}}_i$ | cell form $\rho_iv_{1,i}g_1$ | `original_gravity_work` |
| $W^{\mathrm{face}}_i$ | face form $\tfrac{1}{V_i}[\phi_i\Delta_i[AF]-\Delta_i[A\phi F]]$ | `face_gravity_work` |
| $W^{\mathrm{D}}_i$ | corrected-PE face work $W^{\mathrm{face}}_i + g_1\sigma_i^2s_i[\dot\rho]$ | `face_gravity_work += corrected_pe_work(...)` |
| $W^{\mathrm{wallc}}_i$ | the `face-wallc` work: $W^{\mathrm{face}}_i$ in interior cells, $W^{\mathrm{cell}}_i$ in the two $x_1$ wall cells | |
| $\mathcal E$ | the conserved energy functional of a scheme, named each time ($\mathcal E = \sum_iV_iE_i+P$ under D, $\sum_iV_iE_i+\mathrm{PE}_d$ under the plain face form) | (logged `ie=` + `pe=`) |
| $M$, $M_{\mathrm{wall}}$ | total mass of the domain, and total mass of the $x_1$ wall cells | |
| $\mathcal D$ | the $E+\mathrm{PE}_d$ defect of a step, the quantity the gravity-work fixer removes [J] | `gravity_work_defect()` |
| $F^{\mathrm{ref}}$ | the reference-state part of the $x_1$ mass flux | `bflux1` |

## 6. Hydrostatic reference state

| symbol | meaning | code |
|---|---|---|
| $\rho_{\mathrm{ref}}, p_{\mathrm{ref}}$ | cell reference density and pressure of the well-balanced $x_1$ reconstruction | `rho_ref`, `p_ref` |
| $\rho_{\mathrm{sf}}, p_{\mathrm{sf}}$ | face ("scan face") reference density and pressure | |
| $\rho' = \rho - \rho_{\mathrm{ref}}$ | the perturbation the reconstruction acts on; the prime means "minus the reference", never a derivative | |
| $\chi^s_i$ | the binomially smoothed $\chi$ of the default reference | |
| $B$ | the binomial weights $(1,4,6,4,1)/16$ | |

## 7. Time integration and the implicit solver

| symbol | meaning | code |
|---|---|---|
| $\Delta t$ | the step | `dt` |
| $\Delta q$ | the change of $q$ over one RK stage, stated each time as "per stage" or "per step"; on a state variable in an implicit context write $\Delta^{\mathrm{stg}}\rho$ for the stage change and keep $\Delta\rho_i$ for the solved change of the row below | |
| $t^n$ | time at step $n$ | `cycle` |
| $\mathbf U^{(s)}$ | state after RK stage $s$ | |
| $w_0^{(s)}, w_1^{(s)}, w_2^{(s)}$ | the weights of RK stage $s$: $\mathbf U \leftarrow w_0^{(s)}\mathbf U^n + w_1^{(s)}\mathbf U + w_2^{(s)}\Delta t\,\mathcal L(\mathbf U)$ | `wght0()`, `wght1()`, `wght2()` |
| $\mathcal L$ | the semi-discrete right-hand side (all explicit operators) | |
| $\Delta\mathbf U^{(0)}$ | the explicit stage increment handed to the implicit solve | `du0` |
| $\Delta t_c$ | the time step handed to the implicit solve: $w_{2,s}\Delta t$ under rk3, $\Delta t$ otherwise | `dt_corr` |
| $\boldsymbol\delta_i$ | the implicit solve's unknown in cell $i$ (total mass, normal momentum, [tangential momenta], energy) | `delta` |
| $\delta\rho_i$, $\delta E_i$ | the total-mass and energy components of $\boldsymbol\delta_i$ | `delta[...][0]`, `delta[...][m-1]` |
| $\Delta\rho_i$ | the total density change solved by the implicit step, after redistribution and clamps; never the plain stage change, which is $\Delta^{\mathrm{stg}}\rho_i$ | `du[IDN] + sum du[ICY..]` |
| $\mathsf A_i, \mathsf B_i, \mathsf C_i$ | the diagonal, lower and upper blocks of row $i$ of the block-tridiagonal system | `_a`, `_b`, `_c` |
| $\mathsf A^{\pm}$ | the Roe dissipation matrices $\mathsf R\lvert\Lambda\rvert\mathsf R^{-1}$ at faces $i\pm\tfrac12$ | `Ap`, `Am` |
| $\partial\mathbf F/\partial\mathbf U$ | flux Jacobian | `dfdq_*` |
| $\mathsf\Phi$ | the gravity source Jacobian | `Phi` |
| $\omega^{\mathrm{lo}}_i, \omega^{\mathrm{hi}}_i$ | the implicit face-work weights $\tfrac12A_{i\mp1/2}\lvert x_{1,i}-x_{1,i\mp1/2}\rvert/V_i$ | `work_lo`, `work_hi` |
| $C$ | Courant number (named: acoustic, advective, vertical acoustic) | `cfl` |
| $\epsilon_{\mathrm{piv}}$ | LU pivot tolerance | |
| $\epsilon_{\mathrm{m}}$ | machine epsilon of the working precision (never bare $\epsilon$, which is $\epsilon_{\mathrm{piv}}$) | |
| $\mathsf I$ | the identity matrix, sized by context | |

## 8. Diffusion, sedimentation, forcing

| symbol | meaning |
|---|---|
| $\mu$, $\nu$ | dynamic and kinematic viscosity |
| $\kappa$ | thermal diffusivity (or conductivity, stated) |
| $K_f$ | a diffusion coefficient evaluated on face $f$ |
| $w_{{\mathrm{s}},n}$ | sedimentation (terminal) velocity of species $n$ |
| $\Omega$ | planetary rotation rate |
| $\tau$ | a relaxation time scale (named) |

## 8a. Radiation and the radiating boundary

snapy itself contains no radiative transfer (chapter 1.13, Appendix E). These symbols are for the radiating
characteristic boundary (chapter 11.5), the external radiative time-step limiter (Appendix E) and any
reference to pyharp or pydisort.

| symbol | meaning | code |
|---|---|---|
| $\kappa_{\mathrm{R}}$ | mean opacity [m$^2$ kg$^{-1}$]; never bare $\kappa$, which is thermal diffusivity (§8) | |
| $\sigma_{\mathrm{SB}}$ | Stefan-Boltzmann constant; never bare $\sigma$, which is the cell variance (§1) | |
| $\varepsilon_{\mathrm{esc}}$ | escape probability of the time-step limiter; never bare $\varepsilon$, which is the onset error (§9) | |
| $\tau_{\mathrm{rad}}$ | radiative relaxation time, $c_v/(16\kappa_{\mathrm{R}}\sigma_{\mathrm{SB}}T^3\varepsilon_{\mathrm{esc}})$; never bare $\tau$ (§8) | |
| $q_{\mathrm{bg}}$ | the saved background value of a primitive $q$ at a radiating boundary | `boundary_reference_w`, `_r` |
| $d_q = q_i - q_{\mathrm{bg},i}$ | the interior perturbation the characteristic split acts on; $d$ always carries the quantity it belongs to, because bare $d$ is not used (STYLE.md §5) | |
| $Z = \rho_{\mathrm{bg}}c_{s,\mathrm{bg}}$ | the background acoustic impedance | |
| $\alpha_{\mathrm{adm}}$ | the admissibility factor in $[0,1]$ that scales a radiating ghost toward the background; never bare $\alpha$ | |

## 9. Diagnostics and errors

| symbol | meaning |
|---|---|
| $\mathrm{KE}, \mathrm{IE}$ | kinetic and internal energy totals (logged `ke=`, `ie=`) |
| $\varepsilon$ | relative error of the linear convective onset growth rate against its oracle; $\varepsilon_{\mathrm{eff}}$ the one-step effective value |
| $e_\infty$, $e_1$ | max-norm and 1-norm errors (named quantity) |
| $\mathcal O$ | an oracle (exact or reference value) |
| $\lambda_w$ | a wavelength (named) |

## 10. Reserved letters (do not reuse)

$h$ (cell width), $k$ (x3 index; stencil cells use $l$), $\kappa$ (diffusivity; never a wavenumber), $r$ (radius), $\phi$ (potential), $\varphi$ (azimuth), $\theta$ (colatitude), $e$ (specific internal
energy), $E$ (total energy density), $P$ (corrected PE), $W$ (gravity work), $\mathbf W$ (primitive vector, bold
only), $H$ (scale height), $\mathcal K$ (curvature flux), $s$ (centroid slope), $\sigma^2$ (cell variance),
$\chi$ ($\rho/p$), $\varepsilon$ (onset error), $\rho'$ (reference perturbation).

- The prime is never a derivative. $\rho'$ is the reference perturbation of §6; an $x_1$ derivative is
  $\partial_1\rho$ (§4).
- The RK stage index is always a superscript in parentheses, $(s)$, on the quantity *and* on its weights; it is
  never a subscript, and a second stage index is $(s')$, never $t$, which is time.
- $\delta$ is reserved three ways and never used otherwise: $\delta_i$ with a cell subscript is the centroid
  offset (§1); $\boldsymbol\delta_i$ in bold is the implicit solve's unknown vector (§7); $\delta$ as a prefix
  on a state variable ($\delta\rho_i$, $\delta E_i$) is a component of that vector. Bare $\delta$ with no
  subscript, no bold and no operand is never written. A general small quantity is $\eta$ — not $\delta$, and not
  $\epsilon$ or $\varepsilon$ (both reserved, §7 and §9).
- $O(\cdot)$, upright-weight italic capital O, is always the Landau order symbol. $\mathcal O$, calligraphic, is
  always an oracle (§9). Never write $\mathcal O$ for an order, and never write $O$ for an oracle. Where a
  sentence uses both, name the oracle ($\mathcal O_{\mathrm{EVP}}$).
- $\kappa$ is the thermal diffusivity, never an opacity (use $\kappa_{\mathrm{R}}$, §8a) and never a wavenumber.
  $\sigma$ is the cell variance, never the Stefan-Boltzmann constant ($\sigma_{\mathrm{SB}}$, §8a).
  $\varepsilon$ is the onset error, never an escape probability ($\varepsilon_{\mathrm{esc}}$, §8a) and never a
  general small number. $\tau$ is a named relaxation time, never an optical depth — write $\tau_\nu$ with the
  frequency subscript if an optical depth is ever needed. $\alpha$ is always subscripted, and $d$ is always
  subscripted.
