# Chapter 15 verification rewrite: evidence

Base: `3f80d8fd0e713099fc0b21e0e2166280b39fe11d`, from `git rev-parse HEAD` before editing.
Remote `tech-report` still named that commit when checked by `git ls-remote origin refs/heads/tech-report`
at 2026-10-13T04:37:47Z. Code pin: `6fbb39750f62b83df096058a4746e77d0a634bc5`, read from `code_pin.yml`.
All source locations in the ledgers below refer to that full code pin and were read from its extracted git tree.
The chapter uses symbol shortcodes; line ranges below are the resolved enclosing definitions, not hand-maintained book citations.

## Existing work and scope

`gh pr list --state open --limit 100 --json number,title,headRefName,files` was run on both
UCzhangxi/snapy and happysky19/snapy. The former has overlapping chapter-15 citation work in PR #56;
the latter has no open PR. Branch lists were checked with `gh api --paginate repos/OWNER/snapy/branches`.
The two explicitly chapter-15 branches were fetched and inspected:

- `happysky19/snapy:tr/ch15-ch04`, `56dc8ddb5d6cd33ff40fc9bcffbe5f2dfa488ed0`: its spatial catalogue and data are already incorporated.
- `happysky19/snapy:tr/ch15-tables`, `11a7edc182e2f3205e1a2f8848f3f956e17fc898`: its captions are already incorporated.

The rewrite retains the eight existing catalogue topics and section identifiers, and the earlier spatial-check
coverage. It condenses repeated suite rows into selected assertion-level evidence, rather than promising an exhaustive
CTest inventory. The original detailed spatial formula tables are expressed as three report-check rows and connected
prose; their derivations and executable checks remain in chapter 4. PR #56's applicable enclosing-definition mappings
were rechecked against the pin rather than replaying unrelated chapter edits. No source symbol was renamed or removed
by this work; no code pin changed.

## Content changes

| topic | before | after / reason |
|---|---|---|
| Evidence interpretation | Assertions, old run logs and ports mixed | Separate source contracts, formula checks and runtime results; add complete conservation/drift/order derivations |
| Overview | Old line citations, dispersed assertion notes | Definition-level ledger; preserve import, restart, redo, forcing, exchange and CUDA-line checks |
| Thermodynamics | Mixed pin and offset descriptions | Current conversion/cache/offset, temperature-affinity, registry and phase-change contracts |
| Geometry | Duplicated seam rows and historical measurements | Current geometry, local seam and two-rank contracts; corrected-work on/off distinction |
| Spatial | Constant preservation described as exact; stale render-tool claims | State library-default allclose; retain independent reconstruction/covariance/operator coverage |
| Well-balanced | Old CPU run presented beside newer assertions | Current assertion criteria only; distinguish two-grid regression from asymptotic order evidence |
| Moist | Parent tolerances easy to read as dtype alternatives | Mass and parent checks apply in the same case; net-deficit return is code 1, not a boolean success |
| Boundaries | Mixed-pin curved-energy discussion | Both current curved geometries; explicit distinction between measured quantity and top-level acceptance |
| Configuration | Duplicated historical numerical rows | Package origin, option guards and nonempty seam-filter checks; numerical rows live with their mechanism |
| Symbols | No verification-metric definitions | Flag local `\psi_{15}`, `\zeta_{15}`, and outward unit normal `\mathbf n` in ISSUES; existing meanings retained |
| Generated notation | No first-use entries for interior set/oracle | Generator updates two first-use cells; no hand edit |

No new compiled snapy execution is claimed. No installed snapy package was used and no source build was made.
No new environment was created. Checks used the existing Python environment and the existing workspace pytest dependencies.

## Reproduction and paired gates

