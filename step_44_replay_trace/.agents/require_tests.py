"""Step 41 - example Stop hook: a turn that edited a .py file must run pytest after the last edit.

The harness sends the Stop event as JSON on stdin: `answer` (the final
text or the finish summary), `calls` (every tool call of the turn, each
with tool_name, tool_input and tool_result) and `blocks` (how many times
a Stop hook already sent the agent back this turn). Exit 2 blocks the
stop, and stderr becomes the user message the agent reads. Exit 0 lets
the turn end.
"""

import json
import sys

event = json.load(sys.stdin)
calls = event.get("calls") or []

last_edit = None  # (index in calls, path) of the newest edit to a .py file
for index, call in enumerate(calls):
    path = str((call.get("tool_input") or {}).get("path") or "")
    if call.get("tool_name") in ("write_file", "str_replace") and path.endswith(".py"):
        last_edit = (index, path)

if last_edit is not None:
    index, path = last_edit
    tested = any(
        call.get("tool_name") == "bash" and "pytest" in str((call.get("tool_input") or {}).get("command") or "")
        for call in calls[index + 1:]
    )
    if not tested:
        print(f"tests were not run after editing {path}; run pytest, then answer", file=sys.stderr)
        sys.exit(2)
