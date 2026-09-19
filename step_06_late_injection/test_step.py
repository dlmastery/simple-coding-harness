import runpy
import sys
from types import SimpleNamespace

import openai

import context


class Call(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"id": self.id, "type": "function",
                "function": {"name": self.function.name, "arguments": self.function.arguments}}


def call(cid, name, arguments):
    return Call(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def reply(content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls)


class FakeClient:
    def __init__(self, replies):
        self.replies, self.requests = list(replies), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append([dict(m) for m in request["messages"]])
        return SimpleNamespace(choices=[SimpleNamespace(message=self.replies.pop(0))],
                               usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1,
                                                     completion_tokens_details=None, prompt_tokens_details=None))


def run(monkeypatch, fake, inputs):
    inputs = iter(inputs)

    def read_line(_):
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr(openai, "OpenAI", lambda **kw: fake)
    monkeypatch.setenv("BASE_URL", "http://fake"); monkeypatch.setenv("API_KEY", "x")
    monkeypatch.setattr("builtins.input", read_line)
    sys.modules.pop("llm", None)
    runpy.run_path("agent.py", run_name="__main__")


def test_reminder_is_an_env_block():
    block = context.reminder()
    assert block["role"] == "user" and block["content"].startswith("<env>") and "git branch:" in block["content"]


def test_git_branch_outside_a_repository_says_so(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert context.git_branch() == "(not a git repository)"


def test_injection_is_sent_but_never_stored(monkeypatch):
    fake = FakeClient([reply(content="ok"), reply(content="ok")])
    run(monkeypatch, fake, ["hi", "again"])

    first, second = fake.requests
    assert first[-1]["content"].startswith("<env>") and second[-1]["content"].startswith("<env>")
    assert sum("<env>" in m["content"] for m in second) == 1          # exactly one, at the end
    assert second[: len(first) - 1] == first[:-1]                      # the stored prefix is untouched


def test_bad_tool_calls_still_get_results_with_the_block_last(monkeypatch):
    fake = FakeClient([
        reply(tool_calls=[call("c1", "nope", "{}"), call("c2", "bash", "{bad")]),
        reply(content="fine"),
    ])
    run(monkeypatch, fake, ["go"])
    second = fake.requests[1]
    assert [m["role"] for m in second] == ["system", "user", "assistant", "tool", "tool", "user"]
    assert second[3]["content"] == "Error: no tool named 'nope'."
    assert second[4]["content"].startswith("Error: the arguments of bash are not a JSON object")
    assert second[-1]["content"].startswith("<env>")                   # the block follows the tool results
