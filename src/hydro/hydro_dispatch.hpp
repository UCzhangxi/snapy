#pragma once

// torch
#include <ATen/native/DispatchStub.h>
#include <torch/torch.h>

namespace at::native {

using hydro_ref_x1_fn = void (*)(
    torch::Tensor const& w, torch::Tensor const& dx1f,
    torch::Tensor const& anchor, torch::Tensor const& psf_lo,
    torch::Tensor const& psf_hi, torch::Tensor const& pref,
    torch::Tensor const& dsf, torch::Tensor const& dref, int iu, double grav,
    bool uniform, bool phys_in, bool phys_out, bool wall_clamp);

DECLARE_DISPATCH(hydro_ref_x1_fn, call_hydro_ref_x1);

//! SNAP_FUSED_COV: flux += covariance rows (flux_covariance_impl.h)
using flux_covariance_fn = void (*)(torch::Tensor const& flux,
                                    torch::Tensor const& wbar,
                                    torch::Tensor const& enth,
                                    torch::Tensor const& s2,
                                    torch::Tensor const& x1v, int ny, int iun);

DECLARE_DISPATCH(flux_covariance_fn, call_flux_covariance);

}  // namespace at::native
