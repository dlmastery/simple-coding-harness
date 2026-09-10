from types import SimpleNamespace

from harness import agent, commands, llm, session
from harness.ui import ui

USAGE = {"prompt_tokens": 1, "completion_tokens": 1, "reasoning_tokens": None, "cached_tokens": None}


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def fresh(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "CURRENT", "s1")
    monkeypatch.setattr(session, "WRITTEN", 0)


def test_every_message_is_saved_and_reloads(monkeypatch, tmp_path):
    fresh(monkeypatch, tmp_path)
    replies = [
        (SimpleNamespace(content=None, tool_calls=[call("c1", "bash", '{"command": "echo hi"}')]), USAGE),
        (SimpleNamespace(content="done", tool_calls=None), USAGE),
    ]
    monkeypatch.setattr(llm, "complete", lambda messages, tools=None: replies.pop(0))
    messages = [{"role": "system", "content": "s"}]
    agent.turn(messages, "run it")

    assert session.load("s1") == messages
    assert session.all_sessions() == [{"id": "s1", "title": "run it"}]


def test_rewind_is_append_only(monkeypatch, tmp_path):
    fresh(monkeypatch, tmp_path)
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    session.save(messages)
    monkeypatch.setattr(ui, "pick", lambda title, rows: 1)  # keep through index 1
    monkeypatch.setattr(ui, "clear", lambda: None)
    kept = commands.handle("/rewind", messages)
    assert [m["content"] for m in kept] == ["s", "a"]
    assert session.load("s1") == kept
    # The rewound-past message is still in the file, after a marker.
    raw = session.path_for("s1").read_text()
    assert '"b"' in raw and '"rewind_to": 2' in raw

    # Appending after a rewind continues from the shorter list.
    kept.append({"role": "assistant", "content": "c"})
    session.save(kept)
    assert [m["content"] for m in session.load("s1")] == ["s", "a", "c"]


def test_unknown_command_lists_help(monkeypatch, tmp_path, capsys):
    fresh(monkeypatch, tmp_path)
    assert commands.handle("/what", []) == []
    assert "/rewind" in capsys.readouterr().out
