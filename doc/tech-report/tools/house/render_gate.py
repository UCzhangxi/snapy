#!/usr/bin/env python3
"""G1 render gate that can actually see LuaLaTeX's complaints.

THE PROBLEM THIS EXISTS FOR (ISSUES #9)
---------------------------------------
BOOKCRAFT section 6 defines G1 as a grep over `quarto render`'s **stdout** for
`warn|error|unable|missing character|undefined`. LuaLaTeX does not write most of
those to stdout. It writes them to `book/index.log`, **and quarto deletes that
log on a successful render** -- so for nine waves the gate greped for strings
that could never appear, and passed.

What it could not see, measured on the wave-11 build:

  * **42 `Missing character` warnings.** A missing character is not cosmetic:
    LuaLaTeX DROPS the glyph from the PDF. A tilde or a mu vanishes from a
    printed sentence while the HTML is fine and nothing is reported.
  * **2 multiply-defined labels** (`tbl-whipple-e`, `tbl-pcr-e1`), which make a
    cross-reference resolve to the wrong target.
  * 2034 overfull and 85 underfull boxes, which are typography rather than
    defects, and are reported here only as a count.

THE THIRD BLIND SPOT (ISSUES #10), FOLDED IN 2026-09-02
-------------------------------------------------------
Maths written into a GENERATED TABLE CELL reaches the reader as literal LaTeX,
and a cross-reference in a cell does not resolve -- in the HTML and the PDF
alike. That is invisible to every gate above: the source is well formed, so
`check_math_spans.py` passes; the stdout gate sees nothing; and the log only
notices when a macro happens to be a character-mapping one, which caught 4 of
390. The instrument is a scan of the RENDERED `<th>`/`<td>` contents, which
lives in `reference/check_table_cells.py` and is run from here so that G1 covers
it. **It is folded in rather than left standalone because ISSUES #9's whole
lesson is that a gate nobody runs is a gate that does not exist.**

USAGE
-----
    python reference/render_gate.py book/            # render, then gate
    python reference/render_gate.py book/ --no-render   # gate an existing log
    python reference/render_gate.py book/ --labels-only # cross-chapter labels, no build

⚠️ **Do not run this while another session is rendering the same book.**
`_book/` and `_freeze/` are shared state, which is why chapter writers are
forbidden to run quarto at all. To gate a book another session owns, copy the
book directory elsewhere and run there -- the `_freeze` cache is committed, so
the cells do not re-run and the copy costs a couple of minutes.

⚠️ `-M latex-clean:false` is what keeps `index.log` alive. It is passed on the
command line rather than written into `_quarto.yml` so that this gate needs no
change to a file other sessions own.
"""

import re
import subprocess
import sys
import pathlib

# things that are defects, not taste
FATAL = {
    "missing character": (
        r"Missing character: There is no (.+?) \(U\+([0-9A-F]+)\)",
        "a glyph is being DROPPED from the PDF"),
    "multiply defined": (
        r"LaTeX Warning: Label `([^']+)' multiply defined",
        "a cross-reference resolves to the wrong target"),
    "undefined reference": (
        r"LaTeX Warning: Reference `([^']+)' on page (\d+) undefined",
        "a cross-reference points at nothing"),
    "undefined citation": (
        r"LaTeX Warning: Citation `([^']+)' on page (\d+) undefined",
        "a citation is missing from the bibliography"),
}

# real, but typography rather than correctness: counted, never fatal
NOISE = {
    "overfull hbox": r"Overfull \\hbox",
    "underfull hbox": r"Underfull \\hbox",
    "overfull vbox": r"Overfull \\vbox",
}


