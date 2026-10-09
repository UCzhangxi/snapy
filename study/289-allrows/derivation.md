# Issue #289, all x2/x3 rows: the centroid shift for mass, momentum and tracers, and what it does to hydrostatic balance

**Base.** Fork `happysky19/snapy`, branch `fix/289-flux-covariance-x3-curved` @
`e7f99040834c5be3e97ee9e952d28453dfd0b7d4` (parent `807cfd8`, on `main`
`117e449`). Every `file:line` below is at `117e449` (`src/` is byte-identical on
this branch). The energy-row result of e7f9904
(`docs/derivations/289-covariance-x3-curved.md` §2A, its eq. 2A.9) is used and
not re-derived.

**Scripts** (this directory; about 1.5 min of CPU in total, almost all of it sympy):

| script | what it checks |
|---|---|
| `symbolic_rows.py` | sympy: exact moments; the per-row correction to $O(h^4)$ for mass, tracers and momentum (normal and transverse); the pressure piece; the exact pressure source integrals on both grids |
| `rest_balance.py` | numpy replica of snapy's discrete operators: the rest-state residual of the x2/x3 momentum rows on spherical-polar and on a gnomonic panel, with and without the correction; the uniform-tracer test |
| `quad_source.py` | Gauss–Legendre: snapy's source weight $\bar p_V$ against the face average $\langle p\rangle_A$ the exact source needs |

---

## 0. Verdict

1. **Every x2/x3 row** gets the same two-term correction. For a row whose flux is $\rho u_n\varphi$: $\Delta F_\varphi=\sigma_c^2\,\rho\,\partial_1u_n\,\partial_1\varphi-\delta\,\partial_1(\rho u_n\varphi)$, plus $-\delta\,\partial_1p$ in the normal-momentum row (eqs. 2.4–2.9). The mass row has no covariance term.
2. **Spherical-polar: balance FAILS** in the $\theta$ row. Adding the shift to the flux alone leaves the rest-state tendency $+\delta\,D_1p\;c_{1i}c_{1j}$. The $\phi$ row stays bitwise exact.
3. **Gnomonic panel: balance FAILS** in both the $\alpha$ and $\beta$ rows, by $+\delta\,D_1p$ times `x_ov_rD` and `y_ov_rC`. The non-orthogonal $g_{23}$ cross terms still cancel identically.
4. **The fix is the same on both grids.** The geometric source uses the weight $p\to p-\delta\,D_1p$, with the same $\delta_i$ and the same $D_1$ as the flux. This is the area-measure weight, because every geometric source is $\tfrac1r\times$stress and so integrates against $r\,dr$. With it the balance is back to round-off. snapy's current sources already carry the same $O(\Delta r^2)$ mismatch: today's balance holds only because flux and source make the same error.
5. **Tracers.** A uniform $q$ stays uniform. With the discrete product rule, $\Delta F_q=q\,\Delta F_\rho$ bitwise. If you correct the mass row without the tracer rows, $q$ drifts at $O(\delta)$. The Cartesian $(\Delta z^2/12)\,\rho\,\partial_zu_n\,\partial_zq$ is the $\sigma^2$ term of the same row with $\delta=0$.

---

## 1. Setting

### 1.1 The two measures

For an x2 or x3 face on either curved grid, `face_area2/3` carry the radial
factor $\int_{r_-}^{r_+}r\,dr$. That is `0.5*(rp^2-rm^2)` in
`spherical_polar.cpp:185-198`, and `x1v*dx1f` in `gnomonic_equiangle.cpp:197-203`
with arithmetic `x1v` (`:36`). The angular factor does not depend on $r$. A cell
average is taken over $r^2\,dr$. With $h=r_+-r_-$ and $\bar r=\tfrac12(r_-+r_+)$,
the exact moments (S1 in `symbolic_rows.py`) are

$$
r_c=\frac{12\bar r^2+h^2}{12\bar r},\qquad
r_v=\frac{3\bar r(4\bar r^2+h^2)}{12\bar r^2+h^2},\qquad
\delta\equiv r_v-r_c=\frac{h^2(12\bar r^2-h^2)}{12\bar r(12\bar r^2+h^2)}=\frac{h^2}{12\bar r}+O(h^4),
\tag{1.1}
$$

