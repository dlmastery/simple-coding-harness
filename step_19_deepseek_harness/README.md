# Step 19 - The same harness on DeepSeek Harness (dsh)

**What this step adds:** the harness is a tree of plugins. The loop, the
tool registry, the model adapter, sessions, compaction, subagents and the
permission gate are each a Cordis plugin composed by a *profile*. Our policy
becomes one more plugin in that tree. The Python side is a thin JSON-RPC
client.

Install the Python SDK (pre-release as of September 2026; it pulls the
matching runtime wheel, so no Node.js is needed to run it):

```bash
pip install --pre deepseek-harness-sdk
export DEEPSEEK_API_KEY=sk-...
```

## Files

```text
step_19_deepseek_harness/
├── harness.py         the Python client: the patch, sessions, notifications, the REPL
├── plugin/simple-harness-plugin/
│   ├── package.json           plugin metadata; `npm run check` syntax-checks and tests
│   └── src/
│       ├── index.js           the policy plugin: a tools/pre-execute gate
│       ├── rules.js           the stage 11 rules, ported to JavaScript
│       └── rules.test.js      plain node unit test of decide() and splitCommand()
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
| 3 | UI | `on_notification` callback: the session event stream (`tool/call`, `tool/result`, `turn/end`) | us (`summarize`) |
| 4 | skills | `skill/` package: skill provider registry + loader tool | runtime |
| 6, 7 | late injection, freshness | `context/` request-context plugins; `agent.inject()` for durable context | runtime |
| 8 | JSONL sessions | append-only `SessionEvent` log under `<home>/sessions`; `session_id=` to continue | runtime; we list them |
| 10 | todos | `todo/` package (`todo_write`) | runtime |
| 11 | allow / ask / deny, sandbox | `tools/pre-execute` waterfall: return `{kind: 'deny'}` / `{kind: 'ask'}` or `next()`; `interaction/` handles asks; fs and subprocess *providers* are the sandbox seam | us (the plugin), runtime (mechanics) |
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
    const verdict = decide(command)
    if (verdict === 'deny') return { kind: 'deny', reason: `Blocked by policy: ${command}` }
    if (verdict === 'ask') return { kind: 'ask', reason: `run: ${command}` }
    return next()
  })
```

`apply(ctx)` is the plugin entry point. `ctx` is the Cordis context the
loader hands every plugin. A `deny` return means the call never runs and
the reason becomes the tool result. An `ask` return hands off to the
interaction plugin, which prompts the user. `next()` lets the next
listener, or the default policy, decide. This is the `execute()` hook of
stage 11 as an event listener. The plugin needs no imports beyond its own
rules file, so it loads from a raw path.

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
process. Both listeners are ours. The event vocabulary and the waterfall
are the runtime's.

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
in `rules.test.js` checks the same verdicts as the Python tests. Nothing
here is the runtime's. It is the policy, and policy is ours.

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
    )
```

`dsh_home` is an isolated harness home under `~/.simple-harness`, so the
profile, plugins and sessions of this step never touch a global dsh
install. `profile` picks the plugin tree. `patches` adds ours to it. The
runtime launches on the first `run()` call.

### 5. Presentation: the event stream

Stage 3 drew tool calls from the messages list. Here the SDK primitive is
the `on_notification` callback. It receives every session event as it
happens, and we pick which ones to show.

`harness.py`:

```python
def summarize(note: Notification):
    """One line for the events worth a person's eyes, None for the rest."""
    payload = note.payload or {}
    event = payload.get("event", payload)
    kind = event.get("type") or note.method
    data = event.get("data", {}) if isinstance(event, dict) else {}
    if kind == "tool/call":
        name = data.get("name") or data.get("tool") or "?"
        args = data.get("arguments") or data.get("args") or ""
        return f"  tool> {name} {str(args)[:90]}"
    if kind == "tool/result":
        content = data.get("content") or data.get("result") or ""
        text = " ".join(str(c.get("text", "")) if isinstance(c, dict) else str(c) for c in content) if isinstance(content, list) else str(content)
        return f"        {' '.join(text.split())[:110] or '(no output)'}"
    if kind == "turn/end":
        reason = (data.get("reason") or {}).get("kind") if isinstance(data.get("reason"), dict) else data.get("reason")
        return f"  turn ended: {reason}" if reason else None
    if kind == "compaction":
        return "  compacted"
    return None
```

Four event kinds get a line: a tool call, its result, the end of a turn,
and a compaction. Everything else returns `None` and is not printed. The
compaction line replaces the orange panel of stage 14. The runtime
compacts on its own and only tells us it happened. The event shapes are
the runtime's. The choice of what to show is ours.

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
    with build(minimal=cli.minimal, patch=patch) as harness:
        while True:
            try:
                text = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not text:
                break
            if text == "/sessions":
                for sid in list_sessions():
                    print(f"  {sid}")
                continue
            result = harness.run(
                text,
                session_id=session_id,
                on_notification=lambda n: (line := summarize(n)) and print(line),
            )
            print(f"\n  agent> {result.final_response}")
            print(f"  finish: {result.finish_reason} · {len(result.events)} events")
```

`final_response` is the last assistant text. `finish_reason` is the
`turn/end` kind: `completed`, `max-tokens` or `error`. `events` is the
root-session log for that interval. Subagent traffic arrives through
notifications but cannot replace the root answer. The input loop and the
`/sessions` command are ours. Everything between the prompt and the
answer is the runtime's.

## Run it

```bash
python harness.py                  # full `sdk` profile: files, shell, skills, subagents, compaction
python harness.py --minimal        # `sdk-minimal`: shell + editor only, no policy plugins of its own
you> find where the permission gate runs and add a comment there
you> /sessions
python harness.py --resume 20260910-153000
```

Offline tests: `python -m pytest test_step.py` (patch, client config,
renderer, and the plugin syntax-checked plus unit-tested with `node`).

## What the SDK does not give you

A policy of its own that matches yours, and a screen. The `sdk` profile
ships a default gate; ours sits in front of it and the default still runs
when we call `next()`. The `sdk-minimal` profile ships no policy plugins at
all. What to print from the event stream is our decision.

## Caveats

Developer preview: the runtime is `0.1.5rc`, the README warns of breaking
changes, and the `sdk-minimal` profile pins `danger-full-access` - use a
disposable checkout. The exact argument key of the shell tool is read
defensively in `commandOf()`; if a rule never fires, log `exec.arguments`.
The plugin is plain ESM JavaScript with no imports so it loads from a raw
path; a plugin that uses `defineTool` from `@deepseek-ai/dsh-tools` should be
installed with `dsh plugin --profile sdk add file:<dir>` so its imports
resolve.
