# The O(h²/R) term in snapy's spherical-polar x1 discretisation, and whether it is the curved-harness residual

**Base.** `chengcli/snapy` main `d59836d`. Every `file:line` below is at that
commit. PR #293 (`happysky19/snapy` `fix/289-flux-covariance-x3-curved` @ `6719873`)
is used only for its x2/x3 correction formula. `study/289-allrows/` on this branch
supplies the x2/x3 algebra.

**Question.** The teammate's one-step curved-harness test (spherical-polar column at
R ≈ 5H, cell-average IC, well-balanced reference fixed to 4th order) leaves a constant
O(h²) residual in eps_eff·nz² of about +0.27 to +0.48 at nz 128. The residual is the same
with the flux correction off and scales as 1/R. Which discrete term causes it?

**Scripts.** All of them together take under 20 s of CPU.

| script | output | what it does |
|---|---|---|
| `moments.py` | `moments.out` | sympy. The cell centroid offset, what snapy's x1 face formulas return on r²-averages, the hydrostatic scan step, the x1 pressure force. |
| `replica.py` | (module) | Numpy replica of main's mass and energy rows on a spherical-polar column, linearised about rest, giving the one-step eps_eff of `tests/test_horizontal_flux_covariance.py`. Every candidate term has its own switch. |
| `attribution.py` | `attribution.out` | Validates the replica in the Cartesian limit, takes the 1/R content arm by arm, checks the analytic prediction, and computes the continuum truth of the diagnostic. |
| `rest_force.py` | `rest_force.out` | The same offset seen in the x1 momentum row at rest, and its consistent form. |

---

## 0. Verdict

1. **The term.** On spherical-polar the cell value is an r²-weighted average, so it
   sits at `x1v` = r_v = r̄ + δ_v, with δ_v = 2r̄h²/(12r̄² + h²) = h²/(6r̄) + O(h⁴).
   Every x1 cell→face map in main is a uniform-grid formula, so each one returns the
   value at **r_f + δ_v**, not at r_f. That covers the WENO5/cp5 weights, the
   well-balanced scan and its anchor, the six-face `pref`, the two-point `dsf`,
   `curv_flux1` and the pressure force −(p₊−p₋)/dx1f. The face geometry (r_f², the
   volume, φ_f = g·x1f, φ_c = g·x1v) is evaluated at the true locations. The mismatch
   is O(h²/R), and it is present whatever the x2/x3 flux correction does.
2. **In eps_eff** (an entropy tendency, so only the mass and energy rows enter at
   O(h²)), the term has two parts.
   - The face velocity w(r_f + δ_v) gives ρTS = g ρ δ_v ∂_r w, which is
     **eps·nz² = +(g/6c_p)·(Σρww′/Σρw²)/R = +0.020/R** (eq. 3.4; the replica gives
     +0.022/R). It is positive, exactly 1/R, constant in nz, and independent of the
     x2/x3 correction. It vanishes identically with `gravity-work: face`.
   - The well-balanced reference faces p, ρ at r_f + δ_v contribute **−0.03 to −0.04/R**
     (cell work) and **+0.005/R** (face work).
3. **The consistent form** is to make each x1 cell→face map exact for the r² measure:
   - reconstruction weights that are exact for r² cell averages. Equivalently, a
     pre-shift ā − δ_v·D₁ā, good to O(h⁴);
   - the scan step g·h·(ρ_c − δ_v·D₁ρ_c) in place of g·ρ_c·dx1f;
   - the geometric pressure source (2/V)∫ r p̃ dr in place of (A₊p₊−A₋p₋)/V − (p₊−p₋)/dx1f.

   The x1 weights alone remove **98 %** of the 1/R content in eps_eff: +0.0224/R drops
   to +0.0004/R, and what remains is the 1/R part of the cell work's Cartesian O(h²)
   error. The force fix balances a cell-average column to round-off (1e-14), where
   main leaves −g·δ_v·ρ′. The three changes have to go together, or rest balance is
   lost.
