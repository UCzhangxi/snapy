# Outline inventory: Chapters 12, 13, 15 (snapy @ dae902b)

All code locations are `path:line@dae902b`, read in the worktree at that sha. `src/` is the library; `snap/` is a
symlink to `src/` (same files). ctest names follow `tests/CMakeLists.txt`; `<b>` is the lower-case build type
(`release` in CI and in every `run_*.cmake`).

---

## Chapter 12: Build-time and run-time switches and configurations

Scope: every switch that changes what snapy compiles or computes. That covers CMake options and cache variables,
`configure.h` macros and compile definitions, environment variables read through `get_env`/`std::getenv`, and the
YAML option keys that select a scheme (gravity-work mode, fixer, wall clamp, implicit scheme, limiter, nghost,
reconstruction and Riemann types). For each switch the chapter gives how it is set, its default, the code that reads
it, its couplings, and the tests that run it. It ends with a coverage matrix (switch combination -> ctest entries).
**Recommendation: keep it as one chapter, in three parts:** 12.1 build-time, 12.2 environment (the five `SNAP_*`
scheme switches are the core), 12.3 YAML scheme keys. Put the coverage matrix in 12.4 and cross-link it from
Chapter 15. Do not merge it into Ch.15: Ch.15 indexes tests by topic, while 12.4 indexes them by switch
combination. The study switches (`SNAP_*`) are process-global and read once, and their couplings
(implication, nghost, grid type, gravity-work mode) are real constraints. They deserve a chapter of their own and should
not be scattered across Chapters 4-6.

### Scheme: CMake options and cache variables (build-time)
- Summary: top-level `option()`s and cache variables, plus three variables (`buildl`, `UCX_FOUND`, `CUDAToolkit_FOUND`)
  that gate which tests are registered. Switch: `cmake -D<NAME>=...`; defaults below.

| Name | Default | Set at | Effect / reader | Couplings |
|---|---|---|---|---|
| `BUILD_TESTS` | ON | `CMakeLists.txt:7@dae902b` | `add_subdirectory(tests)` at `CMakeLists.txt:149-153@dae902b` | none |
| `FULL_TESTS` | OFF | `CMakeLists.txt:8@dae902b` | adds `test_shallow_xy`, `test_shallow_splash` reference tests (`tests/CMakeLists.txt:365-368@dae902b`), the decomp matrix `test_shallow_splash_decomp`, `test_shallow_xy_decomp`, `test_shallow_splash_ucx_cuda_decomp` (`tests/CMakeLists.txt:458-510@dae902b`) and, on Apple, `test_exchange_decomp` (`tests/CMakeLists.txt:440@dae902b`) | CI sets ON for non-PR Linux runs (`.github/workflows/ci.yml:87@dae902b`) |
| `BUILD_EXAMPLES` | OFF | `CMakeLists.txt:9@dae902b` | **dead**: the guard is commented out and `add_subdirectory(examples)` is unconditional (`CMakeLists.txt:155-158@dae902b`) | example tests need `bin/straka.<b>` etc., so examples are always built |
| `CUDA` | OFF | `CMakeLists.txt:10@dae902b` | `enable_language(CUDA)` (`:26-28`), CUDA arch list (`:109-143`), `CUDA_OPTION` -> `USE_CUDA` (`cmake/parameters.cmake:6-10@dae902b`); requires commux CUDA sidecar (`src/CMakeLists.txt:93-104@dae902b`) | not CUDA => every ctest whose name contains `cuda` or whose labels are `cuda`/`gpu` is DISABLED and every test gets `SNAPY_BUILD_CUDA=0` (`tests/CMakeLists.txt:514-533@dae902b`) |
| `NETCDF` | ON | `CMakeLists.txt:11@dae902b` | `NETCDF_OPTION` -> `NETCDFOUTPUT` and `find_package(NetCDF REQUIRED)` (`cmake/parameters.cmake:20-25@dae902b`) | none |
| `UCX` | ON (Linux), OFF (Apple) | `CMakeLists.txt:13,16@dae902b` | `UCX_OPTION` -> `USE_UCX` (`cmake/parameters.cmake:13-17@dae902b`); `cmake/ucx.cmake:1-73@dae902b` needs Python `commux` and sets `UCX_FOUND` | `UCX_FOUND` gates `test_exchange_ucx`, `test_sedimentation_cubed_seam_gloo`, `test_parentless_cloud_nb1_mp_gloo` (`tests/CMakeLists.txt:129,142,151@dae902b`) |
| `PNETCDF` | ON (Linux), OFF (Apple) | `CMakeLists.txt:14,17@dae902b` | `PNETCDFOUTPUT`; needs Python `pinc` (`cmake/parameters.cmake:28-46@dae902b`) | `run_straka.cmake`/`run_shallow_splash.cmake` rewrite `type: pnetcdf` to `netcdf` when `NO_PNETCDFOUTPUT` (`tests/run_straka.cmake:26-29@dae902b`) |
| `NMASS` | 0 | `cmake/parameters.cmake:3@dae902b` (`set_if_empty`) | `configure.h.in:19@dae902b`; Athena++ legacy index layout in `src/snap.h:8-27@dae902b` | **effectively dead**: `static_assert(ICY == IPR + 1)` at `src/snap.h:52@dae902b` refuses NMASS>0, so the check at `src/eos/equation_of_state.cpp:89@dae902b` is unreachable |
| `CMAKE_BUILD_TYPE` | Release | `CMakeLists.txt:61-63@dae902b` | flags in `cmake/compilers.cmake:15-35@dae902b` (Release `-O3 ...`; Debug `-g3 -fsanitize=address,undefined` for GNU/Clang) | ctest names carry `buildl`; the example runners hard-code `-Dbuildl=release` (`tests/CMakeLists.txt:371@dae902b`) |
| `SNAPY_TEST_PYTHONPATH` | "" (cache PATH) | `tests/CMakeLists.txt:347-348@dae902b` | prepended to PYTHONPATH of every `*_python` ctest (`:350-355`); unset => warning that python ctests test the installed snapy (`:357-359`) | `test_python_import_path_python` checks the wiring (`tests/CMakeLists.txt:315-323@dae902b`) |
| `KINTERA_DATA_DIR` | undefined | `tests/CMakeLists.txt:333-337@dae902b` | symlinks `nasa9.dat` into the test dir | none |
| `EIGEN`, `FMT`, `GTEST`, `YAML-CPP` | ON | `cmake/macros/macro_add_package.cmake:10@dae902b` via `cmake/{eigen,fmt,gtest,yamlpp}.cmake` | FetchContent with a tarball cache under `.cache/` | none |
| CUDA arch list | 60 61 70 75 80 86 89 (+90 for >=12.0, +120 for >=12.8, minus 60/61/70 for >=13.0) | `CMakeLists.txt:119-142@dae902b` | `CMAKE_CUDA_ARCHITECTURES` | none |

- Derivations: none (configuration).
- Figures: (1) a decision tree from `cmake -D...` to which ctest entries exist and which are disabled; (2) a table
  graphic of build flags -> `configure.h` macros -> the `#ifdef` sites.
- Code: listed in the table.
- Tests: `test_python_import_path_python` — `SNAPY_TEST_PYTHONPATH` is first in PYTHONPATH and the caller's entry
  survives (`tests/test_python_import_path.py:16-21@dae902b`). No test covers `NMASS`, `BUILD_EXAMPLES` or `NETCDF=OFF`.
- Limits / known issues: `BUILD_EXAMPLES` has no effect. `NMASS>0` cannot compile. CI runs CPU only (`-DCUDA=OFF`,
  `.github/workflows/ci.yml:84@dae902b`), so the CUDA entries run only on developer builds.
- Discrepancies: none found in sources.

