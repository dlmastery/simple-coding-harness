---
name: actor-b
description: ModularRSI's actor B - train a classifier for a pool or curriculum problem under a 24-fit budget with the procedure split into five module files (agent loop, tool use, observation, context, completion) that a meta pack may patch one at a time. Use in rsi/step_12_rsi_modular when the pack has a modules/ directory.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
---
# ModularRSI's actor B: five modules, one job

Run every command through the Bash tool from this lesson's directory. This
pack's directory is `.claude/skills/actor-b` (`P`); the task file is `T`
(a pool task under `pool/`, or a curriculum task under `../tasks/`).

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`, `memory.schema.json`, `memory.json`, `eval.md`. 4. The five modules, in this order: `modules/agent_loop.md`, `modules/tool_use.md`, `modules/observation.md`, `modules/context.md`, `modules/completion.md`. Follow them as one procedure; each owns one concern and a meta pack patches one at a time.

## Procedure
The procedure lives in the modules: run `modules/agent_loop.md`.

## Rules
The rules live in the modules. This file names them so a patch to one module leaves the others word for word. Never run `score_test.py` before FREEZE (the completion module says so; the script and the hook enforce it), never write a card, never edit a module yourself.

## Done when
`score_test.py` answered once for the arm.
