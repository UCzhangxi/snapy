#!/usr/bin/env python3
"""One-off: merge the five research inventories and the chapter 6 entries into OUTLINE.md
in the final chapter structure. Prints a completeness report (the four required items)."""
import os
import re
import sys

OUT = "/home/user/snapy/doc/tech-report/outline"
SCR = os.path.dirname(os.path.abspath(__file__))
FILES = {
    "A": os.path.join(OUT, "inventory_A_ch01_03_14.md"),
    "B": os.path.join(OUT, "inventory_B_ch02_09_10.md"),
    "C": os.path.join(OUT, "inventory_C_ch04_05.md"),
    "D": os.path.join(OUT, "inventory_D_ch07_08_11.md"),
    "E": os.path.join(OUT, "inventory_E_ch12_13_15.md"),
    "F": os.path.join(SCR, "ch06.md"),
}


def blocks(path):
    text = open(path).read()
    out, cur, head = [], [], None
    for line in text.splitlines():
        if line.startswith("### ") or line.startswith("## ") or line.strip() == "---":
            if head is not None:
                out.append((head, "\n".join(cur).strip("\n")))
            head, cur = (line[4:].strip(), []) if line.startswith("### ") else (None, [])
            continue
        if head is not None:
            cur.append(line)
    if head is not None:
        out.append((head, "\n".join(cur).strip("\n")))
    return out


def intros(path):
    """chapter intro paragraphs: text after '## Chapter' up to the first '###'"""
    text = open(path).read()
    res = {}
    for m in re.finditer(r"^## (Chapter \d+[^\n]*)\n(.*?)(?=^### |\Z)", text, re.S | re.M):
        res[m.group(1)] = m.group(2).strip()
    return res


BLK = {k: blocks(v) for k, v in FILES.items()}
INTRO = {k: intros(v) for k, v in FILES.items() if k != "F"}
USED = set()


def take(key, pat):
    hits = [(h, b) for h, b in BLK[key] if re.search(pat, h)]
    if len(hits) != 1:
        sys.exit(f"pattern {key}:{pat!r} matched {len(hits)}: {[h for h, _ in hits]}")
    USED.add((key, hits[0][0]))
    return hits[0]


# final structure: chapter -> (title, intro, [(part title or None, [(key, pattern), ...])])
S = []


def ch(num, title, intro, parts, src_intro=None):
    S.append((num, title, intro, parts, src_intro))


ch(1, "Overview and code map",
   "How one step runs from the driver to the kernels; CPU/GPU dispatch; tensor layout; options, YAML and the Python "
   "package; what lives outside snapy. Kept as a code map with a step-flow figure. The environment-switch table moves to "
   "Appendix D (cited by every physics chapter). The redo details are owned by 7.A; this chapter points to them.",
   [(None, [("A", r"^Scheme 1\.%d:" % i) for i in range(1, 14)])], ("A", "Chapter 1"))
ch(2, "Governing equations and thermodynamics",
   "The conservation laws snapy integrates and the order of operators in a stage; the equation-of-state interface and "
   "its types (ideal gas, ideal-moist, kintera moist mixture, ANEOS stubs, shallow water); the consistency conditions "
   "between the EOS and the solver; the thermodynamic side of saturation adjustment. The floors are owned by chapter 8 "
   "(the EOS limiter entry there merges the two inventories' views). H2 dissociation is not in kintera at the pin and is "
   "not claimed (ISSUES.md item 4).",
   [(None, [("B", r"^Scheme: Conservation laws"), ("B", r"^Scheme: EquationOfState interface"),
            ("B", r"^Scheme: Ideal gas EOS"), ("B", r"^Scheme: Ideal-moist EOS"), ("B", r"^Scheme: Moist-mixture EOS"),
            ("B", r"^Scheme: ANEOS"), ("B", r"^Scheme: Shallow-water EOS"),
            ("B", r"^Scheme: EOS ↔ solver consistency"), ("B", r"^Scheme: Saturation adjustment \(kintera")])],
   ("B", "Chapter 2"))
