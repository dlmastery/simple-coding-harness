import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, commands, llm, permissions, session, subagent, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeCall(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        return {"id": self.id, "type": "function", "function": {"name": self.function.name, "arguments": self.function.arguments}}


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [c.model_dump() for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return FakeCall(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


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
    monkeypatch.setattr(ui, "subagent", lambda description: None)


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
    # offered too, so a subagent may run it (what it runs == what it was offered)
    monkeypatch.setattr(tools, "TOOL_SCHEMAS", tools.TOOL_SCHEMAS + [{"type": "function", "function": {"name": "slow", "parameters": {"type": "object", "properties": {}}}}])
    return log


def scripted(monkeypatch, replies, target=agent):
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(target, "call_llm", fake)
    return requests


# ------------------------------------------------------------ decide / run


def test_decide_parses_and_rates_without_running(monkeypatch):
    monkeypatch.setitem(tools.TOOLS, "boom", lambda: pytest.fail("decide must not run the tool"))
    args, action, reason = tools.decide(call("d1", "bash", '{"command": "ls -la"}'))
    assert (args, action, reason) == ({"command": "ls -la"}, "allow", "run: ls -la")
    _, action, reason = tools.decide(call("d2", "bash", '{"command": "sudo ls"}'))
    assert action == "deny" and reason == "run: sudo ls"
    _, action, _ = tools.decide(call("d3", "bash", '{"command": "python -c 1"}'))
    assert action == "ask"
    assert tools.decide(call("d4", "boom", "{}")) == ({}, "allow", None)


def test_decide_turns_bad_arguments_into_an_error_verdict():
    args, action, reason = tools.decide(call("e1", "bash", '{"command": "ls'))
    assert (args, action) == ({}, "error") and reason.startswith("Error: the arguments of bash are not a JSON object")
    assert tools.settle("error", reason) == reason  # settle hands the message straight back
    _, action, reason = tools.decide(call("e2", "bash", "{}"))
    assert (action, reason) == ("deny", "bash: missing argument 'command'")
    _, action, reason = tools.decide(call("e3", "write_file", '{"path": "x", "content": "y"}'), allowed={"bash"})
    assert (action, reason) == ("deny", "write_file is not available to this agent")


def test_run_never_raises(monkeypatch):
    monkeypatch.setitem(tools.TOOLS, "echo_args", lambda **kwargs: json.dumps(kwargs, sort_keys=True))
    assert tools.run(call("r1", "echo_args", "ignored"), {"b": 2, "a": 1}) == '{"a": 1, "b": 2}'
    assert tools.run(call("r2", "nope", "{}"), {}) == "Error: no tool named 'nope'."
    assert tools.run(call("r3", "read_file", "{}"), {"path": "missing-file.txt"}).startswith("Error:")
    monkeypatch.setitem(tools.TOOLS, "none", lambda: None)
    assert tools.run(call("r4", "none", "{}"), {}) == "(no output)"


def test_execute_is_still_decide_ask_and_run(monkeypatch):
    monkeypatch.setattr(ui, "approve", lambda reason: False)
    _, blocked = tools.execute(call("m1", "bash", '{"command": "sudo ls"}'))
    assert blocked.startswith("Blocked by policy")
    _, declined = tools.execute(call("m2", "bash", '{"command": "python -c 1"}'))
    assert declined == "The user denied this tool call."
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    args, result = tools.execute(call("m3", "bash", '{"command": "echo direct"}'))
    assert args == {"command": "echo direct"} and "direct" in result


# ----------------------------------------------------------------- the pool


def test_three_slow_calls_run_together_and_come_back_in_order(quiet, slow_tool):
    calls = [slow_call("s1", "a"), slow_call("s2", "b"), slow_call("s3", "c")]
    started = time.perf_counter()
    outcomes = tools.execute_all(calls)
    elapsed = time.perf_counter() - started

    assert elapsed < 0.9, f"three 0.3s calls took {elapsed:.2f}s - they did not overlap"
    assert [result for _, result in outcomes] == ["done a", "done b", "done c"]
    assert [args["label"] for args, _ in outcomes] == ["a", "b", "c"]
    assert len({thread for _, thread, _ in slow_tool}) == 3  # one worker per call
    assert threading.get_ident() not in {thread for _, thread, _ in slow_tool}  # none on the main thread


def test_denied_declined_and_broken_calls_do_not_run_but_keep_their_place(quiet, slow_tool, monkeypatch):
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
        call("p5", "bash", '{"command": "ls'),                     # broken JSON: an error result
        slow_call("p6", "last"),
    ]
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: events.append(("ran", command)) or f"ran {command}")

    outcomes = tools.execute_all(calls)
    results = [result for _, result in outcomes]

    assert results[0] == "done first" and results[5] == "done last"
    assert results[1].startswith("Blocked by policy")
    assert results[2] == "ran python yes-please.py"
    assert results[3] == "The user denied this tool call."
    assert results[4].startswith("Error: the arguments of bash are not a JSON object")
    # both prompts came first, in order, before anything ran
    assert events[:2] == [("ask", "run: python yes-please.py"), ("ask", "run: python no.py")]
    assert [e for e in events if e[0] == "ran"] == [("ran", "python yes-please.py")]


def test_an_exception_inside_the_pool_is_a_result_and_the_others_survive(quiet, slow_tool, monkeypatch):
    def boom():
        raise RuntimeError("worker died")

    monkeypatch.setitem(tools.TOOLS, "boom", boom)
    outcomes = tools.execute_all([slow_call("a", "a", 0.05), call("b", "boom", "{}"), slow_call("c", "c", 0.05)])
    assert [r for _, r in outcomes] == ["done a", "Error: RuntimeError: worker died", "done c"]


def test_a_single_call_takes_the_direct_path(quiet, slow_tool, monkeypatch):
    monkeypatch.setattr(tools, "ThreadPoolExecutor", lambda *a, **k: pytest.fail("one call must not open a pool"))
    outcomes = tools.execute_all([slow_call("one", "solo", delay=0.0)])
    assert outcomes == [({"label": "solo", "delay": 0.0}, "done solo")]
    assert slow_tool[0][1] == threading.get_ident()  # ran right here, on the calling thread


def test_a_batch_with_a_serial_tool_runs_in_order_on_the_calling_thread(quiet, slow_tool, monkeypatch):
    monkeypatch.setattr(tools, "ThreadPoolExecutor", lambda *a, **k: pytest.fail("a serial batch must not open a pool"))
    monkeypatch.setitem(tools.TOOLS, "task", lambda description: f"report on {description}")
    calls = [slow_call("a", "a", 0.0), call("t", "task", '{"description": "q"}'), slow_call("b", "b", 0.0)]
    outcomes = tools.execute_all(calls)
    assert [r for _, r in outcomes] == ["done a", "report on q", "done b"]
    assert {thread for _, thread, _ in slow_tool} == {threading.get_ident()}
    assert [label for label, _, _ in slow_tool] == ["a", "b"]


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


def test_spinner_is_idle_off_the_main_thread():
    seen = {}

    def worker():
        seen["spinner"] = ui.working("x")

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    from harness.ui import APPROVE_LOCK, Idle

    assert isinstance(seen["spinner"], Idle)
    assert isinstance(APPROVE_LOCK, type(threading.Lock()))


# --------------------------------------------------------------------- loop


def test_turn_appends_results_in_order_and_prints_panels_after_all_finish(quiet, slow_tool, monkeypatch):
    events = []
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False: events.append(("panel", result)))
    requests = scripted(monkeypatch, [
        FakeMessage(content=None, tool_calls=[slow_call("t1", "x", 0.1), slow_call("t2", "y", 0.0)]),
        FakeMessage(content="x and y are done", tool_calls=None),
    ])
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


