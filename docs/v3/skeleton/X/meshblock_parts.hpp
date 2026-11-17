#pragma once
// Lane X skeleton: declarations only, in no build.
// src/mesh/meshblock.cpp split into six parts with one owner each.
// The MeshBlock API seen by Python and tests does not change.
#include <functional>
#include <string>
#include <vector>
#include <torch/torch.h>

namespace snap {

class MeshBlockImpl;

//! now src/mesh/meshblock.cpp:86-574: options, modules, StateStore, initial state
struct BlockInit;       // owner X

//! now src/mesh/meshblock.cpp:698-1007: registers this block's ops into the
//! StageSchedule; no host timers, no global reductions
struct BlockAdvance;    // owner X; ops from R, S, EF, K

//! now src/mesh/meshblock.cpp:644-685, 1111-1205, 1846-1918: exchange phases
//! (pack, host, unpack) and boundary functions
struct BlockExchange;   // owner S

//! now src/mesh/meshblock.cpp:1447-1601: device retry flags, restore, resets
struct BlockRedo;       // owner X; flags from EF, K, R

//! now src/mesh/meshblock.cpp:1603-1833
struct BlockRestart;    // owner O (question to O)

//! now src/mesh/meshblock.cpp:1207-1415: outputs and cycle diagnostics
struct BlockOutput;     // owner O (question to O)

//! state that must be reset at stage 0 and on every rollback, registered by
//! its owner instead of listed in the stage driver (now 722-738); its tensors
//! are allocated once at setup, so a captured graph keeps their addresses
struct StepReset {
  std::string name;   // e.g. "limiter.marks", "register", "vic.dry_clamp"
  std::string owner;
  std::function<void()> reset;          // in place only: zero_, fill_
  std::function<void()> commit, drop;   // optional: step accepted, rejected
};

//! one retry flag, stacked with the others in one fixed dtype; causes by name
struct RetryFlag {
  std::string name, owner, cause;
  torch::Tensor flag;   // 0-d, on the device
};

//! the global corrections leave the block: one Mesh phase for 1 and N blocks
//! (now src/mesh/mesh.cpp:367-402 and src/mesh/meshblock.cpp:983-990)
class Fixer;  // lane R (flux_register.hpp, 543ff84f): partial_sums, apply
//! the registry is X's: partial_sums() of every fixer, one FP64 collective,
//! then apply(), which posts cell_amount; A's AxialClosureFixer first
struct GlobalCorrection {
  std::vector<std::shared_ptr<Fixer>> fixers;  // every stage, inside exact
};

}  // namespace snap
