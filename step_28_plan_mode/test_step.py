import json
import os
import sys
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, context, hooks, llm, permissions, plan, prompt, session, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


GOOD_PLAN = {
    "goal": "Add a --version flag",
    "steps": [
        {"title": "Add the flag to the parser", "files": ["harness/agent.py"], "actions": ["add_argument('--version')"]},
        {"title": "Print the version and exit", "files": ["harness/agent.py"], "actions": ["read pyproject.toml", "print it"]},
    ],
    "risks": ["the version string drifts from pyproject.toml"],
}


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    """Every test starts in act mode with no plan, no todos and no hooks."""
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(plan, "PLAN", None)
    monkeypatch.setattr(plan, "FEEDBACK", [])
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(ui, "plan", lambda plan_: None)


@pytest.fixture
def quiet(monkeypatch):
    """Keep tests off the disk and off the terminal."""
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False: None)
    monkeypatch.setattr(ui, "usage", lambda stats: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "note", lambda text: None)


def answers(monkeypatch, *lines):
    """Script what the user types at the prompts, in order."""
    queue = list(lines)
    asked = []

    def read(text="> "):
        asked.append(text)
        return queue.pop(0)

    monkeypatch.setattr(prompt, "read", read)
    return asked


# ------------------------------------------------------------------- tests


def test_plan_toolset_is_read_only_plus_submit_plan(monkeypatch):
    assert plan.toolset() is tools.TOOL_SCHEMAS
    monkeypatch.setattr(plan, "MODE", "plan")
    names = [s["function"]["name"] for s in plan.toolset()]
    assert names == ["bash", "read_file", "read_skill", "task", "submit_plan"]
    assert not {"write_file", "str_replace", "write_todos", "remember", "forget"} & set(names)
    assert "submit_plan" not in {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
    assert tools.TOOLS["submit_plan"] is plan.submit_plan


def test_plan_mode_denies_ask_commands_and_edits(monkeypatch):
    assert permissions.check("bash", {"command": "python setup.py"}) == ("ask", "run: python setup.py")
    monkeypatch.setattr(plan, "MODE", "plan")
    action, reason = permissions.check("bash", {"command": "python setup.py"})
    assert action == "deny" and "plan mode" in reason
    assert permissions.check("bash", {"command": "ls -la"}) == ("allow", "run: ls -la")
    assert permissions.check("bash", {"command": "rm -rf x"})[0] == "deny"
    assert permissions.check("write_file", {"path": "a.py", "content": ""})[0] == "deny"
    assert permissions.check("read_file", {"path": "a.py"}) == ("allow", None)
    assert permissions.check("submit_plan", {"plan": GOOD_PLAN}) == ("allow", None)
    _, result = tools.execute(call("t1", "bash", {"command": "python setup.py"}))
    assert result.startswith("Blocked by policy: plan mode")


def test_invalid_plan_is_an_error_result_listing_the_problems(monkeypatch):
    monkeypatch.setattr(plan, "MODE", "plan")
    bad = {"goal": "", "steps": [{"title": "x", "files": "a.py"}], "extra": 1}
    result = plan.submit_plan(bad)
    assert result.startswith("Error: the plan is invalid:")
    assert "goal" in result and "actions" in result and "files" in result and "extra" in result
    assert plan.MODE == "plan" and plan.PLAN is None and todos.TODOS == []
    assert plan.submit_plan({"goal": "g", "steps": [], "risks": []}).startswith("Error:")
    assert plan.submit_plan("not an object").startswith("Error:")


def test_manual_check_agrees_with_jsonschema():
    pytest.importorskip("jsonschema")
    cases = [
        GOOD_PLAN,
        {"goal": "", "steps": [{"title": "x", "files": "a.py"}], "extra": 1},
        {"goal": "g", "steps": [], "risks": []},
        {"goal": "g", "steps": [{"title": "t", "files": [], "actions": [1]}], "risks": "no"},
        "not an object",
    ]
    for case in cases:
        assert bool(plan.manual_check(case)) == bool(plan.validate(case)), case
    assert plan.manual_check(GOOD_PLAN) == []


def test_validate_falls_back_to_the_manual_check_without_jsonschema(monkeypatch):
    monkeypatch.setitem(sys.modules, "jsonschema", None)  # makes `import jsonschema` raise ImportError
    bad = {"goal": "", "steps": [{"title": "x", "files": "a.py"}], "extra": 1}
    assert plan.validate(bad) == plan.manual_check(bad)
    assert plan.validate(GOOD_PLAN) == []
    assert "unexpected property 'extra'" in " ".join(plan.validate(bad))


def test_valid_plan_and_yes_makes_todos_and_switches_to_act(monkeypatch):
    monkeypatch.setattr(plan, "MODE", "plan")
    asked = answers(monkeypatch, "y")
    result = plan.submit_plan(GOOD_PLAN)
    assert asked == ["  approve? (y/n)> "]
    assert result.startswith("Plan approved.")
    assert plan.MODE == "act" and plan.PLAN == GOOD_PLAN
    assert [t["content"] for t in todos.TODOS] == ["Add the flag to the parser", "Print the version and exit"]
    assert {t["status"] for t in todos.TODOS} == {"pending"}
    content = context.reminder()["content"]
    assert "mode: act" in content
    assert "<plan>" in content and "goal: Add a --version flag" in content and "1. Add the flag to the parser" in content
    assert content.index("</todos>") < content.index("<plan>")
    # the plan leaves the late block once every todo is completed
    for todo in todos.TODOS:
        todo["status"] = "completed"
    assert "<plan>" not in context.reminder()["content"]
    assert plan.PLAN is None


def test_no_keeps_plan_mode_and_carries_the_feedback(monkeypatch):
    monkeypatch.setattr(plan, "MODE", "plan")
    asked = answers(monkeypatch, "n", "use argparse's version action instead")
    result = plan.submit_plan(GOOD_PLAN)
    assert asked == ["  approve? (y/n)> ", "  feedback> "]
    assert result == "Plan not approved. Still in plan mode. User feedback: use argparse's version action instead"
    assert plan.MODE == "plan" and plan.PLAN is None and todos.TODOS == []
    content = context.reminder()["content"]
    assert "mode: plan" in content
    assert "<plan>" in content and "use argparse's version action instead" in content


def test_plan_and_act_commands_switch_the_mode(monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    messages = [{"role": "system", "content": "s"}]
    assert commands.handle("/plan", messages) is messages
    assert plan.MODE == "plan"
    assert "plan" in notes[-1]
    assert "<plan>" in context.reminder()["content"]
    assert commands.handle("/act", messages) is messages
    assert plan.MODE == "act"
    assert "<plan>" not in context.reminder()["content"]
    assert "/plan" in commands.COMMANDS and "/act" in commands.COMMANDS


def test_plan_mode_adds_a_prompt_suffix(monkeypatch):
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}]
    assert llm.with_mode(messages) is messages
    monkeypatch.setattr(plan, "MODE", "plan")
    sent = llm.with_mode(messages)
    assert sent[0]["content"].startswith("s") and "submit_plan" in sent[0]["content"]
    assert sent[1:] == messages[1:]
    assert messages[0]["content"] == "s"  # the transcript itself is untouched


