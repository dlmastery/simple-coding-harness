"""Lesson 04 - graph engineering with loops: the loop walks paths in paths.json order; an illegal path is
skipped and counted, never repaired or invented; a path id not in paths.json is refused; score_test is
unreachable before FREEZE; graph.json / paths.json are byte-identical after a run; fit_recipe is not a
tool of this pack; lint_pack refuses a cyclic graph and a path that breaks a constraint.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import packs, recipe, testing  # noqa: E402

PACK = "adult-income-graph"
TASK = testing.task("adult_income")


def walk_all(pack):
    testing.tool("load_splits", "--pack", pack, "--task", TASK)
    rows = []
    for t0 in range(0, 24, 6):
        out = testing.tool("walk_path", "--pack", pack, "--task", TASK, "--paths", ",".join(f"p{t:02d}" for t in range(t0, t0 + 6)))
        rows += out["results"]
    return rows, out


def test_loop_walks_paths_in_order_and_scores_once(tmp_path):
    pack = testing.workspace(HERE, tmp_path, PACK)
    paths = json.loads((pack / "paths.json").read_text(encoding="utf-8"))
    rows, last = walk_all(pack)
    assert [r["path"] for r in rows] == [p["id"] for p in paths] and last["FREEZE"]
    assert [r["recipe"] for r in rows] == [p["bindings"] for p in paths] == recipe.static_list()
    best = max(rows, key=lambda r: r["val_score"] or 0)
    assert "test_score" in testing.tool("score_test", "--pack", pack, "--task", TASK, "--recipe", json.dumps(best["recipe"]))
    assert "once already" in testing.tool("score_test", "--pack", pack, "--task", TASK, "--recipe", json.dumps(best["recipe"]))["error"]
    card = testing.tool("scorecard", "--pack", pack, "--task", TASK)
    assert card["fits_used"] == 24 and card["best_val_score"] == 0.9172


def test_illegal_path_is_skipped_and_counted_never_replaced(tmp_path):
    pack = testing.workspace(HERE, tmp_path, PACK)
    pp = pack / "paths.json"
    paths = json.loads(pp.read_text(encoding="utf-8"))
    paths[3]["nodes"] = ["load", "encode", "scale", "model", "fit"]      # an edge the graph does not have
    paths[5]["nodes"] = ["load", "scale", "encode", "model", "fit", "score_test"]   # reaches the sink
    pp.write_text(json.dumps(paths, indent=1), encoding="utf-8")
    testing.tool("load_splits", "--pack", pack, "--task", TASK)
    out = testing.tool("walk_path", "--pack", pack, "--task", TASK, "--paths", "p00,p01,p02,p03,p04,p05")
    r3, r5 = out["results"][3], out["results"][5]
    assert r3["val_score"] is None and "illegal path: edge load -> encode is not in the graph" in r3["error"] and r3["n"] == 4
    assert r5["val_score"] is None and "reaches score_test" in r5["error"] and r5["n"] == 6
    assert out["fits_used"] == 6                    # both counted
    missing = testing.tool("walk_path", "--pack", pack, "--task", TASK, "--path", "p99")
    assert missing["refused"] and "does not invent one" in missing["error"]
    assert testing.tool("scorecard", "--pack", pack, "--task", TASK)["fits_used"] == 6


def test_score_test_unreachable_before_freeze_and_fit_recipe_not_a_tool(tmp_path):
    pack = testing.workspace(HERE, tmp_path, PACK)
    testing.tool("load_splits", "--pack", pack, "--task", TASK)
    out = testing.tool("walk_path", "--pack", pack, "--task", TASK, "--paths", "p00,p01")
    assert "18 fits remain" not in json.dumps(out)
    refused = testing.tool("score_test", "--pack", pack, "--task", TASK, "--recipe", json.dumps(out["results"][0]["recipe"]))
    assert "22 fits remain" in refused["error"]
    direct = testing.tool("fit_recipe", "--pack", pack, "--task", TASK, "--recipe", json.dumps(recipe.BASELINE))
    assert "not in adult-income-graph's tools.md" in direct["error"]


def test_graph_files_byte_identical_after_a_run(tmp_path):
    pack = testing.workspace(HERE, tmp_path, PACK)
    before = packs.checksums(pack)
    rows, _ = walk_all(pack)
    assert packs.checksums(pack) == before
    g = json.loads((pack / "graph.json").read_text(encoding="utf-8"))
    assert g["mutable"] is False and g["nodes"]["score_test"]["gate"] == "freeze_only"


def test_lint_refuses_a_cycle_and_a_bad_path():
    files = packs.read_pack(HERE / ".claude" / "skills" / PACK)
    g = json.loads(files["graph.json"])
    g["edges"].append(["fit", "load"])
    out = testing.tool("lint_pack", "--files", json.dumps(dict(files, **{"graph.json": json.dumps(g)})), "--task", TASK)
    assert any("cycle" in p for p in out["problems"])
    paths = json.loads(files["paths.json"])
    paths[0]["nodes"] = ["load", "scale", "scale", "encode", "model", "fit"]
    out = testing.tool("lint_pack", "--files", json.dumps(dict(files, **{"paths.json": json.dumps(paths)})), "--task", TASK)
    assert any("path p00" in p and "scale" in p for p in out["problems"])
    assert testing.tool("lint_pack", "--pack", HERE / ".claude" / "skills" / PACK, "--task", TASK)["ok"]


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE)
    assert "24" in text
