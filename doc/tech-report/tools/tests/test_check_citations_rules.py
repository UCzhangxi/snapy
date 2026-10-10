"""The anchor-symbol check and the allowed-repository list of tools/check_citations.py (STYLE 3.1, #5),
on links at the pin chengcli/snapy e894700ff7aee30b52882e5202b16461413780b0 (src/hydro/gravity_work_radial.hpp: `x1_variance` at lines 13-22,
`centroid_slope` from line 28).

fixtures/anchor.qmd, by line: 1 anchor in range (passes); 2 anchor outside the range; 3 no anchor;
4 a qualified anchor with a call (passes); 8 the Code table's symbol column, in range (passes); 9 symbol
column, outside the range; 11 two links in a sentence, the second with no anchor of its own.
fixtures/repos.qmd: 1 chengcli/snapy (passes); 2 a fork not on the list;
3 pyharp without its name in front of the link text. Needs the network unless CHECK_CITATIONS_CACHE holds
the pin. Run from the report directory: `python3 -m pytest tools/tests`.
"""

import contextlib
import io
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(TOOLS))

import check_citations  # noqa: E402


def run(name):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        status = check_citations.main([str(FIXTURES / name)])
    found = {}
    for line in out.getvalue().splitlines():
        found.setdefault(int(line.split(":", 2)[1]), []).append(line)
    if any("could not clone" in m or "not found in" in m for ms in found.values() for m in ms):
        pytest.skip("the pin cannot be reached (no network and no cache clone)")
    return status, found


@pytest.fixture(scope="module")
def anchor():
    return run("anchor.qmd")


@pytest.fixture(scope="module")
def repos():
    return run("repos.qmd")


def test_anchors_in_range_pass(anchor):
    _, found = anchor
    for line in (1, 4, 8):
        assert line not in found, found[line]


def test_an_anchor_outside_the_range_fails(anchor):
    status, found = anchor
    assert status == 1
    assert any("anchor symbol `centroid_slope` is not in lines 13-22 of src/hydro/gravity_work_radial.hpp" in m
               for m in found.get(2, [])), found


def test_a_link_with_no_anchor_fails(anchor):
    assert any("names no anchor symbol" in m for m in anchor[1].get(3, [])), anchor[1]


def test_the_symbol_column_is_the_anchor_in_a_code_table(anchor):
    assert any("anchor symbol `centroid_slope` is not in lines 13-22" in m for m in anchor[1].get(9, [])), anchor[1]


def test_an_allowed_repository_passes(repos):
    assert 1 not in repos[1], repos[1][1]


def test_a_repository_not_on_the_list_fails(repos):
    status, found = repos
    assert status == 1
    assert any("octocat/snapy is not a repository the report may cite" in m for m in found.get(2, [])), found


def test_another_repository_needs_its_name_in_the_link_text(repos):
    assert any("link text must start with the repository name: 'pyharp integrator.cpp:49-61'" in m
               for m in repos[1].get(3, [])), repos[1]


def test_each_link_names_its_own_anchor(anchor):
    found = anchor[1].get(11, [])
    assert len(found) == 1 and "names no anchor symbol" in found[0] and "#L28-L29" in found[0], found
