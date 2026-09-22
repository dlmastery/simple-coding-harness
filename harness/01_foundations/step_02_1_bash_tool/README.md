# Stage 2.1 - Chat with a simple bash tool

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **From a reply to an agent**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 1 - Minimal chat](../step_01_minimal_chat/README.md). Next: [Stage 2.2 - Generic tools](../step_02_2_generic_tools/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

This stage introduces tool calls.

**What this stage adds:** one tool. The model can *ask* for a shell
command to be run. The harness runs it and prints the result. The result
is not yet sent back to the model; that is stage 2.4.

```text
you ──▶ model ──▶ tool_call: bash {"command": "pwd"} ──▶ subprocess ──▶ printed for you
```

## Why a tool

A model is text in, text out. It cannot list a directory, and stage 1
showed what happens when you ask: it guesses. A tool call is the model
writing a small JSON request - *please run this command* - and the harness
doing the running. Without it, every fact about your machine has to be
pasted into the prompt by you. With it, the model asks for what it needs.

## The code, piece by piece

### 1. The system prompt says the tool exists

`llm.py`:

```python
SYSTEM_PROMPT = """
You are a coding agent. Your job is to code. Always code.
Use the bash tool to inspect files.
Answer back to the user once exploration is done.
"""
```

The system prompt gains one instruction: use the bash tool to inspect
files. The schema below tells the model *what* the tool is. The prompt
tells it *when* to reach for it.

### 2. The schema: what the model sees

`llm.py`:

```python
BASH_TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a shell command and return its output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to run",
                }
            },
            "required": ["command"],
        },
    },
}
```

The schema is a JSON object that describes the tool's shape. The type is
`function`. The name is `bash`, so the model must use the term `bash` to
invoke this tool. The description says: run a shell command and return
its output. The description is read by the model, so it is a prompt.
`parameters` is a JSON schema; here it is one required string.

### 3. The function: what actually runs

`llm.py`:

```python
def bash(command):
    """The Python behind the schema. A subprocess executes what the model chose."""
    proc = subprocess.Popen(
        command, shell=True, stdin=subprocess.DEVNULL,  # no stdin: an interactive command ends, it does not wait
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", errors="replace",             # never a UnicodeDecodeError on odd output
        env=BASH_ENV, **NEW_GROUP,
    )
    try:
        out, err = proc.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        kill_tree(proc.pid)
        proc.communicate()
        return f"Error: command timed out after {TIMEOUT}s"
    return (out + err) or "(no output)"
```

A subprocess executes a command line from Python. Whatever command the
model chooses, such as `ls`, `grep` or `cat`, is passed to the shell. The
model never runs anything itself. It produces text. This function is the
only thing that executes.

Four lines of this function are plumbing, and each one closes a way for
the agent to hang or crash:

- `stdin=subprocess.DEVNULL`: the command gets no keyboard. `python`,
  `cat` with no file, or `git log` waiting for its pager would otherwise
  sit forever waiting for input nobody can type.
- `encoding="utf-8", errors="replace"`: output is decoded as UTF-8 and an
  undecodable byte becomes a replacement character instead of a
  `UnicodeDecodeError`. Without it, Windows decodes with the console code
  page and `git log` with one accented name takes the program down.
- `TIMEOUT` and `kill_tree`: after 60 seconds the command is killed,
  together with every process it started. Killing only the shell leaves
  its children running and, on Windows, keeps the pipes open so the
  harness would still wait. `NEW_GROUP` puts the command in its own
  process group so that `taskkill /T` (Windows) or `killpg` (elsewhere)
  can take the whole tree.
- `BASH_ENV` sets `PAGER=cat`, `GIT_PAGER=cat` and
  `GIT_TERMINAL_PROMPT=0`, so git never opens a pager or asks for a
  password.

An empty result becomes `(no output)`, because an empty tool result
confuses models.

### 4. Passing the tool and handling the call

`llm.py`:

```python
        tools=[BASH_TOOL],  # the only change to the request
```

The only change to the request is `tools=[BASH_TOOL]`. The whole schema is
passed to the model with every call.

```python
if message.tool_calls:
    tool_call = message.tool_calls[0]
    try:
        command = json.loads(tool_call.function.arguments)["command"]
    except (ValueError, KeyError, TypeError) as e:  # the model can produce broken JSON
        sys.exit(f"Error: the arguments of bash are not a JSON object: {e}")
    print("Tool: bash", command)
    print(bash(command), "\n")
```

Inspect `message` at this point and the shape is clear. Its `content` is
`None`, so the model generated no text. Under `tool_calls` it did do
something: the function name is `bash` and the arguments are the JSON
string `{"command": "pwd"}`. A tool call is the reply taking a different
shape: a function name plus a JSON string of arguments. The harness parses
the JSON and calls the Python function with it.

The arguments are a *string* the model wrote, and models occasionally
write broken JSON or leave out a required key. Parsing is therefore
guarded; this one-shot script exits with an `Error:` line, and from stage
2.4 the same text goes back to the model so it can try again.

This stage runs only the first tool call. A reply can carry several;
stage 2.4 runs them all.

## Run it

bash:

```bash
export BASE_URL=https://openrouter.ai/api/v1
export API_KEY=sk-or-...
python llm.py
```

PowerShell:

```powershell
$env:BASE_URL = "https://openrouter.ai/api/v1"
$env:API_KEY = "sk-or-..."
python llm.py
```

Expected output (Linux/macOS):

```text
Enter your prompt> what is your current directory? also use the bash tool

Agent:  None

Tool: bash pwd
/home/you/simple-coding-harness/harness/01_foundations/step_02_1_bash_tool

{'prompt_tokens': 131, 'completion_tokens': 14, 'reasoning_tokens': None, 'cached_tokens': 0}
```

`Agent:  None` is printed on purpose: it shows that a reply with a tool
call carries no text.

## Error handling

- Broken tool arguments: `Error: the arguments of bash are not a JSON object: ...`, exit code 1.
- A command that fails: its stderr is in the printed output (`out + err`), nothing is raised.
- A command that hangs or runs too long: `Error: command timed out after 60s`.
- A command that prints bytes that are not UTF-8: decoded with a replacement character in place of the bad byte.
- A dead model call: `model call failed: ...`, exit code 1.
- Leaving: the script ends after one reply; ctrl-c at the prompt exits.

## Gotchas

- The tool is *named* `bash`, but `shell=True` runs the platform shell:
  `/bin/sh` on Linux and macOS, `cmd.exe` on Windows. On Windows, `pwd`
  and `ls` answer `'pwd' is not recognized...`; the model usually
  recovers by trying `cd` or `dir`, but the expected output above is a
  Unix transcript.
- There is no sandbox and no confirmation. The model can ask for
  `rm -rf` and this stage runs it. Stage 11 adds permissions and stage 12
  a sandbox.
- The output goes to *your* screen. The model never sees it, so it cannot
  answer a question that needs two commands.

## What is still missing

Stage 2.4 passes the output back into the model and creates a loop of
tool calls. Stage 2.2 first tidies the tool table so adding more tools
costs nothing.

## Files

```text
step_02_1_bash_tool/
├── llm.py           the chat, plus a bash tool the harness runs on request
├── test_step.py     offline tests: a tool call is parsed and executed; bad JSON; UTF-8, stdin, timeout
└── README.md        this file
```

## Test

`python -m pytest test_step.py` runs the script against a fake client that
answers with a tool call, then checks that broken arguments give an
`Error:` line, that UTF-8 output decodes, that a command reading stdin
does not hang, and that a timed-out command is killed.

## Diff from stage 1

```bash
diff ../step_01_minimal_chat/llm.py llm.py
```

## What the next step adds

Stage 2.2 moves the tool into `tools.py` and dispatches calls by name
through a table, so a new tool is one function plus one schema.
