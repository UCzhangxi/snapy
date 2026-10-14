"""The concept registry: tools/reader-glossary.json, one entry per concept, each with its defining section.

Every entry (acronym, YAML key, symbol) carries `section`, the label of the section that defines it (STYLE,
Reader standards N1 and N4). What counts as a definition is checked in the book's own prose, never in the
generated first-use notes:
  - a symbol is defined by its row in Appendix A, so its section is its group (`sec-appa-<notation_group>`);
  - an acronym is defined where the prose writes it next to its expansion ("equation of state (EOS)",
    "WENO, weighted essentially non-oscillatory");
  - a YAML key is defined by a reference-table row whose first cell names it (`cfl`, `integration/cfl`).
An acronym or key that no section defines that way is marked `"not_defined_here": true`: the glossary says
"not defined here" for it, and its section is the first labelled section that uses it in prose, so the reader
can still reach it (N1). A use under a chapter heading before its first section, or under a `##` heading with
no label, belongs to no section of its own; the seed skips such roll-up places.

The count of entries marked "not defined here" is a ratchet, tools/not-defined-here-baseline.json, set at the
commit that lands the registry: it may not rise, and a fall is recorded with --update. A fall is verified,
because an entry that is not marked must pass the definition check in its section.

usage:
  python3 tools/glossary_registry.py              check the registry and the ratchet (exit 0 when clean)
  python3 tools/glossary_registry.py --seed       rewrite `section` and the mark of every entry from the book
  python3 tools/glossary_registry.py --update     write the current count of marked entries as the baseline
  python3 tools/glossary_registry.py --count      print the count, and the entries whose section is a roll-up
"""
import json
import re
import sys
from pathlib import Path

REPORT = Path(__file__).resolve().parent.parent
REGISTRY = 'tools/reader-glossary.json'
BASELINE = 'tools/not-defined-here-baseline.json'
MARK = 'not_defined_here'
_ANY_HEADING = re.compile(r'^(#{1,6}) (.*?)\s*(\{[^{}]*\})?\s*$')
_LABEL = re.compile(r'#(sec-[A-Za-z0-9_-]+)')
# generated pages that list every concept; they are not where a concept is defined
_GENERATED = ('_apph-glossary.qmd', '_appf-topic-index.qmd', 'apph-glossary.qmd', 'appf-topic-index.qmd')


def _tools():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import gen_notation_index as notation
    import gen_reader_reference as reference
    import gen_topic_index as topics
    return notation, reference, topics


def labels(book):
    """Every section label of the book's sources, with the file, title and level that define it."""
    out = {}
    for q in sorted(Path(book).rglob('*.qmd')):
        rel = q.relative_to(book).as_posix()
        if rel.startswith(('_', '.')):
            continue
        for line in q.read_text(encoding='utf-8').splitlines():
            m = re.match(r'^(#{1,6}) (.*?)\s*\{#(sec-[A-Za-z0-9_-]+)[^}]*\}', line)
            if m:
                out[m[3]] = dict(file=rel, title=m[2].strip(), level=len(m[1]))
    return out


def _heading(line, section):
    """The section after `line` if it is a heading: its label; None under an unlabelled `#`/`##` heading."""
    m = _ANY_HEADING.match(line)
    if not m:
        return False, section
    label = _LABEL.search(m[3] or '')
    if label:
        return True, label[1]
    return True, (None if len(m[1]) <= 2 else section)


def prose_uses(report):
    """For each concept identity (kind, key): the (chapter, section) pairs of its prose uses, in reading order.

    The same tokens and the same exclusions as the first-use notes of tools/gen_reader_reference.py: code
    fences (but YAML keys inside YAML fences count), display maths, headings, comments and generated blocks are
    not prose; chapters 01 to 16 are scanned. `section` is the label of the enclosing labelled heading; it is
    the chapter label before the first section, and None under a `##` heading with no label."""
    notation, reference, topics = _tools()
    entries = reference.glossary_entries(report)
    lookup = {(e['kind'], e['key']): e for e in entries if e['key']}
    token = re.compile(r'\{\{<.*?>\}\}|`[^`\n]+`|(?<!\$)\$[^$\n]+\$(?!\$)|\b[A-Z][A-Z0-9]{1,6}\b')
    uses = {}
    for path in topics.book_order(report / 'book'):
        rel = path.relative_to(report / 'book').as_posix()
        m = re.match(r'chapters/(\d\d)-', rel)
        if not m or int(m[1]) > 16:
            continue
        chapter = 'ch' + m[1]
        raw = path.read_text(encoding='utf-8')
        text = reference._GLOSS_REF.sub('', reference._GLOSS_KEYS.sub('', reference._GLOSS_NOTES.sub('', raw)))
        section = None
        fence = comment = display = generated = yaml_fence = False
        for line in text.splitlines():
            stripped = line.lstrip()
            if not fence:
                is_heading, section = _heading(line, section)
            if '<!-- generated reader-reference:' in line:
                generated = True
            if generated:
                if '<!-- end reader-reference:' in line:
                    generated = False
                continue
            if '<!--' in line:
                comment = True
            if comment:
                if '-->' in line:
                    comment = False
                continue
            if stripped.startswith('```'):
                yaml_fence = not fence and stripped.strip() in ('```yaml', '```yml')
                fence = not fence
                continue
            if fence:
                if yaml_fence:
                    source = line.split(' #', 1)[0]
                    if not source.lstrip().startswith('#'):
                        for key in re.findall(r'(?:^\s*|[{,] *)([\w-]+):', source):
                            if ('key', key) in lookup:
                                uses.setdefault(('key', key), []).append((chapter, section))
                continue
            if stripped.startswith('$$'):
                if line.count('$$') % 2:
                    display = not display
                continue
            if display or stripped.startswith('#'):
                continue
            for word in token.findall(line):
                if word.startswith('{{<'):
                    continue
                if word.startswith('`'):
                    identity = ('key', word[1:-1])
                elif word.startswith('$'):
                    identity = ('symbol', notation._norm(word[1:-1]))
                else:
                    identity = ('acronym', word)
                if identity in lookup:
                    uses.setdefault(identity, []).append((chapter, section))
    return entries, uses


