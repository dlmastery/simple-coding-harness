"""Step 42 offline tests. A small Python command plays the slow tool: it
prints numbered lines with a pause between them, so the tests can see
each line reach ui.tool_line before the result comes back. A scripted
fake plays the model for the subagent and the loop smoke test. No model,
browser or network is launched.
"""

import io
import json
import os
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from rich.console import Console

os.environ.setdefault("API_KEY", "x")

STEP = Path(__file__).resolve().parent

from harness import agent, checkpoint, commands, context, handoff, history, hooks, instructions, jobs, llm, mcp_client, memory, modes, permissions, plan, sandbox, session, stop, streaming, subagent, todos, tools  # noqa: E402
from harness import ui as ui_module  # noqa: E402
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


# --------------------------------------------------------------- helpers


def one_liner(count, delay=0.2):
    """A shell command that prints `count` numbered lines, one every `delay` seconds."""
    body = f"import sys,time; [ (print('line', i, flush=True), time.sleep({delay})) for i in range({count}) ]"
    return f'{sys.executable} -c "{body}"'


def lines_seen(monkeypatch):
    """Record every ui.tool_line call as (stream name, line, time)."""
    seen = []
    original = ui.tool_line

    def tool_line(stream, line):
        seen.append((stream.name, line, time.monotonic()))
        original(stream, line)

    monkeypatch.setattr(ui, "tool_line", tool_line)
    return seen


def test_bash_streams_each_line_before_the_result(monkeypatch):
    seen = lines_seen(monkeypatch)
    result = tools.bash(one_liner(3, 0.25))
    finished = time.monotonic()
    assert [line for _, line, _ in seen] == ["line 0", "line 1", "line 2"]
    assert all(name == "bash" for name, _, _ in seen)
    assert finished - seen[0][2] > 0.4       # the first line arrived long before the command ended
    assert seen[2][2] - seen[0][2] > 0.4     # and the lines came one at a time, not in one batch
    assert result == "line 0\nline 1\nline 2\n"  # the model still gets the whole output, untouched


def test_the_result_is_still_capped(monkeypatch):
    seen = lines_seen(monkeypatch)
    count = history.CAP // 8 + 100  # more than CAP characters of output
    result = tools.bash(one_liner(count, 0))
    assert len(seen) == count                # every line reached the screen
    assert history.CAPPED in result          # the model got the capped version, the whole text is on disk
    assert result.startswith("line 0\n")
    assert len(result) < history.CAP + 400


def test_a_timeout_still_becomes_a_result(monkeypatch):
    monkeypatch.setattr(streaming, "TIMEOUT", 1)
    seen = lines_seen(monkeypatch)
    started = time.monotonic()
    result = tools.bash(one_liner(30, 0.3))
    assert result.startswith("Timed out after 1s and was killed. Output so far:\nline 0\n")
    assert time.monotonic() - started < 8    # the process tree was killed, not waited for
    assert seen and seen[0][1] == "line 0"   # the lines before the kill were shown...
    assert "line 0" in result and "line 29" not in result  # ...and handed to the model, which sees where it stopped
    assert ui._streams == [] and ui._live is None  # and the panel came down


def test_a_stream_panel_keeps_the_last_lines_and_comes_down():
    stream = ui.streaming("bash", {"command": "pytest -q"})
    with stream as show:
        assert ui._streams == [stream]
        for i in range(ui_module.STREAM_LINES + 3):
            show(f"line {i}")
        assert stream.count == ui_module.STREAM_LINES + 3
        assert list(stream.lines) == [f"line {i}" for i in range(3, ui_module.STREAM_LINES + 3)]
        console = Console(file=io.StringIO(), force_terminal=False, width=80)
        console.print(stream.render())
        drawn = console.file.getvalue()
        assert "bash pytest -q" in drawn and "… 3 earlier lines" in drawn and "line 10" in drawn and "line 2" not in drawn
        assert f"running · {ui_module.STREAM_LINES + 3} lines" in drawn
    assert ui._streams == [] and ui._live is None


