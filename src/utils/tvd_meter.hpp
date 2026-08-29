#pragma once
// [DIAGNOSTIC, S54 2026-08-23] SNAPY_TVD_METER -- a NON-ACTING count of
// reconstruction face states that fall outside the range of the two cells they
// sit between.  This is snapy's port of ExoCubed's "Meter B" (S53), which
// measured PLM horizontal at 0.000 % of 58 M faces and WENO5 horizontal at
// 28.4 %, and established that lifetime tracks that rate monotonically (F36).
//
// WHAT IS COUNTED, and why it is aligned by construction
// -----------------------------------------------------
// Every reconstruction in snapy funnels through ONE call site:
// `_apply_inplace` in src/recon/reconstruct.cpp, which is the only place in
// the whole tree that calls `pinterp->forward` (verified by grep, S54).  The
// interpolators all write, for cells j = 1 .. size-2 along `dim`:
//
//     outl[m] = cell j's LEFT-face  extrapolation      (m = j - 1)
//     outr[m] = cell j's RIGHT-face extrapolation
//
// (see PLMInterpImpl::forward, src/recon/plm.cpp:32-33: it writes
//  `w.narrow(dim,1,size-2) -/+ 0.5*dwm` into the two output tensors, so both
//  are indexed by m with cell j = m+1.)  So the three cell slices
//
//     wm1 = w.narrow(dim, 0, size-2)   -> w[j-1]
//     w0  = w.narrow(dim, 1, size-2)   -> w[j]
//     wp1 = w.narrow(dim, 2, size-2)   -> w[j+1]
//
// line up with outl/outr elementwise with NO index arithmetic of our own.
// That is deliberate: S53's meter tallied after a downstream restore and
// consequently measured a reflecting wall instead of the operator.  Here the
// tally happens on the operator's own output, before ANY caller-side floor,
// clamp, wall revision or well-balanced reference restore touches it.
//
// MONOTONICITY TEST
//     outl must lie within [min(w[j-1], w[j]), max(w[j-1], w[j])]
//     outr must lie within [min(w[j],  w[j+1]), max(w[j],  w[j+1])]
// van Leer guarantees |dwm| <= 2*min(|dwl|,|dwr|), hence 0.5*|dwm| <= |dw| on
// either side, so a correct PLM must report exactly zero.  Two counts are kept:
// STRICT (bare comparison) and SLACK (allowing 1e-12 * (|w[j-1]|+|w[j]|)), so
// that round-off can never be reported as a finding.
//
// COST / SAFETY: gated on the SNAPY_TVD_METER env var; reads only; allocates
// its own temporaries; never writes w or wlr.  Two device->host reductions per
// metered call.  DIAGNOSTIC BUILD ONLY -- not upstream.

#include <torch/torch.h>

#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <map>
#include <string>
#include <utility>
#include <vector>

//! Bump on EVERY edit. ops greps the installed .so for this exact string;
//! a stale pip build is otherwise completely silent (S54, 2026-08-23).
#define SNAPY_TVD_METER_BUILD "S54-TVD-BUILD-0010"

namespace snap {

inline bool tvd_meter_on() {
  static const bool on = std::getenv("SNAPY_TVD_METER") != nullptr;
  return on;
}

inline int64_t tvd_meter_every() {
  static const int64_t n =
      std::getenv("SNAPY_TVD_METER_EVERY")
          ? std::atoll(std::getenv("SNAPY_TVD_METER_EVERY"))
          : 2000;
  return n > 0 ? n : 2000;
}

inline std::string tvd_meter_rank() {
  static const std::string r =
      std::getenv("RANK") ? std::getenv("RANK") : std::string("0");
  return r;
}

//! one (direction, variable) tally
struct TvdCell {
  int64_t faces = 0;   //!< face states examined (left + right)
  int64_t strict = 0;  //!< outside [min,max] by any amount
  int64_t slack = 0;   //!< outside by more than 1e-12 * local scale
};

class TvdMeter {
 public:
  static std::map<std::pair<int, int>, TvdCell>& table() {
    // leaked ON PURPOSE: read by ~TvdMeterFinal at teardown, and a
    // function-local static would already have been destroyed by then.
    static auto* t = new std::map<std::pair<int, int>, TvdCell>();
    return *t;
  }
  static int64_t& calls() {
    static auto* c = new int64_t(0);
    return *c;
  }

