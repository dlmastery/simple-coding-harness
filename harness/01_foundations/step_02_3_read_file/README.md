# Stage 2.3 - A read_file tool

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **From a reply to an agent**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 2.2 - Generic tools](../step_02_2_generic_tools/README.md). Next: [Stage 2.4 - The agent loop](../step_02_4_agent_loop/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

`read_file` opens a path, reads it, and returns the text to the agent.
That is the whole change.

**What this stage adds:** a second tool, and proof that stage 2.2 paid
off: `llm.py` does not change.

## Why a read tool when `cat` exists

`bash("cat llm.py")` would work. A dedicated tool with a clear
description gets chosen more reliably than a shell command the model has
to remember, and it works the same on Windows, where `cat` does not
exist. Its argument is a path, which the harness can later watch (stage 7
records which files the agent has read) and gate (stage 11 asks before
writes outside the project). A tool per intent is also what makes the
error text useful: `Error: FileNotFoundError: ...` names the file the
model got wrong.

## The code

`tools.py`:

```python
def read_file(path: str) -> str:
    """Read a file and return its contents."""
    # utf-8 whatever the console code page; newline="" keeps CRLF and LF as they are
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
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

One function, one schema, one dictionary entry. `run_tool` in `llm.py`
picks it up because the schema's `name` and the dictionary key are the
same string.

Two arguments to `open` are the rule for every file tool from here on:

- `encoding="utf-8", errors="replace"`: source files are UTF-8; Python's
  default on Windows is the console code page, which turns `é` into
  garbage or raises `UnicodeDecodeError`. A byte that is not valid UTF-8
  becomes a replacement character rather than an exception.
- `newline=""`: no translation. A file with CRLF line endings is returned
  with CRLF, so an edit in stage 5 does not rewrite every line of the
  file.

A missing file raises `FileNotFoundError` inside the tool; `run_tool`
turns that into `Error: FileNotFoundError: [Errno 2] No such file or
directory: 'x'`, which from stage 2.4 the model reads.

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
Enter your prompt> can you read the llm.py file

Agent:  None

Tool:  read_file {'path': 'llm.py'}
"""Stage 2.3 - unchanged from 2.2: adding read_file touched only tools.py.
...

{'prompt_tokens': 182, 'completion_tokens': 11, 'reasoning_tokens': None, 'cached_tokens': 0}
```

The model calls the read tool, and the entire content of the file is
printed.

## Error handling

- A path that does not exist: `Error: FileNotFoundError: ...` as the result.
- A directory, a permission problem: `Error: IsADirectoryError: ...` / `Error: PermissionError: ...` (on Windows a directory is `Error: PermissionError`).
- Bytes that are not UTF-8: replaced, never raised.
- Everything from stage 2.2 (bad JSON, unknown tool, timeout, dead model call) is unchanged.

## Gotchas

- There is no size limit. `read_file` on a 50 MB log returns 50 MB. Stage
  14 caps what the model is shown.
- Relative paths resolve against the directory you started `python` in,
  which is also what the system prompt tells the model from stage 2.4 on.
- No path is off limits: the tool reads `~/.ssh/id_rsa` if asked. Stage 11
  adds the permission check.

## The problem this stage makes obvious

The model generates tool call arguments, and the harness executes them.
The results never go back to the model, so the model cannot act on them.
The file was read into *your* terminal, not into the model's context.
Stage 2.4 closes that gap. That is where the program becomes an *agent*.

## Files

```text
step_02_3_read_file/
├── llm.py           unchanged from 2.2
├── tools.py         the registry gains read_file
├── test_step.py     offline tests: read_file, UTF-8 and CRLF, missing file, the script reading itself
└── README.md        this file
```

## Test

`python -m pytest test_step.py` reads a temp file, checks that UTF-8 and
CRLF survive and that a bad byte is replaced, that a missing file becomes
an `Error:` result, and runs the script against a fake model that asks to
read `llm.py`.

## Diff from stage 2.2

```bash
diff ../step_02_2_generic_tools/tools.py tools.py
```

## What the next step adds

Stage 2.4 sends tool results back to the model and loops until the model
answers in text: the agent loop.

<!-- harness-learning-check -->
## Check your understanding

The file exists, but the requested path points elsewhere. Which observation should guide the answer?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

The actual read outcome for the requested path. A failed read must not be replaced by imagined file contents.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
