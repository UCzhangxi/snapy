"""Run chapter derivations and ensure their committed evidence is current."""
from pathlib import Path
import subprocess
import sys
import pytest

CHECKS = sorted((Path(__file__).parents[1] / 'snapy_report/ch02').glob('*_check.py'))


@pytest.mark.parametrize('script', CHECKS, ids=lambda p: p.stem)
def test_ch02_derivation(script, tmp_path):
    result = subprocess.run([sys.executable, str(script)], text=True, capture_output=True, check=True)
    assert result.stdout == script.with_suffix('.out').read_text()

    # Isolated dynamic loading: neither cwd nor the script directory is on sys.path.
    loader = "import runpy, sys; namespace = runpy.run_path(sys.argv[1]); raise SystemExit(namespace['main']())"
    loaded = subprocess.run([sys.executable, '-I', '-c', loader, str(script.resolve())],
                            cwd=tmp_path, text=True, capture_output=True, check=True)
    assert loaded.stdout == result.stdout
