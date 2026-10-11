#!/usr/bin/env python3
"""Generate Appendix B, the derivation index, from the chapter sources (OUTLINE ch17, STYLE.md 2 and 7).

The index is read from the book itself, so it cannot drift from the chapters. Every scheme file
(`book/chapters/NN-slug/_<scheme>.qmd`, or a chapter file with its own `## ... {#sec-...}` schemes) is
scanned for its Derivation layer (STYLE 2). Each labelled equation `{#eq-...}` in that layer is one row:

  * the scheme (`@sec-...`) and the equation (`@eq-...`), as cross-references;
  * the derivation: the sentence that leads into the equation, or the statement given for it in
    `tools/derivation-statements.json` (equation label -> one line), which wins when present;
  * the code: the code site the chapter tags the equation with (STYLE 2: "each numbered equation that the
    code implements is tagged with the code site that implements it"): the first code link after the
    equation in the layer, else the first one before it, given as its anchor symbol (the one the citation
    checker reads) and its `file:lines` text. The link itself stays in the chapter, which owns the citation;
    the index repeats no URL, so a citation is checked once, where it is made;
  * the check: the executable check scripts the scheme file names (`<scheme>_check.py`, STYLE 7) that exist
    under `src/snapy_report/chNN/`, and the check lines (`[Cn]`) the layer quotes next to the equation;
  * the source: "exists" when the layer cites a derivation note (`docs/derivations/` or `sources/`), else
    "re-derived".

A scheme whose Derivation layer labels no equation gets one row with its first sentence (often "None: ..."),
so every written scheme appears once at least, as OUTLINE asks (one row per scheme). Appendix files and the
generated fragment itself are not scanned.

book/_quarto.yml runs this script as its pre-render step, so every render (local or CI) writes the fragment
from the chapters as they are. The fragment is also committed, because Quarto reads every chapter's includes
before the pre-render step runs; tools/tests fails when the committed copy differs from a fresh generation. The
script needs only the Python standard library, and finishes in well under a second.

    python3 tools/gen_derivation_index.py           # rewrite the fragment (what the pre-render step runs)
    python3 tools/gen_derivation_index.py --check   # exit 1 if the fragment is not what the sources give
    python3 tools/gen_derivation_index.py --stats   # counts per chapter, to stdout
    python3 tools/gen_derivation_index.py --book <dir> --fragment <file>   # another tree (e.g. a draft branch)

Exit status 0 on success, 1 if `--check` finds a difference, 2 for an input error.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_citations import find_anchor  # noqa: E402  (the same anchor rule the checker applies)

REPORT = Path(__file__).resolve().parent.parent
BOOK = REPORT / "book"
FRAGMENT = BOOK / "chapters" / "17-appendices" / "_appb-derivation-index.qmd"
STATEMENTS = REPORT / "tools" / "derivation-statements.json"
CHECKS = REPORT / "src" / "snapy_report"

_SCHEME = re.compile(r"^## (?P<title>.*?)\s*\{#(?P<label>sec-[\w-]+)[^}]*\}\s*$")
_CHAPTER = re.compile(r"^# (?P<title>.*?)\s*\{#(?P<label>sec-ch\d+[a-z]?)\}\s*$")
_EQ = re.compile(r"\{#(eq-[\w-]+)\}")
_CODE = re.compile(r"\[`?[^\]\n]*`?\]\((https://github\.com/(?:chengcli|UCzhangxi)/\w+/blob/[0-9a-f]{40}/[^)\s]+)\)")
_CHECK = re.compile(r"\b([\w-]+_check\.py)\b")
_CLINE = re.compile(r"\[C\d+\]")
_NOTE = re.compile(r"docs/derivations/|(?<![\w/])sources/")
#: chapters that are not schemes: the verification catalogue restates the other chapters' checks
EXCLUDE = {"sec-ch15"}
_INCLUDE = re.compile(r"\{\{<\s*include\s+(\S+)\s*>\}\}")


@dataclass
class Row:
    chapter: str          # sec-chNN
    scheme: str           # sec-chNN-x
    title: str
    equation: str | None  # eq-... or None
    statement: str
    code: str             # markdown cell text
    check: str
    source: str
    given: bool = False   # the statement comes from tools/derivation-statements.json


@dataclass
class Scheme:
    chapter: str
    label: str
    title: str
    path: Path
    lines: list[str] = field(default_factory=list)   # the whole file, for anchors
    start: int = 0        # first line of the Derivation layer (0-based, after the heading)
    end: int = 0          # one past its last line


def _clean(text: str) -> str:
    """One table-cell line: links reduced to their text, whitespace joined, `|` escaped (inside math too)."""
    text = re.sub(r"\[([^\]\n]*)\]\([^)\n]*\)", r"\1", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = " ".join(text.split())
    out, math = [], False
    for part in re.split(r"(\$)", text):
        if part == "$":
            math = not math
            out.append(part)
        else:
            out.append(part.replace("|", r"\vert " if math else r"\|"))
    return "".join(out).strip()


def _sentences(text: str) -> list[str]:
    """Split prose into sentences at . ? ! followed by a space, not inside $...$ or `...`."""
    out, cur, math, tick = [], [], False, False
    for i, ch in enumerate(text):
        cur.append(ch)
        if ch == "$":
            math = not math
        elif ch == "`":
            tick = not tick
        elif ch in ".?!" and not math and not tick and (i + 1 == len(text) or text[i + 1] == " "):
            out.append("".join(cur).strip())
            cur = []
    if "".join(cur).strip():
        out.append("".join(cur).strip())
    return out


def scan_file(path: Path, chapter: str) -> list[Scheme]:
    """The schemes of one file with the bounds of their Derivation layers."""
    lines = path.read_text(encoding="utf-8").splitlines()
    schemes, cur, fence = [], None, False
    for n, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
        if fence:
            continue
        m = _SCHEME.match(line)
        if m and "unnumbered" not in line:
            if cur and cur.start and not cur.end:
                cur.end = n
            cur = Scheme(chapter, m["label"], m["title"], path, lines)
            schemes.append(cur)
        elif cur and line.startswith("### "):
            if cur.start and not cur.end:
                cur.end = n
            if line[4:].strip().lower() == "derivation":
                cur.start = n + 1
    if cur and cur.start and not cur.end:
        cur.end = len(lines)
    return [s for s in schemes if s.start]


def _code_cell(s: Scheme, a: int, b: int) -> str | None:
    """The first code link in lines [a, b) of the scheme, as "`symbol`, [text](url)", or None."""
    for n in range(a, b):
        for m in _CODE.finditer(s.lines[n]):
            text = re.match(r"\[`?([^\]`]*)`?\]", s.lines[n][m.start():])
            sym = find_anchor(s.lines, n, m.start())
            where = f"`{text.group(1).strip()}`"
            return f"`{sym}` at {where}" if sym else where
    return None


def scheme_rows(s: Scheme, statements: dict[str, str], checks_dir: Path) -> list[Row]:
    body = "\n".join(s.lines[s.start:s.end])
    whole = "\n".join(s.lines)
    num = re.match(r"sec-ch(\d+)", s.chapter)
    chk_dir = checks_dir / f"ch{num.group(1)}" if num else None
    scripts = sorted({c for c in _CHECK.findall(whole) if chk_dir and (chk_dir / c).exists()})
    source = "exists" if _NOTE.search(body) else "re-derived"
    title = re.sub(r"\s*\(`[^)]*`\)\s*$", "", s.title).strip()

    eq_lines = [(n, e) for n in range(s.start, s.end) for e in _EQ.findall(s.lines[n])]
    rows = []
    if not eq_lines:
        first = _sentences(_clean("\n".join(l for l in s.lines[s.start:s.end]
                                             if not l.lstrip().startswith(("#", ":::", "|", "```")))))
        stmt = first[0] if first else "Empty layer."
        rows.append(Row(s.chapter, s.label, title, None, stmt, "", ", ".join(f"`{c}`" for c in scripts) or "none",
                        source if re.search(r"^\s*\$\$", body, re.M) else "n/a"))
        return rows

    bounds = [n for n, _ in eq_lines] + [s.end]
    for k, (n, label) in enumerate(eq_lines):
        # the equation block: back up from its closing `$$ {#eq-...}` line to the opening `$$`
        top = n - 1
        while top > s.start and s.lines[top].strip() != "$$":
            top -= 1
        prev = bounds[k - 1] + 1 if k else s.start
        pre = s.lines[prev:top]
        dollars = [i for i, l in enumerate(pre) if l.strip().startswith("$$")]
        pre = pre[dollars[-1] + 1:] if dollars else pre          # prose after any unlabelled display
        pre = [l for l in pre if not l.lstrip().startswith(("#", ":::", "|", "```"))]
        lead = _sentences(_clean("\n".join(pre)))
        stmt = statements.get(label) or (lead[-1] if lead else "")
        code = _code_cell(s, n + 1, bounds[k + 1]) or _code_cell(s, prev, top) or "not tagged"
        after = "\n".join(s.lines[n + 1:bounds[k + 1]])
        clines = sorted(set(_CLINE.findall(after)), key=lambda c: int(c[2:-1]))
        check = ", ".join([f"`{c}`" for c in scripts] + [f"`{c}`" for c in clines]) or "none"
        rows.append(Row(s.chapter, s.label, title, label, stmt, code, check, source, label in statements))
    return rows


def chapter_files(book: Path) -> list[tuple[str, str, list[Path]]]:
    """(chapter label, chapter title, scheme-bearing files in include order) for every chapter file."""
    out = []
    for q in sorted((book / "chapters").glob("[0-9][0-9]*.qmd")):
        text = q.read_text(encoding="utf-8")
        m = next((_CHAPTER.match(l) for l in text.splitlines() if _CHAPTER.match(l)), None)
        if not m or m["label"] in EXCLUDE:
            continue
        files = [q] + [q.parent / inc for inc in _INCLUDE.findall(text)]
        out.append((m["label"], m["title"], [f for f in files if f.exists()]))
    return out


def collect(book: Path, statements: dict[str, str], checks_dir: Path) -> list[tuple[str, str, list[Row]]]:
    out = []
    for label, title, files in chapter_files(book):
        rows = []
        for f in files:
            for s in scan_file(f, label):
                rows += scheme_rows(s, statements, checks_dir)
        if rows:
            out.append((label, title, rows))
    return out


def fragment(chapters: list[tuple[str, str, list[Row]]]) -> str:
    """The Quarto fragment of Appendix B. Same sources, same bytes."""
    rows = [r for _, _, rs in chapters for r in rs]
    eqs = [r for r in rows if r.equation]
    schemes = {r.scheme for r in rows}
    with_eq = {r.scheme for r in eqs}
    lines = [
        "<!-- GENERATED by tools/gen_derivation_index.py from the chapter sources; do not edit.",
        "     one-line statements: tools/derivation-statements.json; refresh: python3 tools/gen_derivation_index.py -->",
        "",
        f"Every derivation the written chapters carry, read from their Derivation layers: {len(eqs)} labelled "
        f"equations in {len(with_eq)} of the {len(schemes)} written schemes. Each row gives the equation, the "
        "statement it derives, the code site the chapter tags it with, and the executable check that verifies it "
        "(STYLE section 7); the code site is named as the chapter gives it, and the link to it is in the chapter. "
        "\"exists\" means the chapter rewrites a derivation note from snapy's "
        "`docs/derivations/` or the report's `sources/`; \"re-derived\" means it was derived from the code at the "
        "pin. A scheme whose Derivation layer labels no equation has one row with that layer's first sentence.",
        "",
        "| chapter | schemes | with a labelled derivation | labelled equations | exists | re-derived | with a check script |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, _, rs in chapters:
        e = [r for r in rs if r.equation]
        lines.append(f"| @{label} | {len({r.scheme for r in rs})} | {len({r.scheme for r in e})} | {len(e)} "
                     f"| {sum(r.source == 'exists' for r in e)} | {sum(r.source == 're-derived' for r in e)} "
                     f"| {len({r.scheme for r in rs if r.check not in ('none',) and '_check.py' in r.check})} |")
    lines.append(f"| total | {len(schemes)} | {len(with_eq)} | {len(eqs)} | "
                 f"{sum(r.source == 'exists' for r in eqs)} | {sum(r.source == 're-derived' for r in eqs)} | "
                 f"{len({r.scheme for r in rows if '_check.py' in r.check})} |")
    lines += ["", ": Derivations per chapter. {#tbl-appb-summary}", ""]

    for label, title, rs in chapters:
        lines += [f"## {title} (@{label}) {{.unnumbered}}", "",
                  "| scheme | equation | derivation | code | check | source |",
                  # pandoc sizes the PDF columns by the dashes
                  "|" + "|".join("-" * n for n in (15, 9, 31, 20, 17, 8)) + "|"]
        for r in rs:
            eq = f"@{r.equation}" if r.equation else "none"
            lines.append(f"| @{r.scheme} | {eq} | {_clean(r.statement)} | {r.code} | {r.check} | {r.source} |")
        lines += ["", f": Derivations of @{label}. {{#tbl-appb-{label[4:]}}}", ""]
    return "\n".join(lines)


def stats(chapters) -> str:
    out = []
    for label, _, rs in chapters:
        e = [r for r in rs if r.equation]
        out.append(f"{label}: {len({r.scheme for r in rs})} schemes, {len(e)} equations, "
                   f"{sum(r.code == 'not tagged' for r in e)} untagged, {sum(r.check == 'none' for r in rs)} rows without a check, "
                   f"{sum(not r.given for r in e)} equations without a given statement")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="exit 1 if the fragment differs from the sources'")
    mode.add_argument("--stats", action="store_true", help="print counts per chapter")
    ap.add_argument("--book", type=Path, default=BOOK)
    ap.add_argument("--fragment", type=Path, default=None)
    ap.add_argument("--statements", type=Path, default=STATEMENTS)
    args = ap.parse_args(argv)
    frag = args.fragment or args.book / "chapters" / "17-appendices" / "_appb-derivation-index.qmd"
    try:
        statements = json.loads(args.statements.read_text()) if args.statements.exists() else {}
    except ValueError as e:
        print(f"error: {args.statements}: {e}", file=sys.stderr)
        return 2
    chapters = collect(args.book, statements, args.book.parent / "src" / "snapy_report")
    if args.stats:
        print(stats(chapters))
        return 0
    want = fragment(chapters).rstrip("\n") + "\n"
    if args.check:
        have = frag.read_text() if frag.exists() else ""
        if have == want:
            print(f"gen_derivation_index: {frag.name} is current", file=sys.stderr)
            return 0
        print("\n".join(list(difflib.unified_diff(have.splitlines(), want.splitlines(), "committed", "sources",
                                                  lineterm=""))[:60]))
        print(f"gen_derivation_index: {frag} is stale; run python3 tools/gen_derivation_index.py", file=sys.stderr)
        return 1
    frag.parent.mkdir(parents=True, exist_ok=True)
    frag.write_text(want)
    n = sum(1 for _, _, rs in chapters for r in rs if r.equation)
    print(f"gen_derivation_index: wrote {n} equations to {frag}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
