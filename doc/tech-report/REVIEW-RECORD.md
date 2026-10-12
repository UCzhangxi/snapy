# Review record — template

One record per review, posted in the PR. A review is of **one head sha**; if the head moves, the record is void
and the review is redone against the new head. Copy the block below and fill every field: a field you cannot
fill is itself the finding, so write "not checked, because ..." rather than leaving it blank.

The verdict line is the reviewer's own, and it rests on reading that head. "Looks good" is not a verdict.

---

```markdown
## Review record

**PR** <owner>/<repo>#<N> — <title>

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

**Verdict** — approve / changes, with the reason in one sentence.
```

---

## Notes on filling it

- **Read the head immediately before posting.** If it moved while you were reviewing, say so and do not post a
  verdict on a sha that is no longer there.
- **Gate numbers are a pair.** A single column proves nothing: 163 problems is fine if the base had 163.
- **A claim you did not check is not a claim you approved.** The "could not check" list is the honest part of
  the record and the one reviewers most often skip.
- **Citations whose symbol changed at the pin** get read first (STYLE.md 3.1, provisional clause): a changed
  body is the usual reason a sentence has quietly gone false.
- The record is evidence, so it keeps its own provenance: every number in it names the command that produced it.
