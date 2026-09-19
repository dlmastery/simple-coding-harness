"""Step 34 offline tests. A fake OpenAI client stands in for the network:
it raises the SDK's own error classes a scripted number of times, then
yields a scripted stream, so the retry is tested end to end through
llm.call_llm with the sleeps captured. The loop detector and the call
limit run through agent.turn with a fake model; the recovery reads a
session file written the way a crash leaves it.
"""

import json
import os
import sys
from types import SimpleNamespace

import httpx
import openai
import pytest

os.environ.setdefault("API_KEY", "x")

from harness import agent, budget, checkpoint, context, durability, hooks, instructions, jobs, llm, memory, plan, session, todos, tools  # noqa: E402
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


def act(cid, name, arguments):
    return FakeMessage(content=None, tool_calls=[call(cid, name, arguments)])


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    """Act mode, no hooks, no jobs, no real home or session store, no sleeping."""
    monkeypatch.setattr(hooks, "CONFIG_PATHS", [tmp_path / "hooks.json"])
    monkeypatch.setattr(plan, "MODE", "act")
    monkeypatch.setattr(todos, "TODOS", [])
    monkeypatch.setattr(checkpoint, "ROOT", tmp_path / "checkpoints")
    monkeypatch.setattr(checkpoint, "TURN", 0)
    monkeypatch.setattr(session, "SESSION_DIR", tmp_path / "sessions")
    monkeypatch.setattr(session, "CURRENT", "test-session")
    monkeypatch.setattr(session, "WRITTEN", 0)
    monkeypatch.setattr(session, "save", lambda messages: None)
    monkeypatch.setattr(context, "changes_note", lambda: "")
    monkeypatch.setattr(instructions, "HOME", tmp_path / "home" / ".simple-harness")
    monkeypatch.setattr(instructions, "LOADED", [])
    monkeypatch.setattr(memory, "MEMORY_DIRS", [tmp_path / "memory" / "project", tmp_path / "memory" / "user"])
    monkeypatch.setattr(budget, "WARNED", set())
    monkeypatch.setattr(tools, "LOADED", set())
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: None)
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "injection", lambda text: None)
    monkeypatch.setattr(ui, "usage", lambda stats, estimate=None: None)
    monkeypatch.setattr(ui, "agent", lambda text: None)
    jobs.kill_all()
    yield
    jobs.kill_all()


def notes(monkeypatch):
    """Capture what ui.note prints."""
    seen = []
    monkeypatch.setattr(ui, "note", lambda text: seen.append(text))
    return seen


def sleeps(monkeypatch):
    """Capture the waits instead of waiting."""
    seen = []
    monkeypatch.setattr(llm, "sleep", lambda seconds: seen.append(seconds))
    return seen


# ------------------------------------------------------------ fake client


def request():
    return httpx.Request("POST", "http://model.test/v1/chat/completions")


def status_error(status, message="failed"):
    """The SDK's error for one HTTP status, built the way the SDK builds it."""
    response = httpx.Response(status, request=request())
    if status == 429:
        return openai.RateLimitError(message, response=response, body=None)
    return openai.APIStatusError(message, response=response, body=None)


def text_chunk(text):
    return SimpleNamespace(usage=None, choices=[SimpleNamespace(delta=SimpleNamespace(content=text, tool_calls=None))])


def usage_chunk():
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=4, completion_tokens_details=None, prompt_tokens_details=None)
    return SimpleNamespace(usage=usage, choices=[])