4. **It does not explain the reported size.** Every arm puts at most **0.08/R** into
   eps·nz², which is about **+0.001 to +0.012 at R = 5**. The teammate's residual is
   +0.27 to +0.48, i.e. 1.4 to 2.4/R, which is 20 to 100 times larger. The momentum
   side (the rest imbalance −gδ_vρ′) cancels in seeded-minus-unseeded and reaches
   entropy only at O(h²·dt). So the reported residual is not this term, unless the
   harness differs from the one modelled here (§6).
5. **The diagnostic has its own 1/R term.** A Cartesian roll copied onto the sphere is
   not anelastic there, because div(ρv) contains 2ρw/r. For that roll the *continuum
   truth* of eps·nz² is **−0.12/R**, which is scheme-independent, O(h²) and 1/R. It has
   the wrong sign to be the residual, but it has to be subtracted before a scheme
   residual is read off (§6).

---

## 1. What eps_eff can see

The harness seeds velocity only, on a rest state, and differences the seeded and
unseeded one-step updates. To first order in amplitude, with the background at rest,

$$
\bar\rho\,T_c\,S=\dot E_{\rm int}-h_c\,\dot\rho,\qquad h_c=c_p\,\bar p/\bar\rho ,
$$

and this is linear in the velocity alone. Seeded p′ and ρ′ produce no linear entropy
tendency, because there is no background velocity to advect them. The KE terms are
second order. Over one RK3 step, S equals the instantaneous tendency plus O(h²·dt).
**So eps_eff is a projection of the mass-row and energy-row operators acting on the
initial velocity.** The momentum rows (the 2p/r and cotθ geometric sources, and the x1
pressure force) cannot enter at O(h²).

`replica.py` builds exactly this operator:

- x1: WENO5 in its smooth limit (5-point upwind, (wl+wr)/2 under LMARS at balanced faces), F_ρ = ρ_f·u, F_E = c_p·p_f·u;
- x1 divergence (A₊F₊ − A₋F₋)/V with A = r_f² and V = (r₊³ − r₋³)/3;
- x3 = φ faces at the equator, which are exactly axisymmetric, with #293's correction optional, or the exact face average;
- cell or face gravity work, including `curv_flux1`;
- a well-balanced reference that is either exact, or main's (`hydro_ref_x1_impl.h`, `wb-wall-clamp` on).

In the Cartesian limit it is close to the harness (`attribution.out` A): off is −0.264,
−0.259, −0.254 at nz 16, 32, 64, inside the harness band [−0.32, −0.20]. On is −0.020,
−0.012, −0.007, against the recorded CART_REF of −0.013, −0.005, +0.000.

The seed is anelastic on the sphere: ρw = k sin(πz)(R/r)² cos mφ and
ρu_φ = −π cos(πz)(R/r) sin mφ, with m = kR. The continuum truth of the diagnostic for it
is **exactly 0**, so anything left over is scheme error.

## 2. The offset (`moments.py`)

| | result | main |
|---|---|---|
| S1 | x1v − r̄ = 2r̄h²/(h² + 12r̄²) = h²/(6r̄) − h⁴/(72r̄³) | `spherical_polar.cpp:20` (volume centroid, which is correct as a centroid) |
| S2 | upwind-5 and central-6 on r²-averages: face value = a(r_f) + δ_v a′ + O(h³) | `interp_simple.hpp` weights, `hydro_forward.cpp:109` (no x1 metric) |
| S2 | scan step g·h·ρ_c − g∫ρ dr = g·h·δ_v·ρ′, so the scanned faces are at r_f + δ_v (the anchor at `:37` adds the same δ_v at the top) | `hydro_ref_x1_impl.h:37,43,53` |
| S3 | −(p₊−p₋)/h − ⟨−∂_r p⟩_{r²} = +δ_v p″ | `spherical_polar.cpp:236` |

`rest_force.py` (b) confirms the scan numerically: main's well-balanced face pressure is
p(r_f) + δ_v p′(r_f). The quantity R·nz²·max|Δp_f| is 0.1666, which is 1/6.

