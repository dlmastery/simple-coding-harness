# Stage 2.2 - Generic tools

A separate `tools.py` file pays off as soon as the number of tools grows.
This stage sets that file up before any more tools arrive.

**What this stage adds:** structure, not capability. The tool moves out of
`llm.py` into `tools.py`, and the model's tool call is dispatched through a
table instead of an `if` on the name.

## The code, piece by piece

### 1. Two tables in `tools.py`

`tools.py`:

```python
def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
    return (result.stdout + result.stderr) or "(no output)"
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

Two small hardening touches come with the move. The subprocess gets a
60-second `timeout`. An empty result becomes `"(no output)"`, because an
empty tool result confuses models.

### 2. Dispatch by name in `llm.py`

`llm.py`:

```python
from tools import TOOLS, TOOL_SCHEMAS
```

```python
    tools=TOOL_SCHEMAS,
```

```python
if message.tool_calls:
    tool_call = message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    result = TOOLS[tool_call.function.name](**args)  # name -> function, JSON -> kwargs
    print("Tool: ", tool_call.function.name, args)
    print(result, "\n")
```

That one line is the registry idea. The model's `function.name` is a
dictionary key, and the parsed JSON arguments become keyword arguments.
`llm.py` no longer knows which tools exist. Adding a tool is one function
and one schema in `tools.py`. Stage 2.3 does exactly that.

## Why this matters

Tools are what give agents capabilities. The system prompt instructs the
model on how to do things. Tools let the agent act outside its network
weights. A bare neural network cannot write files, read files or run bash
commands. With a tool call it can do all of those things.

## Run it

```bash
python llm.py
Enter your prompt> list the files here
```

Same behaviour as 2.1; the difference is in the code.

## Diff from stage 2.1

```bash
diff ../step_02_1_bash_tool/llm.py llm.py
cat tools.py
```
