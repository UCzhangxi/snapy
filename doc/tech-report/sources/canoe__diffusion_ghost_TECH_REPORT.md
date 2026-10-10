> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# The diffusion operator builds its face coefficients from states that were never meant to be physical

Two defects in `forcing/diffusion.cpp`. One live and first-order, and fixed. One latent and catastrophic, and deliberately left alone.

Commit `8edd5f3` · one commit on top of `43e04fd` · 7 files, +417 / −12

**PROVENANCE (added 2026-09-01).** Rebuilt for the upstream PR as `2fb7a01` — content identical, comments de-jargonized (+414/−12). `tests/test_diffusion.cpp` has since gained further options tests, so this report’s five gates are a subset of the file. All findings re-verified against `2fb7a01` on 2026-09-01: no contradictions.

**Problem.** A diffusive flux is a coefficient times a gradient. The coefficient is built at a cell face by averaging the two cells that meet there. At two kinds of face, one of those two cells does not hold a physical state: at a *domain wall* the ghost cell holds whatever the boundary condition put there, and at an *immersed solid* the cell holds deliberate placeholder numbers ($\rho = 10^{3}$, $p = 10^{9}$) chosen to make the Riemann solver treat the solid as impermeable. The diffusion operator reads both as if they were fluid.

**Evidence.** On a uniform fluid whose exact conductive tendency is zero everywhere, the fluid cells flanking a solid receive **$+1.126125\times10^{3}$** of internal energy per stage — 0.45 % of the cell’s entire internal energy in $10^{-4}$ s. The face heat capacity there is **500.5×** the physical value. Separately, at a reflecting wall the face coefficient is wrong by **−14.72 % / +15.52 %** at `dz/H = 0.35`, and the error is confirmed first order in `dz`.

**Fix, and what is deliberately not fixed.** At a physical wall face the coefficient is extrapolated one-sided from the two nearest *active* cells, reading no ghost at all. That half is live: every configuration with `nu_iso > 0` runs reflecting x1 walls. The immersed-solid half is *not* fixed. Nothing in the tree pairs a solid mask with diffusion, a mask was written and then removed because it was not a complete treatment either, and that path is now byte-identical to the code it started from. The 500× defect is recorded, not repaired — see §3a.

**Review banner, added 2026-09-06** (read against snapy `e2e397a`). Every operator, whitelist and test pointer holds at the tip, and the immersed-solid defect of §3 is still there and still correctly left alone: no shipped card supplies a solid mask together with a diffusion block. Four details are stale or imprecise. (1) §5c “the fix goes quiet rather than mis-firing”: an installed boundary function with no recorded name now emits a `TORCH_WARN_ONCE` before falling back (`meshblock_options.cpp:240-248`). (2) §5c “a length disagreement … means no face is classified”: only a `bcnames` record shorter than the face index disables it, and `set_bfuncs` pads, so callers never hit that path. (3) §6 “in both the C++ and the Python paths”: the Python decomposition (`python/exchange.py`) nulls x2/x3 faces only; x1 seams are nulled in the C++ constructor both paths share. (4) §3’s `hydro_forward.cpp` lines 35/362/363 are now 35/376/377, and §1 quotes the pre-fix `face_average` lines as if current. A precondition the report does not state: without a `boundary-condition.external` block no boundary functions exist at all, so `is_wall_boundary` is false everywhere and the fix is dormant. Found beside the solid path: `rectify_solid.cpp:125` bound `solid_outer` to the inner function, so only inner ghosts were ever marked solid; fixed in the 2026-09-06 series.

## Provenance

This is an instance of a defect family whose general statement is:

> A ghost state chosen to make ONE operator exact is silently consumed by ANOTHER operator that needs a different property of it. A single ghost cell has one density degree of freedom and cannot satisfy both. Nothing warns you, conservation still holds, and only an *exact* constraint exposes it.

The consumer half was found in snapy by source inspection on 2026-08-13; this report is the verification of whether a trigger exists, and the fix for the two that do. The affected code is upstream snapy, not a local carry: `face_average` and the face loop bound `face_end[dim] = cell_end[dim] + 1` have been there since the operator was written, and `mark_prim_solid_`’s placeholders are the upstream defaults.

## 1. Background: where a face coefficient comes from

