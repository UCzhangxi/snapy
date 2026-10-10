# Outline inventory: Chapters 1, 3, 14 (snapy at dae902b)

All code locations are `path:line@dae902b`, checked with grep -n / sed -n.
ctest names: `setup_test(X)` registers `X.release` in the default Release build (`cmake/macros/macro_setup_test.cmake`);
`setup_parallel_test(X n)` registers `X.release` run as `torchrun --no-python --nproc-per-node=n`
(`cmake/macros/macro_setup_parallel_test.cmake`); `snapy_add_python_test(X)` registers `X_python`
(`tests/CMakeLists.txt:201`). When the build has no CUDA, every test whose name or label contains cuda/gpu is DISABLED
(`tests/CMakeLists.txt:514-532`).

---

## Chapter 1: Overview and code map

Scope: one time step from driver to kernels (MeshBlock / Mesh, RK stages, hydro forward and its seven sections, scalar,
implicit entry, outputs, redo), CPU/GPU dispatch, tensor layout and indexing, options/YAML/env switches, the Python
package and the external dependencies. Recommendation: keep it as a code map with a step-flow diagram. Move the redo /
`check_redo` details into the chapter that owns limiters and positivity (it is only pointed to here). Put the
environment-switch inventory (S1.14) in an appendix table that the physics chapters cite, so they do not each restate it.
One cross-chapter fact belongs here: `MeshBlock::forward` and `Mesh::forward` order the ghost exchange differently
(S1.5, S1.6).

### Scheme 1.1: Driver loop (time step, stages, redo, outputs)
- Summary: the driver (C++ example or Python) calls `max_time_step`, then `forward(vars, dt, stage)` once per integrator
  stage, then `check_redo`, then `make_outputs`. snapy has no built-in main loop. Switch: integrator `type`, `cfl`, `tlim`, `nlim`
  come from the YAML `integration:` block, read by pyharp's `harp::IntegratorOptionsImpl::from_yaml`. snapy calls it at
  `src/mesh/meshblock_options.cpp:43@dae902b`, and its own key check lists pyharp's keys
  (`src/implicit/implicit_hydro.cpp:27-30@dae902b`).
- Derivations: none (control flow).
- Figures:
  - Flow chart: cycle → max_time_step (MIN-allreduce) → stages s=0..S-1 [exchange → hydro → scalar → user forcing →
    RK combine → limiter → (last stage: saturation adjust, gravity-work fixer) → boundaries] → check_redo (MAX-allreduce)
    → outputs.
  - Timeline of one cycle with the redo branch (dt halves by 2^-redo).
