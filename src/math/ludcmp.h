#pragma once

// Eigen
#include <Eigen/Dense>

// base
#include <configure.h>

//! \brief Perform LU decomposition with partial pivoting
//!
//! Given a matrix a, this routine replaces it by the LU decomposition of a
//! rowwise permutation of itself. The decomposition is used with lubksb to
//! solve linear equations or invert a matrix.
//!
//! \tparam T Scalar type (e.g., float, double)
//! \tparam N Matrix dimension
//! \param[in,out] a Input matrix, replaced by LU decomposition on output
//! \param[out] indx Output vector recording row permutation from partial
//! pivoting
//! \return +1 or -1 depending on whether row interchanges were even or odd;
//!         1 indicates error (singular matrix)
//!
//! \note Adapted from Numerical Recipes in C, 2nd Ed., p. 46.
//! \note Returns 1 if matrix is singular
template <typename T, int N>
inline DISPATCH_MACRO int ludcmp(Eigen::Matrix<T, N, N, Eigen::RowMajor> &a,
                                 int *indx) {
  int i, imax = 0, j, k, d;
  T big, dum, sum, temp;
  T vv[N];

  d = 1;
  for (i = 0; i < N; i++) {
    big = 0.0;
    for (j = 0; j < N; j++)
      if ((temp = fabs(a(i, j))) > big) big = temp;
    if (big == 0.0) {
      printf("Singular matrix in routine ludcmp");
      return 1;
    }
    vv[i] = 1.0 / big;
  }
  for (j = 0; j < N; j++) {
    for (i = 0; i < j; i++) {
      sum = a(i, j);
      for (k = 0; k < i; k++) sum -= a(i, k) * a(k, j);
      a(i, j) = sum;
    }
    big = 0.0;
    for (i = j; i < N; i++) {
      sum = a(i, j);
      for (k = 0; k < j; k++) sum -= a(i, k) * a(k, j);
      a(i, j) = sum;
      if ((dum = vv[i] * fabs(sum)) >= big) {
        big = dum;
        imax = i;
      }
    }
    if (j != imax) {
      for (k = 0; k < N; k++) {
        dum = a(imax, k);
        a(imax, k) = a(j, k);
        a(j, k) = dum;
      }
      d = -d;
      vv[imax] = vv[j];
    }
    indx[j] = imax;
    // [S44-PIVOT] instrumentation (2026-08-16, branch xiz/s44-pivot; NOT FOR
    // SCIENCE). `big` here is the row-SCALED magnitude of the chosen pivot, so
    // it is O(1) for a well-conditioned row and collapses toward 0 as the
    // matrix becomes near-singular. The only existing guard is `big == 0.0` (a
    // fully ZERO row) many lines above; a tiny-but-nonzero pivot passes it and
    // then hits `1.0 / a(j,j)` below with no test and no way to report -- which
    // is exactly a silent 1/pivot amplification.
    if (big < 1.0e-10) {
      printf("[S44-PIVOT] j=%d scaled_pivot=%.6e a_jj=%.6e\n", j, (double)big,
             (double)a(j, j));
    }
    // [S44-FIX v3] Guard on the SCALED pivot `big` (= vv[i]*|sum|, the
    // row-normalised pivot magnitude the diagnostic prints), NOT on |a(j,j)|
    // against vv[j]: vv[j] is stale after the row swap above (NR assigns
    // vv[imax]=vv[j] and leaves vv[j]), so the earlier attempt tested the wrong
    // quantity. Calibration from the measured population on the failing ISSI-HJ
    // case: scaled pivots 1e-20..1e-10 are ROUTINE (2010 events) and must be
    // left alone -- clamping at 1e-4 killed the run instantly (191182 events).
    // The pathological tail is <1e-30 (354 events, min 4.6e-51). Clamp only
    // that tail, bounding the 1/pivot amplification at ~1e30 instead of 1e51.
    const T kPivScaled = static_cast<T>(1.0e-30);
    if (big < kPivScaled && big > 0) {
      T scale = (vv[j] > 0) ? (kPivScaled / vv[j]) : kPivScaled;
      if (fabs(a(j, j)) < scale) a(j, j) = (a(j, j) < 0) ? -scale : scale;
    }
    if (j != N - 1) {
      dum = (1.0 / a(j, j));
      for (i = j + 1; i < N; i++) a(i, j) *= dum;
    }
  }

  return d;
}