For each direction the operator loops over faces, and for each face it forms the two-cell average of whatever quantity multiplies the gradient (`src/forcing/diffusion.cpp`):

    face_average(v, idir, start, end) = 0.5 * (v[start:end] + v[start-1:end-1]);

    auto face_end = cell_end;  ++face_end[dim];        // spans BOTH physical wall faces
    auto rho_face = face_average(w[IDN], ...);
        ... -options->nu_iso() * rho_face * stress;                        // VISCOUS
        ... face_average(rho_cv, ...) * face_normal_derivative(temp, ...);  // CONDUCTIVE

Because the face range runs to `cell_end + 1`, the average at the first face reaches `cell_start − 1`, which is a ghost cell, and at the last face it reaches `cell_end`, likewise. So *both* the viscous and the conductive coefficient are functions of a ghost. Nothing in the operator distinguishes a ghost from a fluid cell, and nothing distinguishes a solid cell from a fluid cell — `grep -n "solid\|mask" forcing/diffusion.cpp` returns nothing.

The loop is over all three directions, and so is the mechanism. Whether the ghost it reaches is *wrong*, however, is a question about the direction: it depends on whether the boundary’s mirror is a numerical device covering a real gradient or an honest statement of symmetry. That distinction is what §5b uses to restrict the repair to x1, and it is the reason this report describes a defect in every direction and a fix in one.

## 2. How this was measured — and the measurement that does not work

The instinctive test is a flux or conservation constraint. It is nearly blind to this defect family. In steady state the temperature gradient compensates so the through-flux stays right; what is wrong is the near-wall structure, not the budget.

So the operator is instrumented instead of the output. Two arms of a **single stage** are run that differ *only* in `nu_iso`/`kappa_iso`. Nothing else in the stage depends on those, so

    u(κ) − u(0)   IS   the diffusion operator's contribution, exactly, in float64.

No reference solution, no averaging window, no statistics, one step. The base state is chosen so the exact answer is known analytically. All numbers below come from this, against the production build (snapy `43e04fd`, kintera `8424748`).

## 3. Defect A — a diffusion face does not know a solid from a fluid

### The mechanism

`src/bc/internal_boundary.cpp` overwrites the primitives inside an immersed solid:

    w[IDN].masked_fill_(solid, options->solid_density());    // default 1.e3
    w[IPR].masked_fill_(solid, options->solid_pressure());   // default 1.e9

These are deliberate and correct *for their purpose*: an enormous pressure and density make the reconstructed face states behave as an impermeable wall in the Riemann solver. They are not a physical state and were never meant to be read as one.

The ordering in `src/hydro/hydro_forward.cpp` is what turns that into a defect. The solid fill is applied at line 35, the temperature is derived from the *same* array at line 362, and the forcings — including diffusion — are called with both at line 363. So the operator sees $\rho = 10^{3}$ and `T = p/(ρR)` evaluated from the placeholders.

### The arithmetic

For the dry air mixture used in the probe (μ = 28.96 g mol$^{-1}$, $R_{\mathrm{sp}}$ = 287.05, $c_{v}$ = 2.5 $R_{\mathrm{sp}}$), against a fluid at $\rho = 1$, $p = 10^{5}$:

    T_solid  = 1e9/(1e3 * R_sp) = 3483 K        T_fluid = 1e5/(1 * R_sp) = 348.3 K     (10x)
    rho_cv face = 0.5*(1000 + 1)*c_v            = 500.5 x the physical value           (500x)
    F_interface = -kappa * rho_cv_face * (T_f - T_s)/dz = -1.1261e7
    du[IPR]     = -dt * (F_right - F_interface)/dz      = +1.1261e3

Both factors are wrong, and they compound: an inflated heat capacity multiplying a temperature jump that is itself an artefact.

### The measurement

16-cell column, *uniform* fluid ($\rho=1$, $p=10^{5}$, `v=0`) whose exact conductive tendency is zero in every cell; interior cells 4–7 marked solid; `kappa_iso` = $10^{-2}$, $dt = 10^{-4}$.

| cell | 0–2 | 3 | 4–7 (solid) | 8 | 9–15 |
|----|----|----|----|----|----|
| control, no solid mask | 0 | 0 | 0 | 0 | 0 |
| `du[IPR]` with the solid mask | 0 | $+1.126125\times10^{3}$ | 0 | $+1.126125\times10^{3}$ | 0 |

