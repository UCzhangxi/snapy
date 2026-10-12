#pragma once

// C/C++
#include <cstdint>

// base
#include <configure.h>

// snap
#include <snap/snap.h>

namespace snap {

// Arithmetic that is never contracted into an FMA: each op rounds once, like
// the separate eager kernels (mul, add, sub) this fused code replaces. nvcc
// contracts a * b + c by default; the _rn intrinsics are never contracted.
inline DISPATCH_MACRO double rn_mul(double a, double b) {
#ifdef __CUDA_ARCH__
  return __dmul_rn(a, b);
#else
  return a * b;
#endif
}
inline DISPATCH_MACRO double rn_add(double a, double b) {
#ifdef __CUDA_ARCH__
  return __dadd_rn(a, b);
#else
  return a + b;
#endif
}
inline DISPATCH_MACRO double rn_sub(double a, double b) {
#ifdef __CUDA_ARCH__
  return __dsub_rn(a, b);
#else
  return a - b;
#endif
}
inline DISPATCH_MACRO float rn_mul(float a, float b) {
#ifdef __CUDA_ARCH__
  return __fmul_rn(a, b);
#else
  return a * b;
#endif
}
inline DISPATCH_MACRO float rn_add(float a, float b) {
#ifdef __CUDA_ARCH__
  return __fadd_rn(a, b);
#else
  return a + b;
#endif
}
inline DISPATCH_MACRO float rn_sub(float a, float b) {
#ifdef __CUDA_ARCH__
  return __fsub_rn(a, b);
#else
  return a - b;
#endif
}

//! SNAP_FUSED_CARRY: flux_positivity_carry_ followed by
//! flux_positivity_scale_ for ONE face of one direction, in the op order of
//! the eager code (flux_positivity.cpp), so the result can be bitwise:
//!   share_n = 1 - th_n,  th_n = f_n > 0 ? theta_n(lower) : theta_n(upper)
//!   per part p (adv = f - fsed then fsed, or f): up = p > 0, dm = share * p
//!     F[IPR] -= sum_n dm_n h_n(up ? lower : upper)
//!     F[IVX+d] -= (sum_n dm_n up_n) v_d(lower) + (sum_n dm_n !up_n) v_d(upper)
//!   then F[ICY+n] *= th_n.
//! The species sums are (((0 + x_0) + x_1) + ...) + 0, the order of torch's
//! reduction over a short outer dimension (one accumulator per element, then
//! combined in order); this is the assumption the GPU bitwise test checks.
//! \param flux   (nvar, ncell) of this direction, contiguous
//! \param theta, hspec, fsed  (ny, ncell); fsed may be null
//! \param vel    (3, ncell)
//! \param upper  flat index of the face's upper cell (= the face index)
//! \param dstride flat distance to the lower cell along the direction
template <typename T>
inline DISPATCH_MACRO void positivity_carry_scale_face(
    T* flux, T const* theta, T const* hspec, T const* vel, T const* fsed,
    int64_t ncell, int ny, int64_t upper, int64_t dstride) {
  int64_t lower = upper - dstride;
  int nparts = fsed ? 2 : 1;
  for (int part = 0; part < nparts; ++part) {
    T se = T(0), sa = T(0), sb = T(0);
    for (int n = 0; n < ny; ++n) {
      T f = flux[(ICY + n) * ncell + upper];
      T th = f > T(0) ? theta[n * ncell + lower] : theta[n * ncell + upper];
      T share = rn_sub(T(1), th);
      T p = f;
      if (fsed) {
        T sd = fsed[n * ncell + upper];
        p = part == 0 ? rn_sub(f, sd) : sd;
      }
      bool up = p > T(0);
      T dm = rn_mul(share, p);
      T h = up ? hspec[n * ncell + lower] : hspec[n * ncell + upper];
      se = rn_add(se, rn_mul(dm, h));
      sa = rn_add(sa, rn_mul(dm, up ? T(1) : T(0)));
      sb = rn_add(sb, rn_mul(dm, up ? T(0) : T(1)));
    }
    se = rn_add(se, T(0));
    sa = rn_add(sa, T(0));
    sb = rn_add(sb, T(0));
    flux[IPR * ncell + upper] = rn_sub(flux[IPR * ncell + upper], se);
    for (int d = 0; d < 3; ++d) {
      T m = rn_add(rn_mul(sa, vel[d * ncell + lower]),
                   rn_mul(sb, vel[d * ncell + upper]));
      flux[(IVX + d) * ncell + upper] =
          rn_sub(flux[(IVX + d) * ncell + upper], m);
    }
  }
  for (int n = 0; n < ny; ++n) {
    T f = flux[(ICY + n) * ncell + upper];
    T th = f > T(0) ? theta[n * ncell + lower] : theta[n * ncell + upper];
    flux[(ICY + n) * ncell + upper] = rn_mul(f, th);
  }
}

//! the flat cell index of face t of the faces lo..hi+1 along `dim`
//! (3: x1, 2: x2, 1: x3) of a (nc3, nc2, nc1) block, every index of the other
//! two dimensions included, as the eager slices take them
inline DISPATCH_MACRO int64_t positivity_face_index(int64_t t, int dim, int lo,
                                                    int nf, int nc3, int nc2,
                                                    int nc1) {
  int64_t k, j, i;
  if (dim == 3) {
    i = lo + t % nf;
    j = (t / nf) % nc2;
    k = t / (int64_t(nf) * nc2);
  } else if (dim == 2) {
    i = t % nc1;
    j = lo + (t / nc1) % nf;
    k = t / (int64_t(nc1) * nf);
  } else {
    i = t % nc1;
    j = (t / nc1) % nc2;
    k = lo + t / (int64_t(nc1) * nc2);
  }
  return (k * nc2 + j) * nc1 + i;
}

}  // namespace snap
