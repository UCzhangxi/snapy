"""Static check of the runnable cards (N8): tools/do-cards.yaml against the chapter sources.

A card is the Code layer's "**A minimal input**" or "**Construction fragment.**" paragraph, with its fenced blocks. The data file holds
one record per card (section anchor, deck, class, trim, time, expected outcome); the card text stays in the chapter.

The check fails when
  - the sources and the data file disagree on the card set (a card with no record, a record with no card, a record
    whose chapter is not the card's chapter, two records for one anchor);
  - a runnable record names no deck (only `not runnable` may have none);
  - a deck does not resolve to a file of the repository;
  - a class or an expected outcome is not one of the allowed values;
  - a `needs-build-option` card does not name its build option as {"name": <CMake option>, "value": "ON"|"OFF"}, the
    name is not an `option()` of the repository's CMake files, or another class names a build option;
  - an exception is stale: it names a card that no longer fails, or a card that does not exist.

A `needs-build-option` card runs only in a build configured with that option: tools/tests/test_do_cards_run.py reads the
build's CMakeCache.txt and skips the card with the reason (`missing_build_option`) when the option is off or unset,
and runs it as a CPU card when it is set.

Named exceptions (`exceptions:` in the data file) are ratchet-style: each lets exactly one card fail the deck check,
and the check fails again once the card is fixed until the exception is removed.

The data file is YAML restricted to one JSON-style flow mapping per list item (`  - {"id": ...}`), so that this
check needs no YAML library: the render job installs none, and `load` below reads exactly that layout.

usage: python3 tools/check_do_cards.py [report_dir]      (exit 0 when clean)
"""
import json
import re
import sys
from pathlib import Path

CLASSES = ("CPU-seconds", "CPU-minutes+", "needs-build-option", "multi-rank", "GPU", "not runnable")
NEEDS = "needs-build-option"
_OPTION = re.compile(r"^\s*option\(\s*([A-Za-z0-9_]+)", re.M)
CARD_LEAD = ("**A minimal input", "**Construction fragment.")
_INCLUDE = re.compile(r"\{\{< include (\S+) >\}\}")
_ANCHOR = re.compile(r"^#{1,2} .*\{#(sec-[A-Za-z0-9_-]+)")


def _chapters(book):
    """Chapter and appendix files in _quarto.yml order."""
    out = []
    for line in (book / "_quarto.yml").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s+- (chapters/\S+\.qmd)\s*$", line)
        if m:
            out.append(m.group(1))
    return out


def _expand(book, path, root=None):
    """The lines of a chapter with its includes expanded: (file, line number, text)."""
    root = root or path.rsplit("/", 1)[0]
    out = []
    for n, text in enumerate((book / path).read_text(encoding="utf-8").splitlines(), 1):
        m = _INCLUDE.match(text.strip())
        if m:
            cands = [path.rsplit("/", 1)[0] + "/" + m.group(1), root + "/" + m.group(1)]
            sub = next((c for c in cands if (book / c).exists()), None)
            if sub:
                out += _expand(book, sub, root)
            continue
        out.append((path, n, text))
    return out


_FENCE = re.compile(r"```+\s*\{?\.?(\w*)[^\n]*\n(.*?)```", re.S)


def source_cards(book):
    """Every card in book order: dict(anchor, chapter, file, line, blocks), where blocks are the (language, code) of
    the card's fenced blocks, up to the next heading or bold-lead paragraph."""
    cards = []
    for ch in _chapters(book):
        anchor = None
        lines = _expand(book, ch)
        for k, (f, n, text) in enumerate(lines):
            m = _ANCHOR.match(text)
            if m:
                anchor = m.group(1)
            if text.startswith(CARD_LEAD):
                body, fenced = [text], False
                for _, _, t in lines[k + 1:]:
                    if t.lstrip().startswith("```"):
                        fenced = not fenced
                    elif not fenced and (t.startswith("#") or re.match(r"^\*\*[A-Z][^*]+\.\*\*", t)):
                        break
                    body.append(t)
                cards.append(dict(anchor=anchor, chapter=Path(ch).stem, file=f, line=n,
                                  blocks=_FENCE.findall("\n".join(body))))
    return cards


LISTS = ("cards", "exceptions", "validation_log")


def load(text):
    """Read do-cards.yaml: top-level keys from LISTS, each a list of one-line flow mappings (or `[]`)."""
    data = {k: [] for k in LISTS}
    top = None
    for n, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith(" "):
            key, _, rest = raw.partition(":")
            if key not in LISTS or rest.strip() not in ("", "[]"):
                raise ValueError(f"line {n}: unknown top-level line {raw!r}")
            top = key
        elif raw.startswith("  - {") and top:
            try:
                data[top].append(json.loads(raw[4:]))
            except json.JSONDecodeError as e:
                raise ValueError(f"line {n}: not a one-line JSON-style mapping: {e}") from None
        else:
            raise ValueError(f"line {n}: expected '  - {{...}}' under {top}")
    return data


