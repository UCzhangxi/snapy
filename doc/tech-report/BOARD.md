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

Last update: 2026-10-11 15:00 PT

## snapy code work (priority: bugs first; report work fills gaps)

Rule: post only when a task is DONE or BLOCKED (no "starting" or "in progress" posts). An owner silent 30 min past an
ETA loses the task to the next free person. Free? Take the top open row of your PR, else the report queue below.

States read with `gh pr view` on chengcli/snapy at 2026-10-11 21:47 UTC.

PR A = chengcli/snapy#303 (x1 direction): **merged** 2026-10-11 13:24 UTC as main `9ad0936779ae001dba65c9eafccaa7c058686c97`.

| task | owner | oracle | state |
|---|---|---|---|
| A1 small fixes: mp test header verb; doc line "face is the default"; doc :690 pe anchors; README torch 2.10.0; TORCH_WARN_ONCE periodic x1 + corrected PE; FindKintera message keeps the #121/#131 reasons | @chengcli | ctest pass set unchanged | accepted; in 9ad0936 |
| A2 face-flux covariance at internal x1 block seams | @chengcli | test_pref_local_seam with SNAP_FLUX_COVARIANCE=1 at 1e-12; the new test fails on the parent | accepted; in 9ad0936 (`test_pref_local_seam_flux_covariance`, tests/CMakeLists.txt:37-43) |
| A3 #302 VIC wall order ~2: cause, 2 h time box | @gitlinffff | (a) code defect + place + fix, or (b) property of the scheme + evidence | DONE: (b), O(dt h) from the first-order upwind VIC correction flux; in the #303 Limits and 6.6 item 7 |
| A4 independent check of A2 (RED parent / GREEN head + named risks) | @happysky19 | rule 14c | closed by the merge (result not recorded here) |
| A5 CUDA ctest on the final head; seam tests twice | @zoeyzyhu | switch-on gaps exactly 0 both runs | closed by the merge (result not recorded here) |
| sign-offs on the final head | @gitlinffff @happysky19 @zoeyzyhu | | closed by the merge |

PR B = chengcli/snapy#307 (passive scalars get the face-flux covariance rows; covariance default ON): **Ready**, head
`913d04982522375a8c5fecec85a23b3ad0c3ad0e`, review required.

| task | owner | oracle | state |
|---|---|---|---|
| B1 scalar totals leak 5e-10 across a cubed-sphere panel seam with the covariance on (test_flux_positivity_cubedsphere*): find where | @happysky19 (read-only diagnosis first) | the face where the scalar flux and the corrected hydro dry-mass flux disagree, with numbers | DONE: panel-seam fix in 9ad0936, test `test_flux_positivity_cubedsphere_flux_covariance_python` (tests/CMakeLists.txt:269-276) |
| B2 covariance rows in src/scalar/scalar.cpp, mirroring the hydro tracer rows (hydro_forward.cpp:166-175) | @zoeyzyhu | a scalar and the same tracer carried as a hydro species agree to round-off | in #307: 1.05e-15 (Cartesian), 1.29e-15 (one cubed-sphere face block) against 1e-12; x1-split fix in the same PR |
| B3 #289 item 3: size of the compositional-buoyancy effect (derivation, text) | @gitlinffff | written estimate in the thread | report text and check script: queue item 2 below |
| B4 covariance on: one CUDA run and one implicit deck | @zoeyzyhu | CUDA == CPU; implicit stable | open: #307's body reports no CUDA run and no implicit deck |
| B5 default ON + test sweep | lead | ctest pass set as before | in #307: `SNAP_FLUX_COVARIANCE` defaults to 1; CPU ctest 118/120 (main 42e941d: 116/118), the same two failures on both |

PR C = chengcli/snapy#291 (GPU step 1.54x slower; issue open)

| task | owner | oracle | state |
|---|---|---|---|
| C1 RECORD_FUNCTION timings, small 2-D deck and a production-size block, 2.10.9 vs 2.11.2 | @gitlinffff | per-phase table | DONE (accepted) |
| C2 cheap fixes: meters only on output cycles, one device read in check_redo, fewer .item() | @gitlinffff (v2), @chengcli (PR) | bitwise equal outputs | merged as chengcli/snapy#306, main `42e941dc11c88e7c7a3c61483d13d0d8d5a8697d` (2026-10-11 18:29 UTC): one device read in check_redo, `.item()` per step 40 -> 24 on the GPU 2-D deck, bitwise equal to 9ad0936 on CPU over 100 steps; the meters change is not in #306 |


## Report: in progress

| chapter | owner | state | ETA (PT) | PR |
|---|---|---|---|---|
| BOARD refresh + the #303-touched statements moved to main 9ad0936 | @gitlinffff | draft PR, render CI before Ready | - | this PR |

## Queue (take from the top)

1. BOARD refresh + stale #303 statements at 9ad0936: @gitlinffff, in progress (see the table above).
2. B3 as text in the covariance section (the two independent derivations of R, O(dz^2), dz cancels in R) with a
   check script in src/snapy_report: @gitlinffff, open.
3. After chengcli/snapy#307 merges: its content (scalar covariance rows, the x1-split scalar fix, the positivity gate
   on the covariance rows, default ON, the pre-B1 seam artefact as a lesson): @gitlinffff, open; waits on the merge.

Done since the last update: ch2 fixes (#48, @chengcli); ch05 1/R figure (#46).

Credit: the ch10/ch14 cross-review merged in #49 is Zoey Hu's (@zoeyzyhu) review; the PR was opened by @happysky19.

## Done after chengcli/snapy#303 merged (main 9ad0936)

6.4, 6.6, 12.8, 13.4, ch14 (two), ch16 (three), the ch15 rows for #303 (ch03, ch05, ch11, ch12 tables), plus the `gravity-work` default lines in ch06/ch12; these sections cite main 9ad0936, the rest of the book stays at the pin e894700.

## In the book

ch1, ch2, ch3, ch4, ch5, ch6 (6.1-6.6 and D; 6.4/6.5/6.6 at main 9ad0936), ch7 (#35), ch8, ch9, ch10 (#49, Zoey Hu's cross-review), ch11, ch12, ch13 (#38; 13.4 at main 9ad0936; App B gaps for ch7/9/13 #40), ch14 (#34; #49 cross-review; #303 items at main 9ad0936), ch15, ch16 (#39, #42: ch13 Limits folded in, 150 items; #303 limits at main 9ad0936), Appendix C, Appendix A, Appendix B (#36), Appendix D, Appendix E
