> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# A GPU chemistry kernel that launched and did nothing

pyminichem dispatches CUDA tensors to an OpenACC batch kernel. Three of its Fortran modules mark the module scalars `n_reac` and `n_sp` with `declare create`, which allocates their device copies at load and makes them permanently present; the patch that was meant to populate them uses `enter data copyin`, which on present data transfers nothing. The device copies stayed at zero, every device loop ran zero iterations, and `forward()` on a CUDA tensor returned its input unchanged — correctly shaped, finite, on the right device, and never integrated. Measured on A100 and GH200 with two independently dated builds. Fixed by one directive, `!$acc update device(n_reac, n_sp)`, after which the GPU reproduces the host solver to $8\times 10^{-10}$ wherever the answer is physical and runs at $6.8\times 10^{6}$ cells/s on GH200. The accuracy of the solver it runs is a separate and unresolved matter, treated in §9.

pyminichem commit `d2baf0a` (2026-09-08); upstream `chengcli/pyminichem`. Adopted into both production venvs (x86 and arm) 2026-09-08, both builds naming `pyminichem: d2baf0a`. Reference oracle: `chengcli/mini_chem` at `3372a50`, built pristine · 2026-09-08

**What was wrong.** `patches/05`, `06` and `07` each add `!$acc declare create(kb, R, P0, n_reac, n_sp, re, g_sp)`. `declare create` gives the module scalars a device copy for the life of the program and marks it present. `patches/08` then populates the network data at the end of `read_react_list` with `!$acc enter data copyin(n_reac, n_sp)`. `enter data copyin` is present-or-copyin: on data already present it increments a reference count and moves no bytes. No `update device` exists anywhere in the ten patches. The device copies therefore held their load-time value, zero.

**What that did.** Every loop inside the device routines is bounded by `n_reac` or `n_sp`, and the dummies of `mini_ch_bdf1_cell_openacc` are dimensioned by them. With both zero the right-hand side and the Jacobian are exactly zero, the single implicit-Euler solve returns `Δy = 0`, and the kernel exits cleanly having written nothing. The arrays `re` and `g_sp` were never implicated: the build uses `-gpu=managed`, so they are reached through managed memory. The two plain scalars are the only non-managed data the kernel reads.

**How it presented.** Silently. `cuda_enabled()` returned true, no exception was raised, and the returned tensor was the right shape, on the right device, and finite. Downstream in the runner, `_vmr_to_mmr` renormalises, so the tracer-sum diagnostic `qtol` read 1.0 throughout. A GPU chemistry run was indistinguishable from a healthy one and was pure advection.

**The fix.** One line in `patches/08`: `!$acc update device(n_reac, n_sp)` immediately after the network files are read. After it the device copies read 10 and 12, and the GPU result matches the host solver to $5\times 10^{-10}$–$8\times 10^{-10}$ on every physical cell.

**The fix does not make GPU chemistry usable at the cadence we run it.** The CUDA path can only run `bdf1`, which is one linearised implicit-Euler step with no substepping and no error control. At `dt` = 60 s it returns volume mixing ratios above 1 and then negative above about 1600 K; 37.6 % of a hot-Jupiter-representative batch is unphysical after a single step. That is a solver limitation, measured in §9, and it is untouched by this fix. The ISSI Test 2 protocol asks for a 1500 s chemistry step.

*Updated 2026-09-09.* That limitation is a cadence price, not a wall: §9's “convergence floor” turned out to be an artefact of the harness, and at matched cadence `bdf1` converges cleanly from 1000 to 2200 K. The 2500 K case does not, and remains a genuine failure.

## 1. The dispatch path, and where the device data comes from

