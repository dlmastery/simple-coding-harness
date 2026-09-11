# Stage 2.3 - A read_file tool

`read_file` opens a path, reads it, and returns the text to the agent.
That is the whole change.

**What this stage adds:** a second tool, and proof that stage 2.2 paid
off: `llm.py` does not change.

## The code

`tools.py`:

```python
def read_file(path: str) -> str:
    """Read a file and return its contents."""
    with open(path) as f:
        return f.read()
```

```python
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    }
                },
                "required": ["path"],
            },
        },
    },
```

```python
TOOLS = {"bash": bash, "read_file": read_file}
```

One function, one schema, one dictionary entry. The dispatch line in
`llm.py` (`TOOLS[tool_call.function.name](**args)`) picks it up because
the schema's `name` and the dictionary key are the same string.

## Why a read tool when `cat` exists

`bash("cat llm.py")` would work. A dedicated tool with a clear
description gets chosen more reliably than a shell command the model has
to remember. Its argument is a path, which the harness can later watch
(stage 7 records which files the agent has read) and gate (stage 11 asks
before writes outside the project).

## Run it

```bash
python llm.py
Enter your prompt> can you read the llm.py file
```

The model calls the read tool, and the entire content of the file is
printed.

## The problem this stage makes obvious

The model generates tool call arguments, and the harness executes them.
The results never go back to the model, so the model cannot act on them.
The file was read into *your* terminal, not into the model's context.
Stage 2.4 closes that gap. That is where the program becomes an *agent*.

## Diff from stage 2.2

```bash
diff ../step_02_2_generic_tools/tools.py tools.py
```
