# Step 44 - Replay and trace viewer

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

## The code, piece by piece

### 1. Stamps and usage entries

`harness/session.py`:

```python
clock = time.time  # the stamp on every entry; a name the tests can replace
...
def stamped(entry):
    """The entry with `ts` added, as one JSON line. The dict passed in is not touched."""
    return json.dumps({**entry, "ts": round(clock(), 3)}) + NL


def save(messages, usage=None, seconds=None, cost=None):
...
    global WRITTEN
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
the dollars step 41 priced it at. The rewind, handoff and compaction
markers go through `stamped` too, so every line of the log has a time.

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

### 3. The loop records the call

`harness/agent.py`:

```python
        started = time.monotonic()  # the seconds of the call go in the log next to its usage
...
        messages.append(message.model_dump(exclude_none=True))
        cost = stop.record(usage)  # priced and added to the session's total
        session.save(messages, usage=usage, seconds=round(time.monotonic() - started, 3), cost=cost)  # the numbers go next to the message
```

The clock starts before `call_llm` and stops when the reply is
appended. The cost is computed once, saved, and then shown on the usage
line as before. A tool result, a steering message or a Stop block is
saved without numbers, because no model call produced it.

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
        if event.kind == "user":
            turns += 1
            if step and turns > 1:
                wait()
        pause = delay(previous, event, speed)
        if pause and not (step and event.kind == "user"):
            sleep(pause)
        draw(event, pending)
        previous = event
    for name, args in pending.values():
        ui.tool(name, args, "")
    return events
```

The pause before an event is the gap between its stamp and the
previous one, divided by `speed` and capped at `MAX_PAUSE`, five
seconds, so a session left open over lunch replays in minutes. An
event without a stamp waits nothing, which is every event of a log
from before this step. `draw` makes the same `ui` calls the live run
made: `ui.user`, `ui.agent`, `ui.tool`, `ui.usage`, `ui.handoff`. A
tool call is drawn when its result arrives, as it was the first time,
and the calls of a run that crashed before their results are drawn at
the end with an empty result. With `--step`, the replay waits for
enter before every user message after the first; `sleep` and `wait`
are parameters so the tests replace them.

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
the page and prints where it went with the totals.

## Run it

```bash
pip install -e .
harness
> list the files here, then write hello.txt with the word hello
> /sessions
```

Have a short chat, then end it with ctrl-d. The session id is the
file stem `/sessions` shows, such as `20260913-101500`. Replay it:

```bash
harness replay last
harness replay 20260913-101500 --speed 4
harness replay last --step
```

The screen redraws the chat: the prompt in green, a usage line per
model call with its cost, the tool panels with their results, the
reply. Between entries the replay waits what the run waited, up to
five seconds, divided by `--speed`. With `--step` it prints `enter for
the next turn>` before every prompt after the first. The summary table
at the end adds up the tokens and dollars of the whole session.

Write the trace:

```bash
harness trace last --html trace.html
```

prints `wrote trace.html · 3 model calls · 2 tool calls · $0.0061`.
Open the file in a browser. Each row is one model call: the number,
the time of day, the seconds it took, prompt, completion and cached
tokens, the cost, and the reply with its tool calls folded under it.
Click a tool call to open its result; the `expand all` button opens
every one. A screenshot from `computer` or `browse` sits under the
call that took it. The footer row is the total.

A log from a session before this step has no stamps and no usage
entries. It replays without pauses, and its trace shows dashes in the
number columns.

Run the offline tests from the repository root:

```bash
python run_tests.py 44
python check_snippets.py 44
```

## What to notice

- The messages on disk are still the messages. The stamp is added on
  the way out and removed on the way in, and the usage sits in a line
  of its own. `load()` returns the same list it returned in step 43,
  and a log from an earlier step still loads.
- The log is append-only, as it has been since step 8. Recording more
  did not mean rewriting anything: two new kinds of line, and a key on
  every line.
- One reader, two views. `timeline()` is the only code that parses
  the log for these commands. `replay` draws its events; `trace`
  groups them. A third viewer would read the same list.
- Replay does not fold. `load()` applies a rewind; `timeline()`
  reports it. A replay shows the turn that was taken back and the
  trace counts its calls, because they happened and were paid for.
- Replay reuses the `ui`. No second renderer: the same `ui.tool`,
  `ui.agent` and `ui.usage` the live loop calls draw the replay, so
  the two look alike and stay alike.
- The duration is measured, not derived. `seconds` is the clock
  around `call_llm`, saved next to the usage. The gap between stamps
  is for the replay's pace; it includes the tool calls and the time
  the user spent typing.
- The page trusts nothing. Every string passes through `escape`, and
  an image is inlined only when it is a base64 PNG or JPEG. A tool
  result that contains `</pre><script>` shows those characters.
- The page needs nothing. Inline styles, one inline function, no
  fetch. It opens from a file, from a mail attachment, from a bug
  report, years later.

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
entry; `rewind_to`, `handoff` and `compacted` stamp their markers;
`load` drops `ts` and skips usage entries), `agent.py` (the call is
timed, `stop.record` runs before `session.save` and the numbers go to
it; the `replay` and `trace` subcommands), `pyproject.toml` (version
0.44.0). Everything else, `capstone/` and `.agents/` included, is
unchanged from step 43.
