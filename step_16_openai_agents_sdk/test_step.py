"""Offline tests. The Runner is never invoked; we test what we own."""

import asyncio
from pathlib import Path

import pytest

pytest.importorskip("agents")

import harness  # noqa: E402
from agents.run import CallModelData, ModelInputData  # noqa: E402


def test_tool_implementations_are_the_step_7_ones(tmp_path):
    f = (tmp_path / "a.txt").as_posix()
    assert "Wrote" in harness._write_file(f, "x = 1\ny = 2\n")
    assert "Replaced 1" in harness._str_replace(f, "y = 2", "y = 3")
    assert harness._read_file(f) == "x = 1\ny = 3\n"
    assert "not found" in harness._str_replace(f, "zzz", "q")
    assert asyncio.run(harness._bash("echo hi")).strip() == "hi"
    assert "# Explaining code" in harness._read_skill("explain-code")
    assert "No skill named" in harness._read_skill("nope")


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
    harness._write_todos([])


def test_subagent_is_an_agent_as_tool():
    assert harness.task.name == "task"
    assert {t.name for t in harness.explorer.tools} == {"bash", "read_file", "read_skill"}  # no edits, no task


def test_rewind_pops_one_turn(tmp_path):
    from agents import SQLiteSession

    session = SQLiteSession("s1", db_path=tmp_path / "t.sqlite")
    asyncio.run(session.add_items([
        {"role": "user", "content": "a"}, {"role": "assistant", "content": "b"},
        {"role": "user", "content": "c"}, {"role": "assistant", "content": "d"},
    ]))
    assert asyncio.run(harness.rewind(session)) == 2
    assert [i["content"] for i in asyncio.run(session.get_items())] == ["a", "b"]
