"""Step 17 - the same harness on the OpenAI Agents SDK.

The Agents SDK gives you the loop (`Runner`), typed function tools, sessions
(`SQLiteSession`), human-in-the-loop approvals, guardrails, hooks and
agents-as-tools. It does *not* give you coding tools: bash, read, edit are
ours again, so the tool code from step 5 comes back unchanged and gets
wrapped instead of hand-registered.

Run:   python harness.py [--resume]
Needs: BASE_URL, API_KEY, MODEL - any OpenAI-compatible endpoint, as before.
"""

import argparse
import asyncio
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from typing_extensions import TypedDict  # pydantic needs this variant on Python < 3.12
from agents import Agent, ModelSettings, RunConfig, RunHooks, Runner, SQLiteSession, function_tool, set_tracing_disabled
from agents.run import CallModelData, ModelInputData
from agents.tool_guardrails import ToolGuardrailFunctionOutput, ToolInputGuardrailData, tool_input_guardrail

import rules

HOME = Path.home() / ".simple-harness"
DB = HOME / "openai_agents.sqlite"
set_tracing_disabled(True)  # tracing posts to OpenAI; off so any endpoint works


def model():
    """An OpenAI-compatible chat model. Built lazily so importing needs no key."""
    from openai import AsyncOpenAI
    from agents import OpenAIChatCompletionsModel

    client = AsyncOpenAI(
        base_url=os.environ.get("BASE_URL", "https://api.openai.com/v1"),
        api_key=os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY"),
    )
    return OpenAIChatCompletionsModel(model=os.environ.get("MODEL", "gpt-4.1-mini"), openai_client=client)


# --- step 4: skills, exactly as before -------------------------------------------

SKILL_DIRS = [Path.cwd() / ".agents" / "skills", Path.home() / ".agents" / "skills"]


def find_skills():
    skills = {}
    for directory in SKILL_DIRS:
        for path in sorted(directory.glob("*/SKILL.md")):
            text = path.read_text(encoding="utf-8")
            if text.startswith("---"):
                _, front, _ = text.split("---", 2)
                meta = yaml.safe_load(front) or {}
                if "name" in meta:
                    skills.setdefault(meta["name"], {"description": " ".join(str(meta.get("description", "")).split()), "path": path})
    return skills


SKILLS = find_skills()

# --- step 5: the tool implementations are plain functions ----------------------


async def _bash(command: str) -> str:
    """Run a shell command and return its stdout and stderr.

    Args:
        command: The command to run.
    """
    # async so the SDK can enforce `timeout=` on it (sync handlers cannot be timed out)
    result = await asyncio.to_thread(subprocess.run, command, shell=True, capture_output=True, text=True)
    return (result.stdout + result.stderr) or "(no output)"


def _read_file(path: str) -> str:
    """Read a file and return its contents.

    Args:
        path: Path to the file.
    """
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write_file(path: str, content: str) -> str:
    """Create a file with the given content, overwriting it if it exists.

    Args:
        path: File to write.
        content: The full contents.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {path}"


def _str_replace(path: str, old_str: str, new_str: str, allow_multi: bool = False) -> str:
    """Replace exact text in a file. old_str must appear exactly once unless allow_multi.

    Args:
        path: File to edit.
        old_str: Exact text to find; include surrounding lines to make it unique.
        new_str: Text to put in its place.
        allow_multi: Replace every match instead of failing.
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()
    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str was not found in {path}. Read the file again and copy the text exactly."
    if count > 1 and not allow_multi:
        return f"Error: old_str matches {count} times in {path}. Add surrounding lines or set allow_multi."
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old_str, new_str))
    return f"Replaced {count} occurrence(s) in {path}"


def _read_skill(name: str) -> str:
    """Open a skill by name and return its full instructions.

    Args:
        name: Name of the skill.
    """
    if name not in SKILLS:
        return f"No skill named '{name}'. Available: {', '.join(SKILLS) or 'none'}."
    return SKILLS[name]["path"].read_text(encoding="utf-8")


class Todo(TypedDict):
    content: str
    active: str
    status: Literal["pending", "in_progress", "done"]


MARKS = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]"}
TODOS: list[Todo] = []


def _write_todos(todos: list[Todo]) -> str:
    """Replace the whole todo list. Send every item each time; keep exactly one in_progress.

    Args:
        todos: The complete plan.
    """
    if sum(1 for t in todos if t["status"] == "in_progress") > 1:
        return "Error: keep exactly one item in_progress."
    TODOS[:] = todos
    return todos_prompt() or "Todo list cleared."


def todos_prompt():
    return "\n".join(f"{MARKS[t['status']]} {t['content']}" for t in TODOS)


# --- step 11: policy = a guardrail (deny) + needs_approval (ask) ---------------


