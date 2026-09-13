"""Step 34 offline tests. A fake OpenAI client stands in for the network:
it raises the SDK's own error classes a scripted number of times, then
yields a scripted stream, so the retry is tested end to end through
llm.call_llm with the sleeps captured. The loop detector and the call
limit run through agent.turn with a fake model; the recovery reads a
session file written the way a crash leaves it.
"""

import json
import os
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
    notes(monkeypatch)
    sleeps(monkeypatch)
    scripted_client(monkeypatch, ([text_chunk("half of a re")], openai.APITimeoutError(request=request())), [text_chunk("whole reply"), usage_chunk()])
    streamed = []

    message, _ = llm.call_llm([{"role": "user", "content": "hi"}], tools=[], on_delta=streamed.append)

    assert message.content == "whole reply"  # nothing of the broken stream survives in the message
    assert streamed == ["half of a re", "whole reply"]


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
    assert llm.MAX_TRIES == 5 and llm.BACKOFF == (0.5, 1.0, 2.0, 4.0)


def test_the_loop_shows_a_failed_call_and_keeps_the_session(monkeypatch):
    seen = notes(monkeypatch)
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (llm.StreamedMessage(failed="model call failed 5 times, giving up"), llm.usage_from(None)))
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
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (replies.pop(0), USAGE))

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
    monkeypatch.setattr(agent, "call_llm", lambda messages, tools=None, on_delta=None: (replies.pop(0), USAGE))

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

    def endless(messages, tools=None, on_delta=None):
        nonlocal count
        count += 1
        return act(f"c{count}", "bash", {"command": f"echo {count}"}), USAGE  # never the same twice

    monkeypatch.setattr(agent, "call_llm", endless)

    out = agent.turn([{"role": "system", "content": "s"}], "go")

    assert count == 6
    assert sum(1 for m in out if m["role"] == "tool") == 6  # the last call's result is in, then the turn ends
    assert seen[-1] == "stopped after 6 model calls in one turn; say continue to go on"
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
