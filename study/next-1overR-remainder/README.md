# The 1/R remainder on spherical-polar: face-form gravity work, curv_flux1, and what is left

**Base.** `chengcli/snapy` main `d59836d`. Every `file:line` below is at that commit.
This follows `study/next-1overR/` (10822ce) on this branch. It answers the PR lead's
three questions about the teammate's harness facts (one-step eps_eff·nz², spherical-polar
column, polytrope deck, nz 128, excess = (spherical − Cartesian twin)·R/H_b).

**Scripts.** All of them together take under 10 s of CPU.

| script | output | what it does |
|---|---|---|
| `replica2.py` | (module) | `../next-1overR/replica.py` made deck-general: any polytrope (γ, index m, depth L, in units g = R_gas = T_b = 1, so R is in H_b), a w-shaped seed as well as the ρw-shaped one, the gravity-work arms `face` (main), `face-exact` (the teammate's exact-measure 2-face weights), `face-rbar` (the conservative O(h⁴) form of §4), curv_flux1 variants, an E+PE budget per φ column, and the split of ρTS into the three parts of the face-form identity (§2). Matches `replica.py` to round-off on the old deck. |
| `attribution2.py` | `attribution2.out` | Tables A to D below. |
| `conservation.py` | `conservation.out` | sympy for the per-face E+PE identities, plus the local order of each gravity-work form. |

Sign and units. Everything here uses the PR #293 harness sign (`tests/test_horizontal_flux_covariance.py`
on `pr293`) and H_b units. In that sign the face-weight term is **positive for any seed that
vanishes at the walls** (§1). The teammate's three facts all carry the opposite sign
(term −1.07, main −1.43, floor +1.72), so I compare them with −1 × theirs. Their deck is not
in the repo. The nearest is the Anders–Brown polytrope of `tests/test_wb_wall_corner.cpp`
(γ = 5/3, adiabatic, depth 2.17 H_b), called **AB** below. **L1** is the old γ = 1.4,
depth-1 deck. The units of their eps are not pinned either. The two ratios floor/term and
main/term do not depend on the eps normalisation, and floor/term does not depend on the roll's k,
so those ratios are what I compare.

---

## 0. Verdict

1. **(a) Partly.** The face-weight term is real and has exactly the teammate's form. The
   replica measures it equal to its analytic value, and it does reproduce the sign pattern
   (floor opposite in sign to main and term). But on the sphere **curv_flux1 cancels its
   dF/dr part at O(1/R)**. Main's face form + curv_flux1 has no 1/R gravity-work error, only
   +g·h²F/(6r²) at O(1/R²). Swapping in the exact-measure weights while keeping main's
   curv_flux1 moves the excess by −term, but it does so by **exposing curv_flux1's own metric
   error of the same size**, not by removing one. The replica does not reproduce the
   teammate's magnitudes: main/term is +5.9 (AB, ρw seed) or +0.89 (AB, w seed) against
   their +1.37, and floor/term is −4.0 or −2.0 against their −1.59. So their deck or seed is
   not the one modelled here.
2. **(b) Not ~0 in the configuration asked about (x2/x3 correction off).** The remainder is
   two named terms:
   - the 1/R re-weighting of the Cartesian x2/x3 covariance defect. This is the teammate's
     guess 3, it is the large part, and #293's x3 term removes it;
   - the curv_flux1 metric term that (d) exposes.

   With #293 on and a consistent gravity work, what is left is +0.009/−0.059 (AB),
   +0.025/+0.020 (AB, w seed) and −0.001/−0.003 (L1) at R = 5/1000. That is the small 1/R
   re-weighting of the Cartesian O(h²) residual. The x1-offset fix of
   `next-1overR` §0.3 does not move any face-type work: the face form makes the entropy row
   blind to mass-flux errors (§2).
