"""Lesson 13 - Recuris: a skill card is selected by the working-memory need, not by recency; an update is
localised to one card file (plus a manifest line for a new card) and validated against the log before it lands;
one update per visit; the horizon report shows each card's gain per sequence length; the actor cannot update
and the meta pack cannot fit.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import memory, packs, recipe, tasks, testing  # noqa: E402

ACTOR, META = "adult-income-skills", "skill-memory-meta"


def setup(tmp_path):
    actor, meta = testing.workspace(HERE, tmp_path, ACTOR, META)
    d = tmp_path / "tasks"
    d.mkdir()
    curriculum, _ = tasks.test_curriculum()
    paths = []
    for t in curriculum:
        p = d / f"{t['index']:02d}_{t['name']}.json"
        p.write_text(json.dumps(t), encoding="utf-8")
        paths.append(p)
    return actor, meta, paths


def play_actor(actor, task_path, seed=0):
    """The actor skill: tags, need, then obey-memory with the selected cards' preferences."""
    from _lib import policies
    from _lib.state import Run

    argv = ["--pack", str(actor), "--task", str(task_path), "--seed", str(seed)]
    testing.tool("load_splits", *argv)
    tags = testing.tool("skill_memory", *argv, "--action", "tags")["need"]
    need = testing.tool("skill_memory", *argv, "--action", "need", "--need", ",".join(tags))
    # the preferences as cards, so the same policy code ranks the grid
    profile = tasks.profile(tasks.load_task(task_path))
    cards = [{"if": {"key": "n_rows", "op": ">", "value": 0}, "then": {"field": f, "prefer": v}, "evidence": 1, "counter": 0} for f, v in need["prefer"].items()]
    schema = json.loads((Path(actor) / "schema.json").read_text(encoding="utf-8"))
    fits, tried = [], []
    while True:
        order = policies.policy_order("obey-memory" if cards else "static", schema["recipes"], cards, profile, fits, seed=seed)
        todo = [x for x in order if x not in tried][:8]
        out = testing.tool("fit_recipe", *argv, "--recipes", json.dumps(todo))
        for res in out["results"]:
            tried.append(res["recipe"])
            if not res.get("refused"):
                fits.append(({"recipe": res["recipe"]}, {"n": res["n"], "val_score": res["val_score"]}))
        if out.get("FREEZE"):
            break
    best = max((f for f in fits if f[1]["val_score"] is not None), key=lambda f: f[1]["val_score"])[0]["recipe"]
    testing.tool("score_test", *argv, "--recipe", json.dumps(best))
    return need, testing.tool("scorecard", *argv)


def play_meta(meta, actor, task_path, visit, seed=0):
    """The meta skill: the first field whose winning value the situation's card does not hold."""
    argv = ["--pack", str(actor), "--task", str(task_path), "--seed", str(seed)]
    rows = testing.tool("read_traces", *argv, "--scope", "problem", "--tally")
    tags = testing.tool("skill_memory", *argv, "--action", "tags")["need"]
    cards = testing.tool("skill_memory", *argv, "--action", "list")["cards"]
    wins = {(w["field"], w["value"]): w["n"] for w in rows["tally"]["wins"]}
    losses = {(l["field"], l["value"]): l["n"] for l in rows["tally"]["losses"]}
    for field in ("model", "class_weight", "encode", "scale"):
        values = {v for f, v in list(wins) + list(losses) if f == field}
        if not values:
            continue
        best = max(sorted(values, key=str), key=lambda v: wins.get((field, v), 0) - losses.get((field, v), 0))
        if wins.get((field, best), 0) - losses.get((field, best), 0) <= 0:
            continue
        held = [c for c in cards if set(c.get("when", [])) <= set(tags) and c["then"].split("=")[0] == field]
        if held and held[0]["then"] == f"{field}={best}":
            continue
        name = held[0]["name"] if held else f"{best}-for-{tags[0] if tags else 'any'}"
        return testing.tool("skill_memory", *argv, "--action", "update", "--as", str(meta), "--card", name, "--then", f"{field}={best}",
                            "--when", ",".join(tags), "--body", f"{field}={best} won on {rows['n']} fits", "--visit", str(visit))
    return None


