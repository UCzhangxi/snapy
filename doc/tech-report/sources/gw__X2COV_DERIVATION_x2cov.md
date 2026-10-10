> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# The missing vertical covariance in the horizontal energy flux (SNAPY_X2COV)

Written 2026-10-08 for the technical report. Numbers quoted come from the one-step mechanism and safety runs
(`mech_table.txt`, `mech_*/mech.json`, `safety_*`) and from the T1L eigenmode files. The patch is `x2cov.patch`
(scratch commit 115a8fa on snapy 117e449).

Notation. $z = x_1$ is vertical (cell height $\Delta z$), $x = x_2$ is horizontal (the $x_3$ case is identical
with $v$ for $u$). Velocities $(u, w)$ are $(x_2, x_1)$ components. Ideal gas, $p = \rho R T$, constant $\gamma$,
$K \equiv \gamma/(\gamma-1) = c_p/R$. The T1L deck: $R = g = 1$, $\gamma = 1.4$, $c_p = 3.5$,
$T_0 = 1 - \beta z$, $p_0 = T_0^{1/\beta}$, $\rho_0 = p_0/T_0$, $0 \le z \le 1$, $\beta = 1/c_p + \varepsilon$,
where $\varepsilon = \nabla - \nabla_{\rm ad}$ is the superadiabatic excess
(so $\mathrm{d}s_0/\mathrm{d}z = -c_p\,\varepsilon/T_0$).

## 1. What the finite-volume scheme should supply at an $x_2$ face

Integrate the energy equation over a cell $[x_{j-1/2}, x_{j+1/2}] \times [z_{k-1/2}, z_{k+1/2}]$ and divide by
its area. The horizontal part of the update of the cell-mean total energy $\bar E$ is

$$
\frac{\mathrm{d}\bar E_{jk}}{\mathrm{d}t}\Big|_{x}
= -\frac{\langle F\rangle_{j+1/2,k} - \langle F\rangle_{j-1/2,k}}{\Delta x},
\qquad
\langle F\rangle_{j-1/2,k} \equiv \frac{1}{\Delta z}\int_{z_{k-1/2}}^{z_{k+1/2}} F\big(x_{j-1/2}, z\big)\,\mathrm{d}z .
$$

The flux the update needs is therefore the **face average over the cell height** of the point flux. The energy
flux is $F = (E + p)\,u = K p u + \tfrac12 \rho |\mathbf v|^2 u$. Around a state at rest the kinetic part is cubic
in the perturbation, so to linear order (and to the order this note keeps)

$$
F = f(p, m, \rho) \equiv K\,\frac{p\,m}{\rho}, \qquad m = \rho u .
$$

What the scheme supplies instead: the reconstruction across $x_2$ is built from the cell means, so the states
handed to the $x_2$ Riemann solver are (to high order in $x$) point values *along* $x$ of the
*height-averaged* state, and the solver returns $f$ of that state:

$$
F_{\rm num} = f\big(\langle p\rangle, \langle m\rangle, \langle \rho\rangle\big).
$$

$\langle\rho\rangle$ and $\langle m\rangle$ are exactly the evolved cell means. The pressure is recovered from
$\langle E\rangle$, $p = (\gamma-1)(\langle E\rangle - \tfrac12\langle m\rangle^2/\langle\rho\rangle)$, which
differs from $\langle p\rangle$ only by a term quadratic in the velocity, dropped here. The missing flux is

$$
\Delta F \equiv \langle f(p, m, \rho)\rangle - f\big(\langle p\rangle, \langle m\rangle, \langle\rho\rangle\big).
$$

## 2. Second-order expansion inside one cell

Let $\zeta = z - z_k \in [-\Delta z/2, \Delta z/2]$ and write every quantity at the cell centre without a
subscript, with primes for $\partial_z$. The moments of $\zeta$ over the cell are

$$
\langle 1\rangle = 1,\quad \langle\zeta\rangle = 0,\quad \langle\zeta^2\rangle = \frac{\Delta z^2}{12},\quad
\langle\zeta^3\rangle = 0,\quad \langle\zeta^4\rangle = \frac{\Delta z^4}{80}.
$$

The three variables, to second order:

$$
p(\zeta) = p + p'\zeta + \tfrac12 p''\zeta^2, \qquad
m(\zeta) = m + m'\zeta + \tfrac12 m''\zeta^2, \qquad
\rho(\zeta) = \rho + \rho'\zeta + \tfrac12 \rho''\zeta^2 ,
$$

