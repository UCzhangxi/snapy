"""tools/ratchet_gate.py: each check fails on a planted instance (RED) and passes once it is removed (GREEN),
and the ratchet fails on a rise and on an unrecorded fall."""
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import ratchet_gate as rg  # noqa: E402

PIN = "6fbb39750f62b83df096058a4746e77d0a634bc5"
OTHER = "e894700ff7aee30b52882e5202b16461413780b0"
RECORD_HEAD = "file\tkind\treviewer\tauthor\tpin\tsha256\tdate\tnote\n"

CH01 = """# Overview {#sec-ch01}

<!-- PROVENANCE
pin: snapy@%s (old pins in PROVENANCE are not counted)
status: %s
author: Alice
-->

## Scheme one {#sec-ch01-one}

The stage calls the flux (see @sec-ch02-two).%s
"""
CH02 = """# Second {#sec-ch02}

## Scheme two {#sec-ch02-two}

It reads the state of @sec-ch01-one and @sec-ch01.%s
"""


def make(tmp_path, ch01_extra="", ch02_extra="", status="draft", record=""):
    root = tmp_path / "tr"
    (root / "book" / "chapters").mkdir(parents=True)
    (root / "tools").mkdir()
    (root / "reviews").mkdir()
    (root / "code_pin.yml").write_text(f"repo: chengcli/snapy\nsha: {PIN}\n")
    (root / "tools" / "package-pins.json").write_text(json.dumps({"kintera": "c55b13b2" + "0" * 32}))
    (root / "book" / "chapters" / "01-overview.qmd").write_text(CH01 % (OTHER, status, ch01_extra))
    (root / "book" / "chapters" / "02-second.qmd").write_text(CH02 % ch02_extra)
    (root / "reviews" / "review-record.tsv").write_text(RECORD_HEAD + record)
    return root


def counts(root):
    return rg.count(root)


def baseline_zero(root):
    (root / "tools" / "ratchet-baseline.json").write_text(json.dumps({"chapters": {}}))


def check(root):
    return rg.main(["--root", str(root), "check"])


# ---- (a) history phrases ------------------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    " Since chengcli/snapy#303 the slope is centred.",
    " This section describes main after the merge.",
    " The flag previously defaulted to off.",
    " The bug is now fixed.",
    " See #307 for the change.",
])
def test_history_red(tmp_path, text):
    root = make(tmp_path, ch01_extra=text)
    assert counts(root)["ch01"]["history"] >= 1
    baseline_zero(root)
    assert check(root) == 1


def test_history_green_exempts_footnotes_provenance_shortcodes(tmp_path):
    extra = ("[^src]\n\n[^src]: chengcli/snapy#303 body, Limits.\n"
             " {{< code src/hydro/hydro.cpp HydroImpl::reset >}}\n\n```python\n# since #303\n```\n")
    root = make(tmp_path, ch01_extra=extra)
    assert counts(root)["ch01"]["history"] == 0


def test_history_overlap_counts_once(tmp_path):
    root = make(tmp_path, ch01_extra=" It changed after #307.")
    assert counts(root)["ch01"]["history"] == 1


# ---- (b) off-pin shas ---------------------------------------------------------------------------------------

def test_offpin_red_and_green(tmp_path):
    bad = f" [`a.cpp:1`](https://github.com/chengcli/snapy/blob/{OTHER}/src/a.cpp#L1) and snapy@{OTHER[:7]}."
    root = make(tmp_path, ch01_extra=bad)
    assert counts(root)["ch01"]["offpin"] == 2
    good = f" [`a.cpp`](https://github.com/chengcli/snapy/blob/{PIN}/src/a.cpp) and snapy@{PIN}."
    root2 = make(tmp_path / "g", ch01_extra=good)
    assert counts(root2)["ch01"]["offpin"] == 0  # PROVENANCE's old pin is not counted either


def test_offpin_other_package(tmp_path):
    root = make(tmp_path, ch01_extra=" kintera@" + "1" * 40 + " and kintera@c55b13b2" + "0" * 32 + ".")
    assert counts(root)["ch01"]["offpin"] == 1


# ---- (c) status vs the review record ------------------------------------------------------------------------