The predicted $+1.1261\times10^{3}$ and the measured $+1.12612500000000000\times10^{3}$ agree to every printed digit, so the mechanism is not inferred, it is identified. In context: the cell’s own internal energy density is $p/(\gamma-1) = 2.5\times10^{5}$, so a single stage at $dt = 10^{-4}$ s injects **0.45 %** of it. The fluid beside a solid is destroyed on a ~20 ms timescale. This face heat capacity is 50,050 % wrong.

### Exposure: latent, which is the fragile kind of safe

The defect is not live today. The only consumer of a `solid` mask anywhere in the tree is `snapy/examples/shock.cpp:53`, and `examples/shock.yaml` declares no `forcing.diffusion` block. The `solid-density`/`solid-pressure` keys that appear in eight example YAMLs configure the `InternalBoundary` module but do not create a mask. So this is not a regression anyone has suffered — it is a trap set for the first case that turns on immersed solids with viscosity or conduction, which would then be wrong by a factor of 500 with nothing warning it.

### 3a. Why this half was measured and then left alone

A mask was written for it: a face with a solid cell on either side carries no diffusive flux, which is the diffusive counterpart of the reflecting internal boundary the hydro path already applies. It worked — the flanking cells went to exactly zero — and it survived two review rounds. It was then removed, for two reasons that only became clear in review.

**It was never a complete treatment.** The mask closes the faces that touch a solid, but `div_vel` and the shear cross-derivatives still reach a solid cell from faces one further in, which the mask leaves open — putting the effective wall at `dx` rather than `dx/2`. Shipping it would have made immersed-solid diffusion look supported when it is not.

**And nothing uses it.** A refusal was considered instead of a mask, and also rejected: a `TORCH_CHECK` that turns a running configuration into a fatal error is a *larger* change to that path than the mask was, for a path no case exercises. So the immersed boundary is untouched, byte for byte.

The cost of that choice is stated plainly because it is real: **there is now no signal at the site** — no mask, no check, no comment. The first case to pair immersed solids with `nu_iso` or `kappa_iso` gets a factor of 500 silently, and an issue-tracker entry is the only warning. That is the right trade only for as long as the combination stays unused.

## 4. Defect B — a wall face coefficient is the first cell’s value, not the wall’s

### What the boundary conditions actually install

snapy’s entire external boundary menu is `reflecting`, `periodic`, `outflow`, `solid` and `custom`; the custom hooks are empty functions and nothing in the tree fills them. Nothing imposes a temperature, an entropy, or a hydrostatic reference into a ghost. That is worth stating plainly, because it is the *good* half of the result: **the defect family’s trigger does not exist in snapy.** Measured on a static stratified column with gravity on, so the well-balanced x1 path is engaged exactly as in a production case:

    x1-inner:  ghost_rho/active_rho = 1.000000000000000   ghost_T/active_T = 1.000000000000000
    x1-outer:  ghost_rho/active_rho = 1.000000000000000   ghost_T/active_T = 1.000000000000000
    dT/dn at BOTH wall faces = 0.000000000000000e+00

The ghost is a bit-exact mirror of a physical state. It has a free density degree of freedom and no operator competes for it. The defect family’s precondition — a ghost density with zero remaining freedom — is absent.

### What is nevertheless wrong

A mirror is a physical state at the ghost’s reflected position, not at the wall. The face average of a mirrored quantity is

    face_average = 0.5*(rho_a + rho_ghost) = 0.5*(rho_a + rho_a) = rho_a

whereas the wall value the flux law asks for is $\rho(z_{\mathrm{wall}})$, half a cell away. For an isothermal layer $\rho(z) = \rho_{0}e^{-z/H}$ with cell centres at `(i+½)dz`, the ratio is exactly $e^{\mp dz/2H}$. Measured:

| dz/H | formed / analytic, x1-inner | x1-outer | predicted $e^{\mp dz/2H}$ |
|----|----|----|----|
| $1.1614\times10^{-4}$ | 0.999941930224 | 1.000058073148 | 0.9999419301 / 1.0000580734 |
| 0.3501 | 0.852758 (−14.72 %) | 1.155179 (+15.52 %) | — (stratification not isothermal) |