- Code:
  - `examples/run_hydro.cpp:161@dae902b` — single-MeshBlock loop (`pintg->stop`, `max_time_step`, stage loop, kinetics,
    `check_redo`, `make_outputs`). Output before the loop only on a fresh start (`:157`).
  - `examples/straka.cpp:110@dae902b` — Mesh-API loop (`mesh->initialize`, `set_cycle`, stage loop, `check_redo`,
    `make_outputs`, `finalize`). It calls `make_outputs` right after initialize, on restart too (`:139`).
  - `src/mesh/meshblock.cpp:510@dae902b` `MeshBlockImpl::max_time_step` — local hydro dt, MIN-allreduce. Returns
    `2^-current_redo * cfl * dt` (`:528`).
  - `src/mesh/mesh.cpp:306@dae902b` `MeshImpl::max_time_step` — MIN over the local blocks, then one allreduce.
  - `src/mesh/meshblock.cpp:1302@dae902b` `check_redo` = `apply_redo(reduce_redo_flags(local_redo_flags()))`
    (`:1229`, `:1278`, `:1288`). `src/mesh/mesh.cpp:422@dae902b` `MeshImpl::check_redo` checks signals first, ORs the
    flags over the local blocks, then makes one reduction.
  - `src/mesh/meshblock.cpp:985@dae902b` `make_outputs` — writes when `current_time >= next_time` (`:991`), then
    advances `next_time` and `file_number`.
  - `src/mesh/meshblock.cpp:1121@dae902b` `finalize` — writes the final outputs and reports the termination reason (signal / nlim /
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

### Scheme 1.2: MeshBlock construction (`reset`)
- Summary: builds the layout (process group), nulls the boundary functions of internal faces, builds outputs,
  integrator, coordinate, hydro, scalar, internal boundary, and the stage registers u0/s0. Switch: the `MeshBlockOptions`
  sub-options (from YAML via `MeshBlockOptionsImpl::from_yaml`).
- Derivations: none.
- Figures: a module tree (MeshBlock → Layout, Integrator(harp), Coordinate, Hydro{EOS(kintera thermo), Recon, Riemann,
  Forcings, Implicit, Sedimentation}, Scalar, InternalBoundary, OutputTypes).
- Code:
  - `src/mesh/meshblock.hpp:41@dae902b` `MeshBlockOptionsImpl`. `:116` `MeshBlockImpl`.
  - `src/mesh/meshblock.cpp:66@dae902b` constructor — `resolve_global_grid()`, and checks that bfuncs has at least 2/4/6 entries.
  - `src/mesh/meshblock.cpp:111@dae902b` `reset`. `:116` `LayoutImpl::create`. `:143` internal-face bfunc set to
    nullptr (slab/cubed only). `:207` output types. `:231` `harp::IntegratorImpl::create`. Then coord, hydro, scalar and
    ib follow in order. u0/s0 are float64 buffers `[nvar, nc3, nc2, nc1]`.
  - `src/mesh/meshblock_options.cpp:13@dae902b` `MeshBlockOptionsImpl::from_yaml` — the order is layout, hydro, scalar
    (scalar recon defaults to hydro recon23), integrator, outputs, coordinate, ib, external BCs.
- Tests: `tests/test_yaml_keys.cpp` (`test_yaml_keys.release`) — 30 cases, each of which refuses an unknown key in its
  YAML block.
- Limits / known issues: the world size must equal px·py·pz (·6 for cubed-sphere), `meshblock.cpp:133`.
- Discrepancies: none.

### Scheme 1.3: Initialization
- Summary: check the shapes of `hydro_w` (and `scalar_r`), apply the physical boundaries to primitives, exchange
  primitive ghosts (interpolating), compute conserved `hydro_u = W->U`, seed `scalar_s = u[IDN]*r`, then fill solids and
  apply the boundaries to conserved variables. Restart replaces all of this with `_init_from_restart` (Ch14 S14.9).
  Switch: `restart_file` argument.
- Derivations: none.
- Figures: sequence of one block's init, showing where the ghosts become valid.
- Code: `src/mesh/meshblock.cpp:360@dae902b` `initialize`; `:401` `initialize_local`; `:434` `initialize_under_mesh`
  (the Mesh path); `:454` `finalize_initialization`; `src/mesh/mesh.cpp:280@dae902b` `MeshImpl::initialize`. A restart
  calls `blocks[i]->initialize(vars[i], file)` one block after another on the caller thread, with no exchange.
- Tests: covered by every example test. Nothing targets this scheme alone.
- Limits / known issues: the restart path does no ghost exchange. It relies on the ghost zones saved in the file
  (`restart.cpp:29-36` saves whole tensors).
- Discrepancies: none.

### Scheme 1.4: Stage update `advance_local` (MeshBlock)
- Summary: stage 0 saves u0/s0 and resets the per-step meters. Then come hydro `forward` (returns du), scalar `forward`
  (plus the implicit dry-mass tracer transfer and the dry-source carry), user TorchScript stage forcings, the RK combine
  `pintg->forward(stage,u0,u,du)`, the conserved limiter, and the solid refill. The last stage also runs kintera
  saturation adjustment and the gravity-work fixer. `apply_boundaries` runs at the end. Switch: integrator stages (harp);
  `user_stage_forcings` (Python `set_user_stage_forcings`).
- Derivations:
  - RK stage form u ← w0 u0 + w1 u + w2 du and the stage weights: external (pyharp). Re-derive the weight product
    `w2_s ∏_{t>s} w1_t` from `src/hydro/hydro_forward.cpp:994-1004@dae902b`.
  - Implicit tracer transfer `(P - P_above)/V` with upwinded r: re-derive from `src/mesh/meshblock.cpp:663-675@dae902b`.
  - Dry-source carry rule: re-derive from `src/mesh/meshblock.cpp:633-645@dae902b`.
- Figures:
  - Box diagram of du accumulation (flux divergence, forcings, implicit, user) feeding the RK combine.
  - Stage-by-stage timeline marking where `rk_stage` is published (used by the implicit dt weight).
- Code: `src/mesh/meshblock.cpp:597@dae902b` `advance_local`; `:612` u0 save; `:650` `phydro->forward`; `:662`
  `pscalar->forward`; `:734` user forcing call; `:755` RK combine (hydro); `:768` RK combine (scalar); `:813`
  `pthermo->forward` (kintera ThermoY saturation adjustment, interior only); `:838` gravity-work fixer; `:841`
  `apply_boundaries`. The user forcing contract (keys `hydro_du`, `scalar_ds` only) is at `:690-720`.
- Tests: `tests/test_user_output.cpp` (`test_user_output.release`) —
  `UserForcing.scripted_stage_forcings_add_tendencies_in_list_order`, `..._rejects_unsupported_keys`,
  `..._module_is_shared_across_parallel_blocks`; `tests/test_jit_user_forcing.py` (`test_jit_user_forcing_python`).
- Limits / known issues: saturation adjustment runs only when `thermo()->reactions().size() > 0`, on the last stage.
- Discrepancies: none.

### Scheme 1.5: `MeshBlock::forward` (exchange-then-advance)
- Summary: a single-block driver exchanges conserved and scalar ghosts BEFORE reconstruction, so operator-split sources
  the driver applied since the last stage (e.g. kinetics on `hydro_u`) are synchronised before use. Switch: none.
- Derivations: none.
- Figures: two orderings side by side, exchange-before-advance (MeshBlock) and advance-then-exchange (Mesh).
- Code: `src/mesh/meshblock.cpp:545@dae902b` `forward` (`:550` `exchange_ghost_zones`, `:551` `advance_local`);
  `:913` `exchange_ghost_zones` (conserved, then scalar, then the x1-wall corner refresh `:972`, then the scalar primitive).
- Tests: indirect (all single-block examples).
- Limits / known issues: the in-code comment says that exchanging before reconstruction removed a one-signed seam bias
  on the cubed sphere. No regression test isolates that.
- Discrepancies: see S1.6. Mesh orders it the other way.

### Scheme 1.6: Mesh (several blocks per process)
- Summary: `Mesh` owns `blocks_per_process` MeshBlocks and runs them concurrently on a worker-thread pool, with one CUDA
  stream per block on GPU. `Mesh::forward` runs `advance_local` on every block, then the global gravity-work fixer (one
  sum over the local blocks, one allreduce), then `exchange_ghost_zones`. Switch: YAML
  `distribute: blocks_per_process` (default 1), read at `src/mesh/mesh.cpp:216-217@dae902b`.
- Derivations: none.
- Figures: thread/stream diagram (caller stream → event → per-block streams → events joined back to the caller).
- Code: `src/mesh/mesh.cpp:47@dae902b` `BlockWorkerPool` (`:57` stream from the pool per block, `:82` `submit` with
  event fences); `:225` `MeshImpl::reset` (clones the options and repartitions each block, `:246-248`); `:265`
  `run_block_jobs`; `:331` `MeshImpl::forward`; `:377` `exchange`; `:460` `finalize`.
- Tests: `tests/test_mesh_multi_block.cpp` (`test_mesh_multi_block.release`, 2 ranks) — ghost sides uniform and equal to
  the neighbour id, both a local and a remote neighbour seen; `tests/test_mesh_exchange.py` (`test_mesh_exchange_python`)
  — every ghost equals the neighbour's rank exactly; `tests/test_cubed_sphere_exchange.cpp` checks one CUDA stream per
  block (`EXPECT_EQ(num_worker_streams, blocks)`).
- Limits / known issues:
  - Blocks of one process must advance concurrently. In-process x1 messages wait at most 5 min
    (`src/layout/layout.cpp:879-899@dae902b`).
  - Remote block-to-block messages allow at most 16 blocks per process (`layout.cpp:849-857`).
- Discrepancies: with `blocks.size()==1`, `Mesh::forward` (`mesh.cpp:335-338`) calls `advance_local` and THEN
  `exchange_ghost_zones`, the reverse of `MeshBlock::forward` (S1.5). A Mesh-API driver that applies operator-split
  sources between `forward` calls therefore reconstructs from ghosts exchanged before those sources (inferred from the
  code; not measured). The cubed-sphere decomposition report (`canoe__cubedsphere_decomposition_TECH_REPORT.md` §4)
  reasons from the MeshBlock order only.

### Scheme 1.7: Hydro forward (code map of its seven sections)
- Summary: (1) EOS U→W; (2) x1 reconstruction with the optional well-balanced reference, x1 Riemann flux, sedimentation,
  x1 seam averaging; (3) x2/x3 LR states and the cubed-sphere seam swap; (4) x2/x3 fluxes, optional #289 covariance,
  tracer positivity limiter; (5) flux divergence and geometric sources (Coordinate::forward); (6) forcings and gravity
  work; (7) implicit correction. Switches: listed per physics chapter. The env switches are in S1.14.
- Derivations: owned by the hydro, WB, gravity-work and positivity chapters. None here.
- Figures: a pipeline diagram of the seven sections, marking the three places that communicate (x1 seam average, LR
  seam swap, θ exchange).
- Code: `src/hydro/hydro_forward.cpp:207@dae902b` `HydroImpl::forward`; `:218` `peos->forward`; `:242` section 2;
  `:297` `_hydro_ref_x1`; `:357` x1 reconstruction (WB path, floor=false); `:413` x1 Riemann; `:430` sedimentation;
  `:448` x1 seam average; `:551`/`:569` x2/x3 LR; `:598`/`:623` x2/x3 flux; `:646` positivity; `:724`/`:735`
  divergence; `:763`/`:773` forcings; `:924` implicit; `:941` stage weight on the implicit dt (rk3 only); `:977`
  `_apply_implicit_correction`. Buffers F1/F2/F3/P1/D: `src/hydro/hydro.cpp:152@dae902b` ff.
- Tests: owned by the physics chapters.
- Limits / known issues: the implicit stage weight is applied only when `stages.size()==3` (`hydro_forward.cpp:939`).
  Other integrators keep the full-dt operator.
- Discrepancies: none.

### Scheme 1.8: Scalar forward
- Summary: tracer reconstruction and upwind flux driven by the hydro mass flux. The cubed-sphere LR states use the same
  `:+`/`:-` raw swap as hydro, and θ is exchanged as a raw copy. Switch: YAML `scalar:` (read at
  `src/scalar/scalar_options.cpp:11@dae902b`).
- Derivations: owned by the scalar/positivity chapter.
- Figures: none here (see Ch3 S3.11).
- Code: `src/scalar/scalar.cpp:64@dae902b` `ScalarImpl::forward`; `:84` sync options; `:96` `scalar_wl:+`; `:144` θ
  raw copy.
- Tests: `tests/test_scalar.cpp` (`test_scalar.release`); the seam tests are listed in Ch3.
- Limits / known issues: none.
- Discrepancies: none.

### Scheme 1.9: CPU/GPU dispatch (DispatchStub + TensorIterator; CUDA loops)
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
  - example CPU path: `src/hydro/hydro_dispatch.cpp:14@dae902b` `hydro_ref_x1_cpu` (`AT_DISPATCH_FLOATING_TYPES` +
    `at::parallel_for` over columns); the MPS path is a tensor-op reimplementation in the same file.
  - `src/utils/loops.cuh:53@dae902b` `gpu_kernel`; `:71` `stencil_kernel` (block = line length).
  - `src/recon/recon_dispatch.cu:18@dae902b` `recon_tile_width`, `:47` `stencil_kernel_tiled` (the fix for issue #251).
  - `src/CMakeLists.txt:122-155@dae902b` — the `*.cu` glob and the `snapy::snap_cu` library.
- Tests: `tests/test_weno5_cuda_line.cpp` (`test_weno5_cuda_line.release`, CUDA builds only) — lines of 32, 1024, 1025,
  1030 and 1280 cells match CPU, `EXPECT_LT(diff, 1e-12)`. `tests/test_coordinate.cpp` DeviceTest runs on CPU and CUDA,
  float32 and float64. The MPS parameter is commented out (`tests/device_testing.hpp:48`).
- Limits / known issues:
  - `call_cs_interp_LR/BT` have CPU kernels only and no caller: the call is commented out
    (`src/coord/gnomonic_equiangle.cpp:556-563`).
  - `bdot_out` (`src/utils/utils_dispatch.cu:70`) still uses the untiled `stencil_kernel` and has no caller in `src/`.
  - MPS registrations exist but no test runs them.
- Discrepancies: none.

### Scheme 1.10: Tensor layout, variable indices, ghost zones, interior slices
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
  - `src/snap.h:34-46@dae902b` index enum; `:52` static_assert ICY==IPR+1; `:60` kPrimitive/kConserved/kScalar.
  - `src/coord/coordinate.hpp:59@dae902b` `nc1()`; `:169` `il()`; `:171` `iu()`.
  - `src/mesh/meshblock.hpp:105@dae902b` `PartOptions`; `src/mesh/meshblock.cpp:284@dae902b` `part`.
  - `src/recon/reconstruct.cpp:50@dae902b` `_apply_inplace` — cell j writes `IRT[j]` (its lower face) and `ILT[j+1]`.
  - Variables keys: `hydro_w`, `hydro_u`, `scalar_r`, `scalar_s`, `solid`, `fill_solid_hydro_{w,u}`,
    `boundary_reference_{w,r}` (`meshblock.cpp:401-508`).
- Tests: indirect.
- Limits / known issues: a block with nx1=1 stores no x1 ghosts (`nc1()==1`), so x1 stencils fall back to edge forms
  (`tests/test_pref_local_seam.cpp:4-7`).
- Discrepancies: none.

### Scheme 1.11: Options objects and YAML
- Summary: every option struct uses `ADD_ARG(T,name)` (chainable getter/setter). `from_yaml` readers build the tree.
  `check_keys` refuses an unknown key in 29+ fixed-key blocks. Switch: YAML top-level sections `distribute`,
  `geometry`, `dynamics`, `forcing`, `integration`, `scalar`, `sedimentation`, `boundary-condition`, `outputs`,
  `verbose`. kintera reads `species` and `reference-state`.
- Derivations: none.
- Figures: a YAML-section → reader-function map.
- Code: `src/add_arg.h:9@dae902b` `ADD_ARG`; `src/input/check_keys.cpp:12@dae902b` `check_keys`;
  `src/layout/layout.cpp:221@dae902b` (distribute); `src/coord/coordinate.cpp:62@dae902b` (geometry);
  `src/hydro/hydro_options.cpp:15@dae902b` (dynamics, `:44`); `src/hydro/register_forcing_modules.cpp:6@dae902b`
  (forcing); `src/scalar/scalar_options.cpp:11@dae902b`; `src/sedimentation/sed_options.cpp:19@dae902b`;
  `src/output/output_type.cpp:64@dae902b` (outputs); `src/mesh/meshblock_options.cpp:88-208@dae902b`
  (boundary-condition); `src/eos/equation_of_state.cpp:86@dae902b` (`kintera::ThermoOptionsImpl::from_yaml`).
- Tests: `tests/test_yaml_keys.cpp` (`test_yaml_keys.release`).
- Limits / known issues: `distribute: backend` is still accepted but dead; the backend comes from env `BACKEND`
  (`layout.cpp:229-231`, PR #242). The top level is not key-checked.
- Discrepancies: none.

### Scheme 1.12: Python package `snapy`
- Summary: a pybind11 extension built by `setup.py` against the CMake build. It exposes options, Mesh/MeshBlock, layouts,
  `SyncOptions`, `distributed.set_process_group`, `load_restart`. Importing it sets float64 as the default dtype and 1
  torch thread. Switch: none.
- Derivations: none.
- Figures: none.
- Code: `python/csrc/snapy.cpp:32@dae902b` module, `:47` `load_restart`; `python/csrc/pymesh.cpp:126@dae902b`
  `set_local_horizontal_cells`, `:184` `forward`; `python/csrc/pylayout.cpp:136-141@dae902b` `distributed` submodule
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

### Scheme 1.13: External dependencies (kintera, pyharp, torch, comm and IO libraries)
- Summary: kintera supplies the thermodynamics (`ThermoY` saturation adjustment, species tables), constants, and tensor
  (de)serialisation for restart. pyharp supplies the time integrator (`harp::Integrator`) and radiation. pydisort is
  imported by `python/__init__.py`. commux supplies UCX, pinc supplies PnetCDF, NetCDF is a system library. Switch: CMake
  `find_package(Kintera 2.5.13 REQUIRED)` (`CMakeLists.txt:101`), `find_package(Harp REQUIRED)` (`:96`); UCX via commux
  (`cmake/ucx.cmake`), PnetCDF via pinc (`cmake/parameters.cmake:28-43`).
- Derivations: none.
- Figures: dependency graph.
- Code: `src/mesh/meshblock.hpp:17@dae902b` (`harp/integrator/integrator.hpp`); `src/mesh/meshblock.cpp:231@dae902b`;
  `src/mesh/meshblock.cpp:808-813@dae902b` (`kintera::ThermoYImpl`); `src/output/restart.cpp:90@dae902b`
  (`kintera::save_tensors`); `src/input/read_restart_file.cpp:223@dae902b` (`kintera::load_tensors`).
- Tests: none specific.
- Limits / known issues: the integrator stage weights and `stop()` live in pyharp and cannot be cited at a snapy line.
  `CMakeLists.txt:97-100` records why the kintera floor is 2.5.13 (saturation-failure counter, kintera #131).
- Discrepancies: none.

### Scheme 1.14: Environment-variable switch inventory (appendix table)
- Summary: run-time numerics switches are read once per process (static lambdas), so every block in a process makes the
  same choice. Nothing checks that ranks agree.
- Derivations: per the owning physics chapter.
- Figures: none.
- Code (name / reader / default):
  - `SNAP_X1_CENTROID_EXACT` / `src/coord/x1_centroid.cpp:96@dae902b` / "0".
  - `SNAP_WB_REF4` / `src/hydro/wb_ref4.cpp:87@dae902b` / "0". It is also implied by `SNAP_X1_CENTROID_EXACT`
    (`wb_ref4.cpp:94`).
  - `SNAP_X1_MASS_COVARIANCE` / `src/hydro/hydro_forward.cpp:41@dae902b` / "0".
  - `SNAP_FLUX_COVARIANCE` / `src/hydro/hydro.cpp:212@dae902b` / "0".
  - `SNAP_GRAVITY_WORK_RADIAL_EXACT` / `src/hydro/hydro.cpp:226@dae902b` / "1". It acts only with `gravity-work: face`.
  - Parallel / IO: `BACKEND`, `DEVICE`, `DEVICE_ID`, `RANK`, `LOCAL_RANK`, `WORLD_SIZE`, `PROCESS_RANK`,
    `PROCESS_WORLD_SIZE`, `MASTER_ADDR`, `MASTER_PORT` (`src/layout/layout.cpp:189-219@dae902b`). commux defaults
    `COMMUX_COALESCE=1`, `COMMUX_GROUP=1`, and `UCX_TLS` without CUDA transports when DEVICE=cpu
    (`src/layout/process_group_ucx.cpp:26-30@dae902b`).
- Tests: the seam arms in `tests/CMakeLists.txt:38-87` set these per ctest entry.
- Limits / known issues: a rank-to-rank mismatch in a numerics switch would make shared faces two-valued, with no check.
  This follows from the code comments; no test covers it.
- Discrepancies: none.

---

## Chapter 3: Grids and geometry

Scope: coordinate systems (Cartesian, spherical-polar, gnomonic equiangular cubed sphere), the metric quantities the FV
update uses (face areas, volumes, centroids, widths, geometric sources, local-frame projections), how the global grid is
cut into blocks (layouts, rank maps, connectivity), and what a ghost cell contains at each seam type (panel edges, x1
seams between blocks, corners). Recommendation: keep geometry and decomposition together. Leave the transport of
ghosts (buffers, tags, backends) to Ch14 and keep here only what the ghost values ARE. The radial face moments and the
x1 centroid belong to both this chapter and the #289/WB chapters: put the geometric identities here and the flux use
there. A short subsection should say that `cylindrical` is a registered but empty type (S3.15).

### Scheme 3.1: One global grid, sliced per block (decomposition-invariant faces)
- Summary: each block's faces are a slice of ONE global `linspace` per axis, and cell widths come from the global
  `(gmax-gmin)/gnx`. A face therefore has the same double in every block and every decomposition (PR #222).
  `resolve_global_grid` adopts the block as the global grid when none was declared, and otherwise checks that the block
  is exactly nx cells of it. Switch: YAML `geometry: {type, bounds, cells:{nx1,nx2,nx3,nghost,interp_order}}`. Defaults:
  type cartesian (`coordinate.hpp:97`), nghost 1 (`:116`), interp_order 2 (`:117`); global_nxN=0 means "no global grid".
- Derivations: none needed (a design invariant). The rationale is the comment at `src/coord/coordinate.cpp:291-298@dae902b`
  and PR #222 (`gh__PR_BODIES_220-226.md:190`): 1 ULP made 15/71 faces inconsistent and 26 differ between decompositions.
- Figures:
  - One global face array with nb2=2 and nb2=3 slices marked, plus the ghost extension past gmin/gmax.
  - A "before" panel where per-block linspace gives two values of one shared face (1 ULP).
- Code: `src/coord/coordinate.cpp:62@dae902b` `CoordinateOptionsImpl::from_yaml` (`:118` bounds-only card = one cell
  per axis; `:143` nx%nb divisibility; `:182` repartition); `:186` `_resolve_axis` (16·eps tolerance, exact cell
  count); `:226` `resolve_global_grid`; `:235` `repartition` (block bounds from loc_of; cubed-sphere forces lx1=0);
  `:283` constructor (faces sliced); `:307` `block_faces_`; `src/coord/coordinate.hpp:76@dae902b` `dx1()` (global
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

### Scheme 3.2: Cartesian metric
- Summary: uniform widths from the global dx. Areas are products of widths, volume the triple product, centroid =
  midpoint, cos θ=0. Switch: `geometry.type: cartesian`.
- Derivations: trivial. Note "re-derive from `src/coord/coordinate.cpp:425-439@dae902b`" for completeness.
- Figures: a cell with face areas A1=dx2·dx3 etc.
- Code: `src/coord/cartesian.cpp:8@dae902b` `CartesianImpl::reset`; `src/coord/coordinate.cpp:425@dae902b`
  `face_area1`, `:429`, `:433`, `:437` `cell_volume`, `:509` `divergence`, `:585` `forward` (pure divergence).
- Tests: `test_coordinate.release` `CoordinateProgrammatic.cell_volume_is_the_product_of_the_callers_widths`.
- Limits / known issues: none.
- Discrepancies: none.

### Scheme 3.3: Spherical-polar metric and geometric sources
- Summary: (r,θ,φ). x1v is the r²-volume centroid and x2v the sinθ centroid. A1 = r²|Δcosθ|Δφ, A2 = ½Δ(r²)sinθΔφ,
  A3 = ½Δ(r²)Δθ, V = Δ(r³)/3·|Δcosθ|·Δφ. Geometric sources use coord_src{1,2}_i and coord_src{1,2,3}_j. The x1
  pressure source uses the face pressures, or under SNAP_X1_CENTROID_EXACT the quintic r-moment. Switch:
  `geometry.type: spherical-polar` (x2 must lie in [0,π], `spherical_polar.cpp:46`).
- Derivations:
  - Centroids, areas, volume, source coefficients: re-derive from `src/coord/spherical_polar.cpp:17@dae902b`,
    `:42`, `:178-211`. The test compares them to Athena++ reference formulas but gives no derivation.
  - Face-pressure form of the radial source: re-derive from `src/coord/spherical_polar.cpp:265-277@dae902b`.
  - r² cell-to-face maps and the quintic pressure source: exists: docs/derivations/x1-centroid-spherical.md@dae902b
    (also sources/deriv__x1-centroid-spherical.md).
- Figures:
  - A spherical shell cell showing r_v (volume centroid) vs the midpoint vs the area centroid r_c.
  - Where coord_src1_i/2_i act (radial momentum source vs angular-momentum flux terms).
- Code: `src/coord/spherical_polar.cpp:17@dae902b` `radial_centers`; `:23` `polar_centers`; `:42` `reset`; `:89`
  `coord_src1_i`; `:178` `face_area1`; `:185` `face_area2`; `:193` `face_area3`; `:200` `cell_volume`; `:213`
  `face_moment2_x1`; `:219` `face_centroid_shift_x1`; `:224` `forward` (sources).
- Tests: `test_coordinate.release` `SphericalPolar.geometry_matches_athena_reference_formulas` (allclose 1e-12/1e-12
  on x1v, x2v, areas, volume, coord_src*); `DeviceTest.radial_source_uses_face_pressure_in_x1_momentum`,
  `radial_source_preserves_face_pressure_gradient`; `tests/test_x1_centroid_rest.py` (`test_x1_centroid_rest_python`).
- Limits / known issues: the docs/derivations line citations of spherical_polar.cpp predate dae902b (see S3.5
  discrepancy).
- Discrepancies: none beyond S3.5.

### Scheme 3.4: Gnomonic equiangular cubed sphere (geometry and metric)
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
    `src/coord/cubed_sphere6.nb@dae902b` is a Mathematica notebook with sections "Christoffel symbols", "Metric terms
    (flux form)", "Finite volume (length, area, volume)", "Orthonormal projection" and "Ghost zone Interpolation". It is
    symbolic, not a prose derivation, and not in sources/ or docs/derivations. Re-derive in prose from
    `src/coord/gnomonic_equiangle.cpp:18@dae902b` (reset) and `:415@dae902b` (forward), and check against the notebook.
  - Exact solid angle of a gnomonic cell (corner-sum formula, six panels sum to 4π): re-derive from
    `src/coord/gnomonic_equiangle.cpp:124-137@dae902b`.
  - Cubed-sphere face measure w(r)=r, and A2 = ∫r dr × angle: exists: docs/derivations/289-covariance-x3-curved.md@dae902b
    §1.3(c).
  - Contravariant↔spherical↔Cartesian velocity transforms: re-derive from `src/coord/gnomonic_equiangle.h:79@dae902b`
    (`gnomonic_contra_to_sph`) and `:105` (`gnomonic_sph_to_contra`). Doxygen formulas exist in
    `src/coord/cubed_sphere_utils.hpp` (basis vectors, partial).
  - Covariant/contravariant lowering (`coord_vec_lower_`, g23 = cos θ): re-derive from
    `src/coord/coord_utils.cpp:12@dae902b`.
- Figures:
  - The cube net with face ids 0..5 (+X,+Y,-X,+Z,-Y,-Z) and local (α,β) axes per panel (from the ASCII art at
    `cubed_sphere_layout.cpp:156-237`).
  - One gnomonic cell: non-orthogonal axes at angle θ, arc widths, the solid-angle corner sum.
  - cos θ over a panel (zero at the centre and the centre lines, -1/2 at corners). This is why covariance errors hide at
    panel centres (forcing_io report).
- Code: `src/coord/gnomonic_equiangle.cpp:18@dae902b` `reset` (`:65` lon/lat, `:80` cos θ, `:104` `dx2f_ang_kj`,
  `:130-137` solid angle, `:142` `x_ov_rD_kji`); `:199`/`:203` `center_width2/3`; `:207` `face_area1`; `:211`
  `face_area2`; `:215` `face_area3`; `:219` `cell_volume`; `:229` `face_moment2_x1`; `:237`
  `face_centroid_shift_x1`; `:266`/`:281` `_set_face{2,3}_metric` (marked "TODO(cli):: CHECK"); `:295`-`:323`
  `prim2local1/2/3_`; `:344`-`:387` `flux2global1/2/3_`; `:415` `forward` (geometric sources);
  `src/coord/gnomonic_equiangle.h:33@dae902b` `gnomonic_sin_cos`, `:45` `gnomonic_prim2local`, `:60`
  `gnomonic_flux2global`; `src/coord/coord_utils.cpp:12@dae902b` `coord_vec_lower_`, `:29` `coord_vec_raise_`;
  `src/coord/coordinate.cpp:611@dae902b` `boundary_velocity_` (g23-aware frame for wall BCs, used by
  `src/bc/bc_func.cpp:152`); Riemann solver use: `src/riemann/hllc.cpp:58-99@dae902b`, `src/riemann/lmars.cpp:56@dae902b`.
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

### Scheme 3.5: Radial face moments and the face-centroid shift (curved-grid helpers)
- Summary: on spherical-polar and cubed-sphere grids an x2/x3 face weighs r dr while a cell weighs r² dr. snapy
  provides the exact second central moment σ1² = (h²/12)(1-h²/(12 r̄²)) and the shift r_v - r_c =
  h²(12r̄²-h²)/(12r̄(12r̄²+h²)), both cancellation-free, both zeroed on degenerate ghost faces with r̄ ≤ h/2. In
  Cartesian they are h²/12 and 0. Switch: used only when `SNAP_FLUX_COVARIANCE` is on (S1.14).
- Derivations: exists: docs/derivations/289-covariance-x3-curved.md@dae902b §2.6-2.7 (moments, r_c, and the
  comparison with x1v); also sources/deriv__289-covariance-x3-curved.md.
- Figures: a radial cell with r_m, r̄, r_c, r_v, r_p marked; σ1²/(h²/12) as a function of h/r̄.
- Code: `src/coord/coordinate.hpp:254@dae902b` (`face_moment2_x1` doc), `:270`, `:285`; `src/coord/coordinate.cpp:442@dae902b`
  `face_moment2_x1`, `:446` `radial_face_moment2_`, `:461` `face_centroid_shift_x1`, `:467` `radial_face_centroid_shift_`.
- Tests: `tests/test_radial_face_moments.cpp` (`test_radial_face_moments.release`) — rational cases to 1e-13 relative,
  closed forms to 1e-14 relative, per-cell indexing (47/1176) to 1e-14.
- Limits / known issues: none.
- Discrepancies: the derivation's line citations (e.g. `coordinate.cpp:429-435`) are shifted at dae902b
  (`face_area2` `:429`, `face_area3` `:433`, consistent). Spot-check each when writing.

### Scheme 3.6: Layouts and rank maps (slab, cubed, cubed-sphere)
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
  hops) from `src/layout/cubed_sphere_layout.cpp:445@dae902b` and `:498@dae902b`.
- Figures:
  - Morton order on a 4×4 block grid.
  - The cube net with the CS_FACE_EDGES table drawn as arrows (neighbour face, side, reversal flag).
  - (rank → process, local block) mapping for bpp>1.
- Code: `src/layout/layout.hpp:52@dae902b` `LayoutOptionsImpl` (`:98` type default slab, `:83-93` block↔process maps);
  `src/layout/layout.cpp:221@dae902b` `from_yaml`; `:246` `LayoutImpl::create`; `src/layout/slab_layout.cpp:10@dae902b`
  (pz==1 `:12`), `:41` `neighbor_rank`; `src/layout/cubed_layout.cpp:10@dae902b`, `:40`;
  `src/layout/connectivity.cpp:28@dae902b` `build_zorder_coords2`, `:45` `build_zorder_coords3`;
  `src/layout/cubed_sphere_layout.hpp:80@dae902b` face-major rank; `src/layout/cubed_sphere_layout.cpp:246@dae902b`
  `CS_FACE_NAMES`, `:309` `CS_FACE_EDGES`, `:413` `_initialize` (pz==1, px==py), `:445` `_step_one`, `:481`
  `rank_of`, `:488` `loc_of`, `:498` `neighbor_rank`; `src/mesh/meshblock_options.cpp:102@dae902b`,`:142`,`:179`
  (periodic flags from BC names).
- Tests: `tests/test_exchange.cpp` + `run_exchange_decomp.py` (`test_exchange_decomp`: mesh6 / proc6 / proc2_mesh3 on
  gloo) — ghost values equal the expected neighbour, with both local and remote neighbours seen.
- Limits / known issues:
  - x1 decomposition exists only for `cubed`; the cubed sphere has no x1 split (`cubed_sphere_layout.cpp:415`).
  - On a cubed sphere with pz>1, x1 ghosts of θ would be neither exchanged nor overwritten. That configuration is
    refused (theta-seam report §7).
- Discrepancies: none.

### Scheme 3.7: Physical vs internal faces (bfunc assignment)
- Summary: YAML boundary names become bfuncs. At construction every face shared with a neighbour (or periodic in a
  layout direction) gets bfunc=nullptr, and `is_physical_boundary` means "a bfunc is installed". On the cubed sphere the
  panel edges carry the no-op `custom_inner/outer` bfuncs and are NOT nulled. The cubed-sphere exchange ignores
  `is_physical_boundary`, so ghosts still arrive. Switch: YAML `boundary-condition: external: {x1-inner, ..., x3-outer}`
  (default "reflecting").
- Derivations: none.
- Figures: a 2×2 slab decomposition with the faces coloured physical/internal/periodic.
- Code: `src/mesh/meshblock.cpp:137-178@dae902b` (nulling, slab/cubed only); `src/mesh/meshblock_options.cpp:218@dae902b`
  `face_of`, `:229` `is_physical_boundary`, `:243` `is_wall_boundary` (whitelist); `src/bc/bc_func.cpp:7-8@dae902b`
  `custom_inner/outer` (empty); `src/hydro/hydro.cpp:195@dae902b` `is_x1_wall`.
- Tests: `tests/test_forcing_cubed_sphere.yaml` header documents a vacuous-test trap (nx1=1 ⇒ no x1 bfunc ⇒ every
  top/bottom forcing returns early).
- Limits / known issues: on the cubed sphere `is_physical_boundary(dy,dx,0)` is TRUE at panel edges (custom bfunc).
  Code that loops over all bfuncs (e.g. the θ ghost fill at `hydro_forward.cpp:694-697`) applies the no-op there. Any
  future x2/x3 "physical boundary" test would misclassify panel edges (inferred from code).
- Discrepancies: none.

### Scheme 3.8: Generic ghost exchange (what is filled)
- Summary: for each face-adjacent neighbour (corners skipped by default) the interior slab is packed and received into
  the ghost slab. A sync can be conserved, primitive or scalar, with `interpolate` (cubed-sphere cross-panel only),
  `skip_corner`, `dim` (face-state syncs) and phase flags. After a sync, `fill_corners` averages the two adjacent edge
  strips into each x2-x3 corner. Transport details are in Ch14 S14.3. Switch: `SyncOptions`
  (`src/layout/layout.hpp:135@dae902b`); defaults skip_corner=true, interpolate=false, type kConserved.
- Derivations: corner value = ½(left strip + bottom strip) is a convention. Re-derive (state it) from
  `src/layout/layout.cpp:710@dae902b`.
- Figures: the 3×3 neighbour stencil with buffer ids (`get_buffer_id`), interior slabs sent vs ghost slabs received,
  and corners synthesised.
- Code: `src/layout/layout.hpp:32@dae902b` `get_buffer_id`; `src/layout/layout.cpp:477@dae902b` `serialize`; `:668`
  `deserialize`; `:710` `fill_corners`; `:753` `finalize` (corner synthesis unless a split phase);
  `src/mesh/meshblock.cpp:554@dae902b` `exchange`.
- Tests: `test_exchange.release` (2 ranks, bpp 3); `test_mesh_multi_block.release`; `test_mesh_exchange_python`;
  `tests/test_cubed_sphere_vertical_velocity_exchange.py` (`..._python`) — a radial velocity passes panel seams
  unchanged to 1e-12 abs + 1e-12 rel.
- Limits / known issues: corners of x1×x2 (and x1×x3) blocks are never exchanged. At physical x1 walls they are
  refreshed (S3.14); at internal x1 seams they keep stale values (inferred). No dimension-split stencil reads them, but
  cross-derivative operators could.
- Discrepancies: none.

### Scheme 3.9: Cubed-sphere cross-panel ghost interpolation
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
  - Ghost-centre mapping (`cs_build_ghost_usrc`): re-derive from `src/coord/cubed_sphere_utils.cpp:78@dae902b`.
  - rev/flip/transpose rules from side parity: re-derive from `src/layout/cubed_sphere_layout.cpp:701-705@dae902b`.
- Figures:
  - Two panels meeting at an edge: ghost centres in layers g=1..3 and their source points sliding toward the edge
    midpoint (Figure 1 of the source report, to be redrawn).
  - A subdivided panel: the widened strip reaching into the sender's intra-panel halo; the two-phase timeline.
  - Frame rotation pipeline: contravariant(sender) → spherical → (send) → interpolate in the sender frame → spherical →
    contravariant(receiver).
- Code: `src/coord/cubed_sphere_utils.hpp:108@dae902b` `cs_interp_margin`; `src/coord/cubed_sphere_utils.cpp:78@dae902b`
  `cs_build_ghost_usrc`, `:259` `cs_velocity_transform_matrix`, `:300` `cs_apply_velocity_transform_`;
  `src/coord/gnomonic_equiangle.cpp:162-196@dae902b` (global usrc + integer shift), `:245` `interp_ghost`, `:475`
  `_interp_ghost_LR`, `:516` `_interp_ghost_BT`; `src/layout/cubed_sphere_layout.cpp:122@dae902b`
  `_velocity_transform` (cached, one radial plane), `:549` `serialize` (`:630` phase-1 return, `:681` margin, `:703-705`
  flags), `:795` `deserialize` (`:848`, `:936` `interp_ghost`), `:961` `exchange_remote` (`:1014` same-panel phase
  filter); `src/mesh/meshblock.cpp:554-572@dae902b` the two-phase branch.
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

### Scheme 3.10: Cubed-sphere face-state seam sync (hydro and scalar LR states)
- Summary: for x2/x3 fluxes, the reconstructed L/R states at panel-edge faces are exchanged as raw copies (depth 1, no
  interpolation, cross-panel only), keyed `*_wl:+` and `*_wr:-`. The suffix selects a directional partial send/receive,
  so the L/R roles resolve correctly at same-sign edges, and both panels solve the same Riemann problem. The scalar
  originally used one un-suffixed key, which swapped L/R on the four same-sign edges and made one face anti-upwind
  (fixed). Switch: none (always on for the cubed-sphere layout).
- Derivations: the anti-upwind mechanism and the role of the suffix: exists:
  sources/canoe__tracer_seam_TECH_REPORT.md §4-6 (argument, not algebra).
- Figures: a same-sign edge (e.g. 1T-3R) with L/R arrows before and after the suffix protocol.
- Code: `src/hydro/hydro_forward.cpp:553-596@dae902b` (`:563` keys, begin/launch/finalize); `src/scalar/scalar.cpp:84@dae902b`,
  `:96`; `src/layout/cubed_sphere_layout.cpp:602@dae902b`, `:715`, `:837`, `:928` (suffix rules); `:704-705`
  (trans/flip flags, no-ops on depth-1 strips).
- Tests: `tests/test_flux_covariance_seams.py` (`test_flux_covariance_seams_python`) — mass, vapour and E+PE conserved
  across seams to round-off with the #289 term on; the tracer seam fix has no dedicated ctest beyond the positivity
  seam test (S3.11).
- Limits / known issues: none.
- Discrepancies: the tracer-seam report cites `cubed_sphere_layout.cpp:711` for `flip_flag`. At dae902b it is `:705`.

### Scheme 3.11: θ (positivity donor factor) across seams: raw copy
- Summary: a face's donor factor θ must be the donor's own number on both sides, or the limiter leaks mass. θ is
  therefore exchanged with `interpolate(false)` (raw index-matched copy). The interpolated cubed-sphere ghost had been a
  blend at every depth. The species enthalpy is recomputed from the ghost W instead of being exchanged (#238). Switch:
  active when `eos.limiter` and ny>0.
- Derivations: conservation needs one shared factor per face: exists: sources/canoe__theta_seam_TECH_REPORT.md §1, §6
  (argument).
- Figures: a seam face with the donor on panel A, θ_A vs the interpolated blend on panel B, and the leaked mass.
- Code: `src/hydro/hydro_forward.cpp:680-697@dae902b` (`:687-688` `topts.interpolate(false)`, `:694` bfunc ghost fill);
  `src/scalar/scalar.cpp:144@dae902b`.
- Tests: `tests/test_flux_positivity_cubedsphere.py` (`test_flux_positivity_cubedsphere_python`, + `_cuda`) — 6 panels in
  one process, hat edge on the +X/+Y seam, tracers conserved to DRIFT_TOL=1e-13 (in the script), hits>0, the hat stays
  in [0,1]; `tests/test_flux_positivity_cubedsphere_moist.py` (+ `_cuda`); `test_sedimentation_cubed_seam.release`
  (2 ranks).
- Limits / known issues: corners keep θ=1 (skip_corner). A corner is never the donor of a consumed face (report §7).
- Discrepancies: the report banner cites `hydro_forward.cpp:341`/`scalar.cpp:144` for the raw copies. The hydro line is
  `:688` at dae902b.

### Scheme 3.12: x1 seams between blocks (column split, `cubed` layout pz>1)
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
  WB4 switch needs nghost≥3 (`src/hydro/hydro.cpp:96-103@dae902b`).
- Derivations:
  - Telescoping conservation of the averaged seam flux: re-derive from `src/hydro/hydro_forward.cpp:434-447@dae902b`
    (comment only).
  - Reference relay (running face value + interior drop): re-derive from `src/hydro/hydro.cpp:490-513@dae902b`
    (comment only); the WB scheme itself is owned by the WB chapter (exists: docs/derivations/wb-ref4.md §7 for the
    seam flag).
- Figures:
  - A column split into 2-4 blocks: the anchor relay arrows top→bottom; ghost rows of pref/dref copied from the
    neighbour interior.
  - The seam face with the two one-sided fluxes and their average (process seam) vs the identical states (in-process).
- Code: `src/hydro/hydro.cpp:242@dae902b` `x1_neighbors`; `:251` `_x1_ghost_rows`; `:484` `_hydro_ref_x1` (`:506`
  `x1_split`, `:512` take anchor, `:559` pass anchor, `:574` ghost-row exchange); `src/hydro/hydro_forward.cpp:242-271@dae902b`
  (physical-face gating), `:293` and `:515` (`_x1_ghost_rows` tags 0x7724/0x7722), `:448-505` (seam average, tags
  0x7720/0x7721); `src/layout/layout.cpp:879@dae902b` `take_x1_anchor`, `:907` `pass_x1_anchor`, `:777`
  `gather_x1`; `src/eos/equation_of_state.cpp:279-282@dae902b` (column gather).
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

### Scheme 3.13: Exchange of conserved vs primitive variables, and the velocity frame at seams
- Summary: the per-stage sync exchanges CONSERVED variables (hydro_u, scalar_s), and the scalar primitive is rebuilt
  afterwards. The init sync exchanges primitives. On the cubed sphere, conserved momenta are covariant (raised before the
  rotation to spherical, lowered after), primitives are contravariant, and scalars are not rotated. Switch:
  `SyncOptions.type`.
- Derivations: covariant/contravariant handling: re-derive from `src/coord/cubed_sphere_utils.cpp:288-296@dae902b`.
- Figures: a table of type → rotation applied.
- Code: `src/mesh/meshblock.cpp:913-983@dae902b`; `src/layout/cubed_sphere_layout.cpp:735-753@dae902b` (serialize
  switch on type).
- Tests: `test_coordinate.release` `DeviceTest.cached_cubed_sphere_velocity_matrices_match_direct`.
- Limits / known issues: none.
- Discrepancies: none.

### Scheme 3.14: x1-wall corner refresh inside tangential ghost slabs (#265)
- Summary: after the tangential exchange, each installed x1 bfunc except outflow is re-applied inside the x2/x3 ghost
  slabs, unless that slab's own tangential face is physical. This keeps wall corners consistent with the updated column.
  It relies on the contract that a face function may be called again on an nghost-wide slab and gives the same ghosts.
  Switch: always on in `MeshBlock::exchange_ghost_zones`.
- Derivations: none (consistency rule). PR #265 records the mechanism (viscous cross-derivatives at the wall row).
- Figures: an x1 wall with the x2 seam: corner cells before (stale reflection) and after the refresh.
- Code: `src/mesh/meshblock.cpp:932-973@dae902b` (`refresh` lambda `:951`, call `:972`); `src/bc/bc_func.hpp` (contract comment).
- Tests: `tests/test_wb_wall_corner.cpp` (`test_wb_wall_corner.release`) — a resting polytrope with viscosity keeps
  max|u2|/c_s ≤ 1e-12 for stock and user walls, a one-block vs two-block x2 split, and scalar corner primitives (CPU and
  CUDA).
- Limits / known issues: `Mesh::exchange_ghost_zones` (`mesh.cpp:389`) does not refresh (PR #265 limits). Only x1
  walls are handled.
- Discrepancies: none.

### Scheme 3.15: Registered but non-functional coordinate type `cylindrical`
- Summary: `cylindrical` is accepted by `CoordinateImpl::create`, but `CylindricalImpl::reset()` is empty and the source
  file is disabled (`cylindrical.cpp_`). No widths, centres or areas are built. Switch: `geometry.type: cylindrical`.
- Derivations: n/a.
- Figures: none.
- Code: `src/coord/coordinate.hpp:363@dae902b` (`reset() {}` at `:374`); `src/coord/coordinate.cpp:601-602@dae902b`.
- Tests: none.
- Limits / known issues: selecting it would run on empty buffers (inferred from code).
- Discrepancies: none.

---

## Chapter 14: Parallelism, GPU, restart/IO and reproducibility

Scope: process launch and communication backends, how exchange messages are matched, several blocks per process,
collectives, GPU execution, NetCDF/PnetCDF output and combining, restart files and resume semantics, and an inventory of
every reproducibility claim with its evidence. Recommendation: split into 14a "Parallel and GPU execution" (S14.1-14.6)
and 14b "Output and restart" (S14.7-14.10). Make S14.11 (reproducibility) a short standalone chapter or appendix,
because its claims draw on Ch3 seams, Ch14 and the physics chapters. Cross-reference Ch3 for what ghost values contain.

### Scheme 14.1: Launch environment and rendezvous
- Summary: one OS process per rank, launched by torchrun or `api/pd-run`. Ranks meet at a c10d TCPStore on
  MASTER_ADDR:MASTER_PORT. MASTER_PORT is required when the world size is >1; a single process picks a random port in
  [29500,29600]. Each process holds bpp blocks. Switch: env `RANK`, `WORLD_SIZE`, `PROCESS_RANK`, `PROCESS_WORLD_SIZE`
  (fall back to RANK/WORLD_SIZE), `LOCAL_RANK`, `MASTER_ADDR` (default 127.0.0.1), `MASTER_PORT`, `DEVICE` (default
  cpu), `DEVICE_ID` (default -1 → LOCAL_RANK), `BACKEND`. `pd-run` defaults BACKEND=ucx, DEVICE=cpu.
- Derivations: none.
- Figures: a launch diagram (torchrun → N processes → TCPStore → process group; each process → bpp blocks → device).
- Code: `src/layout/layout.cpp:34@dae902b` `random_master_port`; `:189` `LayoutOptionsImpl` constructor (`:205`
  MASTER_PORT check); `src/mesh/mesh.cpp:236-247@dae902b` (world_size = process_world_size·bpp, block rank);
  `src/mesh/meshblock_options.cpp:274@dae902b` `device_str` ("cuda:" + device_id or local_rank); `api/pd-run`.
- Tests: `tests/test_process_group.cpp` (`test_process_group.release`) — `LayoutOptions.DefaultsToPlatformCommunicationBackend`,
  `UsesBackendEnvironmentVariable`, `IgnoresYamlBackend`, `BackendEnvironmentOverridesYamlBackend`,
  `RandomizesDefaultMasterPortWhenEnvUnset`, `RequiresMasterPortForMultiProcessWhenEnvUnset`,
  `RequiresMasterPortWhenWorldSizeImpliesMultiProcess`, `UsesProvidedMasterPortForMultiProcess`,
  `ProcessGroupContext.SkipsSingleProcessCommunication`.
- Limits / known issues: `pd-run` exports BLOCKS_PER_PROCESS, but `src/` never reads it; only tests do
  (`tests/test_exchange.cpp`).
- Discrepancies: none.

### Scheme 14.2: Communication backends (Gloo, UCX via commux, external PG; no NCCL)
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
- Code: `src/layout/layout.cpp:41@dae902b` `default_backend`; `src/layout/process_group.hpp:29@dae902b`;
  `src/layout/process_group.cpp:71@dae902b` `create` (cache), `:98` `_init` (`:117` TCPStore, `:129` unsupported
  backend), `:148` `send` (`:155` CPU-only, `:158` one tensor), `:166` `recv`, `:184` `allreduce`, `:212`
  `_init_external`, `:236` `_init_gloo`, `:271` `supports_coalescing`, `:287` no-UCX stub;
  `src/layout/process_group_ucx.cpp:22@dae902b` `_init_ucx`; `src/layout/distributed.cpp:14@dae902b`
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

### Scheme 14.3: Exchange message matching and in-process copies
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
- Derivations: tag non-aliasing: re-derive from `src/layout/layout.hpp:161-170@dae902b` and `layout.hpp:272-278`
  (comment).
- Figures: tag bit layout; the rendezvous state machine for the local exchange.
- Code: `src/layout/layout.hpp:163@dae902b` `make_comm_tag`; `src/layout/layout.cpp:279@dae902b`
  `_prepare_local_exchange`; `:419` `_copy_local_exchange_buffers` (phase filter); `:540` `launch_exchange`; `:548`
  `exchange_remote` (`:576` periodic px==2 order swap, `:622` self-send, `:634` mutex, `:635` coalescing); `:652`
  `exchange_each_var`; `:849` `send_to_block`; `:864` `recv_from_block`; `:924` `post_to_local_block`; `:948`
  `take_from_local_block`; `src/layout/cubed_sphere_layout.cpp:1042@dae902b` (cubed-sphere comm mutex).
- Tests: `test_cubed_sphere_exchange.release` `CommTag.rejects_tags_that_collide_with_the_variable_offset`;
  `test_exchange.release` (buffer reuse: data_ptr unchanged on the second sync; ghost correctness; local and remote seen).
- Limits / known issues: a block-local stepping order (not concurrent) deadlocks until the 5-min timeout
  (PR #259 limits).
- Discrepancies: none.

### Scheme 14.4: Several blocks per process and GPU streams
- Summary: a pool of bpp worker threads, each with its own CUDA stream on GPU. The caller's stream is fenced with events
  both ways. Within a process, blocks exchange by direct copy and the x1 relays go through boards. Switch:
  `distribute: blocks_per_process`.
- Derivations: none.
- Figures: same as S1.6.
- Code: `src/mesh/mesh.cpp:47@dae902b`, `:82`, `:134`; `src/layout/layout.cpp:279-387@dae902b` (CUDA arrival and
  completion events).
- Tests: `test_cubed_sphere_exchange.release` `_cuda` (one stream per block); `tests/test_output_barrier.cpp`
  (`test_output_barrier.release`, 2 ranks × 2 blocks).
- Limits / known issues: PnetCDF requires bpp=1 (`src/output/pnetcdf.cpp:74-79@dae902b`).
- Discrepancies: none.

### Scheme 14.5: Collectives and global decisions
- Summary: all collectives use small CPU tensors. dt is MIN; redo causes are a MAX over 6 flags; signals are MAX;
  the gravity-work fixer is a SUM of 5 doubles (local blocks summed in a fixed order first). Barriers sit at init, around
  output combines and at finalize. Switch: none.
- Derivations: none.
- Figures: one cycle's collective timeline (dt MIN → fixer SUM at the last stage → redo MAX → output barriers).
- Code: `src/mesh/meshblock.cpp:510-528@dae902b` (MIN), `:832-838` (fixer SUM, single block), `:1288` (redo MAX);
  `src/mesh/mesh.cpp:346-355@dae902b` (fixer SUM, multi-block); `src/utils/signal_handler.cpp:64@dae902b`
  `CheckSignalFlags` (MAX).
- Tests: `test_check_redo_parallel.release`; `tests/test_cycle_diagnostics_parallel.cpp`
  (`test_cycle_diagnostics_parallel.release`).
- Limits / known issues: MIN/MAX are order-independent. The fixer SUM's round-off depends on the number of ranks and
  blocks and on the backend's reduction order, so with the fixer on (default with `gravity-work: cell`) results across
  decompositions can differ in the last bits (inference; not measured in sources).
- Discrepancies: none.

### Scheme 14.6: GPU execution
- Summary: a block is built on CPU and moved with `block->to(device)` / `mesh->to(device)`. The device is
  `cuda:<DEVICE_ID or LOCAL_RANK>`. Kernels use the CUDA DispatchStubs (S1.9). Host syncs (`.item()`) come from
  meters, redo flags and the fixer. Switch: CMake `CUDA=ON`; env `DEVICE=cuda`, `DEVICE_ID`.
- Derivations: none.
- Figures: the per-step host↔device sync points (from issue #291's counts).
- Code: `src/mesh/meshblock_options.cpp:274@dae902b`; `examples/run_hydro.cpp:39-47@dae902b`;
  `src/recon/recon_dispatch.cu:18@dae902b` (tiling for lines >1024); `tests/cuda_test_gate.hpp` (a CPU build never
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

### Scheme 14.7: NetCDF output (per-block files, combine)
- Summary: each block writes `<basename>.block<r>.out<fid>.<NNNNN>.nc` (NetCDF-4). Variables are NC_FLOAT by default,
  or NC_DOUBLE with `double_precision: true`. Cubed-sphere panels are laid out on a 3×2 global tile for indexing. After
  the last local block writes, the root process combines all parts with the in-tree `mppnccombine` (a single part is
  renamed). Mirror barriers in a scope guard hold every rank until the combined file exists. Switch: YAML
  `outputs: - {type: netcdf, dt, variables, combine (default true), double_precision (default false),
  include_ghost_zones, x1/x2/x3_slice, output_sumx1..3, cartesian_vector, super-resolution}`; CMake `NETCDF` (default ON).
- Derivations: none.
- Figures: file naming and the combine flow (parts → root mppnccombine → combined file, barrier, barrier).
- Code: `src/output/output_type.cpp:64@dae902b` `OutputOptionsImpl::from_yaml`; `src/output/netcdf.cpp:37@dae902b`
  `write_output_file` (`:127` nc_create, `:166` cubed-sphere tile offsets, `:194` NC_DOUBLE switch);
  `src/output/combine_netcdf.cpp:27@dae902b` `ready_to_combine` (counts local blocks), `:39` `combine_blocks` (`:62`
  barrier, `:70` ReleaseOnExit, `:121` `mppnccombine`); `src/output/mppnccombine.cpp:94@dae902b`;
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

### Scheme 14.8: PnetCDF output
- Summary: one shared file written collectively through pinc/PnetCDF, NC_FLOAT only (double_precision refused at
  construction), bpp must be 1. Switch: YAML `type: pnetcdf`; CMake `PNETCDF` (default ON on Linux, OFF on Apple;
  needs the Python package `pinc`). Without the build flag the type throws ("requires PNETCDF=ON",
  `meshblock.cpp:214`).
- Derivations: none.
- Figures: none.
- Code: `src/output/pnetcdf.cpp:48@dae902b` constructor; `:60` `write_output_file` (`:74-79` bpp check); `cmake/parameters.cmake:28-43@dae902b`.
- Tests: none registered (the refusal was exercised by hand in PR #213, single rank).
- Limits / known issues: multi-rank PnetCDF output is not covered by any ctest.
- Discrepancies: none.

### Scheme 14.9: Restart files (write, bundle, read)
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
- Code: `src/output/restart.cpp:24@dae902b` `write_output_file` (`:47-61` schedule tensors, `:64-81` name, `:90`
  `save_tensors`); `src/output/combine_restart.cpp:18@dae902b` magic, `:35` `make_restart_bundle`, `:76`
  `combine_blocks` (`:95` barrier); `src/input/read_restart_file.cpp:154@dae902b` `load_pt_from_bundle`, `:223`
  `load_restart`; `src/mesh/meshblock.cpp:1306@dae902b` `_init_from_restart` (`:1343` precise keys, `:1379` positional
  file number, `:1388` dt clamp, `:1400` scalar rebuild); `src/output/output_type.cpp:16@dae902b` `schedule_key`,
  `:24` `schedule_key_v2`; `src/hydro/hydro.hpp:183-186@dae902b` (meters not carried).
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

### Scheme 14.10: Output scheduling, statistics and termination
- Summary: each output fires when t ≥ next_time, then next_time += dt and file_number++. With dt=0 it writes every
  cycle. Time-weighted mean/std statistics accumulate between writes. A final write happens at finalize (netcdf skips
  final writes, restart writes `final`). Signals (SIGTERM, SIGINT, SIGALRM wall time) are MAX-reduced and stop the
  run. Switch: output `dt`, `variables` (`*_stat` selection).
- Derivations: time-weighted moments: re-derive from `src/output/output_type.cpp:282-345@dae902b`.
- Figures: a schedule timeline across a restart, showing #272 (next_time clamp) and #277 (rewrite).
- Code: `src/mesh/meshblock.cpp:985@dae902b`; `src/output/output_type.cpp:297@dae902b` `AccumulateStats`;
  `src/utils/signal_handler.cpp:64@dae902b`; `src/mesh/meshblock.cpp:1121@dae902b` `finalize`.
- Tests: `test_user_output.release` `OutputStatistics.primitive_statistics_are_time_weighted_and_reset`,
  `scalar_statistics_...`.
- Limits / known issues: signals are checked only at `check_redo`. A rank that never reaches it hangs
  (`signal_handler.cpp:65-68` comment).
- Discrepancies: none.

### Scheme 14.11: Reproducibility and bit-for-bit claims (inventory)
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

### Scheme 14.12: Combine and inspect tools (post-processing)
- Summary: `pd-combine` / `pd-inspect` Python CLIs combine per-block NetCDF (when `combine: false`) and inspect files.
  Switch: CLI.
- Derivations: none.
- Figures: none.
- Code: `python/api/pd_combine.py`, `python/api/pd_inspect.py`, `pyproject.toml` `[project.scripts]`.
- Tests: used by `run_shallow_splash_decomp.py` (skip if missing).
- Limits / known issues: PR #212 notes `pd-combine` globs every leftover `*.out*.nc` in the working directory, so test
  directories must be clean.
- Discrepancies: none.
