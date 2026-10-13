"""Tests of tools/fix_glance_boxes.py and tools/check_glance_boxes.py (STYLE 2, the "At a glance" box).

Inside an `::: {.callout-note title="At a glance"}` block every line that starts with a bold field label
(`**Purpose.**`, `**Evidence.**`, any `**Word(s).**`) follows a blank line, so each field renders as its own
paragraph. A label directly after the opening fence needs no blank line.

Run from the report directory: `python3 -m pytest tools/tests`.
"""

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import check_glance_boxes  # noqa: E402
import fix_glance_boxes  # noqa: E402

JOINED = """## A scheme {#sec-ch99-a}

### Summary

::: {.callout-note title="At a glance"}
**Purpose.** Adds a source; @eq-ch99-a.
**Data.** In: the stage state. Out: the increment
[$\\mathrm{kg\\,m^{-3}}$], continued on a second line.
**Guarantee / limits.** First order in time.
**Evidence.** A test; the check `[C1]`.
:::

Prose after the box.
"""

FIXED = """## A scheme {#sec-ch99-a}

### Summary

::: {.callout-note title="At a glance"}
**Purpose.** Adds a source; @eq-ch99-a.

**Data.** In: the stage state. Out: the increment
[$\\mathrm{kg\\,m^{-3}}$], continued on a second line.

**Guarantee / limits.** First order in time.

**Evidence.** A test; the check `[C1]`.
:::

Prose after the box.
"""


def test_a_joined_box_fails_the_gate():
    problems = check_glance_boxes.problems(JOINED)
    assert [line for line, _ in problems] == [7, 9, 10]


def test_a_fixed_box_passes_the_gate():
    assert check_glance_boxes.problems(FIXED) == []


def test_fix_gives_the_fixed_box():
    assert fix_glance_boxes.fix_text(JOINED) == FIXED


def test_fix_run_twice_is_byte_identical():
    once = fix_glance_boxes.fix_text(JOINED)
    assert fix_glance_boxes.fix_text(once) == once
    assert fix_glance_boxes.fix_text(FIXED) == FIXED


def test_a_label_right_after_the_fence_needs_no_blank_line():
    text = '::: {.callout-note title="At a glance"}\n**Purpose.** One line.\n:::\n'
    assert check_glance_boxes.problems(text) == []
    assert fix_glance_boxes.fix_text(text) == text


def test_a_blank_line_is_not_doubled():
    text = '::: {.callout-note title="At a glance"}\n**Purpose.** A.\n\n**Data.** B.\n:::\n'
    assert fix_glance_boxes.fix_text(text) == text


def test_labels_outside_an_at_a_glance_box_are_untouched():
    text = ("Prose.\n**Purpose.** not in a box.\n"
            '::: {.callout-note title="Definition"}\n**Purpose.** A.\n**Data.** B.\n:::\n'
            '::: {.callout-important title="Test"}\n**Evidence.** A.\n**Coverage.** B.\n:::\n')
    assert fix_glance_boxes.fix_text(text) == text
    assert check_glance_boxes.problems(text) == []


def test_fenced_code_inside_a_box_is_untouched():
    text = ('::: {.callout-note title="At a glance"}\n**Purpose.** A.\n\n'
            "```yaml\n**Data.** not a label\n:::\n**Evidence.** still code\n```\n"
            "**Evidence.** B.\n:::\n")
    want = text.replace("```\n**Evidence.** B.", "```\n\n**Evidence.** B.")
    assert fix_glance_boxes.fix_text(text) == want
    assert [line for line, _ in check_glance_boxes.problems(text)] == [9]
    assert check_glance_boxes.problems(want) == []


def test_a_nested_div_does_not_end_the_box():
    text = ('::: {.callout-note title="At a glance"}\n**Purpose.** A.\n\n'
            "::: {.inner}\nnested text\n:::\n**Data.** B.\n:::\n**Data.** after the box.\n")
    want = text.replace(":::\n**Data.** B.", ":::\n\n**Data.** B.")
    assert fix_glance_boxes.fix_text(text) == want
    assert [line for line, _ in check_glance_boxes.problems(text)] == [7]


def test_bold_text_that_is_not_a_line_start_label_is_untouched():
    text = ('::: {.callout-note title="At a glance"}\n**What**: a colon form. **Switch**: none.\n'
            "Text with **Data.** mid-line.\n- **Purpose.** in a list item\n:::\n")
    assert fix_glance_boxes.fix_text(text) == text
    assert check_glance_boxes.problems(text) == []


def test_the_gate_lists_file_and_line(tmp_path, capsys):
    bad = tmp_path / "bad.qmd"
    bad.write_text(JOINED)
    good = tmp_path / "good.qmd"
    good.write_text(FIXED)
    assert check_glance_boxes.main([str(good)]) == 0
    assert check_glance_boxes.main([str(bad), str(good)]) == 1
    out = capsys.readouterr().out
    assert f"{bad}:7:" in out and f"{bad}:9:" in out and f"{bad}:10:" in out and str(good) not in out


def test_the_fix_script_rewrites_files_in_place(tmp_path):
    p = tmp_path / "a.qmd"
    p.write_text(JOINED)
    assert fix_glance_boxes.main([str(p)]) == 0
    assert p.read_text() == FIXED
    before = p.read_bytes()
    fix_glance_boxes.main([str(p)])
    assert p.read_bytes() == before
