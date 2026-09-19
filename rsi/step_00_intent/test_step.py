"""Lesson 00 - the intent: task.json and acceptance.md validate; a pack that widens the intent is refused
by lint_pack; the acceptance fields are exactly the scorecard fields; the skill pack meets the contract.
Offline, no key, no agent: the scripts are the gates, so the claims are provable without one.
"""

import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

from _lib import tasks, testing  # noqa: E402
from _lib.scorecard import SCORECARD_FIELDS  # noqa: E402

FIELD_LINE = re.compile(r"^- ([a-z_]+)$", re.M)


def acceptance_fields():
    section = (HERE / "acceptance.md").read_text(encoding="utf-8").split("## The scorecard")[1].split("## ")[0]
    return tuple(FIELD_LINE.findall(section))


def test_intent_validates():
    out = testing.tool("validate_intent", "--task", HERE / "task.json", "--acceptance", HERE / "acceptance.md")
    assert out["ok"], out
    assert out["budget"] == {"n_fits": 24, "per": "arm"} and out["test_rule"] == {"scores": 1, "after": "FREEZE"}


def test_acceptance_fields_are_exactly_the_scorecard_fields():
    assert acceptance_fields() == SCORECARD_FIELDS


def test_widened_pack_is_refused():
    out = testing.tool("lint_pack", "--files", f"@{HERE / '.claude/skills/intent/widened_pack.json'}", "--task", HERE / "task.json")
    assert not out["ok"]
    assert any("n_fits 48" in p for p in out["problems"]) and any("test_rule" in p for p in out["problems"])


def test_a_bad_task_is_a_result_not_a_crash(tmp_path):
    bad = json.loads((HERE / "task.json").read_text(encoding="utf-8"))
    bad["budget"]["n_fits"] = 100
    (tmp_path / "task.json").write_text(json.dumps(bad), encoding="utf-8")
    out = testing.tool("validate_intent", "--task", tmp_path / "task.json")
    assert not out["ok"] and "task.json" in out["problems"][0]


def test_curriculum_validates_in_order():
    names = [t["name"] for t in tasks.all_tasks()]
    assert names == ["adult_income", "breast_cancer", "wine", "digits", "synth_shift_a", "synth_shift_b", "exam"]
    assert [t["role"] for t in tasks.all_tasks()] == ["curriculum"] * 6 + ["exam"]
    for t in tasks.all_tasks():
        assert t["budget"]["n_fits"] == 24 and t["test_rule"] == {"scores": 1, "after": "FREEZE"}


def test_cli_contract_json_out_exit_zero():
    out = testing.tool_cli("validate_intent", "--task", HERE / "task.json", "--acceptance", HERE / "acceptance.md")
    assert out["ok"] is True


def test_pack_contract():
    assert testing.pack_contract(HERE) == []


def test_skill_changes_nothing(tmp_path):
    """The skill's two commands leave the lesson directory byte-identical (no run dir, no card, no pack)."""
    work = tmp_path / "lesson"
    shutil.copytree(HERE, work, ignore=shutil.ignore_patterns("__pycache__", "runs"))
    before = {p.relative_to(work).as_posix(): p.read_bytes() for p in work.rglob("*") if p.is_file()}
    testing.tool("validate_intent", "--task", work / "task.json", "--acceptance", work / "acceptance.md")
    testing.tool("lint_pack", "--files", f"@{work / '.claude/skills/intent/widened_pack.json'}", "--task", work / "task.json")
    after = {p.relative_to(work).as_posix(): p.read_bytes() for p in work.rglob("*") if p.is_file()}
    assert before == after


def test_live_claude_code():
    text = testing.live(HERE)
    assert "24" in text and "FREEZE" in text
