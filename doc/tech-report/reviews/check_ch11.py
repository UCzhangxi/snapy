"""Supplementary pinned-anchor/structure audit; not the official citation gate."""
import argparse
import json
import re
import subprocess
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--code-repo',required=True)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    manifest=json.loads((root/'reviews/ch11-anchors.json').read_text())
    pin=manifest['pin'];known=set()
    for key,a in manifest['anchors'].items():
        lines=subprocess.check_output(['git','-C',args.code_repo,'show',pin+':'+a['path']],text=True).splitlines()
        assert 1<=a['lo']<=a['hi']<=len(lines),key
        assert a['symbol'] in '\n'.join(lines[a['lo']-1:a['hi']]),key
        known.add((a['path'],str(a['lo']),str(a['hi'])))
    files=sorted((root/'book/chapters/11-boundaries').glob('*.qmd'))+[root/'book/chapters/15-verification/_ch11.qmd']
    all_labels=set()
    for f in (root/'book').rglob('*.qmd'):
        text=f.read_text()
        all_labels.update(re.findall(r'\{#((?:sec|eq|fig|tbl)-[a-z0-9-]+)\}',text))
        all_labels.update(re.findall(r'^#\| label: (fig-[a-z0-9-]+)',text,re.M))
    local_labels=[];references=set();count=0
    for file in files:
        text=file.read_text();assert text.isascii(),file
        if file.name!='_opening.qmd':
            assert re.findall(r'^### (.+)$',text,re.M)==['Summary','Derivation','Numerical method','Code','Tests','Limits'],file
        local_labels+=re.findall(r'\{#((?:sec|eq|fig|tbl)-[a-z0-9-]+)\}',text)
        local_labels+=re.findall(r'^#\| label: (fig-[a-z0-9-]+)',text,re.M)
        references.update(re.findall(r'@((?:sec|eq|fig|tbl)-[a-z0-9-]+)',text))
        for sha,path,lo,hi in re.findall(r'https://github.com/chengcli/snapy/blob/([0-9a-f]+)/([^#)]+)#L(\d+)-L(\d+)',text):
            assert sha==pin and (path,lo,hi) in known,(file,path,lo,hi)
            count+=1
        for path,sha in re.findall(r'(docs/derivations/[^`\s@]+)@([0-9a-f]+)',text):
            assert sha==pin,(file,path,sha)
            subprocess.check_call(['git','-C',args.code_repo,'cat-file','-e',sha+':'+path])
    assert len(local_labels)==len(set(local_labels)),'duplicate local labels'
    assert not references-all_labels,references-all_labels
    equations={x for x in local_labels if x.startswith('eq-')}
    assert equations<=references,'unused equation labels'
    print(f'PASS {len(manifest["anchors"])} pinned anchors; {count} code links; {len(files)} QMD files')
    print(f'PASS six layers; ASCII; {len(local_labels)} unique labels; 0 unresolved references; {len(equations)} used equations')
    print('Official citation gate and Quarto render: not exercised by this supplementary audit')


if __name__=='__main__':
    main()
