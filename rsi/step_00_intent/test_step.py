"""Step 00 - the intent validates, nothing may widen it, and the acceptance fields are the scorecard fields."""

import json
import sys
from pathlib import Path

import jsonschema
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from common import packs, tasks  # noqa: E402
from common.scorecard import SCORECARD_FIELDS  # noqa: E402
from run import acceptance_fields, widened  # noqa: E402

REGULAR = HERE.parent / "step_01_regular_harness" / "skills" / "adult-income-regular"


def test_task_json_validates_against_the_schema():
    task = tasks.load_task(HERE / "task.json")
    assert task["name"] == "adult_income" and task["budget"] == {"n_fits": 24, "per": "arm"}
    assert task["test_rule"] == {"scores": 1, "after": "FREEZE"}


def test_a_widened_task_is_rejected():
    task = tasks.load_task(HERE / "task.json")
    with pytest.raises(jsonschema.ValidationError):
        tasks.validate_task({**task, "budget": {"n_fits": 48, "per": "arm"}})
    with pytest.raises(jsonschema.ValidationError):
        tasks.validate_task({**task, "test_rule": {"scores": 2, "after": "FREEZE"}})
    with pytest.raises(jsonschema.ValidationError):
        tasks.validate_task({**task, "extra": "a field the schema does not know"})


def test_every_curriculum_task_validates_and_is_in_order():
    problems = tasks.all_tasks()
    assert [t["index"] for t in problems] == list(range(1, 8))
    assert [t["role"] for t in problems][-1] == "exam" and all(t["role"] == "curriculum" for t in problems[:-1])
    assert all(t["budget"]["n_fits"] == 24 and t["test_rule"] == {"scores": 1, "after": "FREEZE"} for t in problems)


def test_lint_pack_rejects_a_raised_budget_or_a_touched_test_rule():
    task = tasks.load_task(HERE / "task.json")
    assert packs.lint_pack(REGULAR, task) == []
    assert any("n_fits 48" in p for p in packs.lint_pack(widened(REGULAR, n_fits=48), task))
    assert any("test_rule" in p for p in packs.lint_pack(widened(REGULAR, test_rule={"scores": 2, "after": "FREEZE"}), task))
    assert any("metric" in p for p in packs.lint_pack(widened(REGULAR, metric="accuracy"), task))
    assert any("model the task does not allow" in p for p in packs.lint_pack(widened(REGULAR, models=["logreg", "svm"]), task))


def test_acceptance_fields_are_exactly_the_scorecard_fields():
    assert acceptance_fields() == SCORECARD_FIELDS
    text = (HERE / "acceptance.md").read_text(encoding="utf-8")
    assert "3 of 5" in text and "MEMORY_OFF" in text   # the pass rule names the exam and the off switch
