"""The harness codelab's loop, spoken in AG-UI.

harness/ is a verbatim copy of step 21 of the harness codelab: call_llm
streams the reply through an on_delta callback and assembles tool calls;
tools.execute runs one tool through the permission layer. This module
re-runs that loop as an event generator:

    RUN_STARTED, STATE_SNAPSHOT {"todos": [...]}
    repeat, at most MAX_CALLS times:
        TEXT_MESSAGE_START/CONTENT/END       one CONTENT per on_delta call
        TOOL_CALL_START/ARGS/END             per assembled tool call
        TOOL_CALL_RESULT                     after tools.execute, an "Error: ..." text if it failed
        CUSTOM permission                    when the rules said "ask"
        STATE_DELTA replace /todos           after write_todos
    RUN_FINISHED with token usage            (or RUN_ERROR: the model call failed, or the cap)

Nothing in harness/ changes. The harness thinks it is printing to a
terminal; the bridge catches the callbacks and turns them into events.
While the model is silent the generator yields KEEPALIVE, an SSE comment
the server writes raw, so a proxy does not drop the quiet stream.
"""

import copy
import json
import queue
import threading
from uuid import uuid4

import llm  # noqa: F401 - settings first: harness/config.py reads the environment on import
from ag_ui.core import (
    CustomEvent,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StateDeltaEvent,
    StateSnapshotEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    TokenUsage,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)
from harness import history, todos
from harness.context import reminder
from harness.llm import MODEL, SYSTEM_PROMPT, call_llm
from harness.tools import TOOLS, execute
from harness.ui import ui

MAX_CALLS = 40  # model calls in one run, the harness's own cap: past that the model is looping, not working
KEEPALIVE = ": keepalive\n\n"  # an SSE comment; server.py writes it raw, clients ignore it
KEEPALIVE_AFTER = 15  # seconds of model silence before one is sent

ASKED = []  # permission questions the harness raised during the current tool call (one user per process)


def approve_for_the_page(reason):
    """Stands in for ui.approve: the browser has no prompt, so record and allow."""
    ASKED.append(reason)
    return True


ui.approve = approve_for_the_page


def to_openai(messages):
    """AG-UI messages to model messages, with the harness system prompt in front."""
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


def streamed(messages):
    """call_llm as a generator: ("delta", text) while it streams, then ("message", (message, usage)).

    call_llm blocks and reports text through a callback. A worker thread runs
    it and pushes every callback onto a queue; this generator drains the queue.
    """
    items = queue.Queue()

    def worker():
        try:
            result = call_llm(messages, on_delta=lambda text: items.put(("delta", text)))
            items.put(("message", result))
        except Exception as error:  # noqa: BLE001 - re-raised on the generator side
            items.put(("error", error))

    threading.Thread(target=worker, daemon=True).start()
    while True:
        try:
            kind, payload = items.get(timeout=KEEPALIVE_AFTER)
        except queue.Empty:
            yield "keepalive", None  # the model is thinking; say so on the wire
            continue
        if kind == "error":
            raise payload
        yield kind, payload
        if kind == "message":
            return


def run_tool(tool_call):
    """tools.execute with every failure as a result: the page gets one TOOL_CALL_RESULT per call."""
    name = tool_call.function.name
    if name not in TOOLS:
        return f"Error: no tool named {name!r}."
    try:
        _, result = execute(tool_call)
    except json.JSONDecodeError as error:
        return f"Error: the arguments of {name} are not a JSON object: {error}"
    except Exception as error:  # noqa: BLE001 - the tool failed; the model reads why and goes on
        return f"Error: {type(error).__name__}: {error}"
    if not isinstance(result, str):
        result = "(no output)" if result is None else json.dumps(result, default=str)
    return result


def token_usage(usage):
    return TokenUsage(
        model=MODEL, input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"),
        reasoning_tokens=usage.get("reasoning_tokens"), cached_input_tokens=usage.get("cached_tokens"),
    )


def run(input: RunAgentInput):
    """Yield the events of one harness turn."""
    yield RunStartedEvent(thread_id=input.thread_id, run_id=input.run_id)
    yield StateSnapshotEvent(snapshot={"todos": copy.deepcopy(todos.TODOS)})
    messages = to_openai(input.messages)
    usage = {}
    try:
        for calls in range(MAX_CALLS + 1):
            if calls == MAX_CALLS:
                raise RuntimeError(f"stopped after {MAX_CALLS} model calls in one run")
            message_id, started = str(uuid4()), False
            for kind, payload in streamed(messages + [reminder()]):
                if kind == "keepalive":
                    yield KEEPALIVE
                elif kind == "delta":
                    if not started:
                        yield TextMessageStartEvent(message_id=message_id, role="assistant")
                        started = True
                    yield TextMessageContentEvent(message_id=message_id, delta=payload)
                else:
                    message, usage = payload
            if started:
                yield TextMessageEndEvent(message_id=message_id)
            messages.append(message.model_dump(exclude_none=True))
            if not message.tool_calls:
                break

            for tool_call in message.tool_calls:
                # the parent is the text message, when there was one
                yield ToolCallStartEvent(tool_call_id=tool_call.id, tool_call_name=tool_call.function.name, parent_message_id=message_id if started else None)
                yield ToolCallArgsEvent(tool_call_id=tool_call.id, delta=tool_call.function.arguments)
                yield ToolCallEndEvent(tool_call_id=tool_call.id)

                ASKED.clear()
                result = run_tool(tool_call)
                for reason in ASKED:
                    yield CustomEvent(name="permission", value={"reason": reason, "decision": "allow"})
                yield ToolCallResultEvent(message_id=str(uuid4()), tool_call_id=tool_call.id, content=result, role="tool")
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
                if tool_call.function.name == "write_todos":
                    yield StateDeltaEvent(delta=[{"op": "replace", "path": "/todos", "value": copy.deepcopy(todos.TODOS)}])
    except Exception as error:  # noqa: BLE001 - the client must see a terminal event
        yield RunErrorEvent(message=str(error))
        return
    finally:
        history.sweep()  # the turn is over: bin the temp files long tool output spilled into
    yield RunFinishedEvent(thread_id=input.thread_id, run_id=input.run_id, usage=[token_usage(usage)])
