"""Chapter 5: every figure function draws and follows the measurable rules of STYLE 6.2 (house width, text of at
least 8 pt, colours from the palette), and the executable check passes."""
import importlib
import importlib.util
import pkgutil
from pathlib import Path

import pytest
from matplotlib import colors as mcolors
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text

import snapy_report.ch05 as ch05
from snapy_report.ch05 import _style as fs

FIGS = sorted(m.name for m in pkgutil.iter_modules(ch05.__path__) if m.name.startswith("fig_"))
ALLOWED = {c.lower() for c in fs.PALETTE}


def hexes(c):
    return [mcolors.to_hex(x, keep_alpha=False).lower() for x in mcolors.to_rgba_array(c) if x[3] > 0]


@pytest.mark.parametrize("name", FIGS)
def test_figure_rules(name):
    fig = importlib.import_module(f"snapy_report.ch05.{name}").make_fig()
    fig.draw_without_rendering()
    assert min(abs(fig.get_size_inches()[0] - w) for w in (fs.SINGLE, fs.DOUBLE)) < 1e-6
    for art in fig.findobj(lambda a: a.get_visible()):
        found = []
        if isinstance(art, Text) and art.get_text().strip():
            assert art.get_fontsize() >= fs.SMALL_PT - 1e-9, art.get_text()
            found = hexes(art.get_color())
        elif isinstance(art, Line2D):
            if art.get_linestyle() not in ("None", "none", "", " "):
                found += hexes(art.get_color())
            if art.get_marker() not in (None, "None", "none", "", " "):
                found += hexes(art.get_markerfacecolor()) + hexes(art.get_markeredgecolor())
        elif isinstance(art, Patch) and art is not fig.patch:
            found = (hexes(art.get_facecolor()) if art.get_fill() else []) + hexes(art.get_edgecolor())
        assert set(found) <= ALLOWED, (name, type(art).__name__, set(found) - ALLOWED)


def test_check_passes():
    path = Path(ch05.__file__).parent / "wbref_check.py"
    spec = importlib.util.spec_from_file_location("wbref_check", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