Ten-digit agreement at the resolved end confirms the error is exactly the O(`dz`) mirror truncation and nothing else. The second row is the size it reaches at a production resolution.

### Why it matters for viscosity and not for conduction

Parity decides this, and it is worth being precise because it bounds what the fix can change. At a reflecting wall, density and temperature are mirrored *even*, so the face temperature gradient is identically zero and the conductive wall flux vanishes — the coefficient multiplies exactly nothing, at any resolution. Tangential velocities are also even, so the tangential stress vanishes too. But the normal velocity is mirrored *odd*, so $\partial v_{1}/\partial n = 2v_{1,a}/dz$ at the wall face is nonzero whenever the fluid next to the wall is moving — which, in a convecting atmosphere, is always. That single surviving term carries the −14.7 % coefficient.

Measured directly: with a uniform vertical velocity, so that $\partial v_{1}/\partial n$ is zero on every interior face and nonzero only at the two walls, the viscous tendency is nonzero **only** in the cells adjacent to each wall and exactly zero in all twelve interior cells. The term is live.

Unlike defect A, this one is not a placeholder being misread; it is ordinary first-order boundary truncation, of the kind every finite-volume code has somewhere. It is fixed here because the fix is exact and costs nothing.

[EMBEDDED FIGURE: binary not copied; generating script not recorded in the source HTML]

**Figure 1.** **The two defects.** **A:** at a wall the reflecting ghost is a mirror, so averaging the two cells returns the value half a cell inside the domain rather than the value at the wall; extrapolating from the two nearest active cells lands on the wall and touches no ghost. **B:** the face between a solid placeholder cell and fluid builds a heat capacity 500× too large and multiplies it by a temperature jump that exists only because the placeholder pressure is $10^{9}$. This half is measured but deliberately not repaired: no configuration reaches it, and a face mask alone would not have made the path correct (§3a).

## 5. The fix

### (a) The immersed-solid half — not fixed

See §3a. The path is unchanged from the code this change started from.

### (b) A wall face coefficient is extrapolated from active cells

Linear extrapolation from the two nearest active cell centres onto the face. Writing $w_{a}$, $w_{b}$ for the two cell widths, the face sits $w_{a}/2$ from centre *a* and the centres are $(w_{a}+w_{b})/2$ apart, so

    t = w_a / (w_a + w_b)
    q_face = q_a + (q_b - q_a) * (-w_a/2) / ((w_a + w_b)/2)
           = (1 + t) * q_a - t * q_b

and the same expression holds at the upper wall, where both the offset to the face and the direction to the second cell change sign together. On a uniform mesh `t = ½` and this is the familiar $1.5 q_{a} - 0.5 q_{b}$; the width-weighted form is used instead so that a stretched grid is handled correctly rather than silently mis-weighted. It is exact for any profile linear near the wall and second order otherwise, and it reads no ghost.

**The product is extrapolated, not the density.** In snapy `kappa_iso` is a constant scalar, so there is no ghost conductivity — but $c_{v}$ is state dependent under the moist EOS, so the conductive coefficient extrapolates $\rho c_{v}$ as a single quantity. The viscous coefficient extrapolates `ρ`, which is the whole product there because `nu_iso` is likewise a constant.

A positivity fallback returns the nearest active cell value if the extrapolation would go non-positive. That value also reads no ghost, so the fallback cannot reintroduce the defect.

**x1 only — and this is the substantive restriction, not an implementation detail.** The defect argued in §4 is a property of a wall that cuts a *monotone* profile: the mirror is a numerical device, the field genuinely has a gradient there, and killing that gradient in the ghost costs an order. In this code the monotone direction is the vertical — gravity is `grav1`, the well-balanced reconstruction is x1, the bottom anchoring is x1. A lateral `reflecting` face is as likely to be a genuine *symmetry plane*, and there the mirror is not a device: the field really is even, so its wall-normal derivative really is zero, and the first active cell value is already a second-order estimate of the face value. Both forms are then second order, but the one-sided form carries roughly three times the error constant — one-siding a symmetry plane makes the answer worse, not better. The asymmetry is the whole argument, and it does not hold laterally.

