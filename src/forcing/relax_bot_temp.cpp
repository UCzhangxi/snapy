// C/C++
#include <atomic>
#include <cstdlib>
#include <iostream>

// yaml
#include <yaml-cpp/yaml.h>

// snap
#include <snap/snap.h>

#include <snap/hydro/hydro.hpp>
#include <snap/mesh/meshblock.hpp>

#include "forcing.hpp"

namespace snap {

RelaxBotTempOptions RelaxBotTempOptionsImpl::from_yaml(
    YAML::Node const& forcing) {
  if (!forcing["relax-bot-temp"]) return nullptr;

  auto node = forcing["relax-bot-temp"];
  auto op = RelaxBotTempOptionsImpl::create();

  op->tau() = node["tau"].as<double>(0.0);

  TORCH_CHECK(node["btemp"],
              "RelaxBotTempOptions: btemp is required (no default).");
  op->btemp() = node["btemp"].as<double>();

  TORCH_CHECK(op->tau() > 0.,
              "RelaxBotTempOptions: tau must be greater than zero.");
  TORCH_CHECK(op->btemp() > 0.,
              "RelaxBotTempOptions: btemp must be greater than zero.");

  return op;
}

RelaxBotTempImpl::RelaxBotTempImpl(RelaxBotTempOptions const& options_,
                                   torch::nn::Module* p)
    : options(options_) {
  phydro = dynamic_cast<HydroImpl const*>(p);
  reset();
}

void RelaxBotTempImpl::reset() {
  TORCH_CHECK(phydro, "[RelaxBotTemp] Parent Hydro is null");
}

torch::Tensor RelaxBotTempImpl::forward(torch::Tensor du, torch::Tensor w,
                                        torch::Tensor temp, double dt) {
  // Applies at the physical lower x1 boundary only: under an x1-decomposed
  // layout (nb1 > 1) a rank whose lower face is an internal block interface
  // must not force there.
  if (!phydro->pmb->options->is_physical_boundary(0, 0, -1)) return du;

  auto bottom = phydro->pmb->part(
      {0, 0, -1}, PartOptions().exterior(false).depth(1).ndim(3));
  auto rho = w[IDN].index(bottom);
  auto temp_bot = temp.index(bottom);
  auto cv = phydro->peos->specific_heat_cv(w, temp).index(bottom);

  // [S56] The ISSI protocol prescribes a temperature at a PRESSURE LEVEL, and
  // in a finite-volume code a pressure level is a FACE. The domain's lower face
  // already carries the prescribed pressure -- verified: with Ps = 1e7 Pa at
  // the face and H = Rd*T/g = 441 km, the first cell CENTRE should read
  // 100*exp(-dz/2H) = 96.66 bar, and the run measures 96.69 bar.
  //
  // But this forcing has always driven the first interior cell CENTRE, which
  // sits half a cell ABOVE that face. Measured consequence at btemp = 2900 K:
  // the centre relaxes to 2898.8 K while the face extrapolates to 2932.9 K
  // (half-cell) -- i.e. the boundary the protocol specifies is left ~33 K hot,
  // which is 4.7 % in sigma*T^4 at the level where the interior flux enters.
  //
  // Gated on SNAPY_RELAX_BOT_FACE: when set, control the FACE temperature
  //   T_face = 1.5*T0 - 0.5*T1   (linear extrapolation over the half cell)
  // instead of T0. Only cell 0 is nudged, and d(T_face)/d(T0) = 1.5, so the
  // gain is divided by 1.5 to keep the same effective relaxation time on the
  // face.
  //
  // A relaxation is kept rather than a hard Dirichlet ghost condition on
  // purpose: this is a rigid, reflecting, no-flux wall, and pinning T there
  // would imply a conductive energy flux the equations do not carry. Both codes
  // already implement the ISSI condition as a finite-tau relaxation; only its
  // LOCATION was wrong. ⚠ ExoCubed has the identical mislocation
  // (hjupiter.cpp:128-133) -- this is not a cross-code parity term, it is a
  // shared departure from the protocol.
  static const bool face_mode = std::getenv("SNAPY_RELAX_BOT_FACE") != nullptr;
  auto target = temp_bot;
  double gain = 1.0;
  if (face_mode) {
    auto bottom2 = phydro->pmb->part(
        {0, 0, -1}, PartOptions().exterior(false).depth(2).ndim(3));
    auto t2 = temp.index(bottom2);
    // PartOptions::depth is capped at nghost (meshblock.cpp:295) even when
    // exterior(false) selects INTERIOR cells, so nghost = 1 would silently hand
    // back a width-1 slice and the narrow below would throw a bare torch index
    // error with no hint of the cause. nghost defaults to 1; every current deck
    // sets 3. Shape query only -- no device sync.
    TORCH_CHECK(
        t2.size(-1) >= 2,
        "[RelaxBotTemp] SNAPY_RELAX_BOT_FACE needs two interior cells at "
        "the lower boundary; got ",
        t2.size(-1), ". Set nghost >= 2.");
    auto T0 = t2.narrow(-1, 0, 1);
    auto T1 = t2.narrow(-1, 1, 1);
    target = 1.5 * T0 - 0.5 * T1;
    gain = 1.0 / 1.5;
    static std::atomic<bool> announced{false};
    if (!announced.exchange(true)) {
      // Assert the index convention rather than asserting it in a comment:
      // offset 0 of the depth-2 slice must be the cell ADJACENT to the lower
      // face, i.e. the deeper one. On this gravity-down grid that is the hotter
      // one. Checked once (it costs a device sync), so a flipped grid
      // convention fails loudly here instead of silently extrapolating the
      // wrong way.
      double t0 = T0.mean().item<double>(), t1 = T1.mean().item<double>();
      // `>=`, not `>`: an ISOTHERMAL column is legal and gives t0 == t1
      // exactly, where the extrapolation 1.5*T0 - 0.5*T1 == T0 is correct.
      // Only a strictly COLDER deeper cell indicates a flipped convention.
      // A strict `>` threw on the upstream forcing.relax_bottom_temperature
      // unit test, whose fixture is isothermal (found by running ctest, S72).
      TORCH_CHECK(t0 >= t1,
                  "[RelaxBotTemp] index convention violated: offset 0 of the "
                  "lower-boundary slice (T=",
                  t0,
                  ") should be DEEPER, and so "
                  "hotter, than offset 1 (T=",
                  t1,
                  "). The face extrapolation "
                  "would run the wrong way.");
      std::cout << "[S56-RELAX-FACE] ON: btemp=" << options->btemp()
                << " K; first call T0=" << t0 << " T1=" << t1
                << " -> T_face=" << target.mean().item<double>() << " K"
                << std::endl;
    }
  }
  du[IPR].index(bottom) +=
      gain * dt / options->tau() * rho * cv * (options->btemp() - target);
  return du;
}

}  // namespace snap
