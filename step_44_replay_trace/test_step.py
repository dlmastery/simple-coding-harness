"""Step 44 offline tests. The session tests write logs through
session.save with a fake clock and read them back through load(),
replay.timeline and trace.calls; the replay tests catch what the ui
draws and what the sleeps would have waited; the trace tests read the
HTML page. A scripted fake plays the model in the loop smoke test. No
model, browser or network is launched.
"""

import json
import os
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("API_KEY", "x")

STEP = Path(__file__).resolve().parent

from harness import agent, checkpoint, context, handoff, history, hooks, instructions, jobs, llm, memory, modes, permissions, plan, replay, sandbox, session, stop, todos, trace  # noqa: E402
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
    """A temp workspace as cwd, temp stores, no hooks, no jobs, nothing spent, the default agent, a clock that ticks by the second."""
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
    ticks = iter(range(1_000_000, 2_000_000))
    monkeypatch.setattr(session, "clock", lambda: next(ticks))  # every entry is stamped one second after the last
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


# --------------------------------------------------------------- helpers


SYSTEM = {"role": "system", "content": "you are a coding agent"}
ASK = {"role": "user", "content": "list the files"}
REPLY = {"role": "assistant", "content": None, "tool_calls": [{"id": "b1", "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": "ls"})}}]}
RESULT = {"role": "tool", "tool_call_id": "b1", "content": "a.txt\nb.txt"}
ANSWER = {"role": "assistant", "content": "Two files: a.txt and b.txt."}


def write_session(with_usage=True):
    """A two-call session written the way the loop writes one. Returns its messages."""
    messages = [SYSTEM, ASK]
    session.save(messages)
    messages = messages + [REPLY]
    session.save(messages, usage=dict(USAGE), seconds=1.5, cost=0.001) if with_usage else session.save(messages)
    messages = messages + [RESULT]
    session.save(messages)
    messages = messages + [ANSWER]
    session.save(messages, usage=dict(USAGE), seconds=0.5, cost=0.002) if with_usage else session.save(messages)
    return messages


def lines(session_id="test-session"):
    return [json.loads(line) for line in session.path_for(session_id).read_text(encoding="utf-8").splitlines()]


def drawn(monkeypatch):
    """Record every ui call replay makes, in order."""
    seen = []
    monkeypatch.setattr(ui, "user", lambda text: seen.append(("user", text)))
    monkeypatch.setattr(ui, "agent", lambda text: seen.append(("agent", text)))
    monkeypatch.setattr(ui, "tool", lambda name, args, result, nested=False, tag=None: seen.append(("tool", name, args, result)))
    monkeypatch.setattr(ui, "usage", lambda stats, estimate=None, cost=None: seen.append(("usage", stats, cost)))
    monkeypatch.setattr(ui, "note", lambda text: seen.append(("note", text)))
    monkeypatch.setattr(ui, "handoff", lambda previous, name, reason="": seen.append(("handoff", previous, name)))
    return seen


# --------------------------------------------------------------- session


def test_save_stamps_every_entry_and_writes_the_usage_next_to_the_reply():
    messages = write_session()
    entries = lines()
    assert [e.get("role", "usage") for e in entries] == ["system", "user", "assistant", "usage", "tool", "assistant", "usage"]
    assert all(isinstance(e["ts"], (int, float)) for e in entries)
    assert [e["ts"] for e in entries] == sorted(e["ts"] for e in entries)
    assert entries[3] == {"usage": USAGE, "index": 2, "seconds": 1.5, "cost": 0.001, "ts": entries[3]["ts"]}
    assert entries[6]["index"] == 4 and entries[6]["cost"] == 0.002
    assert "ts" not in REPLY and "ts" not in ANSWER  # the dicts in memory are not touched
    assert session.load("test-session") == messages  # no stamps, no usage entries: the list the model read


def test_load_still_applies_rewinds_and_compactions_over_stamped_entries():
    messages = write_session()
    session.rewind_to(2)
    session.save(messages[:2] + [{"role": "user", "content": "never mind"}])
    assert session.load("test-session") == messages[:2] + [{"role": "user", "content": "never mind"}]
    session.compacted([SYSTEM, {"role": "user", "content": "after compaction"}])
    session.save([SYSTEM, {"role": "user", "content": "after compaction"}, ANSWER], usage=USAGE)
    assert session.load("test-session") == [SYSTEM, {"role": "user", "content": "after compaction"}, ANSWER]
    assert [e for e in lines() if "rewind_to" in e][0]["ts"] and [e for e in lines() if "compacted" in e][0]["ts"]
    assert session.open_session("test-session") == session.load("test-session") and session.WRITTEN == 3