def render(book):
    cmd = ["quarto", "render", str(book), "-M", "latex-clean:false"]
    print("$ " + " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


#: Quarto's per-cell progress line, e.g. ``Cell 13/25: 'tbl-p9-errorprop'........Done``.
#: 🔴 **It carries the cell's own LABEL, so a label containing "error", "warn" or
#: "undefined" makes the stdout gate fail on a clean render.** That fired for real on
#: 2026-09-04: ch43's `tbl-p9-errorprop` had always existed but had always been FROZEN, so
#: the line was never printed; clearing ch43's freeze for an unrelated constant fix
#: re-executed the cell and the gate reported ``GATE FAILED: 2 problems`` against a render
#: with nothing wrong in it. A false positive in a gate is not harmless — it is how a gate
#: gets ignored, which is `ISSUES.md` #9's whole lesson running in reverse.
#: ⚠ The exclusion is deliberately narrow: it matches the progress line's exact shape and
#: only up to its terminating ``Done``, so a genuine error printed on any other line — or
#: after a cell fails rather than completing — still reaches the gate.
_CELL_PROGRESS = re.compile(r"^\s*Cell \d+/\d+: '[^']*'\.*Done\s*$")


def gate_stdout(out):
    """The historical check. Necessary, and by itself not sufficient."""
    pat = re.compile(r"warn|error|unable|missing character|undefined", re.I)
    hits = [l for l in out.splitlines()
            if pat.search(l) and "IPKernelApp" not in l
            and not _CELL_PROGRESS.match(l)]
    return hits


def _source_label_counts(book):
    """How many times each label is DEFINED in the .qmd sources.

    Needed to tell a real collision from longtable's own noise: see
    `gate_log`.
    """
    counts = {}
    for q in (book / "chapters").glob("*.qmd"):
        text = q.read_text()
        for lab in re.findall(r"\{#([a-zA-Z][\w-]*)\}", text):
            counts.setdefault(lab, []).append(q.name)
        for lab in re.findall(r"^#\|\s*label:\s*(\S+)", text, re.M):
            counts.setdefault(lab, []).append(q.name)
    return counts


#: The ONLY three crossref categories quarto declares with `kind = "float"`, and therefore
#: the only three that carry a `caption_location`.  Read out of quarto 1.10.18's own
#: `share/filters/main.lua`, not remembered:
#:
#:     awk '/kind = "float"/{f=1} f && /ref_type = "/{print; f=0}' main.lua | sort -u
#:
#: ⚠️ **Quarto registers eleven `ref_type`s** -- cau, fig, imp, lst, nte, prf, rem, sol,
#: tbl, tip, wrn -- **and only these three are floats.**  The other eight are callout and
#: theorem families with no caption location at all, so a CAPTIONED cell labelled `sol-...`
#: crashes exactly as `chk-...` does.  ★ This gate's own first draft listed `sol` as safe
#: and would have passed the wave-16 defect that motivated it; it was caught by reading
#: quarto's source instead of trusting the category list.  Do not widen this tuple without
#: re-running that awk.
FLOAT_PREFIXES = ("fig", "tbl", "lst")


def gate_float_label_prefixes(book):
    """A captioned cell whose label prefix is not a quarto crossref type KILLS THE RENDER.

    Found the hard way in wave 16.  ch46 carried five cells labelled `chk-...` and one
    `sol-...`, each with a real `tbl-cap`/`fig-cap`.  A caption makes the cell a FLOAT, and
    quarto then looks the label's prefix up in `crossref.categories.by_ref_type` to decide
    where to put the caption.  For an unknown prefix that lookup returns nil, and the code
    that is supposed to report the problem does

        error("Invalid caption location for float: " .. obj.identifier ..
              " requested " .. result .. ...)

    with `result` nil -- so it dies concatenating nil *while trying to name the offender*,
    and the render's only output is a Lua stack trace with no filename, no line and no
    identifier in it.  ⚠️ **The three existing label gates are all blind to this**: the
    label is unique, so the collision gate passes; nothing references it, so the dangling
    gate passes; and it is a source-level defect, so the log gate never runs because the
    render never completes.  The book had 1503 clean labels and could not build.

    ⚠️ **An UNcaptioned cell with any label at all is fine** -- quarto only classifies a
    cell as a float when it has a caption -- so this must test the pair, not the label.
    Divs (`::: {#exm-...}`, `{#eq-...}`) are not cells and are not in scope here.
    """
    bad = []
    for q in sorted((book / "chapters").glob("*.qmd")):
        label = None
        for n, line in enumerate(q.read_text().splitlines(), 1):
            m = re.match(r"^#\|\s*label:\s*(\S+)", line)
            if m:
                label = (m.group(1), n)
                continue
            if re.match(r"^#\|\s*(fig-cap|tbl-cap|lst-cap)\s*:", line) and label:
                if label[0].split("-")[0] not in FLOAT_PREFIXES:
                    bad.append((q.name, label[1], label[0]))
                label = None
            elif line.strip() == "```":
                label = None
    if not bad:
        print("\n[float gate] every captioned cell carries a crossref-typed label")
        return 0
    print(f"\n[float gate] {len(bad)} captioned cells whose label prefix is not a quarto"
          " crossref type -- THIS KILLS THE RENDER WITH NO FILENAME IN THE ERROR:")
    for fname, n, lab in bad:
        print(f"   {fname}:{n}  {lab}   (prefix '{lab.split('-')[0]}')")
    return len(bad)


#: The two-letter font-selection commands LaTeX2e deprecated in 1994.  Under a KOMA-Script
#: class -- and this book is `scrbook` -- they are not deprecated but **removed**, and using
#: one is a hard error.
_OLD_FONT_COMMANDS = ("rm", "bf", "it", "sf", "tt", "cal", "sl", "sc", "mit")
_OLD_FONT_RE = re.compile(r"\\(" + "|".join(_OLD_FONT_COMMANDS) + r")(?![a-zA-Z])")
#: A markdown inline-code span, so that quoting the rule does not violate it.
_INLINE_CODE = re.compile(r"`{1,3}[^`]*`{1,3}")

#: A python cell that hands a string to pandoc rather than to matplotlib.  This is the
#: discriminator, and it is a property of the CELL and not of the line: a label is routinely
#: built on one line (``lab = f"... $M_{\\rm J}$"``) and handed to matplotlib on another, so
#: a line-local test misreports four of ch10's five and ch47's one.  A cell that emits
#: markdown is on pandoc's path and is fatal; a cell that does not is a figure, and
#: matplotlib's own mathtext accepts the old commands.
#: ⚠ ``show`` is `classic_papers.tables.show`, this book's DataFrame renderer -- the very
#: route `ISSUES` #10 was filed about.
_MARKDOWN_EMITTER = re.compile(
    r"\bMarkdown\s*\(|to_markdown\s*\(|\bdisplay\s*\(|\bHTML\s*\(|"
    r"\btables\.show\s*\(|(?<![\w.])show\s*\(|to_latex\s*\(|to_html\s*\(")


def gate_old_font_commands(book):
    """A bare ``\\rm`` in maths is FATAL under `scrbook`, and the error names no .qmd.

    🔴 **Measured by three renders on 2026-09-04 (wave 17), because `ISSUES` #21 said this
    rule was FALSE and it is not.**  A minimal document on this book's own PDF settings dies
    with

        Class scrbook Error: undefined old font command `\\rm'.

    at the first inline occurrence, and dies identically when the only occurrence is inside
    a **generated table cell** -- so the "narrower, untested" hypothesis #21 raised is the
    same failure, not `ISSUES` #10's family.

    ⚠️ **But the rule's stated REASON was wrong, and that is what to carry forward.**
    `COMMON.md` said *"LuaLaTeX dies"*.  LuaLaTeX does not: the killer is the **KOMA-Script
    document class**, which removes the old two-letter font commands that plain `book` only
    deprecates.  A sibling book on `article` would read the rule, fail to reproduce it, and
    learn to discount the playbook -- which is exactly the harm #21 was filed about,
    arriving through the other door.

    ⚠️ **And #21's four counter-example chapters are a false positive of the FINDING.**
    ch07 (3), ch10 (6), ch22 (2) and ch26 (9) do contain a bare ``\\rm``, and **all twenty
    occurrences are matplotlib label strings inside python cells** -- ``set_ylabel``,
    ``label=``, ``ax.text`` -- which matplotlib renders with its own mathtext and which
    never reach LaTeX.  Confirmed by a fourth render: a figure whose axis label carries
    ``$\\tau_{\\rm I}$`` builds clean.  The finding was made by grepping ``\\rm`` over whole
    files without excluding code cells.  **The rule stands; the counter-examples were never
    in maths that LaTeX sees.**
    """
    fatal, allowed = [], []
    for q in sorted((book / "chapters").glob("*.qmd")):
        lines = q.read_text().splitlines()
        # Split into cells first: the fatal/safe distinction is a property of the CELL, not
        # of the line.  A label string is often built on one line (`lab = "... $M_{\\rm J}$"`)
        # and handed to matplotlib on another, so a line-local test misreports it.
        blocks, cur, fence = [], [], None
        for n, line in enumerate(lines, 1):
            m = re.match(r"^\s*(`{3,})", line)
            if m and fence is None:
                blocks.append(("prose", cur)); cur = []
                fence = m.group(1); cur = [(n, line)]
            elif m and fence is not None and line.strip() == fence:
                cur.append((n, line)); blocks.append(("cell", cur)); cur = []; fence = None
            else:
                cur.append((n, line))
        blocks.append(("prose" if fence is None else "cell", cur))

        for kind, body in blocks:
            text = "\n".join(l for _, l in body)
            emits_markdown = bool(_MARKDOWN_EMITTER.search(text))
            for n, line in body:
                # An inline-code span is not maths: a chapter documenting this very rule
                # would otherwise fail the gate for quoting it.  Stripped only in PROSE --
                # inside a cell a backtick is a python string delimiter, not markdown.
                probe = _INLINE_CODE.sub("", line) if kind == "prose" else line
                hits = _OLD_FONT_RE.findall(probe)
                if not hits:
                    continue
                if kind == "cell" and not emits_markdown:
                    allowed.append((q.name, n, hits))
                else:
                    fatal.append((q.name, n, hits, line.strip()[:80]))
    if allowed:
        n = sum(len(h) for _, _, h in allowed)
        print(f"\n[font gate] {n} old font commands on {len(allowed)} lines, all inside "
              "figure cells (matplotlib mathtext, never reaches LaTeX -- allowed)")
    if not fatal:
        print("[font gate] no old font command reaches LaTeX")
        return 0
    print(f"\n[font gate] {len(fatal)} old font commands on a path to LaTeX -- EACH ONE"
          " KILLS THE PDF WITH 'undefined old font command' AND NAMES NO .qmd:")
    for fname, n, hits, text in fatal:
        print(f"   {fname}:{n}  {sorted(set(hits))}  {text}")
    return len(fatal)


def gate_cross_chapter_labels(book):
    """A label defined in TWO chapters, checked at SOURCE level and before the render.

    The wave-11/ISSUES-#9 finding: four labels were defined in two chapters each -- one of
    them introduced by wave 11 itself -- because the mandatory cross-chapter diff had only
    ever checked symbols and numbers. **A cross-reference that resolves to the wrong chapter
    is invisible to every test**, produces no warning quarto reports on stdout, and in the
    PDF only shows as a `multiply defined` line inside a log quarto deletes. Checking the
    sources costs milliseconds and needs no build, so it runs first.
    """
    counts = _source_label_counts(book)
    clashes = {lab: files for lab, files in counts.items() if len(set(files)) > 1}
    if not clashes:
        print(f"\n[label gate] {len(counts)} labels, none defined in more than one chapter")
        return 0
    print(f"\n[label gate] {len(clashes)} labels defined in more than one chapter:")
    for lab, files in sorted(clashes.items()):
        print(f"  ✗ {lab}: " + ", ".join(sorted(set(files))))
    print("    a cross-reference to one of these resolves to whichever chapter quarto saw last")
    return len(clashes)


def gate_dangling_refs(book):
    """A `@sec-`/`@eq-`/`@fig-`/`@tbl-` reference with no definition, or one quarto cannot reach.

    The label gate above catches a label defined TWICE. This catches the opposite and equally
    silent failure: a reference to a label that is defined nowhere, or -- the case that
    actually occurred -- defined on a heading DEEPER than quarto's cross-reference depth, so
    the label exists in the source and resolves to nothing in the output. ch40 labelled a
    `####` heading and was the only chapter in the book to do so; every other chapter stops at
    `###`. A dead cross-reference is invisible to every test and reads as a missing number.
    """
    defined = set()
    deep = {}
    for q in (book / "chapters").glob("*.qmd"):
        text = q.read_text()
        defined |= set(re.findall(r"\{#([a-zA-Z][\w-]*)\}", text))
        defined |= set(re.findall(r"^#\|\s*label:\s*(\S+)", text, re.M))
        for lvl, lab in re.findall(r"^(#{4,})\s+.*\{#(sec-[\w-]+)\}", text, re.M):
            deep[lab] = (q.name, len(lvl), "on a level-%d heading, too deep to reference"
                         % len(lvl))
        # 🔴 A `sec-` label on a heading INSIDE a fenced div (`::: {#exm-...}` and friends)
        # is unreachable BY CONSTRUCTION: a heading inside a div is not a document section,
        # so quarto registers no section to point at and `@sec-...` renders as literal text.
        # ch40 hit this, and it survived being "fixed" from #### to ### because the depth was
        # never the real cause. Reference the DIV (`@exm-...`) instead.
        depth = 0
        for line in text.split("\n"):
            s = line.strip()
            if s.startswith(":::"):
                depth += 1 if re.match(r":::+\s*\{", s) else (-1 if set(s) <= {":"} else 0)
                depth = max(depth, 0)
                continue
            if depth:
                m = re.match(r"#{1,6}\s+.*\{#(sec-[\w-]+)\}", s)
                if m:
                    deep[m.group(1)] = (q.name, 0, "on a heading INSIDE a fenced div, which "
                                        "is not a section -- reference the div itself")
    used = {}
    for q in (book / "chapters").glob("*.qmd"):
        # ⚠️ a trailing hyphen belongs to the PROSE, not the label: `@eq-foo--` is
        # `@eq-foo` followed by a markdown en-dash, and a greedy `[\w-]+` invents two
        # dangling references in ch09 that do not exist. The label cannot end in a hyphen.
        for lab in re.findall(r"@((?:sec|eq|fig|tbl|exr|exm|thm)-(?:[\w-]*\w)?)", q.read_text()):
            used.setdefault(lab, set()).add(q.name)
    dangling = {l: f for l, f in used.items() if l not in defined}
    unreachable = {l: v for l, v in deep.items() if l in used}
    if not dangling and not unreachable:
        print(f"\n[xref gate] {len(used)} distinct references, all defined and reachable")
        return 0
    for lab, files in sorted(dangling.items()):
        print(f"  ✗ @{lab}: referenced in {', '.join(sorted(files))} but defined nowhere")
    for lab, (fn, _lvl, why) in sorted(unreachable.items()):
        print(f"  ✗ @{lab}: defined in {fn} {why}")
    return len(dangling) + len(unreachable)


def gate_log(log_path, book):
    if not log_path.exists():
        return None, {}, {}
    text = log_path.read_text(errors="replace")
    fatal = {}
    for name, (pat, why) in FATAL.items():
        found = re.findall(pat, text)

        if name == "multiply defined" and found:
            # ⚠️ longtable writes a caption's \label to the .aux TWICE (it
            # typesets the caption once for the first head and again for
            # continuation heads), so EVERY captioned longtable in the book
            # raises this warning with a single \label in the .tex and a
            # single definition in the source. On the wave-11 build that is
            # 16 of 19 warnings -- pure noise.
            #
            # The real defect is a label defined in more than one PLACE, which
            # makes a cross-reference resolve to the wrong target. Wave 11
            # found three: eq-annulus and eq-scaleheight in both ch22 and
            # ch23, and eq-teq in both ch14 and ch22.
            #
            # A gate that reports the 16 cannot ever come back clean, and a
            # gate that cannot come back clean gets ignored -- which is how
            # this book lost its render gate for nine waves in the first
            # place. So cross-check the source and keep only the real ones.
            src = _source_label_counts(book)
            real = [lab for lab in found if len(set(src.get(lab, []))) > 1]
            noisy = len(found) - len(real)
            if noisy:
                print(f"    ({noisy} 'multiply defined' warnings are "
                      f"longtable's own double-write, not collisions)")
            found = [f"{lab}  (defined in {', '.join(sorted(set(src[lab])))})"
                     for lab in real]

        if found:
            fatal[name] = (found, why)
    noise = {n: len(re.findall(p, text)) for n, p in NOISE.items()}
    return text, fatal, noise


def _gate_table_cells(book):
    """ISSUES #10: rendered table cells carrying unrendered maths or a dead ref."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    try:
        from check_table_cells import scan_path
    except ImportError:
        print("\n[table-cell gate] check_table_cells.py NOT FOUND -- gate is BLIND")
        return 1
    rendered = book / "_book"
    if not rendered.is_dir():
        print(f"\n[table-cell gate] {rendered} not built -- gate is BLIND")
        return 1
    found = scan_path(rendered)
    total = sum(len(v) for v in found.values())
    n_html = len(list(rendered.rglob("*.html")))
    if not total:
        print(f"\n[table-cell gate] {n_html} rendered files, no cell carries "
              "literal $...$ or an unresolved (@ref)")
        return 0
    print(f"\n[table-cell gate] {total} offending cells in {len(found)} of {n_html} files")
    for f, hits in sorted(found.items()):
        print(f"  ✗ {f.name}: {len(hits)}")
        for kind, cell in hits[:3]:
            print(f"       [{kind}] {' '.join(cell.split())[:90]}")
    print("    fix: show(df) from classic_papers.tables, not a bare DataFrame")
    return total



def gate_orphan_caption_blocks(book):
    """A pandoc caption block (``: text {#tbl-x}``) placed after a CODE FENCE binds to
    nothing, and reaches the reader as a literal colon and a literal ``{#tbl-x}``.

    Found in wave 28, in ch51, three times.  The trailing-caption form is valid pandoc
    *after a literal pipe table written in the .qmd*; it is NOT valid after a ```{python}
    cell, because the cell's output is not a table pandoc has parsed.  A code cell takes its
    caption as a cell option -- ``#| label: tbl-x`` plus ``#| tbl-cap: '...'``.

    🔴 **The reason this needs its own gate is that only the REFERENCED ones are visible.**
    Two of ch51's three were caught, and only because ``@tbl-...`` appeared elsewhere in the
    chapter, so quarto emitted "Unable to resolve crossref" and the stdout gate saw it.  The
    third was never referenced, so:

      * the dangling-reference gate passed  -- nothing referenced it;
      * the cross-chapter label gate passed -- the label is unique;
      * the float-prefix gate passed        -- it is not a captioned CELL, so not a float;
      * the table-cell gate passed          -- the stray text is a paragraph, not a cell;
      * the log gate passed                 -- LaTeX is perfectly happy to typeset a colon;
      * the render exited 0.

    The rendered page carried ``: The paper's own Section 5 condensate ranges ... {#tbl-ac-
    ladder}`` in the body text.  ★ **Being referenced is what made the other two visible, and
    that is a property of the rest of the chapter, not of the defect.**

    The rule is deliberately narrow, so it cannot fire on a legitimate pipe-table caption:
    a caption block whose nearest preceding non-blank line is a CLOSING code fence.
    """
    bad = []
    for q in sorted((book / "chapters").glob("*.qmd")):
        lines = q.read_text().splitlines()
        for n, line in enumerate(lines):
            if not re.match(r"^:\s+\S", line):
                continue
            j = n - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            if j >= 0 and lines[j].strip() == "```":
                bad.append((q.name, n + 1, line.strip()[:60]))
    print(f"\n[caption gate] {len(bad)} caption block(s) attached to a code fence")
    for name, n, txt in bad:
        print(f"  \u2717 {name}:{n}  {txt}...")
        print("       a code cell takes '#| label:' + '#| tbl-cap:'; a trailing")
        print("       ': caption {#tbl-x}' after a fence binds to nothing")
    if not bad:
        print("    every caption block follows a table pandoc has parsed")
    return len(bad)


def gate_unbalanced_quotes(book):
    """A paragraph of prose carrying an ODD number of ``"`` marks.

    Found in wave 29, in ch52, by an adversarial reviewer reading the rendered page -- one
    stray opening quote inside a block quotation, which reached the printed page as a
    quotation mark with nothing to close it.

    🔴 **No other gate in this file can see it, and the reason generalises.** Every other gate
    here asks whether a *structure* resolves -- a label, a reference, a float type, a font
    command, a caption's binding.  A stray quotation mark resolves perfectly: pandoc emits a
    curly quote, LaTeX typesets it, the render exits 0, the log is clean.  It is wrong only to
    a reader.  ★ **A defect that is well-formed at every level except meaning needs a gate that
    counts rather than one that parses.**

    The rule is deliberately crude, and the measurement is what makes it usable: run over all
    54 chapter files of a book that had shipped 51 reviewed chapters, it returns **zero**.
    A gate that cannot come back empty on good prose is worse than no gate, because readers
    learn to ignore it -- so the zero is the licence, not the idea.

    ⚠️ Code is excluded before counting, in three forms, because there a quote is syntax and
    not punctuation: fenced blocks, inline code spans, and ``#|`` cell options.  ⚠️ It counts
    the ASCII ``"`` only.  Typographic quotes are already balanced by whoever inserted them
    and an apostrophe would make ``'`` unusable as a parity mark.
    """
    bad = []
    for q in sorted(list((book / "chapters").glob("*.qmd")) + list(book.glob("index.qmd"))):
        t = q.read_text()
        t = re.sub(r"^```.*?^```", "", t, flags=re.S | re.M)   # fenced code
        t = re.sub(r"`[^`\n]*`", "", t)                        # inline code spans
        t = re.sub(r"^\s*#\|.*$", "", t, flags=re.M)           # cell options
        for para in re.split(r"\n\s*\n", t):
            n = para.count('"')
            if n % 2:
                first = next((l for l in para.strip().splitlines() if l.strip()), "")
                bad.append((q.name, n, first.strip()[:70]))
    print(f"\n[quote gate] {len(bad)} paragraph(s) with an odd number of \" marks")
    for name, n, txt in bad:
        print(f"  \u2717 {name}  ({n} quotes)  {txt}...")
        print("       a quotation mark with nothing to close it reaches the printed page;")
        print("       every other gate here passes it, because it is well-formed")
    if not bad:
        print("    every prose paragraph closes the quotations it opens")
    return len(bad)


def gate_maths_span_broken_by_a_bullet(book):
    r"""An inline ``$...$`` span, INSIDE A LIST ITEM, whose continuation line starts with a
    markdown bullet marker.  ⚠️ **Fatal — it kills the render.**

    Added at the W34 close (2026-09-14, `ISSUES` #54), found by ch57 failing its first full
    render after every source gate above had passed.

    **The mechanism, reproduced in isolation before the rule was written.**  Inside a list
    item -- and ``(a)``, ``(b)`` are list items, pandoc renders them with
    ``\def\labelenumi{(\alph{enumi})}`` -- a continuation line beginning ``- `` or ``+ ``
    starts a REAL sibling bullet list.  That ends the paragraph, and with it the open inline
    maths span.  The opening ``$`` never closes, pandoc escapes the lot as text
    (``n\_\{\mathrm{H^0}\}Q\_\{31\}\$``) **but passes ``\mathrm`` through as a control
    sequence**, and LuaLaTeX dies with *"\mathrm allowed only in math mode"*.

    ⛔ **THE LIST-ITEM CONDITION IS THE WHOLE RULE, AND A PATTERN MATCH WITHOUT IT IS WRONG.**
    In ordinary prose a leading ``-``/``+`` is a lazy continuation and pandoc keeps the maths
    span intact.  A first scan for "maths span containing a line that starts with a bullet"
    returned **three** hits across the book -- ch02:39 and ch54:589 as well as ch57 -- and
    **both of the others are in plain prose and have been rendering correctly for dozens of
    waves.**  They were checked against `pandoc -t latex` and left alone.  ★ Had the rule been
    written from the pattern rather than from the mechanism, this gate's first act would have
    been to send someone to "fix" two shipped chapters that are not broken.

    The fix is to reflow so no continuation line of an open span begins with a bullet marker,
    or to promote the equation to a display ``$$...$$``.
    """
    bad = []
    bullet = re.compile(r"^\s{0,7}[-*+]\s")
    item = re.compile(r"^\s{0,7}(?:[-*+]\s|\(?[0-9a-z]{1,3}[.)]\s)")
    for q in sorted(list((book / "chapters").glob("*.qmd")) + list(book.glob("index.qmd"))):
        t = q.read_text()
        t = re.sub(r"^```.*?^```", lambda m: "\n" * m.group(0).count("\n"), t,
                   flags=re.S | re.M)
        t = re.sub(r"`[^`\n]*`", "", t)
        depth, in_item = 0, False
        for i, line in enumerate(t.split("\n"), 1):
            if not line.strip():
                in_item = False
            elif item.match(line) and not depth:
                in_item = True
            if depth and in_item and bullet.match(line):
                bad.append((q.name, i, line.strip()[:70]))
            n = len(re.findall(r"(?<!\\)\$", re.sub(r"\$\$", "", line)))
            depth = (depth + n) % 2
    print(f"\n[maths-span gate] {len(bad)} inline maths span(s) broken by a list bullet")
    for name, i, txt in bad:
        print(f"  \u2717 {name}:{i}  {txt}...")
        print("       inside a list item this line STARTS A BULLET LIST, closing the paragraph")
        print("       and the open $...$ with it -- the render dies on \\mathrm outside maths")
    if not bad:
        print("    no inline maths span is interrupted by a bullet inside a list item")
    return len(bad)


def gate_freeze_is_tracked(book):
    """Every chapter quarto renders must have a TRACKED `_freeze/` cache.

    Added at the W32 close (`ISSUES` #46), after W31 shipped ch54 with its freeze left
    untracked -- so a fresh clone re-executed that chapter on its first render, silently,
    which is the one thing `BOOKCRAFT` §5's freeze exists to prevent.

    🔴 **The reason this needs a gate is the check that MISSES it, and it is the sharpest
    instance of W30's carry-forward the book has produced.** At the moment the defect was
    live, tracked freeze directories numbered **54** and chapters in `_quarto.yml` numbered
    **54**. That does not read like a coincidence -- it reads like the property being
    asserted. It was two errors cancelling: ch54 had no tracked freeze, and `ch01-template`
    has one while not being a chapter. ★ **An aggregate can be correct while its source rows
    are wrong; check rows, not sums.**

    ⛔ **The rule is deliberately ONE-DIRECTIONAL, and the bijection was considered and
    rejected.** A chapter with no tracked freeze is a real defect: it costs every fresh clone
    a re-execution. A freeze with no chapter -- which is what `ch01-template` is -- costs four
    small files and nothing else. Asserting the bijection would fail on a clean book today and
    force either an untracking or a named exception, and a gate that fires on a clean book is
    what `ISSUES` #43 was killed for. **So this gate asserts the implication that has teeth
    and stays silent about the clutter that does not.**

    ⚠️ It asks **git**, not the filesystem: the failure is a file existing on disk and not in
    the index, so a `Path.exists()` check is blind to it by construction. If git is
    unavailable the gate reports that and does not fail -- an unanswerable question is not a
    defect.
    """
    import subprocess
    qmd = re.findall(r"chapters/(\S+)\.qmd", (book / "_quarto.yml").read_text())
    try:
        tracked = subprocess.run(
            ["git", "ls-files", str(book / "_freeze" / "chapters")],
            capture_output=True, text=True, timeout=30, cwd=book.parent)
    except Exception as exc:                                   # pragma: no cover
        print(f"\n[freeze gate] SKIPPED -- could not ask git ({exc})")
        return 0
    if tracked.returncode != 0:
        print(f"\n[freeze gate] SKIPPED -- git returned {tracked.returncode}")
        return 0
    have = {ln.split("/chapters/", 1)[1].split("/", 1)[0]
            for ln in tracked.stdout.splitlines() if "/chapters/" in ln}
    missing = [c for c in qmd if c not in have]
    print(f"\n[freeze gate] {len(qmd)} rendered chapters, "
          f"{len(missing)} with no tracked _freeze/ cache")
    for c in missing:
        print(f"  \u2717 {c}: renders, but its freeze is not in the index")
        print("       a fresh clone re-executes this chapter on its first build, silently")
    if not missing:
        print("    every chapter quarto renders has its computed results committed")
    return len(missing)


def main(argv):
    book = pathlib.Path(argv[0] if argv else "book")
    do_render = "--no-render" not in argv

    if "--labels-only" in argv:
        return 1 if (gate_cross_chapter_labels(book) + gate_dangling_refs(book)
                     + gate_float_label_prefixes(book)
                     + gate_old_font_commands(book)
                     + gate_orphan_caption_blocks(book)
                     + gate_unbalanced_quotes(book)
                     + gate_maths_span_broken_by_a_bullet(book)
                     + gate_freeze_is_tracked(book)) else 0

    label_clashes = (gate_cross_chapter_labels(book) + gate_dangling_refs(book)
                     + gate_float_label_prefixes(book)
                     + gate_old_font_commands(book)
                     + gate_orphan_caption_blocks(book)
                     + gate_unbalanced_quotes(book)
                     + gate_maths_span_broken_by_a_bullet(book)
                     + gate_freeze_is_tracked(book))

    rc, out = (0, "") if not do_render else render(book)
    if rc != 0:
        print(f"\nRENDER FAILED (exit {rc}). Last lines:\n")
        print("\n".join(out.splitlines()[-15:]))
        return 1

    problems = label_clashes

    hits = gate_stdout(out)
    print(f"\n[stdout gate] {len(hits)} matching lines"
          + ("" if hits else "  (this is the check that has always run)"))
    for h in hits[:10]:
        print("   ", h.strip()[:110])
    problems += len(hits)

    log = book / "index.log"
    text, fatal, noise = gate_log(log, book)
    if text is None:
        print(f"\n[log gate] {log} NOT FOUND -- the gate is BLIND.")
        print("   quarto deleted it. Re-run without --no-render so that")
        print("   -M latex-clean:false keeps the log alive.")
        return 1

    print(f"\n[log gate] {log} ({len(text):,} bytes)")
    if not fatal:
        print("    no dropped glyphs, no bad cross-references")
    for name, (found, why) in fatal.items():
        uniq = sorted(set(map(str, found)))
        print(f"  ✗ {name}: {len(found)} ({why})")
        for u in uniq[:8]:
            print(f"       {u}")
        problems += len(found)

    cells = _gate_table_cells(book)
    problems += cells

    print("    typography (not fatal): "
          + ", ".join(f"{n} {c}" for n, c in noise.items() if c))

    print("\n" + ("GATE PASSED" if problems == 0
                  else f"GATE FAILED: {problems} problems"))
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
