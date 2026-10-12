# Review record — template

One record per review, posted in the PR. A review is of **one head sha**; if the head moves, the record is void
and the review is redone against the new head. Copy the block below and fill every field: a field you cannot
fill is itself the finding, so write "not checked, because ..." rather than leaving it blank.

The sign-off line is the reviewer's own, and it rests on a line-by-line reading of that head. "Looks good" is
not a verdict, and neither is a recommendation: only one of the three forms below counts.

---

````markdown
SIGN-OFF #<PR> <sha> approve

## Review record

**PR** <owner>/<repo>#<N> — <title>

The sign-off line above is **the first line of the post**, on a line of its own, with nothing else on it.
`<sha>` is the PR's current head. Exactly one of these three forms, and no other wording:

```
SIGN-OFF #<PR> <sha> approve
SIGN-OFF #<PR> <sha> approve (code review)
SIGN-OFF #<PR> <sha> changes
```

Use `approve (code review)` when the verdict rests on reading the code rather than on a build or run you
performed; the next line then gives the runtime evidence relied on. For `changes`, the next line gives the
reason. One sign-off per (PR, sha) — **any push resets every sign-off on the PR**.

| | value | how it was read | UTC |
|---|---|---|---|
| head | `<40-char sha>` | `gh pr view <N> -R <owner>/<repo> --json headRefOid` | <time> |
| tree | `<40-char sha>` | `git rev-parse <head>^{tree}` | <time> |
| base | `<40-char sha>` | `git ls-remote <url> refs/heads/<branch>` | <time> |
| base re-read | unchanged / moved to `<sha>` | same command | <time> |
| code pin | `<40-char sha>` | `doc/tech-report/code_pin.yml` | <time> |

**Gates** — run on this head, compared against the base.

| gate | base | head | verdict |
|---|---|---|---|
| `code_anchors.py check` | <n> found, <n> distinct, <n> unresolved | | |
| `check_citations.py` | <n> citations, <n> problems | | |
| `check_math_spans.py` | | | |
| `check_table_cells.py book/` | | | |
| generators (derivation, notation, test index, chapter list) | | | |
| `pytest tools/tests` | | | |
| `PYTHONPATH=src pytest src/tests` | | | |
| `render_gate.py book/` source gates | | | |

**Render** run `<id>`, `<conclusion>`, on head `<sha>`, `<start>` → `<end>`.
Link: <url>

**Reviewer context** (STYLE.md 11.3)

- [ ] I did not write this chapter and was not in its drafting conversation (**fresh context**). If I was,
      say so here — the record is still useful, but it does not satisfy 11.3(a).

**Blind restatement** — **[N: to be set]** sampled claims, restated in my own words before re-reading the
author's framing, and confirmed or corrected by the author.

*N has not been set. Xi or the editor sets it; do not pick a number locally. Until it is set, state how many
claims you sampled and how you chose them, so the record is still auditable.*

| # | claim, as I restate it | author: confirms / corrects |
|---|---|---|

**Read** — what I actually read, not what I assume.

- Files read line by line: <list>
- Claims checked against the code at the pin: <n>, of which <n> I re-derived or re-ran
- Claims I could not check, and why: <list>

**Findings**

| # | file:line | severity | what is wrong | what I would do |
|---|---|---|---|---|

Severity: **blocking** (wrong at the pin, or a gate goes red), **should-fix** (true but misleading, or style
rule broken), **note** (observation, no action needed).

**Not checked** — state plainly.

- <e.g. the render could not be reproduced locally: quarto is not installed on this host, so the render is CI's word>
- <e.g. kintera/pyharp citations have no code pin and no gate; I read them by hand / did not read them>

**Verdict, in prose** — one sentence giving the single strongest reason, below the record. This does not
replace the sign-off line at the top; that line is the verdict of record and this is its justification.
````

---

## Notes on filling it

- **Read the head immediately before posting.** If it moved while you were reviewing, say so and do not post a
  verdict on a sha that is no longer there.
- **There is no separate recheck-after-fixes step.** Any push resets every sign-off, so a fix pushed after
  this record invalidates it and the review is redone against the new head. That is why the record is pinned
  to one head sha rather than to a PR number.
- **Gate numbers are a pair.** A single column proves nothing: 163 problems is fine if the base had 163.
- **A claim you did not check is not a claim you approved.** The "could not check" list is the honest part of
  the record and the one reviewers most often skip.
- **Citations whose symbol changed at the pin** get read first (STYLE.md 3.1, provisional clause): a changed
  body is the usual reason a sentence has quietly gone false.
- The record is evidence, so it keeps its own provenance: every number in it names the command that produced it.