Environment: Python 3.11.13; NumPy 2.4.6; SymPy 1.14.0; Matplotlib 3.10.9; pytest 9.1.1;
Universal Ctags 6.2.1. Commands below run from `doc/tech-report`, with `PYTHONPATH=src` plus the existing
pytest dependency directory, `SNAPY_REPO` pointing to the local checkout holding the pin, and `CTAGS` pointing
to the existing 6.2.1 binary. A workspace cache supplies pinned source and citation objects.

| command / gate | base | rewrite |
|---|---|---|
| `python -m pytest tools/tests -q` | 169 passed, 3 skipped | 169 passed, 3 skipped |
| `python tools/ratchet_gate.py check` (history/offpin/status/xref) | 172/509/0/14 | 95/403/0/14; pass with lowered baseline |
| same, chapter 15 | 77/106/0/4 | 0/0/0/4 |
| `python tools/code_anchors.py check` | 2707 occurrences, 624 distinct, 0 unresolved | 2753 occurrences, 637 distinct, 0 unresolved |
| `python tools/check_citations.py` with local repo/cache | 935 links, 20 problems | 850 links, 11 problems; no new problem locations |
| `PYTHONPATH=src python -m pytest src/tests -q` | 61 passed, 1 failed | 61 passed, 1 failed; same fixture |
| `python tools/check_glance_boxes.py` | pass | pass |
| `python tools/check_tables.py` | 58 findings at baseline | 58 findings at baseline; ch15 zero |
| `python tools/check_figstyle.py` | 134 sites at baseline | 134 sites at baseline; no added style site |
| `python tools/check_fig_output.py --chapters ch15 --list` | covered by full render-source gate | 1 figure, 0 findings |
| `python tools/render_gate.py book/`: labels | 869; no duplicates | 872; no duplicates |
| same: references | 467; none dangling | 468; none dangling |
| same: tracked-freeze gaps | 14 | 14 |
| same: hand-typed chapter findings | 2 | 0 |
| same: imported figure functions | 134 exist; 0 pending/raising | 134 exist; 0 pending/raising |
| same: actual Quarto rendering | unavailable (`quarto` absent) | unavailable (`quarto` absent) |
| `python tools/gen_test_index.py --check` | current vs stored fixture | current vs stored fixture; fixture remains at its older pin |
| `python tools/gen_derivation_index.py` | not changed | no diff |
| `python tools/gen_notation_index.py` | existing generated index | two first-use cells regenerated |
| `python tools/book_chapters.py` | existing list | no diff |
| `python tools/check_math_spans.py` on chapter-15 files | existing source gate clean | exit 0 |
| `PYTHONPATH=src python src/snapy_report/ch15/checks/metrics_check.py` | absent | 3 exact symbolic claims pass |
| `git diff --check` | clean | clean |

The independent checks are included in the existing `src/tests/test_checks.py` discovery test, so the added
script does not increase the pytest item count. Its committed output is:

```
[C1] PASS volume-weighted telescoping; closed walls zero; unweighted counterexample -1/2
[C2] PASS relative-drift identity for a nonzero positive oracle
[C3] PASS single-power refinement ratio and logarithmic order
3 claims pass
```

The unchanged failing item is `src/tests/test_ch06.py::test_check_current[d_face_work_pe_check]`:
its byte-comparison fixture differs in roundoff digits. The unchanged failure is not represented as a successful test.
Citation problems outside this chapter remain. Quarto absence prevents HTML/PDF rendering and page inspection;
the figure was drawn locally and visually inspected. Runtime CPU/CUDA/rank coverage was not measured.
The generated test-index fixture still describes the older source snapshot; its `--check` success only establishes
agreement with that fixture. This PR does not regenerate another owner's runtime index.

## Verified assertion ledger

Each row below was checked at `6fbb39750f62b83df096058a4746e77d0a634bc5`.
Acceptance constants are source evidence, not observed residuals. Supplemental helpers, registrations and top-level
acceptance sites are listed in the following definition ledger and cited beside the tables in the chapter.

