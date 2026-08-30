// torch
#include <torch/torch.h>

// snap
#include "interpolation.hpp"

// Zhang & Chen, JAMES 17, e2025MS005056 (2025), eqs (29)-(42); equation numbers
// are theirs. The authors state in their sec 3.3 that the scheme is NOT
// provably monotone above second order, so boundedness is measured, never
// assumed.

namespace snap {
namespace {

//! (42) limiter strength, 1 = fully limited.
constexpr double kSlim = 1.0;

//! (35) guards a zero denominator. The paper prints 1e-6, the authors'
//! reference implementation uses 1e-10; it is relative to the stencil magnitude
//! when scale is set.
constexpr double kEps = 1.0e-10;

//! (29) east-side coefficients; (31) the west side is the same list reversed.
constexpr double kE2[3] = {-1. / 6., 5. / 6., 1. / 3.};
constexpr double kE3[5] = {1. / 30., -13. / 60., 47. / 60., 9. / 20.,
                           -1. / 20.};

//! Interface values for one face of every cell.
/*!
 * Stencil position p of output i is `w.narrow(dim, p, out.size(dim))[i]`; the
 * pivot cell is the centre, p = 2. `_apply_inplace` writes `left()` into
 * `wlr[IRT]` and `right()` into `wlr[ILT]`, so the names say which face of the
 * pivot the value sits on, NOT the Riemann role: `left()` is the pivot's WEST
 * face and `right()` its EAST face. Reading that backwards drops the scheme
 * below donor cell while still reporting a bounded, conservative field, so
 * `mono5_matches_cp5_on_linear_data` pins it against cp5.
 *
 * The gradient ratio belongs to the pivot cell, not the face, so it is formed
 * in stencil order for both sides and only the polynomials are reversed -- as
 * in the authors' own `get_var_we_lim_ng3`, which forms one sigma and applies
 * it to both faces.
 */
void mono5_(torch::Tensor const& out, torch::Tensor w, int dim, bool east,
            bool scale) {
  auto m = out.size(dim);
  auto v = [&](int64_t p) { return w.narrow(dim, p, m); };
  auto v0 = v(0), v1 = v(1), v2 = v(2), v3 = v(3), v4 = v(4);

  // Non-dimensionalise as weno5 does, so kEps is relative to the stencil rather
  // than an absolute floor that silently turns a trace species into donor cell.
  torch::Tensor s;
  if (scale) {
    s = (v0.abs() + v1.abs() + v2.abs() + v3.abs() + v4.abs()) / 5.;
    s = torch::where(s > 0., s, torch::ones_like(s));
    v0 = v0 / s;
    v1 = v1 / s;
    v2 = v2 / s;
    v3 = v3 / s;
    v4 = v4 / s;
  }

  auto r = (v2 - v1) / (v3 - v2 + kEps);  // (35)
  auto phi = 2. * r / (1. + r * r);       // (34)
  // (42). torch::where, not clamp_min: NaN fails the comparison and takes the
  // floor, matching the reference. clamp_min would propagate it.
  phi =
      torch::where(phi > (1. - kSlim), phi, torch::full_like(phi, 1. - kSlim));

  torch::Tensor p2, p3;
  if (east) {
    p2 = kE2[0] * v1 + kE2[1] * v2 + kE2[2] * v3;  // (29) Ng = 2
    p3 = kE3[0] * v0 + kE3[1] * v1 + kE3[2] * v2 + kE3[3] * v3 + kE3[4] * v4;
  } else {
    p2 = kE2[2] * v1 + kE2[1] * v2 + kE2[0] * v3;  // (30) Ng = 2
    p3 = kE3[4] * v0 + kE3[3] * v1 + kE3[2] * v2 + kE3[1] * v3 + kE3[0] * v4;
  }

  auto low = v2 - phi * (v2 - p2);    // (36), (37); poly1 = v2
  auto res = low - phi * (low - p3);  // (32), (33)
  out.copy_(scale ? res * s : res);
}

}  // namespace

void Mono5InterpImpl::left(torch::Tensor w, int dim, torch::Tensor const& out) {
  mono5_(out, w, dim, /*east=*/false, options->scale());
}

void Mono5InterpImpl::right(torch::Tensor w, int dim,
                            torch::Tensor const& out) {
  mono5_(out, w, dim, /*east=*/true, options->scale());
}

}  // namespace snap
