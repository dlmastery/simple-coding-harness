"""Lesson 10 - Dream-RSI: rank_policies makes zero fits (the budget counter proves it); a policy preferring
unvisited recipes scores "unknown" where the log is silent; the winner is proposed as the actor's search-policy
line through the gate and the next lap adds new recipes to the log; a saturated log is reported as such; the
meta pack can patch SKILL.md only and cannot fit.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import packs, recipe, tasks, testing  # noqa: E402

ACTOR, VERIFIER, DREAM = "adult-income", "adult-income-verifier", "adult-income-meta-dream"
POLICIES = "static,obey-memory,random,neighbours-of-top-3,prefer-untried-family"


def problem_one(tmp_path):
    actor, verifier, dream = testing.workspace(HERE, tmp_path, ACTOR, VERIFIER, DREAM)
    d = tmp_path / "tasks"
    d.mkdir()
    curriculum, _ = tasks.test_curriculum()
    paths = []
    for t in curriculum:
        p = d / f"{t['index']:02d}_{t['name']}.json"
        p.write_text(json.dumps(t), encoding="utf-8")
        paths.append(p)
    testing.play_arm(actor, paths[0], arm="control", memory_off=True)
    testing.play_arm(actor, paths[0])
    testing.play_verifier(actor, paths[0], verifier)
    return actor, verifier, dream, paths


def rank(dream, actor, task_path):
    return testing.tool("rank_policies", "--pack", dream, "--task", task_path, "--target", actor, "--policies", POLICIES)


def test_rank_policies_spends_zero_fits_and_marks_unknown(tmp_path):
    actor, verifier, dream, paths = problem_one(tmp_path)
    state_before = json.loads((tmp_path / "runs" / ACTOR / tasks.load_task(paths[0])["name"] / "state.json").read_text(encoding="utf-8"))
    out = rank(dream, actor, paths[0])
    state_after = json.loads((tmp_path / "runs" / ACTOR / tasks.load_task(paths[0])["name"] / "state.json").read_text(encoding="utf-8"))
    assert out["fits_spent"] == 0 and state_before == state_after and out["log_size"] == 24
    by = {e["policy"]: e for e in out["ranking"]}
    assert by["static"]["unknown"] == 0 and by["static"]["visited"] == 24          # the log is the static walk
    assert by["random"]["unknown"] > 0 and by["neighbours-of-top-3"]["unknown"] > 0    # they leave the log (prefer-untried-family walks the static list first: 0 unknown here)
    assert by["obey-memory"]["best_logged_val"] is not None and out["saturated"] is False
    assert out["current_policy"] == "static"
    assert "not in adult-income-meta-dream's tools.md" in testing.tool("fit_recipe", "--pack", dream, "--task", paths[0], "--recipe", json.dumps(recipe.BASELINE))["error"]


def test_winner_becomes_the_policy_line_and_the_next_lap_visits_new_recipes(tmp_path):
    actor, verifier, dream, paths = problem_one(tmp_path)
    out = rank(dream, actor, paths[0])
    winner = out["winner"]
    files = {"SKILL.md": packs.read_pack(actor)["SKILL.md"].replace("Search policy: static", f"Search policy: {winner}")}
    rows = testing.tool("read_traces", "--pack", actor, "--task", paths[0], "--scope", "problem")["rows"]
    evidence = max((r for r in rows if r["val_score"] is not None), key=lambda r: r["val_score"])["recipe"]
    patched = testing.tool("patch_pack", "--pack", dream, "--task", paths[0], "--target", actor, "--files", json.dumps({"SKILL.md": {"after": files["SKILL.md"]}}),
                           "--recipe", json.dumps(evidence), "--summary", f"policy -> {winner}", "--visit", "1")
    assert patched["landed"] and patched["approved_by"] == "gate" and patched["files"] == ["SKILL.md"]
    assert testing.policy_line(actor) == winner != "static"
    logged_before = {recipe.key(r["recipe"]) for r in rows}
    testing.play_arm(actor, paths[1])
    rows2 = testing.tool("read_traces", "--pack", actor, "--task", paths[1], "--scope", "problem")["rows"]
    assert {recipe.key(r["recipe"]) for r in rows2} - logged_before, "the next lap visited nothing new"
    other = testing.tool("patch_pack", "--pack", dream, "--task", paths[1], "--target", actor, "--files", json.dumps({"schema.json": {"after": "{}"}}),
                         "--recipe", json.dumps(evidence), "--summary", "not allowed", "--visit", "2")
    assert "may patch ['SKILL.md'] only" in other["error"]


def test_saturated_log_is_reported(tmp_path):
    actor, verifier, dream, paths = problem_one(tmp_path)
    out = testing.tool("rank_policies", "--pack", dream, "--task", paths[0], "--target", actor, "--policies", "static")
    assert out["saturated"] is True and out["ranking"][0]["unknown"] == 0


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE, timeout=3600)
    assert "fits_spent" in text or "zero fits" in text.lower()
