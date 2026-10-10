# Style guide for the snapy Technical Report

This file is binding for every chapter author. The worked example is
`chapters/06-gravity-energy/D_face_work_pe.md`; it is a **pre-conversion draft**, so sections 1-9 bind it in
full but section 10 (Quarto markup) does not. A pre-conversion draft may hand-number its equations
(`\tag{N.n}`) and its headings and may write code locations as `path:lines@sha`; it may not deviate from any
other rule. Converting a draft to `book/chapters/NN-slug/_<scheme>.qmd` is a mechanical step with exactly four
parts: every `\tag{N.n}` becomes a `{#eq-chNN-<scheme>-<what>}` label and every `(N.n)` in prose becomes
`([-@eq-chNN-<scheme>-<what>])`; every hand-typed heading number is deleted; every `path:lines@sha` becomes the
link of section 10.6; every Unicode symbol becomes math. The author does the conversion and reruns the review
checklist of section 9 afterwards. Where this file and a converted chapter disagree, this file wins and the
chapter is a bug to report.

The binding example is the converted `.qmd`, not the draft: `book/chapters/06-gravity-energy/_dwork.qmd` is the
first real scheme file and the one every other author copies.

Contents: 1 Scope and voice, 2 the six-layer scheme template, 3 citations, 4 numbers and evidence, 5 equations and
notation, 6 figures, 7 executable checks, 8 directory layout, 9 review checklist, 10 Quarto markup.

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
- Source format: Quarto (`.qmd`, Pandoc markdown with LaTeX math), rendered to an HTML site and a PDF from the same
  files. Section 10 gives the markup rules; they are binding. Wrap at about 120 characters.
- Physics is written as connected prose. Bullets are for procedures, lists of switches and checklists only.

## 2. The six-layer scheme template

Every scheme is one file `book/chapters/NN-slug/_<scheme>.qmd`, included into its chapter file (section 10.1), with
exactly these six layers, in this order, with these headings. Do not merge, reorder or rename them. A layer with nothing to say says so in one line
and why ("No known limits beyond those of the base scheme in §5.2.").

```markdown
## <Scheme name, what it does> (`<SWITCH>` or YAML key) {#sec-chNN-<scheme>}

<!-- PROVENANCE
pin: snapy@<sha> (<branch>)
sources: <files>
status: draft | reviewed | approved
author: <name>
reviewer: <name>
-->

### Summary
::: {.callout-note title="At a glance"}
What it does (one line). Switch or key, how it is set, default. Requires / implies / turns off. Order of accuracy.
The one equation that defines it (a reference to the labelled equation).
:::

Then one to three paragraphs of prose: what it does, why it is there (the error or failure it removes, with its
order), and when it is on. Bullets only for the list of switch couplings. Aliases (PR numbers, leg names, option
letters a reader will meet in the code and history) in the last sentence.

### Derivation
Continuous equation -> integral form over a cell -> discrete form, every step written. Each numbered equation that
the code implements is tagged with the code site that implements it. Ends with a statement of what is exact and
what is truncated, with orders. Points to its executable check (section 7 of this guide).

### Numerical method
The discrete method as the code runs it: stencil (with a figure), where each quantity lives (cell average, cell
centroid point value, face average, face point value), ghosts and how they are filled, walls, block seams, solids,
which RK stage and which part of the step it runs in, explicit vs implicit, order of accuracy (interior, wall
cells, seams) with the evidence for each order.

### Code
A table: | what | code link | symbol | switch | (code link as in section 10.6), then a short walk-through in step order. Every
switch read, every setup check, every warning a user can hit is listed.

### Tests
A table: | test (ctest name) | what it asserts | tolerance | where the tolerance comes from |. Then the evidence:
numbers with their sha, deck and run (section 4 of this guide). Say which assertions are covered on CPU only, which
also on CUDA, which on more than one rank.

### Limits
Known limits, failure modes, untested combinations, open issues, each with its evidence or "not measured".
```

Rules for the layers:

- **Summary** fits on one screen: the "At a glance" box and at most three paragraphs. It states the default
  explicitly, even when the default is "off".
- **Derivation** has no gaps. When the derivation exists in `sources/` or `docs/derivations/`, re-write it here in
  the report's notation (do not paste), check every step against the code, and cite the source. When no derivation
  exists, re-derive it from the code at the pinned sha and mark the outline entry "re-derive". Never summarise a
  derivation from memory.
- **Numerical method** contains at least one figure (section 6).
- **Code** citations must resolve at the pinned sha (section 3).
- **Tests** never quotes a number without its sha, deck and run; "missing evidence" is an acceptable entry, a bare
  number is not.
