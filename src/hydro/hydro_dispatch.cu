// torch
#include <ATen/Dispatch.h>
#include <ATen/cuda/CUDAContext.h>
#include <c10/cuda/CUDAGuard.h>

// C/C++
#include <cstdlib>
#include <limits>
#include <string>

// snap
#include "hydro_dispatch.hpp"
#include "flux_covariance_impl.h"
#include "hydro_ref_x1_impl.h"

namespace snap {

template <typename T>
__global__ void
hydro_ref_x1_cuda_kernel(T const *w, T const *dx1f, T const *anchor,
                         T *psf_lo, T *psf_hi, T *pref, T *dsf, T *dref,
                         int ncolumns, int nc1, int iu, T grav, bool uniform,
                         bool phys_in, bool phys_out, bool wall_clamp) {
  int column = blockIdx.x;

  if (threadIdx.x == 0) {
    hydro_ref_x1_scan_impl(w, dx1f, anchor, psf_lo, psf_hi, column, ncolumns,
                           nc1, iu, grav);
  }
  __syncthreads();

  for (int i = threadIdx.x; i < nc1; i += blockDim.x) {
    hydro_ref_x1_cell_impl(w, dx1f, psf_lo, psf_hi, pref, dsf, dref, column, i,
                           ncolumns, nc1, iu, grav, uniform, phys_in, phys_out,
                           wall_clamp);
  }
}

// SNAP_REF_X1_SMEM=1 (perf study, default off): the same arithmetic as
// hydro_ref_x1_cuda_kernel, with the column staged in shared memory. Every
// thread forms grav * rho * dx1f (the scan increments) and rho/p of its cells;
// thread 0 runs the serial scan over shared memory instead of global loads, and
// each cell's smoothed rho/p is formed once (it was formed twice: rs and the
// rf of the cell above).
template <typename T>
__global__ void
hydro_ref_x1_smem_kernel(T const *w, T const *dx1f, T const *anchor,
                         T *psf_lo, T *psf_hi, T *pref, T *dsf, T *dref,
                         int ncolumns, int nc1, int iu, T grav, bool uniform,
                         bool phys_in, bool phys_out, bool wall_clamp) {
  extern __shared__ unsigned char smem_raw[];
  T *gw = reinterpret_cast<T *>(smem_raw);  // grav * rho, nc1
  T *dx = gw + nc1;                         // dx1f, nc1
  T *rop = dx + nc1;                        // rho / p, nc1
  T *rs = rop + nc1;                        // smoothed rho / p, nc1
  int column = blockIdx.x;
  int ncells = ncolumns * nc1;
  int flat = column * nc1;

  for (int i = threadIdx.x; i < nc1; i += blockDim.x) {
    // grav * rho is rounded on its own in the global-memory kernel too; the
    // scan keeps `face + gw * dx` in one expression, so nvcc contracts it the
    // same way (fma(gw, dx, face)) as `face + grav * rho * dx1f` there
    gw[i] = grav * w[IDN * ncells + flat + i];
    dx[i] = dx1f[i];
    rop[i] = w[IDN * ncells + flat + i] / w[IPR * ncells + flat + i];
  }
  __syncthreads();

  if (threadIdx.x == 0) {
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
      T d = gw[i] * dx[i];
      T lo = face + d;
      T hi = face;
      psf_lo[flat + i] = lo > min_positive ? lo : min_positive;
      psf_hi[flat + i] = hi > min_positive ? hi : min_positive;
      face = lo;
    }
    face = top_anchor;
    for (int i = iu + 1; i < nc1; ++i) {
      T d = gw[i] * dx[i];
      T lo = face;
      T hi = lo - d;
      psf_lo[flat + i] = lo > min_positive ? lo : min_positive;
      psf_hi[flat + i] = hi > min_positive ? hi : min_positive;
      face = hi;
    }
  }

  int jlo, jhi;
  bool ext_lo, ext_hi;
  hydro_ref_x1_window(nc1, iu, phys_in, phys_out, wall_clamp, &jlo, &jhi,
                      &ext_lo, &ext_hi);
  auto rop_at = [&](int j) { return rop[j]; };
  for (int i = threadIdx.x; i < nc1; i += blockDim.x)
    rs[i] = hydro_ref_x1_rop_smooth_with<T>(rop_at, i, jlo, jhi, ext_lo,
                                            ext_hi);
  __syncthreads();

  for (int i = threadIdx.x; i < nc1; i += blockDim.x) {
    hydro_ref_x1_cell_impl(w, dx1f, psf_lo, psf_hi, pref, dsf, dref, column, i,
                           ncolumns, nc1, iu, grav, uniform, phys_in, phys_out,
                           wall_clamp, static_cast<T const *>(rs));
  }
}

