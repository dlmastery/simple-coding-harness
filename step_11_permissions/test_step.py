import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, permissions, session, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


def test_verdicts():
    assert permissions.decide("ls -la") == "allow"
    assert permissions.decide("git status && git diff") == "allow"
    assert permissions.decide("ls | python setup.py") == "ask"
    assert permissions.decide("cat f; rm -rf /") == "deny"
    assert permissions.split_command('grep "a|b" f | sort') == ['grep "a|b" f', "sort"]
    assert permissions.check("write_file", {"path": "x.txt", "content": ""})[0] == "allow"
    assert permissions.check("write_file", {"path": str(Path.home() / "x"), "content": ""})[0] == "ask"


def test_what_the_rules_cannot_read_asks():
    # a command hidden inside another one
    assert permissions.decide("echo $(rm -rf /)") == "ask"
    assert permissions.decide("ls `rm -rf ~`") == "ask"
    assert permissions.decide("diff <(ls) <(ls)") == "ask"
    # a newline is a separator, so the second line is rated on its own
    assert permissions.decide("echo hi\nrm -rf /") == "deny"
    # an allowed verb that writes
    assert permissions.decide("echo secret > ~/.bashrc") == "ask"
    assert permissions.decide("cat /dev/null > important.py") == "ask"
    assert permissions.decide("ls | tee out.txt") == "ask"
    assert permissions.decide("find . -name '*.pyc' -delete") == "ask"
    assert permissions.decide("find . -name x -exec rm {} +") == "ask"
    assert permissions.decide("find . -name x") == "allow"
    # ... but a > inside quotes is text, and 2>&1 is not a separator
    assert permissions.decide("grep '>' f") == "allow"
    assert permissions.decide("cat f 2>&1") == "allow"
    assert permissions.split_command("cat f 2>&1 | head -3") == ["cat f 2>&1", "head -3"]
    # env would print API_KEY into the transcript
    assert permissions.decide("env") == "ask"
    # missing arguments and hooks in .git
    assert permissions.check("bash", {}) == ("deny", "bash: missing argument 'command'")
    assert permissions.check("write_file", {"path": ".git/hooks/pre-commit", "content": ""})[0] == "ask"


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


def test_loop_denies_asks_and_allows(monkeypatch, tmp_path):
    replies = [
        FakeMessage(content=None, tool_calls=[call("c1", "bash", '{"command": "sudo ls"}'),
                                              call("c2", "bash", '{"command": "python -c 1"}'),
                                              call("c3", "bash", '{"command": "echo fine"}')]),
        FakeMessage(content="done", tool_calls=None),
    ]
    monkeypatch.setattr(ui, "approve", lambda reason: False)
    seen = run_loop(monkeypatch, tmp_path, replies, ["go", "/exit"])
    results = [m["content"] for m in seen[1] if m["role"] == "tool"]
    assert results[0].startswith("Blocked by policy")
    assert results[1] == "The user denied this tool call."
    assert results[2].strip() == "fine"


def test_bad_tool_calls_become_results_not_crashes(monkeypatch, tmp_path):
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    replies = [
        FakeMessage(content=None, tool_calls=[
            call("c1", "no_such_tool", "{}"),
            call("c2", "bash", '{"command": "ls"'),
            call("c3", "bash", "{}"),                          # the rules cannot rate a missing command
            call("c4", "read_file", '{"path": "missing.txt"}'),
        ]),
        FakeMessage(content="carried on", tool_calls=None),
    ]
    seen = run_loop(monkeypatch, tmp_path, replies, ["go", "/exit"])
    results = {m["tool_call_id"]: m["content"] for m in seen[1] if m["role"] == "tool"}
    assert set(results) == {"c1", "c2", "c3", "c4"}                   # one tool message per call
    assert results["c1"] == "Error: no tool named 'no_such_tool'."
    assert results["c2"].startswith("Error: the arguments of bash are not a JSON object")
    assert results["c3"] == "Blocked by policy: bash: missing argument 'command'"
    assert results["c4"].startswith("Error:")
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
