"""Step 01 - replay the spec's contact-form stream over SSE.

A2UI does not choose a transport; it only asks for ordered delivery and
message framing. Server-sent events give both: one JSON envelope per
`data:` line. The stream pauses between messages so the page can be seen
building the surface up.
"""

import asyncio
import json
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

import a2ui

HERE = Path(__file__).parent
PORT = 8741
GAP = 0.6  # seconds between messages; the demo shortens it

app = FastAPI()


def contact_form_messages():
    """The four messages of the spec's Example Stream, checks repaired to pass the schema."""
    messages = a2ui.read_stream(HERE / "contact_form.jsonl")
    for message in messages:
        a2ui.repair_checks(message)
        problem = a2ui.validate(message)
        if problem:
            raise ValueError(f"refusing to stream an invalid message: {problem}")
    return messages


def sse(message, event=None):
    head = f"event: {event}\n" if event else ""
    return f"{head}data: {json.dumps(message)}\n\n"


@app.get("/stream")
async def stream(all: bool = False):
    """createSurface, updateComponents, updateDataModel; with ?all=1 the deleteSurface too."""
    messages = contact_form_messages()
    if not all:
        messages = [m for m in messages if a2ui.message_type(m) != "deleteSurface"]

    async def body():
        for index, message in enumerate(messages):
            if index:
                await asyncio.sleep(GAP * (4 if a2ui.message_type(message) == "deleteSurface" else 1))
            yield sse(message)
        yield sse({"count": len(messages)}, event="done")

    return StreamingResponse(body(), media_type="text/event-stream")


app.mount("/", StaticFiles(directory=HERE / "static", html=True), name="static")


if __name__ == "__main__":
    print(f"open http://127.0.0.1:{PORT}/")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
