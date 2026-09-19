"""Step 44 - replay: the session log, drawn again at the speed it was written.

entries() reads every line of a session file. timeline() turns the lines
into Event objects in file order: a user message, an assistant message,
a tool result, an image, the usage of a model call, a rewind, a handoff,
a compaction. Nothing is folded: a rewind stays a rewind, so a replay
shows what happened, not what the model was left with, and the trace of
trace.py reads the same list.

replay() draws the events with ui, one at a time. Every entry saved by
this step carries `ts`, the time it was written, and the delay before an
event is the gap between its stamp and the previous one, divided by
`speed` and capped at MAX_PAUSE. A log from before this step has no
stamps and replays without delays. With `step` set, replay() waits for
enter before every user message after the first.
"""

import json
import time
from dataclasses import dataclass, field

from . import prompt
from . import session
from .history import caption_of
from .ui import ui

MAX_PAUSE = 5.0  # seconds: a longer gap in the log is shortened to this at speed 1


@dataclass
class Event:
    """One entry of the log, ready to draw."""
    kind: str                   # user, assistant, tool, image, usage, rewind, handoff, compacted
    ts: float | None = None     # when the entry was written; None in a log from before this step
    data: dict = field(default_factory=dict)


def entries(session_id):
    """Every entry of the log, in order. A half-written last line is skipped, as in load()."""
    parsed = []
    for line in session.path_for(session_id).read_text(encoding="utf-8").splitlines():
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return parsed


def timeline(entries):
    """The entries as events, in file order.

    Marker entries become events of their own kind. A message entry
    becomes a user, image, assistant or tool event. A handoff event
    carries the agent that answered before it, so the drawing can name
    both sides.
    """
    events = []
    agent = "main"
    for entry in entries:
        ts = entry.get("ts")
        if "usage" in entry:
            events.append(Event("usage", ts, {k: v for k, v in entry.items() if k != "ts"}))
        elif "rewind_to" in entry:
            events.append(Event("rewind", ts, {"count": entry["rewind_to"]}))
        elif "handoff" in entry:
            events.append(Event("handoff", ts, {"previous": agent, "name": entry["handoff"]}))
            agent = entry["handoff"]
        elif "compacted" in entry:
            events.append(Event("compacted", ts, {"count": len(entry["compacted"])}))
        elif "role" in entry:
            message = {k: v for k, v in entry.items() if k != "ts"}
            role = message["role"]
            if role == "user" and isinstance(message.get("content"), list):
                events.append(Event("image", ts, {"caption": caption_of(message["content"]), "parts": message["content"]}))
            elif role in ("user", "assistant", "tool"):
                events.append(Event(role, ts, message))
    return events


def delay(previous, event, speed):
    """Seconds to wait before `event`: the recorded gap, scaled and capped. 0 without stamps."""
    if previous is None or event.ts is None or previous.ts is None or speed <= 0:
        return 0.0
    return min(max(event.ts - previous.ts, 0.0) / speed, MAX_PAUSE)


def wait_for_enter():
    """The --step pause. Ctrl-C or Ctrl-D ends the replay."""
    try:
        prompt.read("  enter for the next turn> ")
    except (EOFError, KeyboardInterrupt):
        raise SystemExit(0)


def replay(session_id, speed=1.0, step=False, sleep=time.sleep, wait=wait_for_enter):
    """Draw the log of `session_id` at the recorded pace. Returns the events drawn.

    A tool call is drawn when its result arrives, as it did the first
    time. Calls that never got a result, from a run that crashed, are
    drawn at the end with an empty result.
    """
    events = timeline(entries(session_id))
    pending = {}   # tool call id -> (name, args) of calls waiting for their result
    previous = None
    turns = 0
    for event in events:
        prompt_ = event.kind == "user" and not str(event.data.get("content") or "").startswith("Stop blocked:")  # a Stop hook's block is not a turn
        if prompt_:
            turns += 1
            if step and turns > 1:
                wait()
        pause = delay(previous, event, speed)
        if pause and not (step and prompt_):
            sleep(pause)
        draw(event, pending)
        previous = event
    for name, args in pending.values():
        ui.tool(name, args, "")
    return events


def draw(event, pending):
    """Draw one event with the same ui calls the live run made."""
    data = event.data
    if event.kind == "user":
        ui.user(str(data.get("content") or ""))
    elif event.kind == "image":
        ui.user(data["caption"])
    elif event.kind == "assistant":
        if data.get("content"):
            ui.agent(data["content"])
        for call in data.get("tool_calls") or []:
            pending[call["id"]] = (call["function"]["name"], parse_args(call["function"]["arguments"]))
    elif event.kind == "tool":
        name, args = pending.pop(data.get("tool_call_id"), ("tool", {}))
        ui.tool(name, args, str(data.get("content") or ""))
    elif event.kind == "usage":
        ui.usage(data.get("usage") or {}, cost=data.get("cost"))
    elif event.kind == "rewind":
        ui.note(f"rewind to {data['count']} messages")
    elif event.kind == "handoff":
        ui.handoff(data["previous"], data["name"])
    elif event.kind == "compacted":
        ui.note(f"compacted to {data['count']} messages")


def parse_args(arguments):
    """The JSON arguments of a tool call as a dict; a broken string becomes {"raw": ...}."""
    try:
        args = json.loads(arguments or "{}")
    except (json.JSONDecodeError, TypeError):
        return {"raw": str(arguments)}
    return args if isinstance(args, dict) else {"raw": args}


def resolve(session_id):
    """`last` is the newest session; anything else is a file stem. Raises SystemExit when there is no such log."""
    if session_id == "last":
        saved = session.all_sessions()
        if not saved:
            raise SystemExit("no sessions saved yet")
        return saved[0]["id"]
    if not session.path_for(session_id).exists():
        raise SystemExit(f"no session {session_id} in {session.SESSION_DIR}")
    return session_id


def main(cli):
    """`harness replay <session id> [--speed N] [--step]`. Returns the exit code."""
    session_id = resolve(cli.session)
    ui.resumed(session.load(session_id, apply_handoffs=False), label=f"replay {session_id}")  # a count of the messages; no agent is made active
    events = replay(session_id, speed=cli.speed, step=cli.step)
    ui.note(f"replayed {len(events)} entries")
    ui.summary()  # the tokens and dollars of the session, added up from its usage entries
    return 0
