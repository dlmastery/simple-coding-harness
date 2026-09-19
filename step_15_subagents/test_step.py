import os
import sys
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, llm, prompt, session, subagent, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeCall(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"id": self.id, "type": "function", "function": {"name": self.function.name, "arguments": self.function.arguments}}


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"role": "assistant", "content": self.content}


def call(cid, name, arguments):
    return FakeCall(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def test_toolset_withholds_edits_plan_and_recursion():
    names = {s["function"]["name"] for s in subagent.toolset()}
    assert names == set(tools.TOOLS) - subagent.WITHHELD
    assert {"task", "write_todos", "str_replace", "write_file"}.isdisjoint(names) and "bash" in names


def test_subagent_starts_empty_and_returns_only_its_report(monkeypatch):
    requests = []
    replies = [FakeMessage(content=None, tool_calls=[call("s1", "bash", '{"command": "echo found-it"}')]),
               FakeMessage(content="report: found-it at x.py:3", tool_calls=None)]

    def fake(messages, tools=None):
        requests.append(([dict(m) for m in messages], tools))
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(llm, "call_llm", fake)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    assert subagent.task("where is found-it?") == "report: found-it at x.py:3"
    first, offered = requests[0]
    assert [m["role"] for m in first] == ["system", "user"]                       # rule 1
    assert "task" not in {s["function"]["name"] for s in offered}                 # rule 2
    assert requests[1][0][3]["role"] == "tool" and "found-it" in requests[1][0][3]["content"]  # rule 3
    assert set(requests[1][0][2]) == {"role", "content", "tool_calls"}                # entry(), not model_dump()


def test_a_withheld_tool_is_denied_even_if_the_subagent_names_it(monkeypatch):
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    allowed = {s["function"]["name"] for s in subagent.toolset()}
    _, result = tools.execute(call("w1", "write_file", '{"path": "x.txt", "content": "no"}'), allowed)
    assert result == "Blocked by policy: write_file is not available to this agent" and not os.path.exists("x.txt")
    _, result = tools.execute(call("w2", "task", '{"description": "recurse"}'), allowed)
    assert result.startswith("Blocked by policy: task is not available")


def test_a_failing_tool_or_model_call_inside_the_subagent_is_a_report_not_a_crash(monkeypatch):
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    replies = [FakeMessage(content=None, tool_calls=[call("s1", "read_file", '{"path": "missing.txt"}'), call("s2", "bash", "{")]),
               FakeMessage(content="could not read it", tool_calls=None)]
    seen = []

    def fake(messages, tools=None):
        seen.append([dict(m) for m in messages])
        return replies.pop(0), {}

    monkeypatch.setattr(llm, "call_llm", fake)
    assert subagent.task("read missing.txt") == "could not read it"
    results = {m["tool_call_id"]: m["content"] for m in seen[1] if m["role"] == "tool"}
    assert results["s1"].startswith("Error:") and results["s2"].startswith("Error: the arguments of bash")

    def dead(messages, tools=None):
        raise RuntimeError("empty reply")

    monkeypatch.setattr(llm, "call_llm", dead)
    assert subagent.task("q").startswith("(the subagent's model call failed: empty reply")
    _, result = tools.execute(call("m1", "task", '{"description": "q"}'))  # and the main agent sees a plain result
    assert result.startswith("(the subagent's model call failed")


def test_main_agent_gets_the_report_and_the_same_permissions(monkeypatch):
    monkeypatch.setattr(ui, "approve", lambda reason: False)
    _, blocked = tools.execute(call("m1", "bash", '{"command": "sudo ls"}'))
    assert blocked.startswith("Blocked by policy")
    _, declined = tools.execute(call("m2", "bash", '{"command": "python -c 1"}'))
    assert declined == "The user denied this tool call."
    assert tools.TOOLS["task"] is subagent.task and "task" in {s["function"]["name"] for s in tools.TOOL_SCHEMAS}


def test_runaway_subagent_is_cut_off(monkeypatch):
    monkeypatch.setattr(subagent, "MAX_TURNS", 2)
    monkeypatch.setattr(llm, "call_llm", lambda messages, tools=None: (FakeMessage(content="still looking", tool_calls=[call("x", "bash", '{"command": "echo more"}')]), {}))
    out = subagent.task("q")
    assert out.startswith("(stopped after 2 turns") and "still looking" in out


def run_loop(monkeypatch, tmp_path, replies, inputs):
    """Drive main() with scripted replies and typed lines; return every request sent."""
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    seen = []

    def fake(messages, **kw):
        seen.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(agent, "call_llm", fake)  # agent.py binds call_llm by name at import
    lines = iter(inputs)

    def typed(_prompt):
        try:
            return next(lines)
        except StopIteration:
            raise EOFError  # ctrl-d once the script runs out

    monkeypatch.setattr(prompt, "read", typed)
    monkeypatch.setattr(sys, "argv", ["harness"])
    agent.main()
    return seen


def test_bad_tool_calls_become_results_not_crashes(monkeypatch, tmp_path):
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    replies = [
        FakeMessage(content=None, tool_calls=[
            call("c1", "no_such_tool", "{}"),
            call("c2", "bash", '{"command": "ls"'),
            call("c3", "read_file", '{"path": "missing.txt"}'),
            call("c4", "write_todos", '{"todos": [{"content": "a", "activeForm": "b", "status": "done"}]}'),
        ]),
        FakeMessage(content="carried on", tool_calls=None),
    ]
    seen = run_loop(monkeypatch, tmp_path, replies, ["go"])   # then ctrl-d
    results = {m["tool_call_id"]: m["content"] for m in seen[1] if m["role"] == "tool"}
    assert set(results) == {"c1", "c2", "c3", "c4"}
    assert results["c1"] == "Error: no tool named 'no_such_tool'."
    assert results["c2"].startswith("Error: the arguments of bash are not a JSON object")
    assert results["c3"].startswith("Error:") and results["c4"].startswith("Error: item 0")
    assert session.load(session.CURRENT)[-1]["content"] == "carried on"


def test_utf8_round_trip(tmp_path):
    path = str(tmp_path / "tree.md")
    text = "├── café Łódź 🎉\n"
    assert tools.write_file(path, text) == f"Wrote {path}"
    assert tools.read_file(path) == text
    utf8_bytes = "import sys; sys.stdout.buffer.write('Łódź'.encode('utf-8'))"
    assert tools.bash(f'python -X utf8 -c "{utf8_bytes}"') == "Łódź"


def test_rewind_offers_only_user_messages_and_load_repairs(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "fresh")
    monkeypatch.setattr(session, "WRITTEN", 0)
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "r"},
        {"role": "assistant", "content": "done"},
        {"role": "user", "content": "two"},
    ]
    offered = {}
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.setdefault("rows", rows) and 1)
    monkeypatch.setattr(ui, "clear", lambda: None)
    kept = commands.rewind(messages)
    assert offered["rows"] == ["one", "two"] and kept[-1]["content"] == "done"
    session.save(kept + [{"role": "assistant", "content": None, "tool_calls": [{"id": "c9", "type": "function", "function": {"name": "bash", "arguments": "{"}}]}])
    loaded = session.load(session.CURRENT)
    assert loaded[-1] == {"role": "tool", "tool_call_id": "c9", "content": session.STOPPED}
    ui.replay(loaded)
