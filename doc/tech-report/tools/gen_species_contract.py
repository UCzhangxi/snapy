"""N6: extract the species and condensate interface from the code pin and kintera; verify both complete blocks."""
import json
import re
import subprocess
import sys
from pathlib import Path

import code_anchors

REPORT = Path(__file__).resolve().parent.parent
TARGETS = {
    'species': 'book/chapters/02-thermodynamics/_howto-species.qmd',
    'condensate': 'book/chapters/10-moist-coupling/_howto-condensate.qmd',
}
PIN = '6fbb39750f62b83df096058a4746e77d0a634bc5'
KINTERA = ('chengcli/kintera', 'c55b13b2204997d2d09e04498558ab9495d8ee77')  # kintera v2.6.2


def _reader(repo, sha):
    checkout = code_anchors.find_commit(repo, sha)

    def read(path):
        return subprocess.run(['git', '-C', str(checkout), 'show', f'{sha}:{path}'],
                              check=True, capture_output=True, text=True).stdout

    def excerpt(path, pattern, flat=False):
        text = read(path)
        matches = list(re.finditer(pattern, text, re.M | re.S))
        if len(matches) != 1:
            raise ValueError(f'{repo} {path}: expected one match, got {len(matches)}')
        match = matches[0]
        first = text[:match.start()].count('\n') + 1
        last = first + match[0].rstrip('\n').count('\n')
        lines = f'L{first}' if last == first else f'L{first}-L{last}'
        label = f'{path}:{first}' if last == first else f'{path}:{first}-{last}'
        if repo != 'chengcli/snapy':
            label = f'{repo.split("/")[1]} {label}'
        return (' '.join(match[0].split()) if flat else match[0].strip(), f'[`{label}`](https://github.com/{repo}/blob/{sha}/{path}#{lines})')

    return excerpt


def _scalar(text):
    text = text.strip()
    for kind in (int, float):
        try:
            return kind(text)
        except ValueError:
            pass
    return text


def _entry(block):
    """One flat deck entry (`- key: value` lines, values scalar or a one-line `{k: v}` map), as a Python dict
    literal; the deck's own lines are cited next to it."""
    entry = {}
    for line in block.splitlines():
        line = line.split('#')[0].strip().removeprefix('- ')
        if not line:
            continue
        key, value = (part.strip() for part in line.split(':', 1))
        if value.startswith('{'):
            pairs = (item.split(':', 1) for item in value.strip('{}').split(','))
            entry[key] = {k.strip(): _scalar(v) for k, v in pairs}
        else:
            entry[key] = _scalar(value)
    return json.dumps(entry)


SETUP = '''```python
from pathlib import Path
import torch
import snapy
import kintera
import yaml

# The chemistry of the repository deck, on a tiny column with no native source.
deck = yaml.safe_load(Path("examples/bryan.yaml").read_text())
deck["geometry"] = {
    "type": "cartesian",
    "cells": {"nx1": 4, "nx2": 1, "nx3": 1, "nghost": 3},
    "bounds": {"x1min": 0., "x1max": 1.e3, "x2min": 0.,
               "x2max": 1., "x3min": 0., "x3max": 1.},
}
deck["boundary-condition"] = {"external": {
    "x1-inner": "reflecting", "x1-outer": "reflecting"}}
deck["integration"] = {"type": "rk1", "cfl": 0.5}
for key in ("outputs", "forcing", "problem", "reactions"):
    deck.pop(key, None)
dry = deck["species"][0]

def build(species, reactions, name):
    deck["species"] = species
    if reactions:
        deck["reactions"] = reactions
    Path(name).write_text(yaml.safe_dump(deck))
    block = snapy.MeshBlock(snapy.MeshBlockOptions.from_yaml(name))
    return block, block.module("hydro.eos").nvar()

def one_stage(block, nvar, vapour, pressure):
    coord = block.module("coord")
    shape = (nvar, coord.buffer("x3v").numel(),
             coord.buffer("x2v").numel(), coord.buffer("x1v").numel())
    w = torch.zeros(shape, dtype=torch.float64)
    w[snapy.kIDN].fill_(1.)
    w[snapy.kIPR].fill_(pressure)
    w[snapy.kICY].fill_(vapour)
    variables, _ = block.initialize({"hydro_w": w})
    before = variables["hydro_u"].clone()
    block.advance_local(variables, 0.01, 0)
    return before[..., 3:-3], variables["hydro_u"][..., 3:-3]
```'''


