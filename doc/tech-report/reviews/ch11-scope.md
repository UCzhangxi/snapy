# Chapter 11 scope and integration

Base: `1aeec3b370324f1b9e4e58217937c0cdfde5b941`.
Code pin: `e894700ff7aee30b52882e5202b16461413780b0`. The kintera pin remains `c55b13b2204997d2d09e04498558ab9495d8ee77`;
this chapter cites snapy call sites only and adds no direct kintera citation or dependency change.

| OUTLINE entry | Required content | Derivation/evidence | New runtime evidence |
|---|---|---|---|
| 11.1 | Register and classify block faces | Dispatch contracts; YAML rejection; wall classification | Source tests not run; see verification catalogue |
| 11.2 | Mirror a reflecting wall | Parity re-derived; wall-corner and saturation assertions | Source tests not run; see verification catalogue |
| 11.3 | Wrap values through a callback or the layout | Permutation re-derived; exchange inventory | Source tests not run; see verification catalogue |
| 11.4 | Repeat the nearest owned cell | Constant extension re-derived; pulse comparison unasserted | Source tests not run; see verification catalogue |
| 11.5 | Select outgoing acoustic and advected perturbations | Acoustic split and convex bounds re-derived; mode, tracer, pulse, restart assertions | Source tests not run; see verification catalogue |
| 11.6 | Reserve a face or fill a solid mask | Identity/constant mask maps; rectification assertions | Source tests not run; see verification catalogue |
| 11.7 | Order physical fills, exchange and corner refresh | Corner ownership re-derived; rest and phase-change assertions | Source tests not run; see verification catalogue |
| 11.8 | Supply ghosts through layout exchange | Geometry/parallel pointer; panel and neighbour exchange assertions | Source tests not run; see verification catalogue |
| 11.9 | Rectify a mask and close fluid faces against solids | Line DP and VIC closure re-derived; ghost/count/mass assertions | Source tests not run; see verification catalogue |
| 11.10 | Keep wall ghosts consistent with the hydrostatic reference | Pinned wall note section 4 plus zero-perturbation derivation; clamp and wall tests | Source tests not run; see verification catalogue |

All ten entries are drafted. Each has six layers and an executable schematic. Seven report-only checks
cover the mathematical identities and finite-set optimization, with no snapy import. The geometry chapter
owns interpolation/rotation derivations; the existing stage and switch chapters are referenced rather than copied.

The report base does not provide a book configuration or the official citation checker. The chapter opening
is supplied as `book/chapters/11-boundaries/_opening.qmd`; the editor installs the chapter wrapper and includes
it followed by registry, reflecting, periodic, extrapolation, outflow, custom, timing, exchange, solids and wb.
The Chapter 15 fragment is `book/chapters/15-verification/_ch11.qmd` per the current task.
No shared package bootstrap, matrix or existing chapter file is duplicated or rewritten.

## Pinned anchor inventory

Every range below was read in the pinned source. The supplementary audit rereads each via `git show`.
The JSON manifest is also the machine-readable mapping used by the audit.

