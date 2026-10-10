# Chapter 2 scope and evidence

Rules base: `4b6c2041eca0ed4a2abbedeb4be2290553f086db`. Code: snapy
`e894700ff7aee30b52882e5202b16461413780b0`. Dependency: kintera
`c55b13b2204997d2d09e04498558ab9495d8ee77`, as prescribed by the frozen rules.
The requested snapy main pin takes precedence over the old round pin printed in STYLE.
All snapy links use the full requested main SHA. kintera internals necessarily use their own full dependency SHA.

| outline | required scope | derivation evidence | existing tests | new-run decision |
|---|---|---|---|---|
| 2.1 | Conservation laws; flux/source integration; stage and wall ordering | 2 re-derive | wall saturation | No run needed for telescoping proof; compiled wall rerun remains evidence gap |
| 2.2 | Factory, keys, defaults, validation, type capabilities | interface | hydro options; EOS | No new physics run; configuration assertions not rerun |
| 2.3 | Ideal closure; metric kinetic contraction; fused conversion | 1 re-derive | zero offset; old round trips commented out | New compiled metric inverse test useful |
| 2.4 | Mixture factors; heat ratio; reference energy; enthalpy | 3 re-derive | offset; temperature map; registry | No run for algebra; existing compiled regressions not rerun |
| 2.5 | Sound speed; Newton inversions; enthalpy; NASA/H2; cache | 4 re-derive | EOS cache; enthalpy carry | Pinned compiled heat-capacity plot remains needed |
| 2.6 | External table interface and throwing stubs | interface | none | Requires external implementation for runtime evidence |
| 2.7 | Depth-like state; metric conversion; undefined thermo keys | interface | FULL_TESTS shallow examples | No new thermodynamic run; examples not rerun |
| 2.8 | Temperature-map identity; inverse maps; enthalpy sum; own tables | 2 re-derive | temp2inteng; registry; two cards | Dedicated moist-mixture temperature-map regression remains needed |
| 2.9 | UV constraint; active equations; KKT; warm start; diagnostics | 1 re-derive | redo saturation; wall saturation | Full active-set/runtime convergence evidence not supplied |

The outline lists 13 re-derivations and no existing complete derivation for this chapter. The draft derives
these identities from code. Source history is not promoted into measured evidence. Independent report checks
cover the algebra; full active-set behavior and the requested compiled H2 plot remain explicit gaps.

## Code anchors by section

Every row below is a full pinned link; the corresponding Code table gives its symbol.
The machine-readable manifest also covers equation and Chapter 15 test citations.

### 2.1

