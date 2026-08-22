// C/C++
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>

// snap
#include <snap/snap.h>

#include <snap/mesh/meshblock.hpp>
#include <snap/utils/log.hpp>

#include "flux_positivity.hpp"
#include "hydro.hpp"

namespace snap {

// [SCAFFOLDING] statics for the WB x1 face-fallback meter's FINAL report.
namespace {
torch::Tensor* wb_final = nullptr;
int64_t wb_calls = 0;
}  // namespace

torch::Tensor HydroImpl::forward(double dt, torch::Tensor u,
                                 Variables const& other) {
  enum { DIM1 = 3, DIM2 = 2, DIM3 = 1 };
  bool has_solid = other.count("solid");
  auto start = std::chrono::high_resolution_clock::now();

  auto playout = pmb->get_layout();

  //// ------------ (1) Calculate Primitives ------------ ////
  auto const& w = other.at("hydro_w");

  peos->forward(u, w);
  if (options->verbose()) {
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    SINFO(Hydro) << "EOS time (s): " << elapsed.count() << "\n";
    start = std::chrono::high_resolution_clock::now();
  }

  if (has_solid) {
    pmb->pib->mark_prim_solid_(w, other.at("solid"));
  }

  // hydrostatic pressure correction
  torch::Tensor rho_grav = torch::zeros_like(w[IDN]);

  //// ------------ (2) Calculate dimension 1 flux ------------ ////
  if (u.size(DIM1) > 1) {
    // Hydrostatic wall revision is a PHYSICAL-boundary operation: it rebuilds
    // the x1 boundary in isentropic balance. On a domain decomposed in x1
    // (cubed nb1>1), a block's local il/iu at an internal seam is NOT a
    // physical boundary — the neighbor's data has already been exchanged
    // there — so applying the wall extrapolation would clobber the true
    // neighbor state. Gate each face on whether it is actually physical.
    // (Slab / single-rank: every block owns the whole x1 column, so both
    // faces are physical and behavior is unchanged — bit-identical.)
    bool grav1 = options->grav() && (options->grav()->grav1() != 0);
    bool phys_x1inner = pmb->options->is_physical_boundary(0, 0, -1);
    bool phys_x1outer = pmb->options->is_physical_boundary(0, 0, 1);

    /*if (grav1) {
      if (phys_x1inner) _revise_x1inner_ghost(w);
      if (phys_x1outer) _revise_x1outer_ghost(w);
    }*/

    // Well-balanced x1 reconstruction: decompose pressure and density into a
    // discretely hydrostatic reference + perturbation, reconstruct only the
    // perturbations, restore the reference at the faces. The restored faces
    // satisfy psf_lo(i) - psf_hi(i) = g*rho(i)*dx1f(i) identically, so a
    // resting stratification generates zero flux residual regardless of the
    // reconstruction. Engaged whenever gravity is on and the scheme is
    // defined: the state carries a pressure row, and the block owns the full
    // x1 column, OR it spans a vertical (nb1>1) decomposition -- in which case
    // _hydro_ref_x1 makes the reference continuous across the x1 process seams
    // with a distributed scan, so WB now engages under x1 decomposition too.
    bool wb_x1 =
        grav1 && w.size(0) > IPR && options->eos()->type() != "shallow-water";

    torch::Tensor wtmp;
    if (wb_x1) {
      auto [psf_lo, pref, dsf, dref] = _hydro_ref_x1(w);
      auto pressure = w[IPR].clone();
      auto density = w[IDN].clone();

      // Wall-ghost perturbation parity at physical x1 walls (S46). Stock
      // (upstream WB fix c27e7ca/#191): EVEN for both fields, p'(is-m) =
      // p'(is+m-1) and rho' likewise. Physically rho' is MIXED: its acoustic
      // part (p'/cs^2) is even like p', but its buoyancy/entropy part must be
      // ODD -- a rigid wall forces displacement xi = 0, so a buoyancy anomaly
      // cannot rest on the wall face. ExoCubed fills rho' all-ODD
      // (decomposition/apply_boundary_condition.cpp). At rest the
      // perturbations vanish identically, so every mode is bit-identical on a
      // balanced column.
      //   (default)               rho' even (stock)
      //   SNAPY_WB_GHOST_RHO_ODD  rho' odd (ExoCubed parity)
      //   SNAPY_WB_GHOST_SPLIT    rho'_g = 2 p'_m/cs^2 - rho'_m (even
      //                           acoustic + odd entropy; cs^2 = gam*pref/dref
      //                           at the mirror cell)
      static const int wb_ghost_mode = []() {
        if (std::getenv("SNAPY_WB_GHOST_RHO_ODD")) return 1;
        if (std::getenv("SNAPY_WB_GHOST_SPLIT")) return 2;
        return 0;
      }();
      static bool wb_ghost_logged = false;
      if (wb_ghost_mode && !wb_ghost_logged) {
        SINFO(Hydro) << "WB wall-ghost rho' parity mode " << wb_ghost_mode
                     << (wb_ghost_mode == 1 ? " (odd)" : " (split)") << "\n";
        wb_ghost_logged = true;
      }

      int ng = pmb->pcoord->options->nghost();
      int is = pmb->pcoord->il();
      int iu = pmb->pcoord->iu();

      // Split mode needs gamma at the mirror rows; compute it from the FULL
      // primitive state (perturbations would corrupt a composition/T-dependent
      // EOS), i.e. before the reference subtraction below.
      torch::Tensor gam_in, gam_out;
      if (wb_ghost_mode == 2) {
        if (phys_x1inner) {
          gam_in = peos->compute("W->A", {w.narrow(-1, is, ng)});
        }
        if (phys_x1outer) {
          gam_out = peos->compute("W->A", {w.narrow(-1, iu + 1 - ng, ng)});
        }
      }

      w[IPR] -= pref;
      w[IDN] -= dref;

      // p' is even in every mode.
      if (phys_x1inner) {
        w[IPR]
            .narrow(-1, is - ng, ng)
            .copy_(w[IPR].narrow(-1, is, ng).flip(-1));
      }
      if (phys_x1outer) {
        w[IPR]
            .narrow(-1, iu + 1, ng)
            .copy_(w[IPR].narrow(-1, iu + 1 - ng, ng).flip(-1));
      }

      // rho' ghost values from the mirror rows, by mode.
      auto rho_ghost = [&](int mstart, torch::Tensor const& gam) {
        auto rmir = w[IDN].narrow(-1, mstart, ng);
        if (wb_ghost_mode == 1) return -rmir;
        if (wb_ghost_mode == 2) {
          auto cs2 =
              gam * pref.narrow(-1, mstart, ng) / dref.narrow(-1, mstart, ng);
          return 2. * w[IPR].narrow(-1, mstart, ng) / cs2 - rmir;
        }
        return rmir;
      };
      if (phys_x1inner) {
        w[IDN].narrow(-1, is - ng, ng).copy_(rho_ghost(is, gam_in).flip(-1));
      }
      if (phys_x1outer) {
        w[IDN]
            .narrow(-1, iu + 1, ng)
            .copy_(rho_ghost(iu + 1 - ng, gam_out).flip(-1));
      }

      // floor=false: reconstruction-stage floors would clamp legitimately
      // negative perturbations.
      wtmp = precon1->forward(w, DIM1, /*floor=*/false);

      w[IPR].copy_(pressure);
      w[IDN].copy_(density);
      // Restore full face pressure/density; floor any nonlinear-WENO overshoot
      // that would go non-positive (the references are tiny near the top) back
      // to the reference. At rest the perturbation is ~0 so the floor never
      // fires and well-balancing is preserved.
      auto pl = wtmp[ILT][IPR] + psf_lo;
      auto pr = wtmp[IRT][IPR] + psf_lo;
      wtmp[ILT][IPR].copy_(torch::where(pl > 0., pl, psf_lo));
      wtmp[IRT][IPR].copy_(torch::where(pr > 0., pr, psf_lo));

      auto dl = wtmp[ILT][IDN] + dsf;
      auto dr = wtmp[IRT][IDN] + dsf;
      // Positivity fallback = the adjacent cell's density, not dsf: the
      // bottom-anchored isentrope overestimates density by orders of
      // magnitude on a stratified column (200x at 120 levels), and dsf at
      // the reflecting top wall -- where the mirror-ghost kink makes the
      // reconstruction overshoot every step -- inflated the wall impedance
      // ~14x. That single face is the extent-scaling S44 wall, in both the
      // explicit and implicit modes.
      auto rho_below = torch::roll(density, 1, -1);
      wtmp[ILT][IDN].copy_(torch::where(dl > 0., dl, rho_below));
      wtmp[IRT][IDN].copy_(torch::where(dr > 0., dr, density));

      // [METER] SNAPY_METER=1: count, PER X1 LEVEL, how often each WB face
      // fallback substitutes the reference/donor for the reconstructed value.
      // Diagnostic scaffolding for the h150/h180 extent question -- NOT for
      // upstream. Nothing in either code counts these today, so "the floor
      // fires at the lid every step" has never been measured either way.
      static const bool wb_meter = std::getenv("SNAPY_METER") != nullptr;
      if (wb_meter) {
        static torch::Tensor mcount;  // [4, nc1] : pl, pr, dl, dr
        static int64_t mcalls = 0;
        auto opts =
            torch::TensorOptions().dtype(torch::kInt64).device(torch::kCPU);
        if (!mcount.defined()) mcount = torch::zeros({4, pl.size(-1)}, opts);
        auto per_level = [](torch::Tensor const& bad) {
          auto f = bad.to(torch::kInt64);
          while (f.dim() > 1) f = f.sum(0);
          return f.to(torch::kCPU);
        };
        mcount[0] += per_level(pl <= 0.);
        mcount[1] += per_level(pr <= 0.);
        mcount[2] += per_level(dl <= 0.);
        mcount[3] += per_level(dr <= 0.);

        // [METER] CAUSE-OR-SYMPTOM: report each INTERIOR firing the moment it
        // happens. The aggregate table cannot tell a face that went bad in RK
        // stage 0 (a cause) from one that went bad in stage 2 (wreckage from an
        // update that had already emptied the cell). This call counter advances
        // once per RK stage, so call index -> (cycle, stage) is exact when no
        // step is redone. Ghost x1 columns are zeroed so the lid does not drown
        // the interior signal.
        {
          auto report = [&](const char* nm, torch::Tensor const& bad) {
            auto bi = bad.to(torch::kCPU).to(torch::kInt64);
            if (is > 0) bi.narrow(-1, 0, is).zero_();
            if (iu + 1 < bi.size(-1))
              bi.narrow(-1, iu + 1, bi.size(-1) - iu - 1).zero_();
            if (bi.sum().item<int64_t>() == 0) return;
            auto nz = torch::nonzero(bi);
            std::cout << "[METER] WBX1-INTERIOR call=" << (mcalls + 1) << " "
                      << nm << " n=" << nz.size(0) << " at";
            for (int64_t r = 0; r < nz.size(0) && r < 16; ++r) {
              auto row = nz[r];
              std::cout << " (j=" << row[row.size(0) - 2].item<int64_t>()
                        << ",lev=" << row[row.size(0) - 1].item<int64_t>()
                        << ")";
            }
            std::cout << "\n";
            std::cout.flush();
          };
          report("pl", pl <= 0.);
          report("pr", pr <= 0.);
          report("dl", dl <= 0.);
          report("dr", dr <= 0.);
        }
        // A final report matters more than the periodic one: the h150 death is
        // at call ~2013 and the last periodic print was at 2000, so the fatal
        // cycle's fallbacks were never reported (S49).
        static bool wb_atexit = false;
        if (!wb_atexit) {
          wb_atexit = true;
          std::atexit([]() {
            if (!wb_final || !wb_final->defined()) return;
            std::cout << "[METER] FINAL wb-x1 face fallbacks, calls="
                      << wb_calls << "\n";
            const char* nm[4] = {"pl", "pr", "dl", "dr"};
            for (int c = 0; c < 4; ++c) {
              auto row = (*wb_final)[c];
              std::cout << "[METER]  FINAL " << nm[c]
                        << " total=" << row.sum().item<int64_t>()
                        << " by level:";
              for (int i = 0; i < row.size(0); ++i) {
                auto v = row[i].item<int64_t>();
                if (v > 0) std::cout << " " << i << ":" << v;
              }
              std::cout << "\n";
            }
            std::cout.flush();
          });
        }
        wb_final = &mcount;
        wb_calls = mcalls;
        if (++mcalls % 200 == 0) {
          auto tot = mcount.sum(1);
          std::cout << "[METER] calls=" << mcalls
                    << " totals pl/pr/dl/dr = " << tot[0].item<int64_t>() << "/"
                    << tot[1].item<int64_t>() << "/" << tot[2].item<int64_t>()
                    << "/" << tot[3].item<int64_t>() << "\n";
          for (int c = 0; c < 4; ++c) {
            auto row = mcount[c];
            if (row.sum().item<int64_t>() == 0) continue;
            std::cout << "[METER]  "
                      << (c == 0   ? "pl"
                          : c == 1 ? "pr"
                          : c == 2 ? "dl"
                                   : "dr")
                      << " by level:";
            for (int i = 0; i < row.size(0); ++i) {
              auto v = row[i].item<int64_t>();
              if (v > 0) std::cout << " " << i << ":" << v;
            }
            std::cout << "\n";
          }
          std::cout.flush();
        }
      }
    } else {
      wtmp = precon1->forward(w, DIM1);
      if (grav1) {
        if (phys_x1inner) _revise_x1inner_lr(wtmp[ILT], wtmp[IRT]);
        if (phys_x1outer) _revise_x1outer_lr(wtmp[ILT], wtmp[IRT]);
      }
    }

    auto wlr1 =
        has_solid ? pmb->pib->forward(wtmp, DIM1, other.at("solid")) : wtmp;

    // Compute hydrostatic pressure correction
    if (options->grav() && (options->grav()->grav1() != 0) &&
        (options->grav()->non_hydrostatic() < 1.)) {
      int is = pmb->pcoord->il();
      int ie = pmb->pcoord->iu() + 1;
      rho_grav.slice(2, is, ie) = (wlr1[ILT][IPR].slice(2, is + 1, ie + 1) -
                                   wlr1[IRT][IPR].slice(2, is, ie)) /
                                  pmb->pcoord->dx1f.slice(0, is, ie);
    }

    // riemann solver
    if (!options->disable_flux_x1()) {
      auto face_pressure1 = options->eos()->type() == "shallow-water"
                                ? torch::Tensor()
                                : _face_pressure1;
      priemann->forward(wlr1[ILT], wlr1[IRT], DIM1, _flux1, face_pressure1);
      if (options->verbose()) {
        auto end = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> elapsed = end - start;
        SINFO(Hydro) << "Flux-x1 time (s): " << elapsed.count() << "\n";
        start = std::chrono::high_resolution_clock::now();
      }
    }

    // add sedimentation flux
    if (psed) psed->forward(w, _flux1);

    // Make internal x1 seam fluxes single-valued. The two ranks sharing an
    // internal x1 face each compute the face flux from their own
    // reconstruction. When the two are not bit-identical (e.g. a reference
    // rebuilt per block, as the well-balanced reconstruction does once it
    // spans seams), the shared face carries two different flux values --
    // a spurious source/sink of mass, momentum, and energy at the seam.
    // Exchange the seam-face slab with the x1 neighbors and set both sides
    // to the average: averaging is symmetric, so both ranks hold
    // bit-identical values and the conserved sums telescope exactly across
    // the seam, independent of reconstruction details (same principle as
    // flux correction at mesh-refinement boundaries). The scalar advective
    // flux upwinds by this mass flux afterwards and inherits the property.
    // No exchange, no behavior change at nb1 = 1.
    if (!options->disable_flux_x1() && playout &&
        playout->has_process_group() && playout->options->pz() > 1) {
      auto iloc = playout->loc_of(playout->options->rank());
      int above = playout->neighbor_rank(iloc, {0, 0, 1});
      int below = playout->neighbor_rank(iloc, {0, 0, -1});
      if (above >= 0 || below >= 0) {
        constexpr int kSeamFluxUpTag = 0x7720;  // payload travels upward
        constexpr int kSeamFluxDnTag = 0x7721;  // payload travels downward
        int il = pmb->pcoord->il();
        int iu = pmb->pcoord->iu();
        int nv = _flux1.size(0);
        bool has_fp = _face_pressure1.defined() && _face_pressure1.numel() > 0;

        // Pack the flux slab and the face pressure into ONE contiguous tensor
        // per direction: some backends restrict send/recv to a single tensor,
        // and one message per seam is cheaper anyway. torch::cat allocates
        // fresh storage, so the payload cannot alias the flux buffers while a
        // send is in flight.
        auto pack = [&](int face) {
          auto f = _flux1.select(-1, face);
          if (!has_fp) return f.clone();
          return torch::cat({f, _face_pressure1.select(-1, face).unsqueeze(0)},
                            0);
        };
        auto unpack = [&](int face, torch::Tensor const& avg) {
          _flux1.select(-1, face).copy_(avg.narrow(0, 0, nv));
          if (has_fp) _face_pressure1.select(-1, face).copy_(avg[nv]);
        };

        std::vector<CommWorkPtr> seam_sends;
        std::vector<torch::Tensor> up_mine, dn_mine;
        if (above >= 0) {
          up_mine = {pack(iu + 1)};
          seam_sends.push_back(
              playout->comm->send(up_mine, above, kSeamFluxUpTag));
        }
        if (below >= 0) {
          dn_mine = {pack(il)};
          seam_sends.push_back(
              playout->comm->send(dn_mine, below, kSeamFluxDnTag));
        }
        if (above >= 0) {
          std::vector<torch::Tensor> theirs = {torch::empty_like(up_mine[0])};
          playout->comm->recv(theirs, above, kSeamFluxDnTag)->wait();
          unpack(iu + 1, 0.5 * (up_mine[0] + theirs[0]));
        }
        if (below >= 0) {
          std::vector<torch::Tensor> theirs = {torch::empty_like(dn_mine[0])};
          playout->comm->recv(theirs, below, kSeamFluxUpTag)->wait();
          unpack(il, 0.5 * (dn_mine[0] + theirs[0]));
        }
        for (auto& sw : seam_sends) sw->wait();
      }
    }
  }

  //// ------------ (3.A) Calculate dimension 2 LR states ------------ ////
  torch::Tensor wtmp2, wtmp3;
  SyncOptions sync_opts;
  sync_opts.cross_panel_only(true).interpolate(false).type(kPrimitive);
  std::vector<CommWorkPtr> works2, works3;
  Variables send_vars2, send_vars3;

  if (u.size(DIM2) > 1) {
    wtmp2 = precon23->forward(w, DIM2);

    // sync left/right states across faces for cubed sphere layout
    if (playout->options->type() == "cubed-sphere") {
      send_vars2["hydro_wl:+"] = wtmp2[ILT];
      send_vars2["hydro_wr:-"] = wtmp2[IRT];
      pmb->begin_exchange(send_vars2, sync_opts.dim(DIM2));
    }
  }

  //// ------------ (3.B) Calculate dimension 3 LR states ------------ ////
  if (u.size(DIM3) > 1) {
    wtmp3 = precon23->forward(w, DIM3);

    // sync left/right states across faces for cubed sphere layout
    if (playout->options->type() == "cubed-sphere") {
      send_vars3["hydro_wl:+"] = wtmp3[ILT];
      send_vars3["hydro_wr:-"] = wtmp3[IRT];
      pmb->begin_exchange(send_vars3, sync_opts.dim(DIM3));
    }
  }

  if (playout->options->type() == "cubed-sphere") {
    bool exchange_dim2 = u.size(DIM2) > 1;
    bool exchange_dim3 = u.size(DIM3) > 1;
    if (exchange_dim2) {
      pmb->launch_exchange(sync_opts.dim(DIM2), works2);
    }
    if (exchange_dim3) {
      pmb->launch_exchange(sync_opts.dim(DIM3), works3);
    }
    if (exchange_dim2) {
      pmb->finalize_exchange(send_vars2, sync_opts.dim(DIM2), works2);
    }
    if (exchange_dim3) {
      pmb->finalize_exchange(send_vars3, sync_opts.dim(DIM3), works3);
    }
  }

  //// ------------ (4.A) Calculate dimension 2 flux ------------ ////
  if (u.size(DIM2) > 1) {
    auto wlr2 =
        has_solid ? pmb->pib->forward(wtmp2, DIM2, other.at("solid")) : wtmp2;
    if (!options->disable_flux_x2()) {
      priemann->forward(wlr2[ILT], wlr2[IRT], DIM2, _flux2);
      if (options->verbose()) {
        auto end = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> elapsed = end - start;
        SINFO(Hydro) << "Flux-x2 time (s): " << elapsed.count() << "\n";
        start = std::chrono::high_resolution_clock::now();
      }
    }
  }

  //// ------------ (4.B) Calculate dimension 3 flux ------------ ////
  if (u.size(DIM3) > 1) {
    auto wlr3 =
        has_solid ? pmb->pib->forward(wtmp3, DIM3, other.at("solid")) : wtmp3;
    if (!options->disable_flux_x3()) {
      priemann->forward(wlr3[ILT], wlr3[IRT], DIM3, _flux3);
      if (options->verbose()) {
        auto end = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> elapsed = end - start;
        SINFO(Hydro) << "Flux-x3 time (s): " << elapsed.count() << "\n";
        start = std::chrono::high_resolution_clock::now();
      }
    }
  }

  //// ------- (4.C) Tracer flux positivity limiter (flux_positivity.hpp) ----
  ///////
  // Scale each face's species flux by the donor cell's theta so no cell can be
  // drained below zero by transport in this stage (covers advected species AND
  // the sedimentation flux added into _flux1 above). Runs after the x1 seam
  // averaging, so seam-face fluxes are already single-valued; theta's ghost
  // layer is then filled exactly like conserved-variable ghosts (exchange at
  // internal seams, boundary functions at physical faces) so the donor factor
  // of every shared face is identical on both ranks and conservation stays
  // exact. Positivity of the full multi-stage update follows from the SSP
  // structure of the integrators (see flux_positivity.hpp).
  int ny = u.size(0) - ICY;
  if (options->eos()->limiter() && ny > 0) {
    auto uy = u.narrow(0, ICY, ny);
    auto f1 = _flux1.defined() ? _flux1.narrow(0, ICY, ny) : torch::Tensor();
    auto f2 = _flux2.defined() ? _flux2.narrow(0, ICY, ny) : torch::Tensor();
    auto f3 = _flux3.defined() ? _flux3.narrow(0, ICY, ny) : torch::Tensor();

    auto theta = flux_positivity_theta(uy, f1, f2, f3, pmb->pcoord, dt);
    // census before the ghost fill: ghosts are exactly 1 here, so this counts
    // interior (cell, species) entries only, with no double count across ranks
    _positivity_hits += (theta < 1.).sum();

    Variables tvars;
    tvars["hydro_theta"] = theta;
    SyncOptions topts;
    topts.interpolate(true).type(kScalar);
    pmb->exchange(tvars, topts);

    BoundaryFuncOptions bops;
    bops.nghost(pmb->pcoord->options->nghost());
    bops.type(kScalar);
    for (int i = 0; i < pmb->options->bfuncs().size(); ++i) {
      if (pmb->options->bfuncs()[i] == nullptr) continue;
      pmb->options->bfuncs()[i](theta, 3 - i / 2, bops);
    }

    flux_positivity_scale_(theta, f1, f2, f3, pmb->pcoord);

    if (options->verbose()) {
      auto end = std::chrono::high_resolution_clock::now();
      std::chrono::duration<double> elapsed = end - start;
      SINFO(Hydro) << "Positivity time (s): " << elapsed.count() << "\n";
      start = std::chrono::high_resolution_clock::now();
    }
  }

  //// ------------ (5) Calculate flux divergence ------------ ////
  _div.set_(pmb->pcoord->forward(w, _flux1, _flux2, _flux3, _face_pressure1));
  if (options->verbose()) {
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    SINFO(Hydro) << "Divergence time (s): " << elapsed.count() << "\n";
    start = std::chrono::high_resolution_clock::now();
  }

  //// ------------ (6) Calculate external forcing ------------ ////
  auto du = torch::zeros_like(_div);
  auto interior = pmb->part({0, 0, 0}, PartOptions().exterior(false));
  du.index(interior) = -dt * _div.index(interior);

  auto temp = peos->compute("W->T", {w});
  for (auto& f : forcings) f.forward(du, w, temp, dt);

  // apply hydrostatic correction
  if (options->grav() && (options->grav()->non_hydrostatic() < 1.)) {
    du[IVX] += dt * rho_grav * (1. - options->grav()->non_hydrostatic());
    du[IPR] +=
        dt * w[IVX] * rho_grav * (1. - options->grav()->non_hydrostatic());
  }

  if (options->verbose()) {
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    SINFO(Hydro) << "Forcing time (s): " << elapsed.count() << "\n";
    start = std::chrono::high_resolution_clock::now();
  }

  //// ------------ (7) Perform implicit correction ------------ ////
  if (picorr) {
    // S46 stage-dt A/B: athena assembles the vertical-implicit correction with
    // the STAGE-weighted dt (beta*dt; implicit_hydro_tasks.cpp:253), snapy with
    // the FULL dt at every stage.  Equivalent for linear operators,
    // inequivalent for the dt-nonlinear correction -- possibly the codes'
    // wall-mode threshold difference.  Env SNAPY_VIC_STAGE_DT enables athena
    // parity (SSP-RK3 betas; guarded to 3-stage integrators).
    double dt_corr = dt;
    static const bool vic_stage_dt =
        std::getenv("SNAPY_VIC_STAGE_DT") != nullptr;
    if (vic_stage_dt && vic_stage >= 0 && vic_stage < 3 &&
        pmb->pintg->stages.size() == 3) {
      static const double beta[3] = {1.0, 0.25, 2.0 / 3.0};
      dt_corr *= beta[vic_stage];
    }
    _apply_implicit_correction(du, w, dt_corr, other);

    if (options->verbose()) {
      auto end = std::chrono::high_resolution_clock::now();
      std::chrono::duration<double> elapsed = end - start;
      SINFO(Hydro) << "Implicit time (s): " << elapsed.count() << "\n";
      start = std::chrono::high_resolution_clock::now();
    }
  }

  return du;
}

}  // namespace snap
