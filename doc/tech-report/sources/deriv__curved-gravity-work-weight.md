> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

Source: snapy 6499404:docs/derivations/curved-gravity-work-weight.md
# Face-form gravity work on a radial grid: exact weights versus discrete E+PE conservation

Scope: the x1 face-form gravity work (`gravity-work: face`) on a spherical-polar grid, explicit path
(`src/hydro/hydro_forward.cpp`, the `face_gravity_work` block) and implicit path (`src/implicit/implicit_hydro.cpp`,
`work_lo`/`work_hi`, which carry the same weights times 1/2 for the face average of the two cell momenta).
Base: 8cea3ae. Every closed form below is checked by `curved_gravity_work_weight.py` (sympy + numpy;
`python docs/derivations/curved_gravity_work_weight.py` prints every number quoted; "replica" below).

**Result.** The exact $r^2$-measure weights remove both $O(h^2/\bar r)$ error terms, but they do **not** conserve
discrete E+PE: the per-face defect is $h^3/3$ (relative $h^2/(3R^2)$), the same order as the terms they remove.
No two-point weight choice that keeps the face form's conservation of E+PE$_d$ removes both terms; one or the other, not both.

**Option F (§7).** Conserving a corrected discrete PE, $P = \mathrm{PE}_d - g_1\sum_iV_i\sigma_i^2 s_i[\rho]$ (exact
to $O(h^4)$), instead of $\mathrm{PE}_d$ resolves the conflict: the work $W = W_{\rm face} + g_1\sigma^2 s[\dot\rho]$ is
$O(h^4)$-exact and conserves E+$P$ to round-off by construction. It changes Cartesian too and replaces (not adds to)
the cp3/cp5/weno5 curvature flux. §8 is the Cartesian case written to be ported on its own: there F removes the
$O(h)$ wall-cell error that face+H leaves, and leaves the interior unchanged to $O(h^4)$. §9 compares F with the $\bar r$ potential form; §10 lists
every place that computes a PE under the switch `SNAP_GRAVITY_WORK_RADIAL_EXACT`, which selects F.

## 1. Setup

Per steradian (the polar and azimuthal factors are common to $A$ and $V$ and cancel):
$$A(r) = r^2,\qquad V_i = \tfrac13\left(r_{i+1/2}^3 - r_{i-1/2}^3\right),\qquad
r_{c,i} = \frac{\int_i r^3\,dr}{\int_i r^2\,dr} = \frac34\,\frac{r_{i+1/2}^4 - r_{i-1/2}^4}{r_{i+1/2}^3 - r_{i-1/2}^3},$$
where $r_c$ is `x1v` (`radial_centers` in `src/coord/spherical_polar.cpp`), the volume centroid. Gravity is
$g_1 = $ `grav1` $< 0$ and the potential is $\phi = -g_1 r$, so $\langle\phi\rangle_{V_i} = \phi(r_{c,i})$ exactly.
$F_f$ is the x1 mass-flux density at face $f$ and $G = A F = r^2 F$ the mass flow per steradian. Write
$r_\pm$ for a cell's faces, $h = r_+ - r_-$, $\bar r = (r_+ + r_-)/2$, $\delta = r_c - \bar r$.

Mass: $V_i\,\dot\rho_i = -(A_+F_+ - A_-F_-)$. Discrete potential energy: $\mathrm{PE} = \sum_i \rho_i\,\phi(r_{c,i})\,V_i$
(the exact $\int\rho\phi\,dV$ for piecewise-constant $\rho$).

Exact gravity work per unit volume: $g_1\langle F\rangle_V = \frac{g_1}{V}\int_{r_-}^{r_+} r^2F\,dr$.

## 2. The face-form booking

The code books, per unit volume and time,
$$W_i = \frac{1}{V_i}\Big[\phi_{c,i}\,(A_+F_+ - A_-F_-) - (A_+\phi_+F_+ - A_-\phi_-F_-)\Big]
      = \frac{g_1}{V_i}\Big[(r_+ - r_c)\,r_+^2F_+ + (r_c - r_-)\,r_-^2F_-\Big]. \tag{1}$$
The second form follows from $\phi_c - \phi_\pm = g_1(r_\pm - r_c)$.

