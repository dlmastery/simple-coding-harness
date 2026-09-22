"""Step 40 - build_system_prompt takes the opening role as a parameter:
ROLE, the coding agent, by default, or an agent definition's body after a
handoff. Everything after the role - the tool guidance, the agent index,
the handoff targets, the deferred tools, the instruction files, the
skills - is the same for every agent, so a handed-off prompt is the main
prompt with a different first paragraph. The handoff targets come from
handoff.handoff_section() for the active agent.
The rest is step 36: the system prompt lists the agent definitions, one line each,
under the guidance on when to delegate to one. agents_section() builds the
list. The rest is step 35: the system prompt tells the model when to ask the user with
ask_user: when a requirement is ambiguous, and before a choice that
cannot be undone, never by guessing. The rest is step 34: call_llm retries.
A rate limit, a connection failure, a timeout, a 5xx answer or a
connection that drops mid-stream is tried again after a wait from BACKOFF,
up to MAX_TRIES times, with a note per retry. The client is made with
max_retries=0, so these are the only retries there are. The request and
the whole read of its stream sit inside the retry in stream_once(), so a
stream that breaks halfway starts over. retryable(error) draws the line: a
4xx is never retried. When the tries run out, call_llm returns a
StreamedMessage whose `failed` field carries the reason instead of
raising, so the loop can show it and go on. The rest is step 32:
build_system_prompt lists the deferred tools; PLAN_PROMPT and with_mode()
are step 28; call_llm streams.

The loop in agent.py appends `entry(message)` and reads `message.content` and
`message.tool_calls`. The StreamedMessage dataclass below keeps that exact
surface, so nothing downstream knows the reply was streamed.
"""

import json
import os
import time
from dataclasses import dataclass, field

import openai
from openai import OpenAI

try:
    import httpx2 as httpx_lib  # the http library the SDK ships with, as of openai 3.x
except ImportError:  # older SDKs use httpx itself
    import httpx as httpx_lib

from . import config
from . import plan
from .agents import agents_prompt
from .handoff import handoff_section
from .instructions import instructions_prompt
from .skills import skills_prompt
from .tools import TOOLS, active_schemas, deferred_names
from .ui import ui

client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY, max_retries=0)  # the retry policy is ours, below
MODEL = config.MODEL

# OpenRouter reports the price of a call when asked; other gateways ignore the field.
EXTRA_BODY = {"usage": {"include": True}} if "openrouter" in config.BASE_URL else {}

BACKOFF = (0.5, 1.0, 2.0, 4.0)  # seconds to wait before retry 1, 2, 3 and 4
MAX_TRIES = len(BACKOFF) + 1    # the first try plus one per wait
sleep = time.sleep              # a name the tests can replace

INSTRUCTIONS_INTRO = """
The project ships instruction files, shown below under one header per file.
They come from the user and from the maintainers of the code, and they
describe how this project is built, tested and laid out. Follow them. Where
one contradicts the guidance above, the instruction file wins, and where a
later file contradicts an earlier one, the later file is closer to the code
and wins.
"""


def instructions_section(cwd=None):
    """The instruction files with their introduction, or empty when there are none."""
    text = instructions_prompt(cwd)
    if not text:
        return ""
    return INSTRUCTIONS_INTRO + "\n" + text + "\n"


DEFERRED_INTRO = """
Some tools are deferred to keep the request small: they are offered with
their name and a one-line description only, and no parameters. Call
load_tool with the name before the first call to one of them; it returns the
full schema and the tool stays enabled for the rest of the session. The
deferred tools are:
"""


AGENTS_INTRO = """
Some subagents are defined by the project, one tool each, named agent_<name>.
Each one runs in its own context window with its own instructions and its
own tools, and returns only its final message. Like task, it cannot see this
conversation, so the request must stand alone. Use one when its description
fits the job better than doing it yourself: a plan from the planner, one
step of work from the worker, a check from the reviewer. The agents are:
"""


def agents_section():
    """The agent definitions with their introduction, or empty when there are none."""
    text = agents_prompt()
    if not text:
        return ""
    return AGENTS_INTRO + text + "\n"


def deferred_section(schemas=None):
    """The names of the deferred tools, one per line, or empty when there are none."""
    names = deferred_names(schemas)
    if not names:
        return ""
    return DEFERRED_INTRO + "\n".join(f"- {name}" for name in names) + "\n"


