# Step 5 - A terminal worth using

**New in this step:** a package instead of a file, `rich` for the screen, a
spinner while the model thinks, token counts per call and a total at exit.
Zero new agent capability - this is the step where the code gets a shape.

```
harness/
├── agent.py     the two loops from step 4, unchanged in spirit
├── llm.py       the one function that calls the model, returns (message, usage)
├── tools.py     registry + execute()
├── prompts.py   the system prompt
├── ui.py        everything that touches the screen
└── config.py    BASE_URL / API_KEY / MODEL, from env or ~/.simple-harness/env
```

## Why split now

Step 4 was ~120 lines in one file and still readable. The next nine steps
add roughly 1,200 lines. Splitting by *responsibility* (talking to the
model, running tools, drawing the screen) means each later step touches one
or two files and the diffs stay small enough to read.

The rule that keeps it clean: `ui.py` receives strings and dicts and knows
nothing about the model; `agent.py` never calls `print`.

## Usage numbers

`llm.complete` now returns `(message, usage)`. Watching `prompt_tokens` grow
turn by turn is the best intuition-builder for everything in steps 8, 13
and 14: the prompt is *the whole conversation*, re-sent on every call, and it
only ever gets longer.

## Run it

```bash
python -m harness
```

Put `API_KEY=...` and `BASE_URL=...` in `~/.simple-harness/env` once and you
can stop exporting them.

## Diff from step 4

The logic in `harness/agent.py` is the same `turn()` as before. Compare:

```bash
diff ../step_04_agent_loop/agent.py harness/agent.py
```
