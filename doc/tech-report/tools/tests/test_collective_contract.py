"""N6 contract drift must fail for registration, backend naming and the reduction."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen_collective_contract as c


def test_clean_contract():
    assert c.check() == 0


@pytest.mark.parametrize('old,new', [
    ('snapy.distributed.set_process_group(dist_c10d._get_default_group())',
     'snapy.distributed.set_process_group(None)'),
    ('BACKEND=gloo torchrun', 'torchrun'),
    ('c10d::ReduceOp::MIN', 'c10d::ReduceOp::MAX'),
    ('process_group.cpp#L215', 'process_group.cpp#L214'),
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