There is a second, blunter reason. `reflecting` is the *default* for every face a configuration does not name, so extending the branch to x2/x3 would opt configurations into a changed wall stress that never asked for it, silently. The restriction is pinned by a gate (`x2_wall_is_not_one_sided`, §6) that asserts the x2 wall still reads the average, so a later widening has to be a deliberate act that breaks a test rather than an edit that quietly generalises a loop bound.

### (c) Which faces count as walls — a whitelist, not a blacklist

The existing predicate `is_physical_boundary()` answers “is a boundary function installed on this face”, which is true of every external boundary including periodic. It is the wrong question here, and the first version of this fix got it wrong by inverting it — treating everything except periodic as a wall. Three of the five boundary functions must keep the two-cell average:

- **`periodic`** — the ghost is the *true* state of the wrapped neighbour. One-siding it would give the two images of one physical face different coefficients, which is a conservation leak, not an accuracy loss.
- **`outflow`** — a zero-gradient copy. The boundary condition’s own statement is that the face value *is* the first active cell value, which is exactly what the average returns. Extrapolating there contradicts the condition and injects a spurious half-cell gradient into the coefficient.
- **`custom`** — an empty hook filled by user code. Whatever that code wrote — a Dirichlet state, a nested-grid copy, a hand-rolled wrap — cannot be interpreted here, and discarding it is not this operator’s decision to make.

So the new predicate `is_wall_boundary()` is a whitelist of the one condition whose ghost the operator may legitimately extrapolate past: `reflecting`, which mirrors the interior, so the ghost is a physical state sitting at the wrong place. `solid` was in that whitelist for one revision and should not have been — `solid_inner`/`solid_outer` write a bare `1` into *every* variable, so the temperature gradient at such a face is wrong by five orders of magnitude and repairing the coefficient would not rescue it. Closing such a face outright is the correct treatment, and it is not attempted here — see §3a and §5a. It is backed by a `bcnames` record written beside `bfuncs`. Because those are two parallel arrays, they can desynchronise: a block assembled from Python rather than from YAML has no names at all, and `set_bfunc` can replace a function while leaving the old name behind. Both are handled explicitly — `set_bfunc` clears the name it invalidates, and a length disagreement between the two records means no face is classified. Every failure of that machinery therefore falls back to the two-cell average, which is the safe direction: the fix goes quiet rather than mis-firing.

**Seam safety at nb1 \> 1 is by construction rather than by a guard:** an internal block seam installs no boundary function at all, so `is_wall_boundary` is false there and neither branch of the fix can fire on a seam face. This matters because a one-sided stencil applied at a seam would corrupt data the neighbour owns.

### What the fix deliberately does not touch

- **The velocity divergence at a wall face — and this bounds what §4 claims.** By mirror parity the ghost divergence equals the active one *exactly*, so `face_average(div_vel)` at a wall returns the cell value, not the face value: the same O(dz/2) error the density had. It sits inside the *stress*, not the coefficient, so it is outside this defect family and one-siding it would change the stress operator itself — a larger claim needing its own validation. The honest consequence is that **the wall normal stress is now second order in its coefficient and still first order in its kernel**. The fix removes one of the two first-order terms, not both. This is recorded as a follow-up rather than smuggled into this change.
- **The cross-derivative shear terms.** At a reflecting wall $\partial v_{1}/\partial x_{2}$ is odd about the wall, so their average is *exactly* zero at the wall face. Already correct.
- **The parabolic timestep.** `max_time_step` depends only on cell widths and `max(nu_iso, kappa_iso)`, both unchanged.

## 6. Validation

Five gates ship with the fix, in `tests/test_diffusion.cpp`. They are unit tests on the operator itself, not on a run, for the reason in §2. Each was verified to **fail on a build with the corresponding branch reverted** — a gate that has not been seen to fail is not evidence.

