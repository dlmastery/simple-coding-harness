"""Step 16 - the same harness on the Claude Agent SDK.

Everything steps 1-15 built by hand is built in here: the loop, Bash / Read /
Write / Edit / Glob / Grep, TodoWrite, the Task subagent tool, skills,
sessions, compaction, file-change reminders. The SDK is Claude Code as a
library. What is left for us to write is policy and presentation: which
calls to allow, what to inject, how to draw it.

Run:   python harness.py [--resume]
Needs: the `claude` CLI installed and logged in, or ANTHROPIC_API_KEY.
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import warnings
from datetime import datetime

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    CanUseToolShadowedWarning,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    create_sdk_mcp_server,
    list_sessions,
    tool,
)

import rules

# The SDK warns that tools in allowed_tools never reach can_use_tool. That is
# the point: read-only tools are pre-approved, everything else is gated.
warnings.filterwarnings("ignore", category=CanUseToolShadowedWarning)

# --- step 3/6/11: the prompt. The claude_code preset already carries the ----
# --- operating rules for its built-in tools; we only append ours.        ----

APPEND = """
For any task with more than one step, write a TodoWrite plan first and keep
exactly one item in progress. When you need to understand how something
works, delegate to the "explorer" subagent via the Task tool instead of
grepping your way there yourself; it reads and reports, you edit.
Run the tests with the run_tests tool after you change code.
"""

SUBAGENT_PROMPT = """You are an exploration subagent. Answer the one question you were given
by reading the codebase, then report in under 150 words: paths with line
numbers, names, values. Do not edit anything. Say plainly what you could not
find."""

# --- step 15: a subagent is a definition, not a loop --------------------------

EXPLORER = AgentDefinition(
    description="Explores the codebase and reports findings. Use for 'where is X' and 'how does Y work'.",
    prompt=SUBAGENT_PROMPT,
    tools=["Read", "Grep", "Glob", "Bash"],  # withheld: Write, Edit, Task, TodoWrite
    model="haiku",
    maxTurns=12,
)

# --- step 2.2: one custom tool, registered as an in-process MCP server ----------


def run_tests_impl(path: str = ".") -> str:
    """Run pytest on a path and return the last 30 lines of output."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", path],
            capture_output=True, text=True, timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "Timed out after 300s and was killed."
    lines = (result.stdout + result.stderr).strip().splitlines()
    return "\n".join(lines[-30:]) or "(no output)"


@tool("run_tests", "Run the project's pytest suite and return the last 30 lines.", {"path": str})
async def run_tests(args):
    return {"content": [{"type": "text", "text": run_tests_impl(args.get("path", "."))}]}


SERVER = create_sdk_mcp_server(name="harness", version="1.0.0", tools=[run_tests])

# --- step 11: policy, still two layers ----------------------------------------
#   1. a PreToolUse hook denies structurally - it runs before any permission
#      prompt and its answer cannot be overridden at the prompt
#   2. can_use_tool decides allow / ask for everything the hook let through


async def deny_dangerous(input_data, tool_use_id, context):
    command = input_data.get("tool_input", {}).get("command", "")
    if rules.decide(command) == "deny":
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Blocked by policy: {command}",
            }
        }
    return {}


def confirm(reason) -> bool:
    try:
        return input(f"\n  {reason}\n  allow? (y/n)> ").strip().lower().startswith("y")
    except (EOFError, KeyboardInterrupt):
        return False


async def can_use_tool(tool_name, tool_input, context):
    if tool_name == "Bash":
        verdict, reason = rules.check_bash(tool_input.get("command", ""))
    elif tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        verdict, reason = rules.check_edit(tool_input.get("file_path", ""))
    else:
        verdict, reason = "allow", None

    if verdict == "deny":
        return PermissionResultDeny(message=f"Blocked by policy: {reason}")
    if verdict == "ask" and not await asyncio.to_thread(confirm, reason):
        return PermissionResultDeny(message="The user declined this tool call.")
    return PermissionResultAllow()


# --- step 6: late injection is a UserPromptSubmit hook ------------------------
# Claude Code already injects its own <system-reminder> blocks for changed
# files (step 7) and the todo list (step 10). This adds our <env> block.


