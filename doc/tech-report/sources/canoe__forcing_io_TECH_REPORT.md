> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# A drag that rotates, and a floor you cannot see past

Two small, independent defects fixed alongside a companion scalar-seam fix. 2026-08-28.

**STATUS (added 2026-09-01) — BOTH FIXED AND ON THE PR BRANCH.** The drag fix = `9585ada` (fix + rewritten test, one squashed commit), the netcdf-precision fix = `57369fc`, both on the PR branch. The §Upstream blocker below is **RESOLVED**: the face relaxation shipped as an opt-in YAML option (`relax-bot-temp: {at-face: true}`, default false) in `8fb8f34` — making the face BC opt-in upstream — so the upstream cell-centre default and its unit test are untouched, and the `SNAPY_RELAX_BOT_CENTRE`/`SNAPY_RELAX_BOT_FACE` environment variables no longer exist at the PR branch tip (the `t0 >= t1` isothermal guard survives inside `8fb8f34`). SHA map: scalar-seam fix `283b9df`→`5c61b39`; drag fix `19e9423`+`f1b89a1`→`9585ada`; netcdf-precision fix `075af84`+`658e8f2`→`57369fc`; the base `1dfcfe5` is not carried.

Neither is a physics emergency; both are the kind of defect that stays invisible precisely where you would look for it. They are reported together because they share a build and a verification run, not because they are related.

**Review banner, added 2026-09-06** (read against snapy `e2e397a`). Both fixes are as described at the tip. Three details. (1) “All ten call sites” of `as_float`: there are fourteen, all inside the `else` of `if (nc_dbl)` as the report says, and the `TORCH_CHECK` guards them regardless; the source comment carried the same “ten” and is corrected in the 2026-09-06 series. (2) “about 4 s of granularity at $3\times10^{7}$ s”: the float spacing on $[1.68\times10^{7}, 3.36\times10^{7})$ is 2 s. (3) The quoted pre-fix and fixed lines are the two sponges’ form; `relax_bot_velo.cpp:63-73` lowers a stacked slab with an `expand_as` cosine and differs in shape. A third output commit in the same group, `4b802af` (a barrier after each root-only combine so no rank returns before the combined file exists), is not covered here.

## Defect 1 — the drag was not antiparallel to the wind

### The defect

Three forcing modules — `top_sponge_lyr`, `bot_sponge_lyr` and `relax_bot_velo` — built a drag force from the primitive velocities and added it straight into `du`:

```cpp
du[IVY] -= w[IDN] * w[IVY] / options->tau() * scale * dt;
```

Primitive velocities are **contravariant**; the conserved momenta in `du` are **covariant**. On the gnomonic cubed sphere the horizontal metric is not diagonal, so the correct drag on $m_2$ is `rho*(v2 + cos_theta*v3)`. What was applied was `rho*v2`.

**Why it went unnoticed for so long.** `cos_theta = -sin(x2v)·sin(x3v)` is **exactly zero at a panel centre** and reaches −1/2 only at a corner. The error is therefore identically absent in the middle of every panel — where anyone eyeballing a field would look — and worst in the eight corners. And because the force is not antiparallel to $\mathbf{v}$, it does not brake the wind; it slowly *rotates* it. There is no blow-up and no conservation violation to trip a gate.

### The fix

Lower the force before adding it, with snapy's own `coord_vec_lower_` — the helper the equation of state already calls every step in `prim2cons`:

```cpp
auto force = w[IDN] * w.narrow(0, IVX, 3) / options->tau() * scale * dt;
coord_vec_lower_(force, pcoord->cosine_cell_kj);
du.narrow(0, IVX, 3) -= force;
```

This is `Fix Coriolis (#168)` (`6953016`, June) applied to the three siblings that were never swept; `coriolis.cpp` was until now the only forcing in the tree that converted.

Coriolis needs a *different* transform (contravariant → spherical → covariant) only because $\boldsymbol{\omega}$ is meaningful solely in an orthonormal frame. A force already proportional to $v^i$ needs the single lowering and nothing more.

**A defect found in this fix, by review, before it ran.** The first draft hoisted the scalar factor, writing `v * (rho/tau * scale * dt)` where the original was `rho*v/tau * scale * dt`. Algebraically identical; *not the same floating-point expression*. Measured over $2\times10^{5}$ draws, **53 % of force values shifted by one ulp** — so every cartesian and spherical-polar sponge run would have diverged from baseline at round-off, while the commit claimed they were unchanged. The operand order is now preserved deliberately, and orthogonal grids really are bit-identical: `cosine_cell_kj` is exactly zero there, so the lowering is the exact identity.

### Verification — and what happened when the test was finally run

