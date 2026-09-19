"""Offline: drive the loop with a scripted model, checking the feedback of tool results."""

import runpy
import sys
from types import SimpleNamespace

import openai
import pytest


class Call(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"id": self.id, "type": "function",
                "function": {"name": self.function.name, "arguments": self.function.arguments}}


def call(cid, name, arguments):
    return Call(id=cid, type="function", function=SimpleNamespace(name=name, arguments=arguments))


def reply(content=None, tool_calls=None):
    # what a real reply looks like: extra provider fields the loop must not echo back
    return SimpleNamespace(content=content, tool_calls=tool_calls, reasoning="secret thoughts", annotations=[])


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


def run(monkeypatch, fake, prompt="explain tools.py"):
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", lambda _: prompt)
    sys.modules.pop("llm", None)  # llm builds its client at import: make it import again
    runpy.run_path("agent.py", run_name="__main__")


def test_loop_feeds_results_back_until_a_plain_answer(monkeypatch, capsys):
    fake = FakeClient([
        reply(tool_calls=[call("c1", "bash", '{"command": "echo alpha"}')]),
        reply(tool_calls=[call("c2", "read_file", '{"path": "tools.py"}')]),
        reply(content="done explaining"),
    ])
    run(monkeypatch, fake)

    assert len(fake.requests) == 3
    second = fake.requests[1]
    assert second[2]["role"] == "assistant" and second[2]["tool_calls"][0]["id"] == "c1"
    assert set(second[2]) == {"role", "content", "tool_calls"}          # no reasoning/annotations echoed back
    assert second[3]["role"] == "tool" and second[3]["tool_call_id"] == "c1" and "alpha" in second[3]["content"]
    third = fake.requests[2]
    assert [m["role"] for m in third] == ["system", "user", "assistant", "tool", "assistant", "tool"]
    assert "Stage 2.3" not in third[5]["content"] and "read_file" in third[5]["content"]  # this step's tools.py
    assert "Agent:  done explaining" in capsys.readouterr().out


def test_bad_calls_get_a_tool_message_each_and_the_loop_goes_on(monkeypatch, capsys):
    fake = FakeClient([
        reply(tool_calls=[
            call("c1", "bash", '{"command": '),                 # malformed JSON
            call("c2", "no_such_tool", '{}'),                    # unknown tool
            call("c3", "read_file", '{"path": "missing.txt"}'),  # a tool that raises
        ]),
        reply(content="recovered"),
    ])
    run(monkeypatch, fake)
    second = fake.requests[1]
    results = {m["tool_call_id"]: m["content"] for m in second if m["role"] == "tool"}
    assert set(results) == {"c1", "c2", "c3"}                          # one tool message per call, always
    assert results["c1"].startswith("Error: the arguments of bash are not a JSON object")
    assert results["c2"] == "Error: no tool named 'no_such_tool'."
    assert results["c3"].startswith("Error: FileNotFoundError:")
    assert "Agent:  recovered" in capsys.readouterr().out


def test_the_loop_stops_after_max_calls(monkeypatch, capsys):
    fake = FakeClient([reply(tool_calls=[call(f"c{i}", "bash", '{"command": "echo again"}')]) for i in range(50)])
    run(monkeypatch, fake)
    assert len(fake.requests) == 40
    assert "stopped after 40 model calls" in capsys.readouterr().out


def test_eof_exits_cleanly(monkeypatch):
    def eof(_):
        raise EOFError
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: FakeClient([]))
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", eof)
    sys.modules.pop("llm", None)
    with pytest.raises(SystemExit, match="no prompt given"):
        runpy.run_path("agent.py", run_name="__main__")
