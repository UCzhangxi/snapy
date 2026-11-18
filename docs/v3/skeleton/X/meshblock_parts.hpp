#pragma once
// Lane X skeleton: declarations only, in no build.
// meshblock.cpp in six parts, one owner each; the MeshBlock API is unchanged but user_output_callback (L-2).
#include <functional>
#include <string>
#include <vector>
#include <torch/torch.h>

namespace snap {

//! now src/mesh/meshblock.cpp:86-574: options, modules, StateStore, initial state
struct BlockInit;       // owner X

//! now src/mesh/meshblock.cpp:698-1007: registers this block's ops into the
//! StageSchedule; no host timers, no global reductions
struct BlockAdvance;    // owner X; ops from R, S, EF, K

//! now src/mesh/meshblock.cpp:644-685, 1111-1205, 1846-1918: exchange phases
//! (pack, host, unpack) and boundary functions, less X's scalar_r divide (1198-1200)
struct BlockExchange;   // owner S

//! now src/mesh/meshblock.cpp:1447-1601: device retry flags, restore, resets
struct BlockRedo;       // owner X; flags from EF, K, R

//! now src/mesh/meshblock.cpp:1603-1833; O takes the checks 1623-1653
struct BlockRestart;    // owner O (question to O)

//! now src/mesh/meshblock.cpp:1226-1339 less 1336-1337 (O, c12f78bb); 1207-1224 (o1 cuts 1220-1223), 1340-1415 X's
struct BlockOutput;     // owner O (question to O)

//! registered by owners (now 713-745), tensors allocated once at setup.
//! kStepStart, once per attempt: R's begin_step(), zero the retry flags, the
//! radial post; kStageZero: u0 backup, K's snapshot_active_set,
//! reset_failures (host drain at 736), the latches 722-738; kRollback (pin order,
//! 1476-1504): u0, radial restore_step, K's restore_active_set, cons2prim, s0,
//! R's rollback() with the marks; retry reruns kStepStart
enum class ResetPhase { kStepStart, kStageZero, kRollback };
struct StepReset {
  std::string name;   // e.g. "limiter.marks", "register", "vic.dry_clamp"
  std::string owner;
  ResetPhase phase;
  std::function<void(double dt)> reset;  // in place only: zero_, fill_, copy_
};

//! one retry flag, stacked in hydro_u's dtype, read once as FP64; slots 0-7 as
//! the pin (src/mesh/meshblock.cpp:1559-1560; loop 1568-1569 stays six, out{} value-
//! initialized; 6, 7 -> bit 2); slot 8 -> bit 6 (64): diffusion.radial, reserved in V3
struct RetryFlag {
  std::string name, owner, cause;
  torch::Tensor flag;   // 0-d, on the device
};

//! the global corrections leave the block: one Mesh phase for 1 and N blocks
//! (now src/mesh/mesh.cpp:367-402 and src/mesh/meshblock.cpp:983-990)
class Fixer;  // lane R's only fixer declaration (flux_register.hpp, 4c59162a)
//! X's registry, no apply of its own: partial_sums() of every fixer, one
//! FP64 collective, then Fixer::apply(u, sums, dt, stage_weight, reg) with
//! stage_weight = that stage's w2 (now src/mesh/meshblock.cpp:1027)
struct GlobalCorrection {
  std::vector<std::shared_ptr<Fixer>> fixers;  // R's Fixer list only
};

}  // namespace snap
