"""Step 27 - example PostToolUse hook: append every tool name to a log file.

Runs after each tool call. It prints nothing, so the real result stands.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

event = json.load(sys.stdin)
log = Path(event.get("cwd") or ".") / ".agents" / "tool_log.txt"
log.parent.mkdir(parents=True, exist_ok=True)
with log.open("a", encoding="utf-8") as f:
    f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {event.get('tool_name')}\n")
