"""Lesson 06 - the RSI harness: the verifier's input is {recipe, val_score, error} rows and the profile, nothing
else (no actor text can reach it); write_card refuses a card that names the test or the intent, or carries an
extra field; a planted wrong card is demoted by its counterexample; fit_recipe refuses a forbidden recipe and
spends no fit; with the obey-memory policy, same seed and budget, the memory arm on problem 2 is >= the
control arm and wastes fewer fits after learning on problem 1; MEMORY_OFF reproduces lesson 01's numbers
exactly; the actor cannot write a card and the verifier cannot fit.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import memory, recipe, testing  # noqa: E402

ACTOR, VERIFIER = "adult-income", "adult-income-verifier"
T1, T2 = testing.task("adult_income"), testing.task("breast_cancer")


def packs_in(tmp_path):
    return testing.workspace(HERE, tmp_path, ACTOR, VERIFIER)


def test_memory_off_reproduces_lesson_01_exactly(tmp_path):
    actor, _ = packs_in(tmp_path)
    (actor / "config.json").write_text('{"memory": "off"}', encoding="utf-8")
    card = testing.play_arm(actor, T1, arm="memory")
    assert card["best_val_score"] == 0.9172 and card["test_score"] == 0.9034 and card["fits_used"] == 24
    state = json.loads((tmp_path / "runs" / ACTOR / "adult_income" / "state.json").read_text(encoding="utf-8"))
    assert [f["recipe"] for f in state["arms"]["memory/0"]["fits"]] == recipe.static_list()
    assert "MEMORY_OFF" in testing.tool("write_card", "--pack", actor, "--task", T1, "--card", "{}")["error"]


def test_verifier_sees_only_rows_and_profile_and_writes_typed_cards(tmp_path):
    actor, verifier = packs_in(tmp_path)
    testing.play_arm(actor, T1)
    rows = testing.tool("read_traces", "--pack", actor, "--task", T1, "--scope", "problem", "--tally")
    assert rows["n"] == 24 and all(set(r) == {"recipe", "val_score", "error"} for r in rows["rows"])
    assert set(rows["profile"]) == {"n_rows", "n_features", "n_classes", "imbalance", "has_categorical"}
    out = testing.tool("write_card", "--pack", actor, "--task", T1, "--as", verifier, "--cards", json.dumps(rows["cards_by_rule"]))
    assert out["written"] == len(rows["cards_by_rule"]) and out["refused"] == 0 and out["by"] == "adult-income-verifier"
    cards = memory.load(actor / "memory.json")
    assert any(c["then"] == {"field": "encode", "prefer": "onehot"} for c in cards)      # ordinal hurt logreg
    assert all(set(c) == {"if", "then", "evidence", "counter"} for c in cards)


def test_write_card_refuses_test_intent_and_extra_fields(tmp_path):
    actor, verifier = packs_in(tmp_path)
    base = {"if": {"key": "imbalance", "op": "<", "value": 0.35}, "then": {"field": "class_weight", "prefer": "balanced"}, "evidence": 1, "counter": 0}
    for bad, why in [
        (dict(base, note="peeked at the test split"), "Additional properties"),
        (dict(base, then={"field": "class_weight", "prefer": "test"}), "may not mention 'test'"),
        (dict(base, then={"field": "class_weight", "prefer": "intent"}), "may not mention 'intent'"),
        (dict(base, then={"field": "class_weight", "prefer": "balanced", "forbid": "none"}), "valid under each of"),
        (dict(base, **{"if": {"key": "target_mean", "op": "<", "value": 1}}), "is not one of"),
    ]:
        out = testing.tool("write_card", "--pack", actor, "--task", T1, "--as", verifier, "--card", json.dumps(bad))
        assert "error" in out and why in out["error"], (bad, out)
    assert memory.load(actor / "memory.json") == []
    # the actor cannot write a card; the verifier cannot fit
    assert "not in adult-income's tools.md" in testing.tool("write_card", "--pack", actor, "--task", T1, "--as", actor, "--card", json.dumps(base))["error"]
    assert "not in adult-income-verifier's tools.md" in testing.tool("fit_recipe", "--pack", verifier, "--task", T1, "--recipe", json.dumps(recipe.BASELINE))["error"]


def test_planted_wrong_card_is_demoted_and_forbid_card_refuses_a_fit(tmp_path):
    actor, verifier = packs_in(tmp_path)
    wrong = {"if": {"key": "n_rows", "op": ">=", "value": 1000}, "then": {"field": "model", "prefer": "logreg"}, "evidence": 1, "counter": 0}
    first = testing.tool("write_card", "--pack", actor, "--task", T1, "--as", verifier, "--card", json.dumps(wrong))
    assert first["added"] and first["active"]
    counter = testing.tool("write_card", "--pack", actor, "--task", T1, "--as", verifier, "--card", json.dumps(dict(wrong, evidence=0, counter=1)))
    assert counter["demoted"] and not counter["active"] and counter["card"]["evidence"] == 1 and counter["card"]["counter"] == 1
    forbid = {"if": {"key": "has_categorical", "op": "==", "value": 1}, "then": {"field": "encode", "forbid": "ordinal"}, "evidence": 1, "counter": 0}
    testing.tool("write_card", "--pack", actor, "--task", T1, "--as", verifier, "--card", json.dumps(forbid))
    testing.tool("load_splits", "--pack", actor, "--task", T1)
    out = testing.tool("fit_recipe", "--pack", actor, "--task", T1, "--recipe", json.dumps(dict(recipe.BASELINE, encode="ordinal")))
    assert out["refused"] and "forbid card rules this recipe out" in out["error"]
    assert testing.tool("scorecard", "--pack", actor, "--task", T1)["fits_used"] == 0
    assert testing.tool("fit_recipe", "--pack", actor, "--task", T1, "--recipe", json.dumps(recipe.BASELINE))["n"] == 1


def test_memory_arm_beats_control_on_problem_2_after_problem_1(tmp_path):
    actor, verifier = packs_in(tmp_path)
    control_1 = testing.play_arm(actor, T1, arm="control", memory_off=True)
    memory_1 = testing.play_arm(actor, T1)
    assert memory_1["best_val_score"] == control_1["best_val_score"]         # an empty memory is the static walk
    v = testing.play_verifier(actor, T1, verifier)
    assert v["written"] >= 3
    control_2 = testing.play_arm(actor, T2, arm="control", memory_off=True)
    memory_2 = testing.play_arm(actor, T2)
    # breast cancer is nearly saturated (the baseline is within 0.005 of the static grid's best, so both arms
    # "waste" 0 fits); the memory arm still finds a better recipe because the model belief sends it to hgb's
    # hyper variants the static list never visits: +0.0012 val, +0.0039 test on this machine
    assert memory_2["best_val_score"] > control_2["best_val_score"]
    assert memory_2["test_score"] > control_2["test_score"]
    assert memory_2["wasted_fits"] <= control_2["wasted_fits"]
    assert memory_2["best_recipe"]["hyper"] not in (1, 16, 0.1)      # a hyper variant: outside the static list
    assert memory_2["test_scored_once"] and control_2["test_scored_once"]
    assert memory_2["fits_used"] == control_2["fits_used"] == 24
    assert memory_2["cards_active"] >= 3 and control_2["cards_active"] == 0


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_live_claude_code():
    text = testing.live(HERE)
    assert "card" in text.lower()
