#!/usr/bin/env python3
"""A restart restores each output block's schedule by IDENTITY, so a block inserted ahead of
an existing one must not steal its file numbering and next_time (the pre-fix restore was by
position). Reuses the harness of run_restart_new_output.py."""
import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_restart_new_output import (FRAME_DT, RESTART_DT, RESUME_TLIM, BASE_TLIM,
                                    restart_schedule, run, stream_times, write_case)

SKIP_CODE = 125


def numbers(case_dir: Path, stream: str) -> list[int]:
  return sorted(int(f.name.split(".")[-2]) for f in case_dir.glob(f"*.{stream}.*.nc"))


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--build-dir", required=True)
  parser.add_argument("--build-type", required=True)
  args = parser.parse_args()

  build_dir = Path(args.build_dir).resolve()
  tests_dir = build_dir / "tests"
  repo_root = Path(__file__).resolve().parent.parent
  exe = build_dir / "bin" / f"straka.{args.build_type}"
  if not exe.exists():
    raise FileNotFoundError(f"missing executable {exe}")
  base_yaml = repo_root / "examples" / "straka.yaml"

  torchrun = shutil.which("torchrun")
  if torchrun is None:
    raise FileNotFoundError("torchrun not found in PATH")
  env = os.environ.copy()
  env["BACKEND"] = "gloo"
  env["PYTHONPATH"] = ":".join([str(repo_root / "python"), str(repo_root)]
                              + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))

  restart = {"type": "restart", "dt": RESTART_DT}
  prim = {"type": "netcdf", "variables": ["prim"], "dt": FRAME_DT}
  uov = {"type": "netcdf", "variables": ["uov"], "dt": FRAME_DT}
  launch = [torchrun, "--no-python", "--nproc-per-node=1", str(exe)]

  base_dir = tests_dir / "restart_insert_output_base"
  run(launch + [str(write_case(base_yaml, base_dir, BASE_TLIM, [restart, prim]))], base_dir, env)
  restart_file = sorted(base_dir.glob("*.restart"))[-1]
  base_last = numbers(base_dir, "out1")[-1]
  resume_t, _, saved_numbers = restart_schedule(restart_file)

  # resume with uov INSERTED AHEAD of prim: prim is now out2 and must keep its own schedule
  resumed_dir = tests_dir / "restart_insert_output_resumed"
  resumed_yaml = write_case(base_yaml, resumed_dir, RESUME_TLIM, [restart, uov, prim])
  run(launch + [str(resumed_yaml), "--restart", str(restart_file.resolve())], resumed_dir, env)

  prim_numbers = numbers(resumed_dir, "out2")
  uov_numbers = numbers(resumed_dir, "out1")
  if not prim_numbers or prim_numbers[0] < saved_numbers[1]:
    raise AssertionError(
        f"prim (out2) restarted its numbering at {prim_numbers[:1]} instead of continuing from "
        f"the restart's {saved_numbers[1]} (base run ended at {base_last}): schedule went to the "
        f"inserted block")
  if not uov_numbers or uov_numbers[0] != 0:
    raise AssertionError(f"inserted uov (out1) should number from 0, got {uov_numbers[:1]}")
  _, next_time, file_number = restart_schedule(sorted(resumed_dir.glob("*.restart"))[-1])
  if next_time[1] != next_time[2]:
    raise AssertionError(f"streams not co-scheduled after resume: next_time {next_time}")
  times = stream_times(resumed_dir)   # the inserted block also writes once at the resume instant
  after = {s: [t for t in ts if abs(t - resume_t) > 1e-3] for s, ts in times.items()}
  if after["out2"] != after["out1"]:
    raise AssertionError(f"frames differ after resume:\n  out1 {times['out1']}\n  out2 {times['out2']}")
  print(f"ok: prim numbers {prim_numbers}, uov numbers {uov_numbers}, next_time {next_time}, "
        f"file_number {file_number}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
