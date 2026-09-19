"""Step 18 - the same harness on the Google Antigravity SDK.

`google-antigravity` ships the Antigravity agent runtime as a binary inside
the wheel and drives it from Python. Built-in coding tools, subagents,
compaction, sessions, skills, MCP - all in the runtime. We declare policy
(the rules table again), hooks, one subagent and two tools of our own.

Run:   python harness.py [--resume CONVERSATION_ID]
Needs: GEMINI_API_KEY (or Vertex credentials).
"""

import argparse
import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from google.antigravity import Agent, BuiltinTools, CapabilitiesConfig, LocalAgentConfig
from google.antigravity.hooks import on_compaction, post_tool_call, pre_tool_call_decide
from google.antigravity.hooks.policy import allow, ask_user, deny
from google.antigravity.types import (
    AntigravityConnectionError,
    AntigravityExecutionError,
    HookResult,
    RunCommandConfig,
    SessionContinuationMode,
    SubagentCapabilities,
    SubagentConfig,
    ToolCall,
    ToolResult,
)

import rules

HOME = Path.home() / ".simple-harness" / "antigravity"

# The runtime's own read-only set includes read_url_content. That is the
# network, which the stage 11 rules deny (curl, wget), so it is left out here
# for both the policy list and the subagent.
READ_ONLY = [t for t in BuiltinTools.read_only() if t is not BuiltinTools.READ_URL_CONTENT]

# --- reading tool calls -----------------------------------------------------------
# The runtime names the shell tool `run_command` (argument `CommandLine`) and
# the edit tools `edit_file` / `create_file`. For paths the connection layer
# fills ToolCall.canonical_path; the argument names are the fallback.


def arg(call: ToolCall, *names):
    args = call.args or {}
    for name in names:
        if name in args:
            return str(args[name])
    return ""


def command_of(call):
    return arg(call, "CommandLine", "command", "cmd")


def path_of(call):
    return call.canonical_path or arg(call, "path", "file_path", "TargetFile", "output_path")


# --- step 11: policy as data. `enforce()` compiles this into a decide hook. -------


def is_denied(call: ToolCall) -> bool:
    return rules.decide(command_of(call)) == "deny"


def needs_ask(call: ToolCall) -> bool:
    return rules.decide(command_of(call)) == "ask"


def is_plain(call: ToolCall) -> bool:
    return rules.decide(command_of(call)) == "allow"


def edit_outside(call: ToolCall) -> bool:
    return not rules.inside_project(path_of(call))


def edit_inside(call: ToolCall) -> bool:
    return rules.inside_project(path_of(call))


def prompt(call: ToolCall) -> bool:
    try:
        return input(f"\n  {call.name} {command_of(call) or path_of(call)}\n  allow? (y/n)> ").strip().lower().startswith("y")
    except (EOFError, KeyboardInterrupt):
        return False


async def confirm(call: ToolCall) -> bool:
    """The handler runs on the runtime's event loop; input() must not block it."""
    return await asyncio.to_thread(prompt, call)


def build_policies(handler=confirm):
    return [
        *[allow(t.value) for t in READ_ONLY],
        allow("ask_question"), allow("start_subagent"),
        # the shell: the strictest verdict of the compound command decides.
        # (enforce() sorts deny before ask before allow whatever the order here)
        deny("run_command", when=is_denied, name="denied by rules"),
        ask_user("run_command", handler=handler, when=needs_ask, name="ask by rules"),
        allow("run_command", when=is_plain, name="read-only command"),
        # edits: silent inside the project, a prompt outside it
        allow("edit_file", when=edit_inside), allow("create_file", when=edit_inside),
        ask_user("edit_file", handler=handler, when=edit_outside),
        ask_user("create_file", handler=handler, when=edit_outside),
        # no network, no images: the same lines the bash rules drew
        deny("search_web"), deny("read_url_content"), deny("generate_image"),
    ]


# --- hooks: a structural deny, an audit line, a compaction note ------------------


@pre_tool_call_decide
def block_dangerous(call: ToolCall) -> HookResult:
    """Second layer, independent of the policy list: a deny here is final."""
    if call.name == "run_command" and is_denied(call):
        return HookResult(allow=False, message=f"Blocked by policy: {command_of(call)}")
    return HookResult(allow=True)


@post_tool_call
def audit(result: ToolResult):
    body = result.error or result.result
    first = str(body or "(no output)").strip().splitlines()[:2]
    print(f"  tool> {result.name}  {' / '.join(first)[:110]}")


@on_compaction
def note_compaction(*args, **kwargs):
    print("  compacted: older context was summarised by the runtime")


# --- step 2.2: two tools of our own; the runtime derives schemas from the hints -----


def run_tests(path: str = ".") -> str:
    """Run the project's pytest suite on a path and return the last 30 lines."""
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", path],
                                capture_output=True, encoding="utf-8", errors="replace", timeout=300)
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 300s"
    lines = (result.stdout + result.stderr).strip().splitlines()
    return ("\n".join(lines[-30:]) or "(no output)") + f"\nexit code {result.returncode}"