ROLE = """You are a coding agent. Your job is to code. Always code.
Use the bash tool to inspect files.
Use write_file to create files and str_replace to edit them.
Answer back to the user once exploration is done."""


def build_system_prompt(cwd=None, schemas=None, role=None, handoffs=None):
    """The system prompt for one working directory. Default: where the harness started.

    The instruction files are discovered here, every time, so the prompt is
    built after the discovery and a workspace gets the files that apply to it.
    The deferred tools are listed from schemas, the full registry by default,
    so the prompt is built after the MCP tools have joined it. `role` is the
    opening paragraph: ROLE by default, a definition's body after a handoff.
    `handoffs` is the handoff section: the active agent's by default.
    """
    cwd = cwd or os.getcwd()
    role = ROLE if role is None else role.strip()
    handoffs = handoff_section() if handoffs is None else handoffs
    return f"""
{role}

For any task that takes more than one step, call write_todos first and plan it
out. Send the whole list every time you call it - it replaces the old one.
Keep at most one task in_progress, mark it completed the moment it is finished,
and move the next one to in_progress in the same call. Skip the tool entirely
for single-step tasks; it is noise there.

The current list is injected back to you every turn inside <todos> tags, so
that block - not the transcript - is the truth about where you are.

When several tool calls do not depend on each other - reading three files,
running two greps - put them all in one reply. They run at the same time and
the results come back together, in order. A call that needs the result of
another one goes in the next reply.

When a task needs a web page - reading documentation, checking a page,
filling a form - call browse with the URL and the steps. It drives a real
browser in its own context window and returns a short report; page contents
never enter this conversation. It cannot see this conversation either, so
say exactly what to find or do. It never enters credentials.

When a task needs the desktop itself - an application window, a dialog, a
program without a command line - use the computer tools yourself. Call
computer_screen once, then computer_screenshot; the picture arrives in the
next message. Act with computer_act, then take a new screenshot to check
what happened. Never guess coordinates from memory: look first, act, look
again. Report what you see, and stop if the screen asks for a password.

You have a memory that lasts across sessions. The <memory> block in every
turn lists what is stored, one line per memory. Call remember for durable
facts: who the user is and how they like to work, how this project is built
and run, a correction the user made, a link or ticket worth keeping. Do not
store what the code or git history already records. Before asking the user
something you may already know, look at the <memory> block and call recall
on the matching entry. Call forget when a memory turns out to be wrong.

When you have several independent questions about the code, send them to
task as a list of descriptions. One subagent runs per item, all at the same
time, and the reports come back in one result with a section per question.
Questions that depend on each other go one at a time.

A command that keeps running - a dev server, a watcher, a long test run or
build - goes to bash_background, not bash. It returns a job id at once. The
<jobs> block lists the jobs that are still running. Read the output with
job_status, block on it with job_wait, and stop it with job_kill when you
are done with it. Every job is killed when the session ends.

When a requirement is ambiguous - two readings of the request lead to
different work - call ask_user with the question and, when there are a few
clear choices, the options. Never guess at a destructive choice: which
files to delete, which branch to reset, what to overwrite. Ask, then act on
the answer. Ask once and precisely; do not ask what the code or the
<memory> block already answers. The user may also send a message while you
work; it arrives as a user message after your tool results, and it takes
precedence over what you were doing.

Long tool output is cut short, and the whole thing is written to a temp file
whose path is given at the cut. Page through it with head, tail, sed -n or
grep rather than asking for it again. That file only exists for the current
turn, so read it now or re-run the command later.

When you need to understand how something works - where a feature lives, how
data flows, what calls what - send a task subagent instead of grepping your
way there yourself. It explores in its own context window and hands you back
just the findings, so the search does not fill yours. It cannot see this
conversation, so write the question so it stands alone. Do all editing
yourself; the subagent only reads.

Tools named mcp__<server>__<tool> come from MCP servers the user configured.
They run in another process; call them like any other tool and read the
result as text. If one returns Error:, say so and do not retry blindly.

The user may have configured hooks: small programs that run around tool
calls. A result that starts with "Blocked by hook:" means a hook refused the
call; read the reason, tell the user, and do not retry the same call. The
<hooks> block, when present, carries text a hook added for this turn.
{agents_section()}{handoffs}{deferred_section(schemas)}
Your current working directory is: {cwd}
{instructions_section(cwd)}
You have skills available. Each one is a set of instructions for a task.
If a skill matches what the user wants, call read_skill first and follow it.

{skills_prompt()}
"""


