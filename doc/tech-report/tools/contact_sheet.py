#!/usr/bin/env python3
"""Contact sheet of the book's figures: draw every figure cell once and lay the results out on a few pages, or
compare two such drawings, before and after a change to the figure code (STYLE.md 6; figstyle's port).

    python3 tools/contact_sheet.py draw OUT [--chapters ch03,ch09]
        draws every figure cell of book/chapters (as tools/check_fig_output.py runs it) to OUT/<label>.png at 100
        dpi and writes OUT/index.json: per label, the chapter, the size in inches and the sha256 of its SVG.
    python3 tools/contact_sheet.py sheet OUT -o sheet.png [--compare BEFORE] [--all] [--per-page 24]
        lays the PNGs of OUT out on pages sheet-01.png, sheet-02.png, ... With --compare, each row shows a figure
        BEFORE (left) and OUT (right), only for figures whose SVG changed (all with --all), and prints how many are
        byte-identical, changed, added and removed.

A figure's SVG is compared, not its PNG: the SVG is what the HTML book embeds, and with figstyle's fixed
`svg.hashsalt` two draws of an unchanged figure give the same bytes. Needs numpy, matplotlib and `snapy_report`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_fig_output as cfo  # noqa: E402

REPORT = cfo.REPORT


def draw_all(out: Path, chapters=None, report: Path = REPORT) -> dict:
    src = report / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for cell in cfo.figure_cells(report):
        if chapters and cell.chapter not in chapters:
            continue
        try:
            fig = cfo.draw(cell)
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            if not isinstance(fig.canvas, FigureCanvasAgg):
                FigureCanvasAgg(fig)
            svg = cfo.svg(fig)
            fig.savefig(out / f"{cell.label}.png", dpi=100, bbox_inches="tight", metadata={"Software": None})
            w, h = fig.get_size_inches()
            index[cell.label] = {"chapter": cell.chapter, "size_in": [round(w, 3), round(h, 3)],
                                 "svg_sha256": hashlib.sha256(svg).hexdigest()}
        except Exception as e:  # noqa: BLE001 - recorded, so the sheet shows the gap
            index[cell.label] = {"chapter": cell.chapter, "error": f"{type(e).__name__}: {e}"[:200]}
        finally:
            plt.close("all")
    (out / "index.json").write_text(json.dumps(index, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return index


def compare(before: dict, after: dict) -> dict[str, list[str]]:
    same = [k for k in after if k in before and before[k].get("svg_sha256") == after[k].get("svg_sha256")
            and "svg_sha256" in after[k]]
    changed = [k for k in after if k in before and k not in same]
    return {"identical": sorted(same), "changed": sorted(changed),
            "added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after))}


def _pages(rows: list, per_page: int) -> list[list]:
    return [rows[i:i + per_page] for i in range(0, len(rows), per_page)] or [[]]


def sheet(out: Path, target: Path, before_dir: Path | None = None, show_all=False, per_page=24) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.image as mpimg
    from matplotlib.figure import Figure

    after = json.loads((out / "index.json").read_text(encoding="utf-8"))
    if before_dir is not None:
        before = json.loads((before_dir / "index.json").read_text(encoding="utf-8"))
        groups = compare(before, after)
        labels = sorted(after) if show_all else groups["changed"] + groups["added"]
        cols, rows = 2, [(lab, before_dir / f"{lab}.png", out / f"{lab}.png") for lab in labels]
        per_page = max(1, per_page // 2)
    else:
        groups = None
        rows = [(lab, out / f"{lab}.png") for lab in sorted(after)]
        cols = 4
    written = []
    for n, page in enumerate(_pages(rows, per_page), 1):
        nrow = max(1, len(page) if groups is not None else math.ceil(len(page) / cols))
        fig = Figure(figsize=(cols * 4.0, nrow * 2.6 + 0.4))
        axes = fig.subplots(nrow, cols, squeeze=False)
        for ax in axes.flat:
            ax.set_axis_off()
        cells = []
        for row in page:
            if groups is not None:
                cells.extend([(row[0] + " (before)", row[1]), (row[0] + " (after)", row[2])])
            else:
                cells.append(row)
        for ax, (title, png) in zip(axes.flat, cells):
            ax.set_title(title, fontsize=8)
            if png.exists():
                ax.imshow(mpimg.imread(png))
            else:
                ax.text(0.5, 0.5, "not drawn", ha="center", va="center", fontsize=8, transform=ax.transAxes)
        head = target.stem + (f" page {n}" if len(rows) > per_page else "")
        if groups is not None:
            head += " — {} identical, {} changed, {} added, {} removed".format(
                *(len(groups[k]) for k in ("identical", "changed", "added", "removed")))
        fig.suptitle(head, fontsize=10)
        path = target.with_name(f"{target.stem}-{n:02d}{target.suffix}")
        fig.savefig(path, dpi=80, metadata={"Software": None})
        written.append(path)
    if groups is not None:
        print("contact_sheet: {} identical, {} changed, {} added, {} removed".format(
            *(len(groups[k]) for k in ("identical", "changed", "added", "removed"))))
        for k in ("changed", "added", "removed"):
            for lab in groups[k]:
                print(f"  {k}: {lab}")
    print("contact_sheet: wrote " + ", ".join(str(p) for p in written))
    return written


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draw", help="draw every figure cell to OUT")
    d.add_argument("out", type=Path)
    d.add_argument("--chapters", default="")
    s = sub.add_parser("sheet", help="lay out the PNGs of OUT, or compare them with BEFORE")
    s.add_argument("out", type=Path)
    s.add_argument("-o", "--output", type=Path, required=True)
    s.add_argument("--compare", type=Path, default=None)
    s.add_argument("--all", action="store_true")
    s.add_argument("--per-page", type=int, default=24)
    args = ap.parse_args(argv)
    if args.cmd == "draw":
        chapters = {c.strip() for c in args.chapters.split(",") if c.strip()} or None
        index = draw_all(args.out, chapters)
        errors = [k for k, v in index.items() if "error" in v]
        print(f"contact_sheet: drew {len(index) - len(errors)} figure(s) to {args.out}"
              + (f"; {len(errors)} could not be drawn: " + ", ".join(errors) if errors else ""))
        return 1 if errors else 0
    sheet(args.out, args.output, args.compare, args.all, args.per_page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
