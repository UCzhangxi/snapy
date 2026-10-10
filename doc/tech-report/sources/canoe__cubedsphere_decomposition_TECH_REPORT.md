> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# A cubed-sphere ghost interpolated from a halo that had not been filled yet

Why `nb2 = 1`, `2` and `4` gave three different answers to the same problem — and the ordering constraint, invisible until the panel is spread across processes, that the fix imposes.

Delivered as `0379406`, one squashed commit on the PR branch · developed as five commits (tip `74ff385`), retained as history · 11 files, +242 / −44 · one new option · 2026-08-16

**PROVENANCE (added 2026-09-01).** Ships upstream as two commits on the PR branch: `40906e0` (the exchange fix of this report; was `0379406`) and `96c8851` (the coordinate fix; was `68e4129`). The PR branch now carries the whole rebuilt PR series (tip `4b802af`, since 2026-09-01); the development commits are retired under an archive tag; the validation build at `0379406` is retired (rebuildable from its sha). At the PR-branch tip the in-code issue tags were removed, so quoted snippets differ from the tree by the trailing tag only. Mechanism re-verified against `40906e0` on 2026-09-01: matches exactly (the PR branch additionally touches `src/coord/cubed_sphere_utils.hpp` and `gnomonic_equiangle.hpp`, which the file table below predates).

**Problem.** On a cubed sphere, a ghost cell across a panel edge cannot be a copy — the two panels' coordinate lines meet at an angle, so the ghost is *interpolated* from a strip of the neighbouring panel. The interpolation source does not sit opposite the ghost: it slides along the shared edge, by up to $n_{\rm ghost} - 1/2$ cells. When a panel is divided among several MPI blocks, that slide can run past the end of the sending block, into cells the sender owns only as an *intra-panel halo*. Those halo cells have not been refreshed at the moment the strip is packed, so the ghost is built from the previous synchronisation's data.

**Evidence.** Cross-panel ghosts differ between decompositions of the same problem: **144** of 4608 ghost positions between `nb2=1` and `nb2=2`, and **240** between `nb2=2` and `nb2=4` — located *only* at the along-edge indices where the interpolation source crosses a block seam, with every count and every per-layer split predicted in advance from the gnomonic geometry. The stale input is measured directly, not inferred: at pack time **every** in-panel halo copy disagrees with the interior cell it is a copy of (4824/4824 at `nb2=2`, 15768/15768 at `nb2=4`), while before the first exchange all 4824 agree exactly.

**Fix.** Split an interpolating cubed-sphere synchronisation into two rounds — intra-panel, then cross-panel — so the widened strip is packed from a halo that already holds the current state. The dependency belongs to the scheme rather than to this implementation: Chen & Li (2024) already draw a subdivided panel whose cross-panel ghosts are interpolated from a column that includes the sending meshblock's own intra-panel ghost zones. What no description states — because it only bites once the panel is spread across processes — is that those halo cells must be *current* when they are read. After the fix, `nb2 = 1`, `2` and `4` agree **bit for bit** at every Runge–Kutta stage; this commit leaves `nb2=nb3=1` — the production GPU configuration, which has no intra-panel neighbour and so cannot exhibit the defect — bit-identical, and the example battery is unchanged.

**Review banner, added 2026-09-06** (read against snapy `e2e397a`). The mechanism and every code pointer in this report hold at the tip; the following sentences do not. (1) The PROVENANCE’s “The PR branch now carries the whole rebuilt PR series (tip `4b802af`)”: the tip is `e2e397a`, eleven commits later. (2) §6 “seven interpolating synchronisations”: five remain — `4b59cf6` changed both flux-positivity θ exchanges to `interpolate(false)`, so they no longer enter the two-phase branch. (3) §7’s “`gmin + (gmax − gmin)` need not round to `gmax`” should read `gmin + gnx·dx`, as §9 and the commit say. (4) §1’s “higher order is refused outright when a panel is subdivided”: it is refused at every `px` (`gnomonic_equiangle.cpp:165-170`); the older `interp_order == 2 || 4` check at `:25` still admits 4 and is dead for the cubed sphere. (5) The files-changed tables describe the pre-squash commits (`65dca48`, `74ff385`, `0379406`), not the branch commit `40906e0` (+153/−24 over eight files) or `96c8851` (+69/−18 over four). (6) §9’s premise that `SyncOptions` is “bound wholesale”: the binding is field by field, and `intra_panel_only` was not bound until the 2026-09-06 fix series. Also: the comment this report calls “the defect” (“the intra-panel pass above has already filled this block’s own tangential halo”) shipped verbatim at `e2e397a` and is replaced by a one-line pointer to the phase-1 early return in the same series.

