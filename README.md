# Zero to Hero: Harness Engineering

## Build a coding agent from one API call to a full harness, then run it on four SDKs, OpenRouter and an open-source harness server

**Models are commodities. The harness is the product.** The same model
behaves like a toy or like a colleague depending on the loop around it.
This codelab builds that loop.

You have used a coding agent. You typed a request, it read files, ran
commands, edited code, and came back with an answer. This codelab shows you
what is inside that box, by building one. You start with a single API call.
You end with a harness that has tools, skills, sessions, permissions, a
sandbox, compaction and subagents. Then you rebuild the same harness on four
agent SDKs to see what each one gives you, and you point it at OpenRouter to
route between models and track cost.

Every step is a directory you can run. Every step has a test you can run
without a key. Every step's README shows the code with an explanation under
each snippet.

**What you will build**

```text
Part 1   stages 1 - 15    a coding agent harness, by hand, one idea per stage
Part 2   steps 16 - 19    the same harness on four agent SDKs
Part 3   step 20          the same harness on OpenRouter, with routing and cost
Part 4   steps 21 - 30    ten more capabilities: streaming, parallel tools, browser use,
                          computer use, memory, MCP, hooks, plan mode, background jobs, evals
Part 5   steps 31 - 38    durability, context and orchestration: instruction files, context
                          budget, checkpoints, recovery, human in the loop, pipelines,
                          production anatomy, capstone
Part 6   steps 39 - 45    the production surface: approval modes, handoffs, stop conditions,
                          streaming tool output, extensions, replay, TypeScript core
Part 7   steps 46 - 51    the same harness on TrueForge, an open-source harness server:
                          loop, tools as MCP, sandbox and skills, context, subagents, comparison
```

A second series lives in [`genui/`](genui/): **zero to hero on generative
UI**, where the agent's output becomes an interface. It continues this
codelab into the user-facing side with AG-UI, A2UI, OpenUI Lang,
json-render and MCP Apps.

**What you will learn**

- Why an agent is a loop, and what the loop is made of.
- How tool calls work: a schema for the model, a function for you.
- Why you must never change the beginning of the prompt.
- How to inject fresh facts without breaking the cache.
- How to keep a transcript inside the context window.
- How to gate and sandbox what the agent can do.
- How to run a subagent in a throwaway context.
- Which of those ideas each SDK does for you, and which stay yours.
- How a browser, a desktop, external MCP servers and persistent memory
  plug into the same loop, and how to measure whether any of it helped.

**What you need**

- Python 3.10 or newer.
- A key for any endpoint that speaks the OpenAI chat API. OpenRouter is the
  default and gives you many models with one key.
- About two hours for Parts 1 to 3, and two more for each of Parts 4 to 6.
  Each step takes a few minutes.

---

## Step 0: Set up

### Install

```bash
git clone https://github.com/dlmastery/simple-coding-harness
cd simple-coding-harness
pip install -r requirements.txt
```

### Set the endpoint

The harness uses the `openai` client. Any endpoint that implements the same
API works. Set three variables.

| Variable | What it is | Example |
|----------|------------|---------|
| `BASE_URL` | the endpoint | `https://openrouter.ai/api/v1` |
| `API_KEY` | your key for that endpoint | `sk-or-...` |
| `MODEL` | a model id that supports tool calling | `deepseek/deepseek-v4-flash` |

```bash
# OpenRouter: one key, many models
export BASE_URL=https://openrouter.ai/api/v1 API_KEY=sk-or-... MODEL=deepseek/deepseek-v4-flash

# OpenAI
export BASE_URL=https://api.openai.com/v1 API_KEY=sk-... MODEL=gpt-4.1-mini

# Gemini
export BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/ API_KEY=AIza... MODEL=gemini-2.5-flash

# Ollama, local
export BASE_URL=http://localhost:11434/v1 API_KEY=ollama MODEL=qwen2.5-coder
```

On Windows PowerShell, use `$env:BASE_URL = "..."` for each one.

### Check that everything works

The tests do not need a key. They run each stage against a fake model.

```bash
python run_tests.py
```

You should see one line per stage ending in `passed`. If you do, you are
ready.

> **How to read this codelab.** Each step has the same shape: the goal, the
> idea, the code, a command to try, what you should see, and one takeaway.
> Each step's directory has a longer README with every snippet explained.
> Each README ends with a `diff` command that shows exactly what changed
> from the step before.

---

# Part 1: Build the harness by hand

## Stage 1: One API call

**Goal.** Send a prompt to a model and print the reply.

**The idea.** A model call is a list of messages in and one message out.
There is no hidden state. The model sees only the list you send.

**The code.** `step_01_minimal_chat/llm.py`:

```python
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ],
)
```

The system prompt is the first message. The user's text is the second. The
reply is at `response.choices[0].message`. The script also prints the token
usage, and you will watch one of those numbers, `cached_tokens`, grow in
later stages.

**Try it.**

```bash
cd step_01_minimal_chat
python llm.py
Enter your prompt> hi
```

**You should see** one reply and a usage line with prompt and completion
token counts.

**Takeaway.** Everything that follows is this file plus one idea at a time.

---

## Stage 2.1: The first tool

**Goal.** Let the model ask you to run a shell command.

**The idea.** A tool is two things in two worlds. A JSON schema tells the
model that a function exists and what arguments it takes. A Python function
does the work. The model never executes anything. It replies with a *tool
call*, a function name and JSON arguments, and stops. Your code runs the
function.

**The code.** `step_02_1_bash_tool/llm.py`:

```python
def bash(command):
    """The Python behind the schema. subprocess.run executes what the model chose."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr
```

```python
if message.tool_calls:
    tool_call = message.tool_calls[0]
    command = json.loads(tool_call.function.arguments)["command"]
    print("Tool: bash", command)
    print(bash(command), "\n")
```

**Try it.**

```bash
cd step_02_1_bash_tool
python llm.py
Enter your prompt> what is your current directory? use the bash tool
```

**You should see** `Agent: None`, then `Tool: bash pwd`, then the path. The
model did not write text. It wrote a tool call.

**Takeaway.** The split between schema and function is the security model of
every coding agent. The model proposes. Your code disposes.

---

## Stage 2.2: A tool registry

**Goal.** Make the next tool cost one function and one schema.

**The idea.** Put the schemas in a list the model sees and the functions in a
dictionary keyed by the same names. The model's function name becomes a
dictionary lookup. The JSON arguments become keyword arguments.

**The code.** `step_02_2_generic_tools/llm.py`:

```python
    result = TOOLS[tool_call.function.name](**args)  # name -> function, JSON -> kwargs
```

**Try it.** Same as stage 2.1. The behaviour is the same. The structure is
new.

**Takeaway.** Every later capability, read, write, edit, skills, todos,
subagents, is one entry in each table.

---

## Stage 2.3: A read tool

**Goal.** Add `read_file` without touching `llm.py`.

**The code.** `step_02_3_read_file/tools.py`:

```python
def read_file(path: str) -> str:
    """Read a file and return its contents."""
    with open(path) as f:
        return f.read()
```

**Try it.**

```bash
cd step_02_3_read_file
python llm.py
Enter your prompt> can you read the llm.py file
```

**You should see** the model call `read_file` and the file printed on your
screen.

**Takeaway.** The file went to *your* screen, not to the model. The model
cannot use what it read. That is the problem the next stage solves.

---

## Stage 2.4: The agent loop

**Goal.** Feed tool results back to the model until it answers in text.

**The idea.** An agent is a loop around a model call. Send the transcript.
Add the reply. If the reply has tool calls, run them, add each result with
role `tool`, and send again. If the reply has no tool calls, stop.

**The code.** `step_02_4_agent_loop/agent.py`:

```python
while True:
    # 1. the model sees the whole transcript so far
    message, usage = call_llm(messages)
    # 2. its reply joins the transcript - tool calls included, because every
    #    "tool" message must follow the assistant message that asked for it
    messages.append(message.model_dump(exclude_none=True))

    if message.content:
        print("\nAgent: ", message.content, "\n")

    # 3. no tool calls means it has answered; the loop is done
    if not message.tool_calls:
        break

    # 4. otherwise run each call and feed the result back, tied to the call by id
    for tool_call in message.tool_calls:
        args = json.loads(tool_call.function.arguments)
        result = TOOLS[tool_call.function.name](**args)
        print("Tool: ", tool_call.function.name, args)
        print(result, "\n")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })
```

Two details matter. The assistant message is stored with its tool calls,
because the API rejects a `tool` message that does not follow the assistant
message that asked for it. Each result carries the `tool_call_id` of the
call it answers.

**Try it.**

```bash
cd step_02_4_agent_loop
python agent.py
Enter your prompt> explain what happens in llm.py and agent.py
```

**You should see** three or four tool calls in a row, then one explanation.
That is several model calls for one question. That is the loop working.

**Takeaway.** This loop never changes in spirit for the rest of Part 1. And
it introduces the rule that shapes the rest of the build: the whole
transcript is re-sent on every call, providers cache the unchanged prefix,
so **never change the beginning of the prompt**.

---

## Stage 3: A terminal you can use

**Goal.** Make the agent a chat, and make the screen readable.

**The idea.** Wrap the loop in a second loop that asks for your next message.
Move all drawing into `ui.py`, which knows nothing about models or tools.
Show a usage line after every call.

**The code.** `step_03_better_ui/agent.py`:

```python
while True:
    user_input = ui.ask()
    if not user_input:
        break

    messages.append({"role": "user", "content": user_input})

    while True:
        with ui.working():
            message, usage = call_llm(messages)
```

**Try it.**

```bash
cd step_03_better_ui
python agent.py
> what does this repo do?
> and what is ui.py for?
```

**You should see** the second question answered from memory of the first.
Look at the usage line. Most of the prompt tokens are marked `cached`.

**Takeaway.** The transcript is the memory. The usage line is where prefix
caching becomes visible.

---

## Stage 4: Skills

**Goal.** Let the agent follow a written procedure when a task matches.

**The idea.** A skill is a `SKILL.md` file with a YAML front matter. Only the
name and description go into the system prompt. The body is read on demand
with a `read_skill` tool. A project can ship fifty skills and pay for fifty
lines of context, not fifty documents.

**The code.** `step_04_skills/skills.py`:

```python
def skills_prompt():
    """One line per skill: the index that goes into the system prompt."""
    return "\n".join(f"- {name}: {s['description']}" for name, s in SKILLS.items())


def read_skill(name: str) -> str:
    """Open a skill and return its full instructions."""
    if name not in SKILLS:
        return f"No skill named '{name}'."
    return SKILLS[name]["path"].read_text(encoding="utf-8")
```

**Try it.**

```bash
cd step_04_skills
python skills.py                 # prints the index the model will see
python agent.py
> explain what agent.py does
```

**You should see** a `read_skill` call before the explanation, and an
explanation that follows the skill's four rules.

