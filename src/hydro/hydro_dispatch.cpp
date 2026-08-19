// torch
#include <ATen/Dispatch.h>
#include <ATen/Parallel.h>

// C/C++
#include <limits>

// snap
#include "hydro_dispatch.hpp"
#include "hydro_ref_x1_impl.h"

namespace snap {

void hydro_ref_x1_cpu(torch::Tensor const& w, torch::Tensor const& dx1f,
                      torch::Tensor const& anchor, torch::Tensor const& gam,
                      torch::Tensor const& kbot, torch::Tensor const& psf_lo,
                      torch::Tensor const& psf_hi, torch::Tensor const& pref,
                      torch::Tensor const& dsf, torch::Tensor const& dref,
                      int is, int iu, double grav, bool uniform, bool phys_in,
                      bool phys_out) {
  int ncolumns = w.size(1) * w.size(2);
  int nc1 = w.size(3);
  AT_DISPATCH_FLOATING_TYPES(w.scalar_type(), "hydro_ref_x1_cpu", [&] {
    auto anchor_ptr = anchor.defined() ? anchor.data_ptr<scalar_t>() : nullptr;
    auto kbot_ptr = kbot.defined() ? kbot.data_ptr<scalar_t>() : nullptr;
    at::parallel_for(0, ncolumns, 0, [&](int64_t begin, int64_t end) {
      for (int64_t column = begin; column < end; ++column) {
        hydro_ref_x1_impl(
            w.data_ptr<scalar_t>(), dx1f.data_ptr<scalar_t>(), anchor_ptr,
            gam.data_ptr<scalar_t>(), kbot_ptr, psf_lo.data_ptr<scalar_t>(),
            psf_hi.data_ptr<scalar_t>(), pref.data_ptr<scalar_t>(),
            dsf.data_ptr<scalar_t>(), dref.data_ptr<scalar_t>(),
            static_cast<int>(column), ncolumns, nc1, is, iu, scalar_t(grav),
            uniform, phys_in, phys_out);
      }
    });
  });
}

void hydro_ref_x1_mps(torch::Tensor const& w, torch::Tensor const& dx1f,
                      torch::Tensor const& anchor_in, torch::Tensor const& gam,
                      torch::Tensor const& kbot_in, torch::Tensor const& psf_lo,
                      torch::Tensor const& psf_hi, torch::Tensor const& pref,
                      torch::Tensor const& dsf, torch::Tensor const& dref,
                      int is, int iu, double grav, bool uniform, bool phys_in,
                      bool phys_out) {
  int nc1 = w.size(-1);
  auto rho = w[IDN];
  auto dp = grav * rho * dx1f;
  auto cum = torch::cumsum(dp, -1);

  auto anchor = anchor_in.defined()
                    ? anchor_in
                    : (w[IPR].select(-1, iu) *
                       torch::exp(-grav * 0.5 * dx1f[iu] /
                                  (w[IPR].select(-1, iu) / rho.select(-1, iu))))
                          .unsqueeze(-1);
  auto cum_iu = cum.select(-1, iu).unsqueeze(-1);
  psf_lo.copy_(anchor + cum_iu - cum + dp);
  psf_hi.copy_(psf_lo - dp);
  psf_lo.clamp_min_(std::numeric_limits<double>::min());
  psf_hi.clamp_min_(std::numeric_limits<double>::min());

  auto ratio = psf_lo / psf_hi;
  pref.copy_(torch::where((ratio - 1.).abs() < 1e-6, 0.5 * (psf_lo + psf_hi),
                          dp / torch::log(ratio)));

  auto rop = rho / w[IPR];
  auto lo_edge = rop.narrow(-1, 0, 1);
  auto hi_edge = rop.narrow(-1, nc1 - 1, 1);
  auto pad = torch::cat({lo_edge, lo_edge, rop, hi_edge, hi_edge}, -1);
  auto rs = (pad.narrow(-1, 0, nc1) + 4. * pad.narrow(-1, 1, nc1) +
             6. * pad.narrow(-1, 2, nc1) + 4. * pad.narrow(-1, 3, nc1) +
             pad.narrow(-1, 4, nc1)) /
            16.;
  auto rf = rs.clone();
  rf.narrow(-1, 1, nc1 - 1)
      .copy_(0.5 * (rs.narrow(-1, 0, nc1 - 1) + rs.narrow(-1, 1, nc1 - 1)));
  dref.copy_(pref * rs);
  dsf.copy_(psf_lo * rf);
}

}  // namespace snap

namespace at::native {

DEFINE_DISPATCH(call_hydro_ref_x1);
REGISTER_ALL_CPU_DISPATCH(call_hydro_ref_x1, &snap::hydro_ref_x1_cpu);
REGISTER_MPS_DISPATCH(call_hydro_ref_x1, &snap::hydro_ref_x1_mps);

}  // namespace at::native