def scripted_client(monkeypatch, *scripts):
    """A client whose create() plays one script per call.

    A script is an exception (raised before any chunk arrives), a list of
    chunks (a full stream), or a tuple (chunks, exception): the chunks
    arrive, then the stream breaks.
    """
    queue = list(scripts)
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        script = queue.pop(0)
        if isinstance(script, BaseException):
            raise script

        def stream():
            chunks, error = script if isinstance(script, tuple) else (script, None)
            yield from chunks
            if error is not None:
                raise error

        return stream()

    monkeypatch.setattr(llm, "client", SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    return calls


# ------------------------------------------------------------------ retry


def test_two_failures_then_success_with_backoff_and_a_note_per_retry(monkeypatch):
    seen = notes(monkeypatch)
    waited = sleeps(monkeypatch)
    calls = scripted_client(monkeypatch, status_error(429), openai.APIConnectionError(request=request()), [text_chunk("hel"), text_chunk("lo"), usage_chunk()])

    message, usage = llm.call_llm([{"role": "user", "content": "hi"}], tools=[])

    assert message.content == "hello" and message.failed is None and message.tool_calls is None
    assert usage["prompt_tokens"] == 10
    assert len(calls) == 3 and waited == [0.5, 1.0]
    assert [n.startswith("model call failed") for n in seen] == [True, True]
    assert "RateLimitError 429" in seen[0] and "retry 1 of 4 in 0.5s" in seen[0]
    assert "APIConnectionError" in seen[1] and "retry 2 of 4 in 1s" in seen[1]


def test_a_stream_that_breaks_halfway_is_started_over(monkeypatch):
    """Mid-stream the SDK raises its http library's error, not an APIError: that is what must be retried."""
    notes(monkeypatch)
    sleeps(monkeypatch)
    dropped = llm.httpx_lib.RemoteProtocolError("peer closed connection without sending complete message body")
    scripted_client(monkeypatch, ([text_chunk("half of a re")], dropped), [text_chunk("whole reply"), usage_chunk()])
    streamed = []
    restarts = []

    message, _ = llm.call_llm([{"role": "user", "content": "hi"}], tools=[], on_delta=streamed.append, on_restart=lambda: restarts.append(len(streamed)))

    assert message.content == "whole reply"  # nothing of the broken stream survives in the message
    assert streamed == ["half of a re", "whole reply"]
    assert restarts == [1]  # the caller was told, after the partial text and before the retry
    assert llm.client.max_retries == 0 if hasattr(llm.client, "max_retries") else True


def test_giving_up_after_five_tries_returns_a_failed_message(monkeypatch):
    seen = notes(monkeypatch)
    waited = sleeps(monkeypatch)
    calls = scripted_client(monkeypatch, *[status_error(503, "down") for _ in range(5)])

    message, usage = llm.call_llm([{"role": "user", "content": "hi"}], tools=[])

    assert len(calls) == 5 and waited == [0.5, 1.0, 2.0, 4.0]
    assert len(seen) == 4
    assert message.failed.startswith("model call failed 5 times, giving up (APIStatusError 503)")
    assert message.content is None and message.tool_calls is None
    assert "failed" not in message.model_dump()
    assert usage["prompt_tokens"] is None


def test_a_4xx_is_never_retried(monkeypatch):
    seen = notes(monkeypatch)
    waited = sleeps(monkeypatch)
    response = httpx.Response(400, request=request())
    calls = scripted_client(monkeypatch, openai.BadRequestError("context too long", response=response, body=None))

    message, _ = llm.call_llm([{"role": "user", "content": "hi"}], tools=[])

    assert len(calls) == 1 and waited == [] and seen == []
    assert message.failed.startswith("model call failed and will not be retried (BadRequestError 400)")
    assert "context too long" in message.failed


def test_retryable_says_yes_to_limits_connections_timeouts_and_5xx_only():
    assert llm.retryable(status_error(429))
    assert llm.retryable(openai.APIConnectionError(request=request()))
    assert llm.retryable(openai.APITimeoutError(request=request()))
    assert llm.retryable(status_error(500)) and llm.retryable(status_error(502))
    assert not llm.retryable(status_error(400)) and not llm.retryable(status_error(404)) and not llm.retryable(status_error(401))
    assert not llm.retryable(ValueError("not an API error"))
    assert llm.retryable(llm.httpx_lib.ReadError("connection reset"))  # the read of a stream is not wrapped by the SDK
    overloaded = openai.APIError("overloaded", request=request(), body={"code": 502, "message": "Provider overloaded"})
    rejected = openai.APIError("bad", request=request(), body={"code": 400, "message": "invalid request"})
    assert llm.retryable(overloaded) and not llm.retryable(rejected)  # an error event inside the stream
    assert llm.MAX_TRIES == 5 and llm.BACKOFF == (0.5, 1.0, 2.0, 4.0)


def test_the_loop_shows_a_failed_call_and_keeps_the_session(monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None, on_restart=None: (llm.StreamedMessage(failed="model call failed 5 times, giving up"), llm.usage_from(None)))
    messages = [{"role": "system", "content": "s"}]

    out = agent.turn(messages, "hello")

    assert [m["role"] for m in out] == ["system", "user"]  # the failed reply is not part of the transcript
    assert seen[-1] == "model call failed 5 times, giving up"


# ---------------------------------------------------------- loop detector


def test_the_same_call_three_times_in_a_row_is_replaced_on_the_third(monkeypatch):
    seen = notes(monkeypatch)
    ran = []
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: ran.append(command) or "same output")
    replies = [act(f"c{i}", "bash", {"command": "echo hi"}) for i in range(3)] + [say("done")]
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None, on_restart=None: (replies.pop(0), USAGE))

    out = agent.turn([{"role": "system", "content": "s"}], "go")

    results = [m["content"] for m in out if m["role"] == "tool"]
    assert results == ["same output", "same output", durability.REPEATED]
    assert ran == ["echo hi", "echo hi"]  # the third call never ran
    assert any("repeated call" in n for n in seen)


