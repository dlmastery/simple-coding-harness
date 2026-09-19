# AGENTS.md

Instructions for a coding agent working in this directory. The harness reads
this file into its system prompt at start; `/instructions` lists what it
loaded and `/init` writes a fresh one from a survey of the project.

## Overview

This directory is one step of a series that builds a coding agent, the
`harness` command, one feature at a time. This step adds extensions: a
Python file in `.agents/extensions/` (or `~/.simple-harness/extensions/`)
with one `apply(ctx)` function that registers tools, slash commands, hooks,
prompt sections and agent definitions. The built-in loaders for skills,
hooks, agents and MCP are extensions too. The capstone of step 38 is still
here under `capstone/`.

## Build system

- Python 3.10 or newer, packaged with `hatchling` (see `pyproject.toml`).
- Install in editable mode: `pip install -e .`
- The agent needs `API_KEY`, and optionally `BASE_URL` and `MODEL`, from the
  environment or from `~/.simple-harness/env`.

## Test command

- Whole suite, offline, no key needed: `python -m pytest -q test_step.py`
- One test: `python -m pytest -q test_step.py -k <name>`
- From the repository root: `python run_tests.py 43` and
  `python check_snippets.py 43`.
- The capstone itself, with a real model: `python capstone/run.py` with
  `API_KEY`, `BASE_URL` and `MODEL` set. Needs `pip install -e ".[capstone]"`.

## Layout

- `harness/` - the package. `agent.py` is the loop, `llm.py` builds the
  system prompt and calls the model, `tools.py` is the tool registry,
  `commands.py` handles `/` commands, `instructions.py` finds these files,
  `agents.py` reads the agent definitions, `extensions.py` loads the
  extensions, `pipeline.py` runs `/pipeline`.
- `.agents/` - project skills, agent definitions, hooks, MCP configuration
  and the example extensions in `.agents/extensions/`.
- `evals/` - the evaluation suite for `harness eval evals`.
- `capstone/` - `task.md` (the brief), `run.py` (the headless runner),
  `evals/` (five checks, graded with `harness eval capstone/evals
  --workspace DIR`), `reference/` (a hand-written solution), and the
  `report.json`, `SCORECARD.md` and `transcript.md` of the recorded run.
- `test_step.py` - the offline tests for this step.

## Conventions

- Module docstrings start with `"""Step NN - ...` and describe the code only.
- Short sentences, active voice, no first person in prose and comments.
- Paths go through `pathlib`; every file is read and written as UTF-8.
- Heavy optional libraries are imported inside the function that uses them.
- Never edit files outside this step directory.
