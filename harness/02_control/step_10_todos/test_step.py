import os
import sys
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, context, session, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402

PLAN = [
    {"content": "Write hello.txt", "activeForm": "Writing hello.txt", "status": "completed"},
    {"content": "Write the star pattern", "activeForm": "Writing the star pattern", "status": "in_progress"},
    {"content": "Write fibonacci", "activeForm": "Writing fibonacci", "status": "pending"},
]


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

    monkeypatch.setattr("builtins.input", typed)
    monkeypatch.setattr(sys, "argv", ["harness"])
    agent.main()
    return seen


def test_write_todos_replaces_the_list_and_validates():
    todos.write_todos([])
    assert "Only one may be" in todos.write_todos([dict(PLAN[1]), dict(PLAN[1])])
    assert todos.write_todos(PLAN) == "[x] Write hello.txt\n[~] Write the star pattern\n[ ] Write fibonacci"
    assert todos.active_form() == "Writing the star pattern"
    assert "<todos>\n[x] Write hello.txt" in context.reminder()["content"]   # re-injected every call
    todos.write_todos([])
    assert todos.active_form() == "thinking" and "<todos>" not in context.reminder()["content"]


def test_a_bad_list_is_refused_and_the_old_plan_stays():
    todos.write_todos(PLAN)
    assert todos.write_todos([{"content": "a", "activeForm": "b", "status": "done"}]).startswith("Error: item 0 has status 'done'")
    assert todos.write_todos([{"content": "a"}]).startswith("Error: item 0 needs")
    assert todos.write_todos("not a list") == "Error: todos must be a list."
    assert todos.TODOS == PLAN                          # untouched, so the injected block still renders
    assert "[~] Write the star pattern" in context.reminder()["content"]
    todos.write_todos([])


def test_the_plan_is_rebuilt_from_a_transcript():
    import json
    messages = [
        {"role": "system", "content": "s"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "write_todos", "arguments": json.dumps({"todos": PLAN})}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "..."},
    ]
    todos.restore(messages)
    assert todos.TODOS == PLAN and todos.active_form() == "Writing the star pattern"
    todos.restore([{"role": "system", "content": "s"}])   # opening a chat without a plan clears it
    assert todos.TODOS == []


def test_it_is_a_tool():
    assert tools.TOOLS["write_todos"] is todos.write_todos
    assert "write_todos" in {s["function"]["name"] for s in tools.TOOL_SCHEMAS}


def test_bad_tool_calls_become_results_not_crashes(monkeypatch, tmp_path):
    replies = [
        FakeMessage(content=None, tool_calls=[
            call("c1", "no_such_tool", "{}"),
            call("c2", "bash", '{"command": "ls"'),
            call("c3", "read_file", '{"path": "missing.txt"}'),
            call("c4", "write_todos", '{"todos": [{"content": "a", "activeForm": "b", "status": "done"}]}'),
        ]),
        FakeMessage(content="carried on", tool_calls=None),
    ]
    seen = run_loop(monkeypatch, tmp_path, replies, ["go", "/exit"])
    results = {m["tool_call_id"]: m["content"] for m in seen[1] if m["role"] == "tool"}
    assert set(results) == {"c1", "c2", "c3", "c4"}                   # one tool message per call
    assert results["c1"] == "Error: no tool named 'no_such_tool'."
    assert results["c2"].startswith("Error: the arguments of bash are not a JSON object")
    assert results["c3"].startswith("Error:") and results["c4"].startswith("Error: item 0")
    assert session.load(session.CURRENT)[-1]["content"] == "carried on"  # the loop went on


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
