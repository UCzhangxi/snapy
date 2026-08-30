// external
#include <gtest/gtest.h>

// torch
#include <torch/torch.h>

// snap
#include <snap/recon/interpolation.hpp>

// tests
#include "device_testing.hpp"

using namespace snap;

namespace {

template <typename T>
std::pair<torch::Tensor, torch::Tensor> faces(T interp, torch::Tensor w) {
  auto out = torch::empty({w.size(0) - interp->stencils() + 1}, w.options());
  auto l = torch::empty_like(out);
  auto r = torch::empty_like(out);
  interp->left(w, 0, l);
  interp->right(w, 0, r);
  return {l, r};
}

}  // namespace

// On linear data the gradient ratio is 1, so phi is 1 and the blend reduces to
// its 5th-order term -- which is what Center5Interp computes. Tying the two
// together pins the stencil ORIENTATION against an existing module rather than
// against a hand-derived expectation, because the wrong orientation is also
// exact, one cell away.
TEST_P(DeviceTest, mono5_matches_cp5_on_linear_data) {
  Mono5Interp mono5;
  Center5Interp cp5;
  mono5->to(device, dtype);
  cp5->to(device, dtype);

  auto w = torch::arange(32, torch::device(device).dtype(dtype));
  auto m = faces(mono5, w);
  auto c = faces(cp5, w);

  EXPECT_TRUE(torch::allclose(m.first, c.first, 1e-5, 1e-5));
  EXPECT_TRUE(torch::allclose(m.second, c.second, 1e-5, 1e-5));
}

// The same fact stated in absolute terms: output i has cell i+2 as its pivot,
// so left() is that cell's west face and right() its east face.
TEST_P(DeviceTest, mono5_is_exact_on_linear_data) {
  Mono5Interp mono5;
  mono5->to(device, dtype);

  auto w = torch::arange(32, torch::device(device).dtype(dtype));
  auto f = faces(mono5, w);
  auto i = torch::arange(32 - 4, torch::device(device).dtype(dtype));

  EXPECT_TRUE(torch::allclose(f.first, i + 1.5, 1e-5, 1e-5));
  EXPECT_TRUE(torch::allclose(f.second, i + 2.5, 1e-5, 1e-5));
}

// The point of the scheme: at a local extremum consecutive slopes reverse, phi
// goes negative, and the blend collapses to the cell mean.
TEST_P(DeviceTest, mono5_collapses_to_the_cell_mean_at_an_extremum) {
  Mono5Interp mono5;
  mono5->to(device, dtype);

  auto w = torch::zeros({9}, torch::device(device).dtype(dtype));
  w[2] = 0.4;
  w[3] = 0.8;
  w[4] = 1.0;
  w[5] = 0.8;
  w[6] = 0.4;

  auto f = faces(mono5, w);
  EXPECT_NEAR(f.first[2].template item<double>(), 1.0, 1e-6);
  EXPECT_NEAR(f.second[2].template item<double>(), 1.0, 1e-6);
}

// A tracer face state outside the data range breaks the maximum principle
// downstream. This profile is dense in local extrema, the population that
// defeats a scheme guaranteeing monotonicity only on monotone data.
TEST_P(DeviceTest, mono5_face_states_stay_in_range_on_an_oscillatory_field) {
  Mono5Interp mono5;
  mono5->to(device, dtype);

  auto x = torch::arange(64, torch::device(device).dtype(dtype));
  auto w = 0.5 + 0.5 * torch::sin(2. * M_PI * x / 8.);

  auto f = faces(mono5, w);
  auto lo = std::min(f.first.min().template item<double>(),
                     f.second.min().template item<double>());
  auto hi = std::max(f.first.max().template item<double>(),
                     f.second.max().template item<double>());
  EXPECT_GE(lo, -1e-6);
  EXPECT_LE(hi, 1. + 1e-6);
}

// A denominator that cancels kEps exactly makes r infinite. The reference's
// np.where sends the resulting NaN to the floor; clamp_min would let it through
// into the field.
TEST_P(DeviceTest, mono5_is_finite_when_the_gradient_ratio_diverges) {
  Mono5Interp mono5;
  mono5->to(device, dtype);

  auto w = torch::ones({9}, torch::device(device).dtype(dtype));
  w[3] = 1.5;
  w[4] = 1.0;
  w[5] = 1.0 - 1.0e-10;  // v3 - v2 + kEps == 0

  auto f = faces(mono5, w);
  EXPECT_TRUE(torch::isfinite(f.first).all().template item<bool>());
  EXPECT_TRUE(torch::isfinite(f.second).all().template item<bool>());
}

int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);

  return RUN_ALL_TESTS();
}
