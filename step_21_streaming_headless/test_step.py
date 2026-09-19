import json
import os
import sys
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, llm, permissions, session, subagent, todos, tools  # noqa: E402
from harness.ui import ui  # noqa: E402


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none=True):
        entry = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            entry["tool_calls"] = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in self.tool_calls]
        return entry


def call(cid, name, arguments):
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=arguments))


# ------------------------------------------------------------ a fake stream


def text_chunk(text, finish_reason=None):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text, tool_calls=None), finish_reason=finish_reason)], usage=None)


def call_chunk(index, cid=None, name=None, arguments=None, finish_reason=None):
    piece = SimpleNamespace(index=index, id=cid, function=SimpleNamespace(name=name, arguments=arguments))
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None, tool_calls=[piece]), finish_reason=finish_reason)], usage=None)


def usage_chunk(prompt=40, completion=9, reasoning=3, cached=16):
    usage = SimpleNamespace(
        prompt_tokens=prompt, completion_tokens=completion,
        completion_tokens_details=SimpleNamespace(reasoning_tokens=reasoning),
        prompt_tokens_details=SimpleNamespace(cached_tokens=cached),
    )
    return SimpleNamespace(choices=[], usage=usage)


class FakeClient:
    """Stands in for llm.client: records the request, yields the scripted chunks."""

    def __init__(self, chunks):
        self.chunks = chunks
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.requests.append(request)
        return iter(self.chunks)


SCRIPT = [
    text_chunk("Let me "), text_chunk("look."),
    call_chunk(0, cid="c1", name="bash", arguments='{"comm'),
    call_chunk(1, cid="c2", name="read_file", arguments='{"path": "a'),
    call_chunk(0, arguments='and": "ls"}'),
    call_chunk(1, arguments='.py"}'),
    usage_chunk(),
]


@pytest.fixture
def quiet(monkeypatch):
    """Keep tests off the disk and off the terminal, and undo ui.headless()."""
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False: None)
    monkeypatch.setattr(ui, "usage", lambda stats: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    console, live = ui.console, ui.live
    yield
    ui.console, ui.live = console, live


def scripted(monkeypatch, replies):
    """Make agent.call_llm hand out the scripted replies and record every request."""
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 5, "completion_tokens": 2}

    monkeypatch.setattr(agent, "call_llm", fake)
    return requests


# ------------------------------------------------------------------- stream


def test_stream_assembles_text_two_tool_calls_and_usage(monkeypatch):
    client = FakeClient(SCRIPT)
    monkeypatch.setattr(llm, "client", client)

    message, usage = llm.call_llm([{"role": "user", "content": "hi"}])

    request = client.requests[0]
    assert request["stream"] is True and request["stream_options"] == {"include_usage": True}
    assert request["tools"] is tools.TOOL_SCHEMAS
    assert message.content == "Let me look."
    assert [(c.id, c.function.name, c.function.arguments) for c in message.tool_calls] == [
        ("c1", "bash", '{"command": "ls"}'),
        ("c2", "read_file", '{"path": "a.py"}'),
    ]
    assert usage == {"prompt_tokens": 40, "completion_tokens": 9, "reasoning_tokens": 3, "cached_tokens": 16, "cost": None}


def test_on_delta_receives_every_piece_in_order(monkeypatch):
    monkeypatch.setattr(llm, "client", FakeClient(SCRIPT))
    seen = []
    llm.call_llm([{"role": "user", "content": "hi"}], tools=[], on_delta=seen.append)
    assert seen == ["Let me ", "look."]