**Takeaway.** Index in the prompt, body on demand. This is how every major
coding agent handles skills and rules files.

---

## Stage 5: Editing files

**Goal.** Let the agent change code.

**The idea.** `write_file` creates a file. `str_replace` swaps one exact
block of text for another. It refuses if the text is missing or matches
more than once, and the refusal is the tool's result, so the model reads it
and retries with a more specific match.

**The code.** `step_05_file_editing/tools.py`:

```python
    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str was not found in {path}"
    if count > 1 and not allow_multi_edit:
        return (
            f"Error: old_str matches {count} times in {path}. "
            "Add surrounding lines to make it unique, "
            "or set allow_multi_edit to replace them all."
        )
```

**Try it.**

```bash
cd step_05_file_editing
python agent.py
> write a new file called hello.txt with five hello worlds
> replace every hello world with goodbye
```

**You should see** a `write_file` call, then a `read_file` and a
`str_replace` call, and a file with five `goodbye` lines.

**Takeaway.** Errors are results. Nothing the model does can crash the
session. It reads the error and adapts.

---

## Stage 6: Late injection

**Goal.** Give the model fresh facts on every call without breaking the
cache.

**The idea.** Some facts change on every call: the time, the git branch.
Build them into a small block and append it to the *request*, at the end.
Never store it in the transcript.

**The code.** `step_06_late_injection/agent.py`:

```python
            message, usage = call_llm(messages + [reminder()])  # request = transcript + late block
```

`messages + [reminder()]` builds a new list for this request only. The stored
transcript never contains the block.

**Try it.**

```bash
cd step_06_late_injection
python agent.py
> what branch am I on and what time is it?
```

**You should see** the answer with no tool call. The model read it from the
block.

**Takeaway.** Stable things first, volatile things last, the middle never
edited. Stages 7 and 10 both ride in this block.

---

## Stage 7: File freshness

**Goal.** Warn the agent when a file changed under it.

**The idea.** The tools record the modification time of every file they
touch. If a file changes on disk before the next call, the late block
carries a reminder to read it again before editing.

**The code.** `step_07_file_freshness/context.py`:

```python
def stale_note():
    """Warn about files that changed on disk since the agent read them."""
    changed = stale_files()
    if not changed:
        return ""
    return (
        "\n<system-reminder>\n"
        "These files changed on disk since you read them. Read them again "
        "before editing:\n" + "\n".join(changed) + "\n</system-reminder>"
    )
```

**Try it.** Ask the agent to read a file. Edit that file in your editor.
Then ask the agent to change it.

**You should see** the reminder in the late block, and a fresh `read_file`
before the edit.

**Takeaway.** The model's picture of a file is whatever it last read. The
harness has to tell it when that picture is stale.

---

## Stage 8: Sessions and rewind

**Goal.** Save every chat. Reopen it. Undo it.

**The idea.** Append every message to a JSONL file as it happens. A rewind
is an entry in the file, not a deletion, so the file is the full history.
Loading replays the file and applies the markers.

**The code.** `step_08_sessions_rewind/session.py`:

```python
def save(messages):
    """Append what is new. Never rewrite what is already on disk."""
    global WRITTEN
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        for message in messages[WRITTEN:]:
            f.write(json.dumps(message) + "\n")
    WRITTEN = len(messages)
```

**Try it.**

```bash
cd step_08_sessions_rewind
python agent.py
> what is in this folder?
> /rewind
> /sessions
python agent.py --resume
```

**You should see** a numbered list to rewind to, the screen redrawn from the
transcript, and the last chat reopened with `--resume`.

**Takeaway.** Slash commands never reach the model. A command takes the
message list and returns the list to continue with.

---

## Stage 9: An installable command

**Goal.** Run the harness from any directory.

**The idea.** Move the files into a `harness/` package, put the loop in
`main()`, read credentials from `config.py`, and declare a console script in
`pyproject.toml`.

**Try it.**

```bash
cd step_09_installable_command
pip install -e .
cd ~/some/other/project
harness
```

**You should see** the same chat, in that project. Skills, sessions and git
status all key off the directory you run it in.

**Takeaway.** From here on, `~/.simple-harness/env` can hold your three
variables, so you set them once.

---

## Stage 10: Todos

**Goal.** Keep the agent on plan through a long task.

**The idea.** A `write_todos` tool replaces the plan on every call. Exactly
one item may be in progress. The plan lives in a variable, not in the
transcript, and rides in the late block, so it is the last thing the model
reads before it acts.

**The code.** `step_10_todos/harness/todos.py`:

```python
def write_todos(todos):
    """Replace the whole list. Exactly one task may be in_progress."""
    active = [t for t in todos if t["status"] == "in_progress"]
    if len(active) > 1:
        return f"Error: {len(active)} tasks are in_progress. Only one may be."

    TODOS[:] = todos
    return todos_prompt() or "Todo list cleared."
```

**Try it.**

```bash
harness
> create a todo list with three things: write hello.txt with five hello
  worlds, write a Python file that prints a star pattern, and write another
  with the Fibonacci series. then do them.
```

**You should see** the plan written first, then updated as each item
completes, and the in-progress item as the spinner label.

**Takeaway.** Twenty tool calls later, the plan is still in front of the
model.

---

## Stage 11: Permissions

**Goal.** Decide which tool calls need a human.

**The idea.** A rule table rates every command. Read-only commands run
silently. Risky commands stop and ask you. A few are refused whatever you
answer. Compound commands are split and the strictest part wins. The
verdict is returned as the tool result.

**The code.** `step_11_permissions/harness/permissions.py`:

```python
def decide(command):
    """Rate every part of a compound command; the strictest verdict wins."""
    verdicts = []
    for part in split_command(command):
        action = "ask"
        for pattern, rule in BASH_RULES.items():
            if fnmatch(part, pattern):
                action = rule
        verdicts.append(action)
    for strictest in ("deny", "ask"):
        if strictest in verdicts:
            return strictest
    return "allow"
```

**Try it.**

```bash
harness
> delete the __pycache__ folders
```

**You should see** `Blocked by policy` when the model reaches for `rm -rf`,
and the model finding another way or explaining.

**Takeaway.** The rules only see the command text. A Python one-liner can
still delete a file. This is not real security. The next stage is.

---

## Stage 12: Sandbox

**Goal.** Make the kernel enforce what the agent can touch.

**The idea.** Run `bash` inside an OS sandbox. Read anything, write only
inside the project, no network. On macOS that is Seatbelt. On Linux it is
bubblewrap. A script that deletes a file outside the project fails even when
you approved the command. Every command also has a timeout that comes back
as a result.

**The code.** `step_12_sandbox/harness/sandbox.py`:

```python
PROFILE = f"""(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "{PROJECT}") (literal "/dev/null"))
(deny file-write* (subpath "{PROJECT}/.git"))
"""
```

**Try it.** On macOS or Linux, ask the agent to delete a file outside the
project and say yes at the prompt.

**You should see** `operation not permitted`. The banner shows which
sandbox is active. On Windows it shows `sandbox: none`.

**Takeaway.** Permissions ask whether to interrupt you. The sandbox asks
whether the operation is possible at all.

---

## Stage 13: Readable todos and a real input line

**Goal.** Draw the plan as a checklist. Edit long prompts.

**The idea.** `write_todos` renders as `[x]`, `[~]`, `[ ]` rows. Typing goes
through prompt_toolkit, which can edit a wrapped line, keeps history and
inserts a newline on alt-enter. No change to the loop.

**Takeaway.** Presentation is separate from the loop, so it can improve
without touching it.

---

## Stage 14: Compaction

**Goal.** Keep the transcript inside the context window.

**The idea.** Tool output is the main reason transcripts explode, so it is
handled three ways. A fresh result over 10,000 characters is capped and the
rest goes to a temp file the model can page through. When a turn ends, its
results shrink to a 300-character stub. If a request is still too big, whole
results are dropped, oldest first. When the prompt passes 85% of the window,
a second agent with no tools writes a handoff note about the old messages.
The note is folded into the system prompt and the transcript is cut back to
35%.

**The code.** `step_14_compaction/harness/compact.py`:

```python
def compact(messages):
    """[system + summary, ...recent tail]. Unchanged if nothing is old enough."""
    cut = tail_start(messages, config.CONTEXT_WINDOW * config.COMPACT_TO)
    if cut <= 1:
        return messages

    system = messages[0]["content"]
    summary = summarize(messages[1:cut], previous_summary(system))
    kept = [
        {"role": "system", "content": base_prompt(system) + "\n\n" + HANDOFF.format(summary=summary)},
        *messages[cut:],
    ]
    strip(kept)  # the tail is old news too; shrink it now, while the prefix is already rebuilt
    return kept
```

**Try it.**

```bash
CONTEXT_WINDOW=6000 harness
> cat every file under harness
> /compact
```

**You should see** `[output trimmed: ...]` markers on long results, then the
handoff note in a panel and the message count drop.

**Takeaway.** The prefix is rebuilt once per compaction and then left alone
until the next one. Cheap mechanisms first, the expensive one rarely.

---

## Stage 15: Subagents

**Goal.** Explore a codebase without filling the main context.

**The idea.** A `task` tool runs a fresh agent on one question. It starts
with an empty transcript. It gets every tool except `task`, `write_todos`,
`write_file` and `str_replace`, so it cannot edit and cannot recurse. It
runs the same loop through the same permission check and sandbox. Only its
final answer returns.

**The code.** `step_15_subagents/harness/subagent.py`:

```python
WITHHELD = {"task", "write_todos", "str_replace", "write_file"}
```

```python
        # rule 4: no tool calls means it has stopped looking and started answering
        if not message.tool_calls:
            return report or "(the subagent came back with nothing)"
```

**Try it.**

```bash
harness
> use a sub agent to explore this repo and tell me what you find
```

**You should see** the question in a blue panel, the subagent's tool calls
indented under it, and then the main agent's summary. The subagent's tool
output never enters the main transcript.

**Takeaway.** Compaction throws context away after it is spent. A subagent
spends it somewhere that is thrown away by design.

You have built a coding agent harness from one API call. The full stage
index is at the end of this document.

---

# Part 2: The same harness on four agent SDKs

You now know the fifteen ideas. Each SDK below implements some of them for
you. Rebuilding the stage 15 harness on each one shows you exactly which
ideas the SDK owns and which stay yours. The permission rules from stage 11
are copied into every step unchanged. The SDK supplies the hook. You supply
the policy.

Install them all with `pip install -r requirements-sdks.txt`.

## Step 16: Claude Agent SDK

**What it is.** Claude Code as a library. It spawns the `claude` CLI and
speaks to it over JSON. The loop, the coding tools, sessions, compaction and
the `Task` subagent tool are built in.