def cmake_options(repo):
    """The names of every `option()` of the repository's top-level CMakeLists.txt and cmake/*.cmake."""
    repo = Path(repo)
    files = [repo / "CMakeLists.txt", *sorted((repo / "cmake").glob("*.cmake"))]
    return {m for f in files if f.is_file() for m in _OPTION.findall(f.read_text(encoding="utf-8"))}


def missing_build_option(rec, cache):
    """Why a needs-build-option card cannot run in the build whose CMakeCache.txt text is `cache`; None when it can
    (or when the card needs no option)."""
    if rec.get("class") != NEEDS:
        return None
    name, value = rec["build_option"]["name"], rec["build_option"]["value"]
    m = re.search(rf"^{re.escape(name)}:[A-Z]+=(.*)$", cache, re.M)
    if m is None:
        have = f"does not set {name}"
    elif m.group(1).strip().upper() == value:
        return None
    else:
        have = f"has {name}={m.group(1).strip()}"
    return f"{rec['id']} needs build option {name}={value}; this build {have} (CMakeCache.txt)"


def check(report, data=None):
    """Return (status, messages); status 0 means clean."""
    report = Path(report).resolve()
    book = report / "book"
    repo = report.parent.parent
    data = Path(data) if data else report / "tools" / "do-cards.yaml"
    doc = load(data.read_text(encoding="utf-8"))
    recs = doc.get("cards") or []
    exc = {e["id"]: e for e in (doc.get("exceptions") or [])}
    msgs = []

    src = source_cards(book)
    by_anchor = {}
    for c in src:
        if c["anchor"] in by_anchor:
            msgs.append(f"two cards under one anchor {c['anchor']} ({c['file']}:{c['line']})")
        by_anchor[c["anchor"]] = c
    seen = set()
    for r in recs:
        a = r.get("anchor")
        if a in seen:
            msgs.append(f"{r.get('id')}: a second record for {a}")
        seen.add(a)
        if a not in by_anchor:
            msgs.append(f"{r.get('id')}: record for {a}, but no card under that anchor in the sources")
        elif r.get("chapter") != by_anchor[a]["chapter"]:
            msgs.append(f"{r.get('id')}: chapter {r.get('chapter')} but the card is in {by_anchor[a]['chapter']}")
    for a, c in by_anchor.items():
        if a not in seen:
            msgs.append(f"card under {a} ({c['file']}:{c['line']}) has no record in {data.name}")

    ids = {r.get("id") for r in recs}
    options = cmake_options(repo)
    for r in recs:
        rid, cls, deck = r.get("id"), r.get("class"), r.get("deck")
        if cls not in CLASSES:
            msgs.append(f"{rid}: class {cls!r} is not one of {', '.join(CLASSES)}")
        bo = r.get("build_option")
        if cls == NEEDS:
            if not (isinstance(bo, dict) and bo.get("name") and bo.get("value")):
                msgs.append(f'{rid}: class {NEEDS} needs build_option {{"name": <CMake option>, "value": "ON"|"OFF"}}')
            else:
                if bo["name"] not in options:
                    msgs.append(f"{rid}: build_option {bo['name']} is not an option() of the repository's CMake files")
                if bo["value"] not in ("ON", "OFF"):
                    msgs.append(f"{rid}: build_option value {bo['value']!r} is not ON or OFF")
        elif bo is not None:
            msgs.append(f"{rid}: build_option is only for class {NEEDS}, not {cls}")
        exp = r.get("expect")
        if not (exp in ("exit 0", "nothing to run") or (isinstance(exp, str) and exp.startswith("refused: "))):
            msgs.append(f"{rid}: expect {exp!r} is not 'exit 0', 'nothing to run' or 'refused: <message>'")
        problem = None
        if cls != "not runnable" and not deck:
            problem = "names no deck"
        elif deck and not (repo / deck).is_file():
            problem = f"deck {deck} does not resolve in the repository"
        if problem and rid in exc:
            continue
        if problem:
            msgs.append(f"{rid}: {problem}")
        elif rid in exc:
            msgs.append(f"{rid}: stale exception: the card now passes, remove it from exceptions")
    for e in exc:
        if e not in ids:
            msgs.append(f"exception {e} names no record")
    return (1 if msgs else 0), msgs


def main(argv):
    report = Path(argv[0]) if argv else Path(__file__).resolve().parent.parent
    status, msgs = check(report)
    doc = load((report / "tools" / "do-cards.yaml").read_text(encoding="utf-8"))
    n = len(doc.get("cards") or [])
    print(f"[do-cards] {n} records, {len(source_cards(report / 'book'))} cards in the sources, "
          f"{len(doc.get('exceptions') or [])} named exception(s)")
    for m in msgs:
        print(f"  ✗ {m}")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