def test_model_dump_has_the_shape_the_loop_appends(monkeypatch):
    monkeypatch.setattr(llm, "client", FakeClient(SCRIPT))
    message, _ = llm.call_llm([])
    assert message.model_dump(exclude_none=True) == {
        "role": "assistant",
        "content": "Let me look.",
        "tool_calls": [
            {"id": "c1", "type": "function", "function": {"name": "bash", "arguments": '{"command": "ls"}'}},
            {"id": "c2", "type": "function", "function": {"name": "read_file", "arguments": '{"path": "a.py"}'}},
        ],
    }
    # tools only, no text: content stays in the entry as None - the three keys never change
    monkeypatch.setattr(llm, "client", FakeClient([call_chunk(0, cid="x", name="bash", arguments="{}"), usage_chunk()]))
    message, _ = llm.call_llm([])
    assert message.content is None and message.model_dump()["content"] is None
    # text only: no tool_calls key, so `if not message.tool_calls` ends the loop
    monkeypatch.setattr(llm, "client", FakeClient([text_chunk("done"), usage_chunk()]))
    message, _ = llm.call_llm([], tools=[])
    assert message.tool_calls is None and message.model_dump(exclude_none=True) == {"role": "assistant", "content": "done"}


def test_a_stream_without_a_usage_chunk_still_returns_the_usage_keys(monkeypatch):
    monkeypatch.setattr(llm, "client", FakeClient([text_chunk("ok")]))
    message, usage = llm.call_llm([], tools=[])
    assert message.content == "ok"
    assert usage == {"prompt_tokens": None, "completion_tokens": None, "reasoning_tokens": None, "cached_tokens": None, "cost": None}


def test_a_reply_cut_off_by_max_tokens_drops_its_half_written_calls(monkeypatch):
    chunks = [text_chunk("Running "), call_chunk(0, cid="c1", name="bash", arguments='{"command": "ls -', finish_reason="length"), usage_chunk()]
    monkeypatch.setattr(llm, "client", FakeClient(chunks))
    message, _ = llm.call_llm([])
    assert message.tool_calls is None  # nothing half-parsed reaches execute()
    assert message.content.startswith("Running ") and llm.CUT_OFF in message.content


def test_tool_call_fragments_without_an_index_are_keyed_by_id(monkeypatch):
    chunks = [
        call_chunk(None, cid="a", name="bash", arguments='{"command":'),
        call_chunk(None, cid="b", name="read_file", arguments='{"path": "x"}'),
        call_chunk(None, cid="a", arguments=' "ls"}'),
        usage_chunk(),
    ]
    monkeypatch.setattr(llm, "client", FakeClient(chunks))
    message, _ = llm.call_llm([])
    assert sorted((c.id, c.function.arguments) for c in message.tool_calls) == [("a", '{"command": "ls"}'), ("b", '{"path": "x"}')]


# ---------------------------------------------------------------- execute


def test_bad_calls_are_results_not_exceptions(monkeypatch, tmp_path):
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    _, malformed = tools.execute(call("t1", "bash", '{"command": "ls'))
    assert malformed.startswith("Error: the arguments of bash are not a JSON object")
    _, unknown = tools.execute(call("t2", "no_such_tool", "{}"))
    assert unknown == "Error: no tool named 'no_such_tool'."
    _, missing = tools.execute(call("t3", "read_file", json.dumps({"path": str(tmp_path / "nope.txt")})))
    assert missing.startswith("Error:")
    _, no_arg = tools.execute(call("t4", "bash", "{}"))
    assert no_arg == "Blocked by policy: bash: missing argument 'command'"
    _, not_object = tools.execute(call("t5", "bash", "[1, 2]"))
    assert not_object.startswith("Error: the arguments of bash are not a JSON object")


def test_a_raising_tool_becomes_an_error_result(monkeypatch):
    def boom():
        raise ValueError("kaput")

    monkeypatch.setitem(tools.TOOLS, "boom", boom)
    assert tools.execute(call("b", "boom", "{}")) == ({}, "Error: ValueError: kaput")


def test_a_subagent_cannot_run_a_tool_it_was_not_offered():
    _, result = tools.execute(call("w", "write_file", '{"path": "x", "content": "y"}'), allowed={"bash", "read_file"})
    assert result == "Blocked by policy: write_file is not available to this agent"


