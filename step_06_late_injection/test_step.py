import runpy
from types import SimpleNamespace

import openai

import context


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"role": "assistant", "content": self.content}


class FakeClient:
    def __init__(self, replies):
        self.replies, self.requests = list(replies), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append([dict(m) for m in request["messages"]])
        return SimpleNamespace(choices=[SimpleNamespace(message=self.replies.pop(0))],
                               usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1,
                                                     completion_tokens_details=None, prompt_tokens_details=None))


def test_reminder_is_an_env_block():
    block = context.reminder()
    assert block["role"] == "user" and block["content"].startswith("<env>") and "git branch:" in block["content"]


def test_injection_is_sent_but_never_stored(monkeypatch):
    fake = FakeClient([FakeMessage(content="ok", tool_calls=None), FakeMessage(content="ok", tool_calls=None)])
    inputs = iter(["hi", "again", ""])
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    runpy.run_path("agent.py", run_name="__main__")

    first, second = fake.requests
    assert first[-1]["content"].startswith("<env>") and second[-1]["content"].startswith("<env>")
    assert sum("<env>" in m["content"] for m in second) == 1          # exactly one, at the end
    assert second[: len(first) - 1] == first[:-1]                      # the stored prefix is untouched
