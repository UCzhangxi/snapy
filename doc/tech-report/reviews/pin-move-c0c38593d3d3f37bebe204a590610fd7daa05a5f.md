# Pin move ccf40f9 -> c0c3859: what resolved, the changed bodies, and what was resolved by hand

STYLE.md section 3.1: when the pin moves, each range is re-resolved by locating its
anchor in the new file; where the anchor has moved to another file, been renamed or
been deleted, the script does not guess but lists the citation here, and the owning
author re-reads the code and rewrites the citation and, if the code changed, the claim.

Old pin `ccf40f9565642c32be69f4b9ef0cfa6daff3f201`, new pin
`c0c38593d3d3f37bebe204a590610fd7daa05a5f` (`chengcli/snapy` main, ten merges:
`chengcli/snapy#313`, output metadata, restart schedule and block-size checks;
`#320`, outflow reads only its interior cells; `#321`, flux CCF output; `#323`, combined
slice output; `#324`, cubed-sphere diffusion; `#325`, its convergence test; `#327`,
mismatched exchange variables refused; `#328`, NH3 in three decks (`#315`) and `cstdint`
in the yaml-cpp patch (`#316`); `#329`, donor tangential momentum in the partial VIC;
`#332`, deficit-only `fix_vapor` borrow and the species face clamp).

## What resolved

`python3 tools/code_anchors.py bump c0c38593d3d3f37bebe204a590610fd7daa05a5f` (Universal
Ctags 6.2.1) resolved every `{{< code >}}` citation: 797 distinct symbols, 0 unresolved,
49 with a changed body, and wrote the new sha into `code_pin.yml`.
`python3 tools/code_anchors.py check` then reports 3579 citations, 797 distinct, 0 unresolved.

## Changed bodies, by merge

The merge is the one `git log -L <new range>:<path> ccf40f9..c0c3859` attributes the body
change to; "file" rows are whole-file citations. The owner is the one named for this move
(chapter 7.B: Xinyue; chapter 8 and 4.6 WENO5: Jiheng; chapter 9, the cubed-sphere parts and
the citation edits for `#320`, `#321`, `#323`, `#327`, `#315`: Linfeng).

