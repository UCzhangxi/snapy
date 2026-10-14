"""The N2 task map: Appendix G generated from the curated reader-task list (tools/gen_reader_tasks.py).

Every row resolves to the labelled section that answers it, or names a reason; the source gate and the rendered
gate (index.aux, index.toc) each fail on a broken anchor, on a chapter roll-up and on a not-provided row without a
reason, and pass on the real list.

Run from the report directory: `python3 -m pytest tools/tests`.
"""
import copy
import shutil
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1]
REPORT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import gen_reader_tasks as g  # noqa: E402
import gen_task_map as gtm  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "reader-tasks"


@pytest.fixture(scope="module")
def real():
    rows = g.load(g.DATA.read_text(encoding="utf-8"))
    return rows, gtm.labels(g.BOOK), g.bank_records(REPORT), g.findings()


def _row(rows, rid, **change):
    rows = copy.deepcopy(rows)
    next(r for r in rows if r["id"] == rid).update(change)
    return rows


# --- the list ---------------------------------------------------------------------------------------------------

def test_the_list_has_its_195_rows(real):
    rows = real[0]
    assert len(rows) == 195 and len({r["id"] for r in rows}) == 195
    anchored = [r for r in rows if not r["where"].startswith("not provided")]
    assert (len(anchored), len(rows) - len(anchored), len({r["where"] for r in anchored})) == (172, 23, 103)


def test_the_real_list_passes_and_the_appendix_is_fresh(real, capsys):
    assert g.check() == 0
    out = capsys.readouterr().out
    assert "[N2 reader tasks] 0 problem(s); 195 tasks" in out
    assert out.count("finding: ") == 3


def test_the_statuses(real):
    rows, _, bank, _ = real
    assert g.counts(rows, bank) == {"answered": 95, "partly documented": 77, "undocumented": 15,
                                    "unsupported by the code": 0, "outside scope": 8}


@pytest.mark.parametrize("rid,where,note,bank,expected", [
    ("H03", "not provided: content gap: no deck", "", {}, "undocumented"),
    ("Q-007", "not provided: outside scope: a tutorial", "", {}, "outside scope"),
    ("Q-001", "sec-a", "§1", {"Q-001": {"status": "partly documented"}}, "partly documented"),
    ("Q-012a", "sec-a", "§1", {"Q-012": {"status": "answered"}}, "answered"),
    ("Q-004", "sec-a", "§1; partly: no units", {"Q-004": {"status": "answered"}}, "partly documented"),
    ("H20", "sec-a", "§7.6; FLAG PARTIAL", {}, "partly documented"),
    ("DO-x", "sec-a", "§1", {}, "answered"),
    ("H99", "not provided: nothing", "", {}, None),
])
def test_the_status_rule(rid, where, note, bank, expected):
    assert g.status(dict(id=rid, where=where, note=note), bank) == expected


@pytest.mark.parametrize("where,expected", [
    ("not provided: undocumented: no memory estimate (lookup: device memory 0 hits)", "no memory estimate"),
    ("not provided: outside scope: spin-up is a science study (agreed out); lookup: spin-up 0 hits",
     "spin-up is a science study"),
    ("not provided: undocumented: no tutorial; only the contract exists (sec-ch01-initialization)",
     "no tutorial; only the contract exists (@sec-ch01-initialization)"),
    ("not provided: not in the book: no mapping (13-diagnostics.qmd:19, 13-diagnostics.qmd:27)", "no mapping"),
    ("not provided: undocumented: (lookup: 0 hits)", ""),
])
def test_the_printed_reason_drops_the_reviewers_evidence(where, expected):
    assert g.reason(dict(where=where)) == expected


def test_a_broken_anchor_fails(real):
    rows, labs, bank, known = real
    bad = g.problems(_row(rows, "Q-013", where="sec-ch03-nowhere"), labs, g.BOOK, bank, known)
    assert bad == ["Q-013: anchor sec-ch03-nowhere is not a label of the book"]