def test_a_log_from_before_this_step_loads_and_replays_without_delays(monkeypatch):
    session.SESSION_DIR.mkdir(parents=True)
    session.path_for("old").write_text("".join(json.dumps(m) + "\n" for m in (SYSTEM, ASK, REPLY, RESULT, ANSWER)), encoding="utf-8")
    assert session.load("old") == [SYSTEM, ASK, REPLY, RESULT, ANSWER]
    events = replay.timeline(replay.entries("old"))
    assert [e.kind for e in events] == ["user", "assistant", "tool", "assistant"] and all(e.ts is None for e in events)
    slept = []
    seen = drawn(monkeypatch)
    replay.replay("old", sleep=slept.append)
    assert slept == [] and [s[0] for s in seen] == ["user", "tool", "agent"]  # the first reply has no text, only the call


# ---------------------------------------------------------------- replay


def test_the_timeline_keeps_every_entry_in_file_order():
    write_session()
    session.rewind_to(2)
    session.handoff("reviewer")
    session.compacted([SYSTEM])
    events = replay.timeline(replay.entries("test-session"))
    assert [e.kind for e in events] == ["user", "assistant", "usage", "tool", "assistant", "usage", "rewind", "handoff", "compacted"]
    assert events[2].data == {"usage": USAGE, "index": 2, "seconds": 1.5, "cost": 0.001}
    assert events[6].data == {"count": 2} and events[7].data == {"previous": "main", "name": "reviewer"} and events[8].data == {"count": 1}
    assert "ts" not in events[1].data and events[1].data == REPLY


def test_replay_draws_in_order_and_waits_the_recorded_gaps(monkeypatch):
    write_session()
    session.handoff("reviewer")
    seen = drawn(monkeypatch)
    slept = []
    events = replay.replay("test-session", speed=2.0, sleep=slept.append)
    assert len(events) == 7
    assert seen == [
        ("user", "list the files"),
        ("usage", USAGE, 0.001),
        ("tool", "bash", {"command": "ls"}, "a.txt\nb.txt"),
        ("agent", "Two files: a.txt and b.txt."),
        ("usage", USAGE, 0.002),
        ("handoff", "main", "reviewer"),
    ]
    assert slept == [0.5] * 6  # one second between entries, at speed 2; nothing before the first
    assert replay.delay(replay.Event("user", 0.0), replay.Event("tool", 60.0), 1.0) == replay.MAX_PAUSE


def test_step_waits_for_enter_between_turns(monkeypatch):
    messages = write_session()
    session.save(messages + [{"role": "user", "content": "and now delete them"}, {"role": "assistant", "content": "No."}])
    seen = drawn(monkeypatch)
    waits, slept = [], []
    replay.replay("test-session", step=True, sleep=slept.append, wait=lambda: waits.append(len(seen)))
    assert waits == [5]  # once, before the second user message, after the five draws of the first turn
    assert len(slept) == 6  # the gap before a user message is the wait, not a sleep


def test_the_replay_command_resolves_last_and_the_missing(monkeypatch):
    write_session()
    seen = drawn(monkeypatch)
    monkeypatch.setattr(ui, "resumed", lambda messages, label="resumed": seen.append(("resumed", label)))
    monkeypatch.setattr(ui, "summary", lambda: None)
    with pytest.raises(SystemExit) as done:
        agent.main(["replay", "last", "--speed", "1000"])
    assert done.value.code == 0
    assert seen[0] == ("resumed", "replay test-session") and seen[-1] == ("note", "replayed 6 entries")
    with pytest.raises(SystemExit, match="no session nope"):
        replay.resolve("nope")


# ----------------------------------------------------------------- trace


def test_calls_group_the_reply_its_results_its_usage_and_its_images(tmp_path):
    messages = write_session()
    png = tmp_path / "shot.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
    picture = history.image_message(png, "screenshot from tool computer")
    messages = messages + [{"role": "user", "content": "look"}, {"role": "assistant", "content": "Looking.", "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "computer", "arguments": "{\"action\": \"screenshot\"}"}}]}]
    session.save(messages, usage=USAGE | {"cost": 0.5})  # the API reported the cost; no cost passed
    messages = messages + [{"role": "tool", "tool_call_id": "c1", "content": "done"}, picture]
    session.save(messages)
    result = trace.calls(replay.timeline(replay.entries("test-session")), "test-session")
    assert [c.number for c in result.calls] == [1, 2, 3] and [c.turn for c in result.calls] == [1, 1, 2]
    first, second, third = result.calls
    assert first.tool_calls == [{"id": "b1", "name": "bash", "arguments": json.dumps({"command": "ls"}), "result": "a.txt\nb.txt"}]
    assert (first.seconds, first.cost, first.usage) == (1.5, 0.001, USAGE)
    assert second.content == "Two files: a.txt and b.txt." and second.tool_calls == []
    assert third.cost == 0.5 and third.seconds is None  # priced from the usage the API reported
    assert [(caption, url[:22]) for caption, url in third.images] == [("screenshot from tool computer", "data:image/png;base64,")]
    assert [r[0] for r in result.rows if isinstance(r, tuple)] == ["user", "user"]
    assert trace.totals(result) == {"calls": 3, "seconds": 2.0, "prompt": 30, "completion": 12, "cached": 9, "cost": pytest.approx(0.503), "tools": 2}