### Scheme: `configure.h` macros and compile definitions (build-time)
| Macro | Values | Set from | Read at |
|---|---|---|---|
| `USE_C10D_GLOO` | always defined | `configure.h.in:4@dae902b` | no reader in `src/` (dead) |
| `USE_UCX` / `NOT_USE_UCX` | UCX option | `configure.h.in:7@dae902b` | `default_backend()` returns `ucx` (non-Darwin) or `gloo` at `src/layout/layout.cpp:41-50@dae902b`; UCX process group `src/layout/process_group_ucx.cpp:3,22@dae902b`; stub that throws "built without UCX" at `src/layout/process_group.cpp:286-291@dae902b` |
| `USE_CUDA` / `NOT_USE_CUDA` | CUDA option | `configure.h.in:10@dae902b` | `src/mesh/mesh.cpp:16@dae902b` (and 51, 75, 83, 104, 137, 161, 176, 203), `src/layout/layout.cpp:17,82,283@dae902b`; test gate `snapy_cuda_test_enabled()` at `tests/cuda_test_gate.hpp:9-15@dae902b` |
| `NETCDFOUTPUT` / `NO_NETCDFOUTPUT` | NETCDF | `configure.h.in:13@dae902b` | `src/output/netcdf.cpp:26,43@dae902b`, `src/output/mppnccombine.cpp:55@dae902b`, `src/output/combine_netcdf.cpp:41@dae902b` |
| `PNETCDFOUTPUT` / `NO_PNETCDFOUTPUT` | PNETCDF | `configure.h.in:16@dae902b` | `src/output/pnetcdf.cpp:3@dae902b`, `src/mesh/meshblock.cpp:211@dae902b` |
| `NMASS` | 0 | `configure.h.in:19@dae902b` | `src/snap.h:8,52@dae902b` (see above) |
| `DISPATCH_MACRO` | `__host__ __device__` under nvcc | `configure.h.in:21-25@dae902b` | kernels |
| `KINTERA_ROOT_DIR`, `HARP_ROOT_DIR` | paths | `configure.h.in:27-28@dae902b` | no reader in `src/` |
| `_GLIBCXX_USE_CXX11_ABI` | torch's ABI | `CMakeLists.txt:35-47@dae902b` | global compile definition |
| `HAVE_AVX512_CPU_DEFINITION`, `HAVE_AVX2_CPU_DEFINITION` | 1 (non-Apple) | `cmake/compilers.cmake:12@dae902b` | torch headers |
| `COMMUX_WITH_CUDA_RUNTIME` | 1 when CUDA | `src/CMakeLists.txt:104@dae902b` | commux headers |
- Derivations: none.
- Figures: one box diagram from the CMake option to the macro to the reader file.
- Tests: indirectly, `test_process_group` (`LayoutOptions.DefaultsToPlatformCommunicationBackend`,
  `tests/test_process_group.cpp:74@dae902b`).
- Limits: `USE_C10D_GLOO`, `KINTERA_ROOT_DIR`, `HARP_ROOT_DIR` are defined but unused.

### Scheme: environment helper `get_env` and the read-once rule
- Summary: `get_env(name, def)` returns `getenv(name)` or `def` (`src/layout/layout.hpp:38@dae902b`). All five scheme
  switches parse their value once per process into a function-local `static const bool`. Every block in a process
  must make the same choice, or the x1/x2/x3 seam faces stop being single-valued. Consequence: an A/B comparison
  needs one process per arm, so every python oracle spawns a child per arm.
- Parsing rule (verified): `SNAP_FLUX_COVARIANCE`, `SNAP_WB_REF4`, `SNAP_X1_CENTROID_EXACT`, `SNAP_X1_MASS_COVARIANCE`
  are **off unless set**. Off means empty, `0`, `false`, `off` or `no` (case-insensitive); any other value is on.
  `SNAP_GRAVITY_WORK_RADIAL_EXACT` is **on unless** `0/false/off/no`. Note that an *empty* value turns it on, while it
  turns the other four off (`src/hydro/hydro.cpp:226-229@dae902b` vs `:212-215`).
- Code: `src/layout/layout.hpp:38@dae902b` (`get_env`); readers `src/hydro/hydro.cpp:208-232@dae902b`,
  `src/hydro/wb_ref4.cpp:87@dae902b`, `src/coord/x1_centroid.cpp:96@dae902b`, `src/hydro/hydro_forward.cpp:41@dae902b`.
- Derivations: none.
- Figures: a timeline showing the switch read once at first call and frozen for the process, so each test arm runs in
  a child process.
- Tests: every switch oracle (below) runs arms in child processes. Examples: `tests/test_wb_ref4_order.py:135-139@dae902b`,
  `tests/test_gravity_work_radial_exact.py:346-349@dae902b`.

### Scheme: `SNAP_WB_REF4` (fourth-order, cell/face-consistent x1 well-balanced reference)
- Summary: replaces the kernel's x1 density reference with a fourth-order, cell/face-consistent one; on a
  non-uniform x1 grid it also replaces the reference cell pressure. Switch: env `SNAP_WB_REF4`, default **off**.
- Derivations:
  - fourth-order reference, filter rows, wall extrapolation, resolution flag: exists:
    `docs/derivations/wb-ref4.md@dae902b` (also `sources/deriv__wb-ref4.md`; weights checked by
    `docs/derivations/wb_ref4_weights.py@dae902b`).
  - seam behaviour of the flag (needs nghost>=3): exists: `docs/derivations/wb-ref4.md@dae902b` sec 7 (cited in the
    test header `tests/test_x1_seam_split.cpp:18-22@dae902b`).
- Figures: (1) the 5-point filter stencil F = (-1,4,10,4,-1)/16 with the cubic wall extrapolation E past a clamped wall;
  (2) the resolution flag reading scan pressures three cells away across an x1 seam, with the ghost depth marked.
- Code:
  - `src/hydro/wb_ref4.cpp:83-95@dae902b` — `wb_ref4_enabled()` — reads the env var once; returns
    `on || x1_centroid_exact_enabled()` (the implication).
  - `src/hydro/hydro.cpp:220@dae902b` — `HydroImpl::wb_ref4()` — forwards to it.
  - `src/hydro/hydro.cpp:96-103@dae902b` — `HydroImpl::reset()` — `TORCH_CHECK(ng >= 3)` when on and grav1 != 0:
    "SNAP_WB_REF4 (or SNAP_X1_CENTROID_EXACT, which implies it) needs nghost >= 3".
  - `src/hydro/hydro.cpp:547-556@dae902b` — `HydroImpl::_hydro_ref_x1` — builds `wb_ref4_stencils` and applies
    `wb_ref4_cells` before the seam exchange; `src/hydro/hydro.cpp:626@dae902b` — `wb_ref4_faces` after it.
  - `src/hydro/wb_ref4.cpp:97@dae902b` — `wb_ref4_stencils` (usable iff >=4 owned cells next to a clamped wall and nc1>=5,
    `:114`); `:233` `wb_ref4_cells`; `:276` `wb_ref4_faces`.
  - `src/hydro/balance_column.cpp:73-79,90@dae902b` — `balance_column` — on a non-uniform grid finds the fixed point of
    the switched reference.
- Couplings: implied by `SNAP_X1_CENTROID_EXACT`. Needs `geometry/cells/nghost >= 3` whenever grav1 != 0, which is a
  setup error otherwise. With grav1 = 0 no reference is built and nghost 1 is accepted. The wall closure uses
  `dynamics/wb-wall-clamp` (the `clamp && phys_in` arguments, `src/hydro/hydro.cpp:550-553@dae902b`).
- Tests:
  - `tests/test_wb_ref4_order.py` (`test_wb_ref4_order_python`, `_cuda_python`) — arms unset / `1`, both with
    `SNAP_FLUX_COVARIANCE=1` and `gravity-work: face`, so radial-exact is on by default; the observed order of
    |N2_eff| is >= `ORDER_ON = 2.75` with the switch on and below `ORDER_OFF = 2.5` with it off
    (`tests/test_wb_ref4_order.py:38-39@dae902b`), at 1 and 3 e-folds, nz 32/64/128.
  - `test_balance_column_wb_ref4.<b>`, `test_face_floor_wb_ref4.<b>` — the same binaries with `SNAP_WB_REF4=1`
    (`tests/CMakeLists.txt:93-96@dae902b`). The balance-column fixed point stays at round-off (1e-14). The face-floor
    dipped-face flux stays at 2.83191e-8 +- 1e-5 relative in every arm (`tests/test_face_floor.cpp:107@dae902b`).
  - `test_x1_seam_split_wb_ref4.<b>` — a cold column whose flag switches on above the seam: the 2-block state equals
    the 1-block state to 1e-13 after 20 steps, and nghost 1 and 2 are refused with "needs nghost >= 3"
    (`tests/test_x1_seam_split.cpp:263-287@dae902b`).
  - `test_x1_seam_split_wb_ref4_gravity_0.<b>` — grav1 = 0 on nghost 1 sets up and steps 5 times finite
    (`tests/test_x1_seam_split.cpp:329-345@dae902b`).
  - `test_x1_seam_split_mp_wb_ref4` — the split across 2 ranks equals 2 blocks in one process and equals 1 block, to 1e-13
    (`tests/test_x1_seam_split_mp.cpp:286-297@dae902b`); CUDA arm `test_x1_seam_split_wb_ref4_cuda.<b>`.
