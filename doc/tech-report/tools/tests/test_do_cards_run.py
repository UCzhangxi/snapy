"""Runner of the CPU cards (N8): every CPU card of tools/do-cards.yaml, trimmed, against a code-pin build.

Opt-in. The whole module skips unless SNAP_PIN_BUILD names the build directory of a chengcli/snapy source build at
the sha of code_pin.yml (with build/bin and its linked decks), so the ratchet CI step and a machine without a build
never run it. GPU and multi-rank cards are not run here: their evidence is the dated validation_log of the data file.
A needs-build-option card runs like a CPU card when the build's CMakeCache.txt sets its option, and is skipped with the
reason otherwise (check_do_cards.missing_build_option): it never passes without running.

  SNAP_PIN_BUILD=/path/to/snapy/build python3 -m pytest -q tools/tests/test_do_cards_run.py

Optional: SNAP_PIN_PYTHONPATH (prepended to PYTHONPATH for the Python and ctest cards: the build's snapy package and kintera),
SNAP_CARD_TIMEOUT (seconds per card, default 60). Each card runs in its own tmp directory: its first YAML block is
merged into a copy of its deck with the record's trim, the record's driver runs, and the outcome is compared with
`expect` (exit 0, or a refusal with the quoted message). For Python cards, optional
`run.check` code runs after all Python blocks in the same namespace; assertion failures fail the card.
The runner itself checks exit status; a record may additionally assert physical or interface properties.
"""

import copy
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
REPORT = TOOLS.parent
REPO = REPORT.parent.parent
sys.path.insert(0, str(TOOLS))

import check_do_cards as c  # noqa: E402

BUILD = os.environ.get("SNAP_PIN_BUILD")
if not BUILD:
    pytest.skip("opt-in runner: set SNAP_PIN_BUILD to a code-pin build directory", allow_module_level=True)
yaml = pytest.importorskip("yaml")

BUILD = Path(BUILD).resolve()
BIN = BUILD / "bin"
TIMEOUT = float(os.environ.get("SNAP_CARD_TIMEOUT", "60"))
DATA = c.load((TOOLS / "do-cards.yaml").read_text(encoding="utf-8"))
EXCEPTED = {e["id"] for e in DATA["exceptions"]}
CPU = ("CPU-seconds", "CPU-minutes+", c.NEEDS)
CARDS = {x["anchor"]: x for x in c.source_cards(REPORT / "book")}
RECORDS = [r for r in DATA["cards"] if r["class"] in CPU]


def _pin():
    m = re.search(r"^sha:\s*([0-9a-f]{40})", (REPORT / "code_pin.yml").read_text(encoding="utf-8"), re.M)
    return m.group(1)


def test_the_build_is_at_the_code_pin():
    cache = (BUILD / "CMakeCache.txt").read_text(encoding="utf-8")
    src = re.search(r"^CMAKE_HOME_DIRECTORY:INTERNAL=(.+)$", cache, re.M).group(1)
    head = subprocess.run(["git", "-C", src, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert head == _pin(), f"{BUILD} is a build of {head}, not of the code pin {_pin()}"


def _merge(a, b):
    out = copy.deepcopy(a)
    for k, v in b.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def _block(rec, lang):
    return next(code for language, code in CARDS[rec["anchor"]]["blocks"] if language == lang)


def _run(cmd, cwd, env):
    e = dict(os.environ, **{k: str(v) for k, v in env.items()})
    p = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True, timeout=TIMEOUT)
    return p.returncode, p.stdout + p.stderr


def _execute(rec, tmp):
    run, env = rec["run"], dict(rec["run"].get("env") or {})
    kind = run["kind"]
    if kind in ("python", "ctest") and os.environ.get("SNAP_PIN_PYTHONPATH"):
        env["PYTHONPATH"] = os.environ["SNAP_PIN_PYTHONPATH"] + os.pathsep + os.environ.get("PYTHONPATH", "")
    if kind == "python":
        if rec["deck"]:
            (tmp / Path(rec["deck"]).name).write_text((REPO / rec["deck"]).read_text(encoding="utf-8"))
            deck_copy = tmp / rec["deck"]
            deck_copy.parent.mkdir(parents=True, exist_ok=True)
            deck_copy.write_text((REPO / rec["deck"]).read_text(encoding="utf-8"))
        code = "\n".join(code for lang, code in CARDS[rec["anchor"]]["blocks"] if lang == "python")
        (tmp / "card.py").write_text(
            "\n".join((run.get("prelude", ""), code, run.get("check", ""))).strip() + "\n")
        return _run([sys.executable, "card.py"], tmp, env)
    if kind == "ctest":
        return _run(["ctest", "--test-dir", str(BUILD), "-R", run["select"], "--output-on-failure"], tmp, env)
    deck = yaml.safe_load((REPO / rec["deck"]).read_text(encoding="utf-8"))
    if kind in ("merge", "restart"):
        deck = _merge(deck, yaml.safe_load(_block(rec, "yaml")))
    integ = deck.setdefault("integration", {})
    for k, v in (rec["trim"] or {}).items():
        if integ.get(k, -1) in (-1, None):
            integ[k] = v
    (tmp / "deck.yaml").write_text(yaml.safe_dump(deck, sort_keys=False))
    rc, out = _run([str(BIN / run["driver"]), "deck.yaml"], tmp, env)
    if kind == "restart" and rc == 0:
        restarts = sorted(tmp.glob("*.restart"))
        assert restarts, "the restart card wrote no .restart file"
        rc, out2 = _run([str(BIN / run["driver"]), "deck.yaml", "--restart", restarts[0].name], tmp, env)
        out += out2
    return rc, out


@pytest.mark.parametrize("rec", RECORDS, ids=[r["id"] for r in RECORDS])
def test_cpu_card_runs_trimmed(rec, tmp_path):
    if rec["id"] in EXCEPTED:
        pytest.skip(f"named exception in do-cards.yaml: {rec['id']} (no deck; the Editor's chapter lane fixes it)")
    why = c.missing_build_option(rec, (BUILD / "CMakeCache.txt").read_text(encoding="utf-8"))
    if why:
        pytest.skip(why)
    rc, out = _execute(rec, tmp_path)
    tail = "\n".join(out.strip().splitlines()[-5:])
    if rec["run"].get("check"):
        print(tail)
    if rec["expect"] == "exit 0":
        assert rc == 0, f"exit {rc}:\n{tail}"
    else:
        msg = rec["expect"][len("refused: "):]
        assert rc != 0 and msg in out, f"expected a refusal with {msg!r}, got exit {rc}:\n{tail}"
