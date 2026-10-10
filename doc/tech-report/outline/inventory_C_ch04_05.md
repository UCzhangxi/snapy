# Outline inventory: Chapters 4 and 5 (pinned sha dae902b)

All `path:line` are at `@dae902b` (verified with grep -n / sed -n). "docs/..." means
`docs/derivations/...@dae902b`. "sources/..." means `doc/tech-report/sources/...`. The `sources/deriv__*.md`
copies are OLDER snapshots than the committed docs at dae902b (wb-ref4 from fdf895b, x1-centroid-spherical
from 1cf0bbc, 289-covariance from aea71ed); cite the committed docs first and use the sources copies only as
history (see Discrepancies in each scheme).

Switch parsing convention shared by every `SNAP_*` env switch below: read once per process into a
function-local static via `get_env` (src/layout/layout.hpp:38), case-insensitive; off for unset, empty,
`0`, `false`, `off`, `no` (default "0"), except `SNAP_GRAVITY_WORK_RADIAL_EXACT` (default "1"; not in these
chapters).

---

## Chapter 4: Spatial discretization

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

### Scheme: Finite-volume update and flux divergence (stage operator)
- Summary: du = -dt * [ (A F)_{+} - (A F)_{-} ] / V summed over x1,x2,x3 on interior cells, minus geometric
  sources, then forcings; the stage order is EOS -> x1 recon+Riemann -> seam average -> x2/x3 recon(+cubed-sphere
  face-state exchange)+Riemann(+covariance) -> species positivity limiter -> divergence+sources -> forcings ->
  implicit correction. Switch: per-direction `dynamics/disable-flux-x1|x2|x3` (YAML, default false;
  src/hydro/hydro_options.cpp:54-56; disabling also zeroes the matching grav component, :80-82).
- Derivations:
  - FV balance and face-average definition of the flux: exists docs/289-covariance-x3-curved.md §1.1 (eqs 1.1-1.2;
    its line refs are at 117e449, stale).
  - The stage pipeline and which tensor carries what (flux1/2/3 shapes, face indexing il..iu+1, interior-only
    tendency): re-derive from src/hydro/hydro_forward.cpp:207-1008@dae902b and src/coord/coordinate.cpp:509-553@dae902b.
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

### Scheme: Reconstruction framework (Reconstruct / Interp, variable split, floors)
- Summary: `ReconstructImpl::forward` returns [wl, wr] per face; with `shock: false` density and tracers use
  interp1 and velocity+pressure use interp2; with `shock: true` all rows use interp1 and no floors are applied.
  Switches: YAML `dynamics/reconstruct/{vertical,horizontal}/{type,scale,shock}` (src/recon/reconstruct.cpp:31-36);
  defaults from YAML: type "dc", scale false, shock false. EOS `limiter`, `density-floor`, `pressure-floor` gate the
  face floors (src/eos/equation_of_state.hpp:49-52, defaults 1e-10, 1e-10, false).
- Derivations:
  - Face/cell index map of `_apply_inplace` (outl -> wlr[IRT] at faces il-1..iu, outr -> wlr[ILT] at il..iu+1;
    dummy-region replication): re-derive from src/recon/reconstruct.cpp:50-65@dae902b.
  - Why weno3/weno5 select linear cp3/cp5 for velocity/pressure (interp2): no rationale in any source;
    describe from src/recon/interpolation.cpp:21-36@dae902b (design choice, not derived).
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

### Scheme: Donor cell ("dc")
- Summary: first-order, face value = adjacent cell value. Switch: `type: dc` (default type).
- Derivations: trivial; re-derive from src/recon/interpolation.hpp:100-105@dae902b.
- Figures: piecewise-constant cells with the two face states at one face.
- Code: src/recon/interpolation.hpp:88 — `DonorCellInterpImpl` — `left`/`right` copies (:100-105).
- Tests: tests/test_plm.cpp `reconstruct_preserves_a_constant_field` (dc arm); tests/test_x1_seam_split.cpp `wb_ref4_gravity_0_nghost_1_steps` runs donor cell on nghost 1 (comment :114).
- Limits / known issues: none recorded.

