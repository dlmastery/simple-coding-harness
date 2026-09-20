---
name: actor-b
description: "ModularRSI's actor B - train a classifier for a problem under a 24-fit budget by following the five module files under modules/ (agent loop, tool use, observation, context, completion) with helpers you build from the contracts in tools.md. Use in rsi/step_12_rsi_modular on the pool tables; the meta pack may patch one module at a time."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
---
# ModularRSI's actor: five modules, one harness

Run every helper through the Bash tool from this lesson's directory. This pack's directory is
`.claude/skills/actor-b` (`P`); the problem's directory is `T` (a pool table under `pool/`, or a
curriculum problem under `../tasks/`). Build the helpers of `tools.md` under `runs/actor-b/helpers/`
on first use.

## Boot order
1. This file. 2. `tools.md`. 3. `schema.json`, `memory.schema.json`, `config.md`, `memory.json`. 4. `modules/agent_loop.md`, `modules/tool_use.md`, `modules/observation.md`, `modules/context.md`, `modules/completion.md` - the harness is these five files, and the procedure below only says in which order to read them.

## Procedure
1. Do what `modules/agent_loop.md` says, reading `modules/context.md` for the next recipes, `modules/observation.md` for the result and `modules/completion.md` at FREEZE, under the rules of `modules/tool_use.md`.

## Rules
- A module is one file; only the meta pack may change one, and only one at a time, validated on the pool.
- Never write a card: the verifier's job. Never run `score_test` before FREEZE, never twice.

## Off switch
MEMORY_OFF: `memory: off` in `config.md`, or `--memory off` on the arm.

## Done when
`modules/completion.md` was followed.
