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

10. Chapter 2 local notation for editor reconciliation: species energy $e_n(T)$; tabulated constant
   capacity $c_{v,n}^{\mathrm{ref}}$; integration temperature $T_{\mathrm{int}}$; rotor level $J$,
   Boltzmann constant $k_{\mathrm B}$, and normalized finite-ensemble brackets; shallow-water depth-like
   state $d_{\mathrm{sw}}$; reaction extent $\zeta_k$, linearized residual $\mathbf b$, Jacobian $\mathsf J$,
   and KKT multipliers $\boldsymbol\lambda$. Owners: Chapter 2 / editor. Remove local notes when settled.
11. NOTATION section 2a's sentence describes the API tensor `V` as molar concentration, but at the pinned
   snapy code `MoistMixtureImpl::_adiabatic_index` multiplies `V` by inverse molar mass before using it.
   Chapter 2 describes `V` as partial mass densities and reserves the existing concentration symbol for
   the converted tensor. Editor should reconcile that sentence without changing the mathematical symbols.
12. Chapter 2 source inventory corrects the commented-out 14-variable test in OUTLINE section 2.3.
    The draft does not treat it as active coverage. Publication follow-ups: compiled H2 heat-capacity plot,
    moist-mixture temperature-map regression, active-set evidence, editor skeleton integration and renders.


## Chapter 11 local notation and evidence

The boundary schemes propose these local symbols for notation-table integration:
`outflow`: $\mathbf W^{\mathrm{bg}}$ (saved initial boundary state, separate from the hydrostatic reference),
$v_{\mathrm{out}}$ (outward velocity), $Z_{\mathrm{ac}}$ (acoustic impedance), $a_\pm$ (acoustic perturbations),
$d_{\mathrm{ent}}$ (advected density combination), $\alpha_{\mathrm{bc}}$ (shared admissibility factor), and
$\delta q$ (difference from the saved boundary background; not the centroid offset $\delta_i$).
`solids`: $D_i(b,l)$ (minimum prefix flip count), $m_b$ (minimum run length),
$\mathrm{cost}_i(b)$ (candidate flip cost), and $\mathsf H$ (normal reflection matrix).
Remove the local-symbol notes once the shared notation table incorporates these concepts.

Runtime gaps: outflow/WB/VIC and corner combinations, periodic solid closure, scalar/diffusion coupling
through solids, and at least three-resolution wall-reference convergence. These are missing evidence,
not measured defects. The source tests and report formula checks are separated in the Chapter 15 catalogue.

## Chapter 10 local symbols (draft)

Owners: chapter 10 / editor. Each scheme file lists its symbols in a "Local symbols" line; remove that line when the
symbol enters NOTATION.md.
- `_borrow.qmd`: $\mathcal P_c$, the parent-vapour set of condensate $c$.
- `_fixvapor.qmd`: $\mathcal M$, the window of $x_1$ cells one scan step of the column repair rewrites.
- `_kinetics.qmd`: $\dot{\boldsymbol\omega}$, reaction rates; $\mathsf J_{\dot\omega}$, their concentration Jacobian
  (subscripted to stay apart from chapter 2's $\mathsf J$); $x$, the two-product evaporation extent.
- `_tracer.qmd`: $b$, the tracer upper bound; $F_n$, $F_{\mathrm d}$, the $x_1$ face fluxes of tracer $n$ and of dry air.
- `_sed.qmd`: $a_n$ particle radius, $\rho_{\mathrm p,n}$ particle density, $\beta_n$ Cunningham factor, $\lambda$ mean
  free path, $\mathrm{Kn}$ Knudsen number, and $m$, $d$, $\epsilon$ for the background gas's molecular mass, diameter
  and Lennard-Jones well depth ($k_{\mathrm B}$ as in chapter 2).