| catalogue | test and verified claim | criterion | enclosing definition at code pin |
|---|---|---|---|
| _ch01 | `test_python_import_path_python`: Imported package is under the supplied root; caller search path survives | exact paths; exit 125 if unconfigured | `tests/test_python_import_path.py:1-23` (`file scope`) |
| _ch01 | `test_restart_cycle_limit`: First resumed cycle and logged totals match the uninterrupted run | absolute $10^{-12}$; termination time $10^{-9}$ | `tests/run_restart_cycle_limit.py:108-200` (`main`) |
| _ch01 | `test_check_redo_parallel.release`: Ranks share the redo decision and restore saved tensors | exact tensor equality | `tests/test_check_redo_parallel.cpp:12-69` (`Mesh.check_redo_is_one_decision_across_ranks`) |
| _ch01 | `test_user_output.release`: Scripted stage forcings add increments in list order | rtol = atol = $10^{-12}$ | `tests/test_user_output.cpp:576-609` (`UserForcing.scripted_stage_forcings_add_tendencies_in_list_order`) |
| _ch01 | `test_mesh_multi_block.release`: Both local and remote neighbour payloads arrive | library-default allclose | `tests/test_mesh_multi_block.cpp:25-96` (`Mesh.multi_block_exchange`) |
| _ch01 | `test_weno5_cuda_line.release`: Long-line CUDA reconstruction agrees with CPU | absolute error below $10^{-12}$ | `tests/test_weno5_cuda_line.cpp:83-100` (`expect_matches_cpu`) |
| _ch02-thermodynamics | `test_eos.release`: Moist-mixture round trip and cache refresh after pressure mutation | rtol = atol = $10^{-6}$ | `tests/test_eos.cpp:122-166` (`DeviceTest.moist_mixture`) |
| _ch02-thermodynamics | `test_eos.release`: Ideal-moist offset scales linearly with the supplied density field | rtol = atol = $10^{-6}$ | `tests/test_eos.cpp:168-191` (`DeviceTest.ideal_moist_internal_energy_offset`) |
| _ch02-thermodynamics | `test_eos.release`: Ideal-gas energy offset is zero | rtol = atol = $10^{-12}$ | `tests/test_eos.cpp:193-207` (`DeviceTest.ideal_gas_internal_energy_offset_is_zero`) |
| _ch02-thermodynamics | `test_eos_temp2inteng_python`: Temperature round trip, affinity and energy intercept | relative $10^{-12}$, $10^{-12}$, $10^{-10}$ | `tests/test_eos_temp2inteng.py:76-164` (`main`) |
| _ch02-thermodynamics | `test_eos_species_registry_python`: Conversions survive global table mutation; step output unchanged | relative below `TOL`; exact step | `tests/test_eos_species_registry.py:80-131` (`main`) |
| _ch02-thermodynamics | `test_wall_saturation.release`: Condensation/evaporation changes cloud mass and preserves energy/water | relative drift below $10^{-12}$ | `tests/test_wall_saturation.cpp:15-77` (`WallSaturation.phase_change_preserves_energy_and_water`) |
| _ch03-grids-geometry | `test_coordinate.release`: Spherical-polar metric matches reference formulas | rtol = atol = $10^{-12}$ | `tests/test_coordinate.cpp:146-221` (`SphericalPolar.geometry_matches_athena_reference_formulas`) |
| _ch03-grids-geometry | `test_coordinate.release`: Decomposed faces reproduce the undecomposed grid | bitwise equality | `tests/test_coordinate.cpp:927-960` (`CoordinateDecomposition.blocks_match_the_undecomposed_grid_bitwise`) |
| _ch03-grids-geometry | `test_radial_face_moments.release`: Face centroid shift and second moment match exact integrals | relative $10^{-14}$ | `tests/test_radial_face_moments.cpp:58-70` (`RadialFaceMoments.closed_forms_match_the_exact_integrals`) |
| _ch03-grids-geometry | `test_cubed_sphere_cell_volume_python`: Shell-volume sum, radial divergence and rest checks | per assertion in `main` | `tests/test_cubed_sphere_cell_volume.py:107-142` (`main`) |
| _ch03-grids-geometry | `test_cubed_sphere_exchange.release`: Subdivided panels agree with one block after a stage | bitwise equality | `tests/test_cubed_sphere_exchange.cpp:159-179` (`CubedSphere.subdivided_panel_exchange_matches_one_block`) |
| _ch03-grids-geometry | `test_flux_covariance_seams_python`: Panel-seam conservation, covariance on, cell gravity work | relative drift below $10^{-12}$ | `tests/test_flux_covariance_seams.py:56-93` (`arm_conservation`) |
| _ch03-grids-geometry | `test_x1_seam_split_radial_exact.release`: Split column matches one block; corrected-energy budget closes | gap 0; drift at most $10^{-13}$ | `tests/test_x1_seam_split.cpp:256-277` (`radial_exact_split_gap`) |
| _ch03-grids-geometry | `test_x1_seam_split_mp_radial_exact.release`: Two ranks agree with local split and one-block states | relative gap at most $10^{-13}$ | `tests/test_x1_seam_split_mp.cpp:253-307` (`X1SeamSplitMp.split_across_two_ranks_matches_one_process`) |
| _ch04-spatial-discretization | `test_plm.release`: Donor cell, PLM and WENO5 preserve a constant in all directions | library-default allclose; exact shape | `tests/test_plm.cpp:200-216` (`DeviceTest.reconstruct_preserves_a_constant_field`) |
| _ch04-spatial-discretization | `test_weno5_cuda_line.release`: Long CUDA line agrees with the CPU reconstruction | absolute error below $10^{-12}$ | `tests/test_weno5_cuda_line.cpp:83-100` (`expect_matches_cpu`) |
| _ch04-spatial-discretization | `test_radial_face_moments.release`: Curved-face moments match the integral oracle | relative $10^{-14}$ | `tests/test_radial_face_moments.cpp:58-70` (`RadialFaceMoments.closed_forms_match_the_exact_integrals`) |
| _ch04-spatial-discretization | `test_flux_covariance_rows_python`: Rest, uniform fraction and offset arms | per arm in `main` | `tests/test_flux_covariance_rows.py:271-315` (`main`) |
| _ch04-spatial-discretization | `test_horizontal_flux_covariance_python`: Horizontal onset ladder and energy budget | per arm in `main` | `tests/test_horizontal_flux_covariance.py:168-206` (`main`) |
| _ch05-well-balanced | `test_hydro_ref_x1.release`: Wall-clamped interior reference ignores ghost perturbations | bitwise equality | `tests/test_hydro_ref_x1.cpp:211-232` (`HydroRefX1Dispatch.wall_clamp_keeps_the_interior_free_of_the_ghosts`) |
| _ch05-well-balanced | `test_wb_ref_wall.release`: Near-wall face errors decrease on refinement | order at least 1.7; reference error at most 1.5 times interior | `tests/test_wb_ref_wall.cpp:223-256` (`faces_next_to_the_walls_are_second_order`) |
| _ch05-well-balanced | `test_wb_ref4_order_python`: Enabled reference has high-order convergence; control remains distinguishable | `ORDER_ON` and `ORDER_OFF` | `tests/test_wb_ref4_order.py:146-179` (`main`) |
| _ch05-well-balanced | `test_x1_centroid_rest_python`: Centroid correction separates rest and non-rest controls | `TOL_ON` and `TOL_OFF` | `tests/test_x1_centroid_rest.py:125-158` (`main`) |
| _ch05-well-balanced | `test_balance_column.release`: Moist column balances without changing species; solver remains at rest | rest below $10^{-10}$; vapour change below $10^{-12}$ | `tests/test_balance_column.cpp:466-514` (`BalanceColumn.a_moist_column_with_one_condensable_comes_out_at_rest`) |
| _ch05-well-balanced | `test_pref_local_seam_flux_covariance.release`: Four local blocks match one block after 200 steps | maximum normalized state gap at most $10^{-12}$ | `tests/test_pref_local_seam.cpp:301-335` (`HydroRefX1.in_process_split_matches_one_block_after_200_steps`) |
| _ch10-moist-coupling | `test_wall_saturation.release`: Wall phase change preserves total energy and water | relative drift below $10^{-12}$ | `tests/test_wall_saturation.cpp:15-77` (`WallSaturation.phase_change_preserves_energy_and_water`) |
| _ch10-moist-coupling | `test_condensate_conservation.release`: Two parents pay the stoichiometric debit; cloud deficit is cleared | mass allclose $10^{-12}$; parents $10^{-6}$; cloud exact | `tests/test_condensate_conservation.cpp:17-54` (`DeviceTest.multi_vapor_condensate_debits_stoichiometric_mass`) |
| _ch10-moist-coupling | `test_eos.release`: Net-deficit column is rejected without changing the state | failure code 1; unchanged vector | `tests/test_eos.cpp:89-98` (`eos_limiter.rejects_column_in_net_deficit_without_writing`) |
| _ch10-moist-coupling | `test_scalar.release`: Transported scalar ratio stays bounded on both sides | float32 $10^{-5}$; float64 $10^{-12}$ | `tests/test_scalar.cpp:109-189` (`DeviceTest.scalar_upper_bound_holds_both_sides`) |
| _ch10-moist-coupling | `test_sedimentation_guards.release`: Rising cloud is taken from below | absolute error at most $10^{-9}$ times reference | `tests/test_sedimentation_guards.cpp:41-88` (`expect_rising_cloud_taken_from_below`) |
| _ch10-moist-coupling | `test_check_redo_parallel.release`: A retry decision and rollback are shared by ranks | exact tensor equality | `tests/test_check_redo_parallel.cpp:12-69` (`Mesh.check_redo_is_one_decision_across_ranks`) |
| _ch11 | `test_radiating_boundary.release`: Characteristic modes on all faces and EOS fixtures | float32 0.03; float64 $10^{-8}$ | `tests/test_radiating_boundary.cpp:46-99` (`DeviceTest.radiating_modes_all_faces`) |
| _ch11 | `test_radiating_boundary.release`: Mixed face fills preserve representation and ordering | hydro rtol $10^{-12}$; atol $10^{-9}$ | `tests/test_radiating_boundary.cpp:177-259` (`radiating.mixed_faces_preserve_representation_and_order`) |
| _ch11 | `test_radiating_boundary.release`: Outflow pulse reflection stays bounded | reflection below 0.05 | `tests/test_radiating_boundary.cpp:395-443` (`radiating.acoustic_pulses`) |
| _ch11 | `test_radiating_boundary.release`: Saved reference continues exactly; missing reference is rejected | exact equality; exception | `tests/test_radiating_boundary.cpp:445-470` (`radiating.restart_continuation_and_missing_reference`) |
| _ch11 | `test_radiating_boundary.release`: CPU and CUDA boundary results agree | rtol = atol = $10^{-10}$ | `tests/test_radiating_boundary.cpp:563-579` (`radiating.cpu_cuda_agreement`) |
| _ch11 | `test_implicit_stratified_solid_python`: Solid-separated fluid segments retain mass and finite state | relative segment-mass drift below $10^{-12}$ | `tests/test_implicit_stratified_solid.py:99-141` (`solid_run`) |
| _ch11 | `test_implicit_stratified_solid_radial_exact_python`: Curved-grid corrected-energy budget closes | relative drift at most $10^{-12}$ | `tests/test_implicit_stratified_solid.py:1-305` (`file scope`) |
| _ch12-configuration | `test_python_import_path_python`: Package origin and search-path ordering are correct | exact paths; exit 125 if unconfigured | `tests/test_python_import_path.py:1-23` (`file scope`) |
| _ch12-configuration | `test_hydro_options.release`: Unsupported implicit schemes are refused | exception | `tests/test_hydro_options.cpp:193-235` (`hydro_options.reject_unsupported_implicit_scheme`) |
| _ch12-configuration | `test_hydro_options.release`: Wall clamp is enabled by default and accepts overrides | boolean equality | `tests/test_hydro_options.cpp:237-259` (`hydro_options.wb_wall_clamp_ships_enabled`) |
| _ch12-configuration | `test_yaml_keys.release`: Unknown geometry cell key is rejected | exception message contains key | `tests/test_yaml_keys.cpp:71-73` (`yaml_keys.geometry_cells_refuses_an_unknown_key`) |
| _ch12-configuration | `test_x1_seam_split_x1_mass_covariance.release`: Two owned cells refused; three accepted | exception/no throw | `tests/test_x1_seam_split.cpp:366-380` (`X1SeamSplit.x1_mass_covariance_needs_3_x1_cells`) |
| _ch12-configuration | `test_x1_seam_split_vic_refuses_split.release`: Implicit column accepts one block and refuses a radial split | exception message | `tests/test_x1_seam_split.cpp:323-344` (`X1SeamSplit.vic_refuses_x1_split`) |