def test_utf8_round_trip_through_write_read_and_bash(tmp_path, monkeypatch):
    target = tmp_path / "sub" / "notes.txt"  # the parent does not exist yet
    text = "héllo → wörld ✓\r\nsecond line\n"
    assert tools.write_file(str(target), text) == f"Wrote {target}"
    assert tools.read_file(str(target)) == text  # line endings and accents intact
    assert tools.str_replace(str(target), "", "x") == "Error: old_str is empty."
    assert tools.str_replace(str(target), "wörld", "welt").startswith("Replaced 1")
    assert "welt" in tools.read_file(str(target))
    out = tools.bash(f'{sys.executable} -c "print(chr(233) + chr(10004))"')
    assert chr(233) + chr(10004) in out


def test_bash_timeout_kills_the_command_and_returns_the_partial_output(monkeypatch):
    real_run = tools.sandbox.run
    monkeypatch.setattr(tools.sandbox, "run", lambda command, timeout=60: real_run(command, timeout=1))
    out = tools.bash(f'{sys.executable} -c "import time,sys; print(\'early\'); sys.stdout.flush(); time.sleep(30)"')
    assert out.startswith("Timed out after 1s and was killed.") and "early" in out


# -------------------------------------------------------------- permissions


def test_hidden_commands_and_redirections_are_rated_ask():
    assert permissions.decide("ls $(cat secret)") == "ask"
    assert permissions.decide("echo `whoami`") == "ask"
    assert permissions.decide("cat a.txt > b.txt") == "ask"
    assert permissions.decide("grep x f | tee out") == "ask"
    assert permissions.decide("find . -name '*.py' -delete") == "ask"
    assert permissions.decide("env") == "ask"
    assert permissions.decide("ls 2>&1") == "allow"  # a redirection of stderr into stdout is not a write
    assert permissions.decide("grep '>' file") == "allow"  # quoted, not a redirection
    assert permissions.decide("ls\nrm -rf x") == "deny"  # a newline separates commands too
    assert permissions.check("write_file", {"path": ".git/config"})[0] == "ask"
    assert permissions.check("write_file", {})[0] == "deny"


# -------------------------------------------------------------------- todos


def test_write_todos_rejects_bad_items_and_keeps_the_old_list():
    todos.TODOS[:] = [{"content": "old", "activeForm": "Old", "status": "pending"}]
    bad = todos.write_todos([{"content": "a", "activeForm": "A", "status": "done"}])
    assert bad.startswith("Error: item 0 has status 'done'")
    assert todos.write_todos("nope") == "Error: todos must be a list."
    two = todos.write_todos([{"content": "a", "activeForm": "A", "status": "in_progress"}, {"content": "b", "activeForm": "B", "status": "in_progress"}])
    assert two.startswith("Error: 2 tasks are in_progress")
    assert todos.TODOS == [{"content": "old", "activeForm": "Old", "status": "pending"}]
    todos.TODOS.clear()


def test_ui_shows_the_error_not_a_checklist_when_write_todos_fails(monkeypatch):
    drawn = []
    monkeypatch.setattr(ui, "todos", lambda items: drawn.append("checklist"))
    monkeypatch.setattr(ui.console, "print", lambda *a, **k: drawn.append("panel"))
    ui.tool("write_todos", {"todos": [{"content": "a", "status": "done"}]}, "Error: item 0 has status 'done'")
    assert drawn == ["panel"]


# --------------------------------------------------------------------- loop


def test_turn_feeds_tool_results_back_and_returns_the_list(quiet, monkeypatch, tmp_path):
    target = tmp_path / "note.txt"
    target.write_text("streamed-note", encoding="utf-8")
    requests = scripted(monkeypatch, [
        FakeMessage(content=None, tool_calls=[call("t1", "read_file", json.dumps({"path": str(target)}))]),
        FakeMessage(content="the note says streamed-note", tool_calls=None),
    ])
    messages = [{"role": "system", "content": "s"}]
    out = agent.turn(messages, "read the note")

    assert out is messages
    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "assistant"]
    assert out[3] == {"role": "tool", "tool_call_id": "t1", "content": "streamed-note"}
    assert requests[1][3]["content"] == "streamed-note"  # the second request carried the result
    assert requests[1][-1]["content"].startswith("<env>")   # and the late injection came last
    assert out[-1]["content"] == "the note says streamed-note"


