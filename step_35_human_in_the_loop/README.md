# Step 35 - Human in the loop

**What this step adds:** three ways for the user to take part in a turn
while it runs. An `ask_user` tool lets the model put a question to the
user, with numbered options, and get the answer back as a tool result.
Ctrl-C during a turn no longer kills the loop: it stops the current wait,
reads one line at a `steer>` prompt, appends it as a user message after
the pending tool results, and the turn goes on. A second Ctrl-C within
two seconds exits. The approve prompt takes four answers: `y`, `n`, `a`
for always and `never`. The last two are kept in `permissions.SESSION_RULES`
for the rest of the session, per tool and, for bash, per first word of the
command.

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
middle of anything: a streaming reply, a running command, a wait on a
thread pool. If the loop just stopped there, the transcript would end in
an assistant message whose tool calls have no results, which the API
refuses. So the interrupt is caught in two places, and in both the
transcript is made whole before the user is asked what to do next.

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
empty string as consent.

The tool is in `plan.READ_ONLY`, so it is offered in plan mode: a
question changes nothing on disk, and the plan is where questions come
up. It is withheld from subagents, which cannot see the conversation; a
subagent's question goes through the lead agent. The system prompt says
when to call it: when two readings of the request lead to different work,
and before any choice that cannot be undone.

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

### 3. The two places the interrupt is caught

`harness/agent.py`:

```python
        try:
            with spinner:
                message, usage = call_llm(with_mode(messages) + [injection], tools=active_schemas(plan.toolset()), on_delta=on_delta)
        except KeyboardInterrupt:
            if streamed:
                ui.stream_end()  # the part that arrived is on screen, but it goes nowhere: a reply is whole or absent
            calls += 1
            if not steered(messages, "the model call"):
                raise
            continue  # a new request, with the steering message at the end
...
        try:
            run_results(messages, message.tool_calls, repeated)
        except KeyboardInterrupt:
            if not steered(messages, "the tool calls"):  # every call has a result by now
                raise
```

An interrupted model call has no reply to keep. A partial stream is on
screen, but a reply is whole or absent in the transcript, so the text is
dropped and the last message is still the user's. The steering message
goes after it, and `continue` sends a new request. The interrupted call
still counts against `MAX_CALLS`.

The tool phase is the other place. Here the assistant message with its
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
            execute_all(fresh, outcomes)
    except KeyboardInterrupt as stop:
        interrupt = stop
    outcomes += [(durability.parse_args(call), None) for call in fresh[len(outcomes):]]  # never started
    ran = iter((args, INTERRUPTED if result is None else result) for args, result in outcomes)
    ...
    if interrupt is not None:
        raise interrupt  # the transcript is whole; now the user gets to speak
```

`execute_all` now takes the list it fills, so `run_results` can see how
far it got when the interrupt came. A call that finished keeps its
result. A call that was cut short, or never started, gets `INTERRUPTED`,
which tells the model that nothing ran and that the user's next message
comes first. The results are appended in order, the pictures after them,
and only then is the interrupt raised again for `turn` to handle. The
model reads the reply, its results and the steering message in that
order, which is what happened.

`harness/tools.py`:

```python
    def keep(i):
        """A callback that files the result of call i the moment it is in, on whichever thread ran it."""
        def done(future):
            if future.exception() is None:
                outcomes[i] = (outcomes[i][0], future.result())
        return done

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {i: pool.submit(run, tool_calls[i], outcomes[i][0]) for i in pending}
        for i, future in futures.items():
            future.add_done_callback(keep(i))
        for future in futures.values():
            future.result()  # re-raises the first failure, in call order
```

With several calls running at once, the results are filed by a callback
the moment each call finishes, not when the main thread gets round to
collecting them. So a Ctrl-C that lands while the main thread waits on
the second call does not lose the third call's result.

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
declines it and stores a deny. Both are stored under the tool's name and,
for bash, under the first word of every part of the command. `y` and `n`
are not stored: they answer one call.

### 6. The session rules

`harness/permissions.py`:

```python
SESSION_RULES = {}  # (tool, first word) -> "allow" or "deny", from the a and never answers of this session
...
def rate(part):
    """One command's verdict: a session rule first, then BASH_RULES. A deny in BASH_RULES wins."""
    action = "ask"
    for pattern, rule in BASH_RULES.items():
        if fnmatch(part, pattern):
            action = rule
    remembered = SESSION_RULES.get(("bash", first_word(part)))
    if remembered and action != "deny":
        action = remembered
    return action