def test_a_changed_argument_or_a_different_reply_between_resets_the_count(monkeypatch):
    ran = []
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: ran.append(command) or "ok")
    replies = [
        act("c1", "bash", {"command": "echo hi"}),
        act("c2", "bash", {"command": "echo hi"}),
        act("c3", "bash", {"command": "echo other"}),
        act("c4", "bash", {"command": "echo hi"}),
        act("c5", "bash", {"command": "echo hi"}),
        say("done"),
    ]
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None, on_restart=None: (replies.pop(0), USAGE))

    out = agent.turn([{"role": "system", "content": "s"}], "go")

    assert [m["content"] for m in out if m["role"] == "tool"] == ["ok"] * 5
    assert len(ran) == 5


def test_the_detector_compares_canonical_json_and_tracks_each_pair():
    detector = durability.LoopDetector()
    a = call("1", "bash", {"command": "ls", "x": 1})
    a_reordered = SimpleNamespace(id="2", function=SimpleNamespace(name="bash", arguments='{"x": 1, "command": "ls"}'))
    b = call("3", "read_file", {"path": "a.py"})
    assert detector.observe([a, b]) == [False, False]
    assert detector.observe([a_reordered]) == [False]      # same pair, b's streak is over
    assert detector.observe([a, b]) == [True, False]        # a: 3 in a row; b: starts again
    assert detector.observe([b, b]) == [False, False]       # a dropped out; b: 2
    assert detector.observe([b]) == [True]
    assert durability.signature(a) == durability.signature(a_reordered)
    assert durability.parse_args(SimpleNamespace(function=SimpleNamespace(name="x", arguments="{not json"))) == {}


# -------------------------------------------------------------- call limit


def test_the_call_limit_stops_the_turn_and_says_so(monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(agent, "MAX_CALLS", 6)
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: "ok")
    count = 0

    def endless(messages, tools=None, on_delta=None, on_restart=None):
        nonlocal count
        count += 1
        return act(f"c{count}", "bash", {"command": f"echo {count}"}), USAGE  # never the same twice

    monkeypatch.setattr(agent, "call_llm", endless)

    out = agent.turn([{"role": "system", "content": "s"}], "go")

    assert count == 6
    assert sum(1 for m in out if m["role"] == "tool") == 6  # the last call's result is in, then the turn ends
    assert seen[-1] == "stopped after 6 model calls in one turn; say 'continue' to go on"
    assert durability.REPEAT_LIMIT == 3


def test_the_shipped_limit_is_forty():
    assert agent.MAX_CALLS == 40


# ---------------------------------------------------------------- recovery


def write_session(session_id, messages):
    session.SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with session.path_for(session_id).open("w", encoding="utf-8") as f:
        for message in messages:
            f.write(json.dumps(message) + "\n")


def test_a_session_ending_in_an_unanswered_call_is_recovered(monkeypatch):
    seen = notes(monkeypatch)
    ran = []
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: ran.append(command) or "recovered output")
    write_session("crashed", [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "list it"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": "echo a"})}}]},
    ])

    (checkpoint.ROOT / "crashed" / "0003").mkdir(parents=True)  # the turn that was running when the crash came

    messages = session.open_session("crashed")
    assert len(durability.unanswered(messages)) == 1
    count = agent.recover(messages)

    assert count == 1 and ran == ["echo a"]
    assert checkpoint.TURN == 3  # a recovered edit would be captured under the crashed turn
    assert messages[-1] == {"role": "tool", "tool_call_id": "c1", "content": "recovered output"}
    assert durability.unanswered(messages) == []
    assert seen[-1] == "recovered 1 tool call left unanswered by the last run"


