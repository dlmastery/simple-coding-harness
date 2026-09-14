"""FastAPI server: serves the page and turns a request into a complete spec.

    POST /generate {"prompt": "..."}  -> {"spec": {...}, "usage": {...}, "seconds": 3.2}
    GET  /spec                        -> the last generated spec (the demo opens the page on it)
    GET  /                            -> index.html; app.mjs, registry.mjs, catalog.mjs as static files
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import llm
from prompt import catalog_json, system_prompt
from spec import check_spec

STEP = Path(__file__).resolve().parent
app = FastAPI(title="json-render step 1")
LAST = {"spec": None}


class GenerateRequest(BaseModel):
    prompt: str


@app.post("/generate")
def generate(request: GenerateRequest):
    spec, usage, seconds = llm.complete_spec(system_prompt(), request.prompt)
    problems = check_spec(spec, catalog_json())
    if problems:
        raise HTTPException(status_code=502, detail={"problems": problems, "spec": spec})
    LAST["spec"] = spec
    return {"spec": spec, "usage": usage, "seconds": round(seconds, 2)}


@app.get("/spec")
def last_spec():
    if LAST["spec"] is None:
        raise HTTPException(status_code=404, detail="nothing generated yet")
    return LAST["spec"]


@app.get("/")
def index():
    return FileResponse(STEP / "index.html")


app.mount("/", StaticFiles(directory=STEP), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8055)
