"""Generative UI step 02 - capture a generative UI reply from TrueForge.

TrueForge (Part 7 of the harness codelab) has generative UI built in: with
`config.generative_ui.enabled`, the agent answers a dashboard request with
an OpenUI Lang program inside a ```openui fence, and the TrueForge chat UI
renders it. This module opens such a session over the Python SDK, streams
one turn, and pulls the program out of the reply so a page of ours can
render it instead.
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
INSTRUCTIONS = (
    "You are a concise assistant. When the user asks for a dashboard, a report, "
    "a table or a chart, answer with generative UI."
)

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
    the final message and the token totals.
    """
    if session_id is None:
        session_id = open_session()
    stream = client().sessions.create_turn_stream(session_id=session_id, input=[UserMessage(content=prompt)])
    pieces, text, metrics = [], None, {}
    status = "incomplete"  # only turn.done can change it: a stream that ends without it is a failure, not a reply
    for event in stream.with_metadata():
        data = event.data
        if data.type == "model.message.delta" and data.thread_id == "main" and data.content:
            pieces.append(data.content)
            if on_delta:
                on_delta(data.content)
        elif data.type == "turn.done":
            status = data.state.status
            if status == "done":
                output = data.state.output
                if output is not None and isinstance(output.content, str):
                    text = output.content
                if data.state.metrics is not None:
                    metrics = data.state.metrics.dict(exclude_none=True)
    if status != "done":
        raise RuntimeError(f"the turn ended {status!r} after {len(''.join(pieces))} streamed characters")
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
