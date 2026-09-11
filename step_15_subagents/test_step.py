import json
import os
from types import SimpleNamespace

os.environ.setdefault("API_KEY", "x")

from harness import llm, subagent, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def test_toolset_withholds_edits_plan_and_recursion():
    names = {s["function"]["name"] for s in subagent.toolset()}
    assert names == set(tools.TOOLS) - subagent.WITHHELD
    assert {"task", "write_todos", "str_replace", "write_file"}.isdisjoint(names) and "bash" in names


def test_subagent_starts_empty_and_returns_only_its_report(monkeypatch):
    requests = []
    replies = [FakeMessage(content=None, tool_calls=[call("s1", "bash", '{"command": "echo found-it"}')]),
               FakeMessage(content="report: found-it at x.py:3", tool_calls=None)]

    def fake(messages, tools=None):
        requests.append(([dict(m) for m in messages], tools))
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(llm, "call_llm", fake)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    assert subagent.task("where is found-it?") == "report: found-it at x.py:3"
    first, offered = requests[0]
    assert [m["role"] for m in first] == ["system", "user"]                       # rule 1
    assert "task" not in {s["function"]["name"] for s in offered}                 # rule 2
    assert requests[1][0][3]["role"] == "tool" and "found-it" in requests[1][0][3]["content"]  # rule 3


def test_main_agent_gets_the_report_and_the_same_permissions(monkeypatch):
    monkeypatch.setattr(ui, "approve", lambda reason: False)
    _, blocked = tools.execute(call("m1", "bash", '{"command": "sudo ls"}'))
    assert blocked.startswith("Blocked by policy")
    _, declined = tools.execute(call("m2", "bash", '{"command": "python -c 1"}'))
    assert declined == "The user denied this tool call."
    assert tools.TOOLS["task"] is subagent.task and "task" in {s["function"]["name"] for s in tools.TOOL_SCHEMAS}


def test_runaway_subagent_is_cut_off(monkeypatch):
    monkeypatch.setattr(subagent, "MAX_TURNS", 2)
    monkeypatch.setattr(llm, "call_llm", lambda messages, tools=None: (FakeMessage(content="still looking", tool_calls=[call("x", "bash", '{"command": "echo more"}')]), {}))
    out = subagent.task("q")
    assert out.startswith("(stopped after 2 turns") and "still looking" in out