def paragraphs(report):
    """(labels in reading order, {label: [paragraph]}): the prose of every labelled section of the book, with
    code, comments, generated blocks and the generated first-use notes removed. A table row is one paragraph."""
    _, reference, topics = _tools()
    order, paras = [], {}
    for path in topics.book_order(report / 'book'):
        if path.name in _GENERATED:
            continue
        raw = path.read_text(encoding='utf-8')
        text = reference._GLOSS_REF.sub('', reference._GLOSS_KEYS.sub('', reference._GLOSS_NOTES.sub('', raw)))
        section, buf = None, []
        fence = generated = comment = False

        def flush():
            if buf and section:
                paras.setdefault(section, []).append(' '.join(buf))
            buf.clear()

        for line in text.splitlines():
            if not fence:
                is_heading, new = _heading(line, section)
                if is_heading:
                    flush()
                    section = new
                    if new and new not in order:
                        order.append(new)
                    continue
            if line.lstrip().startswith('```'):
                flush()
                fence = not fence
                continue
            if '<!-- generated reader-reference:' in line:
                generated = True
            if generated:
                generated = '<!-- end reader-reference:' not in line
                continue
            if '<!--' in line:
                comment = True
            if comment:
                comment = '-->' not in line
                continue
            if fence:
                continue
            s = line.strip()
            if not s or s.startswith('|') or re.match(r'([-*]|\d+\.)\s', s):
                flush()
            if s:
                buf.append(s)
            if s.startswith('|'):
                flush()
        flush()
    return order, paras


def _norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


def defines(item, paragraph):
    """Whether `paragraph` defines the acronym or key `item` (see the module docstring)."""
    term = item['term']
    if item['kind'] == 'acronym':
        words = _norm(item['meaning'].split(',')[0]).split()[:3]
        if not words:
            return False
        w = r'[^A-Za-z0-9]+'.join(map(re.escape, words))
        a = re.escape(term)
        return bool(re.search(r'\b%s\b[*_]*\s*(,|\(|—|–|:|=)\s*[*_]*%s|%s[^.;()]{0,60}\(\s*[*_]*%s\b' % (a, w, w, a),
                              paragraph, re.I))
    if item['kind'] == 'key' and paragraph.startswith('|'):
        cells = [c.strip() for c in paragraph.strip().strip('|').split('|')]
        first = cells[0].replace('**', '')
        if len(cells) < 2 or not re.fullmatch(r'`[^`]+`(\s*(,|and|or)\s*`[^`]+`)*(\s+(key|keys|in that block))?', first):
            return False
        return any(s == term or s.endswith('/' + term) for s in re.findall(r'`([^`]+)`', first))
    return False


def definitions(report, data=None):
    """{(kind, term): [labels of the sections that define it, in reading order]} for acronyms and keys."""
    if data is None:
        data = json.loads((report / REGISTRY).read_text(encoding='utf-8'))
    order, paras = paragraphs(report)
    out = {}
    for item in data['entries']:
        if item['kind'] != 'symbol':
            out[(item['kind'], item['term'])] = [s for s in order if any(defines(item, p) for p in paras.get(s, []))]
    return out


def _identity(item, notation):
    return (item['kind'], notation.symbol_key(item['term']) if item['kind'] == 'symbol' else item['term'])


def rollup(section, book_labels):
    """Whether a defining section is a roll-up: a chapter or appendix heading rather than a section of its own."""
    return section in book_labels and book_labels[section]['level'] == 1


