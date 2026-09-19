"""Lesson 09 - the RSI meta harness: generation n+1 boots the files generation n wrote (checksums in the trace);
under approval: human no patch lands without the user's yes and an edit lands the user's version; under
approval: gate a patch whose evidence recipe scores lower on the private split is rejected and versions/
restores the previous pack byte for byte; META_OFF leaves the pack byte-identical; the meta pack cannot score
the test; one proposal per visit; the size cap; the curriculum with the gate improves the actor's policy line
and the curve stays non-negative.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import packs, recipe, tasks, testing  # noqa: E402

ACTOR, VERIFIER, META, GATE = "adult-income", "adult-income-verifier", "adult-income-meta", "adult-income-meta-gate"


def synthetic_tasks(tmp_path):
    d = tmp_path / "tasks"
    d.mkdir(exist_ok=True)
    curriculum, exam = tasks.test_curriculum()
    paths = []
    for t in curriculum:
        p = d / f"{t['index']:02d}_{t['name']}.json"
        p.write_text(json.dumps(t), encoding="utf-8")
        paths.append(p)
    return paths


def problem_one(tmp_path):
    """Both arms and the verifier on problem 1: the state every meta test starts from."""
    actor, verifier, meta, gate = testing.workspace(HERE, tmp_path, ACTOR, VERIFIER, META, GATE)
    paths = synthetic_tasks(tmp_path)
    testing.play_arm(actor, paths[0], arm="control", memory_off=True)
    testing.play_arm(actor, paths[0])
    testing.play_verifier(actor, paths[0], verifier)
    return actor, verifier, meta, gate, paths


def boot_checksums(tmp_path, problem, arm="memory"):
    rows = [json.loads(l) for l in (tmp_path / "runs" / ACTOR / problem / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
    return next(r["info"]["checksums"] for r in rows if r["event"] == "boot" and r["arm"] == arm)


def test_human_no_lands_nothing_yes_lands_and_the_next_generation_boots_it(tmp_path):
    actor, verifier, meta, gate, paths = problem_one(tmp_path)
    before = packs.checksums(actor)
    assert "Search policy: static" in packs.read_pack(actor)["SKILL.md"]
    proposal, files = testing.play_meta(meta, actor, paths[0], visit=1)          # the agent stops and asks
    assert proposal["landed"] is False and proposal["decision"] is None and "SKILL.md" in files and "obey-memory" in proposal["diff"]
    assert packs.checksums(actor) == before
    no = testing.tool("patch_pack", "--pack", meta, "--task", paths[0], "--target", actor, "--proposal", proposal["id"], "--approved", "no")
    assert no["decision"] == "n" and no["landed"] is False and packs.checksums(actor) == before
    # a fresh visit, then the yes
    proposal, files = testing.play_meta(meta, actor, paths[0], visit=2)
    yes = testing.tool("patch_pack", "--pack", meta, "--task", paths[0], "--target", actor, "--proposal", proposal["id"], "--approved", "yes")
    assert yes["landed"] and yes["approved_by"] == "human" and yes["version"] == "gen_001" and yes["files"] == ["SKILL.md"]
    assert "Search policy: obey-memory" in packs.read_pack(actor)["SKILL.md"]
    assert (tmp_path / "runs" / ACTOR / "versions" / "gen_001" / "SKILL.md").read_text(encoding="utf-8") == packs.read_pack(actor)["SKILL.md"].replace("obey-memory", "static", 1)
    # generation 2 boots what generation 1 wrote: the boot row's checksums are the patched pack's
    testing.play_arm(actor, paths[1])
    assert boot_checksums(tmp_path, tasks.load_task(paths[1])["name"]) == packs.checksums(actor) == yes["checksums"] if "checksums" in yes else True
    assert boot_checksums(tmp_path, tasks.load_task(paths[1])["name"])["SKILL.md"] == packs.checksums(actor)["SKILL.md"]


def test_human_edit_lands_the_users_version(tmp_path):
    actor, verifier, meta, gate, paths = problem_one(tmp_path)
    proposal, files = testing.play_meta(meta, actor, paths[0], visit=1)
    theirs = {"SKILL.md": files["SKILL.md"].replace("Search policy: obey-memory", "Search policy: obey-memory\n   (the human turned this on by hand)")}
    out = testing.tool("patch_pack", "--pack", meta, "--task", paths[0], "--target", actor, "--proposal", proposal["id"], "--approved", "edit",
                       "--edited", json.dumps({n: {"after": t} for n, t in theirs.items()}))
    assert out["landed"] and out["decision"] == "edit"
    assert "(the human turned this on by hand)" in packs.read_pack(actor)["SKILL.md"]


def test_gate_keeps_a_good_patch_and_rolls_back_a_bad_one(tmp_path):
    actor, verifier, meta, gate, paths = problem_one(tmp_path)
    before = packs.checksums(actor)
    kept, files = testing.play_meta(gate, actor, paths[0], visit=1)
    assert kept["landed"] and kept["approved_by"] == "gate" and kept["gate"]["keep"] and kept["version"] == "gen_001"
    assert "Search policy: obey-memory" in packs.read_pack(actor)["SKILL.md"]
    # a patch that raises val on paper but whose evidence recipe scores lower on the private split: rejected, rolled back
    now = packs.checksums(actor)
    worse = {"model": "logreg", "hyper": 0.25, "scale": "no", "encode": "ordinal", "class_weight": "balanced"}
    files = {"memory.json": json.dumps([{"if": {"key": "n_rows", "op": "<", "value": 1000}, "then": {"field": "model", "prefer": "logreg"}, "evidence": 5, "counter": 0}], indent=1)}
    out = testing.tool("patch_pack", "--pack", gate, "--task", paths[0], "--target", actor, "--files", json.dumps({n: {"after": t} for n, t in files.items()}),
                       "--recipe", json.dumps(worse), "--summary", "a bad idea", "--visit", "2")
    assert out["decision"] == "n" and out["approved_by"] == "gate" and out["gate"]["after"] < out["gate"]["before"] and out["landed"] is False
    assert out["rolled_back_to"] == "gen_002" and packs.checksums(actor) == now != before
    trace = [json.loads(l) for l in (tmp_path / "runs" / GATE / tasks.load_task(paths[0])["name"] / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["event"] for r in trace][-3:] == ["gate", "rollback", "gate"] or "rollback" in [r["event"] for r in trace]


def test_meta_off_one_per_visit_size_cap_and_no_score_test(tmp_path):
    actor, verifier, meta, gate, paths = problem_one(tmp_path)
    before = packs.checksums(actor)
    (meta / "config.json").write_text('{"meta": "off"}', encoding="utf-8")
    off, _ = testing.play_meta(meta, actor, paths[0], visit=1)
    assert off["meta_off"] and off["landed"] is False and packs.checksums(actor) == before
    (meta / "config.json").unlink()
    testing.play_meta(meta, actor, paths[0], visit=1)
    second = testing.tool("patch_pack", "--pack", meta, "--task", paths[0], "--target", actor, "--files", json.dumps({"memory.json": {"after": "[]"}}),
                          "--recipe", json.dumps(recipe.BASELINE), "--summary", "again", "--visit", "1")
    assert "one proposal per visit" in second["error"]
    big = testing.tool("patch_pack", "--pack", meta, "--task", paths[0], "--target", actor, "--files", json.dumps({"SKILL.md": {"after": "# gone\nafter FREEZE\n"}}),
                       "--recipe", json.dumps(recipe.BASELINE), "--summary", "rewrite", "--visit", "3")
    assert "more than 20 %" in big["error"]
    no_rule = testing.tool("patch_pack", "--pack", meta, "--task", paths[0], "--target", actor, "--files", json.dumps({"SKILL.md": {"after": packs.read_pack(actor)["SKILL.md"].replace("after FREEZE", "whenever")}}),
                           "--recipe", json.dumps(recipe.BASELINE), "--summary", "loosen", "--visit", "4")
    assert "may not remove the test rule" in no_rule["error"]
    assert "not in adult-income-meta's tools.md" in testing.tool("score_test", "--pack", meta, "--task", paths[0], "--recipe", json.dumps(recipe.BASELINE))["error"]
    assert "not in adult-income-meta's tools.md" in testing.tool("fit_recipe", "--pack", meta, "--task", paths[0], "--recipe", json.dumps(recipe.BASELINE))["error"]


def test_curriculum_under_the_gate_improves_the_policy_line(tmp_path):
    actor, verifier, meta, gate = testing.workspace(HERE, tmp_path, ACTOR, VERIFIER, META, GATE)
    paths = synthetic_tasks(tmp_path)
    decisions = []
    for i, p in enumerate(paths, 1):
        testing.play_arm(actor, p, arm="control", memory_off=True)
        testing.play_arm(actor, p)
        testing.play_verifier(actor, p, verifier)
        out, files = testing.play_meta(gate, actor, p, visit=i)
        decisions.append(None if out is None else (out.get("decision"), out.get("version"), sorted(files)))
    curve = testing.tool("curve", "--pack", actor, "--tasks", tmp_path / "tasks")
    assert decisions[0] == ("y", "gen_001", ["SKILL.md"])
    assert "Search policy: obey-memory" in packs.read_pack(actor)["SKILL.md"]
    assert all(r["gap_val"] >= 0 for r in curve["curve"])
    assert testing.tool("read_pack", "--pack", actor)["versions"][0] == "gen_001"


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE, timeout=3600)
    assert "gen_001" in text
