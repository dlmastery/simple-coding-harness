import json
from types import SimpleNamespace

from harness import agent, llm, session, subagent, tools

USAGE = {"prompt_tokens": 1, "completion_tokens": 1, "reasoning_tokens": None, "cached_tokens": None}


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def test_subagent_is_offered_every_tool_but_the_withheld_ones():
    names = {s["function"]["name"] for s in subagent.toolset()}
    assert names == set(tools.TOOLS) - subagent.WITHHELD
    assert "task" not in names and "str_replace" not in names and "bash" in names


def test_subagent_starts_empty_and_returns_only_its_last_message(monkeypatch, tmp_path):
    requests = []
    replies = [
        (SimpleNamespace(content=None, tool_calls=[call("s1", "bash", '{"command": "echo found-it"}')]), USAGE),
        (SimpleNamespace(content="report: found-it at x.py:3", tool_calls=None), USAGE),
    ]

    def fake(messages, tools=None):
        requests.append((list(messages), tools))
        return replies.pop(0)

    monkeypatch.setattr(llm, "complete", fake)
    result = subagent.task("where is found-it?")

    assert result == "report: found-it at x.py:3"
    first, offered = requests[0]
    assert [m["role"] for m in first] == ["system", "user"]            # rule 1: fresh history
    assert first[1]["content"] == "where is found-it?"
    assert "task" not in {s["function"]["name"] for s in offered}      # rule 2: no recursion
    assert requests[1][0][3]["role"] == "tool" and "found-it" in requests[1][0][3]["content"]  # rule 3: same loop


def test_main_agent_only_sees_the_report(monkeypatch, tmp_path):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session, "WRITTEN", 0)
    replies = [
        # main agent asks for a subagent
        (SimpleNamespace(content=None, tool_calls=[call("m1", "task", json.dumps({"description": "find X"}))]), USAGE),
        # subagent: one tool call, then an answer
        (SimpleNamespace(content=None, tool_calls=[call("s1", "bash", '{"command": "echo noisy-output"}')]), USAGE),
        (SimpleNamespace(content="X is in a.py", tool_calls=None), USAGE),
        # main agent finishes
        (SimpleNamespace(content="thanks", tool_calls=None), USAGE),
    ]
    monkeypatch.setattr(llm, "complete", lambda messages, tools=None: replies.pop(0))
    messages = [{"role": "system", "content": "s"}]
    agent.turn(messages, "go")
    tool_results = [m["content"] for m in messages if m["role"] == "tool"]
    assert tool_results == ["X is in a.py"]                             # rule 4: only the report crosses back
    assert not any("noisy-output" in (m.get("content") or "") for m in messages)


def test_runaway_subagent_is_cut_off_with_partial_findings(monkeypatch):
    monkeypatch.setattr(subagent, "MAX_TURNS", 2)
    forever = lambda messages, tools=None: (  # noqa: E731
        SimpleNamespace(content="still looking", tool_calls=[call("x", "bash", '{"command": "echo more"}')]),
        USAGE,
    )
    monkeypatch.setattr(llm, "complete", forever)
    out = subagent.task("q")
    assert out.startswith("(stopped after 2 turns") and "still looking" in out
