"""Step 02 - declarative generation: the model writes a whole layout as JSON.

POST /api/run {"prompt": ..., "mode": "static" | "tree" | "flat"} answers
with an SSE stream. Static mode is step 01: one {"component", "props"}
message per tool call. Tree and flat mode stream the model's JSON as it
arrives, {"delta": "..."} per chunk, then {"done": true, "spec": ...,
"valid": ..., "errors": [...]} once the whole layout is parsed and checked
against the catalog's JSON Schema. GET / serves the page.
"""

import json
import mimetypes
import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import catalog
import llm

HERE = Path(__file__).parent
mimetypes.add_type("text/javascript", ".mjs")  # module scripts need this type; not every OS registers it

STATIC_PROMPT = """You build dashboards out of prebuilt components.
You cannot write prose or markup. The only way to answer is to call the show_* tools.
Call several tools in one reply: three or four show_metric calls for the headline
numbers, one show_table for the detail, and one show_chart for the trend.
Invent plausible sample data when the user gives none. Keep titles short."""

FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$")

app = FastAPI(title="genui step 02: declarative tree")


class Run(BaseModel):
    prompt: str
    mode: Literal["static", "tree", "flat"] = "flat"


def sse(message):
    """One SSE frame: a data line with the JSON, then a blank line."""
    return f"data: {json.dumps(message)}\n\n"


def usage_of(event):
    return {k: v for k, v in event.items() if k != "type"}


def static_components(prompt):
    """Step 01: one model turn with tools, one message per component the model chose."""
    messages = [{"role": "system", "content": STATIC_PROMPT}, {"role": "user", "content": prompt}]
    for event in llm.stream_chat(messages, tools=catalog.TOOL_SCHEMAS):
        if event["type"] == "tool_call":
            message = catalog.message_from_call(event["name"], event["arguments"])
            if message is not None:
                yield message
        elif event["type"] == "text":
            yield {"note": event["text"]}  # the model spoke instead of calling a tool
        elif event["type"] == "usage":
            yield {"done": True, "mode": "static", "usage": usage_of(event)}


def parse_spec(text):
    """The model's JSON, with any code fence stripped. None when it does not parse."""
    try:
        return json.loads(FENCE.sub("", text))
    except json.JSONDecodeError:
        return None


def declarative_layout(prompt, shape):
    """One model turn with the catalog prompt: the JSON as it streams, then the checked spec."""
    messages = [{"role": "system", "content": catalog.system_prompt(shape)}, {"role": "user", "content": prompt}]
    parts = []
    usage = None
    for event in llm.stream_chat(messages, response_format={"type": "json_object"}):
        if event["type"] == "text":
            parts.append(event["text"])
            yield {"delta": event["text"]}
        elif event["type"] == "usage":
            usage = usage_of(event)
    spec = parse_spec("".join(parts))
    errors = ["the reply is not JSON"] if spec is None else catalog.validate(spec, shape)
    yield {"done": True, "mode": shape, "spec": spec, "valid": not errors, "errors": errors, "usage": usage}


def run_mode(prompt, mode):
    return static_components(prompt) if mode == "static" else declarative_layout(prompt, mode)


@app.post("/api/run")
def run(body: Run):
    frames = (sse(message) for message in run_mode(body.prompt, body.mode))
    return StreamingResponse(frames, media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.get("/api/schema/{shape}")
def schema(shape: Literal["tree", "flat"]):
    return catalog.SCHEMAS[shape]()


app.mount("/", StaticFiles(directory=HERE / "page", html=True), name="page")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8010)
