"""Step 47 - the approval loop: stream a turn, answer its approval pauses, resume.

A gated tool call ends the turn with a `tool.approval_required` event. The
event names the call id and the `model.message` that made the call. The
loop keeps every event by id, merges the deltas into their base message,
reads the tool name and arguments from the merged message, asks on the
terminal, and starts the next turn with one `user.tool_approval` per call.
`a` allows a tool for the rest of the session, as in step 35.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Callable

from trueforge_sdk import (
    AgentSpec,
    ApprovalAllow,
    ApprovalDeny,
    AskUserQuestionsConfig,
    DynamicSubAgentsConfig,
    McpServer,
    Model,
    RuntimeConfig,
    SessionAgentSpecBody,
    UserMessage,
    UserToolApprovalEvent,
)

MODEL = os.environ.get("TRUEFORGE_MODEL", "openai/gpt-4-1-mini")
TOOLS_SERVER = "s47-tools"
MAX_ROUNDS = 20  # approval turns one chat() may run; a server that keeps re-pausing cannot loop forever
INSTRUCTIONS = (
    "You are a coding agent. Your only tools live on the s47-tools MCP server. "
    "Paths are relative to the project root. Read a file before you edit it, edit "
    "with str_replace, then report the change in one sentence."
)
PRELOAD_TOOLS = ["read_file", "str_replace"]


def agent_spec(
    model: str = MODEL,
    instructions: str = INSTRUCTIONS,
    preload_tools: list | None = None,
    iteration_limit: int = 12,
) -> SessionAgentSpecBody:
    """An inline agent with the tools server attached: two tools preloaded, the rest deferred, approvals at the default."""
    if preload_tools is None:
        preload_tools = PRELOAD_TOOLS
    tools = McpServer(name=TOOLS_SERVER, preload=False, preload_tools=preload_tools)
    spec = AgentSpec(
        model=Model(name=model),
        instructions=instructions,
        mcp_servers=[tools],
        config=RuntimeConfig(
            iteration_limit=iteration_limit,
            # both default to on; this client handles neither questions nor subagent threads
            ask_user_questions=AskUserQuestionsConfig(enabled=False),
            dynamic_sub_agents=DynamicSubAgentsConfig(enabled=False),
        ),
    )
    return SessionAgentSpecBody(spec=spec)


def merge_delta(message: dict, delta) -> None:
    """Fold one `model.message.delta` into its base message: append text, merge tool calls by index."""
    if delta.content:
        message["content"] = (message.get("content") or "") + delta.content
    for piece in delta.tool_calls or []:
        calls = message.setdefault("tool_calls", [])
        while len(calls) <= piece.index:
            calls.append({"id": None, "name": "", "arguments": ""})
        call = calls[piece.index]
        call["id"] = piece.id or call["id"]
        if piece.function:
            call["name"] += piece.function.name or ""
            call["arguments"] += piece.function.arguments or ""


def describe_call(call: dict) -> str:
    """One line for the prompt: the tool name and its arguments. `call_tool` shows the inner tool."""
    name, arguments = call["name"], call["arguments"]
    try:
        args = json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return f"{name} {arguments}"
    if name == "call_tool" and "tool_name" in args:
        inner = args.get("input", args.get("arguments", {}))
        return f"{args['tool_name']} {json.dumps(inner)}"
    return f"{name} {json.dumps(args)}"


@dataclass
class TurnResult:
    """What one streamed turn produced."""

    text: str = ""
    pending: list = field(default_factory=list)
    metrics: dict | None = None
    status: str = "incomplete"  # only turn.done sets it; a dropped stream stays incomplete


def run_turn(client, session_id: str, inputs: list, events: dict, out: Callable = print) -> TurnResult:
    """Stream one turn. Print text as it arrives and every tool response; collect approval pauses."""
    result = TurnResult()
    printing = False
    for event in client.sessions.create_turn_stream(session_id=session_id, input=inputs):
        if event.type == "model.message":
            events[event.id] = {"content": event.content or "", "tool_calls": []}
        elif event.type == "model.message.delta":
            if event.id in events:
                merge_delta(events[event.id], event)
            if event.content:
                out(event.content, end="", flush=True)
                printing = True
        elif event.type == "tool.response":
            if printing:
                out()
                printing = False
            out(f"  [tool.response] {event.content.strip()[:200]}")
        elif event.type == "tool.approval_required":
            result.pending.append(event)
        elif event.type == "turn.done":
            if printing:
                out()
            result.status = event.state.status
            if event.state.status == "done":
                output = event.state.output
                result.text = (output.content if output and isinstance(output.content, str) else "") or ""
                result.metrics = event.state.metrics.model_dump(exclude_none=True) if event.state.metrics else None
    return result


class Approver:
    """Terminal approvals: y allows once, n denies, a allows the tool for the rest of the session."""

    def __init__(self, ask: Callable = input):
        self.ask = ask
        self.always: set = set()

    def decide(self, label: str):
        name = label.split(" ", 1)[0]
        if name in self.always:
            print(f"  allow? {label} -> always")
            return ApprovalAllow()
        while True:
            try:
                answer = self.ask(f"  allow? {label} (y/n/a=always)> ").strip().lower()
            except (EOFError, KeyboardInterrupt):  # stdin closed or ctrl-c: never allow by accident
                print()
                return ApprovalDeny(reason="The user gave no answer.")
            if answer in ("y", "yes"):
                return ApprovalAllow()
            if answer in ("a", "always"):
                self.always.add(name)
                return ApprovalAllow()
            if answer in ("n", "no"):
                return ApprovalDeny(reason="The user denied this tool call.")


def approvals_for(pending: list, events: dict, approver: Approver) -> list:
    """Turn the pending approval events into `user.tool_approval` inputs, one decision per call."""
    inputs = []
    for event in pending:
        for ref in event.tool_calls:
            message = events.get(ref.source_event_id, {})
            call = next((c for c in message.get("tool_calls", []) if c["id"] == ref.id), None)
            label = describe_call(call) if call else ref.id
            inputs.append(
                UserToolApprovalEvent(thread_id=event.thread_id, tool_call_id=ref.id, approval=approver.decide(label))
            )
    return inputs


def chat(client, session_id: str, prompt: str, approver: Approver | None = None, out: Callable = print) -> TurnResult:
    """One user message, then as many approval rounds as the agent needs. Metrics are summed over the turns.

    A pause is only answered when the turn ended in `done`: an `error` or
    `cancelled` turn that streamed an approval event is reported, not resumed.
    """
    approver = approver or Approver()
    events: dict = {}
    totals: dict = {}
    inputs = [UserMessage(content=prompt)]
    for _round in range(MAX_ROUNDS):
        result = run_turn(client, session_id, inputs, events, out)
        for key, value in (result.metrics or {}).items():
            totals[key] = totals.get(key, 0) + value
        if result.status != "done" or not result.pending:
            result.metrics = totals or None
            return result
        inputs = approvals_for(result.pending, events, approver)
    result.status = "approval-loop"  # MAX_ROUNDS pauses in one chat: something keeps re-asking
    result.metrics = totals or None
    return result
