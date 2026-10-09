# Onset growth-rate error with `SNAP_WB_REF4` (W): defect or unmasking?

Code read: `UCzhangxi/snapy` `next/curved-gravity-work-wb` @ 37dce4e (base `chengcli/snapy` main aea71ed).
Replica: `study/wb-ref4-onset/` (numpy; `replica.py` is the 117e449 explicit-RHS clone used for #289,
`wbonset.py` adds W, D and the onset column; `run_onset.py`, `js_rq.py`; tables in `runs/`).

**Verdict.**
* W is not defective. On a uniform grid it changes only the background face density that the x1 **mass**
  flux carries. That removes a genuine $O(\Delta z^2)$ interior error and an $O(\Delta z)$ wall band of the
  old reference. Neither the momentum (buoyancy/pressure) pairing nor the energy flux sees the density
  reference at linear order.
* In a replica of the discrete linear operator, cov+W+D is fourth order and has a smaller onset error than
  cov on every box (3 H, $n_z$ 64: $-2.2\times10^{-5}$ vs $-2.0\times10^{-3}$).
* snapy's onset error with cov+W+D is the replica's error plus a **common, W/D-independent term**
  $X>0\propto\Delta z^2/\epsilon$. The old reference's offset was partly cancelling $X$; W+D removes the offset and so
  exposes $X$. $X$ is the same depth-growing destabilising energy-row residual found earlier (item 5). It is not
  in the WB reference, the gravity work, the x2 covariance, the wall-ghost temperature or WENO-JS weights.
* The fix belongs on $X$, not on W. Keep W and D together: each alone is worse than cov.

---

## 1. What W changes on a uniform grid (question 1)

### 1.1 The base kernel (unchanged by W)
* Face pressure, top-down scan with the **actual cell density**:
  `src/hydro/hydro_ref_x1_impl.h:42-49`, `dp = grav * w[IDN] * dx1f[i]; lo = face + dp; hi = face`. So
  $$p_{{\rm sf},i-1/2}-p_{{\rm sf},i+1/2}=g\,\bar\rho_i\,\Delta z\qquad\text{(bitwise, by construction).}$$
* Cell pressure `pref`: the six-face quintic average, `hydro_ref_x1_impl.h:110-126` (one-sided rows at clamped walls, `:128-150`).
* Old density reference: `dref = pref * B(rho/p)`, `dsf = psf_lo * mean(B(rho/p))`, `hydro_ref_x1_impl.h:158-167`, with $B=(1,4,6,4,1)/16$ edge-replicated.

### 1.2 W (`SNAP_WB_REF4`)
* `src/hydro/wb_ref4.hpp:8-13`: "fourth-order x1 reference DENSITY …, and on non-uniform x1 grids a fourth-order cell reference pressure. The face pressures (the hydrostatic scan) are never changed."
* `wb_ref4.cpp:252-260`: `pref` is replaced **only** `if (!st.uniform)`.
* `wb_ref4.cpp:263-272`: `dref = pref * F(rho/p)`, $F=(-1,4,10,4,-1)/16$, with cubic wall extrapolation (`:120-163`).
* `wb_ref4.cpp:276-286`: `dsf` = the fourth-order face value of `dref`, weights $(-1,7,7,-1)/12$ in the interior and $(25,-23,13,-3)/12$, $(3,13,-5,1)/12$ at the walls (`:195-221`).
* Called from `src/hydro/hydro.cpp:543-552` (cells, before the seam exchange) and `:622` (faces).

So on a uniform grid W changes `dref` and `dsf` only. `pref` and `psf` stay the kernel's, as the lead suspected.

### 1.3 Where `dref`/`dsf` enter the solver
`hydro_forward.cpp:269-274` subtracts `pref`, `dref`. `:305-315` restores `psf_lo` and `dsf` on the reconstructed faces. `:352` calls LMARS.