## Complete source-definition ledger

All locations below are at `6fbb39750f62b83df096058a4746e77d0a634bc5`.
File-scope entries have no enclosing function (CMake registrations, top-level Python assertions or fixture
instantiation); their reasons are recorded in `reviews/code-anchors-unmapped.tsv`.

| source range at full code pin | enclosing definition |
|---|---|
| `tests/test_python_import_path.py:1-23` | `file scope` |
| `tests/run_restart_cycle_limit.py:108-200` | `main` |
| `tests/test_check_redo_parallel.cpp:12-69` | `Mesh.check_redo_is_one_decision_across_ranks` |
| `tests/test_user_output.cpp:576-609` | `UserForcing.scripted_stage_forcings_add_tendencies_in_list_order` |
| `tests/test_mesh_multi_block.cpp:25-96` | `Mesh.multi_block_exchange` |
| `tests/test_weno5_cuda_line.cpp:83-100` | `expect_matches_cpu` |
| `tests/CMakeLists.txt:1-590` | `file scope` |
| `cmake/macros/macro_setup_test.cmake:1-34` | `file scope` |
| `tests/run_restart_cycle_limit.py:101-105` | `assert_close` |
| `tests/test_mesh_multi_block.cpp:20-22` | `side_is_uniform` |
| `tests/device_testing.hpp:1-57` | `file scope` |
| `tests/test_eos.cpp:122-166` | `DeviceTest.moist_mixture` |
| `tests/test_eos.cpp:168-191` | `DeviceTest.ideal_moist_internal_energy_offset` |
| `tests/test_eos.cpp:193-207` | `DeviceTest.ideal_gas_internal_energy_offset_is_zero` |
| `tests/test_eos_temp2inteng.py:76-164` | `main` |
| `tests/test_eos_species_registry.py:80-131` | `main` |
| `tests/test_wall_saturation.cpp:15-77` | `WallSaturation.phase_change_preserves_energy_and_water` |
| `tests/test_eos_species_registry.py:29-29` | `TOL` |
| `tests/test_coordinate.cpp:146-221` | `SphericalPolar.geometry_matches_athena_reference_formulas` |
| `tests/test_coordinate.cpp:927-960` | `CoordinateDecomposition.blocks_match_the_undecomposed_grid_bitwise` |
| `tests/test_radial_face_moments.cpp:58-70` | `RadialFaceMoments.closed_forms_match_the_exact_integrals` |
| `tests/test_cubed_sphere_cell_volume.py:107-142` | `main` |
| `tests/test_cubed_sphere_exchange.cpp:159-179` | `CubedSphere.subdivided_panel_exchange_matches_one_block` |
| `tests/test_flux_covariance_seams.py:56-93` | `arm_conservation` |
| `tests/test_x1_seam_split.cpp:256-277` | `radial_exact_split_gap` |
| `tests/test_x1_seam_split_mp.cpp:253-307` | `X1SeamSplitMp.split_across_two_ranks_matches_one_process` |
| `tests/test_flux_covariance_seams.py:122-168` | `main` |
| `tests/test_flux_covariance_seams.py:34-34` | `DRIFT_TOL` |
| `tests/test_plm.cpp:200-216` | `DeviceTest.reconstruct_preserves_a_constant_field` |
| `tests/test_flux_covariance_rows.py:271-315` | `main` |
| `tests/test_horizontal_flux_covariance.py:168-206` | `main` |
| `src/recon/interp_simple.hpp:65-69` | `interp_ppm` |
| `tests/test_hydro_ref_x1.cpp:211-232` | `HydroRefX1Dispatch.wall_clamp_keeps_the_interior_free_of_the_ghosts` |
| `tests/test_wb_ref_wall.cpp:223-256` | `faces_next_to_the_walls_are_second_order` |
| `tests/test_wb_ref4_order.py:146-179` | `main` |
| `tests/test_x1_centroid_rest.py:125-158` | `main` |
| `tests/test_balance_column.cpp:466-514` | `BalanceColumn.a_moist_column_with_one_condensable_comes_out_at_rest` |
| `tests/test_pref_local_seam.cpp:301-335` | `HydroRefX1.in_process_split_matches_one_block_after_200_steps` |
| `tests/test_wb_ref4_order.py:38-38` | `ORDER_ON` |
| `tests/test_wb_ref4_order.py:39-39` | `ORDER_OFF` |
| `tests/test_x1_centroid_rest.py:40-40` | `TOL_ON` |
| `tests/test_x1_centroid_rest.py:41-41` | `TOL_OFF` |
| `tests/test_condensate_conservation.cpp:17-54` | `DeviceTest.multi_vapor_condensate_debits_stoichiometric_mass` |
| `tests/test_eos.cpp:89-98` | `eos_limiter.rejects_column_in_net_deficit_without_writing` |
| `tests/test_scalar.cpp:109-189` | `DeviceTest.scalar_upper_bound_holds_both_sides` |
| `tests/test_sedimentation_guards.cpp:41-88` | `expect_rising_cloud_taken_from_below` |
| `tests/test_radiating_boundary.cpp:46-99` | `DeviceTest.radiating_modes_all_faces` |
| `tests/test_radiating_boundary.cpp:177-259` | `radiating.mixed_faces_preserve_representation_and_order` |
| `tests/test_radiating_boundary.cpp:395-443` | `radiating.acoustic_pulses` |
| `tests/test_radiating_boundary.cpp:445-470` | `radiating.restart_continuation_and_missing_reference` |
| `tests/test_radiating_boundary.cpp:563-579` | `radiating.cpu_cuda_agreement` |
| `tests/test_implicit_stratified_solid.py:99-141` | `solid_run` |
| `tests/test_implicit_stratified_solid.py:1-305` | `file scope` |
| `tests/test_implicit_stratified_solid.py:169-217` | `curved_energy` |
| `tests/test_hydro_options.cpp:193-235` | `hydro_options.reject_unsupported_implicit_scheme` |
| `tests/test_hydro_options.cpp:237-259` | `hydro_options.wb_wall_clamp_ships_enabled` |
| `tests/test_yaml_keys.cpp:71-73` | `yaml_keys.geometry_cells_refuses_an_unknown_key` |
| `tests/test_x1_seam_split.cpp:366-380` | `X1SeamSplit.x1_mass_covariance_needs_3_x1_cells` |
| `tests/test_x1_seam_split.cpp:323-344` | `X1SeamSplit.vic_refuses_x1_split` |
| `tests/test_yaml_keys.cpp:35-55` | `expect_refused` |
| `tests/test_yaml_keys.cpp:57-59` | `expect_refused` |
| `src/coord/coordinate.cpp:509-553` | `CoordinateImpl::divergence` |

