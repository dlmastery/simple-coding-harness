"""Step 49 - Context, questions and stop conditions: the agent spec, the stream and the usage table.

`build_spec` puts four codelab mechanisms into one TrueForge agent spec:
compaction with an explicit trigger (stage 14), large tool response
offloading (step 32), an iteration limit (steps 34 and 41) and the
`ask_user_question` tool (step 35). `stream_turn` reads one turn, merges
the deltas into their `model.message` and collects what the turn left
pending. `usage_table` draws the per-call token breakdown as a table.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from trueforge_sdk import SessionAgentSpecBody, TrueForge
from trueforge_sdk.types import (
    AgentSpec,
    AskUserQuestionsConfig,
    CompactionConfig,
    ContextManagementConfig,
    InputTokensCompactionTrigger,
    LargeToolResponseConfig,
    Model,
    RuntimeConfig,
)

BASE_URL = "http://localhost:8790"
MODEL = "openai/gpt-4-1-mini"

COMPACT_AT = 20_000     # input tokens that trigger compaction (stage 14's threshold)
ITERATION_LIMIT = 8     # model calls one turn may make (step 34's MAX_CALLS, step 41's budget)

# the five parts of `input_tokens_breakdown`, in the order the table shows them
CATEGORIES = ("harness", "skills", "instructions", "tool_definitions", "messages")
BAR = 30  # width of the longest bar under the table


def connect(base_url: str = BASE_URL, timeout: int = 600) -> TrueForge:
    """A client for the TrueForge server. Loads the system trust store when it is installed."""
    try:
        import truststore

        truststore.inject_into_ssl()
    except ImportError:
        pass
    return TrueForge(base_url=base_url, timeout=timeout)


def build_spec(instructions: str, model: str = MODEL,
               compact_at: int = COMPACT_AT, iteration_limit: int = ITERATION_LIMIT) -> AgentSpec:
    """An inline agent spec with compaction, offloading, an iteration limit and questions."""
    return AgentSpec(
        model=Model(name=model),
        instructions=instructions,
        config=RuntimeConfig(
            context_management=ContextManagementConfig(
                compaction=CompactionConfig(
                    enabled=True,
                    trigger=InputTokensCompactionTrigger(type="input_tokens", value=compact_at),
                ),
                large_tool_response=LargeToolResponseConfig(enabled=True),
            ),
            iteration_limit=iteration_limit,
            ask_user_questions=AskUserQuestionsConfig(enabled=True),
        ),
    )


def describe_spec(spec: AgentSpec) -> str:
    """One line per configured limit, for the demo banner."""
    config = spec.config
    trigger = config.context_management.compaction.trigger
    return "\n".join([
        f"compaction        at {trigger.value:,} input tokens",
        f"large tool output offloaded to a file: {config.context_management.large_tool_response.enabled}",
        f"iteration limit   {config.iteration_limit} model calls per turn",
        f"questions         ask_user_question enabled: {config.ask_user_questions.enabled}",
    ])


def open_session(client: TrueForge, spec: AgentSpec) -> str:
    """Create a session on an inline spec and return its id."""
    return client.sessions.create(agent=SessionAgentSpecBody(spec=spec)).data.id


@dataclass
class Turn:
    """What one streamed turn produced."""

    turn_id: str | None = None
    events: dict[str, dict] = field(default_factory=dict)   # id -> merged non-delta event
    messages: list[dict] = field(default_factory=list)      # the model.message events, in order
    pending: list[dict] = field(default_factory=list)       # tool.response_required events
    state: dict = field(default_factory=dict)               # turn.done state

    @property
    def text(self) -> str:
        """The text of the last model message."""
        return (self.messages[-1].get("content") or "") if self.messages else ""

    @property
    def metrics(self) -> dict:
        return self.state.get("metrics") or {}


def merge(base: dict, delta: dict) -> None:
    """Fold one `model.message.delta` into its base message, in place.

    Text appends. Tool-call fragments merge by `index`: the first fragment
    carries the id and the name, the rest append to `arguments`. The final
    delta carries `finish_reason` and `usage`.
    """
    if delta.get("content"):
        base["content"] = (base.get("content") or "") + delta["content"]
    for fragment in delta.get("tool_calls") or []:
        calls = base.setdefault("tool_calls", [])
        while len(calls) <= fragment["index"]:
            calls.append({"id": None, "type": "function", "function": {"name": "", "arguments": ""}})
        call = calls[fragment["index"]]
        if fragment.get("id"):
            call["id"] = fragment["id"]
        if fragment.get("tool_info"):
            call["tool_info"] = fragment["tool_info"]
        function = fragment.get("function") or {}
        if function.get("name"):
            call["function"]["name"] = function["name"]
        call["function"]["arguments"] += function.get("arguments") or ""
    for key in ("finish_reason", "usage"):
        if delta.get(key) is not None:
            base[key] = delta[key]


def stream_turn(client: TrueForge, session_id: str, input_items: list, on_delta=None) -> Turn:
    """Stream one turn and return it merged: messages, pending questions, final state."""
    turn = Turn()
    stream = client.sessions.create_turn_stream(session_id=session_id, input=input_items)
    for event in stream.with_metadata():
        data = event.data.model_dump(exclude_none=True)
        kind = data["type"]
        if kind == "turn.created":
            turn.turn_id = data.get("turn_id")
        elif kind == "model.message":
            turn.events[data["id"]] = data
            turn.messages.append(data)
        elif kind == "model.message.delta":
            base = turn.events.get(data["id"])
            if base is not None:
                merge(base, data)
            if on_delta and data.get("content"):
                on_delta(data["content"])
        elif kind == "tool.response_required":
            turn.events[data["id"]] = data
            turn.pending.append(data)
        elif kind == "turn.done":
            turn.state = data["state"]
        else:
            turn.events[data["id"]] = data
    return turn


def usage_table(messages: list[dict]) -> str:
    """The `input_tokens_breakdown` of every model call as a table, plus a bar per category.

    One row per call. The last row sums the calls. Under the table, the
    five categories of the summed input with one bar each: step 32's
    `/context` chart, drawn from what the server reports.
    """
    rows = [message["usage"] for message in messages if message.get("usage")]
    if not rows:
        return "no usage reported"
    head = f"{'call':<5}" + "".join(f"{c:>17}" for c in CATEGORIES) + f"{'input':>9}{'output':>8}"
    lines = [head, "-" * len(head)]
    total = {c: 0 for c in CATEGORIES} | {"input_tokens": 0, "output_tokens": 0}
    for number, usage in enumerate(rows, 1):
        breakdown = usage.get("input_tokens_breakdown") or {}
        for category in CATEGORIES:
            total[category] += breakdown.get(category, 0)
        total["input_tokens"] += usage.get("input_tokens", 0)
        total["output_tokens"] += usage.get("output_tokens", 0)
        lines.append(_row(str(number), breakdown, usage))
    lines.append(_row("all", total, total))
    largest = max(total[c] for c in CATEGORIES) or 1
    lines.append("")
    for category in CATEGORIES:
        bar = "#" * round(BAR * total[category] / largest)
        lines.append(f"{category:<18} {total[category]:>8,}  {bar}".rstrip())
    return "\n".join(lines)


def _row(label: str, breakdown: dict, usage: dict) -> str:
    cells = "".join(f"{breakdown.get(c, 0):>17,}" for c in CATEGORIES)
    return f"{label:<5}{cells}{usage.get('input_tokens', 0):>9,}{usage.get('output_tokens', 0):>8,}"


def metrics_line(metrics: dict) -> str:
    """The turn's totals from `turn.done` `state.metrics` as one line."""
    if not metrics:
        return "metrics: none"
    return (f"metrics: {metrics.get('total_input_tokens', 0):,} in, "
            f"{metrics.get('total_output_tokens', 0):,} out, "
            f"{metrics.get('total_tokens', 0):,} total")


def status_line(state: dict) -> str:
    """How the turn ended. An iteration limit ends it with status `error` and a message."""
    status = state.get("status") or "unknown"
    if status == "done":
        return "status: done"
    detail = state.get("message") or state.get("reason") or ""
    return f"status: {status} - {detail}".rstrip(" -")


def arguments_of(call: dict) -> dict:
    """The parsed JSON arguments of a merged tool call, or an empty dict."""
    try:
        return json.loads(call.get("function", {}).get("arguments") or "{}")
    except json.JSONDecodeError:
        return {}
