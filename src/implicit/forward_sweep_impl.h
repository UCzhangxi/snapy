#pragma once

// eigen
#include <Eigen/Dense>

// base
#include <configure.h>

// snap
#include <snap/math/ludcmp.h>
#include <snap/math/luminv.h>
#include <snap/snap.h>

#define DU(n, i) du[(n) * stride1 + (i) * stride2]
#define W(n, i) w[(n) * stride1 + (i) * stride2]
#define VOL(n) vol[(n) * stride2]

namespace snap {

//! \brief S44 instrumentation: L1 norm of one row of a block. Hand-rolled
//! rather than Eigen's .norm() so it is guaranteed device-callable and
//! sqrt-free.
template <typename T, int N>
inline DISPATCH_MACRO double S44RowAbs(const Eigen::Matrix<T, N, N>& m, int r) {
  double s = 0.0;
  for (int j = 0; j < N; ++j) s += fabs((double)m(r, j));
  return s;
}

template <typename T, int N>
inline DISPATCH_MACRO double S44MatAbs(const Eigen::Matrix<T, N, N>& m) {
  double s = 0.0;
  for (int r = 0; r < N; ++r) s += S44RowAbs<T, N>(m, r);
  return s;
}

template <typename T, int N>
inline DISPATCH_MACRO double S44VecAbs(const Eigen::Matrix<T, N, 1>& v) {
  double s = 0.0;
  for (int r = 0; r < N; ++r) s += fabs((double)v(r));
  return s;
}

template <typename T, int N>
void DISPATCH_MACRO ForwardSweep(Eigen::Matrix<T, N, N>* a,
                                 Eigen::Matrix<T, N, N>* b,
                                 Eigen::Matrix<T, N, N>* c,
                                 Eigen::Matrix<T, N, 1>* delta, T* du,
                                 double dt, int il, int iu, int dir, int ny,
                                 int stride1, int stride2, bool first_block,
                                 bool last_block) {
  Eigen::Matrix<T, N, 1> rhs;

  if constexpr (N == 3) {  // partial matrix
    rhs(0) = DU(IDN, il);
    for (int n = 0; n < ny; ++n) rhs(0) += DU(ICY + n, il);
    rhs(0) /= dt;
    rhs(1) = DU(IVX + dir, il) / dt;
    rhs(2) = DU(IPR, il) / dt;
  } else {  // full matrix
    rhs(0) = DU(IDN, il);
    for (int n = 0; n < ny; ++n) rhs(0) += DU(ICY + n, il);
    rhs(0) /= dt;
    rhs(1) = DU(IVX + dir, il) / dt;
    rhs(2) = DU(IVX + (IVY - IVX + dir) % 3, il) / dt;
    rhs(3) = DU(IVX + (IVZ - IVX + dir) % 3, il) / dt;
    rhs(4) = DU(IPR, il) / dt;
  }

  int indx[N];
  Eigen::Matrix<T, N, N, Eigen::RowMajor> A;
  Eigen::Matrix<T, N, N + 1, Eigen::RowMajor> solved;

  // if (!first_block) {
  // RecvBuffer(a[il - 1], delta[il - 1], bblock);
  // a[il] = (a[il] - b[il] * a[il - 1]).inverse().eval();
  // delta[il] = a[il] * (rhs - b[il] * delta[il - 1]);
  // a[il] *= c[il];
  //} else {
  if constexpr (N > 4) {
    A = a[il];
    for (int n = 0; n < N; ++n) indx[n] = n;
    int sing = -1;
    ludcmp(A, indx, &sing);
    if (sing >= 0) {
      // S44: the FIRST block of the column already degenerates -- no recursion
      // has happened yet, so this would indict the assembly, not the sweep.
      printf(
          "[S44-SWEEP] SEED level=%d il=%d iu=%d dir=%d dt=%.8e sing_row=%d "
          "|a|=%.8e |rhs|=%.8e\n",
          il, il, iu, dir, dt, sing, S44MatAbs<T, N>(a[il]),
          S44VecAbs<T, N>(rhs));
    }
    solved.template leftCols<N>() = c[il];
    solved.col(N) = rhs;
    lubksb(A, indx, solved);
    a[il] = solved.template leftCols<N>();
    delta[il] = solved.col(N);
  } else {  // small matrix
    a[il] = a[il].inverse().eval();
    delta[il] = a[il] * rhs;
    a[il] = a[il] * c[il];
  }
  //}

  for (int i = il + 1; i <= iu; ++i) {
    if constexpr (N == 3) {  // partial matrix
      rhs(0) = DU(IDN, i);
      for (int n = 0; n < ny; ++n) rhs(0) += DU(ICY + n, i);
      rhs(0) /= dt;
      rhs(1) = DU(IVX + dir, i) / dt;
      rhs(2) = DU(IPR, i) / dt;
    } else {
      rhs(0) = DU(IDN, i);
      for (int n = 0; n < ny; ++n) rhs(0) += DU(ICY + n, i);
      rhs(0) /= dt;
      rhs(1) = DU(IVX + dir, i) / dt;
      rhs(2) = DU(IVX + (IVY - IVX + dir) % 3, i) / dt;
      rhs(3) = DU(IVX + (IVZ - IVX + dir) % 3, i) / dt;
      rhs(4) = DU(IPR, i) / dt;
    }

    // S44 instrumentation: keep the two operands of the elimination so a
    // failure downstream can be attributed to the block as assembled (a_pre)
    // or to the recursion term (bprod). Catastrophic cancellation shows up as
    // |A| << |a_pre| ~ |bprod| row by row.
    Eigen::Matrix<T, N, N> a_pre = a[i];
    Eigen::Matrix<T, N, N> bprod = b[i] * a[i - 1];

    a[i] -= bprod;

    if constexpr (N > 4) {
      A = a[i];
      for (int n = 0; n < N; ++n) indx[n] = n;
      int sing = -1;
      ludcmp(A, indx, &sing);
      if (sing >= 0) {
        printf(
            "[S44-SWEEP] level=%d il=%d iu=%d dir=%d dt=%.8e sing_row=%d "
            "|a_pre|=%.8e |bprod|=%.8e |A|=%.8e |b|=%.8e |a_prev|=%.8e "
            "|rhs|=%.8e |delta_prev|=%.8e\n",
            i, il, iu, dir, dt, sing, S44MatAbs<T, N>(a_pre),
            S44MatAbs<T, N>(bprod), S44MatAbs<T, N>(a[i]),
            S44MatAbs<T, N>(b[i]), S44MatAbs<T, N>(a[i - 1]),
            S44VecAbs<T, N>(rhs), S44VecAbs<T, N>(delta[i - 1]));
        for (int r = 0; r < N; ++r) {
          printf("[S44-SWEEP]   row=%d |a_pre|=%.8e |bprod|=%.8e |A|=%.8e\n", r,
                 S44RowAbs<T, N>(a_pre, r), S44RowAbs<T, N>(bprod, r),
                 S44RowAbs<T, N>(a[i], r));
        }
      }
      solved.template leftCols<N>() = c[i];
      solved.col(N) = rhs - b[i] * delta[i - 1];
      lubksb(A, indx, solved);
      a[i] = solved.template leftCols<N>();
      delta[i] = solved.col(N);
    } else {  // small matrix
      a[i] = a[i].inverse().eval();
      // S44: the 3x3 partial path dies SILENTLY -- Eigen's .inverse() reports
      // nothing on a degenerate block. Report it once per block.
      bool bad = false;
      for (int r = 0; r < N && !bad; ++r)
        for (int cc = 0; cc < N && !bad; ++cc) {
          T v = a[i](r, cc);
          if (v != v || (v - v) != (T)0) bad = true;
        }
      if (bad) {
        printf(
            "[S44-INV] level=%d il=%d iu=%d dir=%d dt=%.8e nonfinite after "
            "inverse |a_pre|=%.8e |bprod|=%.8e\n",
            i, il, iu, dir, dt, S44MatAbs<T, N>(a_pre), S44MatAbs<T, N>(bprod));
      }
      delta[i] = a[i] * (rhs - b[i] * delta[i - 1]);
      a[i] = a[i] * c[i];
    }
  }

  // SaveCoefficients(a, delta, il, iu);
  // if (!last_block) SendBuffer(a[iu], delta[iu], tblock);
}

}  // namespace snap

#undef VOL
#undef DU
#undef W
