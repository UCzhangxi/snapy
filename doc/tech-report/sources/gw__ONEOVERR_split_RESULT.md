> Sanitized source copy for the snapy technical report; provenance in MANIFEST.md.

# Does #293's ON-OFF 1/R shift (in excess*R/H_b) follow from a complete O(h^2) curved correction?

Code read: snapy 668a647 (= 6719873 + review fixes), `_flux_covariance` and the p* block in
`src/hydro/hydro_forward.cpp`, `radial_face_moment2_` / `radial_face_centroid_shift_` in `src/coord/coordinate.cpp`,
derivation `docs/derivations/289-covariance-x3-curved.md` sections 1A, 2A, 4B. Scripts here: `face_replica.py`,
`entropy_split.py` (seconds). Two hypotheses: H1, ON-OFF is the removal of the curvature part of the face-average
error and the face fluxes are otherwise complete; H2, a missing or mis-signed h^2/R term in the face fluxes.
**Verdict: H1** (face fluxes complete to O(h^4) incl. h^2/R).

## 1. Face-flux truncation, Cartesian part + 1/R part (h = dr, s2 = h^2/12, delta = r_v - r_c = s2/r + O(h^4/r^3))
Cell values are r^2-weighted averages (Favre for u, h); the face flux needs the r-weighted average. Expanding about
the face area centroid (derivation 2A), for the rows the linear problem sees:

| row | exact face avg - OFF code flux (= what ON adds) | Cartesian part | 1/R part |
|---|---|---|---|
| energy | s2 rho h' u' - delta (rho h u)' | s2 rho h' u' | -(s2/r)(rho h u)' |
| mass | -delta (rho u)' | 0 | -(s2/r)(rho u)' |
| normal momentum (p part) | -delta p' | 0 | -(s2/r) p' (mirrored in the lateral source) |

ON flux error = O(h^4) in every row (momentum's rho u'^2 covariance is quadratic, excluded by design).

**What an entropy diagnostic sees** (rho T S_t = E_t - h0 rho_t at linear order about rest):
dF_s = dF_E - h0 dF_rho = s2 rho0 h0' u' - delta rho0 h0' u = **s2 rho0 h0' r d/dr(u/r)** -- the face-average
error of the curved column is the covariance of the ANGULAR velocity u/r, not of u. OFF misses all of it; ON
removes all of it. The 1/R piece -s2 rho0 h0' u/r has the opposite sign to the Cartesian piece for a mode
whose u' and u/r project with the same sign, which is the partial cancellation H1 postulates.
Isothermal (h0' = 0): dF_s = 0 for BOTH parts, and exactly so on the coded stencils (enth = rho h0 per cell).

## 2. Numeric check of the face fluxes (`face_replica.py`)
Smooth nonlinear profiles on the T4 polytrope (n_rho 2, gamma 5/3, Lz = 2.794, H_b = 1.5175), 24-point
Gauss-Legendre cell/face integrals, coded s2, delta, x1v and centred D1. Max interior error:

| R_b/H_b | row | n=32 | 64 | 128 | 256 | ON err*n^4 |
|---|---|---|---|---|---|---|
| 5 | energy ON | 3.87e-6 | 2.52e-7 | 1.61e-8 | 1.02e-9 | 4.06 -> 4.36 |
| 5 | energy cov-only | 7.78e-4 | 2.02e-4 | 5.16e-5 | 1.30e-5 | (O(h^2): centroid missing) |
| 5 | mass ON | 1.17e-7 | 7.32e-9 | 4.58e-10 | 2.86e-11 | 0.123 |
| 5 | pressure ON | 1.67e-7 | 1.05e-8 | 6.56e-10 | 4.10e-11 | 0.176 |
| 1000 | energy ON | 3.89e-6 | 2.50e-7 | 1.59e-8 | 1.02e-9 | 4.08 -> 4.36 |

Curvature part (spherical error minus the Cartesian twin's on the same z-profiles): OFF = (h^2/R) x const
(energy 0.77->0.83, mass 0.087->0.091, pressure 1.57->1.60 in units h^2/R, both R); ON = O(h^4), x16 per doubling
(R/H 5 energy: 1.17e-6, 7.3e-8, 4.6e-9, 2.9e-10). **H2 is ruled out for the face fluxes**: no missing or mis-signed
h^2/R term (face weight r, centroid term, p*, sigma_c^2, D1 on x1v, x1v = volume centroid all check out).

## 3. Predicted split (`entropy_split.py`; MODEL)
Response of the w-projected entropy tendency to dF_s, split into the centroid part (A ON - C ON) and the
covariance-row part (C ON - A OFF). Mode model: W = sin(pi z/Lz), U from continuity (Cartesian / spherical),
constant g, projection unweighted or r^2-weighted. In this model both parts have the sign opposite to the model's
own Cartesian ON-OFF response, for every R/H_b tried (5 to 1000) and both projections, and their sum in
excess*R/H_b units grows with R/H_b. The cov-row part is nonzero in "excess" units
although the covariance carries no explicit 1/R: the spherical mode (continuity, 1/r divergence) differs from the
Cartesian twin's at O(H/R). Coefficients depend on the seeded mode and projection weights; the signs do not.

## 4. Predictions for a measured split
- C ON - A OFF (covariance rows) and A ON - C ON (centroid + p*): each opposite in sign to the Cartesian ON-OFF;
  p* enters only via RK sub-stages.
- Isothermal deck: A ON - A OFF = 0 to linear order (both parts vanish in rho T S_t = E_t - h0 rho_t; discrete
  identity checked at 2.5e-23). A clearly nonzero isothermal ON-OFF would mean the diagnostic is not this entropy
  projection, or a p*/momentum effect through the RK stages -- not a face-flux defect.
- A 1/R residual common to ON and OFF lies outside the x2 face average: x1 fluxes/area-volume metric, geometric
  sources or the WB reference on the curved column (next PR).
