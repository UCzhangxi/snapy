"""N6: the native C++ route for a new reconstruction or Riemann solver, extracted from the code pin.

It completes the scheme contract of tools/gen_scheme_contract.py (the Python recipe, the interface, the faces, the
stencil and ghost width): this block gives how a scheme is selected from YAML and looked up, which class and file
to write, the shapes and in-place outputs, the dtype, device and ownership rules, and the rebuild. Every fact is an
excerpt that must match the pin exactly once, cited with a line permalink.
"""
import re
import subprocess
import sys
from pathlib import Path

import code_anchors

REPORT = Path(__file__).resolve().parent.parent
TARGET = 'book/chapters/04-spatial-discretization/_howto-native.qmd'
PIN = '6fbb39750f62b83df096058a4746e77d0a634bc5'


def generate(report):
    repo, sha = code_anchors.read_pin(report / 'code_pin.yml')
    if sha != PIN:
        raise ValueError('N6 needs review when the code pin changes')
    checkout = code_anchors.find_commit(repo, sha)

    def read(path):
        return subprocess.run(['git', '-C', str(checkout), 'show', f'{sha}:{path}'],
                              check=True, capture_output=True, text=True).stdout

    def excerpt(path, pattern):
        text = read(path)
        matches = list(re.finditer(pattern, text, re.M | re.S))
        if len(matches) != 1:
            raise ValueError(f'{path}: expected one match, got {len(matches)}')
        match = matches[0]
        first = text[:match.start()].count('\n') + 1
        last = first + match[0].rstrip('\n').count('\n')
        lines = f'L{first}' if last == first else f'L{first}-L{last}'
        label = f'{path}:{first}' if last == first else f'{path}:{first}-{last}'
        return (match[0].rstrip(), f'[`{label}`](https://github.com/{repo}/blob/{sha}/{path}#{lines})')

    # reconstruction: selection, lookup, names, class, interface, files
    recon_yaml, recon_yaml_cite = excerpt('src/recon/reconstruct.cpp',
        r'^  check_keys\(node\[section\], "dynamics/reconstruct/" \+ section,\n.*?'
        r'  op->interp\(\)->scale\(\) = node\[section\]\["scale"\]\.as<bool>\(false\);')
    sections, sections_cite = excerpt('src/hydro/hydro_options.cpp',
        r'^  op->recon1\(\) = ReconstructOptionsImpl::from_yaml\(filename, "vertical"\);\n.*?'
        r'  op->recon23\(\) = ReconstructOptionsImpl::from_yaml\(filename, "horizontal"\);')
    names, names_cite = excerpt('src/recon/reconstruct.cpp',
        r'^  pinterp1 = InterpImpl::create\(options->interp\(\), this, "interp1"\);\n'
        r'  pinterp2 = InterpImpl::create\(options->interp\(\), this, "interp2"\);')
    weno, weno_cite = excerpt('src/recon/interpolation.cpp',
        r'^  \} else if \(opts->type\(\) == "weno5"\) \{\n.*?'
        r'      TORCH_CHECK\(false, "Interp: unknown name " \+ name\);\n    \}')
    interp_unknown, interp_unknown_cite = excerpt('src/recon/interpolation.cpp',
        r'^    TORCH_CHECK\(false, "Interp: unknown type " \+ opts->type\(\)\);')
    interp_base, interp_base_cite = excerpt('src/recon/interpolation.hpp',
        r'^  virtual std::pair<torch::Tensor, torch::Tensor> forward\(\n.*?'
        r'    return std::make_pair\(wlv, wrv\);\n  \}')
    dc_class, dc_class_cite = excerpt('src/recon/interpolation.hpp',
        r'^class DonorCellInterpImpl : public torch::nn::Cloneable<DonorCellInterpImpl>,\n.*?'
        r'TORCH_MODULE\(DonorCellInterp\);')
    alloc, alloc_cite = excerpt('src/recon/reconstruct.cpp',
        r'^  auto result = torch::zeros\(vec, w\.options\(\)\);')
    glob, glob_cite = excerpt('src/CMakeLists.txt', r'^    riemann/\*\.cpp\n    recon/\*\.cpp')
    cuglob, cuglob_cite = excerpt('src/CMakeLists.txt', r'^      recon/\*\.cu\n      riemann/\*\.cu')

    # Riemann solver: selection, defaults, lookup, class, call site, in-place flux
    rs_yaml, rs_yaml_cite = excerpt('src/riemann/riemann_solver.cpp',
        r'^  op->type\(\) = node\["type"\]\.as<std::string>\("roe"\);\n'
        r'  op->dir\(\) = node\["dir"\]\.as<std::string>\("omni"\);')
    rs_keys, rs_keys_cite = excerpt('src/riemann/riemann_solver.cpp',
        r'^  check_keys\(config\["dynamics"\]\["riemann-solver"\], "dynamics/riemann-solver",\n[^;]+;')
    rs_none, rs_none_cite = excerpt('src/riemann/riemann_solver.cpp',
        r'^  if \(!config\[section\]\["riemann-solver"\]\) return op;')
    rs_default, rs_default_cite = excerpt('src/riemann/riemann_solver.hpp',
        r'^  ADD_ARG\(std::string, type\) = "hllc";')
    rs_unknown, rs_unknown_cite = excerpt('src/riemann/riemann_solver.cpp',
        r'^    TORCH_CHECK\(false, "RiemannSolver: unknown type " \+ opts->type\(\)\);')
    roe_class, roe_class_cite = excerpt('src/riemann/riemann_solver.hpp',
        r'^class RoeSolverImpl : public torch::nn::Cloneable<RoeSolverImpl>,\n.*?TORCH_MODULE\(RoeSolver\);')
    call, call_cite = excerpt('src/hydro/hydro_forward.cpp',
        r'^      priemann->forward\(wlr1\[ILT\], wlr1\[IRT\], DIM1, _flux1, face_pressure1\);')
    inplace, inplace_cite = excerpt('src/riemann/roe.cpp',
        r'^  auto iter = at::TensorIteratorConfig\(\)\n.*?\.build\(\);')
    device, device_cite = excerpt('src/riemann/roe.cpp',
        r'^  at::native::call_roe\(flx\.device\(\)\.type\(\), iter, dim, ideal_moist, nvapor,')
    parent, parent_cite = excerpt('src/riemann/riemann_solver.hpp',
        r'^  //! non-owning reference to parent\n  HydroImpl const\* phydro = nullptr;')
    register, register_cite = excerpt('src/riemann/riemann_solver.cpp',
        r'^  if \(opts->type\(\) == "roe"\) \{\n    return p->register_module\(name, RoeSolver\(opts, p\)\);')
    rebuild, rebuild_cite = excerpt('README.md',
        r'^cmake -B build -DCMAKE_BUILD_TYPE=Release -DNETCDF=ON\ncmake --build build --parallel 3')
    install, install_cite = excerpt('README.md', r'^5\. Install the Python package:\n```bash\npip install \.')
    install = install.splitlines()[-1]

    return f'''<!-- generated reader-reference: scheme-native -->
<!-- Generated by tools/gen_scheme_native.py; do not edit. -->
#### Native C++ route

The recipe above prototypes a reconstruction in Python and selects a built-in one by name. A new scheme that the
solver itself runs is a C++ class, built into the library and selected from the YAML card. Each step below is a
fact of the code at the pin.

**Select it from YAML.** A reconstruction is read from `dynamics/reconstruct/vertical` for $x_1$ and from
`dynamics/reconstruct/horizontal` for $x_2$ and $x_3$ ({sections_cite}). Each section takes `shock`, `type` and
`scale`; `type` defaults to `dc` ({recon_yaml_cite}):

```cpp
{recon_yaml}
```

A Riemann solver is read from `dynamics/riemann-solver`, whose keys are `type` and `dir` ({rs_keys_cite}).
A section without `type` gives `roe` ({rs_yaml_cite}):

```cpp
{rs_yaml}
```

A card with no such section keeps the options as created ({rs_none_cite}), whose default is another solver,
`hllc` ({rs_default_cite}):

```cpp
{rs_none}
{rs_default}
```

**Lookup.** The name is compared as a string, branch by branch, in `InterpImpl::create` and
`RiemannSolverImpl::create`; there is no table and no suffix added to the name. A name with no branch is refused
when the block is built ({interp_unknown_cite}, {rs_unknown_cite}):

```cpp
{interp_unknown}
{rs_unknown}
```

A reconstruction module is created twice, under the names `interp1` and `interp2` ({names_cite}):

```cpp
{names}
```

and for `weno3` and `weno5` the last character of that name chooses the class ({weno_cite}):

```cpp
{weno}
```

**Write the class.** The header `src/recon/interpolation.hpp` declares `InterpImpl`, the base of every
reconstruction. Its `forward` sizes the two outputs from `stencils()` and fills them through `left` and `right`
({interp_base_cite}):

```cpp
{interp_base}
```

The donor-cell class is the smallest one to follow ({dc_class_cite}):

```cpp
{dc_class}
```

A Riemann solver derives from `RiemannSolverImpl`, declared in `src/riemann/riemann_solver.hpp`
({roe_class_cite}):

```cpp
{roe_class}
```

Add one branch to the matching `create`, as for `roe` ({register_cite}):

```cpp
{register}
```

**Files.** Every `.cpp` file in `src/recon/` and `src/riemann/` is compiled into the library
({glob_cite}), and with CUDA every `.cu` file there ({cuglob_cite}); a new file there needs no CMake edit.

**Shapes, outputs and device.**

- Reconstruction output: the result is allocated like the input, so it has the input's dtype and device, and the
  method writes into it ({alloc_cite}):

  ```cpp
  {alloc}
  ```

- Riemann call: the solver gets the left and right states from the reconstruction, each of the shape of the state
  (the result above is the state's shape with 2 prepended), the direction, and the flux tensor to fill
  ({call_cite}):

  ```cpp
  {call}
  ```

- In place, one dtype: the solver writes the flux into its fourth argument without resizing it, and all tensors
  must share one dtype ({inplace_cite}):

  ```cpp
{chr(10).join("  " + l for l in inplace.splitlines())}
  ```

- Device: the kernel is chosen by the device of the flux tensor ({device_cite}):

  ```cpp
  {device}
  ```

- Ownership: `create` registers the new module as a submodule of its parent with `register_module`
  ({register_cite}); the solver keeps only a non-owning pointer back to its hydro ({parent_cite}):

  ```cpp
{chr(10).join("  " + l for l in parent.splitlines())}
  ```

**Rebuild.** Build the library ({rebuild_cite}) and reinstall the Python package ({install_cite}):

```bash
{rebuild}
{install}
```

Then set the new name as `type` under `dynamics/reconstruct/vertical` or `horizontal`, or under
`dynamics/riemann-solver`.
<!-- end reader-reference: scheme-native -->
'''


def check(report=REPORT):
    try:
        expected = generate(Path(report))
        actual = (Path(report) / TARGET).read_text()
        errors = [] if actual == expected else [
            f'{TARGET}: generated selection, lookup, classes or shapes differ from the pin']
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        errors = [str(exc)]
    print(f'[N6 scheme native] {len(errors)} problem(s)')
    for error in errors:
        print('  ' + error)
    return int(bool(errors))


if __name__ == '__main__':
    if '--write' in sys.argv:
        (REPORT / TARGET).write_text(generate(REPORT))
    else:
        sys.exit(check())
