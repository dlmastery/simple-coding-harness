"""Lesson 01 - the regular harness: the static walk makes 24 fits in schema order and one test score; the 25th
fit and the second score are refusals (JSON results, not exceptions); a disallowed, malformed or unknown call is
a result too; the trace is append-only; the same pack twice gives the same log. Offline, no agent: the scripts
are the gates, and the test plays the agent by running the same commands SKILL.md names.
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import recipe, testing  # noqa: E402
from _lib.scorecard import SCORECARD_FIELDS  # noqa: E402

PACK = "adult-income-regular"
TASK = testing.task("adult_income")


def walk(tmp_path, name="w"):
    """The procedure of SKILL.md, step by step, on a copy of the pack under a temporary lesson directory."""
    pack = testing.workspace(HERE, tmp_path / name, PACK)
    opened = testing.tool("load_splits", "--pack", pack, "--task", TASK)
    fits = testing.tool("fit_recipe", "--pack", pack, "--task", TASK, "--recipes", f"@{pack / 'schema.json'}")
    best = max((r for r in fits["results"] if r.get("val_score") is not None), key=lambda r: r["val_score"])
    test = testing.tool("score_test", "--pack", pack, "--task", TASK, "--recipe", json.dumps(best["recipe"]))
    saved = testing.tool("save_model", "--pack", pack, "--task", TASK, "--recipe", json.dumps(best["recipe"]))
    card = testing.tool("scorecard", "--pack", pack, "--task", TASK)
    return pack, opened, fits, best, test, saved, card


def test_static_walk_24_fits_in_schema_order_one_test_score(tmp_path):
    pack, opened, fits, best, test, saved, card = walk(tmp_path)
    schema = json.loads((pack / "schema.json").read_text(encoding="utf-8"))
    assert opened["n_fits"] == 24 and opened["profile"]["has_categorical"] == 1
    assert fits["fits_used"] == 24 and fits["FREEZE"] is True and fits["fits_left"] == 0
    assert [r["recipe"] for r in fits["results"]] == schema["recipes"] == recipe.static_list()
    assert fits["results"][0]["recipe"] == schema["baseline"]
    assert "test_score" in test and 0.5 < test["test_score"] < 1.0
    assert "saved" in saved
    assert card["fits_used"] == 24 and card["test_scored_once"] and not card["test_touched_before_freeze"]
    assert set(card) - {"path"} == set(SCORECARD_FIELDS)


def test_25th_fit_and_second_score_are_refusals(tmp_path):
    pack, _, fits, best, test, _, _ = walk(tmp_path)
    again = testing.tool("fit_recipe", "--pack", pack, "--task", TASK, "--recipe", json.dumps(best["recipe"]))
    assert again["refused"] and "fit 25 refused" in again["error"]
    second = testing.tool("score_test", "--pack", pack, "--task", TASK, "--recipe", json.dumps(best["recipe"]))
    assert "scored once already" in second["error"]
    state = json.loads((pack.parents[2] / "runs" / PACK / "adult_income" / "state.json").read_text(encoding="utf-8"))
    assert state["arms"]["memory/0"]["fits_used"] == 24 and state["arms"]["memory/0"]["test_scored"]


def test_score_test_before_freeze_is_refused_by_script_and_hook(tmp_path):
    pack = testing.workspace(HERE, tmp_path / "w", PACK)
    testing.tool("load_splits", "--pack", pack, "--task", TASK)
    testing.tool("fit_recipe", "--pack", pack, "--task", TASK, "--recipe", json.dumps(recipe.BASELINE))
    out = testing.tool("score_test", "--pack", pack, "--task", TASK, "--recipe", json.dumps(recipe.BASELINE))
    assert "locked until FREEZE" in out["error"] and "23 fits remain" in out["error"]
    # the hook, fed the same call the way Claude Code feeds it: exit 2 blocks
    event = {"tool_name": "Bash", "cwd": str(tmp_path / "w"),
             "tool_input": {"command": f"python ../tools/score_test.py --pack .claude/skills/{PACK} --task {TASK} --recipe model=logreg"}}
    proc = subprocess.run([sys.executable, str(testing.HOOK)], input=json.dumps(event), capture_output=True, text=True)
    assert proc.returncode == 2 and "locked until FREEZE" in proc.stderr


def test_bad_calls_are_results_not_crashes(tmp_path):
    pack = testing.workspace(HERE, tmp_path / "w", PACK)
    testing.tool("load_splits", "--pack", pack, "--task", TASK)
    unknown = testing.tool("fit_recipe", "--pack", pack, "--task", TASK, "--recipe", json.dumps({**recipe.BASELINE, "model": "svm"}))
    assert unknown["refused"] and "not one of" in unknown["error"]
    malformed = testing.tool("fit_recipe", "--pack", pack, "--task", TASK, "--recipe", "{not json")
    assert "error" in malformed
    extra = testing.tool("fit_recipe", "--pack", pack, "--task", TASK, "--recipe", json.dumps({**recipe.BASELINE, "note": "x"}))
    assert extra["refused"] and "exactly the fields" in extra["error"]
    disallowed = testing.tool("write_card", "--pack", pack, "--task", TASK, "--as", pack,
                              "--card", json.dumps({"if": {"key": "n_rows", "op": ">", "value": 1}, "then": {"field": "model", "prefer": "rf"}, "evidence": 1, "counter": 0}))
    assert "not in adult-income-regular's tools.md" in disallowed["error"]
    # no fit was spent on any of them
    assert testing.tool("scorecard", "--pack", pack, "--task", TASK)["fits_used"] == 0


def test_trace_is_append_only_and_deterministic(tmp_path):
    pack_a, *_ = walk(tmp_path, "a")
    pack_b, *_ = walk(tmp_path, "b")
    rows = lambda p: [json.loads(l) for l in (p.parents[2] / "runs" / PACK / "adult_income" / "traces.jsonl").read_text(encoding="utf-8").splitlines()]  # noqa: E731
    a, b = rows(pack_a), rows(pack_b)
    strip = lambda r: {k: v for k, v in r.items() if k not in ("t", "seconds")}  # noqa: E731
    assert [strip(r) for r in a] == [strip(r) for r in b]
    assert [r["event"] for r in a] == ["boot"] + ["fit"] * 24 + ["score_test", "save_model"]
    # append-only: a second walk on the same copy adds rows after the first ones, never rewrites them
    n = len(a)
    testing.tool("fit_recipe", "--pack", pack_a, "--task", TASK, "--recipe", json.dumps(recipe.BASELINE))   # refused, no row
    assert rows(pack_a)[:n] == a and len(rows(pack_a)) == n


def test_cli_contract(tmp_path):
    pack = testing.workspace(HERE, tmp_path / "w", PACK)
    out = testing.tool_cli("load_splits", "--pack", pack, "--task", TASK)
    assert out["n_fits"] == 24
    out = testing.tool_cli("fit_recipe", "--pack", pack, "--task", TASK, "--recipe", "model=logreg,hyper=1,scale=yes,encode=onehot,class_weight=none")
    assert out["n"] == 1 and out["val_score"] > 0.5


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE)
    assert "24" in text