**What you write.** Policy hooks, an injection hook, one custom tool, a
subagent definition, and the screen. `step_16_claude_agent_sdk/harness.py`:

```python
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
```

**Needs.** The `claude` CLI logged in, or `ANTHROPIC_API_KEY`.

## Step 17: OpenAI Agents SDK

**What it is.** A general agent framework: the runner loop, typed function
tools, SQLite sessions, approval pauses, guardrails, and agents as tools. It
has no coding tools, so the stage 5 tools come back and get wrapped.

**What you write.** The tools, skills, todos, a request filter that does
late injection and stripping, and the screen.
`step_17_openai_agents_sdk/harness.py`:

```python
bash = function_tool(_bash, name_override="bash", needs_approval=bash_needs_approval, tool_input_guardrails=[policy_gate], timeout=60)
```

```python
task = explorer.as_tool(
    tool_name="task",
```

**Needs.** `BASE_URL`, `API_KEY`, `MODEL`, as in Part 1.

## Step 18: Google Antigravity SDK

**What it is.** The Antigravity agent runtime shipped as a binary inside a
wheel, driven from Python. Coding tools, subagents, compaction, sessions and
skills are in the runtime.

**What you write.** A policy list, three hooks, a subagent config, two
tools, todos. `step_18_google_antigravity_sdk/harness.py`:

```python
EXPLORER = SubagentConfig(
    name="explorer",
    description="Explores the codebase and reports findings. Use for 'where is X' and 'how does Y work'.",
```

**Needs.** `GEMINI_API_KEY`.

## Step 19: DeepSeek Harness

**What it is.** A harness where everything is a plugin: the loop, the tool
registry, the model adapter, sessions and the permission gate are plugins
composed by a profile. The Python SDK drives a bundled runtime over JSON-RPC.

**What you write.** The policy as a plugin on the `tools/pre-execute` event,
the patch that mounts it, and the event renderer.
`step_19_deepseek_harness/plugin/simple-harness-plugin/src/index.js`:

```javascript
  ctx.on('tools/pre-execute', async (exec, next) => {
    if (!SHELL_TOOLS.has(exec.name)) return next()
    const command = commandOf(exec)
    const verdict = decide(command)
    if (verdict === 'deny') return { kind: 'deny', reason: `Blocked by policy: ${command}` }
    if (verdict === 'ask') return { kind: 'ask', reason: `run: ${command}` }
    return next()
  })
```

**Needs.** `DEEPSEEK_API_KEY`.

## Who owns which mechanism

| Mechanism (stage) | Hand-built | Claude Agent SDK | OpenAI Agents SDK | Antigravity SDK | DeepSeek Harness |
|------------------|:-:|:-:|:-:|:-:|:-:|
| agent loop (2.4) | you | SDK | SDK | runtime | runtime |
| coding tools (2.1-2.3, 5) | you | SDK | **you** | runtime | runtime |
| custom tools (2.2) | you | `@tool` + MCP server | `function_tool` | plain functions | `defineTool` plugin |
| skills (4) | you | SDK | **you** | runtime | runtime |
| late injection (6) | you | hook | request filter | prompt prefix | runtime |
| file freshness (7) | you | SDK | **you** | runtime | runtime |
| sessions / rewind (8) | you | SDK | `SQLiteSession` | runtime | runtime |
| todos (10) | you | SDK | **you** | **you** | runtime |
| permissions (11) | you | hook + callback | guardrail + approval pause | policy list + hook | plugin |
| OS sandbox (12) | you | SDK flag | - | runtime flag | provider seam |
| compaction (14) | you | SDK | **you** (strip only) | runtime | runtime |
| subagents (15) | you | `AgentDefinition` | `agent.as_tool()` | `SubagentConfig` | runtime |

Every **you** cell is code you can read in that step, and it is the same
code you wrote in Part 1.

---

# Part 3: The same harness on OpenRouter

## Step 20: Model routing and cost

**Goal.** Swap models without code changes, fall back when one fails, and
see what each call costs.

**The idea.** OpenRouter is one endpoint with one key in front of hundreds
of models. It speaks the OpenAI chat API, so the harness from stage 15 works
against it unchanged. What OpenRouter adds is routing, sent as extra fields
in the request body.

**The code.** `step_20_openrouter/harness/openrouter.py`:

```python
BASE_URL = "https://openrouter.ai/api/v1"
API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("API_KEY", "")
```

```python
    body = {
        "models": list(MODELS),        # the fallback route, primary first
        "usage": {"include": True},    # ask for usage.cost in the response
    }
    if PROVIDER:
        body["provider"] = dict(PROVIDER)
```

`MODELS` is an ordered route. The first model is the primary. The rest are
fallbacks OpenRouter uses when the primary fails or is rate limited. The
usage line shows which model was served and what it cost.

**Try it.**

```bash
export OPENROUTER_API_KEY=sk-or-...
export MODELS=deepseek/deepseek-v4-flash,openai/gpt-4.1-mini
cd step_20_openrouter
python -m harness.agent
> /models
> /route anthropic/claude-sonnet-4,deepseek/deepseek-v4-flash
```

**You should see** the route and a price list from `/models`, the served
model and a dollar cost after every call, and a cost total at exit.

**Takeaway.** The model is a string. The harness is the product.

---

# Part 4: Ten more capabilities

The harness from stage 15 can read, edit, run, plan, remember a session and
delegate. Real coding agents do more. Part 4 adds ten capabilities, one per
step, each built on the step before it, in the same shape as Part 1.

> **Build status.** All 45 steps are built and tested. Every step is
> linked from the index at the end of this document, and every "The code"
> excerpt in this document is verified against the step's source by
> `check_snippets.py` in continuous integration. The specification the
> steps were built from is in `NEXT_STEPS_SPEC.md`.

## Step 21: Streaming and headless mode

**Goal.** See the answer as it is written, and run the harness from a
script.

**The idea.** The model call streams. Text deltas print as they arrive.
Tool call deltas are assembled by index into the same message shape the
loop already stores, so nothing downstream changes. The inner loop moves
into a `turn()` function, and `harness -p "prompt"` runs one turn and prints
the answer.

**The code.** `step_21_streaming_headless/harness/llm.py`:

```python
        if delta.content:
            parts.append(delta.content)
            if on_delta:
                on_delta(delta.content)

        for piece in delta.tool_calls or []:
            call = calls.setdefault(piece.index, StreamedToolCall())
            if piece.id:
                call.id = piece.id
```

Text deltas go to the screen through `on_delta` as they arrive. Tool call
deltas are collected by `index`, because one call's arguments arrive in
many pieces. The assembled `StreamedMessage` has the same `model_dump()`
as before, so the loop stores it unchanged.

**Try it.**

```bash
cd step_21_streaming_headless
python -m harness.agent
> explain harness/llm.py
python -m harness.agent -p "how many tools are registered?"
```

**You should see** text appear word by word instead of after a pause, and
the headless call print one answer and exit.

**Takeaway.** Streaming changes how the reply is collected, not what is
stored. Headless mode is what step 30 uses to run evaluations.

## Step 22: Parallel tool calls

**Goal.** Run several tool calls from one reply at the same time.

**The idea.** Permission decisions happen first, on the main thread, one at
a time, so approval prompts never interleave. Then the allowed calls run in
a thread pool and their results are appended in the original order. The
subagent uses the same path.

**The code.** `step_22_parallel_tools/harness/tools.py`:

```python
    outcomes = []  # (args, result) per call; result is None until it has run
    for tool_call in tool_calls:
        args, action, reason = decide(tool_call)
        outcomes.append((args, settle(action, reason)))

    pending = [i for i, (_, result) in enumerate(outcomes) if result is None]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {i: pool.submit(run, tool_calls[i], outcomes[i][0]) for i in pending}
        for i, future in futures.items():
            outcomes[i] = (outcomes[i][0], future.result())
    return outcomes
```

`decide` does the JSON parse and the permission check. `settle` turns a
deny or a declined prompt into a result string, so those calls never run.
Only calls whose result is still `None` go to the pool, and the results
are written back into their original slots.

**Try it.**

```bash
cd step_22_parallel_tools
python -m harness.agent
> read llm.py, tools.py and ui.py and summarise each in one line
```

**You should see** three tool panels appear together instead of one after
another.

**Takeaway.** Order of results is part of the protocol. Concurrency may
change timing, never order.

## Step 23: Browser use

**Goal.** Let the agent read and operate web pages.

**The idea.** Playwright drives a Chromium page. Six tools open, click,
type, read, screenshot and close. The main agent never holds them. It holds
one tool, `browse(task)`, which runs a browser subagent with its own
context, so page dumps never enter the main transcript. Opening a URL asks
unless the host is on an allow list.

**The code.** `step_23_browser_use/harness/browser.py`:

```python
def browser_read() -> str:
    """The page's title, URL and visible text, capped like any tool output."""
    current = page()
    lines = (line.strip() for line in current.inner_text("body").splitlines())
    text = "
".join(line for line in lines if line)  # visible text, blank lines dropped
    return history.cap(f"Title: {current.title()}
URL: {current.url}

{text}")
```

`step_23_browser_use/harness/browse.py`:

```python
def browse(task: str) -> str:
```

```python
    return loop(SYSTEM_PROMPT, task, toolset(), MAX_TURNS, label="subagent browsing")
```

A page read goes through the same `history.cap` as any tool output. The
`browse` tool is the stage 15 subagent loop with a browser prompt and the
browser tool set. Playwright's sync API must be called from one thread, so
`browser.py` owns a worker thread and every tool call is forwarded to it.

**Try it.**

```bash
pip install playwright && playwright install chromium
cd step_23_browser_use
python -m harness.agent
> browse to https://example.com and tell me the page title and first paragraph
```

**You should see** the subagent panel, its browser tool calls indented, and
a short report.

**Takeaway.** The stage 15 subagent pattern is how any noisy capability is
added without polluting the main context.

## Step 24: Computer use

**Goal.** Let the agent see the screen and act on any application.

**The idea.** A screenshot tool captures the display and the harness turns
the file into an image message the model can see. An act tool clicks,
types, presses keys and scrolls through PyAutoGUI. Every action asks unless
you set `COMPUTER_AUTO=1`.

**The code.** `step_24_computer_use/harness/history.py`:

```python
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": caption},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{data}"}},
```

The screenshot tool returns text with an `[[image:path]]` marker. After the
tool results are appended, the loop turns each marker into a user message
with a text part and an image part, as a base64 data URL, so the file never
leaves the machine. Old screenshots are shrunk to their caption by
`strip()`, like any other tool output.

**Try it.**

```bash
pip install pyautogui
cd step_24_computer_use
python -m harness.agent
> take a screenshot and tell me which windows are open
```

**You should see** a screenshot tool call, then an image message appended
to the transcript, then a description of the screen.

**Takeaway.** Images enter the transcript as user content parts. The tool
result stays text; the harness adds the picture.

