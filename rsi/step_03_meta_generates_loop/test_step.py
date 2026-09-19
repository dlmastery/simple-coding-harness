"""Lesson 03 - a meta skill generates the loop harness under human approval: the writer cannot fit (tools.md
refusal); the proposal is written and shown before anything lands; "no" leaves the disk untouched, "yes" lands
exactly the proposal, "edit" lands the human's text; the same task twice gives byte-identical proposals; the
generated pack lints, runs like lesson 02 and is unchanged by its run; apply without the user's words is
refused by the script and blocked by the hook.
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import packs, recipe, render, tasks, testing  # noqa: E402

WRITER = "loop-writer"
OUT = "adult-income-loop"


def setup(tmp_path):
    """A temporary lesson with the writer pack; the rendered proposal the agent would write, from the same rule."""
    writer = testing.workspace(HERE, tmp_path, WRITER)
    task_path = writer / "task.json"
    task = tasks.load_task(task_path)
    rendered = tmp_path / "runs" / WRITER / "rendered"
    packs.write_pack(rendered, render.render(writer / "template", task))
    target = tmp_path / ".claude" / "skills" / OUT
    return writer, task_path, rendered, target


def propose(writer, task_path, rendered, target):
    return testing.tool("propose", "--pack", writer, "--task", task_path, "--target", target, "--kind", "pack",
                        "--payload", f"@{rendered}", "--summary", "loop pack for adult_income")


def test_writer_cannot_fit(tmp_path):
    writer, task_path, *_ = setup(tmp_path)
    out = testing.tool("fit_recipe", "--pack", writer, "--task", task_path, "--recipe", json.dumps(recipe.BASELINE))
    assert "not in loop-writer's tools.md" in out["error"]
    out = testing.tool("score_test", "--pack", writer, "--task", task_path, "--recipe", json.dumps(recipe.BASELINE))
    assert "not in loop-writer's tools.md" in out["error"]


def test_rendered_pack_lints_and_the_proposal_is_shown_before_anything_lands(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    assert testing.tool("lint_pack", "--pack", rendered, "--task", task_path)["ok"]
    p = propose(writer, task_path, rendered, target)
    assert p["id"] == "p1" and not target.exists()
    for name in ("SKILL.md", "tools.md", "schema.json", "loop.json", "recipes.json"):
        assert f"### {name}" in p["diff"]
    assert "name: adult-income-loop" in p["diff"] and '"N": 24' in p["diff"]
    record = json.loads(Path(p["file"]).read_text(encoding="utf-8"))
    assert record["decision"] is None and not record["applied"]


def test_no_leaves_the_disk_untouched(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    out = testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "no, not like this")
    assert out["decision"] == "n" and out["landed"] is False and not target.exists()
    again = testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "yes")
    assert "rejected already" in again["error"] and not target.exists()


def test_yes_lands_exactly_the_proposal(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    out = testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "Yes, ship it")
    assert out["landed"] and out["approved_by"] == "human" and out["words"] == "Yes, ship it"
    assert packs.read_pack(target) == packs.read_pack(rendered)
    assert "applied already" in testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "yes")["error"]
    trace = [json.loads(l) for l in (tmp_path / "runs" / WRITER / "adult_income" / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["event"] for r in trace] == ["propose", "apply"] and trace[-1]["info"]["by"] == "human"


def test_edit_lands_the_humans_text(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    edited = packs.read_pack(rendered)
    edited["SKILL.md"] = edited["SKILL.md"].replace("# Loop harness for adult_income", "# Loop harness for adult_income (edited by the human)")
    out = testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "edit", "--edited", json.dumps(edited))
    assert out["decision"] == "edit" and out["landed"]
    assert packs.read_pack(target) == edited
    # an edit that widens the budget does not lint and does not land
    p2_target = tmp_path / ".claude" / "skills" / "other-loop"
    p2 = propose(writer, task_path, rendered, p2_target)
    bad = packs.read_pack(rendered)
    bad["loop.json"] = bad["loop.json"].replace('"N": 24', '"N": 48')
    out = testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p2["id"], "--approved", "edit", "--edited", json.dumps(bad))
    assert "does not lint" in out["error"] and not p2_target.exists()


def test_same_task_twice_gives_byte_identical_proposals(tmp_path):
    a = setup(tmp_path / "a")
    b = setup(tmp_path / "b")
    assert packs.read_pack(a[2]) == packs.read_pack(b[2])
    pa, pb = propose(*a), propose(*b)
    ra = json.loads(Path(pa["file"]).read_text(encoding="utf-8"))["payload"]
    rb = json.loads(Path(pb["file"]).read_text(encoding="utf-8"))["payload"]
    assert ra == rb


def test_generated_pack_runs_like_lesson_02_and_is_unchanged_by_its_run(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "y")
    before = packs.checksums(target)
    task = testing.task("adult_income")
    testing.tool("load_splits", "--pack", target, "--task", task)
    rows = []
    for t0 in range(0, 24, 6):
        out = testing.tool("fit_recipe", "--pack", target, "--task", task, "--recipes", f"@{target / 'recipes.json'}", "--range", f"{t0}:{t0 + 6}")
        rows += out["results"]
        testing.tool("write_loop_log", "--pack", target, "--task", task, "--entries", json.dumps([{"t": r["t"], "val_score": r["val_score"]} for r in out["results"]]))
    assert out["FREEZE"] and [r["recipe"] for r in rows] == recipe.static_list()
    best = max(rows, key=lambda r: r["val_score"] or 0)
    assert "test_score" in testing.tool("score_test", "--pack", target, "--task", task, "--recipe", json.dumps(best["recipe"]))
    assert testing.tool("fit_recipe", "--pack", target, "--task", task, "--recipe", json.dumps(recipe.BASELINE))["refused"]
    assert packs.checksums(target) == before
    # nothing came back to the writer: its run directory holds the proposal and nothing from the generated pack's run
    assert not (tmp_path / "runs" / WRITER / "adult_income" / "state.json").exists()


def test_apply_without_words_is_refused_and_blocked(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    out = testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"])
    assert "needs --approved" in out["error"] and not target.exists()
    event = {"tool_name": "Bash", "cwd": str(tmp_path), "tool_input": {"command": f"python ../tools/apply.py --pack .claude/skills/{WRITER} --task {task_path} --proposal p1"}}
    proc = subprocess.run([sys.executable, str(testing.HOOK)], input=json.dumps(event), capture_output=True, text=True)
    assert proc.returncode == 2 and "--approved" in proc.stderr
    event["tool_input"]["command"] += ' --approved "yes"'
    proc = subprocess.run([sys.executable, str(testing.HOOK)], input=json.dumps(event), capture_output=True, text=True)
    assert proc.returncode == 0


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE)
    assert "p1" in text
