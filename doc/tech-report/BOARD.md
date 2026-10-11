# Tech report: chapter board

The one live list of who writes what. Kept by the PR lead, updated on every "taking X", draft PR, ETA or merge
posted in the Slack report thread. Read it here before you take work:
https://github.com/UCzhangxi/snapy/blob/tech-report/doc/tech-report/BOARD.md

Rules (Xi, 2026-10-10): the unit of work is a whole chapter. When you finish, take the TOP queue item and say
"taking X" in the report thread first. Open a draft PR into tech-report early. An owner silent 30 min past an ETA
loses the chapter to the next free person. Queue empty: cross-review a finished chapter.
Hand-in: when the chapter is done, mark your own PR "Ready for review"; ready PRs whose render CI is green on
their exact head are merged; drafts are not.

Last update: 2026-10-10 21:5x PT, tech-report 4e752ac

## In progress

| chapter | owner | state | ETA (PT) | PR |
|---|---|---|---|---|
| ch2 fixes, then ch13 (13.4 waits for #303) | @chengcli | ch2 fixes commit ready locally, checking before push | after the ch2 PR | - |
| ch7 Time integration (7.A + 7.B) | @gitlinffff | resumed 21:5x (the #303 check is done); 7.1-7.3 written, 7.4-7.13 to come | ~3-4 h from 21:5x (author estimate) | #35 (0238189) |
| ch6 Gravity and energy: 6.1-6.3, 6.5 + 3 figure functions (fig_deps, fig_dwork_stencil, fig_dwork_order) | @XinyueWang05 | scoped; writing after Appendix D is applied | ~10-12 working h (author estimate) | - |
| Appendix B: derivation index | @zoeyzyhu | CI green; adding the one-line statements and a pre-render step that regenerates the index | not yet given | #36 (7f83a98) |
| Appendix D: environment-switch table | @XinyueWang05 | drafted: 20 switches, 54 citations pass, full-book render clean vs base; patch docs to be applied by the lead | review + ~30 min fixes | patch eda1ea4 |

## Queue (take from the top)

1. Appendix A: notation (NOTATION.md as a table)
2. ch05: the missing 1/R figure function
3. ch16 Known limits: last, from every chapter's Limits layer (OUTLINE ch16 lists the starting items)

## Waiting on chengcli/snapy#303 (join the queue when it merges)

6.4, 6.6, 12.8, 13.4, the ch15 rows for #303

## In the book

ch1, ch2, ch3, ch4, ch5, ch6 (scheme D only), ch8, ch9, ch10, ch11, ch12, ch14 (#34; 2 #303 placeholders), ch15, Appendix C, Appendix E
