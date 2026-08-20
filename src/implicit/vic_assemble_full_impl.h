#pragma once

// base
#include <configure.h>

// snap
#include "flux_decomposition_impl.h"

#define GAMMA(n) gamma[(n) * stride2]
#define AREA(n) area[(n) * stride2]
#define VOL(n) vol[(n) * stride2]

namespace snap {

template <typename T>
void DISPATCH_MACRO vic_assemble_full_impl(
    Eigen::Matrix<T, 5, 5>* a, Eigen::Matrix<T, 5, 5>* b,
    Eigen::Matrix<T, 5, 5>* c, T* w, T* gamma, T* area, T* vol, int i, int is,
    int ie, double dt, double grav, int dir, int ny, int stride1, int stride2,
    bool first_block, bool last_block, bool periodic) {
  // eigenvectors, eigenvalues, inverse matrix of eigenvectors.
  Eigen::Matrix<T, 5, 5> Rmat, Rimat;
  Eigen::Matrix<T, 5, 1> Lambda;

  // reduced diffusion matrix |A_{i-1/2}|, |A_{i+1/2}|
  Eigen::Matrix<T, 5, 5> Am, Ap;
  Eigen::Matrix<T, 5, 5> dfdq_prev, dfdq_curr, dfdq_next;

  Eigen::Matrix<T, 5, 5> Phi;
  Eigen::Matrix<T, 5, 1> Dt, Bnd;

  Phi.setZero();
  Phi(IVX + dir, IDN) = grav;
  Phi(IPR, IVX + dir) = grav;

  Dt.setConstant(1. / dt);

  Bnd.setConstant(1.);
  Bnd(IVX + dir) = -1;

  T prim[5];       // Roe averaged primitive variables of cell i-1/2
  T wl[5], wr[5];  // left/right primitive variables of cell i-1 and i
  T gm1, cs;

  // Interface i-1/2 and the Jacobians in cells i-1 and i.
  CopyPrimitives(wl, wr, w, i, stride1, stride2, ny);
  gm1 = GAMMA(i - 1) - 1.;
  FluxJacobian(dfdq_prev, gm1, wl, dir);
  gm1 = GAMMA(i) - 1.;
  FluxJacobian(dfdq_curr, gm1, wr, dir);

  gm1 = 0.5 * (GAMMA(i - 1) + GAMMA(i)) - 1.;
  RoeAverage(prim, gm1, wl, wr);

  cs = SoundSpeed(prim, gm1);
  Eigenvalue(Lambda, prim[IVX + dir], cs);
  Eigenvector(Rmat, Rimat, prim, cs, gm1, dir);

  Am.noalias() = Rmat * Lambda.asDiagonal() * Rimat;

  // Interface i+1/2 and the Jacobian in cell i+1.
  CopyPrimitives(wl, wr, w, i + 1, stride1, stride2, ny);
  gm1 = GAMMA(i + 1) - 1.;
  FluxJacobian(dfdq_next, gm1, wr, dir);

  gm1 = 0.5 * (GAMMA(i) + GAMMA(i + 1)) - 1.;
  RoeAverage(prim, gm1, wl, wr);

  cs = SoundSpeed(prim, gm1);
  Eigenvalue(Lambda, prim[IVX + dir], cs);
  Eigenvector(Rmat, Rimat, prim, cs, gm1, dir);

  Ap.noalias() = Rmat * Lambda.asDiagonal() * Rimat;

  // At a reflecting lid the first-order Roe closure under-represents the
  // dissipation the explicit weno5 shock path applies through the mirror ghost
  // to the last cell's normal momentum (measured 4.4x isothermal / 4.6x
  // guillot, ISSUES S44); below ~4x the corrected map carries an unstable lid
  // mode, above it the map is insensitive to the factor (4/6/16/100 agree to
  // 3 digits). Scale the wall-face diffusion into that saturated regime.
  // S44 lid A/B: the ad-hoc 8x wall-face diffusion is REMOVED on this
  // branch (measured inert at rest on the fixed reference; this build is
  // the dynamic A/B the retirement decision needs).  Stock: Ap *= 8.
  // if (i == ie && last_block && !periodic) Ap *= 8.;

  T const& area_i = AREA(i);
  T const& area_ip1 = AREA(i + 1);
  T half_inv_vol = 0.5 / VOL(i);

  // Set up diagonals a, b, c, and the forcing-function Jacobian.
  a[i] = (Am * area_i + Ap * area_ip1 + (area_ip1 - area_i) * dfdq_curr) *
             half_inv_vol -
         Phi;
  a[i].diagonal() += Dt;
  b[i] = -(Am + dfdq_prev) * area_i * half_inv_vol;
  c[i] = -(Ap - dfdq_next) * area_ip1 * half_inv_vol;

  // Fix boundary conditions for the cells at the ends of the column.
  if (i == is && first_block && !periodic) a[i] += b[i] * Bnd.asDiagonal();
  if (i == ie && last_block && !periodic) a[i] += c[i] * Bnd.asDiagonal();
}

}  // namespace snap

#undef GAMMA
#undef AREA
#undef VOL
