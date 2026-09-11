import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import agent, llm, permissions, session  # noqa: E402
from harness.ui import ui  # noqa: E402


def test_verdicts():
    assert permissions.decide("ls -la") == "allow"
    assert permissions.decide("git status && git diff") == "allow"
    assert permissions.decide("ls | python setup.py") == "ask"
    assert permissions.decide("cat f; rm -rf /") == "deny"
    assert permissions.split_command('grep "a|b" f | sort') == ['grep "a|b" f', "sort"]
    assert permissions.check("write_file", {"path": "x.txt", "content": ""})[0] == "allow"
    assert permissions.check("write_file", {"path": str(Path.home() / "x"), "content": ""})[0] == "ask"


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def test_loop_denies_asks_and_allows(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    seen = []
    replies = [
        FakeMessage(content=None, tool_calls=[call("c1", "bash", '{"command": "sudo ls"}'),
                                              call("c2", "bash", '{"command": "python -c 1"}'),
                                              call("c3", "bash", '{"command": "echo fine"}')]),
        FakeMessage(content="done", tool_calls=None),
    ]

    def fake(messages, **kw):
        seen.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(agent, "call_llm", fake)  # agent.py binds call_llm by name at import
    monkeypatch.setattr(ui, "approve", lambda reason: False)
    inputs = iter(["go", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(sys, "argv", ["harness"])
    agent.main()

    results = [m["content"] for m in seen[1] if m["role"] == "tool"]
    assert results[0].startswith("Blocked by policy")
    assert results[1] == "The user denied this tool call."
    assert results[2].strip() == "fine"
