"""Step 03 - the host: a page, its two modules, and one model endpoint.

The host is a different party from the MCP server, so it is a different
process on a different port. It serves host.html, and it owns the chat
model: the page posts the conversation and the server's tool schemas to
/chat, and the model answers with text or with a tool call. Everything MCP
happens in the browser, in mcp-http.mjs. The host's key never reaches the
page, and the server's key never reaches the host.

One addition to step 01: the page may send `context`, the text the view
handed over with `ui/update-model-context`. It goes in front of the
conversation as a second system message, so the next turn knows what the
user did inside the interface.

    python host.py            # http://127.0.0.1:8768/
"""

import argparse
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

import llm

HERE = Path(__file__).parent
PORT = 8768

SYSTEM_PROMPT = """You are the assistant inside a chat host that can render MCP Apps.
When a tool is the right way to answer, call it. After a tool result, answer in one or two short sentences.
Do not describe the numbers row by row: the user sees the interface."""

app = FastAPI(title="genui minimal MCP Apps host, step 03")


class ChatRequest(BaseModel):
    messages: list[dict]
    tools: list[dict] = []
    context: str = ""  # what the view reported with ui/update-model-context, if anything


def chat_turn(messages, tools, context=""):
    """One model turn for the page: the system prompt, the interface's context, the transcript."""
    system = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context:
        system.append({"role": "system", "content": f"Context from the interface: {context}"})
    return llm.complete(system + messages, tools or None)


@app.post("/chat")
def chat(request: ChatRequest):
    return chat_turn(request.messages, request.tools, request.context)


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