pyminichem is a Torch wrapper over the `chengcli/mini_chem` fork, pinned in `cmake/minichem.cmake` at `3372a500f038f83228c9f8f944b3fb6b2dedc572` and built with ten patches applied by `git apply`. `MiniChemImpl::forward` branches on tensor device: CPU tensors go to `forward_host_solver`, which loops cells one at a time under a mutex; CUDA tensors go to `forward_cuda` in `minichem.cu`, which sets the OpenACC device and binds the OpenACC async queue to the current Torch CUDA stream before calling the Fortran batch entry point.

    c10::cuda::CUDAGuard device_guard(temp_cuda.device());
    const auto stream = c10::cuda::getCurrentCUDAStream(temp_cuda.device().index());
    const int async_queue = temp_cuda.device().index() + 1;
    ...
    openacc_set_device_num(temp_cuda.device().index());
    openacc_set_cuda_stream(async_queue, reinterpret_cast<void*>(stream.stream()));
    minichem_c_run_batch_openacc(..., batch_size, nscratch, async_queue);
    openacc_wait(async_queue);

The Fortran side, added by `patches/07` as `mini_ch_bdf1.f90`, is a single gang-parallel loop over cells, each calling a `routine seq` per-cell solver:

    !$acc parallel loop gang deviceptr(T_in, P_in, VMR, Keq_pool, re_f_pool, re_r_pool, scratch_pool) async(async_queue)
    do icell = 1, ncell
      call mini_ch_bdf1_cell_openacc(T_in(icell), P_in(icell), t_end, VMR(1, icell), ...)
    end do

The cell arrays arrive as device pointers, so they need no OpenACC data management. Everything else the kernel reads — the reaction table `re`, the species table `g_sp`, and the two counts `n_reac` and `n_sp` — is module data, and reaching it is the job of the `declare create` in `patches/05`/`06`/`07` plus the `enter data` block that `patches/08` appends to `read_react_list`.

## 2. The symptom

The wrapper's own test asserts the right thing and fails. `test_cuda_solver_behavior` in `tests/test_python_api.py` checks device, shape, in-place pointer identity, finiteness, and then `not torch.allclose(out, vmr_initial)`. Run on a GPU node at T = 1500 K, P = $10^{5}$ Pa, `dt` = 60 s (the venv has no `pytest`, so the test body was transcribed verbatim as `upstream_assert.py`):

| assertion                              | CPU       | CUDA, before the fix |
|----------------------------------------|-----------|----------------------|
| `out.device.type`                      | PASS      | PASS                 |
| `out.shape == (1, 12)`                 | PASS      | PASS                 |
| `out.data_ptr() == vmr.data_ptr()`     | PASS      | PASS                 |
| `torch.isfinite(out).all()`            | PASS      | PASS                 |
| `not torch.allclose(out, vmr_initial)` | PASS      | FAIL                 |
| `max|out − initial|`                   | 2.655e−03 | 0.000e+00            |

Every assertion that describes the *shape* of the result passes; the one assertion that describes its *content* fails. That is the whole character of the defect.

Read per cell over a batch, with a same-binary control run first: two CUDA calls with identical inputs agreed bitwise, and the GPU state was bit-identical to its input at every batch size tried, while the CPU moved by 1.14. The checksum of a $10^{4}$-cell result was exactly 10 000 — every row still summing to one, because every row was still the normalised input.

**A single-cell test at low temperature passes this bug.** At N = 1 the one cell sat at 1000 K, where nothing measurable happens in 60 s on either device, and the GPU–CPU relative difference read $1.2\times 10^{-10}$. The defect is only visible where the chemistry actually moves.

## 3. What it was not

Three explanations were eliminated before the mechanism was sought, because each would have implied a different fix.

**Not a build without device code.** `readelf` on the installed `libpyminichem_release.so` shows `.nv_fatbin`, `__nv_relfatbin` and `__nv_module_id` sections; `nm -D` shows `mini_ch_bdf1_mod_mini_ch_bdf1_batch_openacc_` defined and the `__pgi_uacc_computestart2` / `computedone` / `dataenterstart2` launch symbols undefined-and-needed; `ldd` resolves `libacchost`/`libaccdevice`/`libaccdevaux` against NVHPC 25.5. The object was compiled by nvfortran with OpenACC enabled and linked to its runtime.