def test_recovery_runs_only_the_calls_without_a_result_and_through_permissions(monkeypatch):
    ran = []
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: ran.append(command) or "ok")
    monkeypatch.setattr(ui, "approve", lambda reason: False)  # `make clean` would ask; the user says no
    write_session("partial", [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "c1", "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": "echo one"})}},
            {"id": "c2", "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": "echo two"})}},
            {"id": "c3", "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": "make clean"})}},
        ]},
        {"role": "tool", "tool_call_id": "c1", "content": "one"},
    ])

    messages = session.open_session("partial")
    assert [c.id for c in durability.unanswered(messages)] == ["c2", "c3"]
    assert agent.recover(messages) == 2

    assert ran == ["echo two"]
    assert checkpoint.TURN == 1 and checkpoint.turns() == [1]  # no turn on disk: a new one is begun
    assert [m["tool_call_id"] for m in messages if m["role"] == "tool"] == ["c1", "c2", "c3"]
    assert messages[-1]["content"] == tools.DENIED


def test_nothing_to_recover_when_the_transcript_is_complete(monkeypatch):
    seen = notes(monkeypatch)
    complete = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "one"},
        {"role": "assistant", "content": "done"},
    ]
    assert durability.unanswered(complete) == [] and agent.recover(complete) == 0
    assert durability.unanswered([{"role": "system", "content": "s"}, {"role": "user", "content": "go"}]) == []
    assert durability.unanswered([]) == []
    assert seen == []


# ------------------------------------------------------------------ loop


def test_loop_smoke_a_retry_inside_a_turn_then_a_tool_call_then_an_answer(monkeypatch):
    seen = notes(monkeypatch)
    waited = sleeps(monkeypatch)
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: "hi")
    tool_piece = SimpleNamespace(index=0, id="c1", function=SimpleNamespace(name="bash", arguments=json.dumps({"command": "echo hi"})))
    tool_chunk = SimpleNamespace(usage=None, choices=[SimpleNamespace(delta=SimpleNamespace(content=None, tool_calls=[tool_piece]))])
    scripted_client(
        monkeypatch,
        status_error(429),                      # first try of the first call
        [tool_chunk, usage_chunk()],            # the model asks for a tool
        [text_chunk("all done"), usage_chunk()],  # then answers
    )

    out = agent.turn([{"role": "system", "content": "s"}], "hello")

    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "assistant"]
    assert out[3]["content"] == "hi" and out[4]["content"] == "all done"
    assert waited == [0.5] and sum(1 for n in seen if n.startswith("model call failed")) == 1


# ------------------------------------------------- robustness (shared by every step)

from harness import commands, permissions, prompt, subagent, tools  # noqa: E402 - the tests below need them whatever the step imports above

USAGE = {"prompt_tokens": 10, "completion_tokens": 4, "reasoning_tokens": None, "cached_tokens": 3}


def _fake_model(replies):
    """A call_llm stand-in that answers with the next reply, whatever keywords the loop passes."""
    queue = list(replies)

    def fake(messages, tools=None, on_delta=None, **_):
        return queue.pop(0), USAGE

    return fake


def test_bad_arguments_an_unknown_tool_and_a_raising_tool_each_get_one_tool_message(monkeypatch, tmp_path):
    """The loop never dies on a tool call: every call gets exactly one result, then the model goes on."""
    monkeypatch.setattr(permissions, "PROJECT", tmp_path.resolve())
    broken = SimpleNamespace(id="c1", function=SimpleNamespace(name="bash", arguments='{"command": "echo hi"'))  # cut short
    unknown = call("c2", "no_such_tool", {"x": 1})
    raising = call("c3", "read_file", {"path": str(tmp_path / "missing.txt")})
    wrong = call("c4", "write_file", {"path": str(tmp_path / "a.txt")})  # content missing
    reply = FakeMessage(content=None, tool_calls=[broken, unknown, raising, wrong])
    monkeypatch.setattr(agent, "call_llm", _fake_model([reply, say("recovered")]))

    out = agent.turn([{"role": "system", "content": "s"}], "go")

    results = {m["tool_call_id"]: m["content"] for m in out if m["role"] == "tool"}
    assert list(results) == ["c1", "c2", "c3", "c4"] and out[-1]["content"] == "recovered"
    assert results["c1"].startswith("Error: the arguments of bash are not a JSON object:")
    assert results["c2"] == "Error: no tool named 'no_such_tool'."
    assert results["c3"].startswith("Error: no file at ")
    assert results["c4"].startswith("Error: TypeError:")
    assert tools.execute(call("c5", "bash", {}))[1] == "Blocked by policy: bash: missing argument 'command'"


