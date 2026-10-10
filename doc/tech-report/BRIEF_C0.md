# Brief for C0, the architect/editor: report skeleton (round 1)

You are the architect and editor of the snapy Technical Report. This round you build the skeleton that the chapter
authors will write into. The authors are four other AIs, each in their own area. The project lead reviews your work,
then the project owner (Xi) approves the outline before drafting starts.

## The standard
The report should be as detailed as the WRF, MPAS and CESM technical notes, and easier to learn from. A reader should
be able to learn the model from it and find every scheme in the code.

Every scheme is written in the same six layers, in this order:
1. **Summary.** What the scheme does, why it is there, and when it is on (switch or config key, default).
2. **Derivation.** The full derivation, step by step, from the continuous equations to the discrete form. No "it can
   be shown".
3. **Numerical method.** The discrete method: stencils, faces versus cells, ghosts, walls, seams, and the order of
   accuracy.
4. **Code.** Where it lives, as `path:line@sha`, with the function names and the switch.
5. **Tests.** The tests and the verification evidence: test name, what it asserts, and its tolerance and where that
   tolerance comes from.
6. **Limits.** Its limits and known issues.

Every scheme also gets a clear cartoon: stencil, fluxes, faces, ghosts, walls. Figures are scripts (matplotlib or SVG)
that are committed and rebuildable. No hand-drawn images.

If an important derivation has no notes in sources/, re-derive it from the code at the pinned sha. Mark it
"re-derive" in the outline. Never skip it and never summarise it from memory. Every derivation has an executable check
(sympy or numpy) committed next to it.

Every number names its sha, deck and run. Every code citation must resolve at the pinned sha.

## Inputs
- `doc/tech-report/sources/`: cleaned notes, derivations, PR bodies and issue threads. Read them for content, but
  check every claim against the code.
- `doc/tech-report/ISSUES.md`: known gaps in the sources.
- Code:
  - snapy `main` (this branch is based on chengcli/snapy main aea71ed).
  - The gravity-work round, which is not merged yet: `next/final-batch` on this fork (UCzhangxi/snapy). It holds the
    reference state with the wall closure, the gravity-work schemes (cell, face, D), the x1 and x2/x3 flux
    covariances, the vertical implicit solver with D, the diffusion face coefficient, and their `docs/derivations/*`.
  - The pin moves to the merge sha later. Cite the branch sha you read.

## Deliverables this round (commit them under `doc/tech-report/`)
1. `STYLE.md`
   - The six-layer template with headings.
   - The citation format.
   - The figure standard: script layout, fonts, colour-blind-safe palette, labelled axes and units.
   - Equation and notation rules.
   - How executable checks are laid out.
2. `NOTATION.md`: every symbol used across chapters (state variables, grid indices, face and cell operators, averages,
   the reference state, gravity work and PE, covariance terms), one meaning each.
3. `OUTLINE.md`: chapter by chapter, then scheme by scheme. For each scheme give:
   - the one-line summary;
   - the derivations needed, each marked "exists: <source file>" or "re-derive from <path:line>";
   - the figures to draw, each in one line;
   - the code locations;
   - the tests.

   Proposed chapters (refine them, merge or split as you see fit, and say why):
   1. Overview and code map: how a step runs, CPU/GPU, tensors.
   2. Governing equations and thermodynamics: kintera EOS, species energies, saturation, consistency conditions.
   3. Grids and geometry: Cartesian, spherical-polar, cubed sphere, seams, decomposition.
   4. Spatial discretization: finite volume, PLM/WENO5/cp, LMARS, face versus cell averages, covariance and centroid
      corrections, curvature terms.
   5. Hydrostatic and well-balanced treatment: the reference state, balance_column, the 4th-order reference, the
      x1 centroid, the wall closure, rest states.
   6. Gravity and energy: cell versus face gravity work, the fixer, the conservative face work with its PE (D), and
      what each conserves.
   7. Time integration: RK3, the vertical implicit solver, LU/pivot tolerance, CFL, redo/reject.
   8. Positivity, floors and limiters.
   9. Diffusion, viscosity, sedimentation and forcing.
   10. Moist physics coupling.
   11. Boundary conditions.
   12. Build-time switches and configurations: a matrix of defaults and couplings, and test coverage per combination.
   13. Conservation budgets and diagnostics.
   14. Parallelism, GPU, restart/IO and reproducibility.
   15. Verification catalogue.
   16. Known limits.
   17. Appendices: notation, derivation index, test index.
4. One fully worked example section, `chapters/06-gravity-energy/D_face_work_pe.md`. It covers the conservative face
   gravity work with its corrected PE, the D scheme (SNAP_GRAVITY_WORK_RADIAL_EXACT), at the `next/final-batch` sha.
   - Write all six layers, including how D enters the vertical implicit solve.
   - Add one figure script with its rendered PNG.
   - Add one executable check (e.g. the E+P identity per step on a small column, in numpy, from the discrete
     formulas).

   This section is the model the chapter authors will copy, so make it the best section in the report.

## Rules
- Describe snapy only. Do not write about other models' code or cross-code comparisons. Do not include machine names,
  cluster paths or personal paths.
- Commit only under `doc/tech-report/` on the branch `tech-report`, and push only that branch. Never touch other
  branches or open a PR. Do not add AI attribution trailers.
- First action: push a one-line commit that adds "C0 started" to `doc/tech-report/STATUS.md`. This proves you can push.
- Commit and push often. The lead can only see what is pushed.
- When done, push a commit whose message starts with `C0 DONE:` and contains a 5-line summary: what is there, which
  derivations are marked re-derive, and open questions for the lead.

## Done means
Every scheme in OUTLINE.md has all four items: summary, derivations with their status, figures, and code plus tests.
The D example has all six layers, a rebuildable figure and a passing executable check.
