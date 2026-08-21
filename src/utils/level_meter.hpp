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
// DIAGNOSTIC BUILD ONLY: gated on the SNAPY_METER env var, allocates on first
// use, and costs a device->host reduction per metered predicate per call. NOT
// upstream.
//
// Every tensor metered here is laid out with x1 (the vertical level) LAST,
// whatever direction is being reconstructed, so "per level" is always "reduce
// every dim but the last". LEVEL INDICES ARE ABSOLUTE TENSOR INDICES AND
// INCLUDE THE GHOSTS -- report() prints il/iu and splits the total into
// interior and ghost, because "did it fire in the INTERIOR" is the entire
// question.

#include <torch/torch.h>

#include <cstdlib>
#include <iostream>
#include <string>

namespace snap {

inline bool snapy_meter_on() {
  static const bool on = std::getenv("SNAPY_METER") != nullptr;
  return on;
}

inline std::string snapy_meter_rank() {
  static const std::string r =
      std::getenv("RANK") ? std::getenv("RANK") : std::string("0");
  return r;
}

//! Per-level counter for one boolean predicate.
class LevelMeter {
 public:
  explicit LevelMeter(std::string name) : name_(std::move(name)) {}

  //! Record the interior bounds so report() can split interior from ghost.
  void geometry(int il, int iu) {
    il_ = il;
    iu_ = iu;
  }

  //! Accumulate `bad` (any shape, x1 last).
  void add(torch::Tensor const& bad) {
    if (!bad.defined()) return;
    auto f = bad.to(torch::kInt64);
    while (f.dim() > 1) f = f.sum(0);
    f = f.to(torch::kCPU);
    if (!count_.defined()) {
      count_ = torch::zeros({f.size(0)},
                            torch::TensorOptions().dtype(torch::kInt64));
    } else if (count_.size(0) != f.size(0)) {
      std::cout << "[METER] " << name_ << " SHAPE CHANGED " << count_.size(0)
                << " -> " << f.size(0) << "; meter abandoned\n";
      broken_ = true;
    }
    if (broken_) return;
    count_ += f;
    total_ += f.sum().item<int64_t>();
  }

  //! Worst relative excursion below `floor`, INTERIOR ONLY, with its level.
  //! A NaN anywhere is reported separately instead of silently losing the max.
  void worst(torch::Tensor const& x, torch::Tensor const& floor, int il,
             int iu) {
    if (!x.defined() || !floor.defined() || iu < il) return;
    auto n = iu - il + 1;
    auto d = ((floor - x) / floor.abs().clamp_min(1e-300)).narrow(-1, il, n);
    if (torch::isnan(d).any().item<bool>()) nan_seen_ = true;
    auto flat = torch::nan_to_num(d, -1e300, 1e300, -1e300).reshape(-1);
    auto idx = flat.argmax().item<int64_t>();
    auto v = flat[idx].item<double>();
    if (v > worst_) {
      worst_ = v;
      worst_lev_ = il + static_cast<int>(idx % n);
    }
  }

  int64_t total() const { return total_; }

  void report(std::string const& prefix) const {
    auto tag = "[METER] rank=" + snapy_meter_rank() + " " + prefix + name_;
    if (total_ == 0 || !count_.defined()) {
      std::cout << tag << " NEVER FIRED\n";
      return;
    }
    int64_t nin = 0;
    for (int64_t i = 0; i < count_.size(0); ++i)
      if (i >= il_ && i <= iu_) nin += count_[i].item<int64_t>();
    std::cout << tag << " total=" << total_ << " INTERIOR=" << nin
              << " ghost=" << (total_ - nin) << " (levels are ABSOLUTE tensor "
              << "indices 0.." << count_.size(0) - 1 << ", interior " << il_
              << ".." << iu_ << ")";
    if (worst_ > -1e299)
      std::cout << " worst_rel_deficit=" << worst_ << " at level "
                << worst_lev_;
    if (nan_seen_) std::cout << " [NaN seen in the deficit field]";
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
  int il_ = 0, iu_ = 1 << 30;
  double worst_ = -1e300;
  int worst_lev_ = -1;
  bool nan_seen_ = false;
  bool broken_ = false;
};

}  // namespace snap
