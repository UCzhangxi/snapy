#pragma once
// Lane X skeleton, declarations only, in no build: the general executor (G1), eager by default.
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
class ChemistrySource;  // snapy-owned, declared in K's skeleton (S-K4)

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
  int config_generation;        // only StageExecutor::bump_config_generation()
  int block, stage, segment;
  double dt;                    // recaptured on change first; parameterized later
  std::vector<std::pair<uint64_t, int64_t>> tables;  // (options_digest, epoch) per held kintera table, K 3.3
  std::vector<int64_t> alloc_epochs;  // kintera::alloc_epoch(m), a free function, per module in Op::kintera
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

  double select_dt();  // step-start host phase: global dt (min over blocks and ranks)
  //! once per attempt, before the stage-0 resets: kStepStart (R's begin_step(), then the radial post, now :715)
  void step_start(double dt);
  //! one stage on all blocks, eager or replay per segment; prepare() on each Op::kintera module before warm-up (K 3.3)
  void run_stage(int stage, double dt);
  //! last stage, after the RK combine: finish_step (now src/mesh/meshblock.cpp:905)
  void finish_step(double dt);
  //! every stage, per block in R's order: EF's limiter (907-909), X's scalar slot (920-923), S's solid fill; then A's closure, global phase
  void after_combine(int stage, double dt);
  //! chemistry slot (design 7), last stage: ends MeshBlock::forward; in Mesh::forward, before its final exchange; FP64
  void set_chemistry(std::shared_ptr<ChemistrySource> source);
  //! step-end host phase: one read of the stacked retry flags, MAX allreduce;
  //! kRollback entries on all blocks when rejected; returns the causes
  int decide_retry();
  void observe();  // after the accept, outside graphs: O's Consumer::observe (O's flush sums)

  Capability capability() const;
  void invalidate();  // drops every graph (restart, to(), buffer replacement)
  //! the one owner of config_generation: set_prescribed, option, solid-mask changes
  void bump_config_generation();
  std::map<std::string, int64_t> report() const;  // segments, captures, replays, eager
  std::map<std::string, double> segment_ms() const;  // eager only: CUDA events per segment

 private:
  std::vector<StageSchedule> schedules_;
  //! tables from NoTableBuild::used(); alive while the graph is held (K 3.3)
  struct CapturedGraph { at::cuda::CUDAGraph* graph; std::vector<kintera::ThermoTablesPtr> tables; };
  std::map<GraphKey, CapturedGraph> graphs_;
  ExecutionOptions options_; std::shared_ptr<ChemistrySource> chemistry_;  // null: no chemistry
  MeshImpl* mesh_;
};

}  // namespace snap
