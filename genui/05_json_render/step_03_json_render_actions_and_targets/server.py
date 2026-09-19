"""FastAPI server: streams the first spec, then runs one model turn per action.

    POST /stream {"prompt": "..."}             -> the model's JSONL, forwarded chunk by chunk; starts a session
    POST /action {"action": "...", "params": {}} -> the next turn: JSONL patches against the spec on screen
    GET  /last                                 -> the compiled spec, all patches so far, the transcript, timings
    GET  /spec                                 -> the compiled spec alone (the page opens on it with ?last=1)
    GET  /                                     -> index.html; app.mjs, registry.mjs, catalog.mjs as static files

The session is one transcript: system prompt, the user's request, the
model's patches, then one user message per button press and the model's
patches in reply. The same SpecStream compiles every turn, so LAST["spec"]
is always what the page shows. One session at a time; this is a demo.
"""

import json
import time
from pathlib import Path

import jsonschema
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import llm
from json_patch import SpecStream
from prompt import catalog_json, system_prompt
from spec import check_spec

STEP = Path(__file__).resolve().parent
app = FastAPI(title="json-render step 3")
SESSION = {"messages": [], "compiler": None, "turns": []}
LAST = {}

ACTION_TURN = """The user pressed a button bound to the action "{action}" with params {params}.
Answer with JSONL patches (RFC 6902) that edit the spec you already produced: use replace for
values that change, add for new elements and for new state, remove for elements to drop. Keep
existing ids. Output only patches, one per line."""


class StreamRequest(BaseModel):
    prompt: str


class ActionRequest(BaseModel):
    action: str
    params: dict = {}


def relay(messages, label):
    """Run one model turn on the transcript, forward its chunks, compile them.

    When the model call fails part-way, the stream ends with one more line,
    {"error": "..."}, the transcript keeps no half turn (the user message that
    started it is removed), and the turn is recorded with the error.
    """
    started = time.perf_counter()
    compiler = SESSION["compiler"]
    before = len(compiler.patches)
    text = []
    first_paint = None
    error, usage = None, None
    try:
        stream = llm.stream_text(messages)
        for chunk in stream:
            text.append(chunk)
            compiler.push(chunk)
            if first_paint is None and compiler.has_root():
                first_paint = time.perf_counter() - started
            yield chunk
        usage = stream.usage
    except Exception as failure:  # noqa: BLE001 - the model call failed: say so on the wire, keep the transcript whole
        error = f"{type(failure).__name__}: {failure}"
        yield "\n" + json.dumps({"error": error}) + "\n"
    compiler.finish()
    reply = "".join(text)
    if error is None:
        messages.append({"role": "assistant", "content": reply})
    elif messages and messages[-1]["role"] == "user":
        messages.pop()  # no reply came: the next turn must not start with two user messages
    SESSION["turns"].append({
        "label": label,
        "patches": compiler.patches[before:],
        "seconds": round(time.perf_counter() - started, 2),
        "first_paint": round(first_paint, 2) if first_paint is not None else None,
        "usage": usage,
        "lines": [line for line in reply.splitlines() if line.strip()],
        "error": error,
    })
    LAST.update(
        spec=compiler.spec,
        patches=compiler.patches,
        skipped=compiler.skipped,
        problems=check_spec(compiler.spec, catalog_json()),
        turns=SESSION["turns"],
        error=error,
    )


@app.post("/stream")
def stream(request: StreamRequest):
    SESSION["messages"] = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": request.prompt},
    ]
    SESSION["compiler"] = SpecStream()
    SESSION["turns"] = []
    LAST.clear()
    return StreamingResponse(relay(SESSION["messages"], "generate"), media_type="application/x-ndjson")


@app.post("/action")
def action(request: ActionRequest):
    if SESSION["compiler"] is None:
        raise HTTPException(status_code=409, detail="no spec on screen yet; POST /stream first")
    actions = catalog_json()["actions"]
    if request.action not in actions:
        raise HTTPException(status_code=400, detail=f"unknown action {request.action!r}; the catalog has {sorted(actions)}")
    # the params carry the Zod schema the catalog declared, exported as JSON Schema: check them here
    # so the model is never asked about a press whose params are not what the catalog promised
    for problem in jsonschema.Draft202012Validator(actions[request.action]["params"]).iter_errors(request.params):
        raise HTTPException(status_code=400, detail=f"{request.action} params: {problem.message}")
    SESSION["messages"].append({"role": "user", "content": ACTION_TURN.format(action=request.action, params=json.dumps(request.params))})
    return StreamingResponse(relay(SESSION["messages"], request.action), media_type="application/x-ndjson")


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

    uvicorn.run(app, host="127.0.0.1", port=8057)