$$
\sigma_c^2=\frac{h^2}{12}\Big(1-\frac{h^2}{12\bar r^2}\Big),\qquad
\sigma_c^2-\sigma_v^2=\frac{11\,h^4}{720\,\bar r^2}+O(h^6).
\tag{1.2}
$$

Write $\langle\cdot\rangle_A$ for the face average (weight $r$) and
$\overline{(\cdot)}$ for the cell average (weight $r^2$).

### 1.2 What the code evaluates (reading A4 of e7f9904)

The face state is read as the cell state, as in e7f9904 §4 A4. snapy stores
conserved averages: $\bar\rho$, $\overline{\rho u}$, $\overline{\rho q_n}$,
$\bar E$. Its primitives are therefore Favre averages,
$\tilde u=\overline{\rho u}/\bar\rho$ and $\tilde q=\overline{\rho q}/\bar\rho$.
The total density is dry plus species, $\rho=$ `cons[IDN]` $+\sum$ `cons[ICY+n]`
(`equation_of_state.cpp:229`). LMARS (`lmars_impl.h:50-76`) forms every
advective row as `ubar * rho_up * phi_up`:

| row | flux | $\varphi$ |
|---|---|---|
| `IDN` (dry mass) | $\rho u_n(1-\sum q)$ | $1-\sum_n q_n$ |
| `ICY+n` (species) | $\rho u_n q_n$ | $q_n$ |
| normal momentum `ivx` | $\rho u_n u_n+\bar p$ | $u_n$ |
| transverse momentum `ivy`, `ivz` | $\rho u_n u_t$ | $u_t$ (local frame) |
| energy `IPR` | $\rho u_n h$ | $h$ |

So the code flux of row $\varphi$ is $\bar\rho\,\tilde u_n\,\tilde\varphi$,
while the finite-volume flux needs $\langle\rho u_n\varphi\rangle_A$.

### 1.3 Discrete operators and sign

$D_1f_i=(f_{i+1}-f_{i-1})/(\texttt{x1v}_{i+1}-\texttt{x1v}_{i-1})$ on interior
x1 cells, and zero on the first and last cell. This is exactly e7f9904's
stencil. $\delta_i$ is `radial_face_centroid_shift_` (eq. 1.1, exact form).

**Sign.** The corrected flux is $F_{\rm code}+\Delta F$ with
$\Delta F\ni-\delta\,D_1F$, the sign of e7f9904's energy term. "Adding
$\delta\,D_1p$" in the brief means this term. The balance conclusions below
depend only on applying it to the flux and not to the source. They do not
depend on its sign.

---

## 2. The correction, row by row

### 2.1 One lemma covers every row

Expand each field about $r_c$. A cell average sits a distance $\delta$ off the
face centroid, and its second moment equals $\sigma_c^2$ to $O(h^4)$ (eq. 1.2).
So, as in e7f9904 eq. 2A.4,

$$
\bar a=a_c+\delta\,a'+\tfrac12\sigma^2a''+O(h^4),\qquad
\langle a\rangle_A=a_c+\tfrac12\sigma^2a''+O(h^4).
\tag{2.1}
$$

**Linear rows.** For any $a$:

$$
\langle a\rangle_A-\bar a=-\delta\,a'+O(h^4).
\tag{2.2}
$$

**Favre product.** Let $m=\rho u_n$ and $s=\rho\varphi$. Apply (2.1) to the
quotient $\bar m\bar s/\bar\rho$, exactly as e7f9904 did for (2A.6)–(2A.8) with
$p\to s$. Use $\langle ms/\rho\rangle_A=\rho u_n\varphi|_c+\sigma^2(\ldots)$ and
collect terms:

$$
\langle\rho u_n\varphi\rangle_A-\bar\rho\,\tilde u_n\tilde\varphi
=\sigma^2\,s\,u_n'\,[\ln(s/\rho)]'-\delta\,(\rho u_n\varphi)'
=\boxed{\;\sigma_c^2\,\rho\,\partial_1u_n\,\partial_1\varphi\;-\;\delta\,\partial_1(\rho u_n\varphi)\;}+O(h^4).
\tag{2.3}
$$

