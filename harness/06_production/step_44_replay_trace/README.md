# Step 44 - Replay and trace viewer

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Make a run inspectable**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 43 - Extensions](../step_43_extensions/README.md). Next: [Step 45 - The core loop in TypeScript](../step_45_typescript_core/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** the session log becomes a record of what
happened, not only of what the model was left with, and two commands
read it back. `session.save` stamps every entry it writes with `ts`,
the time it was written, and follows every assistant message with a
usage entry: the tokens of the model call that produced it, the
seconds it took and what it cost, keyed by the message's index. The
message itself is written as the model saw it, and `load()` drops the
stamps and skips the usage entries, so a resumed transcript is the
same list as before. `harness replay <id> [--speed N] [--step]` draws
a saved session again with the recorded pauses between entries, and
`harness trace <id> --html FILE` writes it as one standalone HTML page,
one row per model call, with tokens, cost and duration, the tool calls
folded under each reply, and the screenshots of step 24 inline.

## Files

```text
step_44_replay_trace/
├── .agents/                          project config the harness loads at start
│   ├── .gitignore                    ignores tool_log.txt written by the PostToolUse hook
│   ├── agents/                       one .md per agent definition: front matter + prompt
│   │   ├── coder.md                  writes, changes and tests code; hands off to reviewer
│   │   ├── planner.md                returns a numbered plan without changing anything
│   │   ├── reviewer.md               checks the diff against one plan step: PASS or FAIL
│   │   ├── router.md                 picks the specialist and hands the conversation off
│   │   └── worker.md                 executes one plan step with the edit tools
│   ├── extensions/                   project extension files, one apply(ctx) each
│   │   ├── git_tools.py              example: a git_diff_summary tool and a /status command
│   │   └── word_count.py             example: one paragraph of the system prompt
│   ├── skills/explain-code/SKILL.md  the stage 4 skill
│   ├── hooks.json                    hook config: which script runs on which event
│   ├── mcp.json                      MCP config: the echo server, started with the chat
│   ├── block_env_writes.py           example PreToolUse hook: refuse to write a .env file
│   ├── log_tool_use.py               example PostToolUse hook: append every tool name to a log
│   ├── mcp_echo_server.py            a tiny MCP server: two tools, stdio transport
│   └── require_tests.py              example Stop hook: a .py edit must be followed by pytest
├── capstone/                         the step 38 capstone, carried forward
│   ├── evals/                        one folder per check: task.md, check.py; _common.py shared
│   ├── reference/                    a hand-written todo API: app.py, test_app.py, README.md
│   ├── run.py                        one headless harness run on the brief, then the eval suite
│   ├── task.md                       the brief: a small todo API in an empty directory
│   ├── report.json                   the recorded run: model, timing, per-check results
│   ├── SCORECARD.md                  the recorded run as a table, 4/5
│   └── transcript.md                 the recorded run's transcript
├── evals/                            one folder per task: task.md, check.py or expect.txt, optional workspace/
├── harness/                          the Python harness
│   ├── __init__.py                   package marker
│   ├── agent.py                      the loop; every call timed and priced; replay/trace commands
│   ├── agents.py                     agent definitions as an extension; agent_<name> tools
│   ├── ask_user.py                   the ask_user tool: a question, numbered options, the answer
│   ├── browse.py                     the browse tool set, gated by active_schemas()
│   ├── browser.py                    browser tools: one Chromium page driven through Playwright
│   ├── budget.py                     the context budget: where the window goes, when to warn
│   ├── checkpoint.py                 workspace checkpoints: a copy of every file before an edit
│   ├── commands.py                   slash commands; /extensions; registry commands run here too
│   ├── compact.py                    the compaction agent; its note is kept
│   ├── computer.py                   computer use: the screen as a tool
│   ├── config.py                     settings; real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py                    the late injection block: <env>, <plan>, <jobs>, active agent
│   ├── durability.py                 parse_args, the loop detector and the crash-recovery scan
│   ├── evaluate.py                   the eval runner; run_suite can grade one workspace
│   ├── extensions.py                 the registry: tool, command, hook, prompt_section, agent
│   ├── handoff.py                    handoffs: the conversation moves to another agent definition
│   ├── history.py                    cap / strip / fit: the transcript small enough to send
│   ├── hooks.py                      hooks as an extension; run_hooks over registry and config files
│   ├── instructions.py               project instruction files (AGENTS.md) into the prompt
│   ├── jobs.py                       background jobs: shell commands that keep running
│   ├── llm.py                        the model call; prompt sections come from the registry
│   ├── mcp_client.py                 MCP as an extension; servers start with the chat
│   ├── memory.py                     persistent memory
│   ├── modes.py                      named permission policies, one layer above the rules
│   ├── permissions.py                which tool calls need a human; modes sit above the rules
│   ├── pipeline.py                   the plan, work, review pipeline behind /pipeline
│   ├── plan.py                       plan mode: read-only tools, propose, act after approval
│   ├── prompt.py                     the input line
│   ├── replay.py                     replay: the log drawn again at the speed it was written
│   ├── sandbox.py                    an OS sandbox for bash
│   ├── session.py                    JSONL log with ts stamps and usage entries; load() strips them
│   ├── skills.py                     skills as an extension: read_skill and the prompt section
│   ├── stop.py                       stop conditions: finish(summary) and the turn budgets
│   ├── streaming.py                  streaming tool output: lines reach the screen as they arrive
│   ├── subagent.py                   subagents: task tool, nested loop with a live panel
│   ├── todos.py                      the plan
│   ├── tools.py                      core tools; TOOLS and TOOL_SCHEMAS filled through extensions
│   ├── trace.py                      trace: the log as one HTML page, one row per model call
│   └── ui.py                         rich panels, live ToolStream panels for running tools
├── AGENTS.md                         project instructions read into the system prompt
├── test_step.py                      offline tests: fake clock, replay timeline, trace HTML
├── pyproject.toml                    package metadata; version 0.44.0
└── README.md                         this file
```

## Why a log needs a clock

Step 8 made the session a JSONL file, one message per line, appended
after every message so a crash loses nothing. That file answers one
question: what does the model see when the session is resumed. It
does not answer the questions a person asks after a run went wrong.
How long did the call before the bad edit take? Which reply cost the
most? What came back from the tool call the model then ignored? The
usage of each call was printed to the screen and lost; the time of
each entry was never recorded at all.

Two small additions to the log answer all of them. A stamp on every
entry gives the pace. A usage entry after every reply gives the
numbers. Neither touches the messages: the stamp is added on the way
to disk and removed on the way back, and the usage lives in an entry
of its own, so the message list the model reads is the same list as
in step 43. The log stays append-only, and a log written by an earlier
step still loads and still replays, without pauses and without
numbers.

Reading the log back needs one reader, not two. `replay.timeline`
turns the file into a list of events in file order, rewinds and
handoffs included, and both commands consume it. The replay draws the
events with the same `ui` calls the live run made. The trace groups
them into model calls and renders a page.

### What breaks without it

A run that cost $3 more than expected, or edited the wrong file at the
fourth call, leaves nothing to look at once the terminal is closed.
The transcript on disk has the messages but not their order in time,
and `/cost` shows one total. With this step the same `.jsonl` says
which call took 40 seconds, which one cost the most, and what the tool
result the model ignored actually contained - and `harness trace last
--html trace.html` puts that in a page you can attach to a bug report.

### The log format

One JSON object per line, in the order it was written. Every line has
`ts`, the wall-clock time it was written (seconds since the epoch,
three decimals).

| Line | Written by | Meaning |
|---|---|---|
| `{"role": "system" \| "user" \| "assistant" \| "tool", ..., "ts"}` | `session.save` | a message, exactly as the model saw it (`tool_calls`, `tool_call_id` and image `content` lists included) |
| `{"usage": {...}, "index": N, "seconds": S, "cost": C, "ts"}` | `session.save` after a reply | the model call that produced message `N`: its token counts (and `cost` when the API reported one, else `null`), the seconds the call took, and the dollars it was priced at |
| `{"rewind_to": N, "ts"}` | `/rewind`, `/undo` | the transcript was cut to `N` messages; the old lines stay in the file |
| `{"handoff": "name", "ts"}` | `handoff_to` | from here on `name` answers; `load()` rewrites the system prompt from that definition |
| `{"compacted": [...], "ts"}` | `/compact`, automatic compaction | the transcript was replaced by this list |

When things are stamped: the user message is saved the moment it is
appended, before the model is called; the reply and its usage entry
are saved together when the reply is complete; each tool result is
saved right after it is appended, which is after *all* the tool calls
of that reply have finished (they run in parallel, and are appended in
reply order). So the gap between the user line and the assistant line
is the model call, and the gap between the assistant line and its
first tool line is the longest tool call of that reply; the tool lines
of one reply carry near-identical stamps.

## The code, piece by piece

### 1. Stamps and usage entries

`harness/session.py`:

```python
clock = time.time  # the stamp on every entry; a name the tests can replace
...
def stamped(entry):
    """The entry with `ts` added, as one JSON line. The dict passed in is not touched."""
    return json.dumps({**entry, "ts": round(clock(), 3)}) + "\n"


def save(messages, usage=None, seconds=None, cost=None):
...
    global WRITTEN
    if not PERSIST:
        return
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        for message in messages[WRITTEN:]:
            f.write(stamped(message))
        if usage is not None:
            f.write(stamped({"usage": usage, "index": len(messages) - 1, "seconds": seconds, "cost": cost}))
    WRITTEN = len(messages)
```

`stamped` builds a new dict, so the message in memory never gains a
`ts` key. `save` takes three optional numbers with the messages. When
`usage` is given, one more line follows the new messages: the usage
dict as the client returned it, `index`, the position of the assistant
message it belongs to, `seconds`, how long the call took, and `cost`,
the dollars `stop.record` priced it at. The rewind, mode, handoff and
compaction markers go through `stamped` too, so every line of the log
has a time; `PERSIST` still says whether anything is written at all,
as since step 21.

### 2. Loading drops what the model does not read

`harness/session.py`:

```python
        entry.pop("ts", None)
        if "usage" in entry:
            continue  # the numbers of a model call: replay and trace read them, the model does not
        if "rewind_to" in entry:
            del messages[entry["rewind_to"]:]
```

Two lines in `load()`. The stamp comes off every entry, and a usage
entry is skipped before the marker checks. Everything after that is
step 40: rewinds cut, compactions replace, handoffs rewrite the prompt.
A resumed session sends the model exactly the list it sent before this
step, and the tests assert that equality.

A handoff marker makes that agent the active one, a global, and a mode
marker sets the mode. `all_sessions()`, which titles every log for
`/sessions`, and `replay.main`, which counts the messages, read the raw
lines through `raw_messages()` instead, so listing or replaying old
chats does not change which agent answers the live one or which mode it
is in. Only `open_session` - `/sessions` with a pick, `--resume` -
applies the markers, after a `handoff.reset()`.

### 3. The loop records the call

`harness/agent.py`:

```python
    messages.append({"role": "user", "content": user_input})
    session.save(messages)
...
        started = time.monotonic()  # the seconds of the call go in the log next to its usage
...
    messages.append(entry(message))
    cost = stop.record(usage)  # priced and added to the session's total
    session.save(messages, usage=usage, seconds=round(time.monotonic() - started, 3), cost=cost)  # the numbers go next to the message
```

The user message is saved the moment it is appended, so its stamp is
the time the prompt was sent. The clock starts before `call_llm` and
stops when the reply is appended. The cost is computed once, saved,
and then shown on the usage line as before. A tool result, a steering
message or a Stop block is saved without numbers, because no model
call produced it.

### 4. The timeline

`harness/replay.py`:

```python
@dataclass
class Event:
    """One entry of the log, ready to draw."""
    kind: str                   # user, assistant, tool, image, usage, rewind, handoff, compacted
    ts: float | None = None     # when the entry was written; None in a log from before this step
    data: dict = field(default_factory=dict)
...
def timeline(entries):
...
    events = []
    agent = "main"
    for entry in entries:
        ts = entry.get("ts")
        if "usage" in entry:
            events.append(Event("usage", ts, {k: v for k, v in entry.items() if k != "ts"}))
        elif "rewind_to" in entry:
            events.append(Event("rewind", ts, {"count": entry["rewind_to"]}))
        elif "handoff" in entry:
            events.append(Event("handoff", ts, {"previous": agent, "name": entry["handoff"]}))
            agent = entry["handoff"]
        elif "compacted" in entry:
            events.append(Event("compacted", ts, {"count": len(entry["compacted"])}))
        elif "role" in entry:
            message = {k: v for k, v in entry.items() if k != "ts"}
            role = message["role"]
            if role == "user" and isinstance(message.get("content"), list):
                events.append(Event("image", ts, {"caption": caption_of(message["content"]), "parts": message["content"]}))
            elif role in ("user", "assistant", "tool"):
                events.append(Event(role, ts, message))
    return events
```

`load()` folds the log into the model's view. `timeline()` does the
opposite: nothing is folded, and every line becomes one event in file
order. A rewind stays a rewind, so a replay shows the turn that was
taken back, and the trace counts its calls, because they were paid
for. A user message whose content is a list is a picture from step 24,
and becomes an `image` event with its caption. The system message has
no event: it is not drawn.

### 5. Replay at the recorded pace

`harness/replay.py`:

```python
def delay(previous, event, speed):
    """Seconds to wait before `event`: the recorded gap, scaled and capped. 0 without stamps."""
    if previous is None or event.ts is None or previous.ts is None or speed <= 0:
        return 0.0
    return min(max(event.ts - previous.ts, 0.0) / speed, MAX_PAUSE)
...
def replay(session_id, speed=1.0, step=False, sleep=time.sleep, wait=wait_for_enter):
...
    events = timeline(entries(session_id))
    pending = {}   # tool call id -> (name, args) of calls waiting for their result
    previous = None
    turns = 0
    for event in events:
        prompt_ = event.kind == "user" and not str(event.data.get("content") or "").startswith("Stop blocked:")  # a Stop hook's block is not a turn
        if prompt_:
            turns += 1
            if step and turns > 1:
                wait()
        pause = delay(previous, event, speed)
        if pause and not (step and prompt_):
            sleep(pause)
        draw(event, pending)
        previous = event
    for name, args in pending.values():
        ui.tool(name, args, "")
    return events
...
def parse_args(arguments):
    """The JSON arguments of a tool call as a dict; a broken string becomes {"raw": ...}."""
    try:
        args = json.loads(arguments or "{}")
    except (json.JSONDecodeError, TypeError):
        return {"raw": str(arguments)}
    return args if isinstance(args, dict) else {"raw": args}
```

The pause before an event is the gap between its stamp and the
previous one, divided by `speed` and capped at `MAX_PAUSE`, five
seconds, so a session left open over lunch replays in minutes. An
event without a stamp waits nothing, which is every event of a log
from before this step. `draw` makes the same `ui` calls the live run
made: `ui.user`, `ui.agent`, `ui.tool`, `ui.usage`, `ui.handoff`. A
tool call is drawn when its result arrives, as it was the first time,
and the calls of a run that crashed before their results are drawn at
the end with an empty result. A tool call whose arguments were not
JSON - the model does send those - is drawn with `{"raw": ...}`, never
parsed twice; `ui.replay`, which `--resume` and `/rewind` use, does the
same. With `--step`, the replay waits for enter before every user
message after the first, a `Stop blocked:` message from a Stop hook not
counted; a steering line typed after ctrl-c is a user message and does
count. `sleep` and `wait` are parameters so the tests replace them.

### 6. One row per model call

`harness/trace.py`:

```python
@dataclass
class Call:
    """One model call: the reply and everything it led to."""
    number: int
    turn: int                       # the user message this call answered
    ts: float | None = None
    content: str = ""
    tool_calls: list = field(default_factory=list)   # {"id", "name", "arguments", "result"}
    images: list = field(default_factory=list)       # (caption, data url)
    usage: dict = field(default_factory=dict)
    seconds: float | None = None
    cost: float | None = None
...
        elif event.kind == "tool" and data.get("tool_call_id") in by_id:
            by_id[data["tool_call_id"]]["result"] = str(data.get("content") or "")
...
        elif event.kind == "usage" and current is not None:
            current.usage = data.get("usage") or {}
            current.seconds = data.get("seconds")
            current.cost = data.get("cost")
            if current.cost is None and any(current.usage.get(k) for k in ("prompt_tokens", "completion_tokens", "cost")):
                current.cost = stop.cost_of(current.usage)[0]
```

`calls()` walks the events once. An assistant event opens a `Call`
with its tool calls and no results yet; the tool events that follow
fill in the results by id; an image event attaches its picture; the
usage event fills in the numbers. A log with usage entries but no
saved cost, from a run that had the tokens and not the price, is
priced with step 41's `cost_of`. The user prompts and the markers
become rows of their own between the calls.

Where the dollars come from: `stop.cost_of` uses the `cost` the API
reported when there is one - OpenRouter sends it when the request asks
(`llm.EXTRA_BODY`, on when `BASE_URL` contains `openrouter`), other
servers do not - and otherwise prices the tokens from `stop.PRICES`
(three `gpt-4.1` models) or `FALLBACK_PRICES` (1.00, 4.00 and 0.25
dollars per million prompt, completion and cached tokens, overridable
with `PRICE_PROMPT`, `PRICE_COMPLETION`, `PRICE_CACHED`). With the
default model on a server that reports no cost, every dollar figure in
the trace, in `/cost` and on the usage line is that estimate. `/cost`
says which (`stop.source()`).

### 7. The page

`harness/trace.py`:

```python
DATA_URL = re.compile(r"^data:image/(?:png|jpeg);base64,[A-Za-z0-9+/=\s]+$")  # the only images the page inlines
...
def escape(text):
    """Every string from the log passes through here before it reaches the page."""
    return html_.escape(str(text), quote=True)
...
    for tool_call in call.tool_calls:
        result = tool_call["result"]
        shown = "(no result recorded)" if result is None else (result[:RESULT_CHARS] + ("\n[... trimmed]" if len(result) > RESULT_CHARS else "")) or "(no output)"
        body.append(
            "<details>"
            f'<summary><span class="tool">{escape(tool_call["name"])}</span> <span class="args">{escape(tool_call["arguments"])}</span></summary>'
            f'<pre class="result">{escape(shown)}</pre>'
            "</details>"
        )
    for caption, url in call.images:
        body.append(f'<figure><img src="{escape(url)}" alt="{escape(caption)}"><figcaption>{escape(caption)}</figcaption></figure>')
```

The page is one file: a `<style>` block, a table, and a script of one
function that opens or closes every `<details>`. Nothing is fetched.
Each tool call is a `<details>` element, closed by default, with the
name and arguments in its summary and the result in a `<pre>`. Every
string from the log goes through `escape`, so a reply that contains
`<script>` shows the text `<script>` and runs nothing. An image is
inlined only when its URL matches `DATA_URL`, a base64 PNG or JPEG;
anything else in that slot is dropped. The last row adds up the calls:
seconds, tokens, dollars.

### 8. The commands

`harness/agent.py`:

```python
    play = commands_.add_parser("replay", help="draw a saved session again, at the pace it was recorded")
    play.add_argument("session", help="a session id from /sessions, or last")
    play.add_argument("--speed", type=float, default=1.0, metavar="N", help="replay N times faster (default 1)")
    play.add_argument("--step", action="store_true", help="wait for enter between turns")
    dump = commands_.add_parser("trace", help="write a saved session as one HTML page, one row per model call")
    dump.add_argument("session", help="a session id from /sessions, or last")
    dump.add_argument("--html", metavar="FILE", help="where to write the page (default: trace-<id>.html)")
...
        if cli.command == "replay":
            raise SystemExit(replay.main(cli))
        if cli.command == "trace":
            raise SystemExit(trace.main(cli))
```

Two subcommands next to step 30's `eval`. The session id is the file
stem `/sessions` lists, or `last` for the newest log. `replay.main`
prints the resumed line, draws the events, and ends with the summary
table of step 41, added up from the usage entries. `trace.main` writes
the page and prints where it went with the totals. A session id that
has no log ends with `no session <id> in <dir>` and exit code 1.

## Run it

Prerequisites: Python 3.10+, `API_KEY` (and `BASE_URL`, `MODEL` for a
server other than the default) in the environment or in
`~/.simple-harness/env`. The trace page needs nothing but a browser.

bash:

```bash
pip install -e .
harness
```

PowerShell:

```powershell
pip install -e .
harness
```

Have a short chat, then leave with `/exit`:

```text
> list the files here, then write hello.txt with the word hello
> /sessions
> /exit
```

The session id is the file stem `/sessions` shows, such as
`20260913-101500`. Replay it (the same commands in bash and
PowerShell):

```bash
harness replay last
harness replay 20260913-101500 --speed 4
harness replay last --step
```

The screen redraws the chat: the prompt in green, a usage line per
model call with its cost, the tool panels with their results, the
reply. Between entries the replay waits what the log recorded, up to
five seconds, divided by `--speed`: after the prompt, the model call;
after the reply, the tool calls; between two tool panels of one reply,
almost nothing. With `--step` it prints `enter for the next turn>`
before every prompt after the first. The summary table at the end adds
up the tokens and dollars of the whole session:

```text
  replay 20260913-101500 · 6 messages · 1 turns

  list the files here, then write hello.txt with the word hello

  2,104 prompt · 48 completion · 1,920 cached · $0.0013

  ┌ bash ls ────────────────────────────────────────────────────────────
  │  AGENTS.md
  │  harness
  │  ...
  └────────────────────────────────────────────────────────────────────

  ┌ write_file {"path": "hello.txt", "content": "hello"} ───────────────
  │  Wrote hello.txt
  └────────────────────────────────────────────────────────────────────

  agent

  Listed the directory and wrote hello.txt.

  2,231 prompt · 19 completion · 2,048 cached · $0.0009

  replayed 8 entries

  prompt tokens        4,335
  completion tokens    67
  cached tokens        3,968
  cost                 $0.0022
```

Write the trace:

```bash
harness trace last --html trace.html
```

prints `wrote trace.html · 2 model calls · 2 tool calls · $0.0022`.
Open the file in a browser. Each row is one model call: the number,
the time of day, the seconds it took, prompt, completion and cached
tokens, the cost, and the reply with its tool calls folded under it.
Click a tool call to open its result; the `expand all` button opens
every one. A screenshot the main agent took with `computer_screenshot`
sits under the call that took it. The footer row is the total.

A log from a session before this step has no stamps and no usage
entries. It replays without pauses, and its trace shows dashes in the
number columns.

Run the offline tests from the repository root:

```bash
python run_tests.py 44
python check_snippets.py 44
```

```powershell
python run_tests.py 44
python check_snippets.py 44
```

## Error handling

- **A tool call with broken arguments** (`{not json`, or a JSON array)
  gets the result `Error: the arguments of <name> are not a JSON object:
  ...` and never runs; an unknown tool name gets `Error: no tool named
  'x'.`; a tool that raises gets `Error: <ExceptionType>: <message>`;
  `bash` without a `command` gets `Blocked by policy: bash: missing
  argument 'command'`. Each is one tool message, so the log stays a
  valid transcript, the trace shows the call with its result under it,
  and the replay draws the broken arguments as `{"raw": "{not json"}`.
- **A failing command** comes back as its output and exit status in the
  result; a command that runs past 60 s is killed with its process
  group and the result starts `Timed out after 60s and was killed.
  Output so far:`.
- **Ctrl-C** during a model call or the tool calls reads a steering line;
  every call that had no result by then gets `INTERRUPTED` as its result
  first, so the log has one result per call. A second Ctrl-C within two
  seconds leaves the chat. In a replay, Ctrl-C stops the replay; the
  log is not touched.
- **A dead model call** (no network, a bad key, a 5xx that outlasts the
  four retries) prints `model call failed and will not be retried (...)`
  and ends the turn. The user message is in the log with its stamp and
  no usage entry follows it; the trace shows the prompt row with no call
  under it.
- **`harness replay` or `trace` on an id that does not exist** prints
  `no session <id> in <dir>` and exits 1; a half-written last line from
  a kill mid-save is skipped by `entries()`.
- **Leaving:** `/exit`, ctrl-d (ctrl-z then enter on Windows), or ctrl-c
  at the prompt. `harness --resume` opens the newest log; a run that
  died between a reply and its tool results has those calls run on
  resume, and their results are stamped then.

## Gotchas / What this is not

- **Only the main loop is in the log.** Subagent calls (`task`,
  `browse`, the `agent_*` tools), the compaction summariser and the
  eval judge call the model too; none of those calls has a line in the
  session log. The trace's totals and the replay's summary are the
  main loop's; `ui.summary()` at the end of a live session counts all
  of them, so the two differ on a session that used subagents. A
  screenshot a `browse` subagent took never reaches the log either.
- **The cost column is an estimate** unless the API reported a cost
  (OpenRouter does when asked; see section 6) or `PRICE_*` are set for
  your model. `/cost` names the source.
- **Timing is per reply, not per tool.** Tool results are appended
  after every call of the reply has finished, so the gap between the
  reply and its first tool line is the slowest call's time and the
  tool lines of one reply are stamped together. Replay draws a
  streamed reply at once, not token by token.
- **The log grows.** A `computer_screenshot` puts its PNG into the log
  as a base64 data URL every time; `history.strip` shrinks the copy in
  memory, not the file. `/sessions` parses every log in the directory
  to title it. Delete old logs from `~/.simple-harness/sessions/<project>/`
  when it gets slow.
- **`harness -p "..."` writes no log** unless `--resume` is given: a
  one-shot run prints its answer and leaves nothing to replay. With
  `--resume` it appends to the session it opened.
- **`--step` counts user messages**, which includes a steering line
  typed after ctrl-c (a `Stop blocked:` message is excluded).
- **Replay does not re-apply handoffs**, and `--resume` applies them
  from *today's* definition files: a definition that was renamed since
  is skipped without a note, and the resumed prompt is the current one.
- **This is not an observability stack.** One file per session, no
  server, no query language, no export beyond the HTML page. It is the
  smallest record that answers "what happened" after the terminal is
  gone.

## Diff from step 43

```bash
diff -r ../step_43_extensions/harness harness
```

Added: `replay.py` (`MAX_PAUSE`, `Event`, `entries`, `timeline`,
`delay`, `wait_for_enter`, `replay`, `draw`, `parse_args`, `resolve`,
`main`), `trace.py` (`DATA_URL`, `RESULT_CHARS`, `Call`, `Trace`,
`calls`, `escape`, `stamp`, `number`, `dollars`, `render_call`,
`render_row`, `totals`, `STYLE`, `SCRIPT`, `html`, `write`, `main`).
Changed: `session.py` (`clock`, `stamped`; `save(messages, usage=None,
seconds=None, cost=None)` stamps every line and writes the usage
entry; `rewind_to`, `mode`, `handoff` and `compacted` stamp their
markers; `load` drops `ts` and skips usage entries), `agent.py` (the call is
timed, `stop.record` runs before `session.save` and the numbers go to
it; the `replay` and `trace` subcommands), `pyproject.toml` (version
0.44.0). Everything else, `capstone/` and `.agents/` included, is
unchanged from step 43.

## What the next step adds

Step 45 ports the core of the loop - stage 15: tools, permissions,
todos, subagents, compaction, sessions - to TypeScript under
`harness-ts/`, and reads and writes this exact log format, so a
session started in one language resumes in the other.

<!-- harness-learning-check -->
## Check your understanding

Replay shows the same output twice. Were the underlying tools run twice?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

Not if the viewer only reads saved events. Distinguish replaying a record from executing a new task.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