def test_every_tool_call_gets_a_tool_message_even_when_it_fails(quiet, monkeypatch):
    scripted(monkeypatch, [
        FakeMessage(content=None, tool_calls=[call("a", "bash", '{"command": "ls'), call("b", "nope", "{}"), call("c", "read_file", '{"path": "missing.txt"}')]),
        FakeMessage(content="all three failed", tool_calls=None),
    ])
    out = agent.turn([{"role": "system", "content": "s"}], "go")
    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "tool", "tool", "assistant"]
    assert [m["tool_call_id"] for m in out if m["role"] == "tool"] == ["a", "b", "c"]
    assert all(m["content"].startswith("Error") for m in out if m["role"] == "tool")


def test_a_failed_model_call_ends_the_turn_with_a_valid_transcript(quiet, monkeypatch):
    def failing(messages, tools=None, on_delta=None):
        raise RuntimeError("model call failed: 502")

    monkeypatch.setattr(agent, "call_llm", failing)
    out = agent.turn([{"role": "system", "content": "s"}], "hi")
    assert [m["role"] for m in out] == ["system", "user"]


def test_ctrl_c_mid_batch_answers_the_pending_calls(quiet, slow_tool, monkeypatch):
    scripted(monkeypatch, [FakeMessage(content=None, tool_calls=[slow_call("t1", "a", 0.0), call("t2", "interrupt", "{}")])])

    def interrupt():
        raise KeyboardInterrupt

    monkeypatch.setitem(tools.TOOLS, "interrupt", interrupt)
    out = agent.turn([{"role": "system", "content": "s"}], "go")
    assert [m["tool_call_id"] for m in out if m["role"] == "tool"] == ["t1", "t2"]
    assert out[-1]["content"] == agent.INTERRUPTED


