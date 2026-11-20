// yaml
#include <yaml-cpp/yaml.h>

// snap
#include <snap/snap.h>

#include <snap/input/check_keys.hpp>

#include "forcing.hpp"

namespace snap {
ConstGravityOptions ConstGravityOptionsImpl::from_yaml(
    YAML::Node const& forcing) {
  if (!forcing["const-gravity"]) return nullptr;

  auto node = forcing["const-gravity"];
  check_keys(node, "forcing/const-gravity",
             {"grav1", "grav2", "grav3", "non-hydrostatic", "gravity-work",
              "gravity-work-fixer"});
  auto op = ConstGravityOptionsImpl::create();

  op->grav1() = node["grav1"].as<double>(0.);
  op->grav2() = node["grav2"].as<double>(0.);
  op->grav3() = node["grav3"].as<double>(0.);
  op->non_hydrostatic() = node["non-hydrostatic"].as<double>(1.);
  TORCH_CHECK(op->non_hydrostatic() >= 0. && op->non_hydrostatic() <= 1.);

  // V3 I-7 (rulings (a), (b)): face is the one gravity-work form;
  // the cell form and its global fixer are removed
  op->gravity_work() = node["gravity-work"].as<std::string>("face");
  TORCH_CHECK(op->gravity_work() == "face",
              "forcing/const-gravity/gravity-work: '", op->gravity_work(),
              "' is not supported: the cell form and its global fixer were "
              "removed (V3 I-7); use gravity-work: face");
  // gravity-work-fixer: false is a deprecated no-op; true is refused
  if (node["gravity-work-fixer"]) {
    TORCH_CHECK(!node["gravity-work-fixer"].as<bool>(),
                "forcing/const-gravity/gravity-work-fixer: true is not "
                "supported: the global gravity-work fixer was removed (V3 "
                "I-7) with gravity-work: cell; use gravity-work: face");
    TORCH_WARN_ONCE(
        "forcing/const-gravity/gravity-work-fixer is deprecated and ignored "
        "(the fixer was removed in V3 I-7); remove the key");
  }

  return op;
}

torch::Tensor ConstGravityImpl::forward(torch::Tensor du, torch::Tensor w,
                                        torch::Tensor temp, double dt) {
  return forward_split(du, w, dt, w[IDN]);
}

torch::Tensor ConstGravityImpl::forward_split(torch::Tensor du, torch::Tensor w,
                                              double dt, torch::Tensor rho1) {
  if (options->grav1() != 0.) {
    du[IVX] += dt * rho1 * options->grav1() * options->non_hydrostatic();
    du[IPR] +=
        dt * w[IDN] * w[IVX] * options->grav1() * options->non_hydrostatic();
  }

  if (options->grav2() != 0.) {
    du[IVY] += dt * w[IDN] * options->grav2();
    du[IPR] += dt * w[IDN] * w[IVY] * options->grav2();
  }

  if (options->grav3() != 0.) {
    du[IVZ] += dt * w[IDN] * options->grav3();
    du[IPR] += dt * w[IDN] * w[IVZ] * options->grav3();
  }

  return du;
}
}  // namespace snap