ch(3, "Grids and geometry",
   "Coordinate systems and their metric (Cartesian, spherical-polar, gnomonic cubed sphere), the curved-grid helpers, "
   "how the global grid is cut into blocks, and what a ghost cell contains at each seam type. The transport of ghosts "
   "(buffers, tags, backends) is chapter 14.A; only what the ghost values are is here.",
   [(None, [("A", r"^Scheme 3\.%d:" % i) for i in range(1, 16)])], ("A", "Chapter 3"))
ch(4, "Spatial discretization",
   "Split in two because the second half shares one derivation thread. 4.A: the finite-volume stage operator, the "
   "reconstructions, the Riemann solvers, seam-flux averaging and the geometric sources. 4.B: the $O(\\Delta x_1^2)$ "
   "face-average corrections, the $x_2/x_3$ flux covariance and centroid terms (`SNAP_FLUX_COVARIANCE`) and the $x_1$ "
   "mass-flux covariance (`SNAP_X1_MASS_COVARIANCE`).",
   [("4.A Reconstruction, Riemann solvers, divergence and sources",
     [("C", r"^Scheme: Finite-volume update"), ("C", r"^Scheme: Reconstruction framework"),
      ("C", r"^Scheme: Donor cell"), ("C", r"^Scheme: PLM"), ("C", r"^Scheme: Linear centred"),
      ("C", r"^Scheme: WENO3"), ("C", r"^Scheme: PPM"), ("C", r"^Scheme: Riemann solver framework"),
      ("C", r"^Scheme: LMARS"), ("C", r"^Scheme: HLLC"), ("C", r"^Scheme: Roe"), ("C", r"^Scheme: Shallow-water Roe"),
      ("C", r"^Scheme: Single-valued x1 seam"), ("C", r"^Scheme: Geometric \(curvature\)"),
      ("C", r"^Scheme: Geometric sources, gnomonic")]),
    ("4.B Face-average corrections at $O(\\Delta x_1^2)$",
     [("C", r"^Scheme: x2/x3 face-flux covariance"), ("C", r"^Scheme: x1 rho-w mass-flux")])],
   ("C", "Chapter 4"))
ch(5, "Hydrostatic and well-balanced treatment",
   "The well-balanced $x_1$ reconstruction about a hydrostatic reference, its kernel, the wall clamp and continuation, "
   "seam continuity, the hydrostatic-split mode, `balance_column`, the fourth-order reference (`SNAP_WB_REF4`), the "
   "$r^2$-exact $x_1$ maps (`SNAP_X1_CENTROID_EXACT`) and what is left of the $1/R$ term. No separate $1/R$ chapter: the "
   "remainder is the last section here, with its table rebuilt from an in-snapy run (ISSUES.md item 5). The WB-reference "
   "numbers are re-measured with `tests/test_wb_ref4_order.py` at the pin (ISSUES.md item 3).",
   [(None, [("C", r"^Scheme: Well-balanced x1 reconstruction"), ("C", r"^Scheme: Hydrostatic reference kernel"),
            ("C", r"^Scheme: Wall clamp"), ("C", r"^Scheme: Reference continuity"), ("C", r"^Scheme: Hydrostatic mode"),
            ("C", r"^Scheme: balance_column"), ("C", r"^Scheme: SNAP_WB_REF4"), ("C", r"^Scheme: SNAP_X1_CENTROID_EXACT"),
            ("C", r"^Scheme: The 1/R remainder"), ("C", r"^Scheme \(legacy box\)")])],
   ("C", "Chapter 5"))
