"""Render every boundary figure twice and compare deterministic SVG bytes."""
import argparse
import importlib
import io
from pathlib import Path
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',required=True);args=parser.parse_args()
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    source=Path(__file__).resolve().parents[1]/'src/snapy_report/ch11'
    count=0
    for path in sorted(source.glob('fig_*.py')):
        module=importlib.import_module('snapy_report.ch11.'+path.stem)
        buffers=[]
        for repeat in range(2):
            fig=module.make_fig()
            assert fig.axes and any(ax.texts or ax.lines or ax.patches for ax in fig.axes)
            b=io.BytesIO();fig.savefig(b,format='svg',metadata={'Date':None});buffers.append(b.getvalue())
            if repeat==0:fig.savefig(out/(path.stem+'.png'),dpi=200)
            plt.close(fig)
        assert buffers[0]==buffers[1],path
        (out/(path.stem+'.svg')).write_bytes(buffers[0]);count+=1
    print(f'PASS {count} real figures; {count} byte-identical SVG pairs; PNG previews at 200 dpi')


if __name__=='__main__':main()
