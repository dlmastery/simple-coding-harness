"""Generative UI step 03 - a TrueForge agent that may add one HtmlArtifact.

Step 02's session, with one change: the instructions. TrueForge's own
harness prompt teaches the agent OpenUI Lang and its catalog of static
components. The instructions here add the open-ended half of the report's
hybrid: only when the user asks for something interactive, the agent may
put one `HtmlArtifact("title", "document")` statement in its program, the
document a self-contained HTML/CSS/JS page written to rules copied from
OpenUI's html-artifact example. TrueForge does not know the component; the
page in web/ does. Everything else (ask, extract_program) is step 02.
"""

import os
import re
import sys

try:
    import truststore

    truststore.inject_into_ssl()  # the system trust store, so HTTPS works behind a corporate proxy
except ImportError:
    pass

from trueforge_sdk import (
    AgentSpec,
    GenerativeUiConfig,
    Model,
    RuntimeConfig,
    SessionAgentSpecBody,
    TrueForge,
    UserMessage,
)

BASE_URL = os.environ.get("TRUEFORGE_BASE_URL", "http://localhost:8790")
MODEL = os.environ.get("TRUEFORGE_MODEL", "openai/gpt-4-1-mini")
TIMEOUT = 600
# The rules are OpenUI's html-artifact prompt options, adapted to TrueForge's
# catalog: the catalog is the default, the artifact is the exception. Three
# things were added after live runs, because TrueForge's harness prompt
# makes the agent call get_openui_instructions before any openui fence, and
# the guide that tool returns (about 4,400 tokens, arriving after these
# instructions) teaches Form, Input, Buttons and $state, which this page
# does not run. Without them gpt-4.1-mini answered an interactive request
# with those and never wrote HtmlArtifact. (1) The example, as OpenUI's
# prompt options have. (2) The REMOVED / ADDED framing: the surface's catalog
# is the guide's minus the interactive components plus HtmlArtifact, so the
# model does not invent replacements such as NumInput. (3) The exact shape
# of an interactive reply, one intro and one artifact, so the model does
# not split the experience into four artifacts.
INSTRUCTIONS = """You are a concise assistant. When the user asks for a dashboard, a report, a table, a chart or something interactive, answer with generative UI: call get_openui_instructions first, then write the openui program.

The surface that renders your reply is not the standard one. Its catalog is the one get_openui_instructions describes, with two changes:
- REMOVED: Form, FormControl, Input, Buttons, Button, Action, $ state variables, @ functions and expressions. This surface does not implement them; a program that uses them renders as nothing. Never use them, and never invent components that are not in the catalog.
- ADDED: HtmlArtifact(title: string, document: string). The document is a self-contained HTML/CSS/JavaScript page, run in a sandboxed iframe. This is the only way to give the user something interactive on this surface.

Rules for HtmlArtifact:
- Use it only when the user explicitly asks you to build something interactive: an app, game, simulation, calculator, visualization, or similar experience. Then the whole experience (every input, button and result) lives inside one document, and the program has exactly the shape of the example below: a Stack with one short TextContent intro and one HtmlArtifact, nothing else. Exactly one HtmlArtifact per reply.
- Use the catalog components for dashboards, reports, tables and charts. Never put a dashboard into an HtmlArtifact.
- Inside the document: inline CSS and JavaScript only. Do not depend on external scripts, stylesheets, fonts, images, or network requests.
- Do not wrap the document in Markdown fences. Keep the whole HtmlArtifact statement on one line. Encode line breaks as \\n inside the document string.
- The document is a double-quoted openui-lang string. Prefer single quotes inside HTML and JavaScript, and escape any double quotes or backslashes.
- The HtmlArtifact statement goes inside the same openui program as the catalog components, one statement per line, referenced from root like any other component.

Example of an interactive reply on this surface:

```openui
root = Stack([intro, artifact], "column", "m")
intro = TextContent("Here is a simple click counter:", "default")
artifact = HtmlArtifact("Interactive counter", "<!doctype html><html><head><style>body{font-family:system-ui;padding:2rem}button{padding:.5rem 1rem}</style></head><body><h1>Counter</h1><button id='count'>0</button><script>let count=0;document.querySelector('#count').addEventListener('click',event=>{event.currentTarget.textContent=String(++count)})</script></body></html>")
```
"""

FENCE = re.compile(r"```openui[^\n]*\n(.*?)```", re.DOTALL)

_client = None


def client():
    """The SDK client, created on first use so tests can point BASE_URL at a fake server."""
    global _client
    if _client is None:
        _client = TrueForge(base_url=BASE_URL, timeout=TIMEOUT)
    return _client


def open_session():
    """A session on an inline agent with generative UI switched on."""
    spec = AgentSpec(
        model=Model(name=MODEL),
        instructions=INSTRUCTIONS,
        config=RuntimeConfig(generative_ui=GenerativeUiConfig(enabled=True)),
    )
    session = client().sessions.create(agent=SessionAgentSpecBody(spec=spec))
    return session.data.id


def print_delta(text):
    sys.stdout.write(text)
    sys.stdout.flush()


def ask(prompt, session_id=None, on_delta=print_delta):
    """One streamed turn. Returns (session_id, reply text, metrics).

    Deltas on the main thread are the reply as it streams; turn.done carries
    the final message and the token totals. New in step 03: metrics also
    gets "tools", the system tools the model called (TrueForge hands the
    agent its OpenUI catalog through `get_openui_instructions`), and
    "calls", one usage dict per model call with TrueForge's input breakdown.
    """
    if session_id is None:
        session_id = open_session()
    stream = client().sessions.create_turn_stream(session_id=session_id, input=[UserMessage(content=prompt)])
    pieces, text, metrics, tools, calls = [], None, {}, [], []
    status, why = "incomplete", None  # only turn.done can change it: a stream that ends without it is a failure, not a reply
    for event in stream.with_metadata():
        data = event.data
        if data.type == "model.message.delta" and data.thread_id == "main":
            if data.content:
                pieces.append(data.content)
                if on_delta:
                    on_delta(data.content)
            for call in data.tool_calls or []:
                if call.function is not None and call.function.name:
                    tools.append(call.function.name)
            if data.usage is not None:
                calls.append(data.usage.dict(exclude_none=True))
        elif data.type == "turn.done":
            status = data.state.status
            why = getattr(data.state, "message", None) or getattr(data.state, "reason", None)  # error carries a message, cancelled a reason
            if status == "done":
                output = data.state.output
                if output is not None and isinstance(output.content, str):
                    text = output.content
                if data.state.metrics is not None:
                    metrics = data.state.metrics.dict(exclude_none=True)
    if status != "done":
        raise RuntimeError(f"the turn ended {status!r} ({why or 'no detail'}) after {len(''.join(pieces))} streamed characters")
    metrics.update(tools=tools, calls=calls)
    return session_id, text if text is not None else "".join(pieces), metrics


def extract_program(reply):
    """The OpenUI Lang program inside the first ```openui fence, or None.

    Text around the fence is prose for the chat; the fence is the interface.
    An unterminated fence (a reply cut mid-stream) still yields what arrived.
    """
    match = FENCE.search(reply)
    if match:
        return match.group(1).strip("\n")
    head = reply.find("```openui")
    if head == -1:
        return None
    body = reply[head:].split("\n", 1)
    return body[1].strip("\n") if len(body) == 2 and body[1].strip() else None