def test_every_tool_call_gets_a_tool_message_even_when_it_fails(quiet, monkeypatch):
    replies = [
        FakeMessage(content=None, tool_calls=[call("a", "bash", '{"command": "ls'), call("b", "nope", "{}"), call("c", "read_file", '{"path": "missing.txt"}')]),
        FakeMessage(content="all three failed", tool_calls=None),
    ]
    scripted(monkeypatch, replies)
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


def test_ctrl_c_mid_turn_answers_the_pending_calls(quiet, monkeypatch):
    replies = [FakeMessage(content=None, tool_calls=[call("t1", "slow", "{}")])]
    scripted(monkeypatch, replies)

    def slow():
        raise KeyboardInterrupt

    monkeypatch.setitem(tools.TOOLS, "slow", slow)
    out = agent.turn([{"role": "system", "content": "s"}], "go")
    assert out[-1] == {"role": "tool", "tool_call_id": "t1", "content": agent.INTERRUPTED}


def test_the_turn_stops_after_max_calls(quiet, monkeypatch):
    monkeypatch.setattr(agent, "MAX_CALLS", 3)
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (FakeMessage(content=None, tool_calls=[call("x", "bash", '{"command": "echo hi"}')]), {}))
    out = agent.turn([{"role": "system", "content": "s"}], "loop forever")
    assert sum(1 for m in out if m["role"] == "assistant") == 3
    assert out[-1]["role"] == "tool"  # the last call is still answered


def test_turn_streams_live_and_stops_the_spinner_at_the_first_delta(quiet, monkeypatch):
    events = []
    monkeypatch.setattr(ui, "stream_start", lambda: events.append("start"))
    monkeypatch.setattr(ui, "stream_delta", lambda text: events.append(text))
    monkeypatch.setattr(ui, "stream_end", lambda: events.append("end"))
    monkeypatch.setattr(ui, "agent", lambda text: events.append("agent-panel"))

    class Spinner:
        def __enter__(self):
            events.append("spinner on")
            return self

        def __exit__(self, *exc):
            self.stop()

        def stop(self):
            if "spinner off" not in events:
                events.append("spinner off")

    monkeypatch.setattr(ui, "working", lambda label="": Spinner())

    def fake(messages, tools=None, on_delta=None):
        for piece in ("Hel", "lo"):
            on_delta(piece)
        return FakeMessage(content="Hello", tool_calls=None), {}

    monkeypatch.setattr(agent, "call_llm", fake)
    agent.turn([{"role": "system", "content": "s"}], "hi")
    assert events == ["spinner on", "spinner off", "start", "Hel", "lo", "end"]


def test_turn_returns_the_compacted_list_when_needed(quiet, monkeypatch):
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (FakeMessage(content="ok", tool_calls=None), {"prompt_tokens": 10 ** 9}))
    monkeypatch.setattr(agent.compact, "LAST_SIZE", 0)
    replacement = [{"role": "system", "content": "compacted"}]
    monkeypatch.setattr(agent.commands, "compact", lambda messages: replacement)
    assert agent.turn([{"role": "system", "content": "s"}], "hi") is replacement


# ------------------------------------------------------------------ session


def test_session_load_repairs_a_dangling_tool_call(tmp_path, monkeypatch):
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path)
    lines = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "t9", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
    ]
    (tmp_path / "x.jsonl").write_text("\n".join(json.dumps(l) for l in lines) + "\n", encoding="utf-8")
    loaded = session.load("x")
    assert loaded[-1] == {"role": "tool", "tool_call_id": "t9", "content": session.UNANSWERED}


