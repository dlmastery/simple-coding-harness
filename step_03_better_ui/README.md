# Stage 3 - Better UI (video 16:54 - 18:26)

> "Let's actually ask Claude to build us a better UI so I can actually show
> things off in style."

New file `ui.py` (built with `rich`), and `agent.py` gets an outer loop so
it is a chat rather than a one-shot script.

```
agent.py
  ui.banner()
  while True:                # outer: one iteration per message you type
      user_input = ui.ask()
      messages.append(user)
      while True:            # inner: stage 2.4, unchanged
          call_llm -> append -> tools -> append
  ui.summary()
```

## What the UI shows

- The agent's text, rendered as markdown.
- Each tool call in a panel: name, arguments, the first twelve lines of the
  result (the model still gets the whole thing).
- A usage line after every call: prompt, completion, reasoning and
  **cached** tokens. In the video: "3,624 prompt tokens were sent, 3,328
  were cached, so only 300 new prompt tokens arrived, which is basically the
  output of this tool call." That is prefix caching from stage 2.4, visible.
- A totals table at exit.

`ui.py` never touches `messages` and `agent.py` never calls `print`. That
split is what keeps the loop readable through the next twelve stages.

## Diff from stage 2.4

```bash
diff ../step_02_4_agent_loop/agent.py agent.py
```