**Leading error.** Expand $F = F_0 + F_1 s + F_2 s^2/2$, $s = r - \bar r$, and integrate exactly (replica §1):
$$\frac{W - g_1\langle F\rangle_V}{g_1} = \underbrace{\frac{h^2}{12}F''}_{\text{Cartesian}}
  + \underbrace{\frac{h^2}{6\bar r}F' - \frac{h^2}{6\bar r^2}F}_{\text{curvature}} + O(h^4). \tag{2}$$
The curvature pair is the term the radial ablation found (with its sign: face minus exact). The Cartesian term is the trapezoid
error present on every grid.

Equivalent form in $G = r^2F$: $\;W - g_1\langle F\rangle_V = \frac{g_1}{V}\big[-\delta h\,G' + \frac{h^3}{12}G''\big] + O(h^5)$,
with $\delta = h^2/(6\bar r) + O(h^4)$. So (1) is **exact for $G$ = const**, a steady divergence-free radial mass
flow ($F \propto r^{-2}$): $W = g_1 G h / V = g_1\langle F\rangle_V$ for any $h$.

## 3. Exact replacement weights

A two-point booking $W = g_1(a F_+ + b F_-)$ that is exact for $F \in \{1, r\}$ on the $r^2$ measure needs
$a + b = 1$ and $a r_+ + b r_- = \langle r\rangle_V = r_c$. The solution is unique:
$$a = \frac{r_c - r_-}{h},\qquad b = \frac{r_+ - r_c}{h}. \tag{3}$$
Note that (3) puts the weight $(r_c - r_-)$ on $F_+$, where (1) puts $(r_+ - r_c)r_+^2/V$ on $F_+$: the roles
of the two offsets are swapped. Its error (replica §1, $F$ expanded to $s^4$; the odd orders vanish):
$$\frac{W_{\rm exact} - g_1\langle F\rangle_V}{g_1} = \frac{h^2}{12}F''
  + h^4\Big(-\frac{F''}{360\,\bar r^2} + \frac{F'''}{360\,\bar r} + \frac{F''''}{480}\Big) + O(h^6).\tag{4}$$
Both curvature terms of (2) are gone; the Cartesian term stays. Cartesian limit: $r_c = \bar r$, so
$a = b = 1/2$, and (1) gives $(h/2)\cdot A/V = 1/2$ as well, so (3) reduces to the old weights there.

## 4. Discrete E+PE conservation

**Lemma (what conservation requires).** Let every cell book a two-point work $W_i V_i = g_1(\alpha_i F_{i+1/2} +
\beta_i F_{i-1/2})$. With closed walls ($F = 0$ on the two wall faces) the E+PE change per unit time is
$$\frac{d}{dt}(E + \mathrm{PE}) = \sum_i W_iV_i + \sum_i \phi_{c,i}\,V_i\dot\rho_i
 = g_1\sum_{f\ \rm interior} F_f\Big[\underbrace{\alpha_i + \beta_{i+1}}_{S_f} - A_f\,(r_{c,i+1} - r_{c,i})\Big],$$
using $\sum_i\phi_{c,i}V_i\dot\rho_i = \sum_f A_fF_f(\phi_{c,i+1} - \phi_{c,i})$ (cell $i$ below face $f$, cell $i+1$ above),
and $\phi_{c,i+1} - \phi_{c,i} = -g_1(r_{c,i+1} - r_{c,i})$. The interior $F_f$ are independent, so E+PE is
conserved for every flux field **iff** $S_f = A_f(r_{c,i+1} - r_{c,i})$ on every interior face. The other energy
fluxes telescope to the walls and drop out.

Equivalently: conserving two-point bookings are exactly the face form with an arbitrary face potential,
$W_iV_i = \phi_{c,i}(A_+F_+ - A_-F_-) - (A_+\phi(s_+)F_+ - A_-\phi(s_-)F_-)$, where $s_f$ (the split point of
the face's total weight between the two cells) is free. The code uses $s_f = r_f$.

**Face form (1):** $S_f = A_f(r_f - r_{c,i}) + A_f(r_{c,i+1} - r_f) = A_f(r_{c,i+1} - r_{c,i})$. Conserved
identically, for any grid (replica: `face : 0`).

**Exact weights (3):** $S_f = \frac{V_i}{h_i}(r_{c,i} - r_{i-1/2}) + \frac{V_{i+1}}{h_{i+1}}(r_{i+3/2} - r_{c,i+1})$.
For uniform $h$ and the face at $r_f = R$ the exact closed form is
$$S_f - A_f(r_{c,i+1} - r_{c,i}) = \frac{h^3\,(3R^4 - R^2h^2 + h^4/6)}{9R^4 - 3R^2h^2 + h^4}
 = \frac{h^3}{3} + O(h^5/R^2) \neq 0, \tag{5}$$
relative to the required value: $h^2/(3R^2) + h^4/(18R^4)$. Hence the E+PE change per unit time is
$$\frac{d}{dt}(E+\mathrm{PE}) = g_1\,\frac{h^3}{3}\sum_f F_f + O(h^5) = g_1\,\frac{h^2}{3}\int F\,dr + O(h^4)
\quad\text{(per steradian)},$$
nonzero whenever the column-integrated vertical mass flux density is nonzero. **The exact weights do not keep the
face form's conservation.** The defect is $O(h^2/R^2)$ of the work, the same order as the curvature terms in (2)
that they remove.

**No conserving two-point booking removes both curvature terms.** Take the conserving family with
$s_f = r_f + \lambda h^2/r_f$ (any smooth $O(h^2)$ shift has this leading form locally). Replica §1:
$$\frac{W_\lambda - g_1\langle F\rangle_V}{g_1} = \frac{h^2}{12}F'' + \Big(\lambda + \frac16\Big)\frac{h^2}{\bar r}F'
 + \Big(\lambda - \frac16\Big)\frac{h^2}{\bar r^2}F + O(h^4).$$
$\lambda = 1/6$ removes the $F$ term and doubles the $F'$ term; $\lambda = -1/6$ removes the $F'$ term and doubles
the $F$ term; no $\lambda$ removes both. For a general shift $s_f = r_f + h^2\varepsilon(r_f)$ the two conditions are
$\varepsilon = -1/(6r)$ and $\varepsilon' + 2\varepsilon/r = +1/(6r^2)$, which contradict each other
($-1/(6r)$ gives $-1/(6r^2)$). Only $\lambda = 0$ (the current code) is exact for divergence-free flow ($G$ = const),
because only a constant shift keeps $s_+ - s_- = h$.

**Wider stencils (leading order, a remark not a proof).** Any booking that equals the exact cell average up to the
common Cartesian term books the exact total work, and
$\sum_i g_1\!\int_i G\,dr + \sum_i\phi_{c,i}\dot M_i = -g_1\sum_i\int_i (r - r_{c,i})\,G'\,dr$, whose curvature part is
$+g_1\frac{h^2}{6}\int G'/r\,dr = g_1\frac{h^2}{6}\int F\,dr$ for closed walls. This is a column integral, not a sum of
local face differences, so no local telescoping correction of the *weights* cancels it (the potential is held at
$\mathrm{PE}_d$ here; §7 lifts that). The Cartesian part, $(h^2/12)[G']_{\rm walls}$, is a pure wall term, so it is no real conflict:
a wall closure plus a modified discrete PE removes it with exact conservation (§§7–8, the corrected-PE work behind
`SNAP_GRAVITY_WORK_RADIAL_EXACT`, and an independent four-point booking that is $O(h^4)$ in every cell including the
walls). Only the face form with $\mathrm{PE}_d$ pays the trapezoid error to conserve.

## 5. Numbers (replica §2, §3)

One step, closed column, random interior $F_f$, $g_1 = -10$, column $3H$, $\rho = 1$:

| $R/H$ | $h/R$ | face: $\Delta(E{+}PE)/\sum\lvert WV\rvert$ | exact (3) | cons $\lambda=\pm1/6$ | exact, $\Delta(E{+}PE)/(E{+}PE)$ |
|---|---|---|---|---|---|
| 5 | 9.4e-3 | 3.9e-15 | **-1.3e-6** | 3.9e-15 | -4.1e-8 |
| 5 | 2.3e-3 | -9.8e-16 | **-5.7e-8** | -1.0e-15 | -2.5e-9 |
| 1000 | 4.7e-5 | -6.5e-13 | **+1.2e-10** | -6.5e-13 | +2.8e-14 |
| 1 | 9.4e-2 | 3.1e-15 | **+2.0e-4** | 3.2e-15 | +2.2e-5 |

The face form and both $\lambda$ variants stay at the floor of these sums ($\le 4\times10^{-15}$ for $R \le 5H$; $6.5\times10^{-13}$
at $R = 1000H$, where the $r^2$-weighted terms span a wide range: a cancellation floor, not shown to be round-off); the exact weights fail a 1e-14 relative gate
at every $R$ tested, by both measures (at $R = 1000H$: 2.8e-14 of $E{+}PE$, 1.2e-10 of the step's work).

Convergence against the exact $r^2$-measure cell average, $F = e^{-(r-r_0)/H}\sin(\pi(r-r_0)/4H)$:
- $h$-ladder at $R = 5H$, $\max|e - \tfrac{h^2}{12}F''|$: face 1.18e-3 → 6.27e-6 over nz 16 → 256, slope 1.75 → 1.97
  ($h^2$); exact 2.42e-5 → 3.86e-10, slope 3.96 → 4.00 ($h^4$).
- $R$-ladder at $h/H = 1/16$: face $\times R$ = 4.74e-4, 4.77e-4, 4.60e-4 at $R/H$ = 5, 50, 500 ($h^2/R$); exact at the
  $h^4$ floor 4e-8.
So the exact weights pass oracle (e) and fail oracle (c).

## 6. Two-point options (superseded by option F, §7)

| option | curvature terms in (2) | E+PE per step | divergence-free flow exact |
|---|---|---|---|
| A. current face form ($\lambda = 0$) | both present | round-off | yes |
| B. exact weights (3) | both removed | defect $g_1(h^2/3)\int F\,dr$, rel $h^2/(3R^2)$ | no ($O(h^2/R^2)$) |
| C. conserving, $\lambda = +1/6$ | $F$ term removed, $F'$ doubled | round-off | no |
| D. conserving, $\lambda = -1/6$ | $F'$ term removed, $F$ doubled | round-off | no |
| E. B plus a global E+PE fixer (as gravity-work-fixer does for cell) | both removed | round-off after the fix | no |

Hypothesis (unverified): the ablation's sign surprise (shift +1.05 / +1.19 against the predicted -1.07 / -1.23)
comes from option B's defect, which is the same order as the term removed. The check that settles it: rerun the
ablation arm with option D (conserving, $F'$ term only) and with C; if each moves the excess by its own share of
the predicted term, the defect explains the rest.

## 7. Option F: a corrected discrete PE and the work it implies

The lemma of §4 is about two-point bookings measured against $\mathrm{PE}_d = \sum_i V_i\rho_i\phi(r_{c,i})$. That
functional is itself only $O(h^2)$-accurate: an exact work conserves the exact PE, not $\mathrm{PE}_d$. Option F
changes the functional, not the weights. Checked by `optionF_replica.py` (numpy;
`python docs/derivations/optionF_replica.py` prints every number quoted; "F-replica" below; entries at the
round-off or cancellation floor, $\lesssim 10^{-12}$, differ in their leading digits between numpy builds).

**The functional.** Expand $\rho$ about the centroid inside cell $i$, $\rho = \rho(r_c) + \rho'(r - r_c) +
\tfrac12\rho''(r - r_c)^2 + \dots$. With $\phi = -g_1 r$,
$$\int_i\rho\phi\,dV = -g_1\Big[r_c M_i + \int_i\rho\,(r - r_c)\,dV\Big]
 = V_i\big[\rho_i\phi(r_c) - g_1\,\sigma_i^2\,\rho'(r_c)\big] + O(h^4 V),$$
where $M_i = \rho_iV_i$ (exact), $\sigma_i^2 = \langle(r - r_c)^2\rangle_{V_i}$ (the $r^2$-measure variance; the
third central moment is $O(h^4/R)$). Replace $\rho'$ by $s_i[\rho]$, the slope at $r_{c,i}$ of the quadratic through
the cell values at the centroids (interior: cells $i-1, i, i+1$; the two cells at each closed wall: the one-sided
stencil $0,1,2$ or $n-3,n-2,n-1$). The cell values sit $O(h^2)$ off the point values by a smooth amount, so
$s_i = \rho'(r_c) + O(h^2)$, and
$$P[\rho] = \sum_i V_i\big[\rho_i\,\phi(r_{c,i}) - g_1\,\sigma_i^2\,s_i[\rho]\big] = \int\rho\phi\,dV + O(h^4).\tag{6}$$
On a uniform centroid spacing this is a $\kappa$ form ($\kappa_i \propto \sigma_i^2/(r_{c,i+1} - r_{c,i-1})$);
the quadratic stencil keeps it $O(h^4)$ on the non-uniform centroid spacing as well. Per steradian, cancellation-free:
$\sigma^2 = (\bar r^2h^3/12 + h^5/80)/V - \delta^2$, $\delta = r_c - \bar r = \bar r h^3/(6V)$.

**The work.** Define $W_iV_i := -\dot P_i - (A_+\phi_+F_+ - A_-\phi_-F_-)$ with $\dot\rho$ from the discrete continuity
$V\dot\rho = -(A_+F_+ - A_-F_-)$. Since $P$ is linear in $\rho$,
$$W_i = W_{{\rm face},i} + g_1\,\sigma_i^2\,s_i[\dot\rho]. \tag{7}$$
The first term is (1); the second couples faces $i-3/2 \dots i+3/2$ (wall cells: the first four faces).

**Conservation (exact, by construction).** $\sum_iW_iV_i + \dot P = -\sum_i\Delta_i(A\phi F) = 0$ for closed walls,
for every flux field and every grid. E+P is conserved to round-off; E+PE$_d$ is not (it changes by
$-g_1\sum_iV_i\sigma_i^2s_i[\dot\rho]$, an $O(h^2)$ amount, which is the point: $\mathrm{PE}_d$ is the wrong target).

**Accuracy.** The exact cell budget is $g_1V_i\langle F\rangle = -\dot{\mathrm{PE}}_i - \Delta_i(A\phi F)$, so
$W_iV_i - g_1V_i\langle F\rangle = \frac{d}{dt}(\mathrm{PE}_i - P_i) = O(h^4V)$ by (6). Both curvature terms of (2)
and the Cartesian term go: to leading order $\sigma^2s[\dot\rho] = -\tfrac{h^2}{12}(F'' + 2F'/r - 2F/r^2)$, which is
minus (2).

**Properties.**
1. Exact to $O(h^4)$, both $h^2/R$ terms and the $h^2F''/12$ term removed, interior and wall cells (table below).
2. Cartesian changes. There $\sigma^2 = h^2/12$ and (7) removes the trapezoid term $h^2F''/12$ that the face form
   keeps; E+P is conserved and E+PE$_d$ is not. Change at nz 64: $1.6\times10^{-3}$ of $\max|W|$ (interior),
   $1.9\times10^{-3}$ (wall cells). F applies on Cartesian too, under the same switch; the Cartesian case is
   written out on its own in §8.
3. Closed walls need nothing beyond the one-sided slope stencil: conservation does not use the wall fluxes' value
   (they are zero), and the wall cells converge at $h^{4.4-4.6}$. At an internal block edge the same one-sided
   stencil makes $P$ a sum of per-block functionals; the faces shared by two blocks still telescope, so global
   E+P stays exact. In 2-D/3-D, x2/x3 fluxes book no gravity work and move mass between columns at
   the same radius; on spherical-polar $V = \Omega(\theta,\varphi)V_r(r)$ and $\sigma^2$, $s$ depend on $r$ only, so
   $\sum_{\rm columns}P$ depends only on each shell's total mass, which they conserve: E+P stays exact (§8.6 for Cartesian).
4. Numbers below.

**Interaction with the cp3/cp5/weno5 curvature flux.** `hydro_forward.cpp` already subtracts
$g_1\,\Delta(AH)/V$, $H_f = (r_{c,i} - r_{c,i-1})(m_i - m_{i-1})/12$, zero at physical boundaries, for these
reconstructions. It is a divergence (keeps E+PE$_d$) and removes $\tfrac{h^2}{12}(r^{-2}(r^2F')')
= \tfrac{h^2}{12}(F'' + 2F'/r)$. So, on curved grids, face+H leaves $-\tfrac{h^2}{6\bar r^2}F$ in the interior,
and, because $H = 0$ at the walls, its wall cells are only first order ($h^1$, Cartesian and spherical alike).
F already removes the $F''$ term, so **F must replace H, not add to it**: F+H is back to $O(h^2)$ (double count).

**Numbers** (F-replica §1, §2, §5; $g_1 = -10$; closed walls).

| one step, random interior $F_f$ | face: $\Delta(E{+}P)/\sum\lvert WV\rvert$ | face: $\Delta(E{+}PE_d)$ | F: $\Delta(E{+}P)$ | F: $\Delta(E{+}PE_d)$ | F: $\Delta(E{+}P)/(E{+}P)$ |
|---|---|---|---|---|---|
| sph $R = 5H$ | 8.0e-3 | -3.0e-15 | **-1.3e-15** | -7.3e-3 | -2.0e-16 |
| sph $R = 1000H$ | 3.5e-3 | 5.3e-13 | **-5.7e-14** | -3.2e-3 | -4.6e-17 |
| sph $R = H$ | -2.1e-2 | 9.0e-16 | **1.3e-15** | 1.9e-2 | 1.2e-15 |
| Cartesian | 5.8e-3 | -3.5e-15 | **3.7e-15** | -5.2e-3 | 5.9e-16 |

Oracle (c) measured against $P$: F passes at round-off ($\le 1.2\times10^{-15}$ of E+P); the face form does not
conserve $P$ (it conserves $\mathrm{PE}_d$).

| $\max\lvert W - g_1\langle F\rangle\rvert/\lvert g_1\rvert$, $R = 5H$, nz 16 → 256 | interior | slope | wall cells | slope |
|---|---|---|---|---|
| face (1) | 3.2e-3 → 2.5e-5 | 1.4 → 1.95 | 5.8e-3 → 2.5e-5 | 1.9 → 2.0 |
| F (7) | 3.5e-5 → 5.4e-10 | 3.99 → 4.00 | 5.4e-5 → 1.8e-10 | 4.6 → 4.4 |
| face + H (cp3/cp5/weno5 today), nz 32 → 256 | 2.0e-5 → 3.3e-7 | 2.0 | 8.0e-3 → 1.0e-3 | 1.0 |
| F + H (double count) | 1.2e-3 → 2.5e-5 | 1.9 | 6.5e-3 → 9.9e-4 | 0.96 |
| Cartesian F | 6.9e-5 → 1.2e-9 | 4.00 | 1.3e-4 → 1.9e-9 | 4.0 |

$R$-ladder at nz 64 ($h = H/16$), F interior | wall: 1.4e-7 | 9.0e-8, 2.8e-7 | 4.8e-7, 2.9e-7 | 5.0e-7, 3.0e-7 | 5.0e-7
at $R/H$ = 5, 50, 500, 5000 (flat: no $1/R$ term left), against face $\times R$ = 1.8e-3, 2.1e-2, 0.21, 2.1 (the
face form's interior error at this $h$ is dominated by the $h^2F''/12$ term, which does not fall with $R$).

**Settling check (can a column-integrated diagnostic tell the options apart?).** Same profile,
closed walls, column sums normalised by $\sum\lvert g_1\langle F\rangle\rvert V$ (F-replica §4):

| $R/H$, nz | A face | B exact | C ($\lambda = +1/6$) | D ($\lambda = -1/6$) | F |
|---|---|---|---|---|---|
| 5, 32: work error | +1.420e-3 | +1.292e-3 | +1.420e-3 | +1.420e-3 | -7.3e-6 |
| 5, 32: PE$_d$ defect | 1e-16 | **-1.29e-4** | 3e-16 | 1e-16 | -1.43e-3 |
| 1000, 64: work error | +5.249e-4 | +5.249e-4 | +5.249e-4 | +5.249e-4 | -8.0e-7 |
| 1000, 64: PE$_d$ defect | 3e-14 | -1.3e-9 | 3e-14 | 3e-14 | -5.26e-4 |

A, C and D book the same column total (they differ only in how it is split between cells), so a column-integrated
diagnostic cannot separate them; only B differs, and by exactly its E+PE$_d$ defect. At $R = 5H$, nz 32 that defect is
9% of the column work error. So if the ablation's $(d)$ arm used the exact weights, the shift it saw includes B's
non-conservation; a C or D arm would show the column total of A. The real ablation's $\varepsilon$ harness was not
rebuilt here. F is the only option whose column total is right ($-7\times10^{-6}$ against $+1.4\times10^{-3}$): its
PE$_d$ "defect" is the $O(h^2)$ error of PE$_d$ itself, equal and opposite to A's work error.

## 8. Option F on a Cartesian $x_1$ grid, self-contained ($R \to \infty$)

This section can be read and ported without §§1–7. Every identity is checked in `optionF_replica.py` (§1, §6, §7) and in `tests/test_gravity_work_radial_exact.py` (closed columns in the code).

**8.1 Grid and notation.** One column, $x_1 = z$, cells $i = 0,\dots,n-1$ with faces $z_{i-1/2} < z_{i+1/2}$,
width $h_i = z_{i+1/2} - z_{i-1/2}$, centre $z_i = (z_{i-1/2} + z_{i+1/2})/2$ (the volume centroid, `x1v`). All
quantities are per unit horizontal area. $\rho_i$ is the cell-average total density (dry plus every condensate
and tracer that carries mass, the same sum the code's x1 mass flux uses). $F_{i+1/2}$ is the x1 mass flux through
face $i+1/2$ as the Riemann solver returns it; closed walls mean $F_{-1/2} = F_{n-1/2} = 0$. Gravity is
$g_1 = $ `grav1` $< 0$, the potential $\phi(z) = -g_1 z$. $E$ is the total energy density (the code's `IPR` row).

**8.2 Discrete continuity.** The x1 part of the mass update is
$$h_i\,\dot\rho_i = -(F_{i+1/2} - F_{i-1/2}). \tag{8.1}$$
In the code $\dot\rho_i\,dt$ is the stage's x1 density increment, `-dt * vertical_mass_div`.

**8.3 What the code books today (face form).** `hydro_forward.cpp` books, per cell,
$$W^{\rm face}_i h_i = g_1\big[(z_{i+1/2} - z_i)F_{i+1/2} + (z_i - z_{i-1/2})F_{i-1/2}\big],$$
which is the same as
$$W^{\rm face}_i h_i = -h_i\dot\rho_i\,\phi(z_i) - \big(\phi_{i+1/2}F_{i+1/2} - \phi_{i-1/2}F_{i-1/2}\big),
\qquad \phi_{i\pm1/2} = \phi(z_{i\pm1/2}). \tag{8.2}$$
(Insert (8.1) and $\phi = -g_1z$: the right side is $-g_1z_i(F_+ - F_-) + g_1(z_+F_+ - z_-F_-) =
g_1[(z_+ - z_i)F_+ + (z_i - z_-)F_-]$. The code's form is `dt*(phi_cell*div - div(phi_face*F))` with
`div` $= (F_+ - F_-)/h_i$, the same expression divided by $h_i$.)
Summing (8.2) over the column, the bracket telescopes to $\phi F$ at the two walls, which is zero, so
$\sum_iW^{\rm face}_ih_i + \tfrac{d}{dt}\mathrm{PE}_d = 0$ with $\mathrm{PE}_d = \sum_ih_i\rho_i\phi(z_i)$: the face form
conserves $E + \mathrm{PE}_d$.
*Its error.* The exact cell work is $g_1\langle F\rangle_i = \tfrac{g_1}{h_i}\int_i F\,dz$. On a uniform grid
$W^{\rm face}_i = g_1(F_{i+1/2} + F_{i-1/2})/2$, the trapezoid rule, so
$W^{\rm face}_i - g_1\langle F\rangle_i = g_1\tfrac{h^2}{12}F''(z_i) + O(h^4)$ in every cell, walls included.
*With the cp3/cp5/weno5 curvature flux H* (also in `hydro_forward.cpp`):
$W^{\rm face+H}_i = W^{\rm face}_i - g_1(H_{i+1/2} - H_{i-1/2})/h_i$, $H_{i+1/2} = \tfrac{z_{i+1} - z_i}{12}(m_{i+1} - m_i)$,
$m = \rho v_1$ at the cell centres, $H = 0$ on the walls. In the interior this subtracts $g_1\tfrac{h^2}{12}F''$ and
the result is $O(h^4)$. In a wall cell only one H face acts: $H_{1/2}/h \approx \tfrac{h}{12}F'(z_{\rm wall})$ is left,
an $O(h)$ error, $\approx g_1\tfrac{h}{12}F'(z_{\rm wall})$ (F-replica §6: $1.65\times10^{-2}$ at nz 16 for $F' = \pi/4$,
$h = 1/4$, where $h F'/12 = 1.64\times10^{-2}$).

**8.4 The exact potential energy of a cell, and its discrete stand-in $P$.** Let $\rho(z)$ be smooth and expand about
$z_i$: $\rho = \rho(z_i) + \rho'(z - z_i) + \tfrac12\rho''(z - z_i)^2 + \tfrac16\rho'''(z - z_i)^3 + \dots$ Then, with
$\int_i(z - z_i)\,dz = 0$, $\int_i(z - z_i)^2dz = h^3/12$, $\int_i(z - z_i)^4dz = h^5/80$,
$$\int_i\rho\phi\,dz = -g_1\Big[z_i\int_i\rho\,dz + \int_i\rho\,(z - z_i)\,dz\Big]
= h_i\Big[\rho_i\phi(z_i) - g_1\tfrac{h_i^2}{12}\rho'(z_i)\Big] - g_1\tfrac{h_i^5}{480}\rho'''(z_i) + \dots \tag{8.3}$$
so the exact cell PE is $h_i[\rho_i\phi(z_i) - g_1\sigma_i^2\rho'(z_i)] + O(h^5)$ with $\sigma_i^2 = h_i^2/12$, the variance
of $z$ over the cell. $\mathrm{PE}_d$ drops the $\sigma^2\rho'$ term and is therefore only $O(h^2)$ accurate per unit
length; that is the whole reason the face form, which conserves $\mathrm{PE}_d$ exactly, keeps an $O(h^2)$ work error.
Replace $\rho'(z_i)$ by a slope built from the cell averages,
$$s_i[\rho] = \text{derivative at } z_i \text{ of the quadratic through } (z_k,\rho_k),\ k \in S_i,\qquad
S_i = \{i-1,i,i+1\}\ (0 < i < n-1),\ S_0 = \{0,1,2\},\ S_{n-1} = \{n-3,n-2,n-1\}. \tag{8.4}$$
On a uniform grid: $s_i = (\rho_{i+1} - \rho_{i-1})/(2h)$ inside, $s_0 = (-3\rho_0 + 4\rho_1 - \rho_2)/(2h)$,
$s_{n-1} = (3\rho_{n-1} - 4\rho_{n-2} + \rho_{n-3})/(2h)$; the non-uniform weights are in `centroid_slope`
(`src/hydro/gravity_work_radial.hpp`). Cell averages differ from point values by $\tfrac{h^2}{24}\rho''$, a smooth
amount, so $s_i = \rho'(z_i) + O(h^2)$ (interior and wall alike), and $\sigma^2 s_i = \sigma^2\rho' + O(h^4)$. Define
$$P[\rho] = \sum_i h_i\Big[\rho_i\,\phi(z_i) - g_1\,\sigma_i^2\,s_i[\rho]\Big]
 = \int\rho\phi\,dz + O(h^4). \tag{8.5}$$
$P$ is linear in $\rho$ and needs no data outside the column (no ghost cells): that is the whole wall closure.

**8.5 The work that conserves $E + P$.** Define the booked work by the same recipe as (8.2), with $P$ in place of
$\mathrm{PE}_d$: $W_ih_i := -\dot P_i - (\phi_{i+1/2}F_{i+1/2} - \phi_{i-1/2}F_{i-1/2})$, where $P_i$ is the $i$-th
summand of (8.5). Because $P_i$ is linear in $\rho$, $\dot P_i = h_i[\dot\rho_i\phi(z_i) - g_1\sigma_i^2s_i[\dot\rho]]$,
and comparing with (8.2),
$$W_i = W^{\rm face}_i + g_1\,\sigma_i^2\,s_i[\dot\rho],\qquad \dot\rho \text{ from (8.1)}. \tag{8.6}$$
This is all the switch adds (`corrected_pe_work`; explicit: in `hydro_forward.cpp` on `-dt*vertical_mass_div`;
VIC: in `implicit_hydro.cpp` on the solve's own density change `du - du0`, rows IDN and the condensates). It changes
only the energy row: mass and momentum are untouched, so a state at rest ($F \equiv 0$, $\dot\rho = 0$) gets exactly
zero from it.
*Uniform-grid closed forms* (substitute (8.1) into (8.4); F-replica §7 checks them against the matrix form to
$8\times10^{-16}$):
$$\frac{W_i}{g_1} = \frac{F_{i+1/2} + F_{i-1/2}}{2} - \frac{F_{i+3/2} - F_{i+1/2} - F_{i-1/2} + F_{i-3/2}}{24}
\quad(0 < i < n-1),$$
$$\frac{W_0}{g_1} = \frac{19F_{1/2} - 5F_{3/2} + F_{5/2}}{24},\qquad
\frac{W_{n-1}}{g_1} = \frac{19F_{n-3/2} - 5F_{n-5/2} + F_{n-7/2}}{24}.$$
(Cell 1 and cell $n-2$ use the interior form with the wall flux $F_{\mp1/2} = 0$.)
Hand check of the wall form: for $F = z, z^2, z^3$ on the cell $[0,h]$ with $F(0) = 0$ it gives $h/2$, $h^2/3$, $h^3/4$,
the exact averages; for $z^4$ it gives $5h^4/6$ against $h^4/5$, so the wall cell is exact through cubics, error
$O(h^4)$. Interior: expanding about $z_i$, the trapezoid is $F + \tfrac{h^2}{8}F''$, the 4-face difference is
$2h^2F''$, so $W_i/g_1 = F + \tfrac{h^2}{24}F'' + O(h^4) = \langle F\rangle_i + O(h^4)$.

**8.6 Why $E + P$ is conserved (exactly, not to truncation error).** Sum (8.6)·$h_i$ over the column using the
definition in 8.5: $\sum_iW_ih_i + \dot P = -\sum_i(\phi_{i+1/2}F_{i+1/2} - \phi_{i-1/2}F_{i-1/2}) =
-(\phi_{n-1/2}F_{n-1/2} - \phi_{-1/2}F_{-1/2}) = 0$. Nothing else is used: not the stencil weights, not the grid
spacing, not the size of $F$. The energy fluxes other than gravity work telescope as before. So in exact arithmetic
$E + P$ is constant per stage; every RK stage is $u \leftarrow a u_0 + b u + c\,dt\,\dot u$ and $E + P$ is linear in $u$,
so it is constant per step too, to round-off. $E + \mathrm{PE}_d$ is not conserved any more: it changes by
$-g_1\sum_ih_i\sigma_i^2s_i[\Delta\rho]$ per stage, an $O(h^2)$ amount that is the error of $\mathrm{PE}_d$ itself.
*Horizontal directions.* In 2-D/3-D, x2/x3 fluxes move mass between columns at the same level $i$ and book no
gravity work. $\sigma_i^2$, $h_i$ and the stencil (8.4) are the same in every column and $s$ is linear, so
$\sum_{\rm columns}P = \sum_ih_i[\phi(z_i)\bar M_i - g_1\sigma_i^2s_i[\bar M]]$ with $\bar M_i$ the level's total mass,
which x2/x3 fluxes conserve (periodic or closed lateral boundaries): $E + P$ stays exact.
*Several blocks in x1.* Each block uses its own one-sided stencil at its x1 ends, so $P = \sum_{\rm blocks}P_b$; at a
shared face both blocks use the same $F$ and $\phi$, the $\phi F$ terms cancel between them, and global $E + P$ is exact.
*Rest.* The added term is proportional to $\dot\rho$; at discrete hydrostatic rest it is zero to round-off and the
momentum balance is not touched.

**8.7 Accuracy.** The exact cell budget is $g_1h_i\langle F\rangle_i = -\tfrac{d}{dt}\mathrm{PE}^{\rm exact}_i -
(\phi F)\big|_{i-1/2}^{i+1/2}$; subtract the definition of $W_i$: $W_ih_i - g_1h_i\langle F\rangle_i =
\tfrac{d}{dt}(\mathrm{PE}^{\rm exact}_i - P_i) = O(h^5)$ by (8.5), i.e. $O(h^4)$ per unit length in every cell, wall
cells included. Measured (F-replica §6, $|W - g_1\langle F\rangle|/|g_1|$, profile $F = e^{-z}\sin(\pi z/4)$ on $[0,4]$,
closed walls, nz 16 → 128):

| Cartesian | first cell (wall) | slope | last cell (wall) | slope | interior | slope |
|---|---|---|---|---|---|---|
| face + H (today, cp3/cp5/weno5) | 1.65e-2 → 2.05e-3 | 1.00 | 3.04e-4 → 3.75e-5 | 1.00 | 3.7e-5 → 1.0e-8 | 4.00 |
| F (8.6) | 1.29e-4 → 3.08e-8 | 4.02 | 1.46e-6 → 5.42e-10 | 3.96 | 6.9e-5 → 1.85e-8 | 4.00 |
| face (plm, no H) | — | 2 | — | 2 | — | 2 |

(The last cell is small because $F$ has decayed by $e^{-4}$ there.) The change F makes against today's face+H on a
Cartesian weno5 deck (F-replica §7, $\max|\Delta W|/\max|W|$): interior $1.2\times10^{-4} \to 3.2\times10^{-8}$
(slope 4.00, so the interior is unchanged to $O(h^4)$), first wall cell $6.2\times10^{-2} \to 7.7\times10^{-3}$ and
last wall cell $1.2\times10^{-3} \to 1.4\times10^{-4}$ (slope 1: the change is the removal of face+H's $O(h)$ wall error).
Against plm decks (no H) the change is the $O(h^2)$ trapezoid term in every cell.

**8.8 Porting checklist.** (i) The sum of mass rows that the x1 mass flux carries, as $\dot\rho$. (ii) $\sigma^2 = h^2/12$
per cell. (iii) The 3-point slope (8.4), one-sided at both x1 ends of every block. (iv) Add $g_1\sigma^2s[\Delta\rho]$ to
the energy row after the face work, where $\Delta\rho$ is that stage's x1 density change (implicit solvers: the solved
change). (v) Turn H off (F already removes the $F''$ term; F + H is $O(h^2)$ again). (vi) Test: closed column, any
flow, $\Delta(E + P)$ per step at round-off with $P$ from (8.5).

## 9. F against the $\bar r$ potential form

A smaller alternative keeps the face form and the curvature flux but moves the potential: $\phi_c = -g_1\bar r$,
$\bar r = (r_{i+1/2} + r_{i-1/2})/2$, with the cp3/cp5/weno5 curvature flux applied to $r^2m$,
$A_fH_f = \tfrac{1}{12}(r_{c,i} - r_{c,i-1})(\bar r_i^2m_i - \bar r_{i-1}^2m_{i-1})$, zero at the walls. It is a
divergence plus a face form, so it conserves $E + P_{\bar r}$, $P_{\bar r} = \sum_iV_i\rho_i\phi(\bar r_i)$. Checked in
F-replica §8; spherical, closed walls, the profile of §5, $R = 5H$ unless noted.

| | $\bar r$ form | F |
|---|---|---|
| conserved functional, one step, random $F_f$ and $m$, / $\sum\lvert WV\rvert$ | $E + P_{\bar r}$: 5e-15 ($R = H, 5H$), $\lesssim$ 2e-12 ($R = 1000H$) | $E + P$: 6e-15, $\lesssim$ 2e-12 |
| interior max cell error, nz 64 / 256 | 1.1e-7 / 5.4e-10 ($h^{3.9}$) | 1.4e-7 / 5.4e-10 ($h^{4.0}$) |
| first (wall) cell, nz 64 / 256 | **4.0e-3 / 1.0e-3 ($h^{1.0}$)** | 9.0e-8 / 1.8e-10 ($h^{4.4}$) |
| last (wall) cell, nz 64 / 256 | **7.6e-5 / 1.9e-5 ($h^{1.0}$)** | 4.5e-9 / 2.0e-11 |
| column-summed work error, nz 64, $R = 5H$ / $1000H$ | **+3.39e-4 / +5.25e-4** | -4.7e-7 / -8.0e-7 |
| same, nz 256 | +2.1e-5 / +3.3e-5 ($h^2$) | -1.9e-9 / -3.4e-9 ($h^4$) |
| conserved PE against $\int\rho\phi\,dV$, nz 64 / 256 | $P_{\bar r}$: 3.5e-5 / 2.2e-6 ($h^2$) | $P$: 3.0e-8 / 1.3e-10 ($h^4$) |

($R = 1000H$ conservation is the cancellation floor of §5, the same for both forms. For reference, $\mathrm{PE}_d$ is
5.3e-5 / 3.3e-6 off at nz 64 / 256.)

*Why the $\bar r$ form's wall cells stay $O(h)$.* Its $H$ is zero at the walls, as today's is, so its wall cells are
face+H's: the first cell is 1.02e-3 for both at nz 256 (F-replica §5, §8b). Its column total equals the face form's at
$R = 1000H$ (+5.249e-4 for both, §7 settling table) and is close to it at $R = 5H$ (+3.39e-4 against +3.55e-4). The
interior error is $O(h^4)$, the cell-by-cell and column errors are not.

*Why the two forms cannot be equivalent.* A conservative booking conserves $E$ plus its own functional, so its column
work error is the time derivative of that functional's error. $P_{\bar r} - \int\rho\phi\,dV$ is a pure wall term,
$g_1\tfrac{h^2}{12}[r^2\rho]$ (top minus bottom) $+ O(h^4)$ (F-replica §8e: ratio 0.99998 at nz 64, 1.00000 at nz 256),
so the $\bar r$ form's $O(h^2)$ column error sits in its wall cells. Closing $H$ at the walls would break conservation
unless the PE changes as well, and the PE that makes the walls $O(h^4)$ is $P$ of (6): F is the $\bar r$ idea plus the
wall closure. F's $P$ is not of the form $\sum_iV_i\rho_i\phi_{c,i}$, so the §4 lemma (which bounds those) does not
apply to it.

*Scope.* The $\bar r$ form is spherical only and leaves Cartesian unchanged, so it cannot remove the Cartesian $O(h)$
wall error of face+H (§8.7). Adding its $H$ on top of F would remove the $F''$ term twice, as F + H does (§7). F is the
form implemented.

## 10. Every place that computes a PE, under `SNAP_GRAVITY_WORK_RADIAL_EXACT`

F conserves $E + P$, not $E + \mathrm{PE}_d$, so every site that computes or checks a PE has to agree with the switch.
Searched: `src/`, `python/`, `tests/`.

| site | PE used | under the switch |
|---|---|---|
| explicit face work, `hydro_forward.cpp` | $P$ | the booked work (7); the reference |
| implicit face work: the matrix's work rows and the projection/clamp work in `implicit_hydro.cpp` | $\mathrm{PE}_d$ increments | consistent: the post-solve term adds $g_1\sigma^2s[\Delta\rho]$ with $\Delta\rho$ the solved change `du - du0`, which includes the redistributed and projected mass; $\Delta(E + P)$ per step $\le 4\times10^{-16}$ on the implicit cases of the test |
| gravity-work fixer (`gwfix_stage` in `hydro_forward.cpp`, the implicit `epe` lambda) and its `fixgrav=` printout | $\mathrm{PE}_d$ | consistent by construction: the fixer runs only with `gravity-work: cell` (`hydro.cpp`), the switch acts only with `gravity-work: face` (`radial_exact_work()`); they never meet |
| cycle diagnostics `pe=` (`print_cycle_diagnostics`, `meshblock.cpp`) | $P$ | logs $P$ via `corrected_pe_work` with the same per-block one-sided slope stencil, so the logged `ie=` + `pe=` is the conserved $E + P$ (it logged $\mathrm{PE}_d$ before; the test's check 5 failed on that at $\sim2\times10^{-5}$ relative and passes at $\le 3\times10^{-14}$) |
| netCDF outputs | none | no PE field is written |
| E+PE$_d$ oracles in other tests (`test_horizontal_flux_covariance`, `test_implicit_stratified_solid`, `test_implicit_face_work_operator`, `test_gravity_work_fixer`, `test_forcing.cpp`) | $\mathrm{PE}_d$ | correct as written: they run with the switch unset; the switch-on oracle is `tests/test_gravity_work_radial_exact.py` ($E + P$ per step, and the logged `ie=` + `pe=` against it) |


## Verification script `docs/derivations/curved_gravity_work_weight.py` (at `6499404`)

```python
#!/usr/bin/env python3
"""Replica of snapy's x1 face-form gravity work on a spherical-polar radial grid.

Per steradian: A(r) = r^2, V = (r+^3 - r-^3)/3, r_c = x1v = 3/4 (r+^4 - r-^4)/(r+^3 - r-^3)
(src/coord/spherical_polar.cpp radial_centers). grav1 < 0, phi = -grav1 r.

Weights per unit volume on (F+, F-), cell work = grav1 (a F+ + b F-):
  face     a = A+ (r+ - r_c)/V,       b = A- (r_c - r-)/V      (snapy 8cea3ae, hydro_forward.cpp:676-692)
  exact    a = (r_c - r-)/h,          b = (r+ - r_c)/h         (unique 2-point weights exact for F in {1, r}
                                                                 on the r^2 measure)
  cons(s)  a = A+ (s+ - r_c)/V,       b = A- (r_c - s-)/V      (face form with face potential at s_f)

Checks
 1. sympy: per-face weight sum minus the discrete-PE requirement A_f (r_c,i+1 - r_c,i), exact closed form.
 2. numpy: closed-wall column, one step: (dE + dPE) / dt, relative to the step's sum |work|, and relative
    to E+PE with E = PE (order of magnitude of a real column).
 3. numpy: booked work vs exact r^2-measure cell average on a smooth profile, h-ladder at fixed R and
    R-ladder at fixed h/H; reports the error with and without the common Cartesian (h^2/12) F'' piece.
Usage: python curved_gravity_work_weight.py   (prints every number in curved-gravity-work-weight.md)
"""

import numpy as np
import sympy as sp
from numpy.polynomial.legendre import leggauss

OUT = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); OUT.append(s)

# ---------------------------------------------------------------- 1. sympy closed forms
R, h = sp.symbols("R h", positive=True)
def cell(rm, rp):
    V = (rp**3 - rm**3) / 3
    rc = sp.Rational(3, 4) * (rp**4 - rm**4) / (rp**3 - rm**3)
    return V, rc
Vi, rci = cell(R - h, R)        # cell below face f (face at r = R)
Vj, rcj = cell(R, R + h)        # cell above
need = R**2 * (rcj - rci)       # sum the two cells must book on F_f for E+PE to telescope
S_face = R**2 * (R - rci) + R**2 * (rcj - R)
S_exact = Vi * (rci - (R - h)) / h + Vj * ((R + h) - rcj) / h
say("== 1. per-face weight sum S_f minus need A_f (r_c,i+1 - r_c,i), uniform h, face at R (per sr, x grav1 F_f) ==")
say("face :", sp.simplify(S_face - need))
dex = sp.simplify(S_exact - need)
say("exact:", dex)
say("exact, series in h:", sp.series(dex, h, 0, 6).removeO().expand())
say("exact, relative to need, series:", sp.series(sp.simplify(dex / need), h, 0, 5).removeO().expand())
# leading error terms of the face form (face - exact average), F = F0 + F1 s + ... + F4 s^4/24 about rbar
s, F0, F1, F2, F3, F4, rb = sp.symbols("s F0 F1 F2 F3 F4 rbar")
Fs = F0 + F1 * s + F2 * s**2 / 2 + F3 * s**3 / 6 + F4 * s**4 / 24
rm, rp = rb - h / 2, rb + h / 2
V = sp.integrate((rb + s)**2, (s, -h / 2, h / 2))
rc = sp.integrate((rb + s)**3, (s, -h / 2, h / 2)) / V
avg = sp.integrate((rb + s)**2 * Fs, (s, -h / 2, h / 2)) / V
Fp, Fm = Fs.subs(s, h / 2), Fs.subs(s, -h / 2)
face = (rp**2 * (rp - rc) * Fp + rm**2 * (rc - rm) * Fm) / V
exw = ((rc - rm) * Fp + (rp - rc) * Fm) / h
say("== leading error terms (booked - exact average) / grav1 ==")
say("face :", sp.series(sp.simplify(face - avg), h, 0, 4).removeO().expand())
say("exact:", sp.collect(sp.series(sp.simplify(exw - avg), h, 0, 6).removeO().expand(), h))
# conservative family s_f = r_f + lam h^2 / r_f: leading F and F' coefficients
lam = sp.symbols("lam")
sp_, sm_ = rp + lam * h**2 / rp, rm + lam * h**2 / rm
cons = (rp**2 * (sp_ - rc) * Fp + rm**2 * (rc - sm_) * Fm) / V
ce = sp.series(sp.simplify(cons - avg), h, 0, 4).removeO().expand()
say("cons(lam):", sp.collect(ce, [F0, F1, F2]))
say("  F0 coeff zero at lam =", sp.solve(sp.expand(ce).coeff(F0), lam),
    "; F1 coeff zero at lam =", sp.solve(sp.expand(ce).coeff(F1), lam))

# ---------------------------------------------------------------- numpy grid helpers
def grid(r0, L, n):
    rf = r0 + L * np.arange(n + 1) / n
    rm, rp = rf[:-1], rf[1:]
    V = (rp**3 - rm**3) / 3.
    rc = 0.75 * (rp**4 - rm**4) / (rp**3 - rm**3)
    return rf, rm, rp, V, rc

def weights(kind, rf, rm, rp, V, rc, lam=0.):
    hh = rp - rm
    if kind == "face":
        return rp**2 * (rp - rc) / V, rm**2 * (rc - rm) / V
    if kind == "exact":
        return (rc - rm) / hh, (rp - rc) / hh
    if kind == "cons":
        sf = rf + lam * hh.mean()**2 / rf
        return rp**2 * (sf[1:] - rc) / V, rm**2 * (rc - sf[:-1]) / V
    raise ValueError(kind)

# ---------------------------------------------------------------- 2. one step, closed column
say("== 2. closed-wall column, one step: (dE + dPE)/dt  [grav1 = -10, F_f random interior, F = 0 at walls] ==")
rng = np.random.default_rng(42)
g1 = -10.
for (r0, H, nz) in [(5., 1., 64), (1000., 1., 64), (5., 1., 256), (1.0, 1., 32)]:
    L = 3 * H
    rf, rm, rp, V, rc = grid(r0, L, nz)
    Ff = np.zeros(nz + 1); Ff[1:-1] = rng.standard_normal(nz - 1)
    dM = -(rp**2 * Ff[1:] - rm**2 * Ff[:-1])            # per unit dt
    dPE = np.sum(-g1 * rc * dM)
    PE = np.sum(-g1 * rc * V)                           # rho = 1 column
    for kind, lamv in [("face", 0.), ("exact", 0.), ("cons", 1 / 6), ("cons", -1 / 6)]:
        a, b = weights(kind, rf, rm, rp, V, rc, lamv)
        W = g1 * (a * Ff[1:] + b * Ff[:-1])             # per unit volume per unit dt
        dE = np.sum(W * V)
        d = dE + dPE
        say("  R=%-6g h/R=%.1e %-5s%-6s (dE+dPE)/sum|W V| = %+.3e   /(E+PE) = %+.3e"
            % (r0, L / nz / r0, kind, "" if kind != "cons" else "%+.3f" % lamv,
               d / np.sum(np.abs(W * V)), d / (2 * PE)))

# ---------------------------------------------------------------- 3. convergence on a smooth profile
say("== 3. booked work vs exact r^2-measure cell average, F = exp(-(r-r0)/H) sin(pi (r-r0)/L), L = 4H ==")
xg, wg = leggauss(12)
def Ffun(r, r0, H, L): return np.exp(-(r - r0) / H) * np.sin(np.pi * (r - r0) / L)
def F2fun(r, r0, H, L):
    k = np.pi / L; z = r - r0; e = np.exp(-z / H)
    return e * ((1 / H**2 - k**2) * np.sin(k * z) - 2 * k / H * np.cos(k * z))
def errs(r0, H, nz, kind):
    L = 4 * H
    rf, rm, rp, V, rc = grid(r0, L, nz)
    Ff = Ffun(rf, r0, H, L)
    a, b = weights(kind, rf, rm, rp, V, rc)
    booked = a * Ff[1:] + b * Ff[:-1]
    rq = 0.5 * (rp + rm)[:, None] + 0.5 * (rp - rm)[:, None] * xg[None, :]
    avg = (0.5 * (rp - rm)[:, None] * wg[None, :] * rq**2 * Ffun(rq, r0, H, L)).sum(1) / V
    e = booked - avg
    hh = L / nz
    cart = hh**2 / 12. * F2fun(rc, r0, H, L)            # common Cartesian trapezoid piece
    return np.max(np.abs(e)), np.max(np.abs(e - cart))
say("  h-ladder at fixed R = 5H (H = 1): max|e| and max|e - (h^2/12)F''|; slope = log2 ratio")
for kind in ["face", "exact"]:
    prev = None
    for nz in [16, 32, 64, 128, 256]:
        e, ec = errs(5., 1., nz, kind)
        sl = "" if prev is None else "  slopes %.2f %.2f" % (np.log2(prev[0] / e), np.log2(prev[1] / ec))
        say("   %-5s nz %4d  h=%.4f  %.3e  %.3e%s" % (kind, nz, 4. / nz, e, ec, sl)); prev = (e, ec)
say("  R-ladder at fixed h/H = 1/16: max|e - (h^2/12)F''| (face should scale ~ h^2/R, exact ~ h^4-level)")
for kind in ["face", "exact"]:
    for r0 in [5., 50., 500., 5000.]:
        e, ec = errs(r0, 1., 64, kind)
        say("   %-5s R/H %6g  %.3e  x R = %.3e" % (kind, r0, ec, ec * r0))
```


## Verification script `docs/derivations/optionF_replica.py` (at `6499404`)

```python
#!/usr/bin/env python3
"""Option F: face-form gravity work plus the work implied by a corrected discrete PE functional.

P[rho] = sum_i V_i [rho_i phi(r_v,i) - g1 var_i s_i[rho]],  g1 = grav1 < 0, phi = -g1 r,
  var_i = <(r - r_v)^2>_V (exact r^2-measure variance of r in cell i), s_i[rho] = sum_k d_ik rho_k the slope
  of the quadratic through the cell values at r_v (interior: i-1, i, i+1; wall cells: one-sided 0,1,2).
  P_i is the exact cell PE  g1-free form  int rho phi dV  to O(h^4): rho phi integrates to m phi(r_v) - g1 V cov,
  cov = var * rho' + O(h^4).
Work: W_i V_i := -dP_i/dt - Delta_i(A F phi(r_f)) = W_face,i V_i + g1 V_i var_i s_i[rhodot],
  rhodot_k = -(A_+ F_+ - A_- F_-)_k / V_k (the x1 mass tendency). Sum_i W_i V_i + dP/dt = 0 identically (closed walls).
Checks (prints every number quoted in sections 7-9 of curved-gravity-work-weight.md):
  1. one step, closed column, random F: (dE + dP), (dE + dPE_d), each / sum|W V|; spherical R = H, 5H, 1000H, and Cartesian.
  2. booked work vs exact r^2-measure cell average on smooth closed-wall profiles: interior and wall cells, h- and R-ladders.
  3. Cartesian: option F minus face form (the change it makes there).
  4. settling check for the ablation: conservation defect and booked-work error of A, B, C, D, F on a closed column
     carrying the smooth profile (column sums).
  5. F and face form with the cp3/cp5/weno5 curvature flux H on top (F + H double counts).
  6. cell-by-cell errors, wall cells included, Cartesian and spherical.
  7. Cartesian: F against today's face+H, by region, and the uniform-grid closed forms.
  8. F against the r-bar potential form (phi_c at rbar, H on r^2 m): conservation, cell and column errors,
     accuracy of each conserved functional.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss

xg, wg = leggauss(16)
G1 = -10.


def grid(r0, L, n, cart=False):
    rf = r0 + L * np.arange(n + 1) / n
    rm, rp = rf[:-1], rf[1:]
    if cart:
        A = np.ones_like(rf)
        V = rp - rm
        rv = 0.5 * (rp + rm)
        var = (rp - rm)**2 / 12.
    else:
        A = rf**2
        V = (rp**3 - rm**3) / 3.
        rv = 0.75 * (rp**4 - rm**4) / (rp**3 - rm**3)
        hh, rb = rp - rm, 0.5 * (rp + rm)
        dl = rb * hh**3 / (6. * V)  # r_v - rbar
        var = (rb**2 * hh**3 / 12. + hh**5 / 80.) / V - dl**2  # <(r - r_v)^2>_V, cancellation-free
    return dict(rf=rf, rm=rm, rp=rp, A=A, V=V, rv=rv, var=var, n=n)


def slope_matrix(g):
    """d_ik: derivative at r_v,i of the quadratic through (r_v,k, rho_k), k in the 3-point stencil."""
    n, x = g["n"], g["rv"]
    D = np.zeros((n, n))
    for i in range(n):
        ks = [i - 1, i, i + 1] if 0 < i < n - 1 else ([0, 1, 2] if i == 0 else [n - 3, n - 2, n - 1])
        for a in ks:
            # d/dx of Lagrange basis l_a at x_i
            others = [b for b in ks if b != a]
            den = np.prod([x[a] - x[b] for b in others])
            num = sum(np.prod([x[i] - x[c] for c in others if c != b]) for b in others)
            D[i, a] = num / den
    return D


def rhodot(g, Ff):
    return -(g["A"][1:] * Ff[1:] - g["A"][:-1] * Ff[:-1]) / g["V"]


def work(kind, g, Ff, lam=0.):
    """booked work per unit volume per unit time (grav1 included)"""
    rf, rm, rp, A, V, rv = g["rf"], g["rm"], g["rp"], g["A"], g["V"], g["rv"]
    h = rp - rm
    if kind in ("face", "F", "cons"):
        sf = rf if kind != "cons" else rf + lam * h.mean()**2 / rf
        W = G1 * (A[1:] * (sf[1:] - rv) * Ff[1:] + A[:-1] * (rv - sf[:-1]) * Ff[:-1]) / V
        if kind == "F":
            W = W + G1 * g["var"] * (g["D"] @ rhodot(g, Ff))
        return W
    if kind == "exact":
        return G1 * ((rv - rm) / h * Ff[1:] + (rp - rv) / h * Ff[:-1])
    raise ValueError(kind)


def P(g, rho):
    return np.sum(g["V"] * (rho * (-G1 * g["rv"]) - G1 * g["var"] * (g["D"] @ rho)))


def PEd(g, rho):
    return np.sum(g["V"] * rho * (-G1 * g["rv"]))


def mk(r0, L, n, cart=False):
    g = grid(r0, L, n, cart)
    g["D"] = slope_matrix(g)
    return g


# ------------------------------------------------------------------ 1. conservation, one step
print("== 1. closed column, random interior F, one unit-dt step: defect / sum|W V| ==")
rng = np.random.default_rng(42)
for (r0, cart, n) in [(5., False, 64), (1000., False, 64), (1., False, 32), (5., True, 64)]:
    g = mk(r0, 3., n, cart)
    Ff = np.zeros(n + 1); Ff[1:-1] = rng.standard_normal(n - 1)
    rd = rhodot(g, Ff)
    rho = np.exp(-(g["rv"] - r0))
    for kind in ["face", "F"]:
        W = work(kind, g, Ff)
        dE = np.sum(W * g["V"]); s = np.sum(np.abs(W * g["V"]))
        dP = P(g, rho + rd) - P(g, rho)          # P, PE_d linear in rho
        dPd = PEd(g, rho + rd) - PEd(g, rho)
        print("  %-4s R=%-6g %-4s  (dE+dP)/sum|WV| %+.3e   (dE+dPE_d)/sum|WV| %+.3e   (dE+dP)/(E+P) %+.3e"
              % ("cart" if cart else "sph", r0, kind, (dE + dP) / s, (dE + dPd) / s, (dE + dP) / (2 * P(g, rho))))


# ------------------------------------------------------------------ 2. convergence on a smooth closed-wall profile
def Ffun(r, r0, L, H=1.):
    return np.exp(-(r - r0) / H) * np.sin(np.pi * (r - r0) / L)


def errs(r0, n, kind, cart=False, L=4., lam=0.):
    g = mk(r0, L, n, cart)
    Ff = Ffun(g["rf"], r0, L)
    W = work(kind, g, Ff, lam)
    rm, rp = g["rm"], g["rp"]
    rq = 0.5 * (rp + rm)[:, None] + 0.5 * (rp - rm)[:, None] * xg[None, :]
    wq = rq**2 if not cart else np.ones_like(rq)
    avg = G1 * (0.5 * (rp - rm)[:, None] * wg[None, :] * wq * Ffun(rq, r0, L)).sum(1) / g["V"]
    e = (W - avg) / abs(G1)
    return np.max(np.abs(e[2:-2])), np.max(np.abs(e[[0, 1, -2, -1]])), g, W, avg


print("== 2. max|W - g1<F>_V|/|g1|, F = exp(-(r-r0)/H) sin(pi (r-r0)/4H), interior cells | 2 wall cells each side ==")
for cart, r0 in [(False, 5.), (True, 5.)]:
    for kind in ["face", "F"]:
        prev = None
        for n in [16, 32, 64, 128, 256]:
            ei, ew, *_ = errs(r0, n, kind, cart)
            sl = "" if prev is None else "  slopes %.2f %.2f" % (np.log2(prev[0] / ei), np.log2(prev[1] / ew))
            print("  %-4s R=%g %-4s nz %4d  interior %.3e  wall %.3e%s"
                  % ("cart" if cart else "sph", r0, kind, n, ei, ew, sl)); prev = (ei, ew)
print("  R-ladder, nz 64 (h = H/16), option F interior | wall; face interior x R")
for r0 in [5., 50., 500., 5000.]:
    ei, ew, *_ = errs(r0, 64, "F")
    fi, *_ = errs(r0, 64, "face")
    print("   R/H %6g  F %.3e | %.3e   face x R %.3e" % (r0, ei, ew, fi * r0))

# ------------------------------------------------------------------ 3. Cartesian change
print("== 3. Cartesian: option F - face form, nz 64, same profile: max|dW|/max|W| ==")
g = mk(5., 4., 64, True); Ff = Ffun(g["rf"], 5., 4.)
d = work("F", g, Ff) - work("face", g, Ff)
print("  interior %.3e   wall cells %.3e   (relative to max|W| %.3e)"
      % (np.max(np.abs(d[2:-2])) / np.max(np.abs(work("face", g, Ff))),
         np.max(np.abs(d[[0, 1, -2, -1]])) / np.max(np.abs(work("face", g, Ff))), np.max(np.abs(work("face", g, Ff)))))

# ------------------------------------------------------------------ 4. settling check, column sums
print("== 4. column sums on the smooth profile (closed walls), per option: ==")
print("   sum(W - g1<F>)V / sum|g1<F>|V  = booked-work error;  (sum W V + dPE_d)/sum|g1<F>|V = PE_d defect")
for r0 in [5., 1000.]:
    for n in [32, 64]:
        for kind, lam in [("face", 0.), ("exact", 0.), ("cons", 1 / 6), ("cons", -1 / 6), ("F", 0.)]:
            ei, ew, g, W, avg = errs(r0, n, kind, lam=lam)
            Ff = Ffun(g["rf"], r0, 4.)
            dPd = np.sum(g["V"] * rhodot(g, Ff) * (-G1 * g["rv"]))
            nrm = np.sum(np.abs(avg) * g["V"])
            lab = {"face": "A face", "exact": "B exact", "F": "F"}.get(kind, "C" if lam > 0 else "D")
            print("   R/H %6g nz %3d %-8s work err %+.4e   PE_d defect %+.4e   cell max|err|/max|g1<F>| %.3e"
                  % (r0, n, lab, np.sum((W - avg) * g["V"]) / nrm, (np.sum(W * g["V"]) + dPd) / nrm,
                     max(ei, ew) * abs(G1) / np.max(np.abs(avg))))

# ------------------------------------------------------------------ 5. interaction with the cp3/cp5/weno5 curvature flux
# hydro_forward.cpp subtracts grav1 * div(A H)/V, H_f = (x1v_i - x1v_{i-1})/12 (m_i - m_{i-1}), H = 0 at walls,
# m = the cell mass flux rho*v (here: the exact cell average <F>_V). It is a divergence, so it keeps E + PE_d.
def errs_H(r0, n, kind, cart=False, L=4.):
    ei, ew, g, W, avg = errs(r0, n, kind, cart, L)
    m = avg / G1
    H = np.zeros(n + 1); H[1:-1] = (g["rv"][1:] - g["rv"][:-1]) / 12. * (m[1:] - m[:-1])
    W = W - G1 * (g["A"][1:] * H[1:] - g["A"][:-1] * H[:-1]) / g["V"]
    e = (W - avg) / abs(G1)
    return np.max(np.abs(e[2:-2])), np.max(np.abs(e[[0, 1, -2, -1]])), W
print("== 5. with the cp3/cp5/weno5 curvature flux H on top: max|W - g1<F>_V|/|g1|, interior | wall ==")
for cart, r0 in [(False, 5.), (True, 5.)]:
    for kind in ["face", "F"]:
        prev = None
        for n in [32, 64, 128, 256]:
            ei, ew, _ = errs_H(r0, n, kind, cart)
            sl = "" if prev is None else "  slopes %.2f %.2f" % (np.log2(prev[0] / ei), np.log2(prev[1] / ew))
            print("  %-4s R=%g %-4s+H nz %4d  interior %.3e  wall %.3e%s"
                  % ("cart" if cart else "sph", r0, kind, n, ei, ew, sl)); prev = (ei, ew)
print("  R-ladder nz 64, face+H interior error x R^2 (a -h^2/(6 R^2) F residue gives a constant):")
for r0 in [5., 50., 500.]:
    ei, ew, _ = errs_H(r0, 64, "face")
    print("   R/H %6g  face+H interior %.3e  x R^2 %.3e" % (r0, ei, ei * r0**2))
g = mk(5., 4., 64, True); Ff = Ffun(g["rf"], 5., 4.)
_, _, WH = errs_H(5., 64, "face", True)
print("  Cartesian nz 64: max|W_F - W_face+H| / max|W| = %.3e (both remove h^2/12 F'')"
      % (np.max(np.abs(work("F", g, Ff) - WH)) / np.max(np.abs(WH))))

# ------------------------------------------------------------------ 6. wall cells one by one
print("== 6. |W - g1<F>_V|/|g1| cell by cell, nz 16/32/64/128 (slope = log2 ratio), same profile, closed walls ==")
print("   first = cell 0 (on the lower wall), second = cell 1, last = cell n-1 (on the upper wall),")
print("   interior = max over cells 2..n-3")
for cart in (True, False):
    for kind in ("face+H", "F"):
        prev = None
        for n in (16, 32, 64, 128):
            if kind == "F":
                *_, g, W, avg = errs(5., n, "F", cart)
            else:
                *_, W = errs_H(5., n, "face", cart)
                _, _, g, _, avg = errs(5., n, "face", cart)
            e = np.abs(W - avg) / abs(G1)
            row = np.array([e[0], e[1], e[-2], e[-1], np.max(e[2:-2])])
            sl = "" if prev is None else "  slopes " + " ".join("%.2f" % v for v in np.log2(prev / row))
            print("  %-4s R=5 %-6s nz %4d  first %.2e second %.2e second-last %.2e last %.2e interior %.2e%s"
                  % ("cart" if cart else "sph", kind, n, *row, sl))
            prev = row

# ------------------------------------------------------------------ 7. Cartesian: F against today's face+H, by region
print("== 7. Cartesian, F - (face+H), max|dW| / max|W|: interior (cells 2..n-3) | first cell | last cell ==")
prev = None
for n in (16, 32, 64, 128):
    _, _, g, WF, _ = errs(5., n, "F", True)
    *_, WH = errs_H(5., n, "face", True)
    d, s = np.abs(WF - WH), np.max(np.abs(WH))
    row = np.array([np.max(d[2:-2]), d[0], d[-1]]) / s
    sl = "" if prev is None else "  slopes " + " ".join("%.2f" % v for v in np.log2(prev / row))
    print("  nz %4d  interior %.2e  first %.2e  last %.2e%s" % (n, *row, sl)); prev = row
print("  uniform-grid closed forms (sec 8): interior W/g1 = (F+ + F-)/2 - (F[i+3/2] - F[i+1/2] - F[i-1/2] + F[i-3/2])/24,")
print("  wall cell W/g1 = (19 F[1/2] - 5 F[3/2] + F[5/2])/24; check against the matrix form on random F:")
g = mk(0., 1., 12, True); Ff = np.zeros(13); Ff[1:-1] = np.random.default_rng(7).standard_normal(11)
W = work("F", g, Ff) / G1
Wi = 0.5 * (Ff[3:-2] + Ff[2:-3]) - (Ff[4:-1] - Ff[3:-2] - Ff[2:-3] + Ff[1:-4]) / 24.
print("  interior max diff %.1e   wall cell diff %.1e"
      % (np.max(np.abs(W[2:-2] - Wi)), abs(W[0] - (19 * Ff[1] - 5 * Ff[2] + Ff[3]) / 24.)))
print("  upper wall cell W/g1 = (19 F[n-3/2] - 5 F[n-5/2] + F[n-7/2])/24: diff %.1e"
      % abs(W[-1] - (19 * Ff[-2] - 5 * Ff[-3] + Ff[-4]) / 24.))

# ------------------------------------------------------------------ 8. F against the r-bar potential form (derivation sec 9)
# r-bar form: face form with phi_c = g1-potential at rbar = (r+ + r-)/2, and the curvature flux applied to r^2 m:
# A_f H_f = (x1v_i - x1v_{i-1})/12 (rbar_i^2 m_i - rbar_{i-1}^2 m_{i-1}), zero at the walls; it conserves
# E + P_rbar, P_rbar = sum V rho (-g1 rbar). F conserves E + P, P of eq. (6). m = <F>_V as in sec 5.
def work_rbar(g, Ff, m):
    rf, rm, rp, A, V, rv = g["rf"], g["rm"], g["rp"], g["A"], g["V"], g["rv"]
    rb = 0.5 * (rp + rm)
    W = G1 * (A[1:] * (rf[1:] - rb) * Ff[1:] + A[:-1] * (rb - rf[:-1]) * Ff[:-1]) / V
    AH = np.zeros(g["n"] + 1); AH[1:-1] = (rv[1:] - rv[:-1]) / 12. * (rb[1:]**2 * m[1:] - rb[:-1]**2 * m[:-1])
    return W - G1 * (AH[1:] - AH[:-1]) / V


def Prbar(g, rho):
    return np.sum(g["V"] * rho * (-G1 * 0.5 * (g["rp"] + g["rm"])))


print("== 8. F vs the r-bar potential form (phi_c at rbar + curv on r^2 m), spherical ==")
print("  8a. one step, closed column, random F and m: defect against each form's own functional / sum|W V|")
rng = np.random.default_rng(42)
for r0 in (1., 5., 1000.):
    g = mk(r0, 3., 64)
    Ff = np.zeros(65); Ff[1:-1] = rng.standard_normal(63); m = rng.standard_normal(64)
    rho, rd = np.exp(-(g["rv"] - r0)), rhodot(g, Ff)
    Wb, WF = work_rbar(g, Ff, m), work("F", g, Ff)
    print("   R/H %6g  rbar: (dE+dP_rbar) %+.1e  (dE+dP) %+.1e | F: (dE+dP) %+.1e  (dE+dP_rbar) %+.1e"
          % (r0, (np.sum(Wb * g["V"]) + Prbar(g, rd)) / np.sum(np.abs(Wb * g["V"])),
             (np.sum(Wb * g["V"]) + P(g, rd)) / np.sum(np.abs(Wb * g["V"])),
             (np.sum(WF * g["V"]) + P(g, rd)) / np.sum(np.abs(WF * g["V"])),
             (np.sum(WF * g["V"]) + Prbar(g, rd)) / np.sum(np.abs(WF * g["V"]))))


def errs_rbar(r0, n, L=4.):
    _, _, g, _, avg = errs(r0, n, "face", False, L)
    W = work_rbar(g, Ffun(g["rf"], r0, L), avg / G1)
    return np.abs(W - avg) / abs(G1), g, W, avg


print("  8b. cell error |W - g1<F>_V|/|g1|, same smooth profile as sec 2, R = 5H: first | second | last | interior")
for kind in ("rbar", "F"):
    prev = None
    for n in (16, 32, 64, 128, 256):
        if kind == "F":
            *_, g, W, avg = errs(5., n, "F"); e = np.abs(W - avg) / abs(G1)
        else:
            e, *_ = errs_rbar(5., n)
        row = np.array([e[0], e[1], e[-1], np.max(e[2:-2])])
        sl = "" if prev is None else "  slopes " + " ".join("%.2f" % v for v in np.log2(prev / row))
        print("   %-4s nz %4d  first %.2e second %.2e last %.2e interior %.2e%s" % (kind, n, *row, sl)); prev = row
print("  8c. column-summed work error sum(W - g1<F>)V / sum|g1<F>|V (what a column eps diagnostic sees), R = 5H | 1000H")
for n in (16, 32, 64, 128, 256):
    out = []
    for r0 in (5., 1000.):
        e, g, Wb, avg = errs_rbar(r0, n)
        *_, WF, _ = errs(r0, n, "F")
        nrm = np.sum(np.abs(avg) * g["V"])
        out += [np.sum((Wb - avg) * g["V"]) / nrm, np.sum((WF - avg) * g["V"]) / nrm]
    print("   nz %4d  R=5: rbar %+.3e  F %+.3e   R=1000: rbar %+.3e  F %+.3e" % (n, *out))
print("  8d. accuracy of each conserved functional: |P - int rho phi dV| / |int rho phi dV|, rho = exp(-(r-r0)), R = 5H, L = 4H")
for n in (16, 32, 64, 128, 256):
    g = mk(5., 4., n)
    rq = 0.5 * (g["rp"] + g["rm"])[:, None] + 0.5 * (g["rp"] - g["rm"])[:, None] * xg[None, :]
    wq = 0.5 * (g["rp"] - g["rm"])[:, None] * wg[None, :] * rq**2
    rho = (wq * np.exp(-(rq - 5.))).sum(1) / g["V"]          # exact cell averages
    ex = (wq * np.exp(-(rq - 5.)) * (-G1 * rq)).sum()
    print("   nz %4d  P_d (x1v) %.2e   P_rbar %.2e   P (F) %.2e"
          % (n, abs(PEd(g, rho) - ex) / ex, abs(Prbar(g, rho) - ex) / ex, abs(P(g, rho) - ex) / ex))
print("  8e. P_rbar - int rho phi dV against the pure wall term g1 h^2/12 [r^2 rho] (top minus bottom), same rho")
for n in (32, 64, 128, 256):
    g = mk(5., 4., n); h = 4. / n
    rq = 0.5 * (g["rp"] + g["rm"])[:, None] + 0.5 * (g["rp"] - g["rm"])[:, None] * xg[None, :]
    wq = 0.5 * (g["rp"] - g["rm"])[:, None] * wg[None, :] * rq**2
    rho = (wq * np.exp(-(rq - 5.))).sum(1) / g["V"]
    ex = (wq * np.exp(-(rq - 5.)) * (-G1 * rq)).sum()
    wall = G1 * h**2 / 12. * (9.**2 * np.exp(-4.) - 5.**2)
    print("   nz %4d  P_rbar - exact %+.6e   wall term %+.6e   ratio %.5f" % (n, Prbar(g, rho) - ex, wall, (Prbar(g, rho) - ex) / wall))
```
