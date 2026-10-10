// #289 (RED): the rest face density of the default x1 well-balanced
// reference next to a closed wall.
//
// At linear order the x1 reference enters the dynamics only through the rest
// face density of the mass flux (hydro_forward.cpp, step 2):
//
//   rho_f = WENO5[rho - dref]_f (even-parity wall ghosts) + dsf_f .
//
// This test builds that face density from the solver's own reference
// (HydroImpl::_hydro_ref_x1) and its own x1 reconstruction (precon1), on exact
// cell averages of a hydrostatic column with closed (reflecting) walls on a
// uniform grid, and compares it with the exact face value rho(z_f).
//
//  - isothermal column: rho/p is constant, so the kernel's density reference
//    is exact up to its sixth-order cell pressure (control: the pipeline below
//    is right, and the walls are fine when rho/p has no gradient);
//  - adiabatic polytrope: the two faces next to each wall must converge at
//    second order or better. With the kernel's clamped binomial smoothing of
//    rho/p (hydro_ref_x1_impl.h, rop_smooth, edge-replicated past a clamped
//    wall) they converge at first order (about 1e-4 relative at nz = 64)
//    while the interior faces are second order. The x1 WENO5 is nonlinear
//    (JS weights), and the two-cell O(dz) step of rho - dref next to the wall
//    moves its weights there, so the observed wall order drifts between 1.1
//    and 1.6 over nz 16..128 instead of sitting at 1.
//
// No switch is read or set; the assertions hold for any reference that is
// second order up to the wall.

// C/C++
#include <cmath>
#include <cstdio>
#include <fstream>
#include <string>
#include <tuple>
#include <vector>

// external
#include <gtest/gtest.h>

// torch
#include <torch/torch.h>

// snap
#include <snap/snap.h>

#include <snap/forcing/forcing.hpp>
#include <snap/hydro/hydro.hpp>
#include <snap/mesh/meshblock.hpp>

using namespace snap;

