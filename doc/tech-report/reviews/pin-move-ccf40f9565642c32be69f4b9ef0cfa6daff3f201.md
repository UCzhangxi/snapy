# Pin move 6fbb397 -> ccf40f9: citations the script would not resolve

STYLE.md section 3.1: when the pin moves, each range is re-resolved by locating its
anchor in the new file; where the anchor has moved to another file, been renamed or
been deleted, the script does not guess but lists the citation here, and the owning
author re-reads the code and rewrites the citation and, if the code changed, the claim.

Old pin `6fbb39750f62b83df096058a4746e77d0a634bc5`, new pin
`ccf40f9565642c32be69f4b9ef0cfa6daff3f201` (two commits: `chengcli/snapy#309`,
bitwise-identical step-cost cuts; `chengcli/snapy#312`, IdealMoist autograd reuse and
kinetics rate constants).

`python3 tools/code_anchors.py bump` resolved every `{{< code >}}` citation: 769 distinct
symbols, 0 unresolved, 33 with a changed body. Every chapter that cites a changed body
was re-read against the diff; the sections whose text changed are listed in the pull
request.

## Open: none

No citation is left at the old pin. The run records that keep the old sha are
provenance, not citations; they are listed below.

## Resolved by hand, recorded for review

The line links (STYLE 10.6) were moved by mapping each range through
`git diff -U0 6fbb397 ccf40f9`: a range no hunk touches shifts by the hunks above it.
The rows below were touched by a hunk, or carry the line numbers in their label, and
were re-resolved by reading the code at `ccf40f9`.

| citation | old | new | why |
|---|---|---|---|
| `src/eos/ideal_moist.cpp` (`species_enthalpy` coefficient), ch04 `_lmars`, `_fluxcov`, ch09 `_x1profile`, appendix H (2), `tools/reader-glossary.json` | `268-270` | `278-281` | #312 added a comment line inside the block when it removed the memo |
| `src/mesh/meshblock.cpp` (the multi-stage averaging block), ch07 `_rk`, appendix H, `tools/reader-glossary.json` | `754-756` | `772-777` | #309 added the dry-block condition on the stage limiter inside the block |
| `tests/CMakeLists.txt` (the CUDA registrations), ch14 `_gpu` | `330-356` | `333-362` | #309 registered `test_fix_vapor_stale_count_cuda` inside the block |
| `src/mesh/meshblock.cpp` (restart path), ch14 `_restart`, 7 labels | `1359-1492` and sub-ranges | `+55` | the link moved, the label kept the old numbers; `_init_from_restart` spans `1414-1547` at `ccf40f9` |
| `src/coord/coordinate.cpp` (coordinate dispatch), appendix A item 20 | label `599-608` | `633-642` | the link moved, the label did not |

Hardcoded `src/mesh/meshblock.cpp` lines in the generators, re-mapped and checked at
`ccf40f9`: `tools/gen_boundary_contract.py` 955 -> 977, 1545 -> 1600, 841 -> 862,
938 -> 960; `tools/gen_forcing_contract.py` 690 -> 708 (`apply_extra_forcing`). The six
generators that refuse a moved pin carry the new `PIN` and their fragments were
rewritten; each reports 0 problems.

`tools/ctest-index.json` was carried forward from the `tests/CMakeLists.txt` diff, not
re-configured (the local kintera, 2.5.13, does not meet the pin's floor): two
registrations added (`test_fix_vapor_stale_count_python` at line 244,
`test_flux_covariance_rowset_python` at line 310), 48 later `defined_at` lines shifted
by 1 (31), 3 (5) or 7 (12). No other file that registers tests changed. Appendix C says so in its
provenance footnote.

## Provenance tags

`tools/check_provenance.py` requires a tag's sha to be the pin or a later commit.

- 64 tags of report-port checks (Python ports that do not execute snapy) were moved to
  `ccf40f9`: each command was re-run from the report directory, its output was
  byte-identical to the committed `.out` file, and the tag now names the environment of
  that re-run (Python 3.14.7 with numpy 2.5.1, or Python 3.13.15 with numpy 2.5.3 and
  sympy 1.14.0). None of them sits in a section whose described behaviour the diff
  changes.
- 16 port tags stay at `6fbb397` because their section's behaviour changed at
  `ccf40f9` (VIC rejection, redo flags, stage limiter, vapour repair, kinetics split,
  reflecting walls, clamp meters, fixer resets, flux covariance); the port checks the
  old code and has to be re-read before it moves.
- 24 port tags stay at `6fbb397` because their re-run here differed from the committed
  output in round-off digits only (same PASS lines; another numpy), except
  `ch13/output_diag_check.py` `[C5]`, whose round-off ratio was 1.96 against a stated
  bound of 2 and so printed FAIL here.
- 21 snapy runs (ctest, CUDA and multi-rank cards) stay at `6fbb397`: they ran a build
  of the old pin, which no longer configures at the new kintera floor.

`tools/provenance-baseline.json` and `tools/ratchet-baseline.json` were written at this
pin move; the offpin instances are these kept records.

## Flags for the next pin owner

- The book's kintera package pin is `c55b13b2` (v2.6.2); snapy at `ccf40f9` requires
  kintera 2.6.3 (CMake, `FindKintera`, `pyproject.toml`). The kinetics section cites
  kintera at `c55b13b2`, where the Jacobian has no rate-constant argument; it needs a
  re-read when the kintera pin moves.
- Kept run records that may differ at `ccf40f9`: the CUDA `run_hydro`
  `jupiter_evap_precip_1d` card (ch14 `_gpu`) and the ch10 ctest table (#312 changes
  the kinetics Jacobian); the ch07 ctest table (#309 moves the VIC post-solve check to
  the device).
- `src/snapy_report/ch07/vic_reject_check.py` and `fig_vic_reject.py` port the old
  rejection flow (separate result and correction guards, two host screens);
  `src/snapy_report/ch07/redo_check.py` cites old meshblock lines in comments.
- New registered tests not listed in the chapter test tables: `test_flux_covariance_rowset`
  (ch04), the two new `test_eos` cases (ch15).
