"""Lesson 15 - AIDE2: the outer loop's keep-if-better is evaluated across every problem of the curriculum under one
metered budget (asserted from the trace: both arms spent the same fits on every problem); a rewrite that wins on
one problem and loses on the set is rejected and rolled back; the three guards are present in every operator
(lint refuses one without the anti-overfitting line); a suspicious score is flagged and re-run; the outer loop
may rewrite operators.md only.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import packs, recipe, tasks, testing  # noqa: E402

INNER, VERIFIER, OUTER = "adult-income-aide", "adult-income-verifier", "aide-outer"
TOP3 = "Improve: expand the top three solutions - fit their untried neighbours, one field away, nearest first."


def setup(tmp_path):
    inner, verifier, outer = testing.workspace(HERE, tmp_path, INNER, VERIFIER, OUTER)
    d = tmp_path / "tasks"
    d.mkdir()
    curriculum, _ = tasks.test_curriculum()
    paths = []
    for t in curriculum:
        p = d / f"{t['index']:02d}_{t['name']}.json"
        p.write_text(json.dumps(t), encoding="utf-8")
        paths.append(p)
    return inner, verifier, outer, paths


def version(inner, verifier, paths, arm, policy):
    for p in paths:
        testing.play_arm(inner, p, arm=arm, policy=policy)
        testing.play_verifier(inner, p, verifier, of=arm)


def rewrite(outer, inner, task, text, visit=1):
    files = packs.read_pack(inner)
    new = files["operators.md"].replace("Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.", text)
    rows = testing.tool("read_traces", "--pack", inner, "--task", task, "--scope", "problem", "--of", "v1")["rows"]
    evidence = max((r for r in rows if r["val_score"] is not None), key=lambda r: r["val_score"])["recipe"]
    return testing.tool("patch_pack", "--pack", outer, "--task", task, "--target", inner, "--files", json.dumps({"operators.md": {"after": new}}),
                        "--recipe", json.dumps(evidence), "--summary", "improve rewrite", "--visit", str(visit))


def test_keep_if_better_across_the_set_under_one_budget(tmp_path):
    inner, verifier, outer, paths = setup(tmp_path)
    version(inner, verifier, paths, "v1", "aide-tree")
    m1 = testing.tool("meter", "--pack", outer, "--task", paths[0], "--target", inner, "--of", "v1")
    assert m1["fits"] == 24 * len(paths) and "no token count" in m1["note"]
    pending = rewrite(outer, inner, paths[0], TOP3)
    assert pending["landed"] == "pending" and pending["version"] == "gen_001" and TOP3 in packs.read_pack(inner)["operators.md"]
    early = testing.tool("meter", "--pack", outer, "--task", paths[0], "--target", inner, "--decide", "--proposal", pending["id"], "--before", "v1", "--after", "v2", "--tasks", tmp_path / "tasks")
    assert "has not run" in early["error"]                       # the rule needs every problem under the same budget
    version(inner, verifier, paths, "v2", "aide-tree-top-3")
    m2 = testing.tool("meter", "--pack", outer, "--task", paths[0], "--target", inner, "--of", "v2")
    assert m2["fits"] == m1["fits"]
    decided = testing.tool("meter", "--pack", outer, "--task", paths[0], "--target", inner, "--decide", "--proposal", pending["id"], "--before", "v1", "--after", "v2", "--tasks", tmp_path / "tasks")
    assert set(decided["gains"]) == {tasks.load_task(p)["name"] for p in paths} and decided["budget"] == {"v1": 144, "v2": 144}
    assert decided["decision"] in ("y", "n") and decided["keep"] == (decided["decision"] == "y")
    if decided["keep"]:
        assert TOP3 in packs.read_pack(inner)["operators.md"]
    else:
        assert TOP3 not in packs.read_pack(inner)["operators.md"]
    again = testing.tool("meter", "--pack", outer, "--task", paths[0], "--target", inner, "--decide", "--proposal", pending["id"], "--before", "v1", "--after", "v2", "--tasks", tmp_path / "tasks")
    assert "already decided" in again["error"]


def test_a_rewrite_that_wins_on_one_problem_and_loses_on_the_set_is_rejected(tmp_path):
    inner, verifier, outer, paths = setup(tmp_path)
    version(inner, verifier, paths, "v1", "aide-tree")
    pending = rewrite(outer, inner, paths[0], TOP3)
    # v2 played with a worse policy everywhere but a lucky first problem: the static walk loses to the tree on most
    version(inner, verifier, paths[:1], "v2", "aide-tree-top-3")
    version(inner, verifier, paths[1:], "v2", "random")
    decided = testing.tool("meter", "--pack", outer, "--task", paths[0], "--target", inner, "--decide", "--proposal", pending["id"], "--before", "v1", "--after", "v2", "--tasks", tmp_path / "tasks")
    assert decided["keep"] is False and decided["losses"] > decided["wins"] or decided["total_gain"] <= 0, decided
    assert TOP3 not in packs.read_pack(inner)["operators.md"] and packs.read_pack(inner)["operators.md"] == packs.read_pack(tmp_path / "runs" / INNER / "versions" / "gen_001")["operators.md"]


def test_guards_in_every_operator_and_only_operators_may_change(tmp_path):
    inner, verifier, outer, paths = setup(tmp_path)
    files = packs.read_pack(inner)
    for section in files["operators.md"].split("\n## ")[1:]:
        assert packs.ANTI_OVERFIT in section
    stripped = files["operators.md"].replace(packs.ANTI_OVERFIT, "", 1)
    out = testing.tool("lint_pack", "--files", json.dumps(dict(files, **{"operators.md": stripped})), "--task", paths[0])
    assert any("lacks the anti-overfitting line" in p for p in out["problems"])
    testing.play_arm(inner, paths[0], arm="v1", policy="aide-tree")
    other = testing.tool("patch_pack", "--pack", outer, "--task", paths[0], "--target", inner, "--files", json.dumps({"SKILL.md": {"after": files["SKILL.md"] + "\n"}}),
                         "--recipe", json.dumps(recipe.BASELINE), "--summary", "no", "--visit", "1")
    assert "may patch ['operators.md'] only" in other["error"]
    assert "not in aide-outer's tools.md" in testing.tool("fit_recipe", "--pack", outer, "--task", paths[0], "--recipe", json.dumps(recipe.BASELINE))["error"]


def test_suspicious_score_is_flagged_and_rerun(tmp_path):
    inner, verifier, outer, paths = setup(tmp_path)
    # a noiseless linear table: the baseline scores 0.9998, at or above the 0.999 bar, so it is flagged
    saturated = tmp_path / "tasks" / "99_saturated.json"
    saturated.write_text(json.dumps(tasks.synth_task("saturated", 9, n=2000, seed=5, shift=1, imbalance=0.4, noise=0.0)), encoding="utf-8")
    argv = ["--pack", str(inner), "--task", str(saturated), "--arm", "v1"]
    testing.tool("load_splits", *argv)
    first = testing.tool("fit_recipe", *argv, "--recipe", json.dumps(recipe.BASELINE))
    assert first["val_score"] >= 0.999 and first.get("suspicious") is True
    rerun = testing.tool("fit_recipe", *argv, "--recipe", json.dumps(recipe.BASELINE))       # the review operator: fit it again
    assert rerun["n"] == 2 and rerun["val_score"] == first["val_score"]
    trace = [json.loads(l) for l in (tmp_path / "runs" / INNER / "saturated" / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["info"]["suspicious"] for r in trace if r["event"] == "fit"][0] is True
    saturated.unlink()


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE, timeout=3600)
    assert "keep" in text.lower()
