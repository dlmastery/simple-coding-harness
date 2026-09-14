# Step 45 - The core loop in TypeScript

**What this step adds:** a second harness, in a second language. The
`harness-ts/` package is the stage 15 loop written in TypeScript: the
model call, the seven tools, the permission rules, the OS sandbox, the
cap / strip / fit trio, the compaction agent, the exploration subagent
and the slash commands. Same file names, same environment variables
(`API_KEY`, `BASE_URL`, `MODEL`, `CONTEXT_WINDOW`), same session
directory and the same JSONL log. A session written by the Python
harness resumes in TypeScript, and the other way round. The tests run
on node's own test runner against a fake client, so `npm test` needs
no packages installed and no network. Nothing in the Python `harness/`
changes; it is the step 44 code, carried forward.

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
│   ├── package.json                  npm start / npm test; node >= 22.6; version 0.45.0
│   ├── types.ts                      the shapes shared by every module; nothing here runs
│   ├── config.ts                     settings; same env vars and env file as config.py
│   ├── llm.ts                        one model call and the system prompt; client set lazily
│   ├── tools.ts                      the seven tools and execute(), the permission-checked entry
│   ├── agent.ts                      the loop: turn() and main(); every await is a Python block
│   ├── context.ts                    the late injection: env block, todos, files git saw change
│   ├── session.ts                    the same JSONL log as session.py; resumes Python sessions
│   ├── permissions.ts                which tool calls need a human; rules as an ordered array
│   ├── sandbox.ts                    an OS sandbox for bash
│   ├── history.ts                    cap / strip / fit; fit() takes the budget as an argument
│   ├── compact.ts                    the compaction agent; summarize() and compact() return promises
│   ├── subagent.ts                   exploration subagents through the task tool
│   ├── skills.ts                     the same SKILL.md files, read with a small front-matter parser
│   ├── todos.ts                      the plan: write_todos replaces the whole list
│   ├── commands.ts                   the slash commands: /rewind, /sessions, /compact
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
│   ├── durability.py                 the loop detector and the crash-recovery scan
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
`tsc`, no bundler and no `dist/`. The type annotations are there for
the reader and the editor; the runtime ignores them.

## Python file to TypeScript file

| Python (`harness/`)  | TypeScript (`harness-ts/`) | What changes in the port |
|----------------------|----------------------------|--------------------------|
| `config.py`          | `config.ts`                | `os.environ.setdefault` becomes `process.env[key] ??=` |
| `llm.py`             | `llm.ts`                   | the client is created on the first call; `entry()` replaces `model_dump(exclude_none=True)` |
| `tools.py`           | `tools.ts`                 | tools take one args object; `execute()` is `async` |
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