## Condensed rows, explicitly not re-certified

The rewrite is a selected assertion catalogue. The following 57 distinct named entries from the old
tables no longer have a standalone row here (normalized `<b>` to `release` for comparison).
Their removal is an editorial condensation, not a claim that the test disappeared or passed.
The mechanism chapters retain their own Tests layers. No replacement runtime evidence is claimed.

| old entry | old catalogue | disposition |
|---|---|---|
| `test_bryan_balance_ic` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_check_redo_floor_python` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_check_redo_saturation_cuda_python` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_check_redo_saturation_python` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_cloud_parent_slots.release` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_cubed_sphere_exchange.cpp:150-200` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_cubed_sphere_vertical_velocity_exchange_python` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_diffusion_moist.release` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_dry_carry_zero_base_python` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_exchange.release` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_exchange_decomp` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_face_floor.release` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_fix_vapor_counts_every_column_python` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_fix_vapor_reports_failure_python` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_fix_vapor_volume.release` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_flip_zero_count.release` | `_ch11.qmd` | Detailed row condensed; no new runtime certification |
| `test_flux_covariance_seams.py:34-93` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_flux_positivity_cubedsphere_flux_covariance_python` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_flux_positivity_cubedsphere_python` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_forcing.release` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_hydro_options.cpp:195-258` | `_ch12-configuration.qmd` | Detailed row condensed; no new runtime certification |
| `test_hydrostatic.release` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_jit_user_forcing_python` | `_ch01.qmd` | Detailed row condensed; no new runtime certification |
| `test_local_horizontal_cells.py:28-37` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_local_horizontal_cells_python` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_mesh_exchange.py:20-50` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_mesh_exchange_python` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_parentless_cloud.release` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_parentless_cloud_nb1.release` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_parentless_cloud_nb1_mp.release` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_pref_local_seam.release` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_process_group.cpp:74-186` | `_ch12-configuration.qmd` | Detailed row condensed; no new runtime certification |
| `test_process_group.release` | `_ch12-configuration.qmd` | Detailed row condensed; no new runtime certification |
| `test_python_import_path.py:7-23` | `_ch12-configuration.qmd` | Detailed row condensed; no new runtime certification |
| `test_radial_face_moments.cpp:49-91` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_radiating_boundary_python` | `_ch11.qmd` | Detailed row condensed; no new runtime certification |
| `test_rectify.release` | `_ch11.qmd` | Detailed row condensed; no new runtime certification |
| `test_sedimentation_cubed_seam.release` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_stage_forcing_dry_tracer_python` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_stencil_cache_small_block_python` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_straka_redo` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_tracer_dry_convention_python` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_two_cards_species.release` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_uranus_cycle1_abort.release` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_vapor_column_nb1.release` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_vic_moist_device_python` | `_ch10-moist-coupling.qmd` | Detailed row condensed; no new runtime certification |
| `test_wb_wall_corner.cpp:160-190` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_wb_wall_corner.release` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_x1_seam_split*.release` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_x1_seam_split.cpp:202-286` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_x1_seam_split.release` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_x1_seam_split_mp*.release` | `_ch03-grids-geometry.qmd` | Detailed row condensed; no new runtime certification |
| `test_x1_seam_split_mp.release` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_x1_seam_split_wb_ref4.release` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_x1_seam_split_wb_ref4_gravity_0.release` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_x1_seam_split_x1_centroid.release` | `_ch05-well-balanced.qmd` | Detailed row condensed; no new runtime certification |
| `test_yaml_keys.cpp:63-93` | `_ch12-configuration.qmd` | Detailed row condensed; no new runtime certification |
