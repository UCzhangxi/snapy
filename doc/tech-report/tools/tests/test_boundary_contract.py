"""Source drift and generated recipe drift must fail the N6 boundary gate."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen_boundary_contract as c


def test_clean_boundary_contract():
    assert c.check() == 0


@pytest.mark.parametrize("old,new", [
    ("dx1: int", "dx1: float"),
    ("self->bfuncs()[face] = func;", "self->bfuncs()[face] = nullptr;"),
    ("nx1() + 2 * nghost()", "nx1() + nghost()"),
])
def test_boundary_source_drift(monkeypatch, capsys, old, new):
    read = c.read_source
    seen = []
    def mutated(*args):
        text = read(*args)
        if old in text:
            seen.append(True)
        return text.replace(old, new)
    monkeypatch.setattr(c, "read_source", mutated)
    assert c.check() == 1
    assert seen
    assert "[N6 boundary contract] 1 problem(s)" in capsys.readouterr().out
    monkeypatch.setattr(c, "read_source", read)
    assert c.check() == 0


def test_boundary_recipe_drift(tmp_path):
    target = tmp_path / c.TARGET
    target.parent.mkdir(parents=True)
    (tmp_path / "code_pin.yml").write_text((c.REPORT / "code_pin.yml").read_text())
    clean = c.generate(c.REPORT)
    target.write_text(clean.replace("target.copy_(", "target.add_("))
    assert c.check(tmp_path) == 1
    target.write_text(clean)
    assert c.check(tmp_path) == 0
