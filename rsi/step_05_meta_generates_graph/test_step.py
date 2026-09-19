"""Lesson 05 - a meta skill generates the graph harness under human approval: lint_pack refuses a proposal with
a cycle or a path that violates a constraint before the human ever sees it; the proposal renders the graph as
nodes and edges; an edit that removes a path lands and the pack still runs; an edit that removes an edge every
path needs does not lint and does not land; the writer cannot walk or fit; the generated pack passes lesson
04's checks.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import packs, render, tasks, testing  # noqa: E402

WRITER = "graph-writer"
OUT = "adult-income-graph"


def setup(tmp_path):
    writer = testing.workspace(HERE, tmp_path, WRITER)
    task_path = writer / "task.json"
    rendered = tmp_path / "runs" / WRITER / "rendered"
    packs.write_pack(rendered, render.render(writer / "template", tasks.load_task(task_path)))
    return writer, task_path, rendered, tmp_path / ".claude" / "skills" / OUT


def propose(writer, task_path, payload, target):
    return testing.tool("propose", "--pack", writer, "--task", task_path, "--target", target, "--kind", "pack",
                        "--payload", payload if isinstance(payload, str) else f"@{payload}", "--summary", "graph pack for adult_income")


def test_writer_cannot_walk_or_fit(tmp_path):
    writer, task_path, *_ = setup(tmp_path)
    assert "not in graph-writer's tools.md" in testing.tool("walk_path", "--pack", writer, "--task", task_path, "--path", "p00")["error"]
    assert "not in graph-writer's tools.md" in testing.tool("fit_recipe", "--pack", writer, "--task", task_path, "--recipe", "model=logreg,hyper=1,scale=yes,encode=onehot,class_weight=none")["error"]


def test_cycle_and_bad_path_refused_before_the_human_sees_them(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    files = packs.read_pack(rendered)
    g = json.loads(files["graph.json"])
    g["edges"].append(["fit", "scale"])
    out = propose(writer, task_path, json.dumps(dict(files, **{"graph.json": json.dumps(g)})), target)
    assert "lint_pack refuses this pack before the user sees it" in out["error"] and "cycle" in out["error"]
    paths = json.loads(files["paths.json"])
    paths[1]["nodes"] = ["load", "scale", "encode", "model", "fit", "score_test"]
    out = propose(writer, task_path, json.dumps(dict(files, **{"paths.json": json.dumps(paths)})), target)
    assert "reaches score_test" in out["error"]
    assert not (tmp_path / "runs" / WRITER / "adult_income" / "proposals").exists() or not list((tmp_path / "runs" / WRITER / "adult_income" / "proposals").glob("*.json"))


def test_proposal_shows_the_graph_as_nodes_and_edges(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    assert "### graph.json as a graph" in p["diff"]
    assert "nodes: load, scale, encode, model, fit, score_test" in p["diff"]
    assert "edges: load -> scale; scale -> encode; encode -> model; model -> fit; fit -> score_test" in p["diff"]


def test_edit_removing_a_path_lands_and_the_pack_still_runs(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    edited = packs.read_pack(rendered)
    paths = json.loads(edited["paths.json"])
    removed = paths.pop(7)                       # the human drops one path
    loop = json.loads(edited["loop.json"])
    loop["N"] = 23                               # ...and the counter with it; the linter holds N to the budget
    edited["paths.json"], edited["loop.json"] = json.dumps(paths, indent=1), json.dumps(loop, indent=1)
    out = testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "edit: drop p07", "--edited", json.dumps(edited))
    assert "does not lint" in out["error"] and "N 23" in out["error"]
    # the honest edit: keep N, drop the path, and the linter says the count no longer matches - the human must
    # keep the budget; so the edit that lands is: replace p07's binding with another legal recipe
    edited = packs.read_pack(rendered)
    paths = json.loads(edited["paths.json"])
    paths[7]["bindings"] = dict(paths[7]["bindings"], hyper=0.25)
    edited["paths.json"] = json.dumps(paths, indent=1)
    out = testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "edit: p07 at C=0.25", "--edited", json.dumps(edited))
    assert out["landed"] and out["decision"] == "edit"
    assert json.loads((target / "paths.json").read_text(encoding="utf-8"))[7]["bindings"]["hyper"] == 0.25
    assert removed["id"] == "p07"
    task = testing.task("adult_income")
    testing.tool("load_splits", "--pack", target, "--task", task)
    walked = testing.tool("walk_path", "--pack", target, "--task", task, "--paths", "p06,p07")
    assert walked["results"][1]["recipe"]["hyper"] == 0.25 and walked["results"][1]["val_score"] is not None


def test_edit_removing_a_needed_edge_does_not_land(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    edited = packs.read_pack(rendered)
    g = json.loads(edited["graph.json"])
    g["edges"] = [e for e in g["edges"] if e != ["scale", "encode"]]
    edited["graph.json"] = json.dumps(g)
    out = testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "edit", "--edited", json.dumps(edited))
    assert "does not lint" in out["error"] and "edge scale -> encode is not in the graph" in out["error"]
    assert not target.exists()


def test_generated_pack_passes_lesson_04_checks(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "yes")
    assert packs.read_pack(target) == packs.read_pack(rendered)
    reference = packs.read_pack(HERE.parent / "step_04_graph_harness" / ".claude" / "skills" / OUT)
    assert json.loads(reference["paths.json"]) == json.loads(packs.read_pack(target)["paths.json"])
    assert json.loads(reference["graph.json"]) == json.loads(packs.read_pack(target)["graph.json"])
    task = testing.task("adult_income")
    before = packs.checksums(target)
    testing.tool("load_splits", "--pack", target, "--task", task)
    for t0 in range(0, 24, 6):
        out = testing.tool("walk_path", "--pack", target, "--task", task, "--paths", ",".join(f"p{t:02d}" for t in range(t0, t0 + 6)))
    assert out["FREEZE"] and out["fits_used"] == 24
    assert packs.checksums(target) == before


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE)
    assert "p1" in text
