"""Lesson 14 - the Darwin Goedel Machine lineage: the archive holds every variant with its held-out score; the
parent is chosen from the archive by score, not always the latest; a rewrite that lowers the private score
never becomes a parent (the gate rolls it back before it runs); SKILL.md and loop.json are the only
self-modified files; approval: both puts the human after the gate.
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import packs, recipe, tasks, testing  # noqa: E402

ACTOR, VERIFIER, META = "adult-income", "adult-income-verifier", "dgm-meta"


def setup(tmp_path):
    actor, verifier, meta = testing.workspace(HERE, tmp_path, ACTOR, VERIFIER, META)
    held = sorted((meta / "held-out").glob("*.json"))
    return actor, verifier, meta, held


def benchmark(actor, verifier, held, seed):
    for tp in held:
        testing.play_arm(actor, tp, arm="control", memory_off=True, seed=seed)
        testing.play_arm(actor, tp, seed=seed)
        testing.play_verifier(actor, tp, verifier, seed=seed)


def archive(meta, actor, task, action, seed=0, **kw):
    argv = ["--pack", str(meta), "--task", str(task), "--target", str(actor), "--action", action, "--seed", str(seed)]
    for k, v in kw.items():
        argv += [f"--{k.replace('_', '-')}", str(v)]
    return testing.tool("archive", *argv)


def rewrite(meta, actor, task, policy, evidence, visit, words=None):
    files = packs.read_pack(actor)
    current = testing.policy_line(actor)
    loop = json.loads(files["loop.json"])
    loop["policy"] = policy
    payload = {"SKILL.md": {"after": files["SKILL.md"].replace(f"Search policy: {current}", f"Search policy: {policy}")},
               "loop.json": {"after": json.dumps(loop, indent=1) + "\n"}}
    out = testing.tool("patch_pack", "--pack", meta, "--task", task, "--target", actor, "--files", json.dumps(payload), "--recipe", json.dumps(evidence),
                       "--summary", f"-> {policy}", "--visit", str(visit))
    if words and out.get("landed") == "pending":
        out = testing.tool("patch_pack", "--pack", meta, "--task", task, "--target", actor, "--proposal", out["id"], "--approved", words)
    return out


def best_recipe(actor, task, seed):
    rows = testing.tool("read_traces", "--pack", actor, "--task", task, "--seed", str(seed), "--scope", "problem")["rows"]
    return max((r for r in rows if r["val_score"] is not None), key=lambda r: r["val_score"])["recipe"]


def test_archive_holds_every_variant_and_the_parent_is_by_score_not_recency(tmp_path):
    actor, verifier, meta, held = setup(tmp_path)
    benchmark(actor, verifier, held, seed=1)
    g1 = archive(meta, actor, held[-1], "add", seed=1, label="gen1-static", held_out=meta / "held-out")
    assert g1["variants"][0]["label"] == "gen1-static" and g1["variants"][0]["policy"] == "static"
    assert (tmp_path / "runs" / ACTOR / "archive" / "gen1-static" / "SKILL.md").exists()
    # generation 2: obey-memory, kept by the gate and the human, run on the benchmark, archived
    out = rewrite(meta, actor, held[-1], "obey-memory", best_recipe(actor, held[-1], 1), visit=1, words="approve")
    assert out["landed"] and out["approved_by"] == "human" and sorted(out["files"]) == ["SKILL.md", "loop.json"]
    benchmark(actor, verifier, held, seed=2)
    g2 = archive(meta, actor, held[-1], "add", seed=2, label="gen2-obey-memory", parent="gen1-static", held_out=meta / "held-out")
    scores = {e["label"]: e["held_out"] for e in g2["variants"]}
    assert set(scores) == {"gen1-static", "gen2-obey-memory"} and all(isinstance(v, float) for v in scores.values())
    parent = archive(meta, actor, held[-1], "parent")
    assert parent["parent"] == max(scores, key=lambda k: (scores[k], k == "gen1-static"))
    # plant a newer, worse variant: the parent rule ignores it
    index = tmp_path / "runs" / ACTOR / "archive" / "archive.json"
    entries = json.loads(index.read_text(encoding="utf-8"))
    shutil.copytree(tmp_path / "runs" / ACTOR / "archive" / "gen1-static", tmp_path / "runs" / ACTOR / "archive" / "gen3-worse")
    entries.append(dict(entries[0], label="gen3-worse", held_out=-1.0, policy="random"))
    index.write_text(json.dumps(entries), encoding="utf-8")
    parent = archive(meta, actor, held[-1], "parent")
    assert parent["latest"] == "gen3-worse" and parent["parent"] != "gen3-worse" and parent["is_latest"] is False
    restored = archive(meta, actor, held[-1], "restore", label=parent["parent"])
    assert restored["checksums"]["SKILL.md"] == entries[[e["label"] for e in entries].index(parent["parent"])]["checksums"]["SKILL.md"]


def test_rewrite_that_lowers_the_private_score_is_rolled_back_and_never_archived(tmp_path):
    actor, verifier, meta, held = setup(tmp_path)
    benchmark(actor, verifier, held, seed=1)
    archive(meta, actor, held[-1], "add", seed=1, label="gen1-static", held_out=meta / "held-out")
    before = packs.checksums(actor)
    worse = {"model": "logreg", "hyper": 0.25, "scale": "no", "encode": "ordinal", "class_weight": "balanced"}
    out = rewrite(meta, actor, held[-1], "random", worse, visit=1)
    assert out["decision"] == "n" and out["approved_by"] == "gate" and out["landed"] is False and out["gate"]["keep"] is False
    assert packs.checksums(actor) == before
    labels = [e["label"] for e in archive(meta, actor, held[-1], "list")["variants"]]
    assert labels == ["gen1-static"]


def test_only_skill_and_loop_are_self_modified_and_the_human_comes_after_the_gate(tmp_path):
    actor, verifier, meta, held = setup(tmp_path)
    benchmark(actor, verifier, held, seed=1)
    evidence = best_recipe(actor, held[-1], 1)
    other = testing.tool("patch_pack", "--pack", meta, "--task", held[-1], "--target", actor, "--files", json.dumps({"schema.json": {"after": "{}"}}),
                         "--recipe", json.dumps(evidence), "--summary", "no", "--visit", "1")
    assert "may patch ['SKILL.md', 'loop.json'] only" in other["error"]
    before = packs.checksums(actor)
    pending = rewrite(meta, actor, held[-1], "obey-memory", evidence, visit=2)
    assert pending["landed"] == "pending" and pending["gate"]["keep"] and pending["version"] == "gen_001"
    no = testing.tool("patch_pack", "--pack", meta, "--task", held[-1], "--target", actor, "--proposal", pending["id"], "--approved", "no thanks")
    assert no["decision"] == "n" and no["rolled_back_to"] == "gen_001" and packs.checksums(actor) == before
    yes = rewrite(meta, actor, held[-1], "obey-memory", evidence, visit=3, words="yes")
    after = packs.checksums(actor)
    assert yes["landed"] and {k for k in after if after[k] != before.get(k)} == {"SKILL.md", "loop.json"}
    assert json.loads(packs.read_pack(actor)["loop.json"])["policy"] == "obey-memory" == testing.policy_line(actor)
    assert "not in dgm-meta's tools.md" in testing.tool("score_test", "--pack", meta, "--task", held[-1], "--recipe", json.dumps(recipe.BASELINE))["error"]


def test_held_out_is_disjoint_from_the_curriculum():
    names = {t["name"] for t in tasks.all_tasks()}
    sources = {json.dumps(t["source"], sort_keys=True) for t in tasks.all_tasks()}
    for p in sorted((HERE / ".claude" / "skills" / META / "held-out").glob("*.json")):
        t = tasks.load_task(p)
        assert t["name"] not in names and json.dumps(t["source"], sort_keys=True) not in sources


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE, timeout=3600)
    assert "archive" in text.lower()
