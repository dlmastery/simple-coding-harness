import json
import os
import sys
from types import SimpleNamespace

import httpx
import openai
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
    assert names == ["bash", "read_file", "read_skill", "recall", "task", "submit_plan"]
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


def test_plan_mode_denies_writes_that_hide_inside_allowed_commands(monkeypatch):
    monkeypatch.setattr(plan, "MODE", "plan")
    for command in ("echo hello > pwned.txt", "find . -name '*.pyc' -delete", "echo $(rm -rf x)", "cat a.txt | tee b.txt"):
        action, reason = permissions.check("bash", {"command": command})
        assert action == "deny" and "plan mode" in reason, command
    assert permissions.check("bash", {"command": "ls\nrm -rf x"})[0] == "deny"  # a newline separates commands too
    assert permissions.check("bash", {"command": "grep -n 'a > b' file.py"}) == ("allow", "run: grep -n 'a > b' file.py")  # quoted, not a redirection
    assert permissions.check("bash", {"command": "ls 2>&1"}) == ("allow", "run: ls 2>&1")
    assert permissions.check("recall", {"name": "x"}) == ("allow", None)  # read-only, so offered and allowed


def test_submit_plan_is_an_error_outside_plan_mode_and_an_empty_todo_list_keeps_the_plan(monkeypatch):
    assert plan.submit_plan(GOOD_PLAN) == "Error: not in plan mode"
    assert plan.MODE == "act" and plan.PLAN is None and todos.TODOS == []
    monkeypatch.setattr(plan, "PLAN", GOOD_PLAN)
    assert not plan.done()  # no todos at all is not "every todo completed"
    assert "<plan>" in context.reminder()["content"] and plan.PLAN is GOOD_PLAN


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


# ----------------------------------------------- the error paths of the loop


def raw_call(cid, name, arguments):
    """A tool call whose arguments are exactly this string, valid JSON or not."""
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def fake_model(monkeypatch, *replies):
    """A call_llm that plays the replies in order, for the main loop."""
    queue = list(replies)
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (queue.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}))


def test_bad_arguments_unknown_tool_and_a_raising_tool_each_get_one_tool_message(quiet, monkeypatch, tmp_path):
    fake_model(
        monkeypatch,
        FakeMessage(content=None, tool_calls=[
            raw_call("c1", "read_file", '{"path": '),                                   # cut off mid-stream
            raw_call("c2", "no_such_tool", "{}"),                                       # a name the registry lacks
            raw_call("c3", "bash", json.dumps({"command": "echo hi", "shell": "zsh"})),      # the tool raises (unknown keyword)
            raw_call("c4", "bash", "[1, 2]"),                                           # JSON, but not an object
            raw_call("c5", "bash", "{}"),                                               # a required argument missing
        ]),
        FakeMessage(content="None of that worked.", tool_calls=None),
    )
    messages = agent.turn([{"role": "system", "content": "s"}], "try a few things")
    results = {m["tool_call_id"]: m["content"] for m in messages if m["role"] == "tool"}
    assert list(results) == ["c1", "c2", "c3", "c4", "c5"]  # one tool message per call, in reply order
    assert results["c1"].startswith("Error: the arguments of read_file are not a JSON object:")
    assert results["c2"] == "Error: no tool named 'no_such_tool'."
    assert results["c3"].startswith("Error: TypeError:")
    assert results["c4"] == "Error: the arguments of bash are not a JSON object: got list"
    assert results["c5"] == "Blocked by policy: bash: missing argument 'command'"
    assert messages[-1]["content"] == "None of that worked."  # the loop went on to the next reply


def test_a_failed_model_call_is_a_note_and_the_transcript_stays_valid(quiet, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))

    def down(messages, tools=None, on_delta=None):
        raise openai.APIConnectionError(request=httpx.Request("POST", "https://example.invalid/v1"))

    monkeypatch.setattr(agent, "call_llm", down)
    messages = agent.turn([{"role": "system", "content": "s"}], "hello?")
    assert [m["role"] for m in messages] == ["system", "user"]  # the prompt stays, nothing dangles
    assert notes[-1].startswith("model call failed:")


