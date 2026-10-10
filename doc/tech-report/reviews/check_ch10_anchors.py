"""Local chapter citation audit; not the missing official report checker."""
from pathlib import Path
import json,subprocess,argparse
ap=argparse.ArgumentParser()
ap.add_argument('--snapy',required=True)
ap.add_argument('--kintera',required=True)
ap.add_argument('--pyharp',required=True)
a=ap.parse_args()
repos={'snapy':a.snapy,'kintera':a.kintera,'pyharp':a.pyharp}
r=Path(__file__).resolve().parents[1]; aa=json.loads((r/'reviews/ch10-citation-anchors.json').read_text()); seen=set(); errors=[]
for a in aa:
 key=(a['repo'],a['sha'],a['path'],a['lo'],a['hi'],a['symbol'])
 if key in seen: continue
 seen.add(key)
 text=subprocess.check_output(['git','-C',repos[a['repo']],'show',a['sha']+':'+a['path']],text=True).splitlines()
 lines=text[a['lo']-1:a['hi']]
 if len(lines)!=a['hi']-a['lo']+1 or a['symbol'] not in '\n'.join(lines): errors.append(key)

print(f'Local file/range/anchor audit: {len(seen)} unique anchored ranges; {len(errors)} errors')
for e in errors: print(e)
raise SystemExit(bool(errors))
