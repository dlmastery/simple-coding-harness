"""Step 02 - the recorded demo: the harness as the host, in the terminal.

Runs the harness codelab's loop in print mode with the lemonade server
configured in .agents/mcp.json (stdio). The model calls the tool; the
harness draws the tool panel, then the MCP App's structuredContent as a
text card, then prints the answer. The harness's late-injection panels are
left out of the recording; everything else is verbatim.

    python demo.py
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
PROMPT = "Show me the lemonade stand dashboard for the last 5 days. Answer in one sentence."


def without_injections(text):
    """The harness's stderr minus its late-injection panels: one skip per panel, nothing else touched."""
    kept, skipping = [], False
    for line in text.splitlines():
        if "late injection" in line:
            skipping = True
        if not skipping and line.strip():
            kept.append(line.rstrip())
        if skipping and line.strip().startswith("└"):
            skipping = False
    return kept


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    env = {**os.environ, "MCP_ALLOW": "mcp__lemonade__*", "PYTHONIOENCODING": "utf-8"}
    print(f"$ MCP_ALLOW=mcp__lemonade__* python -m harness.agent -p \"{PROMPT}\"")
    result = subprocess.run([sys.executable, "-m", "harness.agent", "-p", PROMPT], cwd=HERE, env=env, capture_output=True, text=True, encoding="utf-8")
    print()
    for line in without_injections(result.stderr):
        print(line)
    print()
    print("answer:", result.stdout.strip())
    if result.returncode:
        print(f"(harness exited with {result.returncode})")


if __name__ == "__main__":
    main()
