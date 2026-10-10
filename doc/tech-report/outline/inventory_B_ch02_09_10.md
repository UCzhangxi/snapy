# Outline inventory, chapters 2, 9 and 10

Pinned code: snapy `dae902b` (all `src/...`, `tests/...`, `examples/...`, `docs/...` paths below are at `@dae902b`).
kintera: `4dc613d` (cited as `kintera <path>:<line>@4dc613d`). pyharp (integrator only): `4721715`.
ctest names: `setup_test(x)` registers `x.<build>`, written here as `x.release`; `snapy_add_python_test(x)` registers `x_python`.

Conventions used throughout (verified in code):
- Index layout `IDN=0, IVX..IVZ=1..3, IPR=4, ICY=5`; `NMASS>0` (legacy Athena++ order) is refused by a static_assert — `src/snap.h:52`; `NMASS` is a CMake parameter, default 0 — `cmake/parameters.cmake:3`.
- Conserved `hydro_u = [rho_d, m_1, m_2, m_3, E, rho_1..rho_ny]`: slot `IDN` holds the **dry** density, the species slots hold partial densities, momenta are covariant (`coord_vec_lower_`), `E` = internal energy (with reference offsets) + kinetic energy. Primitive `hydro_w = [rho, v^1..v^3, p, y_1..y_ny]`: `IDN` holds the **total** density, velocities are contravariant, species are mass fractions (e.g. `src/eos/moist_mixture.cpp:93`, `:124`).
- Passive scalars are per dry air: `scalar_s = hydro_u[IDN] * r` (`src/mesh/meshblock.cpp:27`, `:470`).

---

## Chapter 2: Governing equations and thermodynamics

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

### Scheme: Conservation laws and operator ordering in one RK stage
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

### Scheme: EquationOfState interface, options and type dispatch
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

### Scheme: Ideal gas EOS
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

### Scheme: Ideal-moist EOS (constant heat capacities, zero-volume condensates, reference energies)
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

### Scheme: Moist-mixture EOS (kintera-backed)
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

### Scheme: ANEOS (tabulated EOS through an external library)
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

### Scheme: Shallow-water EOS
- Summary: `nvar = 4` (h, m); `WA->L` returns `sqrt(h)` (gravity folded into h); `W->T` and `W->A` return undefined
  tensors. Switch: `type: shallow-water`.
- Derivations: none needed (cross-ref the shallow-water test chapter).
- Figures: none.
- Code: `src/eos/shallow_water.cpp:14` — `ShallowWaterImpl::compute`; `:38` `_cons2prim`.
- Tests: `tests/run_shallow_xy.cmake`, `tests/run_shallow_splash.cmake` (`test_shallow_xy`, `test_shallow_splash`, only with `FULL_TESTS`, `tests/CMakeLists.txt:365-369`).
- Limits / known issues: forcings receive an undefined `temp` (`src/hydro/hydro_forward.cpp:768`); only forcings that ignore temp are usable.
- Discrepancies: none.

### Scheme: Conserved/primitive limiter — floors (density, pressure, temperature) and limiter marks
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

### Scheme: EOS ↔ solver consistency conditions (temp2inteng and friends)
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

### Scheme: Saturation adjustment (kintera UV equilibrium) — thermodynamic side
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

## Chapter 9: Diffusion, viscosity, sedimentation and forcing

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

### Scheme: Forcing framework and registration
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

### Scheme: User stage forcings
- Summary: TorchScript/Python modules registered on the MeshBlock receive the stage variables and return
  `hydro_du`/`scalar_ds`, added after the native tendencies. A user dry-density change carries tracers. Switch:
  `MeshBlockImpl::set_user_stage_forcings` (API, no YAML).