| key | pinned code | anchor |
|---|---|---|
| registry | [`bc_func.hpp:14-39`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_func.hpp#L14-L39) | `BC_FUNCTION` |
| context | [`bc.hpp:19-42`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc.hpp#L19-L42) | `BoundaryFuncOptions` |
| yaml | [`meshblock_options.cpp:88-127`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock_options.cpp#L88-L127) | `periodic_z` |
| yamlxy | [`meshblock_options.cpp:139-201`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock_options.cpp#L139-L201) | `periodic_x` |
| classify | [`meshblock_options.cpp:218-271`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock_options.cpp#L218-L271) | `is_wall_boundary` |
| null | [`meshblock.cpp:138-166`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L138-L166) | `bfuncs` |
| x1wall | [`hydro.cpp:204-209`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro.cpp#L204-L209) | `is_x1_wall` |
| reflect | [`bc_func.cpp:10-34`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_func.cpp#L10-L34) | `reflecting_inner` |
| periodic | [`bc_func.cpp:36-50`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_func.cpp#L36-L50) | `periodic_inner` |
| extrap | [`bc_func.cpp:52-66`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_func.cpp#L52-L66) | `extrapolation_inner` |
| custom | [`bc_func.cpp:7-8`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_func.cpp#L7-L8) | `custom_inner` |
| solidbc | [`bc_func.cpp:68-87`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_func.cpp#L68-L87) | `solid_inner` |
| background | [`bc_func.cpp:92-106`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_func.cpp#L92-L106) | `check_background` |
| radiating | [`bc_func.cpp:108-133`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_func.cpp#L108-L133) | `radiating` |
| split | [`bc_func.cpp:135-165`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_func.cpp#L135-L165) | `plus` |
| alpha | [`bc_func.cpp:167-207`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_func.cpp#L167-L207) | `alpha` |
| outflow | [`bc_func.cpp:210-218`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_func.cpp#L210-L218) | `is_outflow` |
| apply | [`meshblock.cpp:1441-1519`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L1441-L1519) | `apply_boundaries` |
| init | [`meshblock.cpp:401-431`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L401-L431) | `boundary_reference_w` |
| finalinit | [`meshblock.cpp:454-500`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L454-L500) | `fill_solid_hydro_u` |
| advance | [`meshblock.cpp:545-572`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L545-L572) | `exchange_ghost_zones` |
| refill | [`meshblock.cpp:782-842`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L782-L842) | `apply_boundaries` |
| fixer | [`meshblock.cpp:850-907`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L850-L907) | `solid` |
| exchange | [`meshblock.cpp:913-929`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L913-L929) | `exchange_ghost_zones` |
| corner | [`meshblock.cpp:951-978`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L951-L978) | `refresh` |
| mesh | [`mesh.cpp:331-365`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/mesh.cpp#L331-L365) | `advance_local` |
| meshex | [`mesh.cpp:389-395`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/mesh.cpp#L389-L395) | `exchange_ghost_zones` |
| sync | [`layout.hpp:149-154`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/layout/layout.hpp#L149-L154) | `skip_corner` |
| wrap | [`slab_layout.cpp:41-70`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/layout/slab_layout.cpp#L41-L70) | `periodic_x` |
| panel | [`cubed_sphere_layout.cpp:922-956`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/layout/cubed_sphere_layout.cpp#L922-L956) | `interp_ghost` |
| interp | [`gnomonic_equiangle.cpp:245-264`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/coord/gnomonic_equiangle.cpp#L245-L264) | `interp_ghost` |
| average | [`layout.cpp:710-740`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/layout/layout.cpp#L710-L740) | `fill_corners` |
| raw | [`hydro_forward.cpp:673-680`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_forward.cpp#L673-L680) | `interpolate` |
| internal | [`internal_boundary.cpp:25-35`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/internal_boundary.cpp#L25-L35) | `max_iter` |
| mark | [`internal_boundary.cpp:47-95`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/internal_boundary.cpp#L47-L95) | `mark_prim_solid_` |
| rectify | [`rectify_solid.cpp:109-168`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/rectify_solid.cpp#L109-L168) | `rectify_solid` |
| dispatch | [`bc_dispatch.cpp:17-56`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/bc_dispatch.cpp#L17-L56) | `compute_min_flips` |
| dp | [`flip_zero_impl.h:24-198`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/flip_zero_impl.h#L24-L198) | `minRun0` |
| backtrack | [`flip_zero_impl.h:202-267`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/bc/flip_zero_impl.h#L202-L267) | `reconstruct` |
| dt | [`hydro.cpp:311-324`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro.cpp#L311-L324) | `solid` |
| masked | [`hydro.cpp:411-438`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro.cpp#L411-L438) | `forward_masked` |
| solidrow | [`implicit_dispatch.cpp:56-69`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/implicit/implicit_dispatch.cpp#L56-L69) | `setIdentity` |
| closure | [`vic_assemble_partial_impl.h:43-65`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/implicit/vic_assemble_partial_impl.h#L43-L65) | `solid_lower` |
| closurediag | [`vic_assemble_partial_impl.h:138-144`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/implicit/vic_assemble_partial_impl.h#L138-L144) | `Bnd` |
| fullclosure | [`vic_assemble_full_impl.h:123-126`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/implicit/vic_assemble_full_impl.h#L123-L126) | `Bnd` |
| wbflags | [`hydro_forward.cpp:243-263`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_forward.cpp#L243-L263) | `wb_x1` |
| wb | [`hydro_forward.cpp:287-343`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_forward.cpp#L287-L343) | `is_outflow` |
| nonwb | [`hydro_forward.cpp:378-383`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_forward.cpp#L378-L383) | `_revise_x1` |
| ref | [`hydro.cpp:503-556`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro.cpp#L503-L556) | `wall_clamp` |
| wallrop | [`hydro_ref_x1_impl.h:69-104`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_ref_x1_impl.h#L69-L104) | `hydro_ref_x1_wall_rop` |
| yamltest | [`test_yaml_keys.cpp:37-64`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_yaml_keys.cpp#L37-L64) | `EXPECT` |
| radiatingtest | [`test_radiating_boundary.cpp:46-98`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_radiating_boundary.cpp#L46-L98) | `EXPECT` |
| mixedtest | [`test_radiating_boundary.cpp:177-259`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_radiating_boundary.cpp#L177-L259) | `EXPECT` |
| tracertest | [`test_radiating_boundary.cpp:288-360`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_radiating_boundary.cpp#L288-L360) | `EXPECT` |
| pulsetest | [`test_radiating_boundary.cpp:395-441`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_radiating_boundary.cpp#L395-L441) | `EXPECT_LT` |
| restarttest | [`test_radiating_boundary.cpp:445-468`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_radiating_boundary.cpp#L445-L468) | `EXPECT_THROW` |
| alphatest | [`test_radiating_boundary.cpp:536-561`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_radiating_boundary.cpp#L536-L561) | `alpha` |
| cudatest | [`test_radiating_boundary.cpp:563-578`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_radiating_boundary.cpp#L563-L578) | `allclose` |
| rectifytest | [`test_rectify.cpp:91-124`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_rectify.cpp#L91-L124) | `test2` |
| counttest | [`test_flip_zero_count.cpp:12-48`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_flip_zero_count.cpp#L12-L48) | `serial` |
| solidtest | [`test_implicit_stratified_solid.py:277-291`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_implicit_stratified_solid.py#L277-L291) | `1.e-12` |
| cornertest | [`test_wb_wall_corner.cpp:166-190`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_wb_wall_corner.cpp#L166-L190) | `EXPECT` |
| sattest | [`test_wall_saturation.cpp:59-89`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_wall_saturation.cpp#L59-L89) | `1.e-12` |
| wbtest | [`test_wb_ref_wall.cpp:229-264`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_wb_ref_wall.cpp#L229-L264) | `EXPECT_GE` |
| reftest | [`test_hydro_ref_x1.cpp:217-247`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_hydro_ref_x1.cpp#L217-L247) | `EXPECT` |
| ctest | [`CMakeLists.txt:5-33`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/CMakeLists.txt#L5-L33) | `test_radiating_boundary` |
| ctestwall | [`CMakeLists.txt:91-117`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/CMakeLists.txt#L91-L117) | `test_wb_ref_wall` |
| ctestpy | [`CMakeLists.txt:192-200`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/CMakeLists.txt#L192-L200) | `test_radiating_boundary_python` |
| ctestsolid | [`CMakeLists.txt:232-235`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/CMakeLists.txt#L232-L235) | `test_implicit_stratified_solid` |
| paneltest | [`test_cubed_sphere_exchange.cpp:161-196`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_cubed_sphere_exchange.cpp#L161-L196) | `torch::equal` |
| veltest | [`test_cubed_sphere_vertical_velocity_exchange.py:81-109`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_cubed_sphere_vertical_velocity_exchange.py#L81-L109) | `ideal_match` |
| meshtest | [`test_mesh_exchange.py:24-49`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_mesh_exchange.py#L24-L49) | `assert` |
| pyoutflowtest | [`test_radiating_boundary_python.py:16-36`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_radiating_boundary_python.py#L16-L36) | `assert` |
| wboption | [`hydro_options.cpp:51-60`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_options.cpp#L51-L60) | `wb_wall_clamp` |
| ref4option | [`wb_ref4.cpp:85-96`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/wb_ref4.cpp#L85-L96) | `SNAP_WB_REF4` |
| centroidoption | [`x1_centroid.cpp:94-103`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/coord/x1_centroid.cpp#L94-L103) | `SNAP_X1_CENTROID_EXACT` |
| initexchange | [`meshblock.cpp:375-396`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L375-L396) | `exchange` |
| massoption | [`hydro.cpp:231-236`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro.cpp#L231-L236) | `x1_mass_covariance` |
| remark | [`hydro_forward.cpp:215-219`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_forward.cpp#L215-L219) | `mark_prim_solid_` |
| mirror1 | [`hydro_forward.cpp:384-387`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_forward.cpp#L384-L387) | `pib` |
| mirror2 | [`hydro_forward.cpp:592-595`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_forward.cpp#L592-L595) | `pib` |
| mirror3 | [`hydro_forward.cpp:614-617`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_forward.cpp#L614-L617) | `pib` |
| scalarraw | [`scalar.cpp:140-153`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/scalar/scalar.cpp#L140-L153) | `sync_theta` |
| solidfixture | [`test_implicit_stratified_solid.py:99-141`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_implicit_stratified_solid.py#L99-L141) | `solid_run` |
| veltol | [`test_cubed_sphere_vertical_velocity_exchange.py:7-15`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_cubed_sphere_vertical_velocity_exchange.py#L7-L15) | `ABS_TOL` |
| exchangetest | [`test_exchange.cpp:292-317`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/test_exchange.cpp#L292-L317) | `saw_remote_neighbor` |
| parallelctest | [`CMakeLists.txt:120-123`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/CMakeLists.txt#L120-L123) | `test_exchange` |
| pyctests | [`CMakeLists.txt:223-225`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/CMakeLists.txt#L223-L225) | `test_mesh_exchange` |
| positivityctests | [`CMakeLists.txt:248-253`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/tests/CMakeLists.txt#L248-L253) | `test_flux_positivity` |

## Findings and open questions

The outflow wave selector uses current speeds while the invariant impedance uses the saved background.
The WB even-parity fill excludes outflow, but the default reference clamp receives physical-face flags.
The hydro x1-wall predicate is also distinct from the diffusion whitelist. These are code observations,
not hypotheses about a measured failure. Runtime implications of mixed outflow/WB/VIC and corner combinations
remain unmeasured. The full implicit solid closure has a nonperiodic guard; periodic-solid coverage is open.
The stage refill restores only hydro in solid cells; passive-scalar and diffusion coupling need separate runs.

No inherited measurement is promoted to a new result. Wall-reference order needs at least three resolutions;
the existing test asserts only a two-grid ratio. Runtime work, if scheduled, must start with a CPU-only build
at the exact pin and record the dependency resolution, dtype, decks and test filter. No build is needed to
validate the current formulas or static code map.
