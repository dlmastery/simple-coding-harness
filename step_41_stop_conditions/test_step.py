"""Step 41 offline tests. A scripted fake plays the model; the loop tests
drive agent.turn with it and watch how the turn ends: by finish, by a
budget, or after a Stop hook sent the agent back. The shipped Stop hook
runs for real as a subprocess. Nothing else is launched.
"""

import json
import os
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

STEP = Path(__file__).resolve().parent

from harness import agent, checkpoint, commands, context, handoff, hooks, instructions, jobs, llm, mcp_client, memory, modes, permissions, plan, sandbox, session, stop, subagent, todos, tools  # noqa: E402
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
    monkeypatch.setattr(session, "ENABLED", True)
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(mcp_client, "CONFIG_PATHS", [tmp_path / "mcp.json"])
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


# ------------------------------------------------- round 2: every call gets a result


def test_bad_tool_calls_each_get_a_result_and_the_loop_goes_on(fresh, monkeypatch):
    """Malformed arguments, an unknown tool and a raising tool: one tool message each, then the model answers."""
    broken = SimpleNamespace(id="b1", function=SimpleNamespace(name="bash", arguments="{broken"))
    Scripted([
        use(broken, call("b2", "no_such_tool", {"x": 1}), call("b3", "read_file", {"path": "missing.txt"}), call("b4", "bash", {})),
        say("all four came back as errors"),
    ]).install(monkeypatch)
    messages = agent.turn(start(), "go")
    results = {m["tool_call_id"]: m["content"] for m in messages if m["role"] == "tool"}
    assert results["b1"].startswith("Error: the arguments of bash are not a JSON object:")
    assert results["b2"] == "Error: no tool named 'no_such_tool'."
    assert results["b3"].startswith("Error: FileNotFoundError:")
    assert results["b4"] == "Blocked by policy: bash: missing argument 'command'"
    assert messages[-1] == {"role": "assistant", "content": "all four came back as errors"}
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool", "tool", "tool", "tool", "assistant"]


def test_utf8_round_trip_through_the_file_tools_and_bash(fresh, monkeypatch):
    monkeypatch.setattr(ui, "approve", lambda reason: "y")  # python -c is rated ask
    text = "héllo ✓ — ünïcode\r\nline two\n"
    assert tools.write_file("u.txt", text) == "Wrote u.txt"
    assert tools.read_file("u.txt") == text  # newline="" keeps the CRLF as it was
    assert (fresh / "u.txt").read_bytes() == text.encode("utf-8")
    out = tools.bash(f'{sys.executable} -c "print(\'h\\u00e9llo \\u2713\')"')
    assert out.strip() == "héllo ✓"
    assert tools.write_file("deep/er/new.txt", "x") == "Wrote deep/er/new.txt" and (fresh / "deep" / "er" / "new.txt").exists()
    assert tools.str_replace("u.txt", "", "y").startswith("Error: old_str is empty")


def test_write_todos_rejects_a_bad_list_and_keeps_the_old_one(fresh):
    todos.TODOS[:] = [{"content": "old", "activeForm": "keeping", "status": "in_progress"}]
    assert todos.write_todos([{"content": "x", "activeForm": "y", "status": "sideways"}]).startswith("Error: item 0 has status 'sideways'")
    assert todos.write_todos("nope") == "Error: todos must be a list of items."
    assert todos.TODOS == [{"content": "old", "activeForm": "keeping", "status": "in_progress"}]


def test_rewind_offers_user_messages_only_so_no_tool_call_is_orphaned(fresh, monkeypatch):
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "t1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "t1", "content": "r"},
        {"role": "assistant", "content": "done one"},
        {"role": "user", "content": "two"},
        {"role": "assistant", "content": "done two"},
    ]
    session.save(messages)
    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.extend(rows) or 1)
    monkeypatch.setattr(ui, "clear", lambda: None)
    monkeypatch.setattr(ui, "replay", lambda m: None)
    monkeypatch.setattr(ui, "resumed", lambda m, label="": None)
    monkeypatch.setattr(ui, "banner", lambda *a, **k: None)
    kept = commands.handle("/rewind", messages)
    assert offered == ["turn 1    one", "turn 2    two"]  # only user rows
    assert [m["role"] for m in kept] == ["system", "user", "assistant", "tool", "assistant"]