## Provenance

This is the last of four defects in one region of code, all found while trying to make a cubed-sphere panel divisible among more than one MPI block. The first three are reported here only as much as is needed to read the fourth:

| commit | defect | consequence |
|----|----|----|
| 8d2ed9b | each block narrowed the interpolation source strip to its own slice with `interp_order/2` = 1 cell of headroom — less than the slide | `nb2=nb3 ≥ 3` aborted at *any* resolution. Fixed by carrying a margin of `nghost` with the data; verified to 384 ranks |
| 01c5931 | each block built its coordinates by `linspace` over its *own* sub-interval | 26 of 71 global faces differed by 1 fp64 ULP across decompositions, and 15 were inconsistent *within* one decomposition. Fixed by slicing one global array |
| 5007644 | `usrc += margin − offset` folded a per-block integer into a double *before* `floor()` | an interpolation weight moved by $3.6\times10^{-15}$. Fixed by shifting the integer index after the floor |
| 65dca48 | **this report** — the margin introduced by `8d2ed9b` is packed from a halo that is not yet filled | ghosts, and therefore the solution, depend on how the panel was divided |

The pattern is worth naming, because three of the four are instances of it: *a quantity that ought to be a property of the sphere is instead computed from something a block happens to own.* A coordinate built per block, an integer folded into a per-block offset, a strip packed from a per-block halo. Each was invisible in a single-block run and each produced a different answer when the same problem was divided differently.

## 1. What a cross-panel ghost is, and why its source slides

The cubed sphere maps six flat panels onto the sphere by gnomonic projection. Within a panel the grid is an ordinary structured mesh in two angular coordinates $(\xi, \eta)$, each spanning $[-\pi/4, \pi/4]$ in $N$ equal steps (Chen & Li 2024, Eq. 16–17). Across a panel edge the two grids do not line up: the coordinate lines of the neighbour cross the edge at an angle. So a ghost cell outside a panel edge cannot be filled by copying a neighbour's cell. It has to be interpolated, which the scheme does with a one-dimensional linear interpolation along the shared great circle (§3.5 of the paper; `interp_order: 2` in the code, and higher order is refused outright when a panel is subdivided).

The essential geometric fact is where the interpolation reads from. It is *not* the position directly opposite the ghost. Take the edge at $\xi = +\pi/4$. A point on the panel has direction $(1, \tan\xi, \tan\eta)$ in that panel's frame (Eq. 18 and 23). The neighbouring panel's frame is the same frame rotated by 90° about the $\eta$ axis, so the identical direction reads $(\tan\xi, -1, \tan\eta)$ there, and the along-edge coordinate the neighbour assigns to it is

$$\eta' = \arctan\!\left(\frac{\tan\eta}{\tan\xi}\right)$$

At the edge itself $\xi = \pi/4$, $\tan\xi = 1$ and $\eta' = \eta$: the grids agree exactly on the seam, as they must. But a ghost cell in layer $g$ sits *outside* the edge, at $\xi = \pi/4 + (g-1/2)\Delta$ with $\Delta = \pi/(2N)$, so $\tan\xi > 1$ and $|\eta'| < |\eta|$. Expanding to first order in $\varepsilon = (g-1/2)\Delta$,

$$\eta' - \eta = -\varepsilon \sin(2\eta) \quad\text{i.e.}\quad \text{slide} = \left(g - \tfrac{1}{2}\right)\sin(2\eta)\ \text{CELLS},$$

always toward $\eta = 0$, the midpoint of the panel edge.

Two properties of this expression matter for everything that follows. It is *resolution independent* — the slide is a number of cells, not an angle, so refining the grid does not reduce it. And it is bounded by $n_{\rm ghost} - 1/2$, attained at the panel corner where $|\sin 2\eta| = 1$. Evaluating the exact expression rather than the expansion, at $N = 64$, $n_{\rm ghost} = 3$, gives a maximum of **2.4955** cells against the bound of 2.5, and agreement with $(g-1/2)\sin(2\eta)$ to better than 0.073 cells everywhere. The approximate form is used below because it is legible; every prediction was checked against the exact one.

