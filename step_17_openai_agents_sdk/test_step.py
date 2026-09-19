"""Offline tests. The Runner is never invoked; we test what we own."""

import asyncio
from pathlib import Path

import pytest

pytest.importorskip("agents")

import harness  # noqa: E402
from agents import AgentsException, MaxTurnsExceeded  # noqa: E402
from agents.run import CallModelData, ModelInputData  # noqa: E402


def test_tool_implementations_are_the_step_7_ones(tmp_path):
    f = (tmp_path / "deep" / "a.txt").as_posix()   # the parent directory is created
    assert "Wrote" in harness._write_file(f, "x = 1\ny = 2\n")
    assert "Replaced 1" in harness._str_replace(f, "y = 2", "y = 3")
    assert harness._read_file(f) == "x = 1\ny = 3\n"
    assert "not found" in harness._str_replace(f, "zzz", "q")
    assert harness._str_replace(f, "", "q") == "Error: old_str is empty"
    assert asyncio.run(harness._bash("echo hi")).strip() == "hi"
    assert "# Explaining code" in harness._read_skill("explain-code")
    assert "No skill named" in harness._read_skill("nope")


def test_file_tools_keep_utf8_and_line_endings(tmp_path):
    f = (tmp_path / "u.txt").as_posix()
    harness._write_file(f, "café → …\r\nline 2\n")
    assert harness._read_file(f) == "café → …\r\nline 2\n"
    out = asyncio.run(harness._bash(f'python -X utf8 -c "print(open(r\'{f}\', encoding=\'utf-8\').read())"'))
    assert "café" in out


def test_bash_kills_a_hung_command_and_caps_output(monkeypatch):
    monkeypatch.setattr(harness, "TIMEOUT", 1)
    assert harness.run_command("python -c \"import time; time.sleep(30)\"") == "Error: command timed out after 1s"
    monkeypatch.setattr(harness, "TIMEOUT", 60)
    long = harness.run_command("python -c \"print('x' * 30000)\"")
    assert "[output capped:" in long and len(long) < 11_000


def test_function_tools_carry_schemas_and_policy_wiring():
    names = {t.name for t in harness.build_agent(model_override="gpt-4.1-mini").tools}
    assert names == {"bash", "read_file", "write_file", "str_replace", "read_skill", "write_todos", "task"}
    assert harness.bash.params_json_schema["properties"]["command"]["type"] == "string"
    assert "allow_multi" in harness.str_replace.params_json_schema["properties"]
    assert harness.bash.needs_approval is harness.bash_needs_approval
    assert harness.write_file.needs_approval is harness.edit_needs_approval


def test_policy_verdicts():
    assert harness.verdict_for("bash", {"command": "ls"})[0] == "allow"
    assert harness.verdict_for("bash", {"command": "cat f | sudo x"})[0] == "deny"
    assert harness.verdict_for("write_file", {"path": "harness.py"})[0] == "allow"
    assert harness.verdict_for("write_file", {"path": str(Path.home() / "x")})[0] == "ask"
    assert asyncio.run(harness.bash_needs_approval(None, {"command": "python -c 1"}, "c")) is True
    assert asyncio.run(harness.bash_needs_approval(None, {"command": "git diff"}, "c")) is False
    assert asyncio.run(harness.edit_needs_approval(None, {"path": str(Path.home() / "x")}, "c")) is True


def test_guardrail_rejects_denied_commands():
    class Ctx:
        tool_name = "bash"
        tool_arguments = '{"command": "rm -rf /"}'

    data = type("D", (), {"context": Ctx(), "agent": None})()
    out = harness.policy_gate.guardrail_function(data)
    assert out.behavior["type"] == "reject_content" and "Blocked by policy" in out.behavior["message"]
    Ctx.tool_arguments = '{"command": "ls"}'
    assert harness.policy_gate.guardrail_function(data).behavior["type"] == "allow"