def test_card_selected_by_need_not_recency(tmp_path):
    actor, meta, paths = setup(tmp_path)
    # a newer card for a situation this problem is NOT in must not be selected
    (actor / "skill-memory" / "cards" / "rf-for-multiclass.md").write_text(
        "---\nname: rf-for-multiclass\nwhen: [multiclass]\nthen: model=rf\nvalidated: true\nhorizon: 1\n---\nnewest card, wrong situation\n", encoding="utf-8")
    m = actor / "skill-memory" / "manifest.yaml"
    m.write_text(m.read_text(encoding="utf-8") + "- name: rf-for-multiclass\n  file: cards/rf-for-multiclass.md\n", encoding="utf-8")
    argv = ["--pack", str(actor), "--task", str(paths[0])]
    testing.tool("load_splits", *argv)
    tags = testing.tool("skill_memory", *argv, "--action", "tags")["need"]
    assert "categorical" in tags and "multiclass" not in tags
    need = testing.tool("skill_memory", *argv, "--action", "need", "--need", ",".join(tags))
    assert [c["name"] for c in need["cards"]] == ["onehot-for-categorical"] and need["prefer"] == {"encode": "onehot"}
    assert "Cards: onehot-for-categorical" in (actor / "working.md").read_text(encoding="utf-8")
    multi = testing.tool("skill_memory", "--pack", actor, "--task", paths[2], "--action", "need", "--need", "multiclass")
    assert [c["name"] for c in multi["cards"]] == ["rf-for-multiclass"]


def test_update_is_localised_validated_and_once_per_visit(tmp_path):
    actor, meta, paths = setup(tmp_path)
    play_actor(actor, paths[0])
    before = packs.checksums(actor)
    # not validated: a value that lost its comparisons does not land
    bad = testing.tool("skill_memory", "--pack", actor, "--task", paths[0], "--action", "update", "--as", meta, "--card", "ordinal-for-categorical",
                       "--then", "encode=ordinal", "--when", "categorical", "--body", "x", "--visit", "1")
    assert "not validated" in bad["error"] and packs.checksums(actor) == before
    out = play_meta(meta, actor, paths[0], visit=1)
    assert out and out["version"] == "gen_001" and out["horizon"] >= 1
    after = packs.checksums(actor)
    changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    assert changed <= {out["file"], "skill-memory/manifest.yaml", "working.md"} and out["file"] in changed
    again = testing.tool("skill_memory", "--pack", actor, "--task", paths[0], "--action", "update", "--as", meta, "--card", "x", "--then", out["file"] and "model=hgb",
                         "--when", "categorical", "--body", "x", "--visit", "1")
    assert "one card update per visit" in again["error"] or "not validated" in again["error"]
    assert "the meta pack updates cards" in testing.tool("skill_memory", "--pack", actor, "--task", paths[0], "--action", "update", "--as", actor,
                                                                   "--card", "x", "--then", "model=hgb", "--when", "small", "--body", "x", "--visit", "2")["error"]
    assert "not in skill-memory-meta's tools.md" in testing.tool("fit_recipe", "--pack", meta, "--task", paths[0], "--recipe", json.dumps(recipe.BASELINE))["error"]


def test_horizon_report_over_the_curriculum(tmp_path):
    actor, meta, paths = setup(tmp_path)
    gains = []
    for i, p in enumerate(paths, 1):
        control = testing.play_arm(actor, p, arm="control", memory_off=True)
        need, card = play_actor(actor, p)
        gains.append(round(card["best_val_score"] - control["best_val_score"], 4))
        play_meta(meta, actor, p, visit=i)
    cards = testing.tool("skill_memory", "--pack", actor, "--task", paths[-1], "--action", "list")["cards"]
    horizons = {c["name"]: c["horizon"] for c in cards}
    assert max(horizons.values()) >= 2 and len(cards) >= 2
    assert all(g >= 0 for g in gains), gains
    curve = testing.tool("curve", "--pack", actor, "--tasks", tmp_path / "tasks")
    assert curve["summary"]["complete"] == 6


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE, timeout=3600)
    assert "horizon" in text.lower()
