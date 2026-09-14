"""Step 01 - the host: a page, its two modules, and one model endpoint.

The host is a different party from the MCP server, so it is a different
process on a different port. It serves host.html, and it owns the model:
the page posts the conversation and the server's tool schemas to /chat, and
the model answers with text or with a tool call. Everything MCP happens in
the browser, in mcp-http.mjs. The key never reaches the page.

    python host.py            # http://127.0.0.1:8766/
"""

import argparse
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

import llm

HERE = Path(__file__).parent
PORT = 8766

SYSTEM_PROMPT = """You are the assistant inside a chat host that can render MCP Apps.
When a tool is the right way to answer, call it. After a tool result, answer in one or two short sentences.
Do not describe the numbers row by row: the user sees the interface."""

app = FastAPI(title="genui minimal MCP Apps host")


class ChatRequest(BaseModel):
    messages: list[dict]
    tools: list[dict] = []


def chat_turn(messages, tools):
    """One model turn for the page: the system prompt goes in front, the reply comes back as is."""
    return llm.complete([{"role": "system", "content": SYSTEM_PROMPT}] + messages, tools or None)


@app.post("/chat")
def chat(request: ChatRequest):
    return chat_turn(request.messages, request.tools)


@app.get("/")
def index():
    return FileResponse(HERE / "host.html")


@app.get("/{name}.mjs")
def module(name: str):
    return FileResponse(HERE / f"{name}.mjs", media_type="text/javascript")


def main():
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT)
    cli = parser.parse_args()
    print(f"host page on http://127.0.0.1:{cli.port}/", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=cli.port, log_level="warning")


if __name__ == "__main__":
    main()
