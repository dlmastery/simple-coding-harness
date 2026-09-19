"""Step 02 - a model writes the A2UI messages.

POST /generate {prompt}  -> SSE: the messages as the model writes them, then the
                            validated final ones; the prompt-generate-validate loop
POST /action  {action}   -> JSON: the updateDataModel messages that answer a click

The reply streams through the SDK's DirectJsonStreamParser so the page paints
while the model is still writing. The finished reply then goes through the
full parser, which repairs small faults and validates against the catalog;
if that fails, the error goes back to the model once, the spec's loop.

Every generation starts by deleting the surfaces of the previous one, on
the page and in the mirror: a repeated createSurface is an error for the
official renderer (step 03), so the reset is explicit. The mirror is one
per process: this server is a demo for one page at a time.
"""

import asyncio
import json
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import envelope
import llm
import prompt

HERE = Path(__file__).parent
PORT = 8742
ATTEMPTS = 2  # one generation, one correction
KEEPALIVE_AFTER = 15  # seconds of silence (the model thinking) before an SSE comment goes out

app = FastAPI()
STORE = envelope.SurfaceStore()  # the server's mirror of what the page holds


class Generate(BaseModel):
    prompt: str


class Action(BaseModel):
    """The client-to-server action message; the fields the answer reads."""

    name: str
    surfaceId: str
    context: dict = {}


def sse(payload, event=None):
    head = f"event: {event}\n" if event else ""
    return f"{head}data: {json.dumps(payload)}\n\n"


def stream_model(messages):
    """Text deltas from the model. Tests replace this with a scripted reply."""
    return llm.stream(messages)


def mirror(message):
    """Apply a message to the server's own SurfaceStore before it goes to the page."""
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
            yield "note", {"prose": " ".join(prose)[:300]}
        yield "note", {"attempt": attempt, "usage": llm.last_usage, "reply_chars": len(text)}
        return
    yield "note", {"error": "gave up after the correction attempt"}


@app.post("/generate")
async def generate_endpoint(body: Generate):
    """Run generate() in a thread and forward its events over SSE as they happen."""
    events = queue.Queue()

    def work():
        try:
            for event, payload in generate(body.prompt):
                events.put((event, payload))
        except Exception as error:  # the page sees the failure instead of a hang
            events.put(("note", {"error": f"{type(error).__name__}: {error}"[:300]}))
        events.put(("done", {}))

    threading.Thread(target=work, daemon=True).start()

    async def stream():
        quiet_since = time.monotonic()
        while True:
            try:
                event, payload = events.get_nowait()
            except queue.Empty:
                if time.monotonic() - quiet_since > KEEPALIVE_AFTER:
                    yield ": keepalive\n\n"  # an SSE comment: the page ignores it, a proxy keeps the stream
                    quiet_since = time.monotonic()
                await asyncio.sleep(0.02)
                continue
            quiet_since = time.monotonic()
            yield sse(payload, event)
            if event == "done":
                return

    return StreamingResponse(stream(), media_type="text/event-stream")


def status_path(surface):
    """The path of the Text the model bound for confirmations: the mirror knows the structure."""
    for component in surface.components.values():
        path = component.get("text", {}).get("path") if isinstance(component.get("text"), dict) else None
        if component["component"] == "Text" and path and path.endswith("status"):
            return path
    return "/status"


def answer_action(action):
    """What a click gets back. A model turn could go here; this step answers
    directly so the loop stays visible: action in, updateDataModel out."""
    fields = ", ".join(f"{key}={value!r}" for key, value in action.get("context", {}).items())
    when = datetime.now(timezone.utc).strftime("%H:%M:%S")
    surface = STORE.surfaces.get(action["surfaceId"])
    path = status_path(surface) if surface else "/status"
    reply = envelope.update_data_model(action["surfaceId"], path, f"Server got '{action['name']}' at {when} with {fields}")
    return [mirror(reply)[1]]


@app.post("/action")
async def action_endpoint(action: Action):
    return answer_action(action.model_dump())


app.mount("/", StaticFiles(directory=HERE / "static", html=True), name="static")


if __name__ == "__main__":
    print(f"open http://127.0.0.1:{PORT}/")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
