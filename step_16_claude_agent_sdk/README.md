# Step 16 - The same harness on the Claude Agent SDK

**What changes:** the loop, the tools, sessions, compaction and subagents are
now the SDK's. We write ~150 lines of *policy and presentation* instead of
~1,200 lines of harness.

The Claude Agent SDK (`pip install claude-agent-sdk`) is Claude Code packaged
as a library. It spawns the `claude` CLI as a subprocess and speaks to it
over JSON. Every mechanism from steps 1-15 has a counterpart; the table says
which ones you configure and which ones you never see again.

## Concept map

| Step | We built | Claude Agent SDK | Who writes it now |
|-----:|----------|------------------|-------------------|
| 1-2.4 | `messages` list, the two loops | `ClaudeSDKClient.query()` / `receive_response()` | SDK |
| 2.1-2.2 | `bash`, `read_file`, registry | built-in `Bash`, `Read`, `Glob`, `Grep`; custom tools via `@tool` + `create_sdk_mcp_server` | SDK, plus one `@tool` of ours (`run_tests`) |
| 3 | rich UI, usage line | message stream: `AssistantMessage`, `ToolUseBlock`, `ResultMessage.usage` / `total_cost_usd` | us (`show()`) |
| 4 | `.agents/skills`, `read_skill` | `.claude/skills/*/SKILL.md` via `setting_sources=["project"]`, `skills="all"`, built-in `Skill` tool | SDK; we ship the skill |
| 5 | `write_file`, `str_replace`, errors as results | built-in `Write`, `Edit`; tool errors are already results | SDK |
| 6 | late-injected `<env>` block | `UserPromptSubmit` hook returning `additionalContext` | us (`env_context`) |
| 7 | file freshness reminders | built in: Claude Code injects its own `<system-reminder>` on changed files | SDK |
| 8 | JSONL sessions, `/rewind`, `--resume` | sessions on disk; `list_sessions()`, `ClaudeAgentOptions(resume=...)`, `resume_session_at` | SDK; we wire `--resume`, `/sessions`, `/resume <id>` |
| 10 | `write_todos`, re-injected plan | built-in `TodoWrite`; the plan is re-injected by Claude Code | SDK |
| 11 | allow / ask / deny, OS sandbox | `PreToolUse` hook (`permissionDecision: "deny"`) + `can_use_tool` callback; `sandbox={"enabled": True}` | us (rules), SDK (sandbox) |
| 14 | cap / strip / fit / compaction | automatic compaction; `PreCompact` hook; `/compact` passes through as a prompt | SDK |
| 15 | `task` subagent | `agents={"explorer": AgentDefinition(...)}` used by the built-in `Task` tool | us (definition), SDK (loop) |

## What is worth reading in `harness.py`

- **Two-layer policy survives.** `deny_dangerous` is a `PreToolUse` hook:
  it runs before any permission prompt and a `deny` there cannot be
  overridden at the prompt. `can_use_tool` then does allow / ask, calling
  the same `rules.py` as step 11. The SDK gives you both hooks; it does not
  tell you what to put in them.
- **Late injection is a hook.** The `UserPromptSubmit` hook returns
  `additionalContext`, which the harness attaches to that prompt only. Same
  cache reasoning as step 6, one function instead of a module.
- **A subagent is data.** `AgentDefinition(tools=[...], maxTurns=12)` is the
  four rules of step 15 as fields: fresh context, withheld tools, same loop,
  only the report comes back. The built-in `Task` tool does the rest.
- **The custom tool is an MCP server that never leaves the process.**
  `create_sdk_mcp_server` turns a decorated coroutine into a tool named
  `mcp__harness__run_tests`; putting that name in `allowed_tools`
  pre-approves it.

## Run it

```bash
pip install claude-agent-sdk          # needs the `claude` CLI on PATH
claude login                          # or export ANTHROPIC_API_KEY
python harness.py
you> where does the permission decision get made in this file? then add a comment there
you> /sessions
you> /compact
```

Offline tests (`python -m pytest test_step.py`) cover the policy, the hooks
and the option wiring without launching Claude.

## What the SDK does not give you

The screen. Every message arrives as a typed object and you decide how it
looks, which is what `show()` does in forty lines. And the policy: the
default permission mode prompts through the SDK, so without `can_use_tool`
and the hook you get Claude Code's defaults, not yours.
