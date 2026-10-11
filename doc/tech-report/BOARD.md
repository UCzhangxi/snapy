# Tech report: chapter board

The one live list of who writes what. Kept by the PR lead, updated on every "taking X", draft PR, ETA or merge
posted in the Slack report thread. Read it here before you take work:
https://github.com/UCzhangxi/snapy/blob/tech-report/doc/tech-report/BOARD.md

Rules (Xi, 2026-10-10): the unit of work is a whole chapter. When you finish, take the TOP queue item and say
"taking X" in the report thread first. Open a draft PR into tech-report early. An owner silent 30 min past an ETA
loses the chapter to the next free person. Queue empty: cross-review a finished chapter.
Hand-in: when the chapter is done, mark your own PR "Ready for review"; ready PRs whose render CI is green on
their exact head are merged; drafts are not.

Last update: 2026-10-10 20:26 PT, tech-report 3b32a47

## In progress

| chapter | owner | state | ETA (PT) | PR |
|---|---|---|---|---|
| ch2 fixes | @chengcli | commit ready locally, checking before push (Cheng is on #303 first) | after #303 work | - |
| ch13 Conservation budgets and diagnostics (13.4 waits for #303) | @gitlinffff | reassigned from Cheng (busy on #303) | - | - |
| ch6 Gravity and energy: 6.1-6.3, 6.5 + 8 figure functions (incl. fig_deps, fig_dwork_stencil, fig_dwork_order) | @XinyueWang05 | DRAFT COMPLETE (commit 7f736dc, +1417); all 11 patch docs received; being applied (render CI first) | done | patch 7f736dc |
| ch05: the missing 1/R figure (fig_oneoverr_remainder; needs a pinned snapy run) | @XinyueWang05 | started | - | - |
| Appendix A: notation (NOTATION.md as a table, with the 2 NOTATION issues from ch6) | @zoeyzyhu | DRAFT COMPLETE (#37); lead's worker lands it after ch6 (pre-workflow base conflicts in _quarto.yml) | done | #37 |

## Queue (take from the top)

1. Fill the gaps the Appendix B index shows: 21 equations without a code tag, 75 rows without a check (by chapter owner)
2. ch16 Known limits: last, from every chapter's Limits layer (OUTLINE ch16 lists the starting items)

## Waiting on chengcli/snapy#303 (join the queue when it merges)

6.4, 6.6, 12.8, 13.4, the ch15 rows for #303

## In the book

ch1, ch2, ch3, ch4, ch5, ch6 (scheme D only), ch7 (#35), ch8, ch9, ch10, ch11, ch12, ch14 (#34; 2 #303 placeholders), ch15, Appendix C, Appendix B (#36), Appendix D, Appendix E
