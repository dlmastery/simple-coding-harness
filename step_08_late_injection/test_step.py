from types import SimpleNamespace

from harness import agent, context, llm

USAGE = {"prompt_tokens": 1, "completion_tokens": 1, "reasoning_tokens": None, "cached_tokens": None}


def test_env_block_has_time_and_branch():
    block = context.env_block()
    assert block.startswith("<env>") and "time: 20" in block and "git branch:" in block


def test_injection_is_sent_but_never_stored(monkeypatch):
    seen = []

    def fake(messages, tools=None):
        seen.append(list(messages))
        return SimpleNamespace(content="ok", tool_calls=None), USAGE

    monkeypatch.setattr(llm, "complete", fake)
    messages = [{"role": "system", "content": "s"}]
    agent.turn(messages, "hi")
    agent.turn(messages, "again")

    # Each request ends with the env block...
    assert all(req[-1]["content"].startswith("<env>") for req in seen)
    # ...but the stored transcript never contains it.
    assert not any("<env>" in (m.get("content") or "") for m in messages)
    # And the stored prefix of request 2 equals request 1 minus its injection.
    assert seen[1][: len(seen[0]) - 1] == seen[0][:-1]
