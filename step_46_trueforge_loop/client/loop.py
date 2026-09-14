"""Step 46 - The agent loop on TrueForge: one session, one streamed turn, deltas as they arrive.

The stage 2.4 loop lived in this process: build the request, call the model,
run the tools, append the results, repeat. On TrueForge that loop runs in the
server. This module opens a session, sends one user message, and reads the
turn's events back over Server-Sent Events. It prints text deltas as they
arrive and returns the session id, the final text and the turn's metrics.
"""

import os
import sys

try:
    import truststore

    truststore.inject_into_ssl()  # the system trust store, so HTTPS works behind a corporate proxy
except ImportError:
    pass

from trueforge_sdk import AgentSpec, Model, SessionAgentSpecBody, TrueForge, UserMessage

BASE_URL = os.environ.get("TRUEFORGE_BASE_URL", "http://localhost:8790")
MODEL = os.environ.get("TRUEFORGE_MODEL", "openai/gpt-4-1-mini")
INSTRUCTIONS = "You are a concise coding assistant. Answer in plain text, in a few sentences."
TIMEOUT = 600  # seconds; a turn holds one HTTP connection open for as long as it runs

_client = None


def client():
    """The SDK client, created on first use so tests can point BASE_URL at a fake server."""
    global _client
    if _client is None:
        _client = TrueForge(base_url=BASE_URL, timeout=TIMEOUT)
    return _client


def open_session():
    """Create a session bound to an inline agent spec and return its id."""
    spec = AgentSpec(model=Model(name=MODEL), instructions=INSTRUCTIONS)
    session = client().sessions.create(agent=SessionAgentSpecBody(spec=spec))
    return session.data.id


def print_delta(text):
    """Write one text fragment without a newline, then flush, so the reply appears as it streams."""
    sys.stdout.write(text)
    sys.stdout.flush()


def chat(prompt, session_id=None, on_delta=print_delta):
    """Run one turn. Return (session_id, text, metrics).

    A new session is opened when `session_id` is None. Passing an id back
    continues that conversation: the server chains the new turn onto the last
    one (`previous_turn_id` defaults to "auto"), so no history is resent.
    """
    if session_id is None:
        session_id = open_session()
    stream = client().sessions.create_turn_stream(session_id=session_id, input=[UserMessage(content=prompt)])
    pieces = []
    text = None
    metrics = {}
    for event in stream.with_metadata():
        data = event.data
        if data.type == "model.message.delta" and data.thread_id == "main" and data.content:
            pieces.append(data.content)
            if on_delta:
                on_delta(data.content)
        elif data.type == "turn.done":
            text, metrics = finish(data.state)
    if text is None:
        text = "".join(pieces)
    return session_id, text, metrics


def finish(state):
    """Read the final text and the metrics out of a turn.done state.

    `done` carries the final model.message in `output` (None when the turn
    paused for an approval) and the whole turn's token totals in `metrics`.
    `cancelled` and `error` carry a reason or a message instead.
    """
    if state.status != "done":
        detail = getattr(state, "reason", None) or getattr(state, "message", None) or ""
        return f"[turn {state.status}: {detail}]", {}
    output = state.output
    text = output.content if output is not None and isinstance(output.content, str) else None
    metrics = state.metrics.dict(exclude_none=True) if state.metrics is not None else {}
    return text, metrics


METRIC_LABELS = {
    "total_input_tokens": "input",
    "total_output_tokens": "output",
    "total_cache_read_tokens": "cached",
    "total_reasoning_tokens": "reasoning",
    "total_tokens": "total",
}


def usage_line(metrics):
    """'1,034 input, 7 output, 1,041 total' from a turn's metrics; '' when the turn had none."""
    parts = [f"{metrics[key]:,} {label}" for key, label in METRIC_LABELS.items() if metrics.get(key)]
    cost = metrics.get("total_cost_in_usd")
    if cost is not None:
        parts.append(f"${cost:.4f}")
    return ", ".join(parts)