| Gate | Construction | Fixed | Reverted |
|----|----|----|----|
| `wall_flux_does_not_depend_on_the_ghost_density` | two states differing ONLY in the x1 ghost density — the mirror the boundary installs versus the linear continuation — must give the same tendency, with the normal velocity mirrored odd so the wall carries a real stress. Asserts that stress is nonzero first | PASS | FAIL |
| `wall_face_coefficient_reads_no_ghost` | density linear in x1 then reflected, so the ghost is off the profile by exactly one mirror; temperature linear everywhere so dT/dn is the same at every face. The tendency must then be the *same constant* in every interior cell | PASS | FAIL |
| `x2_wall_is_not_one_sided` | the same construction along x2 on a companion 2-D config, asserting the *opposite*: the x2 wall row must still sit half a slope short, because the repair is x1-only (§5b). Pins that restriction rather than leaving it to inspection | PASS | — |
| `periodic_x1_face_is_not_extrapolated`, `only_reflecting_counts_as_a_wall` | the same state under a periodic x1, where the two-cell average is the correct answer; plus the predicate itself against periodic, outflow, custom, an unnamed function, and a desynchronised record | PASS | — |

The last two rows are guards rather than regression tests and pass on unfixed code by construction: they exist to catch the new branch *mis*-firing — either on a face whose ghost is a true neighbour, which would break conservation, or on a lateral wall the fix deliberately does not claim. That distinction is worth stating, because a suite in which every test passes before and after proves nothing.

The wall gate is built so that the two answers differ by a factor of two rather than by a few percent: on a linear profile the two-cell average is exact on every *interior* face, so any deviation of the wall cells from the interior constant is attributable to the wall face alone. That is what makes it an exact constraint rather than a tolerance. Whole suite: `test_diffusion` and `test_diffusion_moist`, 100 % passed, CPU float32 and float64.

### End-to-end, through the full solver rather than the unit path

The gates call the operator directly. The same two states were also run through a complete MeshBlock stage against the production build and against a build of the fix, so the result is not an artefact of how the tests reach the operator.

| quantity, per stage | base `43e04fd` | fixed `8edd5f3` |
|----|----|----|
| viscous `du[IVX]`, twelve interior cells | 0 (exactly) | 0 (exactly) |
| viscous `du[IVX]`, second cell from each wall | $+2.455592729155853\times10^{-9}$ | bit-identical |
| viscous `du[IVX]`, bottom wall cell | $-3.088087\times10^{-8}$ | $-3.475022\times10^{-8}$ (+12.5 %) |
| viscous `du[IVX]`, top wall cell | $-3.177926\times10^{-10}$ | $-2.696997\times10^{-10}$ (−15.1 %) |
| viscous `du[IPR]`, every cell | — | bit-identical |

Every row is the claim of §4 made falsifiable and then not falsified: the change is confined to the two cells touching a wall, it does not reach even the second cell in, it moves the momentum budget in opposite directions at the two walls as a density-weighted coefficient must, and it leaves the energy budget *bit-identical* — because the odd-mirrored normal velocity makes the viscous work term vanish at a wall face, exactly as the parity argument said it would.

### Inertness

The fix is a no-op wherever it should be, and this is checked rather than asserted: on any face that is not an x1 `reflecting` wall the coefficient is the two-cell average, byte for byte as before, because the branch is not entered; with a uniform density the extrapolation of a constant returns that constant, which is why the four pre-existing operator tests are untouched; and at a reflecting wall the conductive branch multiplies a temperature gradient that is identically zero, so **the wall fix cannot move conduction in any current production case**. The only quantity it can move is the viscous wall normal stress. That is a tight enough claim to be falsifiable by the battery.

**Seam safety was verified, not assumed.** A block whose x1 face is an internal seam has `bfuncs[kInnerX1] = nullptr` set explicitly during decomposition, in both the C++ and the Python paths, and `is_wall_boundary` returns on that nullptr before it looks at anything else. Neither branch of the fix can fire on a seam face at `nb1 > 1`.

### The example battery, and what it is not evidence of

This is a core file, so the full battery is mandatory rather than optional. The `physics` tier — 19 CPU cases and 9 GPU cases — was run against a build of `8edd5f3` (`stack=2.10.6.dev1+g8edd5f39d`) and is **28/28 pass, zero failures**. Its tables were then compared cell by cell against the base build’s own `physics` tables from 2026-08-07 rather than merely counted.

**The battery is far from blind here, which is worth stating precisely because the honest reading still cuts the other way.** Eight of the twenty-eight cases — `10`, `10b`, `11`, `21`, `30`, `31`, `40`, `41` — carry a `forcing.diffusion` block with `nu_iso > 0`, and every one of them runs `reflecting` x1 walls, so in all eight the fixed branch is *entered* rather than dormant. Two more (`32_neptune2d_ge`, `32b_wb_x1seam_nb1x2`) set `nu_iso = 0` deliberately to follow the reference calculation, and the rest have no diffusion at all. So the change executes; what the battery cannot do is *resolve* it.

