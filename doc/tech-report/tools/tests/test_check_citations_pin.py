"""tools/check_citations.py on links at the report's pin, chengcli/snapy main e894700ff7aee30b52882e5202b16461413780b0.

fixtures/pin.qmd holds one good link, one with a sha that does not exist and one whose lines run past the end
of the file (src/hydro/gravity_work_radial.hpp has 65 lines at the pin). The pin is not on a branch of the
UCzhangxi fork, so the checker finds it in its cache clone of chengcli/snapy: this test needs the network
unless that cache (CHECK_CITATIONS_CACHE) already holds it. Run from the report directory:
`python3 -m pytest tools/tests`.
"""

import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pin.qmd"
sys.path.insert(0, str(TOOLS))

import check_citations  # noqa: E402

PIN = "e894700ff7aee30b52882e5202b16461413780b0"


@pytest.fixture(scope="module")
def problems():
    """{fixture line: [messages]} from one run of the checker over pin.qmd."""
    import contextlib
    import io
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        status = check_citations.main([str(FIXTURE)])
    found = {}
    for line in out.getvalue().splitlines():
        n = int(line.split(":", 2)[1])
        found.setdefault(n, []).append(line)
    if any("could not clone" in m or "not found in chengcli/snapy" in m for m in found.get(1, [])):
        pytest.skip(f"the pin {PIN} cannot be reached (no network and no cache clone)")
    return status, found


def test_the_good_link_passes(problems):
    _, found = problems
    assert 1 not in found, found[1]


def test_a_sha_that_does_not_exist_fails(problems):
    status, found = problems
    assert status == 1
    assert any("sha e894700ff7aee30b52882e5202b16461413780b1 not found in chengcli/snapy" in m
               for m in found.get(2, [])), found


def test_lines_past_the_end_fail(problems):
    status, found = problems
    assert status == 1
    assert any(f"line 70 is past the end of src/hydro/gravity_work_radial.hpp at {PIN} (65 lines)" in m
               for m in found.get(3, [])), found
