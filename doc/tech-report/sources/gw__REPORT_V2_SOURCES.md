> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Sources for the gravity-work tech report, version 2 (snapy round of 2026-10-09)

Version 2 adds #289 (PR #293), #292, and the next PR (legs W, D, G, K).
Every row: what it is, where it lives, the sha it was measured at. Append rows as work lands; never rewrite.

## Merged
| item | sha | evidence |
|---|---|---|
| #288 face work in VIC, curved grids | d59836d (v2.11.3) | upstream PR #288 |
| #292 VIC failed-solve rejection, relative pivot, float32 vicclamp (#290, #294) | e51bdc2 (v2.11.4) | deltas 80506f0 -> af6a3f8 -> 7a69bef |
| #293 = #289 item 2: x2/x3 face-flux covariance + centroid (SNAP_FLUX_COVARIANCE), exact cubed-sphere cell volume | aea71ed (v2.11.5), tree 0183dd10 | deriv__289-covariance-x3-curved.md (.tex) at aea71ed; gw__X2COV_RESULT_x2cov.md s11c-s11g |

## Derivations and analyses behind #293
- gw__X2COV_DERIVATION_x2cov.md (dry Cartesian original); gw__U3_DERIVATION_moist_x2_flux.md (moist form)
- Study branches: f1b3e74 study/289-covariance (study__289-covariance_derivations_draft.md); e2c3f57 study/289-allrows (all rows, rest balance; study__289-allrows_derivation.md)
- Commit afe9f6b: deriv__issue289_moist_covariance_verifier.md (independent moist check)
- gw__ONEOVERR_split_RESULT.md (face_replica.py): the ON face fluxes are O(h^4) including the h^2/R terms; the ON-OFF rise of the 1/R coefficient comes from the centroid term

## The 1/R residual on spherical columns (diagnosis)
- study/next-1overR @ 10822ce (x1 centroid offset; study__next-1overR_README.md); study/next-1overR-remainder @ dcba4b2 (face work vs curv_flux1, conservative O(h^4) form with phi_c = g rbar; study__next-1overR-remainder_README.md)

## Next PR (base aea71ed)
| leg | switch | commit | notes / derivation |
|---|---|---|---|
| W 4th-order WB reference | SNAP_WB_REF4 | 1454878 code, 336101b order ctest, fdf895b derivation | spec gw__NEXTPR_spec_wbref_exact.md; order ~3 at 1/2/3/5 H |
| bryan.yaml BF02 constants | - | 5517876, 022d8c4 | BF02 appendix p.2928; exact consistency with h2o_bryan SVP (u0_R = -beta T_r, cv_l - cv_v - 1 = delta) |
| restart-test flake | - | b3a19d7 | UCX stdout interleave; 14/20 fail on main -> 20/20 |
| G x1 centroid offset (spherical-polar) | SNAP_X1_CENTROID_EXACT | 1cf0bbc | gw__NEXTPR_legG_REPORT.md; rest 2.4e-5 -> 1e-14 |
| D face gravity work, exact + E+P conservative | SNAP_GRAVITY_WORK_RADIAL_EXACT | 6499404 (code 5536c0a, PE diag b7ea6cb, test 3bd859e, docs 6499404) | gw__NEXTPR_legD_REPORT.md; gw__NEXTPR_legD_round3_NOTES.md; deriv__curved-gravity-work-weight.md s7-s8; 4-way: W and D must ship together |
| D independent Cartesian derivation (blind) | - | 2324ed7 | gw__NEXTPR_indep_cartesian_gravity_work_weight.md |
| K diffusion face coefficient (mean of products) | - | 4d3b4d7 | gw__NEXTPR_legK_REPORT.md; deriv__diffusion-face-coefficient.md |
| 1/R closure, all four on | - | c689274 = aea71ed+W+D 5536c0a+G 1cf0bbc | order 4 residual |

## Test catalog
- gw__CARTESIAN_TESTS.md (11 Cartesian tests with tolerances, decks, RED status)
