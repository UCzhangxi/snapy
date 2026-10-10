# Style guide for the snapy Technical Report

This file is binding for every chapter author. The worked example that applies all of it is
`chapters/06-gravity-energy/D_face_work_pe.md`; when this file and the example disagree, this file wins and the
example is a bug to report.

Contents: 1 Scope and voice, 2 the six-layer scheme template, 3 citations, 4 numbers and evidence, 5 equations and
notation, 6 figures, 7 executable checks, 8 directory layout, 9 review checklist.

---

## 1. Scope and voice

- Describe snapy only: its equations, its discretization, its code, its tests. No other model's code, no cross-code
  comparisons, no machine names, cluster paths, user names or personal paths.
- Write for a reader who knows finite-volume methods and wants to learn snapy well enough to change it. Every
  statement is either derived on the page, cited to code at the pinned sha, or cited to a test with its tolerance.
- Plain, direct prose. Present tense for what the code does ("the solver books the work"), past tense only for
  history ("#296 moved the term into the operator"). No "it can be shown", "obviously", "trivially", "it is easy to
  see". If a step is short, write it; if it is long, write it anyway.
- Name a scheme by what it does first and by its switch second: "the corrected-PE face work
  (`SNAP_GRAVITY_WORK_RADIAL_EXACT`)". Project-internal labels (leg D, option F, #NNN) are given once, in the
  Summary layer, as aliases, so a reader can match them to commit messages and the derivation notes.
- Units: SI unless the section states the nondimensionalisation. Give units of every dimensional symbol on first
  use in a section.
- Markdown with LaTeX math (`$...$` inline, `$$...$$` display). One sentence per line is not required; wrap at
  about 120 characters.

## 2. The six-layer scheme template

Every scheme is one section (one file, `chapters/NN-slug/<scheme>.md`) with exactly these six numbered layers, in this
order, with these headings. Do not merge, reorder or rename them. A layer with nothing to say says so in one line
and why ("No known limits beyond those of the base scheme in §5.2.").

```markdown
# <N.M> <Scheme name, what it does> (`<SWITCH>` or YAML key)

> Pinned sha: <repo>@<sha> (<branch>). Derivation sources: <files>. Status: draft | reviewed | approved.

## 1. Summary
- What it does, in two to four sentences.
- Why it is there: the error or failure it removes, with its order.
- When it is on: the switch or config key, how it is set (env, YAML, CMake), the default, and every coupling
  (what it requires, what it implies, what it turns off).
- Aliases: the internal names (PR numbers, leg names, option letters) a reader will meet in the code and history.

## 2. Derivation
Continuous equation -> integral form over a cell -> discrete form, every step written. Each numbered equation that
the code implements is tagged with the code site that implements it. Ends with a statement of what is exact and
what is truncated, with orders. Points to its executable check (section 7 of this guide).

## 3. Numerical method
The discrete method as the code runs it: stencil (with a figure), where each quantity lives (cell average, cell
centroid point value, face average, face point value), ghosts and how they are filled, walls, block seams, solids,
which RK stage and which part of the step it runs in, explicit vs implicit, order of accuracy (interior, wall
cells, seams) with the evidence for each order.

## 4. Code
A table: | what | `path:line@sha` | function / symbol | switch |, then a short walk-through in step order. Every
switch read, every setup check, every warning a user can hit is listed.

## 5. Tests
A table: | test (ctest name) | what it asserts | tolerance | where the tolerance comes from |. Then the evidence:
numbers with their sha, deck and run (section 4 of this guide). Say which assertions are covered on CPU only, which
also on CUDA, which on more than one rank.

## 6. Limits
Known limits, failure modes, untested combinations, open issues, each with its evidence or "not measured".
```

Rules for the layers:

- **Summary** fits on one screen. It states the default explicitly, even when the default is "off".
- **Derivation** has no gaps. When the derivation exists in `sources/` or `docs/derivations/`, re-write it here in
  the report's notation (do not paste), check every step against the code, and cite the source. When no derivation
  exists, re-derive it from the code at the pinned sha and mark the outline entry "re-derive". Never summarise a
  derivation from memory.
- **Numerical method** contains at least one figure (section 6).
- **Code** citations must resolve at the pinned sha (section 3).
- **Tests** never quotes a number without its sha, deck and run; "missing evidence" is an acceptable entry, a bare
  number is not.
