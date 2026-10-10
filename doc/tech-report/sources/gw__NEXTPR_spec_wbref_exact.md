> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Fourth-order well-balanced x1 reference (`SNAPY_WB_REF_EXACT`): specification and derivation

Text-only specification for an independent implementation (snapy #289). It is taken from the derivation on a local #289 branch (file `src/hydro/DERIVATION_wb_ref_exact.md`, blob `1353796c7cdb6f32e4a578fba3f0792d42595631` at commit `c5b810d2db585d7902fb8c0234d1cec1725039d1`). Code, implementation details and line references into the new implementation are removed.

References to existing snapy code are to the base, main `117e449a620bd7fd50abe19239ab660a56d5d4cb`, and are given by routine name only.

## 0. Notation

- $z \equiv x_1$ (vertical, gravity $g$ downward). Cell $i$ spans $[z_{i-1/2}, z_{i+1/2}]$, with width $\Delta z_i$ (uniform $\Delta z$ unless stated). Face $f$ is the lower face of cell $f$.
- Ideal gas with $R_d = 1$: $T = p/\rho$, $R \equiv \rho/p = 1/T$, $\kappa = \gamma/(\gamma-1)$.
- An overbar is a cell average, and $q_f$ is a point value at a face.
- $\mathcal I[\cdot]_f$ is the face value implied by a set of cell averages, i.e. what a high-order reconstruction (WENO5) returns for smooth data, to $O(\Delta z^5)$.
- $\mathcal I_4[\cdot]_f$ is a fourth-order face value from cell averages (defined in §4.2).

## 1. The existing well-balanced x1 reconstruction (base behaviour)

Per column, the base builds a hydrostatic reference (`_hydro_ref_x1`, kernel `hydro_ref_x1_impl.h`). It reconstructs perturbations and restores the reference at faces:

1. Cell perturbations: $p' = \bar p - p_{\rm ref}$ and $\rho' = \bar\rho - \rho_{\rm ref}$.
2. Wall ghosts of $p', \rho'$ are filled with even parity at physical x1 walls.
3. $p', \rho'$ are reconstructed (WENO5) to faces, giving $\widehat{p'}^{L,R}_f$ and $\widehat{\rho'}^{L,R}_f$.
4. The face references are restored:
$$p^{L,R}_f = \widehat{p'}^{L,R}_f + p_{{\rm sf},f},\qquad \rho^{L,R}_f = \widehat{\rho'}^{L,R}_f + \rho_{{\rm sf},f}.$$

The reference has three parts.

**(a) Face pressures (hydrostatic scan).** From a top anchor, scanning down:
$$p_{{\rm sf},i-1/2} = p_{{\rm sf},i+1/2} + g\,\bar\rho_i\,\Delta z_i .$$
This is the discrete hydrostatic balance itself. At rest $p' = $ const, so the face pressures equal $p_{\rm sf}$ and the momentum-flux difference across cell $i$ is exactly $g\bar\rho_i\Delta z_i$.

**(b) Cell pressure $p_{\rm ref}$.**
- On a uniform grid: six-face quadrature, i.e. the cell average of the quintic through six face pressures, with one-sided rows at walls and a $[\min,\max]$ guard against the cell's two face values. The weights are
  - interior: $(11, -93, 802, 802, -93, 11)/1440$;
  - wall rows: $(475, 1427, -798, 482, -173, 27)/1440$ and $(-27, 637, 1022, -258, 77, -11)/1440$.
- On a non-uniform grid: the log-mean $\Delta p/\ln(p_{\rm lo}/p_{\rm hi})$, which is exact only for an isothermal cell.
- The choice is made from grid uniformity (relative spread of $\Delta z$ below $10^{-10}$).

**(c) Density reference.**
- $r_i = \bar\rho_i/\bar p_i$ is smoothed by the clamped binomial $B = (1,4,6,4,1)/16$, giving $r^s_i$. At a clamped wall the stencil index is clamped, which replicates the edge cell.
- Cell reference: $\rho_{{\rm ref},i} = p_{{\rm ref},i}\,r^s_i$.
- Face reference: $\rho_{{\rm sf},f} = p_{{\rm sf},f}\,\tfrac12\big(r^s_{f-1} + r^s_f\big)$.

## 2. The O(Δz²) face-density offset of the base reference

The reconstruction treats $\rho'$ as cell averages, so the face density is
$$\rho_f = \mathcal I[\bar\rho]_f + \delta\rho_f,\qquad \delta\rho_f \equiv \rho_{{\rm sf},f} - \mathcal I[\rho_{\rm ref}]_f .$$
For a consistent scheme $\delta\rho_f$ must vanish to the scheme's order. Take smooth $\rho(z)$, $p(z)$ and $R = \rho/p$, and use $\bar q = q + \tfrac{\Delta z^2}{24}q'' + O(\Delta z^4)$:

1. **Ratio of averages.** $r_i = R_i + \tfrac{\Delta z^2}{24}\,(\rho'' - R p'')/p$.
2. **Binomial bias.** $B$ has unit sum and second moment $\sum_m m^2 w_m = 1$ (cells), so $Bq = q + \tfrac{\Delta z^2}{2}q'' + O(\Delta z^4)$. Hence $r^s_i = r_i + \tfrac{\Delta z^2}{2}R''$.
3. **Cell reference.** Taking $p_{\rm ref} = \bar p$ to high order (see Open points):
$\rho_{{\rm ref},i} = \big(p + \tfrac{\Delta z^2}{24}p''\big)\big(R + \tfrac{\Delta z^2}{24}\tfrac{\rho''-Rp''}{p} + \tfrac{\Delta z^2}{2}R''\big) = \bar\rho_i + \tfrac{\Delta z^2}{2}pR'' + O(\Delta z^4)$.
As cell averages this is $D = \rho + \tfrac{\Delta z^2}{2}pR''$, so $\mathcal I[\rho_{\rm ref}]_f = \rho_f + \tfrac{\Delta z^2}{2}pR''$.
4. **Face reference.** The mean of two cell values adds $\tfrac{\Delta z^2}{8}R''$:
$\rho_{{\rm sf},f} = p_f\big[R_f + \tfrac{\Delta z^2}{24}\tfrac{\rho''-Rp''}{p} + \tfrac{\Delta z^2}{8}R'' + \tfrac{\Delta z^2}{2}R''\big]$.
5. **Subtract**, using $\rho'' - Rp'' = (pR)'' - Rp'' = 2p'R' + pR''$:
$$\boxed{\;\delta\rho_f = \frac{\Delta z^2}{12}\big(p'R' + 2\,p\,R''\big) + O(\Delta z^4)\;}$$

**Example.** For a neutral polytrope, $p = T^{m+1}$ and $R = 1/T$ with $T' = -1$ (units $R_d = 1$, $g = m+1$). This gives $\delta\rho_f/\rho_f = \Delta z^2/(8T^2) > 0$: the face density is too high, most at the top. A direct numerical replica of the base reference agrees with the closed form to a ratio of 1.0001 to 1.0005 at nz 256, converging like $\Delta z^2$.

**Wall layer.** At a clamped wall, edge replication in $B$ is not exact even for linear $r$, so in the first two cells the offset is $O(\Delta z)$. Measured relative face offsets on a 1 H column at the bottom wall are 5.96e-4 / 2.96e-4 / 1.48e-4 / 7.39e-5 (nz 32 to 256), against $O(\Delta z^2)$ mid-column. This wall layer comes on top of the interior $O(\Delta z^2)$ offset.

## 3. Where the reference enters the dynamics

- **Cell references** $p_{\rm ref}, \rho_{\rm ref}$ are used only inside the x1 reconstruction; the primitives are restored afterwards.
- **Face pressure** $p_{\rm sf}$ enters the x1 Riemann (LMARS) face pressure $\bar p$ and velocity $\bar u$, hence the x1 momentum flux and the face pressure. It is the balanced quantity and must not change.
- **Face density** $\rho_{\rm sf}$, hence $\delta\rho_f$, enters only the **x1 mass flux** $\bar u\,\rho_{L/R}$ at linear order. In LMARS:
  - the energy flux is $\bar u\,\rho h$ with $\rho h = \kappa p + \rho K$, which is independent of the face density at linear order ($K$ is quadratic);
  - the momentum flux $\bar u\rho u_1$ is quadratic;
  - $\bar u$ and $\bar p$ see $\rho$ only through $\bar\rho\bar c$ multiplying the reconstruction jumps $u_L - u_R$ and $p_L - p_R$, which are negligible for a smooth mode.
- **Gravity work.** In the `face` / `face-wallc` gravity-work forms the full x1 mass flux is booked, so $\delta F_\rho$ also enters the energy, at $-\tfrac g2(\delta F_{\rho,i-1/2} + \delta F_{\rho,i+1/2})$ per unit time. In the `cell` form only $F - F^R$ is booked, and $\delta F_\rho$ belongs to the Riemann flux $F^R$, so the offset enters through the mass flux only.
- **x2 and x3 faces** use the restored primitives with no reference. The offset does **not** enter the x2 energy flux. The x2 energy-flux covariance ΔF (#289's main term) is a separate term, and the two add.

**One-step tendency (linear, at rest background).** With $\delta F_{\rho,f} = \delta\rho_f\,w_f$, $s = \ln(p\rho^{-\gamma})$ and $\partial_t p = (\gamma-1)\partial_t E$:
$$\partial_t s_i = -\chi\,\frac{(\gamma-1)g}{2p_i}\big(\delta F_{\rho,i-1/2} + \delta F_{\rho,i+1/2}\big) + \frac{\gamma}{\rho_i}\,\frac{\delta F_{\rho,i+1/2} - \delta F_{\rho,i-1/2}}{\Delta z},\qquad \chi = 1\ (\text{face}),\ 0\ (\text{cell}).$$
The continuum limit is $\partial_t s = -\chi(\gamma-1)g\,\delta\rho\,w/p + \gamma\,\partial_z(\delta\rho\,w)/\rho$.

The diagnostic used in the oracle is the effective buoyancy frequency of a seeded overturning mode, $N^2_{\rm eff} = \tfrac{g}{\gamma}\sum V(-\partial_t s\,w)/\sum V w^2$. Its exact value on a neutral column is 0.

## 4. The fix

The face pressures $p_{\rm sf}$ (the scan) are never changed. Everything below is applied after the base reference has been built. It is opt-in behind a switch that is off by default; with the switch off nothing is added and the result is bitwise base.

### 4.1 Cell reference density, fourth order

$$\rho_{{\rm ref},i} = p_{{\rm ref},i}\;(F r)_i,\qquad F = \tfrac{1}{16}(-1, 4, 10, 4, -1).$$

Properties of $F$ (in cell-index units):
- unit sum;
- second moment $\sum m^2 w_m = (2\cdot4 - 2\cdot4)/16 = 0$, so the bias is $O(\Delta z^4)$;
- grid-scale (Nyquist) response $(10 - 8 - 2)/16 = 0$, so it still removes the grid mode, as $B$ does;
- reach $\pm2$, the same as $B$, so the ghost depth and the x1 seam reference exchange are unchanged.

At a **clamped physical wall** the two values beyond the wall are not edge replicas. They are cubic extrapolations, in cell index, of the first (last) four owned cells, which is exact for a cubic. With $r_0..r_3$ the four owned cells from the wall inward, the values at index $-1$ and $-2$ are $4r_0 - 6r_1 + 4r_2 - r_3$ and $10r_0 - 20r_1 + 15r_2 - 4r_3$.

Elsewhere, at seams and non-clamped sides, the array's own (exchanged) values are read. Beyond the array the deepest ghosts replicate the edge, as in the base.

Result: $\rho_{\rm ref} = \bar\rho + O(\Delta z^4)$ up to the wall, and $\rho' = O(\Delta z^4)$.

### 4.2 Face reference density, fourth order and consistent with the cell reference

$$\rho_{{\rm sf},f} = \mathcal I_4[\rho_{\rm ref}]_f \equiv P'(z_f),$$

where $P$ is the quartic through the primitive values $P(z_{s+j}) = \sum_{k<j}\rho_{{\rm ref},s+k}\,\Delta z_{s+k}$, $j = 0..4$. That is, five faces enclose four cells, with window $s = f-2$. The window is clamped so that it stays inside the owned cells at a clamped wall.

This is fourth order on any grid. On a uniform grid in the interior it reduces to
$$\rho_{{\rm sf},f} = \tfrac{1}{12}\big(-\rho_{{\rm ref},f-2} + 7\rho_{{\rm ref},f-1} + 7\rho_{{\rm ref},f} - \rho_{{\rm ref},f+1}\big).$$
Then $\delta\rho_f = \mathcal I_4[\rho_{\rm ref}]_f - \mathcal I[\rho_{\rm ref}]_f = O(\Delta z^4)$.

**Ordering.** The face density must be formed **after** the x1 seam ghost-row exchange of the cell references, so that a column split along x1 gives the same faces as one block. The cell part (§4.1, and §4.3 below) is done **before** that exchange, so the exchanged ghost rows carry the new cell references.

### 4.3 Cell pressure on non-uniform grids only

On a uniform grid the six-face $p_{\rm ref}$ is kept as it is. On a non-uniform grid the log-mean is replaced by the cell average of the cubic through four face pressures, faces $i-1$ to $i+2$, with the window clamped inside the owned faces at a clamped wall. The average is evaluated by three-point Gauss-Legendre, which is exact for a cubic. The base $[\min,\max]$ guard against the cell's two face pressures is kept.

### 4.4 Guards (fall back to the base reference value)

They are inactive on a resolved smooth column.

1. **Range, cells.** If $(Fr)_i$ lies outside $[\min,\max]$ of $r$ over cells $i-1, i, i+1$ (indices clamped to owned cells at a clamped wall), with a relative margin of $10^{-10}$, keep the base $r^s_i$.
2. **Range, faces.** If $\mathcal I_4[\rho_{\rm ref}]_f$ lies outside $[\min,\max]$ of the two adjacent cell references, with the same $10^{-10}$ margin, keep the base $\rho_{{\rm sf},f}$.
3. **Resolution.** Flag a cell when $|\ln(p_{{\rm sf},i-1/2}/p_{{\rm sf},i+1/2})| > 0.5$, i.e. $\Delta z/H_p > 0.5$, fewer than two cells per pressure scale height. Dilate the flag by $\pm2$ cells. Flagged cells keep the base $r^s$ (and on non-uniform grids the base $p_{\rm ref}$); faces next to a flagged cell keep the base $\rho_{\rm sf}$.
4. **Owned cells only.** On a clamped side, ghost cells beyond the wall do not count for the resolution flag. They are not read by the clamped stencils, and their scan pressure falls steeply past a top wall, which would otherwise flag the top owned cells at coarse resolution.

The $10^{-10}$ margin is needed because on a flat profile the bounds coincide. An exact test would flip on round-off between a block-split and a one-block column.

### 4.5 Why exact discrete balance is kept

The balance is the scan relation of §1(a) together with $p' = $ const at rest. The fix changes neither $p_{\rm sf}$ nor how faces are restored.
- **Uniform grid:** $p_{\rm ref}$ is unchanged, so the discrete rest state $\bar p = p_{\rm ref} + c$ is identical to the base. At exact rest the density faces carry no flux ($\bar u = 0$, $\bar p = p_{\rm sf}$).
- **Non-uniform grid:** $p_{\rm ref}$ changes, so the discrete fixed point moves by $O(\Delta z^2)$. It is still a fixed point. Any column-balancing utility has to use the same switched reference to find it.

No obstruction was found between fourth-order faces and exact discrete balance.

## 5. Expected oracles

1. **Switch off:** bitwise identical to the base build in every output.
2. **Rest state.** With a discretely balanced initial state, max|v| after 1000 steps stays at round-off with the switch, on a neutral polytrope and on an isothermal column (wall clamp on). Measured, base vs switch:
   - polytrope: 7.2e-15 vs 1.2e-14;
   - isothermal: 2.525267e-15 for both;
   - log-mean (non-uniform) grid: 1.7e-14 vs 9.0e-15.

   With the wall clamp off the base itself is not at rest; the switch then matches base to about $10^{-3}$ relative.
3. **Residual.** This is a one-step $\epsilon = 0$ tendency of a seeded overturning mode on a neutral polytrope (T4 family, depth set in pressure e-folds $\ln(p_b/p_t)$), with the x2 flux covariance ΔF on, a **cell-average** initial condition, face gravity work and amplitude $10^{-4}$. Values are $N^2_{\rm eff}\,n_z^2$; $p$ is the observed order of $|N^2_{\rm eff}|$ between successive resolutions.

   | depth | base, nz 64 / 128 / 256 | $p$ base | switch, nz 64 / 128 / 256 | $p$ switch |
   |---|---|---|---|---|
   | 1 $H_p$ | +0.109 / +0.087 / +0.076 | 2.32, 2.21 | −0.071 / −0.036 / −0.018 | 2.98, 2.99 |
   | 2 $H_p$ | +0.290 / +0.265 / +0.248 | 2.13, 2.09 | −0.119 / −0.061 / −0.031 | 2.97, 2.98 |
   | 3 $H_p$ | +0.578 / +0.557 / +0.532 | 2.05, 2.07 | −0.235 / −0.122 / −0.062 | 2.95, 2.97 |
   | 5 $H_p$ | +1.458 / +1.702 / +1.699 | 1.78, 2.00 | −1.046 / −0.580 / −0.305 | 2.85, 2.93 |

   With the switch, residual·nz² → 0, falling like $\Delta z$ (order of $N^2$ about 3). The base tends to a constant: a second $O(\Delta z^2)$ term that grows with depth.

   Base − switch against the closed-form prediction (§3 tendency with the §2 offset, all faces including the wall rows, evaluated numerically):

   | depth | measured, nz 64 / 128 / 256 | predicted |
   |---|---|---|
   | 1 $H_p$ | +0.180 / +0.123 / +0.094 | +0.182 / +0.125 / +0.095 |
   | 2 $H_p$ | +0.409 / +0.326 / +0.279 | +0.405 / +0.327 / +0.280 |
   | 3 $H_p$ | +0.813 / +0.679 / +0.594 | +0.786 / +0.674 / +0.595 |
   | 5 $H_p$ | +2.504 / +2.282 / +2.003 | +2.283 / +2.195 / +1.982 |

   With the switch on and ΔF off, $N^2_{\rm eff}n_z^2$ at nz 256 is 1.77 / 1.73 / 1.90 / 3.08. That is the ΔF-only spurious stratification, which ΔF removes.
4. **Wall layer versus interior.** "Band" means the 3 cells at each wall, "interior" the rest; $N^2_{\rm eff}n_z^2$ at nz 32 / 64 / 128 / 256, ΔF on, face gravity work, cell-average IC.

   | case | band | $p$ band | interior | $p$ interior |
   |---|---|---|---|---|
   | 1 $H_p$ base | +0.095 / +0.050 / +0.025 / +0.013 | 2.99, 3.00 | +0.051 / +0.060 / +0.062 / +0.063 | 1.94, 1.98 |
   | 1 $H_p$ switch | −0.142 / −0.072 / −0.036 / −0.018 | 2.99, 3.00 | +0.0039 / +0.0010 / +0.0003 / +0.0001 | 3.99, 3.97 |
   | 5 $H_p$ base | +0.251 / +0.549 / +0.393 / +0.218 | 2.48, 2.85 | +0.289 / +0.909 / +1.309 / +1.481 | 1.47, 1.82 |
   | 5 $H_p$ switch | −1.685 / −1.035 / −0.575 / −0.303 | 2.85, 2.92 | +0.007 / −0.011 / −0.005 / −0.001 | 3.23, 3.79 |

   - **The $O(\Delta z)$ wall layer** (§2) occupies a band of width $O(\Delta z)$, where the mode amplitude is $O(\Delta z)$. It therefore enters the projected tendency at $O(\Delta z^3)$, against $O(\Delta z^2)$ for the interior offset.
   - **The reference change itself** (base − switch) is identical with ΔF on and off. At 1 $H_p$ its band part converges at order 3.0 and its interior part at order 2.0.
   - **With the switch,** the interior converges at order about 4. The leftover is a band term of order about 3 that is *not* the reference layer: it is mostly present with ΔF off, and is also present in the base.

5. **ctests.** Two base well-balanced tests that pin the base reference's values (the non-uniform balanced-column fixed point, and a face-density floor fallback) fail with the switch **on** by construction. They must pass with it off.

## 6. Independent re-derivation check (done for this file)

I re-checked each step numerically on a generic smooth background that is not a polytrope ($p = e^{-0.9z}(1+0.2\sin 1.3z)$, $\rho = e^{-0.7z}(1+0.1\cos 0.8z)$), using exact cell averages:
- **Base offset.** The base face offset over the closed form of §2 gives 0.9943 / 0.9986 / 0.9997 / 0.9999 at $h$ = 0.1 / 0.05 / 0.025 / 0.0125, so the closed form holds in general, converging like $h^2$.
- **Fixed reference.** With §4.1-§4.2, the face density error against the true face value is 5.5e-7 / 3.4e-8 / 2.1e-9 / 1.3e-10, and $|\rho_{\rm ref}-\bar\rho|/\rho$ is 7.5e-7 / 5.1e-8 / 3.4e-9 / 2.2e-10. Both fall by 16 per halving, i.e. $O(h^4)$.
- **Filter and weights.**
  - $F$: sum 1, second moment 0, fourth moment $-1.5$ (cells), Nyquist response 0.
  - Six-face weights: the cell average of the quintic through six faces is $(11,-93,802,802,-93,11)/1440$, the base interior weights.
  - Cubic extrapolation to index $-1, -2$: $(4,-6,4,-1)$ and $(10,-20,15,-4)$.
  - Interior $\mathcal I_4$: $(-1,7,7,-1)/12$.
- **$p_{\rm ref} = \bar p$, re-derived** (previously only asserted). For a hydrostatic background the scan gives $p_{{\rm sf},i-1/2} - p_{{\rm sf},i+1/2} = g\bar\rho_i\Delta z = \int_{\rm cell} g\rho\,dz$ exactly, so the scan faces are the exact face pressures up to one column constant (the top anchor, which is an isothermal half-cell estimate, error $O(\Delta z^2)$). The six-face quadrature then gives $p_{\rm ref} = \bar p + c + O(\Delta z^6)$. The constant $c$ does not create a face offset: it changes $\rho_{\rm ref}$ by the smooth $c\,R$, and since the face reference is $\mathcal I_4$ of the same $\rho_{\rm ref}$, the reconstruction of $\rho' = \bar\rho - \rho_{\rm ref}$ carries it consistently.

## 7. Answers to the three specification questions

The answers below are pinned to the committed tree at `c5b810d2db585d7902fb8c0234d1cec1725039d1` (head of that #289 branch). c0a3636e9d42859a23d3ea74eddeb8773ba9862c differs only in the resolution guard (item Q3.6). `hydro_ref_x1_impl.h`, `hydro_forward.cpp`, `riemann/lmars_impl.h` and `forcing/const_gravity.cpp` are unchanged from the base on this branch. "Harness" means the curved-column harness script `curved_column.py` at that sha. These references are for checking only; the method is fully stated in the text.

### Q1. The one-step residual, and the cell-average initial condition

**Background and mode.**
- Neutral polytrope with $R_d = 1$, $\gamma = 5/3$, $m = 1/(\gamma-1)$ and $g = m+1$: $T_0 = 1 + L_z - z$, $\rho_0 = T_0^{m}$, $p_0 = T_0^{m+1}$ (harness 180-181, 189).
- Seeded mode, as the momentum (not the velocity) field: $\rho_0 v_1 = A k\sin(qz)\cos(kx)$, $\rho_0 v_2 = -A q\cos(qz)\sin(kx)$, with $q = \pi/L_z$, $k = 2\pi/L_x$ and $L_x = 2L_z$ (harness 190, 218-219).
- Default amplitude $A = 10^{-4}$ (harness 773).
- Walls: reflecting x1, periodic x2, face gravity work.

**Cell-average IC** (`--ic average`, harness 196-226).
- Each cell gets the exact cell average of the conserved fields $\rho$, $m_1 = \rho v_1$, $m_2 = \rho v_2$ and $E = p/(\gamma-1) + |m|^2/(2\rho)$.
- The average is a tensor-product 4×4 Gauss-Legendre quadrature per cell (exact to polynomial degree 7; $O(\Delta z^8)$ for these smooth fields), normalised by the summed weights. The weights are uniform on Cartesian grids and $r^2\sin\theta$ on spherical grids.
- The primitives handed to the solver are then $\bar\rho$, $\bar m/\bar\rho$ and $\bar p = (\gamma-1)\big(\bar E - |\bar m|^2/(2\bar\rho)\big)$ (harness 223-226).
- There is no separate averaging of $p$ or of $\rho/p$. $\bar p$ differs from $\langle p\rangle$ only at $O(A^2)$.

**Step.**
- One SSP-RK3 step (all stages) at a fixed $\Delta t = 0.3\,\Delta z/c_b$, with $c_b = \sqrt{\gamma T_{\rm bottom}}$, the same on every grid (harness 240-241, 249).
- The state used is the **end-of-step conserved state**, converted to primitives in the diagnostic (harness 232-235). The solver's primitive array lags one RK stage and is not used.

**Residual.**
- With $s = \ln(p\rho^{-\gamma})$ per cell (harness 237-238):
$$\delta s_i = \frac{\big[s(\rho^1_i,p^1_i) - s(\rho^0_i,p^0_i)\big]_{\rm mode} - \big[s(\rho^1_i,p^1_i) - s(\rho^0_i,p^0_i)\big]_{\rm rest}}{\Delta t}$$
(harness 263-278). The "rest" run is the same IC with $A = 0$; subtracting it removes any amplitude-independent discrete imbalance.
- The measure is a volume-weighted projection onto the seeded vertical velocity $w_i = v_{1,i}$ at $t = 0$, over **all interior cells** (no ghosts; harness 179, 230, 279-280):
$$N^2_{\rm eff} = \frac{g}{\gamma}\,\frac{\sum_i V_i\,(-\delta s_i)\,w_i}{\sum_i V_i\,w_i^2}.$$
- It is reported as $N^2_{\rm eff}\,n_z^2$. The observed order is $\log_2$ of the ratio of successive $|N^2_{\rm eff}|$ at doubled $n_z$, with $n_x = 2n_z$.
- Linearity is checked by repeating at $2A$ (harness 271).
- The "band" values restrict the numerator to the 3 cells at each x1 wall, with the same denominator.

**Why the diagnostic has no $O(\Delta z^2)$ floor of its own** (Cartesian, linear order).
- **Mass:** $m = \nabla\times\psi$, so $\nabla\cdot m = 0$ pointwise, giving $\partial_t\rho = 0$ exactly.
- **Energy:** the linear energy equation is $\partial_t E = -\nabla\cdot(\kappa p_0 v) - g\,m_1 = -\kappa\,m\cdot\nabla T_0 - g\,m_1 = (\kappa - g)\,m_1$. This uses $p_0 v = T_0\,m$, $\nabla\cdot m = 0$ and $T_0' = -1$. Since $\kappa = \gamma/(\gamma-1) = m+1 = g$, it vanishes pointwise.
- **Kinetic energy:** its tendency is $O(A^2)$.
- So the exact cell-average tendencies of $\bar\rho$ and $\bar E$ vanish identically, and $s(\bar\rho,\bar p)$ has zero exact tendency at linear order, whatever its own discretisation. Every measured $\delta s$ is scheme error. This holds for every depth of this polytrope family.
- **Point-value IC.** Setting $\rho_0(z_i)$, $p_0(z_i)$ as cell values (`--ic point`) changes the represented background by $O(\Delta z^2)$ and adds a real offset: $-0.408$ in $N^2n_z^2$ at T4 depth, predicted and measured. The residual tables use the cell-average IC.

### Q2. Which H

- **"1/2/3/5 H" in the residual tables** is the column depth in **pressure e-folds**, $n = \ln(p_b/p_t) = \int dz/H_p$ with the local pressure scale height $H_p(z) = R_dT(z)/g$.
- **For the polytrope**, $H_p$ varies from $1/g$ at the top to $(1+L_z)/g$ at the bottom. The depth is set as $L_z = e^{\,n/(m+1)} - 1$ (harness 62-66). T4 is $n = 10/3$ (harness 59). So "5 H" means $p_b/p_t = e^5$; it does not mean $L_z = 5H$ at any one level.
- **For the isothermal column** (used only in the rest-state test), $H_p = R_dT/g = 1/g$ is constant and $L_z = n/g$ (harness 353).
- **The curved-harness "R ≈ 5H"** uses a different H: the **bottom** pressure scale height $H_b = (1+L_z)/g$, with $R_{\rm in} = 5H_b$ (harness 70, 80).

### Q3. "Exact discrete balance" for the density reference, at walls and in ghosts

1. **The operator balanced.**
   - **Pressure:** the x1 momentum equation in conservation form, with the LMARS face pressure $\bar p = \tfrac12(p_L+p_R) + \tfrac12\bar\rho\bar c\,(u_L-u_R)$ (`lmars_impl.h` 38-39) in the momentum flux $\bar u\rho u + \bar p$ (58, 73), divided by $\Delta z$ through the flux divergence.
   - **Gravity:** the cell source $\Delta t\,\bar\rho_i\,g_1$ added to the x1 momentum (`const_gravity.cpp` 49; non-hydrostatic factor 1 by default, 25).
   - **The reference faces:** the hydrostatic scan sets $p_{{\rm sf},i-1/2} = p_{{\rm sf},i+1/2} + g\bar\rho_i\Delta z_i$ (`hydro_ref_x1_impl.h` 23-60, anchor 37, increment 43/53).
   - **At rest:** $p' = c$ is constant, so $p_L = p_R = p_{\rm sf} + c$, $u = 0$ and $\bar p = p_{\rm sf} + c$ (restore at `hydro_forward.cpp` 184-185). The momentum-flux difference then equals $g\bar\rho_i\Delta z_i$ and cancels the source exactly.
   - **The density reference is not part of this pairing.** At rest $\bar u = \tfrac12(u_L+u_R) + (p_L-p_R)/(2\bar\rho\bar c) = 0$ (`lmars_impl.h` 42-43), so the mass flux $\bar u\rho$ (53, 68) and the face gravity work (`hydro_forward.cpp` 553) vanish whatever the face density is.
   - "Exact discrete balance" therefore means:
     - (a) the fix never changes $p_{\rm sf}$;
     - (b) on uniform grids it never changes $p_{\rm ref}$, so the discrete rest state $\bar p = p_{\rm ref} + c$ is the base's;
     - (c) on non-uniform grids the changed $p_{\rm ref}$ (§4.3) defines a new rest state, which the balancing utility finds with the same switched reference (`balance_column.cpp` 67-78).
2. **Order of operations per x1 block** (`hydro.cpp`):
   - (i) base kernel (434-436);
   - (ii) cell part of the fix: non-uniform $p_{\rm ref}$, then $\rho_{\rm ref} = p_{\rm ref}\,F[\rho/p]$ (444-445);
   - (iii) anchor relay to the block below (449);
   - (iv) ghost-row exchange of $(p_{\rm ref}, \rho_{\rm ref})$ across x1 seams (452 onward), overwriting this block's ghost rows with the neighbour's interior values;
   - (v) face part: $\rho_{\rm sf} = \mathcal I_4[\rho_{\rm ref}]$ (515), **after** the exchange.

   The 5-point filter $F = (-1,4,10,4,-1)/16$ acts on the **cell** ratio $r = \bar\rho/\bar p$ in step (ii), not on faces (`hydro_ref_x1_exact.cpp` 146-177, weights at 164).
3. **Physical walls with the wall clamp on** (default true, `hydro_options.cpp` 57).
   - **Filter:** the two values beyond the wall are cubic extrapolations, in cell index, of the four owned cells nearest the wall (134-145; fewer if the block owns fewer than four, 83). Ghost cells are never read.
   - **Face windows:** the 4-cell window of $\mathcal I_4$ stays inside the owned cells (194-200); with fewer than 4 owned cells it reads past the wall (196).
   - **Pressure:** the six-face $p_{\rm ref}$ keeps the base's one-sided wall rows (`hydro_ref_x1_impl.h` 102, 128-150).
   - **Perturbation ghosts:** the solver fills them with even parity, $\rho'(i_s - m) = \rho'(i_s + m - 1)$ and likewise for $p'$ (`hydro_forward.cpp` 158-173).
   - **The wall face carries no mass flux:** reflecting ghosts give $u_L = -u_R$ and $p_L = p_R$, so $\bar u = 0$.
4. **Clamp off.** The stencils read ghost cells as the base does. The base itself is then not at rest: max|v| about $10^{-5}$ after 1000 steps, and no balanced state exists because the balancing utility requires the clamp (`balance_column.cpp` 28). The switch matches base to about $10^{-3}$ relative there.
5. **Seams and non-physical sides.** The filter reads the array's own ghost values (exchanged primitives). Beyond the array the deepest ghosts replicate the edge (146-150). Ghost rows of $\rho_{\rm ref}$ computed locally are replaced by the neighbour's in step (iv).
6. **Guards.**
   - **Range** (cells 165-171; faces 213-223), with a $10^{-10}$ relative margin.
   - **Resolution:** $|\ln(p_{\rm lo}/p_{\rm hi})| > 0.5$, dilated ±2 cells (30-44). Ghosts beyond a clamped wall are excluded (35-36). That exclusion is in c5b810d; in c0a3636 it was absent, which wrongly flagged top cells at 5 $H_p$, nz 32/64.
   - A guarded cell or face keeps the base value.

## Open points

These are gaps or inconsistencies I found while extracting the spec. None was changed in the math above.

1. **Request vs spec.** The request describes "the (-1,4,10,4,-1)/16 filter applied to faces after the ghost exchange". In the derivation the filter acts on the **cell** ratio $r = \bar\rho/\bar p$ (§4.1), **before** the exchange. The **face** density is the fourth-order interpolation of the filtered cell reference (§4.2), formed **after** the exchange. The spec follows the derivation; the description should be corrected wherever it is reused.
2. **"Reference density and pressure."** The fix changes the reference *pressure* only on non-uniform grids (§4.3); face pressures never change. The source derivation asserted that the uniform six-face $p_{\rm ref}$ is $\bar p + O(\Delta z^6)$ without proof. §6 now derives it for a hydrostatic background, up to the anchor constant, which is shown harmless. For a non-hydrostatic state, $p_{\rm ref}$ and $\bar p$ differ by the imbalance; that difference is part of $p'$ and is reconstructed normally. I did not re-derive the non-uniform four-face cubic (§4.3) beyond its weights being exact for a cubic.
3. **Index-space operations on non-uniform grids.** $F$'s zero second moment and the cubic wall extrapolation are exact in cell-index units only. On a stretched grid both carry an extra error proportional to the grid stretching. The derivation calls the extrapolation "exact for a cubic" without this qualifier. $\mathcal I_4$ (§4.2) and the pressure cubic (§4.3) do use physical spacing.
4. **Thin blocks.** With fewer than four owned cells next to a clamped wall, the extrapolation and face windows must use fewer points or fall back past the wall. The derivation does not specify the reduced order or behaviour there.
5. **Order terminology in the oracle.** "residual·nz² → 0 at about order 3" means the observed order of $N^2_{\rm eff}$ itself is about 3; residual·nz² then falls only like $\Delta z$. A second implementer should report the same quantity.
6. **Unidentified wall leftover.** With the switch on, the remaining order-3 term sits in the wall bands. It is mostly present with ΔF off, and also in the base. Its source is a hypothesis only (the even-parity perturbation ghosts or the reflecting-wall reconstruction). The "about order 3" oracle depends on this leftover, not on the reference.
7. **Guard thresholds.** The 0.5 resolution threshold, the ±2 dilation and the $10^{-10}$ margin are design choices, not derived. Guarded cells fall back to the base reference, including its $O(\Delta z)$ wall layer.
8. **Pre-asymptotic point.** At 5 $H_p$, nz 64, the measured base − switch difference (2.504) is 10 % above the closed-form prediction (2.283); nz 128/256 agree within 0.4–4 %.
9. **Multi-species.** $r$ uses the dry-density channel, as the base reference does. Moist and multi-component columns are untested.
10. **Untested paths.** CUDA, multi-process x1 seams and cubed-sphere blocks were not run with the switch on.
11. **Two different "H".** The residual tables use pressure e-folds over the whole column (Q2). The curved harness's "R ≈ 5H" uses the bottom pressure scale height. #289's onset deck described its box as "one bottom pressure scale height deep" ($\rho_b/\rho_t \approx 2.32$), which is a third convention. Any cross-deck comparison of "1 H" must state which one it uses.
12. **Spherical diagnostic floor.** The no-floor argument in Q1 is Cartesian. On the spherical grid the same seeded field is not divergence-free ($\nabla\cdot m \ne 0$). The cell average of $\partial_t p = \gamma(p/\rho)\partial_t\rho$ then differs from $\gamma(\bar p/\bar\rho)\partial_t\bar\rho$ by an $O(\Delta z^2)$ covariance, so the spherical numbers may carry an $O(\Delta z^2)$ diagnostic floor. This has not been quantified.
13. **Ghost cells in the IC.** The cell-average IC is also evaluated in ghost cells before the solver's boundary fill. I have not checked whether initialisation overwrites them before the first step; interior values are unaffected either way.
14. **Request wording vs code, again.** The request text says "the 5-point filter … and the post-ghost-exchange face construction". In the code the filter is a cell operation before the exchange, and only the face interpolation follows the exchange (Q3.2). The file follows the code.
