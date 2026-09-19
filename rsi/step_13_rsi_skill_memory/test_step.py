"""Step 13 - a skill card is selected by the working-memory need, not by recency; an update is localised to one
card and validated before it lands; the horizon report shows the gain per sequence length."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from common import checks, curriculum, harness, packs, steps, tasks  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import execute, skill_cards  # noqa: E402
from run import ACTOR, META, skills_problem  # noqa: E402

CUR, _ = tasks.test_curriculum()
T1, T3, T6 = CUR[0], CUR[2], CUR[5]      # trees+categorical, trees multiclass, trees imbalanced


def add_card(actor, name, when, then):
    """Append a card to the package: the newest entry in the manifest."""
    root = actor / "skill-memory"
    (root / "cards" / f"{name}.md").write_text(f"---\nname: {name}\nwhen: [{', '.join(when)}]\nthen: {then}\nvalidated: true\nhorizon: 1\n---\nplanted\n", encoding="utf-8")
    manifest = root / "manifest.yaml"
    manifest.write_text(manifest.read_text(encoding="utf-8") + f"- name: {name}\n  file: cards/{name}.md\n", encoding="utf-8")


def test_a_card_is_selected_by_need_not_by_recency(tmp_path):
    actor, meta = steps.workspace(HERE, ACTOR, META, into=tmp_path / "w")
    add_card(actor, "newest-multiclass-card", ["multiclass"], "model=logreg")           # newer, but not this situation
    run = harness.boot(actor, T1, run_dir=tmp_path / "run")
    harness.run(run, FakeModel())
    need = json.loads(checks.tool_results(run, "skill_memory")[0])
    assert need["need"] == ["small", "categorical", "imbalanced"]
    assert [c["name"] for c in need["cards"]] == ["onehot-for-categorical"]                 # the older card, by situation
    assert need["prefer"] == {"encode": "onehot"}
    working = (actor / "working.md").read_text(encoding="utf-8")
    assert "Need: small, categorical, imbalanced" in working and "Cards: onehot-for-categorical" in working
    assert all(r["recipe"]["encode"] == "onehot" for r in run.fits[:3])                     # the probes obeyed the card
    multi = harness.boot(actor, T3, run_dir=tmp_path / "run3")
    harness.run(multi, FakeModel())
    assert [c["name"] for c in json.loads(checks.tool_results(multi, "skill_memory")[0])["cards"]] == ["onehot-for-categorical", "newest-multiclass-card"]   # manifest order, both fit


def test_an_update_is_localised_to_one_card_and_validated_first(tmp_path):
    actor, meta = steps.workspace(HERE, ACTOR, META, into=tmp_path / "w")
    curriculum.run_problem(actor, T1, FakeModel(), tmp_path / "run")
    before = packs.checksums(actor)
    visit = harness.boot(meta, T1, run_dir=tmp_path / "run", target=actor, arm="meta", quiet=True)
    bad = {"card": "model-when-small", "then": "model=logreg", "when": ["small"], "body": "wishful"}
    result = execute(visit, checks.call("skill_memory", action="update", payload=bad))
    assert result.startswith("Error: not validated: model=logreg did not win its comparisons")
    assert packs.checksums(actor) == before                                                  # nothing landed
    good = {"card": "model-when-small", "then": "model=hgb", "when": ["small"], "body": "hgb won"}
    landed = json.loads(execute(visit, checks.call("skill_memory", action="update", payload=good)))
    assert landed["new"] and landed["horizon"] == 1 and landed["version"] == "gen_001"
    after = packs.checksums(actor)
    changed = sorted(n for n in set(before) | set(after) if before.get(n) != after.get(n))
    assert changed == ["skill-memory/cards/model-when-small.md", "skill-memory/manifest.yaml"]   # one card, one manifest line
    assert execute(visit, checks.call("skill_memory", action="update", payload=good)).startswith("Error: one card update per visit")
    assert [c["name"] for c in skill_cards(actor)] == ["onehot-for-categorical", "model-when-small"]
    assert execute(visit, checks.call("fit_recipe", recipe=run_recipe())).startswith("Error: fit_recipe is not in this pack's tools.md")


def run_recipe():
    return {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}


def test_the_horizon_report_shows_the_gain_per_sequence_length(tmp_path):
    actor, meta = steps.workspace(HERE, ACTOR, META, into=tmp_path / "w")
    run_dir = tmp_path / "run"
    curve = curriculum.run_curriculum(actor, None, [T1, T3, T6], FakeModel(), run_dir,
                                      memory_arm=lambda task, bar: skills_problem(FakeModel(), actor, meta, task, run_dir, bar=bar))
    assert [r["index"] for r in curve] == [1, 2, 3]
    horizons = [r["memory"]["horizon"] for r in curve]
    cards = [r["memory"]["skill_cards"] for r in curve]
    assert cards == sorted(cards) and cards[-1] > cards[0] and horizons == sorted(horizons)
    assert all(r["gap_val"] >= 0 for r in curve) and curve[-1]["gap_val"] > 0
    assert (run_dir / "versions" / "gen_001" / "skill-memory" / "manifest.yaml").exists()      # git-native: files you can diff
