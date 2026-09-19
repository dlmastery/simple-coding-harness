"""Lesson 16 - MetaSkill-Evolve: task skills change every problem (the fast loop, under the gate) and meta-skills
only every k problems (the slow loop, with the human) - counted from the traces; a meta-skill change never lands
without the human's approval; the fast loop cannot touch roles/ and the slow loop cannot touch the actor; the
meta pack's version history is a directory you can diff; the fast loop boots what the slow loop wrote.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import packs, recipe, tasks, testing  # noqa: E402

ACTOR, VERIFIER, FAST, SLOW = "adult-income", "adult-income-verifier", "task-skills-meta", "meta-evolver"


def setup(tmp_path):
    actor, verifier, fast, slow = testing.workspace(HERE, tmp_path, ACTOR, VERIFIER, FAST, SLOW)
    d = tmp_path / "tasks"
    d.mkdir()
    curriculum, _ = tasks.test_curriculum()
    paths = []
    for t in curriculum:
        p = d / f"{t['index']:02d}_{t['name']}.json"
        p.write_text(json.dumps(t), encoding="utf-8")
        paths.append(p)
    k = json.loads((slow / "config.json").read_text(encoding="utf-8"))["k"]
    return actor, verifier, fast, slow, paths, k


def number(text, label):
    return int(re.search(rf"{label}: (\d+)", text).group(1))


def play_slow(slow, fast, actor, task_path, index, k, words):
    """The slow loop's rule: one role file, one line, with the human's words (None = ask and stop)."""
    if index % k:
        return None
    roles = packs.read_pack(fast)
    curve = testing.tool("curve", "--pack", actor, "--tasks", task_path.parent)
    done = [r for r in curve["curve"] if not r.get("missing")][-k:]
    adding = sum(r["cards_added"] for r in done) > 0
    growing = len(done) >= 2 and done[-1]["gap_val"] > done[0]["gap_val"]
    if adding and not growing:
        old = number(roles["roles/proposer.md"], "Cards per visit")
        files = {"roles/proposer.md": roles["roles/proposer.md"].replace(f"Cards per visit: {old}", f"Cards per visit: {old + 1}")}
    elif testing.policy_line(actor) == "static":
        old = number(roles["roles/allocator.md"], "Policy flip threshold")
        files = {"roles/allocator.md": roles["roles/allocator.md"].replace(f"Policy flip threshold: {old}", f"Policy flip threshold: {old - 1}")}
    else:
        return None
    rows = testing.tool("read_traces", "--pack", actor, "--task", task_path, "--scope", "problem")["rows"]
    evidence = max((r for r in rows if r["val_score"] is not None), key=lambda r: r["val_score"])["recipe"]
    out = testing.tool("patch_pack", "--pack", slow, "--task", task_path, "--target", fast, "--files", json.dumps({n: {"after": t} for n, t in files.items()}),
                       "--recipe", json.dumps(evidence), "--summary", "one role line", "--visit", str(index // k))
    if words is None or "error" in out:
        return out
    return testing.tool("patch_pack", "--pack", slow, "--task", task_path, "--target", fast, "--proposal", out["id"], "--approved", words)


def test_two_timescales_counted_from_the_traces(tmp_path):
    actor, verifier, fast, slow, paths, k = setup(tmp_path)
    fast_landed, slow_visits = [], []
    for i, p in enumerate(paths, 1):
        testing.play_arm(actor, p, arm="control", memory_off=True)
        testing.play_arm(actor, p)
        testing.play_verifier(actor, p, verifier)
        out, files = testing.play_meta(fast, actor, p, visit=i)
        if out and out.get("landed") is True:
            fast_landed.append(i)
        s = play_slow(slow, fast, actor, p, i, k, words="yes")
        if s is not None:
            slow_visits.append(i)
    assert fast_landed and 1 in fast_landed                    # task skills: the policy flip on problem 1
    assert all(i % k == 0 for i in slow_visits)                 # meta-skills: only on the slow clock
    fast_versions = testing.tool("read_pack", "--pack", fast)["versions"]
    actor_versions = testing.tool("read_pack", "--pack", actor)["versions"]
    assert len(fast_versions) == len(slow_visits) and len(actor_versions) >= len(fast_landed)
    assert len(fast_versions) <= len(paths) // k
    curve = testing.tool("curve", "--pack", actor, "--tasks", tmp_path / "tasks")
    assert all(r["gap_val"] >= 0 for r in curve["curve"])


def test_meta_skill_change_never_lands_without_the_human(tmp_path):
    actor, verifier, fast, slow, paths, k = setup(tmp_path)
    for i, p in enumerate(paths[:k], 1):
        testing.play_arm(actor, p, arm="control", memory_off=True)
        testing.play_arm(actor, p)
        testing.play_verifier(actor, p, verifier)
        testing.play_meta(fast, actor, p, visit=i)
    before = packs.checksums(fast)
    roles = packs.read_pack(fast)
    old = number(roles["roles/proposer.md"], "Cards per visit")
    files = {"roles/proposer.md": {"after": roles["roles/proposer.md"].replace(f"Cards per visit: {old}", f"Cards per visit: {old + 1}")}}

    def propose(visit):
        return testing.tool("patch_pack", "--pack", slow, "--task", paths[k - 1], "--target", fast, "--files", json.dumps(files),
                            "--recipe", json.dumps(recipe.BASELINE), "--summary", "proposer: +1", "--visit", str(visit))

    pending = propose(1)
    assert pending["landed"] is False and pending["decision"] is None and "Cards per visit: 4" in pending["diff"]
    assert packs.checksums(fast) == before
    no = testing.tool("patch_pack", "--pack", slow, "--task", paths[k - 1], "--target", fast, "--proposal", pending["id"], "--approved", "reject")
    assert no["decision"] == "n" and packs.checksums(fast) == before
    # not on the clock: the rule proposes nothing
    assert play_slow(slow, fast, actor, paths[0], 1, k, words="yes") is None
    # the human's yes lands one role line, and the version history is a diff-able directory
    pending = propose(2)
    yes = testing.tool("patch_pack", "--pack", slow, "--task", paths[k - 1], "--target", fast, "--proposal", pending["id"], "--approved", "approve")
    assert yes["landed"] and yes["approved_by"] == "human" and len(yes["files"]) == 1 and yes["files"][0].startswith("roles/")
    after = packs.checksums(fast)
    assert {f for f in after if after[f] != before.get(f)} == set(yes["files"])
    snapshot = tmp_path / "runs" / FAST / "versions" / yes["version"] / yes["files"][0]
    assert snapshot.read_text(encoding="utf-8") != packs.read_pack(fast)[yes["files"][0]]


def test_fast_loop_cannot_touch_roles_and_slow_loop_cannot_touch_the_actor(tmp_path):
    actor, verifier, fast, slow, paths, k = setup(tmp_path)
    testing.play_arm(actor, paths[0])
    files = packs.read_pack(fast)
    out = testing.tool("patch_pack", "--pack", fast, "--task", paths[0], "--target", fast, "--files", json.dumps({"roles/proposer.md": {"after": files["roles/proposer.md"] + "\n"}}),
                       "--recipe", json.dumps(recipe.BASELINE), "--summary", "no", "--visit", "9")
    assert "error" in out           # the fast loop's front matter has no patches: for roles; its own pack is not its target either
    out = testing.tool("patch_pack", "--pack", slow, "--task", paths[0], "--target", actor, "--files", json.dumps({"SKILL.md": {"after": packs.read_pack(actor)["SKILL.md"] + "\n"}}),
                       "--recipe", json.dumps(recipe.BASELINE), "--summary", "no", "--visit", "9")
    assert "may patch ['roles/*.md'] only" in out["error"]
    assert "not in meta-evolver's tools.md" in testing.tool("fit_recipe", "--pack", slow, "--task", paths[0], "--recipe", json.dumps(recipe.BASELINE))["error"]


def test_fast_loop_boots_what_the_slow_loop_wrote(tmp_path):
    actor, verifier, fast, slow, paths, k = setup(tmp_path)
    roles = packs.read_pack(fast)
    threshold = number(roles["roles/allocator.md"], "Policy flip threshold")
    new = roles["roles/allocator.md"].replace(f"Policy flip threshold: {threshold}", "Policy flip threshold: 99")
    testing.play_arm(actor, paths[0])
    out = testing.tool("patch_pack", "--pack", slow, "--task", paths[0], "--target", fast, "--files", json.dumps({"roles/allocator.md": {"after": new}}),
                       "--recipe", json.dumps(recipe.BASELINE), "--summary", "raise", "--visit", "1")
    testing.tool("patch_pack", "--pack", slow, "--task", paths[0], "--target", fast, "--proposal", out["id"], "--approved", "yes")
    assert number(packs.read_pack(fast)["roles/allocator.md"], "Policy flip threshold") == 99


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE, timeout=3600)
    assert "roles/" in text
