"""The N8 Python runner must execute record checks and propagate their failures."""
import runpy
from pathlib import Path

import pytest


@pytest.mark.parametrize('check,expected', [
    ('assert value == 7; print("check executed")', 0),
    ('assert value == 8, "check failed"', 1),
])
def test_record_check(monkeypatch, tmp_path, check, expected):
    monkeypatch.setenv('SNAP_PIN_BUILD', str(tmp_path))
    runner = runpy.run_path(str(Path(__file__).with_name('test_do_cards_run.py')))
    execute = runner['_execute']
    execute.__globals__['CARDS'] = {'test': {'blocks': [('python', 'value = 7')]}}
    rc, out = execute({'anchor': 'test', 'deck': None,
                       'run': {'kind': 'python', 'check': check}}, tmp_path)
    assert rc == expected
    assert ('check executed' if expected == 0 else 'check failed') in out
