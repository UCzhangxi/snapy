"""Pinned rerun of the chapter 10 checks and figures; writes the logs in logs/ (no images are kept).

Run from doc/tech-report, with snapy and kintera built at the pins in the active Python:
    python3 src/snapy_report/ch10/evidence/run_evidence.py \
        --snapy <snapy checkout> --kintera <kintera checkout> --pyharp <pyharp checkout>
The checkouts must be at the pins below (pyharp only needs to contain its pinned commit). Every log starts
with the command, the pins, the UTC date and the exit code; the paths of the checkouts are not written.
Exits with the number of failed steps.
"""
import argparse
import datetime
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SNAPY = "e894700ff7aee30b52882e5202b16461413780b0"
KINTERA = "c55b13b2204997d2d09e04498558ab9495d8ee77"
PYHARP = "4721715855e937c1e8b218e964c0655f46e56e29"  # anchors only (the max_redo default)
CLAIMS_EXPECTED = 26

HERE = Path(__file__).resolve().parent
CH10 = HERE.parent
ROOT = CH10.parents[2]  # doc/tech-report
REL = CH10.relative_to(ROOT).as_posix()


def git_head(path):
    return subprocess.check_output(["git", "-C", path, "rev-parse", "HEAD"], text=True).strip()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scrub(text, hide):
    for h in hide:
        text = text.replace(h, {str(ROOT): ".", sys.prefix: "<venv>", MPLDIR: "<tmp>",
                                os.path.expanduser("~"): "~"}.get(h, "<checkout>"))
    return text


MPLDIR = tempfile.mkdtemp(prefix="mpl")  # a private matplotlib cache, so no home path reaches the logs


def run(argv, shown, hide, env=None):
    env = dict(env or os.environ, MPLCONFIGDIR=MPLDIR)
    p = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, env=env)
    return p.returncode, scrub(p.stdout, hide), scrub(p.stderr, hide), shown


