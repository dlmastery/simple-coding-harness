"""Server-sent events, the reading side, in Python. The page does the same in
sse.mjs; the tests and demo.py use this copy.

One event is one or more `data:` lines followed by a blank line. AG-UI puts
the whole JSON event on a single data line.
"""

import json


def parse_sse(text):
    """Split raw SSE text into the JSON objects it carries, in order."""
    events = []
    for block in text.replace("\r\n", "\n").split("\n\n"):  # the spec allows either line ending
        data = [line[5:].lstrip() for line in block.splitlines() if line.startswith("data:")]
        if data:
            events.append(json.loads("\n".join(data)))
    return events