def test_ctrl_c_mid_turn_answers_the_pending_tool_calls(quiet, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    fake_model(monkeypatch, FakeMessage(content=None, tool_calls=[raw_call("c1", "bash", json.dumps({"command": "echo hi"}))]))

    def interrupted(tool_calls, allowed=None):
        raise KeyboardInterrupt

    monkeypatch.setattr(agent, "execute_all", interrupted)
    messages = agent.turn([{"role": "system", "content": "s"}], "run it")
    assert messages[-1] == {"role": "tool", "tool_call_id": "c1", "content": agent.INTERRUPTED}
    assert notes[-1] == "interrupted"


def test_the_turn_stops_after_max_calls(quiet, monkeypatch):
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    monkeypatch.setattr(agent, "MAX_CALLS", 3)
    forever = lambda messages, tools=None, on_delta=None: (FakeMessage(content=None, tool_calls=[raw_call("c", "bash", '{"command": "echo again"}')]), {"prompt_tokens": 1, "completion_tokens": 1})
    monkeypatch.setattr(agent, "call_llm", forever)
    messages = agent.turn([{"role": "system", "content": "s"}], "loop")
    assert sum(1 for m in messages if m["role"] == "assistant") == 3
    assert messages[-1]["role"] == "tool"  # every call answered before the stop
    assert notes[-1] == "stopped after 3 model calls in one turn; say 'continue' to go on"


def test_session_load_repairs_a_dangling_tool_call(tmp_path, monkeypatch):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    pending = {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]}
    (tmp_path / "old.jsonl").write_text("".join(json.dumps(m) + "\n" for m in [{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}, pending]), encoding="utf-8")
    messages = session.load("old")
    assert messages[-1] == {"role": "tool", "tool_call_id": "c1", "content": session.UNANSWERED}
    assert session.repair([{"role": "user", "content": "hi"}]) == [{"role": "user", "content": "hi"}]  # nothing to repair


def test_rewind_offers_only_user_messages_and_leaves_no_orphan(tmp_path, monkeypatch):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(commands, "redraw", lambda messages, label: messages)
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "x"},
        {"role": "assistant", "content": "done"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "ok"},
    ]
    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.extend(rows) or 1)
    kept = commands.handle("/rewind", list(messages))
    assert len(offered) == 2 and "first" in offered[0] and "second" in offered[1]  # never the tool call
    assert kept == messages[:5]
    monkeypatch.setattr(ui, "pick", lambda title, rows: 0)
    assert commands.handle("/rewind", list(messages)) == messages[:1]
    assert (tmp_path / f"{session.CURRENT}.jsonl").exists()  # a fresh chat got its file before the marker


def test_write_todos_rejects_a_bad_status_and_leaves_the_list_alone(monkeypatch):
    monkeypatch.setattr(todos, "TODOS", [{"content": "a", "activeForm": "doing a", "status": "in_progress"}])
    before = list(todos.TODOS)
    assert todos.write_todos([{"content": "b", "activeForm": "doing b", "status": "done"}]).startswith("Error: item 0 has status 'done'")
    assert todos.write_todos([{"content": "b"}]) == "Error: item 0 needs a non-empty 'activeForm'."
    assert todos.write_todos("b").startswith("Error:")
    assert todos.write_todos([{"content": "b", "activeForm": "b", "status": "in_progress"}, {"content": "c", "activeForm": "c", "status": "in_progress"}]).startswith("Error: 2 tasks are in_progress")
    assert todos.TODOS == before


def test_utf8_survives_write_file_read_file_and_bash(tmp_path):
    path = tmp_path / "näme.txt"
    text = "héllo wörld — ünïcode ✓\r\nline two\n"
    assert tools.write_file(str(path), text).startswith("Wrote")
    assert tools.read_file(str(path)) == text  # bytes and line endings as written
    assert tools.str_replace(str(path), "", "x") == "Error: old_str is empty."
    assert tools.bash(f'"{sys.executable}" -X utf8 -c "print(\'ünïcode ✓\')"').strip() == "ünïcode ✓"
    assert tools.write_file(str(tmp_path / "deep" / "er" / "file.txt"), "x") == f"Wrote {tmp_path / 'deep' / 'er' / 'file.txt'}"  # parents are created
