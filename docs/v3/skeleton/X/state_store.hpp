#pragma once
// Lane X skeleton: declarations only, in no build.
// Fixed state storage allocated once at reset(); the RK combine writes into it
// (pyharp out=), replacing set_/set_data at src/mesh/meshblock.cpp:901-902, 921-922, 44-56.
#include <map>
#include <string>
#include <vector>
#include <torch/torch.h>

namespace snap {

class PrecisionPolicy;

class StateStore {
 public:
  StateStore(PrecisionPolicy const& policy, int64_t nvar_hydro,
             int64_t nvar_scalar, int64_t nc3, int64_t nc2, int64_t nc1,
             torch::Device device);

  torch::Tensor& hydro_u();
  torch::Tensor& scalar_s();
  torch::Tensor& scalar_r();  // scalar_s / dry density, divided with out= (now 923, 1199, 1484; restart 1828)
  torch::Tensor& u0();
  torch::Tensor& s0();
  //! allocates hydro_u, scalar_s, scalar_r, u0, s0 and every declared scratch in the
  //! policy's storage dtype; bumps generation()
  void reset();
  //! owners at set-up, before reset(): the clones now at meshblock.cpp:857, 859, 869, 1517
  void declare_scratch(std::string const& name, std::vector<int64_t> const& sizes,
                       torch::Dtype dtype);
  torch::Tensor& scratch(std::string const& name);  // look-up only, filled with copy_
  //! R's FluxRegister::reset() and kintera allocate their tensors; registered here
  //! (again when kintera::alloc_epoch(m) changes); a new address bumps generation()
  void register_storage(std::string const& name, torch::Tensor const& t,
                        int64_t alloc_epoch = -1);
  torch::Tensor const& storage(std::string const& name) const;  // read access (R, save list)

  void backup();   // stage 0: u0 = hydro_u, s0 = scalar_s (copy_)
  void restore();  // rejected step: hydro_u = u0, scalar_s = s0 (copy_)
  //! copy_ in, addresses kept: initialize the given scalar_r; restart 1743's copy, else (1828) divide out=
  void assign(torch::Tensor const& hydro_u, torch::Tensor const& scalar_s, torch::Tensor const& scalar_r = {});
  int generation() const;  // bumped by reset(), to() and restart; in every GraphKey

 private:
  torch::Tensor hydro_u_, scalar_s_, scalar_r_, u0_, s0_;
  std::map<std::string, torch::Tensor> scratch_;  // allocated at reset()
  int generation_;
};

}  // namespace snap
