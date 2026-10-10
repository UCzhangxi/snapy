# Known gaps in sources/ (decided when the sources were prepared)

1. The gravity-work draft's Fig. 6 plots Mach/Courant boxes whose numbers were removed. Drop the figure; any replacement is regenerated from a committed script on snapy runs.
2. The draft's T1 numbers lack a deck and a sha. Mark them "missing evidence". The chapter author reruns them on the pinned sha or removes them.
3. The WB-reference spec numbers rest on commit c5b810d. The chapter author re-measures them with tests/test_wb_ref4_order.py at the pinned sha.
4. The H2-dissociation EOS note cites a deck outside snapy. Drop that citation and keep the EOS physics with kintera evidence only.
5. Numbers from one-step harness runs on commits not in snapy were removed. The 1/R chapter rebuilds its table from the in-snapy closure run.
6. Carried over:
   - the S39-derived caption A/B swap and the "500.5x vs 50,050 %" wording;
   - ISSI deck naming;
   - Appendix A of the gravity-work draft, which is to be rebuilt from snapy evidence;
   - the figs/fig7* figures, which never ship.
7. Derivations that exist only as commit messages (e.g. #284, #285, #288) are re-derived from the code at the pinned sha, each with an executable check.