def test_a_roll_up_target_fails(real):
    rows, labs, bank, known = real
    bad = g.problems(_row(rows, "Q-013", where="sec-ch03"), labs, g.BOOK, bank, known)
    assert bad == ["Q-013: anchor sec-ch03 is a chapter or appendix roll-up; label the answering section and "
                   "anchor the row there"]


def test_a_not_provided_row_without_a_reason_fails(real):
    rows, labs, bank, known = real
    bad = g.problems(_row(rows, "Q-084", where="not provided: undocumented: (lookup: 0 hits)"), labs, g.BOOK, bank,
                     known)
    assert bad == ["Q-084: not provided, but no reason"]
    bad = g.problems(_row(rows, "Q-084", where="not provided"), labs, g.BOOK, bank, known)
    assert bad[0].startswith("Q-084: no status")


def test_a_finding_that_no_longer_holds_fails(real):
    rows, labs, bank, known = real
    bad = g.problems(_row(rows, "Q-032", where="sec-ch15-ch01"), labs, g.BOOK, bank, known)
    assert bad == ["finding Q-032 -> sec-ch15 no longer holds; remove it from reader-tasks-findings.json"]


def test_every_anchor_is_a_section_and_the_three_roll_ups_are_recorded(real):
    rows, labs, _, known = real
    rolled = {r["id"] for r in rows if not r["where"].startswith("not provided")
              and g.rollup(r["where"], labs, g.BOOK)}
    assert rolled == set(known) == {"Q-031c", "Q-032", "Q-047"}


# --- the rendered book ------------------------------------------------------------------------------------------

def _rendered(tmp_path, aux=None, data=None, fragment_edit=None):
    root = tmp_path / "report"
    shutil.copytree(FIX, root)
    book = root / "book"
    if aux is not None:
        (book / "index.aux").write_text(aux)
    rows = g.load(data if data is not None else (root / "tools/reader-tasks.md").read_text())
    known = g.findings(root / "tools/reader-tasks-findings.json")
    frag = book / "_appg.qmd"
    text = g.render(rows, gtm.labels(book), {})
    frag.write_text(fragment_edit(text) if fragment_edit else text)
    return g.rendered_problems(book, rows, {}, known, frag)


def test_the_rendered_fixture_passes(tmp_path):
    problems, stats = _rendered(tmp_path)
    assert problems == []
    assert stats == dict(rows=4, anchored=3, not_provided=1, in_toc=2, rollup_findings=1, unresolved=0)


def test_a_rendered_anchor_that_does_not_resolve_fails(tmp_path):
    aux = (FIX / "book/index.aux").read_text().replace("\\newlabel{sec-ch01-two}", "\\newlabel{sec-ch01-x}")
    problems, stats = _rendered(tmp_path, aux=aux)
    assert problems == ["T-2: anchor sec-ch01-two does not resolve in index.aux"] and stats["unresolved"] == 1


def test_a_rendered_roll_up_target_fails(tmp_path):
    data = (FIX / "tools/reader-tasks.md").read_text().replace("| T-1 | Run one example | T-1 | sec-ch01-one |",
                                                               "| T-1 | Run one example | T-1 | sec-ch01 |")
    problems, _ = _rendered(tmp_path, data=data)
    assert problems == ["T-1: anchor sec-ch01 lands on chapter.1, a chapter or appendix roll-up"]


def test_a_rendered_not_provided_row_without_a_reason_fails(tmp_path):
    problems, _ = _rendered(tmp_path, fragment_edit=lambda t: t.replace("Not provided: no shock-tube deck.",
                                                                         "Not provided."))
    assert problems == ["T-4: not provided, but the appendix prints no reason"]


def test_the_rendered_gate_needs_a_render(tmp_path):
    (tmp_path / "book").mkdir()
    problems, _ = g.rendered_problems(tmp_path / "book", [], {}, {})
    assert problems and "not found" in problems[0]


@pytest.mark.skipif(not (REPORT / "book/index.aux").exists(), reason="needs a local PDF render of the book")
def test_the_real_render_passes(capsys):
    assert g.check_rendered() == 0
    assert "0 unresolved" in capsys.readouterr().out
