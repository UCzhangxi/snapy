#pragma once

// C/C++
#include <cstdint>

// base
#include <configure.h>

// snap
#include <snap/snap.h>

#include "flux_positivity_impl.h"  // rn_mul, rn_add, rn_sub

namespace snap {

inline DISPATCH_MACRO double rn_div(double a, double b) {
#ifdef __CUDA_ARCH__
  return __ddiv_rn(a, b);
#else
  return a / b;
#endif
}
inline DISPATCH_MACRO float rn_div(float a, float b) {
#ifdef __CUDA_ARCH__
  return __fdiv_rn(a, b);
#else
  return a / b;
#endif
}

//! SNAP_FUSED_COV: HydroImpl::_flux_covariance (no centroid part, i.e. a grid
//! with face_centroid_shift_zero) and the `flux += dcov` that follows it, for
//! one cell of the face array, in the op order of the eager code:
//!   d1(q)    = (q[i+1] - q[i-1]) / (x1v[i+1] - x1v[i-1])
//!   cov(a,b) = ((s2[i] * rho[i]) * d1(a)) * d1(b)
//!   IPR      : cov(h, un), h = enth / rho
//!   ICY + n  : cov(un, q_n)
//!   IDN      : -c_0 - c_1 - ... (species only)
//! for 1 <= i <= nc1 - 2, zero elsewhere; then every row of the flux gets
//! flux + dcov (the +0.0 of the untouched rows included, as the eager += does)
//! \param flux  (nvar, ncell), updated in place
//! \param wbar  (nvar, ncell) face mean 0.5 * (wl + wr), un in row iun
//! \param enth  (ncell) W->I(wbar) + p
//! \param s2    (nc1) face_moment2_x1, x1v (nc1)
template <typename T>
inline DISPATCH_MACRO void flux_covariance_cell(T* flux, T const* wbar,
                                                T const* enth, T const* s2,
                                                T const* x1v, int64_t ncell,
                                                int nvar, int ny, int iun,
                                                int nc1, int64_t cell) {
  int i = cell % nc1;
  bool inside = i >= 1 && i <= nc1 - 2;
  T dipr = T(0), didn = T(0);
  int64_t lo = cell - 1, hi = cell + 1;
  T s2r = T(0), d1un = T(0), dx = T(1);
  if (inside) {
    dx = rn_sub(x1v[i + 1], x1v[i - 1]);
    s2r = rn_mul(s2[i], wbar[IDN * ncell + cell]);
    d1un = rn_div(rn_sub(wbar[iun * ncell + hi], wbar[iun * ncell + lo]), dx);
    T hh = rn_div(enth[hi], wbar[IDN * ncell + hi]);
    T hl = rn_div(enth[lo], wbar[IDN * ncell + lo]);
    T d1h = rn_div(rn_sub(hh, hl), dx);
    dipr = rn_mul(rn_mul(s2r, d1h), d1un);
  }
  for (int n = 0; n < ny; ++n) {
    T c = T(0);
    if (inside) {
      int r = ICY + n;
      T d1q = rn_div(rn_sub(wbar[r * ncell + hi], wbar[r * ncell + lo]), dx);
      c = rn_mul(rn_mul(s2r, d1un), d1q);
      didn = n == 0 ? -c : rn_sub(didn, c);
    }
    flux[(ICY + n) * ncell + cell] = rn_add(flux[(ICY + n) * ncell + cell], c);
  }
  for (int v = 0; v < nvar; ++v) {
    if (v >= ICY && v < ICY + ny) continue;
    T d = v == IPR ? dipr : v == IDN ? didn : T(0);
    flux[v * ncell + cell] = rn_add(flux[v * ncell + cell], d);
  }
}

}  // namespace snap
