"""Offline: drive the loop with a scripted model, checking the feedback of tool results."""

import runpy
from types import SimpleNamespace

import openai


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [
                {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in self.tool_calls
            ]
        return entry


class FakeClient:
    def __init__(self, replies):
        self.replies, self.requests = list(replies), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append([dict(m) for m in request["messages"]])
        return SimpleNamespace(
            choices=[SimpleNamespace(message=self.replies.pop(0))],
            usage=SimpleNamespace(prompt_tokens=len(self.requests) * 10, completion_tokens=1,
                                  completion_tokens_details=None, prompt_tokens_details=None),
        )


def test_loop_feeds_results_back_until_a_plain_answer(monkeypatch, capsys):
    fake = FakeClient([
        FakeMessage(content=None, tool_calls=[call("c1", "bash", '{"command": "echo alpha"}')]),
        FakeMessage(content=None, tool_calls=[call("c2", "read_file", '{"path": "tools.py"}')]),
        FakeMessage(content="done explaining", tool_calls=None),
    ])
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", lambda _: "explain tools.py")

    runpy.run_path("agent.py", run_name="__main__")

    assert len(fake.requests) == 3
    second = fake.requests[1]
    assert second[2]["role"] == "assistant" and second[2]["tool_calls"][0]["id"] == "c1"
    assert second[3]["role"] == "tool" and second[3]["tool_call_id"] == "c1" and "alpha" in second[3]["content"]
    third = fake.requests[2]
    assert [m["role"] for m in third] == ["system", "user", "assistant", "tool", "assistant", "tool"]
    assert "Stage 2.3" not in third[5]["content"] and "read_file" in third[5]["content"]  # this step's tools.py
    assert "Agent:  done explaining" in capsys.readouterr().out