**Not a kernel that never launched.** With `NVCOMPILER_ACC_NOTIFY=3`, which logs launches and transfers, the run prints

    launch CUDA kernel  file=.../mini_ch_bdf1.f90 function=mini_ch_bdf1_batch_openacc line=65
                        device=0 threadid=1 queue=1 num_gangs=1 num_workers=1 vector_length=128 grid=1 block=128

and `grid=8` for a 1000-cell batch. The kernel launches, on the right queue, with a gang count that scales with the batch.

**Not a stream or synchronisation error.** The same log, taken across `initialize()`, shows the only host-to-device traffic to be `variable=descriptor bytes=128` three times and `variable=.attach. bytes=8` eight times — array dope vectors and pointer attachments. **No transfer names `n_reac` or `n_sp`.** Nothing was in flight to be missed; the values had never been sent. (The absence of bulk array traffic — the 150 kB `lkf` rate tables never move — separately confirms that `-gpu=managed` is live and that `re` and `g_sp` reach the device by managed memory.)

## 4. The mechanism

`declare create` on a module variable allocates its device copy when the module is loaded and leaves it present for the life of the program. `enter data copyin` is defined as present-or-copyin: if the data is already present the runtime increments a reference count and performs no transfer. The two directives are therefore in direct conflict for these scalars, and the conflict is silent — it is not a diagnosable error, it is the specified behaviour of each directive taken alone.

    ! patches/05, 06, 07 -- three modules, each:
    !$acc declare create(kb, R, P0, n_reac, n_sp, re, g_sp)     ! -> present for the whole run

    ! patches/08, end of read_react_list, after the files are parsed:
    !$acc enter data copyin(n_reac, n_sp)                        ! -> already present: no transfer
    !$acc enter data copyin(re(1:n_reac), g_sp(1:n_sp))          ! -> managed memory: reached anyway

Nothing else in the ten patches contains `update device`, `update self` or any other explicit transfer. The host reads `n_reac` from the reaction file and `n_sp` from the species file, and those values never left the host.

## 5. The reproduction, without Torch

To separate the wrapper from the Fortran, the fork was checked out at the pinned sha, the ten patches applied in order, and a driver written that reads the module scalars back from a device kernel and then runs the same four cells through the host solver and the device batch routine. Compiled with nvfortran 25.5 and the flags the real build uses (`-acc -gpu=ccall,managed`, and `-O0` for `mini_ch_bdf1.f90` as `patches/04` forces).

    probe = -1
    !$acc parallel loop copyout(probe)
    do i = 1, 1
      probe(1) = n_reac
      probe(2) = n_sp
    end do

|  | host `n_reac`, `n_sp` | device `n_reac`, `n_sp` | max\|device − input\| |
|----|----|----|----|
| as patched | 10, 12 | 0, 0 | 0.000e+00 (all four cells) |
| \+ `update device` | 10, 12 | 10, 12 | matches host, see below |

With the directive added the transfer log gains exactly the two missing lines, `variable=n_reac bytes=4` and `variable=n_sp bytes=4`, and the device solver reproduces the host solver on states that had moved by up to 0.52:

| cell | T (K) | max\|host − input\| | max\|device − input\| | max relative difference |
|------|-------|---------------------|-----------------------|-------------------------|
| 1    | 1500  | 2.655e−03           | 2.655e−03             | 4.710e−11               |
| 2    | 1600  | 2.150e−02           | 2.150e−02             | 4.181e−10               |
| 3    | 1700  | 1.290e−01           | 1.290e−01             | 4.433e−09               |
| 4    | 1800  | 5.229e−01           | 5.229e−01             | 1.944e−08               |

## 6. The fix

         !$acc enter data copyin(n_reac, n_sp)
    +    !$acc update device(n_reac, n_sp)
         !$acc enter data copyin(re(1:n_reac), g_sp(1:n_sp))