(2.3) is linear in $\varphi$ for fixed $(\rho,u_n)$. Symbolic check: S2b in
`symbolic_rows.py`, with generic quartic profiles for $\rho,u,\varphi$.

### 2.2 The rows

Each row below is (2.3) with its own $\varphi$. The pressure piece comes from
(2.2).

* **Total mass** ($\varphi=1$):
  $$\Delta F_\rho=-\delta\,\partial_1(\rho u_n).\tag{2.4}$$
  There is no covariance term, because the mass flux is linear in the conserved
  variables (S2a).
* **Species $n$** ($\varphi=q_n$):
  $$\Delta F_{q_n}=\sigma_c^2\,\rho\,\partial_1u_n\,\partial_1q_n-\delta\,\partial_1(\rho u_nq_n).\tag{2.5}$$
* **Dry mass `IDN`** ($\varphi=1-\sum q_n$):
  $$\Delta F_d=-\sigma_c^2\,\rho\,\partial_1u_n\,\partial_1\!\textstyle\sum_nq_n-\delta\,\partial_1\big(\rho u_n(1-\sum_nq_n)\big).\tag{2.6}$$
  By linearity, $\Delta F_d+\sum_n\Delta F_{q_n}=\Delta F_\rho$ exactly.
* **Transverse momentum** ($\varphi=u_t$, every component that is not normal,
  including $u_r$ on an x2/x3 face):
  $$\Delta F_{t}=\sigma_c^2\,\rho\,\partial_1u_n\,\partial_1u_t-\delta\,\partial_1(\rho u_nu_t).\tag{2.7}$$
* **Normal momentum** ($\varphi=u_n$, plus pressure). S2c and S2d check this:
  $$\Delta F_{n}=\sigma_c^2\,\rho\,(\partial_1u_n)^2-\delta\,\partial_1(\rho u_n^2)\;-\;\delta\,\partial_1p.\tag{2.8}$$
  The pressure has **no covariance term but does have the centroid shift**, by
  (2.2).