  //! \brief tally one reconstruction. NON-ACTING.
  //! \param dim        tensor dim being reconstructed (DIM1=3, DIM2=2, DIM3=1)
  //! \param var_offset global variable index of local channel 0
  //! \param w          cell values, shape [nvar_local, ...]
  //! \param outl,outr  the operator's own left/right face extrapolations
  static void tally(int dim, int var_offset, torch::Tensor const& w,
                    torch::Tensor const& outl, torch::Tensor const& outr) {
    if (!tvd_meter_on()) return;
    auto size = w.size(dim);
    if (size < 3) return;
    // GENERAL alignment, derived -- not assumed.  InterpImpl::forward
    // (interpolation.hpp:64-65) sizes its output as size-(stencils-1) and every
    // stencil is centred, so output index m maps to cell j = m + h with
    //     h = (size - count) / 2,   count = the operator's own output length.
    // PLM (stencils 3) gives h = 1; cp5/weno5 (stencils 5) give h = 2.
    const int64_t count = outl.size(dim);
    if (outr.size(dim) != count) return;
    const int64_t h = (size - count) / 2;
    // need w[j-1] .. w[j+1] in range, and a centred odd stencil
    if (h < 1 || (size - count) % 2 != 0 || h + 1 + count > size) {
      static bool warned = false;
      if (!warned) {
        std::cerr << "[S54-TVD] SKIP dim=" << dim << ": size=" << size
                  << " count=" << count
                  << " -- cannot derive a centred alignment, not tallying\n";
        warned = true;
      }
      return;
    }

    torch::NoGradGuard nograd;
    auto wm1 = w.narrow(dim, h - 1, count);
    auto w0 = w.narrow(dim, h, count);
    auto wp1 = w.narrow(dim, h + 1, count);

    auto lo_l = torch::minimum(wm1, w0);
    auto hi_l = torch::maximum(wm1, w0);
    auto lo_r = torch::minimum(w0, wp1);
    auto hi_r = torch::maximum(w0, wp1);

    auto eps_l = 1e-12 * (wm1.abs() + w0.abs());
    auto eps_r = 1e-12 * (w0.abs() + wp1.abs());

    auto bad_l = (outl < lo_l).logical_or(outl > hi_l);
    auto bad_r = (outr < lo_r).logical_or(outr > hi_r);
    auto slk_l = (outl < lo_l - eps_l).logical_or(outl > hi_l + eps_l);
    auto slk_r = (outr < lo_r - eps_r).logical_or(outr > hi_r + eps_r);

    // reduce every dim but the variable dim (0) -> [nvar_local]
    auto reduce = [](torch::Tensor const& m) {
      auto f = m.to(torch::kInt64);
      while (f.dim() > 1) f = f.sum(-1);
      return f.to(torch::kCPU);
    };
    auto cs = reduce(bad_l) + reduce(bad_r);
    auto ck = reduce(slk_l) + reduce(slk_r);

    int64_t per_var = 2 * bad_l.numel() / bad_l.size(0);
    auto as = cs.accessor<int64_t, 1>();
    auto ak = ck.accessor<int64_t, 1>();
    for (int c = 0; c < cs.size(0); ++c) {
      auto& e = table()[{dim, var_offset + c}];
      e.faces += per_var;
      e.strict += as[c];
      e.slack += ak[c];
    }
  }

  static const char* dim_name(int dim) {
    switch (dim) {
      case 3:
        return "x1(vert)";
      case 2:
        return "x2(horz)";
      case 1:
        return "x3(horz)";
      default:
        return "x?";
    }
  }
  static const char* var_name(int v) {
    switch (v) {
      case 0:
        return "rho ";
      case 1:
        return "vel1";
      case 2:
        return "vel2";
      case 3:
        return "vel3";
      case 4:
        return "pres";
      default:
        return "othr";
    }
  }

  static void report(const char* tag) {
    if (!tvd_meter_on()) return;
    std::cout << "[S54-TVD] build=" << SNAPY_TVD_METER_BUILD << "\n";
    for (auto const& kv : table()) {
      auto const& e = kv.second;
      double ps = e.faces ? 100.0 * e.strict / e.faces : 0.0;
      double pk = e.faces ? 100.0 * e.slack / e.faces : 0.0;
      char buf[320];
      snprintf(buf, sizeof(buf),
               "[S54-TVD] %s rank=%s %s %s faces=%lld strict=%lld (%.4f %%) "
               "slack=%lld (%.4f %%)",
               tag, tvd_meter_rank().c_str(), dim_name(kv.first.first),
               var_name(kv.first.second), (long long)e.faces,
               (long long)e.strict, ps, (long long)e.slack, pk);
      std::cout << buf << "\n";
    }
    std::cout.flush();
  }

  static void tick() {
    if (!tvd_meter_on()) return;
    if (++calls() % tvd_meter_every() == 0) report("PROGRESS");
  }
};

//! \brief DELIVERED-state monotonicity: the pair the Riemann solver actually
//! consumes, AFTER the well-balanced reference restore and its positivity
//! fallbacks. Complements TvdMeter::tally, which measures the raw operator.
//!
//! Alignment (derived from reconstruct.cpp:50-53, see tvd_meter.hpp header):
//!   wlr[IRT][i] = cell i's LEFT  extrapolation  = the RIGHT state at face i
//!   wlr[ILT][i] = cell i-1's RIGHT extrapolation = the LEFT  state at face i
//! so face i sits between cells i-1 and i, and BOTH delivered states must lie
//! within [min,max] of those two cells.
class FaceMeter {
 public:
  struct Cell {
    int64_t faces = 0, badL = 0, badR = 0;
  };
  static std::map<std::string, Cell>& table() {
    static auto* t = new std::map<std::string, Cell>();
    return *t;
  }
  //! per-level firing counts for the positivity fallbacks
  static std::map<std::string, std::vector<int64_t>>& levels() {
    static auto* t = new std::map<std::string, std::vector<int64_t>>();
    return *t;
  }

