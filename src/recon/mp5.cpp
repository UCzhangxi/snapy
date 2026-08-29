// torch
#include <torch/torch.h>

// snap
#include "interpolation.hpp"

// Suresh & Huynh, JCP 136, 83-99 (1997). Equation numbers below are theirs.
// The limiter is applied to the WENO5 interface value, so the scheme keeps
// WENO5's shock capturing and gains its monotonicity constraint.

namespace snap {
namespace {

constexpr double kAlpha =
    4.0;  // (2.8); >= 2 required, 4 recommended for Runge-Kutta

// (2.30) bypass tolerance. 0, not the paper's 1e-10: the tolerance sets a floor
// on the residual overshoot, and a passive tracer is bounded data, not an O(1)
// flow variable.
constexpr double kEps = 0.0;

torch::Tensor minmod2(torch::Tensor const& x, torch::Tensor const& y) {
  return 0.5 * (torch::sign(x) + torch::sign(y)) *
         torch::minimum(x.abs(), y.abs());
}

// (2.6b) with k = 4
torch::Tensor minmod4(torch::Tensor const& a, torch::Tensor const& b,
                      torch::Tensor const& c, torch::Tensor const& d) {
  auto sa = torch::sign(a);
  auto s = 0.125 * (sa + torch::sign(b)) *
           ((sa + torch::sign(c)) * (sa + torch::sign(d))).abs();
  return s * torch::minimum(torch::minimum(a.abs(), b.abs()),
                            torch::minimum(c.abs(), d.abs()));
}

// (2.5)
torch::Tensor median3(torch::Tensor const& x, torch::Tensor const& a,
                      torch::Tensor const& b) {
  return x + minmod2(a - x, b - x);
}

//! Limit interface states in `out` against the five-point stencil in `w`.
/*!
 * Stencil position p of output i is `w.narrow(dim, p, out.size(dim))[i]` and
 * the pivot cell j is the centre, p = 2. `left` reads the stencil REVERSED, p
 * holding v_{j+2-p}: the `cm` rows in weno5.cpp are the standard left-biased
 * sub-stencils written back to front (row 1 is p2, weight .3; row 3 is p0,
 * weight .1). `right` builds from the flipped coefficients and so reads in
 * natural order.
 */
void mp5_limit_(torch::Tensor const& out, torch::Tensor w, int dim,
                bool reversed) {
  auto m = out.size(dim);
  auto st = [&](int64_t k) { return w.narrow(dim, reversed ? 4 - k : k, m); };
  auto vjm2 = st(0), vjm1 = st(1), vj = st(2), vjp1 = st(3), vjp2 = st(4);

  auto vmp = vj + minmod2(vjp1 - vj, kAlpha * (vj - vjm1));  // (2.12)
  auto active = (out - vj) * (out - vmp) > kEps;             // (2.30)

  auto dm1 = vjm2 + vj - 2. * vjm1;  // (2.19)
  auto d0 = vjm1 + vjp1 - 2. * vj;
  auto dp1 = vj + vjp2 - 2. * vjp1;

  auto d4p = minmod4(4. * d0 - dp1, 4. * dp1 - d0, d0, dp1);  // (2.27) j+1/2
  auto d4m = minmod4(4. * dm1 - d0, 4. * d0 - dm1, dm1, d0);  // (2.27) j-1/2

  auto vul = vj + kAlpha * (vj - vjm1);                 // (2.8)
  auto vav = 0.5 * (vj + vjp1);                         // (2.16)
  auto vmd = vav - 0.5 * d4p;                           // (2.28)
  auto vlc = vj + 0.5 * (vj - vjm1) + (4. / 3.) * d4m;  // (2.29)

  auto vmin = torch::maximum(torch::minimum(torch::minimum(vj, vjp1), vmd),
                             torch::minimum(torch::minimum(vj, vul), vlc));
  auto vmax = torch::minimum(torch::maximum(torch::maximum(vj, vjp1), vmd),
                             torch::maximum(torch::maximum(vj, vul), vlc));

  out.copy_(
      torch::where(active, median3(out, vmin, vmax), out));  // (2.24), (2.26)
}

}  // namespace

void MP5InterpImpl::reset() {
  pweno = register_module("weno5", Weno5Interp(options));
}

void MP5InterpImpl::left(torch::Tensor w, int dim, torch::Tensor const& out) {
  pweno->left(w, dim, out);
  mp5_limit_(out, w, dim, /*reversed=*/true);
}

void MP5InterpImpl::right(torch::Tensor w, int dim, torch::Tensor const& out) {
  pweno->right(w, dim, out);
  mp5_limit_(out, w, dim, /*reversed=*/false);
}

}  // namespace snap
