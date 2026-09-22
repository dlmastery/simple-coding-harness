import os
import sys
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, prompt, session, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


def test_todos_render_as_a_checklist_not_raw_output(capsys):
    plan = [{"content": "Read it", "activeForm": "Reading", "status": "completed"},
            {"content": "Edit it", "activeForm": "Editing", "status": "in_progress"}]
    ui.tool("write_todos", {"todos": plan}, "raw text that must not be shown")
    out = capsys.readouterr().out
    assert "todos 1/2" in out and "Edit it" in out and "raw text" not in out


def test_a_refused_plan_shows_the_error_not_a_checklist(capsys):
    bad = [{"content": "a", "activeForm": "b", "status": "done"}]
    result = todos.write_todos(bad)
    ui.tool("write_todos", {"todos": bad}, result)          # what the loop does with the result
    out = capsys.readouterr().out
    assert "Error: item 0" in out and "todos 0/1" not in out
    ui.todos(bad)                                          # and a stray status never raises
    assert "[?]" in capsys.readouterr().out


def test_input_line_falls_back_to_input_without_a_terminal(monkeypatch):
    assert prompt.HISTORY.name == "history"
    monkeypatch.setattr("builtins.input", lambda p: "typed " + p)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    assert prompt.read("> ") == "typed > "                 # piped stdin, tests, plain pipes


def test_an_empty_line_does_not_end_the_chat(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    monkeypatch.setattr(agent, "call_llm", lambda messages, **kw: (_ for _ in ()).throw(AssertionError("no call expected")))
    reads = iter(["", "   ", "/exit"])
    monkeypatch.setattr(prompt, "read", lambda p: next(reads))
    monkeypatch.setattr(sys, "argv", ["harness"])
    agent.main()                                            # returned on /exit, never called the model

    def ctrl_d(p):
        raise EOFError

    monkeypatch.setattr(prompt, "read", ctrl_d)
    assert ui.ask() is None                                  # leaving is None, an empty line is ""


class FakeCall(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"id": self.id, "type": "function", "function": {"name": self.function.name, "arguments": self.function.arguments}}


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"role": "assistant", "content": self.content}


def call(cid, name, arguments):
    return FakeCall(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


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