- **Limits** includes the switch combinations that are not tested (cross-reference chapter 12's matrix).

## 3. Citations

### 3.1 Code
Format: `` `path:line@sha` `` or `` `path:line-line@sha` ``, path relative to the repository root, sha abbreviated
to 7 characters, followed by the symbol in prose:

> The slope stencil is `centroid_slope` (`src/hydro/gravity_work_radial.hpp:28-51@dae902b`).

- The line points at the definition or the statement that carries the claim, not at a comment above it (unless the
  claim is about the comment).
- Other repositories: prefix the repo, `kintera:src/eos/...:42@<sha>`, `pyharp:...@<sha>`.
- Pinned shas for round 1:
  - snapy main: `aea71ed` (chengcli/snapy main; the base of this branch).
  - the gravity-work round: `dae902b` (`next/final-batch` on UCzhangxi/snapy). Code that differs between the two is
    cited at `dae902b`. When the round merges, the editor moves every pin to the merge sha with a script; authors do
    not edit shas by hand.
- A citation is checked by `build/check_citations.py` (planned; see section 9): the file must exist at the sha and
  the line must exist. Authors run `git show <sha>:<path> | sed -n '<line>p'` themselves before committing.
- Tests are cited by file and ctest name: `tests/test_gravity_work_radial_exact.py` (ctest
  `test_gravity_work_radial_exact_python`).

### 3.2 Sources and history
- Derivation notes: `sources/<file>` §n, or `docs/derivations/<file>@<sha>` §n.
- Pull requests and issues: `chengcli/snapy#NNN` or `UCzhangxi/snapy#NNN`, always with the owner/repo.
- Commit: `snapy@<sha>`, with its subject line in quotes when the subject carries the meaning.

## 4. Numbers and evidence

Every number that is a measurement (an error, a drift, a rate, a timing, a growth) carries a provenance tag:

> max per-step $|\Delta(E+P)|/|E+P| = 3.9\times10^{-16}$ [sha `dae902b`; deck: `tests/test_gravity_work_radial_exact.py`
> case `sph_vic`; run: ctest `test_gravity_work_radial_exact_python`, CPU, double].

- **sha**: the code that produced it.
- **deck**: the input (YAML file, or the test/script and case that builds the input).
- **run**: how it was run (ctest name, or the committed script with its arguments), device, precision, ranks.
- A number copied from a source note keeps the note's sha; if the note has none, the number is marked
  **missing evidence** and is either re-run at the pinned sha or removed (ISSUES.md items 2, 3, 5).
- A number from an executable check in this report cites the check script and its output file:
  [check `chapters/06-gravity-energy/checks/d_face_work_pe_check.py`, output `.../d_face_work_pe_check.out`].
- Tolerances are numbers with a reason: "1e-14 relative: 20 steps of round-off on a sum of 32 terms of size 1e2 with
  double precision", not "small".
- Orders of accuracy are fitted slopes from at least three resolutions, with the resolutions.

## 5. Equations and notation

- All symbols are defined in `NOTATION.md`, one meaning each. A chapter may introduce a local symbol only if
  NOTATION.md has no symbol for the concept; it defines it at first use and the editor adds it to NOTATION.md.
- Indices: cell $i$ (x1), $j$ (x2), $k$ (x3); faces at half integers $i\pm\tfrac12$. Code index names (`is`, `ie`,
  `il`, `iu`) appear only in the Code layer, mapped to math indices once.
- Cell averages carry an overbar only where a point value of the same quantity also appears: $\bar\rho_i$ against
  $\rho(x_{1,i})$. In a section that uses only cell averages, say so and drop the bar.
- Face quantities: subscript $f$ or $i\pm\tfrac12$. Operators are written as in NOTATION.md §4 ($\Delta_i$,
  $\delta_{x}$, $\langle\cdot\rangle_V$, ...).
- Equations that the code implements are numbered `(N.M.k)` within the section ("(6.3.7)") and tagged in the text with
  the code site.
- Orders: write $O(h^2)$ with $h$ the local x1 cell width, or $\Delta x_1$ when the section is about x1 specifically.
  "Second order" means the error of the quantity being discussed, which is named.
- Signs: gravity $g_1$ = `grav1` is negative when it points to decreasing $x_1$. Potentials are $\phi = -g_1x_1$
  (increasing upward). Never write $g$ for $|g_1|$ without defining it.
- Code identifiers in prose are in backticks. Math symbols are never in backticks.

## 6. Figures

Every scheme gets at least one cartoon (stencil, fluxes, faces vs cells, ghosts, walls, seams) and, where the scheme
has a measured property, one data figure. All figures are produced by committed scripts; no hand-drawn or
screenshot images.

### 6.1 Layout
```
chapters/NN-slug/figures/
    fig_<scheme>_<what>.py        # one script per figure, runnable from any directory
    fig_<scheme>_<what>.png       # rendered output, committed (200 dpi)
    fig_<scheme>_<what>.svg       # optional vector copy
chapters/common/figstyle.py       # shared style: palette, fonts, sizes, helpers
```
- A figure script takes no arguments, writes its PNG next to itself, and prints the path. It imports only numpy,
  matplotlib and `chapters/common/figstyle.py` (found via a path relative to `__file__`). A data figure reads its
  data from a committed output file of an executable check or a run, never from a live run.
- The script header states what the figure shows, its sha, and the data file it reads.
- `build/render_figures.sh` (planned) re-renders every figure; a figure whose PNG differs after re-rendering is a bug.

### 6.2 Look
- Size: single column 3.4 in wide, double column 7.0 in wide; height as needed. 200 dpi PNG.
- Fonts: matplotlib's DejaVu Sans at 9 pt for labels, 8 pt for ticks and annotations; math in the default mathtext.
  Do not depend on a TeX installation.
- Palette: Okabe-Ito, colour-blind safe, used in this order and with these meanings across the report where
  applicable:

  | name | hex | default use |
  |---|---|---|
  | black | `#000000` | grid, walls, axes |
  | orange | `#E69F00` | face quantities, fluxes |
  | sky blue | `#56B4E9` | cell quantities |
  | bluish green | `#009E73` | the scheme being described (its added term) |
  | yellow | `#F0E442` | highlights (use sparingly; poor on white) |
  | blue | `#0072B2` | reference / exact solution |
  | vermillion | `#D55E00` | errors, defects, the term removed |
  | reddish purple | `#CC79A7` | ghosts, other blocks |

  Never encode meaning by colour alone: pair colour with marker shape, line style or a label.
- Ghost cells are hatched (`//`), solids are cross-hatched (`xx`), walls are thick black lines, block seams are
  dashed reddish purple lines.
- Axes are labelled with quantity and unit ("$x_1$ [m]", "relative error [-]"). Log axes for convergence; a
  reference slope triangle or line labelled with its order.
- Cartoons have no axes frame; they label every cell index and face index that the text refers to.

## 7. Executable checks

Every derivation has an executable check committed next to it: the identities and closed forms of the Derivation
layer are verified symbolically (sympy) or numerically (numpy) from the discrete formulas.

### 7.1 Layout
```
chapters/NN-slug/checks/
    <scheme>_check.py      # the check
    <scheme>_check.out     # its committed output (stdout), regenerated by running the script
```
- Runs with `python3 <scheme>_check.py` from any directory, needs only numpy and sympy, finishes in under a minute
  on a laptop, and exits non-zero if any assertion fails. It prints every number the chapter quotes from it, each on
  a line with a stable label, so the chapter can cite "check line `[C3]`".
- Structure: a header docstring (what is checked, the sha whose formulas it mirrors, how to run), then one function
  per numbered claim `check_C1_...`, `check_C2_...`, each printing `[Cn] PASS/FAIL <label>: <numbers>` and returning
  a bool, then `main()` that runs all and exits with the failure count.
- A check that mirrors code (a numpy port of a C++ function) says so, cites the code lines it ports, and is written
  line for line against them so a reviewer can diff the two by eye.
- Tolerances in checks follow section 4: each is stated with its reason.
- A check does not import snapy. Checks that need snapy are tests in `tests/` and are cited in the Tests layer.

## 8. Directory layout

```
doc/tech-report/
    README.md  BRIEF_*.md  ISSUES.md  STATUS.md
    STYLE.md  NOTATION.md  OUTLINE.md
    sources/                      # inputs, read-only
    chapters/
        common/figstyle.py
        NN-slug/
            README.md             # chapter intro, section list, order of reading
            <scheme>.md           # one file per scheme (six layers)
            figures/  checks/
    reviews/                      # review notes, one file per review round
    build/                        # scripts: citation checker, figure renderer, PDF/HTML build
```

## 9. Review checklist (authors run it before asking for review)

1. Six layers present, in order, with the headings of section 2.
2. Every symbol in NOTATION.md or defined locally and flagged to the editor.
3. Every `path:line@sha` resolves (`git show <sha>:<path> | sed -n '<line>p'` shows the claimed statement).
4. Every number carries sha, deck, run, or is marked missing evidence.
5. Every figure re-renders from its script with no diff; colour-blind palette; labelled axes and units.
6. Every derivation's check runs, passes, and its `.out` is committed and current.
7. No machine names, cluster paths, personal paths; no other model's code.
8. Switch, default and couplings in the Summary agree with chapter 12's matrix.
