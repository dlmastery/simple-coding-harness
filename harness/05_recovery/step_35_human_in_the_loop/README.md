# Step 35 - Human in the loop

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Resume work without guessing**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 34 - Durability and recovery](../step_34_durability/README.md). Next: [Step 36 - Orchestration patterns](../step_36_orchestration/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** three ways for the user to take part in a turn
while it runs. An `ask_user` tool lets the model put a question to the
user, with numbered options, and get the answer back as a tool result.
Ctrl-C during a turn no longer kills the loop: it stops the current wait,
reads one line at a `steer>` prompt, appends it as a user message after
the pending tool results, and the turn goes on. A second Ctrl-C within
two seconds exits. The approve prompt takes four answers: `y`, `n`, `a`
for always and `never`. The last two are kept in `permissions.SESSION_RULES`
for the rest of the session, keyed by what the prompt asked about: the
tool, for bash the first word of each command part, for a write outside
the project that fact, for the browser the host.

## Files

```text
step_35_human_in_the_loop/
├── harness/
│   ├── __init__.py       package marker
│   ├── agent.py          the loop; Ctrl-C anywhere in a turn steers it instead of killing it
│   ├── ask_user.py       the ask_user tool: a question to the user, answer as result
│   ├── browse.py         the browse tool set over the step 23 browser subagent
│   ├── browser.py        browser tools: one Chromium page driven through Playwright
│   ├── budget.py         the context budget: where the window goes, when to warn
│   ├── checkpoint.py     workspace checkpoints: file copies taken before each approved edit
│   ├── commands.py       slash commands: /undo, /rewind, /checkpoints and the rest
│   ├── compact.py        the compaction agent; its note is kept
│   ├── computer.py       computer use: the screen as a tool
│   ├── config.py         settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py        the late injection block: <env>, <plan>, <jobs>
│   ├── durability.py     the loop detector, parse_args and the crash-recovery scan
│   ├── evaluate.py       the evaluation harness; `isolated` auto-answers prompts
│   ├── history.py        keeps the transcript small enough to send, pictures too
│   ├── hooks.py          hook events from hooks.json; PostToolUse carries `ok`
│   ├── instructions.py   project instruction files (AGENTS.md) for the prompt
│   ├── jobs.py           background jobs: commands that run while the chat goes on
│   ├── llm.py            the model call with retries, and the system prompt
│   ├── mcp_client.py     MCP client: tools served by other processes over stdio
│   ├── memory.py         persistent memory
│   ├── permissions.py    which calls need a human; session rules from `a` and `never`
│   ├── plan.py           plan mode: the read-only tool set, ask_user included
│   ├── prompt.py         the input line; prompts go to stderr without a terminal
│   ├── sandbox.py        an OS sandbox for bash; the process-group timeout
│   ├── session.py        append-only JSONL session log, load() and --resume
│   ├── skills.py         skills, unchanged since stage 9
│   ├── subagent.py       the task subagent loop; what it is offered is what it may run
│   ├── todos.py          the plan behind write_todos, validated before it replaces the list
│   ├── tools.py          the tool registry; settle() reads the four approve answers
│   └── ui.py             rich panels; four-answer approve, question(), interrupted()
├── .agents/
│   ├── .gitignore                     ignores tool_log.txt, the PostToolUse hook's log
│   ├── hooks.json                     hook config: one PreToolUse and one PostToolUse hook
│   ├── block_env_writes.py            example PreToolUse hook: refuses to write a .env file
│   ├── log_tool_use.py                example PostToolUse hook: appends every tool name to a log
│   ├── mcp.json                       MCP config: one stdio server, echo
│   ├── mcp_echo_server.py             a tiny MCP server: two tools, stdio transport
│   └── skills/explain-code/SKILL.md   the stage 4 skill
├── evals/           three step 30 tasks: task.md, check.py or expect.txt, workspace/
├── AGENTS.md        project instructions the harness reads into its prompt
├── test_step.py     offline tests: scripted prompts, a real main-thread Ctrl-C, no terminal
├── pyproject.toml   package metadata; version 0.35.0
└── README.md        this file
```

## Why the user belongs inside the turn

Up to step 34 the user speaks twice per turn: once at the input line, and
once at every approve prompt. Between those, the loop is a closed box.
When a request is ambiguous, the model guesses, and a wrong guess costs a
whole turn plus the undo. When the model heads the wrong way, the user
watches until it stops. And every `git commit` asks again, even after the
user said yes to ten of them.

Each of the three additions opens the box a little. The `ask_user` tool
turns a guess into a question. The steer prompt turns watching into
talking. The `a` answer turns repeated approval into a rule. None of them
changes the shape of the transcript: a question is a tool call with a
result, a steering message is a user message, and a session rule is a
verdict the permission layer gives before it reaches the prompt.

The hard part is the interrupt. A `KeyboardInterrupt` can arrive in the
middle of anything: the `git status` of the late block, a streaming
reply, a running command, a wait on a thread pool. If the loop just
stopped there, the transcript would end in an assistant message whose
tool calls have no results, which the API refuses. So the whole turn body
sits under one guard, and in both halves of it - the model call and the
tool calls - the transcript is made whole before the user is asked what
to do next.

What breaks without it: before this step a Ctrl-C during a long `pytest`
run ended the process with a traceback and a transcript ending in
unanswered tool calls; `--resume` then re-ran the same call. A model
that had to choose between two test runners picked one and the user
found out after the install.

## The code, piece by piece

### 1. The question tool

`harness/ask_user.py`:

```python
def ask_user(question: str, options=None) -> str:
    ...
    options = list(options or [])
    ui.question(question, options)
    try:
        answer = prompt.read("  answer> ").strip()
    except (EOFError, KeyboardInterrupt):
        return NO_ANSWER
    if answer.isdigit() and 1 <= int(answer) <= len(options):
        return options[int(answer) - 1]
    return answer or NO_ANSWER
```

The tool prints the question and the options numbered from 1, then reads
one line with the same `prompt.read` the input line uses. A number in
range returns that option's text, so the model reads `pytest` and not
`2`. Anything else is the answer as typed, so the user can reject every
option. Ctrl-C or Ctrl-D at the answer prompt returns `NO_ANSWER`, and the
model learns that the question was not answered rather than reading an
empty string as consent. A Ctrl-C at this prompt, or at an approve
prompt, is an answer, not a steer.

The tool is in `plan.READ_ONLY`, so it is offered in plan mode: a
question changes nothing on disk, and the plan is where questions come
up. It is withheld from subagents, which cannot see the conversation, and
withheld means denied: a subagent that calls it anyway gets
`Blocked by policy: ask_user is not available to this agent`. The system
prompt says when to call it: when two readings of the request lead to
different work, and before any choice that cannot be undone.

### 2. Reading the steer line and appending it

`harness/agent.py`:

```python
STEER_WINDOW = 2.0  # seconds: a second Ctrl-C within this many after the first exits


def steer(where):
    ...
    pressed = time.monotonic()
    ui.interrupted(where)
    try:
        return prompt.read("  steer> ").strip()
    except EOFError:
        return None
    except KeyboardInterrupt:
        return None if time.monotonic() - pressed < STEER_WINDOW else ""
...
def steered(messages, where):
    ...
    line = steer(where)
    if line is None:
        ui.note("exiting; the transcript is saved and --resume picks it up")
        return False
    if line:
        messages.append({"role": "user", "content": line})
        session.save(messages)
        ui.user(line)
    return True
```

`steer` runs after the first Ctrl-C was caught. It notes the time, says
what was interrupted, and reads one line. Three things can come back. A
line is the steering message. An empty string means the user pressed
enter with nothing to add, or pressed Ctrl-C again after the window; the
turn goes on unchanged. `None` means the user wants out: a second Ctrl-C
inside the window, or Ctrl-D.

`steered` appends the line to whatever the turn has built so far, as a
plain user message, and saves. It returns `False` when the user wants
out, and the callers re-raise the interrupt.

### 3. One guard around the whole turn

`harness/agent.py`:

```python
    for _ in range(MAX_CALLS):
        try:
            message, usage = one_call(messages, submitted.context, debug)
        except KeyboardInterrupt:
            if not steered(messages, "the model call"):  # nothing dangles: the reply never went in
                raise
            continue  # a new request, with the steering message at the end
        if message is None or not message.tool_calls:
            break

        repeated = detector.observe(message.tool_calls)
        for tool_call, flag in zip(message.tool_calls, repeated):
            if flag:
                ui.note(f"repeated call detected: {tool_call.function.name} with the same arguments {durability.REPEAT_LIMIT} times in a row")
        try:
            run_results(messages, message.tool_calls, repeated)
        except KeyboardInterrupt:
            if not steered(messages, "the tool calls"):  # every call has a result by now
                raise
    else:
        ui.note(f"stopped after {MAX_CALLS} model calls in one turn; say 'continue' to go on")
```

`one_call` is everything between two tool phases: the late block (which
runs `git status`), the context fit, the request and the stream, and the
reply going into the transcript. A Ctrl-C anywhere in there leaves the
transcript as it was - the last message is still the user's - and the
interrupted call still counts against `MAX_CALLS`, because `continue`
uses up one pass of the `for`:

```python
    except KeyboardInterrupt:
        if streamed:
            ui.stream_end()  # the part that arrived is on screen, but it goes nowhere: a reply is whole or absent
        raise
```

A partial stream is on screen, but a reply is whole or absent in the
transcript, so the text is dropped. The steering message goes after the
user's message, and `continue` sends a new request. When the model call
fails for good, `one_call` returns `None` for the message and the turn
ends with the transcript valid.

The tool phase is the other half. Here the assistant message with its
tool calls is already in the transcript, so a result is owed for every
call. `run_results` pays that debt before the exception reaches this
handler.

### 4. Making the transcript whole first

`harness/agent.py`:

```python
    outcomes = []  # (args, result) per fresh call, filled as each one finishes
    interrupt = None
    try:
        if fresh:
            execute_all(fresh, outcomes=outcomes)
    except KeyboardInterrupt as stop:
        interrupt = stop
    outcomes += [(durability.parse_args(call), None) for call in fresh[len(outcomes):]]  # never started
    ran = iter((args, INTERRUPTED if result is None else result) for args, result in outcomes)
    ...
    if interrupt is not None:
        raise interrupt  # the transcript is whole; now the user gets to speak
```

`execute_all` takes the list it fills, so `run_results` can see how far
it got when the interrupt came. A call that finished keeps its result. A
call that was cut short, or never started, gets `INTERRUPTED`, which
tells the model that nothing ran (or that the result is lost) and that
the user's next message comes first. The results are appended in order,
the pictures after them, and only then is the interrupt raised again for
`turn` to handle. The model reads the reply, its results and the
steering message in that order, which is what happened.

`harness/tools.py`:

```python
    def keep(i):
        """A callback that files the result of call i the moment it is in, on whichever thread ran it."""
        def done(future):
            if future.exception() is None:
                outcomes[i] = (outcomes[i][0], future.result())
        return done

    pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    futures = {i: pool.submit(run, tool_calls[i], outcomes[i][0]) for i in pending}
    for i, future in futures.items():
        future.add_done_callback(keep(i))
    try:
        while not all(future.done() for future in futures.values()):
            wait(futures.values(), timeout=POLL)  # short waits: Windows delivers a Ctrl-C only between them
        for future in futures.values():
            future.result()  # re-raises the first failure, in call order
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)  # the queued calls never start; the running ones finish alone
        raise
    pool.shutdown(wait=True)
    return outcomes
```

With several calls running at once, the results are filed by a callback
the moment each call finishes, not when the main thread gets round to
collecting them. So a Ctrl-C that lands while the main thread waits on
the second call does not lose the third call's result. The pool is not a
`with` block: leaving one waits for every running *and queued* call, so
six one-second commands would hold the steer prompt for two seconds. On
a Ctrl-C the pool is dropped instead: the calls still in the queue are
cancelled and get `INTERRUPTED`, the ones already running finish on a
thread nobody waits for, and their result is lost if it comes in late.
The wait is a loop of short `wait` calls because Windows delivers the
interrupt only when the main thread wakes; with `POLL` at 0.2 s it wakes
soon enough. The same shape is in `subagent.parallel`, so a Ctrl-C during
a `task` that runs four subagents does not wait for the wave.

### 5. Four answers at the approve prompt

`harness/ui.py`:

```python
    ANSWERS = {"y": "y", "yes": "y", "n": "n", "no": "n", "a": "a", "always": "a", "never": "never"}

    def approve(self, reason):
        ...
        try:
            answer = prompt.read("  allow? (y/n/a=always/never)> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "n"
        return self.ANSWERS.get(answer, "n")
```

`approve` used to return a boolean. Now it returns the answer, one of
four strings, and the safe answer is the default: any other text, Ctrl-C
and Ctrl-D are all `n`.

`harness/tools.py`:

```python
    if action == "ask":
        answer = ui.approve(reason)
        if answer in ("a", "never") and name is not None:
            ui.note("remembered: " + permissions.remember(name, args or {}, "allow" if answer == "a" else "deny"))
        if answer not in ("y", "a"):
            return DENIED
    return None
```

`settle` reads the answer. `a` runs the call and stores an allow; `never`
declines it and stores a deny. Both are stored under the keys
`session_keys` computes for the call. `y` and `n` are not stored: they
answer one call. `ui.approve` still holds `APPROVE_LOCK` while it asks, as
since step 29: a `task` with four subagents runs them on threads, and two
of them hitting `ask` at once would otherwise write to one input line
together.

### 6. The session rules

`harness/permissions.py`:

```python
SESSION_RULES = {}  # (tool, what was asked) -> "allow" or "deny", from the a and never answers of this session
...
def session_keys(name, args):
    ...
    if name in ("bash", "bash_background"):
        return [("bash", first_word(part)) for part in split_command(args.get("command", ""))]
    if name in ("write_file", "str_replace"):
        return [(name, "outside" if not inside_project(args.get("path", "")) else "")]
    if name == "browser_open":
        return [(name, (urlparse(args.get("url", "")).hostname or "").lower())]
    return [(name, "")]


def remembered(name, args):
    """The session rule for this call as (verdict, reason), or None. Plan mode ignores the rules: its answer is always no."""
    if plan.MODE == "plan":
        return None
    for key in session_keys(name, args):
        if key in SESSION_RULES:
            return SESSION_RULES[key], f"{SESSION_RULES[key]} for this session: " + " ".join(part for part in key if part)
    return None
```

The key is what the prompt asked about. A bash command is filed under
the first word of every part, so `a` on `cd build && python setup.py`
allows `cd` and `python` - every later `python -c "..."` included, which
is a lot to unlock with one keystroke. A write outside the project is
filed under `("write_file", "outside")`: `never` there blocks the next
outside write and says nothing about writes inside the project, which
were never asked about. A browser page is filed under its host, so `a`
on `docs.python.org` does not open every site. Any other tool - an MCP
tool, `computer_act` - is filed under its name, so one `a` covers every
later call whatever the arguments. Plan mode ignores the rules: its
answer to an `ask` is always no, and a rule stored in act mode must not
change that.

```python
def rate(part):
    ...
    action = "ask"
    for pattern, rule in BASH_RULES.items():
        if fnmatch(part, pattern):
            action = rule
    if action == "allow" and WRITES.search(unquoted(part)):
        action = "ask"  # `cat a > b` is a write, whatever the verb
    rule = SESSION_RULES.get(("bash", first_word(part))) if plan.MODE != "plan" else None
    if rule and action != "deny":
        action = rule
    return action
```

A bash command is rated one part at a time, as before. For each part the
session rule for its first word is consulted after the static rules,
with one exception: a `deny` in `BASH_RULES` still wins. An `a` on
`git commit` allows `git log` and `git commit` for the session and
leaves `git push` denied, because nothing said at the prompt unlocks the
deny list. An allowed command that writes through `>` or `tee`, or a
`find` with `-delete` or `-exec`, is rated `ask` first: `cat x > y` is
not read-only. The eval runner empties the rules for each task and puts
them back after.

## Run it

Prerequisites: Python 3.10+, `API_KEY` in the environment or in
`~/.simple-harness/env`, and a terminal - the steer prompt and the
question prompt read from it.

```bash
cd harness/05_recovery/step_35_human_in_the_loop
pip install -e .
harness
```

```powershell
cd harness/05_recovery/step_35_human_in_the_loop
pip install -e .
harness
```

The offline tests: `python -m pytest -q test_step.py`, or from the
repository root `python run_tests.py 35` and `python check_snippets.py 35`.

### Expected output

Ask for something with a choice in it:

```text
> add a test runner config

  ask_user  Which test runner should the config target?
    1. unittest
    2. pytest
  answer> 2

  bash  pip install pytest
  run: pip install pytest
  allow? (y/n/a=always/never)> a
  remembered: allow for this session: bash pip

  bash  pip install pytest-cov
  ...
  Added pytest.ini and a pytest-cov dependency.
```

The question and the options print with numbers, and the `answer>`
prompt waits. Type `2` or the text of the choice. The answer shows up as
the tool result, and the model goes on with it. The second `pip` runs
without a prompt; `git push` still would not.

Then interrupt a turn. While the spinner runs or a command is running,
press Ctrl-C once:

```text
  interrupted the tool calls. Type a message to steer, press enter to go on, or ctrl-c again to exit
  steer> look in src/ not in tests/
```

The interrupted call gets `INTERRUPTED` as its result, the steering line
prints as a user message, and the next model call sees both. In the
transcript that is `assistant, tool, ..., user (the steer line)`, and
when the late block follows it, two user messages in a row; every
OpenAI-compatible provider tried accepts that, but a strict one may not.
Press enter with nothing typed to go on as before. Press Ctrl-C twice in
quick succession to exit; the transcript is saved and `--resume` picks
it up.

## Error handling

- A tool call with arguments that are not a JSON object gets the result
  `Error: the arguments of <name> are not a JSON object: <reason>`; a
  name that is not in the registry gets `Error: no tool named '<name>'.`;
  a tool that raises gets `Error: <Type>: <message>`; a call without the
  argument the rules read (`command`, `path`, `url`) gets
  `Blocked by policy: <name>: missing argument '<key>'`. Every tool call
  gets exactly one tool message and the turn goes on. Nothing here ends
  the process.
- A failing command is a result too: its output, or
  `Timed out after 60s and was killed. Output so far:` with what it had
  printed. The timeout kills the whole process tree.
- A dead model call: `call_llm` retries transport errors, 429 and 5xx
  with backoff; when every retry fails the note
  `model call failed 5 times, giving up (...)` prints (or
  `model call failed and will not be retried (...)` for a 4xx) and the
  turn ends with the transcript valid - the user's message stays, nothing
  half-written is appended.
- Ctrl-C: once during a turn is the steer prompt; twice within two
  seconds, or Ctrl-D at the steer prompt, leaves the turn and the chat
  with every tool call answered. Ctrl-C at an approve prompt is `n`, at
  an `answer>` prompt is `NO_ANSWER`. Ctrl-C inside a `/command`
  (`/init`, `/compact`) prints `command interrupted` and returns to the
  input line. Ctrl-C at the input line exits.
- `--resume` of a session that ended in unanswered tool calls re-runs
  them through `recover()`; a call that fails there - the same broken
  arguments that crashed the last run, say - becomes an `Error:` result,
  so a resume never crashes on the same call twice.
- `-p` without a terminal on stdin (a pipe, CI): every `ask` is declined
  with `declined, no terminal to ask on: ...` on stderr, `ask_user`
  answers `NO_ANSWER`, prompts never reach stdout, the exit code is 1
  when the reply is empty and 130 on Ctrl-C, and no session file is
  written unless `--resume` was given.
- Leaving: `/exit`, `/quit`, Ctrl-D (Ctrl-Z then Enter on Windows) or
  Ctrl-C at the input line.

## Gotchas / What this is not

- The tool named `bash` runs `cmd.exe` on Windows; there is no sandbox
  there, and the banner says `sandbox: none`.
- Windows delivers Ctrl-C to every process attached to the console, so a
  command that `bash` is running gets it too and dies; the harness sees
  the interrupt once the command has ended, and the result recorded is
  `INTERRUPTED`. Background jobs from step 29 run in their own process
  group and do not get it.
- A running tool call is never killed by the steer: it finishes on its
  own thread. Only the calls still in the queue are cancelled. A
  streamed reply is interrupted at the next chunk.
- `a` on a compound bash line unlocks every first word in it for the
  session, `python` included. `a` on an MCP tool or on `computer_act`
  unlocks every later call of that tool whatever its arguments. Session
  rules do not survive a restart.
- PreToolUse hooks run inside `decide()`, before the approve prompt, so
  a call the user then declines has already been logged by
  `log_tool_use.py`. The checkpoint capture runs in `run()`, after the
  approval, so a declined edit captures nothing.
- The loop detector counts calls that are then denied: the third
  identical denied call reads `REPEATED` instead of `DENIED`. The polling
  tools in `durability.OBSERVE` (`job_status`, `job_wait`, the screenshot
  and page reads) repeat on purpose and are never flagged.
- Approve prompts fire inside subagents too, from pool threads; the lock
  keeps them one at a time, but they interleave with the other
  subagents' panels.
- The "nobody is here" answer to `ask_user` exists only under
  `harness eval` and headless `-p`; in a normal chat the tool waits.

## What to notice

- A question is a tool call. It goes through `decide` and `settle` like
  any other, is always allowed, and its answer is a tool result the model
  reads in the next request. Nothing in the loop knows the tool is special.
- The steering message is appended, not injected. It is a plain user
  message in the transcript, saved with the rest, replayed on `--resume`,
  and moved by compaction. The late block is for the harness; the user's
  words are the user's.
- Both halves restore the invariant first and ask second. The API wants
  a result for every tool call, and `run_results` provides one for every
  call before the exception is raised again. A second Ctrl-C at the steer
  prompt leaves a transcript that `--resume` can send as is.
- `execute_all` fills a list the caller owns, so the caller can read it
  after an exception. A return value would be lost with the exception;
  a shared list is not.
- A session rule sits between the prompt and the static rules, and only
  on the `ask` side. The deny list is not a question, so no answer at the
  prompt reaches it.
- Two seconds is a guess at how fast a person presses a key twice on
  purpose. The window is a constant, `STEER_WINDOW`, so it can be tuned.

## Diff from step 34

```bash
diff -r ../step_34_durability/harness harness
```

Added: `ask_user.py` (`ASK_USER_SCHEMA`, `NO_ANSWER`, `ask_user`).
Changed: `agent.py` (`STEER_WINDOW`, `steer`, `steered`, `one_call` and
the guard around the turn body, `run_results` fills `INTERRUPTED` and
re-raises, `chat` catches the interrupt of a `/command` and ends on one
from `turn`, `headless` declines prompts without a terminal and exits
130 on Ctrl-C), `tools.py` (`ask_user` in `TOOL_SCHEMAS` and `TOOLS`,
`INTERRUPTED`, `POLL`, `settle` takes `name` and `args` and reads four
answers, `execute_all` takes `outcomes`, files results by callback and
polls the pool so a Ctrl-C is seen on Windows too), `permissions.py`
(`SESSION_RULES`, `first_word`, `session_keys`, `remembered`,
`remember`, `rate`, `check` consults the session rules), `ui.py`
(`ANSWERS`, `approve` returns the answer, `question`, `interrupted`, the
banner), `plan.py` (`ask_user` in `READ_ONLY`), `subagent.py` (`ask_user`
in `WITHHELD`, `parallel` polls its pool and drops it on a Ctrl-C),
`llm.py` (the `ask_user` paragraph in the system prompt), `evaluate.py`
(`isolated` answers `y`, replaces `ask_user`, and resets
`SESSION_RULES`). Everything else is unchanged from step 34.

## What the next step adds

Step 36 turns `.agents/agents/<name>.md` files into `agent_<name>` tools
and adds `/pipeline`, which runs the planner, worker and reviewer agents
over a task.