```

A bash command is rated one part at a time, as before. For each part the
session rule for its first word is consulted before the static rules take
effect, with one exception: a `deny` in `BASH_RULES` still wins. An `a`
on `git commit` allows `git log` and `git commit` for the session and
leaves `git push` denied, because nothing said at the prompt unlocks the
deny list. For every other tool the key is the tool name alone, so an `a`
on one `computer_act` click allows every click until the session ends.
The eval runner empties the rules for each task and puts them back after.

## Run it

```bash
cd step_35_human_in_the_loop
pip install -e .
harness
```

Ask for something with a choice in it:

```text
> add a test runner config
```

The model calls `ask_user`, the question and the options print with
numbers, and the `answer>` prompt waits. Type `2` or the text of the
choice. The answer shows up as the tool result, and the model goes on
with it. In plan mode the tool is still there, so the question can come
before the plan.

Then interrupt a turn. While the spinner runs or a command is running,
press Ctrl-C once:

```text
  interrupted the tool calls. Type a message to steer, press enter to go on, or ctrl-c again to exit
  steer> look in src/ not in tests/
```

The interrupted call gets `INTERRUPTED` as its result, the steering line
prints as a user message, and the next model call sees both. Press enter
with nothing typed to go on as before. Press Ctrl-C twice in quick
succession to exit; the transcript is saved and `--resume` picks it up.

At an approve prompt, answer `a`:

```text
  run: git commit -m "add config"
  allow? (y/n/a=always/never)> a
  remembered: allow for this session: bash git
```

The next `git commit` runs without a prompt. `git push` still does not.

Windows caveat: Ctrl-C is delivered to every process attached to the
console, so a command that `bash` is running gets it too and dies; the
harness sees the interrupt once the command has ended, and the result
recorded is `INTERRUPTED`. A wait on a thread pool cannot be interrupted
on Windows until the running calls return, so with several calls in
flight the steer prompt appears when they finish. A streamed reply is
interrupted at the next chunk. Background jobs from step 29 run in their
own process group and do not get the Ctrl-C. Ctrl-C at the input line,
outside a turn, exits as before.

## What to notice

- A question is a tool call. It goes through `decide` and `settle` like
  any other, is always allowed, and its answer is a tool result the model
  reads in the next request. Nothing in the loop knows the tool is special.
- The steering message is appended, not injected. It is a plain user
  message in the transcript, saved with the rest, replayed on `--resume`,
  and moved by compaction. The late block is for the harness; the user's
  words are the user's.
- Both handlers restore the invariant first and ask second. The API
  wants a result for every tool call, and `run_results` provides one for
  every call before the exception is raised again. A second Ctrl-C at the
  steer prompt leaves a transcript that `--resume` can send as is.
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
Changed: `agent.py` (`STEER_WINDOW`, `steer`, `steered`, the two
`KeyboardInterrupt` handlers in `turn`, `run_results` fills
`INTERRUPTED` and re-raises, `chat` ends on a `KeyboardInterrupt` from
`turn`, `-p` exits 130), `tools.py` (`ask_user` in `TOOL_SCHEMAS` and
`TOOLS`, `INTERRUPTED`, `settle` takes `name` and `args` and reads four
answers, `execute_all` takes `outcomes` and files results by callback),
`permissions.py` (`SESSION_RULES`, `first_word`, `session_keys`,
`remember`, `rate`, the session lookup in `check`), `ui.py` (`ANSWERS`,
`approve` returns the answer, `question`, `interrupted`, the banner),
`plan.py` (`ask_user` in `READ_ONLY`), `subagent.py` (`ask_user` in
`WITHHELD`), `llm.py` (the `ask_user` paragraph in the system prompt),
`evaluate.py` (`isolated` answers `y`, replaces `ask_user`, and resets
`SESSION_RULES`). Everything else is unchanged from step 34.
