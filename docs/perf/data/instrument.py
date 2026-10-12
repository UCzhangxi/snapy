"""Insert SNAP_BEGIN/SNAP_END profiler scopes at given lines.

spec: list of (file, begin_line, end_line, name, begin_expect, end_expect)
BEGIN goes before begin_line, END after end_line. Expect strings are checked
as substrings of those lines so a shifted file fails loudly.
"""
import sys, json, collections

def apply(root, spec):
    byfile = collections.defaultdict(list)
    for f, b, e, name, bx, ex in spec:
        byfile[f].append((b, e, name, bx, ex))
    for f, items in byfile.items():
        path = f"{root}/{f}"
        lines = open(path).read().split("\n")
        ins = collections.defaultdict(lambda: ([], []))  # line -> (before, after)
        for n, (b, e, name, bx, ex) in enumerate(items):
            assert bx in lines[b - 1], (f, b, bx, lines[b - 1])
            assert ex in lines[e - 1], (f, e, ex, lines[e - 1])
            var = f"snap_scope_{name.replace('.', '_')}_{n}"
            ins[b][0].append(f'SNAP_BEGIN({var}, "{name}");')
            ins[e][1].insert(0, f"SNAP_END({var});")
        out = []
        for i, l in enumerate(lines, 1):
            out.extend(ins[i][0] if i in ins else [])
            out.append(l)
            out.extend(ins[i][1] if i in ins else [])
        open(path, "w").write("\n".join(out))
        print("instrumented", path, len(items))

if __name__ == "__main__":
    root = sys.argv[1]
    spec = json.load(open(sys.argv[2]))
    apply(root, spec)