void hydro_ref_x1_cuda(torch::Tensor const &w, torch::Tensor const &dx1f,
                       torch::Tensor const &anchor,
                       torch::Tensor const &psf_lo,
                       torch::Tensor const &psf_hi,
                       torch::Tensor const &pref, torch::Tensor const &dsf,
                       torch::Tensor const &dref, int iu, double grav,
                       bool uniform, bool phys_in, bool phys_out, bool wall_clamp) {
  at::cuda::CUDAGuard device_guard(w.device());
  int ncolumns = w.size(1) * w.size(2);
  int nc1 = w.size(3);
  int threads = 256;
  int blocks = ncolumns;
  auto stream = at::cuda::getCurrentCUDAStream();

  static bool const smem = [] {
    char const *v = std::getenv("SNAP_REF_X1_SMEM");
    std::string s = v ? v : "0";
    return s == "1" || s == "true" || s == "on" || s == "yes";
  }();
  AT_DISPATCH_FLOATING_TYPES(w.scalar_type(), "hydro_ref_x1_cuda", [&] {
    auto anchor_ptr = anchor.defined() ? anchor.data_ptr<scalar_t>() : nullptr;
    size_t shmem = 4 * size_t(nc1) * sizeof(scalar_t);
    if (smem && shmem <= 48 * 1024) {
      hydro_ref_x1_smem_kernel<<<blocks, threads, shmem, stream>>>(
          w.data_ptr<scalar_t>(), dx1f.data_ptr<scalar_t>(), anchor_ptr,
          psf_lo.data_ptr<scalar_t>(), psf_hi.data_ptr<scalar_t>(),
          pref.data_ptr<scalar_t>(), dsf.data_ptr<scalar_t>(),
          dref.data_ptr<scalar_t>(), ncolumns, nc1, iu, scalar_t(grav),
          uniform, phys_in, phys_out, wall_clamp);
      return;
    }
    hydro_ref_x1_cuda_kernel<<<blocks, threads, 0, stream>>>(
        w.data_ptr<scalar_t>(), dx1f.data_ptr<scalar_t>(), anchor_ptr,
        psf_lo.data_ptr<scalar_t>(), psf_hi.data_ptr<scalar_t>(),
        pref.data_ptr<scalar_t>(), dsf.data_ptr<scalar_t>(),
        dref.data_ptr<scalar_t>(), ncolumns, nc1, iu, scalar_t(grav), uniform,
        phys_in, phys_out, wall_clamp);
  });
  C10_CUDA_KERNEL_LAUNCH_CHECK();
}

template <typename T>
__global__ void flux_covariance_cuda_kernel(T *flux, T const *wbar,
                                            T const *enth, T const *s2,
                                            T const *x1v, int64_t ncell,
                                            int nvar, int ny, int iun,
                                            int nc1) {
  int64_t c = blockIdx.x * (int64_t)blockDim.x + threadIdx.x;
  if (c >= ncell) return;
  flux_covariance_cell(flux, wbar, enth, s2, x1v, ncell, nvar, ny, iun, nc1,
                       c);
}

void flux_covariance_cuda(torch::Tensor const &flux, torch::Tensor const &wbar,
                          torch::Tensor const &enth, torch::Tensor const &s2,
                          torch::Tensor const &x1v, int ny, int iun) {
  at::cuda::CUDAGuard device_guard(flux.device());
  TORCH_CHECK(flux.is_contiguous(), "fused covariance: flux must be contiguous");
  int nvar = flux.size(0);
  int nc1 = flux.size(-1);
  int64_t ncell = flux.numel() / nvar;
  int threads = 256;
  int64_t blocks = (ncell + threads - 1) / threads;
  auto stream = at::cuda::getCurrentCUDAStream();
  AT_DISPATCH_FLOATING_TYPES(flux.scalar_type(), "flux_covariance_cuda", [&] {
    flux_covariance_cuda_kernel<scalar_t><<<blocks, threads, 0, stream>>>(
        flux.data_ptr<scalar_t>(), wbar.data_ptr<scalar_t>(),
        enth.data_ptr<scalar_t>(), s2.data_ptr<scalar_t>(),
        x1v.data_ptr<scalar_t>(), ncell, nvar, ny, iun, nc1);
  });
  C10_CUDA_KERNEL_LAUNCH_CHECK();
}

} // namespace snap

namespace at::native {

REGISTER_CUDA_DISPATCH(call_hydro_ref_x1, &snap::hydro_ref_x1_cuda);
REGISTER_CUDA_DISPATCH(call_flux_covariance, &snap::flux_covariance_cuda);

} // namespace at::native
