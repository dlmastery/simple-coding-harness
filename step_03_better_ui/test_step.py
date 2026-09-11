"""Offline: two chat turns through the two loops, drawn by the rich UI."""

import runpy
from types import SimpleNamespace

import openai


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function",
                                    "function": {"name": c.function.name, "arguments": c.function.arguments}}
                                   for c in self.tool_calls]
        return entry


class FakeClient:
    def __init__(self, replies):
        self.replies, self.requests = list(replies), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append([dict(m) for m in request["messages"]])
        return SimpleNamespace(
            choices=[SimpleNamespace(message=self.replies.pop(0))],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=7,
                                  completion_tokens_details=SimpleNamespace(reasoning_tokens=None),
                                  prompt_tokens_details=SimpleNamespace(cached_tokens=90)),
        )


def test_two_turns_share_one_transcript(monkeypatch, capsys):
    fake = FakeClient([
        FakeMessage(content=None, tool_calls=[call("c1", "bash", '{"command": "echo turn-one"}')]),
        FakeMessage(content="first answer", tool_calls=None),
        FakeMessage(content="second answer", tool_calls=None),
    ])
    inputs = iter(["run echo", "and again", ""])
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    runpy.run_path("agent.py", run_name="__main__")

    out = capsys.readouterr().out
    assert "turn-one" in out and "first answer" in out and "second answer" in out
    assert "90 cached" in out                                  # the usage line shows the cache working
    roles = [m["role"] for m in fake.requests[2]]
    assert roles == ["system", "user", "assistant", "tool", "assistant", "user"]  # turn 2 sees turn 1
