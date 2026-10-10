"""Independent report identities, not a substitute for CTest."""
import importlib.util
from pathlib import Path
import pytest

path=Path(__file__).parents[1]/'snapy_report/ch12/configuration_check.py'
spec=importlib.util.spec_from_file_location('configuration_check',path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

@pytest.mark.parametrize('check',module.CHECKS,ids=lambda f:f.__name__)
def test_identity(check):
    result = check()
    assert 'passed' in result or 'residual 0' in result
