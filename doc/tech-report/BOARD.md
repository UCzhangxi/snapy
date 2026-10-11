# Tech report: chapter board

The one live list of who writes what. Kept by the PR lead, updated on every "taking X", draft PR, ETA or merge
posted in the Slack report thread. Read it here before you take work:
https://github.com/UCzhangxi/snapy/blob/tech-report/doc/tech-report/BOARD.md

Rules (Xi, 2026-10-10): the unit of work is a whole chapter. When you finish, take the TOP queue item and say
"taking X" in the report thread first. Open a draft PR into tech-report early. An owner silent 30 min past an ETA
loses the chapter to the next free person. Queue empty: cross-review a finished chapter.
Hand-in: when the chapter is done, mark your own PR "Ready for review"; ready PRs whose render CI is green on
their exact head are merged; drafts are not.

Last update: 2026-10-10 21:28 PT, tech-report 798884d

## In progress

| chapter | owner | state | ETA (PT) | PR |
|---|---|---|---|---|
| ch2 fixes | @chengcli | commit ready locally, checking before push (Cheng is on #303 first) | after #303 work | - |
| ch05: the missing 1/R figure (fig_oneoverr_remainder; needs a pinned snapy run) | @XinyueWang05 | drafted (commit 6cc7079); waiting on its delivery (uploads fail; author's choice: fix uploads or push from her fork) | - | - |

## Queue (take from the top)

1. Fill the gaps the Appendix B index shows (in progress: ch7/9/13 #40, ch3/8/11/12 + D rows @happysky19): 21 equations without a code tag, 75 rows without a check (by chapter owner)

## Waiting on chengcli/snapy#303 (join the queue when it merges)

6.4, 6.6, 12.8, 13.4, the ch15 rows for #303

## In the book

ch1, ch2, ch3, ch4, ch5, ch6 (6.1-6.3, 6.5 and D; 6.6 placeholder), ch7 (#35), ch8, ch9, ch10, ch11, ch12, ch13 (#38; 13.4 placeholder), ch14 (#34; 2 #303 placeholders), ch15, ch16 (#39; 3 #303 placeholders), Appendix C, Appendix A, Appendix B (#36), Appendix D, Appendix E