def write_log(name, code, out, err, shown, date, extra=()):
    lines = ["# command: " + shown, "# cwd: doc/tech-report",
             "# pins: snapy@%s kintera@%s" % (SNAPY, KINTERA), "# date: " + date,
             "# exit: %d" % code] + ["# " + e for e in extra] + ["--- stdout ---", out.rstrip("\n")]
    if err.strip():
        lines += ["--- stderr ---", err.rstrip("\n")]
    (HERE / "logs" / (name + ".log")).write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapy", required=True)
    ap.add_argument("--kintera", required=True)
    ap.add_argument("--pyharp", required=True)
    a = ap.parse_args()
    hide = {os.path.abspath(p) for p in (a.snapy, a.kintera, a.pyharp)}
    hide = sorted(hide | {str(ROOT), sys.prefix, MPLDIR, os.path.expanduser("~")}, key=len, reverse=True)
    date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (HERE / "logs").mkdir(exist_ok=True)
    py = "python3"
    failed = []

    # environment: pins of the checkouts and versions of the installed packages
    heads = {"snapy": git_head(a.snapy), "kintera": git_head(a.kintera)}
    probe = ("import importlib,sys,platform\n"
             "print('python', sys.version.split()[0])\n"
             "for m in ['numpy','sympy','matplotlib','torch','pydisort','pyharp','kintera','snapy']:\n"
             "    try: print(m, importlib.import_module(m).__version__)\n"
             "    except Exception as e: print(m, 'import failed:', type(e).__name__)\n")
    code, out, err, _ = run([sys.executable, "-c", probe], "", hide)
    env_lines = ["platform %s %s" % (platform.system(), platform.machine())] + out.splitlines()
    pins_ok = heads["snapy"] == SNAPY and heads["kintera"] == KINTERA and "import failed" not in out
    env_lines += ["checkout snapy %s (%s)" % (heads["snapy"], "pin" if heads["snapy"] == SNAPY else "NOT the pin"),
                  "checkout kintera %s (%s)" % (heads["kintera"], "pin" if heads["kintera"] == KINTERA
                                                else "NOT the pin")]
    write_log("environment", 0 if pins_ok and code == 0 else 1, "\n".join(env_lines), err,
              py + " -c <version probe>", date)
    if not pins_ok or code:
        failed.append("environment")

    # the six executable checks: 26 claims; each rewrites its data/*.csv and must reproduce its committed .out
    claims = []
    for script in sorted(CH10.glob("*_check.py")):
        shown = "%s %s/%s" % (py, REL, script.name)
        code, out, err, _ = run([sys.executable, str(script)], shown, hide)
        same = out == script.with_suffix(".out").read_text()
        found = re.findall(r"^\[(C\d+)\] (PASS|FAIL) ", out, flags=re.M)
        claims += [(script.stem, c, v) for c, v in found]
        write_log(script.stem, code, out, err, shown, date,
                  ["stdout identical to committed %s: %s" % (script.with_suffix(".out").name,
                                                              "yes" if same else "NO")])
        if code or not same:
            failed.append(script.stem)
    npass = sum(v == "PASS" for _, _, v in claims)
    rows = ["check\tclaim\tresult"] + ["%s\t%s\t%s" % c for c in claims]
    rows.append("# %d of %d claims PASS (%d expected)" % (npass, len(claims), CLAIMS_EXPECTED))
    (HERE / "logs" / "claims.tsv").write_text("\n".join(rows) + "\n")
    if npass != CLAIMS_EXPECTED or len(claims) != CLAIMS_EXPECTED:
        failed.append("claims")

    # the data the figures read, after the checks rewrote them, and the committed outputs the checks reproduced
    sums = sorted((CH10 / "data").glob("*.csv")) + sorted(CH10.glob("*_check.out"))
    (HERE / "logs" / "data.sha256").write_text("".join("%s  %s\n" % (sha256(p), p.relative_to(CH10).as_posix())
                                                       for p in sums))

    # every figure generator, rendered with the report style (figstyle.DPI) into a temporary folder: the book
    # renders the figures from these scripts, so only their sha256 is kept, in logs/figures.log
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), MPLBACKEND="Agg")
    figdir = tempfile.mkdtemp(prefix="fig")
    hide = hide + [figdir]
    flog = ["# figures: %d generators, each run as" % len(list(CH10.glob("fig_*.py"))),
            "#   PYTHONPATH=src %s -c 'from snapy_report.ch10.<name> import make_fig; "
            "make_fig().savefig(\"<name>.png\", metadata={\"Software\": None})'" % py,
            "# cwd: doc/tech-report", "# pins: snapy@%s kintera@%s" % (SNAPY, KINTERA), "# date: " + date,
            "# PNGs are not committed; columns: exit, bytes, sha256, figure"]
    nfig = 0
    for script in sorted(CH10.glob("fig_*.py")):
        png = os.path.join(figdir, script.stem + ".png")
        src = ("from snapy_report.ch10.%s import make_fig\n"
               "make_fig().savefig(%r, metadata={'Software': None})\n" % (script.stem, png))
        code, out, err, _ = run([sys.executable, "-c", src], "", hide, env=env)
        ok = code == 0 and os.path.exists(png)
        nfig += ok
        flog.append("%d\t%s\t%s\t%s.png" % (code, os.path.getsize(png) if ok else "-", sha256(png) if ok else "-",
                                           script.stem))
        flog += ["#   " + ln for ln in (out + err).splitlines()]
        if not ok:
            failed.append(script.stem)
    flog.append("# exit: %d (%d of %d rendered)" % (int(nfig != len(list(CH10.glob("fig_*.py")))), nfig,
                                                    len(list(CH10.glob("fig_*.py")))))
    (HERE / "logs" / "figures.log").write_text("\n".join(flog) + "\n")
    shutil.rmtree(figdir, ignore_errors=True)

    # the chapter's pytest and the citation-anchor audit at the pins
    shown = "%s -m pytest -q -p no:cacheprovider src/tests/test_ch10_checks.py" % py
    code, out, err, _ = run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                             "src/tests/test_ch10_checks.py"], shown, hide)
    write_log("pytest_ch10", code, out, err, shown, date)
    if code:
        failed.append("pytest_ch10")
    shown = ("%s reviews/check_ch10_anchors.py --snapy <snapy@%s> --kintera <kintera@%s> --pyharp <pyharp>"
             % (py, SNAPY[:7], KINTERA[:7]))
    code, out, err, _ = run([sys.executable, "reviews/check_ch10_anchors.py", "--snapy", a.snapy,
                             "--kintera", a.kintera, "--pyharp", a.pyharp], shown, hide)
    write_log("anchors_ch10", code, out, err, shown, date, ["pyharp anchors at %s" % PYHARP])
    if code:
        failed.append("anchors_ch10")

    print("claims: %d of %d PASS; figures: %d; failed steps: %s" % (npass, len(claims), nfig,
                                                                     ", ".join(failed) or "none"))
    shutil.rmtree(MPLDIR, ignore_errors=True)
    return len(failed)


if __name__ == "__main__":
    sys.exit(main())
