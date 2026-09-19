import importlib
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, config, session, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


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


def test_console_script_entry_point_runs_the_same_loop(monkeypatch, tmp_path, capsys):
    replies = [FakeMessage(content="hello from main", tool_calls=None)]
    run_loop(monkeypatch, tmp_path, replies, ["hi", "/exit"])
    assert "hello from main" in capsys.readouterr().out
    assert len(list(tmp_path.glob("*.jsonl"))) == 1        # the session was saved under the home dir


def test_empty_line_continues_and_eof_leaves(monkeypatch, tmp_path):
    seen = run_loop(monkeypatch, tmp_path, [], ["", "   "])  # two empty lines, then ctrl-d
    assert seen == []                                          # no model call, and main() returned


def test_bad_tool_calls_become_results_not_crashes(monkeypatch, tmp_path):
    replies = [
        FakeMessage(content=None, tool_calls=[
            call("c1", "no_such_tool", "{}"),
            call("c2", "bash", '{"command": "ls"'),          # cut-off JSON
            call("c3", "read_file", '{"path": "missing.txt"}'),
            call("c4", "read_file", '{"path": "README.md", "lines": 3}'),  # unexpected argument
        ]),
        FakeMessage(content="carried on", tool_calls=None),
    ]
    seen = run_loop(monkeypatch, tmp_path, replies, ["go", "/exit"])
    results = {m["tool_call_id"]: m["content"] for m in seen[1] if m["role"] == "tool"}
    assert set(results) == {"c1", "c2", "c3", "c4"}                   # one tool message per call
    assert results["c1"] == "Error: no tool named 'no_such_tool'."
    assert results["c2"].startswith("Error: the arguments of bash are not a JSON object")
    assert results["c3"].startswith("Error:")
    assert results["c4"].startswith("Error: TypeError")
    assert session.load(session.CURRENT)[-1]["content"] == "carried on"  # the loop went on


def test_utf8_round_trip(tmp_path):
    path = str(tmp_path / "tree.md")
    text = "├── café Łódź 🎉\n"
    assert tools.write_file(path, text) == f"Wrote {path}"
    assert tools.read_file(path) == text
    utf8_bytes = "import sys; sys.stdout.buffer.write('Łódź'.encode('utf-8'))"
    assert tools.bash(f'python -X utf8 -c "{utf8_bytes}"') == "Łódź"   # decoded as utf-8, whatever the locale
    assert tools.str_replace(path, "", "x") == "Error: old_str is empty."
    assert tools.read_file(str(tmp_path)).startswith("Error:")


def test_rewind_offers_only_user_messages(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "fresh")  # /rewind before anything was saved
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
    assert offered["rows"] == ["one", "two"]            # never an assistant or tool row
    assert kept[-1] == {"role": "assistant", "content": "done"}
    assert session.load(session.CURRENT) == kept


def test_load_repairs_a_dangling_tool_call(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "CURRENT", "s1")
    monkeypatch.setattr(session, "WRITTEN", 0)
    session.save([
        {"role": "system", "content": "s"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{"}}]},
    ])
    loaded = session.load("s1")
    assert loaded[-1] == {"role": "tool", "tool_call_id": "c1", "content": session.STOPPED}
    ui.replay(loaded)  # broken arguments are shown raw, not raised


def test_config_file_fills_gaps_and_the_environment_wins(monkeypatch, tmp_path):
    home = tmp_path / ".simple-harness"
    home.mkdir()
    (home / "env").write_text('MODEL="from-file"\nBASE_URL=http://file\n', encoding="utf-8")
    monkeypatch.setenv("BASE_URL", "http://real")
    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.setattr(config.Path, "home", classmethod(lambda cls: tmp_path))
    fresh = importlib.reload(config)
    assert fresh.MODEL == "from-file" and fresh.BASE_URL == "http://real"   # quotes stripped, env wins
    monkeypatch.undo()
    importlib.reload(config)
    assert 'harness = "harness.agent:main"' in open("pyproject.toml").read()


def test_ctrl_c_mid_turn_leaves_a_valid_transcript(monkeypatch, tmp_path):
    def interrupted(command):
        raise KeyboardInterrupt

    monkeypatch.setitem(tools.TOOLS, "bash", interrupted)
    replies = [FakeMessage(content=None, tool_calls=[call("c1", "bash", '{"command": "x"}'), call("c2", "bash", '{"command": "y"}')])]
    run_loop(monkeypatch, tmp_path, replies, ["go", "/exit"])
    saved = session.load(session.CURRENT)
    assert [m["tool_call_id"] for m in saved if m["role"] == "tool"] == ["c1", "c2"]
    assert saved[-1]["content"] == "(interrupted before this tool ran)"


def test_a_turn_stops_after_max_calls(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "MAX_CALLS", 2)
    forever = [FakeMessage(content=None, tool_calls=[call(f"c{i}", "bash", '{"command": "echo hi"}')]) for i in range(5)]
    seen = run_loop(monkeypatch, tmp_path, forever, ["go", "/exit"])
    assert len(seen) == 2
    assert session.load(session.CURRENT)[-1]["role"] == "tool"   # every call answered, then it stopped