def test_the_turn_stops_after_max_calls(quiet, monkeypatch):
    monkeypatch.setattr(agent, "MAX_CALLS", 3)
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (FakeMessage(content=None, tool_calls=[call("x", "bash", '{"command": "echo hi"}')]), {}))
    out = agent.turn([{"role": "system", "content": "s"}], "loop forever")
    assert sum(1 for m in out if m["role"] == "assistant") == 3 and out[-1]["role"] == "tool"


def test_loop_smoke_single_call_then_answer(quiet, monkeypatch, tmp_path):
    target = tmp_path / "note.txt"
    target.write_text("parallel-note", encoding="utf-8")
    scripted(monkeypatch, [
        FakeMessage(content=None, tool_calls=[call("t1", "read_file", json.dumps({"path": str(target)}))]),
        FakeMessage(content="the note says parallel-note", tool_calls=None),
    ])
    out = agent.turn([{"role": "system", "content": "s"}], "read the note")
    assert out[3] == {"role": "tool", "tool_call_id": "t1", "content": "parallel-note"}
    assert out[-1]["content"] == "the note says parallel-note"


# ----------------------------------------------------------------- subagent


def test_subagent_uses_the_same_parallel_path(quiet, slow_tool, monkeypatch):
    requests = scripted(monkeypatch, [
        FakeMessage(content=None, tool_calls=[slow_call("s1", "a"), slow_call("s2", "b"), slow_call("s3", "c")]),
        FakeMessage(content="report: a b c", tool_calls=None),
    ], target=llm)
    started = time.perf_counter()
    assert subagent.task("find a, b and c") == "report: a b c"
    assert time.perf_counter() - started < 0.9
    fed_back = [m for m in requests[1] if m["role"] == "tool"]
    assert [(m["tool_call_id"], m["content"]) for m in fed_back] == [("s1", "done a"), ("s2", "done b"), ("s3", "done c")]
    assert "task" not in {s["function"]["name"] for s in subagent.toolset()}


def test_subagent_is_refused_a_tool_it_was_not_offered(quiet, monkeypatch):
    requests = scripted(monkeypatch, [
        FakeMessage(content=None, tool_calls=[call("s1", "write_file", '{"path": "x", "content": "y"}'), call("s2", "task", '{"description": "again"}')]),
        FakeMessage(content="could not", tool_calls=None),
    ], target=llm)
    subagent.task("write something")
    fed_back = [m["content"] for m in requests[1] if m["role"] == "tool"]
    assert fed_back == ["Blocked by policy: write_file is not available to this agent", "Blocked by policy: task is not available to this agent"]


# ------------------------------------------------- shared with step 21


def test_utf8_round_trip_through_write_read_and_bash(tmp_path):
    target = tmp_path / "sub" / "notes.txt"
    text = "héllo → wörld ✓\r\nsecond line\n"
    assert tools.write_file(str(target), text) == f"Wrote {target}"
    assert tools.read_file(str(target)) == text
    assert tools.str_replace(str(target), "", "x") == "Error: old_str is empty."
    out = tools.bash(f'{sys.executable} -X utf8 -c "print(chr(233) + chr(10004))"')  # -X utf8: the child writes UTF-8 on Windows too
    assert chr(233) + chr(10004) in out


