"""N6 scheme contract drift must fail for the interface, faces, ghost width, dispatch and the recipe."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen_scheme_contract as c


def test_clean_contract():
    assert c.check() == 0


@pytest.mark.parametrize('old,new', [
    ('torch::Tensor forward(torch::Tensor w, int dim, bool floor = true);',
     'torch::Tensor forward(torch::Tensor w, int dim);'),
    ('int nghost = pinterp1->stencils() / 2 + 1;', 'int nghost = pinterp1->stencils() / 2;'),
    ('if (opts->type() == "dc") {', 'if (opts->type() == "donor") {'),
    ('interp.type("dc")', 'interp.type("plm")'),
    ('enum { DIM1 = 3, DIM2 = 2, DIM3 = 1 };', 'enum { DIM1 = 1, DIM2 = 2, DIM3 = 3 };'),
])
def test_contract_drift(tmp_path, old, new):
    target = tmp_path / c.TARGET
    target.parent.mkdir(parents=True)
    (tmp_path / 'code_pin.yml').write_text((c.REPORT / 'code_pin.yml').read_text())
    clean = c.generate(c.REPORT)
    assert old in clean
    target.write_text(clean.replace(old, new))
    assert c.check(tmp_path) == 1
    target.write_text(clean)
    assert c.check(tmp_path) == 0