- Limits / known issues: no test runs it on a gnomonic-equiangle (cubed-sphere) grid. ISSUES.md item 3: the spec
  numbers rest on commit c5b810d and must be re-measured with `test_wb_ref4_order.py` at dae902b.
- Discrepancies: `sources/gw__NEXTPR_spec_wbref_exact.md:286` says CUDA and multi-process x1 seams were not run with
  the switch on. At dae902b both are run (`_cuda` and `_mp_wb_ref4` arms). That source is stale.

### Scheme: `SNAP_X1_CENTROID_EXACT` (spherical-polar r^2-average x1 formulas)
- Summary: on spherical-polar grids the x1 reconstruction, the hydrostatic scan and the reference read plain means
  converted from the r^2 cell averages. The radial pressure force becomes the r^2 average of the gradient (a quintic
  through six faces). Switch: env `SNAP_X1_CENTROID_EXACT`, default **off**.
- Derivations: exists: `docs/derivations/x1-centroid-spherical.md@dae902b` (and `sources/deriv__x1-centroid-spherical.md`;
  checked by `docs/derivations/verify_x1_centroid.py@dae902b`).
- Figures: (1) a five-cell window converting r^2 means to plain means, mirrored past a clamped wall; (2) the six-face
  quintic p~ for the radial pressure source, with two faces past the seam taken from the neighbour.
- Code:
  - `src/coord/x1_centroid.cpp:92-101@dae902b` — `x1_centroid_exact_enabled()` — read once.
  - `src/coord/x1_centroid.cpp:104,117@dae902b` — `x1_plain_mean_stencils` (usable iff >=5 cells and enough owned cells
    for the mirrored ghosts); `:157` `x1_plain_means`; `:184,191` `x1_pressure_source_stencils` (usable iff >=6 faces);
    `:224` `x1_pressure_source`.
  - `src/hydro/hydro_forward.cpp:280-296@dae902b` — `HydroImpl::forward` — when spherical-polar, `wx1` holds plain means
    and the seam ghosts come from `_x1_ghost_rows` (tag 0x7724).
  - `src/hydro/hydro_forward.cpp:524-547@dae902b` — the hydrostatic-split correction (non-hydrostatic < 1) uses the same
    r^2 pressure operator.
  - `src/coord/spherical_polar.cpp:252-264@dae902b` — `SphericalPolarImpl::forward` — the radial source with face pressures.
  - `src/hydro/hydro.cpp:251@dae902b` — `HydroImpl::_x1_ghost_rows` — the seam exchange of the switched rows.
  - `src/hydro/wb_ref4.cpp:94@dae902b` — implies `SNAP_WB_REF4`.
  - `src/hydro/balance_column.cpp:35-40@dae902b` — under the switch, `balance_column` refuses any geometry but
    `cartesian`.
- Couplings: implies `SNAP_WB_REF4`, so it inherits the nghost >= 3 setup check (`src/hydro/hydro.cpp:96-103@dae902b`).
  On Cartesian grids it changes nothing beyond that implication. `balance_column` must be called with
  `geometry='cartesian'`.
- Tests:
  - `tests/test_x1_centroid_rest.py` (`test_x1_centroid_rest_python`, `_cuda_python`) — r0 = 5 and 1000, nz 32, implicit 0
    and 1, non-hydrostatic 1 and 0. The force imbalance must be < `TOL_ON = 1e-10` with the switch on, and > `TOL_OFF = 1e-8`
    at r0 = 5 with it off (`tests/test_x1_centroid_rest.py:40-41@dae902b`).
  - `test_balance_column_x1_centroid.<b>` — the predicate implication `wb_ref4_enabled() == (g || w)`
    (`tests/test_balance_column.cpp:353-358@dae902b`); a non-cartesian column is refused (`:363-375,516-524`).
  - `test_face_floor_x1_centroid.<b>` — the same pinned flux as the plain arm.
  - `test_x1_seam_split_x1_centroid.<b>` (+`_cuda`) — 2-block vs 1-block gap <= 1e-13 after 20 steps, nh 1 and 0
    (`tests/test_x1_seam_split.cpp:232-245@dae902b`).
  - `test_x1_seam_split_mp_x1_centroid` — across 2 ranks <= 1e-13 against 2 blocks and against 1 block.
- Limits: not defined for gnomonic-equiangle. `balance_column` cannot balance a spherical column under the switch.
  Coverage of its combination with `gravity-work: face` and radial-exact is missing (see matrix).

### Scheme: `SNAP_FLUX_COVARIANCE` (#289 x2/x3 face-flux covariance and centroid terms)
- Summary: adds sigma1^2 covariance terms and the centroid offset -(r_v - r_c) d1F to the x2/x3 face fluxes, for all rows
  (tracer, dry mass, energy). It mirrors p* = p - delta d1 p in the lateral geometric source, gated per direction.
  Switch: env `SNAP_FLUX_COVARIANCE`, default **off**.
- Derivations: exists: `docs/derivations/289-covariance-x3-curved.md@dae902b` (and `sources/deriv__289-covariance-x3-curved.md`,
  `sources/study__289-allrows_derivation.md`, `sources/deriv__issue289_moist_covariance_verifier.md`;
  `docs/derivations/allrows_quadrature.py`, `verify_centroid_term.py`, `verify_exact_curved.py@dae902b`).
- Figures: (1) an x2 face with the x1 extent of its area measure, marking r_c (face centroid) and r_v (cell centroid);
  (2) the per-direction gating: x2 source with p*, x3 source plain when the x3 flux is off.
- Code:
  - `src/hydro/hydro.cpp:208-218@dae902b` — `HydroImpl::flux_covariance()` — read once.
  - `src/hydro/hydro_forward.cpp:63@dae902b` — `HydroImpl::_flux_covariance` — the term.
  - `src/hydro/hydro_forward.cpp:608-613,631-636@dae902b` — added to `_flux2`/`_flux3`.
  - `src/hydro/hydro_forward.cpp:733-754@dae902b` — the p* geometric source with per-direction gating.
- Couplings: none at setup. It acts on x2/x3 faces whatever the grid (Cartesian, spherical-polar, gnomonic).
  `test_wb_ref4_order.py` uses it as part of the WB_REF4 oracle.
- Tests:
  - `tests/test_horizontal_flux_covariance.py` (`test_horizontal_flux_covariance_python`, ctest env
    `SNAP_GRAVITY_WORK_RADIAL_EXACT=0`) — arms unset/0/1. Off: eps_eff nz^2 in [-0.32,-0.20]. On: |eps_eff nz^2| < 0.04.
    Unset == 0 bitwise. E+PE closes to `EPE_TOL = 1e-12` over `NSTEP = 50` (`tests/test_horizontal_flux_covariance.py:38-40@dae902b`).
  - `tests/test_flux_covariance_rows.py` (`test_flux_covariance_rows_python`, env radial=0) — rest `REST_TOL 1e-9`,
    uniform tracer `1e-13`, offset invariance `1e-10`, dry Cartesian limit within `CART_TOL 2e-3`
    (`tests/test_flux_covariance_rows.py:33-39@dae902b`).
  - `tests/test_flux_covariance_seams.py` (`test_flux_covariance_seams_python`) — six panels with closed walls; drift of
    each total <= `DRIFT_TOL 1e-12` over 10 steps; the gated rest case <= 1e-9; the on/off difference must exceed
    `DIFF_TOL 1e-13` (`tests/test_flux_covariance_seams.py:33-36@dae902b`).
  - `test_wb_ref4_order_python` (on in both arms).
- Limits: study switch, off by default. The covariance seam test is single-process; no MPI run with the term on.

### Scheme: `SNAP_X1_MASS_COVARIANCE` (x1 mass-flux covariance)
- Summary: subtracts dz^2/12 rho_1 w_1 / rho from the velocity handed to the x1 reconstruction, with a one-sided rho_1
  at reflecting walls and an odd-mirror ghost refill. Switch: env `SNAP_X1_MASS_COVARIANCE`, default **off**.
- Derivations: summary-level only in `docs/derivations/curved-gravity-work-weight.md@dae902b` sec 11.4 (the expansion
  is stated; its "ONSET PLACEHOLDER" is unfilled). Re-derive from `src/hydro/hydro_forward.cpp:324-352@dae902b` with an
  executable check.
