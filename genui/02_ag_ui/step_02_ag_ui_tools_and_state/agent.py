"""The agent as an event generator, now with tools and state.

    RUN_STARTED
    STATE_SNAPSHOT                          the state this run starts from
    repeat until the model stops calling tools (at most MAX_TURNS times):
        TEXT_MESSAGE_START/CONTENT/END      if the model wrote text
        TOOL_CALL_START/ARGS/END            one group per tool call
        STATE_DELTA + TOOL_CALL_RESULT      for each server tool
    RUN_FINISHED                            (or RUN_ERROR)

A tool that fails, an unknown tool, arguments that are not JSON: the error
text is the TOOL_CALL_RESULT, so the model can try again; only the model
call itself failing, or the turn cap, ends the run with RUN_ERROR.

A tool the client declared in RunAgentInput.tools is a client tool. The
server streams the call and ends the run; the page executes it and sends
the result as a tool message on the next run.
"""

import copy
from uuid import uuid4

from ag_ui.core import (
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StateDeltaEvent,
    StateSnapshotEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)

from json_patch import apply_patch
from llm import stream_chat
from tools import TOOL_SCHEMAS, execute, initial_state

MAX_TURNS = 8  # model calls per run: a model that keeps calling tools must not run up the bill

SYSTEM_PROMPT = """You run the dashboard of a lemonade stand.
Build it with tools: show_metric once per metric, show_table once, show_chart once.
Invent plausible numbers. When the user wants to buy something, call confirm_purchase
first; call record_purchase only after the result says confirmed.
Text replies are one short sentence."""


def to_openai(messages):
    """AG-UI messages to model messages, tool calls and tool results included."""
    out = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in messages:
        if m.role == "tool":
            out.append({"role": "tool", "tool_call_id": m.tool_call_id, "content": m.content})
        elif m.role == "assistant":
            entry = {"role": "assistant", "content": m.content or None}
            if m.tool_calls:
                entry["tool_calls"] = [
                    {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                    for c in m.tool_calls
                ]
            out.append(entry)
        elif m.role in ("user", "system"):
            out.append({"role": m.role, "content": m.content})
    return out


def client_schemas(tools):
    """The tools the page offers, in the model's function-calling shape."""
    return [
        {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters or {}}}
        for t in tools
    ]


def run(input: RunAgentInput):
    """Yield the events of one run."""
    yield RunStartedEvent(thread_id=input.thread_id, run_id=input.run_id)
    state = copy.deepcopy(input.state) if input.state else initial_state()
    yield StateSnapshotEvent(snapshot=state)

    client_tools = {t.name for t in input.tools}
    schemas = TOOL_SCHEMAS + client_schemas(input.tools)
    messages = to_openai(input.messages)
    try:
        for turn in range(MAX_TURNS + 1):
            if turn == MAX_TURNS:
                raise RuntimeError(f"stopped after {MAX_TURNS} tool rounds")
            message_id = str(uuid4())
            text, calls = [], {}  # call id -> {"name", "arguments"}
            text_open = False     # a text message is streaming; it ends before the first tool call
            for piece in stream_chat(messages, schemas):
                if piece[0] == "text":
                    if not text:
                        yield TextMessageStartEvent(message_id=message_id, role="assistant")
                        text_open = True
                    text.append(piece[1])
                    yield TextMessageContentEvent(message_id=message_id, delta=piece[1])
                elif piece[0] == "tool_start":
                    if text_open:  # older clients refuse tool events inside an open text message
                        yield TextMessageEndEvent(message_id=message_id)
                        text_open = False
                    calls[piece[1]] = {"name": piece[2], "arguments": ""}
                    yield ToolCallStartEvent(tool_call_id=piece[1], tool_call_name=piece[2], parent_message_id=message_id)
                elif piece[0] == "tool_args":
                    calls[piece[1]]["arguments"] += piece[2]
                    yield ToolCallArgsEvent(tool_call_id=piece[1], delta=piece[2])
                elif piece[0] == "tool_end":
                    yield ToolCallEndEvent(tool_call_id=piece[1])
            if text_open:
                yield TextMessageEndEvent(message_id=message_id)

            reply = {"role": "assistant", "content": "".join(text) or None}
            if calls:
                reply["tool_calls"] = [{"id": i, "type": "function", "function": c} for i, c in calls.items()]
            messages.append(reply)
            if not calls:
                break

            waiting_on_client = False
            for call_id, call in calls.items():
                if call["name"] in client_tools:
                    waiting_on_client = True  # the page runs it; its result opens the next run
                    continue
                result, operations = execute(call["name"], call["arguments"])
                if operations:
                    apply_patch(state, operations)
                    yield StateDeltaEvent(delta=operations)
                yield ToolCallResultEvent(message_id=str(uuid4()), tool_call_id=call_id, content=result, role="tool")
                messages.append({"role": "tool", "tool_call_id": call_id, "content": result})
            if waiting_on_client:
                break
    except Exception as error:  # noqa: BLE001 - the client must see a terminal event
        yield RunErrorEvent(message=str(error))
        return
    yield RunFinishedEvent(thread_id=input.thread_id, run_id=input.run_id)
