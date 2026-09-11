# Step 18 - The same harness on the Google Antigravity SDK

**What this step adds:** the whole runtime lives in a binary that ships
inside the `google-antigravity` wheel: loop, coding tools, subagents,
compaction, sessions, skills. Python configures it. Our contribution is a
policy list, three hooks, one subagent definition and two tools.

`pip install google-antigravity` (Apache-2.0, Python 3.10+, wheels for
Linux, macOS and Windows). Auth is `GEMINI_API_KEY`, or Vertex credentials.
The runtime can also be pointed at an OpenAI-compatible endpoint with
`LocalOpenAIAgentConfig(base_url=...)`. Same harness, different model.

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

## The code, piece by piece

### 1. Policy is a list, not code

Stage 11 wrote a `check()` function that matched a command against a rules
table. The SDK primitive is a policy list: `allow`, `ask_user` and `deny`
entries, each with an optional `when=` predicate. The runtime compiles the
list into a decide hook with `enforce()`.

`harness.py`:

```python
def build_policies(handler=confirm):
    return [
        *[allow(t.value) for t in BuiltinTools.read_only()],
        allow("ask_question"), allow("start_subagent"),
        # the shell: the strictest verdict of the compound command decides
        deny("run_command", when=is_denied, name="denied by rules"),
        ask_user("run_command", handler=handler, when=needs_ask, name="ask by rules"),
        allow("run_command", when=is_plain, name="read-only command"),
        # edits: silent inside the project, a prompt outside it
        allow("edit_file", when=edit_inside), allow("create_file", when=edit_inside),
        ask_user("edit_file", handler=handler, when=edit_outside),
        ask_user("create_file", handler=handler, when=edit_outside),
        # no network, no images: the same lines the bash rules drew
        deny("search_web"), deny("read_url_content"), deny("generate_image"),
    ]
```

Read-only built-ins are allowed outright. The shell tool gets three rows,
one per verdict. Edit tools are silent inside the project and prompt
outside it. Network tools are denied, which draws the same line the
`curl` and `wget` rules drew in stage 11. The predicates are ours and call
the stage 11 `rules.decide` unchanged.

`harness.py`:

```python
def is_denied(call: ToolCall) -> bool:
    return rules.decide(command_of(call)) == "deny"


def needs_ask(call: ToolCall) -> bool:
    return rules.decide(command_of(call)) == "ask"


def is_plain(call: ToolCall) -> bool:
    return rules.decide(command_of(call)) == "allow"
```

`command_of` reads the command out of `ToolCall.args`. It accepts several
key spellings because the runtime, not us, names the arguments. The offline
test compiles the policy list and checks the same verdicts as stage 11.

### 2. Hooks: a second deny layer and an audit line

Stage 11 had one gate. Here there are two, as in step 16. The SDK
primitives are decorated hooks: `@pre_tool_call_decide` runs before a
tool and returns a `HookResult`, `@post_tool_call` runs after it.

`harness.py`:

```python
@pre_tool_call_decide
def block_dangerous(call: ToolCall) -> HookResult:
    """Second layer, independent of the policy list: a deny here is final."""
    if call.name == "run_command" and is_denied(call):
        return HookResult(allow=False, message=f"Blocked by policy: {command_of(call)}")
    return HookResult(allow=True)


@post_tool_call
def audit(result: ToolResult):
    body = result.error or result.result
    first = str(body or "(no output)").strip().splitlines()[:2]
    print(f"  tool> {result.name}  {' / '.join(first)[:110]}")
```

`block_dangerous` denies on its own, independent of the policy list. A
deny here cannot be undone by a later policy row. `audit` is the tool line
of stage 3: name plus the first two lines of the result. Decorated hooks
stay directly callable, so the test for `block_dangerous` is one line.
The third hook, `note_compaction`, prints one line when the runtime
compacts. That replaces the whole compaction agent of stage 14.

### 3. Custom tools are just functions

Stage 2.2 registered each tool with a hand-written schema. Here the SDK
primitive is a plain function in `tools=[...]`. The runtime reads the type
hints and the docstring.

`harness.py`:

```python
def run_tests(path: str = ".") -> str:
    """Run the project's pytest suite on a path and return the last 30 lines."""
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", path],
                                capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return "Timed out after 300s and was killed."
    lines = (result.stdout + result.stderr).strip().splitlines()
    return "\n".join(lines[-30:]) or "(no output)"
```

```python
def write_todos(todos: list[str]) -> str:
    """Replace the plan. One line per item, prefixed [ ] pending, [~] in progress, [x] done. Keep exactly one [~]."""
    if sum(1 for t in todos if t.startswith("[~]")) > 1:
        return "Error: keep exactly one item marked [~]."
    TODOS[:] = todos
    return "\n".join(TODOS) or "Todo list cleared."
```

