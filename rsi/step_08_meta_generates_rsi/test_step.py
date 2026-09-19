"""Lesson 08 - a meta skill generates the RSI harness under human approval: the proposal contains the verifier
contract verbatim and is refused by lint_pack when it is missing; the generated packs pass lesson 06's checks
(cards written after a run, MEMORY_OFF reproduces the control numbers, forbid cards enforced); "no" lands
nothing; the writer cannot fit or write a card; the two packs land side by side under .claude/skills without
touching the writer.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import memory, packs, recipe, render, tasks, testing  # noqa: E402

WRITER = "rsi-writer"


def setup(tmp_path):
    writer = testing.workspace(HERE, tmp_path, WRITER)
    task_path = writer / "task.json"
    rendered = tmp_path / "runs" / WRITER / "rendered"
    packs.write_pack(rendered, render.render(writer / "template", tasks.load_task(task_path), render.RSI_SUBDIRS))
    return writer, task_path, rendered, tmp_path / ".claude" / "skills"


def propose(writer, task_path, payload, target):
    return testing.tool("propose", "--pack", writer, "--task", task_path, "--target", target, "--kind", "pack",
                        "--payload", payload if isinstance(payload, str) else f"@{payload}", "--summary", "RSI harness for adult_income")


def test_proposal_carries_the_contract_and_is_refused_without_it(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    assert p["diff"].startswith("### verifier contract (the acceptance rule you are approving)\n" + packs.VERIFIER_CONTRACT)
    files = packs.read_pack(rendered)
    assert "adult-income/SKILL.md" in files and "adult-income-verifier/SKILL.md" in files
    stripped = dict(files, **{"adult-income-verifier/SKILL.md": files["adult-income-verifier/SKILL.md"].replace(packs.VERIFIER_CONTRACT, "")})
    out = propose(writer, task_path, json.dumps(stripped), target)
    assert "must state the verifier contract verbatim" in out["error"]


def test_no_lands_nothing_and_the_writer_cannot_fit_or_write_a_card(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    out = testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "no")
    assert out["landed"] is False and sorted(d.name for d in target.iterdir()) == [WRITER]
    assert "not in rsi-writer's tools.md" in testing.tool("fit_recipe", "--pack", writer, "--task", task_path, "--recipe", json.dumps(recipe.BASELINE))["error"]
    assert "not in rsi-writer's tools.md" in testing.tool("write_card", "--pack", writer, "--task", task_path, "--as", writer, "--card", "{}")["error"]


def test_generated_packs_land_side_by_side_and_pass_lesson_06_checks(tmp_path):
    writer, task_path, rendered, target = setup(tmp_path)
    p = propose(writer, task_path, rendered, target)
    out = testing.tool("apply", "--pack", writer, "--task", task_path, "--proposal", p["id"], "--approved", "yes, approve the mechanism")
    assert out["landed"] and sorted(out["files"])[:2] == ["adult-income-verifier/SKILL.md", "adult-income-verifier/memory.schema.json"]
    actor, verifier = target / "adult-income", target / "adult-income-verifier"
    assert actor.exists() and verifier.exists() and (target / WRITER / "SKILL.md").exists()     # the writer survived
    assert memory.load(actor / "memory.json") == []
    # lesson 06's checks on the generated packs
    t1, t2 = testing.task("adult_income"), testing.task("breast_cancer")
    control = testing.play_arm(actor, t1, arm="control", memory_off=True)
    mem = testing.play_arm(actor, t1)
    assert mem["best_val_score"] == control["best_val_score"] == 0.9172
    v = testing.play_verifier(actor, t1, verifier)
    assert v["written"] >= 3 and v["by"] == "adult-income-verifier"
    assert len(memory.load(actor / "memory.json")) >= 3
    mem2 = testing.play_arm(actor, t2)
    control2 = testing.play_arm(actor, t2, arm="control", memory_off=True)
    assert mem2["best_val_score"] >= control2["best_val_score"] and mem2["cards_active"] >= 1
    forbid = {"if": {"key": "has_categorical", "op": "==", "value": 1}, "then": {"field": "encode", "forbid": "ordinal"}, "evidence": 1, "counter": 0}
    testing.tool("write_card", "--pack", actor, "--task", t1, "--as", verifier, "--card", json.dumps(forbid))
    refused = testing.tool("fit_recipe", "--pack", actor, "--task", t1, "--recipe", json.dumps(dict(recipe.BASELINE, encode="ordinal")))
    assert refused["refused"] and "forbid card" in refused["error"]
    # nothing came back to the writer
    assert sorted(p.name for p in (tmp_path / "runs" / WRITER / "adult_income").iterdir()) == ["proposals", "traces.jsonl"]


def test_same_task_twice_gives_the_same_proposal(tmp_path):
    a, b = setup(tmp_path / "a"), setup(tmp_path / "b")
    assert packs.read_pack(a[2]) == packs.read_pack(b[2])
    pa, pb = propose(*a[:2], a[2], a[3]), propose(*b[:2], b[2], b[3])
    assert json.loads(Path(pa["file"]).read_text(encoding="utf-8"))["payload"] == json.loads(Path(pb["file"]).read_text(encoding="utf-8"))["payload"]


def test_generated_actor_equals_lesson_07_actor():
    task = tasks.load_task(HERE / ".claude" / "skills" / WRITER / "task.json")
    files = render.render(HERE / ".claude" / "skills" / WRITER / "template", task, render.RSI_SUBDIRS)
    reference = packs.read_pack(HERE.parent / "step_07_proof" / ".claude" / "skills" / "adult-income")
    generated, ref = json.loads(files["adult-income/schema.json"]), json.loads(reference["schema.json"])
    assert {k: v for k, v in generated.items() if k != "task"} == {k: v for k, v in ref.items() if k != "task"}
    assert files["adult-income/memory.schema.json"] == reference["memory.schema.json"]
    assert packs.VERIFIER_CONTRACT in files["adult-income-verifier/SKILL.md"]


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE)
    assert "contract" in text.lower()