def test_a_line_never_redraws_the_panel_itself(monkeypatch):
    """The live display pulls the panels on its own clock: a million lines are a million appends, not a million redraws."""
    calls = []

    class FakeLive:
        def __init__(self, get_renderable=None, **options):
            self.get_renderable = get_renderable
            calls.append(("new", options.get("refresh_per_second")))

        def start(self):
            calls.append(("start", None))

        def refresh(self):
            calls.append(("refresh", None))

        def update(self, renderable):
            calls.append(("update", None))

        def stop(self):
            calls.append(("stop", None))

    monkeypatch.setattr(ui_module, "Live", FakeLive)
    with ui.streaming("bash", {"command": "yes"}) as show:
        for i in range(1000):
            show(f"line {i}")
        assert ui._streams[0].count == 1000
        ui._live.get_renderable()  # what the display would draw: the last STREAM_LINES lines
    assert calls == [("new", ui_module.REFRESH_PER_SECOND), ("start", None), ("refresh", None), ("stop", None)]
    assert ui._streams == [] and ui._live is None


def test_a_huge_output_is_complete_under_the_live_panel():
    count = 20000
    result = tools.bash(one_liner(count, 0))
    assert result.startswith("line 0\n") and history.CAPPED in result  # capped for the model, the whole text on disk...
    stream = ui.streaming("bash", {"command": "x"})
    with stream as show:
        full = streaming.run(one_liner(count, 0), on_line=show)
    assert full.count("\n") == count and full.endswith(f"line {count - 1}\n")  # ...and whole at the source
    assert stream.count == count


def test_stderr_is_interleaved_where_it_happened_and_utf8_survives(monkeypatch):
    seen = lines_seen(monkeypatch)
    body = "import sys; print('out 1', flush=True); print('err 1', file=sys.stderr, flush=True); print('out 2 h\\u00e9 \\u2713', flush=True)"
    result = tools.bash(f'{sys.executable} -c "{body}"')
    assert result == "out 1\nerr 1\nout 2 hé ✓\n"  # one pipe: the order the command wrote in, decoded as utf-8
    assert [line for _, line, _ in seen] == ["out 1", "err 1", "out 2 hé ✓"]


def test_a_callback_that_raises_does_not_lose_the_output():
    shown = []

    def bad(line):
        shown.append(line)
        raise RuntimeError("the screen is gone")

    output = streaming.run(one_liner(3, 0), on_line=bad)
    assert output == "line 0\nline 1\nline 2\n" and shown == ["line 0"]  # shown once, then the pump stops calling it


def test_the_spinner_steps_aside_while_a_panel_is_open():
    with ui.streaming("bash", {"command": "sleep 5"}):
        spinner = ui.working("thinking")
        with spinner:
            spinner.stop()  # what agent.turn does at the first delta
        assert isinstance(spinner, ui_module.Spinner)
    with ui.working("thinking") as spinner:  # and works as before once the panel is down
        spinner.stop()


def test_a_job_fills_its_log_through_the_reader_and_shows_live_while_waited_on(monkeypatch):
    seen = lines_seen(monkeypatch)
    started = jobs.bash_background(one_liner(3, 0.2))
    assert started.startswith("Started job-1")
    assert seen == []  # nobody is watching yet: the lines go to the log only
    waited = jobs.job_wait("job-1", timeout=30)
    assert "exited with code 0" in waited
    assert [line for _, line, _ in seen] == ["line 0", "line 1", "line 2"]
    assert all(name == "job-1" for name, _, _ in seen)
    assert jobs.JOBS["job-1"].log.read_text(encoding="utf-8") == "line 0\nline 1\nline 2\n"
    assert jobs.JOBS["job-1"].on_line is None  # the wait is over: nothing forwards any more


def test_a_subagent_run_streams_its_nested_calls(monkeypatch):
    seen = lines_seen(monkeypatch)
    monkeypatch.setattr(ui, "approve", lambda reason: "y")  # python -c is rated ask
    Scripted([use(call("s1", "bash", {"command": one_liner(2, 0)})), say("two lines")]).install(monkeypatch)
    report = subagent.task("count the lines")
    assert report == "two lines"
    names = [name for name, _, _ in seen]
    assert names == ["bash", "bash", "subagent exploring"]  # the bash lines, then the run's own progress line
    assert seen[2][1] == f"bash {subagent.title(one_liner(2, 0))} · 2 lines"
    assert ui._streams == []


