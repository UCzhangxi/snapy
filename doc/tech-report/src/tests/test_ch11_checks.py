"""Check boundary derivations independently of the compiled solver."""
import pytest
from snapy_report.ch11 import boundary_check as checks


@pytest.mark.parametrize('check',[
    checks.check_copies,checks.check_acoustics,checks.check_admissibility,
    checks.check_corners,checks.check_runs,checks.check_closure,checks.check_reference,
],ids=lambda f:f.__name__)
def test_boundary_identity(check):
    assert check()
