Lane X: execution (precision, CUDA graphs, mesh, integrator, radiation)
=======================================================================

Owner: Xi Zhang. Round-2 reviewers: Zoey (EF), Isaac (K).
Every ``file:line`` below is at the pins of section 1. "Hypothesis" marks a
claim not yet settled by a test; its gate is named next to it.

1. Scope and pins
-----------------

Pins: snapy ``9e5de2d4``, kintera ``3f5ff938``, pyharp ``6bc01d53``,
pydisort ``9e7f0075``.

Lane files, 5,733 lines: snapy ``src/mesh/*`` (3,266) and the precision
code ``src/utils/fp32_storage.hpp``, ``fp32_storage.cpp``, ``fp64_store.hpp``,
``tensor_cast_cache.hpp`` (313); pyharp ``src/integrator`` (564); pydisort
``src`` (1,590). Each directory is counted with::

  git ls-files src/mesh | grep -E '\.(cpp|hpp|h|c|cu|cuh)$' | xargs cat | wc -l

Snapy has no CUDA-graph source at the pin; the prototype is a test,
``tests/straka_cuda_graph.py``.

``src/interface/*`` (1,008 lines) serves output and is O's; section 9 lists it
as joint and does not count it.

Out of scope here: the hydro pipeline (R), exchanges (S), EOS and limiters
(EF), kintera (K), output and restart format (O). This design states what
the executor needs from each of them (section 11).

2. Concepts and current sites
-----------------------------

``src/mesh`` plus ``src/interface`` moved from 3,989 lines at ``919936da`` to 4,274 at the pin
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
  ``integrator_dispatch.{cpp,cu,hpp}``) is deleted. The binding
  (``pyharp/python/csrc/pyintegrator.cpp:51-52``) gains
  ``py::arg("out") = torch::Tensor()``.
- kintera (K): a consume-and-reset failure counter on the device and an
  active-set snapshot/restore (section 11).
- pydisort: no interface change; section 9 items D1 and D2 rewrite two flag
  functions as tables. Its fast path reads the host
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

Counted: everything lane X owns at the pins (section 1, 5,733 lines). New
files count as added lines. Joint rows (the other lane's call) are listed
apart and not counted.

.. csv-table:: lane X
   :header: "File", "Lines now", "Lines after", "Deletions named"

   "src/mesh/meshblock.cpp", 1919, 1508, "items below (-411)"
   "src/mesh/meshblock.hpp", 332, 266, "items below (-66)"
   "src/mesh/mesh.cpp", 566, 355, "items below (-211)"
   "src/mesh/mesh.hpp", 81, 75, "items below (-6)"
   "src/mesh/meshblock_options.cpp", 296, 190, "items below (-106)"
   "src/mesh/mesh_functions.cpp", 36, 31, "items below (-5)"
   "src/mesh/mesh_functions.hpp", 20, 17, "items below (-3)"
   "src/mesh/cycle_diagnostics.hpp", 16, 16, "joint with O, below"
   "src/mesh/stage_executor.hpp (new)", 0, 70, "segments, schedule, graph cache"
   "src/mesh/stage_executor.cpp (new)", 0, 150, "eager run, capture, replay, global phase"
   "src/mesh/precision_policy.hpp (new)", 0, 40, "storage, compute and cast dtypes"
   "src/utils/fp32_storage.hpp", 56, 56, "kept; see the note below"
   "src/utils/fp32_storage.cpp", 119, 119, "kept; see the note below"
   "src/utils/fp64_store.hpp", 85, 85, "kept: FP64 reference buffers"
   "src/utils/tensor_cast_cache.hpp", 53, 53, "kept: the policy's cached casts"
   "pyharp/src/integrator/integrator.cpp", 136, 94, "items below (-42)"
   "pyharp/src/integrator/integrator.hpp", 102, 94, "items below (-8); out= fits line 96"
   "pyharp/src/integrator/integrator_dispatch.cpp", 43, 0, "items below (-43)"
   "pyharp/src/integrator/integrator_dispatch.cu", 30, 0, "items below (-30)"
   "pyharp/src/integrator/integrator_dispatch.hpp", 14, 0, "items below (-14)"
   "pyharp/src/integrator/integrator_formatter.hpp", 37, 37, "kept; see the note below"
   "pyharp/src/integrator/radiation_model.cpp", 114, 114, "kept; see the note below"
   "pyharp/src/integrator/radiation_model.hpp", 88, 88, "kept; see the note below"
   "pydisort/src/disort.cpp", 614, 546, "items below (-68)"
   "pydisort/src/add_arg.h", 28, 28, "untouched"
   "pydisort/src/disort.hpp", 284, 284, "untouched"
   "pydisort/src/disort_dispatch.cpp", 56, 56, "untouched"
   "pydisort/src/disort_dispatch.cu", 146, 146, "untouched"
   "pydisort/src/disort_dispatch.hpp", 18, 18, "untouched"
   "pydisort/src/disort_formatter.hpp", 54, 54, "untouched"
   "pydisort/src/disort_impl.h", 133, 133, "untouched"
   "pydisort/src/index.h", 16, 16, "untouched"
   "pydisort/src/loops.cuh", 116, 116, "untouched"
   "pydisort/src/scattering_moments.cpp", 50, 50, "untouched"
   "pydisort/src/scattering_moments.hpp", 28, 28, "untouched"
   "pydisort/src/vectorize.cpp", 22, 22, "untouched"
   "pydisort/src/vectorize.hpp", 25, 25, "untouched"
   "total", 5733, 4980, "cut 753 (13.1%)"

Items. Each line: net lines, file, ranges at the pin, the replacement.
Gross and added counts are by hand; the bitwise gate is section 5's golden
run on 1 and N blocks, before and after each PR.

a. -59 (meshblock.cpp): host stage timers 711, 774-781, 808-815, 889-898,
   911-918, 924-931, 939-946, 973-980; the executor times segments.
b. -36 (meshblock.cpp): verbose prints in ``reset()`` 188-198, 250-253,
   258-261, 265-268, 272-275, 293-296, 314-318.
c. -18 (meshblock.cpp): six face blocks 161-186 become one loop (+8).
d. -22 (meshblock.cpp): closure and fixer calls 983-1004 go to the global
   phase (hypothesis: bitwise for 1 block only if 1846-1919 is idempotent).
e. -24 (meshblock.cpp): ``initialize`` 412-433 repeats
   ``initialize_under_mesh`` 472-490 and calls it instead; 398-400 is a
   commented-out barrier; the verbose print 415-417 goes (+1).
f. -29 (meshblock.cpp): legacy helpers 1417-1445; the test at
   ``tests/test_forcing.cpp:754`` reads the limiter marks directly.
g. -10 (meshblock.cpp): precision branches 534-538, 719-720, 741-742,
   1798-1800 via the policy (+2).
k. -27 (meshblock.cpp): ``part()`` 337-377, three copied dimension blocks
   become one loop (+14).
l1. -11 (meshblock.cpp): ``max_time_step`` 576-595 calls one global-dt
    helper (MIN allreduce, cfl times 2^-redo) (+9).
l2. -10 (mesh.cpp): ``max_time_step`` 335-347 calls the same helper (+3).
m1. -19 (meshblock.cpp): one retry decision for 1 and N blocks, 1565-1601:
    stack flags, amax, one host read, MAX allreduce (+18).
m2. -13 (mesh.cpp): 476-492 use it (+4).
m3. -7 (meshblock.hpp): 272-280 (+2).
n1. -36 (meshblock.cpp): ``finalize`` 1349-1371, 1399-1414 calls the
    N-block body of ``Mesh::finalize`` (+3).
n2. -3 (mesh.cpp): 519-521, folded into that body.
n3. -27 (meshblock.cpp): ``clock()`` summary 1373-1397, 569, 1658-1660 and
    ``<ctime>`` at 4; executor wall timing replaces it (+3).
n4. -3 (meshblock.hpp): 317-319.
o1. -20 (meshblock.cpp): verbose prints 504-507, 520-522, 542-544, 571-573,
    1202-1204, 1220-1223.
o2. -3 (meshblock_options.cpp): verbose print 27-29.
p. -7 (meshblock.cpp): one fixer-mass helper for 1038-1045 and 1066-1072
   (+8).
q. -5 (meshblock.cpp): one ``thermo()`` lookup for 964-965, 1449-1452,
   1540-1543 (+5).
r. -6 (meshblock.cpp): both ``to()`` overrides 33-42 read the policy (+4).
s1. -4 (meshblock.cpp): commented-out code 242-244, unused ``peos`` 302.
s2. -5 (mesh_functions.cpp): ``UniformMesh`` 8-10 (no caller), comments
    30-31.
s3. -3 (mesh_functions.hpp): its declaration 10-12.
t. -7 (meshblock.cpp): ``bfuncs`` size checks 96-106 become a loop (+4).
u. -14 (meshblock.cpp): one state-exchange helper for 475-487 and 1116-1128
   (+12).
w. -15 (meshblock.cpp): ``apply_extra_forcing`` 819-849 loops over the two
   keys; error texts kept (+16).
y1. -7 (meshblock.cpp): ``round_storage_after_stage`` 636-642 becomes the
    executor's rounding segment.
y2. -2 (meshblock.hpp): 214-215.
aa1. -3 (meshblock.cpp): 1009-1012; the global phase reads the hydro sums
     directly (+1).
aa2. -1 (meshblock.hpp): 226.
bb. -5 (meshblock.cpp): the lock 9, 31, 134-135, 137; blocks are built one
    after another (``src/mesh/mesh.cpp:259-272``; hypothesis).
hp. -16 (meshblock.hpp): defer flags 221-222, 229; legacy helpers 282-294.
x. -37 (meshblock.hpp): ``\param`` blocks restating signatures, 162-167,
   171-175, 186-190, 194-199, 244-249, 253-258, 265-269, 304-309 (+8).
M. -46 (mesh.cpp): 354-361, 363-364, 367-402 into the global phase.
h1. -126 (mesh.cpp): ``BlockWorkerPool`` 6-8, 13-14, 66-227; per-block jobs
    on ATen's inter-op pool with executor-owned streams (+41; hypothesis,
    gate: CPU multi-block wall time within 5%, no nested-launch deadlock).
h2. -6 (mesh.hpp): 69-74.
v. -4 (mesh.cpp): redundant single-block branch 423-426.
z. -9 (mesh.cpp): ``check_same_variables`` 47-62 as one key-set comparison
   (+7).
i. -81 (meshblock_options.cpp): six face-parsing blocks 104-212 become one
   loop; keeps x1 periodic for "cubed" only and the null padding (+28).
j. -22 (meshblock_options.cpp): slice checks 65-86 repeat the bounds and
   order checks in ``reset()`` 203-230; a bad slice now fails at construction.
I1. -6 (pyharp/src/integrator/integrator.cpp): the dead ``call_average3``
    include 6 and comment 113-122; the ``out=`` path of section 8 adds 5.
I2. -43 (pyharp/src/integrator/integrator_dispatch.cpp): dead; its only
    caller is the comment at ``pyharp/src/integrator/integrator.cpp:121``.
I3. -30 (pyharp/src/integrator/integrator_dispatch.cu): dead.
I4. -14 (pyharp/src/integrator/integrator_dispatch.hpp): dead. The build
    globs ``integrator/*.cpp`` and ``*.cu`` (``pyharp/src/CMakeLists.txt:38``,
    ``pyharp/src/CMakeLists.txt:67``), so no build edit.
I5. -29 (pyharp/src/integrator/integrator.cpp): the weight chain 35-87
    becomes one static table from type to {w0, w1, w2} per stage, with
    "euler" an alias of rk1, the same error text and one comment on the
    exact ``1. - 2./3.`` (+21, and +3 includes); the same constants.
I6. -7 (pyharp/src/integrator/integrator.cpp): ``stop()`` 93-103 as one
    boolean return (+4).
I7. -8 (pyharp/src/integrator/integrator.hpp): the ``\param`` block 66-74
    restating the signature (+1).
D1. -51 (pydisort/src/disort.cpp): ``print_ds_flags`` 544-612, eleven
    if/else pairs, becomes a {label, flag} table and one loop (+18); the
    printed text is byte-identical.
D2. -17 (pydisort/src/disort.cpp): ``set_flags`` 49-93 becomes a map from
    token to ``int*`` into ``ds().flag`` (``prnt[0..4]`` kept) and one loop
    (+28); the same 17 tokens and the same error text.

Added counts for I5, D1 and D2 come from clang-format (Google style) on a
draft. Without h1-h2 the cut is 621 (10.8%). If O's options schema replaces
``from_yaml``, i and j are O's: with h1-h2 kept, then 650 (11.3%).
If Cheng drops the FP32 storage emulation, the cut is 753 + 202 = 955
(16.7%): ``fp32_storage.*`` (175), ``src/mesh/meshblock.cpp:22``,
``src/mesh/meshblock.cpp:618`` and ``src/mesh/meshblock.cpp:620-634`` (17),
``src/mesh/meshblock.hpp:207-213`` (7), ``src/mesh/mesh.cpp:403-405`` (3);
nothing replaces it. The other 138
precision lines stay: ``fp64_store.hpp`` (``src/hydro/hydro.hpp:329``) and
``tensor_cast_cache.hpp`` (``src/coord/coordinate.hpp:399``) serve FP32
arithmetic.

.. csv-table:: joint, not counted
   :header: "File", "Lines now", "Lines after", "Owner and request"

   "src/interface/athena_arrays.hpp", 669, 0, "O: output off AthenaArray (section 11)"
   "src/interface/init_from_tensor.hpp", 199, 0, "O: included only at src/interface/athena_arrays.hpp:669"
   "src/interface/stride_iterator.hpp", 140, 0, "O: no built includer"
   "src/mesh/meshblock.cpp", 1919, 1919, "O: restart 1603-1833, diagnostics 1226-1346; S: exchange 644-685, 1135-1196"
   "src/mesh/cycle_diagnostics.hpp", 16, 16, "O: with the diagnostics"

**FOR CHENG**: lane X cuts 13.1%; the remaining 394 lines sit in O's/S's
joint rows: ``src/interface`` (1,008, O), restart 1603-1833 and cycle
diagnostics 1226-1346 in ``meshblock.cpp`` (352, O), exchange 644-685 and
1135-1196 in ``meshblock.cpp`` (104, S).

Not counted, because each removes a capability or a public API:
pyharp ``RadiationModel`` (``radiation_model.*``, 202 lines; no binding,
test, deck or caller found, but a public class); the ``IntegratorWeight``
formatter (``pyharp/src/integrator/integrator_formatter.hpp:12-24``; no user
found); the FP32 storage emulation (``fp32_storage.*``, 175 lines), which
rounds only the stored state, per row and per step or stage, in FP64
arithmetic, which FP32 storage under the policy does not reproduce.

.. csv-table:: touched outside the lane
   :header: "File", "Lines now", "Lines after", "Change"

   "pyharp/python/csrc/pyintegrator.cpp", 57, 57, "py::arg out (+1); include 3 goes (integrator.hpp has it)"

10. Migration
-------------

.. csv-table::
   :header: "PR", "Content", "Against main"

   "P1 pyharp", "forward(..., out); delete dispatch; weight table, stop(), doc (I1-I7)", "bitwise"
   "P2 pydisort", "flag parsing and printing as tables (D1, D2)", "bitwise; same printed text"
   "K", "device failure counter, active-set snapshot", "K's call"
   "X1", "PrecisionPolicy; lane's fp32() branches; u0/s0 in storage dtype", "bitwise"
   "X2", "StateStore; out= replaces set_ at 901-902, 921-922", "bitwise (hypothesis; gate: section 5 golden)"
   "X3", "StageExecutor from tests/straka_cuda_graph.py; deck selection; eager default", "eager bitwise; graph parity"
   "X4", "device closure and fixer; deferred abort; global phase for 1 and N blocks", "bitwise for accepted steps if partial-sum order is kept (hypothesis), else round-off"
   "X5", "meshblock split into six parts; section 9 src/mesh items except d, M, h1-h2", "bitwise (hypothesis; gate: section 5 golden)"
   "X6", "h1-h2: block jobs on the inter-op pool", "bitwise; CPU multi-block wall time within 5%"
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

O (Jiachen), answers to O rev 1 (``7dac5f4a``, section 14, X1-X3):

- X1, yes: the dt choice and the diagnostic reads sit outside captured
  segments (sections 3 and 7); output, flushes and restart writes run in the
  host phase after the global accept, as ``V3_ROADMAP.md:101`` requires.
- X2, not in the first release: dt and the stage weights stay host doubles
  (section 6), dt is chosen at step start, and a changed dt recaptures (section 7, ``V3_ROADMAP.md:124-129``).
  Post-step consumers run after the accept, outside graphs, so no dt is
  baked in. A device dt scalar comes with parameterized graphs; X will share
  that buffer with O's ``observe`` then.
- X3, X's executor: after ``read_restart`` the Mesh calls
  ``StageExecutor::invalidate()`` (skeleton ``stage_executor.hpp``), which
  drops graphs and captured workspaces; restart never serializes them
  (``V3_ROADMAP.md:80``). MeshBlock only loads into the fixed buffers.

Requests to O, and where the two drafts differ:

- Move output off ``AthenaArray`` (``src/output/output_type.hpp:99``) and
  delete ``src/interface``. O rev 1 deletes only ``stride_iterator.hpp``
  (140) and leaves ``athena_arrays.hpp`` (669) and ``init_from_tensor.hpp``
  (199) unlisted.
- Take restart and cycle diagnostics. Ranges differ: X lists
  ``src/mesh/meshblock.cpp:1603-1833`` and ``src/mesh/meshblock.cpp:1226-1346``;
  O lists 1603-1830 and 1226-1339. The extra lines are the end of
  ``_init_from_restart`` (1831-1833) and the ``print_cycle_info`` wrapper
  (1341-1346). ``src/mesh/cycle_diagnostics.hpp`` is in neither of O's
  tables. X asks that restart load into the fixed buffers in the storage
  dtype and that the diagnostics' host reads stay at step end.
- ``src/utils/fp32_storage.*``, ``fp64_store.hpp`` and
  ``tensor_cast_cache.hpp`` (313) are counted in both drafts; X counts them
  as the precision code. O's cut in them (env parsing to option rows,
  ``fp32_storage.cpp`` 119 to 95) and O's move of ``signal_handler.*`` (213)
  into ``src/mesh`` change X's rows; the kickoff decides which lane counts
  them.
- Slice validation has three sites: ``src/output/output_type.cpp:90-98``
  (slice and sum), ``src/mesh/meshblock.cpp:203-230`` (all checks) and
  ``src/mesh/meshblock_options.cpp:65-86`` (bounds and order). O asks the
  owner of ``meshblock.cpp``, which is X, to drop 203-230 once O's generated
  option checks hold them; X will, uncounted until those checks land. Item j
  drops the third now; if the schema replaces ``from_yaml``, j is O's
  (section 9 variant).

C:

- Rev 2 is to specify the register, FP32 and graph contracts: please
  reference X's precision and graph contracts (sections 6 and 7) rather
  than define a second one.

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
