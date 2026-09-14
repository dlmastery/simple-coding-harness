"""The harness behind an AG-UI endpoint. POST /agent runs one harness turn
as an event stream; GET / serves the page, which uses @ag-ui/client.

The harness works in the current directory: its tools, its permission
rules and its system prompt all read it at import time. So the server
moves into the work directory first, then imports the bridge.

    python server.py            # http://127.0.0.1:8023, work dir ./workdir
    HARNESS_WORKDIR=/some/dir python server.py
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

    def stream():
        for event in run(input):
            yield encoder.encode(event)

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
    uvicorn.run(app, host="127.0.0.1", port=PORT)
