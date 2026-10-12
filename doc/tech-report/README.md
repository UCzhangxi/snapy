# snapy Technical Report (work in progress)

This branch (`tech-report` on UCzhangxi/snapy) holds a technical description of snapy, in the style of the WRF, MPAS and CESM technical notes. It is never merged into snapy and never opened as a pull request.

- `sources/`: inputs to draw from. These are existing notes, derivations, PR bodies and issue threads, cleaned for this use. They are inputs, not the report.
- `BRIEF_C0.md`: the brief for the architect/editor. `ISSUES.md`: known gaps in the sources. `STATUS.md`: progress log.
- `STYLE.md`: the binding style guide, covering the six-layer template, citations, evidence, figures and checks.
- `NOTATION.md`: every symbol, with one meaning each.
- `OUTLINE.md`: the plan, chapter by chapter and scheme by scheme.
- `chapters/NN-slug/`: Markdown with LaTeX, with `figures/` (scripts and PNGs) and `checks/` (sympy/numpy scripts and their output). The one figure style is `src/snapy_report/figstyle.py` (`from snapy_report import figstyle as fs`); `chapters/common/figstyle.py` and the chapter shims `src/snapy_report/ch05/_style.py` and `ch09/_style.py` are folded into it and go when their figures are ported. The worked example is `chapters/06-gravity-energy/D_face_work_pe.md`.
- `tools/check_citations.py`: checks that every code citation (STYLE 10.6 links and `path:line@sha`) resolves at its sha, that the cited lines exist and, in a `.qmd`, contain the link's anchor symbol, and that the repository is one STYLE 3.1 allows; `python3 -m pytest tools/tests` tests it.
- **Citing code.** Cite snapy code by file and symbol, never by line number:
  `{{< code src/hydro/hydro_forward.cpp HydroImpl::_flux_covariance >}}` renders as the link
  `hydro_forward.cpp` `HydroImpl::_flux_covariance` to the symbol's lines at the one pinned commit,
  `code_pin.yml`. The symbol is a function, method, class, struct, member or variable; C++ names keep their
  classes and drop their namespaces, gtest tests are `Suite.Name`, Python symbols are `Class.method`, and a file
  alone is `{{< code <path> >}}`. If the gate reports a symbol as ambiguous (overloads), add the `overload=N` it
  lists. `python3 tools/code_anchors.py check` resolves every citation at the pin (Universal Ctags 6.2.1:
  `brew install universal-ctags` or set `CTAGS=<binary>`; a clone holding the pin in `SNAPY_REPO`, else it is
  fetched into `~/.cache/snapy-report`); it is the render's pre-render and a CI step, and either fails on a
  citation that does not resolve. To move the pin: `python3 tools/code_anchors.py bump <full-sha>` lists the
  cited symbols whose body changed (re-read those, and fix the claims they carry), and writes the new sha into
  `code_pin.yml` only when every citation resolves there; `diff <old> <new>` prints the same list for any two
  commits. Links that could not be converted to symbols (lines across several symbols, top-level code,
  kintera/pyharp, generated appendices) remain STYLE 10.6 links, listed in `reviews/code-anchors-unmapped.tsv`.