## Step 25: Persistent memory

**Goal.** Make the agent remember between sessions.

**The idea.** A memory is a markdown file with a name, a description and a
body, per project or per user. A `remember` tool writes one. The index of
names and descriptions rides in the late block on every call, exactly like
the skills index. A `recall` tool reads the body on demand. After a
compaction, the handoff note is saved as a memory, so the next session can
continue where this one stopped.

**The code.** `step_25_memory/harness/memory.py`:

```python
    directory = MEMORY_DIRS[SCOPES.index(scope)]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{slug(name)}.md"
    existed = path.exists()
    front = yaml.safe_dump({"name": name, "description": description, "type": type}, sort_keys=False, allow_unicode=True)
    path.write_text(f"---
{front}---

{content.strip()}
", encoding="utf-8")
```

`step_25_memory/harness/context.py`:

```python
def memory_note():
```

```python
    return f"
<memory>
{index}
</memory>" if index else ""
```

A memory is written with the same front matter shape as a skill, so the
same parser reads both. The index rides in the late block after the todo
list. Nothing about memory touches the stable prefix.

**Try it.**

```bash
cd step_25_memory
python -m harness.agent
> remember that this project uses pytest and the tests live in tests/
# exit, start again
python -m harness.agent
> how do I run the tests here?
```

**You should see** the answer come from memory, with a `recall` call and no
search.

**Takeaway.** Memory is skills plus late injection plus a write tool. Three
mechanisms you already built.

## Step 26: MCP client

**Goal.** Use tools from any MCP server without writing tool code.

**The idea.** A config file lists servers. At start, the harness connects
over stdio, lists each server's tools, and registers them in the same
`TOOLS` and `TOOL_SCHEMAS` tables as `mcp__server__tool`. Same registry,
same permission check, same sandbox. MCP tools ask unless allow-listed.

**The code.** `step_26_mcp_client/harness/mcp_client.py`:

```python
        def wrapper(_tool=tool.name, **args):
            return call_tool(server, _tool, args)

        registry.TOOLS[name] = wrapper
        registry.TOOL_SCHEMAS.append({
            "type": "function",
            "function": {
                "name": name,
                "description": tool.description or f"{tool.name} from the {server} MCP server",
                "parameters": tool.inputSchema or {"type": "object", "properties": {}},
            },
        })
```

Each remote tool becomes one entry in each table, exactly as stage 2.2
laid them out. The server's own JSON schema is passed through as the
`parameters`. The MCP client runs on one background thread with its own
asyncio loop, so the sync tool wrapper can call it from the stage 22 pool.

**Try it.**

```bash
pip install mcp
cd step_26_mcp_client
python -m harness.agent
> /mcp
> use the echo server to add 2 and 3
```

**You should see** the example echo server listed with its two tools, and
the model call `mcp__echo__add`.

**Takeaway.** The registry from stage 2.2 was the right abstraction. A
whole ecosystem of tools plugs into it unchanged.

## Step 27: Hooks

**Goal.** Let users customise the harness without forking it.

**The idea.** A config file maps events to shell commands or Python
functions: before and after a tool call, when a prompt is submitted, before
compaction, at session start and end. A hook can block a call, replace a
result, or add context to the late block.

**The code.** `step_27_hooks/harness/tools.py`:

```python
    args = json.loads(tool_call.function.arguments)
    action, reason = check(tool_call.function.name, args)
    if action == "deny":
        return args, action, reason
    outcome = hooks.run_hooks("PreToolUse", {"tool_name": tool_call.function.name, "tool_input": args})
    if outcome.blocked:
        return args, "blocked", outcome.reason
    return args, action, reason
```

The hook runs after the permission rules and before the tool, on the one
shared path from stage 22, so subagents and parallel calls go through it
too. A command hook gets the event as JSON on stdin and blocks by exiting
with code 2; its stderr becomes the reason the model reads.

**Try it.**

```bash
cd step_27_hooks
python -m harness.agent
> write a file named .env with API_KEY=test
```

**You should see** `Blocked by hook`, from the example hook that protects
`.env` files, and a `tool_log.txt` that grows with every call.

**Takeaway.** Hooks are the same extension points the SDKs in Part 2
expose. Now you know what is behind them.

## Step 28: Plan mode and structured output

**Goal.** Plan first, approve, then act.

**The idea.** In plan mode the model gets read-only tools and one extra:
`submit_plan`, whose argument is validated against a JSON schema. A valid
plan is drawn as a panel and you approve it. On approval the steps become
todos, the mode switches to act, and the plan rides in the late block until
every todo is done.

**The code.** `step_28_plan_mode/harness/plan.py`:

```python
def submit_plan(plan):
    """Validate the plan, show it, and ask the user. Returns the result for the model."""
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    problems = validate(plan)
    if problems:
        return "Error: the plan is invalid:
" + "
".join(f"- {p}" for p in problems)
    ui.plan(plan)
    approved, feedback = ui.approve_plan()
    if approved:
        approve(plan)
```

`submit_plan` is an ordinary tool. Its argument is validated against a
JSON schema; a bad plan comes back as an error result the model can fix.
A good plan is drawn, you approve it, and `approve()` turns its steps into
todos and switches the mode to act.

**Try it.**

```bash
cd step_28_plan_mode
python -m harness.agent
> /plan
> add a --version flag to the harness with a test
```

**You should see** the plan panel, an approval prompt, and then the todo
checklist driving the edits.

**Takeaway.** Structured output turns a free-text plan into data the
harness can act on.

## Step 29: Background jobs and parallel subagents

**Goal.** Run long commands without blocking, and send several explorers at
once.

**The idea.** A background bash tool starts a job and returns an id. Status,
wait and kill tools manage it, and running jobs are listed in the late
block. The `task` tool accepts a list of questions and runs one subagent per
question concurrently.

**The code.** `step_29_jobs_parallel_subagents/harness/subagent.py`:

```python
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL, thread_name_prefix="subagent") as pool:
        futures = [pool.submit(guarded, number, description) for number, description in enumerate(descriptions, 1)]
        reports = [future.result() for future in futures]
    return "

".join(
        f"## subagent {number}: {title(description)}

{report}"
        for number, (description, report) in enumerate(zip(descriptions, reports), 1)
    )
```

Each description gets its own `loop()` run on a worker thread, with its
own message list, and the reports come back joined under numbered headers
in the order they were asked. A background job is the same idea for shell
commands: `Popen` through the sandbox wrapper, output to a temp file, and
an id the model can poll or kill.

**Try it.**

```bash
cd step_29_jobs_parallel_subagents
python -m harness.agent
> start the test suite in the background, then send two subagents to find where sessions are saved and where compaction is triggered
```

**You should see** a job id, two subagent panels running together, and the
job status when you ask for it.

**Takeaway.** Stage 15 stopped at one subagent. The same loop, in a thread
pool, is a team.

## Step 30: Evaluation harness

**Goal.** Measure whether any of this made the agent better.

**The idea.** A suite is a directory of tasks. Each task has a prompt, an
optional starting workspace, and a checker: a script, an expected string,
or an LLM judge. `harness eval` runs each task in a fresh temp workspace
through the same `turn()` function, and reports pass rate, time, tokens and
cost.

**The code.** `step_30_eval/harness/evaluate.py`:

```python
def run_task(task, run=1, suite_name="suite", keep=False):
    """One run of one task in a fresh temp workspace. Returns a Result."""
    root = Path(tempfile.mkdtemp(prefix=f"eval-{task.name}-"))
    workspace = root / "workspace"
    if (task.path / "workspace").is_dir():
        shutil.copytree(task.path / "workspace", workspace)
    else:
        workspace.mkdir()
    session_id = f"eval-{suite_name}-{task.name}-{run}-{datetime.now():%Y%m%d-%H%M%S-%f}"
```

Every run gets a fresh copy of the task's workspace, a fresh session id
and a fresh message list, then goes through the same `turn()` as the chat.
The cost of module-level state shows here: the working directory, the
project root for permissions and the sandbox, and the todo list all have
to be reset per task, and the README of the step says exactly which.

**Try it.**

```bash
cd step_30_eval
python -m harness.agent eval evals
```

**You should see** a table with one row per task and a pass rate, and an
`eval_report.json` next to the suite.

**Takeaway.** Without a number, every change is a guess. With this step, the
harness can be improved on purpose.

---

# Part 5: Durability, context and orchestration

Part 4 gave the harness reach. Part 5 makes it dependable and explains how
it compares to production systems. These steps follow the five layers of a
production harness: the loop, tools and guardrails, the context engine,
durability, and orchestration.

## Step 31: Project instruction files

**Goal.** Let a project tell the agent how to work in it.

**The idea.** An `AGENTS.md` file at the project root, or in any directory
above the working one, holds standing instructions: the build command, the
test command, the conventions. The harness finds every such file from home
down to the working directory and puts them into the system prompt, where
they are stable and cached. A `/init` command writes the first one by
sending an explorer subagent through the repository.

**The code.** `step_31_instruction_files/harness/instructions.py`:

```python
def find_instructions(cwd=None):
    """Every instruction file, in the order it is read: home, root, ..., cwd."""
    found = []
    for directory in search_dirs(cwd):
        for name in NAMES:
            path = directory / name
            if path.is_file():
                found.append(path)
                break  # AGENTS.md and CLAUDE.md are one file under two names
    return found
```

```python
    for path in LOADED:
        parts.append(f"# Instructions from {label(path, cwd)}

{read_instructions(path).strip()}")
    return "

".join(parts)
```

The files are read from the most general to the most specific, joined
under headers, and placed in the system prompt. They change rarely, so
they belong in the cached prefix, not in the late block.

**Try it.**

```bash
cd step_31_instruction_files
python -m harness.agent
> /init
> /instructions
```

**You should see** a generated `AGENTS.md` after approval, and the list of
instruction files the harness loaded.

**Takeaway.** This is the most used harness feature in practice, and it is
sixty lines: find files, join them, put them in the prefix.

## Step 32: Context budget

**Goal.** See where the context window goes, and spend it on purpose.

**The idea.** A `/context` command draws one bar per category: system
prompt, instruction files, skills index, memory index, tool schemas,
transcript, tool results, images. Warnings fire at half and three quarters
of the window. Large tool schemas are sent as one-line stubs and loaded on
demand with a `load_tool` call, so rarely used tools cost almost nothing.

**The code.** `step_32_context_budget/harness/tools.py`:

```python
    offered = []
    stubbed = False
    for schema in TOOL_SCHEMAS if schemas is None else schemas:
        if schema["function"]["name"] in LOADED or not is_deferred(schema):
            offered.append(schema)
        else:
            offered.append(stub(schema))
            stubbed = True
    if stubbed:
        offered.append(LOAD_TOOL_SCHEMA)
    return offered
```

