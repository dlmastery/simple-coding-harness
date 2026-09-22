# AGENTS.md

Instructions for a coding agent working in this directory. The harness reads
this file into its system prompt at start; `/instructions` lists what it
loaded and `/init` writes a fresh one from a survey of the project.

## Overview

This directory is one step of a series that builds a coding agent, the
`harness` command, one feature at a time. This step adds no code: its
README compares the harness, mechanism by mechanism, with five production
harnesses. `harness/` is a byte-identical copy of step 36.

## Build system

- Python 3.10 or newer, packaged with `hatchling` (see `pyproject.toml`).
- Install in editable mode: `pip install -e .`
- The agent needs `API_KEY`, and optionally `BASE_URL` and `MODEL`, from the
  environment or from `~/.simple-harness/env`.

## Test command

- Whole suite, offline, no key needed: `python -m pytest -q test_step.py`
- One test: `python -m pytest -q test_step.py -k <name>`
- From the repository root: `python run_tests.py 37` and
  `python check_snippets.py 37`.

## Layout

- `harness/` - the package. `agent.py` is the loop, `llm.py` builds the
  system prompt and calls the model, `tools.py` is the tool registry,
  `commands.py` handles `/` commands, `instructions.py` finds these files,
  `agents.py` reads the agent definitions, `pipeline.py` runs `/pipeline`.
- `.agents/` - project skills, agent definitions, hooks and MCP configuration.
- `evals/` - the evaluation suite for `harness eval evals`.
- `test_step.py` - the offline tests for this step.

## Conventions

- Module docstrings start with `"""Step NN - ...` and describe the code only.
- Short sentences, active voice, no first person in prose and comments.
- Paths go through `pathlib`; every file is read and written as UTF-8.
- Heavy optional libraries are imported inside the function that uses them.
- Never edit files outside this step directory.