def seed(report):
    """The seeded section and mark of every entry: (item, section, not_defined_here, rule)."""
    notation, _, _ = _tools()
    data = json.loads((report / REGISTRY).read_text(encoding='utf-8'))
    book_labels = labels(report / 'book')
    _, uses = prose_uses(report)
    defs = definitions(report, data)
    out = []
    for item in data['entries']:
        if item['kind'] == 'symbol':
            out.append((item, f"sec-appa-{item['notation_group']}", False, 'Appendix A group'))
            continue
        found = defs[(item['kind'], item['term'])]
        own = [s for s in found if not rollup(s, book_labels)]
        if found:
            out.append((item, (own or found)[0], False, 'defined in prose' if item['kind'] == 'acronym'
                        else 'defined in a reference table'))
            continue
        used = [s for _, s in uses.get(_identity(item, notation), []) if s]
        own = [s for s in used if not rollup(s, book_labels)]
        out.append((item, (own or used or ['sec-apph'])[0], True, 'first prose use' if used else 'no prose use'))
    return data, out


def registry_problems(report, data=None):
    """Every entry has a `section` that resolves. A symbol's is its Appendix A group. An acronym or key not
    marked "not defined here" is defined in its section; a marked one is used in its section's prose (when any
    chapter uses it)."""
    notation, _, _ = _tools()
    if data is None:
        data = json.loads((report / REGISTRY).read_text(encoding='utf-8'))
    book_labels = labels(report / 'book')
    _, uses = prose_uses(report)
    defs = definitions(report, data)
    problems = []
    for item in data['entries']:
        term, section, name = item['term'], item.get('section'), f'{item["kind"]} {item["term"]}'
        if not isinstance(section, str) or not section:
            problems.append(f'{name}: no defining section')
        elif section not in book_labels:
            problems.append(f'{name}: defining section {section} is not a label of the book')
        elif item['kind'] == 'symbol':
            if section != f"sec-appa-{item['notation_group']}":
                problems.append(f'symbol {term}: defined by Appendix A group {item["notation_group"]}, not {section}')
        elif not isinstance(item.get(MARK, False), bool):
            problems.append(f'{name}: {MARK} must be true or false')
        elif not item.get(MARK):
            if section not in defs[(item['kind'], term)]:
                problems.append(f'{name}: section {section} does not define it; give the section that does, or '
                                f'mark it "{MARK}": true')
        else:
            used = {s for _, s in uses.get(_identity(item, notation), [])}
            if used and section not in used:
                problems.append(f'{name}: not defined here, and section {section} does not use it in prose')
    return problems


def marked(data):
    return sum(1 for item in data['entries'] if item.get(MARK))


def ratchet_problems(report, data=None, baseline=None):
    """The count of entries marked "not defined here" against its baseline: no rise, and a fall is recorded."""
    path = Path(baseline) if baseline else report / BASELINE
    if not path.exists():
        return [f'{BASELINE} is missing; write it with python3 tools/glossary_registry.py --update']
    if data is None:
        data = json.loads((report / REGISTRY).read_text(encoding='utf-8'))
    base, have = json.loads(path.read_text(encoding='utf-8'))[MARK], marked(data)
    if have > base:
        return [f'{have} entries marked "not defined here", baseline {base}: define the new concepts instead']
    if have < base:
        return [f'{have} entries marked "not defined here", baseline {base}; record the verified fall with '
                'python3 tools/glossary_registry.py --update']
    return []


def check(report=REPORT):
    try:
        problems = registry_problems(Path(report)) + ratchet_problems(Path(report))
    except (OSError, ValueError, KeyError) as exc:
        problems = [str(exc)]
    print(f'[N4 concept registry] {len(problems)} problem(s)')
    for p in problems:
        print('  ' + p)
    return int(bool(problems))


def main(argv):
    report = REPORT
    if '--seed' in argv:
        data, seeded = seed(report)
        rules = {}
        for item, section, mark, rule in seeded:
            item['section'] = section
            if item['kind'] == 'symbol':
                item.pop(MARK, None)
            else:
                item[MARK] = mark
            rules[rule] = rules.get(rule, 0) + 1
        (report / REGISTRY).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'seeded {len(seeded)} entries: {rules}; {marked(data)} marked "not defined here"')
        return 0
    data = json.loads((report / REGISTRY).read_text(encoding='utf-8'))
    if '--update' in argv:
        (report / BASELINE).write_text(json.dumps({MARK: marked(data)}, indent=1) + '\n', encoding='utf-8')
        print(f'baseline written: {marked(data)} entries marked "not defined here"')
        return 0
    if '--count' in argv:
        book_labels = labels(report / 'book')
        print(f'{marked(data)} of {len(data["entries"])} entries marked "not defined here"')
        for item in data['entries']:
            if rollup(item.get('section'), book_labels):
                print(f'  roll-up: {item["kind"]} {item["term"]} -> {item["section"]}')
        return 0
    return check(report)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