A deferred tool keeps its name on the wire but loses its parameters, so
the model knows it exists and knows to call `load_tool` first. Once loaded
it stays loaded for the session. The function takes an already filtered
list, so it composes with plan mode and with each subagent's tool set.

**Try it.**

```bash
cd step_32_context_budget
python -m harness.agent
> /context
```

**You should see** the breakdown, the estimate next to the real prompt
token count from the last call, and the deferred tools listed by name.

**Takeaway.** The context window is a budget. A harness that cannot show
the bill cannot manage it.

## Step 33: Workspace checkpoints and undo

**Goal.** Undo what the agent did to your files, not just to the
transcript.

**The idea.** Before every edit, the harness copies the file into a
checkpoint directory keyed by session and turn. `/undo` restores the last
turn's files and rewinds the transcript one turn. `/rewind` restores files
to the chosen point as well. The capture is a hook from step 27, not a
change to the tools.

**The code.** `step_33_checkpoints/harness/checkpoint.py`:

```python
    with LOCK:
        restored = [restore(entry, turn, session_id) for entry in reversed(manifest(turn, session_id))]
        start = start_of(turn, session_id)
        shutil.rmtree(turn_dir(turn, session_id), ignore_errors=True)
    return turn, start, restored
```

`step_33_checkpoints/harness/hooks.py`:

```python
BUILTIN = {  # the harness's own hooks; same shape as a config entry, run first
```

The capture is a built-in `PreToolUse` hook that runs before any
configured hook, so the harness uses its own extension point. Undo
replays the turn's manifest in reverse, deletes files that did not exist
before, and returns the transcript length at the start of the turn so the
session can be rewound to match.

**Try it.**

```bash
cd step_33_checkpoints
python -m harness.agent
> add a docstring to harness/config.py
> /undo
```

**You should see** the edit land, then the file back to its previous
content and the transcript one turn shorter.

**Takeaway.** Stage 8 made the transcript durable. This step makes the
workspace match it.

## Step 34: Durability and recovery

**Goal.** Survive rate limits, network failures, crashes and loops.

**The idea.** Model calls retry with backoff on retryable errors. A turn has
a call limit. A loop detector replaces the third identical tool call in a
row with a message asking for a different approach. On `--resume`, a
session that died with unanswered tool calls is completed before the next
prompt.

**The code.** `step_34_durability/harness/llm.py`:

```python
    for attempt in range(1, MAX_TRIES + 1):
        try:
            return stream_once(request, on_delta)
        except openai.APIError as error:
            if not retryable(error):
                reason = f"model call failed and will not be retried ({describe(error)}): {error}"
                break
            if attempt == MAX_TRIES:
                reason = f"model call failed {MAX_TRIES} times, giving up ({describe(error)}): {error}"
                break
            wait = BACKOFF[attempt - 1]
            ui.note(f"model call failed ({describe(error)}); retry {attempt} of {MAX_TRIES - 1} in {wait:g}s")
```

The whole stream sits inside the retry, so a connection that drops halfway
through a reply starts that reply over. A 4xx error is never retried. When
every try fails, the result is a message with a `failed` reason that the
loop shows, and the session continues.

`step_34_durability/harness/agent.py`:

```python
def recover(messages):
```

```python
    pending = durability.unanswered(messages)
    if not pending:
        return 0
```

On resume, tool calls that never received a result are run through the
same permissions and hooks, and their results are appended before the
next prompt, because the API refuses a transcript that ends in an
unanswered call.

**Try it.**

```bash
cd step_34_durability
python -m harness.agent
# kill the process during a tool call, then
python -m harness.agent --resume
```

**You should see** "recovered N pending tool calls" and the chat continue
from where it stopped.

**Takeaway.** Every failure mode becomes a message, a retry, or a recovery.
None of them ends the session.

## Step 35: Human in the loop

**Goal.** Let the agent ask, and let you steer.

**The idea.** An `ask_user` tool with numbered options, so the agent asks
instead of guessing at an ambiguous requirement. Ctrl-C during a turn
pauses the loop and takes a new message from you, appended after the
pending tool results. The approval prompt accepts yes, no, always for this
session, and never.

**The code.** `step_35_human_in_the_loop/harness/ask_user.py`:

```python
    options = list(options or [])
    ui.question(question, options)
    try:
        answer = prompt.read("  answer> ").strip()
    except (EOFError, KeyboardInterrupt):
        return NO_ANSWER
    if answer.isdigit() and 1 <= int(answer) <= len(options):
        return options[int(answer) - 1]
```

`step_35_human_in_the_loop/harness/permissions.py`:

```python
def remember(name, args, verdict):
    """Store an always (allow) or never (deny) answer for the rest of the session. Returns what was stored."""
    stored = []
    for key in session_keys(name, args):
        SESSION_RULES[key] = verdict
        stored.append(" ".join(part for part in key if part))
    return f"{verdict} for this session: " + ", ".join(stored)
```

`ask_user` is an ordinary tool whose result is whatever you typed, so the
answer enters the transcript like any other tool result. Session rules
sit in front of the stage 11 table, keyed by tool and the first word of
the command, and a `deny` in the table still wins over an `always`.

**Try it.**

```bash
cd step_35_human_in_the_loop
python -m harness.agent
> refactor the config module        # press ctrl-c while it works, type a correction
```

**You should see** the steering message land between tool calls and the
agent change course.

**Takeaway.** Approval is one channel. Questions and steering are two more,
and both are cheap.

## Step 36: Orchestration patterns

**Goal.** Define subagents in files, and compose them into a pipeline.

**The idea.** A subagent definition is a markdown file with a name, a
description, a tool list and a prompt, discovered like skills. Each one
becomes a tool. A `/pipeline` command runs a planner, then a worker per
step, then a reviewer per step, retrying a failed step once with the
reviewer's notes.

**The code.** `step_36_orchestration/harness/agents.py`:

```python
def make_tool(name):
    """The callable behind agent_<name>: one request in, one report out."""

    def agent_tool(request: str) -> str:
        return run(name, request)

    agent_tool.__name__ = tool_name(name)
    agent_tool.__doc__ = f"Run the {name} agent on one request and return its report."
    return agent_tool
```

A definition file has the same front matter shape as a skill, plus a tool
list and a turn cap, and its body is the system prompt. Each one becomes
a tool named `agent_<name>` that runs the stage 15 loop with that prompt
and that tool list. The shipped `planner`, `worker` and `reviewer` are
the three roles a pipeline needs.

**Try it.**

```bash
cd step_36_orchestration
python -m harness.agent
> /pipeline add input validation to the todo API
```

**You should see** the plan, one worker run per step, a review verdict per
step, and a summary table.

**Takeaway.** Stage 15 built one subagent. This step builds the vocabulary
for many.

## Step 37: Production harness anatomy

**Goal.** Map everything in this repo to real systems.

**The idea.** No new code. A reading that places each mechanism next to
Claude Code, Codex CLI, OpenCode, pi and Hermes: what each calls it, where
it lives, and how it differs, with links to their public sources. It ends
with what they all agree on and where they disagree.

**What it found.** All five harnesses run the same loop, keep one JSON
transcript per session on disk, walk the directory tree for `AGENTS.md` or
`CLAUDE.md`, and ship a headless mode. They disagree on sandboxing (two of
five have no OS sandbox), on memory (only two ship it), on undo (one has
removed it), and on evaluation (only one ships a scored eval runner). The
step's README has the tables, 49 rows with a source link on every row.

**Takeaway.** After this step, reading any production harness is reading
something you have already built.

## Step 38: Capstone

**Goal.** Build a real application with the harness, and grade it.

**The idea.** A brief asks for a small FastAPI todo service with a database,
tests and a README. `capstone/run.py` runs the harness headless on the
brief in a fresh workspace, then runs a step 30 evaluation suite with five
checks, and writes a scorecard. The README records one full run: tool
calls, tokens, cost, what went wrong, and how the harness recovered.

**The code.** Headless, nobody answers a question. The runner watches how
each turn ended and decides whether to send a follow-up, at most twice.

`step_38_capstone/capstone/run.py`:

```python
def why_continue(messages):
    ...
    last = messages[-1]
    if last["role"] == "tool":
        return "the turn stopped at MAX_CALLS"
    if last["role"] == "user":
        return "the model call failed"
    if last["role"] == "assistant" and (last.get("content") or "").rstrip().endswith("?"):
        return "the answer ended with a question"
    return None
```

The fifth check proves the agent stayed inside its workspace. The runner
hashes every file next to the workspace before and after the run, and the
check compares the two manifests. Without a manifest the check fails: a
check that cannot compare must not pass by default.

```python
def manifest(root, skip):
    """Relative path -> sha256 of every file under root, except those under skip."""
    root, skip = Path(root), Path(skip)
    found = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path != skip and skip not in path.parents:
            found[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found
```

**Try it.**

```bash
cd step_38_capstone
python capstone/run.py
```

**You should see** the build happen, the checks run, and a scorecard with
the pass rate and the cost.

**The recorded run.** The step ships the scorecard, report and transcript
of a real run with `gpt-4.1-mini`. It scored 4 of 5: the server started,
the tests passed, the README had a run section, and nothing outside the
workspace changed. The CRUD check failed because DELETE returned a body.
The three runs before it are written up too, because two of them changed
the harness. The first made zero model calls: the OpenAI API rejects a
function schema with `anyOf` at the top level, which OpenRouter and
DeepSeek had accepted for twenty steps. The second ended with the model
asking "Would you like me to create it now?" to nobody, which is why
`why_continue` treats a trailing question mark as a reason to continue.
The third crashed inside a subagent and still produced a report.

**Takeaway.** This is the whole codelab in one run: a model, a loop, tools,
guardrails, context, durability and a number at the end.

---

# Part 6: The production surface

Six more mechanisms that production harnesses expose, and a port of the
core to a second language.

## Step 39: Approval modes

**Goal.** Switch the whole permission policy with one command.

**The idea.** Named modes: `default` uses the stage 11 rules, `accept-edits`
never asks for edits inside the project, `read-only` denies every write,
`auto` never asks but keeps the deny rules and the sandbox, and `plan`
comes from step 28. `/mode` switches at runtime and `--mode` at start.

**The code.** A mode is a table. It maps the category of a call and the
verdict the rules gave to a final verdict. Only allow and ask appear as
keys, so a deny from the rules, from a session "never", or from the
sandbox is final in every mode, including `auto`.

`step_39_approval_modes/harness/modes.py`:

```python
TABLE = {
    "default": {},
    "accept-edits": {
        "edit-inside": {"ask": "allow"},
    },
    "read-only": {
        "edit-inside": {"allow": "deny", "ask": "deny"},
        "edit-outside": {"allow": "deny", "ask": "deny"},
        "bash": {"ask": "deny"},
        "other": {"ask": "deny"},
    },
    "auto": {
        "edit-inside": {"ask": "allow"},
        "edit-outside": {"ask": "allow"},
        "bash": {"ask": "allow"},
        "other": {"ask": "allow"},
    },
    "plan": {},
}
```

