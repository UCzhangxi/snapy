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

//! Face states from one interpolation over a 1-D field.
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

// The Suresh-Huynh constraint (2.30) is satisfied a priori by smooth data, so
// mp5 must return the WENO5 value unaltered there. Reading the stencil in the
// wrong orientation instead collapses mp5 to donor cell, which still reports a
// perfectly bounded tracer -- a boundedness test cannot catch it, this can.
TEST_P(DeviceTest, mp5_is_weno5_on_linear_data) {
  MP5Interp mp5;
  Weno5Interp weno5;
  mp5->to(device, dtype);
  weno5->to(device, dtype);

  auto w = torch::arange(32, torch::device(device).dtype(dtype));
  auto m = faces(mp5, w);
  auto n = faces(weno5, w);

  EXPECT_TRUE(torch::equal(m.first, n.first));
  EXPECT_TRUE(torch::equal(m.second, n.second));
}

TEST_P(DeviceTest, mp5_is_weno5_on_smooth_data) {
  MP5Interp mp5;
  Weno5Interp weno5;
  mp5->to(device, dtype);
  weno5->to(device, dtype);

  auto x = torch::arange(64, torch::device(device).dtype(dtype));
  auto w = 2. + torch::sin(2. * M_PI * x / 64.);
  auto m = faces(mp5, w);
  auto n = faces(weno5, w);

  EXPECT_TRUE(torch::equal(m.first, n.first));
  EXPECT_TRUE(torch::equal(m.second, n.second));
}

// A tracer face state outside the data range is what breaks the maximum
// principle downstream, however small.
TEST_P(DeviceTest, mp5_face_states_stay_in_range) {
  MP5Interp mp5;
  mp5->to(device, dtype);

  auto w = torch::zeros({24}, torch::device(device).dtype(dtype));
  w.narrow(0, 8, 8).fill_(1.);
  w[7] = 0.35;
  w[16] = 0.65;

  auto f = faces(mp5, w);
  auto lmax = f.first.max().template item<double>();
  auto rmax = f.second.max().template item<double>();
  auto lmin = f.first.min().template item<double>();
  auto rmin = f.second.min().template item<double>();

  EXPECT_LE(lmax, 1.);
  EXPECT_LE(rmax, 1.);
  EXPECT_GE(lmin, 0.);
  EXPECT_GE(rmin, 0.);
}

int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);

  return RUN_ALL_TESTS();
}
