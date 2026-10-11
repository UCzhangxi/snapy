# Tech report: chapter board

The one live list of who writes what. Kept by the PR lead, updated on every "taking X", draft PR, ETA or merge
posted in the Slack report thread. Read it here before you take work:
https://github.com/UCzhangxi/snapy/blob/tech-report/doc/tech-report/BOARD.md

Rules (Xi, 2026-10-10): the unit of work is a whole chapter. When you finish, take the TOP queue item and say
"taking X" in the report thread first. Open a draft PR into tech-report early. An owner silent 30 min past an ETA
loses the chapter to the next free person. Queue empty: cross-review a finished chapter.

Last update: 2026-10-10 20:1x PT, tech-report 9c2930c

## In progress

| chapter | owner | state | ETA (PT) | PR |
|---|---|---|---|---|
| ch2 fixes, then ch13 (13.4 waits for #303) | @chengcli | ch2 fixes commit ready locally, checking before push | after the ch2 PR | - |
| ch7 Time integration (7.A + 7.B) | @gitlinffff | PAUSED ~2 h for a #303 check (straka over-CFL); 7.1-7.3 written, 7.4-7.13 to come | ~3-4 h from 19:0x (author estimate) | #35 (0238189) |
| ch14 Parallelism, GPU, restart/IO, reproducibility | @zoeyzyhu | DRAFT COMPLETE, render green; to merge once the PR is out of draft (2 #303 placeholders) | done | #34 (226f978) |
| ch6 Gravity and energy: 6.1-6.3, 6.5 + 3 figure functions | @happysky19 | not yet acknowledged | - | - |
| Appendix B: derivation index | @zoeyzyhu | started | after the skeleton | - |
| Appendix D: environment-switch table | @XinyueWang05 | drafted: 20 switches, 54 citations pass, full-book render clean vs base; patch docs to be applied by the lead | review + ~30 min fixes | patch eda1ea4 |

## Queue (take from the top)

1. Appendix A: notation (NOTATION.md as a table)
2. ch05: the missing 1/R figure function
3. ch16 Known limits: last, from every chapter's Limits layer (OUTLINE ch16 lists the starting items)

## Waiting on chengcli/snapy#303 (join the queue when it merges)

6.4, 6.6, 12.8, 13.4, the ch15 rows for #303

## In the book

ch1, ch2, ch3, ch4, ch5, ch6 (scheme D only), ch8, ch9, ch10, ch11, ch12, ch15, Appendix C, Appendix E
