from types import SimpleNamespace

from harness import agent, llm, tools


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


USAGE = {"prompt_tokens": 10, "completion_tokens": 5, "reasoning_tokens": None, "cached_tokens": None}


def test_turn_renders_tool_and_answer(monkeypatch, capsys):
    replies = [
        (SimpleNamespace(content=None, tool_calls=[call("c1", "bash", '{"command": "echo tool-ran"}')]), USAGE),
        (SimpleNamespace(content="all done", tool_calls=None), USAGE),
    ]
    monkeypatch.setattr(llm, "complete", lambda messages, tools=None: replies.pop(0))
    messages = [{"role": "system", "content": "s"}]
    assert agent.turn(messages, "go") == "all done"
    out = capsys.readouterr().out
    assert "tool-ran" in out and "all done" in out
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool", "assistant"]


def test_usage_accumulates(monkeypatch, capsys):
    from harness.ui import ui

    ui.totals.clear()
    monkeypatch.setattr(llm, "complete", lambda messages, tools=None: (SimpleNamespace(content="x", tool_calls=None), USAGE))
    agent.turn([{"role": "system", "content": "s"}], "a")
    agent.turn([{"role": "system", "content": "s"}], "b")
    assert ui.totals["prompt_tokens"] == 20


def test_import_needs_no_key():
    assert tools.TOOL_SCHEMAS and llm._client is None
