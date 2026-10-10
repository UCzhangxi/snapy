> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

Source: snapy e2c3f57:study/289-covariance/derivations_draft.md
# snapy #289 — horizontal-flux covariance: derivations, tests, verdict

(draft; numbers in §7–§9 are filled from the runs)

## 0. Notation and assumptions

* $x_1=z$ (vertical, walls), $x_2=x$ (horizontal, periodic), $x_3=y$. Cell $i$ spans $[z_i-\Delta/2,\,z_i+\Delta/2]$, $\Delta=\Delta z=1/n_z$.
* A finite-volume scheme stores **cell averages of conserved variables**
  $\bar U_i=\frac1{V_i}\int_{V_i}U\,dV$ and updates them with **face-averaged fluxes**:
  $$\frac{d\bar U_i}{dt}=-\frac{1}{V_i}\sum_{\text{faces}}A_f\,\hat F_f+\bar S_i,\qquad \hat F_f\equiv\frac1{A_f}\int_{A_f}F(U)\,dA .$$
  This is exact if $\hat F_f$ is the exact face average. Every error below is $\hat F^{\rm scheme}-\hat F$.
* An x2 face of cell $(i,j)$ is the segment $z\in[z_i-\Delta/2,z_i+\Delta/2]$ at $x=x_{j-1/2}$. Its exact face average is an average **over $z$** of the pointwise flux.
* snapy forms primitives from cell averages: $\rho=\bar\rho$, $\mathbf v=\overline{\rho\mathbf v}/\bar\rho$ (mass weighted), $q_n=\overline{\rho q_n}/\bar\rho$, $p=p(\bar\rho,\ \bar E-\tfrac12\overline{\rho\mathbf v}^2/\bar\rho,\ \bar q)$. The x2 reconstruction (WENO5) acts along $x$ only, so it returns the x-point value of these **z-averaged** primitives at the face, up to $O(\Delta x^5)$. LMARS then evaluates the flux pointwise from the face states.
* Linearisation: background at rest, $U_0(z)$; perturbation amplitude $\ll1$; keep terms linear in the perturbation. WENO is taken at its linear weights (the JS weights only add $O(\Delta^3)$ dissipation, which is checked by the time-stepped runs).

## 1. Lemma: averages and covariances over one cell

For a smooth $f$ with Taylor series about the cell midpoint, $f=f_0+f_1s+\tfrac12f_2s^2+\tfrac16f_3s^3+\dots$ with $s=z-z_i$, and a weight $w(z)=w_0(1+a\,s+b\,s^2+\dots)$:

$$\int_{-\Delta/2}^{\Delta/2}s^0\,ds=\Delta,\quad \int s\,ds=0,\quad \int s^2ds=\frac{\Delta^3}{12},\quad \int s^3ds=0,\quad \int s^4 ds=\frac{\Delta^5}{80}.$$

$$\int fw\,ds=w_0\Big[f_0\Delta+\big(b f_0+a f_1+\tfrac12 f_2\big)\frac{\Delta^3}{12}+O(\Delta^5)\Big],\qquad
\int w\,ds=w_0\Big[\Delta+b\frac{\Delta^3}{12}+O(\Delta^5)\Big]$$

