"""Static check of the runnable cards (N8): tools/do-cards.yaml against the chapter sources (tools/check_do_cards.py).

The check fails on a card that names no deck, on a deck that does not resolve, when the sources and the data file
disagree on the card set, and on a stale named exception. The fixture repository under fixtures/do-cards shows each
failure on a two-card book; the last tests run the check on the real book and data file.

Run from the report directory: `python3 -m pytest tools/tests`.
"""

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import check_do_cards as c  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "do-cards"
REPORT = FIX / "repo" / "doc" / "report"


def _check(name):
    return c.check(REPORT, FIX / "data" / name)


# --- the fixture book ---------------------------------------------------------------------------------------------

def test_the_fixture_book_has_two_cards():
    assert [x["anchor"] for x in c.source_cards(REPORT / "book")] == ["sec-ch01-one", "sec-ch01-two"]


def test_the_check_passes_when_every_card_has_a_deck_that_resolves():
    assert _check("good.yaml") == (0, [])


def test_the_check_fails_on_a_card_that_names_no_deck():
    status, msgs = _check("no-deck.yaml")
    assert status == 1
    assert msgs == ["ch01-two: names no deck"]


def test_a_named_exception_lets_exactly_that_card_pass():
    assert _check("no-deck-excepted.yaml") == (0, [])


def test_an_exception_fails_once_its_card_is_fixed():
    status, msgs = _check("stale-exception.yaml")
    assert status == 1
    assert msgs == ["ch01-two: stale exception: the card now passes, remove it from exceptions"]


def test_the_check_fails_on_a_deck_that_does_not_resolve():
    status, msgs = _check("bad-deck.yaml")
    assert status == 1
    assert msgs == ["ch01-two: deck examples/missing.yaml does not resolve in the repository"]


def test_the_check_fails_on_a_card_with_no_record():
    status, msgs = _check("missing-record.yaml")
    assert status == 1
    assert any("card under sec-ch01-two" in m and "has no record" in m for m in msgs)


def test_the_check_fails_on_a_record_with_no_card():
    status, msgs = _check("extra-record.yaml")
    assert status == 1
    assert any(m.startswith("ch01-three: record for sec-ch01-three, but no card") for m in msgs)


def test_the_loader_refuses_another_layout():
    import pytest
    with pytest.raises(ValueError):
        c.load("cards:\n  - id: ch01-one\n")


# --- the real book and data file ----------------------------------------------------------------------------------

def test_the_real_data_file_matches_the_sources():
    report = TOOLS.parent
    status, msgs = c.check(report)
    assert (status, msgs) == (0, [])
    data = c.load((report / "tools" / "do-cards.yaml").read_text(encoding="utf-8"))
    assert len(data["cards"]) == len(c.source_cards(report / "book")) == 69


def test_the_construction_card_has_no_runnable_claim_or_exception():
    data = c.load((TOOLS / "do-cards.yaml").read_text())
    card = next(r for r in data['cards'] if r['id'] == 'ch04-sphsrc')
    assert card['class'] == 'not runnable'
    assert card['expect'] == 'nothing to run'
    assert card['run']['kind'] == 'none'
    assert not data['exceptions']
