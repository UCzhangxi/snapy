C0 started
STYLE.md, NOTATION.md drafted (round 1)
D section: check (10/10 pass) and figure committed; prose in progress
OUTLINE.md generated from five research inventories + ch6 (152 schemes, 439 citations resolve)

# Round 1 status (C0)

## Delivered
| item | file | state |
|---|---|---|
| style guide | `STYLE.md` | draft for review |
| notation | `NOTATION.md` | draft for review |
| outline | `OUTLINE.md` | for the lead's review, then the owner's approval |
| review of the D section | (one adversarial review against the code; 20 findings, all applied) | done |
| worked example (D) | `chapters/06-gravity-energy/D_face_work_pe.md` | draft, six layers |
| its check | `chapters/06-gravity-energy/checks/d_face_work_pe_check.py` | 11/11 claims pass |
| its figure | `chapters/06-gravity-energy/figures/fig_D_face_work_pe.py` (+ `.png`) | rebuilds bit for bit |
| shared figure style | `chapters/common/figstyle.py` | |
| citation checker | `tools/check_citations.py` | NOT COMMITTED: it was written under `build/`, which snapy gitignores; to be re-pushed under `tools/` |

## Open questions for the lead
1. **Evidence at the pin.** This environment has no libtorch build, so no C++/Python test was run at `dae902b`. The D
   section quotes test numbers from the derivation note and tags each one "re-run". Who runs the pinned build, and
   where do the run logs go (proposal: `reviews/runs/<sha>/`)?
2. **Missing evidence in the gravity-work round.** The onset numbers of `curved-gravity-work-weight.md` §11.2 have no
   deck or run, and §11.3 and §11.4 are still placeholders ("to be filled by the lead"). Re-run from a committed deck,
   or drop them?
3. **Repository of the cited issue and PR numbers.** #296 is not a PR on UCzhangxi/snapy, so the D section takes it to
   be chengcli/snapy#296. #277, #252 and #261 are from `sources/gh__ISSUE_THREADS_*` and are assumed to be
   chengcli/snapy too. Please confirm.
4. **Naming.** The report calls the corrected-PE work "scheme D", after its leg. The derivation note calls it
   "option F", and that note's "option D" is a different, rejected weight. The section says so once. Keep "D", or
   use "corrected-PE work" only?
5. **Chapter changes.** Eight changes to the proposed chapter list (OUTLINE.md, "Changes ... and why"): splits of
   4, 7 and 14; sedimentation moved to 10; no separate 1/R chapter; out-of-snapy material moved to Appendix E. Approve?
6. **Author assignment.** Proposed in OUTLINE.md: C1 gets 1/3/14, C2 gets 2/9/10, C3 gets 4/5, C4 gets 7/8/11, C0
   gets 6/12/13/15-17.
7. **Code-side findings, for the owner and not for the report.** The research found:
   - the VIC always closes a column as a reflecting wall, whatever the x1 boundary;
   - the ghost-exchange order of `Mesh::forward` is the reverse of `MeshBlock::forward`;
   - no test covers `SNAP_X1_MASS_COVARIANCE`;
   - option defaults differ between the C++ structs and YAML;
   - `max_redo` cannot be set from YAML;
   - an orphan test runner, `run_example_mass_check.py`, is not registered.

   OUTLINE.md chapter 16 lists them. Should they become issues?
8. **Pin move.** When `next/final-batch` merges, the pins move to the merge sha. `tools/check_citations.py` then shows
   which citations moved, but line shifts must be fixed by hand. Proposal: a `tools/move_pin.py` that remaps line
   numbers with `git blame -C`. Decide before the authors start.
9. **Sign slip in a committed derivation.** `docs/derivations/curved-gravity-work-weight.md` §7 and §8.6 give the
   $E+\mathrm{PE}_d$ change under D as $-g_1\sum V\sigma^2s[\Delta\rho]$. It is $+$. The report's eq. (6.4.13) uses
   the corrected sign, and check C7 asserts it. The code is not affected. Should the note be corrected on
   `next/final-batch`? C0 does not touch other branches.

C0 DONE (round 1): see the commit message of the C0 DONE commit for the summary.
