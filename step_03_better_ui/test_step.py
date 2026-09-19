"""Offline: two chat turns through the two loops, drawn by the rich UI."""

import runpy
import sys
from types import SimpleNamespace

import openai

import tools


class Call(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"id": self.id, "type": "function",
                "function": {"name": self.function.name, "arguments": self.function.arguments}}


def call(cid, name, arguments):
    return Call(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def reply(content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls, reasoning="hidden", annotations=[])


class FakeClient:
    def __init__(self, replies):
        self.replies, self.requests = list(replies), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append([dict(m) for m in request["messages"]])
        answer = self.replies.pop(0)
        if isinstance(answer, BaseException):  # a scripted failure: ctrl-c or the API erroring
            raise answer
        return SimpleNamespace(
            choices=[SimpleNamespace(message=answer)],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=7,
                                  completion_tokens_details=SimpleNamespace(reasoning_tokens=None),
                                  prompt_tokens_details=SimpleNamespace(cached_tokens=90)),
        )


def run(monkeypatch, fake, inputs):
    inputs = iter(inputs)

    def read_line(_):
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError  # what input() raises when stdin is exhausted

    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", read_line)
    sys.modules.pop("llm", None)  # llm builds its client at import
    runpy.run_path("agent.py", run_name="__main__")


def test_two_turns_share_one_transcript(monkeypatch, capsys):
    fake = FakeClient([
        reply(tool_calls=[call("c1", "bash", '{"command": "echo turn-one"}')]),
        reply(content="first answer"),
        reply(content="second answer"),
    ])
    run(monkeypatch, fake, ["run echo", "", "   ", "and again", "/exit"])  # empty lines are skipped, /exit leaves

    out = capsys.readouterr().out
    assert "turn-one" in out and "first answer" in out and "second answer" in out
    assert "90 cached" in out                                  # the usage line shows the cache working
    roles = [m["role"] for m in fake.requests[2]]
    assert roles == ["system", "user", "assistant", "tool", "assistant", "user"]  # turn 2 sees turn 1
    assert set(fake.requests[1][2]) == {"role", "content", "tool_calls"}          # nothing extra echoed back


def test_bad_tool_calls_each_get_a_result_and_the_chat_goes_on(monkeypatch, capsys):
    fake = FakeClient([
        reply(tool_calls=[call("c1", "bash", "{oops"), call("c2", "nope", "{}"),
                          call("c3", "read_file", '{"path": "missing.txt"}')]),
        reply(content="recovered"),
    ])
    run(monkeypatch, fake, ["go"])  # EOF after one turn
    results = {m["tool_call_id"]: m["content"] for m in fake.requests[1] if m["role"] == "tool"}
    assert set(results) == {"c1", "c2", "c3"}
    assert results["c1"].startswith("Error: the arguments of bash are not a JSON object")
    assert results["c2"] == "Error: no tool named 'nope'."
    assert results["c3"].startswith("Error: FileNotFoundError")
    assert "recovered" in capsys.readouterr().out


def test_interrupt_and_api_error_keep_the_transcript_valid(monkeypatch, capsys):
    def ctrl_c(path):
        raise KeyboardInterrupt

    monkeypatch.setitem(tools.TOOLS, "read_file", ctrl_c)
    fake = FakeClient([
        reply(tool_calls=[call("c1", "bash", '{"command": "echo x"}'), call("c2", "read_file", '{"path": "a"}')]),
        openai.APIError("boom", request=None, body=None),        # the model is down on the next turn
        reply(content="back"),
    ])
    run(monkeypatch, fake, ["one", "two", "three"])
    out = capsys.readouterr().out
    assert "interrupted" in out and "model call failed: boom" in out and "back" in out
    second = fake.requests[1]
    assert [m["role"] for m in second] == ["system", "user", "assistant", "tool", "tool", "user"]
    assert second[4] == {"role": "tool", "tool_call_id": "c2", "content": "(interrupted before this tool ran)"}
    assert [m["role"] for m in fake.requests[2]] == [*[m["role"] for m in second], "user"]   # the chat went on


def test_a_tool_that_never_stops_hits_the_cap(monkeypatch, capsys):
    fake = FakeClient([reply(tool_calls=[call(f"c{i}", "bash", '{"command": "echo x"}')]) for i in range(45)])
    run(monkeypatch, fake, ["loop"])
    assert len(fake.requests) == 40 and "stopped after 40 model calls" in capsys.readouterr().out
