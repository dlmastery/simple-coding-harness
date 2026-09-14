"""Step 03 - open-ended generation: the model writes the HTML itself.

POST /api/run {"prompt": ..., "mode": "static" | "tree" | "flat" | "html"}
answers with an SSE stream. Static mode is step 01, tree and flat are step
02. Html mode streams the model's document as {"delta": "..."} chunks and
ends with {"done": true, "html": ...}; the page mounts it in a sandboxed
iframe. Every done message carries "raw", the exact text the model wrote,
so the demo can count tokens per mode. GET / serves the page.
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

HTML_PROMPT = """You build dashboards as one self-contained HTML document.
Write a complete document: <!doctype html>, <html>, <head> with one <style>, <body>,
and one <script> at the end. Everything inline: no external stylesheets, scripts,
fonts or images, because the page that hosts you blocks all network access.
Show three or four headline numbers, one table of detail and one chart drawn as
inline SVG. Invent plausible sample data when the user gives none.
Include at least one <button>. On click it must call
parent.postMessage({type: "event", name: "<what it does>", payload: {...}}, "*")
so the host page hears it. Output only the HTML, no code fence, no prose."""

FENCE = re.compile(r"^\s*```(?:json|html)?\s*|\s*```\s*$")

app = FastAPI(title="genui step 03: open-ended html")


class Run(BaseModel):
    prompt: str
    mode: Literal["static", "tree", "flat", "html"] = "html"


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


def declarative_layout(prompt, shape):
    """Step 02: one model turn with the catalog prompt: the JSON as it streams, then the checked spec."""
    messages = [{"role": "system", "content": catalog.system_prompt(shape)}, {"role": "user", "content": prompt}]
    for item in stream_text(messages, response_format={"type": "json_object"}):
        if isinstance(item, dict):
            yield item
            continue
        text, usage = item
        spec = parse_spec(text)
        errors = ["the reply is not JSON"] if spec is None else catalog.validate(spec, shape)
        yield {"done": True, "mode": shape, "spec": spec, "valid": not errors, "errors": errors, "usage": usage, "raw": text}


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
    return declarative_layout(prompt, mode)


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
