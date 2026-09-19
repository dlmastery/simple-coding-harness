"""Lesson 12 - ModularRSI: contrast names the module whose text differs between the success and the failure; the
patch touches exactly one module file (any other file is refused); validation runs on the pool task's private
split, never on the eval table; the patched module helps both actors (the loser's memory arm beats its control
arm after the patch, as the winner's did before); the meta pack cannot fit.
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import packs, recipe, testing  # noqa: E402

A, B, META, VERIFIER = "actor-a", "actor-b", "modular-meta", "adult-income-verifier"
POOL = sorted((HERE / "pool").glob("*.json"))


def pool_run(tmp_path):
    """Both actors on the pool, memory arms, the verifier after each; the pool copied next to the packs."""
    a, b, meta, verifier = testing.workspace(HERE, tmp_path, A, B, META, VERIFIER)
    shutil.copytree(HERE / "pool", tmp_path / "pool")
    pool = sorted((tmp_path / "pool").glob("*.json"))
    for p in pool:
        for actor in (a, b):
            testing.play_arm(actor, p)
            testing.play_verifier(actor, p, verifier)
    return a, b, meta, verifier, pool


def test_contrast_names_the_differing_module_and_the_winner(tmp_path):
    a, b, meta, verifier, pool = pool_run(tmp_path)
    out = testing.tool("contrast", "--pack", meta, "--task", pool[-1], "--a", a, "--b", b, "--tasks", tmp_path / "pool")
    assert out["modules_differing"] == ["modules/context.md"] and out["module"] == "modules/context.md"
    assert out["fits_spent"] == 0
    decided = [p for p in out["pairs"] if "success" in p]
    assert decided and out["winner"] == B, out["pairs"]          # obey-memory beats static once the cards exist
    assert out["pairs"][0].get("skipped") == "tie"               # pool task 1: empty memory, both static
    assert "Search policy: obey-memory" in out["texts"][B] and "Search policy: static" in out["texts"][A]
    assert "not in modular-meta's tools.md" in testing.tool("fit_recipe", "--pack", meta, "--task", pool[0], "--recipe", json.dumps(recipe.BASELINE))["error"]


def test_patch_touches_exactly_one_module_validated_on_the_pool_and_helps_the_loser(tmp_path):
    a, b, meta, verifier, pool = pool_run(tmp_path)
    out = testing.tool("contrast", "--pack", meta, "--task", pool[-1], "--a", a, "--b", b, "--tasks", tmp_path / "pool")
    loser, winner = (a, b) if out["winner"] == B else (b, a)
    evidence = out["pairs"][-1]["best"][out["winner"]]["recipe"]
    before = packs.checksums(loser)
    other = testing.tool("patch_pack", "--pack", meta, "--task", pool[-1], "--target", loser, "--files", json.dumps({"SKILL.md": {"after": "# no\nafter FREEZE"}}),
                         "--recipe", json.dumps(evidence), "--summary", "not a module", "--visit", "1")
    assert "may patch ['modules/*.md'] only" in other["error"]
    patched = testing.tool("patch_pack", "--pack", meta, "--task", pool[-1], "--target", loser, "--files", json.dumps({out["module"]: {"after": out["texts"][out["winner"]]}}),
                           "--recipe", json.dumps(evidence), "--summary", "context <- winner", "--visit", "2")
    assert patched["landed"] and patched["approved_by"] == "gate" and patched["files"] == ["modules/context.md"]
    after = packs.checksums(loser)
    assert {k for k in after if after[k] != before.get(k)} == {"modules/context.md"}
    assert packs.read_pack(loser)["modules/context.md"] == packs.read_pack(winner)["modules/context.md"]
    # validated on the pool: the gate row names the pool task, and no eval-table run exists anywhere
    trace = [json.loads(l) for l in (tmp_path / "runs" / META / "pool_trees_2" / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(r["event"] == "gate" and r["problem"] == "pool_trees_2" for r in trace)
    assert not any(d.name.startswith(("adult", "breast", "wine", "digits", "synth", "exam")) for d in (tmp_path / "runs").rglob("*") if d.is_dir())
    # the patched module helps the loser too: memory arm vs control arm on the pool task, a fresh seed
    control = testing.play_arm(loser, pool[-1], arm="control", memory_off=True, seed=1)
    mem = testing.play_arm(loser, pool[-1], seed=1)
    assert mem["best_val_score"] >= control["best_val_score"] and mem["wasted_fits"] <= control["wasted_fits"]
    assert mem["best_val_score"] > control["best_val_score"] or mem["wasted_fits"] < control["wasted_fits"]


def test_pool_is_disjoint_from_the_curriculum():
    from _lib import tasks
    names = {t["name"] for t in tasks.all_tasks()}
    seeds = {json.dumps(t["source"], sort_keys=True) for t in tasks.all_tasks()}
    for p in POOL:
        t = tasks.load_task(p)
        assert t["name"] not in names and json.dumps(t["source"], sort_keys=True) not in seeds


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE, timeout=3600)
    assert "context.md" in text
