#pragma once
// Lane X skeleton: declarations only, in no build.
// The general executor (G1), from tests/straka_cuda_graph.py; eager is the default.
#include <cstdint>
#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>
#include <torch/torch.h>

namespace kintera {  // K rev 2, skeleton/K/tables.hpp
struct ThermoTables;
using ThermoTablesPtr = std::shared_ptr<ThermoTables const>;
}  // namespace kintera
namespace snap {
class MeshImpl;

enum class SegmentKind {
  kCompute,  // device ops of one block; capturable if every op is
  kPack,     // fill send buffers (device)
  kHost,     // UCX post/progress/complete, allreduce: never captured
  kUnpack,   // read receive buffers (device)
  kGlobal,   // device partial sums over blocks, then a kHost reduction
  kEager     // an op that declared itself not capturable
};
//! one registered device op; owners: R, S, EF, K, X
struct Op {
  std::string name, owner;  // e.g. "rk.combine", lane letter
  std::vector<std::string> kintera;  // kintera modules it calls (GraphKey::alloc_epochs)
  bool capturable;    // no host read, no allocation outside the graph pool
  std::function<void(int block, int stage, double dt)> run;
};
struct Segment {
  SegmentKind kind;
  std::vector<Op> ops;
  bool capturable() const;
};
//! the segments of one RK stage, built once per configuration
struct StageSchedule {
  int stage;
  std::vector<Segment> segments;
};
//! everything a captured graph depends on; any change invalidates it
struct GraphKey {
  int device_index;
  std::vector<int64_t> shapes;  // flattened shapes and strides of the state
  int dtype_generation;         // PrecisionPolicy::generation()
  int store_generation;         // StateStore::generation(): addresses
  int config_generation;        // physics/options changes
  int block, stage, segment;
  double dt;                    // recaptured on change first; parameterized later
  std::vector<std::pair<uint64_t, int64_t>> tables;  // (options_digest, epoch) per held kintera table, K 3.3
  std::vector<int64_t> alloc_epochs;  // alloc_epoch() per module in the ops' Op::kintera
  bool operator<(GraphKey const& other) const;
};

//! deck: integration.execution and integration.execution-strict (names: G7)
struct ExecutionOptions {
  std::string execution = "eager";  // eager | cuda-graph (CUDA only; else eager)
  bool strict = false;  // true: reject before launch if any segment is eager
};
//! per case, separating numerical from graph support (design section 10)
struct Capability {
  bool eager_fp64, eager_fp32, graph_fp64, graph_fp32;
  std::vector<std::string> eager_reasons;  // which ops forced eager segments
};

class StageExecutor {
 public:
  StageExecutor(MeshImpl* mesh, ExecutionOptions const& options);

  //! step-start host phase: global dt (min over blocks and ranks)
  double select_dt();
  //! once per attempt, before the stage-0 resets: kStepStart entries (R's
  //! begin_step(), then the radial post, now src/mesh/meshblock.cpp:715)
  void step_start(double dt);
  //! runs one stage's schedule on all blocks: eager, or replay per segment
  void run_stage(int stage, double dt);
  //! last stage, after the RK combine: finish_step (now
  //! src/mesh/meshblock.cpp:905); R's after_combine follows every combine
  void finish_step(double dt);
  //! step-end host phase: one read of the stacked retry flags, MAX allreduce;
  //! kRollback entries on all blocks when rejected; returns the causes
  int decide_retry();
  //! after the accept, outside graphs: O's Consumer::observe (O's flush sums)
  void observe();

  Capability capability() const;
  //! drops every graph (restart, to(), buffer replacement)
  void invalidate();

  //! segment count, captures, replays, eager segments and their reasons
  std::map<std::string, int64_t> report() const;
  std::map<std::string, double> segment_ms() const;  // eager only: CUDA events per segment

 private:
  std::vector<StageSchedule> schedules_;
  //! tables from NoTableBuild::used(); alive while the graph is held (K 3.3)
  struct CapturedGraph { at::cuda::CUDAGraph* graph; std::vector<kintera::ThermoTablesPtr> tables; };
  std::map<GraphKey, CapturedGraph> graphs_;
  ExecutionOptions options_;
  MeshImpl* mesh_;
};

}  // namespace snap
