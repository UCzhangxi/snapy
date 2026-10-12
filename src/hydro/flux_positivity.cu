// torch
#include <ATen/Dispatch.h>
#include <ATen/cuda/CUDAContext.h>
#include <c10/cuda/CUDAGuard.h>

// snap
#include "flux_positivity_dispatch.hpp"
#include "flux_positivity_impl.h"

namespace snap {

template <typename T>
__global__ void positivity_carry_scale_kernel(T* flux, T const* theta,
                                              T const* hspec, T const* vel,
                                              T const* fsed, int64_t ncell,
                                              int ny, int64_t dstride, int dim,
                                              int lo, int nf, int nc3, int nc2,
                                              int nc1, int64_t nface) {
  int64_t t = blockIdx.x * (int64_t)blockDim.x + threadIdx.x;
  if (t >= nface) return;
  int64_t upper = positivity_face_index(t, dim, lo, nf, nc3, nc2, nc1);
  positivity_carry_scale_face(flux, theta, hspec, vel, fsed, ncell, ny, upper,
                              dstride);
}

void positivity_carry_scale_cuda(torch::Tensor const& flux,
                                 torch::Tensor const& theta,
                                 torch::Tensor const& hspec,
                                 torch::Tensor const& vel,
                                 torch::Tensor const& fsed, int dim, int lo,
                                 int hi) {
  at::cuda::CUDAGuard device_guard(flux.device());
  TORCH_CHECK(flux.is_contiguous(), "fused carry: flux must be contiguous");
  auto th = theta.contiguous(), hs = hspec.contiguous(), v = vel.contiguous();
  auto fs = fsed.defined() ? fsed.contiguous() : torch::Tensor();
  int nc3 = flux.size(1), nc2 = flux.size(2), nc1 = flux.size(3);
  int64_t ncell = int64_t(nc3) * nc2 * nc1;
  int ny = th.size(0);
  int nf = hi + 2 - lo;
  int64_t dstride = dim == 3 ? 1 : dim == 2 ? nc1 : int64_t(nc1) * nc2;
  int64_t nface = ncell / flux.size(dim) * nf;
  if (nface <= 0) return;
  int threads = 256;
  int64_t blocks = (nface + threads - 1) / threads;
  auto stream = at::cuda::getCurrentCUDAStream();
  AT_DISPATCH_FLOATING_TYPES(flux.scalar_type(), "positivity_carry_scale", [&] {
    positivity_carry_scale_kernel<scalar_t><<<blocks, threads, 0, stream>>>(
        flux.data_ptr<scalar_t>(), th.data_ptr<scalar_t>(),
        hs.data_ptr<scalar_t>(), v.data_ptr<scalar_t>(),
        fs.defined() ? fs.data_ptr<scalar_t>() : nullptr, ncell, ny, dstride,
        dim, lo, nf, nc3, nc2, nc1, nface);
  });
  C10_CUDA_KERNEL_LAUNCH_CHECK();
}

}  // namespace snap

namespace at::native {

REGISTER_CUDA_DISPATCH(call_positivity_carry_scale,
                       &snap::positivity_carry_scale_cuda);

}  // namespace at::native
