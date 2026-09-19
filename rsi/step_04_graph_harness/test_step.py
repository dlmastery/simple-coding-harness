"""Step 04 - an illegal path is skipped and counted, never replaced; score_test is a sink behind FREEZE;
graph.json and paths.json do not change; the loop walks the paths in order."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import checks, graph, packs, steps, tasks  # noqa: E402
from common.fake import FakeModel  # noqa: E402

PACK = "adult-income-graph"
TASK = tasks.test_curriculum()[0][0]


def with_illegal_path(pack, index=5):
    """Break one path of the copy: drop its encode node, so the graph's one-of constraint fails."""
    path = pack / "paths.json"
    paths = json.loads(path.read_text(encoding="utf-8"))
    paths[index]["nodes"] = ["load", "scale", "model", "fit"]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(paths, f, indent=1)
    return paths


def test_loop_walks_the_paths_in_order_and_the_pack_lints(tmp_path):
    pack = steps.workspace(HERE, PACK, into=tmp_path / "p")
    assert packs.lint_pack(pack, TASK) == []
    run = checks.run_pack(pack, TASK, FakeModel(), tmp_path / "p" / "run", arm="control")
    paths = json.loads((pack / "paths.json").read_text(encoding="utf-8"))
    assert [a["path_id"] for _, a in checks.tool_calls(run, "walk_path")] == [p["id"] for p in paths]
    assert [r["recipe"] for r in run.fits] == [graph.path_recipe(p) for p in paths]
    assert run.budget.used == 24 and run.gate.result is not None


def test_illegal_path_is_skipped_and_counted_never_replaced(tmp_path):
    pack = steps.workspace(HERE, PACK, into=tmp_path / "p")
    paths = with_illegal_path(pack)
    before = packs.checksums(pack)
    run = checks.run_pack(pack, TASK, FakeModel(), tmp_path / "p" / "run", arm="control")
    assert run.budget.used == 24                                                       # the skip still cost a fit
    skipped = [r for r in run.fits if r["error"] and r["error"].startswith("illegal path")]
    assert len(skipped) == 1 and skipped[0]["error"] == "illegal path: edge scale -> model is not in the graph"
    assert len([r for r in run.fits if r["val_score"] is not None]) == 23
    legal = [graph.path_recipe(p) for p in paths if graph.why_illegal(json.loads((pack / "graph.json").read_text(encoding="utf-8")), p) is None]
    assert [r["recipe"] for r in run.fits if r["val_score"] is not None] == legal      # no path was invented in its place
    assert packs.checksums(pack) == before                                             # and paths.json was not repaired
    assert run.gate.result["recipe"] in legal


def test_score_test_is_unreachable_before_freeze(tmp_path):
    pack = steps.workspace(HERE, PACK, into=tmp_path / "p")
    g = json.loads((pack / "graph.json").read_text(encoding="utf-8"))
    assert g["nodes"]["score_test"]["gate"] == "freeze_only" and g["mutable"] is False
    assert checks.test_before_freeze(pack, TASK, tmp_path / "p" / "fresh").startswith("Error: the test split is locked until FREEZE")
    bad = {"id": "px", "nodes": ["load", "scale", "encode", "model", "fit", "score_test"], "bindings": graph.path_recipe(json.loads((pack / "paths.json").read_text(encoding="utf-8"))[0])}
    assert graph.why_illegal(g, bad) == "reaches score_test, a sink that opens only after FREEZE"


def test_graph_and_paths_are_byte_identical_after_a_run(tmp_path):
    pack = steps.workspace(HERE, PACK, into=tmp_path / "p")
    assert checks.unchanged(pack, lambda: checks.run_pack(pack, TASK, FakeModel(), tmp_path / "p" / "run", arm="control"))


def test_fit_recipe_is_not_a_way_around_the_graph(tmp_path):
    pack = steps.workspace(HERE, PACK, into=tmp_path / "p")
    run = checks.run_pack(pack, TASK, FakeModel(), tmp_path / "p" / "run", arm="control")
    from common.tools import execute
    assert execute(run, checks.call("fit_recipe", recipe=run.fits[0]["recipe"])).startswith("Error: fit_recipe is not in this pack's tools.md")
    assert execute(run, checks.call("walk_path", path_id="p99")).startswith("Error: no path 'p99' in paths.json")
