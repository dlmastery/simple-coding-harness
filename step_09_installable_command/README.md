# Stage 9 - An installable command

**What this stage adds:** packaging. The flat files move into a `harness/`
package, the loop moves inside `main()`, credentials get a config module,
and `pyproject.toml` declares a console script. The loop itself does not
change: it is the stage 8 loop, indented one level, with the same guard
rails - a tool call can never crash it, and every transcript it saves is
one the API will accept back.

```text
harness/
├── agent.py      main(): the stage 8 loop, indented one level
├── config.py     new: BASE_URL / API_KEY / MODEL from the env or ~/.simple-harness/env
├── llm.py        reads config instead of os.environ
├── tools.py  skills.py  context.py  session.py  commands.py  ui.py   (relative imports)
pyproject.toml    [project.scripts] harness = "harness.agent:main"
```

## Why: a coding agent has to run from the project it edits

Up to stage 8 you `cd` into the stage directory and run `python agent.py`,
so the agent's working directory is the stage directory - it can only edit
itself. A coding agent is useful when you run it from *your* project:
skills come from that project's `.agents/skills`, sessions are filed under
that project's name, `git status` is that project's. That needs a command
on the PATH, which needs a package with an entry point. Without this stage
every later stage would still be a script you copy around.

## Files

```text
step_09_installable_command/
├── harness/
│   ├── __init__.py      marks the package
│   ├── agent.py         main(): the stage 8 loop, indented one level
│   ├── commands.py      slash commands: /rewind (user messages only), /sessions, /exit
│   ├── config.py        BASE_URL / API_KEY / MODEL from env or ~/.simple-harness/env
│   ├── context.py       the late block, unchanged from stage 8
│   ├── llm.py           call_llm reads its credentials from config.py; entry(), usage_from()
│   ├── session.py       transcripts on disk; load() repairs a cut-off transcript
│   ├── skills.py        skills; a broken SKILL.md is skipped, not fatal
│   ├── tools.py         run_tool() never raises; bash kills its process group on timeout
│   └── ui.py            the presentation layer; ask() returns None when you leave
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py         offline tests: the loop, bad tool calls, utf-8, rewind, resume, config
├── pyproject.toml       [project.scripts] harness = "harness.agent:main"; 0.9.0
└── README.md            this file
```

## The code, piece by piece

### 1. The entry point

`pyproject.toml`:

```text
[project.scripts]
harness = "harness.agent:main"
```

`harness/agent.py`:

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="continue the last session")
    parser.add_argument("--debug", action="store_true", help="show the raw model response")
    cli = parser.parse_args()

    ui.banner()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
```

```python
if __name__ == "__main__":
    main()
```

`pip install -e .` creates a `harness` executable that calls
`harness.agent.main`. `uv tool install .` does the same job. Because the
loop now runs from any directory, every "where am I" decision keys off the
current working directory: skills are looked up under that directory's
`.agents/skills`, sessions are filed under its name, and `git status` is
taken there.

### 2. Credentials in one place

`harness/config.py`:

```python
HOME = Path.home() / ".simple-harness"
ENV_FILE = HOME / "env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

BASE_URL = os.environ.get("BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.environ.get("API_KEY", "")
MODEL = os.environ.get("MODEL", "deepseek/deepseek-v4-flash")
```

Real environment variables win; the file fills the gaps, so you set the
key once. `setdefault` is what makes the precedence work. Quotes around a
value are stripped, so `API_KEY="sk-..."` works the way a `.env` file
would. A complete `~/.simple-harness/env`:

```text
API_KEY=sk-or-v1-...
# BASE_URL=https://openrouter.ai/api/v1
# MODEL=deepseek/deepseek-v4-flash
```

`harness/llm.py`:

```python
client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)
MODEL = config.MODEL
```

### 3. Relative imports

Every `from tools import ...` became `from .tools import ...`. That is the
whole difference between a folder of scripts and a package.

### 4. The loop's guard rails

These are the same as in stage 8; they are listed here because the package
is what every later stage copies forward, so this is where to read them.

A tool call never raises. `harness/tools.py`:

```python
def run_tool(tool_call):
    """Turn one tool call into (args, result). Never raises: whatever goes
    wrong becomes the result string, so the model reads it and tries again."""
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments or "{}")
        if not isinstance(args, dict):
            raise ValueError("not an object")
    except ValueError as e:  # the model wrote broken JSON
        return {}, f"Error: the arguments of {name} are not a JSON object: {e}"
    if name not in TOOLS:  # a name that is not in the table
        return args, f"Error: no tool named {name!r}."
    try:
        result = TOOLS[name](**args)  # name -> function, JSON -> kwargs
    except Exception as e:  # wrong arguments, missing file, anything the tool raises
        return args, f"Error: {type(e).__name__}: {e}"
    if not isinstance(result, str):  # a tool message must be text
        result = "(no output)" if result is None else json.dumps(result, default=str)
    return args, result
```

The loop appends the tool message whatever the result was, so every tool
call the model made has exactly one answer - the API rejects a transcript
where one is missing. `harness/agent.py`:

```python
                for tool_call in message.tool_calls:
                    args, result = run_tool(tool_call)
                    ui.tool(tool_call.function.name, args, result)
