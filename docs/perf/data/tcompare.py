import re,sys
def load(p):
    d={}
    for l in open(p):
        m=re.match(r"TIME (\S+) incl_ms=([\d.e+-]+) excl_ms=([\d.e+-]+)",l)
        if m: d[m.group(1)]=(float(m.group(2)),float(m.group(3)))
    return d
o=load(sys.argv[1]); n=load(sys.argv[2])
keys=sorted(set(o)|set(n), key=lambda k:-(n.get(k,(0,0))[1]-o.get(k,(0,0))[1]))
print(f"{'scope (exclusive ms/step, 1 thread)':50s} {'v2.10.9':>8s} {'main':>8s} {'delta':>7s}")
for k in keys:
    a=o.get(k,(0,0))[1]; b=n.get(k,(0,0))[1]
    if abs(b-a)<0.05 and max(a,b)<0.5: continue
    print(f"{k:50s} {a:8.2f} {b:8.2f} {b-a:+7.2f}")
print(f"{'TOTAL (sum of exclusive)':50s} {sum(v[1] for v in o.values()):8.2f} {sum(v[1] for v in n.values()):8.2f}")