def test_rewind_cuts_before_a_user_message_never_inside_an_exchange(monkeypatch):
    from harness import commands

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
        {"role": "assistant", "content": "done"},
    ]
    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.extend(rows) or 1)
    out = commands.rewind(messages)
    assert len(offered) == 2  # only the two user messages are offered
    assert cuts == [4] and [m["role"] for m in out] == ["system", "user", "assistant", "tool"]


# ----------------------------------------------------------------- headless


def test_print_mode_prints_the_final_text_and_exits_zero(quiet, monkeypatch, capsys):
    replies = [FakeMessage(content="working on it", tool_calls=[call("t1", "bash", '{"command": "echo hi"}')]),
               FakeMessage(content="The answer is 42.", tool_calls=None)]
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}))
    monkeypatch.setattr(ui, "ask", lambda: pytest.fail("print mode must not open the input loop"))
    monkeypatch.setattr(ui, "banner", lambda name="": pytest.fail("print mode shows no banner"))
    monkeypatch.setattr(sys, "argv", ["harness", "-p", "what is the answer?"])

    with pytest.raises(SystemExit) as stop:
        agent.main()

    assert stop.value.code == 0
    assert session.PERSIST is False  # a one-off run leaves no session file
    session.PERSIST = True
    out = capsys.readouterr().out
    assert out.strip() == "The answer is 42."  # only the final text reaches stdout


def test_print_mode_exits_one_when_there_is_no_answer(quiet, monkeypatch, capsys):
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (FakeMessage(content=None, tool_calls=None), {}))
    monkeypatch.setattr(sys, "argv", ["harness", "-p", "hello?"])
    with pytest.raises(SystemExit) as stop:
        agent.main()
    session.PERSIST = True
    assert stop.value.code == 1 and capsys.readouterr().out.strip() == ""


def test_headless_ask_is_denied_without_a_terminal_and_stdout_stays_clean(monkeypatch, capsys):
    original = (ui.console, ui.live)
    try:
        ui.headless()
        monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
        assert ui.approve("run: python x.py") is False
        ui.stream_start()
        ui.stream_delta("noise")
        ui.stream_end()
        ui.note("progress")
        captured = capsys.readouterr()
        assert captured.out == "" and "progress" in captured.err and "denied" in captured.err
    finally:
        ui.console, ui.live = original


def test_empty_line_continues_and_exit_leaves(monkeypatch):
    answers = iter(["", "/exit"])
    monkeypatch.setattr(ui, "ask", lambda: next(answers))
    monkeypatch.setattr(ui, "banner", lambda name="": None)
    monkeypatch.setattr(ui, "summary", lambda: None)
    monkeypatch.setattr(agent, "turn", lambda *a, **k: pytest.fail("an empty line must not start a turn"))
    monkeypatch.setattr(sys, "argv", ["harness"])
    agent.main()  # returns: "" was skipped, /exit ended the loop


# ----------------------------------------------------------------- subagent


def test_subagent_still_works_on_the_streamed_call(quiet, monkeypatch):
    replies = [FakeMessage(content=None, tool_calls=[call("s1", "bash", '{"command": "echo found-it"}')]),
               FakeMessage(content="report: found-it", tool_calls=None)]
    offered = []

    def fake(messages, tools=None, on_delta=None):
        offered.append(tools)
        return replies.pop(0), {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(llm, "call_llm", fake)
    assert subagent.task("where is found-it?") == "report: found-it"
    assert "task" not in {s["function"]["name"] for s in offered[0]}


def test_subagent_is_refused_a_tool_it_was_not_offered(quiet, monkeypatch):
    replies = [FakeMessage(content=None, tool_calls=[call("s1", "write_file", '{"path": "x", "content": "y"}')]),
               FakeMessage(content="could not write", tool_calls=None)]
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append([dict(m) for m in messages])
        return replies.pop(0), {}

    monkeypatch.setattr(llm, "call_llm", fake)
    subagent.task("write something")
    assert requests[1][-1]["content"] == "Blocked by policy: write_file is not available to this agent"
