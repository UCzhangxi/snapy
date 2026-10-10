"""Supplementary offline anchor/structure checks, NOT the official citation gate.

Usage: python reviews/check_ch01.py --code-repo /path/to/pinned/snapy
Every range is read using git show at the full pinned sha, never working files.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--code-repo', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'reviews/ch01-anchors.json').read_text())
    pin = manifest['pin']
    known = set()
    for key, anchor in manifest['anchors'].items():
        code = subprocess.check_output(['git', '-C', args.code_repo, 'show',
                                        pin+':'+anchor['path']], text=True).splitlines()
        lo, hi = anchor['lo'], anchor['hi']
        assert 1 <= lo <= hi <= len(code), key
        assert anchor['symbol'] in '\n'.join(code[lo-1:hi]), key
        known.add((anchor['path'], str(lo), str(hi)))
    files = sorted((root / 'book').rglob('*.qmd')) + [root / 'reviews/ch01-opening.qmd']
    labels = []
    references = set()
    links = 0
    for file in files:
        text = file.read_text()
        assert text.isascii(), file
        if file.name.startswith('_'):
            headings = re.findall(r'^### (.+)$', text, re.M)
            assert headings == ['Summary','Derivation','Numerical method','Code','Tests','Limits'], file
        labels += re.findall(r'\{#((?:sec|eq|tbl|fig)-[a-z0-9-]+)\}', text)
        labels += re.findall(r'^#\| label: (fig-[a-z0-9-]+)$', text, re.M)
        references |= set(re.findall(r'@((?:sec|eq|tbl|fig)-[a-z0-9-]+)', text))
        for sha,path,lo,hi in re.findall(r'https://github.com/chengcli/snapy/blob/([0-9a-f]+)/([^#)]+)#L(\d+)-L(\d+)',text):
            assert sha == pin, (file,sha)
            assert (path,lo,hi) in known, (file,path,lo,hi)
            links += 1
    assert len(labels) == len(set(labels)), 'duplicate label'
    missing = references - set(labels)
    assert missing <= {'sec-ch12-matrix'}, missing
    print(f'PASS: {len(manifest["anchors"])} pinned file/range/anchor records; {links} code links; {len(files)} QMD files')
    print(f'PASS: six layers, ASCII and {len(labels)} unique labels')
    print('PENDING external reference: '+', '.join(sorted(missing)))
    print('Official citation checker and Quarto render gate: NOT RUN by this script')


if __name__ == '__main__':
    main()
