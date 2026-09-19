# Step 49 - Context, questions and stop conditions on TrueForge

**What this step adds:** four codelab mechanisms as fields of one TrueForge
agent spec, and the two client loops they need. Compaction with an explicit
trigger (stage 14), large tool responses offloaded to a file (step 32), an
iteration limit per turn (step 34's `MAX_CALLS`, step 41's budget) and the
`ask_user_question` tool (step 35's `ask_user`) all live in
`config`. The client answers questions through the `tool.response_required`
/ `user.tool_response` pair and draws step 32's `/context` chart from the
`input_tokens_breakdown` the server reports on every model call. The demo
exercises the question and the breakdown; the compaction trigger and the
offload are set in the spec but never fire in a two-turn run (see Gotchas).

Setup (the `npx` command, the WSL note for Windows) is in step 46's README.
This step needs nothing else: no MCP server, no skill, no sandbox.

## Why these four belong together, and what breaks in the question loop

Stages 14, 32, 34 and 35 and step 41 each added code to the loop: a
compaction pass, a spill file, a call counter, a question tool, a budget
check. Each one changed `agent.py`. On TrueForge the loop is the server's,
so the same four things are settings on the agent, not code in the client.
The client keeps two jobs the server cannot do for it: answer a question
that only a human can answer, and show the user what the context costs.

Both jobs come back as events. A question is a turn that ends paused with
`tool.response_required`. The cost is a `usage` block on every
`model.message`, with the input split into five named parts. The client
reads both from the same stream it already prints.

The question loop has the same trap as step 47's approval loop: a turn
can stream `tool.response_required` and then end in `error` (the iteration
limit is the usual way). Answering that question on the terminal and
POSTing the reply to a dead turn is wrong twice over. The loop here resumes
only a `done` turn, declines pending calls it cannot run, treats a closed
stdin as "(no answer given)", and stops after `MAX_ROUNDS` resumes.

## Quick demo

```text
$ python demo.py --answer 1
compaction        at 20,000 input tokens
large tool output offloaded to a file: True
iteration limit   8 model calls per turn
questions         ask_user_question enabled: True
session           01m2g5jj5wxmqbs9x6eqk1de10

> set up a project for me

? Which kind of project do you want to set up?
  1. python
  2. node
answer> 1
For a Python project, I would create these files:

1. README.md
2. requirements.txt
3. main.py
4. .gitignore

Would you like me to help you create these files or set up anything specific?

2 turn(s), 2 model call(s)
call           harness           skills     instructions tool_definitions         messages    input  output
-----------------------------------------------------------------------------------------------------------
1                1,288                0               67                0                0    1,091      33
2                1,288                0               67                0                0    1,131      50
all              2,576                0              134                0                0    2,222      83

harness               2,576  ##############################
skills                    0
instructions            134  ##
tool_definitions          0
messages                  0
metrics: 2,222 in, 83 out, 2,305 total
status: done
```

Without `--answer` the `answer>` prompt waits for the keyboard. The
`metrics` line adds up every turn of the run (two here), so it agrees
with the table's `all` row.

## Files

```text
step_49_trueforge_context/
├── client/           context, questions and stop conditions on TrueForge
│   ├── __init__.py   package marker
│   ├── context.py    build_spec, the turn stream with its status, the token breakdown table
│   └── questions.py  tool.response_required -> ask on the terminal -> resume, capped
├── demo.py           an agent that asks before it acts, then the usage table
├── test_step.py      offline tests: a fake server streams a question, then a reply, or an error
└── README.md         this file
```

## The code, piece by piece

### 1. The spec

`client/context.py`:

```python
COMPACT_AT = 20_000     # input tokens that trigger compaction (stage 14's threshold)
ITERATION_LIMIT = 8     # model calls one turn may make (step 34's MAX_CALLS, step 41's budget)
```

```python
def build_spec(instructions: str, model: str = MODEL,
               compact_at: int = COMPACT_AT, iteration_limit: int = ITERATION_LIMIT) -> AgentSpec:
    """An inline agent spec with compaction, offloading, an iteration limit and questions."""
    return AgentSpec(
        model=Model(name=model),
        instructions=instructions,
        config=RuntimeConfig(
            context_management=ContextManagementConfig(
                compaction=CompactionConfig(
                    enabled=True,
                    trigger=InputTokensCompactionTrigger(type="input_tokens", value=compact_at),
                ),
                large_tool_response=LargeToolResponseConfig(enabled=True),
            ),
            iteration_limit=iteration_limit,
            ask_user_questions=AskUserQuestionsConfig(enabled=True),
            dynamic_sub_agents=DynamicSubAgentsConfig(enabled=False),  # on by default; one thread keeps the table honest
        ),
    )
```

`compaction.trigger` is stage 14's threshold. Without it the server compacts
at 80% of the model's context length; with it, at the token count given.
`large_tool_response` is step 32's spill file: a tool result over the limit
goes to a sandbox file and the model sees a stub with the path.
`iteration_limit` is the number of model calls one turn may make. Step 34
set `MAX_CALLS = 40` and step 41 added a cost and a time budget next to it;
TrueForge exposes the call count only. `ask_user_questions` turns on the
built-in `ask_user_question` tool. All four have defaults (`true`, `true`,
`100`, `true`), so the spec here sets each one on purpose. Dynamic
subagents are also on by default and are switched off here: the usage
table counts every `model.message` it sees, and a second thread would put
a subagent's calls in the "model call(s)" count.

### 2. Merging the stream

`client/context.py`:

```python
def merge(base: dict, delta: dict) -> None:
    """Fold one `model.message.delta` into its base message, in place.

    Text appends. Tool-call fragments merge by `index`: the first fragment
    carries the id and the name, the rest append to `arguments`. The final
    delta carries `finish_reason` and `usage`.
    """
    if delta.get("content"):
        base["content"] = (base.get("content") or "") + delta["content"]
    for fragment in delta.get("tool_calls") or []:
        calls = base.setdefault("tool_calls", [])
        while len(calls) <= fragment["index"]:
            calls.append({"id": None, "type": "function", "function": {"name": "", "arguments": ""}})
        call = calls[fragment["index"]]
        if fragment.get("id"):
            call["id"] = fragment["id"]
        if fragment.get("tool_info"):
            call["tool_info"] = fragment["tool_info"]
        function = fragment.get("function") or {}
        if function.get("name"):
            call["function"]["name"] = function["name"]
        call["function"]["arguments"] += function.get("arguments") or ""
    for key in ("finish_reason", "usage"):
        if delta.get(key) is not None:
            base[key] = delta[key]
```

A live `model.message` arrives empty. Its text, its tool calls and its
usage come as `model.message.delta` events that share its `id`. This is
step 21's stream accumulator again: text appends, tool-call fragments
merge by `index`. The Python SDK has no merge helper, so the client keeps
this one. The question's `arguments` are only readable after the merge.

### 3. One turn as an object

`client/context.py`:

```python
@dataclass
class Turn:
    """What one streamed turn produced."""

    turn_id: str | None = None
    events: dict[str, dict] = field(default_factory=dict)   # id -> merged non-delta event
    messages: list[dict] = field(default_factory=list)      # the model.message events, in order
    pending: list[dict] = field(default_factory=list)       # tool.response_required events
    state: dict = field(default_factory=lambda: {"status": "incomplete"})  # turn.done state; only that event replaces it

    @property
    def status(self) -> str:
        """"done", "error", "cancelled", or "incomplete" when the stream ended before turn.done."""
        return self.state.get("status") or "incomplete"
```

```python
def stream_turn(client: TrueForge, session_id: str, input_items: list, on_delta=None) -> Turn:
    """Stream one turn and return it merged: messages, pending questions, final state."""
    turn = Turn()
    stream = client.sessions.create_turn_stream(session_id=session_id, input=input_items)
    for event in stream.with_metadata():
        data = event.data.model_dump(exclude_none=True)
        kind = data["type"]
        if kind == "turn.created":
            turn.turn_id = data.get("turn_id")
        elif kind == "model.message":
            turn.events[data["id"]] = data
            turn.messages.append(data)
        elif kind == "model.message.delta":
            base = turn.events.get(data["id"])
            if base is not None:
                merge(base, data)
            if on_delta and data.get("content"):
                on_delta(data["content"])
        elif kind == "tool.response_required":
            turn.events[data["id"]] = data
            turn.pending.append(data)
        elif kind == "turn.done":
            turn.state = data["state"]
        else:
            turn.events[data["id"]] = data
    return turn
```

`Turn` holds an `id`-keyed event index, the model messages in order, the
pending `tool.response_required` events and the `turn.done` state. The
index is what the docs call for: a pending call points at its
`model.message` by `source_event_id`, and the message holds the call's
name and arguments. `state` starts as `{"status": "incomplete"}` and only
`turn.done` replaces it, so a stream that drops mid-turn reads as
incomplete, not as done.

### 4. Finding the question

`client/questions.py`:

```python
def find_call(turn: context.Turn, ref: dict) -> dict | None:
    """The merged tool call a pending ref points at, through `source_event_id`."""
    message = turn.events.get(ref["source_event_id"])
    if not message or message.get("type") != "model.message":
        return None
    for call in message.get("tool_calls") or []:
        if call.get("id") == ref["id"]:
            return call
    return None
```

```python
def questions(turn: context.Turn) -> list[dict]:
    """Every pending `ask_user_question` call: thread id, call id, question and options."""
    found = []
    for pending in turn.pending:
        for ref in pending["tool_calls"]:
            call = find_call(turn, ref)
            if not call or call.get("function", {}).get("name") != ASK_USER:
                continue
            arguments = context.arguments_of(call)
            found.append({
                "thread_id": pending["thread_id"],
                "tool_call_id": ref["id"],
                "question": arguments.get("question") or "",
                "options": list(arguments.get("options") or []),
            })
    return found
```

`tool.response_required` covers any client-side tool. The loop keeps only
the calls named `ask_user_question` and reads `question` and `options` from
their JSON arguments, which is the same argument shape step 35 gave
`ask_user`. Any other pending call is a tool this client does not have;
`unanswerable` lists those so they can be declined rather than left
hanging:

```python
def unanswerable(turn: context.Turn) -> list[dict]:
    """Pending calls that are not questions: client-side tools this client does not implement."""
```

### 5. Asking and resuming

`client/questions.py`:

```python
def ask(question: str, options: list[str], read=input) -> str:
    """Print the question with numbered options and return the chosen text.

    A number picks an option, as in step 35. Anything else is the answer as
    typed. An empty answer becomes a note the model can act on.
    """
    print(f"\n? {question}")
    for number, option in enumerate(options, 1):
        print(f"  {number}. {option}")
    try:
        answer = read("answer> ").strip()
    except (EOFError, KeyboardInterrupt):  # stdin closed or ctrl-c: the model gets a note, not a crash
        print()
        return NO_ANSWER
    if answer.isdigit() and 1 <= int(answer) <= len(options):
        return options[int(answer) - 1]
    return answer or NO_ANSWER
```

```python
    for call in unanswerable(turn):  # every pending call must get a response or the turn stays paused
        replies.append(UserToolResponseEvent(
            thread_id=call["thread_id"], tool_call_id=call["tool_call_id"],
            content=f"Error: this client cannot run {call['name']}",
        ))
    return replies
```

```python
def run(client: TrueForge, session_id: str, prompt: str, read=input, on_delta=None) -> list[context.Turn]:
    """Send a prompt, answer every question the agent asks, return all the turns.

    The first turn carries the user message. Every `done` turn that ends
    with pending calls is followed by a resume turn whose input is only the
    answers: the server refuses a turn that mixes the two. A turn that
    ended in `error` or `cancelled` is not resumed, whatever it left
    pending, and `MAX_ROUNDS` bounds the number of resumes.
    """
    turns = [context.stream_turn(client, session_id, [UserMessage(content=prompt)], on_delta)]
    for _round in range(MAX_ROUNDS):
        if turns[-1].status != "done" or not turns[-1].pending:
            return turns
        turns.append(context.stream_turn(client, session_id, answers(turns[-1], read), on_delta))
    turns[-1].state = {"status": "error", "message": f"still asking after {MAX_ROUNDS} resume turns"}
    return turns
```

Step 35 answered inside the tool call: the same process printed the
question, read the line and returned it as the tool result. Here the
server has no terminal. It ends the turn, and the client starts a new one
whose input is one `user.tool_response` per pending call, with the
`thread_id` and `tool_call_id` copied from the pending event. Turns chain
on their own, so the answer lands in the right place in the transcript.
Three guards: only a `done` turn is resumed, every pending call gets a
reply (a question gets the user's, anything else gets an `Error:` the
model can read), and `MAX_ROUNDS = 20` ends a run whose agent never stops
asking, with an `error` state that names the cap.

### 6. The usage table

`client/context.py`:

```python
def usage_table(messages: list[dict]) -> str:
    """The `input_tokens_breakdown` of every model call as a table, plus a bar per category.

    One row per call. The last row sums the calls. Under the table, the
    five categories of the summed input with one bar each: step 32's
    `/context` chart, drawn from what the server reports.
    """
    rows = [message["usage"] for message in messages if message.get("usage")]
    if not rows:
        return "no usage reported"
    head = f"{'call':<5}" + "".join(f"{c:>17}" for c in CATEGORIES) + f"{'input':>9}{'output':>8}"
    lines = [head, "-" * len(head)]
    total = {c: 0 for c in CATEGORIES} | {"input_tokens": 0, "output_tokens": 0}
    for number, usage in enumerate(rows, 1):
        breakdown = usage.get("input_tokens_breakdown") or {}
        for category in CATEGORIES:
            total[category] += breakdown.get(category, 0)
        total["input_tokens"] += usage.get("input_tokens", 0)
        total["output_tokens"] += usage.get("output_tokens", 0)
        lines.append(_row(str(number), breakdown, usage))
    lines.append(_row("all", total, total))
    largest = max(total[c] for c in CATEGORIES) or 1
    lines.append("")
    for category in CATEGORIES:
        bar = "#" * round(BAR * total[category] / largest)
        lines.append(f"{category:<18} {total[category]:>8,}  {bar}".rstrip())
    return "\n".join(lines)
```

Step 32 estimated the breakdown on the client, category by category, from
the messages it was about to send. TrueForge reports it on every
`model.message`: `harness` (the server's own framing), `skills`,
`instructions`, `tool_definitions` and `messages`. The bars are step 32's
`render`, scaled to the largest category as before.

### 7. How the run ended

`client/context.py`:

```python
def status_line(state: dict) -> str:
    """How the turn ended. An iteration limit ends it with status `error` and a message."""
    status = state.get("status") or "incomplete"
    if status == "done":
        return "status: done"
    detail = state.get("message") or state.get("reason") or ""
    if status == "incomplete":
        detail = "the stream ended before turn.done"
    return f"status: {status} - {detail}".rstrip(" -")


def sum_metrics(turns) -> dict:
    """The `metrics` of several turns added up, key by key."""
    total: dict = {}
    for turn in turns:
        for key, value in turn.metrics.items():
            if isinstance(value, (int, float)):
                total[key] = total.get(key, 0) + value
    return total
```

Step 41 printed why the loop stopped. On TrueForge the reason is in
`turn.done`: a crossed iteration limit ends the turn with `status: error`
and the message `You have reached iteration limit of N, please request
again`, which is step 41's "say continue to go on". A new turn on the same
session carries on from there. `metrics` on `turn.done` is per turn and a
question makes the run two turns, so the demo prints `sum_metrics` over
all of them; that is why the `metrics` line and the table's `all` row
agree. The demo exits 1 unless the last turn is `done`.

## Run it

Prerequisites: step 46's server and model. No extra packages beyond
`trueforge_sdk`.

bash:

```bash
cd step_49_trueforge_context
python demo.py                      # asks on the terminal, waits at answer>
python demo.py --answer 2           # picks "node" without a prompt
python demo.py "make me a website"  # another prompt; the instructions still ask first
python -m pytest -q test_step.py    # offline: a fake TrueForge server in a thread
```

PowerShell:

```powershell
cd step_49_trueforge_context
python demo.py --answer 2
python -m pytest -q test_step.py
```

Expected output: the Quick demo above. You should see the four limits, the
streamed question with its numbered options, the reply after the answer,
one table row per model call, the bars, the run's summed `metrics` and
the last turn's `status`. To see the iteration limit trip, give the spec
a sandbox (`spec.config.sandbox`) and a task that needs more tool rounds
than `iteration_limit` allows. `--base-url` or `TRUEFORGE_BASE_URL` picks
another server; `TRUEFORGE_MODEL` another model.

## Error handling

- **Server not running.** `request failed: http://localhost:8790 is not answering (ConnectError: ...)`
  on stderr, exit 1.
- **The iteration limit trips, or any `error`/`cancelled` turn.** The
  status line says `status: error - You have reached iteration limit of 8, please request again`
  and the exit code is 1. A question streamed in that turn is not asked.
- **A dropped stream.** `status: incomplete - the stream ended before turn.done`, exit 1.
- **ctrl-d (ctrl-z then enter on Windows) or ctrl-c at `answer>`.** The
  model receives `(no answer given)` and the turn resumes; the demo does
  not crash. ctrl-c while the reply streams ends the demo with a
  `KeyboardInterrupt`; the turn keeps running on the server.
- **A pending client-side tool that is not a question.** The resume
  carries `Error: this client cannot run <name>` for it, so the turn is
  never left paused.
- **An agent that asks forever.** After `MAX_ROUNDS` (20) resumes the
  run stops with `status: error - still asking after 20 resume turns`.

## Gotchas / what this is not

- Only two of the four fields are exercised by the demo. Compaction at
  20,000 input tokens cannot fire in a two-turn run of about 1,100 tokens
  each, and `large_tool_response` needs a tool result to offload; this
  agent has no tools but `ask_user_question`. The offload writes to a
  *sandbox* file, and this spec has no sandbox, so whether it works without
  one was not tested here.
- `input_tokens_breakdown` is the server's estimate per model call;
  `metrics` is the provider's count per turn. In the demo `harness` alone
  is 1,288 while the provider billed 1,091 input tokens, and `messages`
  stays 0 with a user message present. Read the categories as
  proportions, and `input` as the bill.
- `iteration_limit` counts model calls per turn, and the resume after a
  question is a new turn. Step 41's cost and time budgets have no field
  here; `sum_metrics` is the client-side sum that a budget would read.
- Subagents are switched off in the spec; the question tool is the only
  tool this agent has.

## What to notice

- Four codelab files became four fields. The server compacts, spills,
  counts and offers the question tool. The client's code is about the
  two things the server cannot do: read a keyboard and show a chart.
- A question is a paused turn. `tool.response_required` ends the stream;
  the answer is a new turn. The docs are strict about it: a turn's `input`
  cannot mix `user.message` with `user.tool_response` items.
- The pending event carries only ids. `source_event_id` points at the
  `model.message` with the call, and that message is complete only after
  its deltas are merged. Without an event index there is no question text.
- A pause and an error can share a turn. Only a `done` turn is worth
  answering; the same rule as step 47's approvals.
- The step 32 chart cost the client a token counter and the schemas of
  every tool. Here it costs nothing: the numbers ride on events the client
  already receives.

## Capability table

| Capability | This codelab | TrueForge |
| --- | --- | --- |
| Compaction | Stage 14: `compact.py` summarises the transcript when it grows too long, `/compact` on demand | `config.context_management.compaction` with `trigger: {"type": "input_tokens", "value": N}`; done by the server |
| Large tool output | Stage 14: `history.cap` trims a result and parks the rest in a file; step 32 counts it | `config.context_management.large_tool_response.enabled`; the rest goes to a sandbox file |
| Context chart | Step 32: `budget.breakdown` estimates the categories, `/context` draws bars | `usage.input_tokens_breakdown` on every `model.message`; `usage_table` draws it |
| Call budget | Step 34: `MAX_CALLS`; step 41: `stop.tripped` with call, cost and time budgets | `config.iteration_limit`; `turn.done` `state.status: error` with the limit message |
| Questions | Step 35: `ask_user` tool answered inside the tool call | `config.ask_user_questions`; `tool.response_required` then `user.tool_response`, `MAX_ROUNDS` on the client |
| Stop report | Step 41: the loop prints the budget report and `-p` prints the summary | `turn.done` `state` (`done`, `error` with `message`, `cancelled` with `reason`); `incomplete` when the stream ends early |

## What the next step adds

Step 50 turns dynamic subagents on and prints their threads, reads the
session store back (list, replay, reconnect), and runs the step 30 eval
suite through TrueForge with the tools server of step 47.
