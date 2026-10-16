"""Discover executable derivation checks through their script entry points."""
from pathlib import Path
import runpy


def test_derivation_checks():
    for path in sorted((Path(__file__).parents[1] / 'snapy_report').glob('ch*/checks/*_check.py')):
        # Scripts may return normally or use SystemExit; neither requires main().
        try:
            runpy.run_path(str(path), run_name='__main__')
        except SystemExit as status:
            assert status.code in (None, 0), path.name