There is no schema to write. `write_todos` is the tool of stage 10, with a
simpler shape: one string per item. The runtime has no todo tool, so this
one and its re-injection are ours. The "exactly one in progress" rule is
enforced by the tool, as before.

### 4. A subagent is a config object

Stage 15 wrote a second loop with fewer tools. The SDK primitive is
`SubagentConfig`. The built-in `start_subagent` tool runs the loop.

`harness.py`:

```python
EXPLORER = SubagentConfig(
    name="explorer",
    description="Explores the codebase and reports findings. Use for 'where is X' and 'how does Y work'.",
    system_instructions=(
        "You are an exploration subagent. Answer the one question you were given by reading the "
        "codebase, then report in under 150 words: paths with line numbers, names, values. "
        "You cannot edit anything. Say plainly what you could not find."
    ),
    # withheld: edits, run_command and start_subagent - so it cannot write and cannot recurse
    capabilities=SubagentCapabilities(enabled_tools=list(BuiltinTools.read_only())),
)
```

`enabled_tools` is the read-only set. Edits, the shell and
`start_subagent` are absent, so the subagent cannot write and cannot
recurse. The four rules of stage 15 are fields. The prompt and the
description are ours. The loop, the fresh context and the return of only
the report are the runtime's.

### 5. The whole configuration

Stages 1, 4, 8, 12 and 14 each added a piece of setup. Here the SDK
primitive is `LocalAgentConfig`, and every piece is one field.

`harness.py`:

```python
def build_config(resume=None, handler=confirm):
    return LocalAgentConfig(
        system_instructions=SYSTEM,
        tools=[run_tests, write_todos],
        policies=build_policies(handler),
        hooks=[block_dangerous, audit, note_compaction],
        capabilities=CapabilitiesConfig(
            enable_subagents=True,
            max_subagent_depth=1,
            allowed_subagents=["explorer"],
            run_command_config=RunCommandConfig(timeout_seconds=60, enable_sandbox=sys.platform != "win32"),
        ),
        subagents=[EXPLORER],
        skills_paths=[str(Path.cwd() / ".agents" / "skills")],  # step 4
        workspaces=[str(Path.cwd())],
        save_dir=str(HOME),                                     # step 8
        conversation_id=resume,
        session_continuation_mode=SessionContinuationMode.RESUME if resume else None,
    )
```

`max_subagent_depth=1` is the "one level deep" rule of stage 15 as a
number. `RunCommandConfig` carries the timeout of stage 11 and the sandbox
of stage 12. `skills_paths` points at the same directory stage 4 scanned.
`save_dir` and `conversation_id` are the sessions of stage 8. The runtime
stores and resumes them. We only pass the id.

### 6. Late injection and the chat loop

Stage 6 attached an `<env>` block to the newest user message. The runtime
keeps its own context, so there is no hook for this. We prepend the block
to the prompt ourselves.

`harness.py`:

```python
def late_block():
    branch = git("branch --show-current").strip() or "(no git)"
    todos = ("\n<todos>\n" + "\n".join(TODOS) + "\n</todos>") if TODOS else ""
    return f"<env>\ntime: {datetime.now():%Y-%m-%d %H:%M}\ngit branch: {branch}\n</env>{todos}\n\n"
```

```python
            response = await agent.chat(late_block() + text)
            print("\n  agent> ", end="", flush=True)
            async for token in response:
                sys.stdout.write(str(token))
                sys.stdout.flush()
            print()
            usage = response.usage_metadata
            if usage:
                print(f"  {usage}")
```

`agent.chat()` is the loop of stage 2.4. The response streams tokens, and
`usage_metadata` gives the usage line of stage 3. The block carries the
todo list of stage 10 as well. This is the one place where the runtime
gives us less than the hand-built harness had. The block lands in the
stored conversation, because the runtime sees it as part of the prompt.

## Run it

```bash
pip install google-antigravity
export GEMINI_API_KEY=...
python harness.py
you> start the explorer subagent to find where policies are built, then add a comment there and run the tests
```

The conversation id is printed at start; `python harness.py --resume <id>`
picks it up. Offline tests: `python -m pytest test_step.py`.

## What the SDK does not give you

A todo tool, a late-injection hook, and the screen. The plan and its
re-injection are ours. The `<env>` block rides inside the prompt. Tool
lines and the usage line are printed by our hooks and our loop.

## Caveats

The SDK is at 0.1.x. The tool argument names the runtime uses
(`command`, `path`, ...) are read defensively in `arg()`; if a policy never
fires, print the `ToolCall.args` in `audit` and adjust the keys. The sandbox
flag is skipped on Windows.