def test_the_html_carries_every_tool_call_escaped_and_nothing_external(tmp_path):
    messages = write_session()
    messages = messages + [
        {"role": "user", "content": "<script>alert(1)</script> & more"},
        {"role": "assistant", "content": "<b>bold</b>", "tool_calls": [{"id": "w1", "type": "function", "function": {"name": "write_file", "arguments": json.dumps({"path": "x.html", "content": "<img src=x onerror=alert(1)>"})}}]},
    ]
    session.save(messages, usage=USAGE, seconds=2.0, cost=0.003)
    session.save(messages + [{"role": "tool", "tool_call_id": "w1", "content": "wrote x.html </pre><script>evil()</script>"}])
    out = tmp_path / "trace.html"
    result = trace.write("test-session", out)
    page = out.read_text(encoding="utf-8")
    assert page.startswith("<!doctype html>") and "<style>" in page and "<script>" in page
    assert "http://" not in page and "https://" not in page and "<link" not in page and "src=\"http" not in page
    for name, arguments in [(t["name"], t["arguments"]) for c in result.calls for t in c.tool_calls]:
        assert f'<span class="tool">{name}</span>' in page and trace.escape(arguments) in page
    assert "a.txt\nb.txt" in page and "wrote x.html &lt;/pre&gt;&lt;script&gt;evil()&lt;/script&gt;" in page
    assert "<script>alert(1)</script>" not in page and "&lt;script&gt;alert(1)&lt;/script&gt; &amp; more" in page
    assert "<b>bold</b>" not in page and "&lt;b&gt;bold&lt;/b&gt;" in page
    assert "<img src=x" not in page
    assert page.count('<tr class="call">') == 3 and page.count("<details>") == 2
    assert "$0.0010" in page and "$0.0060" in page and ">1.5<" in page and ">10<" in page  # a cost, the total, the seconds, the prompt tokens


def test_the_trace_command_writes_the_page(monkeypatch, tmp_path):
    write_session()
    notes = []
    monkeypatch.setattr(ui, "note", lambda text: notes.append(text))
    out = tmp_path / "out" / "t.html"
    out.parent.mkdir()
    with pytest.raises(SystemExit) as done:
        agent.main(["trace", "test-session", "--html", str(out)])
    assert done.value.code == 0 and out.exists()
    assert notes[-1] == f"wrote {out} · 2 model calls · 1 tool calls · $0.0030"
    assert "data:image/png;base64,QUJD" not in trace.html(trace.calls([replay.Event("assistant", None, {"content": "x"}), replay.Event("image", None, {"caption": "c", "parts": [{"type": "image_url", "image_url": {"url": "javascript:alert(1)"}}]})]))


# ------------------------------------------------------------- loop smoke


def test_loop_smoke_the_turn_logs_its_calls_and_the_trace_reads_them_back(fresh, monkeypatch, tmp_path):
    Scripted([
        use(call("b1", "bash", {"command": "echo hi"})),
        say("hi was echoed"),
    ]).install(monkeypatch)
    messages = agent.turn([{"role": "system", "content": llm.build_system_prompt()}], "echo hi")
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool", "assistant"]

    entries = lines()
    usage_entries = [e for e in entries if "usage" in e]
    assert [e["index"] for e in usage_entries] == [2, 4]
    assert all(e["usage"] == USAGE and e["seconds"] >= 0 and e["cost"] == pytest.approx(stop.cost_of(USAGE)[0]) for e in usage_entries)
    assert session.load("test-session") == messages  # what --resume sends back to the model

    result = trace.write("test-session", tmp_path / "t.html")
    assert [c.number for c in result.calls] == [1, 2]
    assert result.calls[0].tool_calls[0]["name"] == "bash" and "hi" in result.calls[0].tool_calls[0]["result"]
    assert result.calls[1].content == "hi was echoed"
    page = (tmp_path / "t.html").read_text(encoding="utf-8")
    assert '<span class="tool">bash</span>' in page and "hi was echoed" in page

    seen = drawn(monkeypatch)
    replay.replay("test-session", sleep=lambda s: None)
    assert [s[0] for s in seen] == ["user", "usage", "tool", "agent", "usage"]
