import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, llm, session, subagent, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


def slow_call(cid, label, delay=0.3):
    return call(cid, "slow", json.dumps({"label": label, "delay": delay}))


@pytest.fixture
def quiet(monkeypatch):
    """Keep tests off the disk and off the terminal."""
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False: None)
    monkeypatch.setattr(ui, "usage", lambda stats: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)


@pytest.fixture
def slow_tool(monkeypatch):
    """A fake tool that sleeps, and a log of which thread ran it and when it ended."""
    log = []
    lock = threading.Lock()

    def slow(label, delay=0.3):
        time.sleep(delay)
        with lock:
            log.append((label, threading.get_ident(), time.perf_counter()))
        return f"done {label}"

    monkeypatch.setitem(tools.TOOLS, "slow", slow)
    return log


# ------------------------------------------------------------------- tests


def test_decide_parses_and_rates_without_running(monkeypatch):
    monkeypatch.setitem(tools.TOOLS, "boom", lambda: pytest.fail("decide must not run the tool"))
    args, action, reason = tools.decide(call("d1", "bash", '{"command": "ls -la"}'))
    assert (args, action, reason) == ({"command": "ls -la"}, "allow", "run: ls -la")
    _, action, reason = tools.decide(call("d2", "bash", '{"command": "sudo ls"}'))
    assert action == "deny" and reason == "run: sudo ls"
    _, action, _ = tools.decide(call("d3", "bash", '{"command": "python -c 1"}'))
    assert action == "ask"
    assert tools.decide(call("d4", "boom", "{}")) == ({}, "allow", None)


def test_run_calls_the_tool_with_parsed_args(monkeypatch):
    monkeypatch.setitem(tools.TOOLS, "echo_args", lambda **kwargs: json.dumps(kwargs, sort_keys=True))
    assert tools.run(call("r1", "echo_args", "ignored"), {"b": 2, "a": 1}) == '{"a": 1, "b": 2}'


def test_execute_is_still_decide_ask_and_run(monkeypatch):
    monkeypatch.setattr(ui, "approve", lambda reason: False)
    _, blocked = tools.execute(call("m1", "bash", '{"command": "sudo ls"}'))
    assert blocked.startswith("Blocked by policy")
    _, declined = tools.execute(call("m2", "bash", '{"command": "python -c 1"}'))
    assert declined == "The user denied this tool call."
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    args, result = tools.execute(call("m3", "bash", '{"command": "echo direct"}'))
    assert args == {"command": "echo direct"} and "direct" in result


def test_three_slow_calls_run_together_and_come_back_in_order(quiet, slow_tool):
    calls = [slow_call("s1", "a"), slow_call("s2", "b"), slow_call("s3", "c")]
    started = time.perf_counter()
    outcomes = tools.execute_all(calls)
    elapsed = time.perf_counter() - started

    assert elapsed < 0.7, f"three 0.3s calls took {elapsed:.2f}s - they did not overlap"
    assert [result for _, result in outcomes] == ["done a", "done b", "done c"]
    assert [args["label"] for args, _ in outcomes] == ["a", "b", "c"]
    assert len({thread for _, thread, _ in slow_tool}) == 3  # one worker per call
    assert threading.get_ident() not in {thread for _, thread, _ in slow_tool}  # none on the main thread


def test_denied_and_declined_calls_do_not_run_but_keep_their_place(quiet, slow_tool, monkeypatch):
    events = []

    def approve(reason):
        events.append(("ask", reason))
        return "yes-please" in reason

    monkeypatch.setattr(ui, "approve", approve)
    calls = [
        slow_call("p1", "first"),
        call("p2", "bash", '{"command": "sudo rm -rf /"}'),      # deny: never runs
        call("p3", "bash", '{"command": "python yes-please.py"}'),  # ask: approved
        call("p4", "bash", '{"command": "python no.py"}'),          # ask: declined
        slow_call("p5", "last"),
    ]
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: events.append(("ran", command)) or f"ran {command}")

    outcomes = tools.execute_all(calls)
    results = [result for _, result in outcomes]

    assert results[0] == "done first" and results[4] == "done last"
    assert results[1].startswith("Blocked by policy")
    assert results[2] == "ran python yes-please.py"
    assert results[3] == "The user denied this tool call."
    # both prompts came first, in order, before anything ran
    assert events[:2] == [("ask", "run: python yes-please.py"), ("ask", "run: python no.py")]
    assert [e for e in events if e[0] == "ran"] == [("ran", "python yes-please.py")]
    assert [label for label, _, _ in slow_tool] == ["first", "last"] or [label for label, _, _ in slow_tool] == ["last", "first"]


