from types import SimpleNamespace

import agent


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def test_loop_feeds_results_back_until_text(monkeypatch):
    seen = []
    replies = [
        SimpleNamespace(content=None, tool_calls=[call("c1", "bash", '{"command": "echo alpha"}')]),
        SimpleNamespace(content=None, tool_calls=[call("c2", "bash", '{"command": "echo beta"}')]),
        SimpleNamespace(content="done", tool_calls=None),
    ]

    def fake_complete(messages):
        seen.append([dict(m) for m in messages])
        return replies.pop(0)

    monkeypatch.setattr(agent, "complete", fake_complete)
    messages = [{"role": "system", "content": "s"}]
    answer = agent.turn(messages, "go")

    assert answer == "done"
    assert len(seen) == 3
    # The second call saw the first tool result, tied to its call id.
    tool_msgs = [m for m in seen[1] if m["role"] == "tool"]
    assert tool_msgs[0]["tool_call_id"] == "c1" and "alpha" in tool_msgs[0]["content"]
    # The assistant message that made the call was stored with the call.
    assert seen[1][2]["tool_calls"][0]["id"] == "c1"
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool", "assistant", "tool", "assistant"]


def test_history_persists_across_turns(monkeypatch):
    monkeypatch.setattr(agent, "complete", lambda messages: SimpleNamespace(content="ok", tool_calls=None))
    messages = [{"role": "system", "content": "s"}]
    agent.turn(messages, "one")
    agent.turn(messages, "two")
    assert [m["content"] for m in messages if m["role"] == "user"] == ["one", "two"]
