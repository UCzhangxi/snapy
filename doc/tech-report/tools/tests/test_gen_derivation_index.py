"""Tests of tools/gen_derivation_index.py, the Appendix B generator.

Run from the report directory: `python3 -m pytest tools/tests`.
"""

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import gen_derivation_index as g  # noqa: E402

PIN = "e894700ff7aee30b52882e5202b16461413780b0"
URL = f"https://github.com/chengcli/snapy/blob/{PIN}/src/eos/ideal_gas.cpp#L67-L118"

SCHEME = f"""## Ideal gas (`type: ideal-gas`) {{#sec-ch02-gas}}

### Summary

Text with $x$.

### Derivation

The state obeys the gas law. Eliminating $T$ gives

$$
p = (\\gamma-1)\\rho e
$$ {{#eq-ch02-gas-p}}

@eq-ch02-gas-p is implemented by `_prim2cons` in [`ideal_gas.cpp:67-118`]({URL}).
`gas_check.py` line `[C2]` verifies it. The note is `docs/derivations/gas.md`.

A second identity, with $|a|$ inside, follows:

$$
c^2 = \\gamma p/\\rho
$$ {{#eq-ch02-gas-c}}

### Numerical method

Not part of the layer: `[C9]` and {{#eq-ch02-not-here}}.

## Dispatch (`type`) {{#sec-ch02-dispatch}}

### Derivation

No derivation: this is dispatch.

### Code
"""

CHAPTER = """# Thermodynamics {#sec-ch02}

{{< include 02-thermo/_gas.qmd >}}
"""


def make_book(tmp_path):
    book = tmp_path / "book"
    (book / "chapters" / "02-thermo").mkdir(parents=True)
    (book / "chapters" / "02-thermodynamics.qmd").write_text(CHAPTER)
    (book / "chapters" / "02-thermo" / "_gas.qmd").write_text(SCHEME)
    (book / "chapters" / "appb-derivations.qmd").write_text("# Derivation index {#sec-appb}\n")
    checks = tmp_path / "src" / "snapy_report" / "ch02"
    checks.mkdir(parents=True)
    (checks / "gas_check.py").write_text("")
    return book


def test_rows_come_from_the_derivation_layer_only(tmp_path):
    book = make_book(tmp_path)
    chapters = g.collect(book, {}, tmp_path / "src" / "snapy_report")
    assert [c[0] for c in chapters] == ["sec-ch02"]          # the appendix file is not scanned
    rows = chapters[0][2]
    assert [(r.scheme, r.equation) for r in rows] == [
        ("sec-ch02-gas", "eq-ch02-gas-p"), ("sec-ch02-gas", "eq-ch02-gas-c"), ("sec-ch02-dispatch", None)]
    p, c, d = rows
    assert p.statement == "Eliminating $T$ gives"
    assert p.code == "`_prim2cons` at `ideal_gas.cpp:67-118`"   # named, not linked again
    assert p.check == "`gas_check.py`, `[C2]`"                # `[C9]` is outside the layer
    assert p.source == "exists"                               # the layer cites docs/derivations/
    # no link after the second equation: the one before it is taken
    assert c.code == p.code
    assert d.statement == "No derivation: this is dispatch." and d.source == "n/a"


def test_statement_file_wins_and_pipes_are_escaped(tmp_path):
    book = make_book(tmp_path)
    rows = g.collect(book, {"eq-ch02-gas-c": "Sound speed $|c|$ of a | gas."},
                     tmp_path / "src" / "snapy_report")[0][2]
    assert rows[1].statement == "Sound speed $|c|$ of a | gas."
    frag = g.fragment(g.collect(book, {"eq-ch02-gas-c": "Sound speed $|c|$ of a | gas."},
                                tmp_path / "src" / "snapy_report"))
    assert r"Sound speed $\vert c\vert $ of a \| gas." in frag
    assert "{#tbl-appb-summary}" in frag and "{#tbl-appb-ch02}" in frag


def test_a_missing_check_script_is_not_listed(tmp_path):
    book = make_book(tmp_path)
    (tmp_path / "src" / "snapy_report" / "ch02" / "gas_check.py").unlink()
    rows = g.collect(book, {}, tmp_path / "src" / "snapy_report")[0][2]
    assert rows[0].check == "`[C2]`"
    assert rows[2].check == "none"


def test_check_mode_flags_a_stale_fragment(tmp_path, capsys):
    book = make_book(tmp_path)
    frag = tmp_path / "frag.qmd"
    args = ["--book", str(book), "--fragment", str(frag), "--statements", str(tmp_path / "none.json")]
    assert g.main(args + ["--check"]) == 1
    assert g.main(args) == 0
    assert g.main(args + ["--check"]) == 0
    frag.write_text(frag.read_text().replace("Eliminating", "Removing"))
    assert g.main(args + ["--check"]) == 1


def test_every_render_regenerates_the_fragment():
    """The pre-render step in book/_quarto.yml runs this generator, and the appendix includes what it writes."""
    import yaml
    book = TOOLS.parent / "book"
    cfg = yaml.safe_load((book / "_quarto.yml").read_text())
    pre = cfg["project"]["pre-render"]
    pre = [pre] if isinstance(pre, str) else pre
    assert any((book / p).resolve() == Path(g.__file__).resolve() for p in pre)
    include = f"{{{{< include {g.FRAGMENT.relative_to(book / 'chapters').as_posix()} >}}}}"
    assert include in (book / "chapters" / "appb-derivations.qmd").read_text()


def test_the_committed_fragment_matches_a_fresh_generation():
    """Quarto needs the fragment in the tree before pre-render runs, so it is committed; it must not drift."""
    assert g.main(["--check"]) == 0, "run python3 tools/gen_derivation_index.py and commit the fragment"