ch(6, "Gravity and energy",
   "How gravity's work enters the energy equation and what each form conserves: the cell form with the constant-gravity "
   "forcing, the face form (with `face-wallc` and the cp3/cp5/weno5 curvature flux), the gravity-work fixer, the "
   "corrected-PE face work D (the worked example, written in full), the gravity work inside the implicit operator, and a "
   "closing table of invariants and oracles. Written by the editor from the code at dae902b and the gravity-work "
   "sources; the constant-gravity forcing entry of the chapter 2/9/10 inventory is folded into 6.1.",
   [(None, [("F", r"^Scheme: Constant gravity forcing and the cell form"), ("F", r"^Scheme: Face form"),
            ("F", r"^Scheme: Gravity-work fixer"), ("F", r"^Scheme: The corrected-PE"),
            ("F", r"^Scheme: Gravity work inside"), ("F", r"^Scheme: What each form")])], None)
ch(7, "Time integration",
   "Split in two. 7.A: the explicit SSP-RK stages (the integrator is pyharp's `harp::Integrator`, cited at its own sha), "
   "the placement of the ghost exchange, the time step, step acceptance and redo, and the operator-split pieces at the "
   "step boundary. 7.B: the vertical implicit correction (VIC): activation, assembly, the stage-weighted implicit step, "
   "the block-tridiagonal solve, the LU pivot tolerance, rejection, redistribution, and its column closure. The "
   "radiative time-step limiter is not in snapy and moves to Appendix E.",
   [("7.A Explicit stages, time step and step acceptance",
     [("D", r"^Scheme: Explicit SSP"), ("D", r"^Scheme: Ghost-exchange placement"), ("D", r"^Scheme: CFL time step"),
      ("D", r"^Scheme: Step acceptance"), ("D", r"^Scheme: Operator-split pieces")]),
    ("7.B The vertical implicit correction (VIC)",
     [("D", r"^Scheme: VIC activation"), ("D", r"^Scheme: VIC block-tridiagonal assembly"),
      ("D", r"^Scheme: Stage-weighted implicit"), ("D", r"^Scheme: Block-tridiagonal forward sweep"),
      ("D", r"^Scheme: LU pivot"), ("D", r"^Scheme: VIC solve rejection"), ("D", r"^Scheme: VIC constituent"),
      ("D", r"^Scheme: VIC column closure")])],
   ("D", "Chapter 7"))
ch(8, "Positivity, floors and limiters",
   "The tracer flux positivity limiter and the carry of energy and momentum with withheld species mass, the passive-"
   "scalar limiter, the EOS limiters and floors, the reconstruction and well-balanced face floors, the dry-channel "
   "positivity inside the VIC, round-off thresholds and the redo detector. Two pairs of entries came from two inventories "
   "and overlap (the carry; the EOS floors); the chapter author merges each pair into one section.",
   [(None, [("D", r"^Scheme: Tracer flux positivity"), ("D", r"^Scheme: Carry of energy"),
            ("B", r"^Scheme: Positivity-limited species fluxes carry"), ("D", r"^Scheme: Passive-scalar limiter"),
            ("D", r"^Scheme: Conserved-variable EOS limiter"), ("B", r"^Scheme: Conserved/primitive limiter"),
            ("D", r"^Scheme: Primitive-variable EOS limiter"), ("D", r"^Scheme: Reconstruction-stage floors"),
            ("D", r"^Scheme: Well-balanced face positivity"), ("D", r"^Scheme: Dry channel positivity"),
            ("D", r"^Scheme: Round-off thresholds"), ("D", r"^Scheme: Fresh-primitive"), ("D", r"^Scheme: Dry-carry")])],
   ("D", "Chapter 8"))
