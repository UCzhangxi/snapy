"""N9 advisory detection, structured replacements and include reachability."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_limitations as lint


@pytest.mark.parametrize("phrase", ["cannot show", "see elsewhere", "shown elsewhere",
                                    "beyond scope", "beyond the\nscope", "not documented"])
def test_unstructured_deferrals_warn(phrase):
    assert lint.findings("This is " + phrase + ".")


@pytest.mark.parametrize("note", ["Answered at @sec-specific.",
                                  "Not provided: the test cannot show convergence order."])
def test_structured_notes_do_not_warn(note):
    assert not lint.findings(note)


def test_unrelated_link_or_late_note_does_not_hide_deferral():
    assert lint.findings("See elsewhere. @sec-other. Not provided: unrelated.")


def test_comments_and_code_are_not_prose():
    assert not lint.findings("<!-- cannot show -->\n\n```text\nsee elsewhere\n```\n")


def test_data_drives_patterns(tmp_path):
    data = tmp_path / "phrases.json"
    data.write_text('{"phrases": ["deferred answer"]}')
    assert lint.findings("A deferred answer.", data=data)


def test_warning_exit_and_reachable_includes(tmp_path, capsys):
    (tmp_path / "_quarto.yml").write_text("book:\n  chapters: [index.qmd]\n")
    (tmp_path / "index.qmd").write_text("{{< include part.qmd >}}")
    (tmp_path / "part.qmd").write_text("See elsewhere.")
    (tmp_path / "unused.qmd").write_text("Cannot show.")
    assert lint.main(["--book", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "part.qmd:1" in output and "unused" not in output
    assert "1 warning(s)" in output


def test_audited_boundary_and_spatial_prose_is_converted():
    book = Path(__file__).resolve().parents[2] / "book"
    files = list((book / "chapters/11-boundaries").glob("*.qmd"))
    files.append(book / "chapters/15-verification/_ch04-spatial-discretization.qmd")
    files.append(book / "chapters/08-positivity/_eoslimiter.qmd")
    assert not [(p.name, hit) for p in files for hit in lint.findings(p.read_text())]


def test_rendered_pdf_warns_without_failing(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace
    def extract(command, **kwargs):
        assert command[0] == "pdftotext"
        return SimpleNamespace(stdout="First page.\fShown elsewhere.\f")
    monkeypatch.setattr(lint.subprocess, "run", extract)
    assert lint.main(["--pdf", str(tmp_path / "book.pdf")]) == 0
    assert "page 2:1: shown elsewhere" in capsys.readouterr().out


def test_numbered_note_and_actual_elsewhere_are_not_deferrals():
    assert not lint.findings("2. **Not provided:** a rationale; this is beyond scope.")
    assert not lint.findings("The field is zero elsewhere.")
