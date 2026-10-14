"""N6 native scheme route: drift in the generated selection, lookup, classes or shapes must fail."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen_scheme_native as c


def test_clean_contract():
    assert c.check() == 0


@pytest.mark.parametrize('old,new', [
    ('.as<std::string>("dc");', '.as<std::string>("plm");'),
    ('.as<std::string>("roe");', '.as<std::string>("hllc");'),
    ('ADD_ARG(std::string, type) = "hllc";', 'ADD_ARG(std::string, type) = "roe";'),
    ('"Interp: unknown type "', '"Interp: unknown name "'),
    ('this, "interp2");', 'this, "interp1");'),
    ('.check_all_same_dtype(true)', '.check_all_same_dtype(false)'),
    ('src/CMakeLists.txt#L42-L43', 'src/CMakeLists.txt#L41-L43'),
])
def test_contract_drift(tmp_path, old, new):
    target = tmp_path / c.TARGET
    target.parent.mkdir(parents=True)
    (tmp_path / 'code_pin.yml').write_text((c.REPORT / 'code_pin.yml').read_text())
    clean = c.generate(c.REPORT)
    target.write_text(clean)
    assert c.check(tmp_path) == 0
    assert old in clean
    target.write_text(clean.replace(old, new, 1))
    assert c.check(tmp_path) == 1


def test_every_code_line_fits_the_page():
    inside, wide = False, []
    for line in (c.REPORT / c.TARGET).read_text().splitlines():
        if line.strip().startswith('```'):
            inside = not inside
        elif inside and len(line) > 80:
            wide.append(line)
    assert wide == []


def test_the_block_follows_the_scheme_recipe():
    framework = (c.REPORT / 'book/chapters/04-spatial-discretization/_framework.qmd').read_text()
    recipe = framework.index('{{< include 04-spatial-discretization/_howto.qmd >}}')
    native = framework.index('{{< include 04-spatial-discretization/_howto-native.qmd >}}')
    assert recipe < native
