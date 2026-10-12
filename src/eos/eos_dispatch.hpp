#pragma once

// torch
#include <ATen/TensorIterator.h>
#include <ATen/native/DispatchStub.h>

namespace at::native {

using ideal_gas_fn = void (*)(at::TensorIterator &iter, double gammad);
// count: the caller reads the failure count (on CUDA a device-to-host read)
using fix_vapor_fn = int (*)(at::TensorIterator &iter, bool count);

DECLARE_DISPATCH(ideal_gas_fn, ideal_gas_cons2prim);
DECLARE_DISPATCH(fix_vapor_fn, call_fix_vapor);

}  // namespace at::native

namespace snap {

//! SNAP_DEVICE_FIX_VAPOR=1 (perf study, default off): on CUDA the vapor
//! repair's failure count is not read back after every call (one host sync
//! per conserved-limiter call with species); it accumulates in
//! fix_vapor_failures() and MeshBlock::check_redo reads it with its one
//! device-to-host copy, raising the same error there
bool device_fix_vapor();

//! running failure count of the vapor repair on `device` (0-d int32)
at::Tensor& fix_vapor_failures(c10::Device device);

}  // namespace snap