A run cannot test this. The instrument is a unit test: assert that the applied force is antiparallel to the *lowered* momentum, and that the pre-fix contravariant direction is measurably different, so a regression cannot pass by coincidence. Testing at a panel centre would pass either way, which is the whole point.

**The test as first written was vacuous, and only a deliberate anti-vacuity assertion revealed it.** It was committed in `17d7342` but never compiled; two independent reviews passed over it. Building it took about 25 minutes and it failed — on the *fixed* code.

The fixture was `test_exchange.yaml`, which sets `nx1: 1`. With `nc1() == 1` the guard at `meshblock_options.cpp:91` never installs an x1 boundary function, so `is_physical_boundary(0, 0, ±1)` is false and every forcing module that guards on it returns immediately. `du` was identically zero, and the covariance assertion passed on `0 == 0`. Had the “the pre-fix answer must differ here” assertion not been written, this test would have passed against the fix, against the bug, and against a build with no drag at all.

A second defect in the same test: the cell was chosen by `cosine_cell_kj.expand_as(…).argmax()`, but that tensor is **stride-0 along x1**, so the argmax always returns x1 index 0 — a cell where `relax_bot_velo` applies no force at all.

The rewritten test (`f1b89a1`) uses a dedicated cubed-sphere fixture with `nx1 > 1` and real x1 boundary conditions; asserts over the whole field rather than at one cell; scales its tolerance on $\max(|d_2 m_3|, |d_3 m_2|)$ rather than one product that may vanish; adds `EXPECT_GT(dumax, 0)` so vacuity is impossible rather than merely detectable; and covers all three modules rather than one. Both arms were run:

| arm | result |
|----|----|
| against the fix (`19e9423`) | **PASS**, 6 panels × 3 modules |
| against pre-fix (three forcing sources reverted to `1dfcfe5`) | **FAIL**, 36 assertions = 6 × 3 × 2 |

The $|v_2| \ne |v_3|$ choice in the fixture is load-bearing and is now commented as such: the pre-fix cross product is $\cos\theta\,(v_3^2 - v_2^2)$, which vanishes identically when the two are equal in magnitude — so “tidying” the fills to $v_2 = \pm v_3$ would silently make the test pass against broken code.

**A third defect, in the base rather than in any of the three fixes.** Running the suite showed that the upstream test `forcing.relax_bottom_temperature` — present unmodified at snapy `main` (`43e04fd`) — now throws. The index-convention guard added by `8a9c931` and made default by `1dfcfe5` asserts strictly `t0 > t1`, but the upstream fixture is *isothermal*, giving `t0 == t1` exactly, where the extrapolation $1.5\,T_0 - 0.5\,T_1 = T_0$ is exactly right. The guard states a property of a stratified atmosphere, not of the index convention it claims to check. Relaxed to `>=` in `4a37546`.

With that relaxed the guard passes and a *separate* disagreement surfaces: the test’s numeric expectation encodes the old cell-centre relaxation, and the face BC changes the applied `du` by the gain $1/1.5$. Confirmed by one discriminating run — `SNAPY_RELAX_BOT_CENTRE=1` makes the test pass. \[2026-09-01: this env var no longer exists — under the shipped `at-face` option the test passes by default.\] **This is a deliberate default change, not a bug, and it is an upstreaming blocker rather than a physics one:** see §Upstream.

## Defect 2 — every netcdf variable was NC_FLOAT

### The defect

Every variable snapy wrote to netcdf was `NC_FLOAT` — all fifteen `nc_def_var` sites. Nothing could be measured from an output file below a $\sim 10^{-8}$ floor, which is *coarser than the conservation drifts these runs are gated on*. This is why conservation has to be read off the float64 cycle line, and it is what made an earlier investigation look like a physics problem.

It also bit time: `float timef = current_time` at $t \sim 3\times10^{7}$ s has about 4 s of granularity.

### The fix

A `double_precision` flag on an output block, **defaulting to false**. The fill loops are single-versioned in double and narrowed once at write time, so the float path costs one extra copy and the double path none. Coordinate fills moved from `.item<float>()` to `.item<double>()` — otherwise a double file would still carry float-truncated axes.

```yaml
outputs:
- type: netcdf
  variables: [scalar_prim]
  dt: 86400.0
  double_precision: true      # opt in only where the precision is needed
```