def verdict_for(tool_name, args):
    """(verdict, reason) for any of our tools, from the step 11 rules."""
    if tool_name == "bash":
        return rules.check_bash(args.get("command", ""))
    if tool_name in ("write_file", "str_replace"):
        return rules.check_edit(args.get("path", ""))
    return "allow", None


@tool_input_guardrail
def policy_gate(data: ToolInputGuardrailData):
    """Runs before the tool. A rejection becomes the tool's result - the model reads it."""
    raw = data.context.tool_arguments
    args = json.loads(raw) if isinstance(raw, str) and raw else (raw or {})
    verdict, reason = verdict_for(data.context.tool_name, args)
    if verdict == "deny":
        return ToolGuardrailFunctionOutput.reject_content(f"Blocked by policy: {reason}")
    return ToolGuardrailFunctionOutput.allow()


async def bash_needs_approval(ctx, params, call_id) -> bool:
    return rules.check_bash(params.get("command", ""))[0] == "ask"


async def edit_needs_approval(ctx, params, call_id) -> bool:
    return rules.check_edit(params.get("path", ""))[0] == "ask"


# --- step 2.2: registration is decoration ------------------------------------------
# timeout=60 with the default timeout_behavior turns a hang into a result.

bash = function_tool(_bash, name_override="bash", needs_approval=bash_needs_approval, tool_input_guardrails=[policy_gate], timeout=60)
read_file = function_tool(_read_file, name_override="read_file")
write_file = function_tool(_write_file, name_override="write_file", needs_approval=edit_needs_approval)
str_replace = function_tool(_str_replace, name_override="str_replace", needs_approval=edit_needs_approval)
read_skill = function_tool(_read_skill, name_override="read_skill")
write_todos = function_tool(_write_todos, name_override="write_todos")

# --- step 15: a subagent is an agent used as a tool -------------------------------

SUBAGENT_PROMPT = f"""You are an exploration subagent. Answer the one question you were given by
reading the codebase in {os.getcwd()}, then report in under 150 words: paths
with line numbers, names, values. You cannot edit anything. Say plainly what
you could not find."""

# Explicit empty ModelSettings: an Agent built without a model assumes the SDK
# default (GPT-5) and pre-fills verbosity/reasoning that other models reject.
explorer = Agent(name="explorer", instructions=SUBAGENT_PROMPT, tools=[bash, read_file, read_skill], model_settings=ModelSettings())
task = explorer.as_tool(
    tool_name="task",
    tool_description=(
        "Hand a self-contained exploration question to a fresh agent with its own "
        "context window and get back its findings. It cannot see this conversation; "
        "include every detail it needs. It reads and reports; it never edits."
    ),
    max_turns=12,
)

SYSTEM = f"""You are a coding agent. Use bash to explore, read_file before you edit,
write_file to create files and str_replace for targeted edits. For tasks with
several steps call write_todos first and keep exactly one item in_progress;
the current list is injected back to you inside <todos> tags every call. Use
the task tool to understand how something works instead of grepping your way
there. If a skill matches the request, call read_skill first and follow it.
Be concise. Working directory: {os.getcwd()}

Skills:
{chr(10).join(f'- {n}: {s["description"]}' for n, s in SKILLS.items()) or '(none)'}
"""


def build_agent(model_override=None):
    # The subagent runs its own nested Runner.run; without a model it would fall
    # back to the SDK default client, which only knows OPENAI_API_KEY.
    explorer.model = model_override
    return Agent(
        name="harness",
        instructions=SYSTEM,
        tools=[bash, read_file, write_file, str_replace, read_skill, write_todos, task],
        model=model_override,
    )


# --- steps 6, 7, 10, 14: shape every request without touching the session ----------

STUB = 300
KEEP_FULL = 3  # the newest tool outputs stay whole; older ones shrink to a stub
LABELS = {"M": "modified", "D": "deleted", "A": "added", "??": "new"}