That is the caution, and it survives the better coverage. Against the base build, **every verdict, rank count, cycle count, warning count and mass drift is identical on all 28 cases**. Four cells differ in their last digit or two: `10_moist_cloud_slab` 2410.11→2410.1 and `10b_restart_chemistry` 4808.15→4808.14 simulated seconds (both ~$2\times10^{-6}$ relative), `37_dry_convection_box` 26.0999→26.1012 ($5\times10^{-5}$), and `13_rt_moist_uranus`’s mass drift $-1.885\times10^{-14}$→0.

**It is tempting to read the diffusion-enabled ones as the fix. A control that arrived by accident shows they are not.** The change was squashed after the first battery ran, so the suite was run twice against two builds whose *only* difference is a named temporary inlined in the conductive branch — the same expression, computed and subtracted in the same order. Between those two runs of semantically identical code, `31_jupiter2d_crm` moved 4780.39→4780.4 and `37_dry_convection_box` moved 26.0993→26.1012. So a cell of that magnitude moves without any code change at all, and `31` — one of the diffusion-enabled cases — is exactly such a cell. Two further facts point the same way: `37` has the largest excursion of any case and has no `forcing.diffusion` block, and `41_straka_density_current` (`nu_iso = 75.`, by two orders the largest viscosity in the suite, and therefore the case that should move most) is bit-identical across all three runs. What these cells measure is the battery’s own run-to-run spread on unseeded cases, and that spread is larger than any candidate signal in it. **No numeric claim about this change rests on the battery.** The claims rest on the gates and the single-stage probes, which are exact.

## 6a. Independent review, three times

Each version of this change was put through an adversarial review by a reviewer given the code, the claims, and instructions to refute them. All three found real defects; the second found one the first missed that mattered more than anything in the first round, and the third reversed a generalisation the first had asked for.

### Round one

The wall predicate was a *blacklist*, wrongly catching `outflow` and `custom` (§5c). `bcnames` could desynchronise from `bfuncs`. And three test defects: the solid gate ran with every velocity at zero, so `mark_prim_solid_`’s velocity fill was a no-op and the viscous half of the mask was never executed; one tolerance sat below the float32 round-off floor of the quantity it bounded; and the whole suite was one-dimensional in x1, so the face-axis arithmetic only ever ran with the face axis last. All fixed in `ba50e2f` and `63b3d93`.

### Round two — the gates were certifying the wrong branch

The second reviewer noticed something the first did not, and it is the most useful finding of the whole exercise. **All three wall gates exercised only the conductive coefficient — the branch this report itself argues multiplies exactly zero in production.** At a reflecting wall the mirror makes `dT/dn` vanish, so a conduction-only gate is satisfied by code that still reads the ghost for the momentum flux. The reviewer proposed the decisive check: revert the wall branch for `rho_face` alone and leave `rho_cv` fixed. Done, and the entire suite stayed green.

So a fourth gate was added, asserting the property the fix actually claims rather than a consequence of it: **the wall flux must not depend on the ghost density.** Two states differing only in that ghost — the mirror the boundary condition installs, versus the linear continuation — must give the same tendency, with the normal velocity mirrored odd so the wall carries a real stress. It fails on exactly the revert above, where all twenty-two other tests pass.

That round also closed two more: the bulk `bfuncs` setter still left `bcnames` stale, so a caller could install unknown functions from Python and keep the parsed wall names — the very bypass the previous commit claimed to have shut; and `solid` did not belong in the whitelist. It further showed that the follow-up list filed after round one was wrong in both directions: the source-term forcings are *not* the same defect family, because each writes only into the cell it reads and `fill_cons_solid_` restores solid cells every stage. Diffusion was a bug precisely because it is the only forcing with a *flux*. That list is retracted and replaced.

The pattern is worth naming, because it is the same one this whole report is about: **a gate that certifies a quantity which is structurally zero proves nothing about the code path that carries the signal.**

### Round three — the fix was claiming more ground than the argument covered