def test_loop_smoke_streams_then_records_the_full_result(monkeypatch):
    seen = lines_seen(monkeypatch)
    monkeypatch.setattr(ui, "approve", lambda reason: "y")  # python -c is rated ask
    command = one_liner(3, 0.1)
    Scripted([use(call("t1", "bash", {"command": command})), say("done")]).install(monkeypatch)
    messages = agent.turn(start(), "run it")
    assert [line for _, line, _ in seen] == ["line 0", "line 1", "line 2"]
    tool_message = next(m for m in messages if m["role"] == "tool")
    assert tool_message["content"] == "line 0\nline 1\nline 2\n"
    assert messages[-1] == {"role": "assistant", "content": "done"}
    assert ui._streams == [] and ui._live is None


# ------------------------------------------------- round 2: every call gets a result


def test_bad_tool_calls_each_get_a_result_and_the_loop_goes_on(monkeypatch):
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


def test_utf8_round_trip_through_the_file_tools(fresh):
    text = "héllo ✓ — ünïcode\r\nline two\n"
    assert tools.write_file("u.txt", text) == "Wrote u.txt"
    assert tools.read_file("u.txt") == text  # newline="" keeps the CRLF as it was
    assert (fresh / "u.txt").read_bytes() == text.encode("utf-8")
    assert tools.write_file("deep/er/new.txt", "x") == "Wrote deep/er/new.txt" and (fresh / "deep" / "er" / "new.txt").exists()
    assert tools.str_replace("u.txt", "", "y").startswith("Error: old_str is empty")


def test_write_todos_rejects_a_bad_list_and_keeps_the_old_one():
    todos.TODOS[:] = [{"content": "old", "activeForm": "keeping", "status": "in_progress"}]
    assert todos.write_todos([{"content": "x", "activeForm": "y", "status": "sideways"}]).startswith("Error: item 0 has status 'sideways'")
    assert todos.write_todos("nope") == "Error: todos must be a list of items."
    assert todos.TODOS == [{"content": "old", "activeForm": "keeping", "status": "in_progress"}]


def test_rewind_offers_user_messages_only_so_no_tool_call_is_orphaned(monkeypatch):
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


def test_recover_turns_a_failure_into_error_results(monkeypatch):
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "p1", "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": "ls"})}}]},
    ]
    monkeypatch.setattr(agent, "run_results", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert agent.recover(messages) == 1
    assert messages[-1] == {"role": "tool", "tool_call_id": "p1", "content": "Error: RuntimeError: boom"}
    assert agent.recover(messages) == 0  # nothing left unanswered


def test_headless_without_a_terminal_denies_every_ask_and_exits_one_without_an_answer(monkeypatch, capsys):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(ui, "ask", lambda: pytest.fail("print mode must not open the input loop"))
    Scripted([use(call("t1", "bash", {"command": "python x.py"})), say("")]).install(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["harness", "-p", "run it"])
    with pytest.raises(SystemExit) as stop_:
        agent.main()
    assert stop_.value.code == 1  # no answer text: a script can see the run gave nothing
    assert not session.path_for(session.CURRENT).exists()  # a one-off question leaves no session file
    assert "denied (no terminal to ask on)" in capsys.readouterr().err


def test_exit_words_and_eof_end_the_chat(monkeypatch):
    answers = iter(["", "/exit"])
    monkeypatch.setattr(ui, "ask", lambda: next(answers))
    monkeypatch.setattr(ui, "banner", lambda *a, **k: None)
    monkeypatch.setattr(ui, "summary", lambda: None)
    monkeypatch.setattr(agent, "turn", lambda *a, **k: pytest.fail("an empty line must not start a turn"))
    agent.chat(agent.parser().parse_args([]))
    monkeypatch.setattr(ui, "ask", lambda: None)  # ctrl-d
    agent.chat(agent.parser().parse_args([]))