namespace {

// access to the solver's reference without changing its interface
struct RefProbe : HydroImpl {
  using HydroImpl::_hydro_ref_x1;
};

constexpr double kT0 = 300.;
constexpr double kP0 = 1.e5;

std::string write_yaml(int nx1) {
  std::string name = "test_wb_wall_face_density_" + std::to_string(nx1) + ".yaml";
  std::ofstream f(name);
  f << "reference-state:\n  Tref: 300.\n  Pref: 1.e5\n\n"
    << "species:\n  - name: dry\n    composition: {O: 0.42, N: 1.56, Ar: 0.01}\n"
    << "    cv_R: 2.5\n\n"
    << "geometry:\n  type: cartesian\n"
    << "  bounds: {x1min: 0., x1max: 1., x2min: 0., x2max: 1., x3min: 0., "
       "x3max: 1.}\n"
    << "  cells: {nx1: " << nx1 << ", nx2: 1, nx3: 1, nghost: 3}\n\n"
    << "dynamics:\n  equation-of-state:\n    type: ideal-gas\n"
    << "  reconstruct:\n"
    << "    vertical: {type: weno5, scale: false, shock: false}\n"
    << "    horizontal: {type: weno5, scale: false, shock: false}\n\n"
    << "boundary-condition:\n  external:\n    x1-inner: reflecting\n"
    << "    x1-outer: reflecting\n";
  return name;
}

enum class Column { isothermal, polytrope };

struct FaceErrors {
  double bottom = 0., top = 0., interior = 0.;  // max relative error
};

// the gas constant of the block's EOS: T = p / (rho R)
double gas_constant(std::shared_ptr<MeshBlockImpl> const& block) {
  auto w = torch::ones({block->phydro->peos->nvar(), 1, 1, 1},
                       torch::kFloat64);
  return 1. / block->phydro->peos->compute("W->T", {w}).item<double>();
}

FaceErrors face_errors(Column column, int nx1) {
  auto yaml = write_yaml(nx1);
  // the gas constant first (a block without gravity), then the column's block
  // with gravity set before it is built
  double rgas;
  {
    auto probe = std::make_shared<MeshBlockImpl>(
        MeshBlockOptionsImpl::from_yaml(yaml));
    probe->to(torch::kCPU, torch::kFloat64);
    rgas = gas_constant(probe);
  }
  double cp = 3.5 * rgas;  // cv_R = 2.5
  // isothermal: 3 scale heights; polytrope: adiabatic, T_top = (1 - 2 R/cp) T0
  double g = (column == Column::isothermal ? 3. : 2.) * rgas * kT0;
  auto options = MeshBlockOptionsImpl::from_yaml(yaml);
  auto gravity = ConstGravityOptionsImpl::create();
  gravity->grav1(-g);
  options->hydro()->grav() = gravity;
  options->hydro()->icorr() = nullptr;
  auto block = std::make_shared<MeshBlockImpl>(options);
  block->to(torch::kCPU, torch::kFloat64);

  auto T = [&](double z) {
    return column == Column::isothermal ? kT0 : kT0 * (1. - g * z / (cp * kT0));
  };
  auto p = [&](double z) {
    return column == Column::isothermal
               ? kP0 * std::exp(-g * z / (rgas * kT0))
               : kP0 * std::pow(T(z) / kT0, cp / rgas);
  };
  auto rho = [&](double z) { return p(z) / (rgas * T(z)); };

  auto coord = block->pcoord;
  int nc1 = coord->options->nc1();
  int il = coord->il(), iu = coord->iu();
  auto x1f = coord->x1f.to(torch::kCPU).contiguous();
  auto xf = x1f.accessor<double, 1>();

  // exact cell averages (4-point Gauss-Legendre per cell), ghosts mirrored as
  // a reflecting wall fills them
  const double gx[4] = {-0.8611363115940526, -0.3399810435848563,
                        0.3399810435848563, 0.8611363115940526};
  const double gw[4] = {0.3478548451374538, 0.6521451548625461,
                        0.6521451548625461, 0.3478548451374538};
  std::vector<double> rbar(nc1), pbar(nc1);
  for (int i = il; i <= iu; ++i) {
    double c = 0.5 * (xf[i] + xf[i + 1]), h = 0.5 * (xf[i + 1] - xf[i]);
    double sr = 0., sp = 0.;
    for (int q = 0; q < 4; ++q) {
      sr += 0.5 * gw[q] * rho(c + gx[q] * h);
      sp += 0.5 * gw[q] * p(c + gx[q] * h);
    }
    rbar[i] = sr;
    pbar[i] = sp;
  }
  int ng = il;
  for (int m = 1; m <= ng; ++m) {
    rbar[il - m] = rbar[il + m - 1];
    pbar[il - m] = pbar[il + m - 1];
    rbar[iu + m] = rbar[iu - m + 1];
    pbar[iu + m] = pbar[iu - m + 1];
  }
  auto w = torch::zeros({block->phydro->peos->nvar(), 1, 1, nc1},
                        torch::kFloat64);
  for (int i = 0; i < nc1; ++i) {
    w[IDN][0][0][i] = rbar[i];
    w[IPR][0][0][i] = pbar[i];
  }

  // the solver's reference
  auto fn = &RefProbe::_hydro_ref_x1;
  auto [psf_lo, pref, dsf, dref] = (block->phydro.get()->*fn)(w);

  // the face density of hydro_forward.cpp step 2: subtract the reference,
  // even-parity perturbation ghosts at the two closed walls, WENO5, restore
  auto wx1 = w.clone();
  wx1[IPR] -= pref;
  wx1[IDN] -= dref;
  for (int c : {(int)IPR, (int)IDN}) {
    wx1[c].narrow(-1, il - ng, ng).copy_(wx1[c].narrow(-1, il, ng).flip(-1));
    wx1[c].narrow(-1, iu + 1, ng)
        .copy_(wx1[c].narrow(-1, iu + 1 - ng, ng).flip(-1));
  }
  constexpr int DIM1 = 3;
  auto wlr = block->phydro->precon1->forward(wx1, DIM1, /*floor=*/false);
  auto rl = (wlr[ILT][IDN] + dsf).flatten().contiguous();
  auto rr = (wlr[IRT][IDN] + dsf).flatten().contiguous();
  auto al = rl.accessor<double, 1>(), ar = rr.accessor<double, 1>();

  // face f is the lower face of cell f; the wall faces are il and iu + 1
  auto err = [&](int f) {
    double ex = rho(xf[f]);
    return std::max(std::abs(al[f] - ex), std::abs(ar[f] - ex)) / ex;
  };
  FaceErrors e;
  e.bottom = std::max(err(il + 1), err(il + 2));
  e.top = std::max(err(iu), err(iu - 1));
  for (int f = il + 5; f <= iu - 4; ++f) e.interior = std::max(e.interior, err(f));
  return e;
}

struct Table {
  std::vector<int> nz;
  std::vector<FaceErrors> e;
};

Table run(Column column, char const* label) {
  Table t;
  t.nz = {16, 32, 64, 128};
  std::printf("\n%s column: max relative error |rho_f - rho(z_f)| / rho(z_f)\n",
              label);
  std::printf("  (wall: the two faces next to each closed wall, both states)\n");
  std::printf("   nz    bottom wall     top wall       interior   | order: "
              "bottom   top  interior\n");
  for (size_t k = 0; k < t.nz.size(); ++k) {
    t.e.push_back(face_errors(column, t.nz[k]));
    auto const& e = t.e.back();
    std::printf("  %4d   %.3e     %.3e     %.3e", t.nz[k], e.bottom, e.top,
                e.interior);
    if (k > 0) {
      auto const& o = t.e[k - 1];
      std::printf("   |        %5.2f  %5.2f  %5.2f",
                  std::log2(o.bottom / e.bottom), std::log2(o.top / e.top),
                  std::log2(o.interior / e.interior));
    }
    std::printf("\n");
  }
  return t;
}

// the observed order of the max error over the last two doublings
// (nz 32 -> 64 -> 128) must be >= 1.75 (second order with margin for the
// pre-asymptotic range); a pair already at the round-off floor passes
void expect_second_order(Table const& t) {
  constexpr double kMinOrder = 1.75;
  constexpr double kFloor = 1.e-11;
  auto check = [&](double a, double b, char const* where, int n0, int n1) {
    if (a < kFloor && b < kFloor) return;
    EXPECT_GE(std::log2(a / b), kMinOrder)
        << where << ", nz " << n0 << " -> " << n1 << " (" << a << " -> " << b
        << ")";
  };
  for (size_t k = 2; k < t.nz.size(); ++k) {
    auto const& o = t.e[k - 1];
    auto const& e = t.e[k];
    check(o.interior, e.interior, "interior faces", t.nz[k - 1], t.nz[k]);
    check(o.bottom, e.bottom, "the two faces next to the bottom wall",
          t.nz[k - 1], t.nz[k]);
    check(o.top, e.top, "the two faces next to the top wall", t.nz[k - 1],
          t.nz[k]);
  }
}

}  // namespace

// control: rho/p constant, so the kernel's density reference is exact up to
// its sixth-order cell pressure; any reference passes
TEST(WbWallFaceDensity, isothermal_column_is_second_order) {
  expect_second_order(run(Column::isothermal, "isothermal"));
}

// RED with the kernel's reference: the two faces next to each wall converge
// at first order
TEST(WbWallFaceDensity, polytrope_wall_faces_are_second_order) {
  expect_second_order(run(Column::polytrope, "adiabatic polytrope"));
}