Round one had objected, correctly, that the suite only ever ran with the face axis last, and the response had been to extend both the test and *the fix itself* to x2. Round three pointed out that the second half of that response does not follow from the first. Exercising the arithmetic on a non-final axis is a test-coverage question; applying the one-sided coefficient there is a physics claim, and the physics claim is false at a lateral wall that is a genuine symmetry plane, where the mirror is not a device and the average is the better estimate (§5b). The fix was restricted to x1 in `9dc431c`, and the x2 test was inverted to assert the restriction rather than the generalisation.

Round three also removed a residue the descoping had left behind: guard comments that described the solid-mask version of the code, and a named temporary in the conductive branch that existed only to be multiplied by the mask that no longer ships. The change was then squashed to a single commit (`8edd5f3`), so the diff that would be reviewed upstream is the change itself rather than its history of reversals.

## 7. Known limitations and follow-ups

Stated here rather than left to be rediscovered. None of these is a regression introduced by this change except where noted.

- **The wall normal stress is still first order in its kernel.** Fixing the coefficient removes one of the two O(dz) terms at a wall; `face_average(div_vel)` supplies the other. A complete second-order wall stress means one-siding the strain terms too, which changes the stress operator and needs its own validation.
- **The parabolic timestep does not see the new coefficient.** `max_time_step` returns a function of the cell width and `max(nu_iso, kappa_iso)` only, and never included density. Because the extrapolation raises the wall coefficient on the dense side of a stratification — by about 17 % at `dz/H = 0.35` at the inner wall — the effective local diffusivity in that one row is now correspondingly higher than the timestep controller assumes. The existing safety factor covers this at any sane CFL, but a run sitting exactly at the parabolic limit has slightly less margin in the wall row than before. *This one is introduced by this change.*
- **`rectify_solid` marks ghost cells solid** and by default does not re-apply the boundary functions afterwards, so a ghost adjacent to a physical wall can be solid-marked while that face is still classified as a wall. With the solid half descoped nothing reads that marking here, so it cannot bite — but it is a precondition of the mask this change chose not to ship, and it is filed with the rest of that work rather than resolved.
- **Every other forcing still consumes solid-marked primitives.** The same ordering that exposed diffusion exposes the rest: `relax_bot_temp`, `relax_bot_velo`, `relax_bot_comp` and `body_heat` all read `w[IDN]` and `specific_heat_cv` over rows that may contain solid cells, and would weight a placeholder ρ = $10^{3}$ a thousandfold. This change fixes diffusion only; the rest is filed separately, because a mask threaded through fourteen forcings is a different piece of work from a defect in one.
- **The width-weighted extrapolation has no test coverage,** because snapy has no stretched-mesh support at all — every cell width is uniform, so `t ≡ ½` and the general form degenerates to the familiar $1.5q_{a} - 0.5q_{b}$. It is written in the general form deliberately.
- **The positivity fallback is element-wise and silent.** A wall face can be second order in some columns and first order in others with no diagnostic, which would make a convergence study of the wall term non-monotone. It has not been observed to fire.

## Files changed

| File | Role |
|----|----|
| `src/forcing/diffusion.cpp` | the wall-face extrapolation |
| `src/mesh/meshblock.hpp`, `src/mesh/meshblock_options.cpp` | `is_wall_boundary()`, the `bcnames` record it reads, and `set_bfuncs` so a bulk replacement cannot leave a stale name |
| `python/csrc/pymesh.cpp`, `python/snapy/mesh.pyi` | route the bulk `bfuncs` setter through `set_bfuncs`; give `set_bfunc` the optional `name` that declares what was installed |
| `tests/test_diffusion.cpp`, `tests/test_diffusion_2d.yaml` | the five standing gates and the 2-D configuration one of them needs |

`src/hydro/hydro_forward.cpp` and `src/forcing/forcing.hpp` were touched by earlier revisions and are back to their original state byte for byte: the immersed-solid path is untouched.

All measurements were taken on one machine and software stack (snapy `43e04fd`, kintera `8424748`), comparing single stages that differ only in the variable under test, in float64. No number in this report is read from an output file: snapy’s netcdf writer is `NC_FLOAT` throughout, so nothing below ~$10^{-8}$ survives it. Reported differences are relative unless stated otherwise.