- Derivations: none (tracer carry: Ch. 10).
- Figures: interface diagram (inputs dict → module → `{hydro_du, scalar_ds}`).
- Code: `src/mesh/meshblock.cpp:96` — `set_user_stage_forcings`; `:38` `stage_forcing_variables`; `:50` `stage_forcing_result`; `:725-751` application and dry carry.
- Tests: `tests/test_jit_user_forcing.py` (`test_jit_user_forcing_python`); `tests/test_stage_forcing_dry_tracer.py` (`test_stage_forcing_dry_tracer_python`) — tracer ratio deviation ≤ 1e-12, bounds [−1e-12, 1+1e-12].
- Limits / known issues: a user forcing that converts through the limited EOS can mark a redo (PR #226).
- Discrepancies: none.

### Scheme: Constant gravity forcing (source terms only)
- Summary: `du[m_d] += dt rho g_d (non-hydrostatic factor on x1)`, `du[E] += dt rho v_d g_d`. The x1 energy term is the
  "cell" gravity work. Switch: `forcing/const-gravity/{grav1,grav2,grav3,non-hydrostatic,gravity-work,gravity-work-fixer}`;
  defaults 0, 0, 0, 1, "cell", true-if-cell (`src/forcing/const_gravity.cpp:22-36`).
- Derivations: cross-ref the gravity-work chapter (`docs/derivations/curved-gravity-work-weight.md@dae902b` etc.).
- Figures: none here.
- Code: `src/forcing/const_gravity.cpp:12` `from_yaml`; `:46` `ConstGravityImpl::forward`.
- Tests: `tests/test_forcing.cpp:870`, `:920`, `:978`, `:1108` (gravity-work family; other chapter).
- Limits / known issues: `non_hydrostatic` scales only the x1 terms.
- Discrepancies: none.

### Scheme: Coriolis (123 and xyz forms, cubed-sphere covariant)
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

### Scheme: Isotropic viscosity and heat conduction (forcing/diffusion)
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

### Scheme: Diffusion face coefficient at walls and ghosts (one-sided wall extrapolation)
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

### Scheme: x1 profiles of the kinematic coefficients (nu_scale_x1, kappa_scale_x1) and the product face coefficient
- Summary: a positive x1 profile `s(x1)` multiplies `nu_iso`/`kappa_iso`, given as a YAML/Python table (linear between
  knots, held beyond them, interpolated onto cell centres incl. ghosts) or as a per-cell Python tensor (only when x1 is
  one block). On x1 faces the coefficient is the mean of the products `(s_a q_a + s_b q_b)/2`; x2/x3 faces keep
  `mean(q) * s` bit for bit. Profiles are frozen at construction (identity, version and value checks). Switch: YAML
  `nu_scale_x1: {x1: [...], scale: [...]}`, `kappa_scale_x1`; Python `nu_scale_x1[_table]`, `kappa_scale_x1[_table]`;
  refused with `dynamic: true`.
- Derivations:
  - Product of means vs mean of products; second-order spurious tendency of the former on a constant dynamic coefficient. exists: `docs/derivations/diffusion-face-coefficient.md@dae902b` (with `docs/derivations/diffusion_face_coefficient.py`). The copy `sources/deriv__diffusion-face-coefficient.md` is the older `4d3b4d7` version, which lacks the x2/x3 bitwise clause.
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

### Scheme: Body heating, top cooling, bottom heating
- Summary: `body-heat`: `du[E] += dt * dTdt * rho cv` where `pmin <= p <= pmax`. `top-cool`/`bot-heat`: a flux
  `F/(dz*depth)` spread over `depth` cells at the physical upper/lower x1 boundary only. Switch:
  `forcing/body-heat/{dTdt 0, pmin 0, pmax 1}`; `top-cool/{flux ≤ 0, depth 1}`; `bot-heat/{flux ≥ 0, depth 1}`.
- Derivations: trivial; re-derive from `src/forcing/body_heat.cpp:43-55`, `src/forcing/top_cool.cpp:42-55`, `src/forcing/bot_heat.cpp:42-55`.
- Figures: column cartoon with heated/cooled boundary slabs.
- Code: `src/forcing/body_heat.cpp:15`, `:43`; `src/forcing/top_cool.cpp:16`, `:42`; `src/forcing/bot_heat.cpp:16`, `:42`.
- Tests: `tests/test_forcing.cpp:1246` `body_heat_uses_pressure_mask_and_mixture_cv`; `:1269` `boundary_fluxes_scale_with_timestep`.
- Limits / known issues: top-cool/bot-heat use `dx1f` of the boundary cell for all `depth` cells (exact only on a uniform grid near the boundary).
- Discrepancies: none.

### Scheme: Bottom relaxation (temperature, velocity, composition)
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

### Scheme: Sponge layers (top and bottom)
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

### Scheme: Plume forcing (unreachable)
- Summary: entrainment/buoyancy sources for a plume EOS. Installed only if `eos/type == plume-eos`, a type that
  `EquationOfStateImpl::create` rejects (removed in #282). Switch: `forcing/plume-forcing` (still accepted).
- Derivations: none.
- Figures: none.
- Code: `src/forcing/plume_forcing.cpp:29`; `src/hydro/register_forcing_modules.cpp:77`; `src/hydro/hydro_options.cpp:116`.
- Tests: none.
- Limits / known issues: dead code.
- Discrepancies: PR #217 lists `plume-forcing` as a valid key. It is accepted but cannot be installed at the pin.

### Scheme: Sedimentation of condensates (recommended to move to Ch. 10)
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

### Scheme: Turbulence (not built)
- Summary: k–epsilon model files from Athena++; not compiled, no YAML key. Switch: none.
- Derivations: none (not built; described in one paragraph only).
- Figures: none (dead code).
- Code: `src/turbulence/k_epsilon_turbulence.cpp:16`, `src/turbulence/turbulence_model.hpp:19`; build glob `src/CMakeLists.txt:35-52` (no `turbulence/`).
- Tests: none.
- Limits / known issues: dead code; snapy has no turbulence closure beyond constant `nu_iso`/`kappa_iso` (with an x1 profile).
- Discrepancies: none.

---

## Chapter 10: Moist physics coupling

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

### Scheme: Saturation adjustment in the step
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

### Scheme: check_redo — causes, reduction, restore (saturation and limiter)
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

### Scheme: Condensate repair by parent-vapour borrow (stoichiometric split)
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

### Scheme: Column vapour repair fix_vapor (volume-weighted, upward fallback) and parentless clouds
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

### Scheme: Positivity-limited species fluxes carry energy and momentum (moist carry)
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

### Scheme: Precipitation and evaporation kinetics (driver-level coupling, kintera rates)
- Summary: after the dynamics stages, the example drivers refresh `hydro_w` from `hydro_u` (so kinetics sees the
  saturation-adjusted state, #257), build concentrations with kintera `ThermoX`, evaluate kintera `Kinetics`
  rates/Jacobian, take one linearised backward-Euler step (`evolve_implicit`), add `del_rho` to the species rows of
  `hydro_u`, and call `check_redo`. Latent heat enters through the EOS reference energies (E untouched). Two-product
  evaporation (NH4SH ⇒ NH3 + H2S) uses the extent-to-equilibrium law in kintera at the pin. Switch: driver-level (cards
  with `type: evaporation` reactions), not a snapy library option.
- Derivations:
  - Steady-diffusion evaporation rate, the two-product extent quadratic, and the no-overshoot property of one implicit step. exists: `sources/canoe__EVAPORATION_MULTIPRODUCT_TECH_REPORT.md` §4 (step-by-step) and the overshoot analysis that follows. Code: `kintera src/kinetics/evaporation.cpp:128`, `:165-191@4dc613d`.
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

### Scheme: Passive scalar (tracer) transport per dry air, with optional upper bound
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

---

## Cross-cutting discrepancy list (code wins)
1. H2-dissociation EOS (source report) is absent at `kintera 4dc613d`; only the PV->T Newton sign fix is there (`kintera src/thermo/thermo_y.cpp:445-447@4dc613d`). Drop the deck citation (ISSUES.md item 4).
2. `on_theta` conduction (PR #253/#259) was removed by #268. The adiabatic-rest drift of issue #252 is open at the pin.
3. Cloud-parent cache: PR #223 says "global registry"; since #235 it uses the thermo's own table.
4. relax-bot-temp at-face: PR #219 says `1.5 T0 - 0.5 T1`; the code uses the coordinate-spacing weight (#279).
5. EOS floor defaults: struct 1e-10/1e-10 vs YAML 1e-6/1e-3.
6. `moist_mixture.hpp:43-54` call-order comment is stale relative to `_ensure_cache`.
7. Evaporation extent law: the report says "not landed"; it is in kintera at the pin.
8. `plume-forcing` is accepted by the YAML whitelist but cannot be installed (plume EOS removed).
9. `sources/deriv__diffusion-face-coefficient.md` is the pre-`e659b69` version; cite `docs/derivations/diffusion-face-coefficient.md@dae902b`.