def generate(report):
    repo, sha = code_anchors.read_pin(report / 'code_pin.yml')
    if sha != PIN:
        raise ValueError('N6 needs review when the code pin changes')
    snap = _reader(repo, sha)
    kin = _reader(*KINTERA)
    krepo, ksha = KINTERA

    vapour, vapour_cite = snap('examples/bryan.yaml', r'^  - name: H2O\n(?:    [^\n]+\n)+')
    cloud, cloud_cite = snap('examples/bryan.yaml', r'^  - name: H2O\(l\)\n(?:    [^\n]+\n)+')
    reaction, reaction_cite = snap('examples/bryan.yaml', r'^reactions:\n(?:  [^\n]+\n)+')
    load, load_cite = snap('src/eos/equation_of_state.cpp',
        r'  op->thermo\(\) = kintera::ThermoOptionsImpl::from_yaml\(filename, op->verbose\(\)\);')
    nvar, nvar_cite = snap('src/eos/ideal_moist.hpp',
        r'    return 4 \+ pthermo->options->vapor_ids\(\)\.size\(\) \+\n[^;]+;', flat=True)
    icy, icy_cite = snap('python/csrc/snapy.cpp', r'  m\.attr\("kICY"\) = \(int\)snap::ICY;')
    gate, gate_cite = snap('src/mesh/meshblock.cpp',
        r'  if \(stage == pintg->stages\.size\(\) - 1 && phydro->options->eos\(\)->thermo\(\) &&\n'
        r'      phydro->options->eos\(\)->thermo\(\)->reactions\(\)\.size\(\) > 0\)', flat=True)
    writeback, writeback_cite = snap('src/mesh/meshblock.cpp', r'    hydro_u\.narrow\(0, ICY, ny\) = yfrac \* rho;')
    cause, cause_cite = snap('src/mesh/meshblock.cpp',
        r'"the saturation adjustment left a cell unadjusted, or the VIC "')

    phase, phase_cite = kin('src/species.cpp',
        r'    TORCH_CHECK\(phase\.empty\(\) \|\| phase == "gas" \|\| phase == "liquid" \|\|\n[^;]+;')
    cv, cv_cite = kin('src/species.cpp', r'      species_cref_R\.push_back\(5\. / 2\.\);')
    u0, u0_cite = kin('src/species.cpp', r'      species_uref_R\.push_back\(0\.\);')
    clear, clear_cite = kin('src/species.cpp', r'  clear_species_registry\(\);\n  loaded_species = [^\n]+')
    ref, ref_cite = kin('src/thermo/thermo_options.cpp', r'  vapor_set\.insert\(species_names\[0\]\);')
    inert, inert_cite = kin('src/thermo/thermo_options.cpp',
        r'    if \(species_phases\[i\] == "gas"\) \{\n.*?      vapor_set\.insert\(name\);')
    nucleation, nucleation_cite = kin('src/thermo/thermo_options.cpp',
        r'    thermo->nucleation\(\) =\n        NucleationOptionsImpl::from_yaml\(config\["reactions"\]\);\n'
        r'    add_to_vapor_cloud\(vapor_set, cloud_set, thermo->nucleation\(\)\);')
    product, product_cite = kin('src/thermo/nucleation.cpp',
        r'      if \(species_phases\[id\] == "gas"\) \{\n        vapor_set\.insert\(name\);\n'
        r'        op->has_gas_products = true;\n      \} else \{\n        cloud_set\.insert\(name\);\n      \}')
    reactant, reactant_cite = kin('src/thermo/nucleation.cpp',
        r'      TORCH_CHECK\(species_phases\[id\]\.empty\(\) \|\| species_phases\[id\] == "gas",\n[^;]+;')
    formulas, formulas_cite = kin('src/func_table.cpp', r'    "h2o_ideal",[^\n]+\n[^\n]+"nh3_ideal",[^\n]+')

    vapour_py, cloud_py, reaction_py = _entry(vapour), _entry(cloud), _entry(reaction.split('\n', 1)[1])

    species = f'''<!-- generated reader-reference: species-contract -->
<!-- Generated by tools/gen_species_contract.py; do not edit. -->
#### How to add one

**A minimal input.** Follow steps 0–5 in one Python file, run from the repository root. The example adds a
gas that no reaction names, and checks that it becomes a state row only when it declares its phase.
Adding a condensate, which a reaction names, is @sec-ch10-satadj.

0. Prepare a tiny column with the chemistry of `examples/bryan.yaml`, and two helpers: one builds a block from a
   species list, one runs one stage on a uniform state.

{SETUP}

1. Write the species entry. Its values are those of the deck ({vapour_cite}).

```python
vapour = {vapour_py}
```

2. Select its phase. No reaction names this species here, so only `phase: gas` makes it a state row.

```python
listed = dict(vapour)
vapour["phase"] = "gas"
```

3. Build three blocks: dry air alone, the species without a phase, and the species with it.

```python
_, n_dry = build([dry], None, "tiny_dry.yaml")
_, n_listed = build([dry, listed], None, "tiny_listed.yaml")
block, n_gas = build([dry, vapour], None, "tiny_gas.yaml")
```

4. Run one stage with the new row filled.

```python
before, after = one_stage(block, n_gas, 0.01, 1.e5)
```

5. Check the effect: one more state row, at `kICY`, carried unchanged by a stage at rest.

```python
assert (n_dry, n_listed, n_gas) == (5, 5, 6)
assert kintera.species_names() == ["dry", "H2O"]
torch.testing.assert_close(after[snapy.kICY], before[snapy.kICY], rtol=0, atol=0)
print("N6 species: H2O with phase gas adds state row", snapy.kICY)
```

- **Contract.** Reading: the EOS builds its species table from the same YAML card,
  `{load}` ({load_cite}).
- Keys: `name`, `composition` (the molar mass comes from it), `cv_R`, `u0_R` and `phase`. A missing `cv_R`
  defaults as `{cv}` ({cv_cite}); a missing `u0_R` as `{u0}` ({u0_cite}).
- Phase: empty, `gas`, `liquid` or `solid`; anything else is refused ({phase_cite}).
- Reference species: the first entry is always a state species ({ref_cite}); the dry air goes first.
- State rows: a species is a row when a reaction names it or when it declares a phase ({inert_cite});
  a listed species with neither is in kintera's table but not in the state.
- Row count: `{nvar}` ({nvar_cite}), that is the five hydro rows plus one per
  species after the first. The first species row is `kICY` ({icy_cite}).
- One table per process: each card clears kintera's species table and loads its own ({clear_cite});
  `kintera.species_names()` lists the card loaded last, as step 5 checks.

CI checks the contract, and the runtime test runs on a pin build.

**No C++ needed.** A species is data in the card. Its thermodynamics follow from `cv_R`, `u0_R` and the
composition; a phase change is added in the reaction list (@sec-ch10-satadj).
<!-- end reader-reference: species-contract -->
'''

    condensate = f'''<!-- generated reader-reference: condensate-contract -->
<!-- Generated by tools/gen_species_contract.py; do not edit. -->
#### How to add one

**A minimal input.** Follow steps 0–5 in one Python file, run from the repository root. The example adds a
condensate and the reaction that names it, and checks that one step's saturation adjustment moves water from
the vapour to the condensate. Adding a gas on its own is @sec-ch02-ideal-moist.

0. Prepare a tiny column with the chemistry of `examples/bryan.yaml`, and two helpers: one builds a block from a
   species list and a reaction list, one runs one stage on a uniform state.

{SETUP}

1. Write the vapour and the condensate entries. Their values are those of the deck at the pin
   ({vapour_cite}, {cloud_cite}).

```python
vapour = {vapour_py}
cloud = {cloud_py}
```

2. Name it in a reaction, with a saturation formula of kintera ({reaction_cite}).

```python
reactions = [{reaction_py}]
```

3. Build the block.

```python
block, nvar = build([dry, vapour, cloud], reactions, "tiny_cloud.yaml")
```

4. Run one stage on a cold, supersaturated state.

```python
before, after = one_stage(block, nvar, 0.02, 8.e4)
```

5. Check the effect: water moves from the vapour row to the condensate row, and total water and energy are kept.

```python
i = snapy.kICY
assert nvar == 7
assert (after[i] < before[i]).all() and (after[i + 1] > 0).all()
torch.testing.assert_close(after[i:i + 2].sum(0), before[i:i + 2].sum(0), rtol=1.e-12, atol=0)
torch.testing.assert_close(after[snapy.kIPR], before[snapy.kIPR], rtol=1.e-12, atol=0)
print("N6 condensate: condensed", float((after[i + 1]).mean()), "kg m^-3 in one stage")
```

- **Contract.** Classification: the reaction list is read as nucleation reactions, which sort their species
  into vapours and condensates ({nucleation_cite}). A reactant must be a gas ({reactant_cite}).
- Entry: the condensate is a species entry of its own. A product is a condensate unless it declares
  `phase: gas` ({product_cite}), so leave the phase empty or give `liquid` or `solid`.
- Formula: `rate-constant: {{formula: ...}}` names one of kintera's saturation functions
  ({formulas_cite}).
- When: once per step, on the last stage, whenever the reaction list is non-empty:
  `{gate}` ({gate_cite}).
- What it writes: only the species rows, `{writeback}` ({writeback_cite}); the energy row is not written,
  as step 5 checks.
- Failure: a cell the solve leaves unadjusted makes the block redo the step with a smaller `dt`
  ({cause_cite}).

CI checks the contract, and the runtime test runs on a pin build.

**Native C++ alternative.** A new saturation formula is a C++ function registered by name in kintera's
function table ({formulas_cite}); the reaction then names it.
<!-- end reader-reference: condensate-contract -->
'''
    return {'species': species, 'condensate': condensate}


def check(report=REPORT):
    try:
        expected = generate(Path(report))
        errors = []
        for key, target in TARGETS.items():
            if (Path(report) / target).read_text() != expected[key]:
                errors.append(f'{target}: generated keys, rows, reaction or runtime example differs from the pin')
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        errors = [str(exc)]
    print(f'[N6 species contract] {len(errors)} problem(s)')
    for error in errors:
        print('  ' + error)
    return int(bool(errors))


if __name__ == '__main__':
    if '--write' in sys.argv:
        for key, text in generate(REPORT).items():
            (REPORT / TARGETS[key]).write_text(text)
    else:
        sys.exit(check())
