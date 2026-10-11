# Tech report: chapter board

The one live list of who writes what. Kept by the PR lead, updated on every "taking X", draft PR, ETA or merge
posted in the Slack report thread. Read it here before you take work:
https://github.com/UCzhangxi/snapy/blob/tech-report/doc/tech-report/BOARD.md

Rules (Xi, 2026-10-10): the unit of work is a whole chapter. When you finish, take the TOP queue item and say
"taking X" in the report thread first. Open a draft PR into tech-report early. An owner silent 30 min past an ETA
loses the chapter to the next free person. Queue empty: cross-review a finished chapter.

Last update: 2026-10-10 18:4x PT, tech-report b043551

## In progress

| chapter | owner | state | ETA (PT) | PR |
|---|---|---|---|---|
| ch2 fixes, then ch13 (13.4 waits for #303) | @chengcli | ch2 fixes commit ready locally, checking before push | after the ch2 PR | - |
| ch7 Time integration (7.A + 7.B) | @gitlinffff | started | after the draft PR | - |
| ch14 Parallelism, GPU, restart/IO, reproducibility | @zoeyzyhu | started; #303-dependent parts as placeholders | after the draft PR | - |
| ch6 Gravity and energy: 6.1-6.3, 6.5 + 3 figure functions | @happysky19 | not yet acknowledged | - | - |
| Appendix D: environment-switch table | @XinyueWang05 | started (format-patch doc) | after sizing | - |

## Queue (take from the top)

1. Appendix B: derivation index (one row per scheme, exists / re-derive, with its check)
2. Appendix A: notation (NOTATION.md as a table)
3. ch05: the missing 1/R figure function
4. ch16 Known limits: last, from every chapter's Limits layer (OUTLINE ch16 lists the starting items)

## Waiting on chengcli/snapy#303 (join the queue when it merges)

6.4, 6.6, 12.8, 13.4, the ch15 rows for #303

## In the book

ch1, ch2, ch3, ch4, ch5, ch6 (scheme D only), ch8, ch9, ch10, ch11, ch12, ch15, Appendix C, Appendix E
