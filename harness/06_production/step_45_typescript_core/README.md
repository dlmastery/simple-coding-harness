# Step 45 - The core loop in TypeScript

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Make a run inspectable**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 44 - Replay and trace viewer](../step_44_replay_trace/README.md). Next: [Step 46 - The loop on TrueForge](../../07_server/step_46_trueforge_loop/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** a second harness, in a second language. The
`harness-ts/` package is the stage 15 loop written in TypeScript: the
model call, the seven tools, the permission rules, the OS sandbox, the
cap / strip / fit trio, the compaction agent, the exploration subagent
and the slash commands. Same file names, same environment variables
(`API_KEY`, `BASE_URL`, `MODEL`, `CONTEXT_WINDOW`), same session
directory and the same JSONL log. A session written by the Python
harness resumes in TypeScript, and the other way round. The tests run
on node's own test runner against a fake client, so `npm test` needs
no packages installed and no network; `npm run typecheck` runs `tsc`
under `strict` once `npm install` has fetched it. Nothing in the
Python `harness/` changes; it is the step 44 code, carried forward,
and it is the final Python harness of the series: every cross-cutting
fix of the review round is in this copy.

## Files

```text
step_45_typescript_core/
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
├── harness-ts/                       the TypeScript port of the stage 15 loop; no build step
│   ├── package.json                  npm start / test / typecheck; node >= 22.6; version 0.45.0
│   ├── tsconfig.json                 strict, noEmit, nodenext: what `npm run typecheck` checks
│   ├── types.ts                      the shapes shared by every module; nothing here runs
│   ├── config.ts                     settings; same env vars and env file as config.py
│   ├── llm.ts                        one model call and the system prompt; client set lazily
│   ├── tools.ts                      the seven tools, parseArgs and execute(), which never rejects
│   ├── agent.ts                      the loop: turn() and main(); every await is a Python block
│   ├── context.ts                    the late injection: env block, todos, files git saw change
│   ├── session.ts                    the same JSONL log as session.py; resumes Python sessions
│   ├── permissions.ts                which tool calls need a human; rules as an ordered array
│   ├── sandbox.ts                    an OS sandbox for bash; run() kills the process group on timeout
│   ├── history.ts                    cap / strip / fit; fit() takes the budget as an argument
│   ├── compact.ts                    the compaction agent; summarize() and compact() return promises
│   ├── subagent.ts                   exploration subagents through the task tool
│   ├── skills.ts                     the same SKILL.md files, read with a small front-matter parser
│   ├── todos.ts                      the plan: write_todos validates, then replaces the whole list
│   ├── commands.ts                   the slash commands: /rewind, /sessions, /compact, /exit
│   ├── ui.ts                         the screen in plain console output, ANSI colours on a tty
│   └── tests/                        node:test suites per module, fake.ts client, session_bridge.ts, fixtures/
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
├── test_step.py                      runs the node suite and the cross-language session test
├── pyproject.toml                    package metadata; version 0.45.0
└── README.md                         this file
```

## Why a second language

Forty-four steps built one harness in one language. It is easy to lose
track of which parts are the harness and which parts are Python. The
port draws that line. The loop, the tool registry, the permission
verdicts, the log format and the four subagent rules come across almost
line for line. What does not come across is the shape of waiting: where
Python blocks, TypeScript awaits, and where Python starts a thread,
TypeScript already has a promise. Those places are the ones worth
seeing side by side.

The port runs without a build step. Node 22.6 and newer strip type
annotations on load (`node --experimental-strip-types`), so the files
are plain `.ts`, imported with their `.ts` extension, and there is no
bundler and no `dist/`. The annotations are for the reader, the editor
and `tsc`: `npm run typecheck` checks them under `strict` without
emitting anything, and `test_step.py` runs the same check when
`typescript` is installed.

### What breaks without it

Not the Python harness: nothing there changes. What the port catches
is the difference between "the harness" and "how Python does it". The
stage 15 loop ported line for line would have shipped with stage 15's
holes - a tool call with malformed arguments, an unknown tool name or a
tool that throws would end the process with an unhandled rejection and
a log ending in an unanswered call. Steps 38 and later closed those in
Python; the port ships the closed version, and its tests hold it.

## Python file to TypeScript file

| Python (`harness/`)  | TypeScript (`harness-ts/`) | What changes in the port |
|----------------------|----------------------------|--------------------------|
| `config.py`          | `config.ts`                | `os.environ.setdefault` becomes `process.env[key] ??=` |
| `llm.py`             | `llm.ts`                   | the client is created on the first call; `entry()` replaces `StreamedMessage.model_dump` |
| `tools.py`           | `tools.ts`                 | tools take one args object; `execute()` is `async` and never rejects |
| `agent.py`           | `agent.ts`                 | the inner loop is `turn()`; `main()` awaits the prompt |
| `context.py`         | `context.ts`               | `spawnSync("git ...")` in place of `subprocess.run` |
| `session.py`         | `session.ts`               | `CURRENT` and `WRITTEN` live on one `state` object |
| `permissions.py`     | `permissions.ts`           | the rules are an ordered array; `fnmatch` is written out |
| `history.py`         | `history.ts`               | `fit()` takes the budget as an argument, for the tests |
| `compact.py`         | `compact.ts`               | `summarize()` and `compact()` return promises |
| `subagent.py`        | `subagent.ts`              | `tools.ts` is imported inside `task()`, as in Python |
| `ui.py`              | `ui.ts`                    | plain console output; `ask()` and `approve()` are `async` |
| `sandbox.py`         | `sandbox.ts`               | `spawn` and a timer in place of `subprocess.run(timeout=)` |
| `todos.py`, `skills.py`, `commands.py` | same names | skills read front matter with a small key: value reader |
| `test_step.py`       | `tests/*.test.ts`          | `node:test` and a fake client; `test_step.py` runs them |

## The code, piece by piece

### 1. The loop

`harness-ts/agent.ts`:

```ts
export async function turn(messages: Message[], userInput: string, debug = false): Promise<Message[]> {
  messages.push({ role: "user", content: userInput });
  let usage = NO_USAGE;

  while (true) {
    const injection = reminder();
    ui.injection(injection.content);

    if (history.fit(messages)) {
      ui.note("dropped old tool output to make this request fit");
    }

    const done = ui.working(activeForm());
    let message;
    try {
      ({ message, usage } = await callLlm([...messages, injection]));
    } finally {
      done();
    }

    messages.push(entry(message));
    session.save(messages);
    ui.usage(usage);
    ...
    if (!message.tool_calls?.length) {
      break;
    }

    for (const toolCall of message.tool_calls) {
      const [args, result] = await execute(toolCall);
      ui.tool(toolCall.function.name, args, result);

      messages.push({
        role: "tool",
        tool_call_id: toolCall.id,
        content: result,
      });
      session.save(messages); // after every message, so a crash loses nothing
    }
  }

  history.sweep(); // the turn is over: bin its temp files...
  history.strip(messages); // ...and shrink the tool output it produced

  if (compact.needed(usage)) {
    messages = await commands.compact(messages);
  }
  return messages;
}
```

Read it next to the inner `while True` of the Python `turn()`. The
order of events is the same: the late injection is built and shown,
`fit` runs, the spinner starts, the model answers, the reply is
appended and saved, each tool call runs and its result is appended and
saved. Every `await` marks a place where the Python loop blocks. The
one structural change is that the inner loop is a function, `turn()`,
so a test can drive one turn without a keyboard.

`harness-ts/agent.ts`:

```ts
    if (userInput === null || userInput === "/exit" || userInput === "/quit") {
      break; // ctrl-d, ctrl-c at the prompt, or the command: the transcript is saved
    }
    if (!userInput) {
      continue; // an empty line is not a message
    }
...
  main().catch((failure) => {
    // a model call that failed for good, or anything else the loop did not expect:
    // one line, exit 1, and the transcript on disk is whole - --resume picks it up
    console.error(`harness: ${failure?.message ?? failure}`);
    process.exit(1);
  });
```

`main()` is the outer loop. `ui.ask()` returns `null` for ctrl-d or
ctrl-c at the prompt and `""` for an empty line; the first leaves, the
second asks again. The one `.catch` at the bottom is where every
rejection the loop does not handle ends: one line on stderr, exit
code 1, no stack trace. The transcript was saved after every message,
so `--resume` opens it.

### 2. One model call, and the fake client

`harness-ts/llm.ts`:

```ts
let client: Client | null = null;

/** Replace the client. The tests inject a fake; null goes back to the real one. */
export function setClient(replacement: Client | null): void {
  client = replacement;
}

async function getClient(): Promise<Client> {
  if (client === null) {
    const { default: OpenAI } = await import("openai");
    client = new OpenAI({ baseURL: config.BASE_URL, apiKey: config.API_KEY }) as unknown as Client;
  }
  return client;
}
```

The Python module creates `OpenAI(...)` at import time. Here the import
of the `openai` package is a dynamic `import()` inside `getClient()`, so
it happens on the first real call and never in the tests. A test calls
`setClient(fakeClient([...]))` and the loop talks to an object with one
method, `chat.completions.create`. The `Client` type in `types.ts` is
that one method; the real client satisfies it and so does the fake.

`harness-ts/llm.ts`:

```ts
export function entry(message: Reply): Message {
  const out: Message = { role: "assistant", content: message.content ?? null };
  if (message.tool_calls?.length) {
    out.tool_calls = message.tool_calls.map((call) => ({
      id: call.id,
      type: "function",
      function: { name: call.function.name, arguments: call.function.arguments },
    }));
  }
  return out;
}
```

The Python loop appends `message.model_dump(exclude_none=True)`, which
step 21's `StreamedMessage` pins to three keys: `role`, `content`, and
`tool_calls` when there are any. The JS client returns a plain object
with explicit nulls and extras - `refusal`, `annotations`, a reasoning
model's `reasoning` - and none of that may go back to the server on the
next request, so `entry()` builds the same three keys by hand.
`content` stays, `null` included, because that is the shape the API
sends; a reply with an empty `tool_calls` array becomes an entry with
no `tool_calls` key at all, which is what Python writes.

### 3. The permission-checked executor

`harness-ts/tools.ts`:

```ts
export function parseArgs(toolCall: ToolCall): [Args, string | null] {
  let args: unknown;
  try {
    args = JSON.parse(toolCall.function.arguments || "{}");
  } catch (failure) {
    return [{}, (failure as Error).message];
  }
  if (typeof args !== "object" || args === null || Array.isArray(args)) {
    return [{}, `got ${Array.isArray(args) ? "array" : typeof args}, not an object`];
  }
  return [args as Args, null];
}
...
export async function execute(toolCall: ToolCall): Promise<[Args, string]> {
  const name = toolCall.function.name;
  const [args, problem] = parseArgs(toolCall);
  if (problem !== null) {
    return [args, `Error: the arguments of ${name} are not a JSON object: ${problem}`];
  }
  const fn = TOOLS[name];
  if (fn === undefined) {
    return [args, `Error: no tool named '${name}'.`];
  }
  const [action, reason] = check(name, args);
  if (action === "deny") {
    return [args, `Blocked by policy: ${reason}`];
  }
  if (action === "ask" && !(await ui.approve(reason))) {
    return [args, "The user denied this tool call."];
  }
  try {
    return [args, await fn(args)];
  } catch (failure) {
    // a missing file or a wrong argument is the model's problem to fix
    const error = failure as Error;
    return [args, `Error: ${error?.name ?? "Error"}: ${error?.message ?? String(failure)}`];
  }
}
```

The same steps as `tools.execute` in Python, with the same strings:
parse, look the tool up, check, deny or ask, run. Nothing rejects out
of `execute`. Arguments that are not a JSON object, a name the
registry does not have, and an exception inside the tool (a
`readFileSync` on a missing path is the common one) each come back as
an `Error:` result, so every tool call gets exactly one tool message
and the transcript stays one the API accepts. Two awaits appear.
`ui.approve` reads a line from the keyboard, and in node that is a
callback wrapped in a promise. The tool itself may be `bash`, which
spawns a process and resolves later. A tool that runs at once, such as
`read_file`, returns a plain string; `await` on a string is a no-op,
so the registry can hold both.

Python spreads the parsed arguments as keyword arguments,
`TOOLS[name](**args)`. TypeScript has no keyword arguments, so every
tool takes the object whole and destructures it in its signature:
`bash({ command })`, `strReplace({ path, old_str, new_str, allow_multi_edit = false })`.
The registry maps the model-facing names to the functions, as before.
Its type is `Record<string, Tool>` with `Tool = (args: any) => ...`:
each tool narrows its own parameter, and under `strictFunctionTypes` a
narrower parameter does not fit a shared signature, so `any` is the
honest type there - the model's JSON is untyped, and `execute` catches
what does not fit at run time.

`harness-ts/permissions.ts`:

```ts
export function check(name: string, args: Args): [Action, string | null] {
  if (name === "bash") {
    if (typeof args.command !== "string") return ["deny", `${name}: missing argument 'command'`];
    return [decide(args.command), `run: ${args.command}`];
  }
  if (name === "write_file" || name === "str_replace") {
    if (typeof args.path !== "string") return ["deny", `${name}: missing argument 'path'`];
    if (!insideProject(args.path)) return ["ask", `${name} outside ${PROJECT}: ${args.path}`];
  }
  return ["allow", null];
}
```

The rules read `command` and `path`. A call without them is denied
with a reason that names the missing argument, the way the Python
`permissions.missing` does, instead of `splitCommand(undefined)`
throwing inside the check.

### 4. The session log, shared with Python

`harness-ts/session.ts`:

```ts
export const PROJECT = [...resolve(process.cwd())].map((c) => (/^[\p{L}\p{N}]$/u.test(c) ? c : "-")).join("");
export const SESSION_DIR = join(homedir(), ".simple-harness", "sessions", PROJECT);
...
export const state = {
  dir: SESSION_DIR,
  current: stamp(),
  written: 0, // how many messages are already on disk
};
...
/** Append what is new. Never rewrite what is already on disk. */
export function save(messages: Message[]): void {
  for (const message of messages.slice(state.written)) {
    append(message);
  }
  state.written = messages.length;
}

/** Record a rewind as an entry, so the old messages stay in the file. */
export function rewindTo(count: number): void {
  append({ rewind_to: count });
  state.written = count;
}
```

`PROJECT` is the working directory with every non-alphanumeric
character turned into a dash, the same rule as
`"".join(c if c.isalnum() else "-" ...)` in Python, so both harnesses
put the log for one project in one directory. The Python module keeps
`CURRENT` and `WRITTEN` as module globals and tests reassign them
through `monkeypatch`. An ES module export cannot be assigned from
outside, so the two values sit on one exported `state` object instead.

`harness-ts/session.ts`:

```ts
    delete entry.ts;
    if ("usage" in entry) {
      continue;
    }
    if ("rewind_to" in entry) {
      messages.splice(entry.rewind_to as number);
    } else if ("compacted" in entry) {
      messages = [...(entry.compacted as Message[])];
    } else if ("role" in entry) {
      messages.push(entry as Message);
    }
```

`load()` replays the log the way the Python one does: messages
accumulate, a `rewind_to` cuts them back, a `compacted` entry replaces
them. Two lines look back to step 44, where the Python harness stamps
every entry with `ts` and writes a `usage` entry after each model call.
The model never saw either, so `load()` drops the stamp and skips the
usage entry, and a log from any Python step resumes here. For
comparison, the Python side:

`harness/session.py`:

```python
        entry.pop("ts", None)
        if "usage" in entry:
            continue  # the numbers of a model call: replay and trace read them, the model does not
        if "rewind_to" in entry:
            del messages[entry["rewind_to"]:]
        elif "compacted" in entry:
            messages = list(entry["compacted"])
```

The tests hold both directions. `tests/fixtures/python_session.jsonl` is
the exact output of a Python `session.save`, `rewind_to` and
`compacted` sequence, and `session.test.ts` loads it. `test_step.py`
runs `tests/session_bridge.ts` to write a log from TypeScript and loads
it with the Python `session.load`, then writes one with Python and
loads it with the TypeScript side.

What crosses the line and what does not: a `{"handoff": name}` marker
from step 40 is skipped, so a Python session that ended in the
`reviewer` agent resumes here as the plain stage 15 agent with the
stage 15 prompt; an image message from step 24 (a `user` message whose
`content` is a list) is passed to the model unchanged, which works
only if the model accepts image parts; and a log written by the port
has no `ts` and no usage entries, so `harness replay` of it runs
without pauses and `harness trace` shows dashes in the number columns.

### 5. The subagent

`harness-ts/subagent.ts`:

```ts
export async function task({ description }: { description: string }): Promise<string> {
  // Imported here, not at the top: tools imports us, and we need tools. A
  // top-level import would run before TASK_SCHEMA exists on that side.
  const { callLlm, entry } = await import("./llm.ts");
  const { execute } = await import("./tools.ts");

  // rule 1: two messages, born here, dead at the return
  const messages: Message[] = [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "user", content: description },
  ];
  ui.subagent(description);
  let report: string | null = null; // newest thing it has said, kept in case we run out of turns

  // rule 3: the loop from agent.ts, pointed at a different list
  for (let turn = 0; turn < MAX_TURNS; turn++) {
    fit(messages); // its context can overflow too, and nobody compacts it
```

The four rules of step 15 hold: an empty history, four tools withheld,
the same loop, only the final `content` returned. The import cycle is
the same one Python has. `tools.py` imports `subagent.py` for the task
schema, and `subagent.task` imports `tools` inside the function. The
port does the same with a dynamic `import()`. A static import at the
top of `subagent.ts` would run while `tools.ts` was still loading, and
`TASK_SCHEMA` would not exist yet on that side.

### 6. Where the two languages differ in practice

Three places in the port are not a line-for-line translation. Each one
is about waiting.

**Streams.** The Python `bash` tool of stage 15 called `sandbox.run`,
which blocks until the command exits and hands back the whole output
(the function is still in `sandbox.py`, though since step 42 `bash`
goes through `streaming.run` instead):

`harness/sandbox.py`:

```python
def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us. Raises TimeoutExpired with the partial output.
    ...
    sandboxed = wrap(command)
    group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(
        sandboxed or command,
        shell=sandboxed is None,
        stdin=subprocess.DEVNULL,  # a command that waits for input would hang the turn
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        env=ENV,
        **group,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
```

Node has no blocking call that also captures output. `spawn` returns at
once with two streams, and the output arrives in `data` events. The
port collects the chunks and settles when the process exits; the
timeout is a timer that kills the process group and makes the promise
reject with a `TimedOut` that carries the partial output, which `bash`
turns into the result `Timed out after 60s and was killed. Output so
far: ...`:

`harness-ts/sandbox.ts`:

```ts
  return new Promise((done, fail) => {
    let stdout = "";
    let stderr = "";
    let expired = false;
    let settled = false;
    child.stdout.setEncoding("utf-8");
    child.stderr.setEncoding("utf-8");
    child.stdout.on("data", (chunk: string) => (stdout += chunk));
    child.stderr.on("data", (chunk: string) => (stderr += chunk));
    const timer = setTimeout(() => {
      expired = true;
      kill(child.pid, child);
    }, timeout * 1000);
    const settle = () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (expired) fail(new TimedOut(timeout, stdout + stderr));
      else done({ stdout, stderr });
    };
    child.on("error", (failure) => {
      clearTimeout(timer);
      settled = true;
      fail(failure);
    });
    child.on("close", settle); // the pipes closed: the output is complete
    child.on("exit", () => setTimeout(settle, DRAIN_MS)); // or the process is gone and a child still holds the pipe: settle anyway
  });
```

Two events end a spawned process: `exit`, when the process is gone,
and `close`, when its output pipes have closed. They are not the same
moment: a command that started a child and was killed leaves that
child holding the pipes, and `close` never fires. Waiting on `close`
alone would hang the turn. The port settles on `close` when it comes
and `DRAIN_MS` (200 ms) after `exit` otherwise, whichever is first.

Step 42 added a `Reader` thread to Python so lines could reach the
screen as they arrived. The TypeScript side has that already: the
`data` handler is already called per chunk, and forwarding each chunk
to the screen is one more line in it.

**Threads versus promises.** Step 22 runs the tool calls of one reply
in parallel. Python needs a thread pool for that, because `bash` blocks
the thread it runs on:

`harness/tools.py`:

```python
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
```

The stage 15 port runs tool calls one after another, which is what
stage 15 did: `for (const toolCall of message.tool_calls) { await
execute(toolCall) }`. Making them parallel needs no pool and no thread.
Every tool already returns a promise, so the loop becomes one call:
`await Promise.all(message.tool_calls.map(execute))`, and node's event
loop interleaves the spawned processes. What the pool gave Python, the
runtime gives TypeScript - including the ctrl-c problem the Python
version has to handle by hand (`shutdown(wait=False,
cancel_futures=True)`, so a second ctrl-c does not wait for a 60 s
command). The cost is on the other side: a CPU-bound tool would block
the whole process, where Python would have run it on its own thread.

**Sandbox spawning.** Both harnesses ask `wrap(command)` for an argv
that runs the command inside seatbelt or bubblewrap, or `null` when the
OS has neither. Python passes either form to one call and lets
`shell=` pick: `subprocess.run(sandboxed or command, shell=sandboxed is
None)`. Node splits the two cases, because `spawn` takes a program and
an argument list, and `shell: true` changes how the first argument is
read:

`harness-ts/sandbox.ts`:

```ts
  const sandboxed = wrap(command);
  const options = {
    stdio: ["ignore", "pipe", "pipe"] as ["ignore", "pipe", "pipe"],
    env: { ...process.env, ...ENV },
    detached: process.platform !== "win32", // its own process group, so kill() can reach its children
  };
  const child = sandboxed ? spawn(sandboxed[0], sandboxed.slice(1), options) : spawn(command, { ...options, shell: true });
```

Killing on timeout is the same idea as step 42's `streaming.kill` in
Python. `child.kill()` signals one process; a shell that started a
child leaves that child running. On POSIX the command is spawned
`detached`, which puts it in a process group of its own, and
`process.kill(-pid, "SIGKILL")` signals the whole group - the
`start_new_session` and `killpg` pair of the Python version. On
Windows the port runs `taskkill /T /F` on the process id, so the whole
tree goes. `ENV` adds `PAGER=cat`, `GIT_PAGER=cat` and
`GIT_TERMINAL_PROMPT=0`, so a `git log` does not wait on a pager and a
`git push` to a private remote fails instead of waiting for a password
on a terminal it does not have. The seatbelt profile is the Python one,
temp directory included, so `pytest` and `npm` can write their caches
under it on macOS.

### 7. The tests

`harness-ts/tests/fake.ts`:

```ts
export function fakeClient(replies: Reply[], requests: Request[] = []): Client {
  return {
    chat: {
      completions: {
        async create(request: Request): Promise<Completion> {
          requests.push({ ...request, messages: structuredClone(request.messages) }); // a snapshot: the loop mutates its list
          const message = replies.shift() ?? { content: "(out of scripted replies)", tool_calls: null };
          return { choices: [{ message }], usage: USAGE };
        },
      },
    },
  };
}
```

The fake is the same pattern as the Python `FakeMessage`: scripted
replies in order, and every request recorded so a test can check what
the loop sent. The tests mirror the Python ones for the loop, the
permissions, cap / strip / fit, compaction and the subagent, plus the
two session tests, and the ones the review round added: a reply with
malformed arguments, an unknown tool, a tool that throws and a call
without its argument each get one tool message; a UTF-8 round trip
through the file tools; a command that outlives its timeout is killed
and its partial output comes back; `write_todos` with a bad status is
an error that leaves the list alone; `entry()` drops what the server
sent along. `tests/fake.ts` also builds a temp workspace: it points the
permission fence, the session store and the working directory at one
temp directory, and makes `ui.approve` answer yes.

`test_step.py` runs the node suite with a subprocess and skips, the way
`pytest.importorskip` would, when `shutil.which("node")` is `None` or
the version is below 22.6. It runs `tsc -p .` over `harness-ts/` when
`npm install` has put `typescript` in `harness-ts/node_modules`, and
skips with a note otherwise. The two cross-language tests use
`tests/session_bridge.ts`, a small script that writes or loads a
session with the TypeScript module. The Python `harness/` from step 44
gets an import smoke test; its own suite is step 44's.

## Run it

Prerequisites: node 22.6 or newer; `API_KEY` (and `BASE_URL`, `MODEL`)
in the environment for a real session. `npm test` needs no packages.
`npm start` needs the `openai` package and `npm run typecheck` needs
`typescript` and `@types/node`; one `npm install` fetches all three
into `harness-ts/node_modules/`, which the repository's `.gitignore`
excludes.

bash:

```bash
cd harness-ts
npm install          # openai for a real session, typescript for the type check
npm run typecheck    # tsc -p .  - strict, emits nothing
npm start            # node --experimental-strip-types agent.ts
```

PowerShell:

```powershell
cd harness-ts
npm install
npm run typecheck
npm start
```

The banner, the prompt and the panels look like the Python ones, drawn
in plain text. Ask for something:

```text
> list the files in this directory and count them
```

Expected output:

```text
── coding agent ────────────────────────────────────────
  sandbox: none  ·  /sessions  /rewind  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave

> list the files in this directory and count them

  ┌──────────────────────────────────────────────────────────┐
  │ late injection                                           │
  │                                                          │
  │ <env>                                                    │
  │ time: 2026-09-18 21:40                                   │
  │ git branch: main                                         │
  │ </env>                                                   │
  └──────────────────────────────────────────────────────────┘

  1,912 prompt · 27 completion

  ┌──────────────────────────────────────────────────────────┐
  │ bash ls | wc -l                                          │
  │                                                          │
  │ 19                                                       │
  └──────────────────────────────────────────────────────────┘

  2,001 prompt · 14 completion · 1,920 cached

  agent

  There are 19 entries in this directory.
```

The late injection prints first, dimmed, then the `bash` panel with the
command and the first lines of its output, then the agent's answer and
the token line. A command the rules rate as `ask` stops at
`allow? (y/n)>`, as in step 11. `/rewind`, `/sessions`, `/compact` and
`/exit` work as before. Start the Python harness in the same directory
with `harness --resume` and it opens the session the TypeScript one
just wrote; `npm start -- --resume` does the reverse.

Run the tests from `harness-ts/` (no install needed):

```bash
npm test             # node --experimental-strip-types --test "tests/*.test.ts"
```

Thirty tests, TAP output, `# fail 0` at the end. Or from the
repository root, which also runs the type check and the cross-language
checks:

```bash
python run_tests.py 45
python check_snippets.py 45
```

```powershell
python run_tests.py 45
python check_snippets.py 45
```

## Error handling

The port, `harness-ts/`:

- **A tool call with broken arguments** gets `Error: the arguments of
  <name> are not a JSON object: ...`; an unknown tool `Error: no tool
  named 'x'.`; a tool that throws `Error: <name>: <message>` (a missing
  file is `Error: Error: ENOENT: no such file or directory, ...`);
  `bash` without a `command` is `Blocked by policy: bash: missing
  argument 'command'`. Each is one tool message and the loop goes on.
- **A failing command** comes back as its stdout and stderr; one that
  runs past 60 s is killed with its process group and the result starts
  `Timed out after 60s and was killed. Output so far:`.
- **Ctrl-C at a prompt** (`>`, `allow?`, `number>`) closes the readline
  interface: at `>` the chat ends, at `allow?` the call is declined, at
  `number>` nothing is picked. Ctrl-C during a model call or a tool
  call is node's default: the process exits with code 130, no summary,
  no steering prompt. The log is whole up to the last saved message.
- **A dead model call** (no network, a bad key, a 429 or 5xx) gets only
  the `openai` client's own two retries; then the rejection reaches
  `main().catch`, which prints `harness: <message>` and exits 1. A 200 with no `choices` is turned
  into an error with the server's message instead of a `TypeError`.
  `--resume` opens the log again.
- **Leaving:** `/exit`, `/quit`, ctrl-d (ctrl-z then enter on Windows),
  or ctrl-c at the prompt.

The Python `harness/` here is step 44's, so its behaviour is step 44's
README: error strings for every bad call, `INTERRUPTED` results on
ctrl-c, a note and a valid transcript on a dead model call, `recover()`
on resume.

## Gotchas / What this is not

What the port leaves out, by design - it is stage 15, not step 44:

- no cap on model calls per turn, no retry of its own (the `openai`
  client retries twice, then the process ends), no loop detector, no
  stop conditions, no cost;
- sequential tool calls, no streaming of the reply or of tool output,
  no background jobs;
- no checkpoints or `/undo`, no hooks, no MCP, no modes or plan mode,
  no agent definitions or handoffs, no memory, no extensions;
- no `-p` headless mode, no `eval`, no `replay` or `trace`, no
  `recover()` of a dangling tool call on `--resume` (such a log resumes
  with the call unanswered, and the next model call is refused by the
  API - `/rewind` to the last user message first);
- no image messages: a Python log with a screenshot is passed through
  as is.

What behaves differently from the Python harness:

- **Ctrl-C** is not a steer: at a prompt it ends or declines, elsewhere
  it ends the process (section above).
- **The tool named `bash` runs through `cmd.exe` on Windows**, exactly
  as in Python (`spawn(command, { shell: true })`), and there is no OS
  sandbox on Windows; the banner says `sandbox: none`.
- **The deny list is Unix-shaped**: `rm`, `sudo`, `curl`; a `del /s` or
  `Remove-Item -Recurse` is an `ask`, not a `deny`.
- **Handoff markers are dropped** on load, image messages are passed
  through, a TS-written log has no stamps (section 4).
- **`npm install` is only for a real session or the type check.** The
  tests and the cross-language checks run on a bare node 22.6+.
- **Types are for the reader, and now for `tsc`.** Node strips them on
  load, so `npm test` would pass with every annotation deleted;
  `npm run typecheck` is what holds them to the code. `Tool` is
  `(args: any) => ...` on purpose (section 3).
- **The Python harness in this step is the final one.** It is
  byte-identical to step 44's, and every fix of the review round -
  the error path for every tool call, the UTF-8 file tools, the
  process-group kill, `write_todos` validation, `/rewind` on user
  messages only, the fenced subagent tool set, extension permissions,
  the hook `ok` flag, the OpenRouter cost - is in it. Step 44's README
  describes its behaviour; step 43's, the extensions.

## Diff from step 44

```bash
diff -r ../step_44_replay_trace/harness harness
```

No difference. Added: `harness-ts/` (`package.json`, `tsconfig.json`,
`types.ts`, `config.ts`, `llm.ts`, `tools.ts`, `agent.ts`,
`context.ts`, `session.ts`, `permissions.ts`, `history.ts`,
`compact.ts`, `subagent.ts`, `ui.ts`, `sandbox.ts`, `todos.ts`,
`skills.ts`, `commands.ts`, and `tests/` with `fake.ts`,
`session_bridge.ts`, seven `*.test.ts` files and
`fixtures/python_session.jsonl`). Changed: `test_step.py` (runs the
node suite, the type check and the two cross-language session tests),
`pyproject.toml` (version). Everything else is unchanged from step 44.

## What the next step adds

Step 46 leaves the hand-built harness behind: the stage 2.4 loop runs
on TrueForge, an agent server, and the step is the client - a `chat()`
that streams one turn back as events, a REPL with `--resume` and `-p`,
and a setup script that registers the model provider. The five steps
after it map each capability built here onto that server.