| what | code link | symbol | switch |
|---|---|---|---|
| flux and native sources | [`hydro_forward.cpp:754-765`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_forward.cpp#L754-L765) | `du` | `none` |
| implicit step | [`hydro_forward.cpp:915-943`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/hydro/hydro_forward.cpp#L915-L943) | `dt_corr` | `none` |
| callbacks | [`meshblock.cpp:731-756`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L731-L756) | `pintg` | `none` |
| last stage | [`meshblock.cpp:795-841`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L795-L841) | `apply_boundaries` | `none` |
| row layout | [`snap.h:34-55`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/snap.h#L34-L55) | `ICY` | `none` |

: Code map. {#tbl-ch02-laws-code}

### 2.2

| what | code link | symbol | switch |
|---|---|---|---|
| YAML validation/defaults | [`equation_of_state.cpp:33-99`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/equation_of_state.cpp#L33-L99) | `from_yaml` | `type` |
| struct defaults | [`equation_of_state.hpp:45-57`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/equation_of_state.hpp#L45-L57) | `density_floor` | `type` |
| factory | [`equation_of_state.cpp:356-374`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/equation_of_state.cpp#L356-L374) | `create` | `type` |
| base fallback | [`equation_of_state.cpp:165-173`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/equation_of_state.cpp#L165-L173) | `specific_heat_cv` | `type` |

: Code map. {#tbl-ch02-interface-code}

### 2.3

| what | code link | symbol | switch |
|---|---|---|---|
| conversion keys | [`ideal_gas.cpp:30-65`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/ideal_gas.cpp#L30-L65) | `compute` | `ideal-gas` |
| metric and energy | [`ideal_gas.cpp:67-118`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/ideal_gas.cpp#L67-L118) | `_prim2cons` | `ideal-gas` |
| fused conversion | [`ideal_gas_impl.h:16-35`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/ideal_gas_impl.h#L16-L35) | `ideal_gas_cons2prim` | `ideal-gas` |

: Code map. {#tbl-ch02-ideal-gas-code}

### 2.4

| what | code link | symbol | switch |
|---|---|---|---|
| reset and reference energies | [`ideal_moist.cpp:18-51`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/ideal_moist.cpp#L18-L51) | `u0` | `ideal-moist` |
| offset | [`ideal_moist.cpp:70-83`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/ideal_moist.cpp#L70-L83) | `internal_energy_offset` | `ideal-moist` |
| maps | [`ideal_moist.cpp:164-233`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/ideal_moist.cpp#L164-L233) | `_cons2prim` | `ideal-moist` |
| species energy/enthalpy | [`ideal_moist.cpp:235-280`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/ideal_moist.cpp#L235-L280) | `species_enthalpy` | `ideal-moist` |
| temperature map | [`ideal_moist.cpp:293-317`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/ideal_moist.cpp#L293-L317) | `_temp2intEng` | `ideal-moist` |

: Code map. {#tbl-ch02-ideal-moist-code}

### 2.5

| what | code link | symbol | switch |
|---|---|---|---|
| reset | [`moist_mixture.cpp:18-31`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/moist_mixture.cpp#L18-L31) | `reset` | `moist-mixture` |
| conserved map | [`moist_mixture.cpp:124-162`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/moist_mixture.cpp#L124-L162) | `_cons2prim` | `moist-mixture` |
| enthalpy | [`moist_mixture.cpp:196-218`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/moist_mixture.cpp#L196-L218) | `species_enthalpy` | `moist-mixture` |
| temperature map | [`moist_mixture.cpp:232-243`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/moist_mixture.cpp#L232-L243) | `_temp2intEng` | `moist-mixture` |
| cache | [`moist_mixture.cpp:275-294`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/moist_mixture.cpp#L275-L294) | `_ensure_cache` | `moist-mixture` |
| pressure Newton | [`kintera thermo_y.cpp:439-472`](https://github.com/chengcli/kintera/blob/c55b13b2204997d2d09e04498558ab9495d8ee77/src/thermo/thermo_y.cpp#L439-L472) | `_pres_to_temp` | `moist-mixture` |
| NASA polynomial | [`kintera eval_uhs.cpp:24-58`](https://github.com/chengcli/kintera/blob/c55b13b2204997d2d09e04498558ab9495d8ee77/src/thermo/eval_uhs.cpp#L24-L58) | `nasa9_cp_R` | `moist-mixture` |
| rotor modes | [`kintera eval_uhs.cpp:95-147`](https://github.com/chengcli/kintera/blob/c55b13b2204997d2d09e04498558ab9495d8ee77/src/thermo/eval_uhs.cpp#L95-L147) | `eval_h2cp` | `moist-mixture` |

: Code map. {#tbl-ch02-moist-mixture-code}

### 2.6

| what | code link | symbol | switch |
|---|---|---|---|
| keys | [`aneos.cpp:12-48`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/aneos.cpp#L12-L48) | `compute` | `aneos` |
| conserved map | [`aneos.cpp:71-109`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/aneos.cpp#L71-L109) | `_cons2prim` | `aneos` |
| throwing stubs | [`aneos_thermo_dummy.cpp:14-32`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/aneos/aneos_thermo_dummy.cpp#L14-L32) | `ANEOSThermoImpl` | `aneos` |

: Code map. {#tbl-ch02-aneos-code}

### 2.7

| what | code link | symbol | switch |
|---|---|---|---|
| keys | [`shallow_water.cpp:14-35`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/shallow_water.cpp#L14-L35) | `compute` | `shallow-water` |
| maps | [`shallow_water.cpp:38-68`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/shallow_water.cpp#L38-L68) | `_cons2prim` | `shallow-water` |

: Code map. {#tbl-ch02-shallow-water-code}

### 2.8

| what | code link | symbol | switch |
|---|---|---|---|
| floor consumer | [`equation_of_state.cpp:226-233`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/equation_of_state.cpp#L226-L233) | `min_ie` | `none` |
| own species table | [`equation_of_state.cpp:110-134`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/equation_of_state.cpp#L110-L134) | `cache_cloud_parents_` | `none` |
| nonlinear energy evaluation | [`moist_mixture.cpp:232-243`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/moist_mixture.cpp#L232-L243) | `_temp2intEng` | `none` |
| enthalpy carry | [`moist_mixture.cpp:196-218`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/eos/moist_mixture.cpp#L196-L218) | `species_enthalpy` | `none` |

: Code map. {#tbl-ch02-consistency-code}

### 2.9

| what | code link | symbol | switch |
|---|---|---|---|
| snapy call | [`meshblock.cpp:795-816`](https://github.com/chengcli/snapy/blob/e894700ff7aee30b52882e5202b16461413780b0/src/mesh/meshblock.cpp#L795-L816) | `pthermo` | `uv-solver` |
| warm start and solver | [`kintera thermo_y.cpp:275-356`](https://github.com/chengcli/kintera/blob/c55b13b2204997d2d09e04498558ab9495d8ee77/src/thermo/thermo_y.cpp#L275-L356) | `uv_solver` | `uv-solver` |
| failure counter | [`kintera thermo_y.cpp:358-389`](https://github.com/chengcli/kintera/blob/c55b13b2204997d2d09e04498558ab9495d8ee77/src/thermo/thermo_y.cpp#L358-L389) | `nfail_` | `uv-solver` |
| active equations | [`kintera equilibrate_uv.h:383-504`](https://github.com/chengcli/kintera/blob/c55b13b2204997d2d09e04498558ab9495d8ee77/src/thermo/equilibrate_uv.h#L383-L504) | `weight` | `uv-solver` |
| diagnostic encoding | [`kintera equilibrate_uv.h:609-612`](https://github.com/chengcli/kintera/blob/c55b13b2204997d2d09e04498558ab9495d8ee77/src/thermo/equilibrate_uv.h#L609-L612) | `diag` | `uv-solver` |

: Code map. {#tbl-ch02-saturation-code}

## Validation boundary

No snapy or kintera build was started and no installed package was used as evidence of either pinned tree.
The existing Python environment supplies NumPy 2.4.6, SymPy 1.14.0 and Matplotlib 3.10.9 for report checks.
No new environment or dependency installation was needed. The default shell Python lacked NumPy, so the
existing scientific Python executable was used explicitly.

The official `tools/check_citations.py` is absent from this base and from the shared workspace search.
Quarto is absent from PATH. The frozen `tools/house/README.md` explicitly says its render gate is not adapted.
Neither the official citation check nor HTML/PDF rendering passed: they were unavailable.
The independent manifest audit checks local git objects, not remote GitHub URL reachability.

The editor owns chapter files and Quarto configuration under STYLE 10.1. `ch02-integration.md` supplies
includes and the chapter opening for that integration, without editing those editor-owned files.
The only unresolved cross-reference in the supplied fragments is the expected `sec-ch12-matrix`.
Peer review is pending. Owner push confirmation is pending; nothing is pushed or posted.
