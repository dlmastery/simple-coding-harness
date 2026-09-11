# Step 18 - The same harness on the Google Antigravity SDK

**What changes:** the whole runtime - loop, coding tools, subagents,
compaction, sessions, skills - lives in a binary that ships inside the
`google-antigravity` wheel. Python configures it. Our contribution is a
policy list, three hooks, one subagent definition and two tools.

`pip install google-antigravity` (Apache-2.0, Python 3.10+, wheels for
Linux, macOS and Windows). Auth is `GEMINI_API_KEY`, or Vertex credentials.
The runtime can also be pointed at an OpenAI-compatible endpoint with
`LocalOpenAIAgentConfig(base_url=...)` - same harness, different model.

## Concept map

| Step | We built | Antigravity SDK | Who writes it now |
|-----:|----------|-----------------|-------------------|
| 1-2.4 | the two loops | `async with Agent(config)`, `await agent.chat(prompt)` | runtime |
| 2.1-2.2, 5 | `bash`, read, write, edit, registry | built-ins `run_command`, `view_file`, `edit_file`, `create_file`, `search_directory`, `find_file`, `list_directory`; custom tools are plain Python functions in `tools=[...]` | runtime, plus `run_tests` and `write_todos` of ours |
| 3 | UI, usage | streamed tokens (`async for token in response`), `response.usage_metadata`, `@post_tool_call` for tool lines | us |
| 4 | skills | `skills_paths=[".agents/skills"]` | runtime |
| 6 | late injection | prepended to the prompt by the caller (`late_block()`); the runtime keeps its own context | us |
| 7 | file freshness | runtime-managed context | runtime |
| 8 | sessions, `--resume` | `save_dir`, `conversation_id`, `session_continuation_mode=RESUME` | runtime; we pass the id |
| 10 | todos | no built-in; `write_todos` tool + re-injection in `late_block()` | us |
| 11 | allow / ask / deny, sandbox, timeout | policy list (`allow` / `ask_user` / `deny` with `when=` predicates) compiled by `enforce()`; `@pre_tool_call_decide` hook; `RunCommandConfig(timeout_seconds, enable_sandbox)` | us (rules), runtime (mechanics) |
| 14 | cap / strip / fit / compaction | runtime compaction (`compaction_threshold`), `@on_compaction` hook | runtime |
| 15 | `task` subagent | `SubagentConfig` with `SubagentCapabilities(enabled_tools=read-only)`; built-in `start_subagent` | us (definition), runtime (loop) |

## What is worth reading in `harness.py`

- **Policy is a list, not code.** `deny("run_command", when=is_denied)`,
  `ask_user("run_command", handler=confirm, when=needs_ask)`,
  `allow("run_command", when=is_plain)`. The predicates call the step 11
  `rules.decide`. `enforce()` compiles the list into a decide hook; the
  offline test compiles it and checks the same verdicts as step 11.
- **Two layers again.** `block_dangerous` is a `@pre_tool_call_decide`
  hook that denies on its own, independent of the policy list. Decorated
  hooks stay directly callable, so it is a one-line test.
- **A subagent is a config object.** `SubagentConfig(capabilities=
  SubagentCapabilities(enabled_tools=read_only, allowed_subagents=[]))` is
  step 15's four rules as fields: it cannot edit and it cannot recurse.
- **Custom tools are just functions.** The runtime reads the type hints and
  docstring of `run_tests` and `write_todos`; there is no schema to write.

## Run it

```bash
pip install google-antigravity
export GEMINI_API_KEY=...
python harness.py
you> start the explorer subagent to find where policies are built, then add a comment there and run the tests
```

The conversation id is printed at start; `python harness.py --resume <id>`
picks it up. Offline tests: `python -m pytest test_step.py`.

## Caveats

The SDK is at 0.1.x. The tool argument names the runtime uses
(`command`, `path`, ...) are read defensively in `arg()`; if a policy never
fires, print the `ToolCall.args` in `audit` and adjust the keys. The sandbox
flag is skipped on Windows.
