# Tech report: chapter board

The one live list of who writes what. Kept by the PR lead, updated on every "taking X", draft PR, ETA or merge
posted in the Slack report thread. Read it here before you take work:
https://github.com/UCzhangxi/snapy/blob/tech-report/doc/tech-report/BOARD.md

Owners off tonight: @XinyueWang05 (blocked); nothing waits on her.

Rules (Xi, 2026-10-10): the unit of work is a whole chapter. When you finish, take the TOP queue item and say
"taking X" in the report thread first. Open a draft PR into tech-report early. An owner silent 30 min past an ETA
loses the chapter to the next free person. Queue empty: cross-review a finished chapter.
Hand-in: when the chapter is done, mark your own PR "Ready for review"; ready PRs whose render CI is green on
their exact head are merged; drafts are not.

Last update: 2026-10-11 08:45 PT

## snapy code work (priority: bugs first; report work fills gaps)

Rule: post only when a task is DONE or BLOCKED (no "starting" or "in progress" posts). An owner silent 30 min past an
ETA loses the task to the next free person. Free? Take the top open row of your PR, else the report queue below.

PR A = chengcli/snapy#303 (x1 direction; face-flux covariance stays default OFF)

| task | owner | oracle | state |
|---|---|---|---|
| A1 small fixes: mp test header verb; doc line "face is the default"; doc :690 pe anchors; README torch 2.10.0; TORCH_WARN_ONCE periodic x1 + corrected PE; FindKintera message keeps the #121/#131 reasons | @chengcli | ctest pass set unchanged | accepted |
| A2 face-flux covariance at internal x1 block seams | @chengcli | test_pref_local_seam with SNAP_FLUX_COVARIANCE=1 at 1e-12; the new test fails on the parent | accepted |
| A3 #302 VIC wall order ~2: cause, 2 h time box | @gitlinffff | (a) code defect + place + fix, or (b) property of the scheme + evidence | DONE: (b), O(dt h) from the first-order upwind VIC correction flux; dt shrink recovers explicit; goes into the #303 Limits text |
| A4 independent check of A2 (RED parent / GREEN head + named risks) | @happysky19 | rule 14c | after A2 |
| A5 CUDA ctest on the final head; seam tests twice | @zoeyzyhu | switch-on gaps exactly 0 both runs | after A2 |
| sign-offs on the final head | @gitlinffff @happysky19 @zoeyzyhu | | after A5 |

PR B (on top of #303): passive scalars + face-flux covariance default ON

| task | owner | oracle | state |
|---|---|---|---|
| B1 scalar totals leak 5e-10 across a cubed-sphere panel seam with the covariance on (test_flux_positivity_cubedsphere*): find where | @happysky19 (read-only diagnosis first) | the face where the scalar flux and the corrected hydro dry-mass flux disagree, with numbers | open |
| B2 covariance rows in src/scalar/scalar.cpp, mirroring the hydro tracer rows (hydro_forward.cpp:166-175) | @zoeyzyhu | a scalar and the same tracer carried as a hydro species agree to round-off | open |
| B3 #289 item 3: size of the compositional-buoyancy effect (derivation, text) | @gitlinffff after A3 | written estimate in the thread | open |
| B4 covariance on: one CUDA run and one implicit deck | @zoeyzyhu | CUDA == CPU; implicit stable | after B2 |
| B5 default ON + test sweep (patch exists) | lead | ctest pass set as before | last |

PR C: chengcli/snapy#291 (GPU step 1.54x slower)

| task | owner | oracle | state |
|---|---|---|---|
| C1 RECORD_FUNCTION timings, small 2-D deck and a production-size block, 2.10.9 vs 2.11.2 | @zoeyzyhu after B2 and A5 | per-phase table | open |
| C2 cheap fixes: meters only on output cycles, one device read in check_redo, fewer .item() | after C1 | bitwise equal outputs | after C1 |


## Report: in progress

| chapter | owner | state | ETA (PT) | PR |
|---|---|---|---|---|
| ch2 fixes | @chengcli | commit ready locally, checking before push (Cheng is on #303 first) | after #303 work | - |
| ch05 1/R figure (fig_oneoverr_remainder) | @gitlinffff | pinned snapy run at e894700; render CI before Ready | - | #46 |

## Queue (take from the top)

1. ch05: the missing 1/R figure (fig_oneoverr_remainder; needs a pinned snapy run): @gitlinffff, in progress (see the table above).
2. Fill the gaps the Appendix B index shows (done: ch7/9/13 #40, ch1/2/4/5 #43 (16 left with stated reasons); ch3/8/11/12 + D rows @happysky19 #41 (ready, needs a reworded commit); ch10/14 #45 (8 left: 2 wait for #303, 6 with stated reasons)). Done.

## Waiting on chengcli/snapy#303 (merged; now waiting on the round-pin move)

6.4, 6.6, 12.8, 13.4, the ch14 and ch16 placeholders, the ch15 rows for #303

chengcli/snapy#303 merged on 2026-10-11 as `chengcli/snapy` main
`9ad0936779ae001dba65c9eafccaa7c058686c97` (squash; its tree
`8f90eca2e18df12938f754196c06550827ce4d86` equals the final review head `546b1af`), so the first half of the
condition on these rows is met. The second half is not: every one of these placeholders is written "once #303 has
merged **and the pin moves**", and the round pin of STYLE.md section 3.1 is still
`e894700ff7aee30b52882e5202b16461413780b0` (the #297 squash). Each row describes code that #303 changed, so it
cannot be written at the current pin, and STYLE.md section 3.1 reserves the pin move to the editor ("authors do
not edit shas by hand"). See `reviews/pin-move-9ad0936779ae001dba65c9eafccaa7c058686c97.md` for the survey: what
the move costs, which citations do not survive it, and the row-by-row block list. @happysky19 opened that survey
in #47; the rows themselves are not filled and stay open until the editor rules on the pin.

## In the book

ch1, ch2, ch3, ch4, ch5, ch6 (6.1-6.3, 6.5 and D; 6.6 placeholder), ch7 (#35), ch8, ch9, ch10, ch11, ch12, ch13 (#38; 13.4 placeholder; App B gaps for ch7/9/13 #40), ch14 (#34; 2 #303 placeholders), ch15, ch16 (#39, #42: ch13 Limits folded in, 150 items; 3 #303 placeholders), Appendix C, Appendix A, Appendix B (#36), Appendix D, Appendix E