ch(9, "Diffusion, viscosity and forcing",
   "The forcing framework and every forcing module: user stage forcings, Coriolis, isotropic viscosity and conduction "
   "with the face coefficient (walls, $x_1$ profiles, mean of products), heating and cooling, bottom relaxation, sponges. "
   "Sedimentation moves to chapter 10 (it is moist physics). The constant-gravity forcing is chapter 6.1. Two entries "
   "record dead code (plume forcing, the unbuilt turbulence directory) and get one paragraph each.",
   [(None, [("B", r"^Scheme: Forcing framework"), ("B", r"^Scheme: User stage forcings"), ("B", r"^Scheme: Coriolis"),
            ("B", r"^Scheme: Isotropic viscosity"), ("B", r"^Scheme: Diffusion face coefficient at walls"),
            ("B", r"^Scheme: x1 profiles of the kinematic"), ("B", r"^Scheme: Body heating"),
            ("B", r"^Scheme: Bottom relaxation"), ("B", r"^Scheme: Sponge layers"), ("B", r"^Scheme: Plume forcing"),
            ("B", r"^Scheme: Turbulence")])],
   ("B", "Chapter 9"))
ch(10, "Moist physics coupling",
   "Saturation adjustment in the step, the redo causes that moist physics raises, the condensate and vapour repairs "
   "(two inventories describe `fix_vapor`; the author merges them), the precipitation and evaporation kinetics (a driver-"
   "level coupling: it lives in the example driver, which the chapter says plainly), tracer transport per dry air, and "
   "the sedimentation of condensates (moved here from chapter 9).",
   [(None, [("B", r"^Scheme: Saturation adjustment in the step"), ("B", r"^Scheme: check_redo"),
            ("B", r"^Scheme: Condensate repair"), ("B", r"^Scheme: Column vapour repair"),
            ("D", r"^Scheme: Column vapor and cloud repair"), ("B", r"^Scheme: Precipitation and evaporation"),
            ("B", r"^Scheme: Passive scalar \(tracer\)"), ("B", r"^Scheme: Sedimentation of condensates")])],
   ("B", "Chapter 10"))
ch(11, "Boundary conditions and immersed solids",
   "The boundary-function registry and every boundary type, when ghosts are filled, the pointer to exchange-filled "
   "ghosts (chapter 3 and 14), immersed solids (own section), and the interaction of the boundaries with the well-"
   "balanced reference. The VIC's column closure moved to 7.B.",
   [(None, [("D", r"^Scheme: Boundary-function registry"), ("D", r"^Scheme: Reflecting wall"), ("D", r"^Scheme: Periodic"),
            ("D", r"^Scheme: Extrapolation"), ("D", r"^Scheme: Outflow"), ("D", r"^Scheme: Custom \(no-op\)"),
            ("D", r"^Scheme: When ghosts are filled"), ("D", r"^Scheme: Exchange-filled ghosts"),
            ("D", r"^Scheme: Immersed solids"), ("D", r"^Scheme: Boundary conditions and the well-balanced")])],
   ("D", "Chapter 11"))
ch(12, "Build-time and run-time switches and configurations",
   "Every switch that changes what snapy compiles or computes: 12.1 build time, 12.2 environment (the five `SNAP_*` "
   "scheme switches), 12.3 YAML scheme keys, 12.4 the coverage matrix (switch combination → ctest entries). The scheme "
   "switches are process-global and read once; their couplings are real constraints, so they get this chapter rather than "
   "being scattered over chapters 4-6 (each physics section still states its own switch in its Summary layer).",
   [("12.1 Build time", [("E", r"^Scheme: CMake options"), ("E", r"^Scheme: `configure.h`")]),
    ("12.2 Environment", [("E", r"^Scheme: environment helper"), ("E", r"^Scheme: `SNAP_WB_REF4`"),
                          ("E", r"^Scheme: `SNAP_X1_CENTROID_EXACT`"), ("E", r"^Scheme: `SNAP_FLUX_COVARIANCE`"),
                          ("E", r"^Scheme: `SNAP_X1_MASS_COVARIANCE`"), ("E", r"^Scheme: `SNAP_GRAVITY_WORK_RADIAL_EXACT`"),
                          ("E", r"^Scheme: runtime environment"), ("E", r"^Scheme: test-harness")]),
    ("12.3 YAML scheme keys", [("E", r"^Scheme: YAML scheme keys")]),
    ("12.4 Coverage matrix", [("E", r"^Coverage matrix")])],
   ("E", "Chapter 12"))
