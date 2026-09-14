# Stage 2.1 - Chat with a simple bash tool

This stage introduces tool calls.

**What this stage adds:** one tool. The model can *ask* for a shell
command to be run. The harness runs it and prints the result. The result
is not yet sent back to the model; that is stage 2.4.

```text
you ──▶ model ──▶ tool_call: bash {"command": "pwd"} ──▶ subprocess.run ──▶ printed for you
```

## Files

```text
step_02_1_bash_tool/
├── llm.py           the chat, plus a bash tool the harness runs on request
├── test_step.py     offline test: a tool call is parsed and executed
└── README.md        this file
```

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
    """The Python behind the schema. subprocess.run executes what the model chose."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr
```

`subprocess.run` executes a command line command from Python. Whatever
command the model chooses, such as `ls`, `grep` or `cat`, is passed
through `subprocess.run`. The model never runs anything itself. It
produces text. This function is the only thing that executes.

### 4. Passing the tool and handling the call

`llm.py`:

```python
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ],
    tools=[BASH_TOOL],  # the only change to the request
)

message = response.choices[0].message
```

The only change to the request is `tools=[BASH_TOOL]`. The whole schema is
passed to the model with every call.

```python
if message.tool_calls:
    tool_call = message.tool_calls[0]
    command = json.loads(tool_call.function.arguments)["command"]
    print("Tool: bash", command)
    print(bash(command), "\n")
```

Inspect `message` at this point and the shape is clear. Its `content` is
`None`, so the model generated no text. Under `tool_calls` it did do
something: the function name is `bash` and the arguments are the JSON
string `{"command": "pwd"}`. A tool call is the reply taking a different
shape: a function name plus a JSON string of arguments. The harness parses
the JSON and calls the Python function with it.

## Run it

```bash
python llm.py
Enter your prompt> what is your current directory? also use the bash tool
```

Expected:

```text
Agent:  None

Tool: bash pwd
/home/you/simple-coding-harness/step_02_1_bash_tool
```

## What is still missing

The output went to *your* screen. The model never saw it, so it cannot
answer a question that needs two commands. Stage 2.4 passes the output
back into the model and creates a loop of tool calls. Stage 2.2 first
tidies the tool table so adding more tools costs nothing.

## Diff from stage 1

```bash
diff ../step_01_minimal_chat/llm.py llm.py
```
