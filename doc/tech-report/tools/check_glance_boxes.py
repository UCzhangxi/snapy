#!/usr/bin/env python3
"""Gate: every field label in an "At a glance" box starts its own paragraph (STYLE 2).

Fails, listing file:line, for a line inside an `::: {.callout-note title="At a glance"}` block that starts with a
bold field label (`**Word(s).**`) and is not preceded by a blank line or by the opening fence.
`python3 tools/fix_glance_boxes.py` fixes every such line.

    python3 tools/check_glance_boxes.py              # every .qmd under book/
    python3 tools/check_glance_boxes.py FILE.qmd ... # the files given
"""
from __future__ import annotations

import sys

from fix_glance_boxes import label_lines, targets


def problems(text: str) -> list[tuple[int, str]]:
    """(1-based line, label line) for each label that does not start its own paragraph."""
    lines = text.split("\n")
    return [(j + 1, lines[j]) for j, needs in label_lines(lines) if needs]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    bad = 0
    for path in targets(argv):
        for line, text in problems(path.read_text()):
            print(f"{path}:{line}: field label not preceded by a blank line: {text[:60]}")
            bad += 1
    if bad:
        print(f"check_glance_boxes: FAIL, {bad} label lines (python3 tools/fix_glance_boxes.py fixes them)")
        return 1
    print("check_glance_boxes: pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