ch(13, "Conservation budgets and diagnostics",
   "What the cycle line logs and what each term means (the logged potential energy is $P$ under D), the positivity and "
   "VIC-clamp meters, the gravity-work fixer budget, redo causes and termination status as diagnostics, the output-field "
   "diagnostics, and the mass-conservation regression checks. `src/diagnostics/` is legacy code that is not compiled and "
   "is not described.",
   [(None, [("E", r"^Scheme: cycle-line budget"), ("E", r"^Scheme: positivity-limiter meters"),
            ("E", r"^Scheme: VIC clamp meter"), ("E", r"^Scheme: gravity-work fixer E\+PE budget"),
            ("E", r"^Scheme: redo causes and termination"), ("E", r"^Scheme: output-field"),
            ("E", r"^Scheme: mass-conservation")])],
   ("E", "Chapter 13"))
ch(14, "Parallelism, GPU, restart/IO and reproducibility",
   "Split in three: 14.A parallel execution and GPU (launch, backends, message matching, several blocks per process, "
   "collectives, GPU execution); 14.B output and restart (NetCDF, PnetCDF, restart files, scheduling, post-processing "
   "tools); 14.C reproducibility, the inventory of what is shown bit for bit and what is not.",
   [("14.A Parallel execution and GPU", [("A", r"^Scheme 14\.%d:" % i) for i in range(1, 7)]),
    ("14.B Output and restart", [("A", r"^Scheme 14\.%d:" % i) for i in (7, 8, 9, 10, 12)]),
    ("14.C Reproducibility", [("A", r"^Scheme 14\.11:")])],
   ("A", "Chapter 14"))
ch(15, "Verification catalogue",
   "The human-readable index of every ctest entry at the pin, grouped by the chapter that owns the topic, with what each "
   "asserts and its tolerance; the examples used as regression. Appendix C (the machine index) is generated from "
   "`ctest -N` at the pin so the two cannot drift; 12.4 is the same tests indexed by switch combination.",
   [(None, [("E", r"^Scheme: registration mechanics")] + [("E", r"^Scheme: Ch\.%d " % i) for i in range(2, 15)]
     + [("E", r"^Scheme: examples used as regression")])],
   ("E", "Chapter 15"))

# ---------------------------------------------------------------------------------------------
FIELDS = ("Summary", "Derivations", "Figures", "Code", "Tests")
EXEMPT_CH = {12: ("runtime environment", "test-harness", "YAML scheme keys", "Coverage matrix",
                  "CMake options", "configure.h"), 15: ("",)}


def has_field(body, f):
    return re.search(r"^- (\*\*)?%s" % f, body, re.M) is not None


report, toc, body_out, deriv_rows = [], [], [], []
for num, title, intro, parts, src in S:
    toc.append(f"{num}. [{title}](#ch{num})")
    body_out.append(f'\n---\n\n<a id="ch{num}"></a>\n## Chapter {num}. {title}\n\n{intro}\n')
    if src:
        key, name = src
        note = [v for k, v in INTRO[key].items() if k.startswith(name + ":")]
        if note:
            body_out.append("<details><summary>Research note from the inventory (scope, recommendations)</summary>\n\n"
                            + note[0] + "\n\n</details>\n")
    sec = 0
    for ptitle, items in parts:
        if ptitle:
            body_out.append(f"\n### {ptitle}\n")
        for key, pat in items:
            head, body = take(key, pat)
            sec += 1
            name = re.sub(r"^Scheme( \d+\.\d+)?( \(legacy box\))?:\s*", "", head)
            if head.startswith("Scheme (legacy box)"):
                name = "(legacy box) " + name
            sid = f"{num}.{sec}"
            toc.append(f"   - {sid} {name}")
            body_out.append(f"\n#### {sid} {name}\n<sub>inventory {key}: {head}</sub>\n\n{body}\n")
            exempt = any(s in head for s in EXEMPT_CH.get(num, ())) if num in EXEMPT_CH else False
            missing = [f for f in FIELDS if not has_field(body, f)]
            if missing and not exempt:
                report.append(f"{sid} {name}: missing {missing}")
            # derivation index rows
            m = re.search(r"^- (\*\*)?Derivations(\*\*)?:(.*?)(?=^- (\*\*)?[A-Z][a-z]+|\Z)", body, re.S | re.M)
            if m:
                d = m.group(3)
                n_ex = len(re.findall(r"exists", d))
                n_re = len(re.findall(r"re-derive", d))
                n_none = 1 if re.search(r"\bnone\b", d[:80], re.I) else 0
                deriv_rows.append((sid, name, n_ex, n_re, n_none))

