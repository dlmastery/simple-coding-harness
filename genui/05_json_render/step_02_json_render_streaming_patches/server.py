"""FastAPI server: serves the page and streams the model's patches to it.

    POST /stream {"prompt": "..."}   -> the model's JSONL, forwarded chunk by chunk (application/x-ndjson)
    GET  /last                       -> the compiled spec, the patches, the timings and usage of the last stream
    GET  /spec                       -> the compiled spec alone (the page opens on it with ?last=1)
    GET  /                           -> index.html; app.mjs, registry.mjs, catalog.mjs as static files

While the chunks pass through, the same text feeds a SpecStream, so the server
holds the complete spec at the end and knows when the first paint was possible.
"""

import json
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import llm
from json_patch import SpecStream
from prompt import catalog_json, system_prompt
from spec import check_spec

STEP = Path(__file__).resolve().parent
app = FastAPI(title="json-render step 2")
LAST = {}


class StreamRequest(BaseModel):
    prompt: str


def relay(prompt):
    """Forward each chunk as it arrives, and compile a copy on the way.

    When the model call fails part-way, the stream ends with one more line,
    {"error": "..."}: not a patch (the compilers skip it), but the page reads
    it and stops with the reason instead of waiting forever.
    """
    started = time.perf_counter()
    compiler = SpecStream()
    timings = {"first_chunk": None, "first_paint": None, "complete": None}
    error, usage = None, None
    try:
        stream = llm.stream_text(system_prompt(), prompt)
        for chunk in stream:
            if timings["first_chunk"] is None:
                timings["first_chunk"] = time.perf_counter() - started
            compiler.push(chunk)
            if timings["first_paint"] is None and compiler.has_root():
                timings["first_paint"] = time.perf_counter() - started
            yield chunk
        usage = stream.usage
    except Exception as failure:  # noqa: BLE001 - the model call failed: say so on the wire and in /last
        error = f"{type(failure).__name__}: {failure}"
        yield "\n" + json.dumps({"error": error}) + "\n"
    compiler.finish()
    timings["complete"] = time.perf_counter() - started
    LAST.update(
        spec=compiler.spec,
        patches=compiler.patches,
        skipped=compiler.skipped,
        problems=check_spec(compiler.spec, catalog_json()),
        timings={k: round(v, 2) if v is not None else None for k, v in timings.items()},
        usage=usage,
        error=error,
    )


@app.post("/stream")
def stream(request: StreamRequest):
    return StreamingResponse(relay(request.prompt), media_type="application/x-ndjson")


@app.get("/last")
def last():
    if not LAST:
        raise HTTPException(status_code=404, detail="nothing streamed yet")
    return LAST


@app.get("/spec")
def last_spec():
    if not LAST:
        raise HTTPException(status_code=404, detail="nothing streamed yet")
    return LAST["spec"]


@app.get("/")
def index():
    return FileResponse(STEP / "index.html")


app.mount("/", StaticFiles(directory=STEP), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8056)
