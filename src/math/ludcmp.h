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
//! \param[out] sing Optional. Set to the index of the offending row when the
//! matrix is rejected as singular, and to -1 otherwise. Needed because the
//! return value CANNOT report failure: it is +1/-1 for an even/odd number of
//! row interchanges, and the singular path also returns 1 -- so a successful
//! even-permutation decomposition and a singular matrix are indistinguishable
//! to every caller. (S44 instrumentation, 2026-08-15.)
//! \return +1 or -1 depending on whether row interchanges were even or odd;
//!         1 indicates error (singular matrix)
//!
//! \note Adapted from Numerical Recipes in C, 2nd Ed., p. 46.
//! \note Returns 1 if matrix is singular
template <typename T, int N>
inline DISPATCH_MACRO int ludcmp(Eigen::Matrix<T, N, N, Eigen::RowMajor> &a,
                                 int *indx, int *sing = nullptr) {
  int i, imax = 0, j, k, d;
  T big, dum, sum, temp;
  T vv[N];

  if (sing != nullptr) *sing = -1;

  d = 1;
  for (i = 0; i < N; i++) {
    big = 0.0;
    for (j = 0; j < N; j++)
      if ((temp = fabs(a(i, j))) > big) big = temp;
    if (big == 0.0) {
      // S44 instrumentation: `big == 0.0` is reached by an all-ZERO row AND by
      // a row holding NaN (NaN > big is false, so NaN never raises big). Those
      // have completely different causes, so classify before reporting.
      // Infinity is detected as (v - v) != 0, which is type-safe for float and
      // double alike; NaN is caught first by (v != v).
      int nzero = 0, nnan = 0, ninf = 0;
      for (j = 0; j < N; j++) {
        T v = a(i, j);
        if (v != v) {
          ++nnan;
        } else if ((v - v) != (T)0) {
          ++ninf;
        } else if (v == (T)0) {
          ++nzero;
        }
      }
      printf("[S44-LUDCMP] singular row=%d/%d zero=%d nan=%d inf=%d entries=",
             i, N, nzero, nnan, ninf);
      for (j = 0; j < N; j++) printf(" %.8e", (double)a(i, j));
      printf("\n");
      if (sing != nullptr) *sing = i;
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
    if (j != N - 1) {
      dum = (1.0 / a(j, j));
      for (i = j + 1; i < N; i++) a(i, j) *= dum;
    }
  }

  return d;
}
