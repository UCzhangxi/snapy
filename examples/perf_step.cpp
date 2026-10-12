// perf_step: the run_hydro step loop (dynamics + kinetics + check_redo) as a
// measurement tool for the GPU step survey (docs/perf/gpu-step-survey.md).
//
//   perf_step.release -i deck.yaml        (env below)
//   PERF_DEVICE=cuda|cpu   device (default cpu)
//   PERF_KINETICS=1        run the kinetics step (moist decks)
//   PERF_STEPS=n           steps before the dump (default 200)
//   PERF_DUMP=file         after PERF_STEPS steps, write hydro_u (pickle)
//   PERF_WARM=n PERF_TIME=m  after the dump: n warm steps, then time m steps
//                          (device-synchronised) -> ms/step
//   PERF_COUNT=k           then count k steps: CUDA kernels/memcpys (Kineto)
//                          and leaf ATen ops (the CPU proxy)
//   perf_step.release --compare a.pt b.pt   bitwise comparison of two dumps
//
// The leaf-op proxy: a RecordFunction callback counts ATen ops with no child
// op, excluding views and allocations; on the earth_crm 2-D decks it matched
// the measured CUDA kernel counts within 2%.
#include <ATen/record_function.h>
#include <torch/csrc/autograd/profiler_kineto.h>
#include <torch/cuda.h>
#include <yaml-cpp/yaml.h>

#include <chrono>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <map>
#include <set>

#include <kintera/constants.h>
#include <kintera/kinetics/evolve_implicit.hpp>
#include <kintera/kinetics/kinetics.hpp>
#include <kintera/thermo/thermo.hpp>

#include <snap/input/command_line.hpp>
#include <snap/mesh/meshblock.hpp>

using namespace snap;

struct Frame {
  std::string name;
  bool scope;
  bool child;
  int64_t bytes;
};
struct Stat {
  int64_t kernels = 0, bytes = 0, syncs = 0;
  std::map<std::string, int64_t> ops;
};
static thread_local std::vector<Frame> g_stack;
static std::map<std::string, Stat> g_stats;
static bool g_on = false;
// timing mode: only user scopes, inclusive and exclusive wall time
struct TFrame { std::string path; std::chrono::steady_clock::time_point t0; double child; };
static thread_local std::vector<TFrame> t_stack;
static std::map<std::string, std::pair<double, double>> t_stats;  // incl, excl ms
static bool t_on = false;
static std::unique_ptr<at::ObserverContext> t_start(const at::RecordFunction& fn) {
  if (!t_on) return nullptr;
  std::string name = fn.name();
  if (name.rfind("snap::", 0) != 0) return nullptr;
  std::string path = t_stack.empty() ? name.substr(6) : t_stack.back().path + "/" + name.substr(6);
  t_stack.push_back({path, std::chrono::steady_clock::now(), 0.});
  return nullptr;
}
static void t_end(const at::RecordFunction& fn, at::ObserverContext*) {
  if (!t_on) return;
  std::string name = fn.name();
  if (name.rfind("snap::", 0) != 0 || t_stack.empty()) return;
  auto f = t_stack.back();
  t_stack.pop_back();
  double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - f.t0).count();
  t_stats[f.path].first += ms;
  t_stats[f.path].second += ms - f.child;
  if (!t_stack.empty()) t_stack.back().child += ms;
}
static const std::set<std::string> kNoKernel = {
    "aten::empty", "aten::empty_strided", "aten::view", "aten::slice",
    "aten::select", "aten::narrow", "aten::as_strided", "aten::unsqueeze",
    "aten::squeeze", "aten::expand", "aten::permute", "aten::transpose",
    "aten::t", "aten::alias", "aten::_reshape_alias", "aten::reshape",
    "aten::detach", "aten::lift_fresh", "aten::resize_", "aten::set_",
    "aten::unfold", "aten::diagonal", "aten::result_type", "aten::to",
    "aten::contiguous", "aten::_unsafe_view", "aten::expand_as",
    "aten::view_as", "aten::squeeze_", "aten::unsqueeze_", "aten::split",
    "aten::unbind", "aten::chunk", "aten::split_with_sizes",
    "aten::scalar_tensor", "aten::empty_like", "aten::lift",
    "aten::_has_compatible_shallow_copy_type", "aten::is_nonzero",
    "aten::movedim", "aten::flatten", "aten::numpy_T", "aten::matrix_H",
    "aten::_nested_tensor_from_mask_left_aligned", "aten::align_to",
    "aten::detach_", "aten::_conj", "aten::conj", "aten::resolve_conj",
    "aten::resolve_neg", "aten::item", "aten::unflatten", "aten::swapaxes",
    "aten::is_same_size", "aten::broadcast_tensors", "aten::_shape_as_tensor",
    "aten::stride", "aten::size", "aten::sym_size", "aten::sym_stride"};

