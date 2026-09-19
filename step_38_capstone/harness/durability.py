"""Step 34 - the loop detector and the crash-recovery scan.

LoopDetector watches the tool calls of consecutive replies and flags a call
that repeats with the same name and the same arguments REPEAT_LIMIT times
in a row. unanswered(messages) finds the tool calls at the end of a
transcript that never got a result, which is what a crash between a model
reply and its tool results leaves behind. The retry of a failed model call
lives in llm.py, next to the call it protects. Nothing here talks to the
model or runs a tool.
"""

import json

REPEAT_LIMIT = 3
REPEATED = "Repeated call detected; change approach or ask the user"


def parse_args(tool_call, why=False):
    """The arguments of a tool call as a dict; an empty dict when the JSON is broken.

    With `why`, returns (args, problem): the problem is None when the
    arguments are a JSON object, else one line that says what is wrong.
    Works on the SDK's tool-call objects and on the dicts of a transcript.
    """
    function = tool_call["function"] if isinstance(tool_call, dict) else tool_call.function
    raw = function["arguments"] if isinstance(function, dict) else function.arguments
    try:
        args = json.loads(raw or "{}")
    except json.JSONDecodeError as broken:
        return ({}, str(broken)) if why else {}
    if not isinstance(args, dict):
        return ({}, f"got {type(args).__name__}, not an object") if why else {}
    return (args, None) if why else args


def signature(tool_call):
    """What makes two calls the same: the name and the canonical JSON of the arguments."""
    return (tool_call.function.name, json.dumps(parse_args(tool_call), sort_keys=True))


class LoopDetector:
    """Counts how many replies in a row have carried each (name, arguments) pair."""

    def __init__(self, limit=REPEAT_LIMIT):
        self.limit = limit
        self.streaks = {}  # signature -> replies in a row that carried it

    def observe(self, tool_calls):
        """Record one reply. Returns one flag per call: True when it has repeated `limit` times."""
        keys = [signature(call) for call in tool_calls]
        self.streaks = {key: self.streaks.get(key, 0) + 1 for key in set(keys)}  # a pair not in this reply starts over
        return [self.streaks[key] >= self.limit for key in keys]


def unanswered(messages):
    """The tool calls of the last assistant message that have no result yet.

    Returns [] when the transcript ends in anything but that message and its
    tool results. The calls come back as StreamedToolCall objects, the same
    shape the loop hands to execute_all.
    """
    from .llm import StreamedFunction, StreamedToolCall  # here, not at the top: llm imports tools, tools imports this module

    index = len(messages) - 1
    while index >= 0 and messages[index].get("role") == "tool":
        index -= 1
    if index < 0 or messages[index].get("role") != "assistant":
        return []
    answered = {message.get("tool_call_id") for message in messages[index + 1:]}
    return [
        StreamedToolCall(id=call["id"], function=StreamedFunction(call["function"]["name"], call["function"]["arguments"]))
        for call in messages[index].get("tool_calls") or []
        if call["id"] not in answered
    ]