The stage 11 check did not change. Its body became `rules`, and the new
`check` wraps it: read the mode, keep the step 28 plan fence, rate the
call with the rules, then let the table have the last word. When the mode
changed the verdict, the reason names the mode, so the model reads
"read-only mode: write_file a.txt" and knows why nothing was written.

`step_39_approval_modes/harness/permissions.py`:

```python
def check(name, args):
    ...
    mode = modes.current()
    if mode == "plan" and not plan.offered(name):
        return "deny", f"plan mode: {name} is not available until the plan is approved"
    action, reason = rules(name, args)
    final = modes.apply(mode, modes.category(name, args, inside_project), action)
    if final != action:
        reason = f"{mode} mode: {reason or describe(name, args)}"
    return final, reason
```

**Try it.**

```bash
cd step_39_approval_modes
python -m harness.agent --mode read-only
> create a file called notes.txt
> /mode
> /mode auto
```

**You should see** the write denied with a reason that names the mode,
the mode list with the current one starred, and after the switch the same
request run without a prompt.

**Takeaway.** The rules are the same. The mode chooses how much to
interrupt you.

## Step 40: Handoffs

**Goal.** Transfer the conversation to a different agent.

**The idea.** A subagent starts empty and returns a report. A handoff is
the opposite: the transcript stays, the prompt and tools change, and the
new agent answers the user from then on. Definitions declare who they may
hand off to. A router agent shows the pattern.

**The code.** A definition gains one key, `handoffs`, next to its tool
list. The router may pass the conversation to the coder or the reviewer.
The coder and reviewer may pass it to each other, so a change can go
around the loop: written, judged, fixed, judged again.

`step_40_handoffs/.agents/agents/router.md`:

```text
---
name: router
description: Reads the request, decides which specialist should handle it, and hands the conversation off to that specialist.
tools: [bash, read_file, read_skill, task]
handoffs: [coder, reviewer]
max_turns: 6
---
You are the router. You decide who should handle the request, then you hand off.
```

The `handoff_to` tool does not switch anything. It checks the target
against the active agent's list, records it as pending, and returns a
result. The switch happens after every tool result of the reply is in,
so the transcript is never cut between a call and its result.

`step_40_handoffs/harness/handoff.py`:

```python
def handoff_to(agent: str, reason: str) -> str:
    """Ask for a handoff. The switch happens after this reply's results are in."""
    global PENDING, LAST_REASON
    if agent == active_name():
        return f"Error: {agent} is already the active agent."
    allowed = targets()
    if agent not in allowed:
        if definition(agent) is None and agent != MAIN:
            return f"Error: no agent named '{agent}'. You may hand off to: {', '.join(allowed) or 'nobody'}."
        return f"Error: {active_name()} may not hand off to '{agent}'. You may hand off to: {', '.join(allowed) or 'nobody'}."
    PENDING = agent
    LAST_REASON = reason
    return f"Handing off to {agent}: {reason}. The {agent} agent answers from the next reply on; do not answer the user yourself."
```

The switch itself rewrites the first message. The system prompt becomes
the new agent's prompt, the compaction summary from stage 14 is carried
over, and the tool set for the next call comes from the new definition.
The session log gets one marker line, so `--resume` brings back the agent
that was answering when the session ended.

```python
def apply(name, messages):
...
    global ACTIVE
    from . import compact  # here, not at the top: compact imports llm

    ACTIVE = None if name == MAIN else definition(name)
    if name != MAIN and ACTIVE is None:
        raise KeyError(name)
    if messages and messages[0].get("role") == "system":
        summary = compact.previous_summary(messages[0]["content"])
        prompt = system_prompt(ACTIVE)
        messages[0]["content"] = prompt + ("\n\n" + summary if summary else "")
    return ACTIVE
```

**Try it.**

```bash
cd step_40_handoffs
python -m harness.agent
> /handoff router
> add a --verbose flag to the CLI and make sure it is tested
> /agent
```

**You should see** a "handoff -> coder" line when the router decides, the
coder's edits, a second handoff to the reviewer, and `/agent` naming who
is answering now.

**Takeaway.** Subagents isolate work. Handoffs route it.

## Step 41: Stop conditions

**Goal.** Make stopping explicit and checkable.

**The idea.** A `finish` tool ends a turn on purpose. Budgets for calls,
cost and time end it by force. A stop hook can veto a stop, for example
when tests were not run, and send the agent back with the reason.

**The code.** Three budgets, checked before every model call. The call
that would cross a line is the one that is not made. A budget trip does
not ask the hooks: a budget is the harness's decision, and a hook that
sent the agent back would spend past the cap.

`step_41_stop_conditions/harness/stop.py`:

```python
def tripped(calls):
    """The report for the budget this turn has crossed, or None when it may go on.

    calls is how many model calls the turn has made. The three checks run
    before every model call, so the call that would cross a line is the
    one that is not made.
    """
    if calls >= MAX_TURN_CALLS:
        return f"stopped after {calls} model calls in one turn (MAX_TURN_CALLS={MAX_TURN_CALLS}); say continue to go on"
    if SPENT >= MAX_SESSION_COST:
        return (
            f"stopped: this session has cost ${SPENT:.4f}, over MAX_SESSION_COST=${MAX_SESSION_COST:.2f}; "
            "raise it in the environment and start again"
        )
    seconds = elapsed()
    if seconds >= MAX_TURN_SECONDS:
        return f"stopped after {seconds:.0f}s in one turn (MAX_TURN_SECONDS={MAX_TURN_SECONDS:.0f}); say continue to go on"
    return None
```

The loop gained two questions. A reply without tool calls used to end
the turn. Now the Stop hooks see it first, and a block becomes a user
message the agent reads on its next call. A reply that called `finish`
goes through the same gate, so a model cannot get past a Stop hook by
calling `finish` instead of answering.

`step_41_stop_conditions/harness/agent.py`:

```python
        if not message.tool_calls:
            reason = stop.may_stop(messages, start, message.content or "")  # the Stop hooks have the last word
            if reason:
                stop.send_back(messages, reason)
                continue  # the block is a user message now; the agent reads it on the next call
            break
```

The example Stop hook is a script. It reads the turn's tool calls from
stdin, finds the newest edit to a Python file, and looks for a pytest
run after it. No pytest, exit 2, and the agent goes back to work.

`step_41_stop_conditions/.agents/require_tests.py`:

```python
if last_edit is not None:
    index, path = last_edit
    tested = any(
        call.get("tool_name") == "bash" and "pytest" in str((call.get("tool_input") or {}).get("command") or "")
        for call in calls[index + 1:]
    )
    if not tested:
        print(f"tests were not run after editing {path}; run pytest, then answer", file=sys.stderr)
        sys.exit(2)
```

**Try it.**

```bash
cd step_41_stop_conditions
python -m harness.agent
> add a subtract function to calc.py
> /cost
```

**You should see** the agent write the function and try to answer, a
muted "Stop blocked: tests were not run after editing calc.py" line, a
pytest run, then the answer. Every usage line carries the cost of the
call, and `/cost` shows the session total against its cap.

**Takeaway.** When the loop stops is a design decision, not an accident.

## Step 42: Streaming tool output

**Goal.** Watch long commands as they run.

**The idea.** Shell output streams to the screen line by line while the
command runs. The model still receives the capped final result. Background
jobs and subagents use the same reader.

**The code.** The calling thread does not read. It waits, with the
timeout. A reader thread does the reading, one line at a time, and each
line goes two ways: raw into a list, stripped into the screen callback.
This split is why the timeout still works: a `readline` blocks for as
long as the process is silent, and a thread stuck on it cannot count
seconds. `process.wait` can.

`step_42_streaming_tool_output/harness/streaming.py`:

```python
def run(command, timeout=None, on_line=None):
    ...
    timeout = TIMEOUT if timeout is None else timeout
    process = popen(command)
    reader = Reader(process, on_line)
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill(process)
        reader.join()
        raise
    except BaseException:
        kill(process)
        raise
    reader.join()
    return reader.text()
```

The bash tool changed by three lines. It opens a panel, passes the panel
as the line callback, and caps the joined output exactly as stage 14 did.
The model reads the same text it read in step 41. Only you see it early.

`step_42_streaming_tool_output/harness/tools.py`:

```python
    with ui.streaming("bash", {"command": command}) as show:
        try:
            output = streaming.run(command, on_line=show)
        except subprocess.TimeoutExpired as expired:
            # A slow command is the model's problem to work around, not a reason
            # to take the session down. Hand the failure back as a result.
            return f"Timed out after {expired.timeout}s and was killed. Narrow it down."
    return history.cap(output or "(no output)")
```

**Try it.**

```bash
cd step_42_streaming_tool_output
python -m harness.agent
> run the test suite with pytest -v and tell me which test is slowest
```

**You should see** a panel titled "running" that shows the last eight
lines of pytest as they arrive, then the panel comes down and the reply
is built from the capped result.

**Takeaway.** What you see and what the model sees are different streams
with different budgets.

## Step 43: Extensions

**Goal.** One plugin mechanism for everything.

**The idea.** An extension is a Python file with an `apply(ctx)` function
that registers tools, commands, hooks, prompt sections or subagent
definitions. Skills, hooks, agents and MCP become extensions of the same
kind. `/extensions` lists what is loaded.

**The code.** An extension is the smallest possible thing: a file with
one function. The shipped git example registers one tool and one
command. No schema is written. The signature and the docstring become
the schema.

`step_43_extensions/.agents/extensions/git_tools.py`:

```python
def git_diff_summary(staged: bool = False) -> str:
    """Summarise the uncommitted changes: one line per changed file with the lines added and removed."""
    output = git("diff", "--stat", *(["--cached"] if staged else []))
    return output or "no changes"
```

```python
def apply(ctx):
    ctx.tool(git_diff_summary)  # the schema is built from the signature and the docstring
    ctx.command("/status", "show the git branch and the changed files", status)
```

The loader runs one file's `apply`. Three things can go wrong: the file
does not import, it has no `apply`, or `apply` raises. All three end the
same way: what the file registered before it failed is removed, the row
stays so `/extensions` can show the failure, and the loader moves on.

`step_43_extensions/harness/extensions.py`:

```python
def apply_module(name, module, path=None):
    """Run one module's apply(ctx) as the extension `name`. Returns the Extension, loaded or failed."""
    if name in EXTENSIONS:
        unload(name)  # a reload replaces what the old copy registered
    extension = EXTENSIONS[name] = Extension(name, path)
    apply = getattr(module, "apply", None)
    if not callable(apply):
        return _failed(extension, "no apply(ctx) function")
    try:
        apply(Context(extension))
    except Exception as failed:  # noqa: BLE001 - one broken extension must not stop the harness
        return _failed(extension, f"{type(failed).__name__}: {failed}")
    return extension
```