  //! \param name  label, e.g. "x1.dens" / "x1.pres"
  //! \param cm1,c0  cell values at i-1 and i   (FULL variables)
  //! \param fL,fR   delivered left/right state at face i
  static void tally(std::string const& name, torch::Tensor const& cm1,
                    torch::Tensor const& c0, torch::Tensor const& fL,
                    torch::Tensor const& fR) {
    if (!tvd_meter_on()) return;
    torch::NoGradGuard nograd;
    auto lo = torch::minimum(cm1, c0);
    auto hi = torch::maximum(cm1, c0);
    auto bl = (fL < lo).logical_or(fL > hi);
    auto br = (fR < lo).logical_or(fR > hi);
    auto& e = table()[name];
    e.faces += bl.numel();
    e.badL += bl.sum().item<int64_t>();
    e.badR += br.sum().item<int64_t>();
    // WHERE are they?  x1 is the last dim, so a per-level histogram localises
    // the violation instead of leaving it as a column-integrated percentage.
    tally_levels(name + ".outsideL", bl);
    tally_levels(name + ".outsideR", br);
  }

  //! \brief per-x1-level tally of a boolean mask (x1 is the LAST dim)
  static void tally_levels(std::string const& name, torch::Tensor const& mask) {
    if (!tvd_meter_on()) return;
    torch::NoGradGuard nograd;
    auto f = mask.to(torch::kInt64);
    while (f.dim() > 1) f = f.sum(0);
    f = f.to(torch::kCPU);
    auto& v = levels()[name];
    if ((int64_t)v.size() < f.size(0)) v.resize(f.size(0), 0);
    auto a = f.accessor<int64_t, 1>();
    for (int64_t i = 0; i < f.size(0); ++i) v[i] += a[i];
  }

  //! running maxima of scalar diagnostics
  static std::map<std::string, double>& maxima() {
    static auto* t = new std::map<std::string, double>();
    return *t;
  }
  static void note_max(std::string const& name, double v) {
    if (!tvd_meter_on()) return;
    auto it = maxima().find(name);
    if (it == maxima().end() || v > it->second) maxima()[name] = v;
  }

  static void report(const char* tag) {
    if (!tvd_meter_on()) return;
    for (auto const& kv : maxima())
      std::cout << "[S54-VIC] " << tag << " rank=" << tvd_meter_rank() << " "
                << kv.first << " max=" << kv.second << "\n";
    for (auto const& kv : table()) {
      auto const& e = kv.second;
      double pl = e.faces ? 100.0 * e.badL / e.faces : 0.0;
      double pr = e.faces ? 100.0 * e.badR / e.faces : 0.0;
      char b[320];
      snprintf(b, sizeof(b),
               "[S54-FACE] %s rank=%s %-9s faces=%lld outside_L=%lld (%.4f %%) "
               "outside_R=%lld (%.4f %%)",
               tag, tvd_meter_rank().c_str(), kv.first.c_str(),
               (long long)e.faces, (long long)e.badL, pl, (long long)e.badR,
               pr);
      std::cout << b << "\n";
    }
    for (auto const& kv : levels()) {
      int64_t tot = 0, nz = 0, lo = -1, hi = -1;
      for (size_t i = 0; i < kv.second.size(); ++i)
        if (kv.second[i]) {
          tot += kv.second[i];
          ++nz;
          if (lo < 0) lo = (int64_t)i;
          hi = (int64_t)i;
        }
      std::cout << "[S54-FB] " << tag << " rank=" << tvd_meter_rank() << " "
                << kv.first << " events=" << tot << " levels_firing=" << nz
                << " lowest=" << lo << " highest=" << hi << "\n";
      if (tot) {
        std::cout << "[S54-FB]   per-level(nonzero):";
        int shown = 0;
        for (size_t i = 0; i < kv.second.size() && shown < 200; ++i)
          if (kv.second[i]) {
            std::cout << " " << i << ":" << kv.second[i];
            ++shown;
          }
        std::cout << "\n";
      }
    }
    std::cout.flush();
  }
};

//! Emit a FINAL line at process teardown so a run that dies still reports.
struct TvdMeterFinal {
  ~TvdMeterFinal() {
    TvdMeter::report("FINAL");
    FaceMeter::report("FINAL");
  }
};
static TvdMeterFinal _tvd_meter_final_instance;

}  // namespace snap