```

A turn is bounded, and a dead model call or ctrl-c ends the turn, not the
program:

```python
MAX_CALLS = 40  # model calls in one turn before we stop and ask the user
```

```python
                try:
                    with ui.working():
                        message, usage = call_llm(messages + [injection])
                except (openai.APIError, RuntimeError) as failed:
                    ui.note(f"model call failed: {failed}")
                    break
```

```python
        except KeyboardInterrupt:
            # ctrl-c mid-turn: answer the tool calls that never ran, so the
            # transcript stays valid, and go back to the prompt.
            session.repair(messages, "(interrupted before this tool ran)")
            session.save(messages)
            ui.note("interrupted")
```

Only the reply's role, content and tool calls go into the transcript.
`harness/llm.py`:

```python
def entry(message):
    """The transcript entry for a reply: role, content and tool_calls, nothing else.

    Providers attach extras (reasoning, annotations) that must not be sent
    back on the next call, so the whole message is never dumped as it is.
    """
    saved = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        saved["tool_calls"] = [call.model_dump(exclude_none=True) for call in message.tool_calls]
    return saved
```

A transcript that stopped between a reply and its tool results is repaired
when it is loaded, so `--resume` after a crash works. `harness/session.py`:

```python
def repair(messages, note):
    """Answer every tool call in the last reply that has no result. Returns how many.

    A crash or ctrl-c between a reply and its tool results leaves a transcript
    the API refuses; a placeholder result per unanswered call makes it valid.
    """
```

`/rewind` only offers your own messages as cut points, for the same reason:
a cut between a tool call and its result would be refused by the API.

The `bash` tool runs the command in its own process group, with no stdin
and no pager, so a timeout kills everything the command started and a
command that waits for a key ends instead of hanging. `harness/tools.py`:

```python
TIMEOUT = 60
# no pagers, no credential prompts: the command has no terminal to answer on
BASH_ENV = {**os.environ, "PAGER": "cat", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0"}
# the command starts its own process group, so a timeout can kill all of it
NEW_GROUP = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
```

```python
    try:
        out, err = proc.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        kill_tree(proc.pid)
        proc.communicate()
        return f"Error: command timed out after {TIMEOUT}s"
```

Files are read and written as UTF-8 whatever the locale, so a README with
a `├──` tree does not raise `UnicodeEncodeError` on Windows.

## Run it

Prerequisites: Python 3.10+, an OpenRouter key (or any OpenAI-compatible
endpoint) in `~/.simple-harness/env` or the environment.

bash:

```bash
pip install -e .
cd ~/any/other/project
harness
```

PowerShell:

```powershell
pip install -e .
cd ~\any\other\project
harness
```

or without installing: `python -m harness.agent` from this directory.
`harness --resume` reopens the last chat for the project you are in.

### Expected output

```text
─────────────────────────── coding agent ───────────────────────────
  /sessions  /rewind  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave

> what is in this directory?

  ┌─ late injection ─────────────────────────┐
  │ <env>                                     │
  │ time: 2026-09-18 14:02                    │
  │ git branch: main                          │
  │ </env>                                    │
  └───────────────────────────────────────────┘

  ┌──────────────────────────────────────────┐
  │ bash ls -la                              │
  │ ──────────────────────────────────────── │
  │ total 24                                 │
  │ drwxr-xr-x  5 you  staff  160 README.md  │
  └──────────────────────────────────────────┘

  agent

  A Python project: `README.md`, a `src/` package and `tests/`.

  1,412 prompt · 61 completion
```

## Error handling

- A tool call with broken JSON, an unknown tool name, a missing file or a
  wrong argument comes back to the model as `Error: ...` (see `run_tool`).
  The session keeps going and the model usually corrects itself.
- A command that runs longer than 60 s is killed, with everything it
  started, and the model reads `Error: command timed out after 60s`.
- A model call that fails (bad key, rate limit, provider down) prints
  `model call failed: ...` and returns to the prompt; your message is kept.
- ctrl-c during a turn prints `interrupted` and returns to the prompt with a
  valid transcript. ctrl-c at the prompt leaves.
- To leave: `/exit`, ctrl-d (ctrl-z then enter on Windows) or ctrl-c at the
  prompt. An empty line does nothing.

## Gotchas / What this is not

- Every stage installs the same distribution (`simple-coding-harness`) and
  the same package (`harness`), so only one stage is installed at a time.
  `pip install -e .` from another stage directory switches.
- The stage's own `explain-code` skill lives in *this* directory's
  `.agents/skills`; run `harness` from another project and it is not there.
  Put skills you always want under `~/.agents/skills`.
- The tool is named `bash` but runs whatever `shell=True` gives you:
  `/bin/sh` on macOS and Linux, `cmd.exe` on Windows. Stage 12 says more.
- Nothing here checks what a command does before running it. Stage 11 adds
  permissions, stage 12 a sandbox.

## What the next stage adds

Stage 10 gives the model a `write_todos` tool and shows the plan back to
it on every call, so a long task does not lose its place.

## Diff from stage 8

```bash
diff ../step_08_sessions_rewind/agent.py harness/agent.py   # four spaces and a def main()
cat harness/config.py
```