| merge | changed body | cited in | owner | done here |
|---|---|---|---|---|
| #329 | `implicit/vic_assemble_partial_impl.h` `vic_assemble_partial_impl` | ch07 `_vic-assembly`, `_vic-closure`; ch06 `_dwork`, `_vic`; ch11 `_solids`; App. B ch11 | ch07: Xinyue | ch07 rewritten; ch06, ch11 not read (see "Open") |
| #329 | `implicit/implicit_dispatch.cpp` `vic_assemble_partial_cpu` | ch07 `_vic-assembly`; ch06 `_dwork`; ch11 `_solids` | ch07: Xinyue | ch07 rewritten |
| #329 | `implicit/forward_sweep_impl.h` `ForwardSweep` | ch07 `_vic-sweep`, `_vic-stage`, `_vic-pivot`, `_vic-steady`; ch06 `_dwork`; ch16; App. B ch06, ch07 | ch07: Xinyue | `_vic-sweep` rewritten; `_vic-stage`, `_vic-pivot`, `_vic-steady` re-read, unchanged (their claims are about the solve, not the right-hand side) |
| #329 | `implicit/implicit_dispatch.cpp` `vic_solve_cpu` | ch07 `_vic-sweep` | ch07: Xinyue | rewritten |
| #329 | `implicit/implicit_dispatch.cpp` `vic_redistribute_cpu` | ch07 `_vic-redistribute` | ch07: Xinyue | rewritten |
| #329 | `tests/test_backward_substitution.cpp` (file) | ch08 `_vic` | Jiheng | — |
| #332 | `eos/equation_of_state.cpp` `EquationOfStateImpl::apply_conserved_limiter_` | ch08 `_borrow`, `_eoslimiter`, `_fixvapor`; ch10 `_borrow`, `_fixvapor`, `_satadj`; ch02 `_consistency`; ch03 `_x1seams`; ch15 `_invariants`; ch16; App. B ch10 | ch08: Jiheng | — |
| #332 | `eos/fix_vapor_impl.h` `fix_vapor_impl` | ch10 `_fixvapor`; ch15 `_ch10-moist-coupling`; App. B ch10 | Jiheng | — |
| #332 | `recon/reconstruct.cpp` `ReconstructImpl::forward`, and the file | ch08 `_reconfloors`; ch04 `_framework`; ch05 `_wbx1`; ch15 `_invariants`; ch16 | ch08, 4.6: Jiheng | — |
| #332 | `hydro/flux_positivity.hpp` (file) | ch16 | Jiheng | — |
| #332 | `tests/test_eos.cpp`, `tests/test_fix_vapor_volume.cpp` (file and `DeviceTest.fix_vapor_keeps_the_column_mass_on_varying_cell_volume`), `tests/test_forcing.cpp` (file and `forcing.limiter_roundoff_species_repair_is_not_redone`) | ch08 `_fixvapor`, `_eoslimiter`, `_redo`; ch10 `_fixvapor`, `_redo`; ch16 | Jiheng | — |
| #332, #324 | `mesh/meshblock.cpp` `MeshBlockImpl::advance_local` (species clip of the stage forcing; implicit radial diffusion begin/finish) | 29 sections, among them ch07 `_rk`, `_split`, `_vic-redistribute`, `_vic-reject`, `_vic-stage`; ch08 `_drycarry`, `_fixvapor`; ch09 `_framework`, `_user` | ch08: Jiheng; ch09: Linfeng | ch07 `_rk`: the stage list now names the radial diffusion's `begin_step`/`finish_step` and the species clip of the user forcings, with cross-references to ch09 and ch08; `_split`, `_vic-redistribute`, `_vic-reject`, `_vic-stage` re-read, their claims unchanged |
| #324 | `forcing/diffusion.cpp` (file), `DiffusionImpl::forward`, `::max_time_step`, `::reset`, `DiffusionOptionsImpl::from_yaml` | ch09 `_viscosity`, `_wallcoef`, `_x1profile`; App. B ch09 | Linfeng | — |
| #324, #323 | `mesh/meshblock.cpp` `MeshBlockImpl::apply_redo` | ch07 `_redo`; ch08 `_redo`; ch10 `_redo`; ch13 `_fixgrav`, `_redo-view`; ch01 `_driver` | Linfeng (ch09 part) | ch07 `_redo` corrected: a redo no longer touches the cycle count (the driver advances it only after an accepted step) |
| #323 | `mesh/meshblock.cpp` `MeshBlockImpl::local_redo_flag_tensor`, `::reset`; `mesh/meshblock_options.cpp` (file and `MeshBlockOptionsImpl::from_yaml`); `examples/run_hydro.cpp`, `bryan.cpp`, `jupiter_evap_precip_1d.cpp`, `straka.cpp` `main` (and file); `output/output_type.cpp` `OutputOptionsImpl::from_yaml`; `output/output_type.hpp` `OutputOptionsImpl`; `output/pnetcdf.cpp` `PNetcdfOutput::PNetcdfOutput`; `tests/test_check_redo_parallel.cpp` `Mesh.check_redo_is_one_decision_across_ranks`; `tests/test_user_output.cpp` (file) | ch01, ch03, ch07 `_exchange`, `_redo`, `_split`, `_vic-reject`, ch10, ch11, ch12, ch13, ch14 `_netcdf`, `_pnetcdf`, `_restart`, `_repro`, `_schedule`, `_collectives`, `_gpu`, ch16, App. E | Linfeng | ch07 `_redo` corrected: the floor test writes the checked primitives into `hydro_w` and keeps them; `_exchange`, `_split`, `_vic-reject` re-read, unchanged |
| #313, #323 | `output/netcdf.cpp` `NetcdfOutput::write_output_file`; `output/pnetcdf.cpp` `PNetcdfOutput::write_output_file`; `tests/test_coordinate.cpp` (file) | ch14 `_netcdf`, `_pnetcdf`; ch16; ch03 `_cylindrical`, `_facemoments` | Linfeng (#323); #313 is not assigned | — |
| #313 | `output/output_utils.cpp` `MetadataTable::MetadataTable`; `output/restart.cpp` `RestartOutput::write_output_file`; `coord/coordinate.cpp` `CoordinateOptionsImpl::from_yaml`; `tests/test_x1_seam_split.cpp` `X1SeamSplit.x1_mass_covariance_needs_3_x1_cells` | ch14 `_netcdf`, `_restart`; ch13 `_cycle`; ch01; ch03 `_choosing`, `_globalgrid`; ch12 `_yaml`, `_mass-covariance`, `_matrix`; ch15 `_ch12-configuration`; ch16 | not assigned | — |
| #320 | `bc/bc_func.cpp` (file) and `radiating` | ch11 `_extrapolation`, `_outflow`, `_periodic`, `_reflecting`; ch03 `_physfaces`; ch16; App. B ch11 | Linfeng | — |
| #327 | `layout/layout.cpp` `LayoutImpl::_copy_local_exchange_buffers` | ch14 `_msgmatch` | Linfeng | — |
| #313, #320, #324, #325, #328, #329, #332 | `tests/CMakeLists.txt` (file) | 34 sections and App. D | each owner for their tests | ch07: the chapter's ctest table re-run at the pin |
| #321, #315 | no cited body changed; `#315` changed the line ranges of three example decks (below) | ch02 `_ideal-moist`; ch16 | Linfeng | — |