def test_recover_turns_a_failure_into_error_results(fresh, monkeypatch):
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "p1", "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": "ls"})}}]},
    ]
    monkeypatch.setattr(agent, "run_results", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert agent.recover(messages) == 1
    assert messages[-1] == {"role": "tool", "tool_call_id": "p1", "content": "Error: RuntimeError: boom"}
    assert agent.recover(messages) == 0  # nothing left unanswered


def test_headless_without_a_terminal_denies_every_ask_and_exits_one_without_an_answer(fresh, monkeypatch, capsys):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(ui, "ask", lambda: pytest.fail("print mode must not open the input loop"))
    Scripted([use(call("t1", "bash", {"command": "python x.py"})), say("")]).install(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["harness", "--mode", "default", "-p", "run it"])
    with pytest.raises(SystemExit) as stop_:
        agent.main()
    assert stop_.value.code == 1  # no answer text: a script can see the run gave nothing
    assert not session.path_for(session.CURRENT).exists()  # a one-off question leaves no session file, --mode or not
    assert "denied (no terminal to ask on)" in capsys.readouterr().err


def test_exit_words_and_eof_end_the_chat(fresh, monkeypatch):
    answers = iter(["", "/exit"])
    monkeypatch.setattr(ui, "ask", lambda: next(answers))
    monkeypatch.setattr(ui, "banner", lambda *a, **k: None)
    monkeypatch.setattr(ui, "summary", lambda: None)
    monkeypatch.setattr(agent, "turn", lambda *a, **k: pytest.fail("an empty line must not start a turn"))
    agent.chat(agent.parser().parse_args([]))
    monkeypatch.setattr(ui, "ask", lambda: None)  # ctrl-d
    agent.chat(agent.parser().parse_args([]))


# ------------------------------------------------- round 2: the budgets' blind spots


def test_a_tripped_cost_cap_leaves_the_transcript_alone(fresh, monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(stop, "MAX_SESSION_COST", 0.1)
    stop.SPENT = 0.5
    Scripted([say("never called")]).install(monkeypatch)
    messages = agent.turn(start(), "hello?")
    assert roles(messages) == ["system"] and seen[-1].startswith("stopped: this session has cost $0.5000")
    assert not session.path_for("test-session").exists()  # nothing was saved either


def test_a_subagent_stops_on_the_session_budgets_too(fresh, monkeypatch):
    monkeypatch.setattr(stop, "MAX_SESSION_COST", 1.0)
    fake = Scripted([use(call("s1", "bash", {"command": "echo hi"}))], usage=USAGE | {"cost": 0.6}).install(monkeypatch)
    report = subagent.task("look around")
    assert len(fake.requests) == 2  # 0.6, 1.2: the third call is not made
    assert report.startswith("(the subagent stopped: stopped: this session has cost $1.2000, over MAX_SESSION_COST=$1.00")
    ticks = iter(range(0, 10_000, 100))
    monkeypatch.setattr(stop, "clock", lambda: next(ticks))
    monkeypatch.setattr(stop, "MAX_TURN_SECONDS", 150.0)
    stop.reset()
    stop.begin_turn()
    fake = Scripted([use(call("s1", "bash", {"command": "echo hi"}))]).install(monkeypatch)
    assert subagent.task("look around").startswith("(the subagent stopped: stopped after 200s in one turn")
    assert len(fake.requests) == 1


def test_a_denied_finish_is_not_the_answer(fresh, monkeypatch):
    permissions.SESSION_RULES[("finish", "")] = "deny"
    try:
        Scripted([use(call("f1", "finish", {"summary": "all done"})), say("")]).install(monkeypatch)
        monkeypatch.setattr(stop, "MAX_TURN_CALLS", 2)
        messages = agent.turn(start(), "go")
    finally:
        permissions.SESSION_RULES.clear()
    assert messages[3]["content"] == "Blocked by policy: deny for this session: finish"
    assert agent.last_reply(messages) == ""  # the summary of a finish that never ran is nobody's answer
    messages.append({"role": "assistant", "content": None, "tool_calls": [{"id": "f2", "type": "function", "function": {"name": "finish", "arguments": json.dumps({"summary": "really done"})}}]})
    messages.append({"role": "tool", "tool_call_id": "f2", "content": "really done"})
    assert agent.last_reply(messages) == "really done"


def test_a_bad_number_in_the_environment_is_a_note_not_a_crash(monkeypatch, capsys):
    monkeypatch.setenv("MAX_SESSION_COST", "abc")
    assert stop.env_number("MAX_SESSION_COST", 5.0) == 5.0
    assert "MAX_SESSION_COST='abc' is not a number; using 5.0" in capsys.readouterr().err
    monkeypatch.setenv("MAX_SESSION_COST", "2.5")
    assert stop.env_number("MAX_SESSION_COST", 5.0) == 2.5
    monkeypatch.setenv("MAX_TURN_CALLS", "12")
    assert stop.env_number("MAX_TURN_CALLS", 40) == 12


def test_every_eval_task_is_its_own_budget_and_records_its_cost(fresh, tmp_path, monkeypatch):
    from harness import evaluate

    stop.SPENT = 4.9  # nearly spent before the suite: the tasks must not inherit that
    usage = {}
    (tmp_path / "task").mkdir()
    with evaluate.isolated(tmp_path / "task", tmp_path / "sessions", "eval-1", usage):
        assert stop.SPENT == 0.0
        ui.usage(USAGE | {"cost": None}, None, cost=0.0125)
        ui.usage(USAGE, None, cost=0.0125)
    assert usage["cost"] == pytest.approx(0.025) and usage["prompt_tokens"] == 20
    assert stop.SPENT == 4.9  # restored for the chat that follows