and the reciprocal density, from $1/(\rho(1+a))$ with $a = (\rho'\zeta + \tfrac12\rho''\zeta^2)/\rho$,
$1/(1+a) = 1 - a + a^2 + O(\zeta^3)$:

$$
\frac{1}{\rho(\zeta)} = \frac1\rho\left[1 - \frac{\rho'}{\rho}\zeta
+ \left(\frac{\rho'^2}{\rho^2} - \frac{\rho''}{2\rho}\right)\zeta^2\right] + O(\zeta^3).
$$

Cell means:

$$
\langle p\rangle = p + \frac{\Delta z^2}{24}p'', \qquad
\langle m\rangle = m + \frac{\Delta z^2}{24}m'', \qquad
\langle \rho\rangle = \rho + \frac{\Delta z^2}{24}\rho'' \qquad (+\,O(\Delta z^4)).
$$

### 2a. The flux of the means

Expanding $f$ about the centre state to first order in the $O(\Delta z^2)$ shifts
($\partial_p f = Km/\rho$, $\partial_m f = Kp/\rho$, $\partial_\rho f = -Kpm/\rho^2$):

$$
f(\langle p\rangle, \langle m\rangle, \langle\rho\rangle)
= K\frac{pm}{\rho} + K\frac{\Delta z^2}{24}\left[\frac{m\,p''}{\rho} + \frac{p\,m''}{\rho}
- \frac{p\,m\,\rho''}{\rho^2}\right] + O(\Delta z^4).
$$

### 2b. The mean of the flux, term by term

$f/K = p \cdot m \cdot (1/\rho)$ is a product of three series. Its $\zeta^0$ term is $pm/\rho$. Its $\zeta^1$
terms average to zero. Its $\zeta^3$ and higher terms average to $O(\Delta z^4)$. Its $\zeta^2$ coefficient has
six products:

| # | factor from $p$ | factor from $m$ | factor from $1/\rho$ | product ($\times\zeta^2$) |
|---|---|---|---|---|
| (i)   | $\tfrac12 p''$ | $m$ | $1/\rho$ | $\dfrac{m\,p''}{2\rho}$ |
| (ii)  | $p$ | $\tfrac12 m''$ | $1/\rho$ | $\dfrac{p\,m''}{2\rho}$ |
| (iii) | $p$ | $m$ | $\dfrac1\rho\left(\dfrac{\rho'^2}{\rho^2} - \dfrac{\rho''}{2\rho}\right)$ | $\dfrac{pm\rho'^2}{\rho^3} - \dfrac{pm\rho''}{2\rho^2}$ |
| (iv)  | $p'$ | $m'$ | $1/\rho$ | $\dfrac{p'm'}{\rho}$ |
| (v)   | $p'$ | $m$ | $-\rho'/\rho^2$ | $-\dfrac{m\,p'\rho'}{\rho^2}$ |
| (vi)  | $p$ | $m'$ | $-\rho'/\rho^2$ | $-\dfrac{p\,m'\rho'}{\rho^2}$ |

Multiplying by $\langle\zeta^2\rangle = \Delta z^2/12$:

$$
\langle f\rangle = K\frac{pm}{\rho} + K\frac{\Delta z^2}{12}\left[
\frac{m p''}{2\rho} + \frac{p m''}{2\rho} - \frac{pm\rho''}{2\rho^2}
+ \frac{pm\rho'^2}{\rho^3} + \frac{p'm'}{\rho} - \frac{m p'\rho'}{\rho^2} - \frac{p m'\rho'}{\rho^2}\right]
+ O(\Delta z^4).
$$

### 2c. The difference

The second-derivative terms (i), (ii) and the $\rho''$ part of (iii) are exactly the bracket of 2a
($\tfrac{\Delta z^2}{12}\cdot\tfrac12 = \tfrac{\Delta z^2}{24}$), so they cancel in $\Delta F$:

$$
\Delta F = K\frac{\Delta z^2}{12}\left[\frac{pm\rho'^2}{\rho^3} + \frac{p'm'}{\rho}
- \frac{m p'\rho'}{\rho^2} - \frac{p m'\rho'}{\rho^2}\right] + O(\Delta z^4).
$$

Now substitute $m = \rho u$, $m' = \rho' u + \rho u'$, term by term:

$$
\begin{aligned}
\frac{pm\rho'^2}{\rho^3} &= \frac{p\,u\,\rho'^2}{\rho^2} && \text{(A)}\\
\frac{p'm'}{\rho} &= \frac{u\,p'\rho'}{\rho} + p'u' && \text{(B}_1\text{, B}_2\text{)}\\
-\frac{m p'\rho'}{\rho^2} &= -\frac{u\,p'\rho'}{\rho} && \text{(C)}\\
-\frac{p m'\rho'}{\rho^2} &= -\frac{p\,u\,\rho'^2}{\rho^2} - \frac{p\,u'\rho'}{\rho} && \text{(D}_1\text{, D}_2\text{)}
\end{aligned}
$$

The $u\,\rho_z$ terms cancel, A + D$_1$ = 0, and the $u\,p_z$ terms cancel, B$_1$ + C = 0. Only the terms with $u'$
survive:

$$
\Delta F = K\frac{\Delta z^2}{12}\,u'\left(p' - \frac{p\rho'}{\rho}\right)
= K\frac{\Delta z^2}{12}\,p\,\partial_z u\;\partial_z\ln\frac{p}{\rho} + O(\Delta z^4).
$$

### 2d. The result

$$
\boxed{\;\Delta F = \frac{\gamma}{\gamma-1}\,\frac{\Delta z^2}{12}\;p\;\frac{\partial \ln T}{\partial z}\;\frac{\partial u}{\partial z}\;}
\qquad (\ln(p/\rho) = \ln T + \ln R).
$$

Remarks.
- The result is exact to $O(\Delta z^2)$ for the local state. It is not linearised. Linearisation only entered
  through dropping the kinetic-energy flux and the $\langle p\rangle$ vs $p(\langle E\rangle)$ difference.
- With variable composition the exact form is $\partial_z\ln(p/\rho)$, which is what the code uses, not
  $\partial_z \ln T$ with a fixed $R$.
- The general form for any advected specific quantity $q$ with flux $\rho u q$ follows from the same algebra,
  with $\rho$ a factor rather than a divisor: $\Delta F_q = \frac{\Delta z^2}{12}\,\rho\,\partial_z u\,\partial_z q$.
  For energy $q = h = (E+p)/\rho$, and $\rho\,\partial_z h = K p\,\partial_z\ln(p/\rho)$ to linear order, which
  recovers the box. For a tracer $q = Y$ it gives $\frac{\Delta z^2}{12}\rho\,u_z Y_z$.
- The mass flux $m$ is linear in the state and has no covariance. The momentum fluxes have none at linear order:
  $p$ is linear, while $\rho u^2$ and $\rho u w$ are quadratic in velocity.
- The $x_1$ flux is the analogous average over a horizontal face. Its covariance involves $\partial_x$ of two
  fields, both of which are perturbations about a horizontally uniform background, so it is quadratic and absent
  at linear order. The same holds for the $x_3$ average across an $x_2$ face. Only the vertical average across the
  two horizontal face families matters.

## 3. Its effect: a spurious stable stratification

The scheme supplies $F - \Delta F$, so relative to the exact update the cell energy gains

$$
S_E = +\,\partial_x \Delta F = K\frac{\Delta z^2}{12}\,p_0\,\frac{\mathrm{d}\ln T_0}{\mathrm{d}z}\;\partial_x\partial_z u
$$

to linear order (background $p_0$, $T_0$; $u$ is a perturbation). At fixed $\rho$ and $m$ the energy source is an
internal-energy source, so $\partial_t p = (\gamma-1) S_E$. With $s = c_v\ln p - c_p\ln\rho$,

$$
\partial_t s' \big|_{\rm spur} = c_v\frac{(\gamma-1)S_E}{p_0} = \frac{R\,S_E}{p_0} = \frac{S_E}{\rho_0 T_0}.
$$

The physical buoyancy source in the same equation is $-w\,\mathrm{d}s_0/\mathrm{d}z = c_p\,\varepsilon\,w/T_0$.
A source of the form $c_p\,\varepsilon_{\rm spur}\,w/T_0$ therefore acts as an extra superadiabaticity
$\varepsilon_{\rm spur}$. Close the horizontal derivative with low-Mach continuity,
$\partial_x u = -\rho_0^{-1}\partial_z(\rho_0 w) \approx -\partial_z w$ to leading order. Then for a mode
$w \propto \sin(m_z z)$, $\partial_x\partial_z u = -\partial_z^2 w = m_z^2 w$, and

$$
\varepsilon_{\rm spur} = \frac{S_E}{\rho_0 c_p w}
= \frac{K}{c_p}\frac{\Delta z^2}{12}\,\frac{p_0}{\rho_0}\,\frac{\mathrm{d}\ln T_0}{\mathrm{d}z}\,m_z^2
= \frac{\Delta z^2}{12}\,\frac{\mathrm{d}T_0}{\mathrm{d}z}\,m_z^2
\quad\Longrightarrow\quad
\boxed{\;\varepsilon_{\rm spur} = -\frac{\beta\,m_z^2}{12}\,\Delta z^2\;}
$$

(using $K/c_p = 1/R$, $p_0/(\rho_0 R) = T_0$, $\mathrm{d}T_0/\mathrm{d}z = -\beta$). Its sign is stable for any
atmosphere whose temperature falls with height.

For the T1L deck ($\beta = 1/3.5$ at onset, lowest mode $m_z = \pi$, $\Delta z = 1/n_z$) the leading estimate is
$\varepsilon_{\rm spur} n_z^2 = -\beta\pi^2/12 = -0.235$. Projecting the full expression for $S_E$ onto the actual
compressible eigenmode keeps the $\rho_0$-stratification terms dropped above, and gives $-0.2427$ (mode files
n64 and n128 agree; anelastic continuity of the mode holds to $3\times10^{-4}$). Since $\varepsilon \propto 1/n_z^2$
at fixed physics, the relative onset error collapses on $\varepsilon n_z^2$ as
$\varepsilon_{\rm eff}/\varepsilon - 1 \approx -0.24/(\varepsilon n_z^2)$. The base growth-rate errors follow
that collapse (RESULT_x2cov.md).

## 4. The discrete form as coded (`hydro_forward.cpp`, gated by `SNAPY_X2COV=<factor>`)

The term is computed from the primitive state `w` (ghosts included) after each $x_2$ (and $x_3$) Riemann call and
added to the energy slot of that face flux. Per column, for interior rows $k = i_l..i_u$:

1. Centred vertical derivatives on the (possibly stretched) grid, with $z_k$ = `x1v`:
$$
D_k[\ln T] = \frac{\ln(p/\rho)_{k+1} - \ln(p/\rho)_{k-1}}{z_{k+1} - z_{k-1}}, \qquad
D_k[u] = \frac{u_{k+1} - u_{k-1}}{z_{k+1} - z_{k-1}},
$$
   where $u$ is the face-normal velocity: `IVY` for $x_2$ faces, `IVZ` for $x_3$ faces.
2. The cell value, with $\gamma_k$ from the EOS (`W->A`) and $\Delta z_k$ = `dx1f`:
$$
c_{j,k} = \frac{\gamma_k}{\gamma_k - 1}\,\frac{\Delta z_k^2}{12}\;p_k\;D_k[\ln T]\;D_k[u],
$$
   set to zero in the $x_1$ ghost rows.
3. The face value is the arithmetic mean of the two cells sharing the face. It is added to the energy flux on
   every face of the sweep direction:
$$
F^{E}_{j-1/2,k} \mathrel{+}= \texttt{factor}\cdot\tfrac12\left(c_{j-1,k} + c_{j,k}\right).
$$

Accuracy.
- The centred differences are $O(\Delta z^2)$ accurate, on a term that is itself $O(\Delta z^2)$.
- The face mean is $O(\Delta x^2)$ accurate.
- The coded term therefore removes the $O(\Delta z^2)$ error and leaves $O(\Delta z^2\Delta x^2, \Delta z^4)$.

Conservation. The term enters only as a face flux, so it telescopes, and $\sum E$ changes only through the
boundary faces. At a reflecting $x_2$ wall the ghost normal velocity is mirrored with opposite sign while $p$ and
$\rho$ are mirrored evenly. Then $c_{\rm ghost} = -c_{\rm interior}$ and the wall-face value is zero. In the
periodic T1L direction the sum telescopes exactly.

Placement. The term is added inside the right-hand-side evaluation, so it is applied at every RK stage, and
before any $x_1$ implicit solve, which only couples $x_1$ columns. `factor` = 0, i.e. unset, skips the call
entirely, so the default path is bitwise unchanged.

## 5. Why each test checks it

| test | what the derivation predicts | measured |
|---|---|---|
| One-step tendency, adiabatic background ($\varepsilon = 0$), base | Any $\varepsilon_{\rm eff}$ is numerical. Expected $\varepsilon_{\rm eff} n_z^2 \to -0.243$ | $-0.287 / -0.265 / -0.253$ at $n_z$ 16/32/64 |
| Same, fix minus base | Equals the coded term evaluated independently (python, same seeded state) | $0.2397 / 0.2420 / 0.2426$ vs predicted $0.2397 / 0.2420 / 0.2426$; continuum limit $0.2427$ |
| Same, factor 2 | Linear in the term: (×2) − (×1) = (×1) − base | equal to 4 digits |
| Same, $\Delta t/4$ | A spatial flux error is independent of $\Delta t$ | identical to 5 digits |
| Isothermal background | $\partial_z\ln T_0 = 0 \Rightarrow \Delta F = 0$. The probe must return the exact $\varepsilon n_z^2 = -n_z^2/c_p$ | $-292.5711$ vs exact $-292.5714$, base = fix; $W$ difference after 100 steps $\le 1.8\times10^{-14}$ |
| Hydrostatic rest, 1000 steps | $u \equiv 0 \Rightarrow \Delta F = 0$; rest preserved | max$\lvert u\rvert$ $2.8\times10^{-15}$ (cell), $2.0\times10^{-15}$ (face), base = fix |
| Closed walls, face form, no diffusion, 1000 steps | Flux form ⇒ $E$+PE conserved to round-off while the state changes | per step $\le 3.5\times10^{-16}$; states differ by $10^{-7}$–$10^{-6}$ |
| Growth runs, $\varepsilon$ 1e-3…1e-4 | Error $\approx -0.24/(\varepsilon n_z^2)$ (base) removed; residual of higher order in $\Delta z$ | see RESULT_x2cov.md §3 |
| Strong convection, $\varepsilon = 0.02$ | $\varepsilon_{\rm spur}/\varepsilon$ is small; the fix must not make it worse | see RESULT_x2cov.md §3 |

The fixed residual in the one-step test is $\varepsilon_{\rm eff} n_z^2 = -0.047 / -0.023 / -0.010$, i.e.
$\varepsilon_{\rm eff} \propto n_z^{-3}$. It is of higher order than the removed term. Its origin was not isolated
(unverified; the check would be the same one-step test with the $x_1$ reconstruction order changed).

## 6. The vertically implicit solve (implicit scheme 9) and the term

What the solve does (`HydroImpl::_apply_implicit_correction`, `src/hydro/hydro.cpp`, called after `_div` and the
forcings in `hydro_forward.cpp`). It takes the explicit stage tendency $\Delta U = -\Delta t\,\nabla\cdot F$, which
already contains the $x_2/x_3$ fluxes and hence $\partial_x\Delta F$. It returns, column by column,

$$
\Delta U^{\rm imp} = \left(I - \Delta t\,A_1\right)^{-1}\Delta U, \qquad
A_1 = -\frac{\partial\,(\delta_z F_1)}{\partial U}\Big|_{U^{(s)}} + \frac{\partial S_{\rm grav}}{\partial U}\Big|_{U^{(s)}} ,
$$

where $A_1$ is the Jacobian of the $x_1$ flux divergence (and of gravity), frozen at the stage input $U^{(s)}$.
It needs a full $x_1$ column (`nb1 = 1`) and couples nothing across $x_2$ or $x_3$.

Three consequences.

1. **The term is unchanged by the solve.** $\Delta F$ is computed from the stage input $w$ inside the explicit
   $x_2/x_3$ flux, before the solve. The solve only maps the total tendency through a linear column operator. The
   term enters that operator exactly as every other horizontal tendency does, so no extra code is needed under
   scheme 9 and $\Delta F$ is not re-evaluated on the corrected state.
2. **The implicit part has no covariance of its own to miss.** $A_1$ comes from the $x_1$ flux, i.e. horizontal
   faces. Their face average is over $x$ (and $x_3$), and the corresponding covariance is a product of two
   horizontal derivatives of perturbations: quadratic, absent at linear order (§2d). The $x_1$ flux is also where
   the well-balanced reconstruction acts, and nothing in this note changes it.
3. **On an adiabatic column the solve leaves the entropy part of the tendency untouched.** Linearise about rest
   with $\mathrm{d}s_0/\mathrm{d}z = 0$. The $x_1$ operator (vertical acoustics plus gravity) changes entropy only
   through $-w\,\mathrm{d}s_0/\mathrm{d}z = 0$. So the entropy component of $(I - \Delta t A_1)^{-1}\Delta U$ equals
   that of $\Delta U$, whatever $\Delta t$ (the acoustic Courant number in $z$ may exceed 1). Hence the §2 oracle
   carries over unchanged: under scheme 9 the one-step entropy tendency must still give
   $\varepsilon_{\rm eff}(\text{on}) - \varepsilon_{\rm eff}(\text{off}) = \texttt{factor}\times{\rm pred}$.
   For $\varepsilon \neq 0$ the operator couples $s'$ to $w'$ through the physical buoyancy term, the same for
   this source as for every other.

The test: `x2cov_deck.py onestep --scheme 9` (and `--scheme 0` as the control) on the inviscid box with an
analytic anelastic roll. A 2000-step `run` at $\varepsilon = 0.02$ checks stability and the E+PE budget. The
same `run` on CUDA vs CPU checks the device path. Results: RESULT_x2cov.md §6.