- Figures: a stratified cell showing m1/rho vs the cell average of w, and the dz^2/12 rho_z w_z face mass excess.
- Code: `src/hydro/hydro_forward.cpp:39-48@dae902b` — static `x1_mass_covariance()` — read once;
  `src/hydro/hydro_forward.cpp:324-352@dae902b` — applied inside the well-balanced x1 branch (`wb_x1`, `:271`:
  grav1 != 0, IPR present, EOS not shallow-water); velocity restored after reconstruction (`:361`).
- Couplings: acts only when the well-balanced x1 path is active.
- Tests: **none** (not referenced in `tests/` or `tests/CMakeLists.txt`).
- Limits: untested, and its onset effect is unmeasured (placeholder in the derivation).

### Scheme: `SNAP_GRAVITY_WORK_RADIAL_EXACT` (option F: corrected-PE gravity work)
- Summary: with `gravity-work: face`, adds g1 sigma^2 s[drho] to each cell's x1 gravity work so that E + P is conserved,
  where P = sum V[rho phi(x1v) - g1 sigma^2 s[rho]]. It is also booked inside the VIC operator and logged as `pe=`.
  Switch: env `SNAP_GRAVITY_WORK_RADIAL_EXACT`, default **on** (acts only with `gravity-work: face`).
- Derivations: exists: `docs/derivations/curved-gravity-work-weight.md@dae902b` secs 7-8 (option F), 10 (every PE site),
  11.2 (why default on); checked by `docs/derivations/curved_gravity_work_weight.py`, `optionF_replica.py@dae902b`.
  Older copy in `sources/deriv__curved-gravity-work-weight.md` (from 6499404, lacks the seam-limit paragraph).
- Figures: (1) a cell with sigma^2 = <(x1-x1v)^2> and the 3-point slope stencil, one-sided at block ends; (2) the
  booking split between the implicit matrix row and the post-solve term.
