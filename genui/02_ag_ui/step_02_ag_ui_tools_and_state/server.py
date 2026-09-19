"""One AG-UI endpoint. POST /agent takes a RunAgentInput and answers with an
event stream; GET / serves the page that reads it.

    python server.py            # http://127.0.0.1:8022
"""

from pathlib import Path

from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, StreamingResponse

from agent import run

STEP = Path(__file__).resolve().parent
PAGE_FILES = {"index.html", "app.js", "sse.mjs", "json-patch.mjs", "render.mjs"}
PORT = 8022

app = FastAPI(title="AG-UI step 02")


@app.post("/agent")
def agent_endpoint(input: RunAgentInput, request: Request):
    """Encode every event of the run and stream it as text/event-stream."""
    encoder = EventEncoder(accept=request.headers.get("accept"))
    events = run(input)

    async def stream():
        # The generator runs in a worker thread, one event per pull; when the
        # page has gone it is closed, and the model stream with it.
        try:
            while (event := await run_in_threadpool(next, events, None)) is not None:
                if await request.is_disconnected():
                    break
                yield encoder.encode(event)
        finally:
            events.close()

    return StreamingResponse(stream(), media_type=encoder.get_content_type())


@app.get("/")
def index():
    return FileResponse(STEP / "index.html")


@app.get("/{name}")
def page_file(name: str):
    if name not in PAGE_FILES:
        raise HTTPException(404)
    return FileResponse(STEP / name)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=PORT)
