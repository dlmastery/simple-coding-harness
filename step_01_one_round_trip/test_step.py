"""Offline smoke test: swap the model call for a canned reply."""

from types import SimpleNamespace

import agent


def test_round_trip_prints_reply(monkeypatch, capsys):
    monkeypatch.setattr(agent, "complete", lambda messages: SimpleNamespace(content="hi there"))
    monkeypatch.setattr("builtins.input", lambda _: "hello")
    agent.main()
    assert "agent> hi there" in capsys.readouterr().out