def entry(root, kind="review", reviewer="Bob", author="Alice", pin=PIN, note="", sha=None):
    text = (root / "book" / "chapters" / "01-overview.qmd").read_text()
    sha = sha or rg.content_hash(text)
    return f"chapters/01-overview.qmd\t{kind}\t{reviewer}\t{author}\t{pin}\t{sha}\t2026-10-12\t{note}\n"


def with_record(root, *lines):
    (root / "reviews" / "review-record.tsv").write_text(RECORD_HEAD + "".join(lines))
    return root


def test_status_red_without_record(tmp_path):
    root = make(tmp_path, status="reviewed")
    assert counts(root)["ch01"]["status"] == 1


def test_status_green_with_record(tmp_path):
    root = make(tmp_path, status="reviewed")
    with_record(root, entry(root))
    assert counts(root)["ch01"]["status"] == 0


@pytest.mark.parametrize("kw", [dict(reviewer="Alice"), dict(pin=OTHER), dict(sha="0" * 64)])
def test_status_red_bad_entry(tmp_path, kw):
    root = make(tmp_path, status="reviewed")
    with_record(root, entry(root, **kw))
    assert counts(root)["ch01"]["status"] == 1


def test_status_restamp(tmp_path):
    root = make(tmp_path, status="reviewed")
    first = entry(root)
    (root / "book" / "chapters" / "01-overview.qmd").write_text(
        (root / "book" / "chapters" / "01-overview.qmd").read_text() + "\nOne more sentence.\n")
    with_record(root, first)
    assert counts(root)["ch01"]["status"] == 1  # RED: content moved past the review
    with_record(root, first, entry(root, kind="restamp", reviewer="Carol", note="typo"))
    assert counts(root)["ch01"]["status"] == 1  # RED: re-stamp by someone else
    with_record(root, first, entry(root, kind="restamp", note=""))
    assert counts(root)["ch01"]["status"] == 1  # RED: re-stamp without a note
    with_record(root, first, entry(root, kind="restamp", note="one sentence added"))
    assert counts(root)["ch01"]["status"] == 0  # GREEN


def test_status_edit_keeps_hash():
    a = "<!-- PROVENANCE\nstatus: draft\n-->\ntext\n"
    b = "<!-- PROVENANCE\nstatus: reviewed\nreviewer: Bob\n-->\ntext\n"
    assert rg.content_hash(a) == rg.content_hash(b)


# ---- (d) cross-references -----------------------------------------------------------------------------------

def test_xref_green_when_cited_across(tmp_path):
    root = make(tmp_path, ch02_extra=" And @sec-ch02 itself.")
    c = counts(root)
    # ch02's sections are cited from ch01 (sec-ch02-two) and ch02's own self-reference does not count
    assert c["ch01"]["xref"] == 0
    assert c["ch02"]["xref"] == 1  # sec-ch02 is cited only from inside ch02


def test_xref_red_dangling(tmp_path):
    root = make(tmp_path, ch01_extra=" See @sec-ch01-missing.")
    assert counts(root)["ch01"]["xref"] == 1


# ---- the ratchet --------------------------------------------------------------------------------------------

def test_ratchet_rise_and_fall(tmp_path):
    root = make(tmp_path, ch01_extra=" The bug is now fixed.")
    assert rg.main(["--root", str(root), "update"]) == 0
    assert check(root) == 0
    (root / "book" / "chapters" / "01-overview.qmd").write_text(
        (root / "book" / "chapters" / "01-overview.qmd").read_text() + " Since #303 too.\n")
    assert check(root) == 1                                   # a rise fails
    assert rg.main(["--root", str(root), "update"]) == 1      # and the baseline cannot be raised
    (root / "book" / "chapters" / "01-overview.qmd").write_text(CH01 % (OTHER, "draft", ""))
    assert check(root) == 1                                   # a fall fails until the baseline is lowered
    assert rg.main(["--root", str(root), "update"]) == 0
    assert check(root) == 0


def test_chapter_of():
    assert rg.chapter_of("chapters/06-gravity-energy/_dwork.qmd") == "ch06"
    assert rg.chapter_of("chapters/16-known-limits.qmd") == "ch16"
    assert rg.chapter_of("chapters/17-appendices/_appb-derivation-index.qmd") == "appb"
    assert rg.chapter_of("chapters/appd-switches/_switches.qmd") == "appd"
