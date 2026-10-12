"""tools/check_figstyle.py: figure code styles only through snapy_report.figstyle, counted per chapter, ratchet.

fixtures/figstyle/ is a small report tree: ch01/fig_clean.py styles only through figstyle (0 sites);
ch02/fig_inline.py sets rcParams twice and fonts inline six ways (8 sites; `markersize` is not a font);
ch03 imports its own `_style` twice, takes a font size from it, and the shim writes rcParams (4 sites);
chapters/common/figstyle.py writes rcParams (1 site); src/snapy_report/figstyle.py is exempt.
Static: nothing in the tree is imported or drawn. Run from the report directory: `python3 -m pytest tools/tests`.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "figstyle"
sys.path.insert(0, str(TOOLS))

import check_figstyle  # noqa: E402


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "report"
    shutil.copytree(FIXTURE, root)
    return root


def baseline(root):
    return root / "tools" / "figstyle-baseline.json"


def test_counts_per_chapter(tree):
    assert check_figstyle.counts(check_figstyle.scan(tree)) == {"ch02": 8, "ch03": 4, "common": 1}


def test_kinds_of_sites(tree):
    sites = check_figstyle.scan(tree)
    kinds = sorted(k for _, _, k, _ in sites["ch02"])
    assert kinds == ["font"] * 6 + ["rc"] * 2
    assert sorted(k for _, _, k, _ in sites["ch03"]) == ["font", "import", "import", "rc"]
    assert sites.get("ch01", []) == []


def test_figstyle_values_and_the_module_itself_are_not_counted(tree):
    rels = {rel for v in check_figstyle.scan(tree).values() for rel, *_ in v}
    assert "src/snapy_report/figstyle.py" not in rels
    assert "src/snapy_report/ch01/fig_clean.py" not in rels


def test_at_the_baseline_passes(tree):
    assert check_figstyle.main(["--report", str(tree)]) == 0
    assert check_figstyle.check(tree, baseline(tree)) == (0, [])


def test_a_new_site_fails(tree):
    f = tree / "src/snapy_report/ch01/fig_clean.py"
    f.write_text(f.read_text().replace('color=fs.BLACK)', 'color=fs.BLACK, fontsize=7)'))
    status, msgs = check_figstyle.check(tree, baseline(tree))
    assert status == 1 and len(msgs) == 1 and msgs[0].startswith("ch01: 1 styling site(s)") and "baseline 0" in msgs[0]


def test_a_removed_site_fails_until_the_baseline_is_lowered(tree):
    f = tree / "src/snapy_report/ch02/fig_inline.py"
    f.write_text(f.read_text().replace('    ax.text(0, 0, "a", fontsize=7)\n', ""))
    status, msgs = check_figstyle.check(tree, baseline(tree))
    assert status == 1 and "--update" in msgs[0]
    assert check_figstyle.main(["--report", str(tree), "--update"]) == 0
    assert json.loads(baseline(tree).read_text())["chapters"]["ch02"] == 7
    assert check_figstyle.check(tree, baseline(tree)) == (0, [])


def test_update_never_raises_the_baseline(tree):
    f = tree / "src/snapy_report/ch01/fig_clean.py"
    f.write_text(f.read_text() + "\nimport matplotlib.pyplot as plt\nplt.rcParams.update({})\n")
    before = baseline(tree).read_text()
    assert check_figstyle.main(["--report", str(tree), "--update"]) == 1
    assert baseline(tree).read_text() == before


def test_chapter_names():
    assert check_figstyle.chapter_of("src/snapy_report/ch05/fig_x.py") == "ch05"
    assert check_figstyle.chapter_of("src/snapy_report/__init__.py") == "package"
    assert check_figstyle.chapter_of("chapters/common/figstyle.py") == "common"
    assert check_figstyle.chapter_of("chapters/06-gravity-energy/checks/x.py") == "ch06"


def test_the_report_is_at_its_committed_baseline():
    status, msgs = check_figstyle.check()
    assert status == 0, msgs
