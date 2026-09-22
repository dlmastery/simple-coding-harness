# Step 19 - The same harness on DeepSeek Harness (dsh)

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Separate the harness from its provider**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 18 - The same harness on the Google Antigravity SDK](../step_18_google_antigravity_sdk/README.md). Next: [Step 20 - The same harness on OpenRouter](../step_20_openrouter/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** policy as a plugin inside the runtime. The harness
is a tree of plugins: the loop, the tool registry, the model adapter,
sessions, compaction, subagents and the permission gate are each a Cordis
plugin composed by a *profile*. Our policy becomes one more plugin in that
tree, running inside the runtime's process. The Python side is a thin
JSON-RPC client.

Install the Python SDK (pre-release as of September 2026; it pulls the
matching runtime wheel - about 240 MB, a single-file Node executable - so no
Node.js is needed to run it):

```bash
pip install --pre deepseek-harness-sdk
export DEEPSEEK_API_KEY=sk-...
```

## Why

Steps 16-18 kept our policy on our side of a boundary: a callback the SDK
invokes. Every decision costs a round trip to the host process, and the
host has to be alive to answer. dsh takes the other position: the policy
runs *inside* the runtime, as a listener on the same event the built-in
gate listens on, with no privilege the built-in has that ours does not.

Without this step, "plugin" would still mean "a callback the vendor calls".
Here it means a row in the profile that composes the runtime. That is the
most invasive of the four integrations and the one where our code can
break the runtime - which the caveats say.

## Files

```text
step_19_deepseek_harness/
├── harness.py         the Python client: the patch, sessions, notifications, the REPL
├── plugin/simple-harness-plugin/
│   ├── package.json           plugin metadata; `npm run check` syntax-checks and tests
│   └── src/
│       ├── index.js           the policy plugin: a tools/pre-execute gate
│       ├── rules.js           the stage 11 rules, ported to JavaScript
│       └── rules.test.js      plain node unit test of decide(), splitCommand() and the gate
└── test_step.py       offline tests: patch, client config, renderer, plugin via node
```

## Two halves

```text
harness.py                         Python: DeepSeekHarness(profile="sdk", patches=(...)).run(prompt, session_id=...)
plugin/simple-harness-plugin/
├── src/index.js                   the policy plugin: `tools/pre-execute` gate
├── src/rules.js                   the stage 11 rules, in JavaScript
└── src/rules.test.js              node unit test
~/.simple-harness/dsh-home/        the isolated harness home: profile, plugins, JSONL sessions
    simple-harness.patch.yml       written at launch: inserts the plugin row (absolute path)
```

## Concept map

| Step | We built | DeepSeek Harness | Who writes it now |
|-----:|----------|------------------|-------------------|
| 1-2.4 | the two loops | `core/agent-loop` plugin; `harness.run(prompt)` waits from inbox receipt to idle | runtime |
| 2.1-2.2, 5 | `bash`, read, edit, registry | `dsh-base`: persistent `bash` (`pwsh` on Windows), `read` / `write` / `edit`, `str_replace_editor` opt-in; `ctx.tools.register(defineTool(...))` for your own | runtime |
| 3 | UI | `on_notification` callback: the session event stream (`tool/call`, `tool/result`, `turn/end`, `compaction/end`) | us (`summarize`) |
| 4 | skills | `skill/` package: skill provider registry + loader tool | runtime |
| 6, 7 | late injection, freshness | `context/` request-context plugins; `agent.inject()` for durable context | runtime |
| 8 | JSONL sessions | append-only `SessionEvent` log under `<home>/sessions`; `session_id=` to continue | runtime; we list them |
| 10 | todos | `todo/` package (`todo_write`) | runtime |
| 11 | allow / ask / deny, sandbox | `tools/pre-execute` waterfall: return `{kind: 'deny'}` / `{kind: 'ask'}` or `next()`; the approval service answers asks - or fails closed when nobody can; fs and subprocess *providers* are the sandbox seam | us (the plugin), runtime (mechanics) |
| 14 | compaction | `compaction/` capability + provider | runtime |
| 15 | subagents | `subagent/` capability; providers range from a child agent to delegating a turn to Claude Code or Codex | runtime |

## The code, piece by piece

### 1. The policy plugin: a listener on the tool gate

Stage 11 put the permission check inside `execute()`, a function every
tool call passed through. In dsh nothing is privileged. The runtime
primitive is the `tools/pre-execute` waterfall event. Any plugin can listen
and return a decision.

`src/index.js`:

```javascript
export function apply(ctx) {
  ctx.on('tools/pre-execute', async (exec, next) => {
    if (!SHELL_TOOLS.has(exec.name)) return next()
    const command = commandOf(exec)
    const decision = gate(command)
    if (decision) return decision
    if (decide(command) === 'ask') console.error(`[simple-harness-policy] ask, allowed without a human: ${command}`)
    return next()
  })
```

`apply(ctx)` is the plugin entry point. `ctx` is the Cordis context the
loader hands every plugin. A `deny` return means the call never runs and
the reason becomes the tool result. `next()` lets the next listener, or the
default policy, decide. This is the `execute()` hook of stage 11 as an
event listener.

The decision itself is a function, so the node test can drive it:

`src/index.js`:

```javascript
export function gate(command, askFallback = ASK_FALLBACK) {
  const verdict = decide(command)
  if (verdict === 'deny') return { kind: 'deny', reason: `Blocked by policy: ${command}` }
  if (verdict === 'ask' && askFallback === 'deny') {
    return { kind: 'deny', reason: `needs approval, and this profile has nobody to ask: ${command}. Only allow-listed commands run.` }
  }
  return null // allow, or ask-as-allow: let the next listener decide
}
```

Here is the honest part. The waterfall contract has a third answer,
`{ kind: 'ask' }`, which hands the call to the runtime's approval service.
That service asks its *answerers*, and in the SDK profiles there are none:
the JSON-RPC server never sends a question back to the Python client (the
runtime's own README calls server-to-client requests "a dead capability"),
so the service fails closed and the model reads `requires approval, but no
approval channel is available`. The first version of this plugin returned
`ask` and believed the interaction plugin would prompt. It cannot. So
`ASK_FALLBACK` decides what an `ask` verdict becomes: `'deny'`, the
default, keeps the stage 11 line and tells the model why in plain words;
`'allow'` lets those commands through with an audit line on stderr, which
is what `sdk-minimal`'s `danger-full-access` sandbox mode already permits.
Neither is a human saying yes. Add commands to the allow list in `rules.js`
if you want them to run without one.

`src/index.js`:

```javascript
  // Step 3, the audit line: durable session events are the transcript.
  ctx.on('session/event', (_session, event) => {
    if (event?.type === 'tool/call') {
      console.error(`[simple-harness-policy] tool/call ${event.data?.name ?? ''}`)
    }
  })
}
```

The same plugin listens to `session/event` and logs each tool call to
stderr. That is the audit line of stage 3, from inside the runtime
process. Stderr, never stdout: stdout is the JSON-RPC transport, and a
stray `console.log` breaks the framing.

### 2. The rules, ported to JavaScript

The plugin runs inside the dsh process, which is Node.js. So the stage 11
table lives in JavaScript here, with the same patterns and the same
"strictest part wins" rule.

`src/rules.js`:

```javascript
export function decide(command) {
  const verdicts = splitCommand(command).map(part => {
    let action = 'ask'
    for (const [pattern, rule] of BASH_RULES) if (globMatch(part, pattern)) action = rule
    return action
  })
  if (verdicts.includes('deny')) return 'deny'
  if (verdicts.includes('ask')) return 'ask'
  return 'allow'
}
```

`BASH_RULES` is the same list as the Python `rules.py` in steps 16-18, as
an ordered array so last match wins. `splitCommand` is the quote-aware
splitter of stage 11. `globMatch` stands in for `fnmatch`. The unit test
in `rules.test.js` checks the same verdicts as the Python tests, plus the
gate. Nothing here is the runtime's. It is the policy, and policy is ours.

### 3. The patch: how a plugin enters the tree

A profile is an ordered list of Cordis rows. The runtime primitive for
changing one is a patch file that inserts or replaces rows. The plugin
path must be absolute, so the patch is written at launch time.

`harness.py`:

```python
def make_patch(plugin_path: Path, minimal: bool) -> str:
    rows = [
        "- insert:",
        "    - id: simple-harness-policy",
        f"      name: '{plugin_path.as_posix()}'",
    ]
    if minimal:  # sdk-minimal ships only a shell; add the editor and its fs provider
        rows += [
            "    - id: fs-local",
            "      name: '@deepseek-ai/dsh-fs-local'",
            "      config:",
            "        cwd: !!js process.cwd()",
            "    - id: tool-str-replace-editor",
            "      name: '@deepseek-ai/dsh-tool-str-replace-editor'",
        ]
    return "\n".join(rows) + "\n"
```

Our plugin is one row with an absolute path. With `--minimal` the patch
also inserts the filesystem provider and the `str_replace_editor` tool,
because the `sdk-minimal` profile ships only a shell. This replaces the
tool registry of stage 2.2: tools are rows in a profile, not entries in a
dict. The patch text is ours. Loading it is the runtime's.

### 4. The client object

Stage 1 opened an HTTP client to a model. The SDK primitive is
`DeepSeekHarness`, a client for the whole runtime over JSON-RPC on stdio.

`harness.py`:

```python
def build(minimal=False, model=None, patch=None):
    """The client object. Nothing launches until the first run()."""
    return DeepSeekHarness(
        provider="deepseek-official",
        model=model or os.environ.get("MODEL", "deepseek-v4-flash"),
        cwd=os.getcwd(),
        dsh_home=str(HOME),
        profile="sdk-minimal" if minimal else "sdk",
        patches=(str(patch),) if patch else (),
        request_timeout_seconds=REQUEST_TIMEOUT,
    )
```

`dsh_home` is an isolated harness home under `~/.simple-harness`, so the
profile, plugins and sessions of this step never touch a global dsh
install. `profile` picks the plugin tree. `patches` adds ours to it. The
runtime launches on the first `run()` call. `request_timeout_seconds`
bounds how long the runtime may take to *acknowledge* a request; the turn
itself is bounded by the runtime's own timeouts.

### 5. Presentation: the event stream

Stage 3 drew tool calls from the messages list. Here the SDK primitive is
the `on_notification` callback. It receives every session event as it
happens, and we pick which ones to show.

`harness.py`:

```python
def summarize(note: Notification):
    """One line for the events worth a person's eyes, None for the rest.

    The shapes are the runtime's session-event contract: `tool/call` carries
    `{name, arguments}`, `tool/result` carries the tool message under
    `message.content` (and `error` when it failed), compaction is a
    start / end pair.
    """
    payload = note.payload or {}
    event = payload.get("event", payload)
    kind = event.get("type") if isinstance(event, dict) else None
    data = event.get("data", {}) if isinstance(event, dict) else {}
    if kind == "tool/call":
        return f"  tool> {data.get('name', '?')} {str(data.get('arguments', ''))[:90]}"
    if kind == "tool/result":
        error = data.get("error")
        content = (data.get("message") or {}).get("content") or []
        text = " ".join(str(c.get("text", "")) if isinstance(c, dict) else str(c) for c in content) if isinstance(content, list) else str(content)
        if error:
            text = f"error {error.get('name', '')}: {text}" if isinstance(error, dict) else f"error: {text}"
        return f"        {' '.join(text.split())[:110] or '(no output)'}"
    if kind == "turn/end":
        reason = (data.get("reason") or {}).get("kind") if isinstance(data.get("reason"), dict) else data.get("reason")
        return f"  turn ended: {reason}" if reason else None
    if kind == "compaction/end":
        return "  compacted"
    return None
```

Four event kinds get a line: a tool call, its result, the end of a turn,
and the end of a compaction. Everything else returns `None` and is not
printed. The notifications arrive with method `session.event` and the
event under `payload["event"]`; a tool result is a whole tool *message*,
so its text is under `data.message.content`, and a failed tool adds an
`error` object beside it. The compaction line replaces the orange panel of
stage 14. The runtime compacts on its own and only tells us it happened.
The event shapes are the runtime's. The choice of what to show is ours.

### 6. Sessions are JSONL logs under the harness home

Stage 8 wrote a JSONL file per session. The runtime does the same, as an
append-only event log under `<home>/sessions`. The SDK has no listing
call, so we scan the directory.

`harness.py`:

```python
def list_sessions():
    """Newest first: session ids the runtime has written under <home>/sessions."""
    root = HOME / "sessions"
    if not root.exists():
        return []
    dirs = [p for p in root.rglob("*") if p.is_dir() and any(p.glob("session*.jsonl*"))]
    return [p.name for p in sorted(dirs, key=lambda p: p.stat().st_mtime, reverse=True)]
```

A session is a directory holding one or more `session*.jsonl` files. To
continue one, pass its id as `session_id=` on the next `run()`. The write
and the resume are the runtime's. The listing is ours.

### 7. The loop

Stage 2.4 wrote the agent loop. Here `harness.run()` is the whole turn. It
sends the prompt and returns after the agent goes idle.

`harness.py`:

```python
def turn(harness, text, session_id):
    """One prompt in, the final answer out. A runtime failure is one line, not a crash."""
    try:
        result = harness.run(
            text,
            session_id=session_id,
            on_notification=lambda n: (line := summarize(n)) and print(line),
        )
    except (HarnessError, TimeoutError) as failure:
        print(f"\n  error: {type(failure).__name__}: {failure}")
        return
    print(f"\n  agent> {result.final_response}")
    print(f"  finish: {result.finish_reason} · {len(result.events)} events")
```

`final_response` is the last assistant text. `finish_reason` is the
`turn/end` kind: `completed`, `max-tokens`, `error`, `interrupted` or
`aborted`. `events` is the root-session log for that interval. Subagent
traffic arrives through notifications but cannot replace the root answer.
The input loop and the `/sessions` command are ours. Everything between
the prompt and the answer is the runtime's.

## Run it

Prerequisites: Python 3.10+, `pip install --pre deepseek-harness-sdk`, a
DeepSeek key. `node` is only needed for the plugin's own unit test.

bash:

```bash
export DEEPSEEK_API_KEY=sk-...
python harness.py                  # full `sdk` profile: files, shell, skills, subagents, compaction
python harness.py --minimal        # `sdk-minimal`: shell + editor only, no policy plugins of its own
python harness.py --resume 20260910-153000-a1b2c3
```

PowerShell:

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."
python harness.py
```

Then:

```text
> find where the permission gate runs and add a comment there
> /sessions
```

### Expected output

```text
  simple coding harness · deepseek harness · profile sdk · session 20260918-104201-3f9a1c · /sessions
  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave

> find where the permission gate runs and add a comment there
  tool> bash {"command":"grep -n \"tools/pre-execute\" -r plugin"}
        plugin/simple-harness-plugin/src/index.js:46: ctx.on('tools/pre-execute', async (exec, next) => {
  tool> read {"path":"plugin/simple-harness-plugin/src/index.js"}
        // @ts-check /** * simple-harness-policy: the step 11 permission layer as a dsh plugin. …
  tool> edit {"path":"plugin/simple-harness-plugin/src/index.js","old":"  ctx.on('tools/pre-execute'…
        edited
  turn ended: completed

  agent> The gate is the tools/pre-execute listener in src/index.js; I added a comment above it.
  finish: completed · 14 events
```

A command outside the allow list shows up as
`tool> bash {"command":"python x.py"}` followed by
`Error: needs approval, and this profile has nobody to ask: python x.py. Only allow-listed commands run.`
- see section 1.

Offline tests: `python -m pytest test_step.py` (patch, client config,
renderer against the runtime's event shapes, `turn()`'s error path, and the
plugin syntax-checked plus unit-tested with `node`).

## Error handling

- **A bad or failing tool call.** The runtime's tools return their errors
  as tool messages; `summarize` prints them as `error <name>: ...`.
- **A denied call.** The plugin's `deny` reason is the tool result.
- **A dead runtime.** `harness.run()` raises `TransportClosedError`
  (`HarnessError`) when the subprocess exits; `turn()` prints one line and
  returns to the prompt. The next prompt fails the same way - leave and
  start again with `--resume`.
- **A slow acknowledgement** raises `TimeoutError` after `REQUEST_TIMEOUT`
  seconds, printed the same way. A turn that the runtime never finishes is
  not bounded on the Python side; ctrl-c ends the harness with
  `interrupted` (the `with` block closes the runtime on the way out).
- **Leaving.** `/exit`, ctrl-d (ctrl-z then enter on Windows) or ctrl-c at
  the prompt. An empty line does nothing.

## Gotchas / what this is not

- **No prompt for `ask`.** The runtime cannot ask the Python client
  anything in this SDK version (section 1). `ASK_FALLBACK` in `index.js`
  is the switch; the default is deny.
- The `sdk` profile ships a default gate; ours sits in front of it and the
  default still runs when we call `next()`. The `sdk-minimal` profile ships
  no policy plugins at all and pins `danger-full-access` - use a disposable
  checkout.
- The plugin loads from a raw path and imports `./rules.js` relative to
  itself. On Windows the path in the patch is `C:/...`; if the loader
  refuses it, install the plugin with `dsh plugin --profile sdk add
  file:<dir>` instead. A plugin that uses `defineTool` from
  `@deepseek-ai/dsh-tools` needs that route in any case, so its imports
  resolve.
- Developer preview: the runtime is `0.1.5rc` and the README warns of
  breaking changes. The shell tool is `bash` on Linux and macOS and `pwsh`
  on Windows; both are in `SHELL_TOOLS`. If a rule never fires, log
  `exec.arguments` from the plugin (to stderr).
- The screen is ours: what to print from the event stream is our decision.

## What the next step adds

Step 20 goes back to the hand-built harness of stage 15 and points it at
OpenRouter: one key, a route of models with fallbacks, and the cost of
every call.

<!-- harness-learning-check -->
## Check your understanding

Why can two implementations of the same task need different failure handling?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

Their tools, state and completion signals can have different contracts. Compare those observations rather than relying only on equal answer text.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
