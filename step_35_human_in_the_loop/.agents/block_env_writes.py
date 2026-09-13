"""Step 27 - example PreToolUse hook: refuse to write a .env file.

The harness sends the event as JSON on stdin. Exit 2 blocks the tool call
and stderr becomes the reason the model sees. Exit 0 lets it through.
"""

import json
import sys
from pathlib import PurePath

event = json.load(sys.stdin)
path = str((event.get("tool_input") or {}).get("path") or "")
name = PurePath(path).name

if name == ".env" or name.startswith(".env."):
    print(f"{name} holds secrets; edit it by hand, not through the agent", file=sys.stderr)
    sys.exit(2)