unused = [(k, h) for k in BLK for h, _ in BLK[k] if (k, h) not in USED]
print("UNUSED blocks:")
for u in unused:
    print("  ", u)
print("MISSING FIELDS:")
for r in report:
    print("  ", r)
open(os.path.join(SCR, "_body.md"), "w").write("\n".join(body_out))
open(os.path.join(SCR, "_toc.md"), "w").write("\n".join(toc))
with open(os.path.join(SCR, "_deriv.tsv"), "w") as f:
    for row in deriv_rows:
        f.write("\t".join(map(str, row)) + "\n")
print(len(deriv_rows), "schemes with a Derivations item;",
      sum(r[3] > 0 for r in deriv_rows), "need at least one re-derivation;",
      sum(r[2] > 0 for r in deriv_rows), "have at least one existing derivation")

# ---------------------------------------------------------------------------------------------
def blk(key, pat):
    h, b = take(key, pat)
    return h, b


_, b_cg = blk("B", r"^Scheme: Constant gravity forcing \(source")
_, a_env = blk("A", r"^Scheme 1\.14:")
_, d_rt = blk("D", r"^Scheme \(not in snapy\)")
_, d_notes = blk("D", r"^Cross-chapter notes")
body = open(os.path.join(SCR, "_body.md")).read()
anchor = "\n#### 6.2 "
i = body.index(anchor)
body = body[:i] + ("\n**Folded in from inventory B (\"Constant gravity forcing (source terms only)\"):**\n\n"
                   + b_cg + "\n") + body[i:]
b_cross = open(FILES["B"]).read().split("## Cross-cutting discrepancy list (code wins)")[1].strip()

deriv = [l.split("\t") for l in open(os.path.join(SCR, "_deriv.tsv")).read().splitlines()]
n_s = len(deriv)
n_re = sum(int(r[3]) > 0 for r in deriv)
n_ex = sum(int(r[2]) > 0 for r in deriv)
n_none = sum(int(r[2]) == 0 and int(r[3]) == 0 for r in deriv)
per_ch = {}
for sid, name, ex, re_, no in deriv:
    c = int(sid.split(".")[0])
    a = per_ch.setdefault(c, [0, 0, 0, 0])
    a[0] += 1
    a[1] += int(ex) > 0
    a[2] += int(re_) > 0
    a[3] += int(ex) == 0 and int(re_) == 0
glance = ["| ch | title | schemes | with an existing derivation | needing a re-derivation | neither marked (control flow or table; see entry) |",
          "|---|---|---|---|---|---|"]
for num, title, *_ in S:
    a = per_ch.get(num, [0, 0, 0, 0])
    glance.append(f"| {num} | {title} | {a[0]} | {a[1]} | {a[2]} | {a[3]} |")
glance.append(f"| | **total** | **{n_s}** | **{n_ex}** | **{n_re}** | **{n_none}** |")
idx = ["| section | scheme | exists | re-derive |", "|---|---|---|---|"]
for sid, name, ex, re_, no in deriv:
    idx.append(f"| {sid} | {name} | {ex} | {re_} |")

