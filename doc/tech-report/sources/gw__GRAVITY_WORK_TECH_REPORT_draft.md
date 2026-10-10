> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Gravity work in snapy's energy equation: cell form vs face form

Phase 1 (correctness: \#283, \#284, \#285, \#286) and phase 2 (which form is physically right, and where)

Technical report, draft. Prepared 2026-10-08 against snapy upstream main 117e449 (\#285 merge). Phase 2 is still running: results that do not exist yet are marked as placeholders.

## 1. Summary for a reader in a hurry

**The term.** snapy's energy $E$ holds no potential energy, so gravity enters the energy equation as a source, the gravity work $-g\rho w$. It can be computed two ways that agree in the continuum (section 2): from the cell's momentum (**cell form**), or from the mass fluxes through the cell's faces (**face form**). The face form conserves $E$ + potential energy exactly, cell by cell; the cell form keeps the energy equation consistent with the momentum equation, and needs a global fixer to conserve $E$ + PE (section 3).

**What was wrong.** Until 10-07 snapy used only the face form (\#202), but its implicit solver linearised the cell form. The face terms sat outside the implicit operator, and a tall column at rest blew up at implicit Courant 65.6 (issue \#283). \#284 made the cell form the default with an exact global E+PE fixer. That fixer had a feedback of its own above Courant ~150 on tall columns, attributed (no ablation yet) to mass that the implicit matrix diffuses without booking its work. \#285 booked that work inside the operator, put the face form inside the operator on Cartesian grids, and sealed solid cells; the 11 H column is now reported stable to Courant ~2000–2700 (which change did it is not measured). Coarse columns at very large steps remain open as \#286 (section 5).

**Cell vs face.** The two forms differ by one residual, $S = g\times$(mean face mass flux − cell momentum), which is pure truncation error: numerical mass diffusion and a reconstruction inconsistency (section 4). The face form puts $S$ into the local internal energy; the cell form returns it globally as heat uniform per unit mass. Against the buoyancy drive, $S$ grows as the Mach number falls (as $1/\mathrm{Ma}$ to $1/\mathrm{Ma}^2$), so at low Mach the face form adds a numerical heat source that is correlated with the flow, while the cell form's correction barely touches the dynamics. The production decks are low-Mach, below the Mach numbers of any snapy test run so far.

**What is known.** In snapy, T1 (onset near $\mathrm{Ra}_c$) and T4 (forced convection at Re 30) do not reach low Mach and show no decisive difference (face ~10 % closer in T1; no difference at the finest T4 resolution). The mechanism (section 4) favours the cell form at low Mach. **Current reading: cell + fixer stays the default**; face is for runs that need exact local E+PE bookkeeping on explicit Cartesian grids.

**What is open.** The deciding snapy test, T1L (onset against the exact EVP down to $\varepsilon = 10^{-6}$), the long-time rest test T5, and the verification of T4's two coarse face wins have no results yet; this report marks their places. Also open: \#286; and why the fixer adds 54 % more energy on the ISSI G18 deck at 117e449.

## 2. The continuous equations and where the gravity work lives

Everything in this report is about one term, so it is worth seeing first where that term sits in the exact equations and why, in the continuum, there is no choice to make. Take a compressible inviscid gas in a fixed gravitational potential $\Phi(\mathbf{x})$, with gravitational acceleration $\mathbf{g} = -\nabla\Phi$. In snapy gravity is constant and points along the first coordinate $x_1$ (vertical, written $z$ below); the code stores the signed component $g_1$ = `grav1` (negative when gravity points down), so $\Phi = -g_1 z$. Throughout, $g = -g_1 > 0$ is the magnitude and $w = v_1$ the vertical velocity.

### 2.1 The three conservation laws

$$
\begin{aligned}
&\text{mass} && \partial_t\rho + \nabla\cdot(\rho\mathbf{v}) = 0 && (2.1)\\
&\text{momentum} && \partial_t(\rho\mathbf{v}) + \nabla\cdot(\rho\mathbf{v}\mathbf{v} + p\mathbf{I}) = \rho\mathbf{g} && (2.2)\\
&\text{energy} && \partial_t E + \nabla\cdot[(E + p)\mathbf{v}] = \rho\mathbf{v}\cdot\mathbf{g} && (2.3)\\
& && E = \rho e + \tfrac12\rho|\mathbf{v}|^2 \quad \text{(internal + kinetic; the potential is NOT in } E)
\end{aligned}
$$

snapy, like most finite-volume codes, carries $E$ without the potential, so gravity enters the energy equation as a source, $\rho\mathbf{v}\cdot\mathbf{g} = -g\rho w$. That source is the *gravity work*. It is the only place in (2.1)–(2.3) where the energy equation knows about gravity.

### 2.2 Splitting E into kinetic and internal energy

Dot (2.2) with $\mathbf{v}$ and use (2.1) to remove the time derivative of $\rho$. With $K = \tfrac12\rho|\mathbf{v}|^2$:

$$
\begin{aligned}
&\mathbf{v}\cdot\partial_t(\rho\mathbf{v}) = \partial_t K + \tfrac12|\mathbf{v}|^2\,\partial_t\rho\\
&\mathbf{v}\cdot\nabla\cdot(\rho\mathbf{v}\mathbf{v}) = \nabla\cdot(K\mathbf{v}) + \tfrac12|\mathbf{v}|^2\,\nabla\cdot(\rho\mathbf{v})\\
&\Rightarrow\ \text{kinetic:}\quad \partial_t K + \nabla\cdot(K\mathbf{v}) = -\mathbf{v}\cdot\nabla p + \rho\mathbf{v}\cdot\mathbf{g} && (2.4)\\
&(2.3) - (2.4):\quad \text{internal:}\quad \partial_t(\rho e) + \nabla\cdot(\rho e\mathbf{v}) = -p\,\nabla\cdot\mathbf{v} && (2.5)
\end{aligned}
$$

Two facts follow and they drive everything below. First, the gravity work in (2.3) is *identical* to the gravity work in the kinetic-energy equation (2.4): it is the rate at which the gravitational force $\rho\mathbf{g}$ in (2.2) does work on the moving fluid. Second, the internal energy equation (2.5) contains *no gravity term at all*. Gravity changes the temperature of a parcel only indirectly, through the compression work $-p\nabla\cdot\mathbf{v}$ of the motion it drives. A numerical scheme that puts any gravity-dependent source into the internal energy has added something that is not in the physics.

### 2.3 The potential energy and total-energy conservation

Because $\Phi$ does not depend on time, multiplying (2.1) by $\Phi$ gives the potential-energy equation directly:

$$
\begin{aligned}
&\partial_t(\rho\Phi) + \nabla\cdot(\rho\Phi\mathbf{v}) = \rho\mathbf{v}\cdot\nabla\Phi = -\rho\mathbf{v}\cdot\mathbf{g} && (2.6)\\
&(2.3) + (2.6):\quad \partial_t(E + \rho\Phi) + \nabla\cdot[(E + p + \rho\Phi)\mathbf{v}] = 0 && (2.7)
\end{aligned}
$$

The gravity work leaves $E$ exactly where it enters the potential energy, at the same point and at the same time, so E+PE is a conserved density with a flux. In a closed box with impenetrable walls the volume integral of $E+\rho\Phi$ is constant.

### 2.4 One identity, two ways to write the same work

The gravity work can be rewritten with the product rule and the continuity equation:

$$
\begin{aligned}
&\nabla\cdot(\rho\mathbf{v}\Phi) = \Phi\,\nabla\cdot(\rho\mathbf{v}) + \rho\mathbf{v}\cdot\nabla\Phi\\
&\Rightarrow\ \rho\mathbf{v}\cdot\mathbf{g} = -\rho\mathbf{v}\cdot\nabla\Phi = -\nabla\cdot(\rho\mathbf{v}\Phi) + \Phi\,\nabla\cdot(\rho\mathbf{v})\\
&\phantom{\Rightarrow\ \rho\mathbf{v}\cdot\mathbf{g}} = -\nabla\cdot(\rho\mathbf{v}\Phi) - \Phi\,\partial_t\rho && (2.8)
\end{aligned}
$$

(With $\nabla\cdot(\rho\mathbf{v}) = -\partial_t\rho$ the sign of the last term is minus, as written here, not $+\Phi\partial_t\rho$.) In the continuum the two right-hand sides are the same number. They suggest two different discretisations, and that is the whole subject of this report:

- **cell form** — evaluate $\rho\mathbf{v}\cdot\mathbf{g}$ from the cell-centred momentum, the same quantity that the momentum equation's source $\rho\mathbf{g}$ multiplies. The kinetic-energy change from gravity and the energy-equation work then agree cell by cell, as in (2.4)–(2.5).
- **face form** — evaluate the right-hand side of (2.8) from the *mass fluxes at the cell faces*, the same fluxes the discrete continuity equation uses. The discrete E+PE then telescopes exactly, as in (2.7).

On a grid the cell-centred momentum $\rho w_i$ and the average of the face mass fluxes $F_{i\pm1/2}$ are not the same number. The difference is the object of sections 3 and 4: whichever form is chosen, that difference has to be booked somewhere, and the two forms book it in different places.

## 3. The discrete system in snapy

This section writes down what snapy actually computes, at upstream main `117e449` (the \#285 merge). Every step cites the source as `file:line` at that commit (paths under the snapy repository). Grid notation for one vertical column: cell $i$ has volume $V_i$, centre $\mathrm{x1v}_i$, lower face $i-\tfrac12$ and upper face $i+\tfrac12$ with areas $A_{i\pm1/2}$; $F_{i\pm1/2}$ is the total $x_1$ mass flux through a face (dry gas plus all species), $m_i = \rho_i w_i$ the cell's vertical momentum. On a uniform Cartesian column $A/V = 1/dz$. Superscript $s$ labels a Runge–Kutta stage.

### 3.1 One finite-volume stage

Every conserved row $q$ ($\rho$, species, the three momenta, $E$) is updated from the same face fluxes. The divergence is formed in `src/coord/coordinate.cpp:486-490` ($x_1$ part) and returned divided by the volume at `:504`:

$$
\begin{aligned}
&\mathrm{div}_i(q) = \big[A_{i+1/2}F^q_{i+1/2} - A_{i-1/2}F^q_{i-1/2}\big]/V_i + (x_2,\ x_3\ \text{terms}) && (3.1)\\
&du_i = -dt\,\mathrm{div}_i(q) && \texttt{hydro\_forward.cpp:427-429}\\
&du_i \mathrel{+}= \mathrm{forcing}(dt) && \texttt{hydro\_forward.cpp:436}\ \text{(const gravity among them)}
\end{aligned}
$$

The face fluxes come from a Riemann solver applied to reconstructed left and right states. With LMARS (`src/riemann/lmars_impl.h`) the mass flux is the upwinded density times an interface velocity that contains a pressure-jump term:

$$
\begin{aligned}
&\bar\rho = (\rho_L+\rho_R)/2,\qquad \bar c^2 = \bar\gamma(p_L+p_R)/(2\bar\rho) && \texttt{lmars\_impl.h:34-36}\\
&u^* = (u_L+u_R)/2 + (p_L-p_R)/(2\bar\rho\bar c) && \texttt{lmars\_impl.h:42-43}\\
&F = u^*\rho_L\ (u^*>0),\qquad F = u^*\rho_R\ (u^*<0) && \texttt{lmars\_impl.h:53-56, :68-71}
\end{aligned}
$$

Writing $\rho_{up} = \bar\rho - \tfrac12\,\mathrm{sgn}(u^*)(\rho_R-\rho_L)$ and expanding the product gives, exactly,

$$
F = \underbrace{\bar\rho\,(u_L+u_R)/2}_{F^c}\ \underbrace{-\ (p_R-p_L)/(2\bar c)\ -\ \tfrac12|u^*|(\rho_R-\rho_L)}_{F^d} \tag{3.2}
$$

$F^c$ is the "central" estimate of the momentum at the face; $F^d$ is the solver's *numerical mass diffusion*, driven by the jumps in pressure and density between the two reconstructed states. The Roe solver has the same structure: a central part $\tfrac12(\rho_L u_L+\rho_R u_R)$ (`roe_impl.h:103`) minus $\tfrac12\sum_k|\lambda_k|\alpha_k r_k^{\rho}$ (`roe_impl.h:149-150`), i.e. $F^d = -\tfrac12|A|_\rho(q_R-q_L)$. Reconstruction is WENO5 (`src/recon/interp_impl.h:104-120`) or PLM (`src/recon/plm.cpp:20-29`) on primitive variables. With gravity on, $x_1$ reconstruction is well balanced: the code reconstructs $p-p_{ref}$ and $\rho-\rho_{ref}$ and adds the discrete-hydrostatic reference back at the face (`hydro_forward.cpp:79-80, :88-89`, added back at the faces at `:117-123`; reference built at `src/hydro/hydro_ref_x1_impl.h:42-49`). Both sides of a face therefore carry the same reference value, and the jumps in (3.2) are jumps of the *deviation* from hydrostatic balance only. At an exact discrete rest state they vanish, except next to a wall where the stencil is mirrored (section 4.5).

### 3.2 The Runge–Kutta combination

The integrator is pyharp's (`src/mesh/meshblock.cpp:751`), which forms $u \leftarrow w_0u^n + w_1u + w_2\,du$ per stage (pyharp `integrator.cpp:119-120`); for SSP-RK3 the stage weights are $(0,1,1)$, $(\tfrac34,\tfrac14,\tfrac14)$, $(\tfrac13,\tfrac23,\tfrac23)$ (`integrator.cpp:49-61`; read from a local pyharp clone at tag v2.7.1, that 117e449 builds against exactly these lines is inferred). The tendency $du^s$ of stage $s$ therefore enters $u^{n+1}$ with net weight

$$
c_s = w_{2,s}\prod_{t>s} w_{1,t}\quad\Rightarrow\quad (c_0, c_1, c_2) = \big(1\cdot\tfrac14\cdot\tfrac23,\ \tfrac14\cdot\tfrac23,\ \tfrac23\big) = \big(\tfrac16,\ \tfrac16,\ \tfrac23\big) \tag{3.3}
$$

(the same product is coded for the fixer at `hydro_forward.cpp:649-659`). Because every row, $\rho$ included, is combined with these weights, and $\Phi$ does not change in time, any quantity of the form $E + \Phi\rho$ changes over the step by $\sum_s c_s$ times its stage change. That is why a per-stage budget, weighted by $c_s$, closes the step exactly.

### 3.3 Discrete continuity, momentum and potential energy

For one stage, ignoring horizontal fluxes for the moment:

$$
\begin{aligned}
&\Delta\rho_i = -(dt/V_i)\big[A_{i+1/2}F_{i+1/2} - A_{i-1/2}F_{i-1/2}\big] && (3.4)\\
&\Delta m_i = -dt\,\mathrm{div}_i(\text{momentum flux}) + dt\,\rho_i g_1 && \texttt{const\_gravity.cpp:49}\quad (3.5)
\end{aligned}
$$

The potential is $\Phi = -g_1x_1$, evaluated at centres and faces (`hydro_forward.cpp:470-471`), zero at $x_1 = 0$; on a Cartesian grid x1v is the face midpoint (`src/coord/cartesian.cpp:26-27`), so $\Phi_{i\pm1/2} - \Phi_i = \pm g\,dz/2$ on a uniform column. The discrete potential energy is $\mathrm{PE} = \sum_i V_i\rho_i\Phi_i$, and a stage changes it only through (3.4):

$$
\begin{aligned}
\Delta\mathrm{PE} &= \sum_i V_i\Phi_i\,\Delta\rho_i = -dt\sum_i \Phi_i\big[A_{i+1/2}F_{i+1/2} - A_{i-1/2}F_{i-1/2}\big] && (3.6)\\
&= -dt\sum_{\text{faces}} A_fF_f(\Phi_{\text{below}} - \Phi_{\text{above}}) + \text{boundary terms} = +dt\sum_{\text{faces}} A_fF_f\,g\,dz_f + \dots
\end{aligned}
$$

(summation by parts; $dz_f$ = centre-to-centre distance across face $f$). Read physically: the PE rises by $g\,dz$ for every kilogram that crosses a face upward. Horizontal fluxes do not move mass across geopotential surfaces and drop out (the code's comment at `hydro_forward.cpp:525-527`).

### 3.4 Two energy sources

**Cell form.** The const-gravity forcing adds to the energy row the work of the cell momentum, with the same $\rho_iw_i$ as the momentum source (`src/forcing/const_gravity.cpp:50-51`; both also carry the factor `non_hydrostatic`, default 1 at `:25`, taken as 1 throughout this report):

$$
W^{\text{cell}}_i = dt\,\rho_iw_i\,g_1 = -dt\,g\,m_i \tag{3.7}
$$

This is the discrete analogue of (2.4)–(2.5): the kinetic energy the gravity source gives the cell ($\Delta\mathrm{KE}_i \approx w_i\Delta m_i = dt\,g_1\rho_iw_i$) equals the $E$ change, so internal energy receives no gravity term. The code keeps this term in all three modes (`hydro_forward.cpp:514-521` re-forms it as `original_gravity_work` so that the face modes can replace it).

**Face form.** The work done by the mass fluxes of (3.4), each charged with the potential difference between the face and the cell centre (`hydro_forward.cpp:485-487`):

$$
\begin{aligned}
W^{\text{face}}_i &= dt\big[\Phi_i\,\mathrm{div}_i(F) - \mathrm{div}_i(F\Phi_f)\big]\\
&= -(dt/V_i)\big[A_{i+1/2}F_{i+1/2}(\Phi_{i+1/2}-\Phi_i) - A_{i-1/2}F_{i-1/2}(\Phi_{i-1/2}-\Phi_i)\big] && (3.8)\\
\text{uniform Cartesian:}\quad W^{\text{face}}_i &= -dt\,g\,(F_{i+1/2} + F_{i-1/2})/2 && (3.9)
\end{aligned}
$$

(3.9) follows from (3.8) with $\Phi_{i\pm1/2} - \Phi_i = \pm g\,dz/2$ and $A/V = 1/dz$. Compare (3.7): the face form replaces the cell momentum $m_i$ by the mean of the two face mass fluxes. Both are "$-g$ times a vertical mass flux"; they differ only in *which* mass flux.

### 3.5 Why the face form telescopes and the cell form does not

Add $\Phi_i\Delta\rho_i$ from (3.4) to (3.8):

$$
\begin{aligned}
\Delta E_i^{\text{grav}} + \Phi_i\Delta\rho_i &= W^{\text{face}}_i - dt\,\Phi_i\,\mathrm{div}_i(F) = -dt\,\mathrm{div}_i(F\Phi_f)\\
&= -(dt/V_i)\big[A_{i+1/2}F_{i+1/2}\Phi_{i+1/2} - A_{i-1/2}F_{i-1/2}\Phi_{i-1/2}\big] && (3.10)
\end{aligned}
$$

The right side is the divergence of a single face flux $F\Phi_f$, so the cell-by-cell change of $E + \rho\Phi$ is a flux difference, and $\sum V(\Delta E + \Phi\Delta\rho)$ collapses to the two boundary faces. With sealed walls ($F = 0$ there) E + PE is conserved to round-off; the remaining terms of the energy equation (enthalpy flux, pressure work) are already in flux form. This is the property \#202 built the face form for, and is exactly (2.7) in discrete form. In the cell form the same sum is

$$
\sum_i V_i\big(W^{\text{cell}}_i + \Phi_i\Delta\rho_i\big) = \sum_i V_i\big(W^{\text{cell}}_i - W^{\text{face}}_i\big) + \text{boundary terms} \neq 0 \tag{3.11}
$$

because $W^{\text{cell}}$ is built from $m_i$, which is not the flux continuity used (Figure 1).

[FIGURE 1: not copied. File figs/fig1.svg, generated by figs/fig1_column.py (+ figs/fig1_numbers.json) in the gravity-work report build.]

**Figure 1.** One vertical column of cells, with the gravity work of each form drawn where it is booked. Look at the shaded cell $i$. The face form (left, orange) takes its work from the two face mass fluxes: each face flux $F$ gives $\tfrac12 g_1F$ to the cell above it and $\tfrac12 g_1F$ to the cell below, so the column sum telescopes (3.10). The cell form (right, blue) takes it from the cell momentum $m_i$ at the centre, the same $g_1m_i$ the momentum equation uses. Their difference in cell $i$ is the defect $S_i$ (purple), nonzero whenever the face mass fluxes differ from the cell momentum.

### 3.6 The defect D and the exact global fixer

Define the per-cell, per-unit-time residual between the two forms,

$$
S_i = \big(W^{\text{face}}_i - W^{\text{cell}}_i\big)/dt = g_1\big[(F_{i+1/2} + F_{i-1/2})/2 - m_i\big]\qquad\text{(uniform Cartesian)} \tag{3.12}
$$

This is exactly what the face modes add on top of the cell work (`hydro_forward.cpp:555`: `gravity_energy_correction = face_gravity_work - original_gravity_work`). In cell mode the fixer measures, per stage, the change of E + PE caused by gravity and by vertical mass transport (`hydro_forward.cpp:528-542`):

$$
D^s = \sum_i V_i\Big[W^{\text{cell}}_i + W^{\text{face}}_i(F - F^R) + \Phi_i(\Delta\rho_i)_{x1}\Big] + \Delta_{\text{VIC}}(E + \Phi\rho) \tag{3.13}
$$

Here $(\Delta\rho)_{x1}$ is (3.4) with the two $x_1$ wall faces dropped (`:528-535`); $F^R$ is the Riemann flux saved before sedimentation and the positivity limiter add their mass (`:165-168`), and $W^{\text{face}}(F-F^R)$ is the face work of that extra mass, which cell mode books in face form (`:460-464, :523`); $\Delta_{\text{VIC}}$ is the implicit block's change of $E + \Phi\rho$ (`:612-623, :633`). Applying (3.10) to the total flux $F$ and to $F - F^R$, the explicit part of (3.13) reduces to

$$
D^s_{\text{explicit}} = \sum_i V_i\big[W^{\text{cell}}_i - W^{\text{face}}_i(F^R)\big] = -dt\sum_i V_i\,S^R_i\qquad\text{(sealed walls)} \tag{3.14}
$$

with $S^R$ the residual (3.12) of the Riemann flux. The step's defect is the stage-weighted sum $D = \sum_s c_sD^s$ with $c_s$ from (3.3) (`:649-659`). After the last stage the sums are reduced globally (`src/mesh/meshblock.cpp:828-835`; several blocks per process at `src/mesh/mesh.cpp:341-362`), and $-D$ is deposited as heat uniform per unit mass (`meshblock.cpp:898-899`):

$$
\Delta E_i = -D\,\tilde m_i\Big/\sum_j\tilde m_jV_j,\qquad \tilde m = \rho + \textstyle\sum\text{species}\quad\text{(zero in solid cells, :847)} \tag{3.15}
$$

so $\sum V\Delta E = -D$ and the step's E + PE closes to round-off, with mass and momentum untouched. The fixer is a *global* statement: it restores the column's (or the whole domain's) E + PE, not any cell's. Its guards: it runs only in cell mode with grav1 ≠ 0 (`src/hydro/hydro.cpp:177-181`); grav2/grav3 ≠ 0 and periodic $x_1$ are refused at construction (`hydro.cpp:62-65, :69-78`); a step with a redo flag or a non-finite sum deposits nothing and is left to the redo check (`meshblock.cpp:875-882`); mass crossing an $x_1$ wall above $10^3$ machine epsilon of the wall-cell mass is refused (`meshblock.cpp:889-891`), because (3.14) assumes sealed walls. The run-to-date sum of $-D$ is printed as `fixgrav=` (`meshblock.cpp:1092-1093`).

### 3.7 The implicit operator (VIC, schemes 1 and 9)

With an implicit scheme the vertical acoustic terms are solved by a block-tridiagonal Newton step, $(I/(w_2\,dt) + J)\,\Delta q = \mathrm{RHS}$ (`hydro_forward.cpp:593-597`). Scheme 9 selects the "VIC-full" assembly, scheme 1 "VIC-partial" (`src/implicit/implicit_hydro.cpp:239`); both carry the same gravity terms. The gravity block (`vic_assemble_partial_impl.h:43-47`) is

$$
\Phi_{\text{block}} = \begin{pmatrix} 0 & 0 & 0\\ g & 0 & 0\\ 0 & g & 0\end{pmatrix}\qquad\text{rows } (\rho, m, E)\times\text{columns } (\rho, m, E)
$$

i.e. the momentum row gets $g\rho$ and the energy row $g\,m_i$: the operator linearises the *cell* work (3.7) (sign conventions as in the code, grav = $g_1$). At 117e449 two terms were added to the energy row (section 5.4):

- **face mode, Cartesian** (`vic_assemble_partial_impl.h:121-132`; full `vic_assemble_full_impl.h:104-113`): the cell work is removed (`a[i](2,1) += grav`) and replaced by $\tfrac{g}{2}(F_{i-1/2}+F_{i+1/2})$ with the linearised mass-row flux $F_{i+1/2} = (m_i+m_{i+1})/2 - |A|_\rho(q_{i+1}-q_i)/2$, i.e. (3.9) inside the operator. It is active only when gravity-work is `face`, an implicit scheme is on and the grid is Cartesian (`hydro.cpp:183-188`).
- **cell mode, any grid** (`vic_assemble_partial_impl.h:134-140`; full `vic_assemble_full_impl.h:114-120`): the face-form work of the Roe mass-diffusion part alone, with per-side weights $0.5\,A_f\,d/V_i$, $d = |\mathrm{x1f} - \mathrm{x1v}|$ (`implicit_hydro.cpp:201-204`). On a uniform Cartesian column $A\,d/V = \tfrac12$, so both weights are $\tfrac14$, and the added row, $g\cdot\tfrac14(|A|_{\rho,i+1/2} - |A|_{\rho,i-1/2})$ on the diagonal block, is term for term the $|A|_\rho$ part of the face-mode row above: the $F^d$ part of (3.9). The central part stays as cell work.

Mass moved by the post-solve conservative redistribution and its clamps is booked at `implicit_hydro.cpp:272-304` (projection and clamp energy; the physical reading of these two terms is inferred from the code). Face modes outside the operator (curved grids, face-wallc) keep the older post-solve swap of matrix work for face work (`implicit_hydro.cpp:318-339`) and get a construction warning (`hydro.cpp:84-92`) because that combination is the one that failed in \#283.

## 4. The defect S: where it comes from, how big it is, what it does

Section 3 reduced the whole difference between the two forms to one number per cell, the residual (3.12), $S_i = g_1[(F_{i+1/2}+F_{i-1/2})/2 - m_i]$. The face form adds $S$ to the energy of cell $i$; the cell form does not, and its fixer instead adds $-D = dt\sum VS$ (3.14) spread over the whole domain. This section takes $S$ apart.

### 4.1 Three parts of S

Let $m(z)$ be the smooth momentum field whose cell averages are the $m_i$, and write each face mass flux as the true point momentum at the face plus two errors:

$$
F_f = m(z_f) + e_f + F^d_f \tag{4.1}
$$

where $e_f$ is the error of the central part $F^c$ of (3.2) (reconstruction and averaging) and $F^d_f$ the Riemann solver's mass diffusion. Inserting (4.1) into (3.12):

$$
\begin{aligned}
S &= S_{\text{div}} + S_{\text{rec}} + S_{\text{dif}}\\
S_{\text{div}} &= g_1\big[(m(z_{i+1/2}) + m(z_{i-1/2}))/2 - m_i\big] && (4.2)\\
S_{\text{rec}} &= g_1(e_{i+1/2} + e_{i-1/2})/2\\
S_{\text{dif}} &= g_1(F^d_{i+1/2} + F^d_{i-1/2})/2
\end{aligned}
$$

In the continuum all three vanish: the face form and the cell form are the same equation (2.8). $S$ is therefore a pure truncation error. The two forms differ in where that error is put.

**Scope of the split (a review, 10-08; unverified).** The leading-order attributions in 4.2–4.3 assume a third-order or higher $x_1$ reconstruction (cp3, cp5, WENO5). With PLM the face-mean error $-(dz^2/12)q''$ cancels $S_{\text{div}}$, leaving $S \approx g_1(dz^2/4)\,\partial_z\rho\,\partial_zw$ at leading order (the reviewer's algebra; not checked against a run). A further second-order term may come from the well-balanced reference, which is on whenever grav1 ≠ 0: its face density is a second-order mean of the neighbours' smoothed $\rho/p$, not the cell average the reconstruction assumes. On an isothermal background it vanishes; on a polytrope it would add an $O(dz^2)$ term proportional to $\rho w$ (not to $\partial_zw$), coherent with a mode and so entering $\kappa$ in (4.10). *Placeholder: a 1-D column at 117e449 with prescribed smooth $(\rho, w)$ on a polytrope and an isothermal background, WENO5 and PLM, nz 32/64/128, fitting face − cell work against $g_1(dz^2/12)(m'' + \partial_z\rho\,\partial_zw)$; no run exists.*

### 4.2 S_div: two definitions of the potential energy

Taylor-expand about the cell centre $z_c$. The mean of the two face point values is $m_c + (dz^2/8)m''$, the cell average is $m_c + (dz^2/24)m''$, so

$$
S_{\text{div}} = g_1(dz^2/12)\,m'' + O(dz^4) = -g\,(dz^2/12)\,\partial_z^2(\rho w) \tag{4.3}
$$

This term has an exact meaning. With $\Phi = gz$ linear, the true potential energy per unit volume of cell $i$, $(1/dz)\int\rho gz\,dz$ over the cell, is $\rho_i\Phi_i + g(dz^2/12)\partial_z\rho + O(dz^4)$, whereas the discrete PE of section 3.3 is $\rho_i\Phi_i$. Using continuity, $\partial_t\partial_z\rho = -\partial_z^2(\rho w)$, so

$$
\partial_t\big[\mathrm{PE}_{\text{true},i} - \rho_i\Phi_i\big] = \partial_t\big[g(dz^2/12)\,\partial_z\rho\big] = -g(dz^2/12)\,\partial_z^2(\rho w) = S_{\text{div}} \tag{4.4}
$$

The face form conserves $E + \sum\rho_i\Phi_iV$ exactly; the cell form, as far as $S_{\text{div}}$ is concerned, conserves $E + \mathrm{PE}_{\text{true}}$. Neither is wrong: $S_{\text{div}}$ only relabels which second-order piece of energy is called potential. It is the discrete divergence of $g_1(dz^2/12)\partial_zm = -g(dz^2/12)\partial_zm$, so its domain sum reduces to boundary terms. snapy's face modes remove it explicitly when the $x_1$ reconstruction is cp3, cp5 or WENO5, by subtracting $g_1\delta^2m_i/12$ as the divergence of $H = (dz/12)(m_i - m_{i-1})$, zeroed at physical boundaries (`hydro_forward.cpp:493-513`). In cell mode this is not done (`!gw_cell` in the condition), and it need not be: in the fixer's sum $D$ it contributes boundary terms only. (At the pre-\#284 base 531579c the subtraction ran in every mode, `531579c:469`.)

### 4.3 S_rec: a mass flux that the momentum does not contain

The code comment at `hydro_forward.cpp:489-492` states that the face average exceeds $m$ by $dz^2/12\,(m'' + \rho'v')$, and removes only the $m''$ part. The $\rho'v'$ part (primes here are $z$-derivatives) comes from reconstructing the primitives $\rho$ and $w$ separately. The cell velocity $w_i = m_i/\rho_i$ is a ratio of averages; expanding both averages gives $w_i = w_c + (dz^2/24)[w'' + 2\rho_zw_z/\rho]$, while the reconstruction treats $w_i$ as the average of $w$, i.e. as $w_c + (dz^2/24)w''$. The reconstructed face velocity is therefore too large by $(dz^2/12)\rho_zw_z/\rho$, and the face flux by $e_f = (dz^2/12)\rho_zw_z$:

$$
S_{\text{rec}} = g_1(dz^2/12)\,\partial_z\rho\,\partial_zw + O(dz^4);\qquad\text{with } \partial_z\rho = -\rho/H_\rho:\quad \frac{S_{\text{rec}}}{g\rho w} = \frac{dz^2}{12H_\rho}\,\frac{\partial_zw}{w} \tag{4.5}
$$

This is not a divergence. It is a genuine second-order inconsistency between the mass flux of the continuity equation and the momentum on which gravity acts, of relative size $dz^2/(12HL)$ for a flow of vertical scale $L$. The snapy instrument run at 531579c (which already removed $S_{\text{div}}$, section 4.2) measured an interior $S/(g\rho w)$ of $1.67\times10^{-4}$ (nz64, $\varepsilon$ $10^{-2}$), against this estimate of ~$10^{-4}$, and a fall by ×4.9 from nz64 to nz128 at $\varepsilon$ $10^{-3}$ ($1.96\times10^{-4} \to 4.02\times10^{-5}$), i.e. second order. Because $\partial_zw/w$ changes sign across a convective cell, $\sum S_{\text{rec}}w$ is small: the same run found $\mathrm{corr}(S,w) = -0.24$ in the interior and an interior sumS/sumB of 0.0045.

### 4.4 S_dif: numerical mass diffusion

From (3.2), $F^d = -(p_R-p_L)/(2\bar c) - \tfrac12|u^*|(\rho_R-\rho_L)$: the solver moves mass down the jump in pressure (an acoustic term) and down the jump in density (an upwind term) (Figure 2). With the well-balanced reconstruction both jumps are jumps of the deviation from the hydrostatic reference. In smooth flow a jump is $dz^r$ times an $r$-th derivative ($r = 5$ for WENO5 in smooth regions, 2 for PLM), but $r$ falls toward 1 at extrema, under-resolved structures and walls. For a first-order jump and dynamic pressure $p' \sim \rho w^2$ on scale $\ell$,

$$
F^d \sim dz\,\partial_zp'/(2c) \sim dz\,\rho w^2/(2\ell c)\quad\Rightarrow\quad S_{\text{dif}}/(g\rho w) \sim (dz/\ell)\,\mathrm{Ma},\qquad \mathrm{Ma} = w/c \tag{4.6}
$$

The upwind term is quadratic in the perturbation ($|u^*|$ times a density-deviation jump) and is smaller still in the linear regime.

[FIGURE 2: not copied. File figs/fig2.svg, generated by figs/fig2_face.py (+ figs/fig2_numbers.json) in the gravity-work report build.]

**Figure 2.** The origin of $S_{\text{dif}}$ at one face. Look at the dashed purple arrow $F^d$. The two cells reconstruct different states at the shared face (the dots $\rho_L$, $\rho_R$); the Riemann solver's mass flux is the average flux $F^c$, which the momenta also carry, plus a diffusive part $F^d$ set by the jumps, which no momentum carries (LMARS form, `lmars_impl.h:53-56`). Mass that $F^d$ lifts gains potential energy. The face form charges it to the internal energy of the two neighbouring cells; the cell form leaves it to the global fixer.

### 4.5 Wall cells

At a reflecting $x_1$ wall the reconstruction stencil is completed with mirrored ghosts, the reconstruction drops to low order, and both $e_f$ and $F^d_f$ are first order next to the wall. Two measurements show it. At an exact discrete rest state (regression case 36, implicit scheme 9, reflecting $x_1$, 531579c), the velocity is zero to the last bit and yet $\max|S| = 2.0\times10^{-9}$, nonzero only in the bottom three cells: the energy equation books $g\cdot F_{\text{face}} \neq 0$ from a face mass flux next to the wall while the momentum books zero. In the T4 decks at 117e449, $S$ in the wall cells is 5.4 % of the cell work at every $\varepsilon$, nz and scheme. Per wall cell $S$ is $O(1)$ relative to the cell work (instrument-run dz pair, nz64 → nz128: per wall cell $S/(g\rho'w)$ 80 → 281), so the wall cells' share of the domain integral shrinks only with their thickness, $O(dz)$, not as $dz^2$. The same pair's domain sumS/sumB fell 0.125 → 0.019 (×6.5), but each resolution was a single restart of a different flow state, so the pair measures no convergence order for the domain total. This is why the variant face-wallc exists: it keeps the cell work in the two wall cells (`hydro_forward.cpp:557-561`).

### 4.6 What S means physically: who pays for the potential energy

Gravity acts on momentum. The cell form gives each cell the kinetic energy that gravity's pull on $m_i$ produces, and nothing else, exactly as (2.4)–(2.5). Continuity, however, moves the mass $F$, not $m$. The difference $F - m$ is mass that crosses geopotential surfaces without having been lifted or lowered by the momentum equation: numerical mass diffusion, and the reconstruction's inconsistency between the mass flux and the momentum. Every kilogram of it that moves up gains $g\,dz$ of potential energy, and that energy must come from somewhere:

- **Face form** (Figure 3, right): from the cell itself. Since the kinetic energy is fixed by the momentum, the extra work $S$ lands in the cell's *internal* energy. E + PE closes cell by cell, at the price of a local heat source $S$ that is correlated with the flow.
- **Cell form** (Figure 3, left): nobody pays locally; the domain's E + PE drifts by $dt\sum VS$ per step. The fixer pays the bill globally, as heat uniform per unit mass (3.15). A uniform-per-mass heat has essentially no projection on any flow structure with zero horizontal mean, so the error leaves the dynamics almost untouched; it appears instead as a slow, domain-wide warming or cooling that `fixgrav` reports.

The true solution ($F = m$) has neither. So the question of section 6 is not which form is exact, but which way of absorbing the same truncation error disturbs the physics less.

[FIGURE 3: not copied. File figs/fig3.svg, generated by figs/fig3_energy.py (+ figs/fig3_numbers.json) in the gravity-work report build.]

**Figure 3.** Energy flow in one cell, cell form + fixer (left) against face form (right). Both move $g_1m_i$ from potential to kinetic energy through the momentum (black), so momentum and kinetic energy are the same in both. Look at the arrows into IE. In the face form the rest of the potential-energy change, $S_i$, heats cell $i$ itself and follows the flow. In the cell form $S_i$ leaves the cell's budget; the fixer (green) returns the domain total as heat uniform per unit mass, $\langle S\rangle$ in every cell. The two forms therefore differ locally by $S_i - \langle S\rangle$ in the internal-energy source and agree in the domain sum.

### 4.7 Size relative to the drive: why the face form's local error grows as the Mach number falls

Low-Mach convection is driven by the buoyancy work $B = g\rho'w$ ($\rho'$ here the density perturbation), and the density perturbation is tiny: from $w^2 \sim g\ell\rho'/\rho$ and $c^2 \sim gH$, $\rho'/\rho \sim \mathrm{Ma}^2(H/\ell)$. Two cases follow:

$$
\begin{aligned}
&\text{(a) } S \text{ a fixed fraction } \kappa \text{ of the cell work } (S_{\text{rec}}\text{, wall cells}): && S/B \sim \kappa\,\rho/\rho' \sim \kappa/\mathrm{Ma}^2 && (4.7)\\
&\text{(b) first-order mass diffusion (4.6)}: && S/B \sim (dz/\ell)\,\mathrm{Ma}/(\mathrm{Ma}^2H/\ell) \sim (dz/H)/\mathrm{Ma} = 1/(\mathrm{Ma}\,N_H) && (4.8)
\end{aligned}
$$

with $N_H = H/dz$ the cells per scale height. (4.8) is the study's working estimate; (4.7) is the case T4 actually measured, a fixed 5.4 % of the cell work in the wall cells. Either way, at fixed resolution $S/B$ grows without bound as the Mach number falls. T4 saw it begin: the wall $S/B$ rose from about 0.5 at $\varepsilon = 10^{-2}$ to about 10 at $\varepsilon = 10^{-4}$, and the interior rms ratio from 0.028 to 0.205 (section 6.4). The factor ×20 over two decades fits (4.7) (Figure 4): T4's $\varepsilon$ is a forcing parameter with $w \propto \varepsilon^{1/3}c$ (6.4), so $\mathrm{Ma}^2 \propto \varepsilon^{2/3}$ and $100^{2/3} \approx 21.5$. The production decks run with $N_H$ 1.3–10 (section 6.2), at Mach numbers below T4's.

[FIGURE 4: not copied. File figs/fig4.svg, generated by figs/fig4_scaling.py (+ figs/fig4_numbers.json) in the gravity-work report build.]

**Figure 4.** T4's measured $S$ against the buoyancy work $B$, read from the T4 $S$ table (rms over the 600 dumped steps). Filled symbols: the two wall cells at each $x_1$ wall; open symbols: the interior. Orange circles: steps run in the face form; blue squares: in the cell form (the two agree, as the statistics do not depend on the form). Labels give the scheme and nz (E explicit, I implicit scheme 9). Look at the filled symbols: from $\varepsilon = 10^{-2}$ to $10^{-4}$ the wall $S/B$ rises from about 0.5 to about 10, on the dashed $\varepsilon^{-2/3}$ line (drawn through the explicit nz32 face point at 0.54) that (4.7) predicts for a fixed fraction $\kappa$ of the cell work. Points at the same $\varepsilon$ are spread sideways for legibility.

### 4.8 Consequence for a growth rate: the oracle of T1L

Take a linear convective mode in a layer whose entropy decreases upward, $\partial_z\bar s = -c_p\varepsilon/H$ ($\varepsilon$ the superadiabaticity). The face form adds to the internal energy a heat source $S$; let its part coherent with the mode be $\kappa g\rho w$. The linearised entropy equation is

$$
\rho T\,\partial_ts' = \rho T\,w\,c_p\varepsilon/H + \kappa g\rho w\quad\Rightarrow\quad \varepsilon_{\text{eff}} = \varepsilon + \kappa\,gH/(c_pT) = \varepsilon + \kappa(\gamma-1)/\gamma \tag{4.9}
$$

using $gH = RT$ ($H$ the isothermal pressure scale height; for a non-isothermal layer the factor is evaluated locally). In the inviscid limit $\sigma \propto N \propto \sqrt\varepsilon$, so

$$
\delta\sigma/\sigma \approx \tfrac12\,\delta\varepsilon/\varepsilon = \big[(\gamma-1)/(2\gamma)\big]\,\kappa/\varepsilon,\qquad \kappa = \sum Sw\Big/\sum g\rho w^2\quad\text{(weighted as a Rayleigh quotient)} \tag{4.10}
$$

For a fixed fraction $\kappa$ this is an error $\propto 1/\varepsilon = 1/\mathrm{Ma}_{\text{eff}}^2$, with $\mathrm{Ma}_{\text{eff}} \sim \sqrt\varepsilon$ the mode's Mach scale $\sigma H/c$. For first-order mass diffusion in the linear phase, $\partial_zp' \sim \rho\sigma w$ and $\sigma \sim (c/H)\sqrt\varepsilon$, so $\kappa \sim (dz/H)\sqrt\varepsilon$ and $\delta\sigma/\sigma \sim 1/(N_H\sqrt\varepsilon) = 1/(N_H\mathrm{Ma}_{\text{eff}})$, the scaling of (4.8). Only the part of $S$ coherent with $w$ enters: a heat source with zero projection on the mode does nothing to first order. That is the decisive difference between the forms. The face form's $S$ sits in the mode's own cells; the cell form's fixer heat is uniform per mass and projects onto the mode only through $\rho'$, so the cell form's onset error is the scheme's ordinary truncation error, with no $1/\varepsilon$ amplification from this term. **Prediction**, which T1L was designed to test: at fixed $N_H$, the face form's growth-rate error against the EVP grows as $\varepsilon$ falls; the cell form's stays flat. snapy has not yet been tested in that regime.

## 5. Phase 1: the causal chain from \#202 to \#286

Phase 1 was about correctness: a crash at large implicit steps, its cause, and the consequences of each fix. The chain is laid out as symptom → root cause → fix → test → review, step by step. \#283 and \#286 are GitHub *issues*; \#284 and \#285 are pull requests. GitHub holds no review objects for \#284 or \#285; the review findings below are summarised from the review record. Figure 5 summarises the chain.

[FIGURE 5: not copied. File figs/fig5.svg, generated by figs/fig5_chain.py (+ figs/fig5_numbers.json) in the gravity-work report build.]

**Figure 5.** The phase-1 chain as a flow chart. Each box gives what changed, the commit it landed in (top right) and the test that pins it (bottom, italic); the labels on the arrows say why the next step was needed. Look at the colours: orange is the face form, blue the cell form, purple the fixer feedback the cell form introduced, green \#285's repair, grey what is left. Sections 5.1–5.6 give the evidence for each box.

### 5.1 The starting point: the face form of \#202

**What it was.** PR \#202 (merged 2026-09-08, merge commit 02c3cdc) made the energy equation use the work of the same vertical mass flux that continuity uses: "Previously, continuity transported mass using face fluxes, while gravitational work was calculated from cell-centered velocity." In explicit steps it replaced the cell work by the face work (3.8); in the implicit (VIC) step it kept the original gravity coupling inside the solve and then applied, after the solve, a "swap" of the matrix's work for the work of the mass the redistribution actually moved. Its stated scope: "The conservation guarantee applies primarily to closed vertical boundaries." At the pre-\#284 base 531579c this face form was the only form: the swap ran in all modes (`531579c implicit_hydro.cpp:257, :270`), and the explicit correction had no cell branch (`531579c hydro_forward.cpp:497`).

**Why it had to change.** The matrix of the implicit step linearises the *cell* work (section 3.7). Both face pieces were added outside the operator, unlinearised. At small implicit steps that does not matter. At large ones it does: \#283.

### 5.2 \#283: a tall column at rest blows up at large implicit steps

**Symptom** (issue \#283, opened 2026-10-06). A 45-cell isothermal column of 29.9 km cells (11.3 scale heights; $g$ 23.1 m s$^{-2}$, $T$ 786 K, $\gamma$ 1.403461, $R_d$ 3515, $p_{\text{bot}}$ 100 bar; rk3, WENO5, LMARS, implicit scheme 9), balanced and at rest. At $dt$ = 997 s (vertical acoustic Courant 65.6) main blows up: $\max|w|$ $2\times10^{-6}$ m/s at step 10, growing ×2.7 per step, ~$10^{24}$ by day 1 ($8.9\times10^{24}$ m/s after the 40 steps of the test). At $dt$ = 100 s (Courant 6.6) it stays at rest ($4.6\times10^{-9}$ m/s). With both face terms switched off it stays at rest for 10 days. Either term alone is enough: swap off and correction on goes non-finite at 0.97 d; swap on and correction off reaches 0.13 m/s at step 12.

**Root cause.** The operator's finite-difference Jacobian of the energy row is identical to the last bit with the face correction on or off (Evidence 1, issue body; an independent check also found $J_{\text{face}} - J_{\text{cell}} = 0$ exactly), so the implicit solve never sees the face work. The swap's size relative to the step's energy increment grows with the step: 0.5 %, 3.7 % and 20 % at Courant 1, 10 and 66 (Evidence 2). A 20 % unlinearised energy term in a stiff acoustic solve is an explicit term at Courant 66, and it is unstable.

**Test.** `tests/test_implicit_gravity_tall_column.py`: the same column, 40 steps at $dt$ 997 s and 100 s, finite and $\max|w| < 10^{-7}$ m/s (`:37, :123-124` at 117e449). Red on the parent 068f9f4 (large step $8.9\times10^{24}$ m/s, control rung $4.6\times10^{-9}$), green at the \#284 head ($5.8\times10^{-9}$ / $5.0\times10^{-9}$).

**Two ways out**, both listed in the issue: put the face work inside the implicit operator, or use the cell work, which the operator already linearises, and give up E + PE to round-off unless something restores it. A comment on \#283 (2026-10-07) proposed the second: cell form by default, the sedimentation/limiter exception, and a global fixer. Staging: \#284 = the cell scheme; the face-in-operator route a separate later PR; the default question only after both were solid. That last question is phase 2.

**Bugs folded into \#283's scope** (each also on main with `gravity-work: face`):

- \(a\) *Top-cell drain*: the VIC dry-gas availability clamp empties the top cell of a tall resting column at large $dt$. A 30 H isothermal column, 120 cells, Courant 657: top density −84 % and $T$ 786 → 4267 K in one step, NaN by step 3; at 35–37 H it fails silently.
- \(b\) *Coarse $x_1$ grid*: a 40 H column on 45 cells (0.89 H per cell), scheme 9, $dt$ 1500 s (Courant ~28): the LU is singular at step 1 and $\max|w|$ reaches $9.2\times10^{30}$ m/s (top $\rho/\rho_0$ 0.145); on 160 cells (Courant 99) $\max|w|$ is $2.15\times10^{-3}$ and the top density holds.
- \(c\) *Implicit + solid cells*: the fluid mass drifts $1.75\times10^{-5}$ over 20 steps, fixer on or off.

\#285 sealed implicit mass transport at solid cells and books the redistribution's energy (5.5), which is the fix for (c). For (b), \#285 first added a startup refusal of max $dz/H_p > 0.5$ and then removed it (5.5); the coarse-column behaviour is carried by \#286. What closed (a) is not on record (*unverified*: the \#285 projection/clamp terms, `implicit_hydro.cpp:272-304`, book the clamp's energy, but whether the drain itself is gone needs the 30 H / Courant 657 case rerun at 117e449). \#283 was closed on 2026-10-08 by the \#285 merge ("Fixes \#283").

### 5.3 \#284: the cell form and the global E + PE fixer

**What.** PR \#284 (merged 2026-10-07, squash 531e839; "Refs \#283", the explicit part). It adds two keys to `forcing/const-gravity`: `gravity-work` = `cell` (default) | `face-wallc` | `face`, and `gravity-work-fixer` (default true with cell; `src/forcing/const_gravity.cpp:28-36`). `cell` keeps the momentum-consistent work (3.7) and turns off both \#202 pieces, except that mass moved by sedimentation or the positivity limiter keeps its face work (`hydro_forward.cpp:460-464`), because that mass has no counterpart in the momentum at all. `face` reproduces the pre-change numbers bitwise. `face-wallc` is face with the two $x_1$ wall cells on cell work (4.5).

**The fixer** is (3.13)–(3.15): per stage the dynamics' change of E + PE (gravity work booked into $E$, $\Phi$ times the $x_1$ mass divergence, the implicit block's change), stage weights 1/6, 1/6, 2/3, one global reduction after the last stage, $-D$ added as heat uniform per unit mass. Mass and momentum are untouched.

**Numbers it changes** (PR body):

| check | main (face) | \#284 (cell + fixer) |
|----|----|----|
| tall rest column, implicit, Courant 65.6, 40 steps | 8.9e24 m/s | 5.8e-9 m/s |
| same, Courant 6.6 | 4.6e-9 m/s | 5.0e-9 m/s |
| moving isentropic column, total-entropy drift, nz 64 / 128 | 1.11 / 0.235 | 1.97 / 0.473 |
| same, relative E+PE drift | 2.3e-14 / 4.7e-14 | 2.3e-14 / 4.7e-14 |
| closed box, 200 steps, fixer off (the defect the fixer removes) | — | 1.9e-6 (on: 1.2e-14) |

The moving column's entropy drift roughly doubles in the cell form and stays first order in $w_0$; face-wallc's E+PE in the closed box is 1.3e-6 (its wall cells keep the cell work).

**Refusals and their reasons.** The defect (3.14) assumes sealed walls, so (i) mass crossing an $x_1$ wall above $10^3$ machine epsilon (of the run's dtype) of the wall-cell mass is refused; a sealed wall measures 0.14 eps in float64 and float32; (ii) periodic $x_1$ is refused, read from the layout wrap as well as the boundary name, because $\Phi$ jumps by $gL$ at the wrap (`hydro.cpp:66-78`); (iii) grav2 or grav3 ≠ 0 is refused, because the fixer books only $x_1$ transport (`hydro.cpp:62-65`); (iv) a face form with an explicit `gravity-work-fixer: true` is refused (`const_gravity.cpp:37-40`); (v) a step with limiter marks or a non-finite sum deposits nothing and goes to the redo check.

**What review found** (each fixed before merge, with a red-then-green test):

- Float32: a $10^{-12}$ wall-mass bound lay below float32 round-off and stopped a reflecting run at step 38. Fix: bound $10^3$ eps(dtype) × wall-cell mass; float32 arm 200 steps at $6.1\times10^{-6} \le 200\,\mathrm{eps}_{32}$.
- Periodic $x_1$ accepted and then heated (~$2.98\times10^6$ J/m² where a sealed wall gives $1.1\times10^3$ → 71; min $p$ 670 Pa, min $T$ 125 K); E+PE drift $3.6\times10^{-2}$. Fix: refusal at construction; a residual path (cubed layout + $x_1$ periodic after a Python bfuncs round trip) was closed by reading `layout()->periodic_z()` (fefa185).
- NaN/redo ordering: the wall-mass check ran before the redo check, so a transient NaN aborted the run (straka at cfl 1.6: SIGABRT at cycle 15). Fix: guard on all five global sums and the limiter marks; new ctest `test_straka_redo`.
- Solid cells: the fixer heated solid cells; $d(E+\mathrm{PE})_{\text{fluid}}/D = 0.0219 = M_{\text{solid}}/M$ every step. Fix: mask (`meshblock.cpp:847`); 20-step fluid drift $1.25\times10^{-15}$ (was $3.8\times10^{-8}$).
- Implicit face-wallc differed at the wall cells (ratio 0.09/0.37 implicit vs $2\times10^{-3}$ explicit); fixed to 0.012/0.024.

Independent checks: seams and cubed-sphere panels E+PE $1.79\times10^{-15}$ and $1.28\times10^{-15}$; cubed sphere 1/2/3/6 ranks bitwise, E+PE $1.1\times10^{-14}$; stretched $x_1$ $1.1\times10^{-13}$ over 2000 steps. Review kept the uniform-per-mass heat: column-local deposits moved "16–53× more energy", and "local defect is 1100× its global sum"; the entropy drift rate of the cell form over 24 turnovers was 0.863× (nz32) and 0.941× (nz64) of face's; the default stayed cell + fixer, and a "default-by-solver" alternative was withdrawn. Migration: Straka moves by up to 0.43 K / 0.55 m/s and Bryan by 0.18 K in $\theta$; 12 of 22 shipped decks change. Formal sign-offs on fefa185: three independent reviews (CUDA; CUDA on 2 GPUs; CPU); a fourth reviewed without signing.

**The documented Limit.** The fixer adds its heat outside the implicit operator. On the 11 H column cell + fixer was stable at Courant 66 and 148 and unstable from 168 to 657 (the moving column from 197), while cell without the fixer was stable throughout; `examples/jupiter_gcm_dry` (~3 H) was stable at its own Courant of 247 with no redo; a ~3 H column was stable at Courant 1000 and needed redos at 3000. \#284 shipped with this as a stated limit ("a deck deeper than about 10 scale heights that runs at an implicit vertical acoustic Courant above about 150 should check its column"), with no Courant cutoff.

### 5.4 The large-Courant fixer feedback

**Symptom.** Cell + fixer blows up where cell without the fixer is stable, reproduced in three independent snapy runs: step 120 at rest, 18 moving, Courant 197; rest step 122, ×1.16 per step, and at Courant 656 rest step 14, ×3.6; Courant 65.6 holds, 197 fails at step 121, 657 at step 14.

**Mechanism.** Heat uniform per unit mass raises the pressure in proportion to $\rho$. In a tall column $\rho$ falls by $e^{11}$ from bottom to top, so the added pressure has a vertical gradient, $\delta p \propto \rho$, which is a net vertical force. The heat is added after the implicit solve, so this force acts explicitly at a step far above the explicit limit. It drives a net vertical momentum $P$, and $D$ is first order in $P$: $D/(g\,dt\,P) = -0.651$, constant while $P$ grew $10^8$×. Larger $P$ → larger $D$ → larger heat gradient → larger $P$: a loop whose gain crosses 1 between Courant 148 (stable) and 168 (unstable) on this column (5.3).

**Where D came from.** Splitting $D$ by term at Courant 197: one run gave explicit cell work −0.276, PE of all mass moves −0.027, implicit block E side −0.349 (in units of $g\,dt\,P$); an independent run gave $D = -0.758\,gP\,dt$ (correlation −1.0000 over 120 steps), 98 % from the implicit block (E −0.407, PE −0.337), the explicit E and PE cancelling (not reproduced). The two splits disagree: in the second the defect lives in the implicit block; in the first the implicit block carries 0.349/0.651 = 54 % of $D$ and the explicit cell work 0.276/0.651 = 42 %, which \#285 does not change. **Proposed mechanism** for the implicit part (not shown to be the cause): the matrix's mass row moves mass with face fluxes that include the Roe diffusion $|A|_\rho\Delta q$, while its momentum and energy rows use the cell form. The diffusive mass changes PE inside the solve, and the energy row does not see it. This is $S_{\text{dif}}$ of section 4.4 at implicit-step size. Booking it inside the operator is \#285's cell-mode term. *Unverified as the cause: no ablation exists (there is no runtime switch for the diffusive term). The check that settles it: the 11 H column with cell + fixer at Courant 197 and 657, 4000 steps, with the Roe-diffusion booking off, the projection/clamp booking off, and both on, logging $D/(g\,dt\,P)$; if the Roe-off arm blows up again, the mechanism is confirmed; if it stays stable, it is refuted.*

### 5.5 \#285: gravity work consistent with mass transport inside the implicit step

**What.** PR \#285 (merged 2026-10-08, merge commit 117e449). Body: "Put Cartesian x1 face work inside the implicit energy row. In cell mode, book Roe mass-diffusion work with the actual face areas, cell volumes and face-to-centre distances, including spherical/cubed-sphere grids. Seal implicit mass transport at solid cells and account for energy changes from redistribution." "Legacy face-wallc behavior is unchanged."

- **Face inside the operator** (`vic_assemble_partial_impl.h:121-132`): the \#283 fix of the face route. Gated to `face` + implicit + Cartesian (`hydro.cpp:183-188`); elsewhere the post-solve swap remains and a warning is printed (`hydro.cpp:84-92`).
- **Cell-mode Roe mass-diffusion work** (`vic_assemble_partial_impl.h:134-140`, weights `implicit_hydro.cpp:201-204`). Derivation: the linearised mass flux through face $f$ is $F_f = (m_i+m_{i+1})/2 - |A|_\rho\Delta q/2$. Its face work on cell $i$, from (3.8), is $-(A_f/V_i)F_f(\Phi_f-\Phi_i) = g(A_fd_f/V_i)F_f\cdot\mathrm{sgn}$, with $d_f = |\mathrm{x1f} - \mathrm{x1v}|$. Keep the central part as cell work and book only the diffusive part: weight $(A_fd_f/V_i)\times\tfrac12|A|_\rho\Delta q = 0.5A_fd_f/V_i\times|A|_\rho\Delta q$, which is the code's weight; on a uniform Cartesian column it is $\tfrac14$ (PR author's comment, 2026-10-07). Using real $A$, $d$, $V$ makes it valid on curved grids; "the old uniform coefficient fails the curved checks (maximum error 0.635852)".
- **Solid sealing** (`src/implicit/implicit_dispatch.cpp:56-65`) and **projection/clamp energy** (`implicit_hydro.cpp:272-304`).

**Tests named by the author:** CTest 94/94; 72 rest/moving ladder cases (CPU/CUDA; cell + fixer, cell fixer-off, face); frozen-Roe energy-row finite-difference checks 6/6 with curved-grid errors below $1.3\times10^{-10}$ (PR body; the test asserts $10^{-5}$ at `tests/test_implicit_face_work_jacobian.cpp:111`); gnomonic/spherical-polar energy budgets below $2\times10^{-16}$ relative; max solid-span mass drift $2.0\times10^{-15}$. In the tree: `tests/test_implicit_face_work_operator.py` (face, no fixer, Courant 65.6/197/657, schemes 9 and 1, at rest and moving; $|$E+PE drift$| < 10^{-11}$, `:34-35, :129-132`).

**What it achieved.** By the PR author's report of reviewers' runs (no run log of them is on record), \#284's Limit is gone at this head: the 11 H rest column is stable through Courant ~2000–2700, and the fixer's sealed-wall check refuses from ~2500 (CUDA) / ~2750 (CPU) on round-off (PR body). That supersedes \#284's "1370 eps against 1000 at Courant 6000". **Not known: which change did it.** On a cell-mode column without solid cells the face-in-operator route and solid sealing are inactive, while the projection/clamp booking runs in cell mode too (`implicit_hydro.cpp:272`: `if (face_work || diffusive_work)`); so the fix came from the Roe-diffusion booking, the projection/clamp booking, or both. **Not measured:** how much of the old $D$ the new cell-mode term removes; no such ablation has been run (there is no runtime switch for the diffusive term). *Placeholder: fraction of $D$ removed by the Roe-diffusion booking at Courant 66/197 — no number exists.*

**The $dz/H_p$ episode.** \#285 first refused max $dz/H_p > 0.5$ under implicit $x_1$. A deck scan found it would refuse two working brown-dwarf decks (29: 0.749, 30: 0.676; every other deck ≤ 0.46), both of which pass the regression battery. The blanket refusal was removed (head 8710d02); 117e449 has no such check.

**Review.** Formal sign-offs on ae4dd4b by two reviewers; a third validated independently. The body states its limits with numbers: a 45-cell 40 H face column at $dt$ 1500 s "first requests retry on attempt 27, after accepting |w| about 365 m/s"; at $dz/H_p$ 0.8 and Courant 657 cell + fixer reaches 4.4946× top density after 300 accepted CPU steps (4.4962× CUDA; fixer off 0.9916×), where base 531e839 stops after 12 accepted steps.

### 5.6 \#286: what is left

Issue \#286 (opened 2026-10-07, open): "Coarse implicit columns amplify gravity-fixer heat and accept inaccurate states." A 40 H column on 50 cells ($dz/H$ 0.8), nominal Courant 657, $dt$ 31923.99 s, with dt-halving redos: top density 4.4946 (CPU) / 4.4962 (CUDA) of initial with the fixer, 0.9916 without; top $T$ 1439.8 K; E+PE drift $-1.754\times10^{-14}$; max applied heat $2.62\times10^{-4}$ J/kg per step. Removing only the applied heat reproduces the fixer-off retry sequence: "This isolates thermal feedback; the precise amplification mechanism is not yet established." Planned: an accuracy criterion that can request a retry or stop, not a hand-picked Courant cutoff. Not fixed now: the regime ($dz/H_p$ 0.7–0.9 *and* Courant 197–657 on a 40 H column) is not reached by any real deck.

### 5.7 Downstream regression twins

- **To 531e839** (10-07): same-job twins 531579c vs 531e839 with `gravity-work: face` were field-exact (CPU and GPU builds; the ISSI G18 twin series identical). The default (cell + fixer) moved the G18 kinetic energy by −1.0 % ($2.544$ vs $2.569\times10^{26}$), redos 8 vs 18, `fixgrav` $9.2\times10^{25}$ J.
- **To 117e449** (10-07 to 10-08): explicit decks bitwise (straka, robert, 32b) for both the default and face; implicit Cartesian (scheme 9) differs only in vel1 at ~$1.1\times10^{-11}$ m/s; a cubed-sphere twin was field-exact for face and differed only in velocity (max $8.4\times10^{-8}$ m/s) for cell, presumably \#285's diffusive work on a curved grid (not ablated). The downstream regression battery passed on every build (38 pass / 0 fail; GPU 6/6, CPU 13/13; arm 16/16). One observation is open: on the ISSI G18 deck the fixer's run-to-date added energy is 54 % larger at 117e449 than at 531e839 ($1.42\times10^{26}$ vs $9.20\times10^{25}$ J, ~$10^{-4}$ of the internal energy over $2.85\times10^6$ s), against a deck noise floor of ~2.5 % in kinetic energy at 14k cycles. *Unverified: why the fixer adds more at 117e449; a check is a cell-mode G18 twin with the \#285 diffusive term ablated.*

## 6. Phase 2: which form is physically right, and where

### 6.1 The question and the rule written before the runs

Phase 1 left two correct forms in snapy (section 5). Phase 2 (from 10-07) asked which is physically better and in which regime, kept separate from correctness. Two conditions were set: every result needs an owner and an independent verifier in a different environment (machine, build or hardware); and the oracles must have known answers. The decision rule was written before any run (study design, drafts 1–2): a form wins a test only where owner and verifier agree and the gap exceeds their combined spread; deterministic tests additionally need a smaller error at every resolution, convergence of both forms, and a gap above the Richardson error at the finest level; stochastic tests need at least three seeds. Regime bins were fixed in advance: vertical acoustic Courant < 1 / 1–10 / > 10, and $dz/H$ < 0.1 / 0.1–0.5. **If neither form wins, cell stays the default**, because it is the only form that is complete on curved grids and in the implicit GCM path.

### 6.2 How the parameter space was chosen — and how it was first chosen wrongly

Draft 1 had five tests (T1 onset vs EVP; T2 internal gravity waves; T3 the local residual $S$; T4 the forcing ladder; T5 long-time drift), with parameters picked from the literature tests rather than from the error mechanism. This was recorded as a mistake: T4 at Re 30 and T1 near $\mathrm{Ra}_c$ are viscously controlled at Mach numbers $10^{-2}$–$10^{-1}$, where section 4 predicts the forms cannot differ. Draft 3 (10-08) derived the axes from the mechanism instead:

1.  **Mechanism → control parameters.** From section 4.7 the face form's local error relative to the buoyancy drive scales as $S/B \sim (dz/H)/\mathrm{Ma} = 1/(\mathrm{Ma}\,N_H)$, with $\mathrm{Ma}_{\text{eff}} \sim \sqrt\varepsilon$ in linear onset. So the axes are $\varepsilon$ (sets Ma), $N_H = H/dz$, the acoustic Courant number $C$ (sets the implicit solver's dissipation), physical dissipation (viscous vs ILES) and geometry. Rotation (Ekman number) and Ra act only through Ma and are not separate axes.
2.  **Control parameters → the real decks' operating points** (survey 10-08): $dz/H_p$ 0.1–0.46 for most decks and 0.75 for brown-dwarf decks 29/30, i.e. $N_H$ 1.3–10; $C$ ~250 for the Jupiter 3-H decks; all ILES; production is cubed-sphere + implicit scheme 9.
3.  **A correction on the way.** On 10-07 the maximum production Courant number had been given as "about 20"; that covered only some deck families. The Jupiter decks run at a measured vertical acoustic Courant of ~247–249, so T5's Courant-100 arms were restored as deciding.

At low Mach number and these $N_H$, the first-order estimate (4.8) puts $S/B$ well above 1 (Figure 6): the regime where the choice of form can matter, and away from where T4 and T1 were run.

[FIGURE 6: not copied. File figs/fig6.svg, generated by figs/fig6_regime.py (+ figs/fig6_numbers.json) in the gravity-work report build.]

**Figure 6.** Where the tests sit relative to the real decks. (a) Mach number against cells per scale height $N_H$; the grey lines are $S/B \sim 1/(\mathrm{Ma}\,N_H) = 1, 10, \dots, 10^4$, (4.8). The grey band is the $N_H$ range of the decks ($dz/H_p$ 0.1–0.46, down to $N_H$ 1.3 for brown-dwarf decks 29/30). Orange: tests already run, T4 (Ma 0.013–0.095, $dz/H$ 0.056–0.374) and T1 (Ma $10^{-2}$–$10^{-1}$; its $N_H$ is not on record). Purple stars: the planned T1L matrix, $\varepsilon$ $10^{-3}$–$10^{-6}$ at $N_H$ 5 and $N_H$ 2.5, 10, 20 at $\varepsilon$ $10^{-5}$, placed at $\mathrm{Ma}_{\text{eff}} = \sqrt\varepsilon$. Look at the gap: T4 sits at $S/B$ below about 30 and T1 at Ma $10^{-2}$–$10^{-1}$; only T1L reaches the low-Mach corner. (b) Vertical acoustic Courant of T1L's implicit points $C$ 30 and 250 (and T4's $C_v$ 0.2–3.1).

### 6.3 The tests that were run, cut, or kept

| test | status 10-08 afternoon |
|----|----|
| T1 onset vs EVP near $\mathrm{Ra}_c$ (viscous) | n16, n32 done; n64 optional |
| T1L low-Mach onset vs EVP (deciding) | matrix defined; no result |
| T2 internal gravity waves | dropped |
| T3 local residual $S$ | dropped; T4's $S$ table stands in |
| T4 forcing ladder | owner final (6.4); verify cut to the two face-win arms |
| T5 long-time drift of a rest atmosphere | relaunched; shortened to 1000 $T_b$; no result |

**Why the cuts.** The leanest route was chosen. T2 and T3 could only explain a verdict, not deliver one at the operating points; T4's verification was cut to the two arms where a form had won; one deciding test, T1L, replaced the broad programme because the onset growth rate against an EVP is the only oracle with a known answer whose sensitivity to $S$ grows as $1/\varepsilon$ (section 4.8).

### 6.4 T4: weakly forced convection, the full account

**Why this test.** T4 asks whether either form departs from two laws that a correct code must obey in weakly forced, low-Mach convection: in steady state the convective flux carries the imposed flux ($f_{\text{conv}}/F = 1$ in the interior), and at fixed Reynolds number the Mach number scales as $M_{\text{rms}} \propto \varepsilon^{1/3}$, the low-Mach similarity law used by Edelmann et al. (2021) as a well-balanced-scheme oracle. It was chosen in draft 1 because the instrument for $S$ already existed and because Edelmann's test is the standard one in the literature.

**Deck** (commit `024d53e`). Two-dimensional box, LMARS + WENO5, RK3 at CFL 0.4, reflecting (sealed, insulating) $x_1$ walls, periodic $x_2$, $\gamma = 5/3$, $R_d = 1$. The initial state is a *neutral* polytrope (adiabatic, $m = 1.5$) with $n_\rho = 2$ density scale heights ($L_z = 2.794$, top $T = \rho = 1$, bottom $T = 3.79$), aspect $L_x/L_z = 2$. Convection is driven by snapy's own fixed fluxes: $+F$ into the bottom $L_z/16$ and $-F$ out of the top $L_z/16$. The forcing parameter is

$$
\begin{aligned}
&\varepsilon = F/(\rho_tc_t^3),\qquad \rho_t = 1,\quad c_t = (\gamma R_dT_t)^{1/2} = 1.291\\
&t_c = L_z/(\varepsilon^{1/3}c_t)\qquad\text{(nominal convective time)}\\
&\nu = \varepsilon^{1/3}c_tL_z/\mathrm{Re},\quad \mathrm{Re} = 30\qquad\text{(kinematic viscosity; no explicit conduction)}
\end{aligned}
$$

Holding Re fixed makes $M \propto \varepsilon^{1/3}$ the exact similarity law of the deck. Re 30 was chosen after the pilots: the inviscid (ILES) pilot at $\varepsilon = 10^{-2}$ reached $M_{\text{rms}} = 0.567$ in both forms, about 30 times the kinetic energy the flux can power, because in 2-D the inverse cascade builds domain-scale rolls limited only by grid dissipation (M set by numerics, not by $\varepsilon$); Re 300 was still rising at 40 $t_c$; Re 30 saturates by about 8 $t_c$. Runs last 40 $t_c$, frames every 0.5 $t_c$, scoring window 10–40 $t_c$. Arms: explicit (scheme 0, nx = 2nz) and implicit (scheme 9, nx = nz/4); nz = 32, 64, 128; $\varepsilon = 10^{-2}, 10^{-3}, 10^{-4}$; cell (fixer on) and face; seeds 42, 43, 44. That is 2×3×3×2×3 = 108 runs, about 168 CPU-hours, on snapy 117e449.

**Regimes reached.** The implicit arms are capped by snapy's explicit viscous step, $dt = \mathrm{cfl}\cdot dz^2/(4\nu)$ (pilot: $0.4\times0.001906/(4\times0.02588) = 0.0074$, equal to the measured $dt$), so the vertical acoustic Courant number $C_v$ reached only 0.2–3.1 and the bin $C_v > 10$ was unreachable in this deck. $dz/H$ spanned 0.056–0.374.

**Decision rule** (pre-registered, study design draft 2): a form wins an arm only where the cell−face gap exceeds the combined seed spread $\sqrt{sd_{\text{cell}}^2 + sd_{\text{face}}^2}$. A per-form test of $|\langle f\rangle-1|$ against its own spread is a description, never a ranking.

| arm | cell $\langle f\rangle-1$ ± sd | face $\langle f\rangle-1$ ± sd | gap / combined sd | verdict (seed sd) |
|----|----|----|----|----|
| explicit nz32, ε 1e-2 / 1e-3 / 1e-4 | −0.0025 / −0.0064 / −0.0004 | +0.0084 / +0.0093 / +0.0059 | 0.0059/0.0198; 0.0029/0.0235; 0.0055/0.0191 | no difference ×3 |
| explicit nz64, 1e-2 / 1e-3 | +0.0023 / −0.0007 | −0.0044 / +0.0060 | 0.0021/0.0251; 0.0052/0.0136 | no difference ×2 |
| explicit nz64, 1e-4 | +0.0212 ± 0.0034 | −0.0056 ± 0.0033 | 0.0157 / 0.0047 | **face** (owner side) |
| explicit nz128, all ε | −0.0138 / −0.0060 / −0.0017 | −0.0197 / −0.0055 / +0.0008 | 0.0059/0.0219; 0.0005/0.0177; 0.0009/0.0193 | no difference ×3 |
| implicit nz32, 1e-2 | +0.0058 ± 0.0010 | −0.0009 ± 0.0011 | 0.0049 / 0.0014 | degenerate (steady; three seeds are one sample) |
| implicit nz32, 1e-3 | +0.0395 ± 0.0054 | +0.0058 ± 0.0019 | 0.0337 / 0.0057 | **face** (owner side) |
| implicit, the other 7 arms | gaps 0.0013–0.0157 against combined sd 0.0121–0.0395 | | | no difference ×7 |

Oracle (i), $f_{\text{conv}}/F$ in the interior, window 10–40 $t_c$, mean ± sd over three seeds.

**The error bar, argued.** Two bars were available and they disagree by a factor of three. The per-run standard error from 2 $t_c$ blocks (median 0.042) would erase both face wins (gap 0.0157 against a combined per-run SE of 0.063; 0.0337 against 0.158). The seed spread (median 0.0131) keeps them. The study uses the seed spread, for a reason that was checked rather than assumed: the $f_{\text{int}}$ series oscillates, so its autocorrelation has negative lobes, and the error of a window mean computed with the full autocorrelation sum, $\frac{\sigma^2}{N}\big(1 + 2\sum_k(1-k/N)\rho_k\big)$, is median 0.0125 over the 36 arms, matching the seed sd 0.0131, whereas the white-noise $\sigma/\sqrt N$ that the block SE tracks is 0.0417. In one arm (explicit nz64 $\varepsilon$ $10^{-4}$ cell) the three seeds gave +0.019/+0.025/+0.020 with a per-run SE of 0.040 each; if that SE were right the chance of so tight a cluster would be 0.7 %. Two further checks closed the obvious loopholes: the departure $f-1$ is not storage ($\mathrm{corr}(f-1, S_{\text{int}}) = -0.31$ over 108 runs, and removing storage *increases* the spread, 0.0186 → 0.0243), and it is not a box energy source from the fixer (whole-box $B = +0.005 \pm 0.004$ in the +2 % cell arm; median $|B|$ over the 108 runs 0.4 % of $F$).

**Oracle (ii), the scaling.** At nz128 both forms follow $M \propto \varepsilon^{1/3}$ within the seed spread: explicit slope 0.330 ± 0.014 (cell) and 0.332 ± 0.018 (face), implicit 0.335 and 0.323. The coarse-grid slope "wins" (explicit nz32 cell, nz64 face) flip sign with resolution and vanish at nz128. At the low-$\varepsilon$ end (local slope $10^{-4}\to10^{-3}$) no arm separates the forms; explicit nz64 is a tie at gap/sd = 1.00.

**A correction.** An interim reading (10-08) said that face "stays on the $\varepsilon^{1/3}$ law one decade lower than cell". An independent review refuted it: the test compared each form with its own two-sigma band, which a noisier form passes more easily. Under the pre-registered rule there is no difference. The two remaining face wins are both coarse ($dz/H$ 0.1–0.5), neither survives at nz128, and both await the verifier (T4 verification was cut to these arms).

**What T4 measured about S** (the instrument). On saturated pilot states, $S$ = (face work of the total $x_1$ mass flux − cell work)/$dt$ was dumped for 600 steps. At the $x_1$ wall cells $S$ is 5.4 % of the cell work at every $\varepsilon$, nz and scheme; the buoyancy work $B = g\rho'w$ shrinks with $\varepsilon$, so the wall $S/B$ grows from about 0.5 ($\varepsilon$ $10^{-2}$) to about 10 ($\varepsilon$ $10^{-4}$), and it has a net sign there (sumS/sumB 0.06–0.7). In the interior $S$ is about $10^{-3}$ of the cell work and averages to nearly zero, yet still grows against $B$ as $\varepsilon$ falls (rmsS/rmsB 0.028 → 0.205). The statistics do not depend on which form produced the flow. This was the low-Mach signature that section 4 predicts. T4 itself could not show its consequence: at Re 30 the flow is viscously controlled and the Mach numbers (0.013–0.095) are far above those of the low-Mach production decks (section 6.2).

**T4 verdict.** No difference at nz128 in either oracle; two coarse owner-side face wins that await verification. T4 neither supports nor refutes either form at low Mach; it shows that at $M > 10^{-2}$ and Re 30 the choice does not matter for $f_{\text{conv}}$ or the scaling law.

**Placeholder — T4 verification.** The verifier's reproduction of the two face-win arms (implicit nz32 $\varepsilon$ $10^{-3}$ and explicit nz64 $\varepsilon$ $10^{-4}$, both forms × 3 seeds = 12 runs) does not exist yet. To be filled: the verifier's numbers, build, hardware, and whether the wins survive.

### 6.5 T1: onset near Ra_c (viscous)

The T1 deck with an independent EVP gives $\mathrm{Ra}_c(k) = 1268.597$. Results (reported second-hand; no run log is on record): both forms converge at second order (orders 2.14 cell, 2.06 face); growth-rate errors at n16/n32 are $-2.58\times10^{-3}$/$-5.85\times10^{-4}$ (cell) and $-2.27\times10^{-3}$/$-5.44\times10^{-4}$ (face); the n32 critical Rayleigh number is 1285.5 (cell) and 1284.3 (face) against the EVP's 1268.6. Face is about 10 % closer at both resolutions. By the draft-2 rule this is not yet a win (the Richardson estimate at the finest level and the verifier's n64 are missing). It is also outside the regime that matters: near $\mathrm{Ra}_c$ the drive is viscously limited and the deck's $\varepsilon$ is not small, so section 4 predicts a small difference, as observed. The T1 deck itself (box, $\varepsilon$, boundary conditions, $\nu$, $\kappa$) is not on record.

### 6.6 A wrong reading, and its correction

Recorded because it shows how easy the wrong conclusion is. An interim reading (10-08) called face "the physically right local accounting" and proposed face as the default on Cartesian grids, on the argument that energy should be booked where the mass moved. That argument is wrong at low Mach. The mass whose work the face form books, beyond the momentum, is the solver's diffusive and reconstruction flux $F - m$ (section 4.1), not physical transport. Booking its potential energy locally puts a numerical heat source into the cells of the flow, and section 4.7 shows that source grows against the buoyancy drive as $1/\mathrm{Ma}$ or $1/\mathrm{Ma}^2$. The T4 instrument had already shown $S/B$ rising as $\varepsilon$ fell (section 6.4); the argument ignored it. The correction followed the same day: with the mechanism of section 4, the reading became "cell (+ fixer) is right at low Mach; face wins only exact local E+PE bookkeeping", and it is overturned if snapy's T1L shows face's error flat and cell's growing as $\varepsilon$ falls.

### 6.7 T1L: low-Mach onset against the EVP (the deciding test)

**Design** (replaces a first version, which stopped at $\varepsilon$ $10^{-4}$ and so did not reach the decks' Mach numbers). Base point: the T1 deck and EVP with $\varepsilon = 10^{-5}$, $N_H = 5$ cells per pressure scale height, explicit, viscous at $\mathrm{Ra} = 2\mathrm{Ra}_c(k)$, one seed, linear phase. One factor at a time, both forms:

1.  $\varepsilon = 10^{-3}, 10^{-4}, 10^{-5}, 10^{-6}$ (8 runs);
2.  $N_H$ = 2.5, 10, 20 at $\varepsilon$ $10^{-5}$ (6 runs);
3.  implicit scheme 9 at vertical Courant 30 and 250, $\varepsilon$ $10^{-5}$, a wide box with small $k_x$ so the horizontal Courant stays below 1, plus an explicit control at the same $k_x$ (6 runs);
4.  ILES ($\mu = k = 0$) against the inviscid EVP (2 runs);
5.  one small cubed-sphere point, $S/B$ only, no EVP (2 runs).

About 24 short 2-D runs; the cost is set by explicit steps per e-fold ~ $N_H/\sqrt\varepsilon$, worst ~$2\times10^4$. One owner and an independent verifier (axes 1 and 2 at least). **Reading rule**: the form whose growth-rate error stays flat as $\varepsilon$ falls and as $N_H$ falls is right at low Mach; if the errors collapse onto $1/(\sqrt\varepsilon\,N_H)$, the scaling (4.8)/(4.10) holds and no more points are needed. Why this test decides: the EVP gives an exact answer, and section 4.8 predicts the face form's error grows as $1/\varepsilon$ (or $1/(\sqrt\varepsilon N_H)$) while the cell form's does not, so the two hypotheses separate by orders of magnitude over the $\varepsilon$ ladder.

**Placeholder: T1L results.** No deck diff, run or result had been posted when this report was written (10-08). To be filled: per form and $\varepsilon$, the growth-rate error against the EVP (owner and verifier); the same against $N_H$; the implicit, ILES and cubed-sphere points; whether the errors collapse onto $1/(\sqrt\varepsilon\,N_H)$.

### 6.8 T5: long-time drift of a rest atmosphere

**Question.** Does either form, or the fixer, make an atmosphere at rest drift over thousands of buoyancy periods $T_b$? **Design**: a discrete-hydrostatic atmosphere at rest (Mach must stay below $10^{-12}$), plus a seeded perturbed arm; fixer heat and $N^2$ tracked in time; regime grid by Courant and $dz/H$ bins; three seeds; CPU; owner and verifier on different hosts. 128 runs, 65 core-hours.

**Thresholds** (decided before results): $N_0^2 = 3.190\times10^{-4}$ s$^{-2}$ (the physical isothermal value; an earlier $2.279\times10^{-4}$ had missed $\gamma$); $N^2$ may not move by more than 5 %; a common round-off floor in mass and E+PE of about $-4\times10^{-14}$ to $-7.5\times10^{-14}$ per $T_b$, the same in both forms and arms, is not a form difference; forms are compared on perturbed-minus-rest E+PE drift in units of the initial kinetic energy $\mathrm{KE}_0$, by the hypot rule; the absolute $10^{-3}\,\mathrm{KE}_0$ pass line was dropped; the rest arm keeps a $10^{-9}$-of-$E$ limit; the cell form's fixer heat is itself a measured result.

**Run length and Courant.** The first 250 $T_b$ showed only linear round-off drift, so runs not yet started were capped at 1000 $T_b$, with the running explicit 32/H runs finishing 5000 $T_b$ as sentinels. The Courant-100 arms were first dropped as out of range and then restored as deciding, because the Jupiter decks run at a measured vertical acoustic Courant of ~247–249 (section 6.2).

**Placeholder: T5 results.** None posted when this report was written. To be filled: per arm and form, $N^2$ change, perturbed-minus-rest E+PE drift in $\mathrm{KE}_0$ with seed spread, the cell form's cumulative fixer heat (signed and absolute, per $T_b$ and in $\mathrm{KE}_0$), and mass drift; the Courant-100 arms.

### 6.9 Phase-2 status in one table

| test | regime reached | result |
|----|----|----|
| T1 (near $\mathrm{Ra}_c$) | viscous, moderate $\varepsilon$ | face ~10 % closer to EVP at n16, n32; not decisive (6.5) |
| T4 (Re 30 ladder) | Ma 0.013–0.095, $C \le 3.1$ | no difference at nz128; two coarse face wins await verification (6.4) |
| T1L | $\varepsilon$ to $10^{-6}$, $N_H$ 2.5–20, $C$ to 250 | pending |
| T5 | rest, to 5000 $T_b$, $C$ to 100 | pending |
| T4 verify | the two face-win arms, 12 runs | pending |

## 7. Conclusion, guidance and open items

### 7.1 Current conclusion

**Correctness (phase 1) is settled at 117e449** for the decks in use: both forms are correct in the sense that each conserves what it claims (face: local E+PE; cell + fixer: global E+PE, momentum-consistent local energy), the \#283 crash is gone in both, and the \#284 Limit is reported lifted to Courant ~2000–2700 on the 11 H column (reviewers' runs per the PR author; which \#285 change lifted it is not measured). The one known failure regime ($dz/H_p$ 0.7–0.9 together with Courant 197–657 on a 40 H column) is not reached by any real deck and is tracked in \#286.

**Which form is physically right (phase 2) is provisionally answered: the cell form at low Mach.** The argument is section 4: $S$ is truncation error; the face form converts it into a local heat source coherent with the flow whose size against the drive grows as the Mach number falls (4.7)–(4.10); the cell form returns it globally, where it has almost no projection on the dynamics. The evidence: the T4 instrument ($S/B$ rising as $\varepsilon$ falls in snapy). **It is provisional** because no snapy test has yet been run in the low-Mach regime with an exact answer.

**What would overturn it:** T1L showing the face form's growth-rate error flat while the cell form's grows as $\varepsilon$ falls; or T5 showing the cell form's fixer heat changing $N^2$ by more than 5 % or the rest state drifting, where the face form does not.

### 7.2 Operational guidance (until T1L reports)

| deck | form | why |
|----|----|----|
| Production: cubed-sphere, implicit scheme 9, low Mach (ice giants, Jupiter, brown dwarfs, hot Jupiters) | cell + fixer (default) | the only form inside the implicit operator on curved grids; low-Mach argument |
| Explicit Cartesian process studies that need exact local E+PE bookkeeping | face | E+PE to round-off cell by cell |
| Implicit Cartesian with face | face (in-operator) | stable since \#285; face-wallc is not in the operator and warns |
| Decks with open or periodic $x_1$, or grav2/grav3 ≠ 0 | cell, fixer off, or a face form | the fixer refuses them |
| Columns deeper than ~10 H with $dz/H_p > 0.5$ at implicit Courant > ~150 | check the column | \#286 regime; fixer off keeps it stable at the cost of the E+PE budget |

### 7.3 Open items

1.  T1L results (owner and verifier): the deciding test (6.7).
2.  T5 results (owner and verifier), including the fixer's cumulative heat at Courant 100 (6.8).
3.  T4 verification of the two coarse face-win arms (12 runs) (6.4).
4.  \#286: coarse implicit columns amplify the fixer heat.
5.  Face form inside the implicit operator on curved grids does not exist; curved-grid face runs keep the post-solve swap and its warning.
6.  The ISSI G18 deck: the fixer adds 54 % more energy at 117e449 than at 531e839 (~$10^{-4}$ of IE); unexplained.
7.  Which \#285 change lifted the \#284 Limit (Roe-diffusion booking or projection/clamp booking) and the fraction of the old fixer defect each removes were never measured; the mechanism of 5.4 is unverified (ablation arms in 5.4).
8.  The three-part split of $S$ (4.1) is shown only for third-order or higher reconstruction; PLM and the well-balanced reference on non-isothermal backgrounds may add terms (1-D column check in 4.1).
9.  Whether \#283's folded bug (a), the top-cell drain, is fixed at 117e449 is not on record.

## Appendix A. Notation

Symbols in order of first use. Signs follow snapy: the first coordinate $x_1 = z$ is vertical and points up; gravity points down, so grav1 = $g_1 < 0$.

| Symbol | Meaning | First defined |
|----|----|----|
| $\rho, p, T, e$ | density, pressure, temperature, specific internal energy | 2 |
| $\mathbf{v}$, $w = v_1$ | velocity; its vertical ($x_1$) component | 2 |
| $g_1$ = grav1 | the $x_1$ gravity component as the input sets it, negative when gravity points down | 2 |
| $g = -g_1$ | gravity magnitude, > 0 | 2 |
| $\Phi = -g_1z$ | gravitational potential, zero at $x_1 = 0$ | 2 |
| $E = \rho e + \tfrac12\rho\lvert\mathbf{v}\rvert^2$ | snapy's total energy: internal + kinetic, with no potential energy | 2 |
| $K$ | kinetic energy density $\tfrac12\rho\lvert\mathbf{v}\rvert^2$ | 2 |
| $\mathrm{PE} = \rho\Phi$ | potential energy density; $\sum V\Phi\rho$ is the column's PE | 2 |
| $i$, $i\pm\tfrac12$ | cell index; lower and upper face of cell $i$ | 3 |
| $V_i$, $A_{i\pm1/2}$, $dz$ | cell volume, face areas, vertical cell size (uniform Cartesian: $A/V = 1/dz$) | 3 |
| $\mathrm{x1v}_i$ | cell-centre coordinate (on Cartesian grids the face midpoint) | 3 |
| $\Phi_i$, $\Phi_f$ | potential at the cell centre; at a face | 3 |
| $m_i = \rho_iw_i$ | cell vertical momentum | 3 |
| $F_{i\pm1/2}$ | total $x_1$ mass flux through a face (dry gas plus species) | 3 |
| $F^R$ | the Riemann-solver mass flux, saved before sedimentation and the positivity limiter add mass | 3.6 |
| $F^c$, $F^d$ | central and numerical-diffusion parts of the Riemann mass flux, $F = F^c + F^d$ | 3.1 |
| $\rho_{L,R}$, $u_{L,R}$, $p_{L,R}$ | reconstructed left and right states at a face | 3.1 |
| $\bar\rho$, $\bar c$, $u^*$ | LMARS face-mean density, mean sound speed, interface velocity | 3.1 |
| $\lambda_k$, $\alpha_k$, $r_k$ | Roe eigenvalues, wave strengths, right eigenvectors | 3.1 |
| $s$, $w_{1,s}$, $w_{2,s}$, $c_s$ | Runge–Kutta stage; the integrator's stage weights; the stage's weight in the step's result | 3.2 |
| $W^{\text{cell}}_i$, $W^{\text{face}}_i$ | gravity work added to $E_i$ per stage in the cell and face forms | 3.3–3.4 |
| $S_i$ | the residual between the two forms, $g_1[(F_{i+1/2}+F_{i-1/2})/2 - m_i]$; $S^R$ is the same for $F^R$ | 3.5 |
| $D^s$, $D$ | the fixer's per-stage E+PE defect; the stage-weighted step defect $\sum c_sD^s$ | 3.6 |
| $(\Delta\rho)_{x1}$ | the stage's $x_1$ mass change with the two wall faces dropped | 3.6 |
| $\Delta_{\text{VIC}}$ | the implicit block's change of a quantity | 3.6 |
| $\tilde m$ | the fixer's deposit weight, $\rho + \sum$species (zero in solid cells) | 3.6 |
| fixgrav | the run-to-date sum of $-D$, printed in the log | 3.6 |
| VIC | vertically implicit (block-tridiagonal) acoustic solve; scheme 9 = full, scheme 1 = partial | 3.7 |
| $S_{\text{div}}$, $S_{\text{rec}}$, $S_{\text{dif}}$ | the three parts of $S$: PE relabelling, reconstruction mismatch, numerical mass diffusion | 4 |
| $H$, $H_\rho$ | pressure scale height; density scale height | 4 |
| $\ell$ | length scale of the flow | 4.4 |
| $c$, $\gamma$ | sound speed; ratio of specific heats | 4 |
| $\mathrm{Ma} = w/c$ | Mach number; $\mathrm{Ma}_{\text{eff}} \sim \sqrt\varepsilon$ the Mach scale of a linear mode | 4.4 |
| $B = g\rho'w$ | buoyancy work, the drive of convection ($\rho'$ the density perturbation) | 4.7 |
| $N_H = H/dz$ | cells per scale height | 4.7 |
| $\kappa$ | $S$ as a fraction of the cell work (in 4.8: the part of $S$ coherent with a mode, per unit $g\rho w$) | 4.7 |
| $\varepsilon$ (sections 4.8, 6.2, 6.7) | superadiabaticity, $\partial_z\bar s = -c_p\varepsilon/H$ | 4.8 |
| $\varepsilon$ (section 6.4, T4 only) | T4's forcing parameter $F/(\rho_tc_t^3)$ | 6.4 |
| $\sigma$, $N$ | growth rate of a linear mode; buoyancy frequency ($N_0$ its initial value in T5) | 4.8 |
| Ra, $\mathrm{Ra}_c$, Re, Pr | Rayleigh number and its critical value; Reynolds and Prandtl numbers | 6 |
| $C$, $C_v$ | acoustic Courant number of the step; its vertical part | 6.2, 6.4 |
| $T_b$ | buoyancy period (the time unit of T5) | 6.8 |
| $\mathrm{KE}_0$ | T5's initial kinetic energy | 6.8 |
| $\nu$ | kinematic viscosity | 6.4 |
| n16, n32, nz | vertical resolution (cells) | 6.4–6.5 |
| cell, face, face-wallc | the three values of `forcing/const-gravity/gravity-work`: cell work + fixer; face work everywhere; face work except in the $x_1$ wall cells | 3 |
