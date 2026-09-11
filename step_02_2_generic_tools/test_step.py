import runpy
from types import SimpleNamespace

import openai

import tools


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


def test_registry_and_schemas_agree():
    assert set(tools.TOOLS) == {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
    assert tools.bash("echo ok").strip() == "ok"


def test_dispatch_by_name(monkeypatch, capsys):
    fake = FakeClient([SimpleNamespace(content=None, tool_calls=[call("bash", '{"command": "echo via-table"}')])])
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", lambda _: "list files")
    runpy.run_path("llm.py", run_name="__main__")
    out = capsys.readouterr().out
    assert "Tool:  bash {'command': 'echo via-table'}" in out and "via-table" in out