FRONT = f"""# snapy Technical Report: outline (round 1)

> Editor: C0. Status: **for review by the lead, then approval by the project owner before drafting starts.**
> Pinned code: snapy `dae902b` (`next/final-batch` on UCzhangxi/snapy = snapy main `aea71ed` plus the gravity-work
> round); kintera `4dc613d` and pyharp `4721715` for code outside snapy. Every `path:line@sha` below was checked with
> `build/check_citations.py` (file and lines exist at the sha); the inventories behind it were checked by hand against
> the statement each line carries. Binding style: `STYLE.md`. Symbols: `NOTATION.md`.

## How to read this outline

- **Chapter by chapter, then scheme by scheme.** Each scheme entry (`#### N.M`) carries the four items the brief asks
  for, under the bullet names used in the research inventories:
  - **Summary** (one line, with the switch, how it is set, and its default);
  - **Derivations**, each marked `exists: <source>` (a real, step-by-step derivation is in `sources/` or
    `docs/derivations/` at the pin) or `re-derive from <path:line@sha>` (no derivation exists: commit message only,
    result only, or nothing). A PR body that states a result is **not** counted as a derivation;
  - **Figures**, one line each (every figure is a committed script; STYLE.md section 6);
  - **Code** (`path:line@sha`, with function names) and **Tests** (file, ctest name, what it asserts, tolerance).

  Most entries also carry **Limits / known issues** and **Discrepancies** (source vs code; the code wins).
- Each scheme becomes one section file `chapters/NN-slug/<scheme>.md` written in the six layers of STYLE.md, modelled
  on the worked example `chapters/06-gravity-energy/D_face_work_pe.md`.
- The small line `inventory X: ...` under each heading names the research inventory entry it came from (kept in this
  branch's history at the commit that added this outline), so a reviewer can trace it.
- "Research note" boxes keep the inventory's own scope paragraph and recommendations for that chapter.

## Changes to the proposed chapter list, and why

1. **Ch. 4 split into 4.A and 4.B.** The covariance and centroid corrections share one derivation thread (the in-cell
   product expansion) that the reconstruction and Riemann material does not need.
2. **Ch. 6 written by the editor**, with the worked example D. The constant-gravity forcing moved here from Ch. 9
   (the cell work is the default gravity work).
3. **Ch. 7 split into 7.A (explicit stages, time step, redo) and 7.B (the VIC).** The VIC column closure moved here
   from Ch. 11. The RK integrator is pyharp's and is cited there.
4. **Sedimentation moved from Ch. 9 to Ch. 10** (moist physics), with the species repairs.
5. **Ch. 11 renamed "Boundary conditions and immersed solids"**; exchange-filled ghosts are a pointer to Ch. 3/14.
6. **Ch. 14 split into 14.A parallel and GPU, 14.B output and restart, 14.C reproducibility.**
7. **No separate 1/R chapter**: the remainder is the last section of Ch. 5.
8. **Out of snapy, to Appendix E**: the radiative time-step limiter (external runner), the kinetics coupling (example
   driver), GPU chemistry; the integrator (pyharp). Dead code (turbulence, plume forcing, ANEOS stubs, cylindrical
   coordinates, `src/diagnostics/`) gets one paragraph each, not a section.

## Outline at a glance

{chr(10).join(glance)}

"re-derive" is counted per scheme: a scheme with any derivation marked re-derive counts once. The full list is
Appendix B.

## Chapters

{open(os.path.join(SCR, "_toc.md")).read()}
16. [Known limits](#ch16)
17. [Appendices](#ch17)

## Assignment proposal for the four chapter authors (for the lead to decide)

| author | chapters | why together |
|---|---|---|
| C1 | 1, 3, 14 | code map, geometry and decomposition, parallel/IO: one researcher already mapped all three |
| C2 | 2, 9, 10 | thermodynamics, forcing and moist coupling share kintera and the species machinery |
| C3 | 4, 5 | reconstruction, covariance and well-balanced reference: one derivation thread |
| C4 | 7, 8, 11 | time integration, positivity and boundaries share the VIC and the redo machinery |
| C0 (editor) | 6, 12, 13, 15, 16, 17 | gravity/energy (model chapter), and the cross-cutting chapters that must agree with every other |
"""

