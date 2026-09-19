"""Step 04 - the hybrid: a catalog with one escape hatch, and a loop that closes.

POST /api/run {"prompt": ..., "mode": ...} is step 03, with one change: a
declarative run keeps its transcript in a session, and the done message
carries the session id. POST /api/action {"session": ..., "action": ...,
"payload": {...}} appends the event to that transcript as a user message
and runs the next model turn, streaming the updated layout the same way.
A failed model call ends any stream with {"done": true, "error": "..."}.
GET / serves the page.
"""

import json
import mimetypes
import re
import threading
import uuid
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import catalog
import llm

HERE = Path(__file__).parent
# module scripts need this type; Windows may register .js as text/plain
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")

STATIC_PROMPT = """You build dashboards out of prebuilt components.
You cannot write prose or markup. The only way to answer is to call the show_* tools.
Call several tools in one reply: three or four show_metric calls for the headline
numbers, one show_table for the detail, and one show_chart for the trend.
Invent plausible sample data when the user gives none. Keep titles short."""

HTML_PROMPT = """You build dashboards as one self-contained HTML document.
Write a complete document: <!doctype html>, <html>, <head> with one <style>, <body>,
and one <script> at the end. Everything inline: no external stylesheets, scripts,
fonts or images, because the page that hosts you blocks all network access.
Show three or four headline numbers, one table of detail and one chart drawn as
inline SVG. Invent plausible sample data when the user gives none.
Include at least one <button>. On click it must call
parent.postMessage({type: "event", name: "<what it does>", payload: {...}}, "*")
so the host page hears it. Output only the HTML, no code fence, no prose."""

EVENT_PROMPT = (
    "Event from the dashboard: the user triggered {action!r} with payload {payload}. "
    "Apply it and answer with the whole updated dashboard, as one JSON document in the same shape as before. "
    "Change only what the event changes; keep the other elements as they were."
)

FENCE = re.compile(r"^\s*```(?:json|html)?\s*|\s*```\s*$")

# session id -> {"shape": ..., "turn": ..., "lock": ..., "messages": [...]}: the transcript a later action continues
SESSIONS: dict[str, dict] = {}
MAX_SESSIONS = 100  # in memory, for one person: the oldest goes when the hundred-and-first starts

app = FastAPI(title="genui step 04: hybrid escape hatch")


class Run(BaseModel):
    prompt: str
    mode: Literal["static", "tree", "flat", "html"] = "flat"


class Action(BaseModel):
    session: str
    action: str
    payload: Any = None


def sse(message):
    """One SSE frame: a data line with the JSON, then a blank line."""
    return f"data: {json.dumps(message)}\n\n"


def usage_of(event):
    return {k: v for k, v in event.items() if k != "type"}


def static_components(prompt):
    """Step 01: one model turn with tools, one message per component the model chose."""
    messages = [{"role": "system", "content": STATIC_PROMPT}, {"role": "user", "content": prompt}]
    raw = []  # what the model wrote: one line per call, name and arguments
    for event in llm.stream_chat(messages, tools=catalog.TOOL_SCHEMAS):
        if event["type"] == "tool_call":
            raw.append(f"{event['name']} {event['arguments']}")
            message = catalog.message_from_call(event["name"], event["arguments"])
            if message is not None:
                yield message
        elif event["type"] == "text":
            raw.append(event["text"])
            yield {"note": event["text"]}  # the model spoke instead of calling a tool
        elif event["type"] == "usage":
            yield {"done": True, "mode": "static", "usage": usage_of(event), "raw": "\n".join(raw)}


def parse_spec(text):
    """The model's JSON, with any code fence stripped. None when it does not parse."""
    try:
        return json.loads(FENCE.sub("", text))
    except json.JSONDecodeError:
        return None


def stream_text(messages, response_format=None):
    """Yield {"delta"} per chunk; the last item is ("".join(text), usage)."""
    parts = []
    usage = None
    for event in llm.stream_chat(messages, response_format=response_format):
        if event["type"] == "text":
            parts.append(event["text"])
            yield {"delta": event["text"]}
        elif event["type"] == "usage":
            usage = usage_of(event)
    yield "".join(parts), usage


