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

//! registered by owners, not listed in the stage driver (now 713-745); the
//! tensors are allocated once at setup, so a captured graph keeps addresses.
//! kStepStart: once per attempt, before the stage-0 resets (step zeroing,
//! then the radial post); kStageZero: backup, marks, counters (now 719-744);
//! kRollback: restore, radial restore_step, register rollback (now
//! 1476-1489); it erases no step-start post: the retry reruns kStepStart
enum class ResetPhase { kStepStart, kStageZero, kRollback };
struct StepReset {
  std::string name;   // e.g. "limiter.marks", "register", "vic.dry_clamp"
  std::string owner;
  ResetPhase phase;
  std::function<void(double dt)> reset;  // in place only: zero_, fill_, copy_
  std::function<void()> commit, drop;   // optional: step accepted, rejected
};

//! one retry flag, stacked with the others in one fixed dtype; causes by name:
//! the pin's bits 0-5 (src/mesh/meshblock.cpp:1585-1596), then
//! "diffusion.radial" = bit 6 (64)
struct RetryFlag {
  std::string name, owner, cause;
  torch::Tensor flag;   // 0-d, on the device
};

//! the global corrections leave the block: one Mesh phase for 1 and N blocks
//! (now src/mesh/mesh.cpp:367-402 and src/mesh/meshblock.cpp:983-990)
class Fixer;  // lane R's only fixer declaration (flux_register.hpp, 3490d7e1)
//! X's registry, no apply of its own: partial_sums() of every fixer, one
//! FP64 collective, then Fixer::apply(u, sums, dt, stage_weight, reg) with
//! stage_weight = that stage's w2 (now src/mesh/meshblock.cpp:1027)
struct GlobalCorrection {
  std::vector<std::shared_ptr<Fixer>> fixers;  // R's Fixer list only
};

}  // namespace snap
