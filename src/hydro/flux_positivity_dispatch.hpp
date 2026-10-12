#pragma once

// torch
#include <ATen/native/DispatchStub.h>
#include <torch/torch.h>

namespace at::native {

//! SNAP_FUSED_CARRY: flux_positivity_carry_ + flux_positivity_scale_ of one
//! direction in one pass (flux_positivity_impl.h)
using positivity_carry_scale_fn = void (*)(
    torch::Tensor const& flux, torch::Tensor const& theta,
    torch::Tensor const& hspec, torch::Tensor const& vel,
    torch::Tensor const& fsed, int dim, int lo, int hi);

DECLARE_DISPATCH(positivity_carry_scale_fn, call_positivity_carry_scale);

}  // namespace at::native
