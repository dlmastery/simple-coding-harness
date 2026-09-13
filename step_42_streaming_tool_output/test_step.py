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

from harness import agent, checkpoint, context, handoff, history, hooks, instructions, jobs, llm, memory, modes, permissions, plan, sandbox, session, stop, streaming, subagent, todos, tools  # noqa: E402
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
    """Record every ui.tool_line call as (name, line, time)."""
    seen = []
    original = ui.tool_line

    def tool_line(name, line, stream=None):
        seen.append((name, line, time.monotonic()))
        original(name, line, stream)

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
    assert history.TRIMMED in result         # the model got the capped version
    assert result.startswith("line 0\n")
    assert len(result) < history.CAP + 400


def test_a_timeout_still_becomes_a_result(monkeypatch):
    monkeypatch.setattr(streaming, "TIMEOUT", 1)
    seen = lines_seen(monkeypatch)
    started = time.monotonic()
    result = tools.bash(one_liner(30, 0.3))
    assert result.startswith("Timed out after 1s and was killed.")
    assert time.monotonic() - started < 8    # the process tree was killed, not waited for
    assert seen and seen[0][1] == "line 0"   # the lines before the kill were shown
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


def test_tool_line_without_a_stream_opens_one_by_name():
    ui.tool_line("bash", "hello")
    assert len(ui._streams) == 1 and ui._streams[0].name == "bash" and list(ui._streams[0].lines) == ["hello"]
    ui.tool_line("bash", "again")
    assert len(ui._streams) == 1 and ui._streams[0].count == 2  # the same panel, not a second one
    ui.stream_close(ui._streams[0])
    assert ui._streams == []


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
