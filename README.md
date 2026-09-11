# simple-coding-harness

**Zero to hero harness engineering.** Build a coding agent from one API
call to a full harness with tools, skills, sessions, permissions, a
sandbox, compaction and subagents. Then run the same harness on four agent
SDKs and on OpenRouter, and see which parts each framework does for you.

Each stage is one directory. Each directory holds the complete program at
that stage, a README that explains the code line by line, and a test that
runs the code against a fake model. You can run any stage on its own. You
can diff any stage against the one before it.

```text
Part 1   stages 1 - 15    build the harness by hand, one idea per stage
Part 2   steps 16 - 19    the same harness on four agent SDKs
Part 3   step 20          the same harness on OpenRouter, with model routing and cost
```

---

## Quick start

### 1. Install

```bash
git clone https://github.com/dlmastery/simple-coding-harness
cd simple-coding-harness
pip install -r requirements.txt
```

This installs `openai`, `rich`, `pyyaml`, `prompt-toolkit` and `pytest`.
Python 3.10 or newer is required.

### 2. Set the model endpoint

The harness talks to any endpoint that implements the OpenAI chat API.
Set three variables:

| Variable | What it is | Example |
|----------|------------|---------|
| `BASE_URL` | the endpoint | `https://openrouter.ai/api/v1` |
| `API_KEY` | your key for that endpoint | `sk-or-...` |
| `MODEL` | a model id that supports tool calling | `deepseek/deepseek-v4-flash` |

Examples for common providers:

```bash
# OpenRouter (one key, hundreds of models; see Part 3)
export BASE_URL=https://openrouter.ai/api/v1 API_KEY=sk-or-... MODEL=deepseek/deepseek-v4-flash

# OpenAI
export BASE_URL=https://api.openai.com/v1 API_KEY=sk-... MODEL=gpt-4.1-mini

# Google Gemini
export BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/ API_KEY=AIza... MODEL=gemini-2.5-flash

# DeepSeek
export BASE_URL=https://api.deepseek.com/v1 API_KEY=sk-... MODEL=deepseek-chat

# Ollama, local
export BASE_URL=http://localhost:11434/v1 API_KEY=ollama MODEL=qwen2.5-coder
```

On Windows PowerShell use `$env:BASE_URL = "..."` for each variable.

From stage 9 onward you can put the same three lines in
`~/.simple-harness/env` instead. Then you do not export them in each shell.

### 3. Run a stage

Stages 1 to 8 are flat files. Run the script directly:

```bash
cd step_01_minimal_chat && python llm.py          # one prompt, one reply
cd step_02_4_agent_loop && python agent.py        # the first real agent
cd step_08_sessions_rewind && python agent.py     # sessions, /rewind, --resume
```

Stages 9 to 15 are a package named `harness`. Run it as a module, or
install it as a command:

```bash
cd step_15_subagents
python -m harness.agent                           # run in place

pip install -e .                                  # or install the command
cd ~/some/other/project
harness                                           # works in any directory
harness --resume                                  # continue the last chat
```

Inside the chat: type a request and press enter. `/rewind`, `/sessions`
and `/compact` are commands. An empty line or ctrl-d exits.

### 4. Run the tests

No key is needed for the tests. Each stage has a `test_step.py` that runs
the real code against a fake model.

```bash
python run_tests.py              # every stage
python run_tests.py 2 14         # stages 2.x and 14 only
python check_snippets.py         # every code snippet in every README exists in that stage's code
```

CI runs both on Linux, macOS and Windows.

---

## Part 1 - Build the harness by hand

This is the story of the harness. Each stage adds one idea. The code of
each stage is the code of the stage before it plus that idea.

### The core loop

Everything in Part 1 is built around one loop. It appears at stage 2.4 and
never changes in spirit:

```python
while True:
    message, usage = call_llm(messages)              # the model sees the whole transcript
    messages.append(message.model_dump(exclude_none=True))
    if not message.tool_calls:                        # plain text: the turn is over
        break
    for tool_call in message.tool_calls:              # otherwise run each call ...
        args = json.loads(tool_call.function.arguments)
        result = TOOLS[tool_call.function.name](**args)
        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})  # ... and feed it back
```

Read it as four steps. Send the transcript to the model. Add the reply to
the transcript. If the reply has no tool calls, stop. If it has tool
calls, run each one, add each result to the transcript, and go again.

The later stages wrap this loop, inject into its request, save its
messages, gate its tool calls, shrink its transcript, and run a copy of it
inside a subagent. Follow `agent.py` from stage to stage to watch each
change land.

### The stages

**Stage 1 - Minimal chat.** `llm.py` sends a system message and a user
message and prints the reply and the token usage. There are no tools and
no memory. This is the whole program, and every later stage is this file
plus one idea. The usage line is printed from the start because
`cached_tokens` becomes the number to watch once the transcript is re-sent
on every call.