3. **(c) No.** The exact-measure 2-face weight leaks E+PE at h³/3 per face, exactly
   (relative h²/(3r²); 2.6e-6 of the work per column in the replica). With φ_c = g·x1v **no**
   conservative work can be exact past a −g(h²/6)F/r² error, and main's face + curv_flux1
   already sits on that bound. A form that is both conservative and exact to O(h⁴) does
   exist:
   - φ_c = g·r̄ (the arithmetic mid-radius), so that the face form is the trapezoid rule on r²F;
   - curv_flux1 applied to r²ρw, which makes it Euler–Maclaurin.

   E+PE closes to 5e-15 per column, the local error is O(h⁴) (`conservation.out`), and its
   1/R excess equals main's.
4. **For the next PR:**
   - Do not ship the exact-measure weights on their own.
   - The 1/R excess in main is the x2/x3 term (#293). The gravity work is not.
   - If the 1/R² piece matters at R = 5 H_b, use §4's form. It is spherical-polar only and
     leaves Cartesian bit for bit unchanged. The PE diagnostic and the fixer must then use the same φ_c.
5. **The run that discriminates in snapy.** Compare main with "r̄ split + curv on r²ρw"
   (§4), or with "exact weights + curv made metric-consistent". The replica predicts no 1/R
   shift for either (B rows 7→11 and 7→12 with x3 on). If snapy shows the +1.05/+1.19 shift
   there too, the harness has a term the replica lacks.

---

## 1. The face-weight term, and why curv_flux1 cancels it

Main books the x1 gravity work as φ_c∇₁·F − ∇₁·(φ_f F) with φ_c = g·x1v and φ_f = g·x1f
(`hydro_forward.cpp:466-483`), i.e. W = g[(r₊ − x1v)A₊F₊ + (x1v − r₋)A₋F₋]/V. With
G = r²F, V = h(r̄² + h²/12) and δ_v = x1v − r̄ = h²/(6r̄) + O(h⁴),

$$
W-g\langle F\rangle_V=\frac{g}{V}\Big[\tfrac{h^3}{12}G''-\delta_v h G'\Big]
=g\,\frac{h^2}{12}\Big(F''+\frac{2F'}{r}-\frac{2F}{r^2}\Big)+O(h^4),
$$

which is the teammate's expansion: a Cartesian h²F″/12 plus (h²/6)(F′/r − F/r²).

curv_flux1 (`hydro_forward.cpp:487-509`) subtracts ∇₁·H with H = Δx1v/12·(m_i − m_{i−1}),
m = ρw, and its divergence is the **spherical** one, (A₊H₊ − A₋H₋)/V:

$$
\nabla_1\!\cdot H=\frac{h^2}{12}\,\frac{1}{r^2}\big(r^2 m'\big)'=\frac{h^2}{12}\Big(m''+\frac{2m'}{r}\Big).
$$

With F = m up to the Cartesian ρ′w′ covariance, the sum is

$$
W-g\nabla_1\!\cdot H-g\langle F\rangle_V=-g\,\frac{h^2}{6}\,\frac{F}{r^2}+(\text{Cartesian})+O(h^4).
$$

So the F′/r part of the face-weight term and the 2m′/r part of curv_flux1's metric
cancel. Main's pair has no 1/R error, and the leftover is O(h²/R²). `conservation.out` 5
checks this locally: main's error is O(h²) with coefficient equal to (h²/6)F/r² to
1.002. The exact-measure weights (g·F interpolated linearly to x1v, i.e. (½ ± δ_v/h)F±) keep
the Cartesian h²F″/12. Next to main's curv_flux1 they therefore leave −g(h²/6)m′/r, an
O(h²/R) error 30× larger than main's.

In eps the term is ε·n_z²·R → −(gL²/6c_p)·Σ(ρw)′w/Σρw², and Σ(ρw)′w = ½Σρ′w² < 0 for every
seed with w = 0 at the walls. So it is positive in the #293 harness sign, on every deck
where ρ falls with height.

## 2. What main's excess is made of: the face-form identity

With exact face backgrounds, h(r) + g·r is constant on the adiabat. The x1 advective energy
flux h_f F, minus h_c times the mass row, plus the face work, then collapses cell by cell to

$$
\rho T S=-\big(h(r_c)-h_c\big)\,\nabla_1\!\cdot F\;+\;g\,\nabla_1\!\cdot H\;-\;\nabla_3\!\cdot\big(F_{3E}-h_cF_3\big),
\qquad r_c=x1v .
$$

The first term holds **for any face mass flux F**. So no mass-flux error reaches the
entropy row under face work: not the x1 weight bias of `next-1overR`, and not the WB
reference's face ρ (it enters only through h_f = c_p p_f/ρ_f). That is why B rows 2→3 do not move. With x3 off the last
term is 0, and the whole excess is the 1/R re-weighting of the first two terms' Cartesian
O(h²) values. Those are the x2/x3 covariance defect seen from the x1 side, plus curv_flux1.
#293's x3 term supplies the missing third term (Table C).

## 3. Tables (`attribution2.out`)

**A.** Excess at R = 5 and 1000 H_b, nz 128, #293 sign, H_b units:

| deck, seed | floor | main | term | floor/term | main/term |
|---|---|---|---|---|---|
| AB, ρw ∝ sin | −0.630, −0.859 | +0.932, +1.273 | +0.178, +0.215 | −3.99 | +5.91 |
| AB, w ∝ sin | −0.256, −0.313 | +0.102, +0.142 | +0.150, +0.159 | −1.97 | +0.89 |
| L1, ρw ∝ sin | −0.115, −0.130 | +0.045, +0.051 | +0.022, +0.020 | −6.49 | +2.53 |
| teammate (×−1) | −1.72, −1.95 | +1.43, +1.69 | +1.07, +1.23 | −1.59 | +1.37 |

**B.** Excess along the fixes, AB with the ρw seed, R = 5 / 20 / 1000. The full table, with
the w seed and L1, is in `attribution2.out`.

| arm | R=5 | R=20 | R=1000 | Cartesian twin |
|---|---|---|---|---|
| 1 main: face + curv, WB main, x3 off | +0.932 | +1.166 | +1.273 | −0.683 |
| 2 + exact 2-face weights, curv main [d] | +0.754 | +0.962 | +1.057 | −0.683 |
| 3 + x1 r² weights (§0.3) | +0.754 | +0.962 | +1.057 | −0.683 |
| 4 + exact WB reference **[= (b) as asked]** | **+0.434** | +0.606 | **+0.686** | −0.594 |
| 5 + x3 #293 | −0.167 | −0.237 | −0.270 | +0.018 |
| 7 main face + curv, exact WB, x3 off | +0.612 | +0.810 | +0.901 | −0.594 |
| 8 main face + curv, exact WB, x3 #293 | **+0.011** | −0.033 | **−0.055** | +0.018 |
| 10 r̄ + curv(r²m), x1, WB, x3 #293 | −0.031 | −0.047 | −0.055 | +0.018 |
| 12 exact weights + curv made consistent, x3 exact | −0.075 | −0.065 | −0.060 | +0.019 |
| 13 cell work, x1, WB, x3 exact | +0.046 | +0.057 | +0.061 | −0.057 |

Reading (b) from rows 4, 5, 7 and 8:
- 4 − 7 = −0.18/−0.21 is the curv_flux1 metric term exposed by (d).
- 7 − 8 = +0.60/+0.96 is the re-weighted Cartesian x2/x3 defect.
- Row 8 is the floor of what metric fixes can reach.

Row 4 (−0.43/−0.69 after sign mapping) lands within 15 to 40 % of the teammate's −0.38/−0.50. Main and term do
not match, though, so I do not count this as a reproduction.

**C.** The split of §2 for the r̄ form with x3 exact, AB ρw seed, R = 1000: x1 +0.960,
x3 −0.960, curv −0.059. The x1 and x3 parts cancel in the excess, and what remains is the
1/R part of curv_flux1's Cartesian O(h²) term (−0.310 in the twin). With the w seed they do
not cancel exactly (+0.603 against +0.033, curv −0.616, sum +0.020). The remainder is the
1/R re-weighting of the Cartesian residual (the teammate's guess 3). It is O(h²) and is
not removed by any metric change, only by a 4th-order Cartesian operator.

**D.** E+PE per φ column (`max|Σ_i V(W + g r_c ∂_tρ₁)| / Σ|VW|`, AB, R = 5, nz 128): main
face 4.5e-15, exact weights 2.6e-6, r̄ form 4.7e-15.

## 4. (c) Conservation (`conservation.py`)

Write the discrete E+PE as Σ_i V_i(E_i + ρ_i φ_i) with φ_i = g r_c,i. The x1 mass fluxes
change Σ Vρφ by −g Σ_f A_f F_f (r_c,i+1 − r_c,i). A work W_i = −g Σ_f c_if F_f is therefore
conservative iff every interior face's column sum Σ_i V_i c_if equals A_f(r_c,i+1 − r_c,i).

1. **Face form.** Each face's work is split at r_f, so the column sum is A_fΔx1v by
   construction, and conservation holds for any F.
2. **Exact-measure weights** with φ_c = g·x1v. The column sum minus A_fΔx1v is
   h³(h⁴ − 6h²r_f² + 18r_f⁴) / [6(h² − 3hr_f + 3r_f²)(h² + 3hr_f + 3r_f²)] = h³/3 + O(h⁵) (sympy, exact).
   So E+PE drifts at −g Σ_f F_f·h³/3 per unit solid angle. **Not conservative.**
3. **No conservative form can do better with φ_c = g·x1v.** Conservation pins
   Σ_i V_i W_i to −g Σ_f A_fΔx1v_f F_f, and A_fΔx1v_f = h r_f² − h³/6 exactly to O(h⁵). The
   exact Σ V⟨F⟩ is Σ_f h r_f² F_f plus Cartesian end terms. The bulk difference
   −(h²/6)∫F dr is not a local divergence: writing it as one would need H ∝ ∫F dr/r², which
   is nonzero at the walls. So every conservative work with φ_c = g·x1v carries
   −g(h²/6)F/r² in W, and main's face + curv_flux1 has exactly that and nothing else at
   O(h²) beyond the Cartesian part.
4. **The conservative form exact to O(h⁴).** Take φ_c = g·r̄ in the face form, which makes
   it (h/2V)(G₊ + G₋) with G = r²F, the trapezoid rule. Apply curv_flux1 to G instead of m:
   A_fH_f = (h/12)(r̄_i²m_i − r̄_{i−1}²m_{i−1}). That is divergence form and zero at the
   walls, so it stays conservative, and it removes the trapezoid rule's −(h²/12)G″
   (Euler–Maclaurin). Local error × nz⁴ = 0.78, 0.88, 0.91, 0.92, 0.93 at nz 16 to 256
   (`conservation.out` 5). E+PE closes to 4.7e-15. In eps it differs from main only at
   O(1/R²) (B rows 8 and 10).

   In snapy this is spherical-polar only (on Cartesian r̄ = x1v and the r² factors are 1):
   - `hydro_forward.cpp:467`: phi_cell at ½(x1f_i + x1f_{i+1}) in place of x1v;
   - `:493`: rhov → r̄²·ρw;
   - `:494`: curv_flux1 divided by x1f², with the area multiplication kept;
   - the E+PE fixer and `epe_drift` must use the same φ_c.

   The conserved PE then puts the cell mass at r̄ rather than at its r² centroid. That is a
   different O(h²) approximation of ∫ρgr dV, not a worse one.

   The entropy identity of §2 holds with r_c = r̄ too. Its first term then gains
   −gδ_v∇₁·F, and that term cancels against curv_flux1's change at O(1/R). This is why rows 8
   and 10 agree at R = 1000.

## 5. Limits of this study

- The teammate's deck, seed and eps units are not in the repo. Table A shows the replica's
  ratios differ from theirs, so absolute agreement is not claimed. The structural results
  are deck-independent identities checked in the replica: the curv_flux1 cancellation (§1),
  the face-form identity (§2) and the conservation bound and O(h⁴) form (§4).
- The replica is the linear, one-step, smooth-WENO limit, with an exact or main-scan WB
  reference and the wall clamp as in `next-1overR`. It does not model nonlinear WENO
  weights, or an RK3 step at finite dt beyond the instantaneous tendency.