| quantity | formula | sees `dref`/`dsf` at linear order? |
|---|---|---|
| x1 face pressure | $p_f=p_{\rm sf}+\mathcal R(p-p_{\rm ref})$ | no |
| x1 momentum source | $-g\bar\rho_i$, `forcing/const_gravity.cpp:49` (`w[IDN]`) | no |
| x1 mass flux | $\bar u\,\rho_f$, $\rho_f=d_{\rm sf}+\mathcal R(\rho-d_{\rm ref})$ | **yes, via the background $\rho_f$** |
| x1 energy flux | $\bar u\,\rho_f h_f=\bar u\,(I_f+p_f)$ (`riemann/lmars.cpp:36`, `lmars_impl.h:28-31,61`) | no: $\rho_f$ cancels for an ideal gas |
| x1 momentum flux | $\bar u\rho_f u+\bar p$ | quadratic, plus LMARS $\bar\rho\bar c$ terms of size $O(\Delta z^2)\times O(\Delta z^5)$ |
| face gravity work | $-\tfrac g2(F_{\rho,i-1/2}+F_{\rho,i+1/2})$ | yes, through $F_\rho$ |

**The pairing.** The linear momentum tendency of a perturbation is
$$\partial_t(\rho w)'_i=-\frac{1}{\Delta z}\Big[\mathcal R\big(p'-p'_{\rm ref}\big)\Big]_{i-1/2}^{i+1/2},\qquad
p'_{{\rm sf},i-1/2}-p'_{{\rm sf},i+1/2}=g\rho'_i\Delta z ,$$
because the scan of $\rho'$ cancels the source $-g\rho'_i$ exactly. Here $p'_{\rm ref}$ is the six-face average of that scan. Buoyancy and the pressure gradient are therefore paired through the hydrostatic pressure of $\rho'$ itself, consistent to sixth order, and **no density reference appears**. The identity $(p_{{\rm sf},i+1/2}-p_{{\rm sf},i-1/2})/\Delta z=-g\bar\rho_i$ holds to round-off with W on or off. W never touches $p_{\rm sf}$, and the scan reads $\bar\rho$, not `dref`. At rest $p-p_{\rm ref}=c+O(\Delta z^6)$ (uniform `pref` unchanged), so the rest balance is also unchanged. There is no "2nd-order pressure reference + 4th-order density reference" pairing in the momentum equation.

## 2. First-order growth-rate error of the discrete operator (question 2)

### 2.1 Perturbation formula
For the discrete operator $A=A_0+\delta A$ with right and left eigenvectors $\psi,\psi_L$ of $A_0$:
$$\delta\sigma=\frac{\psi_L^\dagger\,\delta A\,\psi}{\psi_L^\dagger\psi}.$$
In the weak-$\epsilon$ limit the components scale as $w\sim1$, $s'\sim p'/p\sim\rho'/\rho\sim\epsilon/\sigma$, and the left entropy component goes as $g/\sigma$. Therefore:
* an entropy-row error $\propto w$ gives $\delta\sigma/\sigma\propto\Delta z^2/\epsilon$ (a spurious stratification $\epsilon_{\rm spur}$, $\delta\sigma/\sigma\simeq a\,\epsilon_{\rm spur}/\epsilon$);
* a momentum-row error $\propto(\rho',p')$ gives only $\delta\sigma/\sigma\propto\Delta z^2$;
* the entropy row sees only velocities at linear order: mass, energy, gravity-work and covariance rows all carry $\bar u$ or $u_n$, and the LMARS pressure jumps are $O(\Delta z^5)$ on smooth data.

The observed $\Delta z^2/\epsilon$ (3 H, $n_z$ 64: $6.43\times10^{-3}$ at $\epsilon=10^{-3}$, $2.59\times10^{-2}$ at $2.5\times10^{-4}$, ratio 4.03) therefore points to an **entropy-row error proportional to velocity**.

