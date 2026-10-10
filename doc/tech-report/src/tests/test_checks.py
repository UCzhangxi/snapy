"""Discover the report's executable derivation checks."""
import importlib.util
from pathlib import Path


def test_derivation_checks():
    for path in sorted((Path(__file__).parents[1] / 'snapy_report').glob('ch*/*_check.py')):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.main() == 0, path.name
