import re, sys, collections
def load(p):
    d = {}
    for l in open(p):
        m = re.match(r"SCOPE (\S+) kernels/step=([\d.]+) MB/step=([\d.e+-]+) syncs/step=([\d.]+)", l)
        if m:
            k = m.group(1)
            a = d.get(k, [0, 0, 0])
            d[k] = [a[0] + float(m.group(2)), a[1] + float(m.group(3)), a[2] + float(m.group(4))]
        m = re.match(r"TOTAL kernels/step=([\d.]+) MB/step=([\d.e+-]+) syncs/step=([\d.]+)", l)
        if m: tot = [float(x) for x in m.groups()]
    return d, tot
def group(d, depth):
    g = collections.defaultdict(lambda: [0, 0, 0])
    for k, v in d.items():
        kk = "/".join(k.split("/")[:depth])
        for i in range(3): g[kk][i] += v[i]
    return g
old, to = load(sys.argv[1]); new, tn = load(sys.argv[2])
depth = int(sys.argv[3]) if len(sys.argv) > 3 else 9
go, gn = group(old, depth), group(new, depth)
keys = sorted(set(go) | set(gn), key=lambda k: -(gn.get(k, [0])[0] - go.get(k, [0])[0]))
print(f"{'scope':55s} {'old k':>7s} {'new k':>7s} {'dk':>6s} {'old MB':>8s} {'new MB':>8s} {'sync o/n':>9s}")
for k in keys:
    o = go.get(k, [0, 0, 0]); n = gn.get(k, [0, 0, 0])
    print(f"{k:55s} {o[0]:7.0f} {n[0]:7.0f} {n[0]-o[0]:+6.0f} {o[1]:8.1f} {n[1]:8.1f} {o[2]:4.0f}/{n[2]:<4.0f}")
print(f"{'TOTAL':55s} {to[0]:7.0f} {tn[0]:7.0f} {tn[0]-to[0]:+6.0f} {to[1]:8.1f} {tn[1]:8.1f} {to[2]:4.0f}/{tn[2]:<4.0f}")
