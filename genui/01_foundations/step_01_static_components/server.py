"""Step 01 - static generation: the model calls show_* tools, the page renders components.

POST /api/run {"prompt": ...} answers with an SSE stream. Every finished tool
call becomes one message {"component": "Metric", "props": {...}}; the last
message is {"done": true, "usage": {...}}, or {"done": true, "error": "..."}
when the model call failed. GET / serves the page.
"""

import json
import mimetypes
from pathlib import Path

from fastapi import FastAPI, Request
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

SYSTEM_PROMPT = """You build dashboards out of prebuilt components.
You cannot write prose or markup. The only way to answer is to call the show_* tools.
Call several tools in one reply: three or four show_metric calls for the headline
numbers, one show_table for the detail, and one show_chart for the trend.
Invent plausible sample data when the user gives none. Keep titles short."""

app = FastAPI(title="genui step 01: static components")


class Run(BaseModel):
    prompt: str


def sse(message):
    """One SSE frame: a data line with the JSON, then a blank line."""
    return f"data: {json.dumps(message)}\n\n"


def components(prompt):
    """Run one model turn and yield one message per component the model chose."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    for event in llm.stream_chat(messages, tools=catalog.TOOL_SCHEMAS):
        if event["type"] == "tool_call":
            message = catalog.message_from_call(event["name"], event["arguments"])
            if message is not None:
                yield message
        elif event["type"] == "text":
            yield {"note": event["text"]}  # the model spoke instead of calling a tool
        elif event["type"] == "usage":
            yield {"done": True, "usage": {k: v for k, v in event.items() if k != "type"}}


def guarded(messages):
    """The messages, then a terminal frame on failure: the page must never wait for one that is not coming."""
    try:
        yield from messages
    except Exception as error:  # noqa: BLE001 - the error is the frame
        yield {"done": True, "error": f"{type(error).__name__}: {error}"}


async def stream(messages, request):
    """Encode the messages as they come; stop pulling from the model when the page has gone."""
    pending = iter(guarded(messages))
    try:
        while (message := await run_in_threadpool(next, pending, None)) is not None:
            if await request.is_disconnected():
                break
            yield sse(message)
    finally:
        pending.close()  # closes the generator chain, and with it the model stream


@app.post("/api/run")
def run(body: Run, request: Request):
    return StreamingResponse(stream(components(body.prompt), request), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


app.mount("/", StaticFiles(directory=HERE / "page", html=True), name="page")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8010)