One line, in `patches/08.minichem_openacc_data.patch`. The regenerated patch was verified by applying all ten patches to a clean checkout of the fork at the pinned sha. An alternative — dropping `n_reac` and `n_sp` from the `declare create` lists so that `enter data copyin` becomes a real transfer — would touch three files instead of one and would change the lifetime of the device copies; it was not taken.

## 7. What the fix changes

Both architectures, built from the same tree, tested with the assertion above and with a per-cell comparison over a batch of $10^{4}$ cells spanning 1000–2000 K and 10–$10^{7}$ Pa at `dt` = 60 s.

|  | x86 / A100-SXM4-80GB | aarch64 / GH200 480GB |
|----|----|----|
| build | `0.3.5.dev1+gd2baf0a0e` | `0.3.5.dev1+gd29d605b8` |
| torch | 2.10.0+cu128 | 2.10.0+cu126 |
| CUDA key assertion | PASS, 2.655e−03 | PASS, 2.655e−03 |
| GPU vs GPU, same inputs | 0.000e+00 | 0.000e+00 |
| GPU vs CPU, physical cells | 8.188e−10 | 4.941e−10 |
|  of which above 1e−8 | 0 cells | 0 cells |
| GPU vs CPU, unphysical cells | 9.631e−04 | 6.136e−04 |
| cells physical / unphysical | 6238 / 3762 | 6238 / 3762 |

The aggregate GPU–CPU difference over the whole batch is $10^{-4}$–$10^{-3}$, and it would be wrong to read that as a residual porting defect. It is contributed entirely by the cells that `bdf1` had already driven unphysical — the worst sit at 1920–1944 K with a maximum mixing ratio of 1.12 and a species sum of 1.56 — where the single linearised solve is ill-conditioned and amplifies the difference in rounding between two architectures on an answer that is already meaningless. Restricted to cells whose result is physical, the two devices agree to under $10^{-9}$, in agreement with the Torch-free reproduction of §5.

## 8. Cost

Per `forward()` call at `dt` = 60 s, measured on kernels that now do the work. The CPU host path loops cells sequentially under a mutex, so a CPU column is the per-rank chemistry cost, not a per-node one.

| batch          | A100, bdf1                 | GH200, bdf1                |
|----------------|----------------------------|----------------------------|
| 1              | 733 µs                     | 623 µs                     |
| 100            | 1.63 ms                    | 1.21 ms                    |
| 10 000         | 2.55 ms                    | 1.65 ms                    |
| 100 000        | 40.1 ms                    | 15.1 ms                    |
| 1 000 000      | 363 ms                     | 147 ms                     |
| **throughput** | $2.8\times 10^{6}$ cells/s | $6.8\times 10^{6}$ cells/s |

| one CPU core | bdf1 | dlsode |
|----|----|----|
| x86 Milan | 36.4 µs/cell  ($2.7\times 10^{4}$ cells/s) | 2784 µs/cell  (359 cells/s) |
| Grace | 25.2 µs/cell  ($4.0\times 10^{4}$ cells/s) | 2240 µs/cell  (447 cells/s) |

A GH200 runs `bdf1` about 170× one Grace core, and about 15 000× that core running `dlsode`. Below roughly $10^{4}$ cells the GPU is launch-bound at 0.6–0.7 ms per call. At $6.8\times 10^{6}$ cells/s and order $2\times 10^{4}$ flop per cell the kernel is running near $1.4\times 10^{11}$ flop/s in double precision, a few per cent of the hardware — unsurprising for a kernel compiled at `-O0` by `patches/04` and structured as one long sequential routine per cell. There is headroom; realising it was not attempted.

`dlsode` raises `RuntimeError: The dlsode solver is not available for CUDA tensors` at every batch size. That is by design in `minichem_c_run_batch_openacc`, which rejects any solver but `bdf1`, and it was confirmed on hardware rather than read from the source.

## 9. What the fix does not fix

The GPU can only run `bdf1`, and `bdf1` is one linearised implicit-Euler step: one right-hand side, one finite-difference Jacobian, one linear solve, over the whole `t_end`. There is no Newton iteration, no substepping, no error control and no adaptivity, so `t_end` is the step size and the caller owns the substepping. This is a different accuracy class from `dlsode`, which is adaptive.

