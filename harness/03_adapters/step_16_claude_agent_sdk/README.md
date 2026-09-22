# Step 16 - The same harness on the Claude Agent SDK

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Separate the harness from its provider**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 15 - Exploration subagents](../../02_control/step_15_subagents/README.md). Next: [Step 17 - The same harness on the OpenAI Agents SDK](../step_17_openai_agents_sdk/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** the harness as a library instead of a program.
The loop, the tools, sessions, compaction and subagents are now the SDK's.
We write about 150 lines of *policy and presentation* instead of about
1,200 lines of harness.

The Claude Agent SDK (`pip install claude-agent-sdk`) is Claude Code packaged
as a library. It spawns the `claude` CLI as a subprocess and speaks to it
over JSON. Every mechanism from stages 1-15 has a counterpart. The table says
which ones you configure and which ones you never see again.

## Why

Stages 1-15 built one harness, and every idea in it - the loop, permissions,
late injection, sessions, compaction, subagents - cost a module. Each of
those modules now has to be maintained, and none of them is the interesting
part of *your* agent. What is yours is the policy: which commands run
without asking, what context gets injected, which subagent exists, what the
screen shows.

Without an SDK, a change to the vendor's tool set or context format means
rewriting your harness. With it, you keep the fifteen ideas and hand the
mechanics to the vendor; the diff between "our harness" and "the SDK" is a
map of which ideas were mechanics all along. Steps 16-19 draw that map four
times, on four SDKs. This is the first.

## Files

```text
step_16_claude_agent_sdk/
├── .claude/skills/explain-code/SKILL.md   the stage 4 skill, where the SDK looks for it
├── harness.py         the SDK client: policy hook, @tool tools, show(), the REPL
├── rules.py           the stage 11 allow / ask / deny table, unchanged
└── test_step.py       offline tests: policy, hooks, config; never launches Claude
```

## Concept map

| Step | We built | Claude Agent SDK | Who writes it now |
|-----:|----------|------------------|-------------------|
| 1-2.4 | `messages` list, the two loops | `ClaudeSDKClient.query()` / `receive_messages()` | SDK |
| 2.1-2.2 | `bash`, `read_file`, registry | built-in `Bash`, `Read`, `Glob`, `Grep`; custom tools via `@tool` + `create_sdk_mcp_server` | SDK, plus one `@tool` of ours (`run_tests`) |
| 3 | rich UI, usage line | message stream: `AssistantMessage`, `ToolUseBlock`, `ResultMessage.usage` / `total_cost_usd` | us (`show()`) |
| 4 | `.agents/skills`, `read_skill` | `.claude/skills/*/SKILL.md` via `setting_sources=["project"]`, `skills="all"`, built-in `Skill` tool | SDK; we ship the skill |
| 5 | `write_file`, `str_replace`, errors as results | built-in `Write`, `Edit`; tool errors are already results | SDK |
| 6 | late-injected `<env>` block | `UserPromptSubmit` hook returning `additionalContext` | us (`env_context`) |
| 7 | file freshness reminders | built in: Claude Code injects its own `<system-reminder>` on changed files | SDK |
| 8 | JSONL sessions, `/rewind`, `--resume` | sessions on disk; `list_sessions()`, `ClaudeAgentOptions(resume=...)` | SDK; we wire `--resume`, `/sessions`, `/resume <id>` |
| 10 | `write_todos`, re-injected plan | built-in `TodoWrite`; the plan is re-injected by Claude Code | SDK |
| 11 | allow / ask / deny, OS sandbox | `PreToolUse` hook (`permissionDecision: "deny"`) + `can_use_tool` callback; `sandbox={"enabled": True}` | us (rules), SDK (sandbox) |
| 14 | cap / strip / fit / compaction | automatic compaction; `PreCompact` hook; `/compact` sent as a prompt | SDK |
| 15 | `task` subagent | `agents={"explorer": AgentDefinition(...)}` used by the built-in `Task` tool | us (definition), SDK (loop) |

## The code, piece by piece

### 1. The whole configuration is one object

The SDK primitive is `ClaudeAgentOptions`. One object replaces the loop of
stage 2.4, the tool registry of stage 2.2, the skill loader of stage 4, the
session file of stage 8 and the sandbox flag of stage 12.

`harness.py`:

```python
def build_options(resume=None):
    options = ClaudeAgentOptions(
        system_prompt={"type": "preset", "preset": "claude_code", "append": APPEND},
        cwd=os.getcwd(),
        setting_sources=["project"],  # step 4: loads .claude/skills/*/SKILL.md
        skills="all",
        mcp_servers={"harness": SERVER},
        # pre-approved: read-only built-ins, the plan, the subagent, our tool
        allowed_tools=["Read", "Glob", "Grep", "TodoWrite", "Task", "Skill", "mcp__harness__run_tests"],
        can_use_tool=can_use_tool,
        hooks={
            "PreToolUse": [HookMatcher(matcher="Bash", hooks=[deny_dangerous])],
            "UserPromptSubmit": [HookMatcher(hooks=[env_context])],
            "PreCompact": [HookMatcher(hooks=[on_compact])],
        },
        agents={"explorer": EXPLORER},
        resume=resume,
    )
    if sys.platform != "win32":  # step 11: the OS sandbox is one flag here
        options.sandbox = {"enabled": True}
    return options
```

Read the fields as a map of the hand-built harness. `system_prompt` uses
the `claude_code` preset and appends our rules. The preset already carries
the operating rules for the built-in tools. `setting_sources` and `skills`
replace the skill scanner of stage 4. `allowed_tools` pre-approves the
read-only tools, so they never reach the permission callback - that is what
the `CanUseToolShadowedWarning` the file silences is about, and it means
`Read`, `Task`, `TodoWrite` and `Skill` are never prompted for. `hooks` and
`can_use_tool` are where our policy plugs in. `agents` is the subagent of
stage 15. `resume` is the session of stage 8. The sandbox of stage 12 is
one flag, and it is skipped on Windows.

What is still ours: every value in this call. The SDK supplies the fields.
It does not tell you what to put in them.

### 2. Policy, still two layers

Stage 11 checked every tool call in `execute()` and returned allow, ask or
deny. The SDK splits that into two primitives. A `PreToolUse` hook runs
before any permission prompt. A `can_use_tool` callback runs after it.

`harness.py`:

```python
async def deny_dangerous(input_data, tool_use_id, context):
    command = input_data.get("tool_input", {}).get("command", "")
    if rules.decide(command) == "deny":
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Blocked by policy: {command}",
            }
        }
    return {}
```

A deny from this hook is final. Nobody can override it at the prompt. The
hook is matched to `Bash` only, through `HookMatcher(matcher="Bash")` in the
options. It returns an empty dict to let the call through to the next layer.

`harness.py`:

```python
async def can_use_tool(tool_name, tool_input, context):
    if tool_name == "Bash":
        verdict, reason = rules.check_bash(tool_input.get("command", ""))
    elif tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        # the CLI sends absolute paths; rules.PROJECT is the directory the harness started in
        verdict, reason = rules.check_edit(tool_input.get("file_path", ""))
    else:
        verdict, reason = "allow", None

    if verdict == "deny":
        return PermissionResultDeny(message=f"Blocked by policy: {reason}")
    if verdict == "ask" and not await asyncio.to_thread(confirm, reason):
        return PermissionResultDeny(message="The user declined this tool call.")
    return PermissionResultAllow()
```

This is the allow / ask half. It calls the same `rules.py` as stage 11,
unchanged. The `confirm` prompt runs in a thread because the callback is
async and `input()` blocks. The SDK owns the mechanics: it pauses the tool
call, waits for the result object, and feeds a deny back to the model as
the tool result. The table of rules is still ours.

### 3. Late injection is a hook

Stage 6 built a module to attach an `<env>` block to the newest user
message only, so the cached prefix stayed stable. The SDK primitive is the
`UserPromptSubmit` hook. Its `additionalContext` field attaches to that
prompt and nothing else.

`harness.py`:

```python
def env_block():
    branch = git("branch --show-current").strip() or "(no git)"
    return f"<env>\ntime: {datetime.now():%Y-%m-%d %H:%M}\ngit branch: {branch}\n</env>"


async def env_context(input_data, tool_use_id, context):
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": env_block()}}
```

Same cache reasoning as stage 6, one function instead of a module. Claude
Code already injects its own reminders for changed files (stage 7) and the
todo list (stage 10). Only the `<env>` block is ours.

### 4. A subagent is data

Stage 15 wrote a second loop with four rules: fresh context, withheld tools,
the same executor, and only the report comes back. The SDK primitive is
`AgentDefinition`. The built-in `Task` tool runs the loop.

`harness.py`:

```python
EXPLORER = AgentDefinition(
    description="Explores the codebase and reports findings. Use for 'where is X' and 'how does Y work'.",
    prompt=SUBAGENT_PROMPT,
    tools=["Read", "Grep", "Glob", "Bash"],  # withheld: Write, Edit, Task, TodoWrite
    model="haiku",
    maxTurns=12,
)
```

The four rules are now fields. `tools` withholds the edit tools and `Task`
itself, so the subagent cannot write and cannot recurse. `maxTurns` is the
turn cap. `model="haiku"` is new: a cheaper model for exploration. Ours are
the prompt, the tool list and the description the main agent reads when it
decides to delegate.

### 5. The custom tool is an in-process MCP server

Stage 2.2 registered tools by hand with a schema dict. The SDK primitive is
the `@tool` decorator plus `create_sdk_mcp_server`. The server never leaves
the process.

`harness.py`:

```python
@tool("run_tests", "Run the project's pytest suite and return the last 30 lines.", {"path": str})
async def run_tests(args):
    return {"content": [{"type": "text", "text": run_tests_impl(args.get("path", "."))}]}


SERVER = create_sdk_mcp_server(name="harness", version="1.0.0", tools=[run_tests])
```

The decorator takes the name, the description and the argument types. The
result is an MCP content list. The tool is registered as
`mcp__harness__run_tests`, and that name in `allowed_tools` pre-approves it.
The implementation in `run_tests_impl` is plain Python and is ours; it
returns the last 30 lines and the exit code, so an empty run is still
readable.

### 6. Presentation is a type switch

Stage 3 drew tool calls and a usage line from a dict. The SDK streams typed
objects instead: `AssistantMessage`, `UserMessage`, `ResultMessage`.

`harness.py`:

```python
def show(message):
    """Render one SDK message. Subagent traffic is indented."""
    if isinstance(message, AssistantMessage):
        pad = "        " if message.parent_tool_use_id else "  "
        for block in message.content:
            if isinstance(block, TextBlock) and block.text.strip():
                print(f"{pad}agent> {block.text.strip()}")
            elif isinstance(block, ToolUseBlock):
                print(f"{pad}tool> {block.name} {compact(block.input)}")
    ...
    elif isinstance(message, ResultMessage):
        usage = message.usage or {}
        cost = message.total_cost_usd or 0
```

`parent_tool_use_id` is set on subagent traffic, so the indent from stage
15 is one field check. `ResultMessage` carries real token counts and a
dollar cost. The SDK does not draw anything. The whole screen is ours.

### 7. The loop, with sessions

Stage 1 wrote the input loop. Stage 8 added sessions and resume. Here the
SDK primitive is `ClaudeSDKClient`, which holds one session for its
lifetime.

`harness.py`:

```python
def ended(message):
    """Does this message close the turn? A ResultMessage always does; so does the
    compact boundary, because a bare `/compact` may not be followed by a result."""
    return isinstance(message, ResultMessage) or (isinstance(message, SystemMessage) and message.subtype == "compact_boundary")


async def turn(client, text):
    """Send one prompt and draw everything that comes back. Never raises past here."""
    try:
        await client.query(text)
        async for message in client.receive_messages():
            show(message)
            if ended(message):
                break
    except ClaudeSDKError as failure:  # the CLI died or the connection dropped: say so, keep the prompt
        print(f"  error: {type(failure).__name__}: {failure}")
```

```python
    while True:  # reconnect loop: /resume swaps the session underneath
        async with ClaudeSDKClient(options=build_options(resume)) as client:
            while True:
                try:
                    text = input("\n> ").strip()
                except (EOFError, KeyboardInterrupt):
                    return
                if text in ("/exit", "/quit"):
                    return
                if not text:
                    continue
                if text == "/sessions":
                    for s in sessions_here():
                        print(f"  {s.session_id}  {(s.summary or '')[:60]}")
                    continue
                if text.startswith("/resume "):
                    resume = text.split(maxsplit=1)[1]
                    break  # leave the client; the outer loop reconnects with resume=
                # /compact and other built-in slash commands go straight through
                await turn(client, text)
```

`query()` sends a prompt. `receive_messages()` yields messages until we
stop reading; `ended()` decides when. The SDK's own `receive_response()`
stops at a `ResultMessage` and *only* there, and it never ends if none
arrives, so the loop also stops at the `compact_boundary` system message
that a `/compact` produces. The session id is fixed when the client opens,
so `/resume` leaves the client and the outer loop opens a new one.
`/compact` is not handled here at all. The CLI treats it as a built-in
command, which replaces the compaction agent of stage 14.

## Run it

Prerequisites: Python 3.10+, `pip install claude-agent-sdk` (the wheel bundles
its own `claude` binary under `claude_agent_sdk/_bundled/`), and either a
logged-in `claude` CLI or `ANTHROPIC_API_KEY`.

bash:

```bash
pip install claude-agent-sdk
export ANTHROPIC_API_KEY=sk-ant-...   # or: claude login
python harness.py
```

PowerShell:

```powershell
pip install claude-agent-sdk
$env:ANTHROPIC_API_KEY = "sk-ant-..."
python harness.py
```

Then:

```text
> where does the permission decision get made in this file? then add a comment there
> /sessions
> /compact
```

### Expected output

```text
  simple coding harness · claude agent sdk · /sessions, /resume <id>, /compact
  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave

> where does the permission decision get made in this file? then add a comment there
  tool> Task {"description": "find permission decision", "prompt": "In harness.py, where…
        agent> can_use_tool at harness.py:122 returns PermissionResultAllow/Deny; deny_dangerous…
  tool> Edit {"file_path": "C:\\...\\harness.py", "old_string": "async def can_use_tool", "new_str…
      The file has been updated…
  agent> Added a comment above `can_use_tool` explaining the two layers.

  12,410 in · 318 out · 11,776 cached · $0.0231 · session 7f0c…
```

The indented lines are the explorer subagent. The last line is the
`ResultMessage`: real token counts, the dollar cost, and the session id
that `--resume` or `/resume <id>` picks up.

Offline tests (`python -m pytest test_step.py`) cover the policy, the hooks,
the option wiring, the turn-ending rule and the error path, without
launching Claude.

## Error handling

- **A bad or failing tool call.** The SDK owns the tools, and Claude Code
  already returns tool errors as results; the model reads them. Our
  `run_tests` tool returns its output and exit code whatever pytest did, and
  `Error: command timed out after 300s` if it hung.
- **A denied call.** A hook deny or a `PermissionResultDeny` reaches the
  model as the tool result, with the reason.
- **A dead CLI or connection.** `turn()` catches `ClaudeSDKError`, prints
  `error: <type>: <message>` and returns to the prompt; the client is still
  open. If the CLI itself is gone, the next prompt fails the same way -
  restart with `--resume` to continue the session.
- **ctrl-c at the approval prompt** answers no. **ctrl-c at the main prompt**
  leaves; **ctrl-c while a turn runs** leaves too, printing `interrupted`
  instead of a traceback, and `--resume` picks the session up.
- **Leaving.** `/exit`, ctrl-d (ctrl-z then enter on Windows) or ctrl-c at
  the prompt. An empty line does nothing.

## Gotchas / what this is not

- The screen is not the SDK's. Every message arrives as a typed object and
  you decide how it looks; that is what `show()` does in forty lines.
- The policy is not the SDK's either. Without `can_use_tool` and the hook you
  get Claude Code's default permission prompts, not your rules.
- `/compact` goes to the CLI as a prompt. If a CLI version answers it without
  a `ResultMessage`, `ended()` is what keeps the loop from waiting forever.
- `rules.PROJECT` is the directory the harness started in, and `cwd=` hands
  the same directory to the CLI. Start the harness in the project root.
- The sandbox flag is skipped on Windows; there is no OS sandbox there.

## What the next step adds

Step 17 rebuilds the same harness on the OpenAI Agents SDK, where the loop
and sessions are the SDK's but the coding tools are ours again.

<!-- harness-learning-check -->
## Check your understanding

When an SDK owns the loop, which responsibility remains for the application?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

The application still defines the task, configures capabilities and checks observed behavior. Inspect the specific SDK contract instead of assuming every control is supplied.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