def test_loop_smoke_plan_then_approve(quiet, monkeypatch):
    monkeypatch.setattr(plan, "MODE", "plan")
    answers(monkeypatch, "y")
    replies = [
        FakeMessage(content=None, tool_calls=[call("t1", "bash", {"command": "ls"})]),
        FakeMessage(content=None, tool_calls=[call("t2", "submit_plan", {"plan": GOOD_PLAN})]),
        FakeMessage(content="plan approved, starting", tool_calls=None),
    ]
    offered = []
    systems = []

    def fake(messages, tools=None, on_delta=None):
        offered.append([s["function"]["name"] for s in tools])
        systems.append(messages[0]["content"])
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(agent, "call_llm", fake)
    out = agent.turn([{"role": "system", "content": "s"}], "add a --version flag")
    assert out[5]["content"].startswith("Plan approved.")
    assert out[-1]["content"] == "plan approved, starting"
    # the first two requests were made in plan mode, the third in act mode
    assert offered[0][-1] == "submit_plan" and "write_file" not in offered[0]
    assert offered[1] == offered[0]
    assert "write_file" in offered[2] and "submit_plan" not in offered[2]
    assert "submit_plan" in systems[0] and "submit_plan" not in systems[2]
    assert plan.MODE == "act" and len(todos.TODOS) == 2
