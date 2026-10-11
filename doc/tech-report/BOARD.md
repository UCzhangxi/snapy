# Tech report: chapter board

The one live list of who writes what. Kept by the PR lead, updated on every "taking X", draft PR, ETA or merge
posted in the Slack report thread. Read it here before you take work:
https://github.com/UCzhangxi/snapy/blob/tech-report/doc/tech-report/BOARD.md

Rules (Xi, 2026-10-10): the unit of work is a whole chapter. When you finish, take the TOP queue item and say
"taking X" in the report thread first. Open a draft PR into tech-report early. An owner silent 30 min past an ETA
loses the chapter to the next free person. Queue empty: cross-review a finished chapter.
Hand-in: when the chapter is done, mark your own PR "Ready for review"; ready PRs whose render CI is green on
their exact head are merged; drafts are not.

Last update: 2026-10-10 22:3x PT, tech-report 17a926a

## In progress

| chapter | owner | state | ETA (PT) | PR |
|---|---|---|---|---|
| ch2 fixes, then ch13 (13.4 waits for #303) | @chengcli | ch2 fixes commit ready locally, checking before push | after the ch2 PR | - |
| ch7 Time integration (7.A + 7.B) | @gitlinffff | 7.1-7.3 done, rebased; scoped 7.4-7.13 + ch15 rows | ~8 working h (author estimate, 22:0x) | #35 (0238189) |
| ch6 Gravity and energy: 6.1-6.3, 6.5 + 8 figure functions (incl. fig_deps, fig_dwork_stencil, fig_dwork_order) | @XinyueWang05 | DRAFT COMPLETE (commit 7f736dc, +1417); patch docs 9 of 11 received, then applied via CI render | done | patch 7f736dc |
| Appendix A: notation (NOTATION.md as a table, with the 2 NOTATION issues from ch6) | @zoeyzyhu | assigned 22:2x | - | - |
| Appendix D: environment-switch table | @XinyueWang05 | both patch parts received; being applied (render CI first) | review + ~30 min fixes | patch eda1ea4 |

## Queue (take from the top)

1. ch05: the missing 1/R figure function
2. Fill the gaps the Appendix B index shows: 21 equations without a code tag, 75 rows without a check (by chapter owner)
3. ch16 Known limits: last, from every chapter's Limits layer (OUTLINE ch16 lists the starting items)

## Waiting on chengcli/snapy#303 (join the queue when it merges)

6.4, 6.6, 12.8, 13.4, the ch15 rows for #303

## In the book

ch1, ch2, ch3, ch4, ch5, ch6 (scheme D only), ch8, ch9, ch10, ch11, ch12, ch14 (#34; 2 #303 placeholders), ch15, Appendix C, Appendix B (#36), Appendix E