def test_utf8_round_trip_through_write_file_read_file_and_bash(monkeypatch, tmp_path):
    monkeypatch.setattr(permissions, "PROJECT", tmp_path.resolve())
    target = tmp_path / "deep" / "unicode.txt"
    text = "naïve café — 日本語 ✓\r\nsecond line\n"
    assert tools.execute(call("w", "write_file", {"path": str(target), "content": text}))[1] == f"Wrote {target}"
    assert target.read_bytes() == text.encode("utf-8")  # parent made, line endings kept
    assert tools.execute(call("r", "read_file", {"path": str(target)}))[1] == text
    assert tools.execute(call("e", "str_replace", {"path": str(target), "old_str": "", "new_str": "x"}))[1].startswith("Error: old_str is empty")
    out = tools.bash(f"{sys.executable} -c \"print('日本語 ✓')\"")
    assert "日本語 ✓" in out


def test_write_todos_with_a_bad_status_returns_an_error_and_leaves_the_list_alone():
    todos.write_todos([{"content": "a", "activeForm": "doing a", "status": "in_progress"}])
    before = list(todos.TODOS)
    assert todos.write_todos([{"content": "b", "activeForm": "doing b", "status": "done"}]).startswith("Error: item 0 has status 'done'")
    assert todos.write_todos([{"content": "b", "status": "pending"}]) == "Error: item 0 needs a non-empty 'activeForm'"
    assert todos.write_todos("not a list") == "Error: todos must be a list"
    assert todos.TODOS == before
    assert todos.write_todos([]) == "Todo list cleared."


def test_rewind_offers_only_user_turns_so_no_tool_call_is_orphaned(monkeypatch):
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "ok"},
        {"role": "assistant", "content": "done one"},
        {"role": "user", "content": "two"},
        {"role": "assistant", "content": "done two"},
    ]
    offered = []
    monkeypatch.setattr(ui, "pick", lambda title, rows: offered.append(rows) or 1)
    monkeypatch.setattr(commands, "redraw", lambda messages, label: messages)
    monkeypatch.setattr(session, "rewind_to", lambda count: None)
    out = commands.handle("/rewind", messages)
    assert len(offered[0]) == 2 and offered[0][0].startswith("turn 1") and "one" in offered[0][0]
    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "assistant"]  # cut before "two"
    for message in out:
        for tool_call in message.get("tool_calls") or []:
            assert any(m.get("tool_call_id") == tool_call["id"] for m in out)


def test_a_subagent_cannot_run_a_tool_it_was_not_offered(monkeypatch):
    seen = []
    monkeypatch.setitem(tools.TOOLS, "write_file", lambda path, content: seen.append(path) or "written")
    replies = [
        FakeMessage(content=None, tool_calls=[call("s1", "write_file", {"path": "x.txt", "content": "1"}), call("s2", "task", {"description": "again"})]),
        say("report"),
    ]
    monkeypatch.setattr(llm, "call_llm", _fake_model(replies))
    monkeypatch.setattr(ui, "subagent", lambda description, tag=None: None)
    monkeypatch.setattr(ui, "usage", lambda stats, estimate=None: None)
    assert subagent.task("look around") == "report" and seen == []


