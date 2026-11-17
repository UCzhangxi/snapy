#pragma once
// Lane X skeleton: the pyharp interface change, declarations only, in no build.
// Now: pyharp/src/integrator/integrator.hpp:95-96 (allocating form only).
#include <torch/torch.h>

#include <vector>

namespace harp {

//! IMEX-ARK pair (X section 3, proposed): host doubles fixed for the run
struct StageTableau {
  std::vector<std::vector<double>> aex, aim;  // s x s; aex strictly lower
  std::vector<double> bex, bim, c;            // aim lower, diagonal gamma_i
  int order;                                // design order p (order gate)
};

class IntegratorImpl {
 public:
  //! Stage combination w0*u0 + w1*u1 + w2*u2 with the weights of `stage`.
  //!
  //! out empty: returns a new tensor, exactly as at the pin.
  //! out given: writes into out and returns it. Rules:
  //!   - out may alias u1; it must not alias u0 or u2;
  //!   - u0, u1, u2 and out share dtype and device, else it throws;
  //!   - evaluation: out = u1 (copy unless aliased); out *= w1; out += w0*u0;
  //!     out += w2*u2. Separate kernels (no fused multiply-add) and commuting
  //!     additions give the pin's ((w0*u0) + (w1*u1)) + (w2*u2) bit for bit.
  torch::Tensor forward(int stage, torch::Tensor u0, torch::Tensor u1,
                        torch::Tensor u2, torch::Tensor out = {});
};

}  // namespace harp
