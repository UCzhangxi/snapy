#!/usr/bin/env python3
"""Ratchet gate for the report's chapter sources (README, "Ratchet gate").

Four counts per chapter, compared with the committed baseline `tools/ratchet-baseline.json`:

  history     change history in body text: PR/issue numbers and phrases such as "main after", "previously",
              "now fixed" (HISTORY_PATTERNS). The body text is the chapter file without HTML comments
              (PROVENANCE), fenced code, `{{< >}}` shortcodes and footnotes, so a source or credit footnote may
              still carry a PR number.
  offpin      a sha of a cited package that is not that package's pin: snapy's pin is `code_pin.yml`, the others
              are `tools/package-pins.json`. Counted in body text, footnotes and link targets; not in PROVENANCE.
  status      a file whose PROVENANCE says `status: reviewed` or `approved` without a valid entry in
              `reviews/review-record.tsv` (see REVIEW RECORD below).
  xref        a `@sec-`/`@eq-`/`@fig-`/`@tbl-` reference that resolves nowhere or that quarto cannot reach
              (render_gate's own resolution), plus every `sec-` label that no file of another chapter cites.

The ratchet: `check` fails when any count differs from the baseline. A rise fails outright; a fall must lower
the baseline in the same PR (`update`), so the baseline only ever shrinks. `update --allow-increase` exists for
the one case where a rise is expected (a pin move), and that PR says why.

REVIEW RECORD (`reviews/review-record.tsv`, tab-separated, one line per event, newest last):

  file    kind    reviewer    author    pin    sha256    date    note

  file      path under book/, e.g. chapters/06-gravity-energy/_dwork.qmd
  kind      `review` (the reviewer read the file) or `restamp` (the same reviewer confirms an unchanged verdict
            after an edit; the note says what changed, in one line)
  pin       the full sha of code_pin.yml the review was made against
  sha256    `python3 tools/ratchet_gate.py hash <file>`: the file's content without its PROVENANCE comment

A reviewed/approved file passes when its newest entry has the file's current hash and the current pin, its
reviewer differs from its author (and from the PROVENANCE `author:` when that is given), and, for a `restamp`,
the reviewer is the one of the newest `review` entry and the note is not empty.

    python3 tools/ratchet_gate.py counts            # the table, per chapter
    python3 tools/ratchet_gate.py check             # CI: exit 1 if any count differs from the baseline
    python3 tools/ratchet_gate.py update            # write the counts as the baseline (no rise allowed)
    python3 tools/ratchet_gate.py hash <file>       # the content hash a review entry records
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

TOOLS = pathlib.Path(__file__).resolve().parent
ROOT = TOOLS.parent
CHECKS = ("history", "offpin", "status", "xref")

# Change history in body text. Built from STYLE.md (sections 1 and 3.2: history is past tense and PR numbers are
# aliases) and the phrases the Q1 re-read removed ("main after", "since #NNN", "at the old pin", ...). Each match
# counts once; matching is case-insensitive.
HISTORY_PATTERNS = [
    r"\b(?:chengcli|UCzhangxi|zoeyzyhu|happysky19)/[\w.-]+#\d+",  # owner/repo#NNN
    r"(?<![\w/&#\[^{])#\d{2,5}\b",                                  # bare #NNN
    r"\bmain after\b",
    r"\bdescribes? main at\b",
    r"\b(?:since|until|before|after|as of) (?:PR )?#\d+",
    r"\bpreviously\b",
    r"\bnow fixed\b",
    r"\bno longer\b",
    r"\bused to\b",
    r"\b(?:at|from) the old pin\b",
    r"\b(?:checked|re-read|pinned) at (?:snapy@|`?[0-9a-f]{7})",
    r"\bwhile the rest of the (?:book|section)\b",
    r"\b(?:was|were|has been|have been) (?:changed|fixed|replaced|removed)\b",
    r"\b(?:fixed|landed|merged) in\b",
]
_HISTORY = [re.compile(p, re.I) for p in HISTORY_PATTERNS]

PACKAGES = ("snapy", "kintera", "pyharp", "pydisort", "commux")
_SHA_PATTERNS = [
    re.compile(r"github\.com/[\w.-]+/(%s)/(?:blob|tree|commit)/([0-9a-f]{7,40})" % "|".join(PACKAGES)),
    re.compile(r"(?<![\w/])(%s)@([0-9a-f]{7,40})\b" % "|".join(PACKAGES)),
]


def chapter_of(rel: str) -> str:
    """The chapter a source file belongs to: ch01..ch17 or appa..appe (files under book/)."""
    parts = pathlib.PurePosixPath(rel).parts
    if len(parts) < 2 or parts[0] != "chapters":
        return "book"
    top = parts[1]
    if top.startswith("app"):
        return top[:4]
    if top == "17-appendices" and len(parts) > 2:
        m = re.match(r"_(app[a-z])-", parts[2])
        if m:
            return m.group(1)
    m = re.match(r"(\d\d)-", top)
    return f"ch{m.group(1)}" if m else top


def _strip_footnotes(text: str) -> str:
    out, in_def = [], False
    for line in text.split("\n"):
        if re.match(r"\[\^[^\]]+\]:", line):
            in_def = True
            continue
        if in_def and (line.startswith("    ") or line.startswith("\t")):
            continue
        in_def = False
        out.append(line)
    text = "\n".join(out)
    # inline footnotes ^[...] (no nesting of brackets inside a footnote in this book)
    return re.sub(r"\^\[[^\]]*\]", "", text)


def body_text(text: str, keep_links: bool = True) -> str:
    """The chapter text a reader sees: no HTML comments, fenced code, shortcodes or footnotes."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"^(```|~~~).*?^\1\s*$", "", text, flags=re.S | re.M)
    text = re.sub(r"\{\{<.*?>\}\}", "", text, flags=re.S)
    text = _strip_footnotes(text)
    if not keep_links:
        text = re.sub(r"\]\([^)]*\)", "]", text)
    return text


def history_hits(text: str) -> list[str]:
    body = body_text(text, keep_links=False)
    spans = sorted((m.start(), m.end()) for rx in _HISTORY for m in rx.finditer(body))
    merged: list[list[int]] = []  # overlapping matches ("after #307" and "#307") count once
    for a, b in spans:
        if merged and a < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [body[a:b] for a, b in merged]


def pins(root: pathlib.Path) -> dict[str, str]:
    out = {}
    pin_file = root / "code_pin.yml"
    if pin_file.exists():
        m = re.search(r"^sha:\s*([0-9a-f]{40})", pin_file.read_text(), re.M)
        if m:
            out["snapy"] = m.group(1)
    extra = root / "tools" / "package-pins.json"
    if extra.exists():
        out.update(json.loads(extra.read_text()))
    return out


def offpin_hits(text: str, pin: dict[str, str]) -> list[str]:
    """Shas of a cited package other than its pin, in body text, footnotes and links (not PROVENANCE)."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    hits = []
    for rx in _SHA_PATTERNS:
        for m in rx.finditer(text):
            pkg, sha = m.group(1), m.group(2)
            want = pin.get(pkg)
            if want is None or not want.startswith(sha):
                hits.append(f"{pkg}@{sha}")
    return hits


def content_hash(text: str) -> str:
    """sha256 of the file without its PROVENANCE comment, so status and reviewer edits keep the hash."""
    text = re.sub(r"<!--\s*PROVENANCE.*?-->", "", text, count=1, flags=re.S)
    return hashlib.sha256(text.encode()).hexdigest()


def _provenance(text: str) -> dict[str, str]:
    m = re.search(r"<!--\s*PROVENANCE(.*?)-->", text, re.S)
    fields = {}
    if m:
        for line in m.group(1).split("\n"):
            k = re.match(r"\s*(status|author|reviewer):\s*(.*)", line)
            if k:
                fields[k.group(1)] = k.group(2).strip()
    return fields


def read_record(root: pathlib.Path) -> dict[str, list[dict[str, str]]]:
    path = root / "reviews" / "review-record.tsv"
    entries: dict[str, list[dict[str, str]]] = {}
    if not path.exists():
        return entries
    lines = [l for l in path.read_text().split("\n") if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    for line in lines[1:]:
        row = dict(zip(head, line.split("\t")))
        entries.setdefault(row.get("file", ""), []).append(row)
    return entries


def status_problem(rel: str, text: str, record, pin: str) -> str | None:
    """None if the file's status needs no record or its record is valid, else the reason."""
    prov = _provenance(text)
    status = prov.get("status", "").split(";")[0].strip().lower()
    if status not in ("reviewed", "approved"):
        return None
    rows = record.get(rel, [])
    if not rows:
        return f"status {status} without a review-record entry"
    last = rows[-1]
    if last.get("sha256") != content_hash(text):
        return "content changed since the last record entry (re-review or re-stamp)"
    if last.get("pin") != pin:
        return "record entry names another pin than code_pin.yml"
    author = last.get("author", "")
    reviewer = last.get("reviewer", "")
    if not reviewer or reviewer == author or reviewer == prov.get("author", "") != "":
        return "reviewer missing or the same as the author"
    if last.get("kind") == "restamp":
        reviews = [r for r in rows if r.get("kind") == "review"]
        if not reviews or reviews[-1].get("reviewer") != reviewer:
            return "re-stamp by someone other than the reviewer"
        if not last.get("note", "").strip():
            return "re-stamp without a note"
    elif last.get("kind") != "review":
        return f"unknown record kind {last.get('kind')!r}"
    return None


def xref_counts(book: pathlib.Path) -> tuple[dict[str, int], list[str]]:
    """Per chapter: dangling/unreachable references (render_gate's resolution) and sections uncited from outside."""
    sys.path.insert(0, str(TOOLS))
    import render_gate  # noqa: E402  (the render's own resolution, reused)

    # every reference that resolves nowhere counts, including those render_gate files under its
    # unwritten-chapter and unwritten-scheme gates: the render fails on those too
    used, defined, deep = render_gate._xrefs(book)
    counts: dict[str, int] = {}
    detail = []
    for lab, files in used.items():
        if lab not in defined or lab in deep:
            for f in files:
                counts[chapter_of(f)] = counts.get(chapter_of(f), 0) + 1
                detail.append(f"{f}: @{lab} does not resolve")
    home = {}
    for q in sorted((book / "chapters").rglob("*.qmd")):
        rel = str(q.relative_to(book))
        for lab in re.findall(r"\{#(sec-[\w-]+)\}", q.read_text()):
            home[lab] = chapter_of(rel)
    for lab, ch in sorted(home.items()):
        outside = {chapter_of(f) for f in used.get(lab, ())} - {ch}
        if not outside:
            counts[ch] = counts.get(ch, 0) + 1
            detail.append(f"{ch}: section {lab} is not cited from another chapter")
    return counts, detail


def count(root: pathlib.Path = ROOT, verbose: bool = False) -> dict[str, dict[str, int]]:
    book = root / "book"
    pin = pins(root)
    record = read_record(root)
    table: dict[str, dict[str, int]] = {}

    def add(ch, check, n=1):
        table.setdefault(ch, dict.fromkeys(CHECKS, 0))[check] += n

    for q in sorted((book / "chapters").rglob("*.qmd")):
        rel = str(q.relative_to(book))
        ch = chapter_of(rel)
        text = q.read_text()
        table.setdefault(ch, dict.fromkeys(CHECKS, 0))
        for h in history_hits(text):
            add(ch, "history")
            if verbose:
                print(f"history  {rel}: {h}")
        for h in offpin_hits(text, pin):
            add(ch, "offpin")
            if verbose:
                print(f"offpin   {rel}: {h}")
        why = status_problem(rel, text, record, pin.get("snapy", ""))
        if why:
            add(ch, "status")
            if verbose:
                print(f"status   {rel}: {why}")
    xc, detail = xref_counts(book)
    for ch, n in xc.items():
        add(ch, "xref", n)
    if verbose:
        for d in detail:
            print(f"xref     {d}")
    return dict(sorted(table.items()))


def compare(counts, baseline) -> list[str]:
    problems = []
    for ch in sorted(set(counts) | set(baseline)):
        for check in CHECKS:
            now = counts.get(ch, {}).get(check, 0)
            was = baseline.get(ch, {}).get(check, 0)
            if now > was:
                problems.append(f"{ch} {check}: {was} -> {now}, a rise; fix the new instances")
            elif now < was:
                problems.append(f"{ch} {check}: {was} -> {now}, a fall; lower the baseline in this PR "
                                f"(python3 tools/ratchet_gate.py update)")
    return problems


def print_table(counts) -> None:
    print("| chapter | " + " | ".join(CHECKS) + " |")
    print("|---|" + "---|" * len(CHECKS))
    tot = dict.fromkeys(CHECKS, 0)
    for ch, c in counts.items():
        print(f"| {ch} | " + " | ".join(str(c[k]) for k in CHECKS) + " |")
        for k in CHECKS:
            tot[k] += c[k]
    print("| **total** | " + " | ".join(f"**{tot[k]}**" for k in CHECKS) + " |")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=pathlib.Path, default=ROOT, help="doc/tech-report (default: this tree)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("counts", help="print the per-chapter counts")
    c.add_argument("-v", "--verbose", action="store_true", help="list every instance")
    sub.add_parser("check", help="exit 1 if any count differs from the baseline")
    u = sub.add_parser("update", help="write the counts as the new baseline")
    u.add_argument("--allow-increase", action="store_true", help="only for a pin move; say why in the PR")
    h = sub.add_parser("hash", help="content hash of a chapter file, for the review record")
    h.add_argument("file", type=pathlib.Path)
    a = ap.parse_args(argv)
    base_path = a.root / "tools" / "ratchet-baseline.json"
    if a.cmd == "hash":
        print(content_hash(a.file.read_text()))
        return 0
    counts = count(a.root, verbose=getattr(a, "verbose", False))
    if a.cmd == "counts":
        print_table(counts)
        return 0
    baseline = json.loads(base_path.read_text())["chapters"] if base_path.exists() else {}
    if a.cmd == "update":
        rises = [p for p in compare(counts, baseline) if "a rise" in p]
        if rises and baseline and not a.allow_increase:
            print("ratchet: refusing to raise the baseline:\n  " + "\n  ".join(rises))
            return 1
        base_path.write_text(json.dumps({"chapters": counts}, indent=1, sort_keys=True) + "\n")
        print(f"ratchet: baseline written ({len(counts)} chapters)")
        return 0
    problems = compare(counts, baseline)
    if problems:
        print("ratchet gate: FAIL\n  " + "\n  ".join(problems))
        print("  (python3 tools/ratchet_gate.py counts -v lists every instance)")
        return 1
    tot = {k: sum(c[k] for c in counts.values()) for k in CHECKS}
    print("ratchet gate: pass (" + ", ".join(f"{k} {v}" for k, v in tot.items()) + ", equal to the baseline)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
