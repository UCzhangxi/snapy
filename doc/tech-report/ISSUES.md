# Known gaps in sources/ (decided when the sources were prepared)

1. The gravity-work draft's Fig. 6 plots Mach/Courant boxes whose numbers were removed. Drop the figure; any replacement is regenerated from a committed script on snapy runs.
2. The draft's T1 numbers lack a deck and a sha. Mark them "missing evidence". The chapter author reruns them on the pinned sha or removes them.
3. The WB-reference spec numbers refer to an unresolved historical revision (full identifier unavailable; missing evidence). The chapter author re-measures them with tests/test_wb_ref4_order.py at the pinned sha.
4. The H2-dissociation EOS note cites a deck outside snapy. Drop that citation and keep the EOS physics with kintera evidence only.
5. Numbers from one-step harness runs on commits not in snapy were removed. The 1/R chapter rebuilds its table from the in-snapy closure run.
6. Carried over:
   - the S39-derived caption A/B swap and the "500.5x vs 50,050 %" wording;
   - ISSI deck naming;
   - Appendix A of the gravity-work draft, which is to be rebuilt from snapy evidence;
   - the figs/fig7* figures, which never ship.
7. Derivations that exist only as commit messages (e.g. #284, #285, #288) are re-derived from the code at the pinned sha, each with an executable check.
8. Local symbol, chapter 9 (`_x1profile.qmd`): $\varsigma$ for the $x_1$ profile of a diffusion coefficient
   (`nu_scale_x1`, `kappa_scale_x1`); NOTATION.md has none, and $s$ is the centroid slope. For the editor to add
   to NOTATION.md §8.
9. Local symbol, chapter 9 (`_relax.qmd`): $\alpha_{\mathrm f}$ for the at-face extrapolation weight of
   `relax-bot-temp` (code `a`). For the editor to add to NOTATION.md §8.
10. Local symbol, chapter 9 (`_sponge.qmd`): $\zeta$ for the depth fraction of a cell inside a sponge layer (code
    `eta`); $\eta$ is taken (NOTATION.md §1, §10). For the editor to add to NOTATION.md §8.

## Chapter 1 local transfer notation (draft)

`book/chapters/01-overview/_stage.qmd` proposes $J^{\mathrm d}_{i+1/2}$ for the time-integrated implicit dry transfer [kg] and $J^{\mathrm{tr}}_{n,i+1/2}$ for its upwind passive-tracer transfer [kg]. These avoid collision with $P$ (corrected potential energy) and $G$ (total mass flow). Superscripts $\mathrm{base}$, $\mathrm{entry}$ and $\mathrm{source}$ (with $\mathrm{carry}$ for the selected ratio) identify source-free, entry and source quantities. The editor should add or replace these in NOTATION and then remove the scheme's local-symbol note. Chapter 1 contains no new runtime measurement.

8. Chapter 12 local symbols awaiting notation integration: lateral face variance
   $\sigma^{2,\mathrm{face}}_i$ and cell-to-lateral-face centroid offset $\delta^{\mathrm{face}}_i$
   in the flux-covariance section. Neither replaces the cell variance or cell-minus-midpoint offset.
   Delete the local-symbol note when these enter NOTATION.md.
9. Chapter 12 distinguishes the mass-covariance setup guard from missing numerical accuracy evidence.
   The coverage matrix needs new runtime evidence for its explicitly listed combinations.
