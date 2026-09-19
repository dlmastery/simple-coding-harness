"""The harness behind an AG-UI endpoint. POST /agent runs one harness turn
as an event stream; GET / serves the page, which uses @ag-ui/client.

The harness works in the current directory: its tools, its permission
rules and its system prompt all read it at import time. So the server
moves into the work directory first, then imports the bridge.

    python server.py            # http://127.0.0.1:8023, work dir ./workdir
    HARNESS_WORKDIR=/some/dir python server.py

This server runs shell commands in the work directory for anyone who can
reach the port, and the harness's "ask" tier is auto-approved (bridge.py).
It binds to 127.0.0.1 and has no authentication: a local demo, never
something to expose.
"""

import os
from pathlib import Path

STEP = Path(__file__).resolve().parent
WORKDIR = Path(os.environ.get("HARNESS_WORKDIR", STEP / "workdir")).resolve()
WORKDIR.mkdir(parents=True, exist_ok=True)
os.chdir(WORKDIR)  # before the harness is imported: it takes the cwd as its project

from ag_ui.core import RunAgentInput  # noqa: E402
from ag_ui.encoder import EventEncoder  # noqa: E402
from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.concurrency import run_in_threadpool  # noqa: E402
from fastapi.responses import FileResponse, StreamingResponse  # noqa: E402

from bridge import run  # noqa: E402

PAGE_FILES = {"index.html", "app.js"}
BUNDLE = STEP / "vendor" / "ag-ui-client.js"
PORT = 8023

app = FastAPI(title="AG-UI step 03")


@app.post("/agent")
def agent_endpoint(input: RunAgentInput, request: Request):
    """Encode every event of the run and stream it as text/event-stream."""
    encoder = EventEncoder(accept=request.headers.get("accept"))
    events = run(input)
    sse = encoder.get_content_type() == "text/event-stream"

    async def stream():
        # The generator runs in a worker thread, one event per pull; when the
        # page has gone it is closed, and the model stream with it.
        try:
            while (event := await run_in_threadpool(next, events, None)) is not None:
                if await request.is_disconnected():
                    break
                if isinstance(event, str):  # the keepalive: an SSE comment, meaningless in protobuf
                    if sse:
                        yield event
                    continue
                yield encoder.encode(event)
        finally:
            events.close()

    return StreamingResponse(stream(), media_type=encoder.get_content_type())


@app.get("/")
def index():
    return FileResponse(STEP / "index.html")


@app.get("/vendor/ag-ui-client.js")
def client_bundle():
    if not BUNDLE.exists():
        raise HTTPException(404, "run `npm install && npm run build` to bundle @ag-ui/client")
    return FileResponse(BUNDLE, media_type="text/javascript")


@app.get("/{name}")
def page_file(name: str):
    if name not in PAGE_FILES:
        raise HTTPException(404)
    return FileResponse(STEP / name)


if __name__ == "__main__":
    import uvicorn

    print(f"harness work directory: {WORKDIR}")
    print("permission 'ask' is auto-approved and bash runs here: local use only, never expose this port")
    uvicorn.run(app, host="127.0.0.1", port=PORT)