Against the unpatched fork's own `dlsode` driver, over an 8×4 grid in (T, P) at `dt` = 60 s, judged per point against the reference's own tolerance spread at that point:

| regime | pyminichem dlsode vs reference | bdf1 vs reference |
|----|----|----|
| ≤ 1000 K | at or below the reference's own spread | at or below it |
| 1300–1600 K | below it | 1.0 — a different answer |
| 1900–2200 K | below it | 2.6 to $8.8\times 10^{3}$ |
| 2500 K | 3–4× it | $10^{8}$ to $6\times 10^{18}$ |

At 2200 K and 1 bar the first `bdf1` step returns a hydrogen volume mixing ratio of 1.96; the second goes negative; the run ends spanning ±$6\times 10^{4}$. The reference at the same point holds $\mathrm{H_2}$ at 0.9973 and reaches equilibrium by the third step. Over a batch spanning 1000–2000 K, **37.6 % of cells are unphysical after one 60 s step**.

**Corrected 2026-09-09.** The convergence table that stood here, and the “floor” read off it, were an artefact of the harness that produced them. That harness integrated 600 s in *one* reference call while the arm under test took *n* substeps, and the protocol renormalises `sum(VMR)` to one before every solver call on a chemistry that does not conserve mole number — $\mathrm{CH_4 + H_2O \leftrightarrow CO + 3\,H_2}$ is two particles against four. The two cadences therefore integrate different problems, by an amount that does not shrink with the step. The retracted table and the corrected one are both below.

Reducing the step reveals two distinct behaviours. Integrating a fixed 600 s with increasing substeps, against adaptive `dlsode` over the same interval — **as measured on 2026-09-08, and retracted:**

| T (K) | dt=60 | 6 | 0.6 | 0.06 | 0.006 | reference vs ITSELF at the same cadence |
|----|----|----|----|----|----|----|
| 1000 | 1.9e−1 | 2.2e−2 | 2.3e−3 | 2.8e−4 | 7.2e−5 | 2.0e−6 |
| 1600 | 1.4e−1 | 1.9e−3 | 7.9e−4 | 6.7e−4 | 6.6e−4 | 2.3e−4 |
| 1900 | 1.0 | 1.8e−2 | 4.5e−3 | 4.8e−3 | 4.8e−3 | 4.6e−3 |
| 2200 | 1.0 | 7.8e−1 | 8.9e−3 | 1.2e−2 | 1.2e−2 | 1.24e−2 |
| 2500 | 1.0 (6 neg) | 2.2e−1 | 1.0 (3 neg) | 1.1 (2 neg) | 1.1 (2 neg) | 2.2e−1 |

The last column is the control that was missing: the *reference* put through the same substepped ladder and scored against itself in one call, same binary, same tolerance. It reproduces the plateau at every temperature above 1600 K, to three digits and species by species. The offset appears in full at ten substeps and does not change over four further decades, so it was never a discretisation error. Its size is the volume-mixing-ratio sum drift of the single reference call, to four digits: after 600 s at 1900 K that sum stands at 1.001697, and the near-uniform major-species offset is $1.695\times 10^{-3}$.

Scored at matched cadence — the reference taking the same *n* substeps — `bdf1` converges. Beside it, for scale, is the reference's own error at that cadence, which is the shipped `rtol` = $10^{-3}$ against $10^{-8}$:

