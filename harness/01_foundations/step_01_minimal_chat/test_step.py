"""Offline: run the script with a fake OpenAI client and a canned prompt."""

import runpy
from types import SimpleNamespace

import openai
import pytest


class FakeClient:
    def __init__(self, replies, usage="normal"):
        self.replies, self.requests, self.usage = list(replies), [], usage
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append(request)
        message = self.replies.pop(0)
        usage = None if self.usage is None else SimpleNamespace(
            prompt_tokens=12, completion_tokens=3,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=None),
            prompt_tokens_details=SimpleNamespace(cached_tokens=0),
        )
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


def run(monkeypatch, fake, prompt="write hello world"):
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake")
    monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", prompt)
    runpy.run_path("llm.py", run_name="__main__")


def test_round_trip(monkeypatch, capsys):
    fake = FakeClient([SimpleNamespace(content="print('hi')", tool_calls=None)])
    run(monkeypatch, fake, lambda _: "write hello world")

    out = capsys.readouterr().out
    assert "Agent:  print('hi')" in out and "'prompt_tokens': 12" in out
    sent = fake.requests[0]["messages"]
    assert [m["role"] for m in sent] == ["system", "user"] and sent[1]["content"] == "write hello world"


def test_missing_usage_does_not_crash(monkeypatch, capsys):
    fake = FakeClient([SimpleNamespace(content="ok", tool_calls=None)], usage=None)
    run(monkeypatch, fake, lambda _: "hi")
    assert "'prompt_tokens': None" in capsys.readouterr().out


def test_eof_on_stdin_exits_cleanly(monkeypatch):
    def eof(_):
        raise EOFError
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeClient([]), eof)
    assert "no prompt given" in str(exit_info.value)
