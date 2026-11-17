Lane X: execution (precision, CUDA graphs, mesh, integrator, radiation)
=======================================================================

Owner: Xi Zhang. Round-2 reviewers: Zoey (EF), Isaac (K).
Every ``file:line`` below is at the pins of section 1. "Hypothesis" marks a
claim not yet settled by a test; its gate is named next to it.

1. Scope and pins
-----------------

Pins: snapy ``9e5de2d4``, kintera ``3f5ff938``, pyharp ``6bc01d53``,
pydisort ``9e7f0075``.

Lane files (snapy): ``src/mesh/*`` (3,266 lines) and ``src/interface/*``
(1,008 lines), 4,274 lines in total, counted with::

  git ls-files src/mesh src/interface | grep -E '\.(cpp|hpp|h|c|cu|cuh)$' | xargs cat | wc -l

Provider side: pyharp ``src/integrator`` (564 lines) and pydisort ``src``
(1,590 lines).

Out of scope here: the hydro pipeline (R), exchanges (S), EOS and limiters
(EF), kintera (K), output and restart format (O). This design states what
the executor needs from each of them (section 11).

2. Concepts and current sites
-----------------------------

Lane size moved from 3,989 lines at ``919936da`` to 4,274 at the pin
(``meshblock.cpp`` 1,689 to 1,919; ``mesh.cpp`` 543 to 566; ``.item<``
lines in ``src/mesh`` 23 to 26).

.. csv-table::
   :header: "Concept", "Site at the pin"

   "precision switch", "src/hydro/hydro.hpp:332; option read at src/hydro/hydro_options.cpp:67"
   "precision branches in the lane", "src/mesh/meshblock.cpp:35, src/mesh/meshblock.cpp:41, src/mesh/meshblock.cpp:448, src/mesh/meshblock.cpp:534-538, src/mesh/meshblock.cpp:1798"
   "FP32 storage emulation (env)", "src/utils/fp32_storage.hpp:12-26; applied at src/mesh/meshblock.cpp:621-642"
   "RK backup buffers, FP64 at creation", "src/mesh/meshblock.cpp:306-312"
   "backup retyped on first use", "src/mesh/meshblock.cpp:719-721, src/mesh/meshblock.cpp:741-743"
   "state rebinding per stage", "src/mesh/meshblock.cpp:901-902, src/mesh/meshblock.cpp:921-922"
   "RK combine (allocating)", "pyharp/src/integrator/integrator.cpp:105-126"
   "RK weights, exact sum", "pyharp/src/integrator/integrator.cpp:59-64"
   "stage driver", "src/mesh/meshblock.cpp:698-1007"
   "exchange inside stage 0 (implicit radial diffusion)", "src/mesh/meshblock.cpp:714-718"
   "exchange split pack/launch/unpack", "src/mesh/meshblock.cpp:664-685; callers src/hydro/hydro_forward.cpp:1017, src/scalar/scalar.cpp:120-146"
   "cubed-sphere two-round exchange", "src/mesh/meshblock.cpp:651-658"
   "axial closure (host copy, 2 reads, 1 branch)", "src/mesh/meshblock.cpp:1014-1034"
   "gravity-work fixer (host sums, branch, abort)", "src/mesh/meshblock.cpp:1036-1109"
   "multi-block global phase", "src/mesh/mesh.cpp:350-407"
   "block worker pool and streams", "src/mesh/mesh.cpp:66-227, src/mesh/mesh.cpp:284-297"
   "global dt", "src/mesh/mesh.cpp:325-348; per block src/mesh/meshblock.cpp:576-595"
   "retry decision", "src/mesh/meshblock.cpp:1506-1601; mesh src/mesh/mesh.cpp:465-507"
   "rollback", "src/mesh/meshblock.cpp:1456-1504"
   "graph prototype", "tests/straka_cuda_graph.py:44-90"
   "radiation provider", "pyharp/src/integrator/radiation_model.cpp:27-34, pydisort/src/disort.cpp:439"

3. Target design
----------------

Types (declared in section 12):

- ``PrecisionPolicy``: built once from ``dynamics.precision``; one row per
  quantity (section 6); ``storage()``, ``compute()``, ``cast()``. Replaces
  every ``fp32() ? a : b``.
- ``StateStore``: owns the fixed buffers ``hydro_u``, ``scalar_s``, ``u0``,
  ``s0`` in the storage dtype, allocated once at ``reset()``. Addresses
  change only on ``reset``, ``to()`` and restart, each of which bumps a
  generation counter.
- ``Segment``: an ordered list of device ops with one ``SegmentKind``
  (compute, pack, host-exchange, unpack, global, eager) and a ``capturable``
  flag set by whoever registers the op.
- ``StageSchedule``: the segments of one RK stage, built once per
  configuration.
- ``StageExecutor`` (owned by ``Mesh``): runs a schedule eagerly or by
  replaying one graph per (block, stage, segment); eager is the reference.
- ``GraphKey``: device, shapes/strides/dtypes, StateStore generation,
  configuration generation, stage, precision, dt.
- ``MeshBlock`` keeps its API; its body splits into six parts (item 6 of the
  thread): init, advance, exchange, redo, restart, output.

Ownership: ``Mesh`` owns the executor and the global phase (reductions over
blocks and ranks). Each ``MeshBlock`` owns its ``StateStore`` and contributes
segments. Lanes R, S, EF, K register ops; X schedules them.

Data flow of one step::

  host: dt = min over blocks, ranks           (outside graphs)
  for stage s:
    [pack]  -> host UCX -> [unpack]           exchange = segment boundary
    [compute: hydro fwd (R) | seam exchanges (S) split it]
    [compute: scalar, forcings, RK combine out=hydro_u, limiter, solid]
    [global: device partial sums] -> host allreduce -> [global: apply]
    [boundaries, storage rounding]
  host: one read of the stacked retry flags -> MAX allreduce
        -> accept, or restore u0/s0 + reset registers on all blocks

4. Flux-register contract (executor side)
-----------------------------------------

- Storage: allocated by ``StateStore`` at ``reset()``, fixed address, never
  in restart (derived state). Its dtype is a ``PrecisionPolicy`` row; the
  step accumulator is FP64 (hypothesis; question to R).
- Posts: device ops inside compute segments (R's pipeline stages).
- Begin stage: the executor calls ``begin_stage(stage, weights)`` with
  pyharp's ``IntegratorWeight`` (``pyharp/src/integrator/integrator.hpp:20-29``).
  The weights are host doubles fixed per stage, so a graph keyed by stage
  bakes them in.
- Reads: the register's exchange is an exchange phase (pack, host, unpack);
  it ends the posting segment.
- Corrects: a device op in the segment after the unpack, before the RK
  combine (now ``src/mesh/meshblock.cpp:901``) if corrected per stage, or
  before the last stage's limiter (now ``src/mesh/meshblock.cpp:909``) if
  corrected per step. R chooses; both fit the schedule.
- Reset: at stage 0 and on every rollback, in the same registered reset list
  as the limiter marks (now ``src/mesh/meshblock.cpp:735``).
- Monitor: a device tensor stacked into the step-end retry read
  (``src/mesh/meshblock.cpp:1566``), so no extra host read.
- Ordering: post before pack; unpack before correct; correct before the
  storage rounding (``src/mesh/mesh.cpp:404-405``) and the stage-end
  exchange (``src/mesh/mesh.cpp:406``).
- No added full-field copy: the register holds face data only.

5. Invariants and gates
-----------------------

.. csv-table::
   :header: "Identity", "Test", "Comparison"

   "eager result after X1, X2, X5 equals the pin", "N-step golden of hydro_u and scalar_s, Cartesian and cubed sphere, FP64 and FP32", "bitwise"
   "out= RK combine equals the allocating form", "pyharp test: each scheme and stage, FP32 and FP64, out aliasing u1 and distinct", "bitwise (x86 CPU: NaN payloads may differ)"
   "state addresses fixed", "data_ptr of hydro_u, scalar_s, u0, s0 unchanged over 10 steps with a retry", "exact"
   "no host sync inside a segment", "replay under torch.cuda.set_sync_debug_mode('error')", "exact"
   "graph replay equals eager", "Straka, both precisions, dt changes, a retry", "bitwise (hypothesis); else the tolerance stated by the test"
   "rollback restores the step", "inject a NaN; after retry, state equals the pre-step state, registers zero", "bitwise"
   "dtype per quantity", "policy test: each row of section 6 in both modes", "exact"
   "global corrections unchanged", "closure and fixer on 1 and 4 blocks, 2 ranks", "bitwise if block partials keep their order (hypothesis)"

6. FP32 contract
----------------

.. csv-table::
   :header: "Quantity", "Storage", "Compute", "Why FP64 where FP64"

   "hydro_u (anomaly form)", "FP32", "FP32", ""
   "u0, s0 backups", "= storage", "copy", "bitwise rollback"
   "scalar_s", "FP32", "FP32", ""
   "fluxes, du", "FP32", "FP32", ""
   "reference and geometry masters", "FP64, cached casts", "per use", "anomalies cancel against them"
   "hydro_w totals", "FP64", "FP64", "EOS on totals (src/mesh/meshblock.cpp:448)"
   "gauges, total face pressure", "FP64", "FP64", "cancellation"
   "dt, budget and fixer sums", "FP64 (MPS: FP32)", "FP64", "sums over all cells; MPS has no FP64 (src/mesh/meshblock.cpp:1057)"
   "vertical implicit correction", "FP32", "FP32, FP64 fallback", "fallback on solve failure"
   "kintera totals, saturation", "FP64", "FP64", "phase equilibrium"
   "time, dt, stage weights", "host double", "host double", "rk3 weights sum to 1 exactly (pyharp/src/integrator/integrator.cpp:59-64)"
   "flux register step accumulator", "FP64 (hypothesis)", "FP64", "sum over stages; question to R"

Mechanism: ``PrecisionPolicy`` replaces the 30 ``fp32()`` calls in ``src``
(hydro, EOS and mesh files) with ``policy.cast(Quantity, x)``. The lane's own five
calls go in X1; the others go with their lanes' PRs. ``u0``/``s0`` are
created in the storage dtype, so ``src/mesh/meshblock.cpp:719-720`` and
``src/mesh/meshblock.cpp:741-742`` go.

7. CUDA-graph contract
----------------------

Host reads, allocations and data-dependent branches in a step, lane X files
(other lanes' sites: ``.item<`` lines per directory at the pin are bc 11,
coord 7, eos 5, forcing 14, hydro 11, implicit 7, output 13, recon 2,
utils 7; each owner rules on its own).

.. csv-table::
   :header: "Site", "Kind", "Fate", "Gate"

   "src/mesh/mesh.cpp:344, src/mesh/meshblock.cpp:588", "dt read", "stays: step start, outside segments", "G1"
   "src/mesh/meshblock.cpp:714-718", "exchange in stage 0", "segment boundary", "G1"
   "src/mesh/meshblock.cpp:719-720, src/mesh/meshblock.cpp:741-742", "allocation on dtype change", "removed (policy)", "G1"
   "src/mesh/meshblock.cpp:736", "host drain of kintera failures", "device counter (K)", "G2"
   "src/mesh/meshblock.cpp:874", "user TorchScript forcing", "eager segment unless declared capturable", "G1"
   "src/mesh/meshblock.cpp:901-902, src/mesh/meshblock.cpp:921-922", "allocation + rebinding", "pyharp out= into fixed storage", "G1"
   "src/mesh/meshblock.cpp:950-981", "saturation adjustment", "eager segment until kintera capture", "G2"
   "src/mesh/meshblock.cpp:1017-1018, src/mesh/meshblock.cpp:1023", "host copy, 2 reads, 1 branch", "device sums and mask; allreduce is a boundary", "G1/G4"
   "src/mesh/meshblock.cpp:1061, src/mesh/meshblock.cpp:1075, src/mesh/meshblock.cpp:1080", "copy to host, branch", "device; last stage only", "G1/G4"
   "src/mesh/meshblock.cpp:1097", "abort on bound", "device flag, read with the retry flags; abort at step end", "G1"
   "src/mesh/meshblock.cpp:1517", "full-field clone in the retry test", "question to EF", "G1"
   "src/mesh/meshblock.cpp:1566, src/mesh/meshblock.cpp:1591", "one read, MAX allreduce", "stays: step end", "G1/G4"
   "src/mesh/meshblock.cpp:1288-1295, src/mesh/meshblock.cpp:1319-1337", "diagnostic reads", "stay: output cadence, outside", "G7"
   "src/mesh/meshblock.cpp:1426-1443", "legacy reads", "removed with the helpers", "G1"
   "src/mesh/meshblock.cpp:1628-1712", "restart reads", "stay: not in a step", "-"

Segment list of one RK stage, Cartesian: exchange (pack | host | unpack);
compute split at each within-stage exchange that R and S declare (now
``src/hydro/hydro_forward.cpp:1017``, ``src/hydro/hydro_forward.cpp:1029``,
``src/scalar/scalar.cpp:120-146``); scalar, forcings, RK combine, limiter,
solid fill; last stage: saturation adjustment (eager until G2); global phase
(closure each stage, fixer last stage); boundaries and storage rounding.
Cubed sphere adds the second exchange round (``src/mesh/meshblock.cpp:651-658``)
and S's corner fill as further boundaries.

dt: recapture on a changed dt first, as ``V3_ROADMAP.md:124-129`` asks;
parameterize later, once every op reads dt from one device scalar (now a host
double, ``src/mesh/meshblock.cpp:773``).

Invalidation: any change in ``GraphKey``. Capture restores state, registers,
counters and retry bookkeeping, as the prototype does
(``tests/straka_cuda_graph.py:53-56``). With fixed storage the per-replay input
copy (``tests/straka_cuda_graph.py:86-88``) never fires and goes.

8. Cross-repository interface changes and merge order
-----------------------------------------------------

- pyharp: ``forward(int stage, Tensor u0, Tensor u1, Tensor u2, Tensor out = {})``
  (now ``pyharp/src/integrator/integrator.hpp:95-96``). Empty ``out`` keeps
  the allocating result. Rules: ``out`` may alias ``u1``, never ``u0`` or
  ``u2``; all four share dtype and device, else it throws. Order:
  ``out = u1`` (copy if not aliased); ``out *= w1``; ``out += w0*u0``;
  ``out += w2*u2``. Each step is a separate kernel, so no fused multiply-add;
  addition commutes (not ``add_(x, alpha)``, which may fuse), so the result
  is bitwise ``(w0*u0 + w1*u1) + w2*u2``
  (now ``pyharp/src/integrator/integrator.cpp:123-124``). The dead
  ``call_average3`` path (``pyharp/src/integrator/integrator.cpp:6``,
  ``pyharp/src/integrator/integrator.cpp:113-122``,
  ``integrator_dispatch.{cpp,cu,hpp}``) is deleted.
- kintera (K): a consume-and-reset failure counter on the device and an
  active-set snapshot/restore (section 11).
- pydisort: no change. Its fast path reads the host
  (``pydisort/src/disort.cpp:439``, ``pydisort/src/disort.cpp:451``), so it
  is not capturable.
- UCX/commux: no change; exchanges stay host-managed.

Merge order (provider first): pyharp out=; kintera (K); snapy X1 to X7
(section 10).

Radiation: snapy calls no radiation on its step path at the pin; its only
pyharp type is ``harp::Integrator`` (``src/mesh/meshblock.cpp:257``). When
added, radiation is an eager FP64 segment on CPU or CUDA whose heating is a
registered source. Unsupported, explicitly: radiation inside a graph, and
FP32 radiation (pyharp keeps FP64 buffers,
``pyharp/src/integrator/radiation_model.cpp:27-34``).

Observation: pyharp's ``from_yaml`` does not read ``max_redo``
(``pyharp/src/integrator/integrator.cpp:20-31``), so the default 5
(``pyharp/src/integrator/integrator.hpp:58``) always holds from a deck.

9. Line budget
--------------

.. csv-table:: snapy lane X
   :header: "File", "Lines now", "Lines after", "Deletions named"

   "src/interface/athena_arrays.hpp", 669, 0, "whole file; needs O to move output off AthenaArray (FOR CHENG)"
   "src/interface/init_from_tensor.hpp", 199, 0, "whole file; built only through src/interface/athena_arrays.hpp:669, goes with it"
   "src/interface/stride_iterator.hpp", 140, 0, "whole file; no built includer"
   "src/mesh/meshblock.cpp", 1919, 1716, "a-g below (-203)"
   "src/mesh/meshblock.hpp", 332, 316, "282-294 legacy helpers; 221-222, 229 defer flags"
   "src/mesh/mesh.cpp", 566, 520, "354-361 single-block path; 363-364; 367-402 into the executor's global phase"
   "src/mesh/mesh.hpp", 81, 81, ""
   "src/mesh/meshblock_options.cpp", 296, 296, ""
   "src/mesh/mesh_functions.cpp", 36, 36, ""
   "src/mesh/mesh_functions.hpp", 20, 20, ""
   "src/mesh/cycle_diagnostics.hpp", 16, 16, ""
   "src/mesh/stage_executor.hpp (new)", 0, 90, ""
   "src/mesh/stage_executor.cpp (new)", 0, 170, ""
   "src/mesh/precision_policy.hpp (new)", 0, 60, ""
   "total", 4274, 3321, "cut 953 (22.3%)"

``meshblock.cpp`` deletions:

a. -57: host timers in the stage driver, 711, 774-781, 808-815, 890-897,
   911-918, 924-931, 939-946, 973-980; the executor times segments.
b. -36: verbose prints in ``reset()``, 188-198, 250-253, 258-261, 265-268,
   272-275, 293-296, 314-318.
c. -18: the six face blocks 161-186 become one loop over three axes.
d. -22: closure and fixer calls 983-1004 move to the global phase.
e. -31: ``initialize`` 397-436 calls ``initialize_under_mesh`` 472-490
   instead of repeating it.
f. -29: legacy helpers 1417-1445 (tests switch to ``local_redo_flags``,
   ``tests/test_forcing.cpp:754``).
g. -10: precision branches 534-538, 719-720, 741-742, 1798-1800 via the
   policy.

.. csv-table:: providers
   :header: "File", "Lines now", "Lines after", "Deletions named"

   "pyharp/src/integrator/integrator.cpp", 136, 130, "6, 113-122 dead path; out= adds 5"
   "pyharp/src/integrator/integrator.hpp", 102, 102, "signature gains out"
   "pyharp/src/integrator/integrator_dispatch.cpp", 43, 0, "dead"
   "pyharp/src/integrator/integrator_dispatch.cu", 30, 0, "dead"
   "pyharp/src/integrator/integrator_dispatch.hpp", 14, 0, "dead"

pydisort: no file touched.

**FOR CHENG** (20% target): 868 of the 953 lines are ``athena_arrays.hpp`` and
the ``init_from_tensor.hpp`` it includes.
Without lane O moving output to tensors, lane X cuts 85 lines (2.0%).

10. Migration
-------------

.. csv-table::
   :header: "PR", "Content", "Against main"

   "P1 pyharp", "forward(..., out); delete dispatch", "bitwise"
   "K", "device failure counter, active-set snapshot", "K's call"
   "X1", "PrecisionPolicy; lane's fp32() branches; u0/s0 in storage dtype", "bitwise"
   "X2", "StateStore; out= replaces set_ at 901-902, 921-922", "bitwise (hypothesis; gate: section 5 golden)"
   "X3", "StageExecutor from tests/straka_cuda_graph.py; deck selection; eager default", "eager bitwise; graph parity"
   "X4", "device closure and fixer; deferred abort; global phase for 1 and N blocks", "bitwise for accepted steps if partial-sum order is kept (hypothesis), else round-off"
   "X5", "meshblock split into six parts; deletions a-f", "bitwise"
   "X6", "delete src/interface (with O)", "bitwise"
   "X7", "capability matrix, docs, benchmarks (G7)", "no numerics"

Removed: host stage timers (replaced by segment timing), the ``defer_*``
flags, the four legacy helpers, the dead pyharp dispatch. No physics option
and no default changes.

Deck (G7; names are Cheng's call, ``V3_ROADMAP.md:301``)::

  integration:
    execution: eager        # eager | cuda-graph
    execution-strict: false # true: reject a case with any eager segment

Capability matrix (numerical support is the eager columns; graph support is
separate):

.. csv-table::
   :header: "Case", "eager FP64", "eager FP32", "graph FP64", "graph FP32"

   "Cartesian dry, 1 block", "yes", "yes", "G1", "G1"
   "Cartesian, N blocks, UCX ranks", "yes", "yes", "G4", "G4"
   "kintera moist", "yes", "M-series", "G2", "G2"
   "vertical implicit correction", "yes", "fallback FP64", "G3", "G3"
   "cubed sphere", "yes", "G5", "G6", "G6"
   "user TorchScript forcing", "yes", "yes", "eager segment", "eager segment"
   "radiation (pyharp/pydisort)", "not on the step path", "no", "no", "no"

11. Open questions to other lanes
---------------------------------

R (Linfeng):

- Register step accumulator dtype: FP64?
- Accept ``begin_stage(stage, IntegratorWeight)`` and a reset hook called on
  rollback?
- Correct per stage or per step (section 4)?
- Can the register monitor join the stacked retry tensor read at
  ``src/mesh/meshblock.cpp:1566``?

S (Jiheng):

- Declare every exchange as pack, host, unpack (today's
  ``begin/launch/finalize``, ``src/mesh/meshblock.cpp:664-685``), including
  the two-round cubed-sphere exchange (``src/mesh/meshblock.cpp:651-658``)
  and the corner fill?
- Who owns the boundary-function refresh ``src/mesh/meshblock.cpp:1135-1196``?

EF (Zoey):

- Limiter marks and vapor failures as device counters reset by the step-reset
  list (``src/mesh/meshblock.cpp:735-738``)?
- Can the retry test avoid the full-field clone at
  ``src/mesh/meshblock.cpp:1517``?

K (Isaac):

- A consume-and-reset device counter to replace the host drain
  (``src/mesh/meshblock.cpp:1544-1546``, ``src/mesh/meshblock.cpp:1453``)?
- An active-set snapshot/restore so a retry repeats the warm start
  (``src/mesh/meshblock.cpp:969-970``)?
- Output buffers for saturation adjustment, to make G2 capturable?

O (Jiachen):

- Move output off ``AthenaArray`` (``src/output/output_type.hpp:99``) so
  ``src/interface`` can go (section 9)?
- Restart (``src/mesh/meshblock.cpp:1603-1833``) and cycle diagnostics
  (``src/mesh/meshblock.cpp:1226-1339``): owned by O or X?
- Retire the FP32 storage emulation (``src/utils/fp32_storage.hpp:12-26``)
  once true FP32 passes?

12. Skeleton index
------------------

``docs/v3/skeleton/X/``, declarations only, in no build:

- ``precision_policy.hpp``: ``Quantity``, ``PrecisionPolicy``.
- ``state_store.hpp``: ``StateStore``.
- ``stage_executor.hpp``: ``SegmentKind``, ``Op``, ``Segment``,
  ``StageSchedule``, ``GraphKey``, ``ExecutionOptions``, ``Capability``,
  ``StageExecutor``.
- ``meshblock_parts.hpp``: the six parts of ``MeshBlock`` and the step-reset
  list.
- ``pyharp_integrator.hpp``: the ``out=`` signature and its alias rules.