def test_shape_request_strips_old_outputs_and_appends_reminder():
    harness._write_todos([{"content": "Do it", "active": "Doing it", "status": "in_progress"}])
    items = [{"role": "user", "content": "go"}]
    for i in range(5):
        items += [
            {"type": "function_call", "call_id": f"c{i}", "name": "bash", "arguments": "{}"},
            {"type": "function_call_output", "call_id": f"c{i}", "output": "o" * 1000},
        ]
    data = CallModelData(model_data=ModelInputData(input=items, instructions="sys"), agent=None, context=None)
    shaped = harness.shape_request(data)

    outputs = [i for i in shaped.input if i.get("type") == "function_call_output"]
    assert "[output trimmed" in outputs[0]["output"] and "[output trimmed" in outputs[1]["output"]
    assert outputs[-1]["output"] == "o" * 1000                       # newest three untouched
    assert items[1 + 1]["output"] == "o" * 1000                       # the original list was not mutated
    tail = shaped.input[-1]
    assert tail["role"] == "system" and "<env>" in tail["content"] and "[~] Do it" in tail["content"]
    assert shaped.instructions == "sys"

    sub = harness.shape_subagent_request(data)  # the explorer: stripped, but no plan, no reminder
    assert sub.input[-1]["type"] == "function_call_output" and all(i.get("role") != "system" for i in sub.input)
    harness._write_todos([])


def test_write_todos_rejects_a_bad_status_and_keeps_the_old_list():
    harness._write_todos([{"content": "Keep me", "active": "Keeping", "status": "pending"}])
    out = harness._write_todos([{"content": "Bad", "active": "Bad", "status": "finished"}])
    assert out.startswith("Error: item 0") and harness.todos_prompt() == "[ ] Keep me"
    assert harness._write_todos([{"content": "a", "active": "a", "status": "in_progress"}, {"content": "b", "active": "b", "status": "in_progress"}]).startswith("Error")
    harness._write_todos([])


def test_changes_note_moves_the_baseline_only_when_marked_seen(monkeypatch):
    states = iter([{"a.py": ("M", "1")}, {"a.py": ("M", "1")}, {"a.py": ("M", "2")}])
    monkeypatch.setattr(harness, "git_state", lambda: next(states))
    monkeypatch.setattr(harness, "LAST", {})
    monkeypatch.setattr(harness, "PENDING", None)
    assert "modified: a.py" in harness.changes_note()
    assert "modified: a.py" in harness.changes_note()  # the call failed, nobody marked it seen: still reported
    harness.mark_seen()
    assert harness.LAST == {"a.py": ("M", "1")}
    assert "modified: a.py" in harness.changes_note()  # a new hash: reported again


def test_subagent_is_an_agent_as_tool_with_its_own_hooks_and_filter():
    assert harness.task.name == "task"
    assert {t.name for t in harness.explorer.tools} == {"bash", "read_file", "read_skill"}  # no edits, no task
    # as_tool keeps its arguments in a closure: check them through the source it was built from
    import inspect

    src = inspect.getsource(harness)
    assert "hooks=CONSOLE" in src and "call_model_input_filter=shape_subagent_request" in src


def test_turn_never_raises(monkeypatch):
    async def exceed(*args, **kwargs):
        raise MaxTurnsExceeded("Max turns (40) exceeded")

    monkeypatch.setattr(harness.Runner, "run", exceed)
    out = asyncio.run(harness.turn(None, None, "hi", None, None))
    assert out.startswith("(turn stopped: MaxTurnsExceeded")

    async def dead(*args, **kwargs):
        raise ConnectionError("endpoint down")

    monkeypatch.setattr(harness.Runner, "run", dead)
    assert asyncio.run(harness.turn(None, None, "hi", None, None)).startswith("(model call failed: ConnectionError")
    assert issubclass(MaxTurnsExceeded, AgentsException)


def test_rewind_pops_one_turn(tmp_path):
    from agents import SQLiteSession

    session = SQLiteSession("s1", db_path=tmp_path / "t.sqlite")
    asyncio.run(session.add_items([
        {"role": "user", "content": "a"}, {"role": "assistant", "content": "b"},
        {"role": "user", "content": "c"}, {"role": "assistant", "content": "d"},
    ]))
    assert asyncio.run(harness.rewind(session)) == 2
    assert [i["content"] for i in asyncio.run(session.get_items())] == ["a", "b"]
