"""The agent as an event generator. run() takes one RunAgentInput and yields
AG-UI events in the order the protocol requires:

    RUN_STARTED
    TEXT_MESSAGE_START
    TEXT_MESSAGE_CONTENT  (one per model delta)
    TEXT_MESSAGE_END
    RUN_FINISHED          (or RUN_ERROR)

The generator knows nothing about HTTP. server.py encodes each event and
streams it; the tests iterate it directly.
"""

from uuid import uuid4

from ag_ui.core import (
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)

from llm import stream_text

SYSTEM_PROMPT = "You are a concise assistant for a lemonade stand. Answer in plain text."


def to_openai(messages):
    """AG-UI messages carry an id and camelCase keys; the model wants role and content."""
    return [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m.role, "content": m.content} for m in messages if m.role in ("user", "assistant", "system")
    ]


def run(input: RunAgentInput):
    """Yield the events of one run. A model failure becomes RUN_ERROR, not a broken stream."""
    yield RunStartedEvent(thread_id=input.thread_id, run_id=input.run_id)
    message_id = str(uuid4())
    try:
        yield TextMessageStartEvent(message_id=message_id, role="assistant")
        for delta in stream_text(to_openai(input.messages)):
            yield TextMessageContentEvent(message_id=message_id, delta=delta)
        yield TextMessageEndEvent(message_id=message_id)
    except Exception as error:  # noqa: BLE001 - the client must see a terminal event
        yield RunErrorEvent(message=str(error))
        return
    yield RunFinishedEvent(thread_id=input.thread_id, run_id=input.run_id)