CH16 = f"""
---

<a id="ch16"></a>
## Chapter 16. Known limits

Assembled at the end from the Limits layer of every section, grouped by severity, each with its evidence. The
cross-cutting items the research found, to be confirmed by the chapter authors:

1. **The VIC always closes a column as a reflecting wall**, whatever the $x_1$ boundary type; outflow or periodic $x_1$
   with the VIC is accepted silently (7.B, inventory D).
2. **Ghost-exchange order differs between `MeshBlock::forward` (exchange, then advance) and `Mesh::forward` (advance,
   then exchange)**; a Mesh-API driver that applies operator-split sources between stages reconstructs from stale
   ghosts (inferred from code, not measured; 1.5, 1.6, 7.2).
3. **No test covers `SNAP_X1_MASS_COVARIANCE`**, and its onset numbers are a placeholder (4.B, 12.4).
4. **Switch combinations not covered**: `SNAP_X1_CENTROID_EXACT` with face work or with flux covariance; `SNAP_WB_REF4`
   and `SNAP_X1_CENTROID_EXACT` on the cubed sphere; flux covariance across ranks; D with any of the other four
   switches (12.4).
5. **Reproducibility**: restart is shown bit for bit only with the same decomposition, float32 NetCDF, within one
   process; the fixer's global sum is decomposition-dependent at round-off (14.C).
6. **Open issues still in the code at the pin**: a resumed run rewrites its last outputs and its source restart file
   (chengcli/snapy#277); the adiabatic-rest drift of issue #252 after `on_theta` conduction was removed; `kappa_iso`
   diffuses temperature at $\\kappa/\\gamma$ at uniform pressure (issue #261). (Issue numbers as cited in
   `sources/gh__ISSUE_THREADS_*.md`; repository to be confirmed as chengcli/snapy.)
7. **Option defaults differ between the C++ structs and YAML** (EOS floors, reconstruction `shock`, Riemann solver
   type); `max_redo` cannot be set from YAML (Ch. 12).
8. **CI**: no CUDA arm runs in CI; the macOS exclude list names tests that do not exist (Ch. 15).

### Editor's notes carried from the inventories

**From inventory D (chapters 7, 8, 11):**

{d_notes}

**From inventory B (chapters 2, 9, 10), cross-cutting discrepancies (code wins):**

{b_cross}

---

<a id="ch17"></a>
## Chapter 17. Appendices

### Appendix A. Notation
`NOTATION.md`, rendered as a table.

### Appendix B. Derivation index
One row per scheme: the number of derivations marked `exists` and `re-derive` in its entry. Every derivation, existing
or re-derived, gets an executable check next to it (STYLE.md section 7); this table becomes the check index as sections
are written.

{chr(10).join(idx)}

### Appendix C. Test index
Generated from `ctest -N` at the pinned sha by a script in `build/` (planned), so it cannot drift from Ch. 15.

### Appendix D. Environment-variable switches
Folded in from inventory A (1.14); Ch. 12.2 is the full treatment.

{a_env}

### Appendix E. Components outside snapy
- The time integrator: pyharp `harp::Integrator` (`pyharp:src/integrator/integrator.cpp:49-60@4721715` for rk3).
- The kinetics coupling and precipitation: in the example driver `examples/run_hydro.cpp` (10.6).
- The radiative time-step limiter, folded in from inventory D:

{d_rt}
"""
with open(os.path.join(OUT, "..", "OUTLINE.md"), "w") as f:
    f.write(FRONT + body + CH16)
print("wrote OUTLINE.md")
