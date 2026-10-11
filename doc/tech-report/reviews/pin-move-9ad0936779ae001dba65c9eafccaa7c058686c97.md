# Round-pin move survey: e894700 -> 9ad0936 (chengcli/snapy#303)

Status: **survey only. No pin is moved by this file or by the PR that adds it.**
Author: @happysky19. Raised because every "Waiting on chengcli/snapy#303" row on BOARD.md is blocked on this move.

## The two shas

| | full sha | what it is |
|---|---|---|
| current round pin | `e894700ff7aee30b52882e5202b16461413780b0` | the gravity-work round as squash-merged by chengcli/snapy#297, on `chengcli/snapy` main (STYLE.md 3.1) |
| candidate new pin | `9ad0936779ae001dba65c9eafccaa7c058686c97` | chengcli/snapy#303 as squash-merged on `chengcli/snapy` main, 2026-10-11 |

`9ad0936`'s tree is `8f90eca2e18df12938f754196c06550827ce4d86`, which is byte-identical to the tree of the
final #303 review head `546b1afd80d47a437a92ead745ef525f8335094a` (`refs/pull/303/head`). Verified with
`git rev-parse <sha>^{tree}` in a clone of `chengcli/snapy`.

## Why the rows are blocked

Each pending row names code that #303 changed, so it cannot be written at the current pin; and each placeholder
states its own condition as "once #303 has merged **and the pin moves**", not merely "once #303 has merged".

STYLE.md 3.1 makes the move the editor's, not an author's:

- the pins are defined "**here and nowhere else**", with `index.qmd` and OUTLINE.md regenerated from the table,
  "never edited by hand";
- "When the round merges, the editor moves every pin with the script of section 3.1; **authors do not edit shas
  by hand**";
- the move "never carries a line range across a sha unchanged": each citation's range is re-resolved by locating
  its anchor in the new file, and anything that does not re-resolve is listed in `reviews/pin-move-<newsha>.md`
  for its owning author;
- "A pin move is not merged until that list is empty."

STYLE.md 3.2 leaves one opening, and it is not wide enough for these rows: a file at a sha that is not a pin
"is cited only in the Limits or Tests layer, with the reason it is off-pin and what it would take to re-run at
the pin". The pending rows need Code, Derivation and Numerical-method layers, which must be at the pin.

## What the move costs

Measured on tech-report at `6774164475374565286c0e7c348a5267a94863a8`:

| what | count |
|---|---|
| citations of the round pin in `book/**/*.qmd` | 2734 |
| `.qmd` files containing at least one | 180 |

The files the pending sections cite do change between the two shas, so their line ranges must be re-resolved
rather than carried across (`git rev-parse <sha>:<path>`, blob identity):

| file | pin -> 9ad0936 |
|---|---|
| `src/hydro/gravity_work_radial.hpp` | changed |
| `src/hydro/hydro_forward.cpp` | changed |
| `src/mesh/meshblock.cpp` | changed |
| `src/mesh/mesh.cpp` | unchanged |

`tools/` holds no pin-move script: `book_chapters.py`, `check_citations.py`, `check_math_spans.py`,
`check_table_cells.py`, `gen_derivation_index.py`, `gen_notation_index.py`, `gen_test_index.py`,
`render_gate.py`. The "script of section 3.1" does not exist in the tree, so the move is at present a manual
editor operation over 2734 citations.

`tools/check_citations.py` would **not** catch a partial move: it checks that the repository is allowed, that
the sha resolves, that the file and lines exist and that the anchor is inside the range. It does not check that
a citation's sha is one of the pins. A book that cited `9ad0936` in the #303 sections and `e894700` everywhere
else would pass the checker while describing two different `chengcli/snapy` mains for the same code.

## Row-by-row block list

| row | file | what the placeholder is | blocked on |
|---|---|---|---|
| 6.4 | `book/chapters/06-gravity-energy/_dwork.qmd` | written section; its Limits item 11 rests on a convergence table at a non-pin sha | pin move (the section's subject, `SNAP_GRAVITY_WORK_RADIAL_EXACT`, is what #303 changed) |
| 6.6 | `book/chapters/06-gravity-energy/_conserves.qmd` | whole section: all six layers read "Pending chengcli/snapy#303" | pin move |
| 12.8 | `book/chapters/12-configuration/_radial-exact.qmd` | written section for the same switch; no literal placeholder | pin move |
| 13.4 | `book/chapters/13-diagnostics/_fixgrav.qmd` | whole section behind one placeholder callout | pin move |
| ch14 (1) | `book/chapters/14-parallelism-io/_collectives.qmd` | placeholder callout: the fixer's five-double SUM and its order of summation | pin move |
| ch14 (2) | `book/chapters/14-parallelism-io/_repro.qmd` | placeholder callout: whether the fixer SUM's round-off makes results depend on the decomposition | pin move |
| ch16 (3) | `book/chapters/16-known-limits.qmd` 221-225 | three "pending #303" limit lines | pin move, and the source sections above, whose "current text" the lines summarise |
| ch15 | `book/chapters/15-verification/` | 15.6 (Ch.6 Gravity and energy) has no file; OUTLINE.md 15.6 | pin move |
| App B | `book/chapters/17-appendices/_appb-derivation-index.qmd` | the `@sec-ch06-conserves` row reads "Pending chengcli/snapy#303" | follows 6.6 automatically; the index is generated |

## What the editor has to decide

1. Move the round pin to `9ad0936` for the whole book, re-resolving all 2734 citations and emptying this file's
   failure list first; then the rows above are written against it. This is the path STYLE.md 3.1 describes.
2. Or rule that the #303 sections may cite `9ad0936` off-pin ahead of the move, and say in what layers. This
   departs from 3.1 and 3.2 as written, and leaves the book citing two mains for the same code until the move.

Until one of these is chosen, the placeholders stay as they are. No number in them has been guessed.