### 2.2 The term W removes
The old background face density is offset from $\mathcal R[\bar\rho]_f$ by (`docs/derivations/wb-ref4.md` §2; verified in `study/289-covariance` §7)
$$\delta\rho_f=\frac{\Delta z^2}{12}\big(p'R'+2pR''\big),\qquad R=\rho/p,$$
plus an $O(\Delta z)$ band on the first two to three faces at each wall from edge replication in $B$. On a polytrope $T=1-\beta z$ ($g=R_d=1$): $R=1/T$, so
$$\delta\rho_f=\frac{\Delta z^2}{12}\,\rho\,\frac{\beta(4\beta-1)}{T^2}.$$
It enters the mass flux $\delta F=\delta\rho_f\,w$ **without** an energy-flux counterpart (§1.3), and the face work as $-g\,\overline{\delta F}$. With $s'=p'/(\gamma p)-\rho'/\rho$:
$$\partial_t s'\ni\frac{1}{\rho}\partial_z\delta F-\frac{\gamma-1}{\gamma p}\,g\,\overline{\delta F}
=\frac{\Delta z^2}{12}\Big[c\,w_z+\frac{c\,(2\beta-1)}{T}\,w\Big],\qquad c=\frac{\beta(4\beta-1)}{T^2},$$
using $\rho_z/\rho=-(1-\beta)/T$, $(\gamma-1)g\rho/(\gamma p)=\beta_{\rm ad}/T\simeq\beta/T$ and $c_z=2c\beta/T$. This is an $O(1)\times\Delta z^2$ entropy source $\propto w$: a spurious stratification, amplified by $1/\epsilon$. Compare the velocity-conversion term V ($w=\langle m\rangle/\langle\rho\rangle$). There the error is in $\bar u$, so it enters **both** the mass flux and the energy flux ($h\,\delta F$), and the bracket collapses to $-(h_{0,z}+g)\delta F=O(\epsilon)\,\delta F$, which is harmless. The density offset has no such partner, so it is a scheme defect. W removes it to $O(\Delta z^4)$, including the wall band (cubic wall rows).

