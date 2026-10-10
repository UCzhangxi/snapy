"""Render Chapter 1 cartoons twice to check deterministic SVG output.

Usage: PYTHONPATH=src python reviews/render_ch01_figures.py --output-dir DIR
This is a matplotlib check, not a Quarto render or PDF page review.
"""
import argparse
import importlib
import io
from pathlib import Path
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    modules = sorted((Path(__file__).resolve().parents[1] / 'src/snapy_report/ch01').glob('fig_*.py'))
    for path in modules:
        make_fig = importlib.import_module('snapy_report.ch01.' + path.stem).make_fig
        outputs = []
        for repeat in range(2):
            fig = make_fig()
            output = io.BytesIO()
            fig.savefig(output, format='svg', metadata={'Date': None})
            outputs.append(output.getvalue())
            if repeat == 0:
                fig.savefig(args.output_dir / (path.stem+'.png'), dpi=150)
                fig.savefig(args.output_dir / (path.stem+'.pdf'), metadata={'CreationDate': None})
            plt.close(fig)
        assert outputs[0] == outputs[1], path.name
        (args.output_dir / (path.stem+'.svg')).write_bytes(outputs[0])
    print(f'PASS: {len(modules)} figure functions; identical SVG bytes on two renders; PNG/PDF previews generated')


if __name__ == '__main__':
    main()
