#pragma once
// Lane X skeleton: declarations only, in no build.
// Fixed state storage: buffers allocated once at reset(); the RK combine writes
// into them (pyharp forward(..., out)), replacing set_ at
// src/mesh/meshblock.cpp:901-902 and src/mesh/meshblock.cpp:921-922.
#include <string>
#include <torch/torch.h>

namespace snap {

class PrecisionPolicy;

class StateStore {
 public:
  //! allocates hydro_u, scalar_s, u0, s0 in the policy's storage dtype
  StateStore(PrecisionPolicy const& policy, int64_t nvar_hydro,
             int64_t nvar_scalar, int64_t nc3, int64_t nc2, int64_t nc1,
             torch::Device device);

  torch::Tensor& hydro_u();
  torch::Tensor& scalar_s();
  torch::Tensor& u0();
  torch::Tensor& s0();
  //! fixed copy of hydro_u for the retry test (now the clone at
  //! src/mesh/meshblock.cpp:1517), filled with copy_
  torch::Tensor& scratch();
  //! R's FluxRegister::reset() allocates its tensors (R.rst 7); registered
  //! here for address stability: a new allocation bumps generation()
  void register_storage(std::string const& name, torch::Tensor const& t);

  //! stage 0: u0 = hydro_u, s0 = scalar_s (copy_, no allocation)
  void backup();
  //! rejected step: hydro_u = u0, scalar_s = s0 (copy_, no allocation)
  void restore();

  //! copy external state in without changing addresses (restart, user edits)
  void assign(torch::Tensor const& hydro_u, torch::Tensor const& scalar_s);

  //! bumped by reset(), to() and restart; part of every GraphKey
  int generation() const;

 private:
  torch::Tensor hydro_u_, scalar_s_, u0_, s0_, scratch_;
  int generation_;
};

}  // namespace snap
