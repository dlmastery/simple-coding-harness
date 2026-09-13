"""Step 41 offline tests. A scripted fake plays the model; the loop tests
drive agent.turn with it and watch how the turn ends: by finish, by a
budget, or after a Stop hook sent the agent back. The shipped Stop hook
runs for real as a subprocess. Nothing else is launched.
"""

import json
import os
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

STEP = Path(__file__).resolve().parent

from harness import agent, checkpoint, commands, context, handoff, hooks, instructions, jobs, llm, memory, modes, permissions, plan, sandbox, session, stop, subagent, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402

USAGE = {"prompt_tokens": 10, "completion_tokens": 4, "reasoning_tokens": None, "cached_tokens": 3}


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


def say(text):
    return FakeMessage(content=text, tool_calls=None)


def use(*calls):
    return FakeMessage(content=None, tool_calls=list(calls))


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    """A temp workspace as cwd, temp stores, no hooks, no jobs, nothing spent, the default agent."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.chdir(workspace)
    monkeypatch.setattr(permissions, "PROJECT", workspace.resolve())
    monkeypatch.setattr(sandbox, "PROJECT", workspace.resolve())
    monkeypatch.setattr(checkpoint, "ROOT", tmp_path / "checkpoints")
    monkeypatch.setattr(checkpoint, "TURN", 0)
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    monkeypatch.setattr(session, "CURRENT", "test-session")
    monkeypatch.setattr(session, "WRITTEN", 0)
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(modes, "CURRENT", "default")
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(instructions, "HOME", tmp_path / "home" / ".simple-harness")
    monkeypatch.setattr(memory, "MEMORY_DIRS", [tmp_path / "memory" / "project", tmp_path / "memory" / "user"])
    monkeypatch.setattr(llm, "MODEL", "gpt-4.1")
    monkeypatch.setattr(stop, "MAX_TURN_CALLS", 40)
    monkeypatch.setattr(stop, "MAX_SESSION_COST", 5.0)
    monkeypatch.setattr(stop, "MAX_TURN_SECONDS", 900.0)
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "agent", lambda text: None)
    monkeypatch.setattr(ui, "usage", lambda *a, **k: None)
    handoff.reset()
    stop.reset()
    jobs.kill_all()
    yield workspace
    jobs.kill_all()
    stop.reset()
    handoff.reset()


def notes(monkeypatch):
    """Capture what ui.note prints."""
    seen = []
    monkeypatch.setattr(ui, "note", lambda text: seen.append(text))
    return seen


class Scripted:
    """A thread-safe fake call_llm: one reply per call, the last one repeated, and a log of every request."""

    def __init__(self, replies, usage=None):
        self.replies = list(replies)
        self.usage = dict(USAGE if usage is None else usage)
        self.requests = []  # (tools offered, user messages) per call
        self.lock = threading.Lock()

    def __call__(self, messages, tools=None, on_delta=None):
        with self.lock:
            self.requests.append(([s["function"]["name"] for s in tools or []], [m["content"] for m in messages if m["role"] == "user"]))
            reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        return reply, dict(self.usage)

    def install(self, monkeypatch):
        monkeypatch.setattr(agent, "call_llm", self)
        monkeypatch.setattr(llm, "call_llm", self)
        return self


def start():
    """The message list chat() starts with."""
    return [{"role": "system", "content": llm.build_system_prompt()}]


def roles(messages):
    return [m["role"] for m in messages]


def stop_hook(tmp_path, command):
    """Register one Stop hook in the temp hooks.json the fixture points at."""
    (tmp_path / "hooks.json").write_text(json.dumps({"Stop": [{"command": command}]}), encoding="utf-8")


REQUIRE_TESTS = f'python "{STEP / ".agents" / "require_tests.py"}"'


# ------------------------------------------------------------------ finish


def test_finish_ends_the_turn_and_its_summary_is_the_answer(fresh, monkeypatch):
    seen = notes(monkeypatch)
    fake = Scripted([
        use(call("b1", "bash", {"command": "echo hi"})),
        use(call("w1", "write_file", {"path": "a.txt", "content": "a"}), call("f1", "finish", {"summary": "wrote a.txt"})),
        say("never sent"),
    ]).install(monkeypatch)
    messages = agent.turn(start(), "make a.txt")

    assert len(fake.requests) == 2  # the reply with finish was the last call
    assert roles(messages) == ["system", "user", "assistant", "tool", "assistant", "tool", "tool"]
    assert (fresh / "a.txt").read_text() == "a"  # the other call of the reply ran
    assert messages[-1] == {"role": "tool", "tool_call_id": "f1", "content": "wrote a.txt"}
    assert agent.last_reply(messages) == "wrote a.txt"  # what -p prints
    assert seen[-1] == "finish: the turn ends here"
    assert stop.SUMMARY is None  # read once, then cleared
    offered, _ = fake.requests[0]
    assert offered[-2:] == ["handoff_to", "finish"]


def test_finish_is_for_the_main_loop_only():
    assert "finish" in tools.TOOLS and "finish" not in [s["function"]["name"] for s in tools.TOOL_SCHEMAS]
    assert "finish" not in [s["function"]["name"] for s in subagent.toolset()]
    assert plan.offered("finish")
    plan.MODE = "plan"
    assert plan.offered("finish") and not plan.offered("write_file")
    assert stop.finish("  done  ") == "done" and stop.finished() == "done" and stop.finished() is None
    assert stop.finish("") == "(finished without a summary)"
    assert stop.finish_summary(json.dumps({"summary": "x"})) == "x" and stop.finish_summary("{broken") == "(finished without a summary)"
    assert agent.last_reply([{"role": "assistant", "content": "text"}]) == "text"
    assert agent.last_reply([{"role": "assistant", "content": None}]) == ""


# -------------------------------------------------------------------- cost


def test_cost_is_reported_or_estimated(monkeypatch):
    assert stop.cost_of({"cost": 0.25, "prompt_tokens": 10}) == (0.25, "reported by the API")
    dollars, source = stop.cost_of(USAGE)  # gpt-4.1: 7 fresh prompt, 4 completion, 3 cached
    assert source == "estimated from list prices" and dollars == pytest.approx((7 * 2.00 + 4 * 8.00 + 3 * 0.50) / 1_000_000)
    monkeypatch.setattr(llm, "MODEL", "nobody/knows")
    assert stop.prices() == stop.FALLBACK_PRICES
    assert stop.cost_of({"prompt_tokens": None, "completion_tokens": None, "cached_tokens": None}) == (0.0, "estimated from list prices")
    assert stop.record({"cost": 0.5}) == 0.5 and stop.record({"cost": 0.25}) == 0.25 and stop.SPENT == 0.75


def test_the_cost_budget_stops_the_loop(fresh, monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(stop, "MAX_SESSION_COST", 1.0)
    fake = Scripted([use(call("b1", "bash", {"command": "echo hi"}))], usage=USAGE | {"cost": 0.4}).install(monkeypatch)
    messages = agent.turn(start(), "loop forever")

    assert len(fake.requests) == 3  # 0.4, 0.8, 1.2: the fourth call is not made
    assert stop.SPENT == pytest.approx(1.2)
    assert seen[-1].startswith("stopped: this session has cost $1.2000, over MAX_SESSION_COST=$1.00")
    assert roles(messages)[-2:] == ["assistant", "tool"]  # every call has its result; the transcript is valid

    messages = agent.turn(messages, "continue")
    assert len(fake.requests) == 3 and seen[-1].startswith("stopped: this session has cost")  # a session cap stays tripped


def test_the_time_budget_stops_the_loop(fresh, monkeypatch):
    seen = notes(monkeypatch)
    ticks = iter(range(0, 10_000, 100))
    monkeypatch.setattr(stop, "clock", lambda: next(ticks))  # every look at the clock is 100s later
    monkeypatch.setattr(stop, "MAX_TURN_SECONDS", 150.0)
    fake = Scripted([use(call("b1", "bash", {"command": "echo hi"}))]).install(monkeypatch)
    agent.turn(start(), "loop forever")
    assert len(fake.requests) == 1  # checked at 100s: fine; checked at 200s: over
    assert seen[-1] == "stopped after 200s in one turn (MAX_TURN_SECONDS=150); say continue to go on"
    assert stop.elapsed() > 0


def test_the_call_budget_stops_the_loop(fresh, monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(stop, "MAX_TURN_CALLS", 2)
    fake = Scripted([use(call("b1", "bash", {"command": "echo hi"}))]).install(monkeypatch)
    agent.turn(start(), "loop forever")
    assert len(fake.requests) == 2
    assert seen[-1] == "stopped after 2 model calls in one turn (MAX_TURN_CALLS=2); say continue to go on"
    assert stop.tripped(0) is None


# ---------------------------------------------------------------- Stop hook


def test_the_stop_hook_sends_the_agent_back_once_then_allows(fresh, tmp_path, monkeypatch):
    seen = notes(monkeypatch)
    stop_hook(tmp_path, REQUIRE_TESTS)
    fake = Scripted([
        use(call("w1", "write_file", {"path": "calc.py", "content": "def add(a, b):\n    return a + b\n"})),
        say("Added add() to calc.py."),
        use(call("b1", "bash", {"command": "echo pytest would run here"})),
        say("Added add() to calc.py and ran the tests."),
    ]).install(monkeypatch)
    messages = agent.turn(start(), "add a function")

    assert len(fake.requests) == 4
    assert roles(messages) == ["system", "user", "assistant", "tool", "assistant", "user", "assistant", "tool", "assistant"]
    assert messages[5] == {"role": "user", "content": "Stop blocked: tests were not run after editing calc.py; run pytest, then answer"}
    assert "Stop blocked: tests were not run after editing calc.py; run pytest, then answer" in seen
    _, users = fake.requests[2]
    assert users[-2].startswith("Stop blocked:")  # the third call read the block (users[-1] is the <env> injection)
    assert messages[-1]["content"] == "Added add() to calc.py and ran the tests."
    assert stop.BLOCKS == 1


def test_the_stop_hook_gates_finish_and_gives_up_after_the_limit(fresh, tmp_path, monkeypatch):
    seen = notes(monkeypatch)
    (fresh / "always_block.py").write_text('def stop(event):\n    return {"block": "not yet"}\n', encoding="utf-8")
    (tmp_path / "hooks.json").write_text(json.dumps({"Stop": [{"python": "always_block:stop"}]}), encoding="utf-8")
    fake = Scripted([use(call(f"f{n}", "finish", {"summary": f"done, try {n}"})) for n in range(1, 5)]).install(monkeypatch)
    messages = agent.turn(start(), "finish now")  # four different summaries: the same one three times would be a repeated call (step 34)

    assert len(fake.requests) == stop.MAX_STOP_BLOCKS + 1  # blocked three times, then allowed with a note
    assert [m["content"] for m in messages if m["role"] == "user"] == ["finish now"] + ["Stop blocked: not yet"] * stop.MAX_STOP_BLOCKS
    assert seen[-2:] == ["the Stop hooks blocked 3 times this turn; stopping anyway", "finish: the turn ends here"]
    assert agent.last_reply(messages) == "done, try 4"


def test_the_stop_event_carries_the_turn(fresh, tmp_path, monkeypatch):
    seen_events = fresh / "events.json"
    (fresh / "record_stop.py").write_text(
        "import json, pathlib\n"
        f"def stop(event):\n    pathlib.Path({str(seen_events)!r}).write_text(json.dumps(event))\n",
        encoding="utf-8",
    )
    (tmp_path / "hooks.json").write_text(json.dumps({"Stop": [{"python": "record_stop:stop"}]}), encoding="utf-8")
    Scripted([use(call("b1", "bash", {"command": "echo hi"})), say("hi is echoed")]).install(monkeypatch)
    agent.turn(start(), "echo")

    event = json.loads(seen_events.read_text())
    assert event["event"] == "Stop" and event["answer"] == "hi is echoed" and event["blocks"] == 0 and event["ended_by"] == "answer"
    assert len(event["calls"]) == 1
    assert event["calls"][0]["tool_name"] == "bash" and event["calls"][0]["tool_input"] == {"command": "echo hi"}
    assert "hi" in event["calls"][0]["tool_result"]
    assert event["cwd"] == os.getcwd()

    # turn_calls on its own: an unanswered call has no result, a broken argument string is an empty input
    messages = [{"role": "assistant", "content": None, "tool_calls": [{"id": "x", "type": "function", "function": {"name": "bash", "arguments": "{broken"}}]}]
    assert stop.turn_calls(messages, 0) == [{"tool_name": "bash", "tool_input": {}, "tool_result": None}]


# ---------------------------------------------------------------- commands


def test_cost_command_and_status(monkeypatch):
    seen = notes(monkeypatch)
    stop.record({"cost": 0.125})
    commands.handle("/cost", [])
    assert seen[-1].startswith("session cost $0.1250 of MAX_SESSION_COST=$5.00 (list prices); MAX_TURN_CALLS=40; MAX_TURN_SECONDS=900")
    assert "/cost" in commands.COMMANDS
    monkeypatch.setattr(llm, "MODEL", "nobody/knows")
    assert "fallback prices" in stop.status()
    assert "Stop" in hooks.EVENTS and hooks.load_config([STEP / ".agents" / "hooks.json"])["Stop"] == [{"command": "python .agents/require_tests.py"}]


# ---------------------------------------------------------------- the loop


def test_loop_smoke_edit_blocked_tested_finished(fresh, tmp_path, monkeypatch):
    """Edit a .py file, get sent back by the Stop hook, run the tests, finish; the cost adds up on the way."""
    seen = notes(monkeypatch)
    stop_hook(tmp_path, REQUIRE_TESTS)
    fake = Scripted([
        use(call("w1", "write_file", {"path": "calc.py", "content": "def add(a, b):\n    return a + b\n"})),
        use(call("f1", "finish", {"summary": "calc.py has add()"})),
        use(call("b1", "bash", {"command": "echo pytest -q"}), call("f2", "finish", {"summary": "calc.py has add(); the tests ran"})),
    ]).install(monkeypatch)
    messages = agent.turn(start(), "add a function and finish")

    assert len(fake.requests) == 3
    assert roles(messages) == ["system", "user", "assistant", "tool", "assistant", "tool", "user", "assistant", "tool", "tool"]
    assert messages[6]["content"] == "Stop blocked: tests were not run after editing calc.py; run pytest, then answer"
    assert agent.last_reply(messages) == "calc.py has add(); the tests ran"
    assert seen[-1] == "finish: the turn ends here"
    assert stop.SPENT == pytest.approx(3 * (7 * 2.00 + 4 * 8.00 + 3 * 0.50) / 1_000_000)
    assert stop.tripped(3) is None