| T (K) | dt=600 | 60 | 6 | 0.6 | 0.06 | 0.006 | reference's own error at dt=0.006 |
|----|----|----|----|----|----|----|----|
| 1000 | 7.0e−1 | 1.9e−1 | 2.2e−2 | 2.3e−3 | 2.2e−4 | 2.1e−5 | 7.7e−5 |
| 1600 | 1.0 | 1.4e−1 | 1.3e−3 | 1.2e−4 | 1.4e−6 | 1.0e−7 | 7.4e−4 |
| 1900 | 1.0 | 1.0 | 1.6e−2 | 2.4e−3 | 1.6e−4 | 8.2e−6 | 1.0e−2 |
| 2200 | 1.0 | 1.0 | 7.8e−1 | 8.7e−3 | 2.8e−4 | 3.6e−5 | 2.9e−3 |
| 2500 | 1.6 (2 neg) | 1.0 (6 neg) | 2.3e−3 | 1.0 (3 neg) | 1.07 (2 neg) | 1.07 (2 neg) | 1.7e−3 |

From 1000 to 2200 K the convergence is clean over five to six decades, and below a substep of about 0.06 s `bdf1` is *more accurate than the shipped-tolerance `dlsode`* driven at the same cadence — at 1900 K, $8\times 10^{-6}$ against $10^{-2}$. The plateau is gone; `bdf1` is a consistent first-order method being given steps two orders of magnitude too large, and nothing more. The finite-difference Jacobian epsilon named earlier as the suspect was never the cause and does not need varying.

This is not two codes agreeing because both have parked on a shared equilibrium: over the last half of the 600 s window the reference state still moves by 46 %, 49 %, 67 % and 22 % at 1000, 1600, 1900 and 2200 K. These are transients.

**The 2500 K, 1000 Pa failure is real and survives every control.** It returns negative abundances at 10, $10^{3}$, $10^{4}$ and $10^{5}$ substeps though not at $10^{2}$, its error sits near unity and moves non-monotonically with the step, and the reference at the identical cadence is flat and stable at $1.7\times 10^{-3}$. That is an instability, not a discretisation error. It is also the one case where the reference reaches its fixed point inside the first substep, so `bdf1` is failing on a stiff jump straight to equilibrium rather than on a hard transient.

The cost consequence is therefore a price, not a wall: the roughly 50× per-call advantage `bdf1` holds over `dlsode` on a CPU core is spent on substepping, and the substep count needed at each temperature can now be read off the table above rather than guessed at. One caution for whoever spends it — substepping the shipped `dlsode` does not buy accuracy either. Its own error at 1900 K grows from $3.9\times 10^{-4}$ at one call to $2.3\times 10^{-2}$ at a hundred, and is still $10^{-2}$ at a hundred thousand. Anything that substeps chemistry has to revisit `rtol`, not only the cadence. On the GPU the throughput of §8 buys a great many substeps, which is the reason the question is worth reopening rather than closed.

## 10. Why nothing caught it

The test exists and is correct. `test_cuda_solver_behavior` skips itself when `torch.cuda.is_available()` is false, which is the case on every build node, so it has evidently never executed on hardware that could fail it. The production venv has no `pytest` installed, so it could not have been run there either without first adding one.

Downstream, the runner's `advance_minichem` converts volume to mass mixing ratios through `_vmr_to_mmr`, which normalises by its own sum, and then writes `rho × mmr` into the conserved scalar. The tracer-total diagnostic `qtol` is the sum of those mass fractions and is therefore identically one after every chemistry call, whatever the chemistry did or did not do. It is not a leak detector and could not have flagged this.

## 11. A second defect, found on the way: the patch cache

The first fixed build failed its gate. The build was provably the one loaded and CUDA was still a no-op, while the standalone Fortran with the same edit passed. The cause is in `cmake/macros/macro_add_package.cmake`: after fetching and patching the fork it writes `.cache/minichem_openacc-<tag>.tar.gz`, keyed on name and tag only, and every later configure reports `Using cached library` and `No patch step` and untars the old source. `rm -rf build` does not touch `.cache/`. **Every edit to `patches/` since 2026-06-15 had been silently ignored by every pyminichem build on both architectures.** The compiled `mini_ch_read_reac_list.f90` under `build/_deps/` was dated 2026-06-15 and contained no `update device`.