def git(args):
    result = subprocess.run(f"git {args}", shell=True, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else ""


def git_state():
    state = {}
    for line in git("status --porcelain").splitlines():
        code, path = line[:2].strip(), line[3:].strip()
        p = Path(path)
        state[path] = (code, hashlib.md5(p.read_bytes()).hexdigest() if p.is_file() else None)
    return state


LAST = git_state()


def changes_note():
    global LAST
    now = git_state()
    changed = {p: v[0] for p, v in now.items() if LAST.get(p) != v}
    LAST = now
    if not changed:
        return ""
    lines = "\n".join(f"{LABELS.get(c, c)}: {p}" for p, c in changed.items())
    return f"\n<system-reminder>\nThese files changed since your last turn. Read them again before editing:\n{lines}\n</system-reminder>"


def reminder():
    branch = git("branch --show-current").strip() or "(no git)"
    env = f"<env>\ntime: {datetime.now():%Y-%m-%d %H:%M}\ngit branch: {branch}\n</env>"
    todos = f"\n<todos>\n{todos_prompt()}\n</todos>" if TODOS else ""
    return env + todos + changes_note()


def shape_request(data: CallModelData) -> ModelInputData:
    """call_model_input_filter: runs on every model call, sees a copy of the input.

    Two jobs from the hand-built harness, in one place:
      strip - older tool outputs shrink to a stub (step 14)
      inject - the late block goes on the end, and only on the wire (step 6)
    The session on disk is untouched; this is the request, not the record.
    """
    items = [dict(item) for item in data.model_data.input]
    outputs = [item for item in items if item.get("type") == "function_call_output"]
    for item in outputs[:-KEEP_FULL]:
        out = item.get("output")
        if isinstance(out, str) and len(out) > STUB:
            item["output"] = out[:STUB] + f"\n[output trimmed: {len(out) - STUB} more chars. Run the command again if you need them.]"
    # A system item, not a user message: when a run resumes after an approval
    # the reminder is the newest thing in the list, and as a user message the
    # model answers it instead of finishing the task it was approved for.
    items.append({"role": "system", "content": "Automated context, not a message from the user. Continue the current task.\n" + reminder()})
    return ModelInputData(input=items, instructions=data.model_data.instructions)


# --- step 3: presentation is a RunHooks subclass ------------------------------------


class Console(RunHooks):
    async def on_agent_start(self, context, agent):
        if agent.name == "explorer":
            print("      subagent · own context")

    async def on_tool_start(self, context, agent, tool):
        pad = "        " if agent.name == "explorer" else "  "
        args = getattr(context, "tool_arguments", None) or getattr(context, "tool_input", None)
        print(f"{pad}tool> {tool.name} {str(args or '')[:90]}")

    async def on_tool_end(self, context, agent, tool, result):
        pad = "        " if agent.name == "explorer" else "  "
        first = str(result).strip().splitlines()[:3]
        print(pad + "      " + (" / ".join(first)[:120] or "(no output)"))

    async def on_llm_end(self, context, agent, response):
        u = getattr(response, "usage", None)
        if u:
            print(f"  {u.input_tokens:,} in · {u.output_tokens:,} out")


# --- step 8: sessions are SQLite rows; rewind pops them ---------------------------


def last_session_id():
    if not DB.exists():
        return None
    try:
        with sqlite3.connect(DB) as db:
            row = db.execute("SELECT session_id FROM agent_sessions ORDER BY updated_at DESC LIMIT 1").fetchone()
        return row[0] if row else None
    except sqlite3.Error:
        return None


def all_session_ids():
    if not DB.exists():
        return []
    try:
        with sqlite3.connect(DB) as db:
            return [r[0] for r in db.execute("SELECT session_id FROM agent_sessions ORDER BY updated_at DESC")]
    except sqlite3.Error:
        return []


async def rewind(session):
    """Pop items until a user message goes: one whole turn undone."""
    popped = 0
    while True:
        item = await session.pop_item()
        if item is None:
            break
        popped += 1
        if item.get("role") == "user":
            break
    return popped


def confirm(reason) -> bool:
    try:
        return input(f"\n  {reason}\n  allow? (y/n)> ").strip().lower().startswith("y")
    except (EOFError, KeyboardInterrupt):
        return False


async def turn(agent, session, text, hooks, config):
    """One user message. Approvals pause the run; we answer and resume it."""
    result = await Runner.run(agent, text, session=session, hooks=hooks, run_config=config, max_turns=40)
    while result.interruptions:
        state = result.to_state()
        for item in result.interruptions:
            if await asyncio.to_thread(confirm, f"{item.name} {item.arguments}"):
                state.approve(item)
            else:
                state.reject(item, rejection_message="The user declined this tool call.")
        result = await Runner.run(agent, state, session=session, hooks=hooks, run_config=config, max_turns=40)
    return result.final_output


async def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="harness-openai-agents")
    parser.add_argument("--resume", action="store_true", help="continue the most recent chat")
    cli = parser.parse_args()

    HOME.mkdir(parents=True, exist_ok=True)
    session_id = (last_session_id() if cli.resume else None) or datetime.now().strftime("%Y%m%d-%H%M%S")
    session = SQLiteSession(session_id, db_path=DB)
    agent = build_agent(model())
    hooks, config = Console(), RunConfig(call_model_input_filter=shape_request)

    print(f"\n  simple coding harness · openai agents sdk · session {session_id} · /sessions, /rewind, ctrl-d to exit")
    while True:
        try:
            text = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            break
        if text == "/sessions":
            for sid in all_session_ids():
                print(f"  {sid}")
            continue
        if text == "/rewind":
            print(f"  popped {await rewind(session)} items")
            continue
        answer = await turn(agent, session, text, hooks, config)
        if answer:
            print(f"\n  agent> {answer}")


if __name__ == "__main__":
    asyncio.run(main())