$$\boxed{\ \langle f\rangle_w=f_0+\frac{\Delta^2}{12}\Big(a\,f'+\tfrac12 f''\Big)+O(\Delta^4)\ }\tag{L1}$$

Covariance. Apply (L1) to $fg$, $f$ and $g$, using $(fg)''=f''g+2f'g'+fg''$:

$$\langle fg\rangle_w-\langle f\rangle_w\langle g\rangle_w=\frac{\Delta^2}{12}\Big[a(fg)'+\tfrac12(fg)''-g\big(af'+\tfrac12f''\big)-f\big(ag'+\tfrac12g''\big)\Big]+O(\Delta^4)$$
$$\boxed{\ \langle fg\rangle_w-\langle f\rangle_w\langle g\rangle_w=\frac{\Delta^2}{12}\,f'g'+O(\Delta^4)\ }\tag{L2}$$

The weight drops out at this order. On Cartesian $w=1$ ($a=b=0$).

Mass-weighted average. Define $\tilde\phi\equiv\langle\rho\phi\rangle/\langle\rho\rangle$ (what snapy calls the primitive of a specific quantity). By (L2) with $f=\rho$, $g=\phi$:
$$\tilde\phi=\langle\phi\rangle+\frac{\Delta^2}{12}\frac{\rho'\phi'}{\rho}+O(\Delta^4).\tag{L3}$$

Mass-weighted covariance. For two specific quantities $\phi,\chi$:
$$\langle\rho\phi\chi\rangle-\langle\rho\rangle\tilde\phi\tilde\chi .$$
Write $\langle\rho\phi\chi\rangle=\langle(\rho\phi)\chi\rangle=\langle\rho\phi\rangle\langle\chi\rangle+\frac{\Delta^2}{12}(\rho\phi)'\chi'$. Then use (L3) for $\tilde\chi$: $\langle\rho\rangle\tilde\phi\tilde\chi=\langle\rho\phi\rangle\big(\langle\chi\rangle+\frac{\Delta^2}{12}\rho'\chi'/\rho\big)$. Subtract:
$$\boxed{\ \langle\rho\phi\chi\rangle-\langle\rho\rangle\tilde\phi\tilde\chi=\frac{\Delta^2}{12}\Big[(\rho\phi)'-\phi\rho'\Big]\chi'=\frac{\Delta^2}{12}\,\rho\,\phi'\chi'\ }\tag{L4}$$

(L4) is symmetric in $\phi,\chi$ and involves only gradients of specific quantities, so it vanishes if either one is uniform in $z$.

## 2. The x2 fluxes, term by term (Cartesian)

LMARS gives the x2 face flux $\hat F=\bar u\,\rho_{\rm up}\,(\ldots)$, with $\bar u$ the normal velocity. Around rest, $\bar u=O(\epsilon)$, so to linear order every flux is (background specific quantity) × (mass flux $\rho u$), plus the pressure in the normal momentum. $\bar u$'s acoustic term $(p_L-p_R)/(2\rho c)$ is $O(\Delta x^5)$ on smooth data, and $\rho_{\rm up}$ is the reconstructed $\bar\rho$.

| flux | exact face average | scheme | difference (linear) |
|---|---|---|---|
| mass | $\langle\rho u\rangle$ | $\bar\rho\,\tilde u=\langle\rho u\rangle$ | $0$ (mass-weighted primitive makes it exact) |
| normal momentum | $\langle\rho u^2+p\rangle$ | $\bar\rho\tilde u^2+p(\bar U)$ | $0$: $p$ is linear in $\bar E$ at linear order (ideal gas, uniform composition); $\rho u^2$ is quadratic |
| tangential momentum | $\langle\rho u w\rangle$ | $\bar\rho\tilde u\tilde w$ | quadratic |
| tracer $n$ | $\langle\rho u q_n\rangle$ | $\bar\rho\tilde u\tilde q_n$ | (L4): $\frac{\Delta^2}{12}\rho\,u_z\,q_{n,z}$ |
| energy | $\langle\rho u\,h\rangle$, $h=e+p/\rho$ | $\bar\rho\tilde u\,h(\bar U)$ | see below |

Energy. $h=e+p/\rho$. The scheme's specific internal energy is $(\bar E-{\rm KE})/\bar\rho=\tilde e$ (mass weighted, exact by construction). Its $p/\rho$ is $p(\bar U)/\bar\rho$. For an ideal gas of uniform composition, $p=(\gamma-1)\rho e$, so $p(\bar U)=(\gamma-1)\overline{\rho e}=\langle p\rangle$ and $p(\bar U)/\bar\rho=\langle p\rangle/\langle\rho\rangle=\widetilde{(p/\rho)}$, also mass weighted. Hence the scheme's $h$ is $\tilde h$ and (L4) with $\phi=u$, $\chi=h$ gives

$$\boxed{\ \Delta F\equiv\hat F_E-\hat F_E^{\rm scheme}=\frac{\Delta z^2}{12}\,\rho\,\partial_z u\;\partial_z h+O(\Delta z^4)\ }\tag{E1}$$

For the ideal gas $h=c_pT$:
$\rho\,\partial_z h=\rho c_p T\,\partial_z\ln T=\frac{\gamma}{\gamma-1}p\,\partial_z\ln T$. So
$$\Delta F=\frac{\gamma}{\gamma-1}\frac{\Delta z^2}{12}\,p\,(\ln T)_z\,u_z ,$$
which is #289's formula. The coefficient is exactly $1/12$, the second moment of a uniform distribution over a cell, and is not fitted. The "1.4" in the earlier study is $\gamma$: it multiplies $\frac{\Delta z^2}{12}\frac{p}{\gamma-1}(\ln T)_zu_z$.

Linear form on a background $T_0(z)$: $\Delta F=\frac{\Delta z^2}{12}\rho_0c_pT_{0,z}\,u_z$. It is proportional to the background **temperature** gradient, not to $\epsilon$, and is zero on an isothermal background.

Why only the horizontal direction. A covariance needs two factors that both vary **along the averaging direction**. On an x2 face the average runs along $z$, where the background ($h_0$, $q_0$) varies at $O(1)$ and the perturbation varies on the mode scale. So the product of averages misses $\frac{\Delta^2}{12}\phi'\chi'$ at linear order. On an x1 face the average runs along $x$, where the background is constant, so the covariance is (perturbation)×(perturbation) and quadratic. The vertical flux has a different $O(\Delta^2)$ issue (§4.1): point values reconstructed from mass-weighted primitives. That one cancels against the gravity work in the face form.

## 3. Effect on the linear dynamics: a spurious stable layer

Write the energy equation with the scheme's x2 flux, $F^{\rm sch}=F-\Delta F$:
$$\partial_tE'=-\partial_x F_x-\partial_zF_z+(\text{gravity work})+\partial_x\Delta F .$$
Mass is exact (§2), so the spurious term enters the pressure only, $p'=(\gamma-1)(E'-{\rm KE}')$. The entropy perturbation is $s'\equiv p'/(\gamma p_0)-\rho'/\rho_0$ (in units of $c_p$). Then
$$\partial_t s'+w\,s_{0,z}=\frac{\gamma-1}{\gamma p_0}\,\partial_x\Delta F=\frac{\gamma-1}{\gamma p_0}\frac{\Delta z^2}{12}\rho_0c_pT_{0,z}\,\partial_z(\partial_x u).$$
Step by step:
1. $\frac{\gamma-1}{\gamma p_0}\rho_0 c_p=\frac{1}{T_0R}\cdot\frac{(\gamma-1)c_p}{\gamma}\cdot\frac{\rho_0 R T_0}{p_0}=\frac1{T_0}$, using $c_p(\gamma-1)/\gamma=R$ and $p_0=\rho_0RT_0$.
2. RHS $=\frac{\Delta z^2}{12}\frac{T_{0,z}}{T_0}\,\partial_z u_x$.
3. Low-Mach continuity, $\partial_x u=-\rho_0^{-1}\partial_z(\rho_0w)$. To leading order in $\Delta$ and for a mode $w\propto\sin mz$, $\partial_z u_x\simeq-\partial_{zz}w=m^2w$. The $\rho_0$ terms give corrections that the eigen-solver keeps.
4. RHS $\simeq\frac{\Delta z^2m^2}{12}\frac{T_{0,z}}{T_0}\,w=-\frac{\beta m^2\Delta z^2}{12}\frac{w}{T_0}$ for $T_0=1-\beta z$.
5. Exact: $s_{0,z}=\frac{p_{0,z}}{p_0}(\nabla-\nabla_{ad})=-\frac{g}{RT_0}\epsilon$, so $-w\,s_{0,z}=+\frac{g\epsilon}{RT_0}w$ (units $g=R=1$: $\epsilon w/T_0$).
6. Steps 4–5 combined: $\partial_ts'=\frac{w}{T_0}\big(\epsilon-\frac{\beta m^2\Delta z^2}{12}\big)$, i.e.
$$\boxed{\ \epsilon_{\rm eff}=\epsilon+\epsilon_{\rm spur},\qquad \epsilon_{\rm spur}=-\frac{\beta\,m^2\Delta z^2}{12}=-\nabla\,\frac{m^2\Delta z^2}{12}\ (\text{units }g=R=1)\ }$$
For the first mode $m=\pi$: $\epsilon_{\rm spur}n_z^2=-\beta\pi^2/12=-0.2350$ (deck: $\beta=0.2867$ at $\epsilon=10^{-3}$). This matches #289's "$\approx-0.24/N^2$".

Growth-rate error. At fixed $\mu,K$: $\sigma(\epsilon_{\rm eff})$ ⇒ $\frac{\delta\sigma}{\sigma}\simeq a\,\frac{\epsilon_{\rm spur}}{\epsilon}$ with $a=\partial\ln\sigma/\partial\ln\epsilon|_\mu$. For this deck the exact solver gives $a=0.5845$ ($\epsilon=10^{-3}$); $a$ is nearly $\epsilon$-independent: 0.5841 at $10^{-4}$, 0.592 at 0.02. So
$$\frac{\delta\sigma}{\sigma}=-\frac{C}{\epsilon n_z^2},\qquad C=a\,\beta\frac{\pi^2}{12}=0.138\ \ (\text{first order, }m=\pi).$$
With the true eigenfunction (density-weighted, compressible), putting (E1) into the Chebyshev solver as a modified-equation term gives $C=0.1443$ at $n_z=64$ and $0.1518$ at $n_z=32$. The difference at $n_z=32$ is the nonlinearity in $\epsilon_{\rm spur}/\epsilon=0.23$.

## 4. Is ΔF the whole O(Δz²) error? The vertical terms, cell vs face

### 4.1 x1 faces: point values from mass-weighted primitives
On an x1 face the exact flux is the **point** value in $z$ (averaged in $x$, where the background is uniform). WB-WENO reconstructs $p'$, $\rho'$ and $w$ as if the cell values were averages. For $p$ and $\rho$ they are. For $w$ the cell value is $\tilde w=\langle w\rangle+\frac{\Delta^2}{12}\rho_z w_z/\rho$ (L3), so the face value carries that offset:
$$F_m^{\rm sch}=\rho w\big|_f+\delta F_m,\qquad \delta F_m=\frac{\Delta z^2}{12}\rho_{0,z}\,w_z\quad(\text{linear}),\qquad F_E^{\rm sch}=h\,F_m^{\rm sch}.$$
(Checked on a manufactured field: measured $\delta F_m/\Delta^2$ at $z=1/4$ is $-0.1158$ vs $-0.1182$ predicted, flat in $n_z$ from 16 to 128.)

Entropy produced by $\delta F_m$. With $\partial_t\rho'\ni-\partial_z\delta F_m$ and $\partial_tE'\ni-\partial_z(h_0\delta F_m)+W_\delta$, where $W_\delta$ is the part of the gravity work that sees $\delta F_m$:
$$\partial_ts'\ni\frac{\gamma-1}{\gamma p_0}\big[-h_0\partial_z\delta F_m-h_{0,z}\delta F_m+W_\delta\big]+\frac{\partial_z\delta F_m}{\rho_0}=\frac{\gamma-1}{\gamma p_0}\big[-h_{0,z}\delta F_m+W_\delta\big].$$
The $h_0\partial_z\delta F_m$ term cancels the mass term because $\frac{(\gamma-1)h_0}{\gamma p_0}=\frac1{\rho_0}$.
* **face form**: $W_\delta=-g\,\delta F_m$, so the bracket is $-(h_{0,z}+g)\delta F_m=O(\epsilon)\,\delta F_m$. This is harmless (no $1/\epsilon$).
* **cell form**: $W_\delta=0$ (the work is $-g\,\overline{\rho w}$), so the bracket is $-h_{0,z}\delta F_m=O(1)\,\delta F_m$. It is $\propto w_z$, which is nearly orthogonal to the mode, so it is small: $C\approx0.003$ (modified equation $-0.0026$ at $\epsilon=10^{-3},n_z=32$; replica, switching to reconstructing $\rho w$: $-0.0017$).

### 4.2 The gravity-work quadrature (why the face form needs its dz²/12 curvature term)
Face form: $W_i=\phi_i\frac{F_+-F_-}{\Delta}-\frac{\phi_+F_+-\phi_-F_-}{\Delta}=-g\frac{F_++F_-}{2}$ for $\phi=gz$ (since $\phi_i-\phi_\pm=\mp g\Delta/2$). With $F_\pm$ point values of $m=\rho w$:
$$\frac{F_++F_-}{2}=m_i+\frac{\Delta^2}{8}m''+O(\Delta^4),\qquad \langle m\rangle_i=m_i+\frac{\Delta^2}{24}m''\ \Rightarrow\ \frac{F_++F_-}2-\langle m\rangle=\frac{\Delta^2}{12}m''+O(\Delta^4).$$
The exact averaged work is $-g\langle m\rangle$. Without the correction the face form adds $-g\frac{\Delta^2}{12}m''=+g\frac{\Delta^2m^2}{12}m$. By §3's algebra this gives
$$\epsilon_{\rm spur}^{\rm noCurv}=+\nabla_{ad}\frac{m^2\Delta^2}{12}.$$
It has the **opposite sign and nearly the same size** as ΔF's $-\beta\frac{m^2\Delta^2}{12}$, because $\beta=\nabla_{ad}+\epsilon\approx\nabla_{ad}$. snapy's curvature term $H=\frac{\Delta}{12}(m_i-m_{i-1})$ removes it to $O(\Delta^4)$: $(F_++F_-)/2-(H_+-H_-)-\langle m\rangle=-\frac{\Delta^4}{120}m''''$. Replica: face without the correction gives $-0.019$ base (the two errors almost cancel) and $+0.113$ with ΔF.

### 4.3 The wall cells of the face form
snapy zeroes $H$ on the wall faces, which keeps the correction energy-conservative. In the wall cell, with $m=a z+\tfrac12bz^2+\dots$:
$$\frac{F_1+0}{2}-(H_1-0)-\langle m\rangle_0=-\frac{a\Delta}{12}+O(\Delta^3).$$
This is an $O(\Delta)$ work error confined to one cell. It enters the growth rate weighted by the entropy adjoint, which vanishes at a fixed-$T$ wall. So its effect is $O(\Delta^3)/\epsilon$. Replica test: a ghost-consistent wall $H$ (odd ghost $m$) makes face and cell (with $\rho w$ reconstruction) agree to $10^{-4}$ (base $-0.16049$ vs $-0.16062$; +ΔF $-0.01114$ vs $-0.01126$).

### 4.4 What remains after ΔF
Replica, consistent forms (cell, or face with ghost-consistent walls), with ΔF: $-0.0111$ ($n_z$ 32), $-0.00102$ ($n_z$ 64) at $\epsilon=10^{-3}$, and $-0.0101$ at $\epsilon=10^{-4}$, $n_z$ 64. That is $\propto1/\epsilon$ with order $\approx3.4$: an $O(\Delta^3)$–$O(\Delta^4)$ remainder, not $O(\Delta^2)$. The face form's wall error (§4.3) is $+0.008$ at $n_z$ 32 and $+0.001$ at $n_z$ 64. It happens to cancel most of that remainder, which is why "face + ΔF" looks super-convergent ($-0.0031$, $-0.0000$).

LMARS: scaling the acoustic terms of $\bar u$ and $\bar p$ by 0 or 2 changes the rate by $<2\times10^{-5}$. On smooth data both are $O(\Delta^5)$ jump terms, so they cannot carry an $O(\Delta^2)$ error.

## 5. Tracers (item 4)

### 5.1 The flux term
Storage and reconstruction, checked in the code:
* conserved: `u[ICY+n]` is the cell average of the partial density $\rho q_n$, and `u[IDN]` is the **dry** density, so $\bar\rho=$ `u[IDN]` $+\sum_n$ `u[ICY+n]` (`moist_mixture.cpp` and `ideal_moist.cpp` `_cons2prim`; `meshblock.cpp` mass sums);
* primitive: `w[ICY+n] = u[ICY+n]/w[IDN]`, i.e. $\tilde q_n=\overline{\rho q_n}/\bar\rho$, mass weighted (`_cons2prim`; `ideal_moist_impl.h:40`);
* reconstruction: `precon23` acts on `w`, and `reconstruct.cpp:151` reconstructs the `ICY` rows as primitives (mass fractions), not $\rho q$;
* flux: LMARS `FLX(ICY+n) = ubar * rho_face * q_face`, `FLX(IDN) = ubar * rho_face * (1 - sum q_face)` (`lmars_impl.h:50-70`).

So snapy's tracer primitive is the mass fraction $\tilde q_n=\overline{\rho q_n}/\bar\rho$ and the face flux is $\bar u\rho\tilde q_n$. This is the same structure as the energy, where $h$ is formed as $h(\bar p,\bar\rho)$, which is mass weighted for an ideal gas (§2), not as a face average of $h$. By (L4) with $\phi=u$, $\chi=q_n$:
$$\boxed{\ \Delta F_{q_n}=\langle\rho u q_n\rangle-\bar\rho\tilde u\tilde q_n=\frac{\Delta z^2}{12}\,\rho\,\partial_zu\,\partial_zq_n\ }$$
#289's $\langle m q\rangle-\bar m\bar q=\frac{\Delta z^2}{12}m_zq_z$ is the covariance against the **unweighted** $\langle q\rangle$. The scheme's $\tilde q$ is mass weighted, which removes the $\rho_zu\,q_z$ part. In linear form both are $\frac{\Delta^2}{12}\rho_0u_zq_{0,z}$ plus $\frac{\Delta^2}{12}\rho_{0,z}u\,q_{0,z}$; only the first is the scheme's error.

The dry (IDN) flux is $\bar u\rho(1-\sum\tilde q)$, so it misses $-\sum_n\Delta F_{q_n}$. The **total** mass flux stays exact.

How much the choice matters (exact solver, `tracer3.py`): the extra piece in $m_zq_z$, $\frac{\Delta^2}{12}\rho_{0,z}u\,q_{0,z}$, scales with $u$, not $u_z$, so it is nearly orthogonal to the mode. It changes the tracer-induced error by 1–2 % at $n_z=16$ (Earth water $-0.00105\to-0.00104$; heavy vapour $+0.00118\to+0.00116$, $+0.00132\to+0.00130$) and by less than $10^{-5}$ at $n_z\ge32$. The correct form is $\rho u_zq_z$, and the table in §5.3 uses it.

Passive scalars (`src/scalar`) are stored per **dry** mass: $r=\bar s/\bar\rho_d$ (`scalar.cpp:71`), with flux $F_{\rm IDN}\,r_{\rm face}$ (upwind on the hydro dry mass flux). By (L4) with weight $\rho_d$, plus the dry-flux debit, the scheme misses $\frac{\Delta^2}{12}\big[\rho_du_zr_z+r\,\rho u_zq_{d,z}\big]=\frac{\Delta^2}{12}\rho\,u_z\,(q_dr)_z$, the same form in terms of the scalar's total-mass fraction $s/\rho=q_dr$. With the IDN debit coded, the $r\,\rho u_z q_{d,z}$ half is inherited automatically; the $\rho_du_zr_z$ half is not coded (scalars have no buoyancy, so it is only an $O(\Delta z^2)$ transport error).

### 5.2 Effect on compositional buoyancy
$\rho_0\partial_tq'=-\rho_0wq_{0,z}+\partial_x\Delta F_q$ (the mass flux is exact). With $\partial_z u_x\simeq m^2w$:
$$\partial_tq'=-w\,q_{0,z}\Big(1-\frac{m^2\Delta z^2}{12}\Big).$$
The scheme sees every background gradient it advects horizontally ($T$ through $h$, and each $q_n$) shrunk by the same factor $1-m^2\Delta z^2/12$ ($\approx1-0.82/n_z^2$ for the first mode). The compositional part of $N^2$ is weakened by that relative amount, whatever its sign.

### 5.3 Size
Thermal: the shrunk quantity is the whole $\nabla\approx0.29$, against a net $\epsilon$. Compositional: the shrunk quantity is $\epsilon_q$ itself, the compositional term of $N^2$ in the same units, about $(\mu_d/\mu_v-1)\,H\,|q_{0,z}|$. For one scale height of vapour: Earth water $q_b=0.02$ gives $\epsilon_q\approx0.61\times0.02=0.012$, about 4 % of the thermal error. Jupiter water ($q=0.01$, $\mu_d/\mu_v-1=-0.87$) gives $\epsilon_q\approx-0.009$ (stabilising), about 3 % and of opposite sign.

Test (exact solver plus a compositional scalar, molecular-weight buoyancy, $q_0=q_be^{-z}$):

| deck | $n_z$ 16 | 32 | 64 | equivalent $q_{0,z}\times(1-\pi^2\Delta^2/12)$, $n_z$ 32 |
|---|---|---|---|---|
| Earth water, $\epsilon=10^{-3}$ | $-0.00105$ | $-0.00026$ | $-0.00007$ | $-0.00024$ |
| heavy vapour $q=0.01$, $\epsilon_T=0.01$ | $+0.00118$ | $+0.00029$ | $+0.00007$ | |
| heavy vapour, $\epsilon_T=0.0095$ | $+0.00132$ | $+0.00033$ | $+0.00008$ | |

It is second order, matches the "shrunk gradient" reading, and is about 1000× smaller than the thermal term. It is amplified only by $\epsilon_q/\epsilon_{\rm net}$, i.e. in a deck whose net stratification is a near-cancellation of thermal and compositional terms. There the relative error is about $a\,\frac{m^2\Delta^2}{12}\frac{\epsilon_q}{\epsilon_{\rm net}}$.

### 5.4 Matching energy term
The mixture enthalpy is $h=\sum_n q_nh_n(T)$ (dry included). (L4) applied to $\langle\rho u h\rangle$ gives $\frac{\Delta^2}{12}\rho u_z h_z$ with
$$h_z=\underbrace{\sum_n h_n\,q_{n,z}}_{\text{species enthalpy}}+\underbrace{\sum_nq_n c_{p,n}T_z}_{\text{sensible}},$$
i.e. $\Delta F_E=\sum_n h_n\Delta F_{q_n}+\frac{\Delta^2}{12}\rho u_zc_{p,\rm mix}T_z$. So yes, the energy flux needs the species-enthalpy term. It comes automatically if (E1) is coded with the mixture $h=(I+p)/\rho$ from the EOS, as in the patch `snapy_df_coef.diff`. That energy term carries $\sum_n h_n\Delta F_{q_n}$, so the species fluxes must carry $\Delta F_{q_n}$ too (and IDN $-\sum_n\Delta F_{q_n}$). Otherwise the energy moves species enthalpy without the species mass, which is the same kind of inconsistency §6 warns against. The patch now adds $\frac{\Delta^2}{12}\rho\,d_1u_n\,d_1\tilde q_n$ to every `ICY` row and debits IDN under the same `SNAPY_DF_COEF` switch. On the dry T1L deck it is bit-identical to the energy-only patch ($\epsilon=10^{-3}$, $n_z=16$, cell, fix 1: $\sigma=0.01513886$ both; `t1l.py`, `runs/e1e-3_n16_cell_fix1.log`). The species path compiles but has not been run; it needs a moist deck. One caveat: for a mixture, $p(\bar U)\neq\langle p\rangle$, because $p=I\,R_{\rm mix}/c_{v,\rm mix}$ is a ratio of linear forms. That adds
$$-\frac{\Delta^2}{12}\,\rho u\,\frac{I}{\rho}\,(\ln T)_z\,\Big(\frac{R_{\rm mix}}{c_{v,\rm mix}}\Big)_z ,$$
which is $\propto u$ (not $u_z$) and $\propto T_z\,q_z$: second order in the background gradients and nearly orthogonal to the mode. I have not coded it; it needs a moist deck to test.

## 6. Curved grids (item 2, independent check)

Exact face average over an x2 (or x3) face of extent $\Delta r$ in $r$ is weighted by the face's area element in $r$, $w_f(r)$. The cell value is weighted by the cell's volume element, $w_c(r)$, possibly normalised by an approximate volume $V^{\rm code}=(1+\nu)\int w_c$. In (L1) form, $a_f=w_f'/w_f$ and $a_c=w_c'/w_c$. The scheme flux is built from $\bar U=\langle U\rangle_c/(1+\nu)$.

Energy, ideal gas, linear in $u$ (the normal velocity), expanded at the radial midpoint. Step by step, with $c=\gamma/(\gamma-1)$:
* exact: $T=c\langle pu\rangle_f=c\big[pu+\frac{\Delta^2}{12}\big(a_f(pu)'+\tfrac12(pu)''\big)\big]$
* scheme: $S=c\,\overline{\rho u}\,\bar p/\bar\rho=\frac{c}{1+\nu}\langle\rho u\rangle_c\frac{\langle p\rangle_c}{\langle\rho\rangle_c}$.

Expanding each factor with (L1):
$$\langle\rho u\rangle_c=\rho u+\tfrac{\Delta^2}{12}\big(a_c(\rho u)'+\tfrac12(\rho u)''\big),\qquad
\frac{\langle p\rangle_c}{\langle\rho\rangle_c}=\frac p\rho\Big[1+\tfrac{\Delta^2}{12}\Big(a_c\big(\tfrac{p'}p-\tfrac{\rho'}\rho\big)+\tfrac{p''}{2p}-\tfrac{\rho''}{2\rho}\Big)\Big].$$
Multiplying and collecting:
* the $a_c$ terms give $\frac p\rho\rho'u+pu'+up'-up\frac{\rho'}\rho=(pu)'$;
* the second-derivative terms give $\frac p\rho\rho'u'+\tfrac12pu''+\tfrac12up''=\tfrac12(pu)''-pu'(\ln T)'$.

So
$$S=\frac{c}{1+\nu}\Big[pu+\frac{\Delta^2}{12}\big(a_c(pu)'+\tfrac12(pu)''-p\,u'(\ln T)'\big)\Big]$$
$$\boxed{\ T-S=\frac{\Delta r^2}{12}\Big[\underbrace{\rho\,u_r\,h_r}_{\rm thermodynamic}+\underbrace{(a_f-a_c)\,(\rho h u)_r}_{\rm centroid}\Big]+\underbrace{\nu\,\rho h u}_{\rm volume\ normalisation}+O(\Delta r^4)\ }$$
using $c\,p=\rho h$ and $c\,p(\ln T)'u'=\rho h_ru'$.

The same computation for mass ($h\to1$) and tracers ($h\to q$) gives:
$$T_m-S_m=\frac{\Delta r^2}{12}(a_f-a_c)(\rho u)_r+\nu\rho u,\qquad T_q-S_q=\frac{\Delta r^2}{12}\big[\rho u_rq_r+(a_f-a_c)(\rho qu)_r\big]+\nu\rho qu .$$
For momentum, the pressure term picks up $\frac{\Delta r^2}{12}(a_f-a_c)p_r+\nu p$. At rest this is balanced by snapy's geometric source, which uses the same face pressure.

**(a) Spherical polar** ($x_1=r$; θ face area element $r\sin\theta\,dr\,d\phi$, φ face $r\,dr\,d\theta$; volume $r^2\sin\theta$). $w_f=r$, $w_c=r^2$, so $a_f-a_c=\frac1r-\frac2r=-\frac1r$. snapy's spherical volumes and areas are exact ($\int r^2dr$, $\int r\,dr$), so $\nu=0$.
$$\Delta F_E^{\rm sph}=\frac{\Delta r^2}{12}\Big[\rho u_rh_r-\frac1r(\rho hu)_r\Big].$$

**(b) Gnomonic equiangle panel** ($x_1=r$, $x_{2,3}$ equiangular). The metric is $ds^2=dr^2+r^2\gamma_{ab}(\alpha,\beta)d\alpha^ad\alpha^b$ with $\gamma_{ab}$ independent of $r$. Face elements are $r\,dr\times$(angular length) and the volume is $r^2dr\times$(angular area). So $a_f-a_c=-\frac1r$ again. The face-normal velocity is an $r$-independent combination of $v_2,v_3$ (snapy rotates to the local face frame in `prim2local2_/3_`), so $\partial_r$ commutes with it. snapy's `face_area2/3` $=x_{1v}\Delta x_1\times$angular is $\int r\,dr$ exactly. But `cell_volume` uses the trapezoid $\frac12(A_1(r_-)+A_1(r_+))\Delta r$, which is $\big(r^2+\frac{\Delta r^2}4\big)\Delta r$ instead of $\big(r^2+\frac{\Delta r^2}{12}\big)\Delta r$. Hence
$$\nu=\frac{\Delta r^2}{6r^2},\qquad \Delta F_E^{\rm gno}=\frac{\Delta r^2}{12}\Big[\rho u_rh_r-\frac1r(\rho hu)_r+\frac{2}{r^2}\rho hu\Big].$$
The metric factors $\sin\theta$, $\gamma_{ab}$ and $\sqrt\gamma$ depend only on the angles and cancel in the radial expansion. Their own $O(\Delta\alpha^2)$ effects are along-face averages of quantities with no background variation, so they are not linear in the perturbation.

**Which terms vanish on uniform Cartesian**: $a_f=a_c=0$ and $\nu=0$, so only the thermodynamic covariance $\frac{\Delta z^2}{12}\rho u_zh_z$ survives (§2).

**Sizes and what a code should use.** For an atmosphere $r\gg H$, the centroid and volume terms are smaller than the thermodynamic term by about $H/(r\nabla)$ and $(H/r)^2$ ($\sim10^{-3}$ and $10^{-6}$ for Jupiter). They are geometric, not tied to the stratification, and they act on mass, momentum, energy and tracers alike.
* **Do not** add the centroid or volume terms to the energy flux alone. Their mass counterpart would then be missing, and the mismatch produces an $O(1)$ entropy source $\propto\frac{\Delta r^2}{12r}\nabla\cdot((\rho hu)_r-h(\rho u)_r)/(\rho h)$, which is again amplified by $1/\epsilon$.
* Either add them to all conserved fluxes consistently, or leave them out (recommended: they are $O(\Delta r^2/(rH))$).
* The thermodynamic term $\frac{\Delta r^2}{12}\rho\,\partial_r u_n\,\partial_r h$ (plus $\frac{\Delta r^2}{12}\rho\,\partial_ru_n\,\partial_rq_n$ for tracers, with the dry flux debited) is the one that matters. Its discrete form is the same as on Cartesian, with $\Delta r=$`dx1f` and centred $\partial_r$ on `x1v` (the radial centroid on spherical, the midpoint on gnomonic; the difference is $O(\Delta r^2/r)$ in the derivative, so higher order).

## 7. WB x1 reference: the background face-density offset (verifier report)

Script `offset.py` (tables `runs/offset*_Dp_nz.txt`; `offset4_*` are the final ones). Setup: replica of `hydro_ref_x1_impl.h` (CPU path), polytrope $T=1-z/c_p$ with exact cell averages, $\epsilon=0$, depth $D_p=1,2,3,5$ pressure e-folds, $n_z=64,128$. Projected one-step entropy tendency in units of $\epsilon_{\rm spur}n_z^2$ (same measure as `onestep.py`).

### 7.1 What the code does
The WB split reconstructs $\rho-d_{\rm ref}$ and adds back a **face** reference $d_{sf}=p_{sf}\,r_f$, where $r_f$ is the two-cell mean of a smoothed $\rho/p$ (1-4-6-4-1 stencil, clamped at the walls). The added face value is not the reconstruction of $d_{\rm ref}$, so at rest the face density differs from $\rho(z_f)$:
$$\rho_f-\rho(z_f)=\Delta z^2\Big[\frac{p\,f''}{6}+\frac{p'f'}{12}\Big]+O(\Delta z^4),\qquad f=\rho/p\quad(\text{interior}).$$
Measured vs formula, relative to $\rho\,\Delta z^2$ at $z=L/4,L/2,3L/4$: $D_p=1$: $+0.00387/+0.00444/+0.00514$ (formula identical); $D_p=5$: $+0.00519/+0.00887/+0.01851$ ($+0.00519/+0.00885/+0.01842$). The face pressure is exact to $10^{-7}$ or better. The rest state stays balanced (residual $10^{-14}$–$10^{-10}$), because the face pressure, not the face density, is what balances.

### 7.2 The O(Δz) wall layer
Near the walls the clamped 1-4-6-4-1 smoother is not second order. The relative face-density error divided by $\Delta z^2$ **doubles with $n_z$** on faces 1–3 (e.g. bottom face 2: $+0.776\to+1.542$ at $D_p=1$; top face 2: $-1.003\to-2.023$). So it is an $O(\Delta z)$ relative error confined to about three faces at each wall. In the projected tendency this layer, not the interior offset, dominates. Removing only the interior offset barely changes face+ΔF ($-0.00638\to-0.00644$ at $D_p=1$, $n_z=64$).

### 7.3 Effect on the growth-rate measure ($\epsilon n_z^2$, $n_z$ 64 / 128)
| case | $D_p=1$ | 2 | 3 | 5 |
|---|---|---|---|---|
| face base | $-0.2495/-0.2469$ | $-0.2750/-0.2723$ | $-0.3118/-0.3091$ | $-0.3965/-0.3937$ |
| face+ΔF | $-0.0064/-0.0036$ | $-0.0086/-0.0058$ | $-0.0119/-0.0089$ | $-0.0194/-0.0162$ |
| face+ΔF, offset removed | $+0.0074/+0.0038$ | $+0.0080/+0.0041$ | $+0.0089/+0.0045$ | $+0.0109/+0.0056$ |
| faceWC+ΔF (ghost-consistent wall $H$) | $-0.0140/-0.0074$ | $-0.0168/-0.0099$ | $-0.0210/-0.0135$ | $-0.0306/-0.0218$ |
| faceWC+ΔF, offset removed | $-0.00015/-0.00004$ | $-0.00018/-0.00004$ | $-0.00022/-0.00005$ | $-0.00029/-0.00007$ |
| cell+ΔF | $-0.0166/-0.0100$ | $-0.0268/-0.0198$ | $-0.0414/-0.0340$ | $-0.0750/-0.0665$ |
| cell+ΔF, offset removed | $-0.0038/-0.0036$ | $-0.0138/-0.0136$ | $-0.0283/-0.0281$ | $-0.0616/-0.0612$ |

* With consistent walls (faceWC) and ΔF, the WB offset is the **entire** remaining one-step error. Removing it leaves $O(\Delta z^4)$ ($-0.00015\to-0.00004$).
* In the face form as coded, the offset (mostly the wall layer) and the face-form wall-cell work error of §4.3 have opposite signs and partly cancel. That is why "face+ΔF" looks small.
* In the cell form, a depth-growing $O(\Delta z^2)$ term remains after the offset is removed ($-0.004\to-0.061$ from $D_p=1$ to 5, flat in $n_z$). Reconstructing $\rho w$ instead of $w$ in x1 (`x1_mom`) removes most of it (cell+ΔF+mom, fix C: $-0.0012$ at $D_p=1$, $-0.0168$ at $D_p=5$). This is the per-cell $w=\langle m\rangle/\langle\rho\rangle$ conversion term ("V"), which grows with depth because $\rho_z/\rho$ does.

### 7.4 Fixes
* **FIX** ($d_{sf}$ = the same WENO reconstruction of $d_{\rm ref}$): the interior offset vanishes to roundoff, but the wall faces keep the $O(\Delta z)$ error (it doubles with $n_z$). faceWC+ΔF FIX: $+0.0065/+0.0033$, i.e. the wall layer is still there.
* **Fix C** = FIX + linear-exact wall closure of the smoother (`rs_wall_exact`) + smooth (quartic-extrapolated) ghosts for $d_{\rm ref}$. Then the face density is $R(\rho-d_{\rm ref})+R(d_{\rm ref})=R(\rho)$, a consistent reconstruction of the full density. The rest state stays balanced ($10^{-14}$–$10^{-10}$). The interior error is $<10^{-7}\rho\,\Delta z^2$. Faces 1–2 keep a ghost-closure error, but it is the same reconstruction the perturbation sees, so it is harmless. Projected: faceWC+ΔF C $=-0.00015/-0.00004$ ($D_p=1$) and $-0.00027/-0.00007$ ($D_p=5$), identical to "offset removed". face+ΔF C $=+0.0074/+0.0038$: the face-form wall-cell work error of §4.3 is then exposed, so fix C should go together with a ghost-consistent wall curvature term. cell+ΔF C = cell+ΔF with the offset removed; the V term remains.
* `predict_offset.py` reproduces the offset's projected contribution analytically: the interior formula plus wall-layer face coefficients $(-1/480,\,7/192,\,1/480)\,\Delta z\,(\ln f)_z\,\rho$.

## 8. Item 2(c): curved-grid reference numbers
`curved.py` (output `runs/curved.txt`): an adiabatic column at $R_b=5H$. (A) Single-face flux test: exact minus scheme, divided by $\Delta r^2$, after subtracting the predicted §6 terms. The residual falls by 4× per doubling (for example sph cell 0: $-2.24\times10^{-4}\to-5.17\times10^{-5}\to-1.24\times10^{-5}$), so the §6 formulas (thermodynamic + centroid $(a_f-a_c)$ + gnomonic trapezoid-volume $\nu$) are complete at $O(\Delta r^2)$ for energy and mass. (B) Projected $\epsilon_{\rm spur}n_z^2$: base $-0.2417$ (spherical, $R=5H$) vs $-0.2465$ (Cartesian). With the Cartesian ΔF the residual is $+0.0006$; with the exact curved term it is $0$. So the Cartesian form of ΔF captures the curved case to about 0.3 % of the base error.

## 9. Item 5 (completeness): status
Open. The candidates under derivation for a remaining $O(\Delta z^2)$ energy-row residual are the WB offset (§7), V through $h(\bar p,\bar\rho)$, gravity work with point vs averaged $w$, and the x1 energy flux with the WB perturbation reconstruction.