Working rule, applied to both builds here: after editing anything in `patches/`, move the cache tarball aside — it is kept under `.cache/_stale_<date>/`, not deleted — and assert the populated source contains the change before compiling.

    grep -q "update device(n_reac, n_sp)" \
      build/_deps/minichem_openacc-src/src_mini_chem_dlsode/mini_ch_read_reac_list.f90 || exit 1

## 12. Provenance and adoption

Both venvs carried one-off builds, x86 dated 2026-07-13 and arm 2026-06-15. The recipe was recovered from `setup.py`, the root `CMakeLists.txt` and `logs/rebuild_inplace.log`:

    # (site NVHPC build environment loaded first)
    export PATH=$NVHPC_COMPILERS/bin:$PATH
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCUDA=ON -DBUILD_TESTS=OFF \
          -DCUDAToolkit_ROOT=$NVHPC_CUDA -DCMAKE_CUDA_COMPILER=$NVHPC_CUDA/bin/nvcc
    cmake --build build -j 8
    python -m pip install --no-cache-dir --no-deps --no-build-isolation --force-reinstall .

Built on login front ends, not on GPU nodes, so the libraries do not acquire a `libcusolver` dependency that would prevent import on a front end. Adopted into both production venvs on 2026-09-08, without the example-deck suite, on the grounds that the validation gates of this report are the stronger test of this change.

## 13. Facts recorded on the way

- **The work was briefly on two branches, and is now on one.** The aarch64 commit `d29d605` was a cherry-pick of `d2baf0a`: identical tree, same parent, differing only in commit metadata. The arm clone was then moved onto `d2baf0a` and `d29d605` deleted; the four uncommitted build files survived the switch byte-for-byte, as the trees are identical. The arm venv's wheel is still stamped `0.3.5.dev1+gd29d605b8` because it was built before the converge — same tree, so the binary is the right one, and the sha in the stamp is the identity, exactly as with the snapy and kintera `scm_pretend` version strings.
- **The aarch64 clone carries four uncommitted build adaptations** from June, left as found: the CUDA architecture list narrowed to 90, the x86 vector definitions replaced by `SVE256`, and — in both `patches/04` and `src/CMakeLists.txt` — the OpenACC target changed from `-gpu=ccall,managed` to `-gpu=cc70,cc80,managed`. That last emits no `sm_90` device code for a `cc90` machine; the kernel evidently reaches the GPU through PTX JIT, since it launches and produces correct results at 2.5× the A100 throughput. Correcting it to `cc90` is a separate change and was not made.
- **nvfortran 25.5 deprecates `-gpu=managed`** in favour of `-gpu=mem:managed`, warning on every compile. Still honoured; it will need attention before an SDK bump.
- **The 200 K guard has a source.** The runner skips cells at or below 200 K, and `mini_ch_bdf1_cell_openacc` clamps with `reverse_reactions_bdf1(max(T_in, 200.0_dp), ...)`. Both descend from an uncommitted 2024 local edit, `call reverse_reactions(max(T_in, 200.0_dp))`. `reverse_reactions` evaluates the thermodynamic polynomials, whose low-temperature fit begins at 200 K, so the guard prevents extrapolation outside the fit rather than being an arbitrary cut. Whether clamping or extending the fit is right for brown-dwarf work is open.
- **The reference oracle.** `chengcli/mini_chem` at the pinned sha, built pristine with the fork's own GNU release flags, is bit-identical across repeated runs and was used as the comparison in §9. Its shipped `dlsode` tolerance is `rtol` $= 10^{-3}$, which is loose: its own spread reaches $9\times 10^{-3}$ on $\mathrm{NH_3}$, $2.7\times 10^{-2}$ on HCN and $1.3\times 10^{-1}$ on $\mathrm{CH_4}$ at 1900 K and 0.01 bar, while major species stay under $5\times 10^{-4}$. No claim about a minor species from this stack should be quoted without that bar.

Source precedence throughout: the source at the pin, then a measurement taken here, then the stamp, then a report. Every number in this document was produced on 2026-09-08 on the builds named in the header, and each traces to a command recorded in the run log. Nothing here is inherited from earlier work.
