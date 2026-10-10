# snapy Technical Report (work in progress)

This branch (`tech-report` on UCzhangxi/snapy) holds a technical description of snapy, in the style of the WRF, MPAS and CESM technical notes. It is never merged into snapy and never opened as a pull request.

- `sources/`: inputs to draw from. These are existing notes, derivations, PR bodies and issue threads, cleaned for this use. They are inputs, not the report.
- `BRIEF_C0.md`: the brief for the architect/editor. `ISSUES.md`: known gaps in the sources. `STATUS.md`: progress log.
- `STYLE.md`: the binding style guide, covering the six-layer template, citations, evidence, figures and checks.
- `NOTATION.md`: every symbol, with one meaning each.
- `OUTLINE.md`: the plan, chapter by chapter and scheme by scheme.
- `chapters/NN-slug/`: Markdown with LaTeX, with `figures/` (scripts and PNGs) and `checks/` (sympy/numpy scripts and their output). `chapters/common/figstyle.py` is the shared figure style. The worked example is `chapters/06-gravity-energy/D_face_work_pe.md`.
- `build/check_citations.py`: checks that every `path:line@sha` citation resolves.
- Planned: `reviews/`, `build/render_figures.sh`, the test-index generator, the PDF/HTML build.
