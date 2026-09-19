"""Step 06 - the verifier sees only the log; write_card refuses test / intent; a wrong card is demoted by
counterexamples; fit_recipe refuses a forbidden recipe; the memory arm beats MEMORY_OFF at the same budget;
MEMORY_OFF reproduces step 01 exactly."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common import checks, curriculum, harness, memory, packs, steps, tasks  # noqa: E402
from common.fake import FakeModel  # noqa: E402
from common.tools import execute  # noqa: E402

ACTOR, VERIFIER = "adult-income", "adult-income-verifier"
CUR, _ = tasks.test_curriculum()
T1, T3, T6 = CUR[0], CUR[2], CUR[5]          # three tree-shaped tables: what problem 1 teaches must help on 3 and 6
STEP01 = HERE.parent / "step_01_regular_harness" / "skills" / "adult-income-regular"


def packs_in(tmp_path):
    return steps.workspace(HERE, ACTOR, VERIFIER, into=tmp_path / "w")


def plant(actor, card):
    memory.save(actor / "memory.json", [card])


def test_verifier_transcript_contains_no_actor_text(tmp_path):
    actor, verifier = packs_in(tmp_path)
    _, inner, ver = curriculum.run_problem(actor, T1, FakeModel(), tmp_path / "run", verifier_dir=verifier)
    iso = checks.verifier_isolation(inner, ver)
    assert iso["leaked"] == [] and not iso["system_has_actor_skill"]
    assert iso["row_keys"] == ["error", "problem", "recipe", "seed", "val_score"]        # the contract, and nothing else
    assert packs.VERIFIER_CONTRACT in ver.system and packs.lint_pack(verifier, T1) == []
    assert execute(ver, checks.call("fit_recipe", recipe=inner.fits[0]["recipe"])).startswith("Error: fit_recipe is not in this pack's tools.md")


def test_write_card_refuses_a_card_that_names_the_test_or_the_intent(tmp_path):
    actor, verifier = packs_in(tmp_path)
    ver = harness.boot(verifier, T1, run_dir=tmp_path / "run", target=actor)
    ok = {"if": {"key": "n_rows", "op": "<", "value": 1000}, "then": {"field": "model", "prefer": "hgb"}, "evidence": 1, "counter": 0}
    assert json.loads(execute(ver, checks.call("write_card", card=ok)))["cards"] == 1
    assert execute(ver, checks.call("write_card", card={**ok, "note": "the test split liked it"})).startswith("Error: not a card")
    assert execute(ver, checks.call("write_card", card={**ok, "then": {"field": "model", "prefer": "test"}})).startswith("Error: not a card: a card may not mention 'test'")
    assert execute(ver, checks.call("write_card", card={**ok, "then": {"field": "model", "prefer": "intent"}})).startswith("Error: not a card: a card may not mention 'intent'")
    assert execute(ver, checks.call("write_card", card={**ok, "if": {"key": "signal_is_linear", "op": "==", "value": 1}})).startswith("Error: not a card")
    assert len(memory.load(actor / "memory.json")) == 1


def test_a_planted_wrong_card_is_demoted_after_two_counterexamples(tmp_path):
    actor, verifier = packs_in(tmp_path)
    wrong = {"if": {"key": "n_rows", "op": "<", "value": 1000}, "then": {"field": "model", "prefer": "logreg"}, "evidence": 2, "counter": 0}
    plant(actor, wrong)
    for task in (T1, T3):                                                              # trees win on both
        card, _, _ = curriculum.run_problem(actor, task, FakeModel(), tmp_path / "run", verifier_dir=verifier)
    planted = next(c for c in memory.load(actor / "memory.json") if memory.card_id(c) == memory.card_id(wrong))
    assert planted["counter"] == 2 and not memory.active(planted)
    assert card["cards_demoted"] == 1


def test_fit_recipe_refuses_a_forbidden_recipe(tmp_path):
    actor, _ = packs_in(tmp_path)
    plant(actor, {"if": {"key": "n_rows", "op": "<", "value": 1000}, "then": {"field": "encode", "forbid": "ordinal"}, "evidence": 2, "counter": 0})
    run = harness.boot(actor, T1, run_dir=tmp_path / "run")
    ordinal = {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "ordinal", "class_weight": "none"}
    assert execute(run, checks.call("fit_recipe", recipe=ordinal)).startswith("Error: a forbid card rules this recipe out")
    assert run.budget.used == 0
    harness.run(run, FakeModel())
    assert run.budget.used == 24 and all(r["recipe"]["encode"] == "onehot" for r in run.fits)


def test_memory_arm_beats_memory_off_at_the_same_budget(tmp_path):
    actor, verifier = packs_in(tmp_path)
    curve = curriculum.run_curriculum(actor, verifier, [T1, T3, T6], FakeModel(), tmp_path / "run")
    assert curve[0]["gap_val"] == 0 and curve[0]["cards_active"] > 0                   # first problem: identical arms, then cards
    last = curve[-1]
    assert last["cards_active"] >= 2 and last["cards_active"] >= curve[0]["cards_active"]
    assert last["memory"]["fits_used"] == last["control"]["fits_used"] == 24
    assert last["gap_val"] >= 0 and last["wasted_memory"] < last["wasted_control"]
    assert last["memory"]["test_scored_once"] and last["control"]["test_scored_once"]


def test_memory_off_reproduces_step_01_exactly(tmp_path):
    actor, _ = packs_in(tmp_path)
    plant(actor, {"if": {"key": "n_rows", "op": "<", "value": 1000}, "then": {"field": "model", "prefer": "hgb"}, "evidence": 5, "counter": 0})
    off = checks.run_pack(actor, T1, FakeModel(), tmp_path / "off", arm="control", memory_off=True)
    regular = checks.run_pack(STEP01, T1, FakeModel(), tmp_path / "reg", arm="control")
    assert checks.fit_sequence(off) == checks.fit_sequence(regular)
    assert off.gate.result == regular.gate.result
    assert "(MEMORY_OFF" in off.system and "prefer" not in off.system.split("### FILE: memory.json")[1][:80]
    on = checks.run_pack(actor, T1, FakeModel(), tmp_path / "on", arm="memory")
    assert checks.fit_sequence(on) != checks.fit_sequence(regular)                     # the cards did change the search
