"""Step 05 - lint_pack rejects a cycle or an illegal path before the human sees it; an edit that removes an edge
lands and the pack still boots; the writer's proposal shows the graph as nodes and edges."""

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from common import checks, packs, tasks  # noqa: E402
from common.approve import Human  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import execute  # noqa: E402
from run import generate_graph  # noqa: E402

TASK = tasks.load_task(HERE / "skills" / "graph-writer" / "task.json")
SYNTH = tasks.test_curriculum()[0][0]


def proposal(tmp_path, answers=("n",)):
    run = generate_graph(FakeModel(), tmp_path / "out", human=Human(list(answers)), quiet=True)
    return run, dict(run.proposals.items["p1"]["payload"])


def test_lint_rejects_a_cycle_before_the_human_sees_it(tmp_path):
    run, files = proposal(tmp_path)
    g = json.loads(files["graph.json"])
    g["edges"].append(["fit", "scale"])                                          # a cycle: scale -> ... -> fit -> scale
    bad = {**files, "graph.json": json.dumps(g, indent=1)}
    asked_before = list(run.human.asked)
    result = execute(run, checks.call("propose", kind="pack", payload=bad, summary="with a cycle"))
    assert result.startswith("Error: lint_pack refuses this pack before the human sees it") and "graph.json has a cycle" in result
    assert run.human.asked == asked_before                                        # the human was never asked


def test_lint_rejects_a_path_that_violates_a_constraint(tmp_path):
    run, files = proposal(tmp_path)
    paths = json.loads(files["paths.json"])
    paths[3]["nodes"] = ["load", "scale", "encode", "encode", "model", "fit"]  # encode twice
    paths[4]["nodes"] = ["load", "scale", "encode", "model", "fit", "score_test"]  # reaches the sink
    bad = {**files, "paths.json": json.dumps(paths, indent=1)}
    result = execute(run, checks.call("propose", kind="pack", payload=bad, summary="bad paths"))
    assert "path p03: edge encode -> encode is not in the graph" in result
    assert "path p04: reaches score_test, a sink that opens only after FREEZE" in result
    assert len(run.human.asked) == 1                                              # only the writer's own, clean proposal


def test_the_human_sees_the_graph_as_nodes_and_edges(tmp_path):
    buf = io.StringIO()
    with redirect_stdout(buf):
        generate_graph(FakeModel(), tmp_path / "out", human=Human(["n"]), quiet=False)
    shown = buf.getvalue()
    assert "### graph.json as a graph" in shown and "nodes: load, scale, encode, model, fit, score_test" in shown
    assert "edges: load -> scale; scale -> encode; encode -> model; model -> fit; fit -> score_test" in shown
    assert not (tmp_path / "out").exists()


def test_an_edit_that_removes_an_edge_lands_and_the_pack_still_boots(tmp_path):
    _, files = proposal(tmp_path)
    g = json.loads(files["graph.json"])
    g["edges"] = [e for e in g["edges"] if e != ["fit", "score_test"]]           # the human removes one edge
    edited = {**files, "graph.json": json.dumps(g, indent=1) + "\n"}
    out = tmp_path / "landed"
    run = generate_graph(FakeModel(), out, human=Human([("edit", edited)]), quiet=True)
    assert run.proposals.items["p1"]["decision"] == "edit"
    assert json.loads((out / "graph.json").read_text(encoding="utf-8"))["edges"] == g["edges"]
    assert packs.lint_pack(out, TASK) == []
    inner = checks.run_pack(out, SYNTH, FakeModel(), tmp_path / "run", arm="control")
    assert inner.budget.used == 24 and inner.gate.result is not None
    assert checks.unchanged(out, lambda: checks.run_pack(out, SYNTH, FakeModel(), tmp_path / "run2", arm="control"))


def test_y_lands_a_graph_pack_that_passes_step_04_checks(tmp_path):
    out = tmp_path / "out"
    generate_graph(FakeModel(), out, human=Human(["y"]), quiet=True)
    assert sorted(packs.read_pack(out)) == ["SKILL.md", "graph.json", "loop.json", "paths.json", "schema.json", "tools.md"]
    run = checks.run_pack(out, SYNTH, FakeModel(), tmp_path / "run", arm="control")
    assert len(checks.tool_calls(run, "walk_path")) == 24 and run.gate.result is not None
    assert checks.test_before_freeze(out, SYNTH, tmp_path / "fresh").startswith("Error: the test split is locked")
