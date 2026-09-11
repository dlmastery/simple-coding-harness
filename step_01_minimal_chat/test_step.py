"""Offline: run the script with a fake OpenAI client and a canned prompt."""

import runpy
from types import SimpleNamespace

import openai


class FakeClient:
    def __init__(self, replies):
        self.replies, self.requests = list(replies), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append(request)
        message = self.replies.pop(0)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message)],
            usage=SimpleNamespace(
                prompt_tokens=12, completion_tokens=3,
                completion_tokens_details=SimpleNamespace(reasoning_tokens=None),
                prompt_tokens_details=SimpleNamespace(cached_tokens=0),
            ),
        )


def test_round_trip(monkeypatch, capsys):
    fake = FakeClient([SimpleNamespace(content="print('hi')", tool_calls=None)])
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake")
    monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", lambda _: "write hello world")

    runpy.run_path("llm.py", run_name="__main__")

    out = capsys.readouterr().out
    assert "Agent:  print('hi')" in out and "'prompt_tokens': 12" in out
    sent = fake.requests[0]["messages"]
    assert [m["role"] for m in sent] == ["system", "user"] and sent[1]["content"] == "write hello world"