[EMBEDDED FIGURE: binary not copied; generating script not recorded in the source HTML]

**Figure 1.** The cross-panel interpolation reads a source displaced along the edge. On an undivided panel every source cell belongs to the sending panel's interior and the displacement is harmless. Divide the panel, and a ghost near a block seam reads across it — into cells the sending block holds only as an intra-panel halo copy.

## 2. What the scheme's description does and does not settle

The slide, and the reading across a block seam, are properties of the geometry rather than accidents of this code — §1 derives them from the gnomonic map alone, so they hold for any implementation of it. The design description goes one step further. Chen & Li (2024) §3.5 gives the interpolation position explicitly (their Eq. 80–84), and the caption of their Figure 5 draws the *subdivided* case:

> Bold pink and green lines indicate meshblock boundaries. Within each panel, four circles bordered in black can be observed: the lower two circles correspond to the top meshblock's intrapanel ghost zones and the upper two to the bottom meshblock's. Values in the open green circles are determined through interpolation from the pink circles column by column from left to right.

So reading a sending meshblock's own intra-panel ghost zones as interpolation source is anticipated, not improvised. That settles the *data dependency*: the interpolation genuinely needs cells that only the neighbouring block owns, and no formulation of the scheme avoids it.

**It settles nothing about the ordering, and it is not a validated reference for this code.** Three qualifications matter, and they are the reason this report leans on measurement rather than on the paper:

- **Different code.** The paper describes the scheme as realised in an earlier code. snapy's cubed sphere is a later, independent implementation by the developer; it shares the mathematics, not the communication layer — and the defect here lives entirely in the communication layer.
- **Subdivided panels were not seriously exercised.** Until this work, `nb2 = nb3 ≥ 3` aborted outright in snapy (defect `8d2ed9b`), which is a fair indication of how much traffic that configuration had seen. A description of a scheme is not evidence that a given decomposition of it has ever been checked.
- **This is the fourth round of seam repair here, not the first.** snapy's cubed sphere has been corrected repeatedly along the panel boundaries — `#80` panel rotation, `#83` corner and flux sync, `#171` spherical velocity frame for the exchange, `#182` seam fixes — each removing a fringe artefact near an edge or a corner. That lineage is the right prior: the region is delicate, previous repairs were real, and none of them was the last one.

The ordering constraint — that the halo must be filled before it is used as interpolation source — is therefore derived and measured here, not quoted. It is the kind of requirement that is invisible in a serial description and unavoidable in a parallel one.

## 3. Instrument: why the obvious test is blind, and the key that makes the right test valid

The natural test — run the same problem at two decompositions and compare the output — is correct in principle and was nearly useless in practice, for three separate reasons, each of which had to be removed before any number here could be believed.

### The output is float32 and the initial condition is degenerate

NetCDF output is single precision, a floor of about $10^{-7}$ relative, which is above the signal for most of the domain and turns a smooth field of differences into an apparently sparse set of "affected cells". Every measurement in this report instead comes from float64 `.npz` dumps taken inside the integrator, one per Runge–Kutta stage, by a probe that wraps `MeshBlock.forward` and needs no rebuild. Separately, the initial condition used for these tests is horizontally uniform, so it compares equal to zero under *any* horizontal permutation of cells: a frame-0 agreement is a necessary check that the two runs started from the same state, and is *not* evidence that a cell mapping is right.

### The interior test cannot see the defect at all at `nb2=1` vs `nb2=2`

The interior comparison, on the mapping-free multiset of all interior cell values, reads exactly zero between `nb2=1` and `nb2=2` at every stage — which is what the project record said for months, and is true. The ghosts are not interior cells. Comparing them is a different measurement, and it is the one that was missing.

### A ghost cannot be keyed by its position on the sphere

The first attempt to compare ghosts keyed each ghost cell by its quantised `(longitude, latitude)`. That key is wrong in a way that is easy to miss: two *different* panels extend their ghost layers across the same edge onto nearly the same physical positions, so the key merges cells that are physically distinct, and it merges a different set of them in each decomposition. It reported 5040 "ghost positions" at `nb2=2` and 5904 at `nb2=4` for the same 4608 physical ones, and 1632 of those positions held copies that disagreed *within a single run* — impossible for one physical cell, and the signature of a colliding key.