The refactor is the point of the step. Skills, hooks, agent definitions
and MCP servers stop being special. Each loader becomes an `apply`
function that registers through the same context. Skills are the
smallest: one tool, one prompt section.

`step_43_extensions/harness/skills.py`:

```python
def apply(ctx):
    """The skills extension: the read_skill tool, and the skill index in the system prompt."""
    ctx.tool(read_skill, READ_SKILL_SCHEMA)
    ctx.prompt_section(skills_section)  # a function: rendered when the prompt is built
```

**Try it.**

```bash
cd step_43_extensions
python -m harness.agent
> /extensions
> /status
> what changed in this repo since the last commit?
```

**You should see** the four built-in loaders and the two shipped
extensions listed with what each registered, the git status from the
extension's command, and the model calling `git_diff_summary`, a tool it
learned about from a file.

**Takeaway.** Small core, everything else pluggable. This is the design
that pi and DeepSeek Harness share.

## Step 44: Replay and trace viewer

**Goal.** Debug a session after the fact.

**The idea.** `harness replay` redraws a session log turn by turn with the
recorded timing. `harness trace` writes a standalone HTML page with one row
per model call, tokens, cost, duration and collapsible tool calls.

**The code.** The session log from stage 8 gains two things: a time
stamp on every line, and one extra line per model call with its usage,
seconds and cost. The stamp goes on the line, not on the message in
memory, and the usage line is keyed by the index of the assistant
message it belongs to. The list sent to the model does not change.

`step_44_replay_trace/harness/session.py`:

```python
def stamped(entry):
    """The entry with `ts` added, as one JSON line. The dict passed in is not touched."""
    return json.dumps({**entry, "ts": round(clock(), 3)}) + NL
```

```python
        for message in messages[WRITTEN:]:
            f.write(stamped(message))
        if usage is not None:
            f.write(stamped({"usage": usage, "index": len(messages) - 1, "seconds": seconds, "cost": cost}))
```

Loading drops both. Two lines in `load`, before the rewind and
compaction markers are applied, and a resumed session sends the model
exactly the list it sent before this step. The tests assert that
equality.

```python
        entry.pop("ts", None)
        if "usage" in entry:
            continue  # the numbers of a model call: replay and trace read them, the model does not
```

Replay is the log read back with its gaps. The delay between two events
is the recorded gap, divided by the speed and capped, so a session that
waited a minute on a slow model does not make you wait a minute.

`step_44_replay_trace/harness/replay.py`:

```python
def delay(previous, event, speed):
    """Seconds to wait before `event`: the recorded gap, scaled and capped. 0 without stamps."""
    if previous is None or event.ts is None or previous.ts is None or speed <= 0:
        return 0.0
    return min(max(event.ts - previous.ts, 0.0) / speed, MAX_PAUSE)
```

The trace page is one file with no fetches. Every string from the log
passes through one escape function, so a reply that contains a script
tag shows the text and runs nothing. An image is inlined only when it
is a base64 PNG or JPEG data URL.

**Try it.**

```bash
cd step_44_replay_trace
python -m harness.agent
> list the python files here and count their lines
> /exit
python -m harness.agent replay last --speed 4
python -m harness.agent trace last --html trace.html
```

**You should see** the session redrawn at four times speed with the
tool panels in their original order, then a `trace.html` you can open in
a browser: one row per model call with tokens, seconds and dollars, each
tool call a collapsed section, and a totals row at the bottom.

**Takeaway.** Evaluations tell you a task failed. Traces tell you where.

## Step 45: The core loop in TypeScript

**Goal.** Prove the design is not tied to Python.

**The idea.** The stage 15 harness as one Node package with the same file
names, the same environment variables and the same session file format, so
a session written by one language resumes in the other. The README shows
the three places the languages differ in practice.

**The code.** The loop is the same loop. Read it next to the inner
`while True` of stage 15: the late injection is built and shown, `fit`
runs, the spinner starts, the model answers, the reply is appended and
saved, each tool call runs and its result is appended and saved. Every
`await` marks a place where the Python loop blocks.

`step_45_typescript_core/harness-ts/agent.ts`:

```ts
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
```

The three differences are all about waiting. Python's `bash` tool calls
`subprocess.run`, which blocks and hands back the whole output. Node has
no blocking call that also captures output. `spawn` returns at once with
two streams, the output arrives in `data` events, and the timeout is a
timer that kills the process. Step 42 added a reader thread to Python so
lines could reach the screen as they arrived. The TypeScript side has
that for free: the `data` handler is already called per chunk.

`step_45_typescript_core/harness/sandbox.py`:

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

`step_45_typescript_core/harness-ts/sandbox.ts`:

```ts
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
```

The second difference is threads versus promises: step 22 needs a
thread pool to run tool calls in parallel, and Node needs
`Promise.all`. The third is sandbox spawning: `spawn(argv)` for the
wrapped command and `spawn(command, {shell: true})` without a sandbox,
with `taskkill /T` on Windows to reach the process tree.

**Try it.**

```bash
cd step_45_typescript_core/harness-ts
npm test                     # 25 tests, no install needed
npm install && npm start     # a real session, same env vars as Python
> list the files in this directory and count them
> /exit
cd .. && python -m harness.agent --resume
```

**You should see** the TypeScript harness answer with the same panels in
plain text, then the Python harness open the session the TypeScript one
just wrote and carry on from it. The step's tests run that round trip in
both directions.

**Takeaway.** The harness is a set of ideas. The language is a detail.

---

# Part 7: The same harness on TrueForge