Read it next to the inner `while True` of the Python `main()`. The
order of events is the same: the late injection is built and shown,
`fit` runs, the spinner starts, the model answers, the reply is
appended and saved, each tool call runs and its result is appended and
saved. Every `await` marks a place where the Python loop blocks. The
one structural change is that the inner loop is a function, `turn()`,
so a test can drive one turn without a keyboard.

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
  const out: Message = { role: "assistant" };
  for (const [key, value] of Object.entries(message)) {
    if (value !== null && value !== undefined && key !== "role") out[key] = value;
  }
  if (message.tool_calls?.length) {
    out.tool_calls = message.tool_calls.map((call) => ({
      id: call.id,
      type: "function",
      function: { name: call.function.name, arguments: call.function.arguments },
    }));
  } else {
    delete out.tool_calls;
  }
  return out;
}
```

The Python loop appends `message.model_dump(exclude_none=True)`. The JS
client returns a plain object with explicit nulls and no `model_dump`,
so `entry()` does the same job by hand: it keeps every field that is
set, drops the nulls, and pins the tool calls to the three-key shape the
session log expects. A reply with an empty `tool_calls` array becomes an
entry with no `tool_calls` key at all, which is what Python writes.

### 3. The permission-checked executor

`harness-ts/tools.ts`:

```ts
export async function execute(toolCall: ToolCall): Promise<[Args, string]> {
  const args: Args = JSON.parse(toolCall.function.arguments);
  const [action, reason] = check(toolCall.function.name, args);
  if (action === "deny") {
    return [args, `Blocked by policy: ${reason}`];
  }
  if (action === "ask" && !(await ui.approve(reason))) {
    return [args, "The user denied this tool call."];
  }
  return [args, await TOOLS[toolCall.function.name](args)];
}
```

Four lines of logic, the same four as `tools.execute` in Python: parse,
check, deny or ask, run. Two awaits appear. `ui.approve` reads a line
from the keyboard, and in node that is a callback wrapped in a promise.
The tool itself may be `bash`, which spawns a process and resolves
later. A tool that runs at once, such as `read_file`, returns a plain
string; `await` on a string is a no-op, so the registry can hold both.

Python spreads the parsed arguments as keyword arguments,
`TOOLS[name](**args)`. TypeScript has no keyword arguments, so every
tool takes the object whole and destructures it in its signature:
`bash({ command })`, `strReplace({ path, old_str, new_str, allow_multi_edit = false })`.
The registry maps the model-facing names to the functions, as before.

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
them. Two lines look ahead to step 44, where the Python harness stamps
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

**Streams.** The Python `bash` tool calls `subprocess.run`, which
blocks until the command exits and hands back the whole output:

`harness/sandbox.py`:

```python
def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us."""
    sandboxed = wrap(command)
    return subprocess.run(
        sandboxed or command,
        shell=sandboxed is None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
```

Node has no blocking call that also captures output. `spawn` returns at
once with two streams, and the output arrives in `data` events. The
port collects the chunks and resolves on `close`; the timeout is a
timer that kills the process and makes the promise reject with the
same `TimedOut` shape `bash` turns into a result:

`harness-ts/sandbox.ts`:

```ts
  return new Promise((done, fail) => {
    let stdout = "";
    let stderr = "";
    let expired = false;
    child.stdout.setEncoding("utf-8");
    child.stderr.setEncoding("utf-8");
    child.stdout.on("data", (chunk: string) => (stdout += chunk));
    child.stderr.on("data", (chunk: string) => (stderr += chunk));
    const timer = setTimeout(() => {
      expired = true;
      kill(child.pid, child);
    }, timeout * 1000);
    child.on("error", (failure) => {
      clearTimeout(timer);
      fail(failure);
    });
    child.on("close", () => {
      clearTimeout(timer);
      if (expired) fail(new TimedOut(timeout));
      else done({ stdout, stderr });
    });
  });
```

Step 42 added a `Reader` thread to Python so lines could reach the
screen as they arrived. The TypeScript side has that already: the
`data` handler is already called per chunk, and forwarding each chunk
to the screen is one more line in it.

**Threads versus promises.** Step 22 runs the tool calls of one reply
in parallel. Python needs a thread pool for that, because `bash` blocks
the thread it runs on:

`harness/tools.py`:

```python
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {i: pool.submit(run, tool_calls[i], outcomes[i][0]) for i in pending}
        for i, future in futures.items():
            future.add_done_callback(keep(i))
        for future in futures.values():
            future.result()  # re-raises the first failure, in call order
```

The stage 15 port runs tool calls one after another, which is what
stage 15 did: `for (const toolCall of message.tool_calls) { await
execute(toolCall) }`. Making them parallel needs no pool and no thread.
Every tool already returns a promise, so the loop becomes one call:
`await Promise.all(message.tool_calls.map(execute))`, and node's event
loop interleaves the spawned processes. What the pool gave Python, the
runtime gives TypeScript. The cost is on the other side: a CPU-bound
tool would block the whole process, where Python would have run it on
its own thread.

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
  const child = sandboxed
    ? spawn(sandboxed[0], sandboxed.slice(1), { stdio: ["ignore", "pipe", "pipe"] })
    : spawn(command, { shell: true, stdio: ["ignore", "pipe", "pipe"] });
```

Killing on timeout differs too. `child.kill()` signals one process; a
shell that started a child leaves that child running. On Windows the
port runs `taskkill /T /F` on the process id, so the whole tree goes,
the way step 42's `kill` does in Python.

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
two session tests. `tests/fake.ts` also builds a temp workspace: it
points the permission fence, the session store and the working
directory at one temp directory, and makes `ui.approve` answer yes.

`test_step.py` runs the node suite with a subprocess and skips, the way
`pytest.importorskip` would, when `shutil.which("node")` is `None` or
the version is below 22.6. The two cross-language tests use
`tests/session_bridge.ts`, a small script that writes or loads a
session with the TypeScript module. The Python `harness/` from step 44
gets an import smoke test; its own suite is not re-run here.

## Run it

Run the TypeScript harness (node 22.6 or newer):

```bash
cd harness-ts
npm install          # only the openai package, only for a real session
npm start            # node --experimental-strip-types agent.ts
```

The banner, the prompt and the panels look like the Python ones, drawn
in plain text. Ask for something:

```text
> list the files in this directory and count them
```

The late injection prints first, dimmed, then the `bash` panel with the
command and the first lines of its output, then the agent's answer and
the token line. A command the rules rate as `ask` stops at
`allow? (y/n)>`, as in step 11. `/rewind`, `/sessions` and `/compact`
work as before. Start the Python harness in the same directory with
`harness --resume` and it opens the session the TypeScript one just
wrote; `npm start -- --resume` does the reverse.

Run the tests from `harness-ts/` (no install needed):

```bash
npm test             # node --experimental-strip-types --test "tests/*.test.ts"
```

Twenty-five tests, TAP output, `# fail 0` at the end. Or from the
repository root, which also runs the cross-language checks:

```bash
python run_tests.py 45
python check_snippets.py 45
```

## What to notice

- The harness is a loop and a file format, not a language. The loop
  came across line for line; the log format came across byte for byte.
- Every `await` is a place where Python blocks. Reading the port with
  that rule makes the two files line up.
- Nothing is installed to run the tests. The `openai` import is dynamic
  and lives on the one path the fake client replaces.
- `entry()` is `model_dump(exclude_none=True)` written by hand. The
  session log needs the same shape from both sides, and the shape is
  decided at the moment the reply is appended.
- The import cycle between `tools` and `subagent` exists in both
  languages, and both break it the same way: import inside the function.
- Streams cost nothing here. Python needed a thread to see output as
  it arrived; node hands it over in `data` events from the start.
- Promises cost nothing either. Parallel tool calls need a thread pool
  in Python and a `Promise.all` in TypeScript. The price is a CPU-bound
  tool, which blocks node's one thread.
- `spawn` is two calls, not one. A sandboxed argv and a plain shell
  string do not go through the same signature, and a kill needs
  `taskkill /T` to reach the tree on Windows.
- Types are for the reader. Node strips them on load; the tests would
  pass with every annotation deleted.

## Diff from step 44

```bash
diff -r ../step_44_replay_trace/harness harness
```

No difference. Added: `harness-ts/` (`package.json`, `types.ts`,
`config.ts`, `llm.ts`, `tools.ts`, `agent.ts`, `context.ts`,
`session.ts`, `permissions.ts`, `history.ts`, `compact.ts`,
`subagent.ts`, `ui.ts`, `sandbox.ts`, `todos.ts`, `skills.ts`,
`commands.ts`, and `tests/` with `fake.ts`, `session_bridge.ts`, seven
`*.test.ts` files and `fixtures/python_session.jsonl`). Changed:
`test_step.py` (runs the node suite and the two cross-language session
tests), `pyproject.toml` (version). Everything else is unchanged from
step 44.
