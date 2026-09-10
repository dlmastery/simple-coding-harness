from types import SimpleNamespace

import agent


def fake_call(name, arguments):
    return SimpleNamespace(id="call_1", function=SimpleNamespace(name=name, arguments=arguments))


def test_tool_call_is_executed(monkeypatch, capsys):
    reply = SimpleNamespace(content=None, tool_calls=[fake_call("bash", '{"command": "echo hello-from-bash"}')])
    monkeypatch.setattr(agent, "complete", lambda messages, tools: reply)
    monkeypatch.setattr("builtins.input", lambda _: "list files")
    agent.main()
    out = capsys.readouterr().out
    assert "tool> bash echo hello-from-bash" in out
    assert "hello-from-bash" in out.strip().splitlines()[-1]


def test_plain_reply_still_works(monkeypatch, capsys):
    monkeypatch.setattr(agent, "complete", lambda messages, tools: SimpleNamespace(content="just text", tool_calls=None))
    monkeypatch.setattr("builtins.input", lambda _: "hi")
    agent.main()
    assert "agent> just text" in capsys.readouterr().out