TODOS: list[str] = []


def write_todos(todos: list[str]) -> str:
    """Replace the plan. One line per item, prefixed [ ] pending, [~] in progress, [x] done. Keep at most one [~]."""
    if not isinstance(todos, list) or not all(isinstance(t, str) for t in todos):
        return "Error: todos must be a list of strings"
    if sum(1 for t in todos if t.startswith("[~]")) > 1:
        return "Error: keep at most one item marked [~]."
    TODOS[:] = todos
    return "\n".join(TODOS) or "Todo list cleared."


# --- step 15: the subagent is a config object -------------------------------------

EXPLORER = SubagentConfig(
    name="explorer",
    description="Explores the codebase and reports findings. Use for 'where is X' and 'how does Y work'.",
    system_instructions=(
        "You are an exploration subagent. Answer the one question you were given by reading the "
        "codebase, then report in under 150 words: paths with line numbers, names, values. "
        "You cannot edit anything. Say plainly what you could not find."
    ),
    # withheld: edits, run_command, the network and start_subagent - so it cannot write, cannot fetch and cannot recurse
    capabilities=SubagentCapabilities(enabled_tools=list(READ_ONLY)),
)

SYSTEM = f"""You are a coding agent. Explore with the built-in file tools, read a file before
you edit it, and run the tests with run_tests after you change code. For tasks with
several steps call write_todos first and keep at most one item marked [~]; the
current list is repeated to you every turn. To understand how something works,
start the explorer subagent instead of searching yourself; it reads, you edit.
Be concise. Working directory: {Path.cwd()}"""


def build_config(resume=None, handler=confirm):
    return LocalAgentConfig(
        system_instructions=SYSTEM,
        tools=[run_tests, write_todos],
        policies=build_policies(handler),
        hooks=[block_dangerous, audit, note_compaction],
        capabilities=CapabilitiesConfig(
            enable_subagents=True,
            max_subagent_depth=1,
            allowed_subagents=["explorer"],
            run_command_config=RunCommandConfig(timeout_seconds=60, enable_sandbox=sys.platform != "win32"),
        ),
        subagents=[EXPLORER],
        skills_paths=[str(Path.cwd() / ".agents" / "skills")],  # step 4
        workspaces=[str(Path.cwd())],
        save_dir=str(HOME),                                     # step 8
        conversation_id=resume,
        session_continuation_mode=SessionContinuationMode.RESUME if resume else None,
    )


# --- step 6: the late block is prepended by the caller, not stored anywhere -------


def git(args):
    result = subprocess.run(f"git {args}", shell=True, capture_output=True, encoding="utf-8", errors="replace")
    return result.stdout if result.returncode == 0 else ""


def late_block():
    branch = git("branch --show-current").strip() or "(no git)"
    todos = ("\n<todos>\n" + "\n".join(TODOS) + "\n</todos>") if TODOS else ""
    return f"<env>\ntime: {datetime.now():%Y-%m-%d %H:%M}\ngit branch: {branch}\n</env>{todos}\n\n"


def usage_line(usage):
    """The stage 3 numbers from the runtime's UsageMetadata."""
    if not usage:
        return ""
    parts = [f"{usage.prompt_token_count or 0:,} in", f"{usage.candidates_token_count or 0:,} out"]
    if usage.cached_content_token_count:
        parts.append(f"{usage.cached_content_token_count:,} cached")
    if usage.thoughts_token_count:
        parts.append(f"{usage.thoughts_token_count:,} thinking")
    return " · ".join(parts)


async def turn(agent, text):
    """One prompt in, the streamed reply out. A runtime failure is one line, not a crash."""
    try:
        response = await agent.chat(late_block() + text)
        print("\n  agent> ", end="", flush=True)
        async for token in response:
            sys.stdout.write(str(token))
            sys.stdout.flush()
        print()
        print(f"  {usage_line(response.usage_metadata)}")
    except (AntigravityConnectionError, AntigravityExecutionError, RuntimeError) as failure:
        print(f"\n  error: {type(failure).__name__}: {failure}")


async def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="harness-antigravity")
    parser.add_argument("--resume", metavar="CONVERSATION_ID", help="continue a saved conversation")
    cli = parser.parse_args()
    HOME.mkdir(parents=True, exist_ok=True)

    async with Agent(build_config(cli.resume)) as agent:
        print("\n  simple coding harness · antigravity sdk")
        print("  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave")
        while True:
            try:
                text = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if text in ("/exit", "/quit"):
                break
            if not text:
                continue
            await turn(agent, text)
            # the runtime assigns the id with the first reply; this is what --resume takes
            print(f"  conversation {agent.conversation_id}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:  # ctrl-c mid-turn: leave without a traceback
        print("\n  interrupted")