- **Limits** includes the switch combinations that are not tested (cross-reference the switch coverage
  matrix, `@sec-ch12-matrix`).

## 3. Citations

### 3.1 Code
In a rendered chapter a code citation is always the link of section 10.6: link text `basename:lines`, target
the file at the pinned **full** sha on GitHub. The notation `path:lines@<short-sha>` names a location in this
guide, in OUTLINE.md, in a review and in a pre-conversion draft; it never appears in a `.qmd`. Converting one
to the other is mechanical. **The old form, forbidden in a `.qmd`,** is
`src/hydro/hydro_forward.cpp:817-822@e894700`; it becomes
`` [`hydro_forward.cpp:817-822`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_forward.cpp#L817-L822) ``.
That line is the one place in this guide where a short sha is allowed, and it is allowed because it is
explicitly labelled as the old form (section 3.2).
In prose the symbol comes first, then the link:

> The slope stencil is `centroid_slope` ([`gravity_work_radial.hpp:28-51`](https://github.com/UCzhangxi/snapy/blob/<sha>/src/hydro/gravity_work_radial.hpp#L28-L51)).

- The line points at the definition or the statement that carries the claim, not at a comment above it (unless the
  claim is about the comment).
- Other repositories are cited exactly like snapy, with the owner spelled out in the URL and the repository name
  prefixed to the link text:
  `` [`pyharp integrator.cpp:49-61`](https://github.com/chengcli/pyharp/blob/4721715855e937c1e8b218e964c0655f46e56e29/src/integrator/integrator.cpp#L49-L61) ``.
  The repositories the report may cite, and the only owner each may be cited from, are listed with their pins in
  `index.qmd`: snapy (`UCzhangxi/snapy` for the round pin, `chengcli/snapy` for the main pin), kintera
  (`chengcli/kintera`), pyharp (`chengcli/pyharp`), pydisort (`zoeyzyhu/pydisort`), commux (`zoeyzyhu/commux`).
  A citation to any other repository, or to a fork not on that list, is a review failure. Note that a sha from a
  fork resolves through the parent's URL on GitHub; cite the repository the commit actually lives on.
- Pins for round 1. They are defined **here and nowhere else**; `index.qmd` and OUTLINE.md reproduce this
  table and are regenerated from it, never edited by hand. Each pin is a full sha and a description of what
  the commit *is*, not of which branch happens to point at it:

  | pin | full sha | what it is |
  |---|---|---|
  | snapy base | `aea71ed852effb09e6aa155dd26349f1210ef556` | the commit of `chengcli/snapy` on which the gravity-work round is based |
  | snapy round | `e894700ff7aee30b52882e5202b16461413780b0` | the gravity-work round as squash-merged by `chengcli/snapy#297`, on `chengcli/snapy` main |
  | kintera | `4dc613d04f24621b3119d343c5c7c9b93628895b` | the kintera commit the round builds against |
  | pyharp | `4721715855e937c1e8b218e964c0655f46e56e29` | the pyharp commit the round builds against |

  Code that differs between the base and the round is cited at the round pin. A branch name may be given as a
  note ("`next/final-batch` pointed here on 2026-10-09") but is never the pin: branches move. When the round
  merges, the editor moves every pin with the script of section 3.1; authors do not edit shas by hand.
- Every code citation names its anchor: the function, method, type or variable whose definition or use the cited
  lines contain. The anchor is the "symbol" column of the Code table, and in prose it is the identifier the
  sentence uses before the link. `tools/check_citations.py` checks three things, not two: the file exists at the
  sha; the lines exist; and the anchor's identifier appears at least once inside the cited range. A citation
  whose range does not contain its anchor fails, even though the lines exist.
- When the pin moves, the editor's script rewrites the sha and **re-resolves each range by locating the anchor
  in the new file**; it never carries a line range across a sha unchanged. Where the anchor has moved to another
  file, been renamed, or been deleted, the script does not guess: it lists the citation in
  `reviews/pin-move-<newsha>.md` and the owning author re-reads the code and rewrites the citation and, if the
  code changed, the claim. A pin move is not merged until that list is empty. Authors check their own citations
  before committing with `git show <full-sha>:<path> | sed -n '<lo>,<hi>p'` and confirm the anchor is in the
  output — not just that the lines exist.
- Tests are cited by file and ctest name: `tests/test_gravity_work_radial_exact.py` (ctest
  `test_gravity_work_radial_exact_python`).

### 3.2 Sources and history
- Derivation notes: `sources/<file> §n` for a copy in this directory, or `docs/derivations/<file>@<full-sha>
  §n` for one in the code tree. The path, the sha and the section are repeated in full at every citation; no
  abbreviation to `§n` alone, and no second form for the same file within a chapter. A script is cited by path
  and sha with a function or a printed label, never a "§": `docs/derivations/optionF_replica.py@<full-sha>`,
  output label `[C6]`. A note or script at a sha that is not one of the pins of section 3.1 is cited only in
  the Limits or Tests layer, with the reason it is off-pin and what it would take to re-run at the pin.
- A derivation note that is still being edited is cited at the pin like any other file, but a statement *about*
  the note — that it has an error, a gap or a placeholder — is a statement about a moving target. Such a
  statement is written in this form: "at `<file>@<full-sha>` §n, ... ; check the note's current head before
  publication". The editor re-reads every such statement against the note's branch tip as the last step before
  each release render, and the author either removes the statement or re-pins it. The same applies to any
  sentence that says a defect was "flagged to its author".
- Pull requests and issues: `chengcli/snapy#NNN` or `UCzhangxi/snapy#NNN`, always with the owner/repo.
- Commit: `snapy@<full-sha>`, the full 40 characters, with its subject line in quotes when the subject carries
  the meaning. A short sha appears nowhere in a rendered file: it is not stable as the repository grows and
  `git fetch` does not accept it. Where a short form is wanted for reading, write the full sha and let the link
  text carry the short form. Two exceptions, and no others:
  - **a short sha may appear only inside an example that is explicitly labelled as the old or forbidden form**,
    so that a rule can show what it converts away from. The example in section 3.1 is the only such example in
    this guide;
  - planning files are exempt (section 10.2): OUTLINE.md and the sources keep the short-sha notation of
    section 3.1, and it is converted when the text moves into a `.qmd`. They are never swept for short shas,
    and a short sha in one of them is not a defect.

## 4. Numbers and evidence

Every number that is a measurement (an error, a drift, a rate, a timing, a growth) carries a provenance tag:

> max per-step $|\Delta(E+P)|/|E+P| = 3.9\times10^{-16}$ [sha `e894700`; deck: `tests/test_gravity_work_radial_exact.py`
> case `sph_vic`; run: ctest `test_gravity_work_radial_exact_python`, CPU, double].

- **sha**: the code that produced it.
- **deck**: the input (YAML file, or the test/script and case that builds the input).
- **run**: how it was run (ctest name, or the committed script with its arguments), device, precision, ranks.
- A number copied from a source note keeps the note's sha; if the note has none, the number is marked
  **missing evidence** and is either re-run at the pinned sha or removed (ISSUES.md items 2, 3, 5).
- A number from an executable check in this report cites the check script and its output file:
  [check `src/snapy_report/ch06/dwork_check.py`, output `src/snapy_report/ch06/dwork_check.out`].
- Tolerances are numbers with a reason: "1e-14 relative: 20 steps of round-off on a sum of 32 terms of size 1e2 with
  double precision", not "small".
- Orders of accuracy are fitted slopes from at least three resolutions, with the resolutions.

## 5. Equations and notation

- All symbols are defined in `NOTATION.md`, one meaning each. A chapter may introduce a local symbol only if
  NOTATION.md has no symbol for the concept. It then does three things: defines the symbol at first use, lists
  it in a "Local symbols" note at the top of the scheme file, and opens an ISSUES.md item naming the symbol and
  the scheme. When the editor adds the symbol to NOTATION.md, the editor closes the item and **deletes the entry
  from the chapter's local-symbol note**; a note that still lists a symbol NOTATION.md defines is a review
  failure (section 9, item 2). A chapter never redefines a symbol NOTATION.md already has, even to narrow it.
- Indices: cell $i$ (x1), $j$ (x2), $k$ (x3); faces at half integers $i\pm\tfrac12$. Code index names (`is`, `ie`,
  `il`, `iu`) appear only in the Code layer, mapped to math indices once.
- Cell averages carry an overbar only where a point value of the same quantity also appears: $\bar\rho_i$ against
  $\rho(x_{1,i})$. In a section that uses only cell averages, say so and drop the bar.
- Scripts are written in this order and no other: quantity, then the upright kind-label as a superscript, then
  the space index as a subscript, then the time level or RK stage as a trailing superscript in parentheses:
  $W^{\mathrm{D}}_i$, $F^{\mathrm{ref}}_{i+1/2}$, $\rho_i^{n}$, $\mathbf U^{(s)}$, $\Delta\mathbf U^{(0)}_{i}$,
  $\mathsf A^{(E,\rho)}_{i}$. Time levels are $n$ (step) and $(s)$ (RK stage), never both at once; a half time
  level is $n+\tfrac12$. Matrix block labels $(E,\rho)$ (row, column) are a superscript in parentheses. A bare
  subscript $0$ is a cell index only; a background or reference state is subscript $\mathrm{ref}$ (NOTATION.md
  §6), and a domain end is named ($r_{\mathrm{in}}$, $z_{\mathrm{bot}}$).
- Superscript $(0)$ is reserved for the explicit RK increment, $\Delta\mathbf U^{(0)}$, and means nothing else.
  A quantity at the thermodynamic reference state carries a star, not a zero: $u^{\star}_n$, $s^{\star}_n$, to
  match the $T_\star, p_\star$ of NOTATION.md §2a. Never write $u^{(0)}_n$ for a reference energy; the two
  would otherwise collide in chapter 6, which uses both.
- Face quantities: subscript $f$ or $i\pm\tfrac12$. Operators are only those of NOTATION.md §4, written exactly
  as that table writes them: $\Delta_i[q]$, $\langle q\rangle_{V_i}$, $\nabla_{\!1}\!\cdot G$, $s_i[q]$,
  $\operatorname{cov}_i(a,b)$, $[q]_{\mathrm{walls}}$. A chapter that needs another operator defines it at first
  use and the editor adds it to §4; it does not invent a short form for an operator the table already has.
- Equations that are referenced or that the code implements carry a Quarto label and are numbered by Quarto
  (section 10.3); never type an equation number by hand. Each such equation is tagged in the text with its code site.
- Orders: write $O(h^2)$ with $h$ the local x1 cell width, or $\Delta x_1$ when the section is about x1 specifically.
  "Second order" means the error of the quantity being discussed, which is named.
- Signs: gravity $g_1$ = `grav1` is negative when it points to decreasing $x_1$. Potentials are $\phi = -g_1x_1$
  (increasing upward). Never write $g$ for $|g_1|$ without defining it.
- Code identifiers in prose are in backticks. Math symbols are never in backticks.
- Upright sub- and superscripts use `\mathrm{}`: `W^{\mathrm{D}}`, `p_{\mathrm{sat}}`. Never `\rm`, `\bf`, `\it`, `\cal`:
  the KOMA class of the PDF removes them and the PDF build fails.
- Bold Greek with `\boldsymbol{}`, never `\mathbf{}` (which drops Greek). Bold Latin vectors with `\mathbf{}`.
- No math macros: write every symbol out (`\overline{\rho}_i`, `\mathrm{d}`, `\partial`). The HTML uses MathML
  (as the house books do), which has no macro layer.
- Differential and operator symbols are upright: `\mathrm{d}` in `\mathrm{d}V`, `\mathrm{d}x_1`,
  `\frac{\mathrm{d}}{\mathrm{d}t}`; `\partial` for partial derivatives; `\mathrm{D}/\mathrm{D}t` for a material
  derivative. Italic $d$ is never a differential; it is free for a symbol. A prime denotes a derivative with
  respect to $x_1$ only where the section says so in words at first use, and never in a chapter that also uses
  the perturbation notation of NOTATION.md §6 (see NOTATION.md §10).
- Approximate values: the number goes inside the math, `$\sim\!0.1$`, never `$\sim$0.1`.
- Relations and arrows in prose are math too: `$\le$`, `$\to$`, `$\times$`; never the Unicode characters ≤, →, ×.

## 6. Figures

Every scheme gets at least one cartoon (stencil, fluxes, faces vs cells, ghosts, walls, seams) and, where the scheme
has a measured property, one data figure. All figures are produced by committed scripts; no hand-drawn or
screenshot images.

### 6.1 Layout
```
src/snapy_report/chNN/fig_<scheme>_<what>.py   # one function per figure: make_fig() -> matplotlib Figure
src/snapy_report/figstyle.py                    # shared style: palette, fonts, sizes, helpers
```
- A figure is drawn by a function in the `snapy_report` package and placed in the chapter by a Quarto code cell
  (section 10.4), so the figure, its caption and its label live in the chapter and its provenance in the package.
  The function imports only numpy, matplotlib and `figstyle`. A data figure reads its data from a committed output
  file of an executable check or a run (`src/snapy_report/chNN/data/`), never from a live run.
- The function's docstring states what the figure shows, its sha, and the data file it reads.
- `quarto render` re-draws every figure (with `freeze: auto`, only changed chapters re-run); a figure that differs
  after a clean re-render is a bug.

### 6.2 Look
- Size: single column 3.4 in wide, double column 7.0 in wide; height as needed. Vector output (SVG for HTML, PDF for
  the PDF; section 10.4); no raster line drawings.
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
  | light blue (fill) | `#EAF5FC` | cell fill in cartoons |
  | light reddish purple (fill) | `#F7E6EF` | ghost-cell fill in cartoons |

  Never encode meaning by colour alone: pair colour with marker shape, line style or a label.
- Ghost cells are hatched (`//`), solids are cross-hatched (`xx`), walls are thick black lines, block seams are
  dashed reddish purple lines.
- Axes are labelled with quantity and unit ("$x_1$ [m]", "relative error [-]"). Log axes for convergence; a
  reference slope triangle or line labelled with its order.
- Cartoons have no axes frame; they label every cell index and face index that the text refers to.
- Shared conventions, drawn only through helpers in `figstyle` (never re-drawn by hand): cell box; cell value =
  sky-blue circle; face value = orange triangle; wall = thick black line; ghost cell = hatched box with the light
  reddish-purple fill `#F7E6EF`; cell fill, where needed, the light blue `#EAF5FC`. Stencil cells are indexed $l$.
- At most 4 panels per figure; a cartoon and a data plot are separate figures. Panels that compare share the y range
  and the y label.
- Text in a figure is never smaller than 8 pt at print size; labels never overlap data or other labels.
- The caption, not the body text, defines every marker, line style and colour.
- Check every figure once in greyscale: it must still read.

## 7. Executable checks

Every derivation has an executable check committed next to it: the identities and closed forms of the Derivation
layer are verified symbolically (sympy) or numerically (numpy) from the discrete formulas.

### 7.1 Layout
```
src/snapy_report/chNN/<scheme>_check.py   # the check
src/snapy_report/chNN/<scheme>_check.out  # its committed output (stdout), regenerated by running the script
src/tests/test_checks.py                   # pytest runs every check; a failing check fails the build
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
    book/                         # the Quarto project
        _quarto.yml               # book config, chapter list, math macros (HTML and PDF), crossref settings
        _freeze/                  # committed: frozen cell outputs (freeze: auto)
        index.qmd  references.qmd  references.bib  apj.csl
        chapters/NN-slug.qmd      # one file per chapter; schemes are its level-2 sections
        figs/                     # static images only (none expected)
    src/                          # python: package snapy_report (figures, checks), tests/ (pytest)
    reviews/                      # review notes, one file per review round
    tools/                        # scripts: citation checker, pin mover
```

## 9. Review checklist (authors run it before asking for review)

1. Six layers present, in order, with the headings of section 2; `quarto render book --to html` and `--to pdf` both
   succeed with no unresolved cross-reference and no warning from the chapter (section 10.9).
2. Every symbol in NOTATION.md or defined locally and flagged to the editor.
3. Every code link resolves at its sha and its lines show the claimed statement (`tools/check_citations.py`).
4. Every number carries sha, deck, run, or is marked missing evidence.
5. Every figure re-renders from its script with no diff; colour-blind palette; labelled axes and units.
6. Every derivation's check runs, passes, and its `.out` is committed and current.
7. No machine names, cluster paths, personal paths; no other model's code.
8. Switch, default and couplings in the Summary agree with the switch coverage matrix,
   `@sec-ch12-matrix`.

## 10. Quarto markup (binding)

The report is a Quarto book (Quarto 1.10), the same toolchain as the project owner's other books. Content is Pandoc
markdown in `.qmd` files. The HTML site (MathJax) and the PDF (LuaLaTeX, KOMA `scrbook`) are both built from the same
files, so every construct below must work in both. When in doubt, render both and look.

### 10.1 Files and structure
- One file per chapter, `book/chapters/NN-slug.qmd`, listed in `book/_quarto.yml` under `book: chapters:` (grouped in
  `part:` entries as in OUTLINE.md). Only the editor edits `_quarto.yml` and the chapter files.
- The chapter file holds only: the chapter heading with its label (`# Gravity and energy {#sec-ch06}`), the chapter
  opening (below), and one include per scheme, in reading order: `{{< include 06-gravity-energy/_dwork.qmd >}}`.
  Each scheme lives in its own file `book/chapters/NN-slug/_<scheme>.qmd` (the leading underscore stops Quarto from
  rendering it alone), owned by one author. Includes are inlined before cross-references resolve, so labels work
  across files. Two authors never edit the same file.
- The chapter opening, written by the chapter's lead author: one paragraph on what the chapter covers; a dependency
  map (a figure: schemes as nodes, "requires / implies / turns off" as edges, from chapter 12's matrix); and a table
  with one row per scheme: scheme, switch, default, order, main test.
- Chapter identifiers are fixed now from OUTLINE.md and never change: `ch01` ... `ch17`; split chapters use a letter,
  `ch04a`, `ch04b`, `ch07a`, `ch07b`, `ch14a` ... `ch14c`; appendices `appa`, `appb`, ... (Quarto numbers appendices
  A, B, ...).
  Scheme numbers inside a chapter are fixed from OUTLINE.md at the same time as the chapter identifiers and do
  not change either; a cross-reference to a scheme uses its label (`@sec-ch12-matrix`), never its number.
- Each scheme is a level-2 section with a label, `## ... {#sec-ch06-dwork}`. Its six layers are level-3 sections with
  exactly the headings of section 2. Deeper structure inside a layer uses level 4 (`####`) at most. Quarto numbers all
  sections (`number-sections: true`); never type a section number.
- Label syntax for every cross-reference target: `<kind>-ch<NN>-<scheme>[-<what>]`, lower case, hyphens only, unique
  in the book. Kinds: `sec`, `eq`, `fig`, `tbl`, and `prp`/`lem` for stated identities (section 10.7). Examples: `sec-ch06-dwork`, `eq-ch06-dwork-pe`,
  `fig-ch06-dwork-stencil`, `tbl-ch06-dwork-code`.
- References in prose use Quarto's syntax only: `@sec-ch05-wbref`, `@eq-ch06-dwork-pe`, `@fig-...`, `@tbl-...`. Write
  "as shown in @fig-ch06-dwork-stencil", not "Figure 3" or "the figure above". A bare equation number is always
  written in parentheses, `([-@eq-ch06-dwork-pe])`; a range is `([-@eq-a])–([-@eq-b])`.
- The table of contents lists chapters and schemes only (`toc-depth: 2`). Layers and their subsections are numbered
  and may be referenced (`@sec-...` on a `###` or `####` heading that the text cites). An `{.unnumbered}` heading is
  linked as `[text](#sec-id)`, never with `@sec`.

### 10.2 Inline text
- Inline code (identifiers, switches, YAML keys, file names): backticks. Math symbols: `$...$`, never backticks.
- OUTLINE.md and the sources are planning files and are not rendered. They may use Unicode symbols, and they
  may use the short-sha citation notation `path:lines@<short-sha>` of section 3.1. Text copied from them into a
  `.qmd` is converted on the way: Unicode to math mode, and every short sha to the full-sha link of section
  10.6. Because the conversion happens at that point and not before, neither a Unicode symbol nor a short sha in
  a planning file is a defect, and these files are never swept for either. NOTATION.md is different: it is rendered,
  as Appendix A. The editor keeps it in the markup of this section (ASCII only, every symbol in `$...$`, pipe
  tables within the column limits of section 10.5) and converts it to `book/chapters/appa-notation.qmd` with the
  label `{#sec-appa}`; chapters reference it as `@sec-appa`. Authors edit NOTATION.md, never the generated
  `.qmd`.
- Units, chemical formulas, relations and arrows always in math mode: `$\mathrm{m\,s^{-2}}$`, `$\mathrm{H_2O}$`,
  `$\le$`, `$\to$`. Never Unicode superscripts, subscripts or symbols (`s⁻¹`, `H₂O`, ≤, →, ×): the PDF can drop them
  silently.
- No raw HTML and no raw LaTeX in prose. The only exception is a `{=latex}` block approved by the editor.
- Emphasis: `*italic*` for a defined term at first use, `**bold**` only in Summary bullets and table headers.
- Code locations appear only as links with the short text of section 10.6: long paths do not wrap in the PDF (tested:
  a full path overflowed the line by 180 pt and, in a table, printed over the next column).

### 10.3 Equations
- Display math: `$$ ... $$` on its own lines, followed by a label when the equation is referenced or implemented by
  the code:
  ```markdown
  $$
  P = \mathrm{PE}_d - g_1 \sum_i V_i \sigma_i^2 s_i[\rho]
  $$ {#eq-ch06-dwork-pe}
  ```
  Quarto numbers it per chapter, as "(6.4)" in the PDF and "Equation 6.4" in references. Unlabelled display math is
  allowed for intermediate steps that are never referenced.
- Multi-line derivations use `\begin{aligned} ... \end{aligned}` inside one `$$` block, with one label for the
  block (tested: one number, in HTML and PDF). Never use `align`, `equation` or `eqnarray` environments: they break
  the cross-references. Use `&` to align at `=`, and `\\` to break lines.
- `\qquad` has exactly one legal use: indenting a continuation line inside `aligned`, where one formula was
  broken at a relation or a `+` because it was wider than the text block. It is never used to put two formulas
  on one line, and never used to separate a formula from a condition on it. Two formulas, two definitions, or a
  formula and its side condition are separate `aligned` rows, aligned at `=` with `&`; a side condition that is
  not an equation goes in the prose sentence that introduces the block. Several definitions or updates are one
  row each. A row that still overflows is split at a relation or a `+`, with `\qquad` on the continuation line.
- An in-place update is written as an assignment with `\leftarrow`, never with a composed `-=` or `+=` glyph and
  never with `\mathrel`: `\mathsf A_i^{(E,\rho)} \leftarrow \mathsf A_i^{(E,\rho)} - g_1\sigma_i^2
  \tilde{\mathsf S}_{ii}/\Delta t_c`. Each update is its own `aligned` row. Where several entries are updated by
  the same expression, write one row per entry; do not collapse them with `\quad`. The code's `+=` and `-=`
  appear only in the Code layer, in backticks.
- Number only an equation that is referenced somewhere in the book or implemented by the code. Textbook
  background — the conservation laws in their usual form, standard vector identities, the definition of a
  standard operator — is unlabelled, even when the surrounding prose points at it; point at it in words ("the
  continuity equation above"). If a later chapter needs to reference a background equation, the editor adds the
  label then; do not pre-label. Before review, check that every label you wrote is used: an unreferenced label
  is a defect, not a spare. In the worked example, (6.4.1) and (6.4.2) are background and lose their numbers.
- A derivation step that needs a sentence of justification gets the sentence in prose between two display
  blocks, never inside the math. `\text{}` is allowed for exactly two things: a short qualifier appended to a
  result after `\quad` ("per stage", "in every cell"), at most six words; and a named placeholder for a group of
  terms that is defined in the prose and not written out ("Jacobian terms"). Everything else — a reason, a
  condition, a reference — is prose. Upright words that are part of a symbol are `\mathrm{}`, not `\text{}`
  (section 5).
- No macros (section 5): the HTML is rendered with `html-math-method: mathml`, as in the house books, so pages work
  offline, and MathML has no macro layer. Write every symbol out exactly as NOTATION.md gives it.
- Matrices and stencils: `\begin{pmatrix}` or `\begin{bmatrix}`. Stencils with more than 5 points go in a figure.
- Do not use `\boxed`, `\colorbox`, `\fbox` or any other framing construct in math: they are amsmath/LaTeX
  macros and the MathML path for the HTML has no macro layer. The defining equation of a scheme is marked by
  being the one the "At a glance" box references, not by a frame. The same applies to `\tag`, `\label`,
  `\nonumber`, `\notag` and `\ref`: numbering and referencing are Quarto's (section 10.3), never TeX's.
  **Status: pending CI.** Whether `\boxed` survives the MathML path has not been tested — there is no Quarto
  on the authors' machines and tech-report has no CI yet. The rule above is the safe default until the first
  CI render settles it; if CI shows `\boxed` renders in both HTML and PDF, the editor may relax this line.
- Every equation that the code implements is followed, in the sentence after the display block, by its code link
  (section 10.6): "@eq-ch06-dwork-pe is computed in [`hydro_forward.cpp:761-790`](...)". The link never precedes
  the equation and never sits in a heading or a bold lead-in; a lead-in names the quantity only.

### 10.4 Figures
- Every figure is a Python code cell, in the scheme's `_<scheme>.qmd`, that calls a function of the `snapy_report`
  package (section 6.1):
  ````markdown
  ```{python}
  #| label: fig-ch06-dwork-stencil
  #| fig-cap: "The corrected-PE face work on a three-cell stencil next to the lower wall. ..."
  #| fig-alt: "Cartoon of cells i-1, i, i+1 with faces, ghost cells hatched, the wall as a thick line."
  #| echo: false
  from snapy_report.ch06.fig_dwork_stencil import make_fig
  make_fig()
  ```
  ````
  `echo: false` for every figure cell. The book sets `freeze: auto`, and `_freeze/` is committed, so a render does not
  re-run a chapter whose cells did not change.
- Captions: one sentence saying what is shown, then one or two sentences saying what to read from it, written so the
  figure can be understood without the text. Define every symbol, colour and line style in the caption or the legend.
  The source data and sha go in the function's docstring, not in the caption.
- `fig-alt` is required (accessibility, and it is what a reviewer reads first).
- Size: set by `figstyle` (3.4 in single, 7.0 in double width; section 6.2). Do not use `fig-width` or `out-width` in
  cells. Formats: SVG for HTML and PDF for the PDF (set in `_quarto.yml`), so lines and text stay sharp. Never use a
  raster image for a line drawing.
- Panels: one function makes the whole multi-panel figure with panel letters (a), (b) in the top left of each panel;
  the caption refers to them. No Quarto sub-figure layouts.
- A static image (none expected) goes in `book/figs/` with its provenance in the caption, and is included as
  `![caption](figs/x.pdf){#fig-... fig-alt="..."}`.

### 10.5 Tables
- Pipe tables with a caption and label on the line after the table: `: Code map of the corrected-PE face work.
  {#tbl-ch06-dwork-code}`.
- At most 5 columns and short cells: the PDF column is about 6.3 in wide. Put long text in prose after the table.
  Code links in tables use the short link text of section 10.6.
- Numbers in tables use the same significant digits within a column; the evidence tag (section 4) goes in a footnote
  or the caption.
- The Code and Tests layers each use one table, as in section 2; the column headers there are fixed.

### 10.6 Code citations and links
- A code citation is a link whose text is `basename:lines` and whose target is the file at the pinned full sha
  on GitHub. Written out, the source is:

  ```markdown
  [`gravity_work_radial.hpp:28-51`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/gravity_work_radial.hpp#L28-L51)
  ```

  The full path and the sha are in the URL, not in the link text. Where two files share a basename, add the last
  directory (`hydro/hydro.cpp:120-140`). The Code table of a scheme holds the same short links, and its "symbol"
  column holds the anchor of section 3.1. The pins are defined in section 3.1 and reproduced in `index.qmd`. The
  editor's pin-mover script rewrites every URL when the pin moves and re-resolves each range by its anchor
  (section 3.1), and `tools/check_citations.py` checks every link (file, lines and anchor at the sha).
- A citation is never abbreviated to a bare `:lines`. Every citation, including the second and tenth to the same
  file, is a full link with the link text `basename:lines`. Repetition is the point: a reader opens the book at
  one page. Where a walk-through cites the same file many times, the numbered list of section 10.7 carries one
  link per step.
- Code excerpts: only when the text discusses the lines, at most 15 lines, in a fenced block with its language
  (`cpp`, `python`, `yaml`) and the citation link in the sentence before it. No line numbers inside the block;
  the link carries them.
- Pull requests and issues: `[chengcli/snapy#296](https://github.com/chengcli/snapy/issues/296)`.

### 10.7 Callouts and boxes
- The Summary layer opens with one `::: {.callout-note title="At a glance"}` box: what the scheme does, the switch,
  the default and the couplings, in at most 6 short lines. The rest of the Summary is prose.
- The Limits layer may use one `::: {.callout-warning title="Limits"}` box for the limits a user can hit by
  configuration.
- No other callouts. Never use `collapse`: the PDF prints everything, so text that only works folded is wrong in the
  PDF.
- An exact identity that the tests check (e.g. "E+P is conserved per step") is stated as a proposition,
  `::: {#prp-ch06-dwork-ep}` ... `:::`, so the Tests layer can cite it; a supporting result as `{#lem-...}`.
- Footnotes (`[^n]`) carry evidence tags and asides that would break the flow.
- Step order (an algorithm, the Code walk-through) is a numbered list, one step per item, each with its code link.
  No LaTeX algorithm packages.

### 10.8 Bibliography
- Papers: BibTeX in `book/references.bib`, cited as `[@key]` or `@key`. Keys follow `<firstauthor><year><word>`. Only
  the editor merges new entries. Every entry has a DOI or a URL.
- snapy's own history (PRs, issues, commits) is linked as in section 10.6, not put in the bibliography.

### 10.9 Rendering and the render gate
- `quarto render doc/tech-report/book --to html` and `--to pdf`. Python for the cells: an environment with numpy,
  matplotlib and the `snapy_report` package installed (`pip install -e doc/tech-report/src`).
- The render gate is the house books' `render_gate.py` (BOOKCRAFT section 6, G1), run on a PDF render made with
  `-M latex-clean:false` so the LaTeX log is kept. It catches unresolved cross-references (`?@...`), duplicate labels,
  references into fenced divs, dropped glyphs (missing characters), unrendered math in table cells, a table caption
  orphaned after a code fence, old font commands and unbalanced quotes. Overfull boxes over 10 pt in the chapter's
  text also fail. Python errors fail.
- `freeze: auto` re-runs a chapter only when its `.qmd` changes. After changing any `snapy_report` function, render
  that chapter file alone (`quarto render book/chapters/NN-slug.qmd`), which ignores the freeze. The release render
  is made with `_freeze/` removed.
- The author looks at every page of their chapter in the PDF before asking for review: equation lines inside the
  margin, tables inside the text width, figures legible at print size.
- `_book/` is build output and is not committed; `_freeze/` is committed.