def test_a_single_call_takes_the_direct_path(quiet, slow_tool, monkeypatch):
    monkeypatch.setattr(tools, "ThreadPoolExecutor", lambda *a, **k: pytest.fail("one call must not open a pool"))
    outcomes = tools.execute_all([slow_call("one", "solo", delay=0.0)])
    assert outcomes == [({"label": "solo", "delay": 0.0}, "done solo")]
    assert slow_tool[0][1] == threading.get_ident()  # ran right here, on the calling thread


def test_pool_is_capped_at_four_workers(quiet, slow_tool, monkeypatch):
    seen = {}

    class Recording(ThreadPoolExecutor):
        def __init__(self, max_workers=None, **kwargs):
            seen["max_workers"] = max_workers
            super().__init__(max_workers=max_workers, **kwargs)

    monkeypatch.setattr(tools, "ThreadPoolExecutor", Recording)
    calls = [slow_call(f"w{i}", f"w{i}", delay=0.05) for i in range(6)]
    outcomes = tools.execute_all(calls)
    assert seen["max_workers"] == 4
    assert [result for _, result in outcomes] == [f"done w{i}" for i in range(6)]
    assert len({thread for _, thread, _ in slow_tool}) <= 4


def test_turn_appends_results_in_order_and_prints_panels_after_all_finish(quiet, slow_tool, monkeypatch):
    events = []
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False: events.append(("panel", result)))
    replies = [FakeMessage(content=None, tool_calls=[slow_call("t1", "x", 0.1), slow_call("t2", "y", 0.0)]),
               FakeMessage(content="x and y are done", tool_calls=None)]
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(agent, "call_llm", fake)
    messages = [{"role": "system", "content": "s"}]
    out = agent.turn(messages, "do x and y")

    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "tool", "assistant"]
    assert out[3] == {"role": "tool", "tool_call_id": "t1", "content": "done x"}
    assert out[4] == {"role": "tool", "tool_call_id": "t2", "content": "done y"}
    assert requests[1][3]["content"] == "done x" and requests[1][4]["content"] == "done y"
    # y finished before x, but the panels print in the reply's order, after both ran
    assert [label for label, _, _ in slow_tool] == ["y", "x"]
    assert events == [("panel", "done x"), ("panel", "done y")]
    assert out[-1]["content"] == "x and y are done"


def test_subagent_uses_the_same_parallel_path(quiet, slow_tool, monkeypatch):
    replies = [FakeMessage(content=None, tool_calls=[slow_call("s1", "a"), slow_call("s2", "b"), slow_call("s3", "c")]),
               FakeMessage(content="report: a b c", tool_calls=None)]
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(llm, "call_llm", fake)
    started = time.perf_counter()
    assert subagent.task("find a, b and c") == "report: a b c"
    assert time.perf_counter() - started < 0.7
    fed_back = [m for m in requests[1] if m["role"] == "tool"]
    assert [(m["tool_call_id"], m["content"]) for m in fed_back] == [("s1", "done a"), ("s2", "done b"), ("s3", "done c")]
    assert "task" not in {s["function"]["name"] for s in subagent.toolset()}


def test_loop_smoke_single_call_then_answer(quiet, monkeypatch, tmp_path):
    target = tmp_path / "note.txt"
    target.write_text("parallel-note", encoding="utf-8")
    replies = [FakeMessage(content=None, tool_calls=[call("t1", "read_file", json.dumps({"path": str(target)}))]),
               FakeMessage(content="the note says parallel-note", tool_calls=None)]
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (replies.pop(0), {"prompt_tokens": 5, "completion_tokens": 2}))
    out = agent.turn([{"role": "system", "content": "s"}], "read the note")
    assert out[3] == {"role": "tool", "tool_call_id": "t1", "content": "parallel-note"}
    assert out[-1]["content"] == "the note says parallel-note"