Parts 1 to 6 built a harness that runs on your machine, in your terminal,
with your files. TrueForge ([github.com/truefoundry/trueforge](https://github.com/truefoundry/trueforge),
MIT) is an open-source harness that runs as a **server**: the loop,
sessions, tools, sandbox, skills, subagents, compaction and approvals live
in the server, and clients talk to it over HTTP and Server-Sent Events. It
presents itself as the open-source alternative to hosted managed-agent
services. Part 7 maps every capability of this codelab onto it, one step
per group, with the Python SDK. Every step README opens with a recorded
quick demo against a local server.

> **Setup.** `npx @truefoundry/trueforge` starts a local server on port
> 8790 with SQLite and no login. It needs Linux or macOS for the local
> sandbox (`bwrap`, `socat`, `rg` on PATH). On Windows run it inside WSL
> with mirrored networking; step 46 has the exact commands. Then
> `pip install trueforge_sdk` and register a model provider with the
> step 46 script. No key goes into any agent definition.

## Step 46: The loop on TrueForge

**Goal.** Run one turn: open a session, stream events, read the usage.

**The idea.** An agent is a definition, a session is a conversation, a turn
is one request, and events stream back: `turn.created`, `model.message`,
`model.message.delta`, `tool.response`, `turn.done`. The client never runs
the loop. Passing the session id back is stage 8's `--resume`.

**The code.** There is no `messages` list and no `while True` on the
client. One function opens a session when it has none, streams one turn,
prints each delta on the main thread, and reads the text and the token
totals out of the terminal event.

`step_46_trueforge_loop/client/loop.py`:

```python
def chat(prompt, session_id=None, on_delta=print_delta):
    """Run one turn. Return (session_id, text, metrics).

    A new session is opened when `session_id` is None. Passing an id back
    continues that conversation: the server chains the new turn onto the last
    one (`previous_turn_id` defaults to "auto"), so no history is resent.
    """
    if session_id is None:
        session_id = open_session()
    stream = client().sessions.create_turn_stream(session_id=session_id, input=[UserMessage(content=prompt)])
    pieces = []
    text = None
    metrics = {}
    for event in stream.with_metadata():
        data = event.data
        if data.type == "model.message.delta" and data.thread_id == "main" and data.content:
            pieces.append(data.content)
            if on_delta:
                on_delta(data.content)
        elif data.type == "turn.done":
            text, metrics = finish(data.state)
    if text is None:
        text = "".join(pieces)
    return session_id, text, metrics
```

A plain turn streams exactly five events. `turn.created` is the user
message being appended. `model.message` is the call beginning. The deltas
are the chunks of content, the last one carrying the usage. `turn.done` is
the `break` when a reply has no tool calls. A turn that calls tools
streams more, and step 47 builds those tools.

**Try it.**

```bash
cd step_46_trueforge_loop
pip install trueforge_sdk truststore
python setup_server.py
python demo.py -p "Remember this: the project codename is HERON. Reply in one short sentence."
python demo.py --resume <session id> -p "What is the project codename?"
```

**You should see** the reply stream, a usage line with the session id, and
the second command answer from the first one's memory. No history was
resent: the transcript lives on the server.

**Takeaway.** The five events of one turn are the stage 2.4 loop, seen
from outside.

## Step 47: Tools and permissions as MCP

**Goal.** Give the server your tools, and gate them the way stage 11 did.

**The idea.** TrueForge has no built-in coding tools. Tools arrive as MCP
servers. The codelab's `read_file`, `write_file`, `str_replace` and `bash`
become a remote MCP server with annotations, and the server's default
approval policy pauses on write and destructive tools. The client answers
`tool.approval_required` with `user.tool_approval`.

**The code.** Stage 11's permission table becomes two annotation sets.
The readers say they are read-only. The writers say they are destructive.
TrueForge's default policy, ask before `@write` and `@destructive`, then
gates exactly what stage 11 gated.

`step_47_trueforge_tools_mcp/tools_server.py`:

```python
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=False)
```

```python
TOOLS = [
    (read_file, READ_ONLY),
    (list_dir, READ_ONLY),
    (write_file, DESTRUCTIVE),
    (str_replace, DESTRUCTIVE),
    (bash, DESTRUCTIVE),
]
```

An approval is a turn boundary. The gated call ends the turn with a
pending event that names the call id and the message it came from. The
client looks the call up, asks on the terminal, and starts a new turn
whose input is one decision per call. A turn's input cannot mix a user
message with approvals, so the resume carries no text.

`step_47_trueforge_tools_mcp/client/approve.py`:

```python
    inputs = [UserMessage(content=prompt)]
    while True:
        result = run_turn(client, session_id, inputs, events, out)
        for key, value in (result.metrics or {}).items():
            totals[key] = totals.get(key, 0) + value
        if not result.pending:
            result.metrics = totals or None
            return result
        inputs = approvals_for(result.pending, events, approver)
```

**Try it.**

```bash
cd step_47_trueforge_tools_mcp
python demo.py "add a docstring to hello.py"
```

**You should see** the five tools listed with their annotations and the
policy verdict for each, the readers run without a prompt, an `allow?`
prompt for `str_replace` with its arguments, and the edited file printed
at the end. Answer `n` and the model reads a denial as its tool result.
There is no `deny` tier in MCP annotations. Stage 11's `rm *` rule has no
equivalent here; the sandbox of step 48 is the answer to that.

**Takeaway.** Permissions moved from a rules table to tool annotations,
and the ask moved from a terminal prompt to an event.

## Step 48: Sandbox, skills and code mode

**Goal.** Run code in a sandbox the server provisions, and load skills
from git.

**The idea.** Stage 12 wrapped `bash` in an OS sandbox around the agent.
TrueForge uses a sandbox as a tool: created on demand, files kept across
turns, credentials never inside it. Skills are `SKILL.md` directories in a
git repository, loaded when the model picks them.

**Takeaway.** Same mechanisms, different host: the sandbox and the skills
belong to the server, not to your machine.

## Step 49: Context, questions and stop conditions

**Goal.** Configure compaction, large-result offloading, questions to the
user, and the iteration limit.

**The idea.** Stage 14's compaction is a trigger in the agent spec. Step
32's spill file is `large_tool_response`. Step 35's `ask_user` is
`ask_user_questions`, answered through `tool.response_required`. Step 41's
call budget is `iteration_limit`. Every `model.message` carries a token
breakdown, which is step 32's `/context` view.

**The code.** Four stages of this codelab are nine lines of one spec.

`step_49_trueforge_context/client/context.py`:

```python
    return AgentSpec(
        model=Model(name=model),
        instructions=instructions,
        config=RuntimeConfig(
            context_management=ContextManagementConfig(
                compaction=CompactionConfig(
                    enabled=True,
                    trigger=InputTokensCompactionTrigger(type="input_tokens", value=compact_at),
                ),
                large_tool_response=LargeToolResponseConfig(enabled=True),
            ),
            iteration_limit=iteration_limit,
            ask_user_questions=AskUserQuestionsConfig(enabled=True),
        ),
    )
```

The client keeps the two jobs the server cannot do: answer a question and
show the bill. Step 35 answered inside the tool call. Here the server has
no terminal, so it ends the turn with a pending question and the client
starts a new turn whose input is only the answers.

`step_49_trueforge_context/client/questions.py`:

```python
    turns = [context.stream_turn(client, session_id, [UserMessage(content=prompt)], on_delta)]
    while turns[-1].pending:
        replies = answers(turns[-1], read)
        if not replies:
            break  # pending calls that are not questions; nothing this client can answer
        turns.append(context.stream_turn(client, session_id, replies, on_delta))
    return turns
```

**Try it.**

```bash
cd step_49_trueforge_context
python demo.py "set up a project for me"
```

**You should see** the spec summary, the agent's question with numbered
options, your answer, the reply, and a token table per model call with
the harness, skills, instructions, tool definitions and messages columns.
Two things the recorded run found: a crossed iteration limit ends the
turn with status `error` and a message asking you to request again, and
the breakdown is a server-side estimate, so read its columns as
proportions and the `input` column as the bill.

**Takeaway.** Context engineering became configuration.

## Step 50: Subagents, sessions and evaluation

**Goal.** Watch subagent threads, replay a session from its events, and
run the step 30 evaluation suite through the server.

**The idea.** Subagents are threads inside a turn, announced by
`thread.created` and `thread.done`. A session's events are the step 44
trace, already stored. The step 30 evaluation format runs unchanged with
the step 47 tools server pointed at a temp workspace.

**Takeaway.** The evaluation harness does not care where the loop runs.

## Step 51: TrueForge versus this codelab versus managed agents

**Goal.** One table per capability, three columns.

**The idea.** What you gain when the harness is a server, what you lose,
and what a hosted managed-agent service does differently, with the cost
numbers from the recorded runs.

**Takeaway.** The design is the same in all three. The trade is where it
runs and who holds the credentials.

---

# Wrap-up

## Three rules that hold the design together

1. **Every tool call goes through one place.** From stage 2.2 the model's
   function name is a dictionary key. From stage 15 that lookup lives in
   `execute()`, shared by the main loop and the subagent. Permissions, the
   sandbox and the subagent all hook in there.
2. **Never change the beginning of the prompt.** The transcript is re-sent
   on every call and the provider caches the unchanged prefix. Volatile
   facts are appended at send time and thrown away. Old tool output is
   shrunk only after its turn ends. Compaction rebuilds the prefix once and
   then leaves it alone.
3. **Errors are results.** A refused edit, a blocked command, a declined
   prompt, a timeout, a failed compaction: each comes back as text the model
   can read and recover from. Nothing the model does can end the session.

## Stage index

| Stage | Adds | Files that change |
|------:|------|-------------------|
| [1](step_01_minimal_chat/) | minimal chat | `llm.py` |
| [2.1](step_02_1_bash_tool/) | a bash tool | `llm.py` |
| [2.2](step_02_2_generic_tools/) | tool registry | `tools.py`, `llm.py` |
| [2.3](step_02_3_read_file/) | `read_file` | `tools.py` |
| [2.4](step_02_4_agent_loop/) | **the agent loop** | `agent.py`, `llm.py` |
| [3](step_03_better_ui/) | terminal UI, chat loop | `ui.py`, `agent.py` |
| [4](step_04_skills/) | skills | `skills.py`, `tools.py`, `llm.py` |
| [5](step_05_file_editing/) | `write_file`, `str_replace` | `tools.py`, `llm.py` |
| [6](step_06_late_injection/) | late injection | `context.py`, `agent.py` |
| [7](step_07_file_freshness/) | file freshness | `context.py`, `tools.py` |
| [8](step_08_sessions_rewind/) | sessions, `/rewind` | `session.py`, `commands.py`, `agent.py`, `ui.py` |
| [9](step_09_installable_command/) | package, `harness` command | `harness/`, `pyproject.toml` |
| [10](step_10_todos/) | todos | `todos.py`, `context.py`, `llm.py` |
| [11](step_11_permissions/) | allow / ask / deny | `permissions.py`, `agent.py`, `ui.py` |
| [12](step_12_sandbox/) | OS sandbox, timeouts | `sandbox.py`, `tools.py` |
| [13](step_13_readable_todos_input_line/) | checklist, input line | `prompt.py`, `ui.py` |
| [14](step_14_compaction/) | cap / strip / fit, compaction | `history.py`, `compact.py`, `agent.py` |
| [15](step_15_subagents/) | subagents | `subagent.py`, `tools.py` |
| [16](step_16_claude_agent_sdk/) | Claude Agent SDK | `harness.py`, `rules.py` |
| [17](step_17_openai_agents_sdk/) | OpenAI Agents SDK | `harness.py`, `rules.py` |
| [18](step_18_google_antigravity_sdk/) | Google Antigravity SDK | `harness.py`, `rules.py` |
| [19](step_19_deepseek_harness/) | DeepSeek Harness | `harness.py`, `plugin/` |
| [20](step_20_openrouter/) | OpenRouter routing and cost | `openrouter.py`, `llm.py`, `commands.py` |
| [21](step_21_streaming_headless/) | streaming, headless `-p` | `llm.py`, `ui.py`, `agent.py` |
| [22](step_22_parallel_tools/) | parallel tool calls | `tools.py`, `agent.py`, `subagent.py` |
| [23](step_23_browser_use/) | browser use, browser subagent | `browser.py`, `permissions.py` |
| [24](step_24_computer_use/) | computer use, image messages | `computer.py`, `history.py`, `agent.py` |
| [25](step_25_memory/) | persistent memory | `memory.py`, `context.py`, `commands.py` |
| [26](step_26_mcp_client/) | MCP client | `mcp_client.py`, `permissions.py`, `commands.py` |
| [27](step_27_hooks/) | hooks | `hooks.py`, `tools.py`, `agent.py` |
| [28](step_28_plan_mode/) | plan mode, structured output | `plan.py`, `commands.py`, `permissions.py` |
| [29](step_29_jobs_parallel_subagents/) | background jobs, parallel subagents | `jobs.py`, `subagent.py`, `context.py` |
| [30](step_30_eval/) | evaluation harness | `evaluate.py`, `agent.py`, `evals/` |
| [31](step_31_instruction_files/) | project instruction files, `/init` | `instructions.py`, `commands.py` |
| [32](step_32_context_budget/) | context budget, deferred tools | `budget.py`, `tools.py` |
| [33](step_33_checkpoints/) | workspace checkpoints, `/undo` | `checkpoint.py`, `commands.py` |
| [34](step_34_durability/) | retries, loop detection, crash recovery | `llm.py`, `agent.py`, `session.py` |
| [35](step_35_human_in_the_loop/) | `ask_user`, steering, session rules | `tools.py`, `agent.py`, `permissions.py` |
| [36](step_36_orchestration/) | subagent definitions, `/pipeline` | `agents.py`, `commands.py` |
| [37](step_37_production_anatomy/) | production harness anatomy | `README.md` |
| [38](step_38_capstone/) | capstone | `capstone/` |
| [39](step_39_approval_modes/) | approval modes | `modes.py`, `permissions.py` |
| [40](step_40_handoffs/) | handoffs | `handoff.py`, `agent.py` |
| [41](step_41_stop_conditions/) | stop conditions, stop hook | `stop.py`, `hooks.py` |
| [42](step_42_streaming_tool_output/) | streaming tool output | `tools.py`, `ui.py` |
| [43](step_43_extensions/) | extensions | `extensions.py` |
| [44](step_44_replay_trace/) | replay and trace viewer | `session.py`, `trace.py` |
| [45](step_45_typescript_core/) | the core loop in TypeScript | `harness-ts/` |
| [46](step_46_trueforge_loop/) | the loop on TrueForge | `client/loop.py` |
| [47](step_47_trueforge_tools_mcp/) | tools and permissions as MCP | `tools_server.py`, `client/approve.py` |
| 48 | sandbox, skills, code mode | `client/sandbox.py` |
| [49](step_49_trueforge_context/) | context, questions, stop conditions | `client/context.py` |
| 50 | subagents, sessions, evaluation | `client/threads.py`, `client/evaluate.py` |
| 51 | TrueForge versus this codelab versus managed agents | `README.md` |

## Tests and checks

```bash
python run_tests.py              # every stage, against a fake model, no key needed
python run_tests.py 2 14         # stages 2.x and 14 only
python check_snippets.py         # every code snippet in every README exists in the code
```

CI runs both on Linux, macOS and Windows.

## Platform notes

- **macOS and Linux.** The stage 12 sandbox uses `sandbox-exec` (built in)
  or `bwrap` (`apt install bubblewrap`). The banner shows which is active.
- **Windows.** There is no OS sandbox. The banner shows `sandbox: none`.
  `bash` runs through `cmd.exe` unless you run from Git Bash or WSL. The UI
  forces UTF-8 output so panels draw correctly.

## Credits

The stage 12 sandbox profile follows the shape used by the OpenAI Codex CLI
(Apache-2.0). The allow / ask permission design follows OpenCode.

MIT licensed.