- Code:
  - `src/hydro/hydro.cpp:222-232@dae902b` — `HydroImpl::gravity_work_radial_exact()` — read once.
  - `src/hydro/hydro.cpp:234-240@dae902b` — `radial_exact_work()` — on, grav1 != 0, `gravity-work: face`, grid
    `cartesian` or `spherical-polar`.
  - `src/hydro/hydro.cpp:83-92@dae902b` — `reset()` — `TORCH_WARN_ONCE` for other grids ("has no form on a '...' grid: the
    x1 wall cells keep the first-order plain face work").
  - `src/hydro/hydro_forward.cpp:826-831@dae902b` — explicit work; the cp3/cp5/weno5 curvature flux is skipped when on
    (`:838`).
  - `src/implicit/implicit_hydro.cpp:288,301-344,451-460@dae902b` — `ImplicitHydroImpl::forward_masked` — the matrix
    coupling and post-solve remainder.
  - `src/hydro/gravity_work_radial.hpp:13,28,57@dae902b` — `x1_variance`, `centroid_slope`, `corrected_pe_work`.
  - `src/mesh/meshblock.cpp:1050-1055@dae902b` — `print_cycle_diagnostics` — logs P instead of PE_d.
- Couplings: inert with `gravity-work: cell` (the default) or `face-wallc`. It never meets the fixer, which requires
  `cell`. On gnomonic-equiangle it warns and keeps the plain face work. At an x1 block seam the slope is one-sided, so
  a split column conserves its own P and differs from one block (by design; `tests/test_x1_seam_split.cpp:12-16@dae902b`).
  With it on, `gravity_work_defect()` and every E+PE_d oracle measure the wrong invariant (`src/hydro/hydro.hpp:170-173@dae902b`).
- Tests:
  - `tests/test_gravity_work_radial_exact.py` (`test_gravity_work_radial_exact_python`, `_cuda_python`) — arms unset/0/1:
    unset == 1 bitwise; per-step |d(E+P)|/|E+P| <= `EP_TOL 1e-14`; logged `ie=`+`pe=` agrees to `DIAG_TOL 1e-11`
    (`tests/test_gravity_work_radial_exact.py:51-53@dae902b`); a gnomonic block warns when on and is silent when off; plus
    VIC clamp and immersed-solid arms.
  - `test_implicit_face_work_operator_python` (env `=0`) and `..._radial_exact_python` (env `=1`)
    (`tests/CMakeLists.txt:232-237,272-274@dae902b`) — `W_TOL 1e-7` m/s at rest, `EPE_TOL 1e-11`
    (`tests/test_implicit_face_work_operator.py:40-41@dae902b`), measured on E+P when on.
  - `test_implicit_stratified_solid_python` (`=0`) / `..._radial_exact_python` (`=1`).
  - `test_implicit_gravity_tall_column_python` — runs both arms itself: rung `W_TOL 1e-7`, settled `1e-10`, on <= 1.1x off
    (`tests/test_implicit_gravity_tall_column.py:31-33@dae902b`).
  - `test_x1_seam_split_radial_exact.<b>` / `_radial_exact_off.<b>` (+`_cuda`) and `test_x1_seam_split_mp_radial_exact[_off]`
    — print the split gap; when on, split E+P drift <= 1e-13 (`tests/test_x1_seam_split.cpp:247-260@dae902b`).
  - Forced off for the plain-face-work oracles: `test_forcing.<b>`, `test_gravity_work_fixer_python`,
    `test_horizontal_flux_covariance_python`, `test_flux_covariance_rows_python` (`tests/CMakeLists.txt:267-270@dae902b`).
- Limits: the seam split differs from one block at O(h^4). Gnomonic grids keep the first-order wall-cell work.
  The convergence-table placeholder in sec 11.3 is unfilled.
- Discrepancies: **the task brief says radial-exact "fails at setup on unsupported grids". At dae902b it does not
  fail: it warns once (`TORCH_WARN_ONCE`, `src/hydro/hydro.cpp:87@dae902b`) and falls back to the plain face work.**
  The test asserts the warning, not an error (`tests/test_gravity_work_radial_exact.py:382@dae902b`). The code wins.

### Scheme: runtime environment for layout/communication
| Var | Default | Read at | Role |
|---|---|---|---|
| `BACKEND` | `default_backend()` (ucx if built with UCX and not Darwin, else gloo) | `src/layout/layout.cpp:190,237@dae902b` | process-group backend; the YAML `distribute/backend` key is accepted but dead (`src/layout/layout.cpp:229-231@dae902b`) |
| `PROCESS_RANK`, `PROCESS_WORLD_SIZE`, `RANK`, `WORLD_SIZE`, `LOCAL_RANK` | `RANK` / `WORLD_SIZE` / 0 | `src/layout/layout.cpp:194-214@dae902b`; `src/layout/layout.hpp:44-50@dae902b` | torchrun ranks |
| `MASTER_ADDR`, `MASTER_PORT` | 127.0.0.1; random port only if single-process | `src/layout/layout.cpp:200-211@dae902b` | a multi-process run without `MASTER_PORT` is a `TORCH_CHECK` error |
| `DEVICE`, `DEVICE_ID` | `cpu`, -1 | `src/layout/layout.cpp:217-218,238@dae902b` | device selection |
| `COMMUX_COALESCE`, `COMMUX_GROUP`, `UCX_TLS` | set to 1, 1, `^cuda_copy,cuda_ipc,gdr_copy` (CPU) only if unset | `src/layout/process_group_ucx.cpp:26-29@dae902b` | UCX tuning defaults |
| `WORKSPACE`, `NC_HOME` | cwd, none | `setup.py:42,62@dae902b` | Python package build only |
- Tests: `test_process_group.<b>` (backend default, BACKEND env overrides YAML, MASTER_PORT rules;
  `tests/test_process_group.cpp:74-186@dae902b`); `test_exchange_ucx` (`BACKEND=ucx`), `test_parentless_cloud_nb1_mp_gloo`
  (`BACKEND=gloo`), `test_sedimentation_cubed_seam_gloo` (`run_seam_backends.py`, `BACKEND` per run).

### Scheme: test-harness environment variables (not read by `src/`)
| Var | Reader | Purpose |
|---|---|---|
| `SNAPY_BUILD_CUDA` | set to 0 on non-CUDA builds (`tests/CMakeLists.txt:517-518@dae902b`); read by python tests, e.g. `tests/test_gravity_work_fixer.py:179@dae902b` | skip (exit 125) CUDA arms |
| `GTEST_FILTER` | `seam_arm` (`tests/CMakeLists.txt:38-46@dae902b`) | one gtest per ctest arm; `PASS_REGULAR_EXPRESSION "[  PASSED  ] 1 test."` makes an empty filter or a skip fail |
| `BLOCKS_PER_PROCESS`, `EXPECT_LOCAL_NEIGHBOR`, `EXPECT_REMOTE_NEIGHBOR` | `tests/test_exchange.cpp:222,303-304@dae902b` | exchange topology (`tests/CMakeLists.txt:161-162,183-186@dae902b`) |
| `SNAPY_RUN_HYDRO` | `tests/test_uranus_cycle1_abort.cpp:47@dae902b` | path to `run_hydro.<b>` |
| `WB_REF_WALL_DUMP`, `WB_REF_WALL_BETAS` | `tests/test_wb_ref_wall.cpp:159,193@dae902b` | review/scan aids |

### Scheme: YAML scheme keys (run-time)
- Summary: keys that select a numerical scheme. Unknown keys are refused by `check_keys` (`src/input/check_keys.cpp:12@dae902b`).
  Python construction (`ConstGravityOptions.gravity_work()`, `.gravity_work_fixer()`, `HydroOptions.wb_wall_clamp`;
  `python/csrc/pyforcing.cpp:28-29@dae902b`, `python/csrc/pyhydro.cpp:34@dae902b`) bypasses YAML. For that reason the
  gravity-work checks are repeated in `HydroImpl::reset()`.

| Key | Default | Parse | Consumer / couplings |
|---|---|---|---|
| `forcing/const-gravity/gravity-work` | `cell` (C++ default `src/forcing/forcing.hpp:58@dae902b`) | `src/forcing/const_gravity.cpp:28-34@dae902b` (cell, face-wallc, face) | re-validated at `src/hydro/hydro.cpp:58@dae902b`; `gw_cell` at `src/hydro/hydro_forward.cpp:239@dae902b`; face-wallc zeroes wall-cell correction `:902-906`; face with implicit and no in-operator work triggers `TORCH_WARN` (#283) at `src/hydro/hydro.cpp:109-118@dae902b`; face work inside the implicit operator iff scheme != 0 (`src/hydro/hydro.cpp:286-290@dae902b`) |
| `forcing/const-gravity/gravity-work-fixer` | = (gravity-work == cell) | `src/forcing/const_gravity.cpp:36-41@dae902b` (set true with non-cell and grav1 != 0 is an error) | forced false for non-cell (`src/hydro/hydro.cpp:64@dae902b`); needs grav2 = grav3 = 0 (`:65-68`) and non-periodic x1 (`:72-81`); active iff grav1 != 0 and cell (`src/hydro/hydro.cpp:202-206@dae902b`) |
| `forcing/const-gravity/grav1,2,3`, `non-hydrostatic` | 0, 0, 0, 1 (in [0,1]) | `src/forcing/const_gravity.cpp:22-26@dae902b` | zeroed by `disable-flux-xN` (`src/hydro/hydro_options.cpp:80-82@dae902b`) |
| `dynamics/wb-wall-clamp` | true | `src/hydro/hydro_options.cpp:57@dae902b` | x1 reference kernel `src/hydro/hydro.cpp:535-537@dae902b`; `balance_column` refuses false (`src/hydro/balance_column.cpp:30-33@dae902b`); bryan `balance-ic` needs it (`examples/bryan.cpp:227@dae902b`) |
| `dynamics/disable-flux-x1/x2/x3`, `verbose` | false | `src/hydro/hydro_options.cpp:53-56@dae902b` | gates the p* source per direction |
| `dynamics/equation-of-state/type` | `moist-mixture` | `src/eos/equation_of_state.cpp:57@dae902b` | shallow-water disables the WB x1 path (`src/hydro/hydro_forward.cpp:271-272@dae902b`) |
| `.../limiter` | false | `src/eos/equation_of_state.cpp:74@dae902b` | flux-positivity limiter and meters (`src/hydro/hydro_forward.cpp:657@dae902b`) |
| `.../density-floor`, `pressure-floor`, `temperature-floor` | 1e-6, 1e-3, 20 | `src/eos/equation_of_state.cpp:65-72@dae902b` | floors / redo |
| `dynamics/reconstruct/{vertical,horizontal}/type,scale,shock` | dc, false, false | `src/recon/reconstruct.cpp:33-36@dae902b` | cp3/cp5/weno5 enable the curvature flux in face work (`src/hydro/hydro_forward.cpp:838-839@dae902b`) |
| `dynamics/riemann-solver/type,dir` | roe, omni | `src/riemann/riemann_solver.cpp:26-27@dae902b` | none |
| `integration/implicit-scheme` | absent = explicit; 0 == absent | `src/implicit/implicit_hydro.cpp:35,71-82@dae902b` | only 0/1/9 accepted (`ImplicitOptionsImpl::type()`, `:84-98`) |
| `integration/implicit-advection-cfl`, `shear-cfl` | 1.0, 0.0 | `src/implicit/implicit_hydro.cpp:59-67@dae902b` | error if set without implicit-scheme (`:37-40`) |
| `geometry/cells/nghost` | 1 | `src/coord/coordinate.cpp:164@dae902b` | >=3 required by WB_REF4 / X1_CENTROID when grav1 != 0 |
| `geometry/type` | cartesian | `src/coord/coordinate.cpp:71@dae902b` | radial-exact acts on cartesian/spherical-polar only; X1_CENTROID acts on spherical-polar only |
| `distribute/layout, nb1, nb2, nb3` | slab, 1, 1, 1 | `src/layout/layout.cpp:233-236@dae902b` | x1 split makes the seam exchanges live |
| `boundary-condition/external/x?-inner/outer` | reflecting | `src/mesh/meshblock_options.cpp:100-193@dae902b` | periodic x1 refused with the fixer |
| `forcing/fric-heat` | removed | refused at `src/hydro/hydro_options.cpp:68-72@dae902b` | none |
- Tests: `test_yaml_keys.<b>` (every block refuses an unknown key; `tests/test_yaml_keys.cpp:63-186@dae902b`);
  `test_hydro_options.<b>` (dynamics/eos/forcing keys, `wb_wall_clamp_ships_enabled`, scheme outside {0,1,9} refused;
  `tests/test_hydro_options.cpp:22-364@dae902b`); `test_implicit_cfl.<b>`; `test_implicit_options_type_python`;
  `test_gravity_work_fixer_python` (fixer guards, face-wallc, Python keys).

### Coverage matrix (switch combination -> ctest entries)
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

## Chapter 13: Conservation budgets and diagnostics

Scope: what snapy measures and prints about its own conservation, and the regression checks that read it. That
covers the cycle line (`mass0=`, `masst=`, `ke=`, `ie=`/`energy=`, `pe=`), the run-to-date meters (`limcut=`,
`thetamin=`, `thetasevere=`, `vicclamp=`, `fixgrav=`), the gravity-work-fixer E+PE budget (D, wall mass, deposit), the
redo cause flags and the termination status, and the output-field diagnostics (`div`, `div_h`, `curl`, `ic_*`).
**Note:** `src/diagnostics/` is legacy Athena++/canoe code (it includes `athena/parameter_input.hpp`). It is not in
the library glob (`src/CMakeLists.txt:35-52@dae902b` lists no `diagnostics/*.cpp`), so it is not compiled. The chapter
must say this, and must not describe it as live. The live diagnostics are in `src/mesh/meshblock.cpp` and
`src/output/load_diag_output_data.cpp`. **Recommendation:** keep the chapter. Move the redo/acceptance mechanics to
Ch.7 and keep only "what the cause flags report" here. Cross-reference the fixer physics to Ch.6, which owns the
derivation; this chapter owns the budget bookkeeping and its printout.

### Scheme: cycle-line budget (`print_cycle_diagnostics`)
- Summary: every `ncycle_out` cycles, one line sums the interior conserved state times cell volume over all local
  blocks, reduces it to the root rank, and prints it. Switch: `integration/ncycle_out` (parsed by pyharp; 0 disables,
  `src/mesh/meshblock.cpp:1010-1012@dae902b`).
- Terms (each a volume integral over interior cells):
  - `mass0=` sum u[IDN] V (dry density); `masst=` sum (u[IDN] + sum_n u[ICY+n]) V, printed if species exist
    (`src/mesh/meshblock.cpp:1091-1096@dae902b`).
  - `ke=` sum 0.5 m_i m^i / rho_total V. The momentum is raised with the metric (`coord_vec_raise_` with
    `cosine_cell_kj`) and the density is the total over all constituents. It is read from `hydro_u`, never from the
    stage-stale `hydro_w` (`src/mesh/meshblock.cpp:1038-1044@dae902b`).
  - `ie=` (MeshBlock line) / `energy=` (Mesh line) = sum u[IPR] V, the total energy E (`:1098-1099`; labels set at
    `src/mesh/meshblock.cpp:1114-1118@dae902b` and `src/mesh/mesh.cpp:409-419@dae902b`, precision max_digits10-4 vs -3).
  - `pe=` sum rho_total(-g1 x1v) V, printed only with const-gravity grav1 != 0. When `radial_exact_work()` it logs the
    corrected P = PE_d - sum V g1 sigma^2 s[rho], so `ie=`+`pe=` is the conserved E+P (`src/mesh/meshblock.cpp:1045-1056,1100@dae902b`).
- Derivations: ke with a non-orthogonal metric: re-derive from `src/mesh/meshblock.cpp:1038-1044@dae902b` (the test
  states the closed form 13/0.75 vs 25, `tests/test_cycle_diagnostics.cpp:209-212@dae902b`). The P form: exists:
  `docs/derivations/curved-gravity-work-weight.md@dae902b` sec 7 and sec 10 (PE-site table).
- Figures: (1) annotate one cycle line, mapping each token to its integral and reduction op (SUM/MIN/MAX); (2) a
  Mesh with two local blocks on two ranks: local sums, then one reduce to root, then one line.
- Code: `src/mesh/meshblock.cpp:1004-1112@dae902b` — `print_cycle_diagnostics`; reductions at `:1074-1086`;
  `src/mesh/cycle_diagnostics.hpp:11-14@dae902b`; `src/mesh/mesh.cpp:409-419@dae902b` — `MeshImpl::print_cycle_info`.
- Tests: `test_cycle_diagnostics.<b>` — `logged_ke_scales_with_density` (2x within 1e-9 rel), `logged_ke_reads_the_conserved_state`
  (4x), `logged_ke_sums_the_constituents` (1.25x for a dry-only denominator), `logged_ke_raises_the_momentum_with_the_metric`
  (13/18.75), `logged_pe_is_the_column_geopotential` (2.5*10*zvol within 1e-9), `mesh_aggregates_all_local_blocks_once`
  (1e-11, one `cycle=` line) (`tests/test_cycle_diagnostics.cpp:72-407@dae902b`); `test_cycle_diagnostics_parallel.<b>`
  (2 ranks x 2 blocks, 1e-11; `tests/test_cycle_diagnostics_parallel.cpp:25@dae902b`); `test_gravity_work_radial_exact_python`
  check 5 (`ie=`+`pe=` = E+P on, E+PE_d off, to `DIAG_TOL 1e-11`); `test_restart_cycle_limit` (the restart leg's
  `time`, `dt`, `mass0`, `energy` match the base run to atol 1e-12; `tests/run_restart_cycle_limit.py:186-189@dae902b`).
- Limits: the `ke`/`pe` sums ignore immersed-solid masking. "Run-to-date" meters reset on restart (buffers are not in
  the restart file; `sources/gh__PR_BODIES_202-219.md` #217 Limits). `pe=` uses the per-block one-sided slope at x1
  seams (sec 7 seam limit).
- Discrepancies: `sources/gh__PR_BODIES_202-219.md` (#217, Limits) says ke/pe/meters are on the MeshBlock line only and
  that the Mesh line "never printed ke". At dae902b both lines come from the same `print_cycle_diagnostics`
  (`src/mesh/mesh.cpp:417@dae902b`) and differ only in the energy label and precision. The PR text is superseded.

### Scheme: positivity-limiter meters (`limcut`, `thetamin`, `thetasevere`, hits)
- Summary: run-to-date counters of the species flux-positivity limiter, accumulated only when
  `equation-of-state/limiter: true` and species exist. Switch: the `limiter` YAML key (default false).
- Terms: hits = count of interior (cell, species) with theta < 1. severe = theta < 0.9 AND withheld mass > round-off
  (4096 ulp float64, 64 ulp float32, times the cell's gas mass). thetamin = run minimum of theta. limcut = sum of the cut
  x1 flux divided by the sum of the offered x1 flux, printed only if the offered flux > 0.
- Derivations: round-off bound rationale: re-derive from `src/hydro/flux_positivity.hpp:10-23@dae902b` (constants
  `kPositivityRoundoffUlp = 4096`, `kPositivityRoundoffUlpFloat = 64`) and `src/hydro/hydro_forward.cpp:668-678@dae902b`.
- Figures: a settling column showing theta = dx/(dt|vsed|) = 0.5 on five interior faces, with offered vs cut flux bars.
- Code: `src/hydro/hydro_forward.cpp:657-714@dae902b` — accumulation in `HydroImpl::forward`; buffers registered at
  `src/hydro/hydro.cpp:178-185@dae902b`; printed at `src/mesh/meshblock.cpp:1102-1107@dae902b`; scalar module has its own
  hits counter (`src/scalar/scalar.cpp:160,189@dae902b`, not printed).
- Tests: `test_cycle_diagnostics.<b>` — `positivity_meters_read_their_hand_computed_values` (thetamin 0.5, severe 5,
  limcut 0.5, to 1e-9 on buffers and 1e-5 on the printed line), `positivity_severe_needs_more_than_roundoff_withheld`,
  `positivity_severe_float32_needs_more_than_roundoff_withheld` (`tests/test_cycle_diagnostics.cpp:269-366@dae902b`);
  `meter_group_is_marked_run_to_date` (token order).
- Limits: thetamin/thetasevere print their initial values (1, 0) when the limiter never ran (#217 Limits).

### Scheme: VIC clamp meter (`vicclamp`)
- Summary: the largest per-cell relative residual between the constituent change and the face transfer M(i)-M(i+1)
  after the implicit availability clamp. It is 0 unclamped and sum(y) when every constituent is starved. Switch:
  printed whenever an implicit scheme is active (`picorr`).
- Code: `src/implicit/implicit_hydro.cpp:360-378@dae902b` (dtype-safe floor: float min in float32, 1e-300 in float64);
  accessor `src/implicit/implicit_hydro.hpp:89@dae902b`; reduced MAX and printed at `src/mesh/meshblock.cpp:1067-1070,1086,1108@dae902b`.
- Derivations: re-derive from `src/implicit/implicit_hydro.cpp:360-378@dae902b` (the residual definition and why it
  equals sum(y) for a fully starved face).
- Figures: a 2-cell column with one face; the dry-only transfer under starvation, so each cell misses M sum(y).
- Tests: `test_cycle_diagnostics.<b>` `vicclamp_reads_the_clamped_fraction` (0.03 within 1e-12; < 1e-12 unclamped;
  `tests/test_cycle_diagnostics.cpp:367-405@dae902b`); `test_lu_failure.<b>` `float_rest_column_finite_vicclamp`,
  `double_rest_column_finite_vicclamp` (`tests/test_lu_failure.cpp:351-354@dae902b`, #294).
- Limits: a run maximum, not per step.

### Scheme: gravity-work fixer E+PE budget (D, wall mass, `fixgrav`)
- Summary: with `gravity-work: cell` and the fixer on (the default), each stage measures the dynamics' change of E+PE_d
  (cell work + face work of the extra limiter/sedimentation mass + Phi times the x1 mass divergence + the VIC change).
  The stages are summed with their RK weights into D. After the last stage, one global reduction deposits -D as heat
  uniform per unit mass. `fixgrav=` prints the accepted-step total. Switch: `gravity-work-fixer` (default true with cell).
- Code (budget terms): `gwfix_stage` per stage (`src/hydro/hydro_forward.cpp:869-898@dae902b`); implicit part via the `epe`
  lambda before/after the solve (`:957-978`); stage weight cw = w2_s prod_{t>s} w1_t (rk3: 1/6, 1/6, 2/3), accumulated
  into `_gwfix_d` (`:995-1004`); wall-face mass `_gwfix_wall` (`:889-897`); 5-vector of sums {D, sum mV, wall mass, wall-cell
  mass, redo flag} (`src/mesh/meshblock.cpp:844-868@dae902b`); deposit dE_i = -D m_i / sum m_j V_j, guarded by
  wall <= 1e3 eps * mwall (`src/mesh/meshblock.cpp:870-911@dae902b`, check at `:899`; `fixgrav=` printed at `:1109-1110`). Pending/total accounting: committed
  at the next step's stage 0 or on acceptance, dropped on redo (`src/hydro/hydro.hpp:182-198@dae902b`;
  `src/mesh/meshblock.cpp:614,1250,1274@dae902b`). Multi-block sum then one allreduce at `src/mesh/mesh.cpp:341-363@dae902b`;
  single block at `src/mesh/meshblock.cpp:832-840@dae902b`.
- Derivations: exists: `sources/gw__GRAVITY_WORK_TECH_REPORT_draft.md` sec 3.6 (eqs. 3.13-3.15). Its line cites are
  pre-dae902b; re-anchor them. Re-derive the stage weight cw from `src/hydro/hydro_forward.cpp:995-1004@dae902b`.
- Figures: (1) a per-stage flow: D^s contributions, weighted sum, global allreduce, uniform-per-mass deposit;
  (2) a closed column with sealed walls, the wall-face mass meter and the 1e3 eps bound.
- Tests: `test_gravity_work_fixer_python` — default cell+fixer |d(E+PE)|/|E+PE| <= `TOL 1e-12`
  (`tests/test_gravity_work_fixer.py:38@dae902b`), explicit and VIC; fixer off drifts > 100 TOL; refuses outflow,
  periodic, grav2 != 0; float32 run; `fixgrav=` reported. `test_straka_redo` — cfl 1.6 redoes steps with the fixer on and
  reaches tlim (`tests/run_straka_redo.cmake:31@dae902b`). `test_forcing.<b>` `implicit_correction_reports_total_energy_delta`
  (`tests/test_forcing.cpp:538@dae902b`).
- Limits: refused for open/periodic x1 and grav2/grav3 != 0 (`src/hydro/hydro.cpp:65-81@dae902b`). The large-Courant
  wall round-off can exceed the bound (comment at `src/mesh/meshblock.cpp:889-896@dae902b`, #285). Not carried across a
  restart.
- Discrepancies: the draft cites `src/mesh/meshblock.cpp:828-835` and `src/hydro/hydro.cpp:177-181` for the reduction
  and the guard. At dae902b these are `src/mesh/meshblock.cpp:832-840` and `src/hydro/hydro.cpp:202-206`.

### Scheme: redo causes and termination status (diagnostic view)
- Summary: the per-step acceptance decision is a 6-bit cause mask (floor, clamp, limiter, nan, saturation, vic-solve),
  allreduced MAX across ranks and printed in "Redoing the step ... (causes: ...)". `finalize` prints the termination
  reason and returns 1 on "Terminating abnormally".
- Code: `src/mesh/meshblock.cpp:1212-1218@dae902b` `limiter_hits`; `:1229-1276` `apply_redo` (message `:1236`);
  `:1278-1286` `local_redo_flags`; `:1288-1300` `reduce_redo_flags`; `src/mesh/mesh.cpp:422@dae902b`
  `MeshImpl::check_redo`; termination `src/mesh/meshblock.cpp:1127-1140@dae902b`.
- Derivations: none (logic).
- Figures: a cause-bit table and the redo loop.
- Tests: `test_check_redo_floor_python`, `test_check_redo_saturation_python` (+cuda), `test_check_redo_parallel.<b>`,
  `test_uranus_cycle1_abort.<b>` (`abnormal_termination_exits_nonzero`), `test_forcing.<b>` limiter-redo cases
  (`tests/test_forcing.cpp:660-848@dae902b`), `test_lu_failure.<b>`.
- Limits: Ch.7 owns the mechanics; this chapter only references them.

### Scheme: output-field diagnostics
- Summary: optional NetCDF fields requested by name in an output block: `div`, `div_h` (horizontal), `curl` (vector in
  3-D, `curl[VEL3]` in 2-D), all under `diagnostics`; `ic_dry`, `ic_mom`, `ic_etot`, `ic_<species>` (implicit
  correction); also `theta`, `rh_*` with `thermo`. Switch: the `outputs/N/variables` list.
- Code: `src/output/load_diag_output_data.cpp:47@dae902b` `OutputType::loadDiagOutputData`; div/curl `:166-217`;
  implicit `:220-260`; called from `src/output/output_type.cpp:191@dae902b`.
- Derivations: none new (they use `pcoord->divergence`/`curl`, Ch.3).
- Figures: none needed.
- Tests: `test_user_output.<b>` `OutputDiagnostics.*` (virtual potential temperature, divergence of uniform velocity is
  0, Cartesian curl of solid-body rotation, gnomonic finite; `tests/test_user_output.cpp:792-910@dae902b`).
- Limits: no PE or budget field is written to NetCDF (`docs/derivations/curved-gravity-work-weight.md@dae902b` sec 10
  table).

### Scheme: mass-conservation regression checks
- Summary: tests that assert conservation of mass, species or energy to round-off on specific operators.
- Derivations: none here; each identity is derived in the chapter that owns the operator.
- Figures: a matrix of conserved quantity × operator × test.
- Code: the operators are cited in their chapters; the orphan runner is `tests/run_example_mass_check.py:29@dae902b`.
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
    (`tests/run_example_mass_check.py:29,133-144@dae902b`). **Not registered** in `tests/CMakeLists.txt` at dae902b
    (orphan).
- Limits: no registered test checks `mass0=` drift over a full example run (only the orphan script).

---

## Chapter 15: Verification catalogue

Scope: an index of every ctest entry registered by `tests/CMakeLists.txt@dae902b`, grouped by the chapter that owns the
topic (chapter numbers from the proposed outline). Each entry gives one line on what it asserts and the tolerance where
it is visible. It also lists the example decks used as regression (straka, bryan, shallow-water, uranus) and the files
that exist but are not registered. **Recommendation:** keep this chapter as the human-readable index. Generate the
appendix test index (Ch.17) from `ctest -N` at the pinned sha, so the two cannot drift. Ch.12.4's switch matrix is the
other view.

### Scheme: registration mechanics and labels
- `setup_test(name)` -> ctest `name.<b>`, a gtest binary, no labels (`cmake/macros/macro_setup_test.cmake:8-34@dae902b`).
- `setup_parallel_test(name N)` -> `name.<b>` run by `torchrun --no-python --nproc-per-node=N`
  (`cmake/macros/macro_setup_parallel_test.cmake:8-34@dae902b`).
- `snapy_add_python_test(name ...)` -> ctest `name_python`, with labels and timeout, enrolled for `SNAPY_TEST_PYTHONPATH`
  (`tests/CMakeLists.txt:201-218@dae902b`).
- Switch arms: `seam_arm` (`:38-46`), `seam_arm_mp` (`:78-83`), the `_wb_ref4`/`_x1_centroid` duplicates (`:93-101`), the
  `_radial_exact` python duplicates (`:232-237`).
- Labels in use: `python`, `boundary`, `exchange`, `ucx`, `gpu`, `cuda`, `cubed-sphere`, `diagnostic`, `forcing`, `eos`,
  `positivity`, `hydro`, `implicit`, `gravity`, `energy`, `mesh`, `redo`, `coordinate`, `scalar`, `reference`,
  `restart`, `examples`, `decomp`, `gloo`, `long`.
- Gates: `if(CUDA)` registrations; `UCX_FOUND`; `APPLE` (`test_gloo_one_tensor` only on Apple, restart tests only on
  non-Apple); `FULL_TESTS`. Non-CUDA builds disable entries with `cuda` in the name or a `cuda`/`gpu` label
  (`tests/CMakeLists.txt:514-533@dae902b`). C++ `_cuda` gtest cases inside CPU binaries skip via `snapy_cuda_test_enabled()`.
- CI: Linux runs all registered entries except `test_shallow_xy_decomp`. PRs use FULL_TESTS=OFF; push/manual runs on
  Linux use ON (`.github/workflows/ci.yml:87,105-113@dae902b`). macOS PRs run only `test_eos`, `test_plm`,
  `test_gloo_one_tensor`, `test_python_import_path_python`.
- Figures: a tree from the CMake option set to the registered and enabled entries.

### Scheme: Ch.2 Equations and thermodynamics (EOS)
| ctest | Asserts | Tol |
|---|---|---|
| `test_eos.<b>` | fix_vapor limiter accepts zero column, repairs bottom from above, rejects net-deficit/single-cell without writing; moist-mixture and ideal-moist energy offsets; ideal-gas offset is zero; prim2cons with 5 clouds | 1e-14 typical |
| `test_eos_temp2inteng_python` | "UT->I" == "W->I" over a T sweep; ie(T) affine with intercept u0 | rtol 1e-12 |
| `test_eos_species_registry_python` | a block's EOS ignores later rewrites of kintera's global species tables (compute and a full step bitwise) | 1e-14 |
| `test_two_cards_species.<b>` | a block keeps card A's species/parents after card B loads (limiter, sedvel; with controls) | exact |
| `test_cloud_parent_slots.<b>` | nucleation parent found when the card has unused species; a negative cloud borrows from its parent | exact |
| `test_condensate_conservation.<b>` | a multi-vapor condensate debits stoichiometric mass | exact |
| `test_hydro_options.<b>` (EOS part) | every EOS key accepted and read; bad `uv-solver` refused by kintera | n/a |

### Scheme: Ch.3 Grids and geometry
| ctest | Asserts | Tol |
|---|---|---|
| `test_coordinate.<b>` | gnomonic area/volume, spherical-polar vs Athena formulas, vector lower/raise, contravariant transforms, flux projections, radial source uses face pressure; programmatic/decomposed coordinates match the global grid bitwise | 1e-15 to 1e-14 |
| `test_radial_face_moments.<b>` | curved x1 face centroid shift and second moment equal the exact rationals (#289) | 1e-14 |
| `test_cubed_sphere_cell_volume_python` | six panels sum to 4/3 pi (ro^3-ri^3); discrete div(r rhat) = 3; rest run | 1e-12; `REST_TOL 1e-6` |
| `test_cubed_sphere_exchange.<b>` | subdivided-panel exchange equals one block (nb2 = 1, 2, 4); comm tag collision refused | exact |
| `test_local_horizontal_cells_python` | `set_local_horizontal_cells` leaves every axis resolved | 1e-12 |
| `test_refine.<b>` | refine functions | n/a |

### Scheme: Ch.4 Spatial discretization
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

### Scheme: Ch.5 Hydrostatic and well-balanced treatment
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
| `test_bryan_balance_ic` | bryan `balance-ic`: passes = 1 fails with the cap error; default converges; the dry case does not enter the moist loop (`tests/run_bryan_balance_ic.cmake:27-61@dae902b`) | TIMEOUT 21 s |

### Scheme: Ch.6 Gravity and energy
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

### Scheme: Ch.7 Time integration (RK3, VIC, LU, CFL, redo)
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

### Scheme: Ch.8 Positivity, floors, limiters
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

### Scheme: Ch.9 Diffusion, sedimentation, forcing
| ctest | Asserts | Tol |
|---|---|---|
| `test_diffusion.<b>` | option parsing; viscous/conductive Laplacians; sine-mode decay; wall faces read no ghost; timestep bounds | 1e-12 to 1e-3 |
| `test_diffusion_moist.<b>` | moist conduction uses the local mixture cp; limiter uses nucleation parents | 1e-12 / 1e-3 |
| `test_diffusion_x1_scale.<b>`, `test_diffusion_x1_scale_python` | x1 profiles (tensor or YAML table): unity profile is bitwise the no-profile run, scaled decay rates, 2nd-order convergence, refusals | 1e-12 / bitwise |
| `test_forcing.<b>` | options, Coriolis (cubed sphere), relax-bot-*, sponge covariance, body heat, boundary fluxes, fused sedimentation == tensor path | 1e-12 / 1e-9 |
| `test_sedimentation_guards.<b>` | refuses a card without const-gravity; skipped when x1 flux off; rising cloud from the cell below | 1e-9 |
| `test_sedimentation_cubed_seam.<b>` (2 ranks), `test_sedimentation_cubed_seam_gloo` | seam repair with sedimentation and limiter; Gloo result == UCX bitwise (17 digits) | exact |
| `test_jit_user_forcing_python` | a scripted user forcing adds the expected tendency | `assert_close` default |

### Scheme: Ch.10 Moist coupling
| ctest | Asserts | Tol |
|---|---|---|
| `test_wall_saturation.<b>` | phase change at a wall preserves energy and water | 1e-12 |
| `test_balance_column.<b>` `a_moist_column_with_one_condensable_comes_out_at_rest` | moist balance; vapor unchanged | 1e-12 |
| `test_check_redo_saturation_python` | see Ch.7 | pinned |

### Scheme: Ch.11 Boundary conditions
| ctest | Asserts | Tol |
|---|---|---|
| `test_radiating_boundary.<b>` | radiating modes on all faces, mixed faces, tracers ride dry density, acoustic pulses, restart reference, decomposed faces, CPU == CUDA | 1e-12 |
| `test_radiating_boundary_python` | a manual Python fill needs the saved reference | n/a |
| `test_rectify.<b>`, `test_flip_zero_count.<b>` | internal-boundary solid rectification; flip count thread-safe (8 threads == serial) | exact |
| `test_wb_wall_corner.<b>` | see Ch.5 | 1e-12 |

### Scheme: Ch.12 Configuration
| ctest | Asserts | Tol |
|---|---|---|
| `test_yaml_keys.<b>` | 30 cases: every option block refuses an unknown key, named by path | n/a |
| `test_hydro_options.<b>` | dynamics/eos/forcing key whitelists; `fric-heat` refused; scheme not in {0,1,9} refused; `wb-wall-clamp` ships true and reaches the reference; non-map blocks refused | n/a |
| `test_process_group.<b>` | backend and `MASTER_PORT` env rules | n/a |
| `test_python_import_path_python` | `SNAPY_TEST_PYTHONPATH` wiring | n/a |
| switch arms | see Ch.12.4 matrix | |

### Scheme: Ch.13 Diagnostics
| ctest | Asserts | Tol |
|---|---|---|
| `test_cycle_diagnostics.<b>` | 11 cases, see Ch.13 | 1e-9 / 1e-11 / 1e-12 |
| `test_cycle_diagnostics_parallel.<b>` | 2 ranks aggregate once | 1e-11 |
| `test_user_output.<b>` `OutputDiagnostics.*` | div/curl/theta_v fields | 1e-12 |

### Scheme: Ch.14 Parallelism, GPU, restart/IO
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

### Scheme: examples used as regression
| Example | Deck(s) | ctest | Check |
|---|---|---|---|
| straka (2-D density current; cartesian, weno5, lmars, ideal-gas, grav1 -9.8, nghost 3, default gravity-work cell+fixer) | `examples/straka.yaml`, `straka_single.yaml`, `straka_proc2.yaml`, `straka_mesh2.yaml` | `test_straka` (label `reference`; 2 ranks; vs Zenodo `straka-ref.nc`), `test_straka_redo`, all restart tests | L2 of theta difference < 50 (`tests/test_straka.py:17@dae902b`) |
| shallow_xy (cartesian shallow-water, shallow-roe) | `shallow_xy*.yaml` | `test_shallow_xy` (FULL, 4 ranks), `test_shallow_xy_decomp` | L2 of rho < 50; decomp bitwise |
| shallow_splash (gnomonic shallow-water) | `shallow_splash*.yaml` | `test_shallow_splash` (FULL, 6 ranks), `test_shallow_splash_decomp`, `_ucx_cuda_decomp` | L2 of rho < 50 (`tests/test_shallow_splash.py:17@dae902b`) |
| bryan (moist bubble; ideal-moist, limiter, weno5, lmars) | `examples/bryan.yaml` edited in place | `test_bryan_balance_ic` | balance-ic cap/convergence/dry path |
| uranus (moist-mixture, VIC 1) | `tests/test_uranus_cycle1_abort.yaml`, `test_uranus_late_abort.yaml`, `test_abnormal_exit_floor.yaml` via `run_hydro.<b>` | `test_uranus_cycle1_abort.<b>` | termination strings and exit code |
| shock, jupiter_*, earth_crm, run_hydro | built (`examples/CMakeLists.txt:5-11@dae902b`) | none (CI's macOS exclude list names `test_shock_cpu`, `test_run_hydro_cpu`, which are not registered at dae902b) | none |

- Figures: (1) a pyramid of the test suite: unit gtests, python oracles, switch arms, multi-rank, reference examples;
  (2) a bar chart of entries per chapter.
- Limits / known issues:
  - Reference checks use a loose L2 < 50 on the final theta/rho field against Zenodo files
    (`tests/run_straka.cmake:8@dae902b`), which needs network access or a cached file.
  - `tests/run_example_mass_check.py` is not registered (orphan). `run_shallow_*.cmake` are registered only under FULL_TESTS.
  - The CI macOS exclude regex names `test_shock_cpu` and `test_run_hydro_cpu`, which do not exist at dae902b (stale).
  - CUDA arms are never run in CI.
  - Python ctests test the installed snapy unless `SNAPY_TEST_PYTHONPATH` is set (warning at
    `tests/CMakeLists.txt:357-359@dae902b`).
- Discrepancies: #217's Limits (Mesh line lacks ke) is superseded (see Ch.13). `gw__NEXTPR_spec_wbref_exact.md:286`
  (no CUDA or multi-process runs of WB_REF4) is superseded by the arms at `tests/CMakeLists.txt:55-87@dae902b`.
