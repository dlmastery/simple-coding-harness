# Step 2 - The first tool

**New in this step:** a `bash` tool. The model can ask us to run a command.

```
you ──▶ model ──▶ tool_call(bash, {"command": "ls"}) ──▶ we run it ──▶ printed
```

## The idea

A "tool" is two things that live in different worlds:

| Part | Who sees it | What it is |
|------|-------------|------------|
| the **schema** (`BASH_SCHEMA`) | the model | JSON describing the name, purpose and arguments |
| the **function** (`bash()`) | our program | ordinary Python that actually does the work |

The model never runs anything. It replies with a *tool call* - a function
name plus JSON arguments - and stops. Our code is the only thing that
executes. That separation is the whole security model of every coding agent,
so it is worth being clear about from the first tool.

## Run it

```bash
export BASE_URL=... API_KEY=...
python agent.py
you> what files are in this directory?
```

The model should answer with a tool call rather than a guess. You will see
the command it chose and its output.

## What is still missing

The output is printed to *you*, not sent to the *model*. Ask a question that
needs two commands (`what does the biggest file here do?`) and the model
cannot finish: it never learns what the first command returned. Step 4 closes
that loop. Step 3 first cleans up how tools are registered so adding more is
cheap.

## Diff from step 1

```bash
diff ../step_01_one_round_trip/agent.py agent.py
```