def test_ctrl_c_mid_turn_fills_the_missing_results_and_the_prompt_comes_back(monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(session, "save", lambda messages: None)

    def boom(command):
        raise KeyboardInterrupt

    monkeypatch.setitem(tools.TOOLS, "bash", boom)
    monkeypatch.setattr(ui, "approve", lambda reason: True)
    monkeypatch.setattr(agent, "call_llm", _fake_model([FakeMessage(content=None, tool_calls=[call("c1", "bash", {"command": "sleep 60"})])]))
    messages = [{"role": "system", "content": "s"}]
    with pytest.raises(KeyboardInterrupt):
        agent.turn(messages, "wait")
    out = agent.interrupted(messages)
    assert out[-1] == {"role": "tool", "tool_call_id": "c1", "content": agent.INTERRUPTED} and seen[-1] == "interrupted"


def test_ask_returns_none_to_leave_and_empty_to_continue(monkeypatch):
    def eof(text="> "):
        raise EOFError

    monkeypatch.setattr(prompt, "read", eof)
    assert ui.ask() is None
    monkeypatch.setattr(prompt, "read", lambda text="> ": "   ")
    assert ui.ask() == ""
    assert "/exit" in commands.COMMANDS


def test_bash_rules_ask_about_substitutions_redirections_and_env():
    assert permissions.decide("ls $(pwd)") == "ask" and permissions.decide("cat `which python`") == "ask"
    assert permissions.decide("echo hi > out.txt") == "ask" and permissions.decide("git log | tee log.txt") == "ask"
    assert permissions.decide("find . -name x -delete") == "ask" and permissions.decide("find . -name x") == "allow"
    assert permissions.decide("cat x 2>&1") == "allow" and permissions.split_command("cat x 2>&1") == ["cat x 2>&1"]
    assert permissions.decide("env") == "ask" and permissions.split_command("ls\nrm -rf /") == ["ls", "rm -rf /"]
    assert permissions.decide("ls\nrm -rf /") == "deny"
    assert permissions.check("write_file", {"path": ".git/config"})[0] == "ask"


def test_compaction_keeps_the_transcript_when_the_summariser_fails(monkeypatch):
    from harness import compact, config

    seen = notes(monkeypatch)
    sleeps(monkeypatch)
    scripted_client(monkeypatch, *[openai.APIConnectionError(request=request()) for _ in range(5)])
    monkeypatch.setattr(config, "CONTEXT_WINDOW", 400)
    monkeypatch.setattr(compact, "remember_handoff", lambda summary: None)
    messages = [{"role": "system", "content": "s"}] + [{"role": "user", "content": "u" * 400}, {"role": "assistant", "content": "a" * 400}] * 4
    out = commands.handle("/compact", messages)
    assert out is messages and len(out) == 9 and "<summary>" not in out[0]["content"]
    assert seen[-1] == "compaction failed (RuntimeError); transcript kept as is"


def test_recovery_survives_a_tool_that_raises_and_places_the_turn_at_the_user_message(monkeypatch):
    def boom(command):
        raise RuntimeError("disk on fire")

    monkeypatch.setitem(tools.TOOLS, "bash", boom)
    write_session("crashed2", [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": "echo a"})}}]},
    ])
    messages = session.open_session("crashed2")
    assert agent.recover(messages) == 1
    assert messages[-1] == {"role": "tool", "tool_call_id": "c1", "content": "Error: RuntimeError: disk on fire"}
    assert checkpoint.start_of(checkpoint.TURN) == 1  # /undo cuts back to before "go", never inside the turn


def test_sessions_command_recovers_a_crashed_chat(monkeypatch):
    ran = []
    monkeypatch.setitem(tools.TOOLS, "bash", lambda command: ran.append(command) or "ok")
    write_session("crashed3", [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": "echo a"})}}]},
    ])
    monkeypatch.setattr(ui, "pick", lambda title, rows: 0)
    monkeypatch.setattr(commands, "redraw", lambda messages, label: messages)
    out = commands.handle("/sessions", [{"role": "system", "content": "s"}])
    assert ran == ["echo a"] and out[-1]["tool_call_id"] == "c1" and durability.unanswered(out) == []


def test_observe_tools_are_never_flagged_as_repeats():
    detector = durability.LoopDetector()
    poll = call("1", "job_status", {"job_id": "job-1"})
    assert [detector.observe([poll]) for _ in range(4)] == [[False]] * 4


def test_the_judge_failing_is_a_run_failure_not_a_verdict(monkeypatch, tmp_path):
    from harness import evaluate

    (tmp_path / "judge.md").write_text("pass if it says done")
    task = SimpleNamespace(path=tmp_path, prompt="do it")
    monkeypatch.setattr(llm, "call_llm", lambda messages, tools=None, on_delta=None, on_restart=None: (llm.StreamedMessage(failed="model call failed 5 times"), llm.usage_from(None)))
    with pytest.raises(RuntimeError, match="judge call failed"):
        evaluate.run_judge(task, tmp_path, "done")
