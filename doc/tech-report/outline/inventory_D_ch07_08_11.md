# Outline inventory D: Chapters 7, 8, 11

Pinned code: snapy `dae902b` (worktree snapy-fb). All `path:line` below are `@dae902b` unless marked otherwise.
The explicit RK integrator is not in snapy. It is `harp::Integrator` from pyharp, an external dependency found by
`cmake/modules/FindHarp.cmake` (`CMakeLists.txt:96`). snapy pins no harp version (`pyproject.toml` lists only
`kintera>=2.5.13`). The harp lines below are cited at the local pyharp clone `4721715` and marked `(harp@4721715)`. The
chapter author must re-verify them against the harp that the release links.

Source files referred to as `sources/<file>` are in the tech-report sources directory.

---

## Chapter 7: Time integration

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

### Scheme: Explicit SSP Runge–Kutta stage update (Shu–Osher form)
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

### Scheme: Ghost-exchange placement within a stage (MeshBlock vs Mesh driver)
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

### Scheme: CFL time step (acoustic, implicit-advective, shear, diffusion; global MIN; redo halving)
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

### Scheme: VIC activation and options
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

### Scheme: VIC block-tridiagonal assembly (Roe-linearised flux Jacobian, |A| dissipation, I/dt, gravity coupling, wall closure)
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

### Scheme: Stage-weighted implicit time step (dt_corr = w2·dt)
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

### Scheme: Block-tridiagonal forward sweep and backward substitution
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

### Scheme: LU pivot tolerance and failed-column sentinel (#290)
- Summary: `ludcmp` returns ±1 (parity) or 0 on failure. It rejects a non-finite input or output, a zero-row scale, and
  any pivot with |p_j|/s_j ≤ 8·N·ε_T, where s_j is the original row max carried with the permutation. On failure the
  sweep writes NaN into δ for the whole column (`vic_fail_column`). The host treats any non-finite δ as a rejected
  column. Switch: none (the tolerance is a compile-time formula).
- Derivations:
  - exists: `docs/derivations/290-lu-pivot-tolerance.md@dae902b` (same as `sources/deriv__290-lu-pivot-tolerance.md`
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

### Scheme: VIC solve rejection, latch and rollback (cause 32)
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

### Scheme: VIC constituent redistribution (implicit mass correction as face fluxes; "Component B")
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

### Scheme: Step acceptance and rejection (`check_redo` / `apply_redo`), collective decision, max_redo, abnormal exit
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

### Scheme: Operator-split pieces at the step boundary (saturation adjustment, kinetics)
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

### Scheme (not in snapy): RT timestep limiter
- Summary: τ_rad = c_v/(16κσT³ε) with an escape-probability ε, dt ≤ C·min τ_rad (C = 0.5), applied by an external
  runner after `max_time_step`. Switch: runner keys `radiative-transfer.rt_limiter: off|relax`, `rt_limiter_safety`. Not
  in snapy.
- Derivations: exists: `sources/canoe__RT_TIMESTEP_LIMITER_TECH_REPORT.md` §3 (a full linearisation and forward-Euler
  monotonicity derivation). It applies to the runner, not to snapy.
- Code: none in snapy (a grep for `rt_limiter`/`tau_rad` is empty).
- Tests: none in snapy.
- Discrepancies: the outline lists it under snapy. It is not part of the pinned tree, so recommend moving it to an
  appendix or dropping it.

---

## Chapter 8: Positivity, floors and limiters

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

### Scheme: Tracer flux positivity limiter θ (hydro species channels)
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

### Scheme: Carry of energy and momentum with withheld species mass
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

### Scheme: Passive-scalar limiter and complement upper bound
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

### Scheme: Conserved-variable EOS limiter (`apply_conserved_limiter_`)
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

### Scheme: Column vapor and cloud repair (`fix_vapor_impl`)
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

### Scheme: Primitive-variable EOS limiter (`apply_primitive_limiter_`)
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

### Scheme: Reconstruction-stage floors
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

### Scheme: Well-balanced face positivity floor (face-density/pressure fallback)
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

### Scheme: Dry channel positivity inside the VIC (pass-3a availability clamp, donor mark, species donor margin)
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

### Scheme: Round-off thresholds for positivity events
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

### Scheme: Fresh-primitive floor detector (redo cause 1)
- Summary: covered in Ch 7 (`floor_hit`). Here, document only that it is the only detector of density or pressure
  collapse when the limiter floors the state. Its 1.001 factor means "at or within 0.1% of the floor".
- Derivations: none needed (a threshold test); state the 1.001 band from `src/mesh/meshblock.cpp:1190-1204@dae902b`.
- Figures: a density profile entering the band [floor, 1.001 floor] and the redo it triggers.
- Code: `src/mesh/meshblock.cpp:1190-1204@dae902b`.
- Tests: `tests/test_check_redo_floor.py` (`test_check_redo_floor_python`).
- Limits / known issues: the floor can mask a defect if the floors exceed the physical regime. Above about 120 levels
  the floors must match the density regime (tall-column report §7).

### Scheme: Dry-carry of passive tracers under dry-mass sources (0/0 guard)
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

## Chapter 11: Boundary conditions

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

### Scheme: Boundary-function registry, YAML parsing, and face classification
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

### Scheme: Reflecting wall
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

### Scheme: Periodic
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

### Scheme: Extrapolation (zero-gradient)
- Summary: every ghost is a copy of the first interior cell. Switch: `extrapolation`. It is also the fallback used by
  outflow for `kScalar` auxiliary fields and for shallow water.
- Derivations: none.
- Figures: none.
- Code: `src/bc/bc_func.cpp:52,60`.
- Tests: `tests/test_radiating_boundary.cpp` — `acoustic_pulses` runs `extrapolation` as the comparison arm (no
  assertion on that arm).
- Limits / known issues: it reflects acoustic waves (not asserted).
- Discrepancies: none.

### Scheme: Outflow / radiating characteristic boundary
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

### Scheme: Custom (no-op) and solid (mask) boundary functions
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

### Scheme: When ghosts are filled (apply_boundaries, exchange_ghost_zones, corner refresh)
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

### Scheme: Exchange-filled ghosts (layouts, cubed-sphere panels) — pointer section
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

### Scheme: Immersed solids (mask, rectification, face-state mirror, refill)
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

### Scheme: Boundary conditions and the well-balanced reference state
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
  - The wall-ghost order of the default reference: exists: `docs/derivations/wb-ref-wall.md@dae902b` (also
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

### Scheme: VIC column closure versus the x1 boundary type
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

### Cross-chapter notes for the editor
- Gravity-work matrix entries are listed under Ch 7 "VIC assembly". The gravity-work author owns their derivations.
- `docs/derivations/290-lu-pivot-tolerance.md` is the only committed derivation that belongs to these chapters. Most
  schemes here need re-derivation from code. The ones that matter most are the VIC linearisation and Bnd closure, the
  stage-weighted dt identity, the outflow characteristic BC with its α limiter, the fix_vapor conservation, and the θ
  margin.
- All tolerance constants in these tests are chosen against measured values. Only the θ/round-off ulp constants and
  the LU guard (8Nε) carry any rationale (`290-lu-pivot-tolerance.md`, PR #258).
