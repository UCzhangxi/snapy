Status: follow-up complete. O1 PASS under the requester’s round-off rule; reproduction results below. No repository source changes or pushes were made.

**O1 rule:** every peak Ma below **1e-12** after ten sound crossings counts as PASS; ordering among round-off values is noise. All 20 study trajectories and four main baselines pass. Frozen peaks are **5.898996468e-14, 2.609396873e-15, 3.488318588e-13, 8.980478710e-14** (isothermal, adiabat, inversion, moist). The full D3 report and its generator were updated locally.

**Reproduction base:** main `5eeb9b6761ae484a98b3993aae18314fc58cf862` has **no local_polytrope form** (`git grep` over that commit returns no matches), so it was not run with an unsupported selection. I built the unchanged harness commit **1ffb3c16d8c6e182461876a30734af73320a45a9**, snapy **v2.10.34-5-g1ffb3c1**, using kintera **2.5.13**, Release/NetCDF/CUDA sm_75. This detached checkout excludes D3 commit afa02fa. Inputs are byte-identical copies of the previous runs; 50 m local_polytrope uses GPU 0 and 25 m uses GPU 1, matching the original assignments.

| Form | Grid (m) | Harness result | Time (s) | Cycle | Wall (s) |
|---|---:|---|---:|---:|---:|
| isentrope | 50 | Completed | 900.009 | 7485 | 72.25 |
| local_polytrope | 100 | Completed | 900.049 | 3730 | 37.97 |
| local_polytrope | 50 | ABORT | 819.064 | 7386 | 75.96 |
| local_polytrope | 25 | ABORT | 798.437 | 13724 | 472.45 |
| none | 50 | Completed | 900.018 | 7485 | 70.49 |
| smooth5 | 50 | Completed | 900.115 | 7487 | 70.45 |

**50 m reproduction without D3: YES, identical** — original t=819.064 s, cycle=7386; harness t=819.064 s, cycle=7386. Cause lines, their count, and all sampled dt/mass/energy history lines match exactly. Cell/variable identity cannot be compared because neither log records it.

Verbatim harness abort excerpt:

```text
[MeshBlock] Density/pressure at or within 0.1% of the floor, the VIC dry-gas clamp emptied a cell, the limiter patched one or found a NaN, or the saturation adjustment left a cell unadjusted. Redoing the step with smaller dt (causes: floor).
[MeshBlock] Maximum number of redo attempts exceeded. Terminating.
Terminating abnormally
time=819.064 cycle=7386
tlim=900 nlim=-1
```

**25 m reproduction without D3: YES, identical** — original t=798.437 s, cycle=13724; harness t=798.437 s, cycle=13724. Cause lines, their count, and all sampled dt/mass/energy history lines match exactly. Cell/variable identity cannot be compared because neither log records it.

Verbatim harness abort excerpt:

```text
[MeshBlock] Density/pressure at or within 0.1% of the floor, the VIC dry-gas clamp emptied a cell, the limiter patched one or found a NaN, or the saturation adjustment left a cell unadjusted. Redoing the step with smaller dt (causes: floor).
[MeshBlock] Maximum number of redo attempts exceeded. Terminating.
Terminating abnormally
time=798.437 cycle=13724
tlim=900 nlim=-1
```

## Original abort excerpts

Source run commit: afa02fa3e1165755bebe517a7b0b6a6573a51b6e. No cell indices, coordinates, or individual triggering variable are printed in either log. The cause is the combined density/pressure floor test; it also treats NaN comparisons as failures.

## 50 m

Verbatim excerpts (the identical cause line occurs 21 times):

```text
cycle=5000 redo=0 time=5.87444544328381e+02 dt=1.12399751873185e-01 mass0=1.45950803527245e+08 energy=2.84750339990426e+13
cycle=6000 redo=0 time=6.94875496856046e+02 dt=9.66279330646877e-02 mass0=1.45950803527237e+08 energy=2.84895895438143e+13
cycle=7000 redo=0 time=7.90813545539332e+02 dt=9.43650234923243e-02 mass0=1.45950803527228e+08 energy=2.85556897362064e+13
[MeshBlock] Density/pressure at or within 0.1% of the floor, the VIC dry-gas clamp emptied a cell, the limiter patched one or found a NaN, or the saturation adjustment left a cell unadjusted. Redoing the step with smaller dt (causes: floor).
[MeshBlock] Maximum number of redo attempts exceeded. Terminating.
Terminating abnormally
time=819.064 cycle=7386
tlim=900 nlim=-1
```

## 25 m

Verbatim excerpts (the identical cause line occurs 13 times):

```text
cycle=11000 redo=0 time=6.73931959183416e+02 dt=6.00453334048839e-02 mass0=1.45950859444999e+08 energy=2.85417766160432e+13
cycle=12000 redo=0 time=7.31185996116643e+02 dt=5.17304600822719e-02 mass0=1.45950859444990e+08 energy=2.85633471000934e+13
cycle=13000 redo=0 time=7.76459612112959e+02 dt=3.89133219303064e-02 mass0=1.45950859444982e+08 energy=2.86235158356561e+13
[MeshBlock] Density/pressure at or within 0.1% of the floor, the VIC dry-gas clamp emptied a cell, the limiter patched one or found a NaN, or the saturation adjustment left a cell unadjusted. Redoing the step with smaller dt (causes: floor).
[MeshBlock] Maximum number of redo attempts exceeded. Terminating.
Terminating abnormally
time=798.437 cycle=13724
tlim=900 nlim=-1
```

The 25 m sampled dt decreases from about 0.0600 to 0.0389 s; the 50 m samples decrease to about 0.0944 s. Neither log prints the per-retry dt sequence, so the final dt collapse cannot be reconstructed from these logs.

## Scope and limits

The recorded cause is `floor`, not the separate `limiter`, `nan`, `clamp`, or `saturation` cause bits. The source floor test combines density and pressure minima and also treats a failed NaN comparison as a hit. Thus the logs do **not** identify which variable, value, cell indices, or coordinates triggered it. Only the initial NetCDF output exists for each original aborted run; no failure-state dump is available. No instrumentation/source edits were introduced. Both original and harness drivers return process exit code 0 after these numerical aborts; completion was checked from the log.

The cheap controls above are measured on the unchanged harness build. Other forms at 25 m were not rerun in this follow-up; their earlier completions belong to the D3 build (13/15 total), not this harness build. Frozen does not exist on the harness commit. O5 and the cancelled NCO ctest rerun remain out of scope.

Build/run commands:

```sh
source build_env.sh
cmake -S snapy-harness-repro -B snapy-harness-repro/build -DCMAKE_BUILD_TYPE=Release -DNETCDF=ON -DCUDA=ON -DCMAKE_EXPORT_NO_PACKAGE_REGISTRY=ON -DPython3_EXECUTABLE=/home/chengcli/pyenv/bin/python -DCMAKE_PROJECT_snapy_INCLUDE="$PWD/d3_study/sm75.cmake"
cmake --build snapy-harness-repro/build --target straka.release --parallel 6
bash snapy-harness-repro/study/rho_ref_250/build_driver.sh snapy-harness-repro/build
python d3_study/reproduction/run_repro.py
```

Logs and inputs: [/mnt/data1/chengcli/ai_workspace/worker2/d3_study/reproduction](/mnt/data1/chengcli/ai_workspace/worker2/d3_study/reproduction). Original excerpts: [original_abort_evidence.md](/mnt/data1/chengcli/ai_workspace/worker2/d3_study/reproduction/original_abort_evidence.md).
