import json
import os
import sys
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


# ------------------------------------------------------------ a fake stream


def text_chunk(text):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text, tool_calls=None))], usage=None)


def call_chunk(index, cid=None, name=None, arguments=None):
    piece = SimpleNamespace(index=index, id=cid, function=SimpleNamespace(name=name, arguments=arguments))
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None, tool_calls=[piece]))], usage=None)


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
    console, live = ui.console, ui.live
    yield
    ui.console, ui.live = console, live


# ------------------------------------------------------------------- tests


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
    assert usage == {"prompt_tokens": 40, "completion_tokens": 9, "reasoning_tokens": 3, "cached_tokens": 16}


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
    # tools only, no text: content is None and so it is left out, as the SDK did
    monkeypatch.setattr(llm, "client", FakeClient([call_chunk(0, cid="x", name="bash", arguments="{}"), usage_chunk()]))
    message, _ = llm.call_llm([])
    assert message.content is None and "content" not in message.model_dump(exclude_none=True)
    # text only: no tool_calls key, so `if not message.tool_calls` ends the loop
    monkeypatch.setattr(llm, "client", FakeClient([text_chunk("done"), usage_chunk()]))
    message, _ = llm.call_llm([], tools=[])
    assert message.tool_calls is None and message.model_dump(exclude_none=True) == {"role": "assistant", "content": "done"}


def test_a_stream_without_a_usage_chunk_still_returns_the_usage_keys(monkeypatch):
    monkeypatch.setattr(llm, "client", FakeClient([text_chunk("ok")]))
    message, usage = llm.call_llm([], tools=[])
    assert message.content == "ok"
    assert usage == {"prompt_tokens": None, "completion_tokens": None, "reasoning_tokens": None, "cached_tokens": None}


def test_turn_feeds_tool_results_back_and_returns_the_list(quiet, monkeypatch, tmp_path):
    target = tmp_path / "note.txt"
    target.write_text("streamed-note", encoding="utf-8")
    replies = [FakeMessage(content=None, tool_calls=[call("t1", "read_file", json.dumps({"path": str(target)}))]),
               FakeMessage(content="the note says streamed-note", tool_calls=None)]
    requests = []

    def fake(messages, tools=None, on_delta=None):
        requests.append([dict(m) for m in messages])
        return replies.pop(0), {"prompt_tokens": 5, "completion_tokens": 2}

    monkeypatch.setattr(agent, "call_llm", fake)
    messages = [{"role": "system", "content": "s"}]
    out = agent.turn(messages, "read the note")

    assert out is messages
    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool", "assistant"]
    assert out[3] == {"role": "tool", "tool_call_id": "t1", "content": "streamed-note"}
    assert requests[1][3]["content"] == "streamed-note"  # the second request carried the result
    assert requests[1][-1]["content"].startswith("<env>")   # and the late injection came last
    assert out[-1]["content"] == "the note says streamed-note"


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
    replacement = [{"role": "system", "content": "compacted"}]
    monkeypatch.setattr(agent.commands, "compact", lambda messages: replacement)
    assert agent.turn([{"role": "system", "content": "s"}], "hi") is replacement


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
    out = capsys.readouterr().out
    assert out.strip().splitlines()[-1] == "The answer is 42."
    assert "working on it" not in out  # only the final text reaches stdout


def test_headless_ui_keeps_stdout_clean(capsys):
    original = (ui.console, ui.live)
    try:
        ui.headless()
        ui.stream_start()
        ui.stream_delta("noise")
        ui.stream_end()
        ui.note("progress")
        captured = capsys.readouterr()
        assert captured.out == "" and "progress" in captured.err
    finally:
        ui.console, ui.live = original


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