D does the same for the face-form wall cells. Zeroing the curvature flux $H$ at walls leaves a work error $-a\Delta z/12$ in the wall cell (#289 draft §4.3). D's corrected-PE work (`hydro_forward.cpp:765-771`, `gravity_work_radial.hpp:57-63`) uses one-sided slopes there instead.

So the term W changes is a **defect** (an inconsistent pairing: a density error in the mass flux without the matching energy-flux error), and W is the correct fix for it. It is not an inherent property of mixing a 4th-order density reference with a 2nd-order momentum/pressure discretisation, because the momentum pairing never sees the density reference.

### 2.3 Replica of the discrete linear operator
Uniform 2-D column, one x2 Fourier mode, inviscid, reflecting walls, WENO5 with linear weights, LMARS, face work, cov. Background: exact cell averages of $T=1-\beta z$, $\beta=g/c_p+\epsilon g/R$, depth $N_H$ pressure e-folds; $L_x=2\sqrt2L$, $n_x=2n_z$. The growth rate is the largest real eigenvalue of the JVP operator. The continuous rate comes from an inviscid Chebyshev problem (the largest eigenvalue stable between N=96 and 144; one spurious wall mode moves with N and is rejected). Entries are $\sigma/\sigma_c-1$.

| box | $n_z$ | cov | cov+W | cov+D | **cov+W+D** |
|---|---|---|---|---|---|
| 1 H, $\epsilon=10^{-3}$ | 16 | $-1.4\times10^{-4}$ | $+4.4\times10^{-2}$ | $-9.3\times10^{-2}$ | $-3.4\times10^{-3}$ |
| | 32 | $-3.65\times10^{-3}$ | $+4.9\times10^{-3}$ | $-1.0\times10^{-2}$ | $-2.0\times10^{-4}$ |
| | 64 | $-6.2\times10^{-4}$ | $+5.9\times10^{-4}$ | $-1.3\times10^{-3}$ | $-1.3\times10^{-5}$ |
| 3 H, $\epsilon=10^{-3}$ | 16 | $+2.2\times10^{-2}$ | $+7.1\times10^{-2}$ | $-1.5\times10^{-1}$ | $-4.6\times10^{-3}$ |
| | 32 | $-8.6\times10^{-3}$ | $+6.6\times10^{-3}$ | $-1.9\times10^{-2}$ | $-2.9\times10^{-4}$ |
| | 64 | $-2.0\times10^{-3}$ | $+7.5\times10^{-4}$ | $-2.9\times10^{-3}$ | $-2.2\times10^{-5}$ |
| 3 H, $\epsilon=2.5\times10^{-4}$ | 32 | $+3.4\times10^{-2}$ | $+5.1\times10^{-2}$ | | $-1.1\times10^{-3}$ |
| | 64 | $-7.1\times10^{-3}$ | $+3.6\times10^{-3}$ | | $-7.0\times10^{-5}$ |
| 5 H, $\epsilon=10^{-3}$ | 16 | $-1.5\times10^{-1}$ | $+1.4\times10^{-1}$ | | $-9.6\times10^{-3}$ |
| | 32 | $-2.0\times10^{-2}$ | $+1.0\times10^{-2}$ | | $-6.0\times10^{-4}$ |
| | 64 | $-4.9\times10^{-3}$ | $+1.0\times10^{-3}$ | | $-4.5\times10^{-5}$ |

* The sign pattern matches the lead's one-step metric: cov negative, cov+W positive (the face-form wall cell, about $\Delta z^3$), cov+W+D fourth order. The replica's operator and the one-step entropy metric agree.
* W alone or D alone is worse than cov. The old WB wall band and the face-form wall-cell work error have opposite signs and partly cancel, so only W+D together is consistent.
* Without cov (3 H, $n_z$ 64): base $-3.9\times10^{-2}$, W+D $-3.7\times10^{-2}$. The x2 covariance is the dominant term, as in #289.

## 3. The term that makes snapy's cov+W+D worse

Subtract the replica's linear-operator error from the lead's snapy onset error:

| box | $n_z$ | snapy cov − replica cov | snapy cov+W+D − replica cov+W+D |
|---|---|---|---|
| 3 H, $\epsilon=10^{-3}$ | 32 | $+2.53\times10^{-2}$ | $+2.62\times10^{-2}$ |
| | 64 | $+6.72\times10^{-3}$ | $+6.45\times10^{-3}$ |
| 3 H, $\epsilon=2.5\times10^{-4}$ | 64 | $+2.63\times10^{-2}$ | $+2.60\times10^{-2}$ |
| 1 H (deck $\epsilon$ assumed $10^{-3}$) | 32 | $+2.8\times10^{-3}$ | $+4.7\times10^{-3}$ |
| | 64 | $+8.8\times10^{-4}$ | $+1.1\times10^{-3}$ |

* On the 3 H decks, whose $\epsilon$ the lead gave, the residual $X$ is the **same with and without W+D** to 1–4 %.
* $X\,\epsilon\,n_z^2=0.027$ in all three 3 H cases, i.e. $X\propto\Delta z^2/\epsilon$, positive (destabilising).
* $X$ (3 H, $n_z$ 64, $\epsilon=10^{-3}$) $=+0.65$–$0.67\,\%$ matches the item-5 depth-growing energy-row residual $+0.72\,\%$; at 1 H, $+0.09$–$0.11\,\%$ vs $+0.06\,\%$.

The explanation of the onset numbers is therefore:
$$\text{snapy}(\text{cov})=\underbrace{E_{\rm WB}}_{<0,\ \text{removed by W+D}}+X,\qquad \text{snapy}(\text{cov+W+D})=O(\Delta z^4)+X .$$
W+D removes the negative WB/wall-cell error that was partly cancelling $X$. The onset error grows because $X$ is exposed, not because W adds an error. That is also why the one-step metric (momentum-seeded, projected on $w$) cannot see it: whatever $X$ is, the replica's operator does not contain it, and neither did the metric.

### 3.1 What X is not (tested in the replica)
| hypothesis | test | result (3 H, $\epsilon=10^{-3}$, $n_z$ 32/64, cov / cov+W+D) |
|---|---|---|
| wall ghost $T$ (reflecting = mirrored, vs fixed-T extrapolated) | `ghostT=mirror` | $-9.7\times10^{-3}/-2.0\times10^{-3}$ and $-3.1\times10^{-4}/-2.2\times10^{-5}$: no positive term |
| nonlinear WENO-JS weights, mode-dominated (seed $\rho'\gg$ background $\rho'$) | `js_rq.py`, Rayleigh quotient at amplitudes $10^{-4},10^{-6}$ | cov $-2.7\times10^{-2}/-3.0\times10^{-3}$; cov+W+D $-2.5\times10^{-4}$ to $+7.8\times10^{-5}$: no positive term |
| frozen JS weights (background-dominated) | JVP with `weno="js"` | $-50$ to $-90\,\%$, nothing like snapy's $10^{-3}$, so not the regime of the runs |
| x2 covariance as merged | read `hydro_forward.cpp:35-190` | in Cartesian the centroid part is 0 and the energy part is $\sigma_1^2\rho\,D_1h\,D_1u_n$ from x2 face states, the replica's $\Delta F$ up to $O(\Delta x^2)$ face averaging |
| WB reference, gravity work | §2 | $X$ is independent of W and D by the table above |

### 3.2 Where to look next (no code in the PR branch)
1. Take snapy's own discrete Jacobian on the 3 H, $n_z$ 32 deck: centred JVPs of `HydroImpl::forward` on one x2 Fourier mode, as `Deck.operator` does. Compare its eigenvalue with the replica's ($-8.6\times10^{-3}$ cov, $-2.9\times10^{-4}$ cov+W+D). If snapy's eigenvalue carries $X\approx+2.6\times10^{-2}$, diff the two Jacobians row by row; the energy row is expected to differ, since item 5 put the residual there. If it does not, $X$ is in the time-stepped measurement (IC projection onto the mode, RK3 stage handling of the face work or of the covariance, fit window), and the one-step-vs-onset comparison should be repeated with the EVP mode as IC.
2. Candidates on the snapy side that the 117e449 replica does not contain: the 326 changed lines of `hydro_forward.cpp` since 117e449 outside cov/W/D (positivity carry, `bflux1`, gravity-work fixer paths, the `face_work_in_operator` branch), and any IC preparation in the onset decks (`balance_column` with the switch).
3. The item-5 split already brackets $X$: its projection is $+0.07/+0.69/+1.78\,\%$ at 1/3/5 H (energy row minus V, with ΔF on), destabilising, $\propto\Delta z^2$. Any candidate must reproduce that vector.

## 4. Recommendation (question 3)
* No change to W: its pairing is consistent and it removes a real defect. Ship W only together with D (each alone is worse than cov, §2.3).
* The "fix" column of the replica is cov+W+D itself: fourth order at every depth and $\epsilon$.
* Localise $X$ with step 3.2(1) before changing anything else. Until then, quote onset errors with cov+W+D as "$X$ exposed", not as a W regression.

## 5. Reproduce
```
cd study/wb-ref4-onset
python3 run_onset.py 3 1e-3 16,32,64 cov,covW,covWD,covD   # table 2.3
python3 run_onset.py 3 1e-3 32,64 cov,covWD linear mirror   # ghost T
python3 js_rq.py 3 1e-3 32,64 1e-4,1e-6                     # WENO-JS, mode-dominated
```
