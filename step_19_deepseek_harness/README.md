# Step 19 - The same harness on DeepSeek Harness (dsh)

**What changes:** the harness is a tree of plugins. The loop, the tool
registry, the model adapter, sessions, compaction, subagents and the
permission gate are each a Cordis plugin composed by a *profile*. Our policy
becomes one more plugin in that tree; the Python side is a thin JSON-RPC
client.

Install the Python SDK (pre-release as of September 2026; it pulls the
matching runtime wheel, so no Node.js is needed to run it):

```bash
pip install --pre deepseek-harness-sdk
export DEEPSEEK_API_KEY=sk-...
```

## Two halves

```
harness.py                         Python: DeepSeekHarness(profile="sdk", patches=(...)).run(prompt, session_id=...)
plugin/simple-harness-plugin/
├── src/index.js                   the policy plugin: `tools/pre-execute` gate
├── src/rules.js                   the step 11 rules, in JavaScript
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

## What is worth reading

- **`plugin/src/index.js`.** Fifteen lines: `ctx.on('tools/pre-execute',
  async (exec, next) => ...)`. Deny returns a decision and the call never
  runs; ask hands off to the interaction plugin; everything else calls
  `next()` so the default policy still applies. This is step 11's
  `execute()` hook, expressed as an event listener instead of a function
  call - and any plugin could register one, which is the point of the
  design.
- **`make_patch()` in `harness.py`.** A profile is a list of rows; a patch
  inserts rows. Our plugin is one row with an absolute path. With
  `--minimal` the patch also inserts the filesystem provider and the
  `str_replace_editor` tool, because the `sdk-minimal` profile ships only a
  shell.
- **`harness.run()` returns after the agent goes idle.** `final_response`
  is the last assistant text, `finish_reason` is the `turn/end` kind
  (`completed`, `max-tokens`, `error`), and `events` is the root-session
  log for that interval. Subagent traffic arrives through notifications
  but cannot replace the root answer.

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

## Caveats

Developer preview: the runtime is `0.1.5rc`, the README warns of breaking
changes, and the `sdk-minimal` profile pins `danger-full-access` - use a
disposable checkout. The exact argument key of the shell tool is read
defensively in `commandOf()`; if a rule never fires, log `exec.arguments`.
The plugin is plain ESM JavaScript with no imports so it loads from a raw
path; a plugin that uses `defineTool` from `@deepseek-ai/dsh-tools` should be
installed with `dsh plugin --profile sdk add file:<dir>` so its imports
resolve.