static int64_t ivalue_bytes(c10::IValue const& v) {
  int64_t b = 0;
  if (v.isTensor()) {
    auto const& t = v.toTensor();
    if (t.defined()) b += t.numel() * t.element_size();
  } else if (v.isTensorList()) {
    for (auto const& t : v.toTensorList()) {
      at::Tensor tt = t;
      if (tt.defined()) b += tt.numel() * tt.element_size();
    }
  }
  return b;
}

static std::string scope_of() {
  for (int i = (int)g_stack.size() - 1; i >= 0; --i)
    if (g_stack[i].scope) return g_stack[i].name;
  return "(none)";
}
static std::string scope_path() {
  std::string p;
  for (auto const& f : g_stack)
    if (f.scope) p += (p.empty() ? "" : "/") + f.name.substr(6);
  return p.empty() ? "(none)" : p;
}

static std::unique_ptr<at::ObserverContext> on_start(
    const at::RecordFunction& fn) {
  if (!g_on) return nullptr;
  std::string name = fn.name();
  bool scope = name.rfind("snap::", 0) == 0;
  if (!g_stack.empty()) g_stack.back().child = true;
  int64_t b = 0;
  if (!scope) {
    try {
      for (auto const& v : fn.inputs()) b += ivalue_bytes(v);
    } catch (...) {
      b = -1;  // inputs not recorded for this op
    }
  }
  g_stack.push_back({name, scope, false, b});
  return nullptr;
}
static void on_end(const at::RecordFunction& fn, at::ObserverContext*) {
  if (!g_on || g_stack.empty()) return;
  auto f = g_stack.back();
  int64_t ob = 0;
  if (!f.scope) {
    try {
      for (auto const& v : fn.outputs()) ob += ivalue_bytes(v);
    } catch (...) {
      ob = 0;
    }
  }
  g_stack.pop_back();
  if (f.scope) return;
  auto& st = g_stats[scope_path()];
  if (f.name == "aten::_local_scalar_dense") {
    st.syncs++;
    st.ops["SYNC item"]++;
    return;
  }
  if (f.child) return;  // count leaves only
  if (kNoKernel.count(f.name)) return;
  // in-place ops: the output aliases an input, count it once
  bool inplace = !f.name.empty() && f.name.back() == '_';
  st.kernels++;
  if (f.bytes < 0) {
    st.ops["(no-inputs) " + f.name]++;
    f.bytes = ob;
  }
  st.bytes += f.bytes + (inplace ? 0 : ob);
  st.ops[f.name]++;
}


static int compare(std::string const& a, std::string const& b) {
  auto read = [](std::string const& p) {
    std::ifstream f(p, std::ios::binary);
    std::vector<char> buf((std::istreambuf_iterator<char>(f)),
                          std::istreambuf_iterator<char>());
    return torch::pickle_load(buf).toTensor();
  };
  auto x = read(a), y = read(b);
  bool same_shape = x.sizes() == y.sizes();
  bool eq = same_shape && torch::equal(x, y);
  // byte-level: also distinguishes -0 from +0 and NaN payloads
  bool bytes = same_shape &&
               std::memcmp(x.data_ptr(), y.data_ptr(), x.nbytes()) == 0;
  double maxabs = same_shape ? (x - y).abs().max().item<double>() : -1.;
  double maxrel = same_shape
                      ? ((x - y).abs() / y.abs().clamp_min(1e-300)).max().item<double>()
                      : -1.;
  int64_t ndiff = same_shape ? (x != y).sum().item<int64_t>() : -1;
  std::cout << "equal(==)=" << eq << " bytes_identical=" << bytes
            << " ndiff=" << ndiff << " max_abs=" << maxabs
            << " max_rel=" << maxrel << std::endl;
  return bytes ? 0 : 1;
}

static int env_int(char const* k, int d) {
  return std::getenv(k) ? std::atoi(std::getenv(k)) : d;
}

