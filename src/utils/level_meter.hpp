#pragma once
// [SCAFFOLDING] SNAPY_METER -- per-x1-level tallies of SILENT repairs.
//
// S49 (2026-08-21): the ISSI h150/5-layer black box caught the dying cell
// sitting at EXACTLY the 20 K energy floor after ONE RK stage, at level 105 of
// 150 -- a silent repair firing deep in the interior of the column. Nothing in
// either snapy or ExoCubed counts these today, so "the floor fires at the lid
// every step" and "it never fires in the interior" have both been asserted and
// neither measured.
//
// This is a DIAGNOSTIC BUILD ONLY: gated on the SNAPY_METER env var, allocates
// on first use, and costs one device->host reduction per metered predicate per
// call. NOT for upstream.
//
// Every tensor snapy meters here is laid out with x1 (the vertical level) LAST,
// so "per level" is always "reduce every dim but the last".

#include <torch/torch.h>

#include <cstdlib>
#include <iostream>
#include <string>

namespace snap {

inline bool snapy_meter_on() {
  static const bool on = std::getenv("SNAPY_METER") != nullptr;
  return on;
}

//! Per-level counter for one boolean predicate.
class LevelMeter {
 public:
  explicit LevelMeter(std::string name) : name_(std::move(name)) {}

  //! Accumulate `bad` (any shape, x1 last). Cheap no-op if the meter is off.
  void add(torch::Tensor const& bad) {
    if (!bad.defined()) return;
    auto f = bad.to(torch::kInt64);
    while (f.dim() > 1) f = f.sum(0);
    f = f.to(torch::kCPU);
    if (!count_.defined()) {
      count_ = torch::zeros({f.size(0)},
                            torch::TensorOptions().dtype(torch::kInt64));
    }
    count_ += f;
    total_ += f.sum().item<int64_t>();
  }

  //! Track the worst relative excursion below a floor: (floor - x)/|floor|.
  void worst(torch::Tensor const& x, torch::Tensor const& floor) {
    if (!x.defined() || !floor.defined()) return;
    auto r = ((floor - x) / floor.abs().clamp_min(1e-300)).max().item<double>();
    if (r > worst_) worst_ = r;
  }

  int64_t total() const { return total_; }

  void report(std::string const& prefix) const {
    if (total_ == 0) {
      std::cout << "[METER] " << prefix << name_ << " NEVER FIRED\n";
      return;
    }
    std::cout << "[METER] " << prefix << name_ << " total=" << total_;
    if (worst_ > -1e299) std::cout << " worst_rel_deficit=" << worst_;
    std::cout << " by level:";
    for (int64_t i = 0; i < count_.size(0); ++i) {
      auto v = count_[i].item<int64_t>();
      if (v > 0) std::cout << " " << i << ":" << v;
    }
    std::cout << "\n";
  }

 private:
  std::string name_;
  torch::Tensor count_;
  int64_t total_ = 0;
  double worst_ = -1e300;
};

}  // namespace snap
