"""Step 01 - the fake follows SKILL.md; the budget, the locked test and execute() are gates; the log is append-only."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import checks, harness, recipe, steps, tasks  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import execute  # noqa: E402
from common.trace import TraceLog  # noqa: E402

PACK = "adult-income-regular"
TASK = tasks.test_curriculum()[0][0]


def booted(tmp_path, name="a"):
    pack = steps.workspace(HERE, PACK, into=tmp_path / name)
    return checks.run_pack(pack, TASK, FakeModel(), tmp_path / name / "run", arm="control"), pack


def test_fake_follows_skill_md_24_fits_in_schema_order_best_val_one_test(tmp_path):
    run, pack = booted(tmp_path)
    schema = json.loads((pack / "schema.json").read_text(encoding="utf-8"))
    assert [r["recipe"] for r in run.fits] == schema["recipes"] == recipe.static_list()
    assert schema["recipes"][0] == schema["baseline"]                       # the first recipe is the baseline
    best = max(run.fits, key=lambda r: r["val_score"])
    assert run.gate.result["recipe"] == best["recipe"]                      # best-val pick
    assert [n for n, _ in checks.tool_calls(run)].count("score_test") == 1
    assert checks.tool_calls(run, "save_model")[0][1]["recipe"] == best["recipe"]
    assert run.messages[-1]["role"] == "assistant" and "Done" in run.messages[-1]["content"]


def test_25th_fit_and_second_score_test_are_error_results(tmp_path):
    run, _ = booted(tmp_path)
    gate = checks.budget_and_gate(run)
    assert gate["fits_used"] == 24
    assert gate["fit_25"].startswith("Error: budget of 24 fits used")
    assert gate["second_test"].startswith("Error: the test split was scored once already")
    assert gate["test_scored_once"]


def test_score_test_before_freeze_is_refused(tmp_path):
    pack = steps.workspace(HERE, PACK, into=tmp_path / "p")
    assert checks.test_before_freeze(pack, TASK, tmp_path / "p" / "run").startswith("Error: the test split is locked until FREEZE")


def test_unknown_disallowed_malformed_calls_are_errors_and_the_loop_continues(tmp_path):
    pack = steps.workspace(HERE, PACK, into=tmp_path / "p")
    run = harness.boot(pack, TASK, run_dir=tmp_path / "p" / "run", arm="control")
    assert execute(run, checks.call("write_card", card={})).startswith("Error: write_card is not in this pack's tools.md")
    assert execute(run, checks.call("no_such_tool")).startswith("Error: no_such_tool is not in this pack's tools.md")
    assert execute(run, {"id": "x", "name": "fit_recipe", "arguments": "{not json"}).startswith("Error: the arguments of fit_recipe are not a JSON object")
    assert execute(run, checks.call("fit_recipe", recipe={"model": "svm"})).startswith("Error: a recipe has exactly the fields")
    assert run.budget.used == 0                                              # none of those cost a fit

    calls = iter([checks.call("no_such_tool"), checks.call("fit_recipe", recipe={"model": "svm"})])

    def clumsy(messages, tools):                                             # two bad calls, then the fake takes over
        try:
            return {"content": None, "tool_calls": [next(calls)]}
        except StopIteration:
            return FakeModel()(messages, tools)

    harness.run(run, clumsy)
    errors = [m["content"] for m in run.messages if m["role"] == "tool" and m["content"].startswith("Error:")]
    assert len(errors) == 2 and run.budget.used == 24 and run.gate.result is not None   # the loop went on to the end


def test_trace_is_append_only(tmp_path):
    run, _ = booted(tmp_path)
    log = TraceLog(run.trace.path)
    n = len(log.rows())
    assert not any(hasattr(log, m) for m in ("rewrite", "delete", "truncate", "write"))
    log.append(event="note", problem="x")
    assert len(log.rows()) == n + 1 and log.rows()[:n] == run.trace.rows()[:n]
    assert [r["event"] for r in run.trace.rows(problem=TASK["name"])][:2] == ["boot", "fit"]


def test_same_pack_twice_gives_the_same_log(tmp_path):
    a, _ = booted(tmp_path, "a")
    b, _ = booted(tmp_path, "b")
    assert checks.fit_sequence(a) == checks.fit_sequence(b)
    assert a.gate.result == b.gate.result


def test_pack_is_byte_identical_after_a_run(tmp_path):
    pack = steps.workspace(HERE, PACK, into=tmp_path / "p")
    assert checks.unchanged(pack, lambda: checks.run_pack(pack, TASK, FakeModel(), tmp_path / "p" / "run", arm="control"))