- `tools/check_figstyle.py`: the figure-style gate (STYLE 6). Figure code under `src/snapy_report/` and `chapters/` may style only through `snapy_report.figstyle`: it counts, per chapter and without importing anything, imports of other style modules, rcParams writes and inline font settings (`fontsize=8`, `family=...`), and compares the counts with `tools/figstyle-baseline.json`. Ratchet: a chapter above its baseline fails, and so does one below it until `python3 tools/check_figstyle.py --update` lowers the baseline in the same commit (it never raises one); `--list` prints every site. `render_gate.py` runs it as its `figstyle` source gate; `python3 -m pytest tools/tests` tests it.
- **Ratchet gate.** `tools/ratchet_gate.py` counts four things per chapter and compares them with the committed
  baseline `tools/ratchet-baseline.json`; the `tech-report-ratchet` workflow runs it with its tests on every pull
  request. **history**: change history in body text (PR or issue numbers, "main after", "previously", "now fixed",
  "no longer" and the other phrases of `HISTORY_PATTERNS`); footnotes, HTML comments (PROVENANCE), shortcodes and
  fenced code are not body text, so a source or credit footnote may carry a PR number. **offpin**: a sha of snapy,
  kintera, pyharp, pydisort or commux that is not that package's one pin (`code_pin.yml` for snapy,
  `tools/package-pins.json` for the others), in body text, footnotes and link targets. **status**: a file whose
  PROVENANCE says `reviewed` or `approved` without a valid entry in `reviews/review-record.tsv`. **xref**: a
  reference that resolves nowhere (render_gate's own resolution) and every `sec-` label no other chapter cites.
  A rise fails the run; a fall must lower the baseline in the same pull request (`python3 tools/ratchet_gate.py
  update`, which refuses to raise it). `python3 tools/ratchet_gate.py counts -v` lists every instance.
  **Review record.** One tab-separated line per event, newest last: `file kind reviewer author pin sha256 date
  note`. `kind` is `review`, or `restamp` when the same reviewer confirms an unchanged verdict after an edit (the
  note says what changed, in one line). `pin` is the full sha of `code_pin.yml`; `sha256` is
  `python3 tools/ratchet_gate.py hash book/<file>`, the file without its PROVENANCE comment, so setting the status
  does not change it. A reviewed file passes when its newest entry has the current hash and pin and a reviewer who
  is not its author.
- `tools/render_gate.py`: renders `book/` to HTML and PDF and gates the render (STYLE 10.9). Outcomes: pass (exit 0), pending (exit 2: a `snapy_report` function a chapter calls is not written yet, or there is no book yet) and fail (exit 1). Nothing is released while anything is pending; `--release` makes pending a failure.
  References into a chapter that is not written yet (a valid chapter id of STYLE 10.1 whose `{#sec-<id>}` is defined nowhere) are listed in their own gate, by target id, as expected failures: they still fail, apart from the real dangling references. So are references into a scheme of a written chapter whose `_<scheme>.qmd` does not exist yet.
- `tools/gen_test_index.py`: generates Appendix C, the test index (`book/chapters/17-appendices/_appc-test-index.qmd`), from `tools/ctest-index.json`, the tests `ctest` lists for snapy at the pin (Eigen's own tests, which the build fetches, are counted, not listed). Both files are committed; CI runs `python3 tools/gen_test_index.py --check`, which fails if the fragment is not what the fixture gives. When the pin moves, refresh both from a clean checkout at the new pin (configuring is enough, no build):
  ```bash
  git clone https://github.com/chengcli/snapy snapy-pin && git -C snapy-pin checkout <pin>
  cmake -S snapy-pin -B snapy-pin/build -DCMAKE_BUILD_TYPE=Release -DNETCDF=ON
  python3 tools/gen_test_index.py --refresh snapy-pin/build
  ```
- `book/_quarto.yml`, `book/index.qmd`: the Quarto book (STYLE 8, 10): KOMA `scrbook` PDF through LuaLaTeX, MathML in the HTML (no math macros), `freeze: auto`, `toc-depth: 2`. It includes `book/_tex/inline-code-breaks.tex`, which lets inline code break after `_`, `/`, `:` (after `::`) and `@` in the PDF, shows only the chapter title in running heads and lets long hex strings (shas) break inside; in the HTML it wraps code blocks (`code-overflow: wrap`) and inline code (`book/report.css`: `code { overflow-wrap: anywhere; }`).
- `tools/book_chapters.py`: writes the chapter list of `book/_quarto.yml` from OUTLINE.md's chapter ids and the chapter files that exist (`NN-slug.qmd`, `appX-slug.qmd`), in OUTLINE order; the render gate fails when the list is out of date. Run `python3 tools/book_chapters.py` after adding a chapter file.
- Planned: `reviews/`, `build/render_figures.sh`, the test-index generator, the PDF/HTML build.