def git(args):
    result = subprocess.run(f"git {args}", shell=True, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else ""


def env_block():
    branch = git("branch --show-current").strip() or "(no git)"
    return f"<env>\ntime: {datetime.now():%Y-%m-%d %H:%M}\ngit branch: {branch}\n</env>"


async def env_context(input_data, tool_use_id, context):
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": env_block()}}


async def on_compact(input_data, tool_use_id, context):
    print(f"\n  compacting ({input_data.get('trigger')})")
    return {}


# --- the whole configuration ---------------------------------------------------


def build_options(resume=None):
    options = ClaudeAgentOptions(
        system_prompt={"type": "preset", "preset": "claude_code", "append": APPEND},
        cwd=os.getcwd(),
        setting_sources=["project"],  # step 4: loads .claude/skills/*/SKILL.md
        skills="all",
        mcp_servers={"harness": SERVER},
        # pre-approved: read-only built-ins, the plan, the subagent, our tool
        allowed_tools=["Read", "Glob", "Grep", "TodoWrite", "Task", "Skill", "mcp__harness__run_tests"],
        can_use_tool=can_use_tool,
        hooks={
            "PreToolUse": [HookMatcher(matcher="Bash", hooks=[deny_dangerous])],
            "UserPromptSubmit": [HookMatcher(hooks=[env_context])],
            "PreCompact": [HookMatcher(hooks=[on_compact])],
        },
        agents={"explorer": EXPLORER},
        resume=resume,
    )
    if sys.platform != "win32":  # step 11: the OS sandbox is one flag here
        options.sandbox = {"enabled": True}
    return options


# --- presentation ----------------------------------------------------------------


def compact(value, limit=90):
    text = value if isinstance(value, str) else json.dumps(value)
    return text if len(text) <= limit else text[:limit] + "…"


def show(message):
    """Render one SDK message. Subagent traffic is indented."""
    if isinstance(message, AssistantMessage):
        pad = "        " if message.parent_tool_use_id else "  "
        for block in message.content:
            if isinstance(block, TextBlock) and block.text.strip():
                print(f"{pad}agent> {block.text.strip()}")
            elif isinstance(block, ToolUseBlock):
                print(f"{pad}tool> {block.name} {compact(block.input)}")
    elif isinstance(message, UserMessage) and isinstance(message.content, list):
        for block in message.content:
            if isinstance(block, ToolResultBlock):
                content = block.content
                if isinstance(content, list):
                    content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
                print(f"      {compact(str(content or '(no output)'))}")
    elif isinstance(message, ResultMessage):
        usage = message.usage or {}
        cost = message.total_cost_usd or 0
        print(
            f"\n  {usage.get('input_tokens', 0):,} in · {usage.get('output_tokens', 0):,} out"
            f" · {usage.get('cache_read_input_tokens', 0):,} cached · ${cost:.4f} · session {message.session_id}"
        )


def sessions_here():
    return list_sessions(directory=os.getcwd(), limit=20)


async def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="harness-claude")
    parser.add_argument("--resume", action="store_true", help="continue the most recent chat")
    cli = parser.parse_args()

    resume = None
    if cli.resume:
        recent = sessions_here()
        if recent:
            resume = recent[0].session_id
            print(f"  resuming {resume}")

    print("\n  simple coding harness · claude agent sdk · /sessions, /resume <id>, /compact, ctrl-d to exit")
    while True:  # reconnect loop: /resume swaps the session underneath
        async with ClaudeSDKClient(options=build_options(resume)) as client:
            while True:
                try:
                    text = input("\n> ").strip()
                except (EOFError, KeyboardInterrupt):
                    return
                if not text:
                    return
                if text == "/sessions":
                    for s in sessions_here():
                        print(f"  {s.session_id}  {(s.summary or '')[:60]}")
                    continue
                if text.startswith("/resume "):
                    resume = text.split(maxsplit=1)[1]
                    break  # leave the client; the outer loop reconnects with resume=
                # /compact and other built-in slash commands go straight through
                await client.query(text)
                async for message in client.receive_response():
                    show(message)


if __name__ == "__main__":
    asyncio.run(main())
