import runpy
from types import SimpleNamespace

import openai


class FakeClient:
    def __init__(self, replies):
        self.replies, self.requests = list(replies), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append(request)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=self.replies.pop(0))],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1,
                                  completion_tokens_details=None, prompt_tokens_details=None),
        )


def call(name, arguments):
    return SimpleNamespace(id="c1", function=SimpleNamespace(name=name, arguments=arguments))


def test_tool_call_is_parsed_and_executed(monkeypatch, capsys):
    fake = FakeClient([SimpleNamespace(content=None, tool_calls=[call("bash", '{"command": "echo from-bash"}')])])
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", lambda _: "what is your current directory?")

    runpy.run_path("llm.py", run_name="__main__")

    out = capsys.readouterr().out
    assert "Tool: bash echo from-bash" in out and "from-bash" in out
    assert fake.requests[0]["tools"][0]["function"]["name"] == "bash"