**Stage 2.1 - A bash tool.** A tool is two things. A JSON schema tells the
model that a function named `bash` exists and takes a `command`. A Python
function runs that command with `subprocess.run`. The model never runs
anything. It replies with a tool call, a function name and JSON arguments,
and the harness runs the function. This split is the security model of
every coding agent.

**Stage 2.2 - Generic tools.** The tool moves into `tools.py` with two
tables. `TOOL_SCHEMAS` is what the model sees. `TOOLS` maps each name to a
function. Dispatch becomes one line: the model's function name is a
dictionary key, and the parsed JSON becomes keyword arguments. Adding a
tool is now one function and one schema.

**Stage 2.3 - A read_file tool.** A second tool proves the point of stage
2.2: `llm.py` does not change. But the result still goes to the screen,
not to the model, so the model cannot use what it read.

**Stage 2.4 - The agent loop.** The request moves into `call_llm(messages)`
and `agent.py` gains the loop shown above. Tool results are appended with
role `tool` and the matching `tool_call_id`, and the model is called again
until it answers in text. The program is now an agent. This stage also
introduces the rule that shapes the rest of the build: the transcript is
re-sent on every call, providers cache the unchanged prefix, so never
change the beginning of the prompt.

**Stage 3 - Better UI.** `ui.py` draws the agent's text, each tool call in
a panel, and a usage line after every call that shows how many tokens were
served from cache. `agent.py` gains an outer loop so the program is a chat.
The inner loop is stage 2.4 unchanged.

**Stage 4 - Skills.** A skill is a `SKILL.md` file with a YAML front
matter. Only the name and description go into the system prompt. The body
is read on demand with a `read_skill` tool. A project can ship fifty
skills and pay for fifty lines of context, not fifty documents.

**Stage 5 - File editing.** `write_file` creates a file. `str_replace`
swaps one exact block of text for another and refuses if the text is
missing or ambiguous. The refusal is returned as the tool result, so the
model reads it and retries with a more specific match. The agent can now
change code.

**Stage 6 - Late injection.** Some facts change on every call: the time,
the git branch. `context.py` builds a small `<env>` block and the loop
sends `messages + [reminder()]`. The block is appended to the request, at
the end, and never stored in the transcript. That keeps the cached prefix
intact and keeps stale copies out of the history.

**Stage 7 - File freshness.** The tools record the modification time of
every file they touch in a `SEEN` dict. If a file changes on disk before
the next call, the late block carries a reminder to read it again before
editing. This prevents edits against a stale picture of a file.

**Stage 8 - Sessions and rewind.** Every message is appended to a JSONL
file as it happens. `--resume` reopens the last chat. `/sessions` opens
any chat. `/rewind` cuts the transcript back, and the rewind is stored as a
marker, not a deletion, so the file is the full history. The freshness
check moves onto `git status` because a dict does not survive a restart.

**Stage 9 - An installable command.** The files move into a `harness/`
package, the loop moves into `main()`, credentials move into `config.py`,
and `pyproject.toml` declares a `harness` console script. Skills, sessions
and git status all key off the directory you run it in.

**Stage 10 - Todos.** A `write_todos` tool replaces the plan on every call.
Exactly one item may be in progress. The plan lives in a variable, not in
the transcript, and is injected in the late block on every call, so it is
always the last thing the model reads before it acts.

**Stage 11 - Permissions.** A rule table rates every tool call before it
runs. Read-only commands run silently. Risky commands stop and ask you.
A few commands are refused whatever you answer. Compound commands are
split and the strictest part wins. The verdict is returned as the tool
result, so the model reads "Blocked by policy" and adapts. The rules only
see the command text, so this is not real security.

**Stage 12 - Sandbox.** `bash` runs inside a kernel-enforced sandbox where
the OS provides one: Seatbelt on macOS, bubblewrap on Linux. The policy is
read anything, write only inside the project, no network. A Python script
that deletes a file outside the project fails even when you approved the
command. Every command also has a timeout that comes back as a result.

**Stage 13 - Readable todos and a real input line.** The plan is drawn as
a checklist. Typing goes through prompt_toolkit, which can edit a wrapped
line, keeps history across sessions and inserts a newline on alt-enter.
No change to the loop.

**Stage 14 - Compaction.** Tool output is the main reason transcripts
explode, so `history.py` handles it three ways. A fresh result over
10,000 characters is capped and the rest is saved to a temp file the model
can page through. When a turn ends, its results shrink to a 300-character
stub. If a request is still too big, whole results are dropped, oldest
first. When the prompt passes 85% of the context window, a second agent
with no tools writes a handoff note about the old messages, the note is
folded into the system prompt, and the transcript is cut back to 35%. The
prefix is rebuilt once and then stays stable until the next compaction.