The replacement keys a ghost by **(panel id, extended `gj`, extended `gk`)**:

    gj = rint( (x2v + π/4)/Δξ − 1/2 )      the global index in the OWNING panel's index space,
                                            so a cross-panel ghost has gj < 0 or gj ≥ N
    panel id from the block's INTERIOR longitude/latitude only  (unit vector → dominant axis + sign)

The key never mentions the block, so it is layout-invariant by construction, and the script asserts that the index is exact rather than merely nearest (worst deviation $< 10^{-6}$ of a cell) and that all of a block's interior cells agree on the panel. Ghosts are then classified by the block that holds them — `edge` (the in-panel axis lies in this block's own interior: the authoritative copy, and exactly one block per position holds it in *every* layout), `edgehalo` (the other axis is in this block's halo), `corner` (both axes outside the panel) — and never mixed.

Three controls run before any localisation is quoted:

1.  **The `edge` position set must be identical between layouts.** It is: 4608 = 4 sides × 3 layers × 64 × 6 panels, with zero positions unique to either side, in every comparison in this report. The broken tool could not even produce equal counts.
2.  **Within one layout, every `edgehalo` copy is compared against the `edge` copy at the same position** — a physical cell held twice must agree.
3.  **A mapping-free multiset over the whole `edge` set** (sorted values, no key at all). At `init` and after stage 0 the keyed difference and the multiset are both exactly zero; where the keyed difference is non-zero, so is the multiset. Their differing-element *counts* are not comparable — sorting displaces everything after an inserted value — only zero against non-zero is.

## 4. The measurement

Two decomposition pairs, C64 ($N = 64$ cells per panel side, 50 vertical levels), $n_{\rm ghost} = 3$, one cycle, identical initial conditions with the initial-condition kick disabled. The state after RK stage 0 is bit-identical in the interior in both pairs; the ghosts are not:

| | `nb2=1` vs `nb2=2` | `nb2=2` vs `nb2=4` |
|----|----|----|
| differing `edge` ghost positions (of 4608) | 144 | 240 |
| along-edge indices affected | 31, 32 | 14, 15, 48, 49 |
| which seam | 31\|32 — the only `nb2=2` seam | 15\|16 and 47\|48 — the seams unique to `nb2=4` |
| split by ghost layer `g` = 1 / 2 / 3 | 48 / 48 / 48 | 48 / 96 / 96 |
| per panel (of 6) | 24 each | 40 each |
| max \|Δ\| in total energy | $1.2543\times10^{4}$ | $2.1672\times10^{5}$ |
| max relative, horizontal momenta | 0.998 | 1.66 |
| differences appear | at RK stage 1, never at `init` or stage 0 (both exactly zero, on both instruments) | (same) |

The locus is not a hint, it is an identification. Every count above follows from the geometry of §1 with no free parameter. A ghost at along-edge index `j` in layer `g` is corrupted exactly when `floor(j + slide)` lands on the far side of a seam:

    nb2 = 4, seam at 15|16, slide toward the midpoint at 31.5 (so positive for j < 31.5):
      j=15, g=1  slide 0.359  → 15.36  → reads 15,16   CROSSES     j=15 hit at all 3 layers
      j=15, g=3  slide 1.738  → 16.74  → reads 16,17   CROSSES
      j=14, g=1  slide 0.376  → 14.38  → reads 14,15   clean       j=14 hit at layers 2,3 only
      j=14, g=2  slide 1.109  → 15.11  → reads 15,16   CROSSES
      j=16, g=3  slide 1.72   → 17.72  → reads 17,18   clean       the far side is never hit
          ⇒ (3 + 2) layers-worth × 2 seams × 4 edges × 6 panels = 240        observed 240

    nb2 = 2, the only seam is 31|32, which sits AT the midpoint where the slide nearly vanishes:
      j=31, g=1  slide 0.012  → 31.01  → reads 31,32   CROSSES     all 3 layers, both sides
          ⇒ 2 indices × 3 layers × 4 edges × 6 panels           = 144        observed 144

The `nb2=2` versus `nb2=4` comparison does not show indices 31 and 32 because that seam exists in *both* layouts and corrupts them identically — which is exactly why the defect survived so long: the natural A/B between two subdivided runs cancels the part they share.

The asymmetry in the affected indices is also diagnostic. Only the side of the seam *from* which the slide crosses is hit (14, 15 but never 16, 17), because the slide always runs toward the midpoint of the panel edge. A defect in indexing or in the communication relabelling would not respect that; a defect in what the displaced source *reads* must.

### The stale input, measured rather than inferred

`MeshBlockImpl::forward()` calls `exchange_ghost_zones()` first and `advance_local()` second, and the probe dumps after `forward` returns. So the stage-0 dump *is* the state that `serialize()` reads when it packs the synchronisation feeding stage 1 — the pack-time state is already on disk, and no additional run is needed to inspect it. There:

| at pack time, in-panel halo copies vs the interior cell they copy | `nb2=2` | `nb2=4` |
|----|----|----|
| copies checked | 4824 | 15768 |
| copies that disagree | 4824 (all) | 15768 (all) |
| max \|Δ\| total energy / max relative in `m1` | $6.05\times10^{3}$ / 1.0085 | $6.05\times10^{3}$ / 1.0085 |
| same check before the first exchange (`init`) | 0 disagree | 0 disagree |

Two candidate explanations were tested against the data and rejected: the bad ghost is not frozen (it does change between stages) and it is not simply the previous stage's correct value. It is an interpolation whose two source cells were taken from a halo that had not been updated, which is neither. The control that the divergence is created between stage 0 and stage 1 — and not earlier — is that the two layouts' ghosts agree to *exactly* zero in the stage-0 dump.

## 5. Root cause in the code

A synchronisation is three steps: `serialize()` packs send buffers, `launch_exchange()` posts the messages, `deserialize()` unpacks into ghost zones. Both the intra-panel and the cross-panel neighbours are handled inside each of those steps, intra-panel first. The cross-panel branch of `serialize()` widens the strip it packs (`src/layout/cubed_sphere_layout.cpp`):

    // When the receiver will INTERPOLATE, send a tangentially wider strip: its
    // interpolation source slides along the edge (cs_interp_margin) and on a
    // subdivided panel that runs past the matching block. The intra-panel pass
    // above has already filled this block's own tangential halo, so the extra
    // cells are local -- no new connectivity.
    if (opts.interpolate()) {
      int margin = cs_interp_margin(pmb->options->coord()->nghost());
      if (dy != 0 && dx == 0)      part_opts.extend_x2(margin);
      else if (dx != 0 && dy == 0) part_opts.extend_x3(margin);
    }

The comment is the defect. "The intra-panel pass above has already filled this block's own tangential halo" is false: that pass fills *send buffers*. Halo cells are written by `deserialize()`, which runs after the communication — after this pack. So at the moment the widened strip is read, its margin cells still hold whatever the previous synchronisation left there, one stage earlier. The intent was right and the ordering was not available to satisfy it.

[EMBEDDED FIGURE: binary not copied; generating script not recorded in the source HTML]

**Figure 2.** The dependency is a cycle within one round: the cross-panel send payload needs data that only arrives in the intra-panel receive. No ordering inside a single round can satisfy it, so the round is split. At `nb2 = nb3 = 1` there is no intra-panel neighbour, phase 1 packs and sends nothing, and phase 2 is exactly the round that ran before.

## 6. The fix

The split is placed in `MeshBlockImpl::exchange()` rather than at a call site, which is what makes it small: there are seven interpolating synchronisations in the tree — the per-stage ghost exchange, both initialization paths, the `Mesh`-level exchange, and the two flux-positivity `theta` exchanges — and one branch covers all of them.

    // A subdivided cubed-sphere panel packs its cross-panel strip EXTENDED into
    // its own tangential halo (cs_interp_margin), and that halo is only written
    // by deserialize(). So the intra-panel round must COMPLETE before the
    // cross-panel round packs, which one round cannot do. Corners are synthesized
    // from the edge strips, so they come after both.
    auto const &lo = *options->layout();
    if (opts.interpolate() && !opts.intra_panel_only() &&
        !opts.cross_panel_only() && lo.type() == "cubed-sphere" &&
        (lo.px() > 1 || lo.py() > 1)) {
      SyncOptions intra = opts, cross = opts;
      _exchange_once(vars, intra.intra_panel_only(true).interpolate(false));
      _exchange_once(vars, cross.cross_panel_only(true));
      if (opts.skip_corner()) _playout->fill_corners(this, vars);
      return;
    }

    _exchange_once(vars, opts);

The whole change is **one new option**, `intra_panel_only`, the mirror of the `cross_panel_only` flag that already existed; it gates the same two loops from the other side. Three supporting points are load-bearing rather than tidying:

- **The guard requires a genuinely subdivided panel.** An undivided panel has no intra-panel neighbour, so phase 1 would pack and post nothing — but at `blocks_per_process > 1` it would still run the condition-variable rendezvous inside `_prepare_local_exchange`: two barriers per stage for no work, in the common six-blocks-in-one-process `Mesh` configuration. `px` and `py` are independent options (`px = nb2`, `py = nb3`), so the guard tests both rather than leaning on the `px == py` invariant that is enforced elsewhere.
- **Corner synthesis is sequencing, not configuration.** The inter-panel corners are never exchanged (`skip_corner`); they are *synthesized* by averaging the four edge ghost strips, so they are valid only once every strip has landed — the end of the cross-panel phase. `exchange()` therefore calls `fill_corners` once, explicitly, after both phases, and the existing derived condition simply grows to exclude phase 1 as well. An earlier revision expressed this as a `fill_corner` option instead; see §9 for why that was wrong.
- **`exchange_remote()` posts messages only to the current phase's peers.** Required, not cosmetic: `serialize()` leaves the other class's send buffers untouched, so without the filter the intra-panel phase would post cross-panel buffers that do not exist yet on the first call. The predicate is `same_panel`, which is symmetric, so both peers of a pair decide alike and no send is left without a matching receive. It also ends a pre-existing waste, in which a cross-panel-only synchronisation sent the stale intra-panel buffers of an earlier sync — data the receiver has always discarded.

Both exchange-buffer keys and the process-local rendezvous key carry `intra_panel_only`, so the two phases cannot share a buffer cache or a barrier state.

**Cost.** One additional latency per synchronisation on a subdivided panel, and *no* additional message volume — the intra-panel messages were already being sent, in the same round. An undivided panel does not enter the branch at all, so that path is untouched by construction as well as by measurement.

## 7. Validation

Four arms in one job on a single node: the previous build at `nb2=1`, and the new build at `nb2=1`, `2` and `4` (6, 6, 24 and 96 ranks). Each gate is checked on *both* instruments — the mapping-free interior multiset and the keyed ghost comparison with its three controls — at every dump: `init`, and after each of the three RK stages.

| gate | arms | before | after |
|----|----|----|----|
| A | previous build (`5007644`) vs new build (`74ff385`), both `nb2=1` | — | 0 differing interior cells, 0 differing ghost positions |
| B | `nb2=1` vs `nb2=2` | 144 ghost positions | 0 |
| C | `nb2=2` vs `nb2=4` | 240 ghost positions | 0 |

The gates were then re-run against the *delivered* build — a build made from the delivered commit `0379406` rather than from the development commits (re-run after the series was rebuilt for authorship) — and every one is zero again. The squash carries the result rather than inheriting it on trust.

Control 1 passes in every gate (4608 positions, none unique to either side), and the block counts in the dumps confirm the arms are what they claim to be (6/6, 6/24, 24/96) rather than a degenerate comparison of a run against itself. **Cubed-sphere decomposition independence now holds at `nb2` = 1, 2 and 4, in the interior and in the ghosts, at every stage.**

### Which baseline gate A is against — and what the series does to `nb2 = nb3 = 1`

Gate A's "previous build" is `5007644`, the tip of the series before this commit. So gate A establishes that **`65dca48` alone** is bit-neutral at `nb2 = 1` — which is the claim the two-phase design makes, since a block with no intra-panel neighbour packs and posts nothing in phase 1. It does *not* say the four commits together leave `nb2 = nb3 = 1` unchanged relative to production, and they do not:

- `8d2ed9b` is **not** inert at `nb2 = 1`. The movement is confined — every changed cell lies within 1.5 cells of a panel edge, none in the interior — but it is non-zero.
- `01c5931` is not bit-neutral *in general* (`gmin + (gmax − gmin)` need not round to `gmax`), though at `nb = 1` in this C64 configuration it measures exactly zero.

So the honest statement about the production GPU configuration is: it has no intra-panel neighbour, so the defect this report describes cannot occur there, and the last commit does not touch it; the series as a whole does move it, near panel edges, by the amount the crash fix requires. The evidence that the series is sound at `nb2 = nb3 = 1` is the battery below, not gate A.

### Regression battery

The full example battery, with the final build as an overlay (one GPU job, one CPU job): **GPU 25/25 with no failures, CPU 28/30**. The two CPU failures are `23_rce_1d_hotjupiter` (timeout) and `28_rce_1d_bd_dcz` — the same two, with the same never-entered-the-time-loop character (`cyc = 0`), that the project record documents for the production build. Both are one-dimensional radiative-convective cases that exercise no part of this change.

The cases that *do* exercise it are green, and they are the ones to read:

| case | ranks | what it covers | mass drift |
|----|----|----|----|
| `44_hydro_cubedsphere_cpu` | 24 | `nb2=nb3=2` — a *subdivided* panel, so it runs the new two-phase path | 0.000e+00 |
| `12_rt_uranus_cubedsphere_gpu` | 6 | `nb2=nb3=1` — the production GPU path, which does not enter the branch | 0.000e+00 |
| `34`/`35_determinism_bitmatch` | 2 / 1 | run-to-run bit-identity, CPU and GPU | 0.000e+00 |

One caveat on reading the battery as conservation evidence: 17 of the 53 green cases are marked `PASS-NC`, meaning mass drift was not sampled at all. The four rows above are not among them.

## 8. What is deliberately not changed

The same instrument exposed a second irregularity, and it is being left alone on evidence rather than on judgement. `deserialize()` lands the received strip in a region widened to match the sender's, and then applies the velocity transform to the *narrow* ghost region only — deliberately, since the extra cells are interpolation source in the neighbour's frame and are not ghost values in their own right. The consequence is that after the sync those margin cells hold the neighbour panel's frame permanently. They exist only when a panel is subdivided: none at `nb2=1`, 432 at `nb2=2`, 1296 at `nb2=4`.

Whether anything reads them was an open question, and gate B answers it: it compares a layout with *zero* such cells against one with 432, and the two agree bit for bit at every stage. If any stencil read them, that comparison could not be zero. Their disagreement with the authoritative ghost also fell from $2.1672\times10^{5}$ to $7.4506\times10^{-9}$ once the data feeding them was fresh. So the region is unread, and closing it would be a change to a path with no consumer. The finding is recorded rather than repaired; if a future stencil widens to reach those cells, this is where to look.

## 9. Independent review, and what it changed

The series was given to a reviewer with no part in writing it, asked to find what was wrong rather than to agree, and held to the project's standard: only the minimum, necessary and accurate edits; no cosmetics; brief comments. It confirmed the central mechanism — independently deriving that the margin bound `nghost` is exactly $\lceil n_{\rm ghost} - 1/2\rceil$ and therefore tight, that only the midpoint-ward margin is ever read, and that the two phases' communication tags cannot alias — and it found four defects, all now fixed in `74ff385`. The result is **33 fewer lines than the commit it reviewed**.

| finding | what was wrong | fix |
|----|----|----|
| a Python regression | `SyncOptions` is bound wholesale to Python and `cross_panel_only` is exposed, but the new `fill_corner` was not. A Python caller passing `cross_panel_only(true)` silently began synthesizing corners, with no way to stop it | the option is **deleted**. Corner synthesis is internal sequencing, not something a caller configures, so `exchange()` calls `fill_corners` explicitly. As a side effect `hydro_forward.cpp` and `scalar.cpp` need no edit at all |
| two wasted barriers per stage | the two-phase branch fired for any cubed-sphere sync; on an undivided panel phase 1 does no work but still ran the `blocks_per_process > 1` rendezvous — in the common six-blocks-in-one-process configuration | the branch now requires `px > 1 \|\| py > 1` |
| a check that pointed at a broken configuration | `interp_order > 2` was refused only when `px > 1`, naming `px: 1` as the remedy — but the 4th-order stencil evaluates `u0−1`, one cell beyond what the exchange carries, at *every* `px` | refused unconditionally on the cubed sphere |
| a leftover ULP | `block_faces_`'s degenerate branch returned `linspace(gmin + ix·dx, …)`, and `gmin + gnx·dx` need not round to `gmax` — a one-ULP hole in the very defect `01c5931` exists to close, reachable by every 2-D case | the degenerate axis is sliced from the global grid like every other axis |

Two of the reviewer's own conclusions did not survive checking, and are recorded because the checking is the point:

- It proposed guarding the two-phase branch on `px() > 1`. That would skip the split at `nb2=1, nb3=2` and silently reinstate the defect, because `px` and `py` are independent options. (`px == py` is enforced for the cubed sphere, so it is safe today — but a guard should not depend on an invariant checked in another file.)
- It argued that the strip should be extended on the midpoint-ward side only, and that this would remove the need for the corner change entirely, since the wide landing would no longer clobber the corner ghosts. The premise is wrong: corners are never exchanged, so `fill_corners` synthesizes them every sync regardless of clobbering, and it must still run after the cross-panel phase. What remains of the idea is a payload saving — at `nx2 = 32`, `nghost = 3` the extension is about 19 % of the strip, so one-sided halves that to 9 % of one message class. That does not pay for adding an asymmetric `extend` to a shared `PartOptions`, whose risk is real: "midpoint-ward" must be expressed in the *receiver's* index frame, after the `rev`/`flip`/`transpose` relabelling, and getting it backwards is a silent wrong answer rather than a crash. Recorded as a possible optimisation, not taken.

What the review could not cover is stated in §10: it was read-only, so none of the measurements above were independently reproduced, and the `blocks_per_process > 1` path was traced but not exercised.

## 10. Limitations

- **The verified range is `nb2 = nb3 ∈ {1, 2, 4}` at C64.** The crash fix is separately exercised to `nb2 = 8` (384 ranks), but the bit-level decomposition-independence gate has been run at 1, 2 and 4. The mechanism is resolution independent and seam-position driven, so there is no reason to expect a new locus at higher `nb2` — but that is an expectation, not a measurement.
- **One block per MPI rank.** Everything measured here ran with `blocks_per_process = 1`. The multi-block-per-process path takes the same phase filter and the same rendezvous key, and was reasoned through but not exercised.
- **One cycle.** The gates compare three RK stages of one cycle. That is the right scope for a bit-identity claim — a difference that is exactly zero at every stage of a cycle cannot appear later without some other source — but it is not a long-run statement.
- **The review was read-only.** It re-derived the geometry and traced the code, but reproduced none of the measurements; the counts and the gate results are this work's, on one machine.
- **CPU only, gloo backend.** The defect requires an intra-panel neighbour, which the GPU production configuration (`nb2 = nb3 = 1`) does not have; gate A confirms that path is untouched. A subdivided GPU run has not been gated at bit level.

## Files changed

Whole series against the production base: 11 files, +242 / −44, adding **one** option to `SyncOptions`. The two-phase work itself (`65dca48` as revised by `74ff385`) is 7 files, +87 / −31:

| file | lines | what |
|----|----|----|
| `src/mesh/meshblock.cpp` | +21 | the two-phase branch in `exchange()`, the explicit `fill_corners` call, and `_exchange_once()` holding the old body |
| `src/mesh/meshblock.hpp` | +4 | declare `_exchange_once` (private) |
| `src/layout/layout.hpp` | +3 | `intra_panel_only` |
| `src/layout/layout.cpp` | +21 / −9 | both keys carry the new flag; corner condition excludes phase 1; phase filter on the process-local path |
| `src/layout/cubed_sphere_layout.cpp` | +23 / −2 | phase guards in `serialize`/`deserialize`; peer filter in `exchange_remote`; buffer key |
| `src/coord/gnomonic_equiangle.cpp` | +10 / −18 | `interp_order > 2` refused unconditionally; comment trimmed of measured values |
| `src/coord/coordinate.cpp` | +5 / −2 | degenerate axis sliced from the global grid |

The commit messages carry the reasoning and the measurements; the source carries the ordering constraint at the two places where violating it is invisible, and nothing else.

**Delivery.** The five development commits are squashed into one on the PR branch (`0379406`), which is now a linear series of self-contained, PR-ready fixes on the pin rather than a stack of merge commits. The regenerated tree was verified bit-identical to the development tip `74ff385` — the tree these gates were run on — before the cutover, so the evidence in this report applies to the delivered code unchanged. The development history is retained under an archive tag; the coordinate fix ships as its own commit (`68e4129`) because it is not cubed-sphere specific and stands alone upstream.

All measurements were taken on one machine and software stack (CPU nodes, gloo; snapy `65dca48` against `5007644`, kintera `8424748`, production venv pin snapy `2.10.5+g43e04fd` untouched throughout). The three gates and the battery reported above were run on the final build; earlier gate and battery runs measured the pre-review build `65dca48` and are superseded. Reference: S. Chen and C. Li, *ExoCubed: A Riemann-solver-based Cubed-sphere Dynamic Core for Planetary Atmospheres*, ApJ **966**:123 (2024), §3.5 and Figure 5 — cited for the scheme and its geometry, which snapy re-implements independently; it is not a reference implementation for this code and carries no validation of it at a subdivided panel (§2).
