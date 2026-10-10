"""Run the chapter 10 derivation checks and ensure their committed evidence is current."""
from pathlib import Path
import subprocess
import sys
import pytest

CHECKS = sorted((Path(__file__).parents[1] / 'snapy_report/ch10').glob('*_check.py'))


@pytest.mark.parametrize('script', CHECKS, ids=lambda p: p.stem)
def test_ch10_derivation(script):
    result = subprocess.run([sys.executable, str(script)], text=True, capture_output=True, check=True)
    assert result.stdout == script.with_suffix('.out').read_text()
