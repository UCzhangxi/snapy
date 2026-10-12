#pragma once
// local profiling scopes (perf study only)
#include <ATen/record_function.h>
#include <optional>
struct SnapScope {
  std::optional<at::RecordFunction> rf;
  explicit SnapScope(const char* name) {
    rf.emplace(at::RecordScope::USER_SCOPE);
    if (rf->isActive()) {
      if (rf->needsInputs())
        rf->before(name, c10::ArrayRef<const c10::IValue>{});
      else
        rf->before(name);
    }
  }
  void end() { rf.reset(); }
};
#define SNAP_BEGIN(var, name) SnapScope var("snap::" name)
#define SNAP_END(var) var.end()
