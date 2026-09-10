# Step 16 - The same harness on the OpenAI Agents SDK

**What changes:** the SDK owns the loop, sessions, approvals and
agents-as-tools. The coding tools are ours again - the step 7 functions come
back verbatim and get *wrapped* instead of hand-registered - and the late
injection / stripping logic becomes one request filter.

`pip install openai-agents`. Works against any OpenAI-compatible endpoint
through `OpenAIChatCompletionsModel`, so the same `BASE_URL` / `API_KEY` /
`MODEL` as steps 1-14.

## Concept map

| Step | We built | OpenAI Agents SDK | Who writes it now |
|-----:|----------|-------------------|-------------------|
| 1-4 | the two loops, `as_dict`, tool-result ids | `Runner.run(agent, input, session=...)` | SDK |
| 2-3, 7 | `bash`, `read_file`, `write_file`, `str_replace`, registry, `schema()` | `function_tool(fn)`: schema from the signature and docstring; errors become results | us (functions), SDK (schema, registry) |
| 5 | rich UI, usage | `RunHooks` (`on_tool_start`, `on_tool_end`, `on_llm_end` with `response.usage`) | us (`Console`) |
| 6 | skills | not an SDK concept; `read_skill` tool + index in `instructions` | us, unchanged |
| 8 | late-injected `<env>` | `RunConfig(call_model_input_filter=...)` appends to the request, never to the session | us (`shape_request`) |
| 9 | file freshness | same filter, same git hash diff | us |
| 10 | JSONL sessions, `/rewind` | `SQLiteSession(id, db_path)`; `session.pop_item()` for rewind | SDK; we wire `--resume`, `/sessions`, `/rewind` |
| 11 | `write_todos`, re-injected plan | `write_todos` tool with a `TypedDict` schema; re-injected by the filter | us |
| 12 | allow / ask / deny, timeouts | `tool_input_guardrails` (deny becomes the tool result), `needs_approval` (ask pauses the run: `result.interruptions`, `state.approve()`), `timeout=60` on the tool | us (rules), SDK (mechanics) |
| 13 | cap / strip / fit / compaction | strip in the filter; no built-in summariser (the SDK has session trimming settings, not a compaction agent) | us |
| 14 | `task` subagent | `explorer.as_tool(tool_name="task", max_turns=12)` - fresh run, own context, only `final_output` returns | SDK |

## What is worth reading in `harness.py`

- **`function_tool(_bash, needs_approval=..., tool_input_guardrails=[...], timeout=60)`.**
  The implementation is a plain function with a docstring; the SDK derives
  the JSON schema (compare `schema()` in step 7). Policy hangs off the same
  call: a guardrail for structural denies, a predicate for asks, a timeout
  that turns hangs into results.
- **Approval is a pause, not a callback.** When `needs_approval` returns
  true the run stops and `result.interruptions` lists the pending calls.
  You approve or reject on a `RunState` and call `Runner.run(agent, state)`
  to continue. The state serialises, so the approval could happen in
  another process - that is the design difference from step 12's inline
  prompt.
- **`shape_request` is steps 8, 9, 11 and 13 in one function.** The
  `call_model_input_filter` sees a copy of the model input on every call.
  It shrinks old tool outputs and appends the `<env>` / `<todos>` /
  changed-files block. The session on disk never sees any of it - the same
  request-vs-record split the hand-built harness enforced by hand.
- **A subagent is `agent.as_tool()`.** Its own `Agent` with its own tool
  list (no `write_file`, no `task`), a `max_turns`, and only the final
  output crosses back. The four rules of step 14, as arguments.

## Run it

```bash
pip install openai-agents
export BASE_URL=... API_KEY=... MODEL=...
python harness.py
you> use the task tool to find where approvals are handled, then add a comment there
you> /rewind
```

Offline tests: `python -m pytest test_step.py` (tools, policy, the request
filter, rewind on a real `SQLiteSession`).

## What the SDK does not give you

Coding tools, skills, a compaction agent, and any opinion about the screen.
It is a general agent framework; the "coding" in coding agent is still your
tools and your prompt.