### Scheme: PLM (van Leer harmonic-mean slope)
- Summary: wl/wr = w_i -+ dwm/2 with dwm = 2 dwl dwr/(dwl+dwr) where dwl dwr > 0, else 0. Switch: `type: plm`.
- Derivations:
  - Harmonic-mean (van Leer) slope and TVD property: re-derive from src/recon/plm.cpp:19-29@dae902b (PR #212 body states only the 0/0 guard, sources/gh__PR_BODIES_202-219.md:243-260; not a derivation).
- Figures: slope cartoon with left/right differences and the harmonic mean; the dw2 <= 0 extremum case.
- Code:
  - src/recon/plm.cpp:10 — `PLMInterpImpl::forward` — vectorised; guard `torch::where(dw2 > 0, ...)` (:26).
  - src/recon/interp_simple.hpp:57 — `interp_plm` — scalar reference used by tests.
  - src/recon/interp_simple.hpp:12-33 — `minmod`, `superbee`, `vanleer`, `mclimiter` — defined, unused anywhere in src.
- Tests:
  - tests/test_plm.cpp (test_plm.<build>) — `interp_plm` (1e-10), `interp_plm_torch1..3`, `interp_plm_round_off_slopes_stay_finite` (finite, bitwise equal to the scalar form in double; added by PR #212), constant field preserved.
- Limits / known issues: the "limiters" in interp_simple.hpp are dead code; PLM is reported worse than WENO5 on the tall rest column (sources/canoe__tall_column_instability_TECH_REPORT.md §3f).

### Scheme: Linear centred polynomials cp3 / cp5 (and cp2/cp4/cp6 helpers)
- Summary: cp3 (1/3, 5/6, -1/6) and cp5 (-1/20, 9/20, 47/60, -13/60, 1/30) face values from cell averages; used
  directly (`type: cp3|cp5`) or as interp2 of weno3/weno5. Switch: `type`.
- Derivations: weights as face values of the interpolating polynomial of cell averages: re-derive from
  src/recon/cp3.cpp:12-16@dae902b and src/recon/cp5.cpp:12-17@dae902b (no source derivation).
- Figures: 3- and 5-cell stencils with weights; mirrored weights for the other face (`cm.flip`).
- Code:
  - src/recon/cp3.cpp:12 — `Center3InterpImpl::reset` — cm/cp weights; :18 `left` via `call_poly3`.
  - src/recon/cp5.cpp:12 — `Center5InterpImpl::reset`.
  - src/recon/interp_simple.hpp:73, :110 — `interp_cp3`, `interp_cp5` scalar references.
  - src/recon/recon_dispatch.cpp:14 — `call_poly_cpu<N>`; :41 `call_poly_mps` (unfold+matmul); src/recon/recon_dispatch.cu:96 `call_poly_cuda` (tiled above 1024 cells, :20).
- Tests: tests/test_weno.cpp (test_weno.<build>) — `interp_cp5m_torch1..3`, `interp_cp5p_torch4` (EXPECT_NEAR 1e-6/1e-10); tests/test_weno5_cuda_line.cpp (test_weno5_cuda_line.<build>, CUDA only) — line > 1024 matches CPU, diff < 1e-12 (issue #251).
- Limits / known issues: interp_bp*/cp2/cp4/cp6/inflection helpers in interp_simple.hpp are unused by the solver.

### Scheme: WENO3 / WENO5 (Jiang–Shu weights, eps 1e-6, optional scaling)
- Summary: nonlinear weights alpha_k = d_k/(beta_k + 1e-6)^2 (d = 2/3,1/3 or 0.3,0.6,0.1); with `scale: true`
  the stencil is normalised by its mean |value| first. Applies to density and tracers (and to all rows when
  shock: true). Switch: `type: weno3|weno5`, `scale` (default false).
- Derivations: candidate polynomials, smoothness indicators and linear weights: re-derive from
  src/recon/weno5.cpp:10-24@dae902b and src/recon/interp_impl.h:74-122@dae902b (no source derivation). Note the
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

### Scheme: PPM
- Summary: registered as `type: ppm` but throws at runtime. Switch: `type: ppm`.
- Derivations: none (not implemented).
- Figures: none.
- Code: src/recon/ppm.cpp:14 — `PPMInterpImpl::forward` throws "not implemented"; src/recon/interp_simple.hpp:67 `interp_ppm` returns phi.
- Tests: none.
- Limits / known issues: a card selecting ppm aborts at the first step; the report should list it as not available.

### Scheme: Riemann solver framework, face-local frame, face-pressure output
- Summary: `RiemannSolverImpl::create` by YAML `dynamics/riemann-solver/type`; solvers project L/R primitives to
  the face-local orthonormal frame (`prim2local*_`) and fluxes back (`flux2global*_`) on the gnomonic grid; LMARS,
  HLLC and Roe also write a face pressure used by the x1 pressure source on curved grids. Switch: YAML
  `type` (default "roe" from YAML), `dir` (default "omni", shallow water).
- Derivations:
  - Face-local frame transforms on the non-orthogonal gnomonic grid: re-derive from src/coord/gnomonic_equiangle.cpp:295-413@dae902b (cross-ref cubed-sphere chapter).
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

### Scheme: LMARS (low-Mach approximate Riemann solver; production default in example decks)
- Summary: rhobar, cbar from averaged gamma and p; pbar = p_avg + (rho c)/2 (uL-uR); ubar = u_avg + (pL-pR)/(2 rho c);
  upwind by sign of ubar; enthalpy flux rho h ubar with h = W->I/rho + KE + p/rho; dry-mass flux carries
  rd = 1 - sum q. Face pressure output = pbar. Switch: `riemann-solver: {type: lmars}`.
- Derivations: linearised acoustic Riemann problem giving pbar/ubar: re-derive from src/riemann/lmars_impl.h:17-78@dae902b (no derivation in sources; the #289 draft only records that scaling the acoustic terms by 0 or 2 changes onset rates by < 2e-5, sources/study__289-covariance_derivations_draft.md §4.4).
- Figures: wave diagram with the single interface state (pbar, ubar); upwind selection of the advected state.
- Code:
  - src/riemann/lmars.cpp:30 — `LmarsSolverImpl::forward` — e = W->I/rho, gamma (aneos via W->L, WL->A), local frame, iterator, global frame.
  - src/riemann/lmars_impl.h:17 — `lmars_impl` — cbar (:36), pbar (:38) and face pressure (:40), ubar (:42), upwind (:47-77).
  - src/riemann/lmars_dispatch.cpp:77 — tensor (MPS) path writes pbar.
- Tests: tests/test_riemann.cpp `lmars_writes_face_pressure_output` (1e-10); tests/test_hydrostatic.cpp and all rest tests run LMARS.
- Limits / known issues: no positivity guard on rhobar*cbar; dissipation independent of HLLC-type wave speeds.

### Scheme: HLLC (PVRS wave speeds)
- Summary: Toro PVRS middle state, shock-corrected wave speeds, contact speed am and pressure cp (clamped >= 0);
  face pressure output = cp. Switch: `type: hllc`.
- Derivations: re-derive from src/riemann/hllc_impl.h:17-130@dae902b (comment cites Toro 10.5.2; no source derivation).
- Figures: three-wave fan (bm, am, bp) with star states.
- Code: src/riemann/hllc.cpp:30 — `HLLCSolverImpl::forward`; src/riemann/hllc_impl.h:17 — `hllc_impl` (pmid :36, cp :70-72); src/riemann/hllc_dispatch.cpp:118 tensor path.
- Tests: tests/test_riemann.cpp `hllc_writes_face_pressure_output` (1e-10).
- Limits / known issues: tall-column study: HLLC reproduces LMARS to < 1% on the rest ladder (sources/canoe__tall_column_instability_TECH_REPORT.md §3f).

### Scheme: Roe (ideal gas and ideal-moist)
- Summary: Roe averages, eigen-decomposed upwinding without an entropy fix; ideal-moist Roe gamma from mass-fraction
  weighted feps/fsig and energy offsets u0; face pressure = 1/2(pL+pR+rhobar cs (uL-uR)). Switch: `type: roe`.
- Derivations: re-derive from src/riemann/roe_impl.h:24-213@dae902b (moist gamma :87-89, face pressure :119-121).
- Figures: Roe average state and the three characteristic families plus species contact.
- Code: src/riemann/roe.cpp:14 — `RoeSolverImpl::forward`; src/riemann/roe_impl.h:24 `roe_impl`; src/riemann/roe_dispatch.cpp:153 tensor path face pressure.
- Tests: tests/test_riemann.cpp `roe_writes_face_pressure_output` and `_ideal_moist` (1e-10).
- Limits / known issues: no entropy fix; no local-frame projection (see framework).

### Scheme: Shallow-water Roe and plume-roe
- Summary: shallow-roe for `shallow-water` EOS (direction mapping by `dir`); plume-roe is a Lax–Friedrichs flux of the
  plume equations. Switch: `type: shallow-roe | plume-roe`, `dir: omni|...`.
- Derivations: re-derive from src/riemann/shallow_roe_impl.h:15-78@dae902b; plume-roe from src/riemann/plume_roe.cpp:14-43@dae902b.
- Figures: none essential (one-line table of supported pairs EOS x solver).
- Code: src/riemann/shallow_roe.cpp:26 — `ShallowRoeSolverImpl::forward` (refuses face pressure); src/riemann/plume_roe.cpp:45.
- Tests: tests/run_shallow_xy.cmake, run_shallow_splash.cmake (reference examples, FULL_TESTS only); test_shallow_xy.py / test_shallow_splash.py.
- Limits / known issues: shallow water skips the WB reference, the x1 face pressure and the flux covariance (hydro_forward.cpp:272, :410-412, :103). plume-roe is dead (see framework).

### Scheme: Single-valued x1 seam fluxes (process-seam averaging)
- Summary: at an internal x1 seam across processes, both ranks exchange the face flux slab (+ face pressure,
  + background mass flux F^R for cell gravity work) and set both to the average, so sums telescope. Same-process
  seams are not averaged (after the reference ghost exchange the two face states already agree). Switch: none;
  active when `layout.pz > 1` with a process group.
- Derivations: re-derive from src/hydro/hydro_forward.cpp:434-508@dae902b (code comment and PR #259 text only,
  sources/gh__PR_BODIES_227-259.md:645-653).
- Figures: two ranks sharing one face, each with its own flux, exchange and average; packing of flux+face pressure+F^R into one tensor.
- Code: src/hydro/hydro_forward.cpp:448-508 — seam exchange (tags 0x7720/0x7721), pack/unpack (:469-482).
- Tests: tests/test_x1_seam_split_mp.cpp (test_x1_seam_split_mp_*.<build>, torchrun 2 ranks, CMakeLists :77-87) — the x1 seam split across 2 ranks matches one block for the switch arms; tests/test_pref_local_seam.cpp (in-process, see Ch5).
- Limits / known issues: averaging masks, rather than removes, any disagreement of the two reconstructions; multi-process x1 seams of the WB reference are covered only through these split tests (docs/wb-ref4.md §12).

### Scheme: Geometric (curvature) sources, spherical-polar; momentum flux form
- Summary: x1 momentum: centrifugal rho(v2^2+v3^2) coord_src1_i plus a pressure force built from the Riemann face
  pressures so that the NET radial pressure force is the plain difference -(p+ - p-)/dx1f (balances g h <rho> of
  the scan); x2/x3 momentum: angular-momentum form using the x1 face fluxes of IVY/IVZ weighted by
  coord_src2_i, plus cot(theta) terms with the cell pressure (p* under SNAP_FLUX_COVARIANCE). Fallback without a
  face pressure: 2 p coord_src1_i. Switch: none (geometry type `spherical-polar`).
- Derivations:
  - Metric coefficients coord_src1_i = (r+^2-r-^2)/2 / ((r+^3-r-^3)/3), coord_src2_i = dx1/((r-+r+) V_r), coord_src1_j/2_j/3_j: re-derive from src/coord/spherical_polar.cpp:78-104@dae902b.
  - Plain-difference radial pressure force with face pressures in the flux: stated (not derived) in docs/x1-centroid-spherical.md §1 item (iii); re-derive from src/coord/spherical_polar.cpp:265-274@dae902b.
  - Angular-momentum-conserving x1-flux form of the IVY/IVZ sources: re-derive from src/coord/spherical_polar.cpp:286-307@dae902b (no source).
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

### Scheme: Geometric sources, gnomonic cubed sphere; exact cell volume and solid angle
- Summary: same face-pressure plain-difference x1 force; src2/src3 with x_ov_rD, y_ov_rC metric coefficients and
  the non-orthogonal cosine terms; exact gnomonic solid angle and exact radial volume (unconditional since PR #293).
  Switch: none (`gnomonic-equiangle`).
- Derivations:
  - Exact solid angle and radial integral: exists docs/289-covariance-x3-curved.md §8.1-8.4.
  - Source terms with g23 != 0: re-derive from src/coord/gnomonic_equiangle.cpp:415-473@dae902b (no source derivation; cross-ref cubed-sphere chapter).
- Figures: gnomonic cell corner-sum solid angle; covariant vs contravariant components at a face.
- Code: src/coord/gnomonic_equiangle.cpp:128-137 (solid angle), :207 `face_area1`, :219 `cell_volume`, :142-145 `x_ov_rD_kji`/`y_ov_rC_kji`, :415 `forward` (src1 :443-460, src2 :463-465, src3 :468-470); :36 x1v = arithmetic mid-radius.
- Tests: tests/test_hydrostatic.cpp (test_hydrostatic.<build>) — six-panel isentropic shell, non-hydrostatic 0, 100 steps, max |v1| < 1e-8 (fixed constant); tests/test_cubed_sphere_cell_volume.py; tests/test_coordinate.cpp `radial_source_uses_face_pressure_in_x1_momentum` (1e-8), `radial_source_preserves_face_pressure_gradient` (1e-6).
- Limits / known issues: x1v is the mid-radius on gnomonic, so a cell-average reading and the gnomonic delta are consistent only if ICs are cell averages (docs/289-covariance-x3-curved.md §4C item 2); SNAP_X1_CENTROID_EXACT does nothing on this grid (docs/x1-centroid-spherical.md §7).
- Discrepancies: PR #293 says the switch-off bitwise property does not hold on gnomonic because the volume change is unconditional (sources/gh__PR_BODIES_285-293.md:240-256) — consistent with code; record for the reader.

### Scheme: x2/x3 face-flux covariance and centroid correction (SNAP_FLUX_COVARIANCE, #289/#293)
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

### Scheme: x1 rho-w mass-flux covariance (SNAP_X1_MASS_COVARIANCE)
- Summary: inside the WB x1 path only, the cell velocity handed to the reconstruction is w_c - (dx1f^2/12) rho_1 w_1 / rho
  (centred derivatives over x1v; rho_1 one-sided second order in the first/last cell at a reflecting wall; ghost w
  refilled as odd mirror), and the full velocity is restored after reconstruction. Rest unchanged (w_1 = 0).
  Switch: env `SNAP_X1_MASS_COVARIANCE`, default off (src/hydro/hydro_forward.cpp:39-47).
- Derivations:
  - The Favre offset w_c = <w> + dz^2/12 rho_z w_z/rho and the extra face mass flux: exists docs/curved-gravity-work-weight.md §11.4 (short) and sources/study__289-covariance_derivations_draft.md §4.1 (with the entropy effect, small in the cell form, harmless in the face form).
  - Wall closure (one-sided rho_1, odd ghost refill) and the use of the Cartesian dx1f^2/12 on curved grids: re-derive from src/hydro/hydro_forward.cpp:324-353@dae902b (commit e04b783 message only).
- Figures: column with rho decreasing, w varying: cell Favre velocity vs cell-average w; corrected velocity profile with mirrored ghosts.
- Code: src/hydro/hydro_forward.cpp:39 — `x1_mass_covariance`; :51 `d1_centred`; :324-353 correction; :361 restore.
- Tests: none in tests/ (grep: the switch appears only in hydro_forward.cpp and docs/curved-gravity-work-weight.md).
- Limits / known issues: not applied when the WB path is off (no gravity, shallow water); uses dx1f^2/12 (Cartesian moment) even on spherical-polar; the doc's "ONSET PLACEHOLDER" is unfilled — no evidence of effect at dae902b.

---

## Chapter 5: Hydrostatic and well-balanced treatment

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

### Scheme: Well-balanced x1 reconstruction (perturbation about a hydrostatic reference)
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
    the degeneracy rho'/rho = p'/p from src/hydro/hydro_ref_x1_impl.h:74-108@dae902b).
  - Positivity fallback choice (adjacent density, not dsf): evidence only (test_face_floor; PR #221 body); describe
    from src/hydro/hydro_forward.cpp:362-386@dae902b.
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

### Scheme: Hydrostatic reference kernel — face-pressure scan, cell pressure, density reference ("smooth5")
- Summary: top-down scan psf_{i-1/2} = psf_{i+1/2} + g rho_i dx1f_i from a top anchor (block top: p_top exp(-g dz/2 / (p/rho)_top); x1-split: anchor relayed from the block above); cell pressure pref = six-face quintic cell average (11,-93,802,802,-93,11)/1440 on uniform grids with one-sided wall rows and a [lo,hi] guard, log-mean dp/ln(lo/hi) on non-uniform grids; dref = pref * B(rho/p), dsf = psf_lo * mean of two smoothed values, B = (1,4,6,4,1)/16. Uniformity: relative spread of dx1f < 1e-10. Switch: none (always with WB).
- Derivations:
  - Scan = discrete hydrostatic balance; six-face quadrature O(dz^6); binomial bias dz^2/2 R'': exists docs/wb-ref4.md §1, §2, §6; wall-row weights in sources/gw__NEXTPR_spec_wbref_exact.md §1(b).
  - Six-face interior weights and the one-sided wall rows w6e: stated (not derived) in docs/wb-ref4.md §1 and sources/gw__NEXTPR_spec_wbref_exact.md §1(b); docs/wb_ref4_weights.py does not check them; re-derive from src/hydro/hydro_ref_x1_impl.h:141-180@dae902b.
  - Log-mean exactness for an isothermal cell: stated docs/wb-ref4.md §5; re-derive from src/hydro/hydro_ref_x1_impl.h:181-186@dae902b.
  - Top anchor half-cell isothermal extrapolation: re-derive from src/hydro/hydro_ref_x1_impl.h:31-38@dae902b.
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

### Scheme: Wall clamp and the wall continuation of the default reference (wb-wall-clamp, linear/ln closure)
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

### Scheme: Reference continuity across x1 seams (anchor relay and ghost-row exchange)
- Summary: the block owning x1-outer anchors at the domain top; each block below receives the running seam-face
  pressure and passes on its bottom-face pressure (serial top-down relay, in-process through a board, remote
  through the process group); then (pref, dref) ghost rows are overwritten with the neighbour's interior rows
  (SNAP_WB_REF4 cell part before, face part after the exchange). Switch: none (x1 split, non-periodic, pz > 1).
- Derivations: re-derive from src/hydro/hydro.cpp:490-626@dae902b (PR #259 body and code comments only; issue #254 thread).
- Figures: stack of x1 blocks with the anchor arrow passing down and ghost rows copied across each seam.
- Code: src/hydro/hydro.cpp:506-514 (`take_x1_anchor`), :559 (`pass_x1_anchor`), :574-621 (ghost-row exchange, tags 0x7717/0x7718); src/layout/layout.cpp:879, :907.
- Tests:
  - tests/test_pref_local_seam.cpp (test_pref_local_seam.<build>) — `local_blocks_restart_the_reference_at_the_seam` (pref under seam equal to one block within 1e-6), `in_process_split_matches_one_block_after_200_steps` (relative state difference <= 1e-12; source PR #259).
  - tests/test_x1_seam_split.cpp arms (Ch5 switches) and tests/test_x1_seam_split_mp.cpp.
- Limits / known issues: the relay is serial along the column (latency grows with nb1); periodic x1 not relayed.
- Discrepancies: test_pref_local_seam.cpp header comments still say "RED on main ... This test does not fix it"; at dae902b both tests are expected to pass (PR #259).

### Scheme: Hydrostatic mode (non-hydrostatic < 1): gravity replaced by the discrete pressure gradient
- Summary: vertical force = nh * rho g (const-gravity forcing) + (1 - nh) * rho_grav, with rho_grav = (pL_{i+1/2} - pR_{i-1/2})/dx1f
  from the cell's own reconstructed face pressures (and the same energy work); under SNAP_X1_CENTROID_EXACT the
  r^2 operator (A pL - A pR)/V - S_i. Switch: YAML `forcing/const-gravity/non-hydrostatic` in [0,1], default 1
  (src/forcing/const_gravity.cpp:25-26).
- Derivations: cancellation at rest against the plain-difference pressure force: stated docs/x1-centroid-spherical.md §4 (last part); otherwise re-derive from src/hydro/hydro_forward.cpp:398-406, :524-548, :910-915@dae902b and src/forcing/const_gravity.cpp:45-51@dae902b.
- Figures: cell with face pressures pL(top), pR(bottom) and the replaced gravity arrow.
- Code: src/hydro/hydro_forward.cpp:399-406 (rho_grav), :524-548 (centroid-exact form), :911-915 (applied to IVX and IPR); src/forcing/const_gravity.cpp:45 `ConstGravityImpl::forward`.
- Tests: tests/test_hydrostatic.cpp (nh 0); tests/test_x1_centroid_rest.py (nh 1 and 0); tests/test_x1_seam_split.cpp (both).
- Limits / known issues: interaction with gravity-work forms is in the gravity-work chapter (original_gravity_work, hydro_forward.cpp:859-866).

### Scheme: balance_column — projection of a ghost-free column onto the scheme's discrete balance
- Summary: iterate p_i <- pref_i(p) + C, rho_i <- p_i/(p/rho)_0 at fixed p/rho (fixed T for ideal mixtures), gauge C
  read at the top cell, until max|p' - C|/(rho g dz) < rtol (default 1e-10, max_iter 120); applies the switched cell
  pressure under SNAP_WB_REF4 on non-uniform grids; requires wall_clamp, nx1 >= 5, positive p and rho; under
  SNAP_X1_CENTROID_EXACT only geometry "cartesian". Switch: API (C++ and Python `balance_column`), used by IC
  builders (examples/bryan.cpp:211).
- Derivations: fixed-point property and the transfer of pref from a ghost-free column to a clamped block: described in the header src/hydro/balance_column.hpp:12-106 (not a derivation; no convergence proof); re-derive from src/hydro/balance_column.cpp:15-109@dae902b.
- Figures: residual vs sweep; column moved by the free gauge C (top fixed).
- Code: src/hydro/balance_column.cpp:15 — `balance_column` (clamp check :30, centroid check :35, nc1 >= 5 :47, uniform test :66-68, ref4 :73-79, loop :85-104, gauge :92); python/csrc/pyhydro.cpp:49 binding.
- Tests:
  - tests/test_balance_column.cpp (test_balance_column.<build>, plus _wb_ref4 and _x1_centroid arms) — ghost-free column reproduces the block's own pref/dref bitwise (dsf except bottom cell); without clamp they disagree; marched column comes out at rest (residual < 1e-10); last allowed update can converge (issue #278 item 5 / PR #279); T and other channels fixed (1e-14); fixed point; thin-block column independence; refusals; centroid switch implies ref4 predicate; moist column; centroid switch balances only Cartesian.
  - tests/run_bryan_balance_ic.cmake (test_bryan_balance_ic) — moist IC converges, capped run reports the cap error, dry case does one projection.
- Limits / known issues: the balanced column moves by a free constant (2.5e-4 to 1.2e-2 of p quoted in the header); per-block uniform classification must match; moist callers must iterate with saturation adjustment.

### Scheme: SNAP_WB_REF4 — fourth-order, cell/face-consistent density reference (and non-uniform cell pressure)
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

### Scheme: SNAP_X1_CENTROID_EXACT — r^2-exact x1 maps on spherical-polar
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

### Scheme: The 1/R remainder on spherical-polar (what is left after the corrections)
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

### Scheme (legacy box): isentropic wall ghosts and zero-gradient wall faces
- Summary: `_revise_x1inner/outer_ghost` (isentropic extrapolation into ghosts) is defined but its call is commented out; `_revise_x1inner/outer_lr` (copy right-state p, rho to left at the wall face) runs only on the non-WB x1 path with gravity on. Switch: none.
- Derivations: none needed beyond describing as legacy; re-derive from src/hydro/hydro.cpp:429-481@dae902b if kept.
- Figures: none.
- Code: src/hydro/hydro.cpp:429, :436, :443, :463; src/hydro/hydro_forward.cpp:256-259 (commented call), :389-392.
- Tests: none.
- Limits / known issues: effectively unreachable for non-shallow EOS with gravity (wb_x1 true there).
