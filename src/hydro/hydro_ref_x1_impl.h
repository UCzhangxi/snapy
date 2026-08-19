#pragma once

// base
#include <configure.h>

// C/C++
#include <cmath>
#include <limits>

// snap
#include <snap/snap.h>

namespace snap {

template <typename T>
inline DISPATCH_MACRO T hydro_ref_x1_face(T const* psf_lo, T const* psf_hi,
                                          int flat, int face, int nc1) {
  if (face < nc1) return psf_lo[flat + face];
  return psf_hi[flat + nc1 - 1];
}

template <typename T>
inline DISPATCH_MACRO void hydro_ref_x1_scan_impl(
    T const* w, T const* dx1f, T const* anchor, T const* gam, T const* kbot_in,
    T* psf_lo, T* psf_hi, int column, int ncolumns, int nc1, int is, int iu,
    T grav, T* kbot, T* inv_gamma) {
  int ncells = ncolumns * nc1;
  int flat = column * nc1;
  T top_anchor;
  if (anchor) {
    top_anchor = anchor[column];
  } else {
    T rho_top = w[IDN * ncells + flat + iu];
    T pres_top = w[IPR * ncells + flat + iu];
    T rdt_top = pres_top / rho_top;
    top_anchor = pres_top * exp(-grav * T(0.5) * dx1f[iu] / rdt_top);
  }

  T face = top_anchor;
  T min_positive = std::numeric_limits<T>::min();
  for (int i = iu; i >= 0; --i) {
    T dp = grav * w[IDN * ncells + flat + i] * dx1f[i];
    T lo = face + dp;
    T hi = face;
    psf_lo[flat + i] = lo > min_positive ? lo : min_positive;
    psf_hi[flat + i] = hi > min_positive ? hi : min_positive;
    face = lo;
  }

  face = top_anchor;
  for (int i = iu + 1; i < nc1; ++i) {
    T dp = grav * w[IDN * ncells + flat + i] * dx1f[i];
    T lo = face;
    T hi = lo - dp;
    psf_lo[flat + i] = lo > min_positive ? lo : min_positive;
    psf_hi[flat + i] = hi > min_positive ? hi : min_positive;
    face = hi;
  }

  T gamma = gam[column];
  // kbot is vestigial: the density reference is local (smoothed rho/p, see
  // hydro_ref_x1_rop_smooth), so nothing consumes it. The relay plumbing in
  // hydro.cpp is retained; removing it is a separate cleanup.
  if (kbot_in) {
    *kbot = kbot_in[column];
  } else {
    T rho_bot = w[IDN * ncells + flat + is];
    T pres_bot = w[IPR * ncells + flat + is];
    *kbot = pres_bot / pow(rho_bot, gamma);
  }
  *inv_gamma = T(1) / gamma;
}

//! rho/p smoothed by a clamped 5-point binomial along x1: the reference must
//! track the column profile at LARGE scales only. An unsmoothed local rho/p
//! makes rho' degenerate with the pressure perturbation, so entropy/buoyancy
//! anomalies bypass the high-order reconstruction (measured fatal on the
//! certified 84-level run); the bottom-anchored isentrope errs by orders of
//! magnitude on a stratified column (ISSUES S44).
template <typename T>
inline DISPATCH_MACRO T hydro_ref_x1_rop_smooth(T const* w, int ncells,
                                                int flat, int nc1, int i) {
  T v[5];
  for (int m = -2; m <= 2; ++m) {
    int j = i + m;
    j = j < 0 ? 0 : (j >= nc1 ? nc1 - 1 : j);
    v[m + 2] = w[IDN * ncells + flat + j] / w[IPR * ncells + flat + j];
  }
  return (v[0] + T(4) * v[1] + T(6) * v[2] + T(4) * v[3] + v[4]) / T(16);
}

template <typename T>
inline DISPATCH_MACRO void hydro_ref_x1_cell_impl(
    T const* w, T const* dx1f, T const* psf_lo, T const* psf_hi, T* pref,
    T* dsf, T* dref, int column, int i, int ncolumns, int nc1, T grav,
    bool uniform, bool phys_in, bool phys_out, T kbot, T inv_gamma) {
  int ncells = ncolumns * nc1;
  int flat = column * nc1;
  T lo = psf_lo[flat + i];
  T hi = psf_hi[flat + i];
  T cell_pref = T(0.5) * (lo + hi);

  // Log-mean cell average on every grid: exact for an exponential (locally
  // isothermal) column, where the degree-5 face quadrature it replaces
  // carries an O((dz/H)^6) residual that seeds the S44 modes (measured
  // cross-code, athena/ExoCubed A1/B1 inventory).
  T dp = grav * w[IDN * ncells + flat + i] * dx1f[i];
  T ratio = lo / hi;
  cell_pref =
      fabs(ratio - T(1)) < T(1.e-6) ? T(0.5) * (lo + hi) : dp / log(ratio);

  pref[flat + i] = cell_pref;
  T rs = hydro_ref_x1_rop_smooth(w, ncells, flat, nc1, i);
  T rf = i > 0 ? T(0.5) *
                     (hydro_ref_x1_rop_smooth(w, ncells, flat, nc1, i - 1) + rs)
               : rs;
  dref[flat + i] = cell_pref * rs;
  dsf[flat + i] = lo * rf;
}

template <typename T>
inline DISPATCH_MACRO void hydro_ref_x1_impl(
    T const* w, T const* dx1f, T const* anchor, T const* gam, T const* kbot_in,
    T* psf_lo, T* psf_hi, T* pref, T* dsf, T* dref, int column, int ncolumns,
    int nc1, int is, int iu, T grav, bool uniform, bool phys_in,
    bool phys_out) {
  T kbot;
  T inv_gamma;
  hydro_ref_x1_scan_impl(w, dx1f, anchor, gam, kbot_in, psf_lo, psf_hi, column,
                         ncolumns, nc1, is, iu, grav, &kbot, &inv_gamma);
  for (int i = 0; i < nc1; ++i) {
    hydro_ref_x1_cell_impl(w, dx1f, psf_lo, psf_hi, pref, dsf, dref, column, i,
                           ncolumns, nc1, grav, uniform, phys_in, phys_out,
                           kbot, inv_gamma);
  }
}

}  // namespace snap
