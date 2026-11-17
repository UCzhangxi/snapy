#pragma once
// Lane X skeleton: declarations only, in no build.
// The general executor (roadmap G1), extracted from tests/straka_cuda_graph.py.
// Eager is the reference and the default; a graph replays a segment eagerly
// recorded with the same ops, in the same order.
#include <cstdint>
#include <functional>
#include <map>
#include <string>
#include <vector>
#include <torch/torch.h>

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
  std::string name;   // e.g. "hydro.forward", "rk.combine", "limiter"
  std::string owner;  // lane letter
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
  //! runs one stage's schedule on all blocks: eager, or replay per segment
  void run_stage(int stage, double dt);
  //! step-end host phase: one read of the stacked retry flags, MAX allreduce;
  //! restore + register reset on all blocks when rejected; returns the causes
  int decide_retry();

  Capability capability() const;
  //! drops every graph (restart, to(), buffer replacement)
  void invalidate();

  //! segment count, captures, replays, eager segments and their reasons
  std::map<std::string, int64_t> report() const;

 private:
  std::vector<StageSchedule> schedules_;
  std::map<GraphKey, at::cuda::CUDAGraph*> graphs_;
  ExecutionOptions options_;
  MeshImpl* mesh_;
};

}  // namespace snap
