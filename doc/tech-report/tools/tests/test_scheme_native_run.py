"""Registration of the schemes, on a code-pin build (N6 native route): opt-in, like the do-cards runner.

The whole module skips unless SNAP_PIN_BUILD names a chengcli/snapy build at the sha of code_pin.yml and the
snapy package of that build is importable. Each case builds a block from a tiny copy of
examples/straka_single.yaml with one reconstruction and one Riemann solver selected by name, and runs one stage;
a name that no branch of `InterpImpl::create` or `RiemannSolverImpl::create` handles must be refused with the
message of that branch.

  SNAP_PIN_BUILD=<build> python3 -m pytest -q -rs tools/tests/test_scheme_native_run.py
"""
import os
from pathlib import Path

import pytest

if not os.environ.get("SNAP_PIN_BUILD"):
    pytest.skip("opt-in runner: set SNAP_PIN_BUILD to a code-pin build directory", allow_module_level=True)
yaml = pytest.importorskip("yaml")
torch = pytest.importorskip("torch")
snapy = pytest.importorskip("snapy")

REPO = Path(__file__).resolve().parents[4]


def _block(tmp_path, recon, riemann):
    deck = yaml.safe_load((REPO / "examples/straka_single.yaml").read_text())
    deck["geometry"]["cells"] = {"nx1": 8, "nx2": 1, "nx3": 1, "nghost": 3}
    deck["boundary-condition"] = {"external": {"x1-inner": "reflecting", "x1-outer": "reflecting"}}
    deck["integration"] = {"type": "rk1", "cfl": 0.5}
    deck["dynamics"]["reconstruct"] = {"vertical": {"type": recon}, "horizontal": {"type": recon}}
    deck["dynamics"]["riemann-solver"] = {"type": riemann}
    for key in ("outputs", "forcing", "problem"):
        deck.pop(key, None)
    path = tmp_path / "deck.yaml"
    path.write_text(yaml.safe_dump(deck))
    return snapy.MeshBlock(snapy.MeshBlockOptions.from_yaml(str(path)))


@pytest.mark.parametrize("recon", ["dc", "plm", "weno5"])
@pytest.mark.parametrize("riemann", ["roe", "lmars", "hllc"])
def test_a_registered_name_builds_and_runs_one_stage(tmp_path, recon, riemann):
    block = _block(tmp_path, recon, riemann)
    coord, eos = block.module("coord"), block.module("hydro.eos")
    w = torch.zeros((eos.nvar(), coord.buffer("x3v").numel(), coord.buffer("x2v").numel(),
                     coord.buffer("x1v").numel()), dtype=torch.float64)
    w[snapy.kIDN] = 1.
    w[snapy.kIPR] = 1.e5
    variables, _ = block.initialize({"hydro_w": w})
    before = variables["hydro_u"].clone()
    block.advance_local(variables, 0.01, 0)
    torch.testing.assert_close(variables["hydro_u"], before, rtol=0, atol=1.e-9)


@pytest.mark.parametrize("recon,riemann,message", [
    ("mine", "roe", "Interp: unknown type mine"),
    ("dc", "mine", "RiemannSolver: unknown type mine"),
])
def test_an_unregistered_name_is_refused(tmp_path, recon, riemann, message):
    with pytest.raises(RuntimeError, match=message):
        _block(tmp_path, recon, riemann)


@pytest.mark.parametrize("block,expected", [(None, "hllc"), ({"dir": "omni"}, "roe"), ({"type": "lmars"}, "lmars")])
def test_the_riemann_default_depends_on_whether_the_section_exists(tmp_path, block, expected):
    deck = yaml.safe_load((REPO / "examples/straka_single.yaml").read_text())
    deck["dynamics"].pop("riemann-solver", None)
    if block is not None:
        deck["dynamics"]["riemann-solver"] = block
    path = tmp_path / "deck.yaml"
    path.write_text(yaml.safe_dump(deck))
    assert snapy.MeshBlockOptions.from_yaml(str(path)).hydro().riemann().type() == expected


def test_the_reader_check_in_the_book_passes(tmp_path):
    """The `Check the registration` code of the generated block, run as written from a repository-like root."""
    import subprocess
    import sys
    block = (Path(__file__).resolve().parents[2]
             / "book/chapters/04-spatial-discretization/_howto-native.qmd").read_text()
    code = block[block.index("**Check the registration.**"):]
    code = code[code.index("```python\n") + len("```python\n"):]
    code = code[:code.index("```")]
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples/straka_single.yaml").write_text((REPO / "examples/straka_single.yaml").read_text())
    (tmp_path / "check.py").write_text(code)
    run = subprocess.run([sys.executable, "check.py"], cwd=tmp_path, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout[-400:] + run.stderr[-800:]
    assert "N6 scheme: the selected names are registered" in run.stdout
