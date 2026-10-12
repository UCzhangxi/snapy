# Author checklist

Run this before opening a chapter PR. Everything here is cheap; the render is the only slow step, and CI runs
it anyway. Rules are in STYLE.md — this is the operational list, not a second rulebook.

## 1. Gates to run

All from `doc/tech-report`. Each command is the whole check; none needs an argument you have to invent.

| # | command | must say |
|---|---|---|
| 1 | `python3 tools/code_anchors.py check` | `0 unresolved`. Needs Universal Ctags 6.2.1 (`CTAGS=<binary>` if it is not on `PATH`) and a clone holding the pin (`SNAPY_REPO`), else it fetches one. |
| 2 | `python3 tools/check_citations.py` | **no new problems**. It is not zero today; compare the count against the base, not against zero. |
| 3 | `python3 tools/gen_derivation_index.py` | writes, and leaves `git status` clean |
| 4 | `python3 tools/gen_notation_index.py` | writes, and leaves `git status` clean |
| 5 | `python3 tools/gen_test_index.py --check` | `is current` |
| 6 | `python3 tools/book_chapters.py` | lists the chapters that exist, and leaves `git status` clean |
| 7 | `find book -name '*.qmd' \| sort \| xargs python3 tools/check_math_spans.py` | exit 0 |
| 8 | `python3 tools/check_table_cells.py book/` | `clean` |
| 9 | `python3 -m pytest tools/tests -q` | all pass |
| 10 | `PYTHONPATH=src python3 -m pytest src/tests -q` | no **new** failures (needs `snapy_report` importable; CI does `pip install -e src`) |
| 11 | `python3 tools/render_gate.py book/` | its `✗` lines are **the same as the base's**, not absent |

**Compare 2, 10 and 11 against the base commit, not against perfection.** Run them on the base in a scratch
worktree first and keep both outputs. A gate that was already red is not yours to fix in a content PR; a gate
that goes red *under your change* is.

Generators (3, 4, 5, 6) must be no-ops. If one rewrites a file, commit what it wrote — never hand-edit a
generated file.

Quarto is not installed on every machine. Where it is missing, `render_gate.py` runs the source gates and then
stops at the render itself; say so in the PR body and let CI be the render's word.

## 2. What goes in the PR body

- **Pins**: the base sha you branched from and the code pin, each with the command that read it
  (`git ls-remote`, `code_pin.yml`) and the UTC time.
- **One line per row or claim you touched**: what it was, what it is now, and why — or `kept`, with what you
  checked at the pin.
- **Citations whose symbol changed at the pin**: old symbol, new symbol, and whether the claim changed
  (STYLE.md 3.1, the provisional clause). A reviewer reads this list first.
- **Gate table, before and after**, with the numbers — not "gates pass".
- **Anything you deliberately did not do**, with its count. "I left 58 of these and here is where" is a
  finding; silence is a trap for the next author.
- No AI attribution line, and no `Co-Authored-By` trailer.

## 3. What the text may not contain

- A hand-written line number, in a link or in `path:lines@sha` form (STYLE.md 3.1).
- A sha restating the pin. Read it from `code_pin.yml`.
- Change history: "since `#NNN`", "main after ...", "checked at `<sha>`", or a PR number in prose
  (STYLE.md 3.2). Provenance goes in the PROVENANCE block or a `[source: ...]` footnote.
- A measured number without its command and the versions behind it (STYLE.md 4).

## 4. What to ask the editor instead of deciding

Open an ISSUES.md item or ask in the report thread; do not settle these inside a chapter PR.

- **A new symbol** that NOTATION.md has no entry for — propose it, use it locally, and flag it.
- **A symbol that clashes** with a reserved letter, or that two chapters use differently.
- **A section that belongs in another chapter**, or a scheme that needs splitting or merging.
- **A cross-chapter claim** you cannot verify from your own chapter's code.
- **A pin move**, always. Authors never move the pin.
- **A gate that is red on the base.** Report the count; do not sweep it in a content PR.