**Stage 15 - Subagents.** A `task` tool runs a fresh agent on one
question. It starts with an empty transcript. It gets every tool except
`task`, `write_todos`, `write_file` and `str_replace`, so it cannot edit
and cannot recurse. It runs the same loop through the same permission
check and sandbox. Only its final answer returns to the main agent. The
exploration cost stays in a context that is thrown away.

### Stage index

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

Each stage README has a "Diff from stage N" section with the exact
`diff` command to see what changed.

---

## Part 2 - The same harness on four agent SDKs

Steps 16 to 19 rebuild the stage 15 feature set on a framework each. The
purpose is to see which of the fifteen ideas a given SDK does for you and
which stay yours. The rule table from stage 11 is copied into each step
unchanged as `rules.py`. The SDK supplies the hook. You supply the policy.

| Step | Framework | Runs where | You still write |
|-----:|-----------|------------|-----------------|
| [16](step_16_claude_agent_sdk/) | **Claude Agent SDK** (`claude-agent-sdk`), Claude Code as a library | spawns the `claude` CLI | policy hooks, a prompt-injection hook, one MCP tool, a subagent definition, the screen |
| [17](step_17_openai_agents_sdk/) | **OpenAI Agents SDK** (`openai-agents`) | in-process, any OpenAI-compatible endpoint | all coding tools, skills, todos, a request filter for injection and stripping, the screen |
| [18](step_18_google_antigravity_sdk/) | **Google Antigravity SDK** (`google-antigravity`) | a bundled runtime binary | a policy list, three hooks, a subagent config, two tools, todos |
| [19](step_19_deepseek_harness/) | **DeepSeek Harness** (`deepseek-harness-sdk`) | a bundled `dsh` runtime over JSON-RPC | the policy as a plugin, the patch that mounts it, the event renderer |

### Who owns which mechanism

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

Install the SDKs with `pip install -r requirements-sdks.txt`. Each step's
README inlines the code that wires the SDK. The tests never launch a
model.

Each SDK needs its own credential:

| Step | Needs |
|-----:|-------|
| 16 | the `claude` CLI logged in, or `ANTHROPIC_API_KEY` |
| 17 | `BASE_URL`, `API_KEY`, `MODEL`, as in Part 1 |
| 18 | `GEMINI_API_KEY` |
| 19 | `DEEPSEEK_API_KEY` |

---

## Part 3 - The same harness on OpenRouter

[Step 20](step_20_openrouter/) takes the stage 15 harness and points it at
OpenRouter, one gateway with one key in front of hundreds of models. The
loop does not change. What changes is the model layer:

- **Model routing.** `MODELS` is an ordered list. The first model is the
  primary. The rest are fallbacks that OpenRouter uses when the primary
  fails or is rate limited. The usage line shows which model was served.
- **Provider preferences.** Sort providers by price, throughput or
  latency for the same model.
- **Cost per call.** OpenRouter returns the cost of each request. The
  harness shows it after every call and totals it at exit.
- **`/models` and `/route`.** List available models with their prices, and
  change the route without restarting.

```bash
export OPENROUTER_API_KEY=sk-or-...
export MODELS=deepseek/deepseek-v4-flash,openai/gpt-4.1-mini
cd step_20_openrouter && python -m harness.agent
```

---

## Three rules that hold the whole thing together

1. **Every tool call goes through one place.** From stage 2.2 the model's
   function name is a dictionary key. From stage 15 that lookup lives in
   `execute()`, which the main loop and the subagent share. Permissions,
   the sandbox and the subagent all hook in there.
2. **Never change the beginning of the prompt.** The transcript is re-sent
   on every call and the provider caches the unchanged prefix. Volatile
   facts are appended at send time and thrown away (stage 6). Old tool
   output is shrunk only after its turn ends (stage 14). Compaction rebuilds
   the prefix once and then leaves it alone (stage 14).
3. **Errors are results.** A refused edit, a blocked command, a declined
   prompt, a timeout, a failed compaction: each comes back as text the
   model can read and recover from. Nothing the model does can end the
   session.

## Platform notes

- **macOS and Linux.** The stage 12 sandbox uses `sandbox-exec` (built in)
  or `bwrap` (`apt install bubblewrap`). The banner shows which is active.
- **Windows.** There is no OS sandbox. The banner shows `sandbox: none`.
  `bash` runs through `cmd.exe` unless you run from Git Bash or WSL. The
  UI forces UTF-8 output so panels draw correctly.

## Credits

The stage 12 sandbox profile follows the shape used by the OpenAI Codex
CLI (Apache-2.0). The allow / ask permission design follows OpenCode.

MIT licensed.
