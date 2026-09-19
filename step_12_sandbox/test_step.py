import os
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, sandbox, session, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


def test_sandbox_name_and_run():
    assert sandbox.name() in {"seatbelt", "bubblewrap", "none"}
    assert sandbox.run("echo boxed").stdout.strip() == "boxed"


def test_timeout_is_a_result_not_a_crash(monkeypatch):
    def slow(command, timeout=60):
        raise subprocess.TimeoutExpired(command, timeout, output="partial")

    monkeypatch.setattr(sandbox, "run", slow)
    assert tools.bash("sleep 999") == "Timed out after 60s and was killed. Output so far:\npartial"


def test_a_timeout_kills_the_whole_tree():
    # the shell starts a child that keeps the pipe open; the timeout must not wait for it
    child = "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)']); time.sleep(20)"
    started = time.time()
    with pytest.raises(subprocess.TimeoutExpired):
        sandbox.run(f'python -c "{child}"', timeout=1)
    assert time.time() - started < 10


def test_no_stdin_and_no_pager():
    assert sandbox.run("python -c \"import sys; print(repr(sys.stdin.read()))\"").stdout.strip() == "''"
    assert sandbox.run("python -c \"import os; print(os.environ['GIT_PAGER'])\"").stdout.strip() == "cat"


@pytest.mark.skipif(sandbox.name() == "none", reason="no OS sandbox on this platform")
def test_the_sandbox_blocks_writes_outside_the_project():
    result = sandbox.run('touch "$HOME/.simple-harness-probe" 2>&1; echo rc=$?; rm -f "$HOME/.simple-harness-probe"')
    assert "rc=0" not in result.stdout          # the home directory is read-only inside the box
    assert sandbox.run("touch .sandbox-probe; echo rc=$?; rm -f .sandbox-probe").stdout.strip().endswith("rc=0")


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


def test_bad_tool_calls_become_results_not_crashes(monkeypatch, tmp_path):
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    replies = [
        FakeMessage(content=None, tool_calls=[
            call("c1", "no_such_tool", "{}"),
            call("c2", "bash", '{"command": "ls"'),
            call("c3", "read_file", '{"path": "missing.txt"}'),
        ]),
        FakeMessage(content="carried on", tool_calls=None),
    ]
    seen = run_loop(monkeypatch, tmp_path, replies, ["go", "/exit"])
    results = {m["tool_call_id"]: m["content"] for m in seen[1] if m["role"] == "tool"}
    assert set(results) == {"c1", "c2", "c3"}
    assert results["c1"] == "Error: no tool named 'no_such_tool'."
    assert results["c2"].startswith("Error: the arguments of bash are not a JSON object")
    assert results["c3"].startswith("Error:")
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
