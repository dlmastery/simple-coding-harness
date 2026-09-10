# simple-coding-harness

**A coding agent, built in 14 snapshots, from a 27-line round trip to a
1,200-line harness with subagents.** Each step is a complete, runnable
program with its own README that explains the one idea it adds.

```
step 1   one round trip            27 lines    you ──▶ model ──▶ reply
   ...
step 4   the agent loop           105 lines    tool results go back to the model
   ...
step 14  subagents              1,219 lines    exploration in a throwaway context
```

The progression follows the commit history of
[avbiswas/neural-code](https://github.com/avbiswas/neural-code) and the
accompanying video
[*Let's build a Coding Agent Harness from Scratch (Step by Step, No frameworks)*](https://www.youtube.com/watch?v=Lu1UWqVTbQg)
by Neural Breakdown with AVB. The code here is an independent
implementation written to be read one step at a time; the ideas, the order
they arrive in, and several of the design decisions are theirs.

No frameworks. Plain Python, the `openai` client (any OpenAI-compatible
endpoint), `rich` for the terminal, and from step 13 `prompt_toolkit` for
the input line.

## The ladder

| Step | Adds | Lines | The idea |
|-----:|------|------:|----------|
| [1](step_01_one_round_trip/) | one round trip | 27 | the model only sees what is in the list |
| [2](step_02_first_tool/) | a `bash` tool | 63 | schema for the model, function for us; the model never executes |
| [3](step_03_tool_registry/) | tool registry, `read_file` | 70 | one `execute()` that every later feature hooks into |
| [4](step_04_agent_loop/) | **the agent loop** | 105 | results go back; call again until there are no tool calls |
| [5](step_05_terminal_ui/) | package + terminal UI | 224 | usage numbers make the growing prompt visible |
| [6](step_06_skills/) | skills | 276 | progressive disclosure: index in the prompt, body on demand |
| [7](step_07_editing_tools/) | `write_file`, `str_replace` | 338 | exact-match edits; errors become results the model can read |
| [8](step_08_late_injection/) | late injection | 381 | volatile context at the end, never stored; the prefix stays cached |
| [9](step_09_file_freshness/) | file freshness reminders | 415 | tell the model which files changed under it |
| [10](step_10_sessions_and_rewind/) | sessions, `/rewind` | 569 | append-only JSONL; a rewind is an entry, not a delete |
| [11](step_11_todos_and_install/) | todos, installable command | 663 | a plan that is re-injected every call cannot be lost |
| [12](step_12_permissions_and_sandbox/) | permissions, OS sandbox | 816 | rules decide what to ask about; the kernel decides what is possible |
| [13](step_13_context_management/) | cap / strip / fit / compact | 1,088 | four ways to stay inside the window, cheapest first |
| [14](step_14_subagents/) | subagents | 1,219 | spend exploration tokens in a context that is thrown away |

Lines are non-blank lines of harness code, excluding tests and READMEs.

## Run a step

```bash
pip install -r requirements.txt

export BASE_URL=https://api.openai.com/v1      # or any OpenAI-compatible endpoint
export API_KEY=sk-...
export MODEL=gpt-4.1-mini                      # optional

cd step_04_agent_loop && python agent.py       # steps 1-4: a single file
cd step_14_subagents  && python -m harness     # steps 5-14: a package
```

From step 5 the settings can live in `~/.simple-harness/env` instead of
your shell. From step 11 `pip install -e .` inside the step gives you a
`harness` command that works in any directory.

Other endpoints that work unchanged: OpenRouter
(`BASE_URL=https://openrouter.ai/api/v1`), Gemini
(`BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/`),
DeepSeek, Ollama (`BASE_URL=http://localhost:11434/v1`). Pick a model that
supports tool calling.

## Read it as diffs

Every step is the previous step plus one idea. The fastest way through is:

```bash
diff ../step_03_tool_registry/agent.py agent.py          # inside step_04
diff -r ../step_12_permissions_and_sandbox/harness harness  # inside step_13
```

Each step's README says which files changed and why. The diffs are small
on purpose: the biggest single step (13) adds three files and touches six.

## Tests

Every step ships an offline test that drives the loop with a fake model,
so you can check a step without an API key:

```bash
python run_tests.py          # all 14
python run_tests.py 13 14    # a subset
cd step_07_editing_tools && python -m pytest test_step.py
```

CI runs the whole ladder on Linux, macOS and Windows.

## The shape you end up with

```
harness/
├── agent.py        the two loops (step 4), plus fit/strip/compact hooks (step 13)
├── llm.py          one function that calls the model, returns (message, usage)
├── tools.py        registry + execute(): permissions, error handling, capping
├── prompts.py      the system prompt
├── ui.py           everything that touches the screen
├── config.py       endpoint, key, model, context window
├── skills.py       SKILL.md discovery + read_skill               (step 6)
├── context.py      late-injected <env>, <todos>, file reminders  (steps 8, 9, 11)
├── session.py      append-only JSONL transcripts                 (step 10)
├── commands.py     /rewind /sessions /compact                    (steps 10, 13)
├── todos.py        the plan                                      (step 11)
├── permissions.py  allow / ask / deny rules                      (step 12)
├── sandbox.py      Seatbelt on macOS, bubblewrap on Linux        (step 12)
├── history.py      cap, strip, fit                               (step 13)
├── compact.py      the compaction agent                          (step 13)
├── inputline.py    prompt_toolkit input                          (step 13)
└── subagent.py     the task tool                                 (step 14)
```

Three rules hold the whole thing together, and each gets its own step:

1. **Every tool call goes through one `execute()`** (step 3). Permissions,
   sandboxing, error handling and subagents all hook in there.
2. **Never edit the cached prefix** (steps 8 and 13). Volatile context is
   appended at send time and dropped; old tool output is shrunk only at the
   tail; compaction freezes everything before its summary.
3. **Errors are results** (step 7). A bad tool call, a missing file, a
   timeout, a failed compaction: each comes back as text the model can read
   and recover from. Nothing the model does can end the session.

## Platform notes

- **macOS / Linux**: the step 12 sandbox uses `sandbox-exec` (built in) or
  `bwrap` (`apt install bubblewrap`). The banner shows which is active.
- **Windows**: no OS sandbox; the permission rules are the only guard, and
  the banner says `sandbox: none`. `bash` runs through `cmd.exe` unless you
  run the harness from Git Bash or WSL.

## Credits

- Avishek Biswas, [neural-code](https://github.com/avbiswas/neural-code)
  and the [video walkthrough](https://www.youtube.com/watch?v=Lu1UWqVTbQg)
  that this ladder follows.
- The Seatbelt profile shape in step 12 follows the one used by the OpenAI
  Codex CLI.

MIT licensed.
