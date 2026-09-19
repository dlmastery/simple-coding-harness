---
name: actor-a
description: Train a classifier for a curriculum problem under a 24-fit budget, with the procedure split into five module files (agent loop, tool use, observation, context, completion) that a meta pack may patch one at a time. Use when the pack has a modules/ directory.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
---
# ModularRSI's actor: five modules, one job

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`, `memory.schema.json`, `memory.json`, `eval.md`. 4. The five modules, in this order: `modules/agent_loop.md`, `modules/tool_use.md`, `modules/observation.md`, `modules/context.md`, `modules/completion.md`. Follow them as one procedure; each owns one concern and a meta pack patches one at a time.

## Rules
The rules live in the modules. This file names them so a patch to one module leaves the others word for word.
