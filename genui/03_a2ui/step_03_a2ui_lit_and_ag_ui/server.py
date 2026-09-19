"""Step 03 - A2UI carried over AG-UI.

POST /agent  RunAgentInput -> SSE of AG-UI events:
    RUN_STARTED, STEP_STARTED/FINISHED per generation attempt,
    CUSTOM name="a2ui" value=<one A2UI envelope> for every message,
    TEXT_MESSAGE_* for the model's prose, RUN_FINISHED with the usage.
An action from the page comes back as a new run whose forwardedProps carry
the A2UI action and the client data model; the answer is a CUSTOM a2ui event.

The generate loop is step 02's. Only the wire changed: the ag-ui-protocol
package's event classes and EventEncoder, instead of hand-written SSE lines.

As in step 02, every generation starts by deleting the surfaces of the
previous one: the official renderer refuses a repeated createSurface, so
the reset is explicit on the wire and in the mirror. The mirror is one per
process, keyed by nothing: one page at a time, even though every run
carries a threadId.
"""

import asyncio
import json
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from ag_ui.core import (
    CustomEvent,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StepFinishedEvent,
    StepStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from ag_ui.encoder import EventEncoder
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

import envelope
import llm
import prompt

HERE = Path(__file__).parent
PORT = 8743
ATTEMPTS = 2  # one generation, one correction
KEEPALIVE_AFTER = 15  # seconds of silence (the model thinking) before an SSE comment goes out

app = FastAPI()
STORE = envelope.SurfaceStore()  # the server's mirror of what the page holds


def stream_model(messages):
    """Text deltas from the model. Tests replace this with a scripted reply."""
    return llm.stream(messages)


def mirror(message):
    """Apply a message to the server's own SurfaceStore before it goes to the page."""
    if envelope.message_type(message) == "createSurface":
        message["createSurface"]["sendDataModel"] = True  # ask the page for its data model with every action
    try:
        STORE.apply(message)
    except ValueError:
        pass  # a surface the page never saw either; the page skips it the same way
    return None, message


def generate(user_prompt):
    """Yield (event, payload) pairs: the progressive messages, then the final ones."""
    for surface_id in list(STORE.surfaces):
        yield mirror(envelope.delete_surface(surface_id))  # the previous generation goes first
    conversation = [{"role": "system", "content": prompt.system_prompt()}, {"role": "user", "content": user_prompt}]
    for attempt in range(1, ATTEMPTS + 1):
        yield "step", {"attempt": attempt, "started": True}
        parser = prompt.stream_parser()
        created, reply = [], []
        for chunk in stream_model(conversation):
            reply.append(chunk)
            if parser is None:
                continue  # the progressive pass gave up; the final pass still runs
            try:
                parts = parser.process_chunk(chunk)
            except Exception as error:  # the stream parser does not repair; the full parser does
                yield "note", {"attempt": attempt, "streaming_stopped": f"{type(error).__name__}: {error}"[:200]}
                parser = None
                continue
            for part in parts:
                for message in part.a2ui_json or []:
                    kind = envelope.message_type(message)
                    if kind == "createSurface":
                        created.append(message["createSurface"]["surfaceId"])
                    if kind == "updateDataModel":
                        continue  # partial values arrive without their path; the final pass sends them
                    yield mirror(message)
        text = "".join(reply)
        try:
            messages, prose = prompt.parse_reply(text)
        except ValueError as error:
            yield "note", {"attempt": attempt, "error": str(error)[:300]}
            for surface_id in created:
                yield mirror(envelope.delete_surface(surface_id))
            yield "step", {"attempt": attempt, "started": False}
            conversation += [{"role": "assistant", "content": text},
                             {"role": "user", "content": f"The reply failed validation. Fix it and send the complete reply again.\n{error}"}]
            continue
        for message in messages:
            problem = envelope.validate(message)
            if problem:
                yield "note", {"attempt": attempt, "warning": problem}
            if envelope.message_type(message) == "createSurface" and message["createSurface"]["surfaceId"] in created:
                continue  # the page has it since the streaming pass
            yield mirror(message)  # the final, validated structure and data
        if prose:
            yield "text", " ".join(prose)
        yield "step", {"attempt": attempt, "started": False}
        yield "done", {"attempt": attempt, "usage": llm.last_usage, "reply_chars": len(text)}
        return
    yield "error", "gave up after the correction attempt"


def status_path(surface):
    """The path of the Text the model bound for confirmations: the mirror knows the structure."""
    for component in surface.components.values():
        path = component.get("text", {}).get("path") if isinstance(component.get("text"), dict) else None
        if component["component"] == "Text" and path and path.endswith("status"):
            return path
    return "/status"


def answer_action(action, client_data_model):
    """A click's answer. The page sent its data model along (sendDataModel), so
    the server can read what the user typed without trusting its mirror."""
    surface = STORE.surfaces.get(action["surfaceId"])
    path = status_path(surface) if surface else "/status"
    typed = (client_data_model or {}).get("surfaces", {}).get(action["surfaceId"], {})
    fields = ", ".join(f"{key}={value!r}" for key, value in action.get("context", {}).items())
    when = datetime.now(timezone.utc).strftime("%H:%M:%S")
    # the context carries what the Button bound; the data model carries every field the user typed
    text = f"Server got '{action['name']}' at {when} with {fields}; the client data model says {json.dumps(typed)[:200]}"
    yield mirror(envelope.update_data_model(action["surfaceId"], path, text))
    yield "done", {"answered": action["name"]}


def run(agent_input: RunAgentInput):
    """One AG-UI run: route to the action answer or the generate loop.
    The page sends the whole thread; the loop reads only the last user message."""
    a2ui_props = (agent_input.forwarded_props or {}).get("a2ui") if isinstance(agent_input.forwarded_props, dict) else None
    if a2ui_props and a2ui_props.get("action"):
        return answer_action(a2ui_props["action"], a2ui_props.get("a2uiClientDataModel"))
    user_turns = [m for m in agent_input.messages if m.role == "user"]
    return generate(user_turns[-1].content if user_turns else "")


def to_events(agent_input, pairs):
    """Map the loop's (kind, payload) pairs onto AG-UI event objects."""
    ids = dict(thread_id=agent_input.thread_id, run_id=agent_input.run_id)
    yield RunStartedEvent(**ids)
    for kind, payload in pairs:
        if kind is None:
            yield CustomEvent(name="a2ui", value=payload)
        elif kind == "note":
            yield CustomEvent(name="a2ui.note", value=payload)
        elif kind == "step":
            step = StepStartedEvent if payload["started"] else StepFinishedEvent
            yield step(step_name=f"attempt {payload['attempt']}")
        elif kind == "text":
            message_id = f"{agent_input.run_id}-text"
            yield TextMessageStartEvent(message_id=message_id)
            yield TextMessageContentEvent(message_id=message_id, delta=payload)
            yield TextMessageEndEvent(message_id=message_id)
        elif kind == "error":
            yield RunErrorEvent(message=payload)
            return
        elif kind == "done":
            yield RunFinishedEvent(**ids, result=payload)
            return
    yield RunFinishedEvent(**ids)


@app.post("/agent")
async def agent_endpoint(agent_input: RunAgentInput, request: Request):
    """The body is validated by FastAPI (a bad one is a 422, not a 500); the events stream as SSE."""
    encoder = EventEncoder(accept=request.headers.get("accept"))
    sse = encoder.get_content_type() == "text/event-stream"  # a comment line means nothing in protobuf
    events = queue.Queue()

    def work():
        try:
            for event in to_events(agent_input, run(agent_input)):
                events.put(encoder.encode(event))
        except Exception as error:  # the page sees the failure instead of a hang
            events.put(encoder.encode(RunErrorEvent(message=f"{type(error).__name__}: {error}"[:300])))
        events.put(None)

    threading.Thread(target=work, daemon=True).start()

    async def stream():
        quiet_since = time.monotonic()
        while True:
            try:
                frame = events.get_nowait()
            except queue.Empty:
                if sse and time.monotonic() - quiet_since > KEEPALIVE_AFTER:
                    yield ": keepalive\n\n"  # an SSE comment: the client skips it, a proxy keeps the stream
                    quiet_since = time.monotonic()
                await asyncio.sleep(0.02)
                continue
            quiet_since = time.monotonic()
            if frame is None:
                return
            yield frame

    return StreamingResponse(stream(), media_type=encoder.get_content_type())


app.mount("/", StaticFiles(directory=HERE / "static", html=True), name="static")


if __name__ == "__main__":
    print(f"open http://127.0.0.1:{PORT}/")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
