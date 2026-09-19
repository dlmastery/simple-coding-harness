"""Lesson 02 - loop engineering: loop.json is honoured by the scripts (N = 24, the 25th fit refused, score_test
before FREEZE refused); the audit log is written and never read back (no script reads it); the pack is byte-
identical after a run; the loop's order is recipes.json's order; lint_pack refuses a loop that changes N.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import packs, testing  # noqa: E402

PACK = "adult-income-loop"
TASK = testing.task("adult_income")


def run_loop(tmp_path):
    """The procedure of SKILL.md: four slices of six, each followed by its audit lines."""
    pack = testing.workspace(HERE, tmp_path / "w", PACK)
    testing.tool("load_splits", "--pack", pack, "--task", TASK)
    rows = []
    for t0 in range(0, 24, 6):
        out = testing.tool("fit_recipe", "--pack", pack, "--task", TASK, "--recipes", f"@{pack / 'recipes.json'}", "--range", f"{t0}:{t0 + 6}")
        rows += out["results"]
        entries = [{"t": r["t"], "recipe": r["recipe"], "val_score": r["val_score"]} for r in out["results"]]
        logged = testing.tool("write_loop_log", "--pack", pack, "--task", TASK, "--entries", json.dumps(entries))
        assert logged["logged"] == 6
    assert out["FREEZE"] is True
    best = max((r for r in rows if r.get("val_score") is not None), key=lambda r: r["val_score"])
    test = testing.tool("score_test", "--pack", pack, "--task", TASK, "--recipe", json.dumps(best["recipe"]))
    testing.tool("save_model", "--pack", pack, "--task", TASK, "--recipe", json.dumps(best["recipe"]))
    card = testing.tool("scorecard", "--pack", pack, "--task", TASK)
    return pack, rows, best, test, card


def test_loop_json_is_honoured(tmp_path):
    pack, rows, best, test, card = run_loop(tmp_path)
    loop = json.loads((pack / "loop.json").read_text(encoding="utf-8"))
    recipes = json.loads((pack / "recipes.json").read_text(encoding="utf-8"))
    assert loop["kind"] == "counted_while" and loop["N"] == 24 and loop["error_still_counts"]
    assert [r["t"] for r in rows] == list(range(24)) and [r["recipe"] for r in rows] == recipes
    assert card["fits_used"] == 24 and card["test_scored_once"] and "test_score" in test
    # the 25th and the second look: refused
    assert testing.tool("fit_recipe", "--pack", pack, "--task", TASK, "--recipe", json.dumps(recipes[0]))["refused"]
    assert "once already" in testing.tool("score_test", "--pack", pack, "--task", TASK, "--recipe", json.dumps(best["recipe"]))["error"]


def test_score_test_before_freeze_refused(tmp_path):
    pack = testing.workspace(HERE, tmp_path / "w", PACK)
    testing.tool("load_splits", "--pack", pack, "--task", TASK)
    out = testing.tool("fit_recipe", "--pack", pack, "--task", TASK, "--recipes", f"@{pack / 'recipes.json'}", "--range", "0:6")
    assert out["fits_used"] == 6 and "FREEZE" not in out
    refused = testing.tool("score_test", "--pack", pack, "--task", TASK, "--recipe", json.dumps(out["results"][0]["recipe"]))
    assert "18 fits remain" in refused["error"]


def test_audit_log_written_never_read(tmp_path):
    pack, rows, *_ = run_loop(tmp_path)
    log = pack.parents[2] / "runs" / PACK / "adult_income" / "loop_log.jsonl"
    lines = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
    assert [l["t"] for l in lines] == list(range(24)) and all(l["arm"] == "memory" for l in lines)
    # no script reads it back: the string loop_log never appears in a read path of any tool
    readers = [p for p in testing.TOOLS.glob("*.py") if "loop_log" in p.read_text(encoding="utf-8") and p.name != "write_loop_log.py"]
    assert readers == []


def test_pack_is_byte_identical_after_a_run(tmp_path):
    pack = testing.workspace(HERE, tmp_path / "w", PACK)
    before = packs.checksums(pack)
    run_loop(tmp_path)   # a fresh copy under the same tmp_path; run it once more on this one too
    testing.tool("load_splits", "--pack", pack, "--task", TASK)
    testing.tool("fit_recipe", "--pack", pack, "--task", TASK, "--recipes", f"@{pack / 'recipes.json'}", "--range", "0:3")
    assert packs.checksums(pack) == before


def test_lint_refuses_a_changed_loop(tmp_path):
    files = packs.read_pack(HERE / ".claude" / "skills" / PACK)
    loop = json.loads(files["loop.json"])
    loop["N"] = 48
    bad = dict(files, **{"loop.json": json.dumps(loop)})
    out = testing.tool("lint_pack", "--files", json.dumps(bad), "--task", TASK)
    assert not out["ok"] and any("loop.json N 48" in p for p in out["problems"])
    loop["N"] = 24
    loop["exit"] = ["score_test", "FREEZE"]
    bad = dict(files, **{"loop.json": json.dumps(loop)})
    out = testing.tool("lint_pack", "--files", json.dumps(bad), "--task", TASK)
    assert any("exit must be FREEZE then score_test" in p for p in out["problems"])


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE)
    assert "24" in text