def declarative_turn(session_id):
    """One model turn on a session's transcript: the JSON as it streams, then the checked spec.

    The model's reply is appended to the transcript, so the next action
    continues from the layout the user is looking at.
    """
    session = SESSIONS[session_id]
    shape = session["shape"]
    with session["lock"]:  # one turn at a time per transcript: a double click must not interleave two
        try:
            for item in stream_text(session["messages"], response_format={"type": "json_object"}):
                if isinstance(item, dict):
                    yield item
                    continue
                text, usage = item
        except Exception:
            if session["messages"][-1]["role"] == "user":
                session["messages"].pop()  # the turn never happened: no dangling user message
            raise
        session["messages"].append({"role": "assistant", "content": text})
        spec = parse_spec(text)
        errors = ["the reply is not JSON"] if spec is None else catalog.validate(spec, shape)
        yield {
            "done": True, "mode": shape, "session": session_id, "turn": session["turn"],
            "spec": spec, "valid": not errors, "errors": errors, "usage": usage, "raw": text,
        }


def new_session(prompt, shape):
    """Start a transcript with the catalog prompt and the user's request."""
    session_id = uuid.uuid4().hex[:12]
    while len(SESSIONS) >= MAX_SESSIONS:
        SESSIONS.pop(next(iter(SESSIONS)))
    SESSIONS[session_id] = {
        "shape": shape, "turn": 1, "lock": threading.Lock(),
        "messages": [{"role": "system", "content": catalog.system_prompt(shape)}, {"role": "user", "content": prompt}],
    }
    return session_id


def open_ended_html(prompt):
    """Step 03: no catalog. The model's HTML as it streams, then the whole document."""
    messages = [{"role": "system", "content": HTML_PROMPT}, {"role": "user", "content": prompt}]
    for item in stream_text(messages):
        if isinstance(item, dict):
            yield item
            continue
        text, usage = item
        yield {"done": True, "mode": "html", "html": FENCE.sub("", text), "usage": usage, "raw": text}


def run_mode(prompt, mode):
    if mode == "static":
        return static_components(prompt)
    if mode == "html":
        return open_ended_html(prompt)
    return declarative_turn(new_session(prompt, mode))


def guarded(messages):
    """The messages, then a terminal frame on failure: the page must never wait for one that is not coming."""
    try:
        yield from messages
    except Exception as error:  # noqa: BLE001 - the error is the frame
        yield {"done": True, "error": f"{type(error).__name__}: {error}"}


async def frames(messages, request):
    """Encode the messages as they come; stop pulling from the model when the page has gone."""
    pending = iter(guarded(messages))
    try:
        while (message := await run_in_threadpool(next, pending, None)) is not None:
            if await request.is_disconnected():
                break
            yield sse(message)
    finally:
        pending.close()  # closes the generator chain, and with it the model stream


def stream(messages, request):
    return StreamingResponse(frames(messages, request), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.post("/api/run")
def run(body: Run, request: Request):
    return stream(run_mode(body.prompt, body.mode), request)


@app.post("/api/action")
def action(body: Action, request: Request):
    """The loop closes: the event becomes a user message, the model answers with the next layout."""
    session = SESSIONS.get(body.session)
    if session is None:
        raise HTTPException(404, "unknown session")
    if session["lock"].locked():
        raise HTTPException(409, "a turn is still running on this session")
    session["turn"] += 1
    session["messages"].append({"role": "user", "content": EVENT_PROMPT.format(action=body.action, payload=json.dumps(body.payload))})
    return stream(declarative_turn(body.session), request)


@app.get("/api/schema/{shape}")
def schema(shape: Literal["tree", "flat"]):
    return catalog.SCHEMAS[shape]()


app.mount("/", StaticFiles(directory=HERE / "page", html=True), name="page")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8010)
