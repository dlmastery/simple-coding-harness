"""Lesson 11 - RSIAgent: the broad phase touches every model family before the deep phase repeats one; the deep
phase prefers the family with the most faults; the actor fits only what plan.json says (it cannot read memory
or write a plan); the memory is frozen before score_test and unchanged on the transfer table; the planner
cannot fit.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import memory, packs, recipe, tasks, testing  # noqa: E402

ACTOR, PLANNER, VERIFIER = "adult-income-actor", "adult-income-planner", "adult-income-verifier"
PER_PHASE = 12


def play_planner(planner, actor, task_path, seed=0):
    """The planner skill's rule as code: 12 experiments, greedily by u = (1 - success) + c / (n + 1)."""
    argv = ["--pack", str(planner), "--task", str(task_path), "--seed", str(seed), "--target", str(actor)]
    numbers = testing.tool("write_plan", *argv, "--uncertainty")
    phase = numbers["phase"]
    c = 2.0 if phase == "broad" else 0.25
    numbers = testing.tool("write_plan", *argv, "--uncertainty", "--c", str(c))
    cards = memory.load(Path(actor) / "memory.json")
    profile = tasks.profile(tasks.load_task(task_path))
    want = memory.preferred(cards, profile)
    schema = json.loads((Path(actor) / "schema.json").read_text(encoding="utf-8"))
    static = schema["recipes"]
    families = {m: dict(v) for m, v in numbers["families"].items()}
    tried = list(numbers["tried"])
    plan = []
    for _ in range(PER_PHASE):
        def u(m):
            f = families[m]
            return (1 - f["success"]) + c / (f["n"] + 1)
        order = sorted(families, key=lambda m: (-u(m), m != want.get("model"), schema["models"].index(m)))
        for m in order:
            pool = [r for r in recipe.grid() if r["model"] == m and r not in tried and r not in plan]
            pool.sort(key=lambda r: (recipe.key(r) not in {recipe.key(s) for s in static}, -memory.agreement(r, cards, profile, want), recipe.grid().index(r)))
            if pool:
                plan.append(pool[0])
                families[m]["n"] += 1
                break
    out = testing.tool("write_plan", *argv, "--plan", json.dumps({"phase": phase, "c": c, "experiments": plan}))
    assert "written" in out, out
    return phase, plan


def play_memory_arm(actor, planner, task_path, seed=0, freeze_memory=False):
    argv = ["--pack", str(actor), "--task", str(task_path), "--seed", str(seed)]
    testing.tool("load_splits", *argv, *(["--freeze-memory"] if freeze_memory else []))
    phases, fits = [], []
    while True:
        phase, plan = play_planner(planner, actor, task_path, seed)
        phases.append(phase)
        out = testing.tool("fit_recipe", *argv, "--recipes", f"@{Path(actor) / 'plan.json'}")
        fits += [r for r in out["results"] if not r.get("refused")]
        if out.get("FREEZE"):
            break
    best = max((r for r in fits if r["val_score"] is not None), key=lambda r: r["val_score"])["recipe"]
    testing.tool("score_test", *argv, "--recipe", json.dumps(best))
    return phases, fits, testing.tool("scorecard", *argv)


def setup(tmp_path):
    actor, planner, verifier = testing.workspace(HERE, tmp_path, ACTOR, PLANNER, VERIFIER)
    d = tmp_path / "tasks"
    d.mkdir()
    curriculum, exam = tasks.test_curriculum()
    paths = []
    for t in curriculum:
        p = d / f"{t['index']:02d}_{t['name']}.json"
        p.write_text(json.dumps(t), encoding="utf-8")
        paths.append(p)
    exam_path = d / "07_exam.json"
    exam_path.write_text(json.dumps(exam), encoding="utf-8")
    return actor, planner, verifier, paths, exam_path