def test_hidden_commands_and_redirections_are_rated_ask():
    assert permissions.decide("ls $(cat secret)") == "ask"
    assert permissions.decide("cat a.txt > b.txt") == "ask"
    assert permissions.decide("find . -name '*.py' -delete") == "ask"
    assert permissions.decide("env") == "ask"
    assert permissions.decide("ls 2>&1") == "allow"
    assert permissions.decide("ls\nrm -rf x") == "deny"
    assert permissions.check("write_file", {"path": ".git/config"})[0] == "ask"


def test_write_todos_rejects_bad_items_and_keeps_the_old_list():
    todos.TODOS[:] = [{"content": "old", "activeForm": "Old", "status": "pending"}]
    assert todos.write_todos([{"content": "a", "activeForm": "A", "status": "done"}]).startswith("Error: item 0 has status 'done'")
    assert todos.TODOS == [{"content": "old", "activeForm": "Old", "status": "pending"}]
    todos.TODOS.clear()


def test_ui_shows_the_error_not_a_checklist_when_write_todos_fails(monkeypatch):
    drawn = []
    monkeypatch.setattr(ui, "todos", lambda items: drawn.append("checklist"))
    monkeypatch.setattr(ui.console, "print", lambda *a, **k: drawn.append("panel"))
    ui.tool("write_todos", {"todos": [{"content": "a", "status": "done"}]}, "Error: item 0 has status 'done'")
    assert drawn == ["panel"]


def test_session_load_repairs_a_dangling_tool_call(tmp_path, monkeypatch):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    lines = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "t9", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
    ]
    (tmp_path / "x.jsonl").write_text("\n".join(json.dumps(l) for l in lines) + "\n", encoding="utf-8")
    assert session.load("x")[-1] == {"role": "tool", "tool_call_id": "t9", "content": session.STOPPED}


def test_rewind_cuts_before_a_user_message_never_inside_an_exchange(monkeypatch):
    monkeypatch.setattr(session, "save", lambda messages: None)
    cuts = []
    monkeypatch.setattr(session, "rewind_to", cuts.append)
    monkeypatch.setattr(commands, "redraw", lambda messages, label: messages)
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "a", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "a", "content": "ok"},
        {"role": "user", "content": "two"},
    ]
    monkeypatch.setattr(ui, "pick", lambda title, rows: 1)
    out = commands.rewind(messages)
    assert cuts == [4] and [m["role"] for m in out] == ["system", "user", "assistant", "tool"]


def test_a_reply_cut_off_by_max_tokens_drops_its_half_written_calls(monkeypatch):
    piece = SimpleNamespace(index=0, id="c1", function=SimpleNamespace(name="bash", arguments='{"command": "ls -'))
    chunk = SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None, tool_calls=[piece]), finish_reason="length")], usage=None)
    monkeypatch.setattr(llm, "client", SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **r: iter([chunk])))))
    message, _ = llm.call_llm([])
    assert message.tool_calls is None and llm.CUT_OFF in message.content


def test_headless_ask_is_denied_without_a_terminal_and_stdout_stays_clean(monkeypatch, capsys):
    original = (ui.console, ui.live)
    try:
        ui.headless()
        monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
        assert ui.approve("run: python x.py") is False
        ui.note("progress")
        captured = capsys.readouterr()
        assert captured.out == "" and "denied" in captured.err
    finally:
        ui.console, ui.live = original


def test_print_mode_exits_one_when_there_is_no_answer(quiet, monkeypatch, capsys):
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (FakeMessage(content=None, tool_calls=None), {}))
    monkeypatch.setattr(sys, "argv", ["harness", "-p", "hello?"])
    console, live = ui.console, ui.live
    with pytest.raises(SystemExit) as stop:
        agent.main()
    ui.console, ui.live, session.PERSIST = console, live, True
    assert stop.value.code == 1 and capsys.readouterr().out.strip() == ""