## 3. The term in eps_eff

**x1 weights, cell work.** The face velocity is biased by δ_v w′. Both rows carry it in
proportion: ΔF_E = h_f·ΔF_ρ, with ΔF_ρ = ρ δ_v w′. Then

$$
\rho T S \;=\; -\nabla_1\!\cdot(h\,\Delta F_\rho)+h_c\,\nabla_1\!\cdot\Delta F_\rho
\;=\; -h'\,\Delta F_\rho \;=\; g\,\rho\,\delta_v\,\partial_r w ,
\tag{3.1}
$$

$$
\varepsilon\,n_z^2 \;=\; \frac{g}{6c_p}\,\frac{1}{R}\,\frac{\sum\rho\,w\,w'}{\sum\rho\,w^2}
\;=\;\frac{g}{12\,c_p R}\Big\langle -\frac{\rho'}{\rho}\Big\rangle_{\rho w^2}+O(R^{-2}).
\tag{3.4}
$$

For the isentropic column, (3.4) gives +0.0199, +0.0200, +0.0201, +0.0201 times 1/R at
R = 5, 10, 20, 40. The replica gives +0.0220, +0.0212, +0.0207, +0.0204
(`attribution.out` D). They agree to O(1/R²).

**Face work.** φ_c = g·x1v. The adiabat with constant g has h_f − h_c = −g(r_f − x1v)
plus a Cartesian O(h²) covariance. So the advective part and the face work cancel
**for any face mass flux F**:

$$
-\tfrac1V\textstyle\sum_\pm \pm A_\pm F_\pm\big[(h_\pm-h_c)+g(r_\pm-x1v)\big]
=-(h(x1v)-h_c)\,\nabla_1\!\cdot F .
$$

The x1-weight bias therefore drops out identically, and the replica's `face` rows do not
change with the x1 weights (table B).

**Well-balanced reference.** With the faces at r_f + δ_v, h_f = h(r_f) − gδ_v. This gives
ρTS = g∇₁·(δ_v F) ≈ gδ_v ∇₁·(ρw) ≈ −gδ_v∇_h·(ρu). The term is nearly orthogonal to w
in the projection. The replica gives −0.03 to −0.04/R with cell work and +0.005/R with face work.

**1/R content, R·[eps·nz²(R) − eps·nz²(∞)], nz 64** (`attribution.out` B; arms with the
#293 x2/x3 correction):

| arm | R=5 | R=10 | R=20 | R=40 |
|---|---|---|---|---|
| cell work, x3 off | +0.058 | +0.069 | +0.075 | +0.078 |
| cell work, x3 #293 | **+0.0226** | +0.0218 | +0.0213 | +0.0211 |
| face work, x3 #293 | +0.006 | +0.001 | −0.002 | −0.003 |
| cell, x3 #293, main's WB reference | −0.009 | −0.016 | −0.019 | −0.022 |
| **fix: cell, x3 #293, r² x1 weights** | **+0.0006** | +0.0006 | +0.0006 | +0.0007 |

Convergence at R = 5 (table C), cell work with x3 #293: +0.0231, +0.0226, +0.0225,
+0.0225 at nz 32 to 256, so the term is O(h²) with a constant coefficient. With r²
weights it is +0.0010, +0.0006, +0.0004, +0.0004. The +0.0004 left over is the 1/R part
of the scheme's own Cartesian O(h²) error (−0.005 in Cartesian, cell work). The metric
fix cannot remove it.

## 4. The same offset in the momentum row (`rest_force.py`)

Take a cell-average column with exact face pressures, i.e. a reference fixed to 4th
order. Main's net force −(p₊−p₋)/dx1f − gρ_c leaves **−gδ_vρ′**. That is O(h²/R):
R·nz²·max = 0.111 to 0.118, matching the prediction to O(h⁴). Main's own balanced state
avoids this only because its scan puts the faces at r_f + δ_v (S2). Main is
self-consistent at rest because flux and force make the same error, as in the θ row of
`study/289-allrows`.

The consistent force is −⟨∂_r p⟩_{r²}. With face data only, that means a geometric
source of (2/V)∫r p̃ dr, where p̃ is the degree-5 interpolant of the six nearest face
pressures. It balances the cell-average column to **1e-14**. This changes the rest
state, not eps_eff.

## 5. Exact consistent forms (what a fix PR would change)

1. **x1 reconstruction, spherical-polar only.** Use weights exact for the r² cell
   average: solve Σⱼ wⱼ⟨(r − r_f)ⁿ⟩_{r²,j} = δ_{n0} for n ≤ 4 on each 5-cell stencil.
   These are fixed per grid and can be precomputed like `x1v`. The cheaper equivalent
   is to reconstruct ā − δ_v·D₁ā, which is good to O(h⁴). `replica.recon_weights(…, "sph")`
   implements the first form.
2. **Well-balanced reference.** Use the scan step g·h·⟨ρ⟩ with ⟨ρ⟩ = ρ_c − δ_v·D₁ρ_c,
   and anchor at the face. Make `pref` the r² mean of the face interpolant, and give
   `dsf` the same r² weights as the perturbation reconstruction. One warning: making
   only `dsf` consistent leaves a product covariance (`replica` `ref="r2"`), which is
   worse than main's matched bias.
3. **x1 pressure force.** Use src1 = (2/V)∫r p̃ dr (§4).

   With 2 alone, the rest state is unbalanced at O(h²/R). With 3 alone, the column is
   unbalanced against main's scan. Ship 2 and 3 together. 1 is independent of them,
   and it is the only one that moves eps_eff with cell work.
4. Gnomonic: `x1v` is the arithmetic mid-radius there (`gnomonic_equiangle.cpp:36`),
   so δ_v = 0 in the stencils. The r² cell measure still puts the true centroid at
   r̄ + h²/(6r̄). The same term is present with "x1v" replaced by that centroid. This
   was not replicated here.

## 6. Why this is not (all of) the reported +0.27 to +0.48, and what to check

The term matches every qualitative signature in the brief: it is positive, scales as
exactly 1/R, is O(h²) with a constant coefficient, and does not depend on the x2/x3
correction. But (3.4) caps it at about +0.004 (R = 5, cell work), and every arm here
stays under 0.08/R. In the harness modelled here, nothing in main's mass and energy
rows reaches 1.4 to 2.4/R. The harness differences that could account for it:

1. **The seed.** A Cartesian roll copied onto the sphere compresses
   (div ρv ∋ 2ρw/r). The continuum truth of eps·nz² is then −0.1155, −0.1224,
   −0.1263, −0.1284 times 1/R at R = 5, 10, 20, 40 (`attribution.out` E). With the
   seed made anelastic on the sphere (§1), the truth is 0.
2. **Gravity-work mode.** With `face` work the x1-weight part is identically 0. If the
   residual does not change between `cell` and `face`, it is not in the x1 weights.
3. **Amplitude and dt.** The linear residual is independent of amplitude, and it does
   not change when dt is halved at fixed h. A dependence on either points to the rest
   drift or to nonlinear WENO weights acting on the WB perturbation (the cell-average
   IC is not main-balanced: §4 gives a w drift of about −gδ_vρ′·t).
4. **Reference.** Turn off "fixed to 4th order", i.e. use main's own scan. Per table B,
   the 1/R content then moves by −0.03/R.
5. **Projection.** Use the harness's own sums. A local S/w ratio near the walls picks
   up the WB O(h) wall artefact below.

Side observation (replica only, not checked in snapy): with `wb-wall-clamp` (default on),
the clamped binomial ρ/p near each x1 wall makes main's reconstructed face *density* at
the 2nd and 3rd faces from the wall O(h)-wrong. The error is Cartesian too: R·nz²·Δρ_f
doubles with nz. This could contaminate any non-interior projection.