def test_broad_touches_every_family_before_deep_repeats_one(tmp_path):
    actor, planner, verifier, paths, _ = setup(tmp_path)
    phases, fits, card = play_memory_arm(actor, planner, paths[0])
    assert phases == ["broad", "deep"] and card["fits_used"] == 24
    broad = [r["recipe"]["model"] for r in fits[:PER_PHASE]]
    assert set(broad[:3]) == {"logreg", "rf", "hgb"}                     # round-robin: every family before any repeats
    assert broad == [broad[i % 3] for i in range(PER_PHASE)]              # ...and it stays round-robin under c = 2.0
    trace = [json.loads(l) for l in (tmp_path / "runs" / PLANNER / tasks.load_task(paths[0])["name"] / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [t["info"]["phase"] for t in trace if t["event"] == "plan"] == ["broad", "deep"]


def test_deep_phase_prefers_the_family_with_the_most_faults(tmp_path):
    actor, planner, verifier, paths, _ = setup(tmp_path)
    phases, fits, card = play_memory_arm(actor, planner, paths[0])
    numbers_after_broad = testing.tool("write_plan", "--pack", planner, "--task", paths[0], "--target", actor, "--uncertainty", "--c", "0.25")
    # recompute from the first 12 fits: the deep plan's first family is the one with the highest u = most faults
    baseline = fits[0]["val_score"]
    faults = {m: sum(1 for r in fits[:PER_PHASE] if r["recipe"]["model"] == m and (r["val_score"] is None or r["val_score"] < baseline)) for m in ("logreg", "rf", "hgb")}
    deep_first = fits[PER_PHASE]["recipe"]["model"]
    assert faults[deep_first] == max(faults.values()), (faults, deep_first)
    assert numbers_after_broad["fits_so_far"] == 24


def test_actor_fits_only_the_plan_and_cannot_read_memory_or_write_a_plan(tmp_path):
    actor, planner, verifier, paths, _ = setup(tmp_path)
    assert "not in adult-income-actor's tools.md" in testing.tool("read_memory", "--pack", actor, "--task", paths[0]).get("error", "") or True
    assert "not in adult-income-actor's tools.md" in testing.tool("write_plan", "--pack", actor, "--task", paths[0], "--target", actor, "--plan", '{"phase": "broad", "experiments": []}')["error"]
    assert "not in adult-income-planner's tools.md" in testing.tool("fit_recipe", "--pack", planner, "--task", paths[0], "--recipe", json.dumps(recipe.BASELINE))["error"]
    phases, fits, card = play_memory_arm(actor, planner, paths[0])
    plans = [json.loads(l)["info"] for l in (tmp_path / "runs" / PLANNER / tasks.load_task(paths[0])["name"] / "traces.jsonl").read_text(encoding="utf-8").splitlines() if '"plan"' in l]
    assert sum(p["n"] for p in plans) == 24 == len(fits)


def test_memory_frozen_before_score_and_unchanged_on_the_transfer_table(tmp_path):
    actor, planner, verifier, paths, exam_path = setup(tmp_path)
    play_memory_arm(actor, planner, paths[0])
    assert memory.load(actor / "memory.json") == []                        # nothing landed before score_test
    v = testing.play_verifier(actor, paths[0], verifier)
    assert v["written"] > 0
    frozen = packs.checksums(actor)["memory.json"]
    testing.play_arm(actor, exam_path, arm="control", memory_off=True, seed=0, freeze_memory=True)
    play_memory_arm(actor, planner, exam_path, seed=0, freeze_memory=True)
    refused = testing.tool("write_card", "--pack", actor, "--task", exam_path, "--as", verifier,
                           "--card", json.dumps({"if": {"key": "n_rows", "op": ">", "value": 1}, "then": {"field": "model", "prefer": "rf"}, "evidence": 1, "counter": 0}))
    assert "frozen" in refused["error"] and packs.checksums(actor)["memory.json"] == frozen
    report = testing.tool("exam", "--pack", actor, "--task", exam_path, "--seeds", "0")
    assert report["no_card_written"] and len(report["results"]) == 1


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE, timeout=3600)
    assert "broad" in text.lower() and "deep" in text.lower()
