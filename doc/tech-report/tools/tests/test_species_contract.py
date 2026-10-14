"""N6 contract drift must fail for the species keys, the state rows and the condensate reaction."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen_species_contract as c


def test_clean_contract():
    assert c.check() == 0


@pytest.mark.parametrize('key,old,new', [
    ('species', 'vapour["phase"] = "gas"', 'vapour["phase"] = "liquid"'),
    ('species', 'assert (n_dry, n_listed, n_gas) == (5, 5, 6)', 'assert (n_dry, n_listed, n_gas) == (5, 6, 6)'),
    ('species', 'src/species.cpp#L175', 'src/species.cpp#L174'),
    ('condensate', '"formula": "h2o_bryan"', '"formula": "h2o_ideal"'),
    ('condensate', 'hydro_u.narrow(0, ICY, ny) = yfrac * rho;', 'hydro_u.narrow(0, IDN, ny) = yfrac * rho;'),
])
def test_contract_drift(tmp_path, key, old, new):
    (tmp_path / 'code_pin.yml').write_text((c.REPORT / 'code_pin.yml').read_text())
    clean = c.generate(c.REPORT)
    for k, target in c.TARGETS.items():
        (tmp_path / target).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / target).write_text(clean[k])
    assert c.check(tmp_path) == 0
    assert old in clean[key]
    (tmp_path / c.TARGETS[key]).write_text(clean[key].replace(old, new))
    assert c.check(tmp_path) == 1