SYSTEM_PROMPT = build_system_prompt()

PLAN_PROMPT = """

You are in plan mode. The user wants a plan before any change is made.
Explore with bash, read_file, read_skill and task until you understand the
task, then call submit_plan once with a goal, the steps in order (each with
the files it touches and the actions taken on them) and the risks. Do not
propose steps you have not checked against the code. If the plan comes back
with feedback, address every point and submit again. Never claim a change
was made: nothing is written in plan mode.
"""


def with_mode(messages):
    """The messages to send: in plan mode the system prompt carries PLAN_PROMPT."""
    if plan.MODE != "plan" or not messages or messages[0].get("role") != "system":
        return messages
    first = dict(messages[0])
    first["content"] = first["content"] + PLAN_PROMPT
    return [first] + messages[1:]


def entry(message):
    """The transcript entry for a reply: role, content and tool_calls, nothing else.

    Providers attach extras (reasoning, annotations) that must not be sent
    back on the next call, so the whole message is never dumped as it is.
    """
    saved = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        saved["tool_calls"] = [call.model_dump(exclude_none=True) for call in message.tool_calls]
    return saved


@dataclass
class StreamedFunction:
    """The name and the JSON arguments of one tool call, built up from deltas."""

    name: str = ""
    arguments: str = ""


@dataclass
class StreamedToolCall:
    """One tool call. Same attributes as the SDK's ChatCompletionMessageToolCall."""

    id: str = ""
    type: str = "function"
    function: StreamedFunction = field(default_factory=StreamedFunction)

    def model_dump(self, exclude_none=True):
        """The dict entry() stores for this call: id, type and the function."""
        return {"id": self.id, "type": self.type, "function": {"name": self.function.name, "arguments": self.function.arguments}}


@dataclass
class StreamedMessage:
    """The assembled reply. Same surface as the SDK's ChatCompletionMessage."""

    content: str | None = None
    tool_calls: list[StreamedToolCall] | None = None
    role: str = "assistant"
    failed: str | None = None  # why no reply came, when every try failed; never part of the transcript

    def model_dump(self, exclude_none=True):
        """The same three keys entry() keeps - there is nothing else to drop."""
        return entry(self)


def usage_from(usage):
    """Token counts as a plain dict. Some proxies send no usage at all."""
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "reasoning_tokens": getattr(getattr(usage, "completion_tokens_details", None), "reasoning_tokens", None),
        "cached_tokens": getattr(getattr(usage, "prompt_tokens_details", None), "cached_tokens", None),
        "cost": getattr(usage, "cost", None),  # OpenRouter, in dollars; None everywhere else
    }


CUT_OFF = "(reply cut off by max_tokens)"

TRANSIENT_CODES = {408, 409, 429, 500, 502, 503, 504, 529}  # from an error event inside a stream


def retryable(error):
    """True when a failed request may succeed on a retry.

    Rate limits, connection failures, timeouts and a connection that drops
    while the stream is being read all pass. A status error passes only
    for a 5xx answer: a 4xx is the request's fault and comes back the same
    every time. An error the provider sends as an event inside the stream
    arrives as a plain APIError with a body; it passes when the body names
    a transient code or says the model is overloaded.
    """
    if isinstance(error, openai.RateLimitError):
        return True
    if isinstance(error, openai.APIConnectionError):  # APITimeoutError is a subclass
        return True
    if isinstance(error, openai.APIStatusError):
        return error.status_code >= 500
    if isinstance(error, httpx_lib.HTTPError):  # the SDK wraps the request, not the read of the stream
        return True
    if isinstance(error, openai.APIError):
        body = error.body if isinstance(error.body, dict) else {}
        code = body.get("code") or body.get("status")
        text = f"{body.get('message', '')} {error}".lower()
        return code in TRANSIENT_CODES or "overloaded" in text or "rate limit" in text
    return False


def describe(error):
    """A short name for a failed request: the class and its status, if any."""
    status = getattr(error, "status_code", None)
    name = type(error).__name__
    return f"{name} {status}" if status else name


