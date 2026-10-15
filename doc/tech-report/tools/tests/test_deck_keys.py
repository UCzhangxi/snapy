"""Tests of tools/gen_deck_keys.py, the Appendix I generator, on small parsers written like snapy's.

Run from the report directory: `python3 -m pytest tools/tests`.
"""

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import gen_deck_keys as g  # noqa: E402

PARSER = r'''
FooOptions FooOptionsImpl::from_yaml(std::string const& filename,
                                     bool verbose) {
  auto config = YAML::LoadFile(filename);
  auto node = config["foo"];
  check_keys(node, "foo", {"alpha", "name", "flag", "must", "sub", "table", "unused"},
             "pyharp", {"cfl"});
  op->alpha() = node["alpha"].as<double>(1.e-6);
  op->verbose() = node["name"].as<bool>(verbose);
  if (node["flag"]) {
    auto const text = node["flag"].Scalar();
    op->flag() = text == "true";
  }
  TORCH_CHECK(node["must"], "FooOptions: must is required (no default).");
  op->must() = node["must"].as<double>();
  auto take = [&](char const* key, double fallback) {
    if (!node[key]) return fallback;
    return node[key].as<double>();
  };
  op->beta() = take("table", 2.5);
  check_keys(node["sub"], "foo/sub", {"type"});
  op->sub() = BarOptionsImpl::from_yaml(node["sub"]);
  return op;
}
'''

READER = r'''
BarOptions BarOptionsImpl::from_yaml(YAML::Node const& node) {
  auto op = BarOptionsImpl::create();
  op->type() = node["type"].as<std::string>("roe");
  return op;
}
'''

HEADER = "struct FooOptionsImpl {\n  ADD_ARG(bool, flag) = false;\n};\n"


def tree(tmp_path):
    (tmp_path / "src" / "foo").mkdir(parents=True)
    (tmp_path / "src" / "foo" / "foo.cpp").write_text(PARSER)
    (tmp_path / "src" / "foo" / "bar.cpp").write_text(READER)
    (tmp_path / "src" / "foo" / "foo.hpp").write_text(HEADER)
    return tmp_path


def test_every_listed_key_once_with_its_default(tmp_path):
    rows = {f"{r['path']}/{r['key']}": r for r in g.extract(tree(tmp_path))}
    assert sorted(rows) == ["foo/alpha", "foo/cfl", "foo/flag", "foo/must", "foo/name", "foo/sub",
                            "foo/sub/type", "foo/table", "foo/unused"]
    d = {k: (r["default"]["kind"], r["default"]["value"]) for k, r in rows.items()}
    assert d["foo/alpha"] == ("fallback", "1.e-6")
    assert d["foo/name"] == ("fallback", "verbose")
    assert d["foo/flag"] == ("struct", "false")          # guarded read; the options struct's value stands
    assert d["foo/must"] == ("required", "")
    assert d["foo/table"] == ("fallback", "2.5")         # helper called with the key and a fallback
    assert d["foo/sub"] == ("block", "")
    assert d["foo/sub/type"] == ("fallback", '"roe"')    # block handed whole to another reader
    assert d["foo/unused"] == ("unread", "")
    assert d["foo/cfl"] == ("library", "")
    assert rows["foo/cfl"]["reader"] == "pyharp"


def test_a_read_of_the_same_key_in_another_block_is_not_its_default(tmp_path):
    t = tree(tmp_path)
    (t / "src" / "foo" / "foo.cpp").write_text(PARSER.replace('op->alpha() = node["alpha"].as<double>(1.e-6);',
                                                              'op->alpha() = other["alpha"].as<double>(9.);'))
    rows = {f"{r['path']}/{r['key']}": r for r in g.extract(t)}
    assert rows["foo/alpha"]["default"]["kind"] != "fallback"


def test_section_link_needs_the_path_or_the_enclosing_block():
    row = {"path": "forcing/top-cool", "key": "tau"}
    secs = [("sec-a", "A", ["tau"]),                          # the key alone: another block's tau
            ("sec-b", "B", ["top-cool", "tau", "tau"]),       # key with its block
            ("sec-c", "C", ["forcing/top-cool/tau"])]         # the full path
    assert g.explaining(row, secs) == ("sec-c", "C")
    assert g.explaining(row, secs[:2]) == ("sec-b", "B")
    assert g.explaining(row, secs[:1]) is None


def test_yaml_example_paths():
    assert g._yaml_paths(["forcing:", "  const-gravity:", "    grav1: -9.8  # m s^-2"]) == [
        "forcing", "forcing/const-gravity", "forcing/const-gravity/grav1"]


def test_committed_fragment_is_current():
    assert g.main(["--check"]) == 0
