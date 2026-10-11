"""Chapter 6: every figure function draws at a house width with text of at least 8 pt and colours from the
palette (STYLE 6.2), and every executable check passes and reproduces its committed output."""
import importlib
import pkgutil
import subprocess
import sys
from pathlib import Path

import pytest
from matplotlib import colors as mcolors
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text

import snapy_report.ch06 as ch06
from snapy_report import figstyle as fs

FIGS = sorted(m.name for m in pkgutil.iter_modules(ch06.__path__) if m.name.startswith("fig_"))
CHECKS = sorted(Path(ch06.__file__).parent.glob("*_check.py"))
ALLOWED = {c.lower() for c in (fs.BLACK, fs.ORANGE, fs.SKY, fs.GREEN, fs.YELLOW, fs.BLUE, fs.VERMILLION, fs.PURPLE,
                               fs.GREY, "#ffffff", "#eaf5fc", "#f7e6ef")}


def hexes(c):
    return [mcolors.to_hex(x, keep_alpha=False).lower() for x in mcolors.to_rgba_array(c) if x[3] > 0]


@pytest.mark.parametrize("name", FIGS)
def test_figure_rules(name):
    fig = importlib.import_module(f"snapy_report.ch06.{name}").make_fig()
    fig.draw_without_rendering()
    assert min(abs(fig.get_size_inches()[0] - w) for w in (fs.SINGLE, fs.DOUBLE)) < 1e-6
    for art in fig.findobj(lambda a: a.get_visible()):
        found = []
        if isinstance(art, Text) and art.get_text().strip():
            assert art.get_fontsize() >= 8 - 1e-9, art.get_text()
            found = hexes(art.get_color())
        elif isinstance(art, Line2D):
            if art.get_linestyle() not in ("None", "none", "", " "):
                found += hexes(art.get_color())
            if art.get_marker() not in (None, "None", "none", "", " "):
                found += hexes(art.get_markerfacecolor()) + hexes(art.get_markeredgecolor())
        elif isinstance(art, Patch) and art is not fig.patch:
            found = (hexes(art.get_facecolor()) if art.get_fill() else []) + hexes(art.get_edgecolor())
        assert set(found) <= ALLOWED, (name, type(art).__name__, set(found) - ALLOWED)


@pytest.mark.parametrize("script", CHECKS, ids=lambda p: p.stem)
def test_check_current(script):
    out = subprocess.run([sys.executable, str(script)], text=True, capture_output=True, check=True).stdout
    assert out == script.with_suffix(".out").read_text()