def stream_once(request, on_delta=None):
    """One request, its stream read to the end. Returns (message, usage).

    A failure anywhere in here, from the first byte to the last, raises,
    and call_llm decides whether to try again.
    """
    stream = client.chat.completions.create(**request)

    parts = []           # text deltas, in order
    calls = {}           # tool call index -> StreamedToolCall
    final_usage = None   # arrives with the last chunk, which has no choices
    finish_reason = None

    for chunk in stream:
        if getattr(chunk, "error", None):  # a gateway can answer an error as a chunk: an APIError, so retryable() rates it
            raise openai.APIError(f"model call failed: {chunk.error}", None, body=chunk.error if isinstance(chunk.error, dict) else None)
        if getattr(chunk, "usage", None) is not None:
            final_usage = chunk.usage
        if not chunk.choices:
            continue
        choice = chunk.choices[0]
        finish_reason = getattr(choice, "finish_reason", None) or finish_reason
        delta = choice.delta
        if delta is None:
            continue

        if delta.content:
            parts.append(delta.content)
            if on_delta:
                on_delta(delta.content)

        for piece in delta.tool_calls or []:
            # fragments of one call share an index; a provider that sends none gets keyed by id
            key = piece.index if getattr(piece, "index", None) is not None else piece.id or len(calls)
            call = calls.setdefault(key, StreamedToolCall())
            if piece.id:
                call.id = piece.id
            function = getattr(piece, "function", None)
            if function is None:
                continue
            if function.name:
                call.function.name = function.name
            if function.arguments:
                call.function.arguments += function.arguments

    if finish_reason == "length" and calls:
        # the arguments stopped mid-JSON: no call is safe to run, say so instead
        calls = {}
        parts.append(f"\n{CUT_OFF}")
        if on_delta:
            on_delta(f"\n{CUT_OFF}")

    message = StreamedMessage(
        content="".join(parts) or None,
        tool_calls=[calls[key] for key in sorted(calls, key=str)] or None,
    )
    return message, usage_from(final_usage)


def call_llm(messages, tools=None, on_delta=None, on_restart=None):
    """One streamed request, retried on transient failures. Returns (message, usage).

    tools=None means the full registry with its deferred tools as stubs;
    tools=[] means no tools (the compaction agent). on_delta, if given, is
    called with every piece of text as it arrives; on_restart, if given, is
    called before a retry that follows a stream which had already produced
    text, so the caller can say that the part on screen is discarded.

    A rate limit, a connection failure, a timeout or a 5xx answer is tried
    again after a wait from BACKOFF, up to MAX_TRIES times in all, with a
    note per retry. The whole stream is inside the retry, so a connection
    that drops halfway through a reply starts the reply over. When every
    try fails, or the error is a 4xx that no retry can fix, the result is a
    message whose `failed` field carries the reason; the loop shows it and
    the session goes on.
    """
    request = {"model": MODEL, "messages": messages, "stream": True, "stream_options": {"include_usage": True}}
    if EXTRA_BODY:
        request["extra_body"] = EXTRA_BODY
    schemas = active_schemas() if tools is None else tools
    if schemas:
        request["tools"] = schemas

    for attempt in range(1, MAX_TRIES + 1):
        seen = []  # what this try streamed, so a retry can say it starts over

        def deltas(text):
            seen.append(text)
            if on_delta:
                on_delta(text)

        try:
            return stream_once(request, deltas)
        except (openai.APIError, httpx_lib.HTTPError) as error:
            if not retryable(error):
                reason = f"model call failed and will not be retried ({describe(error)}): {error}"
                break
            if attempt == MAX_TRIES:
                reason = f"model call failed {MAX_TRIES} times, giving up ({describe(error)}): {error}"
                break
            wait = BACKOFF[attempt - 1]
            ui.note(f"model call failed ({describe(error)}); retry {attempt} of {MAX_TRIES - 1} in {wait:g}s")
            if seen and on_restart:
                on_restart()  # the partial reply on screen is not the reply
            sleep(wait)

    return StreamedMessage(content=None, failed=reason), usage_from(None)


if __name__ == "__main__":
    user_input = input("Enter your prompt> ")

    print("\nAgent: ", end="", flush=True)
    message, usage = call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ], on_delta=lambda text: print(text, end="", flush=True))
    print("\n")

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        result = TOOLS[tool_call.function.name](**args)
        print("Tool: ", tool_call.function.name, args)
        print(result, "\n")

    print(entry(message))
    print(usage)
