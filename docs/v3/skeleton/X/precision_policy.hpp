#pragma once
// Lane X skeleton: declarations only, in no build.
// One table of dtypes per quantity, built once from dynamics.precision.
// Replaces every `fp32() ? a : b` (src/hydro/hydro.hpp:332 and its 29 callers).
#include <array>
#include <string>
#include <torch/torch.h>

namespace snap {

//! the quantities with a fixed dtype contract (design section 6)
enum class Quantity {
  kHydroState,   // hydro_u, anomaly form
  kBackup,       // u0, s0: always the storage dtype
  kScalarState,  // scalar_s
  kFlux,         // fluxes, du
  kReference,    // reference and geometry masters
  kPrimitive,    // hydro_w totals
  kGauge,        // gauges, total face pressure
  kReduction,    // dt, budgets, fixer sums
  kImplicit,     // vertical implicit correction (FP64 fallback)
  kThermo,       // kintera totals, saturation
  kRegister,     // flux-register step accumulator
  kCount
};

struct DtypeRow {
  torch::Dtype storage;
  torch::Dtype compute;
};

class PrecisionPolicy {
 public:
  //! "float64" or "float32", as read at src/hydro/hydro_options.cpp:67
  explicit PrecisionPolicy(std::string const& precision, torch::Device device);

  bool fp32() const;
  DtypeRow const& row(Quantity q) const;
  torch::Dtype storage(Quantity q) const;
  torch::Dtype compute(Quantity q) const;

  //! x in the compute dtype of q; returns x itself when it already is
  torch::Tensor cast(Quantity q, torch::Tensor const& x) const;
  //! x rounded to the storage dtype of q (the only place storage rounding occurs)
  torch::Tensor store(Quantity q, torch::Tensor const& x) const;

  //! part of every GraphKey: a policy change invalidates graphs
  int generation() const;

 private:
  std::array<DtypeRow, static_cast<int>(Quantity::kCount)> rows_;
  int generation_;
};

}  // namespace snap
