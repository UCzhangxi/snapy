# snapy Technical Report: outline (round 1)

> Editor: C0. Status: **for review by the lead, then approval by the project owner before drafting starts.**
> Pinned code: snapy `dae902b` (`next/final-batch` on UCzhangxi/snapy = snapy main `aea71ed` plus the gravity-work
> round); kintera `4dc613d04f24621b3119d343c5c7c9b93628895b` and pyharp `4721715855e937c1e8b218e964c0655f46e56e29`
> for code outside snapy. Every `path:lines@sha` below was checked by hand against the statement the lines carry,
> at the pins above, on 2026-10-09. `tools/check_citations.py` is not written yet; when it lands, this line is
> replaced by its output file and the date of the run. Until then no entry in this outline may claim a
> tool-verified citation. Binding style: `STYLE.md`. Symbols: `NOTATION.md`.

## How to read this outline

- **Chapter by chapter, then scheme by scheme.** Each scheme entry (`#### N.M`) carries the four items the brief asks
  for, under the bullet names used in the research inventories:
  - **Summary** (one line, with the switch, how it is set, and its default);
  - **Derivations**, each marked `exists: <source>` (a real, step-by-step derivation is in `sources/` or
    `docs/derivations/` at the pin) or `re-derive from <path:line@sha>` (no derivation exists: commit message only,
    result only, or nothing). A PR body that states a result is **not** counted as a derivation;
  - **Figures**, one line each (every figure is a committed script; STYLE.md section 6);
  - **Code** (`path:line@sha`, with function names) and **Tests** (file, ctest name, what it asserts, tolerance).

  Most entries also carry **Limits / known issues** and **Discrepancies** (source vs code; the code wins).
- Each scheme becomes one section file `book/chapters/NN-slug/_<scheme>.qmd`, written in the six layers of STYLE.md
  and included into its chapter file (STYLE.md sections 2 and 10.1), modelled on the worked example
  `chapters/06-gravity-energy/D_face_work_pe.md` (to be ported to `book/chapters/06-gravity-energy/_dwork.qmd`).
- The small line `inventory X: ...` under each heading names the research inventory entry it came from (the inventories
  are in this branch's history at commit `e15dd04`, `doc/tech-report/outline/`, with the one-off merge script), so a reviewer can trace it.
- "Research note" boxes keep the inventory's own scope paragraph and recommendations for that chapter.

## Changes to the proposed chapter list, and why

1. **Ch. 4 split into 4.A and 4.B.** The covariance and centroid corrections share one derivation thread (the in-cell
   product expansion) that the reconstruction and Riemann material does not need.
2. **Ch. 6 written by the editor**, with the worked example D. The constant-gravity forcing moved here from Ch. 9
   (the cell work is the default gravity work).
3. **Ch. 7 split into 7.A (explicit stages, time step, redo) and 7.B (the VIC).** The VIC column closure moved here
   from Ch. 11. The RK integrator is pyharp's and is cited there.
4. **Sedimentation moved from Ch. 9 to Ch. 10** (moist physics), with the species repairs.
5. **Ch. 11 renamed "Boundary conditions and immersed solids"**; exchange-filled ghosts are a pointer to Ch. 3/14.
6. **Ch. 14 split into 14.A parallel and GPU, 14.B output and restart, 14.C reproducibility.**
7. **No separate 1/R chapter**: the remainder is the last section of Ch. 5.
8. **Out of snapy, to Appendix E**: the radiative time-step limiter (external runner), the kinetics coupling (example
   driver), GPU chemistry; the integrator (pyharp). Dead code (turbulence, plume forcing, ANEOS stubs, cylindrical
   coordinates, `src/diagnostics/`) gets one paragraph each, not a section.

## Outline at a glance

| ch | title | schemes | with an existing derivation | needing a re-derivation | neither marked (control flow or table; see entry) |
|---|---|---|---|---|---|
| 1 | Overview and code map | 13 | 0 | 1 | 12 |
| 2 | Governing equations and thermodynamics | 9 | 0 | 6 | 3 |
| 3 | Grids and geometry | 15 | 7 | 6 | 6 |
| 4 | Spatial discretization | 17 | 5 | 15 | 1 |
| 5 | Hydrostatic and well-balanced treatment | 10 | 6 | 6 | 0 |
| 6 | Gravity and energy | 6 | 6 | 4 | 0 |
| 7 | Time integration | 13 | 5 | 4 | 7 |
| 8 | Positivity, floors and limiters | 13 | 5 | 5 | 5 |
| 9 | Diffusion, viscosity and forcing | 11 | 2 | 5 | 4 |
| 10 | Moist physics coupling | 8 | 1 | 6 | 2 |
| 11 | Boundary conditions and immersed solids | 10 | 1 | 4 | 6 |
| 12 | Build-time and run-time switches and configurations | 8 | 4 | 0 | 4 |
| 13 | Conservation budgets and diagnostics | 7 | 2 | 3 | 3 |
| 14 | Parallelism, GPU, restart/IO and reproducibility | 12 | 0 | 2 | 10 |
| 15 | Verification catalogue | 0 | 0 | 0 | 0 |
| | **total** | **152** | **44** | **67** | **63** |

"re-derive" is counted per scheme: a scheme with any derivation marked re-derive counts once. The full list is
Appendix B.

## Chapters

1. [Overview and code map](#ch1)
   - 1.1 Driver loop (time step, stages, redo, outputs)
   - 1.2 MeshBlock construction (`reset`)
   - 1.3 Initialization
   - 1.4 Stage update `advance_local` (MeshBlock)
   - 1.5 `MeshBlock::forward` (exchange-then-advance)
   - 1.6 Mesh (several blocks per process)
   - 1.7 Hydro forward (code map of its seven sections)
   - 1.8 Scalar forward
   - 1.9 CPU/GPU dispatch (DispatchStub + TensorIterator; CUDA loops)
   - 1.10 Tensor layout, variable indices, ghost zones, interior slices
   - 1.11 Options objects and YAML
   - 1.12 Python package `snapy`
   - 1.13 External dependencies (kintera, pyharp, torch, comm and IO libraries)
2. [Governing equations and thermodynamics](#ch2)
   - 2.1 Conservation laws and operator ordering in one RK stage
   - 2.2 EquationOfState interface, options and type dispatch
   - 2.3 Ideal gas EOS
   - 2.4 Ideal-moist EOS (constant heat capacities, zero-volume condensates, reference energies)
   - 2.5 Moist-mixture EOS (kintera-backed)
   - 2.6 ANEOS (tabulated EOS through an external library)
   - 2.7 Shallow-water EOS
   - 2.8 EOS ↔ solver consistency conditions (temp2inteng and friends)
   - 2.9 Saturation adjustment (kintera UV equilibrium) — thermodynamic side
3. [Grids and geometry](#ch3)
   - 3.1 One global grid, sliced per block (decomposition-invariant faces)
   - 3.2 Cartesian metric
   - 3.3 Spherical-polar metric and geometric sources
   - 3.4 Gnomonic equiangular cubed sphere (geometry and metric)
   - 3.5 Radial face moments and the face-centroid shift (curved-grid helpers)
   - 3.6 Layouts and rank maps (slab, cubed, cubed-sphere)
   - 3.7 Physical vs internal faces (bfunc assignment)
   - 3.8 Generic ghost exchange (what is filled)
   - 3.9 Cubed-sphere cross-panel ghost interpolation
   - 3.10 Cubed-sphere face-state seam sync (hydro and scalar LR states)
   - 3.11 θ (positivity donor factor) across seams: raw copy
   - 3.12 x1 seams between blocks (column split, `cubed` layout pz>1)
   - 3.13 Exchange of conserved vs primitive variables, and the velocity frame at seams
   - 3.14 x1-wall corner refresh inside tangential ghost slabs (#265)
   - 3.15 Registered but non-functional coordinate type `cylindrical`
4. [Spatial discretization](#ch4)
   - 4.1 Finite-volume update and flux divergence (stage operator)
   - 4.2 Reconstruction framework (Reconstruct / Interp, variable split, floors)
   - 4.3 Donor cell ("dc")
   - 4.4 PLM (van Leer harmonic-mean slope)
   - 4.5 Linear centred polynomials cp3 / cp5 (and cp2/cp4/cp6 helpers)
   - 4.6 WENO3 / WENO5 (Jiang–Shu weights, eps 1e-6, optional scaling)
   - 4.7 PPM
   - 4.8 Riemann solver framework, face-local frame, face-pressure output
   - 4.9 LMARS (low-Mach approximate Riemann solver; production default in example decks)
   - 4.10 HLLC (PVRS wave speeds)
   - 4.11 Roe (ideal gas and ideal-moist)
   - 4.12 Shallow-water Roe and plume-roe
   - 4.13 Single-valued x1 seam fluxes (process-seam averaging)
   - 4.14 Geometric (curvature) sources, spherical-polar; momentum flux form
   - 4.15 Geometric sources, gnomonic cubed sphere; exact cell volume and solid angle
   - 4.16 x2/x3 face-flux covariance and centroid correction (SNAP_FLUX_COVARIANCE, #289/#293)
   - 4.17 x1 rho-w mass-flux covariance (SNAP_X1_MASS_COVARIANCE)
5. [Hydrostatic and well-balanced treatment](#ch5)
   - 5.1 Well-balanced x1 reconstruction (perturbation about a hydrostatic reference)
   - 5.2 Hydrostatic reference kernel — face-pressure scan, cell pressure, density reference ("smooth5")
   - 5.3 Wall clamp and the wall continuation of the default reference (wb-wall-clamp, linear/ln closure)
   - 5.4 Reference continuity across x1 seams (anchor relay and ghost-row exchange)
   - 5.5 Hydrostatic mode (non-hydrostatic < 1): gravity replaced by the discrete pressure gradient
   - 5.6 balance_column — projection of a ghost-free column onto the scheme's discrete balance
   - 5.7 SNAP_WB_REF4 — fourth-order, cell/face-consistent density reference (and non-uniform cell pressure)
   - 5.8 SNAP_X1_CENTROID_EXACT — r^2-exact x1 maps on spherical-polar
   - 5.9 The 1/R remainder on spherical-polar (what is left after the corrections)
   - 5.10 (legacy box) isentropic wall ghosts and zero-gradient wall faces
6. [Gravity and energy](#ch6)
   - 6.1 Constant gravity forcing and the cell form of the gravity work (`gravity-work: cell`, the default)
   - 6.2 Face form of the gravity work (`gravity-work: face`, `face-wallc`) and the cp3/cp5/weno5 curvature flux
   - 6.3 Gravity-work fixer (global $E+\mathrm{PE}_d$ correction for `gravity-work: cell`)
   - 6.4 The corrected-PE face work, scheme D (`SNAP_GRAVITY_WORK_RADIAL_EXACT`)
   - 6.5 Gravity work inside the vertical implicit operator (cell, face rows, projection and clamp work)
   - 6.6 What each form conserves (summary and oracle guide)
7. [Time integration](#ch7)
   - 7.1 Explicit SSP Runge–Kutta stage update (Shu–Osher form)
   - 7.2 Ghost-exchange placement within a stage (MeshBlock vs Mesh driver)
   - 7.3 CFL time step (acoustic, implicit-advective, shear, diffusion; global MIN; redo halving)
   - 7.4 Step acceptance and rejection (`check_redo` / `apply_redo`), collective decision, max_redo, abnormal exit
   - 7.5 Operator-split pieces at the step boundary (saturation adjustment, kinetics)
   - 7.6 VIC activation and options
   - 7.7 VIC block-tridiagonal assembly (Roe-linearised flux Jacobian, |A| dissipation, I/dt, gravity coupling, wall closure)
   - 7.8 Stage-weighted implicit time step (dt_corr = w2·dt)
   - 7.9 Block-tridiagonal forward sweep and backward substitution
   - 7.10 LU pivot tolerance and failed-column sentinel (#290)
   - 7.11 VIC solve rejection, latch and rollback (cause 32)
   - 7.12 VIC constituent redistribution (implicit mass correction as face fluxes; "Component B")
   - 7.13 VIC column closure versus the x1 boundary type
8. [Positivity, floors and limiters](#ch8)
   - 8.1 Tracer flux positivity limiter θ (hydro species channels)
   - 8.2 Carry of energy and momentum with withheld species mass
   - 8.3 Positivity-limited species fluxes carry energy and momentum (moist carry)
   - 8.4 Passive-scalar limiter and complement upper bound
   - 8.5 Conserved-variable EOS limiter (`apply_conserved_limiter_`)
   - 8.6 Conserved/primitive limiter — floors (density, pressure, temperature) and limiter marks
   - 8.7 Primitive-variable EOS limiter (`apply_primitive_limiter_`)
   - 8.8 Reconstruction-stage floors
   - 8.9 Well-balanced face positivity floor (face-density/pressure fallback)
   - 8.10 Dry channel positivity inside the VIC (pass-3a availability clamp, donor mark, species donor margin)
   - 8.11 Round-off thresholds for positivity events
   - 8.12 Fresh-primitive floor detector (redo cause 1)
   - 8.13 Dry-carry of passive tracers under dry-mass sources (0/0 guard)
9. [Diffusion, viscosity and forcing](#ch9)
   - 9.1 Forcing framework and registration
   - 9.2 User stage forcings
   - 9.3 Coriolis (123 and xyz forms, cubed-sphere covariant)
   - 9.4 Isotropic viscosity and heat conduction (forcing/diffusion)
   - 9.5 Diffusion face coefficient at walls and ghosts (one-sided wall extrapolation)
   - 9.6 x1 profiles of the kinematic coefficients (nu_scale_x1, kappa_scale_x1) and the product face coefficient
   - 9.7 Body heating, top cooling, bottom heating
   - 9.8 Bottom relaxation (temperature, velocity, composition)
   - 9.9 Sponge layers (top and bottom)
   - 9.10 Plume forcing (unreachable)
   - 9.11 Turbulence (not built)
10. [Moist physics coupling](#ch10)
   - 10.1 Saturation adjustment in the step
   - 10.2 check_redo — causes, reduction, restore (saturation and limiter)
   - 10.3 Condensate repair by parent-vapour borrow (stoichiometric split)
   - 10.4 Column vapour repair fix_vapor (volume-weighted, upward fallback) and parentless clouds
   - 10.5 Column vapor and cloud repair (`fix_vapor_impl`)
   - 10.6 Precipitation and evaporation kinetics (driver-level coupling, kintera rates)
   - 10.7 Passive scalar (tracer) transport per dry air, with optional upper bound
   - 10.8 Sedimentation of condensates (recommended to move to Ch. 10)
11. [Boundary conditions and immersed solids](#ch11)
   - 11.1 Boundary-function registry, YAML parsing, and face classification
   - 11.2 Reflecting wall
   - 11.3 Periodic
   - 11.4 Extrapolation (zero-gradient)
   - 11.5 Outflow / radiating characteristic boundary
   - 11.6 Custom (no-op) and solid (mask) boundary functions
   - 11.7 When ghosts are filled (apply_boundaries, exchange_ghost_zones, corner refresh)
   - 11.8 Exchange-filled ghosts (layouts, cubed-sphere panels) — pointer section
   - 11.9 Immersed solids (mask, rectification, face-state mirror, refill)
   - 11.10 Boundary conditions and the well-balanced reference state
12. [Build-time and run-time switches and configurations](#ch12)
   - 12.1 CMake options and cache variables (build-time)
   - 12.2 `configure.h` macros and compile definitions (build-time)
   - 12.3 environment helper `get_env` and the read-once rule
   - 12.4 `SNAP_WB_REF4` (fourth-order, cell/face-consistent x1 well-balanced reference)
   - 12.5 `SNAP_X1_CENTROID_EXACT` (spherical-polar r^2-average x1 formulas)
   - 12.6 `SNAP_FLUX_COVARIANCE` (#289 x2/x3 face-flux covariance and centroid terms)
   - 12.7 `SNAP_X1_MASS_COVARIANCE` (x1 mass-flux covariance)
   - 12.8 `SNAP_GRAVITY_WORK_RADIAL_EXACT` (option F: corrected-PE gravity work)
   - 12.9 runtime environment for layout/communication
   - 12.10 test-harness environment variables (not read by `src/`)
   - 12.11 YAML scheme keys (run-time)
   - 12.12 Coverage matrix (switch combination -> ctest entries)
13. [Conservation budgets and diagnostics](#ch13)
   - 13.1 cycle-line budget (`print_cycle_diagnostics`)
   - 13.2 positivity-limiter meters (`limcut`, `thetamin`, `thetasevere`, hits)
   - 13.3 VIC clamp meter (`vicclamp`)
   - 13.4 gravity-work fixer E+PE budget (D, wall mass, `fixgrav`)
   - 13.5 redo causes and termination status (diagnostic view)
   - 13.6 output-field diagnostics
   - 13.7 mass-conservation regression checks
14. [Parallelism, GPU, restart/IO and reproducibility](#ch14)
   - 14.1 Launch environment and rendezvous
   - 14.2 Communication backends (Gloo, UCX via commux, external PG; no NCCL)
   - 14.3 Exchange message matching and in-process copies
   - 14.4 Several blocks per process and GPU streams
   - 14.5 Collectives and global decisions
   - 14.6 GPU execution
   - 14.7 NetCDF output (per-block files, combine)
   - 14.8 PnetCDF output
   - 14.9 Restart files (write, bundle, read)
   - 14.10 Output scheduling, statistics and termination
   - 14.11 Combine and inspect tools (post-processing)
   - 14.12 Reproducibility and bit-for-bit claims (inventory)
15. [Verification catalogue](#ch15)
   - 15.1 registration mechanics and labels
   - 15.2 Ch.2 Equations and thermodynamics (EOS)
   - 15.3 Ch.3 Grids and geometry
   - 15.4 Ch.4 Spatial discretization
   - 15.5 Ch.5 Hydrostatic and well-balanced treatment
   - 15.6 Ch.6 Gravity and energy
   - 15.7 Ch.7 Time integration (RK3, VIC, LU, CFL, redo)
   - 15.8 Ch.8 Positivity, floors, limiters
   - 15.9 Ch.9 Diffusion, sedimentation, forcing
   - 15.10 Ch.10 Moist coupling
   - 15.11 Ch.11 Boundary conditions
   - 15.12 Ch.12 Configuration
   - 15.13 Ch.13 Diagnostics
   - 15.14 Ch.14 Parallelism, GPU, restart/IO
   - 15.15 examples used as regression
16. [Known limits](#ch16)
17. [Appendices](#ch17)

## Assignment proposal for the four chapter authors (for the lead to decide)

| author | chapters | why together |
|---|---|---|
| C1 | 1, 3, 14 | code map, geometry and decomposition, parallel/IO: one researcher already mapped all three |
| C2 | 2, 9, 10 | thermodynamics, forcing and moist coupling share kintera and the species machinery |
| C3 | 4, 5 | reconstruction, covariance and well-balanced reference: one derivation thread |
| C4 | 7, 8, 11 | time integration, positivity and boundaries share the VIC and the redo machinery |
| C0 (editor) | 6, 12, 13, 15, 16, 17 | gravity/energy (model chapter), and the cross-cutting chapters that must agree with every other |

---

<a id="ch1"></a>
## Chapter 1. Overview and code map

How one step runs from the driver to the kernels; CPU/GPU dispatch; tensor layout; options, YAML and the Python package; what lives outside snapy. Kept as a code map with a step-flow figure. The environment-switch table moves to Appendix D (cited by every physics chapter). The redo details are owned by 7.A; this chapter points to them.

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: one time step from driver to kernels (MeshBlock / Mesh, RK stages, hydro forward and its seven sections, scalar,
implicit entry, outputs, redo), CPU/GPU dispatch, tensor layout and indexing, options/YAML/env switches, the Python
package and the external dependencies. Recommendation: keep it as a code map with a step-flow diagram. Move the redo /
`check_redo` details into the chapter that owns limiters and positivity (it is only pointed to here). Put the
environment-switch inventory (S1.14) in an appendix table that the physics chapters cite, so they do not each restate it.
One cross-chapter fact belongs here: `MeshBlock::forward` and `Mesh::forward` order the ghost exchange differently
(S1.5, S1.6).

</details>


#### 1.1 Driver loop (time step, stages, redo, outputs)
<sub>inventory A: Scheme 1.1: Driver loop (time step, stages, redo, outputs)</sub>

- Summary: the driver (C++ example or Python) calls `max_time_step`, then `forward(vars, dt, stage)` once per integrator
  stage, then `check_redo`, then `make_outputs`. snapy has no built-in main loop. Switch: integrator `type`, `cfl`, `tlim`, `nlim`
  come from the YAML `integration:` block, read by pyharp's `harp::IntegratorOptionsImpl::from_yaml`. snapy calls it at
  `src/mesh/meshblock_options.cpp:43@e894700`, and its own key check lists pyharp's keys
  (`src/implicit/implicit_hydro.cpp:27-30@e894700`).
- Derivations: none (control flow).
- Figures:
  - Flow chart: cycle → max_time_step (MIN-allreduce) → stages s=0..S-1 [exchange → hydro → scalar → user forcing →
    RK combine → limiter → (last stage: saturation adjust, gravity-work fixer) → boundaries] → check_redo (MAX-allreduce)
    → outputs.
  - Timeline of one cycle with the redo branch (dt halves by 2^-redo).
- Code:
  - `examples/run_hydro.cpp:161@e894700` — single-MeshBlock loop (`pintg->stop`, `max_time_step`, stage loop, kinetics,
    `check_redo`, `make_outputs`). Output before the loop only on a fresh start (`:157`).
  - `examples/straka.cpp:110@e894700` — Mesh-API loop (`mesh->initialize`, `set_cycle`, stage loop, `check_redo`,
    `make_outputs`, `finalize`). It calls `make_outputs` right after initialize, on restart too (`:139`).
  - `src/mesh/meshblock.cpp:510@e894700` `MeshBlockImpl::max_time_step` — local hydro dt, MIN-allreduce. Returns
    `2^-current_redo * cfl * dt` (`:528`).
  - `src/mesh/mesh.cpp:306@e894700` `MeshImpl::max_time_step` — MIN over the local blocks, then one allreduce.
  - `src/mesh/meshblock.cpp:1302@e894700` `check_redo` = `apply_redo(reduce_redo_flags(local_redo_flags()))`
    (`:1229`, `:1278`, `:1288`). `src/mesh/mesh.cpp:422@e894700` `MeshImpl::check_redo` checks signals first, ORs the
    flags over the local blocks, then makes one reduction.
  - `src/mesh/meshblock.cpp:985@e894700` `make_outputs` — writes when `current_time >= next_time` (`:991`), then
    advances `next_time` and `file_number`.
  - `src/mesh/meshblock.cpp:1121@e894700` `finalize` — writes the final outputs and reports the termination reason (signal / nlim /
    tlim / abnormal → status 1).
- Tests: `tests/run_restart_cycle_limit.py` (`test_restart_cycle_limit`) — a resumed straka run restarts at the same
  cycle and stops at cycle 120. First resumed cycle-line time/dt/mass0/energy match within abs 1e-12, termination time
  within 1e-9 (tolerances hard-coded in the runner, `:101-196`). `tests/test_check_redo_parallel.cpp`
  (`test_check_redo_parallel.release`, 2 ranks) — one redo decision across ranks, and rollback restores `hydro_u` exactly
  (`torch::equal`).
- Limits / known issues:
  - Issue #277 (open in `gh__ISSUE_THREADS_251-294.md:585`): a resumed run rewrites its last outputs, including its
    source restart file. The cause is still in the code: `restart.cpp:47-57` saves the pre-write `file_number`/`next_time`, and
    `meshblock.cpp:991` advances them only after the write.
  - Operator-split work that the driver applies between stages (kinetics in `run_hydro.cpp:171-191`) is outside snapy's step.
- Discrepancies: none.


#### 1.2 MeshBlock construction (`reset`)
<sub>inventory A: Scheme 1.2: MeshBlock construction (`reset`)</sub>

- Summary: builds the layout (process group), nulls the boundary functions of internal faces, builds outputs,
  integrator, coordinate, hydro, scalar, internal boundary, and the stage registers u0/s0. Switch: the `MeshBlockOptions`
  sub-options (from YAML via `MeshBlockOptionsImpl::from_yaml`).
- Derivations: none.
- Figures: a module tree (MeshBlock → Layout, Integrator(harp), Coordinate, Hydro{EOS(kintera thermo), Recon, Riemann,
  Forcings, Implicit, Sedimentation}, Scalar, InternalBoundary, OutputTypes).
- Code:
  - `src/mesh/meshblock.hpp:41@e894700` `MeshBlockOptionsImpl`. `:116` `MeshBlockImpl`.
  - `src/mesh/meshblock.cpp:66@e894700` constructor — `resolve_global_grid()`, and checks that bfuncs has at least 2/4/6 entries.
  - `src/mesh/meshblock.cpp:111@e894700` `reset`. `:116` `LayoutImpl::create`. `:143` internal-face bfunc set to
    nullptr (slab/cubed only). `:207` output types. `:231` `harp::IntegratorImpl::create`. Then coord, hydro, scalar and
    ib follow in order. u0/s0 are float64 buffers `[nvar, nc3, nc2, nc1]`.
  - `src/mesh/meshblock_options.cpp:13@e894700` `MeshBlockOptionsImpl::from_yaml` — the order is layout, hydro, scalar
    (scalar recon defaults to hydro recon23), integrator, outputs, coordinate, ib, external BCs.
- Tests: `tests/test_yaml_keys.cpp` (`test_yaml_keys.release`) — 30 cases, each of which refuses an unknown key in its
  YAML block.
- Limits / known issues: the world size must equal px·py·pz (·6 for cubed-sphere), `meshblock.cpp:133`.
- Discrepancies: none.


#### 1.3 Initialization
<sub>inventory A: Scheme 1.3: Initialization</sub>

- Summary: check the shapes of `hydro_w` (and `scalar_r`), apply the physical boundaries to primitives, exchange
  primitive ghosts (interpolating), compute conserved `hydro_u = W->U`, seed `scalar_s = u[IDN]*r`, then fill solids and
  apply the boundaries to conserved variables. Restart replaces all of this with `_init_from_restart` (Ch14 S14.9).
  Switch: `restart_file` argument.
- Derivations: none.
- Figures: sequence of one block's init, showing where the ghosts become valid.
- Code: `src/mesh/meshblock.cpp:360@e894700` `initialize`; `:401` `initialize_local`; `:434` `initialize_under_mesh`
  (the Mesh path); `:454` `finalize_initialization`; `src/mesh/mesh.cpp:280@e894700` `MeshImpl::initialize`. A restart
  calls `blocks[i]->initialize(vars[i], file)` one block after another on the caller thread, with no exchange.
- Tests: covered by every example test. Nothing targets this scheme alone.
- Limits / known issues: the restart path does no ghost exchange. It relies on the ghost zones saved in the file
  (`restart.cpp:29-36` saves whole tensors).
- Discrepancies: none.


#### 1.4 Stage update `advance_local` (MeshBlock)
<sub>inventory A: Scheme 1.4: Stage update `advance_local` (MeshBlock)</sub>

- Summary: stage 0 saves u0/s0 and resets the per-step meters. Then come hydro `forward` (returns du), scalar `forward`
  (plus the implicit dry-mass tracer transfer and the dry-source carry), user TorchScript stage forcings, the RK combine
  `pintg->forward(stage,u0,u,du)`, the conserved limiter, and the solid refill. The last stage also runs kintera
  saturation adjustment and the gravity-work fixer. `apply_boundaries` runs at the end. Switch: integrator stages (harp);
  `user_stage_forcings` (Python `set_user_stage_forcings`).
- Derivations:
  - RK stage form u ← w0 u0 + w1 u + w2 du and the stage weights: external (pyharp). Re-derive the weight product
    `w2_s ∏_{t>s} w1_t` from `src/hydro/hydro_forward.cpp:985-995@e894700`.
  - Implicit tracer transfer `(P - P_above)/V` with upwinded r: re-derive from `src/mesh/meshblock.cpp:663-675@e894700`.
  - Dry-source carry rule: re-derive from `src/mesh/meshblock.cpp:633-645@e894700`.
- Figures:
  - Box diagram of du accumulation (flux divergence, forcings, implicit, user) feeding the RK combine.
  - Stage-by-stage timeline marking where `rk_stage` is published (used by the implicit dt weight).
- Code: `src/mesh/meshblock.cpp:597@e894700` `advance_local`; `:612` u0 save; `:650` `phydro->forward`; `:662`
  `pscalar->forward`; `:734` user forcing call; `:755` RK combine (hydro); `:768` RK combine (scalar); `:813`
  `pthermo->forward` (kintera ThermoY saturation adjustment, interior only); `:838` gravity-work fixer; `:841`
  `apply_boundaries`. The user forcing contract (keys `hydro_du`, `scalar_ds` only) is at `:690-720`.
- Tests: `tests/test_user_output.cpp` (`test_user_output.release`) —
  `UserForcing.scripted_stage_forcings_add_tendencies_in_list_order`, `..._rejects_unsupported_keys`,
  `..._module_is_shared_across_parallel_blocks`; `tests/test_jit_user_forcing.py` (`test_jit_user_forcing_python`).
- Limits / known issues: saturation adjustment runs only when `thermo()->reactions().size() > 0`, on the last stage.
- Discrepancies: none.


#### 1.5 `MeshBlock::forward` (exchange-then-advance)
<sub>inventory A: Scheme 1.5: `MeshBlock::forward` (exchange-then-advance)</sub>

- Summary: a single-block driver exchanges conserved and scalar ghosts BEFORE reconstruction, so operator-split sources
  the driver applied since the last stage (e.g. kinetics on `hydro_u`) are synchronised before use. Switch: none.
- Derivations: none.
- Figures: two orderings side by side, exchange-before-advance (MeshBlock) and advance-then-exchange (Mesh).
- Code: `src/mesh/meshblock.cpp:545@e894700` `forward` (`:550` `exchange_ghost_zones`, `:551` `advance_local`);
  `:913` `exchange_ghost_zones` (conserved, then scalar, then the x1-wall corner refresh `:972`, then the scalar primitive).
- Tests: indirect (all single-block examples).
- Limits / known issues: the in-code comment says that exchanging before reconstruction removed a one-signed seam bias
  on the cubed sphere. No regression test isolates that.
- Discrepancies: see S1.6. Mesh orders it the other way.


#### 1.6 Mesh (several blocks per process)
<sub>inventory A: Scheme 1.6: Mesh (several blocks per process)</sub>

- Summary: `Mesh` owns `blocks_per_process` MeshBlocks and runs them concurrently on a worker-thread pool, with one CUDA
  stream per block on GPU. `Mesh::forward` runs `advance_local` on every block, then the global gravity-work fixer (one
  sum over the local blocks, one allreduce), then `exchange_ghost_zones`. Switch: YAML
  `distribute: blocks_per_process` (default 1), read at `src/mesh/mesh.cpp:216-217@e894700`.
- Derivations: none.
- Figures: thread/stream diagram (caller stream → event → per-block streams → events joined back to the caller).
- Code: `src/mesh/mesh.cpp:47@e894700` `BlockWorkerPool` (`:57` stream from the pool per block, `:82` `submit` with
  event fences); `:225` `MeshImpl::reset` (clones the options and repartitions each block, `:246-248`); `:265`
  `run_block_jobs`; `:331` `MeshImpl::forward`; `:377` `exchange`; `:460` `finalize`.
- Tests: `tests/test_mesh_multi_block.cpp` (`test_mesh_multi_block.release`, 2 ranks) — ghost sides uniform and equal to
  the neighbour id, both a local and a remote neighbour seen; `tests/test_mesh_exchange.py` (`test_mesh_exchange_python`)
  — every ghost equals the neighbour's rank exactly; `tests/test_cubed_sphere_exchange.cpp` checks one CUDA stream per
  block (`EXPECT_EQ(num_worker_streams, blocks)`).
- Limits / known issues:
  - Blocks of one process must advance concurrently. In-process x1 messages wait at most 5 min
    (`src/layout/layout.cpp:879-899@e894700`).
  - Remote block-to-block messages allow at most 16 blocks per process (`layout.cpp:849-857`).
- Discrepancies: with `blocks.size()==1`, `Mesh::forward` (`mesh.cpp:335-338`) calls `advance_local` and THEN
  `exchange_ghost_zones`, the reverse of `MeshBlock::forward` (S1.5). A Mesh-API driver that applies operator-split
  sources between `forward` calls therefore reconstructs from ghosts exchanged before those sources (inferred from the
  code; not measured). The cubed-sphere decomposition report (`canoe__cubedsphere_decomposition_TECH_REPORT.md` §4)
  reasons from the MeshBlock order only.


#### 1.7 Hydro forward (code map of its seven sections)
<sub>inventory A: Scheme 1.7: Hydro forward (code map of its seven sections)</sub>

- Summary: (1) EOS U→W; (2) x1 reconstruction with the optional well-balanced reference, x1 Riemann flux, sedimentation,
  x1 seam averaging; (3) x2/x3 LR states and the cubed-sphere seam swap; (4) x2/x3 fluxes, optional #289 covariance,
  tracer positivity limiter; (5) flux divergence and geometric sources (Coordinate::forward); (6) forcings and gravity
  work; (7) implicit correction. Switches: listed per physics chapter. The env switches are in S1.14.
- Derivations: owned by the hydro, WB, gravity-work and positivity chapters. None here.
- Figures: a pipeline diagram of the seven sections, marking the three places that communicate (x1 seam average, LR
  seam swap, θ exchange).
- Code: `src/hydro/hydro_forward.cpp:198@e894700` `HydroImpl::forward`; `:218` `peos->forward`; `:242` section 2;
  `:297` `_hydro_ref_x1`; `:357` x1 reconstruction (WB path, floor=false); `:413` x1 Riemann; `:430` sedimentation;
  `:448` x1 seam average; `:551`/`:569` x2/x3 LR; `:598`/`:623` x2/x3 flux; `:646` positivity; `:724`/`:735`
  divergence; `:763`/`:773` forcings; `:924` implicit; `:941` stage weight on the implicit dt (rk3 only); `:977`
  `_apply_implicit_correction`. Buffers F1/F2/F3/P1/D: `src/hydro/hydro.cpp:161@e894700` ff.
- Tests: owned by the physics chapters.
- Limits / known issues: the implicit stage weight is applied only when `stages.size()==3` (`hydro_forward.cpp:939`).
  Other integrators keep the full-dt operator.
- Discrepancies: none.


#### 1.8 Scalar forward
<sub>inventory A: Scheme 1.8: Scalar forward</sub>

- Summary: tracer reconstruction and upwind flux driven by the hydro mass flux. The cubed-sphere LR states use the same
  `:+`/`:-` raw swap as hydro, and θ is exchanged as a raw copy. Switch: YAML `scalar:` (read at
  `src/scalar/scalar_options.cpp:11@e894700`).
- Derivations: owned by the scalar/positivity chapter.
- Figures: none here (see Ch3 S3.11).
- Code: `src/scalar/scalar.cpp:64@e894700` `ScalarImpl::forward`; `:84` sync options; `:96` `scalar_wl:+`; `:144` θ
  raw copy.
- Tests: `tests/test_scalar.cpp` (`test_scalar.release`); the seam tests are listed in Ch3.
- Limits / known issues: none.
- Discrepancies: none.


#### 1.9 CPU/GPU dispatch (DispatchStub + TensorIterator; CUDA loops)
<sub>inventory A: Scheme 1.9: CPU/GPU dispatch (DispatchStub + TensorIterator; CUDA loops)</sub>

- Summary: point kernels are templated `*_impl.h` functions with `DISPATCH_MACRO` = `__host__ __device__`. Each has a
  `DECLARE_DISPATCH` stub with CPU (`REGISTER_ALL_CPU_DISPATCH`), CUDA (`REGISTER_CUDA_DISPATCH` in `*.cu`) and
  sometimes MPS registrations. On CUDA, `gpu_kernel<Arity>` is used for pointwise work and `stencil_kernel` for
  line-wise work (one block per line, shared memory). The rest is plain libtorch tensor ops, which run on any device.
  Switch: CMake `CUDA` (default OFF, `CMakeLists.txt:10`) → `USE_CUDA` (`configure.h.in:10`); the device comes from env
  `DEVICE` (S14.1).
- Derivations: none.
- Figures:
  - A dispatch table: stub → CPU/CUDA/MPS implementation.
  - A CUDA launch geometry sketch: line-per-block `stencil_kernel` vs the tiled variant for lines over 1024 cells.
- Code:
  - stub declarations: `src/hydro/hydro_dispatch.hpp`, `src/recon/recon_dispatch.hpp`,
    `src/riemann/riemann_dispatch.hpp`, `src/implicit/implicit_dispatch.hpp`, `src/eos/eos_dispatch.hpp`,
    `src/coord/coord_dispatch.hpp`, `src/bc/bc_dispatch.hpp`, `src/sedimentation/sed_hydro_dispatch.hpp`,
    `src/utils/utils_dispatch.hpp` (25 stubs).
  - example CPU path: `src/hydro/hydro_dispatch.cpp:14@e894700` `hydro_ref_x1_cpu` (`AT_DISPATCH_FLOATING_TYPES` +
    `at::parallel_for` over columns); the MPS path is a tensor-op reimplementation in the same file.
  - `src/utils/loops.cuh:53@e894700` `gpu_kernel`; `:71` `stencil_kernel` (block = line length).
  - `src/recon/recon_dispatch.cu:18@e894700` `recon_tile_width`, `:47` `stencil_kernel_tiled` (the fix for issue #251).
  - `src/CMakeLists.txt:122-155@e894700` — the `*.cu` glob and the `snapy::snap_cu` library.
- Tests: `tests/test_weno5_cuda_line.cpp` (`test_weno5_cuda_line.release`, CUDA builds only) — lines of 32, 1024, 1025,
  1030 and 1280 cells match CPU, `EXPECT_LT(diff, 1e-12)`. `tests/test_coordinate.cpp` DeviceTest runs on CPU and CUDA,
  float32 and float64. The MPS parameter is commented out (`tests/device_testing.hpp:48`).
- Limits / known issues:
  - `call_cs_interp_LR/BT` have CPU kernels only and no caller: the call is commented out
    (`src/coord/gnomonic_equiangle.cpp:556-563`).
  - `bdot_out` (`src/utils/utils_dispatch.cu:70`) still uses the untiled `stencil_kernel` and has no caller in `src/`.
  - MPS registrations exist but no test runs them.
- Discrepancies: none.


#### 1.10 Tensor layout, variable indices, ghost zones, interior slices
<sub>inventory A: Scheme 1.10: Tensor layout, variable indices, ghost zones, interior slices</sub>

- Summary: every field is `[nvar, nc3, nc2, nc1]` with x1 last (DIM1=3, DIM2=2, DIM3=1). `nc = nx + 2·nghost` when
  nx>1, else 1. Rows are IDN=0, IVX..IVZ=1..3, IPR=4, species from ICY=5. A face array has the cell shape: index i is
  the lower face x1f[i] of cell i. LR states are `[2, nvar, ...]`, where ILT[i] is the state on the left of face i and
  IRT[i] the state on its right. `part(offset, PartOptions)` returns the interior, ghost or extended slabs. Switch: CMake
  `NMASS` (default 0, `cmake/parameters.cmake:3`). NMASS>0 is refused by a static_assert.
- Derivations: none.
- Figures:
  - 1-D index line: ghosts 0..ng-1, interior il..iu, ghosts iu+1..; faces x1f[0..nc1]. Mark which face index holds
    which flux.
  - The `part()` slabs for offsets (-1,0,+1) with exterior=true/false, extend_x2/x3, depth.
- Code:
  - `src/snap.h:34-46@e894700` index enum; `:52` static_assert ICY==IPR+1; `:60` kPrimitive/kConserved/kScalar.
  - `src/coord/coordinate.hpp:59@e894700` `nc1()`; `:169` `il()`; `:171` `iu()`.
  - `src/mesh/meshblock.hpp:105@e894700` `PartOptions`; `src/mesh/meshblock.cpp:284@e894700` `part`.
  - `src/recon/reconstruct.cpp:50@e894700` `_apply_inplace` — cell j writes `IRT[j]` (its lower face) and `ILT[j+1]`.
  - Variables keys: `hydro_w`, `hydro_u`, `scalar_r`, `scalar_s`, `solid`, `fill_solid_hydro_{w,u}`,
    `boundary_reference_{w,r}` (`meshblock.cpp:401-508`).
- Tests: indirect.
- Limits / known issues: a block with nx1=1 stores no x1 ghosts (`nc1()==1`), so x1 stencils fall back to edge forms
  (`tests/test_pref_local_seam.cpp:4-7`).
- Discrepancies: none.


#### 1.11 Options objects and YAML
<sub>inventory A: Scheme 1.11: Options objects and YAML</sub>

- Summary: every option struct uses `ADD_ARG(T,name)` (chainable getter/setter). `from_yaml` readers build the tree.
  `check_keys` refuses an unknown key in 29+ fixed-key blocks. Switch: YAML top-level sections `distribute`,
  `geometry`, `dynamics`, `forcing`, `integration`, `scalar`, `sedimentation`, `boundary-condition`, `outputs`,
  `verbose`. kintera reads `species` and `reference-state`.
- Derivations: none.
- Figures: a YAML-section → reader-function map.
- Code: `src/add_arg.h:9@e894700` `ADD_ARG`; `src/input/check_keys.cpp:12@e894700` `check_keys`;
  `src/layout/layout.cpp:221@e894700` (distribute); `src/coord/coordinate.cpp:62@e894700` (geometry);
  `src/hydro/hydro_options.cpp:15@e894700` (dynamics, `:44`); `src/hydro/register_forcing_modules.cpp:6@e894700`
  (forcing); `src/scalar/scalar_options.cpp:11@e894700`; `src/sedimentation/sed_options.cpp:19@e894700`;
  `src/output/output_type.cpp:64@e894700` (outputs); `src/mesh/meshblock_options.cpp:88-208@e894700`
  (boundary-condition); `src/eos/equation_of_state.cpp:86@e894700` (`kintera::ThermoOptionsImpl::from_yaml`).
- Tests: `tests/test_yaml_keys.cpp` (`test_yaml_keys.release`).
- Limits / known issues: `distribute: backend` is still accepted but dead; the backend comes from env `BACKEND`
  (`layout.cpp:229-231`, PR #242). The top level is not key-checked.
- Discrepancies: none.


#### 1.12 Python package `snapy`
<sub>inventory A: Scheme 1.12: Python package `snapy`</sub>

- Summary: a pybind11 extension built by `setup.py` against the CMake build. It exposes options, Mesh/MeshBlock, layouts,
  `SyncOptions`, `distributed.set_process_group`, `load_restart`. Importing it sets float64 as the default dtype and 1
  torch thread. Switch: none.
- Derivations: none.
- Figures: none.
- Code: `python/csrc/snapy.cpp:32@e894700` module, `:47` `load_restart`; `python/csrc/pymesh.cpp:126@e894700`
  `set_local_horizontal_cells`, `:184` `forward`; `python/csrc/pylayout.cpp:136-141@e894700` `distributed` submodule
  (`set_process_group`); `python/__init__.py` (dtype and thread setup); `pyproject.toml` (`torch==2.10.0`,
  `kintera>=2.5.13`, commux and pinc on Linux, scripts `pd-combine`, `pd-inspect`, `api/pd-run`); stubs under
  `python/snapy/*.pyi`.
- Tests: `tests/test_python_import_path.py` (`test_python_import_path_python`) — the python ctests import the snapy
  build under test when `SNAPY_TEST_PYTHONPATH` is set (`tests/CMakeLists.txt:347-360`).
- Limits / known issues:
  - Without `SNAPY_TEST_PYTHONPATH` the python ctests test the installed snapy, not the tree (CMake warns).
  - `python/exchange.py` uses the `snapy.SlabLayout(px,py,...)` and `DistributeInfo` APIs, which the bindings no longer
    provide (`pylayout.cpp:92` takes `LayoutOptions`). It is stale.
- Discrepancies: none.


#### 1.13 External dependencies (kintera, pyharp, torch, comm and IO libraries)
<sub>inventory A: Scheme 1.13: External dependencies (kintera, pyharp, torch, comm and IO libraries)</sub>

- Summary: kintera supplies the thermodynamics (`ThermoY` saturation adjustment, species tables), constants, and tensor
  (de)serialisation for restart. pyharp supplies the time integrator (`harp::Integrator`) and radiation. pydisort is
  imported by `python/__init__.py`. commux supplies UCX, pinc supplies PnetCDF, NetCDF is a system library. Switch: CMake
  `find_package(Kintera 2.5.13 REQUIRED)` (`CMakeLists.txt:101`), `find_package(Harp REQUIRED)` (`:96`); UCX via commux
  (`cmake/ucx.cmake`), PnetCDF via pinc (`cmake/parameters.cmake:28-43`).
- Derivations: none.
- Figures: dependency graph.
- Code: `src/mesh/meshblock.hpp:17@e894700` (`harp/integrator/integrator.hpp`); `src/mesh/meshblock.cpp:231@e894700`;
  `src/mesh/meshblock.cpp:808-813@e894700` (`kintera::ThermoYImpl`); `src/output/restart.cpp:90@e894700`
  (`kintera::save_tensors`); `src/input/read_restart_file.cpp:223@e894700` (`kintera::load_tensors`).
- Tests: none specific.
- Limits / known issues: the integrator stage weights and `stop()` live in pyharp and cannot be cited at a snapy line.
  `CMakeLists.txt:97-100` records why the kintera floor is 2.5.13 (saturation-failure counter, kintera #131).
- Discrepancies: none.


---

<a id="ch2"></a>
## Chapter 2. Governing equations and thermodynamics

The conservation laws snapy integrates and the order of operators in a stage; the equation-of-state interface and its types (ideal gas, ideal-moist, kintera moist mixture, ANEOS stubs, shallow water); the consistency conditions between the EOS and the solver; the thermodynamic side of saturation adjustment. The floors are owned by chapter 8 (the EOS limiter entry there merges the two inventories' views). H2 dissociation is not in kintera at the pin and is not claimed (ISSUES.md item 4).

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: the conservation laws snapy integrates (variables, flux and source terms, operator ordering inside a step), the
`EquationOfState` interface and its five concrete types (ideal-gas, ideal-moist, moist-mixture, aneos, shallow-water),
the kintera thermodynamics behind the moist types (reference energies, NASA-9/H2 heat capacities, inversions,
saturation adjustment), species energies/enthalpies, the conserved/primitive limiter (floors), and the consistency
conditions the hydro solver relies on (`UT->I` = `W->I`, round trips, species-enthalpy sum, own dry gas).

Merge/split recommendation: **split**. (a) Keep in Ch. 2: governing equations, EOS interface and the five EOS types,
kintera thermo and the consistency conditions. (b) Move the species half of `apply_conserved_limiter_`
(parent-vapour borrow, column `fix_vapor`, parentless-cloud repair, limiter marks) and the saturation adjustment's
place in the step to Ch. 10, which owns condensate conservation and `check_redo`; leave only the density/temperature
floors here. (c) ANEOS and shallow-water need only short sections. ANEOS ships as a stub whose real thermo comes from an
external library through weak symbols, and it is incompatible with several solver paths (see below). (d) H2
dissociation (source report) is **not in kintera at the pinned sha** and must be dropped or marked as future work
(see Discrepancies).

</details>


#### 2.1 Conservation laws and operator ordering in one RK stage
<sub>inventory B: Scheme: Conservation laws and operator ordering in one RK stage</sub>

- Summary: dry mass, species partial densities, covariant momentum and total energy are advanced by an SSP-RK
  integrator. Each stage applies flux divergence, then forcings, then (implicit x1 correction), then the RK average,
  the conserved limiter, and on the last stage the saturation adjustment, the gravity-work fixer and the boundary
  fill. Switch: none; the stage count comes from the pyharp integrator.
- Derivations:
  - Semi-discrete equations for `[rho_d, m, E, rho_i]` with gravity, Coriolis and diffusion sources; total mass
    `rho_d + sum rho_i`. re-derive from `src/hydro/hydro_forward.cpp:763-774` and `src/mesh/meshblock.cpp:597-842`.
  - Why the saturation adjustment and the boundary fill must come in this order (stale wall ghosts after the
    adjustment leak energy and water). PR #206 states only the result (`sources/gh__PR_BODIES_202-219.md` §PR #206);
    re-derive from `src/mesh/meshblock.cpp:795-841`.
- Figures:
  - Flow chart of one RK3 stage: flux → positivity → forcings → VIC → RK average → limiter → (last stage) saturation
    adjustment → fixer → boundary fill.
  - Table/diagram of the conserved vs primitive rows (dry density vs total density; covariant vs contravariant).
- Code:
  - `src/mesh/meshblock.cpp:597` — `MeshBlockImpl::advance_local` — stage driver; (1) save `_hydro_u0`, reset limiter marks and drain saturation failures at stage 0 (`:620-621`).
  - `src/mesh/meshblock.cpp:756` — `apply_conserved_limiter_(hydro_u, whole_column=true)` after the RK average.
  - `src/mesh/meshblock.cpp:795` — step (6) saturation adjustment, last stage only (details in Ch. 10).
  - `src/mesh/meshblock.cpp:841` — `apply_boundaries` after the adjustment (PR #206 ordering).
  - `src/hydro/hydro_forward.cpp:768` — `peos->compute("W->T")` passed to every forcing; `:773` forcing loop.
  - `src/snap.h:34` — index enum (new layout); `src/snap.h:52` — static_assert refusing `NMASS>0`.
- Tests:
  - `tests/test_wall_saturation.cpp` (`test_wall_saturation.release`) — closed 32-cell moist column with condensation/evaporation at each wall: phase change occurs and relative energy and total-water errors < 1e-12 (`:73-74`); PR #206 measured ~1e-14 after the fix and 6e-6–1e-5 before.
- Limits / known issues:
  - `NMASS>0` is unsupported (static_assert; PR #223 Limits says the implicit solver also assumes 5 hydro rows).
- Discrepancies: none.


#### 2.2 EquationOfState interface, options and type dispatch
<sub>inventory B: Scheme: EquationOfState interface, options and type dispatch</sub>

- Summary: abstract `EquationOfStateImpl` with string-keyed conversions (`W->U`, `U->W`, `W->I`, `W->T`, `W->A`,
  `WA->L`, `UT->I`, `U->K`, `W->E`, and `W->L`/`WL->A` for aneos), plus `species_weight`, `species_cv_ref`,
  `specific_heat_cv`, `internal_energy_offset`, `species_enthalpy`. Switch: YAML `dynamics/equation-of-state/type`
  ∈ {ideal-gas, ideal-moist, moist-mixture, aneos, shallow-water}, default `moist-mixture`
  (`src/eos/equation_of_state.cpp:57`). Other keys: `gammad` (1.4), `weight` (29e-3), `density-floor` (1e-6),
  `pressure-floor` (1e-3), `temperature-floor` (20), `limiter` (false), `eos-file` (""), `verbose`; kintera keys
  `max-iter` (10), `ftol` (1e-6), `uv-solver` ("auto") read by kintera (`kintera src/thermo/thermo_options.cpp:91`,
  `:98`, `:105@4dc613d`). Unknown keys are refused (`check_keys`, `src/eos/equation_of_state.cpp:50`).
- Derivations: none (interface).
- Figures:
  - Class diagram: `EquationOfStateImpl` → five concrete types; the moist types hold a kintera `ThermoY` registered as `hydro.eos.thermo`.
  - Table of conversion keys × EOS type (which keys each type implements).
- Code:
  - `src/eos/equation_of_state.hpp:20` — `EquationOfStateOptionsImpl`; defaults `:45-54`.
  - `src/eos/equation_of_state.cpp:33` — `EquationOfStateOptionsImpl::from_yaml`; `:86` loads `kintera::ThermoOptionsImpl::from_yaml`; `:90` NMASS species-count check.
  - `src/eos/equation_of_state.cpp:356` — `EquationOfStateImpl::create` — type dispatch (`:362-370`).
  - `src/eos/equation_of_state.cpp:165` — base `internal_energy_offset` (zero).
- Tests:
  - `tests/test_eos.cpp` (`test_eos.release`) — see the per-type schemes.
  - `tests/test_hydro_options.cpp` (`test_hydro_options.release`) — `reject_unknown_dynamics_keys` (PR #211/#227).
- Limits / known issues:
  - `temperature-floor` is not validated positive/finite (PR #219 Limits; `src/eos/equation_of_state.cpp:72`).
  - With the default type `moist-mixture`, a card without a species/thermo block fails in `MoistMixtureImpl::reset` (`src/eos/moist_mixture.cpp:19`).
- Discrepancies:
  - Floor defaults differ between the C++ options struct and YAML: `density_floor` 1e-10 and `pressure_floor` 1e-10 in `src/eos/equation_of_state.hpp:49-50`, but 1e-6 and 1e-3 from `from_yaml` (`src/eos/equation_of_state.cpp:65`, `:71`). Options built in code or Python get the struct defaults.
  - For ideal-moist and moist-mixture, `gammad` and `weight` from YAML are overwritten from the thermo (`src/eos/ideal_moist.cpp:23-24`, `src/eos/moist_mixture.cpp:23-24`). The YAML values are silently ignored.


#### 2.3 Ideal gas EOS
<sub>inventory B: Scheme: Ideal gas EOS</sub>

- Summary: `p = (gamma-1) rho e`, `T = p/(rho R_d)`, `c = sqrt(gamma p/rho)`, with a fused cons→prim kernel (CPU
  TensorIterator, MPS tensor path). Switch: `type: ideal-gas`.
- Derivations:
  - Trivial closed form, including the covariant/contravariant KE `0.5 v^i m_i`. re-derive from `src/eos/ideal_gas.cpp:67-118` and `src/eos/ideal_gas_impl.h:16`.
- Figures:
  - One cell: conserved → primitive arrows with the metric raise (`cosine_cell_kj`) on the horizontal momenta.
- Code:
  - `src/eos/ideal_gas.cpp:30` — `IdealGasImpl::compute`.
  - `src/eos/ideal_gas.cpp:90` — `_cons2prim` → `at::native::ideal_gas_cons2prim`.
  - `src/eos/ideal_gas_impl.h:16` — `ideal_gas_cons2prim` kernel.
  - `src/eos/eos_dispatch.cpp:21` (CPU), `:41` (MPS) — dispatch.
  - `src/eos/ideal_gas.cpp:115` — `_temp2intEng` (`rho cv T`, no offset).
- Tests:
  - `tests/test_eos.cpp:193` `ideal_gas_internal_energy_offset_is_zero` — offset is 0 (tol 1e-12).
  - `tests/test_eos.cpp:246` `prim2cons_hydro_ideal_ncloud5` — round trip of a 14-variable state, 1e-9 (f64) / 1e-2 (f32), tolerances set in the test.
- Limits / known issues: none found.
- Discrepancies: none.


#### 2.4 Ideal-moist EOS (constant heat capacities, zero-volume condensates, reference energies)
<sub>inventory B: Scheme: Ideal-moist EOS (constant heat capacities, zero-volume condensates, reference energies)</sub>

- Summary: `p = (gamma_d - 1)(E - KE - sum_k rho_k u0_k) f_eps/f_sig`, with
  `f_eps = 1 + sum_vap y_i (mu_d/mu_i - 1) - sum_cloud y_j` and `f_sig = 1 + sum_i y_i (cv_i/cv_d - 1)` (Li 2019
  eqs. 16-17 per the header), `T = p/(rho R_d f_eps)`, `gamma = 1 + (gamma_d-1) f_eps/f_sig`. Reference energies
  `u0_k = uref_R_k R_k` give latent heats. Switch: `type: ideal-moist` (needs a kintera thermo block).
- Derivations:
  - f_eps/f_sig and the pressure/internal-energy relations for a mixture with zero-volume condensates. re-derive from `src/eos/ideal_moist.cpp:164-225`, `:319-346` (no step-by-step derivation in sources; the header only cites "Li2019").
  - Adiabatic index of the mixture. re-derive from `src/eos/ideal_moist.cpp:113-121`.
  - Species energy `rho_i (u0_i + cv_i T + KE)` and species enthalpy (`+R_i T` for vapours only). re-derive from `src/eos/ideal_moist.cpp:235-280`.
- Figures:
  - Bar chart of one cell's energy split: dry `rho_d u0_d`, per-species `rho_i u0_i`, thermal `rho cv T`, kinetic.
  - Schematic: a condensate carries mass and heat capacity but no volume and no pressure share (no `R_j T` term).
- Code:
  - `src/eos/ideal_moist.cpp:18` — `IdealMoistImpl::reset` — buffers `inv_mu_ratio_m1`, `cv_ratio_m1`, `u0` (`:30-51`).
  - `src/eos/ideal_moist.cpp:70` — `internal_energy_offset`.
  - `src/eos/ideal_moist.cpp:164` — `_cons2prim`; `:207` `_prim2intEng`; `:227` `_prim2temp`.
  - `src/eos/ideal_moist.cpp:260` — `species_enthalpy`.
  - `src/eos/ideal_moist.cpp:293` — `_temp2intEng` (see the consistency scheme).
  - `src/eos/ideal_moist.cpp:319` — `f_eps`; `:334` `f_sig`.
- Tests:
  - `tests/test_eos.cpp:168` `ideal_moist_internal_energy_offset` — offset equals `sum rho_k u0_k`, 1e-6.
  - `tests/test_eos_temp2inteng.py` (`test_eos_temp2inteng_python`) — see the consistency scheme.
  - `tests/test_eos_species_registry.py` (`test_eos_species_registry_python`) — `W->T`, `UT->I`, `W->E` and one step unchanged after kintera's global species tables are rewritten; TOL 1e-14 (`:28`).
- Limits / known issues:
  - "TODO(cli) iteration needed" comments at `src/eos/ideal_moist.cpp:200` and `:216`. With constant cv the closed form is exact, so the TODO matters only if cv becomes T-dependent.
  - `src/eos/ideal_moist_impl.h:35` (`ideal_moist_cons2prim`) is dead: its dispatcher is commented out (`src/eos/eos_dispatch.cpp:60-77`), and it lacks the metric raise and the offsets.
- Discrepancies: none.


#### 2.5 Moist-mixture EOS (kintera-backed)
<sub>inventory B: Scheme: Moist-mixture EOS (kintera-backed)</sub>

- Summary: every thermodynamic quantity is delegated to kintera `ThermoY`: `DY->V` (partial densities),
  `VU->T` (Newton), `VT->P`, `PV->T` (Newton), `VT->U`, `VT->cv`. The adiabatic index is `sum c_n cp_n / sum c_n cv_n`.
  The sound speed is `sqrt(gamma) * c_T`, where `c_T^2 = (R T/rho) sum_gas c_n (z_n + c_n dz_n/dc_n)`. `(ivol, temp)`
  are cached, keyed on tensor identity plus the ATen version counter. Switch: `type: moist-mixture` (default).
  Opt-in kintera heat capacities: `reference-state/use-nasa9-cp`, `use-h2-cp`, `h2-cp-mode`
  (`kintera src/species.hpp:110`, `:118`, `:121@4dc613d`).
- Derivations:
  - Isothermal and adiabatic sound speed for a mixture with compressibility `z(T,c)`. re-derive from `src/eos/moist_mixture.cpp:245-272`.
  - Newton for `VU->T` and `PV->T`, and the sign/damping argument (`(cp-cv) c >= f'`). The kintera comment states the Mayer relation only; re-derive from `kintera src/thermo/thermo_y.cpp:423-467`, `:477-510@4dc613d`.
  - Per-species flux enthalpy `u_n + z_n R_n T (+KE)`, summing to `U + p + rho KE`. PR #269 states the result; re-derive from `src/eos/moist_mixture.cpp:196-218`.
  - NASA-9 internal energy referenced to T0 = 300 K, and the H2 rigid-rotor partition function. The physics (but not the code at the pin) is summarised in `sources/canoe__H2_DISSOCIATION_EOS_TECH_REPORT.md` §4; re-derive from `kintera src/thermo/eval_uhs.cpp:65-150`, `:266-300@4dc613d`.
- Figures:
  - Call graph snapy `compute(...)` → kintera `ThermoY::compute` keys → `eval_*_R` hooks.
  - Cache validity diagram: prim tensor identity + `_version()` → reuse `(ivol, temp)`; any in-place write invalidates.
  - cp/R(T) for H2 in equilibrium vs normal mode, regenerated from kintera on the pinned sha.
- Code:
  - `src/eos/moist_mixture.cpp:18` — `MoistMixtureImpl::reset`.
  - `src/eos/moist_mixture.cpp:124` — `_cons2prim` (`DY->V`, `VU->T`, `VT->P`, `:149-151`).
  - `src/eos/moist_mixture.cpp:164` — `_prim2intEng` (`VT->U`).
  - `src/eos/moist_mixture.cpp:196` — `species_enthalpy`.
  - `src/eos/moist_mixture.cpp:232` — `_temp2intEng` (`VT->U` on conserved partial densities).
  - `src/eos/moist_mixture.cpp:245` — `_adiabatic_index`; `:256` `_isothermal_sound_speed`.
  - `src/eos/moist_mixture.cpp:284` — `_ensure_cache`.
  - `kintera src/thermo/thermo_y.cpp:162@4dc613d` — `ThermoYImpl::compute` (keys `DY->V` :196, `PV->T` :212, `VT->cv` :218, `VT->U` :224, `VU->T` :230, `VT->P` :236).
  - `kintera src/thermo/thermo_y.cpp:423@4dc613d` — `_pres_to_temp` (Newton, subtractive step at :447); `:477` `_intEng_to_temp` (:490).
  - `kintera src/thermo/eval_uhs.cpp:153, :190, :223, :245, :266@4dc613d` — `eval_cv_R`, `eval_cp_R`, `eval_czh`, `eval_czh_ddC`, `eval_intEng_R`; `:95` `eval_h2cp`.
  - `kintera src/thermo/thermo.hpp:80-87@4dc613d` — `max_iter` 10, `ftol` 1e-6, `gas_floor` 1e-20, `uv_solver` "auto".
  - `kintera src/species.cpp:216@4dc613d` — `check_reference_state` (allowed keys `Tref`, `Pref`, `use-nasa9-cp`, `use-h2-cp`, `h2-cp-mode`).
- Tests:
  - `tests/test_eos.cpp:122` `moist_mixture` — cons→prim→cons round trip 1e-6; `W->A` = 1.4 for the test card, 1e-6; the cache is invalidated by an in-place pressure write and refreshed for an equal distinct tensor (1e-6).
  - `tests/test_flux_positivity_carry.cpp:381` `moist_mixture_nasa9_h2_enthalpy_matches_internal_plus_pressure` — species enthalpy sum vs `U + p`, rel. 1e-9 (`:458`; measured residual ~1e-16, comment `:456`).
  - `tests/test_flux_positivity_carry.cpp:354` `moist_mixture_withheld_mass_keeps_its_energy_and_momentum` (+ `_cuda` `:364`).
- Limits / known issues:
  - kintera's `func2` registry (`czh`, `intEng_R_extra`) is empty, so `z = 1` everywhere. Non-ideal `z` is parked (issue #276, `sources/gh__ISSUE_THREADS_251-294.md`).
  - `use-nasa9-cp` affects cp/cv/u but not entropy; do not combine it with condensation of a NASA-9 vapour (`kintera src/species.hpp:104-110@4dc613d`).
  - Newton inversions warn and continue at `max_iter` (`kintera src/thermo/thermo_y.cpp:454`, `:497@4dc613d`), with no failure count.
- Discrepancies:
  - The header comment `src/eos/moist_mixture.hpp:43-54` still demands a call order ("W->A must follow W->U or W->I"), but `_ensure_cache` (`src/eos/moist_mixture.cpp:284`) recomputes on any mismatch, so the order is no longer required. The comment is stale; the code wins.
  - **H2 dissociation** (`sources/canoe__H2_DISSOCIATION_EOS_TECH_REPORT.md`): `use-h2-dissociation`, `fused-h2diss`, `h2_dissociation.hpp` and the lumped-species thermo are **absent** at `kintera 4dc613d`. `check_reference_state` accepts no such key (`kintera src/species.cpp:217-218@4dc613d`); the only trace is the comment `kintera src/thermo/thermo_y.cpp:445@4dc613d`. The report's commits (`83e30f1`, `fdc38e9`) are not objects in the kintera clone. Per ISSUES.md item 4, the deck citation goes too. The chapter can state the PV->T Newton sign fix (present) and must not claim the dissociation EOS ships.


#### 2.6 ANEOS (tabulated EOS through an external library)
<sub>inventory B: Scheme: ANEOS (tabulated EOS through an external library)</sub>

- Summary: density/energy ↔ pressure/temperature/sound speed through an `ANEOSThermo` module. The tree ships only
  weak-symbol stubs that throw; a real implementation must be linked in. Conversions are `W->L` and `WL->A` (no
  `W->A`/`WA->L`). Switch: `type: aneos`, `eos-file` (table path).
- Derivations: none in sources. Document only the interface: `gamma = c^2 rho/p` (`src/eos/aneos.cpp:40-45`).
- Figures: none needed (one table of supported keys).
- Code:
  - `src/eos/aneos.cpp:12` — `ANEOSImpl::compute`; `:71` `_cons2prim` (`DU->PTL`); `:94` `_prim2intEng` (`DP->TUL`).
  - `src/eos/aneos/aneos_thermo_dummy.cpp:14-32` — weak stubs that throw "not implemented".
  - `src/riemann/hllc.cpp:38`, `src/riemann/lmars.cpp:38`, `src/hydro/hydro.cpp:296`, `:411` — aneos branches.
- Tests: none (PR #216 Limits: "No test or example card uses aneos with LMARS").
- Limits / known issues:
  - Unusable without an external `ANEOSThermoImpl`.
  - Incompatible with paths that call `W->A` unconditionally: `src/riemann/roe.cpp:32-33`, the radiating BC `src/bc/bc_func.cpp:143`, `src/hydro/hydro.cpp:448`/`:468`.
  - No metric lowering/raising of momenta (`src/eos/aneos.cpp:51-92`), no species, and `specific_heat_cv` falls back to the base class (zeros), so conduction is refused (`src/forcing/diffusion.cpp:343`) and `body-heat` would add zero.
- Discrepancies: none beyond the above.


#### 2.7 Shallow-water EOS
<sub>inventory B: Scheme: Shallow-water EOS</sub>

- Summary: `nvar = 4` (h, m); `WA->L` returns `sqrt(h)` (gravity folded into h); `W->T` and `W->A` return undefined
  tensors. Switch: `type: shallow-water`.
- Derivations: none needed (cross-ref the shallow-water test chapter).
- Figures: none.
- Code: `src/eos/shallow_water.cpp:14` — `ShallowWaterImpl::compute`; `:38` `_cons2prim`.
- Tests: `tests/run_shallow_xy.cmake`, `tests/run_shallow_splash.cmake` (`test_shallow_xy`, `test_shallow_splash`, only with `FULL_TESTS`, `tests/CMakeLists.txt:365-369`).
- Limits / known issues: forcings receive an undefined `temp` (`src/hydro/hydro_forward.cpp:768`); only forcings that ignore temp are usable.
- Discrepancies: none.


#### 2.8 EOS ↔ solver consistency conditions (temp2inteng and friends)
<sub>inventory B: Scheme: EOS ↔ solver consistency conditions (temp2inteng and friends)</sub>

- Summary: the conditions the solver relies on:
  (i) `UT->I(u, T(w)) == W->I(w)`: the offset is added (not scaled by T) and the dry channel `rho_d cv_d T` is included;
  (ii) `W->U ∘ U->W` is the identity;
  (iii) `sum_n rho_n h_n = U + p + rho KE` for the species-enthalpy carry;
  (iv) the EOS uses its own dry gas, not kintera's process-global tables;
  (v) the vapour+cloud count matches `NMASS` when `NMASS>0`.
  Switch: none.
- Derivations:
  - (i) affine structure `ie(T) = offset + (rho_d cv_d + sum rho_i cv_i) T`. PR #219 states the result only; re-derive from `src/eos/ideal_moist.cpp:293-317` and `src/eos/moist_mixture.cpp:232-243`.
  - (iii) re-derive from `src/eos/ideal_moist.cpp:260-280` and `src/eos/moist_mixture.cpp:196-218`.
- Figures:
  - ie(T) line for one state: slope = volumetric cv (dry channel highlighted), intercept = `sum rho_k u0_k`; the pre-#219 wrong line for comparison.
- Code:
  - `src/eos/ideal_moist.cpp:293` — `IdealMoistImpl::_temp2intEng`.
  - `src/eos/moist_mixture.cpp:232` — `MoistMixtureImpl::_temp2intEng`.
  - `src/eos/equation_of_state.cpp:232` — sole consumer (temperature floor).
  - `src/eos/equation_of_state.cpp:110` — `cache_cloud_parents_` reads `thermo->names()/mu()` (own table, #234).
  - `src/sedimentation/sed_hydro.cpp:97-99` — fused sedimentation reads the EOS's own `weight()`/`cref_R` (#223).
- Tests:
  - `tests/test_eos_temp2inteng.py` (`test_eos_temp2inteng_python`) — round trip at 50–400 K, rtol 1e-12 (`:80`, `:106`); affinity curvature ≤ 1e-12 (`:129`); intercept = offset, 1e-10 (`:151`). Pre-fix failure 58–1597 relative (PR #219). Covers **ideal-moist only** (`:44`); registered on CPU only (PR #219 Limits).
  - `tests/test_eos_species_registry.py` (`test_eos_species_registry_python`) — TOL 1e-14.
  - `tests/test_two_cards_species.cpp` (`test_two_cards_species.release`) — limiter split and sedvel names after a second card; 1e-10 (f64) / 1e-4 (f32) (`:84`).
  - `tests/test_eos.cpp:122` — round trip (ii).
- Limits / known issues:
  - No `UT->I` vs `W->I` test for moist-mixture: its `_temp2intEng` reuses `VT->U`, so it holds by construction, but this is not pinned.
- Discrepancies: none.


#### 2.9 Saturation adjustment (kintera UV equilibrium) — thermodynamic side
<sub>inventory B: Scheme: Saturation adjustment (kintera UV equilibrium) — thermodynamic side</sub>

- Summary: at fixed `rho` and internal energy `ie = E - KE`, kintera `ThermoY::forward` solves the isochoric-isoenergetic
  phase equilibrium of the nucleation reactions (KKT/partition solver, warm-started active set) and rewrites the mass
  fractions in place. It counts failures (`diag < 0`) per device. Switch: runs when the thermo has reactions
  (`src/mesh/meshblock.cpp:796-797`); kintera `max-iter`, `ftol`, `uv-solver` ∈ {auto, kkt, partition}.
- Derivations:
  - UV-equilibrium conditions and the KKT system. The manuscript cited by the evaporation report is not in sources; re-derive from `kintera src/thermo/equilibrate_uv.h:285@4dc613d` and `kintera src/thermo/thermo_y.cpp:259-367@4dc613d`.
- Figures:
  - T–q diagram: before/after adjustment at constant U and V, with the saturation curve.
- Code:
  - `kintera src/thermo/thermo_y.cpp:259@4dc613d` — `ThermoYImpl::forward`; failure count `:348-358`; `:369` `take_saturation_adjustment_failures`.
  - `kintera src/thermo/equilibrate_uv.h:285@4dc613d` — `equilibrate_uv`; diag `= -(100*status+iter)` `:587`.
  - snapy call site and redo coupling: Ch. 10.
- Tests: `tests/test_check_redo_saturation.py` (Ch. 10).
- Limits / known issues:
  - The partition solver requires disjoint vapour–cloud reactions, otherwise kkt (`kintera src/thermo/thermo_y.cpp:326-328@4dc613d`).
  - `equilibrate_tp` once stopped at max-iter 5 (issue #270, fixed by kintera #138 and the example max-iter raised to 10).
- Discrepancies: none.


---

<a id="ch3"></a>
## Chapter 3. Grids and geometry

Coordinate systems and their metric (Cartesian, spherical-polar, gnomonic cubed sphere), the curved-grid helpers, how the global grid is cut into blocks, and what a ghost cell contains at each seam type. The transport of ghosts (buffers, tags, backends) is chapter 14.A; only what the ghost values are is here.

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: coordinate systems (Cartesian, spherical-polar, gnomonic equiangular cubed sphere), the metric quantities the FV
update uses (face areas, volumes, centroids, widths, geometric sources, local-frame projections), how the global grid is
cut into blocks (layouts, rank maps, connectivity), and what a ghost cell contains at each seam type (panel edges, x1
seams between blocks, corners). Recommendation: keep geometry and decomposition together. Leave the transport of
ghosts (buffers, tags, backends) to Ch14 and keep here only what the ghost values ARE. The radial face moments and the
x1 centroid belong to both this chapter and the #289/WB chapters: put the geometric identities here and the flux use
there. A short subsection should say that `cylindrical` is a registered but empty type (S3.15).

</details>


#### 3.1 One global grid, sliced per block (decomposition-invariant faces)
<sub>inventory A: Scheme 3.1: One global grid, sliced per block (decomposition-invariant faces)</sub>

- Summary: each block's faces are a slice of ONE global `linspace` per axis, and cell widths come from the global
  `(gmax-gmin)/gnx`. A face therefore has the same double in every block and every decomposition (PR #222).
  `resolve_global_grid` adopts the block as the global grid when none was declared, and otherwise checks that the block
  is exactly nx cells of it. Switch: YAML `geometry: {type, bounds, cells:{nx1,nx2,nx3,nghost,interp_order}}`. Defaults:
  type cartesian (`coordinate.hpp:97`), nghost 1 (`:116`), interp_order 2 (`:117`); global_nxN=0 means "no global grid".
- Derivations: none needed (a design invariant). The rationale is the comment at `src/coord/coordinate.cpp:291-298@e894700`
  and PR #222 (`gh__PR_BODIES_220-226.md:190`): 1 ULP made 15/71 faces inconsistent and 26 differ between decompositions.
- Figures:
  - One global face array with nb2=2 and nb2=3 slices marked, plus the ghost extension past gmin/gmax.
  - A "before" panel where per-block linspace gives two values of one shared face (1 ULP).
- Code: `src/coord/coordinate.cpp:62@e894700` `CoordinateOptionsImpl::from_yaml` (`:118` bounds-only card = one cell
  per axis; `:143` nx%nb divisibility; `:182` repartition); `:186` `_resolve_axis` (16·eps tolerance, exact cell
  count); `:226` `resolve_global_grid`; `:235` `repartition` (block bounds from loc_of; cubed-sphere forces lx1=0);
  `:283` constructor (faces sliced); `:307` `block_faces_`; `src/coord/coordinate.hpp:76@e894700` `dx1()` (global
  width); `:93` `ix1()` (rounded offset).
- Tests: `tests/test_coordinate.cpp` (`test_coordinate.release`) —
  `CoordinateDecomposition.blocks_match_the_undecomposed_grid_bitwise` (`torch::equal`, nb2=2,3), several
  `CoordinateProgrammatic.*` cases (bounds-only card, refused out-of-grid block, degenerate axis);
  `tests/test_local_horizontal_cells.py` (`test_local_horizontal_cells_python`, faces within 1e-12·dx).
- Limits / known issues:
  - The nghost-vs-nx checks at `coordinate.cpp:166-178` read `op->nx1()` before `repartition` sets it (default 1), so
    they never fire (dead check, read from code).
  - `reset_coordinates` with a mesh generator rebuilds faces from the BLOCK bounds (`coordinate.cpp:326-349`), outside
    the global-slice invariant.
- Discrepancies: the PR #222 text says interp_order 4 is refused at construction. The code refuses anything except 2
  twice (`gnomonic_equiangle.cpp:25` `== 2`, `:182` `<= 2`), so the second check is redundant.


#### 3.2 Cartesian metric
<sub>inventory A: Scheme 3.2: Cartesian metric</sub>

- Summary: uniform widths from the global dx. Areas are products of widths, volume the triple product, centroid =
  midpoint, cos θ=0. Switch: `geometry.type: cartesian`.
- Derivations: trivial. Note "re-derive from `src/coord/coordinate.cpp:425-439@e894700`" for completeness.
- Figures: a cell with face areas A1=dx2·dx3 etc.
- Code: `src/coord/cartesian.cpp:8@e894700` `CartesianImpl::reset`; `src/coord/coordinate.cpp:425@e894700`
  `face_area1`, `:429`, `:433`, `:437` `cell_volume`, `:509` `divergence`, `:585` `forward` (pure divergence).
- Tests: `test_coordinate.release` `CoordinateProgrammatic.cell_volume_is_the_product_of_the_callers_widths`.
- Limits / known issues: none.
- Discrepancies: none.


#### 3.3 Spherical-polar metric and geometric sources
<sub>inventory A: Scheme 3.3: Spherical-polar metric and geometric sources</sub>

- Summary: (r,θ,φ). x1v is the r²-volume centroid and x2v the sinθ centroid. A1 = r²|Δcosθ|Δφ, A2 = ½Δ(r²)sinθΔφ,
  A3 = ½Δ(r²)Δθ, V = Δ(r³)/3·|Δcosθ|·Δφ. Geometric sources use coord_src{1,2}_i and coord_src{1,2,3}_j. The x1
  pressure source uses the face pressures, or under SNAP_X1_CENTROID_EXACT the quintic r-moment. Switch:
  `geometry.type: spherical-polar` (x2 must lie in [0,π], `spherical_polar.cpp:46`).
- Derivations:
  - Centroids, areas, volume, source coefficients: re-derive from `src/coord/spherical_polar.cpp:17@e894700`,
    `:42`, `:178-211`. The test compares them to Athena++ reference formulas but gives no derivation.
  - Face-pressure form of the radial source: re-derive from `src/coord/spherical_polar.cpp:265-277@e894700`.
  - r² cell-to-face maps and the quintic pressure source: exists: docs/derivations/x1-centroid-spherical.md@e894700
    (also sources/deriv__x1-centroid-spherical.md).
- Figures:
  - A spherical shell cell showing r_v (volume centroid) vs the midpoint vs the area centroid r_c.
  - Where coord_src1_i/2_i act (radial momentum source vs angular-momentum flux terms).
- Code: `src/coord/spherical_polar.cpp:17@e894700` `radial_centers`; `:23` `polar_centers`; `:42` `reset`; `:89`
  `coord_src1_i`; `:178` `face_area1`; `:185` `face_area2`; `:193` `face_area3`; `:200` `cell_volume`; `:213`
  `face_moment2_x1`; `:219` `face_centroid_shift_x1`; `:224` `forward` (sources).
- Tests: `test_coordinate.release` `SphericalPolar.geometry_matches_athena_reference_formulas` (allclose 1e-12/1e-12
  on x1v, x2v, areas, volume, coord_src*); `DeviceTest.radial_source_uses_face_pressure_in_x1_momentum`,
  `radial_source_preserves_face_pressure_gradient`; `tests/test_x1_centroid_rest.py` (`test_x1_centroid_rest_python`).
- Limits / known issues: the docs/derivations line citations of spherical_polar.cpp predate dae902b (see S3.5
  discrepancy).
- Discrepancies: none beyond S3.5.


#### 3.4 Gnomonic equiangular cubed sphere (geometry and metric)
<sub>inventory A: Scheme 3.4: Gnomonic equiangular cubed sphere (geometry and metric)</sub>

- Summary: (r,α,β), α and β in [-π/4,π/4] per panel, x=tanα, y=tanβ, C=√(1+x²), D=√(1+y²). cos θ = -xy/(CD) and
  sin θ = √(1+x²+y²)/(CD) at cells and faces (g23 = cos θ). The face transverse widths are great-circle angles
  (`dx2f_ang_*`, acos formula). The x1-face area is r² × the exact cell solid angle (corner sum of
  atan(xy/√(1+x²+y²))), and the volume is the exact Δ(r³)/3 × that solid angle. A2 = (x1v·dx1f)·arc. Geometric sources
  come from `x_ov_rD_kji`/`y_ov_rC_kji` (face-area difference × sin θ / V) plus the curvature terms. Riemann problems
  run in a local orthonormal frame (`prim2local*_` / `flux2global*_`). Lon/lat buffers are kept for output. Switch:
  `geometry.type: gnomonic-equiangle`; `nx2==nx3` required (`gnomonic_equiangle.cpp:22`); interp_order must be 2
  (`:25`).
- Derivations:
  - Metric, Christoffel/source terms, FV lengths/areas/volumes, orthonormal projection: partial.
    `src/coord/cubed_sphere6.nb@e894700` is a Mathematica notebook with sections "Christoffel symbols", "Metric terms
    (flux form)", "Finite volume (length, area, volume)", "Orthonormal projection" and "Ghost zone Interpolation". It is
    symbolic, not a prose derivation, and not in sources/ or docs/derivations. Re-derive in prose from
    `src/coord/gnomonic_equiangle.cpp:18@e894700` (reset) and `:415@e894700` (forward), and check against the notebook.
  - Exact solid angle of a gnomonic cell (corner-sum formula, six panels sum to 4π): re-derive from
    `src/coord/gnomonic_equiangle.cpp:124-137@e894700`.
  - Cubed-sphere face measure w(r)=r, and A2 = ∫r dr × angle: exists: docs/derivations/289-covariance-x3-curved.md@e894700
    §1.3(c).
  - Contravariant↔spherical↔Cartesian velocity transforms: re-derive from `src/coord/gnomonic_equiangle.h:79@e894700`
    (`gnomonic_contra_to_sph`) and `:105` (`gnomonic_sph_to_contra`). Doxygen formulas exist in
    `src/coord/cubed_sphere_utils.hpp` (basis vectors, partial).
  - Covariant/contravariant lowering (`coord_vec_lower_`, g23 = cos θ): re-derive from
    `src/coord/coord_utils.cpp:12@e894700`.
- Figures:
  - The cube net with face ids 0..5 (+X,+Y,-X,+Z,-Y,-Z) and local (α,β) axes per panel (from the ASCII art at
    `cubed_sphere_layout.cpp:156-237`).
  - One gnomonic cell: non-orthogonal axes at angle θ, arc widths, the solid-angle corner sum.
  - cos θ over a panel (zero at the centre and the centre lines, -1/2 at corners). This is why covariance errors hide at
    panel centres (forcing_io report).
- Code: `src/coord/gnomonic_equiangle.cpp:18@e894700` `reset` (`:65` lon/lat, `:80` cos θ, `:104` `dx2f_ang_kj`,
  `:130-137` solid angle, `:142` `x_ov_rD_kji`); `:199`/`:203` `center_width2/3`; `:207` `face_area1`; `:211`
  `face_area2`; `:215` `face_area3`; `:219` `cell_volume`; `:229` `face_moment2_x1`; `:237`
  `face_centroid_shift_x1`; `:266`/`:281` `_set_face{2,3}_metric` (marked "TODO(cli):: CHECK"); `:295`-`:323`
  `prim2local1/2/3_`; `:344`-`:387` `flux2global1/2/3_`; `:415` `forward` (geometric sources);
  `src/coord/gnomonic_equiangle.h:33@e894700` `gnomonic_sin_cos`, `:45` `gnomonic_prim2local`, `:60`
  `gnomonic_flux2global`; `src/coord/coord_utils.cpp:12@e894700` `coord_vec_lower_`, `:29` `coord_vec_raise_`;
  `src/coord/coordinate.cpp:611@e894700` `boundary_velocity_` (g23-aware frame for wall BCs, used by
  `src/bc/bc_func.cpp:152`); Riemann solver use: `src/riemann/hllc.cpp:58-99@e894700`, `src/riemann/lmars.cpp:56@e894700`.
- Tests: `tests/test_cubed_sphere_cell_volume.py` (`test_cubed_sphere_cell_volume_python`) — the panels' volumes sum to
  4π(ro³-ri³)/3 and div(r r̂)=3 in every cell, to ROUNDOFF=1e-12 (set in the script); `test_coordinate.release`
  `DeviceTest.vec_lower_raise`, `contra_cart`, `contra_sph`, `cached_cubed_sphere_velocity_matrices_match_direct`,
  `contra_sph_matches_cartesian_composition`, `uniform_radial_spherical_velocity_round_trips`, `flux_projection1/2/3`,
  `GnomonicEquiangle.l2g`; `tests/test_forcing.cpp` with `tests/test_forcing_cubed_sphere.yaml` (covariant drag over
  the whole field).
- Limits / known issues:
  - `GnomonicEquiangle.area_vol` and `DeviceTest.usrc` only print, with no assertions (`test_coordinate.cpp:123-144`,
    `:414-422`).
  - The gnomonic x1v is the arithmetic mid-radius (`gnomonic_equiangle.cpp:36-37`), not the volume centroid as in
    spherical-polar. The covariance derivation relies on this (A2 = x1v·dx1f = ∫r dr exactly).
  - `_set_face2/3_metric` carry "TODO(cli):: CHECK".
  - The corrected-PE gravity work has no gnomonic form (warning at `src/hydro/hydro.cpp:83-93`).
- Discrepancies: docs/derivations/289-covariance-x3-curved.md cites `gnomonic_equiangle.cpp:197-203` for face_area2/3.
  At dae902b they are at `:211`/`:215`. The derivation's line pointers predate the solid-angle rewrite; the content
  holds.


#### 3.5 Radial face moments and the face-centroid shift (curved-grid helpers)
<sub>inventory A: Scheme 3.5: Radial face moments and the face-centroid shift (curved-grid helpers)</sub>

- Summary: on spherical-polar and cubed-sphere grids an x2/x3 face weighs r dr while a cell weighs r² dr. snapy
  provides the exact second central moment σ1² = (h²/12)(1-h²/(12 r̄²)) and the shift r_v - r_c =
  h²(12r̄²-h²)/(12r̄(12r̄²+h²)), both cancellation-free, both zeroed on degenerate ghost faces with r̄ ≤ h/2. In
  Cartesian they are h²/12 and 0. Switch: used only when `SNAP_FLUX_COVARIANCE` is on (S1.14).
- Derivations: exists: docs/derivations/289-covariance-x3-curved.md@e894700 §2.6-2.7 (moments, r_c, and the
  comparison with x1v); also sources/deriv__289-covariance-x3-curved.md.
- Figures: a radial cell with r_m, r̄, r_c, r_v, r_p marked; σ1²/(h²/12) as a function of h/r̄.
- Code: `src/coord/coordinate.hpp:254@e894700` (`face_moment2_x1` doc), `:270`, `:285`; `src/coord/coordinate.cpp:442@e894700`
  `face_moment2_x1`, `:446` `radial_face_moment2_`, `:461` `face_centroid_shift_x1`, `:467` `radial_face_centroid_shift_`.
- Tests: `tests/test_radial_face_moments.cpp` (`test_radial_face_moments.release`) — rational cases to 1e-13 relative,
  closed forms to 1e-14 relative, per-cell indexing (47/1176) to 1e-14.
- Limits / known issues: none.
- Discrepancies: the derivation's line citations (e.g. `coordinate.cpp:429-435`) are shifted at dae902b
  (`face_area2` `:429`, `face_area3` `:433`, consistent). Spot-check each when writing.


#### 3.6 Layouts and rank maps (slab, cubed, cubed-sphere)
<sub>inventory A: Scheme 3.6: Layouts and rank maps (slab, cubed, cubed-sphere)</sub>

- Summary:
  - `slab` is a 2-D (x2,x3) block grid and requires pz=1.
  - `cubed` is a 3-D block grid, the only layout that splits x1 (pz>1).
  - `cubed-sphere` is 6 panels × px×py blocks, requiring pz=1 and px=py.
  - Ranks follow Morton (Z-order) within the block grid or panel, face-major on the cubed sphere.
  - The YAML maps nb2→px (x2), nb3→py (x3), nb1→pz (x1).
  - Block rank = process_rank·bpp + local index.
  Switch: YAML `distribute: {layout: slab|cubed|cubed-sphere (default slab), nb1, nb2, nb3 (default 1),
  blocks_per_process}`. Periodicity comes from boundary names ("periodic" on x2/x3 for all layouts, x1 periodic only
  for `cubed`).
- Derivations: Morton encoding is standard. Re-derive the cubed-sphere edge-stepping (`_step_one`, corners in two
  hops) from `src/layout/cubed_sphere_layout.cpp:445@e894700` and `:498@e894700`.
- Figures:
  - Morton order on a 4×4 block grid.
  - The cube net with the CS_FACE_EDGES table drawn as arrows (neighbour face, side, reversal flag).
  - (rank → process, local block) mapping for bpp>1.
- Code: `src/layout/layout.hpp:52@e894700` `LayoutOptionsImpl` (`:98` type default slab, `:83-93` block↔process maps);
  `src/layout/layout.cpp:221@e894700` `from_yaml`; `:246` `LayoutImpl::create`; `src/layout/slab_layout.cpp:10@e894700`
  (pz==1 `:12`), `:41` `neighbor_rank`; `src/layout/cubed_layout.cpp:10@e894700`, `:40`;
  `src/layout/connectivity.cpp:28@e894700` `build_zorder_coords2`, `:45` `build_zorder_coords3`;
  `src/layout/cubed_sphere_layout.hpp:80@e894700` face-major rank; `src/layout/cubed_sphere_layout.cpp:246@e894700`
  `CS_FACE_NAMES`, `:309` `CS_FACE_EDGES`, `:413` `_initialize` (pz==1, px==py), `:445` `_step_one`, `:481`
  `rank_of`, `:488` `loc_of`, `:498` `neighbor_rank`; `src/mesh/meshblock_options.cpp:102@e894700`,`:142`,`:179`
  (periodic flags from BC names).
- Tests: `tests/test_exchange.cpp` + `run_exchange_decomp.py` (`test_exchange_decomp`: mesh6 / proc6 / proc2_mesh3 on
  gloo) — ghost values equal the expected neighbour, with both local and remote neighbours seen.
- Limits / known issues:
  - x1 decomposition exists only for `cubed`; the cubed sphere has no x1 split (`cubed_sphere_layout.cpp:415`).
  - On a cubed sphere with pz>1, x1 ghosts of θ would be neither exchanged nor overwritten. That configuration is
    refused (theta-seam report §7).
- Discrepancies: none.


#### 3.7 Physical vs internal faces (bfunc assignment)
<sub>inventory A: Scheme 3.7: Physical vs internal faces (bfunc assignment)</sub>

- Summary: YAML boundary names become bfuncs. At construction every face shared with a neighbour (or periodic in a
  layout direction) gets bfunc=nullptr, and `is_physical_boundary` means "a bfunc is installed". On the cubed sphere the
  panel edges carry the no-op `custom_inner/outer` bfuncs and are NOT nulled. The cubed-sphere exchange ignores
  `is_physical_boundary`, so ghosts still arrive. Switch: YAML `boundary-condition: external: {x1-inner, ..., x3-outer}`
  (default "reflecting").
- Derivations: none.
- Figures: a 2×2 slab decomposition with the faces coloured physical/internal/periodic.
- Code: `src/mesh/meshblock.cpp:137-178@e894700` (nulling, slab/cubed only); `src/mesh/meshblock_options.cpp:218@e894700`
  `face_of`, `:229` `is_physical_boundary`, `:243` `is_wall_boundary` (whitelist); `src/bc/bc_func.cpp:7-8@e894700`
  `custom_inner/outer` (empty); `src/hydro/hydro.cpp:204@e894700` `is_x1_wall`.
- Tests: `tests/test_forcing_cubed_sphere.yaml` header documents a vacuous-test trap (nx1=1 ⇒ no x1 bfunc ⇒ every
  top/bottom forcing returns early).
- Limits / known issues: on the cubed sphere `is_physical_boundary(dy,dx,0)` is TRUE at panel edges (custom bfunc).
  Code that loops over all bfuncs (e.g. the θ ghost fill at `hydro_forward.cpp:694-697`) applies the no-op there. Any
  future x2/x3 "physical boundary" test would misclassify panel edges (inferred from code).
- Discrepancies: none.


#### 3.8 Generic ghost exchange (what is filled)
<sub>inventory A: Scheme 3.8: Generic ghost exchange (what is filled)</sub>

- Summary: for each face-adjacent neighbour (corners skipped by default) the interior slab is packed and received into
  the ghost slab. A sync can be conserved, primitive or scalar, with `interpolate` (cubed-sphere cross-panel only),
  `skip_corner`, `dim` (face-state syncs) and phase flags. After a sync, `fill_corners` averages the two adjacent edge
  strips into each x2-x3 corner. Transport details are in Ch14 S14.3. Switch: `SyncOptions`
  (`src/layout/layout.hpp:135@e894700`); defaults skip_corner=true, interpolate=false, type kConserved.
- Derivations: corner value = ½(left strip + bottom strip) is a convention. Re-derive (state it) from
  `src/layout/layout.cpp:710@e894700`.
- Figures: the 3×3 neighbour stencil with buffer ids (`get_buffer_id`), interior slabs sent vs ghost slabs received,
  and corners synthesised.
- Code: `src/layout/layout.hpp:32@e894700` `get_buffer_id`; `src/layout/layout.cpp:477@e894700` `serialize`; `:668`
  `deserialize`; `:710` `fill_corners`; `:753` `finalize` (corner synthesis unless a split phase);
  `src/mesh/meshblock.cpp:554@e894700` `exchange`.
- Tests: `test_exchange.release` (2 ranks, bpp 3); `test_mesh_multi_block.release`; `test_mesh_exchange_python`;
  `tests/test_cubed_sphere_vertical_velocity_exchange.py` (`..._python`) — a radial velocity passes panel seams
  unchanged to 1e-12 abs + 1e-12 rel.
- Limits / known issues: corners of x1×x2 (and x1×x3) blocks are never exchanged. At physical x1 walls they are
  refreshed (S3.14); at internal x1 seams they keep stale values (inferred). No dimension-split stencil reads them, but
  cross-derivative operators could.
- Discrepancies: none.


#### 3.9 Cubed-sphere cross-panel ghost interpolation
<sub>inventory A: Scheme 3.9: Cubed-sphere cross-panel ghost interpolation</sub>

- Summary: across a panel edge a ghost is a 1-D linear interpolation along the edge, at abscissae `usrc` precomputed
  once (face 0, side L, reused by symmetry) by mapping each ghost centre through 3-D onto the source panel. The source
  slides along the edge by about (g-½)·sin2β cells, at most nghost-½, so the strip is widened by `cs_interp_margin =
  nghost` on each side. The block offset is applied to the integer index after `floor`, not folded into the double. On a
  subdivided panel the sync runs in two phases (intra-panel, then cross-panel) so the widened strip is packed from a
  current halo. Corners are synthesised after both phases. Velocities are rotated to the spherical (r,θ,φ) frame before
  sending and back after interpolation. Conserved momenta are raised first and lowered after (cos θ), and the strip gets
  the rev/flip/transpose relabelling. Switch: `SyncOptions.interpolate(true)` (per-stage conserved, init primitive,
  scalar syncs); two-phase only when cubed-sphere and (px>1 or py>1).
- Derivations:
  - Slide formula η'-η ≈ -(g-½)Δ sin2η and its bound nghost-½: exists: sources/canoe__cubedsphere_decomposition_TECH_REPORT.md
    §1 (first-order expansion; the exact form is checked numerically there).
  - Ordering constraint (the halo must be current, a dependency cycle within one round): exists:
    sources/canoe__cubedsphere_decomposition_TECH_REPORT.md §5-6.
  - Ghost-centre mapping (`cs_build_ghost_usrc`): re-derive from `src/coord/cubed_sphere_utils.cpp:78@e894700`.
  - rev/flip/transpose rules from side parity: re-derive from `src/layout/cubed_sphere_layout.cpp:701-705@e894700`.
- Figures:
  - Two panels meeting at an edge: ghost centres in layers g=1..3 and their source points sliding toward the edge
    midpoint (Figure 1 of the source report, to be redrawn).
  - A subdivided panel: the widened strip reaching into the sender's intra-panel halo; the two-phase timeline.
  - Frame rotation pipeline: contravariant(sender) → spherical → (send) → interpolate in the sender frame → spherical →
    contravariant(receiver).
- Code: `src/coord/cubed_sphere_utils.hpp:108@e894700` `cs_interp_margin`; `src/coord/cubed_sphere_utils.cpp:78@e894700`
  `cs_build_ghost_usrc`, `:259` `cs_velocity_transform_matrix`, `:300` `cs_apply_velocity_transform_`;
  `src/coord/gnomonic_equiangle.cpp:162-196@e894700` (global usrc + integer shift), `:245` `interp_ghost`, `:475`
  `_interp_ghost_LR`, `:516` `_interp_ghost_BT`; `src/layout/cubed_sphere_layout.cpp:122@e894700`
  `_velocity_transform` (cached, one radial plane), `:549` `serialize` (`:630` phase-1 return, `:681` margin, `:703-705`
  flags), `:795` `deserialize` (`:848`, `:936` `interp_ghost`), `:961` `exchange_remote` (`:1014` same-panel phase
  filter); `src/mesh/meshblock.cpp:554-572@e894700` the two-phase branch.
- Tests: `tests/test_cubed_sphere_exchange.cpp` (`test_cubed_sphere_exchange.release`) —
  `CubedSphere.subdivided_panel_exchange_matches_one_block` (`torch::equal` on interior x2f, dx2f and hydro_u[IDN]
  after one stage, nb2=1,2,4 in one process) and its `_cuda` twin; `CommTag.rejects_tags_that_collide...`;
  `test_coordinate.release` `DeviceTest.interpolate_LR`.
- Limits / known issues (source report §8, §10):
  - Bit-for-bit decomposition independence is verified only for nb2=nb3 ∈ {1,2,4}. The report ran one cycle, CPU/gloo,
    bpp=1; the ctest runs one stage, bpp=6·nb².
  - The wide-landing margin cells keep the neighbour's frame after deserialize. They are unread (the report shows this
    with gate B).
  - The 4th-order interpolation branch in `_interp_ghost_LR/BT` is dead (interp_order must be 2).
  - `_interpolate_to_local` (`cubed_sphere_layout.cpp:1065`) is a TODO stub with no effect.
  - The base-scheme tracer overshoot at seams from interpolated ghosts is larger than in-panel (1.05 at 12 cells/edge;
    theta-seam report §12).
- Discrepancies: the source report §6 says "seven interpolating synchronisations". Its own review banner corrects this
  to five, because the θ exchanges are raw copies at dae902b. The report's §5 code comment is no longer in the tree.


#### 3.10 Cubed-sphere face-state seam sync (hydro and scalar LR states)
<sub>inventory A: Scheme 3.10: Cubed-sphere face-state seam sync (hydro and scalar LR states)</sub>

- Summary: for x2/x3 fluxes, the reconstructed L/R states at panel-edge faces are exchanged as raw copies (depth 1, no
  interpolation, cross-panel only), keyed `*_wl:+` and `*_wr:-`. The suffix selects a directional partial send/receive,
  so the L/R roles resolve correctly at same-sign edges, and both panels solve the same Riemann problem. The scalar
  originally used one un-suffixed key, which swapped L/R on the four same-sign edges and made one face anti-upwind
  (fixed). Switch: none (always on for the cubed-sphere layout).
- Derivations: the anti-upwind mechanism and the role of the suffix: exists:
  sources/canoe__tracer_seam_TECH_REPORT.md §4-6 (argument, not algebra).
- Figures: a same-sign edge (e.g. 1T-3R) with L/R arrows before and after the suffix protocol.
- Code: `src/hydro/hydro_forward.cpp:544-587@e894700` (`:563` keys, begin/launch/finalize); `src/scalar/scalar.cpp:84@e894700`,
  `:96`; `src/layout/cubed_sphere_layout.cpp:602@e894700`, `:715`, `:837`, `:928` (suffix rules); `:704-705`
  (trans/flip flags, no-ops on depth-1 strips).
- Tests: `tests/test_flux_covariance_seams.py` (`test_flux_covariance_seams_python`) — mass, vapour and E+PE conserved
  across seams to round-off with the #289 term on; the tracer seam fix has no dedicated ctest beyond the positivity
  seam test (S3.11).
- Limits / known issues: none.
- Discrepancies: the tracer-seam report cites `cubed_sphere_layout.cpp:711` for `flip_flag`. At dae902b it is `:705`.


#### 3.11 θ (positivity donor factor) across seams: raw copy
<sub>inventory A: Scheme 3.11: θ (positivity donor factor) across seams: raw copy</sub>

- Summary: a face's donor factor θ must be the donor's own number on both sides, or the limiter leaks mass. θ is
  therefore exchanged with `interpolate(false)` (raw index-matched copy). The interpolated cubed-sphere ghost had been a
  blend at every depth. The species enthalpy is recomputed from the ghost W instead of being exchanged (#238). Switch:
  active when `eos.limiter` and ny>0.
- Derivations: conservation needs one shared factor per face: exists: sources/canoe__theta_seam_TECH_REPORT.md §1, §6
  (argument).
- Figures: a seam face with the donor on panel A, θ_A vs the interpolated blend on panel B, and the leaked mass.
- Code: `src/hydro/hydro_forward.cpp:671-688@e894700` (`:687-688` `topts.interpolate(false)`, `:694` bfunc ghost fill);
  `src/scalar/scalar.cpp:144@e894700`.
- Tests: `tests/test_flux_positivity_cubedsphere.py` (`test_flux_positivity_cubedsphere_python`, + `_cuda`) — 6 panels in
  one process, hat edge on the +X/+Y seam, tracers conserved to DRIFT_TOL=1e-13 (in the script), hits>0, the hat stays
  in [0,1]; `tests/test_flux_positivity_cubedsphere_moist.py` (+ `_cuda`); `test_sedimentation_cubed_seam.release`
  (2 ranks).
- Limits / known issues: corners keep θ=1 (skip_corner). A corner is never the donor of a consumed face (report §7).
- Discrepancies: the report banner cites `hydro_forward.cpp:341`/`scalar.cpp:144` for the raw copies. The hydro line is
  `:688` at dae902b.


#### 3.12 x1 seams between blocks (column split, `cubed` layout pz>1)
<sub>inventory A: Scheme 3.12: x1 seams between blocks (column split, `cubed` layout pz>1)</sub>

- Summary: four mechanisms make a split column match one block.
  - (a) The hydrostatic reference scan is relayed top→bottom across every x1 seam (`take_x1_anchor`/`pass_x1_anchor`):
    a board in-process, the process group across processes.
  - (b) Ghost rows of (pref, dref) are taken from the neighbour's interior.
  - (c) Under SNAP_X1_CENTROID_EXACT, the plain-mean ghost cells and the face-pressure rows past the seam come from the
    neighbour (`_x1_ghost_rows`).
  - (d) Across PROCESS seams only, the x1 seam-face flux (and the face pressure and F^R) is set to the average of the
    two sides. With (b) the two sides already agree, so a same-process seam is not averaged.
  Column-wide EOS repairs gather the whole x1 column (`gather_x1`). The wall reconstruction and the WB wall mirroring
  are gated on `is_physical_boundary`, so they never act at a seam. Switch: `distribute: {layout: cubed, nb1>1}`. The
  WB4 switch needs nghost≥3 (`src/hydro/hydro.cpp:96-103@e894700`).
- Derivations:
  - Telescoping conservation of the averaged seam flux: re-derive from `src/hydro/hydro_forward.cpp:425-438@e894700`
    (comment only).
  - Reference relay (running face value + interior drop): re-derive from `src/hydro/hydro.cpp:509-532@e894700`
    (comment only); the WB scheme itself is owned by the WB chapter (exists: docs/derivations/wb-ref4.md §7 for the
    seam flag).
- Figures:
  - A column split into 2-4 blocks: the anchor relay arrows top→bottom; ghost rows of pref/dref copied from the
    neighbour interior.
  - The seam face with the two one-sided fluxes and their average (process seam) vs the identical states (in-process).
- Code: `src/hydro/hydro.cpp:261@e894700` `x1_neighbors`; `:251` `_x1_ghost_rows`; `:484` `_hydro_ref_x1` (`:506`
  `x1_split`, `:512` take anchor, `:559` pass anchor, `:574` ghost-row exchange); `src/hydro/hydro_forward.cpp:233-262@e894700`
  (physical-face gating), `:293` and `:515` (`_x1_ghost_rows` tags 0x7724/0x7722), `:448-505` (seam average, tags
  0x7720/0x7721); `src/layout/layout.cpp:879@e894700` `take_x1_anchor`, `:907` `pass_x1_anchor`, `:777`
  `gather_x1`; `src/eos/equation_of_state.cpp:279-282@e894700` (column gather).
- Tests:
  - `tests/test_pref_local_seam.cpp` (`test_pref_local_seam.release`):
    `HydroRefX1.local_blocks_restart_the_reference_at_the_seam` (EXPECT_NEAR 1e-6) and
    `in_process_split_matches_one_block_after_200_steps` (max relative state diff ≤1e-12, bound chosen in PR #259).
  - `tests/test_x1_seam_split.cpp` arms (`test_x1_seam_split.release` plus `test_x1_seam_split_x1_centroid`,
    `_radial_exact`, `_radial_exact_off`, `_wb_ref4`, `_wb_ref4_gravity_0`, and CUDA twins): split vs one block ≤1e-13
    relative.
  - `tests/test_x1_seam_split_mp.cpp` (`test_x1_seam_split_mp.release` and arms `_x1_centroid`, `_radial_exact`,
    `_radial_exact_off`, `_wb_ref4`; 2 ranks): cross-rank split vs one block / in-process split ≤1e-13.
  - `test_parentless_cloud_nb1_mp.release` (2 ranks, + `_gloo`): column repair keeps mass across processes.
- Limits / known issues:
  - Not bitwise. The tests use 1e-13 to 1e-12. Issue #250's T4 (pre-#259) found x1 CPU/gloo splits differ by ≤8e-15
    relative, while 2-GPU UCX splits were bitwise (`gh__ISSUE_THREADS_138-250.md:1408`, `:1423`).
  - SNAP_GRAVITY_WORK_RADIAL_EXACT keeps a one-sided slope at block edges, so a split column differs. This is by design;
    the test only prints the gap (`test_x1_seam_split.cpp:12-16`).
  - Blocks of one process must run concurrently (5-min wait) and bpp≤16 for remote block messages.
- Discrepancies: the comments in `tests/test_pref_local_seam.cpp:1-15`, `:141` and `:147-152` still say "RED"
  (pre-#259). The assertions now expect the fixed behaviour.


#### 3.13 Exchange of conserved vs primitive variables, and the velocity frame at seams
<sub>inventory A: Scheme 3.13: Exchange of conserved vs primitive variables, and the velocity frame at seams</sub>

- Summary: the per-stage sync exchanges CONSERVED variables (hydro_u, scalar_s), and the scalar primitive is rebuilt
  afterwards. The init sync exchanges primitives. On the cubed sphere, conserved momenta are covariant (raised before the
  rotation to spherical, lowered after), primitives are contravariant, and scalars are not rotated. Switch:
  `SyncOptions.type`.
- Derivations: covariant/contravariant handling: re-derive from `src/coord/cubed_sphere_utils.cpp:288-296@e894700`.
- Figures: a table of type → rotation applied.
- Code: `src/mesh/meshblock.cpp:913-983@e894700`; `src/layout/cubed_sphere_layout.cpp:735-753@e894700` (serialize
  switch on type).
- Tests: `test_coordinate.release` `DeviceTest.cached_cubed_sphere_velocity_matrices_match_direct`.
- Limits / known issues: none.
- Discrepancies: none.


#### 3.14 x1-wall corner refresh inside tangential ghost slabs (#265)
<sub>inventory A: Scheme 3.14: x1-wall corner refresh inside tangential ghost slabs (#265)</sub>

- Summary: after the tangential exchange, each installed x1 bfunc except outflow is re-applied inside the x2/x3 ghost
  slabs, unless that slab's own tangential face is physical. This keeps wall corners consistent with the updated column.
  It relies on the contract that a face function may be called again on an nghost-wide slab and gives the same ghosts.
  Switch: always on in `MeshBlock::exchange_ghost_zones`.
- Derivations: none (consistency rule). PR #265 records the mechanism (viscous cross-derivatives at the wall row).
- Figures: an x1 wall with the x2 seam: corner cells before (stale reflection) and after the refresh.
- Code: `src/mesh/meshblock.cpp:932-973@e894700` (`refresh` lambda `:951`, call `:972`); `src/bc/bc_func.hpp` (contract comment).
- Tests: `tests/test_wb_wall_corner.cpp` (`test_wb_wall_corner.release`) — a resting polytrope with viscosity keeps
  max|u2|/c_s ≤ 1e-12 for stock and user walls, a one-block vs two-block x2 split, and scalar corner primitives (CPU and
  CUDA).
- Limits / known issues: `Mesh::exchange_ghost_zones` (`mesh.cpp:389`) does not refresh (PR #265 limits). Only x1
  walls are handled.
- Discrepancies: none.


#### 3.15 Registered but non-functional coordinate type `cylindrical`
<sub>inventory A: Scheme 3.15: Registered but non-functional coordinate type `cylindrical`</sub>

- Summary: `cylindrical` is accepted by `CoordinateImpl::create`, but `CylindricalImpl::reset()` is empty and the source
  file is disabled (`cylindrical.cpp_`). No widths, centres or areas are built. Switch: `geometry.type: cylindrical`.
- Derivations: n/a.
- Figures: none.
- Code: `src/coord/coordinate.hpp:363@e894700` (`reset() {}` at `:374`); `src/coord/coordinate.cpp:601-602@e894700`.
- Tests: none.
- Limits / known issues: selecting it would run on empty buffers (inferred from code).
- Discrepancies: none.


---

<a id="ch4"></a>
## Chapter 4. Spatial discretization

Split in two because the second half shares one derivation thread. 4.A: the finite-volume stage operator, the reconstructions, the Riemann solvers, seam-flux averaging and the geometric sources. 4.B: the $O(\Delta x_1^2)$ face-average corrections, the $x_2/x_3$ flux covariance and centroid terms (`SNAP_FLUX_COVARIANCE`) and the $x_1$ mass-flux covariance (`SNAP_X1_MASS_COVARIANCE`).

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: the semi-discrete finite-volume operator of one RK stage as `HydroImpl::forward` builds it: primitive
reconstruction per direction (src/recon), the Riemann flux (src/riemann), the flux divergence and the
geometric (curvature) sources (src/coord), single-valued seam fluxes, and the O(dx1^2) face-average
corrections of the x2/x3 fluxes (`SNAP_FLUX_COVARIANCE`) and of the x1 mass flux (`SNAP_X1_MASS_COVARIANCE`).

Merge/split proposal: split into **4A "Reconstruction, Riemann solvers and the flux divergence"** (FV update,
recon, Riemann, geometric sources, seam averaging; mostly standard methods, re-derived from code) and
**4B "Face averages versus cell averages: the O(dx1^2) corrections"** (SNAP_FLUX_COVARIANCE all rows incl.
centroid shift and p*, radial face moments, SNAP_X1_MASS_COVARIANCE). Reason: 4B has a single derivation
thread (mean of a product vs product of means; volume vs area centroid) with ~2000 lines of committed
derivation and its own test family, while 4A has almost no committed derivation. The x1 r^2 centroid
conversion (SNAP_X1_CENTROID_EXACT) is the x1 member of the same family but is inseparable from the
well-balanced reference, so it stays in Chapter 5 with a forward pointer from 4B.

</details>


### 4.A Reconstruction, Riemann solvers, divergence and sources


#### 4.1 Finite-volume update and flux divergence (stage operator)
<sub>inventory C: Scheme: Finite-volume update and flux divergence (stage operator)</sub>

- Summary: du = -dt * [ (A F)_{+} - (A F)_{-} ] / V summed over x1,x2,x3 on interior cells, minus geometric
  sources, then forcings; the stage order is EOS -> x1 recon+Riemann -> seam average -> x2/x3 recon(+cubed-sphere
  face-state exchange)+Riemann(+covariance) -> species positivity limiter -> divergence+sources -> forcings ->
  implicit correction. Switch: per-direction `dynamics/disable-flux-x1|x2|x3` (YAML, default false;
  src/hydro/hydro_options.cpp:54-56; disabling also zeroes the matching grav component, :80-82).
- Derivations:
  - FV balance and face-average definition of the flux: exists docs/289-covariance-x3-curved.md §1.1 (eqs 1.1-1.2;
    its line refs are at 117e449, stale).
  - The stage pipeline and which tensor carries what (flux1/2/3 shapes, face indexing il..iu+1, interior-only
    tendency): re-derive from src/hydro/hydro_forward.cpp:198-999@e894700 and src/coord/coordinate.cpp:509-553@e894700.
- Figures:
  - One cell with its six faces, A_{i+-1/2}F_{i+-1/2}, V_i; arrows for flux1/flux2/flux3 and where the geometric source enters.
  - Pipeline strip of one RK stage (EOS, x1 sweep, seam average, x2/x3 sweeps, limiter, divergence, forcings, implicit).
  - Index cartoon: cells 0..nc1-1, ghosts, il/iu, faces il..iu+1, which faces `divergence` consumes.
- Code:
  - src/hydro/hydro_forward.cpp:207 — `HydroImpl::forward` — the stage operator.
  - src/hydro/hydro_forward.cpp:218 — `peos->forward(u, w)` — conserved -> primitive.
  - src/hydro/hydro_forward.cpp:559, :571 — `precon23->forward(w, DIM2/DIM3)` — x2/x3 reconstruction (no WB, full state).
  - src/hydro/hydro_forward.cpp:562-596 — cubed-sphere exchange of x2/x3 L/R face states across panels (`cross_panel_only`, `interpolate(false)`; cross-ref cubed-sphere chapter).
  - src/hydro/hydro_forward.cpp:733-755 — step (5) flux divergence via `pcoord->forward` (with or without p*).
  - src/hydro/hydro_forward.cpp:764-766 — `du.index(interior) = -dt * _div.index(interior)`.
  - src/coord/coordinate.cpp:509 — `CoordinateImpl::divergence` — sum of A F differences / V.
  - src/coord/coordinate.cpp:585 — `CoordinateImpl::forward` — Cartesian: divergence only, face pressure ignored.
  - src/coord/coordinate.cpp:425, :437 — `face_area1`, `cell_volume` (Cartesian).
  - src/hydro/hydro.cpp:151-176 — flux buffers F1/F2/F3, face-pressure buffer P1, divergence buffer D.
- Tests:
  - tests/test_coordinate.cpp (test_coordinate.<build>) — `GnomonicEquiangle.area_vol` (prints), `SphericalPolar.geometry_matches_athena_reference_formulas`, `flux_projection1..3` — geometry and frame projections; allclose defaults.
  - tests/test_cubed_sphere_cell_volume.py (test_cubed_sphere_cell_volume_python) — six-panel volumes sum to 4pi(ro^3-ri^3)/3 and div(r rhat) = 3 per cell; ROUNDOFF 1e-12, rest REST_TOL 1e-6 (file constants).
  - tests/run_straka.cmake (test_straka, reference example) — end-to-end against a downloaded reference file (WENO5/LMARS deck examples/straka.yaml).
- Limits / known issues:
  - Cylindrical coordinates: `src/coord/cylindrical.cpp_` not compiled (docs/289-covariance-x3-curved.md §5).
  - x1 tendency on ghost cells is never formed; corrections that write ghost columns are harmless by construction.
- Discrepancies:
  - docs/289-covariance-x3-curved.md §1.1 quotes `coordinate.cpp:461-505` and `hydro_forward.cpp:418,:427-429` at 117e449; at dae902b they are coordinate.cpp:509-553 and hydro_forward.cpp:764-766.


#### 4.2 Reconstruction framework (Reconstruct / Interp, variable split, floors)
<sub>inventory C: Scheme: Reconstruction framework (Reconstruct / Interp, variable split, floors)</sub>

- Summary: `ReconstructImpl::forward` returns [wl, wr] per face; with `shock: false` density and tracers use
  interp1 and velocity+pressure use interp2; with `shock: true` all rows use interp1 and no floors are applied.
  Switches: YAML `dynamics/reconstruct/{vertical,horizontal}/{type,scale,shock}` (src/recon/reconstruct.cpp:31-36);
  defaults from YAML: type "dc", scale false, shock false. EOS `limiter`, `density-floor`, `pressure-floor` gate the
  face floors (src/eos/equation_of_state.hpp:49-52, defaults 1e-10, 1e-10, false).
- Derivations:
  - Face/cell index map of `_apply_inplace` (outl -> wlr[IRT] at faces il-1..iu, outr -> wlr[ILT] at il..iu+1;
    dummy-region replication): re-derive from src/recon/reconstruct.cpp:50-65@e894700.
  - Why weno3/weno5 select linear cp3/cp5 for velocity/pressure (interp2): no rationale in any source;
    describe from src/recon/interpolation.cpp:21-36@e894700 (design choice, not derived).
- Figures:
  - Stencil of a 5-point reconstruction: cell i, its left face (wlr[IRT] at face i) and right face (wlr[ILT] at face i+1).
  - Which rows go through interp1 (WENO) vs interp2 (linear cp) under shock false/true.
- Code:
  - src/recon/reconstruct.cpp:24 — `ReconstructOptionsImpl::from_yaml` — keys type/scale/shock and defaults (:33-36).
  - src/recon/reconstruct.cpp:50 — `_apply_inplace` — face index mapping and ghost-face replication (:60-64).
  - src/recon/reconstruct.cpp:79 — `ReconstructImpl::forward` — nghost = stencils/2+1 (:86); shock branch (:99-102); density via interp1 (:133); density floor (:135-137); velocity/pressure via interp2 (:141); pressure floor (:143-145); tracers via interp1 (:151) and clamp_min(0) whenever the EOS limiter is on, even with floor=false (:153-155).
  - src/recon/reconstruct.hpp:99 — `forward(w, dim, floor=true)` — floor=false used by the WB x1 path.
  - src/recon/interpolation.cpp:6 — `InterpImpl::create` — "dc","plm","ppm","cp3","cp5","weno3","weno5"; interp2 of weno3/weno5 is Center3/Center5 (:21-36).
  - src/hydro/hydro.cpp:35, :42 — `precon1` (vertical), `precon23` (horizontal).
- Tests:
  - tests/test_plm.cpp (test_plm.<build>) — `reconstruct_preserves_a_constant_field` for dc/plm/weno5 in dims 1-3; torch::allclose defaults.
- Limits / known issues:
  - Uniform-spacing weights on every grid (fixed rationals); stretched x1 not accounted for (issue #280 text, sources/gh__ISSUE_THREADS_251-294.md:653-660).
  - "scale: true" changes results through the WB reference in moist bubbles, unexplained (issue #275, sources/gh__ISSUE_THREADS_251-294.md:551-567).
- Discrepancies:
  - `ReconstructOptionsImpl` default `shock = true` (src/recon/reconstruct.hpp:51) but YAML default `false` (src/recon/reconstruct.cpp:33): programmatic and YAML construction differ.
  - The `report()` of ReconstructOptions prints `density_floor`, `pressure_floor`, `limiter`, `is_boundary_*` members that `forward` never reads (floors come from the EOS options, reconstruct.cpp:129-145).


#### 4.3 Donor cell ("dc")
<sub>inventory C: Scheme: Donor cell ("dc")</sub>

- Summary: first-order, face value = adjacent cell value. Switch: `type: dc` (default type).
- Derivations: trivial; re-derive from src/recon/interpolation.hpp:100-105@e894700.
- Figures: piecewise-constant cells with the two face states at one face.
- Code: src/recon/interpolation.hpp:88 — `DonorCellInterpImpl` — `left`/`right` copies (:100-105).
- Tests: tests/test_plm.cpp `reconstruct_preserves_a_constant_field` (dc arm); tests/test_x1_seam_split.cpp `wb_ref4_gravity_0_nghost_1_steps` runs donor cell on nghost 1 (comment :114).
- Limits / known issues: none recorded.


#### 4.4 PLM (van Leer harmonic-mean slope)
<sub>inventory C: Scheme: PLM (van Leer harmonic-mean slope)</sub>

- Summary: wl/wr = w_i -+ dwm/2 with dwm = 2 dwl dwr/(dwl+dwr) where dwl dwr > 0, else 0. Switch: `type: plm`.
- Derivations:
  - Harmonic-mean (van Leer) slope and TVD property: re-derive from src/recon/plm.cpp:19-29@e894700 (PR #212 body states only the 0/0 guard, sources/gh__PR_BODIES_202-219.md:243-260; not a derivation).
- Figures: slope cartoon with left/right differences and the harmonic mean; the dw2 <= 0 extremum case.
- Code:
  - src/recon/plm.cpp:10 — `PLMInterpImpl::forward` — vectorised; guard `torch::where(dw2 > 0, ...)` (:26).
  - src/recon/interp_simple.hpp:57 — `interp_plm` — scalar reference used by tests.
  - src/recon/interp_simple.hpp:12-33 — `minmod`, `superbee`, `vanleer`, `mclimiter` — defined, unused anywhere in src.
- Tests:
  - tests/test_plm.cpp (test_plm.<build>) — `interp_plm` (1e-10), `interp_plm_torch1..3`, `interp_plm_round_off_slopes_stay_finite` (finite, bitwise equal to the scalar form in double; added by PR #212), constant field preserved.
- Limits / known issues: the "limiters" in interp_simple.hpp are dead code; PLM is reported worse than WENO5 on the tall rest column (sources/canoe__tall_column_instability_TECH_REPORT.md §3f).


#### 4.5 Linear centred polynomials cp3 / cp5 (and cp2/cp4/cp6 helpers)
<sub>inventory C: Scheme: Linear centred polynomials cp3 / cp5 (and cp2/cp4/cp6 helpers)</sub>

- Summary: cp3 (1/3, 5/6, -1/6) and cp5 (-1/20, 9/20, 47/60, -13/60, 1/30) face values from cell averages; used
  directly (`type: cp3|cp5`) or as interp2 of weno3/weno5. Switch: `type`.
- Derivations: weights as face values of the interpolating polynomial of cell averages: re-derive from
  src/recon/cp3.cpp:12-16@e894700 and src/recon/cp5.cpp:12-17@e894700 (no source derivation).
- Figures: 3- and 5-cell stencils with weights; mirrored weights for the other face (`cm.flip`).
- Code:
  - src/recon/cp3.cpp:12 — `Center3InterpImpl::reset` — cm/cp weights; :18 `left` via `call_poly3`.
  - src/recon/cp5.cpp:12 — `Center5InterpImpl::reset`.
  - src/recon/interp_simple.hpp:73, :110 — `interp_cp3`, `interp_cp5` scalar references.
  - src/recon/recon_dispatch.cpp:14 — `call_poly_cpu<N>`; :41 `call_poly_mps` (unfold+matmul); src/recon/recon_dispatch.cu:96 `call_poly_cuda` (tiled above 1024 cells, :20).
- Tests: tests/test_weno.cpp (test_weno.<build>) — `interp_cp5m_torch1..3`, `interp_cp5p_torch4` (EXPECT_NEAR 1e-6/1e-10); tests/test_weno5_cuda_line.cpp (test_weno5_cuda_line.<build>, CUDA only) — line > 1024 matches CPU, diff < 1e-12 (issue #251).
- Limits / known issues: interp_bp*/cp2/cp4/cp6/inflection helpers in interp_simple.hpp are unused by the solver.


#### 4.6 WENO3 / WENO5 (Jiang–Shu weights, eps 1e-6, optional scaling)
<sub>inventory C: Scheme: WENO3 / WENO5 (Jiang–Shu weights, eps 1e-6, optional scaling)</sub>

- Summary: nonlinear weights alpha_k = d_k/(beta_k + 1e-6)^2 (d = 2/3,1/3 or 0.3,0.6,0.1); with `scale: true`
  the stencil is normalised by its mean |value| first. Applies to density and tracers (and to all rows when
  shock: true). Switch: `type: weno3|weno5`, `scale` (default false).
- Derivations: candidate polynomials, smoothness indicators and linear weights: re-derive from
  src/recon/weno5.cpp:10-24@e894700 and src/recon/interp_impl.h:74-122@e894700 (no source derivation). Note the
  absolute (not relative) epsilon 1e-6 and its interaction with `scale`.
- Figures: three 3-cell sub-stencils inside the 5-cell stencil and the blended face value; effect of
  `scale` on a small-amplitude perturbation field.
- Code:
  - src/recon/weno3.cpp:10 — `Weno3InterpImpl::reset` — 4x3 coefficient matrix (p0,p1,beta0,beta1).
  - src/recon/weno5.cpp:10 — `Weno5InterpImpl::reset` — 9x5 matrix.
  - src/recon/interp_impl.h:35 — `interp_weno3_impl`; :74 `interp_weno5_impl` (eps at :115-117; vscale == 0 -> 0).
  - src/recon/recon_dispatch.cpp:73, :127 — MPS paths add 1e-10 to the scale (CPU/CUDA do not).
  - src/recon/recon_dispatch.cu:140, :184 — CUDA paths.
- Tests: tests/test_weno.cpp (test_weno.<build>) — scalar references (1e-10), `interp_weno3_smooth_limit` (reduces to cp3 within 1e-6), tensor vs scalar m/p sweeps (1e-6); tests/test_weno5_cuda_line.cpp — CUDA long lines < 1e-12.
- Limits / known issues: WENO overshoot of the WB perturbation at the mirror-ghost kink of a reflecting top drove the tall-column failure via the face floor (sources/canoe__tall_column_instability_TECH_REPORT.md §4); `scale` effect unexplained (issue #275).
- Discrepancies: MPS scale epsilon 1e-10 (recon_dispatch.cpp:86, :145) vs exact-zero test on CPU (interp_impl.h:50-57).


#### 4.7 PPM
<sub>inventory C: Scheme: PPM</sub>

- Summary: registered as `type: ppm` but throws at runtime. Switch: `type: ppm`.
- Derivations: none (not implemented).
- Figures: none.
- Code: src/recon/ppm.cpp:14 — `PPMInterpImpl::forward` throws "not implemented"; src/recon/interp_simple.hpp:67 `interp_ppm` returns phi.
- Tests: none.
- Limits / known issues: a card selecting ppm aborts at the first step; the report should list it as not available.


#### 4.8 Riemann solver framework, face-local frame, face-pressure output
<sub>inventory C: Scheme: Riemann solver framework, face-local frame, face-pressure output</sub>

- Summary: `RiemannSolverImpl::create` by YAML `dynamics/riemann-solver/type`; solvers project L/R primitives to
  the face-local orthonormal frame (`prim2local*_`) and fluxes back (`flux2global*_`) on the gnomonic grid; LMARS,
  HLLC and Roe also write a face pressure used by the x1 pressure source on curved grids. Switch: YAML
  `type` (default "roe" from YAML), `dir` (default "omni", shallow water).
- Derivations:
  - Face-local frame transforms on the non-orthogonal gnomonic grid: re-derive from src/coord/gnomonic_equiangle.cpp:295-413@e894700 (cross-ref cubed-sphere chapter).
  - Role of the x1 face pressure in the curved-grid pressure force: see scheme "Geometric sources, spherical-polar".
- Figures: face-local frame (n, t1, t2) on a gnomonic face with g23 != 0; data flow wl,wr -> local -> flux -> global.
- Code:
  - src/riemann/riemann_solver.cpp:11 — `RiemannSolverOptionsImpl::from_yaml`; defaults :27-28.
  - src/riemann/riemann_solver.cpp:50 — `RiemannSolverImpl::create` — roe, lmars, hllc, upwind, shallow-roe, plume-roe.
  - src/riemann/riemann_solver.cpp:39 — base `forward` = upwind of a velocity; refuses face_pressure (used by the scalar module, src/scalar/scalar.cpp:20).
  - src/coord/coordinate.hpp:309-327 — default no-op `prim2local*_`/`flux2global*_` (orthogonal grids).
  - src/hydro/hydro_forward.cpp:410-413 — x1 call passes `_face_pressure1` except for shallow water.
- Tests: tests/test_riemann.cpp (test_riemann.<build>) — `hllc_/lmars_/roe_writes_face_pressure_output`, `roe_writes_face_pressure_output_ideal_moist`; allclose(1e-10, 1e-10) against hand-coded formulas.
- Limits / known issues:
  - Only the face-pressure output is unit-tested; no flux-value test for any solver.
  - Roe does not call `prim2local*_`/`flux2global*_` (src/riemann/roe.cpp:14-59), so it is not consistent on the non-orthogonal gnomonic grid (docs/289-covariance-x3-curved.md §5 notes "roe does not project").
  - plume-roe and upwind refuse a face pressure, so they cannot be the hydro solver with x1 resolved and non-shallow EOS.
- Discrepancies:
  - Option default `type = "hllc"` (src/riemann/riemann_solver.hpp:33) vs YAML default `"roe"` (src/riemann/riemann_solver.cpp:27).
  - `from_yaml(filename, section)` tests `config[section]` but then reads `config["dynamics"]` regardless (src/riemann/riemann_solver.cpp:16-20).
  - PR #282 "remove plume eos" (sources/gh__PR_BODIES_265-284.md:248) — the EOS factory no longer has plume-eos (src/eos/equation_of_state.cpp:362-370) but `plume-roe` is still registered and plume-eos branches remain (src/hydro/hydro_options.cpp:116, src/hydro/register_forcing_modules.cpp:77): dead paths.


#### 4.9 LMARS (low-Mach approximate Riemann solver; production default in example decks)
<sub>inventory C: Scheme: LMARS (low-Mach approximate Riemann solver; production default in example decks)</sub>

- Summary: rhobar, cbar from averaged gamma and p; pbar = p_avg + (rho c)/2 (uL-uR); ubar = u_avg + (pL-pR)/(2 rho c);
  upwind by sign of ubar; enthalpy flux rho h ubar with h = W->I/rho + KE + p/rho; dry-mass flux carries
  rd = 1 - sum q. Face pressure output = pbar. Switch: `riemann-solver: {type: lmars}`.
- Derivations: linearised acoustic Riemann problem giving pbar/ubar: re-derive from src/riemann/lmars_impl.h:17-78@e894700 (no derivation in sources; the #289 draft only records that scaling the acoustic terms by 0 or 2 changes onset rates by < 2e-5, sources/study__289-covariance_derivations_draft.md §4.4).
- Figures: wave diagram with the single interface state (pbar, ubar); upwind selection of the advected state.
- Code:
  - src/riemann/lmars.cpp:30 — `LmarsSolverImpl::forward` — e = W->I/rho, gamma (aneos via W->L, WL->A), local frame, iterator, global frame.
  - src/riemann/lmars_impl.h:17 — `lmars_impl` — cbar (:36), pbar (:38) and face pressure (:40), ubar (:42), upwind (:47-77).
  - src/riemann/lmars_dispatch.cpp:77 — tensor (MPS) path writes pbar.
- Tests: tests/test_riemann.cpp `lmars_writes_face_pressure_output` (1e-10); tests/test_hydrostatic.cpp and all rest tests run LMARS.
- Limits / known issues: no positivity guard on rhobar*cbar; dissipation independent of HLLC-type wave speeds.


#### 4.10 HLLC (PVRS wave speeds)
<sub>inventory C: Scheme: HLLC (PVRS wave speeds)</sub>

- Summary: Toro PVRS middle state, shock-corrected wave speeds, contact speed am and pressure cp (clamped >= 0);
  face pressure output = cp. Switch: `type: hllc`.
- Derivations: re-derive from src/riemann/hllc_impl.h:17-130@e894700 (comment cites Toro 10.5.2; no source derivation).
- Figures: three-wave fan (bm, am, bp) with star states.
- Code: src/riemann/hllc.cpp:30 — `HLLCSolverImpl::forward`; src/riemann/hllc_impl.h:17 — `hllc_impl` (pmid :36, cp :70-72); src/riemann/hllc_dispatch.cpp:118 tensor path.
- Tests: tests/test_riemann.cpp `hllc_writes_face_pressure_output` (1e-10).
- Limits / known issues: tall-column study: HLLC reproduces LMARS to < 1% on the rest ladder (sources/canoe__tall_column_instability_TECH_REPORT.md §3f).


#### 4.11 Roe (ideal gas and ideal-moist)
<sub>inventory C: Scheme: Roe (ideal gas and ideal-moist)</sub>

- Summary: Roe averages, eigen-decomposed upwinding without an entropy fix; ideal-moist Roe gamma from mass-fraction
  weighted feps/fsig and energy offsets u0; face pressure = 1/2(pL+pR+rhobar cs (uL-uR)). Switch: `type: roe`.
- Derivations: re-derive from src/riemann/roe_impl.h:24-213@e894700 (moist gamma :87-89, face pressure :119-121).
- Figures: Roe average state and the three characteristic families plus species contact.
- Code: src/riemann/roe.cpp:14 — `RoeSolverImpl::forward`; src/riemann/roe_impl.h:24 `roe_impl`; src/riemann/roe_dispatch.cpp:153 tensor path face pressure.
- Tests: tests/test_riemann.cpp `roe_writes_face_pressure_output` and `_ideal_moist` (1e-10).
- Limits / known issues: no entropy fix; no local-frame projection (see framework).


#### 4.12 Shallow-water Roe and plume-roe
<sub>inventory C: Scheme: Shallow-water Roe and plume-roe</sub>

- Summary: shallow-roe for `shallow-water` EOS (direction mapping by `dir`); plume-roe is a Lax–Friedrichs flux of the
  plume equations. Switch: `type: shallow-roe | plume-roe`, `dir: omni|...`.
- Derivations: re-derive from src/riemann/shallow_roe_impl.h:15-78@e894700; plume-roe from src/riemann/plume_roe.cpp:14-43@e894700.
- Figures: none essential (one-line table of supported pairs EOS x solver).
- Code: src/riemann/shallow_roe.cpp:26 — `ShallowRoeSolverImpl::forward` (refuses face pressure); src/riemann/plume_roe.cpp:45.
- Tests: tests/run_shallow_xy.cmake, run_shallow_splash.cmake (reference examples, FULL_TESTS only); test_shallow_xy.py / test_shallow_splash.py.
- Limits / known issues: shallow water skips the WB reference, the x1 face pressure and the flux covariance (hydro_forward.cpp:272, :410-412, :103). plume-roe is dead (see framework).


#### 4.13 Single-valued x1 seam fluxes (process-seam averaging)
<sub>inventory C: Scheme: Single-valued x1 seam fluxes (process-seam averaging)</sub>

- Summary: at an internal x1 seam across processes, both ranks exchange the face flux slab (+ face pressure,
  + background mass flux F^R for cell gravity work) and set both to the average, so sums telescope. Same-process
  seams are not averaged (after the reference ghost exchange the two face states already agree). Switch: none;
  active when `layout.pz > 1` with a process group.
- Derivations: re-derive from src/hydro/hydro_forward.cpp:425-499@e894700 (code comment and PR #259 text only,
  sources/gh__PR_BODIES_227-259.md:645-653).
- Figures: two ranks sharing one face, each with its own flux, exchange and average; packing of flux+face pressure+F^R into one tensor.
- Code: src/hydro/hydro_forward.cpp:448-508 — seam exchange (tags 0x7720/0x7721), pack/unpack (:469-482).
- Tests: tests/test_x1_seam_split_mp.cpp (test_x1_seam_split_mp_*.<build>, torchrun 2 ranks, CMakeLists :77-87) — the x1 seam split across 2 ranks matches one block for the switch arms; tests/test_pref_local_seam.cpp (in-process, see Ch5).
- Limits / known issues: averaging masks, rather than removes, any disagreement of the two reconstructions; multi-process x1 seams of the WB reference are covered only through these split tests (docs/wb-ref4.md §12).


#### 4.14 Geometric (curvature) sources, spherical-polar; momentum flux form
<sub>inventory C: Scheme: Geometric (curvature) sources, spherical-polar; momentum flux form</sub>

- Summary: x1 momentum: centrifugal rho(v2^2+v3^2) coord_src1_i plus a pressure force built from the Riemann face
  pressures so that the NET radial pressure force is the plain difference -(p+ - p-)/dx1f (balances g h <rho> of
  the scan); x2/x3 momentum: angular-momentum form using the x1 face fluxes of IVY/IVZ weighted by
  coord_src2_i, plus cot(theta) terms with the cell pressure (p* under SNAP_FLUX_COVARIANCE). Fallback without a
  face pressure: 2 p coord_src1_i. Switch: none (geometry type `spherical-polar`).
- Derivations:
  - Metric coefficients coord_src1_i = (r+^2-r-^2)/2 / ((r+^3-r-^3)/3), coord_src2_i = dx1/((r-+r+) V_r), coord_src1_j/2_j/3_j: re-derive from src/coord/spherical_polar.cpp:78-104@e894700.
  - Plain-difference radial pressure force with face pressures in the flux: stated (not derived) in docs/x1-centroid-spherical.md §1 item (iii); re-derive from src/coord/spherical_polar.cpp:265-274@e894700.
  - Angular-momentum-conserving x1-flux form of the IVY/IVZ sources: re-derive from src/coord/spherical_polar.cpp:286-307@e894700 (no source).
  - Rest balance of the lateral rows with the same cell pressure in flux and source: exists docs/289-covariance-x3-curved.md §4A.3 (proof) and study copy sources/study__289-allrows_derivation.md §4.2; executable docs/rest_balance.py.
- Figures: radial cell with A+ p+, A- p-, the 2p/r source and the net -(p+ - p-)/h; polar cell showing the sin(theta) face areas and the cot(theta) source.
- Code:
  - src/coord/spherical_polar.cpp:17 — `radial_centers` — x1v = volume (r^2) centroid.
  - src/coord/spherical_polar.cpp:178, :185, :193, :200 — `face_area1/2/3`, `cell_volume` (exact).
  - src/coord/spherical_polar.cpp:224 — `SphericalPolarImpl::forward` — src1 (:243-244), centroid-exact branch (:252-264), plain-difference branch (:265-274), fallback (:276), IVY sources (:281-290), IVZ sources (:292-307).
- Tests:
  - tests/test_coordinate.cpp `spherical_polar_radial_source_uses_face_pressure_in_x1_momentum`, `spherical_polar_radial_source_preserves_face_pressure_gradient` (allclose 1e-6).
  - tests/test_flux_covariance_rows.py (rest arm, spherical one block; REST_TOL 1e-9 in |v|/c_s), tests/test_flux_covariance_seams.py (x3-disabled rest gating).
- Limits / known issues: the lateral source multiplies the volume-average pressure where the exact source wants the area average; rest balance holds because flux and source share the same error (docs/289-covariance-x3-curved.md §4C item 1).


#### 4.15 Geometric sources, gnomonic cubed sphere; exact cell volume and solid angle
<sub>inventory C: Scheme: Geometric sources, gnomonic cubed sphere; exact cell volume and solid angle</sub>

- Summary: same face-pressure plain-difference x1 force; src2/src3 with x_ov_rD, y_ov_rC metric coefficients and
  the non-orthogonal cosine terms; exact gnomonic solid angle and exact radial volume (unconditional since PR #293).
  Switch: none (`gnomonic-equiangle`).
- Derivations:
  - Exact solid angle and radial integral: exists docs/289-covariance-x3-curved.md §8.1-8.4.
  - Source terms with g23 != 0: re-derive from src/coord/gnomonic_equiangle.cpp:415-473@e894700 (no source derivation; cross-ref cubed-sphere chapter).
- Figures: gnomonic cell corner-sum solid angle; covariant vs contravariant components at a face.
- Code: src/coord/gnomonic_equiangle.cpp:128-137 (solid angle), :207 `face_area1`, :219 `cell_volume`, :142-145 `x_ov_rD_kji`/`y_ov_rC_kji`, :415 `forward` (src1 :443-460, src2 :463-465, src3 :468-470); :36 x1v = arithmetic mid-radius.
- Tests: tests/test_hydrostatic.cpp (test_hydrostatic.<build>) — six-panel isentropic shell, non-hydrostatic 0, 100 steps, max |v1| < 1e-8 (fixed constant); tests/test_cubed_sphere_cell_volume.py; tests/test_coordinate.cpp `radial_source_uses_face_pressure_in_x1_momentum` (1e-8), `radial_source_preserves_face_pressure_gradient` (1e-6).
- Limits / known issues: x1v is the mid-radius on gnomonic, so a cell-average reading and the gnomonic delta are consistent only if ICs are cell averages (docs/289-covariance-x3-curved.md §4C item 2); SNAP_X1_CENTROID_EXACT does nothing on this grid (docs/x1-centroid-spherical.md §7).
- Discrepancies: PR #293 says the switch-off bitwise property does not hold on gnomonic because the volume change is unconditional (sources/gh__PR_BODIES_285-293.md:240-256) — consistent with code; record for the reader.


### 4.B Face-average corrections at $O(\Delta x_1^2)$


#### 4.16 x2/x3 face-flux covariance and centroid correction (SNAP_FLUX_COVARIANCE, #289/#293)
<sub>inventory C: Scheme: x2/x3 face-flux covariance and centroid correction (SNAP_FLUX_COVARIANCE, #289/#293)</sub>

- Summary: added to the x2/x3 Riemann flux, per row: energy sigma1^2 rho D1[h] D1[u_n] - delta D1[(I+p) u_n];
  tracer sigma1^2 rho D1[u_n] D1[q] - delta D1[rho u_n q]; dry mass -sum(tracer cov) - delta D1[rho u_n rd];
  momentum -delta D1[rho u_n u_v] in the face-local frame, plus -delta D1^p[p] on the normal row, mirrored as
  p* = p - delta D1^p p in the lateral geometric source (gated per direction). sigma1^2 = face_moment2_x1,
  delta = face_centroid_shift_x1 (0 in Cartesian). Switch: env `SNAP_FLUX_COVARIANCE`, default off
  (src/hydro/hydro.cpp:208-218).
- Derivations:
  - Covariance identity and Cartesian dz^2/12 term: exists docs/289-covariance-x3-curved.md §2.1-2.6, §2.10; Cartesian origin also sources/gw__X2COV_DERIVATION_x2cov.md §1-3 and issue #289 (sources/gh__ISSUE_THREADS_251-294.md:851-924).
  - Curved face moment sigma_c^2 = (h^2/12)(1-h^2/(12 rbar^2)): exists docs/289-covariance-x3-curved.md §2.7-2.8.
  - Centroid term delta = r_v - r_c: exists docs/289-covariance-x3-curved.md §2A.1-2A.5 (scripts docs/verify_centroid_term.py, docs/verify_exact_curved.py).
  - Favre (density-weighted) cell values, all rows, energy in h: exists docs/289-covariance-x3-curved.md §1A, §4A.1, §4B, §4C.2 (docs/allrows_quadrature.py, docs/energy_row.py); independent: sources/deriv__issue289_moist_covariance_verifier.md §2-5, sources/gw__U3_DERIVATION_moist_x2_flux.md §2-5, sources/study__289-allrows_derivation.md §2.
  - Exact rest balance with p* in flux and source; one-sided D1^p at the first/last interior cell: exists docs/289-covariance-x3-curved.md §4A.3, §4B.2, §4C.3 (docs/rest_balance.py, docs/onesided.py).
  - Telescoping: exists docs/289-covariance-x3-curved.md §3.1, §4A.4, §4C.4.
  - x3 direction: exists docs/289-covariance-x3-curved.md §3.
- Figures:
  - x2 face spanning one x1 cell: point flux varying along x1 vs the flux evaluated from the cell state; covariance as the area under the product.
  - Radial cell with volume centroid r_v (r^2 weight) and face area centroid r_c (r weight); delta between them.
  - Rest-balance cartoon: p* entering both the normal-momentum face flux and the cot(theta) source.
- Code:
  - src/hydro/hydro.cpp:208 — `HydroImpl::flux_covariance` — switch.
  - src/hydro/hydro_forward.cpp:63 — `HydroImpl::_flux_covariance` — guards n1<3 / shallow water (:101-103), wbar and h (:105-109), local-frame u_n (:115-120), sigma^2 (:123), delta (:134), energy (:177), tracers and dry (:179-186), momentum centroid (:191-194), normal-row p* (:197-198), back to global frame (:199-203).
  - src/hydro/hydro_forward.cpp:23 — `d1_pressure` — centred, one-sided at il/iu.
  - src/hydro/hydro_forward.cpp:601-621, :624-644 — x2/x3 call sites (built before the solver, added after).
  - src/hydro/hydro_forward.cpp:733-755 — p* in the geometric source, per-direction gate (cov2/cov3).
  - src/coord/coordinate.cpp:442, :446, :461, :467 — `face_moment2_x1`, `radial_face_moment2_`, `face_centroid_shift_x1`, `radial_face_centroid_shift_`; src/coord/spherical_polar.cpp:213, :219; src/coord/gnomonic_equiangle.cpp:229, :237.
- Tests:
  - tests/test_horizontal_flux_covariance.py (test_horizontal_flux_covariance_python; env SNAP_GRAVITY_WORK_RADIAL_EXACT=0) — Cartesian roll: off eps_eff nz^2 in [-0.32,-0.20], on |.| < 0.04, unset == "0" bitwise, E+PE closure 1e-12 over 50 steps; band from the #289 prediction -0.235/nz^2.
  - tests/test_flux_covariance_rows.py (test_flux_covariance_rows_python) — rest (REST_TOL 1e-9), uniform tracer (1e-13), offset invariance (1e-10), Cartesian limit vs CART_REF within 2e-3 (CART_REF recorded with the x1 wall continuation of the default reference).
  - tests/test_flux_covariance_seams.py (test_flux_covariance_seams_python) — six-panel conservation drift < 1e-12 over 10 steps; x3-disabled rest gating; on/off differ > 1e-13.
  - tests/test_radial_face_moments.cpp (test_radial_face_moments.<build>) — exact rationals, 1e-13/1e-14 relative.
- Limits / known issues:
  - Velocity-squared covariances and the pressure Hessian J excluded (docs/289-covariance-x3-curved.md §4B.1, §4C.3), with a caution that the KE part is not negligible in general (§4C item 3).
  - Transverse in-face covariance dropped (§2.9); one-sided D1^p is first order on one boundary row.
  - Momentum row is not a pure divergence; no discrete angular momentum statement (§4C.4).
  - Cylindrical not covered (§5).
- Discrepancies:
  - docs/289-covariance-x3-curved.md §5 still lists the superseded energy row `(I+p) D1 ln(p/rho) D1 u_n`; code uses `rho D1[h] D1[u_n]` (hydro_forward.cpp:176-177), as §4B states.
  - Older names: `SNAPY_X2COV=<factor>` (scalar factor, sources/gw__X2COV_DERIVATION_x2cov.md §4) vs code boolean `SNAP_FLUX_COVARIANCE`.
  - PR #293 body cites `hydro.cpp:188` and `hydro_forward.cpp:597-628`; at dae902b these are hydro.cpp:208 and hydro_forward.cpp:724-755.
  - The committed doc and source copies name individual contributors and chat threads; strip in the report.


#### 4.17 x1 rho-w mass-flux covariance (SNAP_X1_MASS_COVARIANCE)
<sub>inventory C: Scheme: x1 rho-w mass-flux covariance (SNAP_X1_MASS_COVARIANCE)</sub>

- Summary: inside the WB x1 path only, the cell velocity handed to the reconstruction is w_c - (dx1f^2/12) rho_1 w_1 / rho
  (centred derivatives over x1v; rho_1 one-sided second order in the first/last cell at a reflecting wall; ghost w
  refilled as odd mirror), and the full velocity is restored after reconstruction. Rest unchanged (w_1 = 0).
  Switch: env `SNAP_X1_MASS_COVARIANCE`, default off (src/hydro/hydro_forward.cpp:39-47).
- Derivations:
  - The Favre offset w_c = <w> + dz^2/12 rho_z w_z/rho and the extra face mass flux: exists docs/curved-gravity-work-weight.md §11.4 (short) and sources/study__289-covariance_derivations_draft.md §4.1 (with the entropy effect, small in the cell form, harmless in the face form).
  - Wall closure (one-sided rho_1, odd ghost refill) and the use of the Cartesian dx1f^2/12 on curved grids: re-derive from src/hydro/hydro_forward.cpp:315-344@e894700 (commit e04b783 message only).
- Figures: column with rho decreasing, w varying: cell Favre velocity vs cell-average w; corrected velocity profile with mirrored ghosts.
- Code: src/hydro/hydro_forward.cpp:39 — `x1_mass_covariance`; :51 `d1_centred`; :324-353 correction; :361 restore.
- Tests: none in tests/ (grep: the switch appears only in hydro_forward.cpp and docs/curved-gravity-work-weight.md).
- Limits / known issues: not applied when the WB path is off (no gravity, shallow water); uses dx1f^2/12 (Cartesian moment) even on spherical-polar; the doc's "ONSET PLACEHOLDER" is unfilled — no evidence of effect at dae902b.


---

<a id="ch5"></a>
## Chapter 5. Hydrostatic and well-balanced treatment

The well-balanced $x_1$ reconstruction about a hydrostatic reference, its kernel, the wall clamp and continuation, seam continuity, the hydrostatic-split mode, `balance_column`, the fourth-order reference (`SNAP_WB_REF4`), the $r^2$-exact $x_1$ maps (`SNAP_X1_CENTROID_EXACT`) and what is left of the $1/R$ term. No separate $1/R$ chapter: the remainder is the last section here, with its table rebuilt from an in-snapy run (ISSUES.md item 5). The WB-reference numbers are re-measured with `tests/test_wb_ref4_order.py` at the pin (ISSUES.md item 3).

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: how a resting stratified column stays at rest in the x1 sweep: the hydrostatic reference (face
pressure scan, cell pressure, density reference), its wall closure and seam continuity, the reconstructed
perturbations and their floors, the 4th-order reference (SNAP_WB_REF4), the r^2-exact spherical maps
(SNAP_X1_CENTROID_EXACT), the hydrostatic (non-hydrostatic < 1) mode, the projection of initial columns onto the
discrete balance (balance_column), and what is left on curved grids (the 1/R remainder).

Merge/split proposal: keep as one chapter, ordered base reference -> wall closure -> seams -> floors ->
balance_column -> SNAP_WB_REF4 -> SNAP_X1_CENTROID_EXACT -> 1/R remainder. The 1/R remainder needs its table
rebuilt from an in-snapy run (ISSUES.md item 5); if the report has a separate "1/R" chapter, move that scheme
there and keep a one-paragraph pointer here. The isentropic-ghost / zero-gradient-wall legacy routines
(`_revise_x1*`) go in a short "legacy and dead paths" box.

</details>


#### 5.1 Well-balanced x1 reconstruction (perturbation about a hydrostatic reference)
<sub>inventory C: Scheme: Well-balanced x1 reconstruction (perturbation about a hydrostatic reference)</sub>

- Summary: subtract (pref, dref) from (p, rho), fill even-parity perturbation ghosts at physical non-outflow
  walls, reconstruct the perturbation (floor=false), restore psf/dsf at faces; positivity fallback: pressure ->
  psf, density -> adjacent cell density (edge-replicated shift). Engaged whenever grav1 != 0, the state has a
  pressure row, and the EOS is not shallow water (also under x1 decomposition). Switch: implicit (gravity on);
  no off switch.
- Derivations:
  - Base pipeline and exact rest balance (p' = const => LMARS face pressure psf + c, momentum-flux difference
    g rho dz cancels gravity): exists docs/wb-ref4.md §1, §6; spec form sources/gw__NEXTPR_spec_wbref_exact.md §1, §4.5.
  - Face-density offset of the base reference O(dz^2): exists docs/wb-ref4.md §2 (docs/wb_ref4_weights.py check 4).
  - Why the density reference must be smoothed (a reference equal to the local state absorbs the entropy mode):
    measured/argued in sources/canoe__tall_column_instability_TECH_REPORT.md §3d, §4-5 (not a derivation; re-derive
    the degeneracy rho'/rho = p'/p from src/hydro/hydro_ref_x1_impl.h:74-108@e894700).
  - Positivity fallback choice (adjacent density, not dsf): evidence only (test_face_floor; PR #221 body); describe
    from src/hydro/hydro_forward.cpp:353-377@e894700.
- Figures:
  - Column: cell averages, reference staircase, perturbation, WENO of the perturbation, restored face values.
  - Even-parity perturbation ghosts at a reflecting wall (p', rho' mirrored) vs odd velocity.
  - Floor fallback at the top wall: dl <= 0 replaced by the cell below (rho_below) and dr by the cell itself.
- Code:
  - src/hydro/hydro_forward.cpp:271-272 — `wb_x1` gate.
  - src/hydro/hydro_forward.cpp:297 — `_hydro_ref_x1(wx1)`; :301-302 subtraction; :309-321 even-parity ghosts (physical, non-outflow only).
  - src/hydro/hydro_forward.cpp:357 — `precon1->forward(wx1, DIM1, /*floor=*/false)`.
  - src/hydro/hydro_forward.cpp:366-369 — pressure restore, fallback psf_lo; :371-386 density restore, fallback rho_below / density.
  - src/hydro/hydro_forward.cpp:388-392 — non-WB x1 path (shallow water etc.).
- Tests:
  - tests/test_face_floor.cpp (test_face_floor.<build>; also _wb_ref4 and _x1_centroid arms, CMakeLists :93-101) — dipped column: lower-face mass flux 4.07888 within 1e-3, dipped-face |mass flux| < 1e-9 and momentum > 0.03042 (switch off); pinned switched values; unresolved column flux 2.83191e-8 within 1e-5 relative; CUDA parity 1e-5.
  - tests/test_hydrostatic.cpp — cubed-sphere rest < 1e-8 (see Ch4).
  - tests/test_wb_wall_corner.cpp (test_wb_wall_corner.<build>) — balanced polytrope with viscosity keeps u2 and |v|/c_s <= 1e-12 over ten steps; x2 split equals one block exactly.
- Limits / known issues:
  - x2/x3 reconstruction has no WB treatment (hydro_forward.cpp:559, :571).
  - floor=false drops density/pressure floors but tracer clamp_min(0) still applies (src/recon/reconstruct.cpp:153-155).
  - Moist columns: no reference meets the BF02 floor; reference choice is a parked study (issue #275); no YAML key to choose the form (issue #281).
- Discrepancies: tall-column report §5 says the face reference averages two smoothed values at every face; code uses the cell's own smoothed value at array index 0 (src/hydro/hydro_ref_x1_impl.h:195-198), as the report's own review banner and src/hydro/balance_column.hpp:94-97 note.


#### 5.2 Hydrostatic reference kernel — face-pressure scan, cell pressure, density reference ("smooth5")
<sub>inventory C: Scheme: Hydrostatic reference kernel — face-pressure scan, cell pressure, density reference ("smooth5")</sub>

- Summary: top-down scan psf_{i-1/2} = psf_{i+1/2} + g rho_i dx1f_i from a top anchor (block top: p_top exp(-g dz/2 / (p/rho)_top); x1-split: anchor relayed from the block above); cell pressure pref = six-face quintic cell average (11,-93,802,802,-93,11)/1440 on uniform grids with one-sided wall rows and a [lo,hi] guard, log-mean dp/ln(lo/hi) on non-uniform grids; dref = pref * B(rho/p), dsf = psf_lo * mean of two smoothed values, B = (1,4,6,4,1)/16. Uniformity: relative spread of dx1f < 1e-10. Switch: none (always with WB).
- Derivations:
  - Scan = discrete hydrostatic balance; six-face quadrature O(dz^6); binomial bias dz^2/2 R'': exists docs/wb-ref4.md §1, §2, §6; wall-row weights in sources/gw__NEXTPR_spec_wbref_exact.md §1(b).
  - Six-face interior weights and the one-sided wall rows w6e: stated (not derived) in docs/wb-ref4.md §1 and sources/gw__NEXTPR_spec_wbref_exact.md §1(b); docs/wb_ref4_weights.py does not check them; re-derive from src/hydro/hydro_ref_x1_impl.h:141-180@e894700.
  - Log-mean exactness for an isothermal cell: stated docs/wb-ref4.md §5; re-derive from src/hydro/hydro_ref_x1_impl.h:181-186@e894700.
  - Top anchor half-cell isothermal extrapolation: re-derive from src/hydro/hydro_ref_x1_impl.h:31-38@e894700.
- Figures: column of faces with the scan arrow from the top anchor down; six-face stencil and its one-sided wall variants; the binomial window with its clamped/continued edge.
- Code:
  - src/hydro/hydro.cpp:484 — `HydroImpl::_hydro_ref_x1` — anchor relay (:506-514), uniform test (:516-522), kernel call (:535-537), anchor pass (:559).
  - src/hydro/hydro_ref_x1_impl.h:23 — `hydro_ref_x1_scan_impl` (anchor :31-38, downward :42-49, ghosts upward :52-59, floor at numeric_limits::min).
  - src/hydro/hydro_ref_x1_impl.h:111 — `hydro_ref_x1_cell_impl` — thin/fits guards (:124-135), w6 (:141), w6e (:158-163), non-uniform log-mean (:181-186), dref/dsf (:199-200).
  - src/hydro/hydro_ref_x1_impl.h:87 — `hydro_ref_x1_rop_smooth` — binomial (:107).
  - src/hydro/hydro_dispatch.cpp:14, :37 — CPU and MPS (tensor) paths; src/hydro/hydro_dispatch.cu:33 CUDA.
- Tests:
  - tests/test_hydro_ref_x1.cpp (test_hydro_ref_x1.<build>) — CPU vs tensor reference (2e-12 double, 2e-5 float); clamp keeps interior free of ghosts (torch::equal) and its control; thin block; CUDA vs CPU.
  - tests/test_hydro_options.cpp `wb_wall_clamp_ships_enabled`, `wb_wall_clamp_reaches_the_x1_reference` (two settings differ beyond 1e-13).
- Limits / known issues:
  - Non-uniform x1: the log-mean branch is a different operator, exact only for isothermal cells; rest on stretched grids is not round-off unless projected (issue #280; #250 T4 rest residual 7.37e-4 for every density form, sources/gh__ISSUE_THREADS_138-250.md:1240-1330).
  - rho/p divide has no positivity guard (issue #250 §2; T4 fault injections).
- Discrepancies: issue #280 says the reference's face interpolation uses fixed rationals on stretched grids; in code the six-face rationals are used only when the block is uniform (hydro.cpp:516-522), otherwise the log-mean (hydro_ref_x1_impl.h:181-186). The reconstruction weights are uniform-spacing on all grids.


#### 5.3 Wall clamp and the wall continuation of the default reference (wb-wall-clamp, linear/ln closure)
<sub>inventory C: Scheme: Wall clamp and the wall continuation of the default reference (wb-wall-clamp, linear/ln closure)</sub>

- Summary: with `wb-wall-clamp` on, no reference stencil reads a wall ghost: one-sided six-face rows in the two wall
  cells, and past the wall the binomial continues rho/p from the two owned wall cells, linearly r0 + k(r0 - r1) when
  r1 <= r0, ln-linearly r0 (r0/r1)^k when r1 > r0, non-positive -> r0; restores O(dz^2) at faces 0-2 (repeating
  the wall cell was O(dz)). Switch: YAML `dynamics/wb-wall-clamp` (src/hydro/hydro_options.cpp:57), default true
  (src/hydro/hydro.hpp:54).
- Derivations:
  - The repeated wall cell is first order (23/32, 7/32, 1/32 a): exists docs/wb-ref-wall.md §3.
  - The linear/ln closure and its bounds: exists docs/wb-ref-wall.md §4 (no .py check; the order table is in tests/test_wb_ref_wall.cpp).
  - Clamp rationale (ghosts are not a hydrostatic continuation): PR #221 body (statement, sources/gh__PR_BODIES_220-226.md:121-123); property tests in test_hydro_ref_x1.
- Figures: wall cell, first ghost, true continuation vs repeated value; the branch choice (rising vs falling rho/p) with its bounded interval.
- Code:
  - src/hydro/hydro_ref_x1_impl.h:69 — `hydro_ref_x1_wall_rop`.
  - src/hydro/hydro_ref_x1_impl.h:87-108 — `hydro_ref_x1_rop_smooth` with ext_lo/ext_hi.
  - src/hydro/hydro_ref_x1_impl.h:132-135, :189-192 — clamp gates and jlo/jhi/ext flags.
  - src/hydro/hydro_dispatch.cpp:166 — same rule in the tensor path.
- Tests:
  - tests/test_wb_ref_wall.cpp (test_wb_ref_wall.<build>) — `order_table`; `faces_next_to_the_walls_are_second_order`: observed order nz 32->64 >= 1.7 for dsf, rho_L, rho_R at faces 1-2, and wall-face errors <= 1.5 x interior max (tolerances from docs/wb-ref-wall.md §4 table); CUDA vs CPU <= 1e-13.
  - tests/test_face_floor.cpp unresolved-column flux 2.83191e-8 (the closure value, docs/wb-ref-wall.md §4).
  - tests/run_straka_redo.cmake (test_straka_redo) — CFL 1.6 robustness, <= 5 redos per step (docs/wb-ref-wall.md §5).
- Limits / known issues: continuation is in index, not physical spacing (non-uniform not covered); MPS path not run (docs/wb-ref-wall.md §5 "Not covered"); straka CFL 1.6 evidence is marginal and does not separate references at eps 1e-4.
- Discrepancies: docs/wb-ref-wall.md §1 line references are at 37dce4e (`:74`, `:159-160`, `:161-167`, hydro_forward `:276-292`); at dae902b they are hydro_ref_x1_impl.h:69-108, :189-200 and hydro_forward.cpp:309-321. docs/wb-ref4.md §1-2 still describe the kernel binomial as "edge replicated at a clamped wall" (pre-closure).


#### 5.4 Reference continuity across x1 seams (anchor relay and ghost-row exchange)
<sub>inventory C: Scheme: Reference continuity across x1 seams (anchor relay and ghost-row exchange)</sub>

- Summary: the block owning x1-outer anchors at the domain top; each block below receives the running seam-face
  pressure and passes on its bottom-face pressure (serial top-down relay, in-process through a board, remote
  through the process group); then (pref, dref) ghost rows are overwritten with the neighbour's interior rows
  (SNAP_WB_REF4 cell part before, face part after the exchange). Switch: none (x1 split, non-periodic, pz > 1).
- Derivations: re-derive from src/hydro/hydro.cpp:509-645@e894700 (PR #259 body and code comments only; issue #254 thread).
- Figures: stack of x1 blocks with the anchor arrow passing down and ghost rows copied across each seam.
- Code: src/hydro/hydro.cpp:506-514 (`take_x1_anchor`), :559 (`pass_x1_anchor`), :574-621 (ghost-row exchange, tags 0x7717/0x7718); src/layout/layout.cpp:879, :907.
- Tests:
  - tests/test_pref_local_seam.cpp (test_pref_local_seam.<build>) — `local_blocks_restart_the_reference_at_the_seam` (pref under seam equal to one block within 1e-6), `in_process_split_matches_one_block_after_200_steps` (relative state difference <= 1e-12; source PR #259).
  - tests/test_x1_seam_split.cpp arms (Ch5 switches) and tests/test_x1_seam_split_mp.cpp.
- Limits / known issues: the relay is serial along the column (latency grows with nb1); periodic x1 not relayed.
- Discrepancies: test_pref_local_seam.cpp header comments still say "RED on main ... This test does not fix it"; at dae902b both tests are expected to pass (PR #259).


#### 5.5 Hydrostatic mode (non-hydrostatic < 1): gravity replaced by the discrete pressure gradient
<sub>inventory C: Scheme: Hydrostatic mode (non-hydrostatic < 1): gravity replaced by the discrete pressure gradient</sub>

- Summary: vertical force = nh * rho g (const-gravity forcing) + (1 - nh) * rho_grav, with rho_grav = (pL_{i+1/2} - pR_{i-1/2})/dx1f
  from the cell's own reconstructed face pressures (and the same energy work); under SNAP_X1_CENTROID_EXACT the
  r^2 operator (A pL - A pR)/V - S_i. Switch: YAML `forcing/const-gravity/non-hydrostatic` in [0,1], default 1
  (src/forcing/const_gravity.cpp:25-26).
- Derivations: cancellation at rest against the plain-difference pressure force: stated docs/x1-centroid-spherical.md §4 (last part); otherwise re-derive from src/hydro/hydro_forward.cpp:389-397, :515-539, :901-906@e894700 and src/forcing/const_gravity.cpp:45-51@e894700.
- Figures: cell with face pressures pL(top), pR(bottom) and the replaced gravity arrow.
- Code: src/hydro/hydro_forward.cpp:399-406 (rho_grav), :524-548 (centroid-exact form), :911-915 (applied to IVX and IPR); src/forcing/const_gravity.cpp:45 `ConstGravityImpl::forward`.
- Tests: tests/test_hydrostatic.cpp (nh 0); tests/test_x1_centroid_rest.py (nh 1 and 0); tests/test_x1_seam_split.cpp (both).
- Limits / known issues: interaction with gravity-work forms is in the gravity-work chapter (original_gravity_work, hydro_forward.cpp:859-866).


#### 5.6 balance_column — projection of a ghost-free column onto the scheme's discrete balance
<sub>inventory C: Scheme: balance_column — projection of a ghost-free column onto the scheme's discrete balance</sub>

- Summary: iterate p_i <- pref_i(p) + C, rho_i <- p_i/(p/rho)_0 at fixed p/rho (fixed T for ideal mixtures), gauge C
  read at the top cell, until max|p' - C|/(rho g dz) < rtol (default 1e-10, max_iter 120); applies the switched cell
  pressure under SNAP_WB_REF4 on non-uniform grids; requires wall_clamp, nx1 >= 5, positive p and rho; under
  SNAP_X1_CENTROID_EXACT only geometry "cartesian". Switch: API (C++ and Python `balance_column`), used by IC
  builders (examples/bryan.cpp:211).
- Derivations: fixed-point property and the transfer of pref from a ghost-free column to a clamped block: described in the header src/hydro/balance_column.hpp:12-106 (not a derivation; no convergence proof); re-derive from src/hydro/balance_column.cpp:15-109@e894700.
- Figures: residual vs sweep; column moved by the free gauge C (top fixed).
- Code: src/hydro/balance_column.cpp:15 — `balance_column` (clamp check :30, centroid check :35, nc1 >= 5 :47, uniform test :66-68, ref4 :73-79, loop :85-104, gauge :92); python/csrc/pyhydro.cpp:49 binding.
- Tests:
  - tests/test_balance_column.cpp (test_balance_column.<build>, plus _wb_ref4 and _x1_centroid arms) — ghost-free column reproduces the block's own pref/dref bitwise (dsf except bottom cell); without clamp they disagree; marched column comes out at rest (residual < 1e-10); last allowed update can converge (issue #278 item 5 / PR #279); T and other channels fixed (1e-14); fixed point; thin-block column independence; refusals; centroid switch implies ref4 predicate; moist column; centroid switch balances only Cartesian.
  - tests/run_bryan_balance_ic.cmake (test_bryan_balance_ic) — moist IC converges, capped run reports the cap error, dry case does one projection.
- Limits / known issues: the balanced column moves by a free constant (2.5e-4 to 1.2e-2 of p quoted in the header); per-block uniform classification must match; moist callers must iterate with saturation adjustment.


#### 5.7 SNAP_WB_REF4 — fourth-order, cell/face-consistent density reference (and non-uniform cell pressure)
<sub>inventory C: Scheme: SNAP_WB_REF4 — fourth-order, cell/face-consistent density reference (and non-uniform cell pressure)</sub>

- Summary: dref = pref * F(rho/p), F = (-1,4,10,4,-1)/16 with cubic extrapolation past clamped walls; dsf = derivative of the
  quartic primitive through five faces ((-1,7,7,-1)/12 interior, physical spacing); on non-uniform grids pref = 3-point
  Gauss average of the cubic through four face pressures; range guards (margin 1e-10), resolution flag |ln(lo/hi)| > 0.5
  dilated by 2; psf never changed. Cell part before the seam exchange, face part after. Requires nghost >= 3.
  Switch: env `SNAP_WB_REF4`, default off, implied by SNAP_X1_CENTROID_EXACT (src/hydro/wb_ref4.cpp:83-95);
  nghost check src/hydro/hydro.cpp:96-103.
- Derivations:
  - O(dz^2) base offset, F moments, cubic wall values and the identity (Fr) = r in the end cells, quartic-primitive face weights, non-uniform pressure, rest balance unchanged, guards: exists docs/wb-ref4.md §2-7, checked by docs/wb_ref4_weights.py (checks 1-6).
  - Oracle (neutral polytrope, N^2_eff, no diagnostic floor): exists docs/wb-ref4.md §8; spec sources/gw__NEXTPR_spec_wbref_exact.md §5, §7.
- Figures: F vs B frequency response; wall cubic extrapolation of two virtual cells; five-face primitive stencil for the face density; N^2_eff nz^2 vs nz (off flat, on falling).
- Code:
  - src/hydro/wb_ref4.cpp:83 — `wb_ref4_enabled`; :97 `wb_ref4_stencils` (usable :114, F :124, E :126, non-uniform pressure :169-193, face weights :195-221, counted :226-229); :233 `wb_ref4_cells` (flag :239-243); :276 `wb_ref4_faces`; constants kMargin :23, kMaxLogDrop :25.
  - src/hydro/hydro.cpp:547-556 (cell part), :626 (face part); src/hydro/balance_column.cpp:73-90.
- Tests:
  - tests/test_wb_ref4_order.py (test_wb_ref4_order_python; CUDA twin) — 1 and 3 e-folds, nz 32/64/128: on, order >= 2.75 over both doublings; off, < 2.5 at the last doubling (thresholds set below the measured 2.92-2.99 on and 2.07-2.32 off, docs/wb-ref4.md §9).
  - tests/test_x1_seam_split.cpp `wb_ref4_flag_at_the_seam_split_matches_one_block` (ctest test_x1_seam_split_wb_ref4, gap <= 1e-13; nghost < 3 raises), `wb_ref4_gravity_0_nghost_1_steps`.
  - test_balance_column_wb_ref4, test_face_floor_wb_ref4 (pinned switched fluxes, e.g. -1.19257e-7 within 1e-3 relative).
- Limits / known issues: order-3 wall band of unidentified source (docs/wb-ref4.md §9); thresholds not derived (§7); stretched-grid dynamics untested, multi-species untested, multi-process seams only via the in-process split (§12); ISSUES.md item 3: the spec numbers rest on c5b810d and the §9 table must be re-measured with tests/test_wb_ref4_order.py at dae902b.
- Discrepancies: spec names the switch `SNAPY_WB_REF_EXACT` (sources/gw__NEXTPR_spec_wbref_exact.md:3) vs code `SNAP_WB_REF4`; docs/wb-ref4.md "Scope: Cartesian-exact; r^2 extension separate" is superseded on spherical-polar by SNAP_X1_CENTROID_EXACT; docs/wb-ref4.md §9 is at nz 64/128/256, the ctest at 32/64/128; the sources copy (fdf895b) lacks the seam-flag guard text.


#### 5.8 SNAP_X1_CENTROID_EXACT — r^2-exact x1 maps on spherical-polar
<sub>inventory C: Scheme: SNAP_X1_CENTROID_EXACT — r^2-exact x1 maps on spherical-polar</sub>

- Summary: (i)+(ii) every x1 input converted from r^2 means to plain means by a five-cell stencil exact to degree 4 (a view;
  primitives unchanged; seam ghosts from the neighbour), so WENO, the scan and the reference see plain means; implies
  SNAP_WB_REF4; (iii) the x1 pressure source S_i = (2/V) int r p~ dr with p~ the quintic through six face pressures, so the
  net force is the r^2 mean of -dp~/dr; hydrostatic mode uses the same operator. Spherical-polar only; nghost >= 3.
  Switch: env `SNAP_X1_CENTROID_EXACT`, default off (src/coord/x1_centroid.cpp:92-102).
- Derivations: exists docs/x1-centroid-spherical.md §1-5 (defect delta = h^2/(6 rbar); conversion weights; Leg W on plain means; pressure source by parts; rest balance and oracle), checked by docs/verify_x1_centroid.py; background in sources/study__next-1overR_README.md §0-3.
- Figures: radial cell with mid-radius, r^2 centroid x1v and plain mean; five-cell conversion window (centred, wall one-sided, seam ghosts from neighbour); six-face window for S_i extending two faces past a seam.
- Code:
  - src/coord/x1_centroid.cpp:92 `x1_centroid_exact_enabled`; :104 `x1_plain_mean_stencils` (moments rhs :145); :157 `x1_plain_means` (mirrored ghosts with parity); :184 `x1_pressure_source_stencils`; :224 `x1_pressure_source`.
  - src/hydro/hydro_forward.cpp:280-294 (plain-mean view + `_x1_ghost_rows`), :512-517 (face-pressure ghost rows), :524-548 (hydrostatic-mode operator).
  - src/coord/spherical_polar.cpp:252-264 (source); src/hydro/hydro.cpp:251 `_x1_ghost_rows`; src/hydro/wb_ref4.cpp:94 (implies WB_REF4).
- Tests:
  - tests/test_x1_centroid_rest.py (test_x1_centroid_rest_python; CUDA twin) — linear-density column of r^2 means, r0 = 5 and 1000, explicit and vertically implicit, nh 1 and 0: on, force < 1e-10 interior and walls; off, > 1e-8 at r0 = 5 (measured on ~1e-14, off 2.4e-5, docs/x1-centroid-spherical.md §5).
  - tests/test_x1_seam_split.cpp `centroid_exact_split_matches_one_block` (ctest test_x1_seam_split_x1_centroid; gap <= 1e-13 after 20 steps) and test_x1_seam_split_mp_x1_centroid.
  - test_balance_column_x1_centroid, test_face_floor_x1_centroid.
- Limits / known issues: does nothing on gnomonic (x1v is the mid-radius there) or Cartesian beyond implying WB_REF4; ratios of means (Favre w, T, rho/p) remain non-exact, giving the O(h^2/R) remainder (§6); balance_column cannot balance a spherical column under the switch.
- Discrepancies: sources/deriv__x1-centroid-spherical.md (1cf0bbc) says "nothing in wb_ref4.cpp changes" and lacks the seam ghost exchange; at dae902b the switch implies WB_REF4 via `wb_ref4_enabled()` and seam ghosts are exchanged.


#### 5.9 The 1/R remainder on spherical-polar (what is left after the corrections)
<sub>inventory C: Scheme: The 1/R remainder on spherical-polar (what is left after the corrections)</sub>

- Summary: after SNAP_FLUX_COVARIANCE (x3 term) and SNAP_X1_CENTROID_EXACT, the residual 1/R content of the one-step
  eps_eff nz^2 harness is an O(h^2/R) term from reconstructing the Favre velocity <rho w>/<rho> as a plain mean; plus
  the face-form gravity work / curv_flux1 metric interplay. Switch: none (diagnostic result; the related switches
  are the ones above and SNAP_GRAVITY_WORK_RADIAL_EXACT in the gravity-work chapter).
- Derivations:
  - The offset and its eps_eff signature +g/(6 c_p R): exists sources/study__next-1overR_README.md §0-3 (with moments.py replica; at d59836d).
  - Face-flux completeness to O(h^4) incl. h^2/R (hypothesis H1): exists sources/gw__ONEOVERR_split_RESULT.md §1-2 (face_replica.py).
  - Gravity-work weight and curv_flux1 on the radial grid: exists sources/study__next-1overR-remainder_README.md §0-4 and docs/curved-gravity-work-weight.md (gravity-work chapter).
  - What remains after SNAP_X1_CENTROID_EXACT (Favre-velocity ratio): exists docs/x1-centroid-spherical.md §6.
- Figures: R [eps nz^2(R) - eps nz^2(inf)] vs R/H for off/on arms; decomposition bar chart of the 1/R content by source term.
- Code: no dedicated code; the terms live in src/hydro/hydro_forward.cpp:280-294, :63-205 and src/coord/spherical_polar.cpp:224-310.
- Tests: none asserts the remainder; tests/test_x1_centroid_rest.py covers rest only.
- Limits / known issues: ISSUES.md item 5 — one-step harness numbers from commits not in snapy were removed; rebuild the table from an in-snapy closure run at dae902b (docs/x1-centroid-spherical.md §6 quotes code numbers but without a committed script/deck); the volume-weighted metric carries its own 1/R (§6).
- Discrepancies: study READMEs are at d59836d (pre-#293 merge); their file:line refs are stale.


#### 5.10 (legacy box) isentropic wall ghosts and zero-gradient wall faces
<sub>inventory C: Scheme (legacy box): isentropic wall ghosts and zero-gradient wall faces</sub>

- Summary: `_revise_x1inner/outer_ghost` (isentropic extrapolation into ghosts) is defined but its call is commented out; `_revise_x1inner/outer_lr` (copy right-state p, rho to left at the wall face) runs only on the non-WB x1 path with gravity on. Switch: none.
- Derivations: none needed beyond describing as legacy; re-derive from src/hydro/hydro.cpp:448-500@e894700 if kept.
- Figures: none.
- Code: src/hydro/hydro.cpp:429, :436, :443, :463; src/hydro/hydro_forward.cpp:256-259 (commented call), :389-392.
- Tests: none.
- Limits / known issues: effectively unreachable for non-shallow EOS with gravity (wb_x1 true there).


---

<a id="ch6"></a>
## Chapter 6. Gravity and energy

How gravity's work enters the energy equation and what each form conserves: the cell form with the constant-gravity forcing, the face form (with `face-wallc` and the cp3/cp5/weno5 curvature flux), the gravity-work fixer, the corrected-PE face work D (the worked example, written in full), the gravity work inside the implicit operator, and a closing table of invariants and oracles. Written by the editor from the code at dae902b and the gravity-work sources; the constant-gravity forcing entry of the chapter 2/9/10 inventory is folded into 6.1.


#### 6.1 Constant gravity forcing and the cell form of the gravity work (`gravity-work: cell`, the default)
<sub>inventory F: Scheme: Constant gravity forcing and the cell form of the gravity work (`gravity-work: cell`, the default)</sub>

- Summary: `const-gravity` adds the body force $\rho g_a\alpha_{\mathrm{nh}}$ to the momenta and the cell work
  $W^{\mathrm{cell}}=\rho v_1g_1\alpha_{\mathrm{nh}}$ (and $\rho v_2g_2$, $\rho v_3g_3$) to $E$. With `gravity-work: cell` this is
  the booked work, and only the part of the mass flux beyond the reference flux, $F-F^{\mathrm{ref}}$, which sedimentation and
  the positivity limiter add, is booked in face form. Switch: YAML `forcing/const-gravity/{grav1,grav2,grav3,
  non-hydrostatic (1), gravity-work (cell)}`.
- Derivations:
  - Continuous budget, $E+\rho\phi$ conservation, and the cell form's non-telescoping defect: exists:
    sources/gw__GRAVITY_WORK_TECH_REPORT_draft.md §§2.1-2.4, 3.4-3.5 (re-check every equation against the code at
    dae902b; the draft's line citations predate it).
  - The $F-F^{\mathrm{ref}}$ face booking under cell mode: re-derive from `src/hydro/hydro_forward.cpp:781-787@e894700` and
    `:404-408@e894700` (`bflux1`).
  - The hydrostatic-split part ($\alpha_{\mathrm{nh}}<1$, `rho_grav`) of the removed cell work: re-derive from
    `src/hydro/hydro_forward.cpp:850-857@e894700` (chapter 5 owns the split itself).
- Figures:
  - One cell with the body force at its centroid and the cell work $\rho v_1g_1$; the defect drawn as the mismatch
    between the PE change of the mass crossing a face and the work booked in the two cells.
  - Per-face bar chart of the cell-form defect on a closed column (from a committed check).
- Code: `src/forcing/const_gravity.cpp:12-44@e894700` (`from_yaml`, keys, defaults, fixer default = cell);
  `src/forcing/const_gravity.cpp:46-62@e894700` (`forward`); `src/hydro/hydro_forward.cpp:230-231@e894700` (`gw_cell`);
  `src/hydro/hydro_forward.cpp:404-408@e894700` (`bflux1`); `src/hydro/hydro_forward.cpp:781-787@e894700`
  ($F-F^{\mathrm{ref}}$); `src/hydro/hydro_forward.cpp:858-859@e894700` (cell: correction = face work of $F-F^{\mathrm{ref}}$).
- Tests: `tests/test_gravity_work_fixer.py` (`test_gravity_work_fixer_python`, switch 0) arm "cell, fixer false":
  $E+\mathrm{PE}_d$ drift $>100\,$TOL (planted control: the defect is real); `tests/test_forcing.cpp`
  (`test_forcing.release`) with `tests/test_gravity_energy.yaml`, `tests/test_gravity_sedimentation.yaml`.
- Limits / known issues: the cell form does not conserve $E+\mathrm{PE}_d$ by itself (hence the fixer, 6.3); $g_2$,
  $g_3$ book cell work only.
- Discrepancies: none found.


**Folded in from inventory B ("Constant gravity forcing (source terms only)"):**

- Summary: `du[m_d] += dt rho g_d (non-hydrostatic factor on x1)`, `du[E] += dt rho v_d g_d`. The x1 energy term is the
  "cell" gravity work. Switch: `forcing/const-gravity/{grav1,grav2,grav3,non-hydrostatic,gravity-work,gravity-work-fixer}`;
  defaults 0, 0, 0, 1, "cell", true-if-cell (`src/forcing/const_gravity.cpp:22-36`).
- Derivations: cross-ref the gravity-work chapter (`docs/derivations/curved-gravity-work-weight.md@e894700` etc.).
- Figures: none here.
- Code: `src/forcing/const_gravity.cpp:12` `from_yaml`; `:46` `ConstGravityImpl::forward`.
- Tests: `tests/test_forcing.cpp:870`, `:920`, `:978`, `:1108` (gravity-work family; other chapter).
- Limits / known issues: `non_hydrostatic` scales only the x1 terms.
- Discrepancies: none.

#### 6.2 Face form of the gravity work (`gravity-work: face`, `face-wallc`) and the cp3/cp5/weno5 curvature flux
<sub>inventory F: Scheme: Face form of the gravity work (`gravity-work: face`, `face-wallc`) and the cp3/cp5/weno5 curvature flux</sub>

- Summary: books the $x_1$ work as $W^{\mathrm{face}}_i=\frac1{V_i}[\phi_i\Delta_i[AF]-\Delta_i[A\phi F]]$ on the total mass
  flux after positivity and sedimentation, and removes the cell work the forcing added; it conserves $E+\mathrm{PE}_d$
  exactly with an $O(h^2)$ local error (trapezoid term, plus $O(h^2/r)$ curvature terms on spherical-polar). For
  cp3/cp5/weno5 the curvature flux $\mathcal K$ removes the $h^2m''/12$ part, zero at physical $x_1$ faces (wall cells
  first order). `face-wallc` keeps the cell work in the two $x_1$ wall cells. Under D (6.4) $\mathcal K$ is off.
  Switch: YAML `gravity-work: face | face-wallc`; $\mathcal K$ active for `reconstruct/vertical/type` cp3/cp5/weno5
  without D.
- Derivations:
  - Face form, telescoping, $E+\mathrm{PE}_d$ conservation: exists: sources/gw__GRAVITY_WORK_TECH_REPORT_draft.md
    §§2.4, 3.4-3.5; docs/derivations/curved-gravity-work-weight.md@e894700 §§1-2, §4 (lemma).
  - Error expansion (6.4.7) and the exact-weight conflict (options A-E): exists:
    docs/derivations/curved-gravity-work-weight.md@e894700 §§2-6 with `curved_gravity_work_weight.py`.
  - The curvature flux $\mathcal K$ (face average exceeds $m$ by $\tfrac{h^2}{12}(m''+\rho'v')$): re-derive from
    `src/hydro/hydro_forward.cpp:824-849@e894700`; its wall-cell order: exists: curved-gravity-work-weight.md §8.3.
  - Independent Cartesian four-point booking: moved to 6.4. It is an independent derivation of D's own result,
    not an unimplemented alternative to the face form; see the 6.4 entry.
  - `face-wallc` wall cells: re-derive from `src/hydro/hydro_forward.cpp:892-897@e894700`.
- Figures:
  - Stencil: face potential $\phi_{i\pm1/2}$ vs centroid $\phi_i$, the two face weights $(x_{1,i\pm1/2}-x_{1,i})$.
  - The curvature flux $\mathcal K$ on faces, zeroed at the walls (why wall cells drop to first order).
  - Error ladder face vs face+$\mathcal K$ (interior/wall), from `optionF_replica.py` output re-run at the pin.
- Code: `src/hydro/hydro_forward.cpp:767-812@e894700` (mass flux, face work); `:824-849@e894700` ($\mathcal K$);
  `:890-897@e894700` (face minus cell, face-wallc); `src/hydro/hydro.cpp:56-64@e894700` (key check, fixer off);
  `src/hydro/hydro.cpp:204-209@e894700` (`is_x1_wall`).
- Tests: `tests/test_gravity_work_fixer.py` arm face-wallc (reported only); `tests/test_horizontal_flux_covariance.py`,
  `tests/test_flux_covariance_rows.py`, `tests/test_forcing.cpp` (plain face form, switch 0, $E+\mathrm{PE}_d$ oracles);
  `tests/test_implicit_face_work_operator.py` (`..._python`, switch 0).
- Limits / known issues: $O(h^2)$ work error in every cell; first-order wall cells with $\mathcal K$; with an implicit
  scheme the face work must be in the operator (warning at `src/hydro/hydro.cpp:118-126@e894700`, chengcli/snapy#283).
- Discrepancies: the gravity-work draft predates D being on by default with `face` (snapy@84b037f); its "face form"
  results describe the switch-0 arm.


#### 6.3 Gravity-work fixer (global $E+\mathrm{PE}_d$ correction for `gravity-work: cell`)
<sub>inventory F: Scheme: Gravity-work fixer (global $E+\mathrm{PE}_d$ correction for `gravity-work: cell`)</sub>

- Summary: with `gravity-work: cell` and `gravity-work-fixer: true` (the default with cell), each stage accumulates the
  dynamics' $E+\mathrm{PE}_d$ defect $\mathcal D$ (cell work + face work of $F-F^{\mathrm{ref}}$ + PE change of the mass the
  $x_1$ fluxes move, weighted by the stage's weight in the step), and after the last stage subtracts $\mathcal D$
  uniformly per unit mass, $\Delta E = -\rho\,\mathcal D/M$, over the whole domain (one allreduce). It refuses
  periodic $x_1$, $g_2,g_3\ne0$, and any step that moved more than $10^3\epsilon$ of the wall cells' mass through an
  $x_1$ boundary face. Switch: YAML `const-gravity/gravity-work-fixer` (default = `gravity-work == cell`).
- Derivations:
  - The defect $\mathcal D$ and the exact global fix: exists: sources/gw__GRAVITY_WORK_TECH_REPORT_draft.md §3.6, §5.3
    (#284); the implicit part (the `epe` lambda): exists: same §3.7, §5.5 (#285), re-check against
    `src/hydro/hydro_forward.cpp:944-969@e894700`.
  - Stage weight $w_{2,s}\prod_{t>s}w_{1,t}$ of a stage's defect in the step: re-derive from
    `src/hydro/hydro_forward.cpp:985-995@e894700`.
  - The wall-mass bound $10^3\epsilon M_{\mathrm{wall}}$: re-derive from `src/mesh/meshblock.cpp:889-904@e894700` (no
    derivation; tolerance rationale only in the comment and #285).
- Figures:
  - Flow of $\mathcal D$: per stage → weighted sum → allreduce → uniform $-\mathcal D/M$ per kg.
  - Time series of `fixgrav=` and $E+\mathrm{PE}_d$ with and without the fixer (committed run).
- Code: `src/hydro/hydro_forward.cpp:860-889@e894700` (stage defect, wall mass); `:944-969@e894700` (implicit `epe`);
  `:985-995@e894700` (stage weight); `src/mesh/meshblock.cpp:832-838@e894700` (apply after last stage);
  `src/mesh/meshblock.cpp:844-868@e894700` (`gravity_work_fixer_sums`); `src/mesh/meshblock.cpp:870-911@e894700`
  (`apply_gravity_work_fixer`); `src/mesh/mesh.cpp:341-358@e894700` (multi-block: one sum, one allreduce);
  `src/hydro/hydro.cpp:62-81@e894700` (setup checks); `src/hydro/hydro.hpp:150-204@e894700` (meters).
- Tests: `tests/test_gravity_work_fixer.py` (`test_gravity_work_fixer_python`, switch 0): cell+fixer
  $|\Delta(E+\mathrm{PE}_d)|/|E+\mathrm{PE}_d|\le$TOL explicit and VIC-partial; fixer-off control drifts $>100$ TOL;
  refusals (outflow in float64/float32, periodic $x_1$, Python-cleared names, $g_2\ne0$); a NaN wall cell goes to redo;
  `tests/test_implicit_gravity_tall_column.py` (default-cell-global-fixer arm, `W_TOL`).
- Limits / known issues: it is a global, not local, correction (it does not remove the local $O(h^2)$ error, only its
  integral); the sum is decomposition-dependent at round-off (chapter 14); at very large implicit steps sealed-wall
  round-off can exceed the bound (refusals near acoustic Courant 2500-2750 recorded in #285, not universal).
- Discrepancies: none found.


#### 6.4 The corrected-PE face work, scheme D (`SNAP_GRAVITY_WORK_RADIAL_EXACT`)
<sub>inventory F: Scheme: The corrected-PE face work, scheme D (`SNAP_GRAVITY_WORK_RADIAL_EXACT`)</sub>

- Summary: written in full as the worked example, `chapters/06-gravity-energy/D_face_work_pe.md` (all six layers).
  $W^{\mathrm{D}}=W^{\mathrm{face}}+g_1\sigma^2s[\dot\rho]$ conserves $E+P$ ($P$ exact to $O(h^4)$) to round-off and is $O(h^4)$
  in every cell; on by default with `gravity-work: face` on Cartesian and spherical-polar grids.
- Derivations: exists: `docs/derivations/curved-gravity-work-weight.md@e894700ff7aee30b52882e5202b16461413780b0`
  §§1-4 (face form and error expansion), §§7-8 (the corrected potential and the weights), §10 (the implicit
  operator) and §11 (onset); re-written in the report with checks C1-C11
  (`chapters/06-gravity-energy/checks/d_face_work_pe_check.py`, all pass). Two carry-overs from §11 are open
  and must be closed before approval: the §11.2 onset numbers quoted in the Tests layer have no deck or run
  (**missing evidence**), and the §11.3 convergence table was a placeholder at the pin. Note that §7, §8.6 and
  §§11.3-11.4 of the note were edited after the pin on `next/final-batch`; re-read the note's current head
  before approval (STYLE.md §3.2).
- Independent corroboration and open disagreement: `sources/gw__NEXTPR_indep_cartesian_gravity_work_weight.md`
  derives the same result for the Cartesian case by a different construction (§2.3, boundary shifts
  $\varepsilon_i$ on the three cells next to each wall), proves exact conservation (§2.4) and $O(h^4)$ in
  every cell including wall cells (§2.5), shows the modified $P$ is fourth order against the plain one's
  second (§2.6), and verifies all of it numerically (§3). Cite it in the Derivation layer as independent
  confirmation, not as an unimplemented alternative. Its §4.4 lists claims it holds to be wrong or
  under-qualified in `docs/derivations/curved-gravity-work-weight.md`, in particular §4.4(a) on the Cartesian
  "conflict" sentence. Each §4.4 item is dispositioned before 6.4 is approved — accepted and the derivation
  note corrected, or rejected with a reason — and the outcome recorded in the section's Limits layer. An
  undispositioned item blocks approval.
- Figures: done: `chapters/06-gravity-energy/figures/fig_D_face_work_pe.py` (stencils interior/wall/seam, VIC
  lumping, order of accuracy).
- Code: see the section's Code layer. 37 distinct `path:lines@dae902b` citations; each file exists and each
  range exists at `dae902b04d217a824634762dd4e07790a12add5e`, checked 2026-10-10 with
  `git show <sha>:<path>`. One further citation is to pyharp at
  `4721715855e937c1e8b218e964c0655f46e56e29` and must be corrected from `:49-60` to `:49-61`, which is where
  the third rk3 weight is. Re-check all of them with `tools/check_citations.py` when it lands, and record the
  count and the date here rather than a bare number.
- Tests: `test_gravity_work_radial_exact_python` (checks 1-8), `test_x1_seam_split_radial_exact`,
  `test_x1_seam_split_mp_radial_exact`, `test_implicit_gravity_tall_column_python`, the `_radial_exact` arms of
  `test_implicit_face_work_operator` and `test_implicit_stratified_solid`.
- Limits / known issues: see the section's Limits layer (seams $O(h^4)$, no cubed-sphere form, onset numbers missing
  evidence, untested switch combinations).


#### 6.5 Gravity work inside the vertical implicit operator (cell, face rows, projection and clamp work)
<sub>inventory F: Scheme: Gravity work inside the vertical implicit operator (cell, face rows, projection and clamp work)</sub>

- Summary: the VIC linearises the full gravity ($\mathsf\Phi$: $g_1$ in the momentum row's mass column and the energy
  row's momentum column). With `gravity-work: face` the energy row books the face form of the mass the solve moves
  (weights $\omega^{\mathrm{lo}},\omega^{\mathrm{hi}}$; Cartesian has its own exact rows); with `cell` it books a diffusive cell
  form; after the solve the projection work (raw minus projected mass) and the clamp work (moved minus requested face
  mass) are added so the booked energy matches the mass actually moved. `face-wallc` keeps a post-solve swap.
- Derivations:
  - Face work in the operator (#283) and its consistency with mass transport (#285): exists:
    sources/gw__GRAVITY_WORK_TECH_REPORT_draft.md §3.7, §§5.2, 5.5; sources/gh__PR_BODIES_265-284.md,
    gh__PR_BODIES_285-293.md (results only) → re-derive the rows from `src/implicit/vic_assemble_full_impl.h:101-120@e894700`
    and `src/implicit/vic_assemble_partial_impl.h@e894700`.
  - Projection and clamp work: re-derive from `src/implicit/implicit_hydro.cpp:382-414@e894700`.
  - The face-wallc post-solve swap: re-derive from `src/implicit/implicit_hydro.cpp:419-444@e894700`.
- Figures:
  - The block row of cell $i$ with the energy-row entries the face work adds (mass column via $\mathsf A^\pm$ rows,
    momentum column), Cartesian vs curved variant.
  - Raw, projected, clamped face masses and the work each books.
- Code: `src/implicit/implicit_hydro.cpp:239-242@e894700` (weights); `:265-277@e894700` (flags `kVicFaceWork`,
  `kVicCartesianFaceWork`, `kVicDiffusiveCell`); `src/implicit/vic_assemble_full_impl.h:38-40, 101-120@e894700`;
  `src/implicit/implicit_hydro.cpp:382-414@e894700`; `:419-444@e894700`; `src/hydro/hydro.cpp:305-309@e894700`.
- Tests: `tests/test_implicit_face_work_operator.py` (rest columns at Courant 197/657, full and partial VIC; energy
  oracles), `tests/test_implicit_stratified_solid.py` (clamp energy, solids), `tests/test_implicit_gravity_tall_column.py`.
- Limits / known issues: chapter 7's VIC limits (reflecting closure whatever the $x_1$ boundary); the face-work rows
  are a linearisation about the stage state.
- Discrepancies: none found.


#### 6.6 What each form conserves (summary and oracle guide)
<sub>inventory F: Scheme: What each form conserves (summary and oracle guide)</sub>

- Summary: one table, derived in 6.1-6.5: cell (no exact invariant; with the fixer $E+\mathrm{PE}_d$ globally per
  step), face and face-wallc ($E+\mathrm{PE}_d$ exactly; face-wallc not at the wall cells), D ($E+P$ exactly, not
  $E+\mathrm{PE}_d$); per stage, per step, explicit and implicit; which logged quantity (`pe=`, `fixgrav=`) and which
  test oracle matches each. Switch: as 6.1-6.4.
- Derivations: the per-stage-to-per-step argument (linear invariant, $w_0+w_1=1$): exists as written in
  `D_face_work_pe.md` §2.6; the cell-form defect S decomposition ($S_{\mathrm{div}}$, $S_{\mathrm{rec}}$, $S_{\mathrm{dif}}$): exists:
  sources/gw__GRAVITY_WORK_TECH_REPORT_draft.md §4 (re-check; its numbers lack deck/sha, ISSUES.md item 2).
- Figures: the table as a matrix figure (form × invariant × explicit/implicit), and one drift plot of all three forms
  on one deck from a committed run.
- Code: `src/mesh/meshblock.cpp:1045-1057@e894700` (`pe=`), `:1109-1110@e894700` (`fixgrav=`).
- Tests: the union of 6.1-6.5's tests; the oracle per test (which invariant it measures) listed.
- Limits / known issues: the physically "right" form for low-Mach convection is the open question of the draft §§6-7
  (T1L onset); with the wall closure and D the remaining onset error is shared by face and cell (placeholder table in
  curved-gravity-work-weight.md §11.3, missing evidence).
  - Untested combinations of the gravity-work forms with the other scheme switches
    (`SNAP_FLUX_COVARIANCE`, `SNAP_WB_REF4`, `SNAP_X1_CENTROID_EXACT`, `SNAP_X1_MASS_COVARIANCE`), and the face
    forms on moist columns with several mass rows: no ctest entry covers any of them (D's Limits item 12). This
    chapter states the combinations and what would break first in each; §12.12's matrix records the coverage
    gap; neither invents a test. Whether any of them blocks approval of chapter 6 is the lead's decision, taken
    when the matrix is first complete.
- Discrepancies: the draft's Fig. 6 and Appendix A are dropped or rebuilt (ISSUES.md items 1, 6).


---

<a id="ch7"></a>
## Chapter 7. Time integration

Split in two. 7.A: the explicit SSP-RK stages (the integrator is pyharp's `harp::Integrator`, cited at its own sha), the placement of the ghost exchange, the time step, step acceptance and redo, and the operator-split pieces at the step boundary. 7.B: the vertical implicit correction (VIC): activation, assembly, the stage-weighted implicit step, the block-tridiagonal solve, the LU pivot tolerance, rejection, redistribution, and its column closure. The radiative time-step limiter is not in snapy and moves to Appendix E.

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: the explicit multi-stage update and the order of operations inside one stage; the time-step bound; the vertically
implicit correction (VIC), from options through assembly, block-tridiagonal solve, LU guard, rejection and
redistribution; step acceptance and rejection (`check_redo`/`apply_redo`), the abnormal-exit status, and the
operator-split pieces that sit at the step boundary.

Recommendations on structure:
- Split into **7A Explicit stages and step control** (RK, dt, redo, exit status) and **7B The vertical implicit
  correction** (VIC options → assembly → sweep → LU guard → rejection → redistribution). 7B is about as large as 7A, and
  its readers, who audit the solver, differ from 7A's.
- Keep `check_redo` in 7A, but present it as the consumer of six causes. Chapter 8 documents the producers (floors,
  limiter marks, VIC dry clamp, saturation failures). Each cause gets a single forward reference here.
- **Drop the RT timestep limiter from the snapy report.** It is not in snapy. It lives in an external runner script
  (`hj2024_runner.py` per `sources/canoe__RT_TIMESTEP_LIMITER_TECH_REPORT.md` §5c). A grep of the tree for `rt_limiter`,
  `tau_rad` or a radiative dt bound finds nothing. At most, mention it in an appendix as "an external driver can wrap
  `max_time_step`, which is already globally MIN-reduced". The report's §5a rank-safety rule applies to any such wrapper.
- VIC gravity-work rows are covered by another author. Their entry points are listed under the VIC-assembly scheme.

</details>


### 7.A Explicit stages, time step and step acceptance


#### 7.1 Explicit SSP Runge–Kutta stage update (Shu–Osher form)
<sub>inventory D: Scheme: Explicit SSP Runge–Kutta stage update (Shu–Osher form)</sub>

- Summary: each stage forms `u ← w0·u0 + w1·u + w2·Δu(u)`. Here `u0` is the step-start register and `Δu` is the full-dt
  tendency (`-dt·div F + dt·S`, with the implicit correction folded in). Types are rk1/euler, rk2, rk3 (SSP-RK3) and
  rk3s4. Switch: `integration/type` (YAML), read in harp `IntegratorOptionsImpl::from_yaml` with default `"rk3"`
  (harp@4721715 `src/integrator/integrator.cpp:24`). Unknown types throw (`integrator.cpp:79-81`).
- Stage weights (harp@4721715): rk1 `integrator.cpp:35`; rk2 `:40`; rk3 `:49` ({0,1,1}, {3/4,1/4,1/4},
  {1/3,2/3,2/3}); rk3s4 `:62` ({1/2,1/2,1/2}, {0,1,1/2}, {2/3,1/3,1/6}, {0,1,1/2}); `IntegratorImpl::forward` `:101`,
  linear combination `:120`.
- Derivations:
  - SSP-RK3 order conditions and Shu–Osher coefficients: re-derive from harp@4721715 `integrator.cpp:49-61`. Standard,
    but no step-by-step derivation exists in the sources.
  - rk3s4 order and SSP coefficient. The source cites a gkeyll page in a comment (`integrator.hpp:13-14`). Re-derive
    from `integrator.cpp:62-75`, and state its order and effective CFL.
  - Convexity: "every stage is a convex combination of prior states and one full-dt Euler step, with α = w2/w1 ≤ 1".
    exists: `sources/canoe__POSITIVITY_TECH_REPORT.md` §3 (short, but a real argument). Also stated in
    `src/hydro/flux_positivity.hpp:43-46`.
- Figures:
  - Stage tableau as a flow diagram: u0 → u(1) → u(2) → u^{n+1}, with the w0/w1/w2 arrows labelled.
  - A timeline of one stage in `advance_local`: exchange → hydro forward (recon, Riemann, positivity, divergence,
    forcings, VIC) → scalar forward → user forcings → RK average → conserved limiter → solid refill → (last stage)
    saturation adjustment → gravity fixer → physical BCs.
- Code:
  - `src/mesh/meshblock.cpp:597` — `MeshBlockImpl::advance_local` — the stage driver.
  - `src/mesh/meshblock.cpp:603` — publishes `phydro->rk_stage` (consumed by the VIC stage weighting).
  - `src/mesh/meshblock.cpp:612` — stage 0 saves `_hydro_u0`. Stage 0 also resets the gravity defect, the VIC dry-clamp
    and solve-failure latches (`:618`), the limiter marks, and the saturation-failure counter (`:621`).
  - `src/mesh/meshblock.cpp:650` — `phydro->forward(dt, hydro_u, vars)` returns the full-dt `Δu`.
  - `src/mesh/meshblock.cpp:755` — `hydro_u.set_(pintg->forward(stage, _hydro_u0, hydro_u, fut_hydro_du))` — the RK
    average. `:768` is the scalar counterpart.
  - `src/mesh/meshblock.cpp:756` — `apply_conserved_limiter_(hydro_u, whole_column=true)` after every average (Ch 8).
  - `src/hydro/hydro_forward.cpp:218` — `peos->forward(u, w)` at stage entry. This is the only writer of `hydro_w`, so
    `hydro_w` is one stage stale after the last stage (relevant to `floor_hit`).
  - `src/hydro/hydro_forward.cpp:766` — `du = -dt·div` on interior cells. `:773` adds the forcings at the full dt.
  - `src/mesh/meshblock.hpp:290-291` — stage registers `_hydro_u0`, `_scalar_s0`.
- Tests:
  - `tests/test_forcing.cpp` (`test_forcing.release`) — `native_dry_source_uses_each_rk_stage_weight` (`:1309`). The dry
    source enters with each stage's `wght2`, at 1e-12 (hand-computed).
  - `tests/test_forcing.cpp` — `rk3_stage_is_published_by_block_step` (`:1202`). `rk_stage` equals the stage in each
    `advance_local`.
  - `tests/run_straka.cmake` (`test_straka`) — reference-solution regression of the full RK3 path.
- Limits / known issues:
  - `max_redo` is not a YAML key. harp's `from_yaml` never reads it (`integrator.cpp:24-30`), so the default of 5
    (`integrator.hpp:58`) is fixed for YAML runs. This is confirmed by the comment at
    `tests/test_uranus_cycle1_abort.cpp:16-19`.
  - The integrator is pure tensor arithmetic with no fused kernel (`integrator.cpp:107-120`; the dispatch path is
    commented out).
- Discrepancies:
  - `flux_positivity.hpp:43-46` asserts wght2 ≤ wght1 for all shipped integrators. This holds for harp@4721715, but harp
    is unpinned. Treat it as an invariant to re-check against the linked version.


#### 7.2 Ghost-exchange placement within a stage (MeshBlock vs Mesh driver)
<sub>inventory D: Scheme: Ghost-exchange placement within a stage (MeshBlock vs Mesh driver)</sub>

- Summary: `MeshBlockImpl::forward` exchanges ghosts **before** `advance_local`. `MeshImpl::forward` exchanges **after**
  it. Switch: none (the choice of driver API).
- Derivations: none needed. Describe the invariant ("ghosts that reconstruction consumes must be in sync with
  host-side operator-split updates made between forward calls").
- Figures: two timelines side by side, showing where the exchange sits relative to the driver's kinetics or
  condensation step.
- Code:
  - `src/mesh/meshblock.cpp:545-552` — `MeshBlockImpl::forward`: `exchange_ghost_zones` at `:550`, then
    `advance_local`. The comment explains the cubed-sphere seam bias that this ordering removes.
  - `src/mesh/mesh.cpp:331` — `MeshImpl::forward`: for one block, `advance_local` (`:336`) then `exchange_ghost_zones`.
    For several blocks, `advance_local` jobs then exchange (`:364`).
  - `src/mesh/meshblock.cpp:913` — `exchange_ghost_zones` (Ch 11).
- Tests: `tests/test_mesh_multi_block.cpp` (`test_mesh_multi_block.release`, 2 ranks). Chapter 9 owns it.
- Limits / known issues: the two orderings differ. On the Mesh path, a host-side update made between steps (driver
  kinetics, as `examples/run_hydro.cpp:170-191` does for the MeshBlock path) reaches the ghosts only after the next
  stage's exchange. Needs verification. Flag it to the parallel chapter.
- Discrepancies: none in the sources. The comment at `meshblock.cpp:546-549` describes only the MeshBlock path.


#### 7.3 CFL time step (acoustic, implicit-advective, shear, diffusion; global MIN; redo halving)
<sub>inventory D: Scheme: CFL time step (acoustic, implicit-advective, shear, diffusion; global MIN; redo halving)</sub>

- Summary: dt = 2^(−current_redo) · cfl · min over directions and cells of the bound below.
  - An explicit direction uses Δx/(|v|+c_s).
  - An implicit direction (VIC, x1 only) uses (cfl/advection_cfl)·Δx/|v|. In 1-D (nc2 = nc3 = 1) the acoustic bound is
    kept.
  - An optional shear bound applies where |Δv_h| ≥ c_s across an x1 face.
  - The diffusion bound is Δx²/(2·ndim·κ).
  - The result is MIN-allreduced across ranks and local blocks.
- Switches:
  - `integration/cfl` (harp, default 0.9, `integrator.cpp:25`).
  - `integration/implicit-advection-cfl` (default 1.0, must be finite and > 0; `src/implicit/implicit_hydro.cpp:59-62`).
  - `integration/shear-cfl` (default 0 = off, must be ≥ 0; `implicit_hydro.cpp:63-66`).
  - Either key without `implicit-scheme` is a hard error (`implicit_hydro.cpp:36-41`).
- Derivations:
  - Acoustic CFL for the Riemann-flux FV scheme: re-derive from `src/hydro/hydro.cpp:357-374` (textbook).
  - Advective bound in an implicit direction (|w|Δt/Δx ≤ advection_cfl): re-derive from `hydro.cpp:313-333`. The PR
    #218 body (`sources/gh__PR_BODIES_202-219.md`) states only the result.
  - Shear bound dt = shear_cfl·c_f·Δx_h/(|v_h(i)||v_h(i+1)|): re-derive from `hydro.cpp:335-356`. Only the result is
    stated (PR #218, `tests/test_shear_cfl.py` docstring). The physical motivation (a supersonic shear across an implicit
    face) needs a derivation.
  - Diffusion bound: re-derive from `src/forcing/diffusion.cpp:572-618` (dynamic and static coefficient forms).
  - The redo factor 2^(−n): a policy, nothing to derive.
- Figures:
  - The stencil of the three bounds on one x1 face (acoustic across x2, advective in x1, shear between i and i+1).
  - A dt-versus-retry staircase (halving per redo, reset on acceptance).
- Code:
  - `src/hydro/hydro.cpp:292` — `HydroImpl::max_time_step(w, solid)`; `:304` sets c_s = 1e-8 in solid cells; `:313`
    computes `adv`; `:316` holds the 1-D exception `(cs.size(0)==1 && cs.size(1)==1)`; `:335` holds the shear bound;
    `:378` folds in diffusion.
  - `src/mesh/meshblock.cpp:510` — `MeshBlockImpl::max_time_step` with MIN-allreduce; `:528` applies
    `pow(2,-current_redo)*cfl*dt`.
  - `src/mesh/meshblock.cpp:531` — `local_max_time_step` (passes `solid` if present).
  - `src/mesh/mesh.cpp:306` — `MeshImpl::max_time_step`: min over local blocks, then one allreduce. It uses
    `blocks.front()`'s redo counter (`:326`).
  - `src/forcing/diffusion.cpp:572` — `DiffusionImpl::max_time_step`.
  - `src/implicit/implicit_hydro.cpp:24` — `ImplicitOptionsImpl::from_yaml`. `check_keys` of the integration block at
    `:30-33` lists pyharp's keys by name.
- Tests:
  - `tests/test_implicit_advection_cfl.py` (`test_implicit_advection_cfl_python`). With an implicit direction, dt equals
    advection_cfl·dx1/v1, at relative 1e-12. At rest it falls back to the explicit x2 bound. With the explicit scheme
    the acoustic bound returns. The key without implicit raises.
  - `tests/test_shear_cfl.py` (`test_shear_cfl_python`). The bound fires only for a jump ≥ c_s; shear-cfl 0 leaves dt
    alone.
  - `tests/test_implicit_cfl.cpp` (`test_implicit_cfl.release`). Non-numeric, negative and nonfinite values are rejected.
  - `tests/test_diffusion_x1_scale.cpp` / `tests/test_diffusion_moist.cpp`. The diffusion dt bound is checked at 1e-12.
- Limits / known issues:
  - No sedimentation-velocity bound enters `max_time_step` (`hydro.cpp:292-380`). Settling flux is protected only by the
    positivity limiter (Ch 8).
  - `max_time_step` reads scheme bits 1 and 2 (implicit x2/x3) at `hydro.cpp:323,329`, but
    `ImplicitOptionsImpl::type()` accepts only schemes 0, 1 and 9 (`implicit_hydro.cpp:84-98`). The x2/x3 branches are
    unreachable.
  - The 1-D exception keeps the acoustic x1 bound when the column is 1-D. The tall-column report notes that "1-D
    silently runs explicit" as an instrument hazard (`sources/canoe__tall_column_instability_TECH_REPORT.md` §3f).
  - PR #218 records that existing scheme-1/9 cards changed dt silently when the advective bound was introduced
    (`sources/gh__PR_BODIES_202-219.md`, #218 Compatibility).
- Discrepancies: none found against code.


#### 7.4 Step acceptance and rejection (`check_redo` / `apply_redo`), collective decision, max_redo, abnormal exit
<sub>inventory D: Scheme: Step acceptance and rejection (`check_redo` / `apply_redo`), collective decision, max_redo, abnormal exit</sub>

- Summary: after the last stage (and after any driver-level kinetics), the driver calls `check_redo`.
  - Six local causes are collected: 1 floor (fresh primitives within 1.001× the density or pressure floor, or NaN),
    2 VIC dry clamp, 4 limiter patch, 8 NaN found by a limiter, 16 saturation-adjustment failures, 32 VIC solve failure.
  - The causes are MAX-allreduced, ORed across local blocks in a Mesh.
  - On any cause the step rolls back: `hydro_u ← u0`, `hydro_w` and the scalar primitives are recomputed, the cycle is
    decremented, `current_redo` is incremented, and the gravity fix is dropped.
  - The retry runs at 2^(−current_redo)·dt.
  - When `current_redo > max_redo`, the run terminates. A VIC solve failure restores the step first.
  - `finalize` returns status 1 on "Terminating abnormally", and the drivers propagate it.
  Switches: `max_redo` (harp default 5; not YAML-settable); `equation-of-state/density-floor` and `pressure-floor`
  feed `floor_hit` (Ch 8).
- Derivations: none (policy). State the invariants: collective decision; restore both conserved and primitive state;
  dt halving is global because `max_time_step` applies `current_redo` after the MIN-reduce.
- Figures:
  - A flowchart of the driver loop (`examples/run_hydro.cpp:160-200`): dt → stages → kinetics → check_redo → {accept,
    redo, stop}.
  - The cause bitmask table.
- Code:
  - `src/mesh/meshblock.cpp:1190` — `floor_hit`. It recomputes primitives on a clone; `:1199` holds the negated
    comparison so that NaN counts. The IPR guard for shallow water is at `:1200-1202`.
  - `src/mesh/meshblock.cpp:1206` — `vic_dry_clamp_hit`; `:1212` — `limiter_hits` (one device-to-host read); `:1220`
    — `saturation_failures` (drains the kintera counter).
  - `src/mesh/meshblock.cpp:1229` — `apply_redo`: log `:1231-1240`; increment `:1241`; terminate unless cause 32
    `:1242-1247`; restore `:1251-1256`; `cycle -= 1` `:1259`; terminal stop after a VIC restore `:1262-1267`; accept
    `:1272-1274`.
  - `src/mesh/meshblock.cpp:1278` — `local_redo_flags`; `:1288` — `reduce_redo_flags` (MAX-allreduce, bitmask);
    `:1302` — `check_redo`.
  - `src/mesh/mesh.cpp:422` — `MeshImpl::check_redo`. It checks signals first (`:427`), ORs the flags across local
    blocks, reduces once, and applies to all blocks. A VIC terminal failure still restores every block.
  - `src/mesh/meshblock.cpp:1121` — `finalize`; `:1139` sets `status = 1` on abnormal termination. `src/mesh/mesh.cpp:486`
    is the Mesh counterpart.
  - `examples/run_hydro.cpp:193-195` — the driver's redo handling. `:176` refreshes `hydro_w` before kinetics (#257).
- Tests:
  - `tests/test_check_redo_floor.py` (`test_check_redo_floor_python`). Three arms: a floor planted in `hydro_u` only, a
    NaN with the limiter off, and a six-block Mesh with a floor in one block. Every arm must roll back, restore
    `hydro_u` and `hydro_w`, and halve dt.
  - `tests/test_check_redo_parallel.cpp` (`test_check_redo_parallel.release`, 2 ranks). One collective decision; both
    ranks roll back.
  - `tests/test_check_redo_saturation.py` (`test_check_redo_saturation_python`). A saturation failure alone redoes with
    cause 16. The counter is drained, and a failure counted between steps is not the step's.
  - `tests/test_forcing.cpp` — `limiter_*` (`:660-848`). NaN in velocity, vapor or primitive rows, a stage-entry patch,
    and a species repair redo. A clean step and a round-off repair do not.
  - `tests/test_uranus_cycle1_abort.cpp` (`test_uranus_cycle1_abort.release`). `abnormal_termination_exits_nonzero` uses
    `tests/test_abnormal_exit_floor.yaml`, whose pressure floor sits above the initial pressure. Also checks
    `column_finishes_the_two_cycles` and `UranusLate.column_reaches_cycle_40`.
  - `tests/run_straka_redo.cmake` (`test_straka_redo`). Straka at cfl 1.6 must redo at least once and reach tlim = 60 s.
- Limits / known issues:
  - The retry cures gentle events only. An eruption that passes the floor screen and floors on the next step is not
    caught (`sources/canoe__POSITIVITY_TECH_REPORT.md` §9).
  - An unrepairable vapor column is a hard abort (`TORCH_CHECK` inside the limiter), not a redo, and `floor_hit`'s
    U→W can raise it too (same report §9; code `src/eos/equation_of_state.cpp:297-299`).
  - A species repair of a bad start state requests a redo that no dt can cure. This is the #226 choice; #263 closed it
    as a driver issue, with the open question parked in #236 (`sources/gh__ISSUE_THREADS_251-294.md` #263).
  - `MeshBlockImpl::check_redo` does not check signals; only `MeshImpl::check_redo` does (`mesh.cpp:427`).
- Discrepancies:
  - `sources/canoe__POSITIVITY_TECH_REPORT.md` §10 shows a two-predicate `check_redo` with no IPR guard and §9 notes a
    per-block allreduce. Code at dae902b has six causes, the guard (`meshblock.cpp:1200`) and one reduction for all
    local blocks (`mesh.cpp:432-437`). Code wins.
  - The same report's §6 line numbers (`equation_of_state.cpp:165/166/190`) are stale: they are now 203/209/233.


#### 7.5 Operator-split pieces at the step boundary (saturation adjustment, kinetics)
<sub>inventory D: Scheme: Operator-split pieces at the step boundary (saturation adjustment, kinetics)</sub>

- Summary:
  - At the last stage, after the RK average and conserved limiter, kintera's `ThermoY` saturation adjustment runs on
    the interior (warm start).
  - Physical BCs are applied after it (#206).
  - Driver kinetics (`run_hydro`) runs after the stages on refreshed primitives with `evolve_implicit`, and is rolled
    back by a redo.
  Switch: present when `thermo.reactions` is non-empty, or when the driver has a kinetics block.
- Derivations: Lie splitting order and its error. Re-derive from `src/mesh/meshblock.cpp:796-829` and
  `examples/run_hydro.cpp:170-191`. No source derivation exists.
- Figures: a splitting diagram of one step (dynamics RK3 → saturation adjustment → BCs → kinetics → accept/redo).
- Code:
  - `src/mesh/meshblock.cpp:796` — the last-stage saturation adjustment block (the limiter again at `:798`; ThermoY
    forward at `:813`).
  - `src/mesh/meshblock.cpp:841` — `apply_boundaries` after it.
  - `examples/run_hydro.cpp:176-191` — kinetics.
- Tests:
  - `tests/test_wall_saturation.cpp` (`test_wall_saturation.release`). Phase change at walls preserves energy and water
    to 1e-12 (#206 measured about 1e-14).
  - `tests/test_check_redo_saturation.py` (above).
- Limits / known issues: `equilibrate_tp` non-convergence at max-iter 5 is counted (cause 16) but was earlier silent
  (#270).
- Discrepancies: none.


### 7.B The vertical implicit correction (VIC)


#### 7.6 VIC activation and options
<sub>inventory D: Scheme: VIC activation and options</sub>

- Summary: the vertically implicit correction (x1 only) is active iff `integration/implicit-scheme` ≠ 0.
  - Scheme 1 is "vic-partial": a 3×3 block in (ρ_total, ρv1, E).
  - Scheme 9 is "vic-full": a 5×5 block in (ρ, ρv1, ρv2, ρv3, E).
  - `size()` is 5 iff bit 3 is set.
  - Switch: YAML `integration/implicit-scheme` (int, absent ⇒ off; 0 ⇒ `nullptr`, so that explicit runs at nb1 > 1 are
    allowed). `implicit_hydro.cpp:71-82`; type names at `:84-98`.
- Derivations: none (configuration).
- Figures: a table of scheme bits → unknowns.
- Code:
  - `src/implicit/implicit_hydro.hpp:33-38` — `size()`; `:42-44` — `scheme`, `advection_cfl`, `shear_cfl` defaults.
  - `src/hydro/hydro.cpp:394-397` — the implicit solve requires both x1 faces physical (nb1 = 1). The solve has no
    cross-rank coupling.
  - `src/hydro/hydro.cpp:386` — `HydroImpl::_apply_implicit_correction`:
    - removes and restores the EOS reference energy offset around the solve (`:408`, and after the call);
    - masks `du` in solid cells (`:403`);
    - uses `fill_solid_hydro_w` as the primitive in solids;
    - for aneos, takes γ from the sound speed.
- Tests:
  - `tests/test_implicit_options_type.py` (`test_implicit_options_type_python`). `type()` names 0/1/9; scheme 5 raises.
  - `tests/test_hydro_options.cpp` — `reject_unsupported_implicit_scheme` (`:195`).
  - `tests/test_backward_substitution.cpp` — `implicit_options.parses_implicit_scheme_bits` (`:308`).
- Limits / known issues: NMASS > 0 (CMake `NMASS`, `cmake/parameters.cmake:3`, default 0) is unsupported with the 5×5
  matrix (PR #223 Limits).
- Discrepancies: none.


#### 7.7 VIC block-tridiagonal assembly (Roe-linearised flux Jacobian, |A| dissipation, I/dt, gravity coupling, wall closure)
<sub>inventory D: Scheme: VIC block-tridiagonal assembly (Roe-linearised flux Jacobian, |A| dissipation, I/dt, gravity coupling, wall closure)</sub>

- Summary: per column and per cell i, the code builds blocks with `half_inv_vol = 0.5/V_i`:
  - a_i = (|A|_{i−½}·A_{i−½} + |A|_{i+½}·A_{i+½} + (A_{i+½}−A_{i−½})·∂F/∂q|_i)·half_inv_vol − Φ + I/dt;
  - b_i = −(|A|_{i−½} + ∂F/∂q|_{i−1})·A_{i−½}·half_inv_vol;
  - c_i = −(|A|_{i+½} − ∂F/∂q|_{i+1})·A_{i+½}·half_inv_vol.
  - |A| = R·|Λ|·R⁻¹ at the Roe average with γ averaged across the face.
  - Φ couples gravity: momentum ← g·ρ and energy ← g·ρv1.
  - Reflecting closure at the column ends and next to solid cells: a += b·Bnd or a += c·Bnd, with
    Bnd = diag(1, −1, 1[, 1, 1]).
  - Partial uses 3×3 sub-blocks taken from the 5×5 Jacobians.
  - Switch: scheme (above). The gravity-work flags `adir` are set from `forcing/const-gravity/gravity-work`.
- Derivations:
  - Linearised implicit FV update (Newton step on the semi-discrete x1 operator), with the upwind-split Roe flux
    F = ½(F_L + F_R) − ½|A|(q_R − q_L). Re-derive from `src/implicit/vic_assemble_full_impl.h:51-99`. No step-by-step
    derivation exists in the sources. The gravity-work draft §3.7 (`sources/gw__GRAVITY_WORK_TECH_REPORT_draft.md:226`)
    states only the operator form (I/(w2 dt) + J)Δq = RHS.
  - Flux Jacobian, Roe average, eigenvectors: re-derive from `src/implicit/flux_decomposition_impl.h:38`
    (`RoeAverage`), `:71` (`Eigenvalue`), `:77` (`Eigenvector`), `:106` (`FluxJacobian`).
  - Reflecting-wall closure Bnd (ghost = mirror state, normal momentum odd): re-derive from
    `vic_assemble_full_impl.h:44-45,122-126`.
  - Partial (3×3) reduction, and why species enter only through ρ_total: re-derive from
    `vic_assemble_partial_impl.h:56-120` and `forward_sweep_impl.h:35-40`.
- Figures:
  - A three-cell stencil showing faces i±½ with A, |A| and the Jacobians at cells i−1, i, i+1, and the resulting a, b, c
    blocks.
  - The column end with a mirror ghost and the Bnd fold of b into a.
  - A column with a solid cell in the middle: an identity row and two closed sub-columns.
- Code:
  - `src/implicit/vic_assemble_full_impl.h:17` — `vic_assemble_full_impl`. Φ at `:38-40`; Bnd at `:44-45`; a/b/c at
    `:94-99`; closure at `:123-126` (`periodic` is always false).
  - `src/implicit/vic_assemble_partial_impl.h:30` — `vic_assemble_partial_impl`. Φ at `:46-48`; a/b/c at `:115-120`;
    closure at `:143-144`.
  - `src/implicit/implicit_dispatch.cpp:22` / `:77` — CPU assembly loops. Solid rows a = I/dt, b = c = 0 at `:57-63`
    and `:113-119`; solid neighbours set `solid_lower`/`solid_upper`.
  - `src/implicit/implicit_dispatch.cu:32` / `:85` — CUDA assembly, one thread per cell.
  - `src/implicit/implicit_hydro.cpp:160` — `ImplicitHydroImpl::forward_masked`. It projects to the local orthonormal
    frame (`:227-231`) and builds the TensorIterator (`:245-264`). The full pipeline is at `:335-356`.
  - **Gravity-work entries into the matrix (list only; another author covers them):**
    - `src/implicit/vic_assemble_partial_impl.h:46-48` and `vic_assemble_full_impl.h:38-40` — Φ, the linearised
      gravity body force and the cell work in the energy row.
    - `vic_assemble_partial_impl.h:122-140` and `vic_assemble_full_impl.h:101-120` — energy-row face work: the
      `kVicFaceWork`, `kVicCartesianFaceWork` and `kVicDiffusiveCell` branches, using the weights `work_lo`/`work_hi`.
    - `src/implicit/implicit_dispatch.hpp:27-30` — the flag constants.
    - `src/implicit/implicit_hydro.cpp:239-242` — the `work_lo`/`work_hi` metric weights.
    - `implicit_hydro.cpp:266-277` — `adir` selection from `gravity-work`.
    - `implicit_hydro.cpp:301-333` — `couple_radial_exact` (SNAP_GRAVITY_WORK_RADIAL_EXACT) subtracts the corrected-PE
      stencil from `_a`/`_b`/`_c` (`:326-328`).
    - `src/hydro/hydro_forward.cpp:969-975` — the explicit face correction is added to `du` before the solve when face
      work is in the operator.
    - Post-solve energy bookkeeping: `implicit_hydro.cpp:382-414` (projection and clamp work), `:423-444` (legacy
      face-wallc swap) and `:451-471` (radial-exact remainder).
    - Switches: `forcing/const-gravity/gravity-work` (`src/forcing/const_gravity.cpp:28`, default `"cell"`) and env
      `SNAP_GRAVITY_WORK_RADIAL_EXACT` (`src/hydro/hydro.cpp:226`, default `"1"`, acting only with `face` on
      cartesian or spherical-polar, `:234-240`).
- Tests:
  - `tests/test_implicit_gravity_tall_column.py` (`test_implicit_gravity_tall_column_python`). An 11.3H rest column
    stays at rest up to Courant 250. W_TOL is 1e-7 m/s and W_SETTLED 1e-10 m/s (`:31-33`, chosen by the author with no
    derivation).
  - `tests/test_vic_moist_device.py` (`test_vic_moist_device_python`, CUDA only). CPU and CUDA agree to 1e-9: measured
    5.8e-11, about 17× margin (`:13-17`). Schemes 1 and 9 each move the state by more than 1e-8 relative to scheme 0.
  - `tests/test_implicit_stratified_solid.py` (`test_implicit_stratified_solid_python` and the `_radial_exact` twin).
    Tall columns, solid closure, energy (EPE_TOL from the tall-column helper).
  - `tests/test_implicit_face_work_jacobian.cpp` (`test_implicit_face_work_jacobian.release`) — gravity-work author.
- Limits / known issues:
  - The column ends always get the reflecting closure, whatever the x1 BC function (outflow or periodic x1 are not
    refused; there is no `is_outflow` check in `src/implicit/` or `hydro.cpp`).
  - `first_block`/`last_block` are always true, and the distributed sweep is commented out
    (`forward_sweep_impl.h:55-60,136-137`). The VIC is single-rank in x1 by decision (`vic_redistribute_impl.h:75-76`).
  - The tall-column report's lid-closure ×8 (`Ap *= 8.`) is **not** in the code (a grep finds none). It was superseded
    (`sources/canoe__tall_column_instability_TECH_REPORT.md` §3b).
- Discrepancies:
  - The comments at `vic_assemble_partial_impl.h:19-24,110` refer to `vic_solve_partial_impl()`. That function no
    longer exists (a grep finds only the comments).


#### 7.8 Stage-weighted implicit time step (dt_corr = w2·dt)
<sub>inventory D: Scheme: Stage-weighted implicit time step (dt_corr = w2·dt)</sub>

- Summary: the VIC is nonlinear in dt. For 3-stage integrators the solve uses dt_corr = wght2(stage)·dt, while `du`, the
  divergence and the forcings stay at full dt, so the stage applies (I + w2·dt·J)⁻¹(w2·dt·L). Other integrators use the
  full dt. If `rk_stage` was not published, a `TORCH_WARN_ONCE` fires. Switch: none. It keys on `stages.size()==3`.
- Derivations: show that `ForwardSweep` with rhs = du/dt_c and a = I/dt_c + J, followed by the RK multiplication by w2,
  equals (I + w2·dt·J)⁻¹(w2·dt·L). Re-derive from `src/hydro/hydro_forward.cpp:925-951` and `forward_sweep_impl.h:35-49`.
  The comment there states the result. PR #221 and the tall-column report §3a/§5 give the motivation and the measured
  effect (weak) but no derivation.
- Figures: two arrows per stage, "RHS scaled by w2" versus "operator regularised by I/(w2·dt)".
- Code:
  - `src/hydro/hydro_forward.cpp:938-951` — the `dt_corr` logic (`:941` multiplies by `wght2`).
  - `src/hydro/hydro_forward.cpp:977` — `_apply_implicit_correction(du, w, dt_corr, other)`.
  - `src/hydro/hydro.hpp:207` — `int rk_stage = -1`.
- Tests: `tests/test_forcing.cpp` — `implicit_gravity_work_holds_under_rk3_stage_weighting` (`:1192`, plus a CUDA twin
  at `:1196`). The stage-momentum difference must exceed 1e-6 (`:1188`), which is red when the weighting is dropped
  (PR #221).
- Limits / known issues: rk3 only. rk3s4 and rk2 keep the full-dt operator (`hydro_forward.cpp:936-939`, a comment
  "generalising would change rk1/rk2 results").
- Discrepancies: the tall-column report §3a says the linear rest metric got slightly worse (1.796→2.302) while the
  nonlinear signal improved weakly (p = 0.07). Both are stated as true. The code carries the change. Record it as
  "weak evidence".


#### 7.9 Block-tridiagonal forward sweep and backward substitution
<sub>inventory D: Scheme: Block-tridiagonal forward sweep and backward substitution</sub>

- Summary: a block Thomas algorithm per column. For N = 5, each pivot block is LU-factored with partial pivoting
  (`ludcmp`) and [c | rhs] is solved by `lubksb`. For N = 3, the factorisation runs on a copy as a pivot check, then
  Eigen `inverse()` is used. Recurrences: a_i ← a_i − b_i·a_{i−1}; δ_i = a_i⁻¹(rhs_i − b_i·δ_{i−1}); a_i ← a_i⁻¹c_i;
  back-substitution δ_i −= a_i·δ_{i+1}. The rhs is (Σ du_mass, du_mom…, du_E)/dt. Switch: none.
- Derivations: block Thomas recurrences and their stability (diagonal dominance is not guaranteed). Re-derive from
  `src/implicit/forward_sweep_impl.h:26-139` and `src/implicit/vic_redistribute_impl.h:28-36`.
- Figures: a block-tridiagonal matrix sketch with the forward-elimination and back-substitution arrows.
- Code:
  - `src/implicit/forward_sweep_impl.h:26` — `ForwardSweep<T,N>`. N > 4 uses the LU path (`:61-73`, `:108-120`). N = 3
    uses a checked inverse (`:74-80`, `:121-127`). Finite checks on δ and a sit at `:81-86` and `:128-133`.
  - `src/implicit/vic_redistribute_impl.h:28` — `vic_backward_substitute`. It skips when δ[il] is non-finite (the
    sentinel).
  - `src/math/ludcmp.h:30` — `ludcmp`. `src/math/lubksb.h:25,49` — vector and matrix `lubksb`.
  - `src/implicit/implicit_dispatch.cpp:134` — `vic_solve_cpu<N>`. It calls `ForwardSweep` at `:159` and skips back
    substitution on failure.
  - `src/implicit/implicit_dispatch.cu:141` — `vic_solve_cuda<N>`. The same skip is at `:165-167`.
  - `src/implicit/tridiag_thomas_impl.h:24,109` — legacy `forward_sweep_impl` / `backward_substitution_impl`. **Used
    only by `tests/test_lu_failure.cpp`** (the production include graph does not reach it; PR #292 says so too).
- Tests:
  - `tests/test_lu_failure.cpp` (`test_lu_failure.release`). `current_*` and `legacy_*` sweep cases for float/double,
    N = 3/5 (`:200-207`). Nonsingular columns succeed with finite δ; singular and near-singular columns return false.
  - `tests/test_backward_substitution.cpp` (`test_backward_substitution.release`). Back substitution plus redistribution
    conserve the column integrals at 1e-12.
- Limits / known issues: there is no pivoting across blocks and no conditioning estimate (see the LU guard).
- Discrepancies: none.


#### 7.10 LU pivot tolerance and failed-column sentinel (#290)
<sub>inventory D: Scheme: LU pivot tolerance and failed-column sentinel (#290)</sub>

- Summary: `ludcmp` returns ±1 (parity) or 0 on failure. It rejects a non-finite input or output, a zero-row scale, and
  any pivot with |p_j|/s_j ≤ 8·N·ε_T, where s_j is the original row max carried with the permutation. On failure the
  sweep writes NaN into δ for the whole column (`vic_fail_column`). The host treats any non-finite δ as a rejected
  column. Switch: none (the tolerance is a compile-time formula).
- Derivations:
  - exists: `docs/derivations/290-lu-pivot-tolerance.md@e894700` (same as `sources/deriv__290-lu-pivot-tolerance.md`
    up to wording). It derives the γ_{2N} ≈ N·ε accumulation scale and the factor 8 guard band, shows scale invariance,
    and tabulates the thresholds (float 2.86e-6/4.77e-6; double 5.33e-15/8.88e-15). The note says it is a guard, not a
    condition-number bound.
- Figures: a plot of the pivot ratio |p|/s versus the threshold for a few random 3×3/5×5 matrices (illustrative). A flow
  diagram: ludcmp 0 → NaN sentinel → host reject → redo cause 32.
- Code:
  - `src/math/ludcmp.h:35` — `tolerance = 8·N·ε`; `:36-38` input finiteness; `:45` zero row; `:83` pivot rejection;
    `:90-92` output finiteness.
  - `src/implicit/vic_solve_failure.h:14` — `vic_fail_column` (NaN sentinel in δ).
  - `src/implicit/forward_sweep_impl.h:64,76,111,123` — the four production `ludcmp == 0` checks.
- Tests:
  - `tests/test_lu_failure.cpp` — `float_three`/`float_five`/`double_three`/`double_five` (`:196-199`). Exact return
    codes for scaled near-singular rows, final zero pivot, and nonfinite entries.
  - `tests/test_lu_failure.cpp` — `finite_near_singular_forward_masked` (`:291`; CUDA twin `:295`). A finite float32
    column with dt = 1e4 is rejected by the relative guard alone.
  - `tests/test_lu_failure.cpp` — `float_rest_column_finite_vicclamp` / `double_rest_column_finite_vicclamp`
    (`:351-354`). A rest column is accepted and the clamp meter stays finite and zero (#294).
- Limits / known issues:
  - Float32 is much stricter. An independent probe rejected 166/5000 matrices at cond 1e6 and 4915/5000 at 1e8 (derivation
    note "Float32 VIC conditioning limitation"). A smaller dt is not guaranteed to cure it, so use float64.
  - Acceptance does not certify accuracy (derivation note; #286).
- Discrepancies: the source copy and the committed doc differ only in attribution wording (lines 55/63 of the doc).


#### 7.11 VIC solve rejection, latch and rollback (cause 32)
<sub>inventory D: Scheme: VIC solve rejection, latch and rollback (cause 32)</sub>

- Summary: `forward_masked` checks finiteness at four points: inputs (du, w, γ), δ after the sweep, results (du and the
  mass correction), and the final correction. Any bad column calls `reject`, which:
  - restores `du` and `w`;
  - zeroes the correction and the mass correction;
  - logs rank, column, step, stage and retry;
  - latches `_solve_failed`.
  Later stages return zero corrections while latched. `check_redo` reports cause 32. Stage 0 resets the latch. Switch:
  none.
- Derivations: none (policy). Document the invariant "a failed column is never back-substituted or redistributed".
- Figures: a state machine (stage s: solve OK / reject → latched → zero correction → check_redo cause 32 → restore u0 →
  retry or terminate).
- Code:
  - `src/implicit/implicit_hydro.cpp:176-180` — the latched early return; `:198` keeps `w0` for exact restore; `:200-218`
    is the `reject` lambda; `:222-224` input check; `:350-351` sentinel check; `:473-475` result check; `:480-481`
    correction check.
  - `src/implicit/implicit_hydro.hpp:96-97` — `solve_failed()` / `reset_solve_failure()`.
  - `src/mesh/meshblock.cpp:618` — the stage-0 reset; `:1285` passes the cause into `local_redo_flags`; `:860` makes the
    gravity fixer skip a step with a failed solve.
- Tests:
  - `tests/test_lu_failure.cpp` — `partial/full_retry_restores_step`, `partial/full_stop_restores_step`,
    `*_assembly_*` (dt = 0 makes the assembly non-finite) and their CUDA twins (`:208-240`). `du` and `w` stay untouched,
    `check_redo` returns 1 or −1, and `hydro_u` equals the saved step input. All checks are exact (`torch::equal`).
  - `tests/test_lu_failure.cpp` — `mesh_terminal_failure_restores_all_blocks` (`:242`). A two-local-block terminal stop
    restores every block.
- Limits / known issues:
  - `_clamp_residual` is a running maximum that is never reset. The `reject` lambda does not restore it, so a NaN from a
    late reject can persist in that diagnostic (PR #292 "Five-request review revision" item 5; still true at
    `implicit_hydro.cpp:376-377`, with `reset()` at `:118-119` the only zeroing).
  - The old NaN guard remains as a commented-out block at `implicit_hydro.cpp:190-192`. The live checks are the finite
    checks above.
- Discrepancies: `sources/canoe__positivity_dry_channel_TECH_REPORT.md` §7 says "both NaN guards in
  `implicit_hydro.cpp` are commented out". At dae902b, live finiteness rejection exists (`:222`, `:350`, `:473`,
  `:480`). Code wins; the report predates #290/#292.


#### 7.12 VIC constituent redistribution (implicit mass correction as face fluxes; "Component B")
<sub>inventory D: Scheme: VIC constituent redistribution (implicit mass correction as face fluxes; "Component B")</sub>

- Summary: per column, the code applies these passes.
  - φ_i = (δ_i(0) − Σexplicit)·V_i, with residual R = Σφ.
  - φ'_i = φ_i − R·m_i/Σm.
  - Face transfers M come from a prefix sum (closed bottom, top ≈ 0).
  - Dry gas (pass 3a) and each species (pass 3b) move by M times the donor mass fraction, with sequential availability
    clamps.
  - The final per-cell map adds the dry and species increments, and assigns momentum and energy from δ.
  - Solid cells split the column into independent closed segments.
  - The passive scalars ride the clamped dry transfer.
  Switch: none. This runs always with the VIC.
- Derivations:
  - Uniqueness of face transfers for a zero-sum set of increments in a closed column, and exact telescoping: the
    statement exists in `sources/canoe__POSITIVITY_TECH_REPORT.md` §5 (Component B), not step by step. Re-derive from
    `src/implicit/vic_redistribute_impl.h:78-161` (the comment at `:38-76` is the clearest statement).
  - The donor-upwind mixing-ratio transport and why it advects composition: re-derive from `:134-160`.
  - The passive-scalar transfer by the dry flux: re-derive from `src/mesh/meshblock.cpp:663-676`.
- Figures:
  - A column with per-cell φ arrows turned into face arrows M (prefix sum), with R removed mass-weighted.
  - Donor-upwind species transfer at one face: the sign of M picks the donor y.
  - A column split by a solid cell into two segments.
- Code:
  - `src/implicit/vic_redistribute_impl.h:78` — `vic_constituent_column`: pass 1 `:83-93`; pass 2 `:95-101`; pass 3a
    `:104-132`; pass 3b `:134-160`.
  - `src/implicit/vic_redistribute_impl.h:166` — `vic_redistribute_cell`.
  - `src/implicit/implicit_dispatch.cpp:173` — `vic_redistribute_cpu<N>`, with the solid-segment loop at `:199-214`.
    CUDA is at `implicit_dispatch.cu:200,224`.
  - `src/implicit/implicit_hydro.cpp:358-378` — the clamp-residual meter (per-cell |ΣMASS·V − (M_i − M_{i+1})|/scale;
    the float32 floor is FLT_MIN, #294). `:379-380` holds the dry-clamp step flag.
  - `src/mesh/meshblock.cpp:663-676` — the scalar transfer by the dry-gas face mass (`mass_corr[IVY]`).
- Tests:
  - `tests/test_backward_substitution.cpp` — `conserves_constituent_column_tendencies` (`:70`, 1e-12),
    `dry_only_transport_is_conservative_and_clamped` (`:159`), the dry-fraction-above-one mark (`:200`),
    `a_drained_species_donor_stays_non_negative` and its float twin (`:300,304`).
  - `tests/test_tracer_dry_convention.py` (`test_tracer_dry_convention_python`) — tracers ride the dry gas.
  - `tests/test_cycle_diagnostics.cpp` — `vicclamp_reads_the_clamped_fraction` (`:367`).
- Limits / known issues:
  - The momentum and energy rows are assigned from δ while density is clamped, so a binding clamp leaves an
    inconsistent triple. Open in `sources/canoe__positivity_dry_channel_TECH_REPORT.md` §4. It is mitigated (not fixed)
    by redo cause 2 (Ch 8).
  - The top-face residual M_top is not zero in floating point, and it lands on the top cell (same report §6). The code
    comment at `vic_redistribute_impl.h:102` says "exactly zero up to roundoff". No compensation is implemented.
- Discrepancies: the dry-channel report's §8 proposal (abort mode, in-kernel hit counter) is not implemented. #223
  instead added the donor mark `MASS(IPR)` and redo cause 2. Code wins.


#### 7.13 VIC column closure versus the x1 boundary type
<sub>inventory D: Scheme: VIC column closure versus the x1 boundary type</sub>

- Summary: the implicit column always assumes closed reflecting ends (the Bnd fold) and requires both x1 faces to be
  physical (nb1 = 1). It does not consult the boundary-function type. Switch: none.
- Derivations: see Ch 7 (Bnd closure).
- Figures: none beyond Ch 7.
- Code: `src/implicit/vic_assemble_full_impl.h:122-126`; `vic_assemble_partial_impl.h:142-144`; `src/hydro/hydro.cpp:394-397`.
- Tests: none for outflow or periodic x1 with the VIC.
- Limits / known issues: outflow or periodic x1 combined with `implicit-scheme` ≠ 0 is accepted silently, with
  inconsistent closure. Recommend a guard or documentation.
- Discrepancies: none in the sources (not discussed).


---

<a id="ch8"></a>
## Chapter 8. Positivity, floors and limiters

The tracer flux positivity limiter and the carry of energy and momentum with withheld species mass, the passive-scalar limiter, the EOS limiters and floors, the reconstruction and well-balanced face floors, the dry-channel positivity inside the VIC, round-off thresholds and the redo detector. Two pairs of entries came from two inventories and overlap (the carry; the EOS floors); the chapter author merges each pair into one section.

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: every mechanism that keeps the state physically admissible or detects that it is not: the tracer flux limiter θ
(hydro species and passive scalars, with the complement upper bound); carry of energy and momentum with withheld mass;
the conserved and primitive EOS limiters (NaN fill, density, energy and temperature floors, condensate borrow,
parentless-cloud and vapor column repairs); reconstruction-stage floors; the well-balanced face floor; dry-channel
handling inside the VIC; round-off thresholds; and the limiter marks that feed `check_redo`.

Recommendations on structure:
- Organise by the **variable protected**: species (θ limiter, VIC pass 3b, EOS species repairs), dry density and
  pressure (floors, WB face floor, VIC pass 3a, the redo floor detector), and energy and temperature (the T-floor).
- Make clear early that **snapy guarantees no thermodynamic positivity of ρ or p**. Only floors (non-conservative) and
  redo detection exist. The θ limiter acts on tracer channels only (`hydro_forward.cpp:657`, `ny > 0`).
- `fix_vapor` is a column repair, not a floor. Keep it in this chapter under "repairs", with its algorithm as its own
  scheme.
- Note that a single switch (`equation-of-state/limiter`) turns on the θ limiter, the EOS floors, the reconstruction
  floors and the species clamps together (`sources/canoe__POSITIVITY_TECH_REPORT.md` §5–6). This coupling is a
  documented design fact.

</details>


#### 8.1 Tracer flux positivity limiter θ (hydro species channels)
<sub>inventory D: Scheme: Tracer flux positivity limiter θ (hydro species channels)</sub>

- Summary: after the stage fluxes are final (Riemann, sedimentation, x1 seam averaging), per cell and species:
  - out_i = Σ_faces max(±A_f·F_f, 0);
  - θ_i = min(1, u_i⁺·V_i·(1 − 4096ε)/(dt·out_i)), and θ = 1 where out = 0 and in ghosts;
  - θ's ghosts are filled by a raw exchange (`interpolate(false)`) plus the physical BC functions with `kScalar`;
  - each face flux is multiplied by the donor's θ (donor chosen by the sign of that species' flux).
  Switch: `dynamics/equation-of-state/limiter` (YAML, default false; `src/eos/equation_of_state.cpp:74`,
  struct default `equation_of_state.hpp:52`) **and** ny > 0.
- Derivations:
  - Single-step positivity plus exact conservation (one factor per face): exists:
    `sources/canoe__POSITIVITY_TECH_REPORT.md` §3.
  - Extension to SSP stages: exists, same §3 (the α = w2/w1 ≤ 1 convexity argument).
  - The 4096-ulp margin: **no derivation exists**. The report §8 says "magic constant … a derivation would help".
    Re-derive a round-off bound from `src/hydro/flux_positivity.cpp:61-71` (cancellation in u + Δu ≈ 0).
- Figures:
  - A 2-D cell with four faces: outgoing fluxes summed, θ computed, then each face scaled by its donor's θ (one number
    per face, shared by both cells).
  - A panel seam with θ ghosts, contrasting the interpolated ghost (broken, a blend) with the raw copy (correct).
  - A sketch of the margin: an exact-zero target lands at −ulp; the margin target stays at +4096 ulp.
- Code:
  - `src/hydro/flux_positivity.cpp:22` — `flux_positivity_theta` (faces il..iu+1 mirror the divergence; margin at
    `:65-66`; `where` at `:69-71`).
  - `src/hydro/flux_positivity.cpp:74` — `flux_positivity_scale_` (donor selection `:83-86`).
  - `src/hydro/flux_positivity.hpp:32-56` — the contract, including the ghost-fill requirement.
  - `src/hydro/hydro_forward.cpp:657` — the call site (gated on `eos.limiter && ny > 0`). θ at `:664`. The census meters
    are `_positivity_hits` (`:668`), `_positivity_severe` (`:677`, θ < 0.9 with withheld mass above round-off) and
    `_positivity_min`. The ghost fill is at `:684-697` (exchange `interpolate(false)` at `:688`, bfuncs at `:696`).
    Scaling at `:707`; the cut meters `_lim_flux`/`_lim_cut` at `:709-715`.
- Tests:
  - `tests/test_flux_positivity.py` (`test_flux_positivity_python`). Slab A/B with unlimited cp5. The base arm must go
    below −1e-12; the limited arm min ≥ −1e-15 with hits > 0; vapor and scalar drift < 1e-12. The periodic wrap
    exercises the θ ghost fill.
  - `tests/test_flux_positivity_cubedsphere_moist.py` (`test_flux_positivity_cubedsphere_moist_python`, plus `_cuda`).
    The hydro species θ across a panel seam: drift < 1e-13 (DRIFT_TOL, about 50× the measured floor of 2e-14 per the
    report §11); fires; species ≥ 0.
  - `tests/test_sedimentation_cubed_seam.cpp` (`test_sedimentation_cubed_seam.release`, 2 ranks, plus `_gloo`). Seam
    fluxes are identical on both ranks and condensate mass is conserved.
- Limits / known issues:
  - A fully limited face freezes transport (θ → 0 means no flux, not donor-cell). The "scale only the increment above an
    upwind base" repair is not done (report §12).
  - Per-species θ breaks linear constraints across tracers (report §7, §12).
  - The float32 margin is 4.9e-4 (report §8, §12).
  - The θ x1 ghosts are not exchanged on a cubed sphere with nb1 > 1, a disallowed configuration (report §7).
  - The guarantee needs the mass Courant number < 1 per stage. With a VIC the explicit vertical species flux can drain
    order-one fractions (report §5 D1(b)); θ handles that drain, but it is the regime in which θ fires most.
- Discrepancies: the report §2 cites the call site at `hydro_forward.cpp:331`; it is now `:657`. The §10 excerpt
  hard-codes `4096.*eps`; the code uses `kPositivityRoundoffUlp` (`flux_positivity.hpp:18`). The value is the same.


#### 8.2 Carry of energy and momentum with withheld species mass
<sub>inventory D: Scheme: Carry of energy and momentum with withheld species mass</sub>

- Summary: before scaling, for each face and species, dm = (1 − θ_donor)·F. The energy flux loses dm·h_spec(donor) and
  the momentum flux loses dm·v(donor). In x1 the advected and settling parts are each withheld at their own donor.
  Switch: same as θ, and only where `peos->species_enthalpy(w)` is defined (ideal-moist and moist-mixture since #269).
- Derivations: conservation of energy and momentum in the donor/receiver pair when mass is withheld. Re-derive from
  `src/hydro/flux_positivity.cpp:106-149`. PR #226/#269 bodies state the result only.
- Figures: one face with mass, energy and momentum arrows, showing the withheld part staying in the donor, and the
  split into advected and settling donors for a mixed flux.
- Code:
  - `src/hydro/flux_positivity.cpp:106` — `flux_positivity_carry_` (share `:125`, the advected/settling split `:136-143`).
  - `src/hydro/hydro_forward.cpp:701-706` — the call. The settling part is `fsed1`, built at `hydro_forward.cpp:428-432`.
- Tests: `tests/test_flux_positivity_carry.cpp` (`test_flux_positivity_carry.release`). Seven or more cases: advected,
  settling, x2, non-uniform donors, mixed, moist-mixture, and CUDA twins. The dry flux is untouched exactly. The energy
  and momentum withheld equal the hand values at 1e-12·max(|e0|, |dE|) (`:143`).
- Limits / known issues: the carry runs only if `hspec` is defined (`hydro_forward.cpp:703`). For a non-ideal EOS
  (z ≠ 1) the study is parked (#276).
- Discrepancies: `sources/canoe__POSITIVITY_TECH_REPORT.md` §7/§12 lists "the mass/energy partition" as open ("θ scales
  the species channel but not the momentum and enthalpy"). At dae902b, `flux_positivity_carry_` does withhold energy and
  momentum (#226/#269). The open item is closed for ideal-moist and moist-mixture. Code wins; the report predates #226.


#### 8.3 Positivity-limited species fluxes carry energy and momentum (moist carry)
<sub>inventory B: Scheme: Positivity-limited species fluxes carry energy and momentum (moist carry)</sub>

- Summary: when the species flux limiter withholds mass `dm = (1-theta_donor) F`, the energy `dm * h_spec(donor)` and
  momentum `dm * v(donor)` are withheld from the same face. The x1 flux is split into advected `F - fsed1` and settling
  `fsed1` parts, each with its own donor. `h_spec` comes from `EOS::species_enthalpy(w)` (ghosts included, not
  exchanged). Switch: `limiter: true` with species.
- Derivations:
  - Enthalpy carried per species and the conservation oracles (energy, momentum, column ratios). PR #269/issue #236 give results and measurements, not a derivation; re-derive from `src/hydro/flux_positivity.cpp:106-147` and `src/eos/moist_mixture.cpp:196-218`. General positivity theory: cross-ref the positivity chapter.
- Figures:
  - Face between donor/receiver: limited mass flux with its enthalpy and momentum withheld; advected vs settling parts with opposite donors.
- Code:
  - `src/hydro/hydro_forward.cpp:686` — `hspec = peos->species_enthalpy(w)`; `:704` `flux_positivity_carry_`.
  - `src/hydro/flux_positivity.cpp:106` — `flux_positivity_carry_`.
  - `src/hydro/hydro_forward.cpp:427-431` — `fsed1` capture.
- Tests:
  - `tests/test_flux_positivity_carry.cpp:174`, `:189`, `:202`, `:243`/`:247`, `:339`/`:344`, `:354`/`:364`, `:381` (`test_flux_positivity_carry.release`).
  - `tests/test_flux_positivity_cubedsphere_moist.py` (`_python`, `_cuda_python`).
- Limits / known issues: verified only for z = 1 (issue #276, parked); arm G not done (PR #269).
- Discrepancies: none.


#### 8.4 Passive-scalar limiter and complement upper bound
<sub>inventory D: Scheme: Passive-scalar limiter and complement upper bound</sub>

- Summary: the passive-scalar flux gets the same θ (lower bound). With `scalar/upper-bound` b > 0, a second θ is computed
  for the complement bρ − s, whose flux is b·F_mass − F_s. The code scales g = b·F_mass − F_s and adds the change
  (h − g) back to F_s, never recomputing F_s. Switch: the EOS limiter (lower bound); `scalar/upper-bound` (YAML, default
  −1 = off, `src/scalar/scalar_options.cpp:27`). b = 0 is refused (`src/scalar/scalar.cpp:25`), and b > 0 requires the
  EOS limiter (`:28-31`).
- Derivations:
  - r ≤ b as positivity of the complement: the statement exists in `sources/canoe__POSITIVITY_TECH_REPORT.md` §7.
    Re-derive the conservation and boundedness argument from `src/scalar/scalar.cpp:164-200`.
  - The add-the-change rule (bitwise identity where θ = 1): exists as an argument in the same §7. Short and adequate.
- Figures: the complement trick shown as a mirrored bar chart (s and bρ − s), with a face scaled toward donor-cell
  transport at the bound.
- Code:
  - `src/scalar/scalar.cpp:140` — `sync_theta` (raw exchange, bfuncs `kScalar`); `:158-161` — the lower bound;
    `:175-200` — the upper bound (`:188` θ of the complement; `:190` scaling).
- Tests: `tests/test_flux_positivity_cubedsphere.py` (`test_flux_positivity_cubedsphere_python`, plus `_cuda`). A hat
  and its complement across a seam keep drift < 1e-13 and stay in [0, 1], and the limiter fires.
- Limits / known issues: the bound needs the mass Courant number < 1, and density moving only by −dt·∇·F_mass. Scheme 9
  and forcings that write `du[IDN]` break the second condition (report §7, "empirical, not proof").
- Discrepancies: none.


#### 8.5 Conserved-variable EOS limiter (`apply_conserved_limiter_`)
<sub>inventory D: Scheme: Conserved-variable EOS limiter (`apply_conserved_limiter_`)</sub>

- Summary: in this order:
  1. NaN → 0, marking `limiter_marks_[1]` if interior.
  2. Dry density clamp_min(density_floor).
  3. Energy clamp_min(KE + I(T_floor)) via "UT→I".
  4. Each cloud with parent metadata borrows its deficit from its parent vapours by stoichiometric mass fraction, then
     clamps to 0.
  5. Parentless clouds get a column repair (failure tolerated), then clamp ≥ 0.
  6. Vapor gets a column repair (failure throws).
  For split x1 columns with `whole_column`, the column is gathered across blocks. A density or energy change marks
  `limiter_marks_[0]`. A species change above `positivity_roundoff·ρ` marks it too. Switch: `equation-of-state/limiter`
  (default false). Floors: `density-floor` (YAML default 1e-6), `pressure-floor` (1e-3), `temperature-floor` (20)
  (`equation_of_state.cpp:65,71,72`).
- Derivations:
  - Condensate borrow conserves mass and elements: re-derive from `src/eos/equation_of_state.cpp:252-271` and the
    `cache_cloud_parents_` mass fractions (`:110`). The report §6 states it only.
  - The temperature floor I(T_floor) = offset + ρc_v·T: exists in `sources/canoe__COLUMN_CORRECTNESS_TECH_REPORT.md` §1
    (an algebraic identity with W→I, adequate). Code at `src/eos/ideal_moist.cpp:293-316`.
  - The density floor is non-conservative (it creates mass): state it, nothing to derive.
- Figures:
  - The limiter pipeline as a vertical flowchart, marking which steps conserve (borrow, column repairs) and which do not
    (NaN fill, floors).
  - A column with a gathered split across two blocks (`gather_x1`).
- Code:
  - `src/eos/equation_of_state.cpp:192` — `apply_conserved_limiter_`; NaN `:201-203`; density floor `:209`;
    energy/T floor `:226-234`; mark `:235`; borrow `:252-271`; `repair_column` `:276-306` (split gather `:280-284`;
    `call_fix_vapor` at `:296`; the throw at `:297-299`); parentless `:308-311`; vapor `:312`; species mark `:316-321`.
  - Call sites: after every RK average (`src/mesh/meshblock.cpp:756`), before saturation adjustment (`:798`), and
    inside every EOS's U→W/W→U (for example `src/eos/ideal_gas.cpp:87,91`, `src/eos/moist_mixture.cpp:121,126`).
  - `src/eos/equation_of_state.cpp:352` — `reset_limiter_marks`. `equation_of_state.hpp:168` — `limiter_marks()`.
- Tests:
  - `tests/test_condensate_conservation.cpp` (`test_condensate_conservation.release`). Multi-vapour condensate debits
    the stoichiometric mass.
  - `tests/test_cloud_parent_slots.cpp` (`test_cloud_parent_slots.release`). Global-registry parent index (#223).
  - `tests/test_parentless_cloud.cpp`, `tests/test_parentless_cloud_nb1.cpp`, `tests/test_parentless_cloud_nb1_mp.cpp`
    (2 ranks, plus `_gloo`). The column repair keeps mass and is independent of nb1.
  - `tests/test_vapor_column_nb1.cpp` (`test_vapor_column_nb1.release`). Vapor repair with nb1 = 1 versus 2 (#267).
  - `tests/test_eos_temp2inteng.py` (`test_eos_temp2inteng_python`). UT→I equals W→I at T to relative 1e-12, and is
    affine with the offset as intercept.
  - `tests/test_forcing.cpp` — `limiter_patch_is_reported_below_the_temperature_floor` (`:660`), `limiter_marks_on_cuda`
    (`:778`), `limiter_species_repair_redoes_the_step` (`:805`), `limiter_roundoff_species_repair_is_not_redone` (`:824`),
    `limiter_float32_roundoff_is_ulp_of_float32` (`:848`).
- Limits / known issues:
  - The density floor creates mass one way (`sources/canoe__positivity_dry_channel_TECH_REPORT.md` §7).
  - `limiter: true` also disables the reconstruction-floor safety net in the `shock: true` path (report §6). See the
    reconstruction-floors scheme.
  - Any patch marks a redo (#226). A species-only repair that dt cannot cure loops to max_redo (#263, parked in #236).
- Discrepancies:
  - The struct defaults (`equation_of_state.hpp:49-50`: density_floor 1e-10, pressure_floor 1e-10) differ from the YAML
    defaults (`equation_of_state.cpp:65,71`: 1e-6, 1e-3). Report both. Programmatic options get 1e-10.


#### 8.6 Conserved/primitive limiter — floors (density, pressure, temperature) and limiter marks
<sub>inventory B: Scheme: Conserved/primitive limiter — floors (density, pressure, temperature) and limiter marks</sub>

- Summary: with `limiter: true`, NaNs are zeroed and marked, `cons[IDN]` (dry density) is clamped to `density_floor`,
  and `E` is clamped to `KE + UT->I(T_floor)`. Primitives: `rho >= density_floor`, `y >= 0`, `p >= pressure_floor`.
  Every interior repair sets a device bool mark (patched, NaN) that `check_redo` reads. Switch: YAML
  `equation-of-state/limiter` (default false); floors as above.
- Derivations:
  - The temperature floor as an energy floor through `UT->I`. Valid only if `UT->I(T(w)) = W->I(w)`; see the next scheme. re-derive from `src/eos/equation_of_state.cpp:225-234`.
- Figures:
  - Decision diagram of the limiter's repairs and which ones mark a redo (floor, NaN, species above round-off).
- Code:
  - `src/eos/equation_of_state.cpp:192` — `apply_conserved_limiter_`; KE uses the total density `:229`; temperature floor `:232`.
  - `src/eos/equation_of_state.cpp:325` — `apply_primitive_limiter_`.
  - `src/eos/equation_of_state.cpp:352` — `reset_limiter_marks`.
  - `src/mesh/meshblock.cpp:1190` — `floor_hit` (fresh cons→prim; 1.001 × floor).
  - `src/mesh/meshblock.cpp:1212` — `limiter_hits` (one device→host copy).
- Tests:
  - `tests/test_forcing.cpp:660` `limiter_patch_is_reported_below_the_temperature_floor`; `:737`, `:745`, `:753`, `:760` NaN/patch redo cases; `:767` clean step not redone; `:778` CUDA marks.
  - `tests/test_check_redo_floor.py` (`test_check_redo_floor_python`) — block, NaN and six-block mesh arms.
- Limits / known issues:
  - Only interior cells are marked (PR #226 Known limits). Scratch conversions through the limited EOS also mark the step (PR #226).
  - `isnan` does not catch ±inf (PR #226).
- Discrepancies: none.


#### 8.7 Primitive-variable EOS limiter (`apply_primitive_limiter_`)
<sub>inventory D: Scheme: Primitive-variable EOS limiter (`apply_primitive_limiter_`)</sub>

- Summary: NaN → 0 (marks a NaN if interior); ρ clamp_min(density_floor); species mass fractions clamp ≥ 0 (marks when
  below −roundoff); p clamp_min(pressure_floor). Switch: `equation-of-state/limiter`.
- Derivations: none (floors).
- Figures: none needed beyond the pipeline figure.
- Code: `src/eos/equation_of_state.cpp:325-350`. Called in each EOS's U→W, for example `src/eos/ideal_moist.cpp:134` and
  `src/eos/ideal_gas.cpp:68,108`.
- Tests: `tests/test_forcing.cpp` — `limiter_nan_in_a_primitive_redoes_the_step` (`:760`).
- Limits / known issues: floors on primitives do not mark a patch (the comment at `equation_of_state.cpp:328`).
  `floor_hit` judges them.
- Discrepancies: none.


#### 8.8 Reconstruction-stage floors
<sub>inventory D: Scheme: Reconstruction-stage floors</sub>

- Summary: in the non-shock path with `eos.limiter`, face densities are clamped ≥ density_floor (unless `floor=false`),
  face pressures ≥ pressure_floor, and species ≥ 0. The shock path returns with no clamp. The passive-scalar
  reconstruction (no hydro parent) always clamps ≥ 0. Switch: `dynamics/reconstruct/<vertical|horizontal>/shock` (YAML
  default false, `src/recon/reconstruct.cpp:33`; struct default true, `src/recon/reconstruct.hpp:51`) and the EOS
  limiter.
- Derivations: none (floors). Note the interaction with WB perturbation reconstruction (`floor=false`).
- Figures: a face-value overshoot below zero, clamped.
- Code:
  - `src/recon/reconstruct.cpp:79` — `ReconstructImpl::forward`: scalar clamp `:92-96`; shock early return `:98-101`;
    ρ floor `:135-137`; p floor `:143-145`; species `:153-155`.
  - `src/recon/reconstruct.hpp:96-99` — the `floor=false` contract.
  - `src/hydro/hydro_forward.cpp:357` — WB x1 reconstruction with `floor=false`.
- Tests: `tests/test_plm.cpp` (`test_plm.release`, the 0/0 guard, #212). Others are indirect.
- Limits / known issues: the production `shock: true` configuration with the limiter on has no face clamps
  (`sources/canoe__POSITIVITY_TECH_REPORT.md` §6, "a decision"). The excluded shock-path clamps (`1561bbf`) are not in
  the tree (tall-column report provenance table).
- Discrepancies: the struct and YAML defaults of `shock` differ (true versus false). Record it.


#### 8.9 Well-balanced face positivity floor (face-density/pressure fallback)
<sub>inventory D: Scheme: Well-balanced face positivity floor (face-density/pressure fallback)</sub>

- Summary: after reconstructing the perturbations and restoring the reference, a non-positive face pressure falls back
  to the face reference p_sf. A non-positive face density falls back to the adjacent cell's density: the cell below for
  the left state, using an edge-replicated shift rather than a circular roll; the cell itself for the right state. The
  floor does not change how often it fires, only what it substitutes. Switch: active whenever WB x1 is (gravity on,
  pressure row present, not shallow water; `hydro_forward.cpp:271-272`).
- Derivations: none (a fallback). Document why the fallback is the donor cell rather than the reference (tall-column
  report §4: a reference that is wrong aloft inflates the wall impedance).
- Figures: the top wall face, with the reconstructed perturbation overshooting below −ρ_ref and the fallback to the cell
  below (versus the old dsf fallback).
- Code: `src/hydro/hydro_forward.cpp:362-386` (pressure `:366-369`, density `:371-386`, `rho_below` at `:383`).
- Tests: `tests/test_face_floor.cpp` (`test_face_floor.release`, plus `_wb_ref4` and `_x1_centroid` env arms and CUDA
  twins). The dipped-face mass flux is |·| < 1e-9 with momentum > 0.03042. The red arm, with the old dsf fallback, gives
  −9.5e-8 (PR #221). The tolerances are pinned to measured values (`:79-107`).
- Limits / known issues: the edge replication itself is not covered (PR #221 Limits). Recommended monitoring: count
  substitutions per face and level (tall-column report §5).
- Discrepancies: the tall-column report says `3b7485a` "repairs a latent circular-shift wraparound". Its own review
  banner corrects this: the shipped commit introduced the edge-replicated shift. Code matches the banner.


#### 8.10 Dry channel positivity inside the VIC (pass-3a availability clamp, donor mark, species donor margin)
<sub>inventory D: Scheme: Dry channel positivity inside the VIC (pass-3a availability clamp, donor mark, species donor margin)</sub>

- Summary:
  - Pass 3a clamps each dry transfer to the donor's post-explicit dry content (floored at 0) and marks `MASS(IPR)=1` on
    a binding donor. That becomes `_dry_clamp_step` and redo cause 2.
  - Pass 3b clamps species transfers, keeping 4096 ulp of the donor's species (#260).
  - Everything is applied antisymmetrically, so mass is conserved exactly, clamped or not.
  - There is no flux limiter for dry density, and no ρ/p positivity guarantee anywhere.
  Switch: always on with the VIC. The redo is always on.
- Derivations: the antisymmetric clamp telescopes to zero for any q; a binding clamp means the requested density would
  go negative (exists as an argument in `sources/canoe__positivity_dry_channel_TECH_REPORT.md` §4, §5.3). The 4096-ulp
  donor keep (#260): re-derive from `src/implicit/vic_redistribute_impl.h:136-142`.
- Figures: a column with a dry transfer exceeding the donor's content (clamp, mark), with the momentum and energy rows
  not following (the inconsistent triple).
- Code:
  - `src/implicit/vic_redistribute_impl.h:104-132` (clamp marks at `:117-124`); `:140` (`keep`).
  - `src/implicit/implicit_hydro.cpp:379-380` (`_dry_clamp_step`); `src/mesh/meshblock.cpp:1206`
    (`vic_dry_clamp_hit`).
- Tests: `tests/test_backward_substitution.cpp` — `dry_only_transport_is_conservative_and_clamped` (`:159`; clamp to
  −0.25 and mark, at 1e-12) and the donor-fraction mark test (`:200`).
- Limits / known issues: the momentum and energy versus density inconsistency on a binding clamp is open (dry-channel
  report §4, §9). The top-face closure residual is open (§6). No in-kernel hit counter exists; the only meter is
  `clamp_residual` (vicclamp).
- Discrepancies: the dry-channel report (revision 2) claims "no loud failure downstream". At dae902b a binding clamp
  redoes the step (cause 2, #223). Code wins.


#### 8.11 Round-off thresholds for positivity events
<sub>inventory D: Scheme: Round-off thresholds for positivity events</sub>

- Summary: one dtype-scaled bound, `positivity_roundoff` = 4096·ε (float64) or 64·ε (float32), times the cell's total
  gas mass or density. It decides whether a withheld or repaired species amount counts as a positivity event (severe
  census, limiter mark). The θ margin itself stays at 4096 ulp in both precisions. Switch: none (constants).
- Derivations: none exists for 4096. For 64 in float32, PR #258 gives a measured rationale ("depletion rounds by at most
  0.99 ulp"), not a derivation. Re-derive from `src/hydro/flux_positivity.hpp:11-23`.
- Figures: a number line of round-off (ulp) versus real repairs.
- Code: `src/hydro/flux_positivity.hpp:18,23`; `src/hydro/flux_positivity.cpp:16`; uses at `hydro_forward.cpp:674-677`
  and `equation_of_state.cpp:316-321,342-345`.
- Tests: `tests/test_cycle_diagnostics.cpp` — `positivity_severe_needs_more_than_roundoff_withheld` (`:308`) and its
  float32 twin (`:338`). `tests/test_forcing.cpp:824,848`.
- Limits / known issues: these are magic constants (report §8).
- Discrepancies: none.


#### 8.12 Fresh-primitive floor detector (redo cause 1)
<sub>inventory D: Scheme: Fresh-primitive floor detector (redo cause 1)</sub>

- Summary: covered in Ch 7 (`floor_hit`). Here, document only that it is the only detector of density or pressure
  collapse when the limiter floors the state. Its 1.001 factor means "at or within 0.1% of the floor".
- Derivations: none needed (a threshold test); state the 1.001 band from `src/mesh/meshblock.cpp:1190-1204@e894700`.
- Figures: a density profile entering the band [floor, 1.001 floor] and the redo it triggers.
- Code: `src/mesh/meshblock.cpp:1190-1204@e894700`.
- Tests: `tests/test_check_redo_floor.py` (`test_check_redo_floor_python`).
- Limits / known issues: the floor can mask a defect if the floors exceed the physical regime. Above about 120 levels
  the floors must match the density regime (tall-column report §7).


#### 8.13 Dry-carry of passive tracers under dry-mass sources (0/0 guard)
<sub>inventory D: Scheme: Dry-carry of passive tracers under dry-mass sources (0/0 guard)</sub>

- Summary: when a native or user forcing changes dry density, tracers are carried. Additions carry the current r;
  removals carry the source-free stage ratio s_base/ρ_base, falling back to r where ρ_base = 0. Switch: present
  whenever a block has scalars plus forcings that write `du[IDN]`.
- Derivations: re-derive from `src/mesh/meshblock.cpp:631-646`. The PR text only gives the result.
- Figures: none needed.
- Code: `src/mesh/meshblock.cpp:634` (`carry_dry_source`), `:641` (ρ_base == 0 guard), `:678` (native),
  `:741` (user).
- Tests:
  - `tests/test_dry_carry_zero_base.py` (`test_dry_carry_zero_base_python`). Finite result at a zero base; bottom
    `scalar_s` equals −5e-4 at atol 1e-12. This is not a positivity property: the test accepts a negative tracer.
  - `tests/test_stage_forcing_dry_tracer.py` (`test_stage_forcing_dry_tracer_python`).
- Limits / known issues: no positivity guarantee for scalars under dry sinks.
- Discrepancies: none.


---

<a id="ch9"></a>
## Chapter 9. Diffusion, viscosity and forcing

The forcing framework and every forcing module: user stage forcings, Coriolis, isotropic viscosity and conduction with the face coefficient (walls, $x_1$ profiles, mean of products), heating and cooling, bottom relaxation, sponges. Sedimentation moves to chapter 10 (it is moist physics). The constant-gravity forcing is chapter 6.1. Two entries record dead code (plume forcing, the unbuilt turbulence directory) and get one paragraph each.

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: every module registered by `HydroImpl::_register_forcings_module` (const-gravity, coriolis, diffusion,
body-heat, top-cool, bot-heat, relax-bot-comp, relax-bot-temp, relax-bot-velo, top/bottom sponge, plume-forcing), the
diffusion operator in detail (stress tensor, Fourier flux, face coefficient, wall extrapolation, x1 profiles, dynamic
mode, time step), sedimentation (Stokes/Cunningham velocity, donor-cell settling flux, wall sealing, fused kernels),
and user stage forcings.

Merge/split recommendation:
- **Move sedimentation to Ch. 10.** It is the precipitation flux of condensates and shares the positivity carry
  (`fsed1`), the gravity-work booking and the cloud species tables with the moist chapter.
- **const-gravity**: keep a short forcing section here. The gravity-work forms, the fixer and the VIC work belong to
  the gravity-work chapter (cross-reference only).
- **src/turbulence**: legacy Athena++ code (`#include <athena/...>`, `src/turbulence/turbulence_model.hpp:8-10`) that
  is **not compiled**: the `src/CMakeLists.txt:35-52` glob has no `turbulence/` (nor `diagnostics/`). Drop it, or
  give it one sentence stating there is no turbulence closure.
- **plume-forcing**: unreachable (see below); one sentence.

</details>


#### 9.1 Forcing framework and registration
<sub>inventory B: Scheme: Forcing framework and registration</sub>

- Summary: forcing options are parsed from YAML `forcing:` (unknown keys refused; `fric-heat` refused with a removal
  message). Each module is an `AnyModule` whose `forward(du, w, temp, dt)` adds `dt * S` into `du` after the flux
  divergence, using cell-centred primitives and `temp = W->T`. The forcings' dry-density increment is recorded for
  tracers. Switch: presence of each YAML key.
- Derivations: none.
- Figures:
  - Registration order (const-gravity, coriolis, diffusion, body-heat, top-cool, bot-heat, relax-bot-comp, relax-bot-temp, relax-bot-velo, top-sponge, bot-sponge, plume) and where `du` is accumulated in the stage.
- Code:
  - `src/hydro/register_forcing_modules.cpp:6` — `HydroImpl::_register_forcings_module`.
  - `src/hydro/hydro_options.cpp:68` — `fric-heat` refused; `:73-76` `check_keys(forcing, ...)`; `:78-117` per-module `from_yaml`.
  - `src/hydro/hydro.cpp:135` — registration; `src/hydro/hydro_forward.cpp:773` — forcing loop; `:774` `_forcing_dry`.
  - `src/mesh/meshblock.cpp:678` — `carry_dry_source(phydro->forcing_dry_increment(), ...)` (tracer carry; Ch. 10).
- Tests:
  - `tests/test_hydro_options.cpp` (`test_hydro_options.release`) — `reject_removed_and_unknown_forcing_keys`.
  - `tests/test_forcing.cpp:220` `meshblock_registers_parent_dependent_modules`.
  - `tests/test_forcing.cpp:1269` `boundary_fluxes_scale_with_timestep` — `du(2dt) = 2 du(dt)`.
- Limits / known issues: forcings act on the whole array (ghosts included) for modules that do not index the interior. Ghost tendencies are overwritten by the boundary fill.
- Discrepancies: PR #217 lists "twelve" forcing keys including `plume-forcing`. Plume EOS was removed (#282), yet the key is still accepted (`src/hydro/hydro_options.cpp:76`).


#### 9.2 User stage forcings
<sub>inventory B: Scheme: User stage forcings</sub>

- Summary: TorchScript/Python modules registered on the MeshBlock receive the stage variables and return
  `hydro_du`/`scalar_ds`, added after the native tendencies. A user dry-density change carries tracers. Switch:
  `MeshBlockImpl::set_user_stage_forcings` (API, no YAML).
- Derivations: none (tracer carry: Ch. 10).
- Figures: interface diagram (inputs dict → module → `{hydro_du, scalar_ds}`).
- Code: `src/mesh/meshblock.cpp:96` — `set_user_stage_forcings`; `:38` `stage_forcing_variables`; `:50` `stage_forcing_result`; `:725-751` application and dry carry.
- Tests: `tests/test_jit_user_forcing.py` (`test_jit_user_forcing_python`); `tests/test_stage_forcing_dry_tracer.py` (`test_stage_forcing_dry_tracer_python`) — tracer ratio deviation ≤ 1e-12, bounds [−1e-12, 1+1e-12].
- Limits / known issues: a user forcing that converts through the limited EOS can mark a redo (PR #226).
- Discrepancies: none.


#### 9.3 Coriolis (123 and xyz forms, cubed-sphere covariant)
<sub>inventory B: Scheme: Coriolis (123 and xyz forms, cubed-sphere covariant)</sub>

- Summary: `du[m] += -2 dt Omega × (rho v)`. `type: 123` takes Omega directly in the coordinate frame (the third
  component only in 3-D). `type: xyz` projects a Cartesian rotation vector onto cartesian, cylindrical,
  spherical-polar or gnomonic-equiangle cells. On the cubed sphere it maps contravariant → local spherical, crosses,
  and maps back to covariant. `traditional` keeps only the radial Omega (forced for shallow water). Switch:
  `forcing/coriolis/{type (xyz|123), omega1, omega2, omega3, traditional}`, defaults xyz, 0, 0, 0, false.
- Derivations:
  - Projections of Omega for each geometry and the cubed-sphere velocity transforms. re-derive from `src/forcing/coriolis.cpp:75-150`, `:152-192`.
- Figures:
  - Cubed-sphere panel with local (contravariant) and spherical bases; Omega projected; covariant force.
- Code: `src/forcing/coriolis.cpp:19` `from_yaml`; `:50` `Coriolis123Impl::forward`; `:75` `CoriolisXYZImpl::reset`; `:152` `forward`.
- Tests: `tests/test_forcing.cpp:210` `parse_coriolis_traditional`; `:234` `cubed_sphere_coriolis_uses_cartesian_rotation_vector`; `:238` `..._supports_traditional_approximation`; `:242` `cubed_sphere_shallow_water_uses_traditional_coriolis`.
- Limits / known issues: in `xyz` mode `omega1` is the **z** component, `omega2` x and `omega3` y (`src/forcing/coriolis.cpp:86-88`); document this mapping.
- Discrepancies: none.


#### 9.4 Isotropic viscosity and heat conduction (forcing/diffusion)
<sub>inventory B: Scheme: Isotropic viscosity and heat conduction (forcing/diffusion)</sub>

- Summary: Newtonian viscous flux `-nu rho_f [2 S - (2/3)(div v) I]` (two-cell face normal derivatives, cross terms
  averaged from centred derivatives), viscous work `v_f · F_m` in the energy flux, and Fourier flux
  `-kappa (rho cv)_f dT/dn`. With `dynamic: true`: `-mu S`, `-k dT/dn`, no density. The tendency is
  `-dt div F`. Cartesian only. Switch: `forcing/diffusion/{nu_iso (0), kappa_iso (0), dynamic (false), nu_scale_x1, kappa_scale_x1}`.
  Legacy `K`/`type` refused; values must be finite and ≥ 0 (`src/forcing/diffusion.cpp:250-288`).
- Derivations:
  - Discrete stress tensor, viscous work and conservation of total energy. re-derive from `src/forcing/diffusion.cpp:516-542`.
  - Fourier flux with the volumetric mixture heat capacity. re-derive from `src/forcing/diffusion.cpp:544-562`.
  - Parabolic time-step bound `dt = dx_min^2/(2 ndim coeff)` (dynamic: `nu/rho_min`, `kappa/(rho cv)_min`). re-derive from `src/forcing/diffusion.cpp:572-619`.
  - Semantics of `kappa_iso`: with `rho cv` it diffuses T at `kappa/gamma` when p is uniform and at `kappa` at fixed rho. The algebra is in issue #261 (`sources/gh__ISSUE_THREADS_251-294.md` §#261), stated, not derived; re-derive from `src/forcing/diffusion.cpp:477-481`.
- Figures:
  - Staggered stencil: cell centres, x1 face, face-normal derivative, the four centred derivatives averaged for a shear term.
  - Energy flux composition at a face: conduction + viscous work.
- Code:
  - `src/forcing/diffusion.cpp:246` — `DiffusionOptionsImpl::from_yaml`.
  - `src/forcing/diffusion.cpp:334` — `DiffusionImpl::reset` (cartesian-only `:339`, nghost ≥ 2 for viscosity `:341`, conduction needs `species_cv_ref > 0` `:343`).
  - `src/forcing/diffusion.cpp:436` — `DiffusionImpl::forward`.
  - `src/forcing/diffusion.cpp:70` `centered_derivative`, `:86` `face_normal_derivative`, `:99` `face_average`.
  - `src/forcing/diffusion.cpp:572` — `max_time_step`; consumed at `src/hydro/hydro.cpp:378`.
- Tests (`tests/test_diffusion.cpp`, `test_diffusion.release`):
  - `:178` `uniform_state_has_zero_tendency` (1e-6); `:192` `transverse_velocity_uses_viscous_laplacian` (1e-5); `:208` `temperature_uses_conductive_laplacian` (1e-3 abs); `:226` `viscous_sine_mode_matches_analytic_decay`.
  - `:438` `timestep_uses_largest_diffusivity` (1e-12); `:448`, `:457`, `:467` non-finite/non-positive bounds throw; `:492` `dynamic_coefficients_carry_no_density` (1e-12).
  - `:103`, `:116`, `:134`, `:161`, `:171` option validation.
  - `tests/test_diffusion_moist.cpp:44` `moist_conduction_uses_local_mixture_specific_heat` (1e-5); `:66` `dynamic_conduction_timestep_uses_local_volumetric_heat_capacity` (rel. 1e-12) (`test_diffusion_moist.release`).
- Limits / known issues:
  - Cartesian only; no species/tracer diffusion.
  - Conduction acts on T, so a resting adiabatic column drifts (issue #252: walls ~0.9 K in 259 s at K = 75). The `on_theta` remedy (#253/#259) was **removed** in #268 (closes #261), and the drift is unaddressed at the pin.
  - Immersed solids: diffusion reads the solid placeholder state (rho = 1e3, p = 1e9), so the face heat capacity is ~500× too large. Measured and deliberately left unfixed (`sources/canoe__diffusion_ghost_TECH_REPORT.md` §3/§3a). Note ISSUES.md item 6 on its "500.5× vs 50,050 %" wording.
  - The wall normal stress keeps a first-order kernel error from `face_average(div_vel)` at the wall (ghost report §5 "does not touch").
  - Viscosity created u2 beside x2 block edges at an x1 wall row (issue #264), fixed by #265 (x1 walls re-applied inside tangential ghost slabs). Cross-ref the boundary chapter.
  - Python setters bypass the YAML validation (PR #216 Limits).
- Discrepancies:
  - PR #253/#259 bodies describe `on_theta`; it no longer exists (`check_keys` at `src/forcing/diffusion.cpp:253-255` lists no `on_theta`). Code wins.


#### 9.5 Diffusion face coefficient at walls and ghosts (one-sided wall extrapolation)
<sub>inventory B: Scheme: Diffusion face coefficient at walls and ghosts (one-sided wall extrapolation)</sub>

- Summary: interior faces average the two cells. On an x1 face whose boundary is a whitelisted wall (`reflecting_*`,
  `fixed_temperature_*`), the coefficient (`rho`, or `rho cv`, or the product with an x1 profile) is extrapolated
  linearly from the two nearest active cells, `q_f = (1+t) q_a - t q_b` with `t = w_a/(w_a+w_b)`. It falls back to
  `q_a` if non-positive. x2/x3 walls, periodic, outflow, custom and solid faces keep the average. Switch: automatic
  from the boundary names.
- Derivations:
  - Wall extrapolation weight and its order. exists: `sources/canoe__diffusion_ghost_TECH_REPORT.md` §5b (derivation of `t`), §4 (mirror truncation `e^{∓dz/2H}`).
  - Why x1 only, and the whitelist: argued in the same report §5b–§5c (argument, not derivation).
- Figures:
  - Wall face: mirror ghost vs linear continuation; the two-cell average lands half a cell inside, the extrapolation lands on the wall.
  - Whitelist table: reflecting / fixed_temperature → one-sided; periodic / outflow / custom / solid → average.
- Code:
  - `src/forcing/diffusion.cpp:114` — `extrapolate_to_wall`; `:142` `face_coefficient` (fewer than 3 faces → average, `:148`).
  - `src/forcing/diffusion.cpp:501-502` — x1-only wall flags.
  - `src/mesh/meshblock_options.cpp:243` — `MeshBlockOptionsImpl::is_wall_boundary` (whitelist `:270-271`; unnamed bfunc warns and returns false `:250-258`).
  - `src/mesh/meshblock_options.cpp:229` — `is_physical_boundary`.
- Tests (`tests/test_diffusion.cpp`):
  - `:260` `wall_face_coefficient_reads_no_ghost` (1e-5); `:389` `wall_flux_does_not_depend_on_the_ghost_density` (1e-10).
  - `:283` `x2_wall_is_not_one_sided` and `:318` `periodic_x1_face_is_not_extrapolated` (half-slope, 1e-4 rel.) — scope guards.
  - `:341` `wall_names_are_an_exact_whitelist`.
- Limits / known issues:
  - Without a `boundary-condition.external` block no bfuncs exist and the fix is dormant (ghost report banner).
  - No `fixed_temperature_*` bfunc is registered in the tree, so that whitelist entry changes nothing today (PR #216 Limits).
- Discrepancies: the ghost report says `solid` was in the whitelist for one revision. Code: it is excluded (`src/mesh/meshblock_options.cpp:260-271`). Consistent with the report's final state.


#### 9.6 x1 profiles of the kinematic coefficients (nu_scale_x1, kappa_scale_x1) and the product face coefficient
<sub>inventory B: Scheme: x1 profiles of the kinematic coefficients (nu_scale_x1, kappa_scale_x1) and the product face coefficient</sub>

- Summary: a positive x1 profile `s(x1)` multiplies `nu_iso`/`kappa_iso`, given as a YAML/Python table (linear between
  knots, held beyond them, interpolated onto cell centres incl. ghosts) or as a per-cell Python tensor (only when x1 is
  one block). On x1 faces the coefficient is the mean of the products `(s_a q_a + s_b q_b)/2`; x2/x3 faces keep
  `mean(q) * s` bit for bit. Profiles are frozen at construction (identity, version and value checks). Switch: YAML
  `nu_scale_x1: {x1: [...], scale: [...]}`, `kappa_scale_x1`; Python `nu_scale_x1[_table]`, `kappa_scale_x1[_table]`;
  refused with `dynamic: true`.
- Derivations:
  - Product of means vs mean of products; second-order spurious tendency of the former on a constant dynamic coefficient. exists: `docs/derivations/diffusion-face-coefficient.md@e894700` (with `docs/derivations/diffusion_face_coefficient.py`). The copy `sources/deriv__diffusion-face-coefficient.md` is the older `4d3b4d7` version, which lacks the x2/x3 bitwise clause.
- Figures:
  - Covariance term `-(1/4) Δs Δq` on a stratified column; tendency profile with PM vs MP.
  - Table → cell-centre interpolation with ghosts, for two different x1 splits.
- Code:
  - `src/forcing/diffusion.cpp:168` — `face_scaled_coefficient` (x1 branch `:172-175`, x2/x3 `:178-193`).
  - `src/forcing/diffusion.cpp:198` `checked_table`; `:216` `profile_from_table`.
  - `src/forcing/diffusion.cpp:363-402` — profile build in `reset`; `:415` `check_profiles`.
- Tests (`tests/test_diffusion_x1_scale.cpp`, `test_diffusion_x1_scale.release`):
  - `:227` `unity_profile_is_bitwise_no_profile`; `:255`, `:295` scaled sine-mode decay; `:341` `linear_profile_gives_the_analytic_tendency` (1e-12); `:403`/`:407` `constant_dynamic_coefficient_column_has_no_tendency` (< 1e-12 × scale); `:457`/`:461` second-order convergence (CPU/CUDA); `:559` `table_profile_is_independent_of_the_x1_split`; `:588`, `:613`, `:659`, `:692`, `:738` refusals.
  - `tests/test_diffusion_x1_scale.py` (`test_diffusion_x1_scale_python`) — ones profile bitwise, YAML = Python bitwise, non-uniform profile changes the step.
- Limits / known issues: a per-cell tensor is refused when nb1 > 1 (`src/forcing/diffusion.cpp:377-383`).
- Discrepancies: the source derivation file predates `e659b69` (x2/x3 bitwise); cite the docs version.


#### 9.7 Body heating, top cooling, bottom heating
<sub>inventory B: Scheme: Body heating, top cooling, bottom heating</sub>

- Summary: `body-heat`: `du[E] += dt * dTdt * rho cv` where `pmin <= p <= pmax`. `top-cool`/`bot-heat`: a flux
  `F/(dz*depth)` spread over `depth` cells at the physical upper/lower x1 boundary only. Switch:
  `forcing/body-heat/{dTdt 0, pmin 0, pmax 1}`; `top-cool/{flux ≤ 0, depth 1}`; `bot-heat/{flux ≥ 0, depth 1}`.
- Derivations: trivial; re-derive from `src/forcing/body_heat.cpp:43-55`, `src/forcing/top_cool.cpp:42-55`, `src/forcing/bot_heat.cpp:42-55`.
- Figures: column cartoon with heated/cooled boundary slabs.
- Code: `src/forcing/body_heat.cpp:15`, `:43`; `src/forcing/top_cool.cpp:16`, `:42`; `src/forcing/bot_heat.cpp:16`, `:42`.
- Tests: `tests/test_forcing.cpp:1246` `body_heat_uses_pressure_mask_and_mixture_cv`; `:1269` `boundary_fluxes_scale_with_timestep`.
- Limits / known issues: top-cool/bot-heat use `dx1f` of the boundary cell for all `depth` cells (exact only on a uniform grid near the boundary).
- Discrepancies: none.


#### 9.8 Bottom relaxation (temperature, velocity, composition)
<sub>inventory B: Scheme: Bottom relaxation (temperature, velocity, composition)</sub>

- Summary: `relax-bot-temp`: `du[E] += dt/tau rho cv (T_b - T_target)` in the first interior cell. `T_target` is the
  cell value, or with `at-face: true` the face extrapolation `(1+a) T0 - a T1`, `a = (x1v_il - x1f_il)/(x1v_il+1 - x1v_il)`,
  gain `1/(1+a)`. `relax-bot-velo`: momentum relaxed toward `(bvx, bvy, bvz)`, force lowered to covariant.
  `relax-bot-comp`: mole fractions of named species relaxed toward `xfrac` at fixed rho and T (dry fills the rest),
  with the energy change from kintera `VT->U`. All act only at the physical lower boundary. Switch:
  `relax-bot-temp/{tau>0, btemp (required), at-face false}`; `relax-bot-velo/{tau>0, bvx, bvy, bvz}`;
  `relax-bot-comp/{tau>0, species, xfrac (sum ≤ 1)}`.
- Derivations:
  - Face extrapolation weight and gain. PR #219 states 1.5/−0.5 and gain/1.5; re-derive from `src/forcing/relax_bot_temp.cpp:82-103`.
  - Isothermal composition swap conserving total mass. re-derive from `src/forcing/relax_bot_comp.cpp:82-119`.
- Figures:
  - Bottom two cells and the lower face: extrapolated face temperature vs cell centre.
  - relax-bot-comp: dry ↔ vapour exchange at fixed rho, with the energy offset change.
- Code: `src/forcing/relax_bot_temp.cpp:15`, `:58`; `src/forcing/relax_bot_velo.cpp:17`, `:47`; `src/forcing/relax_bot_comp.cpp:20`, `:61` (own `ThermoY`/`ThermoX`), `:82`.
- Tests (`tests/test_forcing.cpp`):
  - `:246` `relax_bottom_temperature`; `:264` `..._at_face_rejects_non_bool`; `:287` `..._under_an_inversion` (1e-13); `:316` `..._uses_coordinate_spacing`; `:342` `..._at_face` (default `torch::equal`, on 1e-13).
  - `:491` `relax_bottom_velocity`; `:509` `relax_bottom_composition_preserves_state`; `:1233` `..._handles_multidimensional_ghost_zones`; `:203` unknown species.
  - `tests/test_tracer_dry_convention.py` (relax arm), `tests/test_dry_carry_zero_base.py`.
- Limits / known issues:
  - `at-face` is off by default; on the one IC tried it cost stability (PR #219 Limits).
  - `relax-bot-comp` uses kintera `VT->U` even with ideal-moist, whose internal energy is snapy's own formula. They agree only while kintera adds no NASA-9/H2/extra terms. Not tested (re-derive).
  - `nghost >= 2` is needed for at-face (`src/forcing/relax_bot_temp.cpp:89-92`).
- Discrepancies:
  - PR #219 describes the at-face target as `1.5 T0 - 0.5 T1` with the gain divided by 1.5. The code uses the coordinate-spacing weight `a` (generalised in #279), which equals 0.5 only on a uniform grid.
  - The options struct default `btemp = 300` (`src/forcing/forcing.hpp:451`), but YAML requires `btemp` (`src/forcing/relax_bot_temp.cpp:25-27`).


#### 9.9 Sponge layers (top and bottom)
<sub>inventory B: Scheme: Sponge layers (top and bottom)</sub>

- Summary: Rayleigh drag `-dt rho v/tau sin^2(pi eta/2)`, `eta = (width - distance)/width` clamped to [0,1], with the
  distance measured from the lower face `x1f[i]` of each cell. The force is lowered to covariant. Energy is not touched,
  so the removed KE becomes internal energy. Physical boundaries only. Switch: `top-sponge-lyr/{tau>0, width>0}`,
  `bot-sponge-lyr/{tau>0, width>0}`.
- Derivations:
  - Drag profile; the implicit frictional heating from conserving E. re-derive from `src/forcing/top_sponge_lyr.cpp:47-76`.
  - Covariant lowering of a force ∝ v^i. Argument in `sources/canoe__forcing_io_TECH_REPORT.md` Defect 1 (argument, no derivation); re-derive from `src/forcing/top_sponge_lyr.cpp:64-73`.
- Figures:
  - sin² profile over the top `width`; cubed-sphere corner showing a contravariant drag rotating the wind vs a covariant drag braking it.
- Code: `src/forcing/top_sponge_lyr.cpp:17`, `:47`; `src/forcing/bot_sponge_lyr.cpp:17`, `:47`.
- Tests: `tests/test_forcing.cpp:442` `cubed_sphere_sponge_drag_is_covariant` (cross product ≤ 1e-12 × scale; checks direction only, PR #219 Limits); option rejections `:175`.
- Limits / known issues:
  - Under x1 decomposition only the block owning the physical boundary applies the sponge (`src/forcing/top_sponge_lyr.cpp:52`). A `width` taller than that block is truncated in the blocks below.
  - `eta` uses the cell's lower face, not its centre (`:59`).
  - Not run at scale on the cubed sphere (PR #219 Limits).
- Discrepancies: `src/forcing/sponge_lyr.cpp_` is an Athena++ leftover, not compiled (wrong extension).


#### 9.10 Plume forcing (unreachable)
<sub>inventory B: Scheme: Plume forcing (unreachable)</sub>

- Summary: entrainment/buoyancy sources for a plume EOS. Installed only if `eos/type == plume-eos`, a type that
  `EquationOfStateImpl::create` rejects (removed in #282). Switch: `forcing/plume-forcing` (still accepted).
- Derivations: none.
- Figures: none.
- Code: `src/forcing/plume_forcing.cpp:29`; `src/hydro/register_forcing_modules.cpp:77`; `src/hydro/hydro_options.cpp:116`.
- Tests: none.
- Limits / known issues: dead code.
- Discrepancies: PR #217 lists `plume-forcing` as a valid key. It is accepted but cannot be installed at the pin.


#### 9.11 Turbulence (not built)
<sub>inventory B: Scheme: Turbulence (not built)</sub>

- Summary: k–epsilon model files from Athena++; not compiled, no YAML key. Switch: none.
- Derivations: none (not built; described in one paragraph only).
- Figures: none (dead code).
- Code: `src/turbulence/k_epsilon_turbulence.cpp:16`, `src/turbulence/turbulence_model.hpp:19`; build glob `src/CMakeLists.txt:35-52` (no `turbulence/`).
- Tests: none.
- Limits / known issues: dead code; snapy has no turbulence closure beyond constant `nu_iso`/`kappa_iso` (with an x1 profile).
- Discrepancies: none.


---

<a id="ch10"></a>
## Chapter 10. Moist physics coupling

Saturation adjustment in the step, the redo causes that moist physics raises, the condensate and vapour repairs (two inventories describe `fix_vapor`; the author merges them), the precipitation and evaporation kinetics (a driver-level coupling: it lives in the example driver, which the chapter says plainly), tracer transport per dry air, and the sedimentation of condensates (moved here from chapter 9).

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: how phase change and condensates enter the step: the saturation adjustment's place in the step and its failure
→ redo path; the conserved limiter's species repairs (parent-vapour borrow by stoichiometry, column `fix_vapor`
weighted by cell volume, parentless clouds, whole-column gathers across x1 blocks); condensate conservation; the
positivity-limited species fluxes carrying their energy and momentum (`species_enthalpy`, `fsed1`); `check_redo` causes;
precipitation (sedimentation, from Ch. 9; kinetics/evaporation in the drivers); passive tracers (`src/scalar`) per dry
air, with an upper bound.

Merge/split recommendation: **merge** sedimentation in from Ch. 9 and the species-repair half of the limiter from
Ch. 2. Keep the positivity limiter's general theory in its own chapter (cross-reference) and here only the moist
energy/momentum carry. Kinetics (evaporation/precipitation rates) runs **outside the snapy library**, in the example
drivers (`examples/run_hydro.cpp`, `examples/jupiter_evap_precip_1d.cpp`) and kintera. Present it as "driver-level
coupling" with a kintera subsection. Radiative timestep limiter (`canoe__RT_TIMESTEP_LIMITER_TECH_REPORT.md`) and the
GPU chemistry kernel (`canoe__PYMINICHEM_GPU_TECH_REPORT.md`) live in external runners, not in the snapy tree at the
pin. Out of scope; mention at most as external users of `max_time_step`/stage forcings.

</details>


#### 10.1 Saturation adjustment in the step
<sub>inventory B: Scheme: Saturation adjustment in the step</sub>

- Summary: on the last RK stage, if the thermo has reactions: run the conserved limiter (whole column), form
  `rho = rho_d + sum rho_i`, `ie = E - KE`, `y = rho_i/rho`, call kintera `ThermoY::forward(rho, ie, y, warm_start=true)`
  on the interior, write back `rho_i = y rho`, then fill boundaries. Dry density, momentum and E are unchanged (UV
  equilibrium; latent heat through the reference energies). Switch: implicit (reactions present in the thermo block);
  kintera `max-iter`, `ftol`, `uv-solver`.
- Derivations:
  - Energy and water conservation of the UV adjustment with reference energies. re-derive from `src/mesh/meshblock.cpp:795-816` and `kintera src/thermo/thermo_y.cpp:259-367@4dc613d`.
- Figures:
  - Timeline of an RK3 step marking where the adjustment, the limiter calls and the boundary fill happen.
  - Before/after column of q_v, q_c, T for one adjustment.
- Code:
  - `src/mesh/meshblock.cpp:795` — step (6); limiter `:798`; kintera call `:813`; write-back `:816`; boundaries `:841`.
  - `kintera src/thermo/thermo_y.cpp:259@4dc613d` — `ThermoYImpl::forward`.
- Tests:
  - `tests/test_wall_saturation.cpp:15` `phase_change_preserves_energy_and_water` — 1e-12 (energy, water); cloud evaporates to < 1e-6 of initial.
  - `tests/test_vic_moist_device.py` (`test_vic_moist_device_python`, CUDA only) — CPU vs CUDA one moist step, 1e-9 (measured 5.8e-11, `:18-20`).
- Limits / known issues:
  - Only the interior is adjusted. Ghosts come from the boundary fill/exchange afterwards (the #206 ordering). Issue #208: no decomposed moist reflecting-wall test (`sources/gh__ISSUE_THREADS_138-250.md`).
  - Warm start reuses the active set only for the same shape/device (kintera #132, `kintera src/thermo/thermo_y.cpp:276-294@4dc613d`).
- Discrepancies: none.


#### 10.2 check_redo — causes, reduction, restore (saturation and limiter)
<sub>inventory B: Scheme: check_redo — causes, reduction, restore (saturation and limiter)</sub>

- Summary: after a step, six causes are evaluated (floor; VIC dry clamp; limiter patch; NaN; saturation failure =
  kintera's drained count > 0; VIC solve failure). They are MAX-allreduced over ranks, then the step is accepted, or
  restored (`hydro_u`, `hydro_w`, scalars, gravity fix dropped, cycle decremented) and redone at smaller dt, up to
  `max_redo`. Switch: integrator `max_redo`, default 5 (`pyharp src/integrator/integrator.hpp:58@4721715`); the
  saturation cause is always on when a ThermoY exists.
- Derivations: none (logic). Bit values: floor 1, clamp 2, limiter 4, nan 8, saturation 16, vic-solve 32 (`src/mesh/meshblock.cpp:1237-1240`).
- Figures:
  - Flow chart: local flags → allreduce MAX → apply_redo (restore / accept / terminate).
- Code:
  - `src/mesh/meshblock.cpp:1302` `check_redo`; `:1278` `local_redo_flags`; `:1288` `reduce_redo_flags`; `:1229` `apply_redo`; `:1220` `saturation_failures` (drains `take_saturation_adjustment_failures`); `:621` drain at stage 0.
  - `src/mesh/mesh.cpp:422` — `MeshImpl::check_redo` (multi-block).
  - `kintera src/thermo/thermo_y.cpp:369@4dc613d` — `take_saturation_adjustment_failures`.
- Tests:
  - `tests/test_check_redo_saturation.py` (`test_check_redo_saturation_python`, `_cuda_python`) — five arms: default max-iter accepted; max-iter 1 leaves ≥1 unadjusted cell; redo with cause `saturation` alone and restore; a failure between steps is not charged; two-block Mesh with the cell in block 1.
  - `tests/test_check_redo_parallel.cpp:16` (`test_check_redo_parallel.release`, 2 ranks) — one decision across ranks.
  - `tests/test_check_redo_floor.py`; `tests/test_forcing.cpp:805` `limiter_species_repair_redoes_the_step`, `:824` `limiter_roundoff_species_repair_is_not_redone`, `:848` Float32 ulp.
  - `tests/test_uranus_cycle1_abort.cpp:85`, `:97`, `:115` (`test_uranus_cycle1_abort.release`) — Uranus column survives cycle 1/40; abnormal termination exits nonzero.
- Limits / known issues:
  - A failure that a smaller dt cannot cure exhausts `max_redo` and ends the run (PR #248 Limits).
  - Species repairs above round-off request a redo; a stale driver state can make every attempt fail (issue #263, closed as a driver defect; `sources/gh__ISSUE_THREADS_251-294.md` §#263).
  - `examples/uranus.yaml` aborted at cycle 342 on an H2S repair (issue #260; #259 changed the VIC donor margin). Re-measure at the pin before quoting.
- Discrepancies: none.


#### 10.3 Condensate repair by parent-vapour borrow (stoichiometric split)
<sub>inventory B: Scheme: Condensate repair by parent-vapour borrow (stoichiometric split)</sub>

- Summary: a negative condensate with a nucleation parent borrows its deficit from its parent vapours in the same cell
  (including ghosts), split by the normalised stoichiometric mass fractions `nu_k mu_k / sum nu mu`, then is clamped to
  exactly zero. Conservative in mass and elements. Parents are cached at construction from the thermo's own species
  table. Switch: `limiter: true`.
- Derivations:
  - Mass-fraction split from the reaction stoichiometry, and its element conservation. re-derive from `src/eos/equation_of_state.cpp:110-163`, `:253-269`.
- Figures:
  - NH4SH deficit split into NH3 and H2S in one cell (mass bars before/after).
- Code:
  - `src/eos/equation_of_state.cpp:110` — `cache_cloud_parents_` (dry slot never a parent `:142-145`; first producing reaction only `:152`).
  - `src/eos/equation_of_state.cpp:266` — borrow; `:268` clamp.
- Tests:
  - `tests/test_condensate_conservation.cpp:17` (`test_condensate_conservation.release`) — total mass 1e-12; NH3/H2S debited by molar-mass share (1e-6); reactions cleared after construction to prove the cache is used.
  - `tests/test_cloud_parent_slots.cpp:22` (`test_cloud_parent_slots.release`) — card with unused species, 1e-12.
  - `tests/test_diffusion_moist.cpp:98` `conserved_limiter_uses_nucleation_parent_metadata` (1e-12).
  - `tests/test_two_cards_species.cpp:139-159` — split correct after a second card.
- Limits / known issues:
  - Uses only the first nucleation reaction producing a cloud.
  - The phase shift (~1 % of the local value) is undone by the next saturation adjustment (comment `src/eos/equation_of_state.cpp:242-250`).
  - An energy correction for the shifted latent heat is **not** applied: E is unchanged, so T shifts through the offsets.
- Discrepancies: PR #223 says the cache "uses the global registry throughout". #235 replaced that with the thermo's own `names()/mu()` (`src/eos/equation_of_state.cpp:128-130`). Code wins.


#### 10.4 Column vapour repair fix_vapor (volume-weighted, upward fallback) and parentless clouds
<sub>inventory B: Scheme: Column vapour repair fix_vapor (volume-weighted, upward fallback) and parentless clouds</sub>

- Summary: per x1 column, scanning top→bottom, a negative vapour cell merges with the cells below until the
  volume-weighted sum is ≥ 0, then sets `q = sum(vapour w)/sum(major w)` times the dry density over the merged range.
  If the bottom is exhausted, it takes the shortfall from above (capped); otherwise it fails. Vapour failure throws.
  Parentless clouds (no nucleation parent, e.g. rain) use the same kernel without requiring success, then clamp, which
  creates mass only if the whole column is short. With `whole_column` and x1 split over blocks (`pz>1`), each block
  gathers the full column (`gather_x1`), repairs it and keeps its slice. Failure counting: `std::atomic` on CPU,
  `atomicAdd` on CUDA. Switch: `limiter: true`; `whole_column` is passed only by `advance_local`.
- Derivations:
  - Mass conservation `sum(q rho_d V)` with weights `V/V_0`, and termination of the scan. re-derive from `src/eos/fix_vapor_impl.h:9-79` (PR #241/#243 state the result only).
- Figures:
  - Column cartoon: negative cell, merged segment, uniform-ratio redistribution; the upward-fallback case.
  - Two x1 blocks: gather → repair → copy-back slices.
- Code:
  - `src/eos/fix_vapor_impl.h:9` — `fix_vapor_impl` (accumulators from zero `:32`; upward fallback `:41`; redistribution `:67`).
  - `src/eos/eos_dispatch.cpp:79` — `call_fix_vapor_cpu` (`std::atomic` `:82`); `src/eos/eos_dispatch.cu:52` CUDA (`atomicAdd` `:68`).
  - `src/eos/equation_of_state.cpp:276` — `repair_column` (gather `:282`; parentless `:307`; vapour `:312`; round-off-bounded marking `:318`; copy-back `:303`).
- Tests:
  - `tests/test_eos.cpp:40`, `:68`, `:90`, `:101`, `:109` (`eos_limiter.*`) — zero column accepted; bottom cell repaired from above (column sum 1e-14 rel.); net deficit rejected without writing; single cell rejected; downward branch unchanged.
  - `tests/test_fix_vapor_volume.cpp:42` (`test_fix_vapor_volume.release`) — spherical-polar column, mass to 1e-12 (f64) / 1e-6 (f32); Cartesian control bitwise.
  - `tests/test_parentless_cloud.cpp:21`, `:60`, `:97` (`test_parentless_cloud.release`) — column mass kept, negative column clamped (+deficit), zero column (1e-12 / 1e-6).
  - `tests/test_parentless_cloud_nb1.cpp:101`, `:113` (`test_parentless_cloud_nb1.release`) — nb1 = 1 and 2.
  - `tests/test_parentless_cloud_nb1_mp.cpp:17` (`test_parentless_cloud_nb1_mp.release`; `_gloo` with UCX) — across processes, rain and total mass 1e-12.
  - `tests/test_vapor_column_nb1.cpp:122`, `:133` (`test_vapor_column_nb1.release`) — vapour column split on x1 equals one block.
  - `tests/test_fix_vapor_reports_failure.py` (`_python`, `_cuda_python`); `tests/test_fix_vapor_counts_every_column.py` (one broken column of 16 384 reported).
- Limits / known issues:
  - Serial callers with nb1 > 1 wait at the gather (PR #244 Limits). The cross-process gather has not run on CUDA.
  - The weight is relative to the column's first cell. Grids with last-bit spacing differences can move at round-off (PR #243 Limits).
- Discrepancies: PR #230's limit "the repair is per meshblock" is superseded by #244/#268 (whole-column gather, `src/eos/equation_of_state.cpp:276-305`).


#### 10.5 Column vapor and cloud repair (`fix_vapor_impl`)
<sub>inventory D: Scheme: Column vapor and cloud repair (`fix_vapor_impl`)</sub>

- Summary: a top-down scan per column.
  - On a negative vapor at `is`, the scan accumulates volume-weighted vapor and "major" (dry) mass downward until the
    sum is ≥ 0, then sets a common mass fraction yfrac = Σvapor/Σmajor over the covered cells.
  - If the column below is exhausted, the deficit is taken from the cells above as a bounded transfer (coverage checked
    before writing).
  - It fails (returns 1, leaving the column untouched) if any major ≤ 0 or the cells above are insufficient.
  - CPU counts failures with `std::atomic`, CUDA with a device tensor and `atomicAdd`.
  Switch: as for the limiter.
- Derivations: mass conservation of Σvapor·V (volume-weighted, #241), and the bound on the upward transfer. Re-derive
  from `src/eos/fix_vapor_impl.h:9-79`. The source has the argument in comments and PR #243 and #218 text only.
- Figures: a column with a negative cell; a downward accumulation window flattened to yfrac; the upward-transfer
  variant for a bottom-cell deficit.
- Code:
  - `src/eos/fix_vapor_impl.h:9` — `fix_vapor_impl` (downward window `:32-39`, upward branch `:41-64`, flatten
    `:66-70`).
  - `src/eos/eos_dispatch.cpp:79` — `call_fix_vapor_cpu` (atomic; call at `:93`). `src/eos/eos_dispatch.cu:52` —
    `call_fix_vapor_cuda` (call at `:67`).
- Tests:
  - `tests/test_eos.cpp` (`test_eos.release`) — `eos_limiter.*` (`:40-109`): zero column, bottom cell repaired from
    above, net deficit rejected without writing, single cell rejected, downward branch unchanged.
  - `tests/test_fix_vapor_volume.cpp` (`test_fix_vapor_volume.release`). Column mass is kept on varying cell volume.
  - `tests/test_fix_vapor_reports_failure.py` (`test_fix_vapor_reports_failure_python`, plus `_cuda`). An unrepairable
    column raises on every device.
  - `tests/test_fix_vapor_counts_every_column.py` (`test_fix_vapor_counts_every_column_python`). One broken column in
    16,384 is still reported (thread race).
- Limits / known issues:
  - The downward branch flattens (a mixing repair), so it moves vapor beyond the deficit.
  - The upward branch fires in practice only for denormals (report §8).
  - Each call costs one device sync (report §8).
- Discrepancies: the report §10 excerpt of the upward branch sums `vapor[j]` unweighted. The code is volume-weighted
  (`fix_vapor_impl.h:43-61`, #241). Code wins.


#### 10.6 Precipitation and evaporation kinetics (driver-level coupling, kintera rates)
<sub>inventory B: Scheme: Precipitation and evaporation kinetics (driver-level coupling, kintera rates)</sub>

- Summary: after the dynamics stages, the example drivers refresh `hydro_w` from `hydro_u` (so kinetics sees the
  saturation-adjusted state, #257), build concentrations with kintera `ThermoX`, evaluate kintera `Kinetics`
  rates/Jacobian, take one linearised backward-Euler step (`evolve_implicit`), add `del_rho` to the species rows of
  `hydro_u`, and call `check_redo`. Latent heat enters through the EOS reference energies (E untouched). Two-product
  evaporation (NH4SH ⇒ NH3 + H2S) uses the extent-to-equilibrium law in kintera at the pin. Switch: driver-level (cards
  with `type: evaporation` reactions), not a snapy library option.
- Derivations:
  - Steady-diffusion evaporation rate, the two-product extent quadratic, and the no-overshoot property of one implicit step. exists: `sources/canoe__EVAPORATION_MULTIPRODUCT_TECH_REPORT.md` §4 (step-by-step) and the overshoot analysis that follows. Code: `kintera src/kinetics/evaporation.cpp:128`, `:165-191@4dc613d`.
  - Notation: this is the only derivation in chapters 2 and 10 that exists rather than needs re-deriving, and it
    is written in symbols that NOTATION.md reserves for other quantities — $r$ (radius), $\kappa$ (thermal
    diffusivity), $C$ (Courant number), $D$ ($\mathcal D$, the gravity-work defect), $K$ ($K_f$, a face
    diffusion coefficient), $F$ (mass flux density), $\mathbf v$ (velocity), and $x$ (a coordinate). Re-writing
    it in the report's notation (STYLE.md §2) needs NOTATION.md §2a first. The chapter author writes a
    translation table as the first thing in the Derivation layer and does not paste the note's symbols.
  - Energy bookkeeping of a species-only update with reference energies. re-derive from `examples/run_hydro.cpp:171-191`.
- Figures:
  - Operator-split diagram: RK stages (dynamics + saturation adjustment) → cons→prim refresh → kinetics implicit step → check_redo.
  - Extent law vs old η law for NH4SH as a function of saturation ratio (regenerate from kintera).
- Code:
  - `examples/run_hydro.cpp:171` — kinetics block; `:175` refresh comment (`peos->forward`); `:187` `evolve_implicit`; `:191` species update; `:193` `check_redo`.
  - `examples/jupiter_evap_precip_1d.cpp:244`, `:254`, `:259`, `:261` — same pattern.
  - `kintera src/kinetics/evaporation.cpp:128@4dc613d` — `EvaporationImpl::forward`; extent branch `:165`.
- Tests:
  - `tests/test_uranus_cycle1_abort.cpp:115` `UranusLate.column_reaches_cycle_40` — no redo after the #257 refresh fix.
  - No snapy test of the evaporation rate; kintera evaporation tests are on the kintera side (report §2).
- Limits / known issues:
  - The kinetics update is not followed by the conserved limiter before `check_redo` (`examples/run_hydro.cpp:191-193`). Negative species from kinetics surface as a limiter repair at the next step's stage 0 (issue #256/#263 history).
  - Kinetics updates the full array, ghosts included, without an exchange; the next stage's boundary fill/exchange restores consistency.
- Discrepancies: the evaporation report's STATUS says "implemented on a branch, not landed" (kintera `f94a335`). At `kintera 4dc613d` the extent law **is** present (`kintera src/kinetics/evaporation.cpp:165`, commit `07c7e9c` "#114"). Code wins.


#### 10.7 Passive scalar (tracer) transport per dry air, with optional upper bound
<sub>inventory B: Scheme: Passive scalar (tracer) transport per dry air, with optional upper bound</sub>

- Summary: `r = s/rho_d`. Reconstruct r, upwind it with the hydro **dry** mass flux `flux{1,2,3}[IDN]`, apply the
  donor-cell positivity limiter if the EOS limiter is on, and optionally a second limiter on the complement
  `b rho_d - s` (upper bound `b`), adding only the change. Tendency `-dt div F`. Tracers ride with the VIC dry face
  transfer and with dry-density sources (native forcings, user forcings) via `carry_dry_source`. On the cubed sphere
  the reconstructed L/R states go through direction-suffixed keys. Switch: YAML `scalar/{nvar|names, upper-bound (−1 = off; 0 refused; needs limiter), reconstruct{shock,type,scale}, riemann-solver{type must be upwind}}`.
- Derivations:
  - Dry-air convention and the tracer transfer under the VIC mass correction. PR #220 states results; re-derive from `src/mesh/meshblock.cpp:634-678`.
  - Complement bound `r <= b` via positivity of `b rho - s` with flux `b F_m - F_s`, and its CFL caveat. Argued in the code comment; re-derive from `src/scalar/scalar.cpp:164-200`. Seam history: `sources/canoe__tracer_seam_TECH_REPORT.md` (mechanism and measurements).
- Figures:
  - Face: dry mass flux sets the upwind direction; tracer flux `F_m r_upwind`; complement flux.
  - Cubed-sphere seam: suffixed `scalar_wl:+`/`scalar_wr:-` keys preserving L/R roles at a flipped edge.
- Code:
  - `src/scalar/scalar_options.cpp:11` — `ScalarOptionsImpl::from_yaml` (keys `:23`; upper-bound `:27`; no `reconstruct` → `recon = nullptr` `:41`).
  - `src/scalar/scalar.cpp:16` `reset` (upwind only `:21`; bound needs limiter `:30`); `:64` `forward` (`r = u/rho_d` `:72`; positivity `:158`; upper bound `:175`; divergence `:202`).
  - `src/mesh/meshblock.cpp:27` `set_scalar_primitive`; `:634` `carry_dry_source`; `:663-676` VIC tracer transfer; `:768` RK average.
- Tests:
  - `tests/test_scalar.cpp:71` `initialize_and_transport_scalar`; `:114` `scalar_upper_bound_holds_both_sides` (`test_scalar.release`).
  - `tests/test_tracer_dry_convention.py` (`_python`) — init/implicit/relax arms, TOL 1e-12 with a 1000× non-vacuity check (`:32`, `:134-179`).
  - `tests/test_stage_forcing_dry_tracer.py`, `tests/test_dry_carry_zero_base.py`; `tests/test_forcing.cpp:1309` `native_dry_source_uses_each_rk_stage_weight` (1e-12), `:1363` `..._preserves_scalar_bounds_at_every_rk_order` (1e-12).
  - `tests/test_flux_positivity_cubedsphere.py` (dry tracer seams).
- Limits / known issues:
  - A scalar block without `reconstruct` sets `recon = nullptr`, and `ReconstructImpl::create` then refuses it (`src/recon/reconstruct.cpp:164`). In practice `reconstruct` is mandatory when `nvar > 0`.
  - `ScalarOptions` has `thermo`/`kinetics` members and `ScalarImpl` creates `pkinetics`, but they are never parsed (`src/scalar/scalar_options.cpp:44-45` commented out) or used.
  - The upper bound holds only while the mass Courant number < 1 and rho moves by `-dt div F_m` alone (comment `src/scalar/scalar.cpp:170-174`).
  - A uniform-tracer test cannot detect a wrong donor choice (`tests/test_tracer_dry_convention.py` docstring).
- Discrepancies: none.


#### 10.8 Sedimentation of condensates (recommended to move to Ch. 10)
<sub>inventory B: Scheme: Sedimentation of condensates (recommended to move to Ch. 10)</sub>

- Summary: each listed cloud species settles at `v_sed`. `v_sed` is a prescribed non-zero `const-vsed` (replaces), or
  Stokes `beta/(9 eta) 2 r^2 g (rho_p - rho)` with Chapman–Enskog viscosity
  `eta = (5/16) sqrt(m k T/pi) (kT/eps)^0.16/(1.22 d^2)`, mean free path `lambda = eta/p sqrt(pi k T/(2m))`, Cunningham
  `beta = 1 + Kn(1.256 + 0.4 e^{-1.1/Kn})`, clamped to `±upper-limit`. A donor-cell x1 flux of mass, momentum and
  energy `rho_s v_sed (u0 + cv T + KE)` is added to `flux1` after the Riemann solver. Faces are sealed only at physical
  x1 walls. A fused CPU/CUDA kernel serves ideal-moist; a tensor path serves the rest; MPS has its own path. Switch:
  YAML top-level `sedimentation:` `{radius, density, const-vsed (per species), a-diameter 2.827e-10, a-epsilon-LJ 8.24e-22, a-mass 3.34e-27, upper-limit 5e3}`.
  Requires `forcing/const-gravity`; inactive if `grav1 == 0` or with `disable_flux_x1`.
- Derivations:
  - Stokes–Cunningham settling and the Chapman–Enskog viscosity of an H2 background. re-derive from `src/sedimentation/sed_vel.cpp:34-71` and `src/sedimentation/sed_hydro_impl.h:57-79` (none in sources).
  - Donor (upwind) choice for rising vs settling particles and wall sealing. re-derive from `src/sedimentation/sed_hydro_dispatch.hpp:12-24`, `src/sedimentation/sed_hydro_impl.h:100-127`.
  - Energy flux carried by settling condensate (no `R T` share). re-derive from `src/sedimentation/sed_hydro_impl.h:84-92`.
- Figures:
  - x1 column: settling flux taken from the cell above each face, rising flux from the cell below; sealed physical walls, open internal seams.
  - v_sed(r) for the H2 defaults at two pressures (Stokes vs slip-corrected).
- Code:
  - `src/sedimentation/sed_options.cpp:17` — `SedHydroOptionsImpl::from_yaml` (particles must be clouds; `hydro_ids`); `:47` `SedVelOptionsImpl::from_yaml` (`check_keys` `:48-50`; radius>0 or const-vsed≠0 `:111-118`).
  - `src/sedimentation/sed_vel.cpp:34` — `SedVelImpl::forward` (`const_vsed` replaces Stokes `:68`).
  - `src/sedimentation/sed_hydro.cpp:68` — `SedHydroImpl::forward` (wall/seam bounds `:80-83`; fused vs tensor `:86`; dispatch `:115`); `:18` `sedimentation_flux_tensor`; `:54` `reset` (refuses missing gravity).
  - `src/sedimentation/sed_hydro_impl.h:33` `sedimentation_donor_impl`; `:100` `sedimentation_flux_impl`.
  - `src/sedimentation/sed_hydro_dispatch.cpp:122` (CPU), `:159` (MPS); `src/sedimentation/sed_hydro_dispatch.cu:72` (CUDA).
  - Call site: `src/hydro/hydro_forward.cpp:427-431` (`fsed1` saved for the positivity carry); created at `src/hydro/hydro.cpp:126`.
- Tests:
  - `tests/test_forcing.cpp:1407` `fused_sedimentation_matches_tensor_path` (1e-10 rel.); `:1430` `sedimentation_is_sealed_only_at_physical_walls`; `:920` `vertical_gravity_work_includes_sedimentation_mass_flux`.
  - `tests/test_sedimentation_guards.cpp` (`test_sedimentation_guards.release`): `:93` refuses a card without const-gravity; `:111` skipped when the x1 flux is off; `:133`/`:137` rising cloud taken from the cell below (1e-9 rel.).
  - `tests/test_sedimentation_cubed_seam.cpp` (`test_sedimentation_cubed_seam.release`, 2 ranks; `test_sedimentation_cubed_seam_gloo` with UCX): seam flux bitwise identical on both ranks, condensate mass conserved to 1e-12, limiter active, pinned momentum/energy sums (1e-7 / 5e-3 abs, `:114-115`).
  - `tests/test_two_cards_species.cpp:147` `two_cards_sedvel_after_block_built`.
- Limits / known issues:
  - No sedimentation CFL in `HydroImpl::max_time_step` (no `vsed` term, `src/hydro/hydro.cpp:292-380`). Over-draining is caught only by the positivity limiter.
  - The MPS path is untested (PR #216 Limits).
  - Casting a block to Float32 turns the index buffer into floats (PR #258).
  - `fric-heat` was removed (it double-counted the face gravity work, PR #217).
- Discrepancies: none found (k_B·T mean-free-path fix and `const-vsed` replacement are consistent across tensor, fused and MPS paths per PR #216; MPS not re-verified).


---

<a id="ch11"></a>
## Chapter 11. Boundary conditions and immersed solids

The boundary-function registry and every boundary type, when ghosts are filled, the pointer to exchange-filled ghosts (chapter 3 and 14), immersed solids (own section), and the interaction of the boundaries with the well-balanced reference. The VIC's column closure moved to 7.B.

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: the external boundary-function registry and each built-in function; when and how ghosts are filled for hydro
(conserved and primitive), scalars, and auxiliary fields; exchange-based ghosts (slab and cubed layouts, cubed-sphere
panels) as far as they substitute for a boundary function; immersed solids; and how boundary types interact with the
well-balanced reference state and with the VIC.

Recommendations on structure:
- Move the exchange and cubed-sphere ghost machinery (serialize, interpolate, velocity transform, corners) to the
  parallel/layout chapter. Keep here only the rule "an internal or periodic face has its bfunc nulled and is filled by
  exchange", plus the θ raw-copy rule.
- Give **immersed solids** their own section. They touch reconstruction (face-state mirror), dt, VIC rows, the gravity
  fixer and diffusion (unsupported).
- Put "BCs and the reference state" here as a short section that points to the WB chapter's derivation
  (`docs/derivations/wb-ref-wall.md`).

</details>


#### 11.1 Boundary-function registry, YAML parsing, and face classification
<sub>inventory D: Scheme: Boundary-function registry, YAML parsing, and face classification</sub>

- Summary: boundary functions have the signature `f(var, dim, BoundaryFuncOptions)`. They are registered by name with
  the `BC_FUNCTION` macro (`<name>_inner`/`<name>_outer`). YAML `boundary-condition/external/x{1,2,3}-{inner,outer}`
  picks `<name>` (default `reflecting`).
  - Internal block faces and periodic faces handled by the layout get a `nullptr` bfunc, so they are filled by
    exchange.
  - `is_physical_boundary` means "bfunc non-null". `is_wall_boundary` is a name whitelist used by diffusion.
    `is_x1_wall` means physical and not periodic (used by gravity work).
  - Face functions must be idempotent and shape-agnostic (they are re-applied on tangential slabs).
  Switch: YAML keys above (`src/mesh/meshblock_options.cpp:88-205`).
- Derivations: none (infrastructure).
- Figures: a block with its six faces coloured by classification (physical wall, outflow, periodic-by-exchange,
  internal seam).
- Code:
  - `src/bc/bc_func.hpp:32-35` — the `BC_FUNCTION` macro and its contract comment (`:28-31`); `:39` — `is_outflow`.
  - `src/bc/bc.hpp:19` — `enum BoundaryFace`; `:29` — `BoundaryFuncOptions` (EOS, coord, reference, tracers, type,
    nghost).
  - `src/mesh/meshblock_options.cpp:100-110` — x1-inner parse (periodic sets `layout.periodic_z` only for layout type
    `cubed`); `:141-142` and `:178-179` — x2/x3 periodic set `periodic_x`/`periodic_y`.
  - `src/mesh/meshblock_options.cpp:218` — `face_of`; `:229` — `is_physical_boundary`; `:243` — `is_wall_boundary`.
  - `src/mesh/meshblock.cpp:138-167` — nulls the bfuncs of internal and periodic faces (slab and cubed layouts).
  - `src/hydro/hydro.cpp:195` — `is_x1_wall`.
- Tests:
  - `tests/test_yaml_keys.cpp` (`test_yaml_keys.release`) — key validation.
  - `tests/test_wb_wall_corner.cpp` — the user wall under another name must behave like `reflecting`.
- Limits / known issues:
  - A bfunc installed programmatically without a name cannot be classified as a wall (a `TORCH_WARN_ONCE` fires,
    `meshblock_options.cpp:250-258`).
  - On a cubed-sphere layout the x2/x3 faces carry `custom` (a no-op, see the examples), so `is_physical_boundary` is
    true at panel edges. This needs verification wherever code gates on it (for example the corner refresh in
    `exchange_ghost_zones`).
- Discrepancies:
  - `is_wall_boundary` whitelists `fixed_temperature_inner/outer` (`meshblock_options.cpp:271`), but no such BC function
    is registered (a grep of `BC_FUNCTION` finds none). The name is dangling.
  - The comment at `meshblock_options.cpp:264-265` calls outflow's ghost "zero-gradient". At dae902b `outflow` is the
    characteristic radiating condition; `extrapolation` is the zero-gradient one.


#### 11.2 Reflecting wall
<sub>inventory D: Scheme: Reflecting wall</sub>

- Summary: ghosts mirror the interior (`flip`). For conserved and primitive types the normal velocity is negated. For
  `kScalar` it is a mirror only. Switch: `reflecting` (the default for every face).
- Derivations: an odd/even parity argument for zero normal mass flux at the face. Re-derive from
  `src/bc/bc_func.cpp:10-34` (textbook).
- Figures: a mirror-ghost picture with ρ, p even and v_n odd.
- Code: `src/bc/bc_func.cpp:10` (`reflecting_inner`), `:22` (`reflecting_outer`). The normal-velocity row is `4 - dim`
  (`:18`, `:32`).
- Tests: `tests/test_wb_wall_corner.cpp` (`test_wb_wall_corner.release`, 8 cases); `tests/test_wall_saturation.cpp`;
  `tests/test_wb_ref_wall.cpp`.
- Limits / known issues: a mirror ghost is not a hydrostatic continuation. This motivates the WB wall clamp and the
  even-parity perturbation ghosts (see the reference-state scheme) and the one-sided diffusion coefficients
  (`sources/canoe__diffusion_ghost_TECH_REPORT.md`).
- Discrepancies: none.


#### 11.3 Periodic
<sub>inventory D: Scheme: Periodic</sub>

- Summary: two mechanisms.
  - If the layout carries the periodicity (x2 and x3 always; x1 only for layout type `cubed`), the face bfunc is nulled
    and the exchange wraps neighbours.
  - Otherwise (for example x1 on a slab layout) `periodic_inner`/`periodic_outer` copy within the block.
  Switch: `periodic`.
- Derivations: none.
- Figures: a wrap diagram.
- Code: `src/bc/bc_func.cpp:36,44`; `src/layout/slab_layout.cpp:41-70` (`neighbor_rank` wrap);
  `src/mesh/meshblock.cpp:142-166`; `src/mesh/meshblock_options.cpp:101-103`.
- Tests: `tests/test_flux_positivity.py` (θ through the periodic wrap must be single-valued); `tests/test_exchange.cpp`
  (`test_exchange.release`, 2 ranks).
- Limits / known issues: an in-block copy and an exchange wrap give the same values but run in different code paths.
  The `periodic_x`/`periodic_y`/`periodic_z` mapping to x2/x3/x1 is easy to misread, so tabulate it.
- Discrepancies: none.


#### 11.4 Extrapolation (zero-gradient)
<sub>inventory D: Scheme: Extrapolation (zero-gradient)</sub>

- Summary: every ghost is a copy of the first interior cell. Switch: `extrapolation`. It is also the fallback used by
  outflow for `kScalar` auxiliary fields and for shallow water.
- Derivations: none.
- Figures: none.
- Code: `src/bc/bc_func.cpp:52,60`.
- Tests: `tests/test_radiating_boundary.cpp` — `acoustic_pulses` runs `extrapolation` as the comparison arm (no
  assertion on that arm).
- Limits / known issues: it reflects acoustic waves (not asserted).
- Discrepancies: none.


#### 11.5 Outflow / radiating characteristic boundary
<sub>inventory D: Scheme: Outflow / radiating characteristic boundary</sub>

- Summary: works on primitives against a saved initial background (`boundary_reference_w`/`_r`).
  - The interior perturbation d = w_i − w_bg,i is decomposed into acoustic invariants (±) and entropy, using the
    background impedance ρ₀c₀.
  - Only outgoing characteristics are kept: the + wave if u_n + c ≥ 0, the − wave if u_n − c ≥ 0, and entropy and
    tracers if u_n ≥ 0.
  - The ghost is set to background + α·d. The single factor α ≤ 1 keeps ρ ≥ floor, p ≥ floor, each species ≥ 0, the
    species sum ≤ 1, and tracers ≥ 0; it is reduced by 0.99 where it binds.
  - Velocities are transformed to the face frame and back.
  - Strict checks apply: finite input, an admissible background, ideal-gas, ideal-moist or moist-mixture EOS, and the
    primitive type only.
  - `kScalar` or shallow water falls back to extrapolation.
  Switch: `outflow`. The reference is captured at initialization before any face fill (`meshblock.cpp:426-429`).
- Derivations:
  - Linearised Euler characteristic decomposition and outgoing-wave selection: re-derive from
    `src/bc/bc_func.cpp:108-207`. No derivation in the sources; PR #205 has no body.
  - The α admissibility limiter: re-derive from `:170-200`.
- Figures:
  - An x–t diagram at the outer face with the three characteristics, showing which are copied and which are set to the
    background.
  - The α scaling of a ghost toward the background.
- Code:
  - `src/bc/bc_func.cpp:92` — `check_background`; `:108` — `radiating`; `:113-120` — kScalar fallback; `:158-165` —
    characteristic split; `:172-185` — α; `:210-211` — `outflow_inner/outer`; `:213` — `is_outflow`.
  - `src/mesh/meshblock.cpp:1441` — `has_radiating_boundary`; `:1452` — `apply_boundaries` (primitive conversion, the
    flush of pending faces, tracers ride the dry density `u[IDN]`, #215).
- Tests:
  - `tests/test_radiating_boundary.cpp` (`test_radiating_boundary.release`, 14 tests including CUDA). `acoustic_pulses`:
    reflected fraction < 0.05 for plm and weno5, both signs. Also covered: mixed faces keep the representation and order,
    errors and admissibility, tracers ride the dry density at 1e-12, a moist per-dry-air check, restart continuation,
    decomposed faces match, and CPU/CUDA agreement.
  - `tests/test_radiating_boundary_python.py` (`test_radiating_boundary_python`). Manual Python fills reuse the
    initialized reference.
- Limits / known issues:
  - Not re-applied on tangential corner slabs (`meshblock.cpp:957`).
  - It is not exempted from the gravity-work fixer's sealed-wall check, which refuses mass through any x1 boundary face
    (`meshblock.cpp:899-907`); use `gravity-work-fixer: false`.
  - The VIC closure stays reflecting (Ch 7).
  - The WB reference treats an outflow face as non-wall (`hydro_forward.cpp:310,316`).
- Discrepancies: none against code. The is_wall_boundary comment wording is noted above.


#### 11.6 Custom (no-op) and solid (mask) boundary functions
<sub>inventory D: Scheme: Custom (no-op) and solid (mask) boundary functions</sub>

- Summary: `custom_*` does nothing. It reserves a physical face for user or layout code (cubed-sphere x2/x3 faces in
  the shipped cards). `solid_*` writes 1 into the ghost slab. It is used only for the immersed-solid mask by
  `rectify_solid`. Switch: `custom`, `solid`.
- Derivations: none.
- Figures: none.
- Code: `src/bc/bc_func.cpp:7-8` (custom), `:68-87` (solid).
- Tests: `tests/test_rectify.cpp` (outer ghost slabs are solid, #212).
- Limits / known issues: `solid` as a hydro BC writes 1 into every variable (`is_wall_boundary` comment,
  `meshblock_options.cpp:266-268`). It is meaningless for hydro.
- Discrepancies: none.


#### 11.7 When ghosts are filled (apply_boundaries, exchange_ghost_zones, corner refresh)
<sub>inventory D: Scheme: When ghosts are filled (apply_boundaries, exchange_ghost_zones, corner refresh)</sub>

- Summary:
  - At initialization: primitive fill, primitive exchange, W→U, conserved fill.
  - Each stage: exchange (conserved and scalar, interpolating) at stage start in the MeshBlock path, or at stage end in
    the Mesh path. Then the x1 face functions (except outflow) are re-applied inside the x2/x3 ghost slabs that the
    exchange owns, so corners match (#264). `apply_boundaries` (conserved, scalars `kScalar`) runs at the end of each
    stage, after saturation adjustment (#206).
  - Auxiliary fields such as θ get an exchange plus the bfuncs with `kScalar`.
  Switch: none.
- Derivations: none. Document the corner contract (`bc_func.hpp:28-31`).
- Figures: a 2-D block corner, showing which call writes each ghost region (x1 wall, x2 exchange, corner re-application).
- Code:
  - `src/mesh/meshblock.cpp:401` — `initialize_local` (reference capture `:426-429`, primitive fill `:430`); `:454` —
    `finalize_initialization` (conserved fill at the end).
  - `src/mesh/meshblock.cpp:913` — `exchange_ghost_zones`; the `refresh` lambda at `:951`; outflow is skipped at `:957`.
  - `src/mesh/meshblock.cpp:1452` — `apply_boundaries`; `:841` — the end-of-stage call.
  - `src/mesh/mesh.cpp:353-358` — the multi-block gravity-fixer path re-applies BCs after the fix.
- Tests:
  - `tests/test_wb_wall_corner.cpp` (`test_wb_wall_corner.release`). A resting x2-uniform polytrope stays at rest at the
    x2 block edge: stock and user wall, one versus two blocks, scalar corner primitives, CPU and CUDA.
  - `tests/test_wall_saturation.cpp` (`test_wall_saturation.release`). Energy and water to 1e-12 at walls with phase
    change.
- Limits / known issues: only x1 walls are re-applied, and `Mesh::exchange_ghost_zones` has no refresh (PR #265 Limits).
- Discrepancies: none.


#### 11.8 Exchange-filled ghosts (layouts, cubed-sphere panels) — pointer section
<sub>inventory D: Scheme: Exchange-filled ghosts (layouts, cubed-sphere panels) — pointer section</sub>

- Summary:
  - Slab and cubed layouts copy neighbour ghosts (with a periodic wrap).
  - The cubed-sphere layout interpolates cross-panel ghosts along the panel edge (`interp_ghost`, widened by
    `cs_interp_margin = nghost`) and rotates velocity vectors between panel frames. A subdivided panel runs two rounds,
    intra-panel then cross-panel. Corners are synthesised by averaging the edge strips (`fill_corners`).
  - Donor factors and reconstructed seam states use the raw copy (`interpolate(false)`).
  Switch: `geometry/.../layout` type; SyncOptions `interpolate`, `skip_corner` (default true).
- Derivations: interpolation weights and the velocity transform belong to the cubed-sphere chapter
  (`sources/canoe__cubedsphere_decomposition_TECH_REPORT.md`). Not re-derived here.
- Figures: the panel-edge ghost strip with interpolation sources, the raw copy at depth 1 versus the interpolated copy.
- Code:
  - `src/mesh/meshblock.cpp:554-572` — the two-round split.
  - `src/layout/cubed_sphere_layout.cpp:549` (serialize), `:795` (deserialize; `interp_ghost` at `:936`), `:122`
    (`_velocity_transform`).
  - `src/coord/gnomonic_equiangle.cpp:245` — `interp_ghost`; `src/coord/cubed_sphere_utils.hpp:108` —
    `cs_interp_margin`.
  - `src/layout/layout.cpp:710` — `fill_corners`; `src/layout/layout.hpp:149-153` — SyncOptions flags.
- Tests: `tests/test_cubed_sphere_exchange.cpp` (`test_cubed_sphere_exchange.release`; a subdivided panel matches one
  block bitwise); `tests/test_cubed_sphere_vertical_velocity_exchange.py` (abs/rel 1e-12); `tests/test_mesh_exchange.py`;
  `tests/test_exchange.cpp`; `tests/test_flux_positivity_cubedsphere*.py` (θ raw copy).
- Limits / known issues: corners are a two-edge average, not an interpolation.
- Discrepancies: none.


#### 11.9 Immersed solids (mask, rectification, face-state mirror, refill)
<sub>inventory D: Scheme: Immersed solids (mask, rectification, face-state mirror, refill)</sub>

- Summary: a user-supplied mask `vars["solid"]` (nc3, nc2, nc1) is handled as follows.
  - It can be pre-processed by `rectify_solid`: all ghosts are set solid, then a DP finds the minimum number of 0→1
    flips so that fluid runs have length ≥ 3 and solid runs ≥ 2 in each dimension (MAXRUN 4, at most `max_iter`
    sweeps), then the BCs are applied to the mask.
  - At initialization the solid fill states are saved (`fill_solid_hydro_w/u`, velocity zeroed), and solid primitives
    are set to (solid_density, solid_pressure, v = 0, y = 0).
  - Each stage:
    - the solid primitives are re-marked;
    - at faces touching a solid, the reconstructed left and right states are mirrored with the normal velocity negated;
    - c_s = 1e-8 is used in solids for dt;
    - the VIC gives solid rows the identity and closes fluid segments with reflecting blocks;
    - after the RK average, solid conserved cells are refilled;
    - the gravity fixer excludes solids.
  Switches: `boundary-condition/internal/{max-iter, solid-density, solid-pressure}` (defaults 5, 1e3, 1e9;
  `src/bc/internal_boundary.cpp:31-33`); the presence of `vars["solid"]`.
- Derivations:
  - The face-state mirror equals a reflecting wall at the solid face: re-derive from
    `src/bc/internal_boundary.cpp:70-95`.
  - The rectification DP (minimum flips under run-length constraints): re-derive from `src/bc/flip_zero_impl.h:75-200`
    and `src/bc/bc_dispatch.cpp:40-49` (minRun0 = 3, minRun1 = 2, 0→1 flips only).
  - The VIC solid closure: re-derive from `implicit_dispatch.cpp:57-69` and `vic_assemble_*_impl.h` with
    `solid_lower`/`solid_upper`.
- Figures:
  - A staircase solid in a 2-D grid, with faces where the mirror applies and arrows for the normal velocity sign flip.
  - Before and after rectification of a 1-D run (thin fluid gaps filled).
- Code:
  - `src/bc/internal_boundary.cpp:47` — `mark_prim_solid_`; `:62` — `fill_cons_solid_`; `:70` —
    `InternalBoundaryImpl::forward` (the face-state mirror).
  - `src/bc/rectify_solid.cpp:109` — `rectify_solid`, with the BC application at `:164-166`;
    `src/bc/bc_dispatch.cpp:17` — `flip_zero_cpu` (atomic count, #212).
  - `src/mesh/meshblock.cpp:474-496` — the initialization fill states; `:782-784` — the per-stage refill; `:850`/`:877`
    — fixer exclusion.
  - `src/hydro/hydro_forward.cpp:226-227` (re-mark), `:396`, `:604`, `:626` (face mirror per dimension).
  - `src/hydro/hydro.cpp:304` (dt); `:400-404` (VIC input and du masking).
  - Python binding: `python/csrc/pybc.cpp:61`.
- Tests:
  - `tests/test_rectify.cpp` (`test_rectify.release`). Every ghost slab is solid after rectification, the outer ones
    included.
  - `tests/test_flip_zero_count.cpp` (`test_flip_zero_count.release`). The flip count on 8 threads equals the serial
    count.
  - `tests/test_implicit_stratified_solid.py` (`test_implicit_stratified_solid_python`). Solid-wall mass closure with
    the VIC; `solid_run` with top, bottom and strided placements.
- Limits / known issues:
  - Diffusion reads the solid placeholder states as fluid (a 500.5× face heat capacity). Recorded, not fixed
    (`sources/canoe__diffusion_ghost_TECH_REPORT.md` §3). No shipped card pairs solids with diffusion.
  - The mask is static (filled from initialization).
  - Scalars in solids are not refilled (only `hydro_u`, `meshblock.cpp:782-784`). Needs checking.
- Discrepancies: none.


#### 11.10 Boundary conditions and the well-balanced reference state
<sub>inventory D: Scheme: Boundary conditions and the well-balanced reference state</sub>

- Summary: with gravity, the x1 sweep reconstructs perturbations about a hydrostatic reference.
  - At a **physical, non-outflow** x1 face, the perturbation ghosts (p′, ρ′) are filled with even parity rather than the
    bfunc's state (`hydro_forward.cpp:305-321`).
  - The reference's own stencils never read wall ghosts when `dynamics/wb-wall-clamp` is true (the default). They
    continue ρ/p linearly past the wall.
  - The optional x1 mass-covariance correction uses one-sided ρ′ and odd velocity ghosts at walls (`:333-353`).
  - Without WB (shallow water, or no pressure row), physical x1 faces under gravity revise the face L/R states to equal
    p and ρ (`_revise_x1*_lr`).
  - The isentropic ghost revision (`_revise_x1*_ghost`) is dead code (commented out at `hydro_forward.cpp:256-259`).
  - Outflow faces are excluded from the even-parity fill and from the centroid stencils.
  - Periodic x1 counts as "physical" for `phys_in/out` here but not for `is_x1_wall`.
  Switches: `dynamics/wb-wall-clamp` (YAML, default true; `src/hydro/hydro_options.cpp:57`, `hydro.hpp:54`); env
  `SNAP_WB_REF4` (default 0, `src/hydro/wb_ref4.cpp:87`); env `SNAP_X1_MASS_COVARIANCE` (default 0,
  `hydro_forward.cpp:41`); env `SNAP_X1_CENTROID_EXACT` (default 0, `src/coord/x1_centroid.cpp:96`).
- Derivations:
  - The wall-ghost order of the default reference: exists: `docs/derivations/wb-ref-wall.md@e894700` (also
    `sources/deriv__wb-ref4.md` for the REF4 variant). The WB chapter owns them; cite them here.
  - Even-parity perturbation ghosts give zero flux residual at rest: re-derive from `hydro_forward.cpp:305-321`.
- Figures: the bottom wall with p_ref and ρ_ref continued past the wall (clamp) versus a repeated wall cell, with the
  even-parity p′ ghosts.
- Code:
  - `src/hydro/hydro_forward.cpp:253-254` (phys flags); `:271-272` (`wb_x1`); `:297` (`_hydro_ref_x1`); `:305-321`
    (even parity); `:388-392` (non-WB `_revise_x1*_lr`).
  - `src/hydro/hydro.cpp:484` — `_hydro_ref_x1` (phys_in/out `:530-531`; clamp passed at `:537`); `:429-441` —
    `_revise_x1*_lr`; `:443-481` — the unused `_revise_x1*_ghost`.
  - `src/hydro/hydro_ref_x1_impl.h:69` (`hydro_ref_x1_wall_rop`), `:87` (`hydro_ref_x1_rop_smooth`), `:132-135` and
    `:189-192` (wall clamp gating).
  - `src/hydro/balance_column.cpp:31` — refuses `wb-wall-clamp: false`.
- Tests:
  - `tests/test_wb_ref_wall.cpp` (`test_wb_ref_wall.release`). Interior faces are O(dz²) at the walls.
  - `tests/test_hydro_ref_x1.cpp` (`test_hydro_ref_x1.release`). The wall clamp keeps the interior free of ghosts
    (`:217`), and without it they do reach the interior (`:236`). Thin-block variants are included.
  - `tests/test_hydro_options.cpp` — `wb_wall_clamp_ships_enabled` (`:240`), `wb_wall_clamp_reaches_the_x1_reference`
    (`:326`).
  - `tests/test_balance_column.cpp` (`test_balance_column.release`, plus env arms) and `tests/test_face_floor.cpp`.
- Limits / known issues: a resting column on a stretched x1 grid is not at rest (#280, parked). The default reference
  is a silent choice (#281).
- Discrepancies: the wb-ref-wall derivation cites line numbers "at 37dce4e" (`hydro_ref_x1_impl.h:74`, `:159-167`,
  `hydro_forward.cpp:276-292`). At dae902b the corresponding code is at `hydro_ref_x1_impl.h:69,87-101,189-192` and
  `hydro_forward.cpp:305-321`. The doc's line references are stale.


---

<a id="ch12"></a>
## Chapter 12. Build-time and run-time switches and configurations

Every switch that changes what snapy compiles or computes: 12.1 build time, 12.2 environment (the five `SNAP_*` scheme switches), 12.3 YAML scheme keys, 12.12 the coverage matrix (switch combination -> ctest entries). The scheme switches are process-global and read once; their couplings are real constraints, so they get this chapter rather than being scattered over chapters 4-6 (each physics section still states its own switch in its Summary layer).

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: every switch that changes what snapy compiles or computes. That covers CMake options and cache variables,
`configure.h` macros and compile definitions, environment variables read through `get_env`/`std::getenv`, and the
YAML option keys that select a scheme (gravity-work mode, fixer, wall clamp, implicit scheme, limiter, nghost,
reconstruction and Riemann types). For each switch the chapter gives how it is set, its default, the code that reads
it, its couplings, and the tests that run it. It ends with a coverage matrix (switch combination -> ctest entries).
**Recommendation: keep it as one chapter, in three parts:** 12.1 build-time, 12.2 environment (the five `SNAP_*`
scheme switches are the core), 12.3 YAML scheme keys. Put the coverage matrix in 12.12 and cross-link it from
Chapter 15. Do not merge it into Ch.15: Ch.15 indexes tests by topic, while 12.12 indexes them by switch
combination. The study switches (`SNAP_*`) are process-global and read once, and their couplings
(implication, nghost, grid type, gravity-work mode) are real constraints. They deserve a chapter of their own and should
not be scattered across Chapters 4-6.

</details>


### 12.1 Build time


#### 12.1 CMake options and cache variables (build-time)
<sub>inventory E: Scheme: CMake options and cache variables (build-time)</sub>

- Summary: top-level `option()`s and cache variables, plus three variables (`buildl`, `UCX_FOUND`, `CUDAToolkit_FOUND`)
  that gate which tests are registered. Switch: `cmake -D<NAME>=...`; defaults below.

| Name | Default | Set at | Effect / reader | Couplings |
|---|---|---|---|---|
| `BUILD_TESTS` | ON | `CMakeLists.txt:7@e894700` | `add_subdirectory(tests)` at `CMakeLists.txt:149-153@e894700` | none |
| `FULL_TESTS` | OFF | `CMakeLists.txt:8@e894700` | adds `test_shallow_xy`, `test_shallow_splash` reference tests (`tests/CMakeLists.txt:368-371@e894700`), the decomp matrix `test_shallow_splash_decomp`, `test_shallow_xy_decomp`, `test_shallow_splash_ucx_cuda_decomp` (`tests/CMakeLists.txt:461-513@e894700`) and, on Apple, `test_exchange_decomp` (`tests/CMakeLists.txt:443@e894700`) | CI sets ON for non-PR Linux runs (`.github/workflows/ci.yml:87@e894700`) |
| `BUILD_EXAMPLES` | OFF | `CMakeLists.txt:9@e894700` | **dead**: the guard is commented out and `add_subdirectory(examples)` is unconditional (`CMakeLists.txt:155-158@e894700`) | example tests need `bin/straka.<b>` etc., so examples are always built |
| `CUDA` | OFF | `CMakeLists.txt:10@e894700` | `enable_language(CUDA)` (`:26-28`), CUDA arch list (`:109-143`), `CUDA_OPTION` -> `USE_CUDA` (`cmake/parameters.cmake:6-10@e894700`); requires commux CUDA sidecar (`src/CMakeLists.txt:93-104@e894700`) | not CUDA => every ctest whose name contains `cuda` or whose labels are `cuda`/`gpu` is DISABLED and every test gets `SNAPY_BUILD_CUDA=0` (`tests/CMakeLists.txt:517-536@e894700`) |
| `NETCDF` | ON | `CMakeLists.txt:11@e894700` | `NETCDF_OPTION` -> `NETCDFOUTPUT` and `find_package(NetCDF REQUIRED)` (`cmake/parameters.cmake:20-25@e894700`) | none |
| `UCX` | ON (Linux), OFF (Apple) | `CMakeLists.txt:13,16@e894700` | `UCX_OPTION` -> `USE_UCX` (`cmake/parameters.cmake:13-17@e894700`); `cmake/ucx.cmake:1-73@e894700` needs Python `commux` and sets `UCX_FOUND` | `UCX_FOUND` gates `test_exchange_ucx`, `test_sedimentation_cubed_seam_gloo`, `test_parentless_cloud_nb1_mp_gloo` (`tests/CMakeLists.txt:132,145,154@e894700`) |
| `PNETCDF` | ON (Linux), OFF (Apple) | `CMakeLists.txt:14,17@e894700` | `PNETCDFOUTPUT`; needs Python `pinc` (`cmake/parameters.cmake:28-46@e894700`) | `run_straka.cmake`/`run_shallow_splash.cmake` rewrite `type: pnetcdf` to `netcdf` when `NO_PNETCDFOUTPUT` (`tests/run_straka.cmake:26-29@e894700`) |
| `NMASS` | 0 | `cmake/parameters.cmake:3@e894700` (`set_if_empty`) | `configure.h.in:19@e894700`; Athena++ legacy index layout in `src/snap.h:8-27@e894700` | **effectively dead**: `static_assert(ICY == IPR + 1)` at `src/snap.h:52@e894700` refuses NMASS>0, so the check at `src/eos/equation_of_state.cpp:89@e894700` is unreachable |
| `CMAKE_BUILD_TYPE` | Release | `CMakeLists.txt:61-63@e894700` | flags in `cmake/compilers.cmake:15-35@e894700` (Release `-O3 ...`; Debug `-g3 -fsanitize=address,undefined` for GNU/Clang) | ctest names carry `buildl`; the example runners hard-code `-Dbuildl=release` (`tests/CMakeLists.txt:374@e894700`) |
| `SNAPY_TEST_PYTHONPATH` | "" (cache PATH) | `tests/CMakeLists.txt:350-351@e894700` | prepended to PYTHONPATH of every `*_python` ctest (`:350-355`); unset => warning that python ctests test the installed snapy (`:357-359`) | `test_python_import_path_python` checks the wiring (`tests/CMakeLists.txt:318-326@e894700`) |
| `KINTERA_DATA_DIR` | undefined | `tests/CMakeLists.txt:336-340@e894700` | symlinks `nasa9.dat` into the test dir | none |
| `EIGEN`, `FMT`, `GTEST`, `YAML-CPP` | ON | `cmake/macros/macro_add_package.cmake:10@e894700` via `cmake/{eigen,fmt,gtest,yamlpp}.cmake` | FetchContent with a tarball cache under `.cache/` | none |
| CUDA arch list | 60 61 70 75 80 86 89 (+90 for >=12.0, +120 for >=12.8, minus 60/61/70 for >=13.0) | `CMakeLists.txt:119-142@e894700` | `CMAKE_CUDA_ARCHITECTURES` | none |

- Derivations: none (configuration).
- Figures: (1) a decision tree from `cmake -D...` to which ctest entries exist and which are disabled; (2) a table
  graphic of build flags -> `configure.h` macros -> the `#ifdef` sites.
- Code: listed in the table.
- Tests: `test_python_import_path_python` — `SNAPY_TEST_PYTHONPATH` is first in PYTHONPATH and the caller's entry
  survives (`tests/test_python_import_path.py:16-21@e894700`). No test covers `NMASS`, `BUILD_EXAMPLES` or `NETCDF=OFF`.
- Limits / known issues: `BUILD_EXAMPLES` has no effect. `NMASS>0` cannot compile. CI runs CPU only (`-DCUDA=OFF`,
  `.github/workflows/ci.yml:84@e894700`), so the CUDA entries run only on developer builds.
- Discrepancies: none found in sources.


#### 12.2 `configure.h` macros and compile definitions (build-time)
<sub>inventory E: Scheme: `configure.h` macros and compile definitions (build-time)</sub>

| Macro | Values | Set from | Read at |
|---|---|---|---|
| `USE_C10D_GLOO` | always defined | `configure.h.in:4@e894700` | no reader in `src/` (dead) |
| `USE_UCX` / `NOT_USE_UCX` | UCX option | `configure.h.in:7@e894700` | `default_backend()` returns `ucx` (non-Darwin) or `gloo` at `src/layout/layout.cpp:41-50@e894700`; UCX process group `src/layout/process_group_ucx.cpp:3,22@e894700`; stub that throws "built without UCX" at `src/layout/process_group.cpp:286-291@e894700` |
| `USE_CUDA` / `NOT_USE_CUDA` | CUDA option | `configure.h.in:10@e894700` | `src/mesh/mesh.cpp:16@e894700` (and 51, 75, 83, 104, 137, 161, 176, 203), `src/layout/layout.cpp:17,82,283@e894700`; test gate `snapy_cuda_test_enabled()` at `tests/cuda_test_gate.hpp:9-15@e894700` |
| `NETCDFOUTPUT` / `NO_NETCDFOUTPUT` | NETCDF | `configure.h.in:13@e894700` | `src/output/netcdf.cpp:26,43@e894700`, `src/output/mppnccombine.cpp:55@e894700`, `src/output/combine_netcdf.cpp:41@e894700` |
| `PNETCDFOUTPUT` / `NO_PNETCDFOUTPUT` | PNETCDF | `configure.h.in:16@e894700` | `src/output/pnetcdf.cpp:3@e894700`, `src/mesh/meshblock.cpp:211@e894700` |
| `NMASS` | 0 | `configure.h.in:19@e894700` | `src/snap.h:8,52@e894700` (see above) |
| `DISPATCH_MACRO` | `__host__ __device__` under nvcc | `configure.h.in:21-25@e894700` | kernels |
| `KINTERA_ROOT_DIR`, `HARP_ROOT_DIR` | paths | `configure.h.in:27-28@e894700` | no reader in `src/` |
| `_GLIBCXX_USE_CXX11_ABI` | torch's ABI | `CMakeLists.txt:35-47@e894700` | global compile definition |
| `HAVE_AVX512_CPU_DEFINITION`, `HAVE_AVX2_CPU_DEFINITION` | 1 (non-Apple) | `cmake/compilers.cmake:12@e894700` | torch headers |
| `COMMUX_WITH_CUDA_RUNTIME` | 1 when CUDA | `src/CMakeLists.txt:104@e894700` | commux headers |
- Derivations: none.
- Figures: one box diagram from the CMake option to the macro to the reader file.
- Tests: indirectly, `test_process_group` (`LayoutOptions.DefaultsToPlatformCommunicationBackend`,
  `tests/test_process_group.cpp:74@e894700`).
- Limits: `USE_C10D_GLOO`, `KINTERA_ROOT_DIR`, `HARP_ROOT_DIR` are defined but unused.


### 12.2 Environment


#### 12.3 environment helper `get_env` and the read-once rule
<sub>inventory E: Scheme: environment helper `get_env` and the read-once rule</sub>

- Summary: `get_env(name, def)` returns `getenv(name)` or `def` (`src/layout/layout.hpp:38@e894700`). All five scheme
  switches parse their value once per process into a function-local `static const bool`. Every block in a process
  must make the same choice, or the x1/x2/x3 seam faces stop being single-valued. Consequence: an A/B comparison
  needs one process per arm, so every python oracle spawns a child per arm.
- Parsing rule (verified): `SNAP_FLUX_COVARIANCE`, `SNAP_WB_REF4`, `SNAP_X1_CENTROID_EXACT`, `SNAP_X1_MASS_COVARIANCE`
  are **off unless set**. Off means empty, `0`, `false`, `off` or `no` (case-insensitive); any other value is on.
  `SNAP_GRAVITY_WORK_RADIAL_EXACT` is **on unless** `0/false/off/no`. Note that an *empty* value turns it on, while it
  turns the other four off (`src/hydro/hydro.cpp:245-248@e894700` vs `:212-215`).
- Code: `src/layout/layout.hpp:38@e894700` (`get_env`); readers `src/hydro/hydro.cpp:217-251@e894700`,
  `src/hydro/wb_ref4.cpp:87@e894700`, `src/coord/x1_centroid.cpp:96@e894700`, `src/hydro/hydro_forward.cpp:41@dae902b`.
- Derivations: none.
- Figures: a timeline showing the switch read once at first call and frozen for the process, so each test arm runs in
  a child process.
- Tests: every switch oracle (below) runs arms in child processes. Examples: `tests/test_wb_ref4_order.py:135-139@e894700`,
  `tests/test_gravity_work_radial_exact.py:346-349@e894700`.


#### 12.4 `SNAP_WB_REF4` (fourth-order, cell/face-consistent x1 well-balanced reference)
<sub>inventory E: Scheme: `SNAP_WB_REF4` (fourth-order, cell/face-consistent x1 well-balanced reference)</sub>

- Summary: replaces the kernel's x1 density reference with a fourth-order, cell/face-consistent one; on a
  non-uniform x1 grid it also replaces the reference cell pressure. Switch: env `SNAP_WB_REF4`, default **off**.
- Derivations:
  - fourth-order reference, filter rows, wall extrapolation, resolution flag: exists:
    `docs/derivations/wb-ref4.md@e894700` (also `sources/deriv__wb-ref4.md`; weights checked by
    `docs/derivations/wb_ref4_weights.py@e894700`).
  - seam behaviour of the flag (needs nghost>=3): exists: `docs/derivations/wb-ref4.md@e894700` sec 7 (cited in the
    test header `tests/test_x1_seam_split.cpp:18-22@e894700`).
- Figures: (1) the 5-point filter stencil F = (-1,4,10,4,-1)/16 with the cubic wall extrapolation E past a clamped wall;
  (2) the resolution flag reading scan pressures three cells away across an x1 seam, with the ghost depth marked.
- Code:
  - `src/hydro/wb_ref4.cpp:83-95@e894700` — `wb_ref4_enabled()` — reads the env var once; returns
    `on || x1_centroid_exact_enabled()` (the implication).
  - `src/hydro/hydro.cpp:229@e894700` — `HydroImpl::wb_ref4()` — forwards to it.
  - `src/hydro/hydro.cpp:96-103@e894700` — `HydroImpl::reset()` — `TORCH_CHECK(ng >= 3)` when on and grav1 != 0:
    "SNAP_WB_REF4 (or SNAP_X1_CENTROID_EXACT, which implies it) needs nghost >= 3".
  - `src/hydro/hydro.cpp:566-575@e894700` — `HydroImpl::_hydro_ref_x1` — builds `wb_ref4_stencils` and applies
    `wb_ref4_cells` before the seam exchange; `src/hydro/hydro.cpp:645@e894700` — `wb_ref4_faces` after it.
  - `src/hydro/wb_ref4.cpp:97@e894700` — `wb_ref4_stencils` (usable iff >=4 owned cells next to a clamped wall and nc1>=5,
    `:114`); `:233` `wb_ref4_cells`; `:276` `wb_ref4_faces`.
  - `src/hydro/balance_column.cpp:73-79,90@e894700` — `balance_column` — on a non-uniform grid finds the fixed point of
    the switched reference.
- Couplings: implied by `SNAP_X1_CENTROID_EXACT`. Needs `geometry/cells/nghost >= 3` whenever grav1 != 0, which is a
  setup error otherwise. With grav1 = 0 no reference is built and nghost 1 is accepted. The wall closure uses
  `dynamics/wb-wall-clamp` (the `clamp && phys_in` arguments, `src/hydro/hydro.cpp:569-572@e894700`).
- Tests:
  - `tests/test_wb_ref4_order.py` (`test_wb_ref4_order_python`, `_cuda_python`) — arms unset / `1`, both with
    `SNAP_FLUX_COVARIANCE=1` and `gravity-work: face`, so radial-exact is on by default; the observed order of
    |N2_eff| is >= `ORDER_ON = 2.75` with the switch on and below `ORDER_OFF = 2.5` with it off
    (`tests/test_wb_ref4_order.py:38-39@e894700`), at 1 and 3 e-folds, nz 32/64/128.
  - `test_balance_column_wb_ref4.<b>`, `test_face_floor_wb_ref4.<b>` — the same binaries with `SNAP_WB_REF4=1`
    (`tests/CMakeLists.txt:96-99@e894700`). The balance-column fixed point stays at round-off (1e-14). The face-floor
    dipped-face flux stays at 2.83191e-8 +- 1e-5 relative in every arm (`tests/test_face_floor.cpp:107@e894700`).
  - `test_x1_seam_split_wb_ref4.<b>` — a cold column whose flag switches on above the seam: the 2-block state equals
    the 1-block state to 1e-13 after 20 steps, and nghost 1 and 2 are refused with "needs nghost >= 3"
    (`tests/test_x1_seam_split.cpp:263-287@e894700`).
  - `test_x1_seam_split_wb_ref4_gravity_0.<b>` — grav1 = 0 on nghost 1 sets up and steps 5 times finite
    (`tests/test_x1_seam_split.cpp:345-361@e894700`).
  - `test_x1_seam_split_mp_wb_ref4` — the split across 2 ranks equals 2 blocks in one process and equals 1 block, to 1e-13
    (`tests/test_x1_seam_split_mp.cpp:286-297@e894700`); CUDA arm `test_x1_seam_split_wb_ref4_cuda.<b>`.
- Limits / known issues: no test runs it on a gnomonic-equiangle (cubed-sphere) grid. ISSUES.md item 3: the spec
  numbers rest on commit c5b810d and must be re-measured with `test_wb_ref4_order.py` at dae902b.
- Discrepancies: `sources/gw__NEXTPR_spec_wbref_exact.md:286` says CUDA and multi-process x1 seams were not run with
  the switch on. At dae902b both are run (`_cuda` and `_mp_wb_ref4` arms). That source is stale.


#### 12.5 `SNAP_X1_CENTROID_EXACT` (spherical-polar r^2-average x1 formulas)
<sub>inventory E: Scheme: `SNAP_X1_CENTROID_EXACT` (spherical-polar r^2-average x1 formulas)</sub>

- Summary: on spherical-polar grids the x1 reconstruction, the hydrostatic scan and the reference read plain means
  converted from the r^2 cell averages. The radial pressure force becomes the r^2 average of the gradient (a quintic
  through six faces). Switch: env `SNAP_X1_CENTROID_EXACT`, default **off**.
- Derivations: exists: `docs/derivations/x1-centroid-spherical.md@e894700` (and `sources/deriv__x1-centroid-spherical.md`;
  checked by `docs/derivations/verify_x1_centroid.py@e894700`).
- Figures: (1) a five-cell window converting r^2 means to plain means, mirrored past a clamped wall; (2) the six-face
  quintic p~ for the radial pressure source, with two faces past the seam taken from the neighbour.
- Code:
  - `src/coord/x1_centroid.cpp:92-101@e894700` — `x1_centroid_exact_enabled()` — read once.
  - `src/coord/x1_centroid.cpp:104,117@e894700` — `x1_plain_mean_stencils` (usable iff >=5 cells and enough owned cells
    for the mirrored ghosts); `:157` `x1_plain_means`; `:184,191` `x1_pressure_source_stencils` (usable iff >=6 faces);
    `:224` `x1_pressure_source`.
  - `src/hydro/hydro_forward.cpp:271-287@e894700` — `HydroImpl::forward` — when spherical-polar, `wx1` holds plain means
    and the seam ghosts come from `_x1_ghost_rows` (tag 0x7724).
  - `src/hydro/hydro_forward.cpp:515-538@e894700` — the hydrostatic-split correction (non-hydrostatic < 1) uses the same
    r^2 pressure operator.
  - `src/coord/spherical_polar.cpp:252-264@e894700` — `SphericalPolarImpl::forward` — the radial source with face pressures.
  - `src/hydro/hydro.cpp:270@e894700` — `HydroImpl::_x1_ghost_rows` — the seam exchange of the switched rows.
  - `src/hydro/wb_ref4.cpp:94@e894700` — implies `SNAP_WB_REF4`.
  - `src/hydro/balance_column.cpp:35-40@e894700` — under the switch, `balance_column` refuses any geometry but
    `cartesian`.
- Couplings: implies `SNAP_WB_REF4`, so it inherits the nghost >= 3 setup check (`src/hydro/hydro.cpp:96-103@e894700`).
  On Cartesian grids it changes nothing beyond that implication. `balance_column` must be called with
  `geometry='cartesian'`.
- Tests:
  - `tests/test_x1_centroid_rest.py` (`test_x1_centroid_rest_python`, `_cuda_python`) — r0 = 5 and 1000, nz 32, implicit 0
    and 1, non-hydrostatic 1 and 0. The force imbalance must be < `TOL_ON = 1e-10` with the switch on, and > `TOL_OFF = 1e-8`
    at r0 = 5 with it off (`tests/test_x1_centroid_rest.py:40-41@e894700`).
  - `test_balance_column_x1_centroid.<b>` — the predicate implication `wb_ref4_enabled() == (g || w)`
    (`tests/test_balance_column.cpp:353-358@e894700`); a non-cartesian column is refused (`:363-375,516-524`).
  - `test_face_floor_x1_centroid.<b>` — the same pinned flux as the plain arm.
  - `test_x1_seam_split_x1_centroid.<b>` (+`_cuda`) — 2-block vs 1-block gap <= 1e-13 after 20 steps, nh 1 and 0
    (`tests/test_x1_seam_split.cpp:232-245@e894700`).
  - `test_x1_seam_split_mp_x1_centroid` — across 2 ranks <= 1e-13 against 2 blocks and against 1 block.
- Limits: not defined for gnomonic-equiangle. `balance_column` cannot balance a spherical column under the switch.
  Coverage of its combination with `gravity-work: face` and radial-exact is missing (see matrix).


#### 12.6 `SNAP_FLUX_COVARIANCE` (#289 x2/x3 face-flux covariance and centroid terms)
<sub>inventory E: Scheme: `SNAP_FLUX_COVARIANCE` (#289 x2/x3 face-flux covariance and centroid terms)</sub>

- Summary: adds sigma1^2 covariance terms and the centroid offset -(r_v - r_c) d1F to the x2/x3 face fluxes, for all rows
  (tracer, dry mass, energy). It mirrors p* = p - delta d1 p in the lateral geometric source, gated per direction.
  Switch: env `SNAP_FLUX_COVARIANCE`, default **off**.
- Derivations: exists: `docs/derivations/289-covariance-x3-curved.md@e894700` (and `sources/deriv__289-covariance-x3-curved.md`,
  `sources/study__289-allrows_derivation.md`, `sources/deriv__issue289_moist_covariance_verifier.md`;
  `docs/derivations/allrows_quadrature.py`, `verify_centroid_term.py`, `verify_exact_curved.py@e894700`).
- Figures: (1) an x2 face with the x1 extent of its area measure, marking r_c (face centroid) and r_v (cell centroid);
  (2) the per-direction gating: x2 source with p*, x3 source plain when the x3 flux is off.
- Code:
  - `src/hydro/hydro.cpp:217-227@e894700` — `HydroImpl::flux_covariance()` — read once.
  - `src/hydro/hydro_forward.cpp:54@e894700` — `HydroImpl::_flux_covariance` — the term.
  - `src/hydro/hydro_forward.cpp:599-604,622-627@e894700` — added to `_flux2`/`_flux3`.
  - `src/hydro/hydro_forward.cpp:724-745@e894700` — the p* geometric source with per-direction gating.
- Couplings: none at setup. It acts on x2/x3 faces whatever the grid (Cartesian, spherical-polar, gnomonic).
  `test_wb_ref4_order.py` uses it as part of the WB_REF4 oracle.
- Tests:
  - `tests/test_horizontal_flux_covariance.py` (`test_horizontal_flux_covariance_python`, ctest env
    `SNAP_GRAVITY_WORK_RADIAL_EXACT=0`) — arms unset/0/1. Off: eps_eff nz^2 in [-0.32,-0.20]. On: |eps_eff nz^2| < 0.04.
    Unset == 0 bitwise. E+PE closes to `EPE_TOL = 1e-12` over `NSTEP = 50` (`tests/test_horizontal_flux_covariance.py:38-40@e894700`).
  - `tests/test_flux_covariance_rows.py` (`test_flux_covariance_rows_python`, env radial=0) — rest `REST_TOL 1e-9`,
    uniform tracer `1e-13`, offset invariance `1e-10`, dry Cartesian limit within `CART_TOL 2e-3`
    (`tests/test_flux_covariance_rows.py:33-39@e894700`).
  - `tests/test_flux_covariance_seams.py` (`test_flux_covariance_seams_python`) — six panels with closed walls; drift of
    each total <= `DRIFT_TOL 1e-12` over 10 steps; the gated rest case <= 1e-9; the on/off difference must exceed
    `DIFF_TOL 1e-13` (`tests/test_flux_covariance_seams.py:33-36@e894700`).
  - `test_wb_ref4_order_python` (on in both arms).
- Limits: study switch, off by default. The covariance seam test is single-process; no MPI run with the term on.


#### 12.7 `SNAP_X1_MASS_COVARIANCE` (x1 mass-flux covariance)
<sub>inventory E: Scheme: `SNAP_X1_MASS_COVARIANCE` (x1 mass-flux covariance)</sub>

- Summary: subtracts dz^2/12 rho_1 w_1 / rho from the velocity handed to the x1 reconstruction, with a one-sided rho_1
  at reflecting walls and an odd-mirror ghost refill. Switch: env `SNAP_X1_MASS_COVARIANCE`, default **off**.
- Derivations: summary-level only in `docs/derivations/curved-gravity-work-weight.md@e894700` sec 11.4 (the expansion
  is stated; its "ONSET PLACEHOLDER" is unfilled). Re-derive from `src/hydro/hydro_forward.cpp:315-343@e894700` with an
  executable check.
- Figures: a stratified cell showing m1/rho vs the cell average of w, and the dz^2/12 rho_z w_z face mass excess.
- Code: `src/hydro/hydro_forward.cpp:39-48@dae902b` — static `x1_mass_covariance()` — read once;
  `src/hydro/hydro_forward.cpp:315-343@e894700` — applied inside the well-balanced x1 branch (`wb_x1`, `:271`:
  grav1 != 0, IPR present, EOS not shallow-water); velocity restored after reconstruction (`:361`).
- Couplings: acts only when the well-balanced x1 path is active.
- Tests: **none** (not referenced in `tests/` or `tests/CMakeLists.txt`).
- Limits: untested, and its onset effect is unmeasured (placeholder in the derivation).


#### 12.8 `SNAP_GRAVITY_WORK_RADIAL_EXACT` (option F: corrected-PE gravity work)
<sub>inventory E: Scheme: `SNAP_GRAVITY_WORK_RADIAL_EXACT` (option F: corrected-PE gravity work)</sub>

- Summary: with `gravity-work: face`, adds g1 sigma^2 s[drho] to each cell's x1 gravity work so that E + P is conserved,
  where P = sum V[rho phi(x1v) - g1 sigma^2 s[rho]]. It is also booked inside the VIC operator and logged as `pe=`.
  Switch: env `SNAP_GRAVITY_WORK_RADIAL_EXACT`, default **on** (acts only with `gravity-work: face`).
- Derivations: exists: `docs/derivations/curved-gravity-work-weight.md@e894700` secs 7-8 (option F), 10 (every PE site),
  11.2 (why default on); checked by `docs/derivations/curved_gravity_work_weight.py`, `optionF_replica.py@e894700`.
  Older copy in `sources/deriv__curved-gravity-work-weight.md` (from 6499404, lacks the seam-limit paragraph).
- Figures: (1) a cell with sigma^2 = <(x1-x1v)^2> and the 3-point slope stencil, one-sided at block ends; (2) the
  booking split between the implicit matrix row and the post-solve term.
- Code:
  - `src/hydro/hydro.cpp:241-251@e894700` — `HydroImpl::gravity_work_radial_exact()` — read once.
  - `src/hydro/hydro.cpp:253-259@e894700` — `radial_exact_work()` — on, grav1 != 0, `gravity-work: face`, grid
    `cartesian` or `spherical-polar`.
  - `src/hydro/hydro.cpp:83-92@e894700` — `reset()` — `TORCH_WARN_ONCE` for other grids ("has no form on a '...' grid: the
    x1 wall cells keep the first-order plain face work").
  - `src/hydro/hydro_forward.cpp:817-822@e894700` — explicit work; the cp3/cp5/weno5 curvature flux is skipped when on
    (`:838`).
  - `src/implicit/implicit_hydro.cpp:288,301-344,451-460@e894700` — `ImplicitHydroImpl::forward_masked` — the matrix
    coupling and post-solve remainder.
  - `src/hydro/gravity_work_radial.hpp:13,28,57@e894700` — `x1_variance`, `centroid_slope`, `corrected_pe_work`.
  - `src/mesh/meshblock.cpp:1050-1055@e894700` — `print_cycle_diagnostics` — logs P instead of PE_d.
- Couplings: inert with `gravity-work: cell` (the default) or `face-wallc`. It never meets the fixer, which requires
  `cell`. On gnomonic-equiangle it warns and keeps the plain face work. At an x1 block seam the slope is one-sided, so
  a split column conserves its own P and differs from one block (by design; `tests/test_x1_seam_split.cpp:12-16@e894700`).
  With it on, `gravity_work_defect()` and every E+PE_d oracle measure the wrong invariant (`src/hydro/hydro.hpp:174-177@e894700`).
- Tests:
  - `tests/test_gravity_work_radial_exact.py` (`test_gravity_work_radial_exact_python`, `_cuda_python`) — arms unset/0/1:
    unset == 1 bitwise; per-step |d(E+P)|/|E+P| <= `EP_TOL 1e-14`; logged `ie=`+`pe=` agrees to `DIAG_TOL 1e-11`
    (`tests/test_gravity_work_radial_exact.py:51-53@e894700`); a gnomonic block warns when on and is silent when off; plus
    VIC clamp and immersed-solid arms.
  - `test_implicit_face_work_operator_python` (env `=0`) and `..._radial_exact_python` (env `=1`)
    (`tests/CMakeLists.txt:235-240,275-277@e894700`) — `W_TOL 1e-7` m/s at rest, `EPE_TOL 1e-11`
    (`tests/test_implicit_face_work_operator.py:40-41@e894700`), measured on E+P when on.
  - `test_implicit_stratified_solid_python` (`=0`) / `..._radial_exact_python` (`=1`).
  - `test_implicit_gravity_tall_column_python` — runs both arms itself: rung `W_TOL 1e-7`, settled `1e-10`, on <= 1.1x off
    (`tests/test_implicit_gravity_tall_column.py:31-33@e894700`).
  - `test_x1_seam_split_radial_exact.<b>` / `_radial_exact_off.<b>` (+`_cuda`) and `test_x1_seam_split_mp_radial_exact[_off]`
    — print the split gap; when on, split E+P drift <= 1e-13 (`tests/test_x1_seam_split.cpp:247-260@e894700`).
  - Forced off for the plain-face-work oracles: `test_forcing.<b>`, `test_gravity_work_fixer_python`,
    `test_horizontal_flux_covariance_python`, `test_flux_covariance_rows_python` (`tests/CMakeLists.txt:270-273@e894700`).
- Limits: the seam split differs from one block at O(h^4). Gnomonic grids keep the first-order wall-cell work.
  The convergence-table placeholder in sec 11.3 is unfilled.
- Discrepancies: **the task brief says radial-exact "fails at setup on unsupported grids". At dae902b it does not
  fail: it warns once (`TORCH_WARN_ONCE`, `src/hydro/hydro.cpp:87@e894700`) and falls back to the plain face work.**
  The test asserts the warning, not an error (`tests/test_gravity_work_radial_exact.py:382@e894700`). The code wins.


#### 12.9 runtime environment for layout/communication
<sub>inventory E: Scheme: runtime environment for layout/communication</sub>

| Var | Default | Read at | Role |
|---|---|---|---|
| `BACKEND` | `default_backend()` (ucx if built with UCX and not Darwin, else gloo) | `src/layout/layout.cpp:190,237@e894700` | process-group backend; the YAML `distribute/backend` key is accepted but dead (`src/layout/layout.cpp:229-231@e894700`) |
| `PROCESS_RANK`, `PROCESS_WORLD_SIZE`, `RANK`, `WORLD_SIZE`, `LOCAL_RANK` | `RANK` / `WORLD_SIZE` / 0 | `src/layout/layout.cpp:194-214@e894700`; `src/layout/layout.hpp:44-50@e894700` | torchrun ranks |
| `MASTER_ADDR`, `MASTER_PORT` | 127.0.0.1; random port only if single-process | `src/layout/layout.cpp:200-211@e894700` | a multi-process run without `MASTER_PORT` is a `TORCH_CHECK` error |
| `DEVICE`, `DEVICE_ID` | `cpu`, -1 | `src/layout/layout.cpp:217-218,238@e894700` | device selection |
| `COMMUX_COALESCE`, `COMMUX_GROUP`, `UCX_TLS` | set to 1, 1, `^cuda_copy,cuda_ipc,gdr_copy` (CPU) only if unset | `src/layout/process_group_ucx.cpp:26-29@e894700` | UCX tuning defaults |
| `WORKSPACE`, `NC_HOME` | cwd, none | `setup.py:42,62@e894700` | Python package build only |
- Tests: `test_process_group.<b>` (backend default, BACKEND env overrides YAML, MASTER_PORT rules;
  `tests/test_process_group.cpp:74-186@e894700`); `test_exchange_ucx` (`BACKEND=ucx`), `test_parentless_cloud_nb1_mp_gloo`
  (`BACKEND=gloo`), `test_sedimentation_cubed_seam_gloo` (`run_seam_backends.py`, `BACKEND` per run).


#### 12.10 test-harness environment variables (not read by `src/`)
<sub>inventory E: Scheme: test-harness environment variables (not read by `src/`)</sub>

| Var | Reader | Purpose |
|---|---|---|
| `SNAPY_BUILD_CUDA` | set to 0 on non-CUDA builds (`tests/CMakeLists.txt:520-521@e894700`); read by python tests, e.g. `tests/test_gravity_work_fixer.py:179@e894700` | skip (exit 125) CUDA arms |
| `GTEST_FILTER` | `seam_arm` (`tests/CMakeLists.txt:38-46@e894700`) | one gtest per ctest arm; `PASS_REGULAR_EXPRESSION "[  PASSED  ] 1 test."` makes an empty filter or a skip fail |
| `BLOCKS_PER_PROCESS`, `EXPECT_LOCAL_NEIGHBOR`, `EXPECT_REMOTE_NEIGHBOR` | `tests/test_exchange.cpp:222,303-304@e894700` | exchange topology (`tests/CMakeLists.txt:164-165,186-189@e894700`) |
| `SNAPY_RUN_HYDRO` | `tests/test_uranus_cycle1_abort.cpp:47@e894700` | path to `run_hydro.<b>` |
| `WB_REF_WALL_DUMP`, `WB_REF_WALL_BETAS` | `tests/test_wb_ref_wall.cpp:159,193@e894700` | review/scan aids |


### 12.3 YAML scheme keys


#### 12.11 YAML scheme keys (run-time)
<sub>inventory E: Scheme: YAML scheme keys (run-time)</sub>

- Summary: keys that select a numerical scheme. Unknown keys are refused by `check_keys` (`src/input/check_keys.cpp:12@e894700`).
  Python construction (`ConstGravityOptions.gravity_work()`, `.gravity_work_fixer()`, `HydroOptions.wb_wall_clamp`;
  `python/csrc/pyforcing.cpp:28-29@e894700`, `python/csrc/pyhydro.cpp:34@e894700`) bypasses YAML. For that reason the
  gravity-work checks are repeated in `HydroImpl::reset()`.

| Key | Default | Parse | Consumer / couplings |
|---|---|---|---|
| `forcing/const-gravity/gravity-work` | `cell` (C++ default `src/forcing/forcing.hpp:58@e894700`) | `src/forcing/const_gravity.cpp:28-34@e894700` (cell, face-wallc, face) | re-validated at `src/hydro/hydro.cpp:58@e894700`; `gw_cell` at `src/hydro/hydro_forward.cpp:230@e894700`; face-wallc zeroes wall-cell correction `:902-906`; face with implicit and no in-operator work triggers `TORCH_WARN` (#283) at `src/hydro/hydro.cpp:118-127@e894700`; face work inside the implicit operator iff scheme != 0 (`src/hydro/hydro.cpp:305-309@e894700`) |
| `forcing/const-gravity/gravity-work-fixer` | = (gravity-work == cell) | `src/forcing/const_gravity.cpp:36-41@e894700` (set true with non-cell and grav1 != 0 is an error) | forced false for non-cell (`src/hydro/hydro.cpp:64@e894700`); needs grav2 = grav3 = 0 (`:65-68`) and non-periodic x1 (`:72-81`); active iff grav1 != 0 and cell (`src/hydro/hydro.cpp:211-215@e894700`) |
| `forcing/const-gravity/grav1,2,3`, `non-hydrostatic` | 0, 0, 0, 1 (in [0,1]) | `src/forcing/const_gravity.cpp:22-26@e894700` | zeroed by `disable-flux-xN` (`src/hydro/hydro_options.cpp:80-82@e894700`) |
| `dynamics/wb-wall-clamp` | true | `src/hydro/hydro_options.cpp:57@e894700` | x1 reference kernel `src/hydro/hydro.cpp:554-556@e894700`; `balance_column` refuses false (`src/hydro/balance_column.cpp:30-33@e894700`); bryan `balance-ic` needs it (`examples/bryan.cpp:227@e894700`) |
| `dynamics/disable-flux-x1/x2/x3`, `verbose` | false | `src/hydro/hydro_options.cpp:53-56@e894700` | gates the p* source per direction |
| `dynamics/equation-of-state/type` | `moist-mixture` | `src/eos/equation_of_state.cpp:57@e894700` | shallow-water disables the WB x1 path (`src/hydro/hydro_forward.cpp:262-263@e894700`) |
| `.../limiter` | false | `src/eos/equation_of_state.cpp:74@e894700` | flux-positivity limiter and meters (`src/hydro/hydro_forward.cpp:648@e894700`) |
| `.../density-floor`, `pressure-floor`, `temperature-floor` | 1e-6, 1e-3, 20 | `src/eos/equation_of_state.cpp:65-72@e894700` | floors / redo |
| `dynamics/reconstruct/{vertical,horizontal}/type,scale,shock` | dc, false, false | `src/recon/reconstruct.cpp:33-36@e894700` | cp3/cp5/weno5 enable the curvature flux in face work (`src/hydro/hydro_forward.cpp:829-830@e894700`) |
| `dynamics/riemann-solver/type,dir` | roe, omni | `src/riemann/riemann_solver.cpp:26-27@e894700` | none |
| `integration/implicit-scheme` | absent = explicit; 0 == absent | `src/implicit/implicit_hydro.cpp:35,71-82@e894700` | only 0/1/9 accepted (`ImplicitOptionsImpl::type()`, `:84-98`) |
| `integration/implicit-advection-cfl`, `shear-cfl` | 1.0, 0.0 | `src/implicit/implicit_hydro.cpp:59-67@e894700` | error if set without implicit-scheme (`:37-40`) |
| `geometry/cells/nghost` | 1 | `src/coord/coordinate.cpp:164@e894700` | >=3 required by WB_REF4 / X1_CENTROID when grav1 != 0 |
| `geometry/type` | cartesian | `src/coord/coordinate.cpp:71@e894700` | radial-exact acts on cartesian/spherical-polar only; X1_CENTROID acts on spherical-polar only |
| `distribute/layout, nb1, nb2, nb3` | slab, 1, 1, 1 | `src/layout/layout.cpp:233-236@e894700` | x1 split makes the seam exchanges live |
| `boundary-condition/external/x?-inner/outer` | reflecting | `src/mesh/meshblock_options.cpp:100-193@e894700` | periodic x1 refused with the fixer |
| `forcing/fric-heat` | removed | refused at `src/hydro/hydro_options.cpp:68-72@e894700` | none |
- Tests: `test_yaml_keys.<b>` (every block refuses an unknown key; `tests/test_yaml_keys.cpp:63-186@e894700`);
  `test_hydro_options.<b>` (dynamics/eos/forcing keys, `wb_wall_clamp_ships_enabled`, scheme outside {0,1,9} refused;
  `tests/test_hydro_options.cpp:22-364@e894700`); `test_implicit_cfl.<b>`; `test_implicit_options_type_python`;
  `test_gravity_work_fixer_python` (fixer guards, face-wallc, Python keys).


### 12.12 Coverage matrix


#### 12.12 Coverage matrix (switch combination -> ctest entries)
<sub>inventory E: Coverage matrix (switch combination -> ctest entries)</sub>

Notation: WB = `SNAP_WB_REF4`, XC = `SNAP_X1_CENTROID_EXACT` (implies WB), FC = `SNAP_FLUX_COVARIANCE`,
MC = `SNAP_X1_MASS_COVARIANCE`, RE = `SNAP_GRAVITY_WORK_RADIAL_EXACT` (effective only with gravity-work face).
"int" = the script runs the arms in child processes; "ctest env" = `ENVIRONMENT` in `tests/CMakeLists.txt`.

| Combination | gravity-work | grid | ctest entries |
|---|---|---|---|
| all defaults (WB/XC/FC/MC off, RE default on) | cell+fixer | any | every entry not listed below, incl. all examples (no example sets `gravity-work`) |
| defaults, RE on (default) | face | cart/sph | `test_lu_failure.<b>`, `test_gravity_work_radial_exact_python` (int: unset/0/1), `test_implicit_gravity_tall_column_python` (int: 0/1) |
| RE=0 (ctest env) | face (and cell arms) | cart/sph | `test_forcing.<b>`, `test_gravity_work_fixer_python`, `test_horizontal_flux_covariance_python`, `test_flux_covariance_rows_python`, `test_implicit_face_work_operator_python`, `test_implicit_stratified_solid_python`, `test_x1_seam_split_radial_exact_off.<b>` (+`_cuda`), `test_x1_seam_split_mp_radial_exact_off` |
| RE=1 (ctest env) | face | cart/sph (+gnomonic warn) | `test_implicit_face_work_operator_radial_exact_python`, `test_implicit_stratified_solid_radial_exact_python`, `test_x1_seam_split_radial_exact.<b>` (+`_cuda`), `test_x1_seam_split_mp_radial_exact` |
| WB=1 | cell | cart | `test_balance_column_wb_ref4.<b>`, `test_face_floor_wb_ref4.<b>`, `test_x1_seam_split_wb_ref4.<b>` (+`_cuda`), `test_x1_seam_split_wb_ref4_gravity_0.<b>`, `test_x1_seam_split_mp_wb_ref4` |
| WB on/off (int) + FC=1 + RE on | face | cart | `test_wb_ref4_order_python` (+`_cuda_python`) |
| XC=1 (=> WB) | cell | sph (seam), cart (balance/face-floor) | `test_balance_column_x1_centroid.<b>`, `test_face_floor_x1_centroid.<b>`, `test_x1_seam_split_x1_centroid.<b>` (+`_cuda`), `test_x1_seam_split_mp_x1_centroid` |
| XC on/off (int), implicit 0/1, nh 1/0 | cell (default) | sph | `test_x1_centroid_rest_python` (+`_cuda_python`) |
| FC on/off (int) + RE=0 | face | cart | `test_horizontal_flux_covariance_python` (int unset/0/1) |
| FC on/off (int) + RE=0 | default and face | sph, gnomonic, cart | `test_flux_covariance_rows_python` |
| FC on/off (int) | cell+fixer | gnomonic (6 panels), sph | `test_flux_covariance_seams_python` |
| all off, nghost 1 | cell | sph | `test_x1_seam_split.<b>` (only `switches_off_nghost_1_sets_up`), `test_x1_seam_split_mp.<b>` |
| MC=1 | any | any | **none** |

Gaps (no entry): MC in any form; XC with `gravity-work: face` (and so XC with RE on); XC with FC; WB/XC on a gnomonic grid;
WB with RE=0 under face work; FC across MPI ranks; all three study switches together (WB+FC+RE is covered only by
`test_wb_ref4_order`). Python construction of gravity-work options is covered by `test_gravity_work_fixer_python`.


---

<a id="ch13"></a>
## Chapter 13. Conservation budgets and diagnostics

What the cycle line logs and what each term means (the logged potential energy is $P$ under D), the positivity and VIC-clamp meters, the gravity-work fixer budget, redo causes and termination status as diagnostics, the output-field diagnostics, and the mass-conservation regression checks. `src/diagnostics/` is legacy code that is not compiled and is not described.

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: what snapy measures and prints about its own conservation, and the regression checks that read it. That
covers the cycle line (`mass0=`, `masst=`, `ke=`, `ie=`/`energy=`, `pe=`), the run-to-date meters (`limcut=`,
`thetamin=`, `thetasevere=`, `vicclamp=`, `fixgrav=`), the gravity-work-fixer E+PE budget (D, wall mass, deposit), the
redo cause flags and the termination status, and the output-field diagnostics (`div`, `div_h`, `curl`, `ic_*`).
**Note:** `src/diagnostics/` is legacy Athena++/canoe code (it includes `athena/parameter_input.hpp`). It is not in
the library glob (`src/CMakeLists.txt:35-52@e894700` lists no `diagnostics/*.cpp`), so it is not compiled. The chapter
must say this, and must not describe it as live. The live diagnostics are in `src/mesh/meshblock.cpp` and
`src/output/load_diag_output_data.cpp`. **Recommendation:** keep the chapter. Move the redo/acceptance mechanics to
Ch.7 and keep only "what the cause flags report" here. Cross-reference the fixer physics to Ch.6, which owns the
derivation; this chapter owns the budget bookkeeping and its printout.

</details>


#### 13.1 cycle-line budget (`print_cycle_diagnostics`)
<sub>inventory E: Scheme: cycle-line budget (`print_cycle_diagnostics`)</sub>

- Summary: every `ncycle_out` cycles, one line sums the interior conserved state times cell volume over all local
  blocks, reduces it to the root rank, and prints it. Switch: `integration/ncycle_out` (parsed by pyharp; 0 disables,
  `src/mesh/meshblock.cpp:1010-1012@e894700`).
- Terms (each a volume integral over interior cells):
  - `mass0=` sum u[IDN] V (dry density); `masst=` sum (u[IDN] + sum_n u[ICY+n]) V, printed if species exist
    (`src/mesh/meshblock.cpp:1091-1096@e894700`).
  - `ke=` sum 0.5 m_i m^i / rho_total V. The momentum is raised with the metric (`coord_vec_raise_` with
    `cosine_cell_kj`) and the density is the total over all constituents. It is read from `hydro_u`, never from the
    stage-stale `hydro_w` (`src/mesh/meshblock.cpp:1038-1044@e894700`).
  - `ie=` (MeshBlock line) / `energy=` (Mesh line) = sum u[IPR] V, the total energy E (`:1098-1099`; labels set at
    `src/mesh/meshblock.cpp:1114-1118@e894700` and `src/mesh/mesh.cpp:409-419@e894700`, precision max_digits10-4 vs -3).
  - `pe=` sum rho_total(-g1 x1v) V, printed only with const-gravity grav1 != 0. When `radial_exact_work()` it logs the
    corrected P = PE_d - sum V g1 sigma^2 s[rho], so `ie=`+`pe=` is the conserved E+P (`src/mesh/meshblock.cpp:1045-1056,1100@e894700`).
- Derivations: ke with a non-orthogonal metric: re-derive from `src/mesh/meshblock.cpp:1038-1044@e894700` (the test
  states the closed form 13/0.75 vs 25, `tests/test_cycle_diagnostics.cpp:209-212@e894700`). The P form: exists:
  `docs/derivations/curved-gravity-work-weight.md@e894700` sec 7 and sec 10 (PE-site table).
- Figures: (1) annotate one cycle line, mapping each token to its integral and reduction op (SUM/MIN/MAX); (2) a
  Mesh with two local blocks on two ranks: local sums, then one reduce to root, then one line.
- Code: `src/mesh/meshblock.cpp:1004-1112@e894700` — `print_cycle_diagnostics`; reductions at `:1074-1086`;
  `src/mesh/cycle_diagnostics.hpp:11-14@e894700`; `src/mesh/mesh.cpp:409-419@e894700` — `MeshImpl::print_cycle_info`.
- Tests: `test_cycle_diagnostics.<b>` — `logged_ke_scales_with_density` (2x within 1e-9 rel), `logged_ke_reads_the_conserved_state`
  (4x), `logged_ke_sums_the_constituents` (1.25x for a dry-only denominator), `logged_ke_raises_the_momentum_with_the_metric`
  (13/18.75), `logged_pe_is_the_column_geopotential` (2.5*10*zvol within 1e-9), `mesh_aggregates_all_local_blocks_once`
  (1e-11, one `cycle=` line) (`tests/test_cycle_diagnostics.cpp:72-407@e894700`); `test_cycle_diagnostics_parallel.<b>`
  (2 ranks x 2 blocks, 1e-11; `tests/test_cycle_diagnostics_parallel.cpp:25@e894700`); `test_gravity_work_radial_exact_python`
  check 5 (`ie=`+`pe=` = E+P on, E+PE_d off, to `DIAG_TOL 1e-11`); `test_restart_cycle_limit` (the restart leg's
  `time`, `dt`, `mass0`, `energy` match the base run to atol 1e-12; `tests/run_restart_cycle_limit.py:186-189@e894700`).
- Limits: the `ke`/`pe` sums ignore immersed-solid masking. "Run-to-date" meters reset on restart (buffers are not in
  the restart file; `sources/gh__PR_BODIES_202-219.md` #217 Limits). `pe=` uses the per-block one-sided slope at x1
  seams (sec 7 seam limit).
- Discrepancies: `sources/gh__PR_BODIES_202-219.md` (#217, Limits) says ke/pe/meters are on the MeshBlock line only and
  that the Mesh line "never printed ke". At dae902b both lines come from the same `print_cycle_diagnostics`
  (`src/mesh/mesh.cpp:417@e894700`) and differ only in the energy label and precision. The PR text is superseded.


#### 13.2 positivity-limiter meters (`limcut`, `thetamin`, `thetasevere`, hits)
<sub>inventory E: Scheme: positivity-limiter meters (`limcut`, `thetamin`, `thetasevere`, hits)</sub>

- Summary: run-to-date counters of the species flux-positivity limiter, accumulated only when
  `equation-of-state/limiter: true` and species exist. Switch: the `limiter` YAML key (default false).
- Terms: hits = count of interior (cell, species) with theta < 1. severe = theta < 0.9 AND withheld mass > round-off
  (4096 ulp float64, 64 ulp float32, times the cell's gas mass). thetamin = run minimum of theta. limcut = sum of the cut
  x1 flux divided by the sum of the offered x1 flux, printed only if the offered flux > 0.
- Derivations: round-off bound rationale: re-derive from `src/hydro/flux_positivity.hpp:10-23@e894700` (constants
  `kPositivityRoundoffUlp = 4096`, `kPositivityRoundoffUlpFloat = 64`) and `src/hydro/hydro_forward.cpp:659-669@e894700`.
- Figures: a settling column showing theta = dx/(dt|vsed|) = 0.5 on five interior faces, with offered vs cut flux bars.
- Code: `src/hydro/hydro_forward.cpp:648-705@e894700` — accumulation in `HydroImpl::forward`; buffers registered at
  `src/hydro/hydro.cpp:187-194@e894700`; printed at `src/mesh/meshblock.cpp:1102-1107@e894700`; scalar module has its own
  hits counter (`src/scalar/scalar.cpp:160,189@e894700`, not printed).
- Tests: `test_cycle_diagnostics.<b>` — `positivity_meters_read_their_hand_computed_values` (thetamin 0.5, severe 5,
  limcut 0.5, to 1e-9 on buffers and 1e-5 on the printed line), `positivity_severe_needs_more_than_roundoff_withheld`,
  `positivity_severe_float32_needs_more_than_roundoff_withheld` (`tests/test_cycle_diagnostics.cpp:269-366@e894700`);
  `meter_group_is_marked_run_to_date` (token order).
- Limits: thetamin/thetasevere print their initial values (1, 0) when the limiter never ran (#217 Limits).


#### 13.3 VIC clamp meter (`vicclamp`)
<sub>inventory E: Scheme: VIC clamp meter (`vicclamp`)</sub>

- Summary: the largest per-cell relative residual between the constituent change and the face transfer M(i)-M(i+1)
  after the implicit availability clamp. It is 0 unclamped and sum(y) when every constituent is starved. Switch:
  printed whenever an implicit scheme is active (`picorr`).
- Code: `src/implicit/implicit_hydro.cpp:360-378@e894700` (dtype-safe floor: float min in float32, 1e-300 in float64);
  accessor `src/implicit/implicit_hydro.hpp:89@e894700`; reduced MAX and printed at `src/mesh/meshblock.cpp:1067-1070,1086,1108@e894700`.
- Derivations: re-derive from `src/implicit/implicit_hydro.cpp:360-378@e894700` (the residual definition and why it
  equals sum(y) for a fully starved face).
- Figures: a 2-cell column with one face; the dry-only transfer under starvation, so each cell misses M sum(y).
- Tests: `test_cycle_diagnostics.<b>` `vicclamp_reads_the_clamped_fraction` (0.03 within 1e-12; < 1e-12 unclamped;
  `tests/test_cycle_diagnostics.cpp:367-405@e894700`); `test_lu_failure.<b>` `float_rest_column_finite_vicclamp`,
  `double_rest_column_finite_vicclamp` (`tests/test_lu_failure.cpp:351-354@e894700`, #294).
- Limits: a run maximum, not per step.


#### 13.4 gravity-work fixer E+PE budget (D, wall mass, `fixgrav`)
<sub>inventory E: Scheme: gravity-work fixer E+PE budget (D, wall mass, `fixgrav`)</sub>

- Summary: with `gravity-work: cell` and the fixer on (the default), each stage measures the dynamics' change of E+PE_d
  (cell work + face work of the extra limiter/sedimentation mass + Phi times the x1 mass divergence + the VIC change).
  The stages are summed with their RK weights into D. After the last stage, one global reduction deposits -D as heat
  uniform per unit mass. `fixgrav=` prints the accepted-step total. Switch: `gravity-work-fixer` (default true with cell).
- Code (budget terms): `gwfix_stage` per stage (`src/hydro/hydro_forward.cpp:860-889@e894700`); implicit part via the `epe`
  lambda before/after the solve (`:957-978`); stage weight cw = w2_s prod_{t>s} w1_t (rk3: 1/6, 1/6, 2/3), accumulated
  into `_gwfix_d` (`:995-1004`); wall-face mass `_gwfix_wall` (`:889-897`); 5-vector of sums {D, sum mV, wall mass, wall-cell
  mass, redo flag} (`src/mesh/meshblock.cpp:844-868@e894700`); deposit dE_i = -D m_i / sum m_j V_j, guarded by
  wall <= 1e3 eps * mwall (`src/mesh/meshblock.cpp:870-911@e894700`, check at `:899`; `fixgrav=` printed at `:1109-1110`). Pending/total accounting: committed
  at the next step's stage 0 or on acceptance, dropped on redo (`src/hydro/hydro.hpp:186-202@e894700`;
  `src/mesh/meshblock.cpp:614,1250,1274@e894700`). Multi-block sum then one allreduce at `src/mesh/mesh.cpp:341-363@e894700`;
  single block at `src/mesh/meshblock.cpp:832-840@e894700`.
- Derivations: exists: `sources/gw__GRAVITY_WORK_TECH_REPORT_draft.md` sec 3.6 (eqs. 3.13-3.15). Its line cites are
  pre-dae902b; re-anchor them. Re-derive the stage weight cw from `src/hydro/hydro_forward.cpp:986-995@e894700`.
- Figures: (1) a per-stage flow: D^s contributions, weighted sum, global allreduce, uniform-per-mass deposit;
  (2) a closed column with sealed walls, the wall-face mass meter and the 1e3 eps bound.
- Tests: `test_gravity_work_fixer_python` — default cell+fixer |d(E+PE)|/|E+PE| <= `TOL 1e-12`
  (`tests/test_gravity_work_fixer.py:38@e894700`), explicit and VIC; fixer off drifts > 100 TOL; refuses outflow,
  periodic, grav2 != 0; float32 run; `fixgrav=` reported. `test_straka_redo` — cfl 1.6 redoes steps with the fixer on and
  reaches tlim (`tests/run_straka_redo.cmake:31@e894700`). `test_forcing.<b>` `implicit_correction_reports_total_energy_delta`
  (`tests/test_forcing.cpp:538@e894700`).
- Limits: refused for open/periodic x1 and grav2/grav3 != 0 (`src/hydro/hydro.cpp:65-81@e894700`). The large-Courant
  wall round-off can exceed the bound (comment at `src/mesh/meshblock.cpp:889-896@e894700`, #285). Not carried across a
  restart.
- Discrepancies: the draft cites `src/mesh/meshblock.cpp:828-835` and `src/hydro/hydro.cpp:177-181` for the reduction
  and the guard. At dae902b these are `src/mesh/meshblock.cpp:832-840` and `src/hydro/hydro.cpp:202-206`.


#### 13.5 redo causes and termination status (diagnostic view)
<sub>inventory E: Scheme: redo causes and termination status (diagnostic view)</sub>

- Summary: the per-step acceptance decision is a 6-bit cause mask (floor, clamp, limiter, nan, saturation, vic-solve),
  allreduced MAX across ranks and printed in "Redoing the step ... (causes: ...)". `finalize` prints the termination
  reason and returns 1 on "Terminating abnormally".
- Code: `src/mesh/meshblock.cpp:1212-1218@e894700` `limiter_hits`; `:1229-1276` `apply_redo` (message `:1236`);
  `:1278-1286` `local_redo_flags`; `:1288-1300` `reduce_redo_flags`; `src/mesh/mesh.cpp:422@e894700`
  `MeshImpl::check_redo`; termination `src/mesh/meshblock.cpp:1127-1140@e894700`.
- Derivations: none (logic).
- Figures: a cause-bit table and the redo loop.
- Tests: `test_check_redo_floor_python`, `test_check_redo_saturation_python` (+cuda), `test_check_redo_parallel.<b>`,
  `test_uranus_cycle1_abort.<b>` (`abnormal_termination_exits_nonzero`), `test_forcing.<b>` limiter-redo cases
  (`tests/test_forcing.cpp:660-848@e894700`), `test_lu_failure.<b>`.
- Limits: Ch.7 owns the mechanics; this chapter only references them.


#### 13.6 output-field diagnostics
<sub>inventory E: Scheme: output-field diagnostics</sub>

- Summary: optional NetCDF fields requested by name in an output block: `div`, `div_h` (horizontal), `curl` (vector in
  3-D, `curl[VEL3]` in 2-D), all under `diagnostics`; `ic_dry`, `ic_mom`, `ic_etot`, `ic_<species>` (implicit
  correction); also `theta`, `rh_*` with `thermo`. Switch: the `outputs/N/variables` list.
- Code: `src/output/load_diag_output_data.cpp:47@e894700` `OutputType::loadDiagOutputData`; div/curl `:166-217`;
  implicit `:220-260`; called from `src/output/output_type.cpp:191@e894700`.
- Derivations: none new (they use `pcoord->divergence`/`curl`, Ch.3).
- Figures: none needed.
- Tests: `test_user_output.<b>` `OutputDiagnostics.*` (virtual potential temperature, divergence of uniform velocity is
  0, Cartesian curl of solid-body rotation, gnomonic finite; `tests/test_user_output.cpp:792-910@e894700`).
- Limits: no PE or budget field is written to NetCDF (`docs/derivations/curved-gravity-work-weight.md@e894700` sec 10
  table).


#### 13.7 mass-conservation regression checks
<sub>inventory E: Scheme: mass-conservation regression checks</sub>

- Summary: tests that assert conservation of mass, species or energy to round-off on specific operators.
- Derivations: none here; each identity is derived in the chapter that owns the operator.
- Figures: a matrix of conserved quantity × operator × test.
- Code: the operators are cited in their chapters; the orphan runner is `tests/run_example_mass_check.py:29@e894700`.
- Tests (all verified to exist):
  - `test_condensate_conservation.<b>` (stoichiometric multi-vapor debit), `test_fix_vapor_volume.<b>` (column vapor mass
    sum rho q V kept on varying V), `test_parentless_cloud.<b>`, `test_parentless_cloud_nb1.<b>`, `test_parentless_cloud_nb1_mp.<b>`
    (+`_gloo`), `test_vapor_column_nb1.<b>` (repairs keep the column mass whatever nb1), `test_wall_saturation.<b>` (energy
    and water preserved, 1e-12).
  - `test_flux_positivity_python` (vapor+cloud total to round-off, 1e-12), `test_flux_positivity_cubedsphere[_moist]_python`
    (`DRIFT_TOL 1e-13`), `test_flux_positivity_carry.<b>` (energy/momentum carried by withheld mass, 1e-12).
  - `test_flux_covariance_seams_python` (mass, vapor, E+PE to 1e-12 across seams), `test_tracer_dry_convention_python`
    (`TOL 1e-12`).
  - `tests/run_example_mass_check.py` — reads `mass0=` from an example run and checks relative drift <= 1e-8
    (`tests/run_example_mass_check.py:29,133-144@e894700`). **Not registered** in `tests/CMakeLists.txt` at dae902b
    (orphan).
- Limits: no registered test checks `mass0=` drift over a full example run (only the orphan script).


---

<a id="ch14"></a>
## Chapter 14. Parallelism, GPU, restart/IO and reproducibility

Split in three: 14.A parallel execution and GPU (launch, backends, message matching, several blocks per process, collectives, GPU execution); 14.B output and restart (NetCDF, PnetCDF, restart files, scheduling, post-processing tools); 14.C reproducibility, the inventory of what is shown bit for bit and what is not.

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: process launch and communication backends, how exchange messages are matched, several blocks per process,
collectives, GPU execution, NetCDF/PnetCDF output and combining, restart files and resume semantics, and an inventory of
every reproducibility claim with its evidence. Recommendation: split into 14a "Parallel and GPU execution" (S14.1-14.6)
and 14b "Output and restart" (S14.7-14.10). Make S14.11 (reproducibility) a short standalone chapter or appendix,
because its claims draw on Ch3 seams, Ch14 and the physics chapters. Cross-reference Ch3 for what ghost values contain.

</details>


### 14.A Parallel execution and GPU


#### 14.1 Launch environment and rendezvous
<sub>inventory A: Scheme 14.1: Launch environment and rendezvous</sub>

- Summary: one OS process per rank, launched by torchrun or `api/pd-run`. Ranks meet at a c10d TCPStore on
  MASTER_ADDR:MASTER_PORT. MASTER_PORT is required when the world size is >1; a single process picks a random port in
  [29500,29600]. Each process holds bpp blocks. Switch: env `RANK`, `WORLD_SIZE`, `PROCESS_RANK`, `PROCESS_WORLD_SIZE`
  (fall back to RANK/WORLD_SIZE), `LOCAL_RANK`, `MASTER_ADDR` (default 127.0.0.1), `MASTER_PORT`, `DEVICE` (default
  cpu), `DEVICE_ID` (default -1 → LOCAL_RANK), `BACKEND`. `pd-run` defaults BACKEND=ucx, DEVICE=cpu.
- Derivations: none.
- Figures: a launch diagram (torchrun → N processes → TCPStore → process group; each process → bpp blocks → device).
- Code: `src/layout/layout.cpp:34@e894700` `random_master_port`; `:189` `LayoutOptionsImpl` constructor (`:205`
  MASTER_PORT check); `src/mesh/mesh.cpp:236-247@e894700` (world_size = process_world_size·bpp, block rank);
  `src/mesh/meshblock_options.cpp:274@e894700` `device_str` ("cuda:" + device_id or local_rank); `api/pd-run`.
- Tests: `tests/test_process_group.cpp` (`test_process_group.release`) — `LayoutOptions.DefaultsToPlatformCommunicationBackend`,
  `UsesBackendEnvironmentVariable`, `IgnoresYamlBackend`, `BackendEnvironmentOverridesYamlBackend`,
  `RandomizesDefaultMasterPortWhenEnvUnset`, `RequiresMasterPortForMultiProcessWhenEnvUnset`,
  `RequiresMasterPortWhenWorldSizeImpliesMultiProcess`, `UsesProvidedMasterPortForMultiProcess`,
  `ProcessGroupContext.SkipsSingleProcessCommunication`.
- Limits / known issues: `pd-run` exports BLOCKS_PER_PROCESS, but `src/` never reads it; only tests do
  (`tests/test_exchange.cpp`).
- Discrepancies: none.


#### 14.2 Communication backends (Gloo, UCX via commux, external PG; no NCCL)
<sub>inventory A: Scheme 14.2: Communication backends (Gloo, UCX via commux, external PG; no NCCL)</sub>

- Summary: `ProcessGroupContext` is cached per (backend, addr, port, rank, size, local_rank).
  - Gloo is CPU-only, takes one tensor per send/recv (refused with a clear message, #240), and has no coalescing.
  - UCX (commux) takes tensor lists, sends CUDA tensors when commux was built with CUDA, and coalesces grouped
    point-to-point ops.
  - An externally created torch.distributed group can be registered (`snapy.distributed.set_process_group`) if its
    backend name equals BACKEND.
  - No NCCL path exists. BACKEND=nccl without an external group throws "Unsupported BACKEND". With an external NCCL
    group, the non-UCX send path would refuse CUDA tensors ("Gloo communication requires CPU tensors"; inferred from
    code).
  Switch: env `BACKEND`. Default `ucx` if built with UCX on Linux, else `gloo` (Darwin is always gloo). CMake
  `UCX` default ON on Linux, OFF on Apple (`CMakeLists.txt:12-18`).
- Derivations: none.
- Figures: a backend capability matrix (device tensors, multi-tensor messages, coalescing, platforms).
- Code: `src/layout/layout.cpp:41@e894700` `default_backend`; `src/layout/process_group.hpp:29@e894700`;
  `src/layout/process_group.cpp:71@e894700` `create` (cache), `:98` `_init` (`:117` TCPStore, `:129` unsupported
  backend), `:148` `send` (`:155` CPU-only, `:158` one tensor), `:166` `recv`, `:184` `allreduce`, `:212`
  `_init_external`, `:236` `_init_gloo`, `:271` `supports_coalescing`, `:287` no-UCX stub;
  `src/layout/process_group_ucx.cpp:22@e894700` `_init_ucx`; `src/layout/distributed.cpp:14@e894700`
  `set_process_group`; `cmake/ucx.cmake` (commux probe).
- Tests:
  - `tests/test_gloo_one_tensor.cpp` (`test_gloo_one_tensor.release`, 2 ranks, APPLE only) — a 2-tensor message is
    refused with the fix text.
  - `test_exchange_ucx` (UCX builds; BACKEND=ucx, bpp 3).
  - `test_exchange_ucx_cuda` (`run_exchange_backend.py --backend ucx --device cuda`; skip 125 without commux-CUDA or
    GPUs).
  - `test_sedimentation_cubed_seam_gloo` (`run_seam_backends.py --compare-ucx`) — the Gloo result line (17 digits) must
    equal UCX's.
  - `test_parentless_cloud_nb1_mp_gloo`.
- Limits / known issues:
  - Maintainer position (#237, #240 comments): Gloo is Mac-only, snapy does not guarantee Gloo, and Linux CI does not run
    Gloo multi-process tests apart from the explicit `_gloo` entries.
  - Gloo with DEVICE=cuda cannot exchange (CPU-only check). Multi-GPU runs need UCX.
  - `cmake/ucx.cmake` carries site-specific UCX hint paths. Do not cite them.
- Discrepancies: none.


#### 14.3 Exchange message matching and in-process copies
<sub>inventory A: Scheme 14.3: Exchange message matching and in-process copies</sub>

- Summary:
  - A sync is serialize → launch → finalize. Remote neighbours get one message per variable; the tag is
    `phyid·1024 + local_block·32 + buffer_id`, plus n·65536 for variable n (the tag must stay < 65536).
  - Same-process neighbours copy buffers directly after a condition-variable rendezvous of all bpp blocks, keyed by
    the sync signature, with CUDA events on GPU.
  - All remote posts in one process are serialised by a mutex.
  - Buffers are cached per sync signature and reused.
  - Block-to-block messages (x1 relays) fold both local indices into the tag (k·65536), so bpp ≤ 16.
  - `gather_x1` uses tags ≥ 1<<24.
  - In-process boards wait at most 5 min.
  Switch: `SyncOptions.phyid` (0..63).
- Derivations: tag non-aliasing: re-derive from `src/layout/layout.hpp:161-170@e894700` and `layout.hpp:272-278`
  (comment).
- Figures: tag bit layout; the rendezvous state machine for the local exchange.
- Code: `src/layout/layout.hpp:163@e894700` `make_comm_tag`; `src/layout/layout.cpp:279@e894700`
  `_prepare_local_exchange`; `:419` `_copy_local_exchange_buffers` (phase filter); `:540` `launch_exchange`; `:548`
  `exchange_remote` (`:576` periodic px==2 order swap, `:622` self-send, `:634` mutex, `:635` coalescing); `:652`
  `exchange_each_var`; `:849` `send_to_block`; `:864` `recv_from_block`; `:924` `post_to_local_block`; `:948`
  `take_from_local_block`; `src/layout/cubed_sphere_layout.cpp:1042@e894700` (cubed-sphere comm mutex).
- Tests: `test_cubed_sphere_exchange.release` `CommTag.rejects_tags_that_collide_with_the_variable_offset`;
  `test_exchange.release` (buffer reuse: data_ptr unchanged on the second sync; ghost correctness; local and remote seen).
- Limits / known issues: a block-local stepping order (not concurrent) deadlocks until the 5-min timeout
  (PR #259 limits).
- Discrepancies: none.


#### 14.4 Several blocks per process and GPU streams
<sub>inventory A: Scheme 14.4: Several blocks per process and GPU streams</sub>

- Summary: a pool of bpp worker threads, each with its own CUDA stream on GPU. The caller's stream is fenced with events
  both ways. Within a process, blocks exchange by direct copy and the x1 relays go through boards. Switch:
  `distribute: blocks_per_process`.
- Derivations: none.
- Figures: same as S1.6.
- Code: `src/mesh/mesh.cpp:47@e894700`, `:82`, `:134`; `src/layout/layout.cpp:279-387@e894700` (CUDA arrival and
  completion events).
- Tests: `test_cubed_sphere_exchange.release` `_cuda` (one stream per block); `tests/test_output_barrier.cpp`
  (`test_output_barrier.release`, 2 ranks × 2 blocks).
- Limits / known issues: PnetCDF requires bpp=1 (`src/output/pnetcdf.cpp:74-79@e894700`).
- Discrepancies: none.


#### 14.5 Collectives and global decisions
<sub>inventory A: Scheme 14.5: Collectives and global decisions</sub>

- Summary: all collectives use small CPU tensors. dt is MIN; redo causes are a MAX over 6 flags; signals are MAX;
  the gravity-work fixer is a SUM of 5 doubles (local blocks summed in a fixed order first). Barriers sit at init, around
  output combines and at finalize. Switch: none.
- Derivations: none.
- Figures: one cycle's collective timeline (dt MIN → fixer SUM at the last stage → redo MAX → output barriers).
- Code: `src/mesh/meshblock.cpp:510-528@e894700` (MIN), `:832-838` (fixer SUM, single block), `:1288` (redo MAX);
  `src/mesh/mesh.cpp:346-355@e894700` (fixer SUM, multi-block); `src/utils/signal_handler.cpp:64@e894700`
  `CheckSignalFlags` (MAX).
- Tests: `test_check_redo_parallel.release`; `tests/test_cycle_diagnostics_parallel.cpp`
  (`test_cycle_diagnostics_parallel.release`).
- Limits / known issues: MIN/MAX are order-independent. The fixer SUM's round-off depends on the number of ranks and
  blocks and on the backend's reduction order, so with the fixer on (default with `gravity-work: cell`) results across
  decompositions can differ in the last bits (inference; not measured in sources).
- Discrepancies: none.


#### 14.6 GPU execution
<sub>inventory A: Scheme 14.6: GPU execution</sub>

- Summary: a block is built on CPU and moved with `block->to(device)` / `mesh->to(device)`. The device is
  `cuda:<DEVICE_ID or LOCAL_RANK>`. Kernels use the CUDA DispatchStubs (S1.9). Host syncs (`.item()`) come from
  meters, redo flags and the fixer. Switch: CMake `CUDA=ON`; env `DEVICE=cuda`, `DEVICE_ID`.
- Derivations: none.
- Figures: the per-step host↔device sync points (from issue #291's counts).
- Code: `src/mesh/meshblock_options.cpp:274@e894700`; `examples/run_hydro.cpp:39-47@e894700`;
  `src/recon/recon_dispatch.cu:18@e894700` (tiling for lines >1024); `tests/cuda_test_gate.hpp` (a CPU build never
  enters CUDA tests).
- Tests: CUDA twins: `test_weno5_cuda_line.release`, `test_x1_seam_split_*_cuda`,
  `test_cubed_sphere_exchange.release` `_cuda`, `*_cuda_python` entries (`tests/CMakeLists.txt:277-311`),
  `test_vic_moist_device_python` (CPU vs CUDA, bound 1e-9 per PR #242 text); `test_shallow_splash_ucx_cuda_decomp`
  (FULL_TESTS, ≥2 GPUs).
- Limits / known issues:
  - Issue #291 (open): a step on a small 2-D moist grid costs 1.54× more than on 2.10.9, with 46% more kernels and 33
    `.item()` per step. Launch-bound.
  - `bdot_out` keeps the untiled launcher (S1.9).
- Discrepancies: none.


### 14.B Output and restart


#### 14.7 NetCDF output (per-block files, combine)
<sub>inventory A: Scheme 14.7: NetCDF output (per-block files, combine)</sub>

- Summary: each block writes `<basename>.block<r>.out<fid>.<NNNNN>.nc` (NetCDF-4). Variables are NC_FLOAT by default,
  or NC_DOUBLE with `double_precision: true`. Cubed-sphere panels are laid out on a 3×2 global tile for indexing. After
  the last local block writes, the root process combines all parts with the in-tree `mppnccombine` (a single part is
  renamed). Mirror barriers in a scope guard hold every rank until the combined file exists. Switch: YAML
  `outputs: - {type: netcdf, dt, variables, combine (default true), double_precision (default false),
  include_ghost_zones, x1/x2/x3_slice, output_sumx1..3, cartesian_vector, super-resolution}`; CMake `NETCDF` (default ON).
- Derivations: none.
- Figures: file naming and the combine flow (parts → root mppnccombine → combined file, barrier, barrier).
- Code: `src/output/output_type.cpp:64@e894700` `OutputOptionsImpl::from_yaml`; `src/output/netcdf.cpp:37@e894700`
  `write_output_file` (`:127` nc_create, `:166` cubed-sphere tile offsets, `:194` NC_DOUBLE switch);
  `src/output/combine_netcdf.cpp:27@e894700` `ready_to_combine` (counts local blocks), `:39` `combine_blocks` (`:62`
  barrier, `:70` ReleaseOnExit, `:121` `mppnccombine`); `src/output/mppnccombine.cpp:94@e894700`;
  `python/api/pd_combine.py` (CLI `pd-combine`).
- Tests: `test_user_output.release` — `OutputPrecision.netcdf_double_precision_reads_back_exactly`,
  `netcdf_float_output_keeps_nonfinite`, `yaml_double_precision_defaults_off_and_is_reported`, `OutputSlice.*`,
  `OutputSelection.*`, `OutputStatistics.*`, `SuperResolution.*`; `test_output_barrier.release` — every rank sees the
  complete combined .nc and restart, and no .part is left; `test_netcdf_utils.release` (name sanitising).
- Limits / known issues: the default float output floors relative differences at ~1e-7, so conservation must be read
  from the float64 cycle line (forcing_io report). The `include_ghost_zones` "FIXME" (`netcdf.cpp:72-73`) says it may
  not work for non-CCC grids. The scope-guard error path is untested (PR #213 limits).
- Discrepancies: the forcing_io report says "fifteen nc_def_var sites" and "ten call sites". Its own banner corrects to
  fourteen `as_float` sites; recount at dae902b if quoted.


#### 14.8 PnetCDF output
<sub>inventory A: Scheme 14.8: PnetCDF output</sub>

- Summary: one shared file written collectively through pinc/PnetCDF, NC_FLOAT only (double_precision refused at
  construction), bpp must be 1. Switch: YAML `type: pnetcdf`; CMake `PNETCDF` (default ON on Linux, OFF on Apple;
  needs the Python package `pinc`). Without the build flag the type throws ("requires PNETCDF=ON",
  `meshblock.cpp:214`).
- Derivations: none.
- Figures: none.
- Code: `src/output/pnetcdf.cpp:48@e894700` constructor; `:60` `write_output_file` (`:74-79` bpp check); `cmake/parameters.cmake:28-43@e894700`.
- Tests: none registered (the refusal was exercised by hand in PR #213, single rank).
- Limits / known issues: multi-rank PnetCDF output is not covered by any ctest.
- Discrepancies: none.


#### 14.9 Restart files (write, bundle, read)
<sub>inventory A: Scheme 14.9: Restart files (write, bundle, read)</sub>

- Summary:
  - Every block saves its whole Variables map (ghosts included; `scalar_r` is dropped when `scalar_s`/`hydro_u` are
    present) to CPU with `kintera::save_tensors`. It adds `last_time`, `last_cycle`, the per-output `file_number`,
    `next_time` and `output_key` (N legacy FNV keys + N exact-bit keys).
  - The root bundles the `.part` files into one `<basename>.<NNNNN|final>.restart` (magic `SNAPY_RESTART_BUNDLE_V1`,
    an index, then payloads). A single part is renamed.
  - On read, each block extracts its own `block<rank>` entry, restores the cycle and time, and matches output schedules
    by key, own slot first. File numbers stay positional. A restored `next_time` more than one dt ahead is reset to now.
    New outputs join the dt grid. The scalar primitive is rebuilt from the conserved state.
  - Run-to-date meters (gravity-work fix total, positivity meters) are not carried.
  Switch: YAML output `type: restart` (always combined); driver argument `-r/--restart <file>`.
- Derivations: none (format and bookkeeping). The FNV-1a keys need only a statement.
- Figures: bundle file layout; the schedule-restore decision tree (key match → own slot → first unclaimed → new output).
- Code: `src/output/restart.cpp:24@e894700` `write_output_file` (`:47-61` schedule tensors, `:64-81` name, `:90`
  `save_tensors`); `src/output/combine_restart.cpp:18@e894700` magic, `:35` `make_restart_bundle`, `:76`
  `combine_blocks` (`:95` barrier); `src/input/read_restart_file.cpp:154@e894700` `load_pt_from_bundle`, `:223`
  `load_restart`; `src/mesh/meshblock.cpp:1306@e894700` `_init_from_restart` (`:1343` precise keys, `:1379` positional
  file number, `:1388` dt clamp, `:1400` scalar rebuild); `src/output/output_type.cpp:16@e894700` `schedule_key`,
  `:24` `schedule_key_v2`; `src/hydro/hydro.hpp:187-190@e894700` (meters not carried).
- Tests: `tests/run_restart_multiblock.py` (`test_restart_multiblock`, non-Apple) — straka bpp 2, shallow_xy bpp 4 and
  shallow_splash bpp 6 in one process; the restarted final NetCDF equals the uninterrupted one exactly (max abs diff == 0,
  NetCDF float32 by default). `run_restart_cycle_limit.py` (S1.1); `run_restart_dt_change.py`
  (`test_restart_dt_change`, issue #272); `run_restart_output_schedule.py` (`test_restart_output_schedule`);
  `run_restart_key_collision.py` (`test_restart_key_collision`); `run_restart_inplace_reorder.py`
  (`test_restart_inplace_reorder`, frame md5s unchanged); `test_user_output.release`
  `OutputScheduleKey.precise_cadences_do_not_collide`; `test_output_barrier.release`.
- Limits / known issues:
  - A restart must be read with the same decomposition: a missing `block<rank>` entry gives an empty map and then
    "missing required variable: hydro_u" (`read_restart_file.cpp:219`, `meshblock.cpp:1315`). Issue #138 asked for
    restart across "multiple ways of decomposition". The test covers bpp variation in ONE process at a fixed block
    count, not a change of block count.
  - Issue #277 (open): a resume rewrites its last outputs and restart index.
  - The restart runners launch one process (PR #212 limits). Multi-rank runs of them were by hand.
  - The NetCDF exactness check is in float32 unless the output sets double_precision.
- Discrepancies: PR #212 names `test_restart_new_output` and `test_restart_insert_output`. Neither is registered at
  dae902b; `tests/CMakeLists.txt:415-420` lists cycle_limit, dt_change, output_schedule, key_collision and
  inplace_reorder.


#### 14.10 Output scheduling, statistics and termination
<sub>inventory A: Scheme 14.10: Output scheduling, statistics and termination</sub>

- Summary: each output fires when t ≥ next_time, then next_time += dt and file_number++. With dt=0 it writes every
  cycle. Time-weighted mean/std statistics accumulate between writes. A final write happens at finalize (netcdf skips
  final writes, restart writes `final`). Signals (SIGTERM, SIGINT, SIGALRM wall time) are MAX-reduced and stop the
  run. Switch: output `dt`, `variables` (`*_stat` selection).
- Derivations: time-weighted moments: re-derive from `src/output/output_type.cpp:282-345@e894700`.
- Figures: a schedule timeline across a restart, showing #272 (next_time clamp) and #277 (rewrite).
- Code: `src/mesh/meshblock.cpp:985@e894700`; `src/output/output_type.cpp:297@e894700` `AccumulateStats`;
  `src/utils/signal_handler.cpp:64@e894700`; `src/mesh/meshblock.cpp:1121@e894700` `finalize`.
- Tests: `test_user_output.release` `OutputStatistics.primitive_statistics_are_time_weighted_and_reset`,
  `scalar_statistics_...`.
- Limits / known issues: signals are checked only at `check_redo`. A rank that never reaches it hangs
  (`signal_handler.cpp:65-68` comment).
- Discrepancies: none.


#### 14.11 Combine and inspect tools (post-processing)
<sub>inventory A: Scheme 14.12: Combine and inspect tools (post-processing)</sub>

- Summary: `pd-combine` / `pd-inspect` Python CLIs combine per-block NetCDF (when `combine: false`) and inspect files.
  Switch: CLI.
- Derivations: none.
- Figures: none.
- Code: `python/api/pd_combine.py`, `python/api/pd_inspect.py`, `pyproject.toml` `[project.scripts]`.
- Tests: used by `run_shallow_splash_decomp.py` (skip if missing).
- Limits / known issues: PR #212 notes `pd-combine` globs every leftover `*.out*.nc` in the working directory, so test
  directories must be clean.
- Discrepancies: none.


### 14.C Reproducibility


#### 14.12 Reproducibility and bit-for-bit claims (inventory)
<sub>inventory A: Scheme 14.11: Reproducibility and bit-for-bit claims (inventory)</sub>

- Summary: the claims, the evidence and its scope.
  - (a) Face coordinates are bitwise identical across decompositions. Evidence: `test_coordinate.release`
    `blocks_match_the_undecomposed_grid_bitwise`.
  - (b) Cubed-sphere nb2=1,2,4 give a bitwise identical interior after one stage. Evidence:
    `test_cubed_sphere_exchange.release` (CPU and CUDA, one process). The source report adds every RK stage of one
    cycle, ghosts included, CPU/gloo, bpp=1.
  - (c) Gloo and UCX give an identical result line (17 digits) on the sedimentation cubed seam. Evidence:
    `test_sedimentation_cubed_seam_gloo` (`--compare-ucx`).
  - (d) Restart reproduces the uninterrupted run exactly in float32 NetCDF output, for bpp 2/4/6 in one process.
    Evidence: `test_restart_multiblock`.
  - (e) x2 splits are bitwise; x1 splits are NOT guaranteed bitwise (1e-13 test tolerance). T4 found ≤8e-15 on CPU/gloo
    and bitwise on 2 GPUs/UCX (pre-#259).
  - (f) In-process vs one-block x1 split ≤1e-12 after 200 steps.
  - (g) Run-to-run determinism at a fixed thread count on CPU. The tracer-seam report §21 shows two nodes bitwise over
    14 frames, with pyharp's longwave thread-count dependence noted as an external caveat. Drivers fix torch threads to
    1 (`examples/straka.cpp:111-112`, `python/__init__.py`).
  - (h) Shallow-xy decompositions (single, mesh4, proc2_mesh2, proc4) are compared with max_abs==0 on NetCDF fields.
    Evidence: `test_shallow_xy_decomp` (FULL_TESTS only). shallow_splash is compared to a downloaded reference by L2<50
    (`tests/test_shallow_splash.py`), not bitwise.
  - (i) CPU counters are atomics (`std::atomic` flip count, fix_vapor failures), so no data races in counts (PR #212,
    PR #218).
  Switch: n/a.
- Derivations: none. This is an evidence table.
- Figures: a claims × configuration matrix (decomposition axis, backend, device, bpp, restart), each cell "bitwise /
  tolerance / untested".
- Code: see the cited schemes. Sources of nondeterminism to list:
  - fixer SUM allreduce (S14.5);
  - x1 seam averaging across processes only (`hydro_forward.cpp:448`);
  - kintera/pyharp threading (external);
  - initial conditions using `torch::rand_like` without a seed (`examples/run_hydro.cpp:134-135`);
  - moist-card IC nondeterminism needing `MALLOC_PERTURB_` (PR #220 measurements, `gh__PR_BODIES_220-226.md:786`).
- Tests: as listed in (a)-(h).
- Limits / known issues:
  - No ctest checks bitwise equality across a change of process count at multi-step length for the dynamics.
    `test_exchange_decomp` checks ghost values only.
  - The decomposition-independence evidence for subdivided GPU panels is limited to the one-stage CUDA ctest.
  - The downstream example battery cited in the source reports (determinism cases) lives outside snapy and cannot be
    cited as snapy evidence.
- Discrepancies:
  - The cubed-sphere report says the series moved the production nb2=nb3=1 configuration near panel edges (`8d2ed9b`
    margin change). So bit-identity with older builds does not hold there, while bit-identity across decompositions
    does.
  - PR #213 notes that cubed-sphere NetCDF axis variables changed by 1 float ulp (double rounding removed). A byte
    compare of axes against older files trips on 10 words.


---

<a id="ch15"></a>
## Chapter 15. Verification catalogue

The human-readable index of every ctest entry at the pin, grouped by the chapter that owns the topic, with what each asserts and its tolerance; the examples used as regression. Appendix C (the machine index) is generated from `ctest -N` at the pin so the two cannot drift; 12.12 is the same tests indexed by switch combination.

<details><summary>Research note from the inventory (scope, recommendations)</summary>

Scope: an index of every ctest entry registered by `tests/CMakeLists.txt@e894700`, grouped by the chapter that owns the
topic (chapter numbers from the proposed outline). Each entry gives one line on what it asserts and the tolerance where
it is visible. It also lists the example decks used as regression (straka, bryan, shallow-water, uranus) and the files
that exist but are not registered. **Recommendation:** keep this chapter as the human-readable index. Generate the
appendix test index (Ch.17) from `ctest -N` at the pinned sha, so the two cannot drift. Ch.12.12's switch matrix is the
other view.

</details>


#### 15.1 registration mechanics and labels
<sub>inventory E: Scheme: registration mechanics and labels</sub>

- `setup_test(name)` -> ctest `name.<b>`, a gtest binary, no labels (`cmake/macros/macro_setup_test.cmake:8-34@e894700`).
- `setup_parallel_test(name N)` -> `name.<b>` run by `torchrun --no-python --nproc-per-node=N`
  (`cmake/macros/macro_setup_parallel_test.cmake:8-34@e894700`).
- `snapy_add_python_test(name ...)` -> ctest `name_python`, with labels and timeout, enrolled for `SNAPY_TEST_PYTHONPATH`
  (`tests/CMakeLists.txt:204-221@e894700`).
- Switch arms: `seam_arm` (`:38-46`), `seam_arm_mp` (`:78-83`), the `_wb_ref4`/`_x1_centroid` duplicates (`:93-101`), the
  `_radial_exact` python duplicates (`:232-237`).
- Labels in use: `python`, `boundary`, `exchange`, `ucx`, `gpu`, `cuda`, `cubed-sphere`, `diagnostic`, `forcing`, `eos`,
  `positivity`, `hydro`, `implicit`, `gravity`, `energy`, `mesh`, `redo`, `coordinate`, `scalar`, `reference`,
  `restart`, `examples`, `decomp`, `gloo`, `long`.
- Gates: `if(CUDA)` registrations; `UCX_FOUND`; `APPLE` (`test_gloo_one_tensor` only on Apple, restart tests only on
  non-Apple); `FULL_TESTS`. Non-CUDA builds disable entries with `cuda` in the name or a `cuda`/`gpu` label
  (`tests/CMakeLists.txt:517-536@e894700`). C++ `_cuda` gtest cases inside CPU binaries skip via `snapy_cuda_test_enabled()`.
- CI: Linux runs all registered entries except `test_shallow_xy_decomp`. PRs use FULL_TESTS=OFF; push/manual runs on
  Linux use ON (`.github/workflows/ci.yml:87,105-113@e894700`). macOS PRs run only `test_eos`, `test_plm`,
  `test_gloo_one_tensor`, `test_python_import_path_python`.
- Figures: a tree from the CMake option set to the registered and enabled entries.


#### 15.2 Ch.2 Equations and thermodynamics (EOS)
<sub>inventory E: Scheme: Ch.2 Equations and thermodynamics (EOS)</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_eos.<b>` | fix_vapor limiter accepts zero column, repairs bottom from above, rejects net-deficit/single-cell without writing; moist-mixture and ideal-moist energy offsets; ideal-gas offset is zero; prim2cons with 5 clouds | 1e-14 typical |
| `test_eos_temp2inteng_python` | "UT->I" == "W->I" over a T sweep; ie(T) affine with intercept u0 | rtol 1e-12 |
| `test_eos_species_registry_python` | a block's EOS ignores later rewrites of kintera's global species tables (compute and a full step bitwise) | 1e-14 |
| `test_two_cards_species.<b>` | a block keeps card A's species/parents after card B loads (limiter, sedvel; with controls) | exact |
| `test_cloud_parent_slots.<b>` | nucleation parent found when the card has unused species; a negative cloud borrows from its parent | exact |
| `test_condensate_conservation.<b>` | a multi-vapor condensate debits stoichiometric mass | exact |
| `test_hydro_options.<b>` (EOS part) | every EOS key accepted and read; bad `uv-solver` refused by kintera | n/a |


#### 15.3 Ch.3 Grids and geometry
<sub>inventory E: Scheme: Ch.3 Grids and geometry</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_coordinate.<b>` | gnomonic area/volume, spherical-polar vs Athena formulas, vector lower/raise, contravariant transforms, flux projections, radial source uses face pressure; programmatic/decomposed coordinates match the global grid bitwise | 1e-15 to 1e-14 |
| `test_radial_face_moments.<b>` | curved x1 face centroid shift and second moment equal the exact rationals (#289) | 1e-14 |
| `test_cubed_sphere_cell_volume_python` | six panels sum to 4/3 pi (ro^3-ri^3); discrete div(r rhat) = 3; rest run | 1e-12; `REST_TOL 1e-6` |
| `test_cubed_sphere_exchange.<b>` | subdivided-panel exchange equals one block (nb2 = 1, 2, 4); comm tag collision refused | exact |
| `test_local_horizontal_cells_python` | `set_local_horizontal_cells` leaves every axis resolved | 1e-12 |
| `test_refine.<b>` | refine functions | n/a |


#### 15.4 Ch.4 Spatial discretization
<sub>inventory E: Scheme: Ch.4 Spatial discretization</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_plm.<b>` | PLM interpolation (torch 1/2/3), round-off slopes finite, constant field preserved | exact |
| `test_weno.<b>` | cp5, weno3, weno5 point and torch variants | exact/ref values |
| `test_weno5_cuda_line.<b>` (CUDA only) | lines > 1024 cells (tiled path) equal CPU | 1e-12 |
| `test_riemann.<b>` | hllc, lmars, roe (and roe ideal-moist) write face-pressure output | n/a |
| `test_horizontal_flux_covariance_python` | see Ch.12 FC | -0.32..-0.20 / 0.04 / 1e-12 |
| `test_flux_covariance_rows_python` | see Ch.12 FC | 1e-9 / 1e-13 / 1e-10 / 2e-3 |
| `test_flux_covariance_seams_python` | see Ch.12 FC | 1e-12 / 1e-9 / 1e-13 |
| `test_scalar.<b>` | scalar init and transport; upper bound holds both sides | exact |


#### 15.5 Ch.5 Hydrostatic and well-balanced treatment
<sub>inventory E: Scheme: Ch.5 Hydrostatic and well-balanced treatment</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_hydro_ref_x1.<b>` | CPU dispatch == tensor reference; with the wall clamp, ghosts do not reach the interior (and do without it); thin block; CUDA == CPU | 1e-14 |
| `test_balance_column.<b>`, `_wb_ref4`, `_x1_centroid` | ghost-free column reproduces the block's reference; marched column comes to rest; fixed point; refuses short/unclamped/negative-g/unconverged; switch predicates | 1e-14 |
| `test_wb_ref_wall.<b>` | default reference: wall-adjacent faces are 2nd order (observed order >= 1.7, nz 32 -> 64); CUDA == CPU | 1e-13 |
| `test_wb_ref4_order_python` (+cuda) | see Ch.12 WB | `ORDER_ON 2.75`, `ORDER_OFF 2.5` |
| `test_x1_centroid_rest_python` (+cuda) | see Ch.12 XC | `TOL_ON 1e-10`, `TOL_OFF 1e-8` |
| `test_pref_local_seam.<b>` | the in-process x1 split restarts p_ref at the seam correctly; split == one block after 200 steps | 1e-6 / 1e-12 |
| `test_face_floor.<b>`, `_wb_ref4`, `_x1_centroid` | positivity face floor uses the adjacent density; unresolved column pinned flux | 2.83191e-8 +- 1e-5 rel |
| `test_hydrostatic.<b>` | cubed-sphere hydrostatic atmosphere stays at rest | 1e-8 |
| `test_wb_wall_corner.<b>` | uniform-in-x2 rest column keeps u2 = 0 (stock and user-named wall); x2 split == one block; scalar corner prim == cons | 1e-12 |
| `test_x1_seam_split*.<b>`, `test_x1_seam_split_mp*` | see Ch.12 matrix | 1e-13 |
| `test_bryan_balance_ic` | bryan `balance-ic`: passes = 1 fails with the cap error; default converges; the dry case does not enter the moist loop (`tests/run_bryan_balance_ic.cmake:27-61@e894700`) | TIMEOUT 21 s |


#### 15.6 Ch.6 Gravity and energy
<sub>inventory E: Scheme: Ch.6 Gravity and energy</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_gravity_work_fixer_python` (RE=0) | E+PE per form; fixer guards | `TOL 1e-12` |
| `test_gravity_work_radial_exact_python` (+cuda) | E+P per step, bitwise default, diag, gnomonic warning, VIC clamp, solid | `EP_TOL 1e-14`, `DIAG_TOL 1e-11` |
| `test_implicit_face_work_operator_python` (RE=0), `_radial_exact_python` (RE=1) | #283 tall column at Courant 65.6/197/657, vic-full and vic-partial: finite, E+PE (or E+P) drift, rest w | `EPE_TOL 1e-11`, `W_TOL 1e-7` m/s |
| `test_implicit_stratified_solid_python` (RE=0), `_radial_exact_python` (RE=1) | tall columns, solid-wall mass closure, clamped face-work energy | 1e-12; `EPE_TOL` |
| `test_implicit_gravity_tall_column_python` | 11.3H column at rest through vertical acoustic Courant up to 250, Cartesian and spherical, RE 0 and 1 | `W_TOL 1e-7`, `W_SETTLED 1e-10`, `ON_OFF 1.1` |
| `test_implicit_face_work_jacobian.<b>` | full/partial energy rows equal the frozen Roe flux; cell work includes Roe mass diffusion; curved metrics | 1e-5 |
| `test_forcing.<b>` (RE=0) gravity cases | vertical gravity work uses the continuity mass flux, includes sedimentation, excludes horizontal divergence, removes the curvature excess; implicit gravity work under rk3 stage weights | 1e-12 / 1e-9 |
| `test_straka_redo` | straka_single at cfl 1.6 to t = 60 s: exits 0 and prints "Redoing the step" | TIMEOUT 600 |


#### 15.7 Ch.7 Time integration (RK3, VIC, LU, CFL, redo)
<sub>inventory E: Scheme: Ch.7 Time integration (RK3, VIC, LU, CFL, redo)</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_implicit_cfl.<b>` | implicit CFL keys reject non-numeric values, keep ranges | n/a |
| `test_implicit_advection_cfl_python` | an implicit direction keeps its advective dt bound | 1e-12 / 1e-3 |
| `test_shear_cfl_python` | shear bound shear_cfl * cs_f dx_h / (\|v_h(i)\|\|v_h(i+1)\|) | 1e-9 |
| `test_implicit_options_type_python` | `ImplicitOptions.type()` names the scheme and is read-only | n/a |
| `test_backward_substitution.<b>` | VIC flux decomposition and redistribution conserve the constituent columns; drained donor stays >= 0 (float and double) | 1e-12 |
| `test_lu_failure.<b>` | LU pivot rejection (float/double, 3/5), retry/stop restores the step (CPU, CUDA), mesh-wide restore, finite vicclamp | exact flags |
| `test_vic_moist_device_python` (CUDA only) | schemes 1 and 9 differ from 0; CPU == CUDA | `DEVICE_TOL 1e-9` |
| `test_check_redo_floor_python` | a floored step is rejected; hydro_u and hydro_w restored; NaN arm; 6-block Mesh halves dt | 1e-12 |
| `test_check_redo_saturation_python` (+cuda) | an unadjusted saturation step is redone; control accepted; block-1 count read | pinned values |
| `test_check_redo_parallel.<b>` | redo is one decision across 2 ranks | exact |


#### 15.8 Ch.8 Positivity, floors, limiters
<sub>inventory E: Scheme: Ch.8 Positivity, floors, limiters</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_flux_positivity_python` | limiter off goes negative, limiter on keeps min >= 0; totals conserved; periodic wrap theta | 1e-12 |
| `test_flux_positivity_cubedsphere_python` (+cuda) | tracer limiter across a panel seam conserves and keeps [0,1] | `DRIFT_TOL 1e-13` |
| `test_flux_positivity_cubedsphere_moist_python` (+cuda) | hydro species limiter across a seam | `DRIFT_TOL 1e-13` |
| `test_flux_positivity_carry.<b>` | withheld mass keeps its donor's energy and momentum (x1, x2, settling; CUDA) | 1e-12 |
| `test_fix_vapor_reports_failure_python` (+cuda), `test_fix_vapor_counts_every_column_python` | an unrepairable column raises from "U->W"; atomic failure counter | n/a |
| `test_fix_vapor_volume.<b>` | column repair keeps sum(rho q V) on varying V | exact |
| `test_parentless_cloud.<b>`, `_nb1.<b>`, `_nb1_mp.<b>`, `_nb1_mp_gloo` | parentless-cloud repair keeps column mass (one block, x1 split, two ranks, Gloo) | 1e-12 |
| `test_vapor_column_nb1.<b>` | vapor repair keeps mass for nb1 = 1, 2 | exact |
| `test_tracer_dry_convention_python` | tracers are per dry air under init, implicit and relax-bot-comp | `TOL 1e-12` |
| `test_stage_forcing_dry_tracer_python`, `test_dry_carry_zero_base_python` | dry-density sources keep scalar bounds at every RK order; a zero dry-carry base | 1e-12 |
| `test_uranus_cycle1_abort.<b>` | uranus column finishes 2 cycles; abnormal termination exits non-zero; late deck reaches cycle 40 | n/a |
| `test_forcing.<b>` limiter cases | patch/NaN marks redo; round-off repairs (4096 ulp, float32 64 ulp) are not redone | n/a |


#### 15.9 Ch.9 Diffusion, sedimentation, forcing
<sub>inventory E: Scheme: Ch.9 Diffusion, sedimentation, forcing</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_diffusion.<b>` | option parsing; viscous/conductive Laplacians; sine-mode decay; wall faces read no ghost; timestep bounds | 1e-12 to 1e-3 |
| `test_diffusion_moist.<b>` | moist conduction uses the local mixture cp; limiter uses nucleation parents | 1e-12 / 1e-3 |
| `test_diffusion_x1_scale.<b>`, `test_diffusion_x1_scale_python` | x1 profiles (tensor or YAML table): unity profile is bitwise the no-profile run, scaled decay rates, 2nd-order convergence, refusals | 1e-12 / bitwise |
| `test_forcing.<b>` | options, Coriolis (cubed sphere), relax-bot-*, sponge covariance, body heat, boundary fluxes, fused sedimentation == tensor path | 1e-12 / 1e-9 |
| `test_sedimentation_guards.<b>` | refuses a card without const-gravity; skipped when x1 flux off; rising cloud from the cell below | 1e-9 |
| `test_sedimentation_cubed_seam.<b>` (2 ranks), `test_sedimentation_cubed_seam_gloo` | seam repair with sedimentation and limiter; Gloo result == UCX bitwise (17 digits) | exact |
| `test_jit_user_forcing_python` | a scripted user forcing adds the expected tendency | `assert_close` default |


#### 15.10 Ch.10 Moist coupling
<sub>inventory E: Scheme: Ch.10 Moist coupling</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_wall_saturation.<b>` | phase change at a wall preserves energy and water | 1e-12 |
| `test_balance_column.<b>` `a_moist_column_with_one_condensable_comes_out_at_rest` | moist balance; vapor unchanged | 1e-12 |
| `test_check_redo_saturation_python` | see Ch.7 | pinned |


#### 15.11 Ch.11 Boundary conditions
<sub>inventory E: Scheme: Ch.11 Boundary conditions</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_radiating_boundary.<b>` | radiating modes on all faces, mixed faces, tracers ride dry density, acoustic pulses, restart reference, decomposed faces, CPU == CUDA | 1e-12 |
| `test_radiating_boundary_python` | a manual Python fill needs the saved reference | n/a |
| `test_rectify.<b>`, `test_flip_zero_count.<b>` | internal-boundary solid rectification; flip count thread-safe (8 threads == serial) | exact |
| `test_wb_wall_corner.<b>` | see Ch.5 | 1e-12 |


#### 15.12 Ch.12 Configuration
<sub>inventory E: Scheme: Ch.12 Configuration</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_yaml_keys.<b>` | 30 cases: every option block refuses an unknown key, named by path | n/a |
| `test_hydro_options.<b>` | dynamics/eos/forcing key whitelists; `fric-heat` refused; scheme not in {0,1,9} refused; `wb-wall-clamp` ships true and reaches the reference; non-map blocks refused | n/a |
| `test_process_group.<b>` | backend and `MASTER_PORT` env rules | n/a |
| `test_python_import_path_python` | `SNAPY_TEST_PYTHONPATH` wiring | n/a |
| switch arms | see Ch.12.12 matrix | |


#### 15.13 Ch.13 Diagnostics
<sub>inventory E: Scheme: Ch.13 Diagnostics</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_cycle_diagnostics.<b>` | 11 cases, see Ch.13 | 1e-9 / 1e-11 / 1e-12 |
| `test_cycle_diagnostics_parallel.<b>` | 2 ranks aggregate once | 1e-11 |
| `test_user_output.<b>` `OutputDiagnostics.*` | div/curl/theta_v fields | 1e-12 |


#### 15.14 Ch.14 Parallelism, GPU, restart/IO
<sub>inventory E: Scheme: Ch.14 Parallelism, GPU, restart/IO</sub>

| ctest | Asserts | Tol |
|---|---|---|
| `test_exchange.<b>` (2 ranks, `BLOCKS_PER_PROCESS=3`), `test_exchange_ucx`, `test_exchange_ucx_cuda` | cubed-sphere exchange with local and remote neighbours | exact |
| `test_mesh_exchange_python` | 4 blocks in one process: ghosts hold the neighbour id | exact |
| `test_cubed_sphere_vertical_velocity_exchange_python` | vertical velocity ghosts across panels | 1e-12 abs+rel |
| `test_mesh_multi_block.<b>` (2 ranks) | multi-block exchange | exact |
| `test_output_barrier.<b>` (2 ranks) | no rank returns before the combined file is complete | n/a |
| `test_gloo_one_tensor.<b>` (Apple) | a 2-tensor Gloo message is refused with the fix | n/a |
| `test_netcdf_utils.<b>` | NetCDF name sanitizing | exact |
| `test_user_output.<b>` | user outputs, slices, schedule keys, double precision readback, statistics, super-resolution | 1e-12 / bitwise |
| `test_restart_multiblock` | straka restart equals a straight run, field by field | max abs diff == 0 |
| `test_restart_cycle_limit`, `_dt_change`, `_output_schedule`, `_key_collision`, `_inplace_reorder` (non-Apple) | restart cycle/time/mass0/energy match (atol 1e-12); dt change resets next_time; schedules/counters kept; no overwrite of finished frames | 1e-12 / md5 |
| `test_exchange_decomp` (non-Apple or FULL) | decomposition matrix of `test_exchange.yaml` | exact |
| `test_shallow_xy_decomp` (FULL; excluded in CI) | single vs mesh4 vs proc2_mesh2 vs proc4 bitwise | max_abs == 0 |
| `test_shallow_splash_decomp`, `test_shallow_splash_ucx_cuda_decomp` (FULL) | splash decompositions vs reference | L2 < 50 |
| `test_x1_seam_split_mp*`, `test_parentless_cloud_nb1_mp*`, `test_check_redo_parallel`, `test_cycle_diagnostics_parallel` | cross-rank seams and collectives | 1e-13 / 1e-12 / 1e-11 |


#### 15.15 examples used as regression
<sub>inventory E: Scheme: examples used as regression</sub>

| Example | Deck(s) | ctest | Check |
|---|---|---|---|
| straka (2-D density current; cartesian, weno5, lmars, ideal-gas, grav1 -9.8, nghost 3, default gravity-work cell+fixer) | `examples/straka.yaml`, `straka_single.yaml`, `straka_proc2.yaml`, `straka_mesh2.yaml` | `test_straka` (label `reference`; 2 ranks; vs Zenodo `straka-ref.nc`), `test_straka_redo`, all restart tests | L2 of theta difference < 50 (`tests/test_straka.py:17@e894700`) |
| shallow_xy (cartesian shallow-water, shallow-roe) | `shallow_xy*.yaml` | `test_shallow_xy` (FULL, 4 ranks), `test_shallow_xy_decomp` | L2 of rho < 50; decomp bitwise |
| shallow_splash (gnomonic shallow-water) | `shallow_splash*.yaml` | `test_shallow_splash` (FULL, 6 ranks), `test_shallow_splash_decomp`, `_ucx_cuda_decomp` | L2 of rho < 50 (`tests/test_shallow_splash.py:17@e894700`) |
| bryan (moist bubble; ideal-moist, limiter, weno5, lmars) | `examples/bryan.yaml` edited in place | `test_bryan_balance_ic` | balance-ic cap/convergence/dry path |
| uranus (moist-mixture, VIC 1) | `tests/test_uranus_cycle1_abort.yaml`, `test_uranus_late_abort.yaml`, `test_abnormal_exit_floor.yaml` via `run_hydro.<b>` | `test_uranus_cycle1_abort.<b>` | termination strings and exit code |
| shock, jupiter_*, earth_crm, run_hydro | built (`examples/CMakeLists.txt:5-11@e894700`) | none (CI's macOS exclude list names `test_shock_cpu`, `test_run_hydro_cpu`, which are not registered at dae902b) | none |

- Figures: (1) a pyramid of the test suite: unit gtests, python oracles, switch arms, multi-rank, reference examples;
  (2) a bar chart of entries per chapter.
- Limits / known issues:
  - Reference checks use a loose L2 < 50 on the final theta/rho field against Zenodo files
    (`tests/run_straka.cmake:8@e894700`), which needs network access or a cached file.
  - `tests/run_example_mass_check.py` is not registered (orphan). `run_shallow_*.cmake` are registered only under FULL_TESTS.
  - The CI macOS exclude regex names `test_shock_cpu` and `test_run_hydro_cpu`, which do not exist at dae902b (stale).
  - CUDA arms are never run in CI.
  - Python ctests test the installed snapy unless `SNAPY_TEST_PYTHONPATH` is set (warning at
    `tests/CMakeLists.txt:360-362@e894700`).
- Discrepancies: #217's Limits (Mesh line lacks ke) is superseded (see Ch.13). `gw__NEXTPR_spec_wbref_exact.md:286`
  (no CUDA or multi-process runs of WB_REF4) is superseded by the arms at `tests/CMakeLists.txt:55-90@e894700`.

---

<a id="ch16"></a>
## Chapter 16. Known limits

Assembled at the end from the Limits layer of every section, grouped by severity, each with its evidence. The
cross-cutting items the research found, to be confirmed by the chapter authors:

1. **The VIC always closes a column as a reflecting wall**, whatever the $x_1$ boundary type; outflow or periodic $x_1$
   with the VIC is accepted silently (7.B, inventory D).
2. **Ghost-exchange order differs between `MeshBlock::forward` (exchange, then advance) and `Mesh::forward` (advance,
   then exchange)**; a Mesh-API driver that applies operator-split sources between stages reconstructs from stale
   ghosts (inferred from code, not measured; 1.5, 1.6, 7.2).
3. **No test covers `SNAP_X1_MASS_COVARIANCE`**, and its onset numbers are a placeholder (4.B, 12.4).
4. **Switch combinations not covered**: `SNAP_X1_CENTROID_EXACT` with face work or with flux covariance; `SNAP_WB_REF4`
   and `SNAP_X1_CENTROID_EXACT` on the cubed sphere; flux covariance across ranks; D with any of the other four
   switches (12.4).
5. **Reproducibility**: restart is shown bit for bit only with the same decomposition, float32 NetCDF, within one
   process; the fixer's global sum is decomposition-dependent at round-off (14.C).
6. **Open issues still in the code at the pin**: a resumed run rewrites its last outputs and its source restart file
   (chengcli/snapy#277); the adiabatic-rest drift of issue #252 after `on_theta` conduction was removed; `kappa_iso`
   diffuses temperature at $\kappa/\gamma$ at uniform pressure (issue #261). (Issue numbers as cited in
   `sources/gh__ISSUE_THREADS_*.md`; repository to be confirmed as chengcli/snapy.)
7. **Option defaults differ between the C++ structs and YAML** (EOS floors, reconstruction `shock`, Riemann solver
   type); `max_redo` cannot be set from YAML (Ch. 12).
8. **CI**: no CUDA arm runs in CI; the macOS exclude list names tests that do not exist (Ch. 15).

### Editor's notes carried from the inventories

**From inventory D (chapters 7, 8, 11):**

- Gravity-work matrix entries are listed under Ch 7 "VIC assembly". The gravity-work author owns their derivations.
- `docs/derivations/290-lu-pivot-tolerance.md` is the only committed derivation that belongs to these chapters. Most
  schemes here need re-derivation from code. The ones that matter most are the VIC linearisation and Bnd closure, the
  stage-weighted dt identity, the outflow characteristic BC with its α limiter, the fix_vapor conservation, and the θ
  margin.
- All tolerance constants in these tests are chosen against measured values. Only the θ/round-off ulp constants and
  the LU guard (8Nε) carry any rationale (`290-lu-pivot-tolerance.md`, PR #258).

**From inventory B (chapters 2, 9, 10), cross-cutting discrepancies (code wins):**

1. H2-dissociation EOS (source report) is absent at `kintera 4dc613d`; only the PV->T Newton sign fix is there (`kintera src/thermo/thermo_y.cpp:445-447@4dc613d`). Drop the deck citation (ISSUES.md item 4).
2. `on_theta` conduction (PR #253/#259) was removed by #268. The adiabatic-rest drift of issue #252 is open at the pin.
3. Cloud-parent cache: PR #223 says "global registry"; since #235 it uses the thermo's own table.
4. relax-bot-temp at-face: PR #219 says `1.5 T0 - 0.5 T1`; the code uses the coordinate-spacing weight (#279).
5. EOS floor defaults: struct 1e-10/1e-10 vs YAML 1e-6/1e-3.
6. `moist_mixture.hpp:43-54` call-order comment is stale relative to `_ensure_cache`.
7. Evaporation extent law: the report says "not landed"; it is in kintera at the pin.
8. `plume-forcing` is accepted by the YAML whitelist but cannot be installed (plume EOS removed).
9. `sources/deriv__diffusion-face-coefficient.md` is the pre-`e659b69` version; cite `docs/derivations/diffusion-face-coefficient.md@e894700`.

---

<a id="ch17"></a>
## Chapter 17. Appendices

### Appendix A. Notation
`NOTATION.md`, rendered as a table.

### Appendix B. Derivation index
One row per scheme: the number of derivations marked `exists` and `re-derive` in its entry. Every derivation, existing
or re-derived, gets an executable check next to it (STYLE.md section 7); this table becomes the check index as sections
are written.

| section | scheme | exists | re-derive |
|---|---|---|---|
| 1.1 | Driver loop (time step, stages, redo, outputs) | 0 | 0 |
| 1.2 | MeshBlock construction (`reset`) | 0 | 0 |
| 1.3 | Initialization | 0 | 0 |
| 1.4 | Stage update `advance_local` (MeshBlock) | 0 | 2 |
| 1.5 | `MeshBlock::forward` (exchange-then-advance) | 0 | 0 |
| 1.6 | Mesh (several blocks per process) | 0 | 0 |
| 1.7 | Hydro forward (code map of its seven sections) | 0 | 0 |
| 1.8 | Scalar forward | 0 | 0 |
| 1.9 | CPU/GPU dispatch (DispatchStub + TensorIterator; CUDA loops) | 0 | 0 |
| 1.10 | Tensor layout, variable indices, ghost zones, interior slices | 0 | 0 |
| 1.11 | Options objects and YAML | 0 | 0 |
| 1.12 | Python package `snapy` | 0 | 0 |
| 1.13 | External dependencies (kintera, pyharp, torch, comm and IO libraries) | 0 | 0 |
| 2.1 | Conservation laws and operator ordering in one RK stage | 0 | 2 |
| 2.2 | EquationOfState interface, options and type dispatch | 0 | 0 |
| 2.3 | Ideal gas EOS | 0 | 1 |
| 2.4 | Ideal-moist EOS (constant heat capacities, zero-volume condensates, reference energies) | 0 | 3 |
| 2.5 | Moist-mixture EOS (kintera-backed) | 0 | 4 |
| 2.6 | ANEOS (tabulated EOS through an external library) | 0 | 0 |
| 2.7 | Shallow-water EOS | 0 | 0 |
| 2.8 | EOS ↔ solver consistency conditions (temp2inteng and friends) | 0 | 2 |
| 2.9 | Saturation adjustment (kintera UV equilibrium) — thermodynamic side | 0 | 1 |
| 3.1 | One global grid, sliced per block (decomposition-invariant faces) | 0 | 0 |
| 3.2 | Cartesian metric | 0 | 1 |
| 3.3 | Spherical-polar metric and geometric sources | 1 | 2 |
| 3.4 | Gnomonic equiangular cubed sphere (geometry and metric) | 1 | 3 |
| 3.5 | Radial face moments and the face-centroid shift (curved-grid helpers) | 1 | 0 |
| 3.6 | Layouts and rank maps (slab, cubed, cubed-sphere) | 0 | 0 |
| 3.7 | Physical vs internal faces (bfunc assignment) | 0 | 0 |
| 3.8 | Generic ghost exchange (what is filled) | 0 | 0 |
| 3.9 | Cubed-sphere cross-panel ghost interpolation | 2 | 2 |
| 3.10 | Cubed-sphere face-state seam sync (hydro and scalar LR states) | 1 | 0 |
| 3.11 | θ (positivity donor factor) across seams: raw copy | 1 | 0 |
| 3.12 | x1 seams between blocks (column split, `cubed` layout pz>1) | 1 | 2 |
| 3.13 | Exchange of conserved vs primitive variables, and the velocity frame at seams | 0 | 1 |
| 3.14 | x1-wall corner refresh inside tangential ghost slabs (#265) | 0 | 0 |
| 3.15 | Registered but non-functional coordinate type `cylindrical` | 0 | 0 |
| 4.1 | Finite-volume update and flux divergence (stage operator) | 1 | 1 |
| 4.2 | Reconstruction framework (Reconstruct / Interp, variable split, floors) | 0 | 1 |
| 4.3 | Donor cell ("dc") | 0 | 1 |
| 4.4 | PLM (van Leer harmonic-mean slope) | 0 | 1 |
| 4.5 | Linear centred polynomials cp3 / cp5 (and cp2/cp4/cp6 helpers) | 0 | 1 |
| 4.6 | WENO3 / WENO5 (Jiang–Shu weights, eps 1e-6, optional scaling) | 0 | 1 |
| 4.7 | PPM | 0 | 0 |
| 4.8 | Riemann solver framework, face-local frame, face-pressure output | 0 | 1 |
| 4.9 | LMARS (low-Mach approximate Riemann solver; production default in example decks) | 0 | 1 |
| 4.10 | HLLC (PVRS wave speeds) | 0 | 1 |
| 4.11 | Roe (ideal gas and ideal-moist) | 0 | 1 |
| 4.12 | Shallow-water Roe and plume-roe | 0 | 1 |
| 4.13 | Single-valued x1 seam fluxes (process-seam averaging) | 0 | 1 |
| 4.14 | Geometric (curvature) sources, spherical-polar; momentum flux form | 1 | 3 |
| 4.15 | Geometric sources, gnomonic cubed sphere; exact cell volume and solid angle | 1 | 1 |
| 4.16 | x2/x3 face-flux covariance and centroid correction (SNAP_FLUX_COVARIANCE, #289/#293) | 7 | 0 |
| 4.17 | x1 rho-w mass-flux covariance (SNAP_X1_MASS_COVARIANCE) | 1 | 1 |
| 5.1 | Well-balanced x1 reconstruction (perturbation about a hydrostatic reference) | 2 | 1 |
| 5.2 | Hydrostatic reference kernel — face-pressure scan, cell pressure, density reference ("smooth5") | 1 | 3 |
| 5.3 | Wall clamp and the wall continuation of the default reference (wb-wall-clamp, linear/ln closure) | 2 | 0 |
| 5.4 | Reference continuity across x1 seams (anchor relay and ghost-row exchange) | 0 | 1 |
| 5.5 | Hydrostatic mode (non-hydrostatic < 1): gravity replaced by the discrete pressure gradient | 0 | 1 |
| 5.6 | balance_column — projection of a ghost-free column onto the scheme's discrete balance | 0 | 1 |
| 5.7 | SNAP_WB_REF4 — fourth-order, cell/face-consistent density reference (and non-uniform cell pressure) | 2 | 0 |
| 5.8 | SNAP_X1_CENTROID_EXACT — r^2-exact x1 maps on spherical-polar | 1 | 0 |
| 5.9 | The 1/R remainder on spherical-polar (what is left after the corrections) | 4 | 0 |
| 5.10 | (legacy box) isentropic wall ghosts and zero-gradient wall faces | 0 | 1 |
| 6.1 | Constant gravity forcing and the cell form of the gravity work (`gravity-work: cell`, the default) | 1 | 2 |
| 6.2 | Face form of the gravity work (`gravity-work: face`, `face-wallc`) and the cp3/cp5/weno5 curvature flux | 4 | 2 |
| 6.3 | Gravity-work fixer (global $E+\mathrm{PE}_d$ correction for `gravity-work: cell`) | 2 | 2 |
| 6.4 | The corrected-PE face work, scheme D (`SNAP_GRAVITY_WORK_RADIAL_EXACT`) | 1 | 0 |
| 6.5 | Gravity work inside the vertical implicit operator (cell, face rows, projection and clamp work) | 1 | 3 |
| 6.6 | What each form conserves (summary and oracle guide) | 2 | 0 |
| 7.1 | Explicit SSP Runge–Kutta stage update (Shu–Osher form) | 2 | 1 |
| 7.2 | Ghost-exchange placement within a stage (MeshBlock vs Mesh driver) | 0 | 0 |
| 7.3 | CFL time step (acoustic, implicit-advective, shear, diffusion; global MIN; redo halving) | 0 | 4 |
| 7.4 | Step acceptance and rejection (`check_redo` / `apply_redo`), collective decision, max_redo, abnormal exit | 0 | 0 |
| 7.5 | Operator-split pieces at the step boundary (saturation adjustment, kinetics) | 1 | 0 |
| 7.6 | VIC activation and options | 0 | 0 |
| 7.7 | VIC block-tridiagonal assembly (Roe-linearised flux Jacobian, |A| dissipation, I/dt, gravity coupling, wall closure) | 1 | 3 |
| 7.8 | Stage-weighted implicit time step (dt_corr = w2·dt) | 0 | 0 |
| 7.9 | Block-tridiagonal forward sweep and backward substitution | 0 | 0 |
| 7.10 | LU pivot tolerance and failed-column sentinel (#290) | 1 | 0 |
| 7.11 | VIC solve rejection, latch and rollback (cause 32) | 0 | 0 |
| 7.12 | VIC constituent redistribution (implicit mass correction as face fluxes; "Component B") | 1 | 2 |
| 7.13 | VIC column closure versus the x1 boundary type | 0 | 0 |
| 8.1 | Tracer flux positivity limiter θ (hydro species channels) | 3 | 0 |
| 8.2 | Carry of energy and momentum with withheld species mass | 0 | 0 |
| 8.3 | Positivity-limited species fluxes carry energy and momentum (moist carry) | 0 | 1 |
| 8.4 | Passive-scalar limiter and complement upper bound | 2 | 0 |
| 8.5 | Conserved-variable EOS limiter (`apply_conserved_limiter_`) | 1 | 1 |
| 8.6 | Conserved/primitive limiter — floors (density, pressure, temperature) and limiter marks | 0 | 1 |
| 8.7 | Primitive-variable EOS limiter (`apply_primitive_limiter_`) | 0 | 0 |
| 8.8 | Reconstruction-stage floors | 0 | 0 |
| 8.9 | Well-balanced face positivity floor (face-density/pressure fallback) | 0 | 0 |
| 8.10 | Dry channel positivity inside the VIC (pass-3a availability clamp, donor mark, species donor margin) | 1 | 1 |
| 8.11 | Round-off thresholds for positivity events | 1 | 0 |
| 8.12 | Fresh-primitive floor detector (redo cause 1) | 0 | 0 |
| 8.13 | Dry-carry of passive tracers under dry-mass sources (0/0 guard) | 0 | 1 |
| 9.1 | Forcing framework and registration | 0 | 0 |
| 9.2 | User stage forcings | 0 | 0 |
| 9.3 | Coriolis (123 and xyz forms, cubed-sphere covariant) | 0 | 1 |
| 9.4 | Isotropic viscosity and heat conduction (forcing/diffusion) | 0 | 4 |
| 9.5 | Diffusion face coefficient at walls and ghosts (one-sided wall extrapolation) | 1 | 0 |
| 9.6 | x1 profiles of the kinematic coefficients (nu_scale_x1, kappa_scale_x1) and the product face coefficient | 1 | 0 |
| 9.7 | Body heating, top cooling, bottom heating | 0 | 1 |
| 9.8 | Bottom relaxation (temperature, velocity, composition) | 0 | 2 |
| 9.9 | Sponge layers (top and bottom) | 0 | 2 |
| 9.10 | Plume forcing (unreachable) | 0 | 0 |
| 9.11 | Turbulence (not built) | 0 | 0 |
| 10.1 | Saturation adjustment in the step | 0 | 1 |
| 10.2 | check_redo — causes, reduction, restore (saturation and limiter) | 0 | 0 |
| 10.3 | Condensate repair by parent-vapour borrow (stoichiometric split) | 0 | 1 |
| 10.4 | Column vapour repair fix_vapor (volume-weighted, upward fallback) and parentless clouds | 0 | 1 |
| 10.5 | Column vapor and cloud repair (`fix_vapor_impl`) | 0 | 0 |
| 10.6 | Precipitation and evaporation kinetics (driver-level coupling, kintera rates) | 1 | 1 |
| 10.7 | Passive scalar (tracer) transport per dry air, with optional upper bound | 0 | 2 |
| 10.8 | Sedimentation of condensates (recommended to move to Ch. 10) | 0 | 3 |

Chapters 2 and 10 carry 22 `re-derive` entries and 1 `exists` between them, and no chapter author. The
notation they need (NOTATION.md §2a, latent heat, entropy, the vapour/condensate split, the thermodynamic
reference state) does not exist yet; settle it with the rules in round 1, before the chapters are assigned,
or they will be written twice.
| 11.1 | Boundary-function registry, YAML parsing, and face classification | 0 | 0 |
| 11.2 | Reflecting wall | 0 | 0 |
| 11.3 | Periodic | 0 | 0 |
| 11.4 | Extrapolation (zero-gradient) | 0 | 0 |
| 11.5 | Outflow / radiating characteristic boundary | 0 | 2 |
| 11.6 | Custom (no-op) and solid (mask) boundary functions | 0 | 0 |
| 11.7 | When ghosts are filled (apply_boundaries, exchange_ghost_zones, corner refresh) | 0 | 0 |
| 11.8 | Exchange-filled ghosts (layouts, cubed-sphere panels) — pointer section | 0 | 1 |
| 11.9 | Immersed solids (mask, rectification, face-state mirror, refill) | 0 | 3 |
| 11.10 | Boundary conditions and the well-balanced reference state | 1 | 1 |
| 12.1 | CMake options and cache variables (build-time) | 0 | 0 |
| 12.2 | `configure.h` macros and compile definitions (build-time) | 0 | 0 |
| 12.3 | environment helper `get_env` and the read-once rule | 0 | 0 |
| 12.4 | `SNAP_WB_REF4` (fourth-order, cell/face-consistent x1 well-balanced reference) | 2 | 0 |
| 12.5 | `SNAP_X1_CENTROID_EXACT` (spherical-polar r^2-average x1 formulas) | 1 | 0 |
| 12.6 | `SNAP_FLUX_COVARIANCE` (#289 x2/x3 face-flux covariance and centroid terms) | 1 | 0 |
| 12.7 | `SNAP_X1_MASS_COVARIANCE` (x1 mass-flux covariance) | 0 | 0 |
| 12.8 | `SNAP_GRAVITY_WORK_RADIAL_EXACT` (option F: corrected-PE gravity work) | 1 | 0 |
| 13.1 | cycle-line budget (`print_cycle_diagnostics`) | 1 | 1 |
| 13.2 | positivity-limiter meters (`limcut`, `thetamin`, `thetasevere`, hits) | 0 | 1 |
| 13.3 | VIC clamp meter (`vicclamp`) | 0 | 1 |
| 13.4 | gravity-work fixer E+PE budget (D, wall mass, `fixgrav`) | 1 | 0 |
| 13.5 | redo causes and termination status (diagnostic view) | 0 | 0 |
| 13.6 | output-field diagnostics | 0 | 0 |
| 13.7 | mass-conservation regression checks | 0 | 0 |
| 14.1 | Launch environment and rendezvous | 0 | 0 |
| 14.2 | Communication backends (Gloo, UCX via commux, external PG; no NCCL) | 0 | 0 |
| 14.3 | Exchange message matching and in-process copies | 0 | 1 |
| 14.4 | Several blocks per process and GPU streams | 0 | 0 |
| 14.5 | Collectives and global decisions | 0 | 0 |
| 14.6 | GPU execution | 0 | 0 |
| 14.7 | NetCDF output (per-block files, combine) | 0 | 0 |
| 14.8 | PnetCDF output | 0 | 0 |
| 14.9 | Restart files (write, bundle, read) | 0 | 0 |
| 14.10 | Output scheduling, statistics and termination | 0 | 1 |
| 14.11 | Combine and inspect tools (post-processing) | 0 | 0 |
| 14.12 | Reproducibility and bit-for-bit claims (inventory) | 0 | 0 |

### Appendix C. Test index
Generated from `ctest -N` at the pinned sha by a script in `tools/` (planned), so it cannot drift from Ch. 15.

### Appendix D. Environment-variable switches
Folded in from inventory A (1.14); Ch. 12.2 is the full treatment.

- Summary: run-time numerics switches are read once per process (static lambdas), so every block in a process makes the
  same choice. Nothing checks that ranks agree.
- Derivations: per the owning physics chapter.
- Figures: none.
- Code (name / reader / default):
  - `SNAP_X1_CENTROID_EXACT` / `src/coord/x1_centroid.cpp:96@e894700` / "0".
  - `SNAP_WB_REF4` / `src/hydro/wb_ref4.cpp:87@e894700` / "0". It is also implied by `SNAP_X1_CENTROID_EXACT`
    (`wb_ref4.cpp:94`).
  - `SNAP_X1_MASS_COVARIANCE` / `src/hydro/hydro_forward.cpp:41@dae902b` / "0".
  - `SNAP_FLUX_COVARIANCE` / `src/hydro/hydro.cpp:221@e894700` / "0".
  - `SNAP_GRAVITY_WORK_RADIAL_EXACT` / `src/hydro/hydro.cpp:245@e894700` / "1". It acts only with `gravity-work: face`.
  - Parallel / IO: `BACKEND`, `DEVICE`, `DEVICE_ID`, `RANK`, `LOCAL_RANK`, `WORLD_SIZE`, `PROCESS_RANK`,
    `PROCESS_WORLD_SIZE`, `MASTER_ADDR`, `MASTER_PORT` (`src/layout/layout.cpp:189-219@e894700`). commux defaults
    `COMMUX_COALESCE=1`, `COMMUX_GROUP=1`, and `UCX_TLS` without CUDA transports when DEVICE=cpu
    (`src/layout/process_group_ucx.cpp:26-30@e894700`).
- Tests: the seam arms in `tests/CMakeLists.txt:38-87` set these per ctest entry.
- Limits / known issues: a rank-to-rank mismatch in a numerics switch would make shared faces two-valued, with no check.
  This follows from the code comments; no test covers it.
- Discrepancies: none.

### Appendix E. Components outside snapy
- Radiation inside the snapy tree: none is compiled. `src/diagnostics/radiative_flux.cpp_` is a disabled
  diagnostic (the trailing underscore keeps it out of the build, as for `src/coord/cylindrical.cpp_` and
  `src/forcing/sponge_lyr.cpp_`); `src/z.junk/load_radiation_output_data.cpp_` is dead;
  `cmake/modules/FindDisort.cmake` is a locator kept for the Python package, which imports pydisort
  (`python/__init__.py`, §1.13). None of them is described further. The only radiation-related scheme in the
  report is the radiating characteristic boundary (§11.5), which is a characteristic outflow condition and
  contains no radiative transfer; its name is the only thing radiative about it, and §11.5 says so in its
  first line.
- The time integrator: pyharp `harp::Integrator` (`pyharp:src/integrator/integrator.cpp:49-60@4721715` for rk3).
- The kinetics coupling and precipitation: in the example driver `examples/run_hydro.cpp` (10.6).
- The radiative time-step limiter, folded in from inventory D:

- Summary: τ_rad = c_v/(16κσT³ε) with an escape-probability ε, dt ≤ C·min τ_rad (C = 0.5), applied by an external
  runner after `max_time_step`. Switch: runner keys `radiative-transfer.rt_limiter: off|relax`, `rt_limiter_safety`. Not
  in snapy.
- Derivations: exists: `sources/canoe__RT_TIMESTEP_LIMITER_TECH_REPORT.md` §3 (a full linearisation and forward-Euler
  monotonicity derivation). It applies to the runner, not to snapy.
- Code: none in snapy (a grep for `rt_limiter`/`tau_rad` is empty).
- Tests: none in snapy.
- Discrepancies: the outline lists it under snapy. It is not part of the pinned tree, so recommend moving it to an
  appendix or dropping it.
