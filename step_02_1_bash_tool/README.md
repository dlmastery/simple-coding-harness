# Stage 2.1 - Chat with a simple bash tool (video 02:54 - 06:20)

> "Let's see what happens when we introduce tool calls into the mix."

Three additions to stage 1, all in `llm.py`:

1. A line in the system prompt: *use the bash tool to inspect files*.
2. `BASH_TOOL`, a JSON schema: type `function`, name `bash`, a
   description, and one required string argument `command`.
3. `tools=[BASH_TOOL]` on the request, and a `bash()` function that runs
   the command through `subprocess.run`.

## What happens at runtime

Ask "what is your current directory? also use the bash tool". In the
response, `message.content` is `None`. The model did not write text; it
wrote a **tool call**: `message.tool_calls[0].function.name == "bash"` and
the arguments are the JSON `{"command": "pwd"}`. We parse that and call
our Python function.

The model never executes anything. It emits a structured request; our code
is the only thing that runs. That split is the security model of every
coding agent, so the video puts a breakpoint here and inspects the object.

## What is missing

The output goes to your screen, not back to the model. "Later on in the
video, we will see how to pass this output back into the model and create a
loop of tool calls." That is stage 2.4.

## Diff from stage 1

```bash
diff ../step_01_minimal_chat/llm.py llm.py
```