* **Energy** (e7f9904 eq. 2A.9, enthalpy part):
  $\kappa[\sigma_c^2\,p\,(\ln p/\rho)'\,u_n'-\delta(p\,u_n)']$. This is (2.3)
  with $\varphi=h$.

**Caveat on the pressure: cons→prim.** (2.8) reads $\bar p$ as the cell average
of $p$. snapy does not store that. It forms $p$ from
$\bar E-\tfrac12\overline{\rho u}^2/\bar\rho$, and the kinetic part of that is a
Favre product. For an ideal gas, S2e gives

$$
\langle p\rangle_A-p_{\rm code}=-\delta\,\partial_1p-\frac{\gamma-1}{2}\,\sigma_c^2\,\rho\,|\partial_1\mathbf u|^2+O(h^4).
\tag{2.9}
$$

The extra term is $O(M^2)$ relative to $p$, the same order as
$\sigma^2\rho(u_n')^2$ in (2.8). It is zero at rest, so the balance question
below does not depend on it. Keep it if you keep $\sigma^2\rho(u_n')^2$. A
moist EOS with $\gamma(q)$ adds further covariances of the same kind, through
$\partial^2p/\partial I\,\partial q$.

### 2.3 The Cartesian limit, and where the tracer covariance sits

Cartesian has $\delta\equiv0$ (`face_centroid_shift_x1` returns zeros) and
$\sigma^2=\Delta z^2/12$. So (2.5) becomes

$$
\Delta F_q^{\rm Cart}=\frac{\Delta z^2}{12}\,\rho\,\partial_zu_n\,\partial_zq .
$$

This is the Cartesian tracer covariance. It is the first term of the same row.
On a curved grid the same slot holds $\sigma_c^2$ from (1.2), and the row gains
the $-\delta\,\partial_1(\rho u_nq)$ term. The mass and pressure pieces vanish
in Cartesian.

---

## 3. A uniform tracer stays uniform

**Continuous.** Put $q_n\equiv$ const in (2.5). Then $\partial_1q_n=0$ and
$\partial_1(\rho u_nq_n)=q_n\partial_1(\rho u_n)$, so

$$
\Delta F_{q_n}=q_n\,\Delta F_\rho,\qquad \Delta F_d=(1-\textstyle\sum q)\,\Delta F_\rho .
$$

S2f checks this against the exact face defect: the ratio is exactly 1. Since
LMARS already gives $F_{q_n}=q_nF_\rho$ for uniform $q$, the corrected fluxes
keep $F_{q_n}+\Delta F_{q_n}=q_n(F_\rho+\Delta F_\rho)$. The update of
$\rho q_n$ is then $q_n$ times the update of $\rho$, and $q_n$ stays put.

**Discrete, bitwise.** Use the exact discrete product rule,
$D_1(ab)=\mathrm{avg}(b)\,D_1a+\mathrm{avg}(a)\,D_1b$ with
$\mathrm{avg}f_i=\tfrac12(f_{i+1}+f_{i-1})$, which is an algebraic identity.
Write

$$
\Delta F_\varphi=\mathrm{avg}(\varphi)\,\Delta F_\rho+\big(\sigma_c^2\rho\,D_1u_n-\delta\,\mathrm{avg}(\rho u_n)\big)\,D_1\varphi .
\tag{3.1}
$$

For bitwise-uniform $q$, $D_1q=0$ and $\mathrm{avg}(q)=q$ exactly in floating
point. So $\Delta F_q=q\,\Delta F_\rho$ bitwise. Taking $D_1$ of the product
directly is correct as well, but agrees only to round-off.

**Numerical** (`rest_balance.py`, `tracer_test`). Spherical-polar $\theta$
sweep, smooth $u_\theta(r,\theta)\neq0$, two species $q=(0.013,\,0.0007)$, one
explicit step:

| correction applied | $\max\lvert q^{n+1}-q\rvert/q$ |
|---|---|
| none | 4.0e-16, 3.1e-16 |
| mass rows only (tracer rows **not** corrected) | **6.3e-05, 6.3e-05** |
| all rows, naive $D_1$(product) | 4.0e-16, 3.1e-16 |
| all rows, split form (3.1) | 4.0e-16, 3.1e-16 |

Correcting the mass row without the tracer rows breaks uniformity at $O(\delta)$.
The tracer rows must carry the shift whenever the mass row does.

---

## 4. Hydrostatic rest state: the momentum rows

### 4.1 What survives at rest

Take $\mathbf u\equiv0$ and $p=p(r)$, $\rho=\rho(r)$. Every term of
(2.4)–(2.7), of the advective part of (2.8), and of the energy correction
carries $u_n$ or $D_1u_n$. These are exactly $0.0$ in floating point, so those
corrections vanish bitwise (`rest_zero_rows` prints zeros). The x1-momentum row
is also untouched: an x2/x3 face's `IVX` row is $\rho u_nu_r\equiv0$.

**The only change at rest is $-\delta\,D_1p$ in the normal-momentum row of
x2/x3 faces.** At rest, LMARS gives `pbar = (pL+pR)/2` (`lmars_impl.h:38`, with
$u_L=u_R=0$). With $p$ uniform along the face direction that equals the cell
$p_i$, to round-off.

Write $P_i$ for whatever per-$i$ scalar appears as "the pressure". The balance
of a horizontal momentum row at rest has the form

$$
-\frac{1}{V}\Big[A_{j+\frac12}\,\Theta_{j+\frac12}\,P^{\rm flux}_i-A_{j-\frac12}\,\Theta_{j-\frac12}\,P^{\rm flux}_i\Big]+G_{ji}\,P^{\rm src}_i=0,
\tag{4.1}
$$

where $\Theta$ is an $r$-independent angular/metric factor and $G$ is built so
that $G=\Delta_j(A\Theta)/V$. (4.1) holds for any $P$ **iff
$P^{\rm flux}_i=P^{\rm src}_i$**. It is linear in $P$, separately at each $i$.

Today both are the cell $\bar p_i$, so (4.1) holds. "Correct the flux only"
sets $P^{\rm flux}=\bar p-\delta D_1\bar p$ but leaves $P^{\rm src}=\bar p$.
The rest of §4 works this through on each grid.

### 4.2 Spherical-polar, step by step

**Geometry** (`spherical_polar.cpp:80-101`, `:185-211`):

$$
A_2=\tfrac12(r_+^2-r_-^2)\,\sin\theta_f\,\Delta\phi,\qquad
V=\tfrac13(r_+^3-r_-^3)\,(\cos\theta_--\cos\theta_+)\,\Delta\phi,
$$
$$
c_{1i}=\frac{\tfrac12(r_+^2-r_-^2)}{\tfrac13(r_+^3-r_-^3)},\qquad
c_{1j}=\frac{\sin\theta_+-\sin\theta_-}{\cos\theta_--\cos\theta_+},
\qquad\Rightarrow\qquad \frac{A_{2,j+\frac12}-A_{2,j-\frac12}}{V}=c_{1i}\,c_{1j}.
\tag{4.2}
$$

**$\theta$ row (`IVY`).** The flux is $F_2=P^{\rm flux}$, and the coordinate is
orthogonal, so `flux2global2_` is the identity. The source is
`div[IVY] -= coord_src1_i*coord_src1_j*m_pp` with
$m_{pp}=\rho v_\phi^2+p\to P^{\rm src}$ at rest (`:251-255`). So

$$
\dot{(\rho v_\theta)}=-\frac{A_{2+}P^{\rm flux}-A_{2-}P^{\rm flux}}{V}+c_{1i}c_{1j}P^{\rm src}
=c_{1i}c_{1j}\,(P^{\rm src}-P^{\rm flux}).
$$

* Baseline: $P^{\rm src}=P^{\rm flux}=\bar p$, so the tendency is 0 to
  round-off.
* Flux corrected only:
  $$\dot{(\rho v_\theta)}=+\,\delta_i\,(D_1p)_i\;c_{1i}c_{1j}\neq0.\tag{4.3}$$
  The relative size is $\delta|p'|/p\approx h^2/(12\,r\,H_p)$. As an
  acceleration this is $-\delta\,g\,\cot\theta/r$: a spurious, pole-ward or
  equator-ward, $O(h^2)$ force in a resting atmosphere.

**$\phi$ row (`IVZ`).** `face_area3` is the same array at $k$ and $k+1$ (it is
`expand`ed over x3, `:193-198`), and there is no pressure source in this row.
So $(A_3P-A_3P)/V\equiv0$ **bitwise**, with or without the correction, because
$P$ is the same scalar on both faces. The other $\phi$-row source,
`coord_src1_i*coord_src2_j*(A2 F2[IVZ] …)` (`:267-274`), is built from the x2
flux of $\phi$-momentum. That flux is $\rho u_\theta u_\phi\equiv0$ at rest. In
motion it inherits the corrected flux automatically, so it is area-consistent
by construction.

**Spherical-polar verdict.** The balance fails in the $\theta$ row and holds in
the $\phi$ row.

### 4.3 Gnomonic panel (non-orthogonal metric), step by step

**Geometry** (`gnomonic_equiangle.cpp:18-133`, `:189-210`):

$$
A_2=(\bar r h)\,\Lambda_2(\alpha_f,\beta),\qquad
A_3=(\bar r h)\,\Lambda_3(\alpha,\beta_f),\qquad
\texttt{x\_ov\_rD}=\frac{\Delta_j(A_2\,s_2)}{V},\qquad
\texttt{y\_ov\_rC}=\frac{\Delta_k(A_3\,s_3)}{V},
$$

Here $\bar r h=\int r\,dr$ exactly. $\Lambda_2$ and $\Lambda_3$ are the
great-circle arcs `dx3f_ang_face2_kj` and `dx2f_ang_face3_kj`. $s_{2,3}$ are
`sine_face2/3_kj`, and $c_{2,3}=$ `cosine_face2/3_kj` $=g_{23}$ on the face.
$V$ is the trapezoid `cell_volume`. Every angular factor is independent of $r$.

**x2 face, at rest.** In the local frame the flux rows are
$(t_{xx},t_{xy},t_{xz})=(0,P,0)$. `flux2global2_` (`:325-351`) uses
$g_{22}=g_{33}=1$, $g_{23}=c_2$, $g^{22}=1/s_2^2$:

$$
\begin{aligned}
f_y&=\sqrt{g^{22}}\,P=P/s_2, & f_z&=-\sqrt{g^{22}}\,\frac{g_{23}}{g_{33}}\,P=-\frac{c_2}{s_2}P,\\
F_2[\texttt{IVY}]&=f_y+f_z\,c_2=\frac{P}{s_2}(1-c_2^2)=P\,s_2, &
F_2[\texttt{IVZ}]&=f_z+f_y\,c_2=-\frac{c_2}{s_2}P+\frac{c_2}{s_2}P=0 .
\end{aligned}
\tag{4.4}
$$

**x3 face, at rest.** The rows are $(0,0,P)$. `flux2global3_` (`:354-380`)
gives the mirror image: $F_3[\texttt{IVY}]=0$ and $F_3[\texttt{IVZ}]=P\,s_3$.

**Non-orthogonality cancels identically.** Each cross-row term vanishes for
*any* $P$, because (4.4) is linear in $P$ and the cancellation is in the
coefficients. So `IVY` receives only the x2 pressure, and `IVZ` only the x3
pressure. With the sources `src2 = x_ov_rD*(p+…)` and `src3 = y_ov_rC*(p+…)`
(`:430-438`):

$$
\dot{(\rho v_\alpha)}=-\frac{\Delta_j(A_2s_2)}{V}P^{\rm flux}+\texttt{x\_ov\_rD}\,P^{\rm src}=\texttt{x\_ov\_rD}\,(P^{\rm src}-P^{\rm flux}),
\qquad
\dot{(\rho v_\beta)}=\texttt{y\_ov\_rC}\,(P^{\rm src}-P^{\rm flux}).
$$

* Baseline: 0 to round-off.
* Flux corrected only:
  $$\dot{(\rho v_\alpha)}=+\delta\,D_1p\;\texttt{x\_ov\_rD},\qquad \dot{(\rho v_\beta)}=+\delta\,D_1p\;\texttt{y\_ov\_rC}.\tag{4.5}$$
  On a panel both are non-zero. They vanish only on the panel's centre lines,
  where $\Delta_j(A_2s_2)=0$ by symmetry.

**Frame.** Is the correction added to the local normal row before
`flux2global`, or to the global rows after it, as e7f9904 does for `IPR`? It
makes no difference: the transform is linear and independent of $r$, so it
commutes with $\delta_iD_1$. `rest_balance.py` case `B_global` matches case `B`.

**Gnomonic verdict.** The balance fails in both horizontal rows. The
non-orthogonal metric neither causes nor cures it.

### 4.4 The source weight that restores exact balance

**What the exact source needs.** In both grids the momentum components are
unit-normalised (physical). So every geometric source is $1/r$ times a
component of the stress $T^{ab}=\rho u^au^b+p\,g^{ab}$:

* spherical $\theta$: $(p+\rho u_\phi^2)\cot\theta/r-\rho u_ru_\theta/r$;
* gnomonic $\alpha$: $(p/r)\,\partial_\alpha\ln\sqrt g+\ldots$, with $\sqrt g=r^2s(\alpha,\beta)$.

Integrated over the cell with $dV\propto r^2dr$, the $1/r$ leaves $r\,dr$.
For $p=p(r)$, S3 checks the spherical identity symbolically for a generic quartic $p(r)$, and S4 checks that the radial factor of the continuous gnomonic source is $p\,r$:

$$
\int_Vp\,\frac{\cot\theta}{r}\,dV=\langle p\rangle_A\,\big(A_{2+}-A_{2-}\big),
\qquad
\int_V\frac{p}{r}\,\partial_\alpha\ln\sqrt g\;dV=\Big[\int p\,r\,dr\Big]\int\!\!\int\partial_\alpha s\,d\alpha\,d\beta .
\tag{4.6}
$$

The exact source carries the **face** average $\langle p\rangle_A$, the same
average as the exact x2/x3 flux. So the area-consistent source weight is

$$
\boxed{\;P^{\rm src}_i=\langle p\rangle_A\big|_i=\bar p_i-\delta_i\,(D_1\bar p)_i+O(h^4)\;}
\tag{4.7}
$$

By (2.2), with the same $\delta_i$ and the same $D_1$ stencil and edge mask as
the flux correction. In the code's own terms:

```
spherical_polar.cpp:251-255   m_pp  = rho*vz^2 + p   ->   rho*vz^2 + (p - delta*D1(p))
gnomonic_equiangle.cpp:430-438 src2 = x_ov_rD*(pr - delta*D1(pr) + ...)
                               src3 = y_ov_rC*(pr - delta*D1(pr) + ...)
```

**Why the balance is then exact to round-off.** (4.1) holds for any $P$ once
$P^{\rm flux}_i=P^{\rm src}_i$. Here both are
$\bar p_i-\delta_iD_1\bar p_i$. They are formed from the same cell values: at
rest the face `pbar` equals the cell $p$ to round-off. So the residual is
round-off, exactly as in the baseline. The argument is identical on both grids,
and the non-orthogonal terms drop out as before (4.4).

**Cost of the corrected weight.** It is the cell-centred $D_1p$ that the flux
correction already evaluates per face.

The dynamic parts of the source weights should get the matching correction too,
for consistency. These are $\rho v_\phi^2$ in spherical, and
$\rho v_3^2\sin^2$ and $\rho v_2^2\sin^2$ in gnomonic. The correction is the
(2.3) correction of the same stress component:
$\langle\rho v^2\rangle_A=\bar\rho\tilde v^2+\sigma_c^2\rho(v')^2-\delta(\rho v^2)'$.
They are zero at rest, so they do not affect the balance.

### 4.5 snapy's current sources already carry the same mismatch

By (4.6), the exact $\theta$, $\alpha$ and $\beta$ pressure sources need
$\langle p\rangle_A$. snapy multiplies the cell value $\bar p_V$. That alone is
off by $\delta p'\times G=O(h^2)$, and `quad_source.py` confirms it:

| shell | $h$ | $\lvert\bar p_V-\langle p\rangle_A\rvert/p$ (current) | ratio | $\lvert\bar p_V-\delta D_1\bar p_V-\langle p\rangle_A\rvert/p$ (4.7) | ratio |
|---|---|---|---|---|---|
| $R_0=1$, $H_p=0.1$ | 0.0313 | 7.76e-04 | 3.82 | 2.10e-05 | 15.1 |
| | 0.0156 | 1.99e-04 | 3.91 | 1.37e-06 | 15.4 |
| | 0.0039 | 1.26e-05 | 3.98 | 5.52e-09 | 15.8 |
| $R_0=10$, $H_p=0.1$ | 0.0313 | 8.09e-05 | 3.96 | 1.53e-06 | 16.1 |
| | 0.0039 | 1.27e-06 | 4.00 | 3.74e-10 | 16.0 |

The current flux carries the same error, with the opposite sign in the
tendency. **Today's rest state is balanced only because the flux and source
errors cancel.** Both use $\bar p_V$ where $\langle p\rangle_A$ is meant.

In motion the uncorrected pair evaluates the horizontal pressure-gradient force
at $r_v$ instead of $r_c$. That is an $O(h^2)$ error
$\delta\,\partial_r(\nabla_hp)$, of relative size $\delta/H_p$. Correcting the
flux alone turns this harmless error into a **spurious force at rest** (4.3,
4.5). Correcting flux and source together removes it from both.

**Not touched.** The x1-row geometric source, in the
`face_pressure1` form that is always taken when `nc1>1`
(`hydro.cpp:126-133`, `spherical_polar.cpp:235-247`,
`gnomonic_equiangle.cpp:411-425`), is defined to cancel the x1 face pressure
identically. It is not involved here. On the gnomonic grid the remaining
$1/\texttt{radius}$ terms use the arithmetic `x1v`, which is a further
$O(h^2/r^2)$ geometric inconsistency. Those terms are zero at rest.

---

## 5. Numerical check of the rest state (`rest_balance.py`)

The script replicates snapy's operators exactly:
`radial_centers`, `face_area2/3`, `cell_volume` (exact for spherical,
trapezoid for gnomonic), `coord_src1_i/j`, the full gnomonic `reset()` arc and
metric arrays, `x_ov_rD`, `y_ov_rC`, `flux2global2_/3_`, the divergence, and
the e7f9904 $\delta$ and $D_1$. Isothermal $p(r)$ with $H_p=0.1R_0$, shell
$[1,1.5]$. Each entry is $\max|$tendency$|/\max|Gp|$ over interior cells.

| grid | $h$ | A: none | B: flux only | B, global frame | C: flux + source (4.7) | B vs $+\delta D_1p\,G$ |
|---|---|---|---|---|---|---|
| spherical $\theta$ row | 0.0313 | 1.5e-15 | **8.0e-04** | — | 2.1e-15 | 2.6e-12 |
| | 0.0156 | 2.0e-15 | **2.0e-04** | — | 1.3e-15 | 6.2e-12 |
| | 0.0078 | 1.3e-15 | **5.0e-05** | — | 1.5e-15 | 3.0e-11 |
| | 0.0039 | 1.5e-15 | **1.3e-05** | — | 1.4e-15 | 1.1e-10 |
| spherical $\phi$ row | all | 0 | 0 | — | 0 | — |
| gnomonic $\alpha+\beta$ rows | 0.0313 | 1.2e-14 | **8.0e-04** | 8.0e-04 | 1.3e-14 | 1.6e-11 |
| | 0.0156 | 1.1e-14 | **2.0e-04** | 2.0e-04 | 9.0e-15 | 4.5e-11 |
| | 0.0078 | 1.0e-14 | **5.0e-05** | 5.0e-05 | 1.1e-14 | 2.1e-10 |
| | 0.0039 | 1.0e-14 | **1.3e-05** | 1.3e-05 | 1.0e-14 | 8.0e-10 |

* B falls $4\times$ per halving, as $h^2/(12rH_p)$ predicts:
  $8.1\times10^{-4}$ at $h=1/32$.
* B agrees with the predicted $+\delta D_1p\,G$ to round-off, amplified by
  $1/|B|$.
* C is back to the baseline round-off.

---

## 6. Assumptions and caveats

* **A4 (face state equals cell state)** is e7f9904's reading. The corrections
  are relative to what LMARS evaluates from reconstructed states. They are not
  a claim about the reconstruction's own error.
* **Gnomonic `x1v` is the arithmetic mid-radius, not $r_v$**
  (`gnomonic_equiangle.cpp:36`). The brief says the volume centroid "is snapy's
  `x1v`"; that is true on spherical-polar only. $\delta$ is defined by the
  measures, not by `x1v`, so (1.1) stands on both grids, and the rest-state
  result does not depend on $\delta$'s value at all. But gnomonic initial
  conditions sampled at `x1v` are values at $\bar r$, not cell averages.
  Together with the trapezoid `cell_volume`, already noted in e7f9904, the
  gnomonic $\delta$ is the right correction only under the "cell average"
  reading of the stored state.
* **$D_1$ on stretched grids** is $O(h)$. The correction stays an improvement
  (e7f9904 A6). The rest-state balance does not depend on this, because flux
  and source use the same $D_1$.
* **Balance is to round-off, not bitwise**, in the $\theta$, $\alpha$ and
  $\beta$ rows. This was already so before the change: $(A_+F-A_-F)/V$ versus
  the precomputed $G$, $P/s(1-c^2)$ versus $Ps$, and WENO face weights. It is
  bitwise only in the spherical $\phi$ row.
* **Flux positivity** (`flux_positivity.hpp`) rescales species fluxes after
  this point. It is unchanged, and it already breaks $F_q=qF_\rho$ for the
  cells it limits.

## 7. Recipe

1. Per x2/x3 face, in the local frame, with face state
   $\bar w=\tfrac12(w_L+w_R)$, compute
   $\Delta F_\rho=-\delta D_1(\rho u_n)$.
2. Then, per row, $\Delta F_\varphi$ by (3.1), with
   $\varphi\in\{1-\sum q,\ q_n,\ u_t,\ u_r,\ u_n\}$.
3. Add $-\delta D_1p$, and optionally the kinetic term of (2.9), to the normal
   momentum row.
4. The energy row as in e7f9904.
5. Apply the result before `flux2global`, or after it: they commute.
6. In `SphericalPolarImpl::forward` and `GnomonicEquiangleImpl::forward`,
   replace the cell pressure in the x2/x3 geometric source weights by
   $p-\delta D_1p$, with the same $\delta$ and $D_1$ (4.7). Optionally give the
   $\rho v^2$ weights their (2.3) correction too.
7. Test: a resting $p(r)$ column must keep a zero horizontal momentum tendency
   to round-off, on both grids; `rest_balance.py` case C is the reference. A
   uniform $q$ must stay uniform.
