# Stage 2.2 - Generic tools

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **From a reply to an agent**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 2.1 - Chat with a simple bash tool](../step_02_1_bash_tool/README.md). Next: [Stage 2.3 - A read_file tool](../step_02_3_read_file/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

A separate `tools.py` file pays off as soon as the number of tools grows.
This stage sets that file up before any more tools arrive.

**What this stage adds:** structure, not capability. The tool moves out of
`llm.py` into `tools.py`, the model's tool call is dispatched through a
table instead of an `if` on the name, and one function, `run_tool`, turns
any tool call into a result string without ever raising.

## Why a table, and why one dispatch function

With one tool, `if name == "bash"` is fine. With five it is a chain of
`if`s that each new tool has to be threaded through, and every error
case has to be handled five times. A dictionary keyed by name makes a new
tool a one-line registration. A single `run_tool` makes the error
handling exist once: whatever the model sends - a name that does not
exist, arguments that are not JSON, a tool that raises - comes back as
text. From stage 2.4 that text is what the model reads next, so a bad call
is a correction, not a crash.

## The code, piece by piece

### 1. Two tables in `tools.py`

`tools.py`:

```python
def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    proc = subprocess.Popen(
        command, shell=True, stdin=subprocess.DEVNULL,  # no stdin: an interactive command ends, it does not wait
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", errors="replace",             # never a UnicodeDecodeError on odd output
        env=BASH_ENV, **NEW_GROUP,
    )
```

```python
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command and return its combined stdout and stderr.",
```

```python
TOOLS = {"bash": bash}
```

Every tool is two things that live in different worlds:

| | Who reads it | What it is |
|---|---|---|
| an entry in `TOOL_SCHEMAS` | the model | JSON: name, description, parameters |
| an entry in `TOOLS` | the harness | the Python function, keyed by the same name |

The `bash` function is the one from stage 2.1 (closed stdin, UTF-8
decoding, a 60-second timeout that kills the whole process tree, no
pagers); it just moved.

### 2. `run_tool`: one call in, one result out, never an exception

`tools.py`:

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

`TOOLS[name](**args)` is the registry idea. The model's `function.name`
is a dictionary key, and the parsed JSON arguments become keyword
arguments. The schema's `required` list and the Python signature are the
contract: a key the model leaves out is a `TypeError` from Python, a key
it invents is a `TypeError` too, and both come back as
`Error: TypeError: ...`.

Three error strings are used verbatim in every later stage:

| Situation | Result string |
|---|---|
| arguments are not a JSON object | `Error: the arguments of {name} are not a JSON object: {reason}` |
| no such tool | `Error: no tool named 'name'.` |
| the tool raised | `Error: {ExceptionType}: {message}` |

A tool that returns something other than a string - `None`, a list, a
dict - is turned into text as well, because a tool message must be text.

### 3. Dispatch in `llm.py`

`llm.py`:

```python
from tools import TOOL_SCHEMAS, run_tool
```

```python
        tools=TOOL_SCHEMAS,
```

```python
if message.tool_calls:
    tool_call = message.tool_calls[0]
    args, result = run_tool(tool_call)  # name -> function, JSON -> kwargs, errors -> text
    print("Tool: ", tool_call.function.name, args)
    print(result, "\n")
```

`llm.py` no longer knows which tools exist. Adding a tool is one function
and one schema in `tools.py`. Stage 2.3 does exactly that.

## Why this matters

Tools are what give agents capabilities. The system prompt instructs the
model on how to do things. Tools let the agent act outside its network
weights. A bare neural network cannot write files, read files or run bash
commands. With a tool call it can do all of those things.

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

Expected output:

```text
Enter your prompt> list the files here

Agent:  None

Tool:  bash {'command': 'ls'}
README.md
llm.py
test_step.py
tools.py

{'prompt_tokens': 140, 'completion_tokens': 12, 'reasoning_tokens': None, 'cached_tokens': 0}
```

Same behaviour as 2.1; the difference is in the code.

## Error handling

- A tool name not in `TOOLS`: `Error: no tool named 'x'.` is printed as the result.
- Arguments that are not a JSON object: `Error: the arguments of bash are not a JSON object: ...`.
- A missing or extra argument, or an exception inside the tool: `Error: TypeError: ...` / `Error: <Type>: ...`.
- A hung command: `Error: command timed out after 60s`; a failed command: its stderr.
- No prompt on stdin, ctrl-c, a dead model call: one line and exit code 1, as in stage 1.
- Leaving: the script ends after one reply.

## Gotchas

- `bash` runs `cmd.exe` on Windows and `/bin/sh` elsewhere; the name is a
  promise about the *idea*, not the shell.
- Only the first tool call of a reply is run in this stage. Stage 2.4 runs
  them all.
- `run_tool` catches `Exception`, not `BaseException`: ctrl-c still stops
  the program, which is what you want.

## Files

```text
step_02_2_generic_tools/
├── llm.py           dispatches the tool call through run_tool
├── tools.py         the tool registry: TOOLS, TOOL_SCHEMAS, run_tool
├── test_step.py     offline tests: registry and schemas agree, dispatch by name, run_tool never raises
└── README.md        this file
```

## Test

`python -m pytest test_step.py` checks that the two tables agree, that a
tool call is dispatched by name, that `run_tool` returns the three
`Error:` strings instead of raising (bad JSON, unknown name, a tool that
raises, a wrong keyword), and the bash tool's UTF-8, stdin and timeout
behaviour.

## Diff from stage 2.1

```bash
diff ../step_02_1_bash_tool/llm.py llm.py
cat tools.py
```

## What the next step adds

Stage 2.3 adds a second tool, `read_file`, and touches only `tools.py`.

<!-- harness-learning-check -->
## Check your understanding

A tool name exists, but its arguments are malformed. What should reach the next decision?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

A clear validation or execution error tied to that call. A tool schema helps describe valid arguments; it does not make every proposed call valid.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