## Resolved by hand, recorded for review

The line links (STYLE 10.6) were moved by mapping each range through
`git diff --no-renames -U0 ccf40f9 c0c3859`: a range no hunk touches shifts by the hunks
above it (746 links in `book/` and `tools/`, and 40 `path[:lines]@sha` citations). The
PROVENANCE `pin:` lines (182) and the `tree/` and `commit/` links (13) take the new sha.
Ranges touched by a hunk were not mapped; they are listed below.

| citation | old | new | why |
|---|---|---|---|
| `src/mesh/meshblock.cpp` (the multi-stage averaging block, $\mathbf U^{(s)}$), ch07 `_rk`, App. H, `tools/reader-glossary.json` | `772-777` | `800-808` | the implicit radial diffusion's `finish_step` call was inserted inside the block |
| `src/forcing/diffusion.cpp` (the `kappa_iso` heat flux, $\kappa$), ch09 `_viscosity` glossary note, App. H, `tools/reader-glossary.json` | `544-558` | `605-639` | the block now also sets the conductive wall temperatures; `gen_reader_reference.py` refuses a glossary source off the pin, so it was re-resolved here (the ch09 body is Linfeng's) |
| link labels that carry line numbers (`[`file:a-b`]`, `[file#La-Lb]`, `[La-Lb]`) | 64 labels | mapped like their links | a label is rewritten only when its numbers map, through the same hunks, to exactly the link's new range |
| `src/eos/equation_of_state.cpp:339`, ch06 `_cell` | `339` | `340` | label and link, one line inserted above |
| `tools/gen_boundary_contract.py` `src/mesh/meshblock.cpp` lines | 412, 431, 498, 862, 960, 977, 1600 | 418, 437, 504, 893, 991, 1008, 1634 | the same lines at the new pin (each compared line for line) |
| `tools/gen_forcing_contract.py` `src/mesh/meshblock.cpp` lines | 708 (`apply_extra_forcing`); 38, 99 | 719; 38, 99 | as above |

The six contract generators carry the new `PIN`; each was run with `--write` and then reports
0 problems at the pin. `gen_notation_index.py`, `gen_derivation_index.py`,
`gen_reader_reference.py` (0 problems, 329 entries) and `book_chapters.py` were re-run.

Left at the old sha for their owners (ranges a hunk touched, in chapters this move does not
rewrite; each still resolves at `ccf40f9565642c32be69f4b9ef0cfa6daff3f201`):

| file | links | code | merge |
|---|---|---|---|
| ch02 `_ideal-moist` | 6: `examples/jupiter_crm.yaml`, `jupiter_gcm.yaml` `1-53`, `uranus.yaml` `1-63` | the deck compositions | #328 (#315) |
| ch16 | 4: the same decks, `15-16` and `uranus.yaml` `35-41` | the deck compositions | #328 (#315) |
| ch14 `_netcdf` | 9: `output_utils.cpp` `29-187`, `37-41`, `235-250`; `netcdf.cpp` `202-256`, `224`, `236`, `256`, `262-263`, `325-348` | metadata table, file writer | #313, #321, #323 |
| ch14 `_restart` | 4: `restart.cpp` `24-61`, `38-61`, `42-61` (twice) | restart writer | #313 |

## Generated fixtures

- `tools/ctest-index.json` and Appendix C were refreshed from a clean checkout configured at
  the pin (no build): `cmake -S snapy-pin -B snapy-pin/build -G Ninja
  -DCMAKE_BUILD_TYPE=Release -DNETCDF=ON -DPNETCDF=OFF`, then
  `python3 tools/gen_test_index.py --refresh snapy-pin/build`. CMake/CTest 4.4.4 (the old
  fixture says 3.31.8), torch 2.10.0, kintera 2.6.4, commux found so `UCX=ON`; the recorded
  switches are the old ones. `PNETCDF=OFF` because `PNETCDF=ON` needs the `pinc` package,
  and no test registration reads it. Registered: 1054 -> 1066; snapy rows 127 -> 139; Eigen
  927 -> 927. Added (12): `test_diffusion_cubed_sphere.release`,
  `test_diffusion_cubed_sphere_mp.release`, `test_diffusion_cubed_sphere_two_gpu.release`,
  `test_example_species_composition`, `test_fix_vapor_deficit.release`,
  `test_forcing_species_clip_python`, `test_netcdf_axis_attrs`,
  `test_outflow_stale_ghosts_python`, `test_restart_resume_schedule`,
  `test_species_face_clamp.release`, `test_vic_partial_tangential.release`,
  `test_yamlcpp_cstdint_patch`. Removed: none. 124 `defined_at` lines shifted; no
  properties or helpers changed. `ctest --show-only=json-v1` lists 1066 distinct names and
  `ctest -N` says `Total Tests: 1066`. App. C's counts (1052/125, already stale) now read
  1066/139, and its provenance footnote says how the fixture was made.
- `tools/deck-keys.json` and Appendix I: `python3 tools/gen_deck_keys.py --refresh`:
  159 -> 163 keys, 148 linked, 15 with no section. Added: `implicit_radial`,
  `temperature_inner`, `temperature_outer`, `wall_velocity` (diffusion, #324). Removed: none.
  `x1_slice`, `x2_slice`, `x3_slice` now default `guarded` in `output_type.cpp` (lists, #323)
  instead of `std::nullopt` in `output_type.hpp`; the other 19 changed entries are line moves.

## Provenance tags

`tools/check_provenance.py` requires a tag's sha to be the pin or a later commit, so every
tag at `ccf40f9` now counts against its chapter.

- 34 tags of report-port checks were moved to `c0c3859`: each command was re-run from the
  report directory with Python 3.12.10, numpy 2.5.4, sympy 1.14.0, its output was
  byte-identical to the committed `.out`, and no section they sit in cites a changed body;
  the tag now names that environment. Chapter 8 was left to its owner.
- The ch09 `_framework` tag was moved too, because `tools/tests/test_provenance.py` requires
  that forcing port to name the pin: it ports `HydroImpl::forward` block (6) of
  `src/hydro/hydro_forward.cpp`, which is identical at both pins, and its output reproduced
  byte for byte. The ch09 text was not touched.
- The ch10 condensate tag is written by `gen_species_contract.py` with its `PIN`, and moved
  with it; its check reproduced byte for byte.
- ch07 `_vic-assembly` and `_vic-redistribute` (at `6fbb397`) moved to the new pin: their
  checks gained `[C7]` for `#329`, and `[C1]`–`[C6]` print the same numbers.
- 33 tags stay at `ccf40f9`: the sections cite a body this move changed (ch01 `_options`,
  ch02 `_saturation`, ch06 `_dwork`, `_fixer`, ch07 `_exchange`, ch11 `_extrapolation`,
  `_outflow`, `_periodic`, `_registry`, `_solids`, ch12 `_mass-covariance`, `_matrix`,
  `_yaml`, ch13 `_cycle`, `_redo-view`, ch14 `_msgmatch`, `_netcdf`, `_pnetcdf`, `_repro`,
  `_restart`, ch15 `_invariants` (4)), or they are in chapter 8 (9). Their checks all
  reproduced byte for byte here; they move when their owner re-reads the section.
- The chapter 7 ctest table was re-run at the pin and its tag moved: 17 of 18 entries pass,
  including `test_vic_partial_tangential.release`; `test_straka` ran (73.7 s) and then failed in
  post-processing (`ncrcat` not installed), so it is reported as not evaluated.
- After this, `ratchet_gate.py update` and `check_provenance.py --update` were run: 39 tags name
  the new pin, and the provenance baseline is 92 failing tags: 62 before, plus the 33 tags
  kept at `ccf40f9`, less the three ch07 records that moved from `6fbb397`.
- `vic_sweep_check.py` stays at `6fbb397`: its re-run differs from the committed output in one
  round-off digit (`[C1]` N = 5: 3.0e-16 here, 4.4e-16 committed).

## Open

- ch07 `_exchange` keeps its tag at the old pin (its section cites `run_hydro.cpp` `main`,
  which changed); its check reproduced byte for byte.
- ch06 `_dwork`, `_vic` and ch11 `_solids` cite the partial VIC (#329: the face-work energy
  terms gain $m_a$ columns; a solid neighbour's face is merged with cell $i$'s $v_a$). Their
  owners (ch06, ch11) were not named for this move.
- `#313` (output metadata, restart schedule, block-size check) has no owner in this move.
- `tools/chapter-owners.tsv` names other owners for chapters 8 and 9 than this move does;
  it was not changed.