**Two defects found in this fix, by review, before it ran.**
(1) The narrowing helper copied the *whole* buffer regardless of how much the variable had filled — the scalar branch fills exactly one element — so every float write read uninitialised heap. Harmless on x86 SSE, but undefined behaviour, it poisons sanitiser builds, and under FP trapping a garbage bit pattern can raise `FE_INVALID`. The buffer is now zero-initialised.
(2) `PNetcdfOutput` hardcodes `NC_FLOAT` at fifteen sites and never read the flag, so setting it on a parallel-netcdf path would have returned a float file *with no warning* — measuring conservation off a file you believe is float64 and is not, which is the exact failure this fix exists to prevent. It now fails loudly instead.

### Verification

One run with both streams, measured from the files:

| stream                   | size    | time        | x1/x2/x3    | r_He        |
|--------------------------|---------|-------------|-------------|-------------|
| default (flag off)       | 1.59 MB | float32     | float32     | float32     |
| `double_precision: true` | 3.17 MB | **float64** | **float64** | **float64** |

And the default path against a control built without the change, frame 0, same config and restart. *An earlier draft of this table reported “1/96 words” in `x2`. That undercounted by an order, because it compared only the cell-centre axes and never the* **face** *axes.* Re-measured over every variable in the file:

```text
r_He   BYTE-IDENTICAL      <- the data
time   BYTE-IDENTICAL
x1     BYTE-IDENTICAL
x1f    BYTE-IDENTICAL
x3     BYTE-IDENTICAL
x2     DIFFERS:  1/96 words   max |delta| = 2.384e-07   maxrel = 6.519e-08
x2f    DIFFERS:  5/97 words   max |delta| = 2.384e-07   maxrel = 1.156e-07
x3f    DIFFERS:  4/65 words   max |delta| = 1.192e-07   maxrel = 1.156e-07
                --------
       TOTAL:   10 words across 3 variables, all float32, all 1 ulp
```

All ten are the predicted consequence of removing a double rounding: the old code computed `(float)((double)(float)x + face·π/2)` and the new rounds once. Each is an accuracy *improvement* at the 1-ulp level (float32 eps is $1.19\times10^{-7}$, and the relative deviations are $6.5\times10^{-8}$ to $1.2\times10^{-7}$). It is scientifically irrelevant, but a byte-compare gate on cubed-sphere axis variables will trip on ten words, not one — anyone diffing files should be told the right number to expect.

### Two further defects, found by review after the fix was written

**The pnetcdf rejection fired too late.** The `TORCH_CHECK` sat in `write_output_file`, so `file_type: pnetcdf` with `double_precision: true` passed setup, launched, and ran to the *first output time* — potentially hours on 384 ranks — before aborting. Outputs are constructed at setup (`meshblock.cpp:202`, beside the existing `validate_slice` calls), so the check belongs in the constructor. Moved in `658e8f2`; the write-time check is kept as a cheap defence against a post-construction mutation.

**A latent heap overflow in the narrowing helper.** `std::vector<float> fbuf(nc_dbl ? 0 : nbuf)` is *empty* on the double path, while `as_float()` copies `nbuf` elements unconditionally. All ten call sites sit inside an `else` of `if (nc_dbl)` today, so it is unreachable — but one future call site outside that guard is a silent overflow of `nbuf` floats, not a crash. Now asserted rather than relied upon.

## Upstream

None of the scalar-seam, drag or netcdf-precision fixes is on `chengcli/snapy`. Running the test suite changed what can honestly be said about upstreaming them, so the position is recorded here.

| fix | upstream readiness |
|----|----|
| **scalar-seam fix** (`283b9df`) | **Ready.** Four functional lines, a derived mechanism, a one-variable A/B, and no test in the upstream suite changes behaviour. The strongest of the three. |
| **drag fix** (`19e9423` + `f1b89a1`) | **Ready**, with the rewritten test. There is an in-repo precedent, `Fix Coriolis (#168)`. The test now carries its own negative control. |
| **netcdf-precision fix** (`075af84` + `658e8f2`) | **Ready.** Opt-in flag, default off, default path differing only in ten 1-ulp axis words. |
| **the base `1dfcfe5`** | **NOT ready — blocker.** It changes a unit-tested default and breaks `forcing.relax_bottom_temperature` on snapy `main`. |

**The blocker is the base, not the three fixes.** All three sit on `1dfcfe5`, which makes the bottom-face relaxation the DEFAULT. The upstream test encodes the old cell-centre behaviour, and the face BC changes the applied `du` by the gain $1/1.5$; `SNAPY_RELAX_BOT_CENTRE=1` restores the pass. A PR carrying this base as it stands would fail snapy’s own CI. \[2026-09-01: resolved — the shipped `at-face` option (status box) carries no default change and no env var.\]

## Provenance

| item | where |
|----|:---|
| drag fix | `19e9423`; test `17d7342` |
| netcdf-precision fix | `075af84` |
| base | `1dfcfe5` |
