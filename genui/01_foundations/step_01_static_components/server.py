"""Step 01 - static generation: the model calls show_* tools, the page renders components.

POST /api/run {"prompt": ...} answers with an SSE stream. Every finished tool
call becomes one message {"component": "Metric", "props": {...}}; the last
message is {"done": true, "usage": {...}}. GET / serves the page.
"""

import json
import mimetypes
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import catalog
import llm

HERE = Path(__file__).parent
mimetypes.add_type("text/javascript", ".mjs")  # module scripts need this type; not every OS registers it

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


@app.post("/api/run")
def run(body: Run):
    frames = (sse(message) for message in components(body.prompt))
    return StreamingResponse(frames, media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


app.mount("/", StaticFiles(directory=HERE / "page", html=True), name="page")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8010)