int main(int argc, char** argv) {
  if (argc == 4 && std::string(argv[1]) == "--compare")
    return compare(argv[2], argv[3]);
  torch::set_num_threads(1);
  torch::set_num_interop_threads(1);

  auto cli = CommandLine::ParseArguments(argc, argv);
  if (!cli) return 0;
  auto infile = std::string(cli->input_filename);
  int nsteps = env_int("PERF_STEPS", 200);
  int nwarm = env_int("PERF_WARM", 0);
  int ntime = env_int("PERF_TIME", 0);
  int ncount = env_int("PERF_COUNT", 0);
  bool kinetics = env_int("PERF_KINETICS", 0) == 1;
  std::string devname = std::getenv("PERF_DEVICE") ? std::getenv("PERF_DEVICE") : "cpu";

  auto config = YAML::LoadFile(infile);
  auto Ps = config["problem"]["Ps"].as<double>(1.e5);
  auto Ts = config["problem"]["Ts"].as<double>(300.);
  auto Tmin = config["problem"]["Tmin"].as<double>(200.);
  auto grav = -config["forcing"]["const-gravity"]["grav1"].as<double>();

  auto op_block = MeshBlockOptionsImpl::from_yaml(infile);
  auto block = MeshBlock(op_block);
  torch::Device device(torch::kCPU);
  if (devname == "cuda") device = torch::Device(torch::kCUDA, 0);
  block->to(device);
  auto sync = [&]() {
    if (device.is_cuda()) torch::cuda::synchronize();
  };
  auto phydro = block->phydro;
  auto pcoord = block->pcoord;
  auto peos = phydro->peos;
  auto m = block->named_modules()["hydro.eos.thermo"];
  auto thermo_y = std::dynamic_pointer_cast<kintera::ThermoYImpl>(m);

  int nc3 = pcoord->x3v.size(0);
  int nc2 = pcoord->x2v.size(0);
  int nc1 = pcoord->x1v.size(0);
  int ny = thermo_y->options->species().size() - 1;
  int nvar = peos->nvar();

  kintera::ThermoX thermo_x(thermo_y->options);
  thermo_x->to(device);
  auto opt = torch::TensorOptions().dtype(torch::kDouble).device(device);
  auto temp = Ts * torch::ones({nc3, nc2}, opt);
  auto pres = Ps * torch::ones({nc3, nc2}, opt);
  auto xfrac = torch::zeros({nc3, nc2, 1 + ny}, opt);
  auto w = torch::zeros({nvar, nc3, nc2, nc1}, opt);
  for (int i = 1; i <= ny; ++i) {
    auto name = thermo_y->options->species()[i];
    xfrac.select(2, i) = config["problem"]["x" + name].as<double>(0.);
  }
  xfrac.select(2, 0) = 1. - xfrac.narrow(-1, 1, ny).sum(-1);
  int il = pcoord->il(), iu = pcoord->iu();
  auto dz = pcoord->dx1f[il].item<double>();
  thermo_x->extrapolate_dz(temp, pres, xfrac,
                           kintera::ExtrapOptions().dz(dz / 2.).grav(grav).ds_dz(0.));
  int i = il;
  for (; i <= iu; ++i) {
    auto conc = thermo_x->compute("TPX->V", {temp, pres, xfrac});
    w[IPR].select(2, i) = pres;
    w[IDN].select(2, i) = thermo_x->compute("V->D", {conc});
    if (ny > 0) w.narrow(0, ICY, ny).select(3, i) = thermo_x->compute("X->Y", {xfrac});
    if ((temp < Tmin).any().item<double>()) break;
    dz = pcoord->dx1f[i].item<double>();
    thermo_x->extrapolate_dz(temp, pres, xfrac,
                             kintera::ExtrapOptions().dz(dz).grav(grav).ds_dz(0.));
  }
  for (; i <= iu; ++i) {
    auto mu = (thermo_x->mu * xfrac).sum(-1);
    dz = pcoord->dx1f[i].item<double>();
    pres *= exp(-grav * mu * dz / (kintera::constants::Rgas * temp));
    auto conc = thermo_x->compute("TPX->V", {temp, pres, xfrac});
    w[IPR].select(2, i) = pres;
    w[IDN].select(2, i) = thermo_x->compute("V->D", {conc});
    if (ny > 0) w.narrow(0, ICY, ny).select(3, i) = thermo_x->compute("X->Y", {xfrac});
  }
  torch::manual_seed(1234);  // same noise on every run
  w[IVX] += 0.01 * torch::rand_like(w[IVX]);
  w[IVY] += 0.01 * torch::rand_like(w[IVY]);

  std::map<std::string, torch::Tensor> vars;
  vars["hydro_w"] = w;
  double current_time = block->initialize(vars, nullptr);

  kintera::Kinetics kinet = nullptr;
  if (kinetics) {
    auto op_kinet = kintera::KineticsOptionsImpl::from_yaml(infile);
    kinet = kintera::Kinetics(op_kinet);
    kinet->to(device);
  }


  auto one_step = [&]() {
    ++block->cycle;
    double dt;
    {
      RECORD_USER_SCOPE("snap::step.max_time_step");
      dt = block->max_time_step(vars);
    }
    {
      RECORD_USER_SCOPE("snap::step.print_cycle_info");
      block->print_cycle_info(vars, current_time, dt);
    }
    for (int stage = 0; stage < block->pintg->stages.size(); ++stage) {
      RECORD_USER_SCOPE("snap::stage");
      block->forward(vars, dt, stage);
    }
    if (kinetics) {
      RECORD_USER_SCOPE("snap::step.kinetics");
      auto& hydro_u = vars["hydro_u"];
      auto& hydro_w = vars["hydro_w"];
      peos->forward(hydro_u, hydro_w);
      auto temp = peos->compute("W->T", {hydro_w});
      auto pres = hydro_w[IPR];
      auto xfrac = thermo_y->compute("Y->X", {hydro_w.narrow(0, ICY, ny)});
      auto conc = thermo_x->compute("TPX->V", {temp, pres, xfrac});
      auto cp_vol = thermo_x->compute("TV->cp", {temp, conc});
      auto conc_kinet = conc.slice(-1, 1, conc.size(-1));
      auto [rate, rc_ddC, rc_ddT] = kinet->forward(temp, pres, conc_kinet);
      auto jac = kinet->jacobian(temp, conc_kinet, cp_vol, rate, rc_ddC, rc_ddT);
      auto del_conc = kintera::evolve_implicit(rate, kinet->stoich, jac, dt);
      std::vector<int64_t> vec(del_conc.dim(), 1);
      vec[del_conc.dim() - 1] = -1;
      auto del_rho = del_conc / thermo_y->inv_mu.narrow(0, 1, ny).view(vec);
      hydro_u.narrow(0, ICY, ny) += del_rho.permute({3, 0, 1, 2});
    }
    int err;
    {
      RECORD_USER_SCOPE("snap::step.check_redo");
      err = block->check_redo(vars);
    }
    if (err == 0) current_time += dt;
    return err;
  };

  int redo = 0;
  for (int n = 0; n < nsteps; ++n) redo += one_step() != 0;
  sync();
  if (const char* dump = std::getenv("PERF_DUMP")) {
    auto bytes = torch::pickle_save(vars.at("hydro_u").to(torch::kCPU).contiguous());
    std::ofstream f(dump, std::ios::binary);
    f.write(bytes.data(), bytes.size());
  }
  std::cout << "steps=" << nsteps << " redo=" << redo << " cycle=" << block->cycle
            << std::endl;

  if (ntime > 0) {
    for (int n = 0; n < nwarm; ++n) one_step();
    sync();
    auto t0 = std::chrono::steady_clock::now();
    for (int n = 0; n < ntime; ++n) one_step();
    sync();
    auto t1 = std::chrono::steady_clock::now();
    std::cout << "ms_per_step="
              << std::chrono::duration<double, std::milli>(t1 - t0).count() / ntime
              << std::endl;
  }

  if (ncount > 0) {
    using namespace torch::profiler::impl;
    std::set<ActivityType> acts{ActivityType::CPU};
    if (device.is_cuda()) acts.insert(ActivityType::CUDA);
    ProfilerConfig cfg(ProfilerState::KINETO);
    torch::autograd::profiler::prepareProfiler(cfg, acts);
    torch::autograd::profiler::enableProfiler(cfg, acts);
    for (int n = 0; n < ncount; ++n) one_step();
    sync();
    auto result = torch::autograd::profiler::disableProfiler();
    int64_t kernels = 0, mem = 0;
    for (auto const& e : result->events()) {
      if (e.deviceType() != c10::DeviceType::CUDA) continue;
      auto nm = e.name();
      if (nm.find("Memcpy") != std::string::npos ||
          nm.find("Memset") != std::string::npos)
        ++mem;
      else
        ++kernels;
    }
    // leaf-op proxy over the same number of steps
    auto handle = at::addThreadLocalCallback(
        at::RecordFunctionCallback(on_start, on_end)
            .needsInputs(true)
            .needsOutputs(true)
            .scopes({at::RecordScope::FUNCTION, at::RecordScope::USER_SCOPE}));
    g_on = true;
    for (int n = 0; n < ncount; ++n) one_step();
    g_on = false;
    at::removeCallback(handle);
    int64_t leaf = 0, syncs = 0;
    for (auto const& [k, s] : g_stats) {
      leaf += s.kernels;
      syncs += s.syncs;
    }
    std::cout << "cuda_kernels_per_step=" << double(kernels) / ncount
              << " cuda_memcpy_memset_per_step=" << double(mem) / ncount
              << " leaf_ops_per_step=" << double(leaf) / ncount
              << " item_calls_per_step=" << double(syncs) / ncount << std::endl;
  }
  CommandLine::Destroy();
  return 0;
}
