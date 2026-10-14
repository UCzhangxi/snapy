"""Check of kintera's saturation-formula table (ch10, adding a formula), on a CPU build of kintera's own files.

kintera v2.6.2 = chengcli/kintera@c55b13b2204997d2d09e04498558ab9495d8ee77 resolves a formula name by its position in
`func1_names` and takes the function at the same position of `func1_table_cpu` (src/utils/user_funcs.hpp,
`get_host_func`; src/func_table.cpp). This check compiles those two files and src/vapors/vapor_functions.h at that
commit with a small driver, CPU only, and runs the lookup twice: on the files as they are, and with two names added to
`func1_names` after "h2o_bryan_ddT" but no functions added to the table.

  [C1] as they are: "h2o_bryan" and "h2o_bryan_ddT" resolve to h2o_bryan and h2o_bryan_ddT
  [C2] as they are: a name not in the list throws "Function <name> not registered."
  [C3] two names without table entries: no error; the first new name resolves to the function after h2o_bryan_ddT
  [C4] the same: every later name resolves to the function two positions further on
  [C5] the same: the last name points past the end of the table, and the driver does not exit cleanly

Needs git and a C++17 compiler (`c++`). Run from the report directory: python3 src/snapy_report/ch10/func_table_check.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPORT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPORT / "tools"))
import code_anchors  # noqa: E402

KINTERA = ("chengcli/kintera", "c55b13b2204997d2d09e04498558ab9495d8ee77")
FILES = {"src/utils/user_funcs.hpp": "inc/kintera/utils/user_funcs.hpp",
         "src/vapors/vapor_functions.h": "inc/kintera/vapors/vapor_functions.h",
         "src/func_table.cpp": "func_table.cpp"}
DRIVER = r'''
#include <cstdio>
#include <stdexcept>
#include <kintera/utils/user_funcs.hpp>
#include <kintera/vapors/vapor_functions.h>
namespace kintera { extern user_func1 func1_table_cpu[]; extern std::vector<std::string> func1_names; }
using namespace kintera;
int main(int argc, char** argv) {
  std::setvbuf(stdout, nullptr, _IONBF, 0);
  for (int i = 1; i < argc; ++i) {
    try {
      auto f = get_host_func(std::vector<std::string>{argv[i]}, func1_names, func1_table_cpu)[0];
      std::printf("%s %.9g\n", argv[i], f(200.));
    } catch (std::exception const& e) {
      std::printf("%s threw %s\n", argv[i], e.what());
    }
  }
  std::printf("done\n");
}
'''
REFERENCE = r'''
#include <cstdio>
#include <kintera/vapors/vapor_functions.h>
using namespace kintera;
int main() {
  std::printf("h2o_bryan %.9g\nh2o_bryan_ddT %.9g\nnh3_ideal %.9g\nnh3_ideal_ddT %.9g\nnh3_h2s_lewis %.9g\n",
              h2o_bryan(200.), h2o_bryan_ddT(200.), nh3_ideal(200.), nh3_ideal_ddT(200.), nh3_h2s_lewis(200.));
}
'''
NAMES = ["h2o_bryan", "h2o_bryan_ddT", "h2o_mine", "nh3_ideal", "na_h2s_visscher_ddT"]


def report(tag, ok, label, numbers):
    print("[%s] %s %s: %s" % (tag, "PASS" if ok else "FAIL", label, numbers))
    return ok


def build(tmp, table, name):
    (tmp / "table.cpp").write_text(table)
    exe = tmp / name
    subprocess.run(["c++", "-std=c++17", "-O1", "-I", str(tmp / "inc"), str(tmp / "driver.cpp"),
                    str(tmp / "table.cpp"), "-o", str(exe)], check=True)
    return exe


def run(exe, *args):
    p = subprocess.run([str(exe), *args], capture_output=True, text=True)
    return p.returncode, dict(l.split(" ", 1) for l in p.stdout.splitlines() if " " in l), p.stdout


def main():
    checkout = code_anchors.find_commit(*KINTERA)
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for src, dst in FILES.items():
            (tmp / dst).parent.mkdir(parents=True, exist_ok=True)
            text = subprocess.run(["git", "-C", str(checkout), "show", f"{KINTERA[1]}:{src}"],
                                  check=True, capture_output=True, text=True).stdout
            (tmp / dst).write_text(text)
        (tmp / "inc" / "configure.h").write_text("#pragma once\n#include <cstddef>\n#define DISPATCH_MACRO\n")
        (tmp / "driver.cpp").write_text(DRIVER)
        (tmp / "reference.cpp").write_text(REFERENCE)
        subprocess.run(["c++", "-std=c++17", "-O1", "-I", str(tmp / "inc"), str(tmp / "reference.cpp"),
                        "-o", str(tmp / "reference")], check=True)
        ref = dict(l.split(" ", 1) for l in subprocess.run([str(tmp / "reference")], capture_output=True,
                                                            text=True, check=True).stdout.splitlines())
        table = (tmp / "func_table.cpp").read_text()
        rc0, got0, _ = run(build(tmp, table, "lookup"), *NAMES)
        mutated = table.replace('"h2o_bryan_ddT",      "nh3_ideal",',
                                '"h2o_bryan_ddT",      "h2o_mine",      "h2o_mine_ddT",      "nh3_ideal",', 1)
        assert mutated != table, "the name list moved; update the mutation"
        rc1, got1, out1 = run(build(tmp, mutated, "lookup_mutated"), *NAMES)

    print("kintera %s, CPU, formulas evaluated at T = 200 K" % KINTERA[1])
    results = []
    results.append(report("C1", rc0 == 0 and got0["h2o_bryan"] == ref["h2o_bryan"]
                 and got0["h2o_bryan_ddT"] == ref["h2o_bryan_ddT"], "names as they are resolve to their functions",
                 "h2o_bryan %s, h2o_bryan_ddT %s" % (got0["h2o_bryan"], got0["h2o_bryan_ddT"])))
    results.append(report("C2", got0["h2o_mine"] == "threw Function h2o_mine not registered.",
                 "a name not in the list throws", got0["h2o_mine"]))
    results.append(report("C3", got1.get("h2o_mine") == ref["nh3_ideal"],
                 "a new name without a table entry resolves silently to the next function",
                 "h2o_mine %s = nh3_ideal %s" % (got1.get("h2o_mine"), ref["nh3_ideal"])))
    results.append(report("C4", got1.get("nh3_ideal") == ref["nh3_h2s_lewis"],
                 "every later name resolves two positions further on",
                 "nh3_ideal %s = nh3_h2s_lewis %s" % (got1.get("nh3_ideal"), ref["nh3_h2s_lewis"])))
    results.append(report("C5", rc1 != 0 and "done" not in out1,
                 "the last name points past the end of the table", "exit status %d, no clean exit" % rc1))
    print("%d of %d passed" % (sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
